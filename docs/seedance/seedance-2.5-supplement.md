# 시댄스 2.5 보충 자료 (스펙 · 플랫폼 · API · 추가 프롬프트 기법)

> `seedance-2.5-ultimate-guide.md`(Higgsfield Soul 팀 실전 분석)를 보완하는 자료입니다.
> 2026-10 기준 웹 자료(서드파티 가이드·API 문서)와 Higgsfield / Comfy Cloud MCP의 실제 모델 스펙을 모았습니다.
> ByteDance 공식 스펙 문서는 아직 일부만 공개되어 있어, 출처마다 다른 수치는 **[불일치]**로 표시했습니다.

---

## 1. 모델 개요와 타임라인

- 2026-06-23 Volcano Engine FORCE 컨퍼런스에서 공개, 2026-07-31 정식 출시(Jimeng/Dreamina 먼저, 8월 초 API).
- 2.0 → 2.5에서 바뀐 핵심

| 항목 | Seedance 2.0 | Seedance 2.5 |
|---|---|---|
| 한 번에 생성하는 길이 | 4~15초 | **4~30초**, 단일 패스 (이어붙이기 아님) |
| 레퍼런스 | 최대 12개 | **최대 50개** (이미지 30 · 비디오 10 · 오디오 10) |
| 편집 | 전체 재생성 | **부분(영역) 편집**, 자연어 편집, 그린스크린 편집 |
| 연장 | — | **앞/뒤 방향 연장** (forward / backward) |
| 오디오 | 네이티브 | 영상과 같은 잠재공간에서 함께 생성, 30초 내내 동기 유지 |
| 해상도 | 최대 1080p / 4K(std) | 480p · 720p · **1080p는 플랫폼에 따라** |
| 프롬프트 준수 | 기준 | ByteDance 주장 약 20% 향상 |
| 기타 | — | 3D 화이트박스 프리뷰(프리비즈), 20개 언어 립싱크, 그래픽 텍스트 가독성 향상, Dreamina 롱비디오 베타(최대 3분) |

- **[불일치] 4K / 10-bit**: 발표 기사(TNW)에는 있었지만 출시본에는 없습니다. 4K는 같은 행사에서 발표된 **2.0 업그레이드** 쪽입니다. 4K가 꼭 필요하면 2.0(std) 또는 업스케일을 씁니다.
- **[불일치] 해상도**: 공개 API(ModelArk)는 480p/720p. **Higgsfield·PixVerse·Picsart·Comfy Cloud 템플릿은 1080p 제공.**

---

## 2. 플랫폼별 실제 파라미터

### 2-1. Higgsfield (`seedance_2_5`) — 가이드의 원 출처 플랫폼

| 파라미터 | 값 |
|---|---|
| `mode` | `t2v` · `omni_reference`(이미지/비디오/오디오 레퍼런스) · `video_edit` · `video_extension` |
| `duration` | 4~30초 (기본 5) — `video_edit`에서는 무시(원본 길이로 과금) |
| `resolution` | 480p / 720p / 1080p (기본 720p) |
| `aspect_ratio` | auto, 21:9, 16:9, 4:3, 1:1, 3:4, 9:16 |
| `generate_audio` | 기본 true → **음악 금지는 프롬프트로** (가이드 4-11) |
| `bitrate_mode` | standard / high |
| `extension_mode` | `forward` / `backward` (video_extension에서 필수) |
| `draft` / `draft_job_id` | **480p 드래프트로 먼저 뽑고 7일 안에 1080p로 확정** → 배치 테스트 비용 절감 |
| 미디어 역할 | `start_image`, `end_image`, `image_references`, `video_references`, `audio_references` |

참고: Higgsfield의 `Ad Multiplier`도 내부적으로 Seedance 2.5입니다. 2.0에는 있던 `genre`(action/horror/comedy/noir/drama/epic) 힌트는 2.5에 없습니다.

### 2-2. Comfy Cloud

- `partner_generate`: `model: "byteplus/seedance-2.0-t2v"` + `params: {"model": "Seedance 2.5"}` (2.5 전용 슬러그 없음)
- 템플릿 (`search_templates(q:"seedance 2.5", limit:20)`)
  - `api_seedance2_5_t2v`, `api_seedance2_5_t2v_1080p`, `api_seedance2_5_i2v_1080p`
  - `api_seedance2_5_r2v` — 이미지 20 · 비디오 6 · 오디오 6
  - `api_seedance2_5_flf2v` — 첫/끝 프레임 보간
  - `api_seedance2_5_video_editing`, `api_seedance2_5_video_extend`
- **주의**: 텍스트만으로 사람을 묘사한 t2v는 ByteDance 초상권 정책으로 이유 없이 `job_failed` 될 수 있습니다. **사람은 사진 레퍼런스(r2v)로** 넣습니다. `*_real_human` 템플릿/KYC는 일반 이미지에는 필요 없습니다.

### 2-3. BytePlus ModelArk 공개 API

- 모델 ID: `dreamina-seedance-2-5-260628`
- `content.role`: `reference_image` · `reference_video` · `reference_audio` · `first_frame` · `last_frame`
- **작업 종류는 프롬프트 동사 + 에셋 role로 자동 판별**됩니다.

| 작업 | 설정 | 고정되는 것 |
|---|---|---|
| T2V / R2V | 비율 + 4~30초 | — |
| 편집 (replace / remove / modify) | `ratio: adaptive`, `duration: -1` | 원본 비율·길이 |
| 연장 (extend / continue) | `ratio: adaptive`, 길이 지정 | 원본 비율 |
| 첫/끝 프레임 | `ratio: adaptive` | 첫 이미지 비율 (두 프레임 비율이 같아야 함) |

- R2V 프롬프트가 편집/연장처럼 읽히면 **편집 작업으로 오분류**되어 파라미터가 거부될 수 있습니다. R2V에서는 replace/extend 같은 동사를 피합니다.
- 출력 MP4 / **MOV**(색 정밀도↑). 편집·연장은 입출력 모두 MOV 권장 → 색·밝기·오디오가 끊기지 않음.
- **negative_prompt 필드가 없습니다.** 금지 사항은 전부 프롬프트 본문 끝에 씁니다.
- 실제 사람 얼굴 업로드는 일부 엔드포인트에서 거부 → 이미지 모델로 시작 프레임을 먼저 만드는 우회법.

### 2-4. 가격 참고 (플랫폼마다 다름)

- Apiframe: 480p $0.15/초, 720p $0.34/초 (10초 720p ≈ $3.40). 레퍼런스 비디오 초도 과금되는 플랫폼이 있습니다.
- 2.0 표준 티어는 약 $0.06/초 → **2.5는 2.0보다 훨씬 비쌉니다.** 짧은 컷·고해상도는 2.0, 긴 연속 테이크·대량 레퍼런스·편집/연장은 2.5.

---

## 3. 레퍼런스 입력 규칙

### 3-1. 태그 문법
- 업로드 순서대로 **유형별로 번호가 따로** 붙습니다: `@Image1, @Image2 … @Video1 … @Audio1`.
  (Higgsfield 프롬프트에서는 `@Image 1`처럼 띄어 쓴 형태도 쓰임 — 가이드 원문 참고)
- 프롬프트의 모든 `@` 태그에는 실제 업로드가 있어야 합니다.
- **이미지 안에 라벨 글자를 넣지 말고** 텍스트에서 이름을 묶습니다.
- 에셋의 **일부만** 쓸 거면 그 부분을 이름으로 지정합니다 ("only the jacket from @Image2").

### 3-2. 권장 개수 (최대치 ≠ 최적)

| 입력 | 최대 | 안정적인 범위 |
|---|---|---|
| 이미지 | 30장 (장당 최대 4K) | **1~8 대상** |
| 비디오 | 10개, 합계 30초 | 1~5개, 각 5~10초 |
| 오디오 | 10개, 합계 30초 | 1~5개, 각 5~10초 |
| 스토리보드 | 이미지 1장에 여러 패널 | 15패널 이하, 단순 선화, 글자 최소 |
| 편집 소스 | — | 원본 20초 미만 + 이미지 1~5장 |

**에셋이 많을수록 오히려 불안정해집니다.** 시작은 "캐릭터/제품 1 + 환경/스타일 1 + 모션 1".

### 3-3. 비디오 · 오디오 레퍼런스 용도
- 비디오: 카메라 무브 복사, 모션/안무, 구도, 그린스크린, 3D 화이트박스(프리비즈) 블로킹.
- 오디오: 목소리(음색), 리듬/타이밍, 앰비언스.
- 예: `A product film for the bottle in @Image1. Open on the camera move from @Video1, then cut to a slow orbit lit like @Image2.`

### 3-4. 스토리보드 / 키프레임
- 스토리보드는 **줄거리 수준 참고**일 뿐 픽셀 일치가 아닙니다. 선화 스타일이 그대로 묻어나지 않게 제외 블록을 둡니다: "Exclude line-art, monochrome, storyboard panel borders."
- 더 엄격히 맞추려면 각 프레임을 **별도 이미지로** 넣고 "Follow these keyframes in order: @Image1 → @Image2 → @Image3"로 시작합니다.

---

## 4. 편집 · 연장 프롬프트

### 편집 (video_edit)
```
Replace the two people in @Video1 with the man in @Image1 and the woman in @Image2,
and replace the courtyard with the bamboo forest in @Image3.
Keep the original actions, rhythm, camera movement and timing unchanged.
Add effects only to the atmosphere (drifting leaves, mist); do not alter faces or wardrobe.
```
- 동사: replace / remove / modify. **"바꾸지 않을 것"을 먼저 못박기** ("Keep the original actions and rhythm unchanged").
- 짧은 제거: `Remove the parked cars from the street.`
- 더빙: `Translate all spoken dialogue into Korean. Adjust lip movement to match. No subtitles.`
- 결과 길이는 항상 원본과 같습니다. 여러 번 시도가 필요할 수 있음.

### 연장 (video_extension)
```
Extend @Video1 by 6 seconds. [이어지는 동작 · 카메라 · 빛 · 사운드]
```
- 이미 끝난 동작을 반복하지 않도록 "The [action] is already complete; do not repeat it." 추가.
- `backward`로 앞쪽에 프리퀄 구간을 붙일 수도 있습니다.
- Seedance 2.5가 만들지 않은 소스는 연장 구간의 음량이 살짝 달라질 수 있음 → 후반에서 맞춤.

---

## 5. 2.5 프롬프트 추가 기법 (가이드에 없거나 보강되는 것)

1. **3층 구조** (ModelArk 권장): `[에셋 매니페스트] → 요약 1문장(주체·장소·사건·스타일·카메라) → 타임코드 상세 → 일관성 노트`.
   Higgsfield 가이드의 13섹션 구조와 호환됩니다. 헤딩보다 **모순 없음**이 중요합니다.
2. **비트 길이**: 30초 테이크는 **8~10초짜리 비트 3개** 정도가 안정적. 구간에 내용이 너무 적으면 모델이 즉흥으로 채우고, 너무 많으면 컷이 추가되거나 비트가 빠집니다.
3. **타임코드 형식**: 정수 초, 구간(`0-3s`)·시점(`At the 2-second mark`)·상대시간. **구간은 빈틈없이 이어지게.**
   빠른 반복 동작(드럼, 펀치 연타)은 타임코드로 쪼개지 말고 "rapid repeated jabs for 3 seconds"처럼 묶어 씁니다.
4. **전환은 트리거 + 방법**: `At the 5-second mark, transition left with a left wipe.`
5. **카메라는 비트당 하나, 사건에 묶기**: "as she stands, the camera slowly pushes in" — 타이머가 아니라 사건이 카메라를 움직이게.
6. **원인 → 결과 → 여파**: "A metal ball strikes the glass; it fractures from the impact point; shards scatter and the base tips over."
7. **가림/퇴장 후 정체성 재고정**: 인물이 가려지거나 프레임 밖에 나갔다 들어오면 특징 2~3개를 다시 적습니다.
8. **상태 연속성**: 흙·상처·젖음·소품 위치는 이야기상 바뀌기 전까지 유지된다고 명시.
9. **조명 공식**: 광원 → 방향 → 질/색 → 효과 ("warm late sun from camera left, cool hallway ambient fill, long shadows across the floor"). "cinematic lighting" 같은 형용사만 쓰지 않기.
10. **오디오 레이어**: Dialogue → SFX → Ambience → Music 순으로 나눠 쓰고, 소리를 물리 동작에 묶습니다.
11. **대사**: 큰따옴표 안에, 화자 + 대사 + 말투 + 동반 행동. 빠른 컷에서는 **한 줄 6단어 안팎**, 짧은 샷에서는 비트당 한 대사. 번역 대사는 길이가 달라지니 타이밍 재확인. 20개 언어 립싱크 지원(한국어 OK).
12. **음악 끄기 문구 (ModelArk 문서 표현)**: `No BGM; generate only environmental sounds and action sounds.` / 완전 무음은 `No audio.` 또는 `generate_audio: false`. 자막 방지: `No subtitles.`
13. **스타일 언어는 하나로**: 서로 당기는 형용사(예: "gritty" + "dreamy pastel")를 같이 쓰지 않기.
14. **끝 상태를 명시**: 마지막 프레임의 동작·구도·감정을 적어야 30초 후반부가 흐트러지지 않습니다 (긴 클립의 대표적 실패: 앞부분만 자세하고 후반이 드리프트).
15. **반복 수정은 변수 하나씩**: 실패 원인을 identity / timing / camera / motion / continuity / sound / 과밀 중 하나로 진단하고 그 줄만 고칩니다.
16. **같은 브리프를 2~3회 돌려 채점** (주체·동작·카메라·사운드 준수) 후 다듬기. Higgsfield `draft`(480p)로 돌리면 저렴.

### 장르별 템플릿 요점 (Kapwing 정리)
- **제품**: 제품 레퍼런스 잠금, 조명과 움직임 분리 지시, 매크로 클로즈업, 패키지·라벨 변형 금지.
- **UGC/토킹헤드**: 아이컨택, 제스처, 의도적 불완전함(핸드헬드 흔들림, 말 더듬기), 대사를 비트별로 분할.
- **애니메**: 캐릭터 레퍼런스와 애니메이션 언어(선, 셰이딩, 2D)를 분리.
- **패션**: 모델 / 의상 / 환경 레퍼런스를 각각 분리, 의상 구조를 샷 내내 잠금.
- **액션**: 원인 → 반응 → 카메라 동기, 물리 제약.
- **POV**: 카메라의 신체 위치, 프레임에 들어올 수 있는 신체 부위, 외부 시점 금지.

---

## 6. 2.0 vs 2.5 선택 가이드

| 상황 | 추천 |
|---|---|
| 15초 이하 단일 컷, 1080p/4K 필요, 비용 중요 | **2.0** (std, 4K 가능) |
| 15~30초 연속 테이크, 대화 씬, 멀티컷 시퀀스 | **2.5** |
| 레퍼런스 12개 초과 (캐릭터 여럿 + 로케이션 + 프롭) | **2.5** |
| 이미 뽑은 클립의 일부만 수정 / 앞뒤 연장 | **2.5** (edit / extension) |
| 장르 힌트 파라미터 활용 | 2.0 (`genre`) |
| 빠른 저가 테스트 | 2.0 Mini 또는 2.5 `draft` |

---

## 출처

- [Apiframe — Seedance 2.5 Complete Guide](https://apiframe.ai/guides/seedance-2-5-guide)
- [Kapwing — How to Prompt Seedance 2.5](https://www.kapwing.com/resources/how-to-prompt-seedance-2-5-a-guide-for-ai-video-creators/)
- [Rendley — How to Prompt Seedance 2.5 (ModelArk 문법)](https://rendley.com/blog/how-to-prompt-seedance-2-5)
- [Empirio Labs — Seedance 2.5 API](https://catalog.empiriolabs.ai/blog/seedance-2-5-api)
- [Picsart — Seedance 2.5 Prompting Guide](https://picsart.com/blog/seedance-2-5-prompting-guide/)
- [PixVerse — Seedance 2.5 Prompt Guide](https://pixverse.ai/en/blog/seedance-2-5-prompt-guide)
- [Miracamp — Seedance 2.5 Explained](https://www.miracamp.com/learn/content-creation/seedance-2-5-bytedance)
- [TNW — 발표 기사](https://thenextweb.com/news/bytedance-seedance-2-5-ai-video-4k-30-seconds)
- [MindStudio — What Is Seedance 2.5](https://www.mindstudio.ai/blog/what-is-seedance-2-5)
- [Dreamina — Seedance 2.5 Video Extension](https://dreamina.capcut.com/seedance/seedance-2-5-video-extension)
- Higgsfield MCP `models_explore` (seedance_2_5 파라미터), Comfy Cloud MCP `get_prompting_guide(topic: seedance-video)`
