// Hollow Ppomo shell, open underneath the belly and head. No lid.
//   - outer shape kept, inside hollowed to a constant wall
//   - legs, ears and paws stay solid and untouched (only the main body is hollowed)
//   - the opening goes through the underside of the belly/head; only the rim around it is trimmed flat
//     so the edge has the full wall thickness instead of a knife edge
// Usage: node export-shell.mjs [lengthMM=110] [wallMM=2.5]
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import {
  FLOOR_Y, loadModel, makeGrid, sample, lookup, distanceToOutside,
  surfaceNets, toPrint, checkAndOrient, writeSTL,
} from './stl-lib.mjs';

const dir = path.dirname(fileURLToPath(import.meta.url));
const LENGTH_MM = +(process.argv[2] || 110);
const WALL_MM = +(process.argv[3] || 2.5);
const CUT_MM = +(process.env.CUT_MM || 3.0);   // opening rim height above the bed (bigger = bigger opening)
const MIN_CAVITY_MM = 3.0;                     // cavity thinner than this radius is left solid (keeps legs/ears/paws solid)
const RIM_MM = 1.5;                            // flat rim width beyond the wall around the opening
const STEP = +(process.env.STEP || 0.0125);
const tag = `${LENGTH_MM}mm`;

const model = loadModel(dir);
const grid = makeGrid([-1.15, -0.45, -1.9], [1.15, 1.68, 1.62], STEP);

// ---- 1. outer shape and scale ----
const outer = sample(grid, model.printSDF);
let zLo = Infinity, zHi = -Infinity;
for (let k = 0; k <= grid.n[2]; k++) for (let j = 0; j <= grid.n[1]; j++) for (let i = 0; i <= grid.n[0]; i++)
  if (outer[grid.at(i, j, k)] < 0) { const z = grid.min[2] + k * STEP; zLo = Math.min(zLo, z); zHi = Math.max(zHi, z); }
const mm = LENGTH_MM / (zHi - zLo + STEP);           // mm per model unit
const t = WALL_MM / mm, r = MIN_CAVITY_MM / mm;
const CUT_Y = FLOOR_Y + CUT_MM / mm;

// ---- 2. cavity ----
// depth = distance to the outside of the body, with the cross-section at CUT_Y extruded straight down so the
// cavity runs out through the underside with vertical walls. core = deeper than t + r. cavity = core grown by r
// (a morphological opening): narrow parts (legs, ears, paws) never reach the core, so they stay solid.
const footAt = (x, y, z) => model.modelSDF(x, Math.max(y, CUT_Y), z);
const foot = sample(grid, footAt);
const inBody = new Uint8Array(grid.size);
for (let q = 0; q < grid.size; q++) inBody[q] = foot[q] < 0 ? 1 : 0;
const depth = distanceToOutside(grid, inBody);
const notCore = new Uint8Array(grid.size);
for (let q = 0; q < grid.size; q++) notCore[q] = depth[q] - STEP / 2 > t + r ? 0 : 1;
const toCore = distanceToOutside(grid, notCore);
const toCoreAt = lookup(grid, toCore);
const cavityOut = (x, y, z) => r - toCoreAt(x, y, z); // > 0 inside the cavity

// ---- 3. opening outline at the rim height (2D signed distance, negative inside) ----
const g2 = makeGrid([grid.min[0], CUT_Y, grid.min[2]], [-grid.min[0], CUT_Y, 1.62], STEP / 2);
const open2 = new Uint8Array(g2.size), closed2 = new Uint8Array(g2.size);
for (let k = 0; k <= g2.n[2]; k++) for (let i = 0; i <= g2.n[0]; i++) {
  const q = g2.at(i, 0, k), v = cavityOut(g2.min[0] + i * g2.step, CUT_Y, g2.min[2] + k * g2.step) > 0;
  open2[q] = v ? 1 : 0; closed2[q] = v ? 0 : 1;
}
const dIn = distanceToOutside(g2, open2), dOut = distanceToOutside(g2, closed2), sd2 = new Float32Array(g2.size);
for (let q = 0; q < g2.size; q++) sd2[q] = open2[q] ? -(dIn[q] - g2.step / 2) : dOut[q] - g2.step / 2;
const sd2At = lookup(g2, sd2);
const opening = (x, z) => sd2At(x, CUT_Y, z);
const rimZone = (x, z) => opening(x, z) < t + RIM_MM / mm;   // the only place the underside is trimmed flat

let oMin = [Infinity, Infinity], oMax = [-Infinity, -Infinity];
for (let k = 0; k <= g2.n[2]; k++) for (let i = 0; i <= g2.n[0]; i++) if (open2[g2.at(i, 0, k)]) {
  const x = g2.min[0] + i * g2.step, z = g2.min[2] + k * g2.step;
  oMin = [Math.min(oMin[0], x), Math.min(oMin[1], z)]; oMax = [Math.max(oMax[0], x), Math.max(oMax[1], z)];
}
const openingMM = [(oMax[0] - oMin[0]) * mm, (oMax[1] - oMin[1]) * mm].map((v) => +v.toFixed(1));

// ---- 4. shell = outer - cavity - (underside below the rim height, inside the rim zone only) ----
const shellField = (x, y, z) => Math.max(model.printSDF(x, y, z), cavityOut(x, y, z), rimZone(x, z) ? CUT_Y - y : -1);
const shellVal = new Float32Array(grid.size);
for (let k = 0; k <= grid.n[2]; k++) for (let j = 0; j <= grid.n[1]; j++) for (let i = 0; i <= grid.n[0]; i++) {
  const q = grid.at(i, j, k), x = grid.min[0] + i * STEP, y = grid.min[1] + j * STEP, z = grid.min[2] + k * STEP;
  shellVal[q] = Math.max(outer[q], r - toCore[q], rimZone(x, z) ? CUT_Y - y : -1);
}
const shell = surfaceNets(grid, shellVal, shellField, 2);

// ---- 5. section image (x = 0) for checking the wall: dark = shell, white = air ----
if (process.env.SECTION_OUT) {
  const { deflateSync, crc32 } = await import('node:zlib');
  const res = 0.2 / mm, y0 = FLOOR_Y - 2 / mm, W = Math.ceil((1.62 - grid.min[2]) / res), H = Math.ceil((1.68 - y0) / res);
  const raw = Buffer.alloc((W * 3 + 1) * H);
  for (let yy = 0; yy < H; yy++) for (let xx = 0; xx < W; xx++) {
    const y = 1.68 - yy * res, z = 1.62 - xx * res;      // front of the cat on the left
    raw.set(shellField(0, y, z) < 0 ? [70, 72, 80] : [250, 250, 252], yy * (W * 3 + 1) + 1 + xx * 3);
  }
  const chunk = (type, data) => { const len = Buffer.alloc(4); len.writeUInt32BE(data.length); const td = Buffer.concat([Buffer.from(type), data]); const crc = Buffer.alloc(4); crc.writeUInt32BE(crc32(td)); return Buffer.concat([len, td, crc]); };
  const ihdr = Buffer.alloc(13); ihdr.writeUInt32BE(W, 0); ihdr.writeUInt32BE(H, 4); ihdr[8] = 8; ihdr[9] = 2;
  (await import('node:fs')).writeFileSync(process.env.SECTION_OUT, Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk('IHDR', ihdr), chunk('IDAT', deflateSync(raw)), chunk('IEND', Buffer.alloc(0))]));
}

// ---- 6. write (mm, Z up, original bed line on Z = 0) ----
let lo = [Infinity, Infinity, Infinity], hi = [-Infinity, -Infinity, -Infinity];
for (let q = 0; q < shell.pos.length; q += 3) for (let d = 0; d < 3; d++) { lo[d] = Math.min(lo[d], shell.pos[q + d]); hi[d] = Math.max(hi[d], shell.pos[q + d]); }
const P = toPrint(shell.pos, mm, [(lo[0] + hi[0]) / 2, -(lo[2] + hi[2]) / 2, lo[1]]);
const { badAt, ...rep } = checkAndOrient(P, shell.tris);
if (process.env.DEBUG_BAD) console.error('non-manifold at (mm):', JSON.stringify(badAt.slice(0, 40)));
writeSTL(path.join(dir, `ppomo-shell-${tag}.stl`), P, shell.tris, `Ppomo hollow shell ${tag} (mm, Z up)`);
console.log(JSON.stringify({ lengthMM: LENGTH_MM, wallMM: WALL_MM, openingMM, rimHeightMM: CUT_MM, shell: rep }, null, 1));
