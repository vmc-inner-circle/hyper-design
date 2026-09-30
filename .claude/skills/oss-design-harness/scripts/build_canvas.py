"""screens.json → 피그마식 캔버스 index.html. 흐름(group)별로 한 줄, links 를 화살표로 잇는다."""
import sys, json, pathlib, html
out = pathlib.Path(sys.argv[1])
m = json.loads((out / "screens.json").read_text(encoding="utf-8"))
screens = m["screens"]
W, H, S = 375, 812, 0.5          # 실제 크기, 축소 배율
CW, CH, GX, GY, TOP, LEFT = W * S, H * S, 90, 150, 110, 60
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
arrows = []
for s in screens:
    for t in s.get("links", []):
        if t not in pos or t == s["id"]: continue
        x1, y1 = pos[s["id"]]; x2, y2 = pos[t]
        if abs(y1 - y2) < 1 and x2 > x1:      # 같은 줄 오른쪽
            a, b = (x1 + CW, y1 + CH * .35), (x2, y2 + CH * .35)
            d = f"M{a[0]},{a[1]} C{a[0]+40},{a[1]} {b[0]-40},{b[1]} {b[0]},{b[1]}"
        else:
            a = (x1 + CW / 2, y1 + CH); b = (x2 + CW / 2, y2 - 8)
            if y2 <= y1: a = (x1 + CW / 2, y1 - 8); b = (x2 + CW / 2, y2 + CH)
            my = (a[1] + b[1]) / 2
            d = f"M{a[0]},{a[1]} C{a[0]},{my} {b[0]},{my} {b[0]},{b[1]}"
        arrows.append(f'<path d="{d}"/>')
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
<div class="phone"><iframe src="{s["file"]}" scrolling="no" tabindex="-1"></iframe>
<a class="hit" href="{s["file"]}" target="view" aria-label="{html.escape(s.get("title",""))} 크게 보기"></a></div>
<div class="fdesc">{html.escape(s.get("purpose",""))}</div><div class="chips">{chips}</div></div>''')
doc = f"""<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>전체 화면 한눈에 보기</title>
<style>
*{{box-sizing:border-box}} body{{margin:0;background:#e9e9e6;font-family:-apple-system,'Pretendard',sans-serif;color:#1c1c1c;overflow:auto}}
header{{position:sticky;top:0;left:0;z-index:5;background:#e9e9e6ee;padding:16px 60px;font-size:20px;font-weight:700;backdrop-filter:blur(6px)}}
header span{{font-weight:400;color:#666;font-size:15px;margin-left:12px}}
.board{{position:relative;width:{width}px;height:{height}px}}
svg{{position:absolute;inset:0;width:{width}px;height:{height}px;pointer-events:none}}
svg path{{fill:none;stroke:#e5484d;stroke-width:2.5;marker-end:url(#h)}}
.glabel{{position:absolute;font-size:22px;font-weight:700}}
.frame{{position:absolute;width:{CW}px}}
.ftitle{{font-size:15px;font-weight:600;margin-bottom:8px}}
.phone{{position:relative;width:{CW}px;height:{CH}px;border-radius:18px;overflow:hidden;background:#fff;box-shadow:0 4px 18px rgba(0,0,0,.12)}}
.phone iframe{{width:{W}px;height:{H}px;border:0;transform:scale({S});transform-origin:0 0;pointer-events:none}}
.hit{{position:absolute;inset:0}} .hit:hover{{outline:3px solid #e5484d;border-radius:18px}}
.fdesc{{font-size:13px;color:#555;margin-top:8px;line-height:1.45}}
.chips{{display:flex;gap:6px;flex-wrap:wrap;margin-top:6px}} .chip{{font-size:12px;padding:4px 8px;border-radius:12px;background:#fff;color:#333;text-decoration:none}}
#viewer{{position:fixed;inset:0;background:rgba(0,0,0,.55);display:none;align-items:center;justify-content:center;z-index:10}}
#viewer.on{{display:flex}} #viewer iframe{{width:{W}px;height:{H}px;max-height:92vh;border:0;border-radius:28px;background:#fff}}
#viewer button{{position:absolute;top:20px;right:28px;font-size:18px;padding:10px 16px;border:0;border-radius:10px;background:#fff;cursor:pointer}}
</style>
<header>전체 화면 한눈에 보기<span>화면을 누르면 크게 보고 직접 눌러볼 수 있어요 · 빨간 화살표는 화면 이동</span></header>
<div class="board">
<svg><defs><marker id="h" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#e5484d" stroke="none"/></marker></defs>{''.join(arrows)}</svg>
{''.join(labels)}{''.join(frames)}
</div>
<div id="viewer"><button onclick="v.classList.remove('on')">닫기</button><iframe name="view"></iframe></div>
<script>const v=document.getElementById('viewer');document.querySelectorAll('a[target=view]').forEach(a=>a.addEventListener('click',()=>v.classList.add('on')));</script>
</html>"""
(out / "index.html").write_text(doc, encoding="utf-8")
print("canvas:", len(screens), "screens,", len(arrows), "arrows,", len(groups), "groups")
