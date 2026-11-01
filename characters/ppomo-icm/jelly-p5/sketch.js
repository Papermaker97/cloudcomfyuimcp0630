/*
  Ppomo Jelly Pile (ICM: array of objects, Week 6-7)

  Click empty space   → drop a new Ppomo there (it lands on the floor or on another Ppomo)
  Click a Ppomo        → squeeze it: cheeks, belly and butt puff up one step (4th squeeze lets the air out)
  Space                → squeeze every Ppomo
  X                    → delete the Ppomo under the mouse
  Backspace            → delete the last Ppomo you added
  Every action is recorded in actionLog (shown under the canvas). "Replay" plays your session back.

  Pipeline (the point of this sketch):
    3D model + jelly physics are made OUTSIDE p5 (three.js soft-body demo, baked to sprite sheets),
    p5.js only does the interaction: positions, stacking, input, logging, DOM controls.
    assets/clips.json tells p5 how each sheet is laid out (cell size, columns, frames, fps, ground line).

  Credits:
    - Ppomo character, 3D model and jelly sprite sheets: made for this project with help from Claude
      (three.js r160 + an XPBD soft body after Matthias Müller's "Ten Minute Physics" soft-body tutorial).
    - p5.js reference for loadImage / loadJSON / image() with a source rectangle / DOM functions: https://p5js.org/reference/
    - The sketch code was written with help from Claude.
*/

// ---------- global variables ----------
let meta;                 // clips.json: { cell, cols, fps, groundY, clips: { land: {...}, puff1: {...}, ... } }
let sheets = {};          // clip name → sprite sheet image
let ppomos = [];          // ARRAY OF OBJECTS: every Ppomo on screen
let actionLog = [];       // every user action: { t, type, id, x }
let nextId = 1;
let sessionStart = 0;
let replay = null;        // while replaying: { start, index, events }

let floorY;               // y of the floor line on the canvas
let sizeSlider, gravitySlider, logBox, statsP;

// ---------- the Ppomo class ----------
class Ppomo {
  constructor(id, x, size) {
    this.id = id;
    this.x = x;              // centre x on the canvas
    this.y = -40;            // y of its feet (starts above the canvas)
    this.vy = 0;
    this.size = size;        // drawn size of one sprite cell, in px
    this.level = 0;          // puff level 0..3
    this.clip = 'land';      // which baked clip is playing
    this.frame = 0;          // current frame of that clip (can be fractional)
    this.state = 'falling';  // 'falling' | 'playing' | 'resting'
    this.below = null;       // the Ppomo it is sitting on, if any
  }

  // body size on screen (the model fills about 60% of a sprite cell)
  get bodyW() { return this.size * 0.6; }
  get bodyH() { return this.size * 0.6; }

  update() {
    // if the Ppomo underneath was deleted, fall again
    if (this.state !== 'falling' && this.below && !ppomos.includes(this.below)) {
      this.below = null;
      this.state = 'falling';
    }
    if (this.state === 'falling') {
      this.vy += gravitySlider.value();
      this.y += this.vy;
      const ground = findGround(this);
      if (this.y >= ground.y) {
        this.y = ground.y;
        this.vy = 0;
        this.below = ground.below;
        this.play('land');
      }
      return;
    }
    if (this.state === 'playing') {
      this.frame += meta.fps * (deltaTime / 1000);
      const total = meta.clips[this.clip].frames;
      if (this.frame >= total - 1) {
        this.frame = total - 1;
        this.state = 'resting';
      }
    }
    // stay on top of the Ppomo underneath (it may still be wobbling)
    if (this.below) this.y = this.below.topY();
  }

  play(clipName) {
    this.clip = clipName;
    this.frame = 0;
    this.state = 'playing';
  }

  squeeze() {
    if (this.state === 'falling') return;
    if (this.level < 3) {
      this.level++;
      this.play('puff' + this.level);
    } else {
      this.level = 0;
      this.play('deflate');
    }
  }

  topY() { return this.y - this.bodyH * (0.82 + 0.05 * this.level); }   // where a Ppomo on top sits (a little sunk in; puffier = taller)

  contains(px, py) {
    const cx = this.x, cy = this.y - this.bodyH / 2;
    const dx = (px - cx) / (this.bodyW / 2), dy = (py - cy) / (this.bodyH / 2);
    return dx * dx + dy * dy <= 1;
  }

  show() {
    const c = meta.clips[this.clip];
    const f = floor(this.frame);
    const sx = (f % meta.cols) * meta.cell;
    const sy = floor(f / meta.cols) * meta.cell;
    const k = this.size / meta.cell;
    // the sheet's ground line (meta.groundY) is lined up with this Ppomo's feet
    image(sheets[this.clip], this.x - this.size / 2, this.y - meta.groundY * k, this.size, this.size, sx, sy, meta.cell, meta.cell);
  }
}

// the highest surface under a falling Ppomo: the floor or the top of a resting Ppomo
function findGround(p) {
  let best = { y: floorY, below: null };
  for (const other of ppomos) {
    if (other === p || other.state === 'falling') continue;
    if (abs(other.x - p.x) < (other.bodyW + p.bodyW) * 0.35 && other.topY() < best.y && other.topY() >= p.y - p.vy - 1) {
      best = { y: other.topY(), below: other };
    }
  }
  return best;
}

// ---------- setup: load the baked assets, then build the DOM ----------
async function setup() {
  createCanvas(540, 960);            // 9:16, ready for an Instagram reel / story
  floorY = height - 90;
  meta = await loadJSON('assets/clips.json');
  for (const name in meta.clips) {
    sheets[name] = await loadImage('assets/' + meta.clips[name].file);
  }

  // DOM controls (EXPLORE-CREATE)
  const panel = createDiv().id('panel');
  createSpan('Size of new Ppomo').parent(panel);
  sizeSlider = createSlider(120, 320, 210, 10).parent(panel);
  createSpan('Gravity').parent(panel);
  gravitySlider = createSlider(0.2, 1.6, 0.6, 0.1).parent(panel);
  const buttons = createDiv().parent(panel).class('buttons');
  createButton('Squeeze all').parent(buttons).mousePressed(() => squeezeAll(true));
  createButton('Clear').parent(buttons).mousePressed(() => { ppomos = []; logAction('clear', 0, 0); });
  createButton('Replay my session').parent(buttons).mousePressed(startReplay);
  createButton('Save log').parent(buttons).mousePressed(() => saveJSON(actionLog, 'ppomo-action-log.json'));
  statsP = createP('').parent(panel);
  logBox = createDiv('').parent(panel).id('log');

  sessionStart = millis();
  // start with two Ppomos so the first frame is not empty
  addPpomo(width * 0.38, 210, null, true);
  addPpomo(width * 0.64, 190, null, true);
}

// ---------- draw ----------
function draw() {
  if (!meta || !sheets.deflate) {               // assets still loading
    background(238, 236, 242);
    return;
  }
  background(238, 236, 242);
  noStroke();
  fill(226, 223, 233);
  rect(0, floorY, width, height - floorY);      // floor

  if (replay) runReplay();

  for (const p of ppomos) p.update();
  // draw lower Ppomos first so a Ppomo sitting on top is drawn in front
  const order = [...ppomos].sort((a, b) => b.y - a.y);
  for (const p of order) p.show();

  // hover hint
  const hovered = ppomoAt(mouseX, mouseY);
  cursor(hovered ? HAND : ARROW);

  fill(60, 58, 70);
  textSize(22);
  textAlign(LEFT, TOP);
  text('Ppomo pile', 24, 24);
  textSize(13);
  fill(110, 106, 124);
  text(replay ? 'Replaying your session…' : 'click: drop · click a Ppomo: squeeze · space: squeeze all · X / ⌫: delete', 24, 54);

  updateStats();
}

// ---------- input ----------
function mousePressed() {
  if (replay || mouseX < 0 || mouseX > width || mouseY < 0 || mouseY > height) return;
  const hit = ppomoAt(mouseX, mouseY);
  if (hit) {
    hit.squeeze();
    logAction('squeeze', hit.id, hit.x);
  } else {
    addPpomo(mouseX, sizeSlider.value(), null, true);
  }
}

function keyPressed() {
  if (replay) return;
  if (key === ' ') {
    squeezeAll(true);
    return false;                                 // stop the page from scrolling
  }
  if (key === 'x' || key === 'X') {
    const hit = ppomoAt(mouseX, mouseY);
    if (hit) removePpomo(hit.id, true);
  }
  if (key === 'Backspace' || keyCode === 8) {
    if (ppomos.length > 0) removePpomo(ppomos[ppomos.length - 1].id, true);
    return false;
  }
}

// ---------- actions (each one can be logged and replayed) ----------
function addPpomo(x, size, id, record) {
  const p = new Ppomo(id || nextId++, x, size);
  nextId = max(nextId, p.id + 1);
  ppomos.push(p);
  if (record) logAction('add', p.id, x, size);
  return p;
}

function removePpomo(id, record) {
  const i = ppomos.findIndex((p) => p.id === id);
  if (i === -1) return;
  const p = ppomos[i];
  ppomos.splice(i, 1);
  if (record) logAction('delete', id, p.x);
}

function squeezeAll(record) {
  for (const p of ppomos) p.squeeze();
  if (record) logAction('squeezeAll', 0, 0);
}

function ppomoAt(x, y) {
  // check from front to back: the Ppomo drawn last (highest) wins
  const order = [...ppomos].sort((a, b) => a.y - b.y);
  for (const p of order) if (p.contains(x, y)) return p;
  return null;
}

// ---------- recording the user's actions ----------
function logAction(type, id, x, size) {
  actionLog.push({ t: round(millis() - sessionStart), type, id, x: round(x), size });
  const last = actionLog.slice(-8).reverse();
  logBox.html(last.map((a) => `${(a.t / 1000).toFixed(1)}s  ${a.type}${a.id ? ' #' + a.id : ''}`).join('<br>'));
}

function updateStats() {
  const squeezes = actionLog.filter((a) => a.type === 'squeeze').length +
                   actionLog.filter((a) => a.type === 'squeezeAll').length;
  statsP.html(`Ppomos on screen: ${ppomos.length} · actions recorded: ${actionLog.length} · squeezes: ${squeezes}`);
}

// ---------- replay: perform the recorded actions again at the same times ----------
function startReplay() {
  if (actionLog.length === 0) return;
  ppomos = [];
  nextId = 1;
  replay = { start: millis(), index: 0, events: actionLog.slice() };
}

function runReplay() {
  const elapsed = millis() - replay.start;
  while (replay.index < replay.events.length && replay.events[replay.index].t <= elapsed) {
    const a = replay.events[replay.index++];
    if (a.type === 'add') addPpomo(a.x, a.size, a.id, false);
    else if (a.type === 'squeeze') { const p = ppomos.find((q) => q.id === a.id); if (p) p.squeeze(); }
    else if (a.type === 'squeezeAll') squeezeAll(false);
    else if (a.type === 'delete') removePpomo(a.id, false);
    else if (a.type === 'clear') ppomos = [];
  }
  if (replay.index >= replay.events.length) replay = null;
}
