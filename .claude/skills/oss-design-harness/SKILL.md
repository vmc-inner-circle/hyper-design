---
name: oss-design-harness
description: PRD 하나를 받아 사용자 개입 5회 이하로 웹·모바일 서비스 화면 전체를 HTML로 만드는 디자인 하네스. 레퍼런스를 조사해 화면 구성이 다른 시안 5개를 먼저 고르게 하고, 고른 시안으로 만든 초안 보드(사용 흐름 = 디자이너식 구역 보드와 화면별 정책 / 화면 디자인)에서 의견을 받아 고치고, 최종본은 화면별 독립 HTML 완성본 + 입구(사용 흐름 · 화면 전체). "이 PRD로 디자인해줘", "화면 만들어줘", "디자인 하네스 시작", PRD 마크다운을 붙여넣는 첫 프롬프트에 트리거된다. 기본은 질문 없이 시안 보드를 만들어 브라우저에 띄우고, 이후 사용자가 붙여넣는 선택·의견만 반영한다.
---

# oss-design-harness

비디자이너가 PRD만 주면 **질문 없이 먼저 만들어 보여주고, 바꿀 것만 받아** 끝내는 하네스. 디자이너처럼 레퍼런스를 조사해 시안 5개를 먼저 보여주고, 고른 시안으로 전체 화면을 만든다.

- 계약(무엇을 만드는가): `docs/harness-design.md`
- **데이터 형식 · 칸 · 생성 단계: `packages/core/schema/README.md`**, 품질 규칙: `packages/core/schema/rules.json`(KRDS 필수 · 권장 / 우리 / 사례)
- 사용자에게 보이는 말: `references/ux-writing.md` — **데이터를 쓰기 전에 반드시 읽는다**
- PRD → 데이터 규칙: `references/prd-to-screens.md`
- 의견 해석: `references/answer-parsing.md`
- 레퍼런스 조사 · 초안 전 질문: `references/research-and-ask.md`
- 화면 조립(모델 배분 · 작업 묶음 · 조립 일꾼 부르기): `references/assembly.md`
- 검수 · 사용자에게 보내는 말: `references/review-and-messages.md`
- 이 문서: 실행 절차

## 읽기 순서 — 단계에 필요한 것만, 한 번씩

1턴이 늦어지는 가장 큰 이유는 문서를 한꺼번에 다 읽는 것이다(전부 1,700줄 넘음). **형식은 시작 때 한 번, 규칙 문장은 검사가 알려 줄 때만** 읽는다. 같은 문서를 다시 열지 않는다.

| 언제 | 읽는 것 | 이때 읽지 않는 것 |
|---|---|---|
| 1턴 시작(S1 · S2) | 이 문서의 '1턴' 절 · research-and-ask · 스키마 README §2(단계별 칸 지도) · §7(예시) · prd-to-screens §1~§3 · §4(첫 단락) · §5~§5-2 · §8 · §9 · ux-writing §1~§3 · §8 | `docs/harness-design.md`(하네스를 고칠 때만) · 칸 사전 `docs/fields.md` · 관계 · 규칙 사전 · `rules.json` 전체 · answer-parsing |
| S3 화면 하나씩 | prd-to-screens §3-1 · §4 · §5-3 · §5-4 · ux-writing §9 | 위와 같음 |
| S5 시안(레퍼런스가 모인 뒤) | prd-to-screens §6 · §6-1 · §7 | — |
| 조각을 맡길 때(1.3 · 2턴 5) | assembly | — |
| 보드를 띄우기 전 · 사용자에게 말할 때 | review-and-messages | — |
| 검사(schema · lint)가 실패를 알릴 때 | 알림의 규칙 id 한 줄(`rules.json`에서 id로) · 칸 사전의 그 칸만 | 사전 전체 |
| 2턴 | 이 문서 '2턴' 절 · answer-parsing §0 · §1 | 1턴에 읽은 것 다시 |
| 3턴 · 4턴 | 이 문서 '3턴' 절 · answer-parsing | — |

## 단계 지도 — 0 · B · A · C와 턴

판단은 0 · B · A · C 네 단계로 나뉘고(배경 `docs/concept.md`), 턴은 그 단계를 사용자와 주고받는 순서다.

| 단계 | 하는 일 | 어느 턴 · 절 | 끝났다는 판정 |
|---|---|---|---|
| **0 요구 정렬** | PRD → 의도(S1) → 여정 · 화면 목록(S2) → 화면별 내용(S3) → 성격(S4). 정하지 못한 것은 가정 로그 | 1턴 1.1 | `node scripts/schema.js runs/<p>` 오류 0(닫기 검사) |
| **B 발산 · 수렴** | 레퍼런스 → 시안 5개(S5) → 고르기 → 초안 | 1턴 1.0-1 · 1.2 · 1.3, 2턴 | 사용자가 시안 하나를 고름 |
| **A 구조 검증** | 데이터 형식 · 관계, 품질 규칙, 조각 HTML | 1.3 · 1.4 · 2턴 6 · 3턴 5 | `schema.js` · `lint.js` exit 0 |
| **C 미적 판단** | 화면을 보고 남긴 의견 → 값만 / B로 / 0으로 | 3턴 · 4턴 | 답변 로그에 원문 · 해석 · 갈래(answer-parsing §0) |

## 절대 규칙

1. **사용자 개입은 PRD 포함 5회 이하.** 필수는 PRD → 시안 고르기 → 초안에 의견(3회). 최종본을 만들면 **묻지 않고 바로 제출**하고, 사용자가 더 고칠 의견을 붙여넣을 때만 4회째(고치기)가 생긴다. 5회째는 여유(사용자 결정 2026-10-07: 제출 확인 질문 없앰).
2. **기본은 질문 없이 바로 초안.** PRD에 없는 것은 추천값으로 정하고 `brief.md` 가정 로그에 남긴다. 질문은 보드 안(`board.ask`, 최대 3개)에서 한다. **예외는 하나** — 잘못 짐작하면 화면 대부분을 다시 그려야 하는 모호함이 PRD에 있을 때만 초안 전에 한 번 묻는다(1.1-0).
3. **취향을 말로 묻지 않는다.** 분위기·글자 크기·버튼 색은 보드 상단에서 눌러 보고 고르게 한다.
4. **확정된 것은 다시 묻지 않는다.** 2라운드부터 `board.locked`.
5. **"끝났다"는 스크립트가 판정한다.** `schema.js` · `lint.js` exit 0 + `build.js` 성공 + 메인의 브라우저 검수 전에는 사용자에게 보여주지 않는다.
6. **결과는 사용자 브라우저에 자동으로 띄운다.** 마지막 빌드는 항상 `--open`. 띄우기 전에 검수용 헤드리스 Chrome을 종료한다.
7. **번호가 나온 화면만 다시 쓴다.**
8. **사용자에게 보이는 말은 ux-writing 규칙대로.** 컴포넌트·디자인 용어 금지, 흐름 제목은 '~하기'.
9. 채팅 메시지는 짧게: 무엇을 띄웠는지 + 할 일 한 줄.
10. **사용자에게 묻는 것은 전부 객관식이다.** 초안 전 확인과 보드의 질문까지 모두 `AskUserQuestion`(또는 보드의 라디오)으로 선택지를 주고, 첫 번째가 추천이며 "(추천)"을 붙인다. "어떻게 할까요?" 같은 열린 질문을 채팅으로 던지지 않는다. 자유 입력은 선택지에 없는 답을 위한 "기타"로만 둔다.
11. **예전 실행물을 보지 않는다.** 실행 중에는 다른 `runs/*` 폴더와 `submissions/`를 읽지 않는다. 형식은 `packages/core/schema/README.md`로 충분하다. 다른 PRD의 화면·문구·구조를 가져오면 "PRD만으로 시작"이라는 조건이 깨진다.

## 모델 · 조립

판단(PRD 분석 · 데이터 · 시안 · 의견 해석 · 게이트 · 검수)은 메인이 하고, 레퍼런스 조사는 ref-scout(sonnet), 화면 조각은 screen-writer(sonnet · 국소 수정은 haiku)가 조립만 한다 — 호출 틀은 `references/assembly.md`. 사용자가 보게 되는 화면(검수 기준)은 `references/review-and-messages.md` §1.

## 시간표 (elapsed.txt)

| 구간 | 목표 |
|---|---|
| 1턴: PRD → 시안 보드 | ≤ 8분 (초안 전 확인을 했으면 답을 받은 뒤부터) |
| 2턴: 시안 고르기 → 초안(전체 화면·흐름) | ≤ 15분 |
| 3턴: 의견 → 최종 | ≤ 10분 |
| 4턴(선택): 더 고칠 의견이 오면 반영 | ≤ 8분 |

턴 계획: **PRD(1) → 시안 고르기(2) → 초안에 의견(3) → 최종본·바로 제출** → (더 고칠 때만) 고치기(4) → 여유(5). 사용자 결정(2026-10-07): "4턴이 필요한가?" → 제출 확인을 묻지 않고 바로 제출. 사용자 요청(리허설 2): "맨 처음에 시안을 선택하고 그 이후에 사용 흐름과 화면 디자인을 주는 게 맞다", "시안은 5개로".

## 1턴 — PRD → 시안 보드 (`stage: "concept"`)

디자이너처럼: 레퍼런스 조사 → 화면 구성이 다른 시안 5개 → 고객이 하나 고른다. **전체 화면은 아직 만들지 않는다**(고른 뒤 2턴에).

### 1.0 기록 시작
- `runs/<project>/` 생성(영문 케밥케이스). `templates/prompt-log.md`·`templates/brief.md` 복사. `harness-notes.md` 빈 파일.
- `elapsed.txt`에 `시작: YYYY-MM-DD HH:MM`(`date`로 확인). `prompt-log.md` 1회에 PRD 원문.

### 1.0-1 레퍼런스 조사 시작 (ref-scout 5개, 백그라운드)
PRD를 읽자마자 ref-scout 5개를 **백그라운드로 동시에** 띄우고 기다리지 않고 1.1로 간다. 관점 · 프롬프트 틀 · 겹침 처리 · 결과 넣는 법은 `references/research-and-ask.md` §1. 시안(`concepts`)만 결과를 본 뒤 정한다.

### 1.1-0 초안 전에 물을지 판단 (메인, 1분)
**대부분의 PRD는 묻지 않는다.** "반대로 짐작했을 때 화면의 절반 이상을 다시 만들어야 하는가?"가 기준 — 표 · 묻는 법은 `references/research-and-ask.md` §2. 묻지 않으면 그 판단을 `brief.md` 가정 로그 첫 줄에 남긴다.

### 1.1 0단계 — PRD → 데이터 (메인, 5분 — 레퍼런스 조사와 동시에)

`references/prd-to-screens.md`대로, **생성 단계 순서로 한 번에 한 단계씩** 쓴다(칸은 앞 단계 칸만 가리킨다 — 스키마 README §2).

- **S1 의도**: 플랫폼(`web` 1280×800 / `mobile` 390×844 — prd-to-screens §1) · 역할 2~3개(`goal` 이루려는 것 · `inclusion` 나이 · 기기 · 읽는 상황 · `nav` · `user`) · 공통 사실 `facts`(이름표 → 사실 한 줄). 역할의 포함 조건에서 글자 크기 추천(`board.recommend.type` · `typeWhy`).
- **S2 여정 · 화면 목록**:
  - 화면 목록(`slug` · `name` · `role` · `file` = `screens/<slug>.html` — lint가 모든 화면에 요구): **핵심 8~14개 + 처음 시작용 3~5개**(빈 홈·등록·빈 목록·초대 받았을 때, `state` · `variantOf`) + **오류 · 완료 상태** 2~4개(입력 화면 중 틀리기 쉬운 곳 `error`, 핵심 작업 끝 `success`). 순서 = 사용자가 만나는 순서. 누르는 버튼이 든 **영역 key**도 이때 계획한다.
  - 구역 `sections` 2~6개 · 흐름(처음 시작 흐름을 역할마다 맨 앞 + 핵심 흐름, 전부 끊김 없는 한 줄, 6~9개) · **갈래** `branches`(흐름 밖 버튼 — 새 입력·선택 UI는 **뜨는 창 화면** `overlayOf` 3~6개) · 갈리는 곳의 조건 이름표 `when`(prd-to-screens §5 · §5-1 · §5-2).
- **S3 화면 하나씩**(prd-to-screens §3-1 · §4 · §5-2~§5-4): `goal` → `problem` → `data`(facts 이름표) → `emphasize`(problem에 답하는 1순위 사실) → `focus` → `defer`, `pattern`(KRDS 이름) · `section` · `step`, 영역 3~6개(`level` 1순위 하나 · `form` · `content` · `label` · `why` — ux-writing §2), 상태 변형을 뺀 모든 화면에 `policy`, 오류 · 안내 문구 `cases`, 화면 그림으로 안 보이는 동작은 `motion`.
- **S4 성격**: 기준어 3개와 무드보드(`mood`).
- 가정 로그: PRD에 없어서 정한 것 전부.
- **닫기 검사**: `node scripts/ids.js runs/<project>` → `node scripts/schema.js runs/<project>` 오류 0(형식 · 관계 · 하나뿐). 경고는 읽고 가정 로그에 이유를 남긴다.

### 1.2 시안 5개 (레퍼런스가 모인 뒤, prd-to-screens §6-1)
- `references`: 조사 결과(겹치면 하나로). `runs/<p>/references.md`에도 표로.
- `looks` 5개(분위기, 시안마다 하나) — KRDS 역할 색 `palette`(brand · support · accent) · 대안 버튼 색 `swatches` ≤4 · 글꼴 세트 `font`(prd-to-screens §6).
- `concepts` 5개: 메뉴 구조(`shell` — web sidebar·top·rail / mobile tabbar·top·none을 모두 쓴다) · 첫 화면 구성(`home`) · 밀도(`density` airy · normal · compact) · 분위기(`look`)가 **서로 다른** 안. 첫 번째가 추천. 안마다 참고한 곳(`refs` — references의 이름으로)과 비교할 **메인 화면 3~6장**(`screens`, 모든 안이 같은 slug — 역할별 메뉴 화면 먼저, 남는 칸에 핵심 작업 화면. PRD를 보고 정한다).
- `"stage": "concept"`, `"concept": "<추천 id>"`.

### 1.3 데이터 파일 → 시안 화면 — screen-writer 병렬 (시안마다 3장씩 1개, 최대 10개 동시, sonnet)
- `screens.json` · `flow.json`(모든 step에 `trigger`, 제목 '~하기', `branches`) · `icons.json` — 형식은 스키마 README. 달력이 있으면 `node scripts/calendar.js …`로 격자를 미리. `node scripts/ids.js runs/<project>` → `node scripts/schema.js runs/<project>` → `node scripts/lint.js runs/<project>` — 이때 FAIL은 "시안 조각 없음"만.

- 시안마다 3장씩 작업 묶음(`node scripts/pack.js runs/<project> --screens <3장> --concept <id> --name <이름>`)을 만들고 screen-writer를 병렬로(최대 10개) — 프롬프트 틀은 `references/assembly.md` §2 · §3. 끝나면 `node scripts/expand.js runs/<project>` → `lint.js`, FAIL 시안만 재호출(최대 2회).

### 1.4 검수 → 띄우기
1. `node scripts/build.js runs/<project> --mode board` (시안 단계면 시안 고르기 화면만 만든다)
2. 헤드리스 Chrome으로 검수 — 항목은 `references/review-and-messages.md` §2.
3. **헤드리스 Chrome 종료** → `node scripts/build.js runs/<project> --mode board --open`
4. `elapsed.txt`에 `시안: HH:MM`. 사용자에게 `references/review-and-messages.md` §3의 1턴 말 그대로.

## 2턴 — 시안 고르기 → 초안 (`stage` 없음 = draft)

1. `prompt-log.md` 2회에 (AI 질문 요약 = "시안 보드") + 붙여넣은 원문. `brief.md` 답변 로그에 **원문 | 해석 | 반영**.
2. `시안 <id>(이름)` → `screens.json`: `concept = <id>`, `stage` 삭제, `theme = 그 시안의 look`, `board.recommend.theme`도 같게, `board.locked = ["concept"]`, `round: 1`(초안 1).
3. `시안 <id> 메모: …` → 고른 시안의 메모면 그 시안을 고칠 점, 다른 시안의 메모면 **그 안에서 가져올 요소**(예: "B의 달력") — 모두 이번 초안의 전역 힌트로(answer-parsing §1).
4. 고른 시안의 메인 화면 `concepts/<id>/<slug>.html`을 `screens/<slug>.html`로 복사(메모가 그 화면을 건드리면 복사 뒤 revise). 셸은 expand.js가 붙였으므로 그대로 맞다(시안을 바꿔 셸만 바꿀 때는 `expand.js --reshell`).
5. 나머지 화면: 3장씩 `pack.js --concept <고른 id>`로 작업 묶음을 만들고 screen-writer를 병렬로(sonnet) — 프롬프트 틀은 `references/assembly.md` §4.

6. `node scripts/expand.js runs/<project>` → `lint.js`(FAIL 화면만 재호출 최대 2회) → `build.js --mode board` → 헤드리스 검수(`references/review-and-messages.md` §2) → **헤드리스 종료** → `--open`.
7. `elapsed.txt`에 `초안: HH:MM`. 사용자에게 `references/review-and-messages.md` §3의 2턴 말 그대로.

## 3턴 — 의견 → 최종

C단계 — `references/answer-parsing.md`대로. 의견마다 먼저 갈래(값만 / B로 / 0으로, answer-parsing §0)를 정하고, **칸을 먼저 고친 뒤** 그 화면을 다시 조립한다.
1. `prompt-log.md` 3회 + 답변 로그(원문 · 해석 · 갈래).
2. 반영: `화면 S 메모: …`가 규칙(정책)에 대한 말이면 그 화면의 `policy`를 고친다(화면 조각은 그대로). `화면 S · … [경로]` 줄은 그 화면의 경로 요소를 고칠 대상으로(answer-parsing §1-1) / 첫 줄의 분위기·글자 크기·버튼 색 확정(`theme`, `toggles.type`, `toggles.swatch`) / `확인:` → 구조 반영 / `화면 S … 빼기` → 요소·조각 블록 제거 / `화면 N 빼기` → 화면 제거 + 흐름을 **끊김 없게** 다시 잇기(끊기면 흐름을 쪼갬) / `추가:` → 새 화면(+ 필요하면 새 흐름·갈래) / `메모:` → 전역 힌트.
2-1. 반영한 화면마다 `board.focus`에 slug, `board.changes`에 `{ slug, said: "남긴 의견 한 줄", did: "바뀐 점 한 줄" }`(규칙만 바꿨으면 "규칙: …"). 다음 보드에서 "의견 반영" 이름표와 ⓘ 카드로 보인다.
3. 의견 때문에 화면에 **새 묶음이 생기거나 버튼이 다른 묶음으로 옮겨지면** screens.json에 항목을 추가하고, 그 버튼을 쓰는 흐름 step·갈래의 `region`도 옮긴다. `ids.js`.
4. 재작성: 문구·아이콘·요소 교체처럼 단순한 수정은 haiku, 배치를 다시 짜는 수정은 sonnet(`MODE=revise`, 1~2개씩 병렬), 새 화면도 sonnet.
5. `schema.js && lint.js && build.js --mode final` → `out/index.html`과 `out/screens/NN-slug.html`(화면마다 하나).
6. 검수는 **실제 클릭**으로(`references/review-and-messages.md` §2) → 헤드리스 종료 → `build.js --mode final --open`.
7. 제출: `out/` 전체(`index.html` + `screens/`)를 `submissions/<github_id>/`로 복사, `prompt-log.md`(총 개입 횟수), `elapsed.txt`(종료·소요).
8. 사용자에게 `references/review-and-messages.md` §3의 3턴 말 그대로(묻지 않는다 — 제출 확인 질문 없음). `prompt-log.md`에 총 개입 3회(초안 전 확인을 했으면 4회).

## 4턴(선택) — 더 고칠 의견이 왔을 때
- 사용자가 의견을 붙여넣을 때만 생긴다. 3턴 2~7과 같은 방식으로 반영해 최종본을 다시 만들고 제출 폴더를 갱신한다.
- 이번에도 **묻지 않고** "반영해서 다시 제출했어요 + 경로"로 끝낸다(5턴은 사고 났을 때만). `prompt-log.md` 총 개입 +1.

## 실행 중에 사용자가 하네스 자체를 지적하면

리허설처럼 사용자가 보드의 구조·말·레이아웃을 지적하면(개입 횟수와 별개로 하네스 개선 대화일 때):
1. 이번 실행물만 고치지 말고 **원인이 있는 층을 고친다**: 말 → `ux-writing.md`·lint / 구조·레이아웃 → `packages/core/canvas` / 데이터 칸 · 품질 규칙 → 스키마 · `rules.json`(README §6 순서) · `prd-to-screens.md` / 조립 → `snippets/00-rules.md`·screen-writer.
2. `runs/<project>/harness-notes.md`에 한 줄: 무엇을 왜 바꿨는지 + 사용자 원문.
3. 반복될 결정이면 계약 §13 표에 옮긴다. 이전 결정을 되돌리는 지적이면 표의 그 줄을 고친다.
4. 도메인 값은 하네스에 넣지 않는다.

## 하지 않는 것

- 1.1-0 기준에 맞지 않는 질문을 초안 전에 하기. 취향 라벨 질문. 확정된 것 재질문.
- screens.json에 없는 화면 만들기(처음 시작 흐름의 빈 상태 화면은 필수).
- 번호가 나온 화면 외의 조각 수정. 조각 전체 재생성.
- `packages/`·`scripts/`에 도메인 값.
- 사용자에게 파일을 찾아 열게 하기. 스크린샷·중간 파일 여러 개 보내기.
