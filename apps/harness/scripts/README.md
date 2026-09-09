# scripts/check_phase.py

`design/` 폴더 산출물(brief.md, decisions.md, design-rules.md, probes/*.html)을 결정론적으로 검사하는 게이트 스크립트. Python 3.11 표준 라이브러리만 사용.

사용법:
```
python3 scripts/check_phase.py --phase {structure|flow|taste|rules|probes|all} [--design-dir design] [--json]
```

종료 코드: `0` 통과 · `1` 실패 · `2` 필요한 파일 없음/파싱 불가.

출력: 텍스트 모드는 `[OK] <검사명>` / `[FAIL] <파일> <검사명> <이유>` / `[SKIP] <단계> — 파일 없음`. `--json`은 `{"phase","passed","results":[{"name","ok","file","detail"}], "skipped"}` 형태.

테스트: `python3 -m unittest discover scripts/tests` (픽스처: `scripts/tests/fixtures/design_ok`, `design_bad`).

---

## Figma A단계 (스냅샷 + 속성 검사)

`design-auditor`의 A단계(노드 속성 수치 검사)를 **결정론적으로** 돌리는 두 도구.
REST API는 쓰지 않는다(토큰 의존 회피). Figma MCP `use_figma` 로 스냅샷을 뜨고, 파이썬으로 검사한다.

| 파일 | 하는 일 |
|---|---|
| `scripts/figma_snapshot.js` | Figma Plugin API 스크립트. `01 Tokens` / `02 Components` / `03 Screens` 를 순회해 검사에 필요한 속성만 JSON으로 반환 |
| `scripts/figma_audit.py` | 그 JSON을 `design/design-rules.md` 기준으로 검사하고 결함 목록을 출력 |

### 1) 스냅샷 뜨기

`figma_snapshot.js` 전체를 `use_figma` 의 `code` 인자로 넘긴다. **호출 전에 반드시**
`ReadMcpResourceTool(server="figma-remote-mcp", uri="skill://figma/figma-use/SKILL.md")` 를 읽는다.

```
mcp__figma-remote-mcp__use_figma({
  fileKey: "<build-log.md 의 figma_file>",
  description: "A단계 스냅샷 수집 (읽기 전용)",
  skillNames: "figma-use",
  code: "<scripts/figma_snapshot.js 내용>"
})
```

반환값(JSON 문자열)을 그대로 `design/figma-snapshot.json` 에 저장한다.
`use_figma` 반환 규약(figma-use SKILL.md §1·§3): 데이터는 `return` 으로만 나가고 자동 JSON 직렬화된다.
`console.log()` 는 절대 반환되지 않고, `figma.closePlugin()` 이나 async IIFE 로 감싸면 안 된다.
이 스크립트는 읽기 전용이라 생성/변경 노드 ID가 없다.

노드가 많으면 파일 상단 상수를 조정한다.

- `PAGES` — 순회할 페이지 이름 배열 (`[]` 면 전체)
- `MAX_DEPTH` — 페이지 직속 자식이 depth 0. 기본 8
- `MAX_NODES_PER_PAGE` — 안전 상한. 넘으면 `truncated: true`

### 2) 검사

```
python3 scripts/figma_audit.py \
  --snapshot design/figma-snapshot.json \
  --rules    design/design-rules.md \
  [--brief   design/brief.md] \
  [--icons   design/icons.md] \
  [--json] [--fix-list design/fix-list.md]
```

종료 코드: `0` 결함 없음 / `1` 결함 있음 / `2` 실행 오류(파일 없음·JSON 파싱 실패·형식 불일치).

출력 한 줄 형식:

```
[FAIL] <페이지>/<프레임> <노드명>(<id>) <규칙 키>: 현재 → 기대
```

`--fix-list` 는 `figma-builder` 의 `STAGE=fix` 에 그대로 넘길 마크다운 표
(`화면 / 노드 ID / 규칙 키 / 현재값 → 기대값`)를 쓴다. **목록에 없는 것은 건드리지 않는다.**

### 검사 항목

| 규칙 키 | 검사 |
|---|---|
| `palette.bound` | 03 Screens 의 모든 SOLID fill/stroke 가 색 변수에 바인딩 |
| `typo.style` | 모든 TEXT 에 `Text/*` 스타일 적용 |
| `space.grid` | padding·itemSpacing·(오토레이아웃 밖 자식의) x·y 가 `space.scale` 배수 |
| `component.reuse` | 인스턴스 / (인스턴스 + 로컬 FRAME) ≥ 90% |
| `naming.default` | `Frame 12`·`Rectangle 3`·`Text` 같은 기본 레이어명 0개 |
| `variant.coverage` | Button·IconButton 은 `default/pressed/selected/disabled/loading`, Thumbnail 은 `default/pressed/selected` |
| `state.frames` | 화면마다 `default/empty/loading/error/long-title/many-items/text-120` 7개 |
| `button.primary-per-screen` | `<화면>/default` 안에 variant=primary Button 인스턴스 정확히 1개 |
| `tap.min` | 탭 가능한 인스턴스 44×44 이상 |
| `tap.gap` | 형제 탭 영역 간격 8 이상 |
| `safe-area` | 화면 프레임 직속 자식이 상단 44 / 하단 34 안쪽 |
| `device.frame` | 화면 프레임 390×844 (`@360`·`@430` 검증 프레임만 예외) |
| `icon.sizes` | `Icon/` 인스턴스 크기 16/20/24 |
| `icon.allowlist` | `Icon/<name>` 의 `<name>` 이 `--icons` 표의 "lucide 이름" 열에 있음 |
| `icon.set` | `Icon/` 컴포넌트 밖의 VECTOR/BOOLEAN_OPERATION/STAR/POLYGON 0개 (AI가 직접 그린 아이콘 탐지) |
| `icon.size-by-text` | 오토레이아웃 안 TEXT 형제 기준 — 글자 12~13 → 아이콘 16, 14~15 → 20, 17 이상 → 24 |
| `button.row-rule` | 같은 오토레이아웃 부모의 Button 인스턴스 height·cornerRadius 동일 |
| `layer.order` | Snackbar > Dialog > BottomSheet > TabBar/AppBar 순으로 자식 인덱스가 뒤(위) |

기준값은 `design/design-rules.md` 표에서 파싱한다
(`space.scale`, `icon.sizes`, `tap.min`, `device.frame`, `safe-area`, `z.scale`,
`button.sizes`, `button.states`, `color.*` …).
파싱에 실패한 키는 `.claude/skills/oss-design-harness/references/design-rules.md` 의 기본값으로
대체하고 `[WARN]` 을 출력한다.

화면 목록은 `--brief` 의 §1 화면 목록 표 첫 열에서 읽고, 없으면 03 Screens 의
`<화면>/default` 패턴으로 추론한다.

### 스냅샷 JSON 형식

스키마는 `scripts/figma_snapshot.js` 상단 주석에 적혀 있다. **같은 형식이면 나중에 REST API로
만든 JSON도 그대로 통과한다** — `figma_audit.py` 는 `--snapshot` 경로만 받고 Figma에 접속하지 않는다.

핵심 노드 필드: `id · name · type · parentId · pageName · depth · childIndex · x · y · width ·
height · visible · layoutMode · padding* · itemSpacing · fills · strokes · cornerRadius ·
textStyleId · fontSize · characters · boundVariables · isInstance · mainComponentName ·
componentPropertyValues · hasLabel · insideIconComponent`

### 테스트

```
python3 -m unittest scripts/tests/test_figma_audit.py
```

픽스처: `scripts/tests/fixtures/snapshot_ok.json`(결함 0건), `snapshot_bad.json`(서로 다른 규칙 18개 실패),
`design-rules.md`, `brief.md`, `icons.md`.

### 화면 구성표 검사 (`--screens design/screens.md`)

`design/screens.md`의 구성 열(위→아래 컴포넌트 목록)과 `<화면>/default` 프레임의 최상위 인스턴스를 대조한다. 빠진 컴포넌트, 구성표 밖 컴포넌트, 구성표에 없는 화면을 `component.manifest`로 보고한다. 파일이 없으면 검사를 건너뛴다. 형식은 `references/final-preview.md` 하단 표 참고.
