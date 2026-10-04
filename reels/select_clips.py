"""transcript.json → clips.json. Claude(Opus 5.5)가 릴스로 쓸 구간을 고른다.

    python reels/select_clips.py work/transcript.json --style work/examples/style_notes.md

ANTHROPIC_API_KEY(또는 `ant auth login` 프로필)가 필요하다.
Claude Code 세션 안에서 돌릴 때는 이 스크립트 대신 세션의 Claude에게
prompts/select.md 기준으로 clips.json을 직접 작성해 달라고 해도 된다(형식 동일).
"""
import argparse
import json
from pathlib import Path

import anthropic

MODEL = "claude-opus-5-5"
PROMPT = Path(__file__).parent / "prompts" / "select.md"

SCHEMA = {
    "type": "object",
    "properties": {
        "clips": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "segments": {
                        "type": "array",
                        "items": {"type": "array", "items": {"type": "integer"}},
                    },
                    "hook_text": {"type": "string"},
                    "caption": {"type": "string"},
                    "scores": {
                        "type": "object",
                        "properties": {k: {"type": "integer"} for k in
                                       ["hook", "standalone", "emotion", "value", "payoff", "total"]},
                        "required": ["hook", "standalone", "emotion", "value", "payoff", "total"],
                        "additionalProperties": False,
                    },
                    "reason": {"type": "string"},
                },
                "required": ["title", "segments", "hook_text", "caption", "scores", "reason"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["clips"],
    "additionalProperties": False,
}


def resolve_times(clips: list[dict], sentences: list[dict]) -> list[dict]:
    """문장ID 구간을 실제 초 단위 구간으로 변환하고 길이를 계산한다."""
    by_id = {s["id"]: s for s in sentences}
    for c in clips:
        spans = []
        for a, b in c["segments"]:
            a, b = min(a, b), max(a, b)
            if a not in by_id or b not in by_id:
                raise ValueError(f"없는 문장ID: {c['title']} {a}-{b}")
            spans.append({"start": by_id[a]["start"], "end": by_id[b]["end"], "s0": a, "s1": b})
        c["spans"] = spans
        c["duration"] = round(sum(s["end"] - s["start"] for s in spans), 2)
    return clips


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("transcript", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--style", type=Path, help="예시 릴스 분석 메모(analyze_examples.py 결과)")
    ap.add_argument("--count", type=int, default=8)
    ap.add_argument("--min-sec", type=int, default=25)
    ap.add_argument("--max-sec", type=int, default=60)
    ap.add_argument("--effort", default="high", choices=["low", "medium", "high", "xhigh", "max"])
    args = ap.parse_args()
    out = args.out or args.transcript.with_name("clips.json")

    data = json.loads(args.transcript.read_text(encoding="utf-8"))
    txt = args.transcript.with_suffix(".txt").read_text(encoding="utf-8")
    style = args.style.read_text(encoding="utf-8") if args.style else "(없음)"
    prompt = PROMPT.read_text(encoding="utf-8").format(
        min_sec=args.min_sec, max_sec=args.max_sec, count=args.count,
        style_notes=style, transcript=txt,
    )

    client = anthropic.Anthropic()
    with client.beta.messages.stream(
        model=MODEL,
        max_tokens=64000,
        thinking={"type": "adaptive"},
        output_config={"effort": args.effort, "format": {"type": "json_schema", "schema": SCHEMA}},
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        msg = stream.get_final_message()

    if msg.stop_reason == "refusal":
        raise SystemExit(f"모델이 요청을 거절했습니다: {msg.stop_details}")
    if msg.stop_reason == "max_tokens":
        raise SystemExit("출력이 max_tokens에서 잘렸습니다. --count를 줄여 다시 시도하세요.")
    text = "".join(b.text for b in msg.content if b.type == "text")
    clips = json.loads(text)["clips"]
    clips = resolve_times(clips, data["sentences"])
    clips.sort(key=lambda c: -c["scores"]["total"])

    out.write_text(json.dumps({"clips": clips}, ensure_ascii=False, indent=1), encoding="utf-8")
    for i, c in enumerate(clips, 1):
        print(f"{i:2d}. [{c['scores']['total']:3d}점 {c['duration']:5.1f}s] {c['title']} — {c['hook_text']}")
    print(f"완료: {out}  (사용 토큰 in={msg.usage.input_tokens} out={msg.usage.output_tokens})")


if __name__ == "__main__":
    main()
