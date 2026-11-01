// Bake the jelly Ppomo (ppomo-jelly-drop.html) into transparent sprite sheets for p5.js.
// Usage: node bake-jelly-sprites.mjs <three.js dir with build/ and examples/> <out dir>
// Each clip is one PNG grid (COLS columns, CELL px cells, 30 fps) + clips.json with the frame counts and anchor.
import { createRequire } from 'node:module';
const { chromium } = createRequire(import.meta.url)('playwright');
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';

const [threeDir, outDir] = process.argv.slice(2);
const here = path.dirname(new URL(import.meta.url).pathname);
const page = fs.readFileSync(path.join(here, 'ppomo-jelly-drop.html'), 'utf8');
const html = `<!doctype html><html><head><meta charset="utf-8"><style>body{margin:0}</style></head><body>${page}</body></html>`;
const server = http.createServer((q, r) => { r.writeHead(200, { 'content-type': 'text/html' }); r.end(html); }).listen(8777);

const CELL = 240, COLS = 8, FPS = 30;
const CLIPS = [
  { name: 'land',    from: 0, to: 0, seconds: 1.6, kind: 'land' },
  { name: 'puff1',   from: 0, to: 1, seconds: 1.4, kind: 'squeeze' },
  { name: 'puff2',   from: 1, to: 2, seconds: 1.4, kind: 'squeeze' },
  { name: 'puff3',   from: 2, to: 3, seconds: 1.4, kind: 'squeeze' },
  { name: 'deflate', from: 3, to: 0, seconds: 1.6, kind: 'squeeze' },
];

const browser = await chromium.launch();
const tab = await browser.newPage({ viewport: { width: 900, height: 700 } });
await tab.route('**/*', (r) => {
  const u = r.request().url();
  if (u.startsWith('http://localhost')) return r.continue();
  const m = u.match(/three@0\.160\.0\/(.*)$/);
  if (m) return r.fulfill({ body: fs.readFileSync(path.join(threeDir, m[1])), contentType: 'text/javascript' });
  return r.abort();
});
tab.on('pageerror', (e) => console.log('page error:', e.message));
await tab.goto('http://localhost:8777/?bake');
await tab.waitForFunction(() => document.body.dataset.bake === '1', null, { timeout: 120000 });

const meta = { cell: CELL, cols: COLS, fps: FPS, clips: {} };
for (const clip of CLIPS) {
  const res = await tab.evaluate(({ clip, CELL, COLS, FPS }) => {
    const J = window.ppomoJelly, { THREE, renderer, scene } = J;
    J.setFirmness(50); J.setDamping(35);
    renderer.setPixelRatio(1); renderer.setSize(CELL, CELL); renderer.setClearColor(0x000000, 0);
    const cam = new THREE.OrthographicCamera(-1.75, 1.75, 1.75, -1.75, 0.1, 40);
    cam.position.set(0, 1.25 + 10 * Math.tan(THREE.MathUtils.degToRad(10)), 10); cam.lookAt(0, 1.25, 0);
    cam.updateMatrixWorld();
    const setLevel = (lv) => { for (const k in J.REGIONS) J.REGIONS[k].target = lv / 3; };
    // keep Ppomo facing the camera and centred: remove yaw drift and sideways drift (p5 owns the position)
    const P = J.pos, R = J.rest, V = J.vel;
    const face = () => {
      let cx = 0, cz = 0, rx = 0, rz = 0; const n = P.length / 3;
      for (let i = 0; i < P.length; i += 3) { cx += P[i]; cz += P[i + 2]; rx += R[i]; rz += R[i + 2]; }
      cx /= n; cz /= n; rx /= n; rz /= n;
      let s = 0, c = 0;
      for (let i = 0; i < P.length; i += 3) {
        const ax = R[i] - rx, az = R[i + 2] - rz, bx = P[i] - cx, bz = P[i + 2] - cz;
        s += az * bx - ax * bz; c += ax * bx + az * bz;
      }
      const a = -Math.atan2(s, c), ca = Math.cos(a), sa = Math.sin(a);
      for (let i = 0; i < P.length; i += 3) {
        const x = P[i] - cx, z = P[i + 2] - cz;
        P[i] = x * ca + z * sa; P[i + 2] = -x * sa + z * ca;
        const vx = V[i], vz = V[i + 2]; V[i] = vx * ca + vz * sa; V[i + 2] = -vx * sa + vz * ca;
      }
    };
    const step = (sec) => { for (let k = 0; k < Math.round(sec * 60); k++) { J.advance(1 / 60); face(); } };
    // start from rest and ease up to the start level, then let it settle
    J.pos.set(J.rest); J.vel.fill(0);
    for (const k in J.REGIONS) J.REGIONS[k].value = 0;
    setLevel(clip.from); step(3);
    if (clip.kind === 'land') {
      for (let i = 1; i < J.pos.length; i += 3) J.pos[i] += 0.5;
      for (let i = 0; i < J.vel.length; i += 3) J.vel[i + 1] = -8;
    } else {
      // a hand squeeze: push every node toward the vertical axis, then change the puff target
      for (let i = 0; i < J.pos.length; i += 3) { J.vel[i] -= 4.5 * J.pos[i]; J.vel[i + 2] -= 4.5 * J.pos[i + 2]; }
      setLevel(clip.to);
    }
    const n = Math.round(clip.seconds * FPS), rows = Math.ceil(n / COLS);
    const sheet = document.createElement('canvas'); sheet.width = COLS * CELL; sheet.height = rows * CELL;
    const ctx = sheet.getContext('2d');
    for (let f = 0; f < n; f++) {
      if (f > 0) step(1 / FPS);
      J.updateMesh(); renderer.render(scene, cam);
      ctx.drawImage(renderer.domElement, (f % COLS) * CELL, Math.floor(f / COLS) * CELL);
    }
    const g = new THREE.Vector3(0, 0, 0).project(cam);
    return { png: sheet.toDataURL('image/png'), frames: n, rows, groundY: Math.round((1 - (g.y + 1) / 2) * CELL) };
  }, { clip, CELL, COLS, FPS });
  const file = `ppomo-${clip.name}.png`;
  fs.writeFileSync(path.join(outDir, file), Buffer.from(res.png.split(',')[1], 'base64'));
  meta.clips[clip.name] = { file, frames: res.frames, rows: res.rows, from: clip.from, to: clip.to };
  meta.groundY = res.groundY;
  console.log(clip.name, res.frames, 'frames', fs.statSync(path.join(outDir, file)).size, 'bytes');
}
fs.writeFileSync(path.join(outDir, 'clips.json'), JSON.stringify(meta, null, 2));
await browser.close(); server.close();
