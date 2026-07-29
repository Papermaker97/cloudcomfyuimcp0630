# ComfyUI VFX 워크플로우 리서치 (2026-07 기준)

Comfy Cloud 템플릿 라이브러리 + 오픈소스/커뮤니티(GitHub, Civitai, HuggingFace, YouTube, 교육 플랫폼) 통합 조사.
`템플릿 이름`으로 표기된 항목은 Comfy Cloud MCP의 `run_template` 로 즉시 실행 가능.

---

## 1. 배경 변경 (Background Replacement) VFX

### Comfy Cloud 템플릿 — 즉시 실행 가능

| 템플릿 | 내용 | 모델 |
|---|---|---|
| `api_bria_video_replace_background` | 비디오 업로드 + 배경 이미지 → 주피사체 자동 검출 후 배경 교체. 가상 프로덕션/광고용 | BRIA |
| `api_bria_remove_video_background_transparent` | 알파 채널 WebM + 마스크 시퀀스 출력. **컴포지팅 파이프라인 연결에 가장 유용** | BRIA |
| `api_bria_remove_video_background` | 배경을 단색으로 치환 | BRIA |
| `api_bria_video_green_screen` | 그린스크린 버전 생성 (기존 키어 파이프라인에 그대로 투입 가능) | BRIA |
| `utility_birefnet_remove_background` | 스틸 이미지 고정밀 세그멘테이션 마스크 | BiRefNet |
| `templates-product_scene_relight` | 제품 + 배경 합성 후 라이팅 통합 재조명 | Seedream 4.5 |

> 배경 교체의 핵심은 "교체" 자체보다 **라이팅 매칭**입니다. Bria로 분리 → 아래 3-2의 릴라이팅 템플릿으로 마감하는 2단 구성을 권장.

### 오픈소스 / 커뮤니티

- **[ggvfx/comfyui-workflows](https://github.com/ggvfx/comfyui-workflows)** (MIT) — **이번 조사 중 최고 품질**. 실제 VFX 프로덕션에서 검증된 파이프라인.
  - *Background Replacement with Unreal Engine Grey Box Driving Plates*: 언리얼 그레이박스를 드라이빙 플레이트로 써서 Wan VACE + SeeDance 2.0 + ControlNet으로 배경 생성. 가려진(occluded) 지오메트리까지 처리. 최종 컴포지팅은 Foundry Nuke.
  - 2026년 3월 최초 공개, **4~5월에 프로덕션 샷 워크플로우 추가**. 24GB VRAM 기준 테스트.
- **[rik-python/AI-Background-Replacement-in-ComfyUI](https://github.com/rik-python/AI-Background-Replacement-in-ComfyUI)** — Wan(i2v) + **Uni3C**(카메라 모션/패럴랙스 일관성) + VACE 조합. 전체 배경 교체와 선택적 교체(창문·하늘·벽·원경) 모두 지원.
  - ⚠️ README가 명시적으로 밝히는 한계: **원본 픽셀 엣지를 보존하지 않고 AI가 재생성**함. 프리비즈/피치/광고용이며 픽셀 락이 필요한 극장용 샷에는 부적합. 커밋 3개로 활발히 유지보수되는 프로젝트는 아님.
- **하늘 교체(Sky Replacement)** — VFX 아티스트 Doug Hogan의 워크플로우가 2026년 공식 ComfyUI 채널에 소개됨. 정적 하늘 스왑이 아니라 프레임 디코드 → 이미지 모델로 하늘 재작성 → **Wan 2.2 + ControlNet으로 구름 이동·광량 변화까지 애니메이션**해 샷에 락시키는 방식. comfy.org 워크플로우 페이지에도 Sky Replacement 항목 존재.
- **[Vace Wan 2.1 World-Building](https://www.runcomfy.com/comfyui-workflows/generate-entire-ai-worlds-vace-wan-2-1-in-comfyui-video-world-building)** (RunComfy) — 원본 카메라 무브를 유지한 채 씬 전체를 AI 환경으로 교체. VACE 임베딩이 씬 구조에 생성을 바인딩.

---

## 2. 오브젝트 변경 / 제거 VFX

### Comfy Cloud 템플릿

| 템플릿 | 내용 | 모델 |
|---|---|---|
| `templates_shane_change_any_objects` | **프롬프트만으로 객체 마스킹 → 프롬프트/레퍼런스 이미지로 교체.** 이 카테고리의 대표 워크플로우 | SAM3 + Wan2.1 VACE |
| `utility_void_video_inpainting` | 마스킹한 객체를 **물리적 상호작용(그림자·반사)까지 함께** 제거 | VOID |
| `template_ltx2_3_obscura_remova_lora_remove_object_from_video` | 프롬프트로 전경 객체 제거. 원클릭에 가까움 | LTX-2.3 Obscura Remova LoRA |
| `template_ltx2_3_lora_remove_subtitles_from_video` | 자막/텍스트 오클루전 제거 (아카이브 소재 정리에 유용) | LTX-2.3 LoRA |
| `utility_video_segment_sam3` / `utility_image_segment_sam3` | 마스크 생성 단독 사용 | SAM3 |
| `api_runway_aleph2_video_edit` | 원본 모션·타이밍 보존하며 지정 변경 적용 | Runway Aleph2 |
| `api_google_gemini_omni_flash_video_edit` | 자연어 지시로 비디오 편집 | Gemini Omni Flash |
| `api_happyhorse1_0_video_edit` | 레퍼런스 이미지 최대 5장으로 국소 교체/스타일 전이 | HappyHorse 1.0 |
| `video_wan21_scail2_character_replacement_int8` | 캐릭터 통째 교체. **int8이 fp8보다 품질 높고 더 빠름** | SCAIL-2 |
| `template_purz_wan22_animate_auto_character_replace` | 비디오 + 캐릭터 이미지로 자동 캐릭터 교체 | Wan2.2 Animate |

> 제거는 `utility_void_video_inpainting`(그림자까지) → `LTX 2.3 Obscura`(빠른 원클릭) 순으로, 교체는 `templates_shane_change_any_objects` 를 기본으로 두면 됩니다.

### 오픈소스 / 커뮤니티

- **ggvfx — Shot Paint Outs & Set Element Replacement**: Wan VACE 기반 클린 플레이트 생성 + 세트 요소 교체. 실제 프로덕션 사용 중, Nuke 컴포지팅 전제.
- **[ComfyUI + Wan VACE = Next-Level Dynamic Paintouts](https://www.youtube.com/watch?v=IybDLzP05cQ)** — 다이내믹 페인트아웃(카메라가 움직이는 샷의 객체 제거) 실무 튜토리얼.
- **[ComfyUI + Nuke: Add Realistic Compositing in Minutes](https://www.youtube.com/watch?v=pLb9vdIHBYY)** — WAN VACE 결과물을 Nuke로 넘기는 마감 워크플로우.
- **[flybirdxx/ComfyUI-SDMatte](https://github.com/flybirdxx/ComfyUI-SDMatte)** — Stable Diffusion 기반 인터랙티브 매팅. 포인트/박스/마스크 3종 비주얼 프롬프트 지원. 정밀 오브젝트 추출용.

---

## 3. FX (이펙트) 관련

### 이펙트 LoRA — Civitai (Wan 계열, 즉시 조합 가능)

| LoRA | 효과 | 베이스 |
|---|---|---|
| [Huge Explosion VFX](https://civitai.com/models/1295945/huge-explosion-vfx-hunyuan-video-lora) | 대형 폭발. 실제 폭발 클립 16개(1분)로 학습 | Hunyuan/Wan |
| [Singularity Explosion](https://civitai.com/models/1380339/singularity-explosion-wan21-i2v-lora) | 회전하는 블랙홀 + 폭발 | Wan2.1 I2V |
| [Realistic Fire](https://civitai.com/models/1376174/realistic-fire-wan21-t2v-lora) | 사실적 화염. 트리거 `[r3al_f1re]` | Wan2.1 14B T2V |
| [Breathing Fire](https://civitai.com/models/1674101/breathing-fire) | 입에서 뿜는 화염 | Wan Video |
| [WAN2.2 Spatial Magic](https://civitai.com/models/1867349/wan22spatial-magic) | 풍경·건축을 갈라 다른 공간을 드러내는 초현실 마법 효과 | Wan2.2 |
| [Hero Run Effect](https://civitai.com/models/1620277/hero-run-effect-wan21-i2v-lora) | 히어로 질주 스피드 이펙트 | Wan2.1 I2V |
| [FireVFX](https://civitai.com/models/9049/firevfx-create-more-consistent-fire) | 일관성 있는 불 (스틸/구버전이지만 레퍼런스로 유효) | SD |
| [Ashmotv/exploded_effect_wan](https://huggingface.co/Ashmotv/exploded_effect_wan) | 오브젝트 분해(exploded view) 모션 | Wan (HF) |

### Comfy Cloud 템플릿 (FX성 모션)

- `templates_ingi_infl8` — 캐릭터 팽창(inflation) 이펙트 (Wan2.2 Animate)
- `templates_rob_wan_ati_motion_control` — **Animate Path 노드로 경로를 직접 그려서** 모션 지정 (Wan ATI). 이펙트 궤적 제어에 활용도 높음
- `templates_shane_video_restyle` — 베이스 영상 + 스타일 레퍼런스 이미지 → 스타일라이즈 (Wan2.1 VACE)
- `template_ltx2_3_lora_video_outpainting` — 비디오 아웃페인팅. 프레이밍 확장/리포맷
- `api_seedance2_0_r2v_4k` — 네이티브 4K, 10bit 컬러 뎁스 출력. **DI/그레이딩 파이프라인에 넣을 수 있는 유일한 등급**

---

## 4. 그 외 VFX에 도움되는 워크플로우

### 매팅 / 로토 (가장 중요한 보조 영역)
- **MatAnyone 2 (CVPR 2026)** — 현재 오픈소스 비디오 매팅 SOTA. 플리커 없는 temporal consistency + 디테일 보존, 전경 투명 영상과 알파 매트를 별도 파일로 출력. ComfyUI 노드 존재(`MatAnyoneMatte`), v2 기본값에 **학습된 품질 평가기(quality evaluator)** 포함. → 배경 교체 전 단계로 Bria 대신 쓰면 엣지 품질이 크게 올라감.
- **[SAM2 Easy Alpha Mattes / Rotoscope](https://civitai.com/models/746889/sam2-easy-comfyui-alphamattes-rotoscope)** + [Civitai 교육 문서](https://education.civitai.com/easy-alpha-mattes-rotoscoping-in-comfyui-using-sam2/) — 로토 입문용 정석 워크플로우.
- Robust Video Matting 노드 (경량, 실시간성 필요할 때).

### 릴라이팅 (합성 마감의 핵심)
- `video_bernini_r_video_editing` — **비디오** 릴라이팅, 일관성 유지 (Bernini-R)
- `api_runway_aleph2_video_edit` — 모션·타이밍 보존 릴라이팅
- `templates_rob_portrait_light_migration.app` — 타깃 + 라이팅 레퍼런스 이미지 → 라이팅 이식 (Qwen-Image-Edit)
- `api_beeble_switchx_image_edit` / `api_magnific_image_relight` / `template_character_portrait_relighting`(Nano Banana Pro)
- ggvfx의 *Lighting Transfer* / *Dynamic Relighting* (Qwen Image Edit 2509 + Lighting Gizmo 노드) — 샷 간 라이팅 플레이트 전이, 다각도 라이팅 제어

### 카메라 / 트래킹 / 3D
- `utility_depth_anything3_video_depth_estimation` — 비디오 뎁스맵 (ControlNet 구동, 3D 리컨용)
- `api_kling_motion_control3` — 캐릭터 이미지 + 모션 레퍼런스 영상 (Kling 3.0, 페이셜 일관성 강화)
- ggvfx *Spatial Re-projection* — Qwen Image Edit 2511 + Camera Angle Gizmo로 다각도 이미지 생성
- ggvfx *SCAIL Motion Transfer* — 포즈 + 카메라 매칭 i2v
- `3d_triposplat_image_to_gaussian_splat` — 이미지 → 3D 가우시안 스플랫

### 마감 / 업스케일
- `utility_seedvr2_3b_int8_upscale_video` — SeedVR2 3B int8, 1-step diffusion. temporal consistency 유지하며 복원. **속도/품질 밸런스 최선**
- `utility_video_upscale` — Wan2.2 크리에이티브 업스케일 (디테일 추가형)
- `utility_video_frame_interpolation` — RIFE / FILM (리타이밍, 슬로모)
- `template_ltx2_3_lora_restore_archival_footage` — 아카이브 푸티지 복원
- ggvfx — NVIDIA RTX VSR 기반 4K 업스케일(노드 설치 후 수정 필요), Z-image Turbo 포토리얼 리파인

### 학습 자료
- **[Comfy Compositing](https://comfycompositing.com/workflows)** — VFX 전문가 대상. **키잉·릴라이팅·컴포지팅 노드 그래프를 유튜브 영상에서 무료 배포.** Wan 2.2 Animate 기반 인물 중심 프로덕션 워크플로우(자동 로토 + 포즈 트래킹 + 페이스 락킹 시스템)를 포함. ※ 사이트가 자동 조회를 차단해 검색 스니펫 기준 정보임
- [ActionVFX — Intro to ComfyUI for VFX](https://courses.actionvfx.com/comfyui-for-vfx) (Doug Hogan, 15개 모듈, After Effects 연동 포함)
- [fxphd — Advanced ComfyUI: Generative Video Production for VFX](https://www.fxphd.com/fxblog/advanced-comfyui-generative-video-production-for-vfx/)
- [NVIDIA 기술 블로그 — ComfyUI 고품질 크리에이터 워크플로우 구축/스케일링](https://developer.nvidia.com/blog/how-to-build-run-and-scale-high-quality-creator-workflows-in-comfyui/)

---

## 추천 파이프라인 조합

**배경 교체 (품질 우선)**
`MatAnyone 2` 매팅 → `api_bria_video_replace_background` 또는 Wan VACE+Uni3C 배경 생성 → `video_bernini_r_video_editing` 릴라이팅 → `utility_seedvr2_3b_int8_upscale_video` 마감

**오브젝트 교체**
`utility_video_segment_sam3` 마스크 → `templates_shane_change_any_objects` (SAM3+VACE) → 그림자 잔상 있으면 `utility_void_video_inpainting` 보정

**FX 합성**
`templates_rob_wan_ati_motion_control` 로 궤적 설계 → Civitai 이펙트 LoRA 적용 → 알파 추출 후 Nuke/AE 컴포지팅

---

### 주의사항
- ggvfx / rik-python 계열은 **로컬 ComfyUI 전제**(24GB VRAM). Comfy Cloud MCP는 클라우드 전용이라 이 워크플로우들을 그대로 실행할 수 없고, 노드 구성을 참고해 재구축하거나 로컬에서 돌려야 합니다.
- `comfycompositing.com` 과 `comfy.org/workflows` 개별 페이지는 자동 조회(403)를 차단해 직접 검증하지 못했습니다. 해당 항목은 검색 스니펫 기반이므로 직접 방문 확인을 권장합니다.
