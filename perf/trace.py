#!/usr/bin/env python3
"""하네스 1회 실행의 속도 분해 → perf/perf.db (SQLite).

python3 perf/trace.py <session_id> --run <run_id> --harness <이름> [--prd prd/x.md] [--out <결과 폴더>] [--note "..."]
python3 perf/trace.py --latest <하네스를 실행한 폴더> --run <run_id> --harness <이름> ...   # 그 폴더의 가장 최근 세션

Claude Code 세션 기록(~/.claude/projects/*/<session_id>.jsonl + <session_id>/subagents/*.jsonl)을 읽어
트레이스/스팬 모델로 적재한다. 하네스는 고치지 않는다.

- runs     : 실행 1회 (하네스 이름, 하네스 시간, 사용자 턴 수, 최대 동시 서브에이전트, 토큰, 화면 수,
             미적 점수는 사람이 나중에 UPDATE — 다시 적재해도 유지)
- segments : 각 에이전트 타임라인을 빈틈없이 나눈 구간. 합 = 그 에이전트의 벽시계 시간.
             category = llm(모델 생성·사고) | wait(사람의 다음 지시 대기, 하네스 시간 아님) | bg_wait(백그라운드 서브에이전트 알림 대기) | subagent | script:<이름> | bash | io:<도구> | other:<도구>
             도구 여러 개가 동시에 돌면 가장 늦게 끝나는 도구에 귀속(크리티컬 패스).
- tools    : 도구 호출 1건 (dur_s 요청→결과, run_s 묶음 대기를 뺀 실제 처리 시간, 요약)
- agents   : 메인 + 서브에이전트별 소요·토큰·도구 수
뷰: v_compare (A/B 한 줄 비교), v_main (메인 타임라인 = 사용자가 기다린 시간의 분해), v_agents, v_scripts,
    v_tool_latency (도구 종류별 평균·최대 — 동시 부하 지표), v_turns (사용자 턴별 하네스 시간)
"""
import sys, json, re, glob, sqlite3, argparse, pathlib, datetime, subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
DB = ROOT / "perf/perf.db"
SCHEMA = """
CREATE TABLE IF NOT EXISTS runs(run_id TEXT PRIMARY KEY, session_id TEXT, prd TEXT, commit_sha TEXT,
  started TEXT, ended TEXT, wall_s REAL, active_s REAL, in_tok INT, out_tok INT, cache_read_tok INT, screens INT,
  aesthetic_score REAL, note TEXT, harness TEXT, turns INT, peak_agents INT);
CREATE TABLE IF NOT EXISTS agents(run_id TEXT, agent TEXT, description TEXT, model TEXT, started TEXT,
  dur_s REAL, in_tok INT, out_tok INT, cache_read_tok INT, n_tools INT);
CREATE TABLE IF NOT EXISTS segments(run_id TEXT, agent TEXT, category TEXT, start TEXT, dur_s REAL, turn INT);
CREATE TABLE IF NOT EXISTS tools(run_id TEXT, agent TEXT, tool TEXT, category TEXT, summary TEXT,
  start TEXT, dur_s REAL, run_s REAL);
CREATE VIEW IF NOT EXISTS v_main AS
  SELECT s.run_id, category, ROUND(SUM(dur_s),1) sec, ROUND(100*SUM(dur_s)/r.active_s,1) pct
  FROM segments s JOIN runs r USING(run_id) WHERE agent='main' AND category<>'wait' GROUP BY s.run_id, category ORDER BY s.run_id, sec DESC;
CREATE VIEW IF NOT EXISTS v_agents AS
  SELECT run_id, agent, description, model, dur_s, n_tools, in_tok, out_tok FROM agents ORDER BY run_id, dur_s DESC;
CREATE VIEW IF NOT EXISTS v_scripts AS
  SELECT run_id, category, COUNT(*) n, ROUND(SUM(dur_s),1) sec, ROUND(MAX(dur_s),1) max_s
  FROM tools WHERE category LIKE 'script:%' GROUP BY run_id, category ORDER BY run_id, sec DESC;
CREATE VIEW IF NOT EXISTS v_tool_latency AS
  SELECT run_id, tool, COUNT(*) n, ROUND(AVG(run_s),1) avg_s, ROUND(MAX(run_s),1) max_s
  FROM tools WHERE tool NOT IN ('Agent','Task') GROUP BY run_id, tool ORDER BY run_id, n DESC;
CREATE VIEW IF NOT EXISTS v_turns AS
  SELECT run_id, turn, ROUND(SUM(dur_s)/60,1) harness_min FROM segments
  WHERE agent='main' AND category<>'wait' GROUP BY run_id, turn ORDER BY run_id, turn;
CREATE VIEW IF NOT EXISTS v_compare AS
  SELECT run_id, harness, prd, ROUND(active_s/60,1) harness_min, turns, peak_agents,
    (SELECT COUNT(*)-1 FROM agents a WHERE a.run_id=r.run_id) subagents,
    (SELECT COUNT(*) FROM tools t WHERE t.run_id=r.run_id) tool_calls,
    (SELECT ROUND(AVG(run_s),1) FROM tools t WHERE t.run_id=r.run_id AND tool IN ('Read','Write','Edit','Glob','Grep')) io_avg_s,
    (SELECT ROUND(AVG(run_s),1) FROM tools t WHERE t.run_id=r.run_id AND tool='Bash') bash_avg_s,
    screens, out_tok, aesthetic_score
  FROM runs r ORDER BY started;
"""

ts = lambda s: datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))

def classify(name, inp):
    if name in ("Agent", "Task"): return "subagent", inp.get("description", "")
    if name == "Bash":
        cmd = inp.get("command", "")
        m = re.search(r"(?:python3?|node)\s+(?:-\S+\s+)*\S*?([\w-]+)\.(?:py|m?js)\b", cmd)
        return ("script:" + m.group(1) if m else "bash"), cmd[:160]
    if name in ("Read", "Write", "Edit", "Glob", "Grep", "NotebookEdit"):
        return "io:" + name, str(inp.get("file_path") or inp.get("pattern") or "")[:160]
    return "other:" + name, json.dumps(inp, ensure_ascii=False)[:160]

def parse(path):
    """한 에이전트 기록 → (시작, 끝, 구간들, 도구들, 토큰, 모델)"""
    rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    rows = [r for r in rows if r.get("timestamp") and r.get("type") in ("user", "assistant")]
    rows.sort(key=lambda r: r["timestamp"])
    calls, ends, tok, seen, model, msg_of = {}, {}, [0, 0, 0], set(), "", {}
    for r in rows:
        c = r["message"].get("content")
        if r["type"] == "assistant":
            m = r["message"]; model = m.get("model", model)
            if m.get("id") not in seen and m.get("usage"):
                seen.add(m.get("id")); u = m["usage"]
                tok[0] += u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
                tok[1] += u.get("output_tokens", 0); tok[2] += u.get("cache_read_input_tokens", 0)
            for b in c if isinstance(c, list) else []:
                if b.get("type") == "tool_use":
                    cat, summ = classify(b["name"], b.get("input", {}))
                    calls[b["id"]] = (b["name"], cat, summ, ts(r["timestamp"])); msg_of[b["id"]] = m.get("id")
        elif isinstance(c, list):
            for b in c:
                if b.get("type") == "tool_result" and b.get("tool_use_id") in calls:
                    ends[b["tool_use_id"]] = ts(r["timestamp"])
    t0, t1 = ts(rows[0]["timestamp"]), ts(rows[-1]["timestamp"])
    # 한 메시지에서 여러 도구를 한꺼번에 요청하면 차례로 실행된다(Write 5개면 5번째는 앞 4개를 기다림).
    # dur_s = 요청→결과(대기 포함), run_s = 같은 묶음의 앞 결과가 나온 뒤부터 자기 결과까지(실제 처리 시간)
    batch, run_s = {}, {}
    for i in calls: batch.setdefault(msg_of[i], []).append(i)
    for ids in batch.values():
        st = prev = min(calls[i][3] for i in ids)
        for i in sorted(ids, key=lambda i: ends.get(i) or t1):
            e = ends.get(i) or t1; run_s[i] = (e - max(st, prev)).total_seconds(); prev = max(prev, e)
    tools = [(n, cat, s, st, ((ends.get(i) or t1) - st).total_seconds(), run_s[i]) for i, (n, cat, s, st) in calls.items()]
    # 타임라인 구간: 경계마다 진행 중인 도구가 있으면 가장 늦게 끝나는 도구의 범주, 없으면 llm
    marks = sorted({ts(r["timestamp"]) for r in rows})
    # 사람이 보낸 다음 지시가 도착하기 전까지는 하네스가 아니라 사용자 대기(wait).
    # 백그라운드 서브에이전트 알림(turnOrigin=task_notification)을 기다린 구간은 하네스 시간(bg_wait).
    def origin(r):
        c = r["message"].get("content")
        if r["type"] != "user" or r.get("isMeta") or (isinstance(c, list) and any(b.get("type") == "tool_result" for b in c)): return None
        return "notify" if r.get("turnOrigin") == "task_notification" else "human"
    prompts = {ts(r["timestamp"]) for r in rows[1:] if origin(r) == "human"}
    notifies = {ts(r["timestamp"]) for r in rows[1:] if origin(r) == "notify"}
    segs = []
    for a, b in zip(marks, marks[1:]):
        live = [(ends.get(i) or t1, cat) for i, (_, cat, _, st) in calls.items() if st <= a < (ends.get(i) or t1)]
        cat = max(live)[1] if live else ("wait" if b in prompts else "bg_wait" if b in notifies else "llm")
        if segs and segs[-1][0] == cat: segs[-1][2] += (b - a).total_seconds()
        else: segs.append([cat, a, (b - a).total_seconds()])
    return t0, t1, segs, tools, tok, model, sorted(prompts)

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(); ap.add_argument("session", nargs="?"); ap.add_argument("--latest")
    ap.add_argument("--run", required=True); ap.add_argument("--harness", required=True)
    ap.add_argument("--prd", default=""); ap.add_argument("--note", default=""); ap.add_argument("--out", default="")
    a = ap.parse_args()
    if a.latest:   # Claude Code는 실행 폴더 경로의 ':' '/' '\' 를 '-'로 바꾼 이름의 폴더에 세션을 남긴다
        proj = pathlib.Path.home() / ".claude/projects" / re.sub(r"[:/\\]", "-", str(pathlib.Path(a.latest).resolve()))
        hits = sorted(proj.glob("*.jsonl"), key=lambda f: f.stat().st_mtime)[-1:]
    else:
        hits = glob.glob(str(pathlib.Path.home() / f".claude/projects/*/{a.session}.jsonl"))
    if not hits: sys.exit(f"세션 기록 없음: {a.session or a.latest}")
    main_path = pathlib.Path(hits[0]); a.session = main_path.stem
    db = sqlite3.connect(DB)
    for v in ("v_main", "v_agents", "v_scripts", "v_tool_latency", "v_turns", "v_compare"): db.execute(f"DROP VIEW IF EXISTS {v}")   # 뷰 정의는 항상 최신으로
    db.executescript(SCHEMA)
    for tb, col in (("runs", "harness TEXT"), ("runs", "turns INT"), ("runs", "peak_agents INT"), ("segments", "turn INT"), ("tools", "run_s REAL")):   # 예전 DB 보강
        try: db.execute(f"ALTER TABLE {tb} ADD COLUMN {col}")
        except sqlite3.OperationalError: pass
    keep = db.execute("SELECT aesthetic_score FROM runs WHERE run_id=?", (a.run,)).fetchone()
    for t in ("runs", "agents", "segments", "tools"): db.execute(f"DELETE FROM {t} WHERE run_id=?", (a.run,))

    t0, t1, segs, tools, tok, model, prompts = parse(main_path); turns = len(prompts) + 1
    turn_of = lambda st: 1 + sum(1 for p in prompts if p <= st)   # 사용자 지시 몇 번째 이후 구간인가
    spans = []
    def load(agent, desc, path_t):
        s0, s1, sg, tl, tk, md = path_t[:6]
        if agent != "main": spans.append((s0, s1))
        db.execute("INSERT INTO agents VALUES(?,?,?,?,?,?,?,?,?,?)",
                   (a.run, agent, desc, md, s0.isoformat(), (s1 - s0).total_seconds(), tk[0], tk[1], tk[2], len(tl)))
        db.executemany("INSERT INTO segments VALUES(?,?,?,?,?,?)", [(a.run, agent, c, st.isoformat(), d, turn_of(st)) for c, st, d in sg])
        db.executemany("INSERT INTO tools VALUES(?,?,?,?,?,?,?,?)",
                       [(a.run, agent, n, c, s, st.isoformat(), d, r) for n, c, s, st, d, r in tl])
        return tk
    total = list(load("main", "", (t0, t1, segs, tools, tok, model)))
    for p in sorted(glob.glob(str(main_path.with_suffix("") / "subagents/*.jsonl"))):
        meta = pathlib.Path(p[:-6] + ".meta.json")
        desc = json.loads(meta.read_text(encoding="utf-8")).get("description", "") if meta.exists() else ""
        try: tk = load(pathlib.Path(p).stem, desc, parse(p))
        except (IndexError, KeyError): continue
        total = [x + y for x, y in zip(total, tk)]

    out = pathlib.Path(a.out) if a.out else None
    screens = len(list(out.glob("screens/*.html"))) if out and out.exists() else None
    sha = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    wall = (t1 - t0).total_seconds(); active = wall - sum(d for c, _, d in segs if c == "wait")
    peak = max([sum(1 for s, e in spans if s <= t < e) for t, _ in spans] or [0])
    db.execute("INSERT INTO runs(run_id, session_id, prd, commit_sha, started, ended, wall_s, active_s, in_tok, out_tok,"
               " cache_read_tok, screens, aesthetic_score, note, harness, turns, peak_agents) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
               (a.run, a.session, a.prd, sha, t0.isoformat(), t1.isoformat(), wall, active,
                total[0], total[1], total[2], screens, keep[0] if keep else None, a.note, a.harness, turns, peak))
    db.commit()
    print(f"[{a.run}] {a.harness} · 하네스 {active/60:.1f}분 (벽시계 {wall/60:.1f}분) · 턴 {turns} · 최대 동시 {peak} · 서브에이전트 {db.execute('SELECT COUNT(*)-1 FROM agents WHERE run_id=?', (a.run,)).fetchone()[0]}개 · 화면 {screens}")
    for cat, sec, pct in db.execute("SELECT category, sec, pct FROM v_main WHERE run_id=? LIMIT 8", (a.run,)):
        print(f"  {cat:<28}{sec:>8.1f}s {pct:>5.1f}%")

if __name__ == "__main__":
    main()
