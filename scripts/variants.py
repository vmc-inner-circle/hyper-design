"""디자인 5벌 (K13, 10-08). 공통 화면(내용) 하나에 겉모습 5벌을 입혀 앱 5개 + 비교 첫 페이지를 만든다.

    python scripts/variants.py build design            # design/app(공통) + design/var/<k>/(겉모습) → design/v/<k>/ 앱 5개
                                                       #  → 대표 화면 캡처 → lint(디자인 규칙 자동 검사) → design/index.html(5개 비교)
    python scripts/variants.py build design --only v2,v4   # 고친 벌만 다시
    python scripts/variants.py build design --no-shots     # 캡처·검사 없이 조립만(빠른 확인)
    python scripts/variants.py build design --only v3 --no-gallery   # 자가 교정 에이전트용: 내 벌만 다시 조립·캡처·검사
    python scripts/variants.py gallery design              # 비교 페이지만 다시(교정이 다 끝난 뒤 메인이 한 번)
    python scripts/variants.py share design                # 팀 공유용 단일 파일 design/share.html(그림 안에 넣음) — 실행기가 끝난 뒤 자동

검사 뒤 design/v/<k>/fix.md = 그 벌의 고칠 목록(FAIL 먼저, 위치·고치는 법). 자가 교정은 이 파일을 보고 한다.

입력
  design/app/base.json · design/app/screens/*.json   공통(모든 벌이 같은 화면·같은 내용). tokens 는 기본값.
  design/var/<k>/var.json   {"name":"이 디자인의 이름","concept":"한 줄 컨셉","from":"스타일 id 또는 free","slopOk":{"S6":"이유"}(선택),
                             "tokens":{… base.json tokens 를 덮어씀 — nav·pcnav·글꼴·색·모서리·밀도 …},
                             "hero":["대표 화면 id", …]}          (hero = 캡처·비교에 쓸 화면, 없으면 역할별 첫 화면)
  design/var/<k>/style.css  이 벌의 디자인 시스템 CSS(80~200줄)
  design/var/<k>/screens/<id>.html | <id>.json   이 벌에서만 바꾸는 화면(직접 그린 대표 화면, 배치를 바꾼 화면)
출력
  design/v/<k>/index.html · app.html · shots/<id>-m.png · <id>-d.png · lint.json
  design/index.html  5벌 비교(폰·PC 대표 화면, 컨셉, 검사 점수, 들어가기)
"""
import json
import pathlib
import shutil
import subprocess
import os
import sys

HERE = pathlib.Path(__file__).resolve().parent
M = {"width": 390, "height": 844}
D = {"width": 1440, "height": 900}
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def assemble(design, k):
    """design/var/<k> + design/app → design/v/<k> 를 조립하고 app.py 로 그린다."""
    common, var, out = design / "app", design / "var" / k, design / "v" / k
    if out.exists():
        shutil.rmtree(out)
    (out / "screens").mkdir(parents=True)
    base = json.loads((common / "base.json").read_text(encoding="utf-8"))
    vj = json.loads((var / "var.json").read_text(encoding="utf-8")) if (var / "var.json").exists() else {}
    base["tokens"] = {**base.get("tokens", {}), **vj.get("tokens", {})}
    base["variant"] = {"id": k, "name": vj.get("name", k), "concept": vj.get("concept", ""), "from": vj.get("from", "")}
    if vj.get("slopOk"):  # 근거 있는 약한 슬롭 허용(예: {"S6":"종이 은유라 크림 배경"}) — lint 가 읽는다
        base["slopOk"] = vj["slopOk"]
    (out / "base.json").write_text(json.dumps(base, ensure_ascii=False, indent=1), encoding="utf-8")
    for f in (common / "screens").glob("*"):
        if f.suffix in (".json", ".html"):
            shutil.copy(f, out / "screens" / f.name)
    if (var / "screens").exists():
        for f in (var / "screens").glob("*"):
            if f.suffix in (".json", ".html"):
                shutil.copy(f, out / "screens" / f.name)
        for f in (var / "screens").glob("*.html"):  # 직접 그린 화면은 공통 블록·side 를 같이 그리지 않는다(아래에 또 그려져 겹침 FAIL)
            jf = out / "screens" / (f.stem + ".json")
            if jf.exists() and not (var / "screens" / jf.name).exists():
                x = json.loads(jf.read_text(encoding="utf-8"))
                x["blocks"], x["side"], x["layout"] = [], [], "wide"  # 한 칸 전체 폭
                jf.write_text(json.dumps(x, ensure_ascii=False), encoding="utf-8")
    css = var / "style.css" if (var / "style.css").exists() else common / "style.css"
    if css.exists():
        shutil.copy(css, out / "style.css")
    r = subprocess.run([sys.executable, str(HERE / "app.py"), str(out)], capture_output=True, text=True, encoding="utf-8", env=ENV)
    if r.returncode:
        print(f"[{k}] 조립 실패:\n{r.stderr[-1500:]}")
        return None
    spec = json.loads((out / "app.json").read_text(encoding="utf-8"))
    hero = vj.get("hero") or [r["nav"][0] for r in spec.get("roles", []) if r.get("nav")]  # 기본 = 역할별 첫 탭(홈)
    if not hero:
        hero = [spec["screens"][0]["id"]]
    ids = {s["id"] for s in spec["screens"]}
    return {"k": k, "out": out, "spec": spec, "var": vj, "hero": [h for h in hero if h in ids][:4]}


def capture_one(it):
    """벌 하나의 폰 전 화면 + PC 대표 화면 캡처 + 흐름 지도. 벌마다 브라우저 하나(프로세스가 따로라 동시에 돌려도 된다)."""
    from playwright.sync_api import sync_playwright
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    with sync_playwright() as pw:
        try:
            b = pw.chromium.launch(channel="chrome")
        except Exception:
            b = pw.chromium.launch()
        sd = it["out"] / "shots"
        sd.mkdir(exist_ok=True)
        for suffix, vp in (("m", M), ("d", D)):
            pg = b.new_page(viewport=vp)
            pg.goto((it["out"] / "app.html").resolve().as_uri())
            pg.wait_for_timeout(800)
            ids = [s["id"] for s in it["spec"]["screens"]] if suffix == "m" else it["hero"]  # 폰은 전 화면(흐름 지도용)
            (sd / "all").mkdir(exist_ok=True)
            for sid in ids:
                pg.set_viewport_size(vp)
                pg.evaluate(f"location.hash={json.dumps(sid)}")
                pg.wait_for_timeout(250)
                p = sd / (f"{sid}-{suffix}.png" if sid in it["hero"] else f"all/{sid}-{suffix}.png")
                pg.screenshot(path=str(p))  # 첫 화면 크기 그대로(비교용 — 스크롤 아래는 앱에서)
                if suffix == "m" and sid in it["hero"]:
                    shutil.copy(p, sd / "all" / f"{sid}-m.png")
            pg.close()
        b.close()
    print(f"[{it['k']}] 캡처 폰 {len(it['spec']['screens'])}장 · PC {len(it['hero'])}장")
    try:  # 흐름 지도(시나리오별·기능별·탭 묶음별 화살표) — 10-12
        import flowmap
        flowmap.build(it["out"])
    except Exception as x:
        print(f"[{it['k']}] 흐름 지도 실패: {x}")


def capture(items):
    """여러 벌이면 벌마다 프로세스를 하나씩 띄워 동시에 찍는다(차례로 찍으면 5벌에 ~1.5분)."""
    if len(items) < 2:
        for it in items:
            capture_one(it)
        return
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=min(5, len(items))) as ex:
        list(ex.map(capture_one, items))


def lint_start(it):
    lp = HERE / "lint.py"
    if not lp.exists():
        return None
    return subprocess.Popen([sys.executable, str(lp), str(it["out"] / "app.html"), "--json", str(it["out"] / "lint.json")],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", env=ENV)


def lint(it, proc):
    if proc is None:
        return None
    out = proc.communicate()[0]
    print(f"[{it['k']}] 검사: {(out.strip().splitlines() or ['(결과 없음)'])[-1]}")
    try:
        L = json.loads((it["out"] / "lint.json").read_text(encoding="utf-8"))
    except Exception:
        return None
    first = it["out"].parent.parent / "var" / it["k"] / "lint-first.json"  # 교정 전 첫 검사(자가 교정·개선 루프 비교용, 재조립에도 남게 var 쪽에)
    if not first.exists():
        first.write_text(json.dumps(L, ensure_ascii=False), encoding="utf-8")
    bad = [r for r in L["rules"] if r["status"] != "PASS"]
    lines = [f"# {it['k']} 고칠 목록 (자가 교정 — FAIL 먼저, WARN 은 시간이 남으면)", "",
             f"고치는 파일: design/var/{it['k']}/style.css · design/var/{it['k']}/screens/*.html (공통 design/app 은 건드리지 않는다)",
             f"다시 검사: python scripts/variants.py build design --only {it['k']} --no-gallery", ""]
    for r in sorted(bad, key=lambda r: r["status"] != "FAIL"):
        lines.append(f"## {r['status']} {r['id']} {r['name']} — {r['msg']}")
        lines += [f"- {x}" for x in r["examples"][:8]]
        lines += [f"- 고치는 법: {r['fix']}", ""]
    (it["out"] / "fix.md").write_text("\n".join(lines) if bad else "# 고칠 것 없음\n", encoding="utf-8")
    return L


GALLERY_CSS = """
:root{--bg:#F3F3F0;--ink:#151716;--mut:#5E6461;--line:#DCDDD8;--card:#fff;--ok:#1E7A4C;--warn:#A15C00;--bad:#B3261E}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#121413;--ink:#ECEEEC;--mut:#A0A6A3;--line:#2B2F2D;--card:#1A1D1C;--ok:#5BC08A;--warn:#E3A44A;--bad:#F08A80}}
*{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--ink);font-family:"Pretendard Variable",Pretendard,"Malgun Gothic",sans-serif;line-height:1.5;word-break:keep-all}
header{padding:28px 24px 8px;max-width:1500px;margin:0 auto} h1{font-size:26px;margin:0 0 4px;letter-spacing:-.01em} .sub{color:var(--mut);font-size:15px}
.bar{display:flex;gap:8px;margin-top:14px} .bar button{border:1px solid var(--line);background:var(--card);color:var(--ink);padding:8px 14px;border-radius:999px;font:inherit;font-size:14px;cursor:pointer} .bar button.a{background:var(--ink);color:var(--bg);border-color:var(--ink)}
main{max-width:1500px;margin:0 auto;padding:16px 24px 48px;display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:20px}
body.d main{grid-template-columns:repeat(auto-fill,minmax(440px,1fr))}
.v{background:var(--card);border:1px solid var(--line);border-radius:16px;overflow:hidden;display:flex;flex-direction:column}
.shots{display:flex;gap:6px;overflow-x:auto;padding:10px;background:color-mix(in srgb,var(--line) 35%,transparent);scroll-snap-type:x mandatory}
.shots a{flex:0 0 100%;scroll-snap-align:start} .shots img{width:100%;display:block;border-radius:8px;border:1px solid var(--line)}
.shots .d{display:none} body.d .shots .d{display:block} body.d .shots .m{display:none}
.meta{padding:14px 16px 16px;display:flex;flex-direction:column;gap:8px;flex:1}
.meta h2{font-size:18px;margin:0;display:flex;gap:8px;align-items:baseline} .meta h2 small{font-size:13px;color:var(--mut);font-weight:500}
.meta p{margin:0;font-size:14px;color:var(--mut)}
.lint{font-size:13px;display:flex;gap:10px;flex-wrap:wrap} .lint b{font-weight:700} .ok{color:var(--ok)} .warn{color:var(--warn)} .bad{color:var(--bad)}
.gos{margin-top:auto;display:flex;gap:8px} .go.alt{background:transparent;color:var(--ink);border:1px solid var(--line)} .go{flex:1;display:inline-block;text-align:center;padding:10px;border-radius:10px;background:var(--ink);color:var(--bg);text-decoration:none;font-weight:600;font-size:15px}
@media (max-width:600px){header,main{padding-left:16px;padding-right:16px} body.d main{grid-template-columns:1fr}}
.rec{max-width:1500px;margin:0 auto;padding:8px 24px 32px} .rec h2{font-size:22px;margin:16px 0 4px} .rec h3{font-size:16px;margin:24px 0 8px} .mut{color:var(--mut);font-size:13px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin-top:12px} .kpis div{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 16px}
.kpis b{display:block;font-size:22px} .kpis span{font-size:13px;color:var(--mut)}
.tw{overflow-x:auto} table{border-collapse:collapse;width:100%;background:var(--card);border:1px solid var(--line);font-size:14px}
th,td{text-align:left;padding:8px 12px;border-bottom:1px solid var(--line);vertical-align:top;white-space:nowrap} th{font-size:13px;color:var(--mut);font-weight:600}
tr.sum td{font-weight:700} tr.wait td{color:var(--mut)} tr.mutrow td{background:color-mix(in srgb,var(--line) 25%,transparent)}
"""


def fmt_t(sec):
    return f"{sec / 60:.1f}분" if sec >= 60 else f"{sec:.0f}초"


def ntok(u):
    return (u.get("in", 0) + u.get("w5", 0) + u.get("w1h", 0) + u.get("read", 0)), u.get("out", 0)


def _sum_usage(agents):
    u = {}
    for x in agents:
        for kk, vv in x["usage"].items():
            u[kk] = u.get(kk, 0) + vv
    return u


def record(design, items):
    """실행 기록(10-12, 사용자: "최종 파일에 각 작업물별, 각 단계별 시간, 토큰 사용량 — 팀에서 공유"). 실행 폴더의 _report.json(hs_report.py)을 읽는다."""
    rf = design.parent / "_report.json"
    if not rf.exists():
        return ""
    R = json.loads(rf.read_text(encoding="utf-8"))
    tot_in, tot_out = ntok(R["total"])
    head = (f'<div class="kpis"><div><b>{fmt_t(R["work_s"])}</b><span>하네스 작업 시간(사용자 답 대기 {fmt_t(R["wait_s"])} 뺌)</span></div>'
            f'<div><b>${R["cost"]:.2f}</b><span>환산 비용(API 정가 · 구독이라 실제 청구 아님)</span></div>'
            f'<div><b>{tot_in / 1e6:.2f}M</b><span>입력 토큰(캐시 읽기 {R["total"].get("read", 0) / 1e6:.2f}M 포함)</span></div>'
            f'<div><b>{tot_out:,}</b><span>출력 토큰</span></div>'
            f'<div><b>{", ".join(m.replace("claude-", "") for m in R["models"])}</b><span>모델 · effort {esc(R.get("effort", ""))}</span></div></div>')
    rows = []
    for x in R["stages"]:
        ti, to = ntok(x["usage"])
        cls = ' class="wait"' if x["stage"].startswith("⏸") else ""
        rows.append(f'<tr{cls}><td>{esc(x["stage"])}</td><td>{fmt_t(x["sec"])}</td><td>{x["calls"]}</td><td>{ti:,}</td><td>{to:,}</td><td>${x["cost"]:.2f}</td></tr>')
    rows.append(f'<tr class="sum"><td>합계(작업)</td><td>{fmt_t(R["work_s"])}</td><td></td><td>{tot_in:,}</td><td>{tot_out:,}</td><td>${R["cost"]:.2f}</td></tr>')
    ag = R.get("agents", [])
    vr = []
    for it in items:
        k, vj = it["k"], it["var"]
        mine = [a for a in ag if a.get("variant") == k]
        first = design / "var" / k / "lint-first.json"
        f0 = json.loads(first.read_text(encoding="utf-8"))["counts"] if first.exists() else {}
        f1 = (it.get("lint") or {}).get("counts", {})
        cells = []
        for kind in ("겉모습", "교정"):
            a = [x for x in mine if x.get("kind") == kind]
            ti, to = ntok(_sum_usage(a))
            cells.append(f'<td>{fmt_t(max(x["sec"] for x in a)) if a else "-"}</td><td>{ti:,} / {to:,}</td><td>${sum(x["cost"] for x in a):.2f}</td>')
        vr.append(f'<tr><td><b>{esc(vj.get("name", k))}</b> {esc(k)}<br><span class="mut">레퍼런스 {esc(vj.get("from", ""))}</span></td>{"".join(cells)}'
                  f'<td>${sum(x["cost"] for x in mine):.2f}</td><td>실패 {f0.get("FAIL", "-")} → <b>{f1.get("FAIL", "-")}</b> · 주의 {f0.get("WARN", "-")} → {f1.get("WARN", "-")}</td></tr>')
    shared = [a for a in ag if not a.get("variant")]
    if shared:
        ti, to = ntok(_sum_usage(shared))
        c = sum(x["cost"] for x in shared)
        vr.append(f'<tr class="mutrow"><td><b>공통 — 화면 내용</b><br><span class="mut">에이전트 {len(shared)}개 · 5벌이 같이 씀</span></td>'
                  f'<td colspan="6">{fmt_t(max(x["sec"] for x in shared))} · 입력 {ti:,} / 출력 {to:,}</td><td>${c:.2f}</td><td></td></tr>')
    main_cost = R["cost"] - sum(a["cost"] for a in ag)
    return ('<section class="rec"><h2>실행 기록</h2><p class="mut">시간·토큰은 하네스 세션 기록(메인 + 서브 에이전트)을 단계 표지로 나눠 합산했어요. '
            '에이전트는 동시에 돌아서 단계 시간 = 가장 늦게 끝난 것 기준.</p>' + head +
            '<h3>단계별</h3><div class="tw"><table><tr><th>단계</th><th>시간</th><th>API 호출</th><th>입력 토큰(캐시 포함)</th><th>출력 토큰</th><th>비용</th></tr>'
            + "".join(rows) + '</table></div>'
            '<h3>작업물(벌)별</h3><div class="tw"><table><tr><th>벌</th><th>겉모습 시간</th><th>겉모습 입력/출력 토큰</th><th>겉모습 비용</th>'
            '<th>교정 시간</th><th>교정 입력/출력 토큰</th><th>교정 비용</th><th>벌 합계</th><th>예쁨·슬롭 검사(교정 전 → 후)</th></tr>'
            + "".join(vr) + '</table></div>'
            f'<p class="mut">나머지 ${main_cost:.2f} 는 메인(설계·조립·검사·마무리). 비용 환산 단가는 실행 폴더 _report.md 맨 아래.</p></section>')


def share(design):
    """팀 공유용 단일 파일(design/share.html) — 비교 페이지의 그림을 JPEG 로 줄여 안에 넣는다(링크된 앱·흐름 지도는 폴더가 있어야 열림)."""
    import base64
    import io
    import re as _re
    from PIL import Image
    src = (design / "index.html").read_text(encoding="utf-8")

    def emb(m):
        f = design / m.group(1)
        if not f.exists():
            return m.group(0)
        im = Image.open(f).convert("RGB")
        im.thumbnail((720, 720) if f.stem.endswith("-m") else (1100, 1100))
        b = io.BytesIO()
        im.save(b, "JPEG", quality=70)
        return 'src="data:image/jpeg;base64,' + base64.b64encode(b.getvalue()).decode() + '"'
    out = _re.sub(r'src="(v/[^"]+\.png)"', emb, src)
    out = out.replace('<header>', '<header><p class="mut" style="margin:0 0 8px">공유용 단일 파일 — 그림은 안에 들어 있어요. "둘러보기·흐름 지도" 는 실행 폴더(design/)가 있어야 열려요.</p>', 1)
    (design / "share.html").write_text(out, encoding="utf-8")
    print(design / "share.html", f"{len(out) / 1e6:.1f}MB")


def credits(design):
    cf = design / "_photos" / "credits.json"
    if not cf.exists():
        return ""
    cr = json.loads(cf.read_text(encoding="utf-8"))
    li = "".join(f'<li><a href="{esc(v.get("source", ""))}">{esc(v.get("title") or k)}</a> — {esc(v.get("creator") or "")} · {esc(v.get("license", ""))}</li>' for k, v in cr.items())
    return f'<footer style="max-width:1500px;margin:0 auto;padding:0 24px 48px;font-size:13px;color:var(--mut)"><b>사진 출처</b> (Openverse · 무료 라이선스)<ul>{li}</ul></footer>'


def gallery(design, items, name, tagline):
    cards = []
    for it in items:
        vj, k = it["var"], it["k"]
        shots = "".join(
            f'<a class="{dv}" href="v/{k}/index.html"><img loading="lazy" src="v/{k}/shots/{h}-{dv}.png" alt="{esc(vj.get("name", k))} · {esc(next((s["title"] for s in it["spec"]["screens"] if s["id"] == h), h))}"></a>'
            for h in it["hero"] for dv in ("m", "d"))
        L = it.get("lint") or {}
        lint_html = ""
        if L:
            c = L.get("counts", {})
            lint_html = (f'<div class="lint"><span class="ok">통과 <b>{c.get("PASS", 0)}</b></span>'
                         f'<span class="warn">주의 <b>{c.get("WARN", 0)}</b></span><span class="bad">실패 <b>{c.get("FAIL", 0)}</b></span></div>')
        cards.append(f'''<article class="v"><div class="shots">{shots}</div><div class="meta">
<h2>{esc(vj.get("name", k))} <small>{esc(k)}</small></h2><p>{esc(vj.get("concept", ""))}</p>{lint_html}
<div class="gos"><a class="go" href="v/{k}/index.html">이 디자인 둘러보기</a><a class="go alt" href="v/{k}/flow.html">흐름 지도</a></div></div></article>''')
    html = f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(name)} 디자인 5벌</title><link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/pretendard@1.3.9/dist/web/variable/pretendardvariable.min.css"><style>{GALLERY_CSS}</style></head>
<body><header><h1>{esc(name)} · 디자인 {len(items)}벌</h1><div class="sub">{esc(tagline)} — 같은 화면·같은 내용에 겉모습만 다르게 입혔어요. 그림을 옆으로 넘기면 다른 화면, 누르면 그 디자인으로 들어가요.</div>
<div class="bar"><button class="a" onclick="dev('m',this)">폰</button><button onclick="dev('d',this)">PC</button></div></header>
<main>{"".join(cards)}</main>{record(design, items)}{credits(design)}
<script>function dev(d,b){{document.body.className=d==='d'?'d':'';document.querySelectorAll('.bar button').forEach(x=>x.classList.toggle('a',x===b))}}</script></body></html>'''
    (design / "index.html").write_text(html, encoding="utf-8")
    print(design / "index.html")


def main():
    a = sys.argv[1:]
    if a and a[0] == "share":
        share(pathlib.Path(a[1] if len(a) > 1 else "design"))
        return
    if not a or a[0] not in ("build", "gallery"):
        print(__doc__)
        return
    design = pathlib.Path(a[1] if len(a) > 1 else "design")
    ks = sorted(p.name for p in (design / "var").iterdir() if p.is_dir())
    only = set(a[a.index("--only") + 1].split(",")) if "--only" in a else None
    if a[0] == "gallery":  # 조립·캡처 없이 비교 페이지만 다시(자가 교정이 끝난 뒤)
        only = {"__none__"}
    items = []
    for k in ks:
        if only and k not in only:
            it = {"k": k, "out": design / "v" / k}
            if (it["out"] / "app.json").exists():  # 다시 안 만든 벌도 비교 페이지에는 넣는다
                it["spec"] = json.loads((it["out"] / "app.json").read_text(encoding="utf-8"))
                it["var"] = json.loads((design / "var" / k / "var.json").read_text(encoding="utf-8"))
                it["hero"] = [p.stem[:-2] for p in sorted((it["out"] / "shots").glob("*-m.png"))]
                lj = it["out"] / "lint.json"
                it["lint"] = json.loads(lj.read_text(encoding="utf-8")) if lj.exists() else None
                items.append(it)
            continue
        it = assemble(design, k)
        if it:
            items.append(it)
            print(f"[{k}] 조립: 화면 {len(it['spec']['screens'])}장 · 대표 {','.join(it['hero'])}")
    fresh = [it for it in items if not only or it["k"] in only]
    if "--no-shots" not in a and fresh:
        procs = [lint_start(it) for it in fresh]  # 검사는 벌마다 동시에(캡처와 겹치지 않게 조립 직후 시작)
        capture(fresh)
        for it, pr in zip(fresh, procs):
            it["lint"] = lint(it, pr)
    if "--no-gallery" in a:
        return
    if a[0] == "gallery":  # 다시 빌드하지 않고도 벌마다 마지막 검사 결과를 보여 준다(완료 메시지용)
        for it in items:
            c = (it.get("lint") or {}).get("counts")
            if c:
                print(f"[{it['k']}] 검사: 합계 PASS {c.get('PASS', 0)} · WARN {c.get('WARN', 0)} · FAIL {c.get('FAIL', 0)}")
    base = json.loads((design / "app" / "base.json").read_text(encoding="utf-8"))
    gallery(design, items, base.get("name", "앱"), base.get("tagline", ""))


if __name__ == "__main__":
    main()
