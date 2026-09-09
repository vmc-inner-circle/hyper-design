# 1단계 구조 — 설문 탭 (허브 첫 탭)

1단계(PRD 확정)는 터미널 질문이 아니라 **허브 Artifact의 첫 탭 "1단계 구조"**에서 설문지처럼 진행한다. 스킬이 PRD에서 뽑을 수 있는 것은 전부 미리 채우고, 정말 빈 칸만 질문으로 노출한다. 터미널 질문은 저장된 의견이 0건일 때의 폴백이다.

## 흐름

1. 스킬이 PRD를 읽어 화면 인벤토리 표를 만든다 (interview-rules.md §1). 빈 칸을 세고 아래 질문 목록에서 **PRD에 답이 없는 것만** 고른다. 상한 8개.
2. `probe-renderer`에 `KIND=structure OUT=design/probes/structure.html`로 위임한다. 렌더러는 `templates/structure-survey.html`을 복사해 상단 `SURVEY` 데이터 블록만 채운다. 나머지 HTML·JS는 손대지 않는다.
3. 메인 대화가 hub.json 첫 탭에 `{"file":"structure.html","title":"1단계 구조","prefix":"structure-","stage":"1단계 구조"}`를 추가하고 `build_hub.py` → 같은 URL로 재배포.
4. 사용자가 "다 봤어"라고 하면 `Artifact(action:"read_db", db_op:"list", collection:"feedback")`로 읽어 `structure-1`, `structure-2`, `structure-overall`을 brief.md에 옮긴다.
5. `python3 scripts/check_phase.py --phase structure` 통과 후 2단계.

## 질문 목록 (PRD에 답이 없을 때만 노출)

| id | 질문 | 선택지 (첫 번째가 추천) | brief.md 반영 |
|---|---|---|---|
| entry | 앱을 열면 맨 처음 무엇이 보이나요? | 바로 메인 화면 / 로그인 먼저 / 온보딩 몇 장 먼저 | §1 진입 경로 |
| core | 가장 자주 반복하는 행동 하나는? | PRD에서 추출한 후보 2~3개 | §2 시나리오 1 |
| platform | 어떤 기기용인가요? | iOS와 Android 둘 다 / iOS만 / Android만 | 플랫폼 |
| tablet | 태블릿이나 가로 화면도 지원하나요? | 아니오, 폰 세로만 / 예 | 태블릿·가로 모드 |
| tabbar | 하단에 탭(홈·검색·내 정보 같은)이 필요한가요? | 예, n개 (PRD 화면 수로 추천) / 아니오, 한 흐름만 | 하단 탭바 |
| empty | 아직 데이터가 하나도 없을 때 무엇을 보여줄까요? | 안내 한 줄 + 첫 행동 버튼 / 샘플 데이터 미리 보여주기 / 아무것도 안 보여줌 | §5 가정 → state.empty |
| data | 제목·이름은 얼마나 길어질 수 있나요? 항목은 몇 개까지? | 짧음(한 줄)·수십 개 / 길어질 수 있음·수백 개 / 모르겠음 | §5 가정 → text.truncate, data.range |
| lang | 언어는 하나인가요? | 한국어만 / 한국어 + 영어 / 셋 이상 | 다국어 |

렌더러는 PRD로 이미 확정된 질문을 **넣지 않는다.** 확정된 값은 "이미 정해진 것" 목록에 읽기 전용으로 보여준다.

## 페이지 구성 (templates/structure-survey.html)

두 단위. 각 단위는 다른 탭과 같은 왼쪽 띠(추천대로 / 다르게 / 저장)를 가진다.

| 단위 | 내용 | "추천대로" 의미 | "다르게" 펼침 |
|---|---|---|---|
| 1 화면 목록 | 표: 화면 / 무슨 화면인지 / 어떻게 들어가는지 / 가장 중요한 버튼. 행마다 체크 "이 화면은 빼도 돼요" | 표 그대로 확정 | 행별 체크 + "빠진 화면·고칠 점" 자유 입력 |
| 2 빈 칸 질문 | 질문 1~8개, 라디오형, 추천이 미리 선택됨 | 모든 질문을 추천값으로 저장 | 질문별 다른 값 선택 + 자유 입력 |

페이지 끝 "전체 의견" 1개. 화면 목록 표에는 번호 라벨을 붙이지 않는다 (가리킬 시각 요소가 없다).

## 저장 스키마 (feedback 컬렉션)

```
feedback/structure-1  {unit:"structure", n:1, label:"화면 목록",
                       best:null, worst:null, marks:[<빼도 되는 화면 id>], markNames:[<화면명>],
                       text:"추천대로" | 자유 입력, updatedAt}
feedback/structure-2  {unit:"structure", n:2, label:"빈 칸 질문",
                       answers:{entry:"main", core:"...", platform:"both", ...},   // 질문 id → 선택지 value
                       best:null, worst:null, marks:[], markNames:[],
                       text:"추천대로" | 자유 입력, updatedAt}
feedback/structure-overall {unit:"overall", n:0, label:"전체", text, updatedAt}
```

기존 본문 스키마에 `answers` 필드 하나만 추가된다. 다른 탭의 읽기 로직은 영향받지 않는다.

## read_db → brief.md 매핑

- `structure-1.marks`에 있는 화면은 §1 표에서 삭제하고 §5 가정 로그에 "사용자 제외" 기록. `text`가 "추천대로"가 아니면 원문을 §5에 남기고 빠진 화면은 §1에 행 추가.
- `structure-2.answers`의 각 값을 위 표 "brief.md 반영" 열대로 채운다. 추천값이 선택된 항목도 **답한 것**으로 취급한다 (가정이 아니다). 노출되지 않은 질문(PRD로 확정)은 출처를 PRD로 적는다.
- 두 문서가 모두 없으면 의견 0건 → interview-rules.md §1의 터미널 질문으로 폴백.

## 렌더러(KIND=structure)가 채우는 것

`templates/structure-survey.html` 상단 `const SURVEY = {...}` 하나. 형식은 템플릿 주석에 있다. 채울 때 규칙:

- `screens[].id`는 영문 slug, `name`은 PRD 화면명 그대로.
- `questions[]`는 노출할 질문만. `options[0]`가 추천. `why`는 추천 이유 한 줄, PRD 근거를 쓴다 ("PRD에 로그인 언급 없음").
- `fixed[]`는 PRD로 확정돼 묻지 않는 항목. `{label, value, source}`.
- `<title>`은 "1단계 구조".
