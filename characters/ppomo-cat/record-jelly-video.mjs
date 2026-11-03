// Record the jelly Ppomo (ppomo-jelly-drop.html) as an MP4: drop, settle, three squeezes that puff it up, then deflate.
// Usage: node record-jelly-video.mjs <three.js dir> <frames dir> ; then ffmpeg (see the end of this file's output).
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
const { chromium } = createRequire(import.meta.url)('playwright');
const [threeDir, outDir] = process.argv.slice(2);
const here = path.dirname(new URL(import.meta.url).pathname);
const page = fs.readFileSync(path.join(here, 'ppomo-jelly-drop.html'), 'utf8');
const html = `<!doctype html><html><head><meta charset="utf-8"><style>body{margin:0}</style></head><body>${page}</body></html>`;
const server = http.createServer((q, r) => { r.writeHead(200, { 'content-type': 'text/html' }); r.end(html); }).listen(8779);
fs.mkdirSync(outDir, { recursive: true });

const browser = await chromium.launch();
const tab = await browser.newPage({ viewport: { width: 900, height: 900 } });
await tab.route('**/*', (r) => {
  const u = r.request().url();
  if (u.startsWith('http://localhost')) return r.continue();
  const m = u.match(/three@0\.160\.0\/(.*)$/);
  if (m) return r.fulfill({ body: fs.readFileSync(path.join(threeDir, m[1])), contentType: 'text/javascript' });
  return r.abort();
});
await tab.goto('http://localhost:8779/?bake');
await tab.waitForFunction(() => document.body.dataset.bake === '1', null, { timeout: 120000 });
await tab.evaluate(() => {
  const J = window.ppomoJelly, { THREE, renderer, scene } = J;
  J.setFirmness(50); J.setDamping(30);
  renderer.setPixelRatio(1); renderer.setSize(720, 720); renderer.setClearColor(0xEEEDF1, 1);
  const cam = new THREE.PerspectiveCamera(30, 1, 0.1, 80);
  cam.position.set(3.6, 3.0, 6.6); cam.lookAt(0, 1.25, 0);
  window.__cam = cam;
  // drop straight down from 3.5 units, a little tilted
  const q = new THREE.Quaternion().setFromEuler(new THREE.Euler(0.1, 0.5, -0.06)), c = new THREE.Vector3(0, 0.95, 0), v = new THREE.Vector3();
  for (let i = 0; i < J.pos.length; i += 3) { v.fromArray(J.rest, i).sub(c).applyQuaternion(q).add(c); J.pos[i] = v.x; J.pos[i + 1] = v.y + 3.5; J.pos[i + 2] = v.z; }
  J.vel.fill(0);
});
const FPS = 30, total = 9 * FPS;
// timeline (seconds): 0 drop · 2.6, 3.6, 4.6 squeeze all three parts · 6.6 deflate
const events = { [Math.round(2.6 * FPS)]: 'sq', [Math.round(3.6 * FPS)]: 'sq', [Math.round(4.6 * FPS)]: 'sq', [Math.round(6.6 * FPS)]: 'deflate' };
for (let f = 0; f < total; f++) {
  const png = await tab.evaluate((ev) => {
    const J = window.ppomoJelly;
    if (ev === 'sq') { for (const k of ['cheek', 'belly', 'butt']) J.squeeze(k); for (let i = 0; i < J.pos.length; i += 3) { J.vel[i] -= 2.5 * J.pos[i]; J.vel[i + 2] -= 2.5 * J.pos[i + 2]; } }
    if (ev === 'deflate') for (const k in J.REGIONS) J.REGIONS[k].target = 0;
    J.advance(1 / 30); J.updateMesh();
    J.renderer.render(J.scene, window.__cam);
    return J.renderer.domElement.toDataURL('image/png');
  }, events[f] || null);
  fs.writeFileSync(path.join(outDir, `f${String(f).padStart(4, '0')}.png`), Buffer.from(png.split(',')[1], 'base64'));
}
console.log('frames', total);
await browser.close(); server.close();
