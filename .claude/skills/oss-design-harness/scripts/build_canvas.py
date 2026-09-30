"""screens.json → 피그마식 캔버스 index.html. 흐름(group)별로 한 줄, links 를 화살표로 잇는다."""
import sys, json, pathlib, html
out = pathlib.Path(sys.argv[1])
m = json.loads((out / "screens.json").read_text(encoding="utf-8"))
screens = m["screens"]
W, H, S = 375, 812, 0.5          # 실제 크기, 축소 배율
CW, CH, GX, GY, TOP, LEFT = W * S, H * S, 90, 250, 120, 60
groups = []
for s in screens:
    g = s.get("group") or "기타"
    if g not in groups: groups.append(g)
pos, rows = {}, {g: [] for g in groups}
for s in screens: rows[s.get("group") or "기타"].append(s)
for gi, g in enumerate(groups):
    for i, s in enumerate(rows[g]):
        pos[s["id"]] = (LEFT + i * (CW + GX), TOP + gi * (CH + GY))
width = LEFT * 2 + max(len(r) for r in rows.values()) * (CW + GX)
height = TOP + len(groups) * (CH + GY)
arrows = []; seen = set()
first = {rows[g][0]["id"] for g in groups}
for s in screens:
    for t in s.get("links", []):
        if t not in pos or t == s["id"]: continue
        x1, y1 = pos[s["id"]]; x2, y2 = pos[t]
        if abs(y1 - y2) < 1 and x2 > x1:      # 같은 줄 오른쪽
            a, b = (x1 + CW, y1 + CH * .35), (x2, y2 + CH * .35)
            d = f"M{a[0]},{a[1]} C{a[0]+40},{a[1]} {b[0]-40},{b[1]} {b[0]},{b[1]}"
        else:
            gs, gt = s.get("group"), next(x.get("group") for x in screens if x["id"] == t)
            if t not in first or (gs, gt) in seen or gs == gt: continue
            seen.add((gs, gt))
            a = (x1 + CW / 2, y1 + CH); b = (x2 + CW / 2, y2 - 8)
            if y2 <= y1: a = (x1 + CW / 2, y1 - 8); b = (x2 + CW / 2, y2 + CH)
            my = (a[1] + b[1]) / 2
            d = f"M{a[0]},{a[1]} C{a[0]},{my} {b[0]},{my} {b[0]},{b[1]}"
        cls = "" if abs(y1 - y2) < 1 else ' class="x"'
        arrows.append(f'<path{cls} d="{d}"/>')
frames, labels = [], []
for gi, g in enumerate(groups):
    labels.append(f'<div class="glabel" style="top:{TOP + gi*(CH+GY) - 70}px;left:{LEFT}px">{html.escape(g)}</div>')
for s in screens:
    x, y = pos[s["id"]]
    states = [st for st in s.get("states", []) if (out / "screens" / f'{s["id"]}--{st}.html').exists()]
    ko = {"empty": "비어 있을 때", "error": "입력이 틀렸을 때", "disabled": "보기만 할 때"}
    chips = "".join(f'<a class="chip" href="screens/{s["id"]}--{st}.html" target="view">{ko.get(st, st)}</a>' for st in states)
    frames.append(f'''<div class="frame" style="left:{x}px;top:{y}px">
<div class="ftitle">{html.escape(s.get("title", s["id"]))}</div>
<div class="phone"><iframe src="{s["file"]}" loading="eager" scrolling="no" tabindex="-1"></iframe>
<a class="hit" href="{s["file"]}" target="view" aria-label="{html.escape(s.get("title",""))} 크게 보기"></a></div>
<div class="fdesc">{html.escape(s.get("purpose",""))}</div><div class="chips">{chips}</div></div>''')
st = m.get("story") or {}
pal_path = out / "palettes.json"
pal = json.loads(pal_path.read_text(encoding="utf-8")) if pal_path.exists() else None
pal_html = ""; credit = ""
if pal:
    credit = '<p class="credit">색 출처: ' + " · ".join(html.escape(o["name"]) + " 웹 팔레트" for o in pal["options"][:3]) + ' — 시안용 참고. 출시 전 자체 브랜드 색으로 교체하세요.</p>'
    dots = "".join(f'<button class="dot" data-slug="{o["slug"]}" title="" aria-label="{html.escape(o["name"])} 색으로 보기" style="--dot:{o["brand"]}"><span></span>{html.escape(o["name"])}</button>' for o in pal["options"][:3])
    pal_html = f'<div class="palette">색 {dots}</div>'

def esc(x): return html.escape(str(x or ""))
ideas = "".join(f'''<div class="idea"><div class="n">{i+1}</div><b>{esc(d.get("title"))}</b><p>{esc(d.get("desc"))}</p>
<div class="refs">{esc(d.get("refs"))}{"".join(f' · <a href="{next((x["file"] for x in screens if x["id"]==sid), "#")}" target="view">{esc(next((x.get("title") for x in screens if x["id"]==sid), sid))}</a>' for sid in d.get("screens", []))}</div></div>''' for i, d in enumerate(st.get("ideas", [])[:3]))
roles = "".join(f'<div class="role"><b>{esc(r.get("name"))}</b><ul>{"".join(f"<li>{esc(x)}</li>" for x in r.get("sees", []))}</ul></div>' for r in st.get("roles", []))
headline = st.get("headline", "")
headline = html.escape(headline).replace("&lt;em&gt;", "<em>").replace("&lt;/em&gt;", "</em>")
story_html = f'''<section class="story"><h1>{headline}</h1><p class="sum">{esc(st.get("summary"))}</p>
<div class="ideas">{ideas}</div>{f'<h2>역할에 따라 다르게 보여요</h2><div class="roles">{roles}</div>' if roles else ""}
<h2>전체 화면</h2></section>''' if st else ""
doc = f"""<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>전체 화면 한눈에 보기</title>
<style>
*{{box-sizing:border-box}} body{{margin:0;background:#e9e9e6;font-family:-apple-system,'Pretendard',sans-serif;color:#1c1c1c;overflow:auto}}
header{{position:sticky;top:0;left:0;z-index:5;background:#e9e9e6ee;padding:16px 60px;font-size:20px;font-weight:700;backdrop-filter:blur(6px)}}
header span{{font-weight:400;color:#666;font-size:15px;margin-left:12px}}
.board{{position:relative;width:{width}px;height:{height}px}}
svg{{position:absolute;inset:0;width:{width}px;height:{height}px;pointer-events:none}}
svg path{{fill:none;stroke:#e5484d;stroke-width:2.5;marker-end:url(#h)}} svg path.x{{stroke-dasharray:6 6;opacity:.6}}
.glabel{{position:absolute;font-size:22px;font-weight:700}}
.frame{{position:absolute;width:{CW}px}}
.ftitle{{font-size:15px;font-weight:600;margin-bottom:8px}}
.phone{{position:relative;width:{CW}px;height:{CH}px;border-radius:18px;overflow:hidden;background:#fff;box-shadow:0 4px 18px rgba(0,0,0,.12)}}
.phone iframe{{width:{W}px;height:{H}px;border:0;transform:scale({S});transform-origin:0 0;pointer-events:none}}
.hit{{position:absolute;inset:0}} .hit:hover{{outline:3px solid #e5484d;border-radius:18px}}
.fdesc{{font-size:13px;color:#555;margin-top:8px;line-height:1.45}}
.chips{{display:flex;gap:6px;flex-wrap:wrap;margin-top:6px}} .chip{{font-size:12px;padding:4px 8px;border-radius:12px;background:#fff;color:#333;text-decoration:none}}
.story{{padding:24px 60px 8px;max-width:1240px}} .story h1{{font-size:40px;line-height:1.25;letter-spacing:-.03em;margin:8px 0 14px}} .story h1 em{{font-style:normal;color:#e5484d}}
.story .sum{{font-size:18px;line-height:1.6;color:#444;max-width:780px;margin:0 0 28px}} .story h2{{font-size:24px;margin:40px 0 16px}}
.ideas{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}} .idea{{background:#fff;border-radius:16px;padding:22px}}
.idea .n{{width:30px;height:30px;border-radius:50%;background:#1c1c1c;color:#fff;display:grid;place-items:center;font-weight:700;margin-bottom:12px}}
.idea b{{font-size:18px}} .idea p{{font-size:15px;line-height:1.6;color:#444;margin:8px 0 12px}} .refs{{font-size:13px;color:#777}} .refs a{{color:#e5484d}}
.roles{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}} .role{{background:#fff;border-radius:16px;padding:22px}} .role b{{font-size:17px}} .role li{{font-size:15px;line-height:1.7;color:#444}}
header{{display:flex;align-items:center;gap:12px;flex-wrap:wrap}} .palette{{margin-left:auto;display:flex;align-items:center;gap:6px;font-size:14px;font-weight:600;color:#555}}
.dot{{display:inline-flex;align-items:center;gap:6px;height:36px;padding:0 12px 0 8px;border-radius:999px;border:1px solid #d6d6d2;background:#fff;font:inherit;font-size:13px;color:#333;cursor:pointer}}
.dot span{{width:18px;height:18px;border-radius:999px;background:var(--dot)}} .dot[aria-pressed="true"]{{border-color:#1c1c1c;box-shadow:inset 0 0 0 1px #1c1c1c}}
.credit{{font-size:12px;color:#777;padding:0 60px 40px}}
#viewer{{position:fixed;inset:0;background:rgba(0,0,0,.55);display:none;align-items:center;justify-content:center;z-index:10}}
#viewer.on{{display:flex}} #viewer iframe{{width:{W}px;height:{H}px;max-height:92vh;border:0;border-radius:28px;background:#fff}}
#viewer button{{position:absolute;top:20px;right:28px;font-size:18px;padding:10px 16px;border:0;border-radius:10px;background:#fff;cursor:pointer}}
</style>
<header>전체 화면 한눈에 보기<span>화면을 누르면 크게 보고 직접 눌러볼 수 있어요 · 빨간 화살표는 화면 이동</span>{pal_html}</header>
{story_html}<div class="board">
<svg><defs><marker id="h" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#e5484d" stroke="none"/></marker></defs>{''.join(arrows)}</svg>
{''.join(labels)}{''.join(frames)}
</div>
<div id="viewer"><button onclick="v.classList.remove('on')">닫기</button><iframe name="view"></iframe></div>
<script>
(function(){{const K='hd-palette';const dots=[...document.querySelectorAll('.dot')];if(!dots.length)return;
 let cur;try{{cur=localStorage.getItem(K)}}catch(e){{}} cur=cur||{json.dumps(pal["default"]) if pal else "null"};
 const send=s=>{{document.querySelectorAll('iframe').forEach(f=>{{try{{f.contentWindow.postMessage({{type:'hd-palette',slug:s}},'*')}}catch(e){{}}}});dots.forEach(d=>d.setAttribute('aria-pressed',d.dataset.slug===s))}};
 dots.forEach(d=>d.addEventListener('click',()=>{{try{{localStorage.setItem(K,d.dataset.slug)}}catch(e){{}};send(d.dataset.slug)}}));
 window.addEventListener('load',()=>send(cur));}})();
</script>
<script>const v=document.getElementById('viewer');document.querySelectorAll('a[target=view]').forEach(a=>a.addEventListener('click',()=>v.classList.add('on')));</script>
{credit}</html>"""
(out / "index.html").write_text(doc, encoding="utf-8")
print("canvas:", len(screens), "screens,", len(arrows), "arrows,", len(groups), "groups")
