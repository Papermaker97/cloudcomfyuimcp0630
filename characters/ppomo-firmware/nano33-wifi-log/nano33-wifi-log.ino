// Ppomo breadboard prototype, end to end: squeeze -> count + date/time -> web.
// Arduino Nano 33 IoT + 2 flex sensors + LED (parts on hand). Same counting logic as nano33-flex-test;
// on top of that, every squeeze is stamped with UTC time from NTP and POSTed over Wi-Fi to the
// Supabase table in ../../ppomo-device/web/schema.sql, so ../../ppomo-device/web/dashboard.html shows it live.
//
// Wiring (per sensor):  3.3V -- flex sensor --+-- A0 (belly) / A1 (butt)
//                                             +-- 10k -- GND
//                       D2 -- 220 ohm -- LED -- GND
// Library: WiFiNINA (Library Manager). Fill in arduino_secrets.h first.
//
// Serial (115200, one JSON object per line), so the test bench page still works:
//   {"type":"ready","count":N}  {"type":"raw",...} every 20 ms  {"type":"squeeze","count":N,"source":"belly","ts":"..."}
//   {"type":"upload","seq":N,"http":201}   {"type":"wifi","status":"connected","time":"..."}
// Commands: P<n> press delta, R<n> release delta, Z re-measure rest, S toggle raw stream.
//
// No squeeze is lost while Wi-Fi is down: events wait in a RAM queue (QUEUE_MAX) and are sent when it
// comes back. The running count continues from the highest seq already on the server at boot.
#include <WiFiNINA.h>
#include "arduino_secrets.h"

const int BELLY_PIN = A0;
const int BUTT_PIN = A1;
const int FEEDBACK_PIN = 2;
const bool USE_BUTT_SENSOR = true;

int pressDelta = 260;
int releaseDelta = 120;
const unsigned long PRESS_CONFIRM_MS = 40;
const unsigned long RELEASE_CONFIRM_MS = 120;
const unsigned long FEEDBACK_MS = 120;
const unsigned long SAMPLE_MS = 10;
const unsigned long RAW_EVERY_MS = 20;
const unsigned long CALIBRATION_MS = 1000;
const float BASELINE_TAU_MS = 20000.0;
const float RELAX_TAU_MS = 200.0;
const unsigned long STUCK_REARM_MS = 4000;
const unsigned long WIFI_RETRY_MS = 30000;            // joining blocks sensing for a few seconds, so don't retry often
const unsigned long UPLOAD_RETRY_MS = 3000;
const int QUEUE_MAX = 200;

// ---------- squeeze state (from nano33-flex-test) ----------
unsigned long squeezeCount = 0;
float bellyBase = 0, buttBase = 0;
int bellyDir = 0, buttDir = 0;
bool squeezed = false, streamRaw = true, feedbackOn = false;
unsigned long pressStartedAt = 0, releaseStartedAt = 0, squeezedAt = 0, feedbackAt = 0;
unsigned long lastSampleAt = 0, lastRawAt = 0;
String cmd;

// ---------- time + upload state ----------
struct Event { unsigned long seq; unsigned long atMillis; const char *source; };
Event queue[QUEUE_MAX];
int queueHead = 0, queueLen = 0;
unsigned long epochAtSync = 0, millisAtSync = 0;     // UTC seconds from NTP and millis() at that moment
bool seqKnown = false;                              // continued from the server's highest seq?
unsigned long lastWifiTry = 0, lastUploadTry = 0;
WiFiSSLClient tls;

int readFiltered(int pin) {
  int a = analogRead(pin), b = analogRead(pin), c = analogRead(pin);
  if (a > b) { int t = a; a = b; b = t; }
  if (b > c) { int t = b; b = c; c = t; }
  if (a > b) { int t = a; a = b; b = t; }
  return b;
}
int readButt() { return USE_BUTT_SENSOR ? readFiltered(BUTT_PIN) : 0; }

void calibrate() {
  unsigned long started = millis(), n = 0;
  float a = 0, b = 0;
  while (millis() - started < CALIBRATION_MS) { a += readFiltered(BELLY_PIN); b += readButt(); n++; delay(10); }
  bellyBase = a / n; buttBase = b / n;
}
float depth(int v, float base, int dir) { return dir == 0 ? fabs(v - base) : dir * (v - base); }
void track(float &base, int v, int dir) {
  float d = v - base;
  if (dir != 0 && dir * d < 0) base += d * (SAMPLE_MS / RELAX_TAU_MS);
  else if (fabs(d) <= releaseDelta) base += d * (SAMPLE_MS / BASELINE_TAU_MS);
}

// ---------- time ----------
bool timeKnown() { return epochAtSync != 0; }
// ISO 8601 UTC for an event that happened at millis() == at
String isoAt(unsigned long at) {
  unsigned long long ms = (unsigned long long)epochAtSync * 1000ULL + (long)(at - millisAtSync);
  unsigned long s = ms / 1000, days = s / 86400, rem = s % 86400;
  // days since 1970-01-01 -> y/m/d (civil-from-days)
  long z = days + 719468, era = z / 146097;
  unsigned long doe = z - era * 146097, yoe = (doe - doe / 1460 + doe / 36524 - doe / 146096) / 365;
  long y = yoe + era * 400;
  unsigned long doy = doe - (365 * yoe + yoe / 4 - yoe / 100), mp = (5 * doy + 2) / 153;
  unsigned d = doy - (153 * mp + 2) / 5 + 1, m = mp < 10 ? mp + 3 : mp - 9;
  if (m <= 2) y++;
  char buf[48];
  snprintf(buf, sizeof buf, "%04ld-%02u-%02uT%02lu:%02lu:%02lu.%03uZ", y, m, d, rem / 3600, (rem / 60) % 60, rem % 60, (unsigned)(ms % 1000));
  return String(buf);
}

// ---------- Wi-Fi ----------
void ensureWifi() {
  if (WiFi.status() == WL_CONNECTED) return;
  if (lastWifiTry && millis() - lastWifiTry < WIFI_RETRY_MS) return;
  lastWifiTry = millis();
  WiFi.begin(SECRET_SSID, SECRET_PASS);              // blocks a few seconds while joining
  if (WiFi.status() != WL_CONNECTED) { Serial.println("{\"type\":\"wifi\",\"status\":\"failed\"}"); return; }
  for (int i = 0; i < 10 && !timeKnown(); i++) {     // NTP through the Wi-Fi module
    unsigned long t = WiFi.getTime();
    if (t > 1700000000UL) { epochAtSync = t; millisAtSync = millis(); }
    else delay(500);
  }
  Serial.print("{\"type\":\"wifi\",\"status\":\"connected\",\"time\":");
  Serial.print(timeKnown() ? "\"" + isoAt(millis()) + "\"" : String("null"));
  Serial.println("}");
}

// one HTTPS request to Supabase's REST API; returns the status code, body in `body`
int supabase(const char *method, const String &path, const String &payload, String &body) {
  body = "";
  if (!tls.connect(SUPABASE_HOST, 443)) return -1;
  tls.print(method); tls.print(" "); tls.print(path); tls.println(" HTTP/1.1");
  tls.println("Host: " SUPABASE_HOST);
  tls.println("apikey: " SUPABASE_KEY);
  tls.println("Authorization: Bearer " SUPABASE_KEY);
  tls.println("Prefer: resolution=ignore-duplicates,return=minimal");
  tls.println("Connection: close");
  if (payload.length()) { tls.println("Content-Type: application/json"); tls.print("Content-Length: "); tls.println(payload.length()); }
  tls.println();
  if (payload.length()) tls.print(payload);
  unsigned long t0 = millis();
  String head;
  int code = -2;
  bool inBody = false;
  while ((tls.connected() || tls.available()) && millis() - t0 < 8000) {
    if (!tls.available()) { delay(2); continue; }
    char c = tls.read();
    if (inBody) { if (body.length() < 512) body += c; continue; }
    head += c;
    if (code == -2 && head.startsWith("HTTP/1.1 ") && head.length() >= 12) code = head.substring(9, 12).toInt();
    if (head.endsWith("\r\n\r\n")) inBody = true;
  }
  tls.stop();
  return code;
}

// continue the running count from the server, so a reboot doesn't restart at 1
void fetchLastSeq() {
  String body;
  int code = supabase("GET", "/rest/v1/squeezes?select=seq&device_id=eq." DEVICE_ID "&order=seq.desc&limit=1", "", body);
  if (code != 200) return;
  int i = body.indexOf("\"seq\":");
  unsigned long last = i >= 0 ? body.substring(i + 6).toInt() : 0;
  // squeezes made before we knew are renumbered after the server's last one
  for (int k = 0; k < queueLen; k++) queue[(queueHead + k) % QUEUE_MAX].seq = last + 1 + k;
  squeezeCount = last + queueLen;
  seqKnown = true;
  Serial.print("{\"type\":\"ready\",\"count\":"); Serial.print(squeezeCount); Serial.println("}");
}

void uploadOne() {
  if (!queueLen || !timeKnown() || !seqKnown) return;
  if (millis() - lastUploadTry < UPLOAD_RETRY_MS && lastUploadTry) return;
  lastUploadTry = millis();
  const Event &e = queue[queueHead];
  String json = String("[{\"device_id\":\"" DEVICE_ID "\",\"seq\":") + e.seq + ",\"ts\":\"" + isoAt(e.atMillis) +
                "\",\"source\":\"" + e.source + "\"}]";
  String body;
  int code = supabase("POST", "/rest/v1/squeezes?on_conflict=device_id,seq", json, body);
  Serial.print("{\"type\":\"upload\",\"seq\":"); Serial.print(e.seq); Serial.print(",\"http\":"); Serial.print(code); Serial.println("}");
  if (code >= 200 && code < 300) { queueHead = (queueHead + 1) % QUEUE_MAX; queueLen--; lastUploadTry = 0; }
}

void enqueue(const char *source) {
  if (queueLen == QUEUE_MAX) { queueHead = (queueHead + 1) % QUEUE_MAX; queueLen--; }   // full: drop the oldest
  queue[(queueHead + queueLen) % QUEUE_MAX] = { squeezeCount, millis(), source };
  queueLen++;
}

void handleCommand(const String &c) {
  if (c.length() == 0) return;
  char k = toupper(c[0]);
  if (k == 'P') pressDelta = max(10, (int)c.substring(1).toInt());
  else if (k == 'R') releaseDelta = max(5, (int)c.substring(1).toInt());
  else if (k == 'Z') { calibrate(); squeezed = false; bellyDir = buttDir = 0; }
  else if (k == 'S') streamRaw = !streamRaw;
  if (releaseDelta >= pressDelta) releaseDelta = pressDelta / 2;
}

void setup() {
  pinMode(FEEDBACK_PIN, OUTPUT);
  pinMode(LED_BUILTIN, OUTPUT);
  analogReadResolution(12);
  Serial.begin(115200);
  unsigned long t0 = millis();
  while (!Serial && millis() - t0 < 2000) {}
  calibrate();
  Serial.println("{\"type\":\"ready\",\"count\":0}");
  ensureWifi();
  if (WiFi.status() == WL_CONNECTED) fetchLastSeq();
}

void loop() {
  while (Serial.available()) {
    char ch = Serial.read();
    if (ch == '\n' || ch == '\r') { handleCommand(cmd); cmd = ""; } else if (cmd.length() < 16) cmd += ch;
  }

  unsigned long now = millis();
  if (feedbackOn && now - feedbackAt >= FEEDBACK_MS) { digitalWrite(FEEDBACK_PIN, LOW); digitalWrite(LED_BUILTIN, LOW); feedbackOn = false; }

  if (now - lastSampleAt >= SAMPLE_MS) {
    lastSampleAt = now;
    int belly = readFiltered(BELLY_PIN), butt = readButt();
    float dBelly = depth(belly, bellyBase, bellyDir), dButt = USE_BUTT_SENSOR ? depth(butt, buttBase, buttDir) : 0;
    bool bellyOn = dBelly >= pressDelta, buttOn = dButt >= pressDelta, anyOn = bellyOn || buttOn;
    bool released = dBelly <= releaseDelta && dButt <= releaseDelta;

    if (!squeezed) {
      track(bellyBase, belly, bellyDir);
      if (USE_BUTT_SENSOR) track(buttBase, butt, buttDir);
      if (anyOn) {
        if (pressStartedAt == 0) pressStartedAt = now;
        if (now - pressStartedAt >= PRESS_CONFIRM_MS) {
          squeezed = true; squeezedAt = now; pressStartedAt = 0; releaseStartedAt = 0;
          squeezeCount++;
          if (bellyOn && bellyDir == 0) bellyDir = belly > bellyBase ? 1 : -1;
          if (buttOn && buttDir == 0) buttDir = butt > buttBase ? 1 : -1;
          digitalWrite(FEEDBACK_PIN, HIGH); digitalWrite(LED_BUILTIN, HIGH); feedbackOn = true; feedbackAt = now;
          // the web table knows body / belly / butt; both sensors at once counts as the whole body
          const char *src = bellyOn ? (buttOn ? "body" : "belly") : "butt";
          enqueue(src);
          Serial.print("{\"type\":\"squeeze\",\"count\":"); Serial.print(squeezeCount);
          Serial.print(",\"source\":\""); Serial.print(bellyOn && buttOn ? "both" : src);
          Serial.print("\",\"ts\":"); Serial.print(timeKnown() ? "\"" + isoAt(now) + "\"" : String("null"));
          Serial.println("}");
        }
      } else pressStartedAt = 0;
    } else {
      if (released) {
        if (releaseStartedAt == 0) releaseStartedAt = now;
        if (now - releaseStartedAt >= RELEASE_CONFIRM_MS) { squeezed = false; releaseStartedAt = 0; }
      } else {
        releaseStartedAt = 0;
        if (now - squeezedAt >= STUCK_REARM_MS) { bellyBase = belly; if (USE_BUTT_SENSOR) buttBase = butt; squeezed = false; }
      }
    }

    if (streamRaw && now - lastRawAt >= RAW_EVERY_MS) {
      lastRawAt = now;
      Serial.print("{\"type\":\"raw\",\"t\":"); Serial.print(now);
      Serial.print(",\"belly\":"); Serial.print(belly); Serial.print(",\"butt\":"); Serial.print(butt);
      Serial.print(",\"bb\":"); Serial.print((int)bellyBase); Serial.print(",\"bt\":"); Serial.print((int)buttBase);
      Serial.print(",\"p\":"); Serial.print(pressDelta); Serial.print(",\"r\":"); Serial.print(releaseDelta);
      Serial.println("}");
    }
  }

  // network work only between squeezes, so a slow request never delays the moment a squeeze is counted
  if (!squeezed && !pressStartedAt) {
    ensureWifi();
    if (WiFi.status() == WL_CONNECTED) {
      if (!seqKnown) fetchLastSeq();
      uploadOne();
    }
  }
}
