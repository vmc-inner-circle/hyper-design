#!/usr/bin/env python3
"""html_audit.py 단위 테스트.

    python3 -m unittest scripts/tests/test_html_audit.py

정적 검사는 표준 라이브러리만으로 돈다. 렌더 판정 함수(render_findings)는 합성 측정값으로
검사하고, 실제 브라우저 렌더 테스트는 playwright·chromium 이 없으면 skip 한다.
"""

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = TESTS_DIR.parent
FIXTURES = TESTS_DIR / "fixtures"
HTML_OK = FIXTURES / "html_ok"
HTML_BAD = FIXTURES / "html_bad"

sys.path.insert(0, str(SCRIPTS_DIR))

import figma_audit  # noqa: E402
import html_audit  # noqa: E402

STATIC_RULES = {"token.bound", "token.defined", "icon.allowlist", "component.manifest",
                "state.frames", "button.primary-per-screen", "no-lorem", "no-external"}
RENDER_RULES = {"tap.min", "tap.gap", "space.grid", "fixed.no-clip", "text.clip", "frame.size", "safe-area"}


def rules_of(findings):
    return {f.rule for f in findings}


def run_main(argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = html_audit.main(argv)
    return code, out.getvalue(), err.getvalue()


def _playwright_ready():
    try:
        sync_playwright = html_audit._import_playwright()
    except ImportError:
        return False
    try:
        with sync_playwright() as p:
            p.chromium.launch().close()
        return True
    except Exception:
        return False


def thresholds():
    rules, warnings = figma_audit.parse_rules_file(str(HTML_OK / "design-rules.md"))
    return figma_audit.Thresholds(rules, warnings)


# ── 파서 ──────────────────────────────────────────────────────────────────
class CompositionParseTest(unittest.TestCase):
    """screens.md 구성 셀 파싱 — 괄호 안 설명·소제목을 컴포넌트로 읽지 않는다."""

    def test_parenthesis_with_middle_dot_is_ignored(self):
        cell = "① AppBar(뒤로 · 제주 가족여행 · eye 부모님 화면) + TripHeader(한 줄) · ② DateChips(20~24, 21 활성)"
        self.assertEqual(html_audit.parse_composition(cell), ["AppBar", "TripHeader", "DateChips"])

    def test_form_fields_description(self):
        cell = "② FormField×3(목적지 · 기간 · 여행 이름) · ③ Chip×5(구성원: 지수·영호 + 추가)"
        self.assertEqual(html_audit.parse_composition(cell), ["FormField", "Chip"])

    def test_heading_and_none(self):
        cell = '③ 소제목 web-h2 "챙길 것" + TodoItem×3(상비약 완료) · ④ (없음, 탭바 없음)'
        self.assertEqual(html_audit.parse_composition(cell), ["TodoItem"])

    def test_nested_parenthesis(self):
        cell = "③ DayFlowCard×3(20일 (비행기) 확정 + TentativeLine \"아직\" · 22일 TentativeLine만)"
        self.assertEqual(html_audit.parse_composition(cell), ["DayFlowCard"])

    def test_state_cell(self):
        cell = "default·empty·loading·error·many-items·text-120·guest-name(누구세요: NameButton×4)"
        self.assertEqual(html_audit.parse_state_cell(cell)[-1], "guest-name")
        self.assertEqual(len(html_audit.parse_state_cell(cell)), 7)

    def test_screens_md(self):
        rows, comp_list, warnings = html_audit.parse_screens_md(str(HTML_OK / "screens.md"))
        self.assertEqual([r["slug"] for r in rows], ["home", "create", "my-prep"])
        self.assertEqual(rows[2]["comps"], ["WebAddressBar", "AppBar", "WebSegment", "TodoItem"])
        self.assertIn("EmptyState", comp_list)
        self.assertEqual(warnings, [])

    def test_real_screens_md_has_no_description_words(self):
        """실제 design/screens.md 에서 괄호 안 한글 설명이 컴포넌트로 새지 않는다 (있을 때만)."""
        real = SCRIPTS_DIR.parent / "design" / "screens.md"
        if not real.is_file():
            self.skipTest("design/screens.md 없음")
        rows, comp_list, _ = html_audit.parse_screens_md(str(real))
        for r in rows:
            for c in r["comps"]:
                self.assertRegex(c, r"^[A-Z][A-Za-z0-9]+$")
                if comp_list:
                    self.assertIn(c, comp_list, "{} 의 {} 가 컴포넌트 목록 밖".format(r["slug"], c))


class IconListTest(unittest.TestCase):
    def test_allow_and_excluded(self):
        allow, excluded, warnings = html_audit.parse_icon_lists(str(HTML_OK / "icons.md"))
        self.assertIn("chevron-left", allow)
        self.assertEqual(len(allow), 12)
        self.assertEqual(excluded, {"arrow-left", "x-circle", "more-horizontal"})


class TokenMappingTest(unittest.TestCase):
    def setUp(self):
        rules, _ = figma_audit.parse_rules_file(str(HTML_OK / "design-rules.md"))
        self.tokens = {v: e for v, e, _ in html_audit.expected_tokens(rules)}

    def test_families(self):
        self.assertEqual(self.tokens["--color-bg"], "#FDFBF7")
        self.assertEqual(self.tokens["--color-accent-soft"], "rgba(249,115,22,.10)")
        self.assertEqual(self.tokens["--space-16"], "16px")
        self.assertEqual(self.tokens["--space-screen-padding"], "16px")
        self.assertEqual(self.tokens["--radius-full"], "9999px")
        self.assertEqual(self.tokens["--shadow-md"], "0 4px 12px rgba(0,0,0,.08)")
        self.assertEqual(self.tokens["--type-h3"], "17px")
        self.assertEqual(self.tokens["--type-h3-weight"], "600")
        self.assertEqual(self.tokens["--type-line-height-title"], "1.3")
        self.assertIn("--font-family", self.tokens)
        self.assertNotIn("--z-base", self.tokens)

    def test_canon(self):
        c = html_audit.canon_css
        self.assertEqual(c("#fdfbf7"), c("#FDFBF7"))
        self.assertEqual(c("rgba(249, 115, 22, 0.1)"), c("rgba(249,115,22,.10)"))
        self.assertEqual(c('"Pretendard", Roboto'), c("Pretendard,Roboto"))
        self.assertEqual(c("#fff"), c("#FFFFFF"))
        self.assertNotEqual(c("#000000"), c("#FDFBF7"))


class CssParseTest(unittest.TestCase):
    def test_nested_and_root(self):
        css = ":root{--a:#fff}\n@media (max-width:400px){.x{padding:10px}}\n.y{color:var(--a)}"
        decls, _ = html_audit.parse_css(css)
        root = [d for d in decls if d.is_root]
        self.assertEqual([(d.prop, d.value) for d in root], [("--a", "#fff")])
        x = next(d for d in decls if d.selector == ".x")
        self.assertEqual((x.prop, x.value, x.line, x.at), ("padding", "10px", 2, ["@media (max-width:400px)"]))

    def test_strings_and_urls(self):
        css = '.a{background:url("data:image/svg+xml;utf8,<svg>;</svg>");content:"a;b"}.b{gap:8px}'
        decls, _ = html_audit.parse_css(css)
        self.assertEqual([d.prop for d in decls], ["background", "content", "gap"])

    def test_literals(self):
        h = html_audit.hardcoded_literals
        self.assertEqual(h("padding", "0 1px"), [])
        self.assertEqual(h("padding", "var(--space-8) 10px"), [("px", "10px")])
        self.assertEqual(h("width", "390px"), [])                 # 간격 속성이 아니면 px 허용
        self.assertEqual(h("fill", "url(#grad)"), [])
        self.assertEqual(h("color", "#FFF"), [("color", "#FFF")])
        self.assertEqual(h("box-shadow", "0 1px 2px rgba(0,0,0,.1)"), [("color", "rgba(0,0,0,.1)")])
        self.assertEqual(h("font-size", "18px", text120=True), [])
        self.assertEqual(h("font-size", "18px"), [("px", "18px")])


# ── 정적 검사 (픽스처) ────────────────────────────────────────────────────
class StaticOkTest(unittest.TestCase):
    def test_ok_passes(self):
        findings, warnings, stats = html_audit.run_audit(str(HTML_OK))
        self.assertEqual([f.line() for f in findings], [])
        self.assertEqual(stats["sections"], 3)
        self.assertEqual(stats["frames"], 23)
        self.assertEqual(sorted(stats["files"]), ["final-preview.html", "rules-preview.html"])


class StaticBadTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.findings, cls.warnings, cls.stats = html_audit.run_audit(str(HTML_BAD))

    def by_rule(self, rule):
        return [f for f in self.findings if f.rule == rule]

    def test_every_static_rule_fails(self):
        missing = STATIC_RULES - rules_of(self.findings)
        self.assertFalse(missing, "실패하지 않은 정적 규칙: {}".format(sorted(missing)))

    def test_token_bound_style_and_inline(self):
        acts = {f.actual for f in self.by_rule("token.bound")}
        self.assertIn("padding: 10px", acts)
        self.assertIn("color: #ff0000", acts)
        self.assertIn("background: #123456", acts)
        # data-chrome 블록(#EEEEEE, 16px)은 면제
        self.assertFalse(any("EEEEEE" in a for a in acts))

    def test_token_defined(self):
        acts = [f.actual for f in self.by_rule("token.defined")]
        self.assertTrue(any(a.startswith("--color-bg: #000000") for a in acts))
        self.assertTrue(any("--radius-full 없음" in a for a in acts))
        self.assertTrue(any("var(--color-nope)" in a for a in acts))

    def test_icons(self):
        acts = {f.actual.split(" · ")[0] for f in self.by_rule("icon.allowlist")}
        self.assertIn("arrow-left (icons.md 제외 목록)", acts)
        self.assertIn("rocket (허용 목록 밖)", acts)
        self.assertIn("data-icon 래퍼 없는 <svg>", acts)
        self.assertIn("x-circle (icons.md 제외 목록)", acts)

    def test_manifest(self):
        acts = {f.actual for f in self.by_rule("component.manifest")}
        self.assertIn("TripHeader 없음", acts)
        self.assertIn("Snackbar (구성표 밖)", acts)
        self.assertIn("Banner (screens.md 컴포넌트 목록 밖)", acts)

    def test_state_frames_and_primary(self):
        states = self.by_rule("state.frames")
        self.assertEqual(len(states), 1)
        self.assertEqual((states[0].screen, states[0].actual), ("create", "누락 text-120/keyboard"))
        prim = self.by_rule("button.primary-per-screen")
        self.assertEqual([(f.screen, f.actual) for f in prim], [("home", "data-primary 2개")])

    def test_exempt_screen_has_no_primary_failure(self):
        self.assertFalse(any(f.screen == "my-prep" for f in self.by_rule("button.primary-per-screen")))

    def test_hygiene(self):
        self.assertEqual(len(self.by_rule("no-lorem")), 1)
        acts = {f.actual for f in self.by_rule("no-external")}
        self.assertEqual(acts, {"src=https://example.invalid/x.png", "href=https://cdn.example.invalid/x.css"})

    def test_render_rules_do_not_run_without_flag(self):
        self.assertFalse(RENDER_RULES & rules_of(self.findings))


class NoContractTest(unittest.TestCase):
    """계약(data-*) 이 없는 화면 파일 — 크래시 없이 '섹션 없음'으로 보고한다."""

    def test_missing_sections_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "probes"))
            for name in ("design-rules.md", "icons.md", "screens.md"):
                Path(tmp, name).write_text((HTML_OK / name).read_text(encoding="utf-8"), encoding="utf-8")
            Path(tmp, "probes", "final-preview.html").write_text(
                "<style>:root{--color-bg:#FDFBF7}</style><main id=m></main>"
                "<script>document.getElementById('m').innerHTML='<div class=phone></div>'</script>",
                encoding="utf-8")
            findings, warnings, _ = html_audit.run_audit(tmp)
        manifest = [f for f in findings if f.rule == "component.manifest"]
        states = [f for f in findings if f.rule == "state.frames"]
        self.assertEqual({f.screen for f in manifest}, {"home", "create", "my-prep"})
        self.assertTrue(all(f.actual == "data-screen 섹션 없음" for f in manifest))
        self.assertEqual(len(states), 3)
        self.assertTrue(any("--render" in w for w in warnings))
        self.assertTrue(any("rules-preview.html 가 없어" in w for w in warnings))


# ── CLI ───────────────────────────────────────────────────────────────────
class CliTest(unittest.TestCase):
    def test_exit_codes(self):
        self.assertEqual(run_main(["--design-dir", str(HTML_OK)])[0], 0)
        self.assertEqual(run_main(["--design-dir", str(HTML_BAD)])[0], 1)
        code, _, err = run_main(["--design-dir", str(FIXTURES / "nope")])
        self.assertEqual(code, 2)
        self.assertIn("[ERROR]", err)

    def test_missing_rules_is_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "probes"))
            Path(tmp, "probes", "final-preview.html").write_text("<p>x</p>", encoding="utf-8")
            self.assertEqual(run_main(["--design-dir", tmp])[0], 2)

    def test_text_format(self):
        code, out, _ = run_main(["--design-dir", str(HTML_BAD)])
        fails = [l for l in out.splitlines() if l.startswith("[FAIL]")]
        self.assertTrue(fails)
        for line in fails:
            self.assertRegex(line, r"^\[FAIL\] [^/ ]+/[^/ ]+/\S+ .+\(.*\) [a-z.\-]+: .+ → .+$")
        self.assertIn("실패", out.strip().splitlines()[-2])

    def test_json_shape(self):
        code, out, _ = run_main(["--design-dir", str(HTML_BAD), "--json"])
        data = json.loads(out)
        self.assertEqual(code, 1)
        for key in ("stats", "failureCountByRule", "findings", "warnings"):
            self.assertIn(key, data)
        self.assertEqual(set(data["findings"][0]),
                         {"rule", "file", "screen", "state", "node", "selector", "actual", "expected"})
        self.assertEqual(sum(data["failureCountByRule"].values()), len(data["findings"]))

    def test_fix_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "html-fix-list.md")
            run_main(["--design-dir", str(HTML_BAD), "--fix-list", path])
            text = Path(path).read_text(encoding="utf-8")
        self.assertIn("| 화면 | 상태 | 요소 | 규칙 키 | 현재값 → 기대값 |", text)
        self.assertIn("button.primary-per-screen", text)
        # 파일 단위 결함(화면 '-')은 화면 칸에 파일 이름
        self.assertIn("| final-preview.html | - |", text)
        self.assertNotIn("| - | - |", text)

    def test_render_without_playwright_is_exit_2(self):
        original = html_audit._import_playwright

        def boom():
            raise ImportError("No module named 'playwright'")
        html_audit._import_playwright = boom
        try:
            code, _, err = run_main(["--design-dir", str(HTML_OK), "--render"])
        finally:
            html_audit._import_playwright = original
        self.assertEqual(code, 2)
        self.assertIn("pip install playwright", err)


# ── 렌더 판정 (합성 측정값, playwright 불필요) ────────────────────────────
def frame_scope(**kw):
    base = {"screen": "home", "state": "default", "raw_state": "default", "width": 390,
            "rect": {"w": 390, "h": 844}, "taps": [], "spacing": [], "fixed": [], "scrolls": [],
            "truncates": [], "untagged": [], "overflow": []}
    base.update(kw)
    return base


def tap(x, y, w=44, h=44, parent=1, grouped=False, sel="span"):
    return {"sel": sel, "node": "AppBar", "parent": parent, "grouped": grouped, "x": x, "y": y, "w": w, "h": h}


class RenderJudgeTest(unittest.TestCase):
    def setUp(self):
        self.th = thresholds()

    def judge(self, **kw):
        return html_audit.render_findings("final-preview.html", [frame_scope(**kw)], self.th)

    def test_clean_frame(self):
        fixed = [{"sel": "cta", "kind": "cta", "top": 700, "bottom": 756, "height": 56, "paddingBottom": 0, "safeH": 0},
                 {"sel": "tab", "kind": "tabbar", "top": 756, "bottom": 810, "height": 54, "paddingBottom": 0, "safeH": 0}]
        out = self.judge(taps=[tap(0, 0), tap(52, 0)], fixed=fixed,
                         scrolls=[{"sel": "body", "lastSel": "row", "lastBottom": 684}],
                         spacing=[{"sel": "x", "node": "AppBar", "prop": "paddingTop", "value": 16}],
                         truncates=[{"sel": "t", "node": "TodoItem", "lines": 2, "clamp": "2", "ellipsis": False,
                                     "nowrap": False, "ovx": "hidden", "sh": 60, "ch": 44, "sw": 10, "cw": 10}])
        self.assertEqual([f.line() for f in out], [])

    def test_frame_size(self):
        self.assertEqual(rules_of(self.judge(rect={"w": 130, "h": 281})), {"frame.size"})
        self.assertEqual(rules_of(self.judge(width=360)), {"frame.size"})

    def test_tap_min_and_gap(self):
        out = self.judge(taps=[tap(0, 0, 32, 32), tap(36, 0)])
        self.assertEqual(rules_of(out), {"tap.min", "tap.gap"})

    def test_tap_gap_group_exempt(self):
        out = self.judge(taps=[tap(0, 0, 97, 48, grouped=True), tap(97, 0, 97, 48, grouped=True)])
        self.assertEqual(out, [])

    def test_space_grid_grouped(self):
        spacing = [{"sel": "a > b", "node": "Snackbar", "prop": p, "value": 10}
                   for p in ("paddingTop", "paddingRight", "paddingBottom", "paddingLeft")]
        out = self.judge(spacing=spacing + [{"sel": "a > c", "node": "Snackbar", "prop": "rowGap", "value": 2}])
        self.assertEqual(len(out), 2)
        self.assertIn("paddingTop·paddingRight·paddingBottom·paddingLeft 10px", {f.actual for f in out})

    def test_space_grid_dedup_across_frames(self):
        sc = [frame_scope(state=s, raw_state=s, spacing=[{"sel": "x > y", "node": "TabBar", "prop": "rowGap", "value": 2}])
              for s in ("default", "empty", "loading")]
        out = html_audit.render_findings("final-preview.html", sc, self.th)
        self.assertEqual(len(out), 1)
        self.assertIn("같은 값 3곳", out[0].actual)

    def test_fixed_no_clip(self):
        fixed = [{"sel": "cta", "kind": "cta", "top": 700, "bottom": 756, "height": 56, "paddingBottom": 0, "safeH": 0}]
        out = self.judge(fixed=fixed, scrolls=[{"sel": "body", "lastSel": "row", "lastBottom": 740}])
        self.assertEqual(rules_of(out), {"fixed.no-clip"})
        # loading 상태는 보지 않는다
        self.assertEqual(self.judge(state="loading", raw_state="loading", fixed=fixed,
                                    scrolls=[{"sel": "b", "lastSel": "r", "lastBottom": 740}]), [])
        # data-scroll 이 없으면 실패
        self.assertEqual(rules_of(self.judge(fixed=fixed)), {"fixed.no-clip"})

    def test_text_clip(self):
        base = {"sel": "t", "node": "X", "ellipsis": False, "nowrap": False, "ovx": "hidden",
                "sh": 20, "ch": 20, "sw": 10, "cw": 10}
        cases = [
            dict(base, lines=2, clamp="none", sh=80, ch=40),       # 잘리는데 clamp 없음
            dict(base, lines=2, clamp="3"),                        # clamp ≠ data-truncate
            dict(base, lines=1, clamp="none"),                     # 1줄 말줄임 미설정
        ]
        for c in cases:
            self.assertEqual(rules_of(self.judge(truncates=[c])), {"text.clip"}, c)
        ok = dict(base, lines=1, clamp="none", ellipsis=True, nowrap=True, sw=300, cw=200)
        self.assertEqual(self.judge(truncates=[ok]), [])
        self.assertEqual(rules_of(self.judge(untagged=[{"sel": "s", "node": "X", "kind": "ellipsis", "text": "긴 제목"}])),
                         {"text.clip"})
        self.assertEqual(rules_of(self.judge(overflow=[{"sel": "s", "node": "X", "by": "frame", "right": 402,
                                                        "limit": 390, "text": "정하는 중"}])), {"text.clip"})

    def test_safe_area(self):
        low = {"sel": "tab", "kind": "tabbar", "top": 795, "bottom": 844, "height": 49, "paddingBottom": 0, "safeH": 0}
        self.assertEqual(rules_of(self.judge(state="loading", raw_state="loading", fixed=[low])), {"safe-area"})
        inside = dict(low, safeH=34)
        self.assertEqual(self.judge(state="loading", raw_state="loading", fixed=[inside]), [])

    def test_doc_scope_skips_frame_rules(self):
        sc = {"screen": None, "state": None, "taps": [tap(0, 0, 30, 30)], "spacing": [], "truncates": [],
              "untagged": [], "overflow": []}
        out = html_audit.render_findings("rules-preview.html", [sc], self.th)
        self.assertEqual(rules_of(out), {"tap.min"})


# ── 실제 렌더 (playwright 있을 때만) ──────────────────────────────────────
@unittest.skipUnless(_playwright_ready(), "playwright/chromium 없음 — 렌더 테스트 skip")
class RenderIntegrationTest(unittest.TestCase):
    def test_ok_render_passes_and_screenshots(self):
        with tempfile.TemporaryDirectory() as tmp:
            findings, warnings, stats = html_audit.run_audit(str(HTML_OK), render=True, shots_dir=tmp, scale=1)
            shots = sorted(os.listdir(tmp))
        self.assertEqual([f.line() for f in findings], [])
        self.assertEqual(stats["screenshots"], 23)
        self.assertEqual(len(shots), 23)
        self.assertIn("home-default@360.png", shots)
        self.assertIn("create-keyboard.png", shots)

    def test_bad_render_every_rule_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            findings, _, _ = html_audit.run_audit(str(HTML_BAD), render=True, shots_dir=tmp, scale=1)
        missing = (STATIC_RULES | RENDER_RULES) - rules_of(findings)
        self.assertFalse(missing, "실패하지 않은 규칙: {}".format(sorted(missing)))
        by = {(f.rule, f.screen, f.state) for f in findings}
        self.assertIn(("frame.size", "home", "default@360"), by)
        self.assertIn(("safe-area", "create", "default"), by)
        self.assertIn(("fixed.no-clip", "home", "many-items"), by)


if __name__ == "__main__":
    unittest.main()
