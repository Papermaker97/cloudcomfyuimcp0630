# VFX 워크플로우 JSON 모음 (2026-07)

실제로 돌아가는 ComfyUI 워크플로우 JSON **45개**. 전부 JSON 파싱 + `nodes` 배열 존재 검증 완료.

- `01-background` ~ `05-utility` (38개): [Comfy-Org/workflow_templates](https://github.com/Comfy-Org/workflow_templates) 공식 템플릿. **Comfy Cloud에서 그대로 실행 가능**
- `06-ggvfx-local` (7개): [ggvfx/comfyui-workflows](https://github.com/ggvfx/comfyui-workflows) (MIT). **로컬 ComfyUI 전용** (24GB VRAM 기준)

## 두 종류를 구분하세요 — 중요

노드 수를 보면 성격이 갈립니다.

- **노드 3~12개 = API 래퍼**. 파트너 API(Bria, Runway, Kling, Gemini, Seedance…)를 호출하는 얇은 그래프입니다. 즉시 결과가 나오지만 내부를 뜯어 고칠 수 없고 크레딧이 듭니다.
- **노드 15개 이상 = 실제 OSS 그래프**. 샘플러·LoRA·ControlNet이 노출돼 있어 VFX 튜닝이 가능합니다. 아래 ★ 표시.

## 1. 배경 변경 — `01-background`

| 파일 | 노드 | 비고 |
|---|---|---|
| `api_bria_video_replace_background` | 4 | 배경 이미지로 교체 |
| ★ `api_bria_remove_video_background_transparent` | 5 | **알파 WebM + 마스크 시퀀스 출력. 컴포지팅 연결용으로 이게 제일 유용** |
| `api_bria_video_green_screen` | 3 | 그린스크린 출력 → 기존 키어 파이프라인 투입 |
| `api_bria_remove_video_background` | 3 | 단색 배경 |
| `utility_birefnet_remove_background` | 5 | 스틸, 로컬 실행 가능 |
| `utility_bria_remove_image_background` | 4 | 스틸 |

## 2. 오브젝트 변경 / 제거 — `02-object`

| 파일 | 노드 | 비고 |
|---|---|---|
| ★★ `templates_shane_change_any_objects` | **30** | **이 카테고리 최고. SAM3 세그멘테이션 → Wan2.1 VACE 인페인팅.** 프롬프트로 마스킹→교체. 노드 노출돼 있어 튜닝 가능 |
| ★ `video_wan21_scail2_character_replacement_int8` | 15 | 캐릭터 통교체. int8이 fp8보다 품질↑ 속도↑ |
| `utility_void_video_inpainting` | 6 | **그림자·반사 등 물리적 상호작용까지 제거** |
| `template_ltx2_3_obscura_remova_lora_..._object...` | 5 | 원클릭 전경 제거 |
| `template_ltx2_3_lora_remove_subtitles_from_video` | 6 | 자막/텍스트 제거 |
| `template_purz_wan22_animate_auto_character_replace` | 8 | Wan2.2 Animate 자동 캐릭터 교체 |
| `api_runway_aleph2_video_edit` | 8 | 모션·타이밍 보존 편집 |
| `api_google_gemini_omni_flash_video_edit` | 6 | 자연어 지시 편집 |

## 3. 합성 / 릴라이팅 — `03-composite-relight`

| 파일 | 노드 | 비고 |
|---|---|---|
| ★ `basic_mask_operations_and_compositing` | **41** | 마스크 생성·논리연산·페더 합성 노드 레퍼런스. **모델 불필요.** 커스텀 합성 그래프 짤 때 부품 창고로 쓰기 좋음 |
| `video_bernini_r_video_editing` | 12 | **비디오** 릴라이팅 (일관성 유지) |
| `video_bernini_r_image_editing` | 11 | 스틸 릴라이팅 + before/after |
| `template_character_portrait_relighting` | 11 | Nano Banana Pro, 다중 라이팅 조건 |
| `api_beeble_switchx_image_edit` | 9 | 레퍼런스 라이팅/스타일 이식 |
| `templates-product_scene_relight` | 8 | 제품+배경 합성 후 통합 재조명 (Seedream 4.5) |
| `templates_rob_portrait_light_migration.app` | 7 | 라이팅 레퍼런스 → 타깃 이식 (Qwen-Image-Edit) |
| `templates-qwen_image_edit-crop_and_stitch-fusion` | 4 | 마스크 영역 릴라이트 |
| `api_magnific_image_relight` | 4 | |

## 4. FX — `04-fx`

| 파일 | 노드 | 비고 |
|---|---|---|
| ★★ `templates_ingi_infl8` | **29** | SAM2 + YOLO 검출 + **WanVideoLoraSelectMulti**. 팽창 이펙트용이지만 **LoRA 슬롯을 갈아끼우면 임의의 이펙트 LoRA 파이프라인으로 전용 가능** — 아래 Civitai LoRA와 조합하기 최적 |
| ★★ `templates_shane_video_restyle` | **25** | Wan2.1 VACE + **Depth Anything v2 ControlNet**. 원본 구조 유지하며 스타일라이즈 |
| `templates_rob_wan_ati_motion_control` | 8 | Animate Path 노드로 궤적 직접 드로잉 (Wan ATI) |
| `template_ltx2_3_lora_video_outpainting` | 5 | 프레이밍 확장/리포맷 |
| `api_seedance2_0_r2v_4k` | 3 | 네이티브 4K / **10-bit** — DI·그레이딩에 넣을 수 있는 유일한 등급 |
| `api_happyhorse1_0_video_edit` | 4 | 레퍼런스 5장 국소 교체 |

### 조합할 이펙트 LoRA (Civitai / HF — 별도 다운로드)
[Huge Explosion VFX](https://civitai.com/models/1295945/huge-explosion-vfx-hunyuan-video-lora) ·
[Singularity Explosion](https://civitai.com/models/1380339/singularity-explosion-wan21-i2v-lora) ·
[Realistic Fire](https://civitai.com/models/1376174/realistic-fire-wan21-t2v-lora) (트리거 `[r3al_f1re]`) ·
[Breathing Fire](https://civitai.com/models/1674101/breathing-fire) ·
[WAN2.2 Spatial Magic](https://civitai.com/models/1867349/wan22spatial-magic) ·
[Hero Run Effect](https://civitai.com/models/1620277/hero-run-effect-wan21-i2v-lora) ·
[exploded_effect_wan](https://huggingface.co/Ashmotv/exploded_effect_wan)

## 5. 유틸 (매팅 / 뎁스 / 업스케일) — `05-utility`

| 파일 | 노드 | 비고 |
|---|---|---|
| ★ `utility_video_upscale` | 13 | Wan2.2 크리에이티브 업스케일 (디테일 생성형) |
| `utility_seedvr2_3b_int8_upscale_video` | 5 | **1-step diffusion, temporal consistency 유지. 속도/품질 밸런스 최선** |
| `utility_seedvr2_video_upscale` | 9 | SeedVR2 풀버전 |
| `utility_video_segment_sam3` / `utility_image_segment_sam3` | 5 / 7 | SAM3 마스크 단독 생성 |
| `utility_depth_anything3_video_depth_estimation` | 7 | ControlNet 구동용 뎁스맵 |
| `utility_video_frame_interpolation` | 4 | RIFE / FILM — 리타이밍·슬로모 |
| `template_ltx2_3_lora_restore_archival_footage` | 6 | 아카이브 복원 |
| `api_kling_motion_control3` | 4 | 모션 레퍼런스 → 캐릭터 (페이셜 일관성 강화) |

## 6. ggvfx 프로덕션 워크플로우 — `06-ggvfx-local` (로컬 전용)

실제 VFX 프로덕션에서 검증된 그래프. **전부 ★★급이며 노드가 크게 노출돼 있어 개조 여지가 가장 큼.**

| 파일 | 노드 | 필요 모델 |
|---|---|---|
| `GGVFX_Cam_SCAIL_Match` | **76** | Wan21-14B-SCAIL, **Uni3C controlnet**, clip_vision_h, umt5-xxl, vitpose-l-wholebody.onnx, yolov10m.onnx |
| `GGVFX_Util_ControlNets` | **65** | SAM3Segment (마스크/Canny/Depth/Normal 다중 컨트롤) |
| `GGVFX_Cam_MultiAngle` | 43 | Qwen-Image-Edit-2511 (GGUF Q5_0), multiple-angles-lora, Lightning 4step |
| `GGVFX_Lite_Relight` | 42 | Qwen-Image-Edit-2509 fp8, **MultiAngleLighting LoRA** |
| `GGVFX_Lite_Transfer` | 39 | Qwen-Image-Edit-2509 fp8, **LightMigration LoRA** |
| `GGVFX_Util_Photoreal` | 23 | z_image_turbo_bf16, qwen_3_4b, flux ae |
| `GGVFX_Util_Upscale4K` | 15 | NVIDIA RTX VSR (노드 설치 후 수정 필요) |

> ⚠️ 모델 경로가 `qwen\...`, `wan\...` 처럼 **역슬래시(Windows)** 로 박혀 있습니다. Linux/macOS에서는 로더 노드에서 경로를 다시 잡아줘야 합니다.

> ⚠️ **README에 스크린샷과 함께 소개된 "Shot Paint Outs" / "Background Replacement (Unreal 그레이박스 + Wan VACE/SeeDance)" 프로덕션 워크플로우는 JSON이 저장소에 포함돼 있지 않습니다.** 리포에 실제로 있는 JSON은 위 7개(camera/lighting/utilities)뿐입니다. 해당 프로덕션 그래프가 필요하면 저자에게 직접 문의해야 합니다. 대신 배경 교체는 `templates_shane_change_any_objects`(SAM3+VACE) 구조를 배경 마스크로 뒤집어 쓰거나, `GGVFX_Cam_SCAIL_Match`의 Uni3C 컨트롤넷 부분을 가져다 쓰는 게 가장 가깝습니다.

---

## 사용법

**Comfy Cloud (01~05)** — MCP로 바로 실행:
```
run_template(template_id="templates_shane_change_any_objects", slot_overrides={...})
get_template_schema(template_id="...")   # 넘길 수 있는 파라미터 확인
```
또는 ComfyUI 웹 UI에 JSON 드래그앤드롭.

**로컬 (06 + 01~05 중 ★ OSS 그래프)** — ComfyUI에 드래그앤드롭 후 ComfyUI-Manager로 누락 노드 설치. 모델은 위 표대로 별도 다운로드.

## 추천 파이프라인

**배경 교체 (품질 우선)**
`api_bria_remove_video_background_transparent` (알파 추출)
→ 배경 생성 (`templates_shane_video_restyle`의 VACE+Depth 구조 활용)
→ `video_bernini_r_video_editing` (라이팅 매칭 — **이 단계를 빼면 합성 티가 남**)
→ `utility_seedvr2_3b_int8_upscale_video`

**오브젝트 교체**
`utility_video_segment_sam3` → `templates_shane_change_any_objects` → 그림자 잔상 시 `utility_void_video_inpainting` 보정

**FX 합성**
`templates_rob_wan_ati_motion_control` (궤적 설계) → `templates_ingi_infl8`의 LoRA 슬롯에 Civitai 이펙트 LoRA 로드 → 알파 추출 후 Nuke/AE 마감

---

### 라이선스
`06-ggvfx-local`은 MIT (`LICENSE.ggvfx` 동봉, © ggvfx). `01`~`05`는 Comfy-Org/workflow_templates 소속.
