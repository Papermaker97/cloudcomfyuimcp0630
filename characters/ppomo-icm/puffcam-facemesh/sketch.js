// noprotect
// ^ tells the p5 web editor not to stop the pixel loops on slower computers (they are long, not infinite).
/*
  Ppomo Puff Cam: FaceMesh (ICM Week 9)

  Week 8's Puff Cam puffed two cheek-shaped pixel regions at fixed spots that you dragged into place.
  This version finds your face with ml5.js FaceMesh, so the puffing follows your real cheeks.
  FaceMesh only says WHERE the cheeks are. The puff itself is still done pixel by pixel:
  every pixel inside a cheek is re-coloured from a point closer to the cheek's centre (a bulge),
  then blushed pink.

  Controls
    Click the video (or press Space)   → squeeze: both cheeks puff up one level (up to 6)
    0 or the "Deflate" button           → back to normal
    Sliders                             → puff strength, and cheek size compared to your face
    "show tracking"                     → draws the face points the cheeks are following

  How it works (each frame)
    1. Draw the webcam image, mirrored, onto the canvas.
    2. Move each cheek toward the newest FaceMesh position (smoothed, so it does not jitter).
       FaceMesh works on the un-mirrored video, so its x is flipped to match the mirrored canvas.
       If no face is found, the cheeks stay where they were last seen.
    3. loadPixels() and keep an untouched copy of the frame (src). For every pixel inside a cheek,
       read the colour from a point closer to the centre in src (reading and writing the same array
       smears the colours), mix in pink, and updatePixels().

  Credits
    - ml5.js FaceMesh (ml5.js 1.x): https://docs.ml5js.org/#/reference/facemesh
    - The Coding Train, ml5.js 1.0 FaceMesh tutorial: https://thecodingtrain.com/tracks/ml5js-beginners-guide/ml5/facemesh
    - Face landmark map (MediaPipe Face Mesh, 468 points):
      https://github.com/google-ai-edge/mediapipe/blob/master/mediapipe/modules/face_geometry/data/canonical_face_model_uv_visualization.png
    - Pixel array and webcam: Allison Parrish, "Working with video" (https://creative-coding.decontextualize.com/video/)
      and The Coding Train 11.1-11.3. p5.js reference: createCapture(), loadPixels(), pixels[], updatePixels().
*/

// LITE = true bends a 320x240 frame and the page shows it scaled up. Set false on a fast computer.
const LITE = true;
const W = LITE ? 320 : 480;
const H = LITE ? 240 : 360;
const K = W / 480;
const MAX_LEVEL = 6;
const PINK = [242, 170, 189];

// FaceMesh landmark numbers around each cheek (averaged so one noisy point does not jump the cheek)
const CHEEK_POINTS = [
  [50, 123, 147, 187],     // the cheek on the left of the un-mirrored video (apple of the cheek, below the outer eye)
  [280, 352, 376, 411],    // the same points on the other cheek
];
const FACE_EDGES = [234, 454]; // the two sides of the face, to size the cheeks to the face
const FOLLOW = 0.45;           // 0..1: how quickly a cheek moves to the new face position each frame
const LOST_AFTER = 800;        // ms without a face before showing "looking for your face"

let cam;
let faceMesh;
let faces = [];
let lastFaceTime = -Infinity;
let faceWidth = 0;             // width of the face in canvas pixels (0 until a face is seen)

let cheeks = [];
let squeezes = 0;
let src;
let strengthSlider, sizeSlider, trackCheckbox, countP;

// ---------- one cheek: a round pixel region that can puff up ----------
class Cheek {
  constructor(x, y) {
    this.x = x;
    this.y = y;
    this.level = 0;
    this.puff = 0;
    this.vel = 0;
  }

  get r() {
    // the cheek is a fraction of the face width; before a face is seen, use a fixed size
    const base = faceWidth > 0 ? faceWidth * sizeSlider.value() : 60 * K;
    return base * (1 + 0.25 * max(0, this.puff));
  }

  follow(tx, ty) {
    this.x = lerp(this.x, tx, FOLLOW);
    this.y = lerp(this.y, ty, FOLLOW);
  }

  isResting() {
    return this.level === 0 && abs(this.puff) < 0.005 && abs(this.vel) < 0.005;
  }

  squeeze() {
    if (this.level < MAX_LEVEL) this.level++;
    this.vel += 0.35;
  }

  deflate() {
    this.level = 0;
    this.vel -= 0.2;
  }

  update() {
    const target = (this.level / MAX_LEVEL) * strengthSlider.value();
    this.vel += (target - this.puff) * 0.12;
    this.vel *= 0.84;
    this.puff += this.vel;
  }

  bend() {
    if (this.isResting()) return;
    const R = this.r, R2 = R * R;
    const power = 1 + max(-0.4, this.puff);
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
        if (d2 >= R2 || d2 === 0) continue;
        const t = Math.sqrt(d2) / R;
        const k = Math.pow(t, power - 1);
        let sx = Math.round(cx + dx * k), sy = Math.round(cy + dy * k);
        sx = sx < 0 ? 0 : sx > W - 1 ? W - 1 : sx;
        sy = sy < 0 ? 0 : sy > H - 1 ? H - 1 : sy;
        const from = (sy * W + sx) * 4;
        const to = (y * W + x) * 4;
        const w = blush * (1 - t) * (1 - t);
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

// ---------- FaceMesh ----------
function preload() {
  // one face is enough; refineLandmarks adds iris points we do not need
  faceMesh = ml5.faceMesh({ maxFaces: 1, refineLandmarks: false, flipped: false });
}

function gotFaces(results) {
  faces = results;
  if (faces.length > 0) lastFaceTime = millis();
}

// a FaceMesh point (un-mirrored video coordinates) → a point on the mirrored canvas
function toCanvas(kp) {
  const sx = W / cam.width, sy = H / cam.height;
  return { x: W - kp.x * sx, y: kp.y * sy };
}

function averagePoint(keypoints, ids) {
  let x = 0, y = 0;
  for (const i of ids) {
    const p = toCanvas(keypoints[i]);
    x += p.x;
    y += p.y;
  }
  return { x: x / ids.length, y: y / ids.length };
}

function trackCheeks() {
  if (faces.length === 0) return;               // no face this frame: keep the last positions
  const kp = faces[0].keypoints;
  if (!kp || kp.length < 468) return;
  const a = toCanvas(kp[FACE_EDGES[0]]), b = toCanvas(kp[FACE_EDGES[1]]);
  const w = dist(a.x, a.y, b.x, b.y);
  faceWidth = faceWidth === 0 ? w : lerp(faceWidth, w, FOLLOW);
  for (let i = 0; i < cheeks.length; i++) {
    const p = averagePoint(kp, CHEEK_POINTS[i]);
    cheeks[i].follow(p.x, p.y);
  }
}

function showTracking() {
  if (faces.length === 0) return;
  const kp = faces[0].keypoints;
  noStroke();
  fill(255, 120, 160);
  for (const ids of CHEEK_POINTS) for (const i of ids) {
    const p = toCanvas(kp[i]);
    circle(p.x, p.y, 4);
  }
  fill(120, 200, 255);
  for (const i of FACE_EDGES) {
    const p = toCanvas(kp[i]);
    circle(p.x, p.y, 5);
  }
}

// ---------- setup ----------
function setup() {
  createCanvas(W, H);
  pixelDensity(1);
  cam = createCapture(VIDEO);
  cam.size(W, H);
  cam.hide();
  faceMesh.detectStart(cam, gotFaces);

  const panel = createDiv().id('panel');
  createSpan('Puff strength').parent(panel);
  strengthSlider = createSlider(0.3, 2.5, 1.4, 0.05).parent(panel);
  createSpan('Cheek size').parent(panel);
  sizeSlider = createSlider(0.1, 0.35, 0.2, 0.01).parent(panel);   // cheek radius as a share of the face width
  trackCheckbox = createCheckbox(' show tracking (the face points the cheeks follow)', false).parent(panel).class('wide');
  const buttons = createDiv().parent(panel).class('wide buttons');
  createButton('Squeeze').parent(buttons).mousePressed(squeezeAll);
  createButton('Deflate').parent(buttons).mousePressed(deflateAll);
  countP = createP('').parent(panel).class('wide');

  // starting spots until the first face is found
  cheeks.push(new Cheek(W * 0.65, H * 0.62));
  cheeks.push(new Cheek(W * 0.35, H * 0.62));
}

// ---------- draw ----------
function draw() {
  push();
  translate(W, 0);
  scale(-1, 1);
  image(cam, 0, 0, W, H);
  pop();

  trackCheeks();

  for (const c of cheeks) c.update();
  if (!cheeks.every((c) => c.isResting())) {
    loadPixels();
    src = pixels.slice();
    for (const c of cheeks) c.bend();
    updatePixels();
  }

  const lost = millis() - lastFaceTime > LOST_AFTER;
  if (trackCheckbox.checked() || lost) for (const c of cheeks) c.showGuide();
  if (trackCheckbox.checked()) showTracking();

  noStroke();
  fill(255);
  textSize(16 * K);
  text(`squeezes: ${squeezes}`, 16 * K, 28 * K);
  if (lost) {
    textAlign(CENTER);
    text('looking for your face…', W / 2, H - 16 * K);
    textAlign(LEFT);
  }
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

function mouseReleased() {
  const onCanvas = mouseX >= 0 && mouseX <= W && mouseY >= 0 && mouseY <= H;
  if (onCanvas) squeezeAll();
}

function keyPressed() {
  if (key === ' ' || keyCode === 32) {
    squeezeAll();
    return false;
  }
  if (key === '0' || key === 'r' || key === 'R') deflateAll();
}
