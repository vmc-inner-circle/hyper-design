# hyper-design

VIBE MAFIA CLUB 이너서클이 함께 만드는 오픈소스 디자인 하네스 실험 레포입니다.

## 지금 이 레포의 상태

하네스톤 개인전(2026-09-30)은 9/5 하네스톤 2회차 참가자가 받은 빈 템플릿([`b946678`](https://github.com/vmc-inner-circle/hyper-design/tree/b946678))에서 출발했습니다. 그 템플릿의 0 · B · A · C 구조를 채운 하네스가 아래 **oss-design-harness**입니다.

- 규칙·제출 방법: [HARNESSTON.md](./HARNESSTON.md)
- 공통 PRD: [prd/family-trip.md](./prd/family-trip.md)(결과물용) · [prd/wedding-meetup.md](./prd/wedding-meetup.md)(연습용)
- 제출 위치: [submissions/](./submissions/)

## 이전 하네스(v1) 아카이브

harnessthon-2-team-3 판본을 이식해 다듬던 기존 하네스(`apps/harness`)는 아래에 보존되어 있습니다.

- 브랜치: [`archive/v1-team3`](https://github.com/vmc-inner-circle/hyper-design/tree/archive/v1-team3)
- 태그: [`v1-team3-final`](https://github.com/vmc-inner-circle/hyper-design/tree/v1-team3-final)
- v1 기준으로 열려 있던 PR(#6·#7·#8)은 base를 `archive/v1-team3`로 옮겨 보존했습니다.

## 기여 규칙

- `main`에 직접 push하지 않습니다. 브랜치를 만들고 GitHub PR로 병합합니다.

---

## oss-design-harness — PRD를 넣으면 화면 전체를 HTML로

**현업 디자이너의 판단 기준을 에이전트가 쓰는 형태로 옮긴 디자인 하네스.** PRD 하나를 받아, 사용자 개입 5회 이하로 웹 · 모바일 서비스 화면 전체를 HTML로 만듭니다. 판단 기준의 바탕은 [KRDS(대한민국 정부 디자인 시스템)](https://www.krds.go.kr/)입니다 — 원칙 · 패턴 이름 · 색 역할 · 글자 · 대비를 스키마와 검사 규칙으로 옮겼습니다.

### 쓰는 법

1. 이 레포를 프로젝트 루트로 Claude Code를 실행합니다.
2. PRD만 넣습니다: `/oss-design-harness prd/family-trip.md` (또는 PRD 내용을 그대로 붙여넣기).
3. 브라우저에 뜨는 보드에서 고르고 의견을 남긴 뒤, 보드가 만들어 준 글을 붙여넣습니다. 흐름 전체: [docs/harness-flow.md](./docs/harness-flow.md)

결과물은 `runs/<project>/out/`(입구 `index.html` · 화면별 완성본)에 생깁니다.

### 4단계 판단 구조와 이 하네스

본판 템플릿의 0 · B · A · C 구조(배경: [docs/concept.md](./docs/concept.md))를 그대로 따릅니다.

| 단계 | 이 하네스에서 |
|---|---|
| **0. 요구사항 정렬** | PRD → 의도(역할 · 공통 사실) → 여정(구역 · 흐름) → 화면 목록 → 화면별 내용(목적 · 겪는 문제 · 1순위) → 닫기 검사. 정하지 못한 것은 `brief.md` 가정 로그에 남깁니다 |
| **B. 발산 · 수렴** | 레퍼런스를 근거로 메뉴 틀 · 첫 화면 · 밀도 · 분위기가 다른 시안 5개 → 보드에서 하나 고르기 → 초안 |
| **A. 구조적 사실 검증** | `scripts/schema.js`(데이터 형식 · 관계) · `scripts/lint.js`(품질 규칙 · 조각 HTML) — 스크립트가 판정합니다 |
| **C. 미적 판단** | 보드의 화면에 남긴 의견을 원인별로 — 값만 고치기 / B로(다른 시안) / 0으로(요구 다시 정렬) |

### 구조

```
.claude/skills/oss-design-harness/   SKILL.md(실행 절차) · references/(PRD → 데이터 · 사용자에게 보이는 말 · 의견 해석 · 레퍼런스 조사와 초안 전 질문 · 화면 조립 · 검수와 사용자에게 보내는 말) · templates/
.claude/agents/                      ref-scout(레퍼런스 조사) · screen-writer(화면 조각 조립)
packages/core/schema/                데이터 정본 — screens · flow 스키마, rules.json(규칙의 유일한 자리), README(기준 문서)
packages/core/                       tokens(기본 값) · canvas(보드) · icons · motion
packages/web/ · packages/mobile/     부품 CSS · 조각 규칙(snippets) · 모양 조합 예시(patterns)
scripts/                             pack · expand · build · lint · looks · schema · test
docs/                                harness-design(설계 계약) · harness-flow(사용 흐름) · concept(4단계 배경)
```

데이터 형식과 칸의 뜻은 [packages/core/schema/README.md](./packages/core/schema/README.md) 한 곳에 있습니다.

### 검사

```bash
node scripts/test.js                 # 저장소 시험 — 처음부터 끝까지 · 회귀 · 스키마 · 부품 CSS · 안내문 · 내부 기록
node scripts/schema.js runs/<p>      # 실행물 데이터 형식 · 관계
node scripts/lint.js runs/<p>        # 품질 규칙 · 조각 HTML
```

의존성은 없습니다(Node 내장 모듈만).

### 라이선스

MIT — [LICENSE](./LICENSE)
