// Lab 1, step 1: read one analog sensor and print it as readable text.
// A0 = FSR (Ppomo's squeeze). Serial Monitor shows 0 - 1023, one number per line.

void setup() {
  Serial.begin(9600);
}

void loop() {
  int analogValue = analogRead(A0);
  Serial.println(analogValue);
}
