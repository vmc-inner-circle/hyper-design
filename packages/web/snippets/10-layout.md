# 10-layout — 앱 프레임 · 상단바 · 사이드바 · 콘텐츠 · 페이지 골격 · 그리드 · 유틸

규칙: 루트는 `<div class="app">` 하나. `.content`만 스크롤한다. 클래스는 아래 것만 쓴다.
아이콘은 `allowlist.json` 값만 (`<svg class="icon" aria-hidden="true"><use href="#i-<name>"/></svg>`).

## app (프레임)
언제: 모든 화면의 루트. 상단바 + 좌 사이드바 + 우 콘텐츠.

```html
<div class="app">
  <header class="topnav">…</header>
  <aside class="sidebar">…</aside>
  <main class="content">…</main>
</div>
```

변형 — 사이드바 없음 (온보딩·로그인·전체폭 보드):

```html
<div class="app no-sidebar">
  <header class="topnav">…</header>
  <main class="content">…</main>
</div>
```

주의: `.app` 밖에 아무것도 두지 않는다. 높이·폭은 토큰이 정한다(1280×800).

## topnav (상단바)
언제: 브랜드 + 현재 위치 + 전역 액션(검색·알림·프로필).

```html
<header class="topnav">
  <div class="topnav-brand">
    <svg class="icon" aria-hidden="true"><use href="#i-layout-dashboard"/></svg>
    <span>팀 워크스페이스</span>
  </div>
  <div class="topnav-title">9월 워크숍 준비</div>
  <div class="topnav-actions">
    <button class="btn btn-ghost btn-icon" aria-label="알림"><svg class="icon" aria-hidden="true"><use href="#i-bell"/></svg></button>
    <button class="btn btn-ghost btn-icon" aria-label="설정"><svg class="icon" aria-hidden="true"><use href="#i-settings"/></svg></button>
    <button class="btn btn-primary btn-sm"><svg class="icon" aria-hidden="true"><use href="#i-plus"/></svg>새 일정</button>
  </div>
</header>
```

변형 — 검색 포함 (`.search`는 30-inputs.md):

```html
<header class="topnav">
  <div class="topnav-brand"><svg class="icon" aria-hidden="true"><use href="#i-layout-dashboard"/></svg><span>팀 워크스페이스</span></div>
  <div class="search">
    <svg class="icon" aria-hidden="true"><use href="#i-search"/></svg>
    <input class="input" type="search" placeholder="일정·담당자 검색">
  </div>
  <div class="topnav-actions">
    <button class="btn btn-ghost btn-icon" aria-label="알림"><svg class="icon" aria-hidden="true"><use href="#i-bell"/></svg></button>
    <div class="avatar avatar-sm">김</div>
  </div>
</header>
```

주의: 상단바의 primary 버튼은 화면 전체에서 primary가 1개일 때만.

## sidebar (사이드바 내비)
언제: 화면 간 이동. 현재 화면에 `.nav-item.active`.

```html
<aside class="sidebar">
  <nav class="nav">
    <div class="nav-section">업무</div>
    <a class="nav-item active" href="#"><svg class="icon" aria-hidden="true"><use href="#i-house"/></svg><span>홈</span></a>
    <a class="nav-item" href="#"><svg class="icon" aria-hidden="true"><use href="#i-calendar"/></svg><span>일정</span><span class="badge badge-neutral">12</span></a>
    <a class="nav-item" href="#"><svg class="icon" aria-hidden="true"><use href="#i-list-checks"/></svg><span>할 일</span></a>
    <a class="nav-item" href="#"><svg class="icon" aria-hidden="true"><use href="#i-users"/></svg><span>참석자</span></a>
    <div class="nav-section">관리</div>
    <a class="nav-item" href="#"><svg class="icon" aria-hidden="true"><use href="#i-chart-bar"/></svg><span>리포트</span></a>
    <a class="nav-item" href="#"><svg class="icon" aria-hidden="true"><use href="#i-settings"/></svg><span>설정</span></a>
  </nav>
  <div class="sidebar-footer">
    <a class="nav-item" href="#"><svg class="icon" aria-hidden="true"><use href="#i-circle-question-mark"/></svg><span>도움말</span></a>
    <a class="nav-item" href="#"><div class="avatar avatar-sm">김</div><span class="truncate">김하은 · 운영팀</span></a>
  </div>
</aside>
```

주의: `.nav-item` 안의 텍스트는 반드시 `<span>`으로 감싼다(말줄임). 항목은 3~7개.

## content (스크롤 영역)
언제: 페이지 본문 전체. 항상 `.page-header`로 시작.

```html
<main class="content">
  <div class="page-header">
    <div>
      <h1 class="page-title">9월 워크숍 일정</h1>
      <p class="page-desc">9월 12일(금) · 참석 24명 · 장소 확정 대기</p>
    </div>
    <div class="page-actions">
      <button class="btn"><svg class="icon" aria-hidden="true"><use href="#i-share-2"/></svg>공유</button>
      <button class="btn btn-primary"><svg class="icon" aria-hidden="true"><use href="#i-plus"/></svg>세션 추가</button>
    </div>
  </div>
  <!-- 본문 -->
</main>
```

변형 — 폭 제한(폼·설정·읽기 화면): 본문을 `.content-inner`로 감싼다.

```html
<main class="content">
  <div class="content-inner">
    <div class="page-header"><div><h1 class="page-title">계정 설정</h1></div></div>
    …
  </div>
</main>
```

주의: `.content` 안에 또 다른 스크롤 영역을 만들지 않는다(`.split` 예외).

## page-header
언제: 페이지 제목 · 한 줄 설명 · 우측 액션. 화면당 1개, `.content` 첫 자식.

```html
<div class="page-header">
  <div>
    <h1 class="page-title">참석자 관리</h1>
    <p class="page-desc">응답 18 / 미응답 6 · 마감 9월 5일</p>
  </div>
  <div class="page-actions">
    <button class="btn"><svg class="icon" aria-hidden="true"><use href="#i-download"/></svg>내보내기</button>
    <button class="btn btn-primary"><svg class="icon" aria-hidden="true"><use href="#i-user-plus"/></svg>참석자 초대</button>
  </div>
</div>
```

변형 — 뒤로가기 + 상태 배지 (상세 화면):

```html
<div class="page-header">
  <div>
    <div class="row gap-2 mb-2">
      <button class="btn btn-ghost btn-sm btn-icon" aria-label="목록으로"><svg class="icon" aria-hidden="true"><use href="#i-arrow-left"/></svg></button>
      <span class="badge badge-success">확정</span>
    </div>
    <h1 class="page-title">오프닝 세션 · 팀 소개</h1>
    <p class="page-desc">09:30–10:20 · 대회의실 A · 발표 박지훈</p>
  </div>
  <div class="page-actions">
    <button class="btn btn-ghost btn-icon" aria-label="더보기"><svg class="icon" aria-hidden="true"><use href="#i-ellipsis"/></svg></button>
    <button class="btn"><svg class="icon" aria-hidden="true"><use href="#i-pencil"/></svg>수정</button>
  </div>
</div>
```

주의: `.page-title`은 `<h1>` 하나. 설명이 없으면 `.page-desc`를 아예 뺀다.

## toolbar
언제: 목록 위 필터·검색·보기 전환 줄. 좌측 검색/필터, 우측 정렬/보기.

```html
<div class="toolbar">
  <div class="search">
    <svg class="icon" aria-hidden="true"><use href="#i-search"/></svg>
    <input class="input" type="search" placeholder="세션 이름·발표자 검색">
  </div>
  <button class="btn"><svg class="icon" aria-hidden="true"><use href="#i-funnel"/></svg>필터</button>
  <div class="segmented">
    <button class="segmented-item active">전체</button>
    <button class="segmented-item">확정</button>
    <button class="segmented-item">후보</button>
  </div>
  <div class="spacer"></div>
  <button class="btn btn-ghost"><svg class="icon" aria-hidden="true"><use href="#i-arrow-up-down"/></svg>시작 시각순</button>
  <div class="btn-group">
    <button class="btn btn-icon active" aria-label="목록 보기"><svg class="icon" aria-hidden="true"><use href="#i-list"/></svg></button>
    <button class="btn btn-icon" aria-label="카드 보기"><svg class="icon" aria-hidden="true"><use href="#i-layout-grid"/></svg></button>
  </div>
</div>
```

주의: 툴바에는 primary 버튼을 두지 않는다(페이지 헤더가 담당).

## section
언제: 본문을 제목 있는 덩어리로 나눌 때. 대시보드·상세·설정.

```html
<section class="section" data-region="example-summary">
  <h2 class="section-title">
    <svg class="icon" aria-hidden="true"><use href="#i-calendar-days"/></svg>
    이번 주 일정
    <button class="link link-muted">전체 보기</button>
  </h2>
  <p class="section-desc">9월 8일(월) – 9월 12일(금)</p>
  <!-- 카드·목록 등 -->
</section>
```

주의: `.section-title`은 `<h2>`. 섹션 사이 간격은 클래스가 준다(`mt-*` 추가 금지).

## grid-2 / grid-3 / grid-4
언제: 카드·통계 타일을 같은 폭 열로 나란히.

```html
<div class="grid-4">
  <div class="stat">…</div><div class="stat">…</div><div class="stat">…</div><div class="stat">…</div>
</div>

<div class="grid-3">
  <div class="card">…</div><div class="card">…</div><div class="card">…</div>
</div>

<div class="grid-2">
  <div class="card">…</div>
  <div class="card">…</div>
</div>
```

변형 — 한 항목을 넓게: `.span-2`(2열 차지) · `.span-full`(전체 폭).

```html
<div class="grid-3">
  <div class="card span-2"><div class="card-body">주간 일정표 …</div></div>
  <div class="card"><div class="card-body">담당자 현황 …</div></div>
</div>
```

주의: 1280 프레임에서 4열까지만. 그리드 안에서는 `.card`/`.stat` 같은 블록만 둔다. 카드 안 내용은 `.card-body`로 감싼다(40-display.md).

## split (좌 목록 / 우 상세)
언제: 목록에서 하나를 골라 오른쪽에서 보는 화면(list-detail 패턴). `.content` 직계 자식으로 두면 남은 높이를 채운다.

```html
<div class="split">
  <div class="split-list" data-region="example-list">
    <div class="toolbar">
      <div class="search w-full">
        <svg class="icon" aria-hidden="true"><use href="#i-search"/></svg>
        <input class="input" type="search" placeholder="세션 검색">
      </div>
    </div>
    <ul class="list">
      <!-- .list-item 은 50-data.md -->
    </ul>
  </div>
  <div class="split-detail" data-region="example-detail">
    <div class="page-header">
      <div><h1 class="page-title">오프닝 세션 · 팀 소개</h1><p class="page-desc">09:30–10:20 · 대회의실 A</p></div>
      <div class="page-actions"><button class="btn"><svg class="icon" aria-hidden="true"><use href="#i-pencil"/></svg>수정</button></div>
    </div>
    <!-- 상세 본문 -->
  </div>
</div>
```

주의: `.split`을 쓸 때 `.content`에는 `.page-header`를 생략하거나 짧게(그래야 목록이 접히지 않는다). 목록 폭 360 고정.

## stack / row / row-between / spacer
언제: 세로 나열은 `.stack`, 가로 정렬은 `.row`, 양끝 정렬은 `.row-between`. 간격은 `.gap-*`.

```html
<div class="stack gap-2">
  <div class="row-between">
    <span class="fw-semibold">장소</span>
    <span class="text-2">대회의실 A</span>
  </div>
  <div class="row-between">
    <span class="fw-semibold">참석</span>
    <span class="text-2">24명</span>
  </div>
</div>

<div class="row gap-2">
  <div class="avatar avatar-sm">박</div>
  <span class="truncate">박지훈 · 기획팀</span>
  <div class="spacer"></div>
  <span class="badge badge-neutral">발표</span>
</div>

<div class="row wrap gap-2">
  <span class="chip">기획</span><span class="chip">디자인</span><span class="chip">개발</span>
</div>
```

주의: `.row`는 줄바꿈하지 않는다. 항목이 많으면 `.row.wrap`.

## 유틸 (조합만, 새 스타일 금지)

| 종류 | 클래스 |
|---|---|
| 간격 | `.gap-1 .gap-2 .gap-3 .gap-4 .gap-6` · `.mt-2 .mt-4 .mt-6` · `.mb-2 .mb-4 .mb-6` |
| 글자색 | `.text-muted .text-2 .text-primary .text-success .text-warning .text-danger` |
| 글자 크기 | `.text-xs .text-sm .text-lg .text-xl` · 굵기 `.fw-medium .fw-semibold .fw-bold` · `.mono` |
| 정렬 | `.text-center .text-right` · `.row.align-start` |
| 폭 | `.w-full .flex-1 .shrink-0 .truncate` |

```html
<p class="text-sm text-muted">마지막 수정 9월 3일 14:20 · 김하은</p>
<span class="text-lg fw-bold mono">₩1,240,000</span>
```

주의: 유틸은 텍스트·간격 미세조정용. 레이아웃 구조는 위 골격 클래스로.
