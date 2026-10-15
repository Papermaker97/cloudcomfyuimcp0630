// Generates ppomo-2d.svg and ppomo-ae-build.jsx from one shape table.
import { writeFileSync, readFileSync } from 'node:fs';
const OUT = process.argv[2];
const W = 1000, H = 700, GROUND = 560;
const C = {
  body: '#F7C3C6', line: '#8A4B30', belly: '#FFF2D8', blush: '#F2A0A6', ink: '#6E3B23', shadow: '#000000',
};
// path: { start:[x,y], segs:[[c1x,c1y,c2x,c2y,x,y],...], closed }
const P = (start, segs, closed = true) => ({ start, segs, closed });
// layers bottom → top. pivot = anchor point for the AE layer. parent = AE parent layer name
const LAYERS = [
  { name: 'shadow', kind: 'ellipse', c: [530, 566], size: [840, 40], fill: C.shadow, fillOp: 8, parent: null, pivot: [530, 566] },
  { name: 'foot_back', kind: 'ellipse', c: [912, 540], size: [96, 54], fill: C.body, stroke: true, parent: 'body', pivot: [912, 540] },
  { name: 'paw_back', kind: 'ellipse', c: [142, 546], size: [92, 48], fill: C.body, stroke: true, parent: 'body', pivot: [142, 546] },
  { name: 'ear_L', kind: 'path', path: P([172, 400], [[165, 345, 190, 305, 220, 300], [250, 302, 280, 330, 302, 362]]), fill: C.body, stroke: true, parent: 'body', pivot: [240, 360] },
  { name: 'ear_R', kind: 'path', path: P([392, 345], [[392, 290, 420, 262, 448, 264], [478, 267, 505, 295, 518, 322]]), fill: C.body, stroke: true, parent: 'body', pivot: [455, 320] },
  { name: 'body', kind: 'path', path: P([175, 560], [
      [130, 560, 105, 520, 105, 470],     // left cheek
      [105, 400, 170, 345, 250, 345],     // round head top
      [330, 345, 440, 325, 520, 315],     // neck -> back (smooth)
      [600, 305, 640, 205, 720, 205],     // back rises into butt lobe 1
      [780, 205, 800, 215, 812, 232],     // into the cleft (only crease)
      [830, 212, 850, 210, 880, 212],     // butt lobe 2
      [940, 216, 962, 300, 962, 380],     // round right side
      [962, 470, 950, 540, 900, 550],
      [870, 558, 800, 561, 760, 561],
    ]), fill: C.body, stroke: true, parent: null, pivot: [530, 560] },
  { name: 'belly', kind: 'path', path: P([162, 540], [
      [230, 498, 330, 488, 420, 503],
      [560, 478, 720, 468, 882, 520],
      [862, 548, 820, 556, 760, 556],
      [560, 557, 360, 557, 182, 556],
      [172, 553, 165, 548, 162, 540],
    ]), fill: C.belly, parent: 'body', pivot: [520, 540] },
  { name: 'butt_line', kind: 'path', path: P([812, 236], [[822, 258, 824, 285, 818, 312]], false), stroke: true, parent: 'body', pivot: [818, 274] },
  { name: 'blush_L', kind: 'ellipse', c: [190, 502], size: [78, 46], fill: C.blush, fillOp: 45, parent: 'body', pivot: [190, 502] },
  { name: 'blush_R', kind: 'ellipse', c: [420, 502], size: [78, 46], fill: C.blush, fillOp: 45, parent: 'body', pivot: [420, 502] },
  { name: 'paw_front', kind: 'ellipse', c: [482, 548], size: [112, 54], fill: C.body, stroke: true, parent: 'body', pivot: [482, 548] },
  { name: 'eye_L', kind: 'ellipse', c: [226, 470], size: [28, 28], fill: C.ink, parent: 'body', pivot: [226, 470] },
  { name: 'eye_R', kind: 'ellipse', c: [388, 470], size: [28, 28], fill: C.ink, parent: 'body', pivot: [388, 470] },
  { name: 'mouth', kind: 'path', path: P([290, 478], [[294, 490, 302, 490, 306, 478], [310, 490, 318, 490, 322, 478]], false), stroke: true, strokeW: 5, parent: 'body', pivot: [306, 482] },
];
const STROKE_W = 6;

// ---------- SVG ----------
const d = (p) => `M ${p.start.join(' ')} ` + p.segs.map((s) => `C ${s.slice(0, 2).join(' ')}, ${s.slice(2, 4).join(' ')}, ${s.slice(4).join(' ')}`).join(' ') + (p.closed ? ' Z' : '');
const svgLayer = (L) => {
  const fill = L.fill ? `fill="${L.fill}"${L.fillOp != null ? ` fill-opacity="${L.fillOp / 100}"` : ''}` : 'fill="none"';
  const stroke = L.stroke ? `stroke="${C.line}" stroke-width="${L.strokeW || STROKE_W}" stroke-linecap="round" stroke-linejoin="round"` : '';
  const shape = L.kind === 'ellipse'
    ? `<ellipse cx="${L.c[0]}" cy="${L.c[1]}" rx="${L.size[0] / 2}" ry="${L.size[1] / 2}" ${fill} ${stroke}/>`
    : `<path d="${d(L.path)}" ${fill} ${stroke}/>`;
  return `  <g id="${L.name}">\n    ${shape}\n  </g>`;
};
writeFileSync(`${OUT}/ppomo-2d.svg`, `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}">
  <title>Ppomo 2D — layered for After Effects</title>
  <rect id="bg" width="${W}" height="${H}" fill="#FBF3EA"/>
${LAYERS.map(svgLayer).join('\n')}
</svg>
`);

// ---------- AE: shape path → vertices / tangents ----------
function aeShape(p) {
  const v = [p.start], inT = [[0, 0]], outT = [];
  p.segs.forEach((s, i) => {
    const prev = v[v.length - 1];
    outT[i] = [s[0] - prev[0], s[1] - prev[1]];
    v.push([s[4], s[5]]);
    inT.push([s[2] - s[4], s[3] - s[5]]);
  });
  outT.push([0, 0]);
  return { v, inT, outT, closed: p.closed };
}
const hex = (h) => [1, 3, 5].map((i) => +(parseInt(h.slice(i, i + 2), 16) / 255).toFixed(4));
const layerData = LAYERS.map((L) => ({
  name: L.name, kind: L.kind, parent: L.parent, pivot: L.pivot,
  c: L.c, size: L.size,
  shape: L.kind === 'path' ? aeShape(L.path) : null,
  fill: L.fill ? hex(L.fill) : null, fillOp: L.fillOp ?? 100,
  stroke: !!L.stroke, strokeW: L.strokeW || STROKE_W,
}));
const tpl = readFileSync(process.argv[3], 'utf8');
writeFileSync(`${OUT}/ppomo-ae-build.jsx`, tpl
  .replace('/*__LAYERS__*/', JSON.stringify(layerData))
  .replace('/*__LINE__*/', JSON.stringify(hex(C.line))));
console.log('ok', LAYERS.length, 'layers');
