"""clips.json → 9:16 릴스 mp4 (자르기 + 세로 변환 + 단어 강조 자막 + 후킹 문구).

    python reels/render.py work/transcript.json work/clips.json --out work/out
    python reels/render.py ... --only 1,3 --layout blur
"""
import argparse
import json
import re
import subprocess
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).parent
FONTS = ROOT / "fonts"


# ---------- 공통 ----------

def probe(video: str) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height", "-of", "json", video],
        capture_output=True, text=True, check=True,
    )
    return json.loads(out.stdout)["streams"][0]


def ass_color(rgb: str, alpha: str = "00") -> str:
    r, g, b = rgb[0:2], rgb[2:4], rgb[4:6]
    return f"&H{alpha}{b}{g}{r}".upper()


def ass_time(t: float) -> str:
    t = max(t, 0)
    cs = int(round(t * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def ass_escape(s: str) -> str:
    return s.replace("\\", "＼").replace("{", "(").replace("}", ")")


# ---------- 클립 구간 / 단어 시간 재배치 ----------

def build_spans(clip: dict, words: list[dict], sentences: list[dict], st: dict) -> list[dict]:
    """문장ID 구간 → 패딩 포함 원본 시간 구간 + 그 안의 단어 목록."""
    by_id = {s["id"]: s for s in sentences}
    spans = []
    for a, b in clip["segments"]:
        a, b = min(a, b), max(a, b)
        w0, w1 = by_id[a]["w0"], by_id[b]["w1"]
        start = max(0.0, words[w0]["start"] - st["pad_before"])
        end = words[w1]["end"] + st["pad_after"]
        if w1 + 1 < len(words):  # 다음 단어 소리가 섞이지 않게
            end = min(end, max(words[w1]["end"], words[w1 + 1]["start"] - 0.02))
        spans.append({"start": start, "end": end, "words": words[w0:w1 + 1]})
    return spans


def clip_words(spans: list[dict]) -> list[dict]:
    """원본 시간의 단어들을 이어붙인 클립 기준 시간으로 바꾼다."""
    out, offset = [], 0.0
    for sp in spans:
        for w in sp["words"]:
            out.append({"text": w["text"],
                        "start": offset + max(w["start"] - sp["start"], 0),
                        "end": offset + min(w["end"], sp["end"]) - sp["start"]})
        offset += sp["end"] - sp["start"]
    return out


# ---------- 자막 (ASS) ----------

def caption_lines(words: list[dict], max_chars: int) -> list[list[dict]]:
    lines, cur, n = [], [], 0
    for w in words:
        gap = w["start"] - cur[-1]["end"] if cur else 0
        ends_sentence = bool(cur) and re.search(r"[.?!…,]$", cur[-1]["text"])
        if cur and (n + len(w["text"]) > max_chars or gap > 0.7 or ends_sentence):
            lines.append(cur)
            cur, n = [], 0
        cur.append(w)
        n += len(w["text"]) + 1
    if cur:
        lines.append(cur)
    return lines


def write_ass(path: Path, words: list[dict], hook: str, duration: float, st: dict) -> None:
    c, h = st["caption"], st["hook"]
    W, H = st["width"], st["height"]
    hi = ass_color(c["highlight"])
    base = ass_color(c["color"])
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{c['font']},{c['size']},{base},{base},{ass_color(c['outline_color'])},&H80000000,0,0,0,0,100,100,0,0,1,{c['outline']},{c['shadow']},2,60,60,{c['bottom_margin']},1
Style: Hook,{h['font']},{h['size']},{ass_color(h['color'])},{ass_color(h['color'])},{ass_color(h['box_color'], '30')},{ass_color(h['box_color'], '30')},0,0,0,0,100,100,0,0,3,18,0,8,80,80,{h['top_margin']},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    if h["enabled"] and hook:
        end = h["seconds"] or duration
        ev.append(f"Dialogue: 1,{ass_time(0)},{ass_time(end)},Hook,,0,0,0,,{ass_escape(hook)}")

    for line in caption_lines(words, c["max_chars"]):
        for i, w in enumerate(line):
            t0 = line[0]["start"] if i == 0 else w["start"]
            t1 = line[i + 1]["start"] if i + 1 < len(line) else w["end"] + 0.15
            parts = []
            for j, x in enumerate(line):
                t = ass_escape(x["text"])
                if j == i:
                    pop = r"\t(0,80,\fscx112\fscy112)\t(80,160,\fscx100\fscy100)" if c["pop"] else ""
                    parts.append(f"{{\\c{hi}{pop}}}{t}{{\\c{base}}}")
                else:
                    parts.append(t)
            ev.append(f"Dialogue: 0,{ass_time(t0)},{ass_time(t1)},Cap,,0,0,0,,{' '.join(parts)}")
    path.write_text(header + "\n".join(ev) + "\n", encoding="utf-8")


# ---------- 얼굴 추적 크롭 ----------

def face_track(video: str, spans: list[dict], src_w: int, src_h: int, crop_w: int,
               step: float = 0.25) -> list[tuple[float, float]]:
    """클립 시간 기준 (t, crop_x) 키프레임. 얼굴이 크게 움직일 때만 카메라를 옮긴다."""
    det = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    cap = cv2.VideoCapture(video)
    scale = 480 / src_w
    ts, xs, offset = [], [], 0.0
    for sp in spans:
        t = sp["start"]
        while t < sp["end"]:
            cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
            ok, frame = cap.read()
            cx = None
            if ok:
                small = cv2.resize(frame, None, fx=scale, fy=scale)
                gray = cv2.equalizeHist(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY))
                faces = det.detectMultiScale(gray, 1.1, 5, minSize=(int(30), int(30)))
                if len(faces):
                    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
                    cx = (x + w / 2) / scale
            ts.append(offset + t - sp["start"])
            xs.append(cx)
            t += step
        offset += sp["end"] - sp["start"]
    cap.release()

    found = [x for x in xs if x is not None]
    if not found:
        return [(0.0, (src_w - crop_w) / 2)]
    last = found[0]
    filled = []
    for x in xs:
        last = x if x is not None else last
        filled.append(last)
    k = 7  # 중앙값 필터로 튀는 검출 제거
    pad = np.pad(np.array(filled), k // 2, mode="edge")
    smooth = [float(np.median(pad[i:i + k])) for i in range(len(filled))]

    dead = crop_w * 0.18
    clamp = lambda cx: float(min(max(cx - crop_w / 2, 0), src_w - crop_w))
    cam = smooth[0]
    keys = [(0.0, clamp(cam))]
    for t, x in zip(ts, smooth):
        if abs(x - cam) > dead:
            keys.append((t, clamp(cam)))
            cam = x
            keys.append((t + 0.4, clamp(cam)))  # 0.4초 동안 부드럽게 이동
    return keys


def x_expr(keys: list[tuple[float, float]]) -> str:
    if len(keys) == 1:
        return f"{keys[0][1]:.1f}"
    expr = f"{keys[-1][1]:.1f}"
    for (t0, x0), (t1, x1) in reversed(list(zip(keys, keys[1:]))):
        seg = f"{x0:.1f}" if t1 <= t0 or x0 == x1 else f"{x0:.1f}+({x1 - x0:.1f})*(t-{t0:.2f})/{t1 - t0:.2f}"
        expr = f"if(lt(t,{t1:.2f}),{seg},{expr})"
    return f"if(lt(t,{keys[0][0]:.2f}),{keys[0][1]:.1f},{expr})"


# ---------- 렌더 ----------

def render(video: str, spans: list[dict], ass: Path, out: Path, st: dict, layout: str) -> None:
    src = probe(video)
    sw, sh = int(src["width"]), int(src["height"])
    W, H = st["width"], st["height"]
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-stats"]
    parts = []
    for i, sp in enumerate(spans):
        d = sp["end"] - sp["start"]
        cmd += ["-ss", f"{sp['start']:.3f}", "-t", f"{d:.3f}", "-i", video]
        fo = max(d - 0.03, 0)
        parts.append(f"[{i}:v]setpts=PTS-STARTPTS,fps={st['fps']},format=yuv420p[v{i}];"
                     f"[{i}:a]asetpts=PTS-STARTPTS,aresample=48000,"
                     f"afade=t=in:d=0.02,afade=t=out:st={fo:.3f}:d=0.03[a{i}]")
    n = len(spans)
    fg = ";".join(parts) + ";" + "".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[cv][ca]"

    crop_w = int(sh * 9 / 16) // 2 * 2
    if layout in ("face", "center") and crop_w < sw:
        if layout == "face":
            keys = face_track(video, spans, sw, sh, crop_w)
            x = x_expr(keys)
        else:
            x = f"{(sw - crop_w) / 2:.1f}"
        fg += f";[cv]crop={crop_w}:{sh}:'{x}':0,scale={W}:{H}:flags=lanczos,setsar=1[fr]"
    elif layout == "letterbox":
        fg += (f";[cv]scale={W}:-2:flags=lanczos,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black,setsar=1[fr]")
    else:  # blur: 흐린 배경 + 가운데 원본
        fg += (f";[cv]split[b][f];[b]scale={W}:{H}:force_original_aspect_ratio=increase,"
               f"crop={W}:{H},boxblur=30:3,eq=brightness=-0.15[bg];"
               f"[f]scale={W}:-2:flags=lanczos[fgv];[bg][fgv]overlay=(W-w)/2:(H-h)/2,setsar=1[fr]")

    fontsdir = f":fontsdir={FONTS.as_posix()}" if FONTS.exists() else ""
    fg += f";[fr]subtitles=filename={ass.as_posix()}{fontsdir}[vout]"
    fg += ";[ca]loudnorm=I=-14:TP=-1.5:LRA=11[aout]" if st["audio"]["loudnorm"] else ";[ca]anull[aout]"

    cmd += ["-filter_complex", fg, "-map", "[vout]", "-map", "[aout]",
            "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", str(out)]
    subprocess.run(cmd, check=True)


def slug(s: str) -> str:
    return re.sub(r"[^\w가-힣]+", "_", s).strip("_")[:30]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("transcript", type=Path)
    ap.add_argument("clips", type=Path)
    ap.add_argument("--out", type=Path, default=Path("work/out"))
    ap.add_argument("--style", type=Path, default=ROOT / "style.json")
    ap.add_argument("--layout", choices=["face", "center", "blur", "letterbox"])
    ap.add_argument("--only", help="렌더할 클립 번호(1부터), 예: 1,3")
    args = ap.parse_args()

    st = json.loads(args.style.read_text(encoding="utf-8"))
    layout = args.layout or st["layout"]
    tr = json.loads(args.transcript.read_text(encoding="utf-8"))
    clips = json.loads(args.clips.read_text(encoding="utf-8"))["clips"]
    only = {int(x) for x in args.only.split(",")} if args.only else None
    args.out.mkdir(parents=True, exist_ok=True)

    for i, clip in enumerate(clips, 1):
        if only and i not in only:
            continue
        name = f"{i:02d}_{slug(clip['title'])}"
        spans = build_spans(clip, tr["words"], tr["sentences"], st)
        words = clip_words(spans)
        dur = sum(s["end"] - s["start"] for s in spans)
        ass = args.out / f"{name}.ass"
        write_ass(ass, words, clip.get("hook_text", ""), dur, st)
        print(f"[{i}/{len(clips)}] {name} ({dur:.1f}s, 구간 {len(spans)}개, {layout})")
        render(tr["video"], spans, ass, args.out / f"{name}.mp4", st, layout)
        (args.out / f"{name}.txt").write_text(clip.get("caption", ""), encoding="utf-8")
    print(f"완료: {args.out}")


if __name__ == "__main__":
    main()
