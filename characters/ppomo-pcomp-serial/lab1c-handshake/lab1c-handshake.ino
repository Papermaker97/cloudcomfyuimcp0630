// Lab 1, Part C: call and response (handshaking)
// The Arduino says "hello" until the computer sends any character.
// After that it sends exactly one reading (fsr,pot,button) each time a character arrives.
// Same wiring as Part B.

const int fsrPin = A0;
const int potPin = A1;
const int buttonPin = 2;

void setup() {
  Serial.begin(9600);
  pinMode(buttonPin, INPUT);
  while (Serial.available() <= 0) {   // nothing received yet
    Serial.println("hello");          // keep asking
    delay(300);
  }
}

void loop() {
  if (Serial.available() > 0) {       // the computer sent something
    Serial.read();                    // take that character out of the buffer
    int fsr = analogRead(fsrPin);
    int pot = analogRead(potPin);
    int button = digitalRead(buttonPin);
    Serial.print(fsr);
    Serial.print(",");
    Serial.print(pot);
    Serial.print(",");
    Serial.println(button);
  }
}
