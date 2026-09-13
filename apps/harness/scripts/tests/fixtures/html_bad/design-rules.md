<!-- html_audit.py 테스트 픽스처. 실제 design-rules.md 형식을 축소했다. -->

status: confirmed
confirmed_at: 2026-09-12

# Design Rules

## A. 토큰

| 키 | 값 | 출처 |
|---|---|---|
| color.bg | #FDFBF7 | 축 1: "추천대로" |
| color.surface-1 | #F5F0E8 | 축 1 |
| color.text | #1F1B16 | 축 1 |
| color.text-muted | #7A6F63 | 축 1 |
| color.border | #E7E0D4 | 축 1 |
| color.accent | #F97316 | 축 4 |
| color.on-accent | #FFFFFF | 자동 |
| color.accent-soft | rgba(249,115,22,.10) (accent 10% 불투명) | 자동 |
| space.scale | 4 / 8 / 12 / 16 / 24 / 32 / 48 | 축 2 |
| space.screen-padding | 좌우 16 | 축 2 |
| radius | sm 4 / md 8 / lg 12 / full 9999. 버튼 md, 카드 lg | 축 3 |
| shadow | sm 0 1px 2px rgba(0,0,0,.06) / md 0 4px 12px rgba(0,0,0,.08). 카드 sm | 축 3 |
| font.family | "Pretendard", Roboto, sans-serif | 축 5 |
| type.roles | h3 17/600 · body 15/400 · caption 12/400 (line-height 1.5, 제목 1.3) | 축 5 |
| z.scale | base 0 · sticky 100 · tab-bar 200 · overlay 300 | 고정 |
| device.frame | 390×844 기준. 검증 폭 360 / 390 / 430 | 1단계 |
| safe-area | 상단 상태바 44 · 하단 홈 인디케이터 34 | 고정 |
| tap.min | 44×44. 인접 탭 영역 간격 최소 8 | 고정 |

## B. 컴포넌트 규칙

| 키 | 값 | 출처 | 사용 여부 |
|---|---|---|---|
| button.sizes | sm 36h / px12 / text14 · md 44h / px16 / text15 · lg 52h / px20 / text16 | 기본값 | 사용 |
| button.states | default · pressed · selected · disabled · loading | 기본값 | 사용 |
| icon.sizes | 16 / 20 / 24 | 기본값 | 사용 |
| icon-button.hit | 44×44 | 기본값 | 사용 |
| thumbnail.spec | | 기본값 | (미사용) |

## C. 프로젝트 전용 규칙

| 키 | 값 | 출처 |
|---|---|---|
| web.primary | 웹 예외 화면(my-prep)은 부모 웹 스타일을 따라 primary 0~1개 | 1단계 |
