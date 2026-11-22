/*
  Ppomo squeeze amount (p5.js + p5.webserial)

  Counting squeezes missed quick taps and long presses, but the pressure itself is measured well.
  So this page does not count. It adds up how much you squeezed over time:
    squeeze amount = (pressure above resting) x (how long), in hPa·s
  A light tap adds a little, a long hard press adds a lot, ten fast taps add ten small amounts.

  Three views
    NOW            the last 15 seconds of pressure, live (you see your own squeeze)
    LAST 10 MIN    one bar per 10 seconds (each person's turn shows up as a bump)
    TODAY          one bar per 30 minutes, midnight to midnight (when in the day you squeezed, and how much)

  The day is kept in this browser (refresh-safe) and S saves it as a CSV: date, time, amount (one row per second).
  Uses the Arduino sketch ppomo_squeeze_amount (one number per line, 50 per second). Use Chrome.

  Keys (for me): P choose port   S save CSV   F fullscreen   R clear today   hold SPACE = fake squeeze (no sensor)
  Written with help from Claude.
*/
const RESTING = 1.0;          // hPa: below this is "not squeezed" (same as the Arduino)
const LIVE_SECONDS = 15;

const serial = new p5.WebSerial();
let portButton;
let delta = 0;                // pressure right now (hPa above resting)
let lastSample = 0;           // ms of the last reading, to know how long it lasted
let live = [];                // { t, v } for the NOW view
let secs = {};                // squeeze amount per second: { unixSecond: hPa·s }
let fake = 0, fakeOn = false;
let lastSave = 0;
let dayKey = todayKey();

function setup() {
  createCanvas(windowWidth, windowHeight);
  textFont("system-ui");
  loadDay();
  if (!navigator.serial) alert("Web Serial does not work in this browser. Use Chrome.");
  else {
    navigator.serial.addEventListener("connect", () => serial.getPorts());
    navigator.serial.addEventListener("disconnect", () => serial.close());
  }
  serial.getPorts();
  serial.on("noport", makePortButton);
  serial.on("portavailable", openPort);
  serial.on("requesterror", (err) => console.log("serial error", err));
  serial.on("data", serialEvent);
  serial.on("close", makePortButton);
}

function windowResized() { resizeCanvas(windowWidth, windowHeight); }

// ---------- data ----------
function serialEvent() {
  let line = serial.readLine();
  while (line) {
    const v = Number(trim(line));
    if (line.trim() !== "" && !isNaN(v) && !fakeOn && fake === 0) addSample(v);
    line = serial.readLine();
  }
}

function addSample(v) {
  const now = Date.now();
  const dt = lastSample ? min((now - lastSample) / 1000, 0.1) : 0.02;   // seconds this reading stands for
  lastSample = now;
  delta = v;
  const amount = max(0, v - RESTING) * dt;
  if (amount > 0) {
    const s = Math.floor(now / 1000);
    secs[s] = (secs[s] || 0) + amount;
  }
  live.push({ t: now, v });
}

function sumRange(fromSec, toSec) {          // total amount between two unix seconds
  let total = 0;
  for (const k in secs) if (k >= fromSec && k < toSec) total += secs[k];
  return total;
}

function startOfDaySec() { const d = new Date(); d.setHours(0, 0, 0, 0); return Math.floor(d.getTime() / 1000); }
function todayKey() { const d = new Date(); return `ppomo-${d.getFullYear()}-${d.getMonth() + 1}-${d.getDate()}`; }

function loadDay() {
  try { secs = JSON.parse(localStorage.getItem(dayKey) || "{}"); } catch (e) { secs = {}; }
}

function saveDay() {
  try { localStorage.setItem(dayKey, JSON.stringify(secs)); } catch (e) {}
}

// ---------- draw ----------
function draw() {
  if (fakeOn || fake > 0) {                  // SPACE: pretend the bulb is squeezed
    fake = fakeOn ? min(fake + 3, 40) : max(fake - 5, 0);
    addSample(fake);
  }
  if (todayKey() !== dayKey) { saveDay(); dayKey = todayKey(); secs = {}; }   // midnight: new day
  if (millis() - lastSave > 5000) { saveDay(); lastSave = millis(); }
  if (Date.now() - lastSample > 100) {       // no reading for a while (unplugged): draw it as resting
    live.push({ t: Date.now(), v: 0 });
    delta = 0;
  }
  const cutoff = Date.now() - LIVE_SECONDS * 1000;
  while (live.length && live[0].t < cutoff) live.shift();

  background(251, 246, 241);
  const m = max(24, width * 0.04), w = width - 2 * m;
  const h = height - 2 * m;
  const total = sumRange(startOfDaySec(), startOfDaySec() + 86400);

  // header
  noStroke();
  fill(90, 52, 36);
  textAlign(LEFT, TOP);
  textSize(min(28, width * 0.05));
  text("Ppomo · today", m, m);
  textAlign(RIGHT, TOP);
  textSize(min(20, width * 0.035));
  text(`squeeze total ${nf(total, 1, 1)} hPa·s`, width - m, m + 6);

  const top = m + 60;
  const gap = 34;
  const panelH = (h - 60 - 2 * gap) / 3;
  drawLive(m, top, w, panelH * 0.8);
  drawBars(m, top + panelH * 0.8 + gap, w, panelH * 1.05, "LAST 10 MIN", 60, 10,
           Math.floor(Date.now() / 1000) - 600, (i) => (i % 6 === 0 ? `-${10 - i / 6}m` : ""));
  drawBars(m, top + panelH * 1.85 + 2 * gap, w, panelH * 1.15, "TODAY", 48, 1800,
           startOfDaySec(), (i) => (i % 12 === 0 ? `${i / 2}:00` : ""), true);
}

function drawLive(x, y, w, h) {
  label("NOW", x, y);
  const y0 = y + 18, maxV = max(30, ...live.map((p) => p.v));
  fill(255); noStroke(); rect(x, y0, w, h, 10);
  fill(236, 138, 162, 170);
  stroke(220, 110, 140);
  strokeWeight(2);
  beginShape();
  vertex(x, y0 + h);
  const now = Date.now();
  for (const p of live) {
    vertex(x + w * (1 - (now - p.t) / (LIVE_SECONDS * 1000)), y0 + h - constrain(max(0, p.v) / maxV, 0, 1) * (h - 8));
  }
  vertex(x + w, y0 + h);
  endShape(CLOSE);
  noStroke(); fill(140, 110, 100); textSize(13); textAlign(RIGHT, TOP);
  text(`${nf(max(0, delta), 1, 1)} hPa`, x + w - 10, y0 + 8);
}

// bars: n bars of `step` seconds starting at `from` (unix seconds)
function drawBars(x, y, w, h, title, n, step, from, tick, markNow) {
  label(title, x, y);
  const y0 = y + 18, ch = h - 18 - 18;
  fill(255); noStroke(); rect(x, y0, w, ch, 10);
  const vals = [];
  for (let i = 0; i < n; i++) vals.push(sumRange(from + i * step, from + (i + 1) * step));
  const maxV = max(5, ...vals);
  const bw = w / n;
  for (let i = 0; i < n; i++) {
    const bh = (vals[i] / maxV) * (ch - 10);
    fill(236, 138, 162);
    if (bh > 0) rect(x + i * bw + bw * 0.15, y0 + ch - bh, bw * 0.7, bh, 3);
    const t = tick(i);
    if (t) { fill(140, 110, 100); textSize(12); textAlign(LEFT, TOP); text(t, x + i * bw, y0 + ch + 4); }
  }
  if (markNow) {                              // a line at the current time of day
    const nx = x + ((Date.now() / 1000 - from) / (n * step)) * w;
    stroke(90, 52, 36, 120); strokeWeight(1); line(nx, y0, nx, y0 + ch);
    noStroke(); fill(90, 52, 36); textSize(12); textAlign(CENTER, BOTTOM); text("now", nx, y0 - 1);
  }
}

function label(t, x, y) {
  noStroke(); fill(140, 110, 100); textSize(13); textAlign(LEFT, TOP); text(t, x, y);
}

// ---------- keys, CSV, port ----------
function saveCsv() {
  const t = new p5.Table();
  ["date", "time", "amount_hPa_s"].forEach((c) => t.addColumn(c));
  const two = (v) => String(v).padStart(2, "0");
  for (const k of Object.keys(secs).sort()) {
    const d = new Date(k * 1000), r = t.addRow();
    r.setString("date", `${d.getFullYear()}-${two(d.getMonth() + 1)}-${two(d.getDate())}`);
    r.setString("time", `${two(d.getHours())}:${two(d.getMinutes())}:${two(d.getSeconds())}`);
    r.setNum("amount_hPa_s", Number(secs[k].toFixed(2)));
  }
  saveTable(t, "ppomo-squeeze-amount.csv");
}

function keyPressed() {
  if (key === " ") { fakeOn = true; return false; }
  const k = key.toLowerCase();
  if (k === "p") serial.requestPort();
  if (k === "s") saveCsv();
  if (k === "f") fullscreen(!fullscreen());
  if (k === "r" && confirm("Clear today's squeezes?")) { secs = {}; saveDay(); }
}

function keyReleased() { if (key === " ") { fakeOn = false; return false; } }

function makePortButton() {
  if (!portButton) portButton = createButton("choose port");
  portButton.show();
  portButton.mousePressed(() => serial.requestPort());
}

function openPort() {
  serial.open().then(() => console.log("port open"));
  if (portButton) portButton.hide();
}
