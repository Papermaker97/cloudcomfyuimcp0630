/*
  Ppomo FOMO Pile (PComp playtest, Nov 24)

  Hold the squishy Ppomo, scroll your phone, and squeeze whenever you feel FOMO.
    Squeeze      -> a Ppomo appears at the top and grows while you squeeze (harder and longer = bigger)
    Let go       -> it drops onto the pile. Your FOMO is now a small, soft thing you can see.
    Stop for 10 s -> "You handed Ppomo 23 little FOMOs", then Ppomo lets them go one by one
                     and the screen is empty for the next person. Nobody has to touch the computer.
  Squeezes are measured as an AMOUNT (pressure above resting x time), not a count, because counting
  missed quick taps and long presses. Every drop is logged with date, time and amount (S saves a CSV).

  Uses the Arduino sketch ppomo_squeeze_amount (one number per line: hPa above resting, 50 per second).
  Use Chrome. Close the Arduino Serial Monitor first.

  Keys (for me): P choose port   S save CSV   D pressure graph   F fullscreen   R clear
                 hold SPACE = fake squeeze (to test without the sensor, or if the sensor fails)
  Credits: Ppomo pictures are renders of my 3D Ppomo (from my ICM doomscroll sketch).
  Physics: Matter.js 0.20.0. Serial: p5.webserial. Written with help from Claude.
*/

// ---------- settings to tune ----------
const RESTING = 1.0;        // hPa: below this the squishy counts as untouched (same as the Arduino)
const PRESS_ON = 3.0;       // hPa: a squeeze starts above this
const PRESS_OFF = 1.5;      // hPa: and ends below this
const AMOUNT_BIG = 20;      // hPa·s that makes the biggest Ppomo (lower it if every Ppomo stays small)
const END_AFTER = 10000;    // ms without squeezing before the session ends
const SUMMARY_TIME = 7000;  // ms the summary stays before Ppomo lets the FOMOs go

// ---------- Matter.js ----------
const Engine = Matter.Engine, Bodies = Matter.Bodies, Composite = Matter.Composite;

const POSES = ['front', 'front', 'front', 'peek', 'peek', 'butt', 'side'];
const COLORS = ['grey', 'grey', 'pink', 'cream', 'peach', 'lilac', 'sky'];
const HIT = { front: 0.29, butt: 0.29, side: 0.27, peek: 0.29 };

const serial = new p5.WebSerial();
let portButton;
let sprites = {};
let engine, walls = [];
let box;                    // the jar the Ppomos pile up in: { x, y, w, h }

let delta = 0, lastSample = 0, history = [];
let fake = 0, fakeOn = false;

let state = 'idle';         // idle -> session -> summary -> letgo -> idle
let pressing = false;
let charge = null;          // the Ppomo growing at the top while you squeeze: { amount, peak, pose, color, flip }
let ppomos = [];            // on the pile
let leaving = [];           // floating away
let session = { start: 0, last: 0, drops: [] };   // drops: { t (ms into session), amount }
let summaryAt = 0, nextLeave = 0;
let log = [];               // every drop: { date, time, amount, peak }
let showGraph = false;

// ---------- the Ppomo on the pile ----------
class Ppomo {
  constructor(x, y, size, pose, color, flip) {
    this.pose = pose; this.color = color; this.flip = flip;
    this.img = sprites[pose + '-' + color];
    this.size = size;
    this.squash = 0; this.lastSpeed = 0; this.age = 0;
    this.body = Bodies.circle(x, y, HIT[pose] * size, { restitution: 0.15, friction: 0.5, angle: random(-0.3, 0.3) });
    Composite.add(engine.world, this.body);
  }
  update() {
    const s = this.body.speed;
    if (this.lastSpeed > 3 && s < 1) this.squash = 1;   // squash for a moment when it lands
    this.squash *= 0.86;
    this.lastSpeed = s;
    this.age++;
  }
  show() {
    drawPpomo(this.img, this.body.position.x, this.body.position.y, this.size, this.body.angle,
              this.flip * (1 + 0.14 * this.squash), 1 - 0.14 * this.squash, 255);
  }
}

function drawPpomo(img, x, y, size, angle, sx, sy, alpha) {
  push();
  translate(x, y);
  rotate(angle);
  scale(sx, sy);
  tint(255, alpha);
  imageMode(CENTER);
  image(img, 0, 0, size, size);
  pop();
}

// ---------- setup ----------
function preload() {
  for (const pose of ['front', 'butt', 'side', 'peek'])
    for (const color of ['grey', 'pink', 'cream', 'peach', 'lilac', 'sky'])
      sprites[pose + '-' + color] = loadImage('sprites/' + pose + '-' + color + '.png');
}

function setup() {
  createCanvas(windowWidth, windowHeight);
  textFont('system-ui');
  engine = Engine.create();
  makeWalls();

  if (!navigator.serial) console.log('Web Serial does not work in this browser. Use Chrome.');
  else {
    navigator.serial.addEventListener('connect', () => serial.getPorts());
    navigator.serial.addEventListener('disconnect', () => serial.close());
  }
  serial.getPorts();                       // reopens a port Chrome already allowed
  serial.on('noport', makePortButton);
  serial.on('portavailable', openPort);
  serial.on('requesterror', (e) => console.log('serial error', e));
  serial.on('data', serialEvent);
  serial.on('close', makePortButton);
}

// the jar: a tall box in the middle of the screen
function makeWalls() {
  for (const w of walls) Composite.remove(engine.world, w);
  const h = height * 0.66, w = min(width * 0.9, h * 0.72);
  box = { x: (width - w) / 2, y: height * 0.31, w, h };
  const t = 200, opt = { isStatic: true };
  walls = [
    Bodies.rectangle(width / 2, box.y + box.h + t / 2, w + 2 * t, t, opt),        // floor
    Bodies.rectangle(box.x - t / 2, box.y + box.h / 2 - height, t, box.h + 2 * height, opt),   // left
    Bodies.rectangle(box.x + w + t / 2, box.y + box.h / 2 - height, t, box.h + 2 * height, opt), // right
  ];
  Composite.add(engine.world, walls);
}

function windowResized() {
  resizeCanvas(windowWidth, windowHeight);
  makeWalls();
}

// ---------- input ----------
function serialEvent() {
  let line = serial.readLine();
  while (line) {
    const v = Number(trim(line));
    if (trim(line) !== '' && !isNaN(v) && !fakeOn && fake === 0) addSample(v);
    line = serial.readLine();
  }
}

function addSample(v) {
  const now = millis();
  const dt = lastSample ? min((now - lastSample) / 1000, 0.1) : 0.02;
  lastSample = now;
  delta = v;
  history.push(v);
  if (history.length > 300) history.shift();

  if (!pressing && v > PRESS_ON) startPress();
  if (pressing) {
    charge.amount += max(0, v - RESTING) * dt;
    charge.peak = max(charge.peak, v);
    if (charge.amount >= AMOUNT_BIG) { endPress(); startPress(); }   // a very long squeeze: drop it and keep going
    else if (v < PRESS_OFF) endPress();
  }
}

function startPress() {
  pressing = true;
  if (state !== 'session') {                      // the first squeeze starts a session
    state = 'session';
    session = { start: millis(), last: millis(), drops: [] };
  }
  charge = { amount: 0, peak: 0, pose: random(POSES), color: random(COLORS), flip: random() < 0.5 ? -1 : 1 };
}

function endPress() {
  pressing = false;
  if (!charge || charge.amount < 0.05) { charge = null; return; }
  const size = sizeFor(charge.amount);
  ppomos.push(new Ppomo(width / 2 + random(-box.w * 0.2, box.w * 0.2), box.y - size * 0.55 - 6, size, charge.pose, charge.color, charge.flip));
  session.drops.push({ t: millis() - session.start, amount: charge.amount });
  session.last = millis();
  addLog(charge);
  charge = null;
}

function sizeFor(amount) {
  const u = box.w / 2.6;                         // the biggest Ppomo is about 40% of the jar's width
  return lerp(u * 0.42, u, sqrt(constrain(amount / AMOUNT_BIG, 0, 1)));
}

// ---------- draw ----------
function draw() {
  if (fakeOn || fake > 0) {                      // SPACE: pretend the squishy is squeezed
    fake = fakeOn ? min(fake + 2.5, 40) : max(fake - 6, 0);
    addSample(fake);
  } else if (millis() - lastSample > 200) {       // no sensor data: count it as resting
    addSample(0);
  }

  const now = millis();
  if (state === 'session' && !pressing && now - session.last > END_AFTER) { state = 'summary'; summaryAt = now; }
  if (state === 'session' && pileIsFull()) { if (pressing) endPress(); state = 'summary'; summaryAt = now; }
  if (state === 'summary' && now - summaryAt > SUMMARY_TIME) { state = 'letgo'; nextLeave = now; }
  if (state === 'letgo') letGo(now);

  Engine.update(engine, 1000 / 60);

  background(246, 243, 248);
  drawJar();
  for (const p of ppomos) { p.update(); p.show(); }
  drawLeaving();
  drawCharge();
  drawText();
  if (showGraph) drawGraph();
}

function drawJar() {
  noStroke();
  fill(255, 255, 255, 170);
  rect(box.x, box.y, box.w, box.h, 0, 0, 28, 28);
  stroke(222, 216, 230);
  strokeWeight(3);
  noFill();
  line(box.x, box.y, box.x, box.y + box.h - 28);
  line(box.x + box.w, box.y, box.x + box.w, box.y + box.h - 28);
  arc(box.x + 28, box.y + box.h - 28, 56, 56, HALF_PI, PI);
  arc(box.x + box.w - 28, box.y + box.h - 28, 56, 56, 0, HALF_PI);
  line(box.x + 28, box.y + box.h, box.x + box.w - 28, box.y + box.h);
}

// the Ppomo growing at the top while you squeeze; it also squishes with how hard you squeeze right now
function drawCharge() {
  if (!charge) return;
  const size = sizeFor(charge.amount);
  const squish = constrain(delta / 40, 0, 1);
  const wob = sin(millis() / 60) * 0.03 * squish;
  drawPpomo(sprites[charge.pose + '-' + charge.color], width / 2, box.y - size * 0.55 - 6, size, 0,
            charge.flip * (1 + 0.22 * squish + wob), 1 - 0.18 * squish - wob, 255);
}

// "let go": the Ppomos float up and fade, one at a time, oldest first
function letGo(now) {
  if (ppomos.length === 0) {
    if (leaving.length === 0) state = 'idle';
    return;
  }
  if (now >= nextLeave) {
    const p = ppomos.shift();
    Composite.remove(engine.world, p.body);
    leaving.push({ p, x: p.body.position.x, y: p.body.position.y, a: 255, vy: -1.5, drift: random(-0.6, 0.6) });
    nextLeave = now + max(60, 1800 / max(1, ppomos.length));
  }
}

function drawLeaving() {
  for (const l of leaving) {
    l.y += l.vy; l.vy -= 0.04; l.x += l.drift + sin(l.y / 30) * 0.6; l.a -= 3;
    drawPpomo(l.p.img, l.x, l.y, l.p.size, sin(l.y / 40) * 0.2, l.p.flip, 1, max(0, l.a));
  }
  leaving = leaving.filter((l) => l.a > 0 && l.y > -200);
}

function pileIsFull() {
  // an old Ppomo resting near the top of the jar (a new one also starts up there, so skip young ones)
  return ppomos.some((p) => p.age > 90 && p.body.speed < 0.3 && p.body.position.y < box.y + box.h * 0.12);
}

function drawText() {
  const k = min(width, height) / 800;
  noStroke();
  textAlign(CENTER, CENTER);
  if (state === 'idle') {
    fill(60, 58, 70);
    textSize(40 * k);
    text('Squeeze Ppomo when you feel FOMO', width / 2, height * 0.08);
    fill(120, 115, 135);
    textSize(20 * k);
    text('hold it in one hand, scroll your phone with the other', width / 2, height * 0.08 + 40 * k);
    return;
  }
  // small line on top during the session
  const n = session.drops.length;
  fill(120, 115, 135);
  textSize(20 * k);
  if (state === 'session') text(n === 0 ? 'squeeze…' : `${n} little FOMO${n === 1 ? '' : 's'}`, width / 2, height * 0.06);

  if (state === 'summary') drawSummary(k);
  if (state === 'letgo') {
    fill(60, 58, 70);
    textSize(28 * k);
    text('Ppomo is letting them go…', width / 2, height * 0.08);
  }
}

// the end of a session: how many, when the biggest was, and a small timeline
function drawSummary(k) {
  const drops = session.drops;
  const total = drops.reduce((s, d) => s + d.amount, 0);
  const biggest = drops.reduce((a, d) => (d.amount > a.amount ? d : a), drops[0] || { t: 0, amount: 0 });
  const dur = max(session.last - session.start, 1000);
  const cw = min(width * 0.8, 640 * k * 1.2), ch = 190 * k;
  const cx = width / 2 - cw / 2, cy = height * 0.45 - ch / 2;
  fill(60, 58, 70, 235);
  rect(cx, cy, cw, ch, 24 * k);
  fill(255);
  textSize(30 * k);
  text(`You handed Ppomo ${drops.length} little FOMO${drops.length === 1 ? '' : 's'}`, width / 2, cy + 40 * k);
  textSize(18 * k);
  fill(225, 220, 235);
  text(`in ${mmss(dur)} · the biggest squeeze at ${mmss(biggest.t)} · total ${total.toFixed(0)} hPa·s`, width / 2, cy + 78 * k);
  // timeline: one bar per drop, placed at its time, as tall as its amount
  const tx = cx + 30 * k, tw = cw - 60 * k, ty = cy + ch - 26 * k, th = 60 * k;
  stroke(255, 255, 255, 90); strokeWeight(1);
  line(tx, ty, tx + tw, ty);
  noStroke();
  const maxA = max(...drops.map((d) => d.amount), 1);
  for (const d of drops) {
    const h = max(3, (d.amount / maxA) * th);
    fill(d === biggest ? color(242, 150, 175) : color(255, 255, 255, 200));
    rect(tx + (d.t / dur) * tw - 2, ty - h, 4, h, 2);
  }
}

function mmss(ms) {
  const s = round(ms / 1000);
  return `${floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
}

function drawGraph() {
  const x0 = 20, y0 = height - 30, gw = 300, gh = 80, m = max(30, ...history);
  fill(255, 255, 255, 230); noStroke(); rect(x0 - 10, y0 - gh - 30, gw + 20, gh + 40, 10);
  noFill(); stroke(236, 138, 162); strokeWeight(2);
  beginShape();
  history.forEach((v, i) => vertex(x0 + (i / 299) * gw, y0 - constrain(v / m, 0, 1) * gh));
  endShape();
  noStroke(); fill(60, 58, 70); textSize(12); textAlign(LEFT, BASELINE);
  text(`delta ${delta.toFixed(1)} hPa · ${pressing ? 'pressing' : 'resting'} · port ${(typeof serial.isOpen === 'function' ? serial.isOpen() : serial.isOpen) ? 'open' : 'closed'}`, x0, y0 - gh - 12);
}

// ---------- log, keys, port ----------
function addLog(c) {
  const d = new Date(), two = (v) => String(v).padStart(2, '0');
  log.push({
    date: `${d.getFullYear()}-${two(d.getMonth() + 1)}-${two(d.getDate())}`,
    time: `${two(d.getHours())}:${two(d.getMinutes())}:${two(d.getSeconds())}`,
    amount: Number(c.amount.toFixed(2)), peak: Number(c.peak.toFixed(1)),
  });
}

function saveCsv() {
  const t = new p5.Table();
  ['date', 'time', 'amount_hPa_s', 'peak_hPa'].forEach((c) => t.addColumn(c));
  for (const e of log) {
    const r = t.addRow();
    r.setString('date', e.date); r.setString('time', e.time);
    r.setNum('amount_hPa_s', e.amount); r.setNum('peak_hPa', e.peak);
  }
  saveTable(t, 'ppomo-fomo-pile.csv');
}

function keyPressed() {
  if (key === ' ') { fakeOn = true; return false; }
  const k = key.toLowerCase();
  if (k === 'p') serial.requestPort();
  if (k === 's') saveCsv();
  if (k === 'd') showGraph = !showGraph;
  if (k === 'f') fullscreen(!fullscreen());
  if (k === 'r') {
    for (const p of ppomos) Composite.remove(engine.world, p.body);
    ppomos = []; leaving = []; charge = null; pressing = false; state = 'idle';
  }
}

function keyReleased() { if (key === ' ') { fakeOn = false; return false; } }

function makePortButton() {
  if (!portButton) portButton = createButton('choose port');
  portButton.show();
  portButton.mousePressed(() => serial.requestPort());
}

function openPort() {
  serial.open().then(() => console.log('port open'));
  if (portButton) portButton.hide();
}
