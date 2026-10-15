#!/usr/bin/env python3
"""보이스톤 프리셋 자동 개선 루프 (Karpathy autoresearch 방식) — docs/voicetone-criteria.md 4절.

python3 loop/voicetone_auto.py --iters 20     # 이 저장소(작업 트리)에서 실행. 별도 worktree 권장.

순서: 보정(바닥·천장·흔들림 실측 → 합격선 계산) → 회차 반복(연구자 서브에이전트가 프리셋 하나 수정 → 고정 평가 →
2σ 넘게 좋아지면 확인 평가 후 커밋, 아니면 되돌림) → test 셋 최종 평가 → SUMMARY.md.
"""
import sys, json, subprocess, pathlib, argparse, statistics, time, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "loop"))
import voicetone_eval as E

D = E.D
TSV = D / "runs.tsv"
TARGETS = ["toss", "daangn"]          # 리디는 정답지가 작아(14) 잠정 — 루프에서 고치지 않고 후보로만 둔다
RESEARCH_MODEL = "claude-opus-5-5"


def sh(*a, check=False): return subprocess.run(a, cwd=ROOT, capture_output=True, text=True, check=check)


def log(row):
    new = not TSV.exists()
    with TSV.open("a", encoding="utf-8") as f:
        if new: f.write("time\titer\ttarget\tscore\tV1_toss\tV1_daangn\tU1\tU2\tagree\tdecision\thypothesis\n")
        f.write("\t".join(str(x) for x in row) + "\n")


def thresholds(cal):
    """합격선은 실측에서 계산한다 — 바닥(보이스톤 없음)과 천장(원문 말투 그대로 바꿔쓰기) 사이의 절반."""
    T = {}
    for co in ("toss", "daangn"):
        f, c = cal["floor"][co], cal["ceiling"][co]
        T[co] = {"floor": f, "ceiling": c, "pass": f + 0.5 * (c - f), "stretch": f + 0.75 * (c - f), "discriminates": c - f >= 0.15}
    T["sigma"] = max(cal["sigma"] or 0, 0.02)
    T["noisy"] = (cal["sigma"] or 0) > 0.05
    return T


def avg_score(rs): return statistics.mean(r["score"] for r in rs)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--iters", type=int, default=20); a = ap.parse_args()
    split, memos, oracle, items = E.load_fixed()
    if not (D / "calibration.json").exists(): E.calibrate()
    cal = json.loads((D / "calibration.json").read_text())
    T = thresholds(cal); (D / "thresholds.json").write_text(json.dumps(T, ensure_ascii=False, indent=1))
    if not all(T[co]["discriminates"] for co in ("toss", "daangn")):
        (D / "SUMMARY.md").write_text("# 중단: 측정이 변별하지 못함\n\n천장−바닥 < 0.15 — 평가 방식부터 다시 설계해야 한다.\n" + json.dumps(T, ensure_ascii=False, indent=1))
        return
    start = 1
    if TSV.exists():                                              # 이어 하기: 지금 프리셋을 새로 재서 출발점으로
        start = max(int(l.split("\t")[1]) for l in TSV.read_text().splitlines()[1:]) + 1
        cur_runs = [E.run("dev", 500 + start + k, tag=f"resume{start}-{k}") for k in range(2)]
    else:
        cur_runs = [json.loads(p.read_text()) for p in sorted((D / "runs").glob("cal-current-*.json"))]
    best = avg_score(cur_runs); best_run = cur_runs[-1]
    base_leak = {s: set(E.leak_check(s, split, items)[0]) for s in E.SLUGS}
    cap = {s: E.leak_check(s, split, items)[1] + 1500 for s in E.SLUGS}
    log([datetime.datetime.now().isoformat(timespec="minutes"), 0, "-", f"{best:.3f}", *(f"{statistics.mean(r['per'][c]['V1'] for r in cur_runs):.3f}" for c in TARGETS),
         f"{statistics.mean(r['U1'] for r in cur_runs):.3f}", f"{statistics.mean(r['U2'] for r in cur_runs):.3f}", f"{statistics.mean(r['agree'] for r in cur_runs):.2f}", "baseline" if start == 1 else "resume", f"σ={T['sigma']:.3f}"])
    program = (ROOT / "loop/voicetone_program.md").read_text()
    for it in range(start, start + a.iters):
        tgt = TARGETS[(it - 1) % len(TARGETS)]
        path = E.VOICES / f"{tgt}.json"; rel = path.relative_to(ROOT)
        fails = [f for f in best_run["fails"] if f["co"] == tgt][:15]
        hist = TSV.read_text().splitlines()[-12:]
        prompt = f"""{program}

## 이번 회차
- 대상: `{rel}` (현재 크기 {len(path.read_bytes())}B, 상한 {cap[tgt]}B)
- 현재 최고 점수 {best:.3f} (σ {T['sigma']:.3f}). 합격선 {tgt}: V1 ≥ {T[tgt]['pass']:.2f} (바닥 {T[tgt]['floor']:.2f}, 천장 {T[tgt]['ceiling']:.2f})
- 최근 기록(tsv):
{chr(10).join(hist)}

## dev 틀린 사례 — 실제 {E_name(tgt)} 원문 / 우리 프리셋 결과 / 판정이 대신 고른 후보(어느 프리셋)
{json.dumps(fails, ensure_ascii=False, indent=1)}

파일 `{rel}`을 직접 열어 고친다."""
        try: txt = E.claude(prompt, RESEARCH_MODEL, cwd=ROOT, tools=True)
        except E.Limit as e:
            sh("git", "checkout", "--", str(rel)); log([datetime.datetime.now().isoformat(timespec="minutes"), it, tgt, "-", "-", "-", "-", "-", "-", "stop:limit", str(e)[:80]])
            print("사용 한도로 중단:", e); return
        hyp = next((l.split("HYPOTHESIS:", 1)[1].strip() for l in reversed(txt.splitlines()) if "HYPOTHESIS:" in l), "(가설 없음)")
        changed = [l[3:] for l in sh("git", "status", "--porcelain").stdout.splitlines()
                   if l.strip() and "__pycache__" not in l and "loop/voicetone/" not in l]
        now = datetime.datetime.now().isoformat(timespec="minutes")
        def revert(reason):
            sh("git", "checkout", "--", str(rel)); sh("git", "clean", "-fdq", "--", "plugins")
            for c in changed:
                if c != str(rel) and not c.startswith("loop/voicetone/"): sh("git", "checkout", "--", c)
            log([now, it, tgt, "-", "-", "-", "-", "-", "-", f"reject:{reason}", hyp])
        if str(rel) not in changed: revert("no-change"); continue
        if any(c != str(rel) and not c.startswith("loop/voicetone/") for c in changed): revert("other-files"); continue
        try: json.loads(path.read_text())
        except Exception: revert("bad-json"); continue
        hits, size = E.leak_check(tgt, split, items)
        if size > cap[tgt]: revert(f"size{size}"); continue
        if set(hits) - base_leak[tgt]: revert(f"leak:{','.join(sorted(set(hits) - base_leak[tgt]))}"); continue
        try: r1 = E.run("dev", 1000 + it, tag=f"iter{it}")
        except E.Limit as e:
            sh("git", "checkout", "--", str(rel)); log([now, it, tgt, "-", "-", "-", "-", "-", "-", "stop:limit", hyp]); print("사용 한도로 중단:", e); return
        dec = "discard" if r1["gate_ok"] else "reject:gate"
        if r1["gate_ok"] and r1["score"] > best + T["sigma"]:                      # 1차 선별: σ보다 크게 좋아짐
            try: r2 = E.run("dev", 2000 + it, tag=f"iter{it}-confirm")
            except E.Limit as e:
                sh("git", "checkout", "--", str(rel)); log([now, it, tgt, "-", "-", "-", "-", "-", "-", "stop:limit", hyp]); print("사용 한도로 중단:", e); return  # 확인: 두 번 평균이 1.5σ 넘게 좋아야 유지
            s = avg_score([r1, r2])
            if s > best + 1.5 * T["sigma"] and r2["gate_ok"]:
                dec = "keep"; best = s; best_run = r1
                sh("git", "add", str(rel)); sh("git", "commit", "-qm", f"보이스톤 루프 iter {it} ({tgt}): {hyp}\n\ndev score {s:.3f}\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>")
        if dec != "keep": sh("git", "checkout", "--", str(rel))
        log([now, it, tgt, f"{r1['score']:.3f}", f"{r1['per']['toss']['V1']:.3f}", f"{r1['per']['daangn']['V1']:.3f}", f"{r1['U1']:.3f}", f"{r1['U2']:.3f}", f"{r1['agree']:.2f}", dec, hyp])
    # test 최종 — 루프 안에서는 한 번도 보지 않은 셋
    rt = E.run("test", 9, tag="final-test")
    L = ["# 보이스톤 자동 개선 루프 결과\n", f"- 회차 {a.iters}, 유지 {sum(1 for l in TSV.read_text().splitlines() if chr(9)+'keep'+chr(9) in l)}회",
         f"- dev 최고 점수 {best:.3f} (출발 {avg_score(cur_runs):.3f}, σ {T['sigma']:.3f})", "\n## test 셋 (루프가 본 적 없음)\n",
         "| 회사 | V1 | 바닥 | 합격선 | 천장 | 판정 |", "|---|---|---|---|---|---|"]
    for co in ("toss", "daangn"):
        v = rt["per"][co]["V1"]; t = T[co]
        if v is None: L.append(f"| {E_name(co)} | 측정 실패 | | | | |"); continue
        L.append(f"| {E_name(co)} | {v:.2f} | {t['floor']:.2f} | {t['pass']:.2f} | {t['ceiling']:.2f} | {'통과' if v >= t['pass'] else '미달'} |")
    L += [f"\nU1 {rt['U1']:.3f} (≥0.98) · U2 {rt['U2']:.3f} (=1) · 판정 2회 일치 {rt['agree']:.2f}", "\n기록: `loop/voicetone/runs.tsv`, 합격선: `thresholds.json`"]
    (D / "SUMMARY.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    sh("git", "add", "loop/voicetone"); sh("git", "commit", "-qm", "보이스톤 루프 결과: runs.tsv·thresholds·test 평가 요약\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>")
    print("\n".join(L))


def E_name(co): return {"toss": "토스", "daangn": "당근", "ridi": "리디"}[co]


if __name__ == "__main__":
    main()
