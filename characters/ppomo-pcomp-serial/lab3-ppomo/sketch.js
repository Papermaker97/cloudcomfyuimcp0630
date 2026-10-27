// Lab 3 (Serial Output from p5.js), Ppomo version: p5.js side
// Click Ppomo on the screen to "squeeze" it: its cheeks blush, and the real LED on the Arduino
// lights up and fades out with them.
// Needs the p5.webserial library (see index.html). Click "Connect" and choose the Arduino port.

let port;
let connectBtn;
let blush = 0;           // 0 = no blush, 255 = fully pink
let lastSent = -1;       // the last brightness we sent, so we only send when it changes

function setup() {
  createCanvas(400, 400);
  port = createSerial();

  let usedPorts = usedSerialPorts();
  if (usedPorts.length > 0) {
    port.open(usedPorts[0], 9600);
  }

  connectBtn = createButton('Connect');
  connectBtn.position(20, 420);
  connectBtn.mousePressed(connectBtnClick);
}

function draw() {
  background(244, 236, 232);
  drawPpomo(width / 2, height / 2, 220, blush);

  blush = blush * 0.95;                  // the blush fades a little every frame
  if (blush < 1) blush = 0;

  let brightness = int(blush);
  if (port.opened() && brightness !== lastSent) {
    port.write(brightness + '\n');       // send it as text, one number per line
    lastSent = brightness;
  }

  fill(46, 43, 42);
  noStroke();
  textSize(16);
  text('click Ppomo · LED: ' + brightness, 20, 30);
  connectBtn.html(port.opened() ? 'Disconnect' : 'Connect');
}

function mousePressed() {
  // only count clicks on Ppomo's body
  if (dist(mouseX, mouseY, width / 2, height / 2) < 110) {
    blush = 255;
  }
}

function connectBtnClick() {
  if (!port.opened()) {
    port.open('Arduino', 9600);
  } else {
    port.close();
  }
}

// a front-facing Ppomo; b (0-255) is how pink the cheeks are
function drawPpomo(x, y, s, b) {
  push();
  translate(x, y);
  noStroke();
  fill('#B9BDC7');
  circle(-s * 0.28, -s * 0.33, s * 0.24);                // ears
  circle(s * 0.28, -s * 0.33, s * 0.24);
  ellipse(0, 0, s, s * 0.8);                             // body
  fill(244, 163, 184, 60 + b * 0.75);                    // cheeks get pinker with b
  let c = 1 + b / 255 * 0.3;                             // and a little bigger
  ellipse(-s * 0.27, s * 0.1, s * 0.34 * c, s * 0.28 * c);
  ellipse(s * 0.27, s * 0.1, s * 0.34 * c, s * 0.28 * c);
  fill('#3A3A3E');
  circle(-s * 0.1, -s * 0.03, s * 0.06);                 // eyes
  circle(s * 0.1, -s * 0.03, s * 0.06);
  noFill();
  stroke('#3A3A3E');
  strokeWeight(2);
  arc(-s * 0.03, s * 0.05, s * 0.06, s * 0.06, 0, PI);   // mouth (ω)
  arc(s * 0.03, s * 0.05, s * 0.06, s * 0.06, 0, PI);
  pop();
}
