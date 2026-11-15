"""
Ppomo vertebra v1: ONE flat print-in-place piece that is a whole squeeze-button.

Why this exists (problems found in concept v5)
  * v5 had no way to be printed: its springs sat in pockets inside a 3D core.
  * nothing held a bone sideways, so a slanted squeeze could push it aside instead of down.
  * the tactile button itself was the end stop (it would take the whole squeeze).
  * five buttons faced five straight directions; diagonals were not covered.

What a vertebra is
  A round disc, 30 mm across and 9 mm thick, printed flat in one go with no supports:
    frame   the lower part of the disc: floor, walls and two lips
    cap     the upper part of the disc (a wide "D"): the part you squeeze. It covers about 150 degrees.
    stem    joins the cap to the springs and reaches down to the button
    springs two zigzags, one on each side of the button (5 beams each), printed in the plane they bend in.
            They are only 3 mm tall and 0.6 mm thick so the squeeze stays light
    lips    guide the stem so the cap cannot be pushed sideways, and STOP the cap after 1.3 mm:
            the button clicks at about 1.05 mm and never carries the squeeze
    seat    a 6 x 6 mm tactile button drops in from the open face; its legs go out through the floor
  Squeezing the cap OR the round back of the frame works: either way the disc is pinched across its
  diameter, so one vertebra covers both directions of its axis.
  Several vertebrae stacked at different angles cover every direction (see make_bone_concept_v6.py).

Print: lay flat as exported (9 mm tall). PLA or PETG, 0.2 mm layers, 3 walls, no supports.
       Then drop a 6 x 6 mm tactile button into the seat (plunger pointing at the stem).
Tune at the top of this file: TRAVEL, T_SPR (spring wall: thicker = stiffer), N_BEAMS.
Needs: pip install manifold3d trimesh numpy
Written for the Ppomo project with help from Claude.
"""
import os

import numpy as np
import trimesh
from manifold3d import CrossSection, JoinType, Manifold

SEG = 96
R = 15.0                      # disc radius
T = 9.0                       # thickness (print height)
TRAVEL = 1.3                  # cap travel until it lands on the lips
CLICK_AT = 0.8                # travel where the stem touches the button (clicks about 0.25 mm later)
T_SPR = 0.6                   # spring wall
SPR_H = 3.0                   # the springs are only this tall (printed on the bed), which keeps them soft
N_BEAMS = 5
GAP = 0.9                     # free gap between spring beams
PITCH = T_SPR + GAP
STEM = 2.5                    # stem half-width
CLEAR = 0.45                  # print-in-place gap
WALL = 1.8
SW, BODY, PL = 6.0, 3.5, 1.5  # tactile button

FLOOR_TOP = -R + 3.0
TIP = FLOOR_TOP + BODY + PL               # button plunger tip
STEM_BOTTOM = TIP + CLICK_AT
U_TOP = -0.2                              # top spring beam (joins the stem)
U_LOW = U_TOP - (N_BEAMS - 1) * PITCH     # lowest beam (joins the wall)
LIP0 = U_TOP + T_SPR / 2 + 1.0
LIP1 = LIP0 + 2.0
CAP0 = LIP1 + TRAVEL
V_IN = STEM + 0.8
V_OUT = float(np.sqrt(R ** 2 - U_LOW ** 2)) - WALL - 1.0
L_BEAM = V_OUT - V_IN


def rect(u0, u1, v0, v1):
    """u = press direction (up), v = sideways. Stored as (x = v, y = u)."""
    v0, v1 = sorted([v0, v1])
    return CrossSection.square([v1 - v0, u1 - u0]).translate([v0, u0])


def disc(r, du=0.0):
    return CrossSection.circle(r, SEG).translate([0, du])


def wall_in(u):
    return float(np.sqrt(max(R ** 2 - u ** 2, 0))) - WALL


def profiles():
    """returns (frame, springs, moving): 2D outlines of the fixed part, the zigzags and the cap + stem."""
    h = T_SPR / 2
    big = 3 * R
    frame = disc(R) ^ rect(-big, LIP1, -big, big)                                   # the disc below the lips
    cavity = (disc(R - WALL) ^ rect(FLOOR_TOP, LIP0, -big, big)) + rect(LIP0 - 0.01, LIP1 + 0.01, -(STEM + CLEAR), STEM + CLEAR)
    frame -= cavity
    springs = CrossSection()
    for s in (-1, 1):
        frame += rect(FLOOR_TOP, FLOOR_TOP + BODY - 0.3, s * (SW / 2 + 0.3), s * (SW / 2 + 1.9))   # fence beside the button
        for i in range(N_BEAMS):
            u = U_TOP - i * PITCH
            v0 = STEM - 0.1 if i == 0 else V_IN
            v1 = wall_in(u) + 0.2 if i == N_BEAMS - 1 else V_OUT
            springs += rect(u - h, u + h, s * v0, s * v1)
            if i < N_BEAMS - 1:
                if i % 2 == 0:                                                       # outer turn
                    springs += rect(u - PITCH - h, u + h, s * (V_OUT - T_SPR), s * V_OUT)
                else:                                                                # inner turn
                    springs += rect(u - PITCH - h, u + h, s * V_IN, s * (V_IN + T_SPR))
    springs = springs.offset(0.3, JoinType.Round).offset(-0.3, JoinType.Round)       # round the inside of every turn
    cap = (disc(R, TRAVEL) ^ rect(CAP0, big, -big, big)).offset(-1.2, JoinType.Round).offset(1.2, JoinType.Round)
    moving = cap + rect(STEM_BOTTOM, CAP0 + 0.5, -STEM, STEM)
    return frame, springs, moving


def solid():
    frame, springs, moving = profiles()
    m = Manifold.extrude(frame + moving, T) + Manifold.extrude(springs, SPR_H)
    # leg slots under the button seat: the legs go out through the floor near both faces
    for z0, z1 in ((-0.1, 1.55), (T - 1.55, T + 0.1)):
        m -= Manifold.cube([SW + 0.6, 4.0, z1 - z0]).translate([-(SW + 0.6) / 2, -R - 0.5, z0])
    return m


def to_tm(m):
    mesh = m.to_mesh()
    return trimesh.Trimesh(np.asarray(mesh.vert_properties)[:, :3], np.asarray(mesh.tri_verts), process=False)


if __name__ == "__main__":
    frame, springs, moving = profiles()
    ok = True
    a = (moving.offset(CLEAR - 0.06, JoinType.Round) ^ frame).area()
    print("print-in-place gap between the cap/stem and the frame OK:", a < 0.01); ok &= a < 0.01
    a = (moving.translate([0, -(TRAVEL - 0.05)]) ^ frame).area()
    print(f"cap moves freely until the stop at {TRAVEL} mm:", a < 0.01); ok &= a < 0.01
    a = (moving.translate([0, -(TRAVEL + 0.05)]) ^ frame).area()
    print("cap is caught by the lips just after that (the stop is real):", a > 0.1); ok &= a > 0.1
    print(f"stem touches the button at {CLICK_AT} mm, clicks by about {CLICK_AT + 0.25:.2f} mm, stop at {TRAVEL} mm -> the button never takes the squeeze:", CLICK_AT + 0.25 < TRAVEL)
    ok &= CLICK_AT + 0.25 < TRAVEL
    side = (moving.translate([CLEAR + 0.2, 0]) ^ frame).area()
    print("a sideways push is caught by the lips (the cap cannot slide off its button):", side > 0.1); ok &= side > 0.1
    d = TRAVEL / N_BEAMS
    strain = 3 * T_SPR * d / L_BEAM ** 2
    k = 2 * (12 * 3000 * (SPR_H * T_SPR ** 3 / 12) / L_BEAM ** 3) / N_BEAMS
    print(f"spring beams {L_BEAM:.1f} mm long: gap {GAP} mm vs worst closing {2 * d:.2f} mm -> never touch:", GAP > 2 * d); ok &= GAP > 2 * d
    print(f"bending strain about {strain * 100:.2f} % (the printed clicker that keeps springing back: roughly 0.9 % by the same formula) | spring force at the click about {k * (CLICK_AT + 0.25) / 9.81 * 1000:.0f} g + the button's own 160-250 g")
    cover = 2 * np.degrees(np.arccos((CAP0 - TRAVEL) / R))
    print(f"the cap covers about {cover:.0f} degrees of the disc's rim")
    m = solid()
    nb = len(m.decompose())
    print("one piece:", nb == 1); ok &= nb == 1
    t = to_tm(m)
    here = os.path.dirname(os.path.abspath(__file__))
    t.export(os.path.join(here, "vertebra-v1.stl"))
    d_ = to_tm(Manifold.extrude(disc(R), 0.8))
    d_.export(os.path.join(here, "vertebra-disc-v1.stl"))
    print("size mm:", np.round(t.extents, 1), "| watertight:", t.is_watertight)
    print("ALL CHECKS OK" if ok else "CHECKS FAILED")
