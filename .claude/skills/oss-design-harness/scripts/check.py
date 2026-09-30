"""design/ 산출물 자체 점검. 사용자에게 보여주기 전에 실행하고, [FAIL]이 없어야 넘어간다.

사용법:
    python .claude/skills/oss-design-harness/scripts/check.py --root design
"""

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

MIN_DATA_ID = 3
DEVICES = Path(__file__).resolve().parents[1] / "schema" / "devices.json"
STACK = Path(__file__).resolve().parents[1] / "schema" / "stack.json"  # 화면 머리 외부 자원(CDN)의 계층·상태
BOARD_KEYS = {"title", "round", "devices", "rows", "screens", "arrows", "flows"}
# 토큰 밖 값: 임의 값(bg-[#..], text-[13px]) · Tailwind 기본 팔레트(bg-gray-400, bg-white) — theme.js의 이름만 쓴다 (screen-generation.md §토큰)
OFF_TOKEN = re.compile(r"(?<![\w-])(?:[a-z]+:)*(?:[a-z-]+-\[[^\]\s]+\]"
                       r"|(?:bg|text|border|ring|fill|stroke|from|to|via|outline|divide|decoration|shadow)-(?:white|black"
                       r"|(?:slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose)-\d{2,3}))(?![\w-])")


class LooseLinks(HTMLParser):
    """data-id 요소 안에 있지 않은 화면 링크(<a href="*.html">) 수를 센다."""

    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}

    def __init__(self):
        super().__init__()
        self.stack, self.loose = [], 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        inside = any(has_id for _, has_id in self.stack) or "data-id" in a
        if tag == "a" and re.fullmatch(r"[^#:]+\.html", a.get("href") or "") and not inside:
            self.loose += 1
        if tag not in self.VOID:
            self.stack.append((tag, "data-id" in a))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    @classmethod
    def count(cls, html):
        p = cls()
        p.feed(html)
        return p.loose


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="design")
    root = Path(ap.parse_args().root)
    fails, warns = [], []

    board_path = root / "board.json"
    if not board_path.exists():
        print(f"[FAIL] {board_path} 없음")
        sys.exit(1)
    board = json.loads(board_path.read_text(encoding="utf-8"))
    screens = board.get("screens", [])
    ids = {s["id"] for s in screens}

    stack = json.loads(STACK.read_text(encoding="utf-8")) if STACK.exists() else {"layers": [], "resources": []}
    layer_rank = {l["id"]: i for i, l in enumerate(stack["layers"])}

    # 기기: devices.json의 키만 허용 (board.schema.json의 enum과 같음)
    devices = {k for k in json.loads(DEVICES.read_text(encoding="utf-8")) if not k.startswith("$")}
    board_devices = board.get("devices", ["mobile"])
    for d in board_devices:
        if d not in devices:
            fails.append(f"board.devices: 모르는 기기 '{d}' (가능: {', '.join(sorted(devices))})")
    for key in set(board) - BOARD_KEYS:
        fails.append(f"board.json: 모르는 항목 '{key}' (오타?)")

    board_files = {(root / s["file"]).resolve() for s in screens}
    dup = sorted({s.get("id") for s in screens if [x.get("id") for x in screens].count(s.get("id")) > 1})
    if dup:
        fails.append(f"화면 id 중복: {', '.join(map(str, dup))}")
    for s in screens:
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", s.get("id", "")):
            fails.append(f"{s.get('id')}: 화면 id는 영문 소문자·숫자·하이픈만")
        want = s.get("devices", board_devices)
        for d in want:
            if d not in devices:
                fails.append(f"{s['id']}: 모르는 기기 '{d}'")
        f = root / s["file"]
        if not f.exists():
            fails.append(f"{s['id']}: 파일 없음 {s['file']}")
            continue
        html = f.read_text(encoding="utf-8")
        m = re.search(r'<html[^>]*\bdata-devices="([^"]*)"', html)
        declared = m.group(1).split() if m else []
        missing = [d for d in want if d not in declared]
        if missing:
            fails.append(f"{s['id']}: <html data-devices>에 {', '.join(missing)} 없음 (board.json과 맞출 것)")
        # 머리의 외부 자원: stack.json의 active만, 계층 순서대로, retired는 금지
        head = html.lower().split("</head>")[0]
        pos = []
        for r in stack["resources"]:
            at = head.find(r["match"].lower())
            if r["status"] == "retired" and at >= 0:
                fails.append(f"{s['id']}: 쓰지 않는 자원 {r['id']} ({r['match']}) — stack.json에서 retired")
            elif r["status"] == "candidate" and at >= 0:
                warns.append(f"{s['id']}: 시험 중인 자원 {r['id']} — stack.json에서 candidate (쓰려면 active로)")
            elif r["status"] == "active":
                if at < 0:
                    warns.append(f"{s['id']}: 머리에 {r['id']} 없음 ({r['layer']} 계층, stack.json)")
                else:
                    pos.append((at, layer_rank.get(r["layer"], 99), r["id"]))
        ranks = [rank for _, rank, _ in sorted(pos)]
        if ranks != sorted(ranks):
            warns.append(f"{s['id']}: 머리 자원 순서가 계층과 다름 — {' → '.join(i for _, _, i in sorted(pos))} (stack.json layers 순서대로)")
        off = sorted({m.group(0) for c in re.findall(r'class="([^"]*)"', html) for m in OFF_TOKEN.finditer(c)})
        if off:
            warns.append(f"{s['id']}: 토큰 밖 값 {len(off)}종 — {' '.join(off[:5])}{' …' if len(off) > 5 else ''} (theme.js 이름으로)")
        if "viewport" not in html:
            warns.append(f"{s['id']}: viewport 메타 없음")
        if "desktop" in want and re.search(r'class="[^"]*\bfixed\b(?![^"]*\blg:hidden\b)', html):
            warns.append(f"{s['id']}: PC 칸에서 보이는 position:fixed 요소 — PC는 내용 길이만큼 늘어나 가운데 뜰 수 있음")
        n = len(re.findall(r'data-id="', html))
        if n < MIN_DATA_ID:
            fails.append(f"{s['id']}: data-id {n}개 (최소 {MIN_DATA_ID}) — 코멘트가 요소에 연결되지 않음")
        for href in re.findall(r'href="([^"#:]+\.html)"', html):
            target = (f.parent / href).resolve()
            if not target.exists():
                fails.append(f"{s['id']}: 깨진 링크 {href}")
            elif target not in board_files:
                warns.append(f"{s['id']}: {href}는 board.json에 없음 — 보드에 '(링크에서 발견)'으로 올라감. 정식 화면이면 board.json에 넣을 것")
        # 관계 화살표는 링크가 든 data-id 컴포넌트에서 출발한다 → data-id 밖의 링크는 화면 테두리에서 출발
        loose = LooseLinks.count(html)
        if loose:
            warns.append(f"{s['id']}: data-id 밖의 링크 {loose}개 — 관계 화살표가 컴포넌트가 아닌 화면 테두리에서 나감")
        if "lorem" in html.lower():
            warns.append(f"{s['id']}: lorem ipsum 더미 텍스트")

    for a in board.get("arrows", []):
        for k in ("from", "to"):
            if a.get(k) not in ids:
                fails.append(f"화살표 {a.get('from')}→{a.get('to')}: 없는 화면 {a.get(k)}")

    # 흐름: 흐름 지도·흐름 줄의 단위. 없으면 캔버스가 줄(row) 배치로 보여준다
    flows = board.get("flows") or []
    if not flows:
        warns.append("flows 없음 — 캔버스가 줄 배치로 보여줌. 흐름 지도·완성본을 쓰려면 flows를 넣을 것 (references/canvas.md)")
    fids, in_flow = [], set()
    for f in flows:
        fids.append(f.get("id"))
        if not f.get("title"):
            fails.append(f"흐름 {f.get('id')}: title(목적 한 문장) 없음")
        for sid in f.get("steps", []):
            if sid not in ids:
                fails.append(f"흐름 {f.get('id')}: 없는 화면 {sid}")
            in_flow.add(sid)
    for dup_f in sorted({x for x in fids if fids.count(x) > 1}, key=str):
        fails.append(f"흐름 id 중복: {dup_f}")
    if flows:
        for s in screens:
            if s["id"] not in in_flow:
                warns.append(f"{s['id']}: 어느 흐름에도 없음 — 보드 맨 아래 '어느 흐름에도 없는 화면' 줄로 감")
            if not s.get("purpose"):
                warns.append(f"{s['id']}: purpose(화면 목적 한 줄) 없음")

    if not (root / "components.md").exists():
        warns.append("components.md 없음 — 화면 전에 컴포넌트(영역·요소)를 먼저 정의할 것")
    if not (root / "index.html").exists():
        warns.append("index.html 없음 (마무리 전까지 만들 것)")

    for w in warns:
        print(f"[WARN] {w}")
    for f in fails:
        print(f"[FAIL] {f}")
    print(f"화면 {len(screens)}개 · 화살표 {len(board.get('arrows', []))}개 · FAIL {len(fails)} · WARN {len(warns)}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
