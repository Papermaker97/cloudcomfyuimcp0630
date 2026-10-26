// Ppomo — FOMO piles up (ICM Week 6, work in progress)
// Every press of the screen (= every squeeze of Ppomo) drops one Ppomo from the top onto the floor.
// It falls into the column you pressed and lands on top of the Ppomos already there.
// Backspace removes the Ppomo that fell last.

const W = 360;
const H = 640;
const SIZE = 60;              // size of one Ppomo = column width
const COLS = W / SIZE;        // number of columns (6)
const STACK_STEP = SIZE * 0.8; // overlap a little when stacking so the pile looks squishy
const GROUND = H - 40;        // floor line
const GRAVITY = 0.6;

// a different pastel color for each Ppomo (from my #4 proposal)
const PASTELS = ['#F6C9D3', '#C9DDF6', '#D7F0C9', '#F6E3B8', '#E2D2F4', '#BFE8E4'];

let ppomos = [];   // the Ppomos on screen (array of objects)
let log = [];      // record of user actions: { action, time }

class Ppomo {
  constructor(col, stackIndex) {
    this.col = col;
    this.x = col * SIZE + SIZE / 2;
    this.y = -SIZE;                                   // start above the screen
    this.targetY = GROUND - SIZE / 2 - stackIndex * STACK_STEP;   // landing height
    this.speed = 0;
    this.landed = false;
    this.squash = 0;                                  // squash on landing (1 → 0)
    this.color = random(PASTELS);
  }

  fall() {
    if (this.landed) {
      this.squash *= 0.85;                            // the squash slowly relaxes
      return;
    }
    this.speed += GRAVITY;
    this.y += this.speed;
    if (this.y >= this.targetY) {
      this.y = this.targetY;
      this.landed = true;
      this.squash = 1;
    }
  }

  show() {
    push();
    translate(this.x, this.y + (SIZE / 2) * 0.2 * this.squash);   // keep the bottom on the ground while squashed
    scale(1 + 0.2 * this.squash, 1 - 0.2 * this.squash);
    noStroke();

    // ears
    fill(this.color);
    circle(-SIZE * 0.28, -SIZE * 0.36, SIZE * 0.26);
    circle(SIZE * 0.28, -SIZE * 0.36, SIZE * 0.26);
    // body
    ellipse(0, 0, SIZE, SIZE * 0.9);
    // cheeks
    fill(244, 150, 170, 150);
    ellipse(-SIZE * 0.25, SIZE * 0.08, SIZE * 0.26, SIZE * 0.17);
    ellipse(SIZE * 0.25, SIZE * 0.08, SIZE * 0.26, SIZE * 0.17);
    // eyes
    fill(58, 58, 62);
    circle(-SIZE * 0.12, -SIZE * 0.04, SIZE * 0.07);
    circle(SIZE * 0.12, -SIZE * 0.04, SIZE * 0.07);
    // mouth (ω)
    noFill();
    stroke(58, 58, 62);
    strokeWeight(1.5);
    arc(-SIZE * 0.035, SIZE * 0.06, SIZE * 0.07, SIZE * 0.07, 0, PI);
    arc(SIZE * 0.035, SIZE * 0.06, SIZE * 0.07, SIZE * 0.07, 0, PI);
    pop();
  }
}

function setup() {
  createCanvas(W, H);
  textFont('sans-serif');
}

function draw() {
  background(250, 247, 243);

  // floor
  stroke(228, 223, 217);
  strokeWeight(2);
  line(0, GROUND, W, GROUND);

  for (let i = 0; i < ppomos.length; i++) {
    ppomos[i].fall();
    ppomos[i].show();
  }

  drawInfo();
}

// count how many Ppomos are in a column
function countInColumn(col) {
  let n = 0;
  for (let i = 0; i < ppomos.length; i++) {
    if (ppomos[i].col === col) n++;
  }
  return n;
}

// one squeeze = add one Ppomo
function squeeze(x) {
  let col = constrain(floor(x / SIZE), 0, COLS - 1);
  let n = countInColumn(col);
  let topY = GROUND - SIZE / 2 - n * STACK_STEP;
  if (topY < SIZE) {                       // this column is full
    log.push({ action: 'full', time: millis() });
    return;
  }
  ppomos.push(new Ppomo(col, n));
  log.push({ action: 'squeeze', time: millis() });
}

function mousePressed() {
  squeeze(mouseX);
}

function keyPressed() {
  if (key === ' ') {
    squeeze(random(W));                    // space: drop into a random column
  } else if (keyCode === BACKSPACE && ppomos.length > 0) {
    ppomos.pop();                          // remove the last Ppomo (it's on top, so nothing else moves)
    log.push({ action: 'remove', time: millis() });
  }
}

// count squeezes from the log array and show them
function drawInfo() {
  let squeezes = 0;
  for (let i = 0; i < log.length; i++) {
    if (log[i].action === 'squeeze') squeezes++;
  }
  noStroke();
  fill(46, 43, 42);
  textSize(16);
  textAlign(LEFT, TOP);
  text(ppomos.length + ' Ppomo' + (ppomos.length === 1 ? '' : 's'), 16, 16);
  fill(122, 116, 111);
  textSize(12);
  text('squeezes: ' + squeezes, 16, 40);
  textAlign(CENTER, BOTTOM);
  text('click to squeeze · Backspace to remove', W / 2, H - 12);
}
