"""
Bridge + post v2 for the version 2 mold: no pins.

The first bridge had two pins that go into holes in the mold's open face. Those holes sit only 0.75 mm from the
mold's outer side, so they do not print cleanly and the pins rest on top: the bridge floats 4 mm.
This bridge has no pins. Instead its two ends reach a little past the mold's sides and bend down as short tabs
that hug the outer side faces, so it cannot slide sideways. The post (same size and length as before) goes into
the core's socket and holds everything else.
Fits the mold halves already printed (mold-v2-left/right.stl, mold width +-43.4 mm at the post).

  python make_bridge_v2.py  ->  mold-v2-hollow/bridge-post-v2.stl  (print flat side down, post and tabs up)
Written for the Ppomo project with help from Claude.
"""
import os

import numpy as np
import trimesh
from manifold3d import Manifold

import make_mold_v1 as v1
from make_hollow_mold import mm

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "mold-v2-hollow")
POST_Y, POST_R, POST_TOP = 14.0, 5.0, 14.5       # same post as before
BRIDGE_T, BRIDGE_W = 5.0, 12.0
TAB_T, TAB_DOWN, TAB_GAP = 2.4, 7.0, 0.35         # tab thickness, how far it reaches down the side, clearance

if __name__ == "__main__":
    bt = trimesh.load(mm.BODY_STL)
    X_HALF = bt.bounds[1][0] + 6.0                # the mold's half width (as in make_mold_v2.py)
    xi = X_HALF + TAB_GAP                         # inner face of each tab
    xo = xi + TAB_T
    y0, y1 = POST_Y - BRIDGE_W / 2, POST_Y + BRIDGE_W / 2
    bridge = v1.box(-xo, xo, y0, y1, -BRIDGE_T, 0.0)
    for s in (-1, 1):
        a, b = sorted((s * xi, s * xo))
        bridge += v1.box(a, b, y0, y1, -BRIDGE_T, TAB_DOWN)
    bridge += Manifold.cylinder(POST_TOP + BRIDGE_T, POST_R, POST_R, 48).translate([0, POST_Y, -BRIDGE_T])

    # check against the mold halves and the core as they sit when assembled
    asm = trimesh.load(os.path.join(OUT, "mold-v2-assembled.stl"))
    parts = sorted(asm.split(only_watertight=False), key=lambda p: -abs(p.volume))
    others = [mm.to_manifold(p) for p in parts[:3]]          # left, right, core
    hit = sum((bridge ^ o).volume() for o in others)
    print(f"bridge overlaps mold or core by {hit:.2f} mm3 (want 0)")
    print(f"tabs hug the mold sides with {TAB_GAP} mm play, reach {TAB_DOWN} mm down; bridge length {2 * xo:.1f} mm")

    t = mm.to_trimesh(bridge)
    t.apply_translation(-t.bounds[0])             # flat outer face on the bed, post and tabs up
    path = os.path.join(OUT, "bridge-post-v2.stl")
    t = v1.save_clean(t, path)
    print(f"bridge-post-v2.stl: watertight {t.is_watertight}, bodies {len(t.split(only_watertight=False))}, {np.round(t.extents, 1)} mm, {t.volume / 1000:.1f} cm3")
