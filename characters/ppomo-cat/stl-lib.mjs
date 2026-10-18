// Shared helpers for the Ppomo print exports (export-stl.mjs, export-shell.mjs).
// The shape is read straight from the page (ppomo-cat-3d.html or ppomo-sit-3d.html) so prints always match the web preview.
import { readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';

export const FLOOR_Y = 0.035;   // flat bottom plane in model units (see modelSDF in the page)
export const smin = (a, b, k) => { const h = Math.max(k - Math.abs(a - b), 0) / k; return Math.min(a, b) - h * h * k * 0.25; };
export const smax = (a, b, k) => -smin(-a, -b, k);

// ---- model ----
export function loadModel(dir, file = 'ppomo-cat-3d.html') {
  const html = readFileSync(path.join(dir, file), 'utf8');
  const grab = (start, end) => { const a = html.indexOf(start); const b = html.indexOf(end, a); if (a < 0 || b < 0) throw new Error(`missing ${start}`); return html.slice(a, b); };
  const shapeSrc = grab('const SHAPE = {', '\nconst PAL');
  const fieldSrc = grab('const SCALE = {', '// ---------- surface extraction');
  const floorLine = 'return smax(d, -(y - 0.035), BLEND.floor);';
  if (!fieldSrc.includes(floorLine)) throw new Error('floor line not found in modelSDF');
  const { SHAPE, BLEND, modelSDF, bodySDF } = Function(
    `${shapeSrc}\n${fieldSrc}\n` +
    `const bodySDF = ${fieldSrc.slice(fieldSrc.indexOf('function modelSDF')).split('\n}')[0].replace('function modelSDF', 'function').replace(floorLine, 'return d;')}\n}\n` +
    'return { SHAPE, BLEND, modelSDF, bodySDF };')();

  // face: eyes and mouth carved in as shallow grooves (printable, easy to paint)
  const frontZ = (x, y) => { let z = 3; while (z > -3 && modelSDF(x, y, z) > 0) z -= 0.002; return z; };
  const EYE_R = 0.05, EYE_DEPTH = 0.025;
  const eyes = [-1, 1].map((s) => { const x = SHAPE.eye.x * s, y = SHAPE.eye.y; return { x, y, z: frontZ(x, y) + EYE_R - EYE_DEPTH }; });
  const M = { R: 0.034, tube: 0.017, y: SHAPE.mouth.y + 0.006 };
  M.z = frontZ(0, M.y);
  const arcs = [-1, 1].map((s) => ({ x: s * M.R, y: M.y }));
  const mouthSDF = (x, y, z) => {                                   // two lower half-circle grooves = ω
    let d = Infinity;
    for (const c of arcs) {
      const qx = x - c.x, qy = y - c.y, dz = z - M.z;
      const dd = qy <= 0 ? Math.hypot(Math.hypot(qx, qy) - M.R, dz) : Math.hypot(Math.abs(qx) - M.R, qy, dz);
      d = Math.min(d, dd - M.tube);
    }
    return d;
  };
  const carveFace = (d, x, y, z) => {
    for (const e of eyes) d = smax(d, -(Math.hypot(x - e.x, y - e.y, z - e.z) - EYE_R), 0.008);
    return Math.max(d, -mouthSDF(x, y, z));
  };
  const printSDF = (x, y, z) => carveFace(modelSDF(x, y, z), x, y, z);
  return { SHAPE, BLEND, modelSDF, bodySDF, carveFace, printSDF, face: { EYE_DEPTH, mouthTube: M.tube } };
}

// ---- grid ----
export function makeGrid(min, max, step) {
  const n = [0, 1, 2].map((a) => Math.ceil((max[a] - min[a]) / step));
  const sx = n[0] + 1, sxy = (n[0] + 1) * (n[1] + 1);
  return { min, step, n, sx, sxy, size: sxy * (n[2] + 1), at: (i, j, k) => i + sx * j + sxy * k };
}
export function sample(grid, f) {
  const v = new Float32Array(grid.size), { min, step, n } = grid;
  for (let k = 0; k <= n[2]; k++) for (let j = 0; j <= n[1]; j++) for (let i = 0; i <= n[0]; i++)
    v[grid.at(i, j, k)] = f(min[0] + i * step, min[1] + j * step, min[2] + k * step);
  return v;
}
// trilinear lookup of a sampled grid field
export function lookup(grid, val) {
  const { min, step, n } = grid;
  return (x, y, z) => {
    const fx = Math.min(Math.max((x - min[0]) / step, 0), n[0] - 1e-6), fy = Math.min(Math.max((y - min[1]) / step, 0), n[1] - 1e-6), fz = Math.min(Math.max((z - min[2]) / step, 0), n[2] - 1e-6);
    const i = Math.floor(fx), j = Math.floor(fy), k = Math.floor(fz), u = fx - i, v = fy - j, w = fz - k;
    const g = (a, b, c) => val[grid.at(i + a, j + b, k + c)];
    return (((g(0, 0, 0) * (1 - u) + g(1, 0, 0) * u) * (1 - v) + (g(0, 1, 0) * (1 - u) + g(1, 1, 0) * u) * v) * (1 - w)
      + ((g(0, 0, 1) * (1 - u) + g(1, 0, 1) * u) * (1 - v) + (g(0, 1, 1) * (1 - u) + g(1, 1, 1) * u) * v) * w);
  };
}

// exact Euclidean distance (in model units) from every grid point to the nearest grid point where inside[] is false
export function distanceToOutside(grid, inside) {
  const { n } = grid, d = new Float64Array(grid.size);
  const maxN = Math.max(...n) + 1, BIG = 4 * maxN * maxN;     // finite "no outside on this line" value keeps the math exact
  const f = new Float64Array(maxN), out = new Float64Array(maxN), v = new Int32Array(maxN), zz = new Float64Array(maxN + 1);
  // pass 1 (x lines): exact 1D squared distance with two sweeps
  for (let k = 0; k <= n[2]; k++) for (let j = 0; j <= n[1]; j++) {
    let last = -1e9;
    for (let i = 0; i <= n[0]; i++) { const q = grid.at(i, j, k); if (!inside[q]) last = i; d[q] = last < -1e8 ? BIG : (i - last) * (i - last); }
    last = 1e9;
    for (let i = n[0]; i >= 0; i--) { const q = grid.at(i, j, k); if (!inside[q]) last = i; if (last < 1e8) d[q] = Math.min(d[q], (last - i) * (last - i)); }
  }
  // passes 2, 3 (y, z lines): Felzenszwalb & Huttenlocher lower envelope of parabolas
  const edt1d = (len) => {
    let k = 0; v[0] = 0; zz[0] = -Infinity; zz[1] = Infinity;
    for (let q = 1; q < len; q++) {
      let s = ((f[q] + q * q) - (f[v[k]] + v[k] * v[k])) / (2 * q - 2 * v[k]);
      while (s <= zz[k]) { k--; s = ((f[q] + q * q) - (f[v[k]] + v[k] * v[k])) / (2 * q - 2 * v[k]); }
      k++; v[k] = q; zz[k] = s; zz[k + 1] = Infinity;
    }
    k = 0;
    for (let q = 0; q < len; q++) { while (zz[k + 1] < q) k++; out[q] = (q - v[k]) * (q - v[k]) + f[v[k]]; }
  };
  const passes = [[n[0] + 1, n[2] + 1, n[1] + 1, (a, b, c) => grid.at(a, c, b)], [n[0] + 1, n[1] + 1, n[2] + 1, (a, b, c) => grid.at(a, b, c)]];
  for (const [A, B, len, idx] of passes) for (let a = 0; a < A; a++) for (let b = 0; b < B; b++) {
    for (let c = 0; c < len; c++) f[c] = d[idx(a, b, c)];
    edt1d(len);
    for (let c = 0; c < len; c++) d[idx(a, b, c)] = out[c];
  }
  const res = new Float32Array(grid.size);
  for (let q = 0; q < grid.size; q++) res[q] = Math.sqrt(d[q]) * grid.step;
  return res;
}

// ---- surface nets + projection onto the field ----
export function surfaceNets(grid, val, field, projectIters = 3) {
  const { min, step, n, sx, sxy } = grid, [nx, ny, nz] = n;
  const cellV = new Int32Array(nx * ny * nz).fill(-1), cellIdx = (i, j, k) => i + nx * (j + ny * k);
  const pos = [], EDGES = [];
  for (let a = 0; a < 8; a++) for (const bit of [1, 2, 4]) if (!(a & bit)) EDGES.push([a, a | bit]);
  const cv = new Float32Array(8);
  for (let k = 0; k < nz; k++) for (let j = 0; j < ny; j++) for (let i = 0; i < nx; i++) {
    let mask = 0;
    for (let c = 0; c < 8; c++) { const v = val[(i + (c & 1)) + sx * (j + ((c >> 1) & 1)) + sxy * (k + ((c >> 2) & 1))]; cv[c] = v; if (v < 0) mask |= 1 << c; }
    if (mask === 0 || mask === 255) continue;
    let px = 0, py = 0, pz = 0, m = 0;
    for (const [a, b] of EDGES) {
      if ((cv[a] < 0) === (cv[b] < 0)) continue;
      const t = cv[a] / (cv[a] - cv[b]);
      px += (a & 1) + t * ((b & 1) - (a & 1)); py += ((a >> 1) & 1) + t * (((b >> 1) & 1) - ((a >> 1) & 1)); pz += ((a >> 2) & 1) + t * (((b >> 2) & 1) - ((a >> 2) & 1)); m++;
    }
    cellV[cellIdx(i, j, k)] = pos.length / 3;
    pos.push(min[0] + (i + px / m) * step, min[1] + (j + py / m) * step, min[2] + (k + pz / m) * step);
  }
  const tris = [];
  for (let k = 0; k <= nz; k++) for (let j = 0; j <= ny; j++) for (let i = 0; i <= nx; i++) {
    const g = [i, j, k], v0 = val[i + sx * j + sxy * k];
    for (let ax = 0; ax < 3; ax++) {
      const u = (ax + 1) % 3, w = (ax + 2) % 3;
      if (g[ax] >= n[ax] || g[u] < 1 || g[w] < 1 || g[u] >= n[u] || g[w] >= n[w]) continue;
      const g2 = g.slice(); g2[ax]++;
      if ((v0 < 0) === (val[g2[0] + sx * g2[1] + sxy * g2[2]] < 0)) continue;
      const cell = (du, dw) => { const c = g.slice(); c[u] -= du; c[w] -= dw; return cellV[cellIdx(c[0], c[1], c[2])]; };
      const a = cell(1, 1), b = cell(0, 1), c = cell(0, 0), d = cell(1, 0);
      if (v0 < 0) tris.push(a, b, c, a, c, d); else tris.push(a, c, b, a, d, c);
    }
  }
  if (field && projectIters) {
    const e = step * 0.25;
    for (let q = 0; q < pos.length; q += 3) {
      let x = pos[q], y = pos[q + 1], z = pos[q + 2];
      const x0 = x, y0 = y, z0 = z;
      for (let it = 0; it < projectIters; it++) {
        const d = field(x, y, z);
        let gx = field(x + e, y, z) - field(x - e, y, z), gy = field(x, y + e, z) - field(x, y - e, z), gz = field(x, y, z + e) - field(x, y, z - e);
        const gl = Math.hypot(gx, gy, gz) || 1; gx /= gl; gy /= gl; gz /= gl;
        x -= d * gx; y -= d * gy; z -= d * gz;
      }
      if (Math.hypot(x - x0, y - y0, z - z0) < step) { pos[q] = x; pos[q + 1] = y; pos[q + 2] = z; }   // never jump to another surface
    }
  }
  return { pos, tris };
}

// ---- print space: (x, y, z)_model -> (x, -z, y) mm, a proper rotation (keeps winding) ----
export function toPrint(pos, mmPerUnit, origin) {
  const P = new Float64Array(pos.length);
  for (let q = 0; q < pos.length; q += 3) {
    P[q] = (pos[q] - origin[0]) * mmPerUnit;
    P[q + 1] = (-pos[q + 2] - origin[1]) * mmPerUnit;
    P[q + 2] = (pos[q + 1] - origin[2]) * mmPerUnit;
  }
  return P;
}

export function checkAndOrient(P, tris) {
  const edgeCount = new Map(), key = (a, b) => (a < b ? a * 8388608 + b : b * 8388608 + a);
  let vol = 0;
  for (let t = 0; t < tris.length; t += 3) {
    const a = tris[t], b = tris[t + 1], c = tris[t + 2];
    for (const [p, q] of [[a, b], [b, c], [c, a]]) { const kk = key(p, q); edgeCount.set(kk, (edgeCount.get(kk) || 0) + 1); }
    const ax = P[a * 3], ay = P[a * 3 + 1], az = P[a * 3 + 2], bx = P[b * 3], by = P[b * 3 + 1], bz = P[b * 3 + 2], cx = P[c * 3], cy = P[c * 3 + 1], cz = P[c * 3 + 2];
    vol += (ax * (by * cz - bz * cy) - ay * (bx * cz - bz * cx) + az * (bx * cy - by * cx)) / 6;
  }
  let open = 0, nonManifold = 0;
  const badAt = [];
  for (const [kk, c] of edgeCount) {
    if (c === 1) open++;
    else if (c > 2) { nonManifold++; if (badAt.length < 400) { const a = Math.floor(kk / 8388608); badAt.push([P[a * 3], P[a * 3 + 1], P[a * 3 + 2]].map((v) => +v.toFixed(1))); } }
  }
  if (vol < 0) for (let t = 0; t < tris.length; t += 3) { const tmp = tris[t + 1]; tris[t + 1] = tris[t + 2]; tris[t + 2] = tmp; }
  let lo = [Infinity, Infinity, Infinity], hi = [-Infinity, -Infinity, -Infinity];
  for (let q = 0; q < P.length; q += 3) for (let d = 0; d < 3; d++) { lo[d] = Math.min(lo[d], P[q + d]); hi[d] = Math.max(hi[d], P[q + d]); }
  return { badAt, triangles: tris.length / 3, openEdges: open, nonManifoldEdges: nonManifold, volumeCm3: +(Math.abs(vol) / 1000).toFixed(1), sizeMM: hi.map((h, d) => +(h - lo[d]).toFixed(1)) };
}

export function writeSTL(file, P, tris, header) {
  const nt = tris.length / 3, buf = Buffer.alloc(84 + nt * 50);
  buf.write(header.slice(0, 79), 0, 'ascii');
  buf.writeUInt32LE(nt, 80);
  let o = 84;
  for (let t = 0; t < tris.length; t += 3) {
    const a = tris[t] * 3, b = tris[t + 1] * 3, c = tris[t + 2] * 3;
    const ux = P[b] - P[a], uy = P[b + 1] - P[a + 1], uz = P[b + 2] - P[a + 2], vx = P[c] - P[a], vy = P[c + 1] - P[a + 1], vz = P[c + 2] - P[a + 2];
    const fx = uy * vz - uz * vy, fy = uz * vx - ux * vz, fz = ux * vy - uy * vx, fl = Math.hypot(fx, fy, fz) || 1;
    for (const f of [fx / fl, fy / fl, fz / fl]) { buf.writeFloatLE(f, o); o += 4; }
    for (const idx of [a, b, c]) for (let d = 0; d < 3; d++) { buf.writeFloatLE(P[idx + d], o); o += 4; }
    buf.writeUInt16LE(0, o); o += 2;
  }
  writeFileSync(file, buf);
}
