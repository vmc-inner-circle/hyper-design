"""구동 결과를 submissions/greatSumini 로 옮긴다. python3 loop/package.py <run_dir> <label>"""
import sys, shutil, pathlib, json
ROOT = pathlib.Path(__file__).resolve().parent.parent
run = pathlib.Path(sys.argv[1]); label = sys.argv[2]
dst = ROOT / "submissions/greatSumini"
if dst.exists(): shutil.rmtree(dst)
shutil.copytree(run / "out", dst)
for f in ("prompt-log.md", "elapsed.txt"): shutil.copy(run / f, dst / f)
ev = json.loads((run / "eval.json").read_text())
r = ev["judge"].get("rubric", {})
(dst / "eval.md").write_text(f"""# 자동 평가 ({label})

- 기계 채점: {ev['score_pass']} ([성공 기준](../../docs/success-criteria.md))
- 평가 에이전트 루브릭 평균: {sum(r.values())/len(r):.2f} / 5 — {json.dumps(r, ensure_ascii=False)}
- P0 {len(ev['judge'].get('p0',[]))} · P1 {len(ev['judge'].get('p1',[]))}
- 바닐라(하네스 없는 Claude Code) 대비 블라인드 비교 승: {ev['vs_vanilla']}
- 한 줄 평: {ev['judge'].get('one_line','')}
""", encoding="utf-8")
print("packaged", run, "->", dst)
