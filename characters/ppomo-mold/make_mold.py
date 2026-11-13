"""
Ppomo v6 -> printable body + two-part casting mold.

Step 1 (body):  python make_mold.py body <body.json from ppomo-v6.html exportBody()>
  writes ppomo-v6-body-110mm.stl   (solid Ppomo, 110 mm long, flat bottom on the bed)
Step 2 (mold):  python make_mold.py mold
  writes mold-left.stl, mold-right.stl   (already oriented: outer flat side on the bed, cavity facing up)

How the mold works
  * Ppomo has a flat bottom, so the mold is a block with Ppomo's shape hollowed out and the
    flat bottom left OPEN. Flip the closed mold upside down: the open face is now on top. Pour there.
  * The block is split down the middle (left / right halves) so the soft silicone comes out easily.
  * 4 pins on the left half drop into 4 holes on the right half so the halves line up.
    Hold the halves together with tape, rubber bands or 2 clamps while pouring.

Coordinates of the STLs (mm): X = Ppomo's left/right, Y = length (face toward -Y), Z = up, floor at Z = 0.
Needs: pip install manifold3d trimesh numpy
Written for the Ppomo project with help from Claude.
"""
import json
import os
import sys

import numpy as np
import trimesh
from manifold3d import Manifold, Mesh

HERE = os.path.dirname(os.path.abspath(__file__))
BODY_STL = os.path.join(HERE, "ppomo-v6-body-110mm.stl")
LENGTH_MM = 110.0          # Ppomo's length, nose to butt
WALL = 8.0                 # mold wall around the body
PIN_R, PIN_H, PIN_CLEAR = 2.5, 4.0, 0.3
SILICONE_DENSITY = 1.07    # g/cm3 (Ecoflex range)


def make_body(json_path):
    d = json.load(open(json_path))
    p = np.array(d["pos"], dtype=float).reshape(-1, 3)
    f = np.array(d["idx"], dtype=np.int64).reshape(-1, 3)
    # web model (x, y-up, z-forward) -> print (x, -z, y): face toward -Y, Z up
    v = np.column_stack([p[:, 0], -p[:, 2], p[:, 1]])
    s = LENGTH_MM / (v[:, 1].max() - v[:, 1].min())
    v *= s
    v[:, 2] -= v[:, 2].min()                       # sit on the bed
    v[:, 0] -= (v[:, 0].max() + v[:, 0].min()) / 2
    v[:, 1] -= (v[:, 1].max() + v[:, 1].min()) / 2
    t = trimesh.Trimesh(v, f, process=True)
    trimesh.repair.fix_normals(t)
    t.export(BODY_STL)
    print("body:", BODY_STL)
    print("  watertight:", t.is_watertight, "| size mm:", np.round(t.extents, 1),
          "| volume cm3:", round(t.volume / 1000, 1),
          "| silicone for a solid cast ~", round(t.volume / 1000 * SILICONE_DENSITY), "g")


def to_manifold(t):
    return Manifold(Mesh(vert_properties=np.asarray(t.vertices, dtype=np.float32),
                         tri_verts=np.asarray(t.faces, dtype=np.uint32)))


def to_trimesh(m):
    mesh = m.to_mesh()
    return trimesh.Trimesh(np.asarray(mesh.vert_properties)[:, :3], np.asarray(mesh.tri_verts), process=False)


def box(x0, x1, y0, y1, z0, z1):
    return Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def make_mold():
    body_t = trimesh.load(BODY_STL)
    body = to_manifold(body_t)
    (x0, y0, z0), (x1, y1, z1) = body_t.bounds
    X0, X1, Y0, Y1 = x0 - WALL, x1 + WALL, y0 - WALL, y1 + WALL
    Z0, Z1 = 0.0, z1 + WALL                      # block starts at Ppomo's flat bottom: that face stays open
    block = box(X0, X1, Y0, Y1, Z0, Z1) - body
    pins = [(Y0 + WALL / 2, Z0 + 8), (Y1 - WALL / 2, Z0 + 8), (Y0 + WALL / 2, Z1 - 6), (Y1 - WALL / 2, Z1 - 6)]

    def pin(y, z, r, h):                         # a short cylinder along +X starting at x = 0
        return Manifold.cylinder(h, r, r, 32).rotate([0, 90, 0]).translate([0, y, z])

    left = block ^ box(X0 - 1, 0, Y0 - 1, Y1 + 1, Z0 - 1, Z1 + 1)
    right = block ^ box(0, X1 + 1, Y0 - 1, Y1 + 1, Z0 - 1, Z1 + 1)
    for y, z in pins:
        left += pin(y, z, PIN_R, PIN_H)
        right -= pin(y, z, PIN_R + PIN_CLEAR, PIN_H + 0.6)
    print("overlap left/right (mm3):", round((left ^ right).volume(), 3))

    # print orientation: outer flat side on the bed, open cavity (and the left half's pins) facing up
    tl = to_trimesh(left)
    tl.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, [0, 1, 0]))
    tl.apply_translation(-tl.bounds[0])
    tr = to_trimesh(right)
    tr.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
    tr.apply_translation(-tr.bounds[0])
    for name, t in (("mold-left.stl", tl), ("mold-right.stl", tr)):
        t.export(os.path.join(HERE, name))
        print(name, "watertight:", t.is_watertight, "| size mm:", np.round(t.extents, 1),
              "| plastic volume cm3:", round(t.volume / 1000, 1))
    # assembled view for checking
    trimesh.util.concatenate([to_trimesh(left), to_trimesh(right)]).export(os.path.join(HERE, "mold-assembled-check.stl"))


if __name__ == "__main__":
    if sys.argv[1:2] == ["body"]:
        make_body(sys.argv[2])
    elif sys.argv[1:2] == ["mold"]:
        make_mold()
    else:
        print(__doc__)
