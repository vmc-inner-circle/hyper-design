"""팔레트 라이브러리에서 기본값 1 + 대안 2를 고르고 토큰 파일을 만든다 — 사용자에게 묻지 않는다.

python3 palette_pick.py <out_dir> --domain 여행 --tags "따뜻함,편안함,신뢰" --temp warm
→ out_dir/tokens.css(기본값) + tokens-<slug>.css ×3 + palettes.json(선택 이유)

점수: 도메인 일치 3 · 성격 태그 겹침 1씩 · 감정 온도(--temp warm|cool) 일치 +1.5 / 반대 -1.5 · 흰 글자 버튼이 성립(대비 3 이상)하지 않으면 -2 · 합성 팔레트 -0.5 · 브랜드가 오류 빨강과 겹치면 -1.5(확정과 주의가 같은 붉은색이 된다)
대안: 기본값과 브랜드 색상각이 40° 이상 다른 것(모노 1개까지) — 원클릭 교체 때 확실히 달라 보이게
"""
import argparse, json, pathlib, subprocess, sys, colorsys
HERE = pathlib.Path(__file__).resolve().parent.parent / "foundation"
sys.path.insert(0, str(HERE)); from derive import hex2rgb, contrast   # noqa: E402

def brand_of(P): return hex2rgb(P["scales"][P["brand"]][P["brand_step"]])
def hue(c): return colorsys.rgb_to_hls(*c)[0] * 360
def gap(a, b): d = abs(hue(a) - hue(b)) % 360; return min(d, 360 - d)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("--domain", default=""); ap.add_argument("--tags", default=""); ap.add_argument("--temp", default="", choices=["", "warm", "cool"])
    a = ap.parse_args(); out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    tags = {t.strip() for t in a.tags.split(",") if t.strip()}
    pals = {f.stem: json.loads(f.read_text(encoding="utf-8")) for f in sorted((HERE / "palettes").glob("*.json"))}
    pals = {k: v for k, v in pals.items() if isinstance(v, dict) and isinstance(v.get("scales"), dict)}   # seeds.json·seed_candidates.json 제외
    scored = []
    for slug, P in pals.items():
        b = brand_of(P); why = []
        s = 0
        if a.domain and any(d in P.get("domain", "") for d in a.domain.split(",")): s += 3; why.append(f"도메인({P['domain']})")
        hit = tags & set(P.get("tags", []))
        if hit: s += len(hit); why.append("성격(" + ",".join(sorted(hit)) + ")")
        if a.temp and not P.get("mono"):
            h = hue(b); warm = h < 60 or h >= 300; cool = 160 <= h < 260
            if (a.temp == "warm" and warm) or (a.temp == "cool" and cool): s += 1.5; why.append("감정 온도(" + ("따뜻한" if warm else "차가운") + " 색)")
            elif (a.temp == "warm" and cool) or (a.temp == "cool" and warm): s -= 1.5; why.append("감정 온도와 반대")
        if not P.get("mono") and not any(contrast((1, 1, 1), hex2rgb(v)) >= 3 and gap(hex2rgb(v), b) < 12 for v in P["scales"][P["brand"]].values()): s -= 2; why.append("흰 글자 버튼 불가")
        if P.get("synthesized"): s -= .5; why.append("측정 합성")
        if not P.get("mono") and gap(b, (0.9, 0.28, 0.3)) < 25: s -= 1.5; why.append("브랜드가 오류 빨강과 겹침")
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
    # custom 모드(v13): 라이브러리 1위가 도메인 불일치 + 성격 겹침 ≤1 → 승인된 브랜드 시드에서 기본값을 만든다
    best = pals[default]; best_hit = len(tags & set(best.get("tags", [])))
    dom_hit = a.domain and any(d in best.get("domain", "") for d in a.domain.split(","))
    seeds_f = HERE / "palettes" / "seeds.json"
    seed = None
    if not dom_hit and best_hit <= 1 and seeds_f.exists():
        sc = []
        for sd in json.loads(seeds_f.read_text(encoding="utf-8")):
            v, why = 0, []
            if a.domain and any(d in x for d in a.domain.split(",") for x in sd.get("domains", [])): v += 3; why.append("도메인(" + "·".join(sd["domains"]) + ")")
            hit = tags & set(sd.get("tags", []))
            if hit: v += len(hit); why.append("성격(" + ",".join(sorted(hit)) + ")")
            if a.temp and sd.get("tone") in ("warm", "cool"):
                if sd["tone"] == a.temp: v += 1.5; why.append("감정 온도")
                else: v -= 1.5
            sc.append((v, sd, why))
        sc.sort(key=lambda x: -x[0])
        if sc and sc[0][0] > 0:
            v, sd, why = sc[0]; seed = sd
            slug = "seed-" + sd["slug"]
            subprocess.run([sys.executable, str(HERE / "derive.py"), "--brand", sd["hex"], "--tone", "brand", "-o", str(out / f"tokens-{slug}.css")], check=True, capture_output=True)
            pals[slug] = {"name": sd["name"], "scales": {"b": {"s": sd["hex"]}}, "brand": "b", "brand_step": "s", "source": "브랜드 시드(" + sd.get("source", "") + ")"}
            scored.insert(0, (v, slug, ["라이브러리에 맞는 도메인이 없어 시드로 만듦"] + why))
            alts = [p for p in picks if p != default][:1] + [default]
            picks = [slug] + [p for p in alts if gap(brand_of(pals[p]), hex2rgb(sd["hex"])) >= 40 or pals[p].get("mono")][:2]
            if len(picks) < 3:
                picks += [x for _, x, _ in scored if x not in picks and not x.startswith("seed-")][: 3 - len(picks)]
            default = slug
    for slug in picks:
        if slug.startswith("seed-"): continue
        subprocess.run([sys.executable, str(HERE / "derive.py"), "--palette", str(HERE / "palettes" / f"{slug}.json"), "-o", str(out / f"tokens-{slug}.css")], check=True, capture_output=True)
    (out / "tokens.css").write_text((out / f"tokens-{default}.css").read_text(encoding="utf-8"), encoding="utf-8")
    info = {"default": default, "options": [{"slug": s, "name": pals[s]["name"], "brand": pals[s]["scales"][pals[s]["brand"]][pals[s]["brand_step"]],
            "source": pals[s]["source"], "why": next(w for _, x, w in scored if x == s),
            **({"accent": pals[s]["scales"][pals[s]["accent"]["scale"]][pals[s]["accent"]["step"]], "accent_seen": pals[s]["accent"].get("seen", "")} if pals[s].get("accent") else {})} for s in picks]}
    (out / "palettes.json").write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(info, ensure_ascii=False))

if __name__ == "__main__":
    main()
