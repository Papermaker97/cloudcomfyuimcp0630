# ComfyUI 인페인팅 워크플로우

Comfy Cloud에서 실행 검증을 마친 마스크 기반 인페인팅 워크플로우입니다.

| 워크플로우 | 모델 | 출시 | 스텝 | 캔버스 |
| --- | --- | --- | --- | --- |
| [`flux2-klein-9b-inpaint.api.json`](./flux2-klein-9b-inpaint.api.json) **(권장)** | FLUX.2 Klein 9B distilled | 2026-01 | 8 | https://cloud.comfy.org/?share=65471d474dd2 |
| [`qwen-image-edit-2511-inpaint.api.json`](./qwen-image-edit-2511-inpaint.api.json) | Qwen-Image-Edit 2511 | 2025-11 | 20 | https://cloud.comfy.org/?share=4af4905c4ff3 |
| [`flux-fill-onereward-inpaint.api.json`](./flux-fill-onereward-inpaint.api.json) | Flux.1 Fill dev + OneReward | 2024-11 / 2025-08 | 24 | https://cloud.comfy.org/?share=09188b15cee1 |

## 실측 비교

동일 이미지·동일 마스크·동일 시드(875421903)로 실행한 결과를 육안 비교했습니다.

| | Klein 9B (8스텝) | Qwen-Image-Edit 2511 | Flux.1 Fill OneReward |
| --- | --- | --- | --- |
| 밀짚 짜임 | **땋은 결이 또렷하게 분리됨** | 선명하지만 다소 부드러움 | 평평하고 단조로움 |
| 리본 | 그로그랭 질감, 형태 깔끔 | 질감 + 리본 매듭까지 형성 | 단색 평면 밴드, 매듭 거의 없음 |
| 브림 디테일 | **미세한 타공 짜임까지 표현** | 보통 | 뭉개짐 |
| 마스크 경계 | 이음선 없음 | 이음선 없음 | 이음선 없음 |
| 종합 | **최상 + 가장 빠름** | 좋음, 프롬프트 반영 우수 | 보수적이고 밋밋함 |

시드 하나·이미지 하나짜리 비교라 벤치마크가 아니라 일화입니다. 다만 텍스처 밀도
차이는 뚜렷했습니다.

### Klein 품질 문제의 원인 — 스텝 수

초기 Klein 워크플로우가 형편없던 이유는 모델이 아니라 **스텝 수**였습니다.

`flux-2-klein-9b.safetensors`는 **distilled 변형**입니다 (undistilled는
`flux-2-klein-base-9b-fp8.safetensors`). Distilled 모델은 소수 스텝으로 증류
학습되었기 때문에 과샘플링하면 품질이 무너집니다. 카탈로그의 권장값
`steps 20`은 Flux.2 계열 일반값이라 distilled 변형에는 맞지 않습니다.

20 → 6~8스텝으로 내리자 세 워크플로우 중 최고 품질이 됐고, 실행 시간도 가장
짧습니다. Klein을 쓸 때 변형 이름을 먼저 확인해야 합니다:

| 파일명 | 종류 | 스텝 |
| --- | --- | --- |
| `flux-2-klein-9b` / `-4b` | distilled | 4~8 |
| `flux-2-klein-base-9b-fp8` / `-base-4b` | undistilled (base) | 20 |

## 설계 원칙 — 왜 이 배선인가

인페인팅이 편집 모델보다 나은 이유는 두 가지고, 이 워크플로우는 둘 다 구조로
보장합니다.

**1. 마스크 밖이 안 바뀌어야 한다.** 편집 모델(Nano Banana, GPT Image, Klein 등)은
"잘 유지"하는 것이지 보장하지 않는다. 이미지가 조금씩 달라진다.
→ `ImageCompositeMasked`로 **픽셀 공간에서** 합성한다. 마스크 밖은 원본 픽셀
그대로다.

**2. 작게 나오는 물체(가방, 제품)는 디테일이 떨어진다.** 전체 프레임을 그리면
마스크 영역에 할당되는 유효 해상도가 작다.
→ `InpaintCropImproved`로 마스크 주변만 1024px로 크롭해 생성하고
`InpaintStitchImproved`로 원본 해상도에 되돌린다.

**3. latent 마스크는 반드시 이진이어야 한다.** 페더링된 마스크를
`SetLatentNoiseMask`에 넣으면 latent 다운샘플 과정에서 경계에 부분 노이즈 밴드가
생기고, 마스크 주변이 지저분해진다.
→ `ThresholdMask(0.5)` → `GrowMask`로 **이진화 후 팽창**한 마스크만 모델에
넣는다. 페더링은 픽셀 합성 단계에서만 쓴다. 자세한 근거는 아래 경계 절 참고.

3번은 초기 Klein 워크플로우의 실제 버그였고, 아래 논문들이 다루는 주제다.
세 워크플로우 모두 이 세 원칙을 동일하게 적용했다.

## Klein 9B 워크플로우 구조 (권장)

```
LoadImage ─┬─ IMAGE ─┐
           └─ MASK  ─┤
                     ├─> InpaintCropImproved ─┬─> stitcher ──────────────────┐
                                              ├─> cropped_image ─> VAEEncode ─┬─> ReferenceLatent
                                              └─> cropped_mask ─> ThresholdMask ─> GrowMask ─┐
                                                                                             │
CLIPTextEncode ─> ReferenceLatent ─> FluxGuidance(4.0) ─> BasicGuider <── UNETLoader          │
                                                              │                              │
                                        SetLatentNoiseMask <──┼──────────────────────────────┘
                                                 │            │
                              SamplerCustomAdvanced(Flux2Scheduler 8스텝, euler)
                                                 └─> VAEDecode ─> ImageCompositeMasked
                                                                   (feathered mask, 픽셀 공간)
                                                                        └─> InpaintStitchImproved ─> SaveImage
```

`Flux2Scheduler`는 Flux.2 전용 해상도 인지 시그마 스케줄이다. `width`/`height`를
`InpaintCropImproved`의 `output_target`과 반드시 일치시켜야 한다.
`ReferenceLatent`로 원본 latent를 편집 레퍼런스로 넣는 것이 핵심 — Klein은 Fill
계열처럼 마스크 입력 채널이 없는 편집 모델이라, 이게 없으면 마스크 안이 주변과
어긋난다. Klein은 guidance-distilled이므로 `BasicGuider`로 충분하고 네거티브
프롬프트는 무시된다.

### 경계를 부드럽게 만드는 법 — latent가 아니라 픽셀에서

경계가 칼같이 잘려 어색하면 **latent 마스크를 흐리게 하지 말고** 두 값을 조정한다.

| 노드 | 값 | 역할 |
| --- | --- | --- |
| `GrowMask.expand` | 20 | 생성 영역을 마스크보다 넓게 준다. 모델이 자연스러운 실루엣을 배치할 여유가 생겨 내용물이 마스크 외곽선에 잘리지 않는다 |
| `InpaintCropImproved.mask_blend_pixels` | 48 | 픽셀 합성 페더링 폭. 시각적 전환을 여기서 담당한다 |

**latent 마스크를 블러하면 안 된다.** `GrowMaskWithBlur`로 blur_radius를 주고
`DifferentialDiffusion`을 켜서 테스트했더니, 경계 밴드에서 모델이 애매한 내용을
생성해 브림 외곽에 **톱니 같은 프린지 아티팩트**가 생겼다 (blur 16에서 심하고
blur 6에서도 잔존). 부드러움은 픽셀 합성에서만 만들어야 한다.

| 시도 | latent 마스크 | DD | 결과 |
| --- | --- | --- | --- |
| **채택** | 이진, 20px 팽창 | off | 외곽 매끄럽고 전환 자연스러움 |
| | 소프트, blur 6 | on | 브림에 미세 프린지 |
| | 소프트, blur 16 | on | 브림에 뚜렷한 톱니 돌출 |

### Klein 파라미터 조정

| 노드 | 값 | 조정 기준 |
| --- | --- | --- |
| `Flux2Scheduler.steps` | 8 | distilled는 4~8. **20으로 올리면 품질이 무너진다** |
| `FluxGuidance.guidance` | 4.0 | 커뮤니티 표준값. 프롬프트를 덜 따르면 5~6 |
| `Flux2Scheduler.width/height` | 1024 | `output_target`과 일치 필수 |
| `GrowMask.expand` | 20 | 내용물이 마스크 모양대로 잘려 보이면 더 키운다 |
| `InpaintCropImproved.mask_blend_pixels` | 48 | 경계가 티나면 64까지. 크롭이 업스케일된 경우 스티치 시 페더 폭이 좁아지므로 넉넉하게 |

## Qwen 2511 워크플로우 구조

```
LoadImage ─┬─ IMAGE ─┐
           └─ MASK  ─┤
                     ├─> InpaintCropImproved ─┬─> stitcher ─────────────────┐
                                              ├─> cropped_image ─┬─> VAEEncode ─┐
                                              │                  └─> TextEncodeQwenImageEditPlus (pos/neg)
                                              └─> cropped_mask ─┬─> ThresholdMask ─> GrowMask ─┐
                                                                │                              │
                                                                │   SetLatentNoiseMask <───────┘
                                                                │            │
UNETLoader ─> ModelSamplingAuraFlow ─> CFGNorm ─────────> KSampler(20, cfg 2.5)
                                                                 └─> VAEDecode
                                                                       └─> ColorTransfer(ref=cropped_image)
                                                                             └─> ImageCompositeMasked
                                                                                  (feathered mask, 픽셀 공간)
                                                                                   └─> InpaintStitchImproved ─> SaveImage
```

`ModelSamplingAuraFlow`와 `CFGNorm`은 Qwen 계열 필수 패치다. 빼면 품질이 무너진다.
`TextEncodeQwenImageEditPlus`가 레퍼런스 latent 컨디셔닝을 내부에서 처리하므로
별도 `ReferenceLatent`는 필요 없다.

## 마스크를 어떻게 칠할 것인가 — 경계 품질의 최대 변수

**MaskEditor의 브러시 경도(hardness)는 이 워크플로우들에서 의미가 없다.**
`ThresholdMask(0.5)`가 마스크를 이진화하므로 부드럽게 칠한 가장자리는 버려진다.
대신 아래 두 가지가 결과를 좌우한다.

**1. 대상에 딱 붙여 칠하지 말고 넉넉하게 칠한다.**
경계 전환은 결국 "생성된 픽셀"과 "원본 픽셀"을 섞는 구간이다. 그 구간이
디테일이 많은 곳(머리카락 끝, 제품 로고, 질감 경계)에 놓이면 아무리 잘 섞어도
이중 노출처럼 보인다. 마스크를 대상보다 넓게 잡아 **전환이 평탄한 영역
(배경, 매끈한 면, 그림자)에서 일어나도록** 만들어야 한다.

**2. 지우는 작업이면 그림자·반사까지 포함시킨다.**
물체만 칠하고 그림자를 남기면 물체 없는 그림자가 남아 가장 부자연스럽다.

## 경계가 어색한 세 가지 원인과 대응

| 원인 | 증상 | 대응 |
| --- | --- | --- |
| 생성물이 마스크 외곽선에 잘림 | 칼로 자른 듯한 단면 | `GrowMask.expand` ↑ (20~32) |
| 톤·노출·화이트밸런스 드리프트 | 붙여넣은 듯 붕 뜸 | `ColorTransfer` (strength 0.4~0.6) |
| 페더 구간의 이중 노출 | 경계가 뿌옇게 겹쳐 보임 | 페더를 무작정 늘리지 말고 마스크를 평탄한 영역까지 확장 |

페더링을 키우는 것이 항상 답은 아니다. 서로 다른 두 이미지를 넓은 폭으로 알파
블렌딩하면 고스팅이 생긴다. 페더는 48 전후에서 멈추고, 나머지는 마스크 위치와
색 정합으로 푸는 것이 맞다.

## 사용법

1. `LoadImage`에 **본인 이미지를 업로드**한다. 기본값은 템플릿 예제 파일명이라
   워크스페이스에 없으면 실행이 막힌다.
2. 우클릭 → **Open in MaskEditor**로 채울 영역을 칠한다.
3. 포지티브 프롬프트에 마스크 영역에 무엇이 있어야 하는지 자연어로 쓴다.
   Qwen은 네거티브 프롬프트를 **실제로 반영한다** (Flux와 다름).
4. 실행. `SaveImage`가 원본 해상도 결과, `PreviewImage`가 크롭 영역 결과다.

## 파라미터 조정

| 노드 | 값 | 조정 기준 |
| --- | --- | --- |
| `KSampler.cfg` | 2.5 | Qwen은 진짜 CFG를 쓴다. 2.5~4 유지. 7 이상은 색이 과포화된다 |
| `KSampler.steps` | 20 | Lightning LoRA를 쓰면 4~8 + cfg 1.0으로 내린다 |
| `ModelSamplingAuraFlow.shift` | 1.73 | Qwen 기본값. 건드리지 않는 편이 낫다 |
| `InpaintCropImproved.output_target_*` | 1024 | 작은 제품 디테일이 부족하면 1536 |
| `InpaintCropImproved.context_from_mask_extend_factor` | 1.4 | 주변 맥락이 더 필요하면 1.6~2.0 |
| `InpaintCropImproved.mask_blend_pixels` | 48 | 픽셀 합성 페더링 폭. 64 이상은 고스팅이 생기니 그 위로는 올리지 않는다 |
| `GrowMask.expand` | 20 | 생성물이 마스크 모양대로 잘려 보이면 32까지 |
| `ColorTransfer.strength` | 0.5 | 생성 영역이 붕 뜨면 0.7까지. 1.0은 새 내용물의 색까지 원본 히스토그램에 끌려간다 |

속도가 필요하면 `Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16` LoRA를
`LoraLoaderModelOnly`로 붙이고 steps 8 / cfg 1.0으로 내린다.

## 필요 모델

**Klein 9B (권장)**

| 종류 | 파일명 |
| --- | --- |
| diffusion_model | `flux-2-klein-9b.safetensors` |
| text_encoder | `qwen_3_8b.safetensors` (CLIPLoader type=`flux2`) |
| vae | `flux2-vae.safetensors` |

**Qwen 2511**

| 종류 | 파일명 |
| --- | --- |
| diffusion_model | `qwen_image_edit_2511_fp8mixed.safetensors` |
| text_encoder | `qwen_2.5_vl_7b_fp8_scaled.safetensors` (CLIPLoader type=`qwen_image`) |
| vae | `qwen_image_vae.safetensors` |

커스텀 노드는 `comfyui-inpaint-cropandstitch`(crop/stitch)와
`ComfyUI-KJNodes`(선택)만 필요하고 나머지는 코어다.

## 2026년 7월 기준 오픈 인페인팅 지형

대형 랩이 내놓은 **마스크 네이티브 아키텍처**는 Flux.1 Fill dev(2024-11)가 마지막이다.
그 이후 모델(Klein, Qwen-Edit, Krea 2, Z-Image)은 전부 지시문 편집 또는 T2I
파운데이션이고, 마스크 조건부 변형을 따로 내지 않았다.

커뮤니티는 전용 모델을 기다리는 대신 **최신 모델 + 태스크 LoRA + crop&stitch +
세컨드 패스** 패턴으로 우회했다. 이게 현재의 실질적 SOTA다.

실측 결과도 이 방향을 지지한다. 마스크 네이티브인 OneReward가 세 워크플로우 중
가장 품질이 낮았고, 마스크 채널이 없는 편집 모델(Klein, Qwen-Edit)에 crop&stitch와
픽셀 합성을 붙인 쪽이 더 좋았다. 전용 아키텍처보다 **모델 자체의 최신성**이 결과에
더 크게 기여한다는 뜻이다.

### 클라우드에서 쓸 수 있는 인페인팅 관련 LoRA

| LoRA | 베이스 | 용도 |
| --- | --- | --- |
| `Qwen-Image-Edit-2511-Object-Remover-v2-9200` | Qwen Edit 2511 | 물체 제거 |
| `Qwen-Image-Edit-easy_inpaint` | Qwen Edit | 검은 영역 채우기 (프롬프트를 `Inpaint the black areas`로 시작) |
| `flux-2-klein-4b-object-remove` / `-outpaint` | Klein **4B 전용** | 제거 / 아웃페인팅 |
| `flux.1-fill-dev-object-removal-lora` | Flux Fill | 제거 |
| `Z-Image-Turbo-Fun-Controlnet-Union-2.1` | Z-Image Turbo | ControlNet 경유 인페인팅 |

Krea 2는 클라우드에 스타일 LoRA만 있고 인페인팅 LoRA는 없다. 커뮤니티의
[Krea 2 Identity Edit LoRA v1.2](https://civitai.com/models/2761113/krea-2-identity-edit)가
"near-pixel 보존" 마스크 편집을 지원하지만 `ComfyUI-Krea2Edit` 커스텀 노드 팩이
필요해 로컬 ComfyUI에서만 쓸 수 있다.

## 검증 기록

| 워크플로우 | prompt_id | 결과 |
| --- | --- | --- |
| Qwen 2511 (최종: 20px 팽창 + ColorTransfer) | `7882d1cd-8d97-4ddb-b314-91f2c6e51d01` | 성공, 육안 확인 — 톤 정합 개선 |
| Qwen 2511 (초기: 8px 팽창, 색 정합 없음) | `7f89e468-678b-49de-b3f5-b0fd0c5702e4` | 성공, 다만 경계가 붕 뜸 |
| OneReward (수정판) | `919aa3b0-ca41-4aeb-b901-75c7fab56d68` | 성공, 육안 확인 |
| Klein 9B (최종: 이진 20px + 페더 48) | `7c7e4ce3-b752-429e-a636-9cc97ee68cf2` | 성공, 육안 확인 — 외곽 매끄러움 |
| Klein 9B (소프트 마스크 blur 6 + DD) | `554dd2b8-2900-4cd0-8565-355633347d88` | 브림에 미세 프린지 |
| Klein 9B (소프트 마스크 blur 16 + DD) | `f1851310-c59b-4a12-9dd0-ec2c9f1d1226` | 브림에 톱니 돌출 |
| Klein 9B (6스텝, 이진 8px + 페더 24) | `b1236062-a68d-44e1-8dc6-1acf1f23df0e` | 성공, 다만 경계 전환이 급함 |
| Klein 9B (20스텝, 초기판) | `bf5b8f6d-8fa8-4820-9658-b77b32661b35` | 실행은 성공했으나 품질 불량 (과샘플링) |

## 참고 자료

### 커뮤니티

- [Qwen Image Edit 2511 Inpainting 3.0 워크플로우 (axiomgraph)](https://github.com/axiomgraph/ComfyUIWorkflow/blob/main/Qwen%20Image%20Edit%202511%20Inpainting%203.0.json) — 이 워크플로우의 배선 출처
- [Inpaint (Qwen ImageEdit 2511)](https://civitai.com/models/2412652/inpaint-qwen-imageedit-2511)
- [QWEN Image Edit 2511 Segment Inpaint, swap, local edit](https://civitai.com/models/2257259/qwen-image-edit-2511-segment-inpaint-swap-local-edit)
- [Qwen Image Edit Easy Inpaint LoRA](https://civitai.com/models/1928341/qwen-image-edit-easy-inpaint-lora)
- [Qwen-Image InstantX Inpainting ControlNet 공식 워크플로우](https://comfy.org/workflows/image_qwen_image_instantx_inpainting_controlnet-15538e51d812/)
- [Z Image Turbo Inpaint (SAM2 + crop/paste + 세컨드 패스)](https://civitai.com/models/2236106/z-image-turbo-inpaint)
- [LanPaint — 훈련 불필요 인페인팅 샘플러](https://github.com/scraed/LanPaint)

### 논문

- [BRIDGE: Coarse-Mask Local Editing](https://arxiv.org/abs/2605.07846) (2026-05) — 마스크가 형태 prior로 오작동하는 문제
- [Your Latent Mask is Wrong](https://arxiv.org/abs/2512.05198) (2025-12) — latent 마스크 경계 아티팩트
- [PixPerfect](https://arxiv.org/pdf/2512.03247) (2025-12) — 픽셀 공간 refinement로 시임 제거
- [LanPaint](https://www.alphaxiv.org/overview/2502.03491v3) — Langevin 기반 정확 조건부 샘플링
