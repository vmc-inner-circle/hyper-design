"""agents/*.md 프론트매터가 TDR v2 16절 표와 같은지."""
from pathlib import Path

AGENTS = Path(__file__).resolve().parents[4] / "agents"

EXPECT = {
    "screen-writer": {"model": "sonnet", "effort": None, "tools": ["Read", "Write"]},
    "state-writer": {"model": "haiku", "effort": "low", "tools": ["Read", "Write"]},
    "fact-checker": {"model": "haiku", "effort": "low", "tools": ["Read"]},
    "screen-reviser": {"model": "haiku", "effort": "low", "tools": ["Read", "Edit"]},
}


def frontmatter(p):
    text = p.read_text(encoding="utf-8")
    assert text.startswith("---\n"), p
    _, fm, body = text.split("---\n", 2)
    meta = {}
    for ln in fm.splitlines():
        if not ln.strip():
            continue
        k, sep, v = ln.partition(":")
        assert sep and k.strip() and not ln.startswith(" "), (p.name, ln)
        v = v.strip()
        if len(v) >= 2 and v[0] == v[-1] == '"':
            assert '"' not in v[1:-1], (p.name, ln)
            v = v[1:-1]
        meta[k.strip()] = v
    return meta, body


def test_agent_files_match_table():
    files = {p.stem: p for p in AGENTS.glob("*.md")}
    assert set(EXPECT) <= set(files)
    for name, exp in EXPECT.items():
        meta, body = frontmatter(files[name])
        assert meta["name"] == name
        assert meta.get("description"), name
        assert meta["model"] == exp["model"], name
        assert meta.get("effort") == exp["effort"], name
        assert [t.strip() for t in meta["tools"].split(",")] == exp["tools"], name
        assert body.strip(), name


def test_screen_writer_body_is_writer_rules():
    writer = (Path(__file__).resolve().parents[1] / "writer.md").read_text(encoding="utf-8")
    rules = writer[writer.index("당신은"):].strip()
    _, body = frontmatter(AGENTS / "screen-writer.md")
    assert rules in body
