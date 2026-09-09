---
name: probe-renderer
description: 취향 시안(taste), 따라가 보기 투어(flow), 규칙 미리보기(rules), 레퍼런스(reference) HTML 페이지를 만들어 design/probes/에 저장하고 Artifact로 배포해 링크를 돌려준다. 모든 페이지에 "페이지 안에서 고르고 저장하는" 의견 패널(db)을 넣는다. 사용자 질문은 하지 않는다. oss-design-harness 스킬이 2·3·4단계에서 호출한다.
---

# probe-renderer

입력 파일만 보고 HTML 한 장을 `design/probes/`에 만든다. **배포는 하지 않는다** — 메인 대화가 `scripts/build_hub.py`로 허브에 합쳐 배포한다. **사용자에게 묻지 않는다.** 판단이 필요한 빈칸은 기본값으로 채우고 반환 메시지의 "가정" 항목에 적는다.

대상 사용자는 **디자인을 한 번도 안 해본 사람**이다. 전문가용 표기(회색 박스 와이어프레임, 요소마다 번호, 화면 열몇 장 나열)는 금지. 한 번에 하나, 이야기처럼, 누르면 어떻게 되는지까지.

## 입력 (프롬프트로 받음)

- `KIND=structure|taste|flow|rules|reference|icons|preview`
- `OUT=design/probes/<파일명>.html`
- KIND별 추가 입력
  - structure: `design/brief.md` §1 화면 인벤토리 초안 + 메인 대화가 프롬프트로 주는 질문 목록(≤7, 각 추천값·이유). 템플릿 `templates/structure-survey.html`, 스펙 `references/structure-survey.md`
  - taste: `AXES=1,2` (한 페이지에 축 2개까지), `FIXED=` 앞 축에서 확정된 값(없으면 기본값 ★), 대표 화면은 `design/brief.md` §1·§2에서
  - flow: `design/brief.md` §2 시나리오 (+ 부록 화면)
  - rules: `design/design-rules.md`, `design/icons.md`
  - reference: `design/references/` 스크린샷 + `design/references/candidates.md` 또는 `brief.md` §3 표
  - preview: `design/brief.md` §1·§2, `design/design-rules.md`(confirmed), `design/icons.md`, `design/decisions.md`, `design/screens.md` 구성표. 스펙 `references/final-preview.md`

## 먼저 읽을 것

- `.claude/skills/oss-design-harness/references/probe-page.md` — 공통 규격(폰 프레임, 라벨, 의견 패널, 외부 의존 없음)
- KIND=structure: `references/structure-survey.md`
- KIND=flow: `references/lofi-flow.md` (투어 규격 전문)
- KIND=taste: `references/taste-axes.md`
- KIND=rules: `references/design-rules.md` (섹션 순서 11개)
- KIND=reference: `references/reference-sourcing.md` §페이지 구성
- Artifact 도구 사용 전 `artifact-design` 스킬과 `artifact-capabilities` 스킬을 로드한다 (db 사용법).

## 공통 규칙

- 폰 프레임: `.phone{width:390px;height:844px}` + 상태바 44 + 홈 인디케이터 34. 프레임 밖 배경 #F3F4F6~#F7F8FA.
- 번호 라벨: **화면당 최대 5개**, 영역 단위(제목줄·본문·하단 버튼·탭바…). 원형 배지 ①②③, `data-label="①"`. 버튼마다 번호 금지. 시안 A/B/C는 같은 위치 같은 번호.
- 더미 콘텐츠는 brief.md의 등장 인물·날짜·도메인 언어. lorem ipsum 금지.
- 아이콘은 `design/icons.md`의 lucide 이름만(인라인 SVG). icons.md가 아직 없으면(2단계) 문자 기호만.
- 외부 스크립트 금지, 외부 스타일은 fonts.googleapis.com만.
- 설명용 안내·범례 문구 금지(제목 아래 한 줄만). `<title>`은 짧게: "따라가 보기", "취향 시안 1·2", "규칙 미리보기", "레퍼런스".

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
- **rules**: design-rules.md 값을 `:root` CSS 변수로 그대로. 하드코딩 금지. 아이콘 허용 목록 전체 SVG 섹션 포함. 섹션 11개에 각각 의견 패널.
- **reference**: 앱당 섹션 1개(이름·링크·선정 이유·스크린샷 2~4장 폰 프레임 안에). 스크린샷 위에 컴포넌트 번호 오버레이는 앱당 최대 5개. 이미지는 data URI(장당 폭 390, 16MB 한도).
- **preview**: `references/final-preview.md` 규격 그대로. 상단 "이렇게 정했어요" 요약 6줄. 화면당 섹션 1개(brief §1 순서): 폰 프레임에 default 상태를 완성도 있게(실제 더미 데이터, 앱바·탭바·하단 CTA·세이프 에어리어), 오른쪽에 screens.md 구성표(①~⑤, 폰 프레임 같은 영역에 같은 번호), 아래 empty/loading/error 썸네일 3개(폭 130). 왼쪽 띠 "괜찮아요 👍 / 고칠 게 있어요 🤔". 🤔일 때만 구성표 행마다 "빼요" 체크 + "다른 걸로" 드롭다운(같은 종류 컴포넌트만) + 번호 칩 + 자유 입력. 페이지 끝 "이대로 Figma로 만들어 주세요" 버튼(전 화면 👍이면 활성). db: `feedback/screen-<slug>` `{unit:"screen", n, label, reaction:"ok"|"fix", remove:[행 id], swap:{행 id→컴포넌트}, marks, markNames, text}` · `feedback/preview-go` · `feedback/preview-overall`. 모든 값은 design-rules.md의 `:root` 변수. 인터랙션 없음(정적). 반환의 "단위 목록"에 화면별 구성표를 그대로 싣는다.

## 배포 전 검사

```
python3 scripts/check_phase.py --phase probes --design-dir design
```

실패하면 고치고 재검. 통과 전에는 배포하지 않는다. **브라우저 자동화(claude-in-chrome, chrome-devtools)는 쓰지 않는다** — 렌더 확인은 사용자가 직접 한다. JS 문법 검사(`node --check`)만 한다.

## 배포

**하지 않는다.** 파일을 `OUT`에 저장하고 반환만 한다. 메인 대화가 hub.json에 탭을 추가하고 `python3 scripts/build_hub.py`로 허브를 만들어 같은 URL로 재배포한다. 자식 페이지는 허브 안 `<iframe srcdoc>`로 들어가며 `window.claude`는 부모 것을 쓴다(허브 빌더가 브리지를 주입). 페이지 코드는 평소처럼 `claude.use("db")`만 쓰면 된다.

## 반환 형식

```
KIND: <kind>
파일: <OUT>
URL: <artifact url>
단위 목록: <장면/축/섹션/앱 번호 → 이름 → (flow) 누를 버튼>
라벨 지도: <단위 → ①②③… → 영역 이름. 메인 대화가 db의 marks를 이 표로 해석한다>
db 경로: feedback/<unit>-<n> 규칙 확인
가정: <기본값으로 채운 것 목록 또는 없음>
검사: check_phase probes 통과 / 실패 내용
```
