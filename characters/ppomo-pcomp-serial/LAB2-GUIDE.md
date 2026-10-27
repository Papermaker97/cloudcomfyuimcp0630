# 랩 2 따라하기: Serial Input to p5.js Using the p5.webserial Library (뽀모 버전)

랩 페이지 순서 그대로야. 각 단계의 ✅가 안 나오면 다음으로 넘어가지 말고 맨 아래 "문제 해결"을 봐.
**배선은 랩 1 그대로 둬.** 다시 꽂을 거 없어.

## 랩 페이지 ↔ 이 가이드
| 랩 페이지 섹션 | 이 가이드 | 파일 |
|---|---|---|
| Prepare the Breadboard / Add a Potentiometer | 0단계 (랩 1 배선 그대로) | |
| Program the Microcontroller | 1단계 | `lab2/arduino/lab2-1-write` |
| The P5.js WebSerial Library | 2단계 | `lab2/p5/index.html` |
| The p5.js Sketch | 3단계 | `lab2/p5/step1-check.js` |
| Serial Events + Reading Incoming Serial Data | 4단계 | `lab2/p5/step2-text.js` |
| Draw a Graph With the Sensor Values | 5단계 | `lab2/p5/step3-graph.js` |
| Reading Serial Data as a String | 6~7단계 | `lab2-2-println` + `step4-string.js` |
| (랩의 마지막 도전) 0~1023 전체 범위 | 8단계 | `lab2-3-full-range` + `step5-full-range.js` |

## 0단계. 뽀모 버전은 뭐가 달라?
- 랩 코드는 `analogRead(A0)`이야. 우리 배선에서 **A0 = FSR**이야.
  그래서 **코드를 한 글자도 안 바꾸고** FSR(뽀모 쥐기)을 그래프로 보게 돼. 랩과 같은 코드 + 센서만 FSR.
- 포텐셔미터로도 해보고 싶으면 아두이노 코드의 `A0`를 `A1`로만 바꾸면 돼. (블로그에 둘 다 있으면 더 좋아. 필수는 아님)

## 시작 전 규칙 3개 (랩 페이지 "Only one port at a time")
1. **브라우저는 Chrome.** Safari는 안 돼.
2. **아두이노 IDE의 시리얼 모니터/플로터는 닫아.** 열려 있으면 p5가 포트를 못 열어.
3. **아두이노에 업로드하기 전에는 p5 스케치를 ■ Stop.** 업로드가 끝나면 다시 ▶ Play.

## 1단계. 아두이노: 1바이트로 보내기 (`Serial.write`)
아두이노 IDE → 파일 → 새 파일 → **⌘A → delete로 전부 지우고** 붙여넣기 → 업로드.
```cpp
// Lab 2, step 1: send one sensor as ONE raw byte (0-255) with Serial.write().
// Same as the lab code. In our wiring A0 is the FSR (Ppomo squeeze).
// To use the potentiometer instead, change A0 to A1.

void setup() {
  Serial.begin(9600); // initialize serial communications
}

void loop() {
  // read the input pin:
  int potentiometer = analogRead(A0);
  // remap the pot value to fit in 1 byte:
  int mappedPot = map(potentiometer, 0, 1023, 0, 255);
  // print it out the serial port:
  Serial.write(mappedPot);
  // slight delay to stabilize the ADC:
  delay(1);
}
```
- `potentiometer`: A0 값 0~1023 (우리는 FSR 값)
- `mappedPot`: 0~255로 줄인 값. 한 바이트에 들어가야 `write()`로 보낼 수 있어서.
  예: 1023 → 255, 512 → 127, 0 → 0
- ✅ "업로드 완료". **시리얼 모니터는 열지 마.** (열어도 랩 1처럼 깨진 글자만 나와)

## 2단계. p5 에디터에 라이브러리 넣기
1. Chrome에서 [editor.p5js.org](https://editor.p5js.org) → 로그인 → **File → New**
2. 왼쪽 위 **`>` (Sketch Files)** 를 눌러 파일 목록 열기 → **index.html** 클릭
3. `<head>` 안에서 **`p5.js` 또는 `p5.min.js` 가 들어간 `<script ...>` 줄**을 찾아. (에디터 버전에 따라 `1.4.0`, `1.11.x`, `2.x` 등 숫자가 달라. 상관없어, 둘 다 테스트했어)
4. **그 줄 바로 다음 줄**에 아래 한 줄을 붙여넣기:
```html
<script src="https://unpkg.com/p5-webserial@0.1.1/build/p5.webserial.js"></script>
```
5. ⚠ 반드시 **p5 줄보다 아래**에 있어야 해. 위에 있으면 `p5.WebSerial is not a constructor` 에러가 나.
6. 참고로 완성된 index.html은 이 모양이야 (`lab2/p5/index.html`):
```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.4.0/p5.js"></script>
    <script src="https://unpkg.com/p5-webserial@0.1.1/build/p5.webserial.js"></script>
    <link rel="stylesheet" type="text/css" href="style.css" />
  </head>
  <body>
    <main></main>
    <script src="sketch.js"></script>
  </body>
</html>
```

## 3단계. 브라우저가 WebSerial을 지원하는지 확인
왼쪽 파일 목록에서 **sketch.js** 클릭 → 전부 지우고 붙여넣기 → **▶ Play**
```js
// variable to hold an instance of the p5.webserial library:
const serial = new p5.WebSerial();

function setup() {
  // check to see if serial is available:
  if (!navigator.serial) {
    alert("WebSerial is not supported in this browser. Try Chrome or MS Edge.");
  }
}
```
- ✅ **아무 일도 안 일어나면 성공** (Chrome은 지원하니까 경고창이 안 떠).
- 경고창 "WebSerial is not supported"가 뜨면 → Safari에서 연 거야. Chrome으로.

## 4단계. 포트 연결 + 센서 값을 글자로 보기
sketch.js 전부 지우고 붙여넣기 → **▶ Play**. (랩 페이지의 Serial Events 코드 + Reading Incoming Serial Data의 draw를 합친 완성본이야)
```js
// variable to hold an instance of the p5.webserial library:
const serial = new p5.WebSerial();

// HTML button object:
let portButton;
let inData;                   // for incoming serial data
let outByte = 0;              // for outgoing data

function setup() {
  createCanvas(400, 300);          // make the canvas
  // check to see if serial is available:
  if (!navigator.serial) {
    alert("WebSerial is not supported in this browser. Try Chrome or MS Edge.");
  }
  // if serial is available, add connect/disconnect listeners:
  navigator.serial.addEventListener("connect", portConnect);
  navigator.serial.addEventListener("disconnect", portDisconnect);
  // check for any ports that are available:
  serial.getPorts();
  // if there's no port chosen, choose one:
  serial.on("noport", makePortButton);
  // open whatever port is available:
  serial.on("portavailable", openPort);
  // handle serial errors:
  serial.on("requesterror", portError);
  // handle any incoming serial data:
  serial.on("data", serialEvent);
  serial.on("close", makePortButton);
}

function draw() {
  background(0);
  fill(255);
  text("sensor value: " + inData, 30, 50);
}

// if there's no port selected,
// make a port select button appear:
function makePortButton() {
  // create and position a port chooser button:
  portButton = createButton("choose port");
  portButton.position(10, 10);
  // give the port button a mousepressed handler:
  portButton.mousePressed(choosePort);
}

// make the port selector window appear:
function choosePort() {
  if (portButton) portButton.show();
  serial.requestPort();
}

// open the selected port, and make the port
// button invisible:
function openPort() {
  // wait for the serial.open promise to return,
  // then call the initiateSerial function
  serial.open().then(initiateSerial);

  // once the port opens, let the user know:
  function initiateSerial() {
    console.log("port open");
  }
  // hide the port button once a port is chosen:
  if (portButton) portButton.hide();
}

// pop up an alert if there's a port error:
function portError(err) {
  alert("Serial port error: " + err);
}

// read any incoming data as a byte:
function serialEvent() {
  inData = Number(serial.read());
  console.log(inData);
}

// try to connect if a new serial port
// gets added (i.e. plugged in via USB):
function portConnect() {
  console.log("port connected");
  serial.getPorts();
}

// if a port is disconnected:
function portDisconnect() {
  serial.close();
  console.log("port disconnected");
}

function closePort() {
  serial.close();
}
```
1. 캔버스 왼쪽 위에 **`choose port`** 버튼 → 클릭
2. Chrome 팝업에서 **`Arduino NANO 33 IoT (cu.usbmodem…)`** 선택 → **연결(Connect)**
3. ✅ 검은 화면에 **`sensor value: 0`** → FSR을 누르면 숫자가 커져 (꽉 = 200대). 아래 Console에도 숫자가 흘러가.
4. 📸 FSR 누른 상태로 캡처
- 두 번째부터는 버튼 없이 **바로 연결**돼. 한 번 허락한 포트를 Chrome이 기억해서 (`getPorts` → `portavailable` → `openPort`).

**코드 읽는 법 (블로그용)**
| 이벤트 | 언제 | 실행되는 함수 |
|---|---|---|
| `noport` | 허락된 포트가 없을 때 | `makePortButton` → 버튼 생성 |
| `portavailable` | 포트를 고르거나 기억된 포트가 있을 때 | `openPort` → 포트 열고 버튼 숨김 |
| `data` | 바이트가 들어올 때마다 | `serialEvent` → `inData`에 저장 |
| `close` | 포트가 닫힐 때 | `makePortButton` |
| `requesterror` | 포트 고르기 창에서 취소 등 | `portError` → 경고창 |
- 숫자 흐름: FSR 꽉 → `analogRead` 900 → `map` 224 → `Serial.write(224)` 1바이트 → p5 `serial.read()` 224 → `inData = 224` → `draw()`가 "sensor value: 224" 표시

## 5단계. 그래프 그리기
sketch.js 전부 지우고 붙여넣기 → ▶ Play. (바뀐 곳: `xPos` 변수, `background`를 setup으로 이동, `graphData()` 추가, `draw()`는 `graphData(inData)`만)
```js
// variable to hold an instance of the p5.webserial library:
const serial = new p5.WebSerial();

// HTML button object:
let portButton;
let inData;                   // for incoming serial data
let outByte = 0;              // for outgoing data
let xPos = 0;                 // x position of the graph

function setup() {
  createCanvas(400, 300);          // make the canvas
  background(0x08, 0x16, 0x40);
  // check to see if serial is available:
  if (!navigator.serial) {
    alert("WebSerial is not supported in this browser. Try Chrome or MS Edge.");
  }
  // if serial is available, add connect/disconnect listeners:
  navigator.serial.addEventListener("connect", portConnect);
  navigator.serial.addEventListener("disconnect", portDisconnect);
  // check for any ports that are available:
  serial.getPorts();
  // if there's no port chosen, choose one:
  serial.on("noport", makePortButton);
  // open whatever port is available:
  serial.on("portavailable", openPort);
  // handle serial errors:
  serial.on("requesterror", portError);
  // handle any incoming serial data:
  serial.on("data", serialEvent);
  serial.on("close", makePortButton);
}

function draw() {
  graphData(inData);
}

function graphData(newData) {
  // map the range of the input to the window height:
  var yPos = map(newData, 0, 255, 0, height);
  // draw the line in a pretty color:
  stroke(0xA8, 0xD9, 0xA7);
  line(xPos, height, xPos, height - yPos);
  // at the edge of the screen, go back to the beginning:
  if (xPos >= width) {
    xPos = 0;
    // clear the screen by resetting the background:
    background(0x08, 0x16, 0x40);
  } else {
    // increment the horizontal position for the next reading:
    xPos++;
  }
}

// if there's no port selected,
// make a port select button appear:
function makePortButton() {
  // create and position a port chooser button:
  portButton = createButton("choose port");
  portButton.position(10, 10);
  // give the port button a mousepressed handler:
  portButton.mousePressed(choosePort);
}

// make the port selector window appear:
function choosePort() {
  if (portButton) portButton.show();
  serial.requestPort();
}

// open the selected port, and make the port
// button invisible:
function openPort() {
  // wait for the serial.open promise to return,
  // then call the initiateSerial function
  serial.open().then(initiateSerial);

  // once the port opens, let the user know:
  function initiateSerial() {
    console.log("port open");
  }
  // hide the port button once a port is chosen:
  if (portButton) portButton.hide();
}

// pop up an alert if there's a port error:
function portError(err) {
  alert("Serial port error: " + err);
}

// read any incoming data as a byte:
function serialEvent() {
  inData = Number(serial.read());
  console.log(inData);
}

// try to connect if a new serial port
// gets added (i.e. plugged in via USB):
function portConnect() {
  console.log("port connected");
  serial.getPorts();
}

// if a port is disconnected:
function portDisconnect() {
  serial.close();
  console.log("port disconnected");
}

function closePort() {
  serial.close();
}
```
- `xPos`: 지금 선을 그릴 x 위치. 매 프레임 1씩 오른쪽으로. 400(캔버스 끝)이 되면 0으로 돌아가고 화면을 지워.
- `yPos = map(newData, 0, 255, 0, height)`: 값 0 → 선 길이 0, 255 → 300(캔버스 높이)
  예: `inData = 127` → `yPos = 149` → 아래에서 149px 높이의 세로선
- ✅ 파란 화면에 초록 세로선이 왼쪽에서 오른쪽으로 쌓여. **FSR을 꾹 쥐면 산이 솟아.**
- 📸 뽀모처럼 몇 번 쥐었다 폈다 한 그래프 캡처 (블로그 핵심 이미지)
- 처음에 Console에 `🌸 p5.js says: map() was expecting Number…` 가 한 번 뜰 수 있어. 데이터가 오기 전 `inData`가 비어 있어서 그래. **정상이고 무시해도 돼.**

## 6단계. 아두이노를 글자(ASCII)로 보내면 어떻게 될까? (일부러 틀리게 해보기)
1. p5 **■ Stop**
2. 아두이노에 이 코드 업로드 (`write` → `println` 한 줄만 다름):
```cpp
// Lab 2, step 5: send the value as ASCII text with println() (adds \r\n).

void setup() {
  Serial.begin(9600); // initialize serial communications
}

void loop() {
  int potentiometer = analogRead(A0);                  // read the input pin
  int mappedPot = map(potentiometer, 0, 1023, 0, 255); // remap the pot value to fit in 1 byte
  Serial.println(mappedPot);                           // print it out the serial port
  delay(1);                                            // slight delay to stabilize the ADC
}
```
3. p5는 **5단계 코드 그대로** ▶ Play
4. ✅ **그래프가 낮고 이상하게** 나와. 값이 대부분 48~57이고 가끔 13, 10.
5. 📸 캡처 (블로그에 "왜 이상한가"를 쓰기 좋아)

**왜?** `println(224)`는 숫자 224가 아니라 글자 `'2' '2' '4' '\r' '\n'` **5바이트**를 보내. p5는 5단계 코드에서 한 바이트씩 숫자로 읽으니까:
| 글자 | `'2'` | `'2'` | `'4'` | `\r` | `\n` |
|---|---|---|---|---|---|
| p5가 받은 숫자 | 50 | 50 | 52 | 13 | 10 |
(랩 페이지 Figure 12는 `'8'`을 58이라고 적었는데 실제로는 56이야. `'0'`=48 … `'9'`=57)

## 7단계. 글자를 한 줄씩 읽기 (`readLine`)
아두이노는 6단계 그대로. p5 sketch.js 전부 지우고 붙여넣기 → ▶ Play. (바뀐 곳은 `serialEvent()` 하나)
```js
// variable to hold an instance of the p5.webserial library:
const serial = new p5.WebSerial();

// HTML button object:
let portButton;
let inData;                   // for incoming serial data
let outByte = 0;              // for outgoing data
let xPos = 0;                 // x position of the graph

function setup() {
  createCanvas(400, 300);          // make the canvas
  background(0x08, 0x16, 0x40);
  // check to see if serial is available:
  if (!navigator.serial) {
    alert("WebSerial is not supported in this browser. Try Chrome or MS Edge.");
  }
  // if serial is available, add connect/disconnect listeners:
  navigator.serial.addEventListener("connect", portConnect);
  navigator.serial.addEventListener("disconnect", portDisconnect);
  // check for any ports that are available:
  serial.getPorts();
  // if there's no port chosen, choose one:
  serial.on("noport", makePortButton);
  // open whatever port is available:
  serial.on("portavailable", openPort);
  // handle serial errors:
  serial.on("requesterror", portError);
  // handle any incoming serial data:
  serial.on("data", serialEvent);
  serial.on("close", makePortButton);
}

function draw() {
  graphData(inData);
}

function graphData(newData) {
  // map the range of the input to the window height:
  var yPos = map(newData, 0, 255, 0, height);
  // draw the line in a pretty color:
  stroke(0xA8, 0xD9, 0xA7);
  line(xPos, height, xPos, height - yPos);
  // at the edge of the screen, go back to the beginning:
  if (xPos >= width) {
    xPos = 0;
    // clear the screen by resetting the background:
    background(0x08, 0x16, 0x40);
  } else {
    // increment the horizontal position for the next reading:
    xPos++;
  }
}

// if there's no port selected,
// make a port select button appear:
function makePortButton() {
  // create and position a port chooser button:
  portButton = createButton("choose port");
  portButton.position(10, 10);
  // give the port button a mousepressed handler:
  portButton.mousePressed(choosePort);
}

// make the port selector window appear:
function choosePort() {
  if (portButton) portButton.show();
  serial.requestPort();
}

// open the selected port, and make the port
// button invisible:
function openPort() {
  // wait for the serial.open promise to return,
  // then call the initiateSerial function
  serial.open().then(initiateSerial);

  // once the port opens, let the user know:
  function initiateSerial() {
    console.log("port open");
  }
  // hide the port button once a port is chosen:
  if (portButton) portButton.hide();
}

// pop up an alert if there's a port error:
function portError(err) {
  alert("Serial port error: " + err);
}

function serialEvent() {
  // read a string from the serial port:
  var inString = serial.readLine();
  // check to see that there's actually a string there:
  if (inString) {
    // convert it to a number:
    inData = Number(inString);
  }
}

// try to connect if a new serial port
// gets added (i.e. plugged in via USB):
function portConnect() {
  console.log("port connected");
  serial.getPorts();
}

// if a port is disconnected:
function portDisconnect() {
  serial.close();
  console.log("port disconnected");
}

function closePort() {
  serial.close();
}
```
- `serial.readLine()`: `\r\n`이 올 때까지 모아서 `"224"` 같은 문자열 하나를 줘. 아직 줄이 다 안 왔으면 `null`.
- `if (inString)`: 줄이 완성됐을 때만 `inData`를 바꿔. 이게 없으면 그래프에 빈틈이 생겨.
- `Number("224")` → 224
- ✅ 그래프가 5단계처럼 다시 정상.
- 📸 캡처

## 8단계. 도전: 0~1023 전체 범위 보내기 (랩 마지막 문단 "See if you can…")
`write`는 1바이트라 255까지가 한계지만 `println`은 글자라서 1023도 보낼 수 있어.
1. p5 ■ Stop → 아두이노에 업로드:
```cpp
// Lab 2, step 7 (the lab's challenge): send the full 0-1023 range as ASCII text.
// No map() any more: println can send any number, not just one byte.

void setup() {
  Serial.begin(9600); // initialize serial communications
}

void loop() {
  int potentiometer = analogRead(A0);  // 0 - 1023 (A0 = FSR in our wiring)
  Serial.println(potentiometer);       // e.g. "812\r\n"
  delay(1);
}
```
2. p5 sketch.js 전부 지우고 붙여넣기 → ▶ Play (7단계에서 `map(newData, 0, 255, …)` → **`0, 1023`** 한 곳만 바뀜)
```js
// variable to hold an instance of the p5.webserial library:
const serial = new p5.WebSerial();

// HTML button object:
let portButton;
let inData;                   // for incoming serial data
let outByte = 0;              // for outgoing data
let xPos = 0;                 // x position of the graph

function setup() {
  createCanvas(400, 300);          // make the canvas
  background(0x08, 0x16, 0x40);
  // check to see if serial is available:
  if (!navigator.serial) {
    alert("WebSerial is not supported in this browser. Try Chrome or MS Edge.");
  }
  // if serial is available, add connect/disconnect listeners:
  navigator.serial.addEventListener("connect", portConnect);
  navigator.serial.addEventListener("disconnect", portDisconnect);
  // check for any ports that are available:
  serial.getPorts();
  // if there's no port chosen, choose one:
  serial.on("noport", makePortButton);
  // open whatever port is available:
  serial.on("portavailable", openPort);
  // handle serial errors:
  serial.on("requesterror", portError);
  // handle any incoming serial data:
  serial.on("data", serialEvent);
  serial.on("close", makePortButton);
}

function draw() {
  graphData(inData);
}

function graphData(newData) {
  // map the range of the input to the window height:
  var yPos = map(newData, 0, 1023, 0, height);   // full range: 0 - 1023
  // draw the line in a pretty color:
  stroke(0xA8, 0xD9, 0xA7);
  line(xPos, height, xPos, height - yPos);
  // at the edge of the screen, go back to the beginning:
  if (xPos >= width) {
    xPos = 0;
    // clear the screen by resetting the background:
    background(0x08, 0x16, 0x40);
  } else {
    // increment the horizontal position for the next reading:
    xPos++;
  }
}

// if there's no port selected,
// make a port select button appear:
function makePortButton() {
  // create and position a port chooser button:
  portButton = createButton("choose port");
  portButton.position(10, 10);
  // give the port button a mousepressed handler:
  portButton.mousePressed(choosePort);
}

// make the port selector window appear:
function choosePort() {
  if (portButton) portButton.show();
  serial.requestPort();
}

// open the selected port, and make the port
// button invisible:
function openPort() {
  // wait for the serial.open promise to return,
  // then call the initiateSerial function
  serial.open().then(initiateSerial);

  // once the port opens, let the user know:
  function initiateSerial() {
    console.log("port open");
  }
  // hide the port button once a port is chosen:
  if (portButton) portButton.hide();
}

// pop up an alert if there's a port error:
function portError(err) {
  alert("Serial port error: " + err);
}

function serialEvent() {
  // read a string from the serial port:
  var inString = serial.readLine();
  // check to see that there's actually a string there:
  if (inString) {
    // convert it to a number:
    inData = Number(inString);
  }
}

// try to connect if a new serial port
// gets added (i.e. plugged in via USB):
function portConnect() {
  console.log("port connected");
  serial.getPorts();
}

// if a port is disconnected:
function portDisconnect() {
  serial.close();
  console.log("port disconnected");
}

function closePort() {
  serial.close();
}
```
- 예: FSR 꽉 = 900 → `yPos = 900 / 1023 × 300 = 264`
- ✅ 7단계보다 더 섬세한 그래프. 📸 캡처. **이게 뽀모 쥐기 그래프 최종본.**

## 제출 전 체크리스트
- [ ] 4단계: `sensor value` 캡처 (FSR 누른 상태)
- [ ] 5단계: 쥐었다 폈다 그래프 캡처 (+ 짧은 영상 추천)
- [ ] 6단계: 깨진 그래프 캡처 + "왜?" (println(224) = 50,50,52,13,10)
- [ ] 7단계: readLine 그래프 캡처
- [ ] 8단계: 0~1023 그래프 캡처
- [ ] 블로그에 크레딧: "The code follows the ITP lab examples; the Ppomo version was adapted with help from Claude."

## 블로그 영어 문장 예시
- "I used the FSR on A0 instead of a potentiometer, so the graph shows each squeeze of Ppomo as a peak."
- "Serial.write() sends the value as one raw byte (0–255), so p5 reads it with serial.read(). Serial.println() sends ASCII text with \r\n, so p5 needs serial.readLine() and Number()."
- "When I sent println() data to the byte-reading sketch, the graph showed only values around 48–57 plus 13 and 10, because each digit arrived as its own ASCII byte."
- "Sending ASCII lets me send the full 0–1023 range, which a single byte cannot hold."

## 문제 해결
| 증상 | 원인 | 해결 |
|---|---|---|
| `p5.WebSerial is not a constructor` | 라이브러리 줄이 p5 줄보다 위, 또는 index.html에 없음 | 2단계 다시: p5 줄 **바로 아래**에 |
| `choose port` 버튼이 안 보임 | 이미 기억된 포트로 연결됐거나, 에러 | Console에 `port open`이 있으면 정상. 없으면 Console 에러 확인 |
| 포트 목록에 Arduino가 없음 | USB 케이블/허브 문제, 또는 다른 프로그램이 사용 중 | 시리얼 모니터 닫기, 다른 USB 구멍 |
| `Serial port error: …` / `Failed to open serial port` | 아두이노 IDE 시리얼 모니터가 열려 있음, 또는 다른 Chrome 탭이 연결 중 | 시리얼 모니터 닫기, 다른 p5 탭 닫기 → 새로고침 |
| 아두이노 업로드 실패 (port busy) | p5가 포트를 쓰는 중 | p5 ■ Stop 후 업로드 |
| `sensor value: undefined` | 아직 데이터가 안 옴 | 포트 연결됐는지 (Console `port open`), 아두이노에 1단계 코드가 올라갔는지 |
| 값이 0에서 안 변함 | 우리 배선에서 A0=FSR. 포텐셔미터를 돌리고 있는 건 아닌지 | FSR을 눌러봐. 포텐셔미터로 하려면 아두이노 코드 `A0`→`A1` |
| Nano 리셋 후 연결이 끊김 | Nano 33 IoT는 리셋하면 USB가 다시 연결됨 (랩 페이지 설명) | ▶ 다시 Play, 또는 `choose port` 다시 |
| **그래프가 손 동작보다 점점 늦게 따라옴** | 바이트가 한 번에 여러 개 도착하는데 `serialEvent`가 하나만 읽어서 밀림 (랩의 "Tricky Combination" 문단과 같은 현상). 테스트에서 실제로 재현됨 | 아래 코드로 `serialEvent`만 바꾸기 |

**밀림 해결용 `serialEvent` (필요할 때만)**
5단계 (바이트):
```js
function serialEvent() {
  // read every byte that is waiting, keep the newest one:
  while (serial.available() > 0) {
    inData = Number(serial.read());
  }
}
```
7·8단계 (문자열):
```js
function serialEvent() {
  // read a string from the serial port:
  var inString = serial.readLine();
  // read every complete line that is waiting, keep the newest one:
  while (inString) {
    inData = Number(inString);
    inString = serial.readLine();
  }
}
```
