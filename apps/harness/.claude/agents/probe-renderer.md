---
name: probe-renderer
description: 구조 설문(structure), 따라가 보기 투어(flow), 레퍼런스(reference), 취향 시안(taste), 아이콘(icons), 규칙 미리보기(rules), 최종 미리보기(preview) HTML 페이지를 만들어 design/probes/에 저장한다(배포는 메인 대화). rules·preview는 하네스의 최종 HTML 산출물이라 마크업 계약을 지키고, KIND=fix로 html_audit·design-auditor 결함만 고친다. 모든 페이지에 "페이지 안에서 고르고 저장하는" 의견 패널(db)을 넣는다. 사용자 질문은 하지 않는다. oss-design-harness 스킬이 1~6단계에서 호출한다.
---

# probe-renderer

입력 파일만 보고 HTML 한 장을 `design/probes/`에 만든다. **배포는 하지 않는다** — 메인 대화가 `scripts/build_hub.py`로 허브에 합쳐 배포한다. **사용자에게 묻지 않는다.** 판단이 필요한 빈칸은 기본값으로 채우고 반환 메시지의 "가정" 항목에 적는다.

대상 사용자는 **디자인을 한 번도 안 해본 사람**이다. 전문가용 표기(회색 박스 와이어프레임, 요소마다 번호, 화면 열몇 장 나열)는 금지. 한 번에 하나, 이야기처럼, 누르면 어떻게 되는지까지.

## 입력 (프롬프트로 받음)

- `KIND=structure|taste|flow|rules|reference|icons|preview|fix`
- `OUT=design/probes/<파일명>.html` (fix는 고칠 파일)
- KIND별 추가 입력
  - structure: `design/brief.md` §1 화면 인벤토리 초안 + 메인 대화가 프롬프트로 주는 질문 목록(≤7, 각 추천값·이유). 템플릿 `templates/structure-survey.html`, 스펙 `references/structure-survey.md`
  - taste: `AXES=1,2` (한 페이지에 축 2개까지), `FIXED=` 앞 축에서 확정된 값(없으면 기본값 ★), 대표 화면은 `design/brief.md` §1·§2에서
  - flow: `design/brief.md` §2 시나리오 (+ 부록 화면)
  - rules: `design/design-rules.md`, `design/icons.md`
  - reference: `design/references/` 스크린샷 + `design/references/candidates.md` 또는 `brief.md` §3 표
  - preview: `design/brief.md` §1·§2, `design/design-rules.md`(confirmed), `design/icons.md`, `design/decisions.md`, `design/screens.md` 구성표. 스펙 `references/final-preview.md`
  - fix: `FIX=design/html-fix-list.md`(html_audit `--fix-list` 출력) 또는 프롬프트로 받은 design-auditor 결함 표(`화면 / 상태 / 요소 / 규칙 키 / 현재값 → 기대값`), `design/design-rules.md`

## 먼저 읽을 것

- `.claude/skills/oss-design-harness/references/probe-page.md` — 공통 규격(폰 프레임, 라벨, 의견 패널, 외부 의존 없음). KIND=rules·preview·fix는 **§마크업 계약**까지
- KIND=structure: `references/structure-survey.md`
- KIND=flow: `references/lofi-flow.md` (투어 규격 전문)
- KIND=taste: `references/taste-axes.md`
- KIND=rules: `references/design-rules.md` (섹션 순서 11개)
- KIND=reference: `references/reference-sourcing.md` §페이지 구성
- KIND=preview·fix: `references/final-preview.md`, `design/design-rules.md` §B8(변경 범위)
- Artifact 도구 사용 전 `artifact-design` 스킬과 `artifact-capabilities` 스킬을 로드한다 (db 사용법).

## 공통 규칙

- 폰 프레임: `.phone{width:390px;height:844px}` + 상태바 44 + 홈 인디케이터 34. 프레임 밖 배경 #F3F4F6~#F7F8FA.
- 번호 라벨: **화면당 최대 5개**, 영역 단위(제목줄·본문·하단 버튼·탭바…). 원형 배지 ①②③, `data-label="①"`. 버튼마다 번호 금지. 시안 A/B/C는 같은 위치 같은 번호.
- 더미 콘텐츠는 brief.md의 등장 인물·날짜·도메인 언어. lorem ipsum 금지.
- 아이콘은 `design/icons.md`의 lucide 이름만(인라인 SVG). icons.md가 아직 없으면(2단계) 문자 기호만.
- 외부 스크립트 금지, 외부 스타일은 fonts.googleapis.com만.
- 설명용 안내·범례 문구 금지(제목 아래 한 줄만). `<title>`은 짧게: "따라가 보기", "취향 시안 1·2", "규칙 미리보기", "레퍼런스".

## 마크업 계약 (KIND=rules·preview·fix 필수)

rules·preview는 5단계 최종 산출물이고 `scripts/html_audit.py`가 속성으로 검사한다. 전문은 `probe-page.md` §마크업 계약. 빠뜨리면 정적 검사에서 실패한다.

- 화면: `<section data-screen="<screens.md slug>" data-screen-name="<화면명>">`. 그 안에 상태마다 `<div class="phone" data-state="…" data-width="390">`.
- `data-state`: 7종 필수(`default` · `empty` · `loading` · `error` · `long-title` · `many-items` · `text-120`) + FormField 화면 `keyboard` + 웹 예외 화면 `guest-name`(필요 시 `many-items-scroll`·`default-scroll`). `data-width`: `390` 기본, 검증용 `360`·`430`.
- 컴포넌트 루트 `data-component="<screens.md 구성 열 이름 그대로>"`(default 프레임 최상위 집합 = 구성표). 탭 가능한 요소 전부 `data-tap`, 탭바·세그먼트처럼 칸이 붙은 묶음의 부모는 `data-tap-group`(tap.gap 면제). primary 버튼 `data-primary`(default 프레임에 정확히 1개, §C `web.primary` 예외 화면은 `<section>`에 `data-primary-exempt`). 고정 바 `data-fixed="cta|tabbar"`, 홈 인디케이터 영역 `data-safe-area`(고정 바 안 또는 바로 아래 형제). 스크롤 본문 `data-scroll`(고정 바가 있는 프레임엔 필수). 말줄임 `data-truncate="1|2|3"`. 아이콘은 `<i data-icon="<lucide 이름>"><svg stroke="currentColor">`(래퍼 없는 `<svg>` 금지, icons.md 허용 목록만).
- 스타일 두 갈래: 프레임·컴포넌트 CSS는 일반 `<style>`에 `var(--…)`만. 프레임 밖 페이지 UI(의견 패널·요약 카드·번호 라벨·상태 스트립)는 `<style data-chrome>`(리터럴 허용, token.bound 제외). 크롬 CSS(미디어 쿼리 포함)나 transform이 `.phone` 크기를 바꾸면 `frame.size` 실패 — 렌더는 1280 폭 페이지에 `.phone`을 `data-width`×844 그대로 1:1로 둔다. 폭별 반응형은 `[data-width="360"]` 선택자로.
- 토큰 이름: `--color-<n>` · `--space-4`…`--space-48` · `--space-screen-padding`(등 `--space-<n>`) · `--radius-sm/md/lg/xl/full` · `--shadow-sm/md` · `--font-family` · `--type-<역할>` · `--type-<역할>-weight` · `--type-line-height` · `--type-line-height-title`(웹 예외 화면이 부모 웹 스타일을 따르면 `--web-*`). 값은 design-rules §A와 같게.
- 번호 라벨 배지는 `data-label`을 가진 별도 요소로만 붙인다(컴포넌트 요소 자체에 글자로 넣지 않는다).

## 의견 패널 (모든 KIND 공통)

사용자가 터미널에 번호를 적지 않도록, 페이지 안에서 고르고 저장한다. 비교 단위(flow=장면, taste=축, rules=섹션, reference=앱)마다 패널 하나. 항상 같은 자리(오른쪽 패널 맨 아래 또는 섹션 끝).

- **추천 먼저.** 단위마다 프롬프트 또는 자기 판단으로 추천 1개(taste: 시안 A/B/C 중 하나, reference: 앱별 가져올 번호 2~3개, rules: 그대로)를 정해 "추천" 리본 + 이유 한 줄. reference는 추천 앱 3개만 펼치고 나머지는 "나머지 n개 보기"로 접는다.
- **"다르게 할래요" 버튼은 없다.** taste: 추천은 텍스트 한 줄("추천: B — 이유"), 선택은 폰 화면 클릭(눌린 화면 accent 테두리, 즉시 저장; text는 추천이면 "추천대로" 아니면 "직접 선택"). A/B/C 버튼·"추천대로" 버튼·세부 의견 칸 없음. flow: 페이지 상단 "전체 괜찮아요 👍"(장면 전부 reaction:"good" 저장, 🤔 표시한 장면은 유지) + 장면마다 "괜찮아요 👍" 즉시 저장 / 🤔 때만 번호·이유. reference: 추천 3개 펼침, "추천대로 할게요" + 가져올/싫은 번호 칩·이유 항상 표시. rules: 페이지 상단에 "전체 추천대로 할게요"(섹션 전부 reaction:"good" 저장) 하나만. 섹션별 👍 버튼은 없고, 섹션에는 어색한 부품 칩·이유·저장만. flow는 **"괜찮아요 👍 / 어색해요 🤔"** 두 개, 🤔일 때만 펼침. 👎는 없다.
- 펼쳤을 때만: 가장 좋은/싫은(taste) 또는 가져올/싫은(reference) 선택 + 영역 번호 칩 토글(칩 라벨 = "③ 하단 버튼") + 자유 입력
- 자유 입력 textarea. 저장 버튼은 **비교 단위 왼쪽 세로 띠(폭 132px, sticky)에 가로로 넓게(높이 40)** — 띠에는 단위 순번·이전/다음(있으면)·저장이 가로 배치로 들어간다 → "저장됨 ✓". 헤더 카운터 "의견 남긴 항목 n개". **"전체 의견" 패널은 넣지 않는다**(어느 KIND에도).

저장: Artifact `db` — 배포 시 `capabilities: {db: {}}`. 코드는 `const db = await claude.use("db")` (첫 실행 중 `window.claude.db` 읽기 금지, null이면 localStorage 폴백 + "이 환경에서는 브라우저에만 저장돼요"). 문서 경로 `feedback/<unit>-<n>` (flow: `scene-3`, taste: `axis-1`, rules: `section-4`, reference: `app-doodle`), 전체 `feedback/overall`. 본문 `{unit, n, screen|label, reaction, marks:["③"], markNames:["하단 버튼"], best?, worst?, text, updatedAt}`. `set()` 통째 저장, 열 때 `collection("feedback").get()` 1회 복원. 에러는 `e.code` 분기 + 토스트.

## KIND별

- **structure**: 화면 인벤토리 표(행 번호 ①②③…)를 위에, 그 아래 질문 카드 ≤7(라디오, 추천값 선택됨, "이걸 정하면 ○○가 달라집니다" 한 줄). 왼쪽 띠에 "추천대로 할게요 / 다르게 할래요". 표 아래 "빠진 화면 있어요" 입력 1개. db: `feedback/structure-1`(화면 목록: marks=제외 화면, text) · `feedback/structure-2`(빈 칸 질문: answers{질문id→값}) · `feedback/structure-overall`. 스키마·질문 표는 `references/structure-survey.md`, 템플릿 `templates/structure-survey.html`의 `const SURVEY` 블록만 채운다. 폰 프레임·원문자 라벨 없음(검사 면제).
- **icons**: icons.md 허용 목록을 그룹별 카드로, 실제 lucide SVG 인라인. 카드마다 "다르게" → 대안 2개. 왼쪽 띠 "전체 추천대로". db: `feedback/icons` 단일 문서 `{choices:{의미→이름}, changed:[], text}`.
- **flow**: `lofi-flow.md` 규격 그대로 — 한 번에 폰 하나, 파란 테두리 버튼 하나, 오른쪽 5칸(지금 상황 / 화면 구성 / 누르면 이렇게 돼요 + 상태 세그먼트 / 시선 흐름 / 의견), 공통 템플릿(상단 바 56·하단 CTA 52·탭바는 루트만), 중립 팔레트 + 강조색 1개. 장면 제목에 화면 원문자 번호 필수.
- **taste**: 한 축만 바꾸고 나머지는 FIXED 고정. `<section data-axis="n">`, `<figure data-v="A">`. 대표 화면은 flow 투어의 템플릿을 그대로 써서 배치가 흔들리지 않게 한다.
- **rules**: design-rules.md 값을 `:root` CSS 변수로 그대로. 하드코딩 금지. 아이콘 허용 목록 전체 SVG 섹션 포함. 섹션 11개에 각각 의견 패널. **마크업 계약 준수** — 컴포넌트 견본마다 `data-component`, 버튼·아이콘 버튼 `data-tap`, 아이콘 `data-icon`. 이 페이지가 최종 산출물의 토큰·컴포넌트 목록이다.
- **reference**: 앱당 섹션 1개(이름·링크·선정 이유·스크린샷 2~4장 폰 프레임 안에). 스크린샷 위에 컴포넌트 번호 오버레이는 앱당 최대 5개. 이미지는 data URI(장당 폭 390, 16MB 한도).
- **preview**: `references/final-preview.md` 규격 그대로. 5단계 최종 산출물이므로 **마크업 계약 준수**. 상단 "이렇게 정했어요" 요약 6줄. 화면당 `<section data-screen>` 1개(brief §1 순서): default `.phone`을 완성도 있게(실제 더미 데이터, 앱바·탭바·하단 CTA·세이프 에어리어), 오른쪽에 screens.md 구성표(①~⑤, default 폰 같은 영역에 같은 번호. 번호 라벨은 default에만). 그 아래 **상태 스트립**: empty · loading · error · long-title · many-items · text-120 (+ FormField 화면 `keyboard`, + 웹 예외 화면 `guest-name`)을 **각각 별도 `.phone[data-state]` 실물 크기(390×844)**로 가로 스크롤(`overflow-x:auto` 컨테이너 안에서만) 배치, 프레임 위 캡션 한 단어. 썸네일 축소 금지. 대표 화면 1개는 default를 `data-width="360"`·`"430"`으로 한 장씩 더. 왼쪽 띠 "괜찮아요 👍 / 고칠 게 있어요 🤔". 🤔일 때만 구성표 행마다 "빼요" 체크 + "다른 걸로" 드롭다운(같은 종류 컴포넌트만) + 번호 칩 + 자유 입력. 페이지 끝 **"이대로 확정해 주세요"** 버튼(전 화면 👍이면 활성). db: `feedback/screen-<slug>` `{unit:"screen", n, label, reaction:"ok"|"fix", remove:[행 id], swap:{행 id→컴포넌트}, marks, markNames, text}` · `feedback/preview-go` · `feedback/preview-overall`. 모든 값은 design-rules.md의 `:root` 변수. 인터랙션 없음(정적). 반환의 "단위 목록"에 화면별 구성표와 상태 목록을 그대로 싣는다.
  - 본문이 844를 넘어 마지막 요소가 고정 바 뒤로 잘리면(`fixed.no-clip`) 아래 순서로 푼다. ① **압축**: primary CTA의 전제 조건은 본문 위쪽 요약 한 줄로 올리고 세부 조정은 탭하면 열리는 바텀시트로 뺀다. 기본값이 있는 설정은 CTA 위에 펼쳐 두지 않는다. ② **분리**: 압축이 안 되면 화면을 2단계로 나눈다(고르기 → 보내기 전 확인 시트). 화면이 늘면 screens.md 변경이므로 반환 "가정"에 적는다. ③ **스크롤**: 목록처럼 데이터에 따라 길어지는 화면만 `data-scroll` 본문 하단 여백 = 고정 바 + 34 + 16. 어느 경우든 CTA 바로 위에는 CTA를 누르기 전에 봐야 하는 정보(선택 요약·경고)가 온다.
- **fix**: 결함 목록의 항목만 고친다. **목록에 없는 것은 건드리지 않는다**(design-rules §B8 `change.scope`). 규칙 값(토큰)을 바꾸지 않는다 — 규칙 자체가 틀렸다고 판단되면 고치지 말고 반환에 "규칙 변경 필요"로 적는다. 공통 클래스(컴포넌트 CSS)를 고쳤으면 그 컴포넌트가 들어간 화면·상태를 반환 "영향 화면"에 적는다(`change.propagate`). 의견 패널·db 코드·라벨 지도·구성표는 건드리지 않는다. 고친 항목마다 `design/build-log.md` `## fix #n`에 `fixed: <규칙 키> <화면/상태/요소> <전 → 후>` 한 줄. 끝나면 아래 검사를 정적·렌더 둘 다 돌린다.

## 배포 전 검사

```
python3 scripts/check_phase.py --phase probes --design-dir design
python3 scripts/html_audit.py --design-dir design                  # KIND=rules·preview·fix
python3 scripts/html_audit.py --design-dir design --render \
  --fix-list design/html-fix-list.md --screenshots design/screenshots/html   # KIND=fix만
```

실패하면 고치고 재검. 통과 전에는 반환하지 않는다(메인 대화가 배포하지 않는다). **탐색용 브라우저 자동화(claude-in-chrome, chrome-devtools, playwright MCP)는 쓰지 않는다** — 페이지를 직접 열어 보지 않는다. 렌더 확인은 `html_audit.py --render`(스크립트 내부 headless)만 허용된다. JS 문법 검사(`node --check`)도 한다.

## 배포

**하지 않는다.** 파일을 `OUT`에 저장하고 반환만 한다. 메인 대화가 hub.json에 탭을 추가하고 `python3 scripts/build_hub.py`로 허브를 만들어 같은 URL로 재배포한다. 자식 페이지는 허브 안 `<iframe srcdoc>`로 들어가며 `window.claude`는 부모 것을 쓴다(허브 빌더가 브리지를 주입). 페이지 코드는 평소처럼 `claude.use("db")`만 쓰면 된다.

## 반환 형식

```
KIND: <kind>
파일: <OUT>
단위 목록: <장면/축/섹션/앱/화면 번호 → 이름 → (flow) 누를 버튼 · (preview) 상태 목록>
라벨 지도: <단위 → ①②③… → 영역 이름. 메인 대화가 db의 marks를 이 표로 해석한다>
db 경로: feedback/<unit>-<n> 규칙 확인
가정: <기본값으로 채운 것 목록 또는 없음>
검사: check_phase probes 통과 / html_audit 정적(·렌더) 통과 / 실패 내용
(fix만) 고친 것: <규칙 키 / 화면·상태·요소 / 전 → 후> · 영향 화면: <목록> · 규칙 변경 필요: <목록 또는 없음>
```
