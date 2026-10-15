"""icons 불변식 — 도메인 4개 × 불변식 4개. 네트워크는 항상 가짜(fetch 바꿔 끼우기)."""
import json, pathlib, sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import resolve  # noqa: E402

SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32"/></svg>'

DOMAINS = {
    "laundry": [(["laundry basket", "basket"], "basket"), (["washing machine", "bubbles"], "bubbles"),
                (["delivery truck"], "delivery-truck"), (["coat"], "coat")],
    "travel": [(["airplane"], "airplane"), (["hotel"], "hotel"), (["luggage"], "luggage")],
    "finance": [(["bank"], "bank"), (["credit card"], "credit-card"), (["money bag"], "money-bag")],
    "pets": [(["dog"], "dog"), (["cat"], "cat"), (["bone"], "bone")],
}

TIER0 = {m["name"] for m in resolve.load_manifest()}


@pytest.fixture
def cands():
    return resolve.candidates(resolve.load_index(), resolve.load_manifest())


@pytest.fixture
def fake_net(monkeypatch):
    calls = []

    def fetch(url, timeout):
        calls.append(url)
        return SVG
    monkeypatch.setattr(resolve, "fetch", fetch)
    return calls


@pytest.fixture
def no_net(monkeypatch):
    def fetch(url, timeout):
        raise AssertionError("network touched")
    monkeypatch.setattr(resolve, "fetch", fetch)


def make_out(tmp_path, domain, name="out"):
    out = tmp_path / name
    out.mkdir()
    slots = [{"slot": f"ic-{i}", "kind": "icon", "screens": ["home"], "what": f"{domain} {i}", "en": en}
             for i, (en, _) in enumerate(DOMAINS[domain])]
    slots.append({"slot": "photo-1", "kind": "photo", "what": "사진", "en": "a photo"})
    (out / "image_slots.json").write_text(json.dumps(slots), encoding="utf-8")
    (out / "decisions.json").write_text(json.dumps({"core": "keep"}), encoding="utf-8")
    return out


def load(p):
    return json.loads(p.read_text(encoding="utf-8"))


def check_invariants_1_2(out):
    icons = load(out / "icons.json")
    slot_entries = [e for e in icons if "slot" in e]
    files = {p.stem for p in (out / "assets" / "fluent").glob("*")}
    assert files <= TIER0 | {e["name"] for e in slot_entries}                     # 1
    slots = [s["slot"] for s in load(out / "image_slots.json") if s["kind"] == "icon"]
    assert [e["slot"] for e in slot_entries] == slots                                # 2
    assert all(e["source"] in ("resolved", "fallback") for e in slot_entries)
    dec = load(out / "decisions.json")
    assert dec["core"] == "keep"
    logged = {f["slot"]: f for f in dec.get("icon_fallbacks", [])}
    for e in slot_entries:
        assert (out / e["file"]).is_file()
        if e["source"] == "fallback":
            assert logged[e["slot"]]["used"] == e["name"]
    return slot_entries


@pytest.mark.parametrize("domain", sorted(DOMAINS))
def test_invariants_online(domain, tmp_path, fake_net):
    out = make_out(tmp_path, domain)
    resolve.main([str(out), "--cache", str(tmp_path / "cache")])
    entries = check_invariants_1_2(out)
    assert [e["name"] for e in entries] == [want for _, want in DOMAINS[domain]]
    assert all(e["source"] == "resolved" for e in entries)
    first = (out / "icons.json").read_bytes()
    resolve.main([str(out), "--cache", str(tmp_path / "cache")])                     # 3
    assert (out / "icons.json").read_bytes() == first
    out2 = make_out(tmp_path, domain, "out2")
    resolve.main([str(out2), "--cache", str(tmp_path / "cache")])
    assert (out2 / "icons.json").read_bytes() == first


@pytest.mark.parametrize("domain", sorted(DOMAINS))
def test_offline_empty_cache(domain, tmp_path, no_net):
    out = make_out(tmp_path, domain)
    assert resolve.main([str(out), "--cache", str(tmp_path / "empty"), "--offline"]) == 0  # 4
    entries = check_invariants_1_2(out)
    for (en, want), e in zip(DOMAINS[domain], entries):
        if want in TIER0:
            assert e["source"] == "resolved" and e["name"] == want
        else:
            assert e["source"] == "fallback" and e["name"] in TIER0
    assert all(f["why"] == "network" for f in load(out / "decisions.json").get("icon_fallbacks", []))


def test_offline_uses_seeded_cache(tmp_path, no_net):
    cache = tmp_path / "cache"
    cache.mkdir()
    for name in ("dog", "cat", "bone"):
        (cache / f"{name}.svg").write_bytes(SVG)
    out = make_out(tmp_path, "pets")
    resolve.main([str(out), "--cache", str(cache), "--offline"])
    assert all(e["source"] == "resolved" for e in check_invariants_1_2(out))


def test_network_error_and_oversize(tmp_path, monkeypatch):
    def boom(url, timeout):
        raise OSError("down")
    monkeypatch.setattr(resolve, "fetch", boom)
    out = make_out(tmp_path, "pets")
    assert resolve.main([str(out), "--cache", str(tmp_path / "c1")]) == 0
    assert all(e["source"] == "fallback" for e in check_invariants_1_2(out))
    monkeypatch.setattr(resolve, "fetch", lambda url, timeout: b"<svg>" + b"x" * resolve.MAX_BYTES)
    out = make_out(tmp_path, "pets", "out2")
    resolve.main([str(out), "--cache", str(tmp_path / "c2")])
    assert all(e["source"] == "fallback" for e in check_invariants_1_2(out))
    assert not list((tmp_path / "c2").glob("*.svg"))


def test_budget(tmp_path, fake_net):
    out = make_out(tmp_path, "pets")
    resolve.main([str(out), "--cache", str(tmp_path / "c"), "--timeout", "0"])
    check_invariants_1_2(out)
    assert {f["why"] for f in load(out / "decisions.json")["icon_fallbacks"]} == {"budget"}
    assert fake_net == []


def test_no_match_logged(tmp_path, no_net):
    out = tmp_path / "out"
    out.mkdir()
    (out / "image_slots.json").write_text(json.dumps(
        [{"slot": "ic-x", "kind": "icon", "what": "x", "en": ["zzqx"]}]), encoding="utf-8")
    resolve.main([str(out), "--offline"])
    dec = load(out / "decisions.json")
    assert dec["icon_fallbacks"] == [{"slot": "ic-x", "wanted": ["zzqx"], "used": "clipboard", "why": "no match"}]


def test_matcher(cands):
    name = lambda qs: (resolve.best(qs, cands) or {}).get("name")
    assert name(["washing machine"]) not in ("fax-machine", "slot-machine")
    assert name(["washing machine", "bubbles"]) == "bubbles"
    assert name(["dress shirt"]) != "dress"
    assert name(["laundry basket"]) == "basket"
    assert name(["delivery truck"]) == "delivery-truck"
    assert resolve.queries_of({"en": "coat"}) == ["coat"]
