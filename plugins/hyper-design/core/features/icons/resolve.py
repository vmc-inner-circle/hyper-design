"""아이콘 해석 — Tier 0 복사 + image_slots.json의 kind:icon 슬롯마다 Fluent 이모지 하나를 고른다.

python3 resolve.py <out> [--cache DIR] [--timeout 10] [--offline]
계약: contract.md. 도메인별 규칙은 두지 않는다 — 모든 도메인에 같은 매칭 규칙만 쓴다.
"""
import argparse, json, pathlib, re, shutil, sys, time, urllib.parse, urllib.request

HERE = pathlib.Path(__file__).resolve().parent
CORE = HERE / "core"
INDEX = HERE / "index.json"
MAX_BYTES = 300 * 1024
FALLBACK_DEFAULT = "clipboard"


def fetch(url, timeout):
    """네트워크 한 번. 테스트는 이 함수를 바꿔 끼운다."""
    req = urllib.request.Request(url, headers={"User-Agent": "hyper-design-icons"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(MAX_BYTES + 1)


def words(text):
    return [w for w in re.split(r"[^a-z0-9]+", str(text).lower()) if w]


def load_index():
    return json.loads(INDEX.read_text(encoding="utf-8"))


def load_manifest():
    return json.loads((CORE / "manifest.json").read_text(encoding="utf-8"))


def candidates(index, manifest):
    """이름 → {name, nw, kw, tier0, entry}. Tier 0 이름도 후보(색인에 있으면 그 키워드를 쓴다)."""
    by_name = {e["name"]: e for e in index["emoji"]}
    out = {}
    for e in index["emoji"]:
        kw = {w for k in e.get("keywords", []) for w in words(k)}
        out[e["name"]] = {"name": e["name"], "nw": set(e["name"].split("-")), "kw": kw, "tier0": False, "entry": e}
    for m in manifest:
        n = m["name"]
        e = by_name.get(n)
        kw = {w for k in (e or {}).get("keywords", []) for w in words(k)}
        out[n] = {"name": n, "nw": set(n.split("-")), "kw": kw, "tier0": True, "entry": e}
    return out


def score(q, c, head_rule=True):
    """None = 후보 아님. q = 질의 단어 목록."""
    if not q:
        return None
    qs = set(q)
    matched = (qs & c["nw"]) | (qs & c["kw"])
    if head_rule:
        head = q[-1]
        if head not in c["nw"] and head not in c["kw"]:
            return None
        # 중심 명사 하나만 겹치는 여러 단어 질의는 거절(washing machine → fax-machine 방지)
        if len(qs) > 1 and matched == {head}:
            return None
    s = 3 * len(qs & c["nw"]) + len(qs & c["kw"]) + (2 if c["name"] == "-".join(q) else 0)
    return s if s > 0 else None


def rank_key(s, c):
    return (-s, not c["tier0"], len(c["name"]), c["name"])


def best(queries, cands, head_rule=True, tier0_only=False):
    """선호 순서대로 첫 번째로 후보가 나온 질의의 최고 후보."""
    pool = [c for c in cands.values() if c["tier0"]] if tier0_only else list(cands.values())
    for q in queries:
        qw = words(q)
        scored = [(score(qw, c, head_rule), c) for c in pool]
        scored = [(s, c) for s, c in scored if s is not None]
        if scored:
            return min(scored, key=lambda t: rank_key(*t))[1]
    return None


def fallback(queries, cands):
    c = best(queries, cands, head_rule=False, tier0_only=True)
    return c["name"] if c else FALLBACK_DEFAULT


def queries_of(slot):
    en = slot.get("en") or []
    return [en] if isinstance(en, str) else [q for q in en if isinstance(q, str)]


def obtain(c, index, cache, deadline, offline):
    """Tier 2 파일을 캐시에 확보. 성공 → 캐시 경로, 실패 → ('network'|'budget')."""
    path = cache / f"{c['name']}.svg"
    if path.is_file() and path.stat().st_size <= MAX_BYTES:
        return path
    if offline:
        return "network"
    left = deadline - time.monotonic()
    if left <= 0:
        return "budget"
    f = c["entry"]["file"]
    if not f.endswith(".svg"):
        return "network"
    url = f"https://raw.githubusercontent.com/{index['repo']}/{index['sha']}/" + urllib.parse.quote(f)
    try:
        data = fetch(url, left)
    except Exception:
        return "budget" if time.monotonic() >= deadline else "network"
    if not data or len(data) > MAX_BYTES or b"<svg" not in data[:2048]:
        return "network"
    cache.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def run(out, cache=None, timeout=10.0, offline=False):
    out = pathlib.Path(out)
    index, manifest = load_index(), load_manifest()
    cache = pathlib.Path(cache) if cache else pathlib.Path.home() / ".cache" / "hyper-design" / "fluent" / index["sha"]
    dest = out / "assets" / "fluent"
    dest.mkdir(parents=True, exist_ok=True)
    for m in manifest:
        shutil.copyfile(CORE / m["file"], dest / f"{m['name']}.svg")
    tier0 = {m["name"]: m for m in manifest}
    cands = candidates(index, manifest)

    slots_path = out / "image_slots.json"
    slots = json.loads(slots_path.read_text(encoding="utf-8")) if slots_path.is_file() else []
    deadline = time.monotonic() + timeout
    entries, fallbacks = [], []
    for slot in slots:
        if not isinstance(slot, dict) or slot.get("kind") != "icon":
            continue
        qs = queries_of(slot)
        c = best(qs, cands)
        why = None
        if c is None:
            why = "no match"
        elif not c["tier0"]:
            got = obtain(c, index, cache, deadline, offline)
            if isinstance(got, str):
                why = got
            else:
                shutil.copyfile(got, dest / f"{c['name']}.svg")
        if why:
            name = fallback(qs, cands)
            kind, source = tier0.get(name, {}).get("kind", "object"), "fallback"
            fallbacks.append({"slot": slot.get("slot"), "wanted": qs, "used": name, "why": why})
        else:
            name, source = c["name"], "resolved"   # 슬롯 항목은 Tier 0에서 맞아도 resolved
            kind = tier0[name]["kind"] if c["tier0"] else ("person" if c["entry"].get("person") else "object")
        entries.append({"name": name, "file": f"assets/fluent/{name}.svg", "meaning": slot.get("what", ""),
                        "kind": kind, "source": source, "slot": slot.get("slot")})

    icons = [dict(m, file=f"assets/fluent/{m['name']}.svg") for m in manifest] + entries
    (out / "icons.json").write_text(json.dumps(icons, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    dec_path = out / "decisions.json"
    dec = json.loads(dec_path.read_text(encoding="utf-8")) if dec_path.is_file() else {}
    if fallbacks or "icon_fallbacks" in dec:
        done = {f["slot"] for f in fallbacks}
        dec["icon_fallbacks"] = [f for f in dec.get("icon_fallbacks", []) if f.get("slot") not in done] + fallbacks
        dec_path.write_text(json.dumps(dec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return entries, fallbacks


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Tier 0 아이콘 복사 + kind:icon 슬롯 해석 → out/icons.json")
    ap.add_argument("out")
    ap.add_argument("--cache", default=None, help="캐시 폴더 (기본 ~/.cache/hyper-design/fluent/<sha>/)")
    ap.add_argument("--timeout", type=float, default=10.0, help="전체 네트워크 상한(초)")
    ap.add_argument("--offline", action="store_true", help="네트워크를 쓰지 않는다")
    a = ap.parse_args(argv)
    entries, fallbacks = run(a.out, a.cache, a.timeout, a.offline)
    n = lambda s: sum(e["source"] == s for e in entries)
    print(f"icons: 슬롯 {len(entries)} (resolved {n('resolved')}, fallback {n('fallback')})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
