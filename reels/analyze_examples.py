"""예시 릴스 분석: 길이·해상도·컷 빈도·음량 + 프레임 contact sheet.

    python reels/analyze_examples.py work/examples/*.mp4 --out work/examples/analysis

결과(report.json, *_sheet.jpg)를 보고 style.json(자막 위치/크기/색, 레이아웃)과
선정 프롬프트용 style_notes.md를 작성한다. Claude Code 세션이라면 Claude에게
"analysis 폴더 보고 style.json이랑 style_notes.md 맞춰줘"라고 하면 된다.
"""
import argparse
import json
import re
import subprocess
from pathlib import Path


def run(cmd: list[str]) -> str:
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.stdout + p.stderr


def info(path: Path) -> dict:
    out = run(["ffprobe", "-v", "error", "-show_entries",
               "format=duration:stream=codec_type,width,height,r_frame_rate", "-of", "json", str(path)])
    d = json.loads(out)
    v = next(s for s in d["streams"] if s["codec_type"] == "video")
    num, den = map(int, v["r_frame_rate"].split("/"))
    return {"duration": round(float(d["format"]["duration"]), 2),
            "width": v["width"], "height": v["height"], "fps": round(num / den, 2)}


def scene_cuts(path: Path, thresh: float = 0.3) -> list[float]:
    out = run(["ffmpeg", "-hide_banner", "-i", str(path), "-vf",
               f"select='gt(scene,{thresh})',showinfo", "-an", "-f", "null", "-"])
    return [round(float(t), 2) for t in re.findall(r"pts_time:([\d.]+)", out)]


def loudness(path: Path) -> float | None:
    out = run(["ffmpeg", "-hide_banner", "-i", str(path), "-af", "ebur128", "-f", "null", "-"])
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", out)
    return float(m[-1]) if m else None


def contact_sheet(path: Path, out: Path, dur: float, n: int = 12) -> None:
    step = max(dur / n, 0.5)
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(path), "-vf",
         f"fps=1/{step:.3f},scale=270:-2,tile=6x2:padding=6:color=white", "-frames:v", "1", str(out)])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("videos", type=Path, nargs="+")
    ap.add_argument("--out", type=Path, default=Path("work/examples/analysis"))
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    report = []
    for v in args.videos:
        d = info(v)
        cuts = scene_cuts(v)
        d.update(name=v.name, cuts=len(cuts), avg_shot_sec=round(d["duration"] / (len(cuts) + 1), 2),
                 cut_times=cuts, lufs=loudness(v))
        contact_sheet(v, args.out / f"{v.stem}_sheet.jpg", d["duration"])
        report.append(d)
        print(f"{v.name}: {d['duration']}s {d['width']}x{d['height']} 컷 {len(cuts)}회 "
              f"(평균 {d['avg_shot_sec']}s) {d['lufs']} LUFS")
    (args.out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"완료: {args.out}")


if __name__ == "__main__":
    main()
