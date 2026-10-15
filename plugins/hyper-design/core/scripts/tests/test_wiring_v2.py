"""harness v2 배선 — expand_states 기본값 · setup_out Tier 0 복사 · selfcheck(icons.json 사람·생성 이미지) · SKILL.md 문구."""
import json, os, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent
CORE = SCRIPTS.parent
PLUGIN = CORE.parent
TIER0 = CORE / "features" / "icons" / "core"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")


def run(script, *args):
    return subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, args)],
                          capture_output=True, text=True, encoding="utf-8", env=ENV)


def wjson(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")


# 1. expand_states 기본값
def test_expand_states_fills_defaults_idempotent(tmp_path):
    screens = [{"id": f"s{i}", "title": f"화면 {i}", "group": "g", "purpose": "p", "kind": "detail", "policies": ["x"]}
               for i in range(3)]
    screens[1]["traits"] = {"shares": True}
    screens[2]["role"] = "editor"
    wjson(tmp_path / "screens.json", {"groups": ["g"], "screens": screens})
    r = run("expand_states.py", tmp_path, "--stage", "go")
    assert r.returncode == 0, r.stdout + r.stderr
    first = (tmp_path / "screens.json").read_bytes()
    M = json.loads(first)
    keys = {"list_first_use", "form", "shares", "large_list", "long_task"}
    base = [s for s in M["screens"] if "--" not in s["id"]]
    assert len(base) == 3
    for s in base:
        assert s["file"] == f"screens/{s['id']}.html"
        assert set(s["traits"]) == keys
    by = {s["id"]: s for s in M["screens"]}
    assert by["s0"]["role"] == "everyone" and by["s2"]["role"] == "editor"
    assert by["s1"]["traits"]["shares"] is True and by["s1"]["traits"]["form"] is False
    assert "s1--done" in by and by["s1"]["states"] == ["done"]
    r = run("expand_states.py", tmp_path, "--stage", "go")
    assert r.returncode == 0
    assert (tmp_path / "screens.json").read_bytes() == first


# 2. setup_out — Tier 0만 out/assets/fluent/로
def test_setup_out_copies_tier0(tmp_path):
    out = tmp_path / "out"
    r = run("setup_out.py", out, "--domain", "생활", "--tags", "생활")
    assert r.returncode == 0, r.stdout + r.stderr
    got = {p.name for p in (out / "assets" / "fluent").iterdir()}
    want = {p.name for p in TIER0.iterdir() if p.suffix == ".svg"} | {"LICENSE.md"}
    assert got == want
    assert "luggage.svg" not in got and "manifest.json" not in got


# 3. selfcheck — icons.json의 사람 · 생성 이미지 credits
def test_selfcheck_icons_person_and_generated_credits(tmp_path):
    out = tmp_path
    page = ('<!doctype html><html><head><link id="tokens" rel="stylesheet" href="../tokens.css">'
            '<script src="../palette.js"></script></head><body><h1>홈</h1>'
            '<span class="avatar"><img src="../assets/fluent/bust-in-silhouette.svg" alt=""></span>'
            '<span class="avatar"><img src="../assets/fluent/delivery-truck.svg" alt=""></span>'
            '</body></html>')
    (out / "screens").mkdir()
    (out / "screens" / "home.html").write_text(page, encoding="utf-8")
    wjson(out / "screens.json", {"screens": [{"id": "home", "file": "screens/home.html", "title": "홈", "group": "g",
                                              "purpose": "p", "policies": ["x"], "states": [], "traits": {}}]})
    wjson(out / "icons.json", [{"name": "bust-in-silhouette", "file": "bust-in-silhouette.svg", "kind": "person"},
                               {"name": "delivery-truck", "file": "delivery-truck.svg", "kind": "object"}])
    (out / "assets" / "photos").mkdir(parents=True)
    (out / "assets" / "photos" / "gen.jpg").write_bytes(b"x")
    (out / "assets" / "photos" / "nocredit.jpg").write_bytes(b"x")
    wjson(out / "credits.json", [{"slot": "gen", "file": "assets/photos/gen.jpg", "author": "AI 생성 (codex image_generation)",
                                  "license": "generated", "url": "", "title": "t"}])
    r = run("selfcheck.py", out)
    txt = r.stdout
    assert "사물 일러스트 delivery-truck" in txt
    assert "사물 일러스트 bust-in-silhouette" not in txt
    assert "assets/photos/nocredit.jpg: credits.json에 출처 없음" in txt
    assert "assets/photos/gen.jpg" not in txt


# 4. SKILL.md 문구
def test_skill_md_wiring():
    go = (PLUGIN / "skills" / "go" / "SKILL.md").read_text(encoding="utf-8")
    for s in ("features/pack/pack.py", "hyper-design:screen-writer", "features/images/imggen.py",
              "features/icons/resolve.py", "hyper-design:fact-checker", "/hyper-design:fix"):
        assert s in go, s
    assert "imgsearch.py" not in go
    mx = (PLUGIN / "skills" / "max" / "SKILL.md").read_text(encoding="utf-8")
    assert "hyper-design:state-writer" in mx


# 1b. 목록 화면은 large_list를 채우지 않는다 — selfcheck가 미선언을 잡는다
def test_list_screen_large_list_stays_undeclared(tmp_path):
    wjson(tmp_path / "screens.json", {"groups": ["g"], "screens": [
        {"id": "lst", "title": "목록", "group": "g", "purpose": "p", "kind": "list", "policies": ["x"]},
        {"id": "lst2", "title": "목록2", "group": "g", "purpose": "p", "kind": "list", "policies": ["x"],
         "traits": {"large_list": True}}]})
    r = run("expand_states.py", tmp_path, "--stage", "go")
    assert r.returncode == 0, r.stdout + r.stderr
    by = {s["id"]: s for s in json.loads((tmp_path / "screens.json").read_text(encoding="utf-8"))["screens"]}
    assert "large_list" not in by["lst"]["traits"]
    assert set(by["lst"]["traits"]) == {"list_first_use", "form", "shares", "long_task"}
    assert by["lst2"]["traits"]["large_list"] is True
    txt = run("selfcheck.py", tmp_path).stdout
    assert "lst: traits.large_list(30개 넘게 쌓이는 목록인가) 미선언" in txt
    assert "lst2: traits.large_list" not in txt
