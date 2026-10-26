// Ppomo — FOMO piles up, with the Matter.js physics engine (ICM Week 6, work in progress)
// Every squeeze (click) drops one Ppomo. Matter.js works out the falling, bumping, rolling and stacking.
// Hold the mouse to keep squeezing. Shift + click on a Ppomo removes that one.
// Keys: space = drop one at a random spot, Backspace = remove the last one, R = start over.
// Needs Matter.js: in index.html, add this line above sketch.js
//   <script src="https://cdnjs.cloudflare.com/ajax/libs/matter-js/0.20.0/matter.min.js"></script>

// short names for the parts of Matter.js we use
const Engine = Matter.Engine;        // the physics world's clock: moves everything forward one step
const Bodies = Matter.Bodies;        // makes physical shapes (circles, rectangles)
const Composite = Matter.Composite;  // adds shapes to the world and takes them out

const W = 360;
const H = 640;
const SIZE = 120;            // drawn width of one Ppomo
const HOLD_EVERY = 6;        // while the mouse is held, one Ppomo every 6 frames

const POSES = ['front', 'front', 'front', 'front', 'butt', 'side'];   // more faces than anything else
const COLORS = ['#B9BDC7', '#B9BDC7', '#F2AABD', '#F2AABD', '#F3E6D8', '#F2C7A4', '#D2C0EC', '#BCD3F0'];
const CHEEK = '#F4A3B8';
const BUTT = '#F6B9A3';
const INK = '#3A3A3E';

let engine;                  // the Matter.js physics world
let ppomos = [];             // every Ppomo on screen (array of objects)
let log = [];                // what the user did: { action, time }
let full = false;

class Ppomo {
  constructor(x) {
    this.pose = random(POSES);
    this.color = random(COLORS);
    this.flip = random() < 0.5 ? -1 : 1;                   // side poses face left or right
    this.size = SIZE * random(0.9, 1.1);
    this.squash = 0;
    this.lastSpeed = 0;

    // the physical body: a little smaller than the drawing, so neighbours overlap a bit like jelly
    let options = { restitution: 0.1, friction: 0.6, angle: random(-0.4, 0.4) };
    if (this.pose === 'side') {
      options.chamfer = { radius: this.size * 0.28 };       // rounded corners: a soft loaf
      this.body = Bodies.rectangle(x, -this.size, this.size * 1.2, this.size * 0.6, options);
    } else {
      this.body = Bodies.circle(x, -this.size, this.size * 0.4, options);
    }
    Composite.add(engine.world, this.body);
  }

  // squash for a moment when it lands (it was moving fast, and now it has nearly stopped)
  update() {
    let speed = this.body.speed;
    if (this.lastSpeed > 3 && speed < 1) this.squash = 1;
    this.squash *= 0.88;
    this.lastSpeed = speed;
  }

  isAt(mx, my) {
    return dist(mx, my, this.body.position.x, this.body.position.y) < this.size * 0.4;
  }

  remove() {
    Composite.remove(engine.world, this.body);
  }

  show() {
    push();
    translate(this.body.position.x, this.body.position.y);   // where Matter.js says it is
    rotate(this.body.angle);                                   // how Matter.js says it is turned
    scale(this.flip * (1 + 0.15 * this.squash), 1 - 0.15 * this.squash);
    stroke(255, 255, 255, 140);                                // soft rim so neighbours read apart
    strokeWeight(2);
    if (this.pose === 'front') this.drawFront();
    else if (this.pose === 'butt') this.drawButt();
    else this.drawSide();
    pop();
  }

  // looking at you: round body, ears, big cheeks, dot eyes, ω mouth
  drawFront() {
    let s = this.size;
    fill(this.color);
    circle(-s * 0.28, -s * 0.33, s * 0.24);                // ears
    circle(s * 0.28, -s * 0.33, s * 0.24);
    ellipse(0, 0, s, s * 0.8);                             // body
    noStroke();
    fill(CHEEK);
    ellipse(-s * 0.27, s * 0.1, s * 0.34, s * 0.28);       // cheeks
    ellipse(s * 0.27, s * 0.1, s * 0.34, s * 0.28);
    fill(INK);
    circle(-s * 0.1, -s * 0.03, s * 0.06);                 // eyes
    circle(s * 0.1, -s * 0.03, s * 0.06);
    noFill();
    stroke(INK);
    strokeWeight(1.5);
    arc(-s * 0.03, s * 0.05, s * 0.06, s * 0.06, 0, PI);   // mouth (ω)
    arc(s * 0.03, s * 0.05, s * 0.06, s * 0.06, 0, PI);
  }

  // turned around: the two peachy butt cheeks
  drawButt() {
    let s = this.size;
    fill(this.color);
    circle(-s * 0.28, -s * 0.33, s * 0.24);                // ears seen from behind
    circle(s * 0.28, -s * 0.33, s * 0.24);
    ellipse(0, 0, s, s * 0.8);
    noStroke();
    fill(BUTT);
    circle(-s * 0.15, s * 0.12, s * 0.38);
    circle(s * 0.15, s * 0.12, s * 0.38);
    fill(this.color);
    ellipse(0, -s * 0.1, s * 0.6, s * 0.3);                // back over the butt
  }

  // side on: the whole loaf, head to the right
  drawSide() {
    let s = this.size;
    fill(this.color);
    ellipse(-s * 0.15, s * 0.02, s * 1.05, s * 0.68);      // long body
    circle(s * 0.3, -s * 0.02, s * 0.6);                   // head
    circle(s * 0.28, -s * 0.3, s * 0.2);                   // ear
    noStroke();
    fill(BUTT);
    circle(-s * 0.6, s * 0.05, s * 0.3);                   // butt
    fill(CHEEK);
    circle(s * 0.48, s * 0.08, s * 0.26);                  // cheek
    fill(INK);
    circle(s * 0.42, -s * 0.05, s * 0.06);                 // eye
  }
}

function setup() {
  createCanvas(W, H);
  textFont('sans-serif');
  engine = Engine.create();                                // gravity points down by default

  // floor and two side walls that never move (isStatic), just outside the canvas
  let wall = { isStatic: true };
  Composite.add(engine.world, [
    Bodies.rectangle(W / 2, H + 25, W * 2, 50, wall),      // floor
    Bodies.rectangle(-25, H / 2, 50, H * 3, wall),         // left wall
    Bodies.rectangle(W + 25, H / 2, 50, H * 3, wall),      // right wall
  ]);
}

function draw() {
  background(244, 236, 232);
  Engine.update(engine, 1000 / 60);                        // move the physics world forward 1/60 s

  if (mouseIsPressed && frameCount % HOLD_EVERY === 0 && !keyIsDown(SHIFT)) squeeze(mouseX);

  full = false;
  for (let p of ppomos) {
    p.update();
    p.show();
    if (p.body.position.y < p.size * 0.4 && p.body.speed < 0.3) full = true;   // the pile reached the top
  }
  drawInfo();
}

// one squeeze = one new Ppomo
function squeeze(x) {
  if (full) return;
  ppomos.push(new Ppomo(constrain(x + random(-10, 10), 40, W - 40)));
  log.push({ action: 'squeeze', time: millis() });
}

function mousePressed() {
  if (keyIsDown(SHIFT)) {
    // Shift + click: remove the Ppomo under the mouse.
    // Go backwards: the last ones are drawn on top, and splice() shifts everything after i.
    for (let i = ppomos.length - 1; i >= 0; i--) {
      if (ppomos[i].isAt(mouseX, mouseY)) {
        ppomos[i].remove();
        ppomos.splice(i, 1);
        log.push({ action: 'remove', time: millis() });
        return;
      }
    }
    return;
  }
  squeeze(mouseX);
}

function keyPressed() {
  if (key === ' ') {
    squeeze(random(W));
  } else if ((key === 'Backspace' || keyCode === 8) && ppomos.length > 0) {
    ppomos[ppomos.length - 1].remove();
    ppomos.pop();
    log.push({ action: 'remove', time: millis() });
  } else if (key === 'r' || key === 'R') {
    for (let p of ppomos) p.remove();
    ppomos = [];
    log.push({ action: 'reset', time: millis() });
  }
}

// count squeezes from the log and show them
function drawInfo() {
  let squeezes = 0;
  for (let entry of log) {
    if (entry.action === 'squeeze') squeezes++;
  }
  noStroke();
  fill(255, 255, 255, 190);
  rect(10, 10, 132, 46, 10);
  fill(46, 43, 42);
  textSize(15);
  textAlign(LEFT, TOP);
  text(ppomos.length + ' Ppomo' + (ppomos.length === 1 ? '' : 's'), 20, 17);
  fill(122, 116, 111);
  textSize(12);
  text('squeezes: ' + squeezes + (full ? ' · full!' : ''), 20, 37);
}
