# ComfyUI 인페인팅 워크플로우

Comfy Cloud 카탈로그를 조사해서 만든 마스크 기반 인페인팅 워크플로우입니다.
두 개 모두 실제로 클라우드에서 실행해 성공을 확인했습니다.

| 워크플로우 | 모델 | 출시 | 캔버스 |
| --- | --- | --- | --- |
| [`flux2-klein-9b-inpaint.api.json`](./flux2-klein-9b-inpaint.api.json) **(권장)** | FLUX.2 Klein 9B | 2026-01 | https://cloud.comfy.org/?share=0971a11a862f |
| [`flux-fill-onereward-inpaint.api.json`](./flux-fill-onereward-inpaint.api.json) | Flux.1 Fill dev + OneReward | 2024-11 / 2025-08 | https://cloud.comfy.org/?share=ecc7af9e3f6f |

## 2026년 7월 기준 오픈 인페인팅 모델 지형

| 모델 | 출시 | 라이선스 | 마스크 인페인팅 적합성 |
| --- | --- | --- | --- |
| **FLUX.2 Klein 9B** | 2026-01 | Apache 2.0 | 편집 모델 + ReferenceLatent. 커뮤니티에서 현시점 최상급 평가. **채택** |
| Krea 2 Raw / Turbo | 2026-06 | 커스텀 커뮤니티 | 12.9B T2I 파운데이션. 미학은 최상위지만 **전용 인페인팅 경로 없음** — SetLatentNoiseMask img2img만 가능 |
| Qwen-Image-Edit 2511 | 2025-11 | Apache 2.0 | 지시문 편집·텍스트 렌더링 강함. 마스크는 네이티브 아님 |
| Z-Image Turbo (ZiT) | 2025-11 | Apache 2.0 | 6B / 8스텝. 빠르지만 인페인팅은 ControlNet·LoRA 경유 |
| Flux.1 Fill dev + OneReward | 2024-11 / 2025-08 | 비상업 (FLUX.1 dev) | 유일한 **전용 인페인팅 아키텍처** (마스크가 입력 채널). 물체 제거는 여전히 강력 |

Klein을 고른 이유는 세 가지입니다 — 가장 최신이고, Apache 2.0이라 상업 사용에
제약이 없고, ReferenceLatent로 원본 이미지 전체를 편집 컨텍스트로 넣으면서
SetLatentNoiseMask로 마스크 밖 latent를 고정할 수 있습니다.

Krea 2는 카탈로그에 `krea2_raw_bf16` / `krea2_turbo_bf16`로 존재하지만
인페인팅용 조건부 입력이 없습니다. 마스크 편집에는 부적합해 채택하지 않았습니다.

## Klein 9B 워크플로우 구조

```
LoadImage ─┬─ IMAGE ─┐
           └─ MASK  ─┤
                     ├─> InpaintCropImproved ─┬─> stitcher ────────────┐
                                              ├─> cropped_image ─┐     │
                                              └─> cropped_mask ─┐│     │
                                                                ││     │
CLIPTextEncode ─> ReferenceLatent <── VAEEncode <────────────────┘│     │
       └─> FluxGuidance(4.0) ─> BasicGuider <── DifferentialDiffusion   │
                                     │                                  │
       SetLatentNoiseMask <──────────┼──────────────────────────────────┘
              └─> SamplerCustomAdvanced(Flux2Scheduler, euler, 20)
                          └─> VAEDecode ─> InpaintStitchImproved ─> SaveImage
```

핵심 설계:

- **ReferenceLatent** — Klein은 Fill 계열처럼 마스크 입력 채널이 없는 편집
  모델이다. 원본 latent를 편집 레퍼런스로 넣어야 마스크 안을 주변과 일치하게
  채운다.
- **SetLatentNoiseMask** — 마스크 밖 latent를 샘플링에서 고정한다. 이게 없으면
  Klein이 이미지 전체를 다시 그린다.
- **Flux2Scheduler** — Flux.2 전용 해상도 인지 시그마 스케줄. 일반 KSampler의
  `simple` 스케줄러와 다르며, Flux.2에서는 이쪽이 맞다.
- **DifferentialDiffusion** — 마스크 회색조를 denoise 강도로 해석해 경계를
  단계적으로 섞는다.
- **Inpaint Crop / Stitch** — 마스크 주변만 1024px로 크롭해 샘플링하고 원본
  해상도로 되돌린다. 마스크 밖 픽셀은 손상되지 않는다.

## 사용법

1. `LoadImage`에 이미지를 올린다. **반드시 본인 이미지를 업로드해야 한다** —
   기본값은 템플릿 예제 파일명이고, 그 파일이 워크스페이스에 없으면 실행이
   막힌다.
2. 우클릭 → **Open in MaskEditor**로 채울 영역을 칠한다.
3. `CLIPTextEncode`에 마스크 영역에 무엇이 있어야 하는지 자연어 문장으로 쓴다.
4. 실행. `SaveImage`가 원본 해상도 결과, `PreviewImage`가 크롭 영역 결과다.

## 파라미터 조정

| 노드 | 값 | 조정 기준 |
| --- | --- | --- |
| `FluxGuidance.guidance` | 4.0 | Flux.2 계열 기본값. 프롬프트를 덜 따르면 5~6, 결과가 튀면 2.5~3 |
| `Flux2Scheduler.steps` | 20 | 디테일이 필요하면 28~30 |
| `Flux2Scheduler.width/height` | 1024 | `InpaintCropImproved`의 output_target과 **반드시 일치**시킨다 |
| `InpaintCropImproved.context_from_mask_extend_factor` | 1.4 | 주변 맥락이 더 필요하면 1.6~2.0 (마스크 영역 유효 해상도는 떨어진다) |
| `InpaintCropImproved.mask_blend_pixels` | 32 | 경계선이 보이면 48~64 |
| `InpaintCropImproved.mask_expand_pixels` | 8 | 지운 물체의 그림자·반사가 남으면 16~32 |

CFG는 별도 노드로 두지 않았다. Klein은 guidance-distilled 모델이라
`BasicGuider`로 충분하고, 네거티브 프롬프트는 무시된다.

## 필요 모델 (Klein 9B)

| 종류 | 파일명 |
| --- | --- |
| diffusion_model | `flux-2-klein-9b.safetensors` |
| text_encoder | `qwen_3_8b_fp8mixed.safetensors` (CLIPLoader type=`flux2`) |
| vae | `flux2-vae.safetensors` |

커스텀 노드는 `comfyui-inpaint-cropandstitch` 하나만 필요하고 나머지는 코어다.

## 검증 기록

| 워크플로우 | prompt_id | 결과 |
| --- | --- | --- |
| Klein 9B | `bf5b8f6d-8fa8-4820-9658-b77b32661b35` | 성공, 이미지 2장 출력 |
| OneReward | `1ab86640-f0f0-411f-9030-160735855610` | 성공 |

## 관련 자료

- [FLUX Klein Unified Image Editing (RunComfy)](https://www.runcomfy.com/comfyui-workflows/flux-klein-unified-image-editing-inpaint-remove-outpaint-in-comfyui-advanced-image-restoration)
- [Flux2 Klein 9B Inpainting 워크플로우 (axiomgraph)](https://github.com/axiomgraph/ComfyUIWorkflow/blob/main/Flux2%20Klein%209b%20Inpainting.json)
- [Krea 2 오픈웨이트 공개](https://www.krea.ai/krea-2-open-source)
- [Z-Image Turbo (Tongyi-MAI)](https://huggingface.co/Tongyi-MAI/Z-Image-Turbo)
