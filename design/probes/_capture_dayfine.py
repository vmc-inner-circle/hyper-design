import asyncio, json, sys
from playwright.async_api import async_playwright

CAPTURE_ID = "b7ac8f11-0467-4562-8878-26273a3b54aa"
ENDPOINT = f"https://mcp.figma.com/mcp/capture/{CAPTURE_ID}/submit?bindVariables=true"
TARGET = "https://dayfine.me/"
OUT_PNG = r"C:\Code\hyper-design\design\references\existing\dayfine-home.png"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 900})

        async def strip_csp(route):
            response = await route.fetch()
            headers = dict(response.headers)
            headers.pop("content-security-policy", None)
            headers.pop("content-security-policy-report-only", None)
            await route.fulfill(response=response, headers=headers)
        await page.route("**/*", strip_csp)

        await page.goto(TARGET, wait_until="networkidle")
        await page.screenshot(path=OUT_PNG, full_page=True)

        # same-host links + anchors + headings for structure table
        info = await page.evaluate("""() => ({
            title: document.title,
            viewport: {w: innerWidth, h: innerHeight},
            links: [...document.querySelectorAll('a[href]')].map(a => ({href: a.getAttribute('href'), text: (a.textContent||'').trim().slice(0,40)})),
            headings: [...document.querySelectorAll('h1,h2,h3')].map(h => h.textContent.trim().slice(0,80)),
            navText: [...document.querySelectorAll('nav a, header a')].map(a => (a.textContent||'').trim()).filter(Boolean),
        })""")
        with open(r"C:\Code\hyper-design\design\references\existing\page-info.json", "w", encoding="utf-8") as f:
            json.dump(info, f, ensure_ascii=False, indent=1)
        print("PAGE_INFO_SAVED")

        r = await page.context.request.get("https://mcp.figma.com/mcp/html-to-design/capture.js")
        src = await r.text()
        await page.evaluate("(s) => { const el = document.createElement('script'); el.textContent = s; document.head.appendChild(el); }", src)
        await page.wait_for_timeout(500)
        res = await page.evaluate(
            "([cid, ep]) => window.figma.captureForDesign({ captureId: cid, endpoint: ep, selector: 'body' })",
            [CAPTURE_ID, ENDPOINT],
        )
        with open(r"C:\Code\hyper-design\design\references\existing\capture-result.json", "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=1)
        print("CAPTURE_DONE", str(res)[:200])
        await browser.close()

asyncio.run(main())
