# canvas — 구조와 규칙 (유지보수용)

에이전트가 보드를 쓰고 피드백을 읽는 방법은 `../references/canvas.md`. 이 문서는 **캔버스를 고치는 사람**을 위한 것이다.

## 파일

```
canvas/
├── canvas.html        껍데기: CSS, Excalidraw 띄우기, 저장·자동 새로고침, UI 조정
├── lib/
│   ├── ids.js         요소 id 규칙 (make / parse) — 모든 모듈이 이것만 쓴다
│   ├── board.js       불러오기(board·devices·canvas-state) + 링크로 하위 페이지 찾기
│   ├── capture.js     기기 크기 probe iframe: 높이·컴포넌트 측정, 이미지 뜨기, 자동 점검, 좌표→요소
│   ├── layout.js      배치: 화면 × 기기 칸, 컴포넌트 이미지, 인터랙션 표시, 피드백 상자, 관계 화살표
│   └── feedback.js    해석: 요소 → feedback items, canvas-state (순수 함수 — DOM·Excalidraw 없음)
├── canvas-state.schema.json  캔버스 전용 복원 상태 (에이전트는 읽지 않음)
├── tests/             node --test canvas/tests/feedback.test.mjs
└── server.py          표준 라이브러리 서버: 정적 파일, /schema/·/lib/, /api/feedback, /api/version

캔버스 밖 (스킬 폴더):
schema/               공통 약속 — devices.json(기기 규격) · stack.json(외부 자원) · board / feedback 스키마. 캔버스는 이것만 보고 동작
scripts/check.py      생성 직후 정적 점검 (board.json ↔ HTML)
```

## 흐름

```
loadBoard ─→ discover ─→ makeFrames ─→ capture.measureFrame ─→ buildScene ─→ Excalidraw
(board.json    (<a href>를     (화면 × 기기)   (probe로 높이·컴포넌트·     (요소 목록)
 devices.json   따라 하위                       이미지·renderChecks)
 canvas-state)  페이지·links)

사용자 편집 ─→ onChange ─→ changeKey가 바뀌면 700ms 뒤 save
                            └─ interpret(요소, capture.elementAt) ─→ POST /api/feedback
                                                                    ├─ feedback.json     (items · renderChecks · discovered)
                                                                    └─ canvas-state.json (scene · files · moved · components)

에이전트가 board.json·theme.js·screens/ 수정 ─→ /api/version 변화 ─→ 캔버스 새로고침
에이전트가 피드백 반영 ─→ feedback·canvas-state를 -r{n}으로 옮기고 board.json round +1 ─→ 지난 라운드 상태는 복원 안 함, 지난 라운드 페이지의 저장은 서버가 409로 거부
```

## 요소 id (`lib/ids.js`)

| 종류 | id | 그룹 |
|---|---|---|
| 기기 칸 (embeddable) | `screen:{screen}@{device}` | `g:{screen}` |
| 칸 제목 | `title:{screen}@{device}` | `g:{screen}` |
| 컴포넌트 이미지 | `img:{screen}@{device}:{data-id}` (같은 data-id가 또 있으면 `#2`) | `g:{screen}`, 영역·요소 묶음은 `cg:{screen}@{device}:{영역 data-id}` 안에 |
| 피드백 상자 / 제목 (화면 아래) | `panel:{screen}` / `ptitle:{screen}` | `g:{screen}` |
| 관계 화살표 | `rel:{from}>{to}` (customData.rel·goto) | — |
| 인터랙션 표시 (빨간 테두리) | `mark:{screen}@{device}:{data-id}` | `g:{screen}` (잠금) |
| 줄 제목 | `row:{row}` | — |

`canvas-state.components`의 키가 컴포넌트 id라서, **형식을 바꾸면 저장된 상태가 복원되지 않는다.** 바꿀 땐 `ids.js`만 고치고 `tests/`를 돌린다.

## customData (AI가 만든 요소에만)

| 필드 | 붙는 곳 | 뜻 |
|---|---|---|
| `generated: true` | 전부 | 사용자가 그린 것과 구분 — 저장(scene)·피드백 해석에서 제외 |
| `screen`, `device` | 전부 (device는 칸·컴포넌트) | 소속 화면·기기 |
| `embed`, `w`, `h`, `base` | 기기 칸 | 원본 크기(좌표 환산), 배치 기준 위치(화면 이동량 계산) |
| `component`, `text`, `rel0`, `w0`, `h0` | 컴포넌트 | data-id, 글자, **원래 자리·크기** — move·resize·remove 판별 기준 |
| `markOf` | 인터랙션 표시 | 감싼 컴포넌트 id — 버튼을 옮기거나 지우면 따라감 (`canvas.html` `markFixes`) |
| `rel`, `goto` | 관계 화살표·출발 버튼 | 관계(from·to·back), 이동할 화면 id |
| `parent` | 요소(2단계) | 속한 영역의 요소 id — 영역과 함께 움직이거나 지워지면 요소는 따로 기록하지 않는다 |

## 규칙이 모여 있는 곳

| 규칙 | 위치 |
|---|---|
| 옮김으로 볼 최소 이동 2px, 크기 변경 2% | `feedback.js` `MOVE_PX`, `SCALE_EPS` |
| 하위 페이지 최대 20개 | `board.js` `MAX_PAGES` |
| 칸·상자 간격, 색 | `layout.js` 상단 상수, `COLORS` |
| 기기 폭·높이 방식·터치 최소 크기 | `schema/devices.json` |
| 라운드: 상태의 round ≠ board.json round면 복원 안 함 / 저장 거부 | `canvas.html` `ROUND`, `server.py` do_POST |
| 옮길 수 있는 컴포넌트 = 2단계(영역 → 요소). 영역 그림은 요소를 숨기고 뜬다 | `capture.js` `measureFrame` |
| 줄 안 순서 = 앞으로 가는 관계의 위상 정렬 / 되돌아감 = `data-back` 또는 흐름상 조상으로 가는 관계 | `layout.js` `flowOrder` |
| 되돌아가는 화살표는 평소 숨김, 화면을 고르면 그 화면 것만 진하게 | `canvas.html` `arrowFixes` |
| 버튼·화살표에 ↗ 대신 goto → 고르면 "→ 이동" 버튼 | `layout.js` `gotoOf`, `canvas.html` `updateGoto` |

## 알아둘 제약

- **화면은 그림 아래에 깔린다** (`.excalidraw__embeddable-container { z-index: 0 }`, 캔버스 배경 투명). 그래서 보드에서 화면 안을 클릭할 수 없고, 배경색 메뉴는 뒤 바탕(`--board-bg`)에 칠한다.
- **이미지 뜨기는 탭이 보일 때만 된다.** 숨은 탭에서는 브라우저가 이미지 로딩을 미뤄서 `capture.js`가 보일 때까지 기다린다.
- **웹 글꼴은 화면이 쓰는 것만 넣는다** — `skipFonts`로 부모 페이지(Excalidraw) 글꼴은 건너뛰고(받느라 멈춤), 화면이 Pretendard를 쓰면 글꼴 파일 하나를 한 번 받아 모든 이미지에 `fontEmbedCSS`로 넣는다 (`capture.js`).
- Excalidraw UI를 CSS로 숨기는 부분은 **0.18.1 기준**이다. 버전을 올리면 `canvas.html`의 CSS 선택자부터 확인한다.
- 기기 enum은 `devices.json`의 키와 `board.schema.json`·`feedback.schema.json`의 `$defs.device`가 같아야 한다 (`check.py`가 board.json 값을 devices.json으로 확인).

## 확인

```bash
node --test .claude/skills/oss-design-harness/canvas/tests/feedback.test.mjs
python .claude/skills/oss-design-harness/scripts/check.py --root design
```
