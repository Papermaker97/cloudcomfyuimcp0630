"""
Ppomo skeleton v2: a real 3D skeleton that fits inside the 110 mm Ppomo v6 body.

Parts (print separately; each is already oriented for printing, no supports except inside the skull):
  skel-axial.stl        skull + neck + spine in one piece.
                        skull: hollow, holds an Arduino Nano 33 IoT (45 x 18 mm) slid in from below
                        spine: hollow wire channel, and 4 pockets for 6 x 6 mm tactile buttons
                               (top, left, right, back), plus square slots for the clicker units
  skel-rib-R.stl / skel-rib-L.stl   side clickers that look like ribs
  skel-vertebra.stl                 top clicker that looks like a row of vertebrae
  skel-pelvis.stl                   back clicker that looks like a pelvis

Each clicker unit is ONE printed piece, no separate spring:
  feet (pinned into the spine) - zigzag springs - a bone-shaped cap with a nub
  squeeze the cap -> it moves in ~1.2 mm on the zigzag springs (soft "squish") -> the nub clicks the
  button -> the cap lands on the stops ~0.35 mm later, so neither the button nor the springs are crushed.
  Release -> the zigzag springs push the cap back out.
The springs bend in the print plane, so their thin walls are printed along their length (strong).
All 4 buttons are wired in parallel to one Arduino pin: any squeeze = one count.

Run:  python make_skeleton_v2.py            (6 x 6 mm buttons, the default)
      python make_skeleton_v2.py 12         (12 x 12 mm buttons; may not fit, the fit check will say)
Needs: pip install manifold3d trimesh numpy rtree
World axes (mm, same as ppomo-v6-body-110mm.stl): X = left/right, Y = length (face at -Y), Z = up.
Written for the Ppomo project with help from Claude.
"""
import os
import sys

import numpy as np
import trimesh
from manifold3d import CrossSection, Manifold, JoinType

SEG = 40
SIZE = sys.argv[1] if len(sys.argv) > 1 else "6"
if SIZE == "12":
    SW, BODY, PL = 12.0, 3.5, 3.8
else:
    SW, BODY, PL = 6.0, 3.5, 1.5           # 6 x 6 x 5 mm tactile button
P = SW / 2 + 0.2                           # half pocket width
POCKET = BODY + 0.2                        # pocket depth for the button body
LEG = 3.0                                  # room behind the button for its legs
TIP = PL - 0.2                             # plunger tip, measured out from the spine face

# clicker unit (local 2D: u = outward from the spine face, v = along the face)
NUB_FREE = 1.2                             # soft travel before the click
STOP = NUB_FREE + 0.35                     # cap lands on the stops here
F = max(3.0, PL + 1.5)                     # foot (stop pad) height
UC = F + STOP                              # cap inner face
CT = 3.5                                   # cap thickness
T_SPR, LVL = 0.8, 1.6                      # spring wall thickness, spacing between zigzag levels
PIN = 2.8                                  # square pin
CLEAR = 0.45                               # print-in-place gap

# axial skeleton placement (from the body profile)
YC = 8.0                                   # where the 3 front clickers sit along the body
SP_X, SP_Z0, SP_Z1, SP_Y0, SP_Y1 = 12.0, 8.0, 27.0, -16.0, 35.0
YT = 14.0                                  # top clicker sits a bit further back (the back is highest there)
ZS = 16.0                                  # side-button height
ZR = 19.0                                  # back-button height


def rect(x0, x1, y0, y1):
    return CrossSection.square([x1 - x0, y1 - y0]).translate([x0, y0])


def circ(x, y, r):
    return CrossSection.circle(r, SEG).translate([x, y])


def box(x0, x1, y0, y1, z0, z1):
    return Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def rbox(x0, x1, y0, y1, z0, z1, r):
    pts = []
    for x in (x0 + r, x1 - r):
        for y in (y0 + r, y1 - r):
            for z in (z0 + r, z1 - r):
                pts.append(Manifold.sphere(r, 24).translate([x, y, z]))
    return Manifold.batch_hull(pts)


# ---------------------------------------------------------------- clicker unit (2D profile)
def unit_profile(cv, ls, bumps):
    """cv: half-length of the cap along the face; ls: zigzag segment length; bumps: [(v, r)] bone bumps."""
    vp0 = P + 0.6                                         # stop pads start just outside the plunger
    vpin = vp0 + 1.6
    v_post = cv + ls + 1.2
    fixed = CrossSection()
    for s in (-1, 1):
        lo, hi = sorted([s * vp0, s * (v_post + 3)])
        fixed += rect(0, 1.4, lo, hi)                     # base bar
        lo, hi = sorted([s * vp0, s * (vp0 + 3.2)])
        fixed += rect(0, F, lo, hi)                       # stop pad
        lo, hi = sorted([s * v_post, s * (v_post + 3)])
        fixed += rect(0, UC + CT, lo, hi)                 # spring post
        lo, hi = sorted([s * (vpin - PIN / 2), s * (vpin + PIN / 2)])
        fixed += rect(-5.0, 0.01, lo, hi)                 # square pin into the spine
    cap = rect(UC, UC + CT, -cv, cv).offset(-1.0, JoinType.Round).offset(1.0, JoinType.Round)
    for v, r in bumps:
        cap += circ(UC + CT - 0.6, v, r)
    cap += rect(TIP + NUB_FREE, UC + 0.5, -1.5, 1.5)       # nub
    spr = CrossSection()
    l1 = UC + CT - 0.6
    l2, l3 = l1 - LVL, l1 - 2 * LVL
    h = T_SPR / 2
    for s in (-1, 1):
        def seg(v0, v1, u):
            lo, hi = sorted([s * v0, s * v1])
            return rect(u - h, u + h, lo, hi)
        spr += seg(cv - 0.8, cv + ls, l1)                  # from the cap end, outward
        spr += seg(cv + ls - T_SPR, cv + ls, l2 - h) + rect(0, 0, 0, 0) if False else seg(cv + ls - T_SPR, cv + ls, l1)
        lo, hi = sorted([s * (cv + ls - T_SPR), s * (cv + ls)])
        spr += rect(l2 - h, l1 + h, lo, hi)                # turn 1
        spr += seg(cv + 1.6, cv + ls, l2)                  # back toward the cap
        lo, hi = sorted([s * (cv + 1.6), s * (cv + 1.6 + T_SPR)])
        spr += rect(l3 - h, l2 + h, lo, hi)                # turn 2
        spr += seg(cv + 1.6, v_post + 0.3, l3)             # out to the post
    return fixed, cap, spr, v_post + 3


def unit_solid(cv, ls, bumps, width):
    fixed, cap, spr, vmax = unit_profile(cv, ls, bumps)
    gap = (cap.offset(CLEAR - 0.05, JoinType.Round) ^ (fixed - rect(-6, 0.02, -100, 100))).area()
    prof = fixed + cap + spr
    solid = Manifold.extrude(prof, width).translate([0, 0, -width / 2])
    return solid, gap, vmax


def place(m, origin, n, v, w):
    """map local (u, v, w) to world: x_world = origin + u*n + v*v + w*w (right-handed)."""
    M = [[n[0], v[0], w[0], origin[0]], [n[1], v[1], w[1], origin[1]], [n[2], v[2], w[2], origin[2]]]
    return m.transform(M)


def slot_for_pins(origin, n, v, w, cv, ls, width):
    """the square slots the unit's pins slide into (world solid to subtract from the spine)."""
    vp0 = P + 0.6
    vpin = vp0 + 1.6
    s2d = CrossSection()
    for s in (-1, 1):
        lo, hi = sorted([s * (vpin - PIN / 2 - 0.2), s * (vpin + PIN / 2 + 0.2)])
        s2d += rect(-5.4, 0.5, lo, hi)
    return place(Manifold.extrude(s2d, width + 0.4).translate([0, 0, -(width + 0.4) / 2]), origin, n, v, w)


# ---------------------------------------------------------------- axial skeleton
def axial():
    spine = rbox(-SP_X, SP_X, SP_Y0, SP_Y1, SP_Z0, SP_Z1, 3.0)
    # skull: wide at the bottom (the 45 mm board lies across it), narrower dome on top like a cranium
    skull = Manifold.batch_hull([rbox(-24.4, 24.4, -46, -22, 8, 17, 4.0), rbox(-17, 17, -45, -23, 14, 27, 7.0)])
    skull -= Manifold.batch_hull([rbox(-22.8, 22.8, -44.4, -23.6, 9.6, 16, 3.0), rbox(-15.4, 15.4, -43.4, -24.6, 13, 25.4, 5.4)])
    skull -= box(-22.9, 22.9, -43.6, -24.4, 7, 12.6)            # board (45 x 18 mm) slides in from below: 45.8 x 19.2 mm opening
    neck = rbox(-8, 8, -24, -12, 12, 26, 3.0)
    ax = spine + skull + neck
    # wire channel from the back pocket to the skull
    ax -= box(-3, 3, -26, SP_Y1 - POCKET - LEG + 0.5, 17, 25)
    # button pockets (open on the face) + a slot from each into the channel
    ax -= box(-P, P, YT - P, YT + P, SP_Z1 - POCKET - LEG, SP_Z1 + 1)                    # top
    for s in (-1, 1):
        lo, hi = sorted([s * (SP_X - POCKET - LEG), s * (SP_X + 1)])
        ax -= box(lo, hi, YC - P, YC + P, ZS - P, ZS + P)                                # sides
        lo, hi = sorted([s * 2.5, s * (SP_X - POCKET - LEG + 0.5)])
        ax -= box(lo, hi, YC - 2, YC + 2, ZS, 21)
    ax -= box(-P, P, SP_Y1 - POCKET - LEG, SP_Y1 + 1, ZR - P, ZR + P)                   # back
    return ax


UNITS = {
    # name: origin, n (outward), v (along face), w (extrusion), cv, ls, width, bumps (bone look)
    "rib-R":    ((SP_X, YC, ZS), (1, 0, 0), (0, 1, 0), (0, 0, 1), 8.0, 12.0, 14.0, [(-5.5, 2.2), (0, 2.2), (5.5, 2.2)]),
    "rib-L":    ((-SP_X, YC, ZS), (-1, 0, 0), (0, 1, 0), (0, 0, -1), 8.0, 12.0, 14.0, [(-5.5, 2.2), (0, 2.2), (5.5, 2.2)]),
    "vertebra": ((0, YT, SP_Z1), (0, 0, 1), (0, 1, 0), (-1, 0, 0), 8.0, 12.0, 14.0, [(-5.5, 2.4), (0, 2.8), (5.5, 2.4)]),
    "pelvis":   ((0, SP_Y1, ZR), (0, 1, 0), (1, 0, 0), (0, 0, -1), 7.0, 9.0, 14.0, [(-4.5, 3.6), (4.5, 3.6)]),
}


def to_tm(m):
    mesh = m.to_mesh()
    return trimesh.Trimesh(np.asarray(mesh.vert_properties)[:, :3], np.asarray(mesh.tri_verts), process=False)


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(here, f"skeleton-v2-{SIZE}mm")
    os.makedirs(out, exist_ok=True)
    ax = axial()
    world = {}
    print_parts = {}
    for name, (o, n, v, w, cv, ls, width, bumps) in UNITS.items():
        local, gap, vmax = unit_solid(cv, ls, bumps, width)
        if gap > 0.01:
            print(f"!! {name}: cap closer than {CLEAR} mm to fixed parts ({gap:.2f} mm2)")
        world[name] = place(local, o, n, v, w)
        ax -= slot_for_pins(o, n, v, w, cv, ls, width)
        print_parts[name] = local                     # local frame: extrusion along Z = print flat
    # ---- checks ----
    ok = True
    ax_b = len(ax.decompose())
    print("axial bodies:", ax_b)
    for name, m in world.items():
        nb = len(m.decompose())
        ov = (m ^ ax).volume()
        # pins sit inside the slots, so allow only the tiny pin/slot contact (should be ~0)
        print(f"{name:9s} bodies {nb} | overlap with spine/skull {ov:.2f} mm3")
        ok &= nb == 1 and ov < 0.5
    names = list(world)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            ov = (world[names[i]] ^ world[names[j]]).volume()
            if ov > 0.01:
                ok = False
                print(f"!! {names[i]} hits {names[j]} ({ov:.2f} mm3)")
    # fit inside the body: every skeleton point at least MARGIN mm inside the surface
    body = trimesh.load(os.path.join(here, "..", "ppomo-mold", "ppomo-v6-body-110mm.stl"))
    full = ax
    for m in world.values():
        full += m
    tf = to_tm(full)
    pts = np.vstack([tf.sample(3000), tf.vertices[::max(1, len(tf.vertices) // 3000)]])
    dist = np.concatenate([trimesh.proximity.signed_distance(body, pts[i:i + 400]) for i in range(0, len(pts), 400)])   # positive = inside
    print(f"fit: min distance to the body surface {dist.min():.1f} mm (5th percentile {np.percentile(dist, 5):.1f} mm)")
    print("assembled size mm:", np.round(tf.extents, 1))
    tf.export(os.path.join(out, "skel-assembled-view.stl"))
    # ---- export print parts ----
    to_tm(ax).export(os.path.join(out, "skel-axial.stl"))
    for name, m in print_parts.items():
        t = to_tm(m)
        t.apply_translation(-t.bounds[0])
        t.export(os.path.join(out, f"skel-{name}.stl"))
    print("all checks OK" if ok else "CHECKS FAILED")
