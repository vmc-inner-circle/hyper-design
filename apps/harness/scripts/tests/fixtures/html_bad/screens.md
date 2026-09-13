status: confirmed

# Screens

컴포넌트 목록(02 Components): AppBar · TripHeader · TodoItem · BottomCTA · TabBar · FormField · Chip · WebAddressBar · WebSegment · EmptyState · Snackbar

| 순번 | 화면 | slug | 구성 (위→아래) | 상태 프레임 |
|---|---|---|---|---|
| 1 | 여행 홈 | home | ① AppBar(제목 "내 여행") · ② TripHeader(제주 · 11/20~24 · 5명, 카드형) · ③ TodoItem×2(오늘 남은 할 일) · ④ BottomCTA(새 여행 만들기) · ⑤ TabBar(일정 활성) | default·empty·loading·error·many-items·text-120 |
| 2 | 여행 만들기 | create | ① AppBar(뒤로 · 여행 만들기) · ② FormField×2(목적지 · 기간) · ③ Chip×3(구성원: 지수·영호 + 추가) · ④ BottomCTA(만들기) | default·empty·loading·error·text-120 |
| 3 | 내 준비 (웹) | my-prep | ① WebAddressBar + AppBar(영호 님 준비) · ② WebSegment(내 준비 활성) · ③ 소제목 web-h2 "챙길 것" + TodoItem×2(상비약 · 신분증) · ④ (없음, 탭바 없음) | default·empty·loading·error·text-120 |
