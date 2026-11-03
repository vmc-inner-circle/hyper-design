#!/bin/bash
# 회귀 확인: 기존 PRD 4개를 main·이 브랜치로 2개씩만 동시에(시간 비교가 서로 느려지는 영향에 덜 휘둘리게) 돌리고,
# evaluate.py로 기계 채점·평가 에이전트·블라인드 비교(이 브랜치 vs main, 5판)
# bash loop/archetype_exp/regress.sh <폴더> <main 플러그인 폴더>
set -u; B=$1; MP=$2; ROOT=$(cd "$(dirname "$0")/../.." && pwd); mkdir -p "$B"
for p in family-trip pilates-booking wedding-meetup ai-saju; do
  PRD=$ROOT/loop/results/v21-$p/prd.md
  python3 "$ROOT/loop/run.py" "$PRD" "$B/branch-$p" > "$B/branch-$p.log" 2>&1 &
  python3 "$ROOT/loop/run.py" "$PRD" "$B/main-$p" --plugin "$MP" > "$B/main-$p.log" 2>&1 &
  wait
done
for p in family-trip pilates-booking wedding-meetup ai-saju; do
  python3 "$ROOT/loop/evaluate.py" "$B/branch-$p" "$ROOT/loop/results/v21-$p/prd.md" "$B/main-$p" > "$B/eval-$p.log" 2>&1 &
done; wait
python3 - "$B" <<'PY'
import sys, pathlib, re
B = pathlib.Path(sys.argv[1])
for p in ("family-trip", "pilates-booking", "wedding-meetup", "ai-saju"):
    t = {s: (re.findall(r"([0-9.]+)분", (B / f"{s}-{p}/elapsed.txt").read_text()) or ["?"])[0] if (B / f"{s}-{p}/elapsed.txt").exists() else "?" for s in ("main", "branch")}
    win = n = 0
    for f in sorted((B / f"branch-{p}").glob("compare-*.txt")):
        txt = f.read_text(); w = re.findall(r"WINNER: ([XY])", txt)
        if not w: continue
        n += 1; harness = "X" if txt.startswith("X=harness") else "Y"   # evaluate.py: harness = 이 브랜치, vanilla = main
        win += w[-1] == harness
    print(f"== {p}  main {t['main']}분 · 브랜치 {t['branch']}분 · 블라인드 비교 브랜치 승 {win}/{n}")
PY
