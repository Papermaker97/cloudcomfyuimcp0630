// Bakes the v6 3D Ppomo into PNG frames at increasing puff (cheeks -> belly -> butt),
// so the show page can run on a slow laptop without live 3D.
//   node bake-puff.js <outDir> [frames=24] [test]
// Uses ../../ppomo-cat/ppomo-v6.html as the model. Written with help from Claude.
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const SRC = path.join(__dirname, '../../ppomo-cat/ppomo-v6.html');
const out = process.argv[2], N = Number(process.argv[3] || 24), TEST = process.argv[4] === 'test';
fs.mkdirSync(out, { recursive: true });

let html = fs.readFileSync(SRC, 'utf8');
html = html.replace("preserveDrawingBuffer: SHEET", "preserveDrawingBuffer: true");
// more room around the body so the puffed parts are not cut off
html = html.replace("const BOUNDS = { min: [-1.0, -0.02, -1.45], max: [1.0, 1.3, 1.3] };", "const BOUNDS = { min: [-1.35, -0.02, -1.85], max: [1.35, 1.6, 1.6] };");
html = html.replace('</head>', '<style>body{background:transparent!important} header,.controls{display:none!important} #stage{position:fixed!important;inset:0!important;width:100vw!important;height:100vh!important}</style></head>');
const last = html.lastIndexOf('</script>');
html = html.slice(0, last) + '\nwindow.bake = { renderer, scene, camera, ground, controls, TARGET, THREE };\n' + html.slice(last);

const server = http.createServer((q, r) => { r.writeHead(200, { 'Content-Type': 'text/html' }); r.end(html); }).listen(0, async () => {
  const b = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: 640, height: 640 } });
  p.on('pageerror', (e) => console.log('pageerror', e.message));
  await p.goto(`http://localhost:${server.address().port}/`);
  await p.waitForFunction(() => window.bake && document.body.dataset.ready === '1', null, { timeout: 120000 });
  await p.evaluate(() => {
    const { renderer, camera, ground, controls, TARGET } = window.bake;
    renderer.setAnimationLoop(null);
    controls.autoRotate = false;
    ground.visible = false;
    renderer.setClearColor(0x000000, 0);
    // a 3/4 front view from a little above: face, one cheek, the belly line and one butt lobe are all visible
    camera.position.set(0.55, 0.38, 1).normalize().multiplyScalar(6.4).add(TARGET.clone().add(new window.bake.THREE.Vector3(0, 0.05, 0)));
    camera.lookAt(TARGET.x, TARGET.y + 0.05, TARGET.z);
    camera.fov = 30; camera.updateProjectionMatrix();
  });
  const ramp = (t, a, b) => Math.min(1, Math.max(0, (t - a) / (b - a)));
  const frames = TEST ? [0, 1] : Array.from({ length: N }, (_, i) => i / (N - 1));
  for (let i = 0; i < frames.length; i++) {
    const t = frames[i];
    const s = { cheek: 1 + 0.4 * ramp(t, 0, 0.4), belly: 1 + 0.38 * ramp(t, 0.3, 0.7), butt: 1 + 0.5 * ramp(t, 0.6, 1) };
    const url = await p.evaluate((s) => {
      const P = window.ppomo;
      P.scales.cheekL = s.cheek; P.scales.cheekR = s.cheek; P.scales.belly = s.belly;
      P.setScale('butt', s.butt);            // setScale rebuilds the mesh once with all four values
      const { renderer, scene, camera } = window.bake;
      renderer.render(scene, camera);
      return renderer.domElement.toDataURL('image/png');
    }, s);
    const name = TEST ? `test-${i}.png` : `puff-${String(i).padStart(2, '0')}.png`;
    fs.writeFileSync(path.join(out, name), Buffer.from(url.split(',')[1], 'base64'));
    console.log(name, JSON.stringify(s));
  }
  await b.close(); server.close();
});
