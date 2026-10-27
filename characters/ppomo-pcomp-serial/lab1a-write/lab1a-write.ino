// Lab 1, Part A: send one sensor as a raw byte with Serial.write()
// The Serial Monitor will show strange characters (or nothing). That is expected:
// write() sends the number itself as one byte, not as readable digits.
// FSR on A0:  3.3V - FSR -+- A0
//                         +- 10k - GND

void setup() {
  Serial.begin(9600);
}

void loop() {
  int analogValue = analogRead(A0) / 4;   // 0-1023 divided by 4 = 0-255, so it fits in one byte
  Serial.write(analogValue);              // send that one byte
  delay(10);
}
