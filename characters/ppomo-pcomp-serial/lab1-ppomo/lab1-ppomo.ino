// Lab 1 (Intro to Asynchronous Serial), Ppomo version
// Two analog sensors = Ppomo's belly and butt flex sensors, one digital input = a reset button.
// Sends one line per reading, values separated by commas:  belly,butt,button   e.g.  480,512,0
//
// Wiring (Nano 33 IoT is a 3.3 V board: use the 3.3V pin, never 5V)
//   3.3V - flex sensor (belly) -+- A0        3.3V - flex sensor (butt) -+- A1
//                               +- 10k - GND                            +- 10k - GND
//   3.3V - pushbutton -+- D2
//                      +- 10k - GND        (not pressed = 0, pressed = 1)

const int bellyPin = A0;
const int buttPin = A1;
const int buttonPin = 2;

void setup() {
  Serial.begin(9600);
  pinMode(buttonPin, INPUT);
}

void loop() {
  int belly = analogRead(bellyPin);     // 0 - 1023
  int butt = analogRead(buttPin);       // 0 - 1023
  int button = digitalRead(buttonPin);  // 0 or 1

  Serial.print(belly);
  Serial.print(",");
  Serial.print(butt);
  Serial.print(",");
  Serial.println(button);               // println ends the line, so the receiver knows one reading is done
  delay(10);
}
