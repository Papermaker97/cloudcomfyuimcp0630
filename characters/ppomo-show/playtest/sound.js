/*
  Ppomo sounds, made in the browser with Web Audio (no sound files, nothing to download).

    squish(s)     the moment you start squeezing: a soft wet squelch (s = 0..1, how hard)
    bubble(p)     while you keep squeezing, a little "blop" each time Ppomo puffs up a step; it climbs a
                  pentatonic scale as Ppomo fills (p = 0..1)
    release(a)    letting go: a low "bloop", deeper after a bigger squeeze (a = 0..1)
    land()        Ppomo landing on your head: a soft thump
    full()        fully puffed: a short sparkly chime
    deflate(sec)  after the chime, the air goes out: a falling "pffff" and whistle
    leak()        air starts leaking because nobody squeezes: a tiny hiss
    leave()       Ppomo floats away: three soft falling notes

  Browsers only allow sound after a click or key press on the page, so call unlock() from one.
  Written with help from Claude.
*/
const SCALE = [523.3, 587.3, 659.3, 784.0, 880.0, 1046.5, 1174.7, 1318.5, 1568.0, 1760.0, 2093.0, 2349.3];

export function createSound() {
  let ctx = null, master = null, noise = null;
  let muted = false, volume = 0.8;
  const log = [];

  function setup() {
    if (ctx) return;
    ctx = new (window.AudioContext || window.webkitAudioContext)();
    const comp = ctx.createDynamicsCompressor();          // keeps loud moments from clipping
    master = ctx.createGain();
    master.gain.value = muted ? 0 : volume;
    master.connect(comp).connect(ctx.destination);
    noise = ctx.createBuffer(1, ctx.sampleRate, ctx.sampleRate);   // one second of white noise, reused
    const d = noise.getChannelData(0);
    for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
  }

  function unlock() {
    try { setup(); if (ctx.state === 'suspended') ctx.resume(); } catch (e) { /* no audio on this machine */ }
  }

  const running = () => !!ctx && ctx.state === 'running';

  // ---- building blocks ----
  function env(g, t, peak, attack, decay) {
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(peak, t + attack);
    g.gain.exponentialRampToValueAtTime(0.0001, t + attack + decay);
  }

  function tone({ type = 'sine', f0, f1 = f0, glide = 0.1, peak = 0.2, attack = 0.005, decay = 0.2, delay = 0 }) {
    const t = ctx.currentTime + delay;
    const o = ctx.createOscillator(), g = ctx.createGain();
    o.type = type;
    o.frequency.setValueAtTime(f0, t);
    o.frequency.exponentialRampToValueAtTime(Math.max(20, f1), t + glide);
    env(g, t, peak, attack, decay);
    o.connect(g).connect(master);
    o.start(t); o.stop(t + attack + decay + 0.05);
  }

  function hiss({ filter = 'bandpass', f0, f1 = f0, q = 1, peak = 0.2, attack = 0.01, decay = 0.2, delay = 0 }) {
    const t = ctx.currentTime + delay;
    const s = ctx.createBufferSource(), bf = ctx.createBiquadFilter(), g = ctx.createGain();
    s.buffer = noise; s.loop = true;
    bf.type = filter; bf.Q.value = q;
    bf.frequency.setValueAtTime(f0, t);
    bf.frequency.exponentialRampToValueAtTime(Math.max(20, f1), t + attack + decay);
    env(g, t, peak, attack, decay);
    s.connect(bf).connect(g).connect(master);
    s.start(t, Math.random() * 0.5); s.stop(t + attack + decay + 0.05);
  }

  function play(name, fn) {
    log.push(name);
    if (log.length > 50) log.shift();
    if (!running() || muted) return;
    try { fn(); } catch (e) { /* ignore a bad note rather than stop the page */ }
  }

  // ---- the sounds ----
  const squish = (s = 0.6) => play('squish', () => {
    hiss({ f0: 900, f1: 260, q: 2.5, peak: 0.18 + 0.22 * s, attack: 0.01, decay: 0.16 });
    tone({ f0: 240, f1: 110, glide: 0.12, peak: 0.12 + 0.12 * s, decay: 0.14 });
  });

  const bubble = (p = 0) => play('bubble', () => {
    const f = SCALE[Math.min(SCALE.length - 1, Math.floor(p * SCALE.length))];
    tone({ f0: f * 0.7, f1: f * 1.15, glide: 0.06, peak: 0.16, attack: 0.004, decay: 0.13 });
  });

  const release = (a = 0.5) => play('release', () => {
    const f = 300 - 150 * Math.min(1, a);
    tone({ f0: f, f1: f * 0.55, glide: 0.2, peak: 0.22 + 0.1 * a, decay: 0.22 });
    hiss({ filter: 'lowpass', f0: 1400, f1: 400, peak: 0.07, decay: 0.16 });
  });

  const land = () => play('land', () => {
    tone({ f0: 150, f1: 60, glide: 0.14, peak: 0.35, decay: 0.16 });
    hiss({ filter: 'lowpass', f0: 600, f1: 200, peak: 0.1, decay: 0.08 });
  });

  const full = () => play('full', () => {
    [523.3, 659.3, 784.0, 1046.5].forEach((f, i) => tone({ type: 'triangle', f0: f, peak: 0.18, decay: 0.4, delay: i * 0.09 }));
    for (let i = 0; i < 6; i++) tone({ f0: 2000 + Math.random() * 1600, peak: 0.05, decay: 0.12, delay: 0.35 + i * 0.07 });
  });

  const deflate = (sec = 1.4) => play('deflate', () => {
    hiss({ filter: 'lowpass', f0: 3200, f1: 250, q: 0.7, peak: 0.22, attack: 0.05, decay: sec });
    tone({ f0: 900, f1: 220, glide: sec, peak: 0.06, attack: 0.05, decay: sec });
  });

  const leak = () => play('leak', () => {
    hiss({ f0: 2500, f1: 1500, q: 0.8, peak: 0.06, attack: 0.05, decay: 0.5 });
  });

  const leave = () => play('leave', () => {
    [784.0, 659.3, 523.3].forEach((f, i) => tone({ f0: f, peak: 0.12, decay: 0.35, delay: i * 0.16 }));
  });

  function setMuted(m) { muted = m; if (master) master.gain.value = muted ? 0 : volume; }
  function setVolume(v) { volume = Math.max(0, Math.min(1, v)); if (master && !muted) master.gain.value = volume; }

  return {
    unlock, running, squish, bubble, release, land, full, deflate, leak, leave,
    setMuted, setVolume, get muted() { return muted; }, get volume() { return volume; }, log,
  };
}
