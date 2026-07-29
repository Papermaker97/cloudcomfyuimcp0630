# 감마 입력용 강의 슬라이드 텍스트

> 사용법: 아래 전체를 Gamma의 `inputText`에 붙여넣고 **Card split = "inputTextBreaks"**, **Text mode = "preserve"** 로 설정하세요. `---` 가 슬라이드 경계입니다. preserve로 안 하면 Gamma가 내용을 재작성합니다.
> 총 34장 / 예상 강의 시간 90~120분

---

# ComfyUI VFX 워크플로우 & Seedance 2.0 프롬프팅

AI 기반 실전 VFX 파이프라인

2026년 7월 기준 · 검증된 워크플로우 12종 + 프롬프트 가이드

---

## 이 강의에서 다루는 것

- **배경 변경** — 피사체는 두고 환경만 바꾸기
- **오브젝트 변경 / 제거** — 그림자까지 지우기
- **FX** — 물·불·연기를 자연스럽게
- **합성 마감** — 매팅, 릴라이팅, 업스케일
- **Seedance 2.0 프롬프팅** — 카메라·FX·사실감

전부 실행 가능한 워크플로우 JSON과 복붙 프롬프트로 제공됩니다.

---

## 시작 전 — 두 가지 실행 환경

**Comfy Cloud**
- 브라우저에서 바로 실행, GPU 불필요
- 크레딧 소모, 구독 필요
- 오늘 다루는 12개 워크플로우가 여기서 동작

**로컬 ComfyUI**
- 24GB VRAM 권장
- 모델 직접 다운로드
- 프로덕션 급 커스터마이징 가능

> 이 강의의 워크플로우는 클라우드 기준입니다.

---

## 오늘의 파이프라인 지도

```
소재 입력
   ↓
① 분리 (매팅 / 세그멘테이션)
   ↓
② 변경 (배경 · 오브젝트 · FX)
   ↓
③ 통합 (릴라이팅 · 컴포지팅)
   ↓
④ 마감 (업스케일 · 리타이밍)
```

**대부분의 실패는 ③에서 납니다.** 바꾸는 건 쉽고, 어울리게 만드는 게 어렵습니다.

---

## 가장 중요한 개념 — 그래프의 두 종류

| | 풀 그래프 | 서브그래프 래퍼 |
|---|---|---|
| 캔버스 | 로더·샘플러·LoRA가 전부 노드 | Load와 Save 사이 노드 하나 |
| 노드 수 | 15개 이상 | 3~12개 |
| 튜닝 | **가능** | 불가 (서버에서 처리) |
| 예시 | SAM3+VACE, Restyle | Bria, Runway, SeedVR2 |

**VFX 파라미터를 직접 만질 거면 풀 그래프를 골라야 합니다.**

---

## 워크플로우 12종 한눈에

**배경** — Bria 알파추출 · Bernini-R 배경교체
**오브젝트** — SAM3+VACE 교체 · VOID 제거 · SCAIL-2 캐릭터교체 · Runway Aleph2
**FX** — VACE 스타일라이즈 · Wan ATI 궤적
**유틸** — SAM3 마스크 · SeedVR2 업스케일 · Depth Anything v3 · 마스크 합성 레퍼런스

파일명이 곧 실행 ID입니다:
`run_template(template_id="templates_shane_change_any_objects")`

---

# PART 1. 배경 변경

---

## 배경 교체의 진짜 문제

배경을 바꾸는 것 자체는 어렵지 않습니다.

**어려운 건 이겁니다:**
- 새 배경의 광원 방향과 피사체의 조명이 안 맞음
- 키잉 엣지에 원래 배경 색이 남음(스필)
- 피사체 그림자가 새 환경에 없음

> 관객은 "배경이 바뀌었다"를 눈치채는 게 아니라 **"조명이 안 맞는다"를 눈치챕니다.**

---

## 전통적 3단 파이프라인

```
① 매팅으로 피사체 분리
② 새 배경 생성
③ 릴라이팅으로 통합
```

**단점** — ①에서 만든 엣지가 끝까지 따라옵니다. 머리카락·모션블러 구간에서 티가 납니다.

---

## 핵심 — Bernini-R 단일 패스

`video_bernini_r_video_editing`

카탈로그엔 "릴라이팅"으로 분류돼 있지만, **기본 프롬프트가 배경 교체 지시문입니다:**

> *"Replace the gray studio backdrop with a daytime urban street... Keep the model's outfit, pose, motion unchanged. **Only the environment behind the subject should change.**"*

**분리 단계가 없으므로 고칠 엣지도 없습니다.**

기반: Wan 2.2 Bernini-R (high/low noise) + lightx2v distill LoRA

---

## 그래도 알파가 필요할 때

Nuke / After Effects로 넘겨서 직접 합성해야 한다면:

`api_bria_remove_video_background_transparent`

- 알파 채널 **WebM** 출력
- **마스크 시퀀스** 동시 출력
- 컴포지팅 툴에 그대로 투입 가능

> 12개 중 유일하게 후속 합성 파이프라인으로 깔끔하게 넘어가는 워크플로우입니다.

---

## 배경 파트 정리

| 상황 | 선택 |
|---|---|
| 빠르고 자연스럽게 | **Bernini-R 단독** |
| 직접 합성 필요 | Bria 알파 → 수동 합성 |
| 모션이 틀어짐 | Runway Aleph2로 대체 |

---

# PART 2. 오브젝트 변경 / 제거

---

## SAM3 + VACE 구조

`templates_shane_change_any_objects` — 30노드 풀그래프

```
입력 영상
  → SAM3 세그멘테이션 (텍스트로 대상 지정)
  → 마스크 확장 / 블러
  → VACE 인페인팅
  → 출력
```

**"red car" 라고 쓰면 빨간 차를 찾아 마스킹합니다.** 로토 작업이 사라집니다.

기반: Wan2.1 VACE 14B + CausVid LoRA + SAM3

---

## 튜닝 포인트

풀 그래프이므로 이 값들을 직접 조정할 수 있습니다:

- **Mask Grow** — 마스크를 얼마나 넓힐지
- **Mask Blur** — 경계 부드러움
- **VACE strength** — 원본을 얼마나 존중할지

> 결과가 어색하면 대부분 **마스크가 너무 타이트해서** 입니다. Grow를 먼저 올려보세요.

---

## 제거의 함정 — 그림자

대부분의 제거 도구는 **물체만 지우고 접지 그림자를 남깁니다.** 그래서 물체가 사라져도 그 자리가 어색합니다.

`utility_void_video_inpainting`

- **그림자·반사 등 물리적 상호작용까지 함께 제거**
- `sam3_text_prompt` 로 대상 지정
- 2패스 구조 (void_pass1 → void_pass2)

---

## 캐릭터 통째 교체

`video_wan21_scail2_character_replacement_int8`

- 원본 **모션은 유지**, 인물만 레퍼런스 캐릭터로
- **Base 패스 + Extend 패스** → 긴 샷도 체인 가능
  (81프레임 세그먼트, 5프레임 오버랩)

> **int8이 fp8보다 품질도 높고 속도도 빠릅니다.** fp8 버전을 고를 이유가 없습니다.

---

# PART 3. FX

---

## FX의 3요소

**① 궤적** — 이펙트가 어디로 움직이는가
**② 질감** — 물·불·연기가 물리적으로 그럴듯한가
**③ 통합** — 씬의 광원과 어울리는가

③을 빼먹으면 "붙여넣은 티"가 납니다.

---

## 궤적 제어

`templates_rob_wan_ati_motion_control`

**Animate Path 노드로 경로를 직접 그립니다.**

- 이미지 위에 마우스로 패스 드로잉
- 생성 영상이 그 경로를 따라감
- 이펙트를 원하는 위치에 배치할 때 유일한 직접 제어 수단

---

## Depth 컨디셔닝 — 프레임 간 미끄러짐 방지

`templates_shane_video_restyle`

```
컨트롤 영상 → Depth Anything v2 → ControlNet
                                      ↓
레퍼런스 이미지 → VACE 인코드 → 샘플러 → 출력
```

**뎁스가 구조를 잡아주지 않으면 스타일이 프레임마다 미끄러집니다.**

---

## 이펙트 LoRA 카탈로그 (Civitai)

| LoRA | 효과 |
|---|---|
| Huge Explosion VFX | 대형 폭발 |
| Singularity Explosion | 블랙홀 + 폭발 |
| Realistic Fire | 사실적 화염 (트리거 `[r3al_f1re]`) |
| Breathing Fire | 입에서 뿜는 불 |
| WAN2.2 Spatial Magic | 공간이 갈라지는 초현실 효과 |
| Hero Run Effect | 질주 스피드 이펙트 |

> LoRA 슬롯이 있는 워크플로우에 끼워 넣어 쓰면 됩니다.

---

# PART 4. 합성 마감

---

## 매팅 — 품질을 가르는 지점

**MatAnyone 2 (CVPR 2026)** — 현재 오픈소스 비디오 매팅 최고 수준

- 플리커 없는 temporal consistency
- 전경 투명 영상 + 알파 매트 **별도 출력**
- 학습된 품질 평가기 내장
- ComfyUI 노드 존재

> 배경 교체 앞단에 넣으면 엣지 품질이 확연히 올라갑니다.

---

## 뎁스 패스의 두 가지 쓰임

`utility_depth_anything3_video_depth_estimation`

**① ControlNet 구동** — 스타일라이즈의 구조 고정
**② 합성용 뎁스 패스** — 안개, 피사계심도, 대기 원근

> 컴포지팅에서 뎁스 패스 하나면 공간감이 완전히 달라집니다.

---

## 업스케일 마감

`utility_seedvr2_3b_int8_upscale_video`

- **1-step diffusion** → 속도/품질 밸런스 최선
- temporal consistency 유지 (프레임 간 떨림 없음)
- `color_correction_method` 노출 → **그레이딩된 플레이트와 매칭할 때 중요**

---

# PART 5. Seedance 2.0 프롬프팅

---

## 왜 Seedance 2.0인가

- **물리 시뮬레이션이 크게 개선** — 물·불·연기·대기
- 복잡한 조명(골든아워, 네온, 촛불)에서 **그림자·광량 감쇠가 물리적으로 정확**
- 4K + 10-bit 출력 → 그레이딩 파이프라인 투입 가능
- 한 프롬프트로 **최대 5샷** 스크립팅

---

## 기본 골격 — 6단계 공식

```
Subject → Action → Environment → Camera → Style → Constraints
```

**분량이 결과를 좌우합니다:**

| 용도 | 단어 수 |
|---|---|
| 단일 샷 | **50~70** |
| 타임라인 멀티샷 | 100~150 |

> **150단어를 넘기면 모델이 "평균값"으로 회귀합니다.** 길게 쓴다고 좋아지지 않습니다.

---

## 카메라 — 가장 효과적인 단일 요소

카메라 무브를 지정하지 않으면 **매번 정적인 미디엄 샷**이 나옵니다.

| ❌ | ✅ |
|---|---|
| move the camera | `smooth dolly forward` |
| camera moves around | `slow pan left` |
| dynamic camera | `smooth dolly follow at eye level` |

**모호한 표현은 물리적 기준점을 주지 못합니다.**

---

## 카메라 — 샷당 하나만

**움직임을 겹쳐 쓰는 것이 지터(떨림)의 1순위 원인입니다.**

앵글이 3개 필요하면 → **타임라인 비트 3개로 분리**

주요 무브:
`Pan` · `Dolly / Track` · `Push-in` · `Orbit` · `Bullet Time`

페이싱 단어: `slow` `smooth` `stable` `gradual` `gentle`

---

## FX 프롬프팅 — 결과가 아니라 물리 거동

`explosion` 한 단어로는 부족합니다.

**실제로 작동하는 예시:**

> *"Fire expands with **believable pressure**, throwing sparks, dust, glowing fragments forward. Smoke rolls across the floor, debris bounces with **convincing weight**, and the explosion **lights the walls dynamically** with flashes of orange and white."*

핵심: 압력 · 무게 · **광원 상호작용**

---

## 물 — 백라이트가 전부

```
Massive ocean waves crashing against black volcanic rock cliffs
during a storm, spray exploding upward in slow motion.
```
```
Water droplets freeze mid-air as they splash against a surface.
Slow-motion capture with strong backlight creating rim highlights.
```

**`strong backlight`, `rim highlights`를 빼면 물처럼 안 보입니다.**
역광이 물방울 가장자리를 살립니다.

---

## 연기 · 대기 — 파티클 재료를 줘라

환경 서술에 넣으세요: `rain` `fog` `dust` `smoke` `sparks` `embers` `ash`

```
mist sitting low between the trunks, water dripping from the needles
```
```
the sky filled with dancing embers and swirling ash
```

`volumetric`을 붙이면 대기 렌더링이 강화됩니다.

---

## 슬로우모션이 유리하다

**AI는 빠른 모션보다 느린 모션을 훨씬 높은 충실도로 생성합니다.**

- ✅ `slow motion`, `slowly turning`, `walking naturally`
- ❌ `fast`, `running fast`

`fast` 키워드는 화면을 무너뜨리고 사지 왜곡을 만듭니다.
**물·불·연기는 특히 슬로우모션에서 디테일이 살아납니다.**

---

## 사실감 — 4개의 축

**렌즈 · 광원 · 팔레트 · 카메라 무브**

이 넷이 "그냥 시네마틱"과 "진짜 35mm 룩"을 가릅니다.

마감 스타일 라인:
```
Cinematic 4K, film grain, anamorphic widescreen,
color grade: warm shadows and cool highlights,
shallow depth of field
```

---

## 라이팅이 최대 레버

**반드시 명시하세요.** 실제 사진 용어를 씁니다:

```
golden hour backlight
soft overcast daylight
hard neon at night
warm interior lamplight
high-key studio light
candlelight
```

피부가 플라스틱처럼 나올 때: `no 3D, no cartoon, no VFX`

---

## 타임라인 멀티샷

모델이 경계에서 **실제로 컷을 칩니다** (설명 라벨이 아니라 편집 마커).

```
3 shots, 12 seconds total, 16:9.
[00:00-00:04] Wide establishing shot, static.
[00:04-00:08] Slow push-in to medium.
[00:08-00:12] Slow orbit around subject.
Cinematic 4K, film grain, consistent lighting across all shots.
```

**비트 수를 길이에 맞추세요** — 15초에 3비트가 적정.

---

## 실패 모드 3가지

**① 카메라 움직임 중복** ← 지터 1순위 원인
**② `fast` 키워드** ← 화면 붕괴
**③ 빠른 카메라 + 빠른 피사체 + 복잡한 씬 동시 요구**

셋 다 "욕심"에서 나옵니다. **하나씩 분리하세요.**

---

## ⚠️ 논쟁 중인 지점 — 네거티브 프롬프트

출처가 정면으로 엇갈립니다:

- "짧은 패턴 블로커는 유효" (`no shimmer, no flicker`)
- "네거티브 필드가 없고, `no blur`는 오히려 블러를 **증가**시킴"

**안전한 방법 — 긍정형으로 치환** (어느 쪽이든 안 틀림)

| ❌ | ✅ |
|---|---|
| no blur | `sharp, in-focus, high clarity` |
| no camera shake | `steady tripod shot` |

긴 네거티브 목록이 역효과라는 점은 양쪽이 일치합니다.

---

## 복붙 템플릿

**단일 샷**
```
[SUBJECT] [ACTION], [ENVIRONMENT + atmosphere: fog / dust / embers].
[ONE camera move: slow dolly forward at eye level].
[LIGHTING: golden hour backlight].
Cinematic 4K, film grain, anamorphic widescreen, shallow depth of field.
```

**FX 샷**
```
[EFFECT] expands with believable pressure, throwing sparks and glowing
fragments forward. Smoke rolls across the floor, debris bounces with
convincing weight, and the [EFFECT] lights the surrounding walls.
Slow motion. Static camera at low angle. Volumetric simulation,
strong backlight, rim highlights.
```

---

## 실습 과제

**과제 1** — 인물 영상 하나를 골라 Bernini-R로 배경만 교체. 라이팅이 맞는지 확인.

**과제 2** — SAM3+VACE로 오브젝트 하나 교체. 마스크 Grow 값을 3단계로 바꿔 비교.

**과제 3** — Seedance 2.0으로 물 또는 불 FX 샷 생성. **물리 거동 서술 있음 / 없음** 두 버전을 만들어 비교.

> 과제 3이 이 강의의 핵심입니다.

---

## 오늘의 요약

**VFX 워크플로우**
- 배경 교체 = 라이팅 문제. Bernini-R 단일 패스가 답
- 오브젝트는 SAM3+VACE, 제거는 그림자까지 지우는 VOID
- 풀 그래프만 튜닝 가능

**Seedance 2.0**
- 카메라 무브는 **샷당 하나**
- FX는 **결과가 아니라 물리 거동**으로 서술
- 물은 **백라이트**, 모션은 **슬로우**
- 50~70단어, 150단어 넘기지 말 것

---

## 자료

**워크플로우 JSON 12종** — 파일명 = 실행 ID
**Seedance 프롬프트 가이드** — 복붙 템플릿 3종
**이펙트 LoRA 링크** — Civitai / HuggingFace

질문 받겠습니다.
