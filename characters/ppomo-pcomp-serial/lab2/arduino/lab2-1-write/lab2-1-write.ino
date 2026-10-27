// Lab 2, step 1: send one sensor as ONE raw byte (0-255) with Serial.write().
// Same as the lab code. In our wiring A0 is the FSR (Ppomo squeeze).
// To use the potentiometer instead, change A0 to A1.

void setup() {
  Serial.begin(9600); // initialize serial communications
}

void loop() {
  // read the input pin:
  int potentiometer = analogRead(A0);
  // remap the pot value to fit in 1 byte:
  int mappedPot = map(potentiometer, 0, 1023, 0, 255);
  // print it out the serial port:
  Serial.write(mappedPot);
  // slight delay to stabilize the ADC:
  delay(1);
}
