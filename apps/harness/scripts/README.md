# scripts/check_phase.py

`design/` 폴더 산출물(brief.md, decisions.md, design-rules.md, probes/*.html)을 결정론적으로 검사하는 게이트 스크립트. Python 3.11 표준 라이브러리만 사용.

사용법:
```
python3 scripts/check_phase.py --phase {structure|flow|taste|rules|probes|all} [--design-dir design] [--json]
```

종료 코드: `0` 통과 · `1` 실패 · `2` 필요한 파일 없음/파싱 불가.

출력: 텍스트 모드는 `[OK] <검사명>` / `[FAIL] <파일> <검사명> <이유>` / `[SKIP] <단계> — 파일 없음`. `--json`은 `{"phase","passed","results":[{"name","ok","file","detail"}], "skipped"}` 형태.

테스트: `python3 -m unittest discover scripts/tests` (픽스처: `scripts/tests/fixtures/design_ok`, `design_bad`).

전체 테스트: `python3 -m unittest discover scripts/tests` — check_phase·figma_audit·html_audit·figma_parity 125개.
playwright 가 없는 python 에서는 실제 렌더 테스트 2개만 skip 된다 (`.venv/bin/python -m unittest discover scripts/tests` 는 전부 실행).

| 단계 | 기본 검증 도구 | 언제 |
|---|---|---|
| 5~6단계 (최종 산출물 = HTML) | `html_audit.py` (정적, `--render` 로 렌더 수치·스크린샷) | 항상 |
| "Figma 생성" 지시를 받았을 때 | `figma_parity.js` + `figma_parity.py` (이름·개수 일치) | 지시가 있을 때만 |
| Figma 전수 검증이 필요할 때 | `figma_snapshot.js` + `figma_audit.py` | 선택 |

---

## HTML A단계 — `scripts/html_audit.py`

최종 산출물 `design/probes/final-preview.html`(화면)과 `design/probes/rules-preview.html`(토큰·컴포넌트)을
`design/design-rules.md`·`icons.md`·`screens.md` 기준으로 검사한다. 정적 검사는 표준 라이브러리만 쓴다.

```
python3 scripts/html_audit.py --design-dir design [--json] [--fix-list design/html-fix-list.md]
.venv/bin/python scripts/html_audit.py --design-dir design --render \
    [--screenshots design/screenshots/html] [--scale 2] [--viewport page|device]
```

종료 코드: `0` 결함 없음 / `1` 결함 있음 / `2` 실행 오류(design 폴더·design-rules.md·대상 HTML 없음, `--render` 인데 playwright/chromium 없음).

출력 한 줄 형식 (마지막에 요약 줄 `파일 N개 / 화면 섹션 N개 / 상태 프레임 N개 [/ 스크린샷 N장] / 실패 N건`):

```
[FAIL] <파일>/<화면>/<상태> <노드>(<선택자>) <규칙 키>: 현재 → 기대
```

`--json` 은 `{"ok","stats","failureCountByRule","findings":[{rule,file,screen,state,node,selector,actual,expected}],"warnings"}`.
`--fix-list` 는 렌더러 수정 입력용 표(`파일 / 화면/상태 / 노드(선택자) / 규칙 키 / 현재값 → 기대값`)를 쓴다.

**`--render` 는 정적 검사도 스크립트 실행 후의 DOM(`page.content()`)으로 돌린다.** 마크업을 JS 템플릿으로 만드는
페이지는 `--render` 없이 돌리면 소스에 `data-screen` 섹션이 없어 `component.manifest`·`state.frames` 가
"data-screen 섹션 없음"으로만 나온다 (이때 `[WARN]` 으로 알려 준다).

### 마크업 계약 (렌더러가 붙이는 속성 — probe-page.md·final-preview.md 에 같은 이름으로 옮긴다)

| 무엇 | 마크업 | 비고 |
|---|---|---|
| 화면 섹션 | `<section data-screen="<slug>" data-screen-name="<화면명>">` | slug·화면명은 screens.md 표와 같게 |
| 상태 프레임 | `<div class="phone" data-state="<state>" data-width="390\|360\|430">` | state: `default·empty·loading·error·long-title·many-items·text-120·keyboard·guest-name` (+ `many-items-scroll`·`default-scroll`). `data-width` 생략 = 390. **1:1 크기로 배치**(축소 썸네일·transform 금지 — `frame.size` 로 걸린다). 같은 화면·상태·폭 프레임은 1개 |
| 컴포넌트 인스턴스 | `data-component="<screens.md 컴포넌트명>"` | 화면 default 프레임의 **최상위** data-component 집합 = 구성표. 컴포넌트 안의 부품은 중첩 data-component 로 둬도 된다(구성표 대조에서 제외) |
| 탭 가능한 요소 | `data-tap` | 탭바·세그먼트처럼 칸이 붙은 묶음은 부모에 `data-tap-group` (`tap.gap` 면제, `tap.min` 은 그대로) |
| primary 버튼 | `data-primary` | default 프레임에 정확히 1개. design-rules §C `web.primary` 예외 화면은 section(또는 default 프레임)에 `data-primary-exempt` → 0~1개 |
| 고정 바 | `data-fixed="cta\|tabbar"` | 홈 인디케이터 영역은 `data-safe-area` (고정 바 안에 두거나 바로 아래 형제로) |
| 스크롤 본문 | `data-scroll` | 고정 바가 있는 default·many-items(-scroll) 프레임에는 필수 |
| 말줄임 텍스트 | `data-truncate="1\|2\|3"` | 1 = `text-overflow:ellipsis`+`white-space:nowrap`+`overflow:hidden` (또는 line-clamp 1), 2·3 = `-webkit-line-clamp` 같은 값. 말줄임이 걸리는데 속성이 없으면 `text.clip` |
| 아이콘 | `<i data-icon="<lucide 이름>"><svg …stroke="currentColor"></svg></i>` | icons.md 허용 목록만. 프레임 안에서 `data-icon` 래퍼 없는 `<svg>` = 직접 그린 아이콘 |
| 토큰 | `:root` 의 `--color-*`·`--space-*`·`--radius-*`·`--shadow-*`·`--font-*`·`--type-*` | 부모 웹 변형은 `--web-*`. 프레임·컴포넌트 CSS 는 `var()` 로만 참조 |
| 페이지 크롬 | `<style data-chrome>` | 프레임 밖 UI(의견 패널·요약 카드 등) 스타일. `token.bound` 면제. 크롬 CSS 가 `.phone` 크기를 바꾸면 안 된다 |

#### 토큰 이름 (design-rules §A 키 → CSS 변수)

| §A 키 | CSS 변수 | 예 |
|---|---|---|
| `color.<n>` | `--color-<n>` | `--color-bg:#FDFBF7`, `--color-accent-soft:rgba(249,115,22,.10)` |
| `space.scale` | `--space-<값>` (값 이름 — Figma 변수 `space/<값>` 과 같다) | `--space-4:4px … --space-48:48px` |
| `space.<n>` | `--space-<n>` | `--space-screen-padding:16px`, `--space-section:24px` |
| `radius` | `--radius-<이름>` | `--radius-md:8px`, `--radius-full:9999px` |
| `shadow` | `--shadow-<이름>` | `--shadow-sm:0 1px 2px rgba(0,0,0,.06)` |
| `font.family` | `--font-family` | |
| `type.roles` | `--type-<역할>`(크기) · `--type-<역할>-weight` · `--type-line-height` · `--type-line-height-title` | `--type-h1:24px`, `--type-h1-weight:600` |

값 비교는 대소문자·공백·따옴표·소수 표기(`.10` = `0.1`)·3자리 hex 를 정규화한 뒤 한다. 그 밖의 변수(`--z-*`, `--motion`, `--frame-w` …)는 자유.

### 검사 항목

정적 (항상)

| 규칙 키 | 검사 |
|---|---|
| `token.bound` | `<style>`(data-chrome 제외)·프레임/컴포넌트 안 인라인 style·SVG `fill`/`stroke` 에서 `:root` 밖 하드코딩 색(#hex·rgb/rgba·hsl)과 간격 속성(padding·margin·gap·border-radius·font-size·font)의 리터럴 px. 예외: `0`·`1px`, `url(#id)`, `data-state="text-120"` 프레임(선택자) 안 font-size |
| `token.defined` | 참조한 `var(--x)` 가 `:root` 에 정의됨 + §A 대응 변수가 있고 값이 문서와 같음 |
| `icon.allowlist` | `data-icon` 이 icons.md 허용 목록에 있음(제외 목록 이름은 따로 표시) + 프레임 안 래퍼 없는 `<svg>` 0개 |
| `component.manifest` | 화면별 default 프레임 최상위 `data-component` 집합 = screens.md 구성 열(빠짐·초과). 구성 셀은 괄호·따옴표 설명을 지우고 `·`/`+` 로 나눈 조각의 첫 PascalCase 토큰만 읽는다("(없음)"·"소제목 web-h2" 무시). 섹션 없음·screens.md 에 없는 화면·컴포넌트 목록 밖 이름도 보고 |
| `state.frames` | 화면마다 7종(default·empty·loading·error·long-title·many-items·text-120) + FormField 화면은 `keyboard` + screens.md 상태 열의 추가 상태(guest-name 등). `data-width` 390 프레임만 센다 |
| `button.primary-per-screen` | default 프레임 안 `data-primary` 정확히 1개 (`data-primary-exempt` 면 0~1개) |
| `no-lorem` | lorem ipsum 금지 (check_phase probes 와 같은 규칙) |
| `no-external` | 외부 `<script src>`·`<link href>`·`<img src>`·CSS `url()`/`@import` 금지. fonts.googleapis.com·fonts.gstatic.com 만 허용 (check_phase `_is_external` 재사용) |

렌더 (`--render`)

| 규칙 키 | 검사 |
|---|---|
| `frame.size` | `.phone` 의 화면상 크기 = `data-width` × 844 (transform 축소도 여기서 걸린다) |
| `tap.min` | `[data-tap]` boundingClientRect ≥ 44×44 (부모 웹도 44) |
| `tap.gap` | 같은 부모의 `[data-tap]` 끼리 간격 ≥ 8 (`data-tap-group`·tabbar 안은 면제) |
| `space.grid` | `[data-component]` 와 그 안(중첩 컴포넌트 제외) 요소의 computed padding·margin·row/column-gap 이 4 배수 (0 허용, `margin:auto` 가운데 정렬 제외). 같은 요소·같은 값은 파일 전체 1건으로 묶고 "같은 값 N곳" 표시 |
| `fixed.no-clip` | default·many-items·many-items-scroll·default-scroll 에서 `[data-scroll]` 을 끝까지 내렸을 때 마지막 자식 bottom ≤ 가장 위 `[data-fixed]` top. `[data-scroll]` 이 없어도 실패 |
| `text.clip` | `[data-truncate]` 의 line-clamp 가 값과 같음(1은 ellipsis+nowrap 도 허용), 말줄임이 걸리는데 `data-truncate` 없음, 텍스트가 프레임·`overflow:hidden` 조상 오른쪽 밖으로 잘림 |
| `safe-area` | 가장 아래 `[data-fixed]` 의 bottom ≤ 844−34, 또는 그 안에 높이 ≥ 34 인 `[data-safe-area]`(또는 padding-bottom ≥ 34) |

기준값(tap 44/8, device 390×844·검증 폭, safe-area 44/34, space 배수)은 `figma_audit` 의 design-rules 파서를 그대로 쓴다.

렌더 동작: 파일마다 한 번 `file://` 로 열고(외부 요청은 폰트 호스트 말고 전부 차단), `.phone[data-state]` 마다
**요소 스크린샷** `<screenshots>/<slug>-<state>[@<width>].png` 를 찍는다(프레임마다 재로드하지 않음, 기본 2배율).
`--viewport page`(기본)는 1280 폭 페이지에 한 번 배치하고 프레임 폭은 CSS 가 정한다.
`--viewport device` 는 `data-width` 별로 뷰포트를 그 폭으로 바꿔 측정한다 — 기존 probe 페이지의
`@media (max-width:440px){.phone{width:100%}}` 같은 크롬 규칙이 프레임을 줄이면 전 프레임이 `frame.size` 로 실패하므로,
프레임 안 반응형은 미디어쿼리 대신 `[data-width="360"]` 선택자로 쓰는 것을 권장한다.

### 설치 (렌더 검사만 필요)

```
python3 -m venv .venv && .venv/bin/pip install playwright && .venv/bin/playwright install chromium
```

`.venv/` 는 .gitignore 에 있다. 브라우저는 `~/Library/Caches/ms-playwright` 에 받는다(버전이 맞는
`chromium_headless_shell-<rev>` 가 이미 있으면 다시 받지 않는다). playwright 가 없는 python 으로 `--render` 를 주면
위 안내와 함께 종료 코드 2.

### 테스트

`scripts/tests/test_html_audit.py` — 픽스처 `scripts/tests/fixtures/html_ok/`(정적·렌더 결함 0건, 3화면·23프레임),
`html_bad/`(15개 규칙 전부 1건 이상 실패). 렌더 판정 함수는 합성 측정값으로도 검사한다.

---

## Figma parity — `scripts/figma_parity.js` + `scripts/figma_parity.py` ("Figma 생성" 지시 때만)

Figma 는 사용자가 "Figma 생성"을 명시했을 때만 만든다. 그때 검증은 전수 스냅샷 대신 **이름·개수 일치**만 본다.

1) 수집 — `figma_parity.js` 전체를 `use_figma` 의 `code` 로 넘긴다(읽기 전용, 이름만 → 20KB 이내. 호출 전 figma-use SKILL.md 를 읽는다).
반환 문자열을 `design/figma-parity.json` 에 저장한다. 형식:
`{variables:[{collection,name}], textStyles:[이름], effectStyles:[이름], componentSets:[이름], components:[단독 컴포넌트 이름], screenFrames:[{name,w,h}]}` (03 Screens 최상위만).

2) 대조

```
python3 scripts/figma_parity.py --actual design/figma-parity.json --rules design/design-rules.md \
    --icons design/icons.md --screens design/screens.md [--states default,empty,…] [--json]
```

종료 코드 `0` 일치 / `1` 불일치 / `2` 실행 오류. 한 줄 형식 `[FAIL] <분류>/<이름> <규칙 키>: 현재 → 기대`.

| 규칙 키 | 기대 목록 (빠짐·초과·중복을 실패로) |
|---|---|
| `parity.variables` | §A `color.<n>` → `color/<n>`, `space.scale` → `space/<값>`, `space.<n>` → `space/<n>`, `radius` → `radius/<이름>`. 초과 검사는 color·space·radius 컬렉션만(그 밖 컬렉션은 `[WARN]` 개수만), `web-` 로 시작하는 이름은 허용 |
| `parity.text-styles` | `type.roles` → `Text/<역할>` (`Text/web-*` 초과 허용) |
| `parity.effect-styles` | `shadow` → `Shadow/<이름>` |
| `parity.components` | screens.md 컴포넌트 목록 + icons.md → `Icon/<이름>` + §B 에 값이 있는 `button.*`→Button, `icon-button.*`→IconButton, `thumbnail.*`→Thumbnail. `_`·`.` 로 시작하는 비공개 컴포넌트는 초과에서 제외 |
| `parity.screens` | screens.md 화면명 × `--states`(기본 `default` 만 — 상태 프레임은 기본 생략) → `<화면명>/<state>`. `<화면>/<상태>` 형식이 아닌 노드(라벨·메모)는 무시 |
| `parity.frame-size` | 화면 프레임 390×844 (`@360` 이면 360×844) |

테스트: `scripts/tests/test_figma_parity.py` (픽스처 `parity_ok.json` 0건 · `parity_bad.json` 6개 규칙 12건, 문서는 `html_ok/` 공유).

---

## (선택) Figma 전수 검증 — 스냅샷 + 속성 검사

> **Figma 생성 후 노드 속성까지 전수 검증이 필요할 때만 쓴다.** 기본 경로는 위의 `html_audit.py`(HTML) 와
> `figma_parity.py`(이름·개수)다. 아래 도구와 테스트는 그대로 유지한다.

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
