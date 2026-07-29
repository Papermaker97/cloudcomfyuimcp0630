# Seedance 2.0 립싱크 멀티씬 워크플로우

한 곡·한 캐릭터로 **여러 씬의 립싱크 영상**을 뽑기 위한 ComfyUI 워크플로우입니다.
공유 인풋(음원·캐릭터 시트·고정 프롬프트)은 그대로 두고, 씬마다 바뀌는 인풋
(음원 구간·키비주얼·가사·연출)만 갈아끼우는 구조입니다.

- 파일: [`lipsync_seedance2_multiscene.api.json`](./lipsync_seedance2_multiscene.api.json) (API 포맷)
- Comfy Cloud 저장본: `lipsync-seedance2-multi-scene.json`
  (workflow id `3ce3050d-41e3-45db-a008-ae7503bd3695`)
- 캔버스 / App Mode 링크: https://cloud.comfy.org/?share=7e9c9859ae9f

## 왜 이 노드인가

`ByteDance2ReferenceNode` (Seedance 2.0: Reference to Video) 하나가 필요한 걸 다 받습니다.

| 받는 것 | 슬롯 | 개수 |
| --- | --- | --- |
| 레퍼런스 이미지 | `model.reference_images.image_1..9` | 최대 9장 |
| 레퍼런스 오디오 | `model.reference_audios.audio_1..3` | 최대 3개 |
| 레퍼런스 비디오 | `model.reference_videos.video_1..3` | 최대 3개 |
| 프롬프트 | `model.prompt` | 1개 (STRING 링크 가능) |

즉 **캐릭터 시트 + 키비주얼을 이미지 레퍼런스로, 잘라낸 음원을 오디오 레퍼런스로**
한 노드에 물리고, 프롬프트는 텍스트 노드 3개를 이어붙여 넣습니다.

> 참고: `api_seedance2_0_r2v_real_human` 계열 템플릿과 `@asset_N` 프롬프트 문법,
> ByteDance 실명 인증(KYC)은 **쓰지 않습니다.** 일반 레퍼런스 이미지 경로만 사용합니다.

## 그래프 구조

```
LoadAudio(1)  ─ 전체 음원 (공유)
   └─ TrimAudioDuration(2)  ─ start_index / duration  ← 씬마다 구간 변경
        ├─ PreviewAudio(3)                            ← 크레딧 쓰기 전 컷 확인
        ├─ ByteDance2ReferenceNode(40).audio_1
        └─ AudioVideoCombine(60).audio

LoadImage(10)  ─ 캐릭터 시트 (공유) ──→ (40).image_1
LoadImage(11)  ─ 키비주얼 (씬별)   ──→ (40).image_2

PrimitiveStringMultiline(20)  [고정] 립싱크·아이덴티티 규칙 ┐
PrimitiveStringMultiline(21)  [씬별] 가사                  ├→ StringConcatenate(30) → (31) → (40).prompt
PrimitiveStringMultiline(22)  [씬별] 공간·연출·카메라       ┘

ByteDance2ReferenceNode(40) ─┬─→ SaveVideo(50)                      : 모델이 낸 오디오 트랙
                             └─→ AudioVideoCombine(60) → SaveVideo(61) : 원본 음원으로 갈아끼운 버전
```

출력이 두 개인 이유: 편집 타임라인에 얹을 때는 **원본 음원 그대로**가 들어간
`Output 2`가 안전합니다. 모델 생성 오디오(호흡·앰비언스 포함)를 쓰고 싶으면
`Output 1`을 쓰면 됩니다. 추가 API 비용은 없고 로컬 먹싱만 한 번 더 돕니다.

## 인풋 정리

### 공유 (한 번만 세팅)

| 노드 | 위젯 | 내용 |
| --- | --- | --- |
| 1 `LoadAudio` | `audio` | 곡 전체 파일 하나만 업로드 |
| 10 `LoadImage` | `image` | 얼굴 여러 각도가 들어간 캐릭터 시트 |
| 20 텍스트 | `value` | **고정 프롬프트** — 얼굴 고정 + 음원에 맞춘 자연스러운 립싱크 지시 |

### 씬마다 바꾸는 것

| 노드 | 위젯 | 내용 |
| --- | --- | --- |
| 2 `TrimAudioDuration` | `start_index` | 이 씬이 쓸 구간의 시작 초 (음수면 끝에서부터) |
| 2 `TrimAudioDuration` | `duration` | 구간 길이(초). 4–15 사이로 |
| 11 `LoadImage` | `image` | 그 씬의 키비주얼 (공간·배경·조명) |
| 21 텍스트 | `value` | 이 컷에서 부르는 가사 |
| 22 텍스트 | `value` | 공간·프레이밍·카메라·앵글·조명·액션 |
| 40 Seedance | `seed` | 같은 세팅으로 다른 테이크를 뽑을 때 |

### ⚠️ 길이는 두 군데를 맞춰야 합니다

`TrimAudioDuration.duration`(초, FLOAT)과 노드 40의 `model.duration`(초, INT 4–15)은
**따로 있는 값이라 자동으로 동기화되지 않습니다.** 8초 컷을 만들면 둘 다 8로 맞추세요.
`model.duration`은 Seedance 노드의 동적 콤보 하위 필드라 App Mode 인풋으로는 노출되지
않으니, 길이를 바꿀 때는 캔버스에서 직접 고치거나 아래 `input_overrides`로 넘기면 됩니다.

## 쓰는 법

### 1. App Mode (제일 간단)

https://cloud.comfy.org/?share=7e9c9859ae9f 를 열면 노드 그래프 없이
위 인풋 9개만 폼으로 보입니다. 파일 3개(음원·캐릭터 시트·키비주얼)를 올리고,
가사/연출 텍스트와 자를 구간만 바꿔가며 Run 하면 씬이 하나씩 나옵니다.

### 2. 캔버스에서 편집

같은 링크가 캔버스로도 열립니다. 해상도(`1080p`), 비율(`16:9`), 길이,
`generate_audio`, 레퍼런스 이미지 추가(최대 9장) 같은 건 여기서 조정하세요.

### 3. MCP로 씬 여러 개 한 번에

저장본을 그대로 돌리면서 씬별 값만 덮어씁니다.

```jsonc
// run_saved_workflow
{
  "filename": "lipsync-seedance2-multi-scene.json",
  "input_overrides": {
    "2":  { "start_index": 42.5, "duration": 9 },
    "11": { "image": "keyvisual_rooftop.png" },
    "21": { "value": "이 컷에서 부르는 가사..." },
    "22": { "value": "SCENE AND STAGING: 옥상, 블루아워, 로우앵글 푸시인..." },
    "40": { "model.duration": 9, "seed": 12345 }
  },
  "confirm": true
}
```

씬을 10개 한 번에 돌릴 거면 `submit_batch`에 `{"tool": "submit_workflow", "workflow": ...}`
아이템을 씬 수만큼 넣으면 됩니다 (한 번에 최대 50개). API 포맷 원본이
[`lipsync_seedance2_multiscene.api.json`](./lipsync_seedance2_multiscene.api.json)이니
이걸 복사해서 위 6개 값만 바꾸면 됩니다.

## 프롬프트 3분할이 이렇게 붙습니다

`StringConcatenate` 두 개가 `\n\n` 구분자로 이어붙여 최종 프롬프트를 만듭니다:

```
[고정] 립싱크 + 아이덴티티 + 품질 규칙
                ↓  \n\n
[씬별] 이 컷의 가사 + 창법 + 감정
                ↓  \n\n
[씬별] 공간 / 프레이밍 / 카메라 / 앵글 / 조명 / 액션 / 그레이딩
```

고정 프롬프트에는 이런 것들이 들어가 있습니다:

- **IDENTITY** — 캐릭터 시트가 아이덴티티의 유일한 기준, 리스타일·나이·헤어 변경 금지, 인물 1명 유지
- **LIP SYNC** — 음원 음소에 프레임 단위로 입모양·턱·혀 매칭, m/b/p 입술 완전 폐쇄,
  f/v 치순 접촉, 롱톤 모음 개구, 간주·쉼표 구간엔 입 정지 (없는 가사 립싱크 금지)
- **PERFORMANCE** — 호흡·헤드밥·눈썹·미세표정이 리듬과 감정을 따라감, 자연스러운 눈깜빡임
- **WORLD** — 로케이션·시간대·컬러그레이딩·조명 방향이 키비주얼과 일관되게
- **QUALITY** — 얼굴 모핑/아이덴티티 드리프트/손 왜곡/자막·텍스트·워터마크 금지

가사 프롬프트는 **화면에 자막을 넣으라는 게 아니라** 모델이 무슨 소리를 부르는지 알게 해서
입모양 정확도를 올리는 용도입니다. 그래서 고정 프롬프트에 `no subtitles`를 박아뒀습니다.

## 준비물 · 팁

- **캐릭터 시트**: 정면 / 3/4 / 측면이 한 장에 정리된 이미지가 가장 잘 먹습니다.
  얼굴이 화면에서 너무 작지 않게, 각 각도의 조명이 비슷하게.
- **키비주얼**: 인물이 없어도 됩니다. 공간·배경·조명·컬러 톤만 전달되면 충분하고,
  오히려 인물이 크게 들어가면 캐릭터 시트와 아이덴티티가 섞일 수 있습니다.
- **음원 컷**: 4–15초. 프레이즈 경계(숨 쉬는 지점)에서 자르면 립싱크가 훨씬 깔끔합니다.
  자르고 나서 `PreviewAudio`로 먼저 들어보고 돌리는 걸 권장합니다 — 여긴 크레딧이 안 듭니다.
- **모델 선택**: `Seedance 2.0`(품질) / `Seedance 2.0 Fast`(속도) / `Seedance 2.0 Mini`(최저가).
  씬 구도를 탐색할 때는 Mini + 480p로 돌려보고, 확정되면 같은 seed로 1080p 본 촬영하는 식이 쌉니다.
- `ByteDance2ReferenceNode`는 **유료 파트너 API 노드**라 실행할 때마다 크레딧이 나갑니다.

## 필요한 노드

전부 Comfy Cloud에 이미 있습니다.

- core: `LoadAudio`, `TrimAudioDuration`, `PreviewAudio`, `LoadImage`,
  `PrimitiveStringMultiline`, `StringConcatenate`, `ByteDance2ReferenceNode`, `SaveVideo`
- `audio-separation-nodes-comfyui`: `AudioVideoCombine` (Output 2 브랜치에서만 사용)
