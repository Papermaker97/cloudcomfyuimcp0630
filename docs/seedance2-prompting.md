# Seedance 2.0 프롬프팅 가이드 (2026-07 수집)

카메라 움직임 / FX(물·불·연기) / 사실감 3개 축 중심.
프롬프트 예시는 **영문 그대로** 쓰세요 — 모델이 영어 기준으로 학습돼 있습니다.

> ⚠️ **출처 신뢰도에 대해 먼저**: 이 환경의 네트워크 정책이 `seed.bytedance.com`(공식 블로그)을 포함한 대부분의 가이드 사이트를 프록시 단에서 차단했습니다(CONNECT 403). 따라서 아래 내용은 **검색 결과 요약 기반이며, 원문 페이지를 직접 열어 확인한 것이 아닙니다.** 여러 출처에서 반복 확인된 것만 담았고, 엇갈리는 항목은 따로 표시했습니다. 실제 작업 전 공식 문서로 재확인을 권합니다.

---

## 0. 기본 골격

여러 출처가 공통으로 제시하는 **6단계 공식**:

```
Subject → Action → Environment → Camera → Style → Constraints
```

**분량**이 결과를 크게 좌우합니다:

| 용도 | 단어 수 |
|---|---|
| 단일 샷 | **50~70 단어** |
| 타임라인(멀티샷) 구조 | 100~150 단어 |
| 권장 기본값 | 60~100 단어 |

**150 단어를 넘기면 모델이 "평균값"으로 회귀합니다** — 가장 흔하게 본 장면으로 뭉개진다는 뜻입니다. 길게 쓴다고 좋아지지 않습니다.

---

## 1. 카메라 움직임

> 여러 가이드가 **"카메라 움직임 지정이 Seedance 2.0 품질을 올리는 가장 효과적인 단일 요소"** 라고 일관되게 말합니다. 안 쓰면 모델은 **매번 정적인 미디엄 샷으로 기본값 처리**합니다.

### 핵심 원칙 — 샷당 움직임 하나

**움직임을 겹쳐 쓰는 게 지터(떨림)의 1순위 원인입니다.** 세 개 앵글이 필요하면 세 개의 타임라인 비트로 쪼개세요.

### 표현 방식

모호한 표현은 물리적 기준점을 못 줍니다.

| ❌ 나쁨 | ✅ 좋음 |
|---|---|
| move the camera | `smooth dolly forward` |
| camera moves around | `slow pan left` |
| dynamic camera | `smooth dolly follow at eye level` |

### 움직임 종류 (확인된 것)

- **Pan** — 측면 회전으로 인접 정보를 드러냄. **느리게 유지**
- **Dolly / Track** — 피사체 쪽으로/멀어지며/나란히 물리적 이동. 속도 무관하게 시네마틱
- **Push-in** — `camera slow push-in`
- **Orbit** — 피사체 주위 공전
- **Bullet Time / Frozen Moment** — 시간은 멈추고 카메라만 이동

> 공식 가이드가 "8종 카메라 움직임"을 정의한다고 여러 출처가 언급하는데, **전체 목록을 열거한 출처는 못 찾았습니다.** 위 5종만 교차 확인됐습니다.

### 페이싱 단어

Seedance는 **사람이 쓰는 리듬 표현**에 잘 반응합니다: `slow`, `smooth`, `stable`, `gradual`, `gentle`

### 샷 서술 순서

```
카메라 움직임 → 피사체 동작 → 위치 → 사운드
```

---

## 2. FX — 물 · 불 · 연기

Seedance 2.0의 **물리 시뮬레이션이 1.x 대비 크게 개선된 부분**이고, 프롬프트에서 물리 상호작용을 명시적으로 언급하면 그 강점이 살아납니다.

### 원칙 — "결과"가 아니라 "물리 거동"을 써라

`explosion` 한 단어보다, 압력·무게·파편이 어떻게 움직이는지 쓰면 결과가 확연히 달라집니다.

실제 확인된 예시 (원문):

> *"Fire expands with believable pressure, throwing sparks, dust, glowing fragments, and debris forward through the air. Smoke rolls across the floor, debris bounces with convincing weight, and the explosion lights the walls dynamically with flashes of orange and white."*

여기서 작동하는 요소: `believable pressure`, `convincing weight`, **그리고 폭발이 벽을 비춘다는 광원 상호작용**.

> *"Massive fireball expansion, shockwaves ripple through the desert, gigantic rock fragments blast outward, volumetric fire and smoke simulations."*

### 물

```
Massive ocean waves crashing against black volcanic rock cliffs during a storm,
spray exploding upward in slow motion.
```
```
Water droplets freeze mid-air as they splash against a surface.
Slow-motion capture with strong backlight creating rim highlights.
```

**물 표현의 핵심은 백라이트입니다.** 역광이 물방울 가장자리에 rim highlight를 만들어야 물처럼 보입니다. `strong backlight`, `rim highlights`를 빼면 밋밋해집니다.

### 연기 / 대기

파티클은 **모델에게 "가지고 놀 재료"를 주는 것**입니다. 환경 서술에 `rain`, `fog`, `dust`, `smoke`, `sparks`를 넣으세요.

```
mist sitting low between the trunks, water dripping from the needles
```
```
the sky filled with dancing embers and swirling ash
```

`volumetric`을 라이팅에 붙이면 대기 요소 렌더링이 강화됩니다 (`volumetric fire and smoke simulations`, volumetric lighting).

### 슬로우모션이 유리합니다

**AI는 빠른 모션보다 느린 모션을 훨씬 높은 충실도로 생성합니다.** 물/불/연기는 특히 그렇습니다. `slow motion`, `slowly`로 쓰면 디테일이 살고, `fast`를 쓰면 무너집니다.

---

## 3. 사실적인 영상

### 4개의 축

여러 출처가 공통으로 지목: **렌즈 · 광원 · 팔레트 · 카메라 무브**. 이 네 개가 "그냥 시네마틱"과 "진짜 35mm 룩"을 가릅니다.

### 라이팅이 최대 레버

**"라이팅은 단일 품질 요소 중 가장 크다. 반드시 명시하라"** 는 조언이 반복됩니다. 실제 사진 용어를 쓰세요:

```
golden hour backlight / soft overcast daylight / hard neon at night
warm interior lamplight / high-key studio light / candlelight
```

Seedance 2.0은 골든아워·네온·촛불·스튜디오 조명 같은 복잡한 상황에서 **그림자·하이라이트·광량 감쇠(falloff)가 물리적으로 더 정확**해졌습니다.

### 글로벌 모디파이어

프롬프트 끝에 스타일 라인으로 마감:

```
Cinematic 4K, film grain, anamorphic aspect ratio,
color grade: warm shadows and cool highlights, shallow depth of field
```

극사실 지향이면:
```
8K photorealistic, anamorphic widescreen, fine grain, hyperdetailed
```

`35mm anamorphic` 하나만 넣어도 결과가 통째로 바뀐다는 언급이 여러 곳에 있습니다. anamorphic lens flare = 수평 광선 줄무늬.

### 피부가 플라스틱처럼 나올 때

```
no 3D, no cartoon, no VFX
```
이 조합이 극사실 쪽으로 강하게 밀어준다는 보고가 있습니다. (단 — 아래 §5의 부정문 논란을 먼저 읽으세요.)

포어 레벨 디테일이 필요하면:
```
skin pore-level — wet translucent dermis, visible dark capillaries, slick film catching light
```

### 품질 파라미터 세트

```
photorealistic, cinematic composition, premium production design,
high detail textures, realistic physics, natural motion,
professional color grading, depth of field, subtle reflections
```

### 4K를 쓸 이유

4K에서는 **직물·피부 등 미세 텍스처가 또렷하게** 렌더됩니다. 즉 **디테일을 구체적으로 지시한 프롬프트일수록 4K에서 이득이 큽니다.** (앞서 정리한 워크플로우 중 `api_seedance2_0_r2v_4k`가 네이티브 4K + 10-bit 출력이라 그레이딩 파이프라인에 넣을 수 있습니다.)

---

## 4. 타임라인 프롬프팅 (멀티샷)

한 프롬프트로 최대 **5개 샷**까지 스크립팅 가능. 모델이 경계에서 **실제로 컷을 칩니다** (설명 라벨이 아니라 편집 마커로 취급).

두 가지 표기법이 확인됩니다:

```
0–4s: wide establishing shot, static
→ 4–8s: slow push-in to medium
→ 8–12s: orbit around subject
```
```
[00:00-00:05] Shot 1 description
[00:05-00:10] Shot 2 description
[00:10-00:15] Shot 3 description
```

**비트 수를 길이에 맞추세요** — 15초에 3비트가 적정. 프롬프트 맨 위에 **샷 개수 · 총 길이 · 화면비**를 먼저 선언하는 게 권장됩니다.

---

## 5. 함정 / 실패 모드

### 부정문(네거티브) — ⚠️ 출처가 정면으로 엇갈립니다

| 주장 | 출처 성격 |
|---|---|
| 짧은 "패턴 블로커"는 유효. `no shimmer, no flicker, no pulsing` | 프롬프트 가이드 계열 |
| **Seedance 2.0에는 네거티브 프롬프트 필드가 없고**, `no blur` 같은 표현은 오히려 그 요소를 **증가**시킴 | 트러블슈팅 계열 |
| API에는 네거티브 프롬프트가 있다 | API 문서 계열 |

**안전한 접근** — 긍정형으로 바꿔 쓰세요. 이건 어느 쪽 주장이든 안 틀립니다:

| ❌ | ✅ |
|---|---|
| no blur | `sharp, in-focus, high clarity` |
| no camera shake | `steady tripod shot` |
| don't show hands | (아예 언급하지 않기) |

긴 네거티브 목록은 무시되거나 역효과가 난다는 점은 **양쪽 출처가 일치**합니다.

### 지터 / 플리커 3대 원인

1. **카메라 움직임을 여러 개 겹침** ← 1순위
2. **`fast` 키워드** — 자주 화면이 무너짐
3. 빠른 카메라 + 빠른 피사체 + 복잡한 씬을 동시에 요구

### 사지 왜곡

`running fast` 대신 `slowly turning`, `walking naturally`. 느린 동작이 팔다리 붕괴를 막습니다.

### ⚠️ 또 하나 엇갈리는 지점 — 기술 스펙

- 한쪽: `35mm anamorphic` 같은 렌즈 명시가 결과를 크게 바꾼다
- 다른 쪽: Seedance는 **mm 단위 초점거리 같은 기술 스펙보다 사람이 쓰는 리듬 표현(`slow, smooth, gradual`)에 더 잘 반응**한다

제 판단으로는 **"35mm anamorphic" 같은 룩 이름(스타일 토큰)은 먹히고, "85mm f/1.4" 같은 정밀 수치는 큰 의미 없다**는 쪽이 두 주장과 모두 모순되지 않습니다. 다만 이건 **제 해석이고 검증된 사실이 아닙니다.**

---

## 6. 복붙 템플릿

### 단일 샷 (60~70 단어)
```
[SUBJECT] [ACTION], [ENVIRONMENT with atmosphere: fog / dust / embers].
[ONE camera move: slow dolly forward at eye level].
[LIGHTING: golden hour backlight].
Cinematic 4K, film grain, anamorphic widescreen,
color grade: warm shadows and cool highlights, shallow depth of field.
```

### FX 샷 (물리 강조)
```
[EFFECT] expands with believable pressure, throwing sparks and glowing fragments
forward through the air. Smoke rolls across the floor, debris bounces with
convincing weight, and the [EFFECT] lights the surrounding walls dynamically.
Slow motion. Static camera at low angle.
Volumetric fire and smoke simulation, strong backlight, rim highlights.
```

### 멀티샷 타임라인
```
3 shots, 12 seconds total, 16:9.
[00:00-00:04] Wide establishing shot, static. [SCENE + LIGHTING].
[00:04-00:08] Slow push-in to medium. [SUBJECT ACTION].
[00:08-00:12] Slow orbit around subject. [DETAIL].
Cinematic 4K, film grain, consistent lighting across all shots.
```

---

## 출처

[seedance.tv 프롬프트 가이드](https://www.seedance.tv/blog/seedance-2-0-prompt-guide-2026) ·
[seedance.tv 카메라 무브 35종](https://www.seedance.tv/blog/seedance-camera-movement-prompts-2026) ·
[seedance2.so 카메라 무브 가이드](https://seedance2.so/blog/ai-video-camera-movement-prompt-guide) ·
[Apiyi — 공식 가이드 해설(6단계+8종 카메라)](https://help.apiyi.com/en/seedance-2-0-prompt-guide-video-generation-camera-style-tips-en.html) ·
[ByteDance Seed 공식 출시 블로그](https://seed.bytedance.com/en/blog/official-launch-of-seedance-2-0) ·
[theseanclaude — 구조 중심 가이드](https://theseanclaude.substack.com/p/seedance-20-prompt-guide-how-to-get) ·
[Higgsfield 프롬프팅 가이드](https://higgsfield.ai/blog/seedance-prompting-guide) ·
[Higgsfield 4K 초사실 가이드](https://higgsfield.ai/blog/Seedance-4k) ·
[invideo 프롬프트 가이드](https://invideo.io/blog/seedance-2-0-prompt-guide/) ·
[Replicate 블로그](https://replicate.com/blog/seedance-2) ·
[fal.ai 프롬프팅 가이드](https://fal.ai/learn/tools/seedance-2-0-prompting-guide) ·
[WaveSpeed — 플리커/지터 해결](https://wavespeed.ai/blog/posts/blog-fix-flicker-jitter-seedance-2-0/) ·
[PromeAI — 네거티브 큐 제약](https://www.promeai.pro/blog/seedance-2-0-prompt-constraints-flicker-warp/) ·
[seedanceai.cc 트러블슈팅](https://www.seedanceai.cc/guides/seedance-2-0-troubleshooting) ·
[MindStudio 타임라인 프롬프팅](https://www.mindstudio.ai/blog/timeline-prompting-seedance-2-cinematic-ai-video) ·
[videoai.me 멀티샷](https://videoai.me/blog/seedance-2-0-multi-shot) ·
[videoai.me 35mm 룩](https://videoai.me/blog/seedance-2-0-cinematic-prompts) ·
[Fliki 프롬프팅 가이드](https://fliki.ai/blog/seedance-2-prompting-guide)
