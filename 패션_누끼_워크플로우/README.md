# 패션 착장 → 상의 누끼 + 고스트컷 워크플로우

> 신세계라이브쇼핑 방송비주얼팀 요구 예제 ③ (모델 착장 이미지 → 아이템 누끼컷 자동 생성) 구현.
> 강사 시연용. Comfy Cloud에서 검증 완료(dry run 통과, 실제 실행 전).

---

## 상태

- ✅ **Dry run 검증 통과** — 노드 존재·링크 무결성·필수 입력 모두 정상, 실행/과금 없음
- ✅ **Comfy Cloud 워크스페이스에 저장 완료** — 이름: `패션_상의누끼_고스트컷_ClothesSegment_GPTImage2`
  (API 포맷이 캔버스에서 열리는 save 포맷으로 자동 변환됨)
- ⬜ 실제 실행(이미지 업로드 후 큐 실행)은 미수행

---

## 구조

```
model_01.png ─→ ClothesSegment(Upper-clothes) ─→ SaveImage  01_top_cutout  ┐
model_02.png ─→ ClothesSegment(Upper-clothes) ─→ SaveImage  02_top_cutout  │
model_03.png ─→ ClothesSegment(Upper-clothes) ─→ SaveImage  03_top_cutout  ├─→ OpenAIGPTImageNodeV2 ─→ SaveImage  05_top_ghostcut
model_04.png ─→ ClothesSegment(Upper-clothes) ─→ SaveImage  04_top_cutout  ┘        (참조 이미지 4장)
```

**두 종류의 결과가 분리되어 나옵니다.**

| 구분 | 결과 | 성격 |
|---|---|---|
| 보존형 (`01~04_top_cutout`) | 투명 배경 상의 누끼 4장 | **원본 픽셀 그대로.** 생성 없음. 가려진 부분은 비어 있음 |
| 생성형 (`05_top_ghostcut`) | 고스트컷 1장 | **AI 추정.** 가려진 부분을 4개 시점을 참고해 복원 |

이 구분은 시연에서 반드시 언급해야 합니다 — 05번은 복원이 아니라 추정입니다.

---

## 사용한 노드 (이름 변경 금지)

| class_type | 역할 | 팩 |
|---|---|---|
| `LoadImage` | 모델 착장 이미지 로드 (4장) | core |
| `ClothesSegment` | 의류 부위별 분할. 표시명 "Clothes Segment (RMBG)" | comfyui-rmbg |
| `OpenAIGPTImageNodeV2` | 고스트컷 생성. 표시명 "OpenAI GPT Image 2" | core (partner/image/OpenAI) |
| `SaveImage` | 결과 저장 | core |

---

## "상의 / 하의" 토글이 구현되는 지점

`ClothesSegment` 노드는 부위별 불리언 스위치를 가지고 있습니다. **이게 고객사가 요구한 "추출할 아이템 선택" 기능 그 자체입니다.**

사용 가능한 스위치 (전부 기본값 `false`):

```
Hat, Hair, Face, Sunglasses, Upper-clothes, Skirt, Dress, Belt, Pants,
Left-arm, Right-arm, Left-leg, Right-leg, Bag, Scarf, Left-shoe, Right-shoe, Background
```

현재 워크플로우는 `Upper-clothes: true`, 나머지 전부 `false`로 **상의만** 추출합니다.

| 추출 대상 | 켤 스위치 |
|---|---|
| 상의 | `Upper-clothes` |
| 하의(바지) | `Pants` |
| 하의(스커트) | `Skirt` |
| 원피스 | `Dress` |
| 상의 + 하의 동시 | `Upper-clothes` + `Pants` |

→ 시연 때 이 불리언 하나만 바꿔서 "상의 → 하의"로 전환하는 걸 보여주면 요구사항이 그대로 충족됩니다.

---

## 주요 파라미터

### ClothesSegment
| 파라미터 | 현재값 | 설명 |
|---|---|---|
| `process_res` | 1024 | 처리 해상도. 높을수록 경계 정밀, VRAM 증가 (128~2048) |
| `mask_blur` | 2 | 마스크 경계 블러. 니트·헤어 경계가 거칠면 3~5로 (0~64) |
| `mask_offset` | 0 | 마스크 확장/축소. 배경 잔여물 있으면 음수로 (-64~64) |
| `background` | `Alpha` | 투명 배경 출력. `Color`로 바꾸면 단색 배경 |
| `invert_output` | false | 반전 |

### OpenAIGPTImageNodeV2
| 파라미터 | 현재값 | 비고 |
|---|---|---|
| `model` | `gpt-image-2` | `gpt-image-1.5` / `gpt-image-1`도 선택 가능 |
| `model.size` | `1024x1024` | |
| `model.background` | `transparent` | 고스트컷이므로 투명 |
| `model.quality` | `medium` | `low`/`high` 선택 가능. 비용·시간에 직결 |
| `model.images.image_1~4` | 누끼 4장 | **최대 16장까지 참조 가능** |
| `n` | 1 | 후보를 여러 개 뽑으려면 2~4 |

---

## 실행 전 준비

1. **입력 이미지 4장을 Comfy Cloud에 업로드**하고, `LoadImage` 노드의 파일명을 실제 업로드된 이름으로 교체
   (현재는 `model_01.png` ~ `model_04.png` 자리표시자)
2. 4장 모두 **같은 상의를 착용한** 이미지여야 고스트컷이 의미 있음
   (서로 다른 옷이면 AI가 섞어버림 — 제작 명세 §6의 금지사항)
3. 큐 실행

**비용 주의**: `OpenAIGPTImageNodeV2`는 유료 파트너 API 노드입니다. 노드 13/14를 뮤트하면 누끼 4장만 무료로 뽑을 수 있습니다.

---

## 시연 시 설명 포인트

1. **"아이템 선택"은 프롬프트가 아니라 불리언 스위치** — `Upper-clothes` 하나 켜고 끄는 걸로 상의/하의가 전환됨. 이게 UI로 노출할 파라미터의 실체
2. **복수 입력 → 복수 출력** — 4장 넣으면 4장이 각각 독립 처리되어 나옴 (고객사가 명시적으로 요구한 배치 동작)
3. **누끼와 고스트컷은 다른 것** — 01~04는 원본 픽셀 보존, 05는 AI 추정. 상품 등록용으로 쓰려면 05는 원본 대조 검수 필요
4. **참조 이미지를 여러 장 주는 이유** — 한 시점에서 가려진 소매·목둘레를 다른 시점이 보완. 단순 평균 합성이 아니라 참조로만 사용

---

## 한계 (시연에서 솔직히 밝힐 것)

- 가려진 뒷면·봉제·안감은 **정확한 복원이 아니라 추정**
- 니트·레이스·프린지처럼 경계가 복잡한 소재는 마스크 품질이 떨어짐
- 옷과 배경 색이 비슷하면 분할 실패 가능
- 로고·프린트가 가려진 상품은 첫 시연 대상으로 부적합
