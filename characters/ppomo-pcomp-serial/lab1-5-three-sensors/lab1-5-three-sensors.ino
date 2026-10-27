// Lab 1, step 5: send three sensors as one comma-separated line (punctuation).
//   A0 = FSR (squeeze), A1 = potentiometer, D2 = pushbutton
// Example:  812,512,0   ->  squeezing, knob in the middle, button not pressed

const int switchPin = 2;     // digital input

void setup() {
  Serial.begin(9600);
  pinMode(switchPin, INPUT);
}

void loop() {
  int sensorValue = analogRead(A0);   // FSR
  Serial.print(sensorValue);
  Serial.print(",");

  sensorValue = analogRead(A1);       // potentiometer
  Serial.print(sensorValue);
  Serial.print(",");

  sensorValue = digitalRead(switchPin);  // button: 0 or 1
  Serial.println(sensorValue);        // println = this reading is finished
}
