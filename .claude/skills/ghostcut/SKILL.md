---
name: ghostcut
description: 모델 착장 사진에서 옷만 뽑아 상품 단독 누끼(고스트컷) PNG를 만든다. 사진 여러 장을 주면 장당 결과 1개씩 만들어 돌려준다. "이 옷 사진 누끼 따줘", "고스트컷 만들어줘", "착장컷에서 상의만 뽑아줘", "모델컷을 상품컷으로" 같은 요청에 사용한다. 상의·하의·스커트·원피스·자켓을 지정할 수 있다.
---

# 고스트컷 생성

모델이 옷을 입은 사진에서, 사람은 지우고 **옷만 남긴 상품 단독 이미지**를 만든다.
가려졌던 소매·목둘레는 AI가 채워 넣어 마네킹에 입힌 것처럼 만든다. 배경은 투명 PNG.

## 이 스킬이 지켜야 할 것

- 사진이 N장이면 **워크플로우를 N번 실행**한다. 워크플로우를 고쳐서 한 번에 여러 장을 처리하려 하지 않는다.
- 노드 ID·class_type·override 키를 **추측하지 않는다.** 아래 적힌 값을 그대로 쓴다.
- **유료 노드가 들어있다.** 실행 전 장수와 예상 크레딧(장당 약 8.6)을 알리고 동의를 받는다.
- 한 장이 실패해도 나머지는 계속 진행한다. 실패한 것만 다시 돌린다.

---

## 1. 워크플로우 확인

Comfy Cloud에 이미 저장되어 있다.

| 항목 | 값 |
|---|---|
| 파일명 | `png.json` |
| 이름 | `패션_고스트컷_누끼PNG_최종` |
| workflow_id | `8ef269d9-eed9-467e-abb1-4023a39782a4` |

`list_saved_workflows({ name: "고스트컷" })` 로 존재를 확인한다.
없으면 이 폴더의 `workflow.api.json` 을 `save_workflow` 로 먼저 저장한다.

### 그래프

```
LoadImage(1)
  └→ GeminiNanoBanana2V2(7)      착장 → 고스트컷(흰 배경)   [유료]
       ├→ PreviewImage(11)        중간 결과
       └→ ImageRemoveAlpha+(12)   RGBA→RGB 변환
            └→ BiRefNetRMBG(8)    배경 제거
                 └→ SaveImage(10) 최종 투명 PNG
```

`ImageRemoveAlpha+`(12)를 빼면 BiRefNet이 **실행 중** 실패한다. 채널 수가 안 맞기 때문.
dry run으로는 안 잡히니 절대 빼지 말 것.

---

## 2. 실행 절차

### STEP 1 — 업로드

사진 1장마다 1회.

```
upload_file({ file_path: "<절대경로>", client_os: "darwin" })
```

반환된 `name` 을 기억한다. 이게 STEP 2에서 쓸 값이다.

### STEP 2 — 실행

**여러 장이면 `submit_batch` 로 한 번에** (권장, confirm 1회로 전체 승인)

```
submit_batch({
  client_os: "darwin",
  items: [
    { tool: "submit_workflow", workflow: <§4 그래프, image=1번파일, seed=랜덤> },
    { tool: "submit_workflow", workflow: <§4 그래프, image=2번파일, seed=랜덤> },
    ...
  ],
  confirm: true
})
```

**한 장이면 `run_saved_workflow`**

```
run_saved_workflow({
  filename: "png.json",
  input_overrides: {
    "1":  { "image": "<업로드된 name>" },
    "7":  { "seed": <랜덤 정수> },
    "10": { "filename_prefix": "<원본파일명>_ghostcut" }
  },
  confirm: true
})
```

### STEP 3 — 대기

```
wait_for_batch({ batch_id })     // 배치
wait_for_job({ prompt_id })      // 단건
```

`timed_out: true` 면 다시 호출한다. 장당 10~30초.

### STEP 4 — 수집

```
get_batch_output({ batch_id, client_os: "darwin" })
get_output({ prompt_id, client_os: "darwin", description: "<설명>" })
```

반환된 다운로드 명령을 직접 실행해 파일을 받는다.
샌드박스 egress가 막혀 실패하면(`403 Host not in allowlist` 등) 명령을 사용자에게 그대로 전달한다.

### STEP 5 — 전달

받은 PNG를 사용자에게 보여준다. 결과가 2종류임을 함께 알린다.

- **SaveImage(10)** = 최종 투명 PNG (사용자에게 줄 것)
- **PreviewImage(11)** = 흰 배경 중간본 (비교·폴백용)

---

## 3. 아이템 지정

사용자가 상의/하의 등을 지정하면 **프롬프트의 명사만** 바꾼다.

| 사용자 표현 | 프롬프트에 넣을 단어 |
|---|---|
| 상의, 티셔츠, 니트, 스웨터 | `top` |
| 하의, 바지, 팬츠 | `pants` |
| 스커트, 치마 | `skirt` |
| 원피스, 드레스 | `dress` |
| 자켓, 아우터, 코트 | `jacket` |

기본 프롬프트의 `the SAME top shown in` 에서 `top` 자리를 교체한다.
지정이 없으면 사진을 보고 판단하되, 애매하면 사용자에게 묻는다.

---

## 4. 워크플로우 그래프 (배치용 원본)

`"1"` 의 `image` 와 `"7"` 의 `seed` 만 매 항목마다 바꾼다.

```json
{
  "1": { "class_type": "LoadImage", "inputs": { "image": "<업로드된 파일명>" } },
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
  "10": { "class_type": "SaveImage", "inputs": { "images": ["8", 0], "filename_prefix": "ghostcut" } },
  "11": { "class_type": "PreviewImage", "inputs": { "images": ["7", 0] } }
}
```

---

## 5. 결과가 마음에 안 들 때

| 증상 | 조치 |
|---|---|
| 형태가 원본과 다름 | 노드 7 `seed` 를 바꿔 재생성 |
| 엉뚱한 옷이 나옴 | 노드 7 `prompt` 의 아이템 단어 확인 (§3) |
| 경계에 배경이 남음 | 노드 8 `mask_offset` 을 `-1` ~ `-2` |
| 니트·퍼 경계가 거침 | 노드 8 `model` 을 `BiRefNet-HR-matting` 으로 |
| 경계에 흰 테두리 | 노드 8 `refine_foreground` 를 `true` 유지 (끄면 악화) |
| 해상도를 높이고 싶음 | 노드 7 `model.resolution` 을 `2K` 로 (비용 증가) |

---

## 6. 실패 시 확인 순서

1. BiRefNet이 실행 중 실패 → `ImageRemoveAlpha+`(12)가 7과 8 사이에 있는지
2. LoadImage가 파일을 못 찾음 → STEP 1 업로드가 끝났는지, 반환된 `name` 을 그대로 썼는지
3. 결과에 사람이 남음 → 프롬프트의 `no person, no skin, no hair, no hands` 가 유지되는지
4. 배치 중 일부 실패 → `failed[]` 항목만 재실행. 전체를 다시 돌리지 않는다

---

## 7. 사용자에게 반드시 알릴 것

- 가려졌던 부분(뒷면, 팔에 가린 영역, 안감)은 **AI의 추정**이지 복원이 아니다.
- 패턴·봉제선·로고·색상이 실제 상품과 달라질 수 있다.
- 상품 등록·납품 전에는 실제 상품 자료와 대조 검수가 필요하다.
