"""
Ppomo bone clicker: LOOK-ONLY concept v2 (nothing moves yet).

v1 was four identical flat peanuts on a stick. v2 takes the pads FROM THE BODY ITSELF:
  * make an inner copy of Ppomo's own surface, a fixed silicone thickness below the skin
  * cut that inner surface into four pads (back, belly, left, right) along wavy seams
  * every pad is therefore different and organic: the back pad slopes up toward the rump,
    the belly pad is the biggest and nearly flat, the side pads wrap round the flanks
  * the seams are S-curves: where a side pad bulges (shoulder, hip) the back and belly pads are
    narrow, and at the flank the back and belly pads bulge into the side pads' waists.
    So the "peanut" in/out curves interlock and no ring of empty space is left.
  * a row of low beads runs down the back pad like a spine
  * the tail is one wide round dome (the back press), not a spike
  * the spine tube, neck and face plate are the same idea as v1

The script also checks numbers that matter later:
  silicone thickness, the gap along the seams, and that two or four pads pressed 3.5 mm
  at the same time do not hit each other or the spine tube.

  python make_bone_concept.py   -> bone-concept/bone-core.stl, bone-pad-*.stl (in the body's coordinates)
Needs: pip install numpy scipy trimesh scikit-image
Written for the Ppomo project with help from Claude.
"""
import os

import numpy as np
import trimesh
from scipy import ndimage
from skimage import measure

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "bone-concept")
H = 0.5                      # grid, mm
S, YC, YF = 51.97, 3.21, 0.0355          # model units -> mm (same as the body STL)
ZC = 19.5                    # spine axis height
T_SKIN, T_BELLY = 8.0, 6.0   # silicone over the back/side pads and over the belly pad
TH = 3.5                     # pad thickness
TRAVEL = 3.5
PAD_Y = (-22.0, 34.0)        # pads run from behind the head to the rump
SEAM0, SEAM_AMP, SEAM_P = 30.0, 11.0, 38.0   # seam angle (deg from horizontal), wave size, wave length
SEAM_PEAK = -12.0            # y where the side pads are widest (shoulder); next peak is the hip
GAP = 5.5                    # gap along the seams (>= 4 so silicone is not pinched)
CORE_R = 5.0
RINGS = (-8.0, 20.0)         # where the stems (later: plungers on the two cones) sit
Y_FACE = -44.0
TAIL = (0.0, 41.0, ZC)

SHAPE = dict(head=(0, .40, .52, .65, .40, .46), torso=(0, .48, -.25, .72, .48, .66), rump=(0, .55, -.45, .43),
             cheek=(.36, .30, .78, .21), ear=(.31, .80, .52, .155, .155, .08, .18), belly=(0, .18, -.10, .66, .20, .85),
             paw=(.50, .09, .70, .11), foot=(.52, .09, -.86, .11), butt=(.27, .42, -.76, .36))
BLEND = dict(body=.12, rump=.30, cheek=.10, ear=.06, leg=.07, belly=.14, butt=.12, floor=.10)


def smin(a, b, k):
    h = np.maximum(k - np.abs(a - b), 0) / k
    return np.minimum(a, b) - h * h * k * 0.25


def ell(x, y, z, c):
    cx, cy, cz, rx, ry, rz = c
    return (np.sqrt(((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 + ((z - cz) / rz) ** 2) - 1) * min(rx, ry, rz)


def sph(x, y, z, cx, cy, cz, r):
    return np.sqrt((x - cx) ** 2 + (y - cy) ** 2 + (z - cz) ** 2) - r


def body_field(X, Y, Z):
    """the Ppomo v6 body (same formula as ppomo-v6.html), evaluated at print coordinates in mm."""
    x, y, z = X / S, Z / S + YF, -(Y + YC) / S
    d = smin(ell(x, y, z, SHAPE["head"]), smin(ell(x, y, z, SHAPE["torso"]), sph(x, y, z, *SHAPE["rump"]), BLEND["rump"]), BLEND["body"])
    d = smin(d, ell(x, y, z, SHAPE["belly"]), BLEND["belly"])
    cx, cy, cz, cr = SHAPE["cheek"]
    ex, ey, ez, erx, ery, erz, tilt = SHAPE["ear"]
    for s in (-1, 1):
        d = smin(d, sph(x, y, z, s * cx, cy, cz, cr), BLEND["cheek"])
        c_, s_ = np.cos(s * tilt), np.sin(s * tilt)
        lx = (x - ex * s) * c_ + (y - ey) * s_
        ly = -(x - ex * s) * s_ + (y - ey) * c_
        d = smin(d, (np.sqrt((lx / erx) ** 2 + (ly / ery) ** 2 + ((z - ez) / erz) ** 2) - 1) * erz * 0.9, BLEND["ear"])
        d = smin(d, sph(x, y, z, SHAPE["paw"][0] * s, *SHAPE["paw"][1:]), BLEND["leg"])
        d = smin(d, sph(x, y, z, SHAPE["foot"][0] * s, *SHAPE["foot"][1:]), BLEND["leg"])
        d = smin(d, sph(x, y, z, SHAPE["butt"][0] * s, *SHAPE["butt"][1:]), BLEND["butt"])
    return -smin(-d, (y - 0.035), BLEND["floor"])


def capsule(P, a, b, r):
    a, b = np.asarray(a, float), np.asarray(b, float)
    ab = b - a
    t = np.clip(((P - a) @ ab) / (ab @ ab), 0, 1)
    return np.linalg.norm(P - (a + t[..., None] * ab), axis=-1) - r


def sminp(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b + (a - b) * h - k * h * (1 - h)


def to_mesh(field, level, lo):
    v, f, _, _ = measure.marching_cubes(field, level, spacing=(H, H, H))
    t = trimesh.Trimesh(v + lo, f, process=True)
    if t.volume < 0:
        t.invert()
    return t


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    lo = np.array([-40.0, -58.0, -2.0])
    ax = [np.arange(lo[i], hi + H, H) for i, hi in enumerate((40.0, 58.0, 54.0))]
    X, Y, Z = np.meshgrid(*ax, indexing="ij")
    inside = body_field(X, Y, Z) < 0
    D = ndimage.distance_transform_edt(inside) * H                 # mm of silicone above each point

    # ---- the four pads: bands of the inner surface, split along wavy seams ----
    phi = np.degrees(np.arctan2(np.abs(Z - ZC), np.abs(X)))        # 0 = sideways, 90 = straight up/down
    seam = SEAM0 + SEAM_AMP * np.cos(2 * np.pi * (Y - SEAM_PEAK) / SEAM_P)
    arc = np.radians(phi - seam) * np.hypot(X, Z - ZC)             # mm from the seam (+ = back/belly side)
    in_y = (Y > PAD_Y[0]) & (Y < PAD_Y[1])
    band = (D >= T_SKIN) & (D < T_SKIN + TH)
    band_belly = (D >= T_BELLY) & (D < T_BELLY + TH)
    masks = {
        "back": band & in_y & (Z > ZC) & (arc > GAP / 2),
        "belly": band_belly & in_y & (Z < ZC) & (arc > GAP / 2),
        "right": band & in_y & (X > 0) & (arc < -GAP / 2),
        "left": band & in_y & (X < 0) & (arc < -GAP / 2),
    }
    # spine beads down the middle of the back pad, following its slope
    ix0 = int(round((0 - lo[0]) / H))
    for yb in np.arange(PAD_Y[0] + 7, PAD_Y[1] - 6, 8.5):
        iy = int(round((yb - lo[1]) / H))
        col = np.where(D[ix0, iy, :] >= T_SKIN)[0]
        zt = lo[2] + col.max() * H                                 # outer face of the back pad here
        bead = ((X / 3.4) ** 2 + ((Y - yb) / 3.4) ** 2 + ((Z - zt + 0.6) / 2.6) ** 2) < 1
        masks["back"] |= bead & (D >= T_SKIN - 1.6)
    sig = 1.2 / H
    soft = {n: ndimage.gaussian_filter(m.astype(np.float32), sig) for n, m in masks.items()}
    pads = {n: to_mesh(f, 0.5, lo) for n, f in soft.items()}
    solid = {n: f > 0.5 for n, f in soft.items()}

    # ---- neck, spine tube, tail dome, stems ----
    sub = (slice(None, None, 1),) * 3
    P = np.stack([X, Y, Z], -1)
    d = capsule(P, (0, Y_FACE - 1, 18.5), (0, Y_FACE + 9, ZC), 5.0)
    d = sminp(d, capsule(P, (0, Y_FACE + 9, ZC), (0, TAIL[1] - 4, ZC), CORE_R), 3.0)
    for yk in (Y_FACE + 10, PAD_Y[1] + 1.0):
        q = (P - np.array([0, yk, ZC])) / np.array([6.2, 4.0, 6.2])
        d = sminp(d, (np.linalg.norm(q, axis=-1) - 1) * 4.0, 2.5)
    q = (P - np.array(TAIL)) / np.array([8.0, 5.5, 8.0])           # tail: one wide round dome
    d = sminp(d, (np.linalg.norm(q, axis=-1) - 1) * 5.5, 3.0)
    core_only = d < 0
    stems = np.full(d.shape, 99.0, np.float32)
    for name, (ux, uz) in {"back": (0, 1), "belly": (0, -1), "right": (1, 0), "left": (-1, 0)}.items():
        for yr in RINGS:
            iy = int(round((yr - lo[1]) / H))
            if ux == 0:
                line = np.where(solid[name][ix0, iy, :])[0]
                end = (0, yr, lo[2] + (line.min() if uz > 0 else line.max()) * H)
            else:
                iz = int(round((ZC - lo[2]) / H))
                line = np.where(solid[name][:, iy, iz])[0]
                end = (lo[0] + (line.min() if ux > 0 else line.max()) * H, yr, ZC)
            stems = np.minimum(stems, capsule(P, (ux * (CORE_R - 1), yr, ZC + uz * (CORE_R - 1)), end, 2.6))
    core = to_mesh(sminp(d, stems, 1.0), 0.0, lo)

    core.export(os.path.join(OUT, "bone-core.stl"))
    for n, t in pads.items():
        t.export(os.path.join(OUT, f"bone-pad-{n}.stl"))

    # ---- checks ----
    ok = True
    whole = trimesh.util.concatenate([core] + list(pads.values()))
    ext = whole.extents
    print("skeleton size mm (x, y, z):", np.round(ext, 1))
    for n, t in pads.items():
        e = t.extents
        print(f"  pad {n:6s}: {e[0]:5.1f} x {e[1]:5.1f} x {e[2]:5.1f} mm, area ~{t.area / 2 / 100:5.1f} cm2")
    allmask = core_only.copy()
    for m in solid.values():
        allmask |= m
    behind_neck = Y > Y_FACE + 8
    wall = D[allmask & behind_neck].min()
    for n_, m_ in list(solid.items()) + [("core", core_only)]:
        print(f"  silicone over {n_:6s}: min {D[m_ & behind_neck].min():.1f} mm")
    print(f"thinnest silicone over the skeleton: {wall:.1f} mm (want >= 5):", wall >= 5.0); ok &= wall >= 5.0
    names = list(solid)
    gmin = 99.0
    for i, a in enumerate(names):
        da = ndimage.distance_transform_edt(~solid[a]) * H
        for b in names[i + 1:]:
            gmin = min(gmin, da[solid[b]].min())
    print(f"smallest gap between two pads at rest: {gmin:.1f} mm (want >= 3.5):", gmin >= 3.5); ok &= gmin >= 3.5
    k = int(round(TRAVEL / H))
    moved = {"back": np.roll(solid["back"], -k, 2), "belly": np.roll(solid["belly"], k, 2),
             "right": np.roll(solid["right"], -k, 0), "left": np.roll(solid["left"], k, 0)}
    hit = 0
    for i, a in enumerate(names):
        c = int((moved[a] & core_only).sum()); hit += c
        if c:
            print(f"  !! pressed {a} pad hits the spine tube: {c * H ** 3:.1f} mm3")
        for b in names[i + 1:]:
            c = int((moved[a] & moved[b]).sum()); hit += c
            if c:
                print(f"  !! pressed {a} and {b} pads overlap: {c * H ** 3:.1f} mm3")
    print(f"all four pads pressed {TRAVEL} mm at once: overlapping volume {hit * H ** 3:.1f} mm3 (want 0):", hit == 0); ok &= hit == 0
    gp = 99.0
    for i, a in enumerate(names):
        da = ndimage.distance_transform_edt(~moved[a]) * H
        for b in names[i + 1:]:
            gp = min(gp, da[moved[b]].min())
    print(f"smallest gap between pads when all are pressed: {gp:.1f} mm")
    sec = np.pi * (3 * (ext[0] / 2 + ext[2] / 2) - np.sqrt((3 * ext[0] / 2 + ext[2] / 2) * (ext[0] / 2 + 3 * ext[2] / 2)))
    op = np.pi * (3 * (17 + 9) - np.sqrt((3 * 17 + 9) * (17 + 3 * 9)))
    print(f"face opening 34 x 18 mm must stretch about {sec / op:.1f}x to let the skeleton through (silicone stretches several times)")
    print("OK" if ok else "CHECK FAILED")
