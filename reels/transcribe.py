"""롱폼 영상 → 단어 단위 타임스탬프 대본 (transcript.json / transcript.txt).

faster-whisper로 받아쓰고, --script로 원본 대본을 주면 실제 발화를 기준으로
대본과 비슷한 부분만 대본 표기로 교정한다(즉흥 발화는 그대로 둔다).

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
    """실제 발화(받아쓰기)를 기준으로 하고, 대본과 비슷한 구간만 대본 표기로 교정한다.
    - 대본과 같거나 비슷한 부분: 대본 표기(오타·띄어쓰기 교정)
    - 촬영 때 즉흥으로 바꾼 말: 받아쓰기 그대로 (말하지 않은 대본 문장은 자막에 넣지 않음)
    각 단어의 eol=True는 대본의 줄 끝(문장 경계)에 해당한다는 표시."""
    script_words, eol = [], set()
    for line in script_text.splitlines():
        ws = line.split()
        if ws:
            script_words += ws
            eol.add(len(script_words) - 1)
    a = [norm(w["text"]) for w in asr]
    b = [norm(w) for w in script_words]
    out = []

    def take_script(i1, i2, j1, j2):
        t0, t1 = asr[i1]["start"], asr[i2 - 1]["end"]
        n = j2 - j1
        for k in range(n):
            out.append({"text": script_words[j1 + k], "start": round(t0 + (t1 - t0) * k / n, 3),
                        "end": round(t0 + (t1 - t0) * (k + 1) / n, 3), "src": "script",
                        "eol": (j1 + k) in eol})

    def take_asr(i1, i2):
        for w in asr[i1:i2]:
            out.append({**w, "src": "asr", "eol": False})

    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                out.append({**asr[i1 + k], "text": script_words[j1 + k], "src": "script",
                            "eol": (j1 + k) in eol})
        elif tag == "replace":
            sim = difflib.SequenceMatcher(None, "".join(a[i1:i2]), "".join(b[j1:j2])).ratio()
            take_script(i1, i2, j1, j2) if sim >= 0.6 else take_asr(i1, i2)
        elif tag == "delete":  # 대본에 없는 즉흥 발화
            take_asr(i1, i2)
        # insert(대본에만 있고 말하지 않음)는 버린다
    n_script = sum(w["src"] == "script" for w in out)
    print(f"  대본 표기로 교정된 단어 {n_script}/{len(out)} ({n_script / len(out):.0%}), 나머지는 실제 발화 그대로")
    return out


def to_sentences(words: list[dict]) -> list[dict]:
    """대본 줄 끝(eol) 또는 문장부호 기준으로 문장을 나눈다."""
    sents, cur = [], []
    for i, w in enumerate(words):
        cur.append(i)
        long_enough = len(cur) >= 4
        if w.get("eol") or (long_enough and SENTENCE_END.search(w["text"])) or len(cur) >= 30:
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
    sentences = to_sentences(words)
    data = {"video": str(args.video.resolve()), "words": words, "sentences": sentences}
    (args.out / "transcript.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    with open(args.out / "transcript.txt", "w", encoding="utf-8") as f:
        for s in sentences:
            f.write(f"[{s['id']:04d}] {fmt(s['start'])}-{fmt(s['end'])} {s['text']}\n")
    print(f"완료: {args.out/'transcript.json'} (문장 {len(sentences)}개)")


if __name__ == "__main__":
    main()
