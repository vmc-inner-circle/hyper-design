# 데이터 형식 — screens.json · flow.json · icons.json

정본은 `docs/harness-design.md` §6. 여기는 복사해서 시작할 **최소 예시**다. (실행 중에는 다른 `runs/` 폴더를 참고하지 않는다 — 형식은 이 문서와 계약 문서로 충분하다.)

## screens.json

```json
{
  "project": "sample",
  "title": "샘플 서비스",
  "platform": "web",
  "round": 1,
  "theme": "a",
  "toggles": { "type": "normal", "accent": "calm" },
  "roles": [
    { "key": "owner", "label": "관리자" },
    { "key": "member", "label": "구성원" }
  ],
  "board": {
    "recommend": {
      "theme": "a", "themeWhy": "업무용이라 중립 톤을 추천해요",
      "type": "normal", "typeWhy": "표가 많아 보통 크기가 알맞아요",
      "accent": "calm", "accentWhy": "상태 색이 눈에 띄도록 강조는 차분하게"
    },
    "ask": [
      { "id": "nav", "text": "왼쪽 메뉴는 어떻게 둘까요?", "options": ["항상 펼침 (추천)", "아이콘만"], "recommended": 0 }
    ],
    "locked": [],
    "focus": []
  },
  "nextScreenId": 1, "nextRegionId": 101,
  "screens": [
    {
      "slug": "home",
      "name": "홈",
      "role": "owner",
      "purpose": "오늘 할 일과 최근 변경을 한눈에 본다",
      "pattern": "dashboard",
      "file": "screens/home.html",
      "regions": [
        { "key": "summary", "label": "오늘 요약", "why": "§2-1 큰 흐름 파악" },
        { "key": "recent",  "label": "최근 변경 목록" },
        { "key": "new",     "label": "새로 만들기 버튼 영역" }
      ]
    }
  ]
}
```

- `id`는 적지 않아도 된다 → `node scripts/ids.js runs/<p>`가 채운다. 화면은 1부터(screens.json 순서), 항목은 101부터 따로. 한 번 발급된 번호는 바뀌지 않는다.
- `roles[].user`(선택): `{ "name": "김지영", "initials": "김지" }` — 셸 오른쪽 위·사이드바 아래 사용자 표시. `brand`·`brandIcon`(선택): 상단바 서비스 이름·아이콘(없으면 `title`·layout-dashboard). 셸은 `scripts/expand.js`가 붙인다. 화면마다 `shell: "none"`(메뉴 없는 한 장)·`navActive: "<nav slug>"`(메뉴에 없는 화면에서 켤 항목)로 바꿀 수 있다.
- `overlayOf`(선택): 뜨는 창 화면 — 조각에는 `.modal-backdrop`만, 뒷 화면은 build가 합친다. 이름은 '~ 창'.
- `board.locked`: 2라운드부터 `["theme","toggles","ask"]`. `board.focus`: 지난 라운드에 고친 화면 slug — 보드 맨 위에 먼저 나온다.

## flow.json

```json
{
  "flows": [
    {
      "key": "create",
      "name": "새 항목 만들기",
      "role": "owner",
      "steps": [
        { "from": "home", "region": "new", "trigger": "create", "action": "'새로 만들기'를 누르면", "to": "editor" },
        { "from": "editor", "region": "save", "trigger": "save", "action": "'저장'을 누르면", "to": "home" }
      ]
    }
  ],
  "branches": [
    { "from": "home", "region": "list", "trigger": "invite", "action": "'초대하기'를 누르면", "to": "invite-dialog" }
  ]
}
```

- `branches`(갈래): 흐름 밖의 버튼이 여는 화면·창. 형식은 step과 같다. 글자가 있는 `.btn`은 `data-trigger`(흐름·갈래) · `data-back` · `data-stay="안내 문구"` 중 하나를 반드시 가진다.

조각에서는 누르는 요소에 `data-trigger`: `<button class="btn btn-primary" data-trigger="create">새로 만들기</button>` (그 step의 region 안).

## icons.json (선택)

```json
{
  "_about": "프로젝트 전용 의미 → lucide 이름. core allowlist에 없는 것만.",
  "itinerary": "route"
}
```
