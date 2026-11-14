"""
Ppomo cone clicker v1: press from the TOP, BOTTOM, LEFT, RIGHT or BACK -> the same ONE button.

How it works
  * A rod runs front-to-back through a block. In the middle it has a 45-degree CONE.
  * Four plungers (top, bottom, left, right) touch the cone with round tips.
    Push any plunger in -> it slides down the cone -> the rod moves forward the same distance.
  * The rod's back end sticks out with its own cap: push it -> the rod moves forward directly.
  * At the front, the rod's thin tip pushes a printed SPIRAL SPRING plate (like a ClickerSwitch)
    and then clicks the one 6 x 6 mm tactile button.
  * Let go -> the spiral pushes the rod back -> the cone pushes all four plungers back out.
    So ONE spring returns all five directions.
  * The cone's front face lands on a wall after 3.5 mm, so neither the button nor the spiral is crushed.

Parts (6 kinds, already oriented for printing, no supports):
  cone-housing.stl      the block. Print front face down (as exported).
  cone-rod.stl          the rod with the cone and the back cap. Print standing on its cap (as exported).
  cone-plunger.stl      print 4. Print standing on its cap (as exported).
  cone-spiral.stl       the spiral spring plate, 1.0 mm thick. Print flat.
  cone-backplate.stl    closes the back of the cone chamber. Print flat.
Assembly
  1. Slide the spiral plate into the slot on the +X side of the block.
  2. Drop the tactile button into the pocket on the front face (plunger pointing into the block).
  3. Put the rod in from the back: its thin tip goes through the hole in the spiral's centre.
  4. Press the back plate into the back opening (a drop of glue if loose).
  5. Put the 4 plungers into the side holes, round tip first.
  6. For testing, one rubber band around the 4 plunger caps keeps them in (later the silicone does this).

Needs: pip install manifold3d trimesh numpy
Written for the Ppomo project with help from Claude.
"""
import os

import numpy as np
import trimesh
from manifold3d import Manifold, CrossSection

SEG = 64
FIT = 0.3                       # clearance between moving parts and their holes (radius)
# button (6 x 6 mm tactile), its plunger points toward +Y (back)
SW, BODY, PL = 6.0, 3.5, 1.5
FRONT_WALL = 1.2
BTN_TIP = FRONT_WALL + BODY + PL          # plunger tip
TIP_GAP = 3.1                             # rod tip travel before it touches the button
STOP = 3.5                                # rod/plunger travel at the stop (click at ~3.25)
# spiral spring plate
PLATE = 22.0
PLATE_T = 1.0
SPIRAL_W, SPIRAL_GAP = 0.8, 0.8
FRAME_W = 1.5
HUB = 7.0
PIN_R = 1.5                               # rod tip radius
PLATE_Y0 = BTN_TIP + TIP_GAP + 3.4        # plate front face (the hub moves 3.5 mm forward into free space)
PLATE_Y1 = PLATE_Y0 + PLATE_T
# rod
SHAFT_R = 3.0
CONE_R0, CONE_R1, CONE_L = 9.0, 3.0, 6.0  # cone: radius 9 at its front face, 3 at its back
WALL1_Y0 = PLATE_Y1 + 0.2
WALL1_Y1 = WALL1_Y0 + 2.0                 # wall between the spiral and the cone chamber (the stop)
CONE_Y0 = WALL1_Y1 + STOP                 # cone front face at rest
CONE_Y1 = CONE_Y0 + CONE_L
CH_R = CONE_R0 + 0.6                      # cone chamber radius
CH_Y1 = CONE_Y1 + 0.8
BACK_T = 2.5
HOUSE_Y1 = CH_Y1 + BACK_T                 # back face of the block
CAP_GAP = 5.5                             # caps stand off the block: > STOP + backplate flange 1.2 + margin
# plungers
TIP_R = 3.0
CONTACT_R = 7.5                           # cone radius where the plungers touch it
YC = CONE_Y0 + (CONE_R0 - CONTACT_R)      # plunger axis position along the rod
RHO_S = CONTACT_R + TIP_R * 2 ** 0.5      # plunger tip centre (radial)
HALF = 14.0                               # block half-size (X and Z)
PCAP_R, PCAP_T = 6.5, 2.5


def cyl_y(y0, y1, r0, r1=None):
    """cylinder (or cone) along +Y from y0 to y1, centred on the Y axis."""
    r1 = r0 if r1 is None else r1
    return Manifold.cylinder(y1 - y0, r0, r1, SEG).rotate([-90, 0, 0]).translate([0, y0, 0])


def box(x0, x1, y0, y1, z0, z1):
    return Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


DIRS = {"right": (1, 0, 0), "left": (-1, 0, 0), "top": (0, 0, 1), "bottom": (0, 0, -1)}
ROT = {"right": [0, 90, 0], "left": [0, -90, 0], "top": [0, 0, 0], "bottom": [180, 0, 0]}


def plunger_local():
    """built along +Z: round tip, stem, cap."""
    m = Manifold.sphere(TIP_R, SEG).translate([0, 0, RHO_S])
    m += Manifold.cylinder(HALF + CAP_GAP - RHO_S, TIP_R, TIP_R, SEG).translate([0, 0, RHO_S])
    cap = Manifold.cylinder(PCAP_T, PCAP_R, PCAP_R, SEG).translate([0, 0, HALF + CAP_GAP])
    return m + cap


def plunger(name, travel=0.0):
    return plunger_local().translate([0, 0, -travel]).rotate(ROT[name]).translate([0, YC, 0])


def rod(forward=0.0):
    pin_y0 = BTN_TIP + TIP_GAP
    m = cyl_y(pin_y0, PLATE_Y1 + 0.01, PIN_R)                 # thin tip (through the spiral hub)
    m += cyl_y(PLATE_Y1, CONE_Y0 + 0.01, SHAFT_R)             # shoulder pushes the hub
    m += cyl_y(CONE_Y0, CONE_Y1, CONE_R0, CONE_R1)            # the cone
    m += cyl_y(CONE_Y1 - 0.01, HOUSE_Y1 + CAP_GAP + 0.01, SHAFT_R)
    m += cyl_y(HOUSE_Y1 + CAP_GAP, HOUSE_Y1 + CAP_GAP + 2.5, 7.0)   # back cap
    return m.translate([0, -forward, 0])


def housing():
    h = box(-HALF, HALF, 0, HOUSE_Y1, -HALF, HALF)
    # front: button pocket + leg slots through the front wall
    p = SW / 2 + 0.2
    h -= box(-p, p, FRONT_WALL, FRONT_WALL + BODY + 0.2, -p, p)
    for s in (-1, 1):
        lo, hi = sorted([s * 2.45, s * 4.05])
        h -= box(-p, p, -1, FRONT_WALL + 0.1, lo, hi)
    # space for the button plunger + the rod tip + the spiral hub moving forward
    c = PLATE / 2 - FRAME_W                                    # square, so the spiral arms never rub; the frame sits on a ledge
    h -= box(-c, c, FRONT_WALL + BODY, PLATE_Y0 + 0.01, -c, c)
    # spiral slot, open on the +X face so the plate slides in
    s = PLATE / 2 + 0.3
    h -= box(-s, HALF + 1, PLATE_Y0 - 0.1, PLATE_Y1 + 0.2, -s, s)
    # wall with a bore for the shoulder, then the cone chamber (open at the back for assembly)
    h -= cyl_y(PLATE_Y1, WALL1_Y1 + 0.01, SHAFT_R + FIT)
    h -= cyl_y(WALL1_Y1, HOUSE_Y1 + 1, CH_R)
    # four plunger bores
    for name in DIRS:
        bore = Manifold.cylinder(HALF + 1 - CH_R + 1, TIP_R + FIT, TIP_R + FIT, SEG).translate([0, 0, CH_R - 1])
        h -= bore.rotate(ROT[name]).translate([0, YC, 0])
    return h


def backplate():
    """a plug that closes the cone chamber; its flange sits on the back face."""
    m = cyl_y(CH_Y1, HOUSE_Y1, CH_R - 0.05)                    # snug plug
    m += cyl_y(HOUSE_Y1, HOUSE_Y1 + 1.2, CH_R + 2.5)           # flange
    m -= cyl_y(CH_Y1 - 1, HOUSE_Y1 + 2, SHAFT_R + FIT)
    return m


def spiral_plate(world=True):
    """flat spring plate in the X-Z plane: square frame + square hub joined by TWO square-spiral arms
    (180 degrees apart, so the hub moves straight instead of tilting). 1.0 mm thick."""
    half, a = PLATE / 2, HUB / 2
    inner = half - FRAME_W
    w = SPIRAL_W
    grow = 2 * (SPIRAL_W + SPIRAL_GAP)              # radius gained per full turn (2 arms share the space)
    corners = [(1, 1), (1, -1), (-1, -1), (-1, 1)]
    m2 = CrossSection.square([PLATE, PLATE]).translate([-half, -half]) - CrossSection.square([2 * inner, 2 * inner]).translate([-inner, -inner])
    m2 += CrossSection.square([HUB, HUB]).translate([-a, -a])
    for arm in (0, 2):
        k, pts = 0, []
        while True:
            r = a + k * grow / 4
            sx, sz = corners[(k + arm) % 4]
            pts.append((sx * r, sz * r))
            if r > inner:
                break
            k += 1
        for (x0, z0), (x1, z1) in zip(pts[:-1], pts[1:]):
            m2 += (CrossSection.circle(w / 2, 16).translate([x0, z0]) + CrossSection.circle(w / 2, 16).translate([x1, z1])).hull()
    m2 -= CrossSection.circle(PIN_R + 0.25, SEG)
    m = Manifold.extrude(m2, PLATE_T)                  # along +Z, z = 0..PLATE_T
    if world:
        # map 2D (x, z) -> world (x, z), thickness along +Y at PLATE_Y0
        m = m.rotate([-90, 0, 0]).translate([0, PLATE_Y0, 0])
        m = m.mirror([0, 0, 1])                        # keep the 2D z sense (rotation flips it)
    return m


def to_tm(m):
    mesh = m.to_mesh()
    return trimesh.Trimesh(np.asarray(mesh.vert_properties)[:, :3], np.asarray(mesh.tri_verts), process=False)


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(here, "cone-clicker-v1")
    os.makedirs(out, exist_ok=True)
    H, B, SP = housing(), backplate(), spiral_plate()
    ok = True

    def vol(a, b):
        return (a ^ b).volume()

    # 1) at rest nothing overlaps (the plunger tips only touch the cone)
    parts = {"rod": rod(), "backplate": B, "spiral": SP}
    for n in DIRS:
        parts["plunger " + n] = plunger(n)
    names = list(parts)
    for i, a in enumerate(names):
        v = vol(parts[a], H)
        if v > 0.02:
            print(f"!! {a} overlaps the block at rest: {v:.2f} mm3"); ok = False
        for b in names[i + 1:]:
            if {a, b} == {"backplate", "spiral"}:
                continue
            v = vol(parts[a], parts[b])
            if v > 0.05:
                print(f"!! {a} overlaps {b} at rest: {v:.2f} mm3"); ok = False
    print("rest: no overlaps (tips just touch the cone):", ok)
    # 2) press each direction: the pressed plunger goes in d, the rod forward d; nothing hits the block or plate
    for press in list(DIRS) + ["back"]:
        worst = 0.0
        for d in np.arange(0.0, STOP - 0.04, 0.25):
            R_ = rod(d)
            worst = max(worst, vol(R_, H), vol(R_, B))
            for n in DIRS:
                p = plunger(n, d if n == press else 0.0)
                worst = max(worst, vol(p, H))
                if n == press:
                    worst = max(worst, vol(p, R_) - 0.05)       # rolling contact only
        good = worst < 0.05
        ok &= good
        print(f"press {press:6s}: free all the way to the stop: {good} (worst overlap {worst:.3f} mm3)")
    # 3) other plungers lose contact (the cone moves away from them), so they never jam
    # 4) the stop: cone face meets the wall exactly at STOP; the button clicks before that
    print(f"rod tip touches the button at {TIP_GAP} mm, clicks at ~{TIP_GAP + 0.25:.2f} mm, cone lands on the stop at {STOP} mm:", TIP_GAP + 0.25 < STOP)
    ok &= TIP_GAP + 0.25 < STOP
    one = all(len(m.decompose()) == 1 for m in (H, rod(), plunger_local(), B, SP))
    print("each part is one piece:", one); ok &= one
    # export, oriented for printing
    t = to_tm(H)                                               # front face (y = 0) down: rotate +Y to +Z
    t.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0])); t.apply_translation(-t.bounds[0])
    t.export(os.path.join(out, "cone-housing.stl"))
    hs = np.round(t.extents, 1)
    t = to_tm(rod())                                           # stand on the back cap
    t.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0])); t.apply_translation(-t.bounds[0])
    t.export(os.path.join(out, "cone-rod.stl"))
    t = to_tm(plunger_local())                                 # stand on its cap
    t.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0])); t.apply_translation(-t.bounds[0])
    t.export(os.path.join(out, "cone-plunger.stl"))
    t = to_tm(spiral_plate(world=False)); t.apply_translation(-t.bounds[0])
    t.export(os.path.join(out, "cone-spiral.stl"))
    t = to_tm(B)
    t.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0])); t.apply_translation(-t.bounds[0])
    t.export(os.path.join(out, "cone-backplate.stl"))
    full = H + B + SP + rod()
    for n in DIRS:
        full += plunger(n)
    to_tm(full).export(os.path.join(out, "cone-assembled-view.stl"))
    print("block size mm:", hs, "| whole thing with caps mm:", np.round(to_tm(full).extents, 1))
    print("ALL CHECKS OK" if ok else "CHECKS FAILED")
