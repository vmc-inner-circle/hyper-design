"""질문 페이지 (v7 엔진). 사용자에게 의견을 구하는 지점 하나 = 이 페이지 하나 = 답 한 번.

    python scripts/ask.py design/ask/q1.json          # → design/ask/q1.html (+ q1.png 캡처는 shots.py page)
    python scripts/ask.py --code design/ask/q1.json '{"a":"b","b":["2"],"c":["1","3"]}'   # 선택 → 답 코드(실행기용)
    python scripts/ask.py --read design/ask/q1.json "Q1 · a=b · b=바꿈:2 · c=1,3"          # 답 코드 → 사람이 읽는 풀이

사용자는 페이지에서 고르고 [답 복사] → 대화창에 붙여 넣는다. 맨 아래 '말로 적기' 칸(선택)에 쓴 글은 답 코드 끝에 ` · 메모=<글>` 로 붙는다(09-28 사용자 요청).

== q<n>.json ==
{"n":1, "title":"짧은 제목", "lead":"지금까지 제가 한 일과 이해한 것(2~3문장, 쉬운 말)",
 "items":[
   {"id":"a","kind":"pick","q":"질문(쉬운 말)","why":"제 추천과 이유 한두 문장","recommend":"o2","multi":false,
    "options":[{"id":"o1","label":"이름","desc":"이걸 고르면 무엇이 달라지나 한 줄",
                "img":"../cand/o1.png","img2":"../cand/o1-d.png(선택: PC 모습)","ref":"레퍼런스 이미지 경로(선택)","refLabel":"실제 앱 이름"}]},
   {"id":"b","kind":"assume","q":"제가 이렇게 가정했어요. 다르면 눌러서 바꿔 주세요",
    "list":[{"id":"1","text":"가정","alt":"바꾸면 이렇게 봅니다"}]},
   {"id":"c","kind":"check","q":"이 중 적용할 것을 골라 주세요(기본: 전부)","list":[{"id":"1","text":"개선안","img":"(선택)"}]}
 ]}
이미지 경로는 q<n>.html 기준 상대 경로.
"""
import html as H
import json
import pathlib
import sys

e = H.escape


def code(q, sel):
    parts = [f"Q{q['n']}"]
    for it in q["items"]:
        v = sel.get(it["id"])
        if it["kind"] == "pick":
            v = v if isinstance(v, list) else [v or it.get("recommend")]
            parts.append(f"{it['id']}={','.join(x for x in v if x)}")
        elif it["kind"] == "assume":
            v = [str(x) for x in (v or [])]
            parts.append(f"{it['id']}=" + (f"바꿈:{','.join(v)}" if v else "그대로"))
        elif it["kind"] == "check":
            v = [str(x) for x in (v if v is not None else [x["id"] for x in it["list"]])]
            parts.append(f"{it['id']}=" + (",".join(v) if v else "없음"))
    return " · ".join(parts)


def read(q, c):
    items = {it["id"]: it for it in q["items"]}
    out = []
    c, _, memo = c.partition("메모=")  # 메모는 맨 끝 — 안에 · 가 있어도 통째로
    for part in c.split("·")[1:]:
        k, _, v = part.strip().partition("=")
        it = items.get(k)
        if not it:
            continue
        if it["kind"] == "pick":
            labels = [next((o["label"] for o in it["options"] if o["id"] == x), x) for x in v.split(",")]
            out.append(f"{it['q']} → {', '.join(labels)}" + (" (추천 그대로)" if v == it.get("recommend") else ""))
        elif it["kind"] == "assume":
            if v == "그대로":
                out.append(f"{it['q']} → 가정 그대로")
            else:
                ch = v.split(":", 1)[1].split(",")
                out.append(f"{it['q']} → 바꿈: " + "; ".join(f"{x['text']} ⇒ {x['alt']}" for x in it["list"] if x["id"] in ch))
        elif it["kind"] == "check":
            ch = [] if v == "없음" else v.split(",")
            out.append(f"{it['q']} → 적용: " + ("; ".join(x["text"] for x in it["list"] if x["id"] in ch) or "없음"))
    if memo.strip():
        out.append(f"사용자가 말로 적은 것 → {memo.strip()}  (고른 것과 겹치면 이 글을 우선해서 반영)")
    return "\n".join(out)


CSS = """
:root{--bg:#F4F4F1;--card:#fff;--ink:#1B1F1D;--mut:#646B67;--line:#DADDD8;--acc:#1F5C4A;--accbg:#E6F0EC}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#141617;--card:#1C2022;--ink:#E9ECEA;--mut:#9BA29E;--line:#2C3134;--acc:#7CC4A8;--accbg:#1F2E29}}
*{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 "Pretendard Variable",Pretendard,"Malgun Gothic",sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:28px 20px 140px}
.kicker{color:var(--acc);font-weight:700;font-size:14px} h1{font-size:26px;margin:4px 0 8px;letter-spacing:-.01em} .lead{color:var(--mut);max-width:760px}
.item{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:20px;margin-top:20px}
.item h2{font-size:18px;margin:0 0 4px} .why{background:var(--accbg);border-radius:10px;padding:10px 12px;margin:10px 0 14px;font-size:15px}
.opts{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:14px}
.opt{border:2px solid var(--line);border-radius:14px;overflow:hidden;cursor:pointer;background:var(--card);display:flex;flex-direction:column;position:relative}
.opt.on{border-color:var(--acc);box-shadow:0 0 0 3px var(--accbg)} .opt .pics{display:grid;grid-template-columns:1fr;gap:8px;background:var(--bg);padding:10px;align-items:start;justify-items:center}
.opt.two{grid-column:span 2} .opt.two .pics{grid-template-columns:1fr 2fr}
.opt img{display:block;max-height:420px;max-width:100%;border-radius:8px;object-fit:contain;background:#fff}
.opt .pics img.d{max-height:none;width:100%}
.opt .tx{padding:12px 14px} .opt b{font-size:16px} .opt .desc{color:var(--mut);font-size:14px}
.rec{position:absolute;top:10px;left:10px;background:var(--acc);color:var(--card);font-size:12px;font-weight:700;padding:3px 8px;border-radius:999px}
.ref{font-size:12px;color:var(--mut);padding:0 14px 12px}
.row{display:flex;gap:10px;align-items:flex-start;padding:10px 0;border-top:1px solid var(--line)} .row:first-of-type{border-top:0}
.sw{flex:none;border:1px solid var(--line);border-radius:999px;padding:5px 12px;font-size:14px;cursor:pointer;background:var(--card);color:inherit;font:inherit;font-size:14px}
.sw.on{background:var(--acc);color:var(--card);border-color:var(--acc)} .alt{color:var(--mut);font-size:14px}
.bar{position:fixed;left:0;right:0;bottom:0;background:var(--card);border-top:1px solid var(--line);padding:12px 20px;display:flex;gap:12px;align-items:center;justify-content:center;flex-wrap:wrap}
.bar code{background:var(--bg);padding:8px 12px;border-radius:8px;font-size:14px;max-width:100%;overflow-wrap:anywhere}
.bar button{background:var(--acc);color:var(--card);border:0;border-radius:10px;padding:12px 22px;font:inherit;font-weight:700;cursor:pointer}
@media (max-width:600px){.wrap{padding:20px 16px 170px} h1{font-size:22px} .opts{grid-template-columns:1fr} .opt.two{grid-column:auto} .opt.two .pics{grid-template-columns:1fr}}
.cap .bar{position:static}
.memo textarea{width:100%;min-height:84px;border:1px solid var(--line);border-radius:10px;padding:10px 12px;font:inherit;background:var(--bg);color:inherit;resize:vertical}
"""

JS = r"""
const Q=__Q__; const sel={};
Q.items.forEach(it=>{ if(it.kind==='pick') sel[it.id]=[it.recommend||it.options[0].id];
  if(it.kind==='assume') sel[it.id]=[]; if(it.kind==='check') sel[it.id]=it.list.map(x=>x.id); });
function codeOf(){const p=['Q'+Q.n]; Q.items.forEach(it=>{const v=sel[it.id];
 if(it.kind==='pick') p.push(it.id+'='+v.join(','));
 if(it.kind==='assume') p.push(it.id+'='+(v.length?'바꿈:'+v.join(','):'그대로'));
 if(it.kind==='check') p.push(it.id+'='+(v.length?v.join(','):'없음'));}); const m=(document.getElementById('memo')||{}).value; if(m&&m.trim()) p.push('메모='+m.trim().replace(/\s+/g,' ')); return p.join(' · ')}
function paint(){document.querySelectorAll('[data-it]').forEach(el=>{const v=sel[el.dataset.it]; el.classList.toggle('on',v.includes(el.dataset.v))});
 document.getElementById('code').textContent=codeOf()}
function tog(it,v){const d=Q.items.find(x=>x.id===it); const a=sel[it];
 if(d.kind==='pick'&&!d.multi){sel[it]=[v]} else {const k=a.indexOf(v); if(k>=0) a.splice(k,1); else a.push(v); if(d.kind==='pick'&&!a.length) a.push(v)} paint()}
function copyCode(){const t=codeOf(); navigator.clipboard&&navigator.clipboard.writeText(t).then(()=>{document.getElementById('ok').textContent='복사했어요. 대화창에 붙여 넣어 주세요.'})}
addEventListener('DOMContentLoaded',()=>{if(location.search.includes('cap'))document.body.classList.add('cap');paint();const m=document.getElementById('memo');if(m)m.addEventListener('input',paint)});
"""


def page(q):
    body = ""
    for it in q["items"]:
        if it["kind"] == "pick":
            opts = ""
            for o in it["options"]:
                pics = "".join(f'<img class="{c}" src="{e(o[k])}" alt="">' for k, c in (("img", ""), ("img2", "d")) if o.get(k))
                ref = f'<div class="pics" style="padding-top:0"><img class="d" src="{e(o["ref"])}" alt=""></div><div class="ref">비슷한 방식을 쓰는 실제 앱: {e(o.get("refLabel", ""))}</div>' if o.get("ref") else ""
                rec = '<span class="rec">추천</span>' if o["id"] == it.get("recommend") else ""
                opts += f'<div class="opt{" two" if o.get("img2") else ""}" data-it="{e(it["id"])}" data-v="{e(o["id"])}" onclick="tog(\'{e(it["id"])}\',\'{e(o["id"])}\')">{rec}<div class="pics">{pics}</div><div class="tx"><b>{e(o["label"])}</b><div class="desc">{e(o.get("desc", ""))}</div></div>{ref}</div>'
            why = f'<div class="why">{e(it["why"])}</div>' if it.get("why") else ""
            body += f'<section class="item"><h2>{e(it["q"])}</h2>{why}<div class="opts">{opts}</div></section>'
        elif it["kind"] == "assume":
            rows = "".join(f'<div class="row"><button class="sw" data-it="{e(it["id"])}" data-v="{e(x["id"])}" onclick="tog(\'{e(it["id"])}\',\'{e(x["id"])}\')">바꾸기</button><div><div>{e(x["text"])}</div><div class="alt">바꾸면: {e(x.get("alt", ""))}</div></div></div>' for x in it["list"])
            body += f'<section class="item"><h2>{e(it["q"])}</h2>{rows}</section>'
        elif it["kind"] == "check":
            rows = ""
            for x in it["list"]:
                img = f'<div><img style="max-width:320px;border-radius:8px;margin-top:6px" src="{e(x["img"])}" alt=""></div>' if x.get("img") else ""
                rows += f'<div class="row"><button class="sw" data-it="{e(it["id"])}" data-v="{e(x["id"])}" onclick="tog(\'{e(it["id"])}\',\'{e(x["id"])}\')">적용</button><div>{e(x["text"])}{img}</div></div>'
            body += f'<section class="item"><h2>{e(it["q"])}</h2>{rows}</section>'
    return f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>질문 {q["n"]} · {e(q["title"])}</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/pretendard@1.3.9/dist/web/variable/pretendardvariable.min.css"><style>{CSS}</style></head><body>
<div class="wrap"><div class="kicker">질문 {q["n"]} / 4 · 고르고 아래 [답 복사]를 눌러 대화창에 붙여 주세요</div><h1>{e(q["title"])}</h1><p class="lead">{e(q.get("lead", ""))}</p>{body}<section class="item memo"><h2>말로 적기 <span class="alt">(선택)</span></h2><div class="alt" style="margin-bottom:8px">위에서 못 고른 것, 더 바꾸고 싶은 점이 있으면 적어 주세요(안 써도 돼요). 답 코드에 같이 붙어요.</div><textarea id="memo" placeholder="예: 홈 상단 요약 카드는 빼고, 버튼은 더 크게 해 주세요"></textarea></section></div>
<div class="bar"><code id="code"></code><button onclick="copyCode()">답 복사</button><span id="ok" class="alt"></span></div>
<script>{JS.replace("__Q__", json.dumps(q, ensure_ascii=False))}</script></body></html>'''


def main():
    a = sys.argv[1:]
    if a[0] == "--code":
        q = json.loads(pathlib.Path(a[1]).read_text(encoding="utf-8"))
        print(code(q, json.loads(a[2])))
        return
    if a[0] == "--read":
        q = json.loads(pathlib.Path(a[1]).read_text(encoding="utf-8"))
        print(read(q, a[2]))
        return
    src = pathlib.Path(a[0])
    q = json.loads(src.read_text(encoding="utf-8"))
    out = src.with_suffix(".html")
    out.write_text(page(q), encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
