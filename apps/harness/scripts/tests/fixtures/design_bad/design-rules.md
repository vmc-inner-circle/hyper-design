<!--
실패 픽스처.
-->

status: draft
confirmed_at:
preview: design/probes/rules-preview.html

# Design Rules

## A. 토큰

| 키 | 값 | 출처 |
|---|---|---|
| color.bg | blue | 축 1 |
| color.surface-1 | #F5F5F7 | 축 1 |
| color.surface-2 | #E9E9EE | 축 1 |
| color.text | #111827 | 축 1 |
| color.text-muted | #6B7280 | 축 1 |
| color.border | #E5E7EB | 축 1 |
| color.accent | #F97316 | 정함 |
| color.accent-pressed | accent를 12% 어둡게 | 자동 |
| color.accent-soft | accent 10% 불투명 | 자동 |
| color.danger | #DC2626 | 고정 |
| color.overlay | rgba(0,0,0,.5) 하나만 | 고정 |
| space.scale | 4 / 8 / 12 / 15 / 24 / 32 / 48 | 축 2 |
| space.screen-padding | 좌우 16 | 축 2 |
| space.section | 24 | 축 2 |
| space.card-padding | | 축 2 |
| radius | sm 4 / md 8 / lg 12 / xl 16 / full 9999 | 축 3 |
| shadow | sm 0 1px 2px rgba(0,0,0,.06) | 축 3 |
| font.family | "Pretendard", -apple-system, Roboto, sans-serif | 축 5 |
| type.roles | display 28/700 · h1 24/600 · body 15/400 | 축 5 |
| z.scale | base 0 · sticky 100 · app-bar 200 · tab-bar 150 · overlay 300 · sheet 400 · dialog 500 · snackbar 600 | 고정 |
| motion | 200ms ease-out | 고정 |
| device.frame | 375×812 기준 | 1단계 플랫폼 |
| safe-area | 상단 44 · 하단 34 | 고정 |
| tap.min | 40×40 | 고정 |
| platform | iOS·Android 공통 1벌 | 1단계 플랫폼 |

## B. 컴포넌트 규칙

| 키 | 값 | 출처 | 사용 여부 |
|---|---|---|---|
| button.sizes | sm 36h / md 40h / lg 52h | 축 3 | |
| button.radius | radius.md | 축 3 | |
| icon.set | lucide 단일 | 고정 | |
| icon.sizes | 16 / 18 / 24 | 고정 | |
| icon-button.hit | 탭 영역 44×44 정사각 | 고정 | |
| thumbnail.spec | | | |
| thumbnail.strip | 가로 스트립 높이 96 | 3단계 | |
| sheet.sizes | half / full | 고정 | |
| app-bar | 높이 56 | 고정 | |
| state.required | 초기·빈·로딩·성공·실패·비활성 6상태 | 고정 | |
| layout.tablet | | 고정 | |

## C. 프로젝트 전용 규칙

| 키 | 값 | 출처 |
|---|---|---|
| filter.strip | 필터 썸네일 가로 스트립 | 레퍼런스 |
