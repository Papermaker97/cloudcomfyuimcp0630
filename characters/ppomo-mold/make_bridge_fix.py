"""
Bridge + post that fit the PRINTED version 2 mold (mold-v2-left/right.stl, v2.1: pin holes at x = +-40.4 mm,
y = 14 mm, on the open face). The bridge first printed came from an earlier file whose pins sit at +-38.4 mm,
2 mm inside the holes, so it could not sit down.

Two files, pick the one for the core you printed (measure the core's length, handle included):
  bridge-post-for-116mm-core.stl   core 116 mm long (later files): post at y = 14, in line with the pins
  bridge-post-for-124mm-core.stl   core 124 mm long (first files): that core's handle is 8 mm longer, so in this
                                   mold the core sits 8 mm further back and its socket is at y = 22
The plate now runs out over the pins so they are fully attached (in the old file they hung half off the end).
Print flat side down, post and pins up.  Written for the Ppomo project with help from Claude.
"""
import os

import numpy as np
import trimesh
from manifold3d import Manifold

import make_mold_v1 as v1
from make_hollow_mold import mm

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "mold-v2-hollow")
X_HALF = trimesh.load(mm.BODY_STL).bounds[1][0] + 6.0
PIN_X, PIN_Y, PIN_R, PIN_H = X_HALF - 3.0, 14.0, 2.0, 4.0
POST_R, POST_TOP, T = 5.0, 14.5, 5.0


def bridge(post_y):
    y0, y1 = min(PIN_Y, post_y) - 6.0, max(PIN_Y, post_y) + 6.0
    m = v1.box(-(X_HALF - 0.5), X_HALF - 0.5, y0, y1, -T, 0.0)
    m += Manifold.cylinder(POST_TOP + T, POST_R, POST_R, 48).translate([0, post_y, -T])
    for s in (-1, 1):
        m += Manifold.cylinder(PIN_H + T, PIN_R, PIN_R, 32).translate([s * PIN_X, PIN_Y, -T])
    return m


if __name__ == "__main__":
    asm = sorted(trimesh.load(os.path.join(OUT, "mold-v2-assembled.stl")).split(only_watertight=False), key=lambda p: -abs(p.volume))
    L, R = mm.to_manifold(asm[0]), mm.to_manifold(asm[1])
    for name, post_y in (("bridge-post-for-116mm-core.stl", 14.0), ("bridge-post-for-124mm-core.stl", 22.0)):
        b = bridge(post_y)
        hit = (b ^ L).volume() + (b ^ R).volume()
        t = mm.to_trimesh(b); t.apply_translation(-t.bounds[0])
        t = v1.save_clean(t, os.path.join(OUT, name))
        print(f"{name}: hits the printed mold by {hit:.2f} mm3 (pins in holes), watertight {t.is_watertight}, "
              f"bodies {len(t.split(only_watertight=False))}, {np.round(t.extents, 1)} mm")
