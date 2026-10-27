// Lab 1, step 3: send the value as ONE raw byte with Serial.write().
// The Serial Monitor shows garbage characters. That is expected:
// write(32) sends the byte 32, which the monitor draws as a space ' '.
// println(32) would send 4 bytes: '3' '2' '\r' '\n'  (51, 50, 13, 10).

void setup() {
  Serial.begin(9600);
}

void loop() {
  int analogValue = analogRead(A0);
  int mappedValue = map(analogValue, 0, 1023, 0, 255);
  Serial.write(mappedValue);
}
