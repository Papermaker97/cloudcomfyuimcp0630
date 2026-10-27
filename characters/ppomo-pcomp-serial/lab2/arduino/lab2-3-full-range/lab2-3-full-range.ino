// Lab 2, step 7 (the lab's challenge): send the full 0-1023 range as ASCII text.
// No map() any more: println can send any number, not just one byte.

void setup() {
  Serial.begin(9600); // initialize serial communications
}

void loop() {
  int potentiometer = analogRead(A0);  // 0 - 1023 (A0 = FSR in our wiring)
  Serial.println(potentiometer);       // e.g. "812\r\n"
  delay(1);
}
