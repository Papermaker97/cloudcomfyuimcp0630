"""
Ppomo wedge test v1: press ANY cap -> ONE button.

Two caps (top and bottom) each ride on serpentine springs like the deep button. Each stem ends in a
45-degree wedge. Between them runs one horizontal rod with two matching ramps. Press either cap
(or both): the wedge pushes the rod sideways, and the rod's tip clicks the single tactile button.
Release: the stems' springs lift the caps, and the rod's own serpentine spring pulls the rod back.

One flat piece, printed in place, no supports, no separate spring.
Learned from a working printed clicker (ClickCLIC): rounded spring turns, and guiding every
moving part at two places along its length.

Print: lay flat as exported (8 mm tall), PLA or PETG, 0.2 mm layers, 3 walls, no supports.
Drop a 6 x 6 mm tactile button into the seat at the right end (plunger toward the rod).
Needs: pip install manifold3d trimesh numpy
Written for the Ppomo project with help from Claude.
"""
import os

import numpy as np
import trimesh
from manifold3d import CrossSection, Manifold, JoinType

SEG = 48
T = 8.0
TRAVEL = 4.3                     # cap travel to the stop
T_SPR, L_BEAM, N_BEAMS, GAP = 0.8, 16.0, 7, 1.5
PITCH = T_SPR + GAP
STEM = 3.0                       # stem half-width
ROD = 2.5                        # rod half-width
CLEAR = 0.5
SW, BODY, PL = 6.0, 3.5, 1.5     # tactile button

V_IN = STEM + 0.8
V_OUT = V_IN + L_BEAM
WALL0, WALL1 = V_OUT + 1.0, V_OUT + 3.4          # 20.8, 23.2
U_FACE = 7.2                     # lowest corner of the stem's wedge face
U7 = 14.6                        # lowest spring beam
U1 = U7 + (N_BEAMS - 1) * PITCH
LIP0 = U1 + T_SPR / 2 + 1.0
LIP1 = LIP0 + 2.0
CAP0 = LIP1 + TRAVEL
CAP_T = 3.0
WEDGE_GAP = CLEAR * 2 ** 0.5     # vertical offset between the wedge faces (0.5 mm apart at rest)
RAMP_V0 = ROD + WEDGE_GAP - STEM - U_FACE        # where the rod's ramp starts
ROD_SPR_V1 = -WALL1 - 5.5 - T_SPR / 2            # rod spring: first beam (leaves room for the rod travel)
ROD_SPR_VN = ROD_SPR_V1 - (N_BEAMS - 1) * PITCH
END0 = ROD_SPR_VN - T_SPR / 2 - 1.0
END1 = END0 - 2.4
TACT_TIP = WALL0 - BODY - PL                     # the button's plunger tip (it points left)
ROD_TIP_GAP = 3.1                                # rod travel before it touches the button
ROD_TIP = TACT_TIP - ROD_TIP_GAP


def R(v0, v1, u0, u1):
    """rectangle in world coords: v = horizontal, u = vertical."""
    v0, v1 = sorted([v0, v1]); u0, u1 = sorted([u0, u1])
    return CrossSection.square([v1 - v0, u1 - u0]).translate([v0, u0])


def circ(v, u, r):
    return CrossSection.circle(r, SEG).translate([v, u])


def poly(pts):
    return CrossSection([pts])


def serpentine(p1, to_world, q_first):
    """7 beams stacked along p (from p1 downward), running sideways (q) on both sides.
    to_world(p0, p1, q0, q1) -> CrossSection. The first beam starts at q_first (joins the stem/rod),
    the last beam ends on the wall."""
    h = T_SPR / 2
    out = CrossSection()
    for s in (-1, 1):
        for i in range(N_BEAMS):
            p = p1 - i * PITCH
            q0 = q_first if i == 0 else V_IN
            q1 = WALL0 + 0.1 if i == N_BEAMS - 1 else V_OUT
            out += to_world(p - h, p + h, s * q0, s * q1)
            if i < N_BEAMS - 1:
                if i % 2 == 0:
                    out += to_world(p - PITCH - h, p + h, s * (V_OUT - T_SPR), s * V_OUT)
                else:
                    out += to_world(p - PITCH - h, p + h, s * V_IN, s * (V_IN + T_SPR))
    return out.offset(0.45, JoinType.Round).offset(-0.45, JoinType.Round)      # round the inside of every turn


def build():
    top = lambda p0, p1, q0, q1: R(q0, q1, p0, p1)          # p = up
    bot = lambda p0, p1, q0, q1: R(q0, q1, -p0, -p1)        # mirrored
    rodw = lambda p0, p1, q0, q1: R(p0, p1, q0, q1)         # p = along the rod

    fixed = R(END1, END0, -WALL1, WALL1)                                 # left end wall
    fixed += R(WALL0, WALL1, -LIP1, LIP1)                                # right wall (button seat on its inside)
    for s in (-1, 1):
        fixed += R(END1, -WALL1, s * WALL0, s * WALL1)                   # rod-spring chamber walls
        fixed += R(-WALL1, -WALL0, s * (ROD + CLEAR), s * LIP1)          # main left wall, open for the rod
        fixed += R(STEM + CLEAR, WALL1, s * LIP0, s * LIP1)              # lips: upper guide + stop
        fixed += R(-WALL1, -(STEM + CLEAR), s * LIP0, s * LIP1)
        fixed += R(-WALL0, -(STEM + CLEAR), s * 10.9, s * 12.4)          # arm holding the lower guide
        fixed += R(-(STEM + CLEAR) - 2.0, -(STEM + CLEAR), s * 7.5, s * 12.4)   # lower guide block (takes the wedge's side push)
        fixed += R(8.0, WALL0, s * (ROD + 0.6), s * (ROD + 2.2))         # rails: guide the rod tip, fence the button

    springs = serpentine(U1, top, STEM - 0.1) + serpentine(U1, bot, STEM - 0.1) + serpentine(ROD_SPR_V1, rodw, ROD - 0.1)

    def stem(sign):
        body = poly([(-STEM, U_FACE), (STEM, U_FACE + 2 * STEM), (STEM, CAP0 + 0.5), (-STEM, CAP0 + 0.5)])
        cap = R(-9, 9, CAP0, CAP0 + CAP_T).offset(-1.2, JoinType.Round).offset(1.2, JoinType.Round)
        cap += circ(0, CAP0 + CAP_T - 0.4, 2.6) + circ(-5.4, CAP0 + CAP_T - 0.6, 2.0) + circ(5.4, CAP0 + CAP_T - 0.6, 2.0)
        m = body + cap
        return m if sign > 0 else m.mirror([0, 1])

    rod = R(ROD_SPR_V1 - 1.1, ROD_TIP, -ROD, ROD)
    lug = poly([(RAMP_V0, ROD), (RAMP_V0 + 8, ROD), (RAMP_V0 + 8, ROD + 8)])
    rod += lug + lug.mirror([0, 1])
    return fixed, springs, stem(1), stem(-1), rod


def rod_travel(d):
    return max(0.0, d - WEDGE_GAP)


def sweep(fixed, stem_t, stem_b, rod, press_top, press_bottom):
    """move the pressed stems down in small steps; the rod follows the wedge. Report any collision."""
    worst = 0.0
    for d in np.arange(0.0, TRAVEL - 0.04, 0.25):
        st = stem_t.translate([0, -d if press_top else 0])
        sb = stem_b.translate([0, d if press_bottom else 0])
        r = rod.translate([rod_travel(d), 0])
        for a, b in ((st, fixed), (sb, fixed), (r, fixed), (st, r), (sb, r)):
            worst = max(worst, (a ^ b).area())
    return worst


if __name__ == "__main__":
    fixed, springs, stem_t, stem_b, rod = build()
    ok = True
    movers = {"top stem": stem_t, "bottom stem": stem_b, "rod": rod}
    for n, mv in movers.items():
        others = fixed
        for n2, m2 in movers.items():
            if n2 != n:
                others += m2
        a = (mv.offset(CLEAR - 0.06, JoinType.Round) ^ others).area()
        print(f"rest gap around the {n} OK:", a < 0.01); ok &= a < 0.01
    for label, pt, pb in (("top only", True, False), ("bottom only", False, True), ("both", True, True)):
        w = sweep(fixed, stem_t, stem_b, rod, pt, pb)
        print(f"press {label}: moves freely to the stop:", w < 0.01); ok &= w < 0.01
    full = rod_travel(TRAVEL)
    click_cap = ROD_TIP_GAP + 0.25 + WEDGE_GAP
    print(f"cap travel {TRAVEL} mm -> rod travel {full:.2f} mm; the rod touches the button after {ROD_TIP_GAP} mm, so the click comes at ~{click_cap:.2f} mm of cap travel:", click_cap < TRAVEL)
    ok &= click_cap < TRAVEL
    d = TRAVEL / N_BEAMS
    print(f"spring beams: gap {GAP} mm vs worst closing {2 * d:.2f} mm -> never touch:", GAP > 2 * d); ok &= GAP > 2 * d
    k = 2 * (12 * 3000 * (T * T_SPR ** 3 / 12) / L_BEAM ** 3) / N_BEAMS
    print(f"force estimate at the click: cap spring ~{k * click_cap / 9.81 * 1000:.0f} g + rod spring ~{k * ROD_TIP_GAP / 9.81 * 1000:.0f} g + button ~200 g (rough, PLA)")
    solid = Manifold.extrude(fixed + springs + stem_t + stem_b + rod, T)
    for z0, z1 in ((-0.1, 1.55), (T - 1.55, T + 0.1)):               # leg slots through the right wall
        solid -= Manifold.cube([WALL1 - WALL0 + 0.6, SW + 0.6, z1 - z0]).translate([WALL0 - 0.3, -(SW + 0.6) / 2, z0])
    nb = len(solid.decompose())
    print("one piece:", nb == 1); ok &= nb == 1
    mesh = solid.to_mesh()
    t = trimesh.Trimesh(np.asarray(mesh.vert_properties)[:, :3], np.asarray(mesh.tri_verts), process=False)
    here = os.path.dirname(os.path.abspath(__file__))
    t.export(os.path.join(here, "wedge-test-v1.stl"))
    print("size mm:", np.round(t.extents, 1), "| watertight:", t.is_watertight)
    print("ALL CHECKS OK" if ok else "CHECKS FAILED")
