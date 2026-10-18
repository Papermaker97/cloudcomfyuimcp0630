// Ppomo device firmware: count squeezes, stamp each with date + time, send them to the web.
//
// Board: Seeed XIAO ESP32-C3 (Arduino core "esp32" by Espressif, 2.x or 3.x)
// Libraries (Library Manager):
//   - SparkFun BMP581 Arduino Library      pressure inside the sealed body = the squeeze sensor
//   - RTClib (Adafruit)                    DS3231 keeps the date/time through reboots and offline
//   - Adafruit DRV2605 Library             haptic "tick" on every counted squeeze
//
// How it works
//   sensor task (100 Hz)  BMP581 -> SqueezeDetector -> haptic tick + event into a queue
//   loop()                queue -> flash log (EventLog) -> serial JSON
//                         every minute, if anything is unsent: Wi-Fi on -> NTP (sets the RTC)
//                         -> HTTPS POST to Supabase -> Wi-Fi off
//   Time: system clock set from the DS3231 at boot, corrected by NTP whenever Wi-Fi is up.
//
// Serial (115200): {"type":"ready",...} {"type":"squeeze","count":N,"source":"body","ts":"2026-..Z"}
//   {"type":"upload","sent":N,"http":201}   commands: P<pa> R<pa> Z (re-measure rest) S (stream pressure)
#include <Wire.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <sys/time.h>
#include <SparkFun_BMP581_Arduino_Library.h>
#include <RTClib.h>
#include <Adafruit_DRV2605.h>
#include "config.h"
#include "squeeze_detector.h"
#include "event_log.h"

// ---- pins (XIAO ESP32-C3) ----
const int BATTERY_PIN = D0;      // VBAT -- 220k -- D0 -- 220k -- GND
const int FSR_BELLY_PIN = D1;    // optional: 3V3 -- FSR -- D1 -- 10k -- GND
const int FSR_BUTT_PIN = D2;     // optional: 3V3 -- FSR -- D2 -- 10k -- GND
const int PRESSURE_INT_PIN = D3; // BMP581 INT, wired now for deep-sleep wake later (not used yet)
// I2C on D4 (SDA) / D5 (SCL): BMP581 0x47, DS3231 0x68, DRV2605L 0x5A

const uint32_t SAMPLE_MS = 10;
const uint32_t UPLOAD_EVERY_MS = 60000;
const uint32_t UPLOAD_MAX_BACKOFF_MS = 15 * 60000;
const size_t UPLOAD_BATCH = 50;
const int FSR_MIN_RISE = 150;    // ADC counts above rest for a pad to name the squeeze location

BMP581 pressure;
RTC_DS3231 rtc;
Adafruit_DRV2605 haptic;
SqueezeDetector detector;
EventLog eventLog;
SemaphoreHandle_t i2c;           // Wire is shared by the sensor task and loop()
QueueHandle_t events;

struct Pending { uint8_t kind; uint32_t uptimeMs; int64_t epochMs; bool timeValid; uint8_t source; uint16_t peakPa; };
enum : uint8_t { PENDING_SQUEEZE, PENDING_PEAK };

volatile bool streamPressure = false, rezero = false;
volatile float lastPa = 0;
bool haveRtc = false, haveHaptic = false;
int fsrRest[2] = {0, 0};
uint32_t openSeq = 0;            // the squeeze still being held (its strength isn't known yet)
uint32_t nextUploadAt = 0, uploadBackoff = UPLOAD_EVERY_MS;

// ---------- time ----------
bool timeValid() { return time(nullptr) > 1700000000; }   // after Nov 2023 = set from RTC or NTP
int64_t epochMsNow() { struct timeval tv; gettimeofday(&tv, nullptr); return (int64_t)tv.tv_sec * 1000 + tv.tv_usec / 1000; }
void setSystemTime(time_t t) { struct timeval tv = { t, 0 }; settimeofday(&tv, nullptr); }
String iso(int64_t ms) {
  time_t s = ms / 1000; struct tm g; gmtime_r(&s, &g);
  char buf[32]; snprintf(buf, sizeof buf, "%04d-%02d-%02dT%02d:%02d:%02d.%03dZ", g.tm_year + 1900, g.tm_mon + 1, g.tm_mday, g.tm_hour, g.tm_min, g.tm_sec, (int)(ms % 1000));
  return String(buf);
}

// ---------- sensors ----------
bool readPressure(float &pa) {
  bmp5_sensor_data d = {0, 0};
  xSemaphoreTake(i2c, portMAX_DELAY);
  int8_t err = pressure.getSensorData(&d);
  xSemaphoreGive(i2c);
  if (err != BMP5_OK) return false;
  pa = d.pressure;
  return true;
}
float measureRest() {
  float sum = 0; int n = 0;
  for (int i = 0; i < 50; i++) { float pa; if (readPressure(pa)) { sum += pa; n++; } delay(SAMPLE_MS); }
  return n ? sum / n : 101325;
}
uint8_t squeezeSource() {
#if USE_LOCATION_FSRS
  int belly = analogRead(FSR_BELLY_PIN) - fsrRest[0], butt = analogRead(FSR_BUTT_PIN) - fsrRest[1];
  if (max(belly, butt) < FSR_MIN_RISE) return SRC_BODY;
  return belly >= butt ? SRC_BELLY : SRC_BUTT;
#else
  return SRC_BODY;
#endif
}
const char *sourceName(uint8_t s) { return s == SRC_BELLY ? "belly" : s == SRC_BUTT ? "butt" : "body"; }
void buzz() {
  if (!haveHaptic) return;
  xSemaphoreTake(i2c, portMAX_DELAY);
  haptic.setWaveform(0, 1);    // effect 1: strong click
  haptic.setWaveform(1, 0);
  haptic.go();
  xSemaphoreGive(i2c);
}

// ---------- sensor task: never blocked by Wi-Fi or flash ----------
void sensorTask(void *) {
  TickType_t last = xTaskGetTickCount();
  for (;;) {
    vTaskDelayUntil(&last, pdMS_TO_TICKS(SAMPLE_MS));
    if (rezero) { detector.begin(measureRest()); rezero = false; last = xTaskGetTickCount(); continue; }
    float pa;
    if (!readPressure(pa)) continue;
    lastPa = pa;
    const uint32_t now = millis();
    const bool wasSqueezed = detector.squeezed();
    if (detector.update(pa, now, SAMPLE_MS)) {
      buzz();
      Pending p = { PENDING_SQUEEZE, now, epochMsNow(), timeValid(), squeezeSource(), 0 };
      xQueueSend(events, &p, 0);
    } else if (wasSqueezed && !detector.squeezed()) {
      Pending p = { PENDING_PEAK, now, 0, false, 0, (uint16_t)min(65535.0f, detector.lastPeakPa()) };
      xQueueSend(events, &p, 0);
    }
  }
}

// ---------- upload ----------
bool wifiUp() {
  if (WiFi.status() == WL_CONNECTED) return true;
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  for (uint32_t t0 = millis(); millis() - t0 < 15000; delay(100)) if (WiFi.status() == WL_CONNECTED) return true;
  return false;
}
void wifiDown() { WiFi.disconnect(true); WiFi.mode(WIFI_OFF); }
void syncClock() {
  configTime(0, 0, "pool.ntp.org", "time.nist.gov");
  for (uint32_t t0 = millis(); millis() - t0 < 8000; delay(100)) {
    struct tm g;
    if (getLocalTime(&g, 0) && timeValid()) {
      if (haveRtc) { xSemaphoreTake(i2c, portMAX_DELAY); rtc.adjust(DateTime((uint32_t)time(nullptr))); xSemaphoreGive(i2c); }
      return;
    }
  }
}
void uploadPending() {
  static SqueezeRecord batch[UPLOAD_BATCH];
  size_t n = eventLog.unsent(batch, UPLOAD_BATCH);
  while (n && batch[n - 1].seq == openSeq) n--;            // wait until the held squeeze is let go
  if (!n) return;
  if (!wifiUp()) { Serial.println("{\"type\":\"upload\",\"error\":\"wifi\"}"); return; }
  syncClock();
  String body = "[";
  for (size_t i = 0; i < n; i++) {
    const SqueezeRecord &r = batch[i];
    String ts = "null";
    if (r.flags & EV_TIME_VALID) ts = "\"" + iso(r.epochMs) + "\"";
    else if (r.boot == eventLog.boot() && timeValid()) ts = "\"" + iso(epochMsNow() - (int64_t)(millis() - r.uptimeMs)) + "\"";   // stamped late, same boot
    body += String(i ? "," : "") + "{\"device_id\":\"" DEVICE_ID "\",\"seq\":" + r.seq + ",\"ts\":" + ts +
            ",\"source\":\"" + sourceName(r.source) + "\",\"peak_pa\":" + r.peakPa + ",\"boot\":" + r.boot + "}";
  }
  body += "]";
  WiFiClientSecure tls;
  tls.setInsecure();           // prototype only: pin the Supabase root CA before shipping
  HTTPClient http;
  http.begin(tls, SUPABASE_URL "/rest/v1/squeezes?on_conflict=device_id,seq");
  http.addHeader("apikey", SUPABASE_ANON_KEY);
  http.addHeader("Authorization", "Bearer " SUPABASE_ANON_KEY);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("Prefer", "resolution=ignore-duplicates,return=minimal");
  const int code = http.POST(body);
  http.end();
  const bool ok = code >= 200 && code < 300;
  if (ok) eventLog.ack(batch[n - 1].seq);
  Serial.printf("{\"type\":\"upload\",\"sent\":%u,\"http\":%d}\n", ok ? (unsigned)n : 0, code);
  uploadBackoff = ok ? UPLOAD_EVERY_MS : min(uploadBackoff * 2, UPLOAD_MAX_BACKOFF_MS);
  if (!eventLog.pending() || !ok) wifiDown();
}

// ---------- setup / loop ----------
void setup() {
  Serial.begin(115200);
  delay(300);
  analogReadResolution(12);
  Wire.begin();
  i2c = xSemaphoreCreateMutex();
  events = xQueueCreate(32, sizeof(Pending));

  if (!eventLog.begin()) Serial.println("{\"type\":\"error\",\"what\":\"flash\"}");
  while (pressure.beginI2C(BMP581_I2C_ADDRESS_DEFAULT) != BMP5_OK) { Serial.println("{\"type\":\"error\",\"what\":\"bmp581\"}"); delay(1000); }
  // 100 Hz, light oversampling: check names against the library's "ODR and OSR" example
  bmp5_osr_odr_press_config osr = { BMP5_OVERSAMPLING_1X, BMP5_OVERSAMPLING_4X, BMP5_ENABLE, 0 };
  pressure.setOSRMultipliers(&osr);
  pressure.setODRFrequency(BMP5_ODR_100_2_HZ);

  haveRtc = rtc.begin();
  if (haveRtc && !rtc.lostPower()) setSystemTime(rtc.now().unixtime());
  haveHaptic = haptic.begin();
  if (haveHaptic) { haptic.selectLibrary(6); haptic.useLRA(); haptic.setMode(DRV2605_MODE_INTTRIG); }   // ERM motor: useERM() + library 1
#if USE_LOCATION_FSRS
  fsrRest[0] = analogRead(FSR_BELLY_PIN); fsrRest[1] = analogRead(FSR_BUTT_PIN);
#endif

  detector.begin(measureRest());
  xTaskCreate(sensorTask, "squeeze", 4096, nullptr, 3, nullptr);
  Serial.printf("{\"type\":\"ready\",\"count\":%u,\"time\":\"%s\",\"rtc\":%s}\n", (unsigned)eventLog.count(),
                timeValid() ? iso(epochMsNow()).c_str() : "unknown", haveRtc ? "true" : "false");
  nextUploadAt = millis() + 5000;
}

void handleCommand(const String &c) {
  if (!c.length()) return;
  const char k = toupper(c[0]);
  if (k == 'P') detector.cfg.pressPa = max(20L, c.substring(1).toInt());
  else if (k == 'R') detector.cfg.releasePa = max(10L, c.substring(1).toInt());
  else if (k == 'Z') rezero = true;
  else if (k == 'S') streamPressure = !streamPressure;
  if (detector.cfg.releasePa >= detector.cfg.pressPa) detector.cfg.releasePa = detector.cfg.pressPa / 2;
}

void loop() {
  static String cmd;
  while (Serial.available()) {
    const char ch = Serial.read();
    if (ch == '\n' || ch == '\r') { handleCommand(cmd); cmd = ""; } else if (cmd.length() < 16) cmd += ch;
  }

  Pending p;
  while (xQueueReceive(events, &p, 0) == pdTRUE) {
    if (p.kind == PENDING_SQUEEZE) {
      SqueezeRecord r = {};
      r.epochMs = p.epochMs; r.uptimeMs = p.uptimeMs; r.source = p.source; r.flags = p.timeValid ? EV_TIME_VALID : 0;
      openSeq = eventLog.append(r);
      Serial.printf("{\"type\":\"squeeze\",\"count\":%u,\"source\":\"%s\",\"ts\":%s}\n", (unsigned)openSeq, sourceName(p.source),
                    p.timeValid ? ("\"" + iso(p.epochMs) + "\"").c_str() : "null");
    } else {
      eventLog.setLastPeak(openSeq, p.peakPa);
      openSeq = 0;
    }
  }

  static uint32_t lastStream = 0;
  if (streamPressure && millis() - lastStream >= 20) {
    lastStream = millis();
    Serial.printf("{\"type\":\"pressure\",\"pa\":%.1f,\"rest\":%.1f,\"p\":%.0f,\"r\":%.0f}\n", lastPa, detector.base(), detector.cfg.pressPa, detector.cfg.releasePa);
  }

  if (eventLog.pending() && (int32_t)(millis() - nextUploadAt) >= 0) {
    uploadPending();
    nextUploadAt = millis() + uploadBackoff;
  }

  static uint32_t lastBattery = 0;
  if (millis() - lastBattery >= 60000) {
    lastBattery = millis();
    Serial.printf("{\"type\":\"battery\",\"mv\":%u}\n", (unsigned)(analogReadMilliVolts(BATTERY_PIN) * 2));
  }
  delay(5);
}
