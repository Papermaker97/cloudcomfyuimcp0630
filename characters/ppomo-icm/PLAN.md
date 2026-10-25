# 뽀모 — FOMO가 쌓인다 (ICM Week 6 CREATE 기획)

## 한 줄
뽀모를 쥘 때마다 화면 위에서 뽀모가 한 마리씩 떨어져 쌓인다. 쥐는 횟수만큼 FOMO가 눈에 보이게 쌓인다.

## 무엇을 만드나
- 화면을 누르는 것이 뽀모를 "쥐는" 행동이다. 실제 쥐기는 PComp 기기에서 하고, 이 화면 버전에서는 클릭·터치가 그 역할을 한다.
- 한 번 누르면 뽀모 한 마리가 위에서 떨어져, 누른 위치의 칸으로 내려간다.
- 바닥이나 이미 쌓인 뽀모 위에 말랑하게 착지한다. 착지할 때 살짝 찌그러졌다가 돌아온다.
- 뽀모마다 다른 파스텔 색이다 (#4 기획서 구상).
- 스크롤을 멈추면 추가가 멈추듯, 쥐기를 멈추면 더 떨어지지 않는다. 이미 쌓인 뽀모는 그대로 남는다.
  - "감정은 소비되는 게 아니라 축적된다" (#4, #5에서 이어지는 문장)

## 왜
무서운 걸 귀엽게 만들면 부담이 줄어든다. FOMO를 손으로 만질 수 있는 귀여운 덩어리로 바꿔서, 내가 얼마나 쌓았는지 보이게 한다.

## 과제 조건과의 연결
| 조건 | 이 스케치에서 |
|---|---|
| 객체 배열 | `ppomos` 배열에 `Ppomo` 클래스 인스턴스가 쌓임 |
| 클릭/키로 추가 | 클릭(또는 스페이스) → `push`로 뽀모 추가 |
| 삭제 | Backspace → 마지막 뽀모 `pop`. 다음 단계: 엉덩이를 비벼 달래면 그 뽀모가 배시시 웃으며 떠나감 |
| 사용자 행동 기록 | `log` 배열에 `{ action, time }`으로 모든 쥐기·빼기를 기록하고, 화면에 쥔 횟수 표시 |
| 변수·조건문·반복문·함수·클래스 | 칸 계산, 꽉 찬 칸 막기, 그리기 반복문, `squeeze()` 함수, `Ppomo` 클래스 |

## 구조
- `class Ppomo`
  - 속성: `col`, `x`, `y`, `targetY`(착지 높이), `speed`, `landed`, `squash`, `color`
  - 메서드: `fall()`(떨어지고 착지), `show()`(귀·몸·볼·눈·입 그리기)
- `ppomos = []`: 화면의 뽀모들
- `log = []`: 행동 기록
- `squeeze(x)`: 누른 칸을 계산한다. 그 칸에 이미 몇 마리 있는지 세서 착지 높이를 정하고, 새 뽀모를 추가한다.
- `mousePressed()`, `keyPressed()`: 입력

## 1주차 (10/26) — 여기까지 했다
- 누를 때마다 뽀모가 떨어져 칸별로 쌓인다.
- 착지할 때 말랑하게 찌그러진다.
- 마리마다 파스텔 색이 다르다.
- Backspace로 마지막 뽀모를 뺄 수 있다.
- 쥔 횟수와 마리 수를 기록·표시한다.

## 2주차 — 완성 범위
- **빵빵해지기:** 쌓인 뽀모를 다시 누르면 그 뽀모의 볼 → 배 → 엉덩이가 단계별로 빵빵해진다. 핵심 메커닉 "쥘수록 커진다"를 한 마리 안에서 살린다.
- **달래서 보내기:** 엉덩이를 마우스로 비비면 배시시 웃고 둥실 떠나간다. 배열에서 삭제되고, 위에 있던 뽀모들이 내려온다.
- 화면이 꽉 차면 전체가 출렁출렁.
- 기록 화면: 쥔 횟수, 빵빵하게 만든 횟수, 달래서 보낸 수.
- 출처 표기 정리.

## 향후 (윈터쇼를 향해)
- 지금은 뽀모가 화면 **바닥**에 한 마리씩 쌓인다.
- 앞으로는 카메라로 **사람의 형태를 인식**해서, 뽀모가 관람객의 **머리나 어깨 위에 자연스럽게 얹혀 쌓이게** 하고 싶다.
  - 예: ml5.js의 몸 자세 인식으로 머리·어깨 위치를 찾아, 그 위치를 "바닥" 대신 착지 높이로 쓴다.
  - 쥘수록 내 머리와 어깨 위에 FOMO 뽀모가 수북이 쌓이는 모습을 사진으로 남기는 전시 경험.
- 입력은 클릭 대신 PComp에서 만드는 실제 뽀모 기기를 쥐는 것으로 바꾼다. 같은 `squeeze()` 함수가 불리게만 하면 된다.
- 과목별 분담: PComp = 기기, ICM = 이 화면, Hypercinema = 영상, Applications = 놀이 개념.

## 출처
- p5.js (https://p5js.org)
- 스케치 코드 작성에 Claude(Anthropic)의 도움을 받았다. 기획·캐릭터·메커닉은 본인 것.

---

## 수업에서 설명할 말 (영어)
> Ppomo is a creature that soaks up FOMO. Every time you squeeze it — here, every click — one Ppomo falls from the top and lands on the pile. When you stop, nothing new falls, but what you've piled up stays. That's my point: the feeling isn't used up, it accumulates. I make the scary thing cute so it's easier to hold.

> In code, each Ppomo is an object of a `Ppomo` class, stored in an array. A click pushes a new one, Backspace pops the last one, and every action is recorded in a log array with a timestamp.

> Next week, pressing a Ppomo on the pile makes its cheeks, belly and butt puff up, and rubbing its butt makes it smile and float away, removing it from the array. For the Winter Show, I want the Ppomos to land on visitors' heads and shoulders using body tracking instead of the floor, and the input will be squeezing the real Ppomo device.
