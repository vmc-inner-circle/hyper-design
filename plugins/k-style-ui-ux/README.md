# k-style-ui-ux — PRD 한 장으로 모바일 앱 디자인

Claude Code·Codex·Cursor 플러그인. PRD(기획 문서)를 주면 모바일 앱 HTML 화면들과 한눈에 보는 캔버스를 만든다.

## 설치

Claude Code에서:
```
/plugin marketplace add vmc-inner-circle/k-style-ui-ux
/plugin install k-style-ui-ux@k-style-ui-ux
```
로컬에서 바로 써 보려면: `claude --plugin-dir <이 저장소>/plugins/k-style-ui-ux`

Codex에서:
```
codex plugin marketplace add vmc-inner-circle/k-style-ui-ux
codex plugin add k-style-ui-ux@k-style-ui-ux
```

Cursor에서: **Customize → Plugins**에서 GitHub 저장소로 가져오기(From GitHub Repository)에 `https://github.com/vmc-inner-circle/k-style-ui-ux`를 넣고 `k-style-ui-ux`를 설치한다(저장소 루트의 `.cursor-plugin/marketplace.json`을 읽는다).
로컬에서 바로 써 보려면 `plugins/k-style-ui-ux` 폴더를 `~/.cursor/plugins/local/k-style-ui-ux`로 복사하고 창을 다시 불러온다(심볼릭 링크는 읽지 않는다).
업데이트: Claude Code `/plugin marketplace update k-style-ui-ux`, Codex `codex plugin marketplace upgrade k-style-ui-ux`.

## 명령

Claude Code는 `/k-style-ui-ux:go`·`/k-style-ui-ux:max`, Codex는 `$k-style-ui-ux:go`·`$k-style-ui-ux:max`, Cursor는 채팅에 `/`를 치고 `go`·`max`로 부른다(아래 표는 Claude Code 표기).

| 명령 | 하는 일 | 시간 |
|---|---|---|
| `/k-style-ui-ux:go <PRD>` | 1차 — 같은 문제를 푸는 잘 되는 앱들의 흐름(시장 관례)을 기본값으로, 사용자가 만들거나 신청하는 모든 대상의 **시작 → 보기 → 고치기 → 끝(결과)** 화면, 실제 사진, 색 팔레트 3벌(원클릭 전환), 캔버스. 그 자체로 완성품 | 약 15분 |
| `/k-style-ui-ux:max` | 2차 — 1차 위에 오류·확인 대화상자·빈 화면·진행 중 같은 상태 화면을 더한다. `out/`에 1차가 없으면 1차부터 이어서 한다 | 1차 위에 약 10분 |

PRD만 붙여넣고 "화면 만들어줘"라고 해도 `go`가 실행된다. PRD 요구사항을 빼거나 가볍게 바꿔야 할 때만 만들기 전에 한 번 확인을 묻는다.

## 결과물 (`out/`)

- `index.html` — 캔버스: Screens(흐름별 줄, 갈래 화살표, 화면별 정책) · Foundation(색·글자·여백) · Components(쓰인 부품) 탭, 드래그 이동·확대, 화면 누르면 크게 보기, 색 점으로 팔레트 전환
- `screens/*.html` — 화면 파일(토큰·부품 클래스만 사용)
- `conventions.json`(시장 관례: 따를 것·참고할 후킹 장치·리뷰 불만) · `market/`(잘 되는 앱 5개의 스토어 화면 시트·설명·리뷰)
- `journey.md`(여정표·사실 표·가정 로그) · `decisions.json`(정한 것·뺀 것) · `spec_inventory.json`(명세 목록·흐름 고리) · `credits.json`(사진 출처)

## 시장 관례

화면을 정하기 전에 PRD의 키워드로 App Store에서 같은 문제를 푸는 앱 중 평점 수 상위 5개를 모은다(`core/scripts/market.py`, 2초 안팎). 해석 에이전트 1개가 스토어 화면·리뷰에서 **2개 이상 앱이 하는 것**만 관례로 뽑는다(약 1~2분, 여정표 작성과 겹쳐 돈다). 온보딩·탭·홈 첫 블록·결제 흐름은 관례를 따르고, 벗어나면 이유를 남긴다. 후킹 장치는 후보일 뿐이고, 이 앱의 차별점은 리서치가 바꾸지 못한다. 도메인별 정리본은 두지 않는다 — 매번 이 PRD의 말로 새로 모은다. 자세히: `core/references/market.md`

## 구조

폴더 하나를 Claude Code·Codex·Cursor가 함께 설치한다 — 사본·빌드 없음.

```
plugins/k-style-ui-ux/
  .claude-plugin/plugin.json   # Claude Code manifest
  .codex-plugin/plugin.json    # Codex manifest
  .cursor-plugin/plugin.json   # Cursor manifest
  plugin.json                  # Agent Plugins 1.0 manifest(최신 Codex가 먼저 읽는다)
  skills/go/SKILL.md           # 1차
  skills/max/SKILL.md          # 2차
  skills/*/agents/openai.yaml  # Codex 표시 이름·기본 프롬프트(Claude는 무시)
  core/                        # 공용 — foundation(토큰·부품·팔레트·시드), scripts(검사·캔버스·이미지 검색), references(원칙·체크리스트·명세·이미지)
```

마켓 파일: `.claude-plugin/marketplace.json`(Claude) · `.agents/plugins/marketplace.json`(Codex) · `.cursor-plugin/marketplace.json`(Cursor) — 모두 이 폴더를 가리킨다. 버전을 올릴 때는 manifest 4개와 `CHANGELOG.md` 맨 위를 함께 바꾼다 — PR마다 CI(`ci/verify.py`)가 어긋남을 잡는다.
