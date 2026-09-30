"""프로토타입 보기 페이지 만들기 — templates/prototype.html에 board.json을 넣어 {root}/index.html로 쓴다.

사용: python .claude/skills/oss-design-harness/scripts/make_prototype.py --root design
- board.json을 페이지 안에 넣으므로 index.html을 파일로 바로 열어도 동작한다 (fetch 없음).
- 왼쪽 흐름 목록(board.json flows) + 가운데 실제 크기 기기 틀(모바일 390×844 / PC 1280) + 화면 제목·목적.
"""
import argparse, json
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--root", default="design")
args = ap.parse_args()

root = Path(args.root)
repo = Path(__file__).resolve().parents[4]
tpl = (repo / "templates" / "prototype.html").read_text(encoding="utf-8")
board = json.loads((root / "board.json").read_text(encoding="utf-8"))

missing = [s["file"] for s in board.get("screens", []) if not (root / s["file"]).exists()]
if missing:
    raise SystemExit(f"없는 화면 파일: {missing}")

data = json.dumps({k: board.get(k) for k in ("title", "devices", "screens", "flows")}, ensure_ascii=False)
data = data.replace("</", "<\\/")  # </script> 조기 종료 방지
out = tpl.replace("__BOARD_JSON__", data)
# 제출 점검·보드가 화면 링크를 찾을 수 있게 정적 링크 목록도 남긴다 (화면에는 안 보임)
links = "".join(f'<a href="{s["file"]}"></a>' for s in board.get("screens", []))
out = out.replace("</body>", f'<nav hidden aria-hidden="true">{links}</nav>\n</body>', 1)
(root / "index.html").write_text(out, encoding="utf-8", newline="\n")
print(f"{root / 'index.html'} — 화면 {len(board.get('screens', []))}개 · 흐름 {len(board.get('flows') or [])}개")
