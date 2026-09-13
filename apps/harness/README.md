# oss-design-harness

**현업 디자이너의 판단 기준(안목)을 추출해, 에이전트에 최적화된 형태로 재구성하는 Figma-네이티브 디자인 하네스.**

VIBE MAFIA CLUB 하네스톤 2회차(2026-09-05)를 계기로 이너서클 코파운더들과 함께 만드는 오픈소스 프로젝트입니다.
지향점: `ui-ux-pro-max` 급, 현업에서 쓸 수 있는 수준의 skill.

## 이 레포의 상태

**team-3 버전이 들어와 있습니다.** 하네스톤 2회차 team-3([harnessthon-2-team-3](https://github.com/vibemafiaclub/harnessthon-2-team-3))이 빈 템플릿을 채운 판본을 이 경로(`apps/harness/`)로 가져왔습니다. 4단계 뼈대는 더 이상 `TODO`가 아니라 실행 가능한 스킬입니다.

- 디자인 초보 사용자용 **인터뷰 스킬**(구조 → 플로우 → 레퍼런스·취향 → 규칙)이 메인 대화를 이끌고, `probe-renderer`가 시안과 **최종 HTML 산출물**을, `design-auditor`가 검증을, `figma-builder`가 (지시가 있을 때만) Figma 생성을 맡습니다.
- 취향은 라벨형 질문 대신 **HTML 시안 비교**로 좁히고, 규칙은 공통 디자인 이슈(`docs/이슈.md`·`docs/desingissue.md`)에서 뽑은 **기본값**으로 관리합니다.
- **최종 산출물은 HTML**(토큰·컴포넌트·화면·상태 프레임)입니다. `scripts/html_audit.py`가 정적 검사와 헤드리스 렌더 검사로 판정하고, design-auditor가 렌더 스크린샷을 눈으로 봅니다. Figma는 사용자가 **"Figma 생성"**이라고 지시할 때만 만들고, 이름·개수 일치(`figma_parity`)만 검사합니다.
- 단계 종료는 LLM 자기보고가 아니라 `scripts/`의 **결정론적 게이트 스크립트**로 판정합니다.
- 판단 기준의 구체값(무엇을 보고 "고급스럽다"고 판단하는지)은 여전히 프로젝트마다 다릅니다 — 다른 팀·참가자 판본과 대조하는 것이 이 오픈소스의 목적입니다.

**왜 HTML이 기준인가.** 첫 과제에서 Figma 생성·검증에 3시간 이상 걸렸고, 그중 절반이 `use_figma` 반환 20KB 제한 때문에 60회로 나눠 받은 스냅샷 수집이었습니다. 반면 사용자가 결정하는 데 필요한 정보(구성·상태·스타일)는 HTML 허브 단계에서 이미 다 나왔습니다. 그래서 검토·검증은 HTML/CSS/JS/이미지로 하고(검증 스크립트 안의 헤드리스 렌더는 허용, 탐색용 브라우저 자동화는 여전히 금지), Figma는 필요할 때 확정 HTML을 옮겨 만드는 선택 단계로 바꿨습니다.

## 프레임워크 — 4단계 판단 구조

디자이너가 일하는 **순서**를 그대로 흉내내지 않습니다. 사람이 순서대로 일하는 이유의 상당수는 사람의 기억력·주의력 한계를 우회하는 것이지, 결과가 좋아지는 진짜 원인이 아닙니다. 대신 각 단계가 실제로 하려던 일(**판단 기준**)만 뽑아서, 에이전트가 잘하는 방식(병렬 생성, 다각도 교차 비평)으로 다시 구현합니다.

| 단계 | 시점 | 하는 일 |
|---|---|---|
| **0. 요구사항 정렬** | 화면을 만들기 **전** | 뭘 만들지 자체가 불확실할 때, 레퍼런스/시나리오를 보여주고 반응(좋다/싫다+이유)을 받아 암묵적 판단기준을 뽑아낸다. 라벨형 질문("모던한 게 좋으세요?") 금지. |
| **B. 발산·수렴** | 만드는 도중, 정답이 여러 개일 때 | 독립적인 축(무드/밀도/난이도 등)을 먼저 나누고, 축마다 후보를 병렬 생성해 비교·수렴한다. |
| **A. 구조적 사실 검증** | 다 만든 후 | 데이터로 예/아니오 확인 가능한 것 (spacing, 컴포넌트 재사용, 네이밍, variant 존재 여부). |
| **C. 미적·게슈탈트 판단** | 다 만든 후 | 스크린샷을 렌더해서 실제로 봐야만 아는 것 (색온도 일관성, 위계, 여백 리듬, 클리셰 여부, 엣지케이스 완성도). |

C단계에서 탈락하면 원인에 따라 세 갈래로 라우팅한다 — ① 국소 결함(그 속성만 고쳐 C 재검) ② 방향 자체가 틀림(B로 회귀) ③ 반복 실패(0으로 에스컬레이션). 재시도 상한을 두고, 최종 판단은 항상 사람이 내린다.

자세한 배경·논리 검증 과정은 킥오프 자료(`docs/concept.md`) 참고.

## 구조

```
.claude/skills/oss-design-harness/SKILL.md          # 하네스 본체 — 인터뷰(1~4단계) + HTML 산출물·검증(5~6단계) + Figma 생성(선택 7단계)
.claude/skills/oss-design-harness/references/
  interview-rules.md                                 # 디자인 초보용 질문 규칙, 단계별 스크립트, 역추출 패턴
  taste-axes.md                                      # 고정 5축(밝기·밀도·형태·강조색·타이포) + 프로젝트 추가 축
  probe-page.md                                      # HTML 시안·로우파이·규칙 미리보기 페이지 규격 + 최종 HTML 마크업 계약(data-*)
  lofi-flow.md                                       # 시나리오 내러티브 + 클릭형 로우파이 규칙
  design-rules.md                                    # docs/이슈.md·desingissue.md를 기본값 있는 규칙 키로 변환
  reference-sourcing.md                              # 스킬이 경쟁 앱을 검색·캡처해 레퍼런스 페이지로 만드는 절차
  structure-survey.md · final-preview.md            # 허브 첫 탭(구조 설문)과 마지막 탭(최종 미리보기 = 5단계 HTML 산출물) 스펙
.claude/agents/probe-renderer.md                     # 시안·규칙 미리보기·최종 미리보기 HTML 제작(파일만, 배포는 메인) + KIND=fix 결함 수정
.claude/agents/design-auditor.md                     # A단계 html_audit --render 출력 + C단계 HTML 스크린샷 판단 + 라우팅
.claude/agents/figma-builder.md                      # "Figma 생성" 지시 시에만: 토큰 → 컴포넌트 → 화면(default) → fix + figma_parity
.claude/skills/oss-design-harness/templates/         # brief · decisions · design-rules · icons · screens · build-log · structure-survey — design/ 산출물 양식
docs/concept.md                                      # 컨셉 스펙 전문
docs/이슈.md · docs/desingissue.md                    # 규칙의 원천이 된 공통 디자인 이슈
docs/example-prd.md                                  # 예시 PRD (청첩장모임 스케줄러)
scripts/                                             # check_phase · build_hub · html_audit · figma_parity · (전수 검사용) figma_snapshot · figma_audit + 테스트
```

## 전체 흐름 한눈에

**[FigJam 흐름도 열기](https://www.figma.com/board/BW8kTvRl6xeGHp1cOMOgHw)** — "디자인 도우미 전체 흐름 (최종, 위에서 아래)" (Figma 생성 이전 판본 기준)

1. **대화로 정하기** 기획서 → 화면 목록 → 눌러보며 순서 확인 → 비슷한 앱 → 스타일(색상 / 모양·간격 / 글자) → 아이콘 → 규칙. 모든 탭은 허브 링크 하나에 쌓이고, 사용자는 "추천대로 / 다르게"만 고른다.
2. **HTML로 확정하기** 규칙 미리보기(색·글자·간격·부품) + 최종 미리보기(모든 화면과 빈·로딩·실패·긴 제목·많은 항목·글자 확대·키보드 상태를 실물 크기로). 사용자가 "이대로 확정해 주세요"를 누르면 이것이 최종 결과물이다.
3. **검사하기** `html_audit.py`로 숫자 검사(정적 → 헤드리스 렌더) → 렌더 스크린샷을 화면당 1장씩 받아 확인 → design-auditor가 눈으로 검사 → 작은 문제는 그 부분만 HTML에서 고치고, 방향이 틀리면 스타일로 되돌아가고, 3번 반복 실패면 사람이 결정한다.
4. **Figma로 옮기기 (선택)** 사용자가 "Figma 생성"이라고 말할 때만. 확정 HTML을 보고 색·글자·간격 → 부품 → 화면(기본 상태만, 다른 상태는 요청 시) 순서로 만들고, 이름·개수가 HTML·규칙과 맞는지만 검사한다.

## 사용법

PRD 하나만 있으면 시작할 수 있다. 예시 PRD는 `docs/example-prd.md`.

1. `apps/harness`를 프로젝트 루트로 해서 Claude Code를 실행한다 (`.claude/`와 `scripts/`가 이 경로 기준이다). 렌더 검사용으로 playwright를 `.venv`에 설치한다(`python3 -m venv .venv && .venv/bin/pip install playwright && .venv/bin/playwright install chromium`, `scripts/README.md` §설치). Figma MCP 인증(`/mcp`)은 Figma 생성을 지시할 때만 필요하다.
2. PRD 파일을 두고 이렇게 말한다: `docs/example-prd.md 이 PRD로 디자인 인터뷰 해줘`.
3. 스킬이 링크 하나(허브 Artifact)를 준다. 탭을 순서대로 보며 "추천대로" 또는 "다르게"를 누르고 저장한 뒤 "다 봤어"라고 말한다. 1단계 구조 → 2단계 플로우 → 3단계 레퍼런스·취향 → 4단계 규칙 순서다.
4. 규칙이 확정되면 최종 미리보기 탭에서 모든 화면·상태를 확인하고 "이대로 확정해 주세요"를 누른다. `html_audit.py`와 design-auditor가 검수하고 결함은 HTML에서 자동으로 고친다. 화면별 렌더 스크린샷이 한 장씩 도착한다.
5. 산출물은 프로젝트의 `design/` 폴더에 쌓인다 (git 추적 제외). 허브 링크와 `design/`(design-rules.md·screens.md·probes/·screenshots/html/)을 개발 쪽에 넘기면 끝이다. Figma 파일이 필요하면 "Figma 생성"이라고 말한다.

검증 스크립트는 `scripts/README.md` 참고.

## 라이선스

MIT — [LICENSE](./LICENSE)
