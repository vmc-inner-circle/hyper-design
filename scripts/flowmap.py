"""흐름 지도 (K14, 10-12, 사용자: "시나리오별 화살표로 표시하는 부분도 있고, 기능별 화살표 표시도 있는데 그런 부분도 나오면 좋겠다").

    python scripts/flowmap.py design/v/v1        # design/v/v1/app.json + shots/all/<id>-m.png → design/v/v1/flow.html

세 가지 보기(탭으로 전환):
  시나리오별 — base.json 의 tour(둘러보기 순서)를 화면 그림 + 화살표로. 화살표 위 글자 = 누르는 것(없으면 '다음 장면')
  기능별     — PRD 기능 요구사항(F1…)마다 그 기능이 들어간 화면들을 연결 순서대로 화살표로
  탭 묶음별  — 역할마다 탭(내비) 하나에서 이어지는 화면들(깊이 순)
보통은 variants.py 가 캡처 뒤 부른다(직접 쓸 일 없음).
"""
import html as H
import json
import pathlib
import re
import sys
from collections import OrderedDict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
e = H.escape


def walk(x, out):
    if isinstance(x, dict) and x.get("t") == "html":
        for to, txt in re.findall(r'href="#([\w-]+)"[^>]*>(.*?)</a>', x.get("html", ""), re.S):
            out.append((to, re.sub(r"<[^>]+>|\s+", " ", txt).strip()[:24]))
        return
    if isinstance(x, dict):
        to = x.get("to")
        if isinstance(to, str) and to:
            out.append((to, str(x.get("label") or x.get("title") or x.get("text") or x.get("cta") or "").strip()[:24]))
        for v in x.values():
            walk(v, out)
    elif isinstance(x, list):
        for v in x:
            walk(v, out)


def graph(spec):
    scr = OrderedDict((s["id"], s) for s in spec["screens"])
    edges = {}
    for s in spec["screens"]:
        out = []
        walk({k: v for k, v in s.items() if k not in ("id", "role")}, out)
        for to, lab in out:
            if to in scr and to != s["id"] and (s["id"], to) not in edges:
                edges[(s["id"], to)] = lab
    for r in spec.get("roles", []):  # 탭바로 오가는 것도 연결
        for a in r.get("nav", []):
            for b in r.get("nav", []):
                if a != b and a in scr and b in scr and (a, b) not in edges:
                    edges[(a, b)] = f'탭 · {scr[b].get("navLabel") or scr[b]["title"]}'
    return scr, edges


def chain(ids, edges, cap=None):
    """화면 id 목록 → 카드·화살표 HTML"""
    h = []
    for i, sid in enumerate(ids):
        if i:
            lab = edges.get((ids[i - 1], sid))
            dashed = lab is None
            h.append(f'<div class="ar{" dash" if dashed else ""}"><span>{e(lab or "다음 장면")}</span><svg viewBox="0 0 48 12" aria-hidden="true"><path d="M0 6h44m-6-5 6 5-6 5"/></svg></div>')
        h.append(f'<figure data-s="{e(sid)}"><img loading="lazy" src="shots/all/{e(sid)}-m.png" alt=""><figcaption>{(cap or {}).get(sid) or ""}</figcaption></figure>')
    return '<div class="row">' + "".join(h) + "</div>"


CSS = """
:root{--bg:#F5F5F3;--ink:#151716;--mut:#5E6461;--line:#D9DAD5;--card:#fff;--ar:#151716}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#111312;--ink:#ECEDEB;--mut:#A2A8A4;--line:#2C302E;--card:#1A1C1B;--ar:#ECEDEB}}
*{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--ink);font-family:"Pretendard Variable",Pretendard,sans-serif;line-height:1.5;word-break:keep-all}
header{position:sticky;top:0;z-index:3;background:var(--bg);border-bottom:1px solid var(--line);padding:16px 24px;display:flex;flex-wrap:wrap;gap:12px;align-items:center}
h1{font-size:20px;margin:0} .sub{color:var(--mut);font-size:14px;flex-basis:100%;margin:0}
.tabs{display:flex;gap:6px} .tabs button{border:1px solid var(--line);background:var(--card);color:var(--ink);padding:8px 16px;border-radius:999px;font:inherit;font-size:14px;cursor:pointer;min-height:40px}
.tabs button.a{background:var(--ink);color:var(--bg);border-color:var(--ink)} header a{color:inherit;font-size:14px;margin-left:auto}
main{padding:16px 24px 64px} section{display:none} section.on{display:block}
.grp{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:16px 16px 8px;margin:16px 0}
.grp h2{font-size:16px;margin:0 0 4px} .grp p{margin:0 0 12px;color:var(--mut);font-size:14px}
.row{display:flex;align-items:flex-start;gap:8px;overflow-x:auto;padding:4px 0 12px}
figure{margin:0;flex:0 0 168px} figure img{width:168px;height:364px;object-fit:cover;object-position:top;display:block;border:1px solid var(--line);border-radius:12px;background:var(--bg)}
figcaption{font-size:13px;margin-top:6px;color:var(--ink)} figcaption b{display:block;font-size:14px}
.ar{flex:0 0 96px;align-self:center;display:flex;flex-direction:column;align-items:center;gap:4px;margin-top:-40px}
.ar span{font-size:12px;color:var(--mut);text-align:center;line-height:1.3;max-width:96px}
.ar svg{width:56px;height:14px;stroke:var(--ar);stroke-width:2;fill:none} .ar.dash svg{stroke-dasharray:4 4;opacity:.6}
.role{font-size:13px;color:var(--mut);margin:24px 0 0}
@media (max-width:600px){header,main{padding-left:16px;padding-right:16px}}
"""


def build(vdir):
    vdir = pathlib.Path(vdir)
    spec = json.loads((vdir / "app.json").read_text(encoding="utf-8"))
    scr, edges = graph(spec)
    title = {k: v["title"] for k, v in scr.items()}
    roles = {r["id"]: r.get("name", r["id"]) for r in spec.get("roles", [])}
    role_of = {k: v.get("role") for k, v in scr.items()}
    # 시나리오별
    tour = [t for t in spec.get("tour", []) if t.get("screen") in scr]
    sc = ""
    if tour:
        ids = [t["screen"] for t in tour]
        cap = {}
        for n, t in enumerate(tour, 1):
            cap.setdefault(t["screen"], f'<b>{n}. {e(title[t["screen"]])}</b>{e(t.get("caption", ""))}')
        sc = f'<div class="grp"><h2>대표 시나리오 — 하네스가 정한 둘러보기 {len(ids)}단계</h2><p>역할을 오가며 이 서비스를 처음부터 끝까지 써 보는 순서. 실선 = 실제로 눌러서 가는 연결(글자 = 누르는 것), 점선 = 다음 장면.</p>{chain_html(ids, edges, cap)}</div>'
    for name, sid in (spec.get("flows") or {}).items():
        if isinstance(sid, str) and sid in scr:
            path = [sid] + bfs(sid, edges, set(scr), 3)
            sc += f'<div class="grp"><h2>{e({"onboarding": "처음 시작", "invite": "함께 쓰는 사람 초대", "empty": "아무것도 없을 때"}.get(name, name))}</h2><p>{e(roles.get(role_of[sid], ""))}</p>{chain_html(path, edges, {s: "<b>" + e(title[s]) + "</b>" for s in path})}</div>'
    # 기능별
    ft = ""
    for f in spec.get("features", []):
        mine = [s for s, v in scr.items() if f["id"] in v.get("features", [])]
        if not mine:
            continue
        order = order_by_links(mine, edges)
        ft += f'<div class="grp"><h2>{e(f["id"])} · {e(f.get("name", ""))}</h2><p>이 기능이 들어간 화면 {len(order)}장 — 연결된 순서대로</p>{chain_html(order, edges, {s: "<b>" + e(title[s]) + "</b>" + e(roles.get(role_of[s], "")) for s in order})}</div>'
    # 탭 묶음별
    tb = ""
    for r in spec.get("roles", []):
        tb += f'<div class="role">{e(r.get("name", r["id"]))} · 탭: {e(" · ".join(title.get(n, n) for n in r.get("nav", [])))}</div>'
        seen = set(r.get("nav", []))
        for n in r.get("nav", []):
            sub = [n] + [s for s in bfs(n, edges, {k for k, v in role_of.items() if v == r["id"]}, 4) if s not in seen]
            seen |= set(sub)
            tb += f'<div class="grp"><h2>탭 · {e(title.get(n, n))}</h2><p>이 탭에서 이어지는 화면 {len(sub)}장</p>{chain_html(sub, edges, {s: "<b>" + e(title[s]) + "</b>" for s in sub})}</div>'
    v = spec.get("variant", {})
    doc = f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(spec.get("name", ""))} 흐름 지도</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/pretendard@1.3.9/dist/web/variable/pretendardvariable.min.css"><style>{CSS}</style></head><body>
<header><h1>{e(spec.get("name", ""))} · 흐름 지도 <small style="font-weight:500;color:var(--mut)">{e(v.get("name", ""))}</small></h1>
<div class="tabs"><button class="a" data-t="sc">시나리오별</button><button data-t="ft">기능별</button><button data-t="tb">탭 묶음별</button></div><a href="index.html">이 디자인 둘러보기</a> <a href="../../index.html">5벌 비교로</a>
<p class="sub">화면 그림 사이 화살표 = 누르면 넘어가는 곳(글자 = 누르는 것). 점선 = 바로 이어지지는 않고 다음에 보는 장면. 옆으로 밀어서 보세요.</p></header>
<main><section id="sc" class="on">{sc or "<p>시나리오 정보 없음</p>"}</section><section id="ft">{ft or "<p>기능 정보 없음</p>"}</section><section id="tb">{tb}</section></main>
<script>document.querySelectorAll('.tabs button').forEach(b=>b.onclick=()=>{{document.querySelectorAll('.tabs button').forEach(x=>x.classList.toggle('a',x===b));document.querySelectorAll('section').forEach(s=>s.classList.toggle('on',s.id===b.dataset.t))}})</script></body></html>'''
    (vdir / "flow.html").write_text(doc, encoding="utf-8")
    return vdir / "flow.html"


def chain_html(ids, edges, cap):
    return chain(ids, edges, cap)


def bfs(start, edges, allowed, depth):
    out, frontier, seen = [], [start], {start}
    for _ in range(depth):
        nxt = []
        for s in frontier:
            for (a, b), lab in edges.items():
                if a == s and b in allowed and b not in seen and not lab.startswith("탭 · "):
                    seen.add(b)
                    nxt.append(b)
        out += nxt
        frontier = nxt
    return out


def order_by_links(ids, edges):
    """같은 기능 화면들을 연결을 따라 한 줄로: 들어오는 연결이 없는 것부터, 이어지는 것을 뒤에"""
    rest, out = list(ids), []
    while rest:
        start = next((s for s in rest if not any((o, s) in edges for o in rest if o != s)), rest[0])
        cur = start
        while cur in rest:
            out.append(cur)
            rest.remove(cur)
            nxt = next((b for b in rest if (cur, b) in edges), None)
            if not nxt:
                break
            cur = nxt
    return out


if __name__ == "__main__":
    print(build(sys.argv[1]))
