"""레퍼런스(실제 유명 사이트의 디자인 시스템) — K14 (2026-10-12).

    python scripts/refs.py ask design/ask/q1.json --recommend dark-tech,mono [--title "…"]
        # 분위기 12가지 질문 페이지 JSON(항목 1개, 여러 개 고르기)을 만든다. 그다음 ask.py 로 HTML.
    python scripts/refs.py pick dark-tech,mono [--n 5]
        # 고른 분위기에서 레퍼런스 사이트 n곳(분위기를 고르게 돌며, 국내·해외 섞어서) → 벌마다 읽을 파일 경로
    python scripts/refs.py list                    # 분위기·사이트 목록

refs/categories.json · refs/cat-<id>.jpg(-d) · refs/design/<site>.md(DESIGN.md) · refs/shots/<site>-m.jpg(-d).
DESIGN.md 는 공개 CSS 값에서 뽑은 '수치와 규칙' — 로고·문구·사진·브랜드 이름은 가져오지 않는다.
"""
import json
import pathlib
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
R = pathlib.Path(__file__).resolve().parent.parent / "refs"
KR = {"toss", "tossbank", "kakaobank", "banksalad", "daangn", "baemin", "kurly", "29cm", "musinsa", "kakao", "naver", "socar", "myrealtrip", "zigbang", "class101"}


def cats():
    return json.loads((R / "categories.json").read_text(encoding="utf-8"))["categories"]


def has(s):
    return (R / "design" / f"{s}.md").exists()


def main():
    a = sys.argv[1:]
    C = cats()
    if not a or a[0] == "list":
        for c in C:
            print(f'{c["id"]:<15} {c["name"]} — {c["desc"]}\n                {", ".join(c["siteNames"][s] + ("" if has(s) else "(문서 없음)") for s in c["sites"])}')
        return
    if a[0] == "ask":
        out = pathlib.Path(a[1])
        rec = a[a.index("--recommend") + 1] if "--recommend" in a else C[0]["id"]
        title = a[a.index("--title") + 1] if "--title" in a else "어떤 분위기로 만들까요?"
        opts = [{"id": c["id"], "label": c["name"], "desc": c["desc"] + " · 예: " + ", ".join(c["siteNames"][s] for s in c["sites"][:5]),
                 "img": f"../../refs/cat-{c['id']}.jpg", "img2": f"../../refs/cat-{c['id']}-d.jpg"} for c in C]
        q = {"n": 1, "of": 1, "title": title,
             "lead": "이 페이지에서 마음에 드는 분위기만 골라 주시면 끝이에요. 고른 분위기의 실제 유명 서비스 디자인을 바탕으로, 서로 다른 디자인 5벌을 15분쯤 뒤에 나란히 보여 드릴게요. 그림은 그 분위기의 실제 사이트 화면이에요.",
             "items": [{"id": "a", "kind": "pick", "multi": True, "q": "마음에 드는 분위기를 모두 골라 주세요",
                        "why": "하나만 골라도, 여러 개 골라도 돼요. 추천은 이 서비스를 쓰는 사람과 상황에 맞춰 골랐어요.",
                        "recommend": rec, "options": opts}]}
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(q, ensure_ascii=False, indent=1), encoding="utf-8")
        print(out)
        return
    if a[0] == "pick":
        ids = [x for x in a[1].split(",") if x]
        n = int(a[a.index("--n") + 1]) if "--n" in a else 5
        by = {c["id"]: c for c in C}
        pools = [[s for s in by[i]["sites"] if has(s)] for i in ids if i in by]
        # 분위기를 돌아가며 하나씩, 같은 분위기 안에서는 국내·해외를 번갈아
        for p in pools:
            kr = [s for s in p if s in KR]
            fx = [s for s in p if s not in KR]
            p[:] = [x for pair in zip(fx, kr) for x in pair] + fx[len(kr):] + kr[len(fx):]
        got, k = [], 0
        while len(got) < n and any(pools):
            p = pools[k % len(pools)]
            while p and p[0] in got:
                p.pop(0)
            if p:
                got.append(p.pop(0))
            k += 1
        cat_of = {s: c["id"] for c in C for s in c["sites"]}
        names = {s: n_ for c in C for s, n_ in c["siteNames"].items()}
        for i, s in enumerate(got, 1):
            print(f'v{i}: {names[s]}({s}) · 분위기 {cat_of[s]} · 문서 refs/design/{s}.md · 화면 refs/shots/{s}-m.jpg, refs/shots/{s}-d.jpg')
        if len(got) < n:
            print(f"(고른 분위기에서 {len(got)}곳만 — 나머지 {n - len(got)}벌은 고른 분위기의 설명을 바탕으로 하네스가 자유롭게)")
        return
    print(__doc__)


if __name__ == "__main__":
    main()
