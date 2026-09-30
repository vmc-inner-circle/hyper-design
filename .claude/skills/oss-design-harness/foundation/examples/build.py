"""가족여행 PRD 레퍼런스 화면 14장 생성기 (docs/scope-family-trip.md 범위).

python3 build.py  →  이 폴더에 *.html + screens.json
빌드 에이전트가 참고할 모범 답안이다. 파운데이션 클래스만 쓰고 인라인 style은 쓰지 않는다.
"""
import json, pathlib

HERE = pathlib.Path(__file__).parent
P = {
    "chev": '<path d="M9 6l6 6-6 6"/>', "back": '<path d="M15 6l-6 6 6 6"/>', "plus": '<path d="M12 5v14M5 12h14"/>',
    "pin": '<path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>',
    "bag": '<rect x="4" y="7" width="16" height="13" rx="3"/><path d="M9 7V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2"/>',
    "home": '<path d="M4 10.5 12 4l8 6.5V20H4z"/><path d="M10 20v-5h4v5"/>',
    "cal": '<rect x="4" y="5" width="16" height="15" rx="3"/><path d="M4 10h16M9 3v4M15 3v4"/>',
    "check": '<rect x="4" y="4" width="16" height="16" rx="4"/><path d="m8.5 12 2.5 2.5 4.5-5"/>',
    "done": '<path d="m6.5 12.5 3.5 3.5 7.5-8"/>',
    "circle": '<circle cx="12" cy="12" r="7.5"/>',
    "users": '<circle cx="9" cy="8" r="3.5"/><path d="M3 20c.8-3.5 3.2-5 6-5s5.2 1.5 6 5"/><path d="M16 4.5a3.5 3.5 0 0 1 0 7M18 15c1.6.6 2.6 2.2 3 5"/>',
    "eye": '<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z"/><circle cx="12" cy="12" r="3"/>',
    "plane": '<path d="M10.5 13.5 3 11l1.5-1.5 8 1 4-4.5a2 2 0 0 1 3 3L15 13l1 8-1.5 1.5-2.5-7.5"/>',
    "bed": '<path d="M3 18V7M3 14h18v4M21 14v-2a3 3 0 0 0-3-3h-7v5"/><circle cx="7" cy="11" r="1.8"/>',
    "walk": '<circle cx="13" cy="4.5" r="1.8"/><path d="m9 21 2.5-6 2.5 2.5V21M8 11l3-3.5 3.5 2.5 2.5 3M11.5 15l1-7"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6l1.4 1.4M17 17l1.4 1.4M5.6 18.4 7 17M17 7l1.4-1.4"/>',
    "ticket": '<path d="M4 8a2 2 0 0 0 2-2h12a2 2 0 0 0 2 2v8a2 2 0 0 0-2 2H6a2 2 0 0 0-2-2z"/><path d="M13 6v12" stroke-dasharray="2 2"/>',
    "car": '<path d="M5 16V11l2-5h10l2 5v5M5 16h14M5 16v2M19 16v2"/><circle cx="8" cy="13.5" r="1"/><circle cx="16" cy="13.5" r="1"/>',
    "q": '<circle cx="12" cy="12" r="8.5"/><path d="M9.8 9.5a2.3 2.3 0 1 1 3.2 2.1c-.6.3-1 .8-1 1.4v.5M12 16.5v.2"/>',
    "link": '<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>',
}
def ic(n): return f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{P[n]}</svg>'
CH = ic("chev")

def doc(title, body, cls=""):
    return f'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=375, initial-scale=1">
<title>{title}</title>
<link rel="stylesheet" href="tokens.css"><link rel="stylesheet" href="../components.css">
</head>
<body class="{cls}">
{body}
</body></html>
'''
def appbar(title, back): return f'<header class="appbar"><a class="appbar-btn" href="{back}" aria-label="뒤로">{ic("back")}</a><h1 class="appbar-title">{title}</h1><span></span></header>'
def row(title, sub="", href=None, lead="", badge=None, trail=CH, cls=""):
    b = f'<span class="badge {badge[0]}">{badge[1]}</span>' if badge else ""
    s = f'<p class="row-sub">{sub}</p>' if sub else ""
    tag, h = ("a", f' href="{href}"') if href else ("div", "")
    t = f'<span class="row-trail">{trail}</span>' if (href and trail) else (f'<span class="row-trail">{trail}</span>' if trail and trail != CH else "")
    return f'<{tag} class="row {cls}"{h}>{lead}<div class="row-main">{b}<p class="row-title">{title}</p>{s}</div>{t}</{tag}>'
def lead(n, cls=""): return f'<span class="row-lead {cls}">{ic(n)}</span>'
def when(a, b=""): return f'<span class="row-date">{a}{"<br>" + b if b else ""}</span>'
def info(n, text): return f'<p class="info">{ic(n)}<span>{text}</span></p>'
KIDS = [("홈", "home", "planner-home.html"), ("일정", "cal", "planner-day.html"), ("준비", "check", "tasks.html"), ("가족", "users", "family.html")]
def tabbar(cur): return '<nav class="tabbar" aria-label="아래 메뉴">' + "".join(
    f'<a class="tab" href="{h}"{" aria-current=\"page\"" if h == cur else ""}>{ic(i)}{t}</a>' for t, i, h in KIDS) + "</nav>"
FIXED = ("is-brand", "확정")
S = {}

# ───────── 부모 (보기만, 탭바 없음) ─────────
flow = f'''<section class="block is-list">
    <div class="block-head"><h2 class="h2">여행 흐름</h2></div>
    {row("제주 도착 · 해비치 호텔", "비행기 10:05 출발", "parent-day.html", when("11/20", "금"), ("is-brand", "시간 바뀜"))}
    {row("오후 2시 섭지코지 산책", "저녁은 정하는 중", "parent-day.html", when("11/21", "토"))}
    {row("정하는 중", "11월 10일까지 정해요", "parent-day.html", when("11/22", "일"))}
    {row("호텔에서 나와 집으로", "김포 도착 오후 4시", "parent-day.html", when("11/23", "월"))}
  </section>'''
S["parent-home"] = ("부모 홈 · D-30 이전", "viewer", "부모님이 보는 모습", f'''<main class="page">
  <header class="hero">
    <p class="eyebrow">지은이가 준비하는 여행 · <span class="num">D-51</span></p>
    <h1 class="title">11월 20일부터 3박&nbsp;4일, 제주에 가요</h1>
    <p class="lead">어머니, 아버지, 민수네 가족과 함께예요</p>
  </header>
  {flow}
  <section class="block is-list">
    {row("챙기실 것 3가지", "천천히 준비하셔도 돼요", "parent-checklist.html", lead("bag"))}
  </section>
</main>''', "is-viewer")

S["parent-home-d7"] = ("부모 홈 · D-7", "viewer", "부모님이 보는 모습", f'''<main class="page">
  <header class="hero">
    <p class="eyebrow">제주 가족여행 · <span class="num">D-3</span></p>
    <h1 class="title">금요일 아침 8시 30분, 김포공항에서 만나요</h1>
    <p class="lead">국내선 1층 대한항공 카운터 앞</p>
    <a class="hero-more" href="#">지도에서 보기{CH}</a>
  </header>
  <section class="block">
    <div class="block-head"><h2 class="h2">챙기실 것 1가지 남았어요</h2></div>
    {info("sun", "제주 낮 17도, 바람이 불어요. 얇은 겉옷을 챙기세요.")}
    <div>
    {row("신분증", "", None, lead("done", "is-done"), cls="is-done")}
    {row("편한 운동화", "하루 30분 정도 걸어요", None, lead("done", "is-done"), cls="is-done")}
    {row("혈압약 4일치", "", None, lead("circle"), trail="")}
    </div>
  </section>
  {flow}
</main>''', "is-viewer")

S["parent-home-trip"] = ("부모 홈 · 여행 중", "viewer", "부모님이 보는 모습", f'''<main class="page">
  <header class="hero">
    <p class="eyebrow">여행 2일째 · 11월 21일 토요일</p>
    <h1 class="title">오늘은 섭지코지에 가요</h1>
    <p class="lead">오후 1시 30분에 호텔 로비에서 모여요</p>
  </header>
  <section class="block is-list">
    <div class="block-head"><h2 class="h2">오늘 하루</h2></div>
    {row("호텔 조식", "1층 식당 · 10시까지", None, when("08:00"), trail="")}
    {row("섭지코지 산책", "차로 40분 · 평지 30분 걷기", "parent-day.html", when("14:00"), FIXED)}
    {row("저녁 · 흑돼지 돈사돈", "호텔에서 차로 15분", "parent-day.html", when("18:30"), FIXED)}
  </section>
  <section class="block">
    {info("walk", "오늘은 많이 걷지 않아요. 계단 없는 길이에요.")}
  </section>
</main>''', "is-viewer")

S["parent-day"] = ("날짜 상세", "viewer", "부모님이 보는 모습", f'''{appbar("11월 21일 토요일", "parent-home.html")}
<main class="page">
  <section class="block is-list">
    {row("섭지코지 산책", "호텔에서 차로 40분 · 평지 30분", None, when("14:00"), FIXED, trail="")}
    {row("저녁은 지은이가 정하는 중이에요", "11월 10일까지 정해요", None, when("저녁"), trail="")}
  </section>
  <section class="block">
    <p class="block-note">이날이 궁금하시면 눌러 주세요. 지은이에게 조용히 표시만 가요.</p>
    <button class="btn secondary">이날 궁금해요</button>
  </section>
</main>''', "is-viewer")

S["parent-checklist"] = ("내 준비물", "viewer", "부모님이 보는 모습", f'''{appbar("챙기실 것", "parent-home.html")}
<main class="page">
  <section class="block is-list">
    {row("신분증", "", None, lead("done", "is-done"), cls="is-done")}
    {row("편한 운동화", "하루 30분 정도 걸어요", None, lead("done", "is-done"), cls="is-done")}
    {row("혈압약 4일치", "누르면 챙겼다고 표시돼요", "#", lead("circle"), trail="")}
  </section>
  <section class="block">
    {info("bag", "나머지 짐은 지은이가 챙겨요 — 우산, 상비약, 충전기")}
  </section>
</main>''', "is-viewer")

# ───────── 자식 (계획하는 사람) ─────────
S["planner-home"] = ("자녀 홈", "planner", "계획하는 자녀", f'''<main class="page">
  <header class="hero">
    <p class="eyebrow">제주 가족여행 · <span class="num">D-51</span></p>
    <h1 class="title">정할 게 3개 남았어요</h1>
    <p class="lead">정하기 전까지 부모님께는 '정하는 중'으로 보여요</p>
  </header>
  <section class="block is-list">
    <div class="block-head"><h2 class="h2">정할 것</h2></div>
    {row("11/21 토 저녁", "후보 2곳 · 11월 10일까지", "planner-day.html", lead("cal"), ("is-brand", "어머니가 궁금해하세요"))}
    {row("11/22 일 하루", "아직 비어 있어요", "planner-day.html", lead("cal"))}
    {row("렌터카 보험", "완전자차 / 일반자차", "item-edit.html", lead("car"))}
  </section>
  <section class="block is-list">
    {row("할 일 5가지 중 2가지 남았어요", "민수: 렌터카 예약 · 어머니: 혈압약", "tasks.html", lead("check"))}
    {row("부모님께 보이는 모습", "", "parent-preview.html", lead("eye"))}
  </section>
</main>
{tabbar("planner-home.html")}''', "has-tab")

S["planner-home-trip"] = ("자녀 홈 · 여행 중", "planner", "계획하는 자녀", f'''<main class="page">
  <header class="hero">
    <p class="eyebrow">여행 2일째 · 11월 21일 토요일</p>
    <h1 class="title">다음은 오후 2시 섭지코지</h1>
    <p class="lead">1시 30분 로비 출발 · 차로 40분</p>
  </header>
  <section class="block is-list">
    <div class="block-head"><h2 class="h2">오늘 예약</h2></div>
    {row("흑돼지 돈사돈 · 6명", "확인번호 <span class='code'>DS-4821</span>", "item-edit.html", when("18:30"))}
    {row("해비치 호텔 · 2박째", "확인번호 <span class='code'>HB-20931</span>", "item-edit.html", lead("bed"))}
  </section>
  <section class="block is-list">
    {row("내일 일정", "우도 배편 · 오전 9시 30분", "planner-day.html", lead("cal"))}
  </section>
</main>
{tabbar("planner-home.html")}''', "has-tab")

S["planner-day"] = ("일정", "planner", "계획하는 자녀", f'''{appbar("일정", "planner-home.html")}
<main class="page">
  <div class="chips" role="tablist" aria-label="날짜">
    <button class="chip" role="tab" aria-selected="false">11/20 금</button>
    <button class="chip is-selected" role="tab" aria-selected="true">11/21 토</button>
    <button class="chip" role="tab" aria-selected="false">11/22 일</button>
    <button class="chip" role="tab" aria-selected="false">11/23 월</button>
  </div>
  <section class="block is-list">
    <div class="block-head"><h2 class="h2">11월 21일 토요일</h2></div>
    {row("섭지코지 산책", "호텔에서 차로 40분", "item-edit.html", when("14:00"), FIXED)}
    {row("흑돼지 '돈사돈'", "대안: 올래국수", "item-edit.html", when("18:30"), ("", "후보"))}
    <a class="row is-add" href="item-edit.html">{lead("plus")}<div class="row-main"><p class="row-title">일정 추가</p></div></a>
  </section>
  <section class="block">
    {info("eye", "부모님께는 저녁이 '정하는 중'으로 보여요")}
  </section>
</main>
{tabbar("planner-day.html")}''', "has-tab")

form = lambda err: f'''{appbar("일정 고치기", "planner-day.html")}
<main class="page">
  <div class="field"><label class="label" for="n">이름</label><input class="input" id="n" value="흑돼지 '돈사돈'"></div>
  <div class="field{' is-error' if err else ''}"><label class="label" for="t">시간</label><input class="input" id="t" value="{'' if err else '11월 21일 토 오후 6시 30분'}" placeholder="시간을 골라 주세요">{'<p class="field-msg">시간을 정해야 확정할 수 있어요</p>' if err else ''}</div>
  <div class="field"><label class="label" for="m">예약 메모</label><input class="input" id="m" value="6명 · 확인번호 DS-4821"></div>
  <div class="field"><span class="label">부모님께 어떻게 보일까요?</span>
    <div class="seg" role="radiogroup"><button class="seg-item" role="radio" aria-checked="false">정하는 중</button><button class="seg-item is-selected" role="radio" aria-checked="true">확정</button></div>
  </div>
</main>
<div class="cta"><button class="btn primary full">저장</button></div>'''
S["item-edit"] = ("항목 편집", "planner", "계획하는 자녀", form(False), "plain has-cta")
S["item-edit--error"] = ("항목 편집 · 시간 없음", "planner", "계획하는 자녀", form(True), "plain has-cta")

S["tasks"] = ("할 일·준비물", "planner", "계획하는 자녀", f'''<main class="page">
  <header class="hero">
    <p class="eyebrow">함께 준비해요</p>
    <h1 class="title">5가지 중 2가지 남았어요</h1>
  </header>
  <section class="block is-list">
    <div class="block-head"><h2 class="h2">남은 것</h2></div>
    {row("렌터카 예약", "민수 · 11월 1일까지", "#", lead("circle"))}
    {row("혈압약 4일치", "어머니", "#", lead("circle"))}
    <a class="row is-add" href="#">{lead("plus")}<div class="row-main"><p class="row-title">할 일 추가</p></div></a>
  </section>
  <section class="block is-list">
    <div class="block-head"><h2 class="h2">끝낸 것</h2></div>
    {row("항공권 예약", "지은", None, lead("done", "is-done"), cls="is-done", trail="")}
    {row("호텔 예약", "지은", None, lead("done", "is-done"), cls="is-done", trail="")}
    {row("신분증 확인", "아버지", None, lead("done", "is-done"), cls="is-done", trail="")}
  </section>
</main>
{tabbar("tasks.html")}''', "has-tab")

S["family"] = ("가족·역할", "planner", "계획하는 자녀", f'''<main class="page">
  <header class="hero">
    <p class="eyebrow">함께 가는 사람 6명</p>
    <h1 class="title">부모님은 보기만 하세요</h1>
    <p class="lead">계획은 지은이와 민수가 함께 짜요</p>
  </header>
  <section class="block is-list">
    {row("어머니", "무릎이 안 좋으셔서 오래 걷기 힘들어요", "#", lead("users"), ("", "보기만"))}
    {row("아버지", "매운 음식은 피해요", "#", lead("users"), ("", "보기만"))}
    {row("민수", "하윤이(7살)와 함께", "#", lead("users"), ("is-brand", "함께 계획"))}
    <a class="row is-add" href="join.html">{lead("plus")}<div class="row-main"><p class="row-title">가족 초대</p></div></a>
  </section>
</main>
{tabbar("family.html")}''', "has-tab")

S["parent-preview"] = ("부모님께 보이는 모습", "planner", "계획하는 자녀", f'''{appbar("부모님께 보이는 모습", "planner-home.html")}
<main class="page">
  <section class="block">
    <p class="block-note">후보는 부모님께 보이지 않아요. 확정하면 바로 부모님 화면에 나타나요.</p>
  </section>
  <section class="block is-list">
    <div class="block-head"><h2 class="h2">11월 21일 토요일</h2></div>
    {row("섭지코지 산책", "그대로 보여요", None, when("14:00"), FIXED, trail="")}
    {row("저녁은 지은이가 정하는 중이에요", "후보 2곳은 보이지 않아요", None, when("저녁"), trail="")}
  </section>
  <section class="block is-list">
    {row("부모님 화면 그대로 보기", "", "parent-home.html", lead("eye"))}
  </section>
</main>''', "")

# ───────── 공통 ─────────
S["join"] = ("초대 링크 첫 화면", "shared", "공통", f'''<main class="page">
  <header class="hero">
    <p class="eyebrow">제주 가족여행</p>
    <h1 class="title">지은이가 여행에 초대했어요</h1>
    <p class="lead">보기만 하셔도 돼요. 계획은 지은이가 짜요.</p>
  </header>
  <section class="block">
    {info("cal", "11월 20일(금) ~ 23일(월), 3박 4일")}
    {info("users", "어머니, 아버지, 지은, 민수네 가족 6명")}
    {info("pin", "제주 · 해비치 호텔")}
  </section>
</main>
<div class="cta"><a class="btn primary full" href="parent-home.html">함께하기</a></div>''', "has-cta")

# ───────── 파일 쓰기 + 매니페스트 ─────────
GROUP = {"viewer": "부모님이 보는 모습", "planner": "계획하는 자녀", "shared": "공통"}
LINKS = {}
for sid, (title, role, group, body, cls) in S.items():
    (HERE / f"{sid}.html").write_text(doc(title, body, cls), encoding="utf-8")
manifest = {"screens": [{"id": sid, "file": f"{sid}.html", "title": t, "role": r, "group": g} for sid, (t, r, g, _, _) in S.items()]}
(HERE / "screens.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(S), "screens")
