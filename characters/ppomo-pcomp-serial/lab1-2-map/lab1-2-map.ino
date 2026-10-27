// Lab 1, step 2: scale 0 - 1023 down to 0 - 255 so it fits in one byte.
// Serial Monitor shows 0 - 255.

void setup() {
  Serial.begin(9600);
}

void loop() {
  int analogValue = analogRead(A0);
  int mappedValue = map(analogValue, 0, 1023, 0, 255);
  Serial.println(mappedValue);
}
