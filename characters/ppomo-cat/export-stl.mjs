// Export the Ppomo cat as a solid, watertight, print-ready binary STL (mm, Z up, flat bottom on Z = 0).
// Usage: node export-stl.mjs [lengthMM=90] [gridStep=0.0122] [out=ppomo-cat.stl]
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { loadModel, makeGrid, sample, surfaceNets, toPrint, checkAndOrient, writeSTL } from './stl-lib.mjs';

const dir = path.dirname(fileURLToPath(import.meta.url));
const LENGTH_MM = +(process.argv[2] || 90);
const STEP = +(process.argv[3] || 0.0122);   // 0.0122 gives 0 open / 0 non-manifold edges
const OUT = path.resolve(dir, process.argv[4] || 'ppomo-cat.stl');

const model = loadModel(dir);
const grid = makeGrid([-1.1, -0.02, -1.85], [1.1, 1.66, 1.6], STEP);
const { pos, tris } = surfaceNets(grid, sample(grid, model.printSDF), model.printSDF);

// size from the mesh: print length runs along model z
let lo = [Infinity, Infinity, Infinity], hi = [-Infinity, -Infinity, -Infinity];
for (let q = 0; q < pos.length; q += 3) for (let d = 0; d < 3; d++) { lo[d] = Math.min(lo[d], pos[q + d]); hi[d] = Math.max(hi[d], pos[q + d]); }
const mm = LENGTH_MM / (hi[2] - lo[2]);
const P = toPrint(pos, mm, [(lo[0] + hi[0]) / 2, -(lo[2] + hi[2]) / 2, lo[1]]);
const { badAt, ...report } = checkAndOrient(P, tris);
writeSTL(OUT, P, tris, 'Ppomo cat - print STL (mm, Z up)');
console.log(JSON.stringify({ out: path.basename(OUT), ...report,
  eyeDimpleMM: +(model.face.EYE_DEPTH * mm).toFixed(2), mouthGrooveWidthMM: +(2 * model.face.mouthTube * mm).toFixed(2) }));
