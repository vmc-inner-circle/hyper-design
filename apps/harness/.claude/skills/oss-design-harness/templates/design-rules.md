<!--
4단계 산출물. 프로젝트의 design/design-rules.md로 복사해서 채운다.
값 열은 ../references/design-rules.md의 기본값에서 시작한다.
덮어쓴 항목은 출처 열에 "축 2: '빡빡해요'"처럼 단계와 원문을 적는다.
figma-builder는 status: confirmed 가 없으면 시작하지 않는다.
-->

status: draft
confirmed_at:
preview: design/probes/rules-preview.html

# Design Rules

## A. 토큰

| 키 | 값 | 출처 |
|---|---|---|
| color.bg | |  |
| color.surface-1 | |  |
| color.surface-2 | |  |
| color.text | |  |
| color.text-muted | |  |
| color.border | |  |
| color.accent | |  |
| color.accent-pressed | | 자동 |
| color.accent-soft | | 자동 |
| color.danger | | 고정 |
| color.overlay | | 고정 |
| space.scale | |  |
| space.screen-padding | |  |
| space.section | |  |
| space.card-padding | |  |
| radius | |  |
| shadow | |  |
| font.family | |  |
| type.roles | |  |
| z.scale | | 고정 |
| motion | | 고정 |
| device.frame | |  |
| safe-area | | 고정 |
| tap.min | | 고정 |
| platform | |  |

## B. 컴포넌트 규칙

| 키 | 값 | 출처 | 사용 여부 |
|---|---|---|---|
| button.sizes | |  |  |
| button.radius | |  |  |
| button.variants | |  |  |
| button.states | |  |  |
| button.row-rule | |  |  |
| button.text | |  |  |
| button.primary-per-screen | |  |  |
| button.duplicate | |  |  |
| icon.set | |  |  |
| icon.sizes | |  |  |
| icon.stroke | |  |  |
| icon.gap | |  |  |
| icon-button.hit | |  |  |
| icon-button.name | |  |  |
| icon.state | |  |  |
| icon.overflow-menu | |  |  |
| icon.proximity | |  |  |
| tap.feedback | |  |  |
| tap.long-press | |  |  |
| image.fit-by-purpose | |  |  |
| image.aspect | |  |  |
| thumbnail.spec | |  | (미사용) |
| thumbnail.strip | |  | (미사용) |
| thumbnail.title | |  | (미사용) |
| thumbnail.pressed | |  | (미사용) |
| thumbnail.selected | |  | (미사용) |
| thumbnail.selected-visible | |  | (미사용) |
| image.transition | |  |  |
| image.placeholder | |  |  |
| text.role-lock | |  |  |
| text.truncate | |  |  |
| text.short-copy | |  |  |
| text.long-copy | |  |  |
| text.scale | |  |  |
| copy.user-language | |  |  |
| copy.error | |  |  |
| copy.i18n | |  |  |
| layout.left-edge | |  |  |
| layout.section-gap | |  |  |
| layout.surface-tiers | |  |  |
| layout.device-widths | |  |  |
| layout.tablet | |  |  |
| layout.thumb-zone | |  |  |
| scroll.single | |  |  |
| scroll.last-item | |  |  |
| fixed.bottom-cta | |  |  |
| fixed.tab-bar | |  |  |
| fixed.no-clip | |  |  |
| keyboard | |  |  |
| sheet.sizes | |  |  |
| sheet.structure | |  |  |
| sheet.use | |  |  |
| dialog | |  |  |
| dialog.dismiss | |  |  |
| app-bar | |  |  |
| help.inline | |  |  |
| snackbar | |  |  |
| layer.order | |  |  |
| state.required | |  |  |
| state.empty | |  |  |
| state.loading | |  |  |
| state.error | |  |  |
| state.offline | |  |  |
| data.range | |  |  |
| data.ownership | |  |  |
| change.scope | | 고정 |  |
| change.relation | | 고정 |  |
| change.propagate | | 고정 |  |
| change.no-dup | | 고정 |  |

## C. 프로젝트 전용 규칙

도메인에만 있는 기준(플랫폼 차이, 태블릿, 제스처 등). 인터뷰에서 새로 정의된 것.

| 키 | 값 | 출처 |
|---|---|---|
