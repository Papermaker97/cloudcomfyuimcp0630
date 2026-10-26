// Drops lying Ppomos into a thin glass jar and lets them settle so none of them overlap, then writes a
// render-pile layout seen straight on. Each Ppomo is approximated by the spheres it is built from
// (head, cheeks, ears, torso, rump, butt, paws, feet); a position-based solver with gravity pushes
// apart any spheres of different Ppomos that touch, and keeps them inside the jar.
// HALF_H=6 node gen-jelly-sim.mjs [seed] [count] > render-jelly-sim.json; then python3 render-pile.py render-jelly-sim.json out.html
// (ppomo-jelly-sim.png: HALF_H=6, seed 7, count 36)
const seed = +(process.argv[2] || 7);
const COUNT = +(process.argv[3] || 70);

let s0 = seed >>> 0;
const rand = () => { s0 = (s0 + 0x6D2B79F5) >>> 0; let t = s0; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
const uni = (a, b) => a + (b - a) * rand();
const pick = (arr) => arr[Math.floor(rand() * arr.length)];

const HALF_H = +(process.env.HALF_H || 5);   // view half-height; no overlap means fewer, bigger-looking Ppomos
const HALF_W = HALF_H * 9 / 16;         // portrait 9:16
const JAR = { x: HALF_W + 0.7, zMin: -3.2, zMax: 1.8, floor: -HALF_H - 1.0 };   // deep enough for a back row that fills the gaps   // walls just outside the frame
const PIVOT = [0, 0.65, -0.1];
const SCALE = 1.15;
const PALETTE = [...Array(4).fill('#AEB3C2'), ...Array(4).fill('#F2AABD'), '#F3E6D8', '#F3E6D8', '#F2C7A4', '#F2C7A4', '#D2C0EC', '#D2C0EC', '#BCD3F0'];

// the lying Ppomo's parts (ppomo-cat-3d.html SHAPE), as collision spheres [x, y, z, r]
const PARTS = [
  [0, 0.60, 0.68, 0.60],
  [0.39, 0.45, 1.05, 0.31], [-0.39, 0.45, 1.05, 0.31],
  [0.36, 1.04, 0.62, 0.19], [-0.36, 1.04, 0.62, 0.19],
  [0, 0.64, -0.28, 0.66], [0.32, 0.60, -0.28, 0.56], [-0.32, 0.60, -0.28, 0.56],
  [0, 0.78, -0.74, 0.72],
  [0.31, 0.56, -1.19, 0.41], [-0.31, 0.56, -1.19, 0.41],
  [0.50, 0.14, 0.66, 0.15], [-0.50, 0.14, 0.66, 0.15], [0.66, 0.14, -0.84, 0.15], [-0.66, 0.14, -0.84, 0.15],
];

function pose() {
  const r = rand();
  if (r < 0.74) return { rx: uni(-0.15, 0.25), ry: uni(-0.45, 0.45) };                       // face front
  if (r < 0.85) return { rx: uni(-0.2, 0.2), ry: Math.PI + uni(-0.35, 0.35) };              // butt
  if (r < 0.93) return { rx: uni(-0.1, 0.1), ry: (rand() < 0.5 ? -1 : 1) * (Math.PI / 2 + uni(-0.3, 0.3)) };   // side on
  return { rx: uni(0.6, 0.9), ry: uni(-0.4, 0.4) };                                          // tipped back
}
// three.js Euler order 'ZXY': R = Rz * Rx * Ry
function rotate(v, rx, ry, rz) {
  let [x, y, z] = v;
  [x, z] = [x * Math.cos(ry) + z * Math.sin(ry), -x * Math.sin(ry) + z * Math.cos(ry)];
  [y, z] = [y * Math.cos(rx) - z * Math.sin(rx), y * Math.sin(rx) + z * Math.cos(rx)];
  [x, y] = [x * Math.cos(rz) - y * Math.sin(rz), x * Math.sin(rz) + y * Math.cos(rz)];
  return [x, y, z];
}

const bodies = [];
for (let i = 0; i < COUNT; i++) {
  const p = pose();
  const rz = rand() < 0.8 ? uni(-0.35, 0.35) : uni(-0.9, 0.9);
  const s = SCALE * uni(0.92, 1.1), squish = uni(0, 0.12), sx = 1 + squish, sy = 1 - squish;
  const spheres = PARTS.map(([x, y, z, r]) => {
    const o = rotate([(x - PIVOT[0]) * s * sx, (y - PIVOT[1]) * s * sy, (z - PIVOT[2]) * s], p.rx, p.ry, rz);
    return { o, r: r * s * (sx + sy + 1) / 3 };
  });
  const reach = Math.max(...spheres.map((q) => Math.hypot(...q.o) + q.r));
  bodies.push({
    // three per layer, far enough apart that nothing starts overlapping
    pos: [((i % 3) - 1) * HALF_W * 0.62 + uni(-0.3, 0.3), JAR.floor + 2.5 + Math.floor(i / 3) * 3.6, Math.floor(i / 3) % 2 ? -1.8 : 0.3],
    prev: null, vel: [0, 0, 0], spheres, reach,
    out: { rx: +p.rx.toFixed(3), ry: +p.ry.toFixed(3), rz: +rz.toFixed(3), s: +s.toFixed(3), sx: +sx.toFixed(3), sy: +sy.toFixed(3), color: pick(PALETTE) },
  });
}

// ---- position-based settling ----
const DT = 1 / 60, G = 9.8, STEPS = 2400, ITERS = 6, DAMP = 0.98, MAX_V = 8;
for (let step = 0; step < STEPS; step++) {
  for (const b of bodies) {
    b.prev = b.pos.slice();
    b.vel[1] -= G * DT;
    for (let d = 0; d < 3; d++) b.pos[d] += b.vel[d] * DT;
  }
  for (let it = 0; it < ITERS; it++) {
    for (let i = 0; i < bodies.length; i++) {
      const A = bodies[i];
      for (let j = i + 1; j < bodies.length; j++) {
        const B = bodies[j];
        const dx = A.pos[0] - B.pos[0], dy = A.pos[1] - B.pos[1], dz = A.pos[2] - B.pos[2];
        if (dx * dx + dy * dy + dz * dz > (A.reach + B.reach) ** 2) continue;
        const push = [0, 0, 0];
        for (const a of A.spheres) for (const c of B.spheres) {
          const vx = A.pos[0] + a.o[0] - B.pos[0] - c.o[0], vy = A.pos[1] + a.o[1] - B.pos[1] - c.o[1], vz = A.pos[2] + a.o[2] - B.pos[2] - c.o[2];
          const dist = Math.hypot(vx, vy, vz) || 1e-6, pen = a.r + c.r - dist;
          if (pen > 0) { push[0] += vx / dist * pen; push[1] += vy / dist * pen; push[2] += vz / dist * pen; }
        }
        for (let d = 0; d < 3; d++) { A.pos[d] += push[d] * 0.25; B.pos[d] -= push[d] * 0.25; }
      }
    }
    for (const b of bodies) for (const q of b.spheres) {   // jar walls and floor
      const x = b.pos[0] + q.o[0], y = b.pos[1] + q.o[1], z = b.pos[2] + q.o[2];
      if (x - q.r < -JAR.x) b.pos[0] += -JAR.x - (x - q.r);
      if (x + q.r > JAR.x) b.pos[0] -= x + q.r - JAR.x;
      if (y - q.r < JAR.floor) b.pos[1] += JAR.floor - (y - q.r);
      if (z - q.r < JAR.zMin) b.pos[2] += JAR.zMin - (z - q.r);
      if (z + q.r > JAR.zMax) b.pos[2] -= z + q.r - JAR.zMax;
    }
  }
  for (const b of bodies) for (let d = 0; d < 3; d++) b.vel[d] = Math.max(-MAX_V, Math.min(MAX_V, (b.pos[d] - b.prev[d]) / DT * DAMP));
}

// ---- report: deepest remaining overlap between different Ppomos, and how high the pile reaches ----
let worst = 0, top = -Infinity;
for (let i = 0; i < bodies.length; i++) {
  for (const q of bodies[i].spheres) top = Math.max(top, bodies[i].pos[1] + q.o[1] + q.r);
  for (let j = i + 1; j < bodies.length; j++)
    for (const a of bodies[i].spheres) for (const c of bodies[j].spheres) {
      const pen = a.r + c.r - Math.hypot(...[0, 1, 2].map((d) => bodies[i].pos[d] + a.o[d] - bodies[j].pos[d] - c.o[d]));
      worst = Math.max(worst, pen);
    }
}
const viewBottom = JAR.floor + 0.6, centerY = viewBottom + HALF_H;
console.error(JSON.stringify({ count: COUNT, deepestOverlap: +worst.toFixed(3), pileTop: +top.toFixed(2), viewTop: +(viewBottom + 2 * HALF_H).toFixed(2) }));

console.log(JSON.stringify({
  source: 'ppomo-cat-3d.html',
  camera: { ortho: HALF_H, target: [0, +centerY.toFixed(3), 0], pos: [0, 0, 60] },
  pivot: PIVOT,
  meshStep: 0.025,
  background: '#F4ECE8',
  noGround: true,
  sun: [-5, 9, 16],
  shadowBox: 10,
  light: { hemi: 0.45, sun: 1.7, env: 0.3, exposure: 0.95, shadowRadius: 6 },
  ppomos: bodies.map((b) => ({ x: +b.pos[0].toFixed(3), y: +b.pos[1].toFixed(3), z: +b.pos[2].toFixed(3), ...b.out })),
}, null, 1));
