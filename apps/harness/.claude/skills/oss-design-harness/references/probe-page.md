# 시안 페이지 만들기 — 공통 규격

취향 시안(3단계), 따라가 보기 투어(2단계), 레퍼런스(3단계), 규칙 미리보기(4단계)를 사용자에게 보여주는 HTML 페이지 규격. 네 종류 모두 같은 규칙을 따른다. 대상은 디자인 초보자다.

## 배포 방식

1. HTML 파일을 `design/probes/<단계>-<이름>.html`로 쓴다 (probe-renderer). **여기서 배포하지 않는다.**
2. 메인 대화가 `design/probes/hub.json`에 탭을 추가하고 `python3 scripts/build_hub.py` → `design/probes/hub.html`을 **같은 URL로** 재배포한다. `capabilities: {db: {}}` 필수. 사용자에게 주는 링크는 항상 허브 하나. 허브 헤더가 "안 본 탭 / 저장 없는 탭"을 보여준다.
3. 반응은 **페이지 안 의견 패널**로 받는다. 사용자가 저장하면 메인 대화가 `read_db`로 읽는다. 터미널 질문은 의견이 0건일 때만.

## 필수 규칙

- **번호 라벨은 영역 단위, 화면당 최대 5개.** ①②③ 원형 배지, 좌상단. 버튼마다 번호를 붙이지 않는다. 시안 A/B/C가 나란히 있으면 같은 위치 같은 번호.
- **한 번에 하나.** 화면 열몇 장을 가로로 늘어놓지 않는다. 투어(장면 넘기기)나 축 하나씩. 비교가 목적인 taste만 A/B/C 3개를 나란히. 예외: 최종 미리보기의 상태 스트립(검증용 실물 프레임, `overflow-x:auto` 컨테이너 안에서만 가로 스크롤).
- **회색 박스 와이어프레임 금지.** 중립 팔레트(배경 #F7F8FA, 카드 흰색, 글자 #1F2937/#6B7280) + 강조색 1개(#2F6BFF)로 그린다. 취향과 무관한 페이지도 "진짜 앱처럼" 보여야 초보자가 읽는다.
- **배치 템플릿 고정.** 상태바 44 / 상단 바 56 / 본문 / 하단 CTA 52 / 홈 인디케이터 34. 리스트 행 56, 카드 패딩 16, 라운드 12. 모든 KIND가 같은 템플릿을 쓴다.
- **상태를 보여준다.** 버튼이 있는 화면은 "누르면 이렇게 돼요" 칩과 상태 세그먼트(기본·눌렀을 때·로딩·성공·실패·비어있음·비활성).
- **추천 1개 + 라이트 패널.** 비교 단위마다 스킬이 추천을 정해 "추천" 리본과 이유 한 줄을 붙인다. **taste**: 추천은 리본·박스 없이 h2 아래 텍스트 한 줄("추천: B — 이유"). 선택은 **폰 화면을 직접 눌러서**(눌린 화면 테두리, 즉시 저장). A/B/C 버튼·"추천대로"·"다르게" 버튼·세부 의견 칸(싫은 것·번호·이유) 전부 없음. **flow/reference/rules**: "괜찮아요 👍"(즉시 저장) + 필요한 최소 칩·이유 입력이 항상 보임. "다르게 할래요" 버튼은 어느 KIND에도 없다. 저장 방식은 `.claude/agents/probe-renderer.md` §의견 패널.
- **외부 의존 없음.** 인라인 CSS/JS. 폰트는 시스템 폰트 스택 + Google Fonts만.
- **더미 콘텐츠는 PRD 도메인 언어.** brief.md의 등장 인물·날짜를 그대로. 이미지 자리는 색 블록 + 비율 텍스트.
- **390×844 폰 프레임.** 데스크톱 1280 폭 기준, 좁으면 세로 쌓기. 가로 스크롤 금지.
- **설명용 안내·범례 문구를 넣지 않는다.** 제목 아래 한 줄(무엇을 보는 페이지인지)만. "파란 테두리 = …", "번호로 말씀해 주세요" 같은 문장은 소음이다.

## 투어 페이지 (flow)

`lofi-flow.md` 전문 참고. 한 번에 폰 하나 + 오른쪽 5칸(지금 상황 / 화면 구성 / 누르면 이렇게 돼요 / 시선 흐름 / 의견).

## 취향 시안 페이지 (taste)

```
<h1>취향 시안 — 축 1·2</h1>
<section data-axis="1">
  <h2>축 1 밝기·색온도  <small>이 축만 다르고 나머지는 같습니다</small></h2>
  <div class="row">
    <figure class="variant" data-v="A"> [대표 화면, 투어 템플릿 그대로, 영역 라벨 ≤5] <figcaption>A</figcaption></figure>
    <figure class="variant" data-v="B"> … </figure>
    <figure class="variant" data-v="C"> … </figure>
  </div>
  [선택은 폰 화면(figure)을 직접 눌러서. 눌린 화면에 accent 테두리, 즉시 저장. 세부 의견 칸(싫은 것·번호 칩·이유) 없음]
</section>
<section data-axis="2"> … </section>
```

한 페이지에 축 2개까지. 5축이면 페이지 3장(1·2 / 3·4 / 5·추가축). db 경로 `feedback/axis-<n>`.

## 레퍼런스 페이지 (reference)

앱당 섹션 1개: 이름·스토어 링크·선정 이유 한 줄 → 스크린샷 2~4장 폰 프레임 안에 가로 → 컴포넌트 번호 오버레이 최대 5개 → 의견 패널(가져오고 싶은 번호 / 싫은 번호 / 이유). db 경로 `feedback/app-<영문이름>`.

## 규칙 미리보기 페이지 (rules)

`design/design-rules.md`의 값을 CSS 변수로 그대로 옮겨서 그린다. 섹션 순서:

1. 색 토큰 스와치 (bg / surface-1 / surface-2 / text / text-muted / border / accent / accent-pressed / danger)
2. 타이포 역할표 (display / h1 / h2 / h3 / body / body-sm / caption / label) 실제 크기로
3. 버튼: primary / secondary / ghost / danger × sm / md / lg × default / pressed / selected / disabled / loading. 탭 영역 44 최소를 반투명 박스로
4. 아이콘 버튼 3사이즈 + 텍스트 옆 아이콘 정렬
5. 썸네일 그리드: 기본 / pressed / selected. 3열 그리드와 가로 스트립
6. 카드 + 긴 제목 2줄 말줄임
7. 입력·셀렉트 + 에러 상태
8. 바텀시트(1/2, 풀) + 다이얼로그 + 하단 고정 CTA 바 + 세이프 에어리어
9. 탭바(활성/비활성) + 상단 앱바 + 스낵바·토스트
10. 빈 상태 / 로딩(스켈레톤) / 실패 상태 카드
11. 기기 폭: 360 / 390 / 430 나란히 + 글자 확대 120% 상태 1개

섹션마다 의견 패널(db 경로 `feedback/section-<n>`). 이 페이지가 최종 산출물의 컴포넌트 목록이다(Figma 생성 시 figma-builder가 만들 목록과 1:1). 아래 마크업 계약을 지킨다.

## 마크업 계약 (rules·preview — 5단계 최종 산출물)

규칙 미리보기와 최종 미리보기는 사용자에게 보여주는 시안이면서 **최종 HTML 산출물**이다. `scripts/html_audit.py`가 아래 속성으로 정적·렌더 검사를 하므로, 속성이 없으면 검사 실패다. 인터뷰용 시안(structure·flow·reference·taste·icons)에는 적용하지 않는다. 이름·값의 기준은 `scripts/README.md` §마크업 계약·§토큰 이름이다.

```html
<style>        /* 프레임·컴포넌트 CSS — var(--…)만 */ </style>
<style data-chrome>  /* 프레임 밖 페이지 UI(의견 패널·요약 카드·번호 라벨) — 리터럴 허용 */ </style>

<section data-screen="<slug>" data-screen-name="<화면명>">
  <div class="phone" data-state="default" data-width="390">
    <header data-component="AppBar">
      <button data-tap><i data-icon="<lucide 이름>"><svg … stroke="currentColor"></svg></i></button>
    </header>
    <main data-scroll>
      <article data-component="Card"><h3 data-truncate="2">…</h3></article>
    </main>
    <div data-component="BottomCTA" data-fixed="cta">
      <button data-tap data-primary>…</button>
      <div data-safe-area></div>
    </div>
  </div>
  <div class="state-strip">   <!-- overflow-x:auto -->
    <div class="phone" data-state="empty" data-width="390">…</div>
    …
  </div>
</section>
```

| 속성 | 붙이는 곳 | 값 | 검사 규칙 |
|---|---|---|---|
| `data-screen` · `data-screen-name` | 화면 `<section>` | screens.md의 slug · 화면명과 같게 | component.manifest, state.frames |
| `data-state` | `.phone` | `default` · `empty` · `loading` · `error` · `long-title` · `many-items` · `text-120`(7종 필수) + `keyboard`(FormField 화면) · `guest-name`(웹 예외 화면) · 필요 시 `many-items-scroll` · `default-scroll`. 같은 화면·상태·폭 프레임은 1개 | state.frames, 스크린샷 파일명 `<slug>-<state>[@<width>].png` |
| `data-width` | `.phone` | `390`(생략 시 390), 검증용 `360` · `430`. state.frames는 390 프레임만 센다 | frame.size |
| `data-component` | 컴포넌트 루트 요소 | screens.md 구성 열 이름 그대로(규칙 미리보기는 견본 이름). default 프레임의 **최상위** 집합 = 구성표. 컴포넌트 안 부품은 중첩 `data-component`로 둬도 된다(대조 제외) | component.manifest |
| `data-tap` | 탭 가능한 요소 전부(버튼·아이콘 버튼·리스트 행·탭·칩) | 값 없음 | tap.min, tap.gap |
| `data-tap-group` | 탭바·세그먼트처럼 칸이 붙은 `data-tap` 묶음의 부모 | 값 없음. `tap.gap` 면제(`tap.min`은 그대로) | tap.gap |
| `data-primary` | primary 버튼 | 값 없음. **default 프레임에 정확히 1개** | button.primary-per-screen |
| `data-primary-exempt` | primary 예외 화면의 `<section>`(또는 default 프레임) | 값 = design-rules §C(프로젝트 전용 규칙) 키 (예: `web.primary`). 빈 값·§C 에 없는 키는 실패. primary 0~1개 허용 | button.primary-per-screen |
| `data-fixed` | 하단 CTA 바 · 탭바 | `cta` · `tabbar` | fixed.no-clip, safe-area |
| `data-safe-area` | 홈 인디케이터 영역(고정 바 안, 또는 바로 아래 형제) | 값 없음. 높이 ≥ 34 | safe-area |
| `data-scroll` | 세로 스크롤 본문(화면당 1개). 고정 바가 있는 default·many-items(-scroll) 프레임엔 필수 | 값 없음 | fixed.no-clip |
| `data-truncate` | 말줄임 텍스트 | `1`(ellipsis+nowrap+overflow:hidden 또는 line-clamp 1) · `2` · `3`(`-webkit-line-clamp` 같은 값). 말줄임이 걸리는데 속성이 없으면 실패 | text.clip |
| `data-icon` | 아이콘 SVG 래퍼 `<i data-icon="…"><svg stroke="currentColor">` | icons.md의 lucide 이름. 프레임 안에서 래퍼 없는 `<svg>` = 직접 그린 아이콘(실패) | icon.allowlist |

**스타일 두 갈래.**
- 일반 `<style>`: 프레임·컴포넌트 CSS. 색·간격·radius·그림자·글꼴은 전부 `var(--…)`(token.bound). 예외는 `0`·`1px`, `url(#id)`, `text-120` 프레임 안 font-size.
- `<style data-chrome>`: 프레임 밖 페이지 UI(의견 패널·요약 카드·번호 라벨·상태 스트립 등). 여기 리터럴은 token.bound에서 제외된다. 단, **크롬 CSS가 `.phone` 크기를 바꾸면 안 된다**(아래 렌더 뷰포트).

**토큰 이름** (design-rules §A 키 → `:root` CSS 변수. 값은 문서와 같아야 한다 — token.defined)

| §A 키 | CSS 변수 |
|---|---|
| `color.<n>` | `--color-<n>` |
| `space.scale` | `--space-4` … `--space-48` (값 이름. Figma 변수 `space/<값>`과 같다) |
| `space.<n>` | `--space-<n>` (예: `--space-screen-padding`, `--space-section`) |
| `radius` | `--radius-sm` · `--radius-md` · `--radius-lg` · `--radius-xl` · `--radius-full` |
| `shadow` | `--shadow-sm` · `--shadow-md` |
| `font.family` | `--font-family` |
| `type.roles` | `--type-<역할>`(크기) · `--type-<역할>-weight` · `--type-line-height` · `--type-line-height-title` |

웹 예외 화면이 부모 웹 스타일을 따르면 `--web-*`를 추가로 쓴다. 그 밖의 변수(`--z-*`, `--motion`, `--frame-w` …)는 자유.

**렌더 뷰포트.** `html_audit.py --render` 기본(`--viewport page`)은 **1280 폭 페이지**에 한 번 배치하고, `.phone`은 `data-width` × 844 크기 그대로 **1:1**로 둔다. 크롬 CSS(미디어 쿼리 포함, 예: `@media (max-width:440px){.phone{width:100%}}`)나 transform이 `.phone` 크기를 바꾸면 `frame.size`에서 실패한다. 프레임 안 폭별 반응형은 미디어 쿼리 대신 `[data-width="360"]` 선택자로 쓴다. `--viewport device`(data-width별 뷰포트로 측정)는 선택이다.

- **상태 프레임**: 화면마다 7종(default·empty·loading·error·long-title·many-items·text-120) 필수, FormField 화면은 +`keyboard`, 웹 예외 화면은 +`guest-name`. 각각 별도 `.phone`, 전부 실물 크기. 썸네일·축소 금지. screens.md 상태 열에도 같은 목록을 전부 적는다.
- **번호 라벨**: `data-label`을 가진 별도 배지 요소로만 붙이고(스타일은 `<style data-chrome>`), 컴포넌트 요소에 글자로 섞지 않는다. default 프레임에만.
- **외부 의존·자리표시 금지**: 외부 `<script src>`·`<link href>`·`<img src>`·CSS `url()`/`@import` 0개(fonts.googleapis.com·fonts.gstatic.com만 허용, no-external), lorem ipsum 0개(no-lorem).
