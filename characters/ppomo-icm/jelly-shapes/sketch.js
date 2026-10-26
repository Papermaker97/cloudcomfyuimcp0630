// Ppomo — FOMO piles up, jelly version drawn with shapes only (ICM Week 6, work in progress)
// Every squeeze (click) drops one Ppomo. It falls, slides into a gap, and settles into the pile,
// pressing into its neighbours a little like jelly. Hold the mouse to keep squeezing.
// Keys: space = drop one at a random spot, Backspace = remove the last one, R = start over.

const W = 360;
const H = 640;
const SIZE = 120;            // body width of one Ppomo
const GRAVITY = 0.5;
const JELLY = 0.75;          // neighbours may come this close (1 = just touching, smaller = more squished)
const HOLD_EVERY = 6;        // while the mouse is held, one Ppomo every 6 frames

const POSES = ['front', 'front', 'front', 'front', 'butt', 'side'];   // more faces than anything else
const COLORS = ['#B9BDC7', '#B9BDC7', '#F2AABD', '#F2AABD', '#F3E6D8', '#F2C7A4', '#D2C0EC', '#BCD3F0'];
const CHEEK = '#F4A3B8';
const BUTT = '#F6B9A3';
const INK = '#3A3A3E';

let ppomos = [];             // every Ppomo on screen (array of objects)
let log = [];                // what the user did: { action, time }
let full = false;

class Ppomo {
  constructor(x) {
    this.pose = random(POSES);
    this.color = random(COLORS);
    this.flip = random() < 0.5 ? -1 : 1;                   // side poses face left or right
    this.size = SIZE * random(0.9, 1.1);
    this.r = this.size * (this.pose === 'side' ? 0.5 : 0.45);
    this.x = x;
    this.y = -this.size;
    this.vx = 0;
    this.vy = 0;
    this.angle = random() < 0.8 ? random(-0.35, 0.35) : random(-0.9, 0.9);
    this.settled = false;
    this.stillFrames = 0;
    this.squash = 0;
  }

  // fall, then get pushed out of the Ppomos it lands on, so it slides into the gaps
  update(others) {
    if (this.settled) {
      this.squash *= 0.88;
      return;
    }
    this.vy += GRAVITY;
    let oldX = this.x;
    let oldY = this.y;
    this.x += this.vx;
    this.y += this.vy;

    let touching = false;
    for (let other of others) {
      if (other === this || !other.settled) continue;
      let dx = this.x - other.x;
      let dy = this.y - other.y;
      let d = sqrt(dx * dx + dy * dy);
      let minD = (this.r + other.r) * JELLY;
      if (d < minD && d > 0) {
        this.x += (dx / d) * (minD - d);                   // push out along the line between centres
        this.y += (dy / d) * (minD - d);
        touching = true;
      }
    }
    let floorY = H - this.r * 0.6;
    if (this.y > floorY) {
      this.y = floorY;
      touching = true;
    }
    this.x = constrain(this.x, 0, W);                      // centres stay on screen; bodies may be cut off

    // new speed = how far it actually moved, a little damped (soft, jelly-like)
    this.vx = (this.x - oldX) * 0.8;
    this.vy = (this.y - oldY) * 0.8;

    if (touching && abs(this.vx) + abs(this.vy) < 0.6) this.stillFrames++;
    else this.stillFrames = 0;
    if (this.stillFrames > 8) {
      this.settled = true;
      this.squash = 1;
      if (this.y < this.size * 0.4) full = true;           // the pile reached the top
    }
  }

  show() {
    push();
    translate(this.x, this.y);
    rotate(this.angle);
    scale(this.flip * (1 + 0.15 * this.squash), 1 - 0.15 * this.squash);
    stroke(255, 255, 255, 140);                            // soft rim so neighbours read apart
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
}

function draw() {
  background(244, 236, 232);

  if (mouseIsPressed && frameCount % HOLD_EVERY === 0) squeeze(mouseX);

  for (let p of ppomos) {
    p.update(ppomos);
    p.show();
  }
  drawInfo();
}

// one squeeze = one new Ppomo
function squeeze(x) {
  if (full) return;
  ppomos.push(new Ppomo(x + random(-10, 10)));
  log.push({ action: 'squeeze', time: millis() });
}

function mousePressed() {
  squeeze(mouseX);
}

function keyPressed() {
  if (key === ' ') {
    squeeze(random(W));
  } else if ((key === 'Backspace' || keyCode === 8) && ppomos.length > 0) {
    ppomos.pop();
    full = false;
    log.push({ action: 'remove', time: millis() });
  } else if (key === 'r' || key === 'R') {
    ppomos = [];
    full = false;
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
