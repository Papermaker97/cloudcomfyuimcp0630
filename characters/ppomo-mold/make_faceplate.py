"""
Ppomo face plate: the eyes / nose / mouth are one hard ivory OVAL that plugs the opening in the face.

Idea (from the project owner): the body must be squeezable everywhere, so it cannot have a plug.
The face is never squeezed, so the opening goes there. The inner parts slide in through the face,
and the plug that closes the opening IS the face (eyes, nose, mouth). Cheeks and ears stay silicone.

What this script makes (design step: the inner cavity is only a placeholder, the clicker is not in yet)
  ppomo-faceplate.stl         the hard plate. Print in ivory PLA/PETG, standing on its flat back, no supports.
                              front = the face surface with carved eyes, nose, mouth (fill them with dark paint)
                              middle = a 45-degree taper the silicone lip sits on
                              back  = a wider flange that sits behind the lip so the plate cannot pop out
                              a 1.6 mm vent through the nose lets air out when the body is squeezed
  ppomo-body-face-opening.stl the body with the oval seat, the opening and a placeholder cavity (for looking)
  ppomo-faceplate-ink.stl     the carved eyes/nose/mouth as solids (only used to colour the renders)

Needs: pip install manifold3d trimesh numpy rtree
Written for the Ppomo project with help from Claude.
"""
import os

import numpy as np
import trimesh
from manifold3d import CrossSection, Manifold

import make_face as mf

HERE = os.path.dirname(os.path.abspath(__file__))
A, B = 17.0, 10.0            # oval half-width, half-height of the visible plate (34 x 20 mm)
ZC = 17.5                    # oval centre height (between the eyes and the mouth)
SKIN = 2.0                   # thickness of the visible part (sits in a seat, flush with the face)
LIP = 3.0                    # silicone lip thickness = length of the taper
NECK_IN = 3.0                # the opening is this much smaller than the plate all round (28 x 14 mm)
FLANGE_T, FLANGE_OUT = 1.6, 1.5
VENT_R = 0.8
CLEAR = 0.15                 # the silicone seat is this much bigger than the plate
CAV_R, CAV_LEN = 14.0, 40.0  # placeholder cavity behind the face (radius, straight length)
CAV_START = 20.0             # the cavity widens from the opening to full size over this distance


def oval_slab(a, b, y0, y1, zc=ZC):
    """an oval plate lying across the Y axis: thickness from y0 to y1, centred at x = 0, z = zc."""
    m = Manifold.extrude(CrossSection.circle(1.0, 96).scale([a, b]), y1 - y0)
    return m.rotate([90, 0, 0]).translate([0, y1, zc])


def build():
    t = trimesh.load(mf.SRC)                         # the body without a face
    body = mf.to_manifold(t)
    cut, _ = mf.build_face(t)                        # the carved eyes / nose / mouth
    # deepest point of the face surface inside the oval: everything behind it is flat slabs
    ys = []
    for ang in np.linspace(0, 2 * np.pi, 48, endpoint=False):
        for k in (0.5, 1.0):
            ys.append(mf.surface(t, k * A * np.cos(ang), ZC + k * B * np.sin(ang))[0][1])
    y_front = min(ys + [mf.surface(t, 0, ZC)[0][1]])
    y0 = max(ys)                                     # deepest surface point on the oval
    y_skin, y_neck, y_fl = y0 + SKIN, y0 + SKIN + LIP, y0 + SKIN + LIP + FLANGE_T
    prism = oval_slab(A, B, y_front - 5, y_skin)
    skin = (body ^ prism) - cut                      # visible part: the real face surface, carved
    taper = Manifold.batch_hull([oval_slab(A, B, y_skin - 0.01, y_skin), oval_slab(A - NECK_IN, B - NECK_IN, y_neck - 0.01, y_neck)])
    flange = oval_slab(A - NECK_IN + FLANGE_OUT, B - NECK_IN + FLANGE_OUT, y_neck, y_fl)
    nose = mf.surface(t, 0.0, (mf.EYE_Y - mf.Y_FLOOR) * mf.S - mf.NOSE_DROP)[0]
    vent = Manifold.cylinder(40, VENT_R, VENT_R, 24).rotate([-90, 0, 0]).translate([0, nose[1] - 5, nose[2]])
    plate = skin + taper + flange - vent
    ink = (body ^ prism) ^ cut                       # what was carved away, for colouring
    # the silicone body: seat for the plate, tapered opening, placeholder cavity
    seat = oval_slab(A + CLEAR, B + CLEAR, y_front - 5, y_skin)
    hole = Manifold.batch_hull([oval_slab(A + CLEAR, B + CLEAR, y_skin - 0.01, y_skin),
                                oval_slab(A - NECK_IN + CLEAR, B - NECK_IN + CLEAR, y_neck - 0.01, y_neck + 0.01)])
    fa, fb = A - NECK_IN + FLANGE_OUT + CLEAR, B - NECK_IN + FLANGE_OUT + CLEAR
    pocket = oval_slab(fa, fb, y_neck, y_fl + 0.5)            # room for the plate's back flange
    zc2 = ZC + 3.0
    ball0 = Manifold.sphere(CAV_R, 64).translate([0, y_neck + CAV_START, zc2])
    ball1 = Manifold.sphere(CAV_R, 64).translate([0, y_neck + CAV_START + CAV_LEN, zc2])
    cav = Manifold.batch_hull([pocket, ball0]) + Manifold.batch_hull([ball0, ball1])
    silicone = body - seat - hole - cav
    info = dict(y_front=y_front, y0=y0, y_fl=y_fl)
    return plate, ink, silicone, body, cav, info


if __name__ == "__main__":
    plate, ink, silicone, body, cav, info = build()
    ok = True
    one = len(plate.decompose()) == 1 and len(silicone.decompose()) == 1
    print("plate is one piece, body is one piece:", one); ok &= one
    v = (plate ^ silicone).volume()
    print("plate and silicone do not overlap:", v < 0.5, f"({v:.2f} mm3)"); ok &= v < 0.5
    # the flange is wider than the opening, so the plate cannot be pushed out through the face
    open_a, open_b = A - NECK_IN, B - NECK_IN
    fl_a, fl_b = open_a + FLANGE_OUT, open_b + FLANGE_OUT
    print(f"visible plate {2 * A:.0f} x {2 * B:.0f} mm | opening {2 * open_a:.0f} x {2 * open_b:.0f} mm | back flange {2 * fl_a:.0f} x {2 * fl_b:.0f} mm (wider than the opening: {fl_a > open_a})")
    # thinnest silicone around the placeholder cavity
    tb = mf.to_trimesh(body)
    tc = mf.to_trimesh(cav)
    pts = tc.vertices[::7]
    d = []
    for i in range(0, len(pts), 400):
        d.extend(trimesh.proximity.signed_distance(tb, pts[i:i + 400]))
    wall = float(np.min(d))
    print(f"placeholder cavity: thinnest silicone wall {wall:.1f} mm (want >= 4):", wall >= 4.0); ok &= wall >= 4.0
    size = np.round(mf.to_trimesh(plate).extents, 1)
    print("plate size mm (x, depth, z):", size, "| depth behind the face surface:", round(info["y_fl"] - info["y_front"], 1), "mm")
    # export: the plate standing on its flat back (flange on the bed, face up)
    tp = mf.to_trimesh(plate)
    tp.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0]))
    tp.apply_translation(-tp.bounds[0])
    tp.export(os.path.join(HERE, "ppomo-faceplate.stl"))
    mf.to_trimesh(silicone).export(os.path.join(HERE, "ppomo-body-face-opening.stl"))
    # world-position copies for the renders (scratch files, not kept in the repo)
    view = os.path.join(HERE, "faceplate-view")
    os.makedirs(view, exist_ok=True)
    mf.to_trimesh(plate).export(os.path.join(view, "plate.stl"))
    mf.to_trimesh(ink).export(os.path.join(view, "ink.stl"))
    mf.to_trimesh(silicone).export(os.path.join(view, "silicone.stl"))
    print("ALL CHECKS OK" if ok else "CHECKS FAILED")
