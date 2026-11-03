"""uibowl.io 에서 한국 앱 실제 화면 스크린샷을 받아온다.
python3 fetch_refs.py <out_dir> 토스 카카오톡 당근 --n 4
"""
import pathlib, urllib.parse, argparse
from playwright.sync_api import sync_playwright
ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("apps", nargs="+"); ap.add_argument("--n", type=int, default=4)
a = ap.parse_args(); out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome"); pg = b.new_page(viewport={"width": 1440, "height": 1600})
    for app in a.apps:
        try:
            pg.goto("https://uibowl.io/name/" + urllib.parse.quote(app), wait_until="networkidle", timeout=30000)
            pg.wait_for_timeout(1500)
            srcs = pg.eval_on_selector_all("img", "els=>els.filter(e=>e.naturalHeight>e.naturalWidth*1.5 && e.naturalWidth>=200).map(e=>e.currentSrc||e.src)")
        except Exception as e:
            print(app, "실패", e); continue
        if not srcs: print(app, "화면 없음"); continue
        for i, src in enumerate(srcs[:a.n]):   # 브라우저 세션으로 받는다(쿠키·리퍼러 포함 → 403 회피, 오버레이 영향 없음)
            try:
                r = pg.request.get(src, headers={"Referer": "https://uibowl.io/"})
                if not r.ok: print(app, i, "HTTP", r.status); continue
                f = out / f"{app}-{i}.jpg"; f.write_bytes(r.body()); print("saved", f)
            except Exception as e:
                print(app, i, "받기 실패", e)
    b.close()
