/*
  Ppomo squeeze amount (Arduino Nano 33 IoT + Adafruit MPRLS)

  No counting here. The board only sends how hard the bulb is squeezed, 50 times a second:
    one line = delta   (hPa above resting air, e.g. "12.4")
  The p5 page adds up the pressure over time (squeeze amount), so a quick tap, many fast taps
  and one long hard press are all measured, which counting missed.

  Wiring: MPRLS VIN -> 3.3V, GND -> GND, SCL -> A5, SDA -> A4. Leave 3Vo, EOC, RST empty.
  Rubber bulb -> silicone tube -> the sensor's metal port.
  Don't touch the bulb for the first second after upload (it learns the resting pressure).
  Library: "Adafruit MPRLS Library". Written with help from Claude.
*/
#include <Wire.h>
#include "Adafruit_MPRLS.h"

Adafruit_MPRLS mpr = Adafruit_MPRLS(-1, -1);

const unsigned long PERIOD = 20;  // ms between readings (50 per second)
const float RESTING = 1.0;        // hPa: below this the bulb counts as untouched
const float DRIFT = 0.01;         // how fast the resting value follows slow changes (warm hands, weather)

float rest = 0;
unsigned long nextRead = 0;

void setup() {
  Serial.begin(9600);
  pinMode(LED_BUILTIN, OUTPUT);
  if (!mpr.begin()) {
    while (true) {                // fast blink = sensor not found: check the 4 wires
      Serial.println("MPRLS not found. Check VIN->3.3V, GND->GND, SCL->A5, SDA->A4");
      digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
      delay(200);
    }
  }
  float sum = 0;                  // learn the resting pressure (about 1 second)
  for (int i = 0; i < 20; i++) {
    sum += mpr.readPressure();
    delay(50);
  }
  rest = sum / 20;
}

void loop() {
  if (millis() < nextRead) return;
  nextRead = millis() + PERIOD;

  float hPa = mpr.readPressure();
  if (isnan(hPa)) return;
  float delta = hPa - rest;
  if (delta < RESTING) rest += (hPa - rest) * DRIFT;   // only follow drift while nobody squeezes

  digitalWrite(LED_BUILTIN, delta > RESTING ? HIGH : LOW);
  Serial.println(delta, 1);
}
