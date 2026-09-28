# 화면 조각 작성 규칙 (screen-writer가 가장 먼저 읽는다)

당신은 **조립**만 한다. 디자인 판단은 이미 `screens.json`에 끝나 있다. 이 폴더의 조각(snippets)을 그대로 복사해 문구만 바꿔 화면을 만든다.

## 반드시 지킬 것

1. **파일은 `<body>` 안쪽 내용만.** `<html> <head> <body> <style> <script> <link>` 금지. 루트는 `<div class="app">` 하나.
2. **클래스는 이 폴더 조각에 있는 것만.** 새 클래스·인라인 `style=` 금지. 스타일이 부족하면 만들지 말고 가장 가까운 조각을 쓴다. (lint가 잡는다)
3. **영역 표시**: `screens.json`의 `regions[].key`마다 그 영역을 감싸는 요소 하나에 `data-region="<key>"`를 붙인다. 화면당 한 key는 정확히 한 번. 빠지거나 남으면 lint 실패.
   - 영역은 사용자가 "7번 바꿔주세요"라고 가리킬 단위다. 버튼 하나보다 **의미 있는 덩어리**(목록 전체, 카드 한 장, 상단 요약 띠, 우측 패널)에 붙인다. 너무 작으면 배지가 겹친다.
3-1. **트리거 표시**: `flow.json`에서 이 화면이 `from`인 step마다, 그 step의 `trigger` key를 **실제로 누르는 요소 하나**(버튼·링크·탭·목록 항목)에 `data-trigger="<key>"`로 붙인다. 그 요소는 step의 `region` 영역 안에 있어야 한다. 누를 요소가 조각에 없으면 그 영역 안에 버튼을 만든다(문구는 step의 `action` 따옴표 안 말). 화살표가 여기서 출발한다.
3-2. **버튼마다 누르면 어떻게 되는지**: 글자가 있는 `.btn`(아이콘만 있는 `.btn-icon`과 `.nav-item` 제외)은 셋 중 하나를 반드시 가진다 — lint FAIL.
   - `data-trigger="<key>"`: flow.json의 step이나 **branches(갈래)** 에 있는 버튼. 다른 화면·창이 열린다.
   - `data-back`: 이전 화면으로 돌아가는 버튼(취소·닫기·'모임으로' 같은 뒤로가기, 창의 완료 버튼).
   - `data-stay="바뀐 뒤 안내 문구"`: 그 자리에서 바뀌는 버튼(삭제·필터·다시 알리기·복사). 문구는 해요체 한 문장("알림을 다시 보냈어요"). 최종본에서 누르면 이 문구가 잠깐 뜬다.
4. **아이콘**: `<svg class="icon" aria-hidden="true"><use href="#i-<lucide-name>"/></svg>`. 크기는 `.icon-sm`(16) `.icon`(20) `.icon-lg`(24). 이름은 `packages/core/icons/allowlist.json` 값 또는 프로젝트 `icons.json` 값만. 아이콘만 있는 버튼은 `aria-label` 필수.
5. **문구는 전부 실제 문구.** PRD 도메인의 그럴듯한 데이터(이름·날짜·장소·금액)를 쓴다. "버튼"·"텍스트"·"제목"·Lorem ipsum 금지. 비어 보이는 목록은 최소 3~5행을 채운다.
6. **프레임은 1280×800 고정.** `.app`이 프레임을 채우고 `.content`만 내부 스크롤한다. 첫 화면(above the fold)에 핵심이 보이게 배치한다.
7. **상태 표시는 `.badge`로 통일**한다 (예: 확정 = `badge-success`, 후보 = `badge-neutral`, 변경됨 = `badge-warning`). 같은 의미에 같은 색.
8. **화면당 primary 버튼은 1개**(`.btn-primary`). 나머지는 secondary/ghost.
9. 패턴 파일(`packages/web/patterns/<pattern>.html`)에서 시작한다. `<!-- slot: … -->` 자리를 조각으로 채우고 주석은 지운다.
10. 완성 후 스스로 점검: data-region 개수 = screens.json 영역 개수 / 이 화면이 from인 step의 trigger가 모두 `data-trigger`로 있음 / 아이콘 이름 allowlist 확인 / `style=` 없음 / Lorem 없음.
11. **사이드바·상단바는 `screens.json`의 `roles[].nav`를 그대로 옮긴다.** 항목 순서·라벨·아이콘을 바꾸지 않고, 현재 화면 항목에만 `.active`. 상단바 제목은 `screens.json`의 `title`. 화면마다 내비가 달라지면 안 된다.
11-1. **메뉴 구조(시안의 shell)**: 기본은 왼쪽 메뉴(`.sidebar`). 프롬프트에 `SHELL=nav-top`이면 `<div class="app nav-top">` + 상단바 안 `<nav class="topnav-nav">`에 같은 `.nav-item`들(사이드바 없음), `SHELL=nav-rail`이면 `<div class="app nav-rail">` + 사이드바는 그대로(좁은 아이콘 메뉴로 보인다). 골격은 `patterns/shell-top.html`·`shell-rail.html`, 설명은 10-layout "app 변형". `.nav-item` 클래스 이름은 바꾸지 않는다.
12. **영역을 나누기 위한 클래스 없는 `<div data-region="…">` 래퍼는 허용**된다(스타일이 필요 없는 순수 묶음). 단 `.stack`/`.section`처럼 간격이 필요하면 그 클래스를 쓴다.
13. **뜨는 창 화면**(`screens.json`에 `overlayOf`가 있음): 파일 전체가 `<div class="modal-backdrop">…</div>` 하나다. 뒷 화면은 쓰지 않는다 — build가 `overlayOf` 화면을 깔고 그 `.app`의 마지막 자식으로 창을 넣는다. 영역은 `.modal`(또는 `.drawer`)에 붙인다. backdrop에는 붙이지 않는다.
14. **primary 버튼은 화면당 최대 1개.** 주 행동이 없는 읽기 전용 화면은 0개여도 된다. 모달이 열려 있으면 모달 안 primary가 그 화면의 유일한 primary다.
15. 달력 격자는 손으로 쓰지 않는다. 메인이 `node scripts/calendar.js`로 만들어 준 `runs/<p>/snippets/calendar-*.html`을 그대로 붙인다. 없으면 `.day-strip`이나 `.timeline`으로 대신한다.
16. `.day-strip`은 행사 기간 앞뒤로 며칠을 채워 7일 이상으로 만들고, 기간 밖은 `.is-muted`.
17. **처음 켰을 때·데이터 없을 때 화면**(`screens.json`의 `state`가 `first-run`·`empty`): 숫자 카드·목록을 채우지 않는다. 가운데에 `.empty` 조각(아이콘 · "아직 ○○이 없어요" · 무엇부터 하면 되는지 한 줄 · primary 버튼 하나). 보기만 하는 역할의 빈 화면은 버튼 없이 "정해지면 알려 드릴게요"처럼 안심시키는 문장. `state: input`(등록 화면)은 입력칸에 예시 값을 채운다.
18-1. 할 일·체크리스트처럼 **보고 체크하는 목록**은 체크박스(input) 대신 아이콘으로: 한 것 `<svg class="icon text-success"><use href="#i-square-check"/></svg>` + 흐린 글자, 안 한 것 `<svg class="icon text-muted"><use href="#i-square"/></svg>`. 여러 열을 나란히 두는 화면은 **열 머리 구조를 모두 같게**(아바타 · 이름 truncate · spacer · 배지), 머리에 버튼을 넣지 않는다(열 위 도구줄로).
18. 화면 안 문구도 `.claude/skills/design-harness/references/ux-writing.md`를 따른다: 높여 부를 사람은 "님"(예: 부모님·고객님), 버튼 문구는 flow의 `action` 따옴표 안 말과 글자까지 같게.

## 조각 목록

| 파일 | 내용 |
|---|---|
| 10-layout.md | app · topnav · sidebar · content · page-header · toolbar · section · grid · split · stack/row |
| 20-buttons.md | btn 변형·크기·아이콘 · btn-icon · 버튼 그룹 |
| 30-inputs.md | field · input · select · textarea · checkbox · radio · switch · segmented · search |
| 40-display.md | card · badge · chip · avatar · tabs · breadcrumb · progress · stat · empty · skeleton · divider · banner · toast · tooltip · kbd |
| 50-data.md | list · table · timeline · steps · calendar · day-strip |
| 60-overlay.md | modal · drawer · dropdown · popover |
