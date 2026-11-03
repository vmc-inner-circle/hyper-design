#!/usr/bin/env python3
"""플러그인 폴더 하나를 Claude Code·Codex·Cursor가 함께 설치할 수 있는 상태인지 확인한다.

python3 ci/verify.py
- manifest 4개·마켓 파일 3개가 JSON으로 읽히고, 세 마켓이 같은 플러그인 폴더를 가리킨다
- manifest 4개 버전이 같고 CHANGELOG 맨 위와 같다
- 스킬마다 Codex용 agents/openai.yaml 이 있다
- 스킬 frontmatter에 한 에이전트 전용 필드(allowed-tools 등)가 없다 — 있으면 폴더 하나로 못 나눠 쓴다
- .gitignore에 걸리는 산출물(loop/results·demos·submissions/*/)이 커밋돼 있지 않다 — 있으면 ci/prune_outputs.sh
"""
from __future__ import annotations
import json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
fails: list[str] = []

def load(rel):
    try: return json.loads((ROOT / rel).read_text(encoding="utf-8"))
    except Exception as e: fails.append(f"JSON 읽기 실패: {rel}: {e}"); return {}

cm, xm, um = (load(".claude-plugin/marketplace.json"), load(".agents/plugins/marketplace.json"),
              load(".cursor-plugin/marketplace.json"))
c_src = {Path(p["source"]).as_posix().lstrip("./") for p in cm.get("plugins", [])}
x_src = {Path(p["source"]["path"]).as_posix().lstrip("./") for p in xm.get("plugins", [])}
u_src = {Path(p["source"]).as_posix().lstrip("./") for p in um.get("plugins", [])}
if not c_src == x_src == u_src:
    fails.append(f"세 마켓이 가리키는 폴더가 다르다: Claude {c_src} / Codex {x_src} / Cursor {u_src}")

for rel in sorted(c_src | x_src | u_src):
    plug = ROOT / rel
    mans = [f"{rel}/.claude-plugin/plugin.json", f"{rel}/.codex-plugin/plugin.json",
            f"{rel}/.cursor-plugin/plugin.json", f"{rel}/plugin.json"]
    vers = {m: load(m).get("version") for m in mans}
    cl = re.search(r"^##\s+v(\S+)", (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"), re.M)
    if len(set(vers.values())) != 1 or None in vers.values() or not cl or cl.group(1) != next(iter(vers.values())):
        fails.append(f"버전 불일치: {vers} · CHANGELOG 맨 위 {cl.group(1) if cl else '없음'}")
    for sk in sorted((plug / "skills").glob("*/SKILL.md")):
        name = sk.parent.name
        if not (sk.parent / "agents/openai.yaml").exists():
            fails.append(f"Codex openai.yaml 없음: {rel}/skills/{name}/agents/openai.yaml")
        fm = re.match(r"\A---\n(.*?)\n---\n", sk.read_text(encoding="utf-8"), re.S)
        if not fm: fails.append(f"frontmatter 없음: {name}")
        elif re.search(r"^(allowed-tools|disable-model-invocation|model):", fm.group(1), re.M):
            fails.append(f"한 에이전트 전용 frontmatter: {name} — 폴더 하나를 같이 쓸 수 없다")

tracked = subprocess.run(["git", "ls-files", "-ci", "--exclude-standard"], cwd=ROOT,
                         capture_output=True, text=True).stdout.split()
if tracked:
    fails.append(f"산출물 {len(tracked)}개가 커밋돼 있다(예: {tracked[0]}) — ci/prune_outputs.sh로 빼고 커밋")

if fails:
    print("\n".join("✗ " + f for f in fails)); sys.exit(1)
print("✓ verify OK — 세 마켓이 같은 폴더를 가리키고 버전·openai.yaml·frontmatter가 맞다")
