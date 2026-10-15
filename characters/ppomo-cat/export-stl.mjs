// Export the Ppomo cat as a watertight, print-ready binary STL.
// Reads SHAPE / SCALE / BLEND / modelSDF straight from ppomo-cat-3d.html so the print matches the web preview.
// Usage: node export-stl.mjs [lengthMM=90] [gridStep=0.0122] [out=ppomo-cat.stl]
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const dir = path.dirname(fileURLToPath(import.meta.url));
const LENGTH_MM = +(process.argv[2] || 90);
const STEP = +(process.argv[3] || 0.0122);   // 0.0122 gives 0 open / 0 non-manifold edges
const OUT = path.resolve(dir, process.argv[4] || 'ppomo-cat.stl');

// ---- pull the shape code out of the web page ----
const html = readFileSync(path.join(dir, 'ppomo-cat-3d.html'), 'utf8');
const grab = (start, end) => { const a = html.indexOf(start); const b = html.indexOf(end, a); if (a < 0 || b < 0) throw new Error(`missing ${start}`); return html.slice(a, b); };
const shapeSrc = grab('const SHAPE = {', '\nconst PAL');
const fieldSrc = grab('const SCALE = {', '// ---------- surface extraction');
const { SHAPE, modelSDF } = Function(`${shapeSrc}\n${fieldSrc}\nreturn { SHAPE, modelSDF };`)();
const smin = (a, b, k) => { const h = Math.max(k - Math.abs(a - b), 0) / k; return Math.min(a, b) - h * h * k * 0.25; };
const smax = (a, b, k) => -smin(-a, -b, k);

// ---- face: eyes and mouth carved in as shallow grooves (printable, easy to paint) ----
const frontZ = (x, y) => { let z = 3; while (z > -3 && modelSDF(x, y, z) > 0) z -= 0.002; return z; };
const EYE_R = 0.05, EYE_DEPTH = 0.025;
const eyes = [-1, 1].map((s) => {
  const x = SHAPE.eye.x * s, y = SHAPE.eye.y;
  return { x, y, z: frontZ(x, y) + EYE_R - EYE_DEPTH };           // sphere sunk so the dimple is EYE_DEPTH deep
});
const M = { R: 0.034, tube: 0.017, y: SHAPE.mouth.y + 0.006 };
M.z = frontZ(0, M.y);
const mouthArcs = [-1, 1].map((s) => ({ x: s * M.R, y: M.y }));
function mouthSDF(x, y, z) {                                       // two lower half-circle grooves = ω
  let d = Infinity;
  for (const c of mouthArcs) {
    const qx = x - c.x, qy = y - c.y, dz = z - M.z;
    const dd = qy <= 0
      ? Math.hypot(Math.hypot(qx, qy) - M.R, dz)
      : Math.hypot(Math.abs(qx) - M.R, qy, dz);                    // round ends above the arc
    d = Math.min(d, dd - M.tube);
  }
  return d;
}
function printSDF(x, y, z) {
  let d = modelSDF(x, y, z);
  for (const e of eyes) d = smax(d, -(Math.hypot(x - e.x, y - e.y, z - e.z) - EYE_R), 0.008);
  d = Math.max(d, -mouthSDF(x, y, z));
  return d;
}

// ---- surface nets on a grid, projected onto the field (same method as the web viewer) ----
const MIN = [-1.1, -0.02, -1.85], MAX = [1.1, 1.66, 1.6];
const nx = Math.ceil((MAX[0] - MIN[0]) / STEP), ny = Math.ceil((MAX[1] - MIN[1]) / STEP), nz = Math.ceil((MAX[2] - MIN[2]) / STEP);
const sx = nx + 1, sxy = (nx + 1) * (ny + 1);
const val = new Float32Array(sxy * (nz + 1));
for (let k = 0; k <= nz; k++) for (let j = 0; j <= ny; j++) for (let i = 0; i <= nx; i++)
  val[i + sx * j + sxy * k] = printSDF(MIN[0] + i * STEP, MIN[1] + j * STEP, MIN[2] + k * STEP);

const cellV = new Int32Array(nx * ny * nz).fill(-1);
const cellIdx = (i, j, k) => i + nx * (j + ny * k);
const pos = [];
const EDGES = [];
for (let a = 0; a < 8; a++) for (const bit of [1, 2, 4]) if (!(a & bit)) EDGES.push([a, a | bit]);
const cv = new Float32Array(8);
for (let k = 0; k < nz; k++) for (let j = 0; j < ny; j++) for (let i = 0; i < nx; i++) {
  let mask = 0;
  for (let c = 0; c < 8; c++) {
    const v = val[(i + (c & 1)) + sx * (j + ((c >> 1) & 1)) + sxy * (k + ((c >> 2) & 1))];
    cv[c] = v; if (v < 0) mask |= 1 << c;
  }
  if (mask === 0 || mask === 255) continue;
  let px = 0, py = 0, pz = 0, n = 0;
  for (const [a, b] of EDGES) {
    if ((cv[a] < 0) === (cv[b] < 0)) continue;
    const t = cv[a] / (cv[a] - cv[b]);
    px += (a & 1) + t * ((b & 1) - (a & 1));
    py += ((a >> 1) & 1) + t * (((b >> 1) & 1) - ((a >> 1) & 1));
    pz += ((a >> 2) & 1) + t * (((b >> 2) & 1) - ((a >> 2) & 1));
    n++;
  }
  cellV[cellIdx(i, j, k)] = pos.length / 3;
  pos.push(MIN[0] + (i + px / n) * STEP, MIN[1] + (j + py / n) * STEP, MIN[2] + (k + pz / n) * STEP);
}
const tris = [];
const dims = [nx, ny, nz];
for (let k = 0; k <= nz; k++) for (let j = 0; j <= ny; j++) for (let i = 0; i <= nx; i++) {
  const g = [i, j, k], v0 = val[i + sx * j + sxy * k];
  for (let ax = 0; ax < 3; ax++) {
    const u = (ax + 1) % 3, w = (ax + 2) % 3;
    if (g[ax] >= dims[ax] || g[u] < 1 || g[w] < 1 || g[u] >= dims[u] || g[w] >= dims[w]) continue;
    const g2 = g.slice(); g2[ax]++;
    const v1 = val[g2[0] + sx * g2[1] + sxy * g2[2]];
    if ((v0 < 0) === (v1 < 0)) continue;
    const cell = (du, dw) => { const c = g.slice(); c[u] -= du; c[w] -= dw; return cellV[cellIdx(c[0], c[1], c[2])]; };
    const a = cell(1, 1), b = cell(0, 1), c = cell(0, 0), d = cell(1, 0);
    if (v0 < 0) tris.push(a, b, c, a, c, d); else tris.push(a, c, b, a, d, c);
  }
}
// project vertices onto the true surface
const e = STEP * 0.25;
for (let q = 0; q < pos.length; q += 3) {
  let x = pos[q], y = pos[q + 1], z = pos[q + 2];
  for (let it = 0; it < 3; it++) {
    const d = printSDF(x, y, z);
    let gx = printSDF(x + e, y, z) - printSDF(x - e, y, z), gy = printSDF(x, y + e, z) - printSDF(x, y - e, z), gz = printSDF(x, y, z + e) - printSDF(x, y, z - e);
    const gl = Math.hypot(gx, gy, gz) || 1; gx /= gl; gy /= gl; gz /= gl;
    x -= d * gx; y -= d * gy; z -= d * gz;
  }
  pos[q] = x; pos[q + 1] = y; pos[q + 2] = z;
}

// ---- to print space: Z up, face toward -Y, millimetres, sitting on Z = 0 ----
// (x, y, z)_three -> (x, -z, y) is a proper rotation, so triangle winding is preserved.
let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity, minZ = Infinity, maxZ = -Infinity;
const P = new Float64Array(pos.length);
for (let q = 0; q < pos.length; q += 3) {
  const X = pos[q], Y = -pos[q + 2], Z = pos[q + 1];
  P[q] = X; P[q + 1] = Y; P[q + 2] = Z;
  minX = Math.min(minX, X); maxX = Math.max(maxX, X); minY = Math.min(minY, Y); maxY = Math.max(maxY, Y); minZ = Math.min(minZ, Z); maxZ = Math.max(maxZ, Z);
}
const scale = LENGTH_MM / (maxY - minY);
for (let q = 0; q < P.length; q += 3) {
  P[q] = (P[q] - (minX + maxX) / 2) * scale;
  P[q + 1] = (P[q + 1] - (minY + maxY) / 2) * scale;
  P[q + 2] = (P[q + 2] - minZ) * scale;
}

// ---- checks: closed manifold + outward orientation ----
const edgeCount = new Map();
const key = (a, b) => (a < b ? a * 4194304 + b : b * 4194304 + a);
let vol = 0, degenerate = 0;
for (let t = 0; t < tris.length; t += 3) {
  const [a, b, c] = [tris[t], tris[t + 1], tris[t + 2]];
  for (const [p, q] of [[a, b], [b, c], [c, a]]) { const kk = key(p, q); edgeCount.set(kk, (edgeCount.get(kk) || 0) + 1); }
  const ax = P[a * 3], ay = P[a * 3 + 1], az = P[a * 3 + 2], bx = P[b * 3], by = P[b * 3 + 1], bz = P[b * 3 + 2], cx = P[c * 3], cy = P[c * 3 + 1], cz = P[c * 3 + 2];
  vol += (ax * (by * cz - bz * cy) - ay * (bx * cz - bz * cx) + az * (bx * cy - by * cx)) / 6;
  const ux = bx - ax, uy = by - ay, uz = bz - az, vx = cx - ax, vy = cy - ay, vz = cz - az;
  if (Math.hypot(uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx) < 1e-12) degenerate++;
}
let open = 0, nonManifold = 0;
for (const c of edgeCount.values()) { if (c === 1) open++; else if (c > 2) nonManifold++; }
if (vol < 0) for (let t = 0; t < tris.length; t += 3) { const tmp = tris[t + 1]; tris[t + 1] = tris[t + 2]; tris[t + 2] = tmp; }

// ---- binary STL ----
const nt = tris.length / 3;
const buf = Buffer.alloc(84 + nt * 50);
buf.write('Ppomo cat - print STL (mm, Z up)', 0, 'ascii');
buf.writeUInt32LE(nt, 80);
let o = 84;
for (let t = 0; t < tris.length; t += 3) {
  const a = tris[t] * 3, b = tris[t + 1] * 3, c = tris[t + 2] * 3;
  const ux = P[b] - P[a], uy = P[b + 1] - P[a + 1], uz = P[b + 2] - P[a + 2];
  const vx = P[c] - P[a], vy = P[c + 1] - P[a + 1], vz = P[c + 2] - P[a + 2];
  let fx = uy * vz - uz * vy, fy = uz * vx - ux * vz, fz = ux * vy - uy * vx;
  const fl = Math.hypot(fx, fy, fz) || 1;
  for (const f of [fx / fl, fy / fl, fz / fl]) { buf.writeFloatLE(f, o); o += 4; }
  for (const idx of [a, b, c]) for (let d = 0; d < 3; d++) { buf.writeFloatLE(P[idx + d], o); o += 4; }
  buf.writeUInt16LE(0, o); o += 2;
}
writeFileSync(OUT, buf);
console.log(JSON.stringify({
  out: path.basename(OUT), triangles: nt, vertices: pos.length / 3,
  sizeMM: [(maxX - minX) * scale, LENGTH_MM, (maxZ - minZ) * scale].map((v) => +v.toFixed(1)),
  volumeCm3: +(Math.abs(vol) / 1000).toFixed(1),
  openEdges: open, nonManifoldEdges: nonManifold, degenerateTris: degenerate,
  eyeDimpleMM: +(EYE_DEPTH * scale).toFixed(2), mouthGrooveWidthMM: +(2 * M.tube * scale).toFixed(2),
}, null, 1));
