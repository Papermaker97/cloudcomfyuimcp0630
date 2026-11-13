"""
Ppomo skeleton clicker - test module v1 (print today, squeeze, learn).

One flat piece, printed in place, no supports, no separate spring:
  * the VERTEBRAL BODY (fixed) holds 3 tactile buttons in pockets: top, left, right
  * the TOP VERTEBRA (with a spinous bump) floats on 4 thin plastic beams (a parallel flexure):
      press it down -> it slides ~0.4 mm -> its nub clicks the top button -> the beams spring it back
  * the LEFT and RIGHT RIBS hang from the transverse processes on a thin living hinge:
      squeeze a rib in -> it swings -> its nub clicks the side button -> the hinge springs it back
  Wire the 3 buttons in parallel to one pin: any press = one squeeze.

Everything moves in the print plane (X-Y), so the thin beams and hinges are printed along their
length (strong), and the part stands T mm tall. Buttons drop into their pockets from the top after printing.

Run:  python make_clicker_module.py 6    (6 x 6 mm buttons)   |   python make_clicker_module.py 12
MEASURE YOUR BUTTON: body thickness along the press direction (BODY) and how far the plunger sticks out (PL).
Suggested print: PLA or PETG, 0.2 mm layers, 3 walls, 20% infill, no supports.
Written for the Ppomo project with help from Claude.
"""
import os
import sys

import numpy as np
import trimesh
from manifold3d import CrossSection, Manifold, JoinType

SIZE = sys.argv[1] if len(sys.argv) > 1 else "6"
if SIZE == "12":
    SW, BODY, PL = 12.0, 3.5, 3.8          # 12 x 12 mm tactile button
else:
    SW, BODY, PL = 6.0, 3.5, 1.5           # 6 x 6 mm tactile button
FIT = 0.4                                  # pocket clearance
NUB_GAP = 0.15                             # nub to plunger at rest (the button is inserted later)
NUB_LEN = 0.8
LEG_ROOM = 3.0                             # room behind the button for its legs and wires
T = SW + 4.0                               # part height (Z)
CLEAR = 0.45                               # print-in-place gap between moving and fixed parts
BEAM_T, BEAM_L = 0.6, 16.0                 # vertebra flexure beams (thin in Y, long in X)
HINGE_T, HINGE_L = 0.8, 2.0                # rib living hinge
SEG = 48

BX = 14.0                                  # half-width of the vertebral body
TOP = 10.0                                 # top face of the vertebral body (y)
P = SW / 2 + FIT / 2                       # half pocket width
YB = TOP - (BODY + FIT) - LEG_ROOM - 0.6 - P          # side-button centre (below the top pocket)
BOT = YB - P - 2.5                         # bottom of the vertebral body
VX = SW / 2 + 3.0                          # half-width of the top vertebra
Y0 = TOP + PL + NUB_GAP + NUB_LEN          # underside of the top vertebra
VH = 8.0                                   # vertebra height


def rect(x0, x1, y0, y1):
    return CrossSection.square([x1 - x0, y1 - y0]).translate([x0, y0])


def circ(x, y, r):
    return CrossSection.circle(r, SEG).translate([x, y])


def rounded(cs, r):
    return cs.offset(-r, JoinType.Round).offset(r, JoinType.Round)


def bar_along(points, r):
    """a rounded bone bar through points (hull of consecutive circles)"""
    out = CrossSection()
    for a, b in zip(points[:-1], points[1:]):
        out += CrossSection.batch_hull([circ(a[0], a[1], r), circ(b[0], b[1], r)])
    return out


def parts():
    # ---- fixed: vertebral body + transverse processes (bars) + posts that hold the beams ----
    body = rounded(rect(-BX, BX, BOT, TOP), 3.0)
    post_x0 = VX + BEAM_L
    fixed = body
    for s in (-1, 1):
        bar = rect(min(s * (BX - 2), s * (post_x0 + 4)), max(s * (BX - 2), s * (post_x0 + 4)), TOP - 4, TOP)
        post = rect(min(s * post_x0, s * (post_x0 + 4)), max(s * post_x0, s * (post_x0 + 4)), TOP - 4, Y0 + VH)
        fixed += rounded(bar + post, 1.0)
        fixed += circ(s * (post_x0 + 2), Y0 + VH, 2.6)                  # knob at the end of the process
    # pockets: top (plunger +Y), left/right (plunger -X/+X); open at the face so the plunger sticks out
    pockets = rect(-P, P, TOP - (BODY + FIT) - LEG_ROOM, TOP + 1)
    for s in (-1, 1):
        x_in, x_out = s * (BX - (BODY + FIT) - LEG_ROOM), s * (BX + 1)
        pockets += rect(min(x_in, x_out), max(x_in, x_out), YB - P, YB + P)

    # ---- moving: top vertebra with a spinous bump and a nub ----
    vert = rounded(rect(-VX, VX, Y0, Y0 + VH), 2.0) + circ(0, Y0 + VH, 3.2) + circ(0, Y0 + VH + 3.0, 2.0)
    vert += rect(-1.5, 1.5, TOP + PL + NUB_GAP, Y0 + 0.5)               # nub on the top button
    beams = CrossSection()
    for s in (-1, 1):
        for y in (Y0 + 1.5, Y0 + VH - 1.5):
            beams += rect(min(s * (VX - 0.5), s * (post_x0 + 0.5)), max(s * (VX - 0.5), s * (post_x0 + 0.5)), y - BEAM_T / 2, y + BEAM_T / 2)

    # ---- moving: ribs on living hinges under the transverse processes ----
    ribs, hinges = CrossSection(), CrossSection()
    for s in (-1, 1):
        xi = BX + PL + NUB_GAP + NUB_LEN                                  # rib inner face (unsigned)
        cx = xi + 2.0
        y_top, y_bot = TOP - 4 - CLEAR - HINGE_L, BOT - 6.0
        pts = []
        for i in range(9):                                               # gently bowed outward, like a rib
            t = i / 8
            y = y_top - (y_top - y_bot) * t
            pts.append((s * (cx + 1.6 * np.sin(np.pi * t)), y))
        rib = bar_along(pts, 2.0)
        rib += rect(min(s * (BX + PL + NUB_GAP), s * (cx + 1.0)), max(s * (BX + PL + NUB_GAP), s * (cx + 1.0)), YB - 1.5, YB + 1.5)   # nub, reaching into the bowed rib
        ribs += rib
        hx = s * (cx)
        hinges += rect(hx - HINGE_T / 2, hx + HINGE_T / 2, y_top, TOP - 4 + 0.2)
    return fixed, pockets, vert, beams, ribs, hinges


def check(fixed, vert, ribs):
    """moving parts must keep a print-in-place gap from the fixed parts (beams/hinges are the only links)"""
    issues = []
    for name, mv in (("vertebra", vert), ("ribs", ribs)):
        a = (mv.offset(CLEAR - 0.05, JoinType.Round) ^ fixed).area()
        if a > 0.01:
            issues.append(f"{name} too close to fixed parts (overlap area {a:.2f} mm2)")
    return issues


if __name__ == "__main__":
    fixed, pockets, vert, beams, ribs, hinges = parts()
    issues = check(fixed, vert, ribs)
    print("gap check:", "OK" if not issues else issues)
    piece2d = fixed + vert + beams + ribs + hinges
    solid = Manifold.extrude(piece2d, T)
    # pockets open from the top, leaving a 2 mm floor
    solid -= Manifold.extrude(pockets, T).translate([0, 0, 2.0])
    mesh = solid.to_mesh()
    t = trimesh.Trimesh(np.asarray(mesh.vert_properties)[:, :3], np.asarray(mesh.tri_verts), process=False)
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(here, f"clicker-module-{SIZE}mm.stl")
    t.export(out)
    print(out, "| watertight:", t.is_watertight, "| size mm:", np.round(t.extents, 1), "| bodies:", solid.decompose().__len__())
