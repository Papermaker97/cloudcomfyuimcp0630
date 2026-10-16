// Ppomo test bench firmware — Arduino Nano 33 IoT + 2 flex sensors + LED (no vibration motor yet)
//
// Wiring (per sensor):  3.3V -- flex sensor --+-- A0 (belly) / A1 (butt)
//                                             +-- 10k (or ~ the sensor's flat resistance) -- GND
//                       D2 -- 220 ohm -- LED -- GND   (stands in for the vibration motor)
//
// Same counting logic as the product firmware (one squeeze = one event, hysteresis, re-arm).
// Flex sensors can read higher or lower when bent depending on how they're mounted, so each
// sensor's direction is learned from its first counted squeeze; moving the other way is treated
// as relaxing back to rest, never as a new squeeze.
//
// Serial (115200, one JSON object per line):
//   {"type":"ready","count":0}
//   {"type":"raw","t":1234,"belly":2010,"butt":1988,"bb":2000,"bt":1990,"p":260,"r":120}   every 20 ms
//   {"type":"squeeze","count":3,"source":"belly"}                                           per counted squeeze
// Commands you can send (end with a newline): P<number> press delta, R<number> release delta,
//   Z re-measure the resting baseline (hands off), C reset the count, S toggle raw streaming.
// Note: the Nano 33 IoT has no EEPROM, so this test version keeps the count in RAM only.

const int BELLY_PIN = A0;
const int BUTT_PIN = A1;
const int FEEDBACK_PIN = 2;            // LED now, vibration motor (through a transistor) later
const bool USE_BUTT_SENSOR = true;     // set false if only one flex sensor is wired

int pressDelta = 260;                  // 12-bit counts away from rest that start a squeeze
int releaseDelta = 120;                // must come back within this to count as released
const unsigned long PRESS_CONFIRM_MS = 40;
const unsigned long RELEASE_CONFIRM_MS = 120;
const unsigned long FEEDBACK_MS = 120;
const unsigned long SAMPLE_MS = 10;
const unsigned long RAW_EVERY_MS = 20;
const unsigned long CALIBRATION_MS = 1000;
const float BASELINE_TAU_MS = 20000.0;  // slow drift follow, only while at rest
const float RELAX_TAU_MS = 200.0;       // quick follow when a sensor relaxes past its baseline
const unsigned long STUCK_REARM_MS = 4000;

unsigned long squeezeCount = 0;
float bellyBase = 0, buttBase = 0;
int bellyDir = 0, buttDir = 0;          // +1 / -1 once learned, 0 = not known yet
bool squeezed = false, streamRaw = true, feedbackOn = false;
unsigned long pressStartedAt = 0, releaseStartedAt = 0, squeezedAt = 0, feedbackAt = 0;
unsigned long lastSampleAt = 0, lastRawAt = 0;
String cmd;

int readFiltered(int pin) {             // median of three
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

// how far a reading is "into" a squeeze: signed once the bend direction is known
float depth(int v, float base, int dir) { return dir == 0 ? fabs(v - base) : dir * (v - base); }

void track(float &base, int v, int dir) {
  float d = v - base;
  if (dir != 0 && dir * d < 0) base += d * (SAMPLE_MS / RELAX_TAU_MS);        // relaxing past rest
  else if (fabs(d) <= releaseDelta) base += d * (SAMPLE_MS / BASELINE_TAU_MS); // slow drift at rest
}

void sendSqueeze(const char *src) {
  Serial.print("{\"type\":\"squeeze\",\"count\":"); Serial.print(squeezeCount);
  Serial.print(",\"source\":\""); Serial.print(src); Serial.println("\"}");
}
void sendReady() { Serial.print("{\"type\":\"ready\",\"count\":"); Serial.print(squeezeCount); Serial.println("}"); }

void handleCommand(const String &c) {
  if (c.length() == 0) return;
  char k = toupper(c[0]);
  if (k == 'P') pressDelta = max(10, (int)c.substring(1).toInt());
  else if (k == 'R') releaseDelta = max(5, (int)c.substring(1).toInt());
  else if (k == 'Z') { calibrate(); squeezed = false; bellyDir = buttDir = 0; }
  else if (k == 'C') { squeezeCount = 0; sendReady(); }
  else if (k == 'S') streamRaw = !streamRaw;
  if (releaseDelta >= pressDelta) releaseDelta = pressDelta / 2;
}

void setup() {
  pinMode(FEEDBACK_PIN, OUTPUT);
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(FEEDBACK_PIN, LOW);
  analogReadResolution(12);
  Serial.begin(115200);
  unsigned long t0 = millis();
  while (!Serial && millis() - t0 < 2000) {}   // give the USB serial a moment, but don't hang without it
  calibrate();
  sendReady();
}

void loop() {
  while (Serial.available()) {
    char ch = Serial.read();
    if (ch == '\n' || ch == '\r') { handleCommand(cmd); cmd = ""; } else if (cmd.length() < 16) cmd += ch;
  }

  unsigned long now = millis();
  if (feedbackOn && now - feedbackAt >= FEEDBACK_MS) { digitalWrite(FEEDBACK_PIN, LOW); digitalWrite(LED_BUILTIN, LOW); feedbackOn = false; }
  if (now - lastSampleAt < SAMPLE_MS) return;
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
        if (bellyOn && bellyDir == 0) bellyDir = belly > bellyBase ? 1 : -1;   // learn bend direction
        if (buttOn && buttDir == 0) buttDir = butt > buttBase ? 1 : -1;
        digitalWrite(FEEDBACK_PIN, HIGH); digitalWrite(LED_BUILTIN, HIGH); feedbackOn = true; feedbackAt = now;
        sendSqueeze(bellyOn ? (buttOn ? "both" : "belly") : "butt");
      }
    } else pressStartedAt = 0;
  } else {
    if (released) {
      if (releaseStartedAt == 0) releaseStartedAt = now;
      if (now - releaseStartedAt >= RELEASE_CONFIRM_MS) { squeezed = false; releaseStartedAt = 0; }
    } else {
      releaseStartedAt = 0;
      if (now - squeezedAt >= STUCK_REARM_MS) {       // long hold / sensor stays bent: new rest, one count only
        bellyBase = belly; if (USE_BUTT_SENSOR) buttBase = butt; squeezed = false;
      }
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
