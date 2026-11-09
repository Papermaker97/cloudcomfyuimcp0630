/*
  Ppomo sensor test, step 2: one squeeze = one event, with the MPRLS air-pressure sensor.

  Idea: the squeezed part of Ppomo (the butt) is a sealed air pocket (bulb / balloon / silicone cavity).
  A soft tube carries the air to the MPRLS, which sits in the head with the Arduino.
  So no wire has to go through the part that gets squeezed: only a tube.

  Wiring: same as step 1 (VIN->3.3V, GND->GND, SCL->A5, SDA->A4).

  Output, 20 times a second, one line:   delta,count
    delta = how much higher the pressure is than the resting air, in hPa
    count = number of squeezes so far
  Built-in LED is on while a squeeze is held.

  How it counts (hysteresis, like the FSR plan):
    a squeeze STARTS when delta goes above SQUEEZE_ON  -> count + 1 (only once)
    it ENDS when delta drops below SQUEEZE_OFF          -> ready for the next squeeze
  Holding a squeeze does not add more counts.

  Tune SQUEEZE_ON / SQUEEZE_OFF after watching step 1: set ON to about half of a normal squeeze's rise.
  Written with help from Claude.
*/
#include <Wire.h>
#include "Adafruit_MPRLS.h"

Adafruit_MPRLS mpr = Adafruit_MPRLS(-1, -1);

const float SQUEEZE_ON  = 8.0;    // hPa above rest that counts as a squeeze (tune this)
const float SQUEEZE_OFF = 3.0;    // hPa above rest that counts as released (lower than ON)
const float DRIFT = 0.01;         // how fast the "rest" value follows slow changes (weather, warming air)

float rest = 0;                   // resting pressure (the baseline)
bool squeezing = false;
unsigned long count = 0;

void setup() {
  Serial.begin(9600);
  pinMode(LED_BUILTIN, OUTPUT);
  if (!mpr.begin()) {
    while (true) {                // blink fast = sensor not found, check the 4 wires
      digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
      delay(100);
    }
  }
  // measure the resting pressure: don't touch Ppomo for the first second
  float sum = 0;
  for (int i = 0; i < 20; i++) {
    sum += mpr.readPressure();
    delay(50);
  }
  rest = sum / 20;
}

void loop() {
  float hPa = mpr.readPressure();
  if (isnan(hPa)) return;         // a failed read: skip it

  float delta = hPa - rest;

  if (!squeezing && delta > SQUEEZE_ON) {          // squeeze starts: one event
    squeezing = true;
    count++;
  } else if (squeezing && delta < SQUEEZE_OFF) {   // released: ready again
    squeezing = false;
  }
  if (!squeezing) rest += (hPa - rest) * DRIFT;    // only learn the resting value while not squeezed

  digitalWrite(LED_BUILTIN, squeezing ? HIGH : LOW);

  Serial.print(delta, 1);
  Serial.print(",");
  Serial.println(count);
  delay(50);
}
