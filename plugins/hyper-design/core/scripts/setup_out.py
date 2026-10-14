"""구동 첫 단계 — 공통 파일을 한 번에 준비한다(메인이 여정표를 쓰는 동안 백그라운드로).

python3 setup_out.py out --domain 여행 --tags "따뜻함,편안함,신뢰"
→ out/components.css · out/palette.js · out/assets/fluent/(Tier 0 아이콘, features/icons/core) · out/tokens.css + tokens-<slug>.css ×3 · out/palettes.json
"""
import argparse, pathlib, shutil, subprocess, sys
F = pathlib.Path(__file__).resolve().parent.parent / "foundation"
ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("--domain", default=""); ap.add_argument("--tags", default=""); ap.add_argument("--temp", default="")
a = ap.parse_args(); out = pathlib.Path(a.out); (out / "screens").mkdir(parents=True, exist_ok=True)
shutil.copy(F / "components.css", out / "components.css"); shutil.copy(F / "palette.js", out / "palette.js")
ICONS = F.parent / "features" / "icons" / "core"   # Tier 0 아이콘(svg + LICENSE.md)
for d in (F / "assets").iterdir() if (F / "assets").exists() else []:
    if d.is_dir() and d.name != "fluent": shutil.copytree(d, out / "assets" / d.name, dirs_exist_ok=True)
    elif d.is_file(): (out / "assets").mkdir(parents=True, exist_ok=True); shutil.copy(d, out / "assets" / d.name)
(out / "assets" / "fluent").mkdir(parents=True, exist_ok=True)
for f in ICONS.iterdir():
    if f.suffix == ".svg" or f.name == "LICENSE.md": shutil.copy(f, out / "assets" / "fluent" / f.name)
r = subprocess.run([sys.executable, str(F.parent / "scripts" / "palette_pick.py"), str(out), "--domain", a.domain, "--tags", a.tags] + (["--temp", a.temp] if a.temp else []), capture_output=True, text=True, encoding="utf-8", errors="replace")
print(r.stdout.strip() or r.stderr.strip())
print("setup ok:", ", ".join(sorted(p.name for p in out.iterdir())))
