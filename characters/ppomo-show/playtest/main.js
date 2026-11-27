/*
  Ppomo Playtest (PComp, Nov 24) — a small version of the Winter Show piece

  Stand in front of the camera and squeeze the soft Ppomo:
    first squeeze      -> a Ppomo drops onto your head and stays there as you move
    while you squeeze  -> it squishes (harder = more)
    every squeeze      -> it puffs up a little more: cheeks, then belly, then butt
    stop squeezing     -> the air slowly leaks out, so you squeeze again
    fully puffed       -> hearts, then it lets the air out and you can fill it again
    walk away / stop   -> it floats away and the screen waits for the next person
  The squeeze is measured as an AMOUNT (pressure above resting x time), not a count.
  Every squeeze is logged with date, time, amount and peak pressure (S saves a CSV).

  Light on purpose, for an old laptop: the 3D Ppomo is pre-rendered into 24 pictures (sprites/),
  the camera runs at 640x480, and face detection (MediaPipe Face Detector) runs about 10 times a second.

  Run with VS Code Live Server (Web Serial and the camera do not work from a file:// address). Use Chrome.
  Arduino: ppomo_squeeze_amount (sends one number per line, hPa above resting, 50 per second).
  Sound comes from the computer (sound.js, made in the browser). Browsers only allow it after one click or key
  press on the page, so click the screen once after opening it.
  Keys (for me): C connect sensor  S save CSV  D debug  F fullscreen  R reset  M sound on/off  [ ] volume
                 hold SPACE = fake squeeze
  Written with help from Claude.
*/
import { FilesetResolver, FaceDetector } from 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/vision_bundle.mjs';
import { createSound } from './sound.js';

// ---------- settings to tune ----------
const RESTING = 1.0;        // hPa below which the squishy counts as untouched (same as the Arduino)
const PRESS_ON = 3.0;       // a squeeze starts above this (hPa)
const PRESS_OFF = 1.5;      // and ends below this
const AMOUNT_FULL = 60;     // hPa·s of squeezing to puff Ppomo all the way (lower = fills faster)
const LEAK_AFTER = 3000;    // ms without squeezing before air starts leaking out
const LEAK_PER_SEC = 0.06;  // how much puff leaks per second (1 = full)
const END_AFTER = 15000;    // ms without squeezing before Ppomo floats away
const NO_FACE_END = 8000;   // ms without a face before Ppomo floats away
const FRAMES = 24;          // sprites/puff-00.png ... puff-23.png
const SIZE_ON_HEAD = 1.6;   // Ppomo width compared to the face width
const DETECT_EVERY = 100;   // ms between face detections

// ---------- page ----------
const canvas = document.getElementById('view');
const ctx = canvas.getContext('2d');
const video = document.getElementById('cam');
const hint = document.getElementById('hint');
const connectBtn = document.getElementById('connect');
const soundNote = document.getElementById('sound');
const sound = createSound();
window.ppomoSound = sound;                     // for checking in the browser console
let lastStep = 0, leaking = false;              // for the sounds: last puff step heard, and whether air is leaking
const STEPS = 12;                              // one "blop" for every 1/12 of a full puff

const sprites = [];
for (let i = 0; i < FRAMES; i++) {
  const img = new Image();
  img.src = `sprites/puff-${String(i).padStart(2, '0')}.png`;
  sprites.push(img);
}

// ---------- state ----------
let delta = 0, maxSeen = 30, lastSample = 0;
let fakeOn = false, fake = 0;
let pressing = false, press = null;         // the squeeze in progress: { start, amount, peak }
let state = 'idle';                          // idle -> session -> leaving -> idle
let session = { start: 0, last: 0, squeezes: [] };
let puff = 0, shownPuff = 0;                 // 0..1, shownPuff follows puff smoothly
let fullUntil = 0;                           // celebrating until this time
let squish = 0;
let face = null, lastFaceAt = -1e9;          // face box in canvas pixels, smoothed
let pp = { x: 0, y: 0, w: 0, angle: 0, drop: 0, vy: 0, alpha: 1 };   // where Ppomo is drawn
let hearts = [], puffs = [];
let log = [];
let debug = false, fps = 0;
let detector = null, lastDetect = 0;

// ---------- camera + face detector ----------
async function startCamera() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480, facingMode: 'user' }, audio: false });
    video.srcObject = stream;
    await video.play();
  } catch (e) {
    console.log('camera error', e);
  }
}

async function startDetector() {
  const files = await FilesetResolver.forVisionTasks('https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm');
  const options = (delegate) => ({
    baseOptions: {
      modelAssetPath: 'https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite',
      delegate,
    },
    runningMode: 'VIDEO',
    minDetectionConfidence: 0.5,
  });
  try { detector = await FaceDetector.createFromOptions(files, options('GPU')); }
  catch (e) { detector = await FaceDetector.createFromOptions(files, options('CPU')); }   // old laptops
}

// the video is drawn mirrored and fitted inside the screen (nothing cut off); this maps a video pixel to the canvas
function videoToCanvas(x, y) {
  const vw = video.videoWidth, vh = video.videoHeight;
  const k = Math.min(canvas.width / vw, canvas.height / vh);
  const ox = (canvas.width - vw * k) / 2, oy = (canvas.height - vh * k) / 2;
  return { x: canvas.width - (ox + x * k), y: oy + y * k, k };
}

function detectFace(now) {
  if (!detector || video.readyState < 2 || now - lastDetect < DETECT_EVERY) return;
  lastDetect = now;
  let res;
  try { res = detector.detectForVideo(video, now); } catch (e) { return; }
  const d = res.detections && res.detections[0];
  if (!d) return;
  const b = d.boundingBox;
  const a = videoToCanvas(b.originX, b.originY), c = videoToCanvas(b.originX + b.width, b.originY + b.height);
  // head roll from the two eyes (keypoints are 0..1 of the video size)
  let angle = 0;
  if (d.keypoints && d.keypoints.length >= 2) {
    const e1 = videoToCanvas(d.keypoints[0].x * video.videoWidth, d.keypoints[0].y * video.videoHeight);
    const e2 = videoToCanvas(d.keypoints[1].x * video.videoWidth, d.keypoints[1].y * video.videoHeight);
    angle = Math.atan2(e2.y - e1.y, e2.x - e1.x);
    if (angle > Math.PI / 2) angle -= Math.PI; else if (angle < -Math.PI / 2) angle += Math.PI;
  }
  const box = { x: Math.min(a.x, c.x), y: a.y, w: Math.abs(c.x - a.x), h: c.y - a.y, angle };
  face = face ? {
    x: lerp(face.x, box.x, 0.5), y: lerp(face.y, box.y, 0.5), w: lerp(face.w, box.w, 0.5),
    h: lerp(face.h, box.h, 0.5), angle: lerp(face.angle, box.angle, 0.4),
  } : box;
  lastFaceAt = now;
}

// ---------- sensor: Web Serial, one number per line ----------
async function connectSensor(port) {
  try {
    port = port || await navigator.serial.requestPort();
    await port.open({ baudRate: 9600 });
    connectBtn.hidden = true;
    const reader = port.readable.pipeThrough(new TextDecoderStream()).getReader();
    let buf = '';
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += value;
      let i;
      while ((i = buf.indexOf('\n')) >= 0) {
        const v = Number(buf.slice(0, i).trim());
        buf = buf.slice(i + 1);
        if (!Number.isNaN(v) && !fakeOn && fake === 0) sample(v);
      }
    }
  } catch (e) {
    console.log('serial', e);
    connectBtn.hidden = false;
  }
}

if ('serial' in navigator) {
  navigator.serial.getPorts().then((ports) => { if (ports[0]) connectSensor(ports[0]); });   // a port Chrome already allowed
  navigator.serial.addEventListener('connect', (e) => connectSensor(e.target));
} else {
  connectBtn.textContent = 'Use Chrome for the sensor';
}
connectBtn.addEventListener('click', () => connectSensor());
addEventListener('pointerdown', () => sound.unlock());   // any click on the page turns sound on

// one pressure reading (hPa above resting)
function sample(v) {
  const now = performance.now();
  const dt = lastSample ? Math.min((now - lastSample) / 1000, 0.1) : 0.02;
  lastSample = now;
  delta = v;
  maxSeen = Math.max(maxSeen, v);

  if (!pressing && v > PRESS_ON) {
    pressing = true;
    press = { start: now, amount: 0, peak: 0 };
    if (state !== 'session') startSession(now);
    sound.squish(Math.min(1, v / 20));
    leaking = false;
  }
  if (pressing) {
    const add = Math.max(0, v - RESTING) * dt;
    press.amount += add;
    press.peak = Math.max(press.peak, v);
    if (now > fullUntil) puff = Math.min(1, puff + add / AMOUNT_FULL);
    const step = Math.floor(puff * STEPS);
    if (step > lastStep && now > fullUntil) sound.bubble(puff);
    lastStep = step;
    session.last = now;
    if (puff >= 1 && now > fullUntil) celebrate(now);
    if (v < PRESS_OFF) endPress(now);
  }
}

function endPress(now) {
  pressing = false;
  if (press && press.amount > 0.05) {
    session.squeezes.push({ t: press.start - session.start, amount: press.amount });
    addLog(press);
    sound.release(Math.min(1, press.amount / (AMOUNT_FULL * 0.3)));
    for (let i = 0; i < 3; i++) puffs.push({ x: pp.x + rand(-0.3, 0.3) * pp.w, y: pp.y - pp.w * 0.35, r: 4, a: 0.8 });
  }
  press = null;
}

// ---------- session ----------
function startSession(now) {
  state = 'session';
  session = { start: now, last: now, squeezes: [] };
  puff = 0; shownPuff = 0; lastStep = 0;
  pp.drop = -1; pp.vy = 0; pp.alpha = 1;           // drops in from above
}

function celebrate(now) {
  fullUntil = now + 3000;
  sound.full();
  for (let i = 0; i < 18; i++) hearts.push({ x: pp.x + rand(-0.5, 0.5) * pp.w, y: pp.y - pp.w * 0.4, vx: rand(-1.5, 1.5), vy: rand(-4, -1.5), a: 1 });
  setTimeout(() => { puff = 0; lastStep = 0; sound.deflate(1.4); }, 3000);   // then it lets all the air out and you can fill it again
}

function update(now, dt) {
  if (fakeOn || fake > 0) {                       // SPACE pretends to squeeze
    fake = fakeOn ? Math.min(fake + 120 * dt, 40) : Math.max(fake - 300 * dt, 0);
    sample(fake);
  } else if (now - lastSample > 200) {
    sample(0);                                    // no sensor data: resting
  }

  if (state === 'session') {
    const quiet = now - session.last;
    if (!pressing && quiet > LEAK_AFTER && now > fullUntil && puff > 0) {
      if (!leaking) { sound.leak(); leaking = true; }
      puff = Math.max(0, puff - LEAK_PER_SEC * dt);
      lastStep = Math.floor(puff * STEPS);
    }
    const faceGone = now - lastFaceAt > NO_FACE_END && lastFaceAt > session.start;
    if (!pressing && (quiet > END_AFTER || faceGone)) { state = 'leaving'; pp.vy = -1; sound.leave(); }
  } else if (state === 'leaving') {
    pp.alpha -= 0.6 * dt;
    if (pp.alpha <= 0) { state = 'idle'; puff = 0; }
  }

  shownPuff += (puff - shownPuff) * Math.min(1, dt * 6);
  squish += ((pressing ? Math.min(1, delta / (maxSeen * 0.8)) : 0) - squish) * Math.min(1, dt * 14);

  // where Ppomo sits: on the head if a face was seen recently, otherwise in the middle of the screen
  const haveFace = face && now - lastFaceAt < 1500;
  const target = haveFace
    ? { x: face.x + face.w / 2, y: face.y - face.h * 0.28, w: face.w * SIZE_ON_HEAD, angle: face.angle }
    : { x: canvas.width / 2, y: canvas.height * 0.62, w: Math.min(canvas.width, canvas.height) * 0.42, angle: 0 };
  // not enough room above the head (the person is close to the top of the picture):
  // first make Ppomo smaller (down to 70% of the face width), and only then let it sit lower
  const RATIO = 0.72 * 1.25;                       // sprite height / width, with room for puffing
  if (haveFace) target.w = Math.max(face.w * 0.7, Math.min(target.w, (target.y - 10) / RATIO));
  target.y = Math.max(target.y, target.w * RATIO + 10);
  const k = pp.w === 0 ? 1 : Math.min(1, dt * 10);
  pp.x = lerp(pp.x, target.x, k); pp.y = lerp(pp.y, target.y, k);
  pp.w = lerp(pp.w, target.w, k); pp.angle = lerp(pp.angle, target.angle, k);
  // the drop: falls from above with a small bounce
  if (state === 'session' && pp.drop < 0) { pp.vy += 6 * dt; pp.drop = Math.min(0, pp.drop + pp.vy * dt); if (pp.drop === 0) { pp.vy = 0; squish = 0.8; sound.land(); } }
  if (state === 'leaving') pp.drop -= 0.6 * dt;
}

// ---------- drawing ----------
function draw(now) {
  const W = canvas.width, H = canvas.height;
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.fillStyle = '#2b2833';
  ctx.fillRect(0, 0, W, H);
  if (video.readyState >= 2) {                     // the camera, mirrored, fitted inside the screen
    const vw = video.videoWidth, vh = video.videoHeight, k = Math.min(W / vw, H / vh);
    ctx.save();
    ctx.translate(W, 0); ctx.scale(-1, 1);
    ctx.drawImage(video, (W - vw * k) / 2, (H - vh * k) / 2, vw * k, vh * k);
    ctx.restore();
  }
  if (state !== 'idle') drawPpomo(now);
  drawParticles();
  if (state === 'session') drawTimeline(now);
  if (debug) drawDebug(now);

  const haveFace = face && now - lastFaceAt < 1500;
  hint.innerHTML = state === 'idle'
    ? (haveFace ? 'Squeeze Ppomo<small>whenever you feel FOMO</small>' : 'Step in front of the camera<small>and squeeze Ppomo</small>')
    : '';
  // a quiet note for whoever sets up the screen: sound needs one click first
  const msg = !sound.running() ? 'Click once to turn on sound' : sound.muted ? 'Sound off (M)' : '';
  if (soundNote.textContent !== msg) soundNote.textContent = msg;
}

function drawPpomo(now) {
  const img = sprites[Math.round(shownPuff * (FRAMES - 1))];
  if (!img.complete || !img.naturalWidth) return;
  const w = pp.w, h = w * img.naturalHeight / img.naturalWidth;
  const happy = now < fullUntil ? Math.sin(now / 90) * 0.05 : 0;
  const sx = 1 + 0.16 * squish + happy, sy = 1 - 0.2 * squish - happy;
  ctx.save();
  ctx.globalAlpha = Math.max(0, pp.alpha);
  ctx.translate(pp.x, pp.y + pp.drop * canvas.height);
  ctx.rotate(pp.angle);
  ctx.scale(sx, sy);
  ctx.drawImage(img, -w / 2, -h, w, h);            // anchored at the bottom middle (where it touches the head)
  ctx.restore();
}

function drawParticles() {
  ctx.textAlign = 'center';
  for (const p of hearts) {
    p.x += p.vx; p.y += p.vy; p.vy += 0.05; p.a -= 0.012;
    ctx.globalAlpha = Math.max(0, p.a);
    ctx.fillStyle = '#F29AB2';
    ctx.font = `${Math.round(pp.w * 0.12)}px system-ui`;
    ctx.fillText('♥', p.x, p.y);
  }
  for (const p of puffs) {                           // little air puffs when you let go
    p.y -= 0.8; p.r += 0.6; p.a -= 0.025;
    ctx.globalAlpha = Math.max(0, p.a);
    ctx.fillStyle = '#ffffff';
    ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2); ctx.fill();
  }
  ctx.globalAlpha = 1;
  hearts = hearts.filter((p) => p.a > 0);
  puffs = puffs.filter((p) => p.a > 0);
}

// the record, shown quietly at the bottom: when you squeezed and how much (this session)
function drawTimeline(now) {
  const W = canvas.width, H = canvas.height;
  const x0 = W * 0.2, x1 = W * 0.8, y = H - 28, hMax = 46;
  const span = Math.max(30000, now - session.start);
  ctx.fillStyle = 'rgba(30,28,36,0.45)';
  roundRect(x0 - 14, y - hMax - 30, x1 - x0 + 28, hMax + 44, 12); ctx.fill();
  ctx.strokeStyle = 'rgba(255,255,255,0.5)'; ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(x0, y); ctx.lineTo(x1, y); ctx.stroke();
  const all = session.squeezes.concat(pressing && press ? [{ t: press.start - session.start, amount: press.amount }] : []);
  const maxA = Math.max(10, ...all.map((s) => s.amount));
  ctx.fillStyle = '#F7B5C6';
  for (const s of all) {
    const h = Math.max(3, (s.amount / maxA) * hMax);
    ctx.fillRect(x0 + (s.t / span) * (x1 - x0) - 2, y - h, 4, h);
  }
  ctx.fillStyle = '#fff'; ctx.font = '13px system-ui'; ctx.textAlign = 'left';
  ctx.fillText(`your squeezes · ${mmss(now - session.start)}`, x0, y - hMax - 12);
}

function drawDebug(now) {
  ctx.fillStyle = 'rgba(0,0,0,0.6)'; ctx.fillRect(10, 10, 330, 92);
  ctx.fillStyle = '#fff'; ctx.font = '13px monospace'; ctx.textAlign = 'left';
  ctx.fillText(`fps ${fps.toFixed(0)}  detector ${detector ? 'on' : 'loading'}`, 20, 30);
  ctx.fillText(`delta ${delta.toFixed(1)} hPa  ${pressing ? 'PRESSING' : 'resting'}`, 20, 50);
  ctx.fillText(`puff ${(puff * 100).toFixed(0)}%  state ${state}`, 20, 70);
  ctx.fillText(`face ${face && now - lastFaceAt < 1500 ? 'yes' : 'no'}  log ${log.length}`, 20, 90);
  if (face && now - lastFaceAt < 1500) {
    ctx.strokeStyle = '#7fd'; ctx.strokeRect(face.x, face.y, face.w, face.h);
  }
}

// ---------- log ----------
function addLog(p) {
  const d = new Date(), two = (v) => String(v).padStart(2, '0');
  log.push({
    date: `${d.getFullYear()}-${two(d.getMonth() + 1)}-${two(d.getDate())}`,
    time: `${two(d.getHours())}:${two(d.getMinutes())}:${two(d.getSeconds())}`,
    amount: p.amount.toFixed(2), peak: p.peak.toFixed(1),
  });
}

function saveCsv() {
  const rows = ['date,time,amount_hPa_s,peak_hPa', ...log.map((e) => `${e.date},${e.time},${e.amount},${e.peak}`)];
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([rows.join('\n')], { type: 'text/csv' }));
  a.download = 'ppomo-playtest.csv';
  a.click();
}

// ---------- keys ----------
addEventListener('keydown', (e) => {
  sound.unlock();
  if (e.code === 'Space') { fakeOn = true; e.preventDefault(); return; }
  const k = e.key.toLowerCase();
  if (k === 'c') connectSensor();
  if (k === 's') saveCsv();
  if (k === 'd') debug = !debug;
  if (k === 'm') sound.setMuted(!sound.muted);
  if (k === '[') sound.setVolume(sound.volume - 0.1);
  if (k === ']') sound.setVolume(sound.volume + 0.1);
  if (k === 'f') { if (document.fullscreenElement) document.exitFullscreen(); else document.documentElement.requestFullscreen(); }
  if (k === 'r') { state = 'idle'; puff = 0; pressing = false; press = null; }
});
addEventListener('keyup', (e) => { if (e.code === 'Space') { fakeOn = false; e.preventDefault(); } });

// ---------- helpers ----------
function lerp(a, b, t) { return a + (b - a) * t; }
function rand(a, b) { return a + Math.random() * (b - a); }
function mmss(ms) { const s = Math.round(ms / 1000); return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`; }
function roundRect(x, y, w, h, r) {
  ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath();
}

// the canvas works at most 1280 px wide and the browser scales it up (lighter on an old laptop)
function resize() {
  const k = Math.min(1, 1280 / innerWidth);
  canvas.width = Math.round(innerWidth * k);
  canvas.height = Math.round(innerHeight * k);
}
addEventListener('resize', resize);
resize();

// ---------- loop ----------
let last = performance.now();
function loop(now) {
  const dt = Math.min(0.05, (now - last) / 1000);
  last = now;
  fps = lerp(fps, 1 / Math.max(dt, 0.001), 0.05);
  detectFace(now);
  update(now, dt);
  draw(now);
  requestAnimationFrame(loop);
}
startCamera();
startDetector().catch((e) => console.log('face detector failed to load', e));
requestAnimationFrame(loop);
