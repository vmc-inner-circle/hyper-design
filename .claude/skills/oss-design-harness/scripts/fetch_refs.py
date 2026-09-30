"""uibowl.io 에서 한국 앱 실제 화면 스크린샷을 받아온다.
python3 fetch_refs.py <out_dir> 토스 카카오톡 당근 --n 4
"""
import sys, pathlib, urllib.parse, urllib.request, argparse
from playwright.sync_api import sync_playwright
ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("apps", nargs="+"); ap.add_argument("--n", type=int, default=4)
a = ap.parse_args(); out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome"); pg = b.new_page(viewport={"width": 1440, "height": 1600})
    for app in a.apps:
        try:
            pg.goto("https://uibowl.io/name/" + urllib.parse.quote(app), wait_until="networkidle", timeout=30000)
            pg.wait_for_timeout(1500)
            srcs = pg.eval_on_selector_all("img", "els=>els.filter(e=>e.naturalHeight>e.naturalWidth*1.5).map(e=>e.src)")
        except Exception as e:
            print(app, "실패", e); continue
        for i, src in enumerate(srcs[:a.n]):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(src).query).get("url", [src])[0]
            f = out / f"{app}-{i}.jpg"
            q = urllib.parse.quote(q, safe=":/")
            req = urllib.request.Request(q, headers={"User-Agent": "Mozilla/5.0"})
            f.write_bytes(urllib.request.urlopen(req, timeout=20).read())
            print("saved", f)
    b.close()
