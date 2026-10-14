# 30-inputs — field · input · select · textarea · input-group · checkbox · radio · switch · segmented · search · form-grid

규칙: 입력은 항상 `.field`로 감싸고 `<label for>`↔`id`를 잇는다. 필수 표시는 `<span class="req">*</span>`. placeholder는 예시 값, 라벨 대신 쓰지 않는다.

## field (라벨 + 컨트롤 + 도움말/오류)
언제: 모든 입력의 기본 단위.

```html
<div class="field">
  <label class="field-label" for="f-title">세션 제목 <span class="req">*</span></label>
  <input class="input" id="f-title" type="text" placeholder="예: 오프닝 세션 · 팀 소개">
  <p class="field-help">참석자 초대장에 그대로 표시됩니다.</p>
</div>
```

변형 — 오류 · 비활성 · 선택 항목:

```html
<div class="field is-error">
  <label class="field-label" for="f-email">이메일 <span class="req">*</span></label>
  <input class="input" id="f-email" type="email" value="hana.kim@">
  <p class="field-error"><svg class="icon-sm" aria-hidden="true"><use href="#i-circle-alert"/></svg>이메일 형식이 올바르지 않습니다.</p>
</div>

<div class="field is-disabled">
  <label class="field-label" for="f-owner">담당자</label>
  <input class="input" id="f-owner" type="text" value="김하은" disabled>
  <p class="field-help">담당자는 운영팀만 바꿀 수 있습니다.</p>
</div>

<div class="field">
  <label class="field-label" for="f-memo">메모 <span class="opt">(선택)</span></label>
  <textarea class="textarea" id="f-memo" placeholder="준비물, 유의사항 등"></textarea>
</div>
```

변형 — 가로 배치(설정 화면의 스위치·셀렉트 행):

```html
<div class="field field-inline">
  <div>
    <div class="field-label">일정 변경 알림</div>
    <p class="field-help">시간·장소가 바뀌면 참석자에게 메일을 보냅니다.</p>
  </div>
  <label class="switch"><input type="checkbox" checked><span class="sr-only">일정 변경 알림</span></label>
</div>
```

주의: `.field-error`는 `.field.is-error`일 때만 보인다(항상 넣어 두어도 됨). 오류 문구는 "무엇을 어떻게" 고칠지 쓴다.

## input (한 줄 입력)
언제: 짧은 텍스트·숫자·날짜·시간.

```html
<input class="input" type="text" placeholder="세션 제목">
<input class="input" type="number" value="24" min="1">
<input class="input" type="date" value="2026-09-12">
<input class="input" type="time" value="09:30">
<input class="input" type="text" value="대회의실 A" readonly>
<input class="input input-sm" type="text" placeholder="작은 입력(표 안)">
<input class="input input-lg" type="text" placeholder="큰 입력(온보딩)">
```

주의: 폭은 부모(`.field`·`.form-grid`)가 정한다. 짧은 값(시간·인원)은 `.grid-2`/`.row`로 나란히.

## select
언제: 5~15개 중 하나 고르기. `.select-wrap`으로 감싸면 테마 아이콘 화살표가 붙는다(권장).

```html
<div class="field">
  <label class="field-label" for="f-room">장소</label>
  <div class="select-wrap">
    <select class="select" id="f-room">
      <option>대회의실 A</option>
      <option selected>대회의실 B</option>
      <option>세미나실 3</option>
      <option>온라인(화상)</option>
    </select>
    <svg class="icon" aria-hidden="true"><use href="#i-chevron-down"/></svg>
  </div>
</div>

<!-- 단독(네이티브 화살표) · 작은 크기 -->
<select class="select select-sm"><option>시작 시각순</option><option>이름순</option></select>
```

주의: 항목이 4개 이하면 `.segmented` 또는 `.radio`가 더 빠르다.

## textarea
언제: 여러 줄 메모·설명·안내문.

```html
<div class="field">
  <label class="field-label" for="f-desc">세션 설명</label>
  <textarea class="textarea" id="f-desc" rows="4" placeholder="세션 목적, 진행 방식, 준비물">각 팀이 3분씩 올해 목표를 공유합니다. 발표 자료는 9월 10일까지 업로드.</textarea>
  <p class="field-help">초대장과 안내 페이지에 표시됩니다.</p>
</div>
```

주의: 세로 크기만 조절 가능. `rows`로 초기 높이를 준다(3~6).

## input-group (접두/접미 · 아이콘 · 버튼 결합)
언제: 단위·통화·URL 접두, 입력 옆 실행 버튼, 입력 안 아이콘.

```html
<!-- 접두/접미 -->
<div class="input-group">
  <span class="input-addon">₩</span>
  <input class="input" type="text" value="1,240,000">
</div>
<div class="input-group">
  <input class="input" type="number" value="50">
  <span class="input-addon">분</span>
</div>

<!-- 입력 + 버튼 -->
<div class="input-group">
  <input class="input" type="text" value="https://team.example/ws/sep-2026" readonly>
  <button class="btn"><svg class="icon" aria-hidden="true"><use href="#i-copy"/></svg>복사</button>
</div>
<div class="input-group">
  <input class="input" type="email" placeholder="초대할 이메일">
  <button class="btn btn-primary">초대</button>
</div>

<!-- 아이콘 안쪽 (앞 / 뒤) -->
<div class="input-group">
  <svg class="icon" aria-hidden="true"><use href="#i-map-pin"/></svg>
  <input class="input" type="text" placeholder="장소 검색">
</div>
<div class="input-group">
  <input class="input" type="password" value="••••••••">
  <svg class="icon" aria-hidden="true"><use href="#i-eye"/></svg>
</div>
```

주의: 그룹 안의 `.btn`은 1개. 검색만 필요하면 `.search`를 쓴다.

## search (돋보기 + 입력)
언제: 목록·표 위 툴바, 상단바. 기본 폭 320, `.w-full`로 꽉 채움.

```html
<div class="search">
  <svg class="icon" aria-hidden="true"><use href="#i-search"/></svg>
  <input class="input" type="search" placeholder="세션·발표자 검색">
</div>

<div class="search w-full">
  <svg class="icon" aria-hidden="true"><use href="#i-search"/></svg>
  <input class="input input-sm" type="search" placeholder="참석자 검색">
</div>
```

주의: `<input type="search">` 사용. 검색 버튼은 붙이지 않는다(입력 즉시 필터).

## checkbox
언제: 여러 개 선택, 동의·옵션 켜기(저장 버튼과 함께). 즉시 반영되는 설정은 `.switch`.

```html
<label class="checkbox"><input type="checkbox" checked>점심 도시락 신청</label>
<label class="checkbox"><input type="checkbox">셔틀버스 이용</label>
<label class="checkbox"><input type="checkbox" disabled>주차 등록 (마감)</label>

<!-- 세로 목록 -->
<div class="field">
  <div class="field-label">참여 세션</div>
  <div class="stack gap-2">
    <label class="checkbox"><input type="checkbox" checked>오프닝 · 팀 소개</label>
    <label class="checkbox"><input type="checkbox" checked>워크숍 A · 고객 여정 그리기</label>
    <label class="checkbox"><input type="checkbox">워크숍 B · 회고 방법론</label>
    <label class="checkbox"><input type="checkbox">네트워킹 디너</label>
  </div>
</div>

<!-- 설명 있는 항목 -->
<label class="checkbox align-start"><input type="checkbox"><span>사진 촬영 동의<span class="desc">행사 사진이 사내 뉴스레터에 실릴 수 있습니다.</span></span></label>
```

주의: `<label>`이 곧 클릭 영역. 텍스트는 input 뒤에 둔다.

## radio
언제: 2~5개 중 하나. 항목 이름은 짧게.

```html
<div class="field">
  <div class="field-label">참석 방식</div>
  <div class="row gap-4">
    <label class="radio"><input type="radio" name="attend" checked>현장 참석</label>
    <label class="radio"><input type="radio" name="attend">온라인 참석</label>
    <label class="radio"><input type="radio" name="attend">불참</label>
  </div>
</div>

<div class="stack gap-2">
  <label class="radio align-start"><input type="radio" name="remind" checked><span>하루 전 알림<span class="desc">9월 11일 오전 9시에 메일 발송</span></span></label>
  <label class="radio align-start"><input type="radio" name="remind"><span>1시간 전 알림<span class="desc">세션 시작 1시간 전 푸시 알림</span></span></label>
  <label class="radio"><input type="radio" name="remind">알림 없음</label>
</div>
```

주의: 같은 묶음은 같은 `name`. 하나는 기본 `checked`.

## switch
언제: 즉시 적용되는 켜기/끄기(알림·공개 여부). 저장 버튼이 있는 폼에서는 `.checkbox`.

```html
<label class="switch"><input type="checkbox" checked>참석자에게 일정 공개</label>
<label class="switch"><input type="checkbox">외부 링크 공유 허용</label>
<label class="switch"><input type="checkbox" disabled>SSO 로그인 강제 (관리자 전용)</label>

<!-- 설정 행: 왼쪽 라벨·설명, 오른쪽 스위치 -->
<div class="field field-inline">
  <div>
    <div class="field-label">주간 요약 메일</div>
    <p class="field-help">매주 월요일 오전 8시에 이번 주 일정을 보냅니다.</p>
  </div>
  <label class="switch"><input type="checkbox" checked><span class="sr-only">주간 요약 메일</span></label>
</div>
```

주의: 스위치 옆 텍스트가 없으면 `.sr-only` 라벨을 넣는다.

## segmented (배타 선택 탭형 컨트롤)
언제: 2~5개 보기/필터 전환(전체·확정·후보, 주·월). 페이지 이동은 `.tabs`(40-display.md).

```html
<div class="segmented">
  <button class="segmented-item active">전체</button>
  <button class="segmented-item">확정</button>
  <button class="segmented-item">후보</button>
</div>

<div class="segmented segmented-sm">
  <button class="segmented-item active">주</button>
  <button class="segmented-item">월</button>
</div>

<div class="segmented w-full">
  <button class="segmented-item"><svg class="icon-sm" aria-hidden="true"><use href="#i-list"/></svg>목록</button>
  <button class="segmented-item active"><svg class="icon-sm" aria-hidden="true"><use href="#i-calendar"/></svg>달력</button>
  <button class="segmented-item"><svg class="icon-sm" aria-hidden="true"><use href="#i-kanban"/></svg>보드</button>
</div>
```

주의: `.active`는 정확히 1개. 항목 텍스트는 2~5자.

## form-grid · form-actions (2열 폼)
언제: 필드가 4개 이상인 생성·수정 폼. 긴 필드는 `.span-2`.

```html
<form class="form-grid">
  <div class="field span-2">
    <label class="field-label" for="s-title">세션 제목 <span class="req">*</span></label>
    <input class="input" id="s-title" type="text" placeholder="예: 워크숍 A · 고객 여정 그리기">
  </div>
  <div class="field">
    <label class="field-label" for="s-date">날짜 <span class="req">*</span></label>
    <input class="input" id="s-date" type="date" value="2026-09-12">
  </div>
  <div class="field">
    <label class="field-label" for="s-time">시작 시각</label>
    <input class="input" id="s-time" type="time" value="10:30">
  </div>
  <div class="field">
    <label class="field-label" for="s-room">장소</label>
    <div class="select-wrap">
      <select class="select" id="s-room"><option>대회의실 A</option><option>세미나실 3</option></select>
      <svg class="icon" aria-hidden="true"><use href="#i-chevron-down"/></svg>
    </div>
  </div>
  <div class="field">
    <label class="field-label" for="s-cap">정원</label>
    <div class="input-group"><input class="input" id="s-cap" type="number" value="30"><span class="input-addon">명</span></div>
  </div>
  <div class="field span-2">
    <label class="field-label" for="s-desc">설명</label>
    <textarea class="textarea" id="s-desc" rows="3" placeholder="세션 목적과 진행 방식"></textarea>
  </div>
</form>
<div class="form-actions">
  <button class="btn btn-ghost">취소</button>
  <button class="btn btn-primary">세션 저장</button>
</div>
```

변형 — 하단 고정 액션(긴 폼): `<div class="form-actions sticky">…</div>`.

주의: 관련 필드(날짜·시각, 장소·정원)를 같은 줄에. `.form-actions`는 폼당 1개, primary 1개.
