"""
Ppomo final product, as one 3D viewer (no skeleton, no translucent body):

  * SILICONE BODY  the v6 Ppomo body, 110 mm, cast hollow: a pocket in the head for the face module,
                   a short neck passage, and a pocket in the torso for the air bag. Opaque pink silicone.
  * FABRIC COVER   a sewn cover over the silicone, open at the face (silicone feels tacky and grabs dust).
  * FACE MODULE    one printed part = the face (eyes, nose, mouth stand out), the plug that closes the
                   body, and the box that holds the electronics. It is pushed into the head pocket.
  * AIR BAG        a sealed bag in the torso pocket. Squeezing the body squeezes the bag; a short hose
                   carries the pressure to the sensor in the face module.
  * ELECTRONICS    in the face module, low-poly boxes at their real sizes:
                   MPRLS pressure sensor (Adafruit 3965: 17.8 x 16.7 mm, 2.5 mm port),
                   a small Bluetooth board (stand-in, about 21 x 17.5 mm, e.g. a XIAO-size board),
                   a small LiPo cell (stand-in, about 20 x 10 x 5 mm).

  python make_final_viewer.py   ->  ppomo-final/ppomo-final-viewer.html
Reuses the checked geometry of make_hollow_mold.py (body, pockets, face module, part layout).
Written for the Ppomo project with help from Claude.
"""
import base64
import json
import os

import numpy as np
from scipy import ndimage

import make_hollow_mold as hm
from make_hollow_mold import h, mv, sk, body_field

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "ppomo-final")
COVER_GAP, COVER_T = 0.4, 1.0        # mm: the cover sits this far off the silicone, this thick
BAG_GAP = 1.5                        # mm: the air bag is this much smaller than its pocket


def pack(t):
    """mesh in body mm -> viewer mm (y up, face toward +z)."""
    v = np.asarray(t.vertices, dtype=np.float64)
    p = np.column_stack([v[:, 0], v[:, 2], -v[:, 1]]).astype(np.float32)
    f = np.asarray(t.faces, dtype=np.uint32)
    return {"p": base64.b64encode(p.tobytes()).decode(), "i": base64.b64encode(f.tobytes()).decode(), "n": int(len(f))}


def box(b):
    x0, x1, y0, y1, z0, z1 = b
    return [x0, z0, -y1, x1, z1, -y0]          # min / max corners in viewer space


def window(X, Y, Z, grow):
    return ((np.abs(X) / (sk.WIN_A + grow)) ** sk.WIN_E + (np.abs(Z - sk.WIN_Z) / (sk.WIN_B + grow)) ** sk.WIN_E < 1) & (Y < sk.CY)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    m = hm.masks()
    lo, X, Y, Z = m["lo"], m["X"], m["Y"], m["Z"]
    meshes = {}

    # silicone body: the body minus its pockets (the head pocket is open at the face)
    sil = m["body"] & ~m["space"]
    meshes["body"] = mv.slim(mv.mc(ndimage.gaussian_filter(sil.astype(np.float32), 0.6), h, lo, level=0.5), 90000)

    # air bag: the torso pocket, BAG_GAP smaller all round, plus a short neck where the hose goes in
    inner = ndimage.distance_transform_edt(m["torso"]) * h >= BAG_GAP
    a, b = np.array(hm.NECK[0]), np.array(hm.NECK[1])
    P = np.stack([X, Y, Z], -1)
    t = np.clip(((P - b) @ (a - b)) / ((a - b) @ (a - b)), 0, 0.35)
    bag_neck = np.linalg.norm(P - (b + t[..., None] * (a - b)), axis=-1) < 2.6
    bag = ndimage.gaussian_filter((inner | bag_neck).astype(np.float32), 0.8) > 0.5
    meshes["bag"] = mv.slim(mv.mc(ndimage.gaussian_filter(bag.astype(np.float32), 0.6), h, lo, level=0.5), 30000)

    # fabric cover: a thin skin just outside the silicone, open where the face is
    # (body_field is not an exact distance; it is close enough near the surface for a 1 mm skin)
    clo = lo - 3.0
    G = mv.grid(clo, (43.0, 61.0, 57.0), h)
    CX, CY_, CZ = G[..., 0], G[..., 1], G[..., 2]
    d_mm = body_field(CX, CY_, CZ) * sk.S
    cover = (d_mm > COVER_GAP) & (d_mm < COVER_GAP + COVER_T) & ~window(CX, CY_, CZ, 1.2)
    meshes["cover"] = mv.slim(mv.mc(ndimage.gaussian_filter(cover.astype(np.float32), 0.5), h, clo, level=0.5), 90000)

    # face module: shell + back cap, and the raised face
    sp = hm.skull_plug()
    g = sp["g"]
    meshes["face"] = mv.slim(mv.mc(ndimage.gaussian_filter((sp["shell"] | sp["cap"]).astype(np.float32), 0.6), sk.h, g["lo"], level=0.5), 80000)
    meshes["ink"] = mv.slim(mv.mc(ndimage.gaussian_filter(sp["face"].astype(np.float32), 0.5), sk.h, g["lo"], level=0.4), 8000)

    # numbers for the page
    vol_body = m["body"].sum() * h ** 3 / 1000
    vol_sil = sil.sum() * h ** 3 / 1000
    vol_bag = bag.sum() * h ** 3 / 1000
    ext = np.ptp(np.argwhere(m["body"]), 0) * h
    port_tip_y = hm.PORT[3]
    bag_front_y = float(Y[bag & (np.abs(X) < 1) & (np.abs(Z - 21) < 1.5)].min())
    hose = [[0.0, hm.PORT_Z, -port_tip_y + 1.0], [0.0, (hm.PORT_Z + hm.NECK[1][2]) / 2, -(port_tip_y + bag_front_y) / 2], [0.0, hm.NECK[1][2], -bag_front_y - 3.0]]
    info = dict(
        size=[round(float(e)) for e in ext], body_cm3=round(float(vol_body)), silicone_cm3=round(float(vol_sil)),
        silicone_g=round(float(vol_sil * 1.07)), bag_cm3=round(float(vol_bag)), hose_mm=round(float(bag_front_y + 3 - port_tip_y + 1)),
    )
    print(info)

    P_ = hm.PARTS
    cfg = dict(
        info=info,
        boxes=[
            dict(name="sensor", b=box(P_["sensor"]), color=0x2F5FB8),
            dict(name="sensor", b=box(P_["chip"]), color=0xD5D8DE),
            dict(name="board", b=box(P_["board"]), color=0x2E7D5C),
            dict(name="battery", b=box(P_["battery"]), color=0xC9A43A),
        ],
        port=dict(a=[0.0, hm.PORT_Z, -hm.PORT[2]], b=[0.0, hm.PORT_Z, -hm.PORT[3]], r=hm.PORT_D / 2),
        hose=hose,
        wires=[[[7.0, 16.0, 28.8], [8.0, 15.2, 27.0], [7.5, 14.5, 26.5]], [[-7.0, 16.0, 28.8], [-8.0, 15.2, 27.0], [-7.5, 14.5, 26.5]],
               [[6.0, 15.6, 37.0], [6.5, 15.0, 36.0], [7.0, 14.5, 34.0]], [[-6.0, 15.6, 37.0], [-6.5, 15.0, 36.0], [-7.0, 14.5, 34.0]]],
    )
    data = {k: pack(v) for k, v in meshes.items()}
    for k, d in data.items():
        print(f"{k:6s} {d['n']:6d} triangles")
    tpl = open(os.path.join(HERE, "final-viewer-template.html"), encoding="utf-8").read()
    html = tpl.replace("/*__MESHES__*/null", json.dumps(data)).replace("/*__CFG__*/null", json.dumps(cfg))
    out = os.path.join(OUT, "ppomo-final-viewer.html")
    open(out, "w", encoding="utf-8").write(html)
    print("saved", out, f"({os.path.getsize(out) / 1e6:.1f} MB)")
