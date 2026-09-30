# 부품 요약 — 화면 파일은 이 클래스만 조합한다

인라인 `style`·임의 색/크기 금지. 색·글자·여백은 전부 `tokens.css`(팔레트에서 생성) 변수. 모범 답안: `foundation/examples/*.html`(구조만 참고, 내용 베끼지 말 것).

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

## 배지 — 뜻마다 다른 색
`is-brand`(확정·핵심) · `is-warning`(바뀜·마감 임박) · `is-info`(요청·안내) · `is-success`(완료) · `is-danger`(실패) · 클래스 없음(회색: 후보·정하는 중)

## 버튼
- 하단 고정(폼·확인·결정·결과 화면에만): `<div class="cta"><button class="btn primary full">저장</button></div>` + body `has-cta`. **탭 첫 화면·홈에는 두지 않는다.** 문구는 확정 동사(저장·보내기·함께하기), "~보기"는 링크.
- 상황에 따라 생기는 할 일: 블록 안 `<a class="btn primary">…</a>`(할 일이 있을 때만)
- 보조: `btn secondary`, 작은 버튼: `btn small tint`
- 비활성: `disabled` 속성. 누를 때 짙어짐(`--c-brand-pressed`)·포커스 링은 자동.

## 입력
`<div class="field"><label class="label" for="x">이름</label><input class="input" id="x" value="…"></div>` · 오류: `field is-error` + `<p class="field-msg">(경고 선 아이콘)문구</p>` — 오류는 색만으로 전달하지 않는다(아이콘 필수).
세그먼트: `<div class="seg" role="radiogroup"><button class="seg-item is-selected" role="radio" aria-checked="true">…</button>…</div>` · 칩: `<div class="chips"><button class="chip is-selected">…</button></div>`

## 기타
- 부가 정보 한 줄: `<p class="info"><img src="../assets/fluent/weather.svg" alt=""><span>…</span></p>`
- 아바타 여럿: `<span class="avatars"><span class="avatar"><img src="../assets/fluent/mother.svg" alt=""></span>…</span>`
- 탭바(목적지 3곳 이상일 때만): `<nav class="tabbar"><a class="tab" aria-current="page">(선 아이콘)라벨</a>…</nav>` + body `has-tab`
- 바텀시트: `<div class="dim"></div><div class="sheet">…</div>`, 완료 표시: `<p class="done">…</p>`, 빈 상태: `<div class="empty">…</div>`

## 일러스트 (assets/fluent/, Fluent Emoji Color · MIT)
beach · calendar · car · clipboard · coffee · eyes · father · hayun · hotel · idcard · invite · jieun · luggage · meal · minsu · mother · phone · pill · pin · plane · shoe · ticket · umbrella · walk · weather

용도: 사물·주제 = 컬러 일러스트 / 누르는 것(+·뒤로·›·체크·스위치) = 선 아이콘(stroke 1.75, 24px, currentColor) / 사람 = 아바타. 유니코드 이모지 금지.
