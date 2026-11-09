/*
  Ppomo air squeeze test (p5.js + p5.webserial 0.1.1)
  Reads "delta,count" lines from step2_ppomo_squeeze.ino:
    top: a live graph of the pressure rise (hPa above rest)
    bottom: a Ppomo that squishes while you squeeze and puffs up a little with every counted squeeze
  The serial setup is the same as the PComp Serial Lab 2 sketches.
  Written with help from Claude.
*/
const serial = new p5.WebSerial();
let portButton;
let delta = 0;            // latest pressure rise, hPa
let count = 0;            // squeezes so far (counted on the Arduino)
let history = [];         // recent deltas for the graph
let maxSeen = 20;         // graph scale grows to fit the biggest squeeze
let puff = 0;             // smooth size boost from the count

function setup() {
  createCanvas(480, 520);
  if (!navigator.serial) alert("WebSerial is not supported in this browser. Try Chrome or Edge.");
  navigator.serial.addEventListener("connect", () => serial.getPorts());
  navigator.serial.addEventListener("disconnect", () => serial.close());
  serial.getPorts();
  serial.on("noport", makePortButton);
  serial.on("portavailable", openPort);
  serial.on("requesterror", (err) => alert("Serial port error: " + err));
  serial.on("data", serialEvent);
  serial.on("close", makePortButton);
}

function draw() {
  background(251, 246, 241);

  // ---- graph of the pressure rise ----
  maxSeen = max(maxSeen, delta * 1.2);
  noFill();
  stroke(233, 154, 166);
  strokeWeight(2);
  beginShape();
  for (let i = 0; i < history.length; i++) {
    vertex(map(i, 0, 199, 20, width - 20), map(history[i], 0, maxSeen, 180, 30, true));
  }
  endShape();
  stroke(200, 180, 170);
  strokeWeight(1);
  line(20, 180, width - 20, 180);
  noStroke();
  fill(90, 52, 36);
  textSize(14);
  text(`pressure rise: ${delta.toFixed(1)} hPa`, 20, 22);

  // ---- Ppomo ----
  puff = lerp(puff, min(count, 20) * 0.03, 0.1);            // +3% per squeeze, up to 20 squeezes
  const squash = constrain(delta / maxSeen, 0, 1) * 0.25;    // flatter while squeezed
  const w = 220 * (1 + puff) * (1 + squash);
  const h = 150 * (1 + puff) * (1 - squash);
  const cx = width / 2, floorY = 470;
  fill(242, 182, 194);
  ellipse(cx, floorY - h / 2, w, h);                         // body
  fill(251, 240, 218);
  ellipse(cx, floorY - h * 0.18, w * 0.7, h * 0.32);         // cream belly
  fill(238, 152, 170, 160);
  ellipse(cx - w * 0.26, floorY - h * 0.42, 40 + puff * 60, 26 + puff * 40);   // cheeks
  ellipse(cx + w * 0.26, floorY - h * 0.42, 40 + puff * 60, 26 + puff * 40);
  fill(74, 46, 36);
  ellipse(cx - w * 0.16, floorY - h * 0.55, 9, 10);           // eyes
  ellipse(cx + w * 0.16, floorY - h * 0.55, 9, 10);

  fill(90, 52, 36);
  textSize(18);
  textAlign(CENTER);
  text(`squeezes: ${count}`, cx, 505);
  textAlign(LEFT);
}

function serialEvent() {
  // read every complete line that has arrived, keep the newest
  let line = serial.readLine();
  while (line) {
    const parts = trim(line).split(",");
    if (parts.length === 2) {
      delta = Number(parts[0]);
      count = Number(parts[1]);
      history.push(delta);
      if (history.length > 200) history.shift();
    }
    line = serial.readLine();
  }
}

function makePortButton() {
  portButton = createButton("choose port");
  portButton.position(10, 10);
  portButton.mousePressed(() => serial.requestPort());
}

function openPort() {
  serial.open().then(() => console.log("port open"));
  if (portButton) portButton.hide();
}
