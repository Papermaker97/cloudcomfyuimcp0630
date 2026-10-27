// Lab 1, step 4: send the same value in many formats on one line.
// Example line for 226:   â	11100010	226	E2	342
//                         raw  binary   decimal hex octal

void setup() {
  Serial.begin(9600);
}

void loop() {
  int analogValue = analogRead(A0);
  int mappedValue = map(analogValue, 0, 1023, 0, 255);

  Serial.write(mappedValue);        // raw byte
  Serial.print("\t");               // tab
  Serial.print(mappedValue, BIN);   // binary
  Serial.print("\t");
  Serial.print(mappedValue, DEC);   // decimal
  Serial.print("\t");
  Serial.print(mappedValue, HEX);   // hexadecimal
  Serial.print("\t");
  Serial.print(mappedValue, OCT);   // octal
  Serial.println();                 // end of line: \r\n
}
