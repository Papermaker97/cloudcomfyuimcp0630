# 롱폼 → 릴스 자동화

편집된 롱폼 영상 + 대본(+ 예시 릴스)으로 9:16 릴스를 여러 개 뽑는 파이프라인.

```
long.mp4 + script.txt
  └─ transcribe.py      faster-whisper 단어 타임스탬프 → 대본 텍스트로 교정 (transcript.json/.txt)
  └─ select_clips.py    Claude Opus 5.5가 훅·단독이해·감정·정보·마무리로 채점해 구간 선정 (clips.json)
  └─ render.py          자르기/점프컷 → 9:16 (얼굴추적·블러·레터박스) → 단어 강조 자막 + 후킹 문구 → mp4
examples/*.mp4
  └─ analyze_examples.py  길이·컷 빈도·음량·프레임 시트 → style.json / style_notes.md 조정에 사용
```

## 설치

```bash
./reels/setup.sh          # pip 의존성 + Pretendard 폰트(reels/fonts)
```
ffmpeg는 libass 포함 빌드가 필요하다. 받아쓰기는 GPU(CUDA)가 있으면 훨씬 빠르다.

## 사용

```bash
mkdir -p work/examples && cp 롱폼.mp4 work/long.mp4 && cp 대본.txt work/script.txt && cp 예시*.mp4 work/examples/

# 0) 예시 릴스 분석 (선택)
python reels/analyze_examples.py work/examples/*.mp4

# 1) 받아쓰기 + 대본 정렬   (CPU면 --model small 또는 medium)
python reels/transcribe.py work/long.mp4 --script work/script.txt --out work

# 2) 구간 선정 (ANTHROPIC_API_KEY 필요)
python reels/select_clips.py work/transcript.json --style work/examples/style_notes.md

# 3) 렌더
python reels/render.py work/transcript.json work/clips.json --out work/out
python reels/render.py work/transcript.json work/clips.json --only 2 --layout blur   # 한 개만 다시
```

결과: `work/out/NN_제목.mp4` + 게시글 본문 `NN_제목.txt` + 자막 `NN_제목.ass`.

## clips.json 형식 (손으로 고치거나 Claude Code 세션에서 직접 작성 가능)

```json
{"clips": [{
  "title": "편집시간 줄이는 법",
  "segments": [[12, 12], [3, 7]],      // transcript.txt의 문장ID 구간, 재생 순서대로 (점프컷)
  "hook_text": "편집 시간 90% 줄이는 법",
  "caption": "인스타 본문 #해시태그"
}]}
```

## 스타일 (style.json)

| 키 | 설명 |
|---|---|
| `layout` | `face` 얼굴추적 크롭 · `center` 중앙 크롭 · `blur` 흐린배경+원본 · `letterbox` 검은배경+원본 |
| `caption.*` | 폰트, 크기, 색(`highlight`=현재 단어), 한 줄 글자수, 아래 여백, 팝 효과 |
| `hook.*` | 상단 후킹 문구 (`seconds`: null이면 끝까지 표시) |
| `pad_before/after` | 문장 앞뒤 여유(초) |

## 메모
- 대본을 주면 자막은 대본 텍스트를 쓴다(받아쓰기 오타 없음). 대본에 있지만 영상에서 잘린 문장은 시간이 보간되며 `unaligned: true`로 표시된다.
- 선정 모델은 `claude-opus-5-5`, adaptive thinking, effort `high`, 거절 시 서버 측 폴백(`fallbacks: "default"`) 사용.
