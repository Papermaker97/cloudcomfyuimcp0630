/*
  Ppomo Doomscroll Pile (ICM: array of objects, Week 6-7)

  Concept: the canvas is a phone feed. Every time you scroll, a Ppomo drops into the feed.
  The longer you doomscroll, the higher the pile gets, until Ppomos fill the screen.
  Your scrolling is recorded: how far you scrolled (in metres), when, and how many Ppomos it made.

  Controls
    Scroll (mouse wheel / trackpad) or drag up on the canvas  → the feed moves and Ppomos fall
    Click empty space                                          → drop one Ppomo where you clicked
    Click a Ppomo                                              → pop it (it disappears)
    Backspace                                                  → remove the last Ppomo
    Space                                                      → drop one Ppomo at a random spot
  DOM controls under the canvas change how much scrolling makes one Ppomo, their size, and more.

  Credits
    - Ppomo pictures: renders of my 3D Ppomo model (made for this project with help from Claude).
    - Physics: Matter.js 0.20.0 (https://brm.io/matter-js/), Engine / Bodies / Composite as in its docs.
    - p5.js reference for mouseWheel(), loadImage(), createSlider() etc.: https://p5js.org/reference/
    - The sketch code was written with help from Claude.
*/

// ---------- Matter.js short names ----------
const Engine = Matter.Engine;        // the physics world's clock
const Bodies = Matter.Bodies;        // makes physical shapes
const Composite = Matter.Composite;  // adds shapes to the world and removes them

// ---------- settings ----------
const W = 360;                       // phone-shaped canvas (9:16)
const H = 640;
const POSES = ['front', 'front', 'front', 'front', 'butt', 'side', 'peek'];
const COLORS = ['grey', 'grey', 'grey', 'pink', 'cream', 'peach', 'lilac', 'sky'];
const HIT = { front: 0.27, butt: 0.27, side: 0.31, peek: 0.29 };   // body radius as a fraction of the sprite size
const PX_TO_M = 0.0254 / 96;         // one CSS pixel is about 0.26 mm

// ---------- global variables ----------
let engine;
let sprites = {};                    // sprites['front-pink'] = image
let ppomos = [];                     // ARRAY OF OBJECTS: every Ppomo on screen
let popping = [];                    // Ppomos playing their pop animation before they disappear
let actionLog = [];                  // every user action: { t, type, px }
let feedOffset = 0;                  // how far the fake feed has moved (px)
let scrolledPx = 0;                  // total distance scrolled this session (px)
let scrollBank = 0;                  // scrolled distance not yet turned into a Ppomo
let sessionStart = 0;
let full = false;

let perPpomoSlider, sizeSlider, feedCheckbox, logBox;

// ---------- the Ppomo class ----------
class Ppomo {
  constructor(x, size) {
    this.pose = random(POSES);
    this.color = random(COLORS);
    this.img = sprites[this.pose + '-' + this.color];
    this.flip = random() < 0.5 ? -1 : 1;
    this.size = size * random(0.9, 1.1);
    this.r = HIT[this.pose] * this.size;
    this.squash = 0;
    this.lastSpeed = 0;
    this.age = 0;                    // frames since it was dropped
    this.body = Bodies.circle(x, -this.size * 0.5, this.r, {
      restitution: 0.15, friction: 0.5, angle: random(-0.4, 0.4),
    });
    Composite.add(engine.world, this.body);
  }

  update() {
    // squash for a moment when it lands (fast before, nearly stopped now)
    const speed = this.body.speed;
    if (this.lastSpeed > 3 && speed < 1) this.squash = 1;
    this.squash *= 0.86;
    this.lastSpeed = speed;
    this.age++;
  }

  contains(px, py) {
    return dist(px, py, this.body.position.x, this.body.position.y) < this.r;
  }

  removeBody() {
    Composite.remove(engine.world, this.body);
  }

  show(extraScale = 1, alpha = 255) {
    push();
    translate(this.body.position.x, this.body.position.y);
    rotate(this.body.angle);
    scale(this.flip * (1 + 0.14 * this.squash) * extraScale, (1 - 0.14 * this.squash) * extraScale);
    tint(255, alpha);
    imageMode(CENTER);
    image(this.img, 0, 0, this.size, this.size);
    pop();
  }
}

// ---------- setup ----------
async function setup() {
  createCanvas(W, H);
  for (const pose of ['front', 'butt', 'side', 'peek']) {
    for (const color of ['grey', 'pink', 'cream', 'peach', 'lilac', 'sky']) {
      sprites[pose + '-' + color] = await loadImage('sprites/' + pose + '-' + color + '.png');
    }
  }

  engine = Engine.create();
  const wall = { isStatic: true };
  Composite.add(engine.world, [
    Bodies.rectangle(W / 2, H + 25, W * 2, 50, wall),   // floor
    Bodies.rectangle(-25, H / 2, 50, H * 4, wall),      // left wall
    Bodies.rectangle(W + 25, H / 2, 50, H * 4, wall),   // right wall
  ]);

  // DOM controls
  const panel = createDiv().id('panel');
  createSpan('Scroll per Ppomo').parent(panel);
  perPpomoSlider = createSlider(40, 600, 160, 10).parent(panel);
  createSpan('Ppomo size').parent(panel);
  sizeSlider = createSlider(100, 240, 160, 10).parent(panel);
  feedCheckbox = createCheckbox(' show the feed', true).parent(panel).class('wide');
  const buttons = createDiv().parent(panel).class('wide buttons');
  createButton('Clear pile').parent(buttons).mousePressed(clearPile);
  createButton('Save log').parent(buttons).mousePressed(() => saveJSON(actionLog, 'ppomo-doomscroll-log.json'));
  logBox = createDiv('').parent(panel).class('wide').id('log');

  sessionStart = millis();
}

// ---------- draw ----------
function draw() {
  if (!engine) {                       // sprites still loading
    background(250, 249, 252);
    return;
  }
  background(250, 249, 252);
  if (feedCheckbox.checked()) drawFeed();

  Engine.update(engine, 1000 / 60);

  full = false;
  for (const p of ppomos) {
    p.update();
    p.show();
    // the pile reached the top: an old, resting Ppomo near the top (a new one starts up there too, so skip those)
    if (p.age > 90 && p.body.position.y < 120 && p.body.speed < 0.3) full = true;
  }
  // pop animation: grow a little and fade out, then forget it
  for (let i = popping.length - 1; i >= 0; i--) {
    const p = popping[i];
    p.popT += 0.08;
    p.show(1 + p.popT * 0.4, 255 * (1 - p.popT));
    if (p.popT >= 1) popping.splice(i, 1);
  }

  cursor(ppomoAt(mouseX, mouseY) ? HAND : ARROW);
  drawHud();
}

// a fake social feed: cards that move up as you scroll
function drawFeed() {
  const cardH = 300;
  const first = floor(feedOffset / cardH);
  noStroke();
  for (let i = first; i < first + 4; i++) {
    const y = i * cardH - feedOffset + 70;
    fill(255);
    rect(16, y, W - 32, cardH - 20, 18);
    fill(230, 227, 236);
    circle(42, y + 26, 28);                          // avatar
    rect(64, y + 18, 110, 8, 4);                      // name
    fill(238, 235, 243);
    rect(28, y + 50, W - 56, 170, 12);                // post picture
    fill(230, 227, 236);
    rect(28, y + 232, W - 120, 8, 4);                 // caption lines
    rect(28, y + 248, W - 170, 8, 4);
  }
}

function drawHud() {
  const minutes = (millis() - sessionStart) / 60000;
  noStroke();
  fill(250, 249, 252, 235);
  rect(0, 0, W, 60);
  fill(60, 58, 70);
  textAlign(LEFT, TOP);
  textSize(16);
  textStyle(BOLD);
  text('ppomo feed', 20, 14);
  textStyle(NORMAL);
  textSize(12);
  fill(110, 106, 124);
  text(`scrolled ${(scrolledPx * PX_TO_M).toFixed(2)} m · ${ppomos.length} Ppomos · ${minutes.toFixed(1)} min`, 20, 36);
  if (full) {
    fill(60, 58, 70, 220);
    rect(40, H / 2 - 40, W - 80, 80, 20);
    fill(255);
    textAlign(CENTER, CENTER);
    textSize(15);
    text(`You scrolled ${(scrolledPx * PX_TO_M).toFixed(1)} m.\nPpomo says: take a break?`, W / 2, H / 2);
  }
}

// ---------- scrolling = the recorded behaviour ----------
function scrollBy(amount) {
  const d = abs(amount);
  feedOffset = max(0, feedOffset + amount);
  scrolledPx += d;
  scrollBank += d;
  // every "Scroll per Ppomo" pixels of scrolling drops one Ppomo
  while (scrollBank >= perPpomoSlider.value()) {
    scrollBank -= perPpomoSlider.value();
    dropPpomo(random(40, W - 40), 'scroll-drop');
  }
}

function mouseWheel(event) {
  if (mouseX < 0 || mouseX > width || mouseY < 0 || mouseY > height) return;   // let the page scroll outside the canvas
  const amount = event.deltaY !== undefined ? event.deltaY : event.delta;
  scrollBy(amount);
  logAction('scroll', round(amount));
  return false;                        // don't scroll the web page
}

// dragging up on the canvas works like a phone swipe
function mouseDragged() {
  if (mouseX < 0 || mouseX > width || mouseY < 0 || mouseY > height) return;
  const amount = pmouseY - mouseY;
  if (amount !== 0) {
    scrollBy(amount);
    logAction('swipe', round(amount));
  }
}

// ---------- click and keys: add and remove ----------
let pressX = 0, pressY = 0;
function mousePressed() {
  pressX = mouseX;
  pressY = mouseY;
}

function mouseReleased() {
  if (mouseX < 0 || mouseX > width || mouseY < 0 || mouseY > height) return;
  if (dist(mouseX, mouseY, pressX, pressY) > 6) return;    // it was a swipe, not a click
  const hit = ppomoAt(mouseX, mouseY);
  if (hit) popPpomo(hit);
  else dropPpomo(mouseX, 'click-drop');
}

function keyPressed() {
  if (key === ' ' || keyCode === 32) {
    dropPpomo(random(40, W - 40), 'key-drop');
    return false;
  }
  if ((key === 'Backspace' || keyCode === 8) && ppomos.length > 0) {
    popPpomo(ppomos[ppomos.length - 1]);
    return false;
  }
}

function dropPpomo(x, type) {
  if (full) return;
  ppomos.push(new Ppomo(constrain(x, 40, W - 40), sizeSlider.value()));
  logAction(type, 0);
}

function popPpomo(p) {
  const i = ppomos.indexOf(p);
  if (i === -1) return;
  p.removeBody();
  ppomos.splice(i, 1);
  p.popT = 0;
  popping.push(p);
  logAction('pop', 0);
}

function clearPile() {
  for (const p of ppomos) p.removeBody();
  ppomos = [];
  logAction('clear', 0);
}

function ppomoAt(x, y) {
  for (let i = ppomos.length - 1; i >= 0; i--) {     // last added is drawn on top
    if (ppomos[i].contains(x, y)) return ppomos[i];
  }
  return null;
}

// ---------- recording ----------
function logAction(type, px) {
  actionLog.push({ t: round(millis() - sessionStart), type, px, ppomos: ppomos.length });
  // show a short summary: totals, then the last few actions that are not plain scroll ticks
  const count = (name) => actionLog.filter((a) => a.type === name).length;
  const recent = actionLog.filter((a) => !['scroll', 'swipe', 'scroll-drop'].includes(a.type)).slice(-5).reverse();
  logBox.html(
    `scroll events: ${count('scroll') + count('swipe')} · drops from scrolling: ${count('scroll-drop')} · ` +
    `clicks/keys: ${count('click-drop') + count('key-drop')} · pops: ${count('pop')}<br>` +
    recent.map((a) => `${(a.t / 1000).toFixed(1)}s ${a.type}`).join('<br>')
  );
}
