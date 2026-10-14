# 10-layout (모바일) — 셸 · 화면 첫머리 · 판 쌓기 · 아래 꽉 찬 버튼 · 아래 창

셸(아래 탭 · 위 제목 줄 · 위 알약 탭)은 **expand.js가 붙인다** — 작성자는 쓰지 않는다. 모양을 알아 두라고 적는다.
프레임 390×844. `.content`만 스크롤한다. 클래스는 web 조각 + 아래 것만.

## 셸 1 — 탭 화면 (roles[].nav에 있는 화면 · 시안 shell: tabbar, 기본)

```html
<div class="app app-mobile">
  <main class="content">…</main>
  <nav class="tabbar">
    <a class="nav-item active" href="#"><svg class="icon" aria-hidden="true"><use href="#i-house"/></svg><span>홈</span></a>
    <a class="nav-item" href="#"><svg class="icon" aria-hidden="true"><use href="#i-search"/></svg><span>찾기</span></a>
    <a class="nav-item" href="#"><svg class="icon" aria-hidden="true"><use href="#i-calendar-check"/></svg><span>내 예약</span></a>
    <a class="nav-item" href="#"><svg class="icon" aria-hidden="true"><use href="#i-user"/></svg><span>마이</span></a>
  </nav>
</div>
```
아래 탭은 3~5개. 지금 탭 = 본문 색, 나머지 = 흐린 회색. 탭 항목 클래스는 `.nav-item`(최종본이 이 글자로 화면을 잇는다).

## 셸 2 — 아래 화면 (메뉴에 없는 화면: 자세히 · 입력 · 확인)

```html
<div class="app app-mobile">
  <header class="appbar"><button class="btn btn-ghost btn-icon" aria-label="뒤로" data-back><svg class="icon" aria-hidden="true"><use href="#i-chevron-left"/></svg></button><div class="appbar-title">수업 상세</div><div class="appbar-actions"></div></header>
  <main class="content">…</main>
</div>
```
가운데 제목 = `screens.json`의 화면 이름(끝의 괄호 설명은 뺀다). 아래 탭은 없다.

## 셸 3 — 위 알약 탭 (시안 shell: top)

```html
<div class="app app-mobile nav-top">
  <header class="appbar appbar-start"><div class="appbar-title">숨결필라테스</div><div class="appbar-actions"><button class="btn btn-ghost btn-icon" aria-label="알림">…bell…</button></div></header>
  <nav class="toptabs"><a class="nav-item active" href="#">…<span>홈</span></a> …</nav>
  <main class="content">…</main>
</div>
```

메뉴 없는 한 장(온보딩 · shell: none)은 `<div class="app app-mobile no-nav">` + `<main class="content">`.

## 화면 첫머리 — 머리줄 + 큰 제목 + 회색 한 줄

```html
<x-page-header eyebrow="다음 수업 · 10월 13일(화)" title="오늘 20:00 리포머 중급" desc="숨결필라테스 망원 · 오지훈 강사"></x-page-header>
```
탭 화면은 제목만 크게(`<x-page-header title="내 예약">`) 두고 바로 나눔 버튼(`.segmented.w-full`)이나 판을 쌓아도 된다.

## 판 쌓기 — 회색 바탕 위 흰 판, 12px 간격

```html
<x-card data-region="next-class">
  <div class="row-between align-start">
    <div class="stack gap-1"><x-badge tone="success">예약함</x-badge><p class="fw-semibold">숨결필라테스 망원</p><p class="text-sm text-2">오지훈 강사 · 20:00~20:50 · 380m</p></div>
    <x-icon name="chevron-right" size="sm" tone="muted"/>
  </div>
  <p class="text-sm text-2">19:30부터 여기서 출석할 수 있어요</p>
</x-card>

<x-section title="대기 중인 수업" action="내 예약" action-trigger="open-bookings" data-region="waiting">
  <x-list>
    <x-item title="10/15(목) 20:00 리포머 중급" sub="18:58까지 확정 · 1시간 42분 남음" badge="확정 필요" badge-tone="warning"><x-icon name="chevron-right" size="sm"/></x-item>
    <x-item title="10/16(금) 20:00 리포머 기초" sub="무료 취소까지 2일 2시간 44분" badge="예약함" badge-tone="success"><x-icon name="chevron-right" size="sm"/></x-item>
  </x-list>
</x-section>
```
- `<x-section>` = 흰 판 하나(제목이 판 안). 안에 `<x-card>`를 또 넣지 않는다.
- 묶음 없이 판만 필요하면 `<x-card>`(제목이 있으면 `title=`).
- 판들을 영역으로 묶을 때는 클래스 없는 `<div data-region="…">`로 감싸도 간격이 그대로 유지된다.

## 큰 숫자

```html
<x-card data-region="pass">
  <p class="eyebrow">고요가 합정 10회권 · 7일 남음</p>
  <p class="big-num">잔여 3회 <small>/ 10</small></p>
  <p class="text-sm text-2">지금 예약 가능 3회</p>
</x-card>
```

## 고르기 — 나눔 버튼 · 칩

```html
<div class="segmented w-full" data-region="tabs"><button class="segmented-item active">예정 2</button><button class="segmented-item">대기 중 2</button><button class="segmented-item">지난 수업</button></div>
<div class="chip-group"><button class="chip active">기구 필라테스</button><button class="chip">매트</button><button class="chip">요가</button><button class="chip">1km 안</button></div>
```

## 아래 꽉 찬 버튼 — 본문 맨 마지막

```html
<div class="bottom-cta" data-region="book"><x-btn variant="primary" data-trigger="book">예약 확정</x-btn></div>
```
화면당 하나. 내용이 짧으면 맨 아래, 길면 아래에 붙어 따라온다. 탭 화면에서는 아래 탭 바로 위에 놓인다.
보조 버튼이 꼭 필요하면 primary 아래에 `<x-btn data-back>돌아가기</x-btn>`(같은 칸 안).

## 아래에서 올라오는 창 (뜨는 창 화면 — 파일 전체가 이것 하나)

```html
<x-modal title="방금 마감됐어요. 대기할까요?" desc="지금 대기 0명이라 1번째로 기다려요. 대기 신청할 땐 차감되지 않아요." data-region="waitlist">
  <div class="modal-footer"><x-btn variant="primary" data-trigger="join-waitlist">대기 신청</x-btn><x-btn data-back>돌아가기</x-btn></div>
</x-modal>
```
펼치면:
```html
<div class="modal-backdrop sheet-backdrop"><div class="modal sheet" role="dialog" data-region="waitlist">
  <span class="sheet-handle" aria-hidden="true"></span>
  <div class="modal-header"><div><h2 class="modal-title">방금 마감됐어요. 대기할까요?</h2><p class="modal-desc">…</p></div></div>
  <div class="modal-footer"><button class="btn btn-primary" data-trigger="join-waitlist">대기 신청</button><button class="btn btn-secondary" data-back>돌아가기</button></div>
</div></div>
```
루트는 `.modal-backdrop`(build가 뒷 화면 `.app`의 마지막 자식으로 넣는다). 영역은 `.modal`(또는 그 안)에 붙인다.
