# 패션 착장 → 아이템 누끼/고스트컷 워크플로우

> 신세계라이브쇼핑 방송비주얼팀 요구 예제 ③ (모델 착장 이미지 → 아이템 누끼컷 자동 생성) 구현.
> **설계 원칙: 워크플로우는 "1장 → 1결과". 여러 장은 이 워크플로우를 N번 실행해서 처리한다.**

---

## 상태

- ✅ **Dry run 검증 통과** — 노드 존재·링크 무결성·필수 입력 정상. 실행/과금 없음
- ✅ **Comfy Cloud 저장 완료** — 이름 `패션_상의누끼_1장당1결과`, 파일 `1-1.json`
- ✅ **노드 ID 보존 확인** — 저장 변환 후에도 1~5 그대로 (override 키가 안 깨짐)
- ⬜ 실제 실행은 미수행

---

## 워크플로우 구조 (1장 → 1결과)

```
LoadImage(1) → ClothesSegment(2) ─┬→ SaveImage(3)              top_cutout   [원본 픽셀]
                                  └→ OpenAIGPTImageNodeV2(4) → SaveImage(5) top_ghostcut [AI 추정]
```

**입력 1장, 출력 2장** (보존형 누끼 + 생성형 고스트컷).
서로 다른 옷 N장을 처리하려면 **이 워크플로우를 N번 실행**한다. 워크플로우 안에서 여러 장을 병렬로 처리하지 않는다.

이 구조를 택한 이유:
- 입력마다 옷이 다르므로 결과가 섞이면 안 됨
- 실패한 입력만 재실행하면 됨
- 입력 개수가 몇 장이든 워크플로우는 그대로 (N에 무관)

---

## 여러 장 처리 — MCP 연동 방식

### 방법 A. 한 번의 호출로 N개 job (권장)

`submit_batch`는 최대 50개 job을 한 번에 제출한다. 각 item에 **파일명만 다른 같은 그래프**를 넣는다.

```
submit_batch({
  client_os: "windows",
  items: [
    { tool: "submit_workflow", workflow: <그래프, LoadImage.image = "model_01.png"> },
    { tool: "submit_workflow", workflow: <그래프, LoadImage.image = "model_02.png"> },
    { tool: "submit_workflow", workflow: <그래프, LoadImage.image = "model_03.png"> },
    { tool: "submit_workflow", workflow: <그래프, LoadImage.image = "model_04.png"> }
  ]
})
```

→ `batch_id` 하나와 job_id 4개 반환
→ `get_batch_status(batch_id)` 로 진행 확인
→ `get_batch_output(batch_id)` 로 결과 4쌍 수집
→ 실패한 항목은 `failed[]` 에 분리되어 나옴

**과금 확인은 배치 전체에 대해 1번만** 물어본다 (`confirm: true`).

### 방법 B. 저장된 워크플로우를 입력만 바꿔 순차 실행

```
run_saved_workflow({ filename: "1-1.json", input_overrides: { "1": { "image": "model_01.png" } } })
run_saved_workflow({ filename: "1-1.json", input_overrides: { "1": { "image": "model_02.png" } } })
run_saved_workflow({ filename: "1-1.json", input_overrides: { "1": { "image": "model_03.png" } } })
run_saved_workflow({ filename: "1-1.json", input_overrides: { "1": { "image": "model_04.png" } } })
```

override 대상이 `{"1": {"image": ...}}` 인 것은 클라우드에서 조회해 확인함:

```
customizable_inputs.images = [{ node_id: "1", class_type: "LoadImage", input_name: "image" }]
```

방법 B는 호출이 N번이라 느리지만, **한 장씩 결과를 확인하며 진행하는 시연**에는 오히려 적합하다.

### 결과 파일명 분리

같은 `filename_prefix`를 쓰면 ComfyUI가 자동으로 번호를 붙이지만(`top_cutout_00001_`),
어떤 입력에서 나온 결과인지 명확히 하려면 실행마다 prefix도 함께 override 한다.

```
input_overrides: {
  "1": { "image": "model_02.png" },
  "3": { "filename_prefix": "02_top_cutout" },
  "5": { "filename_prefix": "02_top_ghostcut" }
}
```

---

## 사용한 노드 (이름 변경 금지)

| class_type | 표시명 | 팩 | 과금 |
|---|---|---|---|
| `LoadImage` | Load Image | core | 무료 |
| `ClothesSegment` | Clothes Segment (RMBG) | comfyui-rmbg | 무료 |
| `OpenAIGPTImageNodeV2` | OpenAI GPT Image 2 | core (partner/image/OpenAI) | **유료** |
| `SaveImage` | Save Image | core | 무료 |

노드 4·5를 뮤트하면 **누끼만 무료로** 뽑을 수 있다.

---

## "상의 / 하의" 선택이 구현되는 지점

`ClothesSegment`는 부위별 불리언 스위치를 가진다. **고객사가 요구한 "추출할 아이템 선택"이 이 스위치 그 자체다.** 프롬프트로 지정할 필요가 없다.

사용 가능한 스위치 (전부 기본 `false`):

```
Hat, Hair, Face, Sunglasses, Upper-clothes, Skirt, Dress, Belt, Pants,
Left-arm, Right-arm, Left-leg, Right-leg, Bag, Scarf, Left-shoe, Right-shoe, Background
```

| 추출 대상 | 켤 스위치 |
|---|---|
| 상의 | `Upper-clothes` |
| 하의(바지) | `Pants` |
| 하의(스커트) | `Skirt` |
| 원피스 | `Dress` |
| 상의+하의 동시 | `Upper-clothes` + `Pants` |

시연에서 이 불리언 하나만 바꾸면 상의→하의로 즉시 전환된다.
UI를 만든다면 **이 스위치들이 그대로 토글 버튼이 된다.**

배치 실행 시에도 override로 바꿀 수 있다:
```
input_overrides: { "2": { "Upper-clothes": false, "Pants": true } }
```

---

## 주요 파라미터

### ClothesSegment (노드 2)
| 파라미터 | 현재값 | 범위 | 설명 |
|---|---|---|---|
| `process_res` | 1024 | 128~2048 | 처리 해상도. 높을수록 경계 정밀, VRAM↑ |
| `mask_blur` | 2 | 0~64 | 경계 블러. 니트·헤어 경계 거칠면 3~5 |
| `mask_offset` | 0 | -64~64 | 마스크 확장/축소. 배경 잔여물 있으면 음수 |
| `background` | `Alpha` | Alpha / Color | 투명 배경 출력 |
| `invert_output` | false | | 반전 |

### OpenAIGPTImageNodeV2 (노드 4)
| 파라미터 | 현재값 | 비고 |
|---|---|---|
| `model` | `gpt-image-2` | `gpt-image-1.5` / `gpt-image-1` 선택 가능 |
| `model.size` | `1024x1024` | |
| `model.background` | `transparent` | 고스트컷이므로 투명 |
| `model.quality` | `medium` | low / high 선택 가능. **비용·시간에 직결** |
| `model.images.image_1` | 노드 2의 누끼 | 참조는 최대 16장까지 가능 |
| `n` | 1 | 후보를 여러 개 뽑으려면 2~4 |

---

## 두 결과의 성격 구분 (시연에서 반드시 언급)

| 출력 | 성격 |
|---|---|
| `top_cutout` | **원본 픽셀 보존.** 생성 없음. 가려졌던 부분은 비어 있음 |
| `top_ghostcut` | **AI 추정.** 가려진 부분을 복원한 것이 아니라 그럴듯하게 만들어낸 것 |

상품 등록용으로 쓰려면 고스트컷은 실제 상품 자료와 대조 검수가 필요하다.

---

## 실행 전 준비

1. 입력 이미지를 Comfy Cloud에 업로드
2. `LoadImage`의 파일명을 실제 업로드된 이름으로 교체 (현재 `model_01.png`는 자리표시자)
3. 배치로 돌릴 경우 파일명 목록을 준비

---

## 한계 (솔직히 밝힐 것)

- 가려진 뒷면·봉제·안감은 **정확한 복원이 아니라 추정**
- 니트·레이스·프린지처럼 경계가 복잡한 소재는 마스크 품질 저하
- 옷과 배경 색이 비슷하면 분할 실패 가능
- 로고·프린트가 가려진 상품은 첫 시연 대상으로 부적합
