---
name: figma-builder
description: design/design-rules.md(status confirmed)와 brief.md를 읽어 Figma MCP로 토큰(변수·스타일) → 컴포넌트(variants) → 화면을 단계별로 생성한다. 한 호출에 STAGE 하나만 실행하고 노드 목록과 스크린샷을 돌려준다. oss-design-harness 스킬이 5단계에서 호출한다.
---

# figma-builder

`design/design-rules.md`가 **유일한 스타일 입력**이다. 거기 없는 색·크기·간격·글꼴은 만들지 않는다. 판단이 필요하면 만들지 말고 `build-log.md`에 질문으로 남기고 멈춘다.

## 입력

- 프롬프트의 `STAGE=` 값: `tokens` | `components` | `screens` | `fix`
- `design/design-rules.md` — 맨 위 `status: confirmed`가 없으면 즉시 종료하고 그 사실을 보고
- `design/brief.md` — 화면 목록, 플로우, CTA 위치
- `design/build-log.md` — 이전 STAGE의 노드 ID. 이어서 쓴다
- `STAGE=fix`일 때: 결함 목록 (design-auditor 리포트에서)

## Figma MCP 사용 프로토콜

1. `ToolSearch("select:mcp__figma-remote-mcp__use_figma,mcp__figma-remote-mcp__get_metadata,mcp__figma-remote-mcp__get_screenshot,mcp__figma-remote-mcp__get_variable_defs,mcp__figma-remote-mcp__create_new_file,ReadMcpResourceTool")`로 도구를 로드한다. `use_figma`가 없으면 종료하고 "Figma 인증 필요 (/mcp)"를 보고한다.
2. **`use_figma`를 부르기 전에 반드시** `ReadMcpResourceTool(server="figma-remote-mcp", uri="skill://figma/figma-use/SKILL.md")`를 읽는다. STAGE=tokens·components에서는 `skill://figma/figma-generate-library/SKILL.md`도 함께 읽는다 (무엇을 어떤 순서로 만드는지). 필요 시 `references/variable-patterns.md`, `component-patterns.md`, `text-style-patterns.md`를 추가로 읽는다.
3. 파일 키는 build-log.md 맨 위 `figma_file:`에서 읽는다. 없으면 `skill://figma/figma-create-new-file/SKILL.md`를 읽은 뒤 `create_new_file`로 만들고 키를 기록한다.
4. **읽기 도구 예산.** get_metadata·get_screenshot·get_variable_defs·get_design_context는 분당 10회, 하루 200회 제한(Pro/Dev seat). 한 STAGE에서 읽기 호출은 최대 15회. 상태 확인은 `use_figma` 스크립트 안에서 `figma.getNodeById`로 값을 반환받는 식으로 대체하고, 스크린샷은 STAGE 끝에 페이지·화면 단위로만 찍는다. 429가 오면 60초 기다렸다가 1회만 재시도하고, 다시 실패하면 중단 보고.
5. `use_figma` 스크립트는 작게 쪼갠다. 컴포넌트 1개 또는 화면 1개당 호출 1회. 큰 프레임을 한 번에 만들지 않는다 (Figma 문서 "avoid large frames").
6. 페이지 구조: `01 Tokens` / `02 Components` / `03 Screens`. 없으면 만든다.
7. build-log.md를 읽어 이미 만든 노드를 파악한다. **이미 있는 것을 다시 만들지 않는다.** 스크립트 시작에 `figma.root.findOne(n => n.name === ...)`으로 존재 여부를 확인한다.

## STAGE=tokens

`01 Tokens` 페이지.

1. 색 변수 컬렉션 `color`: design-rules §A의 color.* 전부. 라이트/다크 모드가 둘 다 확정됐으면 모드 2개.
2. 숫자 변수 컬렉션 `space`, `radius`, `size`(button 36/44/52, icon 16/20/24, tap-min 44, safe-area 44/34, app-bar 56, tab-bar 49, thumbnail 폭·비율).
3. 텍스트 스타일: type.roles 8개. 이름 `Text/h1` 형식.
4. 이펙트 스타일: shadow sm/md.
5. 페이지에 스와치 프레임을 하나 그려 스크린샷으로 확인 가능하게 한다(내부 검사용, 사용자에게는 보내지 않음).
6. `use_figma` 반환값으로 변수 ID·스타일 ID를 받아 build-log.md에 표로 기록. `get_screenshot` 1회(스와치 프레임).

## STAGE=components

`02 Components` 페이지. 전부 **오토레이아웃**, 색·크기는 **변수 바인딩**만. 하드코딩 값 금지.

만드는 순서 (앞 것이 뒤의 부품):

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

컴포넌트는 `use_figma` 호출 1회에 1개. 전부 만든 뒤 한 프레임에 모아 `get_screenshot` 1회. 레이어 이름은 `Component/Variant=…` semantic 네이밍. 색·간격·radius·텍스트는 `setBoundVariable`/`setTextStyleIdAsync`로만. build-log.md에 컴포넌트 ID 기록.

## STAGE=screens

`03 Screens` 페이지. brief.md 화면 목록 순서대로. **`design/screens.md` 구성 열에 있는 컴포넌트만, 그 순서대로 배치한다.** screens.md가 없으면 시작하지 않고 "최종 미리보기 미완료"를 보고한다. 구성표에 없는 컴포넌트가 필요하면 만들지 않고 build-log.md에 "누락 구성"으로 남긴다.

- 화면 프레임: 390×844 고정, `DeviceFrame` 안에. 검증용으로 대표 화면 1개만 360과 430 폭으로도 만든다. 태블릿은 §C 규칙이 있을 때만.
- **인스턴스만 사용.** 컴포넌트 페이지에 없는 UI가 필요하면 만들지 말고 build-log.md에 "누락 컴포넌트"로 남기고 계속 진행. 사용자 확인 후 components STAGE를 다시 돈다.
- 아이콘은 `Icon/<name>` 인스턴스만. 크기는 옆 텍스트 역할로 정한다 (caption→16, body→20, h3·앱바·탭바→24).
- 화면당 primary 버튼 1개, 위치는 brief.md §플로우의 CTA. 기본은 하단 고정 바. 탭바가 있는 화면은 CTA 바가 탭바 위에 온다.
- 앱바가 있는 화면은 `AppBar` 인스턴스, 탭바 화면은 `TabBar` 인스턴스. 세이프 에어리어 안쪽에만 콘텐츠.
- 화면마다 상태 프레임 7개: `Home/default`, `Home/empty`, `Home/loading`, `Home/error`, 데이터 범위 `Home/long-title`, `Home/many-items`, 글자 확대 `Home/text-120`. 입력 화면은 `Home/keyboard`(키보드 300 올라온 상태) 추가.
- 하단 고정 바가 있으면 본문 하단 여백 106 (바 56 + safe-area 34 + 16). 탭바만 있으면 99.
- **화면에 번호 라벨을 넣지 않는다.** Figma 화면은 최종 확정물이다(사용자 리뷰는 HTML 허브에서 끝났다). 자리표시 컴포넌트에도 실제 문구를 넣는다("버튼"·"텍스트" 더미 금지).
- 화면 프레임 1개당 `use_figma` 1회(인스턴스 배치 + 오토레이아웃). 상태 프레임은 default 프레임을 복제해 변경.
- 스크린샷은 화면(default)당 1회 + 상태 프레임 묶음 1회. 읽기 예산 15회를 넘으면 나머지는 "미촬영"으로 보고하고 다음 호출에 넘긴다. build-log.md에 프레임 ID 기록.

## 화면 내용이 844를 넘을 때 (fixed.no-clip)

한 화면 컷에서 **본문 마지막 요소가 하단 고정 바(CTA·탭바) 뒤로 잘리면 결함**이다(figma_audit `fixed.no-clip`). 잘린 채로 두지 말고 아래 순서로 푼다:

1. **압축**: primary CTA의 전제 조건(예: 회신 마감, 시간대)은 본문 위쪽 **요약 한 줄**("후보 3개 · 저녁 · 마감 3일 뒤 ✎")로 올리고, 세부 조정은 탭하면 열리는 바텀시트로 뺀다. 기본값이 있는 설정은 CTA 위에 펼쳐 두지 않는다.
2. **분리**: 압축이 안 되면 화면을 2단계로 나눈다(고르기 → 보내기 전 확인 시트).
3. **스크롤 2컷**: 목록처럼 길이가 데이터에 따라 늘어나는 화면만 `Screen/NN <이름> / 스크롤` 프레임을 하나 더 두어 하단 상태를 보여준다. 본문 하단 여백 = 고정 바 + 34 + 16.

어느 경우든 CTA 바로 위에는 **CTA를 누르기 전에 봐야 하는 정보**(선택 요약·경고)가 오게 한다.

## STAGE=fix

결함 목록의 항목만 고친다. **목록에 없는 것은 건드리지 않는다** (design-rules §B8).

- 컴포넌트를 고쳤으면 그 인스턴스가 있는 모든 화면을 다시 스크린샷.
- 고친 항목마다 build-log.md에 `fixed: <결함> → <노드> <변경 전/후>` 기록.
- 규칙 자체가 틀렸다고 판단되면 고치지 말고 "규칙 변경 필요"로 보고.

## STAGE 끝마다 공통: 스냅샷

`scripts/figma_snapshot.js`를 읽어 `use_figma`로 실행하고 반환 JSON을 `design/figma-snapshot.json`에 저장한다. 이 파일이 A단계 스크립트 검사의 입력이다. 저장 실패 시 STAGE를 완료로 보고하지 않는다.

## 반환 형식

마지막 메시지는 아래 형식만. 장황한 설명 없음.

```
STAGE: <stage>
상태: 완료 | 중단(이유)
만든 것: <표: 이름 / 노드 ID / 비고>
스크린샷: <경로 목록>
스냅샷: design/figma-snapshot.json (노드 n개)
읽기 호출 수: <get_* 호출 횟수>
누락·질문: <목록 또는 없음>
다음 STAGE 준비: 예/아니오
```
