"""브랜드 시드 시트 — 하네스를 '빌드할 때' 1회. 후보를 자동으로 거르고, 사람이 볼 미리보기 시트를 만든다.

python3 seed_sheet.py                 → foundation/palettes/seed-sheet.png + seed_filtered.json(번호 붙은 통과 목록)
python3 seed_sheet.py --approve "3,7"  → 3·7번을 뺀 나머지를 seeds.json으로(사람 승인)

후보: palettes/seed_candidates.json(실제 서비스 웹에서 측정) + 라이브러리 10곳 브랜드색 + palettes/seed_extra.json(디자이너 결과물 등)
거르기: 흰 글자 대비 ≥3(또는 3까지 어둡게 해도 원색과 거의 같음, 아니면 먹색 글자 4.5 이상인 밝은 브랜드 — bright) · OKLCH 채도 C ≥ 0.08 · 명도 L 0.35~0.78 · 오류 빨강과 색상각 15° 이내 제외 · 도메인이 겹치는 것끼리 ΔE(OKLab×100) < 8이면 하나만 · 밝은 색은 3:1까지 어둡게 해도 ΔE ≤ 16이면 통과(어둡게 한 값으로)
"""
import sys, json, math, pathlib, subprocess, argparse, colorsys
HERE = pathlib.Path(__file__).resolve().parent.parent / "foundation"
sys.path.insert(0, str(HERE)); from derive import hex2rgb, rgb2hex, contrast, darken_until, oklch, de, bright_ok   # noqa
P = HERE / "palettes"

def hue(rgb): return colorsys.rgb_to_hls(*rgb)[0] * 360
def hgap(a, b): d = abs(hue(a) - hue(b)) % 360; return min(d, 360 - d)
RED = hex2rgb("#E5484D")
TONE = lambda h: "warm" if (h < 70 or h >= 330) else ("cool" if 170 <= h < 270 else "neutral")

def collect():
    c = []
    f = P / "seed_candidates.json"
    if f.exists():
        for x in json.loads(f.read_text(encoding="utf-8")):
            if x.get("hex"): c.append({"slug": x["slug"], "name": x["name"], "hex": x["hex"].upper(), "domains": x.get("domains") or [x.get("domain", "")], "source": x.get("url", ""), "confidence": x.get("confidence", "")})
    for g in sorted(P.glob("*.json")):
        try: d = json.loads(g.read_text(encoding="utf-8"))
        except Exception: continue
        if isinstance(d, dict) and isinstance(d.get("scales"), dict) and not d.get("mono"):
            c.append({"slug": g.stem, "name": d["name"], "hex": d["scales"][d["brand"]][d["brand_step"]].upper(), "domains": d.get("domain", "").split("·"), "source": "라이브러리", "tags": d.get("tags", [])})
    f = P / "seed_extra.json"
    if f.exists(): c += json.loads(f.read_text(encoding="utf-8"))
    # 이미 승인된 시드(seeds.json)에 손으로 붙인 성격 낱말·도메인·둥글기는 다시 걸러도 잃지 않는다
    old = {x["slug"]: x for x in json.loads((P / "seeds.json").read_text(encoding="utf-8"))} if (P / "seeds.json").exists() else {}
    for x in c:
        o = old.get(x["slug"])
        if not o: continue
        x["domains"] = list(dict.fromkeys((o.get("domains") or []) + (x.get("domains") or [])))
        for k in ("tags", "shape", "gender", "gender_source"):
            if o.get(k) and not x.get(k): x[k] = o[k]
    return c

def filt(c):
    keep, log = [], []
    for x in c:
        rgb = hex2rgb(x["hex"]); L, C, H, _ = oklch(rgb)
        why = None
        if contrast((1, 1, 1), rgb) < 3:
            d = darken_until(rgb, (1, 1, 1), 3)
            if de(d, rgb) <= 16: x["hex"] = rgb2hex(d).upper(); rgb = d; L, C, H, _ = oklch(rgb)
            elif bright_ok(rgb): x["bright"] = True        # 노랑처럼 어둡게 하면 다른 색이 되는 밝은 브랜드 — 면은 그대로, 버튼 글자·선은 먹색(derive.py)
            else: why = f"흰 글자 대비 {contrast((1,1,1), rgb):.1f}"
        if not why and C < 0.08 and not x.get("mono"): why = f"탁함(C {C:.3f})"
        if not why and not (0.35 <= L <= 0.78) and not x.get("bright") and not x.get("mono"): why = f"명도 L {L:.2f}"
        if not why and hgap(rgb, RED) < 15 and not x.get("mono"): why = "오류 빨강과 겹침"
        if not why:
            # 같은 도메인끼리만 하나로 — 색이 비슷해도 도메인이 다르면 남긴다(전에는 쏘카·Spotify·쿠팡이츠가 빠지면서 모빌리티·음악·음식 도메인이 통째로 사라졌다)
            dup = next((k for k in keep if de(hex2rgb(k["hex"]), rgb) < 8 and set(k.get("domains") or []) & set(x.get("domains") or [])), None)
            if dup: why = f"{dup['name']}와 비슷함"
        if why: log.append((x["name"], x["hex"], why)); continue
        x["tone"] = TONE(hue(rgb)); keep.append(x)
    return keep, log

CELL = """<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="tokens.css"><link rel="stylesheet" href="{comp}">
<style>body{{margin:0;background:var(--c-bg);width:360px}} .w{{padding:12px;display:flex;flex-direction:column;gap:10px}}</style></head><body><div class="w">
<button class="btn primary full">예약하기</button>
<div class="chips" style="padding:0"><button class="chip is-selected">전체</button><button class="chip">오늘</button><button class="chip">이번 주</button></div>
<div style="display:flex;gap:6px;flex-wrap:wrap"><span class="badge is-brand">확정</span><span class="badge is-warning">마감 임박</span><span class="badge is-info">요청</span><span class="badge is-success">완료</span><span class="badge is-danger">실패</span><span class="badge">후보</span></div>
<section class="block" style="margin:0"><div class="row"><div class="row-main"><p class="row-title">10월 12일 저녁 7시</p><p class="row-sub">남은 자리 3</p></div><span class="badge is-brand">확정</span></div>
<p class="info"><span>브랜드 틴트 위 글자</span></p></section></div></body></html>"""

def sheet(keep, outpng):
    from playwright.sync_api import sync_playwright
    from PIL import Image, ImageDraw, ImageFont
    tmp = pathlib.Path("/tmp/hd/seedsheet"); tmp.mkdir(parents=True, exist_ok=True)
    shots = []
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome"); pg = b.new_page(viewport={"width": 360, "height": 330}, device_scale_factor=1)
        for i, x in enumerate(keep):
            d = tmp / f"{i}"; d.mkdir(exist_ok=True)
            subprocess.run([sys.executable, str(HERE / "derive.py"), "--brand", x["hex"], "--tone", "brand", "-o", str(d / "tokens.css")], check=True, capture_output=True)
            (d / "c.html").write_text(CELL.format(comp=str(HERE / "components.css")), encoding="utf-8")
            pg.goto((d / "c.html").as_uri()); pg.wait_for_timeout(150); pg.screenshot(path=str(d / "s.png")); shots.append(d / "s.png")
        b.close()
    cols = 6; W, Hc, lab = 360, 330, 46
    rows = (len(shots) + cols - 1) // cols
    S = Image.new("RGB", (cols * (W + 16) + 16, rows * (Hc + lab + 16) + 16), "#E9ECEF"); dr = ImageDraw.Draw(S)
    font = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", 20)
    for i, (x, sp) in enumerate(zip(keep, shots)):
        cx, cy = 16 + (i % cols) * (W + 16), 16 + (i // cols) * (Hc + lab + 16)
        dr.text((cx, cy), f"{i+1}. {x['name']} {x['hex']}", fill="#222", font=font)
        dr.text((cx, cy + 22), f"{x['tone']} · {'·'.join(x.get('domains') or [])[:20]} · {x.get('source','')[:28]}", fill="#666", font=ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", 14))
        S.paste(Image.open(sp), (cx, cy + lab))
    S.save(outpng)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--approve"); a = ap.parse_args()
    if a.approve is not None:
        keep = json.loads((P / "seed_filtered.json").read_text(encoding="utf-8"))
        drop = {int(x) for x in a.approve.replace(" ", "").split(",") if x}
        seeds = [{k: v for k, v in x.items() if k in ("slug", "name", "hex", "tone", "tags", "domains", "source", "shape", "bright", "mono", "gender", "gender_source")} for i, x in enumerate(keep, 1) if i not in drop]
        (P / "seeds.json").write_text(json.dumps(seeds, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"seeds.json {len(seeds)}개 (뺀 번호 {sorted(drop)})"); return
    keep, log = filt(collect())
    (P / "seed_filtered.json").write_text(json.dumps(keep, ensure_ascii=False, indent=1), encoding="utf-8")
    sheet(keep, P / "seed-sheet.png")
    print(f"통과 {len(keep)} · 탈락 {len(log)}")
    for n, h, w in log: print(f"  - {n} {h}: {w}")

if __name__ == "__main__":
    main()
