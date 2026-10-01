# 제품 원본 보존 배경 교체 v1 (ComfyUI)

> **상태: 구성 + 드라이 런(사전 검증) 완료 / 실제 실행 검증 전**
> 요청에 따라 GPU 실행은 하지 않았습니다. 아래 "테스트 결과"의 실행 항목은 모두 **미실행**입니다.
> JSON 구성과 드라이 런 통과만으로는 결과 품질(로고 보존, 외곽, 배치)을 보장하지 않습니다.

## 파일

| 파일 | 내용 |
|---|---|
| `product_bg_swap_v1.json` | **편집 가능한 ComfyUI 워크플로우** (그룹 + 설명 노트 포함, 에디터에 드래그해서 열기) |
| `product_bg_swap_api.json` | 같은 그래프의 API 포맷 (서비스 연동 / `submit_workflow` 용) |
| `build_api.py` | API 포맷 생성 스크립트 (원본 소스) |
| `build_graph.py`, `_server_graph_v1.json` | 서버가 변환한 그래프에 레이아웃·그룹·노트를 입히는 스크립트와 그 입력 |

Comfy Cloud 저장본: `product-bg-swap-preserve-v1` (workflow_id `49f5da7e-0993-4cd5-9e09-71eb7759ab39`, v2)
→ https://cloud.comfy.org/#49f5da7e-0993-4cd5-9e09-71eb7759ab39
기존 워크플로우는 수정하지 않았습니다. 새 파일로만 저장했습니다.

## 실행 위치 / 외부 API

- **외부 유료 API 노드: 없음** (`estimate_credits` = 0 credits)
- 실행 위치: **Comfy Cloud GPU**(원격)에서 오픈 모델로 실행됩니다. 사용자 PC 로컬 실행은 아니며, 입력 이미지는 Comfy Cloud에 업로드됩니다. 제3자 API(Gemini, BFL 등)로는 전송하지 않습니다.
- 추가 설치 없음: 아래 모델과 노드는 모두 현재 Comfy Cloud 환경에 이미 있고, 기존 워크플로우에서 쓰고 있던 것입니다.

## 처리 흐름 (그룹)

0. **사용자 입력·설정**: 사용자는 여기 값만 바꿉니다.
1. **제품 분리**: BiRefNet-HR-matting 자동 마스크와 수동 마스크 중 하나를 스위치로 고르고, 확장/축소·블러·구멍 메움을 적용합니다.
2. **제품 배치**: 마스크 bbox로 제품을 자른 뒤 크기 비율로 스케일하고, 1024×1024 회색 캔버스의 지정 위치에 원본 픽셀을 배치합니다.
3. **배경 생성**: Flux.1 Fill OneReward 인페인트를 씁니다. 인페인트 마스크는 제품 마스크를 반전한 것이라 제품 영역에는 노이즈가 들어가지 않습니다. 제품은 문맥으로만 참조됩니다.
4. **원본 제품 재합성**: 생성된 배경 위에 배치된 원본 제품 픽셀을 마스크로 다시 덮습니다. 생성 모델이 제품 영역을 바꿨더라도 최종 결과에는 원본 픽셀만 남습니다.
5. **저장**: `bg_swap/result`, `bg_swap/product_cutout`(투명 PNG), `bg_swap/product_mask`(흰색=제품)를 저장합니다.

제품 전체를 생성 모델로 다시 그리지 않습니다. 로고, 글자, 형태는 원본 픽셀을 리사이즈만 해서 합성합니다.

## 사용자 조절 항목 (그룹 0)

| 노드(ID) | 의미 | 기본값 |
|---|---|---|
| LoadImage (#1) | 제품 사진 | – |
| LoadImageMask (#2) | 수동 마스크 PNG (흰색=제품, 원본과 같은 해상도). 사용하지 않아도 유효한 파일이 필요하므로 제품 사진을 그대로 지정 | – |
| PrimitiveBoolean (#3) | 수동 마스크 사용 여부 | false |
| PrimitiveBoolean (#4) | 배경 스타일: false=밝은 스튜디오 / true=차분한 라이프스타일 | false |
| PrimitiveFloat (#5) | 제품 크기 (캔버스 대비 최대 비율) | 0.6 |
| PrimitiveFloat (#6) | 가로 위치 0~1 | 0.5 |
| PrimitiveFloat (#7) | 세로 위치 0~1 | 0.62 |
| PrimitiveInt (#8) | 마스크 확장(+)/축소(−) px | 0 |
| PrimitiveFloat (#9) | 마스크 외곽 블러 | 1.0 |

노드 이름(타이틀)은 기본값 그대로이고, 설명은 그룹 제목과 Note 노드에 적었습니다.

**수동 마스크 수정 절차**: 1차 실행 → `product_mask` 저장본을 편집(흰색=제품) → #2에 업로드 → #3을 true로 바꿔 재실행

## 사용 모델 / 필수 노드

모델 (Comfy Cloud에 기존 설치됨)
- `flux.1-fill-dev-OneReward-transformer_fp8.safetensors` (UNETLoader)
- `clip_l.safetensors` + `t5xxl_fp16.safetensors` (DualCLIPLoader, flux)
- `ae.safetensors` (VAELoader)
- BiRefNet-HR-matting (BiRefNetRMBG 내부에서 로드)

노드 팩
- core: LoadImage, LoadImageMask, Primitive*, ComfySwitchNode, InvertMask, JoinImageWithAlpha, MaskToImage, ImageToMask, ImageScaleBy, GetImageSize, EmptyImage, SolidMask, MaskComposite, ImageCompositeMasked, ThresholdMask, UNETLoader, DualCLIPLoader, VAELoader, CLIPTextEncode, FluxGuidance, ConditioningZeroOut, InpaintModelConditioning, KSampler, VAEDecode, SaveImage, PreviewImage
- comfyui-rmbg: BiRefNetRMBG
- ComfyUI-KJNodes: GrowMaskWithBlur
- comfyui_essentials: MaskBoundingBox+, SimpleMath+

## 지원하지 않는 입력 (v1)

- 유리, 보석, 투명·반투명, 강한 반사체 (마스크 품질과 합성 모두 보장하지 않음)
- 한 장에 제품이 여러 개이거나, 사람이 들고 있는 제품
- 마스크가 비어 있는 경우 (bbox 폭 0이면 0으로 나누기 오류 발생)
- 수동 마스크 해상도가 원본과 다른 경우
- 원본보다 크게 확대해야 하는 저해상도 제품 사진 (업스케일 열화)
- 복잡한 그림자·반사: 접지 그림자는 생성 모델 문맥에 맡기며, 별도로 제어하지 않음
- 출력 캔버스는 1024×1024 고정

## 테스트 결과

| 항목 | 결과 |
|---|---|
| 노드 존재 / 링크 무결성 / 필수 입력 (dry_run) | **통과** (`status: validated`) |
| COMBO·모델 파일명 | 통과. 경고 1건: #2 `product.png` 파일 없음(자리표시자, 테스트 이미지 미제공) |
| 유료 API 사용 여부 (estimate_credits) | 0 credits |
| 그래프 저장 후 재변환 (API 55노드 + Note 20개) | 통과 |
| 이미지 3장 × 배경 2종 실제 실행 | **미실행**: 요청에 따라 드라이 런만 수행했고, 테스트 이미지도 제공되지 않음 |
| 같은 입력·설정 재실행 재현성 | **미실행** (seed 고정 20261001로 설계만 되어 있음) |
| 로고·글자 보존 / 외곽 잘림·번짐 / 배치 자연스러움 | **미검증** |
| 수동 마스크로 오류 수정 | **미검증** (경로는 구성되어 있고 dry_run을 통과함) |
| 결과 저장 | **미검증** (SaveImage 3개 구성) |

드라이 런으로 확인할 수 없는 런타임 리스크:
- `ComfySwitchNode`의 lazy 평가 여부. 자동 마스크 경로에서도 #2 파일 존재 검사는 필요합니다.
- `SimpleMath+`의 `min`/`max` 함수 지원 여부. comfyui_essentials 구현상 지원하지만 실제 실행으로는 확인하지 않았습니다.
- Flux Fill이 제품이 없는 회색 캔버스 영역을 자연스러운 바닥이나 테이블로 채우는지는 결과 이미지를 보고 판단해야 합니다.

## 실제 검증 시 필요한 것

1. 사용 권한이 확인된 제품 사진 3장 (불투명, 외곽이 명확한 단일 제품, 로고나 글자가 있는 것 권장)
2. 실행 승인. 무료 노드만 쓰지만 Comfy Cloud GPU 시간이 6회(3×2) + 재현성 확인용 재실행만큼 사용됩니다.

## 작업 기록

| 항목 | 내용 |
|---|---|
| 환경 확인 | Comfy Cloud MCP 연결 확인(production, OAuth 인증됨). 저장된 워크플로우 81개 중 재사용 후보 확인: `png-nanobanana-birefnet`(BiRefNet 노드), `inpainting-pixel-exact-onereward-fill`(Flux Fill 설정), `bg-composite-bria`(GrowMaskWithBlur). 공식 템플릿 `utility_birefnet_remove_background`, `flux_fill_outpaint_example`도 확인 |
| 템플릿 탐색 시간 | 약 10분 (90분 제한 내) |
| 선택 이유 | 이미 설치되어 작동하던 BiRefNet과 Flux Fill OneReward를 재사용했고, 새 설치는 없습니다. 유료 API인 Nano Banana, Bria, Seedream relight는 제품을 다시 그리거나 외부 전송이 필요해 제외했습니다 |
| 드라이 런 횟수 | 1회 (1회 만에 통과, 재시도 0) |
| 실제 실행 | 0회 |
| 사용자 개입 (마스크 수정·설정 변경) | 없음 |
