"""Fluent Emoji 전체 목록(index.json)을 만든다 — 하네스를 '만들 때' 1회. 구동 중에는 실행하지 않는다.

python3 build_index.py [--sha <커밋>]
→ index.json: [{"name","group","subgroup","keywords","unicode","file","person"}]  (file = 저장소 안 Color SVG 경로)

출처: https://github.com/microsoft/fluentui-emoji (MIT) — 각 assets/<이름>/metadata.json
소분류: https://unicode.org/Public/emoji/latest/emoji-test.txt 의 '# subgroup:'
사람(피부톤 변형이 있는 것)은 Medium-Light 변형 경로를 쓴다.
"""
import argparse, json, pathlib, re, sys, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor

HERE = pathlib.Path(__file__).resolve().parent
REPO = "microsoft/fluentui-emoji"
SHA = "1ffb34c752ecf5d402f04cfb4b392c77f57c54bc"   # 2026-08-24 main — 바꾸면 resolve.py의 SHA도 같이


def get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": "hyper-design-icons"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def raw(sha, path):
    return f"https://raw.githubusercontent.com/{REPO}/{sha}/" + urllib.parse.quote(path)


def subgroups():
    """코드포인트(소문자, 공백 구분) → 소분류."""
    out, sub = {}, ""
    for line in get("https://unicode.org/Public/emoji/latest/emoji-test.txt").decode("utf-8").splitlines():
        if line.startswith("# subgroup:"):
            sub = line.split(":", 1)[1].strip()
        elif line and not line.startswith("#") and "; fully-qualified" in line:
            cps = line.split(";")[0].strip().lower()
            out.setdefault(cps, sub)
            out.setdefault(cps.replace(" fe0f", ""), sub)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sha", default=SHA)
    a = ap.parse_args()
    tree = json.loads(get(f"https://api.github.com/repos/{REPO}/git/trees/{a.sha}?recursive=1"))
    if tree.get("truncated"):
        sys.exit("tree truncated — 목록이 잘렸다")
    paths = [x["path"] for x in tree["tree"] if x["type"] == "blob"]
    svgs = {p for p in paths if p.endswith(".svg") and "/Color/" in p}
    dirs = sorted({p.split("/")[1] for p in paths if p.startswith("assets/") and p.endswith("/metadata.json")})
    sub = subgroups()

    def one(d):
        m = json.loads(get(raw(a.sha, f"assets/{d}/metadata.json")))
        plain = [p for p in svgs if p.startswith(f"assets/{d}/Color/")]
        tone = [p for p in svgs if p.startswith(f"assets/{d}/Medium-Light/Color/")]
        f = (plain or tone or [None])[0]
        if not f:
            return None
        cps = m.get("unicode", "").lower()
        return {"name": re.sub(r"[^a-z0-9]+", "-", m.get("cldr", d).lower()).strip("-"),
                "group": m.get("group", ""), "subgroup": sub.get(cps, sub.get(cps.replace(" fe0f", ""), "")),
                "keywords": m.get("keywords", []), "unicode": cps, "file": f, "person": bool(tone and not plain)}

    with ThreadPoolExecutor(16) as ex:
        rows = [r for r in ex.map(one, dirs) if r]
    # 이름 충돌은 뒤에 오는 것에 번호
    seen = {}
    for r in rows:
        n = seen.get(r["name"], 0)
        seen[r["name"]] = n + 1
        if n:
            r["name"] = f"{r['name']}-{n + 1}"
    out = {"repo": REPO, "sha": a.sha, "count": len(rows), "emoji": rows}
    (HERE / "index.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"index.json: {len(rows)}개 (사람 {sum(r['person'] for r in rows)}, 소분류 없음 {sum(not r['subgroup'] for r in rows)})")


if __name__ == "__main__":
    main()
