# hyper-design — PRD 한 장으로 모바일 앱 디자인

Claude Code 플러그인. PRD(기획 문서)를 주면 모바일 앱 HTML 화면들과 한눈에 보는 캔버스를 만든다.

## 설치

Claude Code에서:
```
/plugin marketplace add vmc-inner-circle/hyper-design
/plugin install hyper-design@hyper-design
```
로컬에서 바로 써 보려면: `claude --plugin-dir <이 저장소>/plugins/hyper-design`

## 명령

| 명령 | 하는 일 | 시간 |
|---|---|---|
| `/hyper-design:go <PRD>` | 1차 — 사용자가 만들거나 신청하는 모든 대상의 **시작 → 보기 → 고치기 → 끝(결과)** 화면, 실제 사진, 색 팔레트 3벌(원클릭 전환), 캔버스. 그 자체로 완성품 | 약 15분 |
| `/hyper-design:max` | 2차 — 1차 위에 오류·확인 대화상자·빈 화면·진행 중 같은 상태 화면을 더한다. `out/`에 1차가 없으면 1차부터 이어서 한다 | 1차 위에 약 10분 |

PRD만 붙여넣고 "화면 만들어줘"라고 해도 `go`가 실행된다. PRD 요구사항을 빼거나 가볍게 바꿔야 할 때만 만들기 전에 한 번 확인을 묻는다.

## 결과물 (`out/`)

- `index.html` — 캔버스: Screens(흐름별 줄, 갈래 화살표, 화면별 정책) · Foundation(색·글자·여백) · Components(쓰인 부품) 탭, 드래그 이동·확대, 화면 누르면 크게 보기, 색 점으로 팔레트 전환
- `screens/*.html` — 화면 파일(토큰·부품 클래스만 사용)
- `journey.md`(여정표·사실 표·가정 로그) · `decisions.json`(정한 것·뺀 것) · `spec_inventory.json`(명세 목록·흐름 고리) · `credits.json`(사진 출처)

## 구조

```
plugins/hyper-design/
  skills/go/SKILL.md     # 1차
  skills/max/SKILL.md    # 2차
  core/                  # 공용 — foundation(토큰·부품·팔레트·시드), scripts(검사·캔버스·이미지 검색), references(원칙·체크리스트·명세·이미지)
```
