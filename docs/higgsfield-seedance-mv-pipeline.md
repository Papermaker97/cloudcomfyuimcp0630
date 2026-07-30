# 힉스필드 + Seedance 2.0 뮤직비디오 풀 파이프라인 (2026-07)

VFX / ComfyUI 제외. Higgsfield MCP 도구 + Seedance 2.0 조합만.

---

## ⚠️ 먼저 알아야 할 결정적 제약 — 음악은 힉스필드로 못 만듭니다

Higgsfield MCP의 `generate_audio` 도구 설명에 **명시적으로** 적혀 있습니다:

> "This tool only generates speech: it cannot generate music or sound effects for general use, and there is no standalone music/SFX model here — **decline general music or sound-effect requests** rather than substituting a speech model."

카탈로그에 `sonilo_music`(음악), `mirelo_text_to_audio`(효과음)가 존재하지만 **게임 생성 파이프라인 전용이며 단독 사용 금지**로 못 박혀 있습니다.

**결론: 곡은 외부에서 조달해야 합니다.** (Suno / Udio / 직접 녹음 / 기존 트랙)
힉스필드는 **"곡이 이미 있다"는 전제**에서 시작하는 영상 파이프라인입니다. 이게 파이프라인 0단계입니다.

---

## 전체 파이프라인 (7단계)

```
0. 곡 확보 (외부) — 필수 선행
   ↓
1. 아티스트 아이덴티티 고정 (Soul ID)
   ↓
2. 마스터 이미지 + 캐릭터 시트
   ↓
3. 샷 리스트 / 콘티 설계
   ↓
4. 퍼포먼스 샷 — 립싱크 (Seedance 2.0)
   ↓
5. B롤 / 인서트 샷 (Seedance 2.0 · Kling 3.0)
   ↓
6. 편집 · 마감 (sandbox_exec ffmpeg · upscale · reframe)
   ↓
7. 배포 (tiktok_publish)
```

---

## 1단계. Soul ID — 아티스트 얼굴 고정

뮤직비디오는 같은 인물이 30~50컷 나옵니다. **여기서 무너지면 전부 무너집니다.**

Soul ID는 Higgsfield의 이미지 모델 **Soul 2.0**에 내장된 캐릭터 학습 시스템으로, 인물 사진을 올려 **지속적 디지털 아이덴티티**를 학습시킵니다. 학습 후에는 스타일 프리셋·조명·카메라 앵글·프롬프트가 어떻게 바뀌어도 얼굴이 고정됩니다.

**학습 조건 (확인된 수치)**
- 동일 인물 사진 **20장 이상**
- 고품질 + **일관된 조명**
- **여러 각도**의 얼굴
- 학습 시간 **약 3~5분**

**핵심 원칙 — Identity vs. Motion 분리**
[OSideMedia 스킬 저장소](https://github.com/OSideMedia/higgsfield-ai-prompt-skill)가 이걸 **하드 룰**로 강제합니다:
> 캐릭터 아이덴티티(얼굴·체형·의상)는 Soul ID 레퍼런스로 **고정**, 모션 연출만 샷별로 변화.

즉 프롬프트에 얼굴 묘사를 다시 쓰지 마세요. Soul ID가 담당합니다. 프롬프트는 **동작과 카메라만** 씁니다.

---

## 2단계. 마스터 이미지 + 캐릭터 시트

1. Soul ID로 **강한 "마스터" 이미지 1장** 생성 — 이후 모든 샷의 기준
2. 캐릭터 시트 확장 (정면/측면/전신/의상 베리에이션)

> Claude MCP 경로: 레퍼런스 사진 하나를 던지면 **캐릭터 시트를 자동 구성**하고, 컨셉을 주면 **씬별 이미지 프롬프트**를 써주고, 각 씬을 다시 **Seedance 2.0 비디오 프롬프트**(카메라 무브·페이싱·분위기 포함)로 변환하는 흐름이 문서화돼 있습니다.

**관련 도구**
- `generate_image` — Soul 2.0 / Soul ID
- `show_characters` — 학습된 캐릭터 확인
- `show_reference_elements` — 레퍼런스 엘리먼트
- `media_upload_widget` — 로컬 사진 업로드 (⚠️ Claude 채팅 첨부는 원격 도구가 못 읽습니다. 반드시 위젯 사용)

---

## 3단계. 샷 설계 — MCSLA 공식

프롬프트 5레이어 구조:

| 레이어 | 요소 | 예시 |
|---|---|---|
| **M** | Model | Kling 3.0 / Seedance 2.0 |
| **C** | Camera | "FPV drone weaving through the alley" |
| **S** | Subject | "A woman in a tactical jacket" |
| **L** | Look | "Cinematic, cold blue shadows, 16:9" |
| **A** | Action | "She sprints, slides under a gate" |

뮤직비디오에서는 **S를 Soul ID로 대체**하고 C·L·A만 씁니다.

### Seedance 2.0의 5가지 프롬프트 모드

| 모드 | 용도 (MV 적용) |
|---|---|
| **Reference-Based** | 마스터 이미지 → 첫 샷 |
| **Continuation** | 앞 샷을 이어받아 다음 샷 — **컷 연결의 핵심** |
| **Expand Shot** | 같은 씬을 길게 |
| **Edit Shot** | 나온 샷 부분 수정 |
| **Transformation** | 변신/전환 연출 |

**Continuation 모드가 뮤직비디오의 뼈대**입니다. 벌스→훅 전환처럼 공간 연속성이 필요한 구간에 씁니다.

---

## 4단계. 퍼포먼스 샷 — 립싱크 ⭐ 가장 까다로운 단계

### Seedance 2.0이 특별한 이유

**그림과 소리를 같은 패스에서 씁니다.** 대사를 **큰따옴표**로 넣으면 모델이 립싱크 + 음성 생성 + 컷 타이밍까지 한 번에 처리합니다. **음소 단위(phoneme-level) 립싱크**, 폴리, 앰비언스, 배경음악이 단일 패스로 합성되며 **후처리 0**입니다.

### 뮤직비디오에서의 실전 규칙 (여기가 함정 밭입니다)

**① 오디오 길이를 정확히 맞추세요**
K-Pop MV 튜토리얼에서 확인된 가장 중요한 제약:
> 세그먼트가 15초면 **정확히 15초** 오디오를 넣어야 합니다.

한 프레임도 어긋나면 립싱크가 밀립니다. ffmpeg로 정확히 잘라서 넣으세요.

**② 레퍼런스 영상은 13초 이하로**
> 립싱크 생성 시 안전하게 가려면 **13초를 넘지 않는** 레퍼런스 영상을 쓰세요.

→ 3~4분 곡을 **13초 이하 세그먼트로 쪼개는 게 기본 전제**입니다. 곡을 통째로 넣는 방식은 없습니다.

**③ 레퍼런스 이미지의 입 상태가 결과를 지배합니다**
> 레퍼런스 이미지가 모델이 보존해야 할 얼굴 구조를 정의합니다. **입술이 반쯤 그림자에 있거나, 축에서 너무 돌아가 있거나, 머리카락·플레어에 부분적으로 가려지면 Seedance가 디테일을 지어냅니다.**

마스터 이미지 선택 시 **입이 정면·균일 조명·비가림** 3조건을 만족하는 걸 쓰세요. 이거 하나로 립싱크 품질이 갈립니다.

**④ 오디오 전달 경로**
Higgsfield `generate_video`에서 **Seedance 오디오 레퍼런스는 `medias`의 `audio` 역할로 전달**합니다. `generate_audio`/`sound` 파라미터는 모델이 선언한 경우에만 씁니다.

### 대안 경로 — Higgsfield Speak
Soul / Soul ID 이미지를 **Speak + 모션 프리셋**으로 퍼포먼스 샷화하는 경로도 있습니다. 오디오 업로드 → 모션 프리셋 선택 → **High quality로 생성**. 캐릭터 일관성이 정적 이미지에서 영상까지 유지됩니다.

---

## 5단계. B롤 / 인서트 샷

### 모델 선택 (MCP 기본 라우팅)

`generate_video` 도구 설명에 명시된 기준:

| 모델 | 언제 |
|---|---|
| **`seedance_2_0`** | **아이덴티티**가 중요할 때 (아티스트 등장 샷 전부) |
| **`kling3_0`** | **멀티샷 / 오디오 / 모션 전이** |
| **`kling3_0_turbo`** | 빠른 t2v, 단일 시작프레임 애니메이션 (B롤 대량 생산) |

**즉 인물 샷 = Seedance, 안무 모션 전이 = Kling 3.0, 배경 인서트 = Kling Turbo**로 나누는 게 도구가 의도한 분업입니다.

### 멀티샷을 한 번에

`cut to` 큐로 여러 샷을 한 생성에 쌓을 수 있습니다. Kling 3.0 멀티샷은 **최대 5개 카메라 셋업**을 한 프롬프트에 스크립팅하고, **하드 컷 + 일관된 조명 + 오디오 매칭**이 유지된 연속 클립을 반환합니다.

### 안무 / 모션

- **`motion_control`** — recast / puppeteer / **motion transfer**. 실제 댄서 영상의 안무를 캐릭터에 이식
- **`animation_actions`** — 3D 리그 애니메이션 라이브러리 **678종** (Dancing 그룹 포함). `preview_url` GIF로 미리보기 후 선택
- **`presets_show`** — 이미지→영상 모션 프리셋 목록

### 해상도 전략
OSideMedia 저장소에 **Resolution Decision Matrix**가 있습니다 — Seedance 2.0 + Cinema Studio 3.x를 걸쳐 480p/720p/1080p를 라우팅하는 표입니다. 테스트는 저해상도, 최종만 고해상도로 가는 게 크레딧 절약의 핵심입니다.

---

## 6단계. 편집 · 마감

### ⭐ sandbox_exec — 이게 파이프라인의 숨은 핵심

Higgsfield에 **ffmpeg가 깔린 클라우드 리눅스 샌드박스**가 있습니다. 뮤직비디오 편집을 여기서 합니다.

**설치된 것**: ffmpeg/ffprobe, ImageMagick, sox, python3(Pillow, **faster-whisper**), node/npm, sharp-cli, Playwright, 캡션 폰트(Metropolis, Montserrat), zip, git, curl, jq

**MV 작업에 쓰는 법**
- 곡을 13초 이하 세그먼트로 **정확히 분할** (4단계 ①②의 전제 충족)
- 생성된 클립들 **concat**
- 오디오 트랙 **얹기**
- **faster-whisper로 가사 타임코드 추출** → 자막/리릭 비디오
- 캡션 번인 (폰트 내장)

**주의**: 샌드박스는 호출 종료 ~10초 후 폐기됩니다. `&&`로 한 호출에 체이닝하고 결과물을 반드시 export하세요. 인터넷 접근은 되므로 curl로 미디어를 가져오고, `media_upload` → `curl -X PUT` → `media_confirm`으로 결과를 올립니다.

### 마감 도구

| 도구 | 역할 |
|---|---|
| `upscale_video` | 2K / 4K 업스케일 |
| `reframe` | 종횡비 변경 — **16:9 본편 → 9:16 숏폼 리포맷** |
| `remove_background` | 컷아웃 / 투명 배경 |
| `outpaint_image` | 이미지 확장 |
| `upscale_image` | 스틸 업스케일 |

`reframe`이 특히 유용합니다 — MV 본편 하나로 틱톡/릴스 버전을 뽑습니다.

---

## 7단계. 배포

### TikTok 직접 게시 — `tiktok_publish`

2단계 구조: `tiktok_prepare_publish` → `tiktok_publish`

**할당량 (계정당, 호출 전 강제)**
- 분당 **최대 5건**
- 24시간 **최대 13건** (둘 다 롤링)
- 거부 시 `retry_after_seconds` 만큼 대기 — 재시도하면 또 거부됩니다

**미디어 제약 (사전 확인 필수)**
- 영상: MP4/WebM/MOV, **≤1GB, 3~600초**, 양변 **≥360px**, **23~60 FPS**
- 사진: **JPEG/WebP만** (PNG 거부 — 힉스필드 이미지 생성은 PNG를 뱉으므로 **변환 필수**), 각 ≤20MB

**필수 동의 플래그**
- `is_aigc: true` — **AI 생성물 공시. 뮤직비디오는 반드시 해당**
- `music_usage_confirmed` — 음원 사용 확인
- `branded_content_policy_confirmed` — 브랜드 콘텐츠일 때

**커머셜 음원**: `tiktok_music_trending`으로 Commercial Music Library 트랙을 붙일 수 있습니다(`music_sound_id`, DIRECT_POST 전용). `music_sound_start`/`end`로 밀리초 단위 트림, `music_sound_volume` / `video_original_sound_volume`으로 밸런스 조정.

> ⚠️ `video_duration_sec`는 VIDEO DIRECT_POST에 필수입니다. 안 넣으면 TikTok이 **비동기로** 거부해서 게시 슬롯만 날립니다.

### 분석
- `virality_predictor` — 바이럴 가능성, 어텐션, 리텐션 리스크, 훅 강도 예측
- `video_analysis_create` — 영상 분석
- `shorts_studio_*` / `personal_clipper_*` — 숏폼 클립 자동 추출

---

## 실패 진단

OSideMedia 저장소의 `FAILURE-MODES.md`에 **Iteration Rule**(체계적 실패 진단), **6-pass 진단 시퀀스**, **next-shot decision tree**가 있습니다. **Physics Language** 섹션은 모션 제약 어휘집입니다.

**Seedance 핵심 원칙 — Intent over Precision**: 미세 디테일보다 서사 방향을 우선하세요. 과하게 세밀한 지시는 역효과입니다.

`production-benchmarks.md`에는 **Hell Grind 90분 칸 출품작**을 기준으로 한 역할별 리테이크 횟수 기대값과 수용률 캘리브레이션이 있습니다.

---

## 핵심 자료

- **[OSideMedia/higgsfield-ai-prompt-skill](https://github.com/OSideMedia/higgsfield-ai-prompt-skill)** — MIT, v3.22.1 (2026-07-26 갱신), 235 stars. **이번 조사 최고 수확.** 20개 서브스킬. `~/.claude/skills/`에 클론하면 Claude가 바로 씁니다.
  - MV 직접 관련: `templates/10-dance-music-performance.md`, Seedance coordination 4종(멀티캐릭터 앵커링, 포지션 템플릿, 톱다운 맵, 2인 예제), 텍스트 오버레이 3종(슬로건/말풍선/**자막**)
  - `skills/higgsfield-seedance/SKILL.md` — Seedance 2.0 디렉터 레퍼런스
  - `skills/higgsfield-soul/SKILL.md` — Soul ID 워크플로우
  - `specs/MODEL-SPECS.md` (2026-07-05) — 모델별 기능 지원표
- [Greg Preece — Higgsfield 뮤직비디오: 자기 복제 + 노래 영상](https://gregpreece.com/articles/higgsfield-ai-music-video-clone-singing-workflow)
- [FrankX — 2026 힉스필드 워크플로우: Soul ID, 시네마틱, Claude MCP](https://www.frankx.ai/blog/ultimate-higgsfield-workflow-2026)
- [Higgsfield — Soul ID 캐릭터 일관성](https://higgsfield.ai/blog/sould-id-best-character-consistency) · [Soul ID 심화](https://higgsfield.ai/blog/Soul-ID-AI-Character-Consistency) · [Soul 2.0](https://higgsfield.ai/soul-intro)
- [Higgsfield — Idea to Talking Character](https://higgsfield.ai/blog/Higgsfield-Google-Bring-Your-Character-to-Life)
- [Higgsfield — AI 틱톡 콘텐츠 파이프라인](https://higgsfield.ai/blog/ai-tiktok-pipeline-2026)
- [Abdullah Yahya — Seedance 2.0 사실적 립싱크 뮤직비디오](https://abdullahyahya.com/2026/05/make-realistic-lip-sync-music-videos-with-seedance-2-0/)
- [500images — Seedance 2.0 K-Pop MV 튜토리얼 (가사·립싱크·푸티지 완성)](https://www.500images.com/blog-seedance-gemini-2026-OGT38L0e)
- [Seedance 립싱크 가이드](https://www.seedance.tv/blog/seedance-2-0-lip-sync) · [립싱크 AI 가이드](https://www.seedance.tv/blog/seedance-lip-sync-ai-guide-2026)

---

## 3분 MV 실전 순서 (요약)

| # | 작업 | 도구 |
|---|---|---|
| 0 | 곡 확보 | **외부** (Suno/Udio/녹음) |
| 1 | 곡을 13초 이하 세그먼트로 정확 분할 | `sandbox_exec` (ffmpeg) |
| 2 | 아티스트 사진 20장+ 업로드 → Soul ID 학습 (3~5분) | `media_upload_widget` → Soul ID |
| 3 | 마스터 이미지 — **입 정면·균일조명·비가림** | `generate_image` |
| 4 | 샷 리스트 (MCSLA, 얼굴 묘사 제외) | — |
| 5 | 퍼포먼스 샷: 세그먼트별 립싱크, 오디오 길이 정확히 일치 | `generate_video` (`seedance_2_0`, medias role `audio`) |
| 6 | 안무 이식 | `motion_control` / `animation_actions` |
| 7 | B롤 대량 | `generate_video` (`kling3_0_turbo`) |
| 8 | 컷 연결 | Seedance **Continuation** 모드 |
| 9 | concat + 오디오 + 자막 | `sandbox_exec` (ffmpeg + faster-whisper) |
| 10 | 업스케일 → 숏폼 리포맷 | `upscale_video` → `reframe` |
| 11 | 바이럴 체크 → 게시 (`is_aigc: true`) | `virality_predictor` → `tiktok_publish` |
