"""구동 첫 단계 — 공통 파일을 한 번에 준비한다(메인이 여정표를 쓰는 동안 백그라운드로).

python3 setup_out.py out --domain 여행 --tags "따뜻함,편안함,신뢰"
→ out/components.css · out/palette.js · out/assets/fluent/ · out/tokens.css + tokens-<slug>.css ×3 · out/palettes.json
"""
import argparse, pathlib, shutil, subprocess, sys
F = pathlib.Path(__file__).resolve().parent.parent / "foundation"
ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("--domain", default=""); ap.add_argument("--tags", default="")
a = ap.parse_args(); out = pathlib.Path(a.out); (out / "screens").mkdir(parents=True, exist_ok=True)
shutil.copy(F / "components.css", out / "components.css"); shutil.copy(F / "palette.js", out / "palette.js")
shutil.copytree(F / "assets", out / "assets", dirs_exist_ok=True)
r = subprocess.run([sys.executable, str(F.parent / "scripts" / "palette_pick.py"), str(out), "--domain", a.domain, "--tags", a.tags], capture_output=True, text=True)
print(r.stdout.strip() or r.stderr.strip())
print("setup ok:", ", ".join(sorted(p.name for p in out.iterdir())))
