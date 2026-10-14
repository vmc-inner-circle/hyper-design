# 20-buttons — 버튼 변형 · 크기 · 아이콘 버튼 · 버튼 그룹 · 링크

규칙: 화면당 `.btn-primary`는 **1개**. 아이콘만 있는 버튼은 `aria-label` 필수. 클릭 요소는 `<button>`(이동은 `<a class="btn">`도 가능).

## btn (변형)
언제: 기본 `.btn`은 secondary(테두리). 핵심 행동 1개만 `.btn-primary`. 보조·취소는 `.btn-ghost`. 되돌릴 수 없는 삭제는 `.btn-danger`.

```html
<button class="btn btn-primary">일정 확정</button>
<button class="btn">임시 저장</button>
<button class="btn btn-secondary">임시 저장</button>
<button class="btn btn-soft">후보로 추가</button>
<button class="btn btn-ghost">취소</button>
<button class="btn btn-danger">세션 삭제</button>
<button class="btn btn-danger-soft">참석 취소</button>
```

변형 — 아이콘 + 텍스트 (아이콘은 항상 앞, 뒤는 화살표류만):

```html
<button class="btn btn-primary"><svg class="icon" aria-hidden="true"><use href="#i-plus"/></svg>세션 추가</button>
<button class="btn"><svg class="icon" aria-hidden="true"><use href="#i-download"/></svg>내보내기</button>
<button class="btn btn-ghost">다음 단계<svg class="icon" aria-hidden="true"><use href="#i-arrow-right"/></svg></button>
```

변형 — 상태:

```html
<button class="btn btn-primary" disabled>일정 확정</button>
<button class="btn is-loading"><svg class="icon icon-spin" aria-hidden="true"><use href="#i-loader-circle"/></svg>저장 중…</button>
<a class="btn" href="#"><svg class="icon" aria-hidden="true"><use href="#i-external-link"/></svg>회의실 예약 열기</a>
```

주의: `.btn-secondary`는 `.btn`과 같다(가독성용). `.btn-soft`는 primary의 약한 버전이라 primary와 나란히 두지 않는다.

## 크기 (btn-sm / btn-lg)
언제: 표 행·카드 안은 `.btn-sm`, 온보딩·빈 화면의 단일 CTA는 `.btn-lg`. 기본은 클래스 없음.

```html
<button class="btn btn-sm">상세</button>
<button class="btn btn-primary btn-sm"><svg class="icon" aria-hidden="true"><use href="#i-check"/></svg>승인</button>
<button class="btn btn-ghost btn-sm">보류</button>

<button class="btn btn-primary btn-lg"><svg class="icon" aria-hidden="true"><use href="#i-calendar-plus"/></svg>첫 일정 만들기</button>
<button class="btn btn-lg">나중에 하기</button>
```

주의: 한 줄(같은 `.row`)에는 같은 크기만.

## btn-icon (아이콘 전용 정사각)
언제: 공간이 좁은 반복 행동(수정·삭제·더보기·닫기). `aria-label` 필수.

```html
<button class="btn btn-icon" aria-label="수정"><svg class="icon" aria-hidden="true"><use href="#i-pencil"/></svg></button>
<button class="btn btn-ghost btn-icon" aria-label="더보기"><svg class="icon" aria-hidden="true"><use href="#i-ellipsis"/></svg></button>
<button class="btn btn-ghost btn-icon" aria-label="닫기"><svg class="icon" aria-hidden="true"><use href="#i-x"/></svg></button>
<button class="btn btn-danger-soft btn-icon" aria-label="삭제"><svg class="icon" aria-hidden="true"><use href="#i-trash"/></svg></button>
<button class="btn btn-primary btn-icon" aria-label="추가"><svg class="icon" aria-hidden="true"><use href="#i-plus"/></svg></button>
```

변형 — 크기·둥근 모양:

```html
<button class="btn btn-ghost btn-icon btn-sm" aria-label="복사"><svg class="icon" aria-hidden="true"><use href="#i-copy"/></svg></button>
<button class="btn btn-icon btn-lg" aria-label="새로고침"><svg class="icon" aria-hidden="true"><use href="#i-refresh-cw"/></svg></button>
<button class="btn btn-primary btn-icon btn-round" aria-label="새 일정"><svg class="icon" aria-hidden="true"><use href="#i-plus"/></svg></button>
```

주의: 아이콘 버튼 안에 텍스트를 넣지 않는다(텍스트가 필요하면 일반 `.btn`).

## btn-group (붙은 버튼 묶음)
언제: 서로 관련된 2~4개 행동, 또는 보기 전환(목록/카드). 선택 상태는 `.active`.

```html
<div class="btn-group">
  <button class="btn btn-icon active" aria-label="목록 보기"><svg class="icon" aria-hidden="true"><use href="#i-list"/></svg></button>
  <button class="btn btn-icon" aria-label="카드 보기"><svg class="icon" aria-hidden="true"><use href="#i-layout-grid"/></svg></button>
  <button class="btn btn-icon" aria-label="달력 보기"><svg class="icon" aria-hidden="true"><use href="#i-calendar"/></svg></button>
</div>

<div class="btn-group">
  <button class="btn btn-sm btn-icon" aria-label="이전 주"><svg class="icon" aria-hidden="true"><use href="#i-chevron-left"/></svg></button>
  <button class="btn btn-sm">이번 주</button>
  <button class="btn btn-sm btn-icon" aria-label="다음 주"><svg class="icon" aria-hidden="true"><use href="#i-chevron-right"/></svg></button>
</div>

<div class="btn-group">
  <button class="btn btn-primary">저장</button>
  <button class="btn btn-primary btn-icon" aria-label="저장 옵션"><svg class="icon" aria-hidden="true"><use href="#i-chevron-down"/></svg></button>
</div>
```

주의: 배타 선택이 3개 이상 텍스트면 `.segmented`(30-inputs.md)를 쓴다. 그룹 안은 모두 같은 크기.

## btn-block (전체 폭)
언제: 카드·드로어·모달 하단, 로그인/온보딩의 단일 행동.

```html
<button class="btn btn-primary btn-block">초대 보내기</button>
<button class="btn btn-block">나중에 초대하기</button>
```

주의: 본문 폭이 넓은 `.content` 최상위에는 쓰지 않는다(카드/폼 안에서만).

## link (텍스트 링크)
언제: 문장 속 이동, 섹션 제목 우측의 "전체 보기", 보조 행동.

```html
<a class="link" href="#">참석자 명단 보기</a>
<button class="link">초대 링크 복사<svg class="icon-sm" aria-hidden="true"><use href="#i-copy"/></svg></button>
<button class="link link-muted">전체 보기</button>
<p class="text-sm text-2">응답하지 않은 6명에게 <button class="link">리마인드 보내기</button></p>
```

주의: 링크는 primary 버튼 대신이 아니다. 화면의 주 행동은 항상 `.btn-primary`.

## 배치 관례 (form-actions · page-actions)

```html
<!-- 우측 정렬, 가장 오른쪽이 primary -->
<div class="form-actions">
  <button class="btn btn-ghost">취소</button>
  <button class="btn btn-primary">저장</button>
</div>

<!-- 좌측에 위험 행동, 우측에 취소/저장 -->
<div class="form-actions">
  <button class="btn btn-danger-soft"><svg class="icon" aria-hidden="true"><use href="#i-trash"/></svg>세션 삭제</button>
  <div class="spacer"></div>
  <button class="btn btn-ghost">취소</button>
  <button class="btn btn-primary">변경 저장</button>
</div>
```

주의: 순서는 "취소 → 확인". 위험 행동은 primary와 떨어뜨린다.
