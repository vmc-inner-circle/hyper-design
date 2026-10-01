"""붙여넣은 PRD 원문을 out/prd.md로 저장한다 — 메인이 긴 원문을 다시 쓰지 않도록 대화 기록에서 꺼낸다.

python3 save_prd.py out [--from 파일]
- --from: PRD가 파일이면 그대로 복사
- 아니면 ~/.claude/projects/<현재 폴더>/ 의 가장 최근 세션에서 첫 사용자 메시지를 꺼낸다
- 둘 다 실패하면 종료코드 1 → 메인이 out/prd.md를 직접 쓴다
"""
import sys, json, os, pathlib, argparse, shutil
ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("--from", dest="src")
a = ap.parse_args(); out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
dst = out / "prd.md"
if a.src:
    shutil.copy(a.src, dst); print("copied", dst); sys.exit(0)
cwd = os.path.realpath(os.getcwd())
proj = pathlib.Path.home() / ".claude/projects" / cwd.replace("/", "-").replace(".", "-").replace("_", "-")
cands = sorted(proj.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True) if proj.exists() else []
for f in cands[:3]:
    for line in open(f, encoding="utf-8"):
        try: d = json.loads(line)
        except Exception: continue
        if d.get("type") != "user": continue
        c = d.get("message", {}).get("content")
        if isinstance(c, list): c = "\n".join(x.get("text", "") for x in c if isinstance(x, dict) and x.get("type") == "text")
        if isinstance(c, str) and len(c) > 200:
            dst.write_text(c, encoding="utf-8"); print("saved", dst, len(c), "chars"); sys.exit(0)
        break
print("not found — out/prd.md를 직접 쓴다"); sys.exit(1)
