/*
  Ppomo sensor test, step 1: is the MPRLS alive?

  Board: Arduino Nano 33 IoT (3.3 V)
  Sensor: Adafruit MPRLS ported pressure sensor, 0-25 PSI (borrowed from Tom)

  Wiring (4 wires, nothing else):
    MPRLS VIN -> Nano 3.3V
    MPRLS GND -> Nano GND
    MPRLS SCL -> Nano A5 (SCL)
    MPRLS SDA -> Nano A4 (SDA)
    RST, EOC, 3Vo -> leave unconnected

  What you should see (Tools > Serial Monitor or Serial Plotter, 9600 baud):
    about 1000-1020 hPa just sitting there (that is normal room air pressure),
    and the number goes up while you gently squeeze a bulb / balloon on the metal port.

  Library: "Adafruit MPRLS Library" (Library Manager; it also installs Adafruit BusIO).
  Based on Adafruit's mprls_simpletest example. Written with help from Claude.
*/
#include <Wire.h>
#include "Adafruit_MPRLS.h"

Adafruit_MPRLS mpr = Adafruit_MPRLS(-1, -1);   // no reset pin, no EOC pin

void setup() {
  Serial.begin(9600);
  while (!Serial) {}                     // wait for the Serial Monitor (Nano 33 IoT has native USB)
  if (!mpr.begin()) {
    Serial.println("MPRLS not found. Check: VIN->3.3V, GND->GND, SCL->A5, SDA->A4");
    while (true) delay(10);
  }
  Serial.println("MPRLS found");
}

void loop() {
  float hPa = mpr.readPressure();        // absolute pressure in hectopascals
  Serial.println(hPa);                   // one number per line: works in the Serial Plotter
  delay(100);
}
