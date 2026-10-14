"""fix 스킬 계약 테스트 — frontmatter, 참조, 요청문 예시가 canvas_template.html 형식과 맞는지."""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE / "SKILL.md"
TEMPLATE = HERE.parents[1] / "core" / "features" / "canvas" / "canvas_template.html"

HEADER_RE = re.compile(r"^\[hyper-design 수정 요청\] out=.+ · \d+건$")
ITEM_RE = re.compile(r"^(\d+)\. screen=[^\s·]+ · path=.+$")
TEXT_RE = re.compile(r'^   text=".*" · intent=(change|question)$')
NOTE_RE = re.compile(r"^   요청: .+$")


def _split():
    src = SKILL.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", src, re.S)
    assert m, "frontmatter missing"
    fm = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(":")
        fm[k.strip()] = v.strip()
    return fm, m.group(2)


def _example():
    _, body = _split()
    for block in re.findall(r"```\n(.*?)```", body, re.S):
        lines = block.rstrip("\n").splitlines()
        if lines and lines[0].startswith("[hyper-design 수정 요청]"):
            return lines
    raise AssertionError("no example request block")


def test_frontmatter():
    fm, _ = _split()
    assert fm["name"] == "fix"
    assert "[hyper-design 수정 요청]" in fm["description"]


def test_body_refs():
    _, body = _split()
    for s in ("pack.py", "--mode revise", "hyper-design:screen-reviser", "selfcheck.py", "build_canvas.py"):
        assert s in body, s
    assert 'model: "opus"' not in body
    assert len(SKILL.read_text(encoding="utf-8").splitlines()) <= 80


def test_example_matches_canvas_format():
    lines = _example()
    assert HEADER_RE.match(lines[0]), lines[0]
    n = int(re.search(r"(\d+)건$", lines[0]).group(1))
    items = lines[1:]
    assert len(items) == 3 * n
    for i in range(n):
        m = ITEM_RE.match(items[3 * i])
        assert m and int(m.group(1)) == i + 1, items[3 * i]
        assert TEXT_RE.match(items[3 * i + 1]), items[3 * i + 1]
        assert NOTE_RE.match(items[3 * i + 2]), items[3 * i + 2]
    intents = {TEXT_RE.match(items[3 * i + 1]).group(1) for i in range(n)}
    assert intents == {"change", "question"}


def test_template_emits_same_format():
    js = TEMPLATE.read_text(encoding="utf-8")
    nl = chr(92) + "n"  # JS source escape for newline
    for frag in ("'[hyper-design 수정 요청] out=' + outDir() + ' · ' + list.length + '건" + nl + "'",
                 "'. screen=' + n.screen + ' · path=' + n.path + '" + nl + "   text=\"'",
                 "'\" · intent=' + n.intent",
                 "'" + nl + "   요청: '"):
        assert frag in js, frag
