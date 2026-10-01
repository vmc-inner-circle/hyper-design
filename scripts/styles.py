"""스타일 라이브러리 (v7 엔진, 09-28). 같은 화면을 성격이 다른 스타일로 입혀 개성 후보를 만든다.

    python scripts/styles.py list                                       # 스타일 10종: id · 이름 · 성격(요즘 유행/오래 가는/과감한/따뜻한) · 느낌
    python scripts/styles.py try <화면.json> <id> <id> … [--palette 1] [--out design/cand]
        # <화면.json> = app.py 형식(화면 1~3장). 스타일마다 tokens(글꼴·모서리·색)+CSS 를 입혀
        #   design/cand/style-<id>.json · .css · .html 을 만들고, 폰·PC 캡처 style-<id>.png / -d.png 까지 찍는다.
    python scripts/styles.py use <id> [--palette 0] > design/app/tokens-<id>.json   # 고른 스타일의 tokens 를 base.json 에 넣을 모양으로
        # 그리고 cp styles/<id>.css design/app/style.css 로 시작해서 이 서비스에 맞게 고친다(은유·시그니처 디테일 추가).

css 는 엔진 부품 클래스를 다시 입히는 레시피이고 색은 tokens 변수를 따른다 — palette 를 바꾸거나 accent 만 바꿔도 된다.
"""
import json
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
LIB = HERE.parent / "styles"
KEYS = ["bg", "surface", "ink", "muted", "line", "accent", "accent2", "accent3", "accent4"]


def lib():
    return {s["id"]: s for s in json.loads((LIB / "index.json").read_text(encoding="utf-8"))["styles"]}


def tokens_of(st, pal=0):
    t = dict(st["tokens"])
    p = st["palettes"][min(pal, len(st["palettes"]) - 1)]
    t.update(dict(zip(KEYS, p)))
    t.setdefault("accentInk", "#FFFFFF" if not st["tokens"].get("dark") else p[0])
    return t


def main():
    a = sys.argv[1:]
    L = lib()
    if not a or a[0] == "list":
        for s in L.values():
            print(f'{s["id"]:<10} {s["name"]:<10} [{s["tag"]}] {s["look"]} · 시그니처: {", ".join(s["signature"])}')
        return
    pal = int(a[a.index("--palette") + 1]) if "--palette" in a else 0
    if a[0] == "use":
        print(json.dumps(tokens_of(L[a[1]], pal), ensure_ascii=False, indent=1))
        return
    if a[0] == "try":
        src = pathlib.Path(a[1])
        out = pathlib.Path(a[a.index("--out") + 1]) if "--out" in a else pathlib.Path("design/cand")
        out.mkdir(parents=True, exist_ok=True)
        ids = [x for x in a[2:] if x in L]
        spec0 = json.loads(src.read_text(encoding="utf-8"))
        made = []
        for i in ids:
            spec = json.loads(json.dumps(spec0))
            spec["tokens"] = {**spec.get("tokens", {}), **tokens_of(L[i], pal)}
            shutil.copy(LIB / f"{i}.css", out / f"style-{i}.css")
            spec["styleFile"] = f"style-{i}.css"
            for s in spec["screens"]:  # htmlFile 은 원본 폴더 기준 → 새 폴더 기준으로
                if s.get("htmlFile") and not (out / s["htmlFile"]).exists() and (src.parent / s["htmlFile"]).exists():
                    shutil.copy(src.parent / s["htmlFile"], out / s["htmlFile"])
            j = out / f"style-{i}.json"
            j.write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
            subprocess.run([sys.executable, str(HERE / "app.py"), str(j), "--out", str(out / f"style-{i}.html")], check=True)
            made.append(out / f"style-{i}.html")
        for m in made:  # 캡처(폰 390 · PC 1440)
            subprocess.run([sys.executable, str(HERE / "shots.py"), "cand", str(m), "--d"], check=True)
        return
    print(__doc__)


if __name__ == "__main__":
    sys.path.insert(0, str(HERE))
    main()
