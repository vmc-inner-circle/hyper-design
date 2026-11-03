"""붙여넣은 PRD 원문을 out/prd.md로 저장한다 — 메인이 긴 원문을 다시 쓰지 않도록 대화 기록에서 꺼낸다.

python3 save_prd.py out [--from 파일]
- --from: PRD가 파일이면 그대로 복사
- 아니면 대화 기록에서 현재 폴더 세션의 첫 긴 사용자 메시지를 꺼낸다(최근 수정된 세션부터)
  - Claude Code: ~/.claude/projects/<현재 폴더>/*.jsonl
  - Codex: ~/.codex/sessions/**/rollout-*.jsonl 중 cwd가 현재 폴더인 것
  - Cursor: ~/.cursor/projects/<현재 폴더>/agent-transcripts/*/*.jsonl
- 모두 실패하면 종료코드 1 → 메인이 out/prd.md를 직접 쓴다
"""
import sys, json, os, re, pathlib, argparse, shutil
ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("--from", dest="src")
a = ap.parse_args(); out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
dst = out / "prd.md"
if a.src:
    shutil.copy(a.src, dst); print("copied", dst); sys.exit(0)
cwd = os.path.realpath(os.getcwd())
home = pathlib.Path.home()

def claude_messages(f):
    for line in open(f, encoding="utf-8"):
        try: d = json.loads(line)
        except Exception: continue
        if d.get("type") != "user": continue
        c = d.get("message", {}).get("content")
        if isinstance(c, list): c = "\n".join(x.get("text", "") for x in c if isinstance(x, dict) and x.get("type") == "text")
        if isinstance(c, str) and "<command-args>" in c:      # /k-style-ui-ux:go <PRD> 로 받은 경우
            c = c.split("<command-args>", 1)[1].rsplit("</command-args>", 1)[0]
        if isinstance(c, str) and "<command-name>" in c and len(c) < 400: continue   # 인자 없는 명령 — 다음 메시지가 PRD
        if isinstance(c, str): yield c

def codex_messages(f):
    with open(f, encoding="utf-8") as fh:
        try: meta = json.loads(fh.readline())
        except Exception: return
        if os.path.realpath(meta.get("payload", {}).get("cwd") or "") != cwd: return
        for line in fh:
            try: d = json.loads(line)
            except Exception: continue
            p = d.get("payload", {})
            if d.get("type") == "event_msg" and p.get("type") == "user_message" and isinstance(p.get("message"), str):
                yield re.sub(r"^\s*\$[\w:-]+\s*", "", p["message"])   # "$k-style-ui-ux:go <PRD>"로 받은 경우 스킬 이름은 뗀다

def cursor_messages(f):
    for line in open(f, encoding="utf-8"):
        try: d = json.loads(line)
        except Exception: continue
        if d.get("role") != "user": continue
        c = d.get("message", {}).get("content")
        if isinstance(c, list): c = "\n".join(x.get("text", "") for x in c if isinstance(x, dict) and x.get("type") == "text")
        if not isinstance(c, str): continue
        m = re.search(r"<user_query>\s*(.*?)\s*</user_query>", c, re.S)
        yield re.sub(r"^\s*/[\w:-]+\s*", "", m.group(1) if m else c)   # "/go <PRD>"로 받은 경우 스킬 이름은 뗀다

proj = home / ".claude/projects" / cwd.replace("/", "-").replace(".", "-").replace("_", "-")
cands = [(f, claude_messages) for f in proj.glob("*.jsonl")] if proj.exists() else []
sess = home / ".codex/sessions"
if sess.exists():
    recent = sorted(sess.glob("*/*/*/rollout-*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)[:20]
    cands += [(f, codex_messages) for f in recent]
cur = home / ".cursor/projects" / re.sub(r"[^A-Za-z0-9]+", "-", cwd).strip("-")
cands += [(f, cursor_messages) for f in cur.glob("agent-transcripts/*/*.jsonl")]
cands.sort(key=lambda x: x[0].stat().st_mtime, reverse=True)
for f, read in cands[:5]:
    for c in read(f):
        if len(c) > 200:
            dst.write_text(c, encoding="utf-8"); print("saved", dst, len(c), "chars", "from", f.name); sys.exit(0)
        break   # 첫 메시지가 짧으면 PRD가 대화에 없다 — 다음 세션을 본다
print("not found — out/prd.md를 직접 쓴다"); sys.exit(1)
