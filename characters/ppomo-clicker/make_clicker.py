"""
Ppomo "bone clicker": the 3D-printed core that sits inside Ppomo's butt.

Two printed parts:
  base  - an oval tray with 2 cradles for mouse micro switches (wired in parallel), 2 guide posts,
          slots under the switches for their pins, and a notch for the 2-wire "nerve" to the head.
  lid   - an oval dome that looks like a vertebra / rib cage (a spine ridge + 4 rib ridges).
          It slides down the guide posts; 2 pressing bars underneath rest on the switch plungers.
          Squeeze Ppomo -> the skin pushes the lid down ~1 mm -> click.

All sizes in mm. The switch numbers are for a common mouse micro switch (Omron D2F size, about
12.8 x 5.8 x 6.5 mm). MEASURE YOUR SWITCH and change SWITCH_* below before printing.

Run:  python make_clicker.py   -> writes clicker-base.stl, clicker-lid.stl, clicker-assembly.stl
Needs: pip install manifold3d trimesh numpy
Written for the Ppomo project with help from Claude.
"""
import numpy as np
import trimesh
from manifold3d import Manifold

SEG = 96                      # smoothness of curves

# ---------- parameters ----------
SWITCH_L, SWITCH_W, SWITCH_H = 12.8, 5.8, 6.5   # switch body, lying with its plunger facing up
PLUNGER_UP = 0.8              # how far the plunger sticks out above the body (measure yours)
SWITCH_X = 12.0               # the two switches sit at x = -12 and +12
FIT = 0.3                     # extra room around the switch in its cradle

PLATE_T = 3.0                 # base plate thickness
BASE_RX, BASE_RY = 23.0, 15.0 # base outer oval half-sizes (46 x 30)
WALL_T, WALL_TOP = 1.6, 9.0   # base wall thickness and height (z)
POST_R, POST_TOP, POST_Y = 2.0, 11.0, 9.0       # guide posts at (0, +-9)

CLEAR = 0.5                   # gap between base wall and lid skirt
LID_T = 2.0                   # lid wall thickness
SKIRT_BOTTOM = 5.0            # lid skirt goes down to here, overlapping the base wall (guide)
DOME_BASE, DOME_H = 13.0, 8.0 # dome starts at z=13 and rises 8 mm
REST = PLATE_T + SWITCH_H + PLUNGER_UP          # z of the plunger tops = where the lid's bars rest
SLEEVE_BOTTOM, SLEEVE_R = 8.0, 3.6              # lid sleeves around the guide posts
TRAVEL_NOTE = "lid can travel about 2 mm before anything bottoms out; the switch needs ~0.5-1 mm"

LID_RX = BASE_RX + CLEAR + LID_T                # 25.5
LID_RY = BASE_RY + CLEAR + LID_T                # 17.5


def oval_prism(rx, ry, z0, z1):
    return Manifold.cylinder(z1 - z0, 1.0, 1.0, SEG).scale([rx, ry, 1.0]).translate([0, 0, z0])


def box(x0, x1, y0, y1, z0, z1):
    return Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def ellipsoid(rx, ry, rz, cz):
    return Manifold.sphere(1.0, SEG).scale([rx, ry, rz]).translate([0, 0, cz])


# ---------- base ----------
def make_base():
    b = oval_prism(BASE_RX, BASE_RY, 0, PLATE_T)
    b += oval_prism(BASE_RX, BASE_RY, PLATE_T, WALL_TOP) - oval_prism(BASE_RX - WALL_T, BASE_RY - WALL_T, PLATE_T - 1, WALL_TOP + 1)
    for sx in (-1, 1):
        cx = sx * SWITCH_X
        il, iw = SWITCH_L / 2 + FIT, SWITCH_W / 2 + FIT
        cradle = box(cx - il - 1.2, cx + il + 1.2, -iw - 1.2, iw + 1.2, PLATE_T, PLATE_T + SWITCH_H * 0.5)
        cradle -= box(cx - il, cx + il, -iw, iw, PLATE_T - 1, PLATE_T + SWITCH_H)
        b += cradle
        b -= box(cx - 5.0, cx + 5.0, -1.8, 1.8, -1, PLATE_T + 1)          # slot for the switch pins
    for sy in (-1, 1):
        b += Manifold.cylinder(POST_TOP - PLATE_T, POST_R, POST_R, 48).translate([0, sy * POST_Y, PLATE_T])
    b -= box(-BASE_RX - 1, -BASE_RX + WALL_T + 1, -3, 3, PLATE_T, PLATE_T + 4)   # wire notch at the back
    return b


# ---------- lid (vertebra / rib-cage dome) ----------
def make_lid():
    outer = oval_prism(LID_RX, LID_RY, SKIRT_BOTTOM, DOME_BASE) + (ellipsoid(LID_RX, LID_RY, DOME_H, DOME_BASE) ^ box(-50, 50, -50, 50, DOME_BASE, 50))
    inner = oval_prism(LID_RX - LID_T, LID_RY - LID_T, SKIRT_BOTTOM - 1, DOME_BASE) + (ellipsoid(LID_RX - LID_T, LID_RY - LID_T, DOME_H - LID_T, DOME_BASE) ^ box(-50, 50, -50, 50, DOME_BASE - 0.01, 50))
    lid = outer - inner
    # bone styling on top: one spine ridge along the length, four rib ridges across
    upper = box(-50, 50, -50, 50, DOME_BASE, 50)
    lid += ellipsoid(LID_RX + 1.6, LID_RY + 1.6, DOME_H + 1.6, DOME_BASE) ^ box(-50, 50, -1.6, 1.6, 0, 50) ^ upper
    for x in (-15.0, -5.0, 5.0, 15.0):
        lid += ellipsoid(LID_RX + 1.2, LID_RY + 1.2, DOME_H + 1.2, DOME_BASE) ^ box(x - 1.3, x + 1.3, -50, 50, 0, 50) ^ upper
    # inside: two pressing bars that rest on the switch plungers, and two sleeves for the guide posts
    inside = Manifold()
    for sx in (-1, 1):
        inside += box(sx * SWITCH_X - 4.5, sx * SWITCH_X + 4.5, -2.2, 2.2, REST, 30)
    for sy in (-1, 1):
        inside += Manifold.cylinder(30 - SLEEVE_BOTTOM, SLEEVE_R, SLEEVE_R, 48).translate([0, sy * POST_Y, SLEEVE_BOTTOM])
    inside = inside ^ outer                                            # keep it inside the dome
    lid += inside
    for sy in (-1, 1):                                                 # holes for the posts (0.4 mm clearance)
        lid -= Manifold.cylinder(POST_TOP + 2.5 - SLEEVE_BOTTOM + 1, POST_R + 0.4, POST_R + 0.4, 48).translate([0, sy * POST_Y, SLEEVE_BOTTOM - 1])
    lid -= box(-LID_RX - 1, -LID_RX + LID_T + 1, -3.4, 3.4, SKIRT_BOTTOM - 1, SKIRT_BOTTOM + 4.5)   # wire notch in the skirt
    return lid


def to_trimesh(m):
    mesh = m.to_mesh()
    return trimesh.Trimesh(vertices=np.asarray(mesh.vert_properties)[:, :3], faces=np.asarray(mesh.tri_verts), process=False)


if __name__ == "__main__":
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    base, lid = make_base(), make_lid()
    tb, tl = to_trimesh(base), to_trimesh(lid)
    tb.export(os.path.join(here, "clicker-base.stl"))
    # print the lid upside down (flat skirt edge on the bed)
    tl_print = tl.copy()
    tl_print.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
    tl_print.apply_translation([0, 0, -tl_print.bounds[0][2]])
    tl_print.export(os.path.join(here, "clicker-lid.stl"))
    trimesh.util.concatenate([tb, tl]).export(os.path.join(here, "clicker-assembly.stl"))
    for name, t in (("base", tb), ("lid", tl)):
        print(name, "watertight:", t.is_watertight, "size mm:", np.round(t.extents, 1), "volume cm3:", round(t.volume / 1000, 2))
    # interference check at rest: lid and base must not overlap
    print("overlap at rest (mm3):", round((base ^ lid).volume(), 3))
    pressed = lid.translate([0, 0, -2.0])                              # lid pushed 2 mm down: still no collision?
    print("overlap when pressed 2 mm (mm3):", round((base ^ pressed).volume(), 3))
    print("plunger top z:", REST, "|", TRAVEL_NOTE)
