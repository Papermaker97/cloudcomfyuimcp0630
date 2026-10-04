"""롱폼 영상 → 단어 단위 타임스탬프 대본 (transcript.json / transcript.txt).

faster-whisper로 받아쓰고, --script로 원본 대본을 주면 받아쓰기 결과의 시간 정보에
대본 텍스트를 덮어씌워 오타 없는 자막을 만든다.

    python reels/transcribe.py work/long.mp4 --script work/script.txt --out work/
"""
import argparse
import difflib
import json
import re
import subprocess
from pathlib import Path

SENTENCE_END = re.compile(r"[.?!…。？！]$|[다요죠까네]\.?$")


def norm(word: str) -> str:
    return re.sub(r"[^\w]", "", word).lower()


def extract_audio(video: Path, wav: Path) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(video),
         "-vn", "-ac", "1", "-ar", "16000", str(wav)],
        check=True,
    )


def whisper_words(wav: Path, model_name: str, lang: str, prompt: str | None) -> list[dict]:
    from faster_whisper import WhisperModel

    model = WhisperModel(model_name, device="auto", compute_type="auto")
    segments, _ = model.transcribe(
        str(wav), language=lang, word_timestamps=True, vad_filter=True,
        initial_prompt=prompt, condition_on_previous_text=False,
    )
    words = []
    for seg in segments:
        for w in seg.words or []:
            text = w.word.strip()
            if text:
                words.append({"text": text, "start": round(w.start, 3), "end": round(w.end, 3)})
        print(f"\r  transcribed {seg.end:7.1f}s", end="", flush=True)
    print()
    return words


def align_script(asr: list[dict], script_text: str) -> list[dict]:
    """대본 단어마다 받아쓰기 단어의 시간을 붙인다. 매칭 안 된 단어는 앞뒤 사이를 보간."""
    script_words = script_text.split()
    a = [norm(w["text"]) for w in asr]
    b = [norm(w) for w in script_words]
    out = [{"text": w, "start": None, "end": None, "matched": False} for w in script_words]

    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                out[j1 + k].update(start=asr[i1 + k]["start"], end=asr[i1 + k]["end"], matched=True)
        elif tag == "replace" and i2 > i1:
            # 띄어쓰기/오인식 차이: 해당 구간 시간을 대본 단어 수로 나눠 배분
            t0, t1 = asr[i1]["start"], asr[i2 - 1]["end"]
            n = j2 - j1
            for k in range(n):
                out[j1 + k].update(start=t0 + (t1 - t0) * k / n, end=t0 + (t1 - t0) * (k + 1) / n)

    # 남은 빈칸(영상에서 잘린 대본 등)은 이웃 단어 시간 사이로 보간
    known = [i for i, w in enumerate(out) if w["start"] is not None]
    if not known:
        raise SystemExit("대본과 받아쓰기가 전혀 매칭되지 않았습니다. 영상/대본이 맞는지 확인하세요.")
    for i, w in enumerate(out):
        if w["start"] is not None:
            continue
        prev = max((k for k in known if k < i), default=None)
        nxt = min((k for k in known if k > i), default=None)
        t0 = out[prev]["end"] if prev is not None else out[nxt]["start"]
        t1 = out[nxt]["start"] if nxt is not None else t0
        w["start"] = w["end"] = t0 + (t1 - t0) / 2
        w["unaligned"] = True
    for w in out:
        w["start"], w["end"] = round(w["start"], 3), round(w["end"], 3)
    ratio = sum(w["matched"] for w in out) / len(out)
    print(f"  대본 정렬: 정확히 일치한 단어 {ratio:.0%}")
    return out


def to_sentences(words: list[dict], script_text: str | None) -> list[dict]:
    """대본 줄바꿈 또는 문장부호 기준으로 문장을 나눈다."""
    breaks = set()
    if script_text:
        idx = 0
        for line in script_text.splitlines():
            n = len(line.split())
            if n:
                idx += n
                breaks.add(idx - 1)
    sents, cur = [], []
    for i, w in enumerate(words):
        cur.append(i)
        long_enough = len(cur) >= 4
        if i in breaks or (long_enough and SENTENCE_END.search(w["text"])) or len(cur) >= 30:
            sents.append(cur)
            cur = []
    if cur:
        sents.append(cur)
    return [
        {"id": n, "start": words[ids[0]]["start"], "end": words[ids[-1]]["end"],
         "w0": ids[0], "w1": ids[-1], "text": " ".join(words[i]["text"] for i in ids)}
        for n, ids in enumerate(sents)
    ]


def fmt(t: float) -> str:
    return f"{int(t // 60):02d}:{t % 60:05.2f}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("video", type=Path)
    ap.add_argument("--script", type=Path, help="원본 대본(txt). 있으면 자막 텍스트를 대본으로 교정")
    ap.add_argument("--out", type=Path, default=Path("work"))
    ap.add_argument("--model", default="large-v3-turbo", help="GPU 없으면 small/medium 권장")
    ap.add_argument("--lang", default="ko")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    script_text = args.script.read_text(encoding="utf-8") if args.script else None
    wav = args.out / "audio.wav"
    print("1) 오디오 추출")
    extract_audio(args.video, wav)
    print(f"2) 받아쓰기 ({args.model})")
    asr = whisper_words(wav, args.model, args.lang, script_text[:400] if script_text else None)
    (args.out / "asr_raw.json").write_text(json.dumps(asr, ensure_ascii=False), encoding="utf-8")

    words = align_script(asr, script_text) if script_text else asr
    sentences = to_sentences(words, script_text)
    data = {"video": str(args.video.resolve()), "words": words, "sentences": sentences}
    (args.out / "transcript.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    with open(args.out / "transcript.txt", "w", encoding="utf-8") as f:
        for s in sentences:
            f.write(f"[{s['id']:04d}] {fmt(s['start'])}-{fmt(s['end'])} {s['text']}\n")
    print(f"완료: {args.out/'transcript.json'} (문장 {len(sentences)}개)")


if __name__ == "__main__":
    main()
