"""이미지 검색 — 빙 이미지(키 없음) → 위키미디어 커먼즈 → Openverse. 내부 검토용(저작권 사진 허용, 출처는 기록).

python3 imgsearch.py placeholders out                       # image_slots.json 의 photo 자리마다 회색 자리표시
python3 imgsearch.py search out <slot> "<검색어>" ["<검색어2>" …] [--ratio 3:4] [--keep 12]
    → 여러 검색어 × 여러 소스 후보를 모아 out/.cands/<slot>/sheet-<n>.jpg(번호 시트) + cands.json 에 누적
python3 imgsearch.py shortlist out <slot> 3 7 12 15         # 탐색 에이전트가 남긴 후보 번호 → shortlist.jpg(선택 에이전트가 볼 한 장)
python3 imgsearch.py pick out <slot> <번호> [--ratio 3:4] [--blur-face] [--half left|right|top|bottom]
    → out/assets/photos/<slot>.jpg(비율대로 자름, 긴 변 1200) + out/credits.json
워터마크 스톡 사이트(셔터스톡·아이스톡·게티 등)는 뺀다. 검색 결과는 ~/.cache/hd-img/ 에 캐시.
"""
import sys, json, re, html, hashlib, pathlib, urllib.request, urllib.parse, io, argparse, time
from PIL import Image, ImageDraw, ImageFont, ImageFilter
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"}
CACHE = pathlib.Path.home() / ".cache/hd-img"; CACHE.mkdir(parents=True, exist_ok=True)
RAT = {"3:4": (3, 4), "1:1": (1, 1), "4:3": (4, 3), "16:9": (16, 9), "9:16": (9, 16), "4:5": (4, 5)}
BAN = re.compile(r"shutterstock|istockphoto|gettyimages|depositphotos|123rf|dreamstime|alamy|pngtree|vecteezy|freepik|adobe\.com|stock\.adobe|canstockphoto|bigstock|pond5|lovepik|pikbest|ytimg|pinimg\.com/.*/236x", re.I)

def get(url, timeout=15):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read()

def cached(key, fn):
    f = CACHE / (hashlib.md5(key.encode()).hexdigest() + ".json")
    if f.exists(): return json.loads(f.read_text())
    try: v = fn()
    except Exception as e: print(f"  ! {key[:60]}: {e}", file=sys.stderr); return []
    f.write_text(json.dumps(v)); return v

def bing(q):
    def f():
        s = get("https://www.bing.com/images/search?" + urllib.parse.urlencode({"q": q, "form": "HDRSC2", "first": 1, "qft": "+filterui:imagesize-large"})).decode("utf-8", "ignore")
        out = []
        for m in re.findall(r'class="iusc"[^>]*?m="([^"]+)"', s):
            try: d = json.loads(html.unescape(m))
            except Exception: continue
            if d.get("murl") and not BAN.search(d["murl"] + d.get("purl", "")):
                out.append({"src": "bing", "url": d["murl"], "thumb": d.get("turl") or d["murl"], "title": d.get("t", ""), "page": d.get("purl", "")})
        return out
    return cached("bing:" + q, f)

def commons(q):
    def f():
        d = json.loads(get("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({"action": "query", "generator": "search", "gsrsearch": "filetype:bitmap " + q, "gsrnamespace": 6, "gsrlimit": 12, "prop": "imageinfo", "iiprop": "url|size|extmetadata", "iiurlwidth": 400, "format": "json"})))
        out = []
        for p in d.get("query", {}).get("pages", {}).values():
            ii = p["imageinfo"][0]
            if min(ii.get("width", 0), ii.get("height", 0)) < 600: continue
            out.append({"src": "commons", "url": ii["url"], "thumb": ii.get("thumburl") or ii["url"], "title": p["title"].replace("File:", ""), "page": ii.get("descriptionurl", ""),
                        "license": ii.get("extmetadata", {}).get("LicenseShortName", {}).get("value", ""), "author": re.sub("<[^>]+>", "", ii.get("extmetadata", {}).get("Artist", {}).get("value", ""))[:60]})
        return out
    return cached("commons:" + q, f)

def openverse(q):
    def f():
        d = json.loads(get("https://api.openverse.org/v1/images/?" + urllib.parse.urlencode({"q": q, "license": "cc0,pdm,by", "page_size": 20, "mature": "false"})))
        return [{"src": "openverse", "url": r["url"], "thumb": r.get("thumbnail") or r["url"], "title": r.get("title", ""), "page": r.get("foreign_landing_url", ""), "license": r.get("license"), "author": r.get("creator")}
                for r in d.get("results", []) if min(r.get("width") or 0, r.get("height") or 0) >= 600]
    return cached("ov:" + q, f)

def crop(im, ratio, long_side=1200):
    w, h = im.size; rw, rh = RAT.get(ratio, (3, 4))
    if w / h > rw / rh: nw = int(h * rw / rh); im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    else: nh = int(w * rh / rw); top = max(0, int((h - nh) * 0.3)); im = im.crop((0, top, w, top + nh))
    s = long_side / max(im.size); return im.resize((round(im.width * s), round(im.height * s))) if s < 1 else im

def blur_face(im):   # 위 가운데 타원만 부드럽게 — 띠처럼 보이지 않게
    w, h = im.size; mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).ellipse((int(w * .28), int(h * .04), int(w * .72), int(h * .42)), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(w * .04))
    return Image.composite(im.filter(ImageFilter.GaussianBlur(w * .035)), im, mask)

def sheet(items, path, label=lambda i, c: str(i)):
    tiles = []
    for i, c in items:
        try: im = Image.open(io.BytesIO(get(c["thumb"], 10))).convert("RGB"); im.thumbnail((300, 300)); tiles.append((i, c, im))
        except Exception: continue
    if not tiles: return 0
    cols = 4; W, H = 310, 340
    S = Image.new("RGB", (cols * W, ((len(tiles) + cols - 1) // cols) * H), "white"); d = ImageDraw.Draw(S)
    try: font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 28)
    except Exception: font = ImageFont.load_default()
    for k, (i, c, im) in enumerate(tiles):
        x, y = (k % cols) * W + 5, (k // cols) * H + 5; S.paste(im, (x, y + 34)); d.text((x, y), label(i, c), fill="black", font=font)
    S.save(path, quality=80); return len(tiles)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("cmd"); ap.add_argument("out"); ap.add_argument("rest", nargs="*")
    ap.add_argument("--ratio", default="3:4"); ap.add_argument("--keep", type=int, default=12); ap.add_argument("--blur-face", action="store_true"); ap.add_argument("--half", choices=["left", "right", "top", "bottom"])
    a = ap.parse_args(); out = pathlib.Path(a.out); photos = out / "assets/photos"; photos.mkdir(parents=True, exist_ok=True)
    if a.cmd == "placeholders":
        for s in json.loads((out / "image_slots.json").read_text(encoding="utf-8")):
            if s.get("kind") != "photo": continue
            rw, rh = RAT.get(s.get("ratio", "3:4"), (3, 4)); p = photos / f"{s['slot']}.jpg"
            if not p.exists(): Image.new("RGB", (rw * 200, rh * 200), (226, 226, 222)).save(p, quality=70)
        print("placeholders ok"); return
    if a.cmd == "search":
        slot, qs = a.rest[0], a.rest[1:]
        d = out / ".cands" / slot; d.mkdir(parents=True, exist_ok=True)
        cf = d / "cands.json"; cands = json.loads(cf.read_text()) if cf.exists() else []
        seen = {c["url"] for c in cands}; new = []
        for q in qs:
            for c in (bing(q)[: a.keep] + commons(q)[:4] + (openverse(q)[:3] if not re.search("[가-힣]", q) else [])):
                if c["url"] not in seen: seen.add(c["url"]); c["query"] = q; new.append(c)
        start = len(cands); cands += new; cf.write_text(json.dumps(cands, ensure_ascii=False))
        n = len(list(d.glob("sheet-*.jpg")))
        got = sheet(list(enumerate(cands))[start:], d / f"sheet-{n}.jpg")
        print(json.dumps({"slot": slot, "sheet": str(d / f"sheet-{n}.jpg"), "new": got, "numbers": f"{start}~{len(cands)-1}"}, ensure_ascii=False)); return
    if a.cmd == "shortlist":
        slot, nums = a.rest[0], [int(x) for x in a.rest[1:]]
        d = out / ".cands" / slot; cands = json.loads((d / "cands.json").read_text())
        got = sheet([(i, cands[i]) for i in nums if i < len(cands)], d / "shortlist.jpg")
        (d / "shortlist.json").write_text(json.dumps(nums)); print(json.dumps({"slot": slot, "shortlist": str(d / "shortlist.jpg"), "n": got})); return
    if a.cmd == "pick":
        slot, i = a.rest[0], int(a.rest[1])
        c = json.loads((out / ".cands" / slot / "cands.json").read_text())[i]
        try: im = Image.open(io.BytesIO(get(c["url"], 25))).convert("RGB")
        except Exception: im = Image.open(io.BytesIO(get(c["thumb"]))).convert("RGB")
        if a.half:   # 전·후 콜라주에서 한쪽만(같은 사람의 전·후를 맞출 때)
            w, h = im.size
            im = im.crop({"left": (0, 0, w // 2, h), "right": (w // 2, 0, w, h), "top": (0, 0, w, h // 2), "bottom": (0, h // 2, w, h)}[a.half])
        im = crop(im, a.ratio)
        if a.blur_face: im = blur_face(im)
        im.save(photos / f"{slot}.jpg", quality=82)
        f = out / "credits.json"; cr = json.loads(f.read_text(encoding="utf-8")) if f.exists() else []
        cr = [x for x in cr if x.get("slot") != slot]
        cr.append({"slot": slot, "file": f"assets/photos/{slot}.jpg", "title": c.get("title"), "author": c.get("author", ""), "license": c.get("license") or "unknown(내부 검토용)", "source": c["src"], "url": c.get("page") or c["url"]})
        f.write_text(json.dumps(cr, ensure_ascii=False, indent=1), encoding="utf-8"); print("picked", photos / f"{slot}.jpg"); return
    print(__doc__)

if __name__ == "__main__":
    main()
