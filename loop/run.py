"""하네스 1회 구동: 격리 폴더에서 claude -p 헤드리스 실행, 질문은 가상 사용자가 답한다.
python3 loop/run.py <prd.md> <run_dir>
산출: run_dir/out(결과), prompt-log.md, elapsed.txt, transcript.jsonl
"""
import sys, json, re, shutil, subprocess, time, pathlib, datetime
ROOT = pathlib.Path(__file__).resolve().parent.parent
prd = pathlib.Path(sys.argv[1]).resolve(); run = pathlib.Path(sys.argv[2]).resolve()
MODEL = "claude-opus-5-5"; MAX_TURNS = 4
if run.exists(): shutil.rmtree(run)
work = run / "work"; (work / ".claude/skills").mkdir(parents=True)
shutil.copytree(ROOT / ".claude/skills/oss-design-harness", work / ".claude/skills/oss-design-harness")
shutil.copy(ROOT / "loop/harness-CLAUDE.md", work / "CLAUDE.md")
subprocess.run(["git", "init", "-q"], cwd=work)  # 상위 레포 CLAUDE.md 차단

def claude(prompt, cwd, resume=None, model=MODEL):
    cmd = ["claude", "-p", "--model", model, "--dangerously-skip-permissions", "--output-format", "json"]
    if resume: cmd += ["--resume", resume]
    r = subprocess.run(cmd, input=prompt, capture_output=True, text=True, cwd=cwd)
    try: return json.loads(r.stdout)
    except Exception: return {"result": r.stdout + r.stderr, "session_id": resume, "is_error": True}

def shoot(html, png):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome")
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        pg.goto(html.as_uri()); pg.wait_for_timeout(1500)
        pg.screenshot(path=str(png), full_page=True); b.close()

SIM = (ROOT / "loop/sim_user.md").read_text(encoding="utf-8")
log = [f"# prompt-log\n\n- 하네스: solo/greatSumini `.claude/skills/oss-design-harness`\n- 모델: Claude Code headless / {MODEL}\n- 답변자: 가상 사용자 에이전트(비개발자 페르소나, loop/sim_user.md)\n"]
trans = open(run / "transcript.jsonl", "w")
harness_sec, sid, msg = 0.0, None, prd.read_text(encoding="utf-8")
start = datetime.datetime.now(); turns = 0; status = "max_turns"
while turns < MAX_TURNS:
    turns += 1
    log.append(f"\n## {turns}회" + (" (PRD 입력)\n> " + prd.name + " 원문 그대로\n" if turns == 1 else f"\n> {msg}\n"))
    t0 = time.time(); res = claude(msg, work, sid); dt = time.time() - t0; harness_sec += dt
    sid = res.get("session_id") or sid; text = res.get("result", "")
    trans.write(json.dumps({"turn": turns, "sec": round(dt), "user": msg[:300], "assistant": text}, ensure_ascii=False) + "\n"); trans.flush()
    print(f"[turn {turns}] {dt:.0f}s :: {text[-300:]!r}", flush=True)
    if "[[DONE" in text: status = "done"; break
    m = re.search(r"\[\[ASK ([^\]]+)\]\](.*)", text, re.S)
    if not m: status = "no_marker"; break
    page, q = work / m.group(1).strip(), m.group(2).strip()
    png = run / f"ask-{turns}.png"
    try: shoot(page, png)
    except Exception as e: print("shot fail", e)
    ans = claude(SIM.replace("{{QUESTION}}", q).replace("{{IMAGE}}", str(png)).replace("{{ASSISTANT}}", text[-1500:]),
                 run, model="claude-sonnet-5-5").get("result", "").strip().splitlines()[-1].strip()
    log[-1] += ""
    log.append(f"> (AI 질문) {q}\n")
    msg = ans
end = datetime.datetime.now()
if (work / "out").exists(): shutil.copytree(work / "out", run / "out")
(run / "prompt-log.md").write_text("".join(log) + f"\n\n총 개입 횟수: {turns} / 5 · 종료 상태: {status}\n", encoding="utf-8")
(run / "elapsed.txt").write_text(f"시작: {start:%Y-%m-%d %H:%M}\n종료: {end:%Y-%m-%d %H:%M}\n하네스 실행 시간(가상 사용자 응답 제외): {harness_sec/60:.1f}분\n", encoding="utf-8")
print(json.dumps({"status": status, "turns": turns, "harness_min": round(harness_sec / 60, 1)}))
