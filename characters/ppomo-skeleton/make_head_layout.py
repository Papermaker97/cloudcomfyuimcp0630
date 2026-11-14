"""
Ppomo head pod layout: where the parts that are NOT 3D printed go (button, board, battery, spring, wires).

It places real part sizes inside the head pod of bone concept v3, checks that each one fits with
room for the pod wall, and draws a labelled cutaway (side view and top view).

Parts and the sizes used (check the ones you actually buy):
  tactile button      6 x 6 x 3.5 mm body + 1.5 mm plunger            (the click and the signal)
  Seeed XIAO nRF52840 21 x 17.5 x 3.5 mm incl. parts, USB-C on a short edge (Bluetooth + battery charger on board)
  LiPo battery        5 x 10 x 20 mm class ("501020")                   (capacity: read the label of the cell you buy)
  return spring       about 8 mm wide, 8 mm long, on the rod behind the pod (metal, or the printed spiral)
  wires               2 short wires button -> board, 2 wires battery -> board

  python make_head_layout.py  -> bone-concept/v3/head-layout.png
Needs: numpy pillow (and the v3 concept script next to this file)
Written for the Ppomo project with help from Claude.
"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import make_bone_concept_v3 as v3
from make_bone_concept import body_field

OUT = os.path.join(v3.OUT, "head-layout.png")
WALL = 1.6
AX = v3.AX_Z
PLATE_FRONT, PLATE_BACK = -55.0, v3.PLATE_BACK
PASS = dict(x=13.0, z0=11.3, z1=25.7, y1=-36.0)          # hollow neck between the plate and the pod
# boxes: (x0, x1, y0, y1, z0, z1) in mm, body coordinates (y = front to back, z = up)
PARTS = {
    "button": (-3.0, 3.0, -29.0, -25.5, AX - 3.0, AX + 3.0),
    "board": (-8.75, 8.75, -47.6, -26.6, 12.0, 15.5),
    "battery": (-10.0, 10.0, -42.6, -37.6, 15.6, 25.6),
}
BULKHEAD = (-30.5, -29.0)       # printed wall the button sits on
PLUNGER_TIP = -24.0
ROD_TIP_REST = PLUNGER_TIP + 3.1
SPRING = (-21.0, -13.0)
COL = {"button": (40, 40, 46), "board": (46, 125, 92), "battery": (70, 110, 200), "spring": (150, 150, 160),
       "sil": (247, 205, 214), "print": (226, 205, 160), "cav": (252, 250, 245), "wire": (215, 60, 60), "ink": (60, 40, 30)}


def inside_cavity(p):
    x, y, z = p
    in_pod = v3.pod_field(np.array([[x, y, z]], dtype=np.float32))[0] < -WALL
    in_neck = y < PASS["y1"] and abs(x) < PASS["x"] and PASS["z0"] < z < PASS["z1"] and y > PLATE_BACK - 4.6
    return bool(in_pod or in_neck)


def margin(box):
    """smallest distance from the box corners to the pod's inner wall (negative = pokes into the wall)."""
    x0, x1, y0, y1, z0, z1 = box
    m = 99.0
    for x in (x0, x1):
        for y in (y0, y1):
            for z in (z0, z1):
                if y < PASS["y1"]:
                    d = min(PASS["x"] - abs(x), z - PASS["z0"], PASS["z1"] - z)
                    d = max(d, -(v3.pod_field(np.array([[x, y, z]], dtype=np.float32))[0] + WALL))
                else:
                    d = -(v3.pod_field(np.array([[x, y, z]], dtype=np.float32))[0] + WALL)
                m = min(m, float(d))
    return m


def overlap(a, b):
    return all(a[i] < b[i + 1] and b[i] < a[i + 1] for i in (0, 2, 4))


if __name__ == "__main__":
    ok = True
    for n, b in PARTS.items():
        m = margin(b)
        size = (b[1] - b[0], b[3] - b[2], b[5] - b[4])
        print(f"{n:8s} {size[0]:4.1f} x {size[1]:4.1f} x {size[2]:4.1f} mm: clear of the pod wall by {m:4.1f} mm:", m >= 0.0)
        ok &= m >= 0.0
    names = list(PARTS)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            o = overlap(PARTS[a], PARTS[b])
            if o:
                print(f"!! {a} overlaps {b}")
            ok &= not o
    print(f"rod tip rests {ROD_TIP_REST - PLUNGER_TIP:.1f} mm behind the button plunger (travel {v3.TRAVEL} mm): clicks before the stop:", ROD_TIP_REST - PLUNGER_TIP + 0.25 < v3.TRAVEL)
    ok &= ROD_TIP_REST - PLUNGER_TIP + 0.25 < v3.TRAVEL
    print("ALL PARTS FIT" if ok else "CHECK FAILED")

    # ---------------- drawing ----------------
    SC = 22                                            # pixels per mm
    F = lambda s: ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", s)
    W, Hh = 2300, 1900
    img = Image.new("RGB", (W, Hh), (255, 255, 255))
    dr = ImageDraw.Draw(img)

    def field_img(plane, u0, u1, v0, v1):
        """sample the body and the frame on a plane. plane='side' (u = y, v = z at x = 0) or 'top' (u = y, v = x at z = AX)."""
        us = np.arange(u0, u1, 1 / SC * 2)
        vs = np.arange(v0, v1, 1 / SC * 2)
        U, V = np.meshgrid(us, vs, indexing="ij")
        if plane == "side":
            X, Y, Z = np.zeros_like(U), U, V
        else:
            X, Y, Z = V, U, np.full_like(U, AX - 1.7)
        P = np.stack([X, Y, Z], -1).astype(np.float32)
        body = body_field(X, Y, Z) < 0
        frame = v3.frame_field(P) < 0
        plate = (Y > PLATE_FRONT - 3) & (Y < PLATE_BACK) & body & (np.abs(X) < 20) & (np.abs(Z - 18.5) < 12) if plane == "side" else \
                (Y < PLATE_BACK) & body & (np.abs(X) < 20)
        pod_in = v3.pod_field(P) < -WALL
        neck = (Y < PASS["y1"]) & (Y > PLATE_BACK - 4.6) & (np.abs(X) < PASS["x"]) & (Z > PASS["z0"]) & (Z < PASS["z1"])
        neck_shell = (Y < PASS["y1"] + 1) & (Y > PLATE_BACK - 0.5) & (np.abs(X) < PASS["x"] + WALL) & (Z > PASS["z0"] - WALL) & (Z < PASS["z1"] + WALL)
        a = np.full(U.shape + (3,), 255, np.uint8)
        a[body] = COL["sil"]
        a[frame | plate | neck_shell] = COL["print"]
        a[pod_in | neck] = COL["cav"]
        bulk = (Y > BULKHEAD[0]) & (Y < BULKHEAD[1]) & (v3.pod_field(P) < 0)
        if plane == "side":
            bulk &= Z > 16.2                           # the board passes under the bulkhead
        a[bulk] = COL["print"]
        return a, us, vs

    def panel(plane, ox, oy, u0, u1, v0, v1, title):
        a, us, vs = field_img(plane, u0, u1, v0, v1)
        im = Image.fromarray(np.transpose(a, (1, 0, 2))[::-1]).resize((int((u1 - u0) * SC), int((v1 - v0) * SC)), Image.BILINEAR)
        img.paste(im, (ox, oy))
        px = lambda u: ox + (u - u0) * SC
        py = lambda v: oy + (v1 - v) * SC
        dr.text((ox, oy - 52), title, font=F(38), fill=(20, 20, 20))

        def rect(u_a, u_b, v_a, v_b, col, outline=(20, 20, 20), width=2):
            dr.rectangle([px(u_a), py(v_b), px(u_b), py(v_a)], fill=col, outline=outline, width=width)
        return px, py, rect

    def label(x, y, tx, ty, text, sub=None):
        dr.line([x, y, tx, ty], fill=(40, 40, 40), width=2)
        dr.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(40, 40, 40))
        dr.text((tx + 8, ty - 18), text, font=F(30), fill=(20, 20, 20))
        if sub:
            dr.text((tx + 8, ty + 18), sub, font=F(22), fill=(110, 110, 110))

    # ---- side view ----
    px, py, rect = panel("side", 60, 130, -58, -6, 2, 38, "옆에서 본 단면 (얼굴이 왼쪽)")
    b = PARTS["board"]; rect(b[2], b[3], b[4], b[4] + 1.2, COL["board"]); rect(b[2] - 1.0, b[2] + 6.5, b[4] + 1.2, b[5], (190, 190, 195))
    for k in range(3):
        rect(b[2] + 9 + k * 4, b[2] + 11.5 + k * 4, b[4] + 1.2, b[4] + 2.6, (60, 60, 60), width=1)
    b = PARTS["battery"]; rect(b[2], b[3], b[4], b[5], COL["battery"])
    b = PARTS["button"]; rect(b[2], b[3], b[4], b[5], COL["button"]); rect(b[3], PLUNGER_TIP, AX - 1.6, AX + 1.6, (90, 90, 96))
    for i in range(8):                                 # spring as a zigzag
        y0 = SPRING[0] + i * (SPRING[1] - SPRING[0]) / 8
        y1 = y0 + (SPRING[1] - SPRING[0]) / 8
        dr.line([px(y0), py(AX + (4 if i % 2 else -4)), px(y1), py(AX + (-4 if i % 2 else 4))], fill=COL["spring"], width=5)
    rect(SPRING[1], SPRING[1] + 1.6, AX - 4.4, AX + 4.4, COL["print"])
    wires = [((PARTS["button"][2], AX + 2), (-33, 21), (-33, 14.5), (-34, 13.4)), ((PARTS["button"][2], AX - 2), (-31.5, 17.0), (-31.5, 14.2), (-30, 13.4)),
             ((-39.0, 15.6), (-39.0, 14.4), (-37, 13.4)), ((-41.0, 15.6), (-41.0, 14.6), (-43, 13.4))]
    for wv in wires:
        dr.line([(px(u), py(v)) for u, v in wv], fill=COL["wire"], width=4, joint="curve")
    label(px(-27.2), py(AX + 2.5), px(-33), py(32.5), "택트 버튼 6×6", "딸깍 + 신호. 꼭지가 뒤(막대 쪽)를 향함")
    label(px(-40), py(23), px(-50), py(36.5), "배터리 (5×10×20급)", "얼굴판 바로 뒤에 세워서")
    label(px(-36), py(12.6), px(-44), py(4.2), "블루투스 보드 XIAO nRF52840", "21×17.5mm. 바닥에 눕힘. 충전 회로 내장")
    label(px(-46.6), py(14.3), px(-57.5), py(9.0), "USB-C", "얼굴판 뒤쪽 홈 안")
    label(px(-17), py(AX - 4), px(-24), py(8.5), "되돌림 스프링", "막대에 끼움. 캡슐 밖")
    label(px(-9), py(AX), px(-19), py(28.5), "막대", "뼈를 누르면 앞으로 3.5mm")
    label(px(-33.0), py(18.0), px(-35.5), py(8.5), "전선 4가닥", "버튼 2, 배터리 2")
    # ---- top view ----
    px, py, rect = panel("top", 60, 1020, -58, -6, -19, 19, "위에서 본 모습 (얼굴이 왼쪽)")
    b = PARTS["board"]; rect(b[2], b[3], b[0], b[1], COL["board"]); rect(b[2] - 1.0, b[2] + 6.5, -4.5, 4.5, (190, 190, 195))
    b = PARTS["battery"]; rect(b[2], b[3], b[0], b[1], COL["battery"])
    b = PARTS["button"]; rect(b[2], b[3], b[0], b[1], COL["button"]); rect(b[3], PLUNGER_TIP, -1.6, 1.6, (90, 90, 96))
    for i in range(8):
        y0 = SPRING[0] + i * (SPRING[1] - SPRING[0]) / 8
        y1 = y0 + (SPRING[1] - SPRING[0]) / 8
        dr.line([px(y0), py(4 if i % 2 else -4), px(y1), py(-4 if i % 2 else 4)], fill=COL["spring"], width=5)
    label(px(-33), py(-7.5), px(-24), py(-14.5), "보드 (맨 아래층)")
    label(px(-40), py(8), px(-36), py(17), "배터리 (보드 위)")
    label(px(-27.2), py(2), px(-21), py(12.5), "버튼 (막대와 같은 높이)")
    # ---- legend ----
    X0, y = 1330, 150
    dr.text((X0, y), "3D 프린팅이 아닌 부품", font=F(40), fill=(20, 20, 20)); y += 70
    rows = [(COL["button"], "택트 버튼", "딸깍 소리와 신호"), (COL["board"], "블루투스 보드", "무선 + 배터리 충전"),
            (COL["battery"], "배터리", "보드의 BAT 단자에 연결"), (COL["spring"], "스프링", "막대를 제자리로 되돌림"), (COL["wire"], "전선", "버튼 2가닥, 배터리 2가닥")]
    for c, a, bb in rows:
        dr.rectangle([X0, y, X0 + 46, y + 34], fill=c, outline=(20, 20, 20)); dr.text((X0 + 62, y - 4), a, font=F(30), fill=(20, 20, 20))
        dr.text((X0 + 330, y), bb, font=F(26), fill=(100, 100, 100)); y += 56
    y += 16
    dr.rectangle([X0, y, X0 + 46, y + 34], fill=COL["print"], outline=(20, 20, 20)); dr.text((X0 + 62, y - 4), "3D 프린팅 부품", font=F(30), fill=(20, 20, 20)); y += 56
    dr.rectangle([X0, y, X0 + 46, y + 34], fill=COL["sil"], outline=(20, 20, 20)); dr.text((X0 + 62, y - 4), "실리콘", font=F(30), fill=(20, 20, 20)); y += 90
    dr.text((X0, y), "배선", font=F(36), fill=(20, 20, 20)); y += 56
    for t in ["버튼 한쪽 다리 → 보드 D1", "버튼 다른 쪽 다리 → 보드 GND", "배터리 (+) → 보드 BAT+", "배터리 (-) → 보드 BAT-",
              "몸통 쪽으로 가는 전선은 없음"]:
        dr.text((X0, y), "- " + t, font=F(28), fill=(50, 50, 50)); y += 44
    y += 30
    dr.text((X0, y), "아직 정하지 않은 것", font=F(36), fill=(170, 40, 40)); y += 56
    for t in ["충전 방법: 지금은 얼굴 유닛을 빼서 USB-C 연결", "  (제품: 자석 단자, 또는 입 자리에 USB 구멍)",
              "배터리 용량과 사용 시간: 실제 부품으로 재야 함", "부품 치수: 구입한 부품으로 다시 확인"]:
        dr.text((X0, y), ("- " if not t.startswith("  ") else "") + t, font=F(27), fill=(70, 70, 70)); y += 42
    img.save(OUT)
    print("saved", OUT)
