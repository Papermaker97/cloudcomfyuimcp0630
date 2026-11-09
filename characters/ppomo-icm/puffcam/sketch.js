// noprotect
// ^ tells the p5 web editor not to stop the pixel loops on slower computers (they are long, not infinite).
//   Newer versions of the editor read <!-- noprotect --> in index.html instead, so that line is there too.
/*
  Ppomo Puff Cam (ICM Week 8: Pixels as Data, "Parts of a Whole")

  Your webcam, but your cheeks puff up like Ppomo's every time you squeeze.
  Two round pixel regions (the cheeks) are bent outward like a magnifying bubble and blushed pink.
  Each squeeze adds one puff level; the cheeks wobble like jelly on the way.
  This is a first step toward my Winter Show piece, where squeezing the physical Ppomo will do this.

  Controls
    Click the video (or press Space)   → squeeze: both cheeks puff up one level
    Drag a cheek circle                 → move it onto your own cheek
    0 or the "Deflate" button           → back to normal
    Sliders                             → puff strength and cheek size

  How the pixels are changed (each frame)
    1. Draw the webcam image, mirrored, onto the canvas.
    2. loadPixels() and keep an untouched copy of the frame (src).
    3. For every pixel inside a cheek circle, read the colour from a point closer to the
       centre in src. Pixels near the middle get spread out over a bigger area = a bulge.
       Then mix in pink, strongest in the middle.
    4. updatePixels().

  Credits
    - Pixel array indexing and webcam capture: Allison Parrish, "Working with video"
      (https://creative-coding.decontextualize.com/video/) and The Coding Train 11.1–11.3.
    - p5.js reference: createCapture(), loadPixels(), pixels[], updatePixels().
      https://p5js.org/reference/p5/createCapture/  https://p5js.org/reference/p5/loadPixels/
      https://p5js.org/reference/p5/pixels/  https://p5js.org/reference/p5/updatePixels/
    - "// noprotect" / "<!-- noprotect -->" is a p5.js Web Editor setting, not part of p5.js itself:
      https://github.com/processing/p5.js-web-editor/issues/372
      https://github.com/processing/p5.js-web-editor/issues/458
      https://github.com/processing/p5.js-web-editor/pull/4108
    - The sketch code was written with help from Claude (prompts listed in AI-USE.md).
*/

// LITE = true bends a 320x240 frame (about half the pixels of 480x360) and the page shows it scaled up.
// Set it to false on a fast computer for a sharper image.
const LITE = true;
const W = LITE ? 320 : 480;
const H = LITE ? 240 : 360;
const K = W / 480;              // cheek sizes are designed for 480 wide, scaled by this
const MAX_LEVEL = 6;            // how many squeezes until the cheeks are fully puffed
const PINK = [242, 170, 189];   // Ppomo cheek pink

let cam;                        // the webcam
let cheeks = [];                // ARRAY OF OBJECTS: the two cheek regions
let squeezes = 0;
let src;                        // untouched copy of this frame's pixels
let strengthSlider, sizeSlider, guideCheckbox, countP;
let pressX = 0, pressY = 0, dragging = null;

// ---------- one cheek: a round pixel region that can puff up ----------
class Cheek {
  constructor(x, y) {
    this.x = x;
    this.y = y;
    this.level = 0;      // puff level 0..MAX_LEVEL (goes up by one per squeeze)
    this.puff = 0;       // how much it is bulging right now (springs toward the level)
    this.vel = 0;        // spring speed, for the jelly wobble
  }

  get r() {              // radius grows a little as it puffs
    return sizeSlider.value() * K * (1 + 0.25 * max(0, this.puff));
  }

  isResting() {          // fully deflated and still: nothing to bend, so skip the pixel loop
    return this.level === 0 && abs(this.puff) < 0.005 && abs(this.vel) < 0.005;
  }

  squeeze() {
    if (this.level < MAX_LEVEL) this.level++;
    this.vel += 0.35;    // a kick, so it overshoots and wobbles
  }

  deflate() {
    this.level = 0;
    this.vel -= 0.2;
  }

  update() {
    // a spring: pull toward the target, keep some speed, lose a little each frame
    const target = (this.level / MAX_LEVEL) * strengthSlider.value();
    this.vel += (target - this.puff) * 0.12;
    this.vel *= 0.84;
    this.puff += this.vel;
  }

  contains(px, py) {
    return dist(px, py, this.x, this.y) < this.r;
  }

  // bend the pixels inside this cheek (reads from src, writes into pixels)
  // The inner loop runs tens of thousands of times per frame, so it uses plain Math.* instead of
  // p5's sqrt()/pow()/constrain()/lerp() helpers (same maths, less overhead per call).
  bend() {
    if (this.isResting()) return;
    const R = this.r, R2 = R * R;
    const power = 1 + max(-0.4, this.puff);     // >1 = bulge out, <1 = squash in
    const blush = min(1, this.level / MAX_LEVEL) * 0.55;
    const cx = this.x, cy = this.y;
    const x0 = max(0, floor(cx - R)), x1 = min(W - 1, ceil(cx + R));
    const y0 = max(0, floor(cy - R)), y1 = min(H - 1, ceil(cy + R));
    const [pr, pg, pb] = PINK;
    for (let y = y0; y <= y1; y++) {
      const dy = y - cy;
      for (let x = x0; x <= x1; x++) {
        const dx = x - cx;
        const d2 = dx * dx + dy * dy;
        if (d2 >= R2 || d2 === 0) continue;       // outside the circle (checked without a square root)
        const t = Math.sqrt(d2) / R;              // 0 at the centre, 1 at the edge
        const k = Math.pow(t, power - 1);         // same as pow(t, power) / t: read from closer to the centre
        let sx = Math.round(cx + dx * k), sy = Math.round(cy + dy * k);
        sx = sx < 0 ? 0 : sx > W - 1 ? W - 1 : sx;
        sy = sy < 0 ? 0 : sy > H - 1 ? H - 1 : sy;
        const from = (sy * W + sx) * 4;
        const to = (y * W + x) * 4;
        const w = blush * (1 - t) * (1 - t);      // pink is strongest in the middle
        pixels[to]     = src[from]     + (pr - src[from])     * w;
        pixels[to + 1] = src[from + 1] + (pg - src[from + 1]) * w;
        pixels[to + 2] = src[from + 2] + (pb - src[from + 2]) * w;
      }
    }
  }

  showGuide() {
    noFill();
    stroke(255, 255, 255, 200);
    strokeWeight(2);
    drawingContext.setLineDash([6, 6]);
    circle(this.x, this.y, this.r * 2);
    drawingContext.setLineDash([]);
  }
}

// ---------- setup ----------
function setup() {
  createCanvas(W, H);
  pixelDensity(1);                 // one canvas pixel = one entry in pixels[], keeps the maths simple
  cam = createCapture(VIDEO);
  cam.size(W, H);
  cam.hide();

  // DOM controls
  const panel = createDiv().id('panel');
  createSpan('Puff strength').parent(panel);
  strengthSlider = createSlider(0.3, 2.5, 1.4, 0.05).parent(panel);
  createSpan('Cheek size').parent(panel);
  sizeSlider = createSlider(30, 110, 60, 1).parent(panel);
  guideCheckbox = createCheckbox(' show cheek guides (drag them onto your cheeks)', true).parent(panel).class('wide');
  const buttons = createDiv().parent(panel).class('wide buttons');
  createButton('Squeeze').parent(buttons).mousePressed(squeezeAll);
  createButton('Deflate').parent(buttons).mousePressed(deflateAll);
  countP = createP('').parent(panel).class('wide');

  cheeks.push(new Cheek(W * 0.35, H * 0.62));
  cheeks.push(new Cheek(W * 0.65, H * 0.62));
}

// ---------- draw ----------
function draw() {
  // 1. the webcam, mirrored so it feels like a mirror
  push();
  translate(W, 0);
  scale(-1, 1);
  image(cam, 0, 0, W, H);
  pop();

  // 2–4. bend the pixels inside each cheek (skipped entirely while both cheeks are resting)
  for (const c of cheeks) c.update();
  if (!cheeks.every((c) => c.isResting())) {
    loadPixels();
    src = pixels.slice();          // untouched copy to read from
    for (const c of cheeks) c.bend();
    updatePixels();
  }

  if (guideCheckbox.checked()) for (const c of cheeks) c.showGuide();

  noStroke();
  fill(255);
  textSize(16 * K);
  text(`squeezes: ${squeezes}`, 16 * K, 28 * K);
  countP.html(`Puff level ${cheeks[0].level} / ${MAX_LEVEL}. Click the video or press Space to squeeze.`);
}

// ---------- input ----------
function squeezeAll() {
  squeezes++;
  for (const c of cheeks) c.squeeze();
}

function deflateAll() {
  for (const c of cheeks) c.deflate();
}

function mousePressed() {
  pressX = mouseX;
  pressY = mouseY;
  dragging = null;
  for (const c of cheeks) if (guideCheckbox.checked() && c.contains(mouseX, mouseY)) dragging = c;
}

function mouseDragged() {
  if (dragging) {
    dragging.x = constrain(mouseX, 0, W);
    dragging.y = constrain(mouseY, 0, H);
  }
}

function mouseReleased() {
  const onCanvas = mouseX >= 0 && mouseX <= W && mouseY >= 0 && mouseY <= H;
  const wasClick = dist(mouseX, mouseY, pressX, pressY) < 5;
  if (onCanvas && wasClick) squeezeAll();   // a click (not a drag) is a squeeze
  dragging = null;
}

function keyPressed() {
  if (key === ' ' || keyCode === 32) {
    squeezeAll();
    return false;
  }
  if (key === '0' || key === 'r' || key === 'R') deflateAll();
}
