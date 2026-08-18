# 에이전트 실행 절차 — 옷 이미지 → 고스트컷 투명 PNG

> **이 문서를 Claude Code(또는 Comfy MCP가 연결된 에이전트)에게 워크플로우 JSON과 함께 주면,
> 사용자가 옷 이미지를 건네는 것만으로 결과가 나오게 하는 절차서입니다.**
>
> 에이전트는 이 문서의 절차를 그대로 따르고, 노드 이름·ID·override 키를 임의로 바꾸지 않습니다.

---

## 0. 에이전트에게 주는 지시

사용자가 옷 이미지(모델 착장 사진)를 1장 이상 건네면, 아래 절차로 각 이미지마다
**투명 배경 고스트컷 PNG 1장씩**을 만들어 사용자에게 전달한다.

- 이미지가 N장이면 워크플로우를 **N번** 실행한다. 워크플로우를 수정해 여러 장을 한 번에 처리하려 하지 않는다.
- **유료 API 노드가 포함되어 있다.** 실행 전 사용자에게 장수와 대략 비용을 알리고 동의를 받는다.
- 노드 ID, class_type, override 키를 추측하지 않는다. 이 문서에 적힌 값을 그대로 쓴다.

---

## 1. 사용할 워크플로우

Comfy Cloud 워크스페이스에 이미 저장되어 있다.

| 항목 | 값 |
|---|---|
| 파일명 | `png.json` |
| 표시 이름 | `패션_고스트컷_누끼PNG_최종` |
| workflow_id | `8ef269d9-eed9-467e-abb1-4023a39782a4` |

워크스페이스에 없다면 함께 제공된 `fashion_ghostcut_final.api.json` 을
`save_workflow` 로 먼저 저장한다.

### 그래프 구조

```
LoadImage(1)
   └→ GeminiNanoBanana2V2(7)   착장 사진 → 고스트컷 생성 (흰 배경)   [유료]
        ├→ PreviewImage(11)     중간 결과 (흰 배경본)
        └→ ImageRemoveAlpha+(12)  RGBA → RGB 변환 (BiRefNet 입력 규격)
             └→ BiRefNetRMBG(8)   배경 제거 → 투명 PNG
                  └→ SaveImage(10)  최종 결과
```

**`ImageRemoveAlpha+`(12)는 반드시 있어야 한다.** Nano Banana 출력을 BiRefNet에 직접
연결하면 채널 수가 맞지 않아 BiRefNet이 실행 중 실패한다.

---

## 2. 실행 절차

### STEP 1 — 이미지 업로드

사용자가 준 로컬 이미지를 Comfy Cloud에 올린다. 이미지 1장마다 1회.

```
upload_file({ file_path: "<로컬 절대경로>", client_os: "<darwin|windows|linux>" })
```

반환된 `name` 값을 기억한다. 이게 다음 단계에서 쓸 파일명이다.

> 로컬(stdio) 세션이면 서버가 업로드까지 알아서 처리한다.
> 원격 세션이면 사용자 셸에서 실행할 PUT 명령이 반환되므로, 그대로 전달해 실행을 요청한다.

### STEP 2 — 실행

**이미지가 1장일 때**

```
run_saved_workflow({
  filename: "png.json",
  input_overrides: {
    "1":  { "image": "<STEP 1에서 받은 name>" },
    "10": { "filename_prefix": "<결과 구분용 이름>" }
  },
  confirm: true
})
```

**이미지가 여러 장일 때 (권장)**

`submit_batch` 로 한 번에 제출한다. item마다 파일명만 다르게 넣는다.

```
submit_batch({
  client_os: "<darwin|windows|linux>",
  items: [
    { tool: "submit_workflow", workflow: <아래 §3 그래프, LoadImage.image = 1번 파일> },
    { tool: "submit_workflow", workflow: <아래 §3 그래프, LoadImage.image = 2번 파일> },
    ...
  ],
  confirm: true
})
```

한 번의 confirm으로 배치 전체가 승인된다.

### STEP 3 — 완료 대기

```
wait_for_job({ prompt_id })        // 단건
wait_for_batch({ batch_id })       // 배치
```

`timed_out: true` 가 오면 다시 호출한다. 이미지 1장당 대략 10~30초.

### STEP 4 — 결과 수집

```
get_output({ prompt_id, client_os, description: "<설명>" })
get_batch_output({ batch_id, client_os })    // 배치
```

반환된 다운로드 명령을 실행해 파일을 받는다.
샌드박스에서 네트워크가 막혀 실패하면 (`403 Host not in allowlist` 등)
명령을 사용자에게 그대로 전달한다.

### STEP 5 — 전달

받은 PNG를 사용자에게 전달한다. 결과가 2종류임을 함께 알린다.

| 출력 노드 | 내용 |
|---|---|
| SaveImage(10) | **최종 투명 PNG** — 사용자에게 줄 결과 |
| PreviewImage(11) | 흰 배경 고스트컷 (중간 단계, 비교·폴백용) |

---

## 3. 워크플로우 그래프 (배치 실행용 원본)

`submit_batch` 의 각 item에 넣을 API 포맷 그래프다.
`"1"` 의 `image` 값만 파일마다 바꾼다.

```json
{
  "1": { "class_type": "LoadImage", "inputs": { "image": "<파일명>" } },
  "7": {
    "class_type": "GeminiNanoBanana2V2",
    "inputs": {
      "prompt": "commercial e-commerce product-only garment image of the SAME top shown in the reference image. Preserve the visible color, material, knit texture, seams, cuffs, hem and neckline exactly as in the reference. Reconstruct only the areas that were occluded by the model's arms, hair and body. Front-facing, centered, symmetrical and physically plausible sleeves and neckline, as if worn by an invisible body (ghost mannequin). Clean even studio lighting, no person, no skin, no hair, no hands, no mannequin, no hanger, no background props, no text, no watermark.",
      "model": "Nano Banana 2 Lite",
      "model.aspect_ratio": "auto",
      "model.resolution": "1K",
      "model.thinking_level": "MINIMAL",
      "model.images.image_1": ["1", 0],
      "seed": 843423400485909,
      "response_modalities": "IMAGE",
      "temperature": 1,
      "top_p": 0.95
    }
  },
  "12": { "class_type": "ImageRemoveAlpha+", "inputs": { "image": ["7", 0] } },
  "8": {
    "class_type": "BiRefNetRMBG",
    "inputs": {
      "image": ["12", 0],
      "model": "BiRefNet-HR",
      "mask_blur": 0,
      "mask_offset": 0,
      "invert_output": false,
      "refine_foreground": true,
      "background": "Alpha",
      "background_color": "#222222"
    }
  },
  "10": { "class_type": "SaveImage", "inputs": { "images": ["8", 0], "filename_prefix": "ghostcut_alpha" } },
  "11": { "class_type": "PreviewImage", "inputs": { "images": ["7", 0] } }
}
```

배치로 돌릴 때는 `seed` 도 item마다 다른 값으로 바꾸는 것을 권장한다
(같은 seed로 다른 이미지를 돌리는 것 자체는 문제없지만, 재시도 시 구분이 쉬워진다).

---

## 4. 조정 가능한 값

사용자가 결과에 불만이면 아래를 바꿔 재실행한다.

| 무엇 | 어디 | 어떻게 |
|---|---|---|
| 결과가 원본과 다름 | 노드 7 `seed` | 다른 값으로 바꿔 재생성 |
| 상의 말고 다른 아이템 | 노드 7 `prompt` | `top` → `pants` / `skirt` / `dress` / `jacket` 으로 문구 수정 |
| 경계에 배경 잔여물 | 노드 8 `mask_offset` | `-1` ~ `-2` |
| 니트·퍼 경계가 거침 | 노드 8 `model` | `BiRefNet-HR` → `BiRefNet-HR-matting` |
| 경계에 흰 테두리(할로) | 노드 8 `refine_foreground` | `true` 유지 (끄면 악화) |
| 해상도를 높이고 싶음 | 노드 7 `model.resolution` | `1K` → `2K` (비용 증가) |

---

## 5. 실패 시 확인 순서

1. **BiRefNet 노드가 실행 중 실패** → `ImageRemoveAlpha+`(12)가 7과 8 사이에 있는지 확인
2. **LoadImage 파일을 못 찾음** → STEP 1 업로드가 실제로 끝났는지, 반환된 `name` 을 그대로 썼는지 확인
3. **결과가 사람이 남아 있음** → 프롬프트의 `no person, no skin, no hair, no hands` 부분이 유지되는지 확인
4. **배치 중 일부만 실패** → `failed[]` 에 담긴 항목만 골라 재실행. 전체를 다시 돌리지 않는다

---

## 6. 반드시 사용자에게 알릴 것

- 노드 7(`GeminiNanoBanana2V2`)은 **유료**다. 이미지 1장당 약 8.6 크레딧.
- 가려졌던 부분(뒷면, 팔에 가린 영역, 안감)은 **복원이 아니라 AI의 추정**이다.
- 상품 등록·납품용으로 쓰려면 실제 상품 자료와 대조 검수가 필요하다.
