#!/usr/bin/env python3
"""하네스 1회 실행의 시간·토큰·비용 집계 → stats.json. loop/run.py가 끝날 때 부른다(따로 불러도 된다).

python3 loop/stats.py <세션 id 또는 .jsonl 경로> [<세션 id> …] [--out stats.json]

**Claude Code 세션 기록 형식에 묶여 있다**: ~/.claude/projects/<실행 폴더 이름>/<세션 id>.jsonl(메인) +
<세션 id>/subagents/agent-*.jsonl·*.meta.json(서브에이전트). assistant 줄의 message.usage·model, 도구 호출(tool_use),
cost-state 줄(Claude Code가 남기는 누적 비용)을 읽는다. Codex·Cursor로 구동한 실행은 집계하지 못한다.
형식이 바뀌어 못 읽으면 그 칸을 비우고 이유를 notes에 적는다(run.py의 elapsed.txt는 그대로 남는다).

- 토큰: 메인/서브에이전트 × 모델별 입력·캐시 쓰기(5분·1시간)·캐시 읽기·출력. 같은 message.id가 여러 줄로 나뉘어 기록되므로 id로 한 번만 센다.
- 추정 비용: 아래 PRICE(정가, $/1M 토큰)로 계산. cost-state가 있으면 Claude Code가 계산한 값(cli_cost_usd — 끝난 서브에이전트까지 포함한
  세션 누적, 마지막으로 기록된 시점 값)도 같이 둔다. 끝난 go 실행에서 PRICE 계산과 cost-state가 소수점까지 같았다.
- 단계별 시간(go): 메인이 처음 실행한 스크립트로 단계 경계를 잡는다(SKILL.md 순서) — 1단계 세션 시작 · 1.5단계 expand_states.py ·
  2단계 화면 파일(screens/<id>.html)을 맡긴 첫 서브에이전트(빌드) · 3단계 그 뒤 build_canvas/audit 중 처음 · max는 '/k-style-ui-ux:max' 지시. 추정이다.
아이디어: hydrojun #14(run-stats — 턴별 토큰·비용), eungshin #29(perf/trace.py — 세션 기록 파싱·동시 서브에이전트).
"""
import sys, json, re, glob, pathlib, datetime

# 정가 $/1M 토큰. 캐시 쓰기는 5분 = 입력 × 1.25, 1시간 = 입력 × 2. 표에 없는 모델은 비용을 비운다.
# opus-5-5·sonnet-5-5·haiku-5-5는 실제 go 실행의 cost-state와 소수점까지 맞춘 값(2026-11-03), 나머지는 공개 가격표 값(미검증).
PRICE = {"claude-fable-5-1": (10, 50, 0.25), "claude-fable-5": (10, 50, 1.0), "claude-opus-5-5": (4, 20, 0.20),
         "claude-opus-5": (5, 25, 0.5), "claude-opus-4-8": (5, 25, 0.5), "claude-sonnet-5-5": (2, 10, 0.10),
         "claude-sonnet-5": (2, 10, 0.20), "claude-sonnet-4-6": (3, 15, 0.3), "claude-haiku-5-5": (0.1, 0.5, 0.01),
         "claude-haiku-4-5": (1, 5, 0.1)}   # (입력, 출력, 캐시 읽기)
KEYS = ("input", "cache_write_5m", "cache_write_1h", "cache_read", "output")
RUN = lambda names: r"python3?\s+(?:-\S+\s+)*\S*(?:" + names + r")\.py\s+[^-\s]"   # out 폴더를 넘겨 실행한 호출만(cat·sed로 읽거나 --help는 아님)
STAGES = [("1.5단계", RUN("expand_states")), ("2단계", None), ("3단계", RUN("build_canvas|audit"))]   # 1단계 = 세션 시작. selfcheck는 중간에도 돌려 경계로 쓰지 않는다
ts = lambda s: datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))

def cost(model, t):
    p = PRICE.get(re.sub(r"\[.*\]$|-\d{8}$", "", model or ""))
    if not p: return None
    i, o, r = p
    return round((t["input"] * i + t["cache_write_5m"] * i * 1.25 + t["cache_write_1h"] * i * 2 + t["cache_read"] * r + t["output"] * o) / 1e6, 4)

def find(sid):
    if sid.endswith(".jsonl") and pathlib.Path(sid).exists(): return pathlib.Path(sid)
    hits = glob.glob(str(pathlib.Path.home() / f".claude/projects/*/{sid}.jsonl"))
    return pathlib.Path(hits[0]) if hits else None

def read(path, seen):
    """한 에이전트 기록 → {model: 토큰}, 시작·끝, 도구 호출(시각, 이름, 입력), 사용자 지시 시각, cost-state"""
    by_model, calls, prompts, t0, t1, cs = {}, [], [], None, None, None
    for line in open(path, encoding="utf-8"):
        try: r = json.loads(line)
        except ValueError: continue
        if r.get("type") == "cost-state": cs = r; continue
        if r.get("type") not in ("user", "assistant") or not r.get("timestamp"): continue
        t = ts(r["timestamp"]); t0 = t0 or t; t1 = t
        m = r.get("message") or {}; c = m.get("content")
        if r["type"] == "assistant":
            u = m.get("usage")
            if u and m.get("id") not in seen:
                seen.add(m.get("id"))
                cc = u.get("cache_creation") or {}
                w1h = cc.get("ephemeral_1h_input_tokens", 0); w5 = u.get("cache_creation_input_tokens", 0) - w1h
                d = by_model.setdefault(m.get("model") or "?", dict.fromkeys(KEYS, 0))
                for k, v in zip(KEYS, (u.get("input_tokens", 0), w5, w1h, u.get("cache_read_input_tokens", 0), u.get("output_tokens", 0))): d[k] += v
            for b in c if isinstance(c, list) else []:
                if isinstance(b, dict) and b.get("type") == "tool_use": calls.append((t, b.get("name"), b.get("input") or {}))
        elif not r.get("isMeta") and not r.get("isSidechain"):
            txt = c if isinstance(c, str) else " ".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text") if isinstance(c, list) else ""
            if txt.strip() and not (isinstance(c, list) and any(isinstance(b, dict) and b.get("type") == "tool_result" for b in c)): prompts.append((t, txt[:80]))
    return by_model, t0, t1, calls, prompts, cs

def stages(calls, prompts, t0, t_end):
    marks = {"1단계": t0}
    for t, name, inp in calls:
        cmd = inp.get("command", "") if name == "Bash" else ""
        for st, rx in STAGES:
            if st in marks: continue
            if rx and re.search(rx, cmd) and (st != "3단계" or "2단계" in marks): marks[st] = t
        if name in ("Agent", "Task") and "2단계" not in marks and re.search(r"맡은 화면|COMPONENTS|screens/(?:<id>|[\w-]+)\.html", inp.get("prompt", "")): marks["2단계"] = t   # 빌드 에이전트(화면 파일을 쓴다) — 1.5단계 반대 입장 에이전트는 아님
    for t, txt in prompts:
        if "/k-style-ui-ux:max" in txt and "max" not in marks: marks["max"] = t
    seq = sorted(marks.items(), key=lambda x: x[1])
    return {st: round(((seq[i + 1][1] if i + 1 < len(seq) else t_end) - t).total_seconds()) for i, (st, t) in enumerate(seq)}

def collect(session_ids):
    seen, agents, notes, cli = set(), [], [], {}
    mains = [p for p in (find(s) for s in dict.fromkeys(session_ids)) if p]
    if not mains: return {"notes": [f"세션 기록 없음: {list(session_ids)} — Claude Code 기록(~/.claude/projects)만 읽는다"]}
    main_calls, main_prompts, T0, T1 = [], [], None, None
    for mp in mains:
        bm, t0, t1, calls, prompts, cs = read(mp, seen)
        if t0 is None: notes.append(f"{mp.name}: 읽을 줄 없음(형식 변경?)"); continue
        T0 = min(T0 or t0, t0); T1 = max(T1 or t1, t1); main_calls += calls; main_prompts += prompts
        agents.append({"agent": "main", "session": mp.stem, "start": t0.isoformat(), "sec": round((t1 - t0).total_seconds()), "models": bm})
        if cs: cli[mp.stem] = {"cost_usd": cs.get("totalCostUSD"), "models": {k: v.get("costUSD") for k, v in (cs.get("modelUsage") or {}).items()}}
        for sp in sorted(glob.glob(str(mp.with_suffix("") / "subagents/*.jsonl"))):
            meta = pathlib.Path(sp[:-6] + ".meta.json")
            mt = json.loads(meta.read_text(encoding="utf-8")) if meta.exists() else {}
            bm, s0, s1, *_ = read(sp, seen)
            if s0 is None: continue
            agents.append({"agent": pathlib.Path(sp).stem, "description": mt.get("description", ""), "type": mt.get("agentType", ""),
                           "start": s0.isoformat(), "sec": round((s1 - s0).total_seconds()), "models": bm})
    if T0 is None: return {"notes": notes}
    for a in agents:
        for md, t in a["models"].items(): t["est_cost_usd"] = cost(md, t)
    def total(rows):
        out = {}
        for a in rows:
            for md, t in a["models"].items():
                d = out.setdefault(md, dict.fromkeys(KEYS, 0))
                for k in KEYS: d[k] += t[k]
        for md, t in out.items(): t["est_cost_usd"] = cost(md, t)
        return out
    subs = [a for a in agents if a["agent"] != "main"]
    spans = [(ts(a["start"]), ts(a["start"]) + datetime.timedelta(seconds=a["sec"])) for a in subs]
    peak = max([sum(1 for s, e in spans if s <= t < e) for t, _ in spans] or [0])
    est = [t["est_cost_usd"] for a in agents for t in a["models"].values()]
    if None in est: notes.append("가격표(PRICE)에 없는 모델이 있어 추정 비용에서 빠짐")
    return {"started": T0.isoformat(), "ended": T1.isoformat(), "wall_sec": round((T1 - T0).total_seconds()),
            "stages_sec": stages(sorted(main_calls, key=lambda x: x[0]), sorted(main_prompts), T0, T1),
            "subagents": len(subs), "peak_concurrent_subagents": peak,
            "est_cost_usd": round(sum(x for x in est if x), 2), "cli_cost_usd": round(sum(v["cost_usd"] or 0 for v in cli.values()), 2) if cli else None,
            "main": total([a for a in agents if a["agent"] == "main"]), "subagent_total": total(subs), "by_model": total(agents),
            "agents": agents, "cli_cost_state": cli, "notes": notes,
            "source": "Claude Code 세션 기록(~/.claude/projects) — 다른 에이전트 기록은 읽지 않는다. 단계별 시간은 스크립트 호출로 잡은 추정"}

if __name__ == "__main__":
    a = sys.argv[1:]; out = None
    if "--out" in a: i = a.index("--out"); out = a[i + 1]; del a[i:i + 2]
    st = collect(a)
    txt = json.dumps(st, ensure_ascii=False, indent=1)
    if out: pathlib.Path(out).write_text(txt, encoding="utf-8")
    brief = {k: st.get(k) for k in ("wall_sec", "stages_sec", "subagents", "peak_concurrent_subagents", "est_cost_usd", "cli_cost_usd", "notes")}
    print(json.dumps(brief, ensure_ascii=False))
