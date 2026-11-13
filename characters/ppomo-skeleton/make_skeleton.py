"""
Ppomo skeleton v1: a small animal-bone-looking core that protects the buttons inside and clicks
when pressed from the top, the left, the right or the back.

Parts (print separately, all already oriented flat-side-down for printing):
  skeleton-core.stl        the "body bone": 4 button pockets (top, left, right, back), guide holes,
                           a hollow channel inside for the wires, and a wire exit at the front.
  skeleton-spine.stl       top cap, looks like vertebrae
  skeleton-rib-L.stl       left cap, looks like ribs
  skeleton-rib-R.stl       right cap, looks like ribs
  skeleton-pelvis.stl      back cap, looks like a pelvis with a little tail

How it works
  Each cap has 2 guide stems that slide into the core and a small nub that rests on its button.
  Press a cap -> it slides in ~0.3-1 mm -> the button under it clicks. All 4 buttons are wired in
  parallel to one Arduino pin: any press = one squeeze. For today's test, hold the caps on with a
  rubber band around the whole skeleton (later the silicone body holds them).

Buttons: the default is a 12 x 12 mm tactile button (body ~3.5 mm tall, plunger ~3.8 mm above it).
For 6 x 6 mm buttons run:  python make_skeleton.py 6
MEASURE YOUR BUTTON and adjust SW / SW_BODY / PLUNGER below if it differs.

Sizes (mm). Fits inside the 110 mm Ppomo with ~8 mm or more of silicone around it.
X = left/right, Y = length (the front, toward the face, is -Y), Z = up.
Needs: pip install manifold3d trimesh numpy
Written for the Ppomo project with help from Claude.
"""
import os
import sys

import numpy as np
import trimesh
from manifold3d import Manifold

SEG = 64
BUTTON = sys.argv[1] if len(sys.argv) > 1 else "12"
if BUTTON == "6":
    SW, SW_BODY, PLUNGER = 6.0, 3.5, 1.5        # 6 x 6 x 5 mm tactile button
else:
    SW, SW_BODY, PLUNGER = 12.0, 3.5, 3.8       # 12 x 12 x 7.3 mm tactile button
FIT = 0.4                                        # room around the button in its pocket
REST_GAP = 0.4                                   # gap between the plunger top and the cap plate
NUB = REST_GAP + 0.1                             # nub length: touches the plunger lightly at rest

# core: a rounded "body bone"
CX, CY0, CY1, CZ = 11.0, -12.0, 32.0, 20.0       # half-width, length range, height
SWY = 10.0                                       # button position along the length
STEM_R, HOLE_R, STEM_IN = 1.5, 1.8, 5.0          # guide stems / holes
PLATE_T = 2.4                                    # cap plate thickness


def box(x0, x1, y0, y1, z0, z1):
    return Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def ell(cx, cy, cz, rx, ry, rz):
    return Manifold.sphere(1.0, SEG).scale([rx, ry, rz]).translate([cx, cy, cz])


def cyl(p0, axis, length, r):
    """cylinder starting at p0, running `length` along +axis ('x', 'y' or 'z'; negative length = backwards)."""
    c = Manifold.cylinder(abs(length), r, r, 32)
    if axis == "x":
        c = c.rotate([0, 90, 0])
    elif axis == "y":
        c = c.rotate([-90, 0, 0])
    if length < 0:
        c = c.translate({"x": [-abs(length), 0, 0], "y": [0, -abs(length), 0], "z": [0, 0, -abs(length)]}[axis])
    return c.translate(list(p0))


def rounded_box(x0, x1, y0, y1, z0, z1, r):
    """box with rounded vertical edges (a stack of a box and 4 corner cylinders)."""
    b = box(x0 + r, x1 - r, y0, y1, z0, z1) + box(x0, x1, y0 + r, y1 - r, z0, z1)
    for x in (x0 + r, x1 - r):
        for y in (y0 + r, y1 - r):
            b += cyl((x, y, z0), "z", z1 - z0, r)
    return b


def make_core():
    core = rounded_box(-CX, CX, CY0, CY1, 0, CZ, 4.0)
    p = SW / 2 + FIT / 2
    # pockets (button body sits inside, plunger sticks out) + slots down into the wire channel
    core -= box(-p, p, SWY - p, SWY + p, CZ - SW_BODY, CZ + 1)                         # top
    core -= box(-4, 4, SWY - 3, SWY + 3, CZ - SW_BODY - 4, CZ)
    for s in (-1, 1):                                                                  # left / right
        core -= box(s * CX - (SW_BODY if s > 0 else -SW_BODY) - (0 if s > 0 else 0), s * CX + s * 1, SWY - p, SWY + p, CZ / 2 - p, CZ / 2 + p) if s > 0 else \
                box(-CX - 1, -CX + SW_BODY, SWY - p, SWY + p, CZ / 2 - p, CZ / 2 + p)
        core -= box(min(s * (CX - SW_BODY), s * 4), max(s * (CX - SW_BODY), s * 4), SWY - 3, SWY + 3, CZ / 2 - 3, CZ / 2 + 3)
    core -= box(-p, p, CY1 - SW_BODY, CY1 + 1, CZ / 2 - p, CZ / 2 + p)                 # back
    core -= box(-3, 3, CY1 - SW_BODY - 6, CY1 - SW_BODY, CZ / 2 - 3, CZ / 2 + 3)
    # hollow channel for the wires and the front exit
    core -= box(-4, 4, CY0 + 3, CY1 - SW_BODY - 2, 3, CZ - SW_BODY - 1)
    core -= cyl((0, CY0 - 1, CZ / 2 - 3), "y", 5, 3.0)
    # guide holes
    for y in (SWY - 13, SWY + 13):
        core -= cyl((0, y, CZ - 6), "z", 7, HOLE_R)                                    # top cap
        for s in (-1, 1):
            core -= cyl((s * CX, y, CZ / 2), "x", -s * 6, HOLE_R)                      # side caps
    for x in (-7.5, 7.5):
        core -= cyl((x, CY1, CZ / 2), "y", -6, HOLE_R)                                 # back cap
    # bone look: a slight waist and two knobs at the front like the end of a long bone
    core += ell(-6, CY0 + 2, CZ / 2, 6, 5, 8) + ell(6, CY0 + 2, CZ / 2, 6, 5, 8)
    core -= cyl((0, CY0 - 1, CZ / 2 - 3), "y", 8, 3.0)
    return core


def make_spine():
    z0 = CZ + PLUNGER + REST_GAP                    # plate underside
    cap = rounded_box(-8.5, 8.5, CY0 + 3, CY1 - 3, z0, z0 + PLATE_T, 3.0)
    top = z0 + PLATE_T
    for y in np.linspace(CY0 + 6, CY1 - 6, 5):      # vertebrae, flat-topped for printing
        cap += ell(0, y, top, 7.5, 3.6, 3.2) + ell(0, y, top + 2.5, 2.2, 2.6, 2.2)
    cap = cap ^ box(-50, 50, -50, 80, z0, top + 4.2)
    cap += cyl((0, SWY, z0), "z", -NUB, 2.5)        # nub on the button
    for y in (SWY - 13, SWY + 13):
        cap += cyl((0, y, z0), "z", -(z0 - (CZ - STEM_IN)), STEM_R)
    return cap


def make_rib(s):
    x0 = s * (CX + PLUNGER + REST_GAP)              # plate inner face
    x1 = x0 + s * PLATE_T
    cap = box(min(x0, x1), max(x0, x1), CY0 + 3, CY1 - 3, 1.5, CZ - 1.5)
    for y in (CY0 + 6, SWY, SWY + 9, CY1 - 6):      # ribs: tall rounded bars on the outside
        cap += ell(x1, y, CZ / 2, 2.8, 2.6, 9.5)
    outer = x1 + s * 2.4
    cap = cap ^ box(min(x0, outer), max(x0, outer), -50, 80, -10, 40)          # flat outer face
    cap += cyl((x0, SWY, CZ / 2), "x", -s * NUB, 2.5)
    for y in (SWY - 13, SWY + 13):
        cap += cyl((x0, y, CZ / 2), "x", -s * (abs(x0) - (CX - STEM_IN)), STEM_R)
    return cap


def make_pelvis():
    y0 = CY1 + PLUNGER + REST_GAP
    y1 = y0 + PLATE_T
    cap = box(-CX, CX, y0, y1, 1.5, CZ - 1.5)
    cap += ell(-5.5, y1, CZ / 2 + 1, 6.0, 2.8, 8.0) + ell(5.5, y1, CZ / 2 + 1, 6.0, 2.8, 8.0)   # two hip wings
    cap += ell(0, y1, 3.5, 2.4, 2.8, 3.5)                                                       # little tail
    cap = cap ^ box(-50, 50, y0, y1 + 2.4, -10, 40)
    cap += cyl((0, y0, CZ / 2), "y", -NUB, 2.5)
    for x in (-7.5, 7.5):
        cap += cyl((x, y0, CZ / 2), "y", -(y0 - (CY1 - STEM_IN)), STEM_R)
    return cap


def to_tm(m):
    mesh = m.to_mesh()
    return trimesh.Trimesh(np.asarray(mesh.vert_properties)[:, :3], np.asarray(mesh.tri_verts), process=False)


def laid_flat(t, axis_up):
    """rotate so the cap's flat outer face is on the bed, stems pointing up."""
    R = trimesh.transformations.rotation_matrix
    t = t.copy()
    if axis_up == "-z":
        t.apply_transform(R(np.pi, [1, 0, 0]))
    elif axis_up == "+x":
        t.apply_transform(R(np.pi / 2, [0, 1, 0]))
    elif axis_up == "-x":
        t.apply_transform(R(-np.pi / 2, [0, 1, 0]))
    elif axis_up == "-y":
        t.apply_transform(R(np.pi / 2, [1, 0, 0]))
    t.apply_translation(-t.bounds[0])
    return t


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(here, f"button-{BUTTON}mm")
    os.makedirs(out, exist_ok=True)
    core, spine, ribL, ribR, pelvis = make_core(), make_spine(), make_rib(-1), make_rib(1), make_pelvis()
    caps = {"spine": spine, "rib-L": ribL, "rib-R": ribR, "pelvis": pelvis}
    # checks: nothing overlaps at rest, and nothing hits the core before the button clicks
    for name, c in caps.items():
        print(f"{name:7s} overlap with core at rest (mm3): {round((core ^ c).volume(), 3)}")
    assembled = core
    for c in caps.values():
        assembled += c
    to_tm(assembled).export(os.path.join(out, "skeleton-assembled-view.stl"))
    to_tm(core).export(os.path.join(out, "skeleton-core.stl"))
    laid_flat(to_tm(spine), "-z").export(os.path.join(out, "skeleton-spine.stl"))
    laid_flat(to_tm(ribL), "+x").export(os.path.join(out, "skeleton-rib-L.stl"))
    laid_flat(to_tm(ribR), "-x").export(os.path.join(out, "skeleton-rib-R.stl"))
    laid_flat(to_tm(pelvis), "-y").export(os.path.join(out, "skeleton-pelvis.stl"))
    a = to_tm(assembled)
    print("assembled size mm:", np.round(a.extents, 1), "| watertight:", a.is_watertight)
