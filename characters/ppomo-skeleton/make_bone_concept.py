"""
Ppomo bone clicker: LOOK-ONLY concept (nothing moves yet).

What it shows
  * the ivory face plate (the plug with the eyes, nose, mouth) continues into a short thick neck
  * a rounded spine tube runs along the body (this is where the rod with two cones will live)
  * four press pads (top, bottom, left, right) shaped like smooth "peanut" bone ends:
    two round lobes, one over each cone ring, and a waist between them.
    Thick, no thin ribs to snap, every edge rounded so the silicone is not cut.
  * the top pad has three low bumps down its middle, like a spine
  * a round tailbone knob at the back (the back press)
Shapes are blended like metaballs so there are no sharp edges anywhere.

  python make_bone_concept.py   -> bone-concept/bone-core.stl, bone-pads.stl (in the body's coordinates)
It also checks that the whole thing fits inside the Ppomo v6 body with enough silicone around it.

Needs: pip install numpy trimesh scikit-image rtree
Written for the Ppomo project with help from Claude.
"""
import os

import numpy as np
import trimesh
from skimage import measure

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "bone-concept")
BODY = os.path.join(HERE, "..", "ppomo-mold", "ppomo-v6-body-110mm.stl")
H = 0.4                    # grid size, mm
ZC = 20.0                  # height of the spine axis in the body
Y_FACE = -44.2             # back of the face plate
Y_RING = (-14.0, 14.0)     # the two cone rings = the two lobes of every pad
CORE_R = 6.5
PAD_R = 12.0               # pad centre distance from the axis
LOBE = (8.2, 10.5, 3.0)    # lobe half-sizes: across, along, thick
WAIST = (5.5, 13.0, 2.5)
STEM_R = 3.0
TAIL_Y = 31.0


def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b + (a - b) * h - k * h * (1 - h)


def ell(P, c, r):
    q = (P - np.asarray(c)) / np.asarray(r)
    return (np.linalg.norm(q, axis=-1) - 1.0) * min(r)


def capsule(P, a, b, r):
    a, b = np.asarray(a, float), np.asarray(b, float)
    ab = b - a
    t = np.clip(((P - a) @ ab) / (ab @ ab), 0, 1)
    return np.linalg.norm(P - (a + t[..., None] * ab), axis=-1) - r


def grid(lo, hi):
    ax = [np.arange(lo[i], hi[i] + H, H) for i in range(3)]
    X, Y, Z = np.meshgrid(*ax, indexing="ij")
    return np.stack([X, Y, Z], -1), np.asarray(lo, float)


def mesh(field, lo):
    v, f, _, _ = measure.marching_cubes(field, 0.0, spacing=(H, H, H))
    t = trimesh.Trimesh(v + lo, f[:, ::-1], process=True)
    trimesh.repair.fix_normals(t)
    return t


DIRS = {"top": (0, 1), "bottom": (0, -1), "right": (1, 0), "left": (-1, 0)}   # (x, z) unit vectors


def core_field(P):
    d = capsule(P, (0, Y_FACE - 1, 17.5), (0, Y_FACE + 9, ZC), 5.5)             # neck from the face plate
    d = smin(d, capsule(P, (0, Y_FACE + 9, ZC), (0, 24, ZC), CORE_R), 3.0)       # spine tube
    for y in (Y_FACE + 10, 25.0):                                                # joint knuckles at both ends
        d = smin(d, ell(P, (0, y, ZC), (8.0, 4.5, 8.0)), 2.5)
    d = smin(d, ell(P, (0, TAIL_Y, ZC), (6.5, 7.0, 6.5)), 3.0)                   # tailbone knob
    d = smin(d, ell(P, (0, TAIL_Y + 6.5, ZC - 1.5), (3.2, 4.0, 3.2)), 2.5)
    for ux, uz in DIRS.values():                                                 # stems up to the pads
        for y in Y_RING:
            a = (ux * (CORE_R - 1), y, ZC + uz * (CORE_R - 1))
            b = (ux * PAD_R, y, ZC + uz * PAD_R)
            d = smin(d, capsule(P, a, b, STEM_R), 1.2)
    return d


def pad_field(P, name):
    ux, uz = DIRS[name]
    tx, tz = -uz, ux                                   # across-the-pad direction
    c = np.array([ux * PAD_R, 0.0, ZC + uz * PAD_R])
    Q = P - c
    L = np.stack([Q[..., 0] * tx + Q[..., 2] * tz, Q[..., 1], Q[..., 0] * ux + Q[..., 2] * uz], -1)   # across, along, out
    d = ell(L, (0, np.mean(Y_RING), 0), WAIST)
    for y in Y_RING:
        d = smin(d, ell(L, (0, y, 0), LOBE), 3.5)
    if name == "top":                                  # three low bumps down the middle, like a spine
        for y in np.linspace(Y_RING[0] + 3, Y_RING[1] - 3, 3):
            d = smin(d, ell(L, (0, y, 1.7), (2.6, 3.0, 1.7)), 1.5)
    return d


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    P, lo = grid((-20, Y_FACE - 8, ZC - 20), (20, TAIL_Y + 14, ZC + 20))
    core = mesh(core_field(P), lo)
    pads = [mesh(pad_field(P, n), lo) for n in DIRS]
    pad_all = trimesh.util.concatenate(pads)
    core.export(os.path.join(OUT, "bone-core.stl"))
    pad_all.export(os.path.join(OUT, "bone-pads.stl"))
    whole = trimesh.util.concatenate([core, pad_all])
    print("bone concept size mm (x, y, z):", np.round(whole.extents, 1))
    # fit: thinnest silicone between the bones and the outside of the body
    body = trimesh.load(BODY)
    pts = whole.vertices[::40]
    d = []
    for i in range(0, len(pts), 400):
        d.extend(trimesh.proximity.signed_distance(body, pts[i:i + 400]))
    d = np.asarray(d)
    back = pts[:, 1] > Y_FACE + 6                      # behind the neck (the neck meets the face plate on purpose)
    wall = float(d[back].min())
    worst = pts[back][int(np.argmin(d[back]))]
    print(f"thinnest silicone over the bones: {wall:.1f} mm at {np.round(worst, 1)} (want >= 4):", wall >= 4.0)
    gap = min(np.linalg.norm(pads[0].vertices[::25][:, None] - pads[2].vertices[::25][None], axis=-1).min(), 99)
    print(f"gap between neighbouring pads: {gap:.1f} mm (want <= 1 or >= 4):", gap >= 4.0 or gap <= 1.0)
    print("OK" if wall >= 4.0 and (gap >= 4.0 or gap <= 1.0) else "CHECK FAILED")
