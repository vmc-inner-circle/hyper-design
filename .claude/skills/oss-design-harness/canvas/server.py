"""화이트보드 캔버스용 로컬 서버 (표준 라이브러리만 사용).

design/ 폴더를 루트로 화면을 서빙하고, 캔버스(canvas.html·lib/)와 스키마(schema/)는 스킬 폴더에서 준다.
캔버스가 보낸 저장 요청 하나를 feedback.json(에이전트용)과 canvas-state.json(복원용)으로 나눠 쓴다.
캔버스(canvas.html)와 화면(screens/*.html)이 같은 오리진이어야 코멘트를 화면 안 요소에 연결할 수 있다.

사용법:
    python .claude/skills/oss-design-harness/canvas/server.py --root design --port 4321
"""

import argparse
import json
import sys
from datetime import datetime
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

SHELL = Path(__file__).with_name("canvas.html")
SCHEMA = Path(__file__).resolve().parents[1] / "schema"  # 공통 약속은 스킬 폴더의 schema/
LIB = Path(__file__).with_name("lib")


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        if self.path == "/api/version":
            # 캔버스가 2초마다 확인해 바뀌면 새로고침. 피드백 파일은 제외(저장할 때마다 새로고침되면 안 됨)
            root = Path(self.directory)
            watched = [root / "board.json", root / "theme.js", *root.glob("screens/**/*")]
            body = str(max((p.stat().st_mtime_ns for p in watched if p.is_file()), default=0)).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path.split("?")[0] in ("/", "/canvas", "/canvas.html"):  # ?view=mobile 같은 보기 전환 주소도 캔버스
            self.send_file(SHELL, "text/html; charset=utf-8")
            return
        for prefix, folder, ctype in (("/schema/", SCHEMA, "application/json; charset=utf-8"),
                                      ("/lib/", LIB, "text/javascript; charset=utf-8")):
            if self.path.startswith(prefix):
                # 기기 규격·스키마·캔버스 모듈은 스킬 폴더에서 (design/ 밖)
                f = folder / Path(self.path).name
                if f.is_file():
                    self.send_file(f, ctype)
                else:
                    self.send_error(404)
                return
        super().do_GET()

    def send_file(self, path, ctype):
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/api/feedback":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", 0))
        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            self.send_error(400, "invalid json")
            return
        # 한 번 받아 두 파일로: 에이전트용(feedback.json)과 Excalidraw 복원용(canvas-state.json)
        now = datetime.now().isoformat(timespec="seconds")
        root = Path(self.directory)
        # 지난 라운드를 띄워 둔 페이지의 저장은 받지 않는다 (에이전트가 피드백 파일을 옮긴 뒤 되살아나지 않게)
        round_ = json.loads((root / "board.json").read_text(encoding="utf-8")).get("round", 0)
        if data.get("round", 0) != round_:
            self.send_error(409, "stale round")
            return
        feedback = {"board": data.get("board", ""), "round": round_, "items": data.get("items", []),
                    "renderChecks": data.get("renderChecks", []),
                    "discovered": data.get("discovered", []), "saved_at": now}
        state = {"round": round_, "scene": data.get("scene", []), "files": data.get("files", {}),
                 "moved": data.get("moved", {}), "components": data.get("components", {}), "saved_at": now}
        for name, obj in (("feedback.json", feedback), ("canvas-state.json", state)):
            (root / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[feedback] 피드백 {len(feedback['items'])}개 · 자동 점검 {len(feedback['renderChecks'])}개 저장")
        body = b'{"ok":true}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="design")
    ap.add_argument("--port", type=int, default=4321)
    args = ap.parse_args()
    root = Path(args.root).resolve()
    if not (root / "board.json").exists():
        sys.exit(f"{root}/board.json 이 없습니다. 화면과 board.json을 먼저 만드세요.")
    server = ThreadingHTTPServer(("127.0.0.1", args.port), partial(Handler, directory=str(root)))
    print(f"캔버스: http://localhost:{args.port}/  (루트 {root})")
    server.serve_forever()


if __name__ == "__main__":
    main()
