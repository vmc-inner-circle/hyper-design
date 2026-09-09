# 디자인 규칙 — 기본값과 덮어쓰기 키 (모바일 앱)

`docs/이슈.md`(22항목)와 `docs/desingissue.md`(10주제)를 **모바일 앱 기준** 규칙으로 바꾼 것. 모든 항목에 **기본값**이 있다. 사용자가 아무것도 정하지 않아도 이 값으로 일관성이 보장된다. 인터뷰(1~3단계)에서 확정된 값이 있으면 그 값으로 덮어쓰고 출처를 적는다.

원본 이슈의 데스크톱 개념은 이렇게 옮겼다: hover → pressed, 커서 → 탭 영역, 툴팁 → 롱프레스 라벨·인라인 도움말, 모달 크기 → 바텀시트/다이얼로그, 반응형 → 기기 폭 360/390/430 + 글자 확대.

`design/design-rules.md`는 이 파일의 표를 복사해 값 열을 채운 것이다. figma-builder는 그 파일만 읽는다.

## A. 토큰

| 키 | 기본값 | 덮어쓰는 단계 |
|---|---|---|
| color.bg | #FFFFFF | 축 1 |
| color.surface-1 | #F5F5F7 | 축 1 |
| color.surface-2 | #E9E9EE | 축 1 |
| color.text | #111827 | 축 1 |
| color.text-muted | #6B7280 | 축 1 |
| color.border | #E5E7EB | 축 1 |
| color.accent | #2563EB | 축 4 / 브랜드 색 |
| color.accent-pressed | accent를 12% 어둡게 (다크 테마면 12% 밝게) | 자동 |
| color.accent-soft | accent 10% 불투명 | 자동 |
| color.danger | #DC2626 | 고정 |
| color.overlay | rgba(0,0,0,.5) 하나만. 바텀시트·다이얼로그·로딩 전부 동일 | 고정 |
| space.scale | 4 / 8 / 12 / 16 / 24 / 32 / 48 (4 배수만 허용) | 축 2 |
| space.screen-padding | 좌우 16 (spacious 20) | 축 2 |
| space.section | 24 (compact 16, spacious 32) | 축 2 |
| space.card-padding | 16 (compact 12, spacious 20) | 축 2 |
| radius | sm 4 / md 8 / lg 12 / xl 16 / full 9999 | 축 3 |
| shadow | sm 0 1px 2px rgba(0,0,0,.06) / md 0 4px 12px rgba(0,0,0,.08) | 축 3 |
| font.family | "Pretendard", -apple-system, Roboto, sans-serif | 축 5 |
| type.roles | display 28/700 · h1 24/600 · h2 20/600 · h3 17/600 · body 15/400 · body-sm 14/400 · caption 12/400 · label 13/500 (line-height 1.5, 제목 1.3). 본문 최소 14 | 축 5 |
| z.scale | base 0 · sticky 100 · app-bar 200 · tab-bar 200 · overlay 300 · sheet 400 · dialog 500 · snackbar 600 | 고정 |
| motion | 200ms ease-out. 시트 열림 250ms. 이미지 교체 crossfade 150ms | 고정 |
| device.frame | 390×844 기준. 검증 폭 360 / 390 / 430 | 1단계 플랫폼 |
| safe-area | 상단 상태바 44(노치 기기 47) · 하단 홈 인디케이터 34. 콘텐츠·고정 바는 이 안쪽 | 고정 |
| tap.min | 44×44. 인접 탭 영역 간격 최소 8 | 고정 |
| platform | iOS·Android 공통 1벌. 차이(뒤로 가기, 시스템 폰트, 알림 스타일)는 §C 프로젝트 규칙에 메모 | 1단계 플랫폼 |

## B. 컴포넌트 규칙

### B1. 버튼 (이슈: 호버 색상, 상태 구분, 크기)

| 키 | 기본값 |
|---|---|
| button.sizes | sm 36h / px12 / text14 · md 44h / px16 / text15 · lg 52h / px20 / text16 (풀폭 CTA) |
| button.radius | radius.md (축 3 round면 full) |
| button.variants | primary(accent bg, 흰 글자) · secondary(surface-1 bg, text) · ghost(투명, accent 글자) · danger |
| button.states | default · pressed(배경 12% 명도 변화, **글자·아이콘 색 유지**, 절대 검정 전환 없음) · selected(accent-soft bg + accent 1px border) · disabled(opacity .4) · loading(스피너 20, 라벨 숨김, 폭 유지) |
| button.row-rule | 같은 줄의 버튼은 같은 size·radius. 두 개면 secondary 왼쪽, primary 오른쪽 |
| button.text | 한 줄. 넘치면 문구를 줄인다. 줄바꿈 금지 |
| button.primary-per-screen | 화면당 primary 1개. 기본 위치는 **하단 고정 바** (엄지 영역). 2단계 플로우에서 확정 |
| button.duplicate | 같은 동작의 버튼을 앱바와 본문에 이중 배치하지 않는다. 범위가 다르면 라벨에 범위를 쓴다 |

### B2. 아이콘·탭 영역 (이슈: 아이콘 버튼, 커서, 아이콘 의미)

| 키 | 기본값 |
|---|---|
| icon.set | **lucide-react 단일.** 아이콘은 lucide 공식 SVG를 가져와 `Icon/<lucide-name>` 컴포넌트로 만든 것만 쓴다. AI가 벡터를 직접 그리거나 변형·조합해 새 아이콘을 만드는 것 금지. 다른 세트 혼용 금지 |
| icon.allowlist | 프로젝트당 `design/icons.md` 허용 목록 1개. PRD의 액션·상태마다 lucide 이름 1개를 고정. 목록에 없는 아이콘은 쓰지 않는다. 필요하면 목록에 먼저 추가하고 사용자 확인 |
| icon.one-meaning | 의미 1개 = 아이콘 1개. 같은 액션(저장·삭제·공유·닫기·뒤로)에 화면마다 다른 아이콘 금지. 같은 아이콘을 다른 의미로 재사용 금지 |
| icon.size-by-text | 아이콘 크기는 **옆에 붙는 텍스트 역할**이 정한다. caption·label(12~13) → 16 / body·body-sm(14~15) → 20 / h3 이상·앱바·탭바(17+) → 24. 단독 아이콘 버튼은 그 버튼 size의 텍스트 역할을 따른다 (sm→16, md→20, lg→24) |
| icon.sizes | 16 / 20 / 24. 세 값 외 금지. 크기는 `size` 변수 바인딩 |
| icon.stroke | 크기별 고정: 16→1.5 / 20→1.75 / 24→2. lucide 기본 strokeWidth 2를 크기에 맞춰 조정 |
| icon.color | currentColor. 텍스트 색 변수를 그대로 바인딩. 아이콘 전용 색 변수 만들지 않는다 |
| icon.gap | 텍스트와 8px, 수직 중앙 정렬 |
| icon-button.hit | 탭 영역 44×44 정사각. 그림은 icon.sizes. 앱바 아이콘 버튼은 시각 24 / 탭 44 |
| icon-button.name | 아이콘만 있는 버튼은 접근성 라벨 필수. 탭바 아이콘은 텍스트 라벨 동반 |
| icon.state | 버튼 상태 색을 아이콘도 따른다 |
| icon.overflow-menu | 자주 쓰는 액션은 점 세 개 뒤에 숨기지 않는다. 앱바 액션은 최대 2개 노출 |
| icon.proximity | 액션 아이콘은 대상 제목·내용 바로 옆. 목록 행의 액션은 우측 끝 |
| tap.feedback | 탭 가능한 모든 요소에 pressed 시각 반응. 반응 없는 탭 가능 요소 금지 |
| tap.long-press | 롱프레스는 보조 액션에만. 유일한 진입 경로로 쓰지 않는다 |

### B3. 이미지·썸네일 (이슈: 맞춤, 비율, 규격, 제목 배치, 선택 표시, 전환)

| 키 | 기본값 |
|---|---|
| image.fit-by-purpose | 상세·미리보기(전체가 보여야 함) = contain + surface-2 배경 · 목록 카드(채워야 함) = cover, 중심 피사체 잘림은 C단계에서 확인 |
| image.aspect | 컨테이너에 비율 고정. 로딩 전에도 높이 유지 (레이아웃 이동 금지) |
| thumbnail.spec | 프로젝트당 규격 1개: 기본 1:1, 3열 그리드(390에서 폭 (390-32-16)/3 ≈ 114), gap 8, radius.md |
| thumbnail.strip | 가로 스트립일 때 높이 96, 첫 항목 좌측 패딩 16, 마지막 항목 뒤 여백 16 |
| thumbnail.title | 제목 위치 프로젝트당 1개: 기본 **아래** 1줄 말줄임. 옆·위 혼용 금지 |
| thumbnail.pressed | overlay 8% |
| thumbnail.selected | border accent 2px + accent-soft overlay + 체크 배지 20 우상단. pressed와 반드시 구분 |
| thumbnail.selected-visible | 선택 항목이 스크롤 밖이면 가운데로 스크롤. 이미 보이면 스크롤하지 않는다 |
| image.transition | 다음 이미지가 준비될 때까지 이전 이미지 유지, crossfade 150ms. 영역 크기 불변 |
| image.placeholder | 로딩 = surface-2 스켈레톤, 실패 = surface-2 + 아이콘 image-off 24 |

### B4. 텍스트·문구 (이슈: 텍스트 스타일, 줄바꿈, 문구)

| 키 | 기본값 |
|---|---|
| text.role-lock | 같은 역할 = 같은 type.role. 화면마다 임의 크기 금지 |
| text.truncate | 카드 제목 2줄 line-clamp, 목록 제목 1줄, 설명 3줄 |
| text.short-copy | 버튼·짧은 안내는 한 줄. 넘치면 문구를 줄인다 |
| text.long-copy | 긴 안내는 body-sm, 별도 행, 화면 패딩 안에서 자동 줄바꿈 |
| text.scale | 시스템 글자 확대 120%에서도 버튼·탭바가 깨지지 않게 높이 auto |
| copy.user-language | 내부 화면 명칭 금지. "상세 뷰에서 확인" 대신 "이미지를 탭하면 자세히 볼 수 있어요" |
| copy.error | 실패 문구는 이유 + 다시 할 수 있는 조건 |
| copy.i18n | 다국어면 가장 긴 언어 기준으로 폭 검증 |

### B5. 레이아웃·스크롤·고정 요소 (이슈: 여백·정렬, 배경, 반응형, 스크롤, 고정 요소)

| 키 | 기본값 |
|---|---|
| layout.left-edge | 한 화면의 모든 섹션 좌측 시작선 = space.screen-padding |
| layout.section-gap | space.section 하나만 |
| layout.surface-tiers | bg → surface-1(카드·패널) → surface-2(패널 안 요소). 3단 이상 금지 |
| layout.device-widths | 360 / 390 / 430에서 같은 레이아웃. 열 수 고정, 폭만 늘어남 |
| layout.tablet | 기본 미지원. 지원 시 §C에 별도 규칙 |
| layout.thumb-zone | primary CTA·자주 쓰는 액션은 화면 하단 1/3. 앱바 우측 액션은 보조에만 |
| scroll.single | 세로 스크롤 컨테이너 화면당 1개. 중첩 세로 스크롤 금지. 가로 스트립은 허용 |
| scroll.last-item | 스크롤 영역 하단 여백 = 고정 바 높이 + safe-area 하단 + 16 |
| fixed.bottom-cta | 높이 56 + safe-area 34, 배경 bg, 상단 border. 본문 하단 여백 106 |
| fixed.tab-bar | 높이 49 + safe-area 34. 3~5개 탭, 아이콘 24 + 라벨 caption |
| fixed.no-clip | 고정 바·탭바가 마지막 항목·옵션을 가리지 않음을 C단계에서 확인 |
| keyboard | 입력 화면은 키보드 높이(약 300)만큼 본문이 올라오고 primary CTA는 키보드 위에 붙는다 |

### B6. 시트·다이얼로그·앱바·피드백 (이슈: 모달 크기, 툴팁, 레이어 순서)

| 키 | 기본값 |
|---|---|
| sheet.sizes | half(화면 50%) / full(safe-area 상단까지). 상단 그랩바 36×4 |
| sheet.structure | 헤더 56(제목 + 닫기) · 본문 스크롤 · 푸터 CTA 56 + safe-area. 조작부는 푸터에 고정, 본문 아래로 밀리지 않는다 |
| sheet.use | 옵션 선택·필터·부가 입력은 바텀시트. 새 작업 흐름은 풀스크린 푸시 |
| dialog | 확인·경고만. 폭 화면-48, 가운데, 제목 h3 + 본문 body + 버튼 2개(취소 왼쪽) |
| dialog.dismiss | 시트는 오버레이 탭·아래로 드래그로 닫힘. 다이얼로그는 버튼으로만 |
| app-bar | 높이 56. 뒤로(24) · 제목 h3 · 우측 액션 최대 2개 |
| help.inline | 툴팁 없음. 설명은 필드 아래 caption 또는 정보 아이콘 탭 → 바텀시트 |
| snackbar | 하단 고정 바 위 16. 높이 48, 4초, 액션 1개 |
| layer.order | z.scale 준수. 스낵바(600) > 다이얼로그(500) > 시트(400). 시트 위 다이얼로그 허용, 시트 위 시트 금지 |

### B7. 상태 커버리지 (desingissue §1, §9)

| 키 | 기본값 |
|---|---|
| state.required | 모든 화면·목록·카드에 초기 · 빈 · 로딩 · 성공 · 실패 · 비활성 6상태 정의 |
| state.empty | 일러스트 없이 아이콘 48 + 안내 1줄 + primary 버튼 1개, 화면 세로 중앙 |
| state.loading | 스켈레톤(surface-2). 배경색은 성공 상태와 동일. 풀스크린 스피너 금지 |
| state.error | 이유 + 재시도 버튼. 네트워크 오류는 스낵바로 |
| state.offline | 앱바 아래 배너 1줄 |
| data.range | 제목 짧음/김, 이미지 세로/가로/정사각, 항목 0/1/많음, 글자 확대 120% — 이 조합으로 C단계 검증 |
| data.ownership | 상세·정보 시트는 현재 선택 대상의 정보만 표시 |

### B8. 변경 범위 (desingissue §4, §6, §7)

figma-builder와 fix 단계에 적용되는 행동 규칙.

| 키 | 규칙 |
|---|---|
| change.scope | 요청된 결함만 고친다. 기본 상태 변경 ≠ 조작 제거. 닫기·취소·뒤로·재선택은 유지 |
| change.relation | 위치 요청은 대상·기준·순서로 확인된 문장만 실행 |
| change.propagate | 컴포넌트를 고치면 그 인스턴스가 있는 모든 화면을 다시 스크린샷 |
| change.no-dup | 새 공통 요소 추가 전 같은 액션이 이미 있는지 확인 |

## C. 검수 목록 (design-auditor C단계 기준, desingissue.md를 모바일로 옮김)

- [ ] 버튼과 아이콘이 기본·눌림·선택·비활성·로딩 상태에서 의도대로 보인다.
- [ ] 아이콘의 크기·선 두께·정렬이 일관되고, 탭 영역이 44 이상이며 의미를 알 수 있다.
- [ ] 이미지의 비율과 잘림 방식이 영역의 목적에 맞는다.
- [ ] 썸네일의 규격·제목 위치·선택 표시가 일관되고 선택 항목이 보인다.
- [ ] 문구가 길어지거나 글자를 확대해도 버튼·탭바·레이아웃이 깨지지 않는다.
- [ ] 360 폭에서도 마지막 옵션과 주요 버튼에 접근할 수 있다.
- [ ] 고정 바·탭바·시트·스낵바가 다른 콘텐츠를 가리거나 세이프 에어리어를 침범하지 않는다.
- [ ] 닫기·취소·뒤로·다시 선택 등 기존 조작이 의도치 않게 사라지지 않았다.
- [ ] 같은 역할의 다른 화면에도 변경이 반영되고 액션이 중복되지 않는다.
- [ ] 초기·빈 상태·로딩·실패 상태와 이미지 전환도 확인했다.
- [ ] 상세·정보 시트의 내용이 현재 선택한 대상과 일치한다.
- [ ] 안내문과 도움말이 현재 화면의 명칭·행동 순서를 설명한다.
- [ ] primary CTA가 엄지 영역(하단 1/3)에 있고 화면당 1개다.
