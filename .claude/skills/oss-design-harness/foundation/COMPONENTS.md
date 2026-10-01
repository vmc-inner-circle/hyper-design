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
- 큰 머리글(홈·목록 첫 화면): `<header class="hero"><p class="eyebrow">…</p><h1 class="title">…</h1><p class="lead">…</p></header>` · 이동 링크는 `<a class="hero-more">…›</a>`
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
- 체크리스트: 왼쪽 `row-art`, **오른쪽** `<button class="check" role="checkbox" aria-checked="true|false"><span>(체크 선 아이콘)</span></button>`, 끝낸 행은 `class="row is-done"`
- 켜기/끄기: 오른쪽에 `<button class="switch" role="switch" aria-checked="…">`

## 선택 상태 — 하나의 규칙
칩·세그먼트·체크·스위치의 "선택됨"은 전부 브랜드 색(자동). 선택을 검정·다른 색으로 따로 칠하지 않는다.

## 배지 — 뜻마다 다른 색, 앱 전체에서 하나의 표
`is-brand`(확정·핵심) · `is-warning`(바뀜·마감 임박) · `is-info`(요청·안내) · `is-success`(완료) · `is-danger`(실패) · 클래스 없음(회색: 후보·정하는 중)
- `screens.json`의 `"badges": {"확정": "is-brand", "바뀜": "is-warning", …}` 에 선언한 뜻→색 표만 쓴다(selfcheck가 대조). 한 색에 뜻 하나 — **회색도 뜻 하나**. 내가 해야 할 일(확정 앞둠·답 필요)은 회색 금지(가장 눈에 띄어야 한다). 같은 대상은 모든 화면에서 같은 배지 이름으로 부른다.
- **시간·순서(지금·다음·~까지·D-3)는 배지가 아니라 글자**로. 배지는 상태에만.
- 아직 정하지 않은 것(추천·후보)에 확정 색을 쓰지 않는다.

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

## 기타
- 부가 정보 한 줄: `<p class="info"><img src="../assets/fluent/weather.svg" alt=""><span>…</span></p>`
- 아바타: 인물 일러스트는 mother·father·jieun·minsu·hayun만, 나이·관계가 맞을 때. 그 밖의 사람은 글자 아바타 `<span class="avatar is-text">수</span>`. 사물 일러스트를 사람 자리에 쓰지 않는다.
- 아바타 여럿: `<span class="avatars"><span class="avatar"><img src="../assets/fluent/mother.svg" alt=""></span>…</span>`
- 탭바(목적지 3곳 이상일 때만): `<nav class="tabbar"><a class="tab" aria-current="page">(선 아이콘)라벨</a>…</nav>` + body `has-tab`
- 바텀시트: `<div class="dim"></div><div class="sheet">…</div>`, 빈 상태: `<div class="empty">…</div>`
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
- 사진(상품·장소·결과물을 크게 보여줄 때): `<div class="photo is-16x9"><img src="…" alt="…"></div>` — 비율 `is-3x4`·`is-1x1`·`is-16x9`(없으면 4:3).
- 썸네일(목록 행 왼쪽의 작은 사진): `<span class="thumb"><img src="…" alt=""></span>` · 크게 `thumb is-l`(72px).
- 사진 모음(후기 사진·갤러리 3열): `<div class="photo-grid"><img src="…" alt="">…</div>`
- **사진 자리(`.photo`·`.thumb`·`.photo-grid`·`.compare`)에는 반드시 `<img>`를 넣는다.** 회색 칸에 "사진 1"·"이미지" 같은 글자만 넣지 않는다. `alt`는 무엇의 사진인지 적는다(꾸밈용이면 `alt=""`).
