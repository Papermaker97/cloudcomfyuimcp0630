"""
Ppomo wedge test v2: press ANY cap -> ONE button, now with a printed click and a narrower body.

What changed from v1 (ideas taken from working printed clickers: fidgetbuttonclicker, ClickerSwitch, ClickCLIC):
  * cap springs are diagonal V-zigzags (rounded corners) instead of rectangular serpentines -> narrower
  * a printed LATCH on the rod: two thin fingers with teeth sit just above and below the rod; a bump on the
    rod pushes past them -> "tak". Every cap moves the same rod, so every direction gets the same click.
  * longer guide blocks on the stems, so the wedge's sideways push cannot tilt them

Still one flat piece, printed in place, no supports, no separate spring.
Order of events when a cap is pressed: soft travel -> latch click (~2.9 mm) -> tactile button (~4.1 mm) -> stop (4.3 mm).

Print: lay flat as exported (8 mm tall), PLA or PETG (PETG lasts longer on the latch), 0.2 mm layers,
3 walls, no supports. Drop a 6 x 6 mm tactile button into the seat at the right end (plunger toward the rod).
Tune at the top: T_SPR (springs), LATCH_INT (click strength), LATCH_T (finger thickness).
Needs: pip install manifold3d trimesh numpy
Written for the Ppomo project with help from Claude.
"""
import os

import numpy as np
import trimesh
from manifold3d import CrossSection, Manifold, JoinType

SEG = 32
T = 8.0
TRAVEL = 4.3
CLEAR = 0.5
STEM, ROD = 3.0, 2.5
SW, BODY, PL = 6.0, 3.5, 1.5               # tactile button

# cap springs: V-zigzag of N_DIAG diagonal beams on each side of the stem
T_SPR = 0.6
N_DIAG = 7                                  # odd, so the last vertex lands on the outer side
P_DIAG = 1.7                                # vertical pitch between vertices
V_IN = STEM + 0.95
L_SPAN = 12.0
V_OUT = V_IN + L_SPAN
WALL0, WALL1 = V_OUT + 1.0, V_OUT + 3.4
U_LOW = 14.6                                # lowest vertex
U_TOP = U_LOW + N_DIAG * P_DIAG             # top vertex (joins the stem)
LIP0 = U_TOP + T_SPR / 2 + 1.2
LIP1 = LIP0 + 2.0
CAP0 = LIP1 + TRAVEL
CAP_T = 3.0

# wedge (same as v1)
U_FACE = 7.2
WEDGE_GAP = CLEAR * 2 ** 0.5
RAMP_V0 = ROD + WEDGE_GAP - STEM - U_FACE

# rod return spring (rectangular serpentine, kept from v1, thinner)
T_ROD_SPR, L_ROD_BEAM, N_ROD_BEAMS, ROD_GAP = 0.55, L_SPAN, 7, 1.5
ROD_PITCH = T_ROD_SPR + ROD_GAP
ROD_SPR_V1 = -WALL1 - 5.5 - T_ROD_SPR / 2
ROD_SPR_VN = ROD_SPR_V1 - (N_ROD_BEAMS - 1) * ROD_PITCH
END0 = ROD_SPR_VN - T_ROD_SPR / 2 - 1.0
END1 = END0 - 2.4

# button
TACT_TIP = WALL0 - BODY - PL
ROD_TIP_GAP = 3.1
ROD_TIP = TACT_TIP - ROD_TIP_GAP

# latch
LATCH_T = 0.6                               # finger thickness
LATCH_INT = 0.3                             # how far the bump pushes the tooth (click strength)
LATCH_AT = 2.2                              # rod travel where the bump crest passes the tooth
TOOTH_X = -9.6
FINGER_Y0 = ROD + CLEAR + 1.4               # finger underside
BUMP_X = TOOTH_X - LATCH_AT


def R(v0, v1, u0, u1):
    v0, v1 = sorted([v0, v1]); u0, u1 = sorted([u0, u1])
    return CrossSection.square([v1 - v0, u1 - u0]).translate([v0, u0])


def circ(v, u, r):
    return CrossSection.circle(r, SEG).translate([v, u])


def poly(pts):
    """polygon; points must run counter-clockwise (clockwise = a hole = nothing)."""
    c = CrossSection([pts])
    assert c.area() > 0, 'polygon came out empty (clockwise?)'
    return c


def beam(a, b, t):
    """a straight beam with round ends between points a and b."""
    return CrossSection.batch_hull([circ(a[0], a[1], t / 2), circ(b[0], b[1], t / 2)])


def v_zigzag(sign_u):
    """V-zigzag springs on both sides of a stem. sign_u = +1 for the top cap, -1 for the bottom cap."""
    out = CrossSection()
    for s in (-1, 1):
        pts = []
        for k in range(N_DIAG + 1):
            u = U_TOP - k * P_DIAG
            if k == 0:
                q = STEM - 0.3                       # inside the stem
            else:
                q = V_OUT if k % 2 == 1 else V_IN
            pts.append((s * q, sign_u * u))
        for a, b in zip(pts[:-1], pts[1:]):
            out += beam(a, b, T_SPR)
        last = pts[-1]
        out += beam(last, (s * (WALL0 + 0.3), last[1]), T_SPR)      # stub into the wall
    return out


def rod_serpentine():
    h = T_ROD_SPR / 2
    out = CrossSection()
    for s in (-1, 1):
        for i in range(N_ROD_BEAMS):
            p = ROD_SPR_V1 - i * ROD_PITCH
            q0 = ROD - 0.1 if i == 0 else V_IN
            q1 = WALL0 + 0.1 if i == N_ROD_BEAMS - 1 else V_OUT
            out += R(p - h, p + h, s * q0, s * q1)
            if i < N_ROD_BEAMS - 1:
                if i % 2 == 0:
                    out += R(p - ROD_PITCH - h, p + h, s * (V_OUT - T_ROD_SPR), s * V_OUT)
                else:
                    out += R(p - ROD_PITCH - h, p + h, s * V_IN, s * (V_IN + T_ROD_SPR))
    return out.offset(0.4, JoinType.Round).offset(-0.4, JoinType.Round)


def build():
    fixed = R(END1, END0, -WALL1, WALL1)                                    # left end wall
    fixed += R(WALL0, WALL1, -LIP1, LIP1)                                   # right wall (button seat inside)
    fingers = CrossSection()
    for s in (-1, 1):
        fixed += R(END1, -WALL1, s * WALL0, s * WALL1)                      # rod-spring chamber walls
        fixed += R(-WALL1, -WALL0, s * (ROD + CLEAR), s * LIP1)             # main left wall, open for the rod
        fixed += R(STEM + CLEAR, WALL1, s * LIP0, s * LIP1)                 # lips: upper guide + stop
        fixed += R(-WALL1, -(STEM + CLEAR), s * LIP0, s * LIP1)
        fixed += R(-WALL0, -(STEM + CLEAR), s * 10.9, s * 12.4)             # arm holding the lower guide
        fixed += R(-(STEM + CLEAR) - 2.2, -(STEM + CLEAR), s * 7.5, s * 13.9)   # longer lower guide block
        fixed += R(8.0, WALL0, s * (ROD + 0.6), s * (ROD + 2.2))            # rails: rod tip guide + button fence
        # latch finger: a thin beam from the left wall, with a tooth pointing at the rod
        fy0, fy1 = FINGER_Y0, FINGER_Y0 + LATCH_T
        f = R(-WALL0 - 0.3, TOOTH_X + 0.9, fy0, fy1)
        f += poly([(TOOTH_X, ROD + CLEAR), (TOOTH_X + 0.9, fy0 + 0.01), (TOOTH_X - 0.9, fy0 + 0.01)])   # counter-clockwise
        fingers += f if s > 0 else f.mirror([0, 1])

    springs = v_zigzag(1) + v_zigzag(-1) + rod_serpentine()

    def stem(sign):
        body = poly([(-STEM, U_FACE), (STEM, U_FACE + 2 * STEM), (STEM, CAP0 + 0.5), (-STEM, CAP0 + 0.5)])
        cap = R(-9, 9, CAP0, CAP0 + CAP_T).offset(-1.2, JoinType.Round).offset(1.2, JoinType.Round)
        cap += circ(0, CAP0 + CAP_T - 0.4, 2.6) + circ(-5.4, CAP0 + CAP_T - 0.6, 2.0) + circ(5.4, CAP0 + CAP_T - 0.6, 2.0)
        m = body + cap
        return m if sign > 0 else m.mirror([0, 1])

    rod = R(ROD_SPR_V1 - 1.1, ROD_TIP, -ROD, ROD)
    lug = poly([(RAMP_V0, ROD), (RAMP_V0 + 8, ROD), (RAMP_V0 + 8, ROD + 8)])
    bump = poly([(BUMP_X - 1.1, ROD - 0.05), (BUMP_X + 1.1, ROD - 0.05), (BUMP_X, ROD + CLEAR + LATCH_INT)])
    rod += lug + lug.mirror([0, 1]) + bump + bump.mirror([0, 1])
    return fixed, fingers, springs, stem(1), stem(-1), rod


def rod_travel(d):
    return max(0.0, d - WEDGE_GAP)


def sweep(fixed, stem_t, stem_b, rod, press_top, press_bottom):
    worst = 0.0
    for d in np.arange(0.0, TRAVEL - 0.04, 0.2):
        st = stem_t.translate([0, -d if press_top else 0])
        sb = stem_b.translate([0, d if press_bottom else 0])
        r = rod.translate([rod_travel(d), 0])
        for a, b in ((st, fixed), (sb, fixed), (r, fixed), (st, r), (sb, r)):
            worst = max(worst, (a ^ b).area())
    return worst


def latch_profile(rod, fingers):
    """how far the rod's bumps push into the fingers' teeth along the travel (the click)."""
    hits = []
    for d in np.arange(0.0, TRAVEL - 0.04, 0.1):
        r = rod.translate([rod_travel(d), 0])
        hits.append((d, (r ^ fingers).area()))
    return hits


if __name__ == "__main__":
    fixed, fingers, springs, stem_t, stem_b, rod = build()
    ok = True
    allfixed = fixed + fingers
    movers = {"top stem": stem_t, "bottom stem": stem_b, "rod": rod}
    for n, mv in movers.items():
        others = allfixed
        for n2, m2 in movers.items():
            if n2 != n:
                others += m2
        a = (mv.offset(CLEAR - 0.06, JoinType.Round) ^ others).area()
        print(f"rest gap around the {n} OK:", a < 0.01); ok &= a < 0.01
    a = (springs ^ (fingers + R(-WALL0, -(STEM + CLEAR), 7.5, 13.9) + R(-WALL0, -(STEM + CLEAR), -13.9, -7.5))).area()
    print("springs clear of the latch and guides:", a < 0.01); ok &= a < 0.01
    for label, pt, pb in (("top only", True, False), ("bottom only", False, True), ("both", True, True)):
        w = sweep(fixed, stem_t, stem_b, rod, pt, pb)
        print(f"press {label}: moves freely to the stop (the latch is the only contact):", w < 0.01); ok &= w < 0.01
    hits = latch_profile(rod, fingers)
    touching = [d for d, a in hits if a > 0.005]
    if touching:
        print(f"latch: the bump rides over the teeth between {touching[0]:.1f} and {touching[-1]:.1f} mm of cap travel -> click at ~{(touching[0] + touching[-1]) / 2:.1f} mm")
        ok &= touching[-1] < TRAVEL - 0.05
    else:
        print("!! latch never engages"); ok = False
    click_cap = ROD_TIP_GAP + 0.25 + WEDGE_GAP
    print(f"tactile button clicks at ~{click_cap:.2f} mm of cap travel, stop at {TRAVEL} mm:", click_cap < TRAVEL); ok &= click_cap < TRAVEL
    # springs
    L = (L_SPAN ** 2 + P_DIAG ** 2) ** 0.5
    d = TRAVEL / N_DIAG
    I = T * T_SPR ** 3 / 12
    k_cap = 2 * (12 * 3000 * I / L ** 3) / N_DIAG
    stress = 3 * 3000 * T_SPR * d / L ** 2
    gap_closed = 2 * (P_DIAG - d) * (L_SPAN / L) - T_SPR
    print(f"cap V-springs: never touch when fully pressed: {gap_closed > 0.2} (gap {gap_closed:.2f} mm); bending stress ~{stress:.0f} MPa (PLA yields ~50)")
    ok &= gap_closed > 0.2
    k_rod = 2 * (12 * 3000 * (T * T_ROD_SPR ** 3 / 12) / L_ROD_BEAM ** 3) / N_ROD_BEAMS
    fl = 3 * 3000 * (T * LATCH_T ** 3 / 12) / (abs(-WALL0 - TOOTH_X)) ** 3 * LATCH_INT * 2
    print(f"force estimate at the click: caps ~{k_cap * click_cap / 9.81 * 1000:.0f} g + rod spring ~{k_rod * ROD_TIP_GAP / 9.81 * 1000:.0f} g "
          f"+ latch ~{fl / 9.81 * 1000:.0f} g + button ~200 g (rough, PLA)")
    solid = Manifold.extrude(fixed + fingers + springs + stem_t + stem_b + rod, T)
    for z0, z1 in ((-0.1, 1.55), (T - 1.55, T + 0.1)):
        solid -= Manifold.cube([WALL1 - WALL0 + 0.6, SW + 0.6, z1 - z0]).translate([WALL0 - 0.3, -(SW + 0.6) / 2, z0])
    nb = len(solid.decompose())
    print("one piece:", nb == 1); ok &= nb == 1
    mesh = solid.to_mesh()
    t = trimesh.Trimesh(np.asarray(mesh.vert_properties)[:, :3], np.asarray(mesh.tri_verts), process=False)
    here = os.path.dirname(os.path.abspath(__file__))
    t.export(os.path.join(here, "wedge-test-v2.stl"))
    print("size mm:", np.round(t.extents, 1), "| watertight:", t.is_watertight)
    print("ALL CHECKS OK" if ok else "CHECKS FAILED")
