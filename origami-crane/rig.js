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
    const base = W.facets.map((f, i) => ({ poly: f.poly, T: W.Tend[i], h: W.h1[i], tag: f.tag || null, id: f.id }));
    const restOf = (f, p) => { const w = E.apply(f.T, [p[0], p[1], 0]); return [w[0], w[1]]; };
    const centroidRest = f => { let x = 0, y = 0; f.poly.forEach(p => { const r = restOf(f, p); x += r[0]; y += r[1]; }); return [x / f.poly.length, y / f.poly.length]; };
    let FLOOR = 1e9;
    base.forEach(f => { if (!fw.has(f.id) && !bw.has(f.id)) f.poly.forEach(p => { FLOOR = Math.min(FLOOR, restOf(f, p)[1]); }); });
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

    const wingJoints = k => [J(k + '0', [0, 1], [1, 0], [0, -1], 'wing', 3)].concat(
      [0.82, 0.66, 0.5, 0.34, 0.18].map((y, i) => J(k + (i + 1), [0, y], [1, 0], [0, -1], 'wing', 1)));
    const CHAINS = {
      wF: { name: '앞 날개', joints: wingJoints('wF'), a: [0, -1], tip: [0, 0] },
      wB: { name: '뒤 날개', joints: wingJoints('wB'), a: [0, -1], tip: [0, 0] },
      neck: {
        name: '목·머리', a: aN, tip: null,
        joints: [J('n0', M0, [-0.9087, -0.4171], aN, 'root', 2)]
          .concat([0.2, 0.35, 0.5, 0.65].map((f, i) => J('n' + (i + 1), atN(f), perp(aN), aN, 'bend', 2)))
          .concat([J('h', atN(0.8), mH, aN, 'head', 3)])
      },
      tail: {
        name: '꼬리', a: aT, tip: TIP.map((v, i) => i ? v : -v),
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
      let facets = base.map(f => Object.assign({}, f, { chain: chainOfBase(f), depth: 0 }));
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
      return { facets, chains, creaseEdges, jointChain, FLOOR, PIVOT, restOf };
    }

    // ---------- forward kinematics ----------
    const jv = (pose, id) => (pose.j && pose.j[id]) || [0, 0, 0];
    function jointT(j, v) {
      const p = [j.p[0], j.p[1], 0];
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
    function chainCums(rig, pose) {
      const B = bodyT(pose), out = { body: [B] };
      for (const key in rig.chains) {
        let T = B; out[key] = rig.chains[key].joints.map(j => (T = E.compose(T, jointT(j, jv(pose, j.id)))));
      }
      return out;
    }
    function facetTransforms(rig, pose) {
      const C = chainCums(rig, pose);
      return rig.facets.map(f => f.chain === 'body' ? C.body[0] : C[f.chain][f.depth]);
    }
    const EPS = 0.0022;
    const restPoint = (rig, f, p) => { const w = E.apply(f.T, [p[0], p[1], 0]); w[2] += f.h * EPS; return w; };

    // ---------- handles & IK ----------
    const HANDLES = {
      wF: { chain: 'wF', label: '앞 날개 끝' }, wB: { chain: 'wB', label: '뒤 날개 끝' },
      beak: { chain: 'neck', label: '부리' }, neck: { chain: 'neck', label: '목', upTo: 'h' },
      tail: { chain: 'tail', label: '꼬리 끝' }
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
        return j.id === 'wF0' ? [[-178, 0], LIM.wing0[1], LIM.wing0[2]] : [[0, 178], LIM.wing0[1], LIM.wing0[2]];
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
        const sg = X === 'F' ? -1 : 1, k = 'w' + X;
        j[k + '0'] = [sg * (90 + w.flap), -w.fwd, sg * w.twist];
        for (let i = 1; i <= 5; i++) j[k + i] = [sg * (w.curl / 5 + (i === 5 ? w.tip : 0)), 0, 0];
      });
      const n = Object.assign({ bow: 0, side: 0 }, sem.neck || {});
      j.n0 = [n.side * 0.4, n.bow * 0.4, 0];
      for (let i = 1; i <= 4; i++) j['n' + i] = [n.side * 0.15, n.bow * 0.15, 0];
      const h = Object.assign({ nod: 0, turn: 0, tilt: 0 }, sem.head || {});
      j.h = [h.turn, h.nod, h.tilt];
      const t = Object.assign({ up: 0, side: 0 }, sem.tail || {});
      j.t0 = [t.side * 0.5, t.up * 0.5, 0];
      for (let i = 1; i <= 4; i++) j['t' + i] = [t.side / 8, t.up / 8, 0];
      return { b: Object.assign({ x: 0, y: 0, z: 0, yaw: 0, pitch: 0, roll: 0 }, sem.b || {}), j };
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
            if (pose.j.wF0) pose.j.wF0[0] -= dF;
            if (pose.j.wB0) pose.j.wB0[0] += dB;
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
        M.push({ id: 'look', name: 'Look & Tilt — 발견·갸웃', cut: '2-2', desc: '창문 쪽으로 고개 돌림 → 갸웃 → 조금 더 기울임 → 정지', keys: [
          key('start', P(STAND), 4, { n: 4, ease: 'inout' }),
          key('prep', P({ neck: { bow: 8 }, head: { nod: 12 } }), 1, { n: 3, ease: 'snap' }),
          key('core', P(look), 3, { n: 3, ease: 'out' }),
          key('core', P(merge(look, { head: { tilt: 26 } })), 6, { n: 4, ease: 'inout' }),
          key('end', P(merge(look, { head: { tilt: 36, nod: -20 }, neck: { side: 28 }, b: { roll: 5 } })), 16, null)
        ] });
      }
      // Head Scratch
      {
        const prep = { neck: { bow: 2, side: 10 }, head: { nod: 34 }, b: { pitch: -4 }, wF: { flap: -8 } };
        const reach = merge(prep, { head: { tilt: 14 }, wF: { flap: 75, fwd: 60, curl: 30 } });
        const base = P(reach);
        const headTop = q => {
          const ch = rig.chains.neck, k = ch.joints.findIndex(j => j.id === 'h');
          return pointPos(rig, q, 'neck', k, ch.joints[k].p);
        };
        const touch = (dy) => {
          const q = clone(base), ht = headTop(q);
          solveIK(rig, q, 'wF', [ht[0] + 0.05, ht[1] + 0.07 + dy, ht[2] + 0.04], { iters: 80, mu: 2e-6 });
          return q;
        };
        const up = touch(0), down = touch(-0.07);
        M.push({ id: 'scratch', name: 'Head Scratch — 머리 긁기', cut: '2-7', desc: '고개 숙임 → 한쪽 날개를 머리에 댐 → 짧게 두 번 긁음 → 날개 내림', keys: [
          key('start', P(STAND), 3, { n: 5, ease: 'inout' }),
          key('prep', P(prep), 2, { n: 5, ease: 'inout' }),
          key('core', up, 3, { n: 1, ease: 'linear' }),
          key('core', down, 0, { n: 1, ease: 'linear' }),
          key('core', clone(up), 0, { n: 1, ease: 'linear' }),
          key('core', clone(down), 0, { n: 1, ease: 'linear' }),
          key('core', clone(up), 3, { n: 6, ease: 'inout' }),
          key('end', P({ neck: { bow: 14 }, head: { nod: 8 } }), 12, null)
        ] });
      }
      // Failed Takeoff
      {
        const proud = { wF: { flap: 78, curl: 18 }, wB: { flap: 78, curl: 18 }, neck: { bow: -18 }, head: { nod: -22 }, b: { pitch: 10 }, tail: { up: 8 } };
        M.push({ id: 'takeoff', name: 'Failed Takeoff — 이륙 실패', cut: '2-4', desc: '준비 자세 → 세찬 퍼덕임 → 짧은 점프 → 균형 상실 → 허우적거림 → 머리부터 추락', keys: [
          key('start', P(STAND), 3, { n: 5, ease: 'inout' }),
          key('prep', P({ b: { pitch: -8 }, neck: { bow: 16 }, head: { nod: 6 }, w: { flap: 4, fwd: -28, curl: 2 }, tail: { up: 12 } }), 3, { n: 3, ease: 'snap' }),
          key('core', P(proud), 8, { n: 10, ease: 'linear', flap: { cycles: 3, amp: 55, lag: 0, accel: 0.5 } }),
          key('core', P({ b: { y: 0.2, pitch: 6 }, w: { flap: 25, curl: 10 }, neck: { bow: -10 }, head: { nod: -12 }, tail: { up: 4 } }), 2, { n: 6, ease: 'linear', flap: { cycles: 3.5, amp: 60, lag: 0.22, accel: 1.2 } }),
          key('core', P({ b: { y: 0.15, z: 0.25, roll: 26, pitch: -14 }, wF: { flap: 55, curl: 12 }, wB: { flap: -10, curl: 6 }, neck: { bow: 22, side: -10 }, head: { nod: 18 }, tail: { up: 16 } }), 0, { n: 8, ease: 'linear', flap: { cycles: 4, amp: 62, lag: 0.4, accel: 1.6 } }),
          key('core', P({ b: { y: 0.12, z: 0.5, roll: 34, pitch: -32 }, wF: { flap: 35, curl: 8 }, wB: { flap: 20, curl: 4 }, neck: { bow: 46, side: -14 }, head: { nod: 30 }, tail: { up: 22 } }), 0, { n: 4, ease: 'in', wingLag: 0.45 }),
          key('end', P({ b: { y: -1.6, z: 1.0, roll: 40, pitch: -75 }, w: { flap: 70, curl: 26 }, neck: { bow: 30, side: -8 }, head: { nod: 20 }, tail: { up: 30 } }), 6, null)
        ] });
      }
      const rest = [
        ['wake', 'Wake Up — 깨어나기', '1-3', '고개 숙임 → 천천히 들어 올림 → 순간 멈춤'],
        ['prepfly', 'Prepare to Fly — 비행 준비', '2-3', '몸을 살짝 낮춤 → 목을 뻗음 → 양 날개를 크게 치켜듦 → 자신만만한 정지'],
        ['recover', 'Recover — 벌떡 일어나기', '2-6', '옆으로 누움 → 몸을 흔듦 → 갑자기 일어남 → 한 번 휘청 → 균형 잡기'],
        ['shake', 'Head Shake — 고개 털기', '2-7', '고개 좌우로 짧게 털기 → 마지막에 조금 지나쳤다가 돌아오기'],
        ['dodge', 'Dodge — 발 피하기', '2-8', '앞으로 이동 → 급정지 → 몸을 한쪽으로 기울임 → 급회전 → 반대쪽으로 도망'],
        ['deflate', 'Deflate — 낙담하기', '2-9', '움직임 멈춤 → 날개가 처짐 → 목과 몸이 내려감 → 주저앉음'],
        ['longing', 'Longing — 다시 올려다보기', '2-10', '축 처진 상태 → 고개만 조금 들어 창밖을 바라봄 → 긴 정지'],
        ['crushed', 'Crushed — 밟힌 상태', '3-2', '정상 형태 → 목·날개가 접히며 몸이 납작해짐. 외부 힘으로 변하는 별도 상태']
      ].map(([id, name, cut, desc]) => ({ id, name, cut, desc, draft: true, keys: [key('start', P(STAND), 6, null)] }));
      const order = ['wake', 'look', 'prepfly', 'takeoff', 'recover', 'shake', 'scratch', 'dodge', 'deflate', 'longing', 'crushed'];
      const all = M.concat(rest);
      return order.map(id => all.find(m => m.id === id));
    }

    return { build, facetTransforms, pointPos, presets, restPoint, handlePos, handleInfo, solveIK, mirrorWing, P, expand, lerpPose, EASE, HANDLES, EPS, FLOOR, PIVOT, jv, clone };
  }

  const api = { create };
  if (typeof module !== 'undefined') module.exports = api; else root.CraneRig = api;
})(this);
