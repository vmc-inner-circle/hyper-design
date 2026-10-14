"""실제 앱 화면 레퍼런스 받기 — Apple 공식 iTunes Search API (2026-09-23).

    python scripts/ref_fetch.py <검색어> [<검색어> ...] [--per 3] [--limit 8]

앱스토어 공개 스크린샷(앱 화면)을 작게 받아 reflib/appstore/ 에 쌓고 index.json 에 출처를 남긴다.
로그인·스크래핑 없음(공식 검색 API, 응답 1초 안팎). 내부 참고용 — 화면마다 앱 이름·개발사·스토어 링크를 붙여 보여준다.
받은 파일은 다시 받지 않는다(캐시). contact sheet(한 장에 모아 보기)도 만든다: reflib/appstore/sheet-<검색어>.png
"""
import json
import os
import pathlib
import sys
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

LIB = pathlib.Path(os.environ.get("HD_REFLIB") or pathlib.Path(__file__).resolve().parents[1] / "design/reflib/appstore")
IDX = LIB / "index.json"


def get(url):
    with urllib.request.urlopen(url, timeout=15) as r:
        return r.read()


def small(url, w=300):
    # .../392x696bb.jpg → .../300x0w.jpg (앱스토어 이미지 서버의 크기 지정)
    head, _, _ = url.rpartition("/")
    return f"{head}/{w}x0w.jpg"


def main():
    args = sys.argv[1:]
    per = int(args[args.index("--per") + 1]) if "--per" in args else 3
    limit = int(args[args.index("--limit") + 1]) if "--limit" in args else 8
    terms = [a for i, a in enumerate(args) if not a.startswith("--") and (i == 0 or not args[i - 1].startswith("--"))]
    LIB.mkdir(parents=True, exist_ok=True)
    idx = json.loads(IDX.read_text(encoding="utf-8")) if IDX.exists() else {}
    jobs = []
    for term in terms:
        q = urllib.parse.urlencode({"term": term, "country": "kr", "entity": "software", "limit": limit})
        res = json.loads(get(f"https://itunes.apple.com/search?{q}"))["results"]
        for app in res:
            for n, u in enumerate(app.get("screenshotUrls", [])[:per]):
                key = f"{app['trackId']}-{n}"
                idx.setdefault(key, {
                    "file": f"{key}.jpg", "app": app["trackName"], "seller": app.get("sellerName", ""),
                    "genre": app.get("primaryGenreName", ""), "store": app["trackViewUrl"].split("?")[0],
                    "terms": [], "tags": {},
                })
                if term not in idx[key]["terms"]:
                    idx[key]["terms"].append(term)
                if not (LIB / f"{key}.jpg").exists():
                    jobs.append((small(u), LIB / f"{key}.jpg"))
    with ThreadPoolExecutor(12) as ex:
        list(ex.map(lambda j: j[1].write_bytes(get(j[0])), jobs))
    IDX.write_text(json.dumps(idx, ensure_ascii=False, indent=1), encoding="utf-8")
    for term in terms:
        sheet(term, [k for k, v in idx.items() if term in v["terms"]], idx)
    print(f"새로 받음 {len(jobs)} · 전체 {len(idx)} → {LIB}")


def sheet(term, keys, idx):
    from PIL import Image, ImageDraw
    cols, w, h = 8, 150, 300
    rows = (len(keys) + cols - 1) // cols
    im = Image.new("RGB", (cols * w, rows * (h + 16)), "white")
    d = ImageDraw.Draw(im)
    for i, k in enumerate(keys):
        try:
            t = Image.open(LIB / idx[k]["file"]).convert("RGB")
        except Exception:
            continue
        t.thumbnail((w - 4, h))
        x, y = (i % cols) * w, (i // cols) * (h + 16)
        im.paste(t, (x + 2, y + 14))
        d.text((x + 2, y), k, fill="black")
    im.save(LIB / f"sheet-{term}.png")


if __name__ == "__main__":
    main()
