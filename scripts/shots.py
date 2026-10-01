"""화면 캡처 (v7 엔진). 브라우저 하나로 연속 — 장당 1초 안팎.

    python scripts/shots.py app design/app/app.json            # 모든 화면 × 폰(390)·PC(1440) → design/shots/<id>-m.png, <id>-d.png
    python scripts/shots.py app design/app/app.json --only home,plan
    python scripts/shots.py page design/ask/q1.html [--w 1280]  # 페이지 전체 길이 캡처 → 같은 이름 .png
    python scripts/shots.py cand design/cand                   # 폴더 안 *.html 을 폰 크기로(후보 미리보기) → 같은 이름 .png (+ --d 면 PC 도 -d.png)

찍고 나서 PNG 를 눈으로 본다(깨짐·겹침·잘림·빈 공간·AI 티). 이 캡처가 검사 근거다.
"""
import json
import pathlib
import sys

from playwright.sync_api import sync_playwright

M = {"width": 390, "height": 844}
D = {"width": 1440, "height": 900}


def main():
    a = sys.argv[1:]
    mode, target = a[0], pathlib.Path(a[1])
    with sync_playwright() as pw:
        try:
            b = pw.chromium.launch(channel="chrome")
        except Exception:  # Chrome 이 없으면 playwright 기본 Chromium
            b = pw.chromium.launch()
        if mode == "app":
            spec = json.loads(target.read_text(encoding="utf-8"))
            only = set(a[a.index("--only") + 1].split(",")) if "--only" in a else None
            app = target.parent / "app.html"
            out = target.parent.parent / "shots"
            out.mkdir(parents=True, exist_ok=True)
            for suffix, vp in (("m", M), ("d", D)):
                pg = b.new_page(viewport=vp)
                pg.goto(app.resolve().as_uri())
                pg.wait_for_timeout(900)
                for s in spec["screens"]:
                    if only and s["id"] not in only:
                        continue
                    pg.set_viewport_size(vp)
                    pg.evaluate(f"location.hash={json.dumps(s['id'])}")
                    pg.wait_for_timeout(250)
                    h = pg.evaluate("document.documentElement.scrollHeight")
                    pg.set_viewport_size({"width": vp["width"], "height": max(vp["height"], h)})  # 탭바(sticky)가 중간에 찍히지 않게
                    pg.wait_for_timeout(150)
                    p = out / f"{s['id']}-{suffix}.png"
                    pg.screenshot(path=str(p))
                    print(p)
                pg.close()
        elif mode == "page":
            w = int(a[a.index("--w") + 1]) if "--w" in a else 1280
            pg = b.new_page(viewport={"width": w, "height": 900})
            pg.goto(target.resolve().as_uri() + "?cap")
            pg.wait_for_timeout(900)
            p = target.with_suffix(".png")
            pg.screenshot(path=str(p), full_page=True)
            print(p)
        elif mode == "cand":
            files = sorted(target.glob("*.html")) if target.is_dir() else [target]
            for suffix, vp in (("", M), ("-d", D)) if "--d" in a else (("", M),):
                pg = b.new_page(viewport=vp)
                for f in files:
                    pg.goto(f.resolve().as_uri())
                    pg.wait_for_timeout(700)
                    p = f.with_name(f.stem + suffix + ".png")
                    pg.screenshot(path=str(p))
                    print(p)
                pg.close()
        b.close()


if __name__ == "__main__":
    main()
