"""
Build the turn-it-around 3D viewer for the Ppomo bone clicker concept (v3):
the translucent silicone body, the slightly translucent printed skeleton, and the parts that are not
printed (button, board, battery, spring, wires), all in one page.

  python make_viewer.py   -> ppomo-skeleton-viewer.html   (one self-contained file; three.js comes from a CDN)

It re-meshes everything from the same formulas as make_bone_concept_v3.py and make_head_layout.py,
at a size a browser can load quickly. The rod and tail are a separate mesh so the page can show a press.
Needs: pip install numpy scipy trimesh scikit-image fast-simplification
Written for the Ppomo project with help from Claude.
"""
import base64
import json
import os

import numpy as np
import trimesh
from skimage import measure

import make_bone_concept_v3 as v3
import make_head_layout as lay
from make_bone_concept import body_field, capsule, sminp

HERE = os.path.dirname(os.path.abspath(__file__))
VIEW = os.path.join(HERE, "..", "ppomo-mold", "faceplate-view")
S, YC, YF = 51.97, 3.21, 0.0355
PLATE_A, PLATE_B, PLATE_ZC, Y_SKIN = 20.0, 12.0, 18.5, -47.9


def mc(field, h, lo, level=0.0):
    v, f, _, _ = measure.marching_cubes(field, level, spacing=(h, h, h))
    t = trimesh.Trimesh(v + lo, f, process=True)
    if t.volume < 0:
        t.invert()
    return t


def slim(t, target):
    if len(t.faces) > target:
        try:
            t = t.simplify_quadric_decimation(face_count=target)
        except Exception as e:                       # keep the full mesh if the simplifier is missing
            print("  (not simplified:", e, ")")
    return t


def pack(t):
    """mesh in body mm -> viewer units (the same space as ppomo-v6.html: y up, face toward +z)."""
    v = np.asarray(t.vertices, dtype=np.float64)
    p = np.column_stack([v[:, 0] / S, v[:, 2] / S + YF, -(v[:, 1] + YC) / S]).astype(np.float32)
    f = np.asarray(t.faces, dtype=np.uint32)
    return {"p": base64.b64encode(p.tobytes()).decode(), "i": base64.b64encode(f.tobytes()).decode(), "n": int(len(f))}


def grid(lo, hi, h):
    ax = [np.arange(lo[i], hi[i] + h, h) for i in range(3)]
    return np.stack(np.meshgrid(*ax, indexing="ij"), -1).astype(np.float32)


if __name__ == "__main__":
    meshes = {}
    # silicone body, with the seat for the face plate carved out
    h = 0.8
    lo = np.array([-40.0, -58.0, -2.0])
    P = grid(lo, (40.0, 58.0, 54.0), h)
    f = body_field(P[..., 0], P[..., 1], P[..., 2])
    seat = ((P[..., 0] / (PLATE_A + 0.15)) ** 2 + ((P[..., 2] - PLATE_ZC) / (PLATE_B + 0.15)) ** 2 < 1) & (P[..., 1] < Y_SKIN)
    f = np.where(seat, 1.0, f)
    meshes["body"] = slim(mc(f, h, lo), 60000)
    # printed parts
    h = 0.5
    lo = np.array([-26.0, -46.0, 0.0])
    P = grid(lo, (26.0, 52.0, 46.0), h)
    fixed = v3.pod_field(P)
    fixed = sminp(fixed, capsule(P, (0, v3.PLATE_BACK - 0.5, 18.5), (0, v3.POD["c"][1], 18.5), 8.0), 3.0)
    for hy in v3.HUB_Y:
        fixed = sminp(fixed, v3.ellip(P, (0, hy, v3.AX_Z), (v3.HUB_R, 4.2, v3.HUB_R)), 1.5)
        for ux, uz in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            fixed = sminp(fixed, capsule(P, (0, hy, v3.AX_Z), (ux * (v3.HUB_R - 2.4), hy, v3.AX_Z + uz * (v3.HUB_R - 2.4)), 2.9), 1.0)
    for sx in (-1, 1):
        fixed = sminp(fixed, capsule(P, (sx * 3.3, v3.POD["c"][1] + 6, v3.AX_Z + 3.3), (sx * 3.3, v3.HUB_Y[1], v3.AX_Z + 3.3), 1.7), 1.0)
    meshes["fixed"] = slim(mc(fixed, h, lo), 30000)
    rod = capsule(P, (0, lay.ROD_TIP_REST, v3.AX_Z), (0, v3.TAIL["c"][1], v3.AX_Z), v3.ROD_R - 0.3)
    rod = sminp(rod, v3.ellip(P, (0, v3.TAIL["c"][1] - 6.5, v3.AX_Z), (4.6, 3.0, 4.6)), 1.5)
    rod = sminp(rod, v3.ellip(P, v3.TAIL["c"], v3.TAIL["r"]), 2.5)
    rod = np.minimum(rod, capsule(P, (0, lay.SPRING[1], v3.AX_Z), (0, lay.SPRING[1] + 1.2, v3.AX_Z), 4.2))   # spring collar
    meshes["rod"] = slim(mc(rod, h, lo), 12000)
    for n in v3.BONES:
        meshes["bone_" + n] = slim(mc(sminp(v3.bone_field(P, n), v3.stem_field(P, n), 2.6), h, lo), 14000)
    for n in ("plate", "ink"):
        meshes[n] = slim(trimesh.load(os.path.join(VIEW, n + ".stl"), process=True), 20000)
    data = {k: pack(t) for k, t in meshes.items()}
    for k, d in data.items():
        print(f"{k:12s} {d['n']:6d} triangles")
    wires = [
        [(1.6, lay.PARTS["button"][2], v3.AX_Z + 2), (1.6, -33.0, 21.0), (2.5, -33.0, 15.5), (3.0, -34.0, 13.6)],
        [(-1.6, lay.PARTS["button"][2], v3.AX_Z - 2), (-1.6, -31.5, 17.0), (-2.5, -31.5, 15.0), (-3.0, -30.0, 13.6)],
        [(6.0, -39.0, 15.6), (6.5, -38.0, 14.6), (7.0, -36.0, 13.6)],
        [(-6.0, -39.0, 15.6), (-6.5, -38.0, 14.6), (-7.0, -36.0, 13.6)],
    ]
    cfg = dict(S=S, YC=YC, YF=YF, axZ=v3.AX_Z, travel=v3.TRAVEL, parts=lay.PARTS, plungerTip=lay.PLUNGER_TIP,
               spring=lay.SPRING, wires=wires, dirs={n: v3.BONES[n]["u"] for n in v3.BONES})
    tpl = open(os.path.join(HERE, "viewer-template.html"), encoding="utf-8").read()
    html = tpl.replace("/*__MESHES__*/null", json.dumps(data)).replace("/*__CFG__*/null", json.dumps(cfg))
    out = os.path.join(HERE, "ppomo-skeleton-viewer.html")
    open(out, "w", encoding="utf-8").write(html)
    print("saved", out, f"({os.path.getsize(out) / 1e6:.1f} MB)")
