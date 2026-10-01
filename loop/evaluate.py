"""python3 loop/evaluate.py <run_dir> <prd.md> <baseline_dir> [designer_shots_dir]  →  run_dir/eval.json, compare-*.txt"""
import sys, json, re, random, subprocess, pathlib, concurrent.futures as cf
ROOT = pathlib.Path(__file__).resolve().parent.parent
run, prd, base = (pathlib.Path(a).resolve() for a in sys.argv[1:4])
designer = pathlib.Path(sys.argv[4]).resolve() if len(sys.argv) > 4 else None
shots = run / "shots"; shots.mkdir(exist_ok=True)
subprocess.run(["python3", str(ROOT / "loop/score.py"), str(run / "out"), "--shots", str(shots), "--json", str(run / "score.json")],
               stdout=open(run / "score.txt", "w"), stderr=subprocess.STDOUT)
# 바닐라 스크린샷
bshots = base / "shots"
if not bshots.exists():
    bshots.mkdir()
    from playwright.sync_api import sync_playwright
    htmls = [h for h in sorted((base / "out").rglob("*.html")) if h.name != "index.html"][:30]
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome"); pg = b.new_page(viewport={"width": 375, "height": 812})
        for i, h in enumerate(htmls):
            pg.goto(h.as_uri()); pg.wait_for_timeout(800)
            pg.screenshot(path=str(bshots / f"{i:02d}-{h.stem}.png"))            # 폰 첫 화면(하네스 캡처와 같은 방식)
            pg.evaluate("window.scrollTo(0, document.body.scrollHeight)"); pg.wait_for_timeout(200)
            pg.screenshot(path=str(bshots / f"{i:02d}-{h.stem}-end.png"))
        if len(htmls) < 3 and (base / "out/index.html").exists():   # 한 페이지 앱(SPA) — 전체를 큰 화면으로
            pg2 = b.new_page(viewport={"width": 1440, "height": 900})
            pg2.goto((base / "out/index.html").as_uri()); pg2.wait_for_timeout(2500)
            pg2.screenshot(path=str(bshots / "index-full.png"), full_page=True)
            H = pg2.evaluate("document.documentElement.scrollHeight")
            for k, y in enumerate(range(0, min(H, 900 * 12), 900)):
                pg2.evaluate(f"window.scrollTo(0,{y})"); pg2.wait_for_timeout(300)
                pg2.screenshot(path=str(bshots / f"index-{k:02d}.png"))
        b.close()
def claude(prompt, cwd, model="claude-opus-5-5"):
    r = subprocess.run(["claude", "-p", "--model", model, "--dangerously-skip-permissions", "--output-format", "json"],
                       input=prompt, capture_output=True, text=True, cwd=cwd)
    try: return json.loads(r.stdout).get("result", "")
    except Exception: return r.stdout + r.stderr
J = (ROOT / "loop/judge.md").read_text().replace("{{CRITERIA}}", str(ROOT / "docs/design-criteria.md")) \
    .replace("{{PRD}}", str(prd)).replace("{{SHOTS}}", str(shots)).replace("{{SCORE}}", str(run / "score.txt"))
if designer:
    J += f"""

추가 — 같은 PRD의 실제 디자이너 결과 캡처가 {designer} 에 있다(일부 영역, 흐릴 수 있음). 전부 열어 본 뒤 하네스 결과와 비교해
JSON에 "vs_designer": {{"scope": 1~5, "edge": 1~5, "visual": 1~5, "gaps": ["디자이너에는 있고 하네스에는 없는 것"]}} 를 추가하라
(scope = 흐름·화면을 명세만큼 덮었나, edge = 규칙·예외 상황, visual = 색·이미지·완성도. 5 = 디자이너와 동급)."""
C = (ROOT / "loop/compare.md").read_text().replace("{{PRD}}", str(prd))
def cmp(i):
    flip = random.random() < .5
    x, y = (bshots, shots) if flip else (shots, bshots)
    out = claude(C.replace("{{X}}", str(x)).replace("{{Y}}", str(y)), run, "claude-sonnet-5-5")
    (run / f"compare-{i}.txt").write_text(("X=vanilla Y=harness" if flip else "X=harness Y=vanilla") + "\n\n" + out)
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
