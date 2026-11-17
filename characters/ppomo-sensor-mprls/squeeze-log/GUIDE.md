# Ppomo 쥐기 카운터: 처음부터 끝까지

쥘 때마다 **횟수 + 날짜 + 시간**이 기록되고 CSV로 저장되는 테스트예요.
위에서부터 순서대로만 하면 돼요.

---

## 0. 준비물

| 물건 | 비고 |
|---|---|
| Arduino Nano 33 IoT | |
| Adafruit MPRLS 압력 센서 | 은색 관이 달린 파란 보드 |
| 브레드보드, 점퍼선 4개 | |
| USB 케이블 | 노트북에 맞는 것 (맥북이면 USB-C 어댑터) |
| 고무공 (귀 세척기 등) | 구멍이 하나만 있는 것. 밸브 달린 블로어는 안 됨 |
| 실리콘 호스 10~20cm | 센서 관 지름 2.5mm에 꽉 끼는 것 |
| 테이프 또는 케이블 타이 | 이음새 막는 용도 |
| 노트북 + Chrome | p5 화면은 Chrome에서만 돼요 |

---

## 1. Arduino IDE 준비 (처음 한 번만)

1. Arduino IDE 2를 설치하고 열어요. (arduino.cc/en/software)
2. **보드 패키지**: 왼쪽 세로 메뉴의 **보드 아이콘** → `Arduino SAMD` 검색 → **Arduino SAMD Boards (32-bits ARM Cortex-M0+)** → INSTALL
3. **라이브러리**: 왼쪽 메뉴의 **책 아이콘** → `Adafruit MPRLS` 검색 → **Adafruit MPRLS Library** (by Adafruit) → INSTALL → 창이 뜨면 **INSTALL ALL** (Adafruit BusIO가 같이 깔려요)

---

## 2. 브레드보드 배선 (전선 4개)

| 센서 MPRLS | 보드 Nano 33 IoT |
|---|---|
| VIN | 3.3V |
| GND | GND |
| SCL | A5 |
| SDA | A4 |
| 3Vo, EOC, RST | 연결 안 함 |

- 5V(VUSB)에 연결하지 마세요. **3.3V**예요.
- 그림: `mprls-breadboard.png`

---

## 3. 고무공 연결

```
고무공 ── 실리콘 호스 ── 센서의 은색 관
```

- 호스를 센서 관과 고무공 입구에 **꽉** 끼워요.
- 헐거우면 케이블 타이나 테이프로 감아요. **공기가 새면 제대로 안 세요.**
- 호스는 짧을수록 좋아요.

---

## 4. Arduino 코드 올리기

1. Arduino IDE → **File → New Sketch**
2. 안에 있는 내용을 지우고 아래 코드를 통째로 붙여넣어요.
3. 위쪽 칸에서 **보드: Arduino Nano 33 IoT**, **포트: 연결된 보드**를 골라요.
4. **→ 화살표(Upload)** 클릭
5. 업로드가 끝난 뒤 **1초 동안 공에 손대지 마세요.** (쉬는 상태의 기압을 배워요)

```cpp
/*
  Ppomo squeeze counter (Arduino Nano 33 IoT + Adafruit MPRLS)

  Wiring: MPRLS VIN -> 3.3V, GND -> GND, SCL -> A5, SDA -> A4. Leave 3Vo, EOC, RST empty.
  Rubber bulb -> silicone tube -> the sensor's metal port.

  Sends one line 20 times a second:  delta,count
    delta = how far the pressure is above resting air (hPa)
    count = squeezes counted since the board started
  The p5 page adds the date and time to every squeeze.

  Don't touch the bulb for the first second after upload (it learns the resting pressure).
  Library: "Adafruit MPRLS Library". Written with help from Claude.
*/
#include <Wire.h>
#include "Adafruit_MPRLS.h"

Adafruit_MPRLS mpr = Adafruit_MPRLS(-1, -1);

const float SQUEEZE_ON  = 8.0;   // hPa: above this = squeezed      (lower it if squeezes are missed)
const float SQUEEZE_OFF = 3.0;   // hPa: below this = let go         (keep it smaller than SQUEEZE_ON)
const float DRIFT = 0.01;        // how fast the resting value follows slow changes (warm hands, weather)

float rest = 0;
bool squeezing = false;
unsigned long count = 0;

void setup() {
  Serial.begin(9600);
  pinMode(LED_BUILTIN, OUTPUT);
  if (!mpr.begin()) {
    while (true) {               // fast blink = sensor not found: check the 4 wires
      Serial.println("MPRLS not found. Check VIN->3.3V, GND->GND, SCL->A5, SDA->A4");
      digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
      delay(200);
    }
  }
  float sum = 0;                 // learn the resting pressure (about 1 second)
  for (int i = 0; i < 20; i++) {
    sum += mpr.readPressure();
    delay(50);
  }
  rest = sum / 20;
}

void loop() {
  float hPa = mpr.readPressure();
  if (isnan(hPa)) return;

  float delta = hPa - rest;
  if (!squeezing && delta > SQUEEZE_ON) {          // a new squeeze: count it once
    squeezing = true;
    count++;
  } else if (squeezing && delta < SQUEEZE_OFF) {   // let go: ready for the next one
    squeezing = false;
  }
  if (!squeezing) rest += (hPa - rest) * DRIFT;

  digitalWrite(LED_BUILTIN, squeezing ? HIGH : LOW);
  Serial.print(delta, 1);
  Serial.print(",");
  Serial.println(count);
  delay(50);
}
```

---

## 5. 센서 확인 (Serial Monitor)

1. 오른쪽 위 **돋보기 아이콘(Serial Monitor)** 클릭, 속도 **9600**
2. `0.0,0` 같은 줄이 계속 나오면 정상이에요. 앞 숫자는 기압 변화, 뒤 숫자는 횟수예요.
3. 공을 쥐면 앞 숫자가 올라가고, 뒤 숫자가 1씩 늘어요. 쥐는 동안 보드의 작은 LED가 켜져요.
4. 확인되면 **Serial Monitor 창을 닫으세요.** 열려 있으면 다음 단계의 p5가 연결되지 않아요.

| 화면 | 뜻 | 할 일 |
|---|---|---|
| `MPRLS not found...` + LED 빠르게 깜빡 | 센서를 못 찾음 | 전선 4개 다시 확인 (특히 A4/A5 뒤바뀜) |
| 숫자는 나오는데 쥐어도 안 변함 | 공기가 센서에 안 감 | 호스가 은색 관에 끝까지 끼워졌는지 확인 |
| 쥐고 있는 동안 숫자가 서서히 내려감 | 이음새에서 공기가 샘 | 테이프로 감기 |

---

## 6. p5 화면 (날짜·시간 기록)

1. **Chrome**에서 editor.p5js.org 열고 로그인 → **File → New**
2. 왼쪽 파일 목록에서 **index.html**을 열고 내용을 아래 코드로 통째로 바꿔요.
3. **sketch.js**도 아래 코드로 통째로 바꿔요.
4. ▶ 실행 → **choose port** → 목록에서 보드 선택 → 연결
5. 공을 쥐면 큰 숫자가 늘고, 아래에 **번호 / 날짜 / 시간**이 쌓여요.
6. 끝나면 **Save CSV** → `ppomo-squeezes.csv`가 다운로드돼요. **새로고침하면 기록이 사라지니 꼭 저장하세요.**

### index.html

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Ppomo squeeze log</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.4.0/p5.js"></script>
    <script src="https://unpkg.com/p5-webserial@0.1.1/build/p5.webserial.js"></script>
    <style>
      html, body { margin: 0; background: #FBF6F1; font-family: system-ui, sans-serif; color: #5A3424; }
      main { display: flex; justify-content: center; padding-top: 16px; }
      canvas { border-radius: 16px; }
      button { font: inherit; padding: 6px 14px; border-radius: 999px; border: 1px solid #C9A99A; background: #fff; cursor: pointer; }
    </style>
  </head>
  <body>
    <main></main>
    <script src="sketch.js"></script>
  </body>
</html>
```

### sketch.js

```javascript
/*
  Ppomo squeeze log (p5.js + p5.webserial)
  Reads "delta,count" from the Arduino. Every new squeeze is written down with the date and time
  from this computer. "Save CSV" downloads the whole list.
  Use Chrome. Close the Arduino Serial Monitor first, then click "choose port".
  Written with help from Claude.
*/
const serial = new p5.WebSerial();
let portButton, saveButton, clearButton;
let delta = 0;             // pressure rise right now (hPa)
let lastCount = 0;         // the Arduino's count we have already logged
let log = [];              // every squeeze: { n, date, time }
let history = [];          // recent pressure for the small graph
let maxSeen = 20;

function setup() {
  createCanvas(480, 560);
  if (!navigator.serial) alert("Web Serial does not work in this browser. Use Chrome.");
  navigator.serial.addEventListener("connect", () => serial.getPorts());
  navigator.serial.addEventListener("disconnect", () => serial.close());
  serial.getPorts();
  serial.on("noport", makePortButton);
  serial.on("portavailable", openPort);
  serial.on("requesterror", (err) => alert("Serial port error: " + err));
  serial.on("data", serialEvent);
  serial.on("close", makePortButton);

  saveButton = createButton("Save CSV");
  saveButton.mousePressed(saveLog);
  clearButton = createButton("Clear");
  clearButton.mousePressed(() => { log = []; });
}

function draw() {
  background(251, 246, 241);
  noStroke();
  fill(90, 52, 36);

  // total
  textAlign(CENTER);
  textSize(16);
  text("squeezes", width / 2, 48);
  textSize(72);
  text(log.length, width / 2, 120);

  // pressure graph (to check the sensor and tune the thresholds)
  maxSeen = max(maxSeen, delta * 1.2);
  noFill();
  stroke(233, 154, 166);
  strokeWeight(2);
  beginShape();
  for (let i = 0; i < history.length; i++) {
    vertex(map(i, 0, 199, 20, width - 20), map(history[i], 0, maxSeen, 230, 150, true));
  }
  endShape();
  stroke(210, 190, 180);
  strokeWeight(1);
  line(20, 230, width - 20, 230);
  noStroke();
  fill(140, 110, 100);
  textSize(12);
  textAlign(LEFT);
  text(`pressure rise ${delta.toFixed(1)} hPa`, 20, 250);

  // the newest squeezes, newest first
  fill(90, 52, 36);
  textSize(14);
  text("#      date              time", 40, 290);
  const shown = log.slice(-12).reverse();
  for (let i = 0; i < shown.length; i++) {
    const e = shown[i];
    text(`${e.n}`, 40, 318 + i * 20);
    text(e.date, 90, 318 + i * 20);
    text(e.time, 220, 318 + i * 20);
  }
}

function serialEvent() {
  let line = serial.readLine();
  while (line) {
    const parts = trim(line).split(",");
    if (parts.length === 2 && !isNaN(Number(parts[1]))) {
      delta = Number(parts[0]);
      const count = Number(parts[1]);
      if (count < lastCount) lastCount = 0;       // the Arduino restarted: its count began again
      while (lastCount < count) {                 // one log line per new squeeze
        lastCount++;
        addSqueeze();
      }
      history.push(delta);
      if (history.length > 200) history.shift();
    }
    line = serial.readLine();
  }
}

function addSqueeze() {
  const d = new Date();
  const two = (v) => String(v).padStart(2, "0");
  log.push({
    n: log.length + 1,
    date: `${d.getFullYear()}-${two(d.getMonth() + 1)}-${two(d.getDate())}`,
    time: `${two(d.getHours())}:${two(d.getMinutes())}:${two(d.getSeconds())}`,
  });
}

function saveLog() {
  const table = new p5.Table();
  table.addColumn("n");
  table.addColumn("date");
  table.addColumn("time");
  for (const e of log) {
    const row = table.addRow();
    row.setNum("n", e.n);
    row.setString("date", e.date);
    row.setString("time", e.time);
  }
  saveTable(table, "ppomo-squeezes.csv");
}

function makePortButton() {
  portButton = createButton("choose port");
  portButton.mousePressed(() => serial.requestPort());
}

function openPort() {
  serial.open().then(() => console.log("port open"));
  if (portButton) portButton.hide();
}
```

| 화면 | 할 일 |
|---|---|
| "Web Serial does not work" 경고 | Chrome으로 열기 |
| choose port 목록이 비어 있음 | USB 다시 꽂기 / Arduino Serial Monitor 닫기 |
| 연결됐는데 숫자가 안 움직임 | Arduino 코드가 업로드됐는지, Serial Monitor가 닫혔는지 확인 |

---

## 7. 테스트 (4가지만)

| # | 할 일 | 정상이면 | 결과 적기 |
|---|---|---|---|
| 1 | 공을 10번 쥐기 | 숫자 **10**, 기록 10줄 | |
| 2 | 3초간 꾹 쥔 채로 있기 | **1**만 늘어남 | |
| 3 | 1분간 손에 들고만 있기 | 안 늘어남 | |
| 4 | Save CSV | 번호·날짜·시간이 든 파일이 저장됨 | |

**안 맞으면 Arduino 코드 맨 위 숫자 하나만 바꾸고 다시 업로드하세요.**
- 덜 셈 → `SQUEEZE_ON`을 `8.0` → `4.0`
- 더 셈 / 들고만 있어도 셈 → `SQUEEZE_ON`을 `8.0` → `15.0`
- 다시 업로드할 때는 p5를 멈추거나 탭을 닫아야 해요. (포트를 같이 쓸 수 없어요)

---

## 8. 알아둘 것

- 날짜와 시간은 **노트북 시계** 기준이에요. 보드에는 시계가 없어서 p5 화면이 켜져 있을 때만 기록돼요.
- 보드를 뺐다 꽂아도 p5의 기록은 이어서 쌓여요.
- 센서는 실온보다 약 700 hPa 높은 압력까지만 재요. 그래프가 그 근처에서 멈추면 너무 세게 쥔 거예요.
- 이 p5 페이지는 실제 보드에 연결해서 돌려보지 못했어요. 문법 검사만 했어요. Arduino 코드는 컴파일까지 확인했어요.
