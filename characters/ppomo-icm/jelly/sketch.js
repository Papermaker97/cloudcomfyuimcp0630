// Ppomo — FOMO piles up, jelly version (ICM Week 6, work in progress)
// Every squeeze (click) drops one Ppomo. It falls, slides into a gap, and settles into the pile,
// pressing into its neighbours a little like jelly. Hold the mouse to keep squeezing.
// The Ppomo pictures are renders of the 3D model (sprites/<pose>-<color>.png).
// Keys: space = drop one at a random spot, Backspace = remove the last one, R = start over.

const W = 360;
const H = 640;
const SIZE = 200;            // drawn size of a sprite (the Ppomo fills ~60-80% of it)
const GRAVITY = 0.5;
const JELLY = 0.72;          // neighbours may come this close (1 = just touching, smaller = more squished)
const HOLD_EVERY = 6;        // while the mouse is held, one Ppomo every 6 frames

const POSES = ['front', 'front', 'front', 'front', 'butt', 'side', 'peek'];   // more faces than anything else
const COLORS = ['grey', 'grey', 'pink', 'pink', 'cream', 'peach', 'lilac', 'sky'];
// rough body radius for each pose, as a fraction of SIZE
const HIT = { front: 0.27, butt: 0.27, side: 0.31, peek: 0.29 };

let sprites = {};            // sprites['front-pink'] = image
let ppomos = [];             // every Ppomo on screen (array of objects)
let log = [];                // what the user did: { action, time }
let full = false;


class Ppomo {
  constructor(x) {
    this.pose = random(POSES);
    this.color = random(COLORS);
    this.img = sprites[this.pose + '-' + this.color];
    this.flip = random() < 0.5 ? -1 : 1;                   // side poses face left or right
    this.size = SIZE * random(0.9, 1.1);
    this.r = HIT[this.pose] * this.size;
    this.x = x;
    this.y = -this.size / 2;
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
      if (this.y < this.size * 0.2) full = true;           // the pile reached the top
    }
  }

  show() {
    push();
    translate(this.x, this.y);
    rotate(this.angle);
    scale(this.flip * (1 + 0.15 * this.squash), 1 - 0.15 * this.squash);
    imageMode(CENTER);
    image(this.img, 0, 0, this.size, this.size);
    pop();
  }
}

// p5.js 2.x has no preload(), so the pictures load in setup() with await (this also works in 1.x)
async function setup() {
  createCanvas(W, H);
  textFont('sans-serif');
  for (let pose of ['front', 'butt', 'side', 'peek']) {
    for (let color of ['grey', 'pink', 'cream', 'peach', 'lilac', 'sky']) {
      sprites[pose + '-' + color] = await loadImage('sprites/' + pose + '-' + color + '.png');
    }
  }
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
