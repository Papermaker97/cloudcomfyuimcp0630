// Lab 2 (Serial Input to p5.js), Ppomo version: p5.js side
// Squeeze the flex sensor: Ppomo's cheeks puff up with how hard you squeeze,
// and each full squeeze-and-release counts once.
// Needs the p5.webserial library (see index.html). Click "Connect" and choose the Arduino port.

// Write down your own numbers from the Serial Monitor first:
const REST = 480;        // sensor value when you are not touching it
const SQUEEZED = 720;    // sensor value when you squeeze hard
const PRESS_AT = 650;    // crossing this upward counts a squeeze
const RELEASE_AT = 550;  // must come back below this before the next squeeze can count

let port;
let connectBtn;
let sensor = 0;          // latest number from the Arduino
let puff = 1;            // cheek size: 1 = normal, 1.6 = fully puffed
let squeezed = false;    // are we in the middle of a squeeze?
let count = 0;           // how many squeezes so far

function setup() {
  createCanvas(400, 400);
  port = createSerial();

  // if this port was used before, reconnect to it automatically
  let usedPorts = usedSerialPorts();
  if (usedPorts.length > 0) {
    port.open(usedPorts[0], 9600);
  }

  connectBtn = createButton('Connect');
  connectBtn.position(20, 420);
  connectBtn.mousePressed(connectBtnClick);
}

function draw() {
  // read one line ("480\n") if a whole line has arrived
  let line = port.readUntil('\n');
  if (line.length > 0) {
    sensor = Number(line.trim());
    handleSensor(sensor);
  }

  background(244, 236, 232);
  drawPpomo(width / 2, height / 2, 220, puff);

  fill(46, 43, 42);
  noStroke();
  textSize(16);
  text('sensor: ' + sensor, 20, 30);
  text('squeezes: ' + count, 20, 52);

  connectBtn.html(port.opened() ? 'Disconnect' : 'Connect');
}

function handleSensor(value) {
  // cheek size follows how hard you squeeze (the last "true" keeps it between 1 and 1.6)
  puff = map(value, REST, SQUEEZED, 1, 1.6, true);

  // count once per squeeze: up past PRESS_AT, then back below RELEASE_AT
  if (!squeezed && value > PRESS_AT) {
    squeezed = true;
    count = count + 1;
  }
  if (squeezed && value < RELEASE_AT) {
    squeezed = false;
  }
}

function connectBtnClick() {
  if (!port.opened()) {
    port.open('Arduino', 9600);
  } else {
    port.close();
  }
}

// a front-facing Ppomo; p scales the cheeks
function drawPpomo(x, y, s, p) {
  push();
  translate(x, y);
  noStroke();
  fill('#B9BDC7');
  circle(-s * 0.28, -s * 0.33, s * 0.24);                      // ears
  circle(s * 0.28, -s * 0.33, s * 0.24);
  ellipse(0, 0, s, s * 0.8);                                   // body
  fill('#F4A3B8');
  ellipse(-s * 0.27, s * 0.1, s * 0.34 * p, s * 0.28 * p);     // cheeks
  ellipse(s * 0.27, s * 0.1, s * 0.34 * p, s * 0.28 * p);
  fill('#3A3A3E');
  circle(-s * 0.1, -s * 0.03, s * 0.06);                       // eyes
  circle(s * 0.1, -s * 0.03, s * 0.06);
  noFill();
  stroke('#3A3A3E');
  strokeWeight(2);
  arc(-s * 0.03, s * 0.05, s * 0.06, s * 0.06, 0, PI);         // mouth (ω)
  arc(s * 0.03, s * 0.05, s * 0.06, s * 0.06, 0, PI);
  pop();
}
