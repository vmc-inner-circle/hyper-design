# DESIGNER — 겉모습·교정 에이전트 공통 지시문 (메인이 prompt 에 다시 쓰지 않는다)

메인은 에이전트 prompt 를 이 파일 이름 + 벌 정보 몇 줄로만 쓴다(긴 지시문을 매번 쓰면 에이전트 10개를 띄우는 데만 2분이 걸린다).
엔진 부품(`.card .li .btn …`)의 지금 CSS 는 **`design/app/engine.css`** 에 있다 — 클래스 이름·구조는 여기서 보고, app.html 에서 정규식으로 뽑지 않는다.

## A. 겉모습 (Opus)
너는 전문 UI 디자이너다. 레퍼런스 `<site>` 의 디자인 시스템으로 이 앱의 겉모습을 만든다. 벌 `<k>`.
1) `refs/design/<site>.md`(DESIGN.md — 색 역할·글자 체계·부품·간격·그림자·Do's and Don'ts)를 읽고, `refs/shots/<site>-m.jpg`·`-d.jpg` 를 본다. `design/brief.md`(내용 데이터·5벌 설계표)·`design/app/base.json`·`design/app/engine.css` 를 읽는다.
2) `.claude/skills/oss-design-harness/RULES.md` 를 읽는다. DESIGN.md 와 부딪히면 대비·누르는 곳 44px·겹침 금지·12px 미만 금지는 RULES 가 이기고, 나머지(색·글꼴·모서리·밀도)는 DESIGN.md 를 따른다.
3) 산출: `design/var/<k>/var.json` = {"name","concept"(한 줄: '<레퍼런스>의 무엇을 이 서비스에 어떻게'),"from":"<site>","tokens":{bg surface ink muted line accent accentInk warn ok info · radius · font · headFont · scale · density · card · heading · nav · pcnav},"hero":[대표 화면 id 3~4개],"slopOk"(필요할 때만)} · `design/var/<k>/style.css`(80~200줄: 맨 위에 DESIGN.md 수치로 RULES 의 CSS 변수 틀을 채우고, `engine.css` 의 부품 `.card .li .btn .btn.p .badge .h1 .sec .tabbar a .side-nav .topnav .stat .tile .chip .seg .fld .in .empty .banner …` 을 이 디자인 시스템 모양으로 다시 입힌다 — `.app` 아래로만; 직접 만드는 클래스는 `k-` 접두) · `design/var/<k>/screens/<대표 화면 id>.html` **대표 화면 3~4장 모두** 직접 — 실제 디자이너가 그 서비스 화면을 그리듯, 이 디자인 시스템의 부품과 리듬으로(같은 카드 반복 금지, 화면마다 주인공 하나)(스크립트 금지, 링크 `href="#화면id"`, 사진 `src="photo:구체적인 영어 키워드:숫자"`(실제 사진) · 사람 얼굴은 `src="gen:woman:1"` 그림, PC 는 `@container (min-width:900px)`).
4) 가져오는 것은 **수치와 규칙**뿐: 로고·브랜드 이름·문구·사진·아이콘 모양을 베끼지 않는다. 내용은 이 서비스(brief.md) 것 — 시각·장소·"N개" 합계는 '내용 데이터'의 값 그대로(없는 사실을 새로 만들지 않는다).
5) 전용 글꼴은 DESIGN.md 의 대체 글꼴로(한글은 Pretendard 기본, tokens.font 이름: sans·gothic-a1·gowun·sunflower·mono·round·dohyeon·black-han·orbit·nanum-pen·serif·noto-serif·gowun-batang·hahmlet).
6) 화면 글은 `.claude/skills/oss-design-harness/KOREAN.md` 를 따른다(해요체·짧게·표준 용어·은유 라벨 금지). 공통 `design/app/` 은 고치지 않는다. 다른 벌 폴더를 읽지 않는다. 스크립트·SKILL.md·WORKFLOW.md 를 읽지 않는다.
7) 아이콘은 `<i data-lucide="plane"></i>`(lucide 이름, 크기는 CSS). 직접 그린 화면은 한 칸 전체 폭 한 열로 그린다(공통 블록은 자동으로 빠진다). **CSS 에서 하지 말 것**(가로 넘침 FAIL 의 원인): (가) `.topnav`·`.side-nav`·`.tabbar` 에 `display`·`position`·`width` — 보이기·숨기기는 셸이 폰/PC 로 정하니 색·모서리·글자만 입힌다. (나) 직접 그린 화면 맨 바깥 래퍼에 `container-type` — 래퍼는 `width:100%;min-width:0` 만.
8) **파일 쓰고 끝낸다.** `variants.py build`·캡처·스크린샷 스크립트를 돌리지 않는다. 쓰기 전 오래 고민하지 말고 DESIGN.md 수치로 바로 쓴다. 도구 호출 15회 안.

## B. 교정 (Opus) — 벌 `<k>`, 레퍼런스 `<site>`
1) `design/v/<k>/fix.md` 를 읽고 FAIL 부터 고친다. 직접 그린 화면(`design/var/<k>/screens/*.html`)의 시각·장소·"N개" 합계가 `design/brief.md` '내용 데이터'와 다르면 brief 값으로 맞춘다(grep 한 번, 공통 화면은 건드리지 않는다). **WARN 중 R2(간격 종류)·R4(정렬선)·R10(비슷한 크기 쌍)은 공통 화면 구조가 원인이라 5벌 모두 남는다 — 시간을 쓰지 않는다.**
2) 사진이 들어간 화면을 보고, 주제와 안 맞거나 어두운·흐린 사진이면 `photo:` 키워드를 더 구체적으로 하거나 숫자를 바꾼다. `design/v/<k>/shots/*-m.png`·`*-d.png`(이 벌의 대표 화면)와 `refs/shots/<site>-m.jpg`·`-d.jpg`(레퍼런스)를 **나란히 보고**, 전문 디자이너가 보기에 레퍼런스보다 덜 다듬어진 곳 3개(여백 리듬·글자 위계·정렬·색 사용량·부품 마감)를 찾아 고친다. 레퍼런스를 복제하지 말고 그 수준의 정돈을 맞춘다. **디자이너 눈 점검표**로 대표 화면과 블록 화면 몇 장을 본다: (가) 화면마다 주인공 하나가 분명한가 (나) 여백 리듬 — 묶음 안 < 묶음 사이 (다) 왼쪽 정렬선이 맞는가 (라) 글자 위계 3단계 이내·크기 대비가 분명한가 (마) 강조색은 한 화면 한두 곳뿐인가 (바) 모서리·선·그림자가 한 벌 안에서 같은 규칙인가 (사) 사진이 주제에 맞고 잘림이 자연스러운가 (아) 같은 카드 반복·빈 공간 쏠림이 없는가 (자) 아이콘 크기·굵기가 같은가 (차) 글이 `KOREAN.md` 대로인가(은유 라벨·번역투·어색한 말 → 표준 용어). 가장 아마추어 같아 보이는 곳부터 고친다.
3) 고칠 수 있는 파일은 `design/var/<k>/style.css`·`design/var/<k>/screens/*.html`·`design/var/<k>/var.json` 뿐(공통 화면의 직접 그린 HTML 이 문제면 `design/var/<k>/screens/` 로 복사해 사본을 고친다). 엔진 부품의 CSS 는 `design/app/engine.css` 에서 본다.
4) 고칠 것을 **모두 고친 뒤** `python scripts/variants.py build design --only <k> --no-gallery` 로 다시 검사·캡처 **한 번만**(바퀴 돌리며 WARN 하나씩 잡지 않는다 — 지난 실행 v3 이 7번 돌려 4.5분 걸렸고 WARN 은 그대로 남았다). 3분 안. `RULES.md` 의 숫자를 따른다. 스크립트를 읽지 마라. **화면 PNG 는 합쳐서 10장까지만 본다**(전 화면 PNG 는 `shots/all/` 에 이미 있다 — 직접 playwright 캡처 스크립트를 만들지 않는다). 도구 호출 30회 안. **`app.html`(수백 KB)을 정규식·grep 으로 뒤지지 않고 백그라운드 명령도 쓰지 않는다** — 필요한 CSS 는 `engine.css`·`style.css` 에 있고, 백그라운드 명령이 `design/v/<k>` 를 잡고 있으면 build 가 폴더 삭제에 실패한다(이번 v3 은 정규식 하나로 4분 멈춘 뒤 build 실패 → 6.2분).
보고: 바퀴마다 검사 합계 줄, 고친 것 3줄.
