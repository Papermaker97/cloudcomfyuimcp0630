"""
Ppomo skeleton concept v5: a small core with five buttons; five short curved bones sit ON their buttons.

What changed from v4 (each one answers a problem the owner found)
  SPRING BESIDE THE BUTTON  v4 hung each bone from a spring at its far end, so it tilted like a lever.
                            Now every bone has its button under its middle and a printed zigzag spring on
                            BOTH sides of the button, so it goes straight down wherever you squeeze it
                            (the same idea as the printed clickers and the Clicker Ball caps).
                            The zigzags sit in pockets sunk into the core.
  A TAIL BONE OF ITS OWN    the rump has its own bone and button. It wraps the rump from behind, round both hips.
                            The core ends in a wider cross-bar (a pelvis) to carry it.
  NO PLASTIC NECK           the core floats in its own pocket in the silicone. Only two slack wires and a pull
                            cord run to the skull, so the neck stays soft.
  SKULL                     face, plug and braincase are one piece: deep eye sockets, a nose opening, the mouth
                            groove and a seam down the forehead are carved into the bone itself.

  python make_bone_concept_v5.py   -> bone-concept/v5/*.stl, checks, and ppomo-skeleton-viewer.html
Needs: pip install numpy scipy trimesh scikit-image fast-simplification manifold3d rtree
Written for the Ppomo project with help from Claude.
"""
import json
import os
import sys

import numpy as np
import trimesh
from scipy import ndimage

import make_bone_concept_v3 as v3
import make_head_layout as lay
import make_viewer as mv
from make_bone_concept import H, body_field, sminp

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "bone-concept", "v5")
C = np.array([0.0, 13.0, 22.0])            # core centre: the middle of the body
RX, RY, RZ = 9.0, 20.0, 7.5                # core half-sizes: 18 wide, 40 long, 15 tall
PELVIS_C = C + np.array([0.0, RY - 3.0, 0.0])
PELVIS_R = (13.5, 5.0, 5.0)                # the wider cross-bar at the rear that carries the tail bone
CLEAR = 0.8                                # bone-to-core clearance when fully squeezed
TRAVEL = 2.0                               # how far a bone goes down onto its button
BT = 2.6                                   # bone half-thickness
POCKET = 5.2                               # depth of the spring pockets in the core
ZIG_T, ZIG_N = 0.6, 5                      # zigzag wall thickness (design value) and number of beams
ZIG_DRAWN = 0.8                            # drawn a little thicker so the 0.5 mm grid can show it
BTN_HALF = 3.5                             # half of the button + a little room, between the two springs
OUTLINES = {"core_yz": ("yz", C, RY, RZ), "core_xy": ("xy", C, RX, RY), "pelvis": ("xy", PELVIS_C, PELVIS_R[0], PELVIS_R[1])}
# bones: outline, angle of the button, zigzag beam length, half-width out of the bending plane (middle / ends)
#   yz outlines: 0 = tail end, 90 = top, -90 = bottom.   xy outlines: 0 = tail end, 90 = right, -90 = left
BONES = {
    "back":  dict(out="core_yz", at=92, beam=10.0, half=5.0, tip=3.6, beads=8.0),
    "belly": dict(out="core_yz", at=-92, beam=10.0, half=7.0, tip=4.6, beads=0.0),
    "right": dict(out="core_xy", at=108, beam=9.0, half=4.6, tip=3.4, beads=0.0),
    "left":  dict(out="core_xy", at=-108, beam=9.0, half=4.6, tip=3.4, beads=0.0),
    "tail":  dict(out="pelvis", at=0, beam=8.0, half=4.4, tip=3.4, beads=0.0),
}


def outline(name, ang, off=0.0):
    """point on an outline at `ang` degrees, pushed out by `off` mm; also the outward normal."""
    plane, c, r1, r2 = OUTLINES[name]
    t = np.radians(ang)
    if plane == "yz":
        p = np.array([0.0, r1 * np.cos(t), r2 * np.sin(t)])
        n = np.array([0.0, np.cos(t) / r1, np.sin(t) / r2])
    else:
        p = np.array([r1 * np.sin(t), r2 * np.cos(t), 0.0])
        n = np.array([np.sin(t) / r1, np.cos(t) / r2, 0.0])
    n /= np.linalg.norm(n)
    return c + p + n * off, n


def walk(name, a0, arc, off):
    """the angle reached after walking `arc` mm (signed) along the outline from a0."""
    step = 0.25 if arc > 0 else -0.25
    a, done = a0, 0.0
    prev = outline(name, a, off)[0]
    while done < abs(arc):
        a += step
        cur = outline(name, a, off)[0]
        done += float(np.linalg.norm(cur - prev))
        prev = cur
    return a


def frame(name):
    b = BONES[name]
    plane = OUTLINES[b["out"]][0]
    w = np.array([1.0, 0, 0]) if plane == "yz" else np.array([0, 0, 1.0])
    p0, n = outline(b["out"], b["at"])
    tan = outline(b["out"], b["at"] + 1)[0] - outline(b["out"], b["at"] - 1)[0]
    tan /= np.linalg.norm(tan)
    reach = BTN_HALF + b["beam"] + 3.0                   # the bone covers the button, both springs and a little more
    a0 = walk(b["out"], b["at"], -reach, CLEAR + BT)
    a1 = walk(b["out"], b["at"], reach, CLEAR + BT)
    return dict(w=w, p0=p0, n=n, tan=tan, a0=a0, a1=a1, reach=reach)


def cap_closed(P, name):
    """the bone in its squeezed position: fat rounded beads following the outline."""
    b, fr = BONES[name], frame(name)
    d = np.full(P.shape[:-1], 99.0, np.float32)
    n_s = max(int(2 * fr["reach"] / 2.2), 6)
    for i, ang in enumerate(np.linspace(fr["a0"], fr["a1"], n_s)):
        s = i / (n_s - 1)
        c, nrm = outline(b["out"], ang, CLEAR + BT)
        tan = np.cross(fr["w"], nrm)
        m = np.sin(np.pi * s) ** 0.55                    # plump in the middle, rounded at both ends
        half = b["tip"] + (b["half"] - b["tip"]) * m
        th = BT * (0.8 + 0.2 * m)
        if b["beads"]:                                   # vertebra beads along the back bone
            k = 0.5 + 0.5 * np.cos(2 * np.pi * (s * 2 * fr["reach"]) / b["beads"])
            th *= 0.86 + 0.14 * k
            half *= 0.9 + 0.12 * k
        q = P - c
        e = (np.sqrt((q @ fr["w"] / half) ** 2 + (q @ tan / 3.2) ** 2 + (q @ nrm / th) ** 2) - 1) * min(half, th, 3.2)
        d = sminp(d, e.astype(np.float32), 1.5)
    return d


def zig_points(name, side, press):
    """corner points of one zigzag spring (side = -1 or +1 of the button), from the pocket floor up into the bone."""
    b, fr = BONES[name], frame(name)
    tc = side * (BTN_HALF + b["beam"] / 2)
    top = CLEAR + TRAVEL * (1 - press)                   # the bone's underside above the core surface
    step = (POCKET + top) / ZIG_N
    pts = []
    for j in range(ZIG_N):
        r = -POCKET + 0.3 + j * step
        ends = (tc - b["beam"] / 2, tc + b["beam"] / 2) if j % 2 == 0 else (tc + b["beam"] / 2, tc - b["beam"] / 2)
        pts += [(ends[0], r), (ends[1], r)]
    pts.append((pts[-1][0], top + 1.0))                  # the last beam joins the bone
    return [fr["p0"] + fr["tan"] * t + fr["n"] * r for t, r in pts]


def ribbon(P, pts, w, depth, thick):
    d = np.full(P.shape[:-1], 99.0, np.float32)
    for a, b_ in zip(pts[:-1], pts[1:]):
        ab = b_ - a
        t = np.clip(((P - a) @ ab) / (ab @ ab), 0, 1)
        rel = P - (a + t[..., None] * ab)
        out = np.abs(rel @ w)
        inp = np.sqrt(np.maximum((rel ** 2).sum(-1) - out ** 2, 0))
        d = np.minimum(d, np.maximum(inp - thick / 2, out - depth).astype(np.float32))
    return d


def bone_field(P, name, press=0.0, springs=True):
    """press = 0 at rest, 1 fully squeezed: the bone slides straight down its button's axis."""
    fr = frame(name)
    d = cap_closed(P - fr["n"] * (TRAVEL * (1 - press)), name)
    if springs:
        for side in (-1, 1):
            d = np.minimum(d, ribbon(P, zig_points(name, side, press), fr["w"], BONES[name]["half"] * 0.55, ZIG_DRAWN))
    return d


def core_field(P):
    q = (P - C) / np.array([RX, RY, RZ])
    d = (np.linalg.norm(q, axis=-1) - 1) * RZ
    q = (P - PELVIS_C) / np.array(PELVIS_R)
    d = sminp(d, (np.linalg.norm(q, axis=-1) - 1) * PELVIS_R[2], 2.5)
    for name, b in BONES.items():                        # pockets for the zigzag springs
        fr = frame(name)
        rel = P - fr["p0"]
        t, r, o = rel @ fr["tan"], rel @ fr["n"], np.abs(rel @ fr["w"])
        for side in (-1, 1):
            tc = side * (BTN_HALF + b["beam"] / 2)
            inside = (np.abs(t - tc) < b["beam"] / 2 + 1.0) & (r > -POCKET) & (o < b["half"] * 0.55 + 0.7)
            d = np.where(inside, 1.0, d)
    return d


def skull_field(P):
    """the braincase behind the face: one rounded box that meets the back of the face."""
    d = v3.pod_field(P)
    q = P - np.array([0, v3.PLATE_BACK - 0.5, 18.5])
    neck = np.maximum(np.sqrt((q[..., 0] / 15.0) ** 2 + (q[..., 2] / 9.0) ** 2) - 1, np.abs(q[..., 1] - 4.0) / 5.0 - 1) * 5.0
    return sminp(d, neck, 3.0)


def switch_meshes():
    bodies, plungers = [], []
    for name in BONES:
        fr = frame(name)
        x, z = fr["w"], fr["n"]
        y = np.cross(z, x)
        M = np.eye(4); M[:3, 0], M[:3, 1], M[:3, 2] = x, y, z
        for size, depth, store in (((6, 6, 3.5), -1.3, bodies), ((3.2, 3.2, 1.2), 0.95, plungers)):
            T = M.copy(); T[:3, 3] = fr["p0"] + fr["n"] * depth
            m = trimesh.creation.box(extents=size); m.apply_transform(T); store.append(m)
    return trimesh.util.concatenate(bodies), trimesh.util.concatenate(plungers)


def build_skull_face():
    """the face of the skull: the same flush oval as before, carved like bone (sockets, nose opening, mouth, forehead seam)."""
    sys.path.insert(0, os.path.join(HERE, "..", "ppomo-mold"))
    import make_face as mf
    import make_faceplate as fp
    from manifold3d import Manifold
    mf.EYE_R, mf.EYE_DEPTH, mf.EYE_TALL = 3.5, 2.6, 1.2          # deep round eye sockets
    mf.NOSE_W, mf.NOSE_H, mf.NOSE_DEPTH = 1.3, 1.0, 1.6
    base_build = mf.build_face

    def skull_cut(t):
        cut, marks = base_build(t)
        eye_z = (mf.EYE_Y - mf.Y_FLOOR) * mf.S
        nose_z = eye_z - mf.NOSE_DROP
        for sx in (-1, 1):                                       # nose opening: two small lobes, like an upside-down heart
            p, n = mf.surface(t, sx * 1.1, nose_z + 0.7)
            cut += Manifold.sphere(1.5, 24).translate((p + n * 0.2).tolist())
        balls = []
        for z in np.linspace(eye_z + 4.0, fp.ZC + fp.B - 1.5, 7):  # seam down the forehead
            balls.append(Manifold.sphere(0.45, 16).translate(mf.surface(t, 0.0, z)[0].tolist()))
        for a, b in zip(balls[:-1], balls[1:]):
            cut += Manifold.batch_hull([a, b])
        return cut, marks

    mf.build_face = skull_cut
    plate, ink, silicone, body, cav, info = fp.build()
    return mf.to_trimesh(plate), mf.to_trimesh(ink)


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
    names = list(BONES)
    core = core_field(P)
    skull = skull_field(P)
    rest = {n: bone_field(P, n, 0.0) for n in names}
    cap0 = {n: bone_field(P, n, 0.0, springs=False) < 0 for n in names}
    cap1 = {n: bone_field(P, n, 1.0, springs=False) < 0 for n in names}
    cm = core < 0

    # ---------------- checks ----------------
    ok = True
    allm = cm | (skull < 0)
    grp = cm.copy()
    for m in cap0.values():
        allm |= m
        grp |= m
    idx = np.argwhere(grp)
    ext = (idx.max(0) - idx.min(0)) * H
    print(f"core + bones: {ext[0]:.0f} mm wide x {ext[1]:.0f} mm long x {ext[2]:.0f} mm tall   (body 75 x 110 x 52)")
    for n in names:
        v = Dc[cap0[n]]
        b = BONES[n]
        strain = 3 * ZIG_T * (TRAVEL / ZIG_N) / b["beam"] ** 2
        print(f"  {n:5s} bone: silicone over it {v.min():4.1f} - {v.max():4.1f} mm | two zigzags of {ZIG_N} beams x {b['beam']:.0f} mm, bending strain about {strain * 100:.2f} %")
        ok &= strain < 0.012
    print("    (the printed clicker that is still springing back after a day of play: roughly 0.9 % by the same formula, from its measured walls)")
    behind = P[..., 1] > v3.PLATE_BACK + 4
    wall = float(Dc[allm & behind].min())
    print(f"thinnest silicone anywhere: {wall:.1f} mm (want >= 5):", wall >= 5.0); ok &= wall >= 5.0

    def min_gap(masks):
        g, who = 99.0, None
        for i, a in enumerate(names):
            da = ndimage.distance_transform_edt(~masks[a]) * H
            for b in names[i + 1:]:
                v = float(da[masks[b]].min())
                if v < g:
                    g, who = v, (a, b)
        return g, who

    (g0, w0), (g1, w1) = min_gap(cap0), min_gap(cap1)
    print(f"space between bones: {g0:.1f} mm at rest ({w0[0]}/{w0[1]}), {g1:.1f} mm when all are squeezed ({w1[0]}/{w1[1]}) (want >= 3):", g1 >= 3.0); ok &= g1 >= 3.0
    solid_core = (core_field(P) < 0)
    pen = {n: int((cap1[n] & solid_core).sum()) * H ** 3 for n in names}
    print("squeezed bones stop on the core without cutting into it:", {k: round(v, 1) for k, v in pen.items()}, max(pen.values()) < 3.0); ok &= max(pen.values()) < 3.0
    per = lambda a, b: np.pi * (3 * (a + b) - np.sqrt((3 * a + b) * (a + 3 * b)))
    print(f"face opening 34 x 18 mm must stretch {per(ext[0] / 2, ext[2] / 2) / per(17, 9):.2f}x to let the core and bones through")
    print("ALL CHECKS OK" if ok else "CHECK FAILED")

    if "--checks" in sys.argv:
        sys.exit(0)
    # ---------------- meshes + viewer ----------------
    meshes = {"skull": mv.slim(mv.mc(skull, H, lo2), 20000), "core": mv.slim(mv.mc(core, H, lo2), 24000)}
    for n in names:
        meshes["bone_" + n] = mv.slim(mv.mc(rest[n], H, lo2), 16000)
    for k, t in meshes.items():
        t.export(os.path.join(OUT, k.replace("_", "-") + ".stl"))
    meshes["sw_body"], meshes["sw_plunger"] = switch_meshes()
    plate, ink = build_skull_face()
    plate.export(os.path.join(OUT, "skull-face.stl"))
    meshes["plate"], meshes["ink"] = mv.slim(plate, 24000), mv.slim(ink, 8000)
    h = 0.8
    Pbig = mv.grid(lo, (40.0, 58.0, 54.0), h)
    f = body_field(Pbig[..., 0], Pbig[..., 1], Pbig[..., 2])
    seat = ((Pbig[..., 0] / (mv.PLATE_A + 0.15)) ** 2 + ((Pbig[..., 2] - mv.PLATE_ZC) / (mv.PLATE_B + 0.15)) ** 2 < 1) & (Pbig[..., 1] < mv.Y_SKIN)
    meshes["body"] = mv.slim(mv.mc(np.where(seat, 1.0, f), h, lo), 60000)
    data = {k: mv.pack(t) for k, t in meshes.items()}
    movers = {n: dict(dir=(-frame(n)["n"]).tolist(), dist=TRAVEL) for n in names}
    front = C + np.array([0, -RY + 1.0, 0])
    wires = []
    for sx in (-1, 1):                                   # two slack wires from the core to the board in the skull
        wires.append([(sx * 1.5, front[1], front[2]), (sx * 4.0, front[1] - 5, front[2] + 3.0), (sx * -1.5, front[1] - 9, front[2] - 3.0),
                      (sx * 3.0, -22.0, 20.0), (sx * 3.0, -27.0, 17.0), (sx * 3.0, -31.0, 13.6)])
        wires.append([(sx * 6.0, -39.0, 15.6), (sx * 6.5, -38.0, 14.6), (sx * 7.0, -36.0, 13.6)])
    cord = [(0.0, front[1], front[2] + 2.0), (0.0, front[1] - 7, front[2] + 4.5), (0.0, -21.5, 24.0)]
    cfg = dict(S=mv.S, YC=mv.YC, YF=mv.YF, movers=movers, wires=wires, cord=cord,
               parts={k: lay.PARTS[k] for k in ("board", "battery")})
    tpl = open(os.path.join(HERE, "viewer-template.html"), encoding="utf-8").read()
    html = tpl.replace("/*__MESHES__*/null", json.dumps(data)).replace("/*__CFG__*/null", json.dumps(cfg))
    out = os.path.join(HERE, "ppomo-skeleton-viewer.html")
    open(out, "w", encoding="utf-8").write(html)
    print("saved", out, f"({os.path.getsize(out) / 1e6:.1f} MB)")
