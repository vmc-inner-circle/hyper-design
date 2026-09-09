#!/usr/bin/env python3
"""figma_audit.py — Figma A단계(구조적 사실) 검사기.

`scripts/figma_snapshot.js` 가 만든 스냅샷 JSON을 읽어
`design/design-rules.md` 의 기준값으로 검사하고 결함 목록을 낸다.

    python3 scripts/figma_audit.py \
        --snapshot design/figma-snapshot.json \
        --rules    design/design-rules.md \
        [--brief   design/brief.md] \
        [--icons   design/icons.md] \
        [--json] [--fix-list design/fix-list.md]

종료 코드
    0  결함 없음
    1  결함 있음
    2  실행 오류 (파일 없음, JSON 파싱 실패, 스냅샷 형식 불일치 등)

출력 한 줄 형식
    [FAIL] <페이지>/<프레임> <노드명>(<id>) <규칙 키>: 현재 → 기대

스냅샷 형식은 figma_snapshot.js 상단 주석의 스키마를 따른다.
같은 형식이면 REST API로 만든 JSON도 그대로 통과한다.

Python 3.11 표준 라이브러리만 사용한다.
"""

import argparse
import json
import re
import sys
from pathlib import Path

# ── 규칙 파싱 실패 시 쓰는 기본값 ─────────────────────────────────────────
# 출처: .claude/skills/oss-design-harness/references/design-rules.md
DEFAULT_RULES = {
    "space.scale": "4 / 8 / 12 / 16 / 24 / 32 / 48 (4 배수만 허용)",
    "icon.sizes": "16 (인라인·캡션) / 20 (버튼·목록) / 24 (앱바·탭바). 세 값 외 금지",
    "tap.min": "44×44. 인접 탭 영역 간격 최소 8",
    "device.frame": "390×844 기준. 검증 폭 360 / 390 / 430",
    "safe-area": "상단 상태바 44(노치 기기 47) · 하단 홈 인디케이터 34",
    "z.scale": ("base 0 · sticky 100 · app-bar 200 · tab-bar 200 · overlay 300 · "
                "sheet 400 · dialog 500 · snackbar 600"),
    "button.sizes": "sm 36h / px12 / text14 · md 44h / px16 / text15 · lg 52h / px20 / text16",
    "button.states": "default · pressed · selected · disabled · loading",
    "icon.set": "lucide 단일. 다른 세트 혼용 금지",
}

# 규칙 표에 수치가 없는 값들 (design-auditor.md A단계 표에서 직접 온 상수)
REUSE_THRESHOLD = 0.90                      # 컴포넌트 재사용률 하한
SCREEN_STATES = ["default", "empty", "loading", "error",
                 "long-title", "many-items", "text-120"]
THUMBNAIL_STATES = ["default", "pressed", "selected"]
VARIANT_TARGETS = ["Button", "IconButton", "Thumbnail"]
# AI가 직접 그린 아이콘 탐지 대상 (icon.set)
RAW_VECTOR_TYPES = {"VECTOR", "BOOLEAN_OPERATION", "STAR", "POLYGON"}
# 아이콘 크기 ↔ 옆 텍스트 크기 대응 (icon.size-by-text)
ICON_SIZE_BY_FONT = [((12, 13), 16), ((14, 15), 20), ((17, 10 ** 6), 24)]

DEFAULT_NAME_RE = re.compile(
    r"^(Frame|Rectangle|Group|Ellipse|Vector|Line|Polygon|Star|Slice|Section|"
    r"Component|Instance|Union|Subtract|Intersect|Exclude)(\s+\d+)?$"
)
DEFAULT_NAME_EXACT = {"Text", "Image", "Arrow"}

TOKENS_PAGE = "01 Tokens"
COMPONENTS_PAGE = "02 Components"
SCREENS_PAGE = "03 Screens"

LABEL_PREFIX = "_label"
ICON_PREFIX = "Icon/"

# 레이어 순서 등급 (클수록 위에 있어야 함)
LAYER_RANK = [
    ("Snackbar", 4),
    ("Dialog", 3),
    ("BottomSheet", 2),
    ("TabBar", 1),
    ("AppBar", 1),
]


# ── 결함 ──────────────────────────────────────────────────────────────────
class Finding:
    """검사 실패 1건."""

    __slots__ = ("page", "frame", "node_name", "node_id", "key", "actual", "expected")

    def __init__(self, page, frame, node_name, node_id, key, actual, expected):
        self.page = page or "-"
        self.frame = frame or "-"
        self.node_name = node_name or "-"
        self.node_id = node_id or "-"
        self.key = key
        self.actual = str(actual)
        self.expected = str(expected)

    def line(self):
        return "[FAIL] {}/{} {}({}) {}: {} → {}".format(
            self.page, self.frame, self.node_name, self.node_id,
            self.key, self.actual, self.expected)

    def as_dict(self):
        return {
            "page": self.page, "frame": self.frame,
            "node": self.node_name, "nodeId": self.node_id,
            "rule": self.key, "actual": self.actual, "expected": self.expected,
        }

    def sort_key(self):
        return (self.key, self.page, self.frame, self.node_name, self.node_id)


# ── design-rules.md 파싱 ──────────────────────────────────────────────────
_ROW_RE = re.compile(r"^\|(.+)\|\s*$")
_KEY_RE = re.compile(r"^[a-z][a-z0-9]*(?:[.\-][a-z0-9]+)*$")


def parse_rules_file(path):
    """마크다운 표에서 `키 → 값` 을 읽는다. (rules, warnings) 반환."""
    warnings = []
    rules = {}
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        warnings.append("design-rules.md를 읽지 못했습니다 ({}). 기본값을 사용합니다.".format(exc))
        return {}, warnings

    for raw in text.splitlines():
        m = _ROW_RE.match(raw.strip())
        if not m:
            continue
        cells = [c.strip() for c in m.group(1).split("|")]
        if len(cells) < 2:
            continue
        key, value = cells[0], cells[1]
        if not _KEY_RE.match(key):
            continue
        if set(value) <= set("- :"):      # 표 구분선
            continue
        if not value:
            continue
        rules[key] = value
    if not rules:
        warnings.append("design-rules.md에서 표를 찾지 못했습니다. 전부 기본값을 사용합니다.")
    return rules, warnings


def _ints(text, lo=0, hi=10000):
    return [int(n) for n in re.findall(r"\d+", text or "") if lo <= int(n) <= hi]


class Thresholds:
    """design-rules.md 값에서 뽑아낸 검사 기준값."""

    def __init__(self, rules, warnings):
        self.warnings = warnings
        self.raw = {}

        def get(key):
            value = rules.get(key)
            if not value:
                self.warnings.append(
                    "규칙 '{}' 파싱 실패 — references/design-rules.md 기본값으로 대체합니다.".format(key))
                value = DEFAULT_RULES.get(key, "")
            self.raw[key] = value
            return value

        # space.scale → 그리드 배수 (스케일 값들의 최솟값)
        scale = _ints(get("space.scale"), 1, 512)
        self.space_step = min(scale) if scale else 4
        self.space_scale = sorted(set(scale)) or [4, 8, 12, 16, 24, 32, 48]

        # icon.sizes → 허용 크기 집합
        sizes = _ints(get("icon.sizes"), 8, 96)
        self.icon_sizes = sorted(set(sizes)) or [16, 20, 24]

        # tap.min → 최소 탭 크기 / 인접 간격
        tap = get("tap.min")
        tap_nums = _ints(tap, 1, 200)
        self.tap_min = tap_nums[0] if tap_nums else 44
        gap_m = re.search(r"간격[^\d]*(\d+)", tap)
        self.tap_gap = int(gap_m.group(1)) if gap_m else (tap_nums[-1] if len(tap_nums) > 1 else 8)

        # device.frame → 기준 크기 + 검증 폭
        dev = get("device.frame")
        pair = re.search(r"(\d+)\s*[×xX]\s*(\d+)", dev)
        self.frame_w, self.frame_h = (int(pair.group(1)), int(pair.group(2))) if pair else (390, 844)
        widths = set(_ints(dev, 200, 1200)) - {self.frame_h}
        widths.add(self.frame_w)
        self.alt_widths = sorted(widths)

        # safe-area → 상단 / 하단
        sa = get("safe-area")
        top = re.search(r"상단[^\d]*(\d+)", sa)
        bottom = re.search(r"하단[^\d]*(\d+)", sa)
        sa_nums = _ints(sa, 1, 200)
        self.safe_top = int(top.group(1)) if top else (sa_nums[0] if sa_nums else 44)
        self.safe_bottom = int(bottom.group(1)) if bottom else (sa_nums[-1] if sa_nums else 34)

        # z.scale → 레이어 이름별 z 값
        self.z_scale = {k: int(v) for k, v in re.findall(r"([a-z][a-z\-]*)\s+(\d+)", get("z.scale"))}

        # button.sizes → 허용 높이
        bs = get("button.sizes")
        heights = [int(n) for n in re.findall(r"(\d+)\s*h", bs)]
        self.button_heights = sorted(set(heights)) or [36, 44, 52]

        # button.states → variant 커버리지 기대값
        states = re.findall(r"\b(default|pressed|selected|disabled|loading)\b", get("button.states"))
        seen, ordered = set(), []
        for s in states:
            if s not in seen:
                seen.add(s)
                ordered.append(s)
        self.button_states = ordered or ["default", "pressed", "selected", "disabled", "loading"]
        self.thumbnail_states = [s for s in THUMBNAIL_STATES if s in self.button_states] or THUMBNAIL_STATES


# ── brief.md 화면 목록 파싱 ───────────────────────────────────────────────
def parse_brief_screens(path):
    """brief.md §1 화면 목록 표의 첫 열을 화면 이름으로 읽는다."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        return None, ["brief.md를 읽지 못했습니다 ({}). 스냅샷에서 화면 목록을 추론합니다.".format(exc)]

    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if re.match(r"^#{1,6}\s*1\.?\s*화면 목록", line.strip()):
            start = i + 1
            break
    if start is None:
        return None, ["brief.md에서 '1. 화면 목록' 절을 찾지 못했습니다. 스냅샷에서 추론합니다."]

    screens, header_seen = [], False
    for line in lines[start:]:
        stripped = line.strip()
        if stripped.startswith("#"):
            break
        m = _ROW_RE.match(stripped)
        if not m:
            if screens:
                break
            continue
        cells = [c.strip() for c in m.group(1).split("|")]
        first = cells[0] if cells else ""
        if not header_seen:
            header_seen = True
            continue                                   # 표 머리행
        if not first or set(first) <= set("- :"):
            continue                                   # 구분선 / 빈 템플릿 행
        if first.startswith("<") or first == "화면":
            continue
        screens.append(first)
    if not screens:
        return None, ["brief.md 화면 목록 표가 비어 있습니다. 스냅샷에서 추론합니다."]
    return screens, []


# ── icons.md 허용 목록 파싱 ───────────────────────────────────────────────
def parse_icon_allowlist(path):
    """icons.md 표의 'lucide 이름' 열을 허용 목록으로 읽는다."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        return None, ["icons.md를 읽지 못했습니다 ({}). icon.allowlist 검사를 건너뜁니다.".format(exc)]

    allow, col = set(), None
    for raw in text.splitlines():
        stripped = raw.strip()
        if stripped.startswith("#") and col is not None:
            break                                      # 허용 목록 표가 끝났다 (예: '## 제외 목록')
        m = _ROW_RE.match(stripped)
        if not m:
            continue
        cells = [c.strip() for c in m.group(1).split("|")]
        if col is None:
            for i, c in enumerate(cells):
                if "lucide" in c.lower():
                    col = i
                    break
            continue                                   # 머리행은 값으로 쓰지 않는다
        if col >= len(cells):
            continue
        value = cells[col]
        if not value or set(value) <= set("- :"):
            continue
        for name in re.split(r"[,/]", value):
            name = name.strip().strip("`")
            if name and _KEY_RE.match(name.lower()):
                allow.add(name.lower())
    if col is None:
        return None, ["icons.md에서 'lucide 이름' 열을 찾지 못했습니다. icon.allowlist 검사를 건너뜁니다."]
    if not allow:
        return None, ["icons.md의 'lucide 이름' 열이 비어 있습니다. icon.allowlist 검사를 건너뜁니다."]
    return allow, []


# ── 스냅샷 모델 ───────────────────────────────────────────────────────────
class Snapshot:
    def __init__(self, data):
        if not isinstance(data, dict) or not isinstance(data.get("pages"), list):
            raise ValueError("스냅샷 형식이 아닙니다: 최상위에 'pages' 배열이 필요합니다.")
        self.data = data
        self.nodes = []
        self.by_id = {}
        self.children = {}
        for page in data["pages"]:
            page_name = page.get("name", "?")
            for node in page.get("nodes", []) or []:
                node.setdefault("pageName", page_name)
                self.nodes.append(node)
        for node in self.nodes:
            self.by_id[node.get("id")] = node
        for node in self.nodes:
            self.children.setdefault(node.get("parentId"), []).append(node)
        for kids in self.children.values():
            kids.sort(key=lambda n: (n.get("childIndex") or 0, n.get("id") or ""))

    def page_nodes(self, page_name):
        return [n for n in self.nodes if n.get("pageName") == page_name]

    def parent(self, node):
        return self.by_id.get(node.get("parentId"))

    def descendants(self, node):
        out, stack = [], list(self.children.get(node.get("id"), []))
        while stack:
            cur = stack.pop()
            out.append(cur)
            stack.extend(self.children.get(cur.get("id"), []))
        return out

    def ancestors(self, node):
        out, cur = [], self.parent(node)
        while cur is not None:
            out.append(cur)
            cur = self.parent(cur)
        return out


def is_label(node):
    return (node.get("name") or "").startswith(LABEL_PREFIX)


def in_label(snap, node):
    return is_label(node) or any(is_label(a) for a in snap.ancestors(node))


SCREEN_FRAME_RE = re.compile(r"^(?P<screen>[^/]+)/(?P<state>[a-z0-9][a-z0-9\-]*)(?:@(?P<width>\d+))?$")


def screen_frames(snap):
    """03 Screens 페이지의 최상위 화면 프레임 목록. [(node, screen, state, forced_width)]"""
    out = []
    for node in snap.page_nodes(SCREENS_PAGE):
        if node.get("depth") != 0:
            continue
        if node.get("type") not in ("FRAME", "COMPONENT"):
            continue
        m = SCREEN_FRAME_RE.match(node.get("name") or "")
        if not m:
            continue
        width = int(m.group("width")) if m.group("width") else None
        out.append((node, m.group("screen"), m.group("state"), width))
    return out


def owning_frame(snap, node, frame_ids):
    """노드가 속한 화면 프레임 이름을 찾는다."""
    if node.get("id") in frame_ids:
        return node.get("name")
    for anc in snap.ancestors(node):
        if anc.get("id") in frame_ids:
            return anc.get("name")
    return None


def component_kind(node):
    """노드가 어떤 컴포넌트의 인스턴스인지 (mainComponentName 우선, 없으면 name)."""
    name = node.get("mainComponentName") or node.get("name") or ""
    return name.split("/")[0].split(",")[0].strip()


def icon_base_name(node):
    """'Icon/chevron-left' → 'chevron-left'. 아이콘이 아니면 None."""
    for candidate in (node.get("name") or "", node.get("mainComponentName") or ""):
        if candidate.startswith(ICON_PREFIX):
            rest = candidate[len(ICON_PREFIX):].strip()
            rest = re.split(r"[\s,]", rest)[0]
            if "=" in rest:
                return None                            # variant 표기(size=24)는 아이콘 이름이 아니다
            return rest.lower() or None
    return None


def parse_screens_manifest(path):
    """design/screens.md 의 구성표를 읽는다. {화면명 또는 slug(소문자): [컴포넌트명, ...]}"""
    text = Path(path).read_text(encoding="utf-8")
    manifest, warnings = {}, []
    header = None
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if header is None:
            if "구성" in "".join(cells):
                header = cells
            continue
        if set(line) <= set("|-: "):
            continue
        row = dict(zip(header, cells))
        comp_cell = next((v for k, v in row.items() if "구성" in k), "")
        screen = row.get("화면") or ""
        slug = row.get("slug") or ""
        if not comp_cell or not (screen or slug):
            continue
        comps = []
        for part in re.split(r"[·,]", comp_cell):
            part = re.sub(r"^[\s①-⑳⓪-⓿]+", "", part).strip()
            name = re.split(r"[\s(×xX*]", part)[0].strip()
            if name and name.lower() not in ("icon",):
                comps.append(name)
        if not comps:
            continue
        for key in (screen, slug):
            if key:
                manifest[key.lower()] = comps
    if not manifest:
        warnings.append("screens.md에서 구성표를 읽지 못했습니다 ('구성' 열이 있는 표 필요). component.manifest 검사를 건너뜁니다.")
    return manifest, warnings


MANIFEST_IGNORE = {"DeviceFrame", "Icon", "Skeleton"}


def check_component_manifest(snap, manifest, findings):
    """`<화면>/default` 프레임의 최상위 인스턴스가 screens.md 구성표와 일치해야 한다 (빠짐 0, 표 밖 0)."""
    if not manifest:
        return
    for node, screen, state, width in screen_frames(snap):
        if state != "default" or width:
            continue
        expected = manifest.get(screen.lower())
        if expected is None:
            findings.append(Finding(
                SCREENS_PAGE, node.get("name"), node.get("name"), node.get("id"),
                "component.manifest", "screens.md에 없는 화면", "screens.md 구성표에 행 추가"))
            continue
        found = []
        for desc in snap.descendants(node):
            if not desc.get("isInstance") or in_label(snap, desc):
                continue
            nested = any(a.get("isInstance") for a in snap.ancestors(desc) if a.get("id") != node.get("id"))
            if nested:
                continue
            kind = component_kind(desc)
            if kind in MANIFEST_IGNORE or kind.startswith("_"):
                continue
            found.append((kind, desc))
        found_kinds = {k for k, _ in found}
        expected_kinds = set(expected)
        for missing in sorted(expected_kinds - found_kinds):
            findings.append(Finding(
                SCREENS_PAGE, node.get("name"), node.get("name"), node.get("id"),
                "component.manifest", "{} 없음".format(missing), "screens.md 구성대로 {} 인스턴스 배치".format(missing)))
        for kind, desc in found:
            if kind not in expected_kinds:
                findings.append(Finding(
                    SCREENS_PAGE, node.get("name"), desc.get("name"), desc.get("id"),
                    "component.manifest", "{} (구성표 밖)".format(kind), "제거하거나 screens.md에 추가 후 사용자 확인"))


def numeric(value):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None


# ── 개별 검사 ─────────────────────────────────────────────────────────────
def check_palette(snap, th, frame_ids, findings):
    """03 Screens 의 모든 SOLID fill/stroke 가 색 변수에 바인딩되어야 한다."""
    for node in snap.page_nodes(SCREENS_PAGE):
        if in_label(snap, node):
            continue
        for kind, paints in (("fill", node.get("fills") or []), ("stroke", node.get("strokes") or [])):
            for paint in paints:
                if paint.get("type") != "SOLID" or paint.get("visible") is False:
                    continue
                if paint.get("boundVariable"):
                    continue
                findings.append(Finding(
                    SCREENS_PAGE, owning_frame(snap, node, frame_ids),
                    node.get("name"), node.get("id"), "palette.bound",
                    "{} {} 미바인딩".format(kind, paint.get("hex") or "?"),
                    "color 변수 바인딩"))


def check_typography(snap, frame_ids, findings):
    """모든 TEXT 노드에 텍스트 스타일이 적용되어야 한다."""
    for node in snap.page_nodes(SCREENS_PAGE):
        if node.get("type") != "TEXT" or in_label(snap, node):
            continue
        style_id = node.get("textStyleId")
        if style_id and style_id != "MIXED":
            continue
        findings.append(Finding(
            SCREENS_PAGE, owning_frame(snap, node, frame_ids),
            node.get("name"), node.get("id"), "typo.style",
            "textStyleId {}".format("MIXED" if style_id == "MIXED" else "없음"),
            "Text/* 스타일 적용"))


def off_grid(value, step):
    """소수점이 있거나 step 배수가 아니면 True."""
    return abs(value - round(value)) > 1e-6 or round(value) % step != 0


def check_spacing(snap, th, frame_ids, findings):
    """padding·itemSpacing·(오토레이아웃 밖 자식의) x·y 가 그리드 배수여야 한다."""
    step = th.space_step
    for node in snap.page_nodes(SCREENS_PAGE):
        if in_label(snap, node):
            continue
        frame = owning_frame(snap, node, frame_ids)
        props = ["paddingTop", "paddingRight", "paddingBottom", "paddingLeft", "itemSpacing"]

        parent = snap.parent(node)
        # 페이지 직속(=화면 프레임 자체)이거나 부모가 오토레이아웃이면 x·y 는 저자가 정하지 않는다.
        if parent is not None and (parent.get("layoutMode") or "NONE") == "NONE":
            props += ["x", "y"]

        for prop in props:
            value = numeric(node.get(prop))
            if value is None or not off_grid(value, step):
                continue
            findings.append(Finding(
                SCREENS_PAGE, frame, node.get("name"), node.get("id"), "space.grid",
                "{} {:g}".format(prop, value), "{} 배수".format(step)))


def check_component_reuse(snap, frame_ids, findings):
    """03 Screens 컴포넌트 재사용률 ≥ 90%.

    분자 = 인스턴스 수, 분모 = 인스턴스 + 로컬 FRAME.
    최상위 화면 프레임, `_label` 주석, 인스턴스 내부 노드는 양쪽에서 제외한다
    (인스턴스 내부는 컴포넌트가 소유하므로 화면 저자의 선택이 아니다).
    """
    instances = local_frames = 0
    for node in snap.page_nodes(SCREENS_PAGE):
        if node.get("id") in frame_ids or in_label(snap, node):
            continue
        if any(a.get("isInstance") for a in snap.ancestors(node)):
            continue
        if node.get("isInstance"):
            instances += 1
        elif node.get("type") == "FRAME":
            local_frames += 1
    total = instances + local_frames
    if total == 0:
        return
    ratio = instances / total
    if ratio < REUSE_THRESHOLD:
        findings.append(Finding(
            SCREENS_PAGE, "-", "03 Screens 전체", "-", "component.reuse",
            "{:.0%} (인스턴스 {} / 전체 {})".format(ratio, instances, total),
            "≥ {:.0%}".format(REUSE_THRESHOLD)))


def check_naming(snap, frame_ids, findings):
    """`Frame 12`, `Rectangle 3`, `Text` 같은 Figma 기본 레이어명은 0개여야 한다."""
    for page in (COMPONENTS_PAGE, SCREENS_PAGE):
        for node in snap.page_nodes(page):
            if in_label(snap, node):
                continue
            name = (node.get("name") or "").strip()
            if not name:
                bad = True
            else:
                bad = bool(DEFAULT_NAME_RE.match(name)) or name in DEFAULT_NAME_EXACT
            if bad:
                findings.append(Finding(
                    page, owning_frame(snap, node, frame_ids),
                    name or "(이름 없음)", node.get("id"), "naming.default",
                    name or "(이름 없음)", "역할이 드러나는 이름"))


def check_variant_coverage(snap, th, findings):
    """02 Components 의 Button·IconButton·Thumbnail 이 state 값을 전부 가져야 한다."""
    expected = {
        "Button": th.button_states,
        "IconButton": th.button_states,
        "Thumbnail": th.thumbnail_states,
    }
    comp_nodes = snap.page_nodes(COMPONENTS_PAGE)
    sets_by_name = {}
    for node in comp_nodes:
        if node.get("type") == "COMPONENT_SET":
            sets_by_name.setdefault((node.get("name") or "").strip(), node)

    for target in VARIANT_TARGETS:
        node = sets_by_name.get(target)
        if node is None:
            findings.append(Finding(
                COMPONENTS_PAGE, "-", target, "-", "variant.coverage",
                "컴포넌트 세트 없음", "state " + "/".join(expected[target])))
            continue
        found = set()
        for child in snap.children.get(node.get("id"), []):
            if child.get("type") != "COMPONENT":
                continue
            value = (child.get("componentPropertyValues") or {}).get("state")
            if value:
                found.add(str(value).strip().lower())
        missing = [s for s in expected[target] if s not in found]
        if missing:
            findings.append(Finding(
                COMPONENTS_PAGE, "-", target, node.get("id"), "variant.coverage",
                "state " + ("/".join(sorted(found)) if found else "없음"),
                "state " + "/".join(expected[target])))


def check_state_frames(snap, screens, findings):
    """화면마다 상태 프레임 7개가 있어야 한다."""
    present = {}
    for node, screen, state, width in screen_frames(snap):
        if width:
            continue                                    # @360/@430 검증 프레임은 상태 목록에서 제외
        present.setdefault(screen, set()).add(state)
    for screen in screens:
        found = present.get(screen, set())
        missing = [s for s in SCREEN_STATES if s not in found]
        if missing:
            findings.append(Finding(
                SCREENS_PAGE, screen, screen, "-", "state.frames",
                "누락 " + "/".join(missing),
                "/".join(SCREEN_STATES) + " 7개"))


def check_primary_count(snap, findings):
    """`<화면>/default` 프레임 안에 variant=primary 인 Button 인스턴스가 정확히 1개."""
    for node, screen, state, width in screen_frames(snap):
        if state != "default" or width:
            continue
        count = 0
        for desc in snap.descendants(node):
            if not desc.get("isInstance") or in_label(snap, desc):
                continue
            if component_kind(desc) != "Button":
                continue
            variant = (desc.get("componentPropertyValues") or {}).get("variant")
            if variant and str(variant).strip().lower() == "primary":
                count += 1
        if count != 1:
            findings.append(Finding(
                SCREENS_PAGE, node.get("name"), node.get("name"), node.get("id"),
                "button.primary-per-screen", "{}개".format(count), "정확히 1개"))


TAPPABLE_KINDS = {"Button", "IconButton", "Thumbnail"}


def is_tappable(node):
    if not node.get("isInstance"):
        return False
    kind = component_kind(node)
    if kind in TAPPABLE_KINDS:
        return True
    # TabBar 안의 탭 항목 (이름이 Tab 으로 시작)
    return (node.get("name") or "").startswith("Tab") and kind not in ("TabBar",)


def check_tap_targets(snap, th, frame_ids, findings):
    """탭 가능한 인스턴스는 44×44 이상, 형제 간 간격 8 이상."""
    tappables = [n for n in snap.page_nodes(SCREENS_PAGE)
                 if is_tappable(n) and not in_label(snap, n)]

    for node in tappables:
        w, h = numeric(node.get("width")), numeric(node.get("height"))
        if w is None or h is None:
            continue
        if w < th.tap_min or h < th.tap_min:
            findings.append(Finding(
                SCREENS_PAGE, owning_frame(snap, node, frame_ids),
                node.get("name"), node.get("id"), "tap.min",
                "{:g}×{:g}".format(w, h),
                "≥ {}×{}".format(th.tap_min, th.tap_min)))

    by_parent = {}
    for node in tappables:
        by_parent.setdefault(node.get("parentId"), []).append(node)

    for parent_id, siblings in by_parent.items():
        if len(siblings) < 2:
            continue
        parent = snap.by_id.get(parent_id)
        layout = (parent or {}).get("layoutMode") or "NONE"
        if layout in ("HORIZONTAL", "VERTICAL"):
            gap = numeric((parent or {}).get("itemSpacing"))
            if gap is not None and gap < th.tap_gap:
                findings.append(Finding(
                    SCREENS_PAGE, owning_frame(snap, parent, frame_ids),
                    parent.get("name"), parent.get("id"), "tap.gap",
                    "itemSpacing {:g}".format(gap), "≥ {}".format(th.tap_gap)))
            continue
        ordered = sorted(siblings, key=lambda n: (numeric(n.get("x")) or 0, numeric(n.get("y")) or 0))
        for a, b in zip(ordered, ordered[1:]):
            ax, ay = numeric(a.get("x")), numeric(a.get("y"))
            bx, by = numeric(b.get("x")), numeric(b.get("y"))
            aw, ah = numeric(a.get("width")), numeric(a.get("height"))
            bw, bh = numeric(b.get("width")), numeric(b.get("height"))
            if None in (ax, ay, bx, by, aw, ah, bw, bh):
                continue
            gap_x = max(bx - (ax + aw), ax - (bx + bw))
            gap_y = max(by - (ay + ah), ay - (by + bh))
            gap = max(gap_x, gap_y)
            if gap < th.tap_gap:
                findings.append(Finding(
                    SCREENS_PAGE, owning_frame(snap, b, frame_ids),
                    b.get("name"), b.get("id"), "tap.gap",
                    "{} 와 간격 {:g}".format(a.get("name"), gap),
                    "≥ {}".format(th.tap_gap)))


def check_safe_area(snap, th, findings):
    """화면 프레임 직속 자식이 상단 44 / 하단 34 안쪽에 있어야 한다."""
    for node, screen, state, width in screen_frames(snap):
        frame_h = numeric(node.get("height")) or th.frame_h
        limit = frame_h - th.safe_bottom
        for child in snap.children.get(node.get("id"), []):
            name = child.get("name") or ""
            if is_label(child) or name.startswith("DeviceFrame"):
                continue
            if component_kind(child) == "DeviceFrame":
                continue
            y, h = numeric(child.get("y")), numeric(child.get("height"))
            if y is None or h is None:
                continue
            if y < th.safe_top:
                findings.append(Finding(
                    SCREENS_PAGE, node.get("name"), name, child.get("id"), "safe-area",
                    "y {:g}".format(y), "≥ {}".format(th.safe_top)))
            if y + h > limit:
                findings.append(Finding(
                    SCREENS_PAGE, node.get("name"), name, child.get("id"), "safe-area",
                    "하단 {:g}".format(y + h), "≤ {:g}".format(limit)))


FIXED_BAR_PREFIXES = ("BottomCTA", "Slot/BottomCTA", "TabBar", "Slot/TabBar", "DeviceFrame/home", "Slot/DeviceFrame/home")
OVERLAY_PREFIXES = ("BottomSheet", "Slot/BottomSheet", "Sheet", "Dialog", "Slot/Dialog", "Overlay", "Snackbar", "Slot/Snackbar", "Toast")


def _abs_y(snap, node, frame_id):
    """화면 프레임 기준 절대 y. 스냅샷 좌표는 부모 기준이므로 조상 y를 누적한다."""
    y = numeric(node.get("y")) or 0
    cur = snap.parent(node)
    while cur is not None and cur.get("id") != frame_id:
        y += numeric(cur.get("y")) or 0
        cur = snap.parent(cur)
    return y


def check_no_clip(snap, th, findings):
    """fixed.no-clip: 본문 요소가 하단 고정 바(CTA·탭바) 뒤로 잘리면 안 된다.

    스크롤 영역의 마지막 요소 아래 여백 = 고정 바 + safe-area + 16 (scroll.last-item).
    시트·다이얼로그·스낵바처럼 원래 바 위에 겹치는 오버레이는 제외한다.
    """
    for node, screen, state, width in screen_frames(snap):
        fid = node.get("id")
        frame_h = numeric(node.get("height")) or th.frame_h
        bars = []
        for child in snap.children.get(fid, []):
            name = child.get("name") or ""
            if name.startswith(FIXED_BAR_PREFIXES) or component_kind(child) in ("BottomCTA", "TabBar"):
                y = _abs_y(snap, child, fid)
                if y is not None:
                    bars.append(y)
        if not bars:
            continue
        bar_top = min(bars)
        for desc in snap.descendants(node):
            name = desc.get("name") or ""
            if is_label(desc) or desc.get("type") in ("GROUP",):
                continue
            # 고정 바 자신·그 안의 것, 오버레이 계열은 제외
            skip = False
            for anc in [desc] + list(snap.ancestors(desc)):
                an = anc.get("name") or ""
                if anc.get("id") == fid:
                    break
                if an.startswith(FIXED_BAR_PREFIXES) or an.startswith(OVERLAY_PREFIXES) or component_kind(anc) in ("BottomCTA", "TabBar", "BottomSheet", "Dialog", "Snackbar"):
                    skip = True
                    break
            if skip:
                continue
            if desc.get("type") not in ("TEXT", "INSTANCE", "FRAME", "RECTANGLE", "COMPONENT"):
                continue
            h = numeric(desc.get("height"))
            if h is None:
                continue
            # 스크롤 컨테이너(본문) 자체는 바 위에서 끝나면 OK; 그 안의 잎 요소가 넘치면 잘림
            if desc.get("type") == "FRAME" and snap.children.get(desc.get("id")):
                continue
            y = _abs_y(snap, desc, fid)
            bottom = y + h
            if bottom > bar_top + 1 and y < bar_top:
                findings.append(Finding(
                    SCREENS_PAGE, node.get("name"), name, desc.get("id"), "fixed.no-clip",
                    "요소 하단 {:g} > 고정 바 상단 {:g}".format(bottom, bar_top),
                    "본문 마지막 요소는 고정 바 위에서 끝나야 함 (내용이 넘치면 시트로 분리하거나 스크롤 2컷)"))


def check_frame_size(snap, th, findings):
    """화면 프레임은 390×844. 이름에 @360/@430 이 붙은 검증 프레임만 예외."""
    for node, screen, state, width in screen_frames(snap):
        w, h = numeric(node.get("width")), numeric(node.get("height"))
        if w is None or h is None:
            continue
        expected_w = width if width else th.frame_w
        if width and width not in th.alt_widths:
            findings.append(Finding(
                SCREENS_PAGE, node.get("name"), node.get("name"), node.get("id"),
                "device.frame", "검증 폭 @{}".format(width),
                "검증 폭 " + "/".join(str(x) for x in th.alt_widths)))
        if round(w) != expected_w or round(h) != th.frame_h:
            findings.append(Finding(
                SCREENS_PAGE, node.get("name"), node.get("name"), node.get("id"),
                "device.frame", "{:g}×{:g}".format(w, h),
                "{}×{}".format(expected_w, th.frame_h)))


def check_icon_size(snap, th, frame_ids, findings):
    """`Icon/` 인스턴스 크기는 16/20/24 중 하나."""
    allowed = set(th.icon_sizes)
    for node in snap.nodes:
        if not node.get("isInstance"):
            continue
        if not (node.get("name") or "").startswith(ICON_PREFIX) and \
           not (node.get("mainComponentName") or "").startswith(ICON_PREFIX):
            continue
        w, h = numeric(node.get("width")), numeric(node.get("height"))
        if w is None or h is None:
            continue
        if round(w) not in allowed or round(h) not in allowed:
            findings.append(Finding(
                node.get("pageName"), owning_frame(snap, node, frame_ids),
                node.get("name"), node.get("id"), "icon.sizes",
                "{:g}×{:g}".format(w, h),
                "/".join(str(x) for x in th.icon_sizes)))


def check_icon_allowlist(snap, allowlist, frame_ids, findings):
    """`Icon/<name>` 의 <name> 이 icons.md 의 lucide 허용 목록에 있어야 한다."""
    if not allowlist:
        return
    for node in snap.nodes:
        if node.get("type") not in ("COMPONENT", "COMPONENT_SET", "INSTANCE"):
            continue
        name = icon_base_name(node)
        if name is None:
            continue
        if name not in allowlist:
            findings.append(Finding(
                node.get("pageName"), owning_frame(snap, node, frame_ids),
                node.get("name"), node.get("id"), "icon.allowlist",
                "Icon/{}".format(name), "icons.md 의 lucide 이름"))


def check_icon_set(snap, frame_ids, findings):
    """Icon/ 컴포넌트 밖에서 직접 그린 벡터(VECTOR/BOOLEAN_OPERATION/STAR/POLYGON) 금지."""
    for page in (COMPONENTS_PAGE, SCREENS_PAGE):
        for node in snap.page_nodes(page):
            if node.get("type") not in RAW_VECTOR_TYPES:
                continue
            if node.get("insideIconComponent"):
                continue
            if in_label(snap, node):
                continue
            findings.append(Finding(
                page, owning_frame(snap, node, frame_ids),
                node.get("name"), node.get("id"), "icon.set",
                "{} (직접 그린 도형)".format(node.get("type")),
                "lucide Icon/ 컴포넌트 인스턴스"))


def check_icon_size_by_text(snap, frame_ids, findings):
    """오토레이아웃 안에서 TEXT 형제와 나란한 Icon/ 인스턴스는 글자 크기에 맞는 아이콘 크기여야 한다."""
    for node in snap.nodes:
        if not node.get("isInstance"):
            continue
        if not (node.get("name") or "").startswith(ICON_PREFIX) and \
           not (node.get("mainComponentName") or "").startswith(ICON_PREFIX):
            continue
        parent = snap.parent(node)
        if parent is None or (parent.get("layoutMode") or "NONE") == "NONE":
            continue
        font_size = None
        for sib in snap.children.get(parent.get("id"), []):
            if sib.get("id") == node.get("id") or sib.get("type") != "TEXT":
                continue
            fs = numeric(sib.get("fontSize"))
            if fs is not None:
                font_size = fs
                break
        if font_size is None:
            continue
        expected = None
        for (lo, hi), size in ICON_SIZE_BY_FONT:
            if lo <= font_size <= hi:
                expected = size
                break
        if expected is None:
            continue
        w = numeric(node.get("width"))
        if w is None or round(w) == expected:
            continue
        findings.append(Finding(
            node.get("pageName"), owning_frame(snap, node, frame_ids),
            node.get("name"), node.get("id"), "icon.size-by-text",
            "아이콘 {:g} (텍스트 {:g})".format(w, font_size),
            "아이콘 {}".format(expected)))


def check_button_row(snap, frame_ids, findings):
    """같은 오토레이아웃 부모 안의 Button 인스턴스는 height·cornerRadius 가 같아야 한다."""
    by_parent = {}
    for node in snap.page_nodes(SCREENS_PAGE):
        if not node.get("isInstance") or component_kind(node) != "Button":
            continue
        if in_label(snap, node):
            continue
        parent = snap.parent(node)
        if parent is None or (parent.get("layoutMode") or "NONE") == "NONE":
            continue
        by_parent.setdefault(parent.get("id"), []).append(node)

    for parent_id, buttons in by_parent.items():
        if len(buttons) < 2:
            continue
        base = buttons[0]
        base_h = numeric(base.get("height"))
        base_r = base.get("cornerRadius")
        for node in buttons[1:]:
            h = numeric(node.get("height"))
            r = node.get("cornerRadius")
            if base_h is not None and h is not None and round(h) != round(base_h):
                findings.append(Finding(
                    SCREENS_PAGE, owning_frame(snap, node, frame_ids),
                    node.get("name"), node.get("id"), "button.row-rule",
                    "height {:g}".format(h),
                    "{} 와 같은 {:g}".format(base.get("name"), base_h)))
            if r != base_r:
                findings.append(Finding(
                    SCREENS_PAGE, owning_frame(snap, node, frame_ids),
                    node.get("name"), node.get("id"), "button.row-rule",
                    "cornerRadius {}".format(r),
                    "{} 와 같은 {}".format(base.get("name"), base_r)))


def layer_rank(node):
    name = node.get("mainComponentName") or node.get("name") or ""
    for prefix, rank in LAYER_RANK:
        if name.startswith(prefix):
            return prefix, rank
    return None, None


def check_layer_order(snap, findings):
    """같은 화면 안에서 Snackbar > Dialog > BottomSheet > TabBar/AppBar 순으로 위에 있어야 한다."""
    for node, screen, state, width in screen_frames(snap):
        layered = []
        for child in snap.children.get(node.get("id"), []):
            prefix, rank = layer_rank(child)
            if rank is None:
                continue
            layered.append((child, prefix, rank, child.get("childIndex") or 0))
        for a in layered:
            for b in layered:
                if a[2] <= b[2]:
                    continue
                if a[3] < b[3]:
                    findings.append(Finding(
                        SCREENS_PAGE, node.get("name"), a[0].get("name"), a[0].get("id"),
                        "layer.order",
                        "{} 인덱스 {} < {} 인덱스 {}".format(a[1], a[3], b[1], b[3]),
                        "{} 가 {} 보다 위(뒤 인덱스)".format(a[1], b[1])))


# ── 실행 ──────────────────────────────────────────────────────────────────
def run_audit(snapshot_path, rules_path, brief_path=None, icons_path=None, screens_path=None):
    """검사를 수행하고 (findings, warnings, stats) 를 돌려준다."""
    data = json.loads(Path(snapshot_path).read_text(encoding="utf-8"))
    snap = Snapshot(data)

    rules, warnings = parse_rules_file(rules_path)
    th = Thresholds(rules, warnings)

    frames = screen_frames(snap)
    frame_ids = {n.get("id") for n, _, _, _ in frames}

    if brief_path:
        screens, brief_warnings = parse_brief_screens(brief_path)
        warnings.extend(brief_warnings)
    else:
        screens, brief_warnings = None, []
    if not screens:
        screens = sorted({s for _, s, state, _ in frames if state == "default"})
        if not screens:
            warnings.append("03 Screens에서 '<화면>/default' 프레임을 찾지 못해 상태 프레임 검사를 건너뜁니다.")

    allowlist = None
    if icons_path:
        allowlist, icon_warnings = parse_icon_allowlist(icons_path)
        warnings.extend(icon_warnings)

    manifest = None
    if screens_path:
        manifest, manifest_warnings = parse_screens_manifest(screens_path)
        warnings.extend(manifest_warnings)

    findings = []
    check_palette(snap, th, frame_ids, findings)
    check_typography(snap, frame_ids, findings)
    check_spacing(snap, th, frame_ids, findings)
    check_component_reuse(snap, frame_ids, findings)
    check_naming(snap, frame_ids, findings)
    check_variant_coverage(snap, th, findings)
    if screens:
        check_state_frames(snap, screens, findings)
    check_primary_count(snap, findings)
    check_tap_targets(snap, th, frame_ids, findings)
    check_safe_area(snap, th, findings)
    check_no_clip(snap, th, findings)
    check_frame_size(snap, th, findings)
    check_icon_size(snap, th, frame_ids, findings)
    check_icon_allowlist(snap, allowlist, frame_ids, findings)
    check_icon_set(snap, frame_ids, findings)
    check_icon_size_by_text(snap, frame_ids, findings)
    check_button_row(snap, frame_ids, findings)
    check_layer_order(snap, findings)
    check_component_manifest(snap, manifest, findings)

    findings.sort(key=lambda f: f.sort_key())
    if data.get("truncated"):
        warnings.append("스냅샷이 MAX_DEPTH/노드 상한에 걸려 잘렸습니다. 일부 노드는 검사되지 않았습니다.")
    for err in data.get("errors") or []:
        warnings.append("스냅샷 수집 경고: {}".format(err))

    stats = {
        "file": data.get("file"),
        "generatedAt": data.get("generatedAt"),
        "nodes": len(snap.nodes),
        "screenFrames": len(frames),
        "screens": screens or [],
        "iconAllowlist": len(allowlist) if allowlist else 0,
        "manifestScreens": sum(1 for _, sc, st, w in frames if st == "default" and not w and manifest and sc.lower() in manifest),
    }
    return findings, warnings, stats


def write_fix_list(path, findings):
    """figma-builder STAGE=fix 에 그대로 넘길 결함 목록 마크다운."""
    lines = [
        "<!-- figma_audit.py 자동 생성. figma-builder STAGE=fix 입력. 목록에 없는 것은 건드리지 않는다. -->",
        "",
        "# Fix List",
        "",
        "| 화면 | 노드 ID | 규칙 키 | 현재값 → 기대값 |",
        "|---|---|---|---|",
    ]
    for f in findings:
        screen = f.frame if f.frame != "-" else f.page
        cell = "{} — {} → {}".format(f.node_name, f.actual, f.expected)
        lines.append("| {} | {} | {} | {} |".format(
            _md(screen), _md(f.node_id), _md(f.key), _md(cell)))
    if not findings:
        lines.append("| (없음) | - | - | - |")
    lines.append("")
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def _md(text):
    return str(text).replace("|", "\\|").replace("\n", " ")


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="figma_audit.py",
        description="Figma 스냅샷 JSON을 design-rules.md 기준으로 검사한다 (A단계).")
    parser.add_argument("--snapshot", required=True, help="figma_snapshot.js 결과 JSON 경로")
    parser.add_argument("--rules", required=True, help="design/design-rules.md 경로")
    parser.add_argument("--brief", help="design/brief.md 경로 (화면 목록 출처)")
    parser.add_argument("--icons", help="design/icons.md 경로 (lucide 아이콘 허용 목록)")
    parser.add_argument("--screens", help="design/screens.md 경로 (화면별 컴포넌트 구성표)")
    parser.add_argument("--json", action="store_true", help="결과를 JSON으로 출력")
    parser.add_argument("--fix-list", dest="fix_list", help="결함 목록 마크다운 표 저장 경로")
    args = parser.parse_args(argv)

    try:
        findings, warnings, stats = run_audit(
            args.snapshot, args.rules, args.brief, args.icons, args.screens)
    except FileNotFoundError as exc:
        print("[ERROR] 파일을 찾을 수 없습니다: {}".format(exc), file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print("[ERROR] 스냅샷 JSON 파싱 실패: {}".format(exc), file=sys.stderr)
        return 2
    except (ValueError, OSError) as exc:
        print("[ERROR] {}".format(exc), file=sys.stderr)
        return 2

    if args.fix_list:
        try:
            write_fix_list(args.fix_list, findings)
        except OSError as exc:
            print("[ERROR] fix-list 저장 실패: {}".format(exc), file=sys.stderr)
            return 2

    by_rule = {}
    for f in findings:
        by_rule[f.key] = by_rule.get(f.key, 0) + 1

    if args.json:
        print(json.dumps({
            "ok": not findings,
            "stats": stats,
            "warnings": warnings,
            "failureCountByRule": by_rule,
            "findings": [f.as_dict() for f in findings],
        }, ensure_ascii=False, indent=2))
    else:
        for w in warnings:
            print("[WARN] {}".format(w))
        for f in findings:
            print(f.line())
        print("")
        print("검사 노드 {}개 / 화면 프레임 {}개 / 실패 {}건 ({}개 규칙)".format(
            stats["nodes"], stats["screenFrames"], len(findings), len(by_rule)))
        if findings:
            print("규칙별 실패: " + ", ".join(
                "{} {}".format(k, v) for k, v in sorted(by_rule.items())))
        else:
            print("A단계 통과.")

    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
