#!/usr/bin/env python3
"""figma_parity.py 단위 테스트.

    python3 -m unittest scripts/tests/test_figma_parity.py
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
DOCS = FIXTURES / "html_ok"          # design-rules.md · icons.md · screens.md 를 html_audit 픽스처와 공유
PARITY_OK = FIXTURES / "parity_ok.json"
PARITY_BAD = FIXTURES / "parity_bad.json"

sys.path.insert(0, str(SCRIPTS_DIR))

import figma_audit  # noqa: E402
import figma_parity  # noqa: E402


def parity(actual, states=None):
    return figma_parity.run_parity(str(actual), str(DOCS / "design-rules.md"), str(DOCS / "icons.md"),
                                   str(DOCS / "screens.md"), states)


def run_main(argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = figma_parity.main(argv)
    return code, out.getvalue(), err.getvalue()


class ExpectedListTest(unittest.TestCase):
    def setUp(self):
        self.rules, _ = figma_audit.parse_rules_file(str(DOCS / "design-rules.md"))

    def test_variables(self):
        exp = figma_parity.expected_variables(self.rules)
        self.assertIn("color/bg", exp)
        self.assertIn("space/16", exp)
        self.assertIn("space/screen-padding", exp)
        self.assertIn("radius/full", exp)
        self.assertEqual(len(exp), 8 + 8 + 4)

    def test_styles(self):
        self.assertEqual(set(figma_parity.expected_text_styles(self.rules)), {"Text/h3", "Text/body", "Text/caption"})
        self.assertEqual(set(figma_parity.expected_effect_styles(self.rules)), {"Shadow/sm", "Shadow/md"})

    def test_components(self):
        allow, _ = figma_audit.parse_icon_allowlist(str(DOCS / "icons.md"))
        import html_audit
        rows, comp_list, _ = html_audit.parse_screens_md(str(DOCS / "screens.md"))
        exp = figma_parity.expected_components(self.rules, allow, rows, comp_list)
        self.assertIn("Icon/chevron-left", exp)
        self.assertIn("Button", exp)            # §B button.*
        self.assertIn("IconButton", exp)        # §B icon-button.*
        self.assertNotIn("Thumbnail", exp)      # thumbnail.* 값 비어 있음(미사용)
        self.assertEqual(len(exp), 11 + 2 + 12)


class ParityOkTest(unittest.TestCase):
    def test_ok_passes(self):
        findings, warnings, stats = parity(PARITY_OK)
        self.assertEqual([f.line() for f in findings], [])
        self.assertEqual(stats["expected"]["screenFrames"], 3)
        self.assertTrue(any("size 1개" in w for w in warnings))

    def test_states_option_expects_more_frames(self):
        findings, _, stats = parity(PARITY_OK, states=["default", "empty"])
        self.assertEqual(stats["expected"]["screenFrames"], 6)
        missing = {f.name for f in findings if f.rule == "parity.screens"}
        self.assertEqual(missing, {"여행 홈/empty", "여행 만들기/empty", "내 준비 (웹)/empty"})


class ParityBadTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.findings, cls.warnings, cls.stats = parity(PARITY_BAD)
        cls.index = {(f.rule, f.name): f.actual for f in cls.findings}

    def test_every_rule_fails(self):
        self.assertEqual({f.rule for f in self.findings},
                         {"parity.variables", "parity.text-styles", "parity.effect-styles",
                          "parity.components", "parity.screens", "parity.frame-size"})

    def test_missing_and_extra(self):
        self.assertEqual(self.index[("parity.variables", "color/text-muted")], "없음")
        self.assertEqual(self.index[("parity.variables", "color/brand")], "초과")
        self.assertEqual(self.index[("parity.text-styles", "Text/caption")], "없음")
        self.assertEqual(self.index[("parity.text-styles", "Text/Display2")], "초과")
        self.assertEqual(self.index[("parity.effect-styles", "Shadow/md")], "없음")
        self.assertEqual(self.index[("parity.components", "Icon/clock")], "없음")
        self.assertEqual(self.index[("parity.components", "Thumbnail")], "초과")
        self.assertEqual(self.index[("parity.components", "Chip")], "2개")

    def test_frames(self):
        self.assertEqual(self.index[("parity.screens", "내 준비 (웹)/default")], "없음")
        self.assertEqual(self.index[("parity.screens", "여행 홈/empty")], "초과")
        self.assertEqual(self.index[("parity.screens", "설정/default")], "screens.md 에 없는 화면")
        self.assertEqual(self.index[("parity.frame-size", "여행 홈/default")], "375×812")

    def test_allowed_extras_are_not_failures(self):
        names = {f.name for f in self.findings}
        self.assertNotIn("space/web-card-padding", names)
        self.assertNotIn("_Base/cell", names)


class CliTest(unittest.TestCase):
    def args(self, actual, *extra):
        return ["--actual", str(actual), "--rules", str(DOCS / "design-rules.md"), "--icons", str(DOCS / "icons.md"),
                "--screens", str(DOCS / "screens.md")] + list(extra)

    def test_exit_codes(self):
        self.assertEqual(run_main(self.args(PARITY_OK))[0], 0)
        self.assertEqual(run_main(self.args(PARITY_BAD))[0], 1)
        self.assertEqual(run_main(self.args(FIXTURES / "nope.json"))[0], 2)

    def test_bad_json_is_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = os.path.join(tmp, "x.json")
            Path(bad).write_text("{not json", encoding="utf-8")
            self.assertEqual(run_main(self.args(bad))[0], 2)
            Path(bad).write_text('{"pages": []}', encoding="utf-8")      # 스냅샷 형식 ≠ parity 형식
            code, _, err = run_main(self.args(bad))
            self.assertEqual(code, 2)
            self.assertIn("parity JSON 형식", err)

    def test_text_and_json(self):
        code, out, _ = run_main(self.args(PARITY_BAD))
        fails = [l for l in out.splitlines() if l.startswith("[FAIL]")]
        self.assertEqual(len(fails), 12)
        for line in fails:
            self.assertRegex(line, r"^\[FAIL\] \w+/.+ parity\.[a-z\-]+: .+ → .+$")
        code, out, _ = run_main(self.args(PARITY_BAD, "--json"))
        data = json.loads(out)
        self.assertEqual(set(data), {"ok", "stats", "failureCountByRule", "findings", "warnings"})
        self.assertFalse(data["ok"])

    def test_states_flag(self):
        code, out, _ = run_main(self.args(PARITY_OK, "--states", "default,empty"))
        self.assertEqual(code, 1)
        self.assertIn("여행 홈/empty", out)


class ParityScriptTest(unittest.TestCase):
    """figma_parity.js 가 읽기 전용이고 이름만 반환하는지 (정적 확인)."""

    def test_read_only(self):
        import re
        js = (SCRIPTS_DIR / "figma_parity.js").read_text(encoding="utf-8")
        js = re.sub(r"/\*.*?\*/", "", js, flags=re.S)          # 주석(사용법 설명)은 제외
        js = re.sub(r"^\s*//.*$", "", js, flags=re.M)
        for forbidden in ("createFrame", "createComponent", ".remove()", "closePlugin", "setBoundVariable",
                          "appendChild", "console.log("):
            self.assertNotIn(forbidden, js)
        # 노드 속성 대입(n.name = …) 없음 — 비교(===, !==)는 허용
        self.assertIsNone(re.search(r"\b[a-zA-Z]+\.(name|fills|x|y|resize)\s*=(?!=)", js))
        self.assertIn("return JSON.stringify", js)
        for key in ("variables", "textStyles", "effectStyles", "componentSets", "components", "screenFrames"):
            self.assertIn(key + ":", js)


if __name__ == "__main__":
    unittest.main()
