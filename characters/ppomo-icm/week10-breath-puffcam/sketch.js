// noprotect
/*
  Ppomo Breath Puff (ICM Week 10, step 2: sound applied to my Week 9 sketch)

  Week 9's Puff Cam puffed your cheeks (found with ml5 FaceMesh) one level per click.
  Now your BREATH does it: breathe out slowly toward the laptop mic and your cheeks fill up like a balloon.
  Stop, and they let the air out with a soft "pff". Talking does not count, only a breath.

  How the breath is found (tuned in the step-1 dashboard "Breath or Voice?")
    p5.AudioIn + p5.FFT. Blowing on a mic makes rumbly wind noise, strongest at 20-250 Hz.
    A voice is strongest at 300-3000 Hz. So: loud enough AND (LOW energy / VOICE energy) > ratio  ->  breath.

  Sound out (p5.sound synthesis, no files)
    full cheeks -> two soft sine notes;  letting go -> filtered white noise "pff".
    Both sit above 300 Hz on purpose, so the mic does not hear them as a breath.
    "sound" can be turned off: Ppomo is meant to be used quietly around other people.

  Controls: click the video to start (mic + camera). Hold SPACE = fake breath (no mic). 0 = let the air out.
  Credits: ml5.js FaceMesh (docs.ml5js.org), The Coding Train FaceMesh + Sound videos,
  p5.sound reference (p5.AudioIn, p5.FFT, p5.Oscillator, p5.Noise, p5.BandPass, p5.Envelope),
  MediaPipe face landmark map, Allison Parrish "Working with video".
*/
const LITE = true;
const W = LITE ? 320 : 480;
const H = LITE ? 240 : 360;
const K = W / 480;
const PINK = [242, 170, 189];
const CHEEK_POINTS = [[50, 123, 147, 187], [280, 352, 376, 411]];
const FACE_EDGES = [234, 454];
const FOLLOW = 0.45;
const LOST_AFTER = 800;
const FILL_SECONDS = 4;      // a 4-second breath out fills the cheeks
const EMPTY_SECONDS = 2.5;   // they empty in 2.5 s when you stop

let cam, faceMesh, faces = [], lastFaceTime = -Infinity, faceWidth = 0;
let cheeks = [], src;
let mic, fft, started = false;
let air = 0, wasBreathing = false, breathStart = 0, longest = 0, fulls = 0, wasFull = false;
let fakeBreath = false;
let strengthSlider, sizeSlider, levelSlider, ratioSlider, trackCheckbox, soundCheckbox, info;
let chime, noise, band, env;

// ---------- one cheek ----------
class Cheek {
  constructor(x, y) { this.x = x; this.y = y; this.puff = 0; this.vel = 0; }
  get r() {
    const base = faceWidth > 0 ? faceWidth * sizeSlider.value() : 60 * K;
    return base * (1 + 0.25 * max(0, this.puff));
  }
  follow(tx, ty) { this.x = lerp(this.x, tx, FOLLOW); this.y = lerp(this.y, ty, FOLLOW); }
  isResting() { return air < 0.005 && abs(this.puff) < 0.005 && abs(this.vel) < 0.005; }
  update() {
    const target = air * strengthSlider.value();
    this.vel += (target - this.puff) * 0.12;
    this.vel *= 0.84;
    this.puff += this.vel;
  }
  bend() {
    if (this.isResting()) return;
    const R = this.r, R2 = R * R;
    const power = 1 + max(-0.4, this.puff);
    const blush = air * 0.55;
    const cx = this.x, cy = this.y;
    const x0 = max(0, floor(cx - R)), x1 = min(W - 1, ceil(cx + R));
    const y0 = max(0, floor(cy - R)), y1 = min(H - 1, ceil(cy + R));
    const [pr, pg, pb] = PINK;
    for (let y = y0; y <= y1; y++) {
      const dy = y - cy;
      for (let x = x0; x <= x1; x++) {
        const dx = x - cx, d2 = dx * dx + dy * dy;
        if (d2 >= R2 || d2 === 0) continue;
        const t = Math.sqrt(d2) / R;
        const k = Math.pow(t, power - 1);
        let sx = Math.round(cx + dx * k), sy = Math.round(cy + dy * k);
        sx = sx < 0 ? 0 : sx > W - 1 ? W - 1 : sx;
        sy = sy < 0 ? 0 : sy > H - 1 ? H - 1 : sy;
        const from = (sy * W + sx) * 4, to = (y * W + x) * 4;
        const w = blush * (1 - t) * (1 - t);
        pixels[to] = src[from] + (pr - src[from]) * w;
        pixels[to + 1] = src[from + 1] + (pg - src[from + 1]) * w;
        pixels[to + 2] = src[from + 2] + (pb - src[from + 2]) * w;
      }
    }
  }
  showGuide() {
    noFill(); stroke(255, 255, 255, 200); strokeWeight(2);
    drawingContext.setLineDash([6, 6]); circle(this.x, this.y, this.r * 2); drawingContext.setLineDash([]);
  }
}

// ---------- FaceMesh ----------
function preload() { faceMesh = ml5.faceMesh({ maxFaces: 1, refineLandmarks: false, flipped: false }); }
function gotFaces(r) { faces = r; if (faces.length > 0) lastFaceTime = millis(); }
function toCanvas(kp) { return { x: W - kp.x * (W / cam.width), y: kp.y * (H / cam.height) }; }
function averagePoint(kp, ids) {
  let x = 0, y = 0;
  for (const i of ids) { const p = toCanvas(kp[i]); x += p.x; y += p.y; }
  return { x: x / ids.length, y: y / ids.length };
}
function trackCheeks() {
  if (faces.length === 0) return;
  const kp = faces[0].keypoints;
  if (!kp || kp.length < 468) return;
  const a = toCanvas(kp[FACE_EDGES[0]]), b = toCanvas(kp[FACE_EDGES[1]]);
  const w = dist(a.x, a.y, b.x, b.y);
  faceWidth = faceWidth === 0 ? w : lerp(faceWidth, w, FOLLOW);
  for (let i = 0; i < cheeks.length; i++) { const p = averagePoint(kp, CHEEK_POINTS[i]); cheeks[i].follow(p.x, p.y); }
}

// ---------- setup ----------
function setup() {
  createCanvas(W, H);
  pixelDensity(1);
  cam = createCapture(VIDEO);
  cam.size(W, H);
  cam.hide();
  faceMesh.detectStart(cam, gotFaces);

  mic = new p5.AudioIn();
  fft = new p5.FFT(0.8, 1024);
  fft.setInput(mic);
  // sounds: two sine notes for "full", band-passed white noise for "pff"
  chime = new p5.Oscillator("sine");
  chime.amp(0);
  noise = new p5.Noise("white");
  band = new p5.BandPass();
  band.freq(4000); band.res(2);
  noise.disconnect(); noise.connect(band);
  noise.amp(0);
  env = new p5.Envelope(0.02, 0.25, 0.4, 0);

  const panel = createDiv().id("panel");
  createSpan("Puff strength").parent(panel);
  strengthSlider = createSlider(0.3, 2.5, 1.4, 0.05).parent(panel);
  createSpan("Cheek size").parent(panel);
  sizeSlider = createSlider(0.1, 0.35, 0.2, 0.01).parent(panel);
  createSpan("Breath: loud enough").parent(panel);
  levelSlider = createSlider(0.005, 0.2, 0.03, 0.005).parent(panel);
  createSpan("Breath: LOW / VOICE >").parent(panel);
  ratioSlider = createSlider(0.8, 3, 1.3, 0.05).parent(panel);
  soundCheckbox = createCheckbox(" sound (turn off around other people)", true).parent(panel).class("wide");
  trackCheckbox = createCheckbox(" show tracking", false).parent(panel).class("wide");
  info = createP("").parent(panel).class("wide");

  cheeks.push(new Cheek(W * 0.65, H * 0.62));
  cheeks.push(new Cheek(W * 0.35, H * 0.62));
}

function mousePressed() {
  const onCanvas = mouseX >= 0 && mouseX <= W && mouseY >= 0 && mouseY <= H;
  if (!onCanvas || started) return;
  userStartAudio();
  mic.start(() => {
    const track = mic.stream && mic.stream.getAudioTracks()[0];   // keep the breath noise (Chrome removes it by default)
    if (track) track.applyConstraints({ noiseSuppression: false, autoGainControl: false, echoCancellation: false }).catch(() => {});
  });
  chime.start();
  noise.start();
  started = true;
}

// ---------- breath ----------
function isBreathing() {
  if (fakeBreath) return true;
  if (!started) return false;
  fft.analyze();
  const low = fft.getEnergy(20, 250), voice = fft.getEnergy(300, 3000);
  return mic.getLevel() > levelSlider.value() && low / max(voice, 1) > ratioSlider.value();
}

function updateBreath() {
  const dt = deltaTime / 1000;
  const breathing = isBreathing();
  if (breathing && !wasBreathing) breathStart = millis();
  if (breathing) {
    air = min(1, air + dt / FILL_SECONDS);
    longest = max(longest, (millis() - breathStart) / 1000);
  } else {
    if (wasBreathing && air > 0.25) pff(air);       // stopped: let the air out
    air = max(0, air - dt / EMPTY_SECONDS);
  }
  if (air >= 1 && !wasFull) { fulls++; ding(); }
  wasFull = air >= 1;
  wasBreathing = breathing;
}

function ding() {
  if (!soundCheckbox.checked() || !started) return;
  chime.freq(660); chime.amp(0.15, 0.03); chime.amp(0, 0.3, 0.12);
  setTimeout(() => { chime.freq(990); chime.amp(0.12, 0.03); chime.amp(0, 0.4, 0.12); }, 140);
}

function pff(amount) {
  if (!soundCheckbox.checked() || !started) return;
  env.setADSR(0.02, EMPTY_SECONDS * amount * 0.6, 0, 0.1);
  env.setRange(0.25 * amount, 0);
  env.play(noise);
}

// ---------- draw ----------
function draw() {
  push(); translate(W, 0); scale(-1, 1); image(cam, 0, 0, W, H); pop();
  trackCheeks();
  updateBreath();
  for (const c of cheeks) c.update();
  if (!cheeks.every((c) => c.isResting())) {
    loadPixels();
    src = pixels.slice();
    for (const c of cheeks) c.bend();
    updatePixels();
  }
  const lost = millis() - lastFaceTime > LOST_AFTER;
  if (trackCheckbox.checked() || lost) for (const c of cheeks) c.showGuide();

  // the breath meter on the left edge
  noStroke();
  fill(255, 255, 255, 120); rect(10 * K, 50 * K, 14 * K, H - 80 * K, 7 * K);
  fill(PINK[0], PINK[1], PINK[2]);
  const mh = (H - 80 * K) * air;
  rect(10 * K, 50 * K + (H - 80 * K) - mh, 14 * K, mh, 7 * K);

  fill(255); textSize(16 * K); textAlign(LEFT);
  if (!started) text("click to start, then breathe out slowly", 16 * K, 28 * K);
  else text(wasBreathing ? "filling…" : "breathe out slowly toward the mic", 16 * K, 28 * K);
  if (lost) { textAlign(CENTER); text("looking for your face…", W / 2, H - 16 * K); textAlign(LEFT); }
  info.html(`Full cheeks: ${fulls} · longest breath ${longest.toFixed(1)} s`);
}

function keyPressed() {
  if (key === " ") { fakeBreath = true; return false; }
  if (key === "0") air = 0;
}
function keyReleased() { if (key === " ") { fakeBreath = false; return false; } }
