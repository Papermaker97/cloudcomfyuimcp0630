# 뽀모 브레드보드 프로토타입: 쥐기 → 횟수 + 날짜·시간 → 웹

지금 가진 부품(Nano 33 IoT + 플렉스 센서 + LED)으로 최종 목표의 2번(데이터 전송)과 3번(웹 기록)을 끝까지 실제로 돌려보는 버전입니다.
센서만 최종 설계(BMP581 압력 센서)와 다릅니다.

```
쥐기 → 플렉스 센서 → Nano 33 IoT가 1회 판정 → Wi-Fi 시간(NTP)으로 날짜·시간 찍기
     → Wi-Fi로 Supabase에 한 줄 저장 → dashboard.html에 5초 안에 표시 (폰에서도 열림)
```

## 1. 웹 쪽 준비 (한 번만, 10분)
1. https://supabase.com 에서 무료 계정을 만들고 New project를 만든다. 지역은 East US.
2. 왼쪽 **SQL Editor**에 `../../ppomo-device/web/schema.sql` 내용을 붙여넣고 Run.
3. **Project Settings → API**에서 두 가지를 복사한다.
   - Project URL (`https://abcd.supabase.co`)
   - `anon` public key

## 2. 펌웨어
1. Arduino IDE 라이브러리 매니저에서 **WiFiNINA**를 설치한다.
2. `arduino_secrets.h`를 채운다.
   - Wi-Fi 이름·비번: **폰 핫스팟 추천**. NYU Wi-Fi는 기기 등록이 필요해요.
   - `SUPABASE_HOST`: `abcd.supabase.co` (https:// 빼고)
   - `SUPABASE_KEY`: anon key
3. 보드를 **Arduino NANO 33 IoT**로 고르고 업로드한다.
4. 시리얼 모니터(115200)에서 확인한다.
   - `{"type":"wifi","status":"connected","time":"2026-..."}`가 나오면 Wi-Fi와 시간 연결 OK.
   - 쥐면 `{"type":"squeeze",...}` → `{"type":"upload","seq":1,"http":201}`. **201이면 웹에 저장된 것**.

배선은 `nano33-flex-test`와 같습니다 (A0 배, A1 엉덩이, D2 LED).

## 3. 기록 보기
- `../../ppomo-device/web/dashboard.html`을 연다. 컴퓨터든 폰이든 상관없음.
- 아래 Connect에 Project URL과 anon key를 넣고 Load.
- 쥘 때마다 오늘 횟수, 날짜별·시간대별 그래프, 최근 기록(날짜·시간)이 5초 안에 올라옵니다.
- 센서 튜닝용 그래프는 `../../ppomo-test-bench/index.html`도 그대로 동작합니다 (USB 연결 시).

## 알아둘 점
- **Wi-Fi가 끊겨도 기록은 안 사라집니다.** 최대 200개를 보드에 들고 있다가 다시 연결되면 순서대로 보냅니다.
- 전원이 꺼지면 보내지 못한 기록은 사라져요. 보드 RAM에만 있기 때문입니다.
- 재부팅해도 번호가 이어집니다. 켜질 때 서버의 마지막 번호를 읽어옵니다.
- 업로드 한 번에 1~2초 걸리고, 그동안은 센서를 안 봅니다. 그래서 그 사이에 아주 짧게 쥔 건 놓칠 수 있어요.
  - 업로드는 손을 뗀 상태에서만 합니다.
  - 최종 설계(ESP32-C3)는 센서를 따로 돌려서 이 문제가 없습니다.
- 테스트할 때는 Wi-Fi가 잡힌 뒤에 쥐어보세요. Wi-Fi가 없으면 30초마다 재접속을 시도하는데, 그동안 몇 초씩 멈춥니다.
