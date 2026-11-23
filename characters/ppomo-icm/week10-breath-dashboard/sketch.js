/*
  Breath or Voice? A mic dashboard (ICM Week 10, step 1)

  Question: can the laptop mic tell a long breath OUT (blowing toward the mic) apart from talking?
  If it can, Ppomo's cheeks can puff with your breath instead of a click (step 2).

  What it shows
    - Mic level (p5.Amplitude through p5.AudioIn.getLevel) and its last few seconds
    - The spectrum (p5.FFT), with two bands marked:
        LOW   20-250 Hz      blowing on a mic makes a rumbly "wind" noise that sits here
        VOICE 300-3000 Hz    talking has most of its energy here
    - The decision: QUIET / VOICE / BREATH, and how long the current breath has lasted
  Sliders change the thresholds live, so I can tune them for this room and this laptop.

  Click the canvas to start the mic (browsers block audio until you click).
  Credits: p5.sound reference (p5.AudioIn, p5.FFT, getEnergy, userStartAudio);
  The Coding Train, Sound videos (Mic Input, Amplitude Analysis, Sound Viz); Getting Started with p5.js ch.13.
*/
const W = 640, H = 420;
let mic, fft;
let started = false;
let levelHist = [];
let levelSlider, ratioSlider, smoothSlider;
let state = "QUIET", breathStart = 0, longest = 0;

function setup() {
  createCanvas(W, H);
  mic = new p5.AudioIn();
  fft = new p5.FFT(0.8, 1024);
  fft.setInput(mic);

  const panel = createDiv().id("panel").parent(select("main"));
  levelSlider = addSlider(panel, "Loud enough (level)", 0.005, 0.2, 0.03, 0.005);
  ratioSlider = addSlider(panel, "Breath if LOW / VOICE >", 0.8, 3, 1.3, 0.05);
  smoothSlider = addSlider(panel, "FFT smoothing", 0, 0.99, 0.8, 0.01);
}

function addSlider(parent, label, a, b, v, step) {
  createSpan(label).parent(parent);
  const s = createSlider(a, b, v, step).parent(parent);
  const out = createSpan(v).parent(parent);
  s.input(() => out.html(s.value()));
  return s;
}

function mousePressed() {
  if (started || mouseX < 0 || mouseX > W || mouseY < 0 || mouseY > H) return;
  userStartAudio();
  mic.start(() => {
    // Chrome cleans up the mic by default; noise suppression removes steady breath noise, so turn it off
    const track = mic.stream && mic.stream.getAudioTracks()[0];
    if (track) track.applyConstraints({ noiseSuppression: false, autoGainControl: false, echoCancellation: false }).catch(() => {});
  });
  started = true;
}

function draw() {
  background(255);
  if (!started) {
    fill(90, 52, 36); noStroke(); textAlign(CENTER, CENTER); textSize(22);
    text("Click to start the mic", W / 2, H / 2 - 12);
    textSize(14); fill(140, 110, 100);
    text("then try: talking, a long breath out toward the mic, silence", W / 2, H / 2 + 18);
    return;
  }
  fft.smooth(smoothSlider.value());
  const spectrum = fft.analyze();
  const level = mic.getLevel();
  const low = fft.getEnergy(20, 250);
  const voice = fft.getEnergy(300, 3000);
  const ratio = low / max(voice, 1);

  // decide
  let now = "QUIET";
  if (level > levelSlider.value()) now = ratio > ratioSlider.value() ? "BREATH" : "VOICE";
  if (now === "BREATH" && state !== "BREATH") breathStart = millis();
  state = now;
  const breathSec = state === "BREATH" ? (millis() - breathStart) / 1000 : 0;
  longest = max(longest, breathSec);

  drawSpectrum(spectrum, 20, 20, W - 40, 180);
  levelHist.push(level);
  if (levelHist.length > 200) levelHist.shift();
  drawLevel(20, 230, 380, 100, level);
  drawBands(420, 230, 200, 100, low, voice, ratio);
  drawDecision(20, 350, breathSec);
}

// spectrum on a log frequency axis (so the low band is not squeezed into a few pixels)
function drawSpectrum(sp, x, y, w, h) {
  const nyq = sampleRate() / 2;
  const fx = (f) => x + (Math.log10(f / 20) / Math.log10(nyq / 20)) * w;
  noStroke();
  fill(242, 170, 189, 60); rect(fx(20), y, fx(250) - fx(20), h);
  fill(150, 190, 230, 60); rect(fx(300), y, fx(3000) - fx(300), h);
  fill(236, 110, 140);
  for (let i = 1; i < sp.length; i++) {
    const f0 = (i * nyq) / sp.length, f1 = ((i + 1) * nyq) / sp.length;
    if (f0 < 20) continue;
    const bh = (sp[i] / 255) * h;
    rect(fx(f0), y + h - bh, max(1, fx(f1) - fx(f0)), bh);
  }
  fill(140, 110, 100); textSize(11); textAlign(CENTER, TOP);
  for (const f of [50, 100, 250, 500, 1000, 3000, 10000]) text(f >= 1000 ? f / 1000 + "k" : f, fx(f), y + h + 3);
  textAlign(LEFT, TOP); textSize(12);
  fill(200, 90, 120); text("LOW 20-250 Hz", fx(20) + 4, y + 4);
  fill(70, 120, 170); text("VOICE 300-3000 Hz", fx(300) + 4, y + 4);
}

function drawLevel(x, y, w, h, level) {
  fill(90, 52, 36); noStroke(); textSize(12); textAlign(LEFT, TOP);
  text(`level ${level.toFixed(3)}`, x, y - 16);
  fill(248, 243, 238); rect(x, y, w, h, 6);
  const ty = y + h - constrain(levelSlider.value() / 0.3, 0, 1) * h;
  stroke(90, 52, 36, 120); line(x, ty, x + w, ty);
  noFill(); stroke(236, 110, 140); strokeWeight(2);
  beginShape();
  levelHist.forEach((v, i) => vertex(x + (i / 199) * w, y + h - constrain(v / 0.3, 0, 1) * h));
  endShape();
  strokeWeight(1);
}

function drawBands(x, y, w, h, low, voice, ratio) {
  noStroke(); fill(90, 52, 36); textSize(12); textAlign(LEFT, TOP);
  text(`LOW / VOICE = ${ratio.toFixed(2)}`, x, y - 16);
  const bw = w / 2 - 10;
  fill(248, 243, 238); rect(x, y, w, h, 6);
  fill(236, 110, 140); rect(x + 5, y + h - (low / 255) * h, bw, (low / 255) * h);
  fill(110, 160, 210); rect(x + w / 2 + 5, y + h - (voice / 255) * h, bw, (voice / 255) * h);
  fill(255); textAlign(CENTER, BOTTOM);
  text(`LOW ${low | 0}`, x + 5 + bw / 2, y + h - 4);
  text(`VOICE ${voice | 0}`, x + w / 2 + 5 + bw / 2, y + h - 4);
}

function drawDecision(x, y, breathSec) {
  const c = { QUIET: color(170, 160, 150), VOICE: color(70, 120, 170), BREATH: color(220, 90, 120) }[state];
  fill(c); noStroke(); rect(x, y, 160, 48, 24);
  fill(255); textAlign(CENTER, CENTER); textSize(20); text(state, x + 80, y + 24);
  fill(90, 52, 36); textAlign(LEFT, CENTER); textSize(16);
  text(`this breath ${breathSec.toFixed(1)} s     longest ${longest.toFixed(1)} s`, x + 180, y + 24);
}
