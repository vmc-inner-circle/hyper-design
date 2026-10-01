"""하네스 1회 구동: 격리 폴더에서 claude -p 헤드리스 실행, 질문은 가상 사용자가 답한다.
python3 loop/run.py <prd.md> <run_dir> [--max]
플러그인(plugins/hyper-design)을 --plugin-dir로 불러 /hyper-design:go 로 구동. --max면 go가 끝난 뒤 같은 세션에서 /hyper-design:max(1차 결과는 out-go/로 보존)
산출: run_dir/out(결과), prompt-log.md, elapsed.txt, transcript.jsonl
"""
import sys, json, re, shutil, subprocess, time, pathlib, datetime
ROOT = pathlib.Path(__file__).resolve().parent.parent
prd = pathlib.Path(sys.argv[1]).resolve(); run = pathlib.Path(sys.argv[2]).resolve(); DO_MAX = "--max" in sys.argv
PLUGIN = ROOT / "plugins/hyper-design"
MODEL = "claude-opus-5-5"; MAX_TURNS = 4
if run.exists(): shutil.rmtree(run)
work = run / "work"; work.mkdir(parents=True)
shutil.copy(ROOT / "loop/harness-CLAUDE.md", work / "CLAUDE.md")
subprocess.run(["git", "init", "-q"], cwd=work)  # 상위 레포 CLAUDE.md 차단

def claude(prompt, cwd, resume=None, model=MODEL):
    cmd = ["claude", "-p", "--model", model, "--dangerously-skip-permissions", "--output-format", "json", "--plugin-dir", str(PLUGIN)]
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
harness_sec, sid, msg = 0.0, None, "/hyper-design:go\n\n" + prd.read_text(encoding="utf-8")
start = datetime.datetime.now(); turns = 0; status = "max_turns"
while turns < MAX_TURNS:
    turns += 1
    log.append(f"\n## {turns}회" + (" (PRD 입력)\n> " + prd.name + " 원문 그대로\n" if turns == 1 else f"\n> {msg}\n"))
    t0 = time.time(); res = claude(msg, work, sid); dt = time.time() - t0; harness_sec += dt
    sid = res.get("session_id") or sid; text = res.get("result", "")
    trans.write(json.dumps({"turn": turns, "sec": round(dt), "user": msg[:300], "assistant": text}, ensure_ascii=False) + "\n"); trans.flush()
    print(f"[turn {turns}] {dt:.0f}s :: {text[-300:]!r}", flush=True)
    if "[[DONE" in text: status = "done"; break
    m = re.search(r"\[\[ASK(?: ([^\]]+))?\]\](.*)", text, re.S)
    if not m: status = "no_marker"; break
    png = run / f"ask-{turns}.png"
    if m.group(1):                                   # 화면을 보여주는 질문
        page, q = work / m.group(1).strip(), m.group(2).strip()
        try: shoot(page, png)
        except Exception as e: print("shot fail", e)
    else:                                            # 글로만 묻는 확인(제품 판단) — 마커 앞 본문이 질문
        q = text[:m.start()].strip()[-1200:]
        png = "(없음)"
    ans = claude(SIM.replace("{{QUESTION}}", q).replace("{{IMAGE}}", str(png)).replace("{{ASSISTANT}}", text[-1500:]),
                 run, model="claude-sonnet-5-5").get("result", "").strip().splitlines()[-1].strip()
    log[-1] += ""
    log.append("> (AI 질문) " + q.replace("\n", "\n> ") + "\n")
    msg = ans
go_sec = harness_sec; max_sec = 0.0
if DO_MAX and status == "done":
    if (work / "out").exists(): shutil.copytree(work / "out", run / "out-go", ignore=shutil.ignore_patterns(".shots", ".cands"))
    turns += 1; log.append(f"\n## {turns}회 (/hyper-design:max)\n")
    t0 = time.time(); res = claude("/hyper-design:max", work, sid); max_sec = time.time() - t0; harness_sec += max_sec
    text = res.get("result", ""); trans.write(json.dumps({"turn": turns, "sec": round(max_sec), "user": "/hyper-design:max", "assistant": text}, ensure_ascii=False) + "\n"); trans.flush()
    print(f"[max] {max_sec:.0f}s :: {text[-300:]!r}", flush=True)
    status = "done" if "[[DONE" in text else "max_no_marker"
end = datetime.datetime.now()
if (work / "out").exists(): shutil.copytree(work / "out", run / "out")
(run / "prompt-log.md").write_text("".join(log) + f"\n\n총 개입 횟수: {turns} / 5 · 종료 상태: {status}\n", encoding="utf-8")
(run / "elapsed.txt").write_text(f"시작: {start:%Y-%m-%d %H:%M}\n종료: {end:%Y-%m-%d %H:%M}\n하네스 실행 시간(가상 사용자 응답 제외): {harness_sec/60:.1f}분\n" + (f"1차(go) {go_sec/60:.1f}분 · 2차(max) {max_sec/60:.1f}분\n" if DO_MAX else ""), encoding="utf-8")
print(json.dumps({"status": status, "turns": turns, "harness_min": round(harness_sec / 60, 1), "go_min": round(go_sec / 60, 1), "max_min": round(max_sec / 60, 1)}))
