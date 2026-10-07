# 40 · 표시 (card · badge · chip · avatar · tabs · breadcrumb · progress · stat · empty · skeleton · divider · banner · toast · tooltip · kbd)

공통: 아이콘은 `<svg class="icon" aria-hidden="true"><use href="#i-<name>"/></svg>` (`icon-sm` 16 · `icon` 20 · `icon-lg` 24). 인라인 `style=` 금지 — 너비는 `.w-10`~`.w-100`.

## card — 내용을 묶는 기본 상자
언제: 목록·폼·요약 등 "한 덩어리"를 배경 위에 띄울 때. 페이지 안 거의 모든 블록의 바탕.

```html
<!-- 기본: header + body + footer (필요 없는 부분은 생략 가능) -->
<section class="card">
  <div class="card-header">
    <h3 class="card-title">이번 주 승인 대기</h3>
    <button class="btn btn-ghost btn-sm">전체 보기</button>
  </div>
  <div class="card-body">
    <p>결재 대기 문서 4건이 있습니다. 가장 오래된 건은 3일 전 접수되었습니다.</p>
  </div>
  <div class="card-footer">
    <button class="btn btn-secondary">나중에</button>
    <button class="btn btn-primary">검토하기</button>
  </div>
</section>

<!-- body만 있는 카드 -->
<div class="card"><div class="card-body">간단한 안내 문장 하나.</div></div>

<!-- 선택된 카드 · 클릭 가능한 카드 -->
<div class="card is-selected"><div class="card-body">선택된 항목</div></div>
<a class="card card-clickable" href="#"><div class="card-body">눌러서 열기</div></a>

<!-- 여백이 좁은 카드 -->
<div class="card card-compact"><div class="card-body">사이드 패널용 좁은 카드</div></div>

<!-- 카드 안에 목록/표를 여백 없이 붙일 때: card-body 없이 직접 자식으로 -->
<div class="card">
  <div class="card-header"><h3 class="card-title">최근 활동</h3></div>
  <ul class="list list-divided">…list-item…</ul>
</div>
```
주의: 카드 안에 카드를 넣지 않는다. 제목은 `card-title` 하나만.

## badge — 상태 표시 (화면 전체에서 같은 의미 = 같은 색)
언제: 확정/대기/지연 같은 상태, 카운트, 유형 라벨.

```html
<span class="badge badge-neutral">초안</span>
<span class="badge badge-primary">진행 중</span>
<span class="badge badge-success">완료</span>
<span class="badge badge-warning">지연</span>
<span class="badge badge-danger">반려</span>
<span class="badge badge-info">검토 요청</span>

<!-- 점 변형 (색 점 + 글자) -->
<span class="badge badge-dot badge-success">운영 중</span>
<span class="badge badge-dot badge-warning">점검 예정</span>
<span class="badge badge-dot badge-neutral">중지</span>

<!-- 아이콘 포함 · 숫자 카운트 -->
<span class="badge badge-danger"><svg class="icon-sm" aria-hidden="true"><use href="#i-circle-alert"/></svg> 오류 2</span>
<span class="badge badge-neutral">12</span>
```
주의: 색 없는 `badge`만 쓰면 neutral로 보인다. 한 화면에서 같은 상태에 다른 색을 섞지 않는다.

## chip — 필터·태그 (선택 가능한 알약)
언제: 필터 바의 토글, 선택된 태그 나열, 삭제 가능한 항목.

```html
<div class="chip-group">
  <button class="chip active">전체</button>
  <button class="chip">내 담당</button>
  <button class="chip">이번 주</button>
  <button class="chip"><svg class="icon-sm" aria-hidden="true"><use href="#i-funnel"/></svg> 필터 3</button>
</div>

<!-- 닫기 아이콘 포함 (선택된 태그) -->
<span class="chip active">
  디자인팀
  <button class="chip-close" aria-label="디자인팀 제거"><svg class="icon-sm" aria-hidden="true"><use href="#i-x"/></svg></button>
</span>
```
주의: 페이지 이동은 `.tabs`, 상태 표시는 `.badge`. chip은 "고르는" 용도.

## avatar — 사람 이니셜 원
언제: 담당자, 작성자, 참여자 표시. 사진 없이 이니셜 텍스트로.

```html
<span class="avatar">김민</span>
<span class="avatar avatar-sm">이서</span>
<span class="avatar avatar-lg">박준</span>
<!-- 색 변형 (사람 구분용) -->
<span class="avatar avatar-neutral">JK</span>
<span class="avatar avatar-success">최아</span>
<span class="avatar avatar-warning">정우</span>
<span class="avatar avatar-info">한별</span>

<!-- 겹쳐 쌓기 + 더보기 -->
<div class="avatar-group">
  <span class="avatar avatar-sm">김민</span>
  <span class="avatar avatar-sm avatar-success">이서</span>
  <span class="avatar avatar-sm avatar-warning">박준</span>
  <span class="avatar avatar-sm avatar-more">+4</span>
</div>

<!-- 이름과 함께 -->
<div class="row gap-2"><span class="avatar avatar-sm">김민</span><span>김민수 <span class="text-muted text-sm">· 운영팀</span></span></div>
```
주의: 이니셜은 2글자. 한 사람은 화면 전체에서 같은 색 변형.

## tabs — 같은 페이지 안 콘텐츠 전환
언제: 상세 화면의 "개요 / 활동 / 파일" 같은 뷰 전환.

```html
<nav class="tabs">
  <a class="tab active" href="#">개요</a>
  <a class="tab" href="#">활동 <span class="badge badge-neutral">8</span></a>
  <a class="tab" href="#">파일</a>
  <a class="tab" href="#">설정</a>
</nav>

<!-- 아이콘 포함 -->
<nav class="tabs">
  <a class="tab active" href="#"><svg class="icon-sm" aria-hidden="true"><use href="#i-list"/></svg> 목록</a>
  <a class="tab" href="#"><svg class="icon-sm" aria-hidden="true"><use href="#i-kanban"/></svg> 보드</a>
  <a class="tab" href="#"><svg class="icon-sm" aria-hidden="true"><use href="#i-calendar"/></svg> 달력</a>
</nav>

<!-- 알약형 (밑줄 대신 배경) -->
<nav class="tabs tabs-pill">
  <a class="tab active" href="#">주간</a>
  <a class="tab" href="#">월간</a>
  <a class="tab" href="#">분기</a>
</nav>
```
주의: 활성 탭은 정확히 하나. 페이지 간 이동은 sidebar `.nav`.

## breadcrumb — 현재 위치 경로
언제: 3단 이상 깊이의 상세 화면 상단(page-header 위).

```html
<nav class="breadcrumb" aria-label="현재 위치">
  <a href="#">프로젝트</a>
  <svg class="icon-sm" aria-hidden="true"><use href="#i-chevron-right"/></svg>
  <a href="#">2026 하반기 개편</a>
  <svg class="icon-sm" aria-hidden="true"><use href="#i-chevron-right"/></svg>
  <span aria-current="page">요구사항 정의서</span>
</nav>
```
주의: 마지막 항목은 링크가 아니라 `aria-current="page"`.

## progress — 진행률 막대
언제: 완료 비율, 사용량, 단계 진행. 너비는 `.w-10`~`.w-100` (10% 단위).

```html
<div class="progress"><div class="progress-bar w-60"></div></div>

<!-- 크기 · 색 변형 -->
<div class="progress progress-sm"><div class="progress-bar w-30"></div></div>
<div class="progress progress-lg progress-success"><div class="progress-bar w-100"></div></div>
<div class="progress progress-warning"><div class="progress-bar w-80"></div></div>
<div class="progress progress-danger"><div class="progress-bar w-90"></div></div>

<!-- 숫자와 함께 한 줄 -->
<div class="progress-row">
  <div class="progress"><div class="progress-bar w-70"></div></div>
  <span class="progress-num">70%</span>
</div>

<!-- 라벨 + 막대 (카드 안) -->
<div class="stack gap-2">
  <div class="row row-between text-sm"><span>저장 공간</span><span class="text-muted">7.2 / 10 GB</span></div>
  <div class="progress"><div class="progress-bar w-70"></div></div>
</div>
```
주의: 값이 5% 단위라도 가까운 10%로 반올림한다. 인라인 width 금지.

## stat — 숫자 요약 타일
언제: 대시보드 상단 KPI 4개, 상세 화면의 핵심 수치. 보통 `.card > .card-body` 안에 둔다.

```html
<div class="card"><div class="card-body">
  <div class="stat">
    <span class="stat-label">이번 달 처리 건수</span>
    <span class="stat-value">1,284</span>
    <span class="stat-delta up"><svg class="icon-sm" aria-hidden="true"><use href="#i-trending-up"/></svg> 12.4% 지난달 대비</span>
  </div>
</div></div>

<!-- 하락 · 변화 없음 · 단위 -->
<div class="stat">
  <span class="stat-label">평균 응답 시간</span>
  <span class="stat-value">3.2<small>시간</small></span>
  <span class="stat-delta down"><svg class="icon-sm" aria-hidden="true"><use href="#i-trending-down"/></svg> 0.8시간 느려짐</span>
</div>
<div class="stat">
  <span class="stat-label">활성 사용자</span>
  <span class="stat-value">412</span>
  <span class="stat-delta">지난주와 같음</span>
</div>

<!-- 아이콘 원이 붙은 형태 -->
<div class="card"><div class="card-body">
  <div class="stat-row">
    <div class="stat">
      <span class="stat-label">미결 요청</span>
      <span class="stat-value">27</span>
      <span class="stat-delta down"><svg class="icon-sm" aria-hidden="true"><use href="#i-arrow-up"/></svg> 5건 증가</span>
    </div>
    <span class="stat-icon"><svg class="icon" aria-hidden="true"><use href="#i-inbox"/></svg></span>
  </div>
</div></div>
```
주의: `up`은 좋은 방향(초록), `down`은 나쁜 방향(빨강)이지 화살표 방향이 아니다. 4개면 `.grid-4`에.

## empty — 비어 있는 상태
언제: 목록에 항목이 0개일 때, 검색 결과 없음, 아직 설정 전.

```html
<div class="empty">
  <span class="empty-icon"><svg class="icon-lg" aria-hidden="true"><use href="#i-inbox"/></svg></span>
  <h3 class="empty-title">아직 등록된 요청이 없습니다</h3>
  <p class="empty-desc">첫 요청을 만들면 여기에 목록으로 나타납니다.</p>
  <div class="empty-actions">
    <button class="btn btn-primary"><svg class="icon-sm" aria-hidden="true"><use href="#i-plus"/></svg> 요청 만들기</button>
  </div>
</div>

<!-- 검색 결과 없음 (작은 변형, CTA 없음) -->
<div class="empty empty-sm">
  <span class="empty-icon"><svg class="icon" aria-hidden="true"><use href="#i-search"/></svg></span>
  <h3 class="empty-title">'정산 보고'에 대한 결과가 없습니다</h3>
  <p class="empty-desc">검색어를 줄이거나 필터를 해제해 보세요.</p>
</div>
```
주의: 화면당 primary 버튼은 1개 규칙에 포함된다. 빈 상태를 보여주는 화면이 아니라면 목록을 3~5행 채운다.

## skeleton — 로딩 자리표시자 / 차트 자리
언제: 로딩 화면, 그리고 **차트·지도·이미지처럼 하네스가 그리지 않는 영역의 회색 자리**.

```html
<!-- 차트 자리 (대시보드) -->
<div class="skeleton skeleton-block"></div>

<!-- 텍스트 줄 -->
<div class="skeleton skeleton-title"></div>
<div class="skeleton skeleton-text"></div>
<div class="skeleton skeleton-text"></div>
<div class="skeleton skeleton-text w-60"></div>

<!-- 아바타 + 두 줄 (목록 행 로딩) -->
<div class="skeleton-row">
  <div class="skeleton skeleton-circle"></div>
  <div class="skeleton-lines">
    <div class="skeleton skeleton-text w-40"></div>
    <div class="skeleton skeleton-text w-80"></div>
  </div>
</div>
```
주의: 차트 자리는 `skeleton-block` 하나 + 위에 `card-title`로 "무슨 차트인지" 적는다. 실제 차트를 그리지 않는다.

## divider — 구분선
언제: 같은 카드 안에서 섹션을 나눌 때. 카드 사이에는 쓰지 않는다(간격으로 충분).

```html
<hr class="divider">
<hr class="divider divider-tight">
<!-- 가운데 글자 -->
<div class="divider divider-text">또는</div>
<!-- 세로 (row 안에서) -->
<div class="row gap-2"><span>저장됨</span><span class="divider divider-vertical"></span><span class="text-muted">2분 전</span></div>
```
주의: 목록 행 사이는 `.list-divided`로 처리한다.

## banner — 화면 안 안내 띠
언제: 페이지 상단의 공지·경고·성공 안내. 닫기 버튼은 선택.

```html
<div class="banner banner-info">
  <svg class="icon" aria-hidden="true"><use href="#i-info"/></svg>
  <div class="banner-body">
    <span class="banner-title">10월 1일부터 승인 절차가 바뀝니다</span>
    <span>2단계 승인이 기본이 됩니다. 기존 진행 건은 영향이 없습니다.</span>
  </div>
  <div class="banner-actions">
    <button class="btn btn-ghost btn-sm">자세히</button>
    <button class="btn btn-icon btn-ghost btn-sm" aria-label="닫기"><svg class="icon-sm" aria-hidden="true"><use href="#i-x"/></svg></button>
  </div>
</div>

<div class="banner banner-warning">
  <svg class="icon" aria-hidden="true"><use href="#i-triangle-alert"/></svg>
  <div class="banner-body">결제 수단이 이번 달 말 만료됩니다.</div>
  <div class="banner-actions"><button class="btn btn-secondary btn-sm">갱신</button></div>
</div>

<div class="banner banner-success">
  <svg class="icon" aria-hidden="true"><use href="#i-circle-check"/></svg>
  <div class="banner-body">변경 사항이 저장되었습니다.</div>
</div>

<div class="banner banner-danger">
  <svg class="icon" aria-hidden="true"><use href="#i-circle-alert"/></svg>
  <div class="banner-body"><span class="banner-title">동기화 실패</span><span>서버에 연결할 수 없습니다. 잠시 후 다시 시도하세요.</span></div>
  <div class="banner-actions"><button class="btn btn-secondary btn-sm">재시도</button></div>
</div>

<!-- 색 없는 기본 (중립 안내) -->
<div class="banner"><svg class="icon" aria-hidden="true"><use href="#i-lightbulb"/></svg><div class="banner-body">Tab 키로 다음 칸으로 이동할 수 있습니다.</div></div>
```
주의: 화면당 배너는 1개. 일시적 결과 알림은 `.toast`.

## toast — 방금 일어난 일 알림 (화면 위쪽 가운데 · 본문 크기 글자 — 기본 규칙. 위치는 조각에서 바꾸지 않는다)
언제: "저장됨" "삭제됨" 같은 결과를 보여주는 화면. `.app`의 마지막 자식으로 둔다.

```html
<div class="toast toast-success" role="status">
  <svg class="icon" aria-hidden="true"><use href="#i-circle-check"/></svg>
  <div class="toast-body">
    <span class="toast-title">요청이 제출되었습니다</span>
    <span class="toast-desc">담당자 승인 후 알림을 보내드립니다.</span>
  </div>
  <button class="btn btn-icon btn-ghost btn-sm" aria-label="닫기"><svg class="icon-sm" aria-hidden="true"><use href="#i-x"/></svg></button>
</div>

<!-- 되돌리기 액션 포함 -->
<div class="toast" role="status">
  <svg class="icon" aria-hidden="true"><use href="#i-trash"/></svg>
  <div class="toast-body">
    <span class="toast-title">항목 3개를 삭제했습니다</span>
    <div class="toast-actions"><button class="btn btn-ghost btn-sm">되돌리기</button></div>
  </div>
</div>

<!-- 오류 · 경고 · 정보 -->
<div class="toast toast-danger" role="alert"><svg class="icon" aria-hidden="true"><use href="#i-circle-alert"/></svg><div class="toast-body"><span class="toast-title">업로드 실패</span><span class="toast-desc">파일 크기는 20MB 이하여야 합니다.</span></div></div>
<div class="toast toast-warning" role="status"><svg class="icon" aria-hidden="true"><use href="#i-triangle-alert"/></svg><div class="toast-body"><span class="toast-title">저장되지 않은 변경이 있습니다</span></div></div>
<div class="toast toast-info" role="status"><svg class="icon" aria-hidden="true"><use href="#i-info"/></svg><div class="toast-body"><span class="toast-title">새 버전이 있습니다</span></div></div>

<!-- 여러 개 쌓기 -->
<div class="toast-stack">
  <div class="toast toast-success" role="status"><svg class="icon" aria-hidden="true"><use href="#i-circle-check"/></svg><div class="toast-body"><span class="toast-title">저장됨</span></div></div>
  <div class="toast" role="status"><svg class="icon" aria-hidden="true"><use href="#i-bell"/></svg><div class="toast-body"><span class="toast-title">새 댓글 1개</span></div></div>
</div>
```
주의: 정적 그림이다. 한 화면에 toast는 하나(또는 stack 하나)만. 모달과 같이 쓰면 backdrop 뒤에 가려지므로 toast를 더 뒤에 둔다.

## tooltip — 정적 말풍선
언제: 아이콘 버튼의 이름을 보여주는 상태를 그릴 때. 트리거를 `.tooltip-anchor`로 감싼다.

```html
<span class="tooltip-anchor">
  <button class="btn btn-icon btn-ghost" aria-label="공유"><svg class="icon" aria-hidden="true"><use href="#i-share-2"/></svg></button>
  <span class="tooltip" role="tooltip">공유</span>
</span>

<!-- 아래쪽에 표시 · 단독(anchor 없이 흐름 안에) -->
<span class="tooltip-anchor tooltip-bottom"><span class="badge badge-warning">지연</span><span class="tooltip" role="tooltip">마감 2일 초과</span></span>
<span class="tooltip">단축키 ⌘K</span>
```
주의: 화면당 하나만. 여러 개 켜진 상태는 실제로 존재하지 않는다.

## kbd — 키보드 키
언제: 단축키 안내(검색창 옆, 드롭다운 메뉴 우측).

```html
<span class="kbd">⌘</span><span class="kbd">K</span>
<span class="text-sm text-muted">저장 <span class="kbd">⌘</span><span class="kbd">S</span></span>
```
주의: 실제 동작은 없다. 한 키 = kbd 하나.
