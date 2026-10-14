# 60 · 오버레이 (modal · drawer · dropdown · popover)

오버레이는 **열린 상태를 정적으로 그리는 용도**다. 인터랙션은 없다.

핵심 규칙: **모달·드로어를 보여주는 화면은 "뒷 화면"을 평소처럼 완성한 뒤, `.modal-backdrop`(안에 `.modal` 또는 `.drawer`)을 `.app`의 마지막 자식으로 둔다.** backdrop은 프레임(.app) 기준 absolute 전체 덮개다(fixed 아님). 뒷 화면 내용은 실제 데이터로 채운다 — 흐려 보여도 사용자는 맥락을 본다.

```html
<div class="app">
  <header class="topnav">…</header>
  <aside class="sidebar">…</aside>
  <main class="content">… 뒷 화면 그대로 …</main>

  <!-- 마지막 자식 -->
  <div class="modal-backdrop">
    <div class="modal">…</div>
  </div>
</div>
```

## modal — 가운데 대화상자
언제: 만들기/편집 폼, 확인 질문, 상세 미리보기. 화면당 하나.

```html
<!-- 폼 모달 (기본 크기) -->
<div class="modal-backdrop">
  <div class="modal" role="dialog" aria-labelledby="m-title">
    <div class="modal-header">
      <div>
        <h2 class="modal-title" id="m-title">새 요청 만들기</h2>
        <p class="modal-desc">제출하면 담당자에게 알림이 갑니다.</p>
      </div>
      <button class="btn btn-icon btn-ghost" aria-label="닫기"><svg class="icon" aria-hidden="true"><use href="#i-x"/></svg></button>
    </div>
    <div class="modal-body">
      <div class="field"><label class="field-label">제목</label><input class="input" value="10월 사무용품 구매"></div>
      <div class="field"><label class="field-label">담당자</label><select class="select"><option>김민수</option></select></div>
      <div class="field"><label class="field-label">메모</label><textarea class="textarea">모니터 받침대 2개, A4 5박스</textarea></div>
    </div>
    <div class="modal-footer">
      <button class="btn btn-secondary">취소</button>
      <button class="btn btn-primary">제출</button>
    </div>
  </div>
</div>

<!-- 확인 대화상자 (작은 크기 · 가운데 아이콘) -->
<div class="modal-backdrop">
  <div class="modal modal-sm modal-center" role="alertdialog" aria-labelledby="d-title">
    <span class="modal-icon is-danger"><svg class="icon-lg" aria-hidden="true"><use href="#i-trash"/></svg></span>
    <div class="modal-header"><h2 class="modal-title" id="d-title">요청 3건을 삭제할까요?</h2></div>
    <div class="modal-body"><p class="text-2">삭제한 요청은 30일 뒤 완전히 지워집니다. 그 전까지는 보관함에서 되돌릴 수 있습니다.</p></div>
    <div class="modal-footer">
      <button class="btn btn-secondary">취소</button>
      <button class="btn btn-danger">삭제</button>
    </div>
  </div>
</div>

<!-- 큰 모달 (표·목록 미리보기) · 상단 정렬 -->
<div class="modal-backdrop align-top">
  <div class="modal modal-lg" role="dialog" aria-labelledby="l-title">
    <div class="modal-header"><h2 class="modal-title" id="l-title">참여자 선택</h2><button class="btn btn-icon btn-ghost" aria-label="닫기"><svg class="icon" aria-hidden="true"><use href="#i-x"/></svg></button></div>
    <div class="modal-body">
      <div class="search"><svg class="icon-sm" aria-hidden="true"><use href="#i-search"/></svg><input class="input" placeholder="이름 또는 팀 검색"></div>
      <ul class="list list-divided">
        <li class="list-item"><input class="checkbox" type="checkbox" checked aria-label="선택"><span class="avatar avatar-sm">김민</span><div class="list-main"><span class="list-title">김민수</span><span class="list-sub">영업1팀</span></div></li>
        <li class="list-item"><input class="checkbox" type="checkbox" aria-label="선택"><span class="avatar avatar-sm avatar-success">이서</span><div class="list-main"><span class="list-title">이서연</span><span class="list-sub">디자인팀</span></div></li>
        <li class="list-item"><input class="checkbox" type="checkbox" aria-label="선택"><span class="avatar avatar-sm avatar-warning">박준</span><div class="list-main"><span class="list-title">박준호</span><span class="list-sub">개발팀</span></div></li>
      </ul>
    </div>
    <div class="modal-footer"><span class="text-muted text-sm">1명 선택됨</span><button class="btn btn-secondary">취소</button><button class="btn btn-primary">추가</button></div>
  </div>
</div>

<!-- 아이콘 색 변형: modal-icon is-danger | is-warning | is-success | is-info | (기본 primary) -->
```
주의: 모달 안 primary 버튼이 그 화면의 유일한 primary다(뒷 화면 버튼은 secondary로 바꾼다). `modal-sm`(확인) · 기본(폼) · `modal-lg`(목록/표).

## drawer — 우측 패널
언제: 목록을 유지한 채 상세/편집을 옆에서 여는 화면. backdrop 안에 `.drawer`를 넣는다.

```html
<div class="modal-backdrop">
  <aside class="drawer" role="dialog" aria-labelledby="dr-title">
    <div class="drawer-header">
      <h2 class="drawer-title" id="dr-title">요청 상세 · #2041</h2>
      <div class="row gap-2">
        <button class="btn btn-icon btn-ghost" aria-label="더보기"><svg class="icon" aria-hidden="true"><use href="#i-ellipsis"/></svg></button>
        <button class="btn btn-icon btn-ghost" aria-label="닫기"><svg class="icon" aria-hidden="true"><use href="#i-x"/></svg></button>
      </div>
    </div>
    <div class="drawer-body">
      <div class="row gap-2"><span class="badge badge-warning">검토 중</span><span class="badge badge-neutral">구매</span></div>
      <h3 class="text-lg fw-semibold">사무용품 구매</h3>
      <div class="field"><label class="field-label">담당자</label><div class="row gap-2"><span class="avatar avatar-sm">김민</span>김민수</div></div>
      <div class="field"><label class="field-label">금액</label><span>128,000원</span></div>
      <div class="field"><label class="field-label">메모</label><p class="text-2">모니터 받침대 2개, A4 5박스</p></div>
      <hr class="divider">
      <div class="timeline timeline-compact">
        <div class="timeline-item"><span class="timeline-dot"></span><div class="timeline-content"><div class="timeline-title">검토 요청</div><p class="timeline-desc">김민수 · 9/26 10:15</p></div></div>
        <div class="timeline-item"><span class="timeline-dot dot-neutral"></span><div class="timeline-content"><div class="timeline-title">작성됨</div><p class="timeline-desc">김민수 · 9/25 16:40</p></div></div>
      </div>
    </div>
    <div class="drawer-footer">
      <button class="btn btn-secondary">반려</button>
      <button class="btn btn-primary">승인</button>
    </div>
  </aside>
</div>

<!-- 넓은 드로어 (편집 폼) -->
<div class="modal-backdrop"><aside class="drawer drawer-lg">…drawer-header / drawer-body(form) / drawer-footer…</aside></div>
```
주의: 목록+상세가 항상 함께 보이는 구조면 drawer가 아니라 `.split` 패턴(list-detail)을 쓴다.

## dropdown — 열린 메뉴
언제: "더보기" 버튼 아래 펼쳐진 메뉴, 정렬/필터 선택 메뉴. 트리거를 `.dropdown-anchor`로 감싸면 그 아래 붙는다.

```html
<div class="dropdown-anchor align-end">
  <button class="btn btn-icon btn-secondary" aria-label="더보기"><svg class="icon" aria-hidden="true"><use href="#i-ellipsis"/></svg></button>
  <div class="dropdown" role="menu">
    <button class="dropdown-item" role="menuitem"><svg class="icon-sm" aria-hidden="true"><use href="#i-pencil"/></svg> 편집 <span class="kbd">E</span></button>
    <button class="dropdown-item" role="menuitem"><svg class="icon-sm" aria-hidden="true"><use href="#i-copy"/></svg> 복제</button>
    <button class="dropdown-item" role="menuitem"><svg class="icon-sm" aria-hidden="true"><use href="#i-share-2"/></svg> 공유</button>
    <div class="dropdown-divider"></div>
    <button class="dropdown-item" role="menuitem"><svg class="icon-sm" aria-hidden="true"><use href="#i-archive"/></svg> 보관</button>
    <button class="dropdown-item is-danger" role="menuitem"><svg class="icon-sm" aria-hidden="true"><use href="#i-trash"/></svg> 삭제</button>
  </div>
</div>

<!-- 선택 메뉴 (라벨 + 현재 선택 표시) -->
<div class="dropdown-anchor">
  <button class="btn btn-secondary">정렬: 마감일 <svg class="icon-sm" aria-hidden="true"><use href="#i-chevron-down"/></svg></button>
  <div class="dropdown" role="menu">
    <div class="dropdown-label">정렬 기준</div>
    <button class="dropdown-item active" role="menuitemradio">마감일 <svg class="icon-sm check" aria-hidden="true"><use href="#i-check"/></svg></button>
    <button class="dropdown-item" role="menuitemradio">생성일</button>
    <button class="dropdown-item" role="menuitemradio">담당자</button>
    <button class="dropdown-item is-disabled" role="menuitemradio">우선순위 (준비 중)</button>
  </div>
</div>

<!-- 사용자 메뉴 (topnav 우측, 위로 열지 않음) -->
<div class="dropdown-anchor align-end">
  <button class="avatar avatar-sm" aria-label="내 메뉴">김민</button>
  <div class="dropdown" role="menu">
    <div class="dropdown-label">김민수 · 영업1팀</div>
    <button class="dropdown-item"><svg class="icon-sm" aria-hidden="true"><use href="#i-user"/></svg> 내 프로필</button>
    <button class="dropdown-item"><svg class="icon-sm" aria-hidden="true"><use href="#i-settings"/></svg> 설정</button>
    <div class="dropdown-divider"></div>
    <button class="dropdown-item"><svg class="icon-sm" aria-hidden="true"><use href="#i-log-out"/></svg> 로그아웃</button>
  </div>
</div>

<!-- 흐름 안에 단독으로(앵커 없이) 그릴 때 -->
<div class="dropdown">…dropdown-item…</div>
```
주의: 화면당 열린 dropdown은 하나. 앵커가 `.content` 오른쪽 끝이면 `align-end`, 화면 아래쪽이면 `align-top`.

## popover — 작은 설명 카드
언제: 항목 위에 뜨는 짧은 상세(담당자 카드, 도움말, 미니 확인). 트리거를 `.popover-anchor`로 감싼다.

```html
<div class="popover-anchor">
  <span class="avatar avatar-sm">이서</span>
  <div class="popover">
    <div class="row gap-2"><span class="avatar">이서</span><div class="stack"><span class="fw-semibold">이서연</span><span class="text-muted text-sm">디자인팀 · 리드</span></div></div>
    <p class="popover-desc">진행 중 3건 · 이번 주 휴가 없음</p>
    <div class="popover-actions"><button class="btn btn-secondary btn-sm">메시지</button><button class="btn btn-primary btn-sm">배정</button></div>
  </div>
</div>

<!-- 도움말 · 미니 확인 -->
<div class="popover-anchor">
  <button class="btn btn-icon btn-ghost btn-sm" aria-label="도움말"><svg class="icon-sm" aria-hidden="true"><use href="#i-circle-question-mark"/></svg></button>
  <div class="popover"><div class="popover-title">승인 한도란?</div><p class="popover-desc">직급별로 단독 승인할 수 있는 최대 금액입니다. 초과 시 상위 결재자에게 넘어갑니다.</p></div>
</div>
<div class="popover-anchor align-end">
  <button class="btn btn-ghost btn-sm">보관</button>
  <div class="popover"><div class="popover-title">보관할까요?</div><p class="popover-desc">보관함에서 언제든 복원할 수 있습니다.</p><div class="popover-actions"><button class="btn btn-secondary btn-sm">취소</button><button class="btn btn-primary btn-sm">보관</button></div></div>
</div>
```
주의: 화살표는 없다(그래도 트리거 바로 아래 붙어 보인다). 폼이 들어가면 popover가 아니라 modal.
