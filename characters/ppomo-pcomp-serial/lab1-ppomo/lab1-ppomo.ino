// Lab 1, Part B (Intro to Asynchronous Serial), Ppomo version
// Two analog sensors + one digital input, sent as readable text, one line per reading:
//   fsr,pot,button      e.g.  0,512,0   (not touching)   812,512,0   (squeezing the FSR)
//   A0 = FSR (Ppomo's belly squeeze), A1 = potentiometer, D2 = pushbutton (reset)
//
// Wiring (Nano 33 IoT is a 3.3 V board: use the 3V3 pin, never 5V / VUSB)
//   3V3 - FSR -+- A0                       potentiometer: one outer leg - 3V3,
//              +- 10k - GND                               other outer leg - GND, middle leg - A1
//   3V3 - pushbutton -+- D2
//                     +- 10k - GND          (not pressed = 0, pressed = 1)

const int fsrPin = A0;
const int potPin = A1;
const int buttonPin = 2;

void setup() {
  Serial.begin(9600);
  pinMode(buttonPin, INPUT);
}

void loop() {
  int fsr = analogRead(fsrPin);         // 0 - 1023
  int pot = analogRead(potPin);         // 0 - 1023
  int button = digitalRead(buttonPin);  // 0 or 1

  Serial.print(fsr);
  Serial.print(",");
  Serial.print(pot);
  Serial.print(",");
  Serial.println(button);               // println ends the line, so the receiver knows one reading is done
  delay(10);
}
