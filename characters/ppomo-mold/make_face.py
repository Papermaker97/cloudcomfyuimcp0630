"""
Add a face (two dot eyes, a small nose, an omega mouth) to the printable Ppomo v6 body.

The face is CARVED INTO the surface (shallow dimples and a groove), so:
  * the printed body shows the face without any support or fragile bumps
  * a mold made from this body gets small raised marks, and the silicone cast gets the same carved face
    (fill the dimples with dark silicone or paint later if you like)

Positions come from the 3D model (ppomo-v6.html: eyes at x = +-0.24, y = 0.42; mouth at y = 0.39),
converted to mm with the same scale the body STL uses. Each mark is placed by shooting a ray at the face,
so it follows the real curved surface.

  python make_face.py          -> ppomo-v6-face-110mm.stl
  python make_face.py mold     -> also mold-face-left.stl / mold-face-right.stl

Needs: pip install manifold3d trimesh numpy rtree
Written for the Ppomo project with help from Claude.
"""
import os
import sys

import numpy as np
import trimesh
from manifold3d import Manifold, Mesh

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "ppomo-v6-body-110mm.stl")
OUT = os.path.join(HERE, "ppomo-v6-face-110mm.stl")
S = 110.0 / (0.99658 + 1.11999)          # model units -> mm (the body is 110 mm long)
Y_FLOOR = 0.0355                          # model height of the flat bottom
EYE_X, EYE_Y = 0.24, 0.42
EYE_R, EYE_DEPTH, EYE_TALL = 2.6, 1.0, 1.15   # sphere radius, dimple depth (mm) -> ~4.1 x 4.7 mm dots
NOSE_W, NOSE_H, NOSE_DEPTH = 1.5, 1.05, 0.7   # small oval
NOSE_DROP = 2.0                           # nose centre below the eye centres (mm)
MOUTH_ARC = 1.7                           # radius of each half-circle of the omega (mm)
MOUTH_GROOVE = 0.55                       # groove radius (1.1 mm wide, 0.55 mm deep)
MOUTH_GAP = 1.0                           # mouth top below the nose centre (mm)


def to_manifold(t):
    return Manifold(Mesh(vert_properties=np.asarray(t.vertices, dtype=np.float32),
                         tri_verts=np.asarray(t.faces, dtype=np.uint32)))


def to_trimesh(m):
    mesh = m.to_mesh()
    return trimesh.Trimesh(np.asarray(mesh.vert_properties)[:, :3], np.asarray(mesh.tri_verts), process=False)


def surface(t, x, z):
    """first hit when looking at the face (from -Y toward +Y): point and outward normal."""
    loc, _, tri = t.ray.intersects_location([[x, t.bounds[0][1] - 10, z]], [[0, 1, 0]])
    i = int(np.argmin(loc[:, 1]))
    n = t.face_normals[tri[i]]
    return loc[i], n / np.linalg.norm(n)


def dimple(p, n, rx, rz, depth, r_unit=1.0):
    """an ellipsoid pushed into the surface by `depth` along the normal."""
    e = Manifold.sphere(r_unit, 48).scale([rx, (rx + rz) / 2, rz])
    c = p + n * ((rx + rz) / 2 - depth)
    return e.translate(c.tolist())


def build_face(t):
    eye_z = (EYE_Y - Y_FLOOR) * S
    cut = Manifold()
    marks = {}
    for side in (-1, 1):
        p, n = surface(t, side * EYE_X * S, eye_z)
        cut += dimple(p, n, EYE_R, EYE_R * EYE_TALL, EYE_DEPTH)
        marks["eye " + ("L" if side < 0 else "R")] = p
    nose_z = eye_z - NOSE_DROP
    p, n = surface(t, 0.0, nose_z)
    cut += dimple(p, n, NOSE_W * 2.2, NOSE_H * 2.2, NOSE_DEPTH)
    marks["nose"] = p
    # omega mouth: two lower half-circles side by side, hanging from a line just under the nose
    top_z = nose_z - NOSE_H - MOUTH_GAP
    groove = Manifold()
    for side in (-1, 1):
        cx = side * MOUTH_ARC
        pts = []
        for a in np.linspace(np.pi, 2 * np.pi, 13):          # lower half circle
            x, z = cx + MOUTH_ARC * np.cos(a), top_z + MOUTH_ARC * np.sin(a)
            pts.append(surface(t, x, z)[0])
        balls = [Manifold.sphere(MOUTH_GROOVE, 24).translate(q.tolist()) for q in pts]
        for a, b in zip(balls[:-1], balls[1:]):
            groove += Manifold.batch_hull([a, b])
    cut += groove
    marks["mouth top"] = surface(t, 0.0, top_z)[0]
    return cut, marks


if __name__ == "__main__":
    t = trimesh.load(SRC)
    body = to_manifold(t)
    cut, marks = build_face(t)
    out = body - cut
    removed = body.volume() - out.volume()
    ok = len(out.decompose()) == 1 and 5 < removed < 200
    to = to_trimesh(out)
    to.export(OUT)
    for k, v in marks.items():
        print(f"{k:10s} at mm {np.round(v, 1)}")
    print("carved volume mm3:", round(removed, 1), "| one piece:", len(out.decompose()) == 1,
          "| watertight:", to.is_watertight, "| size mm:", np.round(to.extents, 1))
    print("OK" if ok else "CHECK FAILED")
    if sys.argv[1:2] == ["mold"]:
        import make_mold
        make_mold.BODY_STL = OUT
        make_mold.make_mold()
        # make_mold writes over mold-left/right.stl: keep the face versions under new names, then restore the plain ones from git if needed
        for a, b in (("mold-left.stl", "mold-face-left.stl"), ("mold-right.stl", "mold-face-right.stl"),
                     ("mold-assembled-check.stl", "mold-face-assembled-check.stl")):
            os.replace(os.path.join(HERE, a), os.path.join(HERE, b))
