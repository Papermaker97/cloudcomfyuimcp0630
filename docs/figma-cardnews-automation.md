# Figma MCP로 카드뉴스 자동화하기

법률사무소 탁월 카드뉴스 제작을 Claude + Figma MCP(`use_figma`)로 자동화하는 가이드.

**전제**: 원고는 사람이 쓴다. AI는 그 원고를 템플릿에 기계적으로 주입한다.
원고 생성은 자동화 범위 밖이다.

---

## 목차

1. [왜 이 방식인가](#1-왜-이-방식인가)
2. [사전 준비](#2-사전-준비)
3. [대상 파일 정보](#3-대상-파일-정보)
4. [1단계 — 템플릿 정비 (최초 1회)](#4-1단계--템플릿-정비-최초-1회)
5. [2단계 — 원고 입력 포맷](#5-2단계--원고-입력-포맷)
6. [3단계 — 실행](#6-3단계--실행)
7. [4단계 — PNG 추출](#7-4단계--png-추출)
8. [내부 동작 스크립트](#8-내부-동작-스크립트)
9. [함정 모음](#9-함정-모음)
10. [트러블슈팅](#10-트러블슈팅)
11. [체크리스트](#11-체크리스트)

---

## 1. 왜 이 방식인가

### 다른 선택지가 안 되는 이유

| 방식 | 결론 |
|---|---|
| Figma REST API + n8n/Make | **불가능.** REST API는 노드를 수정하지 못한다. 읽기와 이미지 렌더링(`GET /v1/images`)만 된다 |
| Figma Buzz (CSV bulk create) | 가능하지만 템플릿을 Buzz용으로 재제작해야 하고, API가 없어 매번 수동 업로드. "1게시물 = N장 시퀀스" 구조와 안 맞음 |
| Google Sheets Sync 등 플러그인 | 가능하지만 반자동. 매번 Figma를 열고 플러그인을 실행해야 하며, 카드 장수가 매번 달라지는 상황에 약함 |
| Bannerbear / Placid / Orshot | 완전 무인 자동화 가능하나 디자인을 Figma 밖으로 이전해야 하고 월 구독 비용 발생 |
| HTML → PNG (Playwright) | 무료·무제한. 볼륨이 커지면 정답이지만 Figma와 이중 관리가 됨 |

### `use_figma`를 쓰는 이유

`use_figma`는 **Figma Plugin API 컨텍스트에서 임의의 JavaScript를 실행**한다.
REST API가 못 하는 쓰기 작업이 전부 된다 — 프레임 복제, 텍스트 치환,
이미지 삽입, 오토레이아웃 조정, 컴포넌트 인스턴스 생성.

이 프로젝트에 맞는 결정적 이유 3가지:

1. **템플릿 재제작이 필요 없다.** 지금 파일의 `커버 / 내용_짧은 / 내용_긴 / CTA`
   프레임을 그대로 쓴다
2. **카드 장수가 가변적이어도 된다.** 원고 블록 수만큼 복제한다. 플러그인 방식은
   프레임을 미리 그 개수만큼 만들어 놔야 한다
3. **결과가 편집 가능한 Figma 프레임으로 남는다.** "원고 컨펌 필요" 워크플로에 필수

---

## 2. 사전 준비

### MCP 연결

Claude Code / Claude Desktop에 Figma MCP 서버가 연결되어 있어야 한다.
연결 확인:

```
/mcp
```

`Figma` 서버가 목록에 있고 인증(OAuth)이 완료된 상태여야 한다.

### 플랜 / 시트 요구사항

쓰기(write-to-canvas)는 **유료 플랜의 Full 또는 Dev 시트**가 필요하다.
읽기 툴에는 rate limit이 걸린다:

| 시트 | Starter | Professional | Organization | Enterprise |
|---|---|---|---|---|
| View, Collab | 월 6회 | 월 6회 | 월 6회 | 월 6회 |
| Dev, Full | 월 6회 | **일 200회 / 분 10회** | 일 200회 / 분 15회 | 일 600회 / 분 20회 |

현재 계정(`johnk9938@gmail.com`)은 "Pro" 팀에 Full 시트 보유 → **일 200회 / 분 10회**.

> 쓰기 툴은 rate limit 면제 대상으로 문서화되어 있다. 병목은 읽기(`get_metadata`,
> `get_design_context`, `get_screenshot`) 쪽에서 생긴다. 검증용 스크린샷을
> 남발하지 말 것.

자기 계정 상태 확인:

```
whoami 툴 실행해줘
```

### 폰트

이 파일은 **Pretendard**를 쓴다. 스크립트에서 텍스트를 수정하려면 해당 폰트가
로드되어야 하고, 로컬 Figma에 폰트가 설치되어 있어야 한다.
(파일 내 "안내" 섹션에도 명시되어 있음)

---

## 3. 대상 파일 정보

```
URL      https://www.figma.com/design/gTWljHc8dmzIruAywRK9h2/-탁월--탬플릿
fileKey  gTWljHc8dmzIruAywRK9h2
page     0:1 (Page 1) — 단일 페이지
```

### 섹션 구성

| 섹션 ID | 이름 | 용도 |
|---|---|---|
| `1:180` | 안내 | 폰트·단축키 안내 |
| `1:186` | 크기 | 블로그 580×580 / 인스타 1080×1350 |
| `1:161` | 블로그 | 블로그용 템플릿 + 레퍼런스 |
| `1:147` | 인스타 | **카드뉴스 템플릿 + 실제 원고** |
| `1:176` | 인스타 레퍼런스 | 참고 스크린샷 |
| `1:168` | \*\*정리필요 | 배경본 제작 메모 |

### 인스타 템플릿 프레임 (1080×1350)

섹션 `1:147` 상단 줄이 원본 템플릿:

| 노드 ID | 템플릿 | 구성 |
|---|---|---|
| `1:65` | 커버 | 로고 / 날짜 / 헤드라인 / 태그 |
| `1:74` | 내용_짧은 | 아이브로우 / 타이틀 / 본문 / 로고 |
| `1:84` | 내용_긴 | (현재 비어 있음 — 정비 필요) |
| `1:148` | CTA | 로고 / 연락처 / 헤드라인 / 해시태그 |

하단 줄(`1:91`, `1:96`, `1:101`, `1:110`, `1:115`, `1:120`)은 백지원 변호사 합류
건 실제 원고. **템플릿이 아니라 산출물 예시**다.

### 블로그 템플릿 (580×580)

| 노드 ID | 템플릿 |
|---|---|
| `1:9` | 구성원 소개 (580×768) |
| `1:39` | 카드형_인물 |
| `1:154` | 카드형_배경 |

---

## 4. 1단계 — 템플릿 정비 (최초 1회)

**이 단계가 자동화의 전부다.** 여기를 건너뛰면 나머지가 전부 깨진다.

### 문제: 레이어 이름이 텍스트 내용 그 자체다

현재 상태:

```
text id="1:95" name="백지원 변호사 법률사무소 탁월에 합류"
text id="1:94" name="기업자문 및 민･형사 사건"
```

레이어 이름이 내용이라 **텍스트가 바뀌는 순간 매칭이 깨진다.** 스크립트가
"어느 레이어에 무엇을 넣어야 하는지" 알 방법이 없다.

### 해결: 레이어 이름을 계약서로 만든다

`#` 접두사 + 역할 이름으로 리네이밍한다. 이게 원고와 디자인을 잇는 유일한 규약이다.

**커버 (`1:65`)**

| 현재 레이어 | 변경 후 | 내용 |
|---|---|---|
| logo_가로_white 1 | `#logo` | (고정) |
| "9.30(화)까지" | `#date` | 날짜/기한 |
| "새로운 커머스의 시작..." | `#headline` | 메인 헤드라인 (2줄) |
| "커머스 전직군 대규모..." | `#tag` | 하단 태그 |

**내용_짧은 (`1:74`)**

| 현재 레이어 | 변경 후 | 내용 |
|---|---|---|
| "이런 문제를 풀고 있어요" | `#eyebrow` | 상단 소제목 |
| "ML Engineer" | `#title` | 타이틀 |
| "탐색형 사용자에게..." | `#body` | 본문 |
| logo_가로_white 1 | `#logo` | (고정) |

**내용_긴 (`1:84` / 참고: `1:101`)**

| 레이어 | 이름 | 내용 |
|---|---|---|
| 이미지 | `#image` | 상단 이미지 |
| 본문 | `#body` | 본문 |
| 출처 | `#caption` | 이미지 출처 |
| 로고 | `#logo` | (고정) |

**CTA (`1:148`)**

| 현재 레이어 | 변경 후 | 내용 |
|---|---|---|
| "대표님 지금 바로 문의하세요" | `#headline` | 헤드라인 |
| "전화: 010-..." | `#contact` | 연락처 (고정) |
| "#기업자문변호사 #..." | `#hashtag` | 해시태그 |
| logo_가로_white 1 | `#logo` | (고정) |

### 함께 처리할 것

1. **오토레이아웃 적용** — 현재 텍스트가 절대좌표(x/y)로 배치되어 있다.
   원고 길이가 달라지면 겹치거나 잘린다. 본문 블록은 `figma.createAutoLayout()`
   컨테이너로 감싼다
2. **`textAutoResize = 'HEIGHT'` + 고정 너비** — 줄바꿈 텍스트의 필수 설정.
   이걸 안 하면 텍스트가 한 줄로 뻗어나간다
3. **컴포넌트화 (선택)** — 템플릿 프레임을 컴포넌트로 만들면 디자인 수정이
   기존 카드 전체에 전파된다. 단, 인스턴스는 자식 노드 조작에 제약이 있어
   자동화가 조금 까다로워진다. **처음엔 그냥 프레임 복제 방식을 권장**
4. **템플릿 전용 섹션 분리** — 템플릿(`1:65`, `1:74`, `1:84`, `1:148`)을
   `_템플릿` 같은 별도 섹션으로 옮기면 산출물과 섞이지 않는다

### 정비 실행

Claude에게:

```
탁월 피그마 파일 (gTWljHc8dmzIruAywRK9h2) 인스타 템플릿 정비해줘.

- 1:65(커버), 1:74(내용_짧은), 1:148(CTA)의 텍스트 레이어를
  가이드 규칙대로 #headline, #body 등으로 리네이밍
- 본문 텍스트는 textAutoResize='HEIGHT' + 고정 너비로 설정
- 1:84(내용_긴)는 1:101을 참고해서 빈 상태 채워줘
```

---

## 5. 2단계 — 원고 입력 포맷

사람이 이 형식으로 쓴다. 마크다운, 노션, 구글 시트 무엇이든 상관없다.

```
=== 카드뉴스: 백지원 변호사 합류 ===

[커버]
date: 2026.08.10
headline: 백지원 변호사
          법률사무소 탁월에 합류
tag: 기업자문 및 민･형사 사건

[내용]
eyebrow: 실전 경험이 풍부한 변호사
title: 백지원 변호사
body: 고려대학교 정치외교학과 졸업
      영남대학교 법학전문대학원 졸업
      전) 법무법인 YK 경찰형사부 변호사
      전) 조선일보 더나은미래 기자

[내용]
eyebrow: 이런 사건을 맡습니다
title: 수행 사건 일부
body: 대기업 L사 협력업체 영업비밀 및 부정경쟁 사건
      글로벌 IT기업 국방부 사업비 횡령 사건
      L사 계열사 배임 사건

[내용]
eyebrow: 대표님 사업에만 집중하세요
title: 백지원 변호사의 한마디
body: 기업 사건을 하다 보면, 조금만 일찍 오셨으면
      훨씬 간단했을 사건을 자주 만납니다.

[CTA]
(고정 — 안 쓰면 기본값 사용)
```

### 규칙

- `[내용]` 블록을 몇 개 쓰든 그 수만큼 카드가 생긴다
- `body` 길이에 따라 `내용_짧은` / `내용_긴` 이 자동 선택된다
  (기준: 대략 200자 초과 시 긴 템플릿)
- `[CTA]`를 생략하면 기존 CTA 내용을 그대로 쓴다
- 이미지가 필요한 카드는 `image: <파일경로 또는 URL>` 을 추가한다
- 카드 순서 = 작성 순서. 커버는 항상 맨 앞, CTA는 항상 맨 뒤

### 인스타 권장 장수

커버 1 + 내용 4~8 + CTA 1 = **총 6~10장**

---

## 6. 3단계 — 실행

Claude에게 이렇게 요청한다:

```
탁월 피그마 (gTWljHc8dmzIruAywRK9h2) 인스타 카드뉴스 만들어줘.
템플릿은 섹션 1:147의 상단 줄 사용.
새 카드 세트는 기존 산출물 아래쪽 빈 공간에 가로로 배치.

원고:
[여기에 2단계 포맷대로 붙여넣기]
```

### Claude가 하는 일

1. 원고 파싱 → 카드 배열 생성
2. `get_metadata`로 템플릿 노드 구조 확인 (`#` 레이어 존재 여부 검증)
3. 배치할 빈 좌표 계산 (기존 노드와 겹치지 않게)
4. `use_figma` 호출 — 템플릿 복제 + 텍스트 주입 (카드 3~5장씩 나눠서)
5. `screenshot()`으로 오버플로우/잘림 검증
6. 문제 있으면 수정 스크립트 실행

### 왜 여러 번 호출하나

`use_figma`는 **한 호출당 논리 연산 10개 이하**가 권장된다. 카드 8장이면
2~3회로 쪼갠다. 한 번에 몰아넣으면 디버깅이 불가능해진다.

또한 `use_figma`는 **원자적(atomic)** 이다 — 스크립트가 에러 나면 아무것도
실행되지 않는다. 파일이 반쯤 망가진 상태로 남는 일은 없다.

---

## 7. 4단계 — PNG 추출

컨펌이 끝나면 이미지로 뽑는다. 두 가지 방법:

### 방법 A — `download_assets` (카드 단위)

```
1:91 부터 1:120 까지 카드들 1080x1350 PNG로 뽑아줘
```

노드 하나씩 처리한다. 장수가 적으면 이게 편하다.

### 방법 B — Figma REST API (일괄)

읽기 전용이라 REST가 잘 맞는 유일한 지점이다.

```bash
curl -H "X-Figma-Token: $FIGMA_TOKEN" \
  "https://api.figma.com/v1/images/gTWljHc8dmzIruAywRK9h2?ids=1:91,1:96,1:101&format=png&scale=1"
```

응답의 URL을 받아 다운로드한다. 인스타는 1080×1350이 원본 크기이므로
`scale=1`이면 충분하다.

> REST API는 노드 수가 많으면 burst 제한에 걸린다. 한 번에 20개 이하로 나눠 요청.

### 방법 C — 수동

Figma에서 프레임 선택 → Export → PNG 1x. 장수가 적으면 이게 제일 빠를 때도 있다.

---

## 8. 내부 동작 스크립트

Claude가 실행하는 `use_figma` 코드의 핵심 패턴. 직접 손볼 일이 생길 때 참고.

### 텍스트 주입 (canonical recipe)

**폰트 로드 없이 텍스트를 쓰면 무조건 실패한다.**
`Cannot write to node with unloaded font "Pretendard Bold"` 에러가 난다.

```js
// 노드의 '현재' 폰트를 읽어서 로드 — 하드코딩 금지
async function setText(node, value) {
  const fonts = node.getStyledTextSegments(['fontName']).map(s => s.fontName);
  if (fonts.length === 0 && node.fontName !== figma.mixed) {
    fonts.push(node.fontName);
  }
  for (const f of fonts) {
    await figma.loadFontAsync(f);
  }
  node.characters = value;
}
```

### 템플릿 복제 + 주입

```js
const TEMPLATES = { cover: '1:65', short: '1:74', long: '1:84', cta: '1:148' };

const section = await figma.getNodeByIdAsync('1:147');
const tpl = await figma.getNodeByIdAsync(TEMPLATES.short);

const card = tpl.clone();
section.appendChild(card);
card.x = 176 + (1080 + 96) * index;   // 가로 배치, 96px 간격
card.y = 3800;                         // 기존 산출물 아래
card.name = `내용_짧은 / ${data.title}`;

// query()로 # 레이어를 찾아 주입
for (const [key, value] of Object.entries(data)) {
  const target = card.query(`TEXT[name=#${key}]`).first();
  if (target) await setText(target, value);
}

return { createdNodeIds: [card.id] };
```

### 텍스트 오버플로우 자동 축소

```js
async function fitText(node, maxHeight) {
  const fonts = node.getStyledTextSegments(['fontName']).map(s => s.fontName);
  for (const f of fonts) await figma.loadFontAsync(f);

  node.textAutoResize = 'HEIGHT';   // 세로로만 늘어나게

  let size = node.fontSize === figma.mixed ? 32 : node.fontSize;
  while (node.height > maxHeight && size > 20) {
    size -= 2;
    node.setRangeFontSize(0, node.characters.length, size);
  }
  return { fontSize: size, height: node.height, fitted: node.height <= maxHeight };
}
```

### 검증

```js
// 같은 스크립트 안에서 바로 스크린샷 — 별도 get_screenshot 호출 불필요
await card.screenshot();
```

### 절대 하면 안 되는 것

| 금지 | 이유 |
|---|---|
| `figma.notify()` | `"not implemented"` 에러 발생 |
| `console.log()` | 출력이 Claude에게 전달되지 않음. `return`을 쓸 것 |
| `figma.currentPage = page` | 동작하지 않음. `await figma.setCurrentPageAsync(page)` |
| `figma.createImageAsync()` | 지원되지 않는 API |
| `loadAllPagesAsync()` | 지원되지 않는 API |
| 색상 0~255 | Plugin API는 **0~1 범위**. `{r:1, g:0, b:0}` = 빨강 |
| `fills` 배열 직접 수정 | 읽기 전용. 복제 → 수정 → 재할당 |
| async IIFE 래핑 | 자동으로 감싸진다. top-level `await` 그대로 사용 |

---

## 9. 함정 모음

### 폰트

- Pretendard가 로컬에 설치되어 있지 않으면 텍스트 수정이 실패한다
- 스타일 이름 표기가 까다롭다 (`"Semi Bold"` vs `"SemiBold"`). 확실하지 않으면
  `await figma.listAvailableFontsAsync()` 로 먼저 확인
- 폰트는 **노드의 현재 폰트**를 로드해야 한다. 기본값 하드코딩하면 깨진다

### 텍스트 레이아웃

- 줄바꿈 텍스트는 `textAutoResize = 'HEIGHT'` + **명시적 고정 너비**가 필수.
  `layoutSizingHorizontal = 'FILL'` 만 걸면 너비가 0에 가깝게 붕괴한다
- `layoutSizingHorizontal/Vertical`(자식용, `FIXED|HUG|FILL`)과
  `primaryAxisSizingMode/counterAxisSizingMode`(프레임용, `FIXED|AUTO`)는
  **다른 enum이다.** 섞으면 에러
- `FILL`/`HUG`는 `appendChild` **이후에** 설정해야 한다
- `resize()`는 sizing mode를 FIXED로 되돌린다. resize 먼저, sizing mode 나중

### 노드 배치

- 페이지에 직접 붙인 노드는 (0,0)에 생긴다. 기존 콘텐츠와 겹치지 않게
  좌표를 계산해서 지정할 것
- 이 파일은 좌표가 음수 영역까지 쓴다 (`x: -937` 등). 빈 공간 계산 시 주의

### 인스턴스

- 컴포넌트 인스턴스는 자식 노드 조작에 제약이 있다
- 자식에서 `detachInstance()`를 호출하면 부모 인스턴스가 암묵적으로 분리되면서
  **노드 ID가 전부 바뀐다.** `"The node with id X does not exist"` 에러의 주범
- 처음엔 프레임 복제 방식을 쓰고, 안정화된 뒤 컴포넌트를 검토할 것

### Rate limit

- 읽기 툴만 제한된다 (일 200 / 분 10). 쓰기는 면제
- `get_screenshot`을 매 카드마다 부르면 금방 소진된다.
  스크립트 안의 `await node.screenshot()`을 쓰면 별도 읽기 콜이 아니다
- Starter 팀 파일은 월 6회 제한이다. 파일이 어느 팀 소속인지 확인할 것

### 원자성

- `use_figma`는 원자적이다. 실패하면 아무 변경도 일어나지 않는다
- 에러가 나면 **즉시 재시도하지 말 것.** 에러 메시지를 읽고 고친 뒤 재실행

---

## 10. 트러블슈팅

| 증상 | 원인 | 해결 |
|---|---|---|
| `Cannot write to node with unloaded font "..."` | 폰트 미로드 | `getStyledTextSegments(['fontName'])`로 현재 폰트 읽어 `loadFontAsync` |
| `"not implemented"` | `figma.notify()` 사용 | 제거하고 `return` 사용 |
| `"Setting figma.currentPage is not supported"` | 동기 페이지 setter | `await figma.setCurrentPageAsync(page)` |
| `FILL can only be set on children of auto-layout frames` | 부모가 오토레이아웃이 아니거나 appendChild 전 | `createAutoLayout()` + appendChild 후 설정 |
| `Expected 'FIXED' \| 'AUTO', received 'FILL'` | sizing enum 혼동 | 프레임엔 `counterAxisSizingMode`, 자식엔 `layoutSizing*` |
| 텍스트가 한 줄로 뻗음 | `textAutoResize` 미설정 | `'HEIGHT'` + 고정 너비 |
| 텍스트가 프레임 밖으로 넘침 | 원고가 템플릿 상정보다 김 | `fitText()`로 자동 축소, 또는 `내용_긴` 템플릿 사용 |
| `Cannot read properties of null` | 노드 ID 오류 / 다른 페이지 | 페이지 컨텍스트 확인, ID 재확인 |
| `The node with id X does not exist` | 인스턴스 암묵적 분리로 ID 변경 | 안정적인 상위 프레임에서 재탐색 |
| 카드가 (0,0)에 겹쳐 생김 | 좌표 미지정 | `card.x/y` 명시적으로 설정 |
| MCP 툴이 rate limit 걸림 | 읽기 콜 과다 | 검증용 스크린샷 줄이기, 플랜/시트 확인 |
| 권한 에러 | 파일 소속 팀과 계정 불일치 | `whoami`로 계정·플랜 확인 |

---

## 11. 체크리스트

### 최초 1회

- [ ] Figma MCP 연결 및 OAuth 인증 완료 (`/mcp`)
- [ ] `whoami`로 Full/Dev 시트 + 유료 플랜 확인
- [ ] Pretendard 폰트 로컬 설치
- [ ] 템플릿 텍스트 레이어를 `#` 규칙대로 리네이밍
- [ ] 본문 텍스트에 `textAutoResize='HEIGHT'` + 고정 너비 설정
- [ ] `1:84` (내용_긴) 템플릿 내용 채우기
- [ ] 템플릿을 별도 섹션으로 분리 (선택)

### 매 제작 시

- [ ] 원고를 2단계 포맷대로 작성
- [ ] 커버 1 + 내용 4~8 + CTA 1 구성 확인
- [ ] Claude에게 fileKey + 원고 전달
- [ ] 생성된 카드 스크린샷으로 오버플로우/잘림 확인
- [ ] Figma에서 사람이 최종 컨펌 및 미세 조정
- [ ] PNG 1080×1350 추출
- [ ] 업로드

---

## 부록 — 볼륨이 커지면

하루 수십 건 이상으로 늘어나면 **HTML → PNG (Playwright)** 방식으로 이관을 검토한다.

- 1080×1350 HTML 템플릿을 만들고 데이터만 바꿔 스크린샷
- 무료, 무제한, git으로 버전 관리, CI에서 자동 실행 가능
- Figma는 디자인 원본으로 남기고, MCP(`get_design_context`)로 디자인 토큰을
  뽑아 HTML에 반영하는 하이브리드 구조

전환 시점의 신호: MCP rate limit에 상시로 걸리거나, 사람 컨펌 단계가
불필요해졌을 때.

---

## 참고 자료

- [Get started with the Figma MCP server](https://help.figma.com/hc/en-us/articles/39216419318551-Get-started-with-the-Figma-MCP-server)
- [Figma Plugin API Reference](https://developers.figma.com/docs/plugins/api/api-reference/)
- [Compare Figma APIs (REST vs Plugin)](https://developers.figma.com/compare-apis)
- [Figma MCP vs Figma API for AI Agents](https://www.scalekit.com/blog/figma-mcp-vs-api)
- [Bulk create assets in Figma Buzz](https://help.figma.com/hc/en-us/articles/31271824185623-Bulk-create-assets-in-Figma-Buzz)
