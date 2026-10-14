# images 계약

`python3 $SK/features/images/imggen.py out [--placeholders-only] [--cmd "<생성기>"] [--timeout 480]`

## 입력
- `out/image_slots.json` (목록). `kind == "photo"`만 쓴다 — `kind`가 없으면 photo로 본다.
- 항목 필드: `slot`, `what`(한국어), `ratio`(`1:1`·`4:3`·`3:4`·`16:9`…), `en`(영어 묘사, 문자열 또는 목록 — 첫 문자열을 쓰고, 없으면 `what`).

## 출력
- `out/assets/photos/<slot>.jpg` — 슬롯 비율, 긴 변 1200.
- `out/credits.json` — 생성된 칸만 `{slot,file,author:"AI 생성 (codex image_generation)",license:"generated",url:"",title:what}`. 다른 파일 항목은 그대로 두고, 같은 `file` 항목은 바꾼다. 자리표시로 남은 슬롯은 항목을 쓰지 않는다(selfcheck가 잡는다).
- `out/.images/status.json` — `{state, sheets, generated, placeholders, alternates, elapsed_s, notes[], sheet_plan[], reason?}`.
  `sheet_plan` 항목: `{cells:"2x2", cell_ratio:"4:3", slots:[...]}`.
- `out/.images/sheet-<n>.png` — 생성 시트 원본.
- `out/.images/alt/<slot>-alt<i>.jpg` — 빈칸에 만든 다른 구도. 화면·credits에 쓰지 않는다.

## 동작
1. 모든 사진 자리에 회색 자리표시를 **먼저** 쓴다(빌드는 이 경로를 바로 쓸 수 있다).
2. 시트를 최소로 만든다(같은 입력 → 같은 계획). 슬롯을 정사각(w=h)·가로(w>h)·세로(w<h)로 나눈다.
   - 사진 ≤ 4장 → 2×2 시트 하나에 모두.
   - 그 밖: 정사각은 최대 16칸(≤4 → 2×2, ≤9 → 3×3, 그 밖 4×4), 가로·세로는 방향별로 최대 4칸 2×2.
   - 1–2장만 남은 묶음은 빈칸이 충분한 2×2 방향 시트에 합친다(반대 방향 우선, 작은 묶음부터).
   - 2×2 칸 비율: 가로 ≥ 세로면 `4:3`, 아니면 `3:4`(정사각만이면 `1:1`).
   - 빈칸은 같은 시트 사진의 `alternate angle of: <en>`로 채운다(시트 슬롯을 차례로 돈다).
   - 프롬프트: 단일 물건은 밝은 웜그레이 배경·제품 사진, 장면·실내·인물은 묘사대로의 자연 배경. 칸 비율과 다른 슬롯은 `(… cropped to <ratio>)`를 붙인다.
3. 시트마다 생성기를 **순서대로** 한 번씩 부른다(병렬 없음 — 부하 제한). 호출: `<cmd> "<prompt>" <절대경로.png>`.
4. 흰 간격 감지로 자른다. 띠 개수가 맞지 않으면 균등 분할(`sheet N: equal split fallback` 기록). 칸마다 **슬롯 자신의** 비율로 가운데 자르고 자리표시를 덮어쓴다.

## 생성기 찾기 (먼저 있는 것)
`--cmd` → 환경변수 `HD_IMAGE_CMD` → `~/.claude/skills/gpt-image-bridge/bin/gpt-image-2`(Windows는 `bash`로 실행).

## 상태
| state | 뜻 |
|---|---|
| `running` | 진행 중 |
| `done` | 모든 사진 자리가 생성됨 |
| `fallback` | 하나 이상이 자리표시로 남음 — `reason`/`notes`에 이유 |

## 대체 규칙
- 생성기 없음 → `fallback`, reason `no generator`, 자리표시 유지.
- `--placeholders-only` → `fallback`, reason `placeholders-only`.
- 시트의 시간 초과(`--timeout`, 기본 480초)·0 아닌 종료·출력 없음 → 그 시트의 칸만 자리표시 유지, 이유 기록, 다음 시트 계속.
- 처리된 경우는 모두 종료 코드 0 — fallback은 오류가 아니다.

## 메인이 기다리는 법
1.5단계에서 백그라운드로 시작하고, 3단계 검사 전에 `out/.images/status.json`의 `state`가 `running`이 아닐 때까지 기다린다.
