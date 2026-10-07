# 05 · 짧은 부품 태그 (먼저 읽는다 — 화면을 빨리 쓰는 방법)

화면 조각은 **짧은 부품 태그**로 쓴다. 쓰고 나면 메인이 `node scripts/expand.js runs/<p>`로 라이브러리와 똑같은 HTML로 펼쳐 파일에 다시 쓴다(이후 lint·보드·수정은 펼친 HTML을 본다). 일반 HTML과 섞어 써도 된다 — 부품이 없는 구조(grid·row·stack·chip·table·calendar·week-grid·form 입력칸)는 해당 조각의 HTML을 그대로 쓴다.

## 셸(상단바·메뉴)은 쓰지 않는다

파일은 **`<main class="content">…</main>` 하나**다. 상단바·메뉴·현재 위치(.active)·사용자 표시는 expand.js가 `screens.json`의 `roles[].nav`와 시안의 메뉴 구조(sidebar·top·rail)로 붙인다 — 화면마다 메뉴가 어긋날 일이 없다. 뜨는 창 화면은 `<x-modal>` 하나(뒷 화면은 build가 깐다).

## 부품

모든 부품은 `data-region` · `data-trigger` · `data-back` · `data-stay="…"` · `aria-label` · `id` · `title` · `class`를 받아 펼친 바깥 태그에 그대로 옮긴다.

| 부품 | 속성 | 펼치면 |
|---|---|---|
| `<x-btn variant="primary" size="sm" icon="plus">추가하기</x-btn>` | variant: primary·secondary(기본)·ghost·soft·danger · size: sm·lg · icon · icon-end · href(있으면 `<a>`) | `.btn …` 버튼. 글자 없이 icon만 주면 `.btn-icon`(aria-label 필수) |
| `<x-badge tone="success" icon="circle-check">확정</x-badge>` | tone: neutral(기본)·primary·success·warning·danger·info · icon | `.badge` |
| `<x-icon name="bell" size="sm" tone="muted"/>` | name(allowlist) · size: sm·lg · tone: muted·success·warning·danger·primary | `<svg class="icon…"><use href="#i-…"/></svg>` |
| `<x-avatar size="sm" tone="success">김민</x-avatar>` | size: sm·lg · tone | `.avatar` |
| `<x-list compact>…<x-item …/>…</x-list>` | compact · plain(구분선 없이) | `<ul class="list list-divided">` |
| `<x-item icon="clock" tone="warning" title="…" sub="…" meta="어제" badge="확정" badge-tone="success">버튼들</x-item>` | icon 또는 avatar="김민"(+avatar-tone) · tone(아이콘 원 색) · small(작은 아이콘) · title · sub · meta · badge · badge-tone · muted · selected · 안쪽 = 오른쪽 버튼 | 목록 한 줄 `.list-item` |
| `<x-stat label="이번 달 처리 건수" value="128" unit="건" delta="지난달보다 12건 늘었어요" dir="up"/>` | label · value · unit · delta · dir: up·down | `.stat` |
| `<x-empty icon="inbox" title="아직 ○○이 없어요" desc="…">버튼</x-empty>` | icon · title · desc · size: sm · 안쪽 = 버튼 | `.empty` |
| `<x-card title="이번 주" action="전체 보기" action-trigger="…">안쪽</x-card>` | title · action(머리줄 오른쪽 글자 버튼 — action-trigger="<key>" 또는 action-stay="안내 문구" 또는 action-back. 제목 없이 action만 줘도 된다) · flush(본문 여백 없이 — 목록을 바로 넣을 때) · selected · clickable | `.card` + `.card-header` + `.card-body` |
| `<x-section title="오늘 일정" icon="calendar-days" desc="…" action="전체 보기" action-trigger="…" data-region="today">안쪽</x-section>` | title · icon · desc · action(제목 옆 글자 링크 — action-trigger / action-stay / action-back) | `<section class="section">` |
| `<x-page-header title="회의실 예약" desc="…">오른쪽 버튼들</x-page-header>` | title · desc · 안쪽 = 오른쪽 버튼 | `.page-header` |
| `<x-modal title="예약 확인" desc="…" size="sm">본문 … <div class="modal-footer">버튼들</div></x-modal>` | title · desc · size: sm·lg · center | `.modal-backdrop > .modal` + 머리줄(닫기 = data-back) + 본문 + 바닥줄 |

- 부품 안에 부품을 넣어도 된다(`<x-card flush><x-list><x-item …><x-btn …>예약하기</x-btn></x-item></x-list></x-card>`).
- **모르는 속성은 쓰지 않는다** — expand.js가 경고를 낸다(조용히 사라지거나 엉뚱하게 붙는 것을 막으려고).
- 속성 값에 큰따옴표가 필요하면 작은따옴표로 감싼다. 속성 값에는 태그를 넣지 않는다(굵게 등은 안쪽 HTML로).
- 목록 행마다 같은 버튼은 첫 행에만 `data-trigger`, 나머지는 글자만 똑같이(00-rules 3-2).

## 예 — 이 정도 길이면 된다

```html
<main class="content">
  <x-page-header title="회의실 예약" desc="이번 주 9월 8일(월) – 12일(금)"></x-page-header>
  <x-section title="비어 있는 회의실" data-region="room-list">
    <x-card flush><x-list>
      <x-item icon="calendar-check" tone="success" title="9월 9일(화) 10:00 · 3층 회의실 A" sub="최대 8명" badge="비어 있음" badge-tone="success"><x-btn variant="primary" size="sm" data-trigger="book-room">예약하기</x-btn></x-item>
      <x-item icon="calendar-check" tone="success" title="9월 9일(화) 14:00 · 2층 회의실 B" sub="최대 4명" badge="비어 있음" badge-tone="success"><x-btn size="sm">예약하기</x-btn></x-item>
    </x-list></x-card>
  </x-section>
</main>
```
(예시 값은 형식 설명용 — 실제 문구는 DOMAIN 값을 쓴다)
