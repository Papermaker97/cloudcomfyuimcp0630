# Week 5 ComfyUI 워크플로우: 조사·제작 보고 (dry run)

작성일: 2026-10-01 · 범위: 조사, 그래프 제작, Comfy Cloud 저장, MCP dry run 사전 검증까지.
**실행(Queue/Run), 유료 API 호출, GPU 추론, 학습, 업로드는 하지 않았습니다.**

## 1. 현재 MCP 환경

| 항목 | 확인 결과 |
|---|---|
| 연결 대상 | Comfy Cloud 호스팅 MCP (`https://cloud.comfy.org/mcp`), production, 서버 v0.62.1, OAuth 인증됨 |
| Cloud / Local | **Cloud 전용**. 사용자 노드 설치나 pip 설치 경로 없음. 노드·모델은 Cloud 카탈로그에 있는 것만 사용 가능 |
| 기존 저장 워크플로우 | 83개. `W5_` 이름과 겹치는 것은 없었고, 기존 워크플로우는 덮어쓰거나 삭제하지 않음 |
| 계정 소유 LoRA | 20개 (`search_models owned:true`) |
| 계정 입력 파일 | LoadImage 해시 이름 PNG 11개, LoadVideo 해시 이름 MP4 3개. 내용은 MCP로 열어볼 수 없어 **용도 확인 불가** |
| 비용 미발생 확인 | 작업 전후 `get_billing_activity`의 최신 이벤트가 동일함 (2026-10-01T21:18:12Z, 이 세션 시작 전 이벤트). 큐도 running 0, pending 0 |

도구별 비용 성격 (MCP 도구 설명에 문서화된 내용 기준이며, 독립 검증은 billing 피드 전후 비교로만 했습니다):

- `submit_workflow dry_run:true`: 로컬 사전 검증만 하고 잡을 만들지 않음. 이 세션에서 4회 호출했고 billing 변화 없음.
- `estimate_credits`: 읽기 전용. 다만 **번들 가격표가 최신 노드를 모름**. Ideogram 4.5 Precise Edit에 "0 credits"를 돌려줬는데, 이 노드가 번들 카탈로그에 없어서 생긴 오답입니다. 따라서 견적은 **확인 불가**로 처리합니다. GPU 시간은 견적 범위 밖입니다.
- `save_workflow`: 저장만 하고 실행하지 않음.
- `run_*`, `submit_workflow`(dry_run 없이), `partner_generate`, `submit_batch`: 실행이며 비용이 발생합니다. **사용하지 않았습니다.**

조사 제약: 이 컨테이너에서 `huggingface.co`, `docs.ltx.io`, `x.com`, `github.com`(웹·API), `cloud.comfy.org` 직접 접속이 차단되어 있습니다. `raw.githubusercontent.com`만 열려 있어서 Lightricks와 Comfy-Org 저장소의 원본 파일은 읽었습니다. **BFS 가이드, LTX 모델 카드, X 게시글은 읽지 못했습니다.**

## 2. 6개 구현 가능성

| # | 목표 | 현재 환경 가능 여부 | 실제 템플릿/노드 | 부족한 모델/에셋 | 비용 확인 상태 | 권장 다음 단계 |
|---|---|---|---|---|---|---|
| 1 | 학습 LoRA 적용·비교 | **에셋 필요** (구조는 구성됨) | w4 Z-Image Turbo A/B 구조 재사용: `UNETLoader`, `LoraLoaderModelOnly`, `KSampler`, `SaveImage` | 강사가 학습한 LoRA인지 **확인 불가**. 계정 소유 후보는 `0824_car.safetensors`(ZImageTurbo), `KNP_000003000.safetensors`·`coloso.safetensors`(Krea 2). 트리거 단어 미상 | GPU 실행. API 노드 없음. GPU 초·크레딧 **확인 불가** | 강사가 사용할 LoRA 파일·베이스·트리거를 지정 → 1회 테스트 승인 |
| 2 | Qwen Image 2.1 BFS Body Swap | **추가 모델 필요 + 문서 확인 부족** | 공식 `image_qwen_image_2_1_image_edit`을 평탄화. `TextEncodeQwenImage21`(image_1 장면, image_2 인물), latent는 인코더 출력 LATENT(image_1 크기) | **BFS LoRA가 Cloud 카탈로그에 없음**(`search_models "BFS"` 결과 0건). BFS 가이드를 못 읽어서 트리거 프롬프트·해상도 배분·LoRA 강도·정확한 파일명 미확인. 장면·인물 이미지 없음 | GPU 실행. **확인 불가** | 강사가 BFS 가이드 확인 → LoRA를 Cloud 모델로 import(대용량 다운로드·업로드라 승인 필요) → 노드 4 파일명 교체 |
| 3 | Ideogram 4.5 Precise Edit | **에셋 필요** | 공식 `api_ideogram_v4_5_precise_image_edit` 그대로 사용. `CreateBoundingBoxes` → `BuildJsonPromptIdeogram` → `IdeogramPreciseEditApi`(ideogram-4.5, quality medium). 마스크가 아니라 **bbox + 설명** 방식이며, 참조 이미지 슬롯 image_2~5는 선택 사항 | 편집용 스틸 없음. `IdeogramPreciseEditApi`가 MCP 번들 카탈로그에 없어서 **MCP dry run으로 구조 검증 불가** | **유료 API 노드. 건당 가격 확인 불가** (estimate가 0으로 잘못 표시) | 스틸 준비 → Cloud 화면의 Estimate·가격 표시를 강사가 확인 → 1회 승인 |
| 4 | LTX Clean Plate | **에셋 필요 + 문서 확인 부족** | Lightricks 공식 `LTX-2.3_ICLoRA_HDR_Distilled.json` 구조에서 IC-LoRA만 교체: `LTXICLoRALoaderModelOnly`, `LTXAddVideoICLoRAGuide`, `SamplerCustomAdvanced`, `LTXVCropGuides` | 모델 `ltx-2.3-22b-ic-lora-clean-plate-1.0.safetensors`는 Cloud에 **있음**. 마스크 등 별도 조건 입력이 필요한지는 모델 카드(HF 차단) 미확인. 현재는 원본 영상만 가이드로 넣고 제거 대상을 프롬프트로 지정. 원본 클립 없음 | GPU 실행. **확인 불가** | 강사가 HF 모델 카드에서 입력 조건 확인 → 클립 준비 → 1회 승인 |
| 5 | LTX Day-to-Night / Relight | **에셋 필요** (Day-to-Night 선택) | #4와 같은 공식 구조에 `ltx-2.3-22b-ic-lora-day-to-night-0.9.safetensors` | LTX용 Relight 어댑터는 Cloud·공식 저장소 모두에서 **찾지 못함**(Relight LoRA는 Wan Animate·Qwen Edit용만 있음). 낮 장면 클립 없음 | GPU 실행. **확인 불가** | 클립 준비 → 1회 승인 |
| 6 | LTX Native HDR / EXR | **현재 환경 불가** | 공식 경로는 `LTXVHDRDecodePostprocess`(LogC3 → linear, OpenImageIO로 EXR 저장)인데 **Cloud에 없음**(`get_node` missing). EXR 입력 노드도 없음. Native HDR(`--hdr`, EXR 입력)은 ComfyUI 노드가 아니라 `ltx-pipelines` Python CLI 기능 | IC-LoRA `ltx-2.3-22b-ic-lora-hdr-0.9`는 Cloud에 있음. 다만 **이것은 SDR→HDR 재구성이지 Native HDR이 아님**. EXR 원본 없음 | 해당 없음 | 로컬 ComfyUI + ComfyUI-LTXVideo + openimageio 또는 ltx-pipelines CLI 사용을 제안(환경 이전은 승인 후) |

공개 소스가 있다는 것과 Cloud에서 실행할 수 있다는 것은 별개라서 나눠 적었습니다. #6이 대표적인 경우로, 공식 JSON은 있지만 Cloud에는 필요한 노드가 없습니다.

### Day-to-Night과 Relight 중 Day-to-Night을 고른 이유

- Day-to-Night: 시간대를 바꾸는 작업입니다(하늘, 실내외 조명 점등, 전체 노출). LTX 공식 IC-LoRA가 있고 Cloud에도 설치되어 있습니다.
- Relight: 같은 시간대에서 광원의 방향·색·세기를 바꾸는 작업입니다. LTX용 공식 Relight IC-LoRA는 Cloud와 공식 저장소 README 어디에서도 확인되지 않았습니다.
- 그래서 **"공식 지원 + Cloud에 모델 있음"** 조건을 만족하는 것은 Day-to-Night 하나뿐이었습니다. MiniMax 등 다른 모델로 바꾸려면 먼저 제안 후 승인을 받겠습니다.

## 3. 저장한 워크플로우 (Cloud 저장 · 구조 검증)

| 파일 | Cloud 이름 / workflow_id | 형식 | MCP dry run 결과 |
|---|---|---|---|
| `workflows/W5_01_LoRA_Application_Comparison.json` | `W5_01_LoRA_Application_Comparison` / `50482727-9efc-47be-b100-879278a0e3c8` | API → save 자동 변환 | validated. 경고 1: `0824_car.safetensors`가 번들 색인에 없음(계정 소유 모델이라 정상일 수 있음) |
| `workflows/W5_02_Qwen21_BFS_BodySwap.json` | `W5_02_Qwen21_BFS_BodySwap` / `2ca9a2df-5bb8-4b7d-9007-387436e8c566` | API → save | validated. 경고 4: Qwen 2.1 모델 3개는 번들 색인 지연 때문이고 `search_models`로는 Cloud 존재 확인됨. **BFS LoRA는 실제로 없음** |
| `workflows/W5_03_Ideogram45_PreciseEdit.json` | `W5_03_Ideogram45_PreciseEdit` / `faf147b4-2508-423f-935f-ddbd8d8464fe` | save(공식 템플릿 기반) | **dry run 불가**. 노드가 번들 카탈로그에 없음. 공식 템플릿의 연결 구조를 그대로 둔 것만 근거 |
| `workflows/W5_04_LTX_CleanPlate.json` | `W5_04_LTX_CleanPlate` / `3c90b2a9-45eb-4db4-ab34-054537dd04a9` | API → save | validated, 경고 0. **LoadVideo 파일 존재 여부는 검사하지 않음** |
| `workflows/W5_05_LTX_DayToNight_or_Relight.json` | `W5_05_LTX_DayToNight_or_Relight` / `9aa9397f-a6e4-4685-9078-25dc08814688` | API → save | validated, 경고 0 (LoadVideo 파일은 #4와 같이 검사하지 않음) |
| W5_06 | 만들지 않음 | — | 현재 환경 불가 |

Cloud 캔버스에서 여는 주소: `https://cloud.comfy.org/#<workflow_id>`. 그래프는 `build_workflows.py`로 다시 생성할 수 있습니다.

**구조 검증 통과는 결과가 좋다는 증거가 아닙니다.** dry run은 노드 존재, 연결, 필수 입력만 확인합니다. 모델 호환성, 출력 품질, 메모리 부족 여부는 실제 실행해야 알 수 있습니다.

### 입력 placeholder (모두 누락 상태)

실행하면 명확히 실패하도록 `MISSING_` 접두사를 붙였습니다. 이것들을 성공으로 처리하지 않습니다.

| 노드 | 현재 값 | 상태 |
|---|---|---|
| W5_02 #4 LoRA | `MISSING_BFS_qwen_image_2.1_body.safetensors` | 유효하지 않은 참조(Cloud에 없음, 실제 파일명 미확인) |
| W5_02 #10 / #11 | `MISSING_W5_02_target_scene.png` / `MISSING_W5_02_person_ref_fullbody.png` | 누락 |
| W5_03 LoadImage | `MISSING_W5_03_edit_still.png` | 누락. bbox도 비워 둠(템플릿 예시 좌표는 샘플 초상화 기준이라 제거) |
| W5_04 #10 | `MISSING_W5_04_cleanplate_source.mp4` | 누락 |
| W5_05 #10 | `MISSING_W5_05_day_source.mp4` | 누락 |
| W5_01 #11 | `0824_car.safetensors` | 파일은 계정에 있음. **강사가 학습한 LoRA인지는 미확인** |

## 4. 누락 에셋과 준비 방법

새로 생성한 에셋은 없습니다. 유명 인물이나 학생 개인정보는 쓰지 않습니다.

| 용도 | 필요한 것 | 형식·조건 | 준비 방법 |
|---|---|---|---|
| LoRA 적용 (#1) | 강사가 학습한 LoRA 1개 + 베이스 모델 이름 + 트리거 단어 | `.safetensors`, 베이스와 같은 계열 | 이미 Cloud에 있으면 파일명만 알려 주세요. 없으면 Cloud 모델 import가 필요합니다(업로드라 승인 필요) |
| LoRA 학습 | 데이터, 캡션, 설정, 중간 샘플 | 베이스 모델 확정 후 결정 | **이 MCP에는 학습 도구가 없습니다.** AI Toolkit 저장소는 이 컨테이너에서 접속이 막혀 지원 베이스·설정을 확인하지 못했습니다. 모델과 데이터가 정해지기 전에는 범용 설정을 확정하지 않습니다 |
| Body Swap (#2) | 대상 장면 스틸 1장 | 인물이 화면에서 충분히 크게(얼굴이 작으면 정확도 한계), 정지 이미지, 사용 허가된 촬영본 | 강사 촬영본 또는 허가된 샘플 |
| Body Swap (#2) | 교체 인물 레퍼런스 1장 | **전신, 정면, 단순 배경**, 장면 인물과 체형 차이가 작은 것부터 | 강사 본인 또는 사용 동의를 받은 모델 |
| Body Swap (#2) | BFS LoRA 파일 + 가이드 | HF `Alissonerdx/BFS-Best-Face-Swap` | 강사가 가이드를 읽고 파일명·트리거·해상도 배분을 확정 → Cloud import(승인 필요) |
| Precise Edit (#3) | 승인된 스틸 1장 + 바꿀 요소 하나 | 의상 색이나 작은 소품 하나. 캔버스 크기를 스틸 크기에 맞출 것 | 강사 스틸. #2의 장면 스틸을 재사용해도 됩니다 |
| Clean Plate (#4) | 제거 대상이 화면을 지나가는 짧은 클립 | 3~5초, 카메라 고정이나 완만한 이동, 대상 1개, 24/25/30fps MP4 | 강사 촬영본. 마스크 필요 여부는 모델 카드 확인 후 결정 |
| Day-to-Night (#5) | 낮 외부 장면 짧은 클립 | 3~5초, 하늘과 건물·가로등이 보이는 장면, MP4 | 강사 촬영본. #4 클립이 낮 외부라면 재사용 가능 |
| Native HDR (#6) | 색공간이 확인된 EXR 스틸 또는 시퀀스 | scene-linear Rec.709 / ACEScg / ACEScct 중 하나로 명시 | 강사 보유분. Cloud에서는 처리 경로가 없음 |

## 5. 학생이 바꿀 항목과 강사가 설명할 연결 이유

- **W5_01**: 학생이 바꾸는 것은 `STUDENT 1/2` 강도(0 / 0.5 / 0.8 / 1.0)와 `STUDENT 2/2` 라벨(예: `0824car_str0.80`) **두 개를 함께** 바꾸는 것입니다. 강도 0이 미적용 조건입니다. 프롬프트, 크기, seed, 스텝은 고정입니다. 분기가 하나라서 한 번 실행하면 한 조건만 나옵니다.
  - 강사 설명 포인트: LoRA는 MODEL 경로에만 걸리고 텍스트·latent는 그대로입니다. 그래서 차이가 생기면 LoRA 때문입니다. 단, seed를 고정해도 같은 결과가 정확히 재현된다고 보장되지는 않습니다(GPU와 실행 환경에 따라 달라질 수 있음).
  - 출력 이름은 `W5_01_LoRA/<라벨>`입니다. 라벨과 강도가 서로 맞는지는 학생이 확인해야 합니다. Cloud 코어에 숫자를 문자열로 바꾸는 노드가 없어서 자동 연동은 하지 못했습니다.
- **W5_02**: 학생은 image_1(장면)과 image_2(인물) 두 장만 고르고 실행합니다.
  - 강사 설명 포인트: image_1이 편집 대상이자 캔버스 크기를 정하고(latent가 인코더의 LATENT 출력에서 나옴), image_2는 텍스트 인코더가 보는 참조입니다. `resolution 0`은 참조 이미지를 원래 크기로 유지한다는 뜻이고, cfg 1에서는 negative가 무시됩니다.
  - 저장물은 결과(`result`)와 장면 | 결과 | 레퍼런스 비교 띠(`compare`)입니다.
- **W5_03**: 학생은 스틸 1장, 박스 1개, 변경 설명 1줄만 정합니다.
  - 강사 설명 포인트: 마스크가 아니라 bbox 요소와 JSON 프롬프트로 수정 위치를 지정합니다. `ImageCompare`로 원본과 결과를 비교합니다. 바뀌지 않은 픽셀이 완벽히 보존된다고 약속하지 않습니다.
  - 반복 편집은 결과를 다시 입력으로 넣는 방식이며, 건별 승인 후 진행합니다.
- **W5_04 / W5_05**: 학생은 클립 1개를 고르고 프롬프트의 대상 단어만 바꿉니다.
  - 강사 설명 포인트: 원본 영상은 `LTXAddVideoICLoRAGuide`로 **조건(가이드) 프레임**이 되고, 빈 latent만 새로 생성됩니다. 생성 후 `LTXVCropGuides`로 가이드 프레임을 잘라냅니다. IC-LoRA 로더가 LoRA 메타데이터에서 downscale 비율을 읽고, 그 값이 리사이즈 배수(×32)와 가이드 축소에 함께 쓰입니다. 8스텝은 distilled LoRA 0.5와 ManualSigmas 조합 덕분입니다.
  - 원본(같은 구간·크기·fps로 리사이즈)과 결과를 각각 `source`·`result` MP4로 저장해서 나란히 비교할 수 있습니다. 오디오는 넣지 않았습니다.

## 6. 비용·최소 테스트 설정

| # | 1회 최소 테스트 설정 | 실행 횟수(제안) | 크레딧 / GPU 시간 |
|---|---|---|---|
| 1 | 1344×768, 8 steps, 이미지 1장 | 4회(강도 0 / 0.5 / 0.8 / 1.0), 건별 승인 | 확인 불가 (API 노드 없음, GPU 과금만) |
| 2 | 해상도는 image_1 원본 크기(32 배수), 25 steps, 1장 | 1회 | 확인 불가 |
| 3 | quality medium, 1장 | 1회 + 반복 편집은 건별 | **유료 API, 가격 확인 불가** |
| 4 | 짧은 변 544px, 97프레임(24fps 기준 약 4초), 8 steps, 오디오 없음 | 1회 | 확인 불가 |
| 5 | #4와 동일 | 1회 | 확인 불가 |
| 6 | — | — | — |

- GPU 초와 크레딧은 서로 다른 단위입니다. billing 피드에도 `gpu_seconds`와 `credits_used`가 따로 기록됩니다.
- 참고로 Lightricks 공식 HDR 그래프 노트에는 "Full HD 161프레임 약 100초(H100)"라고 적혀 있습니다. 하지만 이것은 다른 해상도·하드웨어 기준이고 **이 환경에서 측정한 값이 아닙니다**.

## 7. 승인이 필요한 작업

1. #1 테스트 실행 4회 (GPU)
2. #2 BFS LoRA Cloud import (대용량 다운로드·업로드) → 그다음 1회 실행
3. #3 Ideogram 4.5 유료 API 1회 (그리고 반복 편집은 건별로)
4. #4, #5 LTX 영상 실행 각 1회 (GPU, 22B 모델)
5. 강사 에셋(스틸, 클립, 레퍼런스) 업로드
6. #6 로컬 환경 사용 여부, 그리고 별도 SDR→HDR 워크플로우 추가 여부
7. LoRA 학습: 베이스 모델과 데이터가 정해진 뒤 외부 도구(AI Toolkit 등)로 진행

## 8. 출처

- Comfy-Org 공식 템플릿 (`raw.githubusercontent.com/Comfy-Org/workflow_templates/main/templates/`): `image_qwen_image_2_1_image_edit.json`, `api_ideogram_v4_5_precise_image_edit.json`, `video_ltx2_3_ic_lora.json`
- Lightricks ComfyUI-LTXVideo `README.md`, `example_workflows/2.3/LTX-2.3_ICLoRA_HDR_Distilled.json`, `LTX-2.3_ICLoRA_Union_Control_Distilled.json`
- Lightricks LTX-2 `README.md`, `packages/ltx-pipelines/docs/hdr.md`, `docs/pipelines.md` (Native HDR는 CLI `--hdr`, HDR IC-LoRA는 SDR→HDR)
- Comfy Cloud MCP: `get_node`, `search_models`, `search_templates`, `cql` 조회 결과 (2026-10-01)
- 읽지 못한 것: BFS 가이드(HF), LTX 모델 카드(HF), docs.ltx.io, X 게시글, AI Toolkit 저장소

## 9. 최종 상태표

| # | 조사 완료 | 구조 검증 | 실행 성공 | 결과 확인 | 수업용 승인 |
|---|---|---|---|---|---|
| 1 | ✅ (LoRA 출처는 미확인) | ✅ MCP dry run | — | — | — |
| 2 | △ BFS 가이드 미확인 | ✅ dry run (BFS LoRA 누락 경고) | — | — | — |
| 3 | ✅ | ❌ MCP 검증 불가 (공식 템플릿 구조 유지) | — | — | — |
| 4 | △ 조건 입력 요구 미확인 | ✅ dry run | — | — | — |
| 5 | ✅ | ✅ dry run | — | — | — |
| 6 | ✅ | 해당 없음 (현재 환경 불가) | — | — | — |

사전 결과를 미리 만들어 둔 시연과 라이브 실행은 아직 구분할 대상이 없습니다(실행 0회). 수업용 승인은 강사가 결과를 보고 결정합니다.

## 10. 추가: W5_07 Ideogram 4.5 캐릭터 시트 (2026-10-02)

- 기반: 공식 템플릿 `api_ideogram_v4_5_image_edit` (Comfy-Org/workflow_templates). bbox 프롬프트 체인을 빼고 고정 텍스트 프롬프트로 교체.
- 구조(v2): `LoadImage`(image_1 = 인물 사진, **유일한 입력**) + `PrimitiveStringMultiline`(시트 레이아웃 전체를 글로 설명, `@Image1` 참조) → `IdeogramEditApi`(ideogram-4.5, size `(2K) 2560x1440 (16:9)`, quality medium, seed 42 고정) → `SaveImageAdvanced` + `ImageCompare`(원본 vs 결과).
- 레이아웃 이미지는 쓰지 않음. `assets/W5_charsheet_layout_blank.png`는 v1 잔여물로, 결과 비교용 참고 자료로만 둠.
- size 옵션과 가격 출처: ComfyUI `comfy_api_nodes/nodes_ideogram.py` (`IDEOGRAM_45_EDIT_SIZES`, price badge). 이 소스 기준 quality medium은 **1회 $0.0858** (very_low $0.0114, low $0.0429, high $0.286). Comfy 크레딧 환산과 Cloud 실제 청구액은 미확인.
- Cloud: `W5_07_Ideogram45_CharacterSheet` / `219566b5-94c9-497f-aa74-eb88a8e675cd` (버전 3).
- v3: 첫 실행에서 인물이 머리가 크고 다리가 짧게 나옴(입력이 얼굴 클로즈업이라 그 비율을 따라감). 프롬프트 맨 위에 CHARACTER SPECS(NAME/AGE/HEIGHT/WEIGHT/GENDER) 블록을 두고, 체형은 사진이 아니라 키·몸무게에서 정하도록 8등신 규칙(머리 = 키의 1/8, 가랑이 = 키의 1/2)과 '사진의 머리 크기를 따르지 말 것'을 명시. 눈금자는 발 0 ~ 머리 끝 HEIGHT로 지정.
- 검증: `IdeogramEditApi`가 MCP 번들 카탈로그에 없어 dry run 불가. 링크 정합성만 로컬 스크립트로 확인. **실행 0회.**
- 누락: 인물 사진(`MISSING_W5_07_person_input.png`).
- 한계: 레이아웃을 글로만 지정하므로 패널 수, 헤더 글자, 눈금이 매번 맞게 나온다는 보장이 없음. BACK과 PROFILE은 사진 한 장에서 모델이 추정한 것.
