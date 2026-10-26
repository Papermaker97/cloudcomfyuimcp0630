// Cuts render-sprites.json (rendered with render-pile.py) into one transparent PNG per Ppomo, for the p5 jelly sketch.
// THREE_DIR=<three package> node sprite-shot.mjs <rendered.html> render-sprites.json ../ppomo-icm/jelly/sprites
import { chromium } from 'playwright';
import { readFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
const [, , html, layoutPath, outDir] = process.argv;
const layout = JSON.parse(readFileSync(layoutPath, 'utf8'));
const W = 1800, H = 1200, PX = 75;                       // ortho half-height 8 -> 75 px per unit; cells are 4 units = 300 px
const b = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const p = await b.newPage({ viewport: { width: W, height: H } });
await p.route('https://cdn.jsdelivr.net/npm/three@0.160.0/**', (r) => r.fulfill({ body: readFileSync(`${process.env.THREE_DIR}/${r.request().url().split('three@0.160.0/')[1]}`), contentType: 'application/javascript' }));
await p.route('https://fonts.*/**', (r) => r.abort());
await p.goto(pathToFileURL(html).href);
await p.waitForSelector('body[data-ready="1"]', { timeout: 400000 });
await p.addStyleTag({ content: 'html, body { background: transparent !important; }' });
await p.waitForTimeout(500);
for (const q of layout.ppomos) {
  const cx = W / 2 + q.x * PX, cy = H / 2 - q.y * PX;
  await p.screenshot({ path: `${outDir}/${q.name}.png`, omitBackground: true, clip: { x: cx - 150, y: cy - 150, width: 300, height: 300 } });
}
await b.close();
console.log('wrote', layout.ppomos.length);
