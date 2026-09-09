#!/usr/bin/env python3
"""figma_audit.py 단위 테스트.

    python3 -m unittest scripts/tests/test_figma_audit.py
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = TESTS_DIR.parent
FIXTURES = TESTS_DIR / "fixtures"
REPO_ROOT = SCRIPTS_DIR.parent

sys.path.insert(0, str(SCRIPTS_DIR))

import figma_audit  # noqa: E402

SNAPSHOT_OK = FIXTURES / "snapshot_ok.json"
SNAPSHOT_BAD = FIXTURES / "snapshot_bad.json"
RULES = FIXTURES / "design-rules.md"
BRIEF = FIXTURES / "brief.md"
ICONS = FIXTURES / "icons.md"


def audit(snapshot, rules=RULES, brief=BRIEF, icons=ICONS):
    return figma_audit.run_audit(str(snapshot), str(rules),
                                 str(brief) if brief else None,
                                 str(icons) if icons else None)


def keys_of(findings):
    return {f.key for f in findings}


class ThresholdParsingTest(unittest.TestCase):
    """design-rules.md 표에서 기준값을 뽑아내는지."""

    def setUp(self):
        rules, warnings = figma_audit.parse_rules_file(str(RULES))
        self.rules = rules
        self.th = figma_audit.Thresholds(rules, warnings)

    def test_table_rows_parsed(self):
        self.assertEqual(self.rules["color.accent"], "#2563EB")
        self.assertIn("space.scale", self.rules)
        self.assertIn("layer.order", self.rules)

    def test_numeric_thresholds(self):
        self.assertEqual(self.th.space_step, 4)
        self.assertEqual(self.th.icon_sizes, [16, 20, 24])
        self.assertEqual(self.th.tap_min, 44)
        self.assertEqual(self.th.tap_gap, 8)
        self.assertEqual((self.th.frame_w, self.th.frame_h), (390, 844))
        self.assertEqual(self.th.alt_widths, [360, 390, 430])
        self.assertEqual((self.th.safe_top, self.th.safe_bottom), (44, 34))
        self.assertEqual(self.th.button_heights, [36, 44, 52])
        self.assertEqual(self.th.button_states,
                         ["default", "pressed", "selected", "disabled", "loading"])
        self.assertEqual(self.th.z_scale["snackbar"], 600)
        self.assertGreater(self.th.z_scale["snackbar"], self.th.z_scale["dialog"])

    def test_missing_rules_fall_back_to_defaults_with_warning(self):
        warnings = []
        th = figma_audit.Thresholds({}, warnings)
        self.assertEqual(th.space_step, 4)
        self.assertEqual(th.icon_sizes, [16, 20, 24])
        self.assertEqual(th.tap_min, 44)
        self.assertEqual((th.frame_w, th.frame_h), (390, 844))
        self.assertTrue(any("기본값으로 대체" in w for w in warnings))


class BriefAndIconsParsingTest(unittest.TestCase):
    def test_brief_screen_list(self):
        screens, warnings = figma_audit.parse_brief_screens(str(BRIEF))
        self.assertEqual(screens, ["Home", "Detail"])
        self.assertEqual(warnings, [])

    def test_missing_brief_warns(self):
        screens, warnings = figma_audit.parse_brief_screens(str(FIXTURES / "nope.md"))
        self.assertIsNone(screens)
        self.assertTrue(warnings)

    def test_icon_allowlist(self):
        allow, warnings = figma_audit.parse_icon_allowlist(str(ICONS))
        self.assertEqual(warnings, [])
        self.assertIn("chevron-left", allow)
        self.assertIn("image-off", allow)
        self.assertNotIn("lucide 이름", allow)
        self.assertNotIn("sparkles-custom", allow)


class SnapshotOkTest(unittest.TestCase):
    """정상 스냅샷은 결함 0건이어야 한다."""

    def test_no_findings(self):
        findings, warnings, stats = audit(SNAPSHOT_OK)
        self.assertEqual([f.line() for f in findings], [])
        self.assertEqual(warnings, [])
        self.assertEqual(stats["screenFrames"], 15)   # 7상태 × 2화면 + @360 검증 프레임

    def test_screens_inferred_without_brief(self):
        findings, _, stats = audit(SNAPSHOT_OK, brief=None)
        self.assertEqual(stats["screens"], ["Detail", "Home"])
        self.assertEqual(findings, [])

    def test_icon_allowlist_skipped_without_icons_file(self):
        findings, warnings, stats = audit(SNAPSHOT_OK, icons=None)
        self.assertEqual(stats["iconAllowlist"], 0)
        self.assertEqual(findings, [])


class SnapshotBadTest(unittest.TestCase):
    """결함 스냅샷은 서로 다른 규칙 키 10개 이상을 잡아야 한다."""

    EXPECTED_KEYS = {
        "palette.bound",
        "typo.style",
        "space.grid",
        "component.reuse",
        "naming.default",
        "variant.coverage",
        "state.frames",
        "button.primary-per-screen",
        "tap.min",
        "tap.gap",
        "safe-area",
        "device.frame",
        "icon.sizes",
        "icon.allowlist",
        "icon.set",
        "icon.size-by-text",
        "button.row-rule",
        "layer.order",
    }

    @classmethod
    def setUpClass(cls):
        cls.findings, cls.warnings, cls.stats = audit(SNAPSHOT_BAD)
        cls.keys = keys_of(cls.findings)

    def test_at_least_ten_distinct_rules_fail(self):
        self.assertGreaterEqual(len(self.keys), 10, sorted(self.keys))

    def test_every_expected_rule_fails(self):
        self.assertEqual(self.EXPECTED_KEYS - self.keys, set())

    def test_no_unexpected_rule_keys(self):
        self.assertEqual(self.keys - self.EXPECTED_KEYS, set())

    def test_output_line_format(self):
        for f in self.findings:
            line = f.line()
            self.assertTrue(line.startswith("[FAIL] "), line)
            self.assertIn("(", line)
            self.assertIn("→", line)

    def test_findings_are_sorted_deterministically(self):
        again, _, _ = audit(SNAPSHOT_BAD)
        self.assertEqual([f.line() for f in self.findings], [f.line() for f in again])

    def test_palette_points_at_unbound_fill(self):
        hits = [f for f in self.findings if f.key == "palette.bound"]
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].node_id, "S:Home:default:card")
        self.assertIn("미바인딩", hits[0].actual)

    def test_reuse_ratio_below_threshold(self):
        hits = [f for f in self.findings if f.key == "component.reuse"]
        self.assertEqual(len(hits), 1)
        self.assertIn("≥ 90%", hits[0].expected)

    def test_state_frame_reports_missing_state(self):
        hits = [f for f in self.findings if f.key == "state.frames"]
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].frame, "Detail")
        self.assertIn("text-120", hits[0].actual)

    def test_variant_coverage_reports_missing_loading(self):
        hits = [f for f in self.findings if f.key == "variant.coverage"]
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].node_name, "Button")
        self.assertNotIn("loading", hits[0].actual)

    def test_icon_size_by_text_uses_sibling_font_size(self):
        hits = {f.node_id: f for f in self.findings if f.key == "icon.size-by-text"}
        self.assertIn("S:Home:default:capicon", hits)
        self.assertIn("아이콘 16", hits["S:Home:default:capicon"].expected)

    def test_icon_set_flags_hand_drawn_vector(self):
        hits = [f for f in self.findings if f.key == "icon.set"]
        self.assertEqual(len(hits), 1)
        self.assertIn("VECTOR", hits[0].actual)

    def test_layer_order_flags_snackbar_below_tabbar(self):
        hits = [f for f in self.findings if f.key == "layer.order"]
        self.assertEqual(len(hits), 1)
        self.assertIn("Snackbar", hits[0].actual)


class FixListTest(unittest.TestCase):
    def test_fix_list_markdown_table(self):
        findings, _, _ = audit(SNAPSHOT_BAD)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fix-list.md"
            figma_audit.write_fix_list(str(path), findings)
            text = path.read_text(encoding="utf-8")
        self.assertIn("| 화면 | 노드 ID | 규칙 키 | 현재값 → 기대값 |", text)
        self.assertIn("|---|---|---|---|", text)
        rows = [ln for ln in text.splitlines() if ln.startswith("| ") and "노드 ID" not in ln]
        self.assertEqual(len(rows), len(findings))
        self.assertIn("palette.bound", text)

    def test_fix_list_for_clean_snapshot(self):
        findings, _, _ = audit(SNAPSHOT_OK)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fix-list.md"
            figma_audit.write_fix_list(str(path), findings)
            text = path.read_text(encoding="utf-8")
        self.assertIn("| (없음) | - | - | - |", text)


class CliTest(unittest.TestCase):
    """종료 코드 0/1/2 와 --json 출력."""

    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "figma_audit.py"), *args],
            capture_output=True, text=True, cwd=str(REPO_ROOT))

    def test_exit_zero_on_clean_snapshot(self):
        proc = self.run_cli("--snapshot", str(SNAPSHOT_OK), "--rules", str(RULES),
                            "--brief", str(BRIEF), "--icons", str(ICONS))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("A단계 통과", proc.stdout)

    def test_exit_one_on_findings(self):
        proc = self.run_cli("--snapshot", str(SNAPSHOT_BAD), "--rules", str(RULES),
                            "--brief", str(BRIEF), "--icons", str(ICONS))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("[FAIL]", proc.stdout)

    def test_exit_two_on_missing_snapshot(self):
        proc = self.run_cli("--snapshot", str(FIXTURES / "nope.json"), "--rules", str(RULES))
        self.assertEqual(proc.returncode, 2)
        self.assertIn("[ERROR]", proc.stderr)

    def test_exit_two_on_broken_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "broken.json"
            path.write_text("{ not json", encoding="utf-8")
            proc = self.run_cli("--snapshot", str(path), "--rules", str(RULES))
        self.assertEqual(proc.returncode, 2)

    def test_exit_two_on_wrong_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "shape.json"
            path.write_text(json.dumps({"nope": 1}), encoding="utf-8")
            proc = self.run_cli("--snapshot", str(path), "--rules", str(RULES))
        self.assertEqual(proc.returncode, 2)
        self.assertIn("pages", proc.stderr)

    def test_json_output(self):
        proc = self.run_cli("--snapshot", str(SNAPSHOT_BAD), "--rules", str(RULES),
                            "--brief", str(BRIEF), "--icons", str(ICONS), "--json")
        self.assertEqual(proc.returncode, 1)
        payload = json.loads(proc.stdout)
        self.assertFalse(payload["ok"])
        self.assertGreaterEqual(len(payload["failureCountByRule"]), 10)
        self.assertEqual(len(payload["findings"]),
                         sum(payload["failureCountByRule"].values()))
        for item in payload["findings"]:
            self.assertEqual(
                set(item), {"page", "frame", "node", "nodeId", "rule", "actual", "expected"})

    def test_missing_rules_file_warns_but_still_runs(self):
        proc = self.run_cli("--snapshot", str(SNAPSHOT_OK),
                            "--rules", str(FIXTURES / "nope.md"))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("[WARN]", proc.stdout)

    def test_fix_list_written_by_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fix-list.md"
            proc = self.run_cli("--snapshot", str(SNAPSHOT_BAD), "--rules", str(RULES),
                                "--brief", str(BRIEF), "--icons", str(ICONS),
                                "--fix-list", str(path))
            self.assertEqual(proc.returncode, 1)
            self.assertIn("규칙 키", path.read_text(encoding="utf-8"))


class SnapshotShapeTest(unittest.TestCase):
    """픽스처가 figma_snapshot.js 스키마를 지키는지 (REST로 만든 JSON 호환성 확인용)."""

    REQUIRED_NODE_FIELDS = {
        "id", "name", "type", "parentId", "pageName", "depth", "childIndex",
        "x", "y", "width", "height", "visible", "layoutMode",
        "paddingTop", "paddingRight", "paddingBottom", "paddingLeft", "itemSpacing",
        "fills", "strokes", "cornerRadius", "textStyleId", "fontSize", "characters",
        "boundVariables", "isInstance", "mainComponentName", "componentPropertyValues",
        "hasLabel", "insideIconComponent",
    }

    def test_fixture_nodes_have_schema_fields(self):
        for path in (SNAPSHOT_OK, SNAPSHOT_BAD):
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(
                [p["name"] for p in data["pages"]],
                ["01 Tokens", "02 Components", "03 Screens"], path.name)
            for page in data["pages"]:
                for node in page["nodes"]:
                    self.assertEqual(self.REQUIRED_NODE_FIELDS - set(node), set(),
                                     "{} / {}".format(path.name, node.get("id")))

    def test_snapshot_js_documents_the_same_fields(self):
        source = (SCRIPTS_DIR / "figma_snapshot.js").read_text(encoding="utf-8")
        header = source.split("*/", 1)[0]
        for field in self.REQUIRED_NODE_FIELDS:
            self.assertIn('"{}"'.format(field), header, field)


if __name__ == "__main__":
    unittest.main()


class ComponentManifestTest(unittest.TestCase):
    SCREENS = FIXTURES / "screens.md"
    SCREENS_BAD = FIXTURES / "screens_bad.md"

    def test_manifest_parsed(self):
        manifest, warnings = figma_audit.parse_screens_manifest(str(self.SCREENS))
        self.assertEqual(manifest["home"], ["AppBar", "Card", "Button", "TabBar"])
        self.assertEqual(manifest["detail"], manifest["Detail".lower()])
        self.assertEqual(warnings, [])

    def test_ok_snapshot_matches_manifest(self):
        findings, _, stats = figma_audit.run_audit(
            str(SNAPSHOT_OK), str(RULES), str(BRIEF), str(ICONS), str(self.SCREENS))
        self.assertNotIn("component.manifest", keys_of(findings))
        self.assertEqual(stats["manifestScreens"], 2)

    def test_bad_manifest_reports_missing_extra_and_unlisted_screen(self):
        findings, _, _ = figma_audit.run_audit(
            str(SNAPSHOT_OK), str(RULES), str(BRIEF), str(ICONS), str(self.SCREENS_BAD))
        msgs = [f.actual for f in findings if f.key == "component.manifest"]
        self.assertTrue(any("BottomCTA 없음" in m for m in msgs), msgs)
        self.assertTrue(any("Button (구성표 밖)" in m for m in msgs), msgs)
        self.assertTrue(any("screens.md에 없는 화면" in m for m in msgs), msgs)

    def test_cli_accepts_screens_flag(self):
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "figma_audit.py"),
             "--snapshot", str(SNAPSHOT_OK), "--rules", str(RULES),
             "--screens", str(self.SCREENS_BAD), "--json"],
            capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("component.manifest", proc.stdout)
