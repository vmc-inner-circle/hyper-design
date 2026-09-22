# common/ — 범용 렌더러 템플릿

이 폴더의 HTML 파일은 **프로젝트와 무관한 범용 렌더러**다.
프로젝트별 데이터(JSON)만 바꾸면 어떤 앱에서든 동작한다.

## 3파일 패턴

모든 단계에서 동일한 관계:

```
common/[name]-renderer.html   ← 렌더러 (CSS + JS, 프로젝트 무관)
schemas/[name]-data.schema.json ← 데이터 구조 명세
design/probes/[name]-data.json  ← 프로젝트별 데이터 (메인 에이전트가 생성)
```

최종 출력:
```
design/probes/[name].html      ← 인라인된 단일 파일 (브라우저에서 바로 열림)
```

## 렌더러 작성 규칙

### 1. 데이터 주입 지점 — 마커는 바이트 단위로 정확히
렌더러 HTML 상단에 **정확히 이 두 줄**이 있어야 한다. 빌드 스크립트가 이 문자열을 찾아 치환하므로, 주석 문구를 바꾸면 치환이 조용히 실패하고 "DATA가 없습니다" 화면이 뜬다.
```html
<script>
/* REPLACE: DATA */
var DATA = null;
</script>
```
fetch 폴백은 두지 않는다 — 로컬 HTML에서 CORS로 막혀 어차피 동작하지 않고, 있으면 "왜 안 뜨지"를 오래 헤매게 만든다. DATA가 없으면 즉시 실패 메시지.

### 2. 빌드는 손으로 하지 않는다
`scripts/build_flow.py`가 검증 → 치환 → 저장을 한다. 마커 불일치, 없는 phoneId, 짝이 안 맞는 clickId, 모르는 컴포넌트 type, icon에 들어간 HTML — 하나라도 있으면 exit 1.
```bash
python scripts/build_flow.py                                    # design/probes/flow-data.json → flow-animated.html
python scripts/build_flow.py --data <data.json> --out <out.html>
```
손으로 `replace()`를 쓰면 마커가 어긋나도 파일은 생성되므로 실패를 눈치채지 못한다. 그래서 스크립트로만 빌드한다.

### 3. phones는 선언적 컴포넌트, raw HTML 금지
메인 에이전트는 HTML을 몰라도 채울 수 있어야 한다. `type` + 텍스트 필드만 쓴다. 허용 type과 필드는 `schemas/flow-data.schema.json`의 enum이 단일 진실이다.
```json
"home": {
  "bar":  { "title": "내 앱", "back": false },
  "body": [
    { "type": "hero-action", "icon": "i-cam", "label": "항목 추가", "id": "addBtn" },
    { "type": "search", "placeholder": "이름으로 검색" },
    { "type": "hint", "text": "위 버튼을 누르거나 검색하세요" }
  ]
}
```

### 4. 아이콘은 클래스명만
`icon` 필드에는 `"i-cam"`처럼 **클래스명만** 쓴다. 렌더러가 `<div class="ic i-cam"></div>`를 만든다. HTML을 넣으면 `.ic` 안에 `.ic`가 또 들어가 이중 중첩이 된다.
아이콘 자체는 CSS `background-image: url("data:image/svg+xml,…")`로 렌더러 안에 정의한다 — 이모지는 OS마다 폰트가 달라 안 보이는 환경이 있고, 인라인 SVG는 JSON 문자열 안에서 따옴표가 깨진다.

### 4-1. 애니메이션은 한 요소에 하나의 `animation` 선언
`.fi`(페이드인)와 `.hl`(펄스)이 같은 요소에 붙는다. 각각 `animation:`을 따로 선언하면 나중 규칙이 앞 규칙을 **통째로 덮어써** 페이드인이 실행되지 않고 `opacity:0`에 갇힌다. 그래서 `.fi.hl { animation: fi …, pr … }`처럼 한 선언에 나열한다. 새 애니메이션 클래스를 추가할 때 같은 함정을 피할 것.

### 5. 폰 프레임
모든 렌더러는 390×780 폰 프레임 안에서 동작한다.
- 노치: `width:126px; height:34px; border-radius:0 0 20px 20px`
- 상태바: `height:54px`
- 화면 전환: `.sc` 클래스, `transform:translateX()` 애니메이션
- 클릭 대상: `.hl` 클래스 (파란 펄스 하이라이트)

### 6. 우측 패널
각 섹션은 `.rcard` 독립 카드로 분리:
- 섹션 제목: `.rl` (13px, 굵게)
- 내용은 섹션별로 다르지만, 카드 스타일은 통일

### 7. 의견 수집 + 저장
모든 렌더러에 👍/🤔 의견 패널을 포함한다.
- **localStorage 저장** (`feedback/scene-<시나리오>-<장면>` 키)
- 🤔 선택 시 자유 입력 펼침
- 저장 버튼 클릭 → localStorage에 즉시 반영 + 토스트
- 새로고침 시 `loadOps()`로 복원 → 진행 점에 초록 표시

## 현재 렌더러 목록

| 파일 | 단계 | 스키마 | 용도 |
|---|---|---|---|
| flow-renderer.html | 2단계 플로우 | flow-data.schema.json | 따라가 보기 투어 — 시나리오별 화면 전환 + 유저 플로우 + 기대 효과 |
| ui-recommend-renderer.html | 3단계 UI 추천 | ui-recommend-data.schema.json | 화면별 A/B(C) 폰 목업 비교 + 참고 앱 + 추천 이유 |
| preview-renderer.html | 4.5단계 최종 미리보기 | preview-data.schema.json | 화면 + 아이콘 + 토큰 통합 확인 + nav 매핑(폰 클릭→점프) |
