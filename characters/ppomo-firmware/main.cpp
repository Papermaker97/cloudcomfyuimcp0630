#include <Arduino.h>
#include <Preferences.h>

// Ppomo firmware (XIAO ESP32-C3, two FSR 402 pads, coin vibration motor via AO3400A).
// Based on the Schematik version; same pins, timings and messages. Changes are marked "FIX".

constexpr int BELLY_FSR_PIN = 3;
constexpr int BUTT_FSR_PIN = 4;
constexpr int MOTOR_PIN = 5;

// Tune these two values after fitting the sensors under their foam load spreaders.
constexpr int PRESS_DELTA = 260;
constexpr int RELEASE_DELTA = 120;
constexpr uint32_t PRESS_CONFIRM_MS = 40;
constexpr uint32_t RELEASE_CONFIRM_MS = 120;
constexpr uint32_t VIBRATE_MS = 75;
constexpr uint32_t SAMPLE_MS = 10;
constexpr uint32_t CALIBRATION_MS = 1000;

// FIX: baseline tracking. Upward drift is followed slowly and only while the pad is truly at rest
// (within RELEASE_DELTA), so a slow squeeze can't drag the baseline up with it. Readings below the
// baseline mean less load than before (foam recovered), so the baseline follows them down quickly.
constexpr float BASELINE_UP_TAU_MS = 20000.0f;   // ~20 s to follow slow upward creep
constexpr float BASELINE_DOWN_TAU_MS = 200.0f;   // ~0.2 s to follow a lower resting value
// FIX: if a squeeze never "releases" (hand held still, or foam stays compressed), re-arm after this
// long by taking the current reading as the new resting value. Still only one count for the hold.
constexpr uint32_t STUCK_REARM_MS = 4000;

Preferences preferences;
uint32_t squeezeCount = 0;
float bellyBaseline = 0;   // FIX: float, so small drift isn't lost to integer rounding
float buttBaseline = 0;
bool squeezed = false;
uint32_t pressStartedAt = 0;
uint32_t releaseStartedAt = 0;
uint32_t squeezedAt = 0;
bool motorOn = false;
uint32_t motorOnAt = 0;
uint32_t lastSampleAt = 0;

int readFiltered(int pin) {
  // Median-of-three rejects an isolated ADC spike without adding noticeable lag.
  int a = analogRead(pin);
  int b = analogRead(pin);
  int c = analogRead(pin);
  if (a > b) { int t = a; a = b; b = t; }
  if (b > c) { int t = b; b = c; c = t; }
  if (a > b) { int t = a; a = b; b = t; }
  return b;
}

void sendEvent(const char *source) {
  Serial.print("{\"type\":\"squeeze\",\"count\":");
  Serial.print(squeezeCount);
  Serial.print(",\"source\":\"");
  Serial.print(source);
  Serial.println("\"}");
}

void calibrateBaselines() {
  uint32_t started = millis();
  uint32_t samples = 0;
  uint32_t bellyTotal = 0;
  uint32_t buttTotal = 0;
  while (millis() - started < CALIBRATION_MS) {
    bellyTotal += readFiltered(BELLY_FSR_PIN);
    buttTotal += readFiltered(BUTT_FSR_PIN);
    samples++;
    delay(10);
  }
  bellyBaseline = (float)bellyTotal / samples;
  buttBaseline = (float)buttTotal / samples;
}

// FIX: follow the resting value without chasing a squeeze in progress
void trackBaseline(float &baseline, int value) {
  if (value < baseline) {
    baseline += (value - baseline) * (SAMPLE_MS / BASELINE_DOWN_TAU_MS);
  } else if (value <= baseline + RELEASE_DELTA) {
    baseline += (value - baseline) * (SAMPLE_MS / BASELINE_UP_TAU_MS);
  }
  // above RELEASE_DELTA: someone may be pressing, leave the baseline alone
}

void setup() {
  pinMode(MOTOR_PIN, OUTPUT);
  digitalWrite(MOTOR_PIN, LOW);
  analogReadResolution(12);
  Serial.begin(115200);
  delay(200);

  preferences.begin("ppomo", false);
  squeezeCount = preferences.getULong("count", 0);
  calibrateBaselines();

  Serial.print("{\"type\":\"ready\",\"count\":");
  Serial.print(squeezeCount);
  Serial.println("}");
}

void loop() {
  const uint32_t now = millis();
  // FIX: elapsed-time comparison stays correct when millis() wraps (~49 days)
  if (motorOn && now - motorOnAt >= VIBRATE_MS) {
    digitalWrite(MOTOR_PIN, LOW);
    motorOn = false;
  }

  if (now - lastSampleAt < SAMPLE_MS) {
    delay(1);
    return;
  }
  lastSampleAt = now;

  const int belly = readFiltered(BELLY_FSR_PIN);
  const int butt = readFiltered(BUTT_FSR_PIN);
  const bool bellyPressed = belly >= bellyBaseline + PRESS_DELTA;
  const bool buttPressed = butt >= buttBaseline + PRESS_DELTA;
  const bool anyPressed = bellyPressed || buttPressed;
  const bool bothReleased = belly <= bellyBaseline + RELEASE_DELTA &&
                            butt <= buttBaseline + RELEASE_DELTA;

  if (!squeezed) {
    trackBaseline(bellyBaseline, belly);
    trackBaseline(buttBaseline, butt);

    if (anyPressed) {
      if (pressStartedAt == 0) pressStartedAt = now;
      if (now - pressStartedAt >= PRESS_CONFIRM_MS) {
        squeezed = true;
        squeezedAt = now;
        pressStartedAt = 0;
        releaseStartedAt = 0;
        squeezeCount++;
        preferences.putULong("count", squeezeCount); // Commit each event before notifying the app.
        digitalWrite(MOTOR_PIN, HIGH);
        motorOn = true;
        motorOnAt = now;
        sendEvent(bellyPressed ? (buttPressed ? "both" : "belly") : "butt");
      }
    } else {
      pressStartedAt = 0;
    }
  } else {
    // A count cannot happen again until every sensor has been quietly released.
    if (bothReleased) {
      if (releaseStartedAt == 0) releaseStartedAt = now;
      if (now - releaseStartedAt >= RELEASE_CONFIRM_MS) {
        squeezed = false;
        releaseStartedAt = 0;
      }
    } else {
      releaseStartedAt = 0;
      // FIX: never get stuck. A long hold or foam that stays compressed becomes the new resting value;
      // when the pad later relaxes below it, trackBaseline() follows it back down quickly.
      if (now - squeezedAt >= STUCK_REARM_MS) {
        bellyBaseline = belly;
        buttBaseline = butt;
        squeezed = false;
      }
    }
  }

  delay(1);
}
