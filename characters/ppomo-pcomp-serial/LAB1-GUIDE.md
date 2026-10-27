# 랩 1 따라하기: Intro to Asynchronous Serial (뽀모 버전, FSR + 포텐셔미터 + 버튼)

총 1시간 30분 정도 걸려. 순서대로만 하면 돼. 각 단계 끝의 ✅ 확인이 안 되면 다음 단계로 넘어가지 말고, 맨 아래 "문제 해결" 표를 먼저 봐.

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
`lab1-wiring.png` 그림을 옆에 띄워놓고 해. **배선하는 동안은 USB를 빼둬.**

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

## 2단계. Part A — Serial.write: 숫자를 "바이트"로 보내기 (10분)
**목적:** `write()`는 숫자를 사람이 읽는 글자가 아니라 **한 바이트 그대로** 보낸다는 걸 확인하기.

코드 (`lab1a-write/lab1a-write.ino`):
```cpp
void setup() {
  Serial.begin(9600);
}

void loop() {
  int analogValue = analogRead(A0) / 4;   // 0-1023 divided by 4 = 0-255, so it fits in one byte
  Serial.write(analogValue);              // send that one byte
  delay(10);
}
```
1. 업로드
2. 시리얼 모니터 열기: 오른쪽 위 **돋보기 아이콘** (또는 Tools → Serial Monitor)
3. 모니터 오른쪽 속도 선택칸을 **9600 baud**로
4. FSR을 눌렀다 뗐다 해봐.

✅ **기대 결과:** **이상한 기호, 네모, 알 수 없는 글자**가 나오거나 아무것도 안 보여. **이게 정상이야.**
- 안 누를 때 값은 0. 0번 글자는 눈에 안 보이는 글자라 아무것도 안 나와.
- 누르면 예를 들어 65가 가면 모니터는 65번 글자인 `A`로 보여줘. 숫자 "65"가 아니라.
- 📸 이 화면을 캡처해. 블로그에 "write는 바이트, print는 글자"를 설명하는 증거야.

## 3단계. Part B — 세 값을 쉼표로 묶어 보내기 (20분)
**목적:** 여러 센서 값을 사람이 읽을 수 있는 글자로, **쉼표(,)와 줄바꿈으로 구분해서** 보내기. 랩 2(p5로 받기)도 이 방식을 써.

코드 (`lab1-ppomo/lab1-ppomo.ino`):
```cpp
const int fsrPin = A0;
const int potPin = A1;
const int buttonPin = 2;

void setup() {
  Serial.begin(9600);
  pinMode(buttonPin, INPUT);
}

void loop() {
  int fsr = analogRead(fsrPin);         // 0 - 1023
  int pot = analogRead(potPin);         // 0 - 1023
  int button = digitalRead(buttonPin);  // 0 or 1

  Serial.print(fsr);
  Serial.print(",");
  Serial.print(pot);
  Serial.print(",");
  Serial.println(button);
  delay(10);
}
```
1. 업로드 → 시리얼 모니터 (9600)
2. ✅ **기대 결과:** 이런 줄이 계속 흘러가.
```
0,512,0        ← 아무것도 안 만짐 (pot은 돌린 위치에 따라 0~1023)
640,512,0      ← FSR 누르는 중
0,1023,0       ← pot 끝까지 돌림
0,512,1        ← 버튼 누름
```
3. 하나씩 확인
   - [ ] FSR: 안 누르면 0 근처, 누르면 수백까지 올라감
   - [ ] pot: 끝에서 끝까지 돌리면 0 ↔ 1023
   - [ ] 버튼: 누를 때만 1
4. **그래프로 보기 (블로그용):** 시리얼 모니터 창을 닫고 → **Tools → Serial Plotter** (9600)
   → 선 3개가 그려져. FSR을 꾹꾹 누르면 산 모양이 생겨. 📸 캡처해.
5. **뽀모 R&D 측정 (여기가 블로그 핵심):** 아래 표를 채워. 다시 시리얼 모니터로 보면서 해.

| 측정 | 값 |
|---|---|
| FSR 안 누를 때 | |
| FSR 손가락으로 살짝 | |
| FSR 꽉 | |
| FSR을 스트레스볼과 손바닥 사이에 끼우고 쥘 때 | |
| FSR 꽉 누른 채 5초 유지하면 숫자가 변하나? (예: 850 → 890) | |
| FSR 놓으면 바로 0으로 돌아오나? | |

## 4단계. Part C — 주고받기 (handshake, call and response) (15분)
**목적:** 아두이노가 계속 보내는 게 아니라, **컴퓨터가 요청할 때만** 하나씩 보내기.

코드 (`lab1c-handshake/lab1c-handshake.ino`):
```cpp
const int fsrPin = A0;
const int potPin = A1;
const int buttonPin = 2;

void setup() {
  Serial.begin(9600);
  pinMode(buttonPin, INPUT);
  while (Serial.available() <= 0) {   // nothing received yet
    Serial.println("hello");          // keep asking
    delay(300);
  }
}

void loop() {
  if (Serial.available() > 0) {       // the computer sent something
    Serial.read();                    // take that character out of the buffer
    int fsr = analogRead(fsrPin);
    int pot = analogRead(potPin);
    int button = digitalRead(buttonPin);
    Serial.print(fsr);
    Serial.print(",");
    Serial.print(pot);
    Serial.print(",");
    Serial.println(button);
  }
}
```
1. 업로드 → 시리얼 모니터 (9600)
2. ✅ `hello`가 계속 찍혀. 아두이노가 "누구 있어요?" 하는 중이야.
3. 모니터 위쪽 입력칸 옆의 줄바꿈 선택칸을 **No Line Ending**으로 바꿔.
4. 입력칸에 `x` 하나 치고 **Enter**
5. ✅ `hello`가 멈추고 **딱 한 줄**의 값이 나와. (예: `0,512,0`)
6. FSR을 누른 채로 또 `x` + Enter → 누른 값이 한 줄 나와. **보낼 때마다 한 줄씩**이야.
7. 참고
   - 줄바꿈 선택이 "Newline"이면 Enter 한 번에 글자 2개(x와 줄바꿈)가 가서 **두 줄**이 나와. 고장 아니야.
   - 다시 `hello`부터 보고 싶으면 Nano의 **리셋 버튼을 한 번** 누르고 모니터를 다시 열어.
8. 📸 hello → x 입력 → 한 줄 응답 화면을 캡처해.

## 5단계. 제출 전 체크리스트
- [ ] 배선 사진 1장 (위에서 찍기)
- [ ] Part A: write 화면 캡처 (이상한 글자)
- [ ] Part B: 시리얼 모니터 캡처 + 시리얼 플로터 캡처
- [ ] Part B: 측정 표 채움
- [ ] Part C: hello → 응답 캡처
- [ ] (선택) FSR 쥐는 짧은 영상

**랩 2로 넘어가기 전에:** Part B 코드(`lab1-ppomo`)를 다시 업로드해두고, **시리얼 모니터와 플로터를 닫아.** 한 포트는 한 프로그램만 쓸 수 있어서 p5가 연결을 못 해.

## 문제 해결
| 증상 | 원인 | 해결 |
|---|---|---|
| 포트 목록에 Nano가 없음 / "No device found" | 충전 전용 케이블, 또는 보드가 멈춤 | ① 다른 케이블이나 다른 USB 구멍 ② Nano 리셋 버튼을 **빠르게 두 번** → LED가 천천히 깜빡이면 포트를 다시 고르고 업로드 |
| Board 목록에 NANO 33 IoT 없음 | 보드 패키지 미설치 | 0단계 2번 |
| 모니터에 깨진 글자 (Part B·C에서) | 속도 불일치 | 모니터 속도를 **9600**으로 |
| 모니터에 아무것도 안 나옴 | 포트가 틀림, 또는 업로드 중이었음 | 포트 확인 → 모니터 닫았다 다시 열기 |
| "Port busy" / 업로드 실패 | 플로터, p5 페이지 등이 포트를 쓰는 중 | 시리얼 모니터, 플로터, p5 탭을 다 닫고 다시 |
| FSR이 계속 0 | FSR 다리가 헐겁거나, + 레일에 전기가 안 감 | FSR 다시 꽂기, Step 0의 3V3 선 확인, 같은 쪽 레일인지 확인 |
| FSR이 계속 1023 근처 | 10kΩ가 빠졌거나 다른 줄에 꽂힘 | A0 줄에 저항이 꽂혀 있고 반대쪽이 − 레일인지 확인 |
| 안 만져도 FSR 값이 마구 출렁임 | A0 선이 FSR-저항 사이 줄에 안 꽂힘 | A0 선 위치 확인 |
| pot이 0이나 1023에서 안 움직임 | 가운데 다리가 A1이 아님 | 가운데 다리 ↔ A1 확인. 바깥 다리 둘이 각각 +, − 인지 |
| 버튼이 항상 1 | 대각선이 아닌 다리를 써서 늘 연결됨 | 버튼을 90도 돌려 꽂거나 대각선 다리로 |
| 버튼이 항상 0 | 버튼에 3V3가 안 감, 또는 D2 선 위치 | 대각선 다리 A가 + 레일인지, D2가 버튼-저항 사이인지 |
| 버튼을 안 눌러도 0과 1이 왔다 갔다 | 10kΩ(풀다운)이 없거나 헐거움 | D2 줄 ↔ 10kΩ ↔ − 레일 확인 |
| Part C에서 x를 보내도 반응 없음 | 입력칸에 커서가 없었거나 Enter 안 누름, Part C 코드가 아님 | 입력칸 클릭 후 x + Enter, 업로드한 코드 확인 |
| Nano가 뜨거움 | 3V3와 GND가 바로 연결됨 (합선) | **즉시 USB 분리**, 레일 선 확인 |
