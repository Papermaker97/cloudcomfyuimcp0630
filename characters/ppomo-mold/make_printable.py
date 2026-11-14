"""
Make the Ppomo v6 body printable without supports.

Problem found on the printer: the underside of the body curves in so flatly that in the lowest 5 mm
each layer sticks out 0.4 - 4 mm past the layer below it (and at the very bottom it touches the bed in
6 small islands). Those layers are printed in the air, curl up, and the nozzle knocks the print off.

Fix: take the body's outline at 5 mm height and extend it STRAIGHT DOWN to the bed. The result has one
wide flat base (about 61 cm2) and vertical walls for the first 5 mm; everything above 5 mm is unchanged.
Only the tucked-under belly edge changes shape. (This is for a PLA shape print. The casting mold does not
need it: the mold halves print on their flat outer faces.)

  python make_printable.py   -> ppomo-v6-face-110mm-printable.stl   (prints its own check)
Needs: pip install manifold3d trimesh numpy shapely
Written for the Ppomo project with help from Claude.
"""
import os

import numpy as np
import shapely.affinity as A
import trimesh
from manifold3d import CrossSection, Manifold, Mesh
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "ppomo-v6-face-110mm.stl")
OUT = os.path.join(HERE, "ppomo-v6-face-110mm-printable.stl")
SKIRT_Z = 5.0          # below this height the walls go straight down
LAYER = 0.2
MAX_GROWTH = 0.30      # mm a layer may stick out past the one below (about 55 degrees) without support


def section(t, z):
    s, T = t.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1]).to_planar()
    g = unary_union(list(s.polygons_full))
    return A.affine_transform(g, [T[0, 0], T[0, 1], T[1, 0], T[1, 1], T[0, 3], T[1, 3]])


def worst_growth(t, z0, z1):
    worst, where = 0.0, 0.0
    prev = section(t, z0)
    for z in np.arange(z0 + LAYER, z1, LAYER):
        cur = section(t, z)
        polys = cur.geoms if cur.geom_type == "MultiPolygon" else [cur]
        g = max(p.exterior.hausdorff_distance(prev) for p in polys)
        if g > worst:
            worst, where = g, z
        prev = cur
    return worst, where


if __name__ == "__main__":
    t = trimesh.load(SRC)
    body = Manifold(Mesh(vert_properties=np.asarray(t.vertices, dtype=np.float32),
                         tri_verts=np.asarray(t.faces, dtype=np.uint32)))
    g = section(t, SKIRT_Z)
    polys = g.geoms if g.geom_type == "MultiPolygon" else [g]
    rings = []
    for p in polys:
        rings.append(np.asarray(p.exterior.coords)[:-1][::1 if p.exterior.is_ccw else -1].tolist())
    skirt = Manifold.extrude(CrossSection(rings), SKIRT_Z + 0.01)
    out = body + skirt
    m = out.to_mesh()
    o = trimesh.Trimesh(np.asarray(m.vert_properties)[:, :3], np.asarray(m.tri_verts), process=False)
    o.export(OUT)
    base = section(o, 0.1)
    islands = len(base.geoms) if base.geom_type == "MultiPolygon" else 1
    before, zb = worst_growth(t, 0.2, 12.0)
    after, za = worst_growth(o, 0.2, 12.0)
    ok = islands == 1 and after <= MAX_GROWTH and o.is_watertight and len(out.decompose()) == 1
    print(f"base: {base.area / 100:.1f} cm2 in {islands} piece(s)")
    print(f"worst overhang per layer in the lowest 12 mm: before {before:.2f} mm (at z = {zb:.1f}), after {after:.2f} mm (at z = {za:.1f})")
    print("size mm:", np.round(o.extents, 1), "| watertight:", o.is_watertight, "| one piece:", len(out.decompose()) == 1)
    print("OK: printable without supports" if ok else "CHECK FAILED")
