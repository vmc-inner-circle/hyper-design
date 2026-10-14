# 스키마 — 기준 문서

> **스키마의 기준은 이 문서 하나다**. 칸마다의 뜻 · 규칙 상세는 자동 생성 사전(`docs/`)이, 무엇이 언제 바뀌었는지는 **git 이력**이 갖는다 — 따로 적지 않는다.
> 정본은 JSON이다. 이 문서와 JSON이 어긋나면 JSON을 따르고 이 문서를 고친다.

## 1. 파일

| 파일 | 무엇 | |
|---|---|---|
| `screens.schema.json` | 객체 14개의 칸 · 모양 · 뜻 · 층(`x-layer`) · 생성 단계(`x-stage`) · 관계(`x-ref`) · 하나뿐(`x-unique`) · 규칙(`x-rules`) · 읽는 곳(`x-feeds`) | 정본 |
| `flow.schema.json` | 객체 2개(흐름 · 흐름 단계) | 정본 |
| `rules.json` | 권장 · 규칙의 유일한 자리 — 강도(KRDS 필수 · 권장 · 우수 / 우리 / 사례) · 값 · 검사 · 근거 | 정본 |
| `docs/fields.md` · `relations.md` · `rules.md` | 칸 사전 · 객체와 관계 · 규칙 사전 | 자동 생성 — 손으로 고치지 않는다 |

검사기 · 사전 생성기는 `scripts/schema.js` 하나다(5절).

## 2. 층 · 객체 · 생성 단계

**층**(`x-layer`) — 객체마다 하나: 의도(역할) · 성격(기준어 · 무드보드 · 분위기 · 시안 · 레퍼런스) · 화면(구역 · 화면 · 영역 · 움직임 · 메뉴 항목 · 흐름 · 흐름 단계) · 공통(공통 사실) · 실행 상태(보드 설정 · 라운드 · 다음 번호 — 판단이 아니라 하네스가 쓰는 값).

**생성 단계**(`x-stage`) — Claude가 한 번에 하나씩 쓰고, 단계마다 이 정본의 칸을 그대로 쓴다(Claude 구조화 출력 한도 안: 선택 칸 24 · 유니온 16). 칸은 **앞 단계 칸만** 가리킨다 — 뒤 단계를 가리키면 `--stages`가 실패한다.

**단계별 칸 지도** — 칸 이름과 맡은 일 한 줄. 칸마다의 뜻 · 값 · 관계는 [칸 사전](docs/fields.md)이 갖는다.

- **S1 의도**
  - `project` · `title` · `brand` · `brandIcon` · `platform` — 실행 이름 · 서비스 이름 · 웹/모바일
  - `roles[]`(key · label · goal · inclusion · user) — 누가 무엇을 이루려는지, 읽는 상황
  - `facts` — 사실이 사는 유일한 곳(이름표 → 한 줄, strict 없이 쓰고 검사)
  - `board.recommend.type` · `typeWhy` — inclusion을 보고 글자 크기 추천
- **S2 여정 · 화면 목록**
  - `sections[]` — 구역 보드의 큰 띠
  - `screens[].slug` · `name` · `role` · `file`(`screens/<slug>.html`) · `roles[].nav` — 화면 목록과 메뉴
  - flow.json `flows[]` · `branches[]` — 흐름 · 갈래(from · region · trigger · action · to), 누르는 곳의 영역 key
  - 흐름 `steps[].when` — 같은 화면 · 버튼에서 갈릴 때의 이름표
- **S3 화면 하나씩**(screens[] 하나)
  - `section` · `step` — 놓일 구역 · 단계 이름표
  - `goal` · `problem` · `pattern`(KRDS 이름) · `emphasize` · `emphasize2` · `data` · `defer` · `focus` — 이 화면의 1순위와 근거
  - `regions[]`(level · form · content) — 화면 안 덩어리와 위계. 주 버튼 줄은 `form: actions`(모바일 본문 끝 · 2순위)
  - `state`(first-run · empty · input · error · success) · `when` · `variantOf` · `overlayOf` — 상태 화면 · 뜨는 창과 나오는 조건
  - `policy[]` · `cases[]` · `motion[]` — 정책 메모 · 오류/안내 문구 · 움직임
  - `dark` · `shell` · `navActive` — 그 화면만 다른 색 · 메뉴
- **S4 성격**
  - `mood`(keywords 3 · board) — 기준어 · 무드보드
- **S5 시안**
  - `looks[]` — palette(대표색은 palette.brand 한 칸) · `font`(글꼴 세트) · `type`(제목 성격) · 형태 · 바탕
  - `concepts[]` — 메뉴 틀 · 첫 화면 · 밀도 · 참고한 곳(refs → references 이름)
  - `references[]` · `mood.board[].look` — 구조 레퍼런스 · 무드보드 항목을 쓴 분위기
- **하네스**(생성하지 않음)
  - `round` · `stage` · `nextScreenId` · `nextRegionId` — 실행 상태
  - `concept` · `theme` · `toggles`(type · swatch · toast) — 사람이 고른 결정
  - `board`(recommend · ask · locked · focus · changes · hero) — 추천 · 질문 · 확정 · 바뀐 점

칸 하나가 객체와 다른 단계에 쓰이면 **칸에 x-stage**를 적는다 — 칸의 단계가 객체 단계보다 앞선다(예: 무드보드 항목(S4)의 `look`은 S5).

**칸의 기준**:
- 칸마다 읽는 곳이 있어야 한다 — ① 코드(pack · expand · build · lint · looks · ids) ② 보드(사람이 본다) ③ 생성(다음 단계에서 Claude가 읽는다 — `x-feeds`에 그 칸 경로). ③만 있는 칸은 안내문이 그 칸을 가리키는지 시험이 확인할 때만 둔다. 읽는 곳이 없는 칸은 두지 않는다(§6 순서로 지운다).
- 같은 값을 두 칸에 적지 않는다 — 다른 칸이 필요하면 `x-ref`로 가리킨다. 공통 목록은 `$defs`에 하나: 문구 색 성격 `$defs/tone`(cases · data-stay-tone), 메뉴 틀 `$defs/shell`(시안 · 화면), 안내 문구 모양 `$defs/toast`(toggles · board.recommend).
- 같은 말이 다른 뜻인 칸은 설명 첫 말로 가른다 — `screens[].when`(상태 화면이 나오는 조건) · `cases[].when`(문구가 뜨는 때) · 흐름 `steps[].when`(갈래 이름표). 최상위 `brand`(서비스 이름) · `palette.brand`(대표색, KRDS Primary).
- 추천 · 결정은 짝이다 — `board.recommend.*`(추천)와 최상위 `concept` · `theme` · `toggles`(결정). 보드는 잠갔으면(`board.locked`) 결정, 아니면 추천을 쓴다. 글자 크기는 근거(`roles[].inclusion`) → 추천(`board.recommend.type`) → 결정(`toggles.type`).

## 3. 관계 · 칸 표시

| 표시 | 뜻 | 검사 |
|---|---|---|
| `x-ref: "screen.slug"` | 다른 객체의 칸을 가리킨다 — 문서 전체에서 찾는다 | 정본: 대상 칸이 있나 · 실행물: 값이 있나 |
| `x-ref: {to, within}` | 범위 안에서만 찾는다 — `doc` 문서 전체(기본, 문자열 x-ref와 같다) · `screen` 같은 화면의 영역 · `from` 흐름 단계 출발 화면의 영역 · `role` 같은 역할의 화면 · `theme` 고른 분위기의 버튼 색(`also`: 대표색 `brand`도 된다) | 같음 + 범위가 그 자리에서 뜻이 있나 |
| `x-unique: doc · screen · look` | 그 범위 안에서 하나뿐 — 화면 slug는 문서 전체, 영역 key는 같은 화면 안(다른 화면에 같은 key는 된다) | 실행물 |
| `allOf` `if/then` | 조건 필수 — 오류 · 완료 화면은 `variantOf`, 움직임 종류별 `region` · `trigger`, 플랫폼별 메뉴 틀(시안 · 화면 — 화면 하나만 `none`은 두 플랫폼 모두) | 실행물 |

**닫힌 형식**: 정본에 없는 칸 · 값은 받지 않는다(옛 칸 · 옛 값도 실패). 새 칸은 `required` — 빠지면 실패다. `node scripts/schema.js`가 정본에 옛 표시(legacy · 권장 · 낮춘 경고)가 다시 생기면 실패로 알린다.

HTML 조각 안에만 있는 것(`data-trigger` · `data-stay`)은 x-ref가 아니라 lint가 본다. 칸이 아니라 화면 사이를 보는 규칙 — 변형의 대상(`variant-target`) · 뜨는 창은 흐름의 도착(`overlay-reached`) · 같은 버튼이 두 번이면 갈래 이름표(`split-when`) — 은 `rules.json`에 있고 `schema.js`가 실행물에서 본다.

## 4. 값

**값의 주인**:

| 순서 | 어디 | 정하는 것 | 언제 |
|---|---|---|---|
| 1 | `packages/core/tokens/base.css` | 모든 변수의 기본값 — **KRDS 본문 바닥선**(본문 16px 이상 · 기본 17px · 굵기 400/700 · 줄 간격 150%) · 글자 단계 · 간격 · `--pad-card · --pad-row` | 늘 |
| 2 | `packages/core/tokens/toggles.css` | 보드에서 사람이 고른 글자 크기 · 버튼 색 | 보드 |
| 3 | `scripts/looks.js` ← `screens.json looks[]` | 색(바탕 · 글자 · 역할 팔레트 · 상태색) · 모양 · 밀도 | 1턴 시안부터 |
| 4 | `scripts/looks.js` `FONTS` ← `looks[].font` | 글꼴 세트 — 본문 · 제목 글꼴과 제목 굵기 · 줄 간격. **글꼴의 주인은 `look.font` 하나**, `look.type`은 제목 성격(heading · headingWhy · ratio)만 | 1턴 시안부터 |

역할 색 계산 · 상태색 · 글꼴 세트는 looks.js 한 곳에만 있다. 글꼴 세트는 KRDS 본문 바닥선(1번) 아래로 내려가지 않고, 그 위에서 제목 굵기 · 줄 간격만 정한다.

**KRDS 범위**:

| KRDS | 여기서 | 다시 볼 때 |
|---|---|---|
| 원칙 1~7 · 기본 패턴 12 · 서비스 패턴 5 · 색상 · 타이포그래피 · 형태 · 레이아웃 간격 · 디자인 토큰 | **다룬다** — 칸 · 규칙은 칸 사전 · 규칙 사전 | — |
| 아이콘(크기 · 키라인 · 두께) | **범위 밖** — 아이콘은 라이브러리(`packages/core/icons`)가 고정이라 화면마다 고르지 않는다 | 아이콘을 시안마다 고르게 될 때 |
| 엘리베이션(그림자 단계 · 표면 고도) | **범위 밖** — 그림자는 형태(`looks[].shape`)에 묶여 계산된다 | 모달 · 바텀 시트 같은 겹치는 층이 화면 품질 문제로 나올 때 |
| 레이아웃 그리드 · 브레이크포인트 | **범위 밖** — 화면 틀이 1280 고정(web) · 390(mobile) | 반응형을 다룰 때 |
| 선명한 화면 모드(고대비) | **범위 밖** — 보드는 기본 모드만 | 접근성 모드를 보드 토글로 넣을 때 |
| 그래픽 색(차트 · 배너 · 일러스트) | **범위 밖** — 지금 예시에 차트가 없다 | 차트가 있는 PRD가 올 때 — brand · support를 톤 다운(KRDS https://www.krds.go.kr/html/site/style/style_02.html) |

## 5. 명령

모두 실패 0이어야 한다.

```bash
node scripts/schema.js                 # 정본 자체 검사 — 규칙 연결 · 관계(범위) · 생성 단계 · 읽는 곳 · docs/ 최신
node scripts/schema.js runs/<p>        # 실행물 형식 · 값 · 관계(범위) · 하나뿐 — 오류는 실패(경고는 칸이 생성 단계에서만 읽히는 것 등)
node scripts/schema.js --stages        # 생성 단계 — 앞 단계만 가리키나 · Claude 구조화 출력 한도
node scripts/schema.js --feeds         # 읽는 곳 — 칸마다 코드 · 보드 · 생성
node scripts/schema.js --relations     # 객체와 관계 표(범위 · 단계 포함)
node scripts/schema.js --rules         # 규칙 사전 + 칸 ↔ 규칙 연결
node scripts/schema.js --docs          # docs/fields.md · relations.md · rules.md 다시 쓰기
node scripts/lint.js runs/<p>          # 품질 규칙 · 조각 HTML과의 이어짐
node scripts/test.js                   # 저장소 시험(20 = 스키마 — 이 문서의 예시도 검사한다)
```

## 6. 칸 · 규칙을 바꾸는 순서

리뷰에서 정함 → 정본 JSON(칸 · `x-ref` · `x-unique` · `x-stage` · `x-rules` · `x-feeds`) → 규칙이면 `rules.json`(fields ↔ x-rules 두 방향) → `node scripts/schema.js --docs` → 5절 검사 통과 → 커밋. 칸을 지울 때는 정본 · 읽는 코드 · 안내문에서 한 번에 지우고 `x-version`을 올린다 — 옛 형식 실행물은 그 판으로 검사하지 않는다.

## 7. 예시 — 지금 칸 기준 (하네스가 읽는다)

> 정본 검사(`node scripts/schema.js`)를 오류 · 경고 없이 통과하는 최소 예시 — 시험 20이 이 블록을 그대로 검사한다. 1턴의 mood · looks · concepts는 칸 사전을, 분위기까지 있는 예는 `test/fixtures/sample`을 본다.

### screens.json

```json
{
  "project": "sample",
  "title": "동네 빵집 재고",
  "platform": "web",
  "round": 1,
  "facts": {
    "milk-left": "우유 1L 6팩 남음 — 평소 하루 8팩",
    "dairy-deadline": "유제품 주문 마감 오늘 15:00",
    "milk-order": "우유 12팩 주문 추천(내일 7:40 도착)"
  },
  "roles": [
    { "key": "owner", "label": "사장", "goal": "오늘 무엇을 얼마나 시킬지 근거를 보고 바로 주문한다", "inclusion": "오픈 전 10분, 카운터 뒤 컴퓨터",
      "nav": [ { "slug": "order-today", "label": "오늘 발주", "icon": "clipboard-list" } ] }
  ],
  "sections": [
    { "key": "order", "name": "오늘 시키기", "desc": "마감이 급한 것부터 보고 주문을 보내요" }
  ],
  "screens": [
    {
      "slug": "order-today", "name": "오늘 발주", "role": "owner", "section": "order", "step": "시킬 것 보기",
      "goal": "마감이 급한 거래처부터 오늘 시킬 양을 확인한다",
      "problem": "유제품 마감을 놓치면 주말에 우유가 떨어진다",
      "pattern": "목록 탐색",
      "emphasize": "유제품 주문 마감 15:00 — 우유 12팩",
      "data": ["dairy-deadline", "milk-left", "milk-order"],
      "defer": ["지난주 버린 금액 — 살림 화면으로"],
      "focus": "deadline",
      "regions": [
        { "key": "deadline", "label": "가장 급한 마감", "why": "마감을 놓치지 않게", "level": 1, "form": "hero", "content": "dairy-deadline · milk-order" },
        { "key": "by-vendor", "label": "거래처별 시킬 것", "why": "근거를 보고 수량을 고친다", "level": 2, "form": "table", "content": "품목 · 남은 양 · 평소 사용 · 추천 수량" }
      ],
      "policy": [ { "title": "기본 정의", "items": ["마감이 가까운 거래처부터 위에", "추천 수량 = 평소 사용 × 도착까지 날 − 남은 양"] } ]
    },
    {
      "slug": "order-edit", "name": "수량 고치기", "role": "owner", "section": "order", "step": "수량 정하기",
      "goal": "추천 수량을 보고 시킬 양을 정해 주문을 보낸다",
      "problem": "추천이 틀리면 고칠 곳을 바로 찾아야 한다",
      "pattern": "입력폼",
      "emphasize": "우유 12팩 — 고칠 수 있어요",
      "data": ["milk-order", "milk-left"],
      "defer": ["다른 거래처 품목"],
      "focus": "qty-form",
      "regions": [
        { "key": "qty-form", "label": "시킬 양 적는 곳", "why": "추천을 그대로 두거나 고친다", "level": 1, "form": "form", "content": "품목 · 추천 수량 · 고칠 수량 · '주문 보내기'" }
      ],
      "policy": [ { "title": "입력 규칙", "items": ["수량은 0~99, 0이면 이번에 안 시킨다"] } ],
      "cases": [
        { "when": "수량을 비워 두고 보내면", "show": "시킬 수량을 적어 주세요", "tone": "danger" },
        { "when": "평소보다 3배 넘게 적으면", "show": "평소보다 많이 시켜요. 맞는지 한 번 더 봐 주세요", "tone": "warning" }
      ],
      "motion": [ { "type": "hold", "trigger": "send", "ms": 1500, "note": "'주문 보내기'를 길게 누르면 보내져요" } ]
    },
    {
      "slug": "order-edit-error", "name": "수량 고치기 (수량 빠짐)", "role": "owner", "section": "order", "step": "수량 정하기",
      "state": "error", "variantOf": "order-edit", "when": "수량을 비워 두고 '주문 보내기'를 눌렀을 때",
      "goal": "비어 있는 수량 칸을 찾아 채운다", "problem": "왜 안 보내졌는지 모르면 주문을 놓친다",
      "pattern": "오류", "emphasize": "시킬 수량을 적어 주세요", "data": ["milk-order"], "defer": [], "focus": "qty-form",
      "regions": [ { "key": "qty-form", "label": "시킬 양 적는 곳", "why": "빈 칸이 빨갛게 표시돼요", "level": 1, "form": "form", "content": "빈 수량 칸 + 오류 문구" } ]
    },
    {
      "slug": "order-sent", "name": "주문 보냄", "role": "owner", "section": "order", "step": "보낸 것 확인",
      "state": "success", "variantOf": "order-today", "when": "'주문 보내기'가 끝난 뒤",
      "goal": "주문이 거래처에 갔는지 확인한다", "problem": "보냈는지 확신이 없으면 전화로 다시 묻는다",
      "pattern": "확인", "emphasize": "우유 12팩 주문을 보냈어요 — 내일 7:40 도착", "data": ["milk-order"], "defer": [], "focus": "sent",
      "regions": [ { "key": "sent", "label": "보낸 주문", "why": "무엇이 언제 오는지 확인해요", "level": 1, "form": "hero", "content": "milk-order" } ]
    }
  ]
}
```

- `id`는 적지 않는다 → `node scripts/ids.js runs/<p>`가 채운다(화면 1부터, 영역 101부터, 한 번 준 번호는 바뀌지 않는다).
- `roles[].user`(셸 오른쪽 위 사람 `{ "name", "initials" }`) · `brand` · `brandIcon`(상단바 서비스 이름 · 아이콘, 없으면 `title` · layout-dashboard)은 선택이다. 셸은 `scripts/expand.js`가 붙인다. 화면마다 `shell: "none"`(메뉴 없는 한 장) · `navActive`(메뉴에 없는 화면에서 켤 항목) · `overlayOf`(뜨는 창 — 이름은 '~ 창', 흐름이나 갈래가 열어야 한다) · `dark`(밤에 쓰는 화면)는 선택이다.
- 구역 보드: 큰 구역(`sections` 2~6개) → 단계 이름표(`step`) → 화면 나란히, 화면 아래 정책 메모(`policy`, 상태 변형은 선택). 오류 · 안내 문구는 `cases`, 움직임은 `motion`(종류별로 `region` · `trigger`)에 — 정책에 다시 쓰지 않는다.
- `state`: `first-run` · `empty` · `input` · `error` · `success`. 오류 · 완료는 `variantOf`(원래 화면) 필수 · 나오는 조건 `when`. 입력 화면이 있으면 오류 1개 이상, 완료 1개 이상(lint).
- `board.locked`: 2라운드부터 확정한 것 — 예 `["concept", "theme", "type", "swatch", "toast", "ask"]`. `board.focus`: 지난 라운드에 고친 화면 slug — 보드 맨 위에 먼저 나온다. `board.changes`: `[{ "slug", "said", "did" }]` 지난 의견을 반영해 바뀐 점.
- `toggles.toast` · `board.recommend.toast`: 안내 문구 모양 `{ "at": "top|bottom", "icon": "on|off", "tone": "light|dark|color", "size": "normal|large" }` — 없으면 top · on · light · normal.

### flow.json

```json
{
  "flows": [
    {
      "key": "order",
      "name": "오늘 발주하기",
      "role": "owner",
      "steps": [
        { "from": "order-today", "region": "by-vendor", "trigger": "edit-qty", "action": "'수량 고치기'를 누르면", "to": "order-edit" },
        { "from": "order-edit", "region": "qty-form", "trigger": "send", "action": "'주문 보내기'를 누르면", "to": "order-sent" }
      ]
    }
  ],
  "branches": []
}
```

- 흐름은 주인 역할(`role`)이 있다. `branches`(갈래)는 흐름 밖의 버튼이 여는 화면 · 창 — 모양은 step과 같다.
- `region`은 출발 화면(`from`)의 영역 key다. `when`(갈래 이름표, 16자 이내 "~면")은 같은 화면 · 같은 버튼에서 갈릴 때만 — 구역 보드는 `when`이 있는 연결에만 화살표를 그린다.
- 조각에서 누르는 요소: `<button class="btn btn-primary" data-trigger="send">주문 보내기</button>`(그 step의 region 안). 글자가 있는 `.btn`은 `data-trigger` · `data-back` · `data-stay="안내 문구"`(색은 `data-stay-tone` — `$defs/tone`) 중 하나를 가진다.

### icons.json (선택)

```json
{ "_about": "프로젝트 전용 의미 → lucide 이름. core allowlist에 없는 것만.", "itinerary": "route" }
```

icons.json은 이 정본 밖이다 — 형식이 `{ 의미: lucide 이름 }` 한 줄이라 lint가 검사한다.
