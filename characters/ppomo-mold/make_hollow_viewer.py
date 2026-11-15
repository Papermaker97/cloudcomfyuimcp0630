"""
3D viewer for the hollow (air-pressure) Ppomo: the silicone body, the air space inside it, the skull plug
with its raised face, the hose, and on request the mold halves with the dummy.

  python make_hollow_viewer.py   -> ../ppomo-skeleton/ppomo-skeleton-viewer.html
Needs: the same packages as make_hollow_mold.py
Written for the Ppomo project with help from Claude.
"""
import json
import os
import re

import numpy as np
import trimesh
from manifold3d import Manifold
from scipy import ndimage

import make_hollow_mold as hm
from make_hollow_mold import h, mm, mv, sk, body_field

HERE = os.path.dirname(os.path.abspath(__file__))
SKEL = os.path.join(HERE, "..", "ppomo-skeleton")

if __name__ == "__main__":
    m = hm.masks()
    lo = m["lo"]
    sp = hm.skull_plug()
    g = sp["g"]
    meshes = {}
    meshes["skull"] = mv.slim(mv.mc(ndimage.gaussian_filter((sp["shell"] | sp["cap"]).astype(np.float32), 0.6), sk.h, g["lo"], level=0.5), 80000)
    meshes["ink"] = mv.slim(mv.mc(ndimage.gaussian_filter(sp["face"].astype(np.float32), 0.5), sk.h, g["lo"], level=0.4), 8000)
    # the air space that stays empty once the skull plug is in: everything behind the plug's flat back
    air = m["space"] & (m["Y"] > hm.SKULL_BACK + 0.4)
    meshes["air"] = mv.slim(mv.mc(ndimage.gaussian_filter(air.astype(np.float32), 0.6), h, lo, level=0.5), 30000)
    # silicone body with the face opening
    hb = 0.8
    Pb = mv.grid(lo, (40.0, 58.0, 54.0), hb)
    f = body_field(Pb[..., 0], Pb[..., 1], Pb[..., 2])
    seat = ((np.abs(Pb[..., 0]) / (sk.WIN_A + 0.2)) ** sk.WIN_E + (np.abs(Pb[..., 2] - sk.WIN_Z) / (sk.WIN_B + 0.2)) ** sk.WIN_E < 1) & (Pb[..., 1] < sk.CY - sk.RY + 4)
    meshes["body"] = mv.slim(mv.mc(np.where(seat, 1.0, f), hb, lo), 60000)
    # dummy and mold, in body coordinates
    core = mm.to_manifold(mv.mc(ndimage.gaussian_filter(m["space"].astype(np.float32), 0.6), h, lo, level=0.5))
    dummy = core + hm.prism_y(sk.WIN_A, sk.WIN_B, hm.STEM_Y0, sk.CY - 6.0) + hm.prism_y(sk.WIN_A + 4.0, sk.WIN_B + 4.0, hm.STEM_Y0 - hm.FLANGE, hm.STEM_Y0)
    meshes["dummy"] = mv.slim(mm.to_trimesh(dummy), 40000)
    body_t = trimesh.load(mm.BODY_STL)
    (x0, y0, z0), (x1, y1, z1) = body_t.bounds
    W = mm.WALL
    X0, X1, Y0, Y1, Z0, Z1 = x0 - W, x1 + W, y0 - W, y1 + W, 0.0, z1 + W
    block = mm.box(X0, X1, Y0, Y1, Z0, Z1) - mm.to_manifold(body_t) - hm.prism_y(sk.WIN_A + hm.HOLE_CLEAR, sk.WIN_B + hm.HOLE_CLEAR, Y0 - 1.0, sk.CY)
    meshes["mold_l"] = mv.slim(mm.to_trimesh(block ^ mm.box(X0 - 1, 0, Y0 - 1, Y1 + 1, Z0 - 1, Z1 + 1)), 40000)
    meshes["mold_r"] = mv.slim(mm.to_trimesh(block ^ mm.box(0, X1 + 1, Y0 - 1, Y1 + 1, Z0 - 1, Z1 + 1)), 40000)
    data = {k: mv.pack(t) for k, t in meshes.items()}
    for k, d in data.items():
        print(f"{k:8s} {d['n']:6d} triangles")
    P_ = hm.PARTS
    boxes = [dict(b=P_["sensor"], color=0x965ABE), dict(b=P_["chip"], color=0x3C3C42), dict(b=hm.PORT, color=0xB4B6BE, metal=0.9)]
    wires = [[(7.0, -28.8, 16.0), (8.0, -27.0, 15.2), (7.5, -26.5, 14.5)], [(-7.0, -28.8, 16.0), (-8.0, -27.0, 15.2), (-7.5, -26.5, 14.5)],
             [(6.0, -37.0, 15.6), (6.5, -36.0, 15.0), (7.0, -34.0, 14.5)], [(-6.0, -37.0, 15.6), (-6.5, -36.0, 15.0), (-7.0, -34.0, 14.5)]]
    cfg = dict(S=mv.S, YC=mv.YC, YF=mv.YF, movers={}, wires=wires, boxes=boxes, clearDefault=True, boneOpacity=0.36,
               parts=dict(board=P_["board"], battery=P_["battery"]))
    tpl = open(os.path.join(SKEL, "viewer-template.html"), encoding="utf-8").read()
    key = '''<ul class="key" aria-label="부품 색">
    <li><span class="swatch" style="background:#EC8AA2"></span>실리콘 몸</li>
    <li><span class="swatch" style="background:#F2D27A"></span>공기 공간 (공기주머니, 스펀지를 채워요)</li>
    <li><span class="swatch" style="background:#D9C393"></span>두개골 (얼굴 + 마개 + 통)</li>
    <li><span class="swatch" style="background:#965ABE"></span>압력 센서</li>
    <li><span class="swatch" style="background:#2E7D5C"></span>블루투스 보드</li>
    <li><span class="swatch" style="background:#466EC8"></span>배터리</li>
    <li><span class="swatch" style="background:#D73C3C"></span>전선</li>
    <li><span class="swatch" style="background:#E8915A"></span>더미 (몰드 보기에서)</li>
  </ul>'''
    tpl = re.sub(r'<ul class="key".*?</ul>', key, tpl, flags=re.S)
    tpl = tpl.replace("<h1>뽀모 속 뼈대</h1>", "<h1>뽀모 속 공기주머니</h1>")
    tpl = tpl.replace('  <button id="btn-press" type="button" aria-pressed="false">쥐어보기</button>\n', "")
    tpl = tpl.replace("뼈 반투명", "두개골 반투명")
    html = tpl.replace("/*__MESHES__*/null", json.dumps(data)).replace("/*__CFG__*/null", json.dumps(cfg))
    out = os.path.join(SKEL, "ppomo-skeleton-viewer.html")
    open(out, "w", encoding="utf-8").write(html)
    print("saved", out, f"({os.path.getsize(out) / 1e6:.1f} MB)")
