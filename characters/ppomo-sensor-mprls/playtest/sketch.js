/*
  Ppomo playtest (p5.js + p5.webserial)

  Squeeze the bulb -> Ppomo on screen squishes right away (harder = more squish).
  Let go -> it puffs up one step. 10 squeezes -> fully puffed, it celebrates, then deflates and a new round starts.
  Stop squeezing -> the air slowly leaks out, so it asks you to squeeze again.
  Nobody squeezes for 20 s -> back to the "Squeeze me" screen. No one has to press anything on the computer.
  Every squeeze is still logged with the date and time (S saves the CSV).

  Uses the same Arduino sketch as squeeze-log (it sends "delta,count" 20 times a second).
  Use Chrome. Close the Arduino Serial Monitor first.

  Keys for me (not for testers):
    P  choose the serial port      F  fullscreen       S  save CSV
    D  show the pressure graph     R  reset everything
    Hold SPACE  = fake squeeze (to test without the sensor, or if the sensor fails)

  Written with help from Claude.
*/
const GOAL = 10;             // squeezes to fill Ppomo
const LEAK_AFTER = 4000;     // ms without a squeeze before air starts leaking out
const LEAK_EVERY = 1200;     // ms per step lost while leaking
const IDLE_AFTER = 20000;    // ms without a squeeze before going back to "Squeeze me"
const FULL_TIME = 3000;      // ms to celebrate when full
const SQUEEZE_ON = 8, SQUEEZE_OFF = 3;  // hPa, only used for the SPACE fake squeeze

const serial = new p5.WebSerial();
let portButton;

let delta = 0;               // pressure rise right now (hPa), from the sensor or SPACE
let maxSeen = 40;            // the hardest squeeze so far, so any hand can reach "full squish"
let lastCount = 0;           // Arduino count already used
let fake = 0, fakeOn = false, fakeDown = false;

let state = "idle";          // idle -> play -> full -> play ...
let level = 0;               // 0..GOAL
let rounds = 0;
let lastSqueeze = -1e9, lastLeak = 0, fullAt = 0;
let puff = 0, puffVel = 0;   // springy body size
let squish = 0;              // 0..1 live squeeze
let pops = [];               // floating "+1"
let sparks = [];
let log = [];                // { n, date, time }
let history = [];
let showGraph = false;
let audio;

function setup() {
  createCanvas(windowWidth, windowHeight);
  textFont("system-ui");
  if (!navigator.serial) alert("Web Serial does not work in this browser. Use Chrome.");
  else {
    navigator.serial.addEventListener("connect", () => serial.getPorts());
    navigator.serial.addEventListener("disconnect", () => serial.close());
  }
  serial.getPorts();                       // reopens a port Chrome already allowed, no click needed
  serial.on("noport", makePortButton);
  serial.on("portavailable", openPort);
  serial.on("requesterror", (err) => console.log("serial error", err));
  serial.on("data", serialEvent);
  serial.on("close", makePortButton);
}

function windowResized() { resizeCanvas(windowWidth, windowHeight); }

// ---------- input ----------
function serialEvent() {
  let line = serial.readLine();
  while (line) {
    const parts = trim(line).split(",");
    if (parts.length === 2 && !isNaN(Number(parts[0])) && !isNaN(Number(parts[1]))) {
      if (!fakeOn) delta = Number(parts[0]);
      const count = Number(parts[1]);
      if (count < lastCount) lastCount = 0;          // the Arduino restarted
      while (lastCount < count) { lastCount++; squeezed(); }
    }
    line = serial.readLine();
  }
}

function fakeSqueeze() {                             // SPACE behaves like the bulb
  fake = fakeOn ? min(fake + 4, 45) : max(fake - 6, 0);
  if (fakeOn || fake > 0) delta = fake;
  if (!fakeDown && fake > SQUEEZE_ON) { fakeDown = true; squeezed(); }   // same on/off rule as the Arduino
  else if (fakeDown && fake < SQUEEZE_OFF) fakeDown = false;
}

// one counted squeeze
function squeezed() {
  const now = millis();
  lastSqueeze = now;
  lastLeak = now;
  addLog();
  if (state === "full") return;                    // still celebrating: logged, but no level change
  state = "play";
  level = min(level + 1, GOAL);
  puffVel += 0.06;
  pops.push({ x: width / 2 + random(-60, 60), y: height * 0.3, a: 255, t: level === GOAL ? "FULL!" : "+1" });
  beep(300 + level * 60, 0.09);
  if (level === GOAL) {
    state = "full";
    fullAt = now;
    rounds++;
    for (let i = 0; i < 40; i++) sparks.push({ x: width / 2, y: height * 0.5, vx: random(-6, 6), vy: random(-9, -2), a: 255 });
    [660, 880, 1100].forEach((f, i) => setTimeout(() => beep(f, 0.12), i * 110));
  }
}

// ---------- update + draw ----------
function draw() {
  fakeSqueeze();
  const now = millis();

  // the state machine: start, stop and reset all happen by themselves
  if (state === "full" && now - fullAt > FULL_TIME) { level = 0; state = "play"; beep(220, 0.2); }
  if (state === "play" && level > 0 && now - lastSqueeze > LEAK_AFTER && now - lastLeak > LEAK_EVERY) {
    level--; lastLeak = now;                         // air leaks out: squeeze again!
  }
  if (state === "play" && now - lastSqueeze > IDLE_AFTER) { state = "idle"; level = 0; }

  maxSeen = max(maxSeen, delta);
  squish = lerp(squish, constrain(delta / (maxSeen * 0.8), 0, 1), 0.35);
  const target = state === "idle" ? 0.03 * sin(now / 500) : level / GOAL;
  puffVel += (target - puff) * 0.08;
  puffVel *= 0.82;
  puff += puffVel;
  history.push(delta);
  if (history.length > 300) history.shift();

  background(251, 246, 241);
  const s = min(width, height) * 0.32;
  drawPpomo(width / 2, height * 0.52, s, squish, puff, state);
  drawSparks();
  drawPops();
  drawHud(s);
  if (showGraph) drawGraph();
}

function drawPpomo(cx, cy, s, sq, p, st) {
  const grow = 1 + 0.55 * p;
  const w = s * grow * (1 + 0.3 * sq);               // squeezed: wider and shorter
  const h = s * 1.15 * grow * (1 - 0.25 * sq);
  push();
  translate(cx, cy + (s * 1.15 * grow - h) / 2);
  noStroke();
  fill(90, 52, 36, 25);                              // shadow
  ellipse(0, h / 2 + 8, w * 0.9, 18);
  fill(236, 138, 162, 185);                          // translucent silicone body
  ellipse(0, 0, w, h);
  fill(255, 255, 255, 90);                           // shine
  ellipse(-w * 0.22, -h * 0.28, w * 0.22, h * 0.14);

  // ivory face plate
  const fw = w * 0.56, fh = h * 0.36, fy = -h * 0.1;
  fill(247, 238, 218);
  ellipse(0, fy, fw, fh);
  const ex = fw * 0.22, ey = fy - fh * 0.06, es = fw * 0.07;
  stroke(70, 40, 30);
  strokeWeight(max(2, es * 0.45));
  noFill();
  if (st === "full") {                               // happy ^ ^
    arc(-ex, ey + es * 0.3, es * 1.6, es * 1.6, PI, TWO_PI);
    arc(ex, ey + es * 0.3, es * 1.6, es * 1.6, PI, TWO_PI);
  } else if (sq > 0.35) {                            // squeezed > <
    line(-ex - es * 0.6, ey - es * 0.5, -ex + es * 0.5, ey); line(-ex + es * 0.5, ey, -ex - es * 0.6, ey + es * 0.5);
    line(ex + es * 0.6, ey - es * 0.5, ex - es * 0.5, ey); line(ex - es * 0.5, ey, ex + es * 0.6, ey + es * 0.5);
  } else {
    noStroke(); fill(70, 40, 30);
    ellipse(-ex, ey, es, es * 1.2); ellipse(ex, ey, es, es * 1.2);
  }
  noStroke();
  fill(240, 120, 150, 60 + 150 * constrain(p, 0, 1));  // cheeks blush more as it fills
  ellipse(-fw * 0.33, fy + fh * 0.14, fw * 0.2, fh * 0.16);
  ellipse(fw * 0.33, fy + fh * 0.14, fw * 0.2, fh * 0.16);
  fill(70, 40, 30);
  if (st === "full" || sq > 0.35) ellipse(0, fy + fh * 0.2, es * 1.1, es * 1.3);   // "o"
  else { noFill(); stroke(70, 40, 30); strokeWeight(max(2, es * 0.35)); arc(0, fy + fh * 0.15, es * 1.4, es, 0, PI); }
  pop();
}

function drawHud(s) {
  noStroke();
  textAlign(CENTER, CENTER);
  fill(90, 52, 36);
  if (state === "idle") {
    textSize(min(width, height) * 0.07);
    text("Squeeze me!", width / 2, height * 0.14);
    fill(140, 110, 100);
    textSize(18);
    text("squeeze and let go", width / 2, height * 0.14 + min(width, height) * 0.06);
  } else {
    // 10 dots = how full Ppomo is (the goal, without words)
    const r = 16, gap = 10, total = GOAL * (r + gap) - gap;
    for (let i = 0; i < GOAL; i++) {
      fill(i < level ? color(236, 138, 162) : color(230, 218, 208));
      circle(width / 2 - total / 2 + r / 2 + i * (r + gap), height * 0.12, r);
    }
    if (state === "play" && level > 0 && millis() - lastSqueeze > LEAK_AFTER) {
      fill(140, 110, 100); textSize(18);
      text("air is leaking… squeeze!", width / 2, height * 0.12 + 32);
    }
  }
  // the log, quietly at the bottom (this is the real product feature)
  fill(140, 110, 100);
  textSize(15);
  const last = log.length ? log[log.length - 1] : null;
  text(`today ${log.length} squeezes` + (last ? `  ·  last ${last.time}` : "") + (rounds ? `  ·  puffed ${rounds}×` : ""),
       width / 2, height - 28);
}

function drawPops() {
  textAlign(CENTER, CENTER);
  textSize(34);
  for (const p of pops) { fill(236, 110, 140, p.a); text(p.t, p.x, p.y); p.y -= 1.5; p.a -= 5; }
  pops = pops.filter((p) => p.a > 0);
}

function drawSparks() {
  noStroke();
  for (const p of sparks) {
    fill(255, 200, 90, p.a);
    circle(p.x, p.y, 10);
    p.x += p.vx; p.y += p.vy; p.vy += 0.25; p.a -= 4;
  }
  sparks = sparks.filter((p) => p.a > 0);
}

function drawGraph() {
  const x0 = 20, y0 = height - 70, gw = 300, gh = 80;
  fill(255, 255, 255, 220); noStroke(); rect(x0 - 10, y0 - gh - 30, gw + 20, gh + 50, 10);
  noFill(); stroke(236, 138, 162); strokeWeight(2);
  beginShape();
  history.forEach((v, i) => vertex(x0 + (i / 299) * gw, y0 - constrain(v / maxSeen, 0, 1) * gh));
  endShape();
  noStroke(); fill(90, 52, 36); textSize(12); textAlign(LEFT, BASELINE);
  text(`delta ${delta.toFixed(1)} hPa   max ${maxSeen.toFixed(0)}   port ${serial.isOpen ? "open" : "closed"}`, x0, y0 - gh - 12);
}

// ---------- log, sound, keys ----------
function addLog() {
  const d = new Date(), two = (v) => String(v).padStart(2, "0");
  log.push({ n: log.length + 1, date: `${d.getFullYear()}-${two(d.getMonth() + 1)}-${two(d.getDate())}`,
             time: `${two(d.getHours())}:${two(d.getMinutes())}:${two(d.getSeconds())}` });
}

function saveLog() {
  const t = new p5.Table();
  ["n", "date", "time"].forEach((c) => t.addColumn(c));
  for (const e of log) { const r = t.addRow(); r.setNum("n", e.n); r.setString("date", e.date); r.setString("time", e.time); }
  saveTable(t, "ppomo-playtest-squeezes.csv");
}

function beep(freq, dur) {                         // small sound with plain Web Audio (no extra library)
  try {
    audio = audio || new AudioContext();
    if (audio.state === "suspended") audio.resume();
    const o = audio.createOscillator(), g = audio.createGain(), t = audio.currentTime;
    o.type = "sine"; o.frequency.setValueAtTime(freq, t); o.frequency.exponentialRampToValueAtTime(freq * 1.5, t + dur);
    g.gain.setValueAtTime(0.25, t); g.gain.exponentialRampToValueAtTime(0.001, t + dur + 0.05);
    o.connect(g).connect(audio.destination); o.start(t); o.stop(t + dur + 0.06);
  } catch (e) {}
}

function keyPressed() {
  if (key === " ") { fakeOn = true; return false; }
  const k = key.toLowerCase();
  if (k === "p") serial.requestPort();
  if (k === "f") fullscreen(!fullscreen());
  if (k === "s") saveLog();
  if (k === "d") showGraph = !showGraph;
  if (k === "r") { log = []; level = 0; rounds = 0; state = "idle"; }
  beep(1, 0.001);                                  // unlocks sound after the first key press
}

function keyReleased() { if (key === " ") { fakeOn = false; return false; } }
function mousePressed() { beep(1, 0.001); }

function makePortButton() {
  if (!portButton) portButton = createButton("choose port");
  portButton.show();
  portButton.mousePressed(() => serial.requestPort());
}

function openPort() {
  serial.open().then(() => console.log("port open"));
  if (portButton) portButton.hide();
}
