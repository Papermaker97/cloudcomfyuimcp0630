// Paper-crane pose rig: chains of paper segments hinged at bend cuts and creases, IK, and motion timelines.
(function (root) {
  const D2R = Math.PI / 180;
  const sub2 = (a, b) => [a[0] - b[0], a[1] - b[1]];
  const dot2 = (a, b) => a[0] * b[0] + a[1] * b[1];
  const nrm2 = a => { const l = Math.hypot(a[0], a[1]); return [a[0] / l, a[1] / l]; };
  const crossZ = (a, b) => a[0] * b[1] - a[1] * b[0];
  const clone = o => JSON.parse(JSON.stringify(o));

  function clipHalf(P, q, n) {
    const out = [], s = p => n[0] * (p[0] - q[0]) + n[1] * (p[1] - q[1]);
    for (let i = 0; i < P.length; i++) {
      const a = P[i], b = P[(i + 1) % P.length], sa = s(a), sb = s(b);
      if (sa >= 0) out.push(a);
      if ((sa >= 0) !== (sb >= 0)) { const t = sa / (sa - sb); out.push([a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t]); }
    }
    const o = [];
    out.forEach(p => { const l = o[o.length - 1]; if (!l || Math.hypot(l[0] - p[0], l[1] - p[1]) > 1e-9) o.push(p); });
    if (o.length > 1 && Math.hypot(o[0][0] - o[o.length - 1][0], o[0][1] - o[o.length - 1][1]) < 1e-9) o.pop();
    return o;
  }
  const area2 = P => { let a = 0; for (let i = 0; i < P.length; i++) { const p = P[i], q = P[(i + 1) % P.length]; a += p[0] * q[1] - q[0] * p[1]; } return a / 2; };

  function create(E) {
    const steps = E.build();
    const W = steps.find(s => s.title === '날개 내리기'), fin = steps[steps.length - 1];
    const { fw, bw } = fin.wings;
    const base = W.facets.map(f => ({ poly: f.poly, T: f.T0, h: f.h0, tag: f.tag || null, id: f.id }));
    const restOf = (f, p) => { const w = E.apply(f.T, [p[0], p[1], 0]); return [w[0], w[1]]; };
    const centroidRest = f => { let x = 0, y = 0; f.poly.forEach(p => { const r = restOf(f, p); x += r[0]; y += r[1]; }); return [x / f.poly.length, y / f.poly.length]; };
    // wings hinge on the line joining where neck and tail leave the body (the body's widest point)
    const HINGE = 1.35;
    let FLOOR = 1e9;
    base.forEach(f => f.poly.forEach(p => { FLOOR = Math.min(FLOOR, restOf(f, p)[1]); }));
    const PIVOT = [0, 1.15];

    // neck / head / tail geometry (matches the folding sequence)
    const M0 = [-0.0915, 0.958], TIP = [-0.758, 1.652];
    const L0 = Math.hypot(TIP[0] - M0[0], TIP[1] - M0[1]);
    const aN = nrm2(sub2(TIP, M0)), bH = [-0.906, -0.423], mH = nrm2([aN[0] + bH[0], aN[1] + bH[1]]);
    const atN = f => [M0[0] + f * L0 * aN[0], M0[1] + f * L0 * aN[1]];
    const aT = [-aN[0], aN[1]], M0T = [-M0[0], M0[1]];
    const atT = f => [M0T[0] + f * L0 * aT[0], M0T[1] + f * L0 * aT[1]];
    const perp = a => [a[1], -a[0]];
    const fixH = (h, a) => crossZ(h, a) > 0 ? h : [-h[0], -h[1]];
    const J = (id, p, h, a, type, dof) => ({ id, p, h: type === 'wing' ? h : fixH(nrm2(h), a), a, type, dof });

    const wingJoints = k => [J(k + '0', [0, HINGE], [1, 0], [0, 1], 'wing', 3)].concat(
      [0.18, 0.34, 0.5, 0.66, 0.82].map((f, i) => J(k + (i + 1), [0, HINGE + f * (2 - HINGE)], [1, 0], [0, 1], 'wing', 1)));
    const CHAINS = {
      wF: { name: 'Front wing', joints: wingJoints('wF'), a: [0, 1], tip: [0, 2] },
      wB: { name: 'Back wing', joints: wingJoints('wB'), a: [0, 1], tip: [0, 2] },
      neck: {
        name: 'Neck & head', a: aN, tip: null,
        joints: [J('n0', M0, [-0.9087, -0.4171], aN, 'root', 2)]
          .concat([0.2, 0.35, 0.5, 0.65].map((f, i) => J('n' + (i + 1), atN(f), perp(aN), aN, 'bend', 2)))
          .concat([J('h', atN(0.8), mH, aN, 'head', 3)])
      },
      tail: {
        name: 'Tail', a: aT, tip: TIP.map((v, i) => i ? v : -v),
        joints: [J('t0', M0T, [0.9087, -0.4171], aT, 'root', 2)]
          .concat([0.25, 0.42, 0.6, 0.78].map((f, i) => J('t' + (i + 1), atT(f), perp(aT), aT, 'bend', 2)))
      }
    };
    const chainOfBase = f => fw.has(f.id) ? 'wF' : bw.has(f.id) ? 'wB' : (f.tag === 'neck' || f.tag === 'head') ? 'neck' : f.tag === 'tail' ? 'tail' : 'body';

    function splitByRest(f, P, D) {
      const inv = E.inverse(f.T);
      const a = E.apply(inv, [P[0], P[1], 0]), b = E.apply(inv, [P[0] + D[0], P[1] + D[1], 0]);
      const n = [-(b[1] - a[1]), b[0] - a[0]];
      const A = clipHalf(f.poly, a, n), B = clipHalf(f.poly, a, [-n[0], -n[1]]);
      if (A.length < 3 || B.length < 3 || Math.abs(area2(A)) < 1e-9 || Math.abs(area2(B)) < 1e-9) return [f];
      return [Object.assign({}, f, { poly: A }), Object.assign({}, f, { poly: B })];
    }

    // build the rig: base facets + built-in cuts + user creases
    function build(creases) {
      const chains = clone(CHAINS);
      let facets = [];
      base.forEach(f => {
        const ch = chainOfBase(f);
        if (ch !== 'wF' && ch !== 'wB') { facets.push(Object.assign({}, f, { chain: ch, depth: 0 })); return; }
        splitByRest(f, [0, HINGE], [1, 0]).forEach(g => facets.push(Object.assign({}, g, { chain: centroidRest(g)[1] > HINGE ? ch : 'body', depth: 0 })));
      });
      for (const key in chains) {
        const ch = chains[key];
        ch.joints.forEach((j, idx) => {
          if (idx === 0 || j.type === 'head') return;
          const next = [];
          facets.forEach(f => { if (f.chain === key && f.tag !== 'head') next.push(...splitByRest(f, j.p, j.h)); else next.push(f); });
          facets = next;
        });
        facets.forEach(f => {
          if (f.chain !== key) return;
          if (f.tag === 'head') { f.depth = ch.joints.findIndex(j => j.type === 'head'); return; }
          const c = centroidRest(f); let d = 0;
          ch.joints.forEach((j, idx) => { if (idx > 0 && j.type !== 'head' && dot2(sub2(c, j.p), ch.a) > 0) d = idx; });
          f.depth = d;
        });
      }
      // beak tip: farthest head vertex from the head hinge
      let best = null, far = -1;
      facets.forEach(f => { if (f.tag === 'head') f.poly.forEach(p => { const r = restOf(f, p), d = Math.hypot(r[0] - chains.neck.joints.at(-1).p[0], r[1] - chains.neck.joints.at(-1).p[1]); if (d > far) { far = d; best = r; } }); });
      chains.neck.tip = best;
      const creaseLines = [];
      (creases || []).forEach(c => {
        const ch = chains[c.chain]; if (!ch) return;
        const k = ch.joints.findIndex(j => j.id === c.after); if (k < 0) return;
        const D = nrm2(sub2(c.p2, c.p1));
        if (!isFinite(D[0])) return;
        const tipSide = crossZ(D, sub2(ch.tip, c.p1)) > 0 ? 1 : -1;
        const next = [];
        facets.forEach(f => {
          if (f.chain !== c.chain || f.depth !== k) { next.push(f.chain === c.chain && f.depth > k ? Object.assign(f, { depth: f.depth + 1 }) : f); return; }
          splitByRest(f, c.p1, D).forEach(g => {
            const cc = centroidRest(g);
            g = Object.assign({}, g, { depth: crossZ(D, sub2(cc, c.p1)) * tipSide > 0 ? k + 1 : k });
            next.push(g);
          });
        });
        facets = next;
        const mid = [(c.p1[0] + c.p2[0]) / 2, (c.p1[1] + c.p2[1]) / 2];
        ch.joints.splice(k + 1, 0, { id: c.id, p: mid, h: fixH(D, ch.a), a: ch.a, type: 'crease', dof: 1, user: true });
        creaseLines.push({ id: c.id, chain: c.chain, p1: c.p1, p2: c.p2 });
      });
      // edges lying on user crease lines (drawn in red)
      const creaseEdges = [];
      creaseLines.forEach(cl => {
        const D = nrm2(sub2(cl.p2, cl.p1));
        facets.forEach((f, fi) => {
          if (f.chain !== cl.chain) return;
          for (let i = 0; i < f.poly.length; i++) {
            const a = f.poly[i], b = f.poly[(i + 1) % f.poly.length];
            const ra = restOf(f, a), rb = restOf(f, b);
            if (Math.abs(crossZ(D, sub2(ra, cl.p1))) < 1e-6 && Math.abs(crossZ(D, sub2(rb, cl.p1))) < 1e-6 && Math.hypot(ra[0] - rb[0], ra[1] - rb[1]) > 1e-6)
              creaseEdges.push({ fi, a, b, id: cl.id });
          }
        });
      });
      const jointChain = {};
      for (const key in chains) chains[key].joints.forEach(j => { jointChain[j.id] = key; });
      const hBase = {}; facets.forEach(f => { hBase[f.chain] = Math.min(hBase[f.chain] == null ? 1e9 : hBase[f.chain], f.h); });
      // hinge axes sit on the part's own layer so bending does not open gaps
      for (const key in chains) chains[key].joints.forEach(j => { j.z = (hBase[key] || 0) * EPS; });
      return { facets, chains, creaseEdges, jointChain, FLOOR, PIVOT, restOf, hBase };
    }

    // ---------- forward kinematics ----------
    const EPS = 0.0022;
    const restPoint = (rig, f, p) => { const w = E.apply(f.T, [p[0], p[1], 0]); w[2] += (f.chain === 'body' ? f.h : (f.h - rig.hBase[f.chain]) * (f.chain[0] === 'w' ? 0.08 : 0.35) + rig.hBase[f.chain]) * EPS; return w; };
    const jv = (pose, id) => (pose.j && pose.j[id]) || [0, 0, 0];
    function jointT(j, v) {
      const p = [j.p[0], j.p[1], j.z || 0];
      let T = E.rotAxis(p, [j.h[0], j.h[1], 0], v[0] * D2R);
      if (v[1]) T = E.compose(T, E.rotAxis(p, [0, 0, 1], v[1] * D2R));
      if (v[2]) T = E.compose(T, E.rotAxis(p, [j.a[0], j.a[1], 0], v[2] * D2R));
      return T;
    }
    function bodyT(pose) {
      const b = Object.assign({ x: 0, y: 0, z: 0, yaw: 0, pitch: 0, roll: 0 }, pose.b || {});
      const pv = [PIVOT[0], PIVOT[1] - FLOOR, 0];
      let R = E.rotAxis(pv, [0, 1, 0], b.yaw * D2R);
      R = E.compose(R, E.rotAxis(pv, [1, 0, 0], b.roll * D2R));
      R = E.compose(R, E.rotAxis(pv, [0, 0, 1], -b.pitch * D2R));
      const T = E.compose({ R: [1, 0, 0, 0, 1, 0, 0, 0, 1], t: [b.x, b.y, b.z] }, R);
      return E.compose(T, { R: [1, 0, 0, 0, 1, 0, 0, 0, 1], t: [0, -FLOOR, 0] });
    }
    // classroom set: black desk top at y=0 (front edge at z=0.55), oak floor below
    const DESK = { x0: -8, x1: 8, z0: -7.45, z1: 0.55, under: -0.6, floor: -9 };
    const support = w => (w[0] > DESK.x0 && w[0] < DESK.x1 && w[2] > DESK.z0 && w[2] < DESK.z1 && w[1] > DESK.under) ? 0 : DESK.floor;
    function chainCums(rig, pose) {
      const B = bodyT(pose), out = { body: [B] };
      for (const key in rig.chains) {
        let T = B; out[key] = rig.chains[key].joints.map(j => (T = E.compose(T, jointT(j, jv(pose, j.id)))));
      }
      // standing on the ledge: lift the whole crane so its lowest point rests on the ledge instead of sinking in
      const g = pose.b && pose.b.ground != null ? pose.b.ground : 1;
      if (g >= 0.5) {
        let lift = 0;
        rig.facets.forEach(f => {
          const T = f.chain === 'body' ? out.body[0] : out[f.chain][f.depth];
          f.poly.forEach(p => { const w = E.apply(T, restPoint(rig, f, p)); lift = Math.max(lift, support(w) - w[1]); });
        });
        if (lift > 0) {
          const L = { R: [1, 0, 0, 0, 1, 0, 0, 0, 1], t: [0, lift, 0] };
          for (const k in out) out[k] = out[k].map(T => E.compose(L, T));
        }
      }
      return out;
    }
    function facetTransforms(rig, pose) {
      const C = chainCums(rig, pose);
      return rig.facets.map(f => f.chain === 'body' ? C.body[0] : C[f.chain][f.depth]);
    }

    // ---------- handles & IK ----------
    const HANDLES = {
      wF: { chain: 'wF', label: 'Front wing tip' }, wB: { chain: 'wB', label: 'Back wing tip' },
      beak: { chain: 'neck', label: 'Beak' }, neck: { chain: 'neck', label: 'Neck', upTo: 'h' },
      tail: { chain: 'tail', label: 'Tail tip' }
    };
    function handleInfo(rig, hid) {
      const H = HANDLES[hid], ch = rig.chains[H.chain];
      if (H.upTo) { const k = ch.joints.findIndex(j => j.id === H.upTo); return { chain: H.chain, depth: k - 1, point: ch.joints[k].p, joints: ch.joints.slice(0, k) }; }
      return { chain: H.chain, depth: ch.joints.length - 1, point: ch.tip, joints: ch.joints };
    }
    function handlePos(rig, pose, hid) {
      const info = handleInfo(rig, hid), C = chainCums(rig, pose);
      return E.apply(C[info.chain][info.depth], [info.point[0], info.point[1], 0]);
    }
    const LIM = {
      wing0: [[-178, 178], [-125, 125], [-60, 60]], wing: [[-70, 70]],
      root: [[-75, 75], [-70, 90]], bend: [[-40, 40], [-35, 35]], head: [[-70, 70], [-90, 90], [-50, 50]], crease: [[-178, 178]]
    };
    function limits(j, idx) {
      if (j.type === 'wing') {
        if (idx > 0) return LIM.wing;
        return j.id === 'wF0' ? [[-10, 178], LIM.wing0[1], LIM.wing0[2]] : [[-178, 10], LIM.wing0[1], LIM.wing0[2]];
      }
      return LIM[j.type];
    }
    function solveIK(rig, pose, hid, target, opts = {}) {
      const info = handleInfo(rig, hid);
      const params = []; // [jointId, dofIndex, stiffness, lo, hi]
      info.joints.forEach((j, idx) => {
        const lim = limits(j, idx);
        const dofs = j.type === 'wing' ? (idx === 0 ? [0, 1] : [0]) : j.type === 'head' ? [0, 1] : j.type === 'crease' ? [0] : [0, 1];
        const k = j.type === 'crease' ? 0.12 : j.type === 'bend' || (j.type === 'wing' && idx > 0) ? 0.7 : 0.35;
        dofs.forEach(d => params.push([j.id, d, k, lim[d][0], lim[d][1], j.type]));
      });
      pose.j = pose.j || {};
      params.forEach(([id]) => { if (!pose.j[id]) pose.j[id] = [0, 0, 0]; });
      const get = () => params.map(([id, d]) => pose.j[id][d]);
      const set = th => params.forEach(([id, d, , lo, hi], i) => { pose.j[id][d] = Math.max(lo, Math.min(hi, th[i])); });
      const th0 = opts.from ? params.map(([id, d]) => ((opts.from.j || {})[id] || [0, 0, 0])[d]) : get();
      const tipAt = th => { set(th); return handlePos(rig, pose, hid); };
      let th = get();
      const m = th.length;
      for (let it = 0; it < (opts.iters || 14); it++) {
        const p0 = tipAt(th), e = [target[0] - p0[0], target[1] - p0[1], target[2] - p0[2]];
        if (Math.hypot(...e) < 1e-4) break;
        const Jm = [];
        for (let i = 0; i < m; i++) { const t2 = th.slice(); t2[i] += 0.5; const p1 = tipAt(t2); Jm.push([(p1[0] - p0[0]) / 0.5, (p1[1] - p0[1]) / 0.5, (p1[2] - p0[2]) / 0.5]); }
        set(th);
        // (J^T J + damping + stiffness + bend smoothing) dth = J^T e - stiffness (th - th0)
        const A = Array.from({ length: m }, () => new Array(m).fill(0)), g = new Array(m).fill(0);
        const mu = opts.mu != null ? opts.mu : 2e-5;
        for (let i = 0; i < m; i++) {
          for (let k = 0; k < m; k++) A[i][k] = Jm[i][0] * Jm[k][0] + Jm[i][1] * Jm[k][1] + Jm[i][2] * Jm[k][2];
          g[i] = Jm[i][0] * e[0] + Jm[i][1] * e[1] + Jm[i][2] * e[2] - mu * params[i][2] * (th[i] - th0[i]);
          A[i][i] += 1e-5 + mu * params[i][2];
        }
        // smooth curvature across consecutive bend cuts of the same dof
        for (let i = 0; i < m; i++) for (let k = i + 1; k < m; k++) {
          const a = params[i], b = params[k];
          if (a[1] === b[1] && (a[5] === 'bend' || (a[5] === 'wing' && !a[0].endsWith('0'))) && a[5] === b[5] && k === i + (a[5] === 'wing' ? 1 : 2)) {
            const w = 6e-5; A[i][i] += w; A[k][k] += w; A[i][k] -= w; A[k][i] -= w;
            g[i] -= w * (th[i] - th[k]); g[k] -= w * (th[k] - th[i]);
          }
        }
        const dth = gauss(A, g);
        const mx = Math.max(...dth.map(Math.abs)); const sc = mx > 25 ? 25 / mx : 1;
        th = th.map((v, i) => Math.max(params[i][3], Math.min(params[i][4], v + dth[i] * sc)));
      }
      set(th);
      return pose;
    }
    function gauss(A, b) {
      const n = b.length, M = A.map((r, i) => r.concat([b[i]]));
      for (let c = 0; c < n; c++) {
        let p = c; for (let r = c + 1; r < n; r++) if (Math.abs(M[r][c]) > Math.abs(M[p][c])) p = r;
        [M[c], M[p]] = [M[p], M[c]];
        const d = M[c][c] || 1e-12;
        for (let r = c + 1; r < n; r++) { const f = M[r][c] / d; for (let k = c; k <= n; k++) M[r][k] -= f * M[c][k]; }
      }
      const x = new Array(n).fill(0);
      for (let r = n - 1; r >= 0; r--) { let s = M[r][n]; for (let k = r + 1; k < n; k++) s -= M[r][k] * x[k]; x[r] = s / (M[r][r] || 1e-12); }
      return x;
    }
    // mirror one wing's joint values onto the other (reflection through the body plane)
    function mirrorWing(pose, from) {
      const to = from === 'wF' ? 'wB' : 'wF';
      for (let i = 0; i < 6; i++) { const v = jv(pose, from + i); pose.j[to + i] = [-v[0], v[1], -v[2]]; }
    }

    // ---------- semantic pose helper (for presets) ----------
    function P(sem = {}) {
      const j = {};
      ['F', 'B'].forEach(X => {
        const w = Object.assign({ flap: 6, fwd: 0, twist: 0, curl: 8, tip: 0 }, sem['w' + X] || sem.w || {});
        const sg = X === 'F' ? 1 : -1, k = 'w' + X;
        // rest wing points straight up; flap 0 = horizontal, positive = raised
        j[k + '0'] = [sg * (90 - w.flap), w.fwd, sg * w.twist];
        for (let i = 1; i <= 5; i++) j[k + i] = [-sg * (w.curl / 5 + (i === 5 ? w.tip : 0)), 0, 0];
      });
      const n = Object.assign({ bow: 0, side: 0 }, sem.neck || {});
      j.n0 = [n.side * 0.4, n.bow * 0.4, 0];
      for (let i = 1; i <= 4; i++) j['n' + i] = [n.side * 0.15, n.bow * 0.15, 0];
      const h = Object.assign({ nod: 0, turn: 0, tilt: 0 }, sem.head || {});
      j.h = [h.turn, h.nod, h.tilt];
      const t = Object.assign({ up: 0, side: 0 }, sem.tail || {});
      j.t0 = [t.side * 0.5, t.up * 0.5, 0];
      for (let i = 1; i <= 4; i++) j['t' + i] = [t.side / 8, t.up / 8, 0];
      return { b: Object.assign({ x: 0, y: 0, z: 0, yaw: 0, pitch: 0, roll: 0, ground: 1 }, sem.b || {}), j };
    }

    // ---------- timeline ----------
    const EASE = {
      linear: u => u,
      in: u => u * u * u,
      out: u => 1 - Math.pow(1 - u, 3),
      inout: u => u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2,
      snap: u => 1 - Math.pow(1 - u, 6),
      over: u => { const c1 = 2.2, c3 = c1 + 1; return 1 + c3 * Math.pow(u - 1, 3) + c1 * Math.pow(u - 1, 2); }
    };
    const isWing = id => id[0] === 'w';
    function lerpPose(A, B, u, uw, wingIds) {
      const out = { b: {}, j: {} };
      const kb = new Set([...Object.keys(A.b || {}), ...Object.keys(B.b || {})]);
      kb.forEach(k => { const a = (A.b || {})[k] || 0, b = (B.b || {})[k] || 0; out.b[k] = a + (b - a) * u; });
      const kj = new Set([...Object.keys(A.j || {}), ...Object.keys(B.j || {})]);
      kj.forEach(k => {
        const a = (A.j || {})[k] || [0, 0, 0], b = (B.j || {})[k] || [0, 0, 0], w = (isWing(k) || (wingIds && wingIds.has(k))) ? uw : u;
        out.j[k] = [0, 1, 2].map(i => a[i] + (b[i] - a[i]) * w);
      });
      return out;
    }
    // frames: each key, its hold frames, then the in-betweens to the next key
    function expand(motion, rig) {
      const frames = [], keys = motion.keys;
      const wingIds = new Set(); if (rig) for (const id in rig.jointChain) if (rig.jointChain[id][0] === 'w') wingIds.add(id);
      keys.forEach((k, i) => {
        frames.push({ pose: k.pose, key: i, kind: 'key' });
        for (let h = 0; h < (k.hold || 0); h++) frames.push({ pose: k.pose, key: i, kind: 'hold' });
        const nx = keys[i + 1]; if (!nx) return;
        const tr = Object.assign({ n: 3, ease: 'inout', wingLag: 0, flap: null }, k.tr || {});
        for (let s = 1; s <= tr.n; s++) {
          const u = s / (tr.n + 1), e = EASE[tr.ease] || EASE.inout;
          const lag = Math.min(0.9, tr.wingLag || 0), uw = e(Math.max(0, (u - lag) / (1 - lag)));
          const pose = lerpPose(k.pose, nx.pose, e(u), uw, wingIds);
          if (tr.flap && tr.flap.amp) {
            const f = tr.flap, acc = f.accel || 0;
            const ph = f.cycles * (u + acc * u * u) / (1 + acc), env = Math.pow(Math.sin(Math.PI * u), 0.35);
            const dF = f.amp * Math.sin(2 * Math.PI * ph) * env, dB = f.amp * Math.sin(2 * Math.PI * (ph - (f.lag || 0))) * env;
            if (pose.j.wF0) pose.j.wF0[0] = Math.max(26, Math.min(130, pose.j.wF0[0] - dF));
            if (pose.j.wB0) pose.j.wB0[0] = -Math.max(26, Math.min(130, -pose.j.wB0[0] - dB));
          }
          frames.push({ pose, key: i, kind: 'tween', u });
        }
      });
      return frames;
    }

    function pointPos(rig, pose, chain, depth, p) {
      const C = chainCums(rig, pose);
      return E.apply(chain === 'body' ? C.body[0] : C[chain][depth], [p[0], p[1], 0]);
    }

    // ---------- built-in motion presets ----------
    function presets(rig) {
      const key = (role, pose, hold, tr) => ({ role, pose, hold, tr });
      const merge = (a, b) => { const o = clone(a); for (const k in b) o[k] = Object.assign({}, o[k] || {}, b[k]); return o; };
      const STAND = {};
      const M = [];
      // Look & Tilt
      {
        const look = { neck: { bow: -14, side: 22 }, head: { nod: -24, turn: 20 }, b: { yaw: -10 } };
        M.push({ id: 'look', name: 'Look & Tilt', cut: '2-2', desc: 'Turns head toward the window → tilts → tilts a little more → holds', keys: [
          key('start', P(STAND), 4, { n: 4, ease: 'inout' }),
          key('prep', P({ neck: { bow: 8 }, head: { nod: 12 } }), 1, { n: 3, ease: 'snap' }),
          key('core', P(look), 3, { n: 3, ease: 'out' }),
          key('core', P(merge(look, { head: { tilt: 26 } })), 6, { n: 4, ease: 'inout' }),
          key('end', P(merge(look, { head: { tilt: 36, nod: -20 }, neck: { side: 28 }, b: { roll: 5 } })), 16, null)
        ] });
      }
      // Head Scratch — pose fitted to a photo of a real crane scratching its head
      {
        const touch = { b: { roll: -7 }, wB: { flap: -24, fwd: -2, curl: 2, twist: -24 }, wF: { flap: 20, fwd: 25, curl: 109, twist: 27 }, neck: { bow: -45, side: -1 }, head: { nod: 8 }, tail: { up: 11, side: 4 } };
        const rub = merge(touch, { wF: { flap: 15, curl: 122 }, head: { nod: 16, tilt: 8 } });
        const prep = { b: { roll: -5 }, wB: { flap: -18, twist: -18 }, neck: { bow: -36 }, head: { nod: 4 }, tail: { up: 9 } };
        const reach = merge(prep, { wF: { flap: 55, fwd: 15, curl: 40, twist: 15 } });
        M.push({ id: 'scratch', name: 'Head Scratch', cut: '2-7', desc: 'Bows head → brings one wing to the head → two quick scratches → lowers the wing', keys: [
          key('start', P(STAND), 3, { n: 4, ease: 'inout' }),
          key('prep', P(prep), 1, { n: 3, ease: 'inout' }),
          key('core', P(reach), 0, { n: 3, ease: 'out' }),
          key('core', P(touch), 3, { n: 1, ease: 'linear' }),
          key('core', P(rub), 0, { n: 1, ease: 'linear' }),
          key('core', P(touch), 0, { n: 1, ease: 'linear' }),
          key('core', P(rub), 0, { n: 1, ease: 'linear' }),
          key('core', P(touch), 3, { n: 3, ease: 'inout' }),
          key('core', P(reach), 0, { n: 4, ease: 'inout' }),
          key('end', P({ neck: { bow: -10 }, head: { nod: 6 } }), 12, null)
        ] });
      }
      // Failed Takeoff
      {
        const proud = { wF: { flap: 66, curl: 10 }, wB: { flap: 66, curl: 10 }, neck: { bow: -18, side: -8 }, head: { nod: -22 }, b: { pitch: 10 }, tail: { up: 8 } };
        M.push({ id: 'takeoff', name: 'Failed Takeoff', cut: '2-4', desc: 'Ready stance → hard flapping → short hop → loses balance → flails → falls head first', keys: [
          key('start', P(STAND), 3, { n: 5, ease: 'inout' }),
          key('prep', P({ b: { pitch: -8 }, neck: { bow: 16 }, head: { nod: 6 }, w: { flap: 4, curl: 2 }, tail: { up: 12 } }), 3, { n: 3, ease: 'snap' }),
          key('core', P(proud), 8, { n: 10, ease: 'linear', flap: { cycles: 3, amp: 55, lag: 0, accel: 0.5 } }),
          key('core', P({ b: { y: 0.2, pitch: 6 }, w: { flap: 25, curl: 10 }, neck: { bow: -10 }, head: { nod: -12 }, tail: { up: 4 } }), 2, { n: 6, ease: 'linear', flap: { cycles: 3.5, amp: 60, lag: 0.22, accel: 1.2 } }),
          key('core', P({ b: { y: 0.15, z: 0.25, roll: 26, pitch: -14 }, wF: { flap: 55, curl: 12 }, wB: { flap: -10, curl: 6 }, neck: { bow: 22, side: -10 }, head: { nod: 18 }, tail: { up: 16 } }), 0, { n: 8, ease: 'linear', flap: { cycles: 4, amp: 62, lag: 0.4, accel: 1.6 } }),
          key('core', P({ b: { y: 0.12, z: 0.5, roll: 34, pitch: -32 }, wF: { flap: 35, curl: 8 }, wB: { flap: 20, curl: 4 }, neck: { bow: 46, side: -14 }, head: { nod: 30 }, tail: { up: 22 } }), 0, { n: 4, ease: 'in', wingLag: 0.45 }),
          key('end', P({ b: { y: -1.6, z: 1.7, roll: 40, pitch: -75, ground: 0 }, w: { flap: 55, curl: 26 }, neck: { bow: 30, side: -8 }, head: { nod: 20 }, tail: { up: 30 } }), 6, null)
        ] });
      }
      // Wake Up — head down, slow lift, sudden freeze
      {
        const sleep = { b: { pitch: -6 }, neck: { bow: 40 }, head: { nod: 40 }, w: { flap: -20, curl: 4 }, tail: { up: -4 } };
        const up = { neck: { bow: -18 }, head: { nod: -12 }, w: { flap: 10, curl: 8 }, tail: { up: 4 } };
        M.push({ id: 'wake', name: 'Wake Up', cut: '1-3', desc: 'Head down → slowly lifts → sudden freeze', keys: [
          key('start', P(sleep), 8, { n: 4, ease: 'inout' }),
          key('prep', P(merge(sleep, { neck: { bow: 34 }, head: { nod: 30 } })), 2, { n: 12, ease: 'inout' }),
          key('core', P({ neck: { bow: -6 }, head: { nod: 2 }, w: { flap: 4, curl: 6 } }), 0, { n: 2, ease: 'snap' }),
          key('end', P(merge(up, { head: { tilt: 6 } })), 12, null)
        ] });
      }
      // Prepare to Fly — crouch, stretch neck, wings way up, proud hold
      {
        const proud = { b: { pitch: 9 }, w: { flap: 62, curl: 14 }, neck: { bow: -30 }, head: { nod: -22 }, tail: { up: 14 } };
        M.push({ id: 'prepfly', name: 'Prepare to Fly', cut: '2-3', desc: 'Crouches slightly → stretches the neck → throws both wings up → proud hold', keys: [
          key('start', P(STAND), 3, { n: 3, ease: 'inout' }),
          key('prep', P({ b: { pitch: -8 }, neck: { bow: 16 }, head: { nod: 8 }, w: { flap: -10, curl: 4 }, tail: { up: 10 } }), 2, { n: 3, ease: 'snap' }),
          key('core', P({ b: { pitch: 4 }, neck: { bow: -30 }, head: { nod: -15 }, w: { flap: 10 }, tail: { up: 6 } }), 1, { n: 2, ease: 'snap' }),
          key('core', P(merge(proud, { w: { flap: 70 } })), 0, { n: 3, ease: 'over' }),
          key('end', P(proud), 16, null)
        ] });
      }
      // Recover — lying on its side, wriggle, pop up, wobble, settle
      {
        const lying = { b: { roll: -68 }, wB: { flap: 55, curl: 6 }, wF: { flap: -12 }, neck: { bow: 20, side: -14 }, head: { nod: 18 }, tail: { up: -6 } };
        M.push({ id: 'recover', name: 'Recover', cut: '2-6', desc: 'Lying on its side → wriggles → springs up → wobbles once → finds balance', keys: [
          key('start', P(lying), 6, { n: 2, ease: 'linear' }),
          key('prep', P(merge(lying, { b: { roll: -60 }, wF: { flap: 18 }, head: { nod: 6 } })), 0, { n: 2, ease: 'linear' }),
          key('prep', P(merge(lying, { b: { roll: -70 }, wF: { flap: -14 } })), 0, { n: 2, ease: 'linear' }),
          key('prep', P(merge(lying, { b: { roll: -60 }, wF: { flap: 20 } })), 1, { n: 2, ease: 'snap' }),
          key('core', P({ b: { roll: 10 }, w: { flap: 32, curl: 10 }, neck: { bow: -12 }, head: { nod: -8 }, tail: { up: 6 } }), 0, { n: 3, ease: 'out' }),
          key('core', P({ b: { roll: -10, pitch: -8 }, wF: { flap: 12 }, wB: { flap: 42, curl: 10 }, neck: { bow: 10, side: 12 }, head: { nod: 6, tilt: -10 } }), 0, { n: 4, ease: 'over' }),
          key('end', P({ w: { flap: 14, curl: 8 }, neck: { bow: -6 }, head: { nod: -4 } }), 12, null)
        ] });
      }
      // Head Shake — quick left/right shakes, last one overshoots and settles
      {
        const sh = (t, s) => P({ neck: { side: s }, head: { turn: t, nod: 4 }, w: { flap: 6 + Math.abs(s) * 0.3 } });
        M.push({ id: 'shake', name: 'Head Shake', cut: '2-7', desc: 'Quick left-right head shakes → last one overshoots and settles back', keys: [
          key('start', P(STAND), 3, { n: 2, ease: 'inout' }),
          key('prep', P({ neck: { bow: 8 }, head: { nod: 12 } }), 1, { n: 1, ease: 'snap' }),
          key('core', sh(30, 14), 0, { n: 1, ease: 'linear' }),
          key('core', sh(-30, -14), 0, { n: 1, ease: 'linear' }),
          key('core', sh(26, 12), 0, { n: 1, ease: 'linear' }),
          key('core', sh(-24, -11), 0, { n: 4, ease: 'over' }),
          key('end', P({ head: { tilt: 6, nod: -2 }, neck: { bow: -4 } }), 10, null)
        ] });
      }
      // Dodge — walk forward, stop dead, lean, spin, run the other way
      {
        M.push({ id: 'dodge', name: 'Dodge', cut: '2-8', desc: 'Moves forward → stops dead → leans to one side → spins around → flees the other way', keys: [
          key('start', P(STAND), 2, { n: 6, ease: 'linear' }),
          key('core', P({ b: { x: -0.4, pitch: -5 }, neck: { bow: 8 }, w: { flap: 8 } }), 0, { n: 1, ease: 'snap' }),
          key('core', P({ b: { x: -0.46, pitch: 10 }, w: { flap: 28, curl: 10 }, neck: { bow: -22 }, head: { nod: -12 }, tail: { up: 8 } }), 3, { n: 2, ease: 'snap' }),
          key('core', P({ b: { x: -0.46, z: 0.06, roll: 18 }, w: { flap: 20 }, neck: { bow: -10, side: 16 }, head: { turn: 10 } }), 1, { n: 2, ease: 'snap' }),
          key('core', P({ b: { x: -0.4, z: 0.1, yaw: 150, roll: 8 }, w: { flap: 32 }, neck: { bow: 6 } }), 0, { n: 6, ease: 'linear', flap: { cycles: 2, amp: 26, lag: 0.1, accel: 0.4 } }),
          key('end', P({ b: { x: 0.7, z: 0.15, yaw: 150, pitch: -10 }, w: { flap: 36, curl: 10 }, neck: { bow: 22 }, head: { nod: 8 }, tail: { up: 10 } }), 4, null)
        ] });
      }
      // Deflate — stop, wings droop, neck and body sink, slump
      {
        const slump = { b: { pitch: -12, roll: -4 }, w: { flap: -38, curl: -8 }, neck: { bow: 46 }, head: { nod: 34 }, tail: { up: -14 } };
        M.push({ id: 'deflate', name: 'Deflate', cut: '2-9', desc: 'Stops moving → wings droop → neck and body sink → slumps', keys: [
          key('start', P({ neck: { bow: -6 }, head: { nod: -4 } }), 6, { n: 6, ease: 'in' }),
          key('core', P({ w: { flap: -24, curl: -6 }, neck: { bow: -2 } }), 2, { n: 8, ease: 'inout' }),
          key('core', P({ b: { pitch: -8 }, w: { flap: -32, curl: -6 }, neck: { bow: 36 }, head: { nod: 24 }, tail: { up: -8 } }), 2, { n: 3, ease: 'out' }),
          key('end', P(slump), 14, null)
        ] });
      }
      // Longing — still slumped, only the head lifts toward the window, long hold
      {
        const slump = { b: { pitch: -12, roll: -4 }, w: { flap: -38, curl: -8 }, neck: { bow: 46 }, head: { nod: 34 }, tail: { up: -14 } };
        M.push({ id: 'longing', name: 'Longing', cut: '2-10', desc: 'Slumped → lifts only the head to look out the window → long hold', keys: [
          key('start', P(slump), 8, { n: 6, ease: 'inout' }),
          key('prep', P(merge(slump, { head: { nod: 40 } })), 2, { n: 10, ease: 'inout' }),
          key('end', P(merge(slump, { neck: { bow: 22, side: 6 }, head: { nod: -22, turn: 10, tilt: 6 } })), 36, null)
        ] });
      }
      // Crushed — pressed flat by an outside force
      {
        M.push({ id: 'crushed', name: 'Crushed', cut: '3-2', desc: 'Normal shape → neck and wings fold as the body is pressed flat. A separate state caused by an outside force', keys: [
          key('start', P(STAND), 4, { n: 2, ease: 'snap' }),
          key('core', P({ b: { pitch: -4 }, w: { flap: -32, curl: -20 }, neck: { bow: 30 }, head: { nod: 20 }, tail: { up: -22 } }), 0, { n: 3, ease: 'out' }),
          key('end', P({ w: { flap: -40, curl: -40 }, neck: { bow: 46, side: 8 }, head: { nod: 30, tilt: 12 }, tail: { up: -42, side: -6 } }), 14, null)
        ] });
      }
      const rest = [];
      // ---- Folded Wings shots (storyboard + on-set guide): exact 12 fps slot counts ----
      const SH = [];
      const kp = (role, pose, hold, tr, prop) => Object.assign(key(role, pose, hold, tr), { prop });
      {
        const b = { z: -1.5, yaw: 180 };
        const up = { b, neck: { bow: -12 }, head: { nod: -6 } };
        SH.push({ id: 'shot02', group: 'shot', target: 24, name: 'Shot 02 · Awakening and curiosity', cut: '02', desc: 'Raises its head → tilts slightly → turns toward the classroom window → holds. Eye-level close-up, 2 s.',
          cam: { p: [-2.7, 0.75, 2.4], t: [1.1, 0.4, -2.4], lens: 50 }, keys: [
            kp('start', P({ b, neck: { bow: 14 }, head: { nod: 16 } }), 2, { n: 4, ease: 'inout' }, 'Large close-up crane'),
            kp('core', P(up), 1, { n: 2, ease: 'out' }, 'Large close-up crane'),
            kp('core', P(merge(up, { head: { tilt: 14 } })), 1, { n: 3, ease: 'snap' }, 'Large close-up crane'),
            kp('end', P(merge(up, { neck: { side: 22 }, head: { turn: 28, tilt: 18, nod: -10 } })), 7, null, 'Large close-up crane')
          ] });
      }
      const proudAt = z => ({ b: { x: 1.5, z, yaw: 90, pitch: 8 }, w: { flap: 62, curl: 14 }, neck: { bow: -24 }, head: { nod: -18 }, tail: { up: 12 } });
      {
        SH.push({ id: 'shot04', group: 'shot', target: 24, name: 'Shot 04 · Ready to fly', cut: '04', desc: 'Approaches the desk edge → tiny body dip → raises both wings proudly → holds. High angle over the edge, 2 s.',
          cam: { p: [-3.8, 6.6, -6.0], t: [3.4, -4.4, 4.6], lens: 35 }, keys: [
            kp('start', P({ b: { x: 1.5, z: -0.8, yaw: 90 } }), 2, { n: 3, ease: 'inout' }, 'Small crane · neutral'),
            kp('prep', P({ b: { x: 1.5, z: -0.4, yaw: 90, pitch: -7 }, neck: { bow: 10 }, head: { nod: 6 }, w: { flap: 2 } }), 1, { n: 2, ease: 'snap' }, 'Small crane · neutral'),
            kp('core', P(merge(proudAt(-0.4), { w: { flap: 68 } })), 0, { n: 2, ease: 'over' }, 'Small crane · wings-up'),
            kp('end', P(proudAt(-0.4)), 10, null, 'Small crane · wings-up')
          ] });
      }
      {
        SH.push({ id: 'shot05', group: 'shot', target: 12, name: 'Shot 05 · The failed leap', cut: '05', desc: 'One ambitious flap → awkward tumble below the desk → wings splay unevenly → tips head-first and exits low. Extreme wide, 1 s. Fallback: proud pose at edge → one suspended falling pose → floor still.',
          cam: { p: [11.5, -6.9, 9.8], t: [1.6, -6.4, 0.6], lens: 24 }, keys: [
            kp('start', P(proudAt(-0.25)), 0, { n: 1, ease: 'snap' }, 'Small crane · wings-up'),
            kp('core', P({ b: { x: 1.5, z: 0.35, y: 0.35, yaw: 90, pitch: -5 }, wF: { flap: -20 }, wB: { flap: -28 }, neck: { bow: -20 }, head: { nod: -10 }, tail: { up: 10 } }), 0, { n: 2, ease: 'linear' }, 'Small crane · falling pose on removable rig'),
            kp('core', P({ b: { x: 1.5, z: 1.2, y: -1.8, yaw: 90, pitch: -50, roll: 25, ground: 0 }, wF: { flap: 55, curl: 10 }, wB: { flap: -15 }, neck: { bow: 30 }, head: { nod: 25 }, tail: { up: 25 } }), 0, { n: 2, ease: 'in' }, 'Small crane · falling pose on removable rig'),
            kp('core', P({ b: { x: 1.5, z: 1.7, y: -6.0, yaw: 90, pitch: -115, roll: 35, ground: 0 }, wF: { flap: 70, curl: 20 }, wB: { flap: 10 }, neck: { bow: 40 }, head: { nod: 30 }, tail: { up: 30 } }), 0, { n: 1, ease: 'in' }, 'Small crane · falling pose on removable rig'),
            kp('end', P({ b: { x: 1.5, z: 2.0, y: -8.6, yaw: 90, pitch: -140, roll: 40 }, wF: { flap: 30, curl: 10 }, wB: { flap: -10 }, neck: { bow: 40 }, head: { nod: 30 }, tail: { up: 20 } }), 1, null, 'Small crane · collapsed')
          ] });
      }
      {
        SH.push({ id: 'shot06', group: 'shot', target: 36, name: 'Shot 06 · An awkward silence', cut: '06', desc: 'The crane lies collapsed on the oak floor. One still held for 3 s; keep wheels and furniture fixed.',
          cam: { p: [7.8, -3.0, 10.0], t: [1.4, -9, 2.4], lens: 28 }, keys: [
            kp('start', P({ b: { x: 1.6, z: 2.6, y: -9, yaw: 120, roll: 62 }, wF: { flap: -10, curl: -10 }, wB: { flap: 50, curl: 10 }, neck: { bow: 30, side: -10 }, head: { nod: 30 }, tail: { up: -10 } }), 35, null, 'Small crane · collapsed')
          ] });
      }
      const order = ['wake', 'look', 'prepfly', 'takeoff', 'recover', 'shake', 'scratch', 'dodge', 'deflate', 'longing', 'crushed'];
      const all = M.concat(rest);
      all.forEach(m => { m.draft = false; m.group = 'library'; });
      return SH.concat(order.map(id => all.find(m => m.id === id)));
    }

    // ---------- collision: triangle-triangle intersections between parts, plus the ledge ----------
    const LEDGE = DESK;
    const sub3 = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
    const dot3 = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
    const cross3 = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
    function interval(p0, p1, p2, d0, d1, d2) {
      if (d0 * d1 > 0) return [p2 + (p0 - p2) * d2 / (d2 - d0), p2 + (p1 - p2) * d2 / (d2 - d1)];
      if (d0 * d2 > 0) return [p1 + (p0 - p1) * d1 / (d1 - d0), p1 + (p2 - p1) * d1 / (d1 - d2)];
      if (d1 * d2 > 0 || d0 !== 0) return [p0 + (p1 - p0) * d0 / (d0 - d1), p0 + (p2 - p0) * d0 / (d0 - d2)];
      if (d1 !== 0) return [p1 + (p0 - p1) * d1 / (d1 - d0), p1 + (p2 - p1) * d1 / (d1 - d2)];
      if (d2 !== 0) return [p2 + (p0 - p2) * d2 / (d2 - d0), p2 + (p1 - p2) * d2 / (d2 - d1)];
      return null;
    }
    function triTri(V0, V1, V2, U0, U1, U2) {
      const N1 = cross3(sub3(V1, V0), sub3(V2, V0)), d1 = -dot3(N1, V0);
      const e1 = 1e-9 * (Math.abs(N1[0]) + Math.abs(N1[1]) + Math.abs(N1[2]) + 1e-12);
      let du0 = dot3(N1, U0) + d1, du1 = dot3(N1, U1) + d1, du2 = dot3(N1, U2) + d1;
      if (Math.abs(du0) < e1) du0 = 0; if (Math.abs(du1) < e1) du1 = 0; if (Math.abs(du2) < e1) du2 = 0;
      if (du0 * du1 > 0 && du0 * du2 > 0) return false;
      const N2 = cross3(sub3(U1, U0), sub3(U2, U0)), d2 = -dot3(N2, U0);
      const e2 = 1e-9 * (Math.abs(N2[0]) + Math.abs(N2[1]) + Math.abs(N2[2]) + 1e-12);
      let dv0 = dot3(N2, V0) + d2, dv1 = dot3(N2, V1) + d2, dv2 = dot3(N2, V2) + d2;
      if (Math.abs(dv0) < e2) dv0 = 0; if (Math.abs(dv1) < e2) dv1 = 0; if (Math.abs(dv2) < e2) dv2 = 0;
      if (dv0 * dv1 > 0 && dv0 * dv2 > 0) return false;
      const D = cross3(N1, N2), ax = Math.abs(D[0]) > Math.abs(D[1]) ? (Math.abs(D[0]) > Math.abs(D[2]) ? 0 : 2) : (Math.abs(D[1]) > Math.abs(D[2]) ? 1 : 2);
      const a = interval(V0[ax], V1[ax], V2[ax], dv0, dv1, dv2), b = interval(U0[ax], U1[ax], U2[ax], du0, du1, du2);
      if (!a || !b) return false; // coplanar: stacked layers, not a crossing
      const a0 = Math.min(a[0], a[1]), a1 = Math.max(a[0], a[1]), b0 = Math.min(b[0], b[1]), b1 = Math.max(b[0], b[1]);
      return a1 > b0 + 1e-7 && b1 > a0 + 1e-7;
    }
    // which facet pairs may legitimately touch: same rigid piece, neighbouring segments, or a part's root against the body
    function mayTouch(fa, fb) {
      if (fa.chain === fb.chain) return fa.chain === 'body' || Math.abs(fa.depth - fb.depth) <= 1;
      // every part is anchored in the body core, where real paper is layered rather than crossing
      // (the first two segments of each part sit inside that core and press against each other)
      if (fa.depth <= 1 && fb.depth <= 1) return true;
      // neck and tail run between the body layers (which now include the wing bases) for their first segments
      const inBody = (a, b) => a.chain === 'body' && (b.chain === 'neck' || b.chain === 'tail') && b.depth <= 2;
      return inBody(fa, fb) || inBody(fb, fa);
    }
    function worldTris(rig, pose) {
      const Ts = facetTransforms(rig, pose), tris = [];
      rig.facets.forEach((f, fi) => {
        const P = f.poly.map(p => E.apply(Ts[fi], restPoint(rig, f, p)));
        for (let j = 1; j < P.length - 1; j++) {
          let A = P[0], B = P[j], C = P[j + 1];
          const c = [(A[0] + B[0] + C[0]) / 3, (A[1] + B[1] + C[1]) / 3, (A[2] + B[2] + C[2]) / 3];
          const sh = q => [c[0] + (q[0] - c[0]) * 0.97, c[1] + (q[1] - c[1]) * 0.97, c[2] + (q[2] - c[2]) * 0.97];
          A = sh(A); B = sh(B); C = sh(C);
          tris.push({ fi, v: [A, B, C], lo: [Math.min(A[0], B[0], C[0]), Math.min(A[1], B[1], C[1]), Math.min(A[2], B[2], C[2])], hi: [Math.max(A[0], B[0], C[0]), Math.max(A[1], B[1], C[1]), Math.max(A[2], B[2], C[2])] });
        }
      });
      return tris;
    }
    // returns {pairs:[[ti,tj]], floor:[ti], tris, n}; `only` limits checks to triangles of one chain
    function collisions(rig, pose, only) {
      const tris = worldTris(rig, pose), pairs = [], floor = [], side = [];
      const F = rig.facets;
      // each wing must stay on its own side of the body: crossing over means it went through the body
      const bi = F.findIndex(f => f.chain === 'body'), Binv = E.inverse(facetTransforms(rig, pose)[bi]);
      tris.forEach((t, i) => {
        const f = F[t.fi]; if ((f.chain !== 'wF' && f.chain !== 'wB') || f.depth < 1 || (only && f.chain !== only)) return;
        const sg = f.chain === 'wF' ? 1 : -1;
        if (t.v.some(v => { const l = E.apply(Binv, v); return l[2] * sg < -0.03 && Math.abs(l[0]) < 0.34 && l[1] > 0.88 && l[1] < 1.5; })) side.push(i);
      });
      for (let i = 0; i < tris.length; i++) {
        const A = tris[i], fa = F[A.fi];
        if (only && fa.chain !== only) continue;
        if (A.v.some(v => v[1] < support(v) - 0.004)) floor.push(i);
        for (let j = 0; j < tris.length; j++) {
          if (j === i || (!only && j < i)) continue;
          const B = tris[j], fb = F[B.fi];
          if (only && fb.chain === only && j < i) continue;
          if (A.lo[0] > B.hi[0] || B.lo[0] > A.hi[0] || A.lo[1] > B.hi[1] || B.lo[1] > A.hi[1] || A.lo[2] > B.hi[2] || B.lo[2] > A.hi[2]) continue;
          if (mayTouch(fa, fb)) continue;
          if (triTri(A.v[0], A.v[1], A.v[2], B.v[0], B.v[1], B.v[2])) pairs.push([i, j]);
        }
      }
      return { pairs, floor, side, tris, n: pairs.length + floor.length + side.length };
    }
    // move from pose `from` toward `to` (joint values of one chain) as far as possible without new penetration
    function blockAt(rig, from, to, chain) {
      const ids = rig.chains[chain].joints.map(j => j.id);
      const base = collisions(rig, from, chain).n;
      const mix = t => { const q = clone(to); ids.forEach(id => { const a = jv(from, id), b = jv(to, id); q.j[id] = [0, 1, 2].map(k => a[k] + (b[k] - a[k]) * t); }); return q; };
      // walk along the move so a part cannot jump through paper in one step
      let lo = 0, hi = null;
      for (let s = 1; s <= 6; s++) { if (collisions(rig, mix(s / 6), chain).n > base) { hi = s / 6; break; } lo = s / 6; }
      if (hi === null) return { pose: to, blocked: false };
      for (let it = 0; it < 7; it++) { const m = (lo + hi) / 2; if (collisions(rig, mix(m), chain).n <= base) lo = m; else hi = m; }
      return { pose: mix(lo), blocked: true };
    }

    // pull the parts that pass through paper back toward the standing pose until they no longer do
    function fixPose(rig, pose) {
      const stand = P({});
      let cur = clone(pose);
      for (let pass = 0; pass < 4; pass++) {
        const c = collisions(rig, cur);
        if (!c.n) break;
        const hit = new Set();
        c.pairs.forEach(([a, b]) => { hit.add(rig.facets[c.tris[a].fi].chain); hit.add(rig.facets[c.tris[b].fi].chain); });
        c.side.concat(c.floor).forEach(a => hit.add(rig.facets[c.tris[a].fi].chain));
        hit.delete('body');
        // move the smaller parts first: head/neck and tail, then wings
        const order = ['tail', 'neck', 'wB', 'wF'].filter(k => hit.has(k));
        if (!order.length) break;
        for (const ch of order) {
          const from = clone(cur);
          rig.chains[ch].joints.forEach(j => { from.j[j.id] = clone(jv(stand, j.id)); });
          if (collisions(rig, from, ch).n) continue;
          cur = blockAt(rig, from, cur, ch).pose;
          if (!collisions(rig, cur).n) break;
        }
      }
      return { pose: cur, left: collisions(rig, cur).n };
    }

    return { build, facetTransforms, pointPos, presets, collisions, blockAt, fixPose, LEDGE, restPoint, handlePos, handleInfo, solveIK, mirrorWing, P, expand, lerpPose, EASE, HANDLES, EPS, FLOOR, PIVOT, jv, clone };
  }

  const api = { create };
  if (typeof module !== 'undefined') module.exports = api; else root.CraneRig = api;
})(this);
