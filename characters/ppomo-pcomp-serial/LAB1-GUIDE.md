# 랩 1 따라하기: Intro to Asynchronous Serial Communications (뽀모 버전: FSR + 포텐셔미터 + 버튼)

총 1시간 40분 정도 걸려 (선택 단계 빼고). 순서대로만 하면 돼. 각 단계 끝의 ✅ 확인이 안 되면 다음 단계로 넘어가지 말고, 맨 아래 "문제 해결" 표를 먼저 봐.

## 준비물
| 부품 | 개수 | 확인 방법 |
|---|---|---|
| Arduino Nano 33 IoT + **데이터 전송되는** USB 케이블 | 1 | 충전 전용 케이블이면 업로드가 안 돼 |
| 브레드보드 | 1 | |
| FSR (동그란 압력 센서) | 1 | |
| 포텐셔미터 (돌리는 손잡이, 다리 3개) | 1 | |
| 푸시버튼 (다리 4개짜리 작은 버튼) | 1 | |
| 10kΩ 저항 | 2 | 띠 색: **갈색-검정-주황** (220Ω인 빨강-빨강-갈색과 헷갈리지 않기) |
| 점퍼선 | 8개 정도 | |

## 0단계. 업로드 테스트 (10분) — 배선 전에 먼저!
배선하기 전에 보드·케이블·프로그램이 정상인지 먼저 확인해. 나중에 안 될 때 원인을 반으로 줄여줘.

1. Arduino IDE 2를 열어.
2. 보드 패키지 설치 (처음 한 번만): **Tools → Board → Boards Manager**
   → 검색창에 `SAMD` → **Arduino SAMD Boards (32-bits ARM Cortex-M0+)** → **Install**
3. 보드 선택: **Tools → Board → Arduino SAMD Boards → Arduino NANO 33 IoT**
4. USB로 Nano를 꽂고 포트 선택: **Tools → Port →** 이름에 `(Arduino NANO 33 IoT)`가 붙은 것
5. **File → Examples → 01.Basics → Blink** → 업로드 버튼(→ 화살표)
6. ✅ **확인:** 보드 위 작은 주황 LED가 1초 간격으로 깜빡이면 성공.
   하단에 "Done uploading"이 떠.

## 1단계. 배선 (20분)
**`lab1-breadboard.png` 그림 하나만 보고 ①~⑭ 순서로 꽂으면 끝이야.** 아래 글은 헷갈릴 때만 참고해. **배선하는 동안은 USB를 빼둬.**

**브레드보드 규칙 2개만 기억해**
- 가운데 홈을 기준으로 **같은 번호 줄의 구멍 5개는 서로 연결**돼 있어.
- 양옆의 긴 줄(빨강 +, 파랑 −)은 **세로로 쭉 연결**돼 있어. 이걸 "레일"이라고 불러. 양쪽에 레일이 있으면 **한쪽만** 써. 양쪽은 서로 연결 안 돼 있어.

**순서**
1. Nano를 브레드보드 **가운데 홈을 가로지르게** 꽂아. 다리가 홈 양쪽으로 나뉘게.
2. **Step 0 (레일에 전기 넣기):**
   - Nano에서 **`3V3`** 라고 쓰인 핀이 꽂힌 줄 → 점퍼선 → **빨강 + 레일**
   - Nano에서 **`GND`** 라고 쓰인 핀이 꽂힌 줄 → 점퍼선 → **파랑 − 레일**
   - ⚠️ `5V`나 `VUSB`는 쓰지 마. Nano 33 IoT는 3.3V 보드야.
3. **① FSR → A0**
   - FSR 다리 두 개를 **서로 다른 줄**에 꽂아. (예: 다리1은 30번 줄, 다리2는 32번 줄). 방향은 상관없어.
   - 다리1 줄 → 점퍼선 → **+ 레일**
   - 다리2 줄 → **10kΩ 저항** 한쪽. 저항 다른 쪽 → **− 레일**
   - 다리2 줄 → 점퍼선 → Nano **`A0`** 핀이 꽂힌 줄
   - 즉 A0 선은 "FSR과 저항 사이"에 연결돼.
   - FSR 다리가 얇아서 헐거우면 살짝 깊게 꽂거나, 암-수 점퍼선에 끼워서 연결해.
4. **② 포텐셔미터 → A1**
   - 다리 3개를 **서로 다른 줄 3개**에 꽂아.
   - 왼쪽 다리 → **+ 레일**, 오른쪽 다리 → **− 레일**, **가운데 다리 → Nano `A1`**
5. **③ 버튼 → D2**
   - 버튼을 가운데 홈을 가로지르게 꽂아.
   - **대각선으로 마주 보는 다리 두 개**만 써. 대각선 다리는 항상 "누를 때만 연결"되는 짝이라 방향을 헷갈릴 일이 없어.
   - 대각선 다리 A → **+ 레일**
   - 대각선 다리 B 줄 → **10kΩ 저항** → **− 레일**
   - 대각선 다리 B 줄 → 점퍼선 → Nano **`D2`**
6. **꽂기 전 최종 점검**
   - [ ] 3V3 → + 레일, GND → − 레일
   - [ ] 저항 2개 모두 갈색-검정-주황 (10kΩ)
   - [ ] A0 선이 FSR과 저항 **사이** 줄에
   - [ ] D2 선이 버튼과 저항 **사이** 줄에
   - [ ] 5V/VUSB 핀에는 아무것도 없음
7. USB를 꽂아. ✅ 보드 초록 전원 LED가 켜지고 뜨거워지지 않으면 OK.
   **뜨거워지면 바로 USB를 빼.** 3V3와 GND가 바로 이어진 거야.


## 랩 페이지와 이 가이드의 대응표
랩 페이지 순서 그대로 따라가. 센서만 바꿨어. 랩 페이지에 "any two analog sensors"라고 되어 있어서 **A0에 FSR**, **A1에 포텐셔미터**를 써도 과제와 맞아.

| 랩 페이지 섹션 | 이 가이드 | 코드 폴더 |
|---|---|---|
| Prepare the breadboard / Add an analog sensor | 0~1단계 | |
| Program the Arduino module (`println`) | 2단계 | `lab1-1-println` |
| `map()` to 0–255 | 3단계 | `lab1-2-map` |
| `Serial.write()` | 4단계 | `lab1-3-write` |
| Send the data in many formats | 5단계 | `lab1-4-formats` |
| Send the values for all three sensors (punctuation) | 6단계 | `lab1-5-three-sensors` |
| Flow control: call and response (handshaking) | 7단계 | `lab1-6-handshake` |
| Other serial terminal programs (선택) | 8단계 | |
| 보너스: 뽀모 데이터 CSV로 저장 | 9단계 | |

**코드 여는 법:** Arduino IDE에서 **File → Open** → 이 저장소 폴더의 `characters/ppomo-pcomp-serial/폴더이름/폴더이름.ino`.
또는 **File → New Sketch** 만들고 아래 코드를 전부 지우고 붙여넣어도 돼.

**모든 단계 공통 순서:** 코드 붙여넣기 → 업로드(→ 버튼) → "Done uploading" 확인 → 시리얼 모니터 열기(오른쪽 위 돋보기) → 속도 **9600 baud**.
**업로드할 때는 시리얼 플로터를 닫아.** 모니터는 열어둬도 IDE가 알아서 처리해.

## 2단계. println: 센서 값을 글자로 보내기 (5분)
코드 (`lab1-1-println`):
```cpp
void setup() {
  Serial.begin(9600);
}

void loop() {
  int analogValue = analogRead(A0);
  Serial.println(analogValue);
}
```
**변수 설명**
- `analogValue`: A0 핀 전압을 0~1023 숫자로 바꾼 값. 0 = 0V, 1023 = 3.3V.
- 예: FSR을 안 누르면 0, 살짝 누르면 300, 꽉 누르면 900.

**해볼 것**
1. 업로드 → 모니터 (9600)
2. ✅ 숫자가 한 줄에 하나씩 빠르게 흘러가. FSR을 누르면 커져.
3. 📸 캡처 (누른 상태).

## 3단계. map(): 0~1023 을 0~255 로 줄이기 (5분)
**왜?** 한 바이트(byte)는 0~255까지만 담을 수 있어. 다음 단계에서 `write()`로 "한 바이트"를 보낼 거라 먼저 범위를 줄여.

코드 (`lab1-2-map`):
```cpp
void setup() {
  Serial.begin(9600);
}

void loop() {
  int analogValue = analogRead(A0);
  int mappedValue = map(analogValue, 0, 1023, 0, 255);
  Serial.println(mappedValue);
}
```
**숫자 따라가기**
- `map(값, 원래최소, 원래최대, 새최소, 새최대)`
- `analogValue = 0` → `mappedValue = 0`
- `analogValue = 512` → 512 × 255 ÷ 1023 = 127.6 → 정수라 **127**
- `analogValue = 1023` → **255**
- 참고: 랩 페이지에도 나오듯이 `analogRead(A0) / 4` 도 거의 같은 결과야 (1023 ÷ 4 = 255). 과제는 `map()` 버전으로 해.

**해볼 것**
1. 업로드 → 모니터
2. ✅ 이제 숫자가 **0~255** 사이에서만 움직여. FSR 꽉 = 200대.

## 4단계. Serial.write(): 숫자를 "바이트 그대로" 보내기 (5분)
코드 (`lab1-3-write`): 3단계에서 **마지막 줄 하나만** 바뀌어.
```cpp
void setup() {
  Serial.begin(9600);
}

void loop() {
  int analogValue = analogRead(A0);
  int mappedValue = map(analogValue, 0, 1023, 0, 255);
  Serial.write(mappedValue);
}
```
**해볼 것**
1. 업로드 → 모니터
2. ✅ **이상한 기호, 네모, `�`** 가 나오거나 아무것도 안 보여. **이게 정상이야. 고장 아님.**
3. 📸 캡처 (FSR 누른 상태로).

**왜 이상한 글자가 나와? (블로그에 쓸 핵심)**
- 모니터는 받은 바이트를 전부 **ASCII 글자표**로 바꿔서 보여줘.
- `Serial.write(32)` → 바이트 **1개** `32`가 감 → ASCII 32번은 **스페이스(빈칸)** → 화면에 아무것도 없는 것처럼 보여.
- `Serial.write(65)` → 바이트 1개 `65` → ASCII 65번은 **`A`** → 화면에 `A`.
- `Serial.println(32)` → 바이트 **4개**가 감:
  | 보낸 글자 | `'3'` | `'2'` | `\r` | `\n` |
  |---|---|---|---|---|
  | 실제 바이트 값 | 51 | 50 | 13 | 10 |
  → 모니터는 이걸 `32` 그리고 줄바꿈으로 보여줘.
- 정리: **`write()` = 숫자 자체 1바이트 (기계용)**, **`print()`/`println()` = 숫자를 글자로 바꿔 여러 바이트 (사람용)**.
- 안 누를 때(0)는 ASCII 0번이 "안 보이는 글자"라 아무것도 안 나와.
- 128 이상은 표준 ASCII 밖이라 IDE 2는 `�`로 보여줘.

## 5단계. 여러 형식으로 한 번에 보내기 (10분)
같은 값을 **원시 바이트 / 2진수 / 10진수 / 16진수 / 8진수**로 한 줄에 보내.

코드 (`lab1-4-formats`):
```cpp
void setup() {
  Serial.begin(9600);
}

void loop() {
  int analogValue = analogRead(A0);
  int mappedValue = map(analogValue, 0, 1023, 0, 255);

  Serial.write(mappedValue);        // raw byte
  Serial.print("\t");               // tab
  Serial.print(mappedValue, BIN);   // binary
  Serial.print("\t");
  Serial.print(mappedValue, DEC);   // decimal
  Serial.print("\t");
  Serial.print(mappedValue, HEX);   // hexadecimal
  Serial.print("\t");
  Serial.print(mappedValue, OCT);   // octal
  Serial.println();                 // end of line: \r\n
}
```
**해볼 것**
1. 업로드 → 모니터
2. FSR을 꽉 눌러서 값이 200대가 되게.
3. ✅ 이런 줄이 나와 (값이 226일 때):
```
â	11100010	226	E2	342
```
   - IDE 2에서는 첫 칸이 `â` 대신 `�`로 보일 수 있어. 정상이야.
4. 📸 캡처.

**한 값을 다섯 가지로 읽기 (226 예시)**
| 형식 | 화면 | 계산 |
|---|---|---|
| write (원시 바이트) | `â` | 226번 글자 |
| BIN (2진수) | `11100010` | 128+64+32+2 = 226 |
| DEC (10진수) | `226` | |
| HEX (16진수) | `E2` | 14×16 + 2 = 226 (E = 14) |
| OCT (8진수) | `342` | 3×64 + 4×8 + 2 = 226 |

**특수 글자 3개**
- `\t` (tab, ASCII 9): 다음 칸으로 띄우기. 위 줄에서 값 사이 간격.
- `\r` (carriage return, ASCII 13): 커서를 줄 맨 앞으로.
- `\n` (newline, ASCII 10): 다음 줄로.
- `println()` 은 끝에 `\r\n` 두 개를 붙여. 그래서 "한 덩어리 끝" 표시로 쓸 수 있어. 이게 다음 단계의 핵심.

## 6단계. 센서 3개 값 보내기 + 구두점(punctuation) (20분)

### 6-1. 먼저 "구분 없이" 보내면 생기는 문제 (설명만, 2분)
세 값을 그냥 붙여서 `print`만 하면:
```
5121023051210230...
```
- 이게 `512, 1023, 0` 인지 `5, 121, 0230` 인지 **받는 쪽이 알 수 없어.**
- 해결: 값 사이에 **쉼표(,)**, 한 묶음 끝에 **줄바꿈(println)** 을 넣어. 이게 punctuation 방식이야.

### 6-2. 쉼표 + 줄바꿈 버전 (과제 코드)
코드 (`lab1-5-three-sensors`):
```cpp
const int switchPin = 2;     // digital input

void setup() {
  Serial.begin(9600);
  pinMode(switchPin, INPUT);
}

void loop() {
  int sensorValue = analogRead(A0);   // FSR
  Serial.print(sensorValue);
  Serial.print(",");

  sensorValue = analogRead(A1);       // potentiometer
  Serial.print(sensorValue);
  Serial.print(",");

  sensorValue = digitalRead(switchPin);  // button: 0 or 1
  Serial.println(sensorValue);        // println = this reading is finished
}
```
**변수 설명**
- `switchPin = 2`: 버튼이 꽂힌 핀 번호. `const`는 "안 바뀌는 값".
- `sensorValue`: 상자 하나를 **세 번 재사용**해. A0 값 넣고 보내고 → A1 값 넣고 보내고 → 버튼 값 넣고 보내고.
- 한 줄 예: `812,512,0` = FSR 812(꽉 쥠), pot 512(중간), 버튼 0(안 누름).

**해볼 것**
1. 업로드 → 모니터 (9600)
2. ✅ 이런 줄이 계속 흘러가:
```
0,512,0        ← 아무것도 안 만짐 (pot은 돌린 위치에 따라 0~1023)
640,512,0      ← FSR 누르는 중
0,1023,0       ← pot 끝까지 돌림
0,512,1        ← 버튼 누름
```
3. 하나씩 확인
   - [ ] FSR: 안 누르면 0 근처, 누르면 수백까지 올라감
   - [ ] pot: 끝에서 끝까지 돌리면 0 ↔ 1023 (왼쪽 다리=+, 오른쪽 다리=− 이면 시계방향으로 돌릴수록 작아질 수 있어. 정상)
   - [ ] 버튼: 누를 때만 1
4. 📸 캡처.
5. **그래프로 보기 (블로그용, 선택):** 시리얼 모니터 창을 닫고 → **Tools → Serial Plotter** (9600) → 선 3개. FSR을 꾹꾹 누르면 산 모양. 📸 캡처.
6. **뽀모 R&D 측정 (블로그 핵심):** 모니터를 보면서 아래 표를 채워. 이 숫자가 랩 2의 기준값이 돼.

| 측정 | FSR 값 |
|---|---|
| 안 누를 때 | |
| 손가락으로 살짝 | |
| 꽉 | |
| 스트레스볼과 손바닥 사이에 끼우고 쥘 때 | |
| 꽉 누른 채 5초 유지하면 숫자가 변하나? (예: 850 → 890) | |
| 놓으면 바로 0으로 돌아오나? | |

## 7단계. 주고받기 (call and response, handshaking) (15분)
**목적:** 아두이노가 쉬지 않고 보내는 대신 **컴퓨터가 요청할 때만 한 줄씩** 보내기. 받는 쪽이 느려도 데이터가 밀리지 않아.

랩 페이지 코드는 "나머지는 그대로"라고 줄여 써서 그대로 붙이면 `sensorValue`가 선언 안 돼서 에러가 나. 아래는 **그대로 컴파일되는 완성본**이야.

코드 (`lab1-6-handshake`):
```cpp
const int switchPin = 2;
int sensorValue = 0;

void setup() {
  Serial.begin(9600);
  pinMode(switchPin, INPUT);
  while (Serial.available() <= 0) {   // nothing received yet
    Serial.println("hello");          // keep asking
    delay(300);
  }
}

void loop() {
  if (Serial.available() > 0) {       // the computer sent something
    int inByte = Serial.read();       // take that byte out of the buffer

    sensorValue = analogRead(A0);
    Serial.print(sensorValue);
    Serial.print(",");

    sensorValue = analogRead(A1);
    Serial.print(sensorValue);
    Serial.print(",");

    sensorValue = digitalRead(switchPin);
    Serial.println(sensorValue);
  }
}
```
**변수 설명**
- `Serial.available()`: 컴퓨터가 보내서 아직 안 읽은 바이트 수. 아무것도 안 왔으면 0.
- `inByte`: 컴퓨터가 보낸 바이트. 예: `x`를 보내면 120. 값은 안 쓰고 **꺼내서 버퍼를 비우는 용도**야. 안 꺼내면 `available()`이 계속 1이라 쉬지 않고 보내게 돼.

**해볼 것**
1. 업로드 → 모니터 (9600)
2. ✅ `hello`가 0.3초마다 찍혀. 아두이노가 "누구 있어요?" 하는 중.
3. 모니터 입력칸 오른쪽의 줄바꿈 선택칸을 **No Line Ending** 으로 바꿔.
4. 입력칸 클릭 → `x` 하나 입력 → **Enter** (랩 페이지의 "click Send"가 IDE 2에서는 Enter야)
5. ✅ `hello`가 멈추고 **딱 한 줄** 나와. 예: `0,512,0`
6. FSR을 누른 채로 또 `x` + Enter → 누른 값 한 줄. **보낼 때마다 한 줄**.
7. 참고
   - 줄바꿈 선택이 **New Line**이면 Enter 한 번에 `x`와 `\n` **2바이트**가 가서 **두 줄**이 나와. 고장 아니고, 오히려 "바이트 1개당 한 줄"이라는 증거야. 블로그에 써도 좋아.
   - `xxx` + Enter (No Line Ending) → 세 줄.
   - 다시 `hello`부터 보려면 Nano의 **리셋 버튼 한 번** → 모니터 다시 열기.
8. 📸 hello → x → 한 줄 응답 화면 캡처.

## 8단계. (선택) 다른 시리얼 터미널 프로그램
랩 페이지에서 "optional"인 부분이야. 시간이 있으면 하나만 해봐. **먼저 Arduino IDE 시리얼 모니터를 닫아.** 한 포트는 한 프로그램만 쓸 수 있어.

**CoolTerm (추천, 맥/윈도우)**
1. 설치 후 실행 → **Options** → Port에서 `usbmodem...`(맥) / `COM...`(윈도우) 선택, Baudrate **9600** → OK
2. **Connect** → 6단계 코드면 값이 흘러가.
3. **View → View Hex** (또는 ⌘/Ctrl + Shift + H): 같은 데이터를 16진수 바이트로 봐.
   - 예: `512,0` 다음 줄바꿈 → `35 31 32 2C 30 0D 0A`
   - `2C` = 쉼표, `0D 0A` = `\r\n`. 5단계 표와 연결해서 블로그에 쓰기 좋아.
4. 끝나면 **Disconnect** (안 하면 IDE 업로드가 실패해).

**맥 터미널**
```bash
ls -1 /dev/cu.*                     # 포트 이름 찾기 (예: /dev/cu.usbmodem14101)
cat /dev/cu.usbmodem14101           # 값 보기, 멈추려면 ctrl-C
screen /dev/cu.usbmodem14101 9600   # 주고받기용, 끝내려면 ctrl-A 누르고 ctrl-D
```
- `usbmodem14101`은 예시야. `ls` 결과에 나온 이름을 그대로 써.
- 7단계 코드에서 `screen`으로 연결하고 `x`를 누르면 한 줄씩 응답해.

**윈도우 (WSL)**: `sudo cat /dev/ttyS3` (COM3 → ttyS3처럼 숫자를 맞춰).

## 9단계. 보너스: 뽀모 쥐기 데이터를 CSV로 저장 (맥, 5분)
6단계 코드가 이미 CSV 형식이라 **그대로 파일로 저장**하면 엑셀/구글시트에서 열 수 있어. 뽀모 R&D에 바로 쓸 수 있는 실험 기록이야.
1. 6단계 코드에서 `Serial.println(sensorValue);` 다음 줄에 `delay(10);` 을 추가하고 다시 업로드. (Nano 33 IoT는 USB가 빨라서 delay 없으면 몇 초에 파일이 수만 줄이 돼.)
2. 시리얼 모니터/플로터/CoolTerm **모두 닫기**.
3. 터미널:
```bash
cd ~/Desktop
cat /dev/cu.usbmodem14101 > datalog.csv
```
4. 20초 동안: 5초 가만히 → 5초 살짝 쥐기 → 5초 꽉 쥐기 → 5초 쥐었다 폈다.
5. **ctrl-C** 로 멈춤 → 바탕화면의 `datalog.csv`를 구글시트로 열고 첫 열(FSR)로 선 그래프. 📸 캡처.
   - 첫 줄이 잘려 있을 수 있어. 지우면 돼.

## 10단계. 제출 전 체크리스트
- [ ] 배선 사진 1장 (위에서)
- [ ] 2단계: println 0~1023 캡처
- [ ] 3단계: map 0~255 캡처
- [ ] 4단계: write 이상한 글자 캡처 + "왜?" 설명 (32 → 스페이스, println(32) → 51,50,13,10)
- [ ] 5단계: 여러 형식 한 줄 캡처 + 표
- [ ] 6단계: `fsr,pot,button` 캡처 + 측정 표 (+ 선택: 플로터)
- [ ] 7단계: hello → x → 한 줄 응답 캡처
- [ ] (선택) 8단계 CoolTerm hex 화면, 9단계 CSV 그래프
- [ ] 블로그에 "The sketch code follows the ITP lab examples; the Ppomo version was written with help from Claude." 한 줄

**랩 2로 넘어가기 전에:** 시리얼 모니터와 플로터를 **닫아.** 한 포트는 한 프로그램만 쓸 수 있어서 p5가 연결을 못 해.

## 문제 해결
| 증상 | 원인 | 해결 |
|---|---|---|
| 포트 목록에 Nano가 없음 / "No device found" | 충전 전용 케이블, 또는 보드가 멈춤 | ① 다른 케이블이나 다른 USB 구멍 ② Nano 리셋 버튼을 **빠르게 두 번** → LED가 천천히 깜빡이면 포트를 다시 고르고 업로드 |
| Board 목록에 NANO 33 IoT 없음 | 보드 패키지 미설치 | 0단계 2번 |
| 모니터에 깨진 글자 (write 단계 말고 다른 단계에서) | 속도 불일치 | 모니터 속도를 **9600**으로 |
| 모니터에 아무것도 안 나옴 | 포트가 틀림, 또는 업로드 중이었음 | 포트 확인 → 모니터 닫았다 다시 열기 |
| "Port busy" / 업로드 실패 | 플로터, p5 페이지 등이 포트를 쓰는 중 | 시리얼 모니터, 플로터, p5 탭을 다 닫고 다시 |
| FSR이 계속 0 | FSR 다리가 헐겁거나, + 레일에 전기가 안 감 | FSR 다시 꽂기, Step 0의 3V3 선 확인, 같은 쪽 레일인지 확인 |
| FSR이 계속 1023 근처 | 10kΩ가 빠졌거나 다른 줄에 꽂힘 | A0 줄에 저항이 꽂혀 있고 반대쪽이 − 레일인지 확인 |
| 안 만져도 FSR 값이 마구 출렁임 | A0 선이 FSR-저항 사이 줄에 안 꽂힘 | A0 선 위치 확인 |
| pot이 0이나 1023에서 안 움직임 | 가운데 다리가 A1이 아님 | 가운데 다리 ↔ A1 확인. 바깥 다리 둘이 각각 +, − 인지 |
| 버튼이 항상 1 | 대각선이 아닌 다리를 써서 늘 연결됨 | 버튼을 90도 돌려 꽂거나 대각선 다리로 |
| 버튼이 항상 0 | 버튼에 3V3가 안 감, 또는 D2 선 위치 | 대각선 다리 A가 + 레일인지, D2가 버튼-저항 사이인지 |
| 버튼을 안 눌러도 0과 1이 왔다 갔다 | 10kΩ(풀다운)이 없거나 헐거움 | D2 줄 ↔ 10kΩ ↔ − 레일 확인 |
| 7단계에서 x를 보내도 반응 없음 | 입력칸에 커서가 없었거나 Enter 안 누름, 7단계 코드가 아님 | 입력칸 클릭 후 x + Enter, 업로드한 코드 확인 |
| 랩 페이지 코드를 붙였더니 `sensorValue was not declared` | 랩 페이지의 handshake 코드는 일부만 보여줌 | 7단계의 완성본 코드를 써 |
| 터미널 `cat`이 "Resource busy" | IDE 모니터나 CoolTerm이 포트를 쓰는 중 | 다른 프로그램 모두 닫기 (CoolTerm은 Disconnect) |
| Nano가 뜨거움 | 3V3와 GND가 바로 연결됨 (합선) | **즉시 USB 분리**, 레일 선 확인 |
