<!--
design/components.md 템플릿. 토큰(theme.js)을 정한 뒤, 화면을 만들기 전에 채운다 (references/screen-generation.md §생성 순서 3).
여러 화면에 반복되는 공통 컴포넌트만 적는다 — 한 화면에만 있는 것은 그 화면 HTML의 data-id로 충분하다.
모양은 Basecoat 컴포넌트·변형을 고른다 (screen-generation.md §Basecoat 컴포넌트). Basecoat에 없는 조합만 유틸리티 + 토큰 이름으로. 공통 조각은 한 번 쓰고 화면은 그대로 복사한다.
기기별로 구간을 나눈다: 모바일 구간 → PC 구간(PC를 쓰는 화면이 있을 때만).
빈 템플릿입니다 — 아래 TODO는 형식 예시이며 실제 내용이 아닙니다.
-->

# Components (공통)

## 강조 위계 — 화면마다 무엇을 보이고, 하나만 강조하고, 무엇을 숨기나

컴포넌트를 고르기 전에 정한다. 모든 화면이 따른다. 서비스에 맞게 고친 줄은 근거를 G로 바꾼다.

| ID | 규칙 | 적용 | 근거 |
|---|---|---|---|
| P1 | 화면마다 주 행동은 하나 — `btn`(주 변형), 모바일은 엄지가 닿는 아래쪽. 나머지 행동은 `outline`·`ghost` | all | 관찰: 라이브러리 비교 (2026-09-30) |
| P2 | 화면의 핵심 수치·상태 하나만 `text-primary` 또는 큰 글자(`text-2xl` 이상)로 강조 | all | 관찰: 라이브러리 비교 (2026-09-30) |
| P3 | 상태 배지는 상태마다 다른 `data-variant` — 같은 모양 배지로 상태를 나누지 않는다 | 목록 화면 | 관찰: 라이브러리 비교 (2026-09-30) |
| P4 | 보조 정보는 `text-muted-foreground`, 지금 판단에 필요 없는 정보는 숨기거나 다음 화면으로 | all | 관찰: 라이브러리 비교 (2026-09-30) |

## 모바일 구간 (기본)

| data-id | 종류 | Basecoat 컴포넌트·변형 (없으면 유틸리티 + 토큰) | 들어가는 곳 | 상태 |
|---|---|---|---|---|
| TODO: tab-bar | 영역 | (Basecoat 없음) `fixed bottom-0 inset-x-0 bg-card border-t border-border pb-8 lg:hidden` | 역할 A 화면 전부, `data-nav` | — |
| TODO: tab-home | 요소 | `btn` `data-variant="ghost"` + `h-11 flex-col text-xs text-muted-foreground` | tab-bar 안 | 선택됨: `text-primary` |
| TODO: primary-btn | 요소 | `btn` + `h-11 w-full` | 하단 고정 바 | 비활성: `disabled` |
| TODO: list-row | 요소 | `item` `data-variant="outline"` (링크면 `<a class="item">`) | 목록 화면 | — |
| TODO: status-badge | 요소 | `badge` — 상태마다 다른 `data-variant` | list-row 안 | — |

### 모바일 조각

모바일만 쓰는 화면은 이 조각을 그대로 복사하고 글자·링크·현재 상태만 바꾼다.

```html
<!-- TODO: tab-bar -->
<nav data-id="tab-bar" data-nav class="TODO">
  <a data-id="tab-home" href="home.html" class="btn TODO" data-variant="ghost"><i data-lucide="TODO"></i><span>TODO</span></a>
</nav>
```

```html
<!-- TODO: primary-btn -->
<a data-id="TODO-btn" href="TODO.html" class="btn h-11 w-full">TODO</a>
```

## PC 구간 (PC를 쓰는 화면이 있을 때만)

PC를 쓰는 화면: TODO (brief.md 화면 목록의 기기 칸과 같게)

| data-id | 모바일과 무엇이 다른가 | PC 모양 |
|---|---|---|
| TODO: side-nav | PC 전용 (모바일 tab-bar 대신) | `hidden lg:flex w-60 flex-col bg-card border-r border-border` (Basecoat `sidebar`는 쓰지 않는다) |
| TODO: tab-bar | PC에서 숨김 | 모바일 조각 그대로 (`lg:hidden` 포함) |
| TODO: primary-btn | 하단 고정 → 본문 안, 폭 자동 | 모바일 조각 + `lg:static lg:w-auto lg:h-10` |

### PC 조각

PC를 쓰는 화면은 **이 조각을 복사한다** (모바일 클래스 + `lg:` 클래스가 이미 합쳐진 완성본). 화면에서 `lg:`를 새로 붙이지 않는다 — 필요하면 여기에 더한다.

```html
<!-- TODO: side-nav -->
<aside data-id="side-nav" data-nav class="TODO">…</aside>
```

```html
<!-- TODO: primary-btn (PC를 쓰는 화면용) -->
<a data-id="TODO-btn" href="TODO.html" class="btn TODO">TODO</a>
```
