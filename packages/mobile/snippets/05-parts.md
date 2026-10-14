# 05 · 모바일에서 달라지는 부품

부품 태그는 web과 같다(packages/web/snippets/05-parts.md). 모바일에서 달라지는 것만 적는다.

## 부품

| 부품 | 속성 | 펼치면 |
|---|---|---|
| `<x-page-header eyebrow="다음 수업 · 10월 13일(화)" title="오늘 20:00 리포머 중급" desc="숨결필라테스 망원 · 오지훈 강사"></x-page-header>` | **eyebrow**(제목 위 작은 회색 한 줄) · title · desc · 안쪽 = 버튼(제목 아래 꽉 차게) | `.page-header` 안 `<p class="eyebrow">` + `.page-title` + `.page-desc` |
| `<x-modal title="방금 마감됐어요. 대기할까요?" desc="지금 대기 0명이라 1번째로 기다려요.">본문(없어도 됨) <div class="modal-footer"><x-btn variant="primary" data-trigger="…">대기 신청</x-btn><x-btn data-back>돌아가기</x-btn></div></x-modal>` | title · desc · center (size는 무시) | **아래에서 올라오는 창** `.modal-backdrop.sheet-backdrop > .modal.sheet` — 손잡이 · 제목 · 회색 설명 · 본문 · 버튼 위아래로 꽉 차게(primary 맨 위). 바닥줄에 `data-back` 버튼이 있으면 X 닫기는 붙지 않는다 |

## 부품이 없는 모바일 조각 (HTML 그대로)

| 쓰는 곳 | HTML |
|---|---|
| 아래 꽉 찬 버튼 (본문 맨 마지막) | `<div class="bottom-cta" data-region="book"><x-btn variant="primary" data-trigger="book">예약 확정</x-btn></div>` · 안내 한 줄은 버튼 아래 `<p class="text-sm">10월 19일까지 무료 취소</p>` |
| 크게 보여 줄 숫자 | `<p class="big-num">잔여 3회 <small>/ 10</small></p>` |
| 제목 위 작은 회색 줄 (부품 밖에서) | `<p class="eyebrow">기구 필라테스 · 망원1동</p>` |

## 예 — 아래 화면(수업 자세히)

```html
<main class="content">
  <x-page-header eyebrow="숨결필라테스 망원 · 기구 필라테스 · 중급" title="리포머 중급" desc="10월 20일(화) 20:00~20:50 · 50분" data-region="class-info"></x-page-header>
  <x-card data-region="seats"><x-badge tone="danger">마감 임박</x-badge><p class="fw-semibold">잔여 2석</p><p class="text-sm text-2">정원 6명 · 대기 0명</p></x-card>
  <x-section title="취소 규정" data-region="policy">
    <x-list plain><x-item icon="calendar-days" tone="primary" title="10월 19일(월) 20:00까지 무료 취소" sub="이후 취소하면 1회 차감돼요"/></x-list>
  </x-section>
  <div class="bottom-cta" data-region="book"><x-btn variant="primary" data-trigger="book">예약하기</x-btn></div>
</main>
```
(예시 값은 형식 설명용 — 실제 문구는 DOMAIN 값을 쓴다)
