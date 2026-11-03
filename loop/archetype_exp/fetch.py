"""실험 앱의 스토어 설명 전문·스크린샷 시트를 받는다(정답 라벨링·PRD 쓰기 재료). 결과는 <폴더>/<id>/ — 커밋하지 않는다.
python3 fetch.py <폴더>
"""
import sys, json, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "plugins/k-style-ui-ux/core/scripts"))
import market as M
out = pathlib.Path(sys.argv[1]); apps = json.load(open(pathlib.Path(__file__).parent / "apps.json"))
def one(a):
    r = next((x for x in M.search(a["name"].split(" - ")[0].split(":")[0], "kr", 15) if x["trackName"] == a["name"]), None)
    if not r: return a["id"], "없음"
    d = out / a["id"]; d.mkdir(parents=True, exist_ok=True)
    M.sheet(r.get("screenshotUrls") or [], f"{a['name']}", d / "sheet.jpg")
    (d / "description.txt").write_text(r.get("description", ""), encoding="utf-8")
    return a["id"], len(r.get("description", ""))
for x in M.POOL.map(one, apps): print(*x)
