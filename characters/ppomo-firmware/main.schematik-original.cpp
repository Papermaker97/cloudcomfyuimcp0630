#include <Arduino.h>
#include <Preferences.h>

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

Preferences preferences;
uint32_t squeezeCount = 0;
int bellyBaseline = 0;
int buttBaseline = 0;
bool squeezed = false;
uint32_t pressStartedAt = 0;
uint32_t releaseStartedAt = 0;
uint32_t motorOffAt = 0;
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
  bellyBaseline = bellyTotal / samples;
  buttBaseline = buttTotal / samples;
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
  if (motorOffAt != 0 && now >= motorOffAt) {
    digitalWrite(MOTOR_PIN, LOW);
    motorOffAt = 0;
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
    // Adapt slowly only while free: this follows temperature/foam creep, not a hand squeeze.
    if (!anyPressed) {
      bellyBaseline = (bellyBaseline * 63 + belly) / 64;
      buttBaseline = (buttBaseline * 63 + butt) / 64;
    }

    if (anyPressed) {
      if (pressStartedAt == 0) pressStartedAt = now;
      if (now - pressStartedAt >= PRESS_CONFIRM_MS) {
        squeezed = true;
        pressStartedAt = 0;
        releaseStartedAt = 0;
        squeezeCount++;
        preferences.putULong("count", squeezeCount); // Commit each event before notifying the app.
        digitalWrite(MOTOR_PIN, HIGH);
        motorOffAt = now + VIBRATE_MS;
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
    }
  }

  delay(1);
}