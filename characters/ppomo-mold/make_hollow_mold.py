"""
Ppomo hollow mold v1: cast the body with an air space inside, opened and closed through the face.

Idea (air-pressure sensing)
  The whole space inside the body is the air bag. Squeezing anywhere raises the air pressure, and one
  pressure sensor that is open to that space sees it. The face is the only opening:
    * a printed DUMMY (core) hangs inside the mold from the face. Silicone is poured around it.
    * after curing the dummy is pulled out through the face. The space it leaves is the air bag
      (a round head part, a neck, and a larger torso part).
    * the SKULL PLUG is pushed into the head part. Its front fills the opening and is the face.
      It has no holes: the eyes, nose and mouth are raised bumps.
    * the skull is hollow. The pressure sensor, the board and the battery sit inside it. The sensor's
      port pokes out through the skull's back cap into the neck passage, so it reads the air in the body.
      Nothing leaves the toy: no hose to the outside.

Parts written to hollow-v1/
  mold-hollow-left.stl, mold-hollow-right.stl   the two mold halves (print as exported: flat side down)
  dummy-top.stl, dummy-bottom.stl               the dummy in two halves (print flat side down, join with
                                                two bits of 1.75 mm filament as pins, glue, sand the seam)
  skull-shell-v1.stl                            the skull: face + round shell, open at the back (print standing on its open back)
  skull-cap-v1.stl                              the flat back cap with the hole for the sensor port (print flat)
  skull-face-v1.stl                             the raised eyes, nose and mouth only (for colouring / a filament swap)
  hollow-section.png                            a labelled cut through the finished toy

Needs: pip install manifold3d trimesh numpy scipy scikit-image fast-simplification pillow
Written for the Ppomo project with help from Claude.
"""
import os
import sys

import numpy as np
import trimesh
from manifold3d import CrossSection, Manifold
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "ppomo-skeleton"))
import make_mold as mm                       # noqa: E402  (block, pins, helpers)
import make_skull as sk                      # noqa: E402  (the skull shape)
import make_viewer as mv                     # noqa: E402  (meshing helpers)
from make_bone_concept import body_field     # noqa: E402

OUT = os.path.join(HERE, "hollow-v1")
h = 0.4
sk.WIN_A, sk.WIN_B, sk.WIN_E = 20.0, 11.0, 3.0          # the face opening: 40 x 22 mm, rounded rectangle
TORSO_C, TORSO_R, TORSO_E = (0.0, 14.0, 22.0), (22.0, 26.0, 13.0), 2.5   # the air space in the torso: 44 x 52 x 26 mm
NECK = ((0.0, -19.0, 20.0), (0.0, -9.0, 21.5), 8.0)     # the passage between head and torso (two ends, radius)
SKULL_BACK = -21.0                                       # the skull plug is cut flat here (it prints standing on this face)
CAP_T = 1.6                                              # thickness of the skull's back cap
PORT_R, PORT_Z = 1.5, 23.0                               # hole in the cap for the sensor's port
# what sits inside the skull (x0, x1, y0, y1, z0, z1) mm. Sizes are the usual ones for these parts; check yours.
PARTS = {
    "board": (-8.75, 8.75, -46.6, -25.6, 10.0, 13.5),         # small Bluetooth board, about 21 x 17.5 mm, lying flat
    "battery": (-10.0, 10.0, -40.6, -35.6, 15.6, 25.6),       # small LiPo cell, about 5 x 10 x 20 mm
    "sensor": (-8.9, 8.9, -29.6, -28.0, 13.7, 30.2),          # pressure sensor breakout, about 17.8 x 16.5 mm, facing backward
    "chip": (-2.5, 2.5, -28.0, -24.0, 20.5, 25.5),            # the sensor itself on that breakout
}
PORT = (-1.25, 1.25, -24.0, -16.0, PORT_Z - 1.25, PORT_Z + 1.25)   # the sensor's metal port, through the cap into the neck
BUMP = 0.9                                               # how far the eyes, nose and mouth stand out
STEM_Y0, FLANGE = -63.0, 3.0                             # the dummy's flange starts at the mold's front face (the depth stop)
HOLE_CLEAR = 0.25


def superellipse(a, b, e, n=96):
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    c, s = np.cos(t), np.sin(t)
    return np.column_stack([a * np.sign(c) * np.abs(c) ** (2 / e), b * np.sign(s) * np.abs(s) ** (2 / e)])


def prism_y(a, b, y0, y1):
    """a superellipse prism along Y from y0 to y1, centred on x = 0, z = WIN_Z."""
    m = Manifold.extrude(CrossSection([superellipse(a, b, sk.WIN_E).tolist()]), y1 - y0)
    return m.rotate([90, 0, 0]).mirror([0, 0, 1]).translate([0, y1, sk.WIN_Z]) if False else \
        m.rotate([-90, 0, 0]).mirror([0, 0, 1]).translate([0, y0, sk.WIN_Z])


def masks():
    lo = np.array([-40.0, -58.0, -2.0])
    ax = [np.arange(lo[i], hi + h, h, dtype=np.float32) for i, hi in enumerate((40.0, 58.0, 54.0))]
    X, Y, Z = np.meshgrid(*ax, indexing="ij")
    body = body_field(X, Y, Z) < 0
    D = ndimage.distance_transform_edt(body).astype(np.float32) * h
    cran = (((X / sk.RX) ** 2 + ((Y - sk.CY) / sk.RY) ** 2 + ((Z - sk.CZ) / sk.RZ) ** 2) < 1) & (D >= sk.MIN_SIL)
    grow = np.minimum(D, 6.0) / 6.0 * sk.UNDERCUT
    win = (np.abs(X) / (sk.WIN_A + grow)) ** sk.WIN_E + (np.abs(Z - sk.WIN_Z) / (sk.WIN_B + grow)) ** sk.WIN_E < 1
    boss = body & win & (Y < sk.CY)
    head = ndimage.gaussian_filter((cran | boss).astype(np.float32), 0.5 / h) > 0.5
    head &= body
    q = np.abs(np.stack([(X - TORSO_C[0]) / TORSO_R[0], (Y - TORSO_C[1]) / TORSO_R[1], (Z - TORSO_C[2]) / TORSO_R[2]], -1))
    torso = (q ** TORSO_E).sum(-1) < 1
    a, b, r = np.array(NECK[0]), np.array(NECK[1]), NECK[2]
    P = np.stack([X, Y, Z], -1)
    t = np.clip(((P - a) @ (b - a)) / ((b - a) @ (b - a)), 0, 1)
    neck = np.linalg.norm(P - (a + t[..., None] * (b - a)), axis=-1) < r
    space = ndimage.gaussian_filter((head | torso | neck).astype(np.float32), 0.5 / h) > 0.5
    space &= body
    return dict(lo=lo, X=X, Y=Y, Z=Z, body=body, D=D, head=head, boss=boss, torso=torso, neck=neck, space=space)


def skull_plug():
    """the skull at a finer grid: a hollow shell with raised features, closed at the back by a cap with one port hole."""
    g = sk.build()
    X, Y, Z, body, lo, hh = g["X"], g["Y"], g["Z"], g["body"], g["lo"], sk.h

    def surf(x, z):
        i, k = int(round((x - lo[0]) / hh)), int(round((z - lo[2]) / hh))
        return np.array([x, lo[1] + int(np.argmax(body[i, :, k])) * hh, z])

    face = np.zeros(body.shape, bool)
    for side in (-1, 1):                                             # dot eyes: low round bumps
        p = surf(side * sk.EYE_X, sk.EYE_Z)
        face |= ((X - p[0]) / sk.EYE_RX) ** 2 + ((Y - p[1]) / BUMP) ** 2 + ((Z - p[2]) / sk.EYE_RZ) ** 2 < 1
    p = surf(0.0, sk.NOSE_Z)
    face |= ((X - p[0]) / 1.7) ** 2 + ((Y - p[1]) / BUMP) ** 2 + ((Z - p[2]) / 1.25) ** 2 < 1
    for side in (-1, 1):                                             # the "w" mouth: a raised line
        for a in np.linspace(np.pi, 2 * np.pi, 40):
            q = surf(side * sk.MOUTH_ARC + sk.MOUTH_ARC * np.cos(a), sk.MOUTH_TOP + sk.MOUTH_ARC * np.sin(a))
            face |= (X - q[0]) ** 2 + ((Y - q[1]) / 1.3) ** 2 + (Z - q[2]) ** 2 < 0.7 ** 2
    outer = g["solid"] & (Y < SKULL_BACK)
    room = (ndimage.distance_transform_edt(g["solid"]) * hh >= sk.WALL) & (Y < SKULL_BACK - CAP_T)   # the space inside
    port = (X ** 2 + (Z - PORT_Z) ** 2) < PORT_R ** 2
    cap = outer & (Y >= SKULL_BACK - CAP_T) & ~port
    shell = (outer & ~room & (Y < SKULL_BACK - CAP_T)) | (face & (Y < SKULL_BACK))
    return dict(g=g, shell=shell, cap=cap, room=room, face=face & ~g["solid"])


def section_png(m, sp, path):
    """a side cut through the finished toy at x = 0."""
    SC = 14
    i0 = int(round((0 - m["lo"][0]) / h))
    body, space = m["body"][i0], m["space"][i0]
    ys, zs = m["Y"][i0, :, 0], m["Z"][i0, 0, :]
    Yc, Zc = m["Y"][i0], m["Z"][i0]
    g = sp["g"]
    j0 = int(round((0 - g["lo"][0]) / sk.h))
    arr = np.full(body.shape + (3,), 255, np.uint8)
    arr[body] = (247, 205, 214)
    arr[space] = (255, 255, 255)
    arr[space & (Yc > -8)] = (255, 244, 205)                         # foam in the torso space
    # the skull (finer grid) resampled onto this picture
    iy = np.clip(np.round((Yc - g["lo"][1]) / sk.h).astype(int), 0, g["body"].shape[1] - 1)
    iz = np.clip(np.round((Zc - g["lo"][2]) / sk.h).astype(int), 0, g["body"].shape[2] - 1)
    ok_ = (Yc <= -8.0) & (Zc >= g["lo"][2]) & (Zc <= 44.0)
    hard = (sp["shell"][j0] | sp["cap"][j0])[iy, iz] & ok_
    arr[hard] = (226, 205, 160)

    def boxc(b, col):
        arr[(Yc >= b[2]) & (Yc <= b[3]) & (Zc >= b[4]) & (Zc <= b[5])] = col

    boxc(PARTS["board"], (46, 125, 92)); boxc(PARTS["battery"], (70, 110, 200))
    boxc(PARTS["sensor"], (150, 90, 190)); boxc(PARTS["chip"], (60, 60, 66)); boxc(PORT, (170, 172, 180))
    img = Image.fromarray(np.transpose(arr, (1, 0, 2))[::-1]).resize((int(len(ys) * h * SC), int(len(zs) * h * SC)), Image.BILINEAR)
    W, Hh = img.size[0] + 80, img.size[1] + 420
    out = Image.new("RGB", (W, Hh), (255, 255, 255))
    out.paste(img, (40, 90))
    d = ImageDraw.Draw(out)
    F = lambda s_: ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", s_)
    d.text((40, 24), "완성된 뽀모를 옆에서 자른 모습 (얼굴이 왼쪽)", font=F(40), fill=(20, 20, 20))
    y = img.size[1] + 110
    for col, t in (((247, 205, 214), "실리콘 몸"), ((255, 244, 205), "공기 공간 (스펀지를 채워요): 여기가 공기주머니"),
                   ((255, 255, 255), "목 통로: 머리와 몸통의 공기를 이어요"), ((226, 205, 160), "두개골: 얼굴이자 마개이자 속 부품을 감싸는 통"),
                   ((150, 90, 190), "압력 센서 (은색 관이 두개골 뒤판을 지나 목 통로로 나와요)"), ((46, 125, 92), "블루투스 보드"), ((70, 110, 200), "배터리")):
        d.rectangle([40, y, 84, y + 32], fill=col, outline=(20, 20, 20))
        d.text((100, y - 4), t, font=F(30), fill=(40, 40, 40)); y += 42
    out.save(path)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    m = masks()
    ok = True
    D, space = m["D"], m["space"]
    # ---- the air space and the silicone left around it ----
    near_face = ndimage.binary_dilation(m["boss"], iterations=int(3.0 / h))     # the front of the skull reaches the skin on purpose
    inner = space & ~near_face
    wall = float(D[inner].min())
    vol_space = float(space.sum()) * h ** 3 / 1000
    vol_body = float(m["body"].sum()) * h ** 3 / 1000
    print(f"body {vol_body:.0f} cm3 | air space {vol_space:.0f} cm3 | silicone needed about {(vol_body - vol_space) * mm.SILICONE_DENSITY:.0f} g (a solid body took about 271 g)")
    print(f"thinnest silicone wall around the air space: {wall:.1f} mm (want >= 4):", wall >= 4.0); ok &= wall >= 4.0
    for name, part in (("torso space", m["torso"] & space), ("head space", m["head"] & space & ~near_face)):
        v = D[part]
        idx = np.argwhere(part); ext = (idx.max(0) - idx.min(0)) * h
        print(f"  {name}: {ext[0]:.0f} x {ext[1]:.0f} x {ext[2]:.0f} mm, wall {v.min():.1f} mm at its thinnest")
    lab, n = ndimage.label(space)
    print("head, neck and torso are one connected space (air reaches the hose):", n == 1); ok &= n == 1
    per = lambda a, b: np.pi * (3 * (a + b) - np.sqrt((3 * a + b) * (a + 3 * b)))
    idx = np.argwhere(m["torso"] & space); ext = (idx.max(0) - idx.min(0)) * h
    print(f"pulling the dummy out: the opening 40 x 22 mm must stretch about {per(ext[0] / 2, ext[2] / 2) / per(sk.WIN_A, sk.WIN_B):.2f}x for the torso part")

    # ---- dummy ----
    lo = m["lo"]
    core_t = mv.mc(ndimage.gaussian_filter(space.astype(np.float32), 0.6), h, lo, level=0.5)
    core = mm.to_manifold(core_t)
    stem = prism_y(sk.WIN_A, sk.WIN_B, STEM_Y0, sk.CY - 6.0)
    flange = prism_y(sk.WIN_A + 4.0, sk.WIN_B + 4.0, STEM_Y0 - FLANGE, STEM_Y0)
    dummy = core + stem + flange
    one = len(dummy.decompose()) == 1
    print("dummy (core + handle) is one piece:", one); ok &= one
    zs = 20.0
    pins = Manifold()
    for py in (-52.0, 16.0):
        pins += Manifold.cylinder(10.0, 0.95, 0.95, 24).translate([0, py, zs - 5.0])
    dummy -= pins
    big = 200
    top = dummy ^ mm.box(-big, big, -big, big, zs, big)
    bot = dummy ^ mm.box(-big, big, -big, big, -big, zs)
    tt = mm.to_trimesh(top); tt.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [0, 1, 0])); tt.apply_translation(-tt.bounds[0])
    tb = mm.to_trimesh(bot); tb.apply_translation(-tb.bounds[0])
    tt.export(os.path.join(OUT, "dummy-top.stl")); tb.export(os.path.join(OUT, "dummy-bottom.stl"))
    print("dummy halves size mm:", np.round(tt.extents, 1), np.round(tb.extents, 1))

    # ---- mold halves ----
    body_t = trimesh.load(mm.BODY_STL)
    body = mm.to_manifold(body_t)
    (x0, y0, z0), (x1, y1, z1) = body_t.bounds
    W = mm.WALL
    X0, X1, Y0, Y1, Z0, Z1 = x0 - W, x1 + W, y0 - W, y1 + W, 0.0, z1 + W
    hole = prism_y(sk.WIN_A + HOLE_CLEAR, sk.WIN_B + HOLE_CLEAR, Y0 - 1.0, sk.CY)
    block = mm.box(X0, X1, Y0, Y1, Z0, Z1) - body - hole
    front_gap = abs(STEM_Y0 - Y0)
    print(f"the dummy's flange rests on the mold's front face (gap {front_gap:.1f} mm), which sets how deep the dummy sits:", front_gap < 0.5); ok &= front_gap < 0.5
    pin_pos = [(Y0 + W / 2, Z0 + 8), (Y1 - W / 2, Z0 + 8), (Y0 + W / 2, Z1 - 6), (Y1 - W / 2, Z1 - 6)]

    def pin(y, z, r, hh):
        return Manifold.cylinder(hh, r, r, 32).rotate([0, 90, 0]).translate([0, y, z])

    left = block ^ mm.box(X0 - 1, 0, Y0 - 1, Y1 + 1, Z0 - 1, Z1 + 1)
    right = block ^ mm.box(0, X1 + 1, Y0 - 1, Y1 + 1, Z0 - 1, Z1 + 1)
    for y, z in pin_pos:
        left += pin(y, z, mm.PIN_R, mm.PIN_H)
        right -= pin(y, z, mm.PIN_R + mm.PIN_CLEAR, mm.PIN_H + 0.6)
    clash = (dummy ^ block).volume()
    print(f"the dummy fits in the closed mold without touching it: overlap {clash:.1f} mm3 (want < 5):", clash < 5.0); ok &= clash < 5.0
    tl = mm.to_trimesh(left); tl.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, [0, 1, 0])); tl.apply_translation(-tl.bounds[0])
    tr = mm.to_trimesh(right); tr.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0])); tr.apply_translation(-tr.bounds[0])
    for name, t in (("mold-hollow-left.stl", tl), ("mold-hollow-right.stl", tr)):
        t.export(os.path.join(OUT, name))
        print(name, "watertight:", t.is_watertight, "| size mm:", np.round(t.extents, 1))

    # ---- skull: hollow shell + back cap, with the sensor, board and battery inside ----
    sp = skull_plug()
    g = sp["g"]
    whole = sp["shell"] | sp["cap"]
    lab, n = ndimage.label(whole)
    sizes = ndimage.sum(whole, lab, range(1, n + 1))
    one = sizes.max() / sizes.sum() > 0.999
    print("skull (shell + cap) closes into one sealed piece; the only opening is the sensor port hole:", bool(one)); ok &= bool(one)
    idx = np.argwhere(whole); ext = (idx.max(0) - idx.min(0)) * sk.h
    print(f"skull: {ext[0]:.0f} x {ext[1]:.0f} x {ext[2]:.0f} mm, wall {sk.WALL} mm; eyes, nose and mouth stand out {BUMP} mm; no holes in the face")
    room_d = ndimage.distance_transform_edt(sp["room"]) * sk.h
    for name, b in PARTS.items():
        sl = tuple(slice(int(round((b[2 * i] - g["lo"][i]) / sk.h)), int(round((b[2 * i + 1] - g["lo"][i]) / sk.h)) + 1) for i in range(3))
        inside = bool(sp["room"][sl].all())
        print(f"  {name:7s} {b[1] - b[0]:4.1f} x {b[3] - b[2]:4.1f} x {b[5] - b[4]:4.1f} mm fits inside the skull, {float(room_d[sl].min()):.1f} mm from the wall at its tightest corner:", inside)
        ok &= inside
    names = list(PARTS)
    for i, a_ in enumerate(names):
        for b_ in names[i + 1:]:
            A, B = PARTS[a_], PARTS[b_]
            hit = all(A[k] < B[k + 1] and B[k] < A[k + 1] for k in (0, 2, 4)) and {a_, b_} != {"sensor", "chip"}
            if hit:
                print(f"  !! {a_} overlaps {b_}")
            ok &= not hit
    tip = PORT[3] - SKULL_BACK
    print(f"the sensor port reaches {tip:.1f} mm past the skull's back cap into the neck passage, so it reads the air in the body:", tip > 2.0); ok &= tip > 2.0

    def export(mask, name, sigma=0.6, level=0.5, target=250000, stand=False):
        t = mv.slim(mv.mc(ndimage.gaussian_filter(mask.astype(np.float32), sigma), sk.h, g["lo"], level=level), target)
        if stand:
            t.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0])); t.apply_translation(-t.bounds[0])
        t.export(os.path.join(OUT, name))

    export(sp["shell"], "skull-shell-v1.stl", stand=True)
    export(sp["cap"], "skull-cap-v1.stl", sigma=0.4, target=20000, stand=True)
    export(sp["face"], "skull-face-v1.stl", sigma=0.5, level=0.4, target=20000)
    for old in ("skull-plug-v0.stl", "skull-plug-v0-face.stl"):
        if os.path.exists(os.path.join(OUT, old)):
            os.remove(os.path.join(OUT, old))
    section_png(m, sp, os.path.join(OUT, "hollow-section.png"))
    print("ALL CHECKS OK" if ok else "CHECK FAILED")
