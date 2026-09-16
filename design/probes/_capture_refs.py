import asyncio, json, sys
from playwright.async_api import async_playwright

TARGETS = [
    ("immersive-translate", "https://immersivetranslate.com/"),
    ("rememberry", "https://rememberry.com/"),
    ("raycast", "https://www.raycast.com/"),
]
OUT_DIR = r"C:\Code\hyper-design\design\references"

async def main():
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        for slug, url in TARGETS:
            try:
                page = await browser.new_page(viewport={"width": 1440, "height": 900})
                try:
                    await page.goto(url, wait_until="networkidle", timeout=45000)
                except Exception:
                    await page.wait_for_timeout(5000)
                out = f"{OUT_DIR}\\{slug}-1.png"
                await page.screenshot(path=out, full_page=False)
                title = await page.title()
                results.append({"slug": slug, "url": url, "png": out, "title": title, "ok": True})
                await page.close()
            except Exception as e:
                results.append({"slug": slug, "url": url, "ok": False, "err": str(e)[:200]})
        await browser.close()
    with open(OUT_DIR + r"\capture-log.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=1)
    print(json.dumps([{ "slug": r["slug"], "ok": r["ok"], "title": r.get("title","")[:60]} for r in results], ensure_ascii=False))

asyncio.run(main())
