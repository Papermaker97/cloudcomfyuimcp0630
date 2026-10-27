// Lab 1, step 6: call and response (handshaking).
// The Arduino says "hello" until the computer sends any byte.
// After that it sends exactly one line (fsr,pot,button) for every byte it receives.
// Set the Serial Monitor line ending to "No Line Ending" so one Send = one reading.

const int switchPin = 2;
int sensorValue = 0;

void setup() {
  Serial.begin(9600);
  pinMode(switchPin, INPUT);
  while (Serial.available() <= 0) {   // nothing received yet
    Serial.println("hello");          // keep asking
    delay(300);
  }
}

void loop() {
  if (Serial.available() > 0) {       // the computer sent something
    int inByte = Serial.read();       // take that byte out of the buffer

    sensorValue = analogRead(A0);
    Serial.print(sensorValue);
    Serial.print(",");

    sensorValue = analogRead(A1);
    Serial.print(sensorValue);
    Serial.print(",");

    sensorValue = digitalRead(switchPin);
    Serial.println(sensorValue);
  }
}
