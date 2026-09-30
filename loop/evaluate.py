"""python3 loop/evaluate.py <run_dir> <prd.md> <baseline_dir>  →  run_dir/eval.json, eval.md"""
import sys, json, re, random, subprocess, pathlib, concurrent.futures as cf
ROOT = pathlib.Path(__file__).resolve().parent.parent
run, prd, base = (pathlib.Path(a).resolve() for a in sys.argv[1:4])
shots = run / "shots"; shots.mkdir(exist_ok=True)
subprocess.run(["python3", str(ROOT / "loop/score.py"), str(run / "out"), "--shots", str(shots), "--json", str(run / "score.json")],
               stdout=open(run / "score.txt", "w"), stderr=subprocess.STDOUT)
# 바닐라 스크린샷
bshots = base / "shots"
if not bshots.exists():
    bshots.mkdir()
    from playwright.sync_api import sync_playwright
    htmls = sorted((base / "out").rglob("*.html"))[:14]
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome"); pg = b.new_page(viewport={"width": 375, "height": 812})
        for i, h in enumerate(htmls):
            pg.goto(h.as_uri()); pg.wait_for_timeout(800)
            pg.screenshot(path=str(bshots / f"{i:02d}-{h.stem}.png"), full_page=True)
        b.close()
def claude(prompt, cwd, model="claude-opus-5-5"):
    r = subprocess.run(["claude", "-p", "--model", model, "--dangerously-skip-permissions", "--output-format", "json"],
                       input=prompt, capture_output=True, text=True, cwd=cwd)
    try: return json.loads(r.stdout).get("result", "")
    except Exception: return r.stdout + r.stderr
J = (ROOT / "loop/judge.md").read_text().replace("{{CRITERIA}}", str(ROOT / "docs/design-criteria.md")) \
    .replace("{{PRD}}", str(prd)).replace("{{SHOTS}}", str(shots)).replace("{{SCORE}}", str(run / "score.txt"))
C = (ROOT / "loop/compare.md").read_text().replace("{{PRD}}", str(prd))
def cmp(i):
    flip = random.random() < .5
    x, y = (bshots, shots) if flip else (shots, bshots)
    out = claude(C.replace("{{X}}", str(x)).replace("{{Y}}", str(y)), run, "claude-sonnet-5-5")
    w = re.findall(r"WINNER:\s*([XY])", out)
    if not w: return None
    return (w[-1] == "Y") if flip else (w[-1] == "X")   # True = 하네스 승
with cf.ThreadPoolExecutor(6) as ex:
    fj = ex.submit(claude, J, run); fc = [ex.submit(cmp, i) for i in range(5)]
    jtxt = fj.result(); wins = [f.result() for f in fc]
(run / "judge.txt").write_text(jtxt)
m = re.findall(r"```json\s*(\{.*?\})\s*```", jtxt, re.S)
try: judge = json.loads(m[-1])
except Exception: judge = {"parse_error": True}
sc = json.loads((run / "score.json").read_text()) if (run / "score.json").exists() else {}
valid = [w for w in wins if w is not None]
res = {"score_pass": f'{sc.get("passed")}/{sc.get("total")}', "failed_checks": [c for c in sc.get("checks", []) if not c.get("pass")],
       "judge": judge, "vs_vanilla": f"{sum(valid)}/{len(valid)}"}
(run / "eval.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
r = judge.get("rubric", {}); avg = sum(r.values()) / len(r) if r else 0
print(f'기계 채점 {res["score_pass"]} · 루브릭 평균 {avg:.2f} · P0 {len(judge.get("p0",[]))} P1 {len(judge.get("p1",[]))} · 바닐라 대비 {res["vs_vanilla"]}')
