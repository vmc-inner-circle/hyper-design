"""스톡 사진 — Openverse(키 없음, CC0·PDM·CC BY만) 검색·후보 시트·선택·자르기·출처 기록.

python3 openverse.py placeholders out           # out/image_slots.json 의 photo 자리마다 회색 자리표시 jpg를 먼저 만든다
python3 openverse.py search out <slot> "<검색어>" [--ratio 3:4] [--n 6]
    → out/.cands/<slot>/sheet.jpg(번호 붙은 후보 시트 — 이 한 장을 보고 고른다) + 후보 JSON 출력
python3 openverse.py pick out <slot> <번호> [--ratio 3:4] [--blur-faces]
    → out/assets/photos/<slot>.jpg(비율대로 자름, 긴 변 1200) + out/credits.json 갱신
검색 결과는 ~/.cache/hd-openverse/ 에 캐시.
"""
import sys, json, hashlib, pathlib, urllib.request, urllib.parse, io, argparse
from PIL import Image, ImageDraw, ImageFont, ImageFilter
API = "https://api.openverse.org/v1/images/"
UA = {"User-Agent": "Mozilla/5.0 (hyper-design harness)"}
CACHE = pathlib.Path.home() / ".cache/hd-openverse"; CACHE.mkdir(parents=True, exist_ok=True)
RAT = {"3:4": (3, 4), "1:1": (1, 1), "4:3": (4, 3), "16:9": (16, 9), "9:16": (9, 16), "4:5": (4, 5)}

def get(url, timeout=20):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read()

def search(q, ratio, n):
    ar = {"3:4": "tall", "9:16": "tall", "4:5": "tall", "1:1": "square", "4:3": "wide", "16:9": "wide"}.get(ratio, "")
    params = {"q": q, "license": "cc0,pdm,by", "page_size": 20, "mature": "false"}
    if ar: params["aspect_ratio"] = ar
    key = CACHE / (hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest() + ".json")
    if key.exists(): data = json.loads(key.read_text())
    else:
        data = json.loads(get(API + "?" + urllib.parse.urlencode(params)))
        key.write_text(json.dumps(data))
    res = [r for r in data.get("results", []) if min(r.get("width") or 0, r.get("height") or 0) >= 600]
    return res[:n]

def crop(im, ratio, long_side=1200):
    w, h = im.size; rw, rh = RAT.get(ratio, (3, 4))
    if w / h > rw / rh: nw = int(h * rw / rh); im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    else: nh = int(w * rh / rw); top = max(0, int((h - nh) * 0.35)); im = im.crop((0, top, w, top + nh))
    s = long_side / max(im.size); return im.resize((round(im.width * s), round(im.height * s))) if s < 1 else im

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("cmd"); ap.add_argument("out"); ap.add_argument("rest", nargs="*")
    ap.add_argument("--ratio", default="3:4"); ap.add_argument("--n", type=int, default=9); ap.add_argument("--blur-faces", action="store_true")
    a = ap.parse_args(); out = pathlib.Path(a.out)
    photos = out / "assets/photos"; photos.mkdir(parents=True, exist_ok=True)
    if a.cmd == "placeholders":
        slots = json.loads((out / "image_slots.json").read_text(encoding="utf-8"))
        for s in slots:
            if s.get("kind") != "photo": continue
            rw, rh = RAT.get(s.get("ratio", "3:4"), (3, 4))
            p = photos / f"{s['slot']}.jpg"
            if not p.exists(): Image.new("RGB", (rw * 200, rh * 200), (226, 226, 222)).save(p, quality=70)
        print("placeholders ok"); return
    if a.cmd == "search":
        slot, q = a.rest[0], a.rest[1]
        res = search(q, a.ratio, a.n)
        d = out / ".cands" / slot; d.mkdir(parents=True, exist_ok=True)
        tiles = []
        for i, r in enumerate(res):
            try: im = Image.open(io.BytesIO(get(r.get("thumbnail") or r["url"]))).convert("RGB")
            except Exception: continue
            im.thumbnail((360, 360)); tiles.append((i, im))
        (d / "results.json").write_text(json.dumps(res, ensure_ascii=False))
        if not tiles: print(json.dumps({"slot": slot, "found": 0})); return
        cols = 3; W = 380; Hh = 400; sheet = Image.new("RGB", (cols * W, ((len(tiles) + cols - 1) // cols) * Hh), "white")
        dr = ImageDraw.Draw(sheet)
        try: font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 32)
        except Exception: font = ImageFont.load_default()
        for k, (i, im) in enumerate(tiles):
            x, y = (k % cols) * W + 10, (k // cols) * Hh + 10; sheet.paste(im, (x, y + 30)); dr.text((x, y), str(i), fill="black", font=font)
        sheet.save(d / "sheet.jpg", quality=80)
        print(json.dumps({"slot": slot, "sheet": str(d / "sheet.jpg"), "cands": [{"i": i, "title": r.get("title", "")[:60], "license": r.get("license"), "w": r.get("width"), "h": r.get("height")} for i, r in enumerate(res)]}, ensure_ascii=False)); return
    if a.cmd == "pick":
        slot, i = a.rest[0], int(a.rest[1])
        r = json.loads((out / ".cands" / slot / "results.json").read_text())[i]
        try: im = Image.open(io.BytesIO(get(r["url"], 30))).convert("RGB")
        except Exception: im = Image.open(io.BytesIO(get(r["thumbnail"]))).convert("RGB")
        im = crop(im, a.ratio)
        if a.blur_faces:   # 위쪽 1/3(얼굴이 있을 법한 곳)만 흐림 — 얼굴 가림 기능을 보여 줄 때
            top = im.crop((0, 0, im.width, im.height // 3)).filter(ImageFilter.GaussianBlur(18)); im.paste(top, (0, 0))
        im.save(photos / f"{slot}.jpg", quality=82)
        cf = out / "credits.json"; cr = json.loads(cf.read_text(encoding="utf-8")) if cf.exists() else []
        cr = [c for c in cr if c.get("slot") != slot]
        cr.append({"slot": slot, "file": f"assets/photos/{slot}.jpg", "title": r.get("title"), "author": r.get("creator"),
                   "license": r.get("license"), "license_version": r.get("license_version"), "url": r.get("foreign_landing_url") or r.get("url")})
        cf.write_text(json.dumps(cr, ensure_ascii=False, indent=1), encoding="utf-8")
        print("picked", photos / f"{slot}.jpg"); return
    print(__doc__)

if __name__ == "__main__":
    main()
