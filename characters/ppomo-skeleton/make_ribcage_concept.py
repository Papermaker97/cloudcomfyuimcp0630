"""
Ppomo skeleton, look concept "mask + ribcage" (follows the owner's three reference images).

What the references show
  * a hard face that shows through the soft hood like a mask, continuing into a round skull inside the head;
    the eyes are real holes, so the inside can be glimpsed
  * a row of fat, rounded ribs that wrap the torso from a spine along the back, seen as soft bands
    through the translucent silicone
  * ears, paws and cheeks stay silicone

This script fits that look to Ppomo's real body and checks the sizes. It is a LOOK concept:
how a squeeze of the ribs becomes one click is not designed here.
Each rib lies in one flat slice across the body, so it could be printed flat and bend in its print plane.

  python make_ribcage_concept.py   -> bone-concept/ribcage/*.stl, checks, ppomo-skeleton-viewer.html
Needs: pip install numpy scipy trimesh scikit-image fast-simplification
Written for the Ppomo project with help from Claude.
"""
import json
import os

import numpy as np
from scipy import ndimage

import make_skull as sk
import make_viewer as mv
from make_bone_concept import H, body_field

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "bone-concept", "ribcage")
SIL = 9.0                         # silicone left over the ribs
RIB_T = 4.6                       # rib thickness (toward the inside)
RIB_W = 5.0                       # rib width along the body
RIB_Y = (-3.0, 6.0, 15.0, 24.0, 33.0)     # five ribs, 9 mm apart (4 mm of space between them)
BELLY_GAP = 7.0                   # the ribs stop this far from the belly centre line, like real ribs
SPINE_HALF = 3.6                  # half-width of the spine along the back
SPINE_Y = (-8.0, 38.0)

# the mask: a larger, squarer opening than skull v1, and real eye holes
sk.WIN_A, sk.WIN_B, sk.WIN_E = 20.0, 11.0, 3.0


def skull_with_eye_holes():
    g = sk.build()
    X, Y, Z = g["X"], g["Y"], g["Z"]
    eyes = (Y < sk.CY) & ((np.abs(X) - sk.EYE_X) ** 2 / sk.EYE_RX ** 2 + (Z - sk.EYE_Z) ** 2 / sk.EYE_RZ ** 2 < 1)
    g["shell"] = g["shell"] & ~eyes                    # the dot eyes become real holes
    lab, n = ndimage.label(g["ink"])                   # keep only the nose and mouth as dark fill
    for i in range(1, n + 1):
        blob = lab == i
        if np.abs(X[blob]).mean() > 6:                 # an eye dimple
            g["ink"] &= ~blob
    return g


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    lo = np.array([-40.0, -58.0, -2.0])
    P = mv.grid(lo, (40.0, 58.0, 54.0), H)
    X, Y, Z = P[..., 0], P[..., 1], P[..., 2]
    body = body_field(X, Y, Z) < 0
    D = ndimage.distance_transform_edt(body) * H
    band = (D >= SIL) & (D < SIL + RIB_T)
    zc = 22.0
    ribs = np.zeros(body.shape, bool)
    for y in RIB_Y:
        ribs |= band & (np.abs(Y - y) < RIB_W / 2) & ~((np.abs(X) < BELLY_GAP) & (Z < zc))
    spine = band & (np.abs(X) < SPINE_HALF) & (Z > zc) & (Y > SPINE_Y[0]) & (Y < SPINE_Y[1])
    cage = ndimage.gaussian_filter((ribs | spine).astype(np.float32), 1.0 / H) > 0.42      # round everything off

    ok = True
    for name, m in (("ribs", ribs & cage), ("spine", spine & cage)):
        v = D[m]
        print(f"{name:5s}: silicone over them {v.min():.1f} - {v.max():.1f} mm")
    idx = np.argwhere(cage)
    ext = (idx.max(0) - idx.min(0)) * H
    print(f"ribcage: {ext[0]:.0f} mm wide x {ext[1]:.0f} mm long x {ext[2]:.0f} mm tall, {len(RIB_Y)} ribs {RIB_W:.0f} mm wide with {RIB_Y[1] - RIB_Y[0] - RIB_W:.0f} mm between them")
    w = float(D[cage].min())
    print(f"thinnest silicone over the ribcage: {w:.1f} mm (want >= 5):", w >= 5.0); ok &= w >= 5.0
    g = skull_with_eye_holes()
    ok &= sk.checks(g)
    gap = min(RIB_Y) - RIB_W / 2 - (sk.CY + sk.RY)
    print(f"soft neck between the skull and the first rib: {gap:.1f} mm:", gap >= 4.0); ok &= gap >= 4.0
    print("LOOK CONCEPT OK" if ok else "CHECK FAILED")

    cage_t = mv.mc(ndimage.gaussian_filter(cage.astype(np.float32), 0.6), H, lo, level=0.5)
    cage_t.export(os.path.join(OUT, "ribcage.stl"))
    skull_t, ink_t = sk.meshes(g)
    mv.slim(skull_t, 250000).export(os.path.join(OUT, "skull-mask.stl"))
    meshes = {"core": mv.slim(cage_t, 60000), "skull": mv.slim(skull_t, 60000), "ink": mv.slim(ink_t, 6000)}
    h = 0.8
    Pb = mv.grid(lo, (40.0, 58.0, 54.0), h)
    f = body_field(Pb[..., 0], Pb[..., 1], Pb[..., 2])
    seat = ((np.abs(Pb[..., 0]) / (sk.WIN_A + 0.2)) ** sk.WIN_E + (np.abs(Pb[..., 2] - sk.WIN_Z) / (sk.WIN_B + 0.2)) ** sk.WIN_E < 1) & (Pb[..., 1] < sk.CY - sk.RY + 4)
    meshes["body"] = mv.slim(mv.mc(np.where(seat, 1.0, f), h, lo), 60000)
    data = {k: mv.pack(t) for k, t in meshes.items()}
    wires = []
    for sx in (-1, 1):
        wires.append([(sx * 6.0, -37.0, 15.6), (sx * 6.5, -36.0, 14.6), (sx * 7.0, -34.0, 13.6)])
    cfg = dict(S=mv.S, YC=mv.YC, YF=mv.YF, movers={}, wires=wires, parts=sk.parts())
    tpl = open(os.path.join(HERE, "viewer-template.html"), encoding="utf-8").read()
    tpl = tpl.replace("프린팅한 뼈 (두개골, 심, 뼈 5개)", "프린팅한 뼈 (두개골 가면, 갈비뼈, 척추)")
    tpl = tpl.replace('    <li><span class="swatch" style="background:#2B2B31"></span>택트 버튼 5개</li>\n', "")
    tpl = tpl.replace('    <li><span class="swatch" style="background:#8A6A3C"></span>당기는 끈</li>\n', "")
    tpl = tpl.replace('  <button id="btn-press" type="button" aria-pressed="false">쥐어보기</button>\n', "")
    html = tpl.replace("/*__MESHES__*/null", json.dumps(data)).replace("/*__CFG__*/null", json.dumps(cfg))
    out = os.path.join(HERE, "ppomo-skeleton-viewer.html")
    open(out, "w", encoding="utf-8").write(html)
    print("saved", out, f"({os.path.getsize(out) / 1e6:.1f} MB)")
