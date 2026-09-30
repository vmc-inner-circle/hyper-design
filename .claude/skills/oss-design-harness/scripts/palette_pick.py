"""팔레트 라이브러리에서 기본값 1 + 대안 2를 고르고 토큰 파일을 만든다 — 사용자에게 묻지 않는다.

python3 palette_pick.py <out_dir> --domain 여행 --tags "따뜻함,편안함,신뢰"
→ out_dir/tokens.css(기본값) + tokens-<slug>.css ×3 + palettes.json(선택 이유)

점수: 도메인 일치 3 · 성격 태그 겹침 1씩 · 흰 글자 버튼이 성립(대비 3 이상)하지 않으면 -2 · 합성 팔레트 -0.5
대안: 기본값과 브랜드 색상각이 40° 이상 다른 것(모노 1개까지) — 원클릭 교체 때 확실히 달라 보이게
"""
import argparse, json, pathlib, subprocess, sys, colorsys
HERE = pathlib.Path(__file__).resolve().parent.parent / "foundation"
sys.path.insert(0, str(HERE)); from derive import hex2rgb, contrast   # noqa: E402

def brand_of(P): return hex2rgb(P["scales"][P["brand"]][P["brand_step"]])
def hue(c): return colorsys.rgb_to_hls(*c)[0] * 360
def gap(a, b): d = abs(hue(a) - hue(b)) % 360; return min(d, 360 - d)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("--domain", default=""); ap.add_argument("--tags", default="")
    a = ap.parse_args(); out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    tags = {t.strip() for t in a.tags.split(",") if t.strip()}
    pals = {f.stem: json.loads(f.read_text(encoding="utf-8")) for f in sorted((HERE / "palettes").glob("*.json"))}
    scored = []
    for slug, P in pals.items():
        b = brand_of(P); why = []
        s = 0
        if a.domain and any(d in P.get("domain", "") for d in a.domain.split(",")): s += 3; why.append(f"도메인({P['domain']})")
        hit = tags & set(P.get("tags", []))
        if hit: s += len(hit); why.append("성격(" + ",".join(sorted(hit)) + ")")
        if not P.get("mono") and contrast((1, 1, 1), b) < 3: s -= 2; why.append("흰 글자 버튼 불가")
        if P.get("synthesized"): s -= .5; why.append("측정 합성")
        scored.append((s, slug, why))
    scored.sort(key=lambda x: -x[0])
    default = scored[0][1]; picks = [default]; mono_used = pals[default].get("mono", False)
    for s, slug, _ in scored[1:]:
        P = pals[slug]
        if P.get("mono"):
            if mono_used: continue
            picks.append(slug); mono_used = True
        elif all(pals[p].get("mono") or gap(brand_of(P), brand_of(pals[p])) >= 40 for p in picks):
            picks.append(slug)
        if len(picks) == 3: break
    for slug in picks:
        subprocess.run([sys.executable, str(HERE / "derive.py"), "--palette", str(HERE / "palettes" / f"{slug}.json"), "-o", str(out / f"tokens-{slug}.css")], check=True, capture_output=True)
    (out / "tokens.css").write_text((out / f"tokens-{default}.css").read_text(encoding="utf-8"), encoding="utf-8")
    info = {"default": default, "options": [{"slug": s, "name": pals[s]["name"], "brand": pals[s]["scales"][pals[s]["brand"]][pals[s]["brand_step"]],
            "source": pals[s]["source"], "why": next(w for _, x, w in scored if x == s)} for s in picks]}
    (out / "palettes.json").write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(info, ensure_ascii=False))

if __name__ == "__main__":
    main()
