# ComfyUI 인페인팅 워크플로우

Comfy Cloud에서 실행 검증을 마친 마스크 기반 인페인팅 워크플로우입니다.

| 워크플로우 | 모델 | 출시 | 캔버스 |
| --- | --- | --- | --- |
| [`qwen-image-edit-2511-inpaint.api.json`](./qwen-image-edit-2511-inpaint.api.json) **(권장)** | Qwen-Image-Edit 2511 | 2025-11 | https://cloud.comfy.org/?share=4af4905c4ff3 |
| [`flux-fill-onereward-inpaint.api.json`](./flux-fill-onereward-inpaint.api.json) | Flux.1 Fill dev + OneReward | 2024-11 / 2025-08 | https://cloud.comfy.org/?share=09188b15cee1 |
| [`flux2-klein-9b-inpaint.api.json`](./flux2-klein-9b-inpaint.api.json) (비권장) | FLUX.2 Klein 9B | 2026-01 | https://cloud.comfy.org/?share=0971a11a862f |

## 실측 비교

동일 이미지·동일 마스크·동일 시드(875421903)로 실행한 결과를 육안 비교했습니다.

| | Qwen-Image-Edit 2511 | Flux.1 Fill OneReward |
| --- | --- | --- |
| 밀짚 짜임 텍스처 | 선명하고 결이 살아있음 | 평평하고 단조로움 |
| 리본 | 그로그랭 질감 + 리본 매듭까지 형성 | 단색 평면 밴드, 매듭 거의 없음 |
| 마스크 경계 | 이음선 없음 | 이음선 없음 |
| 종합 | **디테일 우위** | 보수적이고 밋밋함 |

시드 하나·이미지 하나짜리 비교라 벤치마크가 아니라 일화입니다. 다만 프롬프트를
따라가는 정도와 텍스처 밀도에서 차이가 뚜렷했습니다.

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
→ `ThresholdMask(0.5)` → `GrowMask(8)`로 **이진화 후 팽창**한 마스크만 모델에
넣는다. 페더링은 픽셀 합성 단계에서만 쓴다.

3번은 초기 Klein 워크플로우의 실제 버그였고, 아래 논문들이 다루는 주제다.

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
                                                                 └─> VAEDecode ─┐
                                                                                │
                                                 ImageCompositeMasked <─────────┘
                                                  (feathered mask, pixel space)
                                                          └─> InpaintStitchImproved ─> SaveImage
```

`ModelSamplingAuraFlow`와 `CFGNorm`은 Qwen 계열 필수 패치다. 빼면 품질이 무너진다.
`TextEncodeQwenImageEditPlus`가 레퍼런스 latent 컨디셔닝을 내부에서 처리하므로
별도 `ReferenceLatent`는 필요 없다.

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
| `GrowMask.expand` | 8 | 경계가 지저분하면 16으로. VAE가 8배 다운샘플이라 latent 1px = 원본 8px |
| `InpaintCropImproved.output_target_*` | 1024 | 작은 제품 디테일이 부족하면 1536 |
| `InpaintCropImproved.context_from_mask_extend_factor` | 1.4 | 주변 맥락이 더 필요하면 1.6~2.0 |
| `InpaintCropImproved.mask_blend_pixels` | 24 | 픽셀 합성 페더링 폭. 경계가 보이면 40~64 |

속도가 필요하면 `Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16` LoRA를
`LoraLoaderModelOnly`로 붙이고 steps 8 / cfg 1.0으로 내린다.

## 필요 모델 (Qwen 2511)

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
| Qwen 2511 | `7f89e468-678b-49de-b3f5-b0fd0c5702e4` | 성공, 육안 확인 |
| OneReward (수정판) | `919aa3b0-ca41-4aeb-b901-75c7fab56d68` | 성공, 육안 확인 |
| Klein 9B | `bf5b8f6d-8fa8-4820-9658-b77b32661b35` | 실행은 성공했으나 마스크 경계 품질 불량 |

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
