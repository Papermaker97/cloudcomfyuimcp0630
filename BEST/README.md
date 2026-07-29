# BEST 12 — 최신·고품질만 추림 (2026-07)

45개 중 **모델 세대가 최신이고 실무에서 실제로 쓸 값어치가 있는 12개**만 남겼습니다.
전부 Comfy Cloud 레지스트리에서 MCP로 조회 검증 완료 → **클라우드에서 돕니다.**

`run_template(template_id="<원본이름>")` 으로 실행하거나, JSON을 ComfyUI에 드래그앤드롭.

| # | 파일 | 원본 template_id | 모델 | 왜 이걸 골랐나 |
|---|---|---|---|---|
| 01 | BG 알파추출 | `api_bria_remove_video_background_transparent` | BRIA | 알파 WebM + **마스크 시퀀스** 동시 출력. Nuke/AE로 넘길 때 유일하게 제대로 된 출력 |
| 02 | **BG교체+라이팅통합** | `video_bernini_r_video_editing` | **Wan2.2 Bernini-R** | ⭐ **이번 조사 최고 발견.** 아래 설명 참조 |
| 03 | 오브젝트 교체 | `templates_shane_change_any_objects` | SAM3 + Wan2.1 VACE | 30노드 풀그래프. 프롬프트로 마스킹→교체, 전 단계 튜닝 가능 |
| 04 | 오브젝트 제거 | `utility_void_video_inpainting` | VOID + SAM3 | **그림자·반사까지 제거.** `sam3_text_prompt`로 대상 지정 |
| 05 | 캐릭터 교체 | `video_wan21_scail2_character_replacement_int8` | SCAIL-2 int8 + sam3.1_multiplex | int8이 fp8보다 품질↑ 속도↑. Base/Extend 2단이라 긴 샷 가능 |
| 06 | 모션보존 편집 | `api_runway_aleph2_video_edit` | Runway Aleph2 | 원본 모션·타이밍 락. 02가 안 먹을 때 대안 |
| 07 | FX 스타일라이즈 | `templates_shane_video_restyle` | Wan2.1 VACE + **Depth Anything v2** | 25노드. 뎁스로 원본 구조 잡고 스타일만 갈아끼움 |
| 08 | FX 궤적 드로잉 | `templates_rob_wan_ati_motion_control` | Wan ATI | 이펙트 경로를 **직접 그려서** 지정 |
| 09 | 마스크 생성 | `utility_video_segment_sam3` | SAM3 | 03/04 앞단에 물리거나 단독으로 로토 대체 |
| 10 | 업스케일 | `utility_seedvr2_3b_int8_upscale_video` | SeedVR2 3B int8 | 1-step diffusion, temporal consistency 유지. 속도/품질 밸런스 최선 |
| 11 | 뎁스맵 | `utility_depth_anything3_video_depth_estimation` | Depth Anything **v3** | ControlNet 구동용. 07과 조합 |
| 12 | 합성 노드 부품창고 | `basic_mask_operations_and_compositing` | 없음 | 41노드. **모델 불필요.** 마스크 논리연산·페더 합성 레퍼런스 |

## ⭐ 02번을 최우선으로 보세요

`video_bernini_r_video_editing`의 **기본 프롬프트가 문자 그대로 배경 교체 지시문**입니다:

> "Replace the gray studio backdrop with a daytime urban street... Keep the model's outfit, accessories, body pose, motion, and full-body framing unchanged. **Only the environment behind the subject should change.**"

즉 이건 릴라이팅 템플릿으로 분류돼 있지만 실제로는 **배경 교체 + 라이팅 통합을 한 패스에 하는 워크플로우**입니다. Wan2.2 기반(`wan2.2_bernini_r_high/low_noise_fp8_scaled` + lightx2v distill LoRA)이라 세대도 가장 최신입니다.

기존 "Bria로 분리 → 배경 생성 → 릴라이팅" 3단 파이프라인을 **이거 하나로 대체**할 수 있습니다. 분리 단계가 없으니 엣지 아티팩트도 안 생깁니다.

## ⚠️ 슬롯 기본값 표시 버그

`get_template_schema`가 돌려주는 `default` 값이 **한 칸씩 밀려 있습니다.** 예를 들어 02번에서:

- `video` 슬롯의 default에 텍스트 프롬프트가 들어있음
- `length` 슬롯의 default에 `.safetensors` 파일명이 들어있음
- `height` = 848, `width` = 81 (뒤바뀜)

**이 기본값들을 그대로 믿고 쓰면 안 됩니다.** 슬롯 이름과 타입(`type` 필드)은 정확하니 그것만 보고, 값은 직접 지정하세요. ComfyUI UI에서 열면 정상적으로 보입니다.

## 뺀 것들과 이유

- **ggvfx 7개** — 로컬 24GB VRAM 전용, 클라우드에서 안 돔. 모델 경로도 Windows 역슬래시
- **Bria 나머지 3개** — 01번의 열화판 (단색배경/그린스크린). 01이 상위호환
- **스틸 전용 릴라이팅 6개** — 영상 작업엔 02가 나음
- **LTX-2.3 계열** — 원클릭이라 편하지만 5~6노드 API 래퍼라 튜닝 여지 없음. 빠른 초벌엔 유용하니 전체 ZIP에 남겨둠
- **Seedance/Kling/Gemini 등** — 생성 위주라 VFX 합성 파이프라인과 결이 다름

전체 45개가 필요하시면 이전 ZIP의 `workflows/` 폴더를 쓰세요.
