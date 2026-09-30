"""가족여행 PRD 레퍼런스 화면 12장 생성기 (docs/scope-family-trip.md 범위, 역할 이름 없이 편집 권한만).

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
    "alert": '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5v5M12 16v.5"/>',
    "q": '<circle cx="12" cy="12" r="8.5"/><path d="M9.8 9.5a2.3 2.3 0 1 1 3.2 2.1c-.6.3-1 .8-1 1.4v.5M12 16.5v.2"/>',
    "link": '<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>',
}
def ic(n): return f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{P[n]}</svg>'
CH = ic("chev")

def doc(title, body, cls=""):
    return f'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=375, initial-scale=1">
<title>{title}</title>
<link id="tokens" rel="stylesheet" href="tokens.css"><link rel="stylesheet" href="../components.css"><script src="../palette.js"></script>
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
A = "../assets/fluent/"
def art(n): return f'<span class="row-art"><img src="{A}{n}.svg" alt=""></span>'
def avatar(n): return f'<span class="avatar"><img src="{A}{n}.svg" alt=""></span>'
def avatars(*ns): return '<span class="avatars" aria-hidden="true">' + "".join(avatar(n) for n in ns) + "</span>"
def todo(title, sub, n, done=False):
    chk = f'<button class="check" role="checkbox" aria-checked="{"true" if done else "false"}" aria-label="{title} 챙김"><span>{ic("done")}</span></button>'
    return row(title, sub, None, art(n), cls="is-done" if done else "", trail=chk)
def info_art(n, text): return f'<p class="info"><img src="{A}{n}.svg" alt=""><span>{text}</span></p>'
def when(a, b=""): return f'<span class="row-date">{a}{"<br>" + b if b else ""}</span>'
def info(n, text): return f'<p class="info">{ic(n)}<span>{text}</span></p>'
FIXED = ("is-brand", "확정")
S = {}


# 역할 이름 없음: 모두가 보는 기본 화면(everyone, 큰 글자) + 편집 권한이 있으면 붙는 요소(editor)
FLOW_ROWS = lambda href: f'''
    {row("제주 도착 · 해비치 호텔", "비행기 10:05 출발", href, when("11/20", "금"), ("is-warning", "시간 바뀜"))}
    {row("오후 2시 섭지코지 산책", "저녁은 정하는 중", href, when("11/21", "토"))}
    {row("정하는 중", "11월 10일까지 정해요", href, when("11/22", "일"))}
    {row("호텔에서 나와 집으로", "김포 도착 오후 4시", href, when("11/23", "월"))}'''
flow = lambda href: f'<section class="block is-list">\n    <div class="block-head"><h2 class="h2">여행 흐름</h2></div>{FLOW_ROWS(href)}\n  </section>'
mine = f'''<section class="block is-list">
    {row("내가 챙길 것 3가지", "천천히 준비해도 돼요", "checklist.html", art("luggage"))}
  </section>'''

# ── 홈: 시기별 3가지 모습 (모두 같은 홈) ──
S["home"] = ("홈 · 출발 50일 전", "everyone", "홈 — 시기마다 맨 위가 바뀐다", f'''<main class="page">
  <header class="hero">
    <p class="eyebrow">지은이가 준비하는 여행 · <span class="num">D-51</span></p>
    <h1 class="title">11월 20일부터 3박&nbsp;4일, 제주에 가요</h1>
    <p class="lead">어머니, 아버지, 민수네 가족과 함께예요</p>
    {avatars("mother", "father", "jieun", "minsu", "hayun")}
  </header>
  {flow("day.html")}
  {mine}
</main>''', "text-large")

S["home-d7"] = ("홈 · 출발 3일 전", "everyone", "홈 — 시기마다 맨 위가 바뀐다", f'''<main class="page">
  <header class="hero">
    <p class="eyebrow">제주 가족여행 · <span class="num">D-3</span></p>
    <h1 class="title">금요일 아침 8시 30분, 김포공항에서 만나요</h1>
    <p class="lead">국내선 1층 대한항공 카운터 앞</p>
    <a class="hero-more" href="#">지도에서 보기{CH}</a>
  </header>
  <section class="block">
    <div class="block-head"><h2 class="h2">챙길 것 1가지 남았어요</h2></div>
    {info_art("weather", "제주 낮 17도, 바람이 불어요. 얇은 겉옷을 챙기세요.")}
    <div>
    {todo("신분증", "", "idcard", True)}
    {todo("편한 운동화", "하루 30분 정도 걸어요", "shoe", True)}
    {todo("혈압약 4일치", "", "pill")}
    </div>
  </section>
  {flow("day.html")}
</main>''', "text-large")

S["home-trip"] = ("홈 · 여행 중", "everyone", "홈 — 시기마다 맨 위가 바뀐다", f'''<main class="page">
  <header class="hero">
    <p class="eyebrow">여행 2일째 · 11월 21일 토요일</p>
    <h1 class="title">오늘은 섭지코지에 가요</h1>
    <p class="lead">오후 1시 30분에 호텔 로비에서 모여요</p>
  </header>
  <section class="block is-list">
    <div class="block-head"><h2 class="h2">오늘 하루</h2></div>
    {row("호텔 조식", "1층 식당 · 10시까지", None, when("08:00"), trail="")}
    {row("섭지코지 산책", "차로 40분 · 평지 30분 걷기", "day.html", when("14:00"), FIXED)}
    {row("저녁 · 흑돼지 돈사돈", "예약 6명 · 확인번호 <span class='code'>DS-4821</span>", "day.html", when("18:30"), FIXED)}
  </section>
  <section class="block">
    {info_art("walk", "오늘은 많이 걷지 않아요. 계단 없는 길이에요.")}
  </section>
</main>''', "text-large")

# ── 편집 권한이 있을 때 같은 홈에 붙는 것 ──
S["home-edit"] = ("홈 · 일정을 짜는 사람", "editor", "일정을 짜는 사람에게만 더 보이는 것", f'''<main class="page">
  <header class="hero">
    <p class="eyebrow">제주 가족여행 · <span class="num">D-51</span></p>
    <h1 class="title">정할 게 3개 남았어요</h1>
    <p class="lead">정하기 전까지 가족에게는 '정하는 중'으로 보여요</p>
  </header>
  <section class="block is-list">
    <div class="block-head"><h2 class="h2">정할 것</h2></div>
    {row("11/21 토 저녁", "후보 2곳 · 11월 10일까지", "day-edit.html", art("meal"), ("is-info", "어머니가 궁금해하세요"))}
    {row("11/22 일 하루", "아직 비어 있어요", "day-edit.html", art("calendar"))}
    {row("렌터카 보험", "완전자차 / 일반자차", "item-edit.html", art("car"))}
  </section>
  {flow("day-edit.html")}
  <section class="block is-list">
    {row("할 일 5가지 중 2가지 남았어요", "민수: 렌터카 예약 · 어머니: 혈압약", "tasks.html", art("clipboard"))}
    {row("가족 6명", "일정을 같이 짜는 사람 2명", "family.html", avatars("jieun", "minsu", "mother"))}
    {row("가족에게 보이는 모습", "", "home.html", art("phone"))}
  </section>
</main>''', "")

# ── 날짜 ──
S["day"] = ("날짜 상세", "everyone", "홈에서 들어가는 곳", f'''{appbar("11월 21일 토요일", "home.html")}
<main class="page">
  <section class="block is-list">
    {row("섭지코지 산책", "호텔에서 차로 40분 · 평지 30분", None, when("14:00"), FIXED, trail="")}
    {row("저녁은 지은이가 정하는 중이에요", "11월 10일까지 정해요", None, when("저녁"), trail="")}
  </section>
  <section class="block">
    <p class="block-note">이날이 궁금하면 눌러 주세요. 지은이에게 조용히 표시만 가요.</p>
    <button class="btn secondary">이날 궁금해요</button>
  </section>
</main>''', "text-large")

S["day-edit"] = ("날짜 · 일정을 짜는 사람", "editor", "일정을 짜는 사람에게만 더 보이는 것", f'''{appbar("일정", "home-edit.html")}
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
    {info_art("eyes", "가족에게는 저녁이 '정하는 중'으로 보여요")}
  </section>
</main>''', "")

form = lambda err: f'''{appbar("일정 고치기", "day-edit.html")}
<main class="page">
  <div class="field"><label class="label" for="n">이름</label><input class="input" id="n" value="흑돼지 '돈사돈'"></div>
  <div class="field{' is-error' if err else ''}"><label class="label" for="t">시간</label><input class="input" id="t" value="{'' if err else '11월 21일 토 오후 6시 30분'}" placeholder="시간을 골라 주세요">{'<p class="field-msg">' + ic("alert") + '시간을 정해야 확정할 수 있어요</p>' if err else ''}</div>
  <div class="field"><label class="label" for="m">예약 메모</label><input class="input" id="m" value="6명 · 확인번호 DS-4821"></div>
  <div class="field"><span class="label">가족에게 어떻게 보일까요?</span>
    <div class="seg" role="radiogroup"><button class="seg-item" role="radio" aria-checked="false">정하는 중</button><button class="seg-item is-selected" role="radio" aria-checked="true">확정</button></div>
  </div>
</main>
<div class="cta"><button class="btn primary full">저장</button></div>'''
S["item-edit"] = ("일정 고치기", "editor", "일정을 짜는 사람에게만 더 보이는 것", form(False), "plain has-cta")
S["item-edit--error"] = ("일정 고치기 · 시간 없음", "editor", "일정을 짜는 사람에게만 더 보이는 것", form(True), "plain has-cta")

# ── 준비 ──
S["checklist"] = ("내가 챙길 것", "everyone", "홈에서 들어가는 곳", f'''{appbar("내가 챙길 것", "home.html")}
<main class="page">
  <section class="block is-list">
    {todo("신분증", "", "idcard", True)}
    {todo("편한 운동화", "하루 30분 정도 걸어요", "shoe", True)}
    {todo("혈압약 4일치", "", "pill")}
  </section>
  <section class="block">
    {info_art("umbrella", "우산, 상비약, 충전기는 지은이가 챙겨요")}
  </section>
</main>''', "text-large")

S["tasks"] = ("할 일 나누기", "editor", "일정을 짜는 사람에게만 더 보이는 것", f'''{appbar("할 일", "home-edit.html")}
<main class="page">
  <section class="block is-list">
    <div class="block-head"><h2 class="h2">남은 것 2가지</h2></div>
    {todo("렌터카 예약", "민수 · 11월 1일까지", "car")}
    {todo("혈압약 4일치", "어머니", "pill")}
    <a class="row is-add" href="#">{lead("plus")}<div class="row-main"><p class="row-title">할 일 추가</p></div></a>
  </section>
  <section class="block is-list">
    <div class="block-head"><h2 class="h2">끝낸 것 3가지</h2></div>
    {todo("항공권 예약", "지은", "plane", True)}
    {todo("호텔 예약", "지은", "hotel", True)}
    {todo("신분증 확인", "아버지", "idcard", True)}
  </section>
</main>''', "")

SW = lambda on: f'<button class="switch" role="switch" aria-checked="{"true" if on else "false"}" aria-label="일정 같이 짜기"></button>'
S["family"] = ("가족", "editor", "일정을 짜는 사람에게만 더 보이는 것", f'''{appbar("가족 6명", "home-edit.html")}
<main class="page">
  <section class="block is-list">
    <div class="block-head"><h2 class="h2">일정 같이 짜기</h2></div>
    {row("지은 (나)", "", None, avatar("jieun"), trail=SW(True))}
    {row("민수", "하윤이(7살)와 함께", None, avatar("minsu"), trail=SW(True))}
    {row("어머니", "무릎이 안 좋아 오래 걷기 힘들어요", None, avatar("mother"), trail=SW(False))}
    {row("아버지", "매운 음식은 피해요", None, avatar("father"), trail=SW(False))}
    <a class="row is-add" href="join.html">{lead("plus")}<div class="row-main"><p class="row-title">가족 초대</p></div></a>
  </section>
  <section class="block">
    {info_art("phone", "같이 짜지 않는 가족에게는 확정된 일정만 큰 글자로 보여요")}
  </section>
</main>''', "")

S["join"] = ("초대 링크 첫 화면", "everyone", "처음 들어올 때", f'''<main class="page">
  <header class="hero">
    <p class="eyebrow">제주 가족여행</p>
    <h1 class="title">지은이가 여행에 초대했어요</h1>
    <p class="lead">지은이가 일정을 짜고 있어요. 여행 전까지 필요한 걸 여기서 알려드려요.</p>
    {avatars("jieun", "mother", "father", "minsu", "hayun")}
  </header>
  <section class="block">
    {info_art("calendar", "11월 20일(금) ~ 23일(월), 3박 4일")}
    {info_art("hotel", "해비치 호텔에서 3박")}
    {info_art("plane", "김포 → 제주, 대한항공")}
  </section>
</main>
<div class="cta"><a class="btn primary full" href="home.html">함께하기</a></div>''', "text-large has-cta")

for old in HERE.glob("*.html"): old.unlink()
for sid, (title, role, group, body, cls) in S.items():
    (HERE / f"{sid}.html").write_text(doc(title, body, cls), encoding="utf-8")
PURPOSE = {"join": "초대 링크로 처음 들어오는 화면", "home": "출발 50일 전 — 큰 흐름", "home-d7": "출발 3일 전 — 모이는 곳·챙길 것",
           "home-trip": "여행 중 — 오늘", "day": "날짜 상세 + 궁금해요", "checklist": "내가 챙길 것", "home-edit": "일정 짜는 사람 — 정할 것",
           "day-edit": "날짜별 일정 편집", "item-edit": "일정 고치기", "item-edit--error": "시간 없이 저장하면", "tasks": "할 일 나누기", "family": "일정 같이 짜기 권한"}
POLICIES = {
    "join": ["초대 링크는 7일 뒤 만료", "처음엔 '일정 같이 짜기' 꺼진 상태로 합류"],
    "home": ["확정된 일정만 보인다 — 후보는 '정하는 중' 한 줄", "출발 7일 전부터 맨 위가 모이는 곳, 여행 중엔 '오늘'", "바뀐 항목은 3일 동안 '바뀜' 표시(알림 없음)"],
    "home-d7": ["챙길 것은 본인 몫만", "날씨는 출발지·도착지 중 도착지 기준"],
    "home-trip": ["여행 기간 동안 이 모습", "예약 확인번호는 모두에게 보인다"],
    "day": ["'이날 궁금해요'는 하루 한 번", "누르면 짜는 사람 홈의 정할 것에 표시만 — 알림 없음"],
    "checklist": ["누가 챙길지는 짜는 사람이 정한다", "체크는 본인과 짜는 사람 모두 가능"],
    "home-edit": ["정할 것 = 후보 상태 항목 + 비어 있는 날", "'궁금해요'가 붙은 항목이 위로"],
    "day-edit": ["끌어서 순서 바꾸기", "후보는 여러 개, 확정은 시간대당 하나"],
    "item-edit": ["'확정'으로 저장하는 순간 가족 화면에 반영", "시간이 없으면 확정 불가('정하는 중'으로는 저장 가능)"],
    "item-edit--error": ["시간 없이 '확정'으로 저장하려 할 때"],
    "tasks": ["맡은 사람 1명, 마감일은 선택"],
    "family": ["켜면 후보까지 보이고 고칠 수 있다", "큰 글자는 같이 짜지 않는 사람의 기본값"],
}
BRANCHES = {
    "join": [{"to": "home", "label": "함께하기"}],
    "home": [{"to": "home-edit", "label": "일정을 같이 짜는 사람이면"}],
    "home-edit": [{"to": "day-edit", "label": "정할 것 누르기"}],
    "item-edit": [{"to": "item-edit--error", "label": "시간 없이 확정"}],
}
GROUPS = ["처음 들어올 때", "홈 — 시기마다 맨 위가 바뀐다", "홈에서 들어가는 곳", "일정을 짜는 사람에게만 더 보이는 것"]
BADGES = {"확정": "is-brand", "바뀜": "is-warning", "궁금해하세요": "is-info", "후보": ""}
manifest = {"groups": GROUPS, "badges": BADGES, "screens": [{"id": sid, "file": f"{sid}.html", "title": t, "role": r, "group": g, "purpose": PURPOSE.get(sid, ""),
             "policies": POLICIES.get(sid, []), "branches": BRANCHES.get(sid, [])} for sid, (t, r, g, _, _) in S.items()]}
(HERE / "screens.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(S), "screens")
