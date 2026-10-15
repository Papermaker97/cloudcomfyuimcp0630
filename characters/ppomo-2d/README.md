# 뽀모 2D — 에프터 이펙트 익스프레션 테스트 키트

| 파일 | 용도 |
|---|---|
| `ppomo-ae-build.jsx` | **이거 하나면 됨.** 에펙에서 실행하면 레이어 나뉜 뽀모 + 익스프레션 5개가 들어간 컴프 5개 자동 생성 |
| `ppomo-2d.svg` | 같은 디자인의 SVG (확인·수정·일러스트레이터용). 부위별 `<g id>`로 나뉨 |

---

## 방법 A. 스크립트로 한 번에 (추천)

1. 에프터 이펙트 → **File › Scripts › Run Script File…** → `ppomo-ae-build.jsx` 선택
2. 프로젝트 패널에 `Ppomo 2D Tests` 폴더가 생기고 그 안에 컴프 5개:
   `01_Wiggle` · `02_SquashStretch` · `03_Heartbeat_loopOut` · `04_Bounce` · `05_Blink`
3. 각 컴프를 열고 재생(스페이스바)하면 끝.

뽀모는 셰이프 레이어 14개로 만들어지고, 모든 부위가 `body` 레이어에 **부모(Parent)** 로 연결돼 있습니다.
그래서 `body` 하나에만 익스프레션을 걸어도 몸 전체가 같이 움직입니다. (그림자만 바닥에 남도록 부모 없음)

> 실행 중 오류가 나면 알림창에 메시지와 줄 번호가 뜹니다. 그대로 알려주세요.

## 방법 B. SVG로 직접 가져와서 수동 적용

1. `ppomo-2d.svg` 를 **일러스트레이터**에서 열기
2. 레이어 패널에서 그룹들이 `Layer 1` 아래 하위 레이어로 들어가 있음 → 레이어 메뉴 **Release to Layers (Sequence)** 후, 생긴 레이어들을 최상위로 끌어올리기
3. `.ai` 로 저장 → 에펙에서 Import, **Composition – Retain Layer Sizes** 로 가져오기
4. 필요하면 레이어 우클릭 › Create › **Create Shapes from Vector Layer**
5. 아래 "기준점" 설정 → 부위 레이어들을 `body`에 Parent 연결 → 익스프레션 붙여넣기

---

## 기준점(Anchor Point) — 중요

| 레이어 | 기준점 위치 | 이유 |
|---|---|---|
| `body` | 몸 **바닥 가운데** (530, 560) | 찌그러질 때 바닥에 붙은 채로 눌림, 바운스 착지 기준 |
| `eye_L`, `eye_R` | 각 **눈 가운데** | 깜빡임이 위아래 가운데로 닫힘 |

방법 A는 스크립트가 이미 맞춰 둡니다. 방법 B는 Pan Behind 도구(Y)로 직접 옮기세요.

---

## 익스프레션 5개 (Alt/Option + 스톱워치 클릭 후 붙여넣기)

### 1. Wiggle — 불안해서 부들부들 (`body` › Position)
```js
// wiggle(초당 횟수, 흔들리는 양 px)
wiggle(14, 4);
```
- 더 불안하게: `wiggle(20, 6)` / 살짝 떨림: `wiggle(10, 2)`

### 2. Squash & Stretch — 쥐었다 놓기 (`body` › Scale)
```js
var period = 2.0;  // 몇 초마다 한 번 쥘지
var freq = 2.5;    // 초당 출렁임 횟수
var decay = 4.0;   // 클수록 빨리 멈춤
var amp = 20;      // 찌그러지는 세기 %
var t = time % period;
var s = amp * Math.sin(t * freq * Math.PI * 2) / Math.exp(t * decay);
[value[0] + s, value[1] - s];
```
- 가로가 늘면 세로가 줄어서 부피감이 유지됩니다.
- 나중에 실제 기기와 연결할 땐 `time % period` 대신 "쥔 순간부터 지난 시간"을 넣으면 됩니다.

### 3. loopOut("pingpong") — 두근두근 (`body` › Scale)
```js
loopOut("pingpong");
```
- **키프레임이 꼭 2개 있어야 작동합니다.** 0초에 100%, 0.28초에 106% (스크립트가 자동으로 넣어 둠)
- 더 긴장되게: 두 번째 키프레임 간격을 0.2초로 줄이기
- 키프레임 없이 익스프레션만으로 심장박동을 원하면:
```js
var bpm = 72;
var b = Math.pow(Math.abs(Math.sin(time * bpm / 60 * Math.PI)), 6) * 6;
[value[0] + b, value[1] + b];
```

### 4. Bounce — 떨어졌다 통통 (`body` › Position)
```js
var period = 3.0;  // 반복 길이(초)
var h = 160;       // 떨어지는 높이(px)
var g = 3200;      // 중력
var e = 0.5;       // 탄성 0~1 (클수록 많이 튐)
var t = time % period;
var v = Math.sqrt(2 * g * h);
var tFall = v / g;
var y = 0;
if (t < tFall) {
  y = -h + 0.5 * g * t * t;
} else {
  t -= tFall;
  v *= e;
  while (v > 40) {
    var tb = 2 * v / g;
    if (t < tb) { y = -(v * t - 0.5 * g * t * t); break; }
    t -= tb;
    v *= e;
  }
}
[value[0], value[1] + y];
```
- 말랑하게 더 튀게: `e = 0.65` / 무겁게: `e = 0.35`

### 5. Blink — 점 눈 깜빡 (`eye_L`, `eye_R` › Scale)
```js
var interval = 3.0;  // 몇 초마다 깜빡일지
var dur = 0.16;      // 깜빡이는 시간(초)
var t = time % interval;
var k = (t < dur) ? Math.abs(Math.cos(t / dur * Math.PI)) : 1;
[value[0], value[1] * k];
```
- 양쪽 눈 레이어에 똑같이 붙이면 동시에 깜빡입니다.
- 왼쪽 눈 `interval`만 3.1로 바꾸면 양쪽이 살짝 엇갈려 깜빡여서 더 자연스럽습니다.

---

## 섞어 쓰기

- 한 속성에는 익스프레션이 하나만 들어가므로, **Position에 wiggle + bounce**를 같이 쓰려면 bounce 코드 마지막 줄을 아래처럼 바꾸세요.
  ```js
  wiggle(14, 4) + [0, y];
  ```
- **깜빡임은 다른 4개와 항상 같이** 켜 두는 걸 추천합니다. 눈 레이어 Scale이라 겹치지 않고, 생명감이 확 살아납니다.

## 참고

- 익스프레션은 에펙 기본(JavaScript) 엔진과 구버전(Legacy ExtendScript) 엔진 둘 다에서 돌아가도록 `var`만 썼습니다.
- 이 키트는 에펙에서 직접 돌려보지는 못했습니다(작업 환경에 에펙 없음). 스크립트 문법 검사와 SVG 렌더 확인까지만 했습니다. 오류가 나면 알림창의 메시지와 줄 번호를 알려주세요.
