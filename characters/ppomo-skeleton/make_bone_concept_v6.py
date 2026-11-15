"""
Ppomo skeleton concept v6: a spine of identical printed vertebrae, each one a whole squeeze-button.

Problems in v5 and how v6 answers them
  could not be printed            -> every moving part is one flat print-in-place vertebra (make_vertebra.py)
  a slanted squeeze pushes a bone aside -> each cap rides on a stem held by two lips
  the button was the end stop     -> the lips stop the cap 0.25 mm after the click
  five straight directions only   -> a vertebra works across its whole diameter (cap side AND back side) and
                                     its cap covers about 156 degrees. Two ring vertebrae at right angles
                                     (belly/back and left/right) leave no direction round the body more than
                                     45 degrees from an axis. A third one stands upright at the rear with its
                                     cap facing backward: the tail.
  one squeeze counted many times  -> the three buttons are wired in parallel; the sketch should count presses
                                     that arrive within about 0.3 s as one squeeze (software, not built here)

Parts
  SKULL     face + plug + braincase (board, battery), as in v5
  VERTEBRA  x 3, all the same print (2 rings + the tail)
  DISC      thin round plates between the vertebrae: they join the stack and close the open faces
  3 tactile buttons, 2 slack wires and a pull cord to the skull

  python make_bone_concept_v6.py   -> bone-concept/v6/*, checks, vertebra diagram, ppomo-skeleton-viewer.html
Needs: pip install numpy scipy trimesh scikit-image fast-simplification manifold3d rtree pillow
Written for the Ppomo project with help from Claude.
"""
import json
import os
import sys

import numpy as np
import trimesh
from manifold3d import Manifold
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

import make_bone_concept_v3 as v3
import make_bone_concept_v5 as v5
import make_head_layout as lay
import make_vertebra as vb
import make_viewer as mv
from make_bone_concept import H, body_field

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "bone-concept", "v6")
AX_Z = 21.5                    # height of the spine axis in the body
Y_FRONT = -9.0                # front face of the first vertebra
DISC_T = 0.8
# cap direction of each ring vertebra, seen from the front: 0 = right, 90 = up, 270 = down (belly).
# Two rings at right angles: belly/back and left/right. A third ring does not fit: the body is too short
# for it once the upright tail vertebra is behind the stack.
ANGLES = {"belly": 270.0, "side": 0.0}


def placements():
    out = {}
    y = Y_FRONT
    for n, ang in ANGLES.items():
        a = np.radians(ang)
        u = np.array([np.cos(a), 0.0, np.sin(a)])
        t = np.array([0.0, 1.0, 0.0])
        out[n] = dict(u=u, t=t, v=np.cross(u, t), c=np.array([0.0, y + vb.T / 2, AX_Z]))
        y += vb.T + DISC_T
    u, t = np.array([0.0, 1.0, 0.0]), np.array([1.0, 0.0, 0.0])            # the tail stands upright, cap facing backward
    out["tail"] = dict(u=u, t=t, v=np.cross(u, t), c=np.array([0.0, y + vb.R, AX_Z]))
    return out, y


def place(mesh, pl):
    """a mesh in vertebra coordinates (x = sideways v, y = press axis u, z = thickness 0..T) -> body coordinates."""
    M = np.eye(4)
    M[:3, 0], M[:3, 1], M[:3, 2] = pl["v"], pl["u"], pl["t"]
    M[:3, 3] = pl["c"] - pl["t"] * vb.T / 2
    m = mesh.copy()
    m.apply_transform(M)
    return m


def box_at(pl, u_c, size):
    m = trimesh.creation.box(extents=size)
    m.apply_translation([0, u_c, vb.T / 2])
    return place(m, pl)


def diagram(path):
    """a labelled front view of one vertebra, at rest and squeezed."""
    frame, springs, moving = vb.profiles()
    SC, W, Hh = 26, 1900, 1270
    img = Image.new("RGB", (W, Hh), (255, 255, 255))
    F = lambda s: ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", s)

    def draw(cs, ox, oy, col, dy=0.0):
        acc = np.zeros((Hh, W), bool)
        for p in cs.to_polygons():
            t = Image.new("1", (W, Hh), 0)
            ImageDraw.Draw(t).polygon([(ox + x * SC, oy - (y + dy) * SC) for x, y in p], fill=1)
            acc ^= np.array(t)
        arr = np.array(img)
        arr[acc] = col
        return Image.fromarray(arr)

    from manifold3d import CrossSection
    btn = CrossSection.square([6, 3.5]).translate([-3, vb.FLOOR_TOP]) + CrossSection.square([3.2, 1.5]).translate([-1.6, vb.FLOOR_TOP + 3.5])
    for k, (ox, press, title) in enumerate(((470, 0.0, "쉬는 상태"), (1360, vb.CLICK_AT + 0.25, "쥔 상태 (딸깍)"))):
        oy = 600
        img = draw(frame, ox, oy, (226, 205, 160))
        img = draw(springs, ox, oy, (90, 150, 215))
        img = draw(btn, ox, oy, (45, 45, 50))
        img = draw(moving, ox, oy, (232, 150, 120), dy=-press)
        d = ImageDraw.Draw(img)
        d.text((ox - 380, 40), title, font=F(44), fill=(20, 20, 20))
    d = ImageDraw.Draw(img)
    notes = [((232, 150, 120), "뚜껑 + 기둥: 쥐는 부분. 원반 둘레의 약 156도를 덮어요"),
             ((90, 150, 215), "지그재그 스프링: 버튼 양옆에 하나씩. 출력 평면 안에서 휘어요"),
             ((226, 205, 160), "틀: 바닥, 벽, 그리고 기둥을 잡고 뚜껑을 멈추는 턱 2개"),
             ((45, 45, 50), "택트 버튼 6×6: 열린 면으로 넣어요. 다리는 바닥 구멍으로 나가요")]
    y = Hh - 190
    for col, t in notes:
        d.rectangle([60, y, 100, y + 30], fill=col, outline=(20, 20, 20))
        d.text((120, y - 4), t, font=F(30), fill=(40, 40, 40)); y += 44
    d.text((1010, Hh - 190), f"원반 지름 {2 * vb.R:.0f}mm, 두께 {vb.T:.0f}mm", font=F(30), fill=(40, 40, 40))
    d.text((1010, Hh - 146), f"{vb.CLICK_AT + 0.25:.2f}mm에서 딸깍, {vb.TRAVEL}mm에서 턱에 닿아 멈춤", font=F(30), fill=(40, 40, 40))
    d.text((1010, Hh - 102), "서포트 없이 눕혀서 한 번에 출력", font=F(30), fill=(40, 40, 40))
    img.save(path)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    frame2, springs2, moving2 = vb.profiles()
    fixed3 = Manifold.extrude(frame2, vb.T) + Manifold.extrude(springs2, vb.SPR_H)
    for z0, z1 in ((-0.1, 1.55), (vb.T - 1.55, vb.T + 0.1)):
        fixed3 -= Manifold.cube([vb.SW + 0.6, 4.0, z1 - z0]).translate([-(vb.SW + 0.6) / 2, -vb.R - 0.5, z0])
    fixed_t, cap_t = vb.to_tm(fixed3), vb.to_tm(Manifold.extrude(moving2, vb.T))
    disc_t = vb.to_tm(Manifold.extrude(vb.disc(vb.R), DISC_T))
    pls, y_end = placements()

    statics, caps, sw_b, sw_p = [], {}, [], []
    for n, pl in pls.items():
        statics.append(place(fixed_t, pl))
        caps[n] = place(cap_t, pl)
        sw_b.append(box_at(pl, vb.FLOOR_TOP + vb.BODY / 2, (vb.SW, vb.BODY, vb.SW)))
        sw_p.append(box_at(pl, vb.FLOOR_TOP + vb.BODY + vb.PL / 2, (3.2, vb.PL, 3.2)))
    y = Y_FRONT - DISC_T
    for i in range(len(ANGLES) + 1):                                   # discs: front, between, back
        d_ = disc_t.copy()
        M = np.eye(4); M[:3, 0], M[:3, 1], M[:3, 2] = [1, 0, 0], [0, 0, 1], [0, 1, 0]; M[:3, 3] = [0, y, AX_Z]
        M[:3, 0] = [-1, 0, 0]
        d_.apply_transform(M); statics.append(d_)
        y += vb.T + DISC_T
    for sx in (-1, 1):                                                 # side covers of the upright tail
        d_ = disc_t.copy()
        M = np.eye(4); M[:3, 0], M[:3, 1], M[:3, 2] = [0, 1, 0], [0, 0, 1], [1, 0, 0]
        M[:3, 3] = pls["tail"]["c"] + np.array([sx * (vb.T / 2) - (0 if sx > 0 else DISC_T), 0, 0])
        d_.apply_transform(M); statics.append(d_)
    core = trimesh.util.concatenate(statics)

    # ---------------- checks ----------------
    ok = True
    lo = np.array([-40.0, -58.0, -2.0])
    Pb = mv.grid(lo, (40.0, 58.0, 54.0), H)
    D = ndimage.distance_transform_edt(body_field(Pb[..., 0], Pb[..., 1], Pb[..., 2]) < 0) * H
    del Pb

    def silicone(mesh):
        pts = np.asarray(mesh.vertices)
        extra = trimesh.sample.sample_surface(mesh, 4000)[0]
        pts = np.vstack([pts, extra])
        idx = np.clip(np.round((pts - lo) / H).astype(int), 0, np.array(D.shape) - 1)
        return D[idx[:, 0], idx[:, 1], idx[:, 2]]

    whole = trimesh.util.concatenate([core] + list(caps.values()))
    ext = whole.extents
    print(f"spine of vertebrae: {ext[0]:.0f} mm wide x {ext[1]:.0f} mm long x {ext[2]:.0f} mm tall   (body 75 x 110 x 52)")
    for n, c in caps.items():
        v = silicone(c)
        print(f"  cap {n:4s} faces {np.round(pls[n]['u'], 2)}: silicone over it {v.min():4.1f} - {v.max():4.1f} mm")
    w = float(silicone(whole).min())
    print(f"thinnest silicone over the skeleton: {w:.1f} mm (want >= 5):", w >= 5.0); ok &= w >= 5.0
    skull_gap = Y_FRONT - DISC_T - (v3.POD["c"][1] + v3.POD["r"][1])
    print(f"soft neck between the skull and the first vertebra: {skull_gap:.1f} mm of silicone, crossed only by 2 wires and a cord:", skull_gap >= 4.0); ok &= skull_gap >= 4.0
    # every direction round the body: how far is it from the nearest cap axis or its opposite (the back of a disc)?
    worst = 0.0
    for a in np.arange(0, 360, 1.0):
        best = min(min(abs((a - ang + 180) % 360 - 180), abs((a - ang) % 360 - 180)) for ang in ANGLES.values())
        worst = max(worst, best)
    cover = float(np.degrees(np.arccos((vb.CAP0 - vb.TRAVEL) / vb.R)))
    print(f"squeeze directions round the body: the furthest any direction is from a vertebra's axis is {worst:.0f} degrees (a cap reaches {cover:.0f} degrees each side):", worst <= cover); ok &= worst <= cover
    per = lambda a, b: np.pi * (3 * (a + b) - np.sqrt((3 * a + b) * (a + 3 * b)))
    print(f"face opening 34 x 18 mm must stretch {per(ext[0] / 2, ext[2] / 2) / per(17, 9):.2f}x to let the spine through")
    print("ALL CHECKS OK" if ok else "CHECK FAILED")
    diagram(os.path.join(OUT, "vertebra-diagram.png"))
    if "--checks" in sys.argv:
        sys.exit(0)

    # ---------------- viewer ----------------
    core.export(os.path.join(OUT, "spine-fixed.stl"))
    meshes = {"core": core, "sw_body": trimesh.util.concatenate(sw_b), "sw_plunger": trimesh.util.concatenate(sw_p)}
    for n, c in caps.items():
        meshes["bone_" + n] = c
    lo2 = np.array([-26.0, -46.0, 0.0])
    P = mv.grid(lo2, (26.0, 52.0, 46.0), H)
    meshes["skull"] = mv.slim(mv.mc(v5.skull_field(P), H, lo2), 20000)
    plate, ink = v5.build_skull_face()
    meshes["plate"], meshes["ink"] = mv.slim(plate, 24000), mv.slim(ink, 8000)
    h = 0.8
    Pbig = mv.grid(lo, (40.0, 58.0, 54.0), h)
    f = body_field(Pbig[..., 0], Pbig[..., 1], Pbig[..., 2])
    seat = ((Pbig[..., 0] / (mv.PLATE_A + 0.15)) ** 2 + ((Pbig[..., 2] - mv.PLATE_ZC) / (mv.PLATE_B + 0.15)) ** 2 < 1) & (Pbig[..., 1] < mv.Y_SKIN)
    meshes["body"] = mv.slim(mv.mc(np.where(seat, 1.0, f), h, lo), 60000)
    data = {k: mv.pack(t) for k, t in meshes.items()}
    movers = {n: dict(dir=(-pls[n]["u"]).tolist(), dist=vb.TRAVEL) for n in caps}
    fy = Y_FRONT - DISC_T
    wires = []
    for sx in (-1, 1):
        wires.append([(sx * 2.0, fy, AX_Z + 9), (sx * 5.0, fy - 4.0, AX_Z + 5), (sx * -1.0, fy - 8.0, AX_Z - 1.0),
                      (sx * 3.0, -22.0, 19.0), (sx * 3.0, -27.0, 16.5), (sx * 3.0, -31.0, 13.6)])
        wires.append([(sx * 6.0, -39.0, 15.6), (sx * 6.5, -38.0, 14.6), (sx * 7.0, -36.0, 13.6)])
    cord = [(0.0, fy, AX_Z + 3.0), (0.0, fy - 6, AX_Z + 6.0), (0.0, -21.5, 24.0)]
    cfg = dict(S=mv.S, YC=mv.YC, YF=mv.YF, movers=movers, wires=wires, cord=cord,
               parts={k: lay.PARTS[k] for k in ("board", "battery")})
    tpl = open(os.path.join(HERE, "viewer-template.html"), encoding="utf-8").read()
    tpl = tpl.replace("프린팅한 뼈 (두개골, 심, 뼈 5개)", "프린팅한 뼈 (두개골, 척추뼈 3마디)").replace("택트 버튼 5개", "택트 버튼 3개")
    html = tpl.replace("/*__MESHES__*/null", json.dumps(data)).replace("/*__CFG__*/null", json.dumps(cfg))
    out = os.path.join(HERE, "ppomo-skeleton-viewer.html")
    open(out, "w", encoding="utf-8").write(html)
    print("saved", out, f"({os.path.getsize(out) / 1e6:.1f} MB)")
