# 화면 조립 — 모델 배분 · 작업 묶음 · 조립 일꾼 부르기

> 이 문서는 SKILL.md에서 나눈 참고 문서다. SKILL의 '읽기 순서'가 언제 여는지 정한다.

## 1. 모델 배분

| 작업 | 모델 | 호출 |
|---|---|---|
| PRD 분석 · 데이터 · 시안 정하기 · 의견 해석 · 게이트 · 검수 | 메인 | 직접 |
| 레퍼런스 조사 (1턴, 관점 5개 동시) | sonnet | `Agent(subagent_type:"ref-scout", model:"sonnet", run_in_background:true)` |
| 시안의 메인 화면 (1턴, `CONCEPT=`, 3장씩 최대 10개 동시) · 새 화면 조립 (2턴, 추가 화면) | sonnet | `Agent(subagent_type:"screen-writer", model:"sonnet")` |
| 고른 시안으로 전체 화면 맞추기 (2턴, `MODE=restyle`) | sonnet | 3개씩 병렬 |
| 국소 수정 (`MODE=revise`) | haiku | `Agent(subagent_type:"screen-writer", model:"haiku")` |
| lint FAIL 재시도 | sonnet | |

haiku에 넘기는 `CHANGES`의 "할 것"은 명령형으로 완결한다(어떤 항목의 어떤 조각을 무엇으로).

## 2. 작업 묶음(PACK)

**화면을 빨리 쓰는 방법(라이브러리·모듈)**: 에이전트마다 먼저 작업 묶음을 만든다 — `node scripts/pack.js runs/<project> --screens <3장> [--concept <id>] --name <이름>` → `runs/<project>/packs/<이름>.md`. 에이전트는 **그 파일 하나만 읽고 화면마다 한 번씩 쓴 뒤 끝낸다**(셸 없이 `<main>`만, 짧은 부품 태그). 셀프 테스트 측정: 3장에 4~8분 · 도구 호출 15~38회 → **1.8분 · 4회**.

```
Agent(subagent_type: "screen-writer", model: "sonnet", prompt: "
PACK=runs/<project>/packs/<이름>.md
RUN=runs/<project>
CONCEPT=<a|b|c|d|e>
SCREENS=<그 시안의 screens 중 3장 — 4장 이상이면 에이전트를 나눠 같은 CONCEPT로 하나 더>
DOMAIN=<도메인 한 줄 + 고정 더미 데이터: 인물(역할 포함)·장소·날짜 범위·상태 어휘. 모든 시안이 같은 값>
시안 메모: <이름 · 첫 화면에 무엇을 먼저(home) · 밀도 · 참고한 곳에서 가져올 점(borrow)을 화면별로 구체적으로>
각 화면은 screens.json의 항목(goal · problem · emphasize · data · regions의 level · form)과 flow.json의 trigger·branches를 따른다(고르면 그대로 옮겨 쓴다).
이 PACK 파일 하나만 읽고, 화면마다 Write 한 번으로 쓴 뒤 끝낸다(다시 열어 점검하지 않는다).
")
```

## 3. 1턴 — 시안의 메인 화면 (시안마다 3장씩 1개, 최대 10개 동시, sonnet)

```
Agent(subagent_type: "screen-writer", model: "sonnet", prompt: "
PACK=runs/<project>/packs/<이름>.md
RUN=runs/<project>
CONCEPT=<a|b|c|d|e>
SCREENS=<그 시안의 screens 중 3장 — 4장 이상이면 에이전트를 나눠 같은 CONCEPT로 하나 더>
DOMAIN=<도메인 한 줄 + 고정 더미 데이터: 인물(역할 포함)·장소·날짜 범위·상태 어휘. 모든 시안이 같은 값>
시안 메모: <이름 · 첫 화면에 무엇을 먼저(home) · 밀도 · 참고한 곳에서 가져올 점(borrow)을 화면별로 구체적으로>
각 화면은 screens.json의 항목(goal · problem · emphasize · data · regions의 level · form)과 flow.json의 trigger·branches를 따른다(고르면 그대로 옮겨 쓴다).
이 PACK 파일 하나만 읽고, 화면마다 Write 한 번으로 쓴 뒤 끝낸다(다시 열어 점검하지 않는다).
")
```

## 4. 2턴 — 나머지 화면

```
Agent(subagent_type: "screen-writer", model: "sonnet", prompt: "
PACK=runs/<project>/packs/<이름>.md
RUN=runs/<project>
SCREENS=<slug1>,<slug2>,<slug3>
DOMAIN=<도메인 한 줄 + 고정 더미 데이터: 인물(역할 포함)·장소·날짜 범위·금액 단위·상태 어휘. 오늘 날짜>
THEME_HINT=<상태 배지 규칙(예: 확정=badge-success+circle-check, 후보=badge-neutral+circle-dashed)>
화면별 메모:
- <slug>: <이 화면에 무엇이 보여야 하는지, 채울 값, 빈 상태면 .empty로 비워 둘 것, primary 버튼 문구>
트리거: runs/<project>/flow.json에서 from이 이 화면인 step의 trigger를 실제 버튼에 data-trigger로 (00-rules 3-1).
이 PACK 파일 하나만 읽고, 화면마다 Write 한 번으로 쓴 뒤 끝낸다(다시 열어 점검하지 않는다).
")
```

## 5. 조립 뒤

- 끝나면 **`node scripts/expand.js runs/<project>`**(짧은 부품 태그를 펼치고 셸을 붙여 파일에 다시 씀) → `lint.js`. FAIL 시안만 FAIL 원문과 함께 재호출(최대 2회), 그래도 실패면 메인이 고친다.

