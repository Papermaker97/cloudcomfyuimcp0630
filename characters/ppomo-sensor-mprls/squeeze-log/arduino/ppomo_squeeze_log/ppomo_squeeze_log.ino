/*
  Ppomo squeeze counter (Arduino Nano 33 IoT + Adafruit MPRLS)

  Wiring: MPRLS VIN -> 3.3V, GND -> GND, SCL -> A5, SDA -> A4. Leave 3Vo, EOC, RST empty.
  Rubber bulb -> silicone tube -> the sensor's metal port.

  Sends one line 20 times a second:  delta,count
    delta = how far the pressure is above resting air (hPa)
    count = squeezes counted since the board started
  The p5 page adds the date and time to every squeeze.

  Don't touch the bulb for the first second after upload (it learns the resting pressure).
  Library: "Adafruit MPRLS Library". Written with help from Claude.
*/
#include <Wire.h>
#include "Adafruit_MPRLS.h"

Adafruit_MPRLS mpr = Adafruit_MPRLS(-1, -1);

const float SQUEEZE_ON  = 8.0;   // hPa: above this = squeezed      (lower it if squeezes are missed)
const float SQUEEZE_OFF = 3.0;   // hPa: below this = let go         (keep it smaller than SQUEEZE_ON)
const float DRIFT = 0.01;        // how fast the resting value follows slow changes (warm hands, weather)

float rest = 0;
bool squeezing = false;
unsigned long count = 0;

void setup() {
  Serial.begin(9600);
  pinMode(LED_BUILTIN, OUTPUT);
  if (!mpr.begin()) {
    while (true) {               // fast blink = sensor not found: check the 4 wires
      Serial.println("MPRLS not found. Check VIN->3.3V, GND->GND, SCL->A5, SDA->A4");
      digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
      delay(200);
    }
  }
  float sum = 0;                 // learn the resting pressure (about 1 second)
  for (int i = 0; i < 20; i++) {
    sum += mpr.readPressure();
    delay(50);
  }
  rest = sum / 20;
}

void loop() {
  float hPa = mpr.readPressure();
  if (isnan(hPa)) return;

  float delta = hPa - rest;
  if (!squeezing && delta > SQUEEZE_ON) {          // a new squeeze: count it once
    squeezing = true;
    count++;
  } else if (squeezing && delta < SQUEEZE_OFF) {   // let go: ready for the next one
    squeezing = false;
  }
  if (!squeezing) rest += (hPa - rest) * DRIFT;

  digitalWrite(LED_BUILTIN, squeezing ? HIGH : LOW);
  Serial.print(delta, 1);
  Serial.print(",");
  Serial.println(count);
  delay(50);
}
