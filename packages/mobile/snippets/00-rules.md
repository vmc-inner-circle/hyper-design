# 모바일 화면 조각 규칙 — web 규칙(packages/web/snippets/00-rules.md)과 **다른 것만**

모바일(`screens.json`의 `platform: "mobile"`)은 web 위에 겹쳐 쓴다. 부품 태그·영역(data-region)·버튼 규칙(data-trigger·data-back·data-stay)·문구 규칙은 web과 같다. 아래만 다르다.

## 반드시 지킬 것

1. **프레임은 390×844, 한 열.** 화면 폭 전체를 한 줄로 쌓는다. 회색 바탕 위에 흰 판(카드·묶음)을 12px 간격으로 쌓고, 판 안쪽은 넉넉하게(20px). 여러 열 배치(`.split`·`.grid-3`·`.grid-4`·`.form-grid` 2열)는 쓰지 않는다 — 나란히 둘 것은 숫자 두 개(`.grid-2`)까지만.
2. **셸은 쓰지 않는다(web과 같음) — 모양은 expand.js가 정한다.** 메뉴에 있는 화면(roles[].nav)은 **아래 탭**, 그 밖의 화면은 **위 제목 줄**(왼쪽 뒤로 · 가운데 화면 이름), 온보딩은 메뉴 없는 한 장. 작성자는 `<main class="content">…</main>`만 쓴다. 위 제목 줄이 화면 이름을 이미 보여 주므로 본문에서 화면 이름을 다시 쓰지 않는다.
3. **화면 첫머리 = 머리줄 + 큰 제목 + 회색 한 줄.** `<x-page-header eyebrow="다음 수업 · 10월 13일(화)" title="오늘 20:00 리포머 중급" desc="숨결필라테스 망원 · 오지훈 강사">`. 탭 화면은 제목 = 탭 이름("내 예약")이어도 되고, 아래 화면은 제목 = 다루는 대상(수업 이름·가게 이름).
4. **묶음(`<x-section>`) 하나 = 흰 판 하나.** 제목("취소 규정")이 판 안 위쪽에 들어간다. 묶음 안에는 `<x-card>`를 또 넣지 말고 목록(`<x-list>`)·줄(`.row-between`)·문장을 바로 넣는다. 묶음 없이 판 하나만 필요하면 `<x-card>`.
5. **주 행동은 아래 꽉 찬 버튼 하나.** 본문 **맨 마지막**에 `<div class="bottom-cta" data-region="…"><x-btn variant="primary" data-trigger="…">예약 확정</x-btn></div>`. 화면을 내려도 아래에 붙어 있다. 버튼 줄(`.form-actions`)·머리줄 오른쪽 primary 버튼 대신 이것을 쓴다. 보조 버튼이 꼭 필요하면 같은 칸 안에 primary 아래에 secondary 하나.
6. **뜨는 창은 아래에서 올라오는 창**이다. 쓰는 법은 web과 같다(`<x-modal title="…" desc="…">본문 <div class="modal-footer">버튼</div></x-modal>`) — expand.js가 아래 창으로 펼친다. 바닥줄 버튼은 위아래로 꽉 차게 놓이고 primary가 맨 위로 간다. 돌아가는 버튼(`data-back`, "돌아가기"·"취소")을 바닥줄에 하나 넣는다(있으면 X 닫기가 빠진다). 제목은 질문이나 결과 한 문장("방금 마감됐어요. 대기할까요?"), desc는 회색 1~2줄.
7. **규정·조건은 그 화면 안에 판으로 보여 준다**(따로 창·링크로 숨기지 않는다). `<x-section title="취소 규정"><x-list plain><x-item icon="calendar-days" tone="primary" title="10월 19일(월) 20:00까지 무료 취소" sub="이후 취소하면 1회 차감돼요"/></x-list></x-section>` — 굵은 날짜·조건 한 줄 + 회색 설명.
8. **중요한 숫자는 크게, 주 색으로.** `<p class="big-num">잔여 3회 <small>/ 10</small></p>` 아래에 회색 한 줄(`<p class="text-sm text-2">지금 예약 가능 3회</p>`).
9. **상태는 작은 연한 알약 배지**(`<x-badge tone="success">예약함</x-badge>`, "확정 필요"=warning, "마감 임박"=danger). 목록 한 줄에서는 제목 위나 제목 옆.
10. **고르기**: 몇 개 중 하나 = `.segmented.w-full`(예정 2 · 대기 중 2 · 지난 수업), 여러 조건 = `.chip-group`(한 줄로 가로로 밀린다). 고른 것은 주 색 테두리 + 연한 주 색으로 보인다.
11. **쓰지 않는 것**: `.split`(목록과 자세히는 화면 두 장으로) · `.table`(목록 `<x-list>`로) · `.week-grid`(날짜 띠 `.day-strip` + 그날 목록) · `.sidebar`·`.topnav`(셸) · 가운데 뜨는 창·오른쪽 서랍(아래 창으로) · `.form-actions`(아래 꽉 찬 버튼으로) · `.grid-3`·`.grid-4`.
12. 목록 한 줄은 `<x-item>`: 제목(굵게) + 회색 부제(줄바꿈 됨) + 오른쪽 `<x-icon name="chevron-right" size="sm"/>`를 안쪽에 넣으면 눌러서 들어가는 줄이 된다.
13. 화면당 primary 버튼은 1개 — 아래 꽉 찬 버튼이 그것이다. 판 안의 버튼은 secondary·soft·ghost.
14. **안내·오류 문구(`.toast`)는 위 제목 줄 바로 아래, 양옆 꽉 차게, 본문 크기 글자** — 아래 꽉 찬 버튼·탭에 가려지지 않게(web 17-2와 같은 기본 규칙). 조각에서 자리를 바꾸지 않는다.

## 조각 목록 (모바일에서 더 읽을 것)

| 파일 | 내용 |
|---|---|
| **05-parts.md** | 모바일에서 달라지는 부품(x-page-header eyebrow · x-modal = 아래 창) |
| 10-layout.md | 셸 모양(아래 탭 · 위 제목 줄 · 위 알약 탭) · 머리줄+제목 · 판 쌓기 · 아래 꽉 찬 버튼 · 아래 창 HTML |
| patterns/*.html | 패턴별 `<main>` 골격 (dashboard = 홈 피드, list-detail = 목록 / 자세히 두 장, form, onboarding, timeline, settings, board = 날짜 띠 + 목록) |
