#!/usr/bin/env python3
"""Devin용 허브 서버 — Artifact db 대신 로컬 JSON 저장소.

- GET / 또는 /hub.html : design/probes/hub.html 을 읽어 맨 앞에
  window.claude(fetch 기반 db)를 주입해 서빙한다. hub.html 파일 자체는 건드리지 않음.
- POST /__db {op,path,data} : avail|get|set|update|delete|list → design/probes/feedback.json
- GET /feedback.json : 저장소 원본 (read_db 대용 — 에이전트가 파일을 직접 읽어도 됨)

사용: python design/probes/hub_server.py [--port 8123]
"""
import argparse
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repo root (design/..)
PROBES = os.path.join(BASE, "design", "probes")
STORE = os.path.join(PROBES, "feedback.json")
_LOCK = threading.Lock()

INJECT = """<script>
window.claude={use:function(n){return Promise.resolve(n==='db'?window.__fetchDb:null)}};
window.__fetchDb=(function(){
function rpc(op,path,data){return fetch('/__db',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({op:op,path:path,data:data})}).then(function(r){return r.json()}).then(function(j){if(j.error){var e=new Error(j.error.message||'db error');e.code=j.error.code;throw e;}return j.result});}
function snap(r){return {id:r.id,exists:r.exists,data:function(){return r.data;}};}
var db={doc:function(p){return {id:p.split('/').pop(),path:p,
get:function(){return rpc('get',p).then(snap);},
set:function(d){return rpc('set',p,d);},
update:function(d){return rpc('update',p,d);},
delete:function(){return rpc('delete',p);}};},
collection:function(p){return {path:p,
get:function(){return rpc('list',p).then(function(rs){return {docs:rs.map(snap),size:rs.length,empty:!rs.length};});},
doc:function(id){return db.doc(p+'/'+id);}};}};
return db;})();
</script>
"""


def load_store():
    try:
        with open(STORE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_store(s):
    tmp = STORE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=1)
    os.replace(tmp, STORE)


def db_op(op, path, data):
    with _LOCK:
        s = load_store()
        if op == "avail":
            return True
        if op == "get":
            d = s.get(path)
            return {"id": path.split("/")[-1], "exists": d is not None, "data": d}
        if op == "set":
            s[path] = data
            save_store(s)
            return True
        if op == "update":
            cur = s.get(path) or {}
            cur.update(data or {})
            s[path] = cur
            save_store(s)
            return True
        if op == "delete":
            s.pop(path, None)
            save_store(s)
            return True
        if op == "list":
            prefix = path.rstrip("/") + "/"
            return [
                {"id": k.split("/")[-1], "exists": True, "data": v}
                for k, v in sorted(s.items())
                if k.startswith(prefix)
            ]
        raise ValueError("unknown op: %s" % op)


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="text/html; charset=utf-8"):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        p = self.path.split("?")[0].split("#")[0]
        if p in ("/", "/hub.html"):
            try:
                with open(os.path.join(PROBES, "hub.html"), encoding="utf-8") as f:
                    self._send(200, INJECT + f.read())
            except FileNotFoundError:
                self._send(404, "hub.html not built yet")
            return
        if p == "/feedback.json":
            try:
                with open(STORE, encoding="utf-8") as f:
                    self._send(200, f.read(), "application/json; charset=utf-8")
            except FileNotFoundError:
                self._send(200, "{}", "application/json; charset=utf-8")
            return
        # debug: serve individual probe files
        name = p.lstrip("/")
        fp = os.path.join(PROBES, name)
        if name.endswith(".html") and os.path.isfile(fp):
            with open(fp, encoding="utf-8") as f:
                self._send(200, INJECT + f.read())
            return
        self._send(404, "not found", "text/plain; charset=utf-8")

    def do_POST(self):
        if self.path.split("?")[0] != "/__db":
            self._send(404, "not found", "text/plain; charset=utf-8")
            return
        try:
            n = int(self.headers.get("Content-Length") or 0)
            m = json.loads(self.rfile.read(n) or b"{}")
            result = db_op(m.get("op"), m.get("path") or "", m.get("data"))
            self._send(200, json.dumps({"result": result}, ensure_ascii=False), "application/json; charset=utf-8")
        except Exception as e:
            self._send(200, json.dumps({"error": {"code": "unavailable", "message": str(e)}}), "application/json; charset=utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8123)
    a = ap.parse_args()
    print("hub server: http://localhost:%d  (store: %s)" % (a.port, STORE))
    ThreadingHTTPServer(("127.0.0.1", a.port), H).serve_forever()
