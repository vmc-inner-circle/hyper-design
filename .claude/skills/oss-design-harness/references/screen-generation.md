# 화면 생성 — HTML 규칙과 기기 규칙

화면 1장 = `design/screens/{id}.html` 1개. 같은 파일이 보드에서는 기기 칸마다 그 폭으로, `index.html`에서는 클릭되는 프로토타입으로 쓰인다. 기기 규격은 `schema/devices.json`이 유일한 출처다.

## 파일 머리

머리에 넣는 외부 자원(CDN)은 **`schema/stack.json`이 유일한 출처**다 — `status`가 `active`인 것만, `layers` 순서(유틸리티 CSS → 컴포넌트 → 글꼴 → 아이콘 → 토큰)대로 넣는다. `candidate`(시험 중)·`retired`(안 씀)는 넣지 않는다. 아래는 지금 active인 자원으로 쓴 머리다.

```html
<!doctype html>
<html lang="ko" data-devices="mobile desktop">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4.3.3"></script>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/basecoat-css@1.0.2/dist/basecoat.cdn.min.css">
  <script src="https://cdn.jsdelivr.net/npm/basecoat-css@1.0.2/dist/js/all.min.js" defer></script>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
  <script src="https://unpkg.com/lucide@1.48.0"></script>
  <script src="../theme.js"></script>
</head>
<body class="bg-background text-foreground font-sans">
```

- `data-devices`: 이 화면이 지원하는 기기를 공백으로. `board.json`에서 이 화면에 걸린 기기와 같아야 한다.
- `theme.js`: 모든 화면이 공유하는 토큰(§생성 순서 2) — Basecoat 변수 중 바꿀 값만 덮어쓰고, Tailwind 유틸리티 이름(`bg-primary` 등)에 연결한다. 아이콘(`lucide.createIcons()`)도 여기서 본문이 생긴 뒤에 만든다 — 화면에서 다시 부르지 않는다.

## 모바일 우선 반응형

기기 칸의 폭이 곧 뷰포트 폭이라, Tailwind 구간이 기기에 맞춰 자동으로 적용된다.

| 기기 | 폭 | 쓰는 클래스 |
|---|---|---|
| mobile | 390 | 접두사 없음 (기본) |
| tablet | 834 | `md:` |
| desktop | 1280 | `lg:` |

- 기본 클래스는 모바일용으로 쓴다. 태블릿·PC에서 달라질 것만 `md:` · `lg:`로 덮는다.
- 보드에 모바일만 걸려 있으면 `md:` · `lg:`를 쓰지 않는다 (덜 만든다).
- **기기별 구조 차이는 한 파일 안에서**: 예) 모바일 하단 탭바 `lg:hidden`, PC 사이드바 `hidden lg:flex`.
- **PC에서는 `position: fixed`를 쓰지 않는다.** PC 칸은 내용 길이만큼 늘어나서 고정 요소가 화면 중간에 뜬다. 탭바·FAB처럼 고정이 필요한 모바일 요소는 `fixed … lg:hidden`으로 모바일에만 둔다.

### 기기별 레이아웃 — 화면비에 맞게

같은 HTML이라도 기기마다 **구조**가 달라야 한다. 폭만 늘린 모바일 화면을 PC로 내지 않는다.

| | 모바일 (390×844, 세로) | 태블릿 (834×1194, 세로) | PC (1280, 가로·내용 길이) |
|---|---|---|---|
| 열 | 1열 | 1~2열 (목록이 길면 목록+상세) | 목록+상세 2열, 또는 본문+보조 패널 |
| 내비게이션 | 하단 탭 | 하단 탭 또는 옆 레일 | 왼쪽 사이드바 또는 상단 바 |
| 주 행동 버튼 | 하단 고정 (`fixed … lg:hidden`) | 하단 고정 또는 본문 안 | 본문 안, 관련 내용 바로 옆 |
| 추가 입력·선택 | 새 화면 또는 아래 시트 | 시트 또는 옆 패널 | 옆 패널 또는 대화 상자 (화면 이동 줄이기) |
| 콘텐츠 폭 | 화면 폭 | `max-w-content` 가운데 | 영역마다 `max-w-content`, 표·목록은 넓게 (`--content-max`) |
| 한 화면 정보량 | 한 가지 일 | 한두 가지 | 비교·한눈에 보기가 필요한 일 |

## 생성 순서 — 화면 목록 → 토큰 → 컴포넌트 → 화면

앞 단계가 끝나기 전에 다음 단계 파일을 쓰지 않는다. 각 단계는 앞 단계의 이름만 가져다 쓴다 — 화면 목록은 지침 G를, 토큰은 G를, 컴포넌트는 토큰과 Basecoat를, 화면은 공통 조각과 Basecoat를. 화면에서 무언가를 새로 정해야 하면 화면을 고치지 말고 그 단계로 돌아가 정의에 더한다.

### 1. 기기 → 화면 목록 (`brief.md` §기기, §화면 목록)

**기기부터 정한다.** 기본은 모바일 하나. 아래 신호가 PRD나 답에 있을 때만 기기를 더하고, 더한 이유를 지침 G로 남긴다.

| 신호 | 더할 기기 |
|---|---|
| 많이 입력·등록한다 (수십 건 이상, 긴 글, 표 형태 편집) | PC |
| 여러 항목을 한눈에 비교·조망한다 (전체 일정, 대시보드, 표) | PC (또는 태블릿) |
| 책상에서 일하는 사람이 업무로 쓴다 | PC |
| 이동 중·현장에서 확인·응답한다, 알림을 받고 바로 답한다 | 모바일 (기본) |
| 여럿이 한 화면을 같이 본다, 매장·현장 비치 | 태블릿 |

- 기기는 **화면마다** 정한다. 모든 화면을 모든 기기로 만들지 않는다 — 그 기기에서 실제로 하는 일의 화면만 (예: PC는 대량 입력·조망 화면만).
- 신호가 없으면 모바일만. PRD로 판단이 안 서고 기기에 따라 화면 수가 크게 달라지면 인터뷰에서 한 번 묻는다(`interview.md` §8 점검 3).

화면마다 한 줄: id · 역할 · 목적(한 줄) · 들어오는 곳 · **기기** · 상태 · 근거 G.

- **상태 화면은 필요한 곳만**: 비거나 실패할 수 있는 화면(목록·검색·입력·전송)에만 빈 상태·오류 상태를 둔다. 구조가 바뀌는 상태(빈 목록, 전송 실패)는 별도 화면 `{id}-empty`·`{id}-error`로 만들어 `board.json`의 같은 줄에 넣고, 작은 상태(비활성 버튼, 입력칸 오류 문구)는 Basecoat 상태(`disabled`, `aria-invalid`)로 화면 안에서. 빈 상태는 Basecoat `empty`.
- 덜어내거나 미룬 기능(PRD 판단 remove·defer)의 화면은 목록에 넣지 않는다.

### 2. 토큰 (`design/theme.js`)

`templates/theme.js`를 복사한다. **바탕은 Basecoat 기본값**(무채색, 절제된 테두리·여백 — `stack.json` basecoat)이고, 여기에는 **근거가 있어 바꾸는 값만** 적는다. 근거 없는 값은 적지 않는다 — 기본값이 AI가 지어낸 값보다 낫다.

- 바꾸는 값은 Basecoat(shadcn) 변수 이름으로: `--background`, `--primary`, `--muted-foreground`, `--border`, `--radius` … 주로 색(서비스 성격·대비)과 `--radius` 정도다. 템플릿에 없는 의미 색이 필요하면 의미 이름으로 더한다 (예: 역할이 둘이면 `role-a`·`role-b`가 아니라 그 역할의 이름으로).
- 값마다 주석으로 근거를 단다: `// G3` 또는 `// 가정: 이유`. 적지 않은 변수의 출처는 `seed:basecoat`다.
- 화면에서는 토큰 이름 유틸리티만 쓴다 (`bg-primary`, `text-muted-foreground`, `border-border`, `bg-card`). Tailwind 기본 팔레트(`bg-blue-500`, `text-gray-400`, `bg-white`)와 임의 값(`bg-[#3b82f6]`, `text-[13px]`, `h-[52px]`)은 쓰지 않는다. 글자 크기는 Tailwind 단계(`text-xs`~`text-3xl`), 모서리는 `rounded-sm`~`rounded-xl`(`--radius`에서 계산)만.
- **기기를 둘 이상 쓰면**: 색은 공통. PC 콘텐츠 최대 폭은 `--content-max`(→ `max-w-content`), 기기마다 달라지는 글자·여백은 Tailwind 단계에 `lg:`를 붙여 쓴다 (예: `text-xl lg:text-2xl`). 기기별 값을 임의 값으로 쓰지 않는다.
- **쓰지 않는 것 (토큰)** — AI 기본값처럼 보이게 만드는 것들:
  - 보라·인디고·청록 그라데이션, 그라데이션 글자, 채도 높은 번지는 빛(glow), 흐림 유리 효과
  - 요청 없는 다크 모드(`dark:`)
  - 모든 것에 같은 큰 radius — 카드와 버튼과 칩의 radius를 역할별로 나눈다
  - 12px 미만 본문, 1.4 미만 본문 행간, 본문 자간 벌림
  - 테두리 + 넓고 흐린 그림자를 함께. 그림자는 떠 있는 것(시트·하단 고정 바)에만
  - 회색 배경 위 회색 글자처럼 대비가 낮은 조합

### 3. 컴포넌트 (`design/components.md`)

`templates/components.md`를 복사해 채운다. **여러 화면에 반복되는 공통 컴포넌트만** 정의한다 — 한 화면에만 있는 것은 그 화면 HTML의 `data-id`로 충분하다. 같은 탭바·버튼·카드가 화면마다 달라지지 않게, 그리고 보드에서 사용자가 가리키는 단위가 미리 정해져 있게. 모양은 직접 짜지 않고 **Basecoat 컴포넌트·변형을 고른다** (§Basecoat 컴포넌트). Basecoat에 없는 조합(하단 탭바·헤더·하단 고정 바)만 Tailwind 유틸리티 + 토큰 이름으로 짠다.

- **강조 위계를 먼저 정한다** — `components.md` 맨 위 표(P1~P4): 화면마다 주 행동 하나, 강조할 핵심 하나, 보조로 낮출 것·숨길 것. Basecoat는 모양을 절제해 주지만 무엇을 강조할지는 정해 주지 않는다 — 정하지 않으면 모든 요소가 같은 무게로 나온다.

- **영역**: 화면을 이루는 큰 덩어리. 예) 헤더, 하단 탭바(푸터), 요약 칩 줄, 카드 목록, 입력 폼, 하단 고정 버튼
- **요소**: 영역 안에서 사용자가 누르거나 가리킬 것. 예) 탭바 안의 탭 버튼(아이콘+글자), 헤더의 알림 아이콘 버튼, 카드 안의 확정 버튼, 칩 하나
- 표에는 이름(`data-id`), 종류(영역/요소), **Basecoat 컴포넌트·변형**(`btn` + `data-variant="outline"`, `item`, `card`, `badge` … 없으면 유틸리티 + 토큰 이름), 들어가는 곳, 상태(선택됨·비활성·오류 등 실제로 쓰는 것만)를 적는다.
- **기기별로 구간을 나눈다**: `## 모바일 구간`(표 + 모바일 조각) → `## PC 구간`(PC를 쓰는 화면이 있을 때만: 모바일과 다른 점 표 + PC 조각). 한 표에 기기를 섞지 않는다.
- **PC 조각은 완성본**이다: 모바일 클래스와 `lg:` 클래스를 이미 합친 한 줄. PC를 쓰는 화면은 PC 조각을, 모바일만 쓰는 화면은 모바일 조각을 복사한다. 화면에서 `lg:`를 새로 붙이지 않는다 — 필요하면 PC 구간에 더하고 거기서 복사한다.
- 모바일 탭바와 PC 사이드바처럼 구조가 다른 것은 data-id를 따로 두고 `lg:hidden` / `hidden lg:flex`로 나눈다 (PC 구간 표에 "PC 전용"으로). PC 사이드바는 Basecoat `sidebar`(화면 밖으로 밀어 두는 방식이라 모바일 칸에서 작은 터치 요소로 걸림)가 아니라 `hidden lg:flex`로 짠다.
- 누르는 요소는 터치 기기(모바일·태블릿)에서 44×44px 이상 — **Basecoat 버튼·입력칸은 36px(`data-size="lg"`도 40px)**이라 모바일 조각에 `h-11`을 붙인다 (조각이 모든 화면에 복사되므로 여기서 틀리면 전부 틀린다).
- 여러 화면에 반복되는 것(탭바, 헤더, 기본 버튼, 카드)은 **HTML 조각을 한 번** 쓴다. 화면은 이 조각을 그대로 복사하고 글자·링크·현재 상태만 바꾼다 — class를 화면마다 새로 쓰지 않는다.
- **쓰지 않는 것 (컴포넌트)**:
  - 성격이 다른 내용을 전부 같은 카드로. 아이콘-제목-문단 카드를 3개 이상 똑같이 나열
  - 카드 안에 카드
  - 배지·수치·라벨마다 붙는 장식 아이콘, 제목 위 아이콘 타일, 이모지를 아이콘 대신
  - 제목 위의 작은 대문자·넓은 자간 라벨(eyebrow)
  - 여기저기 흩어진 칩·배지 — 화면 하나에 상태 칩은 한 종류로
  - 전부 굵은 글자 — 굵기는 제목·핵심 수치에만
  - PC 칸에 모바일 구조 그대로: 가운데 좁은 한 열, 하단 고정 버튼, 하단 탭바
  - 첫 화면 아래가 텅 빈 채 끝나는 화면 — 짧은 게 아니라 덜 만든 것처럼 보인다. 주 행동을 아래에 두거나(P1) 본문이 화면을 채우게 한다

### 4. 화면

공통 조각을 복사하고, 나머지는 Basecoat 컴포넌트로 조립한다. 아래 §data-id, §모바일 우선 반응형, §입력 방식을 따른다.

- **쓰지 않는 것 (문구)**: 근거 없는 수치("99.9%", "10배"), "경험을 한 단계 높여"류의 빈 약속, 문장마다 긴 줄표(—)나 "A · B · C" 나열.

## data-id — 2단계 (영역 → 요소)

- `components.md`의 영역과 요소에 `data-id`를 붙인다. **요소는 영역 안에** 넣는다 — 보드에서 영역을 끌면 안의 요소가 함께 움직이고, 한 번 더 들어가면 요소 하나만 옮기거나 지울 수 있다.
  ```html
  <nav data-id="tab-bar" data-nav>                 <!-- 영역 -->
    <a data-id="tab-home" href="home.html">…</a>   <!-- 요소 -->
    <a data-id="tab-calendar" href="calendar.html">…</a>
  </nav>
  ```
- 3단계 이상은 만들지 않는다. 더 깊은 `data-id`는 가리키기만 되고 따로 옮길 수 없다.
- 영역이 아닌 곳에 요소만 단독으로 둬도 된다 (예: 하단 고정 버튼 하나).
- 화면당 영역 3개 이상. 너무 큰 덩어리(화면 전체를 감싼 `data-id`)는 피한다.
- 이름은 영문 소문자·하이픈 (`summary-card`, `tab-home`). 한 화면 안에서 겹치지 않게. 요소 이름은 영역 이름을 앞에 붙이면 읽기 쉽다 (`tab-bar` → `tab-home`).
- **기기와 상관없이 같은 이름**. 모바일 카드와 PC 카드가 같은 요소로 이어진다.

## 입력 방식

- 터치 기기(mobile · tablet): 누르는 요소는 44×44px 이상. hover 효과는 `lg:hover:`에만.
- 상단·하단 안전 영역(`devices.json`의 `safeArea`)에 내용이 깔리지 않게 모바일 화면 위아래 여백을 둔다 (`pt-12`, 하단 고정 바는 `pb-8`).

## 그 밖

- 컴포넌트는 Basecoat(shadcn/ui를 CSS 클래스로) — §Basecoat 컴포넌트. 아이콘은 lucide `<i data-lucide="...">`.
- 화면 사이 이동은 실제 `<a href="other.html">`. **링크는 `data-id`가 붙은 요소 안에** 둔다 — 보드의 관계 화살표가 그 컴포넌트에서 출발한다. 링크로 이어진 페이지는 `board.json`에 없어도 보드에 자동으로 올라가지만, 흐름의 정식 화면이면 `board.json`에 넣는다.
- **뒤로·취소처럼 흐름을 거슬러 가는 링크**에는 `data-back`을 붙인다 (`<a data-id="back-btn" data-back href="…">`). 보드는 이 관계를 평소에 숨기고, 그 화면을 골랐을 때만 회색 점선으로 보여준다.
- **탭바·하단 메뉴 같은 전역 내비게이션**은 감싸는 요소에 `data-nav`를 붙인다 (`<nav data-id="tab-bar" data-nav>`). 모든 화면에서 반복되는 링크라 보드에 관계 화살표로 그리지 않는다.
- 글꼴은 **Pretendard 하나** (`stack.json`의 font 계층, `theme.js`의 `--font-sans`). 다른 웹 글꼴은 쓰지 않는다 — 보드는 컴포넌트를 이미지로 뜰 때 Pretendard만 넣어 주므로, 다른 글꼴은 보드와 실제 화면이 달라진다.
- 더미 데이터는 PRD 상황에 맞는 실제 같은 한국어. lorem ipsum 금지.
- 선언하지 않은 화면·상태를 "혹시 몰라서" 만들지 않는다.

## Basecoat 컴포넌트 (1.0.2)

모양은 클래스 하나 + `data-variant`·`data-size`로 고른다. 색·모서리는 theme.js 변수를 따른다. 전체 목록: https://basecoat.dev

| 쓰임 | 클래스 | 변형 |
|---|---|---|
| 버튼·링크 버튼 | `btn` (`<a class="btn">`도 됨) | `data-variant`: 없음(주) · `secondary` · `outline` · `ghost` · `destructive` · `link` / `data-size`: `sm` · `lg` · `icon` — 모바일은 `h-11` |
| 카드 | `card` (안에 `header`·`section`·`footer`, `card-title`·`card-description`) | — |
| 목록 행 | `item` (링크면 `<a class="item">`), 묶음 `item-group` | `data-variant`: `outline` · `muted` |
| 배지 | `badge` | `data-variant`: 없음 · `secondary` · `outline` · `destructive` — 상태마다 다른 변형 (강조 위계 P3) |
| 입력 | `field` 안에 `label` + `input`·`textarea`·`select`, 묶음 `fieldset` | 오류: `aria-invalid="true"` |
| 탭 | `tabs` (`role="tablist"`·`tab`·`tabpanel`, 동작은 머리의 all.min.js) | — |
| 표 | `table-container` > `table` | — |
| 빈 상태 | `empty` (`figure` 아이콘 + 제목 + 설명 + 버튼) | — |
| 그 밖 | `alert` · `dialog` · `progress` · `skeleton` · `avatar` · `kbd` · `toast` | — |

## 만든 뒤

`python .claude/skills/oss-design-harness/scripts/check.py --root design` — `[FAIL]`이 없을 때까지 고친다. 보드를 연 뒤에는 `feedback.json`의 `renderChecks`(가로 넘침, 작은 터치 요소 등)도 고친다.
