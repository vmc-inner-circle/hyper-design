"""screens.json → 캔버스 (v3, docs/v13-spec.md §7 · success-criteria §9).

python3 build_canvas.py <out_dir>

출력
- out/index.html      : canvas_template.html 에 데이터 JSON(<script id="hd-data">)만 끼워 넣은 것.
                        헤더 = 제목 · 탭[Screens|Foundation|Components] · 팔레트 점 · [전체 보기][배율%]
                        (조작 그룹 3개: data-group="tabs"/"palette"/"view", 모드 전환 없음)
                        Screens 판 = 끌어서 이동, Ctrl/⌘+휠·핀치 확대, 카드 누르면 390×844 크게 보기.
- out/foundation.html : tokens.css 의 색 역할(쉬운 이름)·글자 단계·여백·모서리·그림자 견본. palette.js 로 즉시 전환.
- out/components.html : foundation/specimens.html 중 화면들이 실제로 쓴 클래스의 섹션만. 배지는 screens.json badges 로.

판 규칙(그대로 유지)
- 한 줄 = 한 흐름(group). 상태 변형(id에 --)은 원래 화면 바로 뒤에, 같은 줄에.
- 화살표는 분기(branches)에만. 줄을 넘으면 왼쪽 통로로 우회.
- 화면 아래: 목적 1줄 + 정책(policies) 최대 3줄, 넘치면 접기. 첫 배율 0.72.

screens.json:
{"groups": [...], "story": {...}, "badges": {"뜻": "is-brand", ...},
 "screens": [{"id", "file", "title", "group", "purpose", "policies": [], "branches": [{"to", "label"}]}]}
선택: decisions.json · palettes.json · credits.json([{slot,file,author,license,url,title}])
환경변수 HD_SPECIMENS 로 specimens.html 경로를 바꿀 수 있다(테스트용).
"""
import sys, os, json, re, html, pathlib

HERE = pathlib.Path(__file__).resolve().parent
TEMPLATE = HERE / "canvas_template.html"
SPECIMENS = pathlib.Path(os.environ.get("HD_SPECIMENS") or HERE.parent / "foundation" / "specimens.html")
SCALE, CARD, MODAL = 0.72, {"w": 375, "h": 812}, {"w": 390, "h": 844}

esc = lambda x: html.escape(str(x if x is not None else ""))


def load(p, default=None):
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default
    except Exception as e:
        print(f"경고: {p.name} 읽기 실패 — {e}", file=sys.stderr)
        return default


# ---------------------------------------------------------------- index.html
def build_index(out, m):
    screens = m["screens"]
    groups = list(m.get("groups") or [])
    for s in screens:
        g = s.get("group") or "기타"
        if g not in groups:
            groups.append(g)
    rows = {g: [] for g in groups}
    for s in screens:                                   # 상태 변형은 원래 화면 바로 뒤에
        if "--" in s["id"]:
            continue
        g = s.get("group") or "기타"
        rows[g].append(s)
        rows[g].extend(v for v in screens if v["id"].startswith(s["id"] + "--"))
    placed = {s["id"] for r in rows.values() for s in r}
    for s in screens:                                   # 원래 화면이 없는 상태 변형도 버리지 않는다
        if s["id"] not in placed:
            rows[s.get("group") or "기타"].append(s)
    card = lambda s: {"id": s["id"], "file": s.get("file") or f"screens/{s['id']}.html",
                      "title": s.get("title") or s["id"], "purpose": s.get("purpose") or "",
                      "policies": [p for p in (s.get("policies") or []) if p], "state": "--" in s["id"]}
    data_rows = [{"group": g, "screens": [card(s) for s in rows[g]]} for g in groups if rows[g]]
    ids = {s["id"] for s in screens}
    arrows = [{"from": s["id"], "to": b.get("to"), "label": b.get("label") or ""}
              for s in screens for b in (s.get("branches") or [])
              if b.get("to") in ids and b.get("to") != s["id"]]

    D = load(out / "decisions.json")
    decisions = None
    if D:
        label = {"lighten": "가볍게", "cut": "뺌", "later": "나중에"}
        items = [{"verdict": i["verdict"], "label": label[i["verdict"]], "name": i.get("name") or "",
                  "how": i.get("how") if i.get("verdict") == "lighten" else "", "why": i.get("why") or ""}
                 for i in D.get("items", []) if i.get("verdict") in label][:6]
        if items or D.get("core"):
            decisions = {"core": D.get("core") or "", "items": items}

    pal = load(out / "palettes.json")
    if pal and pal.get("options"):
        pal = {"default": pal.get("default"),
               "options": [{k: o.get(k) for k in ("slug", "name", "brand", "source")} for o in pal["options"][:3]]}
    else:
        pal = None
    credits = load(out / "credits.json", []) or []

    data = {"title": m.get("title") or "전체 화면 한눈에 보기", "scale": SCALE, "card": CARD, "modal": MODAL,
            "story": m.get("story") or None, "decisions": decisions, "rows": data_rows, "arrows": arrows,
            "palettes": pal, "credits": credits if isinstance(credits, list) else []}
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/").replace("<!--", "<\\!--")
    tpl = TEMPLATE.read_text(encoding="utf-8")
    marker = '<script id="hd-data" type="application/json">{}</script>'
    assert marker in tpl, "canvas_template.html 에 hd-data 자리가 없다"
    # 스크립트 없이도(그리고 도달성 검사가) 따라갈 수 있는 화면 링크 목록
    links = "".join(f'<li><a href="{esc(c["file"])}">{esc(c["title"])}</a></li>' for r in data_rows for c in r["screens"])
    nos = f'<noscript id="hd-links"><ul>{links}<li><a href="foundation.html">Foundation</a></li><li><a href="components.html">Components</a></li></ul></noscript>'
    tpl = tpl.replace('<noscript id="hd-links"></noscript>', nos)
    (out / "index.html").write_text(tpl.replace(marker, marker.replace("{}", blob)), encoding="utf-8")
    return len(screens), len(arrows), len(data_rows)


# ---------------------------------------------------------------- foundation.html
COLOR_GROUPS = [("bg", "배경"), ("text", "글자"), ("brand", "브랜드"), ("sem", "의미색 — 성공 · 주의 · 정보 · 오류"), ("etc", "선 · 그림자 · 기타")]
COLOR_NAMES = {   # 토큰 → (묶음, 쉬운 이름). 표에 없는 변수는 변수 이름 그대로 '기타'에.
    "--c-bg": ("bg", "화면 바탕"), "--c-surface": ("bg", "블록 바탕"), "--c-surface-2": ("bg", "한 단계 깊은 바탕"),
    "--c-disabled-bg": ("bg", "못 누르는 칸 바탕"), "--c-overlay": ("bg", "뒤를 가리는 막"),
    "--c-text": ("text", "본문 글자"), "--c-text-1": ("text", "제목·본문 글자"), "--c-text-2": ("text", "보조 글자"),
    "--c-text-3": ("text", "흐린 설명 글자"), "--c-text-disabled": ("text", "못 누르는 글자"),
    "--c-brand": ("brand", "버튼·강조 색"), "--c-on-brand": ("brand", "버튼 위 글자"), "--c-brand-text": ("brand", "강조 글자"),
    "--c-brand-tint": ("brand", "연한 강조 바탕"), "--c-brand-tint-text": ("brand", "연한 강조 위 글자"),
    "--c-brand-pressed": ("brand", "눌렀을 때 버튼 색"), "--c-focus": ("brand", "고른 칸 테두리"),
    "--c-success": ("sem", "성공 색"), "--c-success-tint": ("sem", "성공 연한 바탕"), "--c-success-tint-text": ("sem", "성공 바탕 위 글자"),
    "--c-warning": ("sem", "주의 색"), "--c-warning-tint": ("sem", "주의 연한 바탕"), "--c-warning-tint-text": ("sem", "주의 바탕 위 글자"),
    "--c-info": ("sem", "정보 색"), "--c-info-tint": ("sem", "정보 연한 바탕"), "--c-info-tint-text": ("sem", "정보 바탕 위 글자"),
    "--c-danger": ("sem", "오류 색"), "--c-danger-tint": ("sem", "오류 연한 바탕"), "--c-danger-tint-text": ("sem", "오류 바탕 위 글자"),
    "--c-line": ("etc", "구분선"), "--c-line-strong": ("etc", "진한 테두리"), "--c-shadow": ("etc", "그림자 색"),
}
FS_NAMES = {"title": "큰 제목", "h2": "블록 제목", "body": "본문", "strong": "강조 본문", "sub": "보조 글", "caption": "작은 글"}
SPACE_NAMES = {"--stack-s": "작은 간격", "--stack-m": "보통 간격", "--stack-l": "큰 간격", "--page-x": "화면 좌우 여백",
               "--block-pad": "블록 안쪽 여백", "--block-gap": "블록 사이", "--row-py": "줄 위아래 여백"}
R_NAMES = {"--r-s": "작은 모서리", "--r-m": "보통 모서리", "--r-l": "큰 모서리", "--r-pill": "알약 모양"}
SH_NAMES = {"--shadow-1": "약한 그림자", "--shadow-2": "뜬 그림자", "--shadow-3": "가장 뜬 그림자"}

FOUNDATION_CSS = """
*{box-sizing:border-box} body{margin:0;background:#F6F6F3;color:#1c1c1c;font-family:-apple-system,BlinkMacSystemFont,'Pretendard',sans-serif;word-break:keep-all;padding:24px 24px 64px}
.wrap{max-width:1200px;margin:0 auto} h1{font-size:24px;margin:0 0 4px} .lead{color:#666;margin:0 0 28px;font-size:15px}
h2{font-size:20px;margin:36px 0 12px} h3{font-size:15px;color:#555;margin:20px 0 10px;font-weight:700}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px}
.sw{background:#fff;border-radius:14px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.08)}
.sw .chip{height:72px;border-bottom:1px solid rgba(0,0,0,.06)}
.sw .meta{padding:10px 12px 12px} .sw .nm{font-size:16px;font-weight:700;line-height:1.35}
.tok{font:12px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;color:#777;word-break:break-all} .val{color:#333}
.type{background:#fff;border-radius:14px;padding:4px 16px} .type .ln{display:flex;align-items:baseline;gap:16px;padding:12px 0;border-bottom:1px solid #eee}
.type .ln:last-child{border:0} .type .lb{flex:none;width:150px} .type .lb b{display:block;font-size:14px}
.type .sample{font-family:var(--font);letter-spacing:var(--tracking);min-width:0;overflow:hidden;white-space:nowrap;text-overflow:ellipsis}
.box{background:#fff;border-radius:14px;padding:16px} .bar{height:20px;background:var(--c-brand,#2563eb);border-radius:3px;margin:8px 0 6px}
.rad{width:100%;height:72px;background:var(--c-brand-tint,#e7f0ff);border:2px solid var(--c-brand,#2563eb);margin-bottom:10px}
.shd{height:72px;background:#fff;border-radius:12px;margin:8px 4px 14px}
.box b{font-size:15px}
"""
FOUNDATION_JS = """
(function(){
  function read(){ var cs=getComputedStyle(document.documentElement);
    document.querySelectorAll('[data-var]').forEach(function(el){ var v=cs.getPropertyValue(el.getAttribute('data-var')).trim();
      var o=el.querySelector('.val'); if(o) o.textContent=v||'(없음)'; }); }
  var l=document.getElementById('tokens'); if(l) l.addEventListener('load',read);
  addEventListener('message',function(e){ if(e.data&&e.data.type==='hd-palette'){ [30,150,500,1200].forEach(function(t){setTimeout(read,t)}); } });
  addEventListener('DOMContentLoaded',read); addEventListener('load',read);
})();
"""


def root_vars(css):
    names = []
    for block in re.findall(r":root\s*\{(.*?)\}", css, re.S):
        for n in re.findall(r"(--[\w-]+)\s*:", re.sub(r"/\*.*?\*/", "", block, flags=re.S)):
            if n not in names:
                names.append(n)
    return names


def build_foundation(out):
    tok = out / "tokens.css"
    names = root_vars(tok.read_text(encoding="utf-8")) if tok.exists() else []
    tokcell = lambda n: f'<div class="tok">{esc(n)} · <span class="val"></span></div>'
    parts = []
    colors = [n for n in names if n.startswith("--c-")]
    by = {k: [] for k, _ in COLOR_GROUPS}
    for n in colors:
        g, nm = COLOR_NAMES.get(n, ("etc", n))
        by[g].append((n, nm))
    parts.append("<h2>색</h2>")
    for k, title in COLOR_GROUPS:
        if not by[k]:
            continue
        cells = "".join(f'<div class="sw" data-var="{esc(n)}" data-role="{k}"><div class="chip" style="background:var({esc(n)})"></div>'
                        f'<div class="meta"><div class="nm">{esc(nm)}</div>{tokcell(n)}</div></div>' for n, nm in by[k])
        parts.append(f'<h3>{esc(title)}</h3><div class="grid colors">{cells}</div>')
    fs = [n[5:] for n in names if n.startswith("--fs-")]
    if fs:
        lines = []
        for f in fs:
            style = f"font-size:var(--fs-{f});" + (f"font-weight:var(--fw-{f});" if f"--fw-{f}" in names else "") + (f"line-height:var(--lh-{f});" if f"--lh-{f}" in names else "")
            lines.append(f'<div class="ln" data-var="--fs-{esc(f)}"><div class="lb"><b>{esc(FS_NAMES.get(f, "--fs-" + f))}</b>{tokcell("--fs-" + f)}</div>'
                         f'<div class="sample" style="{style}">가나다 Aa 123 — 모임 날짜를 정해요</div></div>')
        parts.append(f'<h2>글자 단계</h2><div class="type">{"".join(lines)}</div>')
    sp = [n for n in names if n.startswith("--stack-") or n in SPACE_NAMES]
    if sp:
        cells = "".join(f'<div class="box" data-var="{esc(n)}"><b>{esc(SPACE_NAMES.get(n, n))}</b><div class="bar" style="width:var({esc(n)})"></div>{tokcell(n)}</div>' for n in sp)
        parts.append(f'<h2>여백</h2><div class="grid">{cells}</div>')
    rr = [n for n in names if n.startswith("--r-")]
    if rr:
        cells = "".join(f'<div class="box" data-var="{esc(n)}"><div class="rad" style="border-radius:var({esc(n)})"></div><b>{esc(R_NAMES.get(n, n))}</b>{tokcell(n)}</div>' for n in rr)
        parts.append(f'<h2>모서리</h2><div class="grid">{cells}</div>')
    sh = [n for n in names if n.startswith("--shadow-")]
    if sh:
        cells = "".join(f'<div class="box" data-var="{esc(n)}" style="background:#F1F1EE"><div class="shd" style="box-shadow:var({esc(n)})"></div><b>{esc(SH_NAMES.get(n, n))}</b>{tokcell(n)}</div>' for n in sh)
        parts.append(f'<h2>그림자</h2><div class="grid">{cells}</div>')
    if not names:
        parts.append('<p class="lead">tokens.css 가 없어 보여줄 토큰이 없어요.</p>')
    doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Foundation — 색·글자·여백</title>
<link id="tokens" rel="stylesheet" href="tokens.css"><script src="palette.js"></script>
<style>{FOUNDATION_CSS}</style></head><body><div class="wrap">
<h1>Foundation</h1><p class="lead">이 앱의 모든 화면이 쓰는 색·글자·여백. 위의 색 점을 누르면 여기도 바로 바뀌어요.</p>
{"".join(parts)}
</div><script>{FOUNDATION_JS}</script></body></html>"""
    (out / "foundation.html").write_text(doc, encoding="utf-8")
    return len(colors)


# ---------------------------------------------------------------- components.html
def used_classes(out):
    used = set()
    for f in (out / "screens").glob("*.html"):
        for v in re.findall(r"""\bclass\s*=\s*(?:"([^"]*)"|'([^']*)')""", f.read_text(encoding="utf-8", errors="ignore")):
            used.update((v[0] or v[1]).split())
    return used


def spec_sections(body):
    """<section class="spec" …>…</section> 을 중첩 section 까지 세어 잘라낸다 → [(start, end, open_tag, inner)]."""
    res, i = [], 0
    opener = re.compile(r"<section\b[^>]*>", re.I)
    tag = re.compile(r"<(/?)section\b[^>]*>", re.I)
    while True:
        mo = opener.search(body, i)
        if not mo:
            break
        if not re.search(r"""class\s*=\s*["'][^"']*\bspec\b""", mo.group(0)):
            i = mo.end(); continue
        depth, j = 1, mo.end()
        while depth:
            t = tag.search(body, j)
            if not t:
                j = len(body); break
            depth += -1 if t.group(1) else 1
            j = t.end()
        res.append((mo.start(), j, mo.group(0), body[mo.end():j - len("</section>")]))
        i = j
    return res


def attr(tag, name):
    mo = re.search(rf"""\b{name}\s*=\s*["']([^"']*)["']""", tag)
    return mo.group(1) if mo else ""


def badge_section(open_tag, inner, badges):
    cls = lambda c: ".badge" + ("." + esc(c) if c else "")
    if "spec-cell" in inner:                            # specimens.html 의 칸 모양을 그대로 따른다
        cells = "".join(f'<div class="spec-cell"><p class="spec-cap">{esc(k)} · {cls(c)}</p>'
                        f'<div class="spec-stage"><span class="badge {esc(c)}">{esc(k)}</span></div></div>' for k, c in badges.items())
        return f"{open_tag}{cells}</section>"
    head = re.match(r"\s*(<h[1-6]\b[^>]*>.*?</h[1-6]>)", inner, re.S)
    rows = "".join(f'<tr><td style="padding:8px 16px 8px 0"><span class="badge {esc(c)}">{esc(k)}</span></td>'
                   f'<td style="padding:8px 16px 8px 0">{esc(k)}</td><td style="padding:8px 0"><code>.badge{("." + esc(c)) if c else ""}</code></td></tr>'
                   for k, c in badges.items())
    table = (f'<table style="border-collapse:collapse;font-size:14px"><thead><tr style="text-align:left;color:#777">'
             f'<th style="padding:0 16px 6px 0;font-weight:600">모습</th><th style="padding:0 16px 6px 0;font-weight:600">뜻</th>'
             f'<th style="padding:0 0 6px;font-weight:600">클래스</th></tr></thead><tbody>{rows}</tbody></table>')
    return f'{open_tag}{head.group(1) if head else ""}{table}</section>'


def build_components(out, m):
    used = used_classes(out)
    badges = m.get("badges") or {}
    if not SPECIMENS.exists():
        sec = badge_section('<section class="spec" data-key="badge" data-title="배지">', "<h2>배지</h2>", badges) if badges else ""
        doc = (f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
               f'<title>Components</title><link id="tokens" rel="stylesheet" href="tokens.css"><link rel="stylesheet" href="components.css">'
               f'<script src="palette.js"></script></head><body style="padding:24px;font-family:-apple-system,sans-serif">'
               f'<p>부품 견본 파일(foundation/specimens.html)이 아직 없어요.</p>{sec}</body></html>')
        (out / "components.html").write_text(doc, encoding="utf-8")
        print(f"경고: {SPECIMENS} 없음 — components.html 은 배지만", file=sys.stderr)
        return 0
    src = SPECIMENS.read_text(encoding="utf-8")
    # 링크 경로를 out/ 기준으로
    src = re.sub(r"""(<link\b[^>]*\bid\s*=\s*["']tokens["'][^>]*\bhref\s*=\s*["'])[^"']*(["'])""", r"\1tokens.css\2", src)
    src = re.sub(r"""(<link\b[^>]*\bhref\s*=\s*["'])[^"']*\btokens\.css(["'][^>]*\bid\s*=\s*["']tokens["'])""", r"\1tokens.css\2", src)
    src = re.sub(r"""(\bhref\s*=\s*["'])[^"']*components\.css(["'])""", r"\1components.css\2", src)
    src = re.sub(r"""(\bsrc\s*=\s*["'])[^"']*palette\.js(["'])""", r"\1palette.js\2", src)
    out_parts, last, kept = [], 0, 0
    for s, e, open_tag, inner in spec_sections(src):
        out_parts.append(src[last:s]); last = e
        key = attr(open_tag, "data-key")
        if key not in used:
            continue
        kept += 1
        out_parts.append(badge_section(open_tag, inner, badges) if key == "badge" and badges else src[s:e])
    out_parts.append(src[last:])
    (out / "components.html").write_text("".join(out_parts), encoding="utf-8")
    return kept


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: python3 build_canvas.py <out_dir>")
    out = pathlib.Path(sys.argv[1])
    m = json.loads((out / "screens.json").read_text(encoding="utf-8"))
    n, na, ng = build_index(out, m)
    nc = build_foundation(out)
    nk = build_components(out, m)
    print(f"canvas v3: {n} screens, {na} branch arrows, {ng} groups, scale {SCALE} · foundation {nc} colors · components {nk} sections")


if __name__ == "__main__":
    main()
