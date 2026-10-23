"""Low-poly mannequin pose renderer for pose-reference test images.

Builds an articulated mannequin with forward kinematics, renders it with a
flat-shaded painter's-algorithm rasterizer (numpy + PIL only), and writes a
matching OpenPose (COCO-18) skeleton image for each shot.

Conventions (character faces +z, y is up, character's left is +x):
  Down-hanging limbs (arms, legs): x+ swings backward, x- swings forward,
  z+ moves toward +x (outward for left limbs, inward for right limbs).
  Elbow flex = x-, knee flex = x+.
  Up bones (spine, chest, neck, head): x+ leans forward, y+ turns to the
  character's left, z+ leans to the character's right.
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = os.path.dirname(os.path.abspath(__file__))
SS = 2  # supersampling factor


def rx(d):
    a = math.radians(d); c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def ry(d):
    a = math.radians(d); c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rz(d):
    a = math.radians(d); c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def euler(x=0, y=0, z=0):
    return rz(z) @ rx(x) @ ry(y)


def unit(v):
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else v


# ---------------------------------------------------------------- skeleton

def build_skeleton(prop):
    """Return bone table (name, parent, attach, vec, r0, r1) in head units."""
    N = prop["heads"]
    sw, hw, bulk = prop["sw"], prop["hw"], prop["bulk"]
    leg = N * prop.get("leg_ratio", 0.48)
    torso = N - leg - 1.0 - 0.3          # hip joint -> neck base
    s = N / 8.0
    thigh, shin = leg * 0.50, leg * 0.44  # remaining ~6% is ankle height
    b = bulk
    return [
        ("pelvis", None, (0, 0, 0), (0, 0, 0), 0, 0),
        ("spine", "pelvis", (0, 0, 0), (0, torso * 0.42, 0), 0, 0),
        ("chest", "spine", (0, 0, 0), (0, torso * 0.58, 0), 0, 0),
        ("neck", "chest", (0, 0, 0), (0, 0.3, 0), 0.15 * b, 0.14 * b),
        ("head", "neck", (0, 0, 0), (0, 1.0, 0), 0, 0),
        ("upperarm_l", "chest", (sw, -0.14, 0), (0, -1.45 * s, 0), 0.17 * b, 0.12 * b),
        ("forearm_l", "upperarm_l", (0, 0, 0), (0, -1.25 * s, 0), 0.12 * b, 0.08 * b),
        ("hand_l", "forearm_l", (0, 0, 0), (0, -0.7 * s, 0), 0.08 * b, 0.07 * b),
        ("upperarm_r", "chest", (-sw, -0.14, 0), (0, -1.45 * s, 0), 0.17 * b, 0.12 * b),
        ("forearm_r", "upperarm_r", (0, 0, 0), (0, -1.25 * s, 0), 0.12 * b, 0.08 * b),
        ("hand_r", "forearm_r", (0, 0, 0), (0, -0.7 * s, 0), 0.08 * b, 0.07 * b),
        ("thigh_l", "pelvis", (hw, 0, 0), (0, -thigh, 0), 0.30 * b, 0.18 * b),
        ("shin_l", "thigh_l", (0, 0, 0), (0, -shin, 0), 0.18 * b, 0.10 * b),
        ("foot_l", "shin_l", (0, 0, 0), (0, 0, 0.95 * s), 0, 0),
        ("thigh_r", "pelvis", (-hw, 0, 0), (0, -thigh, 0), 0.30 * b, 0.18 * b),
        ("shin_r", "thigh_r", (0, 0, 0), (0, -shin, 0), 0.18 * b, 0.10 * b),
        ("foot_r", "shin_r", (0, 0, 0), (0, 0, 0.95 * s), 0, 0),
    ]


def solve_fk(bones, pose):
    W = {}
    for name, parent, attach, vec, _, _ in bones:
        local = euler(*pose.get(name, (0, 0, 0)))
        if parent is None:
            R = euler(*pose.get("root", (0, 0, 0)))
            start = np.zeros(3)
        else:
            PR, _, pend = W[parent]
            start = pend + PR @ np.array(attach, float)
            if name.startswith("foot"):
                # keep feet flat on the ground unless the pose rotates them
                f = PR @ np.array([0, 0, 1.0]); f[1] = 0
                if np.linalg.norm(f) < 1e-6:
                    f = PR @ np.array([0, -1.0, 0]); f[1] = 0
                f = unit(f); up = np.array([0, 1.0, 0])
                R = np.column_stack([np.cross(up, f), up, f]) @ local
            else:
                R = PR @ local
        W[name] = (R, start, start + R @ np.array(vec, float))
    return W


# ---------------------------------------------------------------- geometry

class Mesh:
    def __init__(self):
        self.parts = []  # list of (verts Nx3, faces [idx lists], color)

    def add(self, verts, faces, color=(206, 201, 194), cull=True):
        verts = np.asarray(verts, float)
        c = verts.mean(axis=0)
        fixed = []
        for f in faces:
            p = verts[f]
            n = np.cross(p[1] - p[0], p[2] - p[0])
            if np.dot(n, p.mean(axis=0) - c) < 0:
                f = f[::-1]
            fixed.append(list(f))
        self.parts.append((verts, fixed, color, cull))


def prism(mesh, p0, p1, R, rx0, rz0, rx1, rz1, n=6, rot=0.0):
    ax, az = R[:, 0], R[:, 2]
    verts = []
    for p, a, b in ((p0, rx0, rz0), (p1, rx1, rz1)):
        for i in range(n):
            t = 2 * math.pi * i / n + rot
            verts.append(p + ax * a * math.cos(t) + az * b * math.sin(t))
    faces = [[i, (i + 1) % n, n + (i + 1) % n, n + i] for i in range(n)]
    faces += [list(range(n)), list(range(n, 2 * n))]
    mesh.add(verts, faces)


def ellipsoid(mesh, c, R, r, lat=5, lon=8):
    verts = [c + R @ np.array([0, r[1], 0])]
    for i in range(1, lat):
        th = math.pi * i / lat
        for j in range(lon):
            ph = 2 * math.pi * j / lon
            verts.append(c + R @ np.array([r[0] * math.sin(th) * math.cos(ph),
                                           r[1] * math.cos(th),
                                           r[2] * math.sin(th) * math.sin(ph)]))
    verts.append(c + R @ np.array([0, -r[1], 0]))
    last = len(verts) - 1
    faces = [[0, 1 + (j + 1) % lon, 1 + j] for j in range(lon)]
    for i in range(lat - 2):
        a, b = 1 + i * lon, 1 + (i + 1) * lon
        for j in range(lon):
            faces.append([a + j, a + (j + 1) % lon, b + (j + 1) % lon, b + j])
    base = 1 + (lat - 2) * lon
    faces += [[base + j, base + (j + 1) % lon, last] for j in range(lon)]
    mesh.add(verts, faces)


def box(mesh, c, R, half, color=(206, 201, 194)):
    hx, hy, hz = half
    verts = [c + R @ np.array([sx * hx, sy * hy, sz * hz])
             for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
    faces = [[0, 1, 3, 2], [4, 6, 7, 5], [0, 4, 5, 1], [2, 3, 7, 6], [0, 2, 6, 4], [1, 5, 7, 3]]
    mesh.add(verts, faces, color)


def build_mesh(bones, W, prop):
    m = Mesh()
    sw, hw, b = prop["sw"], prop["hw"], prop["bulk"]
    tw = prop.get("waist", 0.62)
    radii = {n: (r0, r1) for n, _, _, _, r0, r1 in bones}

    R, p0, _ = W["pelvis"]
    prism(m, p0 + R @ np.array([0, 0.25, 0]), p0 + R @ np.array([0, -0.32, 0]), R,
          hw + 0.2 * b, 0.36 * b, hw + 0.08 * b, 0.3 * b, n=8)
    R, p0, p1 = W["spine"]
    prism(m, p0 + R @ np.array([0, 0.2, 0]), p1, R, hw + 0.18 * b, 0.34 * b, tw * b, 0.3 * b, n=8)
    R, p0, p1 = W["chest"]
    prism(m, p0, p0 + (p1 - p0) * 0.55, R, tw * b, 0.3 * b, sw * 0.92, 0.4 * b, n=8)
    prism(m, p0 + (p1 - p0) * 0.55, p1, R, sw * 0.95, 0.4 * b, sw * 0.8, 0.3 * b, n=8)

    for name in ("neck", "upperarm_l", "forearm_l", "upperarm_r", "forearm_r",
                 "thigh_l", "shin_l", "thigh_r", "shin_r"):
        R, p0, p1 = W[name]
        r0, r1 = radii[name]
        prism(m, p0, p1, R, r0, r0 * 0.9, r1, r1 * 0.9, n=6, rot=math.pi / 6)
    for name, r in (("upperarm_l", 0.17), ("upperarm_r", 0.17), ("forearm_l", 0.12),
                    ("forearm_r", 0.12), ("thigh_l", 0.24), ("thigh_r", 0.24),
                    ("shin_l", 0.17), ("shin_r", 0.17)):
        R, p0, _ = W[name]
        ellipsoid(m, p0, R, (r * b,) * 3, lat=4, lon=6)
    for side in "lr":
        R, p0, p1 = W["hand_" + side]
        prism(m, p0, p1, R, 0.1 * b, 0.05 * b, 0.08 * b, 0.04 * b, n=4, rot=math.pi / 4)
        R, a, _ = W["shin_" + side]
        ellipsoid(m, W["shin_" + side][2], R, (0.1 * b,) * 3, lat=4, lon=6)
        R, a, e = W["foot_" + side]
        L = np.linalg.norm(e - a)
        prism(m, a + R @ np.array([0, -0.05, -0.12]), a + R @ np.array([0, -0.12, L]),
              R @ rx(90), 0.11 * b, 0.08 * b, 0.12 * b, 0.04 * b, n=4, rot=math.pi / 4)

    R, p0, _ = W["head"]
    hc = p0 + R @ np.array([0, 0.48, 0.04])
    ellipsoid(m, hc, R, (0.36, 0.5, 0.43), lat=6, lon=10)
    nose = hc + R @ np.array([0, -0.08, 0.41])
    m.add([nose + R @ np.array([-0.06, 0.05, 0]), nose + R @ np.array([0.06, 0.05, 0]),
           nose + R @ np.array([0, -0.08, 0]), nose + R @ np.array([0, -0.04, 0.12])],
          [[0, 1, 3], [1, 2, 3], [2, 0, 3], [0, 2, 1]])
    return m, hc


def keypoints(W, hc):
    """COCO-18 keypoints in world space (None = not present)."""
    R = W["head"][0]
    k = {
        "nose": hc + R @ np.array([0, -0.08, 0.45]),
        "r_eye": hc + R @ np.array([-0.14, 0.05, 0.37]),
        "l_eye": hc + R @ np.array([0.14, 0.05, 0.37]),
        "r_ear": hc + R @ np.array([-0.37, 0.0, 0.0]),
        "l_ear": hc + R @ np.array([0.37, 0.0, 0.0]),
    }
    for s, S in (("l", "l"), ("r", "r")):
        k[S + "_sho"] = W["upperarm_" + s][1]
        k[S + "_elb"] = W["forearm_" + s][1]
        k[S + "_wri"] = W["hand_" + s][1]
        k[S + "_hip"] = W["thigh_" + s][1]
        k[S + "_knee"] = W["shin_" + s][1]
        k[S + "_ank"] = W["foot_" + s][1]
    k["neck"] = (k["l_sho"] + k["r_sho"]) / 2
    return k


COCO = ["nose", "neck", "r_sho", "r_elb", "r_wri", "l_sho", "l_elb", "l_wri", "r_hip", "r_knee",
        "r_ank", "l_hip", "l_knee", "l_ank", "r_eye", "l_eye", "r_ear", "l_ear"]
LIMBS = [(2, 3), (2, 6), (3, 4), (4, 5), (6, 7), (7, 8), (2, 9), (9, 10), (10, 11), (2, 12),
         (12, 13), (13, 14), (2, 1), (1, 15), (15, 17), (1, 16), (16, 18)]
COLORS = [(255, 0, 0), (255, 85, 0), (255, 170, 0), (255, 255, 0), (170, 255, 0), (85, 255, 0),
          (0, 255, 0), (0, 255, 85), (0, 255, 170), (0, 255, 255), (0, 170, 255), (0, 85, 255),
          (0, 0, 255), (85, 0, 255), (170, 0, 255), (255, 0, 255), (255, 0, 170), (255, 0, 85)]


# ---------------------------------------------------------------- render

def render(shot, idx):
    prop, pose, cam = shot["prop"], shot["pose"], shot["cam"]
    Wd, Ht = shot["size"]
    bones = build_skeleton(prop)
    W = solve_fk(bones, pose)
    mesh, hc = build_mesh(bones, W, prop)

    # ground the figure: lowest vertex sits on y=0
    ymin = min(v[:, 1].min() for v, _, _, _ in mesh.parts)
    shift = np.array([0, -ymin, 0])
    mesh.parts = [(v + shift, f, c, cu) for v, f, c, cu in mesh.parts]
    W = {k: (R, a + shift, e + shift) for k, (R, a, e) in W.items()}
    hc = hc + shift
    kp = keypoints(W, hc)

    if "seat" in shot:  # box prop under the pelvis
        sh = W["pelvis"][1][1] - 0.32 * prop["bulk"]
        R0 = W["pelvis"][0]
        f = R0 @ np.array([0, 0, 1.0]); f[1] = 0; f = unit(f)
        Rb = np.column_stack([np.cross([0, 1.0, 0], f), [0, 1.0, 0], f])
        c = W["pelvis"][1].copy(); c[1] = sh / 2; c -= f * 0.25
        box(mesh, c, Rb, (shot["seat"], sh / 2, 0.75), color=(150, 158, 170))

    allv = np.vstack([v for v, _, _, _ in mesh.parts])
    height = allv[:, 1].max()
    center = (allv.min(axis=0) + allv.max(axis=0)) / 2
    target = np.array([center[0], height * cam.get("target", 0.5), center[2]])
    yaw, el = math.radians(cam["yaw"]), math.radians(cam["el"])
    dist = height * cam.get("dist", 3.2)
    eye = target + dist * np.array([math.sin(yaw) * math.cos(el), math.sin(el),
                                    math.cos(yaw) * math.cos(el)])
    fwd = unit(target - eye)
    right = unit(np.cross(fwd, [0, 1.0, 0]))
    up = np.cross(right, fwd)

    def proj(P):
        d = P - eye
        z = d @ fwd
        return np.stack([(d @ right) / z, (d @ up) / z], axis=-1), z

    pts2, _ = proj(allv)
    lo, hi = pts2.min(axis=0), pts2.max(axis=0)
    margin = 0.08
    scale = min(Wd * (1 - 2 * margin) / (hi[0] - lo[0]), Ht * (1 - 2 * margin) / (hi[1] - lo[1]))
    mid = (lo + hi) / 2

    def to_px(uv):
        return np.stack([Wd / 2 + (uv[..., 0] - mid[0]) * scale,
                         Ht / 2 - (uv[..., 1] - mid[1]) * scale], axis=-1) * SS

    L = unit(-0.45 * right + 0.75 * up - 0.5 * fwd)
    img = Image.new("RGB", (Wd * SS, Ht * SS), (236, 236, 238))
    dr = ImageDraw.Draw(img)

    # floor: horizon-free gradient band + contact shadow
    floor = []
    for i in range(48):
        t = 2 * math.pi * i / 48
        floor.append(np.array([center[0] + math.cos(t) * height * 0.3, 0.0,
                               center[2] + math.sin(t) * height * 0.22]))
    fp, fz = proj(np.array(floor))
    if (fz > 0).all() and el > -0.05:
        sh = Image.new("L", img.size, 0)
        ImageDraw.Draw(sh).polygon([tuple(p) for p in to_px(fp)], fill=70)
        sh = sh.filter(ImageFilter.GaussianBlur(14 * SS))
        img.paste((190, 190, 196), (0, 0), sh)

    faces = []
    for verts, flist, color, cull in mesh.parts:
        uv, z = proj(verts)
        px = to_px(uv)
        for f in flist:
            p = verts[f]
            n = unit(np.cross(p[1] - p[0], p[2] - p[0]))
            if cull and np.dot(n, eye - p.mean(axis=0)) <= 0:
                continue
            shade = 0.42 + 0.58 * max(0.0, float(n @ L))
            col = tuple(int(c * shade) for c in color)
            faces.append((z[f].mean(), [tuple(q) for q in px[f]], col))
    faces.sort(key=lambda t: -t[0])
    for _, poly, col in faces:
        edge = tuple(int(c * 0.82) for c in col)
        dr.polygon(poly, fill=col, outline=edge)
    img = img.resize((Wd, Ht), Image.LANCZOS)
    img.save(os.path.join(OUT, f"mannequin_{idx:02d}.png"))

    # openpose skeleton
    op = Image.new("RGB", (Wd, Ht), (0, 0, 0))
    od = ImageDraw.Draw(op)
    to_cam = unit(eye - hc)
    Rh = W["head"][0]
    face_fwd, face_left = Rh @ np.array([0, 0, 1.0]), Rh @ np.array([1.0, 0, 0])
    visible = {k: True for k in COCO}
    if face_fwd @ to_cam < -0.15:
        visible["nose"] = visible["l_eye"] = visible["r_eye"] = False
    if face_left @ to_cam < -0.35:
        visible["l_ear"] = False
    if -face_left @ to_cam < -0.35:
        visible["r_ear"] = False
    P = {k: to_px(proj(kp[k][None])[0])[0] / SS for k in COCO}
    sw_px = max(3, int(min(Wd, Ht) / 170))
    for i, (a, b) in enumerate(LIMBS):
        ka, kb = COCO[a - 1], COCO[b - 1]
        if not (visible[ka] and visible[kb]):
            continue
        col = tuple(int(c * 0.6) for c in COLORS[i])
        pa, pb = P[ka], P[kb]
        d = pb - pa
        length = np.linalg.norm(d)
        ang = math.atan2(d[1], d[0])
        poly = []
        for t in range(24):
            th = 2 * math.pi * t / 24
            x, y = length / 2 * math.cos(th), sw_px * math.sin(th)
            poly.append(((pa[0] + pb[0]) / 2 + x * math.cos(ang) - y * math.sin(ang),
                         (pa[1] + pb[1]) / 2 + x * math.sin(ang) + y * math.cos(ang)))
        od.polygon(poly, fill=col)
    for i, k in enumerate(COCO):
        if visible[k]:
            x, y = P[k]
            r = sw_px
            od.ellipse([x - r, y - r, x + r, y + r], fill=COLORS[i])
    op.save(os.path.join(OUT, f"openpose_{idx:02d}.png"))


# ---------------------------------------------------------------- shots

AVG_F = dict(heads=7.5, sw=0.85, hw=0.5, bulk=1.0)
SLIM_TALL = dict(heads=8.0, sw=0.82, hw=0.46, bulk=0.85, leg_ratio=0.5)
STOCKY = dict(heads=6.8, sw=1.08, hw=0.55, bulk=1.3, leg_ratio=0.45, waist=0.78)
HERO = dict(heads=8.5, sw=1.12, hw=0.46, bulk=1.1, leg_ratio=0.5, waist=0.6)
PETITE = dict(heads=6.5, sw=0.8, hw=0.5, bulk=0.95, leg_ratio=0.46)
ATHLETIC_M = dict(heads=8.0, sw=1.1, hw=0.45, bulk=1.15, waist=0.66)
AVG_7 = dict(heads=7.0, sw=0.9, hw=0.52, bulk=1.0)

SHOTS = [
    dict(name="A-pose, front, 7.5 heads", size=(1024, 1536), prop=AVG_F,
         pose=dict(upperarm_l=(0, 0, 22), upperarm_r=(0, 0, -22),
                   forearm_l=(-8, 0, 0), forearm_r=(-8, 0, 0),
                   thigh_l=(0, 0, 4), thigh_r=(0, 0, -4)),
         cam=dict(yaw=0, el=4)),
    dict(name="walking, 3/4 front-left, 8 heads slim", size=(1024, 1536), prop=SLIM_TALL,
         pose=dict(thigh_l=(-28, 0, 2), shin_l=(12, 0, 0), thigh_r=(18, 0, -2), shin_r=(32, 0, 0),
                   foot_r=(25, 0, 0),
                   upperarm_r=(-22, 0, -6), forearm_r=(-25, 0, 0),
                   upperarm_l=(22, 0, 6), forearm_l=(-12, 0, 0),
                   spine=(3, -6, 0), chest=(0, -6, 0), head=(0, 10, 0)),
         cam=dict(yaw=35, el=8)),
    dict(name="hands on hips, 3/4 right profile, 6.8 heads stocky", size=(1024, 1024), prop=STOCKY,
         pose=dict(upperarm_l=(12, -90, 48), forearm_l=(-105, 0, 0),
                   upperarm_r=(12, 90, -48), forearm_r=(-105, 0, 0),
                   thigh_l=(0, 0, 9), thigh_r=(0, 0, -9), chest=(-4, 0, 0), head=(-6, 0, 0)),
         cam=dict(yaw=-62, el=6)),
    dict(name="sitting on a box, 3/4 front, 7.5 heads", size=(1024, 1024), prop=AVG_F, seat=0.9,
         pose=dict(thigh_l=(-86, 0, 10), shin_l=(80, 0, -6), thigh_r=(-86, 0, -14), shin_r=(95, 0, 8),
                   spine=(8, 0, 0), chest=(6, 0, 0), head=(-8, 15, 0),
                   upperarm_l=(-28, 0, 10), forearm_l=(-55, 0, 0),
                   upperarm_r=(-20, 0, -12), forearm_r=(-60, 0, 0)),
         cam=dict(yaw=28, el=10)),
    dict(name="running, low angle, 8.5 heads heroic", size=(1152, 2048), prop=HERO,
         pose=dict(spine=(14, 6, 0), chest=(4, 6, 0), head=(-14, -10, 0),
                   thigh_l=(-60, 0, 3), shin_l=(80, 0, 0),
                   thigh_r=(28, 0, -3), shin_r=(50, 0, 0), foot_r=(35, 0, 0),
                   upperarm_r=(-45, 0, -8), forearm_r=(-75, 0, 0),
                   upperarm_l=(38, 0, 8), forearm_l=(-65, 0, 0)),
         cam=dict(yaw=-65, el=-10, dist=2.4, target=0.45)),
    dict(name="looking back over shoulder, back view, 7 heads", size=(1024, 1536), prop=AVG_7,
         pose=dict(root=(0, 0, -4), thigh_r=(0, 0, 0), thigh_l=(-10, 0, 7), shin_l=(18, 0, 0),
                   spine=(0, 25, 6), chest=(0, 18, 2), neck=(0, 20, 0), head=(-4, 42, 0),
                   upperarm_l=(10, 0, 10), forearm_l=(-20, 0, 0),
                   upperarm_r=(-4, 0, -8), forearm_r=(-15, 0, 0)),
         cam=dict(yaw=165, el=5)),
    dict(name="kneeling on one knee, high angle, 6.5 heads petite", size=(1024, 1024), prop=PETITE,
         pose=dict(thigh_r=(8, 0, -6), shin_r=(88, 0, 0), foot_r=(20, 0, 0),
                   thigh_l=(-92, 0, 8), shin_l=(92, 0, 0),
                   spine=(12, -8, 0), chest=(4, 0, 0), head=(-20, 0, 0),
                   upperarm_l=(-18, 0, 10), forearm_l=(-28, 0, 0),
                   upperarm_r=(4, 0, -12), forearm_r=(-20, 0, 0)),
         cam=dict(yaw=55, el=28)),
    dict(name="waving, 3/4 right, 8 heads athletic male", size=(1536, 1024), prop=ATHLETIC_M,
         pose=dict(root=(0, 0, 3), thigh_l=(-6, 0, 6), shin_l=(14, 0, 0), thigh_r=(0, 0, -4),
                   upperarm_r=(-10, 0, -128), forearm_r=(0, 0, -30), hand_r=(0, 0, -10),
                   upperarm_l=(8, 0, 8), forearm_l=(-30, 0, 0),
                   spine=(0, -8, 3), chest=(0, -6, 0), head=(0, -15, 6)),
         cam=dict(yaw=-40, el=2)),
]


def contact_sheet():
    tiles = []
    for i in range(1, len(SHOTS) + 1):
        a = Image.open(os.path.join(OUT, f"mannequin_{i:02d}.png"))
        b = Image.open(os.path.join(OUT, f"openpose_{i:02d}.png"))
        h = 420
        a = a.resize((int(a.width * h / a.height), h))
        b = b.resize((int(b.width * h / b.height), h))
        t = Image.new("RGB", (a.width + b.width + 8, h), (255, 255, 255))
        t.paste(a, (0, 0)); t.paste(b, (a.width + 8, 0))
        tiles.append(t)
    cols = 2
    rows = math.ceil(len(tiles) / cols)
    cw = max(t.width for t in tiles) + 24
    sheet = Image.new("RGB", (cw * cols, (420 + 24) * rows), (255, 255, 255))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % cols) * cw + 12, (i // cols) * 444 + 12))
    sheet.save(os.path.join(OUT, "_contact_sheet.png"))


if __name__ == "__main__":
    only = [int(a) for a in sys.argv[1:]]
    for i, shot in enumerate(SHOTS, 1):
        if not only or i in only:
            render(shot, i)
            print(i, shot["name"])
    contact_sheet()
