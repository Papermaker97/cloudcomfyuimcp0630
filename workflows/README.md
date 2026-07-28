# Flux.1 Fill dev (OneReward) 인페인팅 워크플로우

현재 공개된 오픈소스 모델 중 인페인팅 품질이 가장 좋은 조합으로 구성한 ComfyUI
워크플로우입니다. Comfy Cloud 노드 카탈로그 기준으로 dry-run 검증을 마쳤습니다
(경고 0건).

- 파일: [`flux-fill-onereward-inpaint.api.json`](./flux-fill-onereward-inpaint.api.json) (API 포맷)
- 캔버스: https://cloud.comfy.org/?share=ecc7af9e3f6f

## 왜 이 조합인가

| 구성 요소 | 역할 |
| --- | --- |
| `flux.1-fill-dev-OneReward-transformer_fp8` | ByteDance Research가 Flux.1 Fill dev를 단일 리워드 모델로 추가 정렬한 버전. 인페인팅·아웃페인팅·물체 제거에서 원본 Fill dev보다 마스크 밖 컨텍스트 일치도가 높다. |
| `removal_timestep_alpha-2-1740` LoRA | 물체 제거 전용. 기본값 0.0(비활성), 제거 작업일 때만 1.0. |
| Differential Diffusion | 마스크의 회색조를 denoise 강도로 해석해 경계를 단계적으로 섞는다. 하드 엣지 티가 사라진다. |
| Inpaint Crop / Stitch (Improved) | 마스크 주변만 1024px로 크롭해 샘플링하고 원본 해상도로 되돌린다. 4K 사진에서도 마스크 영역이 풀 해상도로 생성되고, 마스크 밖 픽셀은 전혀 손상되지 않는다. |
| `InpaintModelConditioning` | Fill 계열 전용 컨디셔닝. `SetLatentNoiseMask` 방식보다 Fill 모델과 맞다. |

## 사용법

1. `LoadImage`에 이미지를 올리고 우클릭 → **Open in MaskEditor**로 채울 영역을 칠한다.
2. `CLIPTextEncode`에 **마스크 영역에 무엇이 있어야 하는지**를 자연어 문장으로 쓴다.
   장면 전체 묘사가 아니라 채울 대상만 쓰는 편이 정확하다.
3. 물체를 지우는 작업이면 `LoraLoaderModelOnly`의 `strength_model`을 `1.0`으로 올리고
   프롬프트는 비우거나 배경만 묘사한다 (예: `empty wooden table surface`).
4. 실행. `SaveImage`가 원본 해상도 결과, `PreviewImage`가 크롭 영역 결과다.

## 파라미터 조정 가이드

| 노드 | 값 | 조정 기준 |
| --- | --- | --- |
| `FluxGuidance.guidance` | 30 | OneReward 권장값. 프롬프트를 덜 따르면 40~50, 결과가 과하게 튀면 20까지 낮춘다. |
| `KSampler.steps` | 20 | 미세 디테일이 필요하면 28~30. |
| `KSampler.cfg` | 1.0 | **고정.** Flux는 CFG > 1에서 품질이 무너진다. 프롬프트 반영은 FluxGuidance로 조절. |
| `InpaintCropImproved.context_from_mask_extend_factor` | 1.4 | 주변 맥락을 더 참고해야 하면 1.6~2.0. 값이 클수록 마스크 영역의 유효 해상도는 떨어진다. |
| `InpaintCropImproved.mask_blend_pixels` | 32 | 경계선이 보이면 48~64로 올린다. |
| `InpaintCropImproved.mask_expand_pixels` | 8 | 지우려는 물체의 그림자·반사가 남으면 16~32로 올린다. |
| `InpaintCropImproved.output_target_*` | 1024 | 얼굴 등 디테일이 중요하면 1536. VRAM/시간이 늘어난다. |

네거티브 프롬프트는 쓰지 않는다. Flux는 이를 무시하며, 워크플로우는
`ConditioningZeroOut`으로 빈 조건을 넣는다.

## 필요 모델

| 종류 | 파일명 |
| --- | --- |
| diffusion_model | `flux.1-fill-dev-OneReward-transformer_fp8.safetensors` |
| lora | `removal_timestep_alpha-2-1740.safetensors` |
| text_encoder | `clip_l.safetensors`, `t5xxl_fp16.safetensors` |
| vae | `ae.safetensors` |

커스텀 노드는 `comfyui-inpaint-cropandstitch` 하나만 필요하고 나머지는 코어 노드다.
Comfy Cloud에는 모두 사전 설치되어 있다.

## 대안

- **Qwen-Image InstantX Inpainting ControlNet** (`image_qwen_image_instantx_inpainting_controlnet`
  템플릿): 마스크 영역에 글자를 넣거나 지시문 기반 편집("이 간판 문구를 …로 바꿔")을
  할 때는 Qwen 쪽이 강하다. 사진 리터치·물체 제거는 OneReward가 낫다.
- **Wan 2.2 Fun Inpaint / VACE**: 동영상 인페인팅용.
