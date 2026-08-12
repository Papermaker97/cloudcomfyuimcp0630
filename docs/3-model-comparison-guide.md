# 3-모델 영상 비교 워크플로우

이미지 4장 + **대충 쓴 프롬프트 하나**를 넣으면, 모델별 프롬프트 재작성기를 거쳐
Seedance / MiniMax H3(오픈웨이트) / FLUX 3 세 개를 같은 조건으로 돌립니다.

| 파일 | 재작성기 | 성격 |
|---|---|---|
| `workflows/ksampler_3model_compare_v2.json` | `OpenRouter LLM` | API 호출. 이미지 4장 개별 입력, system_prompt 필드 있음 |
| `workflows/ksampler_3model_compare_v3_local_vlm.json` | `QwenVL (Advanced)` | **완전 로컬.** 외부 API 호출 없음 |

영상 모델 3개와 시스템 프롬프트는 두 파일이 완전히 동일합니다. 재작성기 열만 다릅니다.

```bash
python3 tools/build_workflows.py   # 시스템 프롬프트 수정 후 두 파일 동기화
```

## 0. Seedance 2.5 — 쓸 수 있게 됐습니다

올려주신 파일을 보니 `ByteDance2ReferenceNode`에 `Seedance 2.5` 옵션이 생겼습니다
(프론트엔드 1.49.3, 위젯이 11개 → 13개로 늘어남). 제가 조회한 카탈로그는 아직 2.0까지만
보여서 v1에서 2.0으로 내렸던 건데, 손봐주신 값 그대로 **2.5로 유지**했습니다.

다만 모델 위젯을 바꾸면 프론트엔드가 duration을 노드 기본값으로 되돌립니다. 올려주신
파일에서 **5초로 리셋되어 있어서 10초로 되돌렸습니다** (세 모델 비교 조건을 맞추려고).
`tools/build_workflows.py`가 매번 세 개의 duration을 10초로 고정합니다.

2.5에서 늘어난 위젯 2개(BOOLEAN 하나 + `mp4` COMBO 하나)는 제 카탈로그에 스펙이 없어서
**손대지 않고 저장하신 값 그대로 뒀습니다.**

---

## 1. 원본 파일에서 고친 것

### 1.1 MiniMax H3 — API 노드 → 오픈웨이트 노드

원본은 `MinimaxHailuo03ReferenceNode`(`partner/video/MiniMax`, API 과금)를 쓰고 있었습니다.
오픈소스 경로는 별도 노드로 존재합니다:

| | 원본 (잘못됨) | 현재 |
|---|---|---|
| 노드 | `MinimaxHailuo03ReferenceNode` | `MiniMaxH3ReferenceToVideo` |
| 카테고리 | `partner/video/MiniMax` | `model/conditioning/minimax` |
| 성격 | API 호출 | 로컬 가중치 |
| 출력 | `VIDEO` 완제품 | `CONDITIONING` + `LATENT` |
| 레퍼런스 표기 | `Image 1` | `<Picture 1>` |

오픈웨이트는 완성된 영상을 뱉지 않고 컨디셔닝과 latent를 뱉기 때문에, 샘플링 체인을
직접 붙여야 합니다. v2에는 공식 `video_minimax_h3_r2v` 템플릿과 동일한 구성이 들어가
있습니다:

```
UNETLoader  ─┬─→ BasicScheduler ─→┐
             └─→ BasicGuider ────→│
CLIPLoader ──→┐                   ├→ SamplerCustomAdvanced ─→ VAEDecode ──────┐
VAELoader ×2 →┤ MiniMaxH3          │                       └→ VAEDecodeAudio ─┤
LoadImage ×4 →┤ ReferenceToVideo ─→┘                                          │
              └─→ (CONDITIONING, LATENT)                     CreateVideo ←────┘
                                                                  ↓
                                                              SaveVideo
```

모델은 첫 실행 때 [Comfy-Org/MiniMax-H3](https://huggingface.co/Comfy-Org/MiniMax-H3)에서
자동 다운로드됩니다.

```
ComfyUI/models/
  diffusion_models/minimax_h3_ref2va_pruned_int8_convrot.safetensors
  text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors
  vae/minimax_h3_video_vae_fp16.safetensors
  vae/minimax_h3_audio_vae_fp32.safetensors
```

### 1.2 FLUX 3 키프레임 슬롯 인덱스

`Flux3ImageToVideoNode`의 auto-grow 슬롯은 **0부터** 시작합니다
(`keyframes.image_0`, `keyframes.image_1`, ...). 원본은 `image_1`~`image_4`로 되어 있어
한 칸씩 밀려 있었습니다. 공식 `api_bfl_flux3_i2v` 템플릿에서 확인했습니다.

참고로 같은 파일 안에서도 규칙이 다릅니다:

| 노드 | 슬롯 이름 | 시작 |
|---|---|---|
| `ByteDance2ReferenceNode` | `model.reference_images.image_N` | 1 |
| `Flux3ImageToVideoNode` | `keyframes.image_N` | **0** |
| `MiniMaxH3ReferenceToVideo` | `ref_images.ref_image_N` | **0** |
| `OpenRouterLLMNode` | `model.images.image_N` | 1 |

### 1.3 위젯 값 누락

`ByteDance2ReferenceNode`와 `Flux3ImageToVideoNode` 모두 seed 뒤의
`control_after_generate` 위젯이 빠져 있어서 위젯 배열이 한 칸 짧았습니다.

---

## 1.5. 로컬 재작성기 (v3) — Qwen3-VL

`ksampler_3model_compare_v3_local_vlm.json`. OpenRouter 노드 3개를
`QwenVL (Advanced)`(`ComfyUI-QwenVL` 팩) 3개로 교체했습니다. 외부 API 호출이 없습니다.

```
LoadImage ×4 ─→ Draw Text Overlay ×4 ("REF 1"~"REF 4") ─→ Batch Images ─┐
                                                                        │ video
SYSTEM PROMPT ─┐                                                        ↓
               ├→ Concatenate Text ─→ custom_prompt ─→ QwenVL (Advanced) ─┬→ Preview as Text
ROUGH PROMPT ──┘                                                          └→ 영상 모델
```

노드 소스를 직접 읽고 맞춘 부분이 세 군데 있습니다.

**① 이미지 배치는 `image`가 아니라 `video`로 들어가야 합니다.**
`AILab_QwenVL.py`의 `image` 처리는 `tensor_to_pil(image)`인데, 이 함수는 4D 텐서를 받으면
`tensor[0]`만 씁니다. 배치 4장을 `image`에 물리면 **3장이 조용히 버려집니다.**
`video`는 `for frame in video`로 전부 순회합니다. `frame_count`는 배치가 그보다 클 때만
서브샘플링하므로 기본값 16이면 4장이 그대로 통과합니다.

**② system_prompt 필드가 없습니다.**
이 노드의 대화는 `[{"role": "user", ...}]` 한 턴뿐입니다. system 역할 자체가 없어서
`Concatenate Text`로 시스템 프롬프트 + 러프 프롬프트를 합쳐 `custom_prompt`에 넣습니다.
`custom_prompt`는 비어있지 않으면 `preset_prompt`를 완전히 대체합니다.

**③ `keep_model_loaded`를 껐습니다.**
`QwenVLBase.__init__`이 `self.model`을 **인스턴스마다** 들고 있습니다. 노드가 3개니까
켜두면 모델이 3벌 상주합니다. 끄면 로드→실행→언로드를 3번 반복 — 느리지만 안 터집니다.

### 캡션을 굽는 이유

Qwen은 레퍼런스 4장을 "영상 프레임"으로 봅니다. "두 번째 것"을 지목할 근거가 필요해서
`Draw Text Overlay`로 `REF 1`~`REF 4`를 구워 넣습니다. **VLM이 보는 사본에만** 들어가고
영상 모델은 원본을 그대로 받습니다. 시스템 프롬프트 3개 모두에 "이 캡션은 파이프라인
라벨이니 묘사하지 말고 결과물에 넣지 말 것"이라고 못박아 뒀습니다.

캡션이 싫으면 CAPTION 노드들을 Ctrl+B 하세요 — 바이패스된 TextOverlay는 이미지를 그대로
통과시킵니다.

### 튜닝 값

| 위젯 | 값 | 이유 |
|---|---|---|
| `model_name` | `Qwen3-VL-8B-Instruct` | FP16 ~12GB. 첫 실행 시 `models/LLM/Qwen-VL`로 다운로드 |
| `max_tokens` | 4096 | H3 6섹션 브리프가 800~1000토큰 나옴 |
| `temperature` | 0.3 | 구조화 출력이라 낮게 |
| `repetition_penalty` | **1.05** | 노드 기본값 1.2는 `<Subject 1>`처럼 **일부러 반복하는** H3 라벨을 방해합니다 |
| `frame_count` | 16 | 4장이라 서브샘플링 안 걸림 |

`quantization`은 `None (FP16)` 하나뿐입니다 — 이 환경에 bitsandbytes가 없어서 8bit/4bit
선택지가 안 뜹니다.

### 솔직한 한계

**세 개 중 H3 브리프가 제일 어렵습니다.** `subject_definitions:` ~ `non_diegetic_music:`
6섹션에 `fully_preserved` 같은 고정 마커까지 맞춰야 하는데, 8B는 섹션을 빠뜨리거나
마커를 지어내는 경우가 있습니다. Preview as Text에서 형식이 무너지면:

- `Qwen3-VL-32B-Instruct`로 올리세요 (FP16 ~28GB). 형식 준수가 확실히 안정적입니다.
- VRAM이 부족하면 `Qwen3-VL-4B-Instruct` (~6GB). 대신 형식은 더 흔들립니다.

**중간 선택지도 있습니다.** OpenRouter 노드를 그대로 두고 모델 위젯만
`qwen/qwen3.6-plus`나 `z-ai/glm-5`, `deepseek/deepseek-v4-pro`로 바꾸면 — **오픈웨이트
모델이면서** 이미지 4장 개별 입력과 system_prompt 필드를 그대로 씁니다. OpenAI에서만
벗어나면 되는 거라면 이게 위젯 하나 바꾸는 걸로 끝나고 품질도 제일 낫습니다.
완전 로컬이어야 한다면 v3입니다.

**`Batch Images`는 첫 이미지 크기로 리사이즈합니다** (`batch_images()`가 나머지를
`common_upscale(..., "center")`로 맞춤). VLM이 보는 그림만 잘리고, 영상 모델은 원본
해상도를 그대로 받습니다.

---

## 2. 프롬프트 재작성기

첨부해주신 스크린샷 구조 그대로입니다. 다만 시스템 프롬프트를 커스텀 노드(Comfyroll) 대신
코어 `PrimitiveStringMultiline` 노드에 넣어서 의존성을 없앴습니다.

```
ROUGH PROMPT ─┐
              ├→ OpenRouter LLM ─┬→ Preview as Text  (무엇을 시켰는지 확인)
LoadImage ×4 ─┘   + SYSTEM PROMPT└→ 영상 모델의 prompt 입력
```

세 벌이 각각 돌아가고, **레퍼런스 이미지 4장이 LLM에도 함께 들어갑니다.** 그래서
재작성기가 "Image 1은 배경 빼고 형태만" 같은 역할 배정을 추측이 아니라 실제로 그림을 보고
씁니다.

기본 모델은 `openai/gpt-5.6-sol` / `reasoning_effort: low`(스크린샷과 동일). 세 개 다 같은
모델이라 비교 결과가 재작성기 차이가 아니라 시스템 프롬프트 차이에서 나옵니다.

### 시스템 프롬프트 원본

편집 가능한 마크다운으로 따로 두고, 빌드할 때 워크플로우 JSON에 인라인됩니다.

| 파일 | 근거 |
|---|---|
| `workflows/system_prompts/seedance20_rewriter.md` | 첨부해주신 Seedance 2.5 통합 가이드 (바이트댄스 공식 提示词指南 요약 + EvoLink 라이브러리) |
| `workflows/system_prompts/minimax_h3_rewriter.md` | MiniMax H3-Context-IR 구조 (`subject_definitions:` … `non_diegetic_music:` 6-섹션 브리프) |
| `workflows/system_prompts/flux3_rewriter.md` | Black Forest Labs 공식 스킬 `flux-3-cinematic-inserts` / `flux-3-keyframes-continuation` / `flux-3-audio-dialogue` / `flux-3-prompt-doctor` |

수정 후에는 다시 빌드하세요 — v2와 v3 양쪽에 반영됩니다:

```bash
python3 tools/build_workflows.py
```

### 세 모델이 원하는 프롬프트가 실제로 다릅니다

**Seedance — 촬영 대본**

```
Y2K Korean toy commercial. The handheld device rotates against a blue gradient,
slow push-in, 50mm.

@Image1 defines the device's shape, material and color. Do NOT take its background.
@Image2 defines the exploded-parts layout only. Do NOT take its color grade.

[00:00-00:03] ...  End state: device centered, screen facing lens.
[00:03-00:06] ...  lens switch
[00:08-00:10] Closing — held logo card on white.

Consistency: same face, same hairstyle, same outfit, same body type throughout.
Audio: bright upbeat synth jingle; crisp plastic clicks as parts lock.
Negative: no subtitles, no background music, no gibberish text, no watermark.
```

**MiniMax H3 — 6섹션 구조 브리프**

```
subject_definitions:
<Subject 1> is the handheld electronic device whose shape and glossy shell come from <Picture 1>.
...
summary:
[reference generation] ...
retention_analysis:
<Subject 1> (appears in [Shot 1], [Shot 2]): fully_preserved - ...
detailed_description:
The target video is in a vintage Korean TV-commercial style ...
[Shot 1] ... [Shot 2] At 00:03.000, the shot cuts to ...
<Subject 3> (S1) says, <d>[Korean] 신난다!</d>
overall_soundscape:
...
non_diegetic_music:
...
```

**FLUX 3 — 흐르는 산문**

```
The device holds center frame and begins a slow clockwise rotation as light sweeps
across its shell; the camera pushes in and holds. HARD CUT. The panel separates into
floating modules that drift apart and lock back together with three sharp plastic
clicks. ... Audio in layers: a bright synth jingle leads, plastic clicks sit on each
lock, one airy whoosh per transition. No on-screen text, no subtitles.
```

---

## 3. 결과를 비교할 때 알아야 할 것

### 3.1 세 모델은 이미지를 같은 방식으로 쓰지 않습니다

- **Seedance / MiniMax H3** — 이미지는 **레퍼런스**입니다. 정체성·재질·스타일을 참고해
  모델이 새로 그립니다.
- **FLUX 3** — 이미지는 **키프레임**입니다. 그 픽셀이 0초 / 3초 / 6초 / 8초에 화면에 그대로
  나옵니다.

즉 "프롬프트 해석력과 모션"은 공정하게 비교되지만, "소스 이미지 보존"은 애초에 다른 종목
입니다. FLUX 3이 알아서 배치하게 하려면 `placement` 위젯을 `spread across the clip`으로
바꾸세요. 대신 `placement.times`는 시리얼라이즈에서 빠집니다.

BFL 공식 스킬 표현으로는 — 중간 핀은 제안이 아니라 **마감 시한**입니다. 4장을 다 핀으로
박으면 모션이 뻣뻣해질 수 있습니다.

### 3.2 해상도가 동일하지 않습니다

API 두 개는 720p, 로컬 H3는 기본 864×480(0.4 MP)입니다. 243프레임을 로컬에서 돌리는
비용 때문에 낮춰뒀습니다. **Resolution Selector의 megapixels를 0.9로 올리면 1280×736**이
되어 720p와 맞습니다. 시간은 그만큼 더 듭니다.

| MP | 16:9 출력 (multiple=32) |
|---|---|
| 0.4 | 864 × 480 ← 기본값 |
| 0.5 | 960 × 544 |
| 0.7 | 1152 × 640 |
| 0.9 | 1280 × 736 ← 720p 대응 |
| 2.0 | 1920 × 1088 |

### 3.3 길이

셋 다 10초입니다. H3의 `length`는 24fps 기준 **프레임 수**이고 `17k + 5` 격자에 떨어져야
합니다. Math Expression 노드가 처리합니다:

```
max(5, round(a * 24)) + (5 - (max(5, round(a * 24)) % 17)) % 17
```

10초 → 243프레임 (= 17×14 + 5). 학습 구간은 대략 124~362프레임이므로 5~15초 사이에서
Duration 노드만 바꾸면 됩니다.

### 3.4 비용

v2는 한 번 실행에 LLM API 3회 + 파트너 API 2회 + 로컬 GPU 1회입니다.
v3는 LLM 호출이 로컬 GPU 3회로 바뀝니다 (API 비용 0, 대신 모델 로드 3회). 프롬프트만 다듬는
단계에서는 세 영상 그룹을 전부 Ctrl+B로 바이패스하고 재작성기와 Preview as Text만 돌려서
확인하세요. 훨씬 쌉니다.

---

## 4. 사용법

1. LoadImage 4개에 이미지를 넣습니다 (연결 순서 = 참조 번호).
2. **ROUGH PROMPT**에 아이디어를 대충 씁니다. 한국어로 써도 됩니다.
3. 실행합니다.
4. **Preview as Text** 3개에서 각 모델이 실제로 무엇을 지시받았는지 읽습니다.
5. 마음에 안 들면 영상 그룹을 바이패스한 채로 시스템 프롬프트만 고쳐가며 반복합니다.

한 모델만 돌리려면 나머지 두 그룹을 Ctrl+G 헤더에서 Ctrl+B로 바이패스하세요.

---

## 5. 출처

- 첨부: `SEEDANCE 2.5 프롬프트 통합 가이드` (바이트댄스 공식 提示词指南 요약, EvoLink,
  K-SAMPLER, PJ Ace, @onofumi_AI 실측)
- [Black Forest Labs 공식 스킬 저장소](https://github.com/black-forest-labs/skills) —
  `flux-3-cinematic-inserts`, `flux-3-keyframes-continuation`, `flux-3-audio-dialogue`,
  `flux-3-prompt-doctor`
- [FLUX Prompting Guide — Black Forest Labs](https://docs.bfl.ml/guides/prompting_summary)
- [MiniMax H3 — MiniMax 공식 블로그](https://www.minimax.io/blog/minimax-h3)
- [MiniMaxAI/MiniMax-H3 · VIDEO_PROMPT_WRITING_GUIDE](https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/docs/VIDEO_PROMPT_WRITING_GUIDE_ref_en.md)
- [MiniMax H3 Prompting Guide — fal](https://fal.ai/learn/devs/minimax-h3-prompting-guide)
- [MiniMax H3 Prompt Guide — RunDiffusion](https://www.rundiffusion.com/minimax-h3-prompt-guide)
- ComfyUI 공식 템플릿: `video_minimax_h3_r2v`, `api_seedance2_0_r2v`, `api_bfl_flux3_i2v`
