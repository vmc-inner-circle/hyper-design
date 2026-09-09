<!--
테스트용 픽스처. templates/design-rules.md 를 references/design-rules.md 기본값으로 채운 예시.
figma_audit.py 가 이 표에서 기준값(space.scale, icon.sizes, tap.min, device.frame,
safe-area, z.scale, button.sizes, button.states 등)을 파싱한다.
-->

status: confirmed
confirmed_at: 2026-09-05
preview: design/probes/rules-preview.html

# Design Rules

## A. 토큰

| 키 | 값 | 출처 |
|---|---|---|
| color.bg | #FFFFFF | 기본값 |
| color.surface-1 | #F5F5F7 | 기본값 |
| color.surface-2 | #E9E9EE | 기본값 |
| color.text | #111827 | 기본값 |
| color.text-muted | #6B7280 | 기본값 |
| color.border | #E5E7EB | 기본값 |
| color.accent | #2563EB | 기본값 |
| color.accent-pressed | #1D4FD8 | 자동 |
| color.accent-soft | rgba(37,99,235,.1) | 자동 |
| color.danger | #DC2626 | 고정 |
| color.overlay | rgba(0,0,0,.5) | 고정 |
| space.scale | 4 / 8 / 12 / 16 / 24 / 32 / 48 (4 배수만 허용) | 기본값 |
| space.screen-padding | 좌우 16 | 기본값 |
| space.section | 24 | 기본값 |
| space.card-padding | 16 | 기본값 |
| radius | sm 4 / md 8 / lg 12 / xl 16 / full 9999 | 기본값 |
| shadow | sm 0 1px 2px rgba(0,0,0,.06) / md 0 4px 12px rgba(0,0,0,.08) | 기본값 |
| font.family | "Pretendard", -apple-system, Roboto, sans-serif | 기본값 |
| type.roles | display 28/700 · h1 24/600 · h2 20/600 · h3 17/600 · body 15/400 · body-sm 14/400 · caption 12/400 · label 13/500 | 기본값 |
| z.scale | base 0 · sticky 100 · app-bar 200 · tab-bar 200 · overlay 300 · sheet 400 · dialog 500 · snackbar 600 | 고정 |
| motion | 200ms ease-out. 시트 열림 250ms | 고정 |
| device.frame | 390×844 기준. 검증 폭 360 / 390 / 430 | 기본값 |
| safe-area | 상단 상태바 44(노치 기기 47) · 하단 홈 인디케이터 34 | 고정 |
| tap.min | 44×44. 인접 탭 영역 간격 최소 8 | 고정 |
| platform | iOS·Android 공통 1벌 | 1단계 |

## B. 컴포넌트 규칙

| 키 | 값 | 출처 | 사용 여부 |
|---|---|---|---|
| button.sizes | sm 36h / px12 / text14 · md 44h / px16 / text15 · lg 52h / px20 / text16 | 기본값 | 사용 |
| button.radius | radius.md | 기본값 | 사용 |
| button.variants | primary · secondary · ghost · danger | 기본값 | 사용 |
| button.states | default · pressed(배경 12% 명도 변화) · selected(accent-soft) · disabled(opacity .4) · loading(스피너 20) | 기본값 | 사용 |
| button.row-rule | 같은 줄의 버튼은 같은 size·radius | 기본값 | 사용 |
| button.primary-per-screen | 화면당 primary 1개. 하단 고정 바 | 기본값 | 사용 |
| icon.set | lucide 단일. 다른 세트 혼용 금지 | 기본값 | 사용 |
| icon.sizes | 16 (인라인·캡션) / 20 (버튼·목록) / 24 (앱바·탭바). 세 값 외 금지 | 기본값 | 사용 |
| icon.stroke | 1.75 고정 | 기본값 | 사용 |
| icon.gap | 텍스트와 8px, 수직 중앙 정렬 | 기본값 | 사용 |
| icon-button.hit | 탭 영역 44×44 정사각 | 기본값 | 사용 |
| thumbnail.spec | 1:1, 3열 그리드, gap 8, radius.md | 기본값 | 사용 |
| thumbnail.title | 아래 1줄 말줄임 | 기본값 | 사용 |
| thumbnail.selected | border accent 2px + 체크 배지 20 | 기본값 | 사용 |
| text.role-lock | 같은 역할 = 같은 type.role | 기본값 | 사용 |
| layout.left-edge | 좌측 시작선 = 16 | 기본값 | 사용 |
| layout.section-gap | 24 | 기본값 | 사용 |
| fixed.bottom-cta | 높이 56 + safe-area 34 | 기본값 | 사용 |
| fixed.tab-bar | 높이 49 + safe-area 34 | 기본값 | 사용 |
| app-bar | 높이 56 | 기본값 | 사용 |
| snackbar | 하단 고정 바 위 16 | 기본값 | 사용 |
| layer.order | 스낵바 > 다이얼로그 > 시트 > 탭바·앱바 | 고정 | 사용 |
| state.required | 초기 · 빈 · 로딩 · 성공 · 실패 · 비활성 | 기본값 | 사용 |

## C. 프로젝트 전용 규칙

| 키 | 값 | 출처 |
|---|---|---|
