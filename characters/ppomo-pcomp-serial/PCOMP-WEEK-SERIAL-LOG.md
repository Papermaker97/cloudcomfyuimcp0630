# PComp: Serial Communication Labs (Ppomo version)

**Project context:** I'm building **Ppomo**, a squishy companion toy. Every squeeze is recorded as an event, and the count shows up on a screen. For these labs I swapped the potentiometer on A0 for an **FSR (force-sensing resistor)**, which stands in for Ppomo's belly. This way the serial labs also became my first test of reading a squeeze and sending it to a computer.

> Status: I completed the **first section of Lab 1** and the **first half of Lab 2** (up to displaying the live sensor value in p5.js). The remaining sections are listed at the end.

---

## Parts
- Arduino Nano 33 IoT (3.3 V board)
- Solderless breadboard (60 rows), jumper wires
- FSR + 10 kΩ resistor, used as a voltage divider on **A0**
- Potentiometer on **A1**
- Pushbutton + 10 kΩ pull-down resistor on **D2**

## Wiring
- Nano **3V3 → red (voltage) bus**, Nano **GND → blue (ground) bus**. I didn't use 5V/VUSB because the Nano 33 IoT is a 3.3 V board.
- **FSR (A0):** one leg goes to 3.3 V. The other leg goes to A0 and, through a 10 kΩ resistor, to ground. More pressure means lower FSR resistance, which means a higher voltage on A0.
- **Potentiometer (A1):** the outer legs go to 3.3 V and ground, and the middle leg goes to A1.
- **Pushbutton (D2):** one side goes to 3.3 V. The other side goes to D2, with a 10 kΩ pull-down to ground.
- This is the same layout as Figure 11 in the Lab 1 page. The only change is that the A0 potentiometer is replaced with the FSR and its 10 kΩ resistor.

**Things I had to adjust on the real breadboard**
- The Nano 33 IoT has an antenna tab below its last pin row. I couldn't place the button right under the Nano, so I moved all the lower parts down a few rows.
- My potentiometer is a panel-mount type with 5 mm (0.2") leg spacing. I placed its legs one hole apart (every other row).

---

## Lab 1: Intro to Asynchronous Serial Communications

### What I did: read one analog sensor and print it as text
```cpp
void setup() {
  Serial.begin(9600);
}

void loop() {
  int analogValue = analogRead(A0);
  Serial.println(analogValue);
}
```
- `analogRead(A0)` turns the voltage on A0 into a number from **0 (0 V) to 1023 (3.3 V)**.
- `Serial.println()` sends that number as **ASCII text** followed by a carriage return and a newline (`\r\n`). That's why the Serial Monitor shows one readable number per line.

### Result
- With the FSR untouched, the Serial Monitor showed values near **0**. When I squeezed the FSR, the numbers rose immediately, and they dropped back when I let go.
- 🎥 Video: `IMG_1483.mov`, the Serial Monitor responding as I press the FSR.

### Problem I ran into
- My first upload failed with `redefinition of 'void setup()'`. A new Arduino sketch already contains empty `setup()` and `loop()` functions, and I had pasted my code below them, so each function existed twice. I selected everything (⌘A), deleted it, and pasted the code into an empty file. After that it compiled and uploaded.

---

## Lab 2: Serial Input to p5.js Using the p5.webserial Library

### Arduino: send the sensor as one raw byte
```cpp
void setup() {
  Serial.begin(9600); // initialize serial communications
}

void loop() {
  // read the input pin:
  int potentiometer = analogRead(A0);
  // remap the pot value to fit in 1 byte:
  int mappedPot = map(potentiometer, 0, 1023, 0, 255);
  // print it out the serial port:
  Serial.write(mappedPot);
  // slight delay to stabilize the ADC:
  delay(1);
}
```
- I used the lab code unchanged. In my wiring A0 is the FSR, so this sketch sends the squeeze value.
- `map()` scales 0–1023 down to 0–255. For example, 1023 → 255, 512 → 127, and 0 → 0.
- `Serial.write()` sends the value as **one raw byte**, not as text. A byte can only hold 0–255, which is why the value is mapped first.

### p5.js: include the library
In the p5.js web editor (Chrome, since WebSerial only works in Chrome/Edge), I added the library to `index.html` right after the p5.js script tag:
```html
<script src="https://unpkg.com/p5-webserial@0.1.1/build/p5.webserial.js"></script>
```
The web editor now defaults to p5.js v2 (2.3.4). The library loaded and worked fine with it.

### p5.js: open the port and display the value
I used the lab's sketch with the serial event callbacks, plus this `draw()` and `serialEvent()`:
```js
function draw() {
  background(0);
  fill(255);
  text("sensor value: " + inData, 30, 50);
}

function serialEvent() {
  inData = Number(serial.read());
  console.log(inData);
}
```
How the events work:

| Event | When it happens | Callback |
|---|---|---|
| `noport` | no port has been chosen yet | `makePortButton()` shows a "choose port" button |
| `portavailable` | a port was chosen, or Chrome remembered one | `openPort()` opens it and hides the button |
| `data` | new bytes arrive | `serialEvent()` stores the byte in `inData` |
| `close` | the port closes | `makePortButton()` |
| `requesterror` | choosing a port fails or is cancelled | `portError()` shows an alert |

### Result
- I clicked **choose port**, selected the Arduino NANO 33 IoT, and the sketch showed **`sensor value: 0`** at rest.
- When I pressed the FSR, the value rose (for example **142** and **214** in my video) and went back to 0 when I let go.
- 🎥 Video: `IMG_1484.mov`, the p5.js sketch updating live as I squeeze the FSR.

**The path of one squeeze:**
FSR pressed → `analogRead` ≈ 860 → `map` ≈ 214 → `Serial.write(214)` sends one byte → p5 `serial.read()` returns 214 → `draw()` shows "sensor value: 214".

### What I learned
- **Only one program can use a serial port at a time.** I had to close the Arduino Serial Monitor before p5 could connect. I also have to stop the p5 sketch before uploading new Arduino code.
- **`Serial.println()` (Lab 1) and `Serial.write()` (Lab 2) send different things.**
  - `println()` sends human-readable ASCII text.
  - `write()` sends a single raw byte.
  - The receiving side must read the data the same way it was sent: `serial.read()` for raw bytes, `serial.readLine()` for text lines.

---

## Connection to Ppomo
- This is the first working piece of Ppomo's data path: **squeeze → microcontroller → computer → screen.**
- **Winter Show goal:** when a person stands in front of the camera, a digital Ppomo appears perched on their head or belly. I plan to use body tracking such as ml5.js BodyPose for this. Each time they squeeze the physical Ppomo, the on-screen Ppomo's **cheeks, belly, or butt puff up.**
- **How this lab connects:** the FSR value tells p5.js when and how hard Ppomo is squeezed. Next, I'll set a threshold so that each time the value crosses it, one squeeze is counted. That count (or the pressure itself) will control how much the character inflates.
- In Lab 2's terms, the `inData` value I displayed today is the number that will eventually drive the size of Ppomo's cheeks and belly.

## Still to do
- **Lab 1:**
  - `map()` to 0–255
  - `Serial.write()` (raw bytes in the Serial Monitor)
  - sending the value in many formats (BIN/DEC/HEX/OCT)
  - sending all three sensors with punctuation (`fsr,pot,button`)
  - call-and-response handshaking
- **Lab 2:**
  - draw a graph of the sensor values
  - send ASCII with `println()` and read it with `serial.readLine()`
  - send the full 0–1023 range
- **Lab 3:** Serial output from p5.js

---

*Credit: The Arduino and p5.js code follows the ITP Physical Computing lab examples. The Ppomo adaptation, wiring layout, and this write-up were prepared with help from Claude.*
