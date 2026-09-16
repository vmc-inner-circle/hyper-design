#!/usr/bin/env python3
"""
check_phase.py에 대한 unittest.
`python3 -m unittest discover scripts/tests` 로 실행한다.
"""
import os
import subprocess
import sys
import unittest

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
DESIGN_OK = os.path.join(FIXTURES_DIR, "design_ok")
DESIGN_BAD = os.path.join(FIXTURES_DIR, "design_bad")
SCRIPT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "check_phase.py")

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import check_phase as cp  # noqa: E402


def run_cli(phase, design_dir, extra=None):
    cmd = [sys.executable, SCRIPT, "--phase", phase, "--design-dir", design_dir]
    if extra:
        cmd += extra
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


class CliExitCodeTests(unittest.TestCase):
    def test_ok_fixture_all_passes(self):
        code, out, _ = run_cli("all", DESIGN_OK)
        self.assertEqual(code, 0, out)
        self.assertNotIn("[FAIL]", out)

    def test_bad_fixture_all_fails(self):
        code, out, _ = run_cli("all", DESIGN_BAD)
        self.assertEqual(code, 1)
        self.assertIn("[FAIL]", out)

    def test_bad_fixture_has_at_least_8_distinct_failures(self):
        code, out, _ = run_cli("all", DESIGN_BAD, extra=["--json"])
        import json

        data = json.loads(out)
        fail_names = {r["name"] for r in data["results"] if not r["ok"]}
        self.assertGreaterEqual(
            len(fail_names), 8, f"실패 종류가 8개 미만: {fail_names}"
        )

    def test_missing_design_dir_exit_code_2(self):
        code, out, _ = run_cli("structure", os.path.join(FIXTURES_DIR, "does_not_exist"))
        self.assertEqual(code, 2)

    def test_missing_design_dir_all_exit_code_2(self):
        code, out, _ = run_cli("all", os.path.join(FIXTURES_DIR, "does_not_exist"))
        self.assertEqual(code, 2)
        self.assertIn("[SKIP]", out)

    def test_json_output_shape(self):
        code, out, _ = run_cli("structure", DESIGN_OK, extra=["--json"])
        import json

        data = json.loads(out)
        self.assertIn("phase", data)
        self.assertIn("passed", data)
        self.assertIn("results", data)
        self.assertIsInstance(data["results"], list)
        for r in data["results"]:
            self.assertIn("name", r)
            self.assertIn("ok", r)
            self.assertIn("file", r)
            self.assertIn("detail", r)

    def test_all_skips_missing_phase_but_continues(self):
        # rules/probes만 있는 임시 디렉터리를 만들어 structure/flow/taste가 SKIP 되는지 확인.
        import shutil
        import tempfile

        tmp = tempfile.mkdtemp()
        try:
            os.makedirs(os.path.join(tmp, "probes"))
            shutil.copy(
                os.path.join(DESIGN_OK, "design-rules.md"), os.path.join(tmp, "design-rules.md")
            )
            shutil.copy(
                os.path.join(DESIGN_OK, "probes", "taste-1-2.html"),
                os.path.join(tmp, "probes", "taste-1-2.html"),
            )
            code, out, _ = run_cli("all", tmp)
            self.assertIn("[SKIP] structure", out)
            self.assertIn("[SKIP] flow", out)
            self.assertIn("[SKIP] taste", out)
            self.assertEqual(code, 0)
        finally:
            shutil.rmtree(tmp)


class StateTokenTests(unittest.TestCase):
    """상태 셀 파싱 — 표기가 흔들려도 같은 결과가 나와야 한다."""

    def test_parenthetical_negation_is_not_counted(self):
        # "해당없음" 설명을 세면 안 쓰는 상태까지 쓰는 것으로 잡힌다
        self.assertEqual(cp.state_tokens("empty (error·disabled 해당없음)"), ["empty"])

    def test_empty_markers_are_dropped(self):
        for marker in ("-", "—", "없음", "N/A", "none", ""):
            self.assertEqual(cp.state_tokens(marker), [], marker)

    def test_separator_variants_give_same_tokens(self):
        expected = ["empty", "error"]
        for cell in ("empty·error", "empty, error", "empty / error",
                     "empty\nerror", "EMPTY·Error"):
            self.assertEqual(cp.state_tokens(cell), expected, cell)

    def test_substring_does_not_match(self):
        # 부분 문자열 매칭이면 'nonempty' 가 'empty' 로 잡힌다
        self.assertEqual(cp.state_tokens("nonempty"), ["nonempty"])

    def test_legacy_korean_names_are_detected(self):
        self.assertEqual(cp.state_tokens("빈·실패"), ["빈", "실패"])
        self.assertEqual(cp.LEGACY_STATE_ALIASES["빈"], "empty")


class StateLanguageTests(unittest.TestCase):
    """상태명 영어 고정 — 한글 문서가 조용히 통과하면 안 된다."""

    def test_korean_state_names_fail_with_english_hint(self):
        results = cp.check_structure(DESIGN_BAD)
        hits = [r for r in results if not r.ok and r.name == "structure:screens-state-lang"]
        self.assertTrue(hits)
        self.assertIn("빈→empty", " ".join(h.detail for h in hits))

    def test_korean_names_still_judged_for_layer(self):
        """한글이라고 층위 검사를 건너뛰지 않는다 ('로딩'도 loading 으로 잡힌다)."""
        results = cp.check_structure(DESIGN_BAD)
        msgs = " ".join(r.detail for r in results
                        if not r.ok and r.name == "structure:screens-state-layer")
        self.assertIn("loading", msgs)

    def test_unknown_state_is_rejected(self):
        results = cp.check_structure(DESIGN_BAD)
        names = [r.name for r in results if not r.ok]
        self.assertIn("structure:screens-state-unknown", names)


class StructureUnitTests(unittest.TestCase):
    def test_ok_fixture_structure_passes(self):
        results = cp.check_structure(DESIGN_OK)
        self.assertTrue(all(r.ok for r in results))

    def test_bad_fixture_detects_multi_value_primary_action(self):
        results = cp.check_structure(DESIGN_BAD)
        names = [r.name for r in results if not r.ok]
        self.assertIn("structure:screens-primary-single", names)

    def test_bad_fixture_detects_missing_state(self):
        results = cp.check_structure(DESIGN_BAD)
        names = [r.name for r in results if not r.ok]
        self.assertIn("structure:screens-state-layer", names)   # loading
        self.assertIn("structure:screens-state-cap", names)     # 허용 상태 3개 > 상한 2
        self.assertIn("structure:screens-state-lang", names)    # 한글 표기

    def test_bad_fixture_detects_unselected_platform(self):
        results = cp.check_structure(DESIGN_BAD)
        names = [r.name for r in results if not r.ok]
        self.assertIn("structure:platform", names)

    def test_missing_file_returns_none(self):
        self.assertIsNone(cp.check_structure(os.path.join(FIXTURES_DIR, "nope")))


class FlowUnitTests(unittest.TestCase):
    def test_ok_fixture_flow_passes(self):
        results = cp.check_flow(DESIGN_OK)
        self.assertTrue(all(r.ok for r in results))

    def test_bad_fixture_detects_step_count(self):
        results = cp.check_flow(DESIGN_BAD)
        names = [r.name for r in results if not r.ok]
        self.assertIn("flow:scenario-steps-count", names)

    def test_bad_fixture_detects_missing_label(self):
        results = cp.check_flow(DESIGN_BAD)
        names = [r.name for r in results if not r.ok]
        self.assertIn("flow:scenario-step-label", names)

    def test_bad_fixture_detects_missing_cta_line(self):
        results = cp.check_flow(DESIGN_BAD)
        names = [r.name for r in results if not r.ok]
        self.assertIn("flow:cta-line", names)


class TasteUnitTests(unittest.TestCase):
    def test_ok_fixture_taste_passes(self):
        results = cp.check_taste(DESIGN_OK)
        self.assertTrue(all(r.ok for r in results))

    def test_bad_fixture_detects_placeholder_best(self):
        results = cp.check_taste(DESIGN_BAD)
        names = [r.name for r in results if not r.ok]
        self.assertIn("taste:axis-best", names)

    def test_bad_fixture_detects_unlogged_unknown(self):
        results = cp.check_taste(DESIGN_BAD)
        names = [r.name for r in results if not r.ok]
        self.assertIn("taste:axis-unknown-logged", names)

    def test_bad_fixture_detects_missing_selected_value(self):
        results = cp.check_taste(DESIGN_BAD)
        names = [r.name for r in results if not r.ok]
        self.assertIn("taste:axis-selected-value", names)


class RulesUnitTests(unittest.TestCase):
    def test_ok_fixture_rules_passes(self):
        results = cp.check_rules(DESIGN_OK)
        self.assertTrue(all(r.ok for r in results))

    def test_bad_fixture_detects_status_not_confirmed(self):
        results = cp.check_rules(DESIGN_BAD)
        names = [r.name for r in results if not r.ok]
        self.assertIn("rules:status", names)

    def test_bad_fixture_detects_bad_color(self):
        results = cp.check_rules(DESIGN_BAD)
        names = [r.name for r in results if not r.ok]
        self.assertIn("rules:A-value-format", names)

    def test_bad_fixture_detects_missing_source_stage(self):
        results = cp.check_rules(DESIGN_BAD)
        names = [r.name for r in results if not r.ok]
        self.assertIn("rules:source-stage-mark", names)

    def test_validators_directly(self):
        self.assertTrue(cp.validate_color_value("#112233"))
        self.assertTrue(cp.validate_color_value("rgba(0,0,0,.5) 하나만"))
        self.assertTrue(cp.validate_color_value("accent를 12% 어둡게"))
        self.assertFalse(cp.validate_color_value("blue"))

        self.assertTrue(cp.validate_space_scale("4 / 8 / 12 / 16 / 24 / 32 / 48"))
        self.assertFalse(cp.validate_space_scale("4 / 15"))

        self.assertTrue(cp.validate_icon_sizes("16 / 20 / 24"))
        self.assertFalse(cp.validate_icon_sizes("16 / 18 / 24"))

        self.assertTrue(cp.validate_tap_min("44×44"))
        self.assertFalse(cp.validate_tap_min("40×40"))

        self.assertTrue(cp.validate_device_frame("390×844 기준"))
        self.assertFalse(cp.validate_device_frame("375×812 기준"))

        self.assertTrue(cp.validate_zscale_ascending("0 100 200 200 300"))
        self.assertFalse(cp.validate_zscale_ascending("0 100 50 300"))

        self.assertTrue(cp.validate_button_sizes("sm 36h / md 44h / lg 52h"))
        self.assertFalse(cp.validate_button_sizes("sm 36h / md 40h / lg 52h"))


class ProbesUnitTests(unittest.TestCase):
    def test_ok_fixture_probes_passes(self):
        results = cp.check_probes(DESIGN_OK)
        self.assertTrue(all(r.ok for r in results))

    def test_bad_fixture_detects_external_script(self):
        results = cp.check_probes(DESIGN_BAD)
        names = [r.name for r in results if not r.ok]
        self.assertIn("probes:no-external-script", names)

    def test_bad_fixture_detects_lorem_ipsum(self):
        results = cp.check_probes(DESIGN_BAD)
        names = [r.name for r in results if not r.ok]
        self.assertIn("probes:no-lorem-ipsum", names)

    def test_bad_fixture_detects_axis_count(self):
        results = cp.check_probes(DESIGN_BAD)
        names = [r.name for r in results if not r.ok]
        self.assertIn("probes:axis-section-count", names)

    def test_missing_probes_dir_returns_none(self):
        import shutil
        import tempfile

        tmp = tempfile.mkdtemp()
        try:
            self.assertIsNone(cp.check_probes(tmp))
        finally:
            shutil.rmtree(tmp)


class MarkdownParsingUnitTests(unittest.TestCase):
    def test_parse_tables_basic(self):
        text = """
| a | b |
|---|---|
| 1 | 2 |
| 3 | 4 |
"""
        tables = cp.parse_tables(text)
        self.assertEqual(len(tables), 1)
        self.assertEqual(tables[0]["header"], ["a", "b"])
        self.assertEqual(tables[0]["rows"], [["1", "2"], ["3", "4"]])

    def test_split_sections(self):
        text = "# Title\n\n## A\ntext a\n\n## B\ntext b\n"
        sections = cp.split_sections(text)
        titles = [s["title"] for s in sections]
        self.assertIn("A", titles)
        self.assertIn("B", titles)


if __name__ == "__main__":
    unittest.main()
