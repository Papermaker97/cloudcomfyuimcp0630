// Origami crane folding engine: rigid facets, keyframed folds, layer ordering.
// Paper coords: square [-1,1]^2. World ("table") coords: paper lies in z=0 plane when flat, viewer at +z.
(function (root) {
  const PI = Math.PI, S2 = Math.SQRT2, K = S2 - 1; // K = 0.4142

  // ---------- vector / transform math ----------
  const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
  const add = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
  const mul = (a, s) => [a[0] * s, a[1] * s, a[2] * s];
  const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
  const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
  const len = a => Math.hypot(a[0], a[1], a[2]);
  const norm = a => mul(a, 1 / len(a));
  const I = () => ({ R: [1, 0, 0, 0, 1, 0, 0, 0, 1], t: [0, 0, 0] });
  const applyR = (R, p) => [R[0] * p[0] + R[1] * p[1] + R[2] * p[2], R[3] * p[0] + R[4] * p[1] + R[5] * p[2], R[6] * p[0] + R[7] * p[1] + R[8] * p[2]];
  const apply = (T, p) => add(applyR(T.R, p), T.t);
  const matmul = (A, B) => {
    const C = new Array(9);
    for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) C[i * 3 + j] = A[i * 3] * B[j] + A[i * 3 + 1] * B[3 + j] + A[i * 3 + 2] * B[6 + j];
    return C;
  };
  const transpose = R => [R[0], R[3], R[6], R[1], R[4], R[7], R[2], R[5], R[8]];
  const compose = (A, B) => ({ R: matmul(A.R, B.R), t: add(applyR(A.R, B.t), A.t) });
  const inverse = T => { const Rt = transpose(T.R); return { R: Rt, t: mul(applyR(Rt, T.t), -1) }; };
  function rodrigues(d, a) {
    const c = Math.cos(a), s = Math.sin(a), v = 1 - c, [x, y, z] = d;
    return [c + x * x * v, x * y * v - z * s, x * z * v + y * s,
      y * x * v + z * s, c + y * y * v, y * z * v - x * s,
      z * x * v - y * s, z * y * v + x * s, c + z * z * v];
  }
  function rotAxis(P, d, a) { const R = rodrigues(d, a); return { R, t: sub(P, applyR(R, P)) }; }
  function frameFrom(a, b, c, A, B, C) { // rigid map taking paper pts a,b,c (3D) to world A,B,C
    const f = (p, q, r) => { const e1 = norm(sub(q, p)); let w = sub(r, p); w = norm(sub(w, mul(e1, dot(w, e1)))); return [e1, w, cross(e1, w)]; };
    const [e1, e2, e3] = f(a, b, c), [E1, E2, E3] = f(A, B, C);
    const M = [E1[0], E2[0], E3[0], E1[1], E2[1], E3[1], E1[2], E2[2], E3[2]];
    const m = [e1[0], e1[1], e1[2], e2[0], e2[1], e2[2], e3[0], e3[1], e3[2]];
    const R = matmul(M, m);
    return { R, t: sub(A, applyR(R, a)) };
  }
  function matToQuat(R) {
    const tr = R[0] + R[4] + R[8]; let w, x, y, z;
    if (tr > 0) { const s = Math.sqrt(tr + 1) * 2; w = s / 4; x = (R[7] - R[5]) / s; y = (R[2] - R[6]) / s; z = (R[3] - R[1]) / s; }
    else if (R[0] > R[4] && R[0] > R[8]) { const s = Math.sqrt(1 + R[0] - R[4] - R[8]) * 2; w = (R[7] - R[5]) / s; x = s / 4; y = (R[1] + R[3]) / s; z = (R[2] + R[6]) / s; }
    else if (R[4] > R[8]) { const s = Math.sqrt(1 + R[4] - R[0] - R[8]) * 2; w = (R[2] - R[6]) / s; x = (R[1] + R[3]) / s; y = s / 4; z = (R[5] + R[7]) / s; }
    else { const s = Math.sqrt(1 + R[8] - R[0] - R[4]) * 2; w = (R[3] - R[1]) / s; x = (R[2] + R[6]) / s; y = (R[5] + R[7]) / s; z = s / 4; }
    return [w, x, y, z];
  }
  function quatToMat([w, x, y, z]) {
    return [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w),
      2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w),
      2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)];
  }
  function slerpI(T, s) { // interpolate from identity to T
    let q = matToQuat(T.R); if (q[0] < 0) q = q.map(v => -v);
    const ang = 2 * Math.acos(Math.min(1, q[0])), sn = Math.sin(ang / 2);
    if (sn < 1e-9) return { R: I().R, t: mul(T.t, s) };
    const ax = [q[1] / sn, q[2] / sn, q[3] / sn];
    return { R: rodrigues(ax, ang * s), t: mul(T.t, s) };
  }

  // ---------- 2D polygon helpers ----------
  const area2 = P => { let a = 0; for (let i = 0; i < P.length; i++) { const p = P[i], q = P[(i + 1) % P.length]; a += p[0] * q[1] - q[0] * p[1]; } return a / 2; };
  const centroid2 = P => { let x = 0, y = 0; P.forEach(p => { x += p[0]; y += p[1]; }); return [x / P.length, y / P.length]; };
  function clipHalf(P, q, n) { // keep n.(p-q) >= 0
    const out = [], s = p => n[0] * (p[0] - q[0]) + n[1] * (p[1] - q[1]);
    for (let i = 0; i < P.length; i++) {
      const a = P[i], b = P[(i + 1) % P.length], sa = s(a), sb = s(b);
      if (sa >= 0) out.push(a);
      if ((sa >= 0) !== (sb >= 0)) { const t = sa / (sa - sb); out.push([a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t]); }
    }
    return dedupe(out);
  }
  function dedupe(P) {
    const o = [];
    P.forEach(p => { const l = o[o.length - 1]; if (!l || Math.hypot(l[0] - p[0], l[1] - p[1]) > 1e-9) o.push(p); });
    if (o.length > 1 && Math.hypot(o[0][0] - o[o.length - 1][0], o[0][1] - o[o.length - 1][1]) < 1e-9) o.pop();
    return o;
  }
  const ccw = P => area2(P) < 0 ? P.slice().reverse() : P;
  function intersectConvex(A, B) {
    let P = ccw(A); const Q = ccw(B);
    for (let i = 0; i < Q.length && P.length; i++) {
      const a = Q[i], b = Q[(i + 1) % Q.length];
      P = clipHalf(P, a, [-(b[1] - a[1]), b[0] - a[0]]);
    }
    return P;
  }
  function insideConvex(P, p, tol = 1e-9) {
    const Q = ccw(P);
    for (let i = 0; i < Q.length; i++) {
      const a = Q[i], b = Q[(i + 1) % Q.length];
      if ((b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) < -tol) return false;
    }
    return true;
  }

  // ---------- facets ----------
  let nextId = 1;
  const mkFacet = (poly, T, l) => ({ id: nextId++, poly, T, l: l || 0, h: 0 });
  const world = (f, p) => apply(f.T, [p[0], p[1], 0]);
  const tableProj = f => f.poly.map(p => { const w = world(f, p); return [w[0], w[1]]; });
  const toPaper = (f, P) => { const q = apply(inverse(f.T), [P[0], P[1], 0]); return [q[0], q[1]]; };

  function splitFacet(f, P, D) { // split by table line through P with dir D (2D); returns [f] or [a,b]
    const a = toPaper(f, P), b = toPaper(f, [P[0] + D[0], P[1] + D[1]]);
    const n = [-(b[1] - a[1]), b[0] - a[0]];
    const A = clipHalf(f.poly, a, n), B = clipHalf(f.poly, a, [-n[0], -n[1]]);
    if (A.length < 3 || B.length < 3 || Math.abs(area2(A)) < 1e-9 || Math.abs(area2(B)) < 1e-9) return [f];
    return [mkFacet(A, f.T, f.l), mkFacet(B, f.T, f.l)].map(g => (g.h = f.h, g));
  }
  function facetsAt(facets, pt) { // facets containing table pt, sorted top (high h/l) first
    return facets.filter(f => insideConvex(tableProj(f), pt, 1e-7)).sort((a, b) => (b.l - a.l));
  }
  // shared paper edge segments between two facets
  function sharedEdges(f, g) {
    const out = [];
    for (let i = 0; i < f.poly.length; i++) {
      const a = f.poly[i], b = f.poly[(i + 1) % f.poly.length];
      const d = [b[0] - a[0], b[1] - a[1]], L = Math.hypot(d[0], d[1]); if (L < 1e-9) continue;
      const u = [d[0] / L, d[1] / L];
      for (let j = 0; j < g.poly.length; j++) {
        const c = g.poly[j], e = g.poly[(j + 1) % g.poly.length];
        const dc = u[0] * (c[1] - a[1]) - u[1] * (c[0] - a[0]), de = u[0] * (e[1] - a[1]) - u[1] * (e[0] - a[0]);
        if (Math.abs(dc) > 1e-7 || Math.abs(de) > 1e-7) continue;
        const tc = u[0] * (c[0] - a[0]) + u[1] * (c[1] - a[1]), te = u[0] * (e[0] - a[0]) + u[1] * (e[1] - a[1]);
        const lo = Math.max(0, Math.min(tc, te)), hi = Math.min(L, Math.max(tc, te));
        if (hi - lo > 1e-7) out.push([[a[0] + u[0] * lo, a[1] + u[1] * lo], [a[0] + u[0] * hi, a[1] + u[1] * hi]]);
      }
    }
    return out;
  }
  // flood fill from seed through paper edges having a part strictly on the moving side
  function flood(facets, seed, sideFn, filter) {
    const set = new Set([seed]), q = [seed];
    while (q.length) {
      const f = q.pop();
      for (const g of facets) {
        if (set.has(g) || (filter && !filter(g))) continue;
        const sh = sharedEdges(f, g);
        if (sh.some(([a, b]) => {
          const pts = [a, b, [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2]];
          return Math.max(...pts.map(p => sideFn(world(f, p)))) > 1e-6;
        })) { set.add(g); q.push(g); }
      }
    }
    return set;
  }
  const lineSide = (P, D, M) => { // signed side fn, positive on side of M
    const s = p => D[0] * (p[1] - P[1]) - D[1] * (p[0] - P[0]);
    const sg = Math.sign(s(M)); return p => sg * s(p);
  };
  const paperCentroid = f => centroid2(f.poly);
  const quadOf = f => { const c = paperCentroid(f); return [Math.sign(c[0]), Math.sign(c[1])]; };

  // ---------- ordering & heights ----------
  function overlapPairs(facets, Tend) {
    const polys = facets.map((f, i) => ccw(f.poly.map(p => { const w = apply(Tend[i], [p[0], p[1], 0]); return [w[0], w[1]]; })));
    const bb = polys.map(P => { let a = [1e9, 1e9, -1e9, -1e9]; P.forEach(p => { a[0] = Math.min(a[0], p[0]); a[1] = Math.min(a[1], p[1]); a[2] = Math.max(a[2], p[0]); a[3] = Math.max(a[3], p[1]); }); return a; });
    const pairs = [];
    for (let i = 0; i < polys.length; i++) for (let j = i + 1; j < polys.length; j++) {
      const A = bb[i], B = bb[j];
      if (A[0] > B[2] - 1e-6 || B[0] > A[2] - 1e-6 || A[1] > B[3] - 1e-6 || B[1] > A[3] - 1e-6) continue;
      const X = intersectConvex(polys[i], polys[j]);
      if (X.length >= 3 && Math.abs(area2(X)) > 2e-6) pairs.push([i, j, centroid2(X)]);
    }
    return pairs;
  }
  function order(facets, T0, Tend, Tprobe, rule) {
    const n = facets.length, pairs = overlapPairs(facets, Tend), above = [];
    const flipped = i => Math.sign(Tend[i].R[8]) !== Math.sign(T0[i].R[8]);
    for (const [i, j, p] of pairs) {
      let r = rule ? rule(i, j) : 0; // +1: i above j
      if (!r) {
        const pi = apply(inverse(Tend[i]), [p[0], p[1], 0]), pj = apply(inverse(Tend[j]), [p[0], p[1], 0]);
        const zi = apply(Tprobe[i], pi)[2], zj = apply(Tprobe[j], pj)[2];
        if (Math.abs(zi - zj) > 1e-7) r = zi > zj ? 1 : -1;
        else { r = facets[i].l > facets[j].l ? 1 : -1; if (flipped(i) && flipped(j)) r = -r; }
      }
      above.push(r > 0 ? [j, i] : [i, j]); // [lower, upper]
    }
    // Kahn topological sort, stable by previous l
    const indeg = new Array(n).fill(0), out = Array.from({ length: n }, () => []);
    above.forEach(([lo, hi]) => { out[lo].push(hi); indeg[hi]++; });
    const L = new Array(n), done = new Array(n).fill(false);
    for (let k = 0; k < n; k++) {
      let best = -1;
      for (let i = 0; i < n; i++) if (!done[i] && indeg[i] === 0 && (best < 0 || facets[i].l < facets[best].l)) best = i;
      if (best < 0) { // cycle: break
        for (let i = 0; i < n; i++) if (!done[i] && (best < 0 || indeg[i] < indeg[best])) best = i;
        order.cycles = (order.cycles || 0) + 1;
      }
      done[best] = true; L[best] = k; out[best].forEach(h => indeg[h]--);
    }
    // heights: longest chain of overlapping facets beneath
    const H = new Array(n).fill(0), byL = [...Array(n).keys()].sort((a, b) => L[a] - L[b]);
    const nb = Array.from({ length: n }, () => []);
    pairs.forEach(([i, j]) => { nb[i].push(j); nb[j].push(i); });
    byL.forEach(i => { nb[i].forEach(j => { if (L[j] < L[i]) H[i] = Math.max(H[i], H[j] + 1); }); });
    return { L, H };
  }

  // ---------- timeline builder ----------
  function build() {
    nextId = 1;
    let facets = [mkFacet([[-1, -1], [1, -1], [1, 1], [-1, 1]], I(), 0)];
    const steps = []; api._steps = steps;
    const cur = () => facets;

    function commit(step, motion, opts = {}) {
      const T0 = facets.map(f => f.T);
      const Tend = motion(1);
      let L, H;
      if (opts.flat === false) { L = facets.map(f => f.l); H = facets.map(f => f.h); }
      else { const r = order(facets, T0, Tend, opts.probe ? opts.probe() : motion(0.985), opts.rule); L = r.L; H = r.H; }
      steps.push(Object.assign(step, {
        facets: facets.map(f => ({ id: f.id, poly: f.poly, T0: f.T, h0: f.h })),
        motion, Tend, h1: H, mode: opts.mode || 'flat'
      }));
      facets = facets.map((f, i) => Object.assign(mkFacet(f.poly, Tend[i], L[i]), { id: f.id, h: H[i] }));
    }
    const rotGroups = groups => { const F = facets; return s => F.map(f => {
      let T = f.T;
      for (const g of groups) if (g.ids.has(f.id)) T = compose(rotAxis(g.P, g.d, g.ang(s)), T);
      return T;
    }); };

    // simple fold through layers reached by flood
    function makeFold(fd) {
      const P = fd.line[0], D = [fd.line[1][0] - P[0], fd.line[1][1] - P[1]];
      const side = lineSide(P, D, fd.move);
      const at = facetsAt(facets, fd.seed);
      const seed = fd.seedBottom ? at[at.length - 1] : at[0];
      const fl = fd.all ? new Set(facets.filter(f => !fd.filter || fd.filter(f))) : flood(facets, seed, side, fd.filter);
      const moving = new Set();
      const next = [];
      for (const f of facets) {
        if (!fl.has(f)) { next.push(f); continue; }
        for (const g of splitFacet(f, P, D)) {
          next.push(g);
          const c = centroid2(tableProj(g));
          if (side(c) > 1e-7) moving.add(g.id);
        }
      }
      facets = next;
      const d3 = norm([D[0], D[1], 0]), P3 = [P[0], P[1], 0];
      const m3 = [fd.move[0], fd.move[1], 0];
      const sgn = apply(rotAxis(P3, d3, 0.1), m3)[2] * (fd.dir || 1) > 0 ? 1 : -1;
      return { ids: moving, P: P3, d: d3, a: sgn * (fd.angle || PI) };
    }
    function fold(step, folds, unfoldAfter) {
      const groups = folds.map(makeFold);
      if (unfoldAfter) {
        const bump = s => { const e = x => x * x * (3 - 2 * x), c = v => Math.max(0, Math.min(1, v)); return e(c(s / 0.42)) - e(c((s - 0.58) / 0.42)); };
        groups.forEach(g => { const a = g.a * 0.985; g.ang = s => a * bump(s); });
      } else groups.forEach(g => { const a = g.a; g.ang = s => a * s; });
      commit(step, rotGroups(groups));
      return groups;
    }
    function unfold(step, groups) {
      const gs = groups.map(g => ({ ids: g.ids, P: g.P, d: g.d, ang: s => -g.a * s }));
      commit(step, rotGroups(gs));
    }
    function turnOver(step) {
      const g = { ids: new Set(facets.map(f => f.id)), P: [0, 0, 0], d: [0, 1, 0], ang: s => PI * s };
      commit(step, rotGroups([g]));
    }

    // ---- 1. pre-creases ----
    fold({ title: '대각선으로 접었다 펴기', desc: '색면을 위로 두고, 아래 모서리를 위 모서리에 맞춰 삼각형으로 접은 뒤 다시 폅니다.' },
      [{ line: [[-1, 1], [1, -1]], move: [-1, -1], seed: [-0.5, -0.6], dir: 1 }], true);
    fold({ title: '반대쪽 대각선도 접었다 펴기', desc: '나머지 대각선도 같은 방법으로 접었다 펴면 X자 접힘선이 생깁니다.' },
      [{ line: [[-1, -1], [1, 1]], move: [1, -1], seed: [0.6, -0.5], dir: 1 }], true);
    turnOver({ title: '뒤집기', desc: '종이를 뒤집어 흰 면이 위로 오게 합니다.' });
    fold({ title: '가로로 반 접었다 펴기', desc: '아래 변을 위 변에 맞춰 반으로 접고 다시 폅니다.' },
      [{ line: [[-1, 0], [1, 0]], move: [0, -1], seed: [0.3, -0.5], dir: 1 }], true);
    fold({ title: '세로로 반 접었다 펴기', desc: '왼쪽 변을 오른쪽 변에 맞춰 접고 다시 폅니다. 이제 접힘선이 8갈래가 됩니다.' },
      [{ line: [[0, -1], [0, 1]], move: [-1, 0], seed: [-0.5, 0.3], dir: 1 }], true);
    turnOver({ title: '다시 뒤집기', desc: '색면이 위로 오게 뒤집습니다. 대각선은 골접기, 가로·세로선은 산접기가 됩니다.' });

    // ---- 2. collapse into preliminary (square) base ----
    {
      const info = facets.map(f => {
        const O = f.poly.find(p => Math.hypot(p[0], p[1]) < 1e-6);
        const M = f.poly.find(p => Math.abs(Math.hypot(p[0], p[1]) - 1) < 1e-6);
        const Dc = f.poly.find(p => Math.abs(Math.hypot(p[0], p[1]) - S2) < 1e-6);
        const aM = Math.atan2(M[1], M[0]), aD = Math.atan2(Dc[1], Dc[0]);
        const k = Math.round(((aM / (PI / 2)) % 4 + 4) % 4);
        return { O, M, D: Dc, aM, aD, fin: k };
      });
      const c45 = Math.SQRT1_2;
      const Lay = { R: [c45, c45, 0, 0, 0, 1, c45, -c45, 0], t: [0, S2, 0] };
      const ss = (a, b, s) => { const x = Math.max(0, Math.min(1, (s - a) / (b - a))); return x * x * (3 - 2 * x); };
      const F0 = facets;
      const conf = (ed, psi, lay) => F0.map((f, i) => {
        const q = info[i], cd = Math.cos(45 * PI / 180);
        const A = cd * Math.cos(ed), B = Math.sin(ed), R = Math.hypot(A, B);
        const em = Math.atan2(B, A) - Math.acos(Math.min(1, cd / R));
        const mh = [Math.cos(q.aM) * Math.cos(em), Math.sin(q.aM) * Math.cos(em), -Math.sin(em)];
        const dh = [Math.cos(q.aD) * Math.cos(ed), Math.sin(q.aD) * Math.cos(ed), -Math.sin(ed)];
        let T = frameFrom([0, 0, 0], [q.M[0], q.M[1], 0], [q.D[0], q.D[1], 0], [0, 0, 0], mh, mul(dh, S2));
        const sgn = (q.fin % 2 === 0) ? 1 : -1;
        T = compose(rotAxis([0, 0, 0], [0, 0, 1], sgn * psi), T);
        return compose(slerpI(Lay, lay), T);
      });
      const motion = s => conf(PI / 2 * ss(0, 0.55, s), PI / 4 * ss(0.4, 0.8, s), ss(0.55, 1, s));
      commit({ title: '접어 모아 정사각 기본형 만들기', desc: '접힘선을 따라 네 모서리를 한 점으로 모으고 납작하게 눌러 작은 정사각형(정사각 기본형)을 만듭니다. 트인 쪽이 아래로 오게 둡니다.' },
        motion, { probe: () => conf(PI / 2 - 0.05, PI / 4 - 0.05, 1) });
    }

    // geometry of the preliminary base: C=(0,√2) top, B=(0,0) open corners, sides at (±√2/2, √2/2)
    const KL = [-K, 1], KR = [K, 1], H = S2 / 2;
    const kiteFolds = () => [
      { line: [[0, 0], KL], move: [-H, H], seed: [-0.37, 0.57], dir: 1 },
      { line: [[0, 0], KR], move: [H, H], seed: [0.37, 0.57], dir: 1 }];

    function petal(step) {
      // split the top layer's middle along the horizontal crease y=1
      for (const x of [-0.1, 0.1]) {
        const f = facetsAt(facets, [x, 0.6])[0];
        const parts = splitFacet(f, [0, 1], [1, 0]);
        facets.splice(facets.indexOf(f), 1, ...parts);
      }
      const top = p => facetsAt(facets, p);
      const sides = [-1, 1].map(sx => {
        const Kp = [sx * K, 1, 0], Lp = [sx * H, H, 0], Bp = [0, 0, 0];
        const central = top([sx * 0.1, 0.6])[0];
        const st = top([sx * 0.37, 0.57]);
        const side1 = st[0], side2 = st[1];
        return { sx, Kp, Lp, Bp, central, side1, side2 };
      });
      const axC = [1, 0, 0], PC = [0, 1, 0];
      const sC = apply(rotAxis(PC, axC, 0.1), [0, 0, 0])[2] > 0 ? 1 : -1;
      const Bth = th => apply(rotAxis(PC, axC, sC * th), [0, 0, 0]);
      sides.forEach(sd => {
        sd.ax2 = norm(sub(sd.Bp, sd.Kp));
        sd.s2 = apply(rotAxis(sd.Kp, sd.ax2, 0.1), sd.Lp)[2] > 0 ? 1 : -1;
        sd.Lph = ph => apply(rotAxis(sd.Kp, sd.ax2, sd.s2 * ph), sd.Lp);
        const dBL = len(sub(sd.Bp, sd.Lp));
        const g = (th, ph) => len(sub(Bth(th), sd.Lph(ph))) - dBL;
        // track root phi(theta) from the far end (unique there) back to 0
        const N = 600, tab = new Array(N + 1);
        let prev = PI;
        for (let i = N; i >= 0; i--) {
          const th = PI * i / N, roots = [];
          const M = 1440;
          let pv = g(th, -0.02), px = -0.02;
          for (let k = 1; k <= M; k++) {
            const x = -0.02 + (PI + 0.04) * k / M, v = g(th, x);
            if (pv === 0) roots.push(px);
            else if (pv * v < 0) { let a = px, b = x, fa = pv; for (let it = 0; it < 50; it++) { const m = (a + b) / 2, fm = g(th, m); if (fa * fm <= 0) b = m; else { a = m; fa = fm; } } roots.push((a + b) / 2); }
            pv = v; px = x;
          }
          if (roots.length) prev = roots.reduce((a, b) => Math.abs(b - prev) < Math.abs(a - prev) ? b : a);
          tab[i] = prev;
        }
        tab[0] = 0; tab[N] = PI;
        sd.phi = th => { const x = th / PI * N, i = Math.max(0, Math.min(N - 1, Math.floor(x))), f = x - i; return tab[i] * (1 - f) + tab[i + 1] * f; };
        const inv = inverse(sd.side1.T);
        sd.pK = apply(inv, sd.Kp); sd.pB = apply(inv, sd.Bp); sd.pL = apply(inv, sd.Lp);
      });
      const FP = facets;
      const motion = s => {
        const th = PI * s;
        return FP.map(f => {
          for (const sd of sides) {
            if (f === sd.central) return compose(rotAxis(PC, axC, sC * th), f.T);
            if (f === sd.side2) return compose(rotAxis(sd.Kp, sd.ax2, sd.s2 * sd.phi(th)), f.T);
            if (f === sd.side1) return frameFrom(sd.pK, sd.pB, sd.pL, sd.Kp, Bth(th), sd.Lph(sd.phi(th)));
          }
          return f.T;
        });
      };
      commit(step, motion);
    }

    let g;
    g = fold({ title: '양옆을 중심선에 맞춰 접기', desc: '윗장의 아래쪽 두 변을 가운데 선에 맞춰 접어 연 모양을 만듭니다.' }, kiteFolds());
    unfold({ title: '다시 펴기', desc: '방금 접은 두 날개를 펴서 접힘선만 남깁니다.' }, g);
    petal({ title: '꽃잎 접기', desc: '윗장의 아래 꼭짓점을 들어 올리면 양옆이 접힘선을 따라 안으로 모입니다. 길쭉한 마름모가 생깁니다.' });
    turnOver({ title: '뒤집기', desc: '뒷면에서도 같은 과정을 반복합니다.' });
    g = fold({ title: '양옆을 중심선에 맞춰 접기', desc: '뒷면의 윗장도 아래 두 변을 가운데 선에 맞춰 접습니다.' }, kiteFolds());
    unfold({ title: '다시 펴기', desc: '접힘선만 남기고 폅니다.' }, g);
    petal({ title: '꽃잎 접기 (학 기본형 완성)', desc: '아래 꼭짓점을 들어 올려 꽃잎 접기를 하면 학 기본형이 완성됩니다.' });

    // ---- 3. narrow the legs ----
    const tn = Math.tan(PI / 16);
    const narrowFolds = () => [
      { line: [[0, 0], [-tn, 1]], move: [-0.3, 0.5], seed: [-0.18, 0.6], dir: 1 },
      { line: [[0, 0], [tn, 1]], move: [0.3, 0.5], seed: [0.18, 0.6], dir: 1 }];
    fold({ title: '아래쪽 다리를 가늘게 접기', desc: '윗장의 아래쪽 두 변을 가운데 선에 맞춰 접어 다리를 가늘게 만듭니다.' }, narrowFolds());
    turnOver({ title: '뒤집기', desc: '뒷면도 같은 방법으로 접습니다.' });
    fold({ title: '뒷면 다리도 가늘게 접기', desc: '아래쪽 두 변을 가운데 선에 맞춰 접습니다.' }, narrowFolds());

    // ---- 4. inside reverse folds ----
    const frontCorner = () => { const f = facetsAt(facets, [0, 1.8])[0]; const c = paperCentroid(f); return [Math.sign(c[0]), Math.sign(c[1])]; };
    function reverseFold(step, P, D, move, seedPt) {
      const fc = frontCorner();
      const front = f => { const c = paperCentroid(f); return c[0] * fc[0] + c[1] * fc[1] > 0; };
      const seed = facetsAt(facets, seedPt)[0];
      const q = quadOf(seed);
      const filter = f => { const c = quadOf(f); return c[0] === q[0] && c[1] === q[1]; };
      const side = lineSide(P, D, move);
      const fl = flood(facets, seed, side, filter);
      const moving = new Set(), next = [];
      for (const f of facets) {
        if (!fl.has(f)) { next.push(f); continue; }
        for (const gg of splitFacet(f, P, D)) { next.push(gg); if (side(centroid2(tableProj(gg))) > 1e-7) moving.add(gg.id); }
      }
      facets = next;
      const d3 = norm([D[0], D[1], 0]), P3 = [P[0], P[1], 0], m3 = [move[0], move[1], 0];
      const sg = apply(rotAxis(P3, d3, 0.1), m3)[2] > 0 ? 1 : -1;
      const isF = facets.map(f => front(f)), isM = facets.map(f => moving.has(f.id));
      const FR = facets;
      const motion = s => FR.map((f, i) => {
        if (!isM[i]) return f.T;
        // front layers swing behind, back layers swing forward: the tip turns inside out
        return compose(rotAxis(P3, d3, (isF[i] ? -1 : 1) * sg * PI * s), f.T);
      });
      const rule = (i, j) => {
        const mi = isM[i], mj = isM[j];
        if (!mi && !mj) return 0;
        if (mi && mj) {
          if (isF[i] !== isF[j]) return isF[i] ? 1 : -1;
          return facets[i].l > facets[j].l ? -1 : 1; // order reverses inside each half
        }
        const o = mi ? j : i, sgn = mi ? 1 : -1; // sgn: +1 if i is the moving one
        return (isF[o] ? -1 : 1) * sgn;
      };
      commit(step, motion, { rule });
    }
    const nA = [-0.9087, -0.4171];
    reverseFold({ title: '목 만들기 (안으로 뒤집어 접기)', desc: '왼쪽 다리를 두 겹 사이로 뒤집어 넣으며 위로 올립니다.' }, [0, 1], nA, [-0.05, 0.3], [-0.05, 0.5]);
    reverseFold({ title: '꼬리 만들기 (안으로 뒤집어 접기)', desc: '오른쪽 다리도 같은 방법으로 위로 올려 꼬리를 만듭니다.' }, [0, 1], [-nA[0], nA[1]], [0.05, 0.3], [0.05, 0.5]);
    {
      const M0 = [-0.0915, 0.958], tipP = [-0.758, 1.652];
      const L0 = Math.hypot(tipP[0] - M0[0], tipP[1] - M0[1]);
      const a = [(tipP[0] - M0[0]) / L0, (tipP[1] - M0[1]) / L0], b = [-0.906, -0.423];
      const m = norm([a[0] + b[0], a[1] + b[1], 0]);
      const at = f => [M0[0] + f * L0 * a[0], M0[1] + f * L0 * a[1]];
      reverseFold({ title: '머리 만들기', desc: '목 끝을 조금 남기고 안으로 뒤집어 접어 부리를 만듭니다.' }, at(0.8), [m[0], m[1]], at(0.97), at(0.88));
    }

    // ---- 5. wings ----
    {
      const fc = frontCorner(), bc = [-fc[0], -fc[1]];
      const inWing = (f, c) => { const p = paperCentroid(f); return Math.sign(p[0]) === c[0] && Math.sign(p[1]) === c[1] && (p[0] * c[0] + p[1] * c[1]) > 2 - S2 + 1e-6; };
      const fw = new Set(facets.filter(f => inWing(f, fc)).map(f => f.id));
      const bw = new Set(facets.filter(f => inWing(f, bc)).map(f => f.id));
      const P = [0, 1, 0], d = [1, 0, 0];
      const sF = apply(rotAxis(P, d, 0.1), [0, 1.8, 0])[2] > 0 ? 1 : -1;
      commit({ title: '날개 내리기', desc: '앞 날개는 앞으로, 뒤 날개는 뒤로 접어 내립니다.' },
        rotGroups([{ ids: fw, P, d, ang: s => sF * PI * s }, { ids: bw, P, d, ang: s => -sF * PI * s }]));
      const ss = (a, b, s) => { const x = Math.max(0, Math.min(1, (s - a) / (b - a))); return x * x * (3 - 2 * x); };
      let wOpen = 0;
      const openR = rotGroups([{ ids: fw, P, d, ang: () => -sF * PI * 0.5 * wOpen }, { ids: bw, P, d, ang: () => sF * PI * 0.5 * wOpen }]);
      const open = s => { wOpen = ss(0, 0.75, s); return openR(s); };
      commit({ title: '날개를 펼쳐 완성', desc: '날개를 수평으로 펼치면 종이학이 완성됩니다. 드래그해서 돌려 보세요.' }, open, { flat: false, mode: '3d' });
      steps[steps.length - 1].wings = { fw, bw };
    }
    return steps;
  }

  var api = { build, apply, compose, rotAxis, I, order };
  if (typeof module !== 'undefined') module.exports = api; else root.CraneEngine = api;
})(this);
