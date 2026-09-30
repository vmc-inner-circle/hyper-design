"""웹 서비스의 컬러 팔레트 수집기 — 하네스를 '빌드할 때' 돌려 foundation/palettes/ 라이브러리를 만든다.
구동 중에는 라이브러리를 먼저 찾고, 맞는 도메인이 없을 때만 이 스크립트를 쓴다.

python3 palette_scrape.py <slug> <url> --name "마이리얼트립" --domain 여행 --tags "밝음,신뢰" -o foundation/palettes/

수집:
1. 모든 스타일시트의 CSS 변수 중 색 값 → 이름 끝이 숫자 단계(-50, _100, 500…)인 것을 스케일로 묶는다
2. 화면 요소의 실사용 색 → 채워진 버튼 배경·본문 글자·배경 빈도
3. 브랜드 스케일 = 실사용 주요 버튼 색에 가장 가까운 단계를 가진 스케일, 회색 = 평균 채도가 가장 낮은 스케일,
   오류 = 색상각이 빨강에 가장 가까운 스케일
"""
import argparse, colorsys, json, re, sys, pathlib, datetime
from playwright.sync_api import sync_playwright

def to_rgb(v):
    v = v.strip().lower()
    m = re.fullmatch(r"#([0-9a-f]{3}|[0-9a-f]{6})", v)
    if m:
        h = m.group(1); h = "".join(c * 2 for c in h) if len(h) == 3 else h
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    m = re.fullmatch(r"rgba?\(([^)]+)\)", v)
    if m:
        p = [x for x in re.split(r"[\s,/]+", m.group(1)) if x]
        if len(p) >= 3 and (len(p) == 3 or float(p[3].rstrip('%')) >= 0.99):
            return tuple(int(float(x)) for x in p[:3])
    return None
hexs = lambda c: "#%02x%02x%02x" % c
def hsv(c): return colorsys.rgb_to_hsv(*(x / 255 for x in c))
def dist(a, b): return sum((x - y) ** 2 for x, y in zip(a, b)) ** .5

JS_VARS = r"""()=>{ const out={};
  const walk=(rs)=>{ for(const r of rs){ if(r.style){ for(let i=0;i<r.style.length;i++){ const n=r.style[i];
      if(n.startsWith('--')) out[n]=r.style.getPropertyValue(n).trim(); } } if(r.cssRules) walk(r.cssRules); } };
  for(const ss of document.styleSheets){ try{ walk(ss.cssRules) }catch(e){} }
  const cs=getComputedStyle(document.documentElement);   // 계산된 값으로 var() 참조를 풀기
  for(const k of Object.keys(out)) { const v=cs.getPropertyValue(k).trim(); if(v) out[k]=v; }
  return out; }"""
JS_USED = r"""()=>{ const c={}; const add=(k,v)=>{ if(!v||v==='rgba(0, 0, 0, 0)') return; c[k]=c[k]||{}; c[k][v]=(c[k][v]||0)+1; };
  for(const el of document.querySelectorAll('body *')){ const r=el.getBoundingClientRect(); if(r.width<2||r.height<2) continue;
    const cs=getComputedStyle(el); const tag=el.tagName;
    const btn = tag==='BUTTON'||el.getAttribute('role')==='button'||(tag==='A'&&parseFloat(cs.paddingLeft)>=10&&cs.backgroundColor!=='rgba(0, 0, 0, 0)');
    if(btn) add('button.bg', cs.backgroundColor);
    if([...el.childNodes].some(n=>n.nodeType===3&&n.textContent.trim())) add(btn?'button.text':'text', cs.color);
    add('bg', cs.backgroundColor); }
  add('bg', getComputedStyle(document.body).backgroundColor); return c; }"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug"); ap.add_argument("url"); ap.add_argument("--name", required=True)
    ap.add_argument("--brand", default="", help="캡처를 보고 확정한 브랜드 색(#hex). 없으면 자동 판정(참고용)")
    ap.add_argument("--domain", default=""); ap.add_argument("--tags", default=""); ap.add_argument("-o", "--out", required=True)
    a = ap.parse_args()
    pathlib.Path('/tmp/hd/palette-shots').mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome")
        pg = b.new_context(viewport={"width": 1280, "height": 900}, locale="ko-KR",
                           user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140 Safari/537.36").new_page()
        pg.goto(a.url, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(5000)
        raw, used = pg.evaluate(JS_VARS), pg.evaluate(JS_USED)
        pg.screenshot(path=f"/tmp/hd/palette-shots/{a.slug}.png")
        b.close()
    colors = {k: to_rgb(v) for k, v in raw.items()}; colors = {k: v for k, v in colors.items() if v}
    # 스케일: 이름 끝 숫자 단계로 묶기
    scales = {}
    for k, c in colors.items():
        m = re.fullmatch(r"--(.+?)[-_]?(\d{2,3})", k)
        if m and 0 < int(m.group(2)) <= 1000: scales.setdefault(m.group(1), {})[m.group(2)] = c
    scales = {k: v for k, v in scales.items() if len(v) >= 5}
    def top(kind, pred=lambda c: True):
        items = [(to_rgb(v), n) for v, n in used.get(kind, {}).items()]
        items = [(c, n) for c, n in items if c and pred(c)]
        return max(items, key=lambda x: x[1])[0] if items else None
    chroma = lambda c: hsv(c)[1] > .35 and .3 < hsv(c)[2] < .98
    # 브랜드 색: 버튼 배경(가중 3)·버튼 글자·글자·배경 전체에서 가장 자주 쓰인 유채색 (배너 한두 개에 끌려가지 않게)
    score = {}
    for kind, w in (("button.bg", 3), ("button.text", 2), ("text", 1), ("bg", 1)):
        for v, n in used.get(kind, {}).items():
            c = to_rgb(v)
            if c and chroma(c): score[c] = score.get(c, 0) + n * w
    cands = sorted(score, key=score.get, reverse=True)[:6]
    brand_c = to_rgb(a.brand) if a.brand else (cands[0] if cands else None)   # 자동 판정은 참고용 — 빌드 때 캡처를 보고 --brand로 확정
    ink = top("text", lambda c: hsv(c)[2] < .3)
    if not brand_c:
        print(f"{a.slug}: 유채색을 찾지 못함 — 캡처를 보고 --brand로 지정", file=sys.stderr); sys.exit(2)
    mono = hsv(brand_c)[1] < .1          # 29CM·무신사처럼 검정이 브랜드인 모노 팔레트
    bgc = top("bg", lambda c: hsv(c)[1] < .1 and .9 < hsv(c)[2] < .995)
    synthesized = False
    if scales and mono:
        sat = lambda k: sum(hsv(c)[1] for c in scales[k].values()) / len(scales[k])
        gray_key = min(scales, key=sat); brand_key = gray_key
        brand_step = min(scales[gray_key], key=lambda st: dist(brand_c, scales[gray_key][st]))
        reds = [k for k in scales if k != gray_key and sat(k) > .3]
        mid = lambda k: scales[k][sorted(scales[k], key=int)[len(scales[k]) // 2]]
        danger_key = min(reds, key=lambda k: min(hsv(mid(k))[0], 1 - hsv(mid(k))[0])) if reds else None
    elif scales:
        brand_key = min(scales, key=lambda k: min(dist(brand_c, c) for c in scales[k].values()))
        brand_step = min(scales[brand_key], key=lambda st: dist(brand_c, scales[brand_key][st]))
        sat = lambda k: sum(hsv(c)[1] for c in scales[k].values()) / len(scales[k])
        gray_key = min(scales, key=sat)
        reds = [k for k in scales if k not in (brand_key, gray_key) and sat(k) > .3]
        mid = lambda k: scales[k][sorted(scales[k], key=int)[len(scales[k]) // 2]]
        danger_key = min(reds, key=lambda k: min(hsv(mid(k))[0], 1 - hsv(mid(k))[0])) if reds else None
    else:
        # 변수 스케일이 없으면 측정한 실제 색으로 합성: 회색은 실측 무채색, 브랜드 500은 실측 원본 그대로
        synthesized = True
        achro = []
        for kind in ("text", "bg", "button.bg", "button.text"):
            for v in used.get(kind, {}):
                c = to_rgb(v)
                if c and hsv(c)[1] < .12 and all(dist(c, x) > 8 for x in achro): achro.append(c)
        achro.sort(key=lambda c: -sum(c))
        steps = ["50", "80", "100", "200", "300", "400", "500", "600", "700", "800", "900"]
        pick = [achro[round(i * (len(achro) - 1) / (len(steps) - 1))] for i in range(len(steps))] if len(achro) >= 4 else None
        def ramp(base):
            h, l, s_ = colorsys.rgb_to_hls(*(x / 255 for x in base))
            L = {"50": .97, "80": .94, "100": .9, "200": .82, "300": .72, "400": .62, "600": l * .82, "700": l * .68, "800": l * .54, "900": l * .4}
            out = {st: tuple(round(x * 255) for x in colorsys.hls_to_rgb(h, L[st], s_)) for st in L}
            out["500"] = base; return out
        scales = {"gray": dict(zip(steps, pick)) if pick else ramp((134, 140, 148)), "red": ramp((229, 72, 77))}
        if not mono: scales["brand"] = ramp(brand_c)
        brand_key, brand_step, gray_key, danger_key = ("gray", "900", "gray", "red") if mono else ("brand", "500", "gray", "red")
        if mono: scales["gray"]["900"] = brand_c
    grays = sorted(scales[gray_key], key=int)
    bg_step = min(grays, key=lambda st: dist(bgc, scales[gray_key][st])) if bgc else grays[1]
    btn = brand_c
    out = {"name": a.name, "slug": a.slug, "domain": a.domain, "tags": [t for t in a.tags.split(",") if t],
           "source": f"{a.url} {'화면 실사용 색으로 합성' if synthesized else 'CSS 변수 + 화면 실사용 색'} ({datetime.date.today()} 수집)",
           "synthesized": synthesized,
           "ink": hexs(ink) if ink else hexs(scales[gray_key][grays[-1]]), "white": "#ffffff",
           "scales": {k: {st: hexs(c) for st, c in sorted(v.items(), key=lambda x: int(x[0]))} for k, v in scales.items()},
           "brand": brand_key, "brand_step": brand_step, "mono": mono, "gray": gray_key, "danger": danger_key,
           "bg_step": bg_step, "line_step": grays[min(len(grays) - 1, grays.index(bg_step) + 1)],
           "brand_confirmed": bool(a.brand), "candidates": [[hexs(c), score[c]] for c in cands],
           "measured": {"brand": hexs(btn), "ink": hexs(ink) if ink else None, "bg": hexs(bgc) if bgc else None}}
    pathlib.Path(a.out).mkdir(parents=True, exist_ok=True)
    (pathlib.Path(a.out) / f"{a.slug}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{a.slug}: {'합성' if synthesized else '변수'} · 브랜드 {brand_key}-{brand_step} {hexs(btn)} · 회색 {gray_key} · 오류 {danger_key}")

if __name__ == "__main__":
    main()
