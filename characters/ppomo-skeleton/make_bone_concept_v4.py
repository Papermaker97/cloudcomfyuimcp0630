"""
Ppomo skeleton concept v4: a small core with buttons on it, wrapped by curved bones that ARE the springs.

Why v4 exists
  v1-v3 pushed one far-away button through a long straight rod, so every bone had to slide straight in
  ("press", not "squeeze"), and each new problem got another part (rod, cones, stems, hubs, metal spring).
  v4 follows the things that already work:
    * Clicker Ball: a small core in the middle, switches facing outward, curved caps cover the surface
    * the printed clickers: the spring is the shape itself, printed flat so it bends inside the print plane
    * the owner's own model: fat curved bones that wrap a core

Three kinds of printed parts, each doing several jobs
  SKULL   one piece: the face (eyes, nose, mouth), the plug that closes the opening in the silicone,
          and the braincase that protects the board and battery.
  CORE    a small smooth pebble in the middle of the body with a short neck to the skull.
          It carries 5 tactile buttons (top, back, belly, left, right) and their wires; nothing in it moves,
          so the wires never bend.
  BONES   four curved bones wrap the core. Each one is fixed to the core at ONE end by a thin flat leaf
          and is free at the other end, like a clam: squeezing anywhere along it closes it onto its button.
          The bone is the press surface, the spring and the stop (it lands on the core) at the same time.
            spine  : from the neck, over the back, curling down round the rump = back + tail in one bone
            belly  : from under the rump forward to the chest (the other way round, so the bones interlock)
            sides  : from the shoulders back to the hips
          Each bone lies in one flat plane, so it prints lying on its side and bends inside the print plane
          (the direction the printed clickers survive in).

The rest shape of every bone is its closed shape rotated open about its leaf, so the gap grows toward the
free end and the whole bone closes at the same moment.

  python make_bone_concept_v4.py   -> bone-concept/v4/*.stl, checks, and ppomo-skeleton-viewer.html
Needs: pip install numpy scipy trimesh scikit-image fast-simplification
Written for the Ppomo project with help from Claude.
"""
import json
import os

import numpy as np
import trimesh
from scipy import ndimage

import make_bone_concept_v3 as v3
import make_head_layout as lay
import make_viewer as mv
from make_bone_concept import H, body_field, capsule, sminp

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "bone-concept", "v4")
C = np.array([0.0, 17.0, 22.0])            # core centre (x, y, z): the middle of the body
RX, RY, RZ = 9.0, 19.0, 7.5                # core half-sizes: 18 wide, 38 long, 15 tall
CLEAR = 0.8                                # bone-to-core clearance when fully squeezed
TRAVEL = 2.5                               # how far a bone closes at its button
BT = 2.6                                   # bone half-thickness (in its bending plane)
LEAF_T, FOLDS, FOLD_ARC = 0.8, 4, 9.5      # the root of each bone: a flat zigzag (4 folds over 9.5 mm), like the printed clickers
# bones: plane 'yz' (prints on its side, bends up/down) or 'xy' (bends in/out). Angles in degrees.
#   yz: 0 = tail end of the core, 90 = top, 180 = neck end, -90 = bottom
#   xy: 0 = tail end, 90 = right side, 180 = neck end, -90 = left side
BONES = {
    "spine": dict(plane="yz", a0=140, a1=0, sw=(95, 12), half=5.0, tip=3.4, beads=9.0),
    "belly": dict(plane="yz", a0=-58, a1=-142, sw=(-97,), half=7.0, tip=4.5, beads=0.0),
    "right": dict(plane="xy", a0=138, a1=62, sw=(84,), half=4.6, tip=3.6, beads=0.0),
    "left":  dict(plane="xy", a0=-138, a1=-62, sw=(-84,), half=4.6, tip=3.6, beads=0.0),
}


def on_ellipse(plane, ang, off):
    """a point at angle `ang` on the core's outline in that plane, pushed out by `off` mm, and the outward normal."""
    t = np.radians(ang)
    if plane == "yz":
        p = np.array([0.0, RY * np.cos(t), RZ * np.sin(t)])
        n = np.array([0.0, np.cos(t) / RY, np.sin(t) / RZ])
    else:
        p = np.array([RX * np.sin(t), RY * np.cos(t), 0.0])
        n = np.array([np.sin(t) / RX, np.cos(t) / RY, 0.0])
    n /= np.linalg.norm(n)
    return C + p + n * off, n


def ang_after(plane, a0, a1, arc):
    """the angle reached after walking `arc` mm along the core's outline from a0 toward a1."""
    step = 0.25 if a1 > a0 else -0.25
    a, walked = a0, 0.0
    prev = on_ellipse(plane, a, CLEAR + BT)[0]
    while walked < arc:
        a += step
        cur = on_ellipse(plane, a, CLEAR + BT)[0]
        walked += float(np.linalg.norm(cur - prev))
        prev = cur
    return a


def rot(P, hinge, plane, ang):
    """rotate points about the hinge, around the axis that sticks out of the bone's plane."""
    q = P - hinge
    c, s = np.cos(ang), np.sin(ang)
    out = np.empty_like(q)
    if plane == "yz":                     # about +x
        out[..., 0] = q[..., 0]
        out[..., 1] = q[..., 1] * c - q[..., 2] * s
        out[..., 2] = q[..., 1] * s + q[..., 2] * c
    else:                                 # about +z
        out[..., 0] = q[..., 0] * c - q[..., 1] * s
        out[..., 1] = q[..., 0] * s + q[..., 1] * c
        out[..., 2] = q[..., 2]
    return out + hinge


def closed_field(P, name):
    """the bone in its squeezed position: a chain of fat rounded beads following the core's outline."""
    b = BONES[name]
    w = np.array([1.0, 0, 0]) if b["plane"] == "yz" else np.array([0, 0, 1.0])     # out-of-plane direction
    d = np.full(P.shape[:-1], 99.0, np.float32)
    a_body = ang_after(b["plane"], b["a0"], b["a1"], FOLD_ARC)                    # the bone starts after its zigzag root
    n_s = int(abs(b["a1"] - a_body) / 4) + 1
    for i, ang in enumerate(np.linspace(a_body, b["a1"], n_s)):
        s = i / (n_s - 1)
        c, nrm = on_ellipse(b["plane"], ang, CLEAR + BT)
        tan = np.cross(w, nrm)
        half = b["half"] + (b["tip"] - b["half"]) * s ** 1.6                      # slimmer toward the free end
        half *= 0.72 + 0.28 * np.sin(np.pi * min(s * 1.25 + 0.12, 1.0)) ** 0.6    # rounded start and belly
        th = BT * (0.86 + 0.14 * np.sin(np.pi * s))
        if b["beads"]:                                                            # vertebra beads along the spine
            arc = s * n_s * 4 / 57.3 * (RY + RZ) / 2
            k = 0.5 + 0.5 * np.cos(2 * np.pi * arc / b["beads"])
            th *= 0.82 + 0.16 * k
            half *= 0.9 + 0.14 * k
        q = P - c
        e = (np.sqrt((q @ w / half) ** 2 + (q @ tan / 3.4) ** 2 + (q @ nrm / th) ** 2) - 1) * min(half, th, 3.4)
        d = sminp(d, e.astype(np.float32), 1.6)
    return d


def bone_setup(name):
    b = BONES[name]
    start, n0 = on_ellipse(b["plane"], ang_after(b["plane"], b["a0"], b["a1"], FOLD_ARC), CLEAR + BT)
    hinge, _ = on_ellipse(b["plane"], b["a0"], 0.0)                                  # the zigzag is fixed to the core here
    contact, _ = on_ellipse(b["plane"], b["sw"][0], CLEAR)
    lever = float(np.linalg.norm(contact - hinge))
    theta = TRAVEL / lever
    best = None
    for sgn in (1, -1):                   # opening direction: the one that lifts the bone away from the core
        r = rot(contact[None], hinge, b["plane"], -sgn * theta)[0]
        dist = np.linalg.norm((r - C) / np.array([RX, RY, RZ]))
        if best is None or dist > best[0]:
            best = (dist, sgn)
    return dict(hinge=hinge, start=start, theta=theta, sgn=best[1], lever=lever)


def bone_field(P, name, press=0.0):
    """press = 0 at rest (open), 1 fully squeezed."""
    st = bone_setup(name)
    ang = st["sgn"] * st["theta"] * (1 - press)
    Q = rot(P, st["hinge"], BONES[name]["plane"], ang)
    d = closed_field(Q, name)
    # the root: a flat zigzag between the core and the bone, thin in the bending plane, nearly as deep as the bone
    b = BONES[name]
    w = np.array([1.0, 0, 0]) if b["plane"] == "yz" else np.array([0, 0, 1.0])
    pts = [st["hinge"]]
    for k in range(1, 2 * FOLDS + 1):
        a = ang_after(b["plane"], b["a0"], b["a1"], FOLD_ARC * k / (2 * FOLDS + 1))
        pts.append(on_ellipse(b["plane"], a, 0.7 if k % 2 == 0 else CLEAR + 2 * BT - 0.7)[0])
    pts.append(st["start"])
    leaf = np.full(Q.shape[:-1], 99.0, np.float32)
    for a, b_ in zip(pts[:-1], pts[1:]):
        ab = b_ - a
        t = np.clip(((Q - a) @ ab) / (ab @ ab), 0, 1)
        rel = Q - (a + t[..., None] * ab)
        out = np.abs(rel @ w)
        inp = np.sqrt(np.maximum((rel ** 2).sum(-1) - out ** 2, 0))
        leaf = np.minimum(leaf, np.maximum(inp - LEAF_T / 2, out - b["half"] * 0.6).astype(np.float32))
    return np.minimum(d, leaf)


def core_field(P):
    q = (P - C) / np.array([RX, RY, RZ])
    d = (np.linalg.norm(q, axis=-1) - 1) * RZ
    neck0 = np.array([0.0, v3.POD["c"][1] + 8.0, 19.5])
    d = sminp(d, capsule(P, neck0, C + np.array([0, -RY + 3, 0]), 4.0), 3.0)      # short thick neck to the skull
    return d


def skull_field(P):
    d = v3.pod_field(P)
    return sminp(d, capsule(P, (0, v3.PLATE_BACK - 0.5, 18.5), (0, v3.POD["c"][1], 18.5), 8.0), 3.0)


def switch_meshes():
    """the tactile buttons on the core, as small boxes (body + plunger), for the viewer."""
    bodies, plungers = [], []
    for name, b in BONES.items():
        for ang in b["sw"]:
            p, n = on_ellipse(b["plane"], ang, 0.0)
            z = n
            x = np.array([1.0, 0, 0]) if b["plane"] == "yz" else np.array([0, 0, 1.0])
            y = np.cross(z, x)
            M = np.eye(4); M[:3, 0], M[:3, 1], M[:3, 2] = x, y, z
            for size, depth, store in (((6, 6, 3.5), -1.4, bodies), ((3.2, 3.2, 1.3), 0.95 - 0.0, plungers)):
                T = M.copy(); T[:3, 3] = p + n * depth
                m = trimesh.creation.box(extents=size); m.apply_transform(T); store.append(m)
    return trimesh.util.concatenate(bodies), trimesh.util.concatenate(plungers)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    lo = np.array([-40.0, -58.0, -2.0])
    Pb = mv.grid(lo, (40.0, 58.0, 54.0), H)
    D = ndimage.distance_transform_edt(body_field(Pb[..., 0], Pb[..., 1], Pb[..., 2]) < 0) * H
    sl = tuple(slice(int((a - lo[i]) / H), int((b - lo[i]) / H) + 1) for i, (a, b) in enumerate(((-26, 26), (-46, 52), (0, 46))))
    lo2 = np.array([lo[i] + sl[i].start * H for i in range(3)])
    P = Pb[sl]
    Dc = D[sl]
    del Pb

    core = core_field(P)
    skull = skull_field(P)
    rest = {n: bone_field(P, n, 0.0) for n in BONES}
    shut = {n: bone_field(P, n, 1.0) for n in BONES}
    names = list(BONES)

    # ---------------- checks ----------------
    ok = True
    solid = {n: f < 0 for n, f in rest.items()}
    closed = {n: f < 0 for n, f in shut.items()}
    cm = core < 0
    allm = cm | (skull < 0)
    for m in solid.values():
        allm |= m
    behind = P[..., 1] > v3.PLATE_BACK + 4
    bone_core = cm.copy()
    for m in solid.values():
        bone_core |= m
    idx = np.argwhere(bone_core)
    ext = (idx.max(0) - idx.min(0)) * H
    print(f"core + bones: {ext[0]:.0f} mm wide x {ext[1]:.0f} mm long x {ext[2]:.0f} mm tall   (body 75 x 110 x 52)")
    for n in names:
        v = Dc[solid[n]]
        st = bone_setup(n)
        print(f"  {n:5s} bone: silicone over it {v.min():4.1f} - {v.max():4.1f} mm | closes {TRAVEL} mm at its button by turning {np.degrees(st['theta']):.1f} deg about its leaf")
    wall = float(Dc[allm & behind].min())
    print(f"thinnest silicone anywhere: {wall:.1f} mm (want >= 5):", wall >= 5.0); ok &= wall >= 5.0

    def min_gap(masks):
        g = 99.0
        for i, a in enumerate(names):
            da = ndimage.distance_transform_edt(~masks[a]) * H
            for b in names[i + 1:]:
                g = min(g, float(da[masks[b]].min()))
        return g

    g0, g1 = min_gap(solid), min_gap(closed)
    print(f"space between bones: {g0:.1f} mm at rest, {g1:.1f} mm when all are squeezed (want >= 3):", g1 >= 3.0); ok &= g1 >= 3.0
    def body_mask(n, press):
        st_ = bone_setup(n)
        return closed_field(rot(P, st_["hinge"], BONES[n]["plane"], st_["sgn"] * st_["theta"] * (1 - press)), n) < 0

    pen = max(int((body_mask(n, 1.0) & cm).sum()) for n in names) * H ** 3
    print(f"squeezed bones land on the core without cutting into it: {pen:.1f} mm3 overlap (want < 3):", pen < 3.0); ok &= pen < 3.0
    dcore = ndimage.distance_transform_edt(~cm) * H
    for n in names:                                  # bone body only (the leaf touches the core on purpose)
        print(f"  {n:5s}: at rest the bone sits {float(dcore[body_mask(n, 0.0)].min()):.1f} mm off the core at its root, more toward the free end")
    # zigzag strain: FOLDS beams of length ~2*BT share the turn -> surface strain t*theta/(2*l*FOLDS)
    worst = max(LEAF_T * bone_setup(n)["theta"] / (2 * (2 * BT - 1.0) * FOLDS) for n in names)
    print(f"zigzag root bending strain at a full squeeze: about {worst * 100:.2f} % (PLA yields near 1.5 - 2 %; want < 0.5):", worst < 0.005); ok &= worst < 0.005
    per = lambda a, b: np.pi * (3 * (a + b) - np.sqrt((3 * a + b) * (a + 3 * b)))
    print(f"face opening 34 x 18 mm must stretch {per(ext[0] / 2, ext[2] / 2) / per(17, 9):.2f}x to let it through")
    print("ALL CHECKS OK" if ok else "CHECK FAILED")

    # ---------------- meshes + viewer ----------------
    meshes = {"skull": mv.slim(mv.mc(skull, H, lo2), 20000), "core": mv.slim(mv.mc(core, H, lo2), 16000)}
    for n in names:
        meshes["bone_" + n] = mv.slim(mv.mc(rest[n], H, lo2), 16000)
    for k, t in meshes.items():
        t.export(os.path.join(OUT, k.replace("_", "-") + ".stl"))
    sw_b, sw_p = switch_meshes()
    meshes["sw_body"], meshes["sw_plunger"] = sw_b, sw_p
    for n in ("plate", "ink"):
        meshes[n] = mv.slim(trimesh.load(os.path.join(mv.VIEW, n + ".stl"), process=True), 20000)
    h = 0.8
    Pbig = mv.grid(lo, (40.0, 58.0, 54.0), h)
    f = body_field(Pbig[..., 0], Pbig[..., 1], Pbig[..., 2])
    seat = ((Pbig[..., 0] / (mv.PLATE_A + 0.15)) ** 2 + ((Pbig[..., 2] - mv.PLATE_ZC) / (mv.PLATE_B + 0.15)) ** 2 < 1) & (Pbig[..., 1] < mv.Y_SKIN)
    meshes["body"] = mv.slim(mv.mc(np.where(seat, 1.0, f), h, lo), 60000)
    data = {k: mv.pack(t) for k, t in meshes.items()}
    movers = {}
    for n in names:
        st = bone_setup(n)
        movers[n] = dict(hinge=st["hinge"].tolist(), axis=[1, 0, 0] if BONES[n]["plane"] == "yz" else [0, 0, 1],
                         angle=float(-st["sgn"] * st["theta"]))
    neck0 = [0.0, v3.POD["c"][1] + 8.0, 19.5]
    wires = [[(1.5, C[1] - RY + 4, C[2] - 1), (1.8, neck0[1] + 3, 20.5), (2.5, -27.0, 18.0), (3.0, -31.0, 13.6)],
             [(-1.5, C[1] - RY + 4, C[2] - 1), (-1.8, neck0[1] + 3, 20.5), (-2.5, -27.0, 18.0), (-3.0, -30.0, 13.6)],
             [(6.0, -39.0, 15.6), (6.5, -38.0, 14.6), (7.0, -36.0, 13.6)],
             [(-6.0, -39.0, 15.6), (-6.5, -38.0, 14.6), (-7.0, -36.0, 13.6)]]
    cfg = dict(S=mv.S, YC=mv.YC, YF=mv.YF, movers=movers, wires=wires,
               parts={k: lay.PARTS[k] for k in ("board", "battery")})
    tpl = open(os.path.join(HERE, "viewer-template.html"), encoding="utf-8").read()
    html = tpl.replace("/*__MESHES__*/null", json.dumps(data)).replace("/*__CFG__*/null", json.dumps(cfg))
    out = os.path.join(HERE, "ppomo-skeleton-viewer.html")
    open(out, "w", encoding="utf-8").write(html)
    print("saved", out, f"({os.path.getsize(out) / 1e6:.1f} MB)")
