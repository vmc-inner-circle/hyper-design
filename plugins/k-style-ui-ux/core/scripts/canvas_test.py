#!/usr/bin/env python3
"""캔버스(out/index.html) 상호작용 테스트 — Playwright(python, channel="chrome").

python3 canvas_test.py <out_dir> [--shot PNG]

결과를 JSON 으로 출력({"pass": bool, "passed": n, "total": n, "checks": [...]}). 하나라도 실패하면 종료코드 1.
확인: 헤더 조작 그룹 3개·모드 토글 0 / 빈 곳 200px 드래그 → 판 이동 / 카드 클릭 → 모달, Esc → 닫힘 /
      Ctrl+휠 → 배율 변경, 전체 보기 → 배율 변경 / Foundation 색 칸 ≥ 20 / Components 섹션 ≥ 5 /
      팔레트 점 → Foundation 브랜드 칸 값 변경 / 콘솔 에러 0 / 첫 로드 < 1초
"""
import sys, json, time, argparse
from pathlib import Path

MODE_WORDS = ("편집", "선택 모드", "범위", "모드", "손 도구", "Edit", "Select", "Mode")

FIND_EMPTY_JS = r"""
() => {
  const pane = document.getElementById('screens'), r = pane.getBoundingClientRect();
  const ok = el => el && (el === pane || el.id === 'stage' || el.id === 'rows' || el.classList.contains('flow') ||
                          el.classList.contains('cards') || el.id === 'intro' || el.id === 'foot');
  for (let y = r.top + 40; y < r.bottom - 240; y += 23)
    for (let x = r.left + 40; x < r.right - 240; x += 31) {
      if (ok(document.elementFromPoint(x, y)) && ok(document.elementFromPoint(x + 200, y))) return {x, y};
    }
  return null;
}
"""


def run(out: Path, shot=None):
    from playwright.sync_api import sync_playwright
    checks, errors = [], []

    def add(cid, ok, value="", detail=""):
        checks.append({"id": cid, "pass": bool(ok), "value": value, "detail": detail})

    idx = out / "index.html"
    if not idx.exists():
        add("index_exists", False, detail=str(idx))
        return checks
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome")
        except Exception:
            browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.on("console", lambda m: errors.append(m.text[:160]) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(str(e)[:160]))
        zoom = lambda: float(page.get_attribute("#stage", "data-zoom") or 0)
        transform = lambda: page.eval_on_selector("#stage", "e => e.style.transform")
        try:
            t0 = time.time()
            page.goto(idx.resolve().as_uri(), wait_until="domcontentloaded", timeout=15000)
            page.wait_for_function("window.__hdReady !== undefined", timeout=5000)
            ready = page.evaluate("window.__hdReady")
            dcl = page.evaluate("(() => { const n = performance.getEntriesByType('navigation')[0]; return n ? n.domContentLoadedEventEnd : 0 })()")
            wall = (time.time() - t0) * 1000
            add("first_load_under_1s", ready < 1000 and dcl < 1000, f"ready {ready:.0f}ms · DOMContentLoaded {dcl:.0f}ms", f"wall {wall:.0f}ms")
            page.wait_for_timeout(300)
            loaded = page.evaluate("document.querySelectorAll('.phone iframe[src]').length")
            total = page.evaluate("document.querySelectorAll('.phone iframe').length")

            # (1) 조작 그룹 3개, 모드 토글 없음
            groups = page.eval_on_selector_all("header [data-group]", "els => els.map(e => e.dataset.group)")
            modes = page.evaluate("""(words) => [...document.querySelectorAll('header button, header [role=switch], header input')]
                .filter(b => b.hasAttribute('data-mode') || words.some(w => (b.textContent || '').includes(w))).map(b => b.textContent.trim())""", list(MODE_WORDS))
            add("header_groups", sorted(groups) == ["palette", "tabs", "view"], groups)
            add("no_mode_toggle", not modes, len(modes), ", ".join(modes))

            # (2) 빈 곳 200px 드래그 → transform 변경
            pt = page.evaluate(FIND_EMPTY_JS)
            if pt:
                before = transform()
                page.mouse.move(pt["x"], pt["y"]); page.mouse.down()
                for i in range(1, 11):
                    page.mouse.move(pt["x"] + 20 * i, pt["y"] + 4 * i)
                page.mouse.up()
                after = transform()
                add("drag_pans", before != after, f"{before} → {after}")
                modal_open = page.evaluate("!document.getElementById('modal').hidden")
                add("drag_no_modal", not modal_open, modal_open)
            else:
                add("drag_pans", False, detail="빈 곳을 찾지 못함")
            page.click("#zoom")          # 처음 배율·위치로
            page.wait_for_timeout(200)

            # (3) 카드 클릭 → 모달, Esc → 닫힘
            box = page.evaluate("""() => { const pr = document.getElementById('screens').getBoundingClientRect();
                for (const c of document.querySelectorAll('.cover')) { const r = c.getBoundingClientRect();
                  if (r.top > pr.top && r.top + 40 < pr.bottom && r.left > pr.left && r.right < pr.right) return {x: r.left + r.width / 2, y: r.top + Math.min(r.height / 2, (pr.bottom - r.top) / 2)}; }
                return null; }""")
            if box:
                page.mouse.click(box["x"], box["y"])
                page.wait_for_timeout(250)
                opened = page.evaluate("!document.getElementById('modal').hidden && !!document.getElementById('mframe').getAttribute('src')")
                size = page.evaluate("(() => { const f = document.getElementById('mframe'); return [f.offsetWidth, f.offsetHeight] })()")
                add("card_click_opens_modal", opened and size == [390, 844], f"open={opened} iframe={size}")
                page.keyboard.press("Escape"); page.wait_for_timeout(150)
                closed = page.evaluate("document.getElementById('modal').hidden")
                add("esc_closes_modal", closed, closed)
            else:
                add("card_click_opens_modal", False, detail="보이는 카드 없음")
                add("esc_closes_modal", False, detail="보이는 카드 없음")

            # (4) Ctrl+휠 → 배율, 전체 보기 → 배율
            z0 = zoom()
            page.mouse.move(700, 500)
            page.keyboard.down("Control"); page.mouse.wheel(0, -240); page.keyboard.up("Control")
            page.wait_for_timeout(150)
            z1 = zoom()
            add("ctrl_wheel_zooms", abs(z1 - z0) > 0.01, f"{z0} → {z1}")
            page.click("#fit"); page.wait_for_timeout(150)
            z2 = zoom()
            add("fit_changes_zoom", abs(z2 - z1) > 0.01 and 0 < z2 <= 1.5, f"{z1} → {z2}")
            page.mouse.move(700, 500)
            t1 = transform()
            page.mouse.wheel(0, 200); page.wait_for_timeout(150)
            add("wheel_pans_not_zooms", abs(zoom() - z2) < 1e-4 and transform() != t1, transform())
            page.click("#zoom"); page.wait_for_timeout(300)

            # (5) Foundation 색 칸 ≥ 20
            page.click(".tab[data-tab=foundation]")
            page.wait_for_function("document.querySelector('#foundation iframe').getAttribute('src')", timeout=3000)
            ff = page.frame_locator("#foundation iframe")
            ff.locator(".sw").first.wait_for(timeout=5000)
            nsw = ff.locator(".sw[data-var^='--c-']").count()
            add("foundation_colors", nsw >= 20, nsw)
            brand = ff.locator(".sw[data-var='--c-brand'] .val")
            page.wait_for_timeout(300)
            v0 = brand.text_content() if brand.count() else ""

            # (7) 팔레트 점 → 브랜드 칸 값 변경
            dots = page.locator("header .dot[aria-pressed=false]")
            if dots.count() and v0:
                dots.first.click()
                v1 = v0
                for _ in range(30):
                    page.wait_for_timeout(100)
                    v1 = brand.text_content()
                    if v1 != v0:
                        break
                add("palette_changes_foundation", v1 != v0, f"{v0} → {v1}")
            else:
                add("palette_changes_foundation", False, detail=f"dots={dots.count()} brand={v0!r}")

            # (6) Components 섹션 ≥ 5
            page.click(".tab[data-tab=components]")
            cf = page.frame_locator("#components iframe")
            try:
                cf.locator("section.spec").first.wait_for(timeout=5000)
            except Exception:
                pass
            nsec = cf.locator("section.spec").count()
            add("components_sections", nsec >= 5, nsec)

            page.click(".tab[data-tab=screens]"); page.wait_for_timeout(200)
            add("lazy_iframes", 0 < loaded < total or total <= 4, f"{loaded}/{total} 로드됨(보이는 것만)")
            if shot:
                page.wait_for_timeout(1500)
                page.screenshot(path=str(shot))
        except Exception as e:
            add("run", False, detail=str(e)[:300])
        add("console_errors", not errors, len(errors), " | ".join(errors[:5]))
        browser.close()
    return checks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--shot")
    a = ap.parse_args()
    checks = run(Path(a.out), a.shot)
    passed = sum(c["pass"] for c in checks)
    res = {"pass": passed == len(checks), "passed": passed, "total": len(checks), "checks": checks}
    print(json.dumps(res, ensure_ascii=False, indent=1, default=str))
    sys.exit(0 if res["pass"] else 1)


if __name__ == "__main__":
    main()
