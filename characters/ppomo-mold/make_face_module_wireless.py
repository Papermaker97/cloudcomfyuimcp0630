"""
Ppomo face module, WIRELESS version for the first cast (124 mm core).

The face module is a plug: it pushes into the 40 x 22 mm face tunnel and the soft silicone hugs it all round,
which is what seals Ppomo's body. Everything sits inside the plug, so there is no hole anywhere in the face.
To charge, pull the whole plug out, plug a USB-C cable into its back, push it back in.

  * SHELL: Ppomo's face on the front (eyes, nose, mouth stand out 0.9 mm), 0.5 mm bigger than the tunnel on every
    side. Behind the tunnel the body's head pocket opens up; there a soft RIDGE (0.7 mm, tapered both ways) on the
    shell catches the tunnel's inner edge, so squeezing Ppomo cannot push the face out. No wire hole.
  * SLED (the back cap with rails): the Seeed XIAO nRF52840 lies on two rails, its USB-C socket in an opening in
    the cap. A stop in front keeps the board from sliding in when you push a cable in. The battery lies on top of
    the XIAO (tape), the MPRLS sensor stands against the inside of the face, port pointing back.
    The back of the plug is inside Ppomo's air, so the openings in the cap just let that air reach the sensor.

Measured against the cast: the tunnel runs from the face (y = -54) to about y = -41, the head pocket behind it
to about y = -16; the module ends at y = -16.3 (its back lip 1 mm smaller, as the pocket narrows there).
Parts: XIAO nRF52840 21 x 17.8 x 4.4 mm (with the socket); MPRLS 17.8 x 16.7 x 7.5 mm (with the port);
battery up to 30 x 17 x 6 mm.

  python make_face_module_wireless.py  ->  face-module-wireless/face-shell.stl, face-sled.stl, preview
Print: face-shell standing on its open back (face up); face-sled on the cap's outer face (rails up).
PLA or PETG, 0.2 mm, no supports, 4 walls (the shell is the air seal).
Written for the Ppomo project with help from Claude.
"""
import os

import numpy as np
import trimesh
from manifold3d import CrossSection, Manifold
from scipy import ndimage

import make_hollow_mold as hm
import make_mold_v1 as v1
from make_hollow_mold import mm, mv, sk, prism_y, superellipse

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "face-module-wireless")
SEAL = 0.5                       # bigger than the tunnel on each side
WALL, FRONT = 2.2, 2.4
Y_BACK = -17.5                   # back end of the shell
CAP_T, LIP_T, CAP_GAP = 2.0, 1.2, 0.25
RIDGE = (-40.0, -35.0, 0.7)      # y from, y to, how much it stands out (peak in the middle)
CLEAR = 0.3                      # sled to shell
# parts, (x0, x1, y0, y1, z0, z1) in the body frame (z = 17.5 is the tunnel's centre line)
RAIL_TOP = 10.0
XIAO = (-8.9, 8.9, Y_BACK - CAP_T - 21.0, Y_BACK - CAP_T, RAIL_TOP, RAIL_TOP + 1.2)   # the board itself
XIAO_TALL = (-8.9, 8.9, XIAO[2], XIAO[3], RAIL_TOP, RAIL_TOP + 4.4)                 # with the shield and socket
USB = (-4.5, 4.5, XIAO[3] - 7.4, XIAO[3] + 1.0, RAIL_TOP + 1.2, RAIL_TOP + 4.4)      # socket sticks out ~1 mm
BATTERY = (-15.0, 15.0, -38.5, -21.5, RAIL_TOP + 4.8, RAIL_TOP + 10.8)              # 30 x 17 x 6 (the biggest allowed)
SENSOR = (-8.9, 8.9, -54.1 + FRONT + 0.3, -54.1 + FRONT + 0.3 + 7.5, sk.WIN_Z - 8.35, sk.WIN_Z + 8.35)


def box(b):
    return v1.box(*b)


def ridge(a, b):
    """a band round the shell that rises to +RIDGE[2] in the middle and back down (tapered both ways)."""
    y0, y1, up = RIDGE
    mid = (y0 + y1) / 2
    cs = CrossSection([superellipse(a, b, sk.WIN_E).tolist()])
    s = 1 + up / a
    half = Manifold.extrude(cs, (y1 - y0) / 2, 8, 0.0, [s, (b + up) / b])            # grows from base to peak
    half = half.rotate([-90, 0, 0]).mirror([0, 0, 1])                                # along +y, mirror as prism_y
    rise = half.translate([0, y0, sk.WIN_Z])
    fall = half.mirror([0, 1, 0]).translate([0, y1, sk.WIN_Z])
    return rise + fall


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    body = mm.to_manifold(trimesh.load(mm.BODY_STL))
    A, B = sk.WIN_A + SEAL, sk.WIN_B + SEAL
    ai, bi = A - WALL, B - WALL
    outer = (prism_y(A, B, -75.0, Y_BACK) ^ body) + (ridge(A, B) ^ prism_y(A + 2, B + 2, RIDGE[0], RIDGE[1]))
    inner = prism_y(ai, bi, -75.0, Y_BACK + 5.0) ^ body.translate([0, FRONT, 0])
    shell = outer - inner

    sp = hm.skull_plug()
    bumps = mm.to_manifold(mv.mc(ndimage.gaussian_filter(sp["face"].astype(np.float32), 0.5), sk.h, sp["g"]["lo"], level=0.4))
    shell = shell + bumps

    # ---- sled: cap + lip + rails + front stop ----
    room = prism_y(ai - CLEAR, bi - CLEAR, -60.0, Y_BACK)                             # where the sled may be
    plate = prism_y(ai - CAP_GAP, bi - CAP_GAP, Y_BACK - CAP_T, Y_BACK)
    lip = prism_y(A - 1.0, B - 1.0, Y_BACK, Y_BACK + LIP_T)                         # 1 mm smaller: the pocket narrows here
    rails = Manifold()
    for s in (-1, 1):
        x0, x1 = sorted((s * 6.4, s * 12.0))
        rails += box((x0, x1, XIAO[2] - 1.0, Y_BACK - CAP_T + 0.1, 0.0, RAIL_TOP))     # under the board's edges
        x0, x1 = sorted((s * 9.25, s * 12.0))
        rails += box((x0, x1, XIAO[2] - 1.0, Y_BACK - CAP_T + 0.1, 0.0, RAIL_TOP + 1.6))   # side lips
    stop = box((-8.0, 8.0, XIAO[2] - 1.0, XIAO[2] - 0.15, 0.0, RAIL_TOP + 1.6))      # board cannot slide in
    sled = plate + lip + ((rails + stop) ^ room)
    # openings in the cap: the USB-C plug (12.5 x 7 mm, room for the cable's moulded end) and 3 air holes
    plug = box((-6.25, 6.25, Y_BACK - CAP_T - 1, Y_BACK + LIP_T + 1, USB[4] + 1.6 - 3.5, USB[4] + 1.6 + 3.5))
    sled = sled - plug
    for x in (-9.0, 0.0, 9.0):
        sled -= Manifold.cylinder(10.0, 1.6, 1.6, 24).rotate([-90, 0, 0]).translate([x, Y_BACK - CAP_T - 2, sk.WIN_Z + 5.5])

    # the inside of the face is curved, so the sensor's corners need it a little further back than the centre
    for d in np.arange(0.0, 4.01, 0.25):
        b = (SENSOR[0], SENSOR[1], SENSOR[2] + d, SENSOR[3] + d, SENSOR[4], SENSOR[5])
        if (box(b) ^ shell).volume() < 0.3:
            break
    SENSOR = b
    print(f"sensor sits {d:.2f} mm behind the centre of the face's inside")

    # ---- checks ----
    ok = True

    def check(name, v, want):
        global ok
        good = v <= want
        ok &= good
        print(f"  {name}: {v:.2f} mm3 (want <= {want})", "OK" if good else "FAIL")

    print("shell one piece:", len(shell.decompose()) == 1, "| sled one piece:", len(sled.decompose()) == 1)
    check("sled vs shell", (sled ^ shell).volume(), 0.5)
    for name, b in (("XIAO", XIAO_TALL), ("battery 30x17x6", BATTERY), ("MPRLS", SENSOR)):
        part = box(b)
        check(f"{name} vs shell", (part ^ shell).volume(), 0.5)
        check(f"{name} vs sled", (part ^ (sled - box(USB))).volume() if name != "XIAO" else (box(XIAO) ^ sled).volume(), 0.5)
    print(f"  XIAO sits on rails: {(box((-8.9, 8.9, XIAO[2], XIAO[3], RAIL_TOP - 0.2, RAIL_TOP)) ^ sled).volume():.0f} mm3 of rail under it")
    check("MPRLS vs XIAO", (box(SENSOR) ^ box(XIAO_TALL)).volume(), 0.0)
    check("battery vs XIAO", (box(BATTERY) ^ box(XIAO_TALL)).volume(), 0.0)
    print(f"  air gap from the sensor's port to the XIAO's stop: {XIAO[2] - 1.0 - SENSOR[3]:.1f} mm")

    # ---- export ----
    ts = mm.to_trimesh(shell)
    ts.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0]))   # face up, open back on the bed
    tc = mm.to_trimesh(sled)
    tc.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0]))    # cap (back end) down, rails up
    for name, t in (("face-shell.stl", ts), ("face-sled.stl", tc)):
        t = v1.save_clean(t, os.path.join(OUT, name))
        print(f"{name}: watertight {t.is_watertight}, bodies {len(t.split(only_watertight=False))}, {np.round(t.extents, 1)} mm, {t.volume / 1000:.1f} cm3 (~{t.volume / 1000 * 1.24:.0f} g)")
    parts = {"xiao": box(XIAO_TALL), "battery": box(BATTERY), "sensor": box(SENSOR)}
    for k, v in parts.items():
        mm.to_trimesh(v).export(os.path.join(OUT, f"_part-{k}.stl"))
    mm.to_trimesh(shell).export(os.path.join(OUT, "_shell-body-frame.stl"))
    mm.to_trimesh(sled).export(os.path.join(OUT, "_sled-body-frame.stl"))

    # does the module stay inside the cast's cavity? (the 124 mm core sat 8 mm further back)
    # checked slice by slice on the module's outline, which keeps memory low
    del sp
    m = hm.masks()
    X, Z, yy = m["X"][:, 0, 0][:, None], m["Z"][0, 0, :][None, :], m["Y"][0, :, 0]
    sh = int(round(8 / hm.h))
    cav = np.zeros_like(m["space"])
    cav[:, sh:, :] = m["space"][:, :-sh, :]
    tun = (np.abs(X) / sk.WIN_A) ** sk.WIN_E + (np.abs(Z - sk.WIN_Z) / sk.WIN_B) ** sk.WIN_E < 1
    neck = np.zeros_like(m["neck"])
    neck[:, sh:, :] = m["neck"][:, :-sh, :]
    worst = {"tunnel": 0.0, "pocket": 0.0}
    blocks_neck = 0
    for j, y in enumerate(yy):
        if y < -51.0 or y > Y_BACK + LIP_T:                      # the face itself is the front 3 mm
            continue
        a, b = (A, B) if y <= Y_BACK else (A - 1.0, B - 1.0)
        if RIDGE[0] <= y <= RIDGE[1]:
            t = 1 - abs(y - (RIDGE[0] + RIDGE[1]) / 2) / ((RIDGE[1] - RIDGE[0]) / 2)
            a, b = a + RIDGE[2] * t, b + RIDGE[2] * t
        mod = (np.abs(X) / a) ** sk.WIN_E + (np.abs(Z - sk.WIN_Z) / b) ** sk.WIN_E < 1
        c = cav[:, j, :] | (tun & (y < sk.CY + 2) & m["body"][:, j, :])
        out = mod & ~c
        if out.any():
            d = float((ndimage.distance_transform_edt(~c) * hm.h)[out].max())
            key = "tunnel" if y < -41 else "pocket"
            worst[key] = max(worst[key], d)
        blocks_neck += int((mod & neck[:, j, :] & ~cav[:, j, :]).sum())
    print(f"  presses into the silicone: tunnel {worst['tunnel']:.1f} mm (the seal), head pocket {worst['pocket']:.1f} mm (ridge)")
    print(f"  module in the neck passage: {blocks_neck * hm.h ** 2:.0f} mm2 (want 0)")
    print("ALL CHECKS OK" if ok else "CHECK FAILED")
