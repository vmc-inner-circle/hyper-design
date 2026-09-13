#!/usr/bin/env python3
"""figma_parity.py — "Figma 생성" 뒤 이름·개수 일치(parity) 검사.

`scripts/figma_parity.js` 가 `use_figma` 로 수집한 JSON(이름만)을
design-rules.md · icons.md · screens.md 에서 만든 기대 목록과 대조한다.
전수 스냅샷(figma_snapshot.js + figma_audit.py)과 달리 노드 속성은 보지 않는다.

    python3 scripts/figma_parity.py --actual design/figma-parity.json \
        --rules design/design-rules.md --icons design/icons.md --screens design/screens.md \
        [--states default,empty,loading] [--json]

종료 코드: 0 일치 / 1 불일치 / 2 실행 오류(파일 없음·JSON 형식 불일치)

출력 한 줄 형식
    [FAIL] <분류>/<이름> <규칙 키>: 현재 → 기대

기대 목록
    variables     design-rules §A: color.<n> → color/<n>, space.scale → space/<v>, space.<n> → space/<n>,
                  radius → radius/<n>   (초과 검사는 color·space·radius 컬렉션만. 'web-' 이름은 부모 웹 변형으로 허용)
    textStyles    type.roles → Text/<role>   ('Text/web-*' 초과는 허용)
    effectStyles  shadow → Shadow/<n>
    components    screens.md 컴포넌트 목록 + icons.md 허용 목록 → Icon/<name>
                  + §B 에 값이 있는 button.* → Button, icon-button.* → IconButton, thumbnail.* → Thumbnail
                  ('_' '.' 로 시작하는 비공개 컴포넌트는 초과에서 제외. 같은 이름 2개 이상 = 중복)
    screenFrames  screens.md 화면명 × --states → '<화면명>/<state>' (기본 default 만. 상태 프레임은 기본 생략)
                  + 크기 device.frame(390×844, '@360' 은 360×844)
"""

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import figma_audit  # noqa: E402
import html_audit  # noqa: E402

VAR_COLLECTIONS_CHECKED = ("color", "space", "radius")
ALLOWED_EXTRA_PREFIX = "web-"
FRAME_NAME_RE = re.compile(r"^(?P<screen>.+?)/(?P<state>[a-z0-9][a-z0-9-]*)(?:@(?P<width>\d+))?$")


class Finding:
    __slots__ = ("rule", "kind", "name", "actual", "expected")

    def __init__(self, rule, kind, name, actual, expected):
        self.rule, self.kind, self.name = rule, kind, name
        self.actual, self.expected = str(actual), str(expected)

    def line(self):
        return "[FAIL] {}/{} {}: {} → {}".format(self.kind, self.name, self.rule, self.actual, self.expected)

    def as_dict(self):
        return {"rule": self.rule, "kind": self.kind, "name": self.name,
                "actual": self.actual, "expected": self.expected}


def _norm(name):
    return re.sub(r"\s*/\s*", "/", (name or "").strip()).lower()


# ── 기대 목록 ─────────────────────────────────────────────────────────────
def expected_variables(rules):
    """{'color/bg': 'color.bg', 'space/16': 'space.scale', …}"""
    out = {}
    for key, value in rules.items():
        if key.startswith("color."):
            out["color/" + key[6:]] = key
        elif key == "space.scale":
            for n in figma_audit._ints(value, 1, 512):
                out["space/{}".format(n)] = key
        elif key.startswith("space."):
            out["space/" + key[6:]] = key
        elif key == "radius":
            for name, _ in re.findall(r"\b([a-z][a-z0-9-]*)\s+(\d+)\b", value.split(".")[0]):
                out["radius/" + name] = key
    return out


def expected_text_styles(rules):
    roles = re.findall(r"\b([a-z][a-z0-9-]*)\s+\d+\s*/\s*\d+", rules.get("type.roles", ""))
    return {"Text/" + r: "type.roles" for r in roles}


def expected_effect_styles(rules):
    names = re.findall(r"\b([a-z][a-z0-9-]*)\s+(?:-?[\d.]+(?:px)?\s+){1,4}(?:rgba?|hsla?)\(", rules.get("shadow", ""))
    return {"Shadow/" + n: "shadow" for n in names}


def expected_components(rules, allow, rows, component_list):
    out = {}
    names = component_list or {c for r in rows for c in r["comps"]}
    for n in sorted(names):
        out[n] = "screens.md 컴포넌트 목록"
    for prefix, comp in (("button.", "Button"), ("icon-button.", "IconButton"), ("thumbnail.", "Thumbnail")):
        if any(k.startswith(prefix) for k in rules):
            out.setdefault(comp, "design-rules §B {}*".format(prefix))
    for icon in sorted(allow or ()):
        out["Icon/" + icon] = "icons.md"
    return out


def expected_frames(rows, states):
    out = {}
    for r in rows:
        if not r["name"]:
            continue
        for st in states:
            out["{}/{}".format(r["name"], st)] = r["slug"] or r["name"]
    return out


# ── 대조 ──────────────────────────────────────────────────────────────────
def _diff(kind, rule, expected, actual_names, findings, allow_extra=lambda n: False):
    """expected: {정규 이름: 출처}, actual_names: [원 이름] → 빠짐·초과·중복."""
    exp_norm = {_norm(k): (k, src) for k, src in expected.items()}
    counts = Counter(_norm(n) for n in actual_names)
    shown = {}
    for n in actual_names:
        shown.setdefault(_norm(n), n)
    for key, (name, src) in sorted(exp_norm.items()):
        if counts.get(key, 0) == 0:
            findings.append(Finding(rule, kind, name, "없음", "있어야 함 ({})".format(src)))
    for key, cnt in sorted(counts.items()):
        name = shown[key]
        if key not in exp_norm:
            if allow_extra(name):
                continue
            findings.append(Finding(rule, kind, name, "초과", "기대 목록에 없음 — 지우거나 규칙 문서에 추가"))
        elif cnt > 1:
            findings.append(Finding(rule, kind, name, "{}개".format(cnt), "1개 (중복)"))


def run_parity(actual_path, rules_path, icons_path=None, screens_path=None, states=None):
    data = json.loads(Path(actual_path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("screenFrames"), list):
        raise ValueError("parity JSON 형식이 아닙니다: 최상위에 'screenFrames' 배열 등이 필요합니다 (figma_parity.js 결과).")
    if not os.path.isfile(rules_path):
        raise FileNotFoundError(rules_path)
    rules, warnings = figma_audit.parse_rules_file(rules_path)
    th = figma_audit.Thresholds(rules, warnings)

    allow = None
    if icons_path:
        allow, w = figma_audit.parse_icon_allowlist(icons_path)
        warnings.extend(w)
    rows, component_list = [], None
    if screens_path:
        rows, component_list, w = html_audit.parse_screens_md(screens_path)
        warnings.extend(w)
    states = states or ["default"]

    findings = []

    # variables
    exp_vars = expected_variables(rules)
    actual_vars = []
    other = Counter()
    for v in data.get("variables") or []:
        coll = (v.get("collection") or "").strip()
        name = (v.get("name") or "").strip()
        full = name if name.lower().startswith(coll.lower() + "/") else "{}/{}".format(coll, name)
        if coll.lower() in VAR_COLLECTIONS_CHECKED:
            actual_vars.append(full)
        else:
            other[coll or "(없음)"] += 1
    if other:
        warnings.append("초과 검사 대상이 아닌 변수 컬렉션: " + ", ".join(
            "{} {}개".format(k, v) for k, v in sorted(other.items())))
    _diff("variables", "parity.variables", exp_vars, actual_vars, findings,
          allow_extra=lambda n: n.split("/")[-1].startswith(ALLOWED_EXTRA_PREFIX))

    # styles
    _diff("textStyles", "parity.text-styles", expected_text_styles(rules), data.get("textStyles") or [], findings,
          allow_extra=lambda n: _norm(n).startswith("text/" + ALLOWED_EXTRA_PREFIX))
    _diff("effectStyles", "parity.effect-styles", expected_effect_styles(rules),
          data.get("effectStyles") or [], findings)

    # components
    exp_comps = expected_components(rules, allow, rows, component_list)
    actual_comps = list(data.get("componentSets") or []) + list(data.get("components") or [])
    _diff("components", "parity.components", exp_comps, actual_comps, findings,
          allow_extra=lambda n: n.strip().startswith(("_", ".")))

    # screen frames
    exp_frames = expected_frames(rows, states) if rows else {}
    if not rows:
        warnings.append("screens.md 가 없거나 비어 있어 screenFrames 는 크기만 검사합니다.")
    frame_names = []
    unmatched = 0
    known_screens = {r["name"] for r in rows}
    for fr in data.get("screenFrames") or []:
        name = (fr.get("name") or "").strip()
        m = FRAME_NAME_RE.match(name)
        if not m:
            unmatched += 1
            continue
        frame_names.append(name)
        width = int(m.group("width")) if m.group("width") else th.frame_w
        w, h = fr.get("w"), fr.get("h")
        if isinstance(w, (int, float)) and isinstance(h, (int, float)):
            if round(w) != width or round(h) != th.frame_h:
                findings.append(Finding("parity.frame-size", "screenFrames", name,
                                        "{}×{}".format(round(w), round(h)), "{}×{}".format(width, th.frame_h)))
    if unmatched:
        warnings.append("'<화면>/<상태>' 형식이 아닌 03 Screens 최상위 노드 {}개는 무시했습니다 (라벨·메모 등).".format(unmatched))
    if rows:
        for name in frame_names:
            screen = FRAME_NAME_RE.match(name).group("screen")
            if screen not in known_screens:
                findings.append(Finding("parity.screens", "screenFrames", name,
                                        "screens.md 에 없는 화면", "screens.md 화면명과 같은 이름"))
        _diff("screenFrames", "parity.screens", exp_frames,
              [n for n in frame_names if FRAME_NAME_RE.match(n).group("screen") in known_screens],
              findings)

    for err in data.get("errors") or []:
        warnings.append("수집 경고: {}".format(err))
    if data.get("truncated"):
        warnings.append("수집 결과가 상한에 걸려 잘렸습니다 (figma_parity.js MAX_ITEMS).")

    findings.sort(key=lambda f: (f.rule, f.kind, f.name))
    stats = {
        "file": data.get("file"),
        "expected": {"variables": len(exp_vars), "textStyles": len(expected_text_styles(rules)),
                     "effectStyles": len(expected_effect_styles(rules)), "components": len(exp_comps),
                     "screenFrames": len(exp_frames)},
        "actual": {"variables": len(data.get("variables") or []), "textStyles": len(data.get("textStyles") or []),
                   "effectStyles": len(data.get("effectStyles") or []), "components": len(actual_comps),
                   "screenFrames": len(data.get("screenFrames") or [])},
        "states": states,
    }
    return findings, warnings, stats


def main(argv=None):
    parser = argparse.ArgumentParser(prog="figma_parity.py",
                                     description="figma_parity.js 결과를 규칙 문서와 이름·개수로 대조한다.")
    parser.add_argument("--actual", required=True, help="figma_parity.js 결과 JSON")
    parser.add_argument("--rules", required=True, help="design/design-rules.md")
    parser.add_argument("--icons", help="design/icons.md")
    parser.add_argument("--screens", help="design/screens.md")
    parser.add_argument("--states", help="기대 상태 프레임 (쉼표 구분, 기본 default)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    states = [s.strip() for s in args.states.split(",") if s.strip()] if args.states else None
    try:
        findings, warnings, stats = run_parity(args.actual, args.rules, args.icons, args.screens, states)
    except FileNotFoundError as exc:
        print("[ERROR] 파일을 찾을 수 없습니다: {}".format(exc), file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print("[ERROR] parity JSON 파싱 실패: {}".format(exc), file=sys.stderr)
        return 2
    except (ValueError, OSError) as exc:
        print("[ERROR] {}".format(exc), file=sys.stderr)
        return 2

    by_rule = Counter(f.rule for f in findings)
    if args.json:
        print(json.dumps({"ok": not findings, "stats": stats, "failureCountByRule": dict(by_rule),
                          "findings": [f.as_dict() for f in findings], "warnings": warnings},
                         ensure_ascii=False, indent=2))
    else:
        for w in warnings:
            print("[WARN] {}".format(w))
        for f in findings:
            print(f.line())
        print("")
        e, a = stats["expected"], stats["actual"]
        print("기대 변수 {} / 텍스트 스타일 {} / 이펙트 {} / 컴포넌트 {} / 화면 프레임 {} — 실패 {}건".format(
            e["variables"], e["textStyles"], e["effectStyles"], e["components"], e["screenFrames"], len(findings)))
        if findings:
            print("규칙별 실패: " + ", ".join("{} {}".format(k, v) for k, v in sorted(by_rule.items())))
        else:
            print("parity 통과.")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
