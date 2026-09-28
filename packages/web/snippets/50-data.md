# 50 · 데이터 (list · table · timeline · steps · calendar · day-strip)

공통: 목록·표는 **최소 3~5행**을 실제 문구로 채운다. 상태는 `.badge`, 숫자 열은 `.num`.

## list — 행 목록 (아이콘 · 제목/부제 · 메타 · 액션)
언제: 요청·문서·사람·알림처럼 "행 하나 = 항목 하나"인 목록. 좌측 목록 패널, 카드 안 최근 활동.

```html
<!-- 기본: 카드 안에 구분선 목록 -->
<div class="card">
  <div class="card-header"><h3 class="card-title">최근 요청</h3><button class="btn btn-ghost btn-sm">전체</button></div>
  <ul class="list list-divided">
    <li class="list-item">
      <span class="list-icon"><svg class="icon" aria-hidden="true"><use href="#i-file-text"/></svg></span>
      <div class="list-main">
        <span class="list-title">출장 경비 정산 <span class="badge badge-warning">검토 중</span></span>
        <span class="list-sub">김민수 · 영업1팀 · 342,000원</span>
      </div>
      <span class="list-meta">2시간 전</span>
      <div class="list-actions"><button class="btn btn-icon btn-ghost btn-sm" aria-label="더보기"><svg class="icon-sm" aria-hidden="true"><use href="#i-ellipsis"/></svg></button></div>
    </li>
    <li class="list-item">
      <span class="list-icon is-success"><svg class="icon" aria-hidden="true"><use href="#i-circle-check"/></svg></span>
      <div class="list-main"><span class="list-title">연차 신청 10/2~10/3</span><span class="list-sub">이서연 · 디자인팀</span></div>
      <span class="list-meta">어제</span>
    </li>
    <li class="list-item is-muted">
      <span class="list-icon"><svg class="icon" aria-hidden="true"><use href="#i-archive"/></svg></span>
      <div class="list-main"><span class="list-title">장비 반납 확인</span><span class="list-sub">보관 처리됨</span></div>
      <span class="list-meta">9월 12일</span>
    </li>
  </ul>
</div>

<!-- 선택 가능한 목록 (좌측 패널): a 요소 + active -->
<nav class="list">
  <a class="list-item active" href="#">
    <span class="avatar avatar-sm">김민</span>
    <div class="list-main"><span class="list-title">김민수</span><span class="list-sub">계약서 초안 확인 부탁드립니다</span></div>
    <span class="list-meta">09:12</span>
  </a>
  <a class="list-item" href="#">
    <span class="avatar avatar-sm avatar-success">이서</span>
    <div class="list-main"><span class="list-title">이서연</span><span class="list-sub">회의록 공유합니다</span></div>
    <span class="list-meta">어제 <span class="badge badge-primary">2</span></span>
  </a>
  <a class="list-item" href="#">
    <span class="avatar avatar-sm avatar-warning">박준</span>
    <div class="list-main"><span class="list-title">박준호</span><span class="list-sub">다음 주 일정 조율</span></div>
    <span class="list-meta">9/24</span>
  </a>
</nav>

<!-- 아이콘 색 변형 · 그룹 제목 · 좁은 목록 -->
<ul class="list list-compact">
  <li class="list-group-title">오늘</li>
  <li class="list-item"><span class="list-icon is-primary"><svg class="icon-sm" aria-hidden="true"><use href="#i-bell"/></svg></span><div class="list-main"><span class="list-title">승인 요청이 도착했습니다</span></div><span class="list-meta">10:40</span></li>
  <li class="list-item"><span class="list-icon is-warning"><svg class="icon-sm" aria-hidden="true"><use href="#i-clock"/></svg></span><div class="list-main"><span class="list-title">마감 1일 전: 분기 보고</span></div><span class="list-meta">09:00</span></li>
  <li class="list-group-title">어제</li>
  <li class="list-item"><span class="list-icon is-danger"><svg class="icon-sm" aria-hidden="true"><use href="#i-circle-alert"/></svg></span><div class="list-main"><span class="list-title">결제 실패 1건</span></div><span class="list-meta">18:22</span></li>
</ul>
```
주의: `list-icon` 대신 `avatar`를 넣어도 된다. `active`는 한 목록에 하나. 체크박스는 `list-icon` 자리에 `.checkbox`. 목록이 `<nav class="list">` + `<a class="list-item">` 형태(list-detail 좌측)면 그룹 제목은 `<li>`가 아니라 `<div class="list-group-title">날짜</div>`로 넣는다(같은 스타일).

## table — 표
언제: 열이 3개 이상이고 비교·정렬이 중요한 데이터. `.table-wrap`으로 감싸야 둥근 모서리·가로 스크롤이 생긴다.

```html
<div class="table-wrap">
  <table class="table">
    <thead>
      <tr>
        <th class="col-check"><input class="checkbox" type="checkbox" aria-label="전체 선택"></th>
        <th>요청명</th>
        <th>담당자</th>
        <th>상태</th>
        <th class="num">금액</th>
        <th>마감 <svg class="icon-sm" aria-hidden="true"><use href="#i-arrow-up-down"/></svg></th>
        <th class="col-actions"></th>
      </tr>
    </thead>
    <tbody>
      <tr class="is-selected">
        <td class="col-check"><input class="checkbox" type="checkbox" checked aria-label="선택"></td>
        <td class="fw-semibold">사무용품 구매</td>
        <td><div class="row gap-2"><span class="avatar avatar-sm">김민</span>김민수</div></td>
        <td><span class="badge badge-warning">검토 중</span></td>
        <td class="num">128,000</td>
        <td>2026-10-02</td>
        <td class="col-actions"><button class="btn btn-icon btn-ghost btn-sm" aria-label="더보기"><svg class="icon-sm" aria-hidden="true"><use href="#i-ellipsis"/></svg></button></td>
      </tr>
      <tr>
        <td class="col-check"><input class="checkbox" type="checkbox" aria-label="선택"></td>
        <td class="fw-semibold">외부 교육 참가비</td>
        <td><div class="row gap-2"><span class="avatar avatar-sm avatar-success">이서</span>이서연</div></td>
        <td><span class="badge badge-success">승인</span></td>
        <td class="num">450,000</td>
        <td>2026-09-30</td>
        <td class="col-actions"><button class="btn btn-icon btn-ghost btn-sm" aria-label="더보기"><svg class="icon-sm" aria-hidden="true"><use href="#i-ellipsis"/></svg></button></td>
      </tr>
      <tr>
        <td class="col-check"><input class="checkbox" type="checkbox" aria-label="선택"></td>
        <td class="fw-semibold">서버 임대료 9월</td>
        <td><div class="row gap-2"><span class="avatar avatar-sm avatar-warning">박준</span>박준호</div></td>
        <td><span class="badge badge-danger">반려</span></td>
        <td class="num">1,320,000</td>
        <td>2026-09-28</td>
        <td class="col-actions"><button class="btn btn-icon btn-ghost btn-sm" aria-label="더보기"><svg class="icon-sm" aria-hidden="true"><use href="#i-ellipsis"/></svg></button></td>
      </tr>
      <tr class="is-muted">
        <td class="col-check"><input class="checkbox" type="checkbox" aria-label="선택"></td>
        <td>회식비 8월</td>
        <td>정우진</td>
        <td><span class="badge badge-neutral">보관</span></td>
        <td class="num">86,500</td>
        <td>2026-08-29</td>
        <td class="col-actions"></td>
      </tr>
    </tbody>
  </table>
  <div class="table-foot"><span>총 42건 중 1–4</span><div class="btn-group"><button class="btn btn-secondary btn-sm">이전</button><button class="btn btn-secondary btn-sm">다음</button></div></div>
</div>

<!-- 변형: 좁은 행 · 줄무늬 · 카드 안에 붙이기 -->
<div class="table-wrap"><table class="table table-compact table-striped">…</table></div>
<div class="card"><div class="card-header"><h3 class="card-title">인원 현황</h3></div><div class="table-wrap"><table class="table">…</table></div></div>
```
주의: 숫자 열은 th·td 모두 `num`. 선택된 행은 `tr.is-selected`. 4열 이하이고 행마다 부제가 있으면 `.list`가 낫다.

## timeline — 날짜별 세로 타임라인
언제: 활동 이력, 일정표(시간 순), 변경 기록. 날짜 헤더(`timeline-date`)로 묶고 그 아래 항목을 쌓는다.

```html
<div class="timeline">
  <div class="timeline-date">9월 27일 (토) · 오늘</div>
  <div class="timeline-item">
    <span class="timeline-time">09:30</span>
    <span class="timeline-dot dot-success"></span>
    <div class="timeline-content">
      <div class="timeline-title">주간 계획 회의 <span class="badge badge-success">완료</span></div>
      <p class="timeline-desc">3층 회의실 B · 참석 6명</p>
    </div>
  </div>
  <div class="timeline-item">
    <span class="timeline-time">11:00</span>
    <span class="timeline-dot"></span>
    <div class="timeline-content">
      <div class="timeline-title">고객사 제안서 검토 <span class="badge badge-primary">진행 중</span></div>
      <p class="timeline-desc">담당: 김민수 · 마감 14:00</p>
    </div>
  </div>
  <div class="timeline-item">
    <span class="timeline-time">15:00</span>
    <span class="timeline-dot dot-warning"></span>
    <div class="timeline-content">
      <div class="timeline-title">배포 점검 <span class="badge badge-warning">지연 가능</span></div>
      <p class="timeline-desc">QA 결과 대기 중</p>
    </div>
  </div>
  <div class="timeline-date">9월 28일 (일)</div>
  <div class="timeline-item">
    <span class="timeline-time">종일</span>
    <span class="timeline-dot dot-neutral"></span>
    <div class="timeline-content"><div class="timeline-title">휴무</div></div>
  </div>
</div>

<!-- 항목 안에 카드 (상세가 긴 경우) -->
<div class="timeline-item">
  <span class="timeline-time">14:20</span>
  <span class="timeline-dot dot-info"></span>
  <div class="timeline-content">
    <div class="timeline-title">이서연 님이 댓글을 남겼습니다</div>
    <div class="card card-compact"><div class="card-body">첨부한 견적서 2안으로 진행하면 좋겠습니다.</div></div>
  </div>
</div>

<!-- 시간 열 없는 간단 이력 -->
<div class="timeline timeline-compact">
  <div class="timeline-item"><span class="timeline-dot dot-success"></span><div class="timeline-content"><div class="timeline-title">승인됨</div><p class="timeline-desc">박준호 · 9/26 17:02</p></div></div>
  <div class="timeline-item"><span class="timeline-dot"></span><div class="timeline-content"><div class="timeline-title">검토 요청</div><p class="timeline-desc">김민수 · 9/26 10:15</p></div></div>
  <div class="timeline-item"><span class="timeline-dot dot-neutral"></span><div class="timeline-content"><div class="timeline-title">작성됨</div><p class="timeline-desc">김민수 · 9/25 16:40</p></div></div>
</div>
```
주의: 점 색 = 상태 (`dot-success` 완료 · 기본 진행 · `dot-warning` 주의 · `dot-danger` 실패 · `dot-neutral` 예정/취소 · `dot-info` 정보). 배지 색과 맞춘다.

## steps — 단계 진행 표시
언제: 온보딩·다단계 폼·승인 흐름의 "지금 몇 단계인지". 번호는 자동(비워 두면 카운터).

```html
<ol class="steps">
  <li class="step done"><span class="step-num"><svg class="icon-sm" aria-hidden="true"><use href="#i-check"/></svg></span><span class="step-label">계정 정보</span></li>
  <li class="step done"><span class="step-num"><svg class="icon-sm" aria-hidden="true"><use href="#i-check"/></svg></span><span class="step-label">조직 설정</span></li>
  <li class="step current"><span class="step-num"></span><span class="step-label">팀원 초대</span><span class="step-desc">선택 사항</span></li>
  <li class="step"><span class="step-num"></span><span class="step-label">완료</span></li>
</ol>

<!-- 세로 (사이드 진행) -->
<ol class="steps steps-vertical">
  <li class="step done"><span class="step-num"><svg class="icon-sm" aria-hidden="true"><use href="#i-check"/></svg></span><div class="step-body"><span class="step-label">신청 접수</span><span class="step-desc">9/25 10:12</span></div></li>
  <li class="step current"><span class="step-num"></span><div class="step-body"><span class="step-label">담당자 검토</span><span class="step-desc">평균 1영업일</span></div></li>
  <li class="step"><span class="step-num"></span><div class="step-body"><span class="step-label">최종 승인</span></div></li>
</ol>
```
주의: `current`는 하나. 완료 단계는 번호 대신 check 아이콘.

## calendar — 월 달력 (7열)
언제: 날짜 선택, 일정 밀도 보기. 작은 달력은 점(`has-event`), 큰 달력(`calendar-month`)은 칸 안에 일정 칩.

```html
<!-- 작은 달력 (사이드 패널 · 날짜 선택) -->
<div class="calendar">
  <div class="calendar-header">
    <span class="calendar-title">2026년 9월</span>
    <div class="calendar-nav">
      <button class="btn btn-icon btn-ghost btn-sm" aria-label="이전 달"><svg class="icon-sm" aria-hidden="true"><use href="#i-chevron-left"/></svg></button>
      <button class="btn btn-icon btn-ghost btn-sm" aria-label="다음 달"><svg class="icon-sm" aria-hidden="true"><use href="#i-chevron-right"/></svg></button>
    </div>
  </div>
  <div class="calendar-grid">
    <span class="calendar-weekday">일</span><span class="calendar-weekday">월</span><span class="calendar-weekday">화</span><span class="calendar-weekday">수</span><span class="calendar-weekday">목</span><span class="calendar-weekday">금</span><span class="calendar-weekday">토</span>
    <button class="calendar-day is-other-month">30</button><button class="calendar-day is-other-month">31</button>
    <button class="calendar-day">1</button><button class="calendar-day">2</button><button class="calendar-day has-event">3</button><button class="calendar-day">4</button><button class="calendar-day">5</button>
    <button class="calendar-day">6</button><button class="calendar-day">7</button><button class="calendar-day has-event">8</button><button class="calendar-day">9</button><button class="calendar-day">10</button><button class="calendar-day">11</button><button class="calendar-day">12</button>
    <button class="calendar-day">13</button><button class="calendar-day">14</button><button class="calendar-day">15</button><button class="calendar-day has-event">16</button><button class="calendar-day">17</button><button class="calendar-day">18</button><button class="calendar-day">19</button>
    <button class="calendar-day">20</button><button class="calendar-day">21</button><button class="calendar-day">22</button><button class="calendar-day">23</button><button class="calendar-day has-event">24</button><button class="calendar-day">25</button><button class="calendar-day">26</button>
    <button class="calendar-day today">27</button><button class="calendar-day selected has-event">28</button><button class="calendar-day">29</button><button class="calendar-day">30</button>
    <button class="calendar-day is-other-month">1</button><button class="calendar-day is-other-month">2</button><button class="calendar-day is-other-month">3</button>
  </div>
</div>

<!-- 큰 월 보기: 각 칸 = daynum + 일정 칩 (한 주만 예시, 실제로는 5~6주 채움) -->
<div class="calendar calendar-month">
  <div class="calendar-header"><span class="calendar-title">2026년 9월</span><div class="calendar-nav"><button class="btn btn-secondary btn-sm">오늘</button></div></div>
  <div class="calendar-grid">
    <span class="calendar-weekday">일</span><span class="calendar-weekday">월</span><span class="calendar-weekday">화</span><span class="calendar-weekday">수</span><span class="calendar-weekday">목</span><span class="calendar-weekday">금</span><span class="calendar-weekday">토</span>
    <div class="calendar-day today"><span class="calendar-daynum">27</span><span class="calendar-event">10:00 주간 회의</span><span class="calendar-event is-success">배포 완료</span></div>
    <div class="calendar-day selected"><span class="calendar-daynum">28</span><span class="calendar-event is-warning">보고서 마감</span></div>
    <div class="calendar-day"><span class="calendar-daynum">29</span></div>
    <div class="calendar-day"><span class="calendar-daynum">30</span><span class="calendar-event is-neutral">휴가 · 이서연</span><span class="calendar-more">+2</span></div>
    <div class="calendar-day is-other-month"><span class="calendar-daynum">1</span></div>
    <div class="calendar-day is-other-month"><span class="calendar-daynum">2</span></div>
    <div class="calendar-day is-other-month"><span class="calendar-daynum">3</span></div>
  </div>
</div>
```
주의: 요일 7개 + 날짜 칸은 7의 배수. `today`와 `selected`는 각각 하나. 이전/다음 달 칸은 `is-other-month`.

## day-strip — 가로 날짜 칩 (요일/날짜 2줄)
언제: 주 단위 일정에서 날짜를 고르는 상단 띠. 좌우로 7~14개.

```html
<div class="day-strip">
  <button class="day"><span class="day-name">월</span><span class="day-num">22</span></button>
  <button class="day"><span class="day-name">화</span><span class="day-num">23</span><span class="day-dot"></span></button>
  <button class="day"><span class="day-name">수</span><span class="day-num">24</span></button>
  <button class="day"><span class="day-name">목</span><span class="day-num">25</span><span class="day-dot"></span></button>
  <button class="day today"><span class="day-name">금</span><span class="day-num">26</span></button>
  <button class="day active"><span class="day-name">토</span><span class="day-num">27</span><span class="day-dot"></span></button>
  <button class="day is-muted"><span class="day-name">일</span><span class="day-num">28</span></button>
</div>
<!-- 폭을 꽉 채우는 7일 -->
<div class="day-strip day-strip-wide">…day×7…</div>
```
주의: `active`(선택)와 `today`는 다르다. 일정 있는 날은 `day-dot`.
