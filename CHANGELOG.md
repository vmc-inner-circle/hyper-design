# Changelog

버전은 `plugins/k-style-ui-ux/`의 manifest 4개(`.claude-plugin/plugin.json`·`.codex-plugin/plugin.json`·`.cursor-plugin/plugin.json`·`plugin.json`)와 이 파일 맨 위 항목이 같아야 한다(`ci/verify.py`가 검사).

## v0.19.2

- 정보에는 브랜드 색을 쓰지 않는다(#48): 숫자 강조(`.num`)·할인율(`.price-off`)·진행 막대(`.progress .is-on`)·읽기용 별점(`.rating .is-on`)을 브랜드 색 → 먹색(`--c-text-1`). 별점 입력(`.rating.is-input`)·범위 고르기·체크·스위치·주 버튼·탭 선택은 그대로 브랜드 색. 원칙 21에 한 줄, `COMPONENTS.md`·체크리스트에 같은 규칙. 근거: 팔레트 원본 8곳(당근·컬리 등) 모바일 웹 첫 화면은 숫자·진행·별점에 핵심 색 0회, 지난 결과물 528화면 중 27%가 그 자리에 브랜드 색을 썼다(화면당 브랜드 색 수는 원본과 같은 중앙값 1곳 — 양이 아니라 자리의 문제).
- selfcheck: 화면 `<style>`에서 숫자 글자·얇은 막대를 `--c-brand*`로 칠하면 실패(지난 결과물 528화면 중 20화면에 해당).

## v0.19.1

- 캔버스 연결 보기(@eungshin #29): 카드 아래 "갈 수 있는 곳 N"(또는 Shift+클릭)을 누르면 그 화면의 버튼·링크가 어느 화면으로 가는지 색 선과 버튼 글자로 보이고, 나머지 화면은 흐려진다. Esc나 빈 곳을 누르면 꺼진다. 링크는 build_canvas가 화면 HTML의 `<a href>`에서 읽는다(뒤로·하단 탭 제외, 같은 곳으로 가는 링크는 한 선으로 묶음). go 시간 영향 없음.

## v0.19.0

하네스톤 멤버 PR의 아이디어를 지금 구조로 옮겼다(원래 커밋은 그대로 history에).

- 캔버스에서 의견 남기기(@yeoul9703 #13·#30, @srlee0408 #16, @eungshin #29): 크게 보기에서 "의견"을 켜고 화면 요소를 눌러 의견을 달면, `[k-style-ui-ux 수정 요청]` 텍스트로 한 번에 복사된다. 대화창에 붙여넣으면 go/max가 `core/references/feedback.md`(고치는 순서, 막연한 말 해석표 17줄)를 따라 그 요소만 고치고 selfcheck·audit·캔버스를 다시 돌린다. 캔버스 테스트 +1.9초.
- 한글 문구 검사(@hydrojun #26): selfcheck가 해요체 앱에 섞인 하십시오체, "~을 통해", "제공합니다"는 실패로, 나머지 번역투·띄어쓰기·은유 라벨은 경고로 낸다. 짧은 라벨과 후기 본문은 뺀다. 지난 결과물 795화면 기준 실패 오탐 0, +0.04초.
- 누르는 것은 반드시 어딘가로 이어진다(@srlee0408 #16·#23): `<button>`·`<a>`는 다른 화면 링크·`data-back`·`data-stay="안내 문구"` 중 하나가 없으면 selfcheck 실패다. 칩·세그먼트·체크·스위치·탭은 면제. `data-stay`는 화면 위쪽 토스트로 뜬다. 사실 대조 에이전트의 이 일을 뺐다. 실측 go 14.2·13.0분 → 12.3·13.1분(PRD 2개).
- 저장소: 산출물(`loop/results`·`demos`·`submissions/*/`)은 커밋하지 않는다(#59, `ci/verify.py` 검사). `loop/run.py`가 `stats.json`(단계별 시간·모델별 토큰·비용)을 남긴다(@hydrojun #14).

## v0.18.2

- 큰 글자 세트의 캡션 14px → 16px(@doojin88, #19): 배지·탭 라벨이 캡션 토큰을 써서 큰 글자 화면에서도 14px로 남아 audit `large_text_body_font`가 83%(기준 90%)로 떨어지던 것. 예시 토큰 4벌도 같은 한 줄.

## v0.18.1

- Cursor 지원: 저장소 루트 `.cursor-plugin/marketplace.json`과 플러그인 `.cursor-plugin/plugin.json`을 더해 Cursor에서 GitHub 저장소로 가져와 설치한다(같은 폴더, 사본 없음). 스킬 부르기는 `/` → `go`·`max`.
- `save_prd.py`가 Cursor 대화 기록(`~/.cursor/projects/<폴더>/agent-transcripts/`)에서도 붙여넣은 PRD를 꺼낸다.
- `ci/verify.py`가 Cursor 마켓·manifest까지 같은 폴더·같은 버전인지 본다.

## v0.18.0

- 화면 유형: 홈·상세·목록 기본 화면은 `core/references/screen-kinds.md`의 유형 하나로 짠다(`screens.json`의 `archetype`, selfcheck). 유형 = 첫 화면에서 가장 큰 면적을 차지하는 것 — 국내 서비스 화면 296장(앱 37개 + 모바일 웹 57곳)에서 묶었다(`docs/research/screen-archetypes/`). 홈 7(찾기·진열·현황·목록·피드·대표 콘텐츠·일정), 상세 6, 목록 6.
- 고르는 법: 시장 해석 에이전트가 상위 앱의 홈·상세·목록을 유형으로 분류해 `conventions.json`의 `archetypes`에 적고, 2개 이상 앱이 같으면 그것이 기본값(벗어나면 `archetype_why`). 없으면 판단 질문.
- `market.py --exclude`(또는 `MARKET_EXCLUDE`): 이름에 그 말이 든 앱을 뺀다 — 실험에서 원본 앱이 정답을 알려 주지 않게.
- 채움 부품(검색창·입력칸·세그먼트·보조 버튼·배지·아이콘 칸)의 바탕을 `--c-fill` 하나로: 회색 페이지 위에서는 흰색, 흰 블록·시트·흰 바탕 화면 안에서는 회색. 전에는 늘 회색이라 회색 페이지 위에서 사라졌다(유형 실험 12개 결과물에서 검색창 73곳 중 30곳, 세그먼트 63곳 중 18곳).
- 첫 화면 주인공 강제: 유형 화면은 주인공 요소에 `data-anchor`(selfcheck), audit `archetype_anchor`가 렌더링해서 주인공이 첫 화면 위쪽 절반에서 시작하고 다른 덩어리보다 큰지 잰다(대표 콘텐츠형은 맨 위·화면 폭 전체). 대표 콘텐츠 부품 `feature` 추가, 대표 콘텐츠형·피드형 홈은 큰 머리글 없이(h1은 앱바 서비스 이름) — 치지직 익명 PRD 실험에서 머리글·아바타 줄이 위를 차지해 다른 유형으로 읽힌 것.
- 칩·세그먼트 선택에서 브랜드 색을 뺐다: 칩(걸러 보기)은 먹색 채움 + 흰 글자, 세그먼트(보기 전환)는 회색 판 위의 흰 칸 + 먹색 글자. 브랜드 색은 버튼·체크·스위치(행동·값)에만. 판은 `--c-track`(회색 페이지 위에서는 한 단계 짙은 회색, 흰 바탕 안에서는 회색).
- 아바타 스타일 라이브러리(`assets/avatars/`): 컬러 사람 일러스트(Fluent 밝은 피부, MIT)·선 드로잉(Notionists, CC0)·부드러운 선(Lorelei, CC0)·동물 얼굴(Fluent, MIT) + 실제 사진. 앱 전체에 하나(`avatar_style`), 사람마다 성별·나이가 맞는 파일 하나를 사실 표에 적어 모든 화면이 같이 쓴다. 이름 한 글자 아바타 금지(selfcheck) — 7개 시안 비교(`docs/pr/avatar-styles/`), 도형·Open Peeps·Thumbs는 뺐다.
- 팔레트 도메인 공백 메우기: 시드 후보 실측 추가(토스·카카오뱅크·케이뱅크·치지직·카카오모빌리티·티맵·밴드·멜론·FLO)와 브랜드 가이드 색(Discord·Facebook·Threads·X), 도메인 동의어. 색이 비슷해도 도메인이 다르면 남긴다. 유형 실험 6개 앱 중 5개가 "맞는 도메인 없음"으로 성격 낱말만 보고 골라 택시 앱에 뷰티 앱 청록이 들어가던 것.
- 밝은 브랜드(카카오 노랑·배민 민트·치지직 초록): 면은 원색, 버튼 글자·선·링크는 먹색(`--c-brand-line` 토큰 추가). 전에는 어둡게 해 올리브색이 되거나 시드에서 빠졌다. 모노 시드(Threads·X)도 받는다.
- 시드 기본값일 때 대안을 점수 순으로(전에는 늘 당근·마이리얼트립, 이유 없음), 시드 도메인 점수는 맞은 낱말마다 3, 재거르기 때 승인 시드의 손 값 보존.
- 타깃 성별 표시: 근거가 분명한 곳만(지그재그·화해 시드, 29CM 라이브러리 — 출처·연도 함께), `--gender`는 PRD에 타깃 성별이 적혀 있을 때만, 일치 +1.
- 대안은 기본값이 라이브러리여도 시드·라이브러리 통합 점수로(패션: 29CM 기본 → 대안 지그재그·프립, 전에는 당근·마이리얼트립).
- 브랜드 시드 42개 승인(수민).
- 유형 주인공 위에 원칙 1의 상황 머리글은 그대로 둔다(대표 콘텐츠형·피드형 제외) — 청첩장 회귀 확인에서 머리글을 빼 블라인드 0/5 → 고친 뒤 2/5.

## v0.17.1

- `audit.py`에 한국어 줄바꿈 실측: 글자 하나하나의 실제 위치로 줄을 되살려 어절 쪼개짐(`word_split`)·칸 넘침(`box_overflow`)은 실패로, 마지막 줄 한두 글자(`last_line_orphan`)는 보고만. 셈은 hanmariyang/giting-skills의 hangul-wrap(`wrapcheck.mjs`, MIT)에서 옮겼다. v19 4개 앱에서 audit 시간 +4~7초/앱.
- `.row-date`를 고정 폭(52px) 대신 `min-width`로: `11/16 (월)`·`10월 30일`이 칸을 6~12px 넘겨 옆 제목에 붙던 것(v19 필라테스·사주 9건)이 0건.

## v0.17.0

- 이름: hyper-design → k-style-ui-ux(플러그인 폴더·마켓·명령어). 지난 결과 기록(`loop/results`, `loop/RESULTS.md`, `demos/`)은 당시 이름 그대로.
- Codex 지원: `plugins/k-style-ui-ux/` 폴더 하나에 Claude·Codex manifest를 함께 두고 두 마켓 파일(`.claude-plugin/marketplace.json`·`.agents/plugins/marketplace.json`)이 같은 폴더를 가리킨다. 스킬마다 Codex용 `agents/openai.yaml`.
- 스킬 문구에서 Claude 전용 표현(모델 이름·Base directory·`/k-style-ui-ux:max`)을 걷어 내고 플랫폼 차이는 go 스킬 맨 위 한 곳에 모았다.
- `save_prd.py`가 Codex 세션 기록(`~/.codex/sessions`)에서도 PRD를 꺼낸다.
- v19 부품: 상단 가로 탭·정렬/필터 바·아이콘 격자·가로 스크롤 줄·상품 카드 격자·가격·찜·FAB·넘기는 배너·띠 배너·쿠폰·남은 시간, 고르기 시트.

## v0.16.0

- 사람 카드: PRD의 사용자 구분을 그대로 가져와 처음 오는 이유·마음·성공한 순간·첫 화면을 정한다.
