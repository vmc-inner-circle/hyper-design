# 최종 미리보기 탭 — 5단계 HTML 산출물(화면)

4단계 규칙이 확정(`status: confirmed`)된 직후 허브 마지막 탭 "최종 미리보기"를 만든다. brief.md의 모든 화면을 확정된 토큰·컴포넌트·아이콘으로 HTML로 그린 것이다. **이 탭(화면)과 규칙 미리보기 탭(토큰·컴포넌트)이 하네스의 최종 산출물이다.** 사용자가 여기서 "이대로 확정해 주세요"를 눌러야 html_audit 게이트로 간다. Figma는 사용자가 "Figma 생성"을 지시할 때만 이 HTML을 입력으로 만든다.

목적 세 가지. ① 방향 오류를 사용자 눈으로 잡는다. ② 화면 구성(어떤 컴포넌트가 어느 순서로 들어가는지)을 사용자가 **지정·삭제**할 수 있는 마지막 자리다. ③ `html_audit.py`·design-auditor가 검증할 **실물**이다 — 모든 상태 프레임을 실물 크기로 담는다.

## 위치

- 허브 탭 순서: 구조 → 따라가 보기 → 레퍼런스 → 취향(색상/모양·간격/글자) → 아이콘 → 규칙 미리보기 → **최종 미리보기**
- hub.json: `{"file":"final-preview.html","title":"최종 미리보기","prefix":"screen-","stage":"5단계"}`
- 페이즈 게이트: `check_phase.py --phase rules` 통과 → 최종 미리보기 탭 생성(렌더러 배포 전 검사: `check_phase --phase probes` + `html_audit.py` 정적) → 사용자 "이대로 확정해 주세요" → `html_audit.py` 정적 → `--render` → design-auditor(6단계)

## 입력 (probe-renderer KIND=preview)

- `design/brief.md` §1 화면 목록 (화면·목적·진입·primary 액션), §2 시나리오 (화면 순서, 상태)
- `design/design-rules.md` — 모든 값을 `:root` CSS 변수로. 하드코딩 금지
- `design/icons.md` — 허용 목록의 lucide SVG만 인라인
- `design/decisions.md` — 축별 선택값(미리보기 상단에 "이렇게 정했어요" 요약 6줄)
- `design/screens.md` (있으면) — 화면별 컴포넌트 구성표. 없으면 렌더러가 만들고 반환에 포함

## 페이지 구성

1. 상단 요약 카드: 결정된 스타일 6줄(밝기, 밀도, 형태, 강조색, 글꼴, 탭바 유무)과 "이 화면들이 최종 결과물이에요. 확정하면 자동 검사를 거쳐 마무리됩니다" 한 줄.
2. 화면당 `<section data-screen="<slug>" data-screen-name="<화면명>">` 1개, brief §1 순서. 왼쪽 띠(다른 탭과 동일): 화면 번호·이름, "괜찮아요 👍 / 고칠 게 있어요 🤔", 저장.
   - `.phone[data-state="default"]` 390×844 안에 default 상태를 완성도 있게 그린다. 실제 더미 데이터(brief 도메인 언어), 앱바·탭바·하단 CTA·세이프 에어리어 포함.
   - 오른쪽에 **화면 구성표**: 위에서 아래 순서로 컴포넌트 행 (예: `AppBar` 제목 / `Card` 목록 n개 / `BottomCTA` primary 액션 — 이름·문구는 brief.md에서만 가져온다). 각 행에 원문자 번호가 있고 default 폰의 같은 영역에 같은 번호 라벨. 화면당 최대 5개. 번호 라벨은 default에만.
   - 그 아래 **상태 스트립**: 상태마다 별도 `.phone[data-state]`를 **실물 크기(390×844)**로 가로 스크롤(`overflow-x:auto` 컨테이너 안에서만. 페이지 자체는 가로 스크롤 없음). 순서 `empty` · `loading` · `error` · `long-title` · `many-items` · `text-120`, 입력 화면이면 `keyboard`, 웹 예외 화면이면 `guest-name`. 프레임 위 캡션 한 단어(비어 있을 때 / 불러오는 중 / 실패 / 긴 제목 / 항목 많음 / 글자 120% / 키보드 / 이름 입력). 썸네일로 줄이지 않는다.
   - 대표 화면 1개(가장 빽빽한 화면)는 default를 `data-width="360"`·`"430"`으로 한 장씩 더 그린다.
3. **마크업 계약**(`probe-page.md` §마크업 계약) 전부 적용: `data-component`(구성표 이름 그대로) · `data-tap` · `data-primary`(default 프레임에 1개, 예외 화면은 `<section>`에 `data-primary-exempt`) · `data-fixed` · `data-scroll` · `data-truncate` · `data-icon` · `:root` 토큰만. 상태 프레임도 default와 같은 규칙.
4. "고칠 게 있어요"를 눌렀을 때만 펼침:
   - 구성표 행마다 **"빼요" 체크**와 **"다른 걸로" 드롭다운**(규칙 미리보기의 컴포넌트 목록에서 같은 종류만: 카드↔리스트 행, 바텀CTA↔앱바 액션 등)
   - 번호 칩 토글 + 자유 입력
5. 페이지 끝 "전체 의견" + **"이대로 확정해 주세요"** 버튼 1개 (전 화면 👍이면 활성). 누르면 `feedback/preview-go` 저장.

## 저장 스키마

```
feedback/screen-<slug>   {unit:"screen", n:<순번>, label:<화면명>, reaction:"ok"|"fix",
                          remove:[<구성표 행 id>], swap:{<행 id>:<컴포넌트명>},
                          marks:["③"], markNames:[...], text, updatedAt}
feedback/preview-go      {unit:"preview", n:0, label:"HTML 확정", text:"go", updatedAt}
feedback/preview-overall {unit:"overall", ...}
```

`preview-go`는 **HTML 산출물 확정**이다. Figma 생성 요청이 아니다.

## read_db → 다음 단계

- `preview-go`가 있고 모든 `screen-*`가 `ok` → `design/screens.md`를 확정본으로 저장(구성표 그대로) → `html_audit.py --design-dir design` 정적 → `--render --fix-list design/html-fix-list.md --screenshots design/screenshots/html`. 실패하면 html-fix-list.md를 probe-renderer `KIND=fix`에 넘기고 재검. 통과하면 design-auditor(6단계).
- `fix`가 있는 화면: `remove`·`swap`을 screens.md에 반영하고 그 화면만 다시 그려 같은 URL로 재배포. 2회까지. 3회째면 방향 오류로 보고 3단계 해당 축을 재확인.
- `remove`된 컴포넌트는 HTML에서 빠진다. `html_audit`의 `component.manifest` 검사(screens.md 밖 `data-component` 0개, 빠진 행 0개)로 확인한다. Figma 생성 시에는 `figma_parity`가 같은 표로 대조한다.
- 의견 0건이면 터미널로 "화면 n개 중 고칠 것이 있나요? (없음 / 번호)" 1회.

## design/screens.md 형식

```
# Screens

| 순번 | 화면 | slug | 구성 (위→아래) | 상태 프레임 |
|---|---|---|---|---|
| 1 | <화면명> | <slug> | ① AppBar(제목) · ② Card×n · ③ BottomCTA(primary 액션) · ④ TabBar | default·empty·loading·error·long-title·many-items·text-120 (+keyboard) (+guest-name) |
```

최종 HTML은 이 표의 구성 열 이름을 `data-component`로, slug를 `data-screen`으로, 상태 프레임 열을 `data-state`로 그대로 쓴다. figma-builder도 이 표의 구성 열만 보고 인스턴스를 배치한다. 표에 없는 컴포넌트가 필요하면 만들지 않고 build-log에 "누락 구성"으로 남긴다.

## 하지 않는 것

- 인터랙션(탭 전환, 시트 열림)은 넣지 않는다. 정적 화면. 흐름은 2단계 투어가 이미 담당했다. 상태는 인터랙션 대신 상태 스트립의 별도 프레임으로 보여준다.
- 규칙 값을 미리보기에서 바꾸지 않는다. 규칙 수정은 규칙 미리보기 탭으로 돌아간다.
- 화면을 새로 추가하지 않는다. 화면 추가는 1단계 구조 탭에서 한다.
