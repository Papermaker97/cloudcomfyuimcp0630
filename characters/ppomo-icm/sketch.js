// 뽀모 — FOMO가 쌓인다 (ICM Week 6, 진행 중)
// 화면을 누를 때마다(= 뽀모를 쥘 때마다) 뽀모가 한 마리씩 위에서 떨어져 바닥에 쌓인다.
// 누른 위치의 칸으로 떨어지고, 그 칸에 이미 있는 뽀모 위에 올라간다.
// Backspace: 마지막으로 떨어진 뽀모를 뺀다.

const W = 360;
const H = 640;
const SIZE = 60;              // 뽀모 한 마리 크기 = 칸 너비
const COLS = W / SIZE;        // 칸 수 (6칸)
const STACK_STEP = SIZE * 0.8; // 쌓일 때 조금씩 겹쳐서 말랑하게
const GROUND = H - 40;        // 바닥 선
const GRAVITY = 0.6;

// 마리마다 다른 파스텔 색 (#4 기획서 구상)
const PASTELS = ['#F6C9D3', '#C9DDF6', '#D7F0C9', '#F6E3B8', '#E2D2F4', '#BFE8E4'];

let ppomos = [];   // 쌓인 뽀모들 (객체 배열)
let log = [];      // 사용자 행동 기록: { action, time }

class Ppomo {
  constructor(col, stackIndex) {
    this.col = col;
    this.x = col * SIZE + SIZE / 2;
    this.y = -SIZE;                                   // 화면 위에서 시작
    this.targetY = GROUND - SIZE / 2 - stackIndex * STACK_STEP;   // 착지할 높이
    this.speed = 0;
    this.landed = false;
    this.squash = 0;                                  // 착지할 때 찌그러짐 (1 → 0)
    this.color = random(PASTELS);
  }

  fall() {
    if (this.landed) {
      this.squash *= 0.85;                            // 찌그러짐이 천천히 풀린다
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
    translate(this.x, this.y + (SIZE / 2) * 0.2 * this.squash);   // 찌그러질 때 바닥에 붙어 있게
    scale(1 + 0.2 * this.squash, 1 - 0.2 * this.squash);
    noStroke();

    // 귀
    fill(this.color);
    circle(-SIZE * 0.28, -SIZE * 0.36, SIZE * 0.26);
    circle(SIZE * 0.28, -SIZE * 0.36, SIZE * 0.26);
    // 몸
    ellipse(0, 0, SIZE, SIZE * 0.9);
    // 볼
    fill(244, 150, 170, 150);
    ellipse(-SIZE * 0.25, SIZE * 0.08, SIZE * 0.26, SIZE * 0.17);
    ellipse(SIZE * 0.25, SIZE * 0.08, SIZE * 0.26, SIZE * 0.17);
    // 눈
    fill(58, 58, 62);
    circle(-SIZE * 0.12, -SIZE * 0.04, SIZE * 0.07);
    circle(SIZE * 0.12, -SIZE * 0.04, SIZE * 0.07);
    // 입 (ω)
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

  // 바닥
  stroke(228, 223, 217);
  strokeWeight(2);
  line(0, GROUND, W, GROUND);

  for (let i = 0; i < ppomos.length; i++) {
    ppomos[i].fall();
    ppomos[i].show();
  }

  drawInfo();
}

// 그 칸에 몇 마리가 있는지 센다
function countInColumn(col) {
  let n = 0;
  for (let i = 0; i < ppomos.length; i++) {
    if (ppomos[i].col === col) n++;
  }
  return n;
}

// 뽀모를 한 번 쥐었다 = 뽀모 한 마리 추가
function squeeze(x) {
  let col = constrain(floor(x / SIZE), 0, COLS - 1);
  let n = countInColumn(col);
  let topY = GROUND - SIZE / 2 - n * STACK_STEP;
  if (topY < SIZE) {                       // 이 칸은 꽉 찼다
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
    squeeze(random(W));                    // 스페이스: 아무 칸에나 떨어뜨리기
  } else if (keyCode === BACKSPACE && ppomos.length > 0) {
    ppomos.pop();                          // 마지막 뽀모 빼기 (가장 위에 있으니 다른 뽀모는 그대로)
    log.push({ action: 'remove', time: millis() });
  }
}

// 기록 배열로 횟수를 세서 보여준다
function drawInfo() {
  let squeezes = 0;
  for (let i = 0; i < log.length; i++) {
    if (log[i].action === 'squeeze') squeezes++;
  }
  noStroke();
  fill(46, 43, 42);
  textSize(16);
  textAlign(LEFT, TOP);
  text('뽀모 ' + ppomos.length + '마리', 16, 16);
  fill(122, 116, 111);
  textSize(12);
  text('쥔 횟수 ' + squeezes, 16, 40);
  textAlign(CENTER, BOTTOM);
  text('눌러서 뽀모 쥐기 · Backspace 빼기', W / 2, H - 12);
}
