"""
Ppomo casting mold, VERSION 2: a hollow body for the final product.

Inside the silicone body: a pocket in the head (the face module goes in here, through the 40 x 22 mm face
opening), a short neck passage, and a pocket in the torso (the air bag goes in here). The pockets are made by
a printed CORE that sits inside the mold while the silicone is poured.

The core is held at BOTH ends, so it cannot sag or float (the idea from the concrete-candle mold example):
  * front: a handle runs out through the face opening and a hole in the mold; its flange rests on the mold's
    front face, which sets how deep the core sits.
  * bottom: a BRIDGE lies across the mold's open bottom (the pour side) and a POST goes up from it through the
    belly into a socket in the core. Two pins keep the bridge from sliding. The post leaves a 10 mm hole in
    the belly; the air bag is sealed on its own, so the body does not need to be airtight (the cover hides it).

Unmolding: undo the bolts, open the halves, pull the bridge + post straight out of the belly, then pull the
core out through the face opening (the opening stretches about 1.1x; Ecoflex stretches many times that).

Writes mold-v2-hollow/:
  mold-v2-left.stl, mold-v2-right.stl     mold halves (print lying on the outer side, cavity up)
  core-top.stl, core-bottom.stl            the core in two halves (print flat side down); join with two
                                           bits of 1.75 mm filament in the pin holes, glue, sand the seam
  bridge-post.stl                          the bridge with its post and pins (print flat, post up)
  mold-v2-assembled.stl                    everything in place, for checking
Seam (tongue and groove) and the 4 M4 bolt flanges are the same as version 1.
Needs: pip install manifold3d trimesh numpy scipy scikit-image fast-simplification
Written for the Ppomo project with help from Claude.
"""
import os

import numpy as np
import trimesh
from manifold3d import Manifold
from scipy import ndimage

import make_hollow_mold as hm
import make_mold_v1 as v1
from make_hollow_mold import h, mm, mv, sk, prism_y

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "mold-v2-hollow")
WALL, FLANGE = v1.WALL, v1.FLANGE
POST_Y, POST_R, SOCKET_CLEAR = 14.0, 5.0, 0.25     # the post goes up into the torso core here
BRIDGE_T, BRIDGE_W = 5.0, 12.0                     # bridge thickness and width
BPIN_R, BPIN_H, BPIN_CLEAR = 2.0, 4.0, 0.25
CORE_SPLIT_Z = 20.0                                # the core is printed in two halves split here


def export(m, name, flip=False):
    t = mm.to_trimesh(m)
    if flip:
        t.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [0, 1, 0]))
    t.apply_translation(-t.bounds[0])
    t.export(os.path.join(OUT, name))
    print(f"  {name}: watertight {t.is_watertight}, {np.round(t.extents, 1)} mm, {t.volume / 1000:.0f} cm3")
    return t


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    ok = True
    m = hm.masks()
    lo, space, D = m["lo"], m["space"], m["D"]

    # ---- mold block (same outside as version 1) ----
    bt = trimesh.load(mm.BODY_STL)
    body = mm.to_manifold(bt)
    (bx0, by0, bz0), (bx1, by1, bz1) = bt.bounds
    X0, X1, Y0, Y1, Z0, Z1 = bx0 - WALL, bx1 + WALL, by0 - WALL, by1 + WALL, 0.0, bz1 + WALL
    YF = Y0 - FLANGE                                       # the mold's front face
    floor = Manifold.extrude(body.slice(0.4), 3.0).translate([0, 0, -2.6])
    hole = prism_y(sk.WIN_A + hm.HOLE_CLEAR, sk.WIN_B + hm.HOLE_CLEAR, YF - 1.0, sk.CY)
    block = v1.box(X0, X1, YF, Y1 + FLANGE, Z0, Z1) - (body + floor) - hole

    # ---- core: the pockets, a handle out through the face, a socket for the post ----
    core = mm.to_manifold(mv.mc(ndimage.gaussian_filter(space.astype(np.float32), 0.6), h, lo, level=0.5))
    stem = prism_y(sk.WIN_A, sk.WIN_B, YF, sk.CY - 6.0)
    flange = prism_y(sk.WIN_A + 4.0, sk.WIN_B + 4.0, YF - 3.0, YF)
    core = core + stem + flange
    socket = Manifold.cylinder(9.0, POST_R + SOCKET_CLEAR, POST_R + SOCKET_CLEAR, 48).translate([0, POST_Y, 6.0])
    core = core - socket
    print("core is one piece:", len(core.decompose()) == 1); ok &= len(core.decompose()) == 1
    clash = (core ^ block).volume()
    print(f"core does not touch the mold: overlap {clash:.1f} mm3 (want < 5):", clash < 5); ok &= clash < 5

    # ---- bridge + post ----
    post_top = 14.5
    bridge = v1.box(X0 + 4, X1 - 4, POST_Y - BRIDGE_W / 2, POST_Y + BRIDGE_W / 2, -BRIDGE_T, 0.0)
    post = Manifold.cylinder(post_top + BRIDGE_T, POST_R, POST_R, 48).translate([0, POST_Y, -BRIDGE_T])
    bpins = [(sx * (X1 - 9.0), POST_Y) for sx in (-1, 1)]
    bp = bridge + post
    for px, py in bpins:
        bp += Manifold.cylinder(BPIN_H + BRIDGE_T, BPIN_R, BPIN_R, 32).translate([px, py, -BRIDGE_T])
        block -= Manifold.cylinder(BPIN_H + 0.6, BPIN_R + BPIN_CLEAR, BPIN_R + BPIN_CLEAR, 32).translate([px, py, -0.1])
    inside_socket = post_top - 6.0
    print(f"the post reaches {inside_socket:.1f} mm into the core's socket")
    clash2 = (bp ^ (block + core)).volume()
    print(f"bridge + post does not hit the mold or core except where meant: overlap {clash2:.1f} mm3 (want < 5):", clash2 < 5); ok &= clash2 < 5
    ring = bp ^ v1.box(-200, 200, -200, 200, 0.0, 200)
    print(f"post passes through the belly: {POST_R * 2:.0f} mm hole in the silicone floor")

    # ---- mold halves, seam and bolts as in version 1 (the face hole is kept clear of the tongue) ----
    left = block ^ v1.box(X0 - 1, 0, YF - 1, Y1 + FLANGE + 1, -1, Z1 + 1)
    right = block ^ v1.box(0, X1 + 1, YF - 1, Y1 + FLANGE + 1, -1, Z1 + 1)
    section = body.rotate([0, 90, 0]).slice(0.0)
    tongue = v1.ring_in_x(section, v1.TONGUE[0], v1.TONGUE[1], 0.0, v1.TONGUE[2], Z1) - hole
    groove = v1.ring_in_x(section, v1.TONGUE[0] - v1.GAP, v1.TONGUE[1] + v1.GAP, 0.0, v1.TONGUE[2] + 0.4, Z1)
    left = left + tongue
    right = right - groove
    for yy, zz in [(yy, zz) for yy in (YF + FLANGE / 2, Y1 + FLANGE / 2) for zz in (Z0 + 12.0, Z1 - 10.0)]:
        hb = Manifold.cylinder(X1 - X0 + 4, v1.BOLT_R, v1.BOLT_R, 32).rotate([0, 90, 0]).translate([X0 - 2, yy, zz])
        pl = Manifold.cylinder(-v1.KEEP - X0 + 1, v1.NUT_R, v1.NUT_R, 6).rotate([0, 90, 0]).translate([X0 - 1, yy, zz])
        pr = Manifold.cylinder(X1 - v1.KEEP + 1, v1.NUT_R, v1.NUT_R, 6).rotate([0, 90, 0]).translate([v1.KEEP, yy, zz])
        left, right = left - hb - pl, right - hb - pr
    print(f"left/right overlap {(left ^ right).volume():.2f} mm3; core vs tongue {(core ^ tongue).volume():.2f} mm3")

    # ---- numbers ----
    vol_body = float(m["body"].sum()) * h ** 3 / 1000
    vol_space = float(space.sum()) * h ** 3 / 1000
    print(f"silicone per cast about {(vol_body - vol_space) * 1.07:.0f} g (solid version 1: about 271 g)")
    near_face = ndimage.binary_dilation(m["boss"], iterations=int(3.0 / h))
    print(f"thinnest silicone wall around the pockets: {float(D[space & ~near_face].min()):.1f} mm")
    per = lambda a, b: np.pi * (3 * (a + b) - np.sqrt((3 * a + b) * (a + 3 * b)))
    idx = np.argwhere(m["torso"] & space); ext = (idx.max(0) - idx.min(0)) * h
    print(f"pulling the core out: the face opening stretches about {per(ext[0] / 2, ext[2] / 2) / per(sk.WIN_A, sk.WIN_B):.2f}x")

    # ---- export ----
    print("files:")
    trimesh.util.concatenate([mm.to_trimesh(x) for x in (left, right, core, bp)]).export(os.path.join(OUT, "mold-v2-assembled.stl"))
    tl = mm.to_trimesh(left); tl.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, [0, 1, 0])); tl.apply_translation(-tl.bounds[0])
    tr = mm.to_trimesh(right); tr.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0])); tr.apply_translation(-tr.bounds[0])
    for name, t in (("mold-v2-left.stl", tl), ("mold-v2-right.stl", tr)):
        t.export(os.path.join(OUT, name)); print(f"  {name}: watertight {t.is_watertight}, {np.round(t.extents, 1)} mm, {t.volume / 1000:.0f} cm3")
    pins = Manifold()
    for py in (-52.0, 16.0 + 8.0):
        pins += Manifold.cylinder(10.0, 0.95, 0.95, 24).translate([0, py, CORE_SPLIT_Z - 5.0])
    cpin = core - pins
    big = 300
    export(cpin ^ v1.box(-big, big, -big, big, CORE_SPLIT_Z, big), "core-top.stl")            # flat cut face is already at the bottom
    export(cpin ^ v1.box(-big, big, -big, big, -big, CORE_SPLIT_Z), "core-bottom.stl", flip=True)   # turned over: flat cut face down
    export(bp, "bridge-post.stl")
    print("ALL CHECKS OK" if ok else "CHECK FAILED")
