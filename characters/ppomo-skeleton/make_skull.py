"""
Ppomo skull v1: ONE rounded hollow bone that sits inside the head.

What the owner asked for (and what the earlier oval face plate got wrong)
  The skull is not a face plate with a plug and a box joined behind it, and it does not change the face.
  It is a single smooth bone shaped like the head, inside the head, with soft silicone around it:
    FACE     its front comes up through the silicone and lies flush with the face. Ppomo's own expression
             is on it: two small dot eyes, a small nose, the "w" mouth.
    PLUG     that front fills the opening the inside parts went in through. The round part behind it is
             much bigger than the opening, so it can neither pop out nor be pushed in.
    HOUSING  it is hollow. The board and the battery sit inside it, the way a skull holds a brain.
             The eyes, nose and mouth are shallow carvings filled dark, exactly as on the original face.
             (They could be made real holes later, to glimpse the board, as in the reference images.)
  Cheeks and ears stay silicone.

  python make_skull.py   -> bone-concept/skull-v1.stl, skull-v1-ink.stl and a list of checks
Needs: pip install numpy scipy trimesh scikit-image fast-simplification
Written for the Ppomo project with help from Claude.
"""
import os

import numpy as np
from scipy import ndimage

import make_head_layout as lay
import make_viewer as mv
from make_bone_concept import body_field

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "bone-concept")
h = 0.25                                   # grid, mm
S = 51.97
# the round part: the head's own ellipsoid, made smaller so silicone stays around it
CY, CZ = -31.0, 18.9                       # centre (y, z); x = 0
RX, RY, RZ = 24.0, 15.5, 14.8              # half-sizes: 48 wide, 31 long, about 30 tall
MIN_SIL = 4.5                              # never closer than this to the outside of the body
WALL = 1.6                                 # shell thickness
# the face: a rounded window in the silicone that the front of the skull fills
WIN_A, WIN_B, WIN_Z, WIN_E = 16.5, 9.0, 17.5, 2.6
UNDERCUT = 1.5                             # the front widens this much toward the inside, to key into the silicone
# Ppomo's own face (same numbers as ppomo-mold/make_face.py)
EYE_X, EYE_Z = 0.24 * S, (0.42 - 0.0355) * S
EYE_RX, EYE_RZ = 2.05, 2.35                # small dot eyes, about 4.1 x 4.7 mm across at the surface
EYE_R, EYE_DEPTH = (2.6, 2.8, 3.0), 1.0    # the dimple that makes them
NOSE_Z = EYE_Z - 2.0
NOSE_R = (3.3, 2.8, 2.31)
NOSE_DEPTH = 0.7
MOUTH_TOP = NOSE_Z - 1.05 - 1.0
MOUTH_ARC, MOUTH_GROOVE = 1.7, 0.55
PART_SHIFT = 2.0                           # the board and battery sit this much further back than in the old layout


def build():
    lo = np.array([-32.0, -58.0, -1.0])
    ax = [np.arange(lo[i], hi + h, h, dtype=np.float32) for i, hi in enumerate((32.0, -8.0, 44.0))]
    X, Y, Z = np.meshgrid(*ax, indexing="ij")
    body = body_field(X, Y, Z) < 0
    D = ndimage.distance_transform_edt(body).astype(np.float32) * h          # silicone depth below the skin
    cran = (((X / RX) ** 2 + ((Y - CY) / RY) ** 2 + ((Z - CZ) / RZ) ** 2) < 1) & (D >= MIN_SIL)
    grow = np.minimum(D, 6.0) / 6.0 * UNDERCUT
    win = (np.abs(X) / (WIN_A + grow)) ** WIN_E + (np.abs(Z - WIN_Z) / (WIN_B + grow)) ** WIN_E < 1
    boss = body & win & (Y < CY)
    solid = ndimage.gaussian_filter((cran | boss).astype(np.float32), 0.5 / h) > 0.5
    solid &= body
    cavity = ndimage.distance_transform_edt(solid) * h >= WALL
    shell = solid & ~cavity

    def surf(x, z):
        """the face surface at (x, z): the first point inside the body, looking from the front."""
        i, k = int(round((x - lo[0]) / h)), int(round((z - lo[2]) / h))
        j = int(np.argmax(body[i, :, k]))
        return np.array([x, lo[1] + j * h, z])

    carve = np.zeros(body.shape, bool)
    for side in (-1, 1):                                   # dot eyes: shallow dimples, filled dark, as on the original face
        p = surf(side * EYE_X, EYE_Z)
        c = p + np.array([0, -(EYE_R[1] - EYE_DEPTH), 0])
        carve |= ((X - c[0]) / EYE_R[0]) ** 2 + ((Y - c[1]) / EYE_R[1]) ** 2 + ((Z - c[2]) / EYE_R[2]) ** 2 < 1
    p = surf(0.0, NOSE_Z)
    c = p + np.array([0, -(NOSE_R[1] - NOSE_DEPTH), 0])
    carve |= ((X - c[0]) / NOSE_R[0]) ** 2 + ((Y - c[1]) / NOSE_R[1]) ** 2 + ((Z - c[2]) / NOSE_R[2]) ** 2 < 1
    for side in (-1, 1):                                   # the "w" mouth: two lower half-circles side by side
        for a in np.linspace(np.pi, 2 * np.pi, 40):
            q = surf(side * MOUTH_ARC + MOUTH_ARC * np.cos(a), MOUTH_TOP + MOUTH_ARC * np.sin(a))
            carve |= (X - q[0]) ** 2 + (Y - q[1]) ** 2 + (Z - q[2]) ** 2 < MOUTH_GROOVE ** 2
    ink = shell & carve
    shell = shell & ~carve
    return dict(lo=lo, X=X, Y=Y, Z=Z, body=body, D=D, solid=solid, cavity=cavity, shell=shell, ink=ink, win=win, boss=boss)


def parts():
    out = {}
    for k in ("board", "battery"):
        b = list(lay.PARTS[k])
        b[2] += PART_SHIFT; b[3] += PART_SHIFT
        out[k] = tuple(b)
    return out


def checks(g):
    ok = True
    lo, D = g["lo"], g["D"]
    idx = np.argwhere(g["shell"])
    ext = (idx.max(0) - idx.min(0)) * h
    print(f"skull: {ext[0]:.0f} mm wide x {ext[1]:.0f} mm long x {ext[2]:.0f} mm tall, shell {WALL} mm, one hollow piece")
    lab, n = ndimage.label(g["shell"])
    sizes = ndimage.sum(g["shell"], lab, range(1, n + 1))
    one = n >= 1 and sizes.max() / sizes.sum() > 0.999
    print("the face, the plug and the housing are one connected piece:", bool(one)); ok &= bool(one)
    round_part = g["shell"] & ~g["boss"]
    sil = float(D[round_part].min())
    print(f"silicone over the round part: at least {sil:.1f} mm (want >= 4):", sil >= 4.0); ok &= sil >= 4.0
    flush = float(D[g["shell"] & g["boss"]].min())
    print(f"the face part comes up flush with the skin (silicone over it {flush:.2f} mm, want 0):", flush <= 0.3); ok &= flush <= 0.3
    for name, b in parts().items():
        sl = tuple(slice(int(round((b[2 * i] - lo[i]) / h)), int(round((b[2 * i + 1] - lo[i]) / h)) + 1) for i in range(3))
        inside = bool(g["cavity"][sl].all())
        size = (b[1] - b[0], b[3] - b[2], b[5] - b[4])
        room = float((ndimage.distance_transform_edt(g["cavity"])[sl] * h).min())
        print(f"  {name:7s} {size[0]:4.1f} x {size[1]:4.1f} x {size[2]:4.1f} mm fits inside the skull, {room:.1f} mm from the wall at its tightest corner:", inside)
        ok &= inside
    vol = float(g["cavity"].sum()) * h ** 3 / 1000
    print(f"room inside the skull: about {vol:.1f} cm3")
    per = lambda a, b: np.pi * (3 * (a + b) - np.sqrt((3 * a + b) * (a + 3 * b)))
    stretch = per(ext[0] / 2, ext[2] / 2) / per(WIN_A, WIN_B)
    print(f"opening in the face {2 * WIN_A:.0f} x {2 * WIN_B:.0f} mm; the round part behind it is {ext[0]:.0f} x {ext[2]:.0f} mm, so the opening stretches {stretch:.2f}x to let it in and it cannot fall out")
    eye_edge = WIN_A - (EYE_X + EYE_RX)
    print(f"Ppomo's own face: dot eyes {2 * EYE_RX:.1f} x {2 * EYE_RZ:.1f} mm, {eye_edge:.1f} mm inside the edge of the face part:", eye_edge >= 1.5); ok &= eye_edge >= 1.5
    print("ALL CHECKS OK" if ok else "CHECK FAILED")
    return ok


def meshes(g):
    f = ndimage.gaussian_filter(g["shell"].astype(np.float32), 0.6)
    skull = mv.mc(f, h, g["lo"], level=0.5)
    ink = mv.mc(ndimage.gaussian_filter(g["ink"].astype(np.float32), 0.5), h, g["lo"], level=0.4)
    return skull, ink


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    g = build()
    checks(g)
    skull, ink = meshes(g)
    mv.slim(skull, 250000).export(os.path.join(OUT, "skull-v1.stl"))
    ink.export(os.path.join(OUT, "skull-v1-ink.stl"))
    print("saved", os.path.join(OUT, "skull-v1.stl"))
