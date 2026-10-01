"""기능 커버·구조 검사 (v7 엔진). 사람 없이 돌리는 A단계.

    python scripts/coverage.py design/app/app.json

검사: ① features 의 모든 기능이 최소 1개 화면에 연결(screens[].features)되고 그 화면이 실제 블록을 가짐
      ② 모든 "to" 가 있는 화면을 가리킴(끊긴 링크 0) ③ 모든 화면이 내비 또는 다른 화면에서 도달 가능(고아 0)
      ④ 역할마다 내비 2~5개 ⑤ 필수 흐름 태그(flows) — 처음 시작/초대/빈 상태 가 화면 id 로 있는지
      ⑥ 이모지 아이콘·가짜 상태바 문자열 없음 ⑦ 색 토큰 대비(본문 ink/bg ≥ 4.5)
통과하면 "PASS", 아니면 고칠 목록과 함께 "FAIL" (종료 코드 1).
"""
import json
import pathlib
import re
import sys

EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")


def lum(h):
    h = h.lstrip("#")
    if len(h) != 6:
        return None
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def walk(blocks):
    for b in blocks or []:
        yield b
        for k in ("items", "blocks", "cols", "fields"):
            v = b.get(k)
            if isinstance(v, list):
                for x in v:
                    if isinstance(x, dict):
                        yield x
                        yield from walk(x.get("items") if isinstance(x.get("items"), list) and x.get("items") and isinstance(x["items"][0], dict) else [])
        if b.get("t") == "sheet":
            yield from walk(b.get("blocks"))


def main():
    spec = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
    ids = {s["id"] for s in spec["screens"]}
    probs = []
    for f in spec.get("features", []):
        ss = [s for s in spec["screens"] if f["id"] in s.get("features", []) and s.get("blocks")]
        if not ss:
            probs.append(f"기능 {f['id']} {f['name']}: 연결된 화면 없음")
    if not spec.get("features"):
        probs.append("features(PRD 기능 요구사항 목록)가 비어 있음")
    reach = set()
    for r in spec.get("roles", []):
        nav = [n for n in r.get("nav", []) if n in ids]
        reach |= set(nav)
        if not 2 <= len(nav) <= 5:
            probs.append(f"역할 {r['id']}: 내비 {len(nav)}개(2~5개여야)")
    for s in spec["screens"]:
        for b in walk(s.get("blocks", []) + s.get("side", [])):
            tos = [b["to"]] if b.get("to") else []
            if b.get("t") == "html":  # 직접 그린 화면: href="#화면id" 도 링크로 본다
                tos += re.findall(r'href="#([\w-]+)"', b.get("html", ""))
            for to in tos:
                if to not in ids:
                    probs.append(f"화면 {s['id']}: 끊긴 링크 → {to}")
                reach.add(to)
            txt = json.dumps(b, ensure_ascii=False)
            if b.get("icon") and EMOJI.search(str(b.get("icon"))):
                probs.append(f"화면 {s['id']}: 이모지 아이콘 {b.get('icon')}")
            if re.search(r"\b9:41\b", txt):
                probs.append(f"화면 {s['id']}: 가짜 상태바 문자열")
    for s in spec["screens"]:
        if s["id"] not in reach and s["id"] != spec["screens"][0]["id"]:
            probs.append(f"화면 {s['id']}: 어디서도 갈 수 없음(내비나 다른 화면의 to 로 연결)")
    css_lines = [x for x in spec.get("style", "").replace("}", "}\n").splitlines() if x.strip()]
    if len(css_lines) < 30:
        probs.append(f"디자인 시스템 CSS(design/app/style.css)가 {len(css_lines)}줄 — 이 서비스만의 디테일이 없다(30줄 이상, SKILL '디테일로 와우')")
    flows = spec.get("flows", {})
    for need in ("onboarding", "invite", "empty"):
        if not flows.get(need) or flows[need] not in ids:
            probs.append(f"필수 흐름 {need}: flows.{need} 에 화면 id 가 없음")
    t = spec.get("tokens", {})
    li, lb = lum(t.get("ink", "#1D2320")), lum(t.get("bg", "#F7F7F5"))
    if li is not None and lb is not None:
        hi, lo = max(li, lb), min(li, lb)
        if (hi + 0.05) / (lo + 0.05) < 4.5:
            probs.append("본문 글자/배경 대비 4.5 미만")
    n = len(spec["screens"])
    print(f"화면 {n}장 · 기능 {len(spec.get('features', []))}개 · 역할 {len(spec.get('roles', []))}개")
    if probs:
        print("FAIL")
        for p in probs:
            print(" -", p)
        sys.exit(1)
    print("PASS")


if __name__ == "__main__":
    main()
