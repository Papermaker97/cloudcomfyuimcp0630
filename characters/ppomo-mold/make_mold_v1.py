"""
Ppomo casting mold, VERSION 1: a solid squishy (no parts inside), the same shape as the printed v6 body with its face.

How it works
  * The mold is a block with Ppomo hollowed out, split down the middle (left / right halves).
  * Ppomo's flat bottom is left OPEN. Turn the closed mold upside down: the open face is on top and is the
    pour opening. Fill to the brim and scrape flat. (Checked: in this position no air gets trapped anywhere.)
  * A TONGUE runs around the cavity on the left half and sits in a GROOVE on the right half. It lines the
    halves up (no separate pins) and keeps the thin silicone from leaking out through the seam.
  * Two FLANGES (front and back) with 4 bolt holes for M4 bolts (16-20 mm) and nuts, like the box molds in
    the examples. The flanges also give clamps something to grip.

Writes mold-v1-solid/:
  mold-v1-left.stl, mold-v1-right.stl   (print lying on their outer side, cavity facing up; PLA or PETG)
  mold-v1-assembled.stl                 (both halves in place, for checking only)
  mold-v1-preview.png
Uses ppomo-v6-face-110mm.stl (the printed body with the carved face).
Needs: pip install manifold3d trimesh numpy pillow
Written for the Ppomo project with help from Claude.
"""
import os

import numpy as np
import trimesh
from manifold3d import CrossSection, JoinType, Manifold, Mesh

HERE = os.path.dirname(os.path.abspath(__file__))
BODY = os.path.join(HERE, "ppomo-v6-face-110mm.stl")
OUT = os.path.join(HERE, "mold-v1-solid")
WALL = 10.0                       # mold wall around the body (top, sides, front, back)
TONGUE = (3.0, 5.5, 2.0)          # the tongue: from 3 to 5.5 mm out from the cavity edge, 2 mm tall
GAP = 0.25                        # clearance around the tongue in the groove
FLANGE = 16.0                     # how far the flanges reach out in front and behind
BOLT_R, NUT_R, KEEP = 2.25, 4.6, 6.0   # M4 clearance hole, nut/washer pocket, solid plastic left at the seam
SILICONE_DENSITY = 1.07


def to_manifold(t):
    return Manifold(Mesh(vert_properties=np.asarray(t.vertices, dtype=np.float32), tri_verts=np.asarray(t.faces, dtype=np.uint32)))


def to_trimesh(m):
    mesh = m.to_mesh()
    return trimesh.Trimesh(np.asarray(mesh.vert_properties)[:, :3], np.asarray(mesh.tri_verts), process=False)


def box(x0, x1, y0, y1, z0, z1):
    return Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def ring_in_x(section, r0, r1, x0, x1, zmax):
    """a band around the body's outline in the x = 0 plane, r0..r1 mm out from it, spanning x0..x1."""
    band = section.offset(r1, JoinType.Round) - section.offset(r0, JoinType.Round)
    band = band ^ CrossSection.square([zmax, 400.0]).translate([0.0, -200.0])     # keep z >= 0 (section x' = z)
    m = Manifold.extrude(band, x1 - x0)          # along z' (= -x in the body frame)
    m = m.translate([0, 0, -x1])                 # z' from -x1 to -x0  ->  x from x0 to x1
    return m.rotate([0, -90, 0])


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    bt = trimesh.load(BODY)
    body = to_manifold(bt)
    (bx0, by0, bz0), (bx1, by1, bz1) = bt.bounds
    X0, X1, Y0, Y1, Z0, Z1 = bx0 - WALL, bx1 + WALL, by0 - WALL, by1 + WALL, 0.0, bz1 + WALL

    # the outline of the body where the mold splits (x = 0): rotate so x becomes the slicing axis
    section = body.rotate([0, 90, 0]).slice(0.0)          # coordinates (z, y) of the body

    # the cavity: the body, plus its floor outline pushed down through the bottom face so the bottom is really open
    floor = Manifold.extrude(body.slice(0.4), 3.0).translate([0, 0, -2.6])
    block = box(X0, X1, Y0 - FLANGE, Y1 + FLANGE, Z0, Z1) - (body + floor)
    left = block ^ box(X0 - 1, 0, Y0 - FLANGE - 1, Y1 + FLANGE + 1, -1, Z1 + 1)
    right = block ^ box(0, X1 + 1, Y0 - FLANGE - 1, Y1 + FLANGE + 1, -1, Z1 + 1)

    # tongue on the left half (sticks out into +x), groove in the right half
    tongue = ring_in_x(section, TONGUE[0], TONGUE[1], 0.0, TONGUE[2], Z1)
    groove = ring_in_x(section, TONGUE[0] - GAP, TONGUE[1] + GAP, 0.0, TONGUE[2] + 0.4, Z1)
    left = left + tongue
    right = right - groove

    # 4 bolt holes through the flanges, with a pocket from each outer side for the bolt head / nut
    bolts = [(yy, zz) for yy in (Y0 - FLANGE / 2, Y1 + FLANGE / 2) for zz in (Z0 + 12.0, Z1 - 10.0)]
    for yy, zz in bolts:
        hole = Manifold.cylinder(X1 - X0 + 4, BOLT_R, BOLT_R, 32).rotate([0, 90, 0]).translate([X0 - 2, yy, zz])
        pl = Manifold.cylinder(-KEEP - X0 + 1, NUT_R, NUT_R, 6).rotate([0, 90, 0]).translate([X0 - 1, yy, zz])
        pr = Manifold.cylinder(X1 - KEEP + 1, NUT_R, NUT_R, 6).rotate([0, 90, 0]).translate([KEEP, yy, zz])
        left = left - hole - pl
        right = right - hole - pr

    overlap = (left ^ right).volume()
    print(f"left/right overlap {overlap:.2f} mm3 (want 0)")
    print(f"body {bt.volume / 1000:.0f} cm3 -> about {bt.volume / 1000 * SILICONE_DENSITY:.0f} g silicone per cast")
    print(f"mold block {X1 - X0:.0f} x {Y1 - Y0 + 2 * FLANGE:.0f} x {Z1 - Z0:.0f} mm; open face {bx1 - bx0:.0f} x {by1 - by0:.0f} mm")
    print(f"the seam's tongue ring is {TONGUE[1] - TONGUE[0]:.1f} mm wide and stays {WALL - TONGUE[1]:.1f} mm inside the outer wall")

    tl, tr = to_trimesh(left), to_trimesh(right)
    trimesh.util.concatenate([tl, tr]).export(os.path.join(OUT, "mold-v1-assembled.stl"))
    # print orientation: outer side on the bed, cavity facing up
    tl.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, [0, 1, 0])); tl.apply_translation(-tl.bounds[0])
    tr.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0])); tr.apply_translation(-tr.bounds[0])
    for name, t in (("mold-v1-left.stl", tl), ("mold-v1-right.stl", tr)):
        t.export(os.path.join(OUT, name))
        print(f"{name}: watertight {t.is_watertight}, {np.round(t.extents, 1)} mm, plastic {t.volume / 1000:.0f} cm3 (~{t.volume / 1000 * 1.24:.0f} g PLA solid)")
