"""
Ppomo deep button v1: one basic test button with keycap-like travel (about 4 mm).

One flat piece, printed in place, no supports, no separate spring:
  * a housing (floor, two walls, two top lips that guide the stem)
  * a stem with a wide cap on top
  * two serpentine springs (7 thin beams each) between the stem and the walls
  * a seat on the floor for a 6 x 6 mm tactile button (optional): the stem reaches it after
    3.8 mm, clicks it, and the cap lands on the lips at 4.3 mm so nothing gets crushed
Press the cap: it sinks ~4 mm against the springs, clicks at the bottom, and springs back.

Print: lay it flat as exported (8 mm tall), PLA or PETG, 0.2 mm layers, 3 walls, no supports.
Then drop the tactile button into the seat from above (plunger pointing at the stem).
Tune at the top of this file: TRAVEL (depth), T_SPR (spring wall: thicker = stiffer), N_BEAMS.
Needs: pip install manifold3d trimesh numpy
Written for the Ppomo project with help from Claude.
"""
import os

import numpy as np
import trimesh
from manifold3d import CrossSection, Manifold, JoinType

SEG = 48
T = 8.0                       # part thickness (print height)
TRAVEL = 4.3                  # cap travel until it lands on the lips
CLICK_AT = 3.8                # travel where the stem touches the tactile button
T_SPR = 0.8                   # spring beam thickness
L_BEAM = 16.0                 # spring beam length
N_BEAMS = 7                   # beams per side (odd: the last one ends on the wall)
GAP = 1.5                     # free gap between beams
PITCH = T_SPR + GAP
STEM = 3.0                    # stem half-width
CLEAR = 0.5                   # print-in-place gap
# tactile button, 6 x 6 mm
SW, BODY, PL = 6.0, 3.5, 1.5

FLOOR = 3.0
TIP = FLOOR + BODY + PL                       # plunger tip
STEM_BOTTOM = TIP + CLICK_AT
U7 = TIP + 1.0                                # lowest beam
U1 = U7 + (N_BEAMS - 1) * PITCH               # top beam (joins the stem)
LIP0 = U1 + T_SPR / 2 + 1.0
LIP1 = LIP0 + 2.0
CAP0 = LIP1 + TRAVEL
CAP_T = 3.0
V_IN = STEM + 0.8
V_OUT = V_IN + L_BEAM
WALL0 = V_OUT + 1.0
WALL1 = WALL0 + 2.4


def rect(u0, u1, v0, v1):
    """u = press direction (up), v = sideways. Stored as (x=v, y=u)."""
    return CrossSection.square([v1 - v0, u1 - u0]).translate([v0, u0])


def srect(u0, u1, s, v0, v1):
    lo, hi = sorted([s * v0, s * v1])
    return rect(u0, u1, lo, hi)


def circ(u, v, r):
    return CrossSection.circle(r, SEG).translate([v, u])


def profiles():
    h = T_SPR / 2
    fixed = rect(0, FLOOR, -WALL1, WALL1)
    springs = CrossSection()
    for s in (-1, 1):
        fixed += srect(0, LIP1, s, WALL0, WALL1)                          # wall
        fixed += srect(LIP0, LIP1, s, STEM + CLEAR, WALL1)                # top lip (guide + stop)
        fixed += srect(FLOOR, FLOOR + BODY - 0.3, s, SW / 2 + 0.3, SW / 2 + 1.9)   # fence beside the button seat
        for i in range(N_BEAMS):
            u = U1 - i * PITCH
            v0 = STEM - 0.1 if i == 0 else V_IN                          # top beam joins the stem
            v1 = WALL0 + 0.1 if i == N_BEAMS - 1 else V_OUT               # last beam joins the wall
            springs += srect(u - h, u + h, s, v0, v1)
            if i < N_BEAMS - 1:
                if i % 2 == 0:                                            # outer turn
                    springs += srect(u - PITCH - h, u + h, s, V_OUT - T_SPR, V_OUT)
                else:                                                     # inner turn
                    springs += srect(u - PITCH - h, u + h, s, V_IN, V_IN + T_SPR)
    moving = rect(STEM_BOTTOM, CAP0 + 0.5, -STEM, STEM)
    cap = rect(CAP0, CAP0 + CAP_T, -9, 9).offset(-1.2, JoinType.Round).offset(1.2, JoinType.Round)
    moving += cap + circ(CAP0 + CAP_T - 0.4, 0, 2.6) + circ(CAP0 + CAP_T - 0.6, -5.4, 2.0) + circ(CAP0 + CAP_T - 0.6, 5.4, 2.0)
    return fixed, springs, moving


if __name__ == "__main__":
    fixed, springs, moving = profiles()
    ok = True
    # 1) nothing fused: the stem/cap keep a gap from the housing at rest
    a = (moving.offset(CLEAR - 0.06, JoinType.Round) ^ fixed).area()
    print("rest gap between stem/cap and housing OK:", a < 0.01); ok &= a < 0.01
    # 2) free travel: just before the stop, the stem/cap still touch nothing
    a = (moving.translate([0, -(TRAVEL - 0.05)]) ^ fixed).area()
    print(f"free until the stop at {TRAVEL} mm:", a < 0.01); ok &= a < 0.01
    # 3) the stem reaches the button before the stop
    print(f"stem touches the button at {CLICK_AT} mm, button clicks by ~{CLICK_AT + 0.25:.2f} mm, stop at {TRAVEL} mm:", CLICK_AT + 0.25 < TRAVEL)
    ok &= CLICK_AT + 0.25 < TRAVEL
    # 4) springs: beams never touch, stress and force estimates (guided-beam model, PLA E = 3000 MPa)
    d = TRAVEL / N_BEAMS
    stress = 3 * 3000 * T_SPR * d / L_BEAM ** 2
    k_beam = 12 * 3000 * (T * T_SPR ** 3 / 12) / L_BEAM ** 3
    k = 2 * k_beam / N_BEAMS
    print(f"beam gap {GAP} mm vs worst closing {2 * d:.2f} mm -> never touch:", GAP > 2 * d); ok &= GAP > 2 * d
    print(f"spring: ~{k:.2f} N/mm -> ~{k * CLICK_AT / 9.81 * 1000:.0f} g at the click (+ the button's own ~160-250 g); bending stress ~{stress:.0f} MPa (PLA yields ~50)")
    solid = Manifold.extrude(fixed + springs + moving, T)
    # leg slots under the button seat: the legs go through the floor near both faces, a land stays in the middle
    for z0, z1 in ((-0.1, 1.55), (T - 1.55, T + 0.1)):
        solid -= Manifold.cube([SW + 0.6, FLOOR + 0.4, z1 - z0]).translate([-(SW + 0.6) / 2, -0.2, z0])
    nb = len(solid.decompose())
    print("one piece:", nb == 1); ok &= nb == 1
    mesh = solid.to_mesh()
    t = trimesh.Trimesh(np.asarray(mesh.vert_properties)[:, :3], np.asarray(mesh.tri_verts), process=False)
    here = os.path.dirname(os.path.abspath(__file__))
    t.export(os.path.join(here, "deep-button-v1.stl"))
    print("size mm:", np.round(t.extents, 1), "| watertight:", t.is_watertight)
    print("ALL CHECKS OK" if ok else "CHECKS FAILED")
