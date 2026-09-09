---
name: oss-design-harness
description: PRD를 받아 디자인 초보 사용자와 인터뷰(구조→플로우→레퍼런스·취향→규칙)를 진행해 brief/decisions/design-rules를 확정하고, figma-builder·design-auditor 서브 에이전트로 Figma 화면을 생성·검증하는 하네스. "이 PRD로 UI 만들어줘", "디자인 인터뷰 해줘", "Figma 화면 만들어줘", "디자인 규칙 정해줘", "UI/UX 방향 잡아줘" 같은 요청에 트리거된다.
---

# oss-design-harness

**디자인을 한 번도 해본 적 없는 사용자**가 자기 PRD에 맞는 UI/UX 스타일을 찾아가도록 돕고, 확정된 결과를 Figma 화면으로 만드는 하네스.

**대상은 모바일 앱(iOS·Android)이다.** 모든 시안·로우파이·Figma 프레임은 390×844(iPhone 기준) 세로 화면으로 만든다. hover·커서·툴팁 같은 데스크톱 개념은 쓰지 않고 press·롱프레스·바텀시트·탭바·세이프 에어리어로 생각한다. PRD가 태블릿이나 웹도 요구하면 1단계에서 확인하고 예외로 기록한다.

핵심 원칙 네 가지. 모든 단계에서 지킨다.

1. **표상이 아니라 체험.** "모던한 게 좋으세요?" 같은 라벨형 질문은 금지. 만들어서 보여주고 "좋다/싫다 + 왜"를 받는다. 플로우도 다이어그램 대신 **"따라가 보기" 투어**(한 번에 화면 하나, 눌러야 할 버튼 하나, 누르면 어떻게 되는지 상태별로)로 눌러보게 한다. 회색 박스 와이어프레임 열몇 장을 늘어놓는 것도 전문 표기법이다 — 금지.
2. **페이지 안에서 고르게 한다. 링크는 하나, 선택은 최소.** 모든 시안은 `design/probes/hub.html` **허브 artifact 하나**에 탭으로 쌓인다(`scripts/build_hub.py`, 같은 URL 유지). 보여주는 화면에는 영역 번호 라벨(①②③, 화면당 최대 5개)을 붙이되, 비교 단위마다 **스킬이 추천 1개를 정해 이유 한 줄과 함께** 보여주고 기본 패널은 **"추천대로 할게요 / 다르게 할래요" 두 버튼**뿐이다. 핵심 선택 1줄(예: 마음에 드는 것 A/B/C)은 항상 보이게 두고, 세부(싫은 것·번호 칩·자유 입력)만 "다르게"를 눌렀을 때 펼친다. 용어(타이포·밀도 등)에는 작은 글씨로 쉬운 설명 한 줄을 붙인다. 저장은 페이지 안(db)에서 하고 스킬이 `read_db`로 읽어온다. 터미널로 "번호를 말해달라"고 하지 않는다.
3. **기본값이 항상 있다.** 사용자가 "모르겠어요"라고 해도 진행이 멈추지 않는다. `references/design-rules.md`의 기본값을 적용하고 `brief.md` 가정 로그에 남긴다.
4. **작은 단위로 확정한다.** 토큰 → 컴포넌트 → 화면 순서. 앞 단계가 확정되기 전에 다음 단계를 만들지 않는다. 확정된 것은 다시 묻지 않는다.

**브라우저 자동화 금지.** 이 스킬과 서브 에이전트는 `claude-in-chrome`·`chrome-devtools` 도구를 쓰지 않는다. 시안 페이지를 배포하면 링크만 주고, 렌더 확인은 사용자가 직접 한다.

## 산출물 위치

사용자 프로젝트 루트에 `design/` 폴더를 만든다. 이 스킬 폴더의 `templates/`를 복사해서 채운다.

```
design/
  brief.md          # 화면 목록, 상태, 플로우, 레퍼런스 반응, 역추출한 기준, 가정 로그
  decisions.md      # 축별 시안 반응과 선택 근거
  design-rules.md   # 확정된 토큰·컴포넌트·레이아웃 규칙 (figma-builder의 유일한 입력)
  references/       # 스킬이 수집한 경쟁 앱 스크린샷 (내부 비교용)
  icons.md          # lucide 아이콘 허용 목록: 액션·상태 → 아이콘 이름 1:1
  screens.md        # 화면별 컴포넌트 구성표 (최종 미리보기에서 확정, figma-builder 화면 STAGE의 입력)
  probes/           # 보여준 HTML 시안·로우파이 사본
  build-log.md      # figma-builder / design-auditor 진행 기록
```

## 전체 흐름

| 단계 | 하는 일 | 산출물 | 상세 |
|---|---|---|---|
| 1. 구조 | PRD에서 화면·상태·빈구멍을 표로 만들고, 빈 것만 **허브 첫 탭 "구조" 설문**(probe-renderer KIND=structure, 추천값 선택된 질문 ≤7 + "빠진 화면" 입력)으로 묻는다 | brief.md §화면 목록 | `references/interview-rules.md` §1, `references/structure-survey.md` |
| 2. 플로우 | 핵심 작업마다 시나리오 내러티브 + "따라가 보기" 투어(probe-renderer KIND=flow: 장면별 폰 1개, 상태 세그먼트, 시선 흐름, 의견 패널)로 체험시키고 페이지에 저장된 의견을 읽는다 | brief.md §플로우 | `references/lofi-flow.md` |
| 3. 레퍼런스·취향 | 스킬이 PRD 도메인의 경쟁 앱 3~5개를 직접 찾아 스크린샷 레퍼런스 페이지로 보여주고 컴포넌트별 반응을 받은 뒤, 고정 5축 HTML 시안으로 취향을 좁힌다 | brief.md §3, decisions.md | `references/reference-sourcing.md`, `references/taste-axes.md`, `references/probe-page.md` |
| 4. 규칙 | 기본값 위에 1~3단계 결과를 얹어 design-rules.md를 확정. 규칙 미리보기 페이지로 최종 확인 | design-rules.md | `references/design-rules.md` |
| 5. 생성 | `figma-builder`: 토큰 → 컴포넌트 → 화면. 단계마다 사용자 확인 | Figma, build-log.md | `.claude/agents/figma-builder.md` |
| 6. 검증 | `design-auditor`: A단계(속성 수치) + C단계(스크린샷) → 실패 시 라우팅 | build-log.md | `.claude/agents/design-auditor.md` |

1~4단계의 질문과 해석은 이 스킬이 메인 대화에서 직접 한다. HTML 페이지 제작은 `probe-renderer` 서브 에이전트에게 넘기되 **서브 에이전트는 배포하지 않는다** — 파일만 만들고, 메인 대화가 `design/probes/hub.json`에 탭을 추가한 뒤 `python3 scripts/build_hub.py`로 허브를 다시 만들어 **같은 URL로 재배포**한다(`capabilities: {db: {}}`). 병렬로 만든 탭들은 전부 끝난 뒤 한 번에 합쳐 링크 하나만 준다. 사용자 반응은 페이지 안 의견 패널에 저장되고(Artifact `db`, 컬렉션 `feedback`), 사용자가 "다 봤어"라고 하면 메인 대화가 `Artifact(action:"read_db", db_op:"list", collection:"feedback")`로 읽어 반환된 라벨 지도로 `marks`를 영역 이름으로 푼다. 의견이 0건일 때만 터미널로 묻는다. 5~6단계는 서브 에이전트에게 넘기되, **사용자 확인 게이트는 항상 메인 대화에서** 연다.

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
- 확정 후 design-rules.md 맨 위에 `status: confirmed`와 날짜를 적는다. figma-builder는 이 값이 없으면 시작하지 않는다.

## 4.5단계 최종 미리보기 (Figma로 만들기 전 마지막 게이트)

규칙이 confirmed 되면 **figma-builder를 부르기 전에** 허브 마지막 탭 "최종 미리보기"를 만든다. 전문은 `references/final-preview.md`.

- `check_phase.py --phase rules` 통과 → brief §1 화면 목록으로 `design/screens.md` 초안(화면별 컴포넌트 구성표, 템플릿 `templates/screens.md`)을 만든다 → `probe-renderer`에 `KIND=preview OUT=design/probes/final-preview.html`로 위임 → hub.json 마지막 탭 `{"file":"final-preview.html","title":"최종 미리보기","prefix":"screen-","stage":"5단계 직전"}` 추가 → `build_hub.py` → 같은 URL로 재배포.
- 사용자가 "다 봤어"라고 하면 `read_db`로 `feedback/screen-*`와 `feedback/preview-go`를 읽는다.
  - `preview-go` 있음 + 모든 화면 `ok` → screens.md를 확정본으로 저장하고 5단계 시작.
  - `fix`인 화면 → `remove`·`swap`을 screens.md에 반영하고 **그 화면만** 다시 그려 재배포. 2회까지. 3회째면 방향 오류로 보고 3단계 해당 축을 재확인한다.
  - 의견 0건 → 터미널로 "화면 n개 중 고칠 것이 있나요? (없음 / 번호)" 1회.
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
| 최종 미리보기 끝 | `read_db`에 `feedback/preview-go` 존재 + 모든 `screen-*`가 ok | 없으면 figma-builder를 부르지 않는다 |
| figma-builder STAGE 끝 | `python3 scripts/figma_audit.py --snapshot design/figma-snapshot.json --rules design/design-rules.md --brief design/brief.md --icons design/icons.md --screens design/screens.md --fix-list design/fix-list.md` | fix-list.md를 `STAGE=fix`에 넘긴다 |

종료 코드 0이 아니면 그 단계는 끝나지 않은 것이다. 출력의 `[FAIL]` 줄을 사용자에게 그대로 보여준다.

## 5~6단계 위임

```
Agent(subagent_type: "figma-builder",
      prompt: "design/design-rules.md, design/brief.md, design/screens.md를 읽고 STAGE=tokens 실행. 결과를 design/build-log.md에 기록.")
```

- 빌더는 한 번에 한 STAGE(tokens / components / screens / fix)만 실행하고 결과(노드 목록 + 스크린샷)를 돌려준다. **tokens·components 스크린샷은 사용자에게 보내지 않는다** — `figma_audit.py` 통과 여부만 한 줄로 알리고 다음 STAGE로 바로 간다. 사용자 확인은 **screens STAGE에서 화면이 하나 완성될 때마다** 그 화면 스크린샷 1장을 바로 보낸다(SendUserFile, 한 번에 몰아서 보내지 않는다). **Figma 화면에는 번호 라벨(①②③)을 넣지 않는다** — Figma는 최종 확정물이다. 번호 라벨은 HTML 시안(허브)에서만 쓴다. 자리표시 컴포넌트에도 실제 문구를 넣는다("버튼"·"텍스트" 같은 더미 금지). 사용자는 어색한 화면만 답하고, 답이 없으면 다음 화면을 계속 만든다. **screens STAGE는 기본이 병렬**이다 — 최종 확정은 4.5단계 HTML 미리보기에서 끝났으므로 Figma 화면은 순서대로 볼 필요가 없다. brief §1 화면을 3~4개씩 묶어 에이전트 2~3개에 나눠 돌린다(같은 페이지, x 위치를 화면 번호×470으로 고정해 겹치지 않게). components도 아이콘/나머지로 나눈다. build-log는 에이전트별 파일(build-log-screens-<n>.md)로 받아 메인이 합치고, 스냅샷·figma_audit은 마지막 에이전트 하나만 실행한다. Figma 읽기 예산(분당 10)은 에이전트 합산이므로 화면당 스크린샷 1회 외 읽기 금지. 기본 화면이 끝나면 **상태 변형(빈·로딩·실패·비활성·오프라인)을 10~12장** 추가로 만든다 — 전부 만들지 않고 PRD §3 까다로운 상황과 첫 사용(빈 상태)에 닿는 것만 고른다. 사용자에게는 그중 **핵심 3~4장만** 보내고 나머지는 목록으로 알린다.
- 각 STAGE가 끝나면 빌더가 `scripts/figma_snapshot.js`를 `use_figma`로 실행해 `design/figma-snapshot.json`을 갱신한다. 메인 대화에서 `figma_audit.py`를 돌려 A단계를 먼저 스크립트로 통과시킨다. 통과 전에는 design-auditor를 부르지 않는다.
- screens STAGE + figma_audit 통과 후 `design-auditor`를 호출한다 (C단계 스크린샷 판단 전담). 오디터 리포트는 `국소 결함 / 방향 오류 / 반복 실패` 셋 중 하나로 끝난다.
  - 국소 결함 → figma-builder에 `STAGE=fix` + 결함 목록. 고친 뒤 오디터 재실행. **결함 목록에 없는 것은 건드리지 않는다.**
  - 방향 오류 → 3단계 decisions.md의 해당 축만 재발산.
  - 반복 실패(같은 이유로 3회) → 사용자에게 에스컬레이션. "이 정도면 됐다"는 항상 사용자가 정한다.
- 재시도 상한 3회. 초과 시 현재 상태와 남은 문제를 표로 정리해 사용자에게 넘긴다.


## 운영 세팅 (확정된 작업 방식 — 모든 프로젝트 공통)

| 항목 | 방식 |
|---|---|
| 링크 | 항상 **허브 하나**(`design/probes/hub.html`, `capabilities: {db: {}}`). 탭은 단계마다 hub.json에 추가하고 같은 URL로 재배포. 외부 공유가 필요하면 `python3 scripts/build_hub.py --share` → `hub-share.html`을 **별도 artifact**(`capabilities: {}`, 공개 가능)로 배포. 공유본 저장은 보는 사람 브라우저에만 남는다고 사용자에게 말한다 |
| 저장 확인 | 사용자가 "저장했다"고 하면 믿지 말고 `read_db`로 확인한다. 허브 db 브리지는 postMessage RPC(build_hub.py가 주입) — 자식 페이지는 `claude.use("db")`만 쓴다. 탭 배지 카운트는 hub.json `prefix`/`prefixes`로 센다 |
| 선택 UI | 추천은 텍스트("추천: B — 이유"), 선택은 화면 클릭 또는 "전체 추천대로/괜찮아요" 버튼 하나. "다르게 할래요"·"전체 의견"·섹션별 👍·번호 칩 세부 패널은 **없다**. 용어에는 `.plain` 쉬운 설명 한 줄 |
| 탭 구성 | 구조 · 따라가 보기 · 레퍼런스 · 색상 · 모양·간격 · 글자·달력 · 아이콘 · 규칙 미리보기 · 최종 미리보기 (순서 고정) |
| 안내 문구 | 페이지에 범례·설명 문장 금지. 제목 아래 한 줄만 |
| 브라우저 | claude-in-chrome·chrome-devtools 금지. 렌더 확인은 사용자 |
| Figma | 번호 라벨 없음. tokens·components 스크린샷은 사용자에게 안 보냄. screens는 병렬 + 화면당 스크린샷 1장 즉시 전송. components STAGE는 사용자가 "필요 없다"고 하면 중단하고 화면은 자리표시(실제 문구)로 만든 뒤 fix STAGE에서 교체 |
| 게이트 | 단계 끝마다 `check_phase.py`, Figma STAGE 끝마다 `figma_audit.py`. 스크립트 exit 0 전에는 "끝났다"고 하지 않는다 |
| 기록 | 사용자 원문은 brief.md에 그대로, 해석은 별도. 추천 수락은 가정 로그에 "추천 수락"으로. 하네스 규칙 변경은 사용자가 산출물로 검증한 뒤에만 반영 |
| 일반성 | 도메인 이름·더미 데이터·화면 수를 스킬/스크립트/템플릿에 박지 않는다. 프로젝트 값은 `design/`에만 |

## 서브 에이전트 활용법

| 에이전트 | 언제 | 호출 형태 | 주의 |
|---|---|---|---|
| `probe-renderer` | 허브 탭 하나 만들 때마다 | `Agent(subagent_type:"probe-renderer", prompt:"KIND=<structure|flow|reference|taste|icons|rules|preview> OUT=design/probes/<file>.html …")` | 배포 안 함(파일만). 여러 탭은 **동시에** 띄운다(레퍼런스+취향 1페이지, 취향 3페이지 등). 반환된 라벨 지도를 보관 |
| `general-purpose` | 레퍼런스 앱 검색·스크린샷 수집, 조사 작업 | 사용자 답과 무관한 조사는 인터뷰 중에 **미리** 돌린다 | 결과는 `design/references/candidates.md`처럼 별도 파일로 받는다 |
| `figma-builder` | STAGE 하나씩. screens는 화면 3~4개씩 에이전트 2~3개 | `STAGE=screens` + 담당 화면 번호 + x 위치(번호×470) + 스크린샷 파일명 규칙 | build-log는 에이전트별 파일. 스냅샷·audit은 마지막 하나만. 변경 사항(색 값 등)은 `SendMessage`로 진행 중인 에이전트에 바로 알린다 |
| `design-auditor` | screens + figma_audit 통과 후 | 결함을 국소/방향/반복 셋 중 하나로 라우팅 | 국소 결함만 `STAGE=fix`에 넘긴다 |
| 진행 중 에이전트에 지시 변경 | 사용자 피드백이 오면 | `SendMessage(to:<agentId>, message:…)` — 재생성하지 말고 이어서 고치게 | 같은 파일을 두 에이전트가 동시에 쓰지 않게 영역·파일을 나눈다 |
| 파일 생성 감시 | 화면 스크린샷 순차 전송 | `Monitor`로 `design/screenshots/screen-*.png` 감시 → 새 파일마다 `SendUserFile` | 파일 크기가 2초간 안 변할 때만 보낸다(쓰기 중 전송 방지) |
| 병렬 원칙 | 사용자 답이 필요 없는 작업은 전부 병렬 | 인터뷰 대기 중에 레퍼런스 소싱·아이콘 탭·design-rules 초안을 미리 | 한 사용자 응답을 두 번 기다리게 하지 않는다 |
| 중단 | 사용자가 "필요 없다"면 `TaskStop` | 관련 에이전트에 분담 변경을 `SendMessage`로 알린다 | |

## Figma MCP 예산

현재 계정(Pro, Dev seat)은 읽기 도구가 **분당 10회, 하루 200회**다. 쓰기(`use_figma`)는 별도. 하루 예산을 STAGE별로 나눈다: tokens 5 · components 10 · screens 화면당 3 · 오디트 1회당 20. 서브 에이전트가 반환한 읽기 호출 수를 build-log.md `figma_read_calls_today`에 누적하고, 150을 넘으면 사용자에게 알리고 남은 스크린샷은 다음 날로 미룬다.

## Figma MCP가 없을 때

Figma MCP가 연결되지 않았거나 인증이 안 된 경우, 1~4단계는 그대로 진행하고 5단계 직전에 인증을 요청한다. 인증이 불가능하면 design-rules.md와 규칙 미리보기 HTML까지를 산출물로 마무리하고 그 사실을 명시한다. 조용히 범위를 줄이지 않는다.
