---
name: oss-design-harness
description: PRD를 받아 디자인 초보 사용자와 인터뷰(구조→플로우→레퍼런스·취향→규칙)를 진행해 brief/decisions/design-rules를 확정하고, 최종 산출물을 HTML(토큰·컴포넌트·화면·상태 프레임)로 만들어 html_audit 스크립트와 design-auditor로 검증하는 하네스. Figma는 사용자가 "Figma 생성"을 지시할 때만 figma-builder로 만든다. "이 PRD로 UI 만들어줘", "디자인 인터뷰 해줘", "Figma 화면 만들어줘", "디자인 규칙 정해줘", "UI/UX 방향 잡아줘" 같은 요청에 트리거된다.
---

# oss-design-harness

**디자인을 한 번도 해본 적 없는 사용자**가 자기 PRD에 맞는 UI/UX 스타일을 찾아가도록 돕고, 확정된 결과를 **HTML 화면**으로 내놓고 검증하는 하네스. Figma는 사용자가 **"Figma 생성"**을 명시할 때만 그 HTML을 입력으로 만든다.

**대상은 모바일 앱(iOS·Android)이다.** 모든 시안·로우파이·최종 HTML(·Figma 프레임)은 390×844(iPhone 기준) 세로 화면으로 만든다. hover·커서·툴팁 같은 데스크톱 개념은 쓰지 않고 press·롱프레스·바텀시트·탭바·세이프 에어리어로 생각한다. PRD가 태블릿이나 웹도 요구하면 1단계에서 확인하고 예외로 기록한다.

핵심 원칙 네 가지. 모든 단계에서 지킨다.

1. **표상이 아니라 체험.** "모던한 게 좋으세요?" 같은 라벨형 질문은 금지. 만들어서 보여주고 "좋다/싫다 + 왜"를 받는다. 플로우도 다이어그램 대신 **"따라가 보기" 투어**(한 번에 화면 하나, 눌러야 할 버튼 하나, 누르면 어떻게 되는지 상태별로)로 눌러보게 한다. 회색 박스 와이어프레임 열몇 장을 늘어놓는 것도 전문 표기법이다 — 금지.
2. **페이지 안에서 고르게 한다. 링크는 하나, 선택은 최소.** 모든 시안은 `design/probes/hub.html` **허브 artifact 하나**에 탭으로 쌓인다(`scripts/build_hub.py`, 같은 URL 유지). 보여주는 화면에는 영역 번호 라벨(①②③, 화면당 최대 5개)을 붙이되, 비교 단위마다 **스킬이 추천 1개를 정해 이유 한 줄과 함께** 보여주고 기본 패널은 **"추천대로 할게요 / 다르게 할래요" 두 버튼**뿐이다. 핵심 선택 1줄(예: 마음에 드는 것 A/B/C)은 항상 보이게 두고, 세부(싫은 것·번호 칩·자유 입력)만 "다르게"를 눌렀을 때 펼친다. 용어(타이포·밀도 등)에는 작은 글씨로 쉬운 설명 한 줄을 붙인다. 저장은 페이지 안(db)에서 하고 스킬이 `read_db`로 읽어온다. 터미널로 "번호를 말해달라"고 하지 않는다.
3. **기본값이 항상 있다.** 사용자가 "모르겠어요"라고 해도 진행이 멈추지 않는다. `references/design-rules.md`의 기본값을 적용하고 `brief.md` 가정 로그에 남긴다.
4. **작은 단위로 확정한다.** 토큰 → 컴포넌트 → 화면 순서. 앞 단계가 확정되기 전에 다음 단계를 만들지 않는다. 확정된 것은 다시 묻지 않는다.

**탐색·인터뷰용 브라우저 자동화 금지.** 이 스킬과 서브 에이전트는 `claude-in-chrome`·`chrome-devtools`·playwright MCP 도구로 페이지를 열거나 조작하지 않는다. 시안 페이지를 배포하면 링크만 주고, 인터뷰 중 렌더 확인은 사용자가 직접 한다. **예외: 검증 스크립트 내부의 headless 렌더.** `scripts/html_audit.py --render`가 playwright 라이브러리로 HTML을 헤드리스 렌더해 수치 검사·스크린샷을 만드는 것은 허용한다. 에이전트는 스크립트를 실행만 하고, 브라우저를 직접 다루지 않는다.

## 산출물 위치

사용자 프로젝트 루트에 `design/` 폴더를 만든다. 이 스킬 폴더의 `templates/`를 복사해서 채운다.

```
design/
  brief.md          # 화면 목록, 상태, 플로우, 레퍼런스 반응, 역추출한 기준, 가정 로그
  decisions.md      # 축별 시안 반응과 선택 근거
  design-rules.md   # 확정된 토큰·컴포넌트·레이아웃 규칙 (최종 HTML과 figma-builder의 유일한 스타일 입력)
  references/       # 스킬이 수집한 경쟁 앱 스크린샷 (내부 비교용)
  icons.md          # lucide 아이콘 허용 목록: 액션·상태 → 아이콘 이름 1:1
  screens.md        # 화면별 컴포넌트 구성표 (5단계에서 확정. html_audit·figma_parity의 입력)
  probes/           # 보여준 HTML 시안·로우파이 사본. rules-preview.html + final-preview.html = 최종 HTML 산출물
  screenshots/html/ # html_audit --render 스크린샷 (<slug>-<state>[@<width>].png)
  html-fix-list.md  # html_audit 결함 목록 (probe-renderer KIND=fix의 입력)
  build-log.md      # html-audit / 오디트 / fix / (선택) figma 진행 기록
```

## 전체 흐름

| 단계 | 하는 일 | 산출물 | 상세 |
|---|---|---|---|
| 1. 구조 | PRD에서 화면·상태·빈구멍을 표로 만들고, 빈 것만 **허브 첫 탭 "구조" 설문**(probe-renderer KIND=structure, 추천값 선택된 질문 ≤7 + "빠진 화면" 입력)으로 묻는다 | brief.md §화면 목록 | `references/interview-rules.md` §1, `references/structure-survey.md` |
| 2. 플로우 | 핵심 작업마다 시나리오 내러티브 + "따라가 보기" 투어(probe-renderer KIND=flow: 장면별 폰 1개, 상태 세그먼트, 시선 흐름, 의견 패널)로 체험시키고 페이지에 저장된 의견을 읽는다 | brief.md §플로우 | `references/lofi-flow.md` |
| 3. 레퍼런스·취향 | 스킬이 PRD 도메인의 경쟁 앱 3~5개를 직접 찾아 스크린샷 레퍼런스 페이지로 보여주고 컴포넌트별 반응을 받은 뒤, 고정 5축 HTML 시안으로 취향을 좁힌다 | brief.md §3, decisions.md | `references/reference-sourcing.md`, `references/taste-axes.md`, `references/probe-page.md` |
| 4. 규칙 | 기본값 위에 1~3단계 결과를 얹어 design-rules.md를 확정. 규칙 미리보기 페이지로 최종 확인 | design-rules.md | `references/design-rules.md` |
| 5. HTML 산출물 확정 | 규칙 미리보기(토큰·컴포넌트) + 최종 미리보기(화면)를 **최종 산출물**로 확정. 화면마다 상태 프레임 7종 + FormField가 있는 화면 `keyboard` + 웹 예외 화면 `guest-name`을 실물 크기로, 마크업 계약 준수(probe-renderer KIND=rules·preview) → 사용자 "이대로 확정해 주세요" → `html_audit.py` 정적 → `--render` | probes/rules-preview.html, probes/final-preview.html, screens.md, screenshots/html/ | `references/final-preview.md`, `references/probe-page.md` §마크업 계약 |
| 6. 검증 | `design-auditor`: A단계(`html_audit.py --render` 출력 첨부) + C단계(HTML 스크린샷 육안) → 국소 결함이면 probe-renderer KIND=fix → html_audit 재검 → 오디터 재실행 | build-log.md | `.claude/agents/design-auditor.md` |
| 7. Figma 생성 (선택) | 사용자가 **"Figma 생성"**이라고 명시할 때만. `figma-builder`가 확정 HTML·design-rules·icons·screens를 입력으로 토큰 → 컴포넌트 → 화면(default만, 상태는 요청 시) → `figma_parity` 검사 | Figma, build-log.md | `.claude/agents/figma-builder.md` |

1~4단계의 질문과 해석은 이 스킬이 메인 대화에서 직접 한다. HTML 페이지 제작은 `probe-renderer` 서브 에이전트에게 넘기되 **서브 에이전트는 배포하지 않는다** — 파일만 만들고, 메인 대화가 `design/probes/hub.json`에 탭을 추가한 뒤 `python3 scripts/build_hub.py`로 허브를 다시 만들어 **같은 URL로 재배포**한다(`capabilities: {db: {}}`). 병렬로 만든 탭들은 전부 끝난 뒤 한 번에 합쳐 링크 하나만 준다. 사용자 반응은 페이지 안 의견 패널에 저장되고(Artifact `db`, 컬렉션 `feedback`), 사용자가 "다 봤어"라고 하면 메인 대화가 `Artifact(action:"read_db", db_op:"list", collection:"feedback")`로 읽어 반환된 라벨 지도로 `marks`를 영역 이름으로 푼다. 의견이 0건일 때만 터미널로 묻는다. 5~7단계는 서브 에이전트에게 넘기되, **사용자 확인 게이트는 항상 메인 대화에서** 연다.

## 시작 절차

1. PRD 파일을 읽는다. 없으면 붙여넣어 달라고 한다. 한 문단짜리여도 그대로 시작한다. 빈구멍은 1단계에서 채운다.
2. 대상 프로젝트에 `design/`이 있으면 읽고 어느 단계까지 끝났는지 파악해 그 다음부터 이어간다.
3. 사용자에게 흐름을 4줄로 알려준다. "질문은 한 번에 최대 4개, 모르면 '모르겠어요'를 고르면 기본값으로 진행합니다. 화면은 링크 하나(허브)에 탭으로 쌓이고, 탭마다 제가 추천을 표시해두니 '추천대로'만 눌러도 됩니다"를 반드시 말한다.
4. `references/interview-rules.md`를 읽고 1단계를 시작한다. 화면 인벤토리 표를 먼저 만든 뒤 `probe-renderer`에 `KIND=structure OUT=design/probes/structure.html`로 설문 탭을 만들게 하고, hub.json 첫 탭으로 넣어 허브를 배포한다. 사용자가 "다 봤어"라고 하면 `read_db`(`feedback/structure-1`, `structure-2`, `structure-overall`)를 읽어 brief.md §1을 채우고 `check_phase.py --phase structure`를 돌린다. 의견 0건일 때만 터미널 질문(최대 4개).

## 질문 규칙 (요약. 전문은 references/interview-rules.md)

- 한 라운드에 질문 최대 4개. 각 질문에 **추천 옵션을 첫 번째**에 두고 `(추천)`을 붙인다.
- 모든 질문에 "이걸 정하면 무엇이 달라지는지" 한 줄을 붙인다.
- 모든 질문에 "모르겠어요 / 알아서 해주세요" 선택지를 둔다. 선택 시 기본값 적용 + 가정 로그.
- 취향·스타일에 관한 것은 **절대 말로 묻지 않는다.** 시안을 만들어 보여준다.
- 사용자의 자유서술은 원문 그대로 brief.md에 남기고, 역추출한 기준은 그 옆에 따로 적는다. 원문과 해석을 섞지 않는다.
- 위치·배치 요청은 **대상 · 기준 요소 · 순서** 세 가지를 확인해 다시 말해준다. ("제목을 위로" → "썸네일 위 별도 행, 제목→이미지→설명 순서, 모든 카드 공통. 맞나요?")

## 3단계 취향 추출 요령

- **레퍼런스는 스킬이 찾는다.** 사용자에게 레퍼런스를 달라고 하지 않는다. `references/reference-sourcing.md`대로 PRD 도메인의 경쟁 앱 3~5개를 검색해 고르고, 앱스토어 스크린샷을 모아 `probe-renderer`(KIND=reference)로 레퍼런스 페이지를 만든다. 앱마다 "왜 골랐는지" 한 줄과 컴포넌트 번호 라벨. 사용자는 "가져오고 싶은 번호 / 싫은 번호 / 이유"만 답한다. 전체를 따라 하지 않는다. 일부만 가져온다. 사용자가 따로 가진 캡처가 있으면 같은 페이지에 추가한다.
- **시안 생성.** PRD의 대표 화면 하나를 로우파이 콘텐츠로 그린다. 축 하나만 바꾸고 나머지 축은 기본값(또는 앞 축에서 확정된 값)에 고정한다. 축을 섞으면 왜 골랐는지 알 수 없게 된다.
- 페이지 제작은 위임한다: `Agent(subagent_type: "probe-renderer", prompt: "KIND=taste AXES=1,4 FIXED=<앞 축 확정값> RECOMMEND=<축별 추천 시안과 이유> OUT=design/probes/taste-color.html")`. 탭은 주제별 3개(색상=축1+4 / 모양·간격=축3+2 / 글자·달력=축5+추가축, `taste-axes.md` 표 참고). 추천은 메인 대화가 PRD 도메인을 보고 정한다. 반환 후 hub.json에 탭을 추가하고 `build_hub.py` → 허브를 같은 URL로 재배포한다. 라벨 지도를 보관한다.
- 반응은 페이지 안에서 받는다. 축마다 "추천: B — 이유" 텍스트 한 줄이 있고, 사용자는 **마음에 드는 폰 화면을 누르면** 즉시 `feedback/axis-<n>`에 저장된다(text: 추천이면 "추천대로", 아니면 "직접 선택"). 버튼·세부 의견 칸은 없다. 사용자가 "다 봤어"라고 하면 `read_db`로 읽어 decisions.md에 옮긴다. 저장이 0건인 축은 추천값 + 가정 로그. 한 페이지에 축 2개까지.
- 한 축에서 "모르겠어요"면 기본값 + 가정 로그. 좋다와 싫다의 이유가 충돌하면 그 축만 중간값 시안으로 2차를 한 번 보여준다. 3차는 없다.

## 4단계 규칙 확정 요령

- `design/icons.md`를 만든다. brief.md 화면 목록의 모든 액션·상태·탭·빈 상태를 행으로 놓고 lucide 이름을 하나씩 배정한다 (템플릿 `templates/icons.md`). 같은 의미에 두 아이콘, 같은 아이콘에 두 의미가 없는지 표를 훑어 확인한다. 규칙 미리보기 페이지에 이 목록을 실제 lucide SVG로 그려 사용자에게 보여준다.
- `references/design-rules.md`의 항목을 전부 채운 `design/design-rules.md`를 만든다. PRD 화면에 등장하지 않는 항목(예: 썸네일 없는 서비스)은 기본값으로 채우고 `(미사용)` 표시.
- 규칙 미리보기는 `probe-renderer`에 `KIND=rules OUT=design/probes/rules-preview.html`로 위임한다. 버튼 3사이즈 × 5상태, 아이콘 허용 목록 전체, 썸네일 그리드(선택 상태 포함), 바텀시트·다이얼로그, 탭바·상단 앱바, 타이포 역할표, 빈 상태·로딩 상태가 390 폭 프레임 안에 번호 라벨과 함께 담긴다. 페이지 상단 "전체 추천대로 할게요" 하나로 11개 섹션을 한 번에 저장하고, 어색한 섹션만 부품 칩·이유를 적어 저장한다. 스킬이 `feedback/section-<n>`을 읽어 marks가 있는 섹션에만 국소 질문("눌렀을 때 색이 너무 어두운가요, 너무 약한가요?")을 허용한다. 아이콘 탭(KIND=icons, "전체 추천대로" + 카드마다 추천·대안 2개 상시 표시)은 취향과 무관하므로 3단계와 **병렬**로 미리 만든다.
- 확정 후 design-rules.md 맨 위에 `status: confirmed`와 날짜를 적는다. 최종 미리보기(5단계)와 figma-builder는 이 값이 없으면 시작하지 않는다.

## 5단계 HTML 산출물 확정 (최종 미리보기)

규칙이 confirmed 되면 허브 마지막 탭 "최종 미리보기"를 만든다. **규칙 미리보기 탭(토큰·컴포넌트) + 최종 미리보기 탭(화면)이 이 하네스의 최종 산출물이다.** 둘 다 `references/probe-page.md` §마크업 계약을 지켜야 `html_audit.py`가 검사할 수 있다. 전문은 `references/final-preview.md`.

- `check_phase.py --phase rules` 통과 → brief §1 화면 목록으로 `design/screens.md` 초안(화면별 컴포넌트 구성표, 템플릿 `templates/screens.md`)을 만든다 → `probe-renderer`에 `KIND=preview OUT=design/probes/final-preview.html`로 위임 → hub.json 마지막 탭 `{"file":"final-preview.html","title":"최종 미리보기","prefix":"screen-","stage":"5단계"}` 추가 → `build_hub.py` → 같은 URL로 재배포.
- 화면마다 default 1장 + 상태 프레임(empty·loading·error·long-title·many-items·text-120, FormField가 있는 화면 `keyboard`, 웹 예외 화면 `guest-name`)을 **전부 실물 크기** `.phone[data-state]`로 그린다. 썸네일로 줄이지 않는다.
- 사용자가 "다 봤어"라고 하면 `read_db`로 `feedback/screen-*`와 `feedback/preview-go`를 읽는다.
  - `preview-go` 있음 + 모든 화면 `ok` → screens.md를 확정본으로 저장하고 `html_audit.py` 정적 → `--render` 게이트(아래 페이즈 게이트 표)를 돌린다.
  - `fix`인 화면 → `remove`·`swap`을 screens.md에 반영하고 **그 화면만** 다시 그려 재배포. 2회까지. 3회째면 방향 오류로 보고 3단계 해당 축을 재확인한다.
  - 의견 0건 → 터미널로 "화면 n개 중 고칠 것이 있나요? (없음 / 번호)" 1회.
- 확정 버튼 문구는 **"이대로 확정해 주세요"**다("Figma로 만들어 주세요"가 아니다). `preview-go`는 HTML 확정이지 Figma 생성 요청이 아니다.
- 이 탭에서는 규칙 값이나 화면 추가를 바꾸지 않는다. 규칙은 규칙 미리보기 탭, 화면 추가는 1단계 구조 탭으로 돌아간다.

## 페이즈 게이트 (스크립트 검증)

각 단계를 "끝났다"고 선언하기 전에 반드시 스크립트를 돌린다. LLM의 자기 보고를 믿지 않는다. 스크립트는 이 레포의 `scripts/`에 있다. 스킬만 복사된 환경이면 `scripts/`도 함께 복사한다.

| 시점 | 명령 | 실패 시 |
|---|---|---|
| 1단계 구조 끝 | `python3 scripts/check_phase.py --phase structure` | 빈 셀·미선택 항목을 채우는 질문 라운드 1회 더 |
| 2단계 플로우 끝 | `python3 scripts/check_phase.py --phase flow` | 시나리오 번호와 투어 장면 라벨을 맞춘다 |
| 시안 페이지 배포 직전 | `python3 scripts/check_phase.py --phase probes` → `python3 scripts/build_hub.py` | HTML 수정 후 재검 (의견 패널·db 코드·장면 구조·상태 세그먼트 검사). 허브 빌드가 실패하면 배포하지 않는다 |
| 3단계 취향 끝 | `python3 scripts/check_phase.py --phase taste` | 미확정 축 재질문 또는 가정 로그 추가 |
| 4단계 규칙 끝 | `python3 scripts/check_phase.py --phase rules` | 통과 전에는 `status: confirmed`를 쓰지 않는다 |
| 최종 미리보기 확인 | `read_db`에 `feedback/preview-go` 존재 + 모든 `screen-*`가 ok | 없으면 html_audit 게이트로 가지 않는다 |
| 5단계 HTML 산출물 끝 | `python3 scripts/html_audit.py --design-dir design` exit 0 → `python3 scripts/html_audit.py --design-dir design --render --fix-list design/html-fix-list.md --screenshots design/screenshots/html` exit 0 | html-fix-list.md를 probe-renderer `KIND=fix`에 넘기고 재검 |
| 6단계 검증 끝 | design-auditor 리포트 진단이 **"통과"** | 국소 결함 → `KIND=fix` / 방향 오류 → 3단계 축 / 반복 실패 → 에스컬레이션 |
| Figma 생성 시 STAGE 끝 | `scripts/figma_parity.js`(use_figma 1회) → `python3 scripts/figma_parity.py --actual design/figma-parity.json --rules design/design-rules.md --icons design/icons.md --screens design/screens.md [--states …]` exit 0 | 불일치 목록을 design-auditor → figma-builder `STAGE=fix`로 |
| 전수 스냅샷 (사용자 요청 시만) | `figma_snapshot.js` → `python3 scripts/figma_audit.py --snapshot design/figma-snapshot.json --rules design/design-rules.md --brief design/brief.md --icons design/icons.md --screens design/screens.md --fix-list design/fix-list.md` | fix-list.md를 `STAGE=fix`에 넘긴다 |

playwright는 `.venv`에 설치한다(`scripts/README.md` 참고). 없으면 `--render`는 exit 2.

종료 코드 0이 아니면 그 단계는 끝나지 않은 것이다. 출력의 `[FAIL]` 줄을 사용자에게 그대로 보여준다. exit 2(입력 파일 없음·렌더 환경 없음)는 결함이 아니라 준비 문제다 — 파일·playwright 설치부터 확인하고, 조용히 `--render`를 건너뛰지 않는다.

## 5~7단계 위임

Figma는 선택이다. 사용자 결정에 필요한 정보는 5단계 HTML 허브에서 이미 다 나오고, Figma 생성·전수 스냅샷 검증은 비용이 크다(지난 과제에서 3시간 이상, 그중 절반이 `use_figma` 반환 20KB 제한 때문에 60회로 나눠 받은 스냅샷 수집). 그래서 검증 기준은 HTML이고, Figma는 지시가 있을 때 만든 뒤 이름·개수 일치(parity)만 본다.

### 5단계 — HTML 산출물 (probe-renderer)

```
Agent(subagent_type: "probe-renderer",
      prompt: "KIND=preview OUT=design/probes/final-preview.html")
```

- 게이트 순서: 렌더러 배포 전 검사(`check_phase --phase probes` + `html_audit.py` 정적) → 허브 재배포 → 사용자 "이대로 확정해 주세요"(`preview-go`) → 메인이 `html_audit.py` 정적 → `--render`.
- `--render` 실패 → `design/html-fix-list.md`를 `Agent(subagent_type:"probe-renderer", prompt:"KIND=fix FIX=design/html-fix-list.md OUT=design/probes/<고칠 파일>")`에 넘긴다 → 정적·렌더 재검 → 허브 재배포. 사용자 확인 없이 돌린다(확정된 규칙에 맞추는 수정이다). 재시도 상한 3회.
- **스크린샷 전송(Figma 때와 같은 UX)**: `--render` 통과 후 `design/screenshots/html/<slug>-default.png`를 brief §1 순서로 **화면당 1장씩 즉시** `SendUserFile`(몰아서 보내지 않는다). 상태 묶음(empty·loading·error·long-title·many-items·text-120·keyboard·guest-name·@360·@430)은 보내지 않고 "화면별 상태 n장" 목록으로 알린다. 사용자가 특정 상태를 보자고 하면 그 파일만 보낸다. 사용자는 어색한 화면만 답한다. fix 뒤에는 바뀐 화면의 default만 다시 보낸다.

### 6단계 — 검증 (design-auditor)

- `html_audit.py --render` exit 0 후 호출한다. 오디터는 A단계에 스크립트 출력을 그대로 붙이고, C단계는 `design/screenshots/html/*.png`를 직접 본다. **Figma 읽기 0회.** 리포트는 `통과 / 국소 결함 / 방향 오류 / 반복 실패` 중 하나로 끝난다.
  - 국소 결함 → probe-renderer `KIND=fix` + 결함 목록 → html_audit 정적·렌더 재검 → 오디터 재실행. **결함 목록에 없는 것은 건드리지 않는다.**
  - 방향 오류 → 3단계 decisions.md의 해당 축만 재발산.
  - 반복 실패(같은 이유로 3회) → 사용자에게 에스컬레이션. "이 정도면 됐다"는 항상 사용자가 정한다.
- 재시도 상한 3회. 초과 시 현재 상태와 남은 문제를 표로 정리해 사용자에게 넘긴다.
- "통과"면 산출물은 허브 링크 + `design/`(design-rules.md·icons.md·screens.md·probes/·screenshots/html/)이다. Figma가 필요하면 "Figma 생성"이라고 말하면 된다고 한 줄만 알린다. 먼저 권하지 않는다.

### 7단계 — Figma 생성 (선택. 사용자가 "Figma 생성"을 명시했을 때만)

```
Agent(subagent_type: "figma-builder",
      prompt: "Figma 생성 지시 있음. STAGE=tokens. 입력: design/probes/final-preview.html, design/probes/rules-preview.html, design/design-rules.md, design/icons.md, design/screens.md. 결과는 design/build-log.md에 기록.")
```

- 트리거는 사용자의 명시 지시뿐이다. 스킬이 6단계 뒤에 자동으로 이어가지 않는다. 6단계 통과 전에 지시가 오면 남은 결함을 알리고 진행 여부는 사용자가 정한다.
- 빌더는 한 번에 한 STAGE(tokens / components / screens / fix)만 실행한다. 값은 design-rules.md, 배치·문구는 확정 HTML을 따른다. **screens는 default 프레임만** 만든다. 상태 프레임은 사용자가 요청한 것만 프롬프트에 `STATES=empty,error`처럼 넘긴다.
- STAGE 끝마다 빌더가 `figma_parity.js`를 `use_figma`로 1회 실행해 `design/figma-parity.json`에 저장하고 `figma_parity.py`를 돌린다. 전수 스냅샷(`figma_snapshot.js` + `figma_audit.py`)은 사용자가 요청할 때만 `SNAPSHOT=full`로.
- **tokens·components 스크린샷은 사용자에게 보내지 않는다** — parity 통과 여부만 한 줄. screens는 화면 default가 하나 완성될 때마다 1장 즉시 `SendUserFile`. **Figma 화면에는 번호 라벨(①②③)을 넣지 않는다.** 자리표시 컴포넌트에도 HTML과 같은 실제 문구를 넣는다.
- **screens STAGE는 기본이 병렬**이다. brief §1 화면을 3~4개씩 묶어 에이전트 2~3개에 나눠 돌린다(같은 페이지, x 위치를 화면 번호×470으로 고정). build-log는 에이전트별 파일(build-log-screens-<n>.md)로 받아 메인이 합치고, parity는 마지막 에이전트 하나만 실행한다.
- parity 실패 → design-auditor(Figma parity 모드)가 불일치를 국소/반복으로 라우팅 → 국소면 figma-builder `STAGE=fix` + 결함 목록 → parity 재검. 재시도 상한 3회.


## 운영 세팅 (확정된 작업 방식 — 모든 프로젝트 공통)

| 항목 | 방식 |
|---|---|
| 링크 | 항상 **허브 하나**(`design/probes/hub.html`, `capabilities: {db: {}}`). 탭은 단계마다 hub.json에 추가하고 같은 URL로 재배포. 외부 공유가 필요하면 `python3 scripts/build_hub.py --share` → `hub-share.html`을 **별도 artifact**(`capabilities: {}`, 공개 가능)로 배포. 공유본 저장은 보는 사람 브라우저에만 남는다고 사용자에게 말한다 |
| 저장 확인 | 사용자가 "저장했다"고 하면 믿지 말고 `read_db`로 확인한다. 허브 db 브리지는 postMessage RPC(build_hub.py가 주입) — 자식 페이지는 `claude.use("db")`만 쓴다. 탭 배지 카운트는 hub.json `prefix`/`prefixes`로 센다 |
| 선택 UI | 추천은 텍스트("추천: B — 이유"), 선택은 화면 클릭 또는 "전체 추천대로/괜찮아요" 버튼 하나. "다르게 할래요"·"전체 의견"·섹션별 👍·번호 칩 세부 패널은 **없다**. 용어에는 `.plain` 쉬운 설명 한 줄 |
| 탭 구성 | 구조 · 따라가 보기 · 레퍼런스 · 색상 · 모양·간격 · 글자·달력 · 아이콘 · 규칙 미리보기 · 최종 미리보기 (순서 고정) |
| 안내 문구 | 페이지에 범례·설명 문장 금지. 제목 아래 한 줄만 |
| 브라우저 | 탐색·인터뷰용 claude-in-chrome·chrome-devtools·playwright MCP 금지. 인터뷰 중 렌더 확인은 사용자. 검증 스크립트(`html_audit.py --render`) 안의 headless playwright만 허용 |
| 최종 산출물 | HTML — 허브의 규칙 미리보기(토큰·컴포넌트) + 최종 미리보기(화면·상태 프레임 전부 실물 크기). 마크업 계약(`probe-page.md`) 준수. 렌더 스크린샷은 화면당 default 1장 즉시 전송, 상태는 목록 |
| Figma | 사용자가 **"Figma 생성"**을 명시할 때만. 번호 라벨 없음. tokens·components 스크린샷은 사용자에게 안 보냄. screens는 default만(상태는 `STATES=` 요청분만), 병렬 + 화면당 스크린샷 1장 즉시 전송. 검증은 `figma_parity`(이름·개수 일치). 전수 스냅샷은 요청 시만. components STAGE는 사용자가 "필요 없다"고 하면 중단하고 화면은 자리표시(실제 문구)로 만든 뒤 fix STAGE에서 교체 |
| 게이트 | 단계 끝마다 `check_phase.py`, 5단계 끝 `html_audit.py`(정적 → `--render`), Figma STAGE 끝마다 `figma_parity.py`. 스크립트 exit 0 전에는 "끝났다"고 하지 않는다 |
| 기록 | 사용자 원문은 brief.md에 그대로, 해석은 별도. 추천 수락은 가정 로그에 "추천 수락"으로. 하네스 규칙 변경은 사용자가 산출물로 검증한 뒤에만 반영 |
| 일반성 | 도메인 이름·더미 데이터·화면 수를 스킬/스크립트/템플릿에 박지 않는다. 프로젝트 값은 `design/`에만 |

## 서브 에이전트 활용법

| 에이전트 | 언제 | 호출 형태 | 주의 |
|---|---|---|---|
| `probe-renderer` | 허브 탭 하나 만들 때마다 + HTML 결함 수정 | `Agent(subagent_type:"probe-renderer", prompt:"KIND=<structure|flow|reference|taste|icons|rules|preview|fix> OUT=design/probes/<file>.html …")` | 배포 안 함(파일만). 여러 탭은 **동시에** 띄운다(레퍼런스+취향 1페이지, 취향 3페이지 등). 반환된 라벨 지도를 보관. `KIND=fix`는 결함 목록만 고치고 html_audit 재검 |
| `general-purpose` | 레퍼런스 앱 검색·스크린샷 수집, 조사 작업 | 사용자 답과 무관한 조사는 인터뷰 중에 **미리** 돌린다 | 결과는 `design/references/candidates.md`처럼 별도 파일로 받는다 |
| `design-auditor` | `html_audit.py --render` 통과 후. Figma 생성 시엔 parity 실패 때 | 결함을 통과/국소/방향/반복 중 하나로 라우팅 | 국소 결함은 HTML이면 probe-renderer `KIND=fix`, Figma면 figma-builder `STAGE=fix` |
| `figma-builder` | **"Figma 생성" 지시가 있을 때만.** STAGE 하나씩. screens는 화면 3~4개씩 에이전트 2~3개 | 프롬프트 첫머리 "Figma 생성 지시 있음" + `STAGE=screens` + 담당 화면 번호 + x 위치(번호×470) + (요청 시) `STATES=` | build-log는 에이전트별 파일. parity는 마지막 하나만. 변경 사항(색 값 등)은 `SendMessage`로 진행 중인 에이전트에 바로 알린다 |
| 진행 중 에이전트에 지시 변경 | 사용자 피드백이 오면 | `SendMessage(to:<agentId>, message:…)` — 재생성하지 말고 이어서 고치게 | 같은 파일을 두 에이전트가 동시에 쓰지 않게 영역·파일을 나눈다 |
| 파일 생성 감시 | 화면 스크린샷 순차 전송 | `html_audit.py --render`를 백그라운드로 돌리고 `Monitor`로 `design/screenshots/html/*-default.png`(Figma면 `design/screenshots/figma/*-default.png`) 감시 → 새 파일마다 `SendUserFile` | 파일 크기가 2초간 안 변할 때만 보낸다(쓰기 중 전송 방지) |
| 병렬 원칙 | 사용자 답이 필요 없는 작업은 전부 병렬 | 인터뷰 대기 중에 레퍼런스 소싱·아이콘 탭·design-rules 초안을 미리 | 한 사용자 응답을 두 번 기다리게 하지 않는다 |
| 중단 | 사용자가 "필요 없다"면 `TaskStop` | 관련 에이전트에 분담 변경을 `SendMessage`로 알린다 | |

## Figma MCP 예산 (Figma 생성 지시가 있을 때)

1~6단계는 Figma를 읽지도 쓰지도 않는다. 아래는 7단계에만 적용한다.

현재 계정(Pro, Dev seat)은 읽기 도구가 **분당 10회, 하루 200회**다. 쓰기(`use_figma`)는 별도지만 **반환값이 20KB로 잘린다** — 큰 JSON을 한 번에 받으려 하지 않는다(parity는 이름·개수만 받아 1회에 끝난다). 읽기 예산: tokens 0 · components 1 · screens 화면(default)당 1 · parity 0(use_figma) · 오디트(parity 실패 원인 확인) 최대 5. 서브 에이전트가 반환한 읽기 호출 수를 build-log.md `figma_read_calls_today`에 누적하고, 150을 넘으면 사용자에게 알리고 남은 스크린샷은 다음 날로 미룬다.

## Figma 생성 지시가 있는데 Figma MCP가 없을 때

Figma MCP가 연결되지 않았거나 인증이 안 된 경우 인증(`/mcp`)을 요청한다. 인증이 불가능하면 6단계까지의 HTML 산출물(허브 + `design/`)이 최종 결과물이라고 명시하고 마무리한다. 조용히 범위를 줄이지 않는다. 1~6단계는 Figma 연결과 무관하게 끝까지 진행한다.
