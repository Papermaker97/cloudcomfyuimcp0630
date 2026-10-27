// Lab 3 (Serial Output from p5.js), Ppomo version: Arduino side
// p5.js sends a brightness as text, one number per line ("0" to "255"), and the LED shows it.
// The LED stands in for Ppomo's blushing cheek.
//
// Wiring: D5 - 220 ohm - LED long leg (+);  LED short leg (-) - GND
// (D5 can dim the LED with analogWrite)

const int ledPin = 5;

void setup() {
  Serial.begin(9600);
  Serial.setTimeout(10);          // don't wait long for the rest of a number
  pinMode(ledPin, OUTPUT);
}

void loop() {
  if (Serial.available() > 0) {   // something arrived from p5.js
    int brightness = Serial.parseInt();   // read the number, e.g. "128\n" -> 128
    brightness = constrain(brightness, 0, 255);
    analogWrite(ledPin, brightness);
  }
}
