#!/usr/bin/env python3
# ============================================================
# 고스트컷 자동 생성 — 로컬 브릿지 서버
# ------------------------------------------------------------
# 브라우저(index.html)는 API 키를 가질 수 없습니다. 프론트엔드에 키를 넣으면
# 누구나 볼 수 있고, 브라우저 보안 정책(CORS) 때문에 외부 API를 직접 부르지도 못합니다.
# 그래서 이 서버가 중간에서 대신 호출합니다.
#
# 실행:  python3 server.py
#        (별도 설치 없이 macOS 기본 python3로 동작합니다)
#
# 그다음 index.html 의 LIVE 를 true 로 바꾸고 브라우저에서 새로고침하세요.
# ============================================================

import json
import os
import time
import uuid
import urllib.request
import urllib.error
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

# ------------------------------------------------------------
# 설정 — 여기만 본인 환경에 맞게 바꾸면 됩니다
# ------------------------------------------------------------
PORT = 8787

# ComfyUI 서버 주소.
#   - 로컬 ComfyUI를 띄웠다면: http://127.0.0.1:8188
#   - 다른 곳에 띄웠다면 그 주소
COMFY_HOST = os.environ.get("COMFY_HOST", "http://127.0.0.1:8188")

# 인증이 필요한 경우 헤더에 넣을 API 키. 필요 없으면 빈 문자열로 둡니다.
COMFY_API_KEY = os.environ.get("COMFY_API_KEY", "")

# 결과 이미지를 저장할 폴더
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "out")

# 워크플로우 파일 (API 포맷)
WORKFLOW = os.path.join(os.path.dirname(os.path.abspath(__file__)), "workflow.api.json")


# ------------------------------------------------------------
# 워크플로우 로드 & 값 채우기
# ------------------------------------------------------------
def build_workflow(image_name, item_en, background):
    """워크플로우 JSON을 읽어서 이번 요청에 맞는 값으로 바꿔 돌려줍니다."""
    with open(WORKFLOW, encoding="utf-8") as f:
        wf = json.load(f)

    # 1번 노드(LoadImage)에 업로드된 파일명을 넣습니다.
    wf["1"]["inputs"]["image"] = image_name

    # 7번 노드(생성)의 프롬프트에서 아이템 종류만 바꿉니다.
    # 원본 프롬프트가 "the SAME top shown in" 형태라, top 자리를 교체합니다.
    prompt = wf["7"]["inputs"]["prompt"]
    wf["7"]["inputs"]["prompt"] = prompt.replace("the SAME top ", f"the SAME {item_en} ")

    # 매번 다른 결과가 나오도록 seed를 바꿉니다.
    wf["7"]["inputs"]["seed"] = int(time.time() * 1000) % 2147483647

    # 8번 노드(배경 제거)의 출력 방식을 바꿉니다.
    wf["8"]["inputs"]["background"] = "Alpha" if background == "alpha" else "Color"
    if background != "alpha":
        wf["8"]["inputs"]["background_color"] = "#FFFFFF"

    return wf


# ------------------------------------------------------------
# ComfyUI 호출 (표준 ComfyUI HTTP API 기준)
# ------------------------------------------------------------
def _headers(extra=None):
    h = dict(extra or {})
    if COMFY_API_KEY:
        h["Authorization"] = f"Bearer {COMFY_API_KEY}"
    return h


def upload_image(raw_bytes, filename):
    """이미지를 ComfyUI input 폴더로 올리고, 저장된 파일명을 돌려줍니다."""
    boundary = "----ghostcut" + uuid.uuid4().hex
    body = b""
    body += f"--{boundary}\r\n".encode()
    body += f'Content-Disposition: form-data; name="image"; filename="{filename}"\r\n'.encode()
    body += b"Content-Type: application/octet-stream\r\n\r\n"
    body += raw_bytes + b"\r\n"
    body += f"--{boundary}\r\n".encode()
    body += b'Content-Disposition: form-data; name="overwrite"\r\n\r\ntrue\r\n'
    body += f"--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        COMFY_HOST + "/upload/image",
        data=body,
        headers=_headers({"Content-Type": f"multipart/form-data; boundary={boundary}"}),
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())["name"]


def submit(wf):
    """워크플로우를 큐에 넣고 prompt_id를 돌려줍니다."""
    payload = json.dumps({"prompt": wf}).encode()
    req = urllib.request.Request(
        COMFY_HOST + "/prompt",
        data=payload,
        headers=_headers({"Content-Type": "application/json"}),
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())["prompt_id"]


def wait_and_fetch(prompt_id, timeout_sec=300):
    """작업이 끝날 때까지 기다렸다가 결과 이미지 바이트를 돌려줍니다."""
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        req = urllib.request.Request(
            f"{COMFY_HOST}/history/{prompt_id}", headers=_headers()
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            hist = json.loads(r.read())

        if prompt_id in hist:
            outputs = hist[prompt_id].get("outputs", {})
            # 10번 노드(SaveImage)의 결과를 찾습니다. 없으면 아무 이미지나 집습니다.
            for node_id in ["10"] + list(outputs.keys()):
                imgs = outputs.get(node_id, {}).get("images")
                if imgs:
                    info = imgs[0]
                    q = urllib.parse.urlencode({
                        "filename": info["filename"],
                        "subfolder": info.get("subfolder", ""),
                        "type": info.get("type", "output"),
                    })
                    vreq = urllib.request.Request(
                        f"{COMFY_HOST}/view?{q}", headers=_headers()
                    )
                    with urllib.request.urlopen(vreq, timeout=120) as vr:
                        return vr.read()
            raise RuntimeError("작업은 끝났지만 결과 이미지를 찾지 못했습니다")
        time.sleep(1.5)
    raise TimeoutError("시간 초과 — ComfyUI가 응답하지 않습니다")


# ------------------------------------------------------------
# HTTP 핸들러
# ------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        # 결과 이미지 서빙
        if self.path.startswith("/out/"):
            name = os.path.basename(self.path[5:])
            path = os.path.join(OUT_DIR, name)
            if os.path.exists(path):
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self._cors()
                self.end_headers()
                with open(path, "rb") as f:
                    self.wfile.write(f.read())
                return
        self.send_response(404)
        self._cors()
        self.end_headers()

    def do_POST(self):
        if self.path != "/generate":
            self.send_response(404)
            self._cors()
            self.end_headers()
            return

        try:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length)
            fields = parse_multipart(raw, self.headers.get("Content-Type", ""))

            img_bytes = fields["image"]["data"]
            img_name = fields["image"]["filename"] or "input.png"
            item_en = fields.get("item", {}).get("value", "top")
            background = fields.get("background", {}).get("value", "alpha")

            print(f"[생성] {img_name}  아이템={item_en}  배경={background}")

            uploaded = upload_image(img_bytes, img_name)
            wf = build_workflow(uploaded, item_en, background)
            prompt_id = submit(wf)
            result = wait_and_fetch(prompt_id)

            os.makedirs(OUT_DIR, exist_ok=True)
            out_name = f"{uuid.uuid4().hex}.png"
            with open(os.path.join(OUT_DIR, out_name), "wb") as f:
                f.write(result)

            self._json(200, {"url": f"http://127.0.0.1:{PORT}/out/{out_name}"})
            print(f"[완료] {out_name}")

        except Exception as e:
            print(f"[실패] {e}")
            self._json(200, {"error": str(e)})

    def _json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass  # 기본 접속 로그는 끕니다


def parse_multipart(raw, content_type):
    """multipart/form-data 를 아주 단순하게 파싱합니다 (이 툴 용도에 한정)."""
    if "boundary=" not in content_type:
        return {}
    boundary = content_type.split("boundary=")[1].strip().strip('"').encode()
    parts = raw.split(b"--" + boundary)
    out = {}
    for p in parts:
        if b"Content-Disposition" not in p:
            continue
        head, _, data = p.partition(b"\r\n\r\n")
        data = data.rstrip(b"\r\n")
        head_s = head.decode("utf-8", "ignore")
        name = None
        filename = None
        for token in head_s.split(";"):
            token = token.strip()
            if token.startswith('name="'):
                name = token[6:].split('"')[0]
            elif token.startswith('filename="'):
                filename = token[10:].split('"')[0]
        if not name:
            continue
        if filename is not None:
            out[name] = {"data": data, "filename": filename}
        else:
            out[name] = {"value": data.decode("utf-8", "ignore").strip()}
    return out


if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    print("=" * 52)
    print("  고스트컷 브릿지 서버")
    print(f"  포트      : {PORT}")
    print(f"  ComfyUI   : {COMFY_HOST}")
    print(f"  API 키    : {'설정됨' if COMFY_API_KEY else '없음'}")
    print("=" * 52)
    print("  index.html 의 LIVE 를 true 로 바꾼 뒤 브라우저를 새로고침하세요.")
    print("  종료하려면 Ctrl+C")
    print()
    HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
