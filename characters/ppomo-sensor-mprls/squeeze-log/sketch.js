/*
  Ppomo squeeze log (p5.js + p5.webserial)
  Reads "delta,count" from the Arduino. Every new squeeze is written down with the date and time
  from this computer. "Save CSV" downloads the whole list.
  Use Chrome. Close the Arduino Serial Monitor first, then click "choose port".
  Written with help from Claude.
*/
const serial = new p5.WebSerial();
let portButton, saveButton, clearButton;
let delta = 0;             // pressure rise right now (hPa)
let lastCount = 0;         // the Arduino's count we have already logged
let log = [];              // every squeeze: { n, date, time }
let history = [];          // recent pressure for the small graph
let maxSeen = 20;

function setup() {
  createCanvas(480, 560);
  if (!navigator.serial) alert("Web Serial does not work in this browser. Use Chrome.");
  navigator.serial.addEventListener("connect", () => serial.getPorts());
  navigator.serial.addEventListener("disconnect", () => serial.close());
  serial.getPorts();
  serial.on("noport", makePortButton);
  serial.on("portavailable", openPort);
  serial.on("requesterror", (err) => alert("Serial port error: " + err));
  serial.on("data", serialEvent);
  serial.on("close", makePortButton);

  saveButton = createButton("Save CSV");
  saveButton.mousePressed(saveLog);
  clearButton = createButton("Clear");
  clearButton.mousePressed(() => { log = []; });
}

function draw() {
  background(251, 246, 241);
  noStroke();
  fill(90, 52, 36);

  // total
  textAlign(CENTER);
  textSize(16);
  text("squeezes", width / 2, 48);
  textSize(72);
  text(log.length, width / 2, 120);

  // pressure graph (to check the sensor and tune the thresholds)
  maxSeen = max(maxSeen, delta * 1.2);
  noFill();
  stroke(233, 154, 166);
  strokeWeight(2);
  beginShape();
  for (let i = 0; i < history.length; i++) {
    vertex(map(i, 0, 199, 20, width - 20), map(history[i], 0, maxSeen, 230, 150, true));
  }
  endShape();
  stroke(210, 190, 180);
  strokeWeight(1);
  line(20, 230, width - 20, 230);
  noStroke();
  fill(140, 110, 100);
  textSize(12);
  textAlign(LEFT);
  text(`pressure rise ${delta.toFixed(1)} hPa`, 20, 250);

  // the newest squeezes, newest first
  fill(90, 52, 36);
  textSize(14);
  text("#      date              time", 40, 290);
  const shown = log.slice(-12).reverse();
  for (let i = 0; i < shown.length; i++) {
    const e = shown[i];
    text(`${e.n}`, 40, 318 + i * 20);
    text(e.date, 90, 318 + i * 20);
    text(e.time, 220, 318 + i * 20);
  }
}

function serialEvent() {
  let line = serial.readLine();
  while (line) {
    const parts = trim(line).split(",");
    if (parts.length === 2 && !isNaN(Number(parts[1]))) {
      delta = Number(parts[0]);
      const count = Number(parts[1]);
      if (count < lastCount) lastCount = 0;       // the Arduino restarted: its count began again
      while (lastCount < count) {                 // one log line per new squeeze
        lastCount++;
        addSqueeze();
      }
      history.push(delta);
      if (history.length > 200) history.shift();
    }
    line = serial.readLine();
  }
}

function addSqueeze() {
  const d = new Date();
  const two = (v) => String(v).padStart(2, "0");
  log.push({
    n: log.length + 1,
    date: `${d.getFullYear()}-${two(d.getMonth() + 1)}-${two(d.getDate())}`,
    time: `${two(d.getHours())}:${two(d.getMinutes())}:${two(d.getSeconds())}`,
  });
}

function saveLog() {
  const table = new p5.Table();
  table.addColumn("n");
  table.addColumn("date");
  table.addColumn("time");
  for (const e of log) {
    const row = table.addRow();
    row.setNum("n", e.n);
    row.setString("date", e.date);
    row.setString("time", e.time);
  }
  saveTable(table, "ppomo-squeezes.csv");
}

function makePortButton() {
  portButton = createButton("choose port");
  portButton.mousePressed(() => serial.requestPort());
}

function openPort() {
  serial.open().then(() => console.log("port open"));
  if (portButton) portButton.hide();
}
