"""앱 데이터(JSON) → PC·폰 겸용 웹앱 HTML 한 장 (hyper-design v7 엔진, 2026-09-27).

    python scripts/app.py design/app/app.json                     # → design/app/index.html (체험 투어 셸 포함)
    python scripts/app.py design/cand/c1.json --out design/cand/c1.html   # 후보 미리보기(같은 형식, 화면 1~2장이어도 됨)
    python scripts/app.py design/app                                # 폴더 조립: base.json(screens 뺀 전부 + "order":[화면id…])
                                                                    #   + screens/*.json(파일 하나 = 화면 하나 또는 화면 목록) → app.json → 렌더
    서브 에이전트는 screens/<id>.json 만 쓴다. 메인이 이 명령 한 번으로 합치고 그린다.

HTML 을 직접 길게 쓰지 않는다. 데이터만 쓰면 이 스크립트가 그린다. 한 화면 = 블록 20~40줄.
화면 너비에 따라 저절로 바뀐다(컨테이너 기준): 폭 < 900px = 폰(아래 탭바·한 열), 폭 ≥ 900px = PC(왼쪽 사이드바·본문+보조 열).

== app.json ==
{
  "name": "앱 이름", "tagline": "한 줄 소개",
  "tokens": {...},                       # 아래 tokens
  "roles": [ {"id":"planner","name":"자녀 민지(계획)","nav":["home","plan","todo","family"]},
             {"id":"viewer","name":"아버지(확인)","nav":["v-home","v-todo"]} ],
  "screens": [ {"id":"home","title":"홈","role":"planner","icon":"home","features":["F1","F2"],
                "blocks":[...],            # 본문(폰에서는 이것 다음에 side 가 이어짐)
                "side":[...]}  ],          # PC 에서 오른쪽 보조 열(선택)
  "tour": [ {"screen":"home","role":"planner","device":"m","caption":"D-60 민지가 후보를 적는다"} ],   # 체험 투어 순서
  "decisions": [ {"q":"Q1 제품 방향","answer":"B안 여행 안내서","where":"보는 사람 홈·알림 묶음"} ],
  "assumptions": ["부모님은 폰만 쓴다(가정)"],
  "features": [ {"id":"F1","name":"일정 작성·수정"} ]   # PRD 기능 요구사항 목록(coverage.py 가 검사)
}
screens[].nav 에 없는 화면(상세·작성·빈 상태 등)은 다른 블록의 "to" 로 연결한다. 화면 이동은 #화면id.

== tokens ==
색: bg surface ink muted line accent accentInk warn ok info · radius(px) · font("sans"|"round"|"serif"|"mono") · scale(글자 배율)
density("tight"|"normal"|"airy") · card("flat"|"outline"|"shadow"|"tint") · dark(true)
heading("bold"|"light"|"serif") · headFont(제목·숫자 글꼴, FONTS 이름)
형태: nav(폰) "tabbar" 아래 탭 | "pill" 떠 있는 알약 | "topbar" 위 탭 | "hub" 내비 없음(홈이 타일 허브, 나머지는 뒤로) | "drawer" 메뉴 버튼
      pcnav(PC) "side" 왼쪽 사이드바 | "top" 위 가로 메뉴 | "rail" 아이콘 레일
화면마다 "layout": "stack"(본문+보조 열) | "wide"(넓게, 보조는 아래 줄) | "center"(가운데 좁게 — 읽기·작성) | "split"(PC 왼쪽 목록 + 오른쪽 본문) | "canvas"(지도·달력을 크게, 보조는 떠 있는 패널)
base.json 의 "style": 이 서비스만의 CSS(.app 아래). 블록에 "cls" 를 달면 그 블록만 꾸밀 수 있다.

== blocks (t = 종류, 모든 블록에 "to":"화면id" 를 주면 누를 수 있다) ==
  header    {title, sub?, right?, back?(true면 ← 표시)}
  hero      {img?(URL) | icon?, title?, text?, tone?}          큰 그림·요약 자리. img 없으면 accent 면 + 아이콘
  stats     {items:[{label, value, tone?}]}
  banner    {text, tone:"warn"|"info"|"ok", icon?}
  section   {title, right?}                                       구역 제목
  list      {title?, items:[{title, sub?, right?, badge?, tone?, state?("done"|"todo"|"alert"|"draft"), icon?, img?, to?}]}
  checklist {title?, items:[{title, sub?, checked?, who?}]}
  timeline  {title?, items:[{time, title, sub?, badge?, state?("fixed"|"draft"), who?, to?}]}   확정/후보 구분에 좋음
  cards     {cols?, items:[{title, sub?, img?, icon?, badge?, meta?, to?}]}
  grid      {cols?, items:[{label, value?, icon?, tone?, to?}]}   큰 타일 버튼
  table     {cols:[...], rows:[[...]]}                            PC 에서 쓰기 좋음(폰은 가로 스크롤)
  kanban    {cols:[{title, items:[{title, sub?, badge?}]}]}       열 여러 개(폰은 가로 스크롤)
  buttons   {items:[{label, icon?, primary?, to?}]}
  chips     {items:[text], active?}
  segment   {items:[text], active?}                               탭처럼 생긴 전환
  avatars   {items:[{name, sub?, done?}]}
  progress  {value(0~1), label?}
  calendar  {month, start?(첫날 요일 0=일), days?(30), marks:{"12":"done"|"part"|"miss"|"accent"}, note?}
  form      {fields:[{label, value?, hint?, kind?("text"|"select"|"toggle"|"date")}], submit?}
  steps     {items:[text], active}                                단계 표시
  sheet     {title, blocks:[...]}                                 폰 바텀시트 / PC 오른쪽 패널처럼 보이는 상자
  empty     {icon, title, body?, cta?, to?}
  text      {text, size?("s"|"m"|"l"), tone?}
  quote     {text, who?}                                          메시지·메모
  html      {html}                                                이 서비스만의 특별한 조각(style 과 함께)
  ── 형태 블록 ──
  carousel  {title?, items:[{title, sub?, img?, badge?, to?}]}     폰 가로 넘김 카드 / PC 3열
  map       {pins:[{x,y(0~100), label, tone?}], route?, numbered?, height?}   지도 그림(길·물·핀·경로)
  bignum    {value, label?, sub?}                                 아주 큰 숫자 하나(D-7, 3곳, 12만원)
  poster    {img?, kicker?, title, text?, cta?}                   화면 폭 가득 큰 그림+제목(첫 화면·소개)
  gallery   {items:["gen:…", …]}                                  사진 모음(첫 장 크게)
  chat      {items:[{who?, text, me?}]}                           대화 말풍선
  tabs      {items:[text], active?}                               밑줄 탭
  cols      {cols:[[블록…],[블록…]]}                              PC 다단(폰은 위아래)
icon = Lucide 아이콘 이름(예: "plane","hotel","map-pin","bell","check","calendar","users"). 이모지 쓰지 않는다.
img = 사진 자리. "gen:<영어 키워드,쉼표로 1~3개>:<숫자>" 로 쓰면 그 키워드의 그림을 엔진이 그려 넣는다(외부 서비스 없음, scripts/pics.py).
      사람 = "gen:woman:1" "gen:man:2" "gen:grandma:3" "gen:couple:4" · 장소·음식 = "gen:jeju,beach:3" "gen:koreanfood,restaurant:7" "gen:hotel,room:2".
      숫자를 바꾸면 다른 얼굴·색. 주제와 무관한 그림은 쓰지 않는다. (loremflickr 주소는 막혀서 자동으로 이 그림으로 바뀐다.)
badge 는 짧은 글자("확정","후보","D-3"), tone 은 "warn"|"ok"|"info"|"muted".
그리지 않는 것: 가짜 상태바·폰 테두리·홈 인디케이터·가짜 키보드.
"""
import html as H
import json
import re
import pathlib
import sys

import pics
import shapes

e = H.escape
BASE = {"bg": "#F7F7F5", "surface": "#FFFFFF", "ink": "#1D2320", "muted": "#66706A", "line": "#E2E5E1",
        "accent": "#2F6B57", "accentInk": "#FFFFFF", "warn": "#B8502B", "ok": "#2F8A5B", "info": "#2D6A9F",
        "radius": 12, "font": "sans", "scale": 1, "density": "normal", "card": "outline", "heading": "bold", "nav": "tabbar"}
DARK = {"bg": "#131618", "surface": "#1D2225", "ink": "#EDF0EE", "muted": "#9AA39E", "line": "#2D3438"}
FONTS = {"sans": '"Pretendard Variable",Pretendard,"Malgun Gothic","Apple SD Gothic Neo",sans-serif',
         "round": '"Jua","Pretendard Variable","Malgun Gothic",sans-serif',
         "serif": '"Nanum Myeongjo","Pretendard Variable",serif',
         "mono": '"IBM Plex Sans KR","Pretendard Variable",sans-serif',
         "gowun": '"Gowun Dodum","Pretendard Variable",sans-serif',
         "gowun-batang": '"Gowun Batang","Pretendard Variable",serif',
         "gothic-a1": '"Gothic A1","Pretendard Variable",sans-serif',
         "noto-serif": '"Noto Serif KR","Pretendard Variable",serif',
         "hahmlet": '"Hahmlet","Pretendard Variable",serif',
         "dohyeon": '"Do Hyeon","Pretendard Variable",sans-serif',
         "black-han": '"Black Han Sans","Pretendard Variable",sans-serif',
         "sunflower": '"Sunflower","Pretendard Variable",sans-serif',
         "nanum-pen": '"Nanum Pen Script","Pretendard Variable",cursive',
         "orbit": '"Orbit","Pretendard Variable",sans-serif'}
GF = {"round": "Jua", "serif": "Nanum+Myeongjo:wght@400;700;800", "mono": "IBM+Plex+Sans+KR:wght@400;600",
      "gowun": "Gowun+Dodum", "gowun-batang": "Gowun+Batang:wght@400;700", "gothic-a1": "Gothic+A1:wght@400;600;800",
      "noto-serif": "Noto+Serif+KR:wght@400;600;800", "hahmlet": "Hahmlet:wght@400;600;800", "dohyeon": "Do+Hyeon",
      "black-han": "Black+Han+Sans", "sunflower": "Sunflower:wght@300;500;700", "nanum-pen": "Nanum+Pen+Script", "orbit": "Orbit"}
PRETENDARD = '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/pretendard@1.3.9/dist/web/variable/pretendardvariable.min.css">'


def font_links(t):
    used = [f for f in dict.fromkeys([t.get("font"), t.get("headFont"), "serif" if t.get("heading") == "serif" else None]) if f in GF]
    g = "".join(f"&family={GF[f]}" for f in used)
    return PRETENDARD + (f'<link rel="stylesheet" href="https://fonts.googleapis.com/css2?{g[1:]}&display=swap">' if g else "")


def tok(spec):
    t = dict(BASE)
    if spec.get("tokens", {}).get("dark"):
        t.update(DARK)
    t.update({k: v for k, v in spec.get("tokens", {}).items() if k != "dark"})
    return t


FORM_CSS = r"""
/* ── 형태 층(09-28): 폰 내비 m-* · PC 내비 d-* · 화면 배치 l-* · 형태 블록 ── */
.topnav{display:none;align-items:center;gap:6px;background:var(--bg);position:sticky;top:0;z-index:6;padding:10px var(--pad);border-bottom:1px solid var(--line)}
.topnav .brand{font-weight:800;margin-right:auto} .topnav .menu{display:none;border:0;background:none;color:inherit;padding:6px;cursor:pointer}
.topnav .links{display:flex;gap:4px} .topnav .links a{display:flex;align-items:center;gap:6px;padding:8px 10px;border-radius:calc(var(--r) - 4px);color:var(--muted);white-space:nowrap} .topnav .links a.a{color:var(--accent);font-weight:700}
.m-pill .tabbar{position:fixed;left:50%;transform:translateX(-50%);bottom:14px;border:1px solid var(--line);border-radius:999px;padding:6px 8px;gap:2px;box-shadow:0 8px 24px rgba(0,0,0,.12);justify-content:center}
.m-pill .tabbar a{flex-direction:row;gap:6px;padding:8px 12px;border-radius:999px;min-width:0} .m-pill .tabbar a span{display:none} .m-pill .tabbar a.a{background:var(--accent);color:var(--accent-ink)} .m-pill .tabbar a.a span{display:inline}
.m-topbar .tabbar,.m-hub .tabbar,.m-drawer .tabbar{display:none}
.m-topbar .topnav{display:flex;flex-wrap:wrap;padding-bottom:0} .m-topbar .topnav .links{width:100%;overflow-x:auto;gap:0} .m-topbar .topnav .links a{border-radius:0;padding:10px 12px;border-bottom:2px solid transparent} .m-topbar .topnav .links a svg{display:none} .m-topbar .topnav .links a.a{border-bottom-color:var(--accent)}
.m-hub .topnav{display:flex} .m-hub .topnav .links{display:none}
.m-drawer .topnav{display:flex;flex-wrap:wrap} .m-drawer .topnav .menu{display:block} .m-drawer .topnav .links{display:none;width:100%;flex-direction:column} .m-drawer .topnav.open .links{display:flex}
.m-topbar .body,.m-hub .body,.m-drawer .body{padding-bottom:40px} .m-pill .body{padding-bottom:110px}
@container (min-width:900px){
 .shell .topnav{display:none} .shell .tabbar{display:none}
 .d-top{flex-direction:column} .d-top .side-nav{display:none} .d-top .topnav{display:flex;flex-wrap:nowrap;padding:14px 36px} .d-top .topnav .menu{display:none} .d-top .topnav .links{display:flex;flex-direction:row;width:auto} .d-top .topnav .links a svg{display:inline-block}
 .d-top .topnav .links a{border-bottom:0!important} .d-top .scr.on{margin:0 auto;width:100%}
 .d-rail .side-nav{width:88px;padding:18px 8px;align-items:stretch} .d-rail .side-nav .brand{font-size:.8em;text-align:center;padding:4px 0 14px}
 .d-rail .side-nav a{flex-direction:column;gap:4px;font-size:.72em;text-align:center;padding:10px 4px}
 .scr.on.l-wide{grid-template-columns:minmax(0,1fr);max-width:none} .l-wide .aside{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));padding:0 36px 48px}
 .scr.on.l-center{display:block;max-width:760px;margin:0 auto;width:100%} .l-center .aside{padding:0 36px 48px}
 .scr.on.l-split{grid-template-columns:380px minmax(0,1fr);max-width:none} .l-split .aside{order:-1;padding:32px 24px;border-right:1px solid var(--line);min-height:100vh;background:var(--surface)}
 .scr.on.l-canvas{display:block;position:relative;max-width:none} .l-canvas .aside{position:absolute;right:32px;top:32px;width:360px;padding:18px;background:var(--surface);border-radius:var(--r);box-shadow:0 10px 30px rgba(0,0,0,.12)}
 .l-canvas .map{height:calc(100vh - 80px)!important}
 .car{grid-auto-flow:row!important;grid-template-columns:repeat(3,1fr);overflow:visible!important} .colsb{grid-template-columns:repeat(var(--n),minmax(0,1fr))!important} .gal{grid-template-columns:repeat(4,1fr)!important}
}
.car{display:grid;grid-auto-flow:column;grid-auto-columns:76%;gap:var(--gap);overflow-x:auto;scroll-snap-type:x mandatory;padding-bottom:4px} .car .ci{scroll-snap-align:start}
.map{position:relative;border-radius:var(--r);overflow:hidden;background:color-mix(in srgb,var(--ok) 10%,var(--surface))}
.map svg{position:absolute;inset:0;width:100%;height:100%} .map .rd path{fill:none;stroke:var(--surface);stroke-width:2.2;vector-effect:non-scaling-stroke} .map .w{fill:color-mix(in srgb,var(--info) 22%,var(--surface))}
.map .rt{fill:none;stroke:var(--accent);stroke-width:3;stroke-dasharray:6 5;vector-effect:non-scaling-stroke}
.pin{position:absolute;transform:translate(-50%,-100%);display:flex;flex-direction:column;align-items:center;gap:2px}
.pin i{width:26px;height:26px;border-radius:50% 50% 50% 0;transform:rotate(-45deg);background:var(--accent);color:var(--accent-ink);display:grid;place-items:center;font-style:normal;font-weight:800;font-size:12px;box-shadow:0 2px 6px rgba(0,0,0,.2)}
.pin i em{transform:rotate(45deg);font-style:normal} .pin.p-warn i{background:var(--warn)} .pin.p-ok i{background:var(--ok)} .pin.p-muted i{background:var(--muted)}
.pin span{background:var(--surface);border-radius:6px;padding:1px 6px;font-size:.74em;font-weight:700;white-space:nowrap;box-shadow:0 1px 3px rgba(0,0,0,.12)}
.bign{display:flex;flex-direction:column;gap:2px;padding:6px 0} .bign b{font-size:3.2em;line-height:1;letter-spacing:-.02em;color:var(--accent)} .bign span{font-weight:700}
.poster{position:relative;margin:0 calc(-1 * var(--pad));min-height:320px;display:flex;align-items:flex-end;background:color-mix(in srgb,var(--accent) 16%,var(--surface));overflow:hidden}
.poster img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover} .poster .pc{position:relative;padding:28px var(--pad);width:100%}
.poster.has-img .pc{background:linear-gradient(transparent,rgba(0,0,0,.6));color:#fff} .poster h2{font-size:1.9em;line-height:1.2;margin:4px 0 6px} .poster p{margin:0;opacity:.9} .poster small{font-weight:700;letter-spacing:.04em;opacity:.85}
.gal{display:grid;grid-template-columns:repeat(2,1fr);gap:6px} .gal img{width:100%;aspect-ratio:1;object-fit:cover;border-radius:calc(var(--r) - 4px)} .gal img:first-child{grid-column:span 2;aspect-ratio:2}
.chat{display:flex;flex-direction:column;gap:8px} .bub{max-width:80%;align-self:flex-start;background:var(--surface);border:1px solid var(--line);border-radius:16px 16px 16px 4px;padding:8px 12px}
.bub small{display:block;color:var(--muted);font-size:.78em} .bub.me{align-self:flex-end;background:var(--accent);color:var(--accent-ink);border-color:var(--accent);border-radius:16px 16px 4px 16px}
.utabs{display:flex;gap:18px;border-bottom:1px solid var(--line);overflow-x:auto} .utabs span{padding:8px 0;color:var(--muted);white-space:nowrap} .utabs span.a{color:var(--ink);font-weight:700;border-bottom:2px solid var(--accent)}
.colsb{display:grid;gap:var(--gap);grid-template-columns:1fr} .colc{display:flex;flex-direction:column;gap:var(--gap);min-width:0}
"""


def css(t):
    gap = {"tight": 8, "normal": 12, "airy": 18}.get(t["density"], 12)
    pad = {"tight": 14, "normal": 18, "airy": 24}.get(t["density"], 18)
    card = {"flat": "background:var(--surface)",
            "outline": "background:var(--surface);border:1px solid var(--line)",
            "shadow": "background:var(--surface);box-shadow:0 1px 2px rgba(0,0,0,.05),0 6px 18px rgba(0,0,0,.06)",
            "tint": "background:color-mix(in srgb,var(--accent) 6%,var(--surface))"}.get(t["card"], "")
    hw = {"bold": 800, "light": 500, "serif": 800}.get(t["heading"], 800)
    hf = FONTS[t["headFont"]] if t.get("headFont") in FONTS else (FONTS["serif"] if "serif" in (t["heading"], t["font"]) else "inherit")
    body_font = FONTS["sans"] if t["font"] == "serif" else FONTS.get(t["font"], FONTS["sans"])  # 명조는 제목·숫자 전용(09-28)
    s = float(t["scale"])
    return f"""
:root{{--bg:{t['bg']};--surface:{t['surface']};--ink:{t['ink']};--muted:{t['muted']};--line:{t['line']};--accent:{t['accent']};
--accent-ink:{t['accentInk']};--a1:{t['accent']};--a2:{t.get('accent2') or t['info']};--a3:{t.get('accent3') or t['ok']};--a4:{t.get('accent4') or t['warn']};--warn:{t['warn']};--ok:{t['ok']};--info:{t['info']};--r:{t['radius']}px;--gap:{gap}px;--pad:{pad}px}}
.app{{container-type:inline-size;background:var(--bg);color:var(--ink);font-family:{body_font};font-size:{15*s:.1f}px;line-height:1.5;min-height:100%;-webkit-font-smoothing:antialiased}}
.app *{{box-sizing:border-box}} .app a{{color:inherit;text-decoration:none}}
.shell{{display:flex;flex-direction:column;min-height:100vh}}
.side-nav{{display:none}} .scr{{display:none}} .scr.on{{display:block}}
.body{{flex:1;padding:{20*s:.0f}px var(--pad) 96px;display:flex;flex-direction:column;gap:var(--gap)}} .aside{{display:flex;flex-direction:column;gap:var(--gap);padding:0 var(--pad) 96px;margin-top:calc(-96px + var(--gap))}}
.aside:empty{{display:none}}
.tabbar{{position:sticky;bottom:0;display:flex;justify-content:space-around;background:var(--surface);border-top:1px solid var(--line);padding:8px 0 12px;z-index:5}}
.tabbar a{{display:flex;flex-direction:column;align-items:center;gap:2px;font-size:{11*s:.1f}px;color:var(--muted);min-width:56px}} .tabbar a.a{{color:var(--accent);font-weight:700}}
.topnav{{display:none}}
@container (min-width:900px){{
 .stats.n4{{--n:4}}
 .shell{{flex-direction:row}}
 .side-nav{{display:flex;flex-direction:column;gap:4px;width:232px;flex:none;padding:24px 14px;border-right:1px solid var(--line);background:var(--surface);position:sticky;top:0;height:100vh}}
 .side-nav .brand{{font-weight:800;font-size:1.1em;padding:4px 10px 18px}}
 .side-nav a{{display:flex;gap:10px;align-items:center;padding:10px 12px;border-radius:calc(var(--r) - 2px);color:var(--muted)}} .side-nav a.a{{background:color-mix(in srgb,var(--accent) 10%,transparent);color:var(--accent);font-weight:700}}
 .tabbar{{display:none}}
 .scr.on{{display:grid;grid-template-columns:minmax(0,1fr) 340px;align-items:start;flex:1;max-width:1240px}}
 .scr.on.nos{{grid-template-columns:minmax(0,1fr)}}
 .body{{padding:32px 36px 48px}} .aside{{padding:32px 32px 48px 0;margin:0}}
 .h1{{font-size:{28*s:.0f}px!important}}
 .cards{{grid-template-columns:repeat(var(--cols-d,3),1fr)!important}} .gridb{{grid-template-columns:repeat(var(--cols-d,4),1fr)!important}}
 .sheet{{border:1px solid var(--line)}}
}}
.main{{flex:1;display:flex;flex-direction:column;min-width:0}}
.card{{{card};border-radius:var(--r);padding:{14*s:.0f}px 16px}}
.muted{{color:var(--muted);font-size:.86em}} .h1{{font-family:{hf};font-size:{23*s:.0f}px;font-weight:{hw};margin:0;letter-spacing:-.01em;line-height:1.3}}
.row{{display:flex;align-items:center;gap:10px}} .sp{{flex:1;min-width:0}}
.back{{font-size:.9em;color:var(--muted);display:inline-flex;align-items:center;gap:4px;margin-bottom:4px}}
.hero{{border-radius:var(--r);overflow:hidden;position:relative;min-height:{150*s:.0f}px;display:flex;align-items:flex-end;background:color-mix(in srgb,var(--accent) 14%,var(--surface))}}
.hero img{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}} .hero .ic-big{{position:absolute;right:18px;top:18px;opacity:.5}}
.hero .cap{{position:relative;padding:16px 18px;width:100%}} .hero.has-img .cap{{background:linear-gradient(transparent,rgba(0,0,0,.55));color:#fff}}
.hero .cap b{{display:block;font-size:1.25em}}
.stats{{display:grid;grid-template-columns:repeat(var(--n,3),minmax(0,1fr));gap:var(--gap)}} .stats.n1{{--n:1}} .stats.n2{{--n:2}} .stats.n4{{--n:2}} .stat span{{white-space:nowrap}} .stat b{{font-size:1.45em;display:block;line-height:1.2;font-family:{hf}}} .sec b,.hero .cap b{{font-family:{hf}}}
.banner{{border-radius:var(--r);padding:12px 14px;display:flex;gap:10px;align-items:flex-start}}
.tone-warn{{background:color-mix(in srgb,var(--warn) 12%,var(--surface));color:var(--warn)}}
.tone-info{{background:color-mix(in srgb,var(--info) 10%,var(--surface))}} .tone-ok{{background:color-mix(in srgb,var(--ok) 12%,var(--surface));color:var(--ok)}}
.sec{{display:flex;align-items:baseline;justify-content:space-between;margin-top:6px}} .sec b{{font-size:1.02em}}
.li{{display:flex;align-items:center;gap:12px;padding:{10*s:.0f}px 0;border-bottom:1px solid var(--line)}} .li:last-child{{border:0}}
.li img{{width:48px;height:48px;border-radius:calc(var(--r) - 4px);object-fit:cover;flex:none}}
.dot{{width:30px;height:30px;border-radius:50%;display:grid;place-items:center;flex:none;background:color-mix(in srgb,var(--accent) 10%,var(--surface));color:var(--accent)}}
.st-done .dot{{background:var(--ok);color:#fff}} .st-alert .dot{{background:color-mix(in srgb,var(--warn) 15%,var(--surface));color:var(--warn)}}
.st-draft{{opacity:.92}} .st-draft .dot{{background:transparent;border:1.5px dashed var(--muted);color:var(--muted)}}
.badge{{display:inline-block;font-size:.74em;font-weight:700;padding:2px 8px;border-radius:999px;background:color-mix(in srgb,var(--accent) 12%,var(--surface));color:var(--accent);white-space:nowrap}}
.badge.b-warn{{background:color-mix(in srgb,var(--warn) 14%,var(--surface));color:var(--warn)}} .badge.b-ok{{background:color-mix(in srgb,var(--ok) 14%,var(--surface));color:var(--ok)}}
.badge.b-info{{background:color-mix(in srgb,var(--info) 12%,var(--surface));color:var(--info)}} .badge.b-muted{{background:var(--line);color:var(--muted)}}
.tl{{position:relative;padding-left:24px}} .tl:before{{content:"";position:absolute;left:7px;top:6px;bottom:6px;border-left:2px solid var(--line)}}
.tli{{position:relative;padding:0 0 {12*s:.0f}px}} .tli:before{{content:"";position:absolute;left:-22px;top:6px;width:12px;height:12px;border-radius:50%;background:var(--accent)}}
.tli.draft:before{{background:var(--surface);border:2px dashed var(--muted);width:10px;height:10px}} .tli.draft .ttl{{color:var(--muted)}}
.cards{{display:grid;gap:var(--gap);grid-template-columns:repeat(var(--cols-m,1),1fr)}} .cardi{{overflow:hidden;padding:0!important}}
.cardi img{{width:100%;height:140px;object-fit:cover;display:block}} .cardi .in{{padding:12px 14px}}
.gridb{{display:grid;gap:var(--gap);grid-template-columns:repeat(var(--cols-m,2),1fr)}} .tile{{display:flex;flex-direction:column;gap:6px;padding:16px}} .tile b{{font-size:1.05em}}
.tbl{{overflow-x:auto}} .tbl table{{border-collapse:collapse;width:100%;min-width:520px;font-size:.92em}} .tbl th{{text-align:left;color:var(--muted);font-weight:600;padding:8px 10px;border-bottom:1px solid var(--line)}} .tbl td{{padding:10px;border-bottom:1px solid var(--line)}}
.kan{{display:grid;grid-auto-flow:column;grid-auto-columns:minmax(220px,1fr);gap:var(--gap);overflow-x:auto}} .kcol{{background:color-mix(in srgb,var(--ink) 4%,var(--bg));border-radius:var(--r);padding:10px;display:flex;flex-direction:column;gap:8px}}
.btns{{display:flex;gap:var(--gap);flex-wrap:wrap}} .btn{{flex:1;min-height:{50*s:.0f}px;padding:0 16px;border-radius:var(--r);display:flex;align-items:center;justify-content:center;gap:8px;font-weight:700;border:1.5px solid var(--line);background:var(--surface);cursor:pointer}}
.btn.p{{background:var(--accent);color:var(--accent-ink);border-color:var(--accent)}}
.chips{{display:flex;gap:8px;flex-wrap:wrap}} .chip{{padding:6px 12px;border-radius:999px;border:1px solid var(--line);font-size:.86em;background:var(--surface)}} .chip.a{{background:var(--ink);color:var(--bg);border-color:var(--ink)}}
.seg{{display:flex;background:color-mix(in srgb,var(--ink) 6%,var(--bg));border-radius:calc(var(--r) - 2px);padding:3px}} .seg span{{flex:1;text-align:center;padding:8px;border-radius:calc(var(--r) - 4px);font-size:.9em;color:var(--muted)}} .seg span.a{{background:var(--surface);color:var(--ink);font-weight:700;box-shadow:0 1px 3px rgba(0,0,0,.08)}}
.av{{display:flex;gap:14px;flex-wrap:wrap}} .av div{{display:flex;flex-direction:column;align-items:center;gap:4px;font-size:.8em}} .av i{{width:46px;height:46px;border-radius:50%;display:grid;place-items:center;background:var(--line);font-weight:700;font-style:normal;font-size:1.1em}} .av .d i{{background:var(--accent);color:var(--accent-ink)}}
.bar{{height:10px;border-radius:5px;background:var(--line);overflow:hidden}} .bar i{{display:block;height:100%;background:var(--accent)}}
.cal{{display:grid;grid-template-columns:repeat(7,1fr);gap:4px;text-align:center;font-size:.84em}} .cal span{{padding:7px 0;border-radius:8px}} .cal .wd{{color:var(--muted);font-size:.8em}}
.m-done{{background:var(--ok);color:#fff}} .m-part{{background:color-mix(in srgb,var(--ok) 30%,var(--surface))}} .m-miss{{background:color-mix(in srgb,var(--warn) 22%,var(--surface))}} .m-accent{{background:var(--accent);color:var(--accent-ink);font-weight:700}}
.fld{{display:grid;gap:5px;margin-bottom:12px}} .fld .in{{border:1px solid var(--line);border-radius:calc(var(--r) - 4px);padding:11px 12px;background:var(--surface);display:flex;justify-content:space-between}} .fld .in.hint{{color:var(--muted)}}
.tg{{width:40px;height:24px;border-radius:12px;background:var(--accent);position:relative}} .tg:after{{content:"";position:absolute;right:3px;top:3px;width:18px;height:18px;border-radius:50%;background:#fff}}
.steps{{display:flex;gap:6px;align-items:center;font-size:.82em;color:var(--muted);flex-wrap:wrap}} .steps .a{{color:var(--accent);font-weight:700}} .steps .d{{color:var(--ink)}}
.sheet{{border-radius:var(--r) var(--r) 0 0;background:var(--surface);box-shadow:0 -6px 24px rgba(0,0,0,.08);padding:16px;display:flex;flex-direction:column;gap:var(--gap)}}
.empty{{text-align:center;display:grid;gap:8px;justify-items:center;padding:36px 12px}} .empty .ic{{width:64px;height:64px;border-radius:50%;display:grid;place-items:center;background:color-mix(in srgb,var(--accent) 10%,var(--surface));color:var(--accent)}}
.quote{{border-radius:var(--r);padding:12px 14px;background:color-mix(in srgb,var(--ink) 5%,var(--bg))}}
.t-s{{font-size:.84em}} .t-l{{font-size:1.2em;font-weight:700}}
.lk{{cursor:pointer}} .lk:hover{{filter:brightness(.97)}}
svg.lucide{{width:1.15em;height:1.15em;stroke-width:1.9;vertical-align:-.2em}} .dot svg.lucide{{width:16px;height:16px}} .hero .ic-big svg{{width:56px;height:56px}} .empty svg{{width:28px;height:28px}}
""" + FORM_CSS + shapes.css()


def icname(name):
    """Lucide 이름은 kebab-case. PascalCase('CalendarRange')로 쓰면 두 단어 이상 아이콘이 빈칸이 되므로 바꿔 준다(09-28)."""
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Za-z])(?=[0-9])", "-", (name or "").strip()).lower().replace("_", "-").replace(" ", "-")


def ic(name):
    return f'<i data-lucide="{e(icname(name))}"></i>' if name else ""


def link(b):
    return f' href="#{e(b["to"])}"' if b.get("to") else ""


def wrap(b, inner, tag_cls=""):
    if b.get("to"):
        return f'<a class="lk {tag_cls}" href="#{e(b["to"])}">{inner}</a>'
    return f'<div class="{tag_cls}">{inner}</div>' if tag_cls else inner


def badge(x, tone=None):
    return f'<span class="badge {"b-"+tone if tone else ""}">{e(str(x))}</span>' if x else ""


def muted(x):
    return f'<div class="muted">{e(str(x))}</div>' if x else ""


def block(b):
    h = _block(b)
    return f'<div class="{e(b["cls"])}">{h}</div>' if b.get("cls") else h


def _block(b):
    t = b.get("t")
    if t == "header":
        back = f'<a class="back" href="#{e(b["to"])}">{ic("chevron-left")}뒤로</a>' if b.get("back") and b.get("to") else (
            f'<span class="back">{ic("chevron-left")}뒤로</span>' if b.get("back") else "")
        return f'<div>{back}<div class="row"><div class="sp"><h1 class="h1">{e(b["title"])}</h1>{muted(b.get("sub"))}</div><span class="muted">{e(b.get("right", ""))}</span></div></div>'
    if t == "hero":
        img = f'<img src="{e(pics.src(b["img"]))}" alt="">' if b.get("img") else f'<span class="ic-big">{ic(b.get("icon", ""))}</span>'
        cap = f'<div class="cap"><b>{e(b.get("title", ""))}</b>{e(b.get("text", ""))}</div>'
        return wrap(b, f'<div class="hero {"has-img" if b.get("img") else ""}">{img}{cap}</div>')
    if t == "stats":
        n = min(len(b["items"]), 4) or 1
        return f'<div class="stats n{n}">' + "".join(
            f'<div class="card stat {"tone-"+i["tone"] if i.get("tone") else ""}"><b>{e(str(i["value"]))}</b><span class="muted">{e(i["label"])}</span></div>' for i in b["items"]) + "</div>"
    if t == "banner":
        return wrap(b, f'<div class="banner tone-{b.get("tone", "info")}">{ic(b.get("icon", "info"))}<div>{e(b["text"])}</div></div>')
    if t == "section":
        return f'<div class="sec"><b>{e(b["title"])}</b><span class="muted">{e(b.get("right", ""))}</span></div>'
    if t in ("list", "checklist"):
        out = ""
        for i in b["items"]:
            st = "done" if i.get("checked") or i.get("state") == "done" else i.get("state", "todo")
            lead = f'<img src="{e(pics.src(i["img"]))}" alt="">' if i.get("img") else f'<span class="dot">{ic("check" if st == "done" else (i.get("icon") or ("alert-circle" if st == "alert" else "circle")))}</span>'
            subline = " · ".join(x for x in (i.get("sub"), i.get("who")) if x)
            inner = f'{lead}<div class="sp"><div>{e(i["title"])}</div>{muted(subline)}</div>{badge(i.get("badge"), i.get("tone"))}<span class="muted">{e(i.get("right", ""))}</span>'
            out += f'<a class="li lk st-{st}" href="#{e(i["to"])}">{inner}</a>' if i.get("to") else f'<div class="li st-{st}">{inner}</div>'
        return f'<div class="card">{muted(b.get("title"))}{out}</div>'
    if t == "timeline":
        its = ""
        for i in b["items"]:
            inner = f'<div class="muted">{e(i["time"])}{" · "+e(i["who"]) if i.get("who") else ""}</div><div class="row"><span class="ttl sp">{e(i["title"])}</span>{badge(i.get("badge"), i.get("tone") or ("muted" if i.get("state") == "draft" else None))}</div>{muted(i.get("sub"))}'
            cls = "tli draft" if i.get("state") == "draft" else "tli"
            its += f'<a class="{cls} lk" style="display:block" href="#{e(i["to"])}">{inner}</a>' if i.get("to") else f'<div class="{cls}">{inner}</div>'
        return f'<div class="card">{muted(b.get("title"))}<div class="tl" style="margin-top:8px">{its}</div></div>'
    if t == "cards":
        cols = b.get("cols", 3)
        its = ""
        for i in b["items"]:
            top = f'<img src="{e(pics.src(i["img"]))}" alt="">' if i.get("img") else ""
            inner = f'{top}<div class="in"><div class="row"><b class="sp">{ic(i.get("icon", ""))} {e(i["title"])}</b>{badge(i.get("badge"), i.get("tone"))}</div>{muted(i.get("sub"))}{muted(i.get("meta"))}</div>'
            its += f'<a class="card cardi lk" href="#{e(i["to"])}">{inner}</a>' if i.get("to") else f'<div class="card cardi">{inner}</div>'
        return f'<div class="cards" style="--cols-m:{1 if cols > 2 else cols};--cols-d:{cols}">{its}</div>'
    if t == "grid":
        cols = b.get("cols", 3)
        its = ""
        for i in b["items"]:
            inner = f'<span style="color:var(--accent)">{ic(i.get("icon", ""))}</span><b>{e(i["label"])}</b>{muted(i.get("value"))}'
            cls = f'card tile {"tone-"+i["tone"] if i.get("tone") else ""}'
            its += f'<a class="{cls} lk" href="#{e(i["to"])}">{inner}</a>' if i.get("to") else f'<div class="{cls}">{inner}</div>'
        return f'<div class="gridb" style="--cols-m:{min(cols, 2)};--cols-d:{cols}">{its}</div>'
    if t == "table":
        th = "".join(f"<th>{e(str(c))}</th>" for c in b["cols"])
        tr = "".join("<tr>" + "".join(f"<td>{e(str(c))}</td>" for c in r) + "</tr>" for r in b["rows"])
        return f'<div class="card tbl"><table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>'
    if t == "kanban":
        cols = "".join(f'<div class="kcol"><div class="row"><b class="sp">{e(c["title"])}</b><span class="muted">{len(c["items"])}</span></div>' + "".join(
            f'<div class="card" style="padding:10px 12px"><div class="row"><span class="sp">{e(i["title"])}</span>{badge(i.get("badge"), i.get("tone"))}</div>{muted(i.get("sub"))}</div>' for i in c["items"]) + "</div>" for c in b["cols"])
        return f'<div class="kan">{cols}</div>'
    if t == "buttons":
        return '<div class="btns">' + "".join(
            f'<a class="btn {"p" if i.get("primary") else ""}"{link(i)}>{ic(i.get("icon", ""))}{e(i["label"])}</a>' for i in b["items"]) + "</div>"
    if t == "chips":
        return '<div class="chips">' + "".join(f'<span class="chip {"a" if x == b.get("active") else ""}">{e(x)}</span>' for x in b["items"]) + "</div>"
    if t == "segment":
        return '<div class="seg">' + "".join(f'<span class="{"a" if x == b.get("active") else ""}">{e(x)}</span>' for x in b["items"]) + "</div>"
    if t == "avatars":
        return '<div class="av">' + "".join(
            f'<div class="{"d" if i.get("done") else ""}"><i>{e(i["name"][:1])}</i><span>{e(i["name"])}</span>{muted(i.get("sub"))}</div>' for i in b["items"]) + "</div>"
    if t == "progress":
        return f'<div><div class="row"><span class="muted sp">{e(b.get("label", ""))}</span><span class="muted">{int(100*b["value"])}%</span></div><div class="bar"><i style="width:{int(100*b["value"])}%"></i></div></div>'
    if t == "calendar":
        start, days = int(b.get("start", 0)), int(b.get("days", 30))
        wd = "".join(f'<span class="wd">{d}</span>' for d in "일월화수목금토")
        cells = "<span></span>" * start + "".join(f'<span class="m-{b.get("marks", {}).get(str(d), "")}">{d}</span>' for d in range(1, days + 1))
        return f'<div class="card"><div class="row"><b class="sp">{e(b.get("month", ""))}</b>{muted(b.get("note"))}</div><div class="cal" style="margin-top:8px">{wd}{cells}</div></div>'
    if t == "form":
        f = ""
        for x in b["fields"]:
            k = x.get("kind", "text")
            right = '<span class="tg"></span>' if k == "toggle" else (ic("chevron-down") if k == "select" else (ic("calendar") if k == "date" else ""))
            val = x.get("value") or x.get("hint", "")
            f += f'<div class="fld"><span class="muted">{e(x["label"])}</span><div class="in {"" if x.get("value") else "hint"}"><span>{e(val)}</span>{right}</div></div>'
        sub = f'<div class="btns"><a class="btn p"{link(b)}>{e(b["submit"])}</a></div>' if b.get("submit") else ""
        return f'<div class="card">{f}{sub}</div>'
    if t == "steps":
        items, a = b["items"], b.get("active", 0)
        a = items.index(a) if isinstance(a, str) and a in items else int(a) if not isinstance(a, str) else 0
        return '<div class="steps">' + f' {ic("chevron-right")} '.join(f'<span class="{"a" if n == a else ("d" if n < a else "")}">{n+1}. {e(x)}</span>' for n, x in enumerate(items)) + "</div>"
    if t == "sheet":
        return f'<div class="sheet"><b>{e(b.get("title", ""))}</b>{"".join(block(x) for x in b.get("blocks", []))}</div>'
    if t == "empty":
        c = f'<a class="btn p" style="flex:none"{link(b)}>{e(b["cta"])}</a>' if b.get("cta") else ""
        return f'<div class="card empty"><span class="ic">{ic(b.get("icon", "inbox"))}</span><b>{e(b["title"])}</b>{muted(b.get("body"))}{c}</div>'
    if t == "text":
        return f'<div class="t-{b.get("size", "m")} {"tone-"+b["tone"] if b.get("tone") else ""}">{e(b["text"])}</div>'
    if t == "quote":
        return f'<div class="quote">{e(b["text"])}{muted("— " + b["who"]) if b.get("who") else ""}</div>'
    if t == "html":  # 직접 그린 조각·화면 — src="gen:…" 도 그림으로 바꾼다
        return re.sub(r'src="(gen:[^"]+)"', lambda m: f'src="{e(pics.src(m.group(1)))}"', b["html"])
    # ── 형태 블록 (09-28, 자유도) ──
    if t == "art":
        return wrap(b, shapes.art(b, e))
    if t == "carousel":
        its = ""
        for i in b["items"]:
            im = f'<img src="{e(pics.src(i["img"]))}" alt="">' if i.get("img") else ""
            its += (f'<a class="card cardi ci"{link(i)}>{im}<div class="in"><div class="row"><b class="sp">{e(i["title"])}</b>'
                    f'{badge(i.get("badge"), i.get("tone"))}</div>{muted(i.get("sub"))}</div></a>')
        ttl = f'<div class="sec"><b>{e(b["title"])}</b><span class="muted">{e(b.get("right", ""))}</span></div>' if b.get("title") else ""
        return f'<div>{ttl}<div class="car">{its}</div></div>'
    if t == "map":
        return map_svg(b)
    if t == "bignum":
        return wrap(b, f'<div class="bign"><b>{e(str(b["value"]))}</b><span>{e(b.get("label", ""))}</span>{muted(b.get("sub"))}</div>')
    if t == "poster":
        img = f'<img src="{e(pics.src(b["img"]))}" alt="">' if b.get("img") else ""
        cta = f'<span class="btn p" style="flex:none;display:inline-flex;margin-top:12px">{e(b["cta"])}</span>' if b.get("cta") else ""
        return wrap(b, f'<div class="poster{" has-img" if img else ""}">{img}<div class="pc"><small>{e(b.get("kicker", ""))}</small><h2>{e(b.get("title", ""))}</h2><p>{e(b.get("text", ""))}</p>{cta}</div></div>')
    if t == "gallery":
        return '<div class="gal">' + "".join(f'<img src="{e(pics.src(x if isinstance(x, str) else x.get("img", "")))}" alt="">' for x in b["items"]) + "</div>"
    if t == "chat":
        out = ""
        for i in b["items"]:
            who = "" if i.get("me") else f'<small>{e(i.get("who", ""))}</small>'
            out += f'<div class="bub{" me" if i.get("me") else ""}">{who}<div>{e(i["text"])}</div></div>'
        return f'<div class="chat">{out}</div>'
    if t == "tabs":
        return '<div class="utabs">' + "".join(f'<span class="{"a" if k == b.get("active", 0) else ""}">{e(x)}</span>' for k, x in enumerate(b["items"])) + "</div>"
    if t == "cols":
        return f'<div class="colsb" style="--n:{len(b["cols"])}">' + "".join(f'<div class="colc">{"".join(block(x) for x in c)}</div>' for c in b["cols"]) + "</div>"
    return f"<!-- 모르는 블록 {e(str(t))} -->"


def map_svg(b):
    """지도 자리 그림 — 실제 지도가 아니라 길·물·핀을 그린 일러스트. pins x,y 는 0~100(%)."""
    import hashlib
    r = int(hashlib.md5(json.dumps(b.get("pins", []), ensure_ascii=False).encode()).hexdigest()[:8], 16)
    roads = "".join(f'<path d="M{(r >> i) % 100 - 10},{-5} C{(r >> (i + 3)) % 100},{40} {(r >> (i + 5)) % 100},{60} {(r >> (i + 7)) % 100 + 5},105" />' for i in range(0, 12, 3))
    roads += "".join(f'<path d="M-5,{(r >> i) % 100} C30,{(r >> (i + 2)) % 100} 70,{(r >> (i + 4)) % 100} 105,{(r >> (i + 6)) % 100}" />' for i in range(1, 10, 4))
    water = f'<path d="M{60 + r % 20},-5 C{50 + r % 30},30 {80 + r % 15},55 {70 + r % 20},105 L105,105 L105,-5 Z" class="w"/>' if r % 3 else ""
    pins = b.get("pins", [])
    route = ""
    if b.get("route") and len(pins) > 1:
        route = '<polyline class="rt" points="' + " ".join(f'{p["x"]},{p["y"]}' for p in pins) + '"/>'
    ps = "".join(f'<div class="pin{" p-" + p["tone"] if p.get("tone") else ""}" style="left:{p["x"]}%;top:{p["y"]}%"><i><em>{k + 1 if b.get("numbered") else ""}</em></i><span>{e(p.get("label", ""))}</span></div>' for k, p in enumerate(pins))
    h = b.get("height", 240)
    svg = f'<svg viewBox="0 0 100 100" preserveAspectRatio="none">{water}<g class="rd">{roads}</g>{route}</svg>'
    return wrap(b, f'<div class="map" style="height:{h}px">{svg}{ps}</div>')


def screens_html(spec):
    roles = spec.get("roles") or [{"id": "all", "name": "", "nav": [s["id"] for s in spec["screens"]][:5]}]
    by_id = {s["id"]: s for s in spec["screens"]}
    out = []
    for s in spec["screens"]:
        role = s.get("role") or roles[0]["id"]
        r = next((x for x in roles if x["id"] == role), roles[0])
        nav_ids = [n for n in r.get("nav", []) if n in by_id]
        def navlinks(cls):
            return "".join(f'<a class="{"a" if n == s["id"] or n == s.get("navActive") else ""}" href="#{e(n)}">{ic(by_id[n].get("icon", "circle"))}<span>{e(by_id[n].get("navLabel") or by_id[n]["title"])}</span></a>' for n in nav_ids)
        side = "".join(block(b) for b in s.get("side", []))
        out.append(
            f'<section class="scr l-{e(s.get("layout", "stack"))} {"" if side else "nos"}" id="s-{e(s["id"])}" data-role="{e(role)}">'
            f'<div class="body">{"".join(block(b) for b in s.get("blocks", []))}</div><div class="aside">{side}</div></section>')
    # 역할별 내비는 화면마다 달라서 JS 가 바꾼다
    navdata = {r["id"]: [{"id": n, "label": by_id[n].get("navLabel") or by_id[n]["title"], "icon": icname(by_id[n].get("icon") or "circle")} for n in r.get("nav", []) if n in by_id] for r in roles}
    return "".join(out), navdata, roles


APP_JS = r"""
const NAV=__NAV__, ROLE_OF=__ROLE_OF__, FIRST=__FIRST__, NAME=__NAME__;
function navHtml(role,cur){return (NAV[role]||[]).map(n=>`<a class="${n.id===cur?'a':''}" href="#${n.id}"><i data-lucide="${n.icon}"></i><span>${n.label}</span></a>`).join('')}
function show(){let id=location.hash.slice(1)||FIRST; if(!document.getElementById('s-'+id)) id=FIRST;
 document.querySelectorAll('.scr').forEach(s=>s.classList.toggle('on',s.id==='s-'+id));
 const role=ROLE_OF[id]; const act=(NAV[role]||[]).some(n=>n.id===id)?id:(window.__lastNav&&window.__lastNav[role])||'';
 if((NAV[role]||[]).some(n=>n.id===id)){window.__lastNav=window.__lastNav||{};window.__lastNav[role]=id}
 document.querySelector('.side-nav').innerHTML=`<div class="brand">${NAME}</div>`+navHtml(role,act);
 document.querySelector('.tabbar').innerHTML=navHtml(role,act);
 const first=(NAV[role]||[])[0]; const tn=document.querySelector('.topnav'); tn.classList.remove('open');
 tn.innerHTML=`<a class="brand" href="#${first?first.id:FIRST}">${NAME}</a><button class="menu" onclick="this.parentNode.classList.toggle('open')"><i data-lucide="menu"></i></button><div class="links">${navHtml(role,act)}</div>`;
 if(window.lucide) lucide.createIcons(); window.scrollTo(0,0);
 if(window.parent!==window) try{parent.postMessage({screen:id,role},'*')}catch(e){} }
addEventListener('hashchange',show); addEventListener('DOMContentLoaded',show);
"""


def app_doc(spec, bare=False):
    t = tok(spec)
    body, navdata, roles = screens_html(spec)
    role_of = {s["id"]: s.get("role") or roles[0]["id"] for s in spec["screens"]}
    js = (APP_JS.replace("__NAV__", json.dumps(navdata, ensure_ascii=False)).replace("__ROLE_OF__", json.dumps(role_of))
          .replace("__FIRST__", json.dumps(spec["screens"][0]["id"])).replace("__NAME__", json.dumps(e(spec.get("name", "")), ensure_ascii=False)))
    return (f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{e(spec.get("name", "앱"))}</title>{font_links(t)}<style>html,body{{margin:0;height:100%}}{css(t)}{spec.get("style", "")}</style>'
            f'<script src="https://cdn.jsdelivr.net/npm/lucide@0.469.0/dist/umd/lucide.min.js"></script></head>'
            f'<body class="app"><div class="shell m-{e(t.get("nav", "tabbar"))} d-{e(t.get("pcnav", "side"))}"><nav class="side-nav"></nav><div class="main"><nav class="topnav"></nav>{body}<nav class="tabbar"></nav></div></div><script>{js}</script></body></html>')


TOUR_CSS = """
:root{--c-bg:#EEEFEC;--c-ink:#1B1F1D;--c-mut:#646B67;--c-line:#D6D9D5;--c-card:#fff;--c-acc:#1B1F1D}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--c-bg:#141617;--c-ink:#E9ECEA;--c-mut:#9BA29E;--c-line:#2C3134;--c-card:#1C2022;--c-acc:#E9ECEA}}
*{box-sizing:border-box} body{margin:0;background:var(--c-bg);color:var(--c-ink);font-family:"Pretendard Variable",Pretendard,"Malgun Gothic",sans-serif}
header.top{display:flex;flex-wrap:wrap;gap:12px;align-items:center;padding:14px 20px;border-bottom:1px solid var(--c-line);position:sticky;top:0;background:var(--c-bg);z-index:3}
header.top h1{font-size:17px;margin:0} header.top .tag{color:var(--c-mut);font-size:13px}
.ctl{display:flex;gap:4px;background:var(--c-card);border:1px solid var(--c-line);border-radius:10px;padding:3px}
.ctl button{border:0;background:none;padding:7px 12px;border-radius:7px;font:inherit;font-size:13px;color:var(--c-mut);cursor:pointer}
.ctl button.a{background:var(--c-acc);color:var(--c-bg);font-weight:700}
.wrap{display:grid;grid-template-columns:minmax(0,1fr) 320px;gap:20px;padding:20px;align-items:start}
@media (max-width:1100px){.wrap{grid-template-columns:1fr}}
.stage{display:flex;justify-content:center} .frame{background:#fff;border-radius:18px;overflow:hidden;box-shadow:0 10px 40px rgba(0,0,0,.12);transition:width .25s}
.frame iframe{border:0;display:block;width:100%;height:100%}
.m .frame{width:390px;height:844px;max-width:100%} .d .frame{width:100%;max-width:1280px;height:800px}
aside.panel{background:var(--c-card);border:1px solid var(--c-line);border-radius:14px;padding:16px;display:flex;flex-direction:column;gap:14px;font-size:14px;line-height:1.55}
aside.panel h2{font-size:14px;margin:0 0 6px} .muted{color:var(--c-mut);font-size:13px}
.tourcap{font-size:15px;font-weight:600} .tnav{display:flex;gap:8px} .tnav button{flex:1;padding:9px;border-radius:9px;border:1px solid var(--c-line);background:none;color:inherit;font:inherit;cursor:pointer}
ol.steps{margin:0;padding-left:18px} ol.steps li{cursor:pointer;padding:2px 0} ol.steps li.a{font-weight:700}
.dec{border-top:1px solid var(--c-line);padding-top:8px} .dec b{display:block} table.cov{width:100%;border-collapse:collapse;font-size:13px} table.cov td{border-top:1px solid var(--c-line);padding:5px 4px;vertical-align:top}
.screens{display:flex;flex-wrap:wrap;gap:6px} .screens a{font-size:12px;padding:4px 8px;border:1px solid var(--c-line);border-radius:6px;color:inherit;text-decoration:none;cursor:pointer}
@media (max-width:600px){.wrap{padding:12px} .m .frame{width:100%;height:760px}}
"""

TOUR_JS = r"""
const TOUR=__TOUR__, ROLE_OF=__ROLE_OF__, TITLES=__TITLES__; let i=0, dev='m';
const fr=document.getElementById('f');
function setDev(d){dev=d;document.querySelector('.stage').className='stage '+d;document.querySelectorAll('[data-dev]').forEach(b=>b.classList.toggle('a',b.dataset.dev===d))}
function go(id){fr.contentWindow.location.hash=id}
function step(n){if(!TOUR.length)return; i=(n+TOUR.length)%TOUR.length; const s=TOUR[i]; if(s.device) setDev(s.device); go(s.screen);
 document.getElementById('cap').textContent=(i+1)+' / '+TOUR.length+' · '+s.caption;
 document.querySelectorAll('ol.steps li').forEach((li,k)=>li.classList.toggle('a',k===i))}
function role(r){const first=Object.keys(ROLE_OF).find(k=>ROLE_OF[k]===r); if(first) go(first);
 document.querySelectorAll('[data-role]').forEach(b=>b.classList.toggle('a',b.dataset.role===r))}
addEventListener('message',ev=>{if(ev.data&&ev.data.role) document.querySelectorAll('[data-role]').forEach(b=>b.classList.toggle('a',b.dataset.role===ev.data.role));
 if(ev.data&&ev.data.screen) document.getElementById('cur').textContent=TITLES[ev.data.screen]||ev.data.screen});
fr.addEventListener('load',()=>{ if(TOUR.length) step(0) });
"""


def tour_doc(spec, app_file):
    roles = spec.get("roles") or []
    by_id = {s["id"]: s for s in spec["screens"]}
    role_of = {s["id"]: s.get("role") or (roles[0]["id"] if roles else "all") for s in spec["screens"]}
    tour = spec.get("tour") or [{"screen": s["id"], "caption": s["title"]} for s in spec["screens"]]
    steps = "".join(f'<li onclick="step({n})">{e(x.get("caption", ""))}</li>' for n, x in enumerate(tour))
    rbtn = "".join(f'<button data-role="{e(r["id"])}" onclick="role(\'{e(r["id"])}\')">{e(r["name"])}</button>' for r in roles)
    decs = "".join(f'<div class="dec"><b>{e(d.get("q", ""))}</b><span>답: {e(str(d.get("answer", "")))}</span><div class="muted">반영: {e(str(d.get("where", "")))}</div></div>' for d in spec.get("decisions", []))
    assum = "".join(f"<li>{e(a)}</li>" for a in spec.get("assumptions", []))
    cov = ""
    for f in spec.get("features", []):
        ss = [s for s in spec["screens"] if f["id"] in s.get("features", [])]
        cov += f'<tr><td>{e(f["id"])}</td><td>{e(f["name"])}<div class="screens">' + "".join(f'<a onclick="go(\'{e(s["id"])}\')">{e(s["title"])}</a>' for s in ss) + "</div></td></tr>"
    allscr = "".join(f'<a onclick="go(\'{e(s["id"])}\')">{e(s["title"])}</a>' for s in spec["screens"])
    js = (TOUR_JS.replace("__TOUR__", json.dumps(tour, ensure_ascii=False)).replace("__ROLE_OF__", json.dumps(role_of))
          .replace("__TITLES__", json.dumps({k: v["title"] for k, v in by_id.items()}, ensure_ascii=False)))
    return f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(spec.get("name", "앱"))} 둘러보기</title><link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/pretendard@1.3.9/dist/web/variable/pretendardvariable.min.css"><style>{TOUR_CSS}</style></head><body>
<header class="top"><div><h1>{e(spec.get("name", ""))}</h1><div class="tag">{e(spec.get("tagline", ""))}</div></div><span style="flex:1"></span>
<div class="ctl">{rbtn}</div><div class="ctl"><button data-dev="m" class="a" onclick="setDev('m')">폰</button><button data-dev="d" onclick="setDev('d')">PC</button></div></header>
<div class="wrap"><div class="stage m"><div class="frame"><iframe id="f" src="{e(app_file)}" title="앱 화면"></iframe></div></div>
<aside class="panel"><div><h2>따라가 보기</h2><div class="tourcap" id="cap"></div><div class="tnav" style="margin-top:8px"><button onclick="step(i-1)">이전</button><button onclick="step(i+1)">다음</button></div>
<ol class="steps" style="margin-top:10px">{steps}</ol></div>
<div><h2>지금 화면</h2><div id="cur" class="muted"></div><div class="screens" style="margin-top:6px">{allscr}</div></div>
<div><h2>이 화면은 이렇게 정해졌어요</h2>{decs or '<div class="muted">-</div>'}</div>
<div><h2>가정한 것</h2><ul class="muted" style="margin:0;padding-left:18px">{assum}</ul></div>
<div><h2>기능 요구사항 → 화면</h2><table class="cov">{cov}</table></div></aside></div>
<script>{js}</script></body></html>'''


def main():
    args = sys.argv[1:]
    src = pathlib.Path(args[0])
    if src.is_dir():
        base = json.loads((src / "base.json").read_text(encoding="utf-8"))
        scr = []
        for f in sorted((src / "screens").glob("*.json")):
            x = json.loads(f.read_text(encoding="utf-8"))
            scr += x if isinstance(x, list) else [x]
        order = base.pop("order", [])
        rank = {k: n for n, k in enumerate(order)}
        scr.sort(key=lambda s: rank.get(s["id"], len(rank)))
        base["screens"] = scr
        if (src / "style.css").exists():  # 디자인 시스템 CSS(09-28)
            base["style"] = (src / "style.css").read_text(encoding="utf-8") + "\n" + base.get("style", "")
        for s in scr:  # 직접 그린 화면: screens/<id>.html
            h = src / "screens" / f'{s["id"]}.html'
            if s.get("htmlFile"):
                h = src / "screens" / s["htmlFile"]
            if h.exists():
                s["blocks"] = [{"t": "html", "html": h.read_text(encoding="utf-8")}] + [b for b in s.get("blocks", []) if b.get("t") != "html"]
        src = src / "app.json"
        src.write_text(json.dumps(base, ensure_ascii=False, indent=1), encoding="utf-8")
    spec = json.loads(src.read_text(encoding="utf-8"))
    if spec.get("styleFile"):  # 후보 미리보기: 같은 폴더의 CSS
        spec["style"] = (src.parent / spec["styleFile"]).read_text(encoding="utf-8") + "\n" + spec.get("style", "")
    for s in spec["screens"]:
        if s.get("htmlFile") and (src.parent / s["htmlFile"]).exists():
            s["blocks"] = [{"t": "html", "html": (src.parent / s["htmlFile"]).read_text(encoding="utf-8")}] + [b for b in s.get("blocks", []) if b.get("t") != "html"]
    if "--out" in args:
        out = pathlib.Path(args[args.index("--out") + 1])
        out.write_text(app_doc(spec), encoding="utf-8")
        print(out)
        return
    d = src.parent
    (d / "app.html").write_text(app_doc(spec), encoding="utf-8")
    (d / "index.html").write_text(tour_doc(spec, "app.html"), encoding="utf-8")
    print(d / "index.html", d / "app.html", f"화면 {len(spec['screens'])}장")


if __name__ == "__main__":
    main()
