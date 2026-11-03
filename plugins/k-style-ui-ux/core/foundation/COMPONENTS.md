# 부품 요약 — 화면 파일은 이 클래스만 조합한다

인라인 `style`·임의 색/크기 금지(예외 하나: `.range`의 `style="--from:…;--to:…"` — 아래 "공통 부품"). 색·글자·여백은 전부 `tokens.css`(팔레트에서 생성) 변수. 모범 답안: `foundation/examples/*.html`(구조만 참고, 내용 베끼지 말 것).

## 화면 파일 뼈대 (out/screens/<id>.html)

```html
<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=375, initial-scale=1">
<title>화면 제목</title>
<link id="tokens" rel="stylesheet" href="../tokens.css"><link rel="stylesheet" href="../components.css"><script src="../palette.js"></script>
</head>
<body class="…">   <!-- text-large(같이 짜지 않는 사람 화면) · has-tab(탭바) · has-cta(하단 고정 버튼) · plain(폼·상세: 흰 바탕 한 장) -->
…
</body></html>
```

## 골격
- **첫 화면 주인공 표시**: `archetype`이 있는 화면은 `references/screen-kinds.md`의 그 유형 주인공 요소에 `data-anchor`를 단다(여러 덩어리면 각각). audit가 렌더링해서 그 요소가 스크롤 전 첫 화면에서 다른 덩어리보다 큰지 잰다.
- 큰 머리글(홈·목록 첫 화면 — **대표 콘텐츠형·피드형 홈은 쓰지 않는다**, 주인공이 맨 위. 그 홈의 `h1`은 앱바 가운데 서비스 이름 `<header class="appbar"><span></span><h1 class="appbar-title">서비스 이름</h1><span></span></header>`): `<header class="hero"><p class="eyebrow">…</p><h1 class="title">…</h1><p class="lead">…</p></header>` · 이동 링크는 `<a class="hero-more">…›</a>`
- 앱바(들어간 화면): `<header class="appbar"><a class="appbar-btn" href="…" aria-label="뒤로">(선 아이콘)</a><h1 class="appbar-title">…</h1><span></span></header>`
- 본문: `<main class="page">` 안에 `<section class="block">`(흰 블록) / `<section class="block is-list">`(목록 블록). 블록 제목 `<div class="block-head"><h2 class="h2">…</h2><a class="block-link">…</a></div>`
- `h1`은 화면당 정확히 1개.

## 목록 행
```html
<a class="row" href="…"><span class="row-art"><img src="../assets/fluent/luggage.svg" alt=""></span>
  <div class="row-main"><span class="badge is-brand">확정</span><p class="row-title">…</p><p class="row-sub">…</p></div>
  <span class="row-trail">(› 선 아이콘)</span></a>
```
- 왼쪽: 사물 `row-art`(컬러 일러스트) · 사람 `avatar` · 시간/날짜 `row-date` · 누르는 추가 행은 `class="row is-add"` + `row-lead`(선 + 아이콘)
- 행의 행동 버튼(`row-trail` 안 `btn small`)은 글 아래 줄에 글 칸 너비로 자동 배치된다(가운데 글자). 문구는 **명사형 짝**("리뷰 작성" → 한 뒤 "리뷰 완료", "대기 신청" → "신청 완료") — 하단 고정 버튼의 "~하기"와 다르다. 기한은 덧붙여도 된다("리뷰 작성 · 10/23까지").
- **한 번뿐인 행동을 이미 했으면 같은 자리에 비활성 버튼으로 결과를 적는다**: `<span class="btn small is-done" aria-disabled="true">리뷰 완료</span>` — 글자만 남기거나 버튼을 없애지 않는다(목록에서 했는지/안 했는지가 같은 모양으로 비교된다).
- 안내 한 줄(`info`)·설명은 블록 안에 둔다. 블록 밖에 둘 때는 페이지에 바로(여백 자동).
- 체크리스트: 왼쪽 `row-art`, **오른쪽** `<button class="check" role="checkbox" aria-checked="true|false"><span>(체크 선 아이콘)</span></button>`, 끝낸 행은 `class="row is-done"`
- 켜기/끄기: 오른쪽에 `<button class="switch" role="switch" aria-checked="…">`

## 선택 상태 — 하나의 규칙
선택 표시는 부품마다 하나로 정해져 있고 자동이다 — 손으로 칠하지 않는다. **체크·스위치**(켜고 끄는 값) = 브랜드 색. **칩**(걸러 보기) = 먹색 채움 + 흰 글자. **세그먼트**(보기 전환) = 회색 판 위에 뜬 흰 칸 + 먹색 글자. 칩·세그먼트에 브랜드 색을 쓰지 않는다 — 브랜드 색은 버튼·켜짐처럼 "행동·값"에 남겨 둔다.

## 배지 — 뜻마다 다른 색, 앱 전체에서 하나의 표
`is-brand`(확정·핵심) · `is-warning`(바뀜·마감 임박) · `is-info`(요청·안내) · `is-success`(완료) · `is-danger`(실패) · 클래스 없음(회색: 후보·정하는 중)
- `screens.json`의 `"badges": {"확정": "is-brand", "바뀜": "is-warning", …}` 에 선언한 뜻→색 표만 쓴다(selfcheck가 대조). 한 색에 뜻 하나 — **회색도 뜻 하나**. 내가 해야 할 일(확정 앞둠·답 필요)은 회색 금지(가장 눈에 띄어야 한다). 같은 대상은 모든 화면에서 같은 배지 이름으로 부른다.
- **시간·순서(지금·다음·~까지·D-3)는 배지가 아니라 글자**로. 배지는 상태에만.
- 아직 정하지 않은 것(추천·후보)에 확정 색을 쓰지 않는다.

## 강조색 — 드물게, 뜻 하나에만
`screens.json`의 `"accent": "할인"`처럼 **뜻 하나**를 선언했을 때만 쓴다(없으면 쓰지 않는다). 숫자든 짧은 말이든 같은 부품:
- 강조 글자: `<span class="accent-text">32%</span>` · `<span class="accent-text">오늘 마감</span>` — 공백 포함 **8자 이하** 한 덩어리, 줄 안에 끼워 넣는다.
- 강조 점: `<span class="accent-dot" role="img" aria-label="새 소식"></span>` — 글자 옆에. 점만으로 뜻을 전하지 않는다(`aria-label` 필수).
- **화면당 2곳 이하**. 목록의 행·카드마다 같은 자리에 반복되면(상품마다 할인율) 1곳으로 센다.
- 제목(`h1`·`h2`)·버튼·CTA·배지·탭바 안에 넣지 않는다. 면을 칠하지 않는다. 화면 `<style>`에서 `--c-accent`를 직접 쓰지 않는다. (selfcheck가 검사)
- 팔레트에 강조색이 없으면 브랜드 글자색으로 보인다 — 그래도 같은 규칙.

## 버튼
- 하단 고정(폼·확인·결정·결과 화면에만): `<div class="cta"><button class="btn primary full">저장</button></div>` + body `has-cta`. **탭 첫 화면·홈에는 두지 않는다.** 문구는 확정 동사(저장·보내기·함께하기), "~보기"는 링크.
- 상황에 따라 생기는 할 일: 블록 안 `<a class="btn primary">…</a>`(할 일이 있을 때만)
- 보조: `btn secondary`, 작은 버튼: `btn small tint`
- 비활성: `disabled` 속성. 누를 때 짙어짐(`--c-brand-pressed`)·포커스 링은 자동.

## 입력
`<div class="field"><label class="label" for="x">이름</label><input class="input" id="x" value="…"></div>` · 오류: `field is-error` + `<p class="field-msg">(경고 선 아이콘)문구</p>` — 오류는 색만으로 전달하지 않는다(아이콘 필수).
- **오류 상태 화면은 기본 화면과 같은 요소**에서 문제 칸만 `is-error`로 바꾼다. 버튼 아래 새 칸·새 블록을 붙이지 않는다.
- 입력 순서: 뒤 입력의 규칙을 바꾸는 선택(예: 1:1인지, 누구와 함께인지)은 **앞에**.
- 검색(목록이 30개를 넘을 수 있으면 목록 블록 맨 위): `<label class="search">(돋보기 선 아이콘)<input type="search" placeholder="이름으로 찾기"></label>` + 그 아래 걸러 보는 칩(전체·아직 모임 없음 등). **제목이 "~ 23명"처럼 일부를 약속하면 그 칩이 선택된 모습으로 23명만 보여 준다.**
세그먼트: `<div class="seg" role="radiogroup"><button class="seg-item is-selected" role="radio" aria-checked="true">…</button>…</div>` · 칩: `<div class="chips"><button class="chip is-selected">…</button></div>`
- **세그먼트** — "같은 내용을 2~4가지 방식으로 바꿔 보거나(목록/지도·예정/지난), 짧은 값 2~4개 중 하나를 고르는가?"(성별·양력/음력). 5개 이상이면 시트로 고르기·가로 날짜 줄·칩. 세그먼트를 여러 줄 쌓아 격자를 만들지 않는다(12지시처럼 많으면 고르기 시트).
- **칩** — "이 목록을 사용자가 직접 좁히거나, 짧은 태그를 여러 개 고르는가?"(전체·오전·체험 가능 / 좋았던 점). 라벨은 **10자 이하 낱말**. 문장(추천 질문·제안 문구)은 칩이 아니라 목록 행(`row`)이나 버튼으로. 한 줄에 8개를 넘기면 묶음을 나누거나 필터 시트로. 걸러 보기 칩 사이에 행동("+ 새 무리"·"관리")을 섞지 않는다 — 행동은 `block-link`나 `row is-add`. (selfcheck가 라벨 길이·칸 수·쌓기를 잰다)

## 기타
- 부가 정보 한 줄: `<p class="info"><img src="../assets/fluent/weather.svg" alt=""><span>…</span></p>`
- **아바타 — 미리 준비한 그림만**: `<span class="avatar"><img src="../assets/avatars/<스타일>/NN.svg" alt=""></span>` · 여럿: `<span class="avatars"><span class="avatar"><img …></span>…</span>`. 이름 한 글자(`avatar is-text`)·사물 일러스트를 사람 자리에 쓰지 않는다(selfcheck).
  - 스타일은 앱 전체에 하나 — `screens.json`의 `"avatar_style"`(`assets/avatars/avatars.json`의 `styles`): `people` 컬러 사람 일러스트(친근·가족·생활·교육) · `line` 선 드로잉(업무·에디토리얼·신뢰) · `soft` 부드러운 선(감성·뷰티·커뮤니티) · `animals` 동물 얼굴(익명 서비스) · `photo` 실제 사진(실명이 신뢰의 핵심 — 후기·전문가·매칭, `assets/photos/`에 사람 사진을 찾아 쓴다).
  - 사람마다 파일 하나 — `journey.md` 사실 표의 사람(이름·성별·나이)에 맞춰 `avatars.json`의 `files.<스타일>`에서 고르고(성별·나이가 맞는 것), 모든 화면이 같은 사람에게 같은 파일을 쓴다. 같은 파일을 두 사람에게 주지 않는다.
  - 그룹·채팅방·채널처럼 사람이 아닌 자리는 구성원 아바타 겹침(`avatars`)이나 주제 일러스트(`row-art`).
- 탭바(목적지 3곳 이상일 때만): `<nav class="tabbar"><a class="tab" aria-current="page">(선 아이콘)라벨</a>…</nav>` + body `has-tab`
- 빈 상태: `<div class="empty">…</div>`
- 바텀시트 — **"지금 화면을 벗어나지 않고 고르거나 확인하는 일인가?"** 그렇다면 새 화면이 아니라 시트(몇 개 중 하나 고르기·한 번 더 확인·용어/근거 설명·정렬 고르기). 입력 칸이 3개를 넘거나 다시 돌아와 볼 내용이면 화면으로.
  - 시트 화면은 `screens.json`에 `"kind": "sheet", "over": "<아래 깔리는 화면 id>"`로 적고, 파일은 그 화면을 복사한 뒤 끝에 `<div class="dim"></div><div class="sheet" role="dialog" aria-label="…">…</div>`를 붙인다(selfcheck가 대조). 여는 쪽 화면의 버튼·행은 이 시트 파일로 `<a href>`.
  - 고르기 시트: `<span class="sheet-grip"></span><div class="sheet-head"><p class="h2">사용할 수강권</p></div>` + `<button class="row" role="radio" aria-checked="true">…<span class="row-trail">(체크 선 아이콘)</span></button>` 행들. 확인 시트: 제목 + lead + `btn primary full` + `btn secondary full`.
- 완료 표시(`<id>--done` 상태, 링크 복사·초대·공유처럼 밖으로 내보낸 뒤): 같은 화면 맨 위에 `<p class="done">링크를 복사했어요 — 단톡방에 붙여넣으세요</p>`
- 목록에 추가할 수 있으면 끝에 `row is-add`(**반드시 다른 화면·시트로 가는 `<a href>`** — 자기 화면으로 가면 누른 뒤 모습이 없는 것), 순서를 바꿀 수 있으면 행 오른쪽에 끌기 손잡이(선 아이콘 ≡), 지울 수 있으면 편집 화면에 "지우기"(btn secondary)

## 일러스트 (assets/fluent/, Fluent Emoji Color · MIT)
beach · calendar · car · clipboard · coffee · eyes · father · hayun · hotel · idcard · invite · jieun · luggage · meal · minsu · mother · phone · pill · pin · plane · shoe · ticket · umbrella · walk · weather

용도: 사물·주제 = 컬러 일러스트 / 누르는 것(+·뒤로·›·체크·스위치) = 선 아이콘(stroke 1.75, 24px, currentColor) / 사람 = 아바타. 유니코드 이모지 금지.

## 공통 부품
견본: `foundation/specimens.html`(부품마다 `<section class="spec" data-key="…">`, 상태별 모습).
- 진행 막대(여러 단계 입력·온보딩에서 지금 몇 단계인지): `<div class="progress" role="progressbar" aria-valuenow="2" aria-valuemax="5"><span class="is-on"></span><span class="is-on"></span><span></span><span></span><span></span></div>` — 칸 수 = 전체 단계, `is-on` = 지나온 단계.
- 별점 표시(후기·평점 보여줄 때): `<div class="rating" role="img" aria-label="5점 중 4점"><svg class="is-on" …>(별 선 아이콘)</svg>…5개</div>` — 별 svg는 HTML 인라인(fill 없이 stroke만), 채운 별은 `is-on`.
- 별점 입력(후기 쓰기): `<div class="rating is-input" role="radiogroup"><button class="is-on" role="radio" aria-checked="false" aria-label="1점">(별 svg)</button>…</div>` — 각 별이 44px 버튼, 고른 점수까지 `is-on`, 고른 버튼만 `aria-checked="true"`.
- 범위 표시(가격대·기간처럼 "어디부터 어디까지"를 보여줄 때): `<div class="range" style="--from:20%;--to:60%"><div class="range-track"></div><div class="range-ticks"><span>0</span>…<span>10만</span></div></div>`
  - **인라인 style 예외는 이것 하나**: `.range`에 CSS 변수 `--from`·`--to`(0~100%)만 설정한다. 다른 속성·다른 요소의 인라인 style은 계속 금지.
- 타임라인(진행 이력·예약/시술 경과처럼 날짜 순 기록): `<ol class="timeline"><li class="tl-item"><p class="tl-date">3월 2일</p><div class="tl-body"><p>첫 상담</p></div></li><li class="tl-item is-now">…</li></ol>` — 지금 항목만 `is-now`(점이 브랜드 색).
- 전·후 비교(시술·수리·정리 결과처럼 바뀐 모습을 증명할 때): `<div class="compare"><div class="photo is-3x4"><img src="…" alt="전"><span class="compare-label">전</span></div><div class="photo is-3x4"><img src="…" alt="후"><span class="compare-label">후</span></div></div>`
- 대표 콘텐츠(대표 콘텐츠형 홈의 주인공 — 지금 볼 것 하나, 페이지 맨 위·화면 폭 전체, 블록에 넣지 않는다): `<a class="feature" href="…" data-anchor><div class="photo"><img src="…" alt="…"></div><div class="feature-text"><span class="badge is-brand">방송 중</span><p class="feature-title">…</p><p class="feature-sub">…</p></div></a>` — 사진 비율은 4:3 기본, 영상이면 `photo is-16x9`. 사람 카드의 답(누가 방송 중인지 등)은 이 아래 줄로.
- 사진(상품·장소·결과물을 크게 보여줄 때): `<div class="photo is-16x9"><img src="…" alt="…"></div>` — 비율 `is-3x4`·`is-1x1`·`is-16x9`(없으면 4:3).
- 썸네일(목록 행 왼쪽의 작은 사진): `<span class="thumb"><img src="…" alt=""></span>` · 크게 `thumb is-l`(72px).
- 사진 모음(후기 사진·갤러리 3열): `<div class="photo-grid"><img src="…" alt="">…</div>`
- **사진 자리(`.photo`·`.thumb`·`.photo-grid`·`.compare`)에는 반드시 `<img>`를 넣는다.** 회색 칸에 "사진 1"·"이미지" 같은 글자만 넣지 않는다. `alt`는 무엇의 사진인지 적는다(꾸밈용이면 `alt=""`).

## 탐색·진열·판촉
견본은 `specimens.html`의 같은 이름 칸. 부품마다 **판단 질문 하나** — 예면 쓰고, 아니면 쓰지 않는다. 화면을 채우려고 쓰지 않는다.

- **상단 가로 탭** — "같은 화면 안에서 성격이 다른 내용 묶음 3개 이상을 오가는가?"(추천·랭킹·새로 나온 / 전체·내 글). 2개면 세그먼트, 다른 목적지면 탭바.
  `<nav class="tabs" role="tablist"><a class="tabs-item" role="tab" aria-selected="true" href="…">추천</a>…</nav>` — 앱바 바로 아래. 칸마다 화면은 `screens.json`의 `"tabs"`로 잇는다.
- **정렬·필터 바** — "목록이 사용자가 기준을 바꿔 가며 훑는 양인가?"(`large_list` 목록·상품·수업 찾기). 개수 + 정렬 + 필터(켜진 수).
  `<div class="toolbar"><p class="toolbar-count">1,250개</p><a class="toolbar-btn" href="…">추천순(아래 선 아이콘)</a><a class="toolbar-btn" href="…">(필터 선 아이콘)필터 <span class="toolbar-on">2</span></a></div>` — 정렬 고르기는 시트로.
- **아이콘 격자 메뉴** — "무게가 같은 목적지·분류가 6~10개라 목록보다 한눈에 고르는 게 빠른가?"(카테고리·서비스 바로가기). 5개 이하면 칩, 11개 이상이면 목록.
  `<nav class="menu-grid"><a class="menu-item" href="…"><span><img src="../assets/fluent/plane.svg" alt=""></span>항공</a>…</nav>` — 4열은 `menu-grid is-4`. 라벨은 4자 안팎. 일러스트가 없으면 쓰지 않는다(선 아이콘 격자 금지).
- **가로 스크롤 카드 줄** — "한 묶음을 맛보기로 보여 주고 전체는 다른 화면에 있는가?"(추천·최근 본·이번 주 새로 연). 블록 제목에 `block-link`("전체 보기")를 함께 단다.
  `<div class="scroller"><a class="s-card" href="…"><div class="photo"><img src="…" alt="…"></div><p class="s-title">…</p><p class="s-sub">…</p></a>…</div>` — 넓은 카드 `s-card is-wide`(16:9). 카드 4개 이상(다음 카드가 잘려 보여야 넘길 수 있다는 게 보인다).
  - 동그란 썸네일 줄 — "사람·주제·분류를 **사진으로** 알아보고 고르는가?": `<a class="s-circle" href="…" aria-current="true"><span><img src="…" alt=""></span>요가</a>`
- **상품·콘텐츠 카드 격자** — "사진을 보고 고르는 것이 여러 개인가?"(상품·수업·숙소·글). 사진이 핵심이 아니면 목록 행.
  `<div class="product-grid"><a class="p-card" href="…"><div class="photo"><img src="…" alt="…"><button class="like" aria-pressed="false" aria-label="찜">(하트 svg)</button></div><p class="p-brand">…</p><p class="p-name">…</p><p class="price">…</p><p class="p-meta">(별점) 4.8 · 후기 312</p></a>…</div>` — 촘촘하면 `product-grid is-3`, 세로 사진 `photo is-3x4`.
- **가격** — 값이 있는 것을 사고·예약할 때: `<p class="price"><span class="price-off">15%</span><span class="price-now">170,000원</span><s class="price-was">200,000원</s></p>`(상세는 `price is-l`). 할인이 없으면 `price-now`만. 할인율을 강조색으로 보이려면 `accent`가 "할인"일 때 `price-off accent-text`.
- **찜·좋아요** — "사용자가 나중에 다시 보려고 모아 두는 기능이 PRD·여정에 있는가?" 모은 것을 볼 곳(찜 목록 화면)도 함께 만든다. `<button class="like" aria-pressed="true" aria-label="찜 취소">(하트 svg: fill 없이 stroke)129</button>` — 누른 상태 = 브랜드 색 채움.
- **떠 있는 버튼(FAB)** — "이 화면의 주 행동이 '새로 만들기'(글쓰기·새 일정·판매하기) 하나이고, 목록을 내려도 계속 눌러야 하는가?" 화면당 하나, 하단 고정 버튼(`cta`)과 함께 쓰지 않는다. `<a class="fab" href="…">(+ 선 아이콘)글쓰기</a>` — 글자 없이 쓰면 `aria-label`.

### 판촉 부품 — `screens.json`의 `"promos"`에 선언한 것만
배너·띠 배너·쿠폰·남은 시간은 **이 서비스가 실제로 하는 판촉·소식**만 보여 준다. PRD·여정에서 근거를 찾아 `"promos": [{"name": "첫 예약 1만원 쿠폰", "until": "11월 30일", "source": "PRD F7"}]`로 선언하고, 화면 글자는 그 이름·기한 그대로. 선언이 없으면 판촉 부품을 쓰지 않는다(selfcheck). 지어낸 이벤트·할인 금지.
- **넘기는 배너** — "홈 맨 위에서 알릴 판촉·소식이 2개 이상인가?"(1개면 띠 배너나 블록). 정적 시안이라 한 장만 그리고 개수를 적는다.
  `<a class="banner" href="…"><div class="banner-text"><p class="banner-eyebrow">11월 30일까지</p><p class="banner-title">첫 예약 1만원 할인</p><p class="banner-sub">…</p></div><span class="banner-art"><img src="../assets/fluent/ticket.svg" alt=""></span><span class="banner-count">1/4</span></a>` — 사진이면 `banner-art is-photo`. 개수 대신 점: 배너 아래 `<div class="dots" aria-hidden="true"><span class="is-on"></span><span></span>…</div>`.
- **띠 배너** — "본문을 밀어내지 않고 한 줄로 알릴 혜택·소식인가?": `<a class="strip" href="…"><img src="../assets/fluent/invite.svg" alt=""><span>친구를 초대하면 둘 다 1회 무료</span>(› 선 아이콘)</a>` — 화면당 하나.
- **쿠폰** — "사용자가 받거나 고르는 할인이 있는가?": `<div class="coupon"><div class="coupon-main"><p class="coupon-amount">10,000원</p><p class="coupon-cond">5만원 이상 · 11월 30일까지</p></div><button class="coupon-get">(내려받기 선 아이콘)받기</button></div>` — 받은 뒤 `coupon is-done` + `<span class="coupon-get" aria-disabled="true">(체크)받음</span>`.
- **남은 시간** — "마감 시각이 정해진 판촉·신청이고, 남은 시간이 행동을 바꾸는가?": `<span class="countdown" role="timer" aria-label="남은 시간 3시간 25분">(시계 선 아이콘)03:25:13</span>`. 날짜 단위면 글자("D-3")로.
