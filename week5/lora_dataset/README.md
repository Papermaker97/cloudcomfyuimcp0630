# LoRA 데이터셋: 운동화 1켤레 (Z-Image Turbo)

트리거 단어: `oncld_shoe` · 목표 24장 · 긴 변 1024px 이상 · JPG/PNG

## 촬영 원칙

- **운동화는 늘 같고, 나머지(각도·배경·조명·사용 상황)만 바꿉니다.** 같은 배경·같은 각도가 반복되면 그 배경과 각도까지 '이 운동화'로 학습됩니다.
- 실물을 직접 촬영하세요. 브랜드 공식 제품 사진을 학습 데이터로 쓰면 권리 문제가 있고, 공식 컷은 대부분 흰 배경 측면 한 각도라서 학습용으로도 부족합니다.
- 초점이 맞고 운동화가 화면의 30~70%를 차지하게 찍습니다. 흐린 컷, 일부가 잘린 컷, 다른 신발이 섞인 컷은 뺍니다.
- 신은 컷(20~22)에서는 발과 다리만 나오게 하고 얼굴은 넣지 않습니다.
- 파일 이름을 아래 번호와 똑같이 맞춥니다(`01.jpg` ↔ `captions/01.txt`). 학습 도구는 같은 이름의 txt를 캡션으로 읽습니다.

## 캡션 규칙

- 형식: `oncld_shoe running shoe, <각도>, <배경/조명/상황>`
- **운동화 자체의 특징(색, 로고, 메쉬, 밑창 구멍 모양 등)은 쓰지 않습니다.** 쓰지 않은 특징이 트리거 단어에 붙어서 학습됩니다.
- 바뀌는 것(각도, 배경, 조명, 손·발 등)만 씁니다. 그래야 생성할 때 그 부분을 프롬프트로 바꿀 수 있습니다.
- 실제 사진이 계획과 다르게 나오면 캡션도 사진에 맞게 고칩니다.

## 컷 목록

| # | 각도 | 배경·조명·상황 | 캡션 |
|---|---|---|---|
| 01 | 오른쪽 측면 (바깥쪽) | 흰 배경 스튜디오, 소프트박스 | `oncld_shoe running shoe, right side view, on a white seamless studio background, soft even light` |
| 02 | 왼쪽 측면 (안쪽) | 흰 배경 스튜디오, 소프트박스 | `oncld_shoe running shoe, left side view, on a white seamless studio background, soft even light` |
| 03 | 앞 45° (오른쪽) | 회색 배경, 소프트박스 | `oncld_shoe running shoe, front three-quarter view from the right, on a grey studio background, soft light` |
| 04 | 앞 45° (왼쪽) | 회색 배경, 하드 사이드 라이트 | `oncld_shoe running shoe, front three-quarter view from the left, on a grey studio background, hard side light with strong shadows` |
| 05 | 뒤 45° | 회색 배경, 림 라이트 | `oncld_shoe running shoe, rear three-quarter view, on a dark grey studio background, rim light` |
| 06 | 정후면 (뒤꿈치) | 흰 배경 | `oncld_shoe running shoe, straight rear view of the heel, on a white studio background` |
| 07 | 정면 (앞코) | 흰 배경 | `oncld_shoe running shoe, straight front view of the toe, on a white studio background` |
| 08 | 위에서 내려다봄 | 나무 테이블, 창가 자연광 | `oncld_shoe running shoe, top-down view, on a wooden table, natural window light` |
| 09 | 밑창 (아웃솔) | 흰 배경, 뒤집어 놓음 | `oncld_shoe running shoe, bottom view of the outsole, shoe turned upside down, on a white background` |
| 10 | 미드솔 디테일 클로즈업 | 스튜디오, 측광 | `oncld_shoe running shoe, close-up detail of the midsole, studio side light, shallow depth of field` |
| 11 | 측면 로고 클로즈업 | 스튜디오 | `oncld_shoe running shoe, close-up detail of the side panel, studio light` |
| 12 | 끈·발등 클로즈업 | 스튜디오 | `oncld_shoe running shoe, close-up detail of the laces and tongue, studio light` |
| 13 | 로우앵글 히어로 | 콘크리트 바닥, 강한 햇빛 | `oncld_shoe running shoe, low-angle hero shot, on a concrete floor, harsh midday sunlight` |
| 14 | 오른쪽 측면 | 젖은 아스팔트, 해질녘 | `oncld_shoe running shoe, right side view, on wet asphalt at dusk, warm golden hour light, reflections` |
| 15 | 앞 45° | 공원 잔디, 흐린 날 | `oncld_shoe running shoe, front three-quarter view, on grass in a park, overcast diffused light` |
| 16 | 측면 | 육상 트랙 | `oncld_shoe running shoe, side view, on a red running track, bright daylight` |
| 17 | 앞 45° | 밤 거리, 네온·가로등 | `oncld_shoe running shoe, front three-quarter view, on a city sidewalk at night, neon and streetlight` |
| 18 | 한 켤레 나란히 | 스튜디오 | `oncld_shoe running shoe, a pair of shoes side by side, front three-quarter view, studio background` |
| 19 | 손에 든 컷 | 실내, 자연광 | `oncld_shoe running shoe, held in a hand, side view, indoor natural light` |
| 20 | 신은 컷 (측면) | 보도, 걷는 중 | `oncld_shoe running shoe, worn on a foot, walking on a sidewalk, side view, motion` |
| 21 | 신은 컷 (뒤) | 트랙, 달리는 중 | `oncld_shoe running shoe, worn on a foot, running on a track, rear view, motion blur in the background` |
| 22 | 신은 컷 (앞) | 계단 | `oncld_shoe running shoe, worn on a foot, stepping on concrete stairs, front view` |
| 23 | 박스 위 | 나무 테이블 | `oncld_shoe running shoe, resting on top of a shoe box, three-quarter view, on a wooden table` |
| 24 | 측면, 끈 풀린 상태 | 흰 배경 | `oncld_shoe running shoe, side view with untied laces, on a white studio background` |

구성: 순수 스튜디오 각도 12장(01~12), 장소·조명 변화 5장(13~17), 사용 상황 7장(18~24).

## 수업용 비교: 나쁜 데이터셋

같은 운동화로 **흰 배경 오른쪽 측면만 20장**(공식 제품 컷과 같은 구도)을 따로 찍어 두면 좋은 비교 자료가 됩니다. 이 세트로 학습한 LoRA는 앞·뒤·위 각도나 신은 컷을 요청해도 측면·흰 배경으로 끌려가는 경향을 보일 것으로 예상합니다. 실제로 그렇게 나오는지는 학습해 보고 확인해야 합니다.

## 학습 후 테스트 프롬프트 (W5_01에 사용)

- `oncld_shoe running shoe, front three-quarter view, on wet asphalt at night, neon reflections`
- `oncld_shoe running shoe, worn on a foot, jogging on a beach at sunrise` (학습에 없던 장소)
- `oncld_shoe running shoe, floating in mid-air, studio product shot, pastel background` (학습에 없던 연출)

형태와 로고가 유지되면서 장소·연출이 프롬프트를 따라가면 잘 된 것이고, 배경까지 학습 사진처럼 고정되면 과학습입니다.
