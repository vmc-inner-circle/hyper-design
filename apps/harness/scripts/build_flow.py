#!/usr/bin/env python3
"""flow-data.json + common/flow-renderer.html → design/probes/<out>.html (인라인 단일 파일)

검증을 먼저 하고 빌드한다. 하나라도 어긋나면 exit 1.
- 렌더러에 REPLACE 마커가 있는가 (없으면 데이터가 조용히 빠진 채 빌드된다)
- scenarios[].steps[].phoneId 가 phones에 있는가
- clickId 가 해당 phone의 컴포넌트/버튼/항목 id 중 하나인가
- 컴포넌트 type 이 렌더러가 아는 것인가
- icon 이 HTML이 아니라 클래스명인가

사용:
  python scripts/build_flow.py                       # 기본 경로
  python scripts/build_flow.py --data design/probes/flow-data-wedding.json --out design/probes/flow-wedding.html
"""
import argparse, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RENDERER = os.path.join(ROOT, ".claude", "skills", "oss-design-harness", "templates", "common", "flow-renderer.html")
MARKER = "/* REPLACE: DATA */\nvar DATA = null;"

KNOWN_TYPES = {"hero-action", "search", "hint", "card-list", "confirm", "badge-list",
               "compare", "loading", "fail", "empty", "disclaimer", "share-bar"}


def collect_ids(phone):
    ids = set()
    bar = phone.get("bar") or {}
    if bar.get("actionId"):
        ids.add(bar["actionId"])
    for c in phone.get("body", []):
        if c.get("id"):
            ids.add(c["id"])
        for b in c.get("buttons", []) or []:
            if b.get("id"):
                ids.add(b["id"])
        for it in c.get("items", []) or []:
            if it.get("id"):
                ids.add(it["id"])
    return ids


def defined_icons(renderer_css, data_css):
    """렌더러 <style>과 DATA.css에 정의된 .i-* 클래스 집합"""
    return set(re.findall(r"\.(i-[a-z0-9-]+)\s*\{", renderer_css + "\n" + (data_css or "")))


def validate(data, renderer=""):
    errs = []
    phones = data.get("phones", {})
    icons_ok = defined_icons(renderer, data.get("css", ""))
    for si, sc in enumerate(data.get("scenarios", [])):
        for ti, st in enumerate(sc.get("steps", [])):
            where = f"scenarios[{si}].steps[{ti}] ({st.get('title', '?')})"
            pid = st.get("phoneId")
            if pid not in phones:
                errs.append(f"{where}: phoneId '{pid}' 가 phones에 없음")
                continue
            cid = st.get("clickId")
            if cid and cid not in collect_ids(phones[pid]):
                errs.append(f"{where}: clickId '{cid}' 가 phones['{pid}'] 안에 없음")
    for pid, ph in phones.items():
        if isinstance(ph, str):
            # 렌더러는 아직 raw HTML도 그리므로 막지는 않는다. 다만 새 데이터는 선언적으로 쓴다.
            print(f"[WARN] phones['{pid}']: raw HTML 문자열 (레거시). 선언적 컴포넌트로 전환 권장", file=sys.stderr)
            continue
        for c in ph.get("body", []):
            t = c.get("type")
            if t not in KNOWN_TYPES:
                errs.append(f"phones['{pid}']: 모르는 type '{t}' (허용: {sorted(KNOWN_TYPES)})")
            ic = c.get("icon")
            if isinstance(ic, str) and ic.lstrip().startswith("<"):
                errs.append(f"phones['{pid}']: icon 에 HTML 이 들어감 — 클래스명만 ('i-cam')")
            elif ic and ic not in icons_ok:
                errs.append(f"phones['{pid}']: icon '{ic}' 가 어디에도 정의되지 않음 — 렌더러 기본({sorted(i for i in icons_ok)}) 외 아이콘은 DATA.css 에 .{ic}{{background-image:…}} 로 정의")
    return errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.path.join(ROOT, "design", "probes", "flow-data.json"))
    ap.add_argument("--out", default=os.path.join(ROOT, "design", "probes", "flow-animated.html"))
    ap.add_argument("--renderer", default=RENDERER)
    a = ap.parse_args()

    with open(a.renderer, encoding="utf-8") as f:
        renderer = f.read()
    if MARKER not in renderer:
        print(f"[FAIL] 렌더러에 마커가 없음: {MARKER!r}\n       {a.renderer}", file=sys.stderr)
        return 1

    with open(a.data, encoding="utf-8") as f:
        raw = f.read()
    data = json.loads(raw)

    errs = validate(data, renderer)
    if errs:
        for e in errs:
            print(f"[FAIL] {e}", file=sys.stderr)
        return 1

    html = renderer.replace(MARKER, f"/* {data.get('title', '')} — build_flow.py */\nvar DATA = {raw.strip()};")
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(html)

    n_sc = len(data["scenarios"])
    n_st = sum(len(s["steps"]) for s in data["scenarios"])
    print(f"[OK] {os.path.relpath(a.out, ROOT)}  시나리오 {n_sc} · 장면 {n_st} · 화면 {len(data['phones'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
