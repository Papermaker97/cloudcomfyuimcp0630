"""
Ppomo skeleton v3: prints as modelled, clicks from 5 directions (top, belly, left, right, butt).

Fixes over v2:
  * every button now sits on a solid LAND (ledge) so a press clicks it instead of pushing it back;
    its legs go down two slots beside the land into the wire channel
  * softer zigzag springs (0.8 mm walls, only 4 mm tall, 3 levels 2.2 mm apart so levels never touch)
  * clicker units slide into DOVETAIL slots (cannot pull out); each slot is closed at one end so the
    unit stops centred over its button
  * a BELLY clicker; the skull and spine now share one flat underside for printing

Parts (all already oriented for printing):
  skel-axial.stl     skull (bay for an Arduino Nano 33 IoT, 45 x 18 mm, from below) + neck + hollow spine
                     with 5 pockets for 6 x 6 mm tactile buttons. Print flat side down. The belly pocket and
                     slots face the bed (short bridges). The skull dome may want supports inside.
  skel-rib-R / rib-L / vertebra / belly / pelvis .stl   the 5 clicker units, printed flat, no supports.

One clicker unit (one printed piece, no separate spring):
  dovetail feet - zigzag springs - bone-shaped cap with a nub.
  Squeeze: the cap travels ~1.0 mm on the springs (soft), the nub then clicks the button (~0.25 mm);
  stop pads catch the cap at 1.7 mm so the springs are never crushed. Release: the springs push it back.
Wire all 5 buttons in parallel to one pin: any squeeze = one count.

MEASURE YOUR BUTTON first: 6 x 6 mm body, BODY = body height (3.5), PL = plunger above the body (1.5).
Needs: pip install manifold3d trimesh numpy rtree
World axes (mm, same as ppomo-v6-body-110mm.stl): X = left/right, Y = length (face at -Y), Z = up, floor Z = 0.
Written for the Ppomo project with help from Claude.
"""
import os

import numpy as np
import trimesh
from manifold3d import CrossSection, Manifold, JoinType

SEG = 40
# ---- button (6 x 6 mm tactile) ----
SW, BODY, PL = 6.0, 3.5, 1.5
P = SW / 2 + 0.2                 # half pocket size along v
PW = 3.9                         # half pocket size along w (the legs come out on these two sides)
POCKET = BODY + 0.2              # the body sits 0.2 mm below the face
TIP = PL - 0.2                   # plunger tip above the face
LEG0, LEG1 = 2.45, 4.05          # leg slots beside the land

# ---- clicker unit (local 2D: u = out of the face, v = along the face; extruded along w) ----
W = 10.0                         # unit width
SPR_H = 4.0                      # springs are only this tall (softer)
NUB_FREE = 1.0                   # soft travel before the nub touches the plunger
STOP = 1.7                       # the cap lands on the stop pads here
F = 3.0                          # stop pad height
UC = F + STOP                    # cap inner face
CT = 3.0                         # cap thickness
BASE = 1.2
T_SPR, LVL = 0.8, 2.2            # spring wall, spacing of the zigzag levels
VPIN = 6.6                       # dovetail centre
DT_NECK, DT_FLARE, DT_D = 1.4, 2.0, 3.0
CLEAR = 0.45

# ---- axial skeleton ----
CH = 3.0                         # wire channel half-size
LAND = 1.4
SP_X = 12.0
SP_Z0 = 14.0
SP_Z1 = SP_Z0 + 2 * (CH + LAND + POCKET)
ZM = (SP_Z0 + SP_Z1) / 2
SP_Y0, SP_Y1 = -16.0, 35.0
Y_TOP = 15.0                     # the clickers are staggered along the spine so their slots never meet
Y_BELLY = 6.0
Y_SIDE = 10.5


def rect(x0, x1, y0, y1):
    return CrossSection.square([x1 - x0, y1 - y0]).translate([x0, y0])


def srect(u0, u1, s, v0, v1):
    lo, hi = sorted([s * v0, s * v1])
    return rect(u0, u1, lo, hi)


def circ(x, y, r):
    return CrossSection.circle(r, SEG).translate([x, y])


def box(x0, x1, y0, y1, z0, z1):
    return Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def rbox(x0, x1, y0, y1, z0, z1, r):
    assert min(x1 - x0, y1 - y0, z1 - z0) >= 2 * r - 1e-6, 'rbox: radius too big for the box'
    return Manifold.batch_hull([Manifold.sphere(r, 24).translate([x, y, z])
                                for x in (x0 + r, x1 - r) for y in (y0 + r, y1 - r) for z in (z0 + r, z1 - r)])


def place(m, origin, n, v, w):
    M = [[n[0], v[0], w[0], origin[0]], [n[1], v[1], w[1], origin[1]], [n[2], v[2], w[2], origin[2]]]
    return m.transform(M)


def lbox(u0, u1, v0, v1, w0, w1):
    return Manifold.cube([u1 - u0, v1 - v0, w1 - w0]).translate([u0, v0, w0])


# ------------------------------------------------------------------ clicker unit
def dovetail(s, grow=0.0, depth=DT_D):
    a = srect(-0.01, 0.01, s, VPIN - DT_NECK - grow, VPIN + DT_NECK + grow)
    b = srect(-depth, -depth + 0.01, s, VPIN - DT_FLARE - grow, VPIN + DT_FLARE + grow)
    return CrossSection.batch_hull([a, b])


def unit_profiles(cv, ls, bumps):
    v_post = cv + ls + 1.2
    fixed = CrossSection()
    for s in (-1, 1):
        fixed += srect(0, BASE, s, P + 0.6, v_post + 3)            # base bar (leaves the plunger free)
        fixed += srect(0, F, s, P + 0.6, P + 3.8)                   # stop pad
        fixed += srect(0, UC + CT, s, v_post, v_post + 3)           # spring post
        fixed += circ(UC + CT - 0.3, s * (v_post + 1.5), 1.0)       # small rounded knob on the post
        fixed += dovetail(s)
    cap = rect(UC, UC + CT, -cv, cv).offset(-1.0, JoinType.Round).offset(1.0, JoinType.Round)
    for v, r in bumps:
        cap += circ(UC + CT - 0.6, v, r)
    cap += rect(TIP + NUB_FREE, UC + 0.5, -1.5, 1.5)                # nub
    l1 = UC + CT - 0.6
    l2, l3 = l1 - LVL, l1 - 2 * LVL
    h = T_SPR / 2
    spr = CrossSection()
    for s in (-1, 1):
        spr += srect(l1 - h, l1 + h, s, cv - 0.8, cv + ls)                       # level 1: from the cap outward
        spr += srect(l2 - h, l1 + h, s, cv + ls - T_SPR, cv + ls)                # turn
        spr += srect(l2 - h, l2 + h, s, cv + 1.6, cv + ls)                       # level 2: back toward the cap
        spr += srect(l3 - h, l2 + h, s, cv + 1.6, cv + 1.6 + T_SPR)              # turn
        spr += srect(l3 - h, l3 + h, s, cv + 1.6, v_post + 0.3)                  # level 3: out to the post
    return fixed, cap, spr


def unit_solid(cv, ls, bumps):
    fixed, cap, spr = unit_profiles(cv, ls, bumps)
    body = Manifold.extrude(fixed + cap, W).translate([0, 0, -W / 2])
    springs = Manifold.extrude(spr, SPR_H).translate([0, 0, -W / 2])
    # checks on the 2D profile
    above = fixed - rect(-10, 0.02, -100, 100)
    rest_gap = (cap.offset(CLEAR - 0.05, JoinType.Round) ^ above).area()
    early_hit = (cap.translate([-(STOP - 0.05), 0]) ^ above).area()           # must still be free just before the stop
    return body + springs, rest_gap, early_hit


def stiffness(ls):
    """rough upper bound (N/mm): 3 guided beams in series per side, 2 sides, PLA E = 3000 MPa."""
    I = SPR_H * T_SPR ** 3 / 12
    k = [12 * 3000 * I / L ** 3 for L in (ls + 0.8, ls - 1.6, ls - 0.1)]
    return 2 / sum(1 / x for x in k)


# ------------------------------------------------------------------ axial skeleton
def pocket_cut(depth_to_channel):
    """button pocket + two leg slots (local coords, face at u = 0)."""
    cut = lbox(-POCKET, 1.0, -P, P, -PW, PW)
    for s in (-1, 1):
        lo, hi = sorted([s * LEG0, s * LEG1])
        cut += lbox(-(depth_to_channel + 0.5), -POCKET + 0.01, -P, P, lo, hi)
    return cut


def slot_cut():
    """dovetail slots, closed at w = -(W/2 + 0.2) so the unit stops centred, open toward +w."""
    s2d = dovetail(1, 0.15, DT_D + 0.3) + dovetail(-1, 0.15, DT_D + 0.3)
    return Manifold.extrude(s2d, 40).translate([0, 0, -(W / 2 + 0.2)])


UNITS = {
    # name: origin, n (out), v (along), w (slide-in axis), cv, ls, depth from face to the channel, bumps
    "vertebra": ((0, Y_TOP, SP_Z1), (0, 0, 1), (0, 1, 0), (-1, 0, 0), 8.0, 10.0, SP_Z1 - ZM - CH, [(-5.2, 1.8), (0, 2.2), (5.2, 1.8)]),
    "belly":    ((0, Y_BELLY, SP_Z0), (0, 0, -1), (0, 1, 0), (1, 0, 0), 8.0, 10.0, ZM - CH - SP_Z0, [(-5.2, 1.8), (0, 1.8), (5.2, 1.8)]),
    "rib-R":    ((SP_X, Y_SIDE, ZM), (1, 0, 0), (0, 1, 0), (0, 0, 1), 8.0, 10.0, SP_X - CH, [(-5.2, 1.8), (0, 1.8), (5.2, 1.8)]),
    "rib-L":    ((-SP_X, Y_SIDE, ZM), (-1, 0, 0), (0, 1, 0), (0, 0, -1), 8.0, 10.0, SP_X - CH, [(-5.2, 1.8), (0, 1.8), (5.2, 1.8)]),
    "pelvis":   ((0, SP_Y1, ZM), (0, 1, 0), (1, 0, 0), (0, 0, -1), 7.0, 9.0, POCKET + LAND, [(-4.2, 2.4), (4.2, 2.4)]),
}


def axial():
    spine = rbox(-SP_X, SP_X, SP_Y0, SP_Y1, SP_Z0, SP_Z1, 2.0)
    skull = Manifold.batch_hull([rbox(-24.4, 24.4, -46, -22, SP_Z0, SP_Z0 + 8, 4.0), rbox(-17, 17, -45, -23, SP_Z0 + 3, SP_Z0 + 13, 5.0)])
    skull -= Manifold.batch_hull([rbox(-22.8, 22.8, -44.4, -23.6, SP_Z0 + 1.6, SP_Z0 + 7, 2.5), rbox(-15.4, 15.4, -43.4, -24.6, SP_Z0 + 4, SP_Z0 + 11.4, 3.5)])
    skull -= box(-22.9, 22.9, -43.6, -24.4, SP_Z0 - 1, SP_Z0 + 4.6)      # board bay, from below
    neck = rbox(-8, 8, -24, -12, SP_Z0 + 1, SP_Z1 - 1, 3.0)
    ax = spine + skull + neck
    ax -= box(-CH, CH, -26, SP_Y1 - POCKET - LAND, ZM - CH, ZM + CH)      # wire channel into the skull
    for name, (o, n, v, w, cv, ls, depth, bumps) in UNITS.items():
        ax -= place(pocket_cut(depth), o, n, v, w)
        ax -= place(slot_cut(), o, n, v, w)
    return ax ^ box(-100, 100, -100, 100, SP_Z0, 100)                     # flat underside for printing


def to_tm(m):
    mesh = m.to_mesh()
    return trimesh.Trimesh(np.asarray(mesh.vert_properties)[:, :3], np.asarray(mesh.tri_verts), process=False)


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(here, "skeleton-v3")
    os.makedirs(out, exist_ok=True)
    ok = True
    ax = axial()
    print("axial: bodies", len(ax.decompose()), "| underside z", round(to_tm(ax).bounds[0][2], 2))
    ok &= len(ax.decompose()) == 1
    world, local = {}, {}
    for name, (o, n, v, w, cv, ls, depth, bumps) in UNITS.items():
        m, rest_gap, early_hit = unit_solid(cv, ls, bumps)
        local[name] = m
        world[name] = place(m, o, n, v, w)
        # button support: solid just behind the pocket (the land), empty where the button body goes
        land = (place(lbox(-POCKET - 1.0, -POCKET - 0.2, -1, 1, -1, 1), o, n, v, w) ^ ax).volume()
        room = (place(lbox(-POCKET + 0.1, 0, -P + 0.1, P - 0.1, -3.0, 3.0), o, n, v, w) ^ ax).volume()
        legs = (place(lbox(-POCKET - 1.0, -POCKET - 0.2, -1, 1, LEG0 + 0.2, LEG1 - 0.2), o, n, v, w) ^ ax).volume()
        ov = (world[name] ^ ax).volume()
        nb = len(m.decompose())
        k = stiffness(ls)
        good = nb == 1 and ov < 0.01 and land > 3.1 and room < 0.01 and legs < 0.01 and rest_gap < 0.01 and early_hit < 0.01
        ok &= good
        print(f"{name:9s} {'OK ' if good else 'BAD'} one piece: {nb == 1} | hits spine: {ov:.2f} | button land: {land > 3.1} | pocket clear: {room < 0.01} "
              f"| leg slots open: {legs < 0.01} | cap free until stop: {early_hit < 0.01} | force to click <= {(k * (NUB_FREE + 0.25) + 2.5) / 9.81:.2f} kg")
    names = list(world)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            ov = (world[names[i]] ^ world[names[j]]).volume()
            if ov > 0.01:
                ok = False
                print(f"!! {names[i]} hits {names[j]} ({ov:.2f} mm3)")
    l1 = UC + CT - 0.6
    print(f"spring levels: gap {LVL - T_SPR:.1f} mm between levels, worst closing {STOP * 2 / 3:.2f} mm -> never touch: {LVL - T_SPR > STOP * 2 / 3}")
    ok &= LVL - T_SPR > STOP * 2 / 3
    # fit inside the body
    body = trimesh.load(os.path.join(here, "..", "ppomo-mold", "ppomo-v6-body-110mm.stl"))
    full = ax
    for m in world.values():
        full += m
    tf = to_tm(full)
    pts = np.vstack([tf.sample(3000), tf.vertices[::max(1, len(tf.vertices) // 3000)]])
    dist = np.concatenate([trimesh.proximity.signed_distance(body, pts[i:i + 400]) for i in range(0, len(pts), 400)])
    print(f"fit in body: thinnest silicone {dist.min():.1f} mm (5th percentile {np.percentile(dist, 5):.1f} mm) | skeleton size mm {np.round(tf.extents, 1)}")
    ok &= dist.min() >= 4.5
    tf.export(os.path.join(out, "skel-assembled-view.stl"))
    to_tm(ax).export(os.path.join(out, "skel-axial.stl"))
    for name, m in local.items():
        t = to_tm(m)
        t.apply_translation(-t.bounds[0])
        t.export(os.path.join(out, f"skel-{name}.stl"))
    for name, m in world.items():
        to_tm(m).export(os.path.join(out, f"view-{name}.stl"))
    print("ALL CHECKS OK" if ok else "CHECKS FAILED")
