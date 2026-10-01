"""Adds layout, groups and Note nodes to the server-converted graph (node types/titles unchanged)."""
import json, pathlib
here = pathlib.Path(__file__).parent
g = json.loads((here / "_server_graph_v1.json").read_text())
nodes = {n["id"]: n for n in g["nodes"]}

def place(nid, x, y, w=300, h=110):
    nodes[nid]["pos"] = [x, y]; nodes[nid]["size"] = [w, h]

notes = []
next_id = [100]
def note(x, y, text, w=330, h=110):
    nid = next_id[0]; next_id[0] += 1
    notes.append({"id": nid, "type": "Note", "pos": [x, y], "size": [w, h], "flags": {}, "order": 0,
                  "mode": 0, "inputs": [], "outputs": [], "properties": {}, "widgets_values": [text],
                  "color": "#432", "bgcolor": "#653"})

groups = []
def group(title, x, y, w, h, color):
    groups.append({"title": title, "bounding": [x, y, w, h], "color": color, "font_size": 24, "flags": {}})

# ---------- 0. 사용자 입력 / 설정 ----------
X0, Y0 = 0, 0
group("0. 사용자 입력·설정 — 여기 값만 바꾸세요 (입력 이미지 / 배경 스타일 / 제품 크기·위치 / 마스크 정도)",
      X0 - 20, Y0 - 60, 720, 1700, "#3f789e")
note(X0, Y0, "【사용 방법】\n1) 아래 LoadImage에 제품 사진 1장 업로드\n2) 배경 스타일·크기·위치·마스크 값을 조절\n3) 실행 → output/bg_swap/ 에 result, product_cutout, product_mask 저장\n\n제품 픽셀은 생성 모델이 다시 그리지 않고 원본에서 그대로 합성됩니다.\n외부 유료 API 노드 없음 (Comfy Cloud GPU에서 오픈 모델로 실행).", 660, 190)
place(1, X0, Y0 + 210, 320, 320)
note(X0 + 340, Y0 + 210, "[입력] 제품 사진 (불투명·외곽이 뚜렷한 단일 제품 1개). 유리·보석·강한 반사체는 v1 지원 범위 밖.", 320, 120)
place(2, X0, Y0 + 550, 320, 320)
note(X0 + 340, Y0 + 550, "[수동 마스크 (선택)] 흰색=제품, 검정=배경인 PNG. 반드시 제품 사진과 같은 해상도.\n사용하지 않을 때도 유효한 파일이 필요 → 제품 사진을 그대로 지정해 두면 됨 (아래 스위치가 false면 파일 존재 검사만 통과하면 되고 결과에는 쓰이지 않음).", 320, 160)
rows = [
    (3, "[수동 마스크 사용] false = BiRefNet 자동 마스크 / true = 위 수동 마스크 사용 (자동 마스크가 틀렸을 때)"),
    (4, "[배경 스타일] false = 밝은 스튜디오 / true = 차분한 라이프스타일"),
    (5, "[제품 크기] 캔버스 대비 제품이 차지할 최대 비율 (0.3~0.85 권장, 기본 0.6). 원본보다 커지면 업스케일되어 화질이 떨어질 수 있음."),
    (6, "[가로 위치] 0 = 왼쪽 끝, 0.5 = 중앙, 1 = 오른쪽 끝"),
    (7, "[세로 위치] 0 = 위, 0.5 = 중앙, 1 = 아래 (바닥에 놓인 느낌은 0.6~0.75)"),
    (8, "[마스크 확장/축소 px] 음수 = 외곽을 안쪽으로 줄임(배경 테두리 잔상 제거), 양수 = 넓힘(제품 가장자리 잘림 보정). 보통 -2~2"),
    (9, "[마스크 외곽 부드러움] 합성 경계 블러 반경. 0 = 딱딱한 경계, 1~2 권장, 크게 하면 외곽이 번짐"),
]
y = Y0 + 890
for nid, txt in rows:
    place(nid, X0, y, 320, 90); note(X0 + 340, y, txt, 320, 90); y += 110

# ---------- 1. 제품 분리 ----------
X1 = 800
group("1. 제품 분리 — BiRefNet-HR-matting 자동 마스크 ↔ 수동 마스크 스위치 → 마스크 정도 적용", X1 - 20, -60, 1100, 700, "#8A8")
place(20, X1, 0, 320, 260)
place(21, X1 + 360, 0, 260, 110)
place(22, X1 + 660, 0, 320, 300)
place(23, X1 + 360, 340, 260, 60)
place(24, X1 + 660, 340, 320, 60)
place(25, X1 + 660, 430, 320, 60)
note(X1, 300, "If/Else Switch: false → BiRefNet MASK, true → Load Image (as Mask).\nGrow Mask With Blur: fill_holes=true (로고 안쪽 구멍 메움), expand/blur는 왼쪽 설정값 연결.\nInvert Mask → Join Image with Alpha: ComfyUI의 alpha 입력은 반전 규약이라 한 번 뒤집어 투명 누끼 PNG를 만듦.", 330, 220)

# ---------- 2. 제품 배치 ----------
X2 = 2000
group("2. 제품 배치 — 마스크 bbox로 제품만 잘라 크기 맞춤 → 1024×1024 캔버스의 지정 위치에 원본 픽셀 배치", X2 - 20, -60, 1700, 1000, "#b58b2a")
place(10, X2, 0, 260, 90); place(11, X2, 110, 260, 90)
note(X2, 220, "캔버스 가로/세로 (고정값 1024×1024, 16의 배수 유지). 사용자 조절 항목 아님.", 260, 100)
place(30, X2 + 300, 0, 300, 160)
place(31, X2 + 300, 200, 300, 120); place(32, X2 + 300, 340, 300, 120)
place(33, X2 + 640, 200, 300, 120); place(34, X2 + 640, 340, 300, 120)
place(35, X2 + 980, 270, 300, 120)
note(X2 + 300, 490, "크기 계산: scale = min(캔버스W×크기비율 / bboxW, 캔버스H×크기비율 / bboxH)\n→ 제품이 캔버스 밖으로 나가지 않도록 가로·세로 중 작은 배율 사용.", 640, 100)
place(36, X2 + 640, 0, 300, 110)
place(37, X2 + 980, 0, 260, 60); place(38, X2 + 980, 90, 300, 110); place(39, X2 + 1320, 90, 300, 80)
place(40, X2 + 1320, 0, 260, 80)
place(41, X2 + 980, 430, 300, 120); place(42, X2 + 1320, 430, 300, 120)
place(43, X2 + 980, 570, 300, 120); place(44, X2 + 1320, 570, 300, 120)
note(X2 + 980, 710, "위치 계산: x = max(0, (캔버스W − 제품W) × 가로위치), y = max(0, (캔버스H − 제품H) × 세로위치)", 640, 80)
place(45, X2, 640, 260, 130); place(47, X2, 790, 260, 110)
place(46, X2 + 300, 640, 300, 140); place(48, X2 + 640, 640, 300, 140)
note(X2 + 300, 800, "Image Composite Masked: 회색 캔버스 위에 원본 제품 픽셀 배치.\nCombine Masks(add): 같은 위치의 제품 마스크 = 이후 '보호 영역'.", 640, 100)

# ---------- 3. 배경 생성 ----------
X3 = 3800
group("3. 배경 생성 — Flux.1 Fill (OneReward) 인페인트: 제품 바깥 영역만 생성, 제품 영역은 노이즈를 넣지 않음", X3 - 20, -60, 1800, 1000, "#a1309b")
place(50, X3, 0, 340, 90); place(51, X3, 110, 340, 130); place(52, X3, 260, 340, 70)
place(53, X3, 360, 380, 200); place(54, X3, 580, 380, 200)
note(X3, 800, "위: 밝은 스튜디오 프롬프트 / 아래: 차분한 라이프스타일 프롬프트.\n스타일 선택은 0번 그룹의 [배경 스타일] Boolean 으로 함 (프롬프트 직접 수정은 관리자용).", 380, 110)
place(55, X3 + 420, 360, 260, 110)
place(56, X3 + 420, 0, 300, 90); place(57, X3 + 760, 0, 260, 70); place(58, X3 + 760, 100, 260, 60)
place(59, X3 + 420, 520, 260, 70); place(60, X3 + 420, 620, 260, 60)
note(X3 + 420, 700, "Threshold Mask → Invert Mask: 제품=0, 배경=1 인 인페인트 마스크.\nInpaintModelConditioning(noise_mask=true): 생성은 배경 영역에서만. 제품 픽셀은 문맥으로만 보여 줘서 접지 그림자·조명이 자연스럽게 맞도록 함.", 600, 140)
place(61, X3 + 1060, 0, 300, 140)
place(62, X3 + 1060, 180, 300, 270)
note(X3 + 1060, 470, "seed 고정(20261001, fixed): 같은 입력·설정이면 같은 배경이 재현됨.\n24 steps / cfg 1 / guidance 30 / euler·normal — 기존 inpainting-pixel-exact-onereward-fill 설정 재사용.", 300, 160)
place(63, X3 + 1400, 0, 260, 60)
place(64, X3 + 1400, 100, 300, 300)

# ---------- 4. 원본 합성 ----------
X4 = 5700
group("4. 원본 제품 재합성 — 생성된 배경 위에 원본 제품 픽셀을 마스크로 다시 덮음 (로고·글자 보존)", X4 - 20, -60, 420, 420, "#b06634")
place(70, X4, 0, 340, 140)
note(X4, 170, "destination = 생성된 배경, source = 배치된 원본 제품, mask = 배치 마스크(외곽 블러 포함).\n생성 모델이 제품 영역을 바꿨더라도 여기서 원본으로 되돌림.", 340, 140)

# ---------- 5. 저장 ----------
X5 = 6200
group("5. 결과 저장 — output/bg_swap/ (result · product_cutout · product_mask)", X5 - 20, -60, 760, 820, "#444")
place(71, X5, 0, 340, 360)
place(26, X5 + 380, 0, 340, 340)
place(27, X5 + 380, 380, 340, 340)
note(X5, 380, "result: 최종 배경 교체 이미지 (1024×1024)\nproduct_cutout: 원본 해상도 투명 PNG 누끼\nproduct_mask: 원본 해상도 흑백 마스크 (흰=제품). 수동 수정 후 0번 그룹 수동 마스크로 다시 넣을 수 있음.", 340, 160)

g["nodes"] = list(nodes.values()) + notes
g["groups"] = groups
g["last_node_id"] = max(n["id"] for n in g["nodes"])
g["extra"]["ds"] = {"scale": 0.45, "offset": [40, 120]}
(here / "product_bg_swap_v1.json").write_text(json.dumps(g, ensure_ascii=False, indent=1))
print(len(g["nodes"]), "nodes,", len(groups), "groups,", len(notes), "notes")
