"""
Ppomo bone clicker: concept v3 (look + clearances; the mechanism inside the hubs is not modelled yet).

Design decisions (and why)
  SMALL        about 34 mm wide inside a 75 mm body: like a squeaker in a toy, the hand first sinks
               into soft silicone, then finds the click. (v2 filled the body and killed the squish.)
  NO BOX       the push rod itself is the spine and stays visible. It only needs two small hubs
               ("vertebrae") that guide the rod and the four stems, joined to the head pod by two slim rails.
  HEAD POD     the only closed part: button, board, battery sit right behind the face plate,
               where nobody squeezes.
  PLUMP BONES  the four press parts are not plates. Each is a fat rounded body, thick in section,
               swelling into knuckles and necking between them, so there is no thin edge to snap
               or to cut the silicone, and the spaces between bones are open round valleys, not slits.
  EACH ONE DIFFERENT
               back  : three knuckles in a row that climb toward the rump = the spine line
               belly : the widest and flattest = the part you press most on a doll
               sides : two knuckles (shoulder, hip) that sweep upward toward the back and bow out at the flank
  INTERLOCK    back/belly knuckles sit beside the side bones' waists and the other way round,
               so the bones nest instead of leaving an empty ring.
  ROUND TAIL   one wide dome at the end of the rod = the back press.

  python make_bone_concept_v3.py  -> bone-concept/v3/*.stl  (body coordinates, mm) and a list of checks
Needs: pip install numpy scipy trimesh scikit-image
Written for the Ppomo project with help from Claude.
"""
import os

import numpy as np
from scipy import ndimage

import make_bone_concept as base
from make_bone_concept import H, body_field, capsule, sminp, to_mesh

OUT = os.path.join(base.HERE, "bone-concept", "v3")
AX_Z = 20.2                  # height of the rod axis
TRAVEL = 3.5
HUB_Y = (-2.0, 20.0)         # the two vertebra hubs (later: the two cones)
HUB_R = 4.5
ROD_R = 3.0
BONE_R = HUB_R + 0.5 + TRAVEL + 3.0            # bone centreline distance from the axis (underside clears the hub when pressed)
PLATE_BACK = -43.3
POD = dict(c=(0.0, -32.0, 18.5), r=(14.0, 11.0, 9.5))
TAIL = dict(c=(0.0, 41.0, AX_Z), r=(8.0, 5.5, 8.0))
BONES = {
    #        direction   y-span        knuckles         half-width knuckle/waist   half-thickness knuckle/waist
    "back":  dict(u=(0, 1), span=(-17.0, 35.0), kn=(-13.0, 9.0, 31.0), a=(5.0, 2.3), b=(3.0, 2.1)),
    "belly": dict(u=(0, -1), span=(-17.0, 35.0), kn=(-13.0, 9.0, 31.0), a=(6.4, 2.9), b=(2.8, 2.1)),
    "right": dict(u=(1, 0), span=(-9.0, 27.0), kn=(-2.0, 20.0), a=(4.6, 2.2), b=(3.0, 2.1)),
    "left":  dict(u=(-1, 0), span=(-9.0, 27.0), kn=(-2.0, 20.0), a=(4.6, 2.2), b=(3.0, 2.1)),
}


def bone_centre(name, y):
    """centreline point of a bone at length y: (x, z)."""
    b = BONES[name]
    ux, uz = b["u"]
    tx, tz = -uz, ux
    s = (y - b["span"][0]) / (b["span"][1] - b["span"][0])          # 0 at the head end, 1 at the tail end
    r, sway = BONE_R, 0.0
    if name == "back":
        r += 3.5 * s ** 1.5                                         # climbs toward the rump like the body
    elif name == "belly":
        pass                                                        # belly stays low and flat
    else:
        r += 1.6 * np.sin(np.pi * s)                                # bows out at the flank
        sway = (s - 0.5) * 3.0 * (1 if name == "right" else -1)     # shoulder low, hip high
    return ux * r + tx * sway, AX_Z + uz * r + tz * sway


def bone_field(P, name):
    b = BONES[name]
    ux, uz = b["u"]
    tx, tz = -uz, ux
    d = np.full(P.shape[:-1], 99.0, np.float32)
    ys = np.arange(b["span"][0] + 2.5, b["span"][1] - 2.4, 2.0)
    for y in ys:
        bump = max(np.exp(-((y - k) / 3.8) ** 2) for k in b["kn"])
        a = b["a"][1] + (b["a"][0] - b["a"][1]) * bump
        th = b["b"][1] + (b["b"][0] - b["b"][1]) * bump
        cx, cz = bone_centre(name, y)
        qx, qy, qz = P[..., 0] - cx, P[..., 1] - y, P[..., 2] - cz
        lt, lr = qx * tx + qz * tz, qx * ux + qz * uz
        e = (np.sqrt((lt / a) ** 2 + (qy / 3.6) ** 2 + (lr / th) ** 2) - 1) * min(a, th, 3.6)
        d = sminp(d, e.astype(np.float32), 2.0)
    return d


def ellip(P, c, r):
    q = (P - np.asarray(c)) / np.asarray(r)
    return (np.linalg.norm(q, axis=-1) - 1) * min(r)


def frame_field(P):
    """head pod, visible rod, two hubs, two slim rails, tail dome (everything that does not move sideways)."""
    d = ellip(P, POD["c"], POD["r"])                                              # closed pod behind the face plate
    d = sminp(d, capsule(P, (0, PLATE_BACK - 0.5, 18.5), (0, POD["c"][1], 18.5), 8.0), 3.0)
    rod = capsule(P, (0, POD["c"][1], AX_Z), (0, TAIL["c"][1], AX_Z), ROD_R)
    d = sminp(d, rod, 1.5)
    for hy in HUB_Y:                                                              # vertebra hubs: a bead with four short guides
        d = sminp(d, ellip(P, (0, hy, AX_Z), (HUB_R, 4.2, HUB_R)), 1.5)
        for ux, uz in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            d = sminp(d, capsule(P, (0, hy, AX_Z), (ux * (HUB_R - 2.4), hy, AX_Z + uz * (HUB_R - 2.4)), 2.9), 1.0)
    for sx in (-1, 1):                                                            # two slim rails, upper diagonals
        a = (sx * 3.3, POD["c"][1] + 6, AX_Z + 3.3)
        b_ = (sx * 3.3, HUB_Y[1], AX_Z + 3.3)
        d = sminp(d, capsule(P, a, b_, 1.7), 1.0)
    d = sminp(d, ellip(P, (0, TAIL["c"][1] - 6.5, AX_Z), (4.6, 3.0, 4.6)), 1.5)   # small bead before the dome
    d = sminp(d, ellip(P, TAIL["c"], TAIL["r"]), 2.5)                             # one wide round tail dome
    return d


def stem_field(P, name):
    b = BONES[name]
    ux, uz = b["u"]
    d = np.full(P.shape[:-1], 99.0, np.float32)
    for hy in HUB_Y:
        cx, cz = bone_centre(name, hy)
        d = np.minimum(d, capsule(P, (ux * HUB_R, hy, AX_Z + uz * HUB_R), (cx, hy, cz), 2.4).astype(np.float32))
    return d


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    lo = np.array([-40.0, -58.0, -2.0])
    ax = [np.arange(lo[i], hi + H, H) for i, hi in enumerate((40.0, 58.0, 54.0))]
    X, Y, Z = np.meshgrid(*ax, indexing="ij")
    D = ndimage.distance_transform_edt(body_field(X, Y, Z) < 0) * H             # silicone above each point
    del X, Y, Z
    # work box around the skeleton
    sl = tuple(slice(int((a - lo[i]) / H), int((b - lo[i]) / H) + 1) for i, (a, b) in enumerate(((-26, 26), (-46, 52), (0, 46))))
    lo2 = np.array([lo[i] + sl[i].start * H for i in range(3)])
    ax2 = [np.arange(s.stop - s.start) * H + lo2[i] for i, s in enumerate(sl)]
    P = np.stack(np.meshgrid(*ax2, indexing="ij"), -1).astype(np.float32)
    Dc = D[sl]

    frame = frame_field(P)
    bones = {n: sminp(bone_field(P, n), stem_field(P, n), 2.6) for n in BONES}
    bone_only = {n: bone_field(P, n) < 0 for n in BONES}
    to_mesh(frame, 0.0, lo2).export(os.path.join(OUT, "frame.stl"))
    for n, f in bones.items():
        to_mesh(f, 0.0, lo2).export(os.path.join(OUT, f"bone-{n}.stl"))

    # ---------------- checks ----------------
    ok = True
    solid = {n: f < 0 for n, f in bones.items()}
    fr = frame < 0
    allm = fr.copy()
    for m in solid.values():
        allm |= m
    idx = np.argwhere(allm)
    ext = (idx.max(0) - idx.min(0)) * H
    print(f"skeleton size: {ext[0]:.0f} mm wide x {ext[1]:.0f} mm long x {ext[2]:.0f} mm tall  (body: 75 x 110 x 52)")
    behind = P[..., 1] > PLATE_BACK + 4
    for n, m in list(bone_only.items()) + [("frame", fr)]:
        v = Dc[m & behind]
        print(f"  silicone over {n:6s}: {v.min():4.1f} - {v.max():4.1f} mm")
    wall = min(Dc[m & behind].min() for m in list(solid.values()) + [fr])
    print(f"thinnest silicone anywhere: {wall:.1f} mm (want >= 5):", wall >= 5.0); ok &= wall >= 5.0
    names = list(BONES)

    def min_gap(masks):
        g = 99.0
        for i, a in enumerate(names):
            da = ndimage.distance_transform_edt(~masks[a]) * H
            for b in names[i + 1:]:
                g = min(g, float(da[masks[b]].min()))
        return g

    g0 = min_gap(bone_only)
    print(f"valley between bones at rest: at least {g0:.1f} mm wide (want >= 4):", g0 >= 4.0); ok &= g0 >= 4.0
    k = int(round(TRAVEL / H))
    shift = {"back": (2, -k), "belly": (2, k), "right": (0, -k), "left": (0, k)}
    moved = {n: np.roll(solid[n], shift[n][1], shift[n][0]) for n in names}
    moved_b = {n: np.roll(bone_only[n], shift[n][1], shift[n][0]) for n in names}
    hit = 0
    for i, a in enumerate(names):
        c = int((moved_b[a] & fr).sum()); hit += c
        if c:
            print(f"  !! pressed {a} bone hits the frame: {c * H ** 3:.1f} mm3")
        for b in names[i + 1:]:
            c = int((moved_b[a] & moved_b[b]).sum()); hit += c
            if c:
                print(f"  !! pressed {a} and {b} overlap: {c * H ** 3:.1f} mm3")
    print(f"all four pressed {TRAVEL} mm together: nothing collides:", hit == 0); ok &= hit == 0
    g1 = min_gap(moved_b)
    print(f"valley between bones with all four pressed: at least {g1:.1f} mm (want >= 3, so silicone is not pinched):", g1 >= 3.0); ok &= g1 >= 3.0
    df = ndimage.distance_transform_edt(~fr) * H
    under = min(float(df[moved_b[n]].min()) for n in names)
    print(f"pressed bones stay {under:.1f} mm clear of the rod, hubs and rails")
    per = lambda a, b: np.pi * (3 * (a + b) - np.sqrt((3 * a + b) * (a + 3 * b)))
    print(f"face opening 34 x 18 mm vs skeleton {ext[0]:.0f} x {ext[2]:.0f} mm: stretch {per(ext[0] / 2, ext[2] / 2) / per(17, 9):.2f}x")
    print("ALL CHECKS OK" if ok else "CHECK FAILED")
