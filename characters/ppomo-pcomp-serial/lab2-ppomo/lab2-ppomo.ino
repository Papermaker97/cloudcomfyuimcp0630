// Lab 2 (Serial Input to p5.js), Ppomo version: Arduino side
// Sends the belly flex sensor (or a potentiometer) as one number per line, e.g. 480
//
// Wiring: 3.3V - flex sensor -+- A0
//                             +- 10k - GND
// (a potentiometer works the same: outer legs to 3.3V and GND, middle leg to A0)

void setup() {
  Serial.begin(9600);
}

void loop() {
  int sensor = analogRead(A0);   // 0 - 1023
  Serial.println(sensor);
  delay(10);
}
