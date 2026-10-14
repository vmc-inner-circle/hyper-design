# 칸 사전 — screens.json · flow.json

> `node scripts/schema.js --docs`가 정본 스키마(packages/core/schema/)에서 만든다. 손으로 고치지 않는다.
> 상태: ✔ 쓰는 칸 · ○ 제안 · ✕ 옛 칸(받되 경고, 다음 판에서 지움). 필수: 필수 · 권장(없으면 경고, 다음 판에서 필수).
> 단계는 그 칸을 쓰는 생성 단계 — 칸에 따로 적힌 단계(굵게)가 객체 단계보다 앞선다.

## screens.json (v1)

정본. 객체(x-object)마다 하나의 정의($defs)와 층(x-layer: 의도 · 성격 · 화면 · 공통 · 실행 상태). 다른 객체를 가리키는 칸은 x-ref — 문자열이면 문서 전체에서, {to, within}이면 범위(screen 같은 화면 · from 흐름 단계의 출발 화면 · role 같은 역할 · theme 고른 분위기) 안에서 찾는다. 하나뿐이어야 하는 칸은 x-unique — 범위 doc(문서 전체) · screen(같은 화면) · look(같은 분위기). 옛 모양과만 생기는 어긋남은 x-ref의 warnWith(그 옛 칸이 함께 있을 때만 경고)로 적는다. 권장 · 규칙은 같은 폴더 rules.json — 칸의 x-rules가 규칙 id를 가리킨다. 생성은 단계별(x-stage: S1 의도 · S2 여정 · 화면 목록 · S3 화면 하나씩 · S4 성격 · S5 시안 · 하네스) — 칸의 x-stage가 객체 단계보다 앞선다. x-recommended는 지금은 권장(없으면 경고), 다음 판에서 필수. x-status legacy는 옛 칸 · 옛 값 — 받되 경고하고 다음 판에서 지운다.

| 칸 | 상태 | 필수 | 단계 | 뜻 | 관계 · 규칙 · 읽는 곳 | 칸이 왜 있나 |
|---|---|---|---|---|---|---|
| `project` | ✔ | 필수 | **S1 의도** | 실행 이름 | build · 보드 |  |
| `title` | ✔ | 필수 | **S1 의도** | 서비스 이름 | build · expand · 보드 |  |
| `brand` | ✔ |  | **S1 의도** | 서비스 이름 — 보드 · 상단바에 보이는 이름(대표색 looks[].palette.brand와 다른 칸) | expand · 보드 |  |
| `brandIcon` | ✔ |  | **S1 의도** | 상단바 서비스 아이콘(없으면 layout-dashboard) | expand |  |
| `platform` | ✔ | 필수 | **S1 의도** | 웹 · 모바일 — 값: web · mobile | `shell-platform` · expand · lint · build |  |
| `round` | ✔ | 필수 | **하네스** | 0 = 1턴 시안 보드, 1 = 2턴 초안 1, 이후 의견마다 +1 | build · 보드 |  |
| `stage` | ✔ |  | **하네스** | 1턴 시안 단계에만, 2턴에 지운다 | build · 보드 |  |
| `concept` | ✔ |  | **하네스** | 고른(추천) 시안 id | → `concept.id` · build · 보드 |  |
| `theme` | ✔ |  | **하네스** | 지금 분위기 = looks[].id | → `look.id` · build · looks |  |
| `shell` | ✕ |  |  | 뺌 — 메뉴 틀은 concepts[].shell |  |  |
| `toggles` | ✔ |  | **하네스** | 보드에서 고른 글자 크기 · 버튼 색 | build · 보드 |  |
| `toggles.type` | ✔ |  | 하네스 | 고른 글자 크기 보통 · 크게 — 값: normal · large | build · 보드 |  |
| `toggles.swatch` | ✔ |  | 하네스 | 고른 버튼 색 = 지금 분위기(theme)의 swatches[].id 또는 brand(대표색) | → `look.swatches.id (theme 안) ∪ brand` · build · looks · 보드 |  |
| `toggles.toast` | ✔ |  | 하네스 | 고른 안내 문구 모양 — 보드 '안내 문구 모음' | build · 보드 |  |
| `toggles.toast.at` |  |  | 하네스 | 위치 — 화면 위 · 아래 — 값: top · bottom |  |  |
| `toggles.toast.icon` |  |  | 하네스 | 아이콘 있음 · 없음 — 값: on · off |  |  |
| `toggles.toast.tone` |  |  | 하네스 | 흰 바탕 · 어두운 바탕 · 상태 색 바탕 — 값: light · dark · color |  |  |
| `toggles.toast.size` |  |  | 하네스 | 글자 보통 · 크게 — 값: normal · large |  |  |
| `toggles.accent` | ✕ |  | 하네스 | 뺌 — 버튼 색은 swatch |  |  |
| `facts` | ✔ |  | **S1 의도** | 모든 화면 공통 사실 — 이름표(키) → 사실 한 줄. 사실이 사는 유일한 곳. screens[].data가 이름표로 가리킨다 | `data-key-exists` | 사실이 사는 유일한 곳 — 화면들은 이름표로 가리켜 같은 사실을 같은 문장으로 쓴다 |
| `purpose` | ✕ |  | **S1 의도** | 뺌 — 분야 사실은 facts로 |  |  |
| `purpose.domain` | ✕ |  | S1 의도 | 이 분야에서 꼭 챙길 것 (예: 확정과 후보를 한눈에 가른다) — 기준어 from이 가리킨다 |  |  |
| `purpose.domain[].id` | ✕ |  | S1 의도 | 항목 id(기준어 from이 가리킴) |  |  |
| `purpose.domain[].what` | ✕ | 필수 | S1 의도 | 챙길 것 한 줄 |  |  |
| `purpose.domain[].prd` | ✕ | 필수 | S1 의도 | PRD 근거 |  |  |
| `purpose.conflict` | ✕ |  | S1 의도 | 뺌 — 장면(scene) · DESIGN.md Overview가 담는다. 새로 쓰지 않는다 |  |  |
| `purpose.conflict.text` | ✕ | 필수 | S1 의도 | 갈등 한 줄(옛 칸) |  |  |
| `purpose.conflict.prd` | ✕ |  | S1 의도 | 근거(옛 칸) |  |  |
| `purpose.users` | ✕ |  | S1 의도 | 옛 칸 — roles[]로 합쳤다. 새로 쓰지 않는다 |  |  |
| `purpose.problem` | ✕ |  | S1 의도 | 옛 칸 — 아무도 가리키지 않음 |  |  |
| `purpose.scope` | ✕ |  | S1 의도 | 옛 칸 — 아무도 가리키지 않음 |  |  |
| `purpose.constraints` | ✕ |  | S1 의도 | 옛 칸 — 아무도 가리키지 않음 |  |  |
| `roles` | ✔ | 필수 | **S1 의도** | 역할 = 사용자 유형 | `roles-count` |  |
| `roles[].key` | ✔ | 필수 | S1 의도 | 역할 id. 다른 칸이 사람을 가리킬 때는 이것을 쓴다 (screens[].role · mood.keywords[].from) | 하나뿐(doc) |  |
| `roles[].label` | ✔ | 필수 | S1 의도 | 보드에 보이는 이름 (예: 부모님) | 보드 · pack · expand |  |
| `roles[].nav` | ✔ |  | **S2 여정 · 화면 목록** | 이 역할의 메뉴 — 모든 화면 셸이 그대로 복사한다. 화면 목록과 함께 S2에서 | `nav-count` · expand | 모든 화면의 메뉴가 같아야 화면 사이에서 길을 잃지 않는다 |
| `roles[].nav[].slug` | ✔ | 필수 | S2 여정 · 화면 목록 | 이 메뉴가 여는 화면 | → `screen.slug (role 안)` · expand |  |
| `roles[].nav[].label` | ✔ | 필수 | S2 여정 · 화면 목록 | 메뉴 이름(화면 이름보다 짧게) | expand |  |
| `roles[].nav[].icon` | ✔ |  | S2 여정 · 화면 목록 | 아이콘 이름 | expand |  |
| `roles[].user` | ✔ |  | S1 의도 | 셸 오른쪽 위에 보일 사람 | expand |  |
| `roles[].user.name` |  |  | S1 의도 | 이름 |  |  |
| `roles[].user.initials` |  |  | S1 의도 | 줄임 이름(아바타) |  |  |
| `roles[].goal` | ✔ | 권장 | S1 의도 | 이 사람이 서비스로 이루려는 것 한 문장 — 화면마다 goal이 여기서 나온다 | 보드 · 생성 → screens[].goal | 화면마다 무엇을 가장 크게 보여 줄지(1순위)가 이 목표에서 나온다 · KRDS 원칙 1 — https://www.krds.go.kr/html/site/utility/utility_02.html |
| `roles[].frequency` | ✕ |  | S1 의도 | 뺌 — 읽는 곳 없음(규칙 · 조립 · 다음 칸 모두 0). KRDS 원칙 1의 '빈도'는 칸이 아니라 생각 순서(지침)로 — 결과는 screens[].problem · 영역 수에 남는다 |  | KRDS 원칙 1 — https://www.krds.go.kr/html/site/utility/utility_02.html |
| `roles[].difficulty` | ✕ |  | S1 의도 | 뺌 — 읽는 곳 없음 · screens[].problem과 겹침 — 화면에 닿는 것은 화면별 겪는 문제 |  | KRDS 원칙 1 — https://www.krds.go.kr/html/site/utility/utility_02.html |
| `roles[].inclusion` | ✔ | 권장 | S1 의도 | 포용 조건 — 나이 · 기기 · 읽는 상황. 글자 크기 추천(board.recommend.type)의 근거 | 보드 · 생성 → board.recommend.type | 나이 · 기기 · 읽는 상황이 글자 크기 추천의 근거가 된다 — 근거(inclusion) → 추천(board.recommend.type) → 결정(toggles.type) · KRDS 원칙 2 모든 사용자 포용 — https://www.krds.go.kr/html/site/utility/utility_02.html |
| `roles[].prd` | ✕ |  | S1 의도 | 뺌 — PRD 근거는 brief.md 가정 로그 한 곳에 — 칸마다 PRD를 다시 옮기지 않는다 |  |  |
| `sections` | ✔ | 권장 | **S2 여정 · 화면 목록** | 구역 — 사용 흐름(구역 보드)의 큰 띠. 2~6개, 사용자가 하는 일로 이름 짓는다 | `sections-count` | 화면을 큰 구역 → 단계 이름표 → 화면 순서로 나란히 놓아야 사람이 서비스 전체 흐름을 한눈에 본다 · KRDS 서비스 패턴 — 여정 단계 기반(https://www.krds.go.kr/html/site/service/service_summary.html) |
| `sections[].key` | ✔ | 필수 | S2 여정 · 화면 목록 | 구역 id — screens[].section이 가리킨다 | 하나뿐(doc) |  |
| `sections[].name` | ✔ | 필수 | S2 여정 · 화면 목록 | 하는 일을 일상어로 12자 이내 (예: 처음 시작하기) | `sections-count` · build · 보드 |  |
| `sections[].desc` | ✔ | 필수 | S2 여정 · 화면 목록 | 구역 띠에 보이는 한 줄 40자 이내 — 여기서 무엇을 하는지 | build · 보드 |  |
| `screens` | ✔ | 필수 | **S3 화면 하나씩** | 화면 목록 — 사용자가 만나는 순서. 화면 id · 이름 · 역할은 S2 화면 목록에서, 나머지는 S3에서 화면 하나씩 | `primary-action-one` |  |
| `screens[].id` | ✔ |  | S3 화면 하나씩 | 화면 번호 — ids.js가 사용자가 만나는 순서로 | `ids-range` |  |
| `screens[].slug` | ✔ | 필수 | **S2 여정 · 화면 목록** | 화면 id — 흐름 · 메뉴 · 시안이 가리킨다 | 하나뿐(doc) |  |
| `screens[].name` | ✔ | 필수 | **S2 여정 · 화면 목록** | 화면 이름 | 보드 · pack · build |  |
| `screens[].role` | ✔ | 필수 | **S2 여정 · 화면 목록** | 이 화면이 누구를 위한 것인가 = roles[].key | → `role.key` · expand · build | 화면마다 누구의 화면인지 알아야 그 사람의 목표로 1순위를 정한다 |
| `screens[].section` | ✔ | 권장 | S3 화면 하나씩 | 이 화면이 놓일 구역 = sections[].key | → `section.key` · `sections-count` · build · lint · 보드 |  |
| `screens[].step` | ✔ | 권장 | S3 화면 하나씩 | 화면 위 단계 이름표 14자 이내 (예: 약관 동의) — 같은 단계 화면은 같은 이름표, screens.json에서 붙여 둔다 | `step-label` · build · lint · 보드 |  |
| `screens[].file` | ✔ |  | S3 화면 하나씩 | 조각 파일 경로 (screens/<slug>.html) | build · expand · lint |  |
| `screens[].goal` | ✔ | 권장 | S3 화면 하나씩 | 이 화면에서 사용자가 이루는 것 한 문장(동사로 끝남) — 모든 화면(처음 시작 · 뜨는 창 포함). roles[].goal의 한 조각이고, problem은 그 이유, emphasize는 그 답 | 생성 → screens[].emphasize · pack · 보드 | 뜨는 창 · 처음 시작 화면까지 모든 화면에 목적 한 문장이 있으면, 1순위 문장이 목적을 실제 사실로 말하게 된다 · KRDS 서비스 패턴 — 여정 단계마다 화면(https://www.krds.go.kr/html/site/service/service_summary.html) · KRDS 서비스 메인에서 시급·중요 정보를 빨리(필수) |
| `screens[].problem` | ✔ | 권장 | S3 화면 하나씩 | 이 화면에서 사용자가 겪는 문제 한 줄 — 모든 화면 | `emphasize-fact` · pack · 보드 | 사용자가 이 화면에서 겪는 걱정을 알면 1순위 문장이 그 걱정에 답하는 사실이 된다(KRDS 원칙 1 — 여정 중 겪는 문제) · KRDS 원칙 1 주요 방안 2 — 여정 중 겪게 되는 문제를 분석하고 해결(https://www.krds.go.kr/html/site/utility/utility_02.html) |
| `screens[].pattern` | ✔ | 권장 | S3 화면 하나씩 | 이 화면이 무슨 일을 하는 화면인가 — KRDS 패턴 이름(기본 · 서비스) 또는 사례 '처음 시작'. 배치는 정하지 않는다 — 값: 입력폼 · 목록 탐색 · 상세 정보 확인 · 확인 · 오류 · 도움 · 동의 · 필터링·정렬 · 사용자 피드백 · 첨부파일 · 개인 식별 정보 입력 · 방문 · 검색 · 로그인 · 신청 · 정책 정보 확인 · 처음 시작 · form(옛 값) · list-detail(옛 값) · dashboard(옛 값) · timeline(옛 값) · onboarding(옛 값) · board(옛 값) · settings(옛 값) | `pattern-krds` · pack · lint | KRDS 패턴 이름으로 부르면 그 패턴의 규칙(한 열 입력 · 창 안 입력 5개 이내 …)을 그대로 설명할 수 있다. 배치는 정하지 않는다 · KRDS 기본 패턴 12 — https://www.krds.go.kr/html/site/global/global_summary.html · 서비스 패턴 5 — https://www.krds.go.kr/html/site/service/service_summary.html. '확인'은 원문 미수집 ✕ |
| `screens[].purpose` | ✕ |  | S3 화면 하나씩 | goal로 이름을 바꿈 — 새로 쓰지 않는다(다음 판에서 지움) |  |  |
| `screens[].state` | ✔ |  | S3 화면 하나씩 | 상태 화면 — first-run 처음 · empty 빈 상태 · input 입력 중 · error 오류 · success 완료. error · success는 variantOf(원래 화면) 필수 — 값: first-run · empty · input · error · success | `state-pair` · build · lint · 보드 |  |
| `screens[].when` | ✔ |  | S3 화면 하나씩 | 이 상태 화면이 나오는 조건 — state가 error · success일 때만 (예: "돌아오는 날을 안 적고 눌렀을 때"). cases[].when(문구가 뜨는 때) · 흐름 step.when(갈래 이름표)과 다른 칸 | `state-pair` · build · 보드 |  |
| `screens[].variantOf` | ✔ |  | S3 화면 하나씩 | 상태 화면(빈 · 오류 · 완료 …)이 변형한 원래 화면 slug — 같은 역할, 자기 자신 · 변형의 변형은 안 된다 | → `screen.slug (role 안)` · `variant-target` · 보드 · build |  |
| `screens[].overlayOf` | ✔ |  | S3 화면 하나씩 | 뜨는 창 화면의 뒷 화면 slug — 이름은 '~ 창'. 뜨는 창은 흐름 · 갈래의 도착(to)이어야 한다 | → `screen.slug (role 안)` · `variant-target` · `overlay-reached` · build |  |
| `screens[].navActive` | ✔ |  | S3 화면 하나씩 | 메뉴에 없는 화면에서 켜 둘 메뉴 항목 slug | → `screen.slug (role 안)` · expand |  |
| `screens[].shell` | ✔ |  | S3 화면 하나씩 | 이 화면만 다른 메뉴 틀 — 플랫폼별 값은 최상위 allOf(규칙 shell-platform), none(메뉴 없는 한 장)은 두 플랫폼 모두 — 값: sidebar · top · rail · tabbar · none | `shell-platform` · expand |  |
| `screens[].dark` | ✔ |  | S3 화면 하나씩 | 밤에 쓰는 화면 — 고른 분위기와 상관없이 어두운 분위기(looks 중 mode dark의 첫째)의 색만 빌린다 | build |  |
| `screens[].scene` | ✕ |  | S3 화면 하나씩 | 뺌 — 누구로서는 role, 무엇을은 goal, 그래서는 problem이 맡는다 |  |  |
| `screens[].emphasize` | ✔ | 권장 | S3 화면 하나씩 | 크게 할 내용 문장 하나 | `emphasize-length` · `emphasize-fact` · `display-only-emphasize` · `rank1-fold` · pack | 1순위 문장은 한 줄로 짧게 — 길면 첫눈에 읽히지 않는다 · KRDS 핵심 주제는 첫 문장에(권장) · 사례: 토스 One Thing |
| `screens[].emphasize2` | ✔ |  | S3 화면 하나씩 | 1순위에서 넘친 말 한 줄 — 굵기로 | `emphasize-length` · pack | 1순위 문장이 넘칠 때 뒷부분을 받는 자리 · KRDS 같은 크기면 굵기로(권장) |
| `screens[].defer` | ✔ | 권장 | S3 화면 하나씩 | 이 화면에서 덜어내거나 미룰 것 목록 — data의 사실 중 이 화면에서 빼거나 다르게 보일 것 포함 | `rank3-max` · pack | 덜어낼 것을 미리 정해 두면 화면에 볼 것이 넘치지 않는다 · KRDS 강조 표현 과다 금지(목록 탐색, https://www.krds.go.kr/html/site/global/global_04.html) · 사례: 점진적 공개(NN/g) |
| `screens[].data` | ✔ | 권장 | S3 화면 하나씩 | 이 화면에 쓸 사실 = facts의 이름표(키) 목록. 조립 담당은 이 사실만 쓴다 | → `facts.key` · `data-key-exists` · pack | 사실은 facts 한 곳에만 두고 화면은 이름표로 가리킨다 — 없는 이름표는 검사에서 걸려 지어낸 사실을 막는다 · 우리 과정 규칙 (사례: 데이터 정규화 — 한 사실 한 곳) |
| `screens[].focus` | ✔ | 권장 | S3 화면 하나씩 | 1순위 영역의 key | → `region.key (screen 안)` · `rank1-one` · pack |  |
| `screens[].regions` | ✔ | 필수 | S3 화면 하나씩 | 화면 안 의미 덩어리 목록 | `regions-count` · `info-volume` · pack · build · lint |  |
| `screens[].regions[].id` | ✔ |  | S3 화면 하나씩 | 영역 번호 — ids.js가 101부터 준다 | `ids-range` |  |
| `screens[].regions[].key` | ✔ | 필수 | **S2 여정 · 화면 목록** | 화면 안 영역 id — 조각의 data-region, 흐름 step.region · motion.region · focus가 가리킨다. 같은 화면 안에서만 하나(다른 화면에 같은 key가 있어도 된다). 흐름을 짤 때(S2) 누르는 곳의 key를 먼저 정한다 | 하나뿐(screen) |  |
| `screens[].regions[].label` | ✔ | 필수 | S3 화면 하나씩 | 무엇이 보이는 곳 / 하는 곳 — 사용자에게 보이는 이름 | `label-plain` · pack · 보드 | ux-writing §2 |
| `screens[].regions[].why` | ✔ | 권장 | S3 화면 하나씩 | 이게 뭐냐면 — 사용자 눈높이 한 문장 | pack |  |
| `screens[].regions[].prd` | ✕ |  | S3 화면 하나씩 | 뺌 — 읽는 곳 없음 — PRD 근거는 brief.md 한 곳 |  |  |
| `screens[].regions[].content` | ✔ | 권장 | S3 화면 하나씩 | 이 영역에 들어갈 실제 내용 | pack | 영역에 실제로 들어갈 내용을 먼저 적어야 순서와 크기를 정할 수 있다 |
| `screens[].regions[].level` | ✔ | 권장 | S3 화면 하나씩 | 영역의 중요도 등급 — 1이 가장 중요 — 값: 1 · 2 · 3 | `rank1-one` · `rank3-max` | 화면마다 1순위를 하나로 두면 전하는 바가 분명해진다 · KRDS 서비스 메인 — 시급 · 중요 정보를 먼저(필수) |
| `screens[].regions[].form` | ✔ | 권장 | S3 화면 하나씩 | 영역 모양 — 이 내용을 어떤 모양으로 놓나. 값은 Claude JSON용 짧은 영문 키, KRDS 이름은 x-krds. 시안이 바꾸지 않는다 — 값: hero · list(KRDS 구조화 목록) · table(KRDS 표) · calendar(KRDS 달력) · form(KRDS 입력폼(기본 패턴)) · timeline · cards · stat-row · split | `rank1-hero` · `repeat-unit` · `table-empty-dash` · `table-plain` · `calendar-state` | 같은 내용도 모양(한 칸 큰 글 · 표 · 목록 …)에 따라 위계가 무너지거나 산다 · 값마다 x-krds · x-source (KRDS 컴포넌트 · 패턴, 없으면 우리 규칙 · 사례) |
| `screens[].regions[].signature` | ✔ |  | S3 화면 하나씩 | 시안 특징 장치 — 1순위가 hero가 아니어도 되는 예외 | `rank1-hero` · pack |  |
| `screens[].regions[].stays` | ✔ |  | S3 화면 하나씩 | 그 자리에서 바뀌는 버튼과 문구 계획 — 결과는 조각의 data-stay. 계획(여기)과 결과(HTML)가 맞는지는 lint가 본다 | pack · lint |  |
| `screens[].policy` | ✔ |  | S3 화면 하나씩 | 화면 아래 정책 메모 — 이 화면의 규칙 1~4묶음. 상태 변형(variantOf)은 선택. 움직임은 motion에, 오류 · 안내 문구는 cases에 — 여기 다시 쓰지 않는다 | `policy-required` · build · lint · 보드 |  |
| `screens[].policy[].title` |  | 필수 | S3 화면 하나씩 | 묶음 이름 — 자유 글(권장 예: 기본 정의 · 제한 · 입력 규칙 · 표기 · 예외) |  |  |
| `screens[].policy[].items` |  | 필수 | S3 화면 하나씩 | 규칙 한 줄씩 — 70자 이내, 6줄 이하 |  |  |
| `screens[].cases` | ✔ |  | S3 화면 하나씩 | 오류 · 안내 문구 모음 — 빈칸 · 너무 김 · 겹침 · 실패 때 보여 줄 문구 | `cases-edge` · build · lint · 보드 |  |
| `screens[].cases[].when` |  | 필수 | S3 화면 하나씩 | 이 문구가 뜨는 때 (예: 이름을 비워 두고 보내면) |  |  |
| `screens[].cases[].show` |  | 필수 | S3 화면 하나씩 | 보여 줄 문구 50자 이내 |  |  |
| `screens[].cases[].tone` |  |  | S3 화면 하나씩 | 문구 색 성격(없으면 danger) — 값: danger · warning · info · success |  |  |
| `screens[].motion` | ✔ |  | S3 화면 하나씩 | 화면 움직임 — 완성본에서 실제로 재생된다. 정책에 글로만 적지 않는다 | `motion-target` · build · lint · 보드 |  |
| `screens[].motion[].type` | ✔ | 필수 | S3 화면 하나씩 | 움직임 종류 — 값: hold · breathe · dim · countup · stagger · reorder · carousel · play | `motion-target` · build · lint |  |
| `screens[].motion[].region` | ✔ |  | S3 화면 하나씩 | 움직이는 영역 key(조각의 data-region) | → `region.key (screen 안)`(옛 칸 target과 함께면 경고) · build |  |
| `screens[].motion[].trigger` | ✔ |  | S3 화면 하나씩 | 누르는 버튼 key(조각의 data-trigger) — 조각에 있는지는 lint가 본다 | `motion-target` |  |
| `screens[].motion[].target` | ✕ |  | S3 화면 하나씩 | 뺌 — region · trigger 두 칸으로 나눔 |  |  |
| `screens[].motion[].ms` | ✔ |  | S3 화면 하나씩 | 길이(밀리초) 100~60000 | build |  |
| `screens[].motion[].level` | ✔ |  | S3 화면 하나씩 | 세기 단계 — build가 재생기로 넘긴다 | build |  |
| `screens[].motion[].note` | ✔ | 필수 | S3 화면 하나씩 | 완성본 '움직임' 안내에 보이는 한 문장 44자 이내 | build · 보드 |  |
| `mood` | ✔ |  | **S4 성격** | ② 성격 — 기준어 · 표현용 무드보드 | 보드 |  |
| `mood.keywords` | ✔ |  | S4 성격 | 기준어 3개 | `mood-keywords-3` |  |
| `mood.keywords[].word` | ✔ | 필수 | S4 성격 | 기준어 — 반대로 짐작하면 틀리는 말 | 하나뿐(doc) · 보드 |  |
| `mood.keywords[].not` | ✔ | 필수 | S4 성격 | 넘친 쪽을 막는 말 (하지만 …은 아님) | 보드 |  |
| `mood.keywords[].prd` | ✔ | 필수 | S4 성격 | 근거 절 | 보드 | 기준어는 사람이 보드에서 근거와 함께 본다 |
| `mood.keywords[].from` | ○ |  | S4 성격 | 이 기준어가 나온 사실 — roles[].key 또는 facts 이름표 (옛 실행물의 purpose.domain id는 경고) | → `role.key` · → `facts.key` · → `domainItem.id(옛 대상)` · 보드 | 기준어가 어느 사실에서 나왔는지 적으면 실행마다 덜 흔들린다 |
| `mood.board` | ✔ |  | S4 성격 | 표현용 무드보드 | 보드 |  |
| `mood.board[].id` | ✔ | 필수 | S4 성격 | 항목 id | 보드 |  |
| `mood.board[].name` | ✔ | 필수 | S4 성격 | 레퍼런스 이름 | 보드 |  |
| `mood.board[].url` | ✔ | 필수 | S4 성격 | 레퍼런스 주소 | 보드 |  |
| `mood.board[].fetched` | ✕ |  | S4 성격 | 뺌 — 레퍼런스 조사 상태 |  |  |
| `mood.board[].take` | ✔ | 필수 | S4 성격 | 이 레퍼런스에서 가져올 한 가지 — 값: color(KRDS 색상) · type(KRDS 타이포그래피) · shape(KRDS 형태) · space(KRDS 레이아웃(간격)) · graphic(KRDS 그래픽 색상 · 아이콘) · photo | 보드 | KRDS 스타일 항목 — https://www.krds.go.kr/html/site/style/style_01.html |
| `mood.board[].what` | ✔ | 필수 | S4 성격 | 그 한 가지를 눈에 보이게 한 줄 | 보드 |  |
| `mood.board[].keyword` | ✔ | 필수 | S4 성격 | 어느 기준어 때문인가 = mood.keywords[].word | → `keyword.word` · 보드 |  |
| `mood.board[].colors` | ✔ |  | S4 성격 | 가져온 색(잰 값) | 보드 |  |
| `mood.board[].look` | ✔ | 필수 | **S5 시안** | 이 항목을 쓴 분위기 = looks[].id — 시안 단계(S5)에서 채운다 | → `look.id` |  |
| `looks` | ✔ |  | **S5 시안** | 분위기 — 시안마다 하나 | looks · build · 보드 |  |
| `looks[].id` | ✔ | 필수 | S5 시안 | 분위기 id | 하나뿐(doc) · looks · build · 보드 |  |
| `looks[].name` | ✔ | 필수 | S5 시안 | 한국어 일상어 이름 (예: 따뜻한 크림) | 보드 |  |
| `looks[].mode` | ✔ | 필수 | S5 시안 | 밝음 · 어두움 — 값: light(KRDS 기본 모드) · dark | looks | https://www.krds.go.kr/html/site/style/style_02.html |
| `looks[].tone` | ✔ | 권장 | S5 시안 | 바탕 톤 — 값: white(KRDS 60% 배경 · 중립 색) · paper(KRDS 60% 배경 · 중립 색) · tint(KRDS 60% 배경 · 중립 색) · color · dark | `tone-spread` · `tone-distance` · lint | 시안끼리 바탕 톤이 갈려야 색 이름만 다른 시안이 되지 않는다 · KRDS 색상 비율 — https://www.krds.go.kr/html/site/style/style_02.html |
| `looks[].bg` | ✔ | 필수 | S5 시안 | 바탕색 | `color-ratio` · looks |  |
| `looks[].ink` | ✔ | 필수 | S5 시안 | 글자색 | `text-contrast` · looks |  |
| `looks[].shape` | ✔ | 필수 | S5 시안 | 모서리 성격 — 값: sharp(KRDS 형태: 각진 형태) · soft(KRDS 형태: 표준형 래디어스) · round(KRDS 형태: 둥근 형태) | `radius-scale` · looks | 기준어(말)를 모서리(형태)로 옮기는 근거 — KRDS 형태가 주는 이미지 · KRDS 형태가 주는 이미지 — https://www.krds.go.kr/html/site/style/style_04.html |
| `looks[].font` | ✔ | 권장 | S5 시안 | 글꼴 세트 — 본문 · 제목 글꼴과 제목 굵기 · 줄 간격을 함께 가진다(looks.js FONTS). 본문은 KRDS 바닥선(굵기 400 · 줄 간격 1.5 이상)을 지킨다 — 값: pretendard · suit · nanum-square-round · ibm-plex · serif-title | `font-gothic` · `leading-min` · `font-weight-krds` · looks · build | 글꼴은 한 칸(세트 id)이 주인 — 제목 성격(type)은 따로 적는다 · KRDS 타이포그래피 — 본문 고딕 · 굵기 · 줄 간격 https://www.krds.go.kr/html/site/style/style_03.html |
| `looks[].lean` | ✔ | 권장 | S5 시안 | 가장 기운 기준어 = mood.keywords[].word | → `keyword.word` · 보드 |  |
| `looks[].palette` | ✔ | 권장 | S5 시안 | 역할 팔레트 — 대표색(brand, KRDS Primary)이 주인 · 보조(support) · 강조(accent) | `palette-roles` · `accent-share` · `color-ratio` · `color-role-use` · `text-contrast` · `palette-steps` · looks | 색을 후보 나열이 아니라 역할(주요 · 보조 · 강조)로 정한다 — KRDS 색 체계 · KRDS 색 비율 60·30·10 · accent 5% 이하 |
| `looks[].palette.brand` |  |  | S5 시안 | 대표색(KRDS Primary) — 주요 상호작용(중요한 버튼 · 링크), 비율 10%. 버튼 색 토글의 첫 번째 |  | https://www.krds.go.kr/html/site/style/style_02.html |
| `looks[].palette.brand.name` |  |  | S5 시안 | 한국어 색 이름 |  |  |
| `looks[].palette.brand.hex` |  | 필수 | S5 시안 |  |  |  |
| `looks[].palette.brand.why` |  |  | S5 시안 | 어느 기준어 · 역할 때문인지 한 줄 |  |  |
| `looks[].palette.support` |  |  | S5 시안 | KRDS Secondary — 보조 상호작용 · 구분 배경, 비율 30% |  | https://www.krds.go.kr/html/site/style/style_02.html |
| `looks[].palette.support.name` |  |  | S5 시안 | 한국어 색 이름 |  |  |
| `looks[].palette.support.hex` |  | 필수 | S5 시안 |  |  |  |
| `looks[].palette.support.why` |  |  | S5 시안 | 어느 기준어 · 역할 때문인지 한 줄 |  |  |
| `looks[].palette.accent` |  |  | S5 시안 | KRDS Accent — 새 알림 · 중요 배지처럼 제한적으로, 면적 5% 이하 |  | https://www.krds.go.kr/html/site/style/style_02.html |
| `looks[].palette.accent.name` |  |  | S5 시안 | 한국어 색 이름 |  |  |
| `looks[].palette.accent.hex` |  | 필수 | S5 시안 |  |  |  |
| `looks[].palette.accent.why` |  |  | S5 시안 | 어느 기준어 · 역할 때문인지 한 줄 |  |  |
| `looks[].palette.why` |  |  | S5 시안 | 색 조합 이유 한 줄 |  |  |
| `looks[].swatches` | ✔ |  | S5 시안 | 대안 버튼 색 — 대표색(palette.brand)을 뺀 나머지, 4개 이하. 옛 실행물은 첫째가 대표색(looks.js가 palette.brand로 옮겨 읽는다) | 보드 · looks | 대표색은 palette.brand 한 칸에만 — 버튼 색 토글의 첫 번째는 looks.js가 붙인다 |
| `looks[].swatches[].id` |  | 필수 | S5 시안 |  | 하나뿐(look) |  |
| `looks[].swatches[].name` |  |  | S5 시안 | 한국어 색 이름 |  |  |
| `looks[].swatches[].hex` |  | 필수 | S5 시안 |  |  |  |
| `looks[].type` | ✔ | 권장 | S5 시안 | 제목 성격 — heading · headingWhy · ratio · why (글꼴은 font, 밀도는 concepts[].density) | `font-gothic` · looks · 보드 |  |
| `looks[].type.heading` |  |  | S5 시안 | 제목 서체 성격 |  |  |
| `looks[].type.headingWhy` |  |  | S5 시안 | 제목 서체를 고른 이유 |  |  |
| `looks[].type.font` | ✕ |  | S5 시안 | 뺌 — 글꼴은 looks[].font(세트 id)가 주인 |  |  |
| `looks[].type.density` | ✕ |  | S5 시안 | 뺌 — 밀도는 concepts[].density가 주인. 옛 실행물만 |  |  |
| `looks[].type.ratio` |  |  | S5 시안 | 글자 비율 |  |  |
| `looks[].type.why` |  |  | S5 시안 | 이유 한 줄 |  |  |
| `looks[].refs` | ✕ |  | S5 시안 | 뺌 — 무드보드 항목의 look이 이 관계를 가리킨다 |  |  |
| `looks[].why` | ✔ | 필수 | S5 시안 | 이 분위기를 고른 이유 한 줄 | 보드 |  |
| `references` | ✔ |  | **S5 시안** | 구조 레퍼런스 목록 | 보드 |  |
| `references[].name` | ✔ | 필수 | S5 시안 | 서비스 이름 — concepts[].refs[].name이 가리킨다 | 하나뿐(doc) · 보드 |  |
| `references[].url` | ✔ | 필수 | S5 시안 | 주소 | 보드 |  |
| `references[].kind` | ✕ |  | S5 시안 | 뺌 — 읽는 곳 없음(보드 꼬리표도 지움) |  |  |
| `references[].borrow` | ✔ | 필수 | S5 시안 | 가져올 점 | 보드 |  |
| `references[].avoid` | ✕ |  | S5 시안 | 뺌 — 레퍼런스 조사 출력 잔재 |  |  |
| `references[].layout` | ✔ | 필수 | S5 시안 | 비슷한 서비스의 화면 구성 메모 — 시안의 메뉴 틀 · 첫 화면을 정할 때 읽는다(생성) | 생성 → concepts[].shell · 생성 → concepts[].home |  |
| `references[].layout.nav` |  | 필수 | S5 시안 | 메뉴 틀 |  |  |
| `references[].layout.home` |  | 필수 | S5 시안 | 첫 화면 구성 |  |  |
| `references[].layout.density` |  | 필수 | S5 시안 | 밀도 |  |  |
| `references[].layout.signature` |  | 필수 | S5 시안 | 눈에 띄는 장치 |  |  |
| `concepts` | ✔ |  | **S5 시안** | 시안 — 첫 번째가 추천 | `concepts-count` |  |
| `concepts[].id` | ✔ | 필수 | S5 시안 | 시안 id(a~e) | 하나뿐(doc) · build · 보드 |  |
| `concepts[].name` | ✔ | 필수 | S5 시안 | 무엇이 먼저 보이는지 일상어로 | 보드 |  |
| `concepts[].why` | ✔ | 필수 | S5 시안 | 이 시안의 이유 한 줄 | 보드 |  |
| `concepts[].shell` | ✔ | 필수 | S5 시안 | 메뉴 틀 — 플랫폼별 값은 최상위 allOf(규칙 shell-platform) — 값: sidebar · top · rail · tabbar · none | `shell-spread` · `shell-platform` · expand |  |
| `concepts[].home` | ✔ | 필수 | S5 시안 | 첫 화면 구성 | 보드 |  |
| `concepts[].density` | ✔ | 필수 | S5 시안 | 밀도 — 시안을 가르는 축(메뉴 틀 · 첫 화면 · 밀도). 분위기(looks.js)가 이 값으로 여백을 계산한다 — 값: airy · normal · compact · 넓게(옛 값) · 보통(옛 값) · 빽빽하게(옛 값) | looks | 밀도는 메뉴 틀 · 첫 화면과 함께 시안을 가르는 축이다 — 분위기의 여백도 이 값으로 계산한다 |
| `concepts[].look` | ✔ | 필수 | S5 시안 | = looks[].id | → `look.id` |  |
| `concepts[].lean` | ✕ |  | S5 시안 | 뺌 — 시안의 분위기(look)의 lean을 쓴다 |  |  |
| `concepts[].traits` | ✔ | 필수 | S5 시안 | 특징 낱말들 | 보드 |  |
| `concepts[].refs` | ✔ | 필수 | S5 시안 | 참고한 곳과 가져온 점 — 레퍼런스는 이름으로 가리키고 주소는 references에만 | 보드 · lint |  |
| `concepts[].refs[].name` |  | 필수 | S5 시안 | 참고한 곳 = references[].name | → `reference.name`(옛 칸 url과 함께면 경고) |  |
| `concepts[].refs[].borrow` |  | 필수 | S5 시안 | 이 시안에서 그곳에서 가져온 점 한 줄 |  |  |
| `concepts[].refs[].url` | ✕ |  | S5 시안 | 뺌 — 주소는 references[].url 한 곳에(이름으로 가리킨다) |  |  |
| `concepts[].screens` | ✔ | 필수 | S5 시안 | 시안을 비교할 메인 화면 목록 | → `screen.slug` · `concept-screens` · build · 보드 |  |
| `board` | ✔ |  | **하네스** | 보드 설정 — 추천(recommend) · 구조 질문(ask) · 확정(locked) · 먼저 볼 화면(focus) · 바뀐 점(changes) · 첫 화면(hero). 최상위 concept · theme · toggles는 결정, 여기 recommend는 추천 — 보드는 잠갔으면 결정, 아니면 추천을 쓴다 | `board-ask` · 보드 · lint |  |
| `board.recommend` |  |  | 하네스 | 보드가 추천하는 시안 · 분위기 · 글자 크기 · 버튼 색 · 안내 문구 모양과 이유 |  |  |
| `board.recommend.concept` |  |  | 하네스 | 추천 시안 = concepts[].id | → `concept.id` |  |
| `board.recommend.theme` |  |  | 하네스 | 추천 분위기 = looks[].id | → `look.id` |  |
| `board.recommend.themeWhy` |  |  | 하네스 | 분위기 추천 이유 한 줄 |  |  |
| `board.recommend.type` |  |  | **S1 의도** | 추천 글자 크기 — S1에서 roles[].inclusion(나이 · 기기 · 읽는 상황)을 보고 정한다 — 값: normal · large |  |  |
| `board.recommend.typeWhy` |  |  | **S1 의도** | 글자 크기 추천 이유 — 어느 역할의 inclusion 때문인지 |  |  |
| `board.recommend.swatch` |  |  | 하네스 | 추천 버튼 색 = 추천 분위기의 swatches[].id 또는 brand(대표색) | → `look.swatches.id (theme 안) ∪ brand` |  |
| `board.recommend.swatchWhy` |  |  | 하네스 | 버튼 색 추천 이유 한 줄 |  |  |
| `board.recommend.toast` |  |  | 하네스 | 추천 안내 문구 모양(toggles.toast와 같은 모양) |  |  |
| `board.recommend.toast.at` |  |  | 하네스 | 위치 — 화면 위 · 아래 — 값: top · bottom |  |  |
| `board.recommend.toast.icon` |  |  | 하네스 | 아이콘 있음 · 없음 — 값: on · off |  |  |
| `board.recommend.toast.tone` |  |  | 하네스 | 흰 바탕 · 어두운 바탕 · 상태 색 바탕 — 값: light · dark · color |  |  |
| `board.recommend.toast.size` |  |  | 하네스 | 글자 보통 · 크게 — 값: normal · large |  |  |
| `board.recommend.accent` | ✕ |  | 하네스 | 뺌 — swatch로 |  |  |
| `board.recommend.accentWhy` | ✕ |  | 하네스 | 뺌 — swatchWhy로 |  |  |
| `board.ask` |  |  | 하네스 | 구조 질문 — 3개까지(규칙 board-ask) |  |  |
| `board.ask[].id` |  | 필수 | 하네스 | 질문 id |  |  |
| `board.ask[].text` |  | 필수 | 하네스 | 질문 한 문장 |  |  |
| `board.ask[].options` |  | 필수 | 하네스 | 고를 것 — 추천에는 '(추천)' |  |  |
| `board.ask[].recommended` |  | 필수 | 하네스 | 추천 선택지 번호 |  |  |
| `board.locked` |  |  | 하네스 | 확정한 선택 — 보드가 더 묻지 않는다 — 값: concept · theme · type · swatch · toast · ask · toggles(옛 값) |  |  |
| `board.focus` |  |  | 하네스 | 보드에서 먼저 볼 화면 slug — 지난 라운드에 고친 화면 | → `screen.slug` |  |
| `board.changes` |  |  | 하네스 | 지난 의견을 반영해 바뀐 점 — 화면 ⓘ에 보인다 |  |  |
| `board.changes[].slug` |  | 필수 | 하네스 | 바뀐 화면 slug | → `screen.slug` |  |
| `board.changes[].said` |  | 필수 | 하네스 | 사람이 한 말 |  |  |
| `board.changes[].did` |  | 필수 | 하네스 | 그래서 바꾼 것 |  |  |
| `board.hero` |  |  | 하네스 | 보드 첫 화면에 크게 둘 화면 slug | → `screen.slug` |  |
| `nextScreenId` | ✔ |  | **하네스** | 다음에 줄 화면 번호(ids.js) | ids |  |
| `nextRegionId` | ✔ |  | **하네스** | 다음에 줄 영역 번호(ids.js) | ids |  |
| `record` | ✕ |  |  | 옛 칸 |  |  |
| `system` | ✕ |  |  | 옛 enum 시스템 — 쓰지 않음 — system.schema.json과 함께 다음 판에서 지움 |  |  |
| `direction` | ✕ |  |  | 옛 방향 슬라이더 — 쓰지 않음 |  |  |

## flow.json (v1)

정본. 객체: 흐름(flow) · 흐름 단계(step, 갈래도 같은 모양). x-ref로 screens.schema.json의 객체를 가리킨다(screens#…). 규칙은 rules.json(x-rules), 조각 HTML과의 이어짐(data-trigger)은 lint.js.

| 칸 | 상태 | 필수 | 단계 | 뜻 | 관계 · 규칙 · 읽는 곳 | 칸이 왜 있나 |
|---|---|---|---|---|---|---|
| `flows` | ✔ | 필수 | **S2 여정 · 화면 목록** | 여정을 화면 사이 이동으로 — 역할별 처음 시작 흐름이 맨 앞 | `flow-steps` | 화면 사이를 끊김 없이 이어 가는 작업 단위 · KRDS 서비스 패턴 — 여정 단계 기반(https://www.krds.go.kr/html/site/service/service_summary.html) |
| `flows[].key` | ✔ | 필수 | S2 여정 · 화면 목록 | 흐름 id | 하나뿐(doc) · 보드 |  |
| `flows[].name` | ✔ | 필수 | S2 여정 · 화면 목록 | 작업 이름 '~하기' | 보드 |  |
| `flows[].role` | ✔ | 필수 | S2 여정 · 화면 목록 | 이 흐름의 주인 = roles[].key | → `screens#role.key` · `flow-role` · 보드 | 흐름마다 주인이 있어야 그 역할의 목표를 이루는지 볼 수 있다 · KRDS 서비스 패턴 — 여정 단계 기반(https://www.krds.go.kr/html/site/service/service_summary.html) |
| `flows[].steps` | ✔ | 필수 | S2 여정 · 화면 목록 | 끊김 없는 단계들 | `flow-steps` |  |
| `flows[].steps[].from` | ✔ | 필수 | S2 여정 · 화면 목록 | 출발 화면 slug | → `screens#screen.slug` · build · 보드 |  |
| `flows[].steps[].region` | ✔ | 필수 | S2 여정 · 화면 목록 | 누르는 곳이 속한 영역 key | → `screens#region.key (from 안)` |  |
| `flows[].steps[].trigger` | ✔ | 필수 | S2 여정 · 화면 목록 | 누르는 버튼 key — 조각의 data-trigger | lint · build |  |
| `flows[].steps[].action` | ✔ | 필수 | S2 여정 · 화면 목록 | '버튼 문구'를 누르면 — 문구를 따옴표 안에 그대로 | build · 보드 |  |
| `flows[].steps[].to` | ✔ | 필수 | S2 여정 · 화면 목록 | 도착 화면 slug | → `screens#screen.slug` |  |
| `flows[].steps[].when` | ✔ |  | S2 여정 · 화면 목록 | 갈래 이름표 16자 이내 "~면" — 같은 화면 · 같은 버튼에서 갈릴 때만. 구역 보드는 when이 있는 연결에만 화살표를 그린다 | `split-when` · build · lint · 보드 |  |
| `branches` | ✔ |  | **S2 여정 · 화면 목록** | 흐름 밖에서 다른 화면 · 창을 여는 버튼 | build · lint · 보드 | 흐름 밖 버튼이 여는 화면을 적어 두면 '누르면 무슨 화면이 나오는지' 빠지지 않는다 |
| `branches[].from` | ✔ | 필수 | S2 여정 · 화면 목록 | 출발 화면 slug | → `screens#screen.slug` · build · 보드 |  |
| `branches[].region` | ✔ | 필수 | S2 여정 · 화면 목록 | 누르는 곳이 속한 영역 key | → `screens#region.key (from 안)` |  |
| `branches[].trigger` | ✔ | 필수 | S2 여정 · 화면 목록 | 누르는 버튼 key — 조각의 data-trigger | lint · build |  |
| `branches[].action` | ✔ | 필수 | S2 여정 · 화면 목록 | '버튼 문구'를 누르면 — 문구를 따옴표 안에 그대로 | build · 보드 |  |
| `branches[].to` | ✔ | 필수 | S2 여정 · 화면 목록 | 도착 화면 slug | → `screens#screen.slug` |  |
| `branches[].when` | ✔ |  | S2 여정 · 화면 목록 | 갈래 이름표 16자 이내 "~면" — 같은 화면 · 같은 버튼에서 갈릴 때만. 구역 보드는 when이 있는 연결에만 화살표를 그린다 | `split-when` · build · lint · 보드 |  |
