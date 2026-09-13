#!/usr/bin/env python3
"""html_audit.py — HTML A단계(구조적 사실) 검사기.

최종 산출물인 `design/probes/final-preview.html`(화면)과 `design/probes/rules-preview.html`
(토큰·컴포넌트)을 `design/design-rules.md`·`icons.md`·`screens.md` 기준으로 검사한다.

    python3 scripts/html_audit.py --design-dir design \
        [--render] [--json] [--fix-list design/html-fix-list.md] \
        [--screenshots design/screenshots/html] [--scale 2] [--viewport page|device]

종료 코드
    0  결함 없음
    1  결함 있음
    2  실행 오류 (파일 없음, --render 인데 playwright/chromium 없음 등)

출력 한 줄 형식
    [FAIL] <파일>/<화면>/<상태> <노드>(<선택자>) <규칙 키>: 현재 → 기대

정적 검사(항상, 표준 라이브러리만)
    token.bound · token.defined · icon.allowlist · component.manifest · state.frames ·
    button.primary-per-screen · no-lorem · no-external
렌더 검사(--render, playwright 지연 import)
    tap.min · tap.gap · space.grid · fixed.no-clip · text.clip · frame.size · safe-area

--render 를 주면 정적 검사도 **스크립트 실행 후의 DOM**(page.content())으로 돌린다.
마크업을 JS 로 만드는 페이지는 --render 없이는 구조 검사가 "섹션 없음"으로만 나온다.

마크업 계약은 scripts/README.md "HTML A단계" 절에 있다.
"""

import argparse
import bisect
import json
import os
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import check_phase  # noqa: E402  (no-external 판정 _is_external 재사용)
import figma_audit  # noqa: E402  (design-rules.md 파싱·기준값, icons.md 허용 목록 재사용)

# ── 대상·상수 ──────────────────────────────────────────────────────────────
SCREENS_FILE = "final-preview.html"
RULES_FILE = "rules-preview.html"
TARGET_FILES = [SCREENS_FILE, RULES_FILE]

BASE_STATES = ["default", "empty", "loading", "error", "long-title", "many-items", "text-120"]
KEYBOARD_STATE = "keyboard"
KNOWN_STATES = set(BASE_STATES) | {KEYBOARD_STATE, "guest-name", "many-items-scroll", "default-scroll"}
FORM_COMPONENT = "FormField"
# 화면 규칙 — final-preview.html 과 screens.md 가 모두 있을 때만 돈다 (4단계엔 SKIP)
SCREEN_RULES = ["component.manifest", "state.frames", "button.primary-per-screen"]
# fixed.no-clip 을 보는 상태 (스크롤 끝까지 내렸을 때 마지막 요소가 고정 바 위에서 끝나야 한다)
NO_CLIP_STATES = {"default", "many-items", "many-items-scroll", "default-scroll"}

TOKEN_FAMILIES = ("color", "space", "radius", "shadow", "font", "type")
FONT_ALLOWED_HOSTS = ("fonts.googleapis.com", "fonts.gstatic.com")

INSTALL_HINT = (
    "--render 에는 playwright(python)와 chromium 이 필요합니다.\n"
    "  python3 -m venv .venv && .venv/bin/pip install playwright && .venv/bin/playwright install chromium\n"
    "  그 뒤 .venv/bin/python scripts/html_audit.py --design-dir design --render\n"
    "  (브라우저 캐시: ~/Library/Caches/ms-playwright — 버전이 맞는 chromium_headless_shell 이 이미 있으면 설치가 빠르다)"
)


# ── 결함 ──────────────────────────────────────────────────────────────────
class Finding:
    """검사 실패 1건."""

    __slots__ = ("rule", "file", "screen", "state", "node", "selector", "actual", "expected")

    def __init__(self, rule, file, screen, state, node, selector, actual, expected):
        self.rule = rule
        self.file = file or "-"
        self.screen = screen or "-"
        self.state = state or "-"
        self.node = node or "-"
        self.selector = selector or "-"
        self.actual = str(actual)
        self.expected = str(expected)

    def line(self):
        return "[FAIL] {}/{}/{} {}({}) {}: {} → {}".format(
            self.file, self.screen, self.state, self.node, self.selector,
            self.rule, self.actual, self.expected)

    def as_dict(self):
        return {"rule": self.rule, "file": self.file, "screen": self.screen, "state": self.state,
                "node": self.node, "selector": self.selector,
                "actual": self.actual, "expected": self.expected}

    def sort_key(self):
        return (self.rule, self.file, self.screen, self.state, self.node, self.selector, self.actual)


class AuditError(Exception):
    """실행 오류 (종료 코드 2)."""


# ── 마크다운 파싱 ─────────────────────────────────────────────────────────
def _read(path):
    return Path(path).read_text(encoding="utf-8")


_CAMEL_RE = re.compile(r"(?<![A-Za-z0-9])[A-Z][A-Za-z0-9]*")
_STATE_TOKEN_RE = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*")


def strip_parens(text):
    """괄호(중첩 포함)와 따옴표 안 설명을 지운다."""
    s = re.sub(r"\"[^\"]*\"|“[^”]*”|'[^']*'", "", text)
    prev = None
    while prev != s:
        prev = s
        s = re.sub(r"[(（][^()（）]*[)）]", "", s)
    return s


def parse_composition(cell):
    """screens.md 구성 셀 → 컴포넌트명 목록.

    괄호 안 설명을 먼저 지우고 `·`·`+`·`,` 로 나눈 뒤 조각마다 첫 PascalCase 토큰만 취한다.
    (figma_audit 처럼 괄호 안 `·` 를 잘라 '기간' 같은 설명어를 컴포넌트로 읽지 않는다.)
    """
    comps = []
    for part in re.split(r"[·+,]", strip_parens(cell)):
        m = _CAMEL_RE.search(part)
        if m and m.group(0) not in comps:
            comps.append(m.group(0))
    return comps


def parse_state_cell(cell):
    """'default·empty·…·guest-name(누구세요: …)' → ['default', 'empty', …, 'guest-name']"""
    out = []
    for part in re.split(r"[·,/]", strip_parens(cell)):
        m = _STATE_TOKEN_RE.search(part.strip())
        if m and m.group(0) not in out:
            out.append(m.group(0))
    return out


def parse_screens_md(path):
    """design/screens.md → (rows, component_list, warnings).

    rows: [{"name", "slug", "comps", "states"}]. component_list: '컴포넌트 목록' 줄의 이름 집합 또는 None.
    """
    text = _read(path)
    warnings = []
    component_list = None
    rows = []
    header = None
    for raw in text.splitlines():
        line = raw.strip()
        m = re.match(r"^컴포넌트 목록[^:：]*[:：]\s*(.+)$", line)
        if m and component_list is None:
            names = []
            for part in re.split(r"[·,]", m.group(1)):
                cm = _CAMEL_RE.search(part)
                if cm:
                    names.append(cm.group(0))
            component_list = set(names) or None
            continue
        if not line.startswith("|"):
            if header is not None and rows:
                header = None          # 표가 끝났다
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if header is None:
            if any("구성" in c for c in cells):
                header = cells
            continue
        if set(line) <= set("|-: "):
            continue
        row = dict(zip(header, cells))
        comp_cell = next((v for k, v in row.items() if "구성" in k), "")
        state_cell = next((v for k, v in row.items() if "상태" in k), "")
        name = row.get("화면", "").strip()
        slug = row.get("slug", "").strip()
        if not (name or slug):
            continue
        rows.append({"name": name, "slug": slug,
                     "comps": parse_composition(comp_cell),
                     "states": parse_state_cell(state_cell)})
    if not rows:
        warnings.append("screens.md 에서 구성표('구성' 열이 있는 표)를 읽지 못했습니다. "
                        "component.manifest·state.frames 는 HTML 섹션만 보고 검사합니다.")
    return rows, component_list, warnings


def parse_icon_lists(path):
    """icons.md → (allow:set|None, excluded:set, warnings). 허용 목록은 figma_audit 파서를 재사용."""
    allow, warnings = figma_audit.parse_icon_allowlist(path)
    excluded = set()
    try:
        text = _read(path)
    except OSError:
        return allow, excluded, warnings
    in_excl = False
    header_seen = False
    for raw in text.splitlines():
        s = raw.strip()
        if s.startswith("#"):
            in_excl = "제외" in s
            header_seen = False
            continue
        if not in_excl or not s.startswith("|"):
            continue
        if not header_seen:
            header_seen = True
            continue
        first = s.strip("|").split("|")[0].strip()
        if not first or set(first) <= set("-: "):
            continue
        for name in re.split(r"[,/]", first):
            name = name.strip().strip("`").lower()
            if name:
                excluded.add(name)
    return allow, excluded, warnings


# ── design-rules §A → CSS 변수 기대값 ─────────────────────────────────────
_COLOR_LITERAL_RE = re.compile(r"#[0-9A-Fa-f]{3,8}\b|(?:rgba?|hsla?)\([^)]*\)", re.I)


def canon_css(value):
    """CSS 값 비교용 정규화 (대소문자·공백·따옴표·소수 표기·3자리 hex)."""
    v = (value or "").strip().lower()
    v = re.sub(r"\s*!important\s*$", "", v)
    v = v.replace('"', "").replace("'", "")
    v = re.sub(r"\s*([,()/])\s*", r"\1", v)
    v = re.sub(r"\s+", " ", v)
    v = re.sub(r"(?<![\d.])\.(\d)", r"0.\1", v)
    v = re.sub(r"(\d+)\.(\d*?)0+(?=\D|$)",
               lambda m: m.group(1) + ("." + m.group(2) if m.group(2) else ""), v)
    v = re.sub(r"#([0-9a-f])([0-9a-f])([0-9a-f])(?![0-9a-f])", r"#\1\1\2\2\3\3", v)
    return v


def expected_tokens(rules):
    """design-rules §A 값 → [(css 변수명, 기대값, 원 키)].

    대응 규칙 (README '토큰 이름' 표와 같다)
      color.<n>            → --color-<n>            (값 안 첫 색 리터럴)
      space.scale          → --space-<v>: <v>px     (값 이름. Figma 변수 space/<v> 와 같다)
      space.<n>            → --space-<n>            (첫 정수 px)
      radius               → --radius-<n>: <v>px    ('sm 4 / md 8 …')
      shadow               → --shadow-<n>           ('sm 0 1px 2px rgba(…) / md …')
      font.family          → --font-family
      type.roles           → --type-<role>: <size>px, --type-<role>-weight: <w>
                             (+ 'line-height 1.5, 제목 1.3' → --type-line-height, --type-line-height-title)
    """
    out = []
    for key, value in rules.items():
        fam, _, rest = key.partition(".")
        if fam not in TOKEN_FAMILIES and key not in ("radius", "shadow"):
            continue
        if key.startswith("color."):
            m = _COLOR_LITERAL_RE.search(value)
            if m:
                out.append(("--color-" + rest, m.group(0), key))
        elif key == "space.scale":
            for n in figma_audit._ints(value, 1, 512):
                out.append(("--space-{}".format(n), "{}px".format(n), key))
        elif key.startswith("space."):
            nums = figma_audit._ints(value, 0, 512)
            if nums:
                out.append(("--space-" + rest, "{}px".format(nums[0]), key))
        elif key == "radius":
            for name, num in re.findall(r"\b([a-z][a-z0-9-]*)\s+(\d+)\b", value.split(".")[0]):
                out.append(("--radius-" + name, "{}px".format(num), key))
        elif key == "shadow":
            for name, val in re.findall(
                    r"\b([a-z][a-z0-9-]*)\s+((?:-?[\d.]+(?:px)?\s+){1,4}(?:rgba?|hsla?)\([^)]*\))", value):
                out.append(("--shadow-" + name, val.strip(), key))
        elif key == "font.family":
            out.append(("--font-family", value.strip(), key))
        elif key.startswith("font."):
            out.append(("--font-" + rest, value.strip(), key))
        elif key == "type.roles":
            for role, size, weight in re.findall(r"\b([a-z][a-z0-9-]*)\s+(\d+)\s*/\s*(\d+)", value):
                out.append(("--type-" + role, "{}px".format(size), key))
                out.append(("--type-{}-weight".format(role), weight, key))
            lh = re.search(r"line-height\s*([\d.]+)", value)
            if lh:
                out.append(("--type-line-height", lh.group(1), key))
            lht = re.search(r"제목\s*([\d.]+)", value)
            if lht:
                out.append(("--type-line-height-title", lht.group(1), key))
    seen, uniq = set(), []
    for item in out:
        if item[0] not in seen:
            seen.add(item[0])
            uniq.append(item)
    return uniq


# ── DOM (html.parser) ─────────────────────────────────────────────────────
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
             "param", "source", "track", "wbr"}


class El:
    __slots__ = ("tag", "attrs", "children", "parent", "line", "text")

    def __init__(self, tag, attrs, parent, line):
        self.tag = tag
        self.attrs = attrs
        self.children = []
        self.parent = parent
        self.line = line
        self.text = []

    @property
    def classes(self):
        return (self.attrs.get("class") or "").split()

    def has(self, name):
        return name in self.attrs

    def get(self, name, default=None):
        v = self.attrs.get(name)
        return default if v is None else v


class _DomBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = El("#root", {}, None, 1)
        self.cur = self.root
        self.styles = []          # [(style El, css 텍스트, 시작 줄)]

    def handle_starttag(self, tag, attrs):
        el = El(tag, {k: (v if v is not None else "") for k, v in attrs}, self.cur, self.getpos()[0])
        self.cur.children.append(el)
        if tag not in VOID_TAGS:
            self.cur = el

    def handle_startendtag(self, tag, attrs):
        el = El(tag, {k: (v if v is not None else "") for k, v in attrs}, self.cur, self.getpos()[0])
        self.cur.children.append(el)

    def handle_endtag(self, tag):
        node = self.cur
        while node is not None and node.tag != tag:
            node = node.parent
        if node is not None and node.parent is not None:
            if tag == "style":
                self.styles.append((node, "".join(node.text), node.line))
            self.cur = node.parent

    def handle_data(self, data):
        if self.cur.tag == "style" and not self.cur.text:
            # <style> 여는 태그와 내용 첫 줄이 다르면 줄 번호를 보정할 수 있게 위치를 기억해 둔다
            self.cur.line = self.getpos()[0]
        self.cur.text.append(data)


def build_dom(html):
    b = _DomBuilder()
    b.feed(html)
    b.close()
    return b.root, b.styles


def walk(el):
    stack = list(reversed(el.children))
    while stack:
        cur = stack.pop()
        yield cur
        stack.extend(reversed(cur.children))


def ancestors(el):
    cur = el.parent
    while cur is not None and cur.tag != "#root":
        yield cur
        cur = cur.parent


def direct_text(el):
    return "".join(el.text).strip()


def el_selector(el, stop=None, max_parts=4):
    """사람이 읽을 짧은 선택자. stop(보통 상태 프레임) 아래 경로만."""
    parts = []
    cur = el
    while cur is not None and cur.tag != "#root" and cur is not stop and len(parts) < max_parts:
        s = cur.tag
        if cur.get("data-component"):
            s += '[data-component="{}"]'.format(cur.get("data-component"))
        elif cur.get("id"):
            s += "#" + cur.get("id")
        elif cur.classes:
            s += "." + ".".join(cur.classes[:2])
        par = cur.parent
        if par is not None:
            same = [c for c in par.children if c.tag == cur.tag]
            if len(same) > 1:
                s += ":nth-of-type({})".format(same.index(cur) + 1)
        parts.insert(0, s)
        cur = par
    if cur is not None and cur is not stop and cur.tag != "#root":
        parts.insert(0, "…")
    return " > ".join(parts)


# ── CSS 파싱 ──────────────────────────────────────────────────────────────
class Decl:
    __slots__ = ("prop", "value", "line", "selector", "at", "is_root")

    def __init__(self, prop, value, line, selector, at, is_root):
        self.prop = prop
        self.value = value
        self.line = line
        self.selector = selector
        self.at = at
        self.is_root = is_root


_ROOT_SEL_RE = re.compile(r"^:root(\[[^\]]*\])*$")


def is_root_selector(sel):
    parts = [p.strip() for p in (sel or "").split(",") if p.strip()]
    return bool(parts) and all(_ROOT_SEL_RE.match(p) for p in parts)


def parse_css(css, base_line=1):
    """선언 목록과 @import 문 목록을 돌려준다. 중첩(@media·@supports·CSS nesting)을 따라간다."""
    css = re.sub(r"/\*.*?\*/", lambda m: re.sub(r"[^\n]", " ", m.group(0)), css, flags=re.S)
    newlines = [i for i, c in enumerate(css) if c == "\n"]

    def line_at(pos):
        return base_line + bisect.bisect_left(newlines, pos)

    decls, imports = [], []
    stack = []

    def emit(start, end):
        chunk = css[start:end]
        text = chunk.strip()
        if not text:
            return
        pos = start + (len(chunk) - len(chunk.lstrip()))
        if text.startswith("@"):
            if text.lower().startswith("@import"):
                imports.append((text, line_at(pos)))
            return
        if ":" not in text:
            return
        prop, _, value = text.partition(":")
        sels = [p for p in stack if not p.startswith("@")]
        ats = [p for p in stack if p.startswith("@")]
        selector = sels[-1] if sels else (ats[-1] if ats else None)
        decls.append(Decl(prop.strip().lower(), value.strip(), line_at(pos), selector,
                          ats, bool(sels) and is_root_selector(sels[-1])))

    i, n = 0, len(css)
    start = 0
    quote = None
    paren = 0
    while i < n:
        c = css[i]
        if quote:
            if c == "\\":
                i += 2
                continue
            if c == quote:
                quote = None
        elif c in "\"'":
            quote = c
        elif c == "(":
            paren += 1
        elif c == ")":
            paren = max(0, paren - 1)
        elif paren == 0:
            if c == "{":
                stack.append(re.sub(r"\s+", " ", css[start:i].strip()))
                start = i + 1
            elif c == ";":
                emit(start, i)
                start = i + 1
            elif c == "}":
                emit(start, i)
                if stack:
                    stack.pop()
                start = i + 1
        i += 1
    emit(start, n)
    return decls, imports


# ── token.bound 판정 ──────────────────────────────────────────────────────
_HEX_RE = re.compile(r"(?<![\w&])#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})(?![0-9a-zA-Z_-])")
_FUNC_COLOR_RE = re.compile(r"\b(?:rgba?|hsla?)\s*\([^)]*\)", re.I)
_PX_RE = re.compile(r"(?<![\w.#-])(-?(?:\d+(?:\.\d+)?|\.\d+))px\b")
_URL_RE = re.compile(r"url\([^)]*\)", re.I)
_SPACING_EXACT = {"gap", "row-gap", "column-gap", "grid-gap", "grid-row-gap", "grid-column-gap",
                  "font-size", "font"}
_FONT_PROPS = {"font-size", "font"}
_TEXT120_SEL_RE = re.compile(r"data-state\s*=\s*[\"']?text-120")
_SVG_COLOR_ATTRS = ("fill", "stroke", "stop-color", "color", "flood-color", "lighting-color")


def is_spacing_prop(prop):
    return (prop.startswith("padding") or prop.startswith("margin")
            or prop.endswith("radius") or prop in _SPACING_EXACT)


def hardcoded_literals(prop, value, text120=False):
    """선언 1개에서 토큰 대신 박힌 리터럴을 찾는다. [(종류, 리터럴)]"""
    v = _URL_RE.sub("url()", value or "")
    hits = [("color", m.group(0)) for m in _HEX_RE.finditer(v)]
    hits += [("color", m.group(0)) for m in _FUNC_COLOR_RE.finditer(v)]
    if is_spacing_prop(prop) and not (text120 and prop in _FONT_PROPS):
        for m in _PX_RE.finditer(v):
            if abs(float(m.group(1))) in (0.0, 1.0):
                continue
            hits.append(("px", m.group(0)))
    return hits


def _expected_for(prop, kinds):
    if "color" in kinds:
        return "var(--color-*) 토큰"
    if prop in _FONT_PROPS:
        return "var(--type-*) 토큰"
    if prop.endswith("radius"):
        return "var(--radius-*) 토큰"
    return "var(--space-*) 토큰"


# ── 페이지 모델 ───────────────────────────────────────────────────────────
class Frame:
    __slots__ = ("el", "slug", "section", "state", "width", "label")

    def __init__(self, el, slug, section, state, width, label):
        self.el = el
        self.slug = slug
        self.section = section
        self.state = state
        self.width = width
        self.label = label


class Page:
    def __init__(self, path, html, th):
        self.path = path
        self.name = os.path.basename(path)
        self.html = html
        self.root, self.styles = build_dom(html)
        self.sections = [el for el in walk(self.root) if el.has("data-screen")]
        self.frames = []
        self.frame_of = {}
        for el in walk(self.root):
            if not (el.has("data-state") and "phone" in el.classes):
                continue
            section = next((a for a in ancestors(el) if a.has("data-screen")), None)
            slug = section.get("data-screen") if section is not None else None
            try:
                width = int(el.get("data-width") or th.frame_w)
            except ValueError:
                width = th.frame_w
            state = el.get("data-state").strip()
            label = state + ("@{}".format(width) if width != th.frame_w else "")
            fr = Frame(el, slug, section, state, width, label)
            self.frames.append(fr)
            for d in walk(el):
                self.frame_of[id(d)] = fr
            self.frame_of[id(el)] = fr
        self.has_script = any(el.tag == "script" and direct_text(el) for el in walk(self.root))

    def locate(self, el):
        """요소 → (화면, 상태, 기준 프레임 El)."""
        fr = self.frame_of.get(id(el))
        if fr is not None:
            return fr.slug, fr.label, fr.el
        section = el if el.has("data-screen") else next((a for a in ancestors(el) if a.has("data-screen")), None)
        return (section.get("data-screen") if section is not None else None), None, None

    def in_product(self, el):
        """토큰 규칙 대상 영역 = 상태 프레임 안, 또는 [data-component] 안(규칙 미리보기 견본)."""
        if id(el) in self.frame_of:
            return True
        return el.has("data-component") or any(a.has("data-component") for a in ancestors(el))


def _loc_from_selector(sel):
    """CSS 선택자 안의 data-screen / data-state 값을 위치로 쓴다."""
    screen = re.search(r"data-screen\s*=\s*[\"']?([\w-]+)", sel or "")
    state = re.search(r"data-state\s*=\s*[\"']?([\w-]+)", sel or "")
    return (screen.group(1) if screen else None), (state.group(1) if state else None)


# ── 정적 검사 ─────────────────────────────────────────────────────────────
def check_token_bound(page, findings):
    for style_el, css, line in page.styles:
        if style_el.has("data-chrome"):
            continue
        decls, _ = parse_css(css, line)
        for d in decls:
            if d.is_root:
                continue
            text120 = bool(_TEXT120_SEL_RE.search(d.selector or ""))
            hits = hardcoded_literals(d.prop, d.value, text120)
            if not hits:
                continue
            screen, state = _loc_from_selector(d.selector)
            findings.append(Finding(
                "token.bound", page.name, screen, state, "<style>:L{}".format(d.line), d.selector,
                "{}: {}".format(d.prop, d.value),
                "{} (리터럴 {})".format(_expected_for(d.prop, {k for k, _ in hits}),
                                     ", ".join(lit for _, lit in hits))))
    for el in walk(page.root):
        if not page.in_product(el):
            continue
        screen, state, frame_el = page.locate(el)
        text120 = state is not None and state.split("@")[0] == "text-120"
        style = el.get("style")
        if style:
            decls, _ = parse_css(style)
            for d in decls:
                hits = hardcoded_literals(d.prop, d.value, text120)
                if hits:
                    findings.append(Finding(
                        "token.bound", page.name, screen, state, el.tag + "[style]",
                        el_selector(el, frame_el), "{}: {}".format(d.prop, d.value),
                        "{} (인라인 style 리터럴 {})".format(
                            _expected_for(d.prop, {k for k, _ in hits}), ", ".join(l for _, l in hits))))
        for attr in _SVG_COLOR_ATTRS:
            val = el.get(attr)
            if val and (_HEX_RE.search(val) or _FUNC_COLOR_RE.search(val)):
                findings.append(Finding(
                    "token.bound", page.name, screen, state, "{}[{}]".format(el.tag, attr),
                    el_selector(el, frame_el), '{}="{}"'.format(attr, val),
                    "currentColor 또는 var(--color-*)"))


def check_token_defined(page, tokens, findings):
    root_vars = {}
    refs = {}

    def add_ref(name, where):
        refs.setdefault(name, []).append(where)

    for style_el, css, line in page.styles:
        decls, _ = parse_css(css, line)
        for d in decls:
            if d.is_root and d.prop.startswith("--"):
                root_vars.setdefault(d.prop, (d.value, d.line))
            for m in re.finditer(r"var\(\s*(--[\w-]+)", d.value):
                screen, state = _loc_from_selector(d.selector)
                add_ref(m.group(1), (screen, state, "<style>:L{}".format(d.line), d.selector))
    for el in walk(page.root):
        style = el.get("style")
        if not style or "var(" not in style:
            continue
        screen, state, frame_el = page.locate(el)
        for m in re.finditer(r"var\(\s*(--[\w-]+)", style):
            add_ref(m.group(1), (screen, state, el.tag + "[style]", el_selector(el, frame_el)))

    for name in sorted(set(refs) - set(root_vars)):
        where = refs[name]
        screen, state, node, sel = where[0]
        more = " 외 {}곳".format(len(where) - 1) if len(where) > 1 else ""
        findings.append(Finding(
            "token.defined", page.name, screen, state, node, sel,
            "var({}) 참조{} · :root 정의 없음".format(name, more), ":root 에 {} 정의".format(name)))

    for var, expected, key in tokens:
        if var not in root_vars:
            findings.append(Finding(
                "token.defined", page.name, None, None, ":root", ":root",
                "{} 없음".format(var), "{}: {} ({})".format(var, expected, key)))
            continue
        actual, line = root_vars[var]
        if canon_css(actual) != canon_css(expected):
            findings.append(Finding(
                "token.defined", page.name, None, None, ":root:L{}".format(line), ":root",
                "{}: {}".format(var, actual), "{} (design-rules {})".format(expected, key)))


def check_icons(page, allow, excluded, findings):
    seen = {}
    for el in walk(page.root):
        name = el.get("data-icon")
        if name is None:
            continue
        name = name.strip().lower()
        screen, state, frame_el = page.locate(el)
        key = (screen, name)
        if key in seen:
            seen[key][1] += 1
            continue
        if name in excluded:
            f = Finding("icon.allowlist", page.name, screen, state, "data-icon", el_selector(el, frame_el),
                        "{} (icons.md 제외 목록)".format(name), "icons.md 허용 목록의 같은 의미 아이콘")
        elif allow is not None and name not in allow:
            f = Finding("icon.allowlist", page.name, screen, state, "data-icon", el_selector(el, frame_el),
                        "{} (허용 목록 밖)".format(name), "icons.md 'lucide 이름' 열의 이름")
        else:
            continue
        seen[key] = [f, 1]
        findings.append(f)
    for f, count in seen.values():
        if count > 1:
            f.actual += " · {}곳".format(count)
    # 프레임 안에서 data-icon 래퍼 없이 그린 SVG = 직접 그린 아이콘
    for fr in page.frames:
        for el in walk(fr.el):
            if el.tag != "svg":
                continue
            if el.has("data-icon") or any(a.has("data-icon") for a in ancestors(el)):
                continue
            findings.append(Finding(
                "icon.allowlist", page.name, fr.slug, fr.label, "svg", el_selector(el, fr.el),
                "data-icon 래퍼 없는 <svg>", '<i data-icon="<lucide 이름>"> 안의 lucide SVG'))


def _top_components(frame_el):
    """프레임 안 최상위 data-component (다른 data-component 안에 든 것은 제외)."""
    out = []
    for el in walk(frame_el):
        if not el.has("data-component"):
            continue
        nested = False
        for a in ancestors(el):
            if a is frame_el:
                break
            if a.has("data-component"):
                nested = True
                break
        if not nested:
            out.append(el)
    return out


def required_states(row, found_names):
    """필수 상태 = 기본 7종 + (FormField 가 있으면 keyboard) + screens.md 상태 열의 추가 상태(guest-name 등)."""
    need = list(BASE_STATES)
    comps = set(row["comps"]) if row else set()
    if FORM_COMPONENT in comps or FORM_COMPONENT in found_names:
        need.append(KEYBOARD_STATE)
    for st in (row["states"] if row else []):
        if st not in need and st in KNOWN_STATES:
            need.append(st)
    return need


def check_screens(page, rows, component_list, th, findings, rule_keys=frozenset()):
    """component.manifest · state.frames · button.primary-per-screen (화면 파일에만)."""
    by_slug = {r["slug"]: r for r in rows if r["slug"]}
    by_name = {r["name"]: r for r in rows if r["name"]}
    sections = {}
    for sec in page.sections:
        sections.setdefault(sec.get("data-screen"), sec)

    matched_rows = set()
    for slug, sec in sections.items():
        row = by_slug.get(slug) or by_name.get(sec.get("data-screen-name") or "")
        if row is None and rows:
            findings.append(Finding(
                "component.manifest", page.name, slug, None, "section", '[data-screen="{}"]'.format(slug),
                "screens.md 에 없는 화면", "screens.md 구성표에 행 추가 후 사용자 확인"))
        if row is not None:
            matched_rows.add(id(row))
    for row in rows:
        if id(row) in matched_rows:
            continue
        slug = row["slug"] or row["name"]
        findings.append(Finding(
            "component.manifest", page.name, slug, None, "section", '[data-screen="{}"]'.format(slug),
            "data-screen 섹션 없음", '<section data-screen="{}" data-screen-name="{}">'.format(
                row["slug"], row["name"])))
        need = required_states(row, [])
        findings.append(Finding(
            "state.frames", page.name, slug, None, "section", '[data-screen="{}"]'.format(slug),
            "data-screen 섹션 없음 (상태 프레임 0개)",
            '.phone[data-state] × {}'.format("/".join(need))))

    frames_by_slug = {}
    for fr in page.frames:
        frames_by_slug.setdefault(fr.slug, []).append(fr)

    for slug, sec in sections.items():
        row = by_slug.get(slug) or by_name.get(sec.get("data-screen-name") or "")
        frames = frames_by_slug.get(slug, [])
        main = [fr for fr in frames if fr.width == th.frame_w]
        default = next((fr for fr in main if fr.state == "default"), None)
        found = _top_components(default.el) if default is not None else []
        found_names = [el.get("data-component") for el in found]

        # state.frames
        need = required_states(row, found_names)
        present = {fr.state for fr in main}
        missing = [s for s in need if s not in present]
        if missing:
            findings.append(Finding(
                "state.frames", page.name, slug, None, "section", '[data-screen="{}"]'.format(slug),
                "누락 " + "/".join(missing) + ("" if frames else " (.phone[data-state] 0개)"),
                "/".join(need) + " {}개".format(len(need))))

        if default is None:
            continue

        # component.manifest — default 프레임 최상위 data-component 집합 = 구성표
        if row is not None:
            expected = set(row["comps"])
            got = set(found_names)
            if not found:
                findings.append(Finding(
                    "component.manifest", page.name, slug, default.label, "frame", ".phone[data-state=default]",
                    "data-component 속성 없음 (0개)", "구성표 " + " · ".join(row["comps"])))
            else:
                for name in sorted(expected - got):
                    findings.append(Finding(
                        "component.manifest", page.name, slug, default.label, name, ".phone[data-state=default]",
                        "{} 없음".format(name), 'screens.md 구성대로 data-component="{}" 배치'.format(name)))
                for el in found:
                    name = el.get("data-component")
                    if name not in expected:
                        findings.append(Finding(
                            "component.manifest", page.name, slug, default.label, name,
                            el_selector(el, default.el), "{} (구성표 밖)".format(name),
                            "제거하거나 screens.md 에 추가 후 사용자 확인"))

        # button.primary-per-screen — 예외는 .phone[data-state] 의 data-primary-exempt="<design-rules §C 키>"
        count = sum(1 for el in [default.el] + list(walk(default.el)) if el.has("data-primary"))
        exempt = default.el.has("data-primary-exempt")
        key = (default.el.get("data-primary-exempt") or "").strip()
        if exempt and rule_keys and key not in rule_keys:
            findings.append(Finding(
                "button.primary-per-screen", page.name, slug, default.label, "frame", ".phone[data-state=default]",
                'data-primary-exempt="{}" (design-rules 에 없는 키)'.format(key),
                'design-rules §C 의 예외 키 (예: data-primary-exempt="web.primary")'))
        ok = count <= 1 if exempt else count == 1
        if not ok:
            findings.append(Finding(
                "button.primary-per-screen", page.name, slug, default.label, "frame", ".phone[data-state=default]",
                "data-primary {}개".format(count),
                "0~1개 (data-primary-exempt={})".format(key) if exempt else "정확히 1개"))

    # 컴포넌트 목록에 없는 이름 (모든 프레임)
    if component_list:
        seen = set()
        for fr in page.frames:
            for el in walk(fr.el):
                name = el.get("data-component")
                if name and name not in component_list and (fr.slug, name) not in seen:
                    seen.add((fr.slug, name))
                    findings.append(Finding(
                        "component.manifest", page.name, fr.slug, fr.label, name, el_selector(el, fr.el),
                        "{} (screens.md 컴포넌트 목록 밖)".format(name), "컴포넌트 목록의 이름"))


# 외부 자원을 불러오는 태그·속성 (<a href> 같은 이동 링크는 자원이 아니므로 제외)
_RESOURCE_ATTRS = {
    "script": ("src",), "img": ("src", "srcset"), "link": ("href",), "source": ("src", "srcset"),
    "video": ("src", "poster"), "audio": ("src",), "iframe": ("src",), "embed": ("src",),
    "track": ("src",), "object": ("data",), "image": ("href", "xlink:href"), "use": ("href", "xlink:href"),
}


def check_hygiene(page, findings):
    """no-lorem · no-external (check_phase probes 규칙 재사용 + img·CSS url 추가)."""
    m = re.search(r"lorem ipsum", page.html, re.I)
    if m:
        line = page.html.count("\n", 0, m.start()) + 1
        findings.append(Finding("no-lorem", page.name, None, None, "L{}".format(line), "-",
                                "lorem ipsum 문자열", "실제 문구"))

    def allowed(url):
        return any(h in url for h in FONT_ALLOWED_HOSTS)

    for el in walk(page.root):
        for attr in _RESOURCE_ATTRS.get(el.tag, ()):
            url = el.get(attr)
            if not url:
                continue
            urls = [u.strip().split(" ")[0] for u in url.split(",")] if attr == "srcset" else [url]
            for u in urls:
                if check_phase._is_external(u) and not allowed(u):
                    findings.append(Finding("no-external", page.name, None, None,
                                            "<{}>:L{}".format(el.tag, el.line), el.tag,
                                            "{}={}".format(attr, u), "인라인(데이터 URI) 또는 fonts.googleapis.com"))
    for style_el, css, line in page.styles:
        decls, imports = parse_css(css, line)
        sources = [(d.value, d.line, d.selector) for d in decls] + [(t, ln, "@import") for t, ln in imports]
        for value, ln, sel in sources:
            for um in re.finditer(r"url\(\s*[\"']?([^\"')]+)|@import\s+[\"']([^\"']+)", value, re.I):
                url = um.group(1) or um.group(2)
                if check_phase._is_external(url) and not allowed(url):
                    findings.append(Finding("no-external", page.name, None, None, "<style>:L{}".format(ln),
                                            sel, "url({})".format(url), "인라인(데이터 URI) 또는 fonts.googleapis.com"))


def static_findings(page, ctx):
    findings = []
    check_token_bound(page, findings)
    check_token_defined(page, ctx["tokens"], findings)
    check_icons(page, ctx["allow"], ctx["excluded"], findings)
    if page.name == SCREENS_FILE and not ctx["skip_screens"]:
        check_screens(page, ctx["rows"], ctx["component_list"], ctx["th"], findings, ctx["rule_keys"])
    check_hygiene(page, findings)
    return findings


# ── 렌더 검사 (playwright) ────────────────────────────────────────────────
class RenderUnavailable(Exception):
    pass


def _import_playwright():
    from playwright.sync_api import sync_playwright  # noqa: WPS433 (지연 import)
    return sync_playwright


TAG_FRAMES_JS = r"""
() => Array.from(document.querySelectorAll('.phone[data-state]')).map((el, i) => {
  el.setAttribute('data-audit-id', String(i));
  const sec = el.closest('[data-screen]');
  const r = el.getBoundingClientRect();
  return {id: String(i), screen: sec ? sec.getAttribute('data-screen') : null,
          state: (el.getAttribute('data-state') || '').trim(),
          width: parseInt(el.getAttribute('data-width') || '0', 10) || null,
          visible: r.width > 0 && r.height > 0};
})
"""

MEASURE_JS = r"""
([mode, ids, step]) => {
  const FRAME = '.phone[data-state]';
  const pids = new WeakMap(); let seq = 0;
  const pid = el => { if (!el) return -1; if (!pids.has(el)) pids.set(el, ++seq); return pids.get(el); };
  const vis = el => {
    const r = el.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) return false;
    const cs = getComputedStyle(el);
    return cs.visibility !== 'hidden' && cs.display !== 'none';
  };
  const sel = (el, stop) => {
    const parts = []; let cur = el;
    while (cur && cur !== stop && cur.nodeType === 1 && cur !== document.body && parts.length < 4) {
      let s = cur.tagName.toLowerCase();
      if (cur.dataset && cur.dataset.component) s += `[data-component="${cur.dataset.component}"]`;
      else if (cur.id) s += '#' + cur.id;
      else if (cur.classList && cur.classList.length) s += '.' + Array.from(cur.classList).slice(0, 2).join('.');
      const p = cur.parentElement;
      if (p) { const same = Array.from(p.children).filter(c => c.tagName === cur.tagName);
               if (same.length > 1) s += `:nth-of-type(${same.indexOf(cur) + 1})`; }
      parts.unshift(s); cur = cur.parentElement;
    }
    if (cur && cur !== stop && cur !== document.body) parts.unshift('…');
    return parts.join(' > ');
  };
  const nodeName = (el, stop) => {
    const c = el.closest('[data-component]');
    return c && (!stop || stop.contains(c)) ? c.getAttribute('data-component') : el.tagName.toLowerCase();
  };
  const isLabel = el => !!el.closest('[data-label]');
  const offGrid = v => Math.abs(v - Math.round(v)) > 0.01 || Math.round(Math.abs(v)) % step !== 0;
  const SP = ['paddingTop','paddingRight','paddingBottom','paddingLeft','marginTop','marginRight','marginBottom','marginLeft','rowGap','columnGap'];

  function measure(scope, frame, keep) {
    const base = frame ? frame.getBoundingClientRect() : {left: 0, top: 0, right: 0};
    const rel = r => ({x: r.left - base.left, y: r.top - base.top, w: r.width, h: r.height});
    const q = s => Array.from(scope.querySelectorAll(s)).filter(keep);
    const out = {taps: [], spacing: [], fixed: [], scrolls: [], truncates: [], untagged: [], overflow: []};

    for (const el of q('[data-tap]')) {
      if (isLabel(el) || !vis(el)) continue;
      const r = rel(el.getBoundingClientRect());
      const par = el.parentElement;
      out.taps.push(Object.assign({sel: sel(el, frame), node: nodeName(el, frame), parent: pid(par),
        grouped: !!(par && par.closest('[data-tap-group],[data-fixed="tabbar"]'))}, r));
    }
    for (const comp of q('[data-component]')) {
      const els = [comp].concat(Array.from(comp.querySelectorAll('*')))
        .filter(el => el.closest('[data-component]') === comp && !isLabel(el) && vis(el));
      for (const el of els) {
        const cs = getComputedStyle(el);
        const ml = parseFloat(cs.marginLeft) || 0, mr = parseFloat(cs.marginRight) || 0;
        for (const p of SP) {
          const raw = cs[p];
          if (!raw || raw === 'normal' || raw === 'auto') continue;
          if ((p === 'marginLeft' || p === 'marginRight') && ml === mr && ml !== 0) continue; // margin:auto 가운데 정렬
          const v = parseFloat(raw);
          if (!isFinite(v) || v === 0 || !offGrid(v)) continue;
          out.spacing.push({sel: sel(el, frame), node: comp.getAttribute('data-component'), prop: p, value: v});
        }
      }
    }
    for (const el of q('[data-truncate]')) {
      if (isLabel(el) || !vis(el)) continue;
      const cs = getComputedStyle(el);
      out.truncates.push({sel: sel(el, frame), node: nodeName(el, frame),
        lines: parseInt(el.getAttribute('data-truncate'), 10) || 0,
        clamp: String(cs.webkitLineClamp || cs.getPropertyValue('-webkit-line-clamp') || 'none'),
        ellipsis: cs.textOverflow === 'ellipsis', nowrap: cs.whiteSpace === 'nowrap' || cs.whiteSpace === 'pre',
        ovx: cs.overflowX, sh: el.scrollHeight, ch: el.clientHeight, sw: el.scrollWidth, cw: el.clientWidth});
    }
    for (const el of q('*')) {
      if (el.closest('[data-truncate]') || isLabel(el) || !vis(el)) continue;
      const cs = getComputedStyle(el);
      const clamp = String(cs.webkitLineClamp || 'none');
      const cutX = cs.textOverflow === 'ellipsis' && cs.overflowX !== 'visible' && el.scrollWidth > el.clientWidth + 1;
      const cutY = clamp !== 'none' && el.scrollHeight > el.clientHeight + 1;
      if (cutX || cutY) out.untagged.push({sel: sel(el, frame), node: nodeName(el, frame), kind: cutX ? 'ellipsis' : 'line-clamp ' + clamp,
        text: (el.textContent || '').trim().slice(0, 24)});
    }
    if (frame) {
      const fr = frame.getBoundingClientRect();
      for (const el of q('[data-fixed]')) {
        if (!vis(el)) continue;
        const r = rel(el.getBoundingClientRect());
        const cs = getComputedStyle(el);
        let safeH = 0;
        for (const s of el.querySelectorAll('[data-safe-area]')) safeH = Math.max(safeH, s.getBoundingClientRect().height);
        out.fixed.push({sel: sel(el, frame), kind: el.getAttribute('data-fixed'), top: r.y, bottom: r.y + r.h,
          height: r.h, paddingBottom: parseFloat(cs.paddingBottom) || 0, safeH});
      }
      for (const el of q('[data-scroll]')) {
        const prev = el.scrollTop;
        el.scrollTop = el.scrollHeight;
        const kids = Array.from(el.children).filter(vis);
        const last = kids[kids.length - 1];
        let lastBottom = null, lastSel = null;
        if (last) { const r = rel(last.getBoundingClientRect()); lastBottom = r.y + r.h; lastSel = sel(last, frame); }
        el.scrollTop = prev;
        out.scrolls.push({sel: sel(el, frame), lastSel, lastBottom});
      }
      for (const el of q('*')) {
        const hasText = Array.from(el.childNodes).some(n => n.nodeType === 3 && n.textContent.trim());
        if (!hasText || isLabel(el) || !vis(el)) continue;
        const r = el.getBoundingClientRect();
        let by = null, limit = null;
        if (r.right > fr.right + 1) { by = 'frame'; limit = fr.right; }
        else {
          for (let a = el.parentElement; a && a !== frame; a = a.parentElement) {
            const cs = getComputedStyle(a);
            if (a.hasAttribute('data-truncate') || cs.textOverflow === 'ellipsis') break;
            if (cs.overflowX === 'hidden' || cs.overflowX === 'clip') {
              const ar = a.getBoundingClientRect();
              if (r.right > ar.right + 1) { by = sel(a, frame); limit = ar.right; }
              break;
            }
          }
        }
        if (by) out.overflow.push({sel: sel(el, frame), node: nodeName(el, frame), by,
          right: r.right - fr.left, limit: limit - fr.left, text: el.textContent.trim().slice(0, 24)});
      }
      const r = frame.getBoundingClientRect();
      out.rect = {w: r.width, h: r.height};
    }
    return out;
  }

  if (mode === 'frames') {
    return ids.map(id => {
      const f = document.querySelector(`[data-audit-id="${id}"]`);
      return Object.assign({id}, measure(f, f, () => true));
    });
  }
  return measure(document.body, null, el => !el.closest(FRAME));
}
"""

NO_ANIM_CSS = ("*,*::before,*::after{animation:none!important;transition:none!important;"
               "caret-color:transparent!important}")


def _fmt(v):
    return "{:g}".format(round(v, 2))


def render_findings(file, scopes, th):
    """측정값(scopes) → 결함. scopes: [{screen, state(label), [rect, width, raw_state], taps, …}]

    playwright 없이도 테스트할 수 있게 판정은 전부 여기(파이썬)에서 한다.
    """
    findings = []
    step = th.space_step
    grid_seen = {}
    for sc in scopes:
        screen, label = sc.get("screen"), sc.get("state")
        raw_state = sc.get("raw_state") or (label or "").split("@")[0]
        width = sc.get("width") or th.frame_w
        is_frame = sc.get("rect") is not None

        def add(rule, node, sel, actual, expected):
            findings.append(Finding(rule, file, screen, label, node, sel, actual, expected))

        # frame.size
        if is_frame:
            w, h = sc["rect"]["w"], sc["rect"]["h"]
            if abs(w - width) > 0.5 or abs(h - th.frame_h) > 0.5:
                add("frame.size", "frame", ".phone[data-state]", "{}×{}".format(_fmt(w), _fmt(h)),
                    "{}×{} (data-width × device.frame 높이, 축소·transform 금지)".format(width, th.frame_h))

        # tap.min / tap.gap
        taps = sc.get("taps") or []
        for t in taps:
            if t["w"] < th.tap_min - 0.5 or t["h"] < th.tap_min - 0.5:
                add("tap.min", t["node"], t["sel"], "{}×{}".format(_fmt(t["w"]), _fmt(t["h"])),
                    "≥ {}×{}".format(th.tap_min, th.tap_min))
        by_parent = {}
        for t in taps:
            if not t.get("grouped"):
                by_parent.setdefault(t["parent"], []).append(t)
        for sibs in by_parent.values():
            for i, a in enumerate(sibs):
                for b in sibs[i + 1:]:
                    gap_x = max(b["x"] - (a["x"] + a["w"]), a["x"] - (b["x"] + b["w"]))
                    gap_y = max(b["y"] - (a["y"] + a["h"]), a["y"] - (b["y"] + b["h"]))
                    gap = max(gap_x, gap_y)
                    if gap < th.tap_gap - 0.5:
                        add("tap.gap", b["node"], b["sel"], "{} 와 간격 {}".format(a["sel"], _fmt(gap)),
                            "≥ {} (칸이 붙는 묶음이면 부모에 data-tap-group)".format(th.tap_gap))

        # space.grid — 한 요소의 같은 값 속성은 한 줄로, 같은 요소·같은 값은 파일 전체에서 1건으로 묶는다
        per_el = {}
        for s in sc.get("spacing") or []:
            v = s["value"]
            if not (abs(v - round(v)) > 0.01 or round(abs(v)) % step != 0):
                continue
            per_el.setdefault((s["node"], s["sel"], round(v, 2)), []).append(s["prop"])
        for (node, sel, v), props in per_el.items():
            tail = re.sub(r":nth-of-type\(\d+\)", "", " > ".join(sel.split(" > ")[-2:]))
            key = (node, tail, tuple(props), v)
            if key in grid_seen:
                grid_seen[key][1] += 1
                continue
            f = Finding("space.grid", file, screen, label, node, sel,
                        "{} {}px".format("·".join(props), _fmt(v)), "{} 배수 (space.scale)".format(step))
            grid_seen[key] = [f, 1]
            findings.append(f)

        # text.clip
        for t in sc.get("truncates") or []:
            lines, clamp = t["lines"], str(t["clamp"])
            clamp_n = int(clamp) if clamp.isdigit() else None
            overflow = t["sh"] > t["ch"] + 1 or (t["sw"] > t["cw"] + 1 and not t["ellipsis"])
            if lines >= 2:
                if clamp_n is None:
                    add("text.clip", t["node"], t["sel"],
                        "-webkit-line-clamp 없음" + (" · 내용이 잘림" if overflow else ""),
                        "-webkit-line-clamp: {} (data-truncate)".format(lines))
                elif clamp_n != lines:
                    add("text.clip", t["node"], t["sel"], "-webkit-line-clamp {}".format(clamp_n),
                        "{} (data-truncate)".format(lines))
            else:
                one_line = t["ellipsis"] and t["nowrap"] and t["ovx"] not in ("visible",)
                if clamp_n is not None and clamp_n != 1:
                    add("text.clip", t["node"], t["sel"], "-webkit-line-clamp {}".format(clamp_n),
                        "1 (data-truncate)")
                elif clamp_n is None and not one_line:
                    add("text.clip", t["node"], t["sel"],
                        "1줄 말줄임 미설정" + (" · 내용이 잘림" if overflow else ""),
                        "text-overflow:ellipsis + white-space:nowrap + overflow:hidden (또는 line-clamp 1)")
        for u in sc.get("untagged") or []:
            add("text.clip", u["node"], u["sel"], "말줄임 적용({}) · data-truncate 없음 '{}'".format(u["kind"], u["text"]),
                'text.truncate 대상이면 data-truncate="n", 아니면 줄바꿈 허용')
        for o in sc.get("overflow") or []:
            add("text.clip", o["node"], o["sel"],
                "'{}' 오른쪽 {} > {} ({}에서 잘림)".format(o["text"], _fmt(o["right"]), _fmt(o["limit"]), o["by"]),
                "줄바꿈·말줄임(data-truncate) 또는 레이아웃 조정")

        if not is_frame:
            continue
        fixed = sc.get("fixed") or []

        # fixed.no-clip
        if fixed and raw_state in NO_CLIP_STATES:
            bar = min(fixed, key=lambda f: f["top"])
            scrolls = sc.get("scrolls") or []
            if not scrolls:
                add("fixed.no-clip", "frame", ".phone[data-state]", "[data-scroll] 없음",
                    "스크롤 본문에 data-scroll")
            for s in scrolls:
                if s["lastBottom"] is not None and s["lastBottom"] > bar["top"] + 0.5:
                    add("fixed.no-clip", s["lastSel"] or "-", s["sel"],
                        "스크롤 끝 마지막 요소 하단 {} > 고정 바({}) 상단 {}".format(
                            _fmt(s["lastBottom"]), bar["kind"], _fmt(bar["top"])),
                        "고정 바 위에서 끝남 (scroll.last-item: 하단 여백 = 고정 바 + safe-area + 16)")

        # safe-area — 가장 아래 고정 바는 홈 인디케이터(34) 위에서 끝나거나 안에 safe-area 영역을 가진다
        if fixed:
            low = max(fixed, key=lambda f: f["bottom"])
            limit = th.frame_h - th.safe_bottom
            inside = max(low.get("safeH") or 0, low.get("paddingBottom") or 0) >= th.safe_bottom - 0.5
            if low["bottom"] > limit + 0.5 and not inside:
                add("safe-area", low["kind"], low["sel"], "{} 하단 {}".format(low["kind"], _fmt(low["bottom"])),
                    "≤ {} 또는 안쪽 [data-safe-area] 높이 ≥ {}".format(limit, th.safe_bottom))

    for f, count in grid_seen.values():
        if count > 1:
            f.actual += " (같은 값 {}곳)".format(count)
    return findings


def _shot_name(frame, used, th, stem):
    slug = frame["screen"] or stem
    name = "{}-{}".format(slug, frame["state"] or "frame")
    if frame["width"] and frame["width"] != th.frame_w:
        name += "@{}".format(frame["width"])
    base, k = name, 2
    while name in used:
        name = "{}-{}".format(base, k)
        k += 1
    used.add(name)
    return re.sub(r"[^\w@.-]+", "_", name) + ".png"


PAGE_VIEWPORT = {"width": 1280, "height": 900}


def run_render(paths, th, shots_dir, scale=2, viewport="page"):
    """파일마다 1회 로드 → (렌더된 HTML, 측정 scopes, 스크린샷 수, 경고).

    viewport="page"   : 미리보기 페이지 폭(1280)으로 한 번 배치하고 프레임 폭은 CSS(data-width)가 정한다 (기본).
    viewport="device" : data-width 별로 뷰포트를 그 폭으로 바꿔 측정한다 (페이지 재로드 없음).
                        페이지 크롬의 모바일 미디어쿼리가 .phone 크기를 바꾸면 frame.size 로 드러난다.
    """
    try:
        sync_playwright = _import_playwright()
    except ImportError as exc:
        raise RenderUnavailable("playwright 를 import 하지 못했습니다 ({}).\n{}".format(exc, INSTALL_HINT))
    results = {}
    warnings = []
    shots = 0
    if shots_dir:
        os.makedirs(shots_dir, exist_ok=True)
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Exception as exc:  # 브라우저 미설치·버전 불일치
            raise RenderUnavailable("chromium 실행 실패: {}\n{}".format(str(exc).splitlines()[0], INSTALL_HINT))
        try:
            page = browser.new_page(viewport=dict(PAGE_VIEWPORT), device_scale_factor=scale)

            def route(r):
                url = r.request.url
                if url.startswith(("file:", "data:", "blob:")) or any(h in url for h in FONT_ALLOWED_HOSTS):
                    r.continue_()
                else:
                    r.abort()
            page.route("**/*", route)
            used = set()
            for path in paths:
                page.set_viewport_size(dict(PAGE_VIEWPORT))
                page.goto(Path(path).resolve().as_uri(), wait_until="load")
                page.evaluate("async () => { if (document.fonts) { await document.fonts.ready; } return true; }")
                rendered = page.content()
                page.add_style_tag(content=NO_ANIM_CSS)
                frames = page.evaluate(TAG_FRAMES_JS)
                scopes = []
                doc = page.evaluate(MEASURE_JS, ["doc", [], th.space_step])
                doc.update({"screen": None, "state": None})
                scopes.append(doc)
                widths = sorted({fr["width"] or th.frame_w for fr in frames})
                stem = Path(path).stem
                for w in widths:
                    group = [fr for fr in frames if (fr["width"] or th.frame_w) == w]
                    if viewport == "device":
                        page.set_viewport_size({"width": w, "height": th.frame_h})
                    for fr in group:
                        if shots_dir and fr["visible"]:
                            target = os.path.join(shots_dir, _shot_name(fr, used, th, stem))
                            try:
                                page.locator('[data-audit-id="{}"]'.format(fr["id"])).screenshot(
                                    path=target, timeout=10000)
                                shots += 1
                            except Exception as exc:
                                warnings.append("스크린샷 실패 {} {}: {}".format(
                                    fr["screen"] or stem, fr["state"], str(exc).splitlines()[0]))
                    measured = page.evaluate(MEASURE_JS, ["frames", [fr["id"] for fr in group], th.space_step])
                    info = {fr["id"]: fr for fr in group}
                    for m in measured:
                        fr = info[m["id"]]
                        width = fr["width"] or th.frame_w
                        m.update({"screen": fr["screen"], "raw_state": fr["state"], "width": width,
                                  "state": fr["state"] + ("@{}".format(width) if width != th.frame_w else "")})
                        scopes.append(m)
                if viewport == "device":
                    page.set_viewport_size(dict(PAGE_VIEWPORT))
                results[path] = (rendered, scopes)
        finally:
            browser.close()
    return results, shots, warnings


# ── 실행 ──────────────────────────────────────────────────────────────────
def find_targets(design_dir):
    out = []
    for name in TARGET_FILES:
        for cand in (os.path.join(design_dir, "probes", name), os.path.join(design_dir, name)):
            if os.path.isfile(cand):
                out.append(cand)
                break
    return out


def run_audit(design_dir, render=False, shots_dir=None, scale=2, viewport="page"):
    """검사 수행 → (findings, warnings, stats). 실행 오류는 AuditError / RenderUnavailable."""
    if not os.path.isdir(design_dir):
        raise AuditError("design 폴더가 없습니다: {}".format(design_dir))
    rules_path = os.path.join(design_dir, "design-rules.md")
    if not os.path.isfile(rules_path):
        raise AuditError("design-rules.md 가 없습니다: {}".format(rules_path))
    targets = find_targets(design_dir)
    if not targets:
        raise AuditError("검사할 HTML 이 없습니다: {}/probes/{{{}}}".format(design_dir, ",".join(TARGET_FILES)))

    rules, warnings = figma_audit.parse_rules_file(rules_path)
    th = figma_audit.Thresholds(rules, warnings)
    tokens = expected_tokens(rules)
    if not tokens:
        warnings.append("design-rules §A 에서 토큰 값을 읽지 못했습니다. token.defined 는 참조·정의 짝만 봅니다.")

    allow, excluded = None, set()
    icons_path = os.path.join(design_dir, "icons.md")
    if os.path.isfile(icons_path):
        allow, excluded, w = parse_icon_lists(icons_path)
        warnings.extend(w)
    else:
        warnings.append("icons.md 가 없어 icon.allowlist 는 제외 목록 없이 SVG 래퍼만 봅니다.")

    rows, component_list = [], None
    screens_path = os.path.join(design_dir, "screens.md")
    has_screens_html = any(os.path.basename(t) == SCREENS_FILE for t in targets)
    skipped = []
    if not has_screens_html:
        skip_reason = "{} 없음 (4단계 — 규칙 미리보기만 검사)".format(SCREENS_FILE)
    elif not os.path.isfile(screens_path):
        skip_reason = "screens.md 없음 (화면 구성표 확정 전)"
    else:
        skip_reason = None
        rows, component_list, w = parse_screens_md(screens_path)
        warnings.extend(w)
    if skip_reason:
        skipped = [{"rule": r, "reason": skip_reason} for r in SCREEN_RULES]
    if has_screens_html and not any(os.path.basename(t) == RULES_FILE for t in targets):
        warnings.append("{} 가 없어 건너뜁니다.".format(RULES_FILE))

    rendered, shots = {}, 0
    if render:
        rendered, shots, w = run_render(targets, th, shots_dir, scale, viewport)
        warnings.extend(w)

    ctx = {"tokens": tokens, "allow": allow, "excluded": excluded, "rows": rows,
           "component_list": component_list, "th": th, "skip_screens": bool(skip_reason),
           "rule_keys": frozenset(rules)}
    findings = []
    stats = {"files": [], "sections": 0, "frames": 0, "render": bool(render), "screenshots": shots,
             "viewport": viewport if render else None, "skipped": skipped,
             "tokensExpected": len(tokens), "iconAllowlist": len(allow or ()), "manifestScreens": len(rows)}
    for path in targets:
        if render:
            html, scopes = rendered[path]
        else:
            html, scopes = _read(path), None
        page = Page(path, html, th)
        stats["files"].append(page.name)
        stats["sections"] += len(page.sections)
        stats["frames"] += len(page.frames)
        if not render and page.has_script and page.name == SCREENS_FILE and not page.sections:
            warnings.append("{}: data-screen 섹션이 소스에 없고 <script> 가 있습니다 — 마크업을 JS 로 만든다면 "
                            "--render 로 렌더된 DOM 을 검사하세요.".format(page.name))
        findings.extend(static_findings(page, ctx))
        if scopes is not None:
            findings.extend(render_findings(page.name, scopes, th))
    findings.sort(key=lambda f: f.sort_key())
    return findings, warnings, stats


def write_fix_list(path, findings):
    lines = [
        "<!-- html_audit.py 자동 생성. 렌더러(probe-page) 수정 입력. 목록에 없는 것은 건드리지 않는다. -->",
        "",
        "# HTML Fix List",
        "",
        "화면이 `-` 인 결함(CSS 규칙·:root·파일 단위)은 화면 칸에 파일 이름을 적는다.",
        "",
        "| 화면 | 상태 | 요소 | 규칙 키 | 현재값 → 기대값 |",
        "|---|---|---|---|---|",
    ]
    for f in findings:
        screen = f.screen if f.screen != "-" else f.file
        lines.append("| {} | {} | {} | {} | {} |".format(
            _md(screen), _md(f.state), _md("{} ({})".format(f.node, f.selector)),
            _md(f.rule), _md("{} → {}".format(f.actual, f.expected))))
    if not findings:
        lines.append("| (없음) | - | - | - | - |")
    lines.append("")
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def _md(text):
    return str(text).replace("|", "\\|").replace("\n", " ")


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="html_audit.py",
        description="최종 HTML(final-preview·rules-preview)을 design-rules.md 기준으로 검사한다 (A단계).")
    parser.add_argument("--design-dir", default="design", help="design 폴더 (기본 design)")
    parser.add_argument("--render", action="store_true", help="playwright 로 렌더해 수치 검사 + 스크린샷")
    parser.add_argument("--json", action="store_true", help="결과를 JSON 으로 출력")
    parser.add_argument("--fix-list", dest="fix_list", help="결함 목록 마크다운 표 저장 경로")
    parser.add_argument("--screenshots", help="스크린샷 폴더 (기본 <design-dir>/screenshots/html)")
    parser.add_argument("--scale", type=float, default=2, help="스크린샷 배율 (기본 2)")
    parser.add_argument("--viewport", choices=["page", "device"], default="page",
                        help="page: 1280 폭 페이지에 배치(기본) / device: data-width 폭 뷰포트로 측정")
    args = parser.parse_args(argv)

    shots_dir = args.screenshots or os.path.join(args.design_dir, "screenshots", "html")
    try:
        findings, warnings, stats = run_audit(args.design_dir, args.render, shots_dir if args.render else None,
                                              args.scale, args.viewport)
    except RenderUnavailable as exc:
        print("[ERROR] {}".format(exc), file=sys.stderr)
        return 2
    except (AuditError, OSError, ValueError) as exc:
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
        by_rule[f.rule] = by_rule.get(f.rule, 0) + 1

    if args.json:
        print(json.dumps({
            "ok": not findings,
            "stats": stats,
            "failureCountByRule": by_rule,
            "findings": [f.as_dict() for f in findings],
            "warnings": warnings,
            "skipped": stats["skipped"],
        }, ensure_ascii=False, indent=2))
    else:
        for sk in stats["skipped"]:
            print("[SKIP] {} — {}".format(sk["rule"], sk["reason"]))
        for w in warnings:
            print("[WARN] {}".format(w))
        for f in findings:
            print(f.line())
        print("")
        summary = "파일 {}개 / 화면 섹션 {}개 / 상태 프레임 {}개".format(
            len(stats["files"]), stats["sections"], stats["frames"])
        if stats["render"]:
            summary += " / 스크린샷 {}장".format(stats["screenshots"])
        print(summary + " / 실패 {}건 ({}개 규칙)".format(len(findings), len(by_rule)))
        if findings:
            print("규칙별 실패: " + ", ".join("{} {}".format(k, v) for k, v in sorted(by_rule.items())))
        else:
            print("HTML A단계 통과." + ("" if stats["render"] else " (렌더 검사는 --render)"))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
