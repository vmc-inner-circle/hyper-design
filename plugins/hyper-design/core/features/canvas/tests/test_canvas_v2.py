"""캔버스 v2 — 연결 보기 · 요소 고르기 · 메모 저장 · 보내기 (Playwright, 실제 브라우저).

runs/laundry-v1/out 를 임시 폴더로 복사하고 build_canvas.py 로 다시 만든 뒤 index.html 을 file:// 로 연다.
"""
import os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent
REPO = SCRIPTS.parents[4]
FIXTURE = REPO / "runs" / "laundry-v1" / "out"
SHOTS = REPO / "tasks" / "0-harness-v2" / "phase3-shots"

sync_api = pytest.importorskip("playwright.sync_api")
if not FIXTURE.exists():
    pytest.skip(f"fixture 없음: {FIXTURE}", allow_module_level=True)


@pytest.fixture(scope="module")
def out_dir():
    tmp = Path(tempfile.mkdtemp(prefix="hd-canvas-v2-"))
    out = tmp / "out"
    shutil.copytree(FIXTURE, out)
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, str(SCRIPTS / "build_canvas.py"), str(out)], capture_output=True, text=True, encoding="utf-8", env=env)
    assert r.returncode == 0, r.stderr
    yield out
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture(scope="module")
def browser():
    with sync_api.sync_playwright() as p:
        b = None
        for kw in ({"channel": "chrome"}, {}):
            try:
                b = p.chromium.launch(**kw)
                break
            except Exception:
                continue
        if b is None:
            pytest.skip("chromium 을 띄울 수 없음")
        yield b
        b.close()


@pytest.fixture(scope="module")
def ctx(browser):
    c = browser.new_context(viewport={"width": 1440, "height": 1000})
    yield c
    c.close()


@pytest.fixture(scope="module")
def page(ctx, out_dir):
    pg = ctx.new_page()
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto((out_dir / "index.html").resolve().as_uri())
    pg.wait_for_function("window.__hdReady !== undefined")
    pg.evaluate("Object.keys(localStorage).filter(k => k.startsWith('hd-')).forEach(k => localStorage.removeItem(k))")
    reload(pg)
    pg.errors = errors
    yield pg
    assert not errors, errors


def reload(pg):
    pg.reload()
    pg.wait_for_function("window.__hdReady !== undefined")
    pg.wait_for_timeout(200)


def visible_paths(pg):
    return pg.evaluate("[...document.querySelectorAll('#rows path.ln')].filter(p => getComputedStyle(p).display !== 'none').length")


def test_arrow_toggle_persists(page):
    total = page.locator("#rows path.ln").count()
    assert total > 0
    assert visible_paths(page) == total
    page.click("#arrows")
    assert visible_paths(page) == 0
    reload(page)
    assert visible_paths(page) == 0
    assert page.get_attribute("#arrows", "aria-pressed") == "false"
    page.keyboard.press("a")                       # 단축키 A 로 다시 켜기
    assert visible_paths(page) == total
    reload(page)
    assert visible_paths(page) == total


def test_shift_click_focus(page):
    page.click("#fit")
    page.wait_for_timeout(200)
    fid = page.evaluate("document.querySelector('#rows path.ln').getAttribute('data-from')")
    linked = set(page.evaluate("""(id) => [...document.querySelectorAll('#rows path.ln')]
        .filter(p => p.dataset.from === id || p.dataset.to === id).flatMap(p => [p.dataset.from, p.dataset.to])""", fid))
    box = page.locator(f'.card[data-id="{fid}"] .cover').bounding_box()
    page.keyboard.down("Shift")
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.keyboard.up("Shift")
    page.wait_for_timeout(600)
    assert page.evaluate("document.getElementById('modal').hidden"), "Shift+클릭은 크게 보기를 열지 않는다"
    # 화면 안 링크의 대상(색 고리)도 연결된 화면이다
    linked |= set(page.evaluate("[...document.querySelectorAll('#rows .card.lt')].map(c => c.dataset.id)"))
    state = page.evaluate("""() => [...document.querySelectorAll('#rows .card')].map(c =>
        [c.dataset.id, c.classList.contains('hl'), +getComputedStyle(c).opacity])""")
    for cid, hl, op in state:
        if cid in linked:
            assert hl and op == 1, (cid, hl, op)
        else:
            assert not hl and op < 0.5, (cid, hl, op)
    on = page.evaluate("[...document.querySelectorAll('#rows path.ln')].map(p => [p.classList.contains('on'), +getComputedStyle(p).opacity])")
    assert any(o for o, _ in on) and all((op == 1) if o else (op < 0.5) for o, op in on)
    SHOTS.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(SHOTS / "focus-mode.png"))
    page.keyboard.press("Escape")
    page.wait_for_timeout(100)
    assert page.evaluate("!document.getElementById('rows').classList.contains('focusing') && !document.querySelector('#rows .card.hl')")
    page.click("#zoom")


def open_screen(pg, sid):
    pg.evaluate("""(id) => { const c = document.querySelector('.card[data-id="' + id + '"] .cover');
        c.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true})); }""", sid)
    pg.wait_for_function("!document.getElementById('modal').hidden")
    fr = pg.frame_locator("#mframe")
    fr.locator("body").wait_for()
    pg.wait_for_timeout(300)
    return fr


def test_pick_note_pin_persists(page):
    sid = page.evaluate("document.querySelector('#rows .card').dataset.id")
    fr = open_screen(page, sid)
    page.click("#mpick")
    assert page.get_attribute("#mpick", "aria-pressed") == "true"
    page.wait_for_timeout(150)
    target = fr.locator("h1, h2, button, a").filter(has_text=re.compile(r"\S")).first
    want = re.sub(r"\s+", " ", target.inner_text()).strip()[:60]
    target.click()
    page.wait_for_selector("#pop:not([hidden])")
    assert page.text_content("#ptitle") == want
    assert page.text_content("#ppath")
    page.fill("#pnote", "가격을 오른쪽 끝으로 붙이고 굵게")
    page.click("#padd")
    assert page.locator("#mpins .pin").count() == 1
    assert page.text_content("#mpins .pin") == "①"
    SHOTS.mkdir(parents=True, exist_ok=True)
    # 팝오버 + 핀을 한 장에: 두 번째 요소를 고른 상태로 찍고 취소
    fr.locator("body *").filter(has_text=re.compile(r"\S")).nth(3).click()
    page.wait_for_selector("#pop:not([hidden])")
    page.screenshot(path=str(SHOTS / "popover-pin.png"))
    page.click("#pcancel")
    assert page.locator(f'.card[data-id="{sid}"] .nbadge').text_content() == "1"
    reload(page)
    assert page.locator(f'.card[data-id="{sid}"] .nbadge').text_content() == "1"
    open_screen(page, sid)
    assert page.locator("#mpins .pin").count() == 1
    page.keyboard.press("Escape")


def test_send_format(page):
    page.wait_for_selector("#notes:not([hidden])")
    page.click("#nsend")
    t = page.evaluate("window.__hdLastSend")
    assert t, "보내기 글이 없음"
    lines = t.split("\n")
    m = re.match(r"^\[hyper-design 수정 요청\] out=(.+) · (\d+)건$", lines[0])
    assert m, lines[0]
    out = m.group(1)
    assert not out.startswith("/") or os.name != "nt", out
    assert out.replace("\\", "/").rstrip("/").lower().endswith("/out")
    n = int(m.group(2))
    assert n == 1 and len(lines) == 1 + 3 * n
    assert re.match(r"^1\. screen=\S+ · path=.+$", lines[1]), lines[1]
    assert re.match(r'^   text=".*" · intent=(change|question)$', lines[2]), lines[2]
    assert lines[3] == "   요청: 가격을 오른쪽 끝으로 붙이고 굵게"
    assert "복사했어요" in page.text_content("#nmsg")


def test_clear_sent(page):
    assert page.is_visible("#nclear")
    page.click("#nclear")
    assert page.evaluate("document.querySelectorAll('#nlist li').length") == 0
    assert page.is_hidden("#notes")
    reload(page)
    assert page.locator(".nbadge").count() == 0


def test_multi_select_note(page):
    """주석 달기에서 Shift+클릭 2개 → 요소 2개 · 핀 번호 하나가 두 곳 · 보내기는 요소마다 한 항목(형식 그대로)."""
    sid = page.evaluate("document.querySelector('#rows .card').dataset.id")
    fr = open_screen(page, sid)
    page.click("#mpick")
    page.wait_for_timeout(150)
    els = fr.locator("h1, h2, button, a").filter(has_text=re.compile(r"\S"))
    assert els.count() >= 2
    els.nth(0).click(modifiers=["Shift"])
    page.wait_for_selector("#pop:not([hidden])")
    els.nth(1).click(modifiers=["Shift"])
    page.wait_for_timeout(150)
    assert page.text_content("#ptitle").startswith("2개 요소"), page.text_content("#ptitle")
    assert page.locator("#mpins .sel-box").count() == 2
    assert page.evaluate("document.getElementById('mframe').getAttribute('src')"), "Shift+클릭이 화면을 옮기면 안 된다"
    page.fill("#pnote", "두 곳 모두 굵게")
    page.click("#padd")
    pins = page.locator("#mpins .pin")
    assert pins.count() == 2 and pins.nth(0).text_content() == pins.nth(1).text_content() == "①"
    assert "2개 요소" in page.text_content("#nlist")
    page.keyboard.press("Escape")
    page.click("#nsend")
    t = page.evaluate("window.__hdLastSend")
    lines = t.split("\n")
    assert re.match(r"^\[hyper-design 수정 요청\] out=.+ · 2건$", lines[0]), lines[0]
    assert len(lines) == 7
    assert lines[1].startswith("1. screen=" + sid + " · path=") and lines[4].startswith("2. screen=" + sid + " · path=")
    assert lines[1] != lines[4]
    assert lines[3] == lines[6] == "   요청: 두 곳 모두 굵게"
    page.click("#nclear")


# ---------------------------------------------------------------- gym-v2: 색 링크 · 확대 · 주석 달기 · 안내
GYM = REPO / "runs" / "gym-v2" / "out"
GSHOTS = REPO / "tasks" / "1-canvas-links-imggen" / "shots"


@pytest.fixture(scope="module")
def gym_out():
    if not GYM.exists():
        pytest.skip(f"fixture 없음: {GYM}")
    tmp = Path(tempfile.mkdtemp(prefix="hd-canvas-gym-"))
    out = tmp / "out"
    shutil.copytree(GYM, out)
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, str(SCRIPTS / "build_canvas.py"), str(out)], capture_output=True, text=True, encoding="utf-8", env=env)
    assert r.returncode == 0, r.stderr
    yield out
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture(scope="module")
def gpage(ctx, gym_out):
    pg = ctx.new_page()
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto((gym_out / "index.html").resolve().as_uri())
    pg.wait_for_function("window.__hdReady !== undefined")
    pg.wait_for_timeout(300)
    yield pg
    assert not errors, errors
    pg.close()


def link_targets(out, sid):
    ids = {p.stem for p in (out / "screens").glob("*.html")}
    t = (out / "screens" / f"{sid}.html").read_text(encoding="utf-8")
    seen = []
    for h in re.findall(r"""href\s*=\s*["']([^"'#?]+)\.html""", t):
        if h in ids and h != sid and h not in seen:
            seen.append(h)
    return seen


def rgb(hx):
    v = int(hx.lstrip("#"), 16)
    return f"rgb({v >> 16 & 255}, {v >> 8 & 255}, {v & 255})"


def zoom_to(pg, sid, min_h=420):
    """전체 보기 → 그 카드 위에서 Ctrl+휠로 카드 높이가 min_h 가 될 때까지 확대."""
    pg.keyboard.press("0")
    pg.wait_for_timeout(150)
    for _ in range(40):
        b = pg.locator(f'.card[data-id="{sid}"] .phone').bounding_box()
        if b["height"] >= min_h:
            break
        pg.mouse.move(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2)
        pg.keyboard.down("Control"); pg.mouse.wheel(0, -200); pg.keyboard.up("Control")
        pg.wait_for_timeout(60)
    b, pr = pg.locator(f'.card[data-id="{sid}"] .phone').bounding_box(), pg.locator("#screens").bounding_box()
    pg.mouse.move(pr["x"] + 200, pr["y"] + 200)
    pg.mouse.wheel(b["x"] - (pr["x"] + 60), b["y"] - (pr["y"] + 60))    # 카드 윗부분이 판 안에 오게
    pg.wait_for_timeout(400)
    return pg.locator(f'.card[data-id="{sid}"] .phone').bounding_box()


def test_gym_link_colors(gpage, gym_out):
    sid = "pass" if len(link_targets(gym_out, "pass")) >= 2 else next(
        p.stem for p in sorted((gym_out / "screens").glob("*.html")) if len(link_targets(gym_out, p.stem)) >= 2)
    want = link_targets(gym_out, sid)
    zoom_to(gpage, sid, 380)
    gpage.evaluate("""(id) => document.querySelector('.card[data-id="' + id + '"] .cover')
        .dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, shiftKey: true}))""", sid)
    gpage.wait_for_function("document.querySelectorAll('#lks path.lk').length >= 1", timeout=5000)
    assert gpage.evaluate("document.getElementById('modal').hidden")
    # v3: 첫 Shift+클릭이 '전체' (v2 에서는 색 1 부터였다)
    for _ in range(len(want) + 1):
        if "전체" in gpage.text_content("#lgTitle"):
            break
        gpage.evaluate("""(id) => document.querySelector('.card[data-id="' + id + '"] .cover')
            .dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, shiftKey: true}))""", sid)
    assert "전체" in gpage.text_content("#lgTitle")
    gpage.wait_for_timeout(200)
    arrows = gpage.evaluate("[...document.querySelectorAll('#lks path.lk')].map(p => [p.dataset.to, p.getAttribute('stroke')])")
    color = {}
    for to, c in arrows:
        assert color.setdefault(to, c) == c, ("같은 대상은 같은 색", to)
    assert set(color) == set(want), (color, want)
    assert len(set(color.values())) == len(color), ("대상마다 다른 색", color)
    assert [to for to, _ in arrows][0] == want[0]          # 처음 나온 순서대로 색을 준다
    for to, c in color.items():
        ring = gpage.evaluate("""(id) => { const c = document.querySelector('.card[data-id="' + id + '"]');
            return [c.classList.contains('lt'), c.style.getPropertyValue('--ring'), getComputedStyle(c.querySelector('.phone')).boxShadow]; }""", to)
        assert ring[0] and ring[1].strip().lower() == c.lower() and rgb(c) in ring[2], (to, c, ring)
    fr = gpage.frame_locator(f'.card[data-id="{sid}"] .phone iframe')
    outl = fr.locator("[data-hd-links]")
    assert outl.count() == len(arrows)
    inner = set(outl.evaluate_all("els => els.map(e => getComputedStyle(e).borderTopColor)"))
    assert inner == {rgb(c) for c in color.values()}, inner
    GSHOTS.mkdir(parents=True, exist_ok=True)
    gpage.screenshot(path=str(GSHOTS / "a-focus-links.png"))
    gpage.keyboard.press("Escape")
    gpage.wait_for_timeout(300)
    assert gpage.evaluate("document.querySelectorAll('#lks path.lk, .card.lt, .lnum, #lkl .ltag').length") == 0
    assert gpage.evaluate("!document.getElementById('rows').classList.contains('focusing')")
    assert outl.count() == 0


def test_gym_zoom_floor_and_fit(gpage):
    gpage.click("#zoom")
    gpage.wait_for_timeout(150)
    gpage.mouse.move(700, 500)
    for _ in range(20):
        gpage.keyboard.down("Control"); gpage.mouse.wheel(0, 400); gpage.keyboard.up("Control")
        gpage.wait_for_timeout(30)
    z = float(gpage.get_attribute("#stage", "data-zoom"))
    assert z < 0.25, z
    assert int(gpage.text_content("#zoom").rstrip("%")) < 25
    gpage.keyboard.press("0")
    gpage.wait_for_timeout(200)
    pr = gpage.locator("#screens").bounding_box()
    boxes = gpage.evaluate("[...document.querySelectorAll('#rows .card')].map(c => { const r = c.getBoundingClientRect(); return [c.dataset.id, r.left, r.top, r.right, r.bottom]; })")
    for cid, l, t, r, b in boxes:
        assert l >= pr["x"] - 1 and t >= pr["y"] - 1 and r <= pr["x"] + pr["width"] + 1 and b <= pr["y"] + pr["height"] + 1, cid
    gpage.wait_for_timeout(800)
    GSHOTS.mkdir(parents=True, exist_ok=True)
    gpage.screenshot(path=str(GSHOTS / "b-zoomed-out.png"))


def test_gym_annotate_button(gpage):
    sid = gpage.evaluate("document.querySelector('#rows .card').dataset.id")
    gpage.evaluate("""(id) => document.querySelector('.card[data-id="' + id + '"] .cover')
        .dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}))""", sid)
    gpage.wait_for_function("!document.getElementById('modal').hidden")
    gpage.frame_locator("#mframe").locator("body").wait_for()
    gpage.wait_for_timeout(400)
    assert gpage.text_content("#mpick").strip() == "주석 달기"
    pb, fb = gpage.locator("#mpick").bounding_box(), gpage.locator("#mbox").bounding_box()
    assert pb["y"] + pb["height"] <= fb["y"], (pb, fb)          # v2: 휴대폰 위 가운데
    assert pb["y"] >= 0
    assert abs((pb["x"] + pb["width"] / 2) - (fb["x"] + fb["width"] / 2)) < 2
    assert pb["y"] + pb["height"] <= gpage.viewport_size["height"]
    GSHOTS.mkdir(parents=True, exist_ok=True)
    gpage.screenshot(path=str(GSHOTS / "c-modal-annotate.png"))
    gpage.keyboard.press("Escape")
    gpage.wait_for_timeout(150)
    assert gpage.evaluate("document.getElementById('modal').hidden")
    # 카드에 올리면 '주석' → 누르면 주석 달기가 켜진 채로 크게 보기
    b = zoom_to(gpage, sid)
    anno = gpage.locator(f'.card[data-id="{sid}"] .anno')
    gpage.mouse.move(5, 5)
    assert not anno.is_visible()
    gpage.mouse.move(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2)
    gpage.wait_for_timeout(100)
    assert anno.is_visible() and anno.text_content().strip() == "주석"
    ab = anno.bounding_box()
    assert ab["y"] + ab["height"] <= b["y"] + 0.5, (ab, b)      # v2: 카드 바깥(오른쪽 위)
    anno.click()
    gpage.wait_for_function("!document.getElementById('modal').hidden")
    assert gpage.get_attribute("#mpick", "aria-pressed") == "true"
    gpage.keyboard.press("Escape")
    gpage.wait_for_timeout(150)


def test_gym_shortcut_hint(gpage):
    hint = gpage.locator("#khint")
    assert hint.is_visible()
    assert hint.text_content().strip() == "Shift+클릭 연결 보기 · A 주요 흐름 · 0 전체 보기 · 클릭 크게 보기"   # v3: 화살표 → 주요 흐름
    hb, pr = hint.bounding_box(), gpage.locator("#screens").bounding_box()
    assert hb["x"] < pr["x"] + 40 and hb["y"] + hb["height"] > pr["y"] + pr["height"] - 40
    gpage.evaluate("document.querySelector('#rows .cover').dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}))")
    gpage.wait_for_function("!document.getElementById('modal').hidden")
    assert not hint.is_visible()
    gpage.keyboard.press("Escape")
    gpage.wait_for_timeout(150)
    assert hint.is_visible()


# ---------------------------------------------------------------- canvas-focus-v2
FSHOTS = REPO / "tasks" / "2-canvas-focus-v2" / "shots"
V3SHOTS = REPO / "tasks" / "3-canvas-v3" / "shots"

LABEL_GEOM_JS = """() => [...document.querySelectorAll('#rows .alabel')].map(n => {
    const p = [...document.querySelectorAll('#rows path.ln')].find(q => q.dataset.from === n.dataset.from && q.dataset.to === n.dataset.to);
    const b = p ? p.getBBox() : null;
    return {left: n.style.left, top: n.style.top, box: b && [b.x, b.y, b.x + b.width, b.y + b.height]};
})"""


def test_v2_label_positions(gpage):
    """회귀(0efa322): .alabel 의 style 따옴표가 깨져 모든 이름표가 판 원점에 쌓였다."""
    labels = gpage.evaluate(LABEL_GEOM_JS)
    assert labels, "gym-v2 에 갈래 이름표가 있어야 한다"
    for l in labels:
        assert l["left"].endswith("px") and l["top"].endswith("px"), l
        x, y = float(l["left"][:-2]), float(l["top"][:-2])
        assert not (abs(x) < 1 and abs(y) < 1), ("원점에 쌓임", l)
        x0, y0, x1, y1 = l["box"]
        dx = max(x0 - x, 0, x - x1)
        dy = max(y0 - y, 0, y - y1)
        assert (dx * dx + dy * dy) ** 0.5 <= 400, l


def shift_click(pg, sid):
    pg.evaluate("""(id) => document.querySelector('.card[data-id="' + id + '"] .cover')
        .dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, shiftKey: true}))""", sid)


def lk_state(pg):
    return pg.evaluate("""() => ({title: document.getElementById('lgTitle').textContent,
        legend: !document.getElementById('legend').hidden,
        paths: [...document.querySelectorAll('#lks path.lk')].map(p => [p.dataset.to, p.getAttribute('stroke')]),
        rows: document.querySelectorAll('#lgRows .lgrow').length})""")


EMPTY_JS = r"""() => {
  const pane = document.getElementById('screens'), r = pane.getBoundingClientRect();
  const ok = el => el && (el === pane || el.id === 'stage' || el.id === 'rows' || el.classList.contains('flow') ||
                          el.classList.contains('cards') || el.id === 'intro' || el.id === 'foot');
  for (let y = r.top + 40; y < r.bottom - 60; y += 17)
    for (let x = r.left + 40; x < r.right - 400; x += 23) if (ok(document.elementFromPoint(x, y))) return {x, y};
  return null;
}"""


ALL_JS = "(() => { const a = document.getElementById('lgAll'); return a ? [a.checked, a.indeterminate] : null; })()"


def test_v2_focus_cycle(gpage, gym_out):
    """v3(S1): Shift+클릭 = 전체 → 다시 = 그룹 1 … n → 전체. 범례 '모두 표시' 체크 · 직접 선택."""
    want = link_targets(gym_out, "pass")
    n = len(want)
    assert n >= 2
    gpage.keyboard.press("Escape")
    zoom_to(gpage, "pass", 380)
    shift_click(gpage, "pass")
    gpage.wait_for_function("document.querySelectorAll('#lks path.lk').length >= 1", timeout=5000)
    gpage.wait_for_timeout(300)
    st = lk_state(gpage)
    assert st["legend"] and st["title"].endswith(f"전체 {n}개"), st
    assert {t for t, _ in st["paths"]} == set(want) and len({c for _, c in st["paths"]}) == n, st
    assert gpage.evaluate("document.querySelectorAll('#lgRows .lgrow[data-k]').length") == n
    assert gpage.evaluate(ALL_JS) == [True, False]
    V3SHOTS.mkdir(parents=True, exist_ok=True)
    gpage.wait_for_timeout(600)
    gpage.screenshot(path=str(V3SHOTS / "p1-a-all.png"))
    gpage.screenshot(path=str(FSHOTS / "a-focus-all.png"))
    seen = []
    for k in range(1, n + 1):
        shift_click(gpage, "pass")
        st = lk_state(gpage)
        assert f"{k}/{n}" in st["title"], st
        cols = {c for _, c in st["paths"]}
        assert len(cols) == 1 and st["paths"][0][0] == want[k - 1], (k, st)
        assert cols.isdisjoint(seen), (k, st)
        seen += list(cols)
        assert gpage.evaluate(ALL_JS) == [False, True], k                      # 일부만 켜짐 = indeterminate
        if k == 1:
            gpage.wait_for_timeout(400)
            gpage.screenshot(path=str(V3SHOTS / "p1-b-one.png"))
            gpage.screenshot(path=str(FSHOTS / "b-focus-stage1.png"))
    shift_click(gpage, "pass")
    st = lk_state(gpage)
    assert st["title"].endswith(f"전체 {n}개") and len({c for _, c in st["paths"]}) == n, st
    shift_click(gpage, "pass")
    st = lk_state(gpage)
    assert f"1/{n}" in st["title"] and {c for _, c in st["paths"]} == {seen[0]}, st
    # 범례 체크를 끄면 다음 Shift+클릭 전까지 그대로 · 제목 = 직접 선택
    gpage.locator("#lgRows .lgrow[data-k] input").first.uncheck()
    st = lk_state(gpage)
    assert len(st["paths"]) == 0 and st["title"].endswith(f"직접 선택 0/{n}"), st
    assert gpage.evaluate(ALL_JS) == [False, False]
    assert gpage.evaluate("document.getElementById('rows').classList.contains('focusing')"), "범례 조작은 연결 보기를 끄지 않는다"
    gpage.locator("#lgAll").check()
    st = lk_state(gpage)
    assert st["title"].endswith(f"직접 선택 {n}/{n}") and len({c for _, c in st["paths"]}) == n, st
    assert gpage.evaluate(ALL_JS) == [True, False]
    gpage.locator("#lgAll").uncheck()
    assert len(lk_state(gpage)["paths"]) == 0 and gpage.evaluate(ALL_JS) == [False, False]
    shift_click(gpage, "pass")
    assert f"2/{n}" in lk_state(gpage)["title"]


def test_v2_hover_emphasis(gpage):
    for _ in range(6):
        if "전체" in lk_state(gpage)["title"]:
            break
        shift_click(gpage, "pass")
    row = gpage.locator("#lgRows .lgrow[data-k]").first
    row.hover()
    gpage.wait_for_timeout(350)
    res = gpage.evaluate("""() => {
        const k = document.querySelector('#lgRows .lgrow[data-k]').dataset.k;
        const ps = [...document.querySelectorAll('#lks path.lk')];
        const me = ps.find(p => p.dataset.k === k), to = me.dataset.to;
        const tags = [...document.querySelectorAll('#lkl .ltag.on')];
        return {me: +getComputedStyle(me).opacity,
                others: ps.filter(p => p.dataset.to !== to).map(p => +getComputedStyle(p).opacity),
                mytag: +getComputedStyle(tags.find(t => t.dataset.k === k)).opacity,
                tags: tags.filter(t => t.dataset.k !== k).map(t => +getComputedStyle(t).opacity),
                lrows: [...document.querySelectorAll('#lgRows .lgrow[data-k]')].filter(r => r.dataset.k !== k).map(r => +getComputedStyle(r).opacity),
                rings: [...document.querySelectorAll('#rows .card.lt')].filter(c => c.dataset.id !== to).map(c => +getComputedStyle(c).opacity),
                myring: +getComputedStyle(document.querySelector('.card[data-id="' + to + '"]')).opacity};
    }""")
    assert res["me"] == 1 and res["myring"] == 1, res
    assert res["others"] and all(o < 0.5 for o in res["others"]), res
    assert res["rings"] and all(o < 0.5 for o in res["rings"]), res
    assert res["mytag"] == 1 and res["tags"] and all(o < 0.5 for o in res["tags"]), res           # v3: 태그·범례 줄도 흐리게
    assert res["lrows"] and all(o < 0.6 for o in res["lrows"]), res
    gpage.screenshot(path=str(FSHOTS / "c-hover-emphasis.png"))
    V3SHOTS.mkdir(parents=True, exist_ok=True)
    gpage.screenshot(path=str(V3SHOTS / "p1-c-hover.png"))
    gpage.mouse.move(5, 300)


def parse_path(d):
    toks = re.findall(r"[MLQCSAZ]|-?\d+(?:\.\d+)?", d)
    cmds, i = [], 0
    while i < len(toks):
        c = toks[i]; i += 1
        nums = []
        while i < len(toks) and not toks[i].isalpha():
            nums.append(float(toks[i])); i += 1
        cmds.append((c, nums))
    return cmds


def check_route(d, max_q=3):
    """둥근 직각 연결선: M/L/Q 만, L 은 가로·세로만, 꺾임(Q) ≤ max_q, 자기 교차 없음."""
    cmds = parse_path(d)
    assert {c for c, _ in cmds} <= {"M", "L", "Q"}, d
    assert cmds[0][0] == "M"
    assert sum(1 for c, _ in cmds if c == "Q") <= max_q, d
    pts, cur = [], tuple(cmds[0][1])
    pts.append(cur)
    for c, n in cmds[1:]:
        if c == "L":
            nxt = (n[0], n[1])
            assert abs(nxt[0] - cur[0]) < 0.25 or abs(nxt[1] - cur[1]) < 0.25, ("사선", cur, nxt, d)
            pts.append(nxt); cur = nxt
        else:
            qx, qy, ex, ey = n
            for t in [i / 8 for i in range(1, 9)]:
                pts.append(((1 - t) ** 2 * cur[0] + 2 * (1 - t) * t * qx + t * t * ex, (1 - t) ** 2 * cur[1] + 2 * (1 - t) * t * qy + t * t * ey))
            cur = (ex, ey)
    segs = [(pts[i], pts[i + 1]) for i in range(len(pts) - 1) if pts[i] != pts[i + 1]]

    def o(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])

    def cross(a, b, c, e):
        d1, d2, d3, d4 = o(c, e, a), o(c, e, b), o(a, b, c), o(a, b, e)
        return d1 * d2 < -1e-6 and d3 * d4 < -1e-6
    for i in range(len(segs)):
        for j in range(i + 2, len(segs)):
            assert not cross(*segs[i], *segs[j]), ("자기 교차", d)
    return cmds


def test_v2_route_shapes(gpage):
    cases = gpage.evaluate("""() => {
        const R = window.HDCanvas.routeCurve, s = {x: 400, y: 500, dir: 'right'};
        return [R(s, {x: 1100, y: 100}), R(s, {x: -300, y: 100}), R(s, {x: -200, y: 1500}), R(s, {x: 900, y: 1500}),
                R(s, {x: 420, y: 100}), R(s, {x: 400, y: 100}, {apex: 32, k: 2}),
                R({x: 500, y: 300, dir: 'up'}, {x: 1300, y: 290}), R({x: 500, y: 300, dir: 'up'}, {x: 100, y: 1300}, {apex: 28}),
                R({x: 500, y: 1300, dir: 'up'}, {x: 1200, y: 290})];
    }""")
    for d in cases:
        check_route(d)
    lane = gpage.evaluate("window.HDCanvas.routeCurve({x: 900, y: 300, dir: 'up'}, {x: 400, y: 1300}, {lift: 16, apex: 10, laneX: 220})")
    check_route(lane, 4)                                  # 다른 줄 갈래: 왼쪽 통로(꺾임 4)
    a, b, c = (parse_path(d) for d in cases[:3])          # (a) 오른쪽 (b) 왼쪽 (c) 아래 왼쪽
    assert a[-1][1] == [1100, 100] and b[-1][1] == [-300, 100] and c[-1][1] == [-200, 1500]
    # 화면 위 모든 선도 같은 규칙, 화살촉 색 = 선 색
    on = gpage.evaluate("""() => [...document.querySelectorAll('#lks path.lk')].map(p => {
        const id = (p.getAttribute('marker-end') || '').match(/#([^)]+)/)[1];
        return [p.getAttribute('d'), p.getAttribute('stroke'), document.querySelector('#' + id + ' path').getAttribute('fill')]; })""")
    assert on
    for d, stroke, fill in on:
        check_route(d, 5)                                  # v3: 다른 줄 대상은 왼쪽 통로로(꺾임 ≤ 5)
        assert stroke.lower() == fill.lower(), (stroke, fill)
    for d in gpage.evaluate("[...document.querySelectorAll('#rows path.ln')].map(p => p.getAttribute('d'))"):
        check_route(d, 4)


def test_v2_exit_focus(gpage):
    assert gpage.evaluate("document.getElementById('rows').classList.contains('focusing')")
    pt = gpage.evaluate(EMPTY_JS)
    assert pt, "빈 판 자리를 찾지 못함"
    gpage.mouse.click(pt["x"], pt["y"])
    gpage.wait_for_timeout(150)
    assert gpage.evaluate("!document.getElementById('rows').classList.contains('focusing') && document.getElementById('legend').hidden")
    assert gpage.evaluate("document.getElementById('modal').hidden")
    shift_click(gpage, "pass")
    gpage.wait_for_function("document.querySelectorAll('#lks path.lk').length >= 1", timeout=5000)
    gpage.keyboard.press("Escape")
    gpage.wait_for_timeout(150)
    assert gpage.evaluate("!document.getElementById('rows').classList.contains('focusing')")
    shift_click(gpage, "pass")
    gpage.wait_for_function("document.querySelectorAll('#lks path.lk').length >= 1", timeout=5000)
    gpage.evaluate("""() => document.querySelector('.card[data-id="pass"] .cover')
        .dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}))""")
    gpage.wait_for_function("!document.getElementById('modal').hidden")
    assert gpage.evaluate("!document.getElementById('rows').classList.contains('focusing') && !document.querySelector('#lks path.lk')")
    gpage.frame_locator("#mframe").locator("body").wait_for()
    gpage.wait_for_timeout(300)
    FSHOTS.mkdir(parents=True, exist_ok=True)
    gpage.screenshot(path=str(FSHOTS / "e-modal-annotate-top.png"))
    gpage.keyboard.press("Escape")
    gpage.wait_for_timeout(150)


def test_v2_expand_tall_screen(gpage, gym_out):
    sid = "renew"
    assert link_targets(gym_out, sid)
    zoom_to(gpage, sid, 300)
    before = gpage.evaluate("[...document.querySelectorAll('#rows .card')].map(c => [c.dataset.id, c.offsetLeft, c.offsetTop])")
    shift_click(gpage, sid)
    gpage.wait_for_function("document.querySelectorAll('#lks path.lk').length >= 1", timeout=5000)
    gpage.wait_for_timeout(300)
    h = gpage.evaluate(f"""document.querySelector('.card[data-id="{sid}"] .phone').offsetHeight""")
    assert h > 812, h
    after = gpage.evaluate("[...document.querySelectorAll('#rows .card')].map(c => [c.dataset.id, c.offsetLeft, c.offsetTop])")
    assert before == after
    ph = gpage.locator(f'.card[data-id="{sid}"] .phone').bounding_box()
    for _ in range(4):
        if "전체" in lk_state(gpage)["title"]:
            break
        shift_click(gpage, sid)
    gpage.wait_for_timeout(250)
    assert check_tags(gpage) > 0                          # v3: 칩(카드 테두리) 대신 선 위 태그 — 자기 차선 위
    FSHOTS.mkdir(parents=True, exist_ok=True)
    gpage.screenshot(path=str(FSHOTS / "d-expanded-tall.png"))
    gpage.keyboard.press("Escape")
    gpage.wait_for_timeout(400)
    assert gpage.evaluate(f"""document.querySelector('.card[data-id="{sid}"] .phone').offsetHeight""") == 812


def test_v2_base_curves_shot(gpage):
    gpage.keyboard.press("0")
    gpage.wait_for_timeout(300)
    assert gpage.evaluate("[...document.querySelectorAll('#rows .alabel')].every(n => getComputedStyle(n).display === 'none')")
    FSHOTS.mkdir(parents=True, exist_ok=True)
    gpage.screenshot(path=str(FSHOTS / "f-base-fit.png"))
    zoom_to(gpage, "pt-detail", 300)
    gpage.mouse.wheel(-420, -160)                          # 줄 위 통로와 왼쪽 카드가 보이게
    gpage.wait_for_timeout(400)
    gpage.screenshot(path=str(FSHOTS / "f-base-curves.png"))


CARD_BOXES_JS = """() => [...document.querySelectorAll('#rows .card')].map(c => {
    const ph = c.querySelector('.phone');
    return [c.dataset.id, c.offsetLeft, c.offsetTop, c.offsetLeft + c.offsetWidth, c.offsetTop + Math.max(c.offsetHeight, ph.offsetHeight)]; })"""


def vertical_points(d, step=4, skip=12):
    """세로 L 구간 위 점들(경로 처음·끝 12px 제외)."""
    cmds = parse_path(d)
    cur, out, segs = tuple(cmds[0][1]), [], []
    for c, n in cmds[1:]:
        nxt = (n[-2], n[-1])
        if c == "L" and abs(nxt[0] - cur[0]) < 0.25 and abs(nxt[1] - cur[1]) > 0:
            segs.append((cur, nxt))
        cur = nxt
    start, end = tuple(cmds[0][1]), cur
    for a, b in segs:
        n = max(1, int(abs(b[1] - a[1]) // step))
        for i in range(n + 1):
            p = (a[0], a[1] + (b[1] - a[1]) * i / n)
            if min(((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2) ** 0.5 for q in (start, end)) > skip:
                out.append(p)
    return out


def assert_no_vertical_in_cards(pg, sel):
    boxes = pg.evaluate(CARD_BOXES_JS)
    paths = pg.evaluate(f"[...document.querySelectorAll('{sel}')].map(p => [p.dataset.from, p.dataset.to, p.getAttribute('d')])")
    for fr, to, d in paths:
        for x, y in vertical_points(d):
            for cid, l, t, r, b in boxes:
                assert not (l < x < r and t < y < b), (f"{fr}→{to} 세로선이 카드 {cid} 안을 지남", (x, y), d)
    return len(paths)


def test_v2_no_vertical_through_cards(gpage, gym_out):
    gpage.keyboard.press("Escape")
    assert assert_no_vertical_in_cards(gpage, "#rows path.ln") > 0
    for sid in ("pass", "renew", "pt-detail", "home"):
        if not link_targets(gym_out, sid):
            continue
        zoom_to(gpage, sid, 300)
        shift_click(gpage, sid)
        gpage.wait_for_function("document.querySelectorAll('#lks path.lk').length >= 1", timeout=5000)
        for _ in range(12):
            if "전체" in lk_state(gpage)["title"]:
                break
            shift_click(gpage, sid)
        gpage.wait_for_timeout(350)
        assert assert_no_vertical_in_cards(gpage, "#lks path.lk") > 0, sid
        assert check_tags(gpage) > 0, sid                 # v3: 칩 대신 선 위 태그(자기 차선 위, 안 겹침)
        gpage.keyboard.press("Escape")
        gpage.wait_for_timeout(400)


# ---------------------------------------------------------------- canvas-v3 (phase 1): 옆면 출발 · 선 위 태그 · 주요 흐름 점선
LINK_GEOM_JS = """() => ({
    paths: [...document.querySelectorAll('#lks path.lk')].map(p => ({k: +p.dataset.k, to: p.dataset.to, pts: JSON.parse(p.dataset.pts)})),
    tags: [...document.querySelectorAll('#lkl .ltag.on')].map(n => ({k: +n.dataset.k, text: n.textContent, x: n.offsetLeft, y: n.offsetTop, w: n.offsetWidth, h: n.offsetHeight}))})"""


def _segs(pts):
    return [(pts[i], pts[i + 1]) for i in range(len(pts) - 1) if pts[i] != pts[i + 1]]


def _overlap(s1, s2):
    (a, b), (c, d) = s1, s2
    if abs(a[1] - b[1]) < 0.01 and abs(c[1] - d[1]) < 0.01 and abs(a[1] - c[1]) < 0.01:
        return max(0, min(max(a[0], b[0]), max(c[0], d[0])) - max(min(a[0], b[0]), min(c[0], d[0])))
    if abs(a[0] - b[0]) < 0.01 and abs(c[0] - d[0]) < 0.01 and abs(a[0] - c[0]) < 0.01:
        return max(0, min(max(a[1], b[1]), max(c[1], d[1])) - max(min(a[1], b[1]), min(c[1], d[1])))
    return 0


def check_tags(pg):
    """보이는 태그: 가운데가 자기 그룹의 가로(차선) 구간 위(±2px) · 태그끼리 안 겹침 · 다른 그룹 세로선과 안 겹침.
    서로 다른 그룹의 선은 20px 넘게 같은 줄을 나눠 쓰지 않는다(경로 계획 꺾은선으로 확인)."""
    g = pg.evaluate(LINK_GEOM_JS)
    by = {}
    for p in g["paths"]:
        by.setdefault(p["k"], []).extend(_segs(p["pts"]))
    for t in g["tags"]:
        hs = [s for s in by[t["k"]] if abs(s[0][1] - s[1][1]) < 0.01]
        assert any(abs(t["y"] - a[1]) <= 2 and min(a[0], b[0]) - 2 <= t["x"] <= max(a[0], b[0]) + 2 for a, b in hs), ("태그가 자기 차선 위가 아님", t, hs)
        box = (t["x"] - t["w"] / 2, t["y"] - t["h"] / 2, t["x"] + t["w"] / 2, t["y"] + t["h"] / 2)
        for k, segs in by.items():
            if k == t["k"]:
                continue
            for a, b in segs:
                if abs(a[0] - b[0]) < 0.01:
                    y0, y1 = min(a[1], b[1]), max(a[1], b[1])
                    assert not (box[0] < a[0] < box[2] and y0 < box[3] and box[1] < y1), ("태그가 다른 그룹 세로선 위", t, (a, b))
    for i, a in enumerate(g["tags"]):
        for b in g["tags"][i + 1:]:
            assert abs(a["x"] - b["x"]) >= (a["w"] + b["w"]) / 2 or abs(a["y"] - b["y"]) >= (a["h"] + b["h"]) / 2, ("태그 겹침", a, b)
    ks = sorted(by)
    for i, k1 in enumerate(ks):
        for k2 in ks[i + 1:]:
            for s1 in by[k1]:
                for s2 in by[k2]:
                    assert _overlap(s1, s2) <= 20, ("다른 그룹 선이 겹침", k1, k2, s1, s2)
    return len(g["tags"])


def focus_all(pg, sid, n_max=12):
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(200)
    zoom_to(pg, sid, 300)
    shift_click(pg, sid)
    pg.wait_for_function("document.querySelectorAll('#lks path.lk').length >= 1", timeout=5000)
    pg.wait_for_timeout(900)                               # 긴 화면은 펼친 뒤 다시 그린다
    assert "전체" in lk_state(pg)["title"]


def test_v3_back_exits_left(gpage, gym_out):
    """S2: 왼쪽 위 '뒤로' → 선은 그 요소의 왼쪽 가장자리에서 출발해 왼쪽으로 나간다(카드 왼쪽 바깥 통로)."""
    for sid in ("trainer-change", "pass"):
        to = link_targets(gym_out, sid)[0]
        focus_all(gpage, sid)
        fr = gpage.frame_locator(f'.card[data-id="{sid}"] .phone iframe')
        el = fr.locator('a[aria-label="뒤로"]').first.evaluate("e => { const r = e.getBoundingClientRect(); return [r.left, r.width]; }")
        left = gpage.evaluate(f"""document.querySelector('.card[data-id="{sid}"]').offsetLeft""")
        assert el[0] + el[1] / 2 < 375 * 0.3, el
        pts = gpage.evaluate(f"""JSON.parse(document.querySelector('#lks path.lk[data-to="{to}"]').dataset.pts)""")
        x0, x1 = pts[0][0], pts[1][0]
        assert abs(x0 - (left + el[0])) <= 2, (sid, pts[0], left, el)     # 요소 왼쪽 가장자리에서 출발
        assert x1 < x0 and x1 < left and abs(pts[1][1] - pts[0][1]) < 0.01, (sid, pts)   # 첫 구간은 왼쪽으로, 카드 밖까지
        if sid == "trainer-change":
            gpage.wait_for_timeout(300)
            V3SHOTS.mkdir(parents=True, exist_ok=True)
            gpage.screenshot(path=str(V3SHOTS / "p1-d-back.png"))


def test_v3_tags_on_lanes(gpage, gym_out):
    """S2: 태그는 선 위(자기 차선) · 태그끼리 · 다른 세로선과 안 겹침 · 서로 다른 그룹 선은 같은 줄을 나눠 쓰지 않음."""
    for sid in ("pass", "trainer-change", "renew", "pt-detail", "home", "log-today"):
        if not link_targets(gym_out, sid):
            continue
        focus_all(gpage, sid)
        assert check_tags(gpage) > 0, sid
        assert assert_no_vertical_in_cards(gpage, "#lks path.lk") > 0, sid


def test_v3_same_target_merge(gpage, gym_out):
    """S2: 같은 대상으로 가는 요소 여럿 = 줄기 하나 · 태그 하나('A · B (2)') · 범례 한 줄."""
    focus_all(gpage, "home")
    n = len(link_targets(gym_out, "home"))
    g = gpage.evaluate(LINK_GEOM_JS)
    assert len(g["tags"]) == n and gpage.evaluate("document.querySelectorAll('#lgRows .lgrow[data-k]').length") == n
    merged = [t for t in g["tags"] if t["text"].endswith(" (2)")]
    assert merged, g["tags"]
    for t in merged:
        assert " · " in t["text"], t
        assert sum(1 for p in g["paths"] if p["k"] == t["k"]) == 2                     # 요소마다 출발, 같은 줄기
        rows = gpage.evaluate(f"""[...document.querySelectorAll('#lgRows .lgrow[data-k="{t["k"]}"]')].map(r => r.textContent)""")
        assert len(rows) == 1 and "(2)" in rows[0], rows
        a, b = [p["pts"] for p in g["paths"] if p["k"] == t["k"]]
        assert a[2:] == b[2:], (a, b)                                                  # 바깥 통로 · 차선 · 내려가는 선 공유


def test_v3_main_flow_dashed(gpage):
    """S3: 회색 갈래 화살표 = '주요 흐름' 회색 점선. 버튼 · A · 범례 체크로 켜고 끄기, 새로고침 뒤에도. 설명 문단 없음."""
    gpage.keyboard.press("Escape")
    gpage.wait_for_timeout(200)
    vis = lambda: gpage.evaluate("[...document.querySelectorAll('#rows path.ln')].filter(p => getComputedStyle(p).display !== 'none').length")
    total = gpage.locator("#rows path.ln").count()
    assert total > 0 and vis() == total
    dash = gpage.evaluate("[...document.querySelectorAll('#rows path.ln')].map(p => getComputedStyle(p).strokeDasharray)")
    assert all(d and d != "none" for d in dash), dash
    assert gpage.text_content("#arrows").strip() == "주요 흐름"
    assert "설계 단계" not in gpage.evaluate("document.body.innerText")
    assert gpage.evaluate("[...document.querySelectorAll('#rows .alabel')].every(n => getComputedStyle(n).display === 'none')")
    zoom_to(gpage, "pt-detail", 300)
    gpage.mouse.wheel(-420, -160)
    gpage.wait_for_timeout(500)
    V3SHOTS.mkdir(parents=True, exist_ok=True)
    gpage.screenshot(path=str(V3SHOTS / "p1-e-base.png"))
    gpage.click("#arrows")
    assert vis() == 0 and gpage.get_attribute("#arrows", "aria-pressed") == "false"
    gpage.reload()
    gpage.wait_for_function("window.__hdReady !== undefined")
    gpage.wait_for_timeout(300)
    assert vis() == 0 and gpage.get_attribute("#arrows", "aria-pressed") == "false"
    gpage.keyboard.press("a")
    assert vis() == total
    # 범례 맨 아래 체크(연결 보기 중)
    zoom_to(gpage, "pass", 300)
    shift_click(gpage, "pass")
    gpage.wait_for_function("!document.getElementById('legend').hidden", timeout=5000)
    assert gpage.evaluate("document.getElementById('lgFlow').checked")
    assert gpage.text_content("#legend .lgflow").strip() == "주요 흐름 (회색 점선)"
    gpage.locator("#lgFlow").uncheck()
    assert vis() == 0 and gpage.get_attribute("#arrows", "aria-pressed") == "false"
    assert gpage.evaluate("document.getElementById('rows').classList.contains('focusing')")
    # 연결 보기 중 주요 흐름은 흐리게(.18), 태그를 덮지 않는다(태그 층이 위)
    gpage.locator("#lgFlow").check()
    assert vis() == total - gpage.locator("#rows path.ln.rep").count()   # 색 링크가 대신 그리는 갈래(.rep)는 연결 보기 중 숨김
    ops = gpage.evaluate("[...document.querySelectorAll('#rows path.ln:not(.on)')].map(p => +getComputedStyle(p).opacity)")
    assert ops and all(abs(o - 0.18) < 0.01 for o in ops), ops
    gpage.reload()
    gpage.wait_for_function("window.__hdReady !== undefined")
    gpage.wait_for_timeout(300)
    assert vis() == total


# ---------------------------------------------------------------- canvas-v3 (phase 2): Ctrl+클릭 카메라 · 전환 메뉴 · 선 색/굵기
CAM_DONE = "window.__hdCam && !window.__hdCam.running"
OFFSET_JS = """(id) => { const r = document.querySelector('.card[data-id="' + id + '"] .phone').getBoundingClientRect(),
    p = document.getElementById('screens').getBoundingClientRect();
    return [r.left + r.width / 2 - (p.left + p.width / 2), r.top + r.height / 2 - (p.top + p.height / 2)]; }"""


def ctrl_click_link(pg, sid, text):
    """카드 안 링크 요소 자리를 Ctrl+클릭(카드 위 덮개가 받는다)."""
    b = pg.frame_locator(f'.card[data-id="{sid}"] .phone iframe').locator("a", has_text=text).first.bounding_box()
    pg.keyboard.down("Control")
    pg.mouse.click(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2)
    pg.keyboard.up("Control")


def centred(pg, sid, tol=8):
    dx, dy = pg.evaluate(OFFSET_JS, sid)
    return abs(dx) <= tol and abs(dy) <= tol


def test_v3_ctrl_click_camera(gpage, gym_out):
    """S4: 카드 안 링크 Ctrl+클릭 → 화면은 이동하지 않고, 카메라가 대상 카드 가운데로(8px) · 그 쌍만 강조. 범례 줄 Ctrl+클릭도. Esc 는 바로 멈춤."""
    want = link_targets(gym_out, "pass")
    gpage.keyboard.press("Escape")
    zoom_to(gpage, "pass", 380)
    frame_url = lambda: gpage.frame_locator('.card[data-id="pass"] .phone iframe').locator("body").evaluate("() => location.href")
    url0 = frame_url()
    ctrl_click_link(gpage, "pass", "일시정지 신청")
    gpage.wait_for_function("window.__hdCam && window.__hdCam.running", timeout=3000)
    gpage.wait_for_timeout(420)
    V3SHOTS.mkdir(parents=True, exist_ok=True)
    gpage.screenshot(path=str(V3SHOTS / "p2-b-mid.png"))
    gpage.wait_for_function(CAM_DONE, timeout=4000)
    assert gpage.evaluate("window.__hdCam.to") == "pause"
    gpage.wait_for_timeout(120)
    gpage.screenshot(path=str(V3SHOTS / "p2-c-end.png"))
    assert centred(gpage, "pause"), gpage.evaluate(OFFSET_JS, "pause")
    assert frame_url() == url0, "Ctrl+클릭은 화면을 이동시키지 않는다"
    assert gpage.evaluate("document.querySelector('.card[data-id=\"pause\"]').classList.contains('pulse')")
    gpage.wait_for_function("document.querySelectorAll('#lks path.lk').length >= 1", timeout=5000)   # 연결 보기 밖 → 그 쌍 하나만
    assert set(gpage.evaluate("[...document.querySelectorAll('#lks path.lk')].map(p => p.dataset.to)")) == {"pause"}
    # 범례 줄 Ctrl+클릭: 그 대상으로, 체크는 그대로
    k = want.index("renew")
    row = gpage.locator(f'#lgRows .lgrow[data-k="{k}"]')
    before = row.locator("input").is_checked()
    row.locator(".lgtx").click(modifiers=["Control"])
    gpage.wait_for_function(CAM_DONE + " && window.__hdCam.to === 'renew'", timeout=4000)
    assert centred(gpage, "renew") and row.locator("input").is_checked() == before
    # Esc 중간에 → 그 자리에서 멈춤
    gpage.locator('#lgRows .lgrow[data-k="0"] .lgtx').click(modifiers=["Control"])
    gpage.wait_for_timeout(200)
    gpage.keyboard.press("Escape")
    v0 = gpage.evaluate("HDCanvas.view()")
    gpage.wait_for_timeout(300)
    assert gpage.evaluate("window.__hdCam.running") is False and gpage.evaluate("HDCanvas.view()") == v0
    assert not centred(gpage, want[0])


def test_v3_reduced_motion_jumps(gpage):
    """S4: prefers-reduced-motion: reduce → 카메라는 끝 상태로 바로."""
    gpage.emulate_media(reduced_motion="reduce")
    try:
        gpage.keyboard.press("Escape")
        zoom_to(gpage, "pass", 380)
        ctrl_click_link(gpage, "pass", "연장하기")
        gpage.wait_for_function("window.__hdCam && window.__hdCam.to === 'renew'", timeout=3000)
        assert gpage.evaluate("window.__hdCam.keys.length") == 1 and gpage.evaluate("window.__hdCam.running") is False
        assert centred(gpage, "renew")
    finally:
        gpage.emulate_media(reduced_motion="no-preference")
        gpage.keyboard.press("Escape")


def test_v3_transition_menu(gpage):
    """S6: T → 전환 메뉴(표의 전환마다 한 줄, 토큰 값) · ▶ 마다 페이지 오류 없음 · '애니메이션 끄기'는 새로고침 뒤에도, 카메라는 바로."""
    errs = []
    gpage.on("pageerror", lambda e: errs.append(str(e)))
    gpage.keyboard.press("Escape")
    gpage.mouse.click(5, 300)
    gpage.keyboard.press("t")
    gpage.wait_for_selector("#tmenu:not([hidden])")
    names = gpage.evaluate("[...document.querySelectorAll('#tmenu .trow .tn')].map(n => n.textContent)")
    assert names == ["포커스 진입 / 해제", "카드 펼치기 / 접기", "카메라 이동", "크게 보기 모달 열기/닫기", "범례 패널 표시", "드롭다운 / 팝오버", "태그·툴팁 등장"]
    vals = gpage.evaluate("[...document.querySelectorAll('#tmenu .trow .tv')].map(n => n.textContent)")
    assert all(re.match(r"^\d+ms · \S", v) for v in vals), vals
    gpage.wait_for_timeout(300)
    V3SHOTS.mkdir(parents=True, exist_ok=True)
    gpage.screenshot(path=str(V3SHOTS / "p2-a-menu.png"))
    for t in ["focus", "expand", "camera", "modal", "legend", "dropdown", "tooltip"]:
        gpage.click(f'#tmenu button[data-play="{t}"]')
        gpage.wait_for_timeout(1300)
        assert not errs, (t, errs)
    gpage.keyboard.press("Escape")
    gpage.wait_for_timeout(300)
    if gpage.is_hidden("#tmenu"):
        gpage.keyboard.press("t")
    gpage.check("#tmOff")
    assert gpage.evaluate("document.body.classList.contains('nomotion')")
    reload(gpage)
    assert gpage.evaluate("document.body.classList.contains('nomotion') && JSON.parse(localStorage.getItem('hd-canvas-prefs')).motion === false")
    zoom_to(gpage, "pass", 380)
    ctrl_click_link(gpage, "pass", "연장하기")
    gpage.wait_for_function("window.__hdCam && window.__hdCam.to === 'renew'", timeout=3000)
    assert gpage.evaluate("window.__hdCam.keys.length") == 1 and centred(gpage, "renew")
    gpage.keyboard.press("Escape")
    gpage.keyboard.press("t")
    gpage.wait_for_selector("#tmenu:not([hidden])")
    assert gpage.is_checked("#tmOff")
    gpage.uncheck("#tmOff")
    gpage.keyboard.press("Escape")
    assert not gpage.evaluate("document.body.classList.contains('nomotion')")
    assert not errs, errs


# ---------------------------------------------------------------- canvas-v3 (phase 3): 색 드롭다운 · 쌍 색 · 굵기
STROKES_JS = """() => [...document.querySelectorAll('#lks path.lk')].map(p => {
    const id = (p.getAttribute('marker-end') || '').match(/#([^)]+)/)[1];
    return [+p.dataset.k, p.getAttribute('stroke').toLowerCase(), document.querySelector('#' + id + ' path').getAttribute('fill').toLowerCase(), getComputedStyle(p).strokeWidth]; })"""


def set_width(pg, w):
    pg.evaluate("(w) => { const i = document.getElementById('lgW'); i.value = String(w); i.dispatchEvent(new Event('input', {bubbles: true})); }", w)


def test_v3_line_style(gpage):
    """S5: 색 드롭다운(진하게) · 랜덤(누를 때마다 다름, 메뉴 그대로) · 밖 클릭 닫기 · ● 쌍 색(그 쌍만) · 초기화 · 굵기 5(강조 7) · 새로고침 유지 · 설명 글 없음."""
    focus_all(gpage, "pass")
    deep = [c.lower() for c in gpage.evaluate("HDCanvas.style.PRESETS.deep.c")]
    gpage.click("#lgDdb")
    gpage.wait_for_selector("#lgDd:not([hidden])")
    gpage.wait_for_timeout(300)
    V3SHOTS.mkdir(parents=True, exist_ok=True)
    gpage.screenshot(path=str(V3SHOTS / "p3-a-dropdown.png"))
    dd, bt = gpage.locator("#lgDd").bounding_box(), gpage.locator("#lgDdb").bounding_box()
    assert dd["y"] + dd["height"] <= bt["y"], "위로 열림"
    gpage.click('#lgDd button[data-preset="deep"]')
    gpage.wait_for_timeout(250)
    assert gpage.is_hidden("#lgDd")
    st = gpage.evaluate(STROKES_JS)
    assert st and all(s in deep and f == s for _, s, f, _ in st), st
    set_width(gpage, 5)
    st = gpage.evaluate(STROKES_JS)
    assert {w for *_, w in st} == {"5px"}, st
    gpage.locator('#lgRows .lgrow[data-k="0"]').hover()
    gpage.wait_for_timeout(200)
    assert gpage.evaluate("getComputedStyle(document.querySelector('#lks path.lk.em')).strokeWidth") == "7px"
    gpage.mouse.move(5, 300)
    gpage.wait_for_timeout(200)
    gpage.screenshot(path=str(V3SHOTS / "p3-b-deep-width5.png"))
    # ● → 색판 → 그 쌍만
    before = {k: s for k, s, _, _ in gpage.evaluate(STROKES_JS)}
    chk = gpage.locator('#lgRows .lgrow[data-k="1"] input').is_checked()
    gpage.click('#lgRows .lgrow[data-k="1"] .lgdot')
    gpage.wait_for_selector("#lgSw:not([hidden])")
    assert gpage.locator('#lgRows .lgrow[data-k="1"] input').is_checked() == chk
    gpage.click('#lgSwG button[data-c="#F97316"]')
    gpage.wait_for_timeout(250)
    after = {k: s for k, s, _, _ in gpage.evaluate(STROKES_JS)}
    assert after[1] == "#f97316" and all(after[k] == before[k] for k in before if k != 1), (before, after)
    gpage.screenshot(path=str(V3SHOTS / "p3-c-custom-pair.png"))
    reload(gpage)
    focus_all(gpage, "pass")
    st = gpage.evaluate(STROKES_JS)
    assert {k: s for k, s, _, _ in st} == after and {w for *_, w in st} == {"5px"}, st
    # 초기화 → 프리셋 색으로
    gpage.click("#lgDdb")
    gpage.click('#lgDd button[data-act="reset"]')
    gpage.wait_for_timeout(250)
    assert {k: s for k, s, _, _ in gpage.evaluate(STROKES_JS)} == before
    # 밖 클릭 → 닫힘
    gpage.click("#lgDdb")
    gpage.wait_for_selector("#lgDd:not([hidden])")
    gpage.click("#lgTitle")
    gpage.wait_for_timeout(250)
    assert gpage.is_hidden("#lgDd")
    # 랜덤 두 번 → 색이 다름, 메뉴는 열린 채
    gpage.click("#lgDdb")
    gpage.click('#lgDd button[data-preset="random"]')
    gpage.wait_for_timeout(150)
    r1 = [s for _, s, _, _ in gpage.evaluate(STROKES_JS)]
    assert gpage.is_visible("#lgDd")
    gpage.click('#lgDd button[data-preset="random"]')
    gpage.wait_for_timeout(150)
    r2 = [s for _, s, _, _ in gpage.evaluate(STROKES_JS)]
    assert r1 != r2 and gpage.is_visible("#lgDd")
    # 스타일 줄엔 설명 문장이 없다(요소마다 자기 글 40자 이하)
    long = gpage.evaluate("""() => [...document.querySelectorAll('#lgStyle, #lgStyle *, #legend .lgflow, #legend .lgflow *, #lgDd *, #lgSw, #lgSw *')]
        .map(e => [...e.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent.trim()).join(' ')).filter(t => t.length > 40)""")
    assert not long, long
    gpage.evaluate("localStorage.removeItem('hd-canvas-prefs')")
    gpage.keyboard.press("Escape")
