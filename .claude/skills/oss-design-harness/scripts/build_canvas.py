"""screens.json → 캔버스 index.html (v2, 화이트보드 단순성 docs/success-criteria §9).

python3 build_canvas.py <out_dir>

- 보는 것만: 스크롤 + 화면 누르면 크게 보기. 조작 요소는 색 점(팔레트) 최대 3개뿐, 편집·선택 모드 없음, 외부 라이브러리 없음.
- 한 줄 = 한 흐름(group). 순서는 왼→오 배치로 보여주고 **화살표는 분기(branches)에만**.
- 상태 변형(id에 --)은 원래 화면 바로 오른쪽에, 같은 줄에.
- 화면 아래: 목적 1줄 + 정책(policies) 최대 3줄, 넘치면 접기.
- 화면 축소 0.72배(본문 16px → 11.5px).

screens.json:
{"groups": ["처음 들어올 때", ...],          # 줄 순서(선택)
 "story": {...},                               # 맨 위 설계 이야기(선택)
 "screens": [{"id", "file", "title", "group", "purpose",
              "policies": ["…"], "branches": [{"to": "id", "label": "…"}]}]}
palettes.json(선택): 색 점 3개 + 색 출처.
"""
import sys, json, pathlib, html

out = pathlib.Path(sys.argv[1])
m = json.loads((out / "screens.json").read_text(encoding="utf-8"))
screens = m["screens"]
byid = {s["id"]: s for s in screens}
esc = lambda x: html.escape(str(x or ""))

W, H, S = 375, 812, 0.72
CW, CH = round(W * S), round(H * S)
GX, TOP, LEFT, LABEL, INFO = 56, 64, 190, 96, 150      # LEFT 안쪽이 줄을 넘는 화살표 통로      # 화면 사이, 줄 위 여백, 왼쪽, 흐름 이름 높이, 화면 아래 글 높이

groups = list(m.get("groups") or [])
for s in screens:
    g = s.get("group") or "기타"
    if g not in groups: groups.append(g)
rows = {g: [] for g in groups}
for s in screens:                                      # 상태 변형은 원래 화면 바로 뒤에
    if "--" in s["id"]: continue
    rows[s.get("group") or "기타"].append(s)
    rows[s.get("group") or "기타"].extend(v for v in screens if v["id"].startswith(s["id"] + "--"))
rows = {g: r for g, r in rows.items() if r}
groups = [g for g in groups if g in rows]

pos, y = {}, 0
row_top = {}
for g in groups:
    row_top[g] = y
    for i, s in enumerate(rows[g]):
        pos[s["id"]] = (LEFT + i * (CW + GX), y + LABEL)
    y += LABEL + CH + INFO + TOP
width = LEFT * 2 + max(len(r) for r in rows.values()) * (CW + GX)
height = y

# 분기 화살표만: 같은 줄이면 위쪽 호, 다른 줄이면 아래로 곡선
arrows, labels = [], []
for s in screens:
    for b in s.get("branches", []):
        t = b.get("to")
        if t not in pos or t == s["id"]: continue
        (x1, y1), (x2, y2) = pos[s["id"]], pos[t]
        if abs(y1 - y2) < 1:
            a, c = (x1 + CW / 2, y1 - 6), (x2 + CW / 2, y2 - 6)
            peak = y1 - 34
            d = f"M{a[0]},{a[1]} C{a[0]},{peak} {c[0]},{peak} {c[0]},{c[1]}"
            lx, ly = (a[0] + c[0]) / 2, peak - 4
        else:                                          # 줄을 넘으면 화면을 가로지르지 않고 왼쪽 통로로 우회
            lane = LEFT - 40 - 14 * (len(arrows) % 4)
            a = (x1, y1 + 60); c = (x2 - 4, y2 + 60)
            r = 14
            dy = 1 if c[1] > a[1] else -1
            d = (f"M{a[0]},{a[1]} H{lane + r} Q{lane},{a[1]} {lane},{a[1] + dy * r} "
                 f"V{c[1] - dy * r} Q{lane},{c[1]} {lane + r},{c[1]} H{c[0]}")
            lx, ly = lane - 8, (a[1] + c[1]) / 2
        arrows.append(f'<path d="{d}"/>')
        if b.get("label"):
            labels.append(f'<div class="alabel{" side" if abs(y1 - y2) >= 1 else ""}" style="left:{lx}px;top:{ly}px">{esc(b["label"])}</div>')

frames = []
for g in groups:
    frames.append(f'<div class="glabel" style="top:{row_top[g]}px;left:{LEFT}px">{esc(g)}</div>')
for s in screens:
    if s["id"] not in pos: continue
    x, yy = pos[s["id"]]
    pol = s.get("policies", []) or []
    shown = "".join(f"<li>{esc(p)}</li>" for p in pol[:3])
    more = (f'<details><summary>정책 {len(pol) - 3}개 더</summary><ul>' + "".join(f"<li>{esc(p)}</li>" for p in pol[3:]) + "</ul></details>") if len(pol) > 3 else ""
    state = '<span class="state">상태</span>' if "--" in s["id"] else ""
    frames.append(f'''<div class="frame" style="left:{x}px;top:{yy}px">
<div class="phone"><iframe src="{esc(s["file"])}" loading="eager" scrolling="no" tabindex="-1" title="{esc(s.get("title"))}"></iframe>
<a class="hit" href="{esc(s["file"])}" target="view" aria-label="{esc(s.get("title"))} 크게 보기"></a></div>
<div class="ftitle">{state}{esc(s.get("title", s["id"]))}</div>
<div class="fdesc">{esc(s.get("purpose"))}</div><ul class="pol">{shown}</ul>{more}</div>''')

st = m.get("story") or {}
story = ""
if st:
    ideas = "".join(f'<div class="idea"><b>{esc(d.get("title"))}</b><p>{esc(d.get("desc"))}</p></div>' for d in st.get("ideas", [])[:3])
    head = esc(st.get("headline")).replace("&lt;em&gt;", "<em>").replace("&lt;/em&gt;", "</em>")
    story = f'<section class="story"><h1>{head}</h1><p class="sum">{esc(st.get("summary"))}</p><div class="ideas">{ideas}</div></section>'

dec_path = out / "decisions.json"
decisions = ""
if dec_path.exists():
    D = json.loads(dec_path.read_text(encoding="utf-8"))
    label = {"lighten": "가볍게", "cut": "뺌", "later": "나중에"}
    items = [i for i in D.get("items", []) if i.get("verdict") in label][:6]
    lis = "".join(f'<li><span class="v v-{esc(i["verdict"])}">{label[i["verdict"]]}</span><b>{esc(i.get("name"))}</b>'
                  f'{(" → " + esc(i.get("how"))) if i.get("how") and i["verdict"] == "lighten" else ""}<span class="why">{esc(i.get("why"))}</span></li>' for i in items)
    decisions = (f'<section class="decisions"><h2>정한 것 · 뺀 것</h2><p class="core">{esc(D.get("core"))}</p><ul>{lis}</ul></section>') if (items or D.get("core")) else ""

pal_path = out / "palettes.json"
pal = json.loads(pal_path.read_text(encoding="utf-8")) if pal_path.exists() else None
dots, credit, default = "", "", "null"
if pal:
    dots = '<div class="palette">색 ' + "".join(
        f'<button class="dot" data-slug="{esc(o["slug"])}" aria-label="{esc(o["name"])} 색으로 보기" style="--dot:{esc(o["brand"])}"><span></span>{esc(o["name"])}</button>'
        for o in pal["options"][:3]) + "</div>"
    credit = '<p class="credit">색 출처: ' + " · ".join(esc(o["name"]) + " 웹 팔레트" for o in pal["options"][:3]) + " — 시안용 참고. 출시 전 자체 브랜드 색으로 바꾸세요.</p>"
    default = json.dumps(pal["default"])

doc = f"""<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>전체 화면 한눈에 보기</title>
<style>
*{{box-sizing:border-box}} body{{margin:0;background:#EDEDEA;font-family:-apple-system,'Pretendard',sans-serif;color:#1c1c1c;word-break:keep-all}}
header{{position:sticky;top:0;z-index:5;display:flex;align-items:center;gap:12px;flex-wrap:wrap;background:#EDEDEAee;backdrop-filter:blur(6px);padding:14px 190px 14px 64px}}
header h1{{font-size:20px;margin:0}} header .hint{{font-size:14px;color:#666}}
.palette{{margin-left:auto;display:flex;align-items:center;gap:6px;font-size:14px;font-weight:600;color:#555}}
.dot{{display:inline-flex;align-items:center;gap:6px;height:36px;padding:0 12px 0 8px;border-radius:999px;border:1px solid #d3d3cf;background:#fff;font:inherit;font-size:13px;color:#333;cursor:pointer}}
.dot span{{width:18px;height:18px;border-radius:999px;background:var(--dot)}} .dot[aria-pressed="true"]{{border-color:#1c1c1c;box-shadow:inset 0 0 0 1px #1c1c1c}}
.story{{padding:24px 64px 8px;max-width:1240px}} .story h1{{font-size:34px;line-height:1.3;margin:8px 0 12px}} .story h1 em{{font-style:normal;color:#2563eb}}
.story .sum{{font-size:17px;line-height:1.6;color:#444;max-width:760px;margin:0 0 20px}}
.ideas{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}} .idea{{background:#fff;border-radius:14px;padding:18px}} .idea b{{font-size:16px}} .idea p{{font-size:14px;line-height:1.55;color:#555;margin:6px 0 0}}
.decisions{{padding:8px 64px 0;max-width:1240px}} .decisions h2{{font-size:18px;margin:16px 0 6px}} .decisions .core{{font-size:15px;color:#333;margin:0 0 10px}}
.decisions ul{{list-style:none;padding:0;margin:0;display:grid;grid-template-columns:repeat(2,1fr);gap:8px}}
.decisions li{{background:#fff;border-radius:12px;padding:10px 14px;font-size:14px;line-height:1.5}} .decisions b{{margin-right:4px}} .decisions .why{{display:block;color:#666;font-size:13px}}
.v{{display:inline-block;font-size:11px;font-weight:700;border-radius:6px;padding:1px 6px;margin-right:6px;background:#eee;color:#444}} .v-cut{{background:#fde8e8;color:#9b1c1c}} .v-lighten{{background:#e7f0ff;color:#1d4ed8}}
.board{{position:relative;width:{width}px;height:{height}px;margin-top:32px}}
svg.ar{{position:absolute;inset:0;width:{width}px;height:{height}px;pointer-events:none;overflow:visible}}
svg.ar path{{fill:none;stroke:#2563eb;stroke-width:2;marker-end:url(#h)}}
.alabel{{position:absolute;transform:translate(-50%,-100%);max-width:150px;white-space:normal;text-align:center;background:#fff;border:1px solid #c7d6fb;color:#1d4ed8;font-size:12px;font-weight:600;padding:3px 8px;border-radius:999px;white-space:nowrap}}
.alabel.side{{transform:translate(-100%,-50%);text-align:right}}
.glabel{{position:absolute;font-size:20px;font-weight:700}}
.frame{{position:absolute;width:{CW}px}}
.phone{{position:relative;width:{CW}px;height:{CH}px;border-radius:20px;overflow:hidden;background:#fff;box-shadow:0 2px 10px rgba(0,0,0,.10)}}
.phone iframe{{width:{W}px;height:{H}px;border:0;transform:scale({S});transform-origin:0 0;pointer-events:none}}
.hit{{position:absolute;inset:0;border-radius:20px}} .hit:hover{{outline:3px solid #2563eb}}
.ftitle{{font-size:15px;font-weight:700;margin-top:10px}} .state{{font-size:11px;font-weight:700;color:#8a5a00;background:#fff3cf;border-radius:6px;padding:2px 6px;margin-right:6px}}
.fdesc{{font-size:13px;color:#555;margin-top:2px}}
.pol{{margin:6px 0 0;padding-left:16px;font-size:12px;line-height:1.5;color:#444}} details{{font-size:12px;color:#666}} summary{{cursor:pointer}}
.credit{{font-size:12px;color:#777;padding:0 64px 40px}}
#viewer{{position:fixed;inset:0;background:rgba(0,0,0,.55);display:none;align-items:center;justify-content:center;z-index:10}}
#viewer.on{{display:flex}} #viewer iframe{{width:{W}px;height:{H}px;max-height:92vh;border:0;border-radius:28px;background:#fff}}
#viewer .close{{position:absolute;top:20px;right:28px;font-size:16px;padding:10px 16px;border:0;border-radius:10px;background:#fff;cursor:pointer}}
</style>
<header><h1>전체 화면 한눈에 보기</h1><span class="hint">화면을 누르면 크게 보고 직접 눌러볼 수 있어요 · 파란 화살표는 갈래</span>{dots}</header>
{story}
{decisions}
<div class="board">
<svg class="ar"><defs><marker id="h" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#2563eb" stroke="none"/></marker></defs>{''.join(arrows)}</svg>
{''.join(frames)}{''.join(labels)}
</div>
{credit}
<div id="viewer"><button class="close" onclick="document.getElementById('viewer').classList.remove('on')">닫기</button><iframe name="view" title="크게 보기"></iframe></div>
<script>
const v=document.getElementById('viewer');document.querySelectorAll('a[target=view]').forEach(a=>a.addEventListener('click',()=>v.classList.add('on')));
(function(){{const K='hd-palette';const dots=[...document.querySelectorAll('.dot')];if(!dots.length)return;
 let cur;try{{cur=localStorage.getItem(K)}}catch(e){{}} cur=cur||{default};
 const send=s=>{{document.querySelectorAll('iframe').forEach(f=>{{try{{f.contentWindow.postMessage({{type:'hd-palette',slug:s}},'*')}}catch(e){{}}}});dots.forEach(d=>d.setAttribute('aria-pressed',String(d.dataset.slug===s)))}};
 dots.forEach(d=>d.addEventListener('click',()=>{{cur=d.dataset.slug;try{{localStorage.setItem(K,cur)}}catch(e){{}};send(cur)}}));
 document.querySelector('iframe[name=view]').addEventListener('load',()=>send(cur));
 window.addEventListener('load',()=>send(cur));}})();
</script>
</html>"""
(out / "index.html").write_text(doc, encoding="utf-8")
print(f"canvas v2: {len(screens)} screens, {len(arrows)} branch arrows, {len(groups)} groups, scale {S}")
