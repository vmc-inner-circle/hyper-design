---
name: figma-builder
description: 사용자가 "Figma 생성"을 명시 지시했을 때만 실행한다. 6단계까지 확정된 HTML(final-preview.html·rules-preview.html)과 design/design-rules.md(status confirmed)·icons.md·screens.md를 입력으로 Figma MCP로 토큰(변수·스타일) → 컴포넌트(variants) → 화면(default, 상태는 요청 시)을 단계별로 생성하고, STAGE 끝마다 figma_parity로 이름·개수 일치를 검사한다. 한 호출에 STAGE 하나만 실행한다. oss-design-harness 스킬이 선택 7단계에서 호출한다.
---

# figma-builder

**실행 조건: 사용자의 "Figma 생성" 명시 지시.** 메인 대화가 프롬프트에 `Figma 생성 지시 있음`을 적지 않았으면 아무것도 만들지 않고 `상태: 중단(Figma 생성 지시 없음)`으로 반환한다. 하네스의 최종 산출물은 HTML이다. Figma는 그 HTML을 옮겨 만드는 선택 단계다.

**값은 `design/design-rules.md`, 배치·문구는 확정 HTML을 따른다.** design-rules에 없는 색·크기·간격·글꼴은 만들지 않는다. 화면 구성·순서·문구·상태 모습은 `final-preview.html`의 `.phone[data-state]`, 컴포넌트 모양은 `rules-preview.html`의 `data-component` 견본을 따른다. 둘이 어긋나면 값은 규칙, 배치는 HTML — 어긋남은 build-log.md에 기록한다. 판단이 필요하면 만들지 말고 build-log.md에 질문으로 남기고 멈춘다.

## 입력

- 프롬프트: `Figma 생성 지시 있음` + `STAGE=` 값(`tokens` | `components` | `screens` | `fix`). 선택: `STATES=<상태 목록>`(screens), `SNAPSHOT=full`(전수 스냅샷)
- `design/probes/final-preview.html` — 화면별 default·상태 프레임의 배치·문구 (HTML 소스를 `Read`로 읽는다. 브라우저로 열지 않는다)
- `design/probes/rules-preview.html` — 컴포넌트 견본·상태
- `design/design-rules.md` — 맨 위 `status: confirmed`가 없으면 즉시 종료하고 그 사실을 보고
- `design/icons.md` — 아이콘 허용 목록
- `design/screens.md` — 화면별 구성표(구성 열 = 인스턴스 목록). 확정본이 아니면 시작하지 않는다
- `design/brief.md` — 화면 목록, 플로우, CTA 위치
- `design/build-log.md` — 이전 STAGE의 노드 ID. 이어서 쓴다. 6단계 오디트 "통과"가 없으면 반환 "누락·질문"에 경고로 적는다(멈추지는 않는다)
- `STAGE=fix`일 때: 결함 목록 (design-auditor의 parity 라우팅에서)

## Figma MCP 사용 프로토콜

1. **도구 이름을 먼저 확인한다.** 환경마다 접두사가 다르다(`mcp__plugin_figma_figma__*` 또는 `mcp__figma-remote-mcp__*`). `ToolSearch("use_figma")`로 실제 이름을 찾은 뒤 그 접두사로 `use_figma`·`get_screenshot`·`create_new_file`·`get_variable_defs`를 한 번에 로드한다. `use_figma`가 없으면 종료하고 "Figma 인증 필요 (/mcp)"를 보고한다.
2. **`use_figma`를 부르기 전에 반드시** figma-use 스킬을 읽는다. 플러그인 도구면 `Skill("figma:figma-use")`, 원격 MCP면 `ReadMcpResourceTool(server="figma-remote-mcp", uri="skill://figma/figma-use/SKILL.md")`. STAGE=tokens·components에서는 figma-generate-library도 함께 읽는다(무엇을 어떤 순서로 만드는지).
3. 파일 키는 build-log.md `## figma` 절의 `figma_file:`에서 읽는다. 없으면 figma-create-new-file 스킬을 읽은 뒤 `create_new_file`로 만들고 키를 기록한다.
4. **읽기 도구 예산.** get_metadata·get_screenshot·get_variable_defs·get_design_context는 분당 10회, 하루 200회 제한(Pro/Dev seat). STAGE별 읽기: tokens 0 · components 1(모음 프레임) · screens 화면(default)당 1. 상태 확인은 `use_figma` 스크립트 안에서 `await figma.getNodeByIdAsync(id)`로 값을 반환받는 식으로 대체한다. 429가 오면 60초 기다렸다가 1회만 재시도하고, 다시 실패하면 중단 보고.
5. `use_figma` 스크립트는 작게 쪼갠다. 컴포넌트 1개 또는 화면 1개당 호출 1회. 큰 프레임을 한 번에 만들지 않는다. 반환값은 필요한 ID·이름만(20KB 제한, 아래 함정 참고).
6. 페이지 구조: `01 Tokens` / `02 Components` / `03 Screens`. 없으면 만든다.
7. build-log.md를 읽어 이미 만든 노드를 파악한다. **이미 있는 것을 다시 만들지 않는다.** 스크립트 시작에 `figma.root.findOne(n => n.name === ...)`으로 존재 여부를 확인한다.

## STAGE=tokens

`01 Tokens` 페이지.

1. 색 변수 컬렉션 `color`: design-rules §A의 color.* 전부. 라이트/다크 모드가 둘 다 확정됐으면 모드 2개.
2. 숫자 변수 컬렉션 `space`, `radius`, `size`(button 36/44/52, icon 16/20/24, tap-min 44, safe-area 44/34, app-bar 56, tab-bar 49, thumbnail 폭·비율).
3. 텍스트 스타일: type.roles 8개. 이름 `Text/h1` 형식.
4. 이펙트 스타일: design-rules §A `shadow`의 이름마다 `Shadow/<이름>`(예: `Shadow/sm`, `Shadow/md`). parity가 이 이름으로 대조한다(`parity.effect-styles`).
5. `use_figma` 반환값으로 변수 ID·스타일 ID를 받아 build-log.md에 표로 기록. 스크린샷은 찍지 않는다(parity로 대체).

## STAGE=components

`02 Components` 페이지. 전부 **오토레이아웃**, 색·크기는 **변수 바인딩**만. 하드코딩 값 금지. **`rules-preview.html`의 `data-component` 견본과 screens.md 구성 열에 등장하는 컴포넌트만** 만든다. 이름은 `data-component` 값과 정확히 같게(parity가 이름으로 대조한다).

만드는 순서 (앞 것이 뒤의 부품. 목록에 없는 것은 건너뛴다):

1. `Icon/<name>` — `design/icons.md` 허용 목록의 lucide 아이콘만. 각 이름마다 SVG를 가져와(`curl -s https://unpkg.com/lucide-static@latest/icons/<name>.svg`) `use_figma`에서 `figma.createNodeFromSvg(svg)`로 만들고 컴포넌트화. size 속성 16/20/24 variants, stroke 1.5/1.75/2, 색은 currentColor → text 변수 바인딩. **벡터를 직접 그리거나 기존 아이콘을 변형해 새 아이콘을 만들지 않는다.** 목록에 없는 아이콘이 필요하면 만들지 말고 build-log.md "누락 아이콘"에 적고 계속 진행
2. `Button` — variants: variant(primary/secondary/ghost/danger) × size(sm/md/lg) × state(default/pressed/selected/disabled/loading). 텍스트 한 줄. 아이콘 슬롯 boolean
3. `IconButton` — size(sm/md/lg) × state. 탭 영역 44 정사각 (시각 크기와 별도)
4. `Thumbnail` — state(default/pressed/selected) × 제목 위치는 규칙의 1개만
5. `Card` — 제목 2줄 말줄임 텍스트(고정 높이 2줄)
6. `Input`, `Select` — state(default/focus/error/disabled). 도움말 caption 슬롯
7. `AppBar` — 뒤로 boolean, 제목, 우측 액션 0~2
8. `TabBar` — 탭 3/4/5 × 활성 인덱스. safe-area 하단 포함
9. `BottomSheet` — size(half/full). 그랩바 / 헤더 56 / 본문 fill / 푸터 CTA + safe-area
10. `Dialog` — 폭 화면-48, 버튼 2개
11. `BottomCTA` — 높이 56 + safe-area 34
12. `Snackbar` — 액션 boolean
13. `EmptyState`, `Skeleton`, `ErrorState`, `OfflineBanner`
14. `DeviceFrame` — 390×844 상태바 44 + 홈 인디케이터 34. 모든 화면의 바깥 틀

컴포넌트는 `use_figma` 호출 1회에 1개. 크기가 화면마다 달라야 하는 부품은 **처음부터 variant·속성으로 만든다**(인스턴스에서 크기를 못 바꾼다 — 아래 함정). 전부 만든 뒤 한 프레임에 모아 `get_screenshot` 1회(내부 확인용, 사용자에게 보내지 않음). 레이어 이름은 `Component/Variant=…` semantic 네이밍. 색·간격·radius·텍스트는 `setBoundVariable`/`setTextStyleIdAsync`로만. build-log.md에 컴포넌트 ID 기록.

## STAGE=screens

`03 Screens` 페이지. brief.md 화면 목록 순서대로. **`design/screens.md` 구성 열에 있는 컴포넌트만, 그 순서대로 배치한다.** 배치·문구는 `final-preview.html`의 해당 `<section data-screen>` default `.phone`을 그대로 옮긴다. 구성표에 없는 컴포넌트가 필요하면 만들지 않고 build-log.md에 "누락 구성"으로 남긴다.

- **기본은 default 프레임만.** 이름 `<화면명>/default`. 상태 프레임은 프롬프트에 `STATES=`가 있을 때 **그 상태만** 만든다(`<화면명>/<state>`, HTML의 같은 `data-state` 프레임을 옮긴다). default를 복제해 변경한다.
- 화면 프레임: 390×844 고정, `DeviceFrame` 안에. 360·430 검증 폭 프레임은 만들지 않는다(HTML 렌더에서 검증이 끝났다). 요청 시만.
- **인스턴스만 사용.** 컴포넌트 페이지에 없는 UI가 필요하면 만들지 말고 build-log.md에 "누락 컴포넌트"로 남기고 계속 진행. detach 금지.
- 아이콘은 `Icon/<name>` 인스턴스만. 크기는 옆 텍스트 역할로 정한다 (caption→16, body→20, h3·앱바·탭바→24).
- 화면당 primary 버튼 1개, 위치는 HTML의 `data-primary`와 같은 자리. 앱바·탭바·하단 고정 바도 HTML과 같게. 세이프 에어리어 안쪽에만 콘텐츠.
- 하단 고정 바가 있으면 본문 하단 여백 106 (바 56 + safe-area 34 + 16). 탭바만 있으면 99.
- 본문이 844를 넘는 화면은 HTML이 이미 푼 방식(요약 한 줄 + 시트 / 화면 분리 / 스크롤 여백)을 그대로 따른다. HTML에 없는 새 해결을 만들지 않는다.
- **화면에 번호 라벨을 넣지 않는다.** 자리표시 컴포넌트에도 HTML과 같은 실제 문구를 넣는다("버튼"·"텍스트" 더미 금지).
- 화면 프레임 1개당 `use_figma` 1회(인스턴스 배치 + 오토레이아웃).
- 스크린샷은 화면 default당 1회 → `design/screenshots/figma/<slug>-default.png`. 메인 대화가 한 장씩 사용자에게 보낸다. 상태 프레임은 찍지 않는다(요청 시만). build-log.md에 프레임 ID 기록.

## STAGE=fix

결함 목록의 항목만 고친다. **목록에 없는 것은 건드리지 않는다** (design-rules §B8).

- 컴포넌트를 고쳤으면 그 인스턴스가 있는 화면 목록을 반환에 적는다(스크린샷은 사용자가 요청할 때만).
- 고친 항목마다 build-log.md에 `fixed: <결함> → <노드> <변경 전/후>` 기록.
- 규칙 자체가 틀렸다고 판단되면 고치지 말고 "규칙 변경 필요"로 보고.

## STAGE 끝마다 공통: parity 검사

1. `scripts/figma_parity.js`를 읽어 `use_figma`로 **1회** 실행한다(읽기 전용, 이름·개수만 반환). 반환 JSON을 `design/figma-parity.json`에 저장한다.
2. `python3 scripts/figma_parity.py --actual design/figma-parity.json --rules design/design-rules.md --icons design/icons.md --screens design/screens.md [--states <STATES 값>]`을 돌린다.
3. tokens·components STAGE에서는 그 STAGE 항목(변수·스타일 / 컴포넌트·아이콘)의 결과만 본다 — 아직 안 만든 화면의 누락은 실패로 보지 않는다. screens·fix STAGE에서는 **exit 0 필수**. 저장·실행이 실패하면 STAGE를 완료로 보고하지 않는다.
4. **전수 스냅샷은 `SNAPSHOT=full`일 때만.** `scripts/figma_snapshot.js` → `design/figma-snapshot.json` → `figma_audit.py`. 20KB 제한 때문에 여러 번 나눠 받아야 하므로 기본으로 돌리지 않는다.

## 알려진 함정

| 함정 | 증상 | 대응 |
|---|---|---|
| 도구 이름이 환경마다 다름 | `mcp__figma-remote-mcp__use_figma`를 불렀는데 도구 없음 | `ToolSearch("use_figma")`로 실제 접두사(`mcp__plugin_figma_figma__*` 등)를 확인하고 로드. 스킬 로드 방식(Skill / ReadMcpResourceTool)도 접두사에 맞춘다 |
| `use_figma` 반환 20KB 제한 | 큰 JSON이 잘려 파싱 실패. 전수 스냅샷을 받으려면 수십 회(지난 과제 60회)로 나눠야 했다 | 반환은 ID·이름·개수만. 전수 스냅샷은 `SNAPSHOT=full`일 때만, 페이지·화면 단위로 나눠 받는다 |
| 인스턴스 override 한계 | 인스턴스에서 `resize()`·`minWidth`/`maxWidth` 변경이 안 되거나 무시됨 | 크기 차이는 컴포넌트의 variant·속성으로 만들거나 부모 오토레이아웃의 `layoutSizingHorizontal/Vertical`(FILL/HUG)로 푼다. detach로 우회하지 않는다 |
| 슬롯 스왑 후 컨테이너 sizing | `swapComponent`·자식 교체 뒤 부모가 FIXED로 남거나 HUG가 풀려 잘림·늘어남 | 스왑 직후 부모 컨테이너의 sizing을 다시 지정하고, 같은 스크립트에서 width·height를 반환받아 HTML 크기와 비교한다 |
| 읽기 예산 | 429, 하루 200회 소진 | 상태 확인은 `use_figma` 반환값으로. 스크린샷은 화면 default당 1회만 |

## 반환 형식

마지막 메시지는 아래 형식만. 장황한 설명 없음.

```
STAGE: <stage>
상태: 완료 | 중단(이유)
만든 것: <표: 이름 / 노드 ID / 비고>
스크린샷: <경로 목록>
parity: figma_parity.py exit <n> — 실패 항목 요약 (design/figma-parity.json)
읽기 호출 수: <get_* 호출 횟수>
누락·질문: <목록 또는 없음>
다음 STAGE 준비: 예/아니오
```
