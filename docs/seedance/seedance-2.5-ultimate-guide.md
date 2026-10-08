# 시댄스 2.5 궁극의 가이드
### Higgsfield Soul 팀의 실제 프로젝트·블로그 프롬프트를 분석해 정리한 제작 매뉴얼

> **출처**: higgsfield.ai/@higgsfield.soul의 프로젝트(Blackpine, Soul Angel, Princess Glow Up, Today Is Your Day, Dusk, Whimsy Bag, Rewind Club)와 블로그 7개(@oz_woo, Breakfast for Two, @p.jinjoooo, Paper World, The Last Draft, Cat Guardian, @haakim_jsn)에 공개된 브리프와 실제 생성 프롬프트.
> 프롬프트 예시는 원문 그대로 쓸 수 있게 영어로 두고, 설명은 한국어로 달았습니다.

---

## 0. 한 장 요약

1. **영상보다 먼저 레퍼런스를 고정한다.** 캐릭터 시트, 빈 로케이션, 프롭, 군중 무드보드를 이미지 모델로 만들고 `@Image N`으로 태그해 모든 샷에 재사용합니다.
2. **룩과 규칙은 프로젝트 내내 바꾸지 않는다.** `Style Prefix`와 `Visual Constraints` 문단을 모든 프롬프트 맨 앞에 똑같이 넣습니다.
3. **프롬프트는 섹션으로 쪼개 쓴다.** SCENE CONTEXT → ACTIVE REFERENCES → FORMAT MODE → LOCATION MAP → FIRST FRAME → OPTICS → CAMERA → ACTION TIMING → PHYSICS → LIGHTING → AUDIO → ACTING TASK → POSITIVE LOCKS 순서입니다.
4. **모델에게 아무것도 맡기지 않는다.** 인원수, 화면 좌우, 시선 방향, 소품 상태, 시간대, 컷 위치, 대사 한 줄 한 줄까지 다 적습니다.
5. **음악은 명시적으로 금지한다.** 시댄스는 기본적으로 음악을 깔기 때문에 `No music. Only SFX and dialogue.`를 넣고, 음악은 후반에 붙입니다.
6. **연속성은 이미지로 이어간다.** 완성된 테이크의 마지막 프레임(또는 마지막 3~4초)을 다음 샷의 레퍼런스로 넣습니다.
7. **한 번에 완성하려 하지 않는다.** 배치로 여러 번 돌리고, 각 테이크에서 가장 좋은 몇 초만 골라 이어 붙입니다.

---

## 1. 전체 파이프라인

```
[스크립트 작성]
     ↓
[레퍼런스 라이브러리 구축]  ← Soul 2.0 / Soul Cinema / Nano Banana Pro / GPT Image 2 / Seedream 5.0 Pro
  · 캐릭터 시트 (상태별로 여러 버전)
  · 빈 로케이션 스틸 (필요한 각도별로)
  · 프롭 제품 사진
  · 군중/엑스트라 무드보드
  · 키비주얼 / 타이틀 카드
     ↓
[Style Prefix + Visual Constraints 확정]
     ↓
[샷별 시댄스 2.5 프롬프트 작성]  ← Claude 채팅에 스크립트와 실패 기록을 넣어두고 작성
     ↓
[배치 생성 → 가장 좋은 구간 고르기 → 마지막 프레임을 다음 샷에 넣기]
     ↓
[후반: 사운드 정리·효과음 보강, 음악 작곡, 컬러, 편집]
```

**실제 프로젝트 규모 참고**

| 프로젝트 | 길이 | 샷 구성 | 해상도/비율 | 모델 비중 |
|---|---|---|---|---|
| Blackpine | 약 80초 파일럿 | 8~15초 샷을 연속성으로 연결 | 1080p, 16:9 | Seedance 2.5 69.5%, Soul V2 14%, Nano Banana Pro 12% |
| Soul Angel | 에피소드당 약 2분 | 대화 중심 멀티컷 | 1440×1080, 4:3, 24fps | Soul + Seedance 2.5 |
| Today Is Your Day | 약 80초 | 8~15초 샷 | 4K 16:9 | Seedance 2.0 |
| Rewind Club | 14.5초 | 약 29컷, 컷당 약 0.45초 | 1920×1080 | Soul Cinema + Seedance |
| Whimsy Bag | 33초 | 3~5샷 | 1080×1920 세로 | Seedance 2.5 |

**폴더 구성** (Today Is Your Day 방식): 씬별 폴더(시도한 버전을 모두 보관), `Final Keyframes`(다음 샷으로 넘길 고정 프레임), `Final Generations`(최종 선택본), `Failed Generations`(얼굴 드리프트, 카메라 앞을 지나간 군중, 스마트폰으로 바뀐 폴더폰, 립싱크 실패 같은 실패작). 실패작을 남겨두면 다음 프롬프트에 반영할 수 있습니다.

---

## 2. 프리프로덕션: 레퍼런스 자산 고정하기

모든 프로젝트 브리프가 공통으로 강조하는 원칙은 이것입니다. **한 초라도 생성하기 전에 반복 등장하는 모든 요소를 만들어 고정한다.**

### 2-1. 캐릭터 시트

**구성 형식**
- **3분할**: 전신 정면 / 전신 후면 / 얼굴 클로즈업 (Soul Angel, Princess Glow Up)
- **4분할**: 정면 / 측면 / 후면 / 포트레이트 (Blackpine, Today Is Your Day)
- 배경은 **이음매 없는 중립 회색 스튜디오 배경**에 그림자를 최소화하고, 포즈는 **중립 자세**(체중 고르게, 팔은 옆으로, 손은 비움)로 둡니다.

**간단한 수정형 프롬프트** (Nano Banana Pro / Seedream / GPT Image 2에 사진 여러 장과 함께)
```
make the character sheet of first girl like second photo
where she looking forward, side, back and her portrait photo
she wears the full outfit from third photo in a relaxed pose,
remove the cross necklace from her neck and ribbon
and make her hairstyle with two braids
```
```
make a simple character sheet of her @Image 1 front back view and a portrait
no lines or text or frame keep her appearance
she wears this outfit @Image 2
```

**정밀형 프롬프트의 핵심 구조** (Soul Angel의 GPT Image 2 3분할 시트에서 정리)
1. 레이아웃: "Three-panel character sheet of one woman in a single 16:9 image, three equal vertical panels... she is the only person in the image."
2. 얼굴: "take the face exactly from Image 1 — facial structure, eyes, brows, nose, lips, skin tone"
3. 의상: "take the complete outfit worn by the woman in Image 2 and put it on her exactly as it is... refit to her body"
4. 체형: 키, 비율, 목 길이까지 적기 ("175 cm tall, slim, long slender neck, small head-to-body ratio")
5. 패널 정의: 각 패널의 크롭 범위
6. 포즈 / 배경 / 카메라 (전신은 약 3m 표준 렌즈, 포트레이트는 짧은 망원)
7. **룩과 컬러 그레이드를 작품과 맞추기**: 시트도 작품 그레이드(예: early-2000s film-still)로 찍어두면 영상에서 톤이 튀지 않습니다.
8. 헥스 컬러 값 명시

**측면 뷰 함정** (Nano Banana Pro 4분할 남성 시트): 측면 패널에서 모델은 고개를 카메라 쪽으로 돌리려는 경향이 있습니다. 이렇게 막습니다.
```
PROFILE — the body turned a full 90 degrees... his HEAD IS TURNED EXACTLY AS FAR AS HIS BODY:
his face is in full profile... He does not turn his head back toward the camera.
Only one side of his face is visible, the far eye hidden.
```
그 밖에 "the four are NOT the same size", "all three sets of feet on exactly the same ground line", "No panel borders, no dividing lines"처럼 레이아웃도 강하게 고정합니다. 소재가 핵심인 의상은 질감의 **스케일**까지 적습니다 ("small and delicate — no large sheets of leaf").

**상태별로 버전을 나누기**
- Blackpine: 아이비를 **목에 표식이 없는 버전**과 **초승달 표식이 있는 버전** 두 가지로 고정했습니다. 표식이 드러나는 정확한 비트 전에 새어 나오지 않게 하기 위해서입니다.
- Princess Glow Up: 엔주를 **화장기 없는 후드티 버전**과 **글로우업 스타일 버전** 두 개의 턴테이블로 고정했습니다.
- Dusk: 소녀를 **교복 턴테이블**과 **집에서 입는 옷** 사진으로 따로 고정했습니다.
- Today Is Your Day: 대니의 재킷을 **마른 상태**와 **얼룩진 상태**로 따로 고정했습니다.

### 2-2. 로케이션 스틸 (Soul 2.0 / Soul Cinema)

**원칙**
- **사람 없이 비워서** 찍습니다 ("No people, no traffic", "completely empty of people").
- **광각, 방 구석에서, 딥 포커스**로 공간 전체를 한 프레임에 담습니다 ("photographed from a corner", "floor, walls and ceiling all clearly visible").
- 재질, 노후 정도, 소품 배치를 아주 구체적으로 적습니다.
- **헥스 컬러 팔레트**를 함께 적습니다.
- 카메라 질감도 적어둡니다 ("consumer digital camera or smartphone, deep focus, visible digital noise in darker areas").
- 대본에 필요한 **각도별로** 따로 찍습니다 (Today Is Your Day: 뷔페 테이블 쪽, 소파 쪽, 틴슬 벽 쪽).
- 시간대는 영상에서 덮어쓸 수 있습니다. Blackpine은 낮 거리 사진을 쓰고 영상 프롬프트에서 "override its grey daytime look"으로 황혼으로 바꿨습니다.

**로케이션 프롬프트 골격**
```
A wide-angle [interior/exterior] shot from [corner/position] captures [space] on [time/weather].
[Walls/floor/ceiling materials with wear]. [Furniture with positions]. [Props on surfaces].
[What's visible through windows/doors]. [Light sources and how light falls].
The colour palette consists of [...] #hex, #hex, #hex.
[Camera character: deep focus, wide-angle distortion, digital noise / film grain].
The atmosphere is [mood], with no people present.
```

**인페인트로 정리하기** (Seedream 5.0 Pro, 마스크 기반): 레퍼런스에 원치 않는 물건이 있으면 영상에 그대로 나옵니다. 미리 지워두세요.
```
Fill the masked areas so they read as clean, empty background... Continue the wall's even paint
and the ceiling line straight through the patch... No trace, outline or shadow of the removed
objects remains. Match the surrounding image exactly in exposure, colour temperature,
sharpness, softness and film grain. Change nothing outside the masked areas.
```
요소를 고칠 때는 "Improve only the quality... Do not make them bigger, denser or fuller"처럼 **바꾸지 말아야 할 것**을 먼저 적습니다.

### 2-3. 프롭 (제품 사진 스타일)

흰 배경이나 중립 배경 위의 **제품 사진**으로 만듭니다 (Nano Banana Pro 4K).
- 구조: `[SCENE] Product photograph ... on a clean pure white background` → `[COMPOSITION]` → 부위별 섹션(`[CORD]`, `[PENDANT]`)
- 크기, 재질, 문양, 마모, 상태까지 적습니다 (예: 깨지는 거울 → "the glass breaks out but the dented metal compact body survives").
- 화면 상태가 바뀌는 프롭은 **상태별로** 만듭니다 (폴더폰 LCD: 운세 화면 / "Wish granted!" 화면).

### 2-4. 군중·엑스트라

- **군중 무드보드**: "5 girls in cute pastel extravagant outfits... on white background", 9명 그룹샷 등으로 군중의 의상 계열을 고정합니다.
- 이유: 맥시멀한 의상이 많을 때 **고정되지 않은 엑스트라가 주연의 실루엣을 슬쩍 빌려 입습니다** (Princess Glow Up 브리프).
- 레퍼런스가 없는 조연은 프롬프트에서 **서로 확실히 다르게** 묘사합니다 (@oz_woo: "Friend A: short black bob with blunt bangs... Friend B: long wavy auburn hair half-up...", "neither resembling the protagonist").

### 2-5. 키비주얼·스틸컷·연속성 프레임

- **연속성 앵커 프레임도 태그합니다**: 생성 결과 중 이후 기준이 되는 프레임(카페테리아 마스터 투샷, 계단 그룹 블로킹 등)은 `@image19+` 같은 식으로 태그해서, **다시 등장하는 장면을 기억이 아니라 이미지로 재구성**합니다.
- **9:16 키아트**와 **타이틀 카드**(예: 핫핑크 마키 글자)도 그래픽 자산으로 미리 만듭니다.
- **스틸을 먼저 만들고 애니메이트하기** (Rewind Club): 이미지 모델로 스틸을 대량으로 뽑고, 고른 프레임을 시댄스의 첫 프레임으로 씁니다. 3장에서 자세히 다룹니다.

---

## 3. Style Prefix와 Visual Constraints

모든 프로젝트가 **프롬프트 맨 앞에 고정 문단 두 개**를 넣습니다. 프로젝트마다 내용은 다르지만 프로젝트 안에서는 절대 바꾸지 않습니다.

### 3-1. Style Prefix 구성 요소
1. **매체·포맷**: 16mm, 35mm 컬러 네거티브, 2000년대 콤팩트 디카, 480i TV, 2D 잉크 애니메이션
2. **빛**: 블루아워, 확산된 흐린 날, 하이키
3. **색**: 팔레트 단어와 대비 (milky low-contrast, lifted blacks)
4. **질감**: 그레인, 할레이션, 디퓨전 글로우
5. **템포**: calm unhurried stillness
6. **렌즈 느낌**: 50mm feel, rectilinear, shallow DoF
7. **카메라 원칙**: flat true horizon, no tilt, handheld or locked
8. **레퍼런스 장르/감독 톤**: "in the restraint of Eggers / Aster"
9. **비율**: 4:3, 1440×1080, horizontal landscape

### 3-2. 장르별 Style Prefix 예시

**그라운디드 16mm 다크 판타지 (Blackpine)**
```
Grounded 16mm dark-fantasy look — deep blue-hour dusk, milky low-contrast color, muted warm-cool
palette, volumetric fog, real film grain, calm unhurried stillness. Naturalistic, intimate,
physically grounded genre cinema in the restraint of Eggers / Aster, no spectacle for its own sake.
Handheld or locked, flat true horizon, no tilt. Horizontal landscape framing.
```

**2000년대 중반 35mm 패션 드라마 (Soul Angel)**
```
Mid-2000s 35mm feature-film photography on fine-grain colour negative, warm-timed print:
honey-caramel skin and wood, clean daylight at the windows, gently lifted blacks, glossy
fashion-magazine saturation on dark fabric, chrome and lips. Light diffusion-filter glow —
highlights bloom softly, skin reads smooth, gentle halation on bright edges. Rectilinear lenses,
straight verticals. Shallow depth of field with creamy round bokeh wherever a face is the subject.
Real 24 fps motion blur. 4:3, 1440x1080.
```

**K-드라마 파스텔 (Princess Glow Up)**
```
Soft K-drama pastel look — bright diffused daylight, palette of peach, powder blue, cream, gold and
pink marble, gentle low contrast, natural skin texture with visible pores and no beauty smoothing,
very light grain, unhurried stillness. 50mm lens feel, soft background bokeh. Naturalistic,
intimate. Steady, level, well-composed framing — flat true horizon, no tilt; the camera holds
still and lets a moment breathe.
```

**차가운 미스터리 (Dusk)**
```
Cold mystery look — grey fog-bound atmosphere, soft diffused overcast light, muted desaturated
palette with cool blue-grey tones, lifted blacks, fine 35mm grain, quiet unhurried stillness.
50mm lens feel, soft background bokeh. Naturalistic, intimate. Steady, level, well-composed
framing — flat true horizon, no tilt; the camera holds still and lets a moment breathe.
```

**2000년대 초 미국 멀티캠 시트콤 (Today Is Your Day)**
```
Early-2000s American multi-camera teen sitcom look — bright high-key lighting, soft frontal key
from above, faces fully lit with no deep shadows, candy-saturated color with the party's
warm-pink cast... Locked-off tripod coverage at eye level, clean two-shots and reaction
close-ups, no handheld, no push-ins. Slightly heightened performances with a still beat after
every punchline for laugh-track room.
```

**2D 잉크·붓 애니메이션 (Whimsy Bag)**
```
2D hand-drawn animation in an ink-and-brush illustration style. Fine confident black ink linework
with hand-drawn imperfection and varied weight... High-contrast look on a warm cream / bone paper
ground, muted desaturated accents... The whole frame sits on one aged-paper surface: subtle grain,
faint smudges, analog print texture over characters, props and corridor alike.
```

### 3-3. Visual Constraints 공통 골격

```
Photoreal live-action — no 3D render, no game-engine gloss, no cartoon or anime read.
Hard positive locks in every prompt: headcounts, screen geography, prop states, character
proportions, screen-direction, wardrobe continuity and lip-sync are written into the prompt,
not left to chance. Faces blink and breathe, never masklike; identities, hair, and wardrobe
match their @tag references every shot.
[프로젝트 고유 규칙들]
Only scripted English lines are spoken, one voice at a time; lips still otherwise.
4K UHD, sharp clarity, stable lighting, consistent frame rate, clean picture.
```

**프로젝트별로 추가된 고유 규칙 (실패 경험에서 나온 것들)**
- **로케이션 확장 금지**: "Locations render only what the location reference shows and are never widened, re-furnished or made grander." (Princess Glow Up, Dusk, Soul Angel 모두에서 **가장 큰 드리프트 원인**이었습니다)
- **가구 개수 고정**: "Exactly one table exists in the room and nothing stands against the walls." (앉을 사람이 생기면 모델이 책상을 하나 더 만들어 냅니다)
- **글자 제거**: "Every printed surface is blank — no title, masthead, word, numeral, logo or maker's mark." (잡지 표지에 실제 제호가 생기는 문제)
- **노출 정직하게**: "the windows are not blown out and the trees outside keep their colour."
- **촬영 장비 금지**: "No studio lamp, softbox, reflector, stand or cable is visible in any corner."
- **슬로모션 규칙**: "Slow motion appears only where scripted and returns to full speed on a hard cut, never a ramp."
- **대사 규칙**: "Every line is delivered on camera by the speaker with their mouth in frame... no line is heard while the speaker is out of frame." / "Accents are locked per character and never borrowed between them."
- **표식 위치**: "The crescent mark sits low on the left side of Ivy's neck below the ear, stays hidden until its reveal beat, and never drifts."
- **변신 묘사**: "the transformation is never shown mid-morph — off-screen only, before/after states." (Dusk)
- **소품 혼동 방지**: "Enju's round frames and Ryan's rectangular frames never swap."
- **의미 있는 소품의 연출 억제**: "Ryan's watch stays an ordinary object in ordinary light — no glint, no bloom, no push-in."
- **배경 인물**: "Background students stay in soft focus inside their own conversations and never look at camera."

---

## 4. 시댄스 2.5 프롬프트 해부 (섹션별 작성법)

### 4-1. SCENE CONTEXT
씬 전체를 **2~5문장 줄거리**로 씁니다. 무엇이 일어나고 어디서 끝나는지까지 적습니다.
```
SCENE CONTEXT
In deep blue-hour twilight two friends step out of a small-town café and walk away from it
straight toward camera down the middle of the empty foggy street, one continuous distant wide
shot. Wind sets the chimes under the café awning ringing behind them. Held as a single static
far shot the whole time.
```
- 반전이 있으면 반전까지 씁니다 ("mid-sentence Ivy turns to her friend and finds her gone").
- 등장인물이 많으면 "Named characters: ... Every other person is an anonymous background extra."라고 정리합니다.

### 4-2. ACTIVE REFERENCES: 레퍼런스마다 역할 지정
가장 중요한 섹션입니다. **각 이미지가 무엇을 통제하고 무엇을 통제하지 않는지** 적습니다.

**캐릭터**
```
@Image 1 — identity anchor for IVY: pale skin, dark center-parted hair in two long braids...
She is on the SHOP side of the pair = screen-LEFT of frame. 100% matches the reference.
```
- 외형을 **텍스트로도 한 번 더** 적습니다 (이미지와 텍스트가 서로 보강).
- 끝에 `100% matches the reference.`
- 화면 위치를 같이 적습니다.
- 성격과 감정 상태 한 줄: "sarcastic by reflex, gentle by nature", "braced for trouble"

**얼굴과 스타일링을 다른 이미지에서 가져올 때** (@oz_woo)
```
@Image 5: the protagonist's FACE. Her face, facial proportions, eye shape, skin tone and physique
come only from @Image 5... Ignore the pink lace jacket, the sea-screen background, the bangles
and the pose in @Image 5.
@Image 1: the protagonist's STYLING only, 100% matches the reference; the face in @Image 1 is
not used... Ignore the background, daylight, pose...
```

**캐릭터 시트를 쓸 때 꼭 넣을 문장** (Soul Angel 브리프): 시트는 단색 배경에서 찍었기 때문에, 이 문장이 없으면 **씬이 시트의 배경과 조명을 따라갑니다**.
```
...take only the face, the hair and the clothing from it, never its lighting, background or
camera angle. Ignore the studio grey background, the multi-panel layout and the neutral standing pose.
```

**로케이션**
```
@Image 3 — location anchor: [핵심 지리 요약]. Controls geography, surfaces and color only;
time of day is dusk, darker than the reference.
```
```
@Image 2: the bedroom. Controls layout, furniture, materials, practical lights and warm
photographic color only. Does not control camera angle.
```
```
@Image 1 — LOCATION LOCK: the exact room from this image, unchanged.
```
레퍼런스보다 공간이 더 커야 하면 이렇게 적습니다: "reference is a MOOD/DETAIL guide only — the actual room is LARGER... Don't copy the reference framing or its cramped scale." (Dusk)

**상태가 바뀌는 레퍼런스**
```
@Image 2 — IVY neck-mark reference: ... Use ONLY for the reveal in CUT 5; source of truth for
the mark's shape, placement and skin rendering.
```
그리고 ACTION TIMING 안에서 이렇게 전환합니다: "On the now-bare skin — switch identity control to @Image 2 — a thin crescent-moon mark..."

**인서트 전용 레퍼런스**: "@BOY_COLLAR — used ONLY inside the 0.6s flash insert... No face, no head, no eyes."

**군중 레퍼런스**: "@Image 2 — the models, each 100% matching her own figure in the reference... MODEL ONE: the woman in the black strapless romper..., fourth standing figure from the left" (그룹 사진에서 위치로 지목)

### 4-3. FORMAT MODE
샷 구조를 한 문단에 선언합니다.
```
FORMAT MODE
Controlled five-segment sequence with four HARD CUTs. Cold open on a close-up hook. Real-time
motion. One living character only. SFX-driven, no music bed, no dialogue, no subtitles.
Horizontal landscape.
```
- 컷 수와 컷 종류: `HARD CUT`, `INSERT CUT`, `MATCH CUT`, "No dissolves, no fades."
- `Real-time motion`: 시댄스는 그대로 두면 몽환적으로 느려지는 경향이 있습니다.
- 인원수 (`Two living principals only`)
- 대사 유무, 음악 유무, 자막 금지, 화면 방향
- 비트 구분: "Beat one, 0.0s to 9.0s: ... Beat two, 9.0s to 26.5s: ..."

### 4-4. LOCATION MAP
**카메라 기준으로** 공간의 지도를 그립니다.
```
LOCATION MAP
The camera sits low at the near end of the street. The café is at the FAR end behind the girls...
The sidewalk and shopfronts run down screen-LEFT; the wet asphalt road, field and fence run
screen-RIGHT. From the first frame every light is on...
```
**복잡한 실내는 방위로** 정리합니다 (Soul Angel):
```
LOCATION MAP (compass as in image_1)
West wall: the tall arched windows... North wall: the glass partition... East side: the white
seamless backdrop... South end: the white Parsons table. RAPHAEL sits at the table's north
corner... the models' mark is on the runway 4 m north of RAPHAEL...
All cameras stay on the east side of the RAPHAEL–mark line: RAPHAEL and the table screen-left,
the mark and the line screen-right... RAPHAEL faces north toward the mark, so his gaze to the
mark is screen-right; the models on the mark face south toward him, so their faces turn screen-left.
```
여기서 핵심은 **180도 규칙**을 직접 적는 것입니다 ("All cameras stay on the east side of the A–B line"). 그래야 컷이 바뀌어도 시선 방향이 뒤집히지 않습니다.

**스케일 고정** (Paper World): "Scale, constant through the whole film: ... her crown top reaches the top of the castle door arch; the cottage eave is at her head height..."

### 4-5. FIRST FRAME AND SPATIAL BLOCKING
**첫 프레임을 정확히 묘사합니다.** 빈 설정샷으로 시간을 낭비하지 않게 합니다.
```
Open already on both girls mid-walk and mid-conversation, no empty establishing frame.
IVY occupies left third, x 38%, y 58%, walking into depth. JESS occupies right of her,
x 55%, y 58%, half-turned toward Ivy as she talks. The black cat sits curbside deep-MG,
x 62%, y 70%.
```
- **x%, y% 좌표**로 인물 위치를 지정합니다.
- 전경(FG), 중경(MG), 배경(BG)을 나눕니다.
- "The first visible frame already contains [인물] and the full crowd."
- 프레임에 없어야 할 것: "Nobody else is in frame.", "No cat, no animals, no extra people anywhere in frame."
- 훅으로 시작: "Open TIGHT, no empty establishing frame: a close-up of hurried motion... The hook is the first thing on screen."

### 4-6. OPTICS: LENS LOCK
**대각선 화각(°)으로** 렌즈를 지정하고, 세그먼트 안에서는 바꾸지 않습니다.
```
LENS LOCK CUT 1 = 27° short telephoto, ~65–85mm feel, tight close-up, shallow depth of field.
LENS LOCK CUT 2 = 56° wide, ~24–28mm feel, full-room distant shot, deep focus, static.
...No drift mid-segment.
```

**화각 치트시트** (실제 프롬프트에서 쓰인 값)

| 대각 화각 | 느낌 | 쓰임새 |
|---|---|---|
| 18~20° | classic telephoto, 85~100mm | 익스트림 클로즈업, 손·디테일 인서트, 표식 리빌 |
| 27~29° | short telephoto portrait, 65mm | 얼굴 클로즈업, 리버스샷, 대화 커버리지 |
| 34~40° | medium, 35~40mm | 투샷, 걸으며 따라가기 |
| 46~47° | standard normal | 미디엄 와이드, 마스터샷, 신발 높이 로우앵글 |
| 50~56° | normal-wide, 28mm | 방 전체 와이드, 고양이 시점 POV |
| 62~63° | moderate wide | 무중력·오빗, 군중 속 따라가기 |
| 75~84° | wide | 원거리 설정샷, 지면 레벨, 항공샷 |

- 거리와 높이를 같이 적습니다: "camera 2.5 m east of him at seated eye level", "Camera low, about 0.4 m off the wet asphalt".
- 초점: "Deep focus, the whole street sharp", "face and hands razor-sharp, windows a warm blur".
- **반복되는 앵글은 똑같이 다시 쓰게** 합니다: "Identical framing every time.", "reuse the same frame every time they return, without any change."
- 왜곡 금지: "classic wide rectilinear character, straight lines undistorted, no fisheye", "no zoom, no lens breathing, no flare".

### 4-7. CAMERA
움직임을 **한 단어 + 강도**로 지정합니다.
```
Handheld throughout, real human operator: soft breath, micro weight-shift, tiny corrections,
3–5% movement intensity, locked horizon, subject stays readable.
CUT 1: fast handheld close, whip-down with the drop, then snaps still on the shattered glass.
CUT 2: locked-off wide, no movement, holds on the frozen figure.
CUT 4: slow tight push toward the neck for the reveal.
```
- 고정: "Locked tripod, fully static, locked horizon. The camera never moves and never changes framing."
- 움직임 비율: "slow 3% pan", "slow 2% push-in that settles before he stands"
- 핸드헬드 질감 (@oz_woo): "Gentle vertical bobbing from footsteps, sideways sway, small left-right corrections... Camera moves come from a human body, never from smooth gimbal or crane motion."
- 정확한 오빗 (@p.jinjoooo): "exactly 360 degrees... at a constant 45 degrees per second with no easing, no acceleration, no zoom and no change of height or radius"
- 항공샷 (Dusk): "begins already in motion on frame one and is still in motion on the last frame... never stops, never rebounds, never accelerates, never whips, never orbits and never rolls."
- 가장 중요한 규칙을 섹션 제목에 박아두기도 합니다: `CAMERA MOVEMENT (THE MOST IMPORTANT RULE)`

### 4-8. ACTION TIMING
**초 단위 타임라인**입니다. 시댄스 프롬프트의 중심입니다.
```
CUT 1 — 0.0s to 3.0s (BEDROOM — the hook)
0.0s: tight close-up, hurried energy — Ivy's hands sweep up a black jacket and house keys...
1.4s: her forearm/elbow clips the silver compact mirror at the edge of the surface; it tips...
2.0s: the camera whips down with it; the compact strikes the dark plank floor...
HARD CUT 1 at 3.0s
```
- 세그먼트마다 **이름**(예: `the hook`, `the freeze`)을 붙여 의도를 전달합니다.
- 컷 시점은 독립된 줄로 씁니다: `6.5s HARD CUT`
- **대사 타이밍**: "Line begins within 0.5s.", "(5.2s to 6.0s)"처럼 대사마다 구간을 줍니다.
- **분할 지점 표시**: "HARD CUT 2 at 7.0s [recommended split point → Gen 1 ends here]". 긴 시퀀스를 여러 번 생성으로 나눌 위치를 미리 정해둡니다.
- **원인 → 결과 순서를 강제**합니다 (Breakfast for Two):
  ```
  ONE CONTINUOUS medium close-up... He takes a real mouthful of coffee, lowers the cup... and
  visibly swallows. ONLY AFTER the sip and swallow, the salty taste registers... The wince starts
  AFTER drinking, never while merely looking at the coffee. No cut during this sip-then-reaction action.
  ```
- **들어오고 나가는 동선**: "Seedance obeys entrance/exit blocking." 첫 프레임에 있는 손이 중간에 필요 없으면 "the hand immediately exits frame right and stays out... in the final second the hand enters from frame right and snatches the red pair."
- **숨은 컷**으로 의상 바꾸기 (@p.jinjoooo): 전경의 선풍기 날개가 화면을 덮는 순간에 컷 → "[03s] Blade fully covers her — hidden cut — Look B, already flowing into a new pose."
- **매치 컷**으로 장소 이동 (Princess Glow Up): 명함이 화면을 꽉 채운 같은 프레임에서 조명과 앰비언스만 바꿔 식당에서 거리로 넘어갑니다. "card, hands, framing, scale, angle and lens completely unchanged, and only the quality of the light on the card and the ambience replaced."
- **반복 개그**: 같은 프레이밍, 같은 타이밍을 반복하고 반응만 점점 차갑게 만듭니다 ("three identical model frames joined by MATCH CUTs with his voice hardening off screen").
- **사운드 컷**: "18.5s HARD CUT — abrupt cut into sudden dead silence, the ambient bed and chatter gone in an instant."
- **4벽 깨기**: "Ivy turns front and lifts her eyes straight into the lens... holding the stare."
- **루프**: "SEAMLESS 8-SECOND LOOP: the camera completes precisely one revolution and returns to its exact starting position."

### 4-9. PHYSICS
**무게, 지연, 관성**을 씁니다. 리얼리티의 대부분이 여기서 나옵니다.
```
Jacket: soft heavy fabric, swings and settles with follow-through. Keys: small metal, brief jingle.
Compact mirror: a ~7cm silver metal disc with real mass; it tips over the edge, tumbles, hits
hardwood with a hard clink... Braids carry weight and settle a half-beat behind head turns.
Door: real hinge swing and a firm latch click. Grounded weight transfer throughout.
```
- 공식: **[대상] + [재질·질량] + [동작] + [지연·정착]**
- 단골 표현: "hair lags half a step behind the body", "bouncing a beat after the body", "real pendulum motion", "heel contact and weight transfer on every step"
- 무중력: "light things rise faster and sway more, heavier things rise slower and rotate lazily", "hair behaves like it is suspended in water"
- 바뀌면 안 되는 것도 적습니다: "The cap stays on her head. The skirt stays down and does not lift or flare up."

### 4-10. LIGHTING
- **키 라이트의 방향과 성격**: "Low late-afternoon sun through the tall windows on screen-left is the key light."
- **샷마다 유지할 것**: "The side sunlight from screen-left stays on her in every shot."
- **시간대 고정**: "Deep blue-hour twilight from the first frame and held constant across all cuts — never daytime, never full black night, always dusk."
- **레퍼런스 덮어쓰기**: "Use @Image 3 for geography and materials only; override its grey daytime look."
- 조명 변화는 **변하지 않는 기준**과 함께 적습니다: "When a lamp dies the girls drop into cooler blue fog-shade... but the ambient twilight base never changes."
- 필름 반응: "16mm film response", "faces naturally modelled, not flat studio fill"

### 4-11. AUDIO / VOICE
**음악 금지 블록** (Soul Angel 브리프의 핵심 교훈): 시댄스는 클립에 기본으로 음악을 깝니다. 금지할 것과 **허용할 소리 목록**을 모두 적습니다.
```
AUDIO
No music. Only SFX and scripted dialogue. No score, no underscore, no pads, no ambient musical
tone, no swell on an entrance. Allowed sounds only: voices, room tone, [구체적 효과음 목록].
```
- 효과음은 **시점까지** 적습니다: "Door bell rings twice at 0.5s and 1.0s, the door clicks shut..."
- 대사 규칙: "Only the quoted lines are spoken, in English, close and clean... Lips still when not speaking."
- 화자별 목소리 정의:
  ```
  VOICE — IVY: soft, low-volume, slightly husky, breathy at the edges, mid-to-low register,
  unhurried American delivery. "Okay." is easy, agreeing without much thought.
  VOICE — MRS. MARLOWE: rich, warm contralto... British-inflected English, precise consonants.
  ```
  → 음색, 음역, 억양, 그리고 **대사 한 줄마다 어떻게 말하는지**까지 적습니다.
- 억양 고정: "speaks English with a strong, elegant Parisian French accent in every line"
- 한국어 대사도 됩니다 (Cat Guardian): `"괜찮아. 내가 도와줄게."` + "All dialogue is Korean, with natural delivery and accurate lip synchronization. Exactly the three written lines are spoken."
- 군중 소리: "never forming understandable words"
- **예외**: 의도적으로 음악을 넣은 경우도 있습니다 (Breakfast for Two의 "Original quiet romantic jazz underscore below speech", Cat Guardian의 TV 판타지 음악). 원칙은 **후반에서 음악을 붙이는 것**이고, 생성 단계에서 넣을 때는 장르와 위치를 정확히 지정합니다.

### 4-12. ACTING TASK (연기 연출)
감정 이름을 주는 대신 **동기 → 목표 → 장애물 → 전술**을 줍니다.
```
ACTING TASK — IVY (the work is in her eyes):
SCENE DIRECTION (shared, unspoken): an ordinary morning, the good kind.
MOTIVE: this café is the one place that still feels like her grandmother's.
GOAL: be greeted, be normal.
TACTIC: she looks for MARLOWE before she looks at anything else and checks her face for the usual welcome.
(Safety: gaze always engaged in the task — never a frozen, glassy stare; natural blink cadence.)
```
- 한 씬의 모든 인물에게 **같은 SCENE DIRECTION**, **각자 다른 MOTIVE/TACTIC**을 줍니다.
- 몸싸움 직전 씬 (Dusk): "nobody plays 'anger', both play NOT losing it / winning the ground"
- 순간별 전술 (@haakim_jsn): "— first crystal — her eyes snap down to her own cheek... — the last stones — she comes back to the lens and holds it"
- **Safety 줄은 항상 넣습니다.** 죽은 눈과 마네킹 같은 얼굴을 막아줍니다.
- 미세 표정은 수치로: "the brow lifts a few millimeters", "turns his head only slightly toward REBECCA, about fifteen degrees"

### 4-13. POSITIVE LOCKS
마지막에 **절대 규칙을 다시 정리**합니다. 부정문보다 긍정문 위주로 씁니다.
```
POSITIVE LOCKS
Two people total and never more; no animals, no cat anywhere in frame. IVY 100% matches @Image 1,
on the SHOP side of the pair, screen-LEFT... JESS 100% matches @Image 2, on the ROAD side,
screen-RIGHT... Never swap their faces, hair, sides or wardrobe. One single continuous distant
wide low shot, locked static, no cut, no push-in. Every street lamp and every shop window stays lit
from first frame to last. Blue-hour dusk locked for the entire shot; no time-of-day drift.
Maintain face and clothing consistency. High detail. Natural smooth movements. Sharp clarity.
Stable lighting. Clean picture. 16mm film, horizontal landscape framing, low contrast, real grain.
```
**잠가야 할 항목 체크리스트**
- [ ] 총 인원수 ("never more")
- [ ] 각 인물의 화면 좌우, 절대 바꾸지 않기
- [ ] 의상과 액세서리 전체 목록 유지
- [ ] 소품 상태와 위치 ("The typewriter stays on her right and the cocoa mug on her left in every shot")
- [ ] 소품 이동 시점 ("The black jacket stays on IVY's right forearm until 9.0s")
- [ ] 숨겨야 할 것 ("The crescent mark stays covered by IVY's left braid for the whole clip")
- [ ] 엑스트라 규칙 ("tiny, soft and far in the deep background, never near the girls, never duplicated")
- [ ] 동물·특정 인물의 등장/부재 ("Jess is completely absent from the first frame after the 18.5s cut — never partially in frame, never a silhouette")
- [ ] 시간대와 조명 유지
- [ ] 컷 시점 ("Cut lands exactly at 4.5s")
- [ ] 마무리 품질 문구 (아래 고정 꼬리말)

**고정 꼬리말** (거의 모든 프롬프트 끝에 붙어 있습니다)
```
Maintain face and clothing consistency. High detail. Natural smooth movements. Sharp clarity.
Stable lighting. Consistent frame rate. Clean picture.
```

---

## 5. 연속성: 샷과 샷 잇기

1. **마지막 프레임 이어받기**: 완성된 샷의 마지막 프레임을 다음 샷의 레퍼런스(또는 첫 프레임)로 넣습니다. 자세, 얼룩, 컵 상태, 군중 밀도가 그대로 이어집니다.
2. **마지막 3~4초를 @video 레퍼런스로**: Blackpine은 완성된 테이크의 마지막 몇 초를 비디오 레퍼런스로 넣어 포즈, 프레이밍, 빛을 정확히 이어받았습니다.
3. **앵커 프레임 태그**: 다시 등장하는 장면의 마스터샷은 이미지로 태그해 재사용합니다.
4. **긴 씬 분할**: 15~30초짜리 다중 세그먼트 프롬프트에 `[recommended split point]`를 표시하고 나눠 생성합니다.
5. **가장 좋은 구간만 쓰기**: "batch after batch, with the best seconds pulled from each pass and stitched together."
6. **씬 전환을 소리로 숨기기**: Blackpine은 문 닫히고 열리는 소리 뒤에 씬 전환을 숨겼습니다.

---

## 6. 단일 사진 애니메이트 템플릿 (Soul 2.0 사진 → 시댄스)

블로그 협업 작품들(@haakim_jsn, @p.jinjoooo)은 **잘 만든 사진 한 장 + 초현실 아이디어 하나**로 8초짜리 컷을 만듭니다.

```
SCENE CONTEXT
Take the uploaded photo as the base and animate it. [한 문장 컨셉: 무엇이 변하고 무엇이 그대로인가]

FRAME AND IDENTITY LOCK
Keep her exactly as in the photo: [얼굴, 머리, 의상, 액세서리 전체 목록].
Keep the scene: [배경 요소 전체 목록]. All the objects stay exactly as pictured — [소품 목록].

FORMAT MODE
Single continuous take, ~8 seconds, vertical framing. [Fully static locked camera / Static-to-subtle camera].

OPTICS
LENS LOCK = [50–62]° diagonal field of view, matching the original photo's framing and perspective exactly.

ACTION TIMING
0.0s–1.0s: The photo holds, real and still. [아주 작은 생명감: 눈빛, 숨]
1.0s–5.0s: [변화가 시작되고 커짐]
5.0s–8.0s: [변화의 절정과 유지]

PHYSICS
[변하는 것은 어떻게 움직이는지 / 변하지 않는 것은 완전히 고정]

LIGHTING
Keep the original photo's [빛] exactly. Consistent exposure throughout.

AUDIO
[앰비언스] + [변화에 맞는 효과음]; no dialogue.

STYLE
Photoreal, matching the uploaded photo exactly. Natural grain, realistic [physics], clean and stable.
[Surreal/Dreamy] but grounded in real light.
```

**검증된 아이디어**
- 머리카락이 계속 자라 바닥에 고이고 바람에 날림 (몸은 살아있는 조각상처럼 고정)
- 중력이 꺼지고 주변 물건과 본인이 함께 떠오름 (무게별로 다른 속도)
- 인물과 강아지만 정지, 도시는 실시간으로 움직이고 카메라가 360° 오빗 → 끊김 없는 루프
- 전경 선풍기 날개가 지나갈 때마다 숨은 컷으로 의상 3벌 교체
- 카메라가 25° 기울어지며 방이 기우는 착시, 물건들이 미끄러져 지나가는데 인물은 태연함
- 얼굴 한쪽에 보석이 하나씩 붙어 퍼짐 (셀카 앵글을 찾는 연기)

**포인트**: 리얼한 컷은 "Shot on an iPhone, candid UGC realism", "iPhone realism, true-to-life colors". 유머는 **인물의 태연함과 주변 혼돈의 대비**에서 나옵니다.

---

## 7. 인서트 몽타주 방식 (Rewind Club)

"존재하지 않는 2000년대 로맨틱 코미디의 인서트 컷" 몽타주를 처음부터 끝까지 만드는 방법입니다.

### 7-1. 스틸 생성 (Soul Cinema, 16:9, 2K)
**공식**: `[손/발 + 의식 같은 동작 하나] + [포인트 색 하나를 가진 주인공 소품] + [중립적인 세트] + [빛] + 고정 꼬리말`
```
고정 꼬리말:
close-up insert shot, still frame from a 2000s teen romantic comedy, shot on 35mm film, glossy
soft studio lighting, warm natural 2000s film color grade, shallow depth of field, gentle film
grain, hands or feet only, no faces, no text, no logos
```
- **얼굴, 글자, 브랜드를 모두 빼서** 익명성을 지키면 "기억 속 영화"처럼 읽힙니다.
- **핑크 빼기 규칙**: 꼬리말에 "saturated candy-pink" 그레이드를 넣으면 전부 단조로운 핑크가 됩니다. 그레이드는 중립적인 웜톤으로 두고, **포인트 색은 프레임당 하나, 주인공 소품에만** 줍니다. 세트는 나무, 크롬, 데님, 회색 니트, 베이지 카펫처럼 중립적으로 둡니다.
- 콘텐츠 버킷 10개(뷰티, 신발, Y2K 기기, 우정, 간식, 파자마 파티, 옷장, 썸, 학교·차·외출, 계절)에 프롬프트 100개를 분산합니다.
- **스타일 테스트 먼저**: 3개 프롬프트 × 8장으로 그레이드를 승인받은 뒤 전체를 × 2장씩 돌립니다.

### 7-2. 애니메이트 (시댄스, 5초, 고른 프레임을 시작 이미지로)
- ❌ **실패**: 고정 카메라 + 미세 동작("참이 한 번 흔들리고 멈춘다")은 스크린세이버처럼 죽어 보입니다.
- ✅ **성공**: 샷마다 **에너지원 두 개**를 넣습니다.
  1. **움직이는 카메라**: 슬로 푸시인, 측면 트래킹, 1/4 원호, 핸드헬드 흔들림, POV 중 하나를 명시
  2. **5초 내내 이어지는 동작**: 시작, 전개, 완결의 비트를 갖춥니다. 손이 들어오고 나가고, 잡고 던지고 쏟습니다. 프레임 밖의 삶을 새어 들게 합니다 (프레임 위에서 들리는 웃음, 마카롱을 훔치는 두 번째 손).

```
Use the attached image as the exact first frame. Real-time natural speed.
[CAMERA MOVE, named explicitly] while [CONTINUOUS ACTION with 2-3 beats, physics: momentum,
swing, settle, splash]; [environment motion: fabric, light, particles]. Warm natural 2000s 35mm
film grade and grain preserved from the first frame.
Audio: [2-3 diegetic sounds, one can be above/off frame].
```
- **슬로모션 방지**: `Real-time natural speed`를 맨 앞에 넣습니다.
- 프리셋이 자동으로 제안되면 거절하고 글자 그대로 생성합니다.

### 7-3. 편집
- 약 14.5초, 약 29컷, 컷당 약 0.42~0.46초로 박자에 맞춥니다 (130bpm 전후의 강한 비트).
- 5초 클립에서 **동작이 꽂히는 0.5초**(잡기, 탁 닫기, 튀기기)만 씁니다.
- 메트로놈 같은 리듬을 **딱 두 번** 깨고 가장 좋은 클립을 길게 둡니다 (약 0.9초, 약 1.3초).

---

## 8. 장르별 룩 레시피 모음

| 룩 | 핵심 키워드 |
|---|---|
| 16mm 다크 판타지 | blue-hour dusk, milky low-contrast, volumetric fog, real grain, warm-cool, Eggers/Aster restraint |
| 2000년대 중반 35mm 드라마 | warm-timed colour negative, honey skin, lifted blacks, diffusion glow, halation, 4:3 |
| 2000년대 초 드라마 / DVD 스틸 | milky blacks, creamy highlights, bloom around sconces, DVD compression artifacts, golden haze |
| K-드라마 파스텔 | peach/powder blue/cream/gold, visible pores no smoothing, 50mm feel, camera holds still |
| 차가운 미스터리 | fog as permanent layer, cool blue-grey, desaturated, lifted blacks, 35mm grain |
| 미국 멀티캠 시트콤 | high-key frontal top light, candy-saturated, locked tripod, beat after punchline |
| 2000년대 도쿄 콤팩트 디카 | heavy irregular high-ISO grain, color noise, smeary, chromatic fringing, clipped neon |
| 2000년대 초 일본 TV 특촬 | 4:3, ~480i, interlacing, faded pastel, milky bloom, animated transformation plate |
| 1997 뉴욕 롬콤 (9:16) | movie-star faces, voluminous hair, 35mm grain, warm golden practicals, creamy contrast |
| 2D 잉크·붓 애니메이션 | ink linework, cream paper ground, limited animation, held keyframes, stepped cadence |
| 종이 스톱모션 | one pose at a time, 3–4 frame holds, paper jitter, glass-sheet sequins, dream-memory filter |

**스톱모션 규칙** (Paper World): "Each held pose lasts 3 to 4 frames, then the object jumps to its next position. Every frame is a sharp still photograph... every change on screen is a physical displacement or a fold along a visible crease."

**TV 변신 시퀀스** (Cat Guardian): 변신에 8초를 통째로 주고, 신발 → 장갑 → 의상 → 티아라 → 지팡이 순서로 **디테일마다 별도의 읽히는 샷**을 줍니다. 마지막 포즈는 최소 0.5초 유지합니다. 거리로 돌아오면 원래 노출과 빛 방향을 복원합니다.

---

## 9. 자주 생기는 실패와 해결

| 증상 | 원인 | 해결 문장 |
|---|---|---|
| 방이 넓어지고 가구가 늘어남 | 모델이 "도움이 되려고" 공간을 키움 | "Locations render only what the location reference shows and are never widened, re-furnished or made grander." / "Exactly one table exists" |
| 씬이 캐릭터 시트의 회색 배경을 닮음 | 시트의 조명과 배경까지 따라감 | "take only the face, the hair and the clothing... never its lighting, background or camera angle" |
| 음악이 깔림 | 시댄스의 기본 동작 | NO MUSIC 블록 + 허용 사운드 목록 |
| 잡지·간판에 실제 로고가 생김 | 인쇄면 자동 채움 | "Every printed surface is blank" |
| 엑스트라가 주연 의상을 따라 입음 | 고정되지 않은 엑스트라 | 군중 무드보드 + 엑스트라 의상 명시 + "never becoming a sharp face" |
| 두 인물의 얼굴·좌우가 바뀜 | 위치 미지정 | 화면 좌우 + x% 좌표 + "Never swap their faces, hair, sides or wardrobe" |
| 컷마다 시선 방향이 뒤집힘 | 축선을 넘음 | 방위 지도 + "All cameras stay on the east side of the A–B line" |
| 시간대가 바뀜 | 레퍼런스의 낮 사진 | "Use @Image N for geography only; override its daytime look" + "no time-of-day drift" |
| 표식·상처가 너무 일찍 보임 | 레퍼런스 하나에 상태가 섞임 | 상태별 레퍼런스 분리 + 비트에서 "switch identity control to @Image 2" |
| 슬로모션처럼 몽환적임 | 기본 경향 | "Real-time natural speed" / "Real-time motion" |
| 화면이 죽어 보임 | 고정 카메라 + 미세 동작 | 카메라 움직임 + 5초 내내 이어지는 동작 (에너지원 두 개) |
| 반응이 원인보다 먼저 나옴 | 순서가 모호함 | "ONLY AFTER... never before..." + 그 동작 중에는 컷 금지 |
| 가구를 끌고 다님 | 앉는 동작을 모델이 해석함 | "fixed built-in banquettes... Nobody touches, pulls, drags any furniture. Show the human moving, not the furniture." |
| 화면 밖의 사람이 말함 | 대사 배치 실패 | "no line is heard while the speaker is out of frame" + 대사마다 시간 구간 지정 |
| 유리알 같은 눈, 마네킹 얼굴 | 연기 지시 부족 | ACTING TASK + Safety 줄 |
| 폴더폰이 스마트폰이 됨 | 시대 고증 이탈 | 프롭 레퍼런스 + "100% matches the reference, including the on-screen text" + "no modern phones" |
| 측면 시트에서 고개를 돌림 | 카메라를 보려는 경향 | "HEAD IS TURNED EXACTLY AS FAR AS HIS BODY" |
| 같은 인물이 둘로 복제됨 | 사진 속 인물을 살아있는 사람으로 해석 | "exists only as a small framed still photograph — never a living person; do not duplicate" |

---

## 10. 복사해서 쓰는 마스터 템플릿

```
[STYLE PREFIX — 프로젝트 고정 문단]

[VISUAL CONSTRAINTS — 프로젝트 고정 문단]

SCENE CONTEXT
[2~5문장. 무슨 일이 일어나고 어떻게 끝나는지. 반전 포함.]

ACTIVE REFERENCES
@Image 1 — [이름] identity anchor: [얼굴/머리/피부/의상 텍스트 요약]. Take only face, hair and
clothing; ignore its background, lighting, pose and panel layout. Stays screen-[LEFT/RIGHT].
100% matches the reference.
@Image 2 — [이름] identity anchor: ... 100% matches the reference.
@Image 3 — LOCATION: [핵심 지리]. Controls geography, materials and light sources only; does not
control camera angle. [시간대 덮어쓰기]
@Image 4 — PROP: [소품 묘사, 상태]. 100% matches the reference.

FORMAT MODE
[N]-segment sequence with [N-1] HARD CUTs. Real-time motion. [인원] living principals only.
[Dialogue / SFX only]. No music. No subtitles. [Horizontal landscape / Vertical 9:16 / 4:3].

LOCATION MAP
[카메라 기준 좌우·앞뒤 지도 / 방위 지도. 축선 규칙.]

FIRST FRAME AND SPATIAL BLOCKING
Open already on [동작 중인 상태], no empty establishing frame. [인물] x __%, y __%, [자세/시선].
[FG/MG/BG]. Nobody else in frame.

OPTICS
LENS LOCK SEG 1 = __° [character], camera __ m, [height], [focus].
LENS LOCK SEG 2 = __° ...
No drift mid-segment.

CAMERA
[전체 원칙: handheld 3–5% / locked tripod, locked horizon]
SEG 1: [움직임]. SEG 2: [움직임].

ACTION TIMING
SEG 1 — 0.0s to __s ([비트 이름])
0.0s: ...
__s: [인물] ([목소리 묘사]): "[대사]"
__s HARD CUT
SEG 2 — ...

PHYSICS
[대상 + 재질/질량 + 동작 + 지연/정착]

LIGHTING
[키 방향과 성격, 샷마다 유지할 것, 시간대 고정, 레퍼런스 덮어쓰기, 필름 반응]

AUDIO
No music. Only SFX and scripted dialogue. [허용 효과음 + 시점]. Only the quoted lines are
spoken, in [언어], one voice at a time; lips still otherwise.
VOICE — [이름]: [음색, 음역, 억양, 속도]. "[대사]" is [어떻게].

ACTING TASK — [이름] (the work is in the eyes):
SCENE DIRECTION (shared, unspoken): ...
MOTIVE: ... GOAL: ... OBSTACLE: ... TACTIC: ...
(Safety: gaze always engaged in the task — never a frozen, glassy stare; natural blink cadence.)

POSITIVE LOCKS
[인원수] total and never more. [인물] 100% matches @Image 1, screen-LEFT... Never swap faces,
hair, sides or wardrobe. [소품 상태/위치]. [숨길 것]. [시간대]. [컷 시점].
Maintain face and clothing consistency. High detail. Natural smooth movements. Sharp clarity.
Stable lighting. Consistent frame rate. Clean picture.
```

---

## 11. 작업 체크리스트

**프리프로덕션**
- [ ] 스크립트 완성 (대사는 짧고 적게, 감정은 시선과 침묵으로)
- [ ] 캐릭터 시트: 인물별로, **상태별로** 따로
- [ ] 로케이션: 비어 있게, 광각, 필요한 각도별로, 헥스 팔레트 포함
- [ ] 인페인트로 레퍼런스의 잡동사니 제거
- [ ] 프롭: 제품 사진, 상태별로
- [ ] 군중 무드보드
- [ ] Style Prefix와 Visual Constraints 확정

**프롬프트 작성**
- [ ] Claude 채팅에 스크립트 전문, 고정 문단, **지금까지의 실패 기록**을 넣어두고 작성 (샷이 어떤 비트를 담당하는지, 직전에 무슨 일이 있었는지 알게 함)
- [ ] 레퍼런스마다 통제할 것과 무시할 것을 명시
- [ ] 첫 프레임 좌표, 렌즈 화각, 카메라 움직임
- [ ] 초 단위 타이밍, 컷 위치, 대사 구간
- [ ] NO MUSIC 블록
- [ ] ACTING TASK + Safety 줄
- [ ] POSITIVE LOCKS + 품질 꼬리말

**생성과 편집**
- [ ] 스타일 테스트를 먼저 하고 그레이드 승인
- [ ] 샷 길이는 8~15초 (최대 약 30초까지 다중 세그먼트)
- [ ] 배치로 여러 번 생성 → 가장 좋은 몇 초만 선택
- [ ] 마지막 프레임 또는 마지막 3~4초를 다음 샷 레퍼런스로
- [ ] 실패작은 Failed 폴더에 보관하고 실패 기록에 추가
- [ ] 후반: 트랙 정리, 효과음 수작업 보강, 음악 작곡, 씬 전환을 사운드로 숨기기

---

## 12. 참고: 이미지 모델 사용 분담 (관찰 기준)

| 모델 | 쓰임 |
|---|---|
| Higgsfield Soul 2.0 | 로케이션 스틸, 패션 전신 사진(Soul ID 기반), 군중 무드보드 |
| Soul Cinema | 시네마틱 로케이션, 인서트 스틸 대량 생성 |
| Nano Banana Pro | 캐릭터 시트(여러 이미지 조합), 프롭 제품 사진 4K, 업스케일, 간단한 수정 |
| GPT Image 2 | 정밀한 다중 패널 캐릭터 시트, 의상 교체, 얼굴 교체 |
| Seedream 5.0 Pro | 마스크 인페인트·지우기, 부분 품질 개선, 캐릭터 시트 수정 |
| Seedance 2.5 | 최종 영상 (1080p; 16:9 1920×1080, 4:3 1440×1080, 9:16 1080×1920) |
