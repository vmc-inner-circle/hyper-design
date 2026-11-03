"""화면 유형 실험 — 실제 앱을 익명 PRD로 하네스에 넣어, 그 앱의 실제 유형대로 고르고 만드는지 본다.

python3 loop/archetype_exp/exp.py select <폴더> [--jobs 6] [--only id,id]   이 브랜치로 화면 목록까지만 → 고른 유형
python3 loop/archetype_exp/exp.py full <폴더> --only id,id [--jobs 6]        이 브랜치·main 둘 다 끝까지 → 만든 홈
python3 loop/archetype_exp/exp.py score <폴더>                               채점(full은 만든 홈 라벨이 있어야 — 아래)

- 재료: apps.json(정답 truth·원본 앱 이름 exclude·조사에 쓴 앱인지 surveyed), prds/<id>.md(익명 PRD, lint_prd.py 통과)
- 원본 앱은 시장 조사에서 뺀다: run.py를 MARKET_EXCLUDE=<exclude>로 띄운다(market.py가 읽음)
- main 하네스는 <폴더>/main-wt(origin/main 워크트리)의 플러그인으로 돌린다 — 실행기(run.py)는 이 브랜치 것
- full의 "만든 홈 유형"은 사람이 정하지 않는다: score가 <폴더>/home_label.in.json(만든 홈 첫 화면 캡처 목록, 어느 쪽인지 숨김)을 쓰고,
  라벨러 에이전트가 docs/research/screen-archetypes/LABEL_PROMPT.md로 home_label.out.json을 쓰면 다시 score
"""
import sys, os, json, random, pathlib, subprocess
from concurrent.futures import ThreadPoolExecutor
HERE = pathlib.Path(__file__).resolve().parent; ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "docs/research/screen-archetypes"))
APPS = {a["id"]: a for a in json.load(open(HERE / "apps.json"))}

def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default

def ids():
    only = arg("--only"); return only.split(",") if only else list(APPS)

def run_one(prd, out, exclude, extra):
    env = dict(os.environ, MARKET_EXCLUDE=exclude)
    log = open(str(out) + ".log", "w")
    subprocess.run([sys.executable, str(ROOT / "loop/run.py"), str(prd), str(out)] + extra, env=env, stdout=log, stderr=subprocess.STDOUT)
    return out.name

def main_plugin(base):
    wt = base / "main-wt"
    if not wt.exists():
        subprocess.run(["git", "fetch", "-q", "origin", "main"], cwd=ROOT)
        subprocess.run(["git", "worktree", "add", "-q", "--detach", str(wt), "origin/main"], cwd=ROOT, check=True)
    return wt / "plugins/k-style-ui-ux"

def first_home(out):
    try: S = json.load(open(out / "out/screens.json"))["screens"]
    except Exception: return None
    return next((s for s in S if s.get("kind") == "home" and "--" not in s["id"]), None)

def score(base):
    from classify_v2 import typ
    rows = []
    for i in APPS:
        h = first_home(base / "select" / i)
        if h is not None or (base / "select" / i).exists():
            rows.append((i, APPS[i]["surveyed"], APPS[i]["truth"], (h or {}).get("archetype")))
    if rows:
        print("## 고르기 (이 브랜치, 화면 목록까지)\n| 앱 | 조사에 씀 | 정답 | 고른 유형 | |\n|---|---|---|---|---|")
        for i, sv, t, a in rows: print(f"| {i} | {'예' if sv else '아니오'} | {t} | {a} | {'✅' if a == t else '❌'} |")
        for sv, name in ((True, "조사한 앱"), (False, "조사 안 한 앱"), (None, "전체")):
            r = [x for x in rows if sv is None or x[1] == sv]
            if r: print(f"- {name}: {sum(x[2] == x[3] for x in r)}/{len(r)}")
    # full: 만든 홈 첫 화면 → 블라인드 라벨
    shots = []
    for side in ("branch", "main"):
        for i in APPS:
            d = base / f"full-{side}" / i; h = first_home(d)
            png = d / "out/.shots" / f"{h['id']}.png" if h else None
            if png and png.exists(): shots.append({"key": f"{side}|{i}", "file": str(png)})
    if not shots: return
    lab = base / "home_label.out.json"
    if not lab.exists():
        random.seed(56); random.shuffle(shots)
        items = [{"src": "mweb", "file": s["file"], "site": f"x{n:02d}", "domain": "", "page": "home"} for n, s in enumerate(shots)]
        json.dump(items, open(base / "home_label.in.json", "w"), ensure_ascii=False, indent=1)
        json.dump({it["site"]: s["key"] for it, s in zip(items, shots)}, open(base / "home_label.key.json", "w"), ensure_ascii=False, indent=1)
        print(f"\n만든 홈 {len(shots)}장 → {base / 'home_label.in.json'} 를 라벨러로 라벨링한 뒤 다시 score"); return
    key = json.load(open(base / "home_label.key.json")); got = {}
    for r in json.load(open(lab)):
        side, i = key[r["site"]].split("|"); got[(side, i)] = typ("home", r["anchor"], r.get("exit", "")) if r.get("valid", True) else "무효"
    print("\n## 끝까지 만든 홈 (블라인드 라벨)\n| 앱 | 정답 | main | 이 브랜치 | 이 브랜치 선언 |\n|---|---|---|---|---|")
    hit = {"main": 0, "branch": 0}; n = 0; comply = [0, 0]
    for i in APPS:
        if ("branch", i) not in got and ("main", i) not in got: continue
        n += 1; t = APPS[i]["truth"]; decl = (first_home(base / "full-branch" / i) or {}).get("archetype")
        for side in hit: hit[side] += got.get((side, i)) == t
        if decl: comply[0] += got.get(("branch", i)) == decl; comply[1] += 1
        print(f"| {i} | {t} | {got.get(('main', i))} | {got.get(('branch', i))} | {decl} |")
    print(f"- 정답 일치: main {hit['main']}/{n} · 이 브랜치 {hit['branch']}/{n}\n- 준수(선언한 유형대로 만들었나): {comply[0]}/{comply[1]}")

def main():
    cmd, base = sys.argv[1], pathlib.Path(sys.argv[2]).resolve(); base.mkdir(parents=True, exist_ok=True)
    jobs = int(arg("--jobs", 6)); tasks = []
    if cmd == "select":
        for i in ids(): tasks.append((HERE / "prds" / f"{i}.md", base / "select" / i, APPS[i]["exclude"], ["--until-screens"]))
    elif cmd == "full":
        mp = main_plugin(base)
        for i in ids():
            tasks.append((HERE / "prds" / f"{i}.md", base / "full-branch" / i, APPS[i]["exclude"], []))
            tasks.append((HERE / "prds" / f"{i}.md", base / "full-main" / i, APPS[i]["exclude"], ["--plugin", str(mp)]))
    elif cmd == "score": return score(base)
    for d in tasks: d[1].parent.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(jobs) as ex:
        for name in ex.map(lambda t: run_one(*t), tasks): print("끝:", name, flush=True)
    score(base)

if __name__ == "__main__": main()
