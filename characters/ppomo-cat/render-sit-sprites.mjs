// Render the round sitting Ppomo (ppomo-jelly-drop.html) as transparent sprites for the p5 doomscroll pile:
// 4 views (front, butt, side, peek = 3/4) × 6 colours, 300×300 px each, named <view>-<colour>.png.
// Usage: node render-sit-sprites.mjs <three.js dir with build/ and examples/> <out dir>
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
const { chromium } = createRequire(import.meta.url)('playwright');

const [threeDir, outDir] = process.argv.slice(2);
const here = path.dirname(new URL(import.meta.url).pathname);
const page = fs.readFileSync(path.join(here, 'ppomo-jelly-drop.html'), 'utf8');
const html = `<!doctype html><html><head><meta charset="utf-8"><style>body{margin:0}</style></head><body>${page}</body></html>`;
const server = http.createServer((q, r) => { r.writeHead(200, { 'content-type': 'text/html' }); r.end(html); }).listen(8778);

const COLORS = { grey: '#AEB3C2', pink: '#F2AABD', cream: '#F3E6D8', peach: '#F2C7A4', lilac: '#D2C0EC', sky: '#BCD3F0' };
const VIEWS = { front: [0, 0.18, 1], butt: [0, 0.18, -1], side: [1, 0.12, 0], peek: [0.75, 0.2, 0.75] };
const SIZE = 300;

const browser = await chromium.launch();
const tab = await browser.newPage({ viewport: { width: 700, height: 700 } });
await tab.route('**/*', (r) => {
  const u = r.request().url();
  if (u.startsWith('http://localhost')) return r.continue();
  const m = u.match(/three@0\.160\.0\/(.*)$/);
  if (m) return r.fulfill({ body: fs.readFileSync(path.join(threeDir, m[1])), contentType: 'text/javascript' });
  return r.abort();
});
tab.on('pageerror', (e) => console.log('page error:', e.message));
await tab.goto('http://localhost:8778/?bake');
await tab.waitForFunction(() => document.body.dataset.bake === '1', null, { timeout: 120000 });

for (const [cname, hex] of Object.entries(COLORS)) {
  for (const [vname, dir] of Object.entries(VIEWS)) {
    const png = await tab.evaluate(({ hex, dir, SIZE }) => {
      const J = window.ppomoJelly, { THREE, renderer, scene, ground } = J;
      J.pos.set(J.rest); J.updateMesh(); J.recolor(hex);
      ground.visible = false;
      renderer.setPixelRatio(1); renderer.setSize(SIZE, SIZE); renderer.setClearColor(0x000000, 0);
      const c = new THREE.Vector3(0, 1.0, 0), cam = new THREE.OrthographicCamera(-1.55, 1.55, 1.55, -1.55, 0.1, 40);
      cam.position.copy(new THREE.Vector3(...dir).normalize().multiplyScalar(12).add(c)); cam.lookAt(c);
      renderer.render(scene, cam);
      return renderer.domElement.toDataURL('image/png');
    }, { hex, dir, SIZE });
    fs.writeFileSync(path.join(outDir, `${vname}-${cname}.png`), Buffer.from(png.split(',')[1], 'base64'));
  }
}
console.log('wrote', Object.keys(COLORS).length * Object.keys(VIEWS).length, 'sprites');
await browser.close(); server.close();
