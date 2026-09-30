<!--
design/components.md — 공통 컴포넌트 (가족여행 계획). references/screen-generation.md §생성 순서 3.
여러 화면에 반복되는 것만. 화면은 조각을 그대로 복사하고 글자·링크·현재 상태만 바꾼다.
-->

# Components (공통)

## 강조 위계 — 화면마다 무엇을 보이고, 하나만 강조하고, 무엇을 숨기나

| ID | 규칙 | 적용 | 근거 |
|---|---|---|---|
| P1 | 화면마다 주 행동은 하나 — `btn`(주 변형), 모바일은 엄지가 닿는 아래쪽. 나머지 행동은 `outline`·`ghost`. 확인하는 사람 화면은 주 행동 버튼이 없을 수 있다 (읽는 화면) — 그때는 P2가 화면의 중심 | all | 관찰: 라이브러리 비교 (2026-09-30) · G6 |
| P2 | 화면의 핵심 하나만 크게: 확인하는 사람 첫 화면은 "다음에 모일 때·곳", 그날 상세는 항목마다 시각·장소, 짜는 사람 일정은 확정/후보 | all | G2 G6 G7 |
| P3 | 상태 배지는 상태마다 다른 `data-variant` — 확정 = `badge` 기본, 후보 = `badge` `outline`. 배지는 짜는 사람 화면에만 (확인하는 사람 화면엔 확정만 있으므로 배지 없음) | plan, item-edit | G1 G2 |
| P4 | 보조 정보는 `text-muted-foreground`. 확인하는 사람 화면에는 수정 시각·작성자·후보 수 같은 짜는 쪽 정보를 숨긴다 | all | G1 G8 |

## 모바일 구간 (기본)

### 짜는 사람

| data-id | 종류 | Basecoat 컴포넌트·변형 (없으면 유틸리티 + 토큰) | 들어가는 곳 | 상태 |
|---|---|---|---|---|
| plan-tab-bar | 영역 | (Basecoat 없음) `fixed bottom-0 inset-x-0 grid grid-cols-3 bg-card border-t border-border pb-8 lg:hidden`, `data-nav` | plan, packing, members | — |
| tab-plan · tab-packing · tab-members | 요소 | `btn` `ghost` + `h-14 flex-col gap-1 text-xs rounded-none` | plan-tab-bar 안 | 선택됨: `text-foreground font-semibold` + `aria-current="page"`, 나머지 `text-muted-foreground` |
| app-header | 영역 | (Basecoat 없음) `sticky top-0 z-10 bg-background border-b border-border px-4 pt-12 pb-3 flex items-center gap-2` | plan, packing, members | — |
| plan-item | 요소 | `item` `outline` (링크 `<a class="item">`), 후보는 `border-dashed` 추가. 왼쪽 손잡이 `grip-vertical` 아이콘, 오른쪽 배지 | plan | 확정 / 후보 |
| status-badge | 요소 | `badge` 확정 = 기본 / 후보 = `data-variant="outline"` | plan-item 안, item-edit | — |
| add-btn | 요소 | `btn` + `h-11 text-base lg:h-10`, app-header 오른쪽. 떠 있는 버튼으로 두지 않는다 (G13), 글자 한 단계 크게 (G17) | plan | — |
| header-add | 요소 | `btn` `outline` + `h-11 shrink-0`, app-header 오른쪽. 목록 위에 입력 줄을 두지 않는다 (G15) | packing | — |
| bottom-bar | 영역 | (Basecoat 없음) `fixed bottom-0 inset-x-0 bg-card border-t border-border px-4 pt-3 pb-8 shadow-lg lg:hidden` | item-edit | — |
| primary-btn | 요소 | `btn` + `h-11 w-full` | bottom-bar 안 / 목록 끝 | 비활성: `disabled` |

### 확인하는 사람 (글자 한 단계 크게 — G8)

| data-id | 종류 | Basecoat 컴포넌트·변형 | 들어가는 곳 | 상태 |
|---|---|---|---|---|
| view-header | 영역 | (Basecoat 없음) `sticky top-0 z-10 bg-background border-b border-border px-4 pt-12 pb-3 flex items-center gap-2` | view-day, view-news, view-packing | — |
| back-btn | 요소 | `btn` `ghost` `size=icon` + `size-12`, `data-back` | view-header 안 | — |
| view-row | 요소 | `item` `outline` + `min-h-14 text-lg` (링크면 `<a class="item">`). view-home은 `min-h-16 text-xl`, 제목 `text-xl`·설명 `text-lg` (G14) | view-home, view-news | — |

### 모바일 조각

```html
<!-- plan-tab-bar (현재 탭만 aria-current·굵게) -->
<nav data-id="plan-tab-bar" data-nav class="fixed bottom-0 inset-x-0 z-10 grid grid-cols-3 bg-card border-t border-border pb-8 lg:hidden">
  <a data-id="tab-plan" href="plan.html" aria-current="page" class="btn h-14 flex-col gap-1 text-xs text-foreground font-semibold rounded-none" data-variant="ghost"><i data-lucide="calendar-days"></i><span>일정</span></a>
  <a data-id="tab-packing" href="packing.html" class="btn h-14 flex-col gap-1 text-xs text-muted-foreground rounded-none" data-variant="ghost"><i data-lucide="list"></i><span>준비물</span></a>
  <a data-id="tab-members" href="members.html" class="btn h-14 flex-col gap-1 text-xs text-muted-foreground rounded-none" data-variant="ghost"><i data-lucide="users"></i><span>가족</span></a>
</nav>
```

```html
<!-- app-header -->
<header data-id="app-header" class="sticky top-0 z-10 bg-background border-b border-border px-4 pt-12 pb-3 flex items-center gap-2">
  <div class="flex-1 min-w-0">
    <h1 class="text-lg font-semibold">제주 가족여행</h1>
    <p class="text-sm text-muted-foreground">11월 12일(목)~15일(일) · 출발까지 43일</p>
  </div>
</header>
```

```html
<!-- plan-item: 확정 / 후보 -->
<a data-id="item-1" href="item-edit.html" class="item" data-variant="outline">
  <i data-lucide="grip-vertical" class="text-muted-foreground"></i>
  <div class="flex-1 min-w-0"><p class="font-medium">09:10 김포 → 제주 항공</p><p class="text-sm text-muted-foreground">김포공항 3층 08:00 모임</p></div>
  <span class="badge">확정</span>
</a>
<a data-id="item-2" href="item-edit.html" class="item border-dashed" data-variant="outline">
  <i data-lucide="grip-vertical" class="text-muted-foreground"></i>
  <div class="flex-1 min-w-0"><p class="font-medium">12:30 점심 — 고기국수</p><p class="text-sm text-muted-foreground">후보 2곳</p></div>
  <span class="badge" data-variant="outline">후보</span>
</a>
```

```html
<!-- bottom-bar + primary-btn -->
<div data-id="bottom-bar" class="fixed bottom-0 inset-x-0 bg-card border-t border-border px-4 pt-3 pb-8 shadow-lg lg:hidden">
  <a data-id="save-btn" href="plan.html" class="btn h-11 w-full">저장</a>
</div>
```

```html
<!-- view-header -->
<header data-id="view-header" class="sticky top-0 z-10 bg-background border-b border-border px-4 pt-12 pb-3 flex items-center gap-2">
  <a data-id="back-btn" data-back href="view-home.html" class="btn size-12" data-variant="ghost" data-size="icon" aria-label="뒤로"><i data-lucide="chevron-left"></i></a>
  <h1 class="text-xl font-semibold">제목</h1>
</header>
```

```html
<!-- view-row -->
<a data-id="day-1" href="view-day.html" class="item min-h-14 text-lg" data-variant="outline">
  <div class="flex-1 min-w-0"><p class="text-lg font-semibold">첫째 날 · 11월 12일(목)</p><p class="text-base text-muted-foreground">김포 → 제주, 서귀포 숙소</p></div>
  <i data-lucide="chevron-right" class="text-muted-foreground"></i>
</a>
```

## PC 구간

PC를 쓰는 화면: plan, item-edit (G9)

| data-id | 모바일과 무엇이 다른가 | PC 모양 |
|---|---|---|
| side-nav | PC 전용 (모바일 plan-tab-bar 대신) | `hidden lg:flex w-56 shrink-0 flex-col gap-1 border-r border-border bg-card p-4 min-h-screen`, `data-nav` |
| plan-tab-bar | PC에서 숨김 | 모바일 조각 그대로 (`lg:hidden` 포함) |
| app-header | 위 여백·붙박이 없앰 | 모바일 조각 + `lg:static lg:pt-6 lg:px-8` |
| bottom-bar | 하단 고정 → 본문 안 폼 끝 (모바일용은 `lg:hidden`, PC용은 따로) | `hidden lg:flex justify-end gap-2 pt-6` 안에 `btn` (폭 자동) |

### PC 조각

```html
<!-- side-nav (plan, item-edit) -->
<aside data-id="side-nav" data-nav class="hidden lg:flex w-56 shrink-0 flex-col gap-1 border-r border-border bg-card p-4 min-h-screen">
  <p class="px-3 pb-3 font-semibold">제주 가족여행</p>
  <a data-id="nav-plan" href="plan.html" aria-current="page" class="btn justify-start font-semibold" data-variant="secondary"><i data-lucide="calendar-days"></i>일정</a>
  <a data-id="nav-packing" href="packing.html" class="btn justify-start text-muted-foreground" data-variant="ghost"><i data-lucide="list"></i>준비물</a>
  <a data-id="nav-members" href="members.html" class="btn justify-start text-muted-foreground" data-variant="ghost"><i data-lucide="users"></i>가족</a>
</aside>
```

```html
<!-- app-header (PC를 쓰는 화면용) -->
<header data-id="app-header" class="sticky top-0 z-10 bg-background border-b border-border px-4 pt-12 pb-3 flex items-center gap-2 lg:static lg:pt-6 lg:px-8">…</header>
```

```html
<!-- PC 저장 줄 (item-edit) -->
<div data-id="pc-actions" class="hidden lg:flex justify-end gap-2 pt-6">
  <a data-back href="plan.html" class="btn" data-variant="outline">취소</a>
  <a href="plan.html" class="btn">저장</a>
</div>
```
