---
name: oss-design-harness
description: PRD(기능 요구사항 문서)를 받아, 사용자에게 딱 4번만 의견을 묻고 나머지는 스스로 판단해서 30분 안팎에 PRD 의 모든 기능이 들어간 PC·폰 겸용 웹앱 HTML 을 만드는 디자인 하네스. 사용자가 PRD·기획서·요구사항을 붙여 넣거나 "이걸로 화면 만들어줘", "HTML 로 디자인해줘" 라고 하면 쓴다.
---

# oss-design-harness (v7 엔진)

현업 디자이너처럼 스스로 판단해 실제 화면을 만든다. **사용자는 디자인을 모르는 사람이다. 사용자의 시간은 질문 4번뿐이다.**
이 파일 = 모든 워크플로우가 공유하는 엔진. **질문 4번을 언제·무엇으로 쓰는지는 같은 폴더의 `WORKFLOW.md` 가 정한다 — 반드시 먼저 읽고 그대로 따른다.**

## 규칙 (어기면 실격)

1. **사용자에게 턴을 넘기는 것 = 질문 1번.** 최대 4번. 첫 PRD 입력이 1번째 개입이고, 질문 4번이 남은 전부다.
2. 턴을 넘길 때는 **반드시 질문 페이지(`design/ask/q<n>.html`)와 함께** 넘긴다. "진행할까요?", "확인 부탁드려요", 중간 보고로 턴을 넘기지 않는다. 질문이 아닌 일은 전부 스스로 끝까지 한다.
3. 질문 밖의 빈칸(사실·수량·기기·환경)은 묻지 않는다. **가정하고** `design/brief.md` 가정 목록에 적고, 중요한 가정만 질문 페이지의 `assume` 항목으로 보여준다(사용자는 틀린 것만 누른다).
4. 사용자 답은 **답 코드**(`Q1 · a=o2 · b=바꿈:2 · c=1,3`)로 온다. `python scripts/ask.py --read design/ask/q<n>.json "<답 코드>"` 로 풀어 읽고, 원문과 풀이를 `design/decisions.md` 에 남긴다. 코드 끝의 `메모=<글>` 은 사용자가 말로 적은 요청 — 고른 것과 겹치면 메모를 우선해 반영한다. 답은 **보이는 결과로** 반영하고, 무엇을 어디에 반영했는지 다음 페이지 `lead` 첫 줄에 쓴다.
5. 마지막 답을 받은 뒤 더 묻지 않는다. 끝나면 마지막 줄에 `[완료] design/app/index.html`.
6. 턴을 넘기는 답의 마지막 줄은 정확히 `[질문 <n>] design/ask/q<n>.html`.

## 결과물의 기준 (관문 — 하나라도 못 넘으면 실패)

- **PRD 기능 요구사항 전부**가 실제 화면에 있다. `features` 목록 = PRD 의 기능 요구사항 번호 그대로(F1…). 화면마다 `features` 로 연결.
- **필수 흐름**: 처음 시작(온보딩) · 함께 쓰는 사람 초대 · 아무것도 없을 때(빈 상태) — `flows` 에 화면 id. PRD 에 없어도 쓰려면 필요한 흐름(예: 확인만 하는 사람의 첫 화면, 알림 모아 보기)은 스스로 넣는다.
- **PC·폰 둘 다**: 같은 app.json 이 폭에 따라 폰(탭바·한 열) / PC(사이드바·본문+보조 열)로 바뀐다. PC 에서 보조 열(`side`)을 적극 쓴다 — 폰 화면을 넓혀 놓은 것처럼 보이면 실패.
- **역할별로 다르게**: 사용자 종류(PRD 의 유저스토리)마다 `roles` 하나, 역할마다 내비 2~5개. 같은 정보를 역할에 맞게 다르게 보여준다.
- **충분한 페이지 수**: 비개발자가 둘러보고 서비스를 이해할 만큼 — 보통 12~20 화면(역할별 메인 + 상세 + 작성·수정 + 빈 상태·온보딩·초대·알림).
- `python scripts/coverage.py design/app/app.json` 가 **PASS**.

## 품질 바닥 (답과 무관하게 하네스가 책임진다)

- **진짜 같은 내용**: 실제 한국 이름·지명·가게·날짜·금액·시간. "항목 1", "사용자 A", "Lorem" 금지. 날짜는 오늘(실행일) 기준으로 그럴듯하게. 수량은 PRD "사용자들의 상황"의 범위 안.
- **사진**: 필요한 곳(사람·장소·음식 등)에만 `"img":"gen:<영어 키워드>:<숫자>"` — 엔진이 그림을 그려 넣는다(예: `gen:woman:1`, `gen:jeju,beach:3`). 외부 사진 주소(loremflickr·unsplash 등) 금지 — 막히면 빈칸이 된다. 주제와 무관한 그림 금지. 사진 없는 곳은 아이콘·색면.
- **아이콘**: Lucide 이름만. 이모지 금지.
- **AI 티 금지 목록**: 보라→파랑 그라디언트 · 인디고 #6366F1/#4F46E5 기본 강조색 · 크림 배경+세리프+테라코타 조합을 이유 없이 · 카드 왼쪽 색 띠 · 같은 모양 카드 3개 나열로 때우기 · 모든 카드 같은 radius·같은 그림자 · 가짜 상태바·폰 테두리 · 영어 직역체("~을 통해 ~를 제공합니다") · 버즈워드. 색은 **이 서비스 사정에서 이유가 있는** 팔레트로(이유를 decisions.md 에 한 줄).
- **확정/후보·상태 구분**이 필요한 서비스면 모양으로 구분(`state:"draft"` 점선·`badge`) — 색만으로 구분하지 않는다.
- 글자: 보는 사람이 나이 든 사람이면 `scale` 1.15~1.3, 버튼 크게.
- **검사**: 전체 생성 뒤 반드시 ① `coverage.py` PASS ② `shots.py app` 로 전 화면 폰·PC 캡처 ③ **PNG 를 실제로 눈으로 본다**(모두가 아니라도 역할별 메인 화면 폰·PC 전부 + 나머지 중 절반) — 깨짐·잘림·빈 공간·겹침·AI 티 ④ 고칠 곳은 JSON 을 고쳐 다시 그린다. 최대 2바퀴.

## 도구 (읽지 말고 이대로 쓴다 — 쓰는 법은 여기 있다)

- `python scripts/app.py design/app` — `design/app/base.json`(name·tagline·tokens·roles·features·flows·tour·decisions·assumptions·order) + `design/app/screens/*.json`(화면) → `app.json` → `app.html`(앱) + `index.html`(체험 투어: 역할·폰/PC 전환·따라가 보기·결정 기록·기능→화면 표). 형식 요약:
  - 화면 = `{"id","title","role","icon","features":["F1"],"navLabel"?,"layout"?,"blocks":[...],"side":[...]}` — layout: stack(기본)|wide|center|split|canvas
  - 블록 t: header{title,sub,right,back,to} · hero{img|icon,title,text} · stats{items:[{label,value,tone}]} · banner{text,tone,icon} · section{title,right} · list{title,items:[{title,sub,right,badge,tone,state(done|todo|alert|draft),icon,img,who,to}]} · checklist{title,items:[{title,sub,checked,who}]} · timeline{title,items:[{time,title,sub,badge,state(fixed|draft),who,to}]} · cards{cols,items:[{title,sub,img,icon,badge,meta,to}]} · grid{cols,items:[{label,value,icon,tone,to}]} · table{cols,rows} · kanban{cols:[{title,items}]} · buttons{items:[{label,icon,primary,to}]} · chips{items,active} · segment{items,active} · avatars{items:[{name,sub,done}]} · progress{value,label} · calendar{month,start,days,marks{"12":"done|part|miss|accent"},note} · form{fields:[{label,value,hint,kind(text|select|toggle|date)}],submit,to} · steps{items,active} · sheet{title,blocks} · empty{icon,title,body,cta,to} · text{text,size,tone} · quote{text,who} · html{html}(이 서비스만의 조각) · **형태 블록**: carousel{title,items:[{title,sub,img,badge,to}]} · map{pins:[{x,y,label,tone}],route,numbered,height} · bignum{value,label,sub} · poster{img,kicker,title,text,cta,to} · gallery{items:["gen:…"]} · chat{items:[{who,text,me}]} · tabs{items,active} · cols{cols:[[블록],[블록]]} · art{height,items:[{s:도형,c:a1~a4|ink|#hex,x,y,w(%),rot,o}],title,text} 도형으로 그린 그림
  - tokens: bg surface ink muted line accent accentInk warn ok info(색) · radius · font(본문) · headFont(제목·숫자) · scale · density(tight|normal|airy) · card(flat|outline|shadow|tint) · heading(bold|light|serif) · dark · **nav**(폰: tabbar|pill|topbar|hub|drawer) · **pcnav**(PC: side|top|rail)
    글꼴 이름: sans(Pretendard) · gothic-a1 · gowun · sunflower · mono(IBM Plex) · round(Jua) · dohyeon · black-han · orbit · nanum-pen · serif(나눔명조) · noto-serif · gowun-batang · hahmlet. 본문(font)은 읽기 편한 고딕 계열, 성격은 headFont 로.
  - 디자인 시스템 CSS = `design/app/style.css`(80~200줄, 없으면 coverage FAIL) — '디테일로 와우' 3번. 후보 미리보기 JSON 은 `"styleFile":"<같은 폴더의 css>"`. 블록에 `"cls":"이름"` 을 달면 그 블록만 꾸밀 수 있다.
  - 직접 그린 화면 = `design/app/screens/<id>.html`(같은 id 의 json 옆). 후보 미리보기는 화면에 `"htmlFile":"<같은 폴더의 html>"`.
  - `"to":"화면id"` 로 화면을 잇는다(누르면 이동). 내비에 없는 화면은 반드시 어딘가에서 `to` 로 연결.
- `python scripts/app.py design/cand/<이름>.json --out design/cand/<이름>.html` — 후보 미리보기(같은 형식, 화면 1~3장). 그리고 `python scripts/shots.py cand design/cand --d` → `<이름>.png`(폰) + `<이름>-d.png`(PC).
- `python scripts/styles.py list | try <화면.json> <id>… [--palette 1] | use <id>` — 스타일 라이브러리(10종). try = 같은 화면을 여러 스타일로 입혀 `design/cand/style-<id>.png`·`-d.png` 까지.
- `python scripts/ask.py design/ask/q<n>.json` → 질문 페이지. 형식:
  `{"n":1,"title":"…","lead":"…","items":[{"id":"a","kind":"pick","q":"…","why":"추천과 이유","recommend":"o2","options":[{"id":"o1","label":"…","desc":"고르면 무엇이 달라지나","img":"../cand/o1.png","img2":"../cand/o1-d.png","ref":"…","refLabel":"…"}]},{"id":"b","kind":"assume","q":"…","list":[{"id":"1","text":"가정","alt":"바꾸면"}]},{"id":"c","kind":"check","q":"…","list":[{"id":"1","text":"개선안"}]}]}`
  만든 뒤 `python scripts/shots.py page design/ask/q<n>.html` 로 캡처하고 PNG 를 한 번 본다(이미지가 안 보이거나 깨졌으면 고친다).
- `python scripts/shots.py app design/app/app.json [--only a,b]` → `design/shots/<id>-m.png`, `<id>-d.png`.
- `python scripts/coverage.py design/app/app.json` → PASS/FAIL + 고칠 목록.
- `python scripts/ref_fetch.py <검색어>… --per 3 --limit 8` → 실제 앱 스크린샷 레퍼런스(`$HD_REFLIB`), 모아보기 `sheet-<검색어>.png`. 레퍼런스에서는 **방식·관찰값만** 빌린다(구성·정보 형태·밀도·모서리·글자 비율·색 분위기). 로고·문구·브랜드 색·배치 통째 금지.

## 이 서비스만의 얼굴 (자유도 — 09-28 사용자: "다른 PRD 결과와 비슷하게 나오면 안 된다")

- 엔진은 **구조**(PC·폰 겸용·기능 커버·화면 잇기)만 책임진다. **겉모습과 화면 구성은 매번 이 PRD 에서 새로 정한다.** 이 파일의 예시·지난 결과·다른 서비스에서 본 모양을 기본값으로 쓰지 않는다.
- 출발점 = 이 PRD 사용자의 **상황·장소·감정·쓰는 순간**(예: 이동 중 한 손으로? 여럿이 같이 보며? 설레는 준비? 급한 확인?). 여기서 색·글꼴·밀도·장식의 이유를 뽑아 `decisions.md` 에 한 줄씩.
- 레퍼런스는 **이 PRD 도메인의 실제 앱**에서(`ref_fetch.py` 검색어 2~3개) — 방식·관찰값만 빌린다.
- 홈 화면 구성도 이 서비스의 **핵심 행동 하나**를 중심으로 짠다. "통계 칸 + 목록 + 빠른 이동" 같은 틀을 기본으로 깔지 않는다(필요할 때만).
- **형태를 고른다(기본값 없음).** 아래 네 축을 이 서비스 사정에서 매번 새로 고르고 이유를 `decisions.md` 에 한 줄씩:
  | 축 | 고를 것 | 이럴 때 |
  |---|---|---|
  | 폰 내비 `nav` | tabbar · pill · topbar · hub · drawer | 자주 오가는 곳 3~5개=tabbar/pill · 읽기 위주=topbar · 한 가지 일을 순서대로=hub · 메뉴가 많고 드물게=drawer |
  | PC 내비 `pcnav` | side · top · rail | 메뉴 많음=side · 콘텐츠가 넓게 보여야=top · 도구처럼 오래 켜 둠=rail |
  | 화면 배치 `layout` | stack · wide · center · split · canvas | 보조 정보 곁들임=stack · 사진·카드 많이=wide · 읽기·작성=center · 목록 고르고 상세=split · 지도·달력이 주인공=canvas |
  | 주인공 블록 | poster · map · calendar · bignum · carousel · timeline · kanban · chat · gallery · table · cols … | 사용자가 그 화면에서 제일 먼저 봐야 할 것 하나 |
- `tokens` 와 `style` 로 표정을 만든다. **후보끼리는 색만 달라서는 안 된다.** 방향 후보끼리는 **형태**(내비·배치·주인공 블록) 중 둘 이상이, 분위기 후보끼리는 글꼴 짝·모양(모서리·카드·구분선)·장식(`style`)·밀도 중 **3가지 이상**이 달라야 한다.

## 디테일로 와우 — 개성 (09-28 사용자: "뻔한 결과보다 와 하는 결과", "나만의 개성이 잘 나오면 좋겠다, 요즘은 개성시대")

실제 웹의 잘 만든 서비스들은 **뼈대(내비·목록·상세)는 비슷해도 세부 디자인이 전부 다르다.** 우리도 그렇게 만든다. 뼈대는 엔진이, **개성은 디테일이** 만든다.

1. **은유 한 단어** — 이 서비스를 물건 하나로(예: 티켓·여권·공책·지도·영수증·게시판·앨범·계기판·편지·스티커북). PRD 사용자의 상황과 **사용자가 고른 분위기·말로 적은 취향**에서 뽑는다. `decisions.md` 에 이유 한 줄.
2. **시그니처 디테일 3~5개** — 은유에서 나온, 전 화면에 반복되는 작은 장치. 아래 도구 상자에서 고르거나 새로 만든다. 한 번 보면 이 앱인 줄 알 정도로.
   - 글자: 아주 큰 숫자 · 굵기 대비(900/300) · 넓은 자간 작은 라벨 · 숫자만 다른 글꼴 · 세로 라벨 · 손글씨 한 곳
   - 모양: 절취선·구멍 뚫린 카드 · 도장·스탬프 배지 · 스티커(살짝 기운) · 탭 달린 카드 · 비대칭 모서리 · 각진 알약 · 오프셋 테두리
   - 면과 선: 종이 질감(SVG 노이즈 data URI) · 모눈·줄 노트 배경 · 점선 구분선 · 두 색 면 분할 · 색 띠 헤더 · 큰 번호 워터마크
   - 깊이: 겹친 카드 · 딱딱한 그림자(blur 0 오프셋) · 레이어 종이
   - 아이콘·그림: 선 굵기 통일 · 네모 아이콘 틀 · 한 색 일러스트(`gen:` 그림에 CSS filter/mix-blend)
   - **여러 색**: 강조색 4개(`accent`~`accent4` → `--a1`~`--a4`)를 카드·통계·아이콘·배지가 돌려 쓴다. 색 하나로 다 칠하지 않는다.
   - **도형**: `.sh .sh-<이름>` 또는 CSS 변수 `--m-<이름>`(mask) — circle ring half quarter blob blob2 star sparkle flower triangle plus dots squiggle zigzag arc wave pill. 머리말 옆·빈 곳·일러스트(`art` 블록)에.
3. **디자인 시스템 CSS = `design/app/style.css`**(80~200줄, 반드시) — **스타일 라이브러리에서 출발한다**: `python scripts/styles.py list`(10종: 타일 상자·굵은 선 포스터·잡지·스위스 격자·종이와 문구·티켓과 여권·말랑 파스텔·어두운 계기판·자연과 곡선·스티커 팝, 성격표 요즘 유행/오래 가는/과감한/따뜻한). (사용자가 "완전 자유" 를 골랐으면 라이브러리 없이 모델 스스로 처음부터 쓴다.) 사용자가 고른 스타일의 `styles/<id>.css` 를 복사하고 `styles.py use <id>` 의 tokens 를 base.json 에 넣은 뒤, 이 서비스의 은유·시그니처 디테일을 **덧붙여** 고친다(색은 서비스 사정에 맞게 바꿔도 된다). 엔진 부품을 전부 이 서비스의 모양으로 다시 입힌다. `.app` 아래로만. 걸 수 있는 곳:
   `.h1 .sec b .card .li .dot .badge .b-warn/.b-ok/.b-info/.b-muted .btn .btn.p .banner .tone-* .hero .stat .tl .tli .cardi .tile .chip .seg .utabs .tabbar a .side-nav .topnav .empty .quote .poster .bign .car .map .pin .sheet .fld .in .cal span .bub` · 변수 `--bg --surface --ink --muted --line --accent --r --gap --pad` · PC 는 `@container (min-width:900px){…}` · 블록에 `"cls"` 로 이름표.
4. **대표 화면은 직접 그린다** — 역할별 홈·첫 화면 2~4장은 블록 대신 `design/app/screens/<id>.html`(HTML 조각, 스크립트 금지). `style.css` 클래스와 변수만 쓴다. 링크는 `href="#화면id"`, 그림은 `src="gen:키워드:숫자"`. PC 는 컨테이너 쿼리로. 같은 id 의 `screens/<id>.json` 에는 id·title·role·icon·features·layout 만.
5. **뻔함 금지(개성 없는 결과의 신호)**: 흰 둥근 카드 목록만 반복 · 모든 배지가 같은 알약 · 도메인 상징 아이콘 하나 크게 박은 연한 색 카드(하트·비행기 D-day 카드) · 요약 통계 칸을 홈 맨 위에 · 기본 그림자 · 버튼이 전부 같은 모양 · 제목·본문 같은 글꼴 같은 굵기.
6. **비평 한 바퀴**: 전체를 그린 뒤 서브 에이전트 1개에게 폰·PC 대표 화면 캡처 4장을 보여 주고 "템플릿처럼 보이는 곳 5개와 고칠 CSS/HTML" 을 받는다 → 적용 → 다시 그림. 사용자에게 묻지 않는다.

## 질문 페이지를 만드는 법 (모든 워크플로우 공통)

- **취향은 사용자가 말로 설명하게 하지 않는다**(사용자는 디자인 초보 — 좋아하는 브랜드·색을 묻지 않는다). 하네스가 스타일 라이브러리로 성격이 다른 후보를 **그림으로** 보여 주고 고르게 한다.

- **전문가가 먼저 판단한다.** "무엇을 원하세요?" 가 아니라 "저는 이게 맞다고 봅니다(이유). 대안은 이것들입니다." 추천 1개에 `recommend`. 사용자가 아무것도 안 바꾸고 [답 복사]만 눌러도 좋은 결과가 나와야 한다.
- 묻는 것은 **취향과 방향뿐**. 기능 목록·기술·로그인 방식처럼 전문가가 정할 것은 묻지 않는다.
- **항상 그림으로.** pick 의 모든 선택지에 실제로 그린 화면(`img`, 가능하면 `img2` PC). 글만 있는 선택지 금지. 선택지 3~5개, 서로 **한눈에 다르게**(색만 바꾼 변형 금지 — 구성·정보 형태·밀도 중 둘 이상이 달라야).
- 한 페이지 items 는 3개 이하. 쉬운 말. 전문 용어(온보딩·CTA·대시보드·UX·컴포넌트) 금지.
- **재검증**: 사용자 답을 그대로 믿지 않는다. 같은 주제를 다른 각도로 확인하는 항목을 같은 페이지나 다음 페이지에 둔다(예: 고른 방향을 "작은 폰·큰 글자에서는 이렇게 보여요" 그림으로 다시 보여주고 맞는지 assume/check 로).
- `lead` 는 2~3문장: 지금까지 한 일, 이해한 핵심, 지난 답을 어디에 반영했는지.

## 전체 화면을 만드는 법 (속도 — 30분 안에)

1. 메인이 먼저 `design/brief.md`(핵심 갈등 한 문장·역할·기기 가정·기능 F목록·필수 흐름·가정·확정된 결정·디자인 토큰과 그 이유)와 `design/app/base.json`(order 에 화면 목록 전부)을 쓴다. **화면 목록 = 이름·역할·목적 한 줄·features.**
2. **서브 에이전트를 한 응답 안에서 한꺼번에(포그라운드)** 띄운다. 에이전트 하나 = 화면 3~5장. 지시문은 짧게: "`design/brief.md` 와 `design/app/base.json` 을 읽고, 아래 화면들을 `design/app/screens/<id>.json` 에 화면 JSON 으로 써라(형식: SKILL.md '도구'). 그리거나 다른 파일을 읽지 마라. 화면 목록: …". 에이전트에게 SKILL.md 의 블록 요약 줄을 그대로 붙여 준다.
3. 끝나면 메인이 `python scripts/app.py design/app` 한 번 → `coverage.py` → `shots.py app` → 눈으로 검사 → 고치기.
4. 금지: 스크립트 파일 읽기 · 긴 HTML 직접 쓰기 · 에이전트를 하나씩 띄우기 · 기다리는 동안 상태 확인 명령 · localhost 주소 지어내기.
5. 질문과 무관한 공통 작업(기능 목록·화면 목록·내용 데이터·레퍼런스)은 **질문하기 전에** 끝내 둔다 — 답을 받은 뒤에는 답에 따라 달라지는 일만 남게.

## 시간 예산 (PRD 입력 → 완료, 사람 답 시간 포함 30분)

| 구간 | 목표 |
|---|---|
| 첫 질문 페이지까지 | 5분 이내 |
| 답 받고 다음 질문 페이지까지 | 3분 이내 |
| 전체 화면 생성(에이전트 동시) | 8분 이내 |
| 검사·고치기 | 4분 이내 |

## 산출물

`design/brief.md` · `design/decisions.md`(질문마다 답 코드 원문·풀이·반영 위치) · `design/ask/q<n>.json|html|png` · `design/cand/` · `design/app/`(base.json·screens/·app.json·app.html·index.html) · `design/shots/`.
`base.json` 의 `decisions` 에 질문마다 {q, answer(풀이), where(반영 화면)} 을, `tour` 에 역할을 오가는 따라가 보기 8~12단계(각 단계 device m/d 지정)를 넣는다.
