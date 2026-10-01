"""Adds layout, groups and Note nodes to the server-converted Qwen Image 2.1 graph (node types/titles unchanged)."""
import json, pathlib
here = pathlib.Path(__file__).parent
g = json.loads((here / "_server_graph_qwen21.json").read_text())
nodes = {n["id"]: n for n in g["nodes"]}
def place(nid, x, y, w=320, h=110): nodes[nid]["pos"] = [x, y]; nodes[nid]["size"] = [w, h]
notes, groups, nid_ = [], [], [100]
def note(x, y, text, w=320, h=110):
    notes.append({"id": nid_[0], "type": "Note", "pos": [x, y], "size": [w, h], "flags": {}, "order": 0, "mode": 0,
                  "inputs": [], "outputs": [], "properties": {}, "widgets_values": [text], "color": "#432", "bgcolor": "#653"})
    nid_[0] += 1
def group(title, x, y, w, h, color):
    groups.append({"title": title, "bounding": [x, y, w, h], "color": color, "font_size": 24, "flags": {}})

group("0. 사용자 입력·설정 — 입력 이미지 / 배경 스타일", -20, -60, 720, 760, "#3f789e")
note(0, 0, "【비교용 Qwen Image 2.1 버전】\n제품까지 포함해 이미지 전체를 Qwen Image 2.1 편집 모델이 다시 생성합니다 (원본 재합성 없음).\n같은 입력·같은 스타일로 product-bg-swap-preserve-v1 과 결과를 비교하세요.\n외부 유료 API 노드 없음 (Comfy Cloud GPU에서 오픈 모델 실행).", 660, 170)
place(1, 0, 190, 320, 320)
note(340, 190, "[입력] 제품 사진 1장. 출력은 입력 비율을 유지하며 약 1024×1024 면적(32의 배수)으로 생성됨.", 320, 120)
place(4, 0, 530, 320, 90)
note(340, 530, "[배경 스타일] false = 밝은 스튜디오 / true = 차분한 라이프스타일 (v1과 동일한 의미)", 320, 110)

X = 780
group("1. 배경 교체 지시문 — 스타일별 편집 프롬프트 (제품 유지 문구 포함)", X - 20, -60, 820, 760, "#8A8")
place(53, X, 0, 400, 220); place(54, X, 240, 400, 220)
place(55, X + 440, 0, 300, 110)
note(X + 440, 140, "If/Else Switch: false → 위(스튜디오), true → 아래(라이프스타일).\n편집 모델이라 '배경만 바꾸고 제품은 그대로'라는 지시를 문장으로 줍니다. 강제력은 없으므로 로고·글자 변형 여부는 결과로 확인해야 함.", 300, 200)
note(X, 480, "프롬프트 직접 수정은 관리자용. v1(Flux Fill)과 같은 장면 묘사를 쓰도록 맞춤.", 400, 80)

X = 1660
group("2. Qwen Image 2.1 편집 생성 — 공식 템플릿(image_qwen_image_2_1_image_edit) 기본값 재현", X - 20, -60, 1160, 760, "#a1309b")
place(50, X, 0, 340, 90); place(57, X, 110, 340, 110); place(51, X, 240, 340, 110); place(52, X, 370, 340, 70)
place(56, X + 380, 0, 340, 200)
place(62, X + 760, 0, 340, 270)
note(X, 460, "모델: qwen_image_2.1_int8_convrot / 텍스트 인코더: qwen3vl_8b_int8_convrot / VAE: qwen_image_2.1_vae_bf16 (모두 Comfy Cloud 기존 보유).\nCLIPLoader type=qwen_image 는 추정값 — 실행 시 오류가 나면 이 값부터 확인.", 720, 140)
note(X + 760, 290, "seed 고정(20261001), 25 steps, cfg 1, euler/simple — 공식 템플릿 기본값. cfg 1이라 negative 프롬프트는 효과 없음.\n공식 템플릿의 프롬프트 확장(PE) 옵션은 생략.", 340, 170)

X = 2880
group("3. 결과 저장 — output/bg_swap_qwen21/result", X - 20, -60, 760, 500, "#444")
place(63, X, 0, 300, 60)
place(71, X + 340, 0, 380, 380)
note(X, 100, "result 하나만 저장 (제품이 재생성되므로 v1의 누끼·마스크 출력은 없음).", 300, 110)

g["nodes"] = list(nodes.values()) + notes
g["groups"] = groups
g["last_node_id"] = max(n["id"] for n in g["nodes"])
g["extra"]["ds"] = {"scale": 0.55, "offset": [40, 120]}
(here / "product_bg_swap_qwen21_v1.json").write_text(json.dumps(g, ensure_ascii=False, indent=1))
for n in g["nodes"]:
    x, y = n["pos"]; w, h = n["size"]
    ins = [gr for gr in groups if gr["bounding"][0] <= x and x + w <= gr["bounding"][0] + gr["bounding"][2]
           and gr["bounding"][1] + 30 <= y and y + h <= gr["bounding"][1] + gr["bounding"][3]]
    assert len(ins) == 1, (n["id"], n["type"])
print(json.dumps(g, ensure_ascii=False, separators=(",", ":")))
