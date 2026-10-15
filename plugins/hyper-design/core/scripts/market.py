"""시장 리서치 재료 모으기 — 이 PRD와 같은 문제를 푸는 앱들 중 잘 되는 것(평점 수 상위)의 스토어 화면·설명·리뷰.

python3 market.py out "<키워드1>" "<키워드2>" … [--country kr] [--n 5] [--min-ratings 300]
- 키워드는 도메인 이름이 아니라 PRD의 핵심 기능·갈등에서 뽑는다(예: "AI 사주 상담", "궁합", "만세력")
- App Store 검색 API·리뷰 RSS(키 없음)만 쓴다 — 전부 병렬, 보통 10~20초
- 저장 위치(매번 새로, 캐시하지 않는다):
    out/market/apps.json           앱별 이름·평점 수·평점·장르·설명 앞부분·시트 경로·리뷰 수
    out/market/<n>-<앱>.jpg        스토어 스크린샷 한 장 시트(번호 붙임)
    out/market/reviews.md          앱별 낮은 별점(1~3) / 높은 별점(4~5) 리뷰 — 해석 에이전트가 읽는다
- 해석은 하지 않는다 — references/market.md의 해석 에이전트가 conventions.json을 쓴다
"""
import sys, json, re, io, pathlib, argparse, urllib.request, urllib.parse, time
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFont

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"}
POOL = ThreadPoolExecutor(24)
GENERIC = {"ai", "앱", "app", "어플", "추천", "무료", "서비스", "기록", "관리"}

def get(url, timeout=12):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read()

def search(term, country, limit=15):
    try:
        d = json.loads(get("https://itunes.apple.com/search?" + urllib.parse.urlencode(
            {"term": term, "country": country, "entity": "software", "limit": limit})))
        return d.get("results", [])
    except Exception as e:
        print(f"  ! 검색 실패 {term}: {e}", file=sys.stderr); return []

def reviews(app_id, country, pages=(1, 2, 3)):
    out = []
    def page(p):
        try:
            d = json.loads(get(f"https://itunes.apple.com/{country}/rss/customerreviews/page={p}/id={app_id}/sortBy=mostRecent/json"))
            return d.get("feed", {}).get("entry", []) or []
        except Exception: return []
    for ents in POOL.map(page, pages):
        for e in ents if isinstance(ents, list) else [ents]:
            if "im:rating" not in e: continue        # 첫 항목이 앱 정보인 경우
            out.append({"rating": int(e["im:rating"]["label"]), "title": e.get("title", {}).get("label", ""),
                        "text": re.sub(r"\s+", " ", e.get("content", {}).get("label", "")).strip()})
    return out

def font(size):
    for f in ("/System/Library/Fonts/AppleSDGothicNeo.ttc", "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"):
        try: return ImageFont.truetype(f, size)
        except Exception: pass
    return ImageFont.load_default()

def sheet(urls, title, path, h=520):
    def fetch(u):
        try: return Image.open(io.BytesIO(get(u))).convert("RGB")
        except Exception: return None
    ims = [im for im in POOL.map(fetch, urls[:8]) if im]
    if not ims: return False
    ims = [im.resize((max(1, int(im.width * h / im.height)), h)) for im in ims]
    pad, top = 12, 44
    W = pad + sum(im.width + pad for im in ims)
    S = Image.new("RGB", (W, h + top + pad), "white"); d = ImageDraw.Draw(S)
    d.text((pad, 10), title, fill="#111", font=font(24))
    x = pad
    for i, im in enumerate(ims, 1):
        S.paste(im, (x, top)); d.rectangle((x, top, x + 30, top + 26), fill="#111"); d.text((x + 8, top + 2), str(i), fill="white", font=font(20))
        x += im.width + pad
    S.save(path, quality=82); return True

def slug(s): return re.sub(r"[^0-9A-Za-z가-힣]+", "", s)[:12] or "app"

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("keywords", nargs="+")
    ap.add_argument("--country", default="kr"); ap.add_argument("--n", type=int, default=5); ap.add_argument("--min-ratings", type=int, default=300)
    a = ap.parse_args(); t0 = time.time()
    M = pathlib.Path(a.out) / "market"; M.mkdir(parents=True, exist_ok=True)
    for f in M.glob("*"): f.unlink()
    found = {}
    for res in POOL.map(lambda k: search(k, a.country), a.keywords):
        for r in res:
            r.setdefault("_hits", 0)
            found.setdefault(r["trackId"], r)["_hits"] += 1
    # 관련성: 키워드의 낱말(2자 이상, 'AI'·'앱' 같은 범용어 제외)이 이름·설명에 하나라도 나와야 한다 — "AI 사주"로 ChatGPT가 잡히는 것 방지
    toks = {t for k in a.keywords for t in re.split(r"\s+", k) if len(t) >= 2 and t.lower() not in GENERIC}
    def rel(r):
        txt = (r.get("trackName", "") + " " + r.get("description", "")).lower()
        return sum(1 for t in toks if t.lower() in txt)
    dropped = [r["trackName"] for r in found.values() if toks and rel(r) == 0 and r.get("userRatingCount", 0) >= a.min_ratings]
    apps = sorted((r for r in found.values() if not toks or rel(r) > 0), key=lambda r: r.get("userRatingCount", 0), reverse=True)
    top = [r for r in apps if r.get("userRatingCount", 0) >= a.min_ratings][:a.n] or apps[:a.n]
    def one(ir):
        i, r = ir
        name = r["trackName"]; p = M / f"{i}-{slug(name)}.jpg"
        ok = sheet(r.get("screenshotUrls") or [], f"{i}. {name} · 평점 {r.get('averageUserRating', 0):.1f} ({r.get('userRatingCount', 0):,}명)", p)
        rv = reviews(r["trackId"], a.country)
        return {"no": i, "name": name, "id": r["trackId"], "seller": r.get("sellerName"), "ratings": r.get("userRatingCount", 0),
                "rating": round(r.get("averageUserRating", 0), 2), "genre": r.get("primaryGenreName"), "price": r.get("formattedPrice"),
                "url": r.get("trackViewUrl"), "keywords_hit": r["_hits"], "sheet": str(p) if ok else None,
                "description": re.sub(r"\s+", " ", r.get("description", ""))[:900], "_reviews": rv}
    rows = list(POOL.map(one, enumerate(top, 1)))
    lines = ["# 리뷰 — 낮은 별점(1~3)은 불만, 높은 별점(4~5)은 계속 쓰는 이유\n"]
    for x in rows:
        rv = x.pop("_reviews"); x["reviews"] = len(rv)
        low = [r for r in rv if r["rating"] <= 3][:25]; high = [r for r in rv if r["rating"] >= 4][:15]
        lines.append(f"\n## {x['no']}. {x['name']} (리뷰 {len(rv)}개 중 낮은 별점 {sum(r['rating'] <= 3 for r in rv)}개)\n")
        lines.append("### 낮은 별점\n" + ("\n".join(f"- ({r['rating']}) {r['title']} — {r['text'][:220]}" for r in low) or "- 없음"))
        lines.append("\n### 높은 별점\n" + ("\n".join(f"- ({r['rating']}) {r['title']} — {r['text'][:160]}" for r in high) or "- 없음"))
    (M / "reviews.md").write_text("\n".join(lines), encoding="utf-8")
    (M / "apps.json").write_text(json.dumps({"keywords": a.keywords, "country": a.country, "apps": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"market: 앱 {len(rows)}개 · 시트 {sum(1 for x in rows if x['sheet'])}장 · 리뷰 {sum(x['reviews'] for x in rows)}개 · {time.time() - t0:.1f}초")
    for x in rows: print(f"  {x['no']}. {x['name']} — {x['ratings']:,}명 {x['rating']}")
    if dropped: print("  (관련 낱말 없어 뺌: " + ", ".join(d[:20] for d in dropped[:5]) + ")")
    POOL.shutdown(wait=False)

if __name__ == "__main__":
    main()
