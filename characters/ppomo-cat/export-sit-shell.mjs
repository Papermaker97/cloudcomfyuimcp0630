// Hollow sitting Ppomo (ppomo-sit-3d.html) with a small round opening in the flat bottom. No lid.
//   - outer shape kept, inside hollowed to a constant wall
//   - legs, ears, paws stay solid (cavity thinner than MIN_CAVITY_MM is never opened)
//   - the bottom is a thicker flat floor with one round hole (parts go in through it)
//   - a shallow groove under the floor runs from the hole to the back, so a USB cable can lie in it
//     and the toy still sits flat
// Usage: node --max-old-space-size=6000 export-sit-shell.mjs [heightMM=95] [wallMM=2.5]
// Env: OPEN_MM (hole diameter, 30), FLOOR_MM (floor thickness, 5), GROOVE_W_MM (7), GROOVE_D_MM (3), STEP, SECTION_OUT
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { writeFileSync } from 'node:fs';
import {
  FLOOR_Y, smin, loadModel, makeGrid, sample, lookup, distanceToOutside,
  surfaceNets, toPrint, checkAndOrient, writeSTL,
} from './stl-lib.mjs';

const dir = path.dirname(fileURLToPath(import.meta.url));
const HEIGHT_MM = +(process.argv[2] || 95);
const WALL_MM = +(process.argv[3] || 2.5);
const OPEN_MM = +(process.env.OPEN_MM || 30);
const FLOOR_MM = +(process.env.FLOOR_MM || 5);
const GROOVE_W_MM = +(process.env.GROOVE_W_MM || 7);
const GROOVE_D_MM = +(process.env.GROOVE_D_MM || 3);
const MIN_CAVITY_MM = 3.0;
const STEP = +(process.env.STEP || 0.0127);   // grid step that meshes with no non-manifold edges for the current shape at 95 mm; re-check after shape edits
const tag = `${HEIGHT_MM}mm`;

const model = loadModel(dir, 'ppomo-sit-3d.html');
const MIN = [-1.2, -0.1, -1.3], MAX = [1.2, 2.2, 1.3];
const grid = makeGrid(MIN, MAX, STEP);

// ---- 1. outer shape and scale (by height) ----
const outer = sample(grid, model.printSDF);
let yHi = -Infinity;
for (let q = 0; q < grid.size; q++) if (outer[q] < 0) { const j = Math.floor(q / grid.sx) % (grid.n[1] + 1); yHi = Math.max(yHi, MIN[1] + j * STEP); }
const mm = HEIGHT_MM / (yHi - FLOOR_Y + STEP);
const t = WALL_MM / mm, r = MIN_CAVITY_MM / mm;
const FLOOR_TOP = FLOOR_Y + FLOOR_MM / mm;

// ---- 2. cavity: morphological opening of "deeper than the wall", kept above the floor ----
const inBody = new Uint8Array(grid.size);
for (let q = 0; q < grid.size; q++) inBody[q] = outer[q] < 0 ? 1 : 0;
const depth = distanceToOutside(grid, inBody);
const notCore = new Uint8Array(grid.size);
for (let q = 0; q < grid.size; q++) notCore[q] = depth[q] - STEP / 2 > t + r ? 0 : 1;
const toCore = distanceToOutside(grid, notCore);
const toCoreAt = lookup(grid, toCore);
// the carved eyes and mouth eat into the wall, so the cavity keeps a full wall's distance from them
const frontZ = (x, y) => { let z = 3; while (z > -3 && model.modelSDF(x, y, z) > 0) z -= 0.002; return z; };
const S = model.SHAPE, FACE_R = 0.06 + t;
const faceKeep = [[-S.eye.x, S.eye.y], [S.eye.x, S.eye.y], [-0.034, S.mouth.y], [0.034, S.mouth.y]].map(([x, y]) => [x, y, frontZ(x, y)]);
const keepOut = (x, y, z) => { let d = Infinity; for (const c of faceKeep) d = Math.min(d, Math.hypot(x - c[0], y - c[1], z - c[2]) - FACE_R); return d; };
const inner = (x, y, z, toCoreV) => Math.min(smin(r - toCoreV, keepOut(x, y, z), 0.03), y - FLOOR_TOP);
const cavityOut = (x, y, z) => inner(x, y, z, toCoreAt(x, y, z));   // > 0 inside the cavity

// hole centre = middle of the cavity footprint just above the floor
let xs = 0, zs = 0, n = 0, cMin = [Infinity, Infinity], cMax = [-Infinity, -Infinity];
for (let z = MIN[2]; z <= MAX[2]; z += STEP / 2) for (let x = MIN[0]; x <= MAX[0]; x += STEP / 2)
  if (cavityOut(x, FLOOR_TOP + 2 * STEP, z) > 0) {
    xs += x; zs += z; n++;
    cMin = [Math.min(cMin[0], x), Math.min(cMin[1], z)]; cMax = [Math.max(cMax[0], x), Math.max(cMax[1], z)];
  }
const HC = [xs / n, zs / n], HR = OPEN_MM / 2 / mm;
const footprintMM = [(cMax[0] - cMin[0]) * mm, (cMax[1] - cMin[1]) * mm].map((v) => +v.toFixed(1));
if (OPEN_MM >= Math.min(...footprintMM) - 2 * WALL_MM) throw new Error(`opening ${OPEN_MM} mm is wider than the cavity floor ${footprintMM}`);

// ---- 3. cut-outs through the floor: round hole + cable groove toward the back (-z) ----
const hole = (x, y, z) => Math.min(HR - Math.hypot(x - HC[0], z - HC[1]), FLOOR_TOP + STEP - y);
const GW = GROOVE_W_MM / 2 / mm, GD = FLOOR_Y + GROOVE_D_MM / mm;
const groove = (x, y, z) => Math.min(GW - Math.abs(x - HC[0]), GD - y, HC[1] - z);
const cutOut = (x, y, z) => Math.max(cavityOut(x, y, z), hole(x, y, z), groove(x, y, z));

// ---- 4. shell ----
const shellField = (x, y, z) => Math.max(model.printSDF(x, y, z), cutOut(x, y, z));
const shellVal = new Float32Array(grid.size);
for (let k = 0; k <= grid.n[2]; k++) for (let j = 0; j <= grid.n[1]; j++) for (let i = 0; i <= grid.n[0]; i++) {
  const q = grid.at(i, j, k), x = MIN[0] + i * STEP, y = MIN[1] + j * STEP, z = MIN[2] + k * STEP;
  shellVal[q] = Math.max(outer[q], inner(x, y, z, toCore[q]), hole(x, y, z), groove(x, y, z));
}
const shell = surfaceNets(grid, shellVal, shellField, 2);

// ---- 5. section image (x = hole centre): dark = shell, white = air, front on the left ----
if (process.env.SECTION_OUT) {
  const { deflateSync, crc32 } = await import('node:zlib');
  const res = 0.2 / mm, y0 = FLOOR_Y - 2 / mm, W = Math.ceil((MAX[2] - MIN[2]) / res), H = Math.ceil((MAX[1] - y0) / res);
  const raw = Buffer.alloc((W * 3 + 1) * H);
  for (let yy = 0; yy < H; yy++) for (let xx = 0; xx < W; xx++) {
    const y = MAX[1] - yy * res, z = MAX[2] - xx * res;
    raw.set(shellField(HC[0], y, z) < 0 ? [70, 72, 80] : [250, 250, 252], yy * (W * 3 + 1) + 1 + xx * 3);
  }
  const chunk = (type, data) => { const len = Buffer.alloc(4); len.writeUInt32BE(data.length); const td = Buffer.concat([Buffer.from(type), data]); const crc = Buffer.alloc(4); crc.writeUInt32BE(crc32(td)); return Buffer.concat([len, td, crc]); };
  const ihdr = Buffer.alloc(13); ihdr.writeUInt32BE(W, 0); ihdr.writeUInt32BE(H, 4); ihdr[8] = 8; ihdr[9] = 2;
  writeFileSync(process.env.SECTION_OUT, Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk('IHDR', ihdr), chunk('IDAT', deflateSync(raw)), chunk('IEND', Buffer.alloc(0))]));
}

// ---- 6. inner size, for checking parts fit ----
let iLo = [Infinity, Infinity, Infinity], iHi = [-Infinity, -Infinity, -Infinity];
for (let k = 0; k <= grid.n[2]; k++) for (let j = 0; j <= grid.n[1]; j++) for (let i = 0; i <= grid.n[0]; i++) {
  const q = grid.at(i, j, k), y = MIN[1] + j * STEP;
  if (r - toCore[q] > 0 && y > FLOOR_TOP) { const p = [MIN[0] + i * STEP, y, MIN[2] + k * STEP]; for (let d = 0; d < 3; d++) { iLo[d] = Math.min(iLo[d], p[d]); iHi[d] = Math.max(iHi[d], p[d]); } }
}
const cavityMM = { width: (iHi[0] - iLo[0]) * mm, height: (iHi[1] - iLo[1]) * mm, depth: (iHi[2] - iLo[2]) * mm };

// ---- 7. write (mm, Z up, bed on Z = 0, front of the cat toward -Y) ----
let lo = [Infinity, Infinity, Infinity], hi = [-Infinity, -Infinity, -Infinity];
for (let q = 0; q < shell.pos.length; q += 3) for (let d = 0; d < 3; d++) { lo[d] = Math.min(lo[d], shell.pos[q + d]); hi[d] = Math.max(hi[d], shell.pos[q + d]); }
const P = toPrint(shell.pos, mm, [(lo[0] + hi[0]) / 2, -(lo[2] + hi[2]) / 2, lo[1]]);
const { badAt, ...rep } = checkAndOrient(P, shell.tris);
if (process.env.DEBUG_BAD) console.error('non-manifold at (mm):', JSON.stringify(badAt.slice(0, 40)));
writeSTL(path.join(dir, `ppomo-sit-shell-${tag}.stl`), P, shell.tris, `Ppomo sitting hollow shell ${tag} (mm, Z up)`);
const round = (o) => Object.fromEntries(Object.entries(o).map(([k, v]) => [k, +v.toFixed(1)]));
console.log(JSON.stringify({
  heightMM: HEIGHT_MM, wallMM: WALL_MM, floorMM: FLOOR_MM, openingMM: OPEN_MM,
  groove: `${GROOVE_W_MM} wide x ${GROOVE_D_MM} deep, hole to back`, cavityFloorMM: footprintMM,
  cavityMM: round(cavityMM), shell: rep,
}, null, 1));
