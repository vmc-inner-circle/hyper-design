"""빠른 자가 점검(v8) — 매니페스트·파일·링크·상태 규칙·금지 문구. 실패 항목을 출력하고 종료코드 1.

python3 selfcheck.py out
"""
import sys, json, re, pathlib

out = pathlib.Path(sys.argv[1]); errs = []
try:
    m = json.loads((out / "screens.json").read_text(encoding="utf-8"))
except Exception as e:
    print("screens.json 읽기 실패:", e); sys.exit(1)
S = m.get("screens", []); ids = {s["id"] for s in S}
base = [s for s in S if "--" not in s["id"]]
if len(base) < 10: errs.append(f"기본 화면 {len(base)}장 < 10")
for k, v in (m.get("prd_coverage") or {}).items():
    if not v: errs.append(f"PRD 커버리지 비어 있음: {k}")
    for x in v:
        if x not in ids: errs.append(f"PRD 커버리지 {k}: 없는 화면 {x}")
if not m.get("prd_coverage"): errs.append("prd_coverage 없음")
if not (out / "journey.md").exists(): errs.append("journey.md(여정표) 없음 — 화면 목록보다 먼저 쓴다")

PLACE = re.compile(r"lorem|TODO|>\s*(텍스트|제목|내용)\s*<|여행\s*1\b", re.I)
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")
PASSIVE = re.compile(r"보기만|읽기 전용|게스트|확인만 하")
for s in S:
    for key in ("title", "group", "purpose", "file"):
        if not s.get(key): errs.append(f'{s["id"]}: {key} 없음')
    if len(s.get("policies", []) or []) == 0 and "--" not in s["id"]: errs.append(f'{s["id"]}: policies(화면 정책) 없음')
    for b in s.get("branches", []) or []:
        if b.get("to") not in ids: errs.append(f'{s["id"]}: 갈래가 없는 화면으로 {b.get("to")}')
    # 상태: traits 에서만 파생
    t = s.get("traits", {}) or {}
    exp = set()
    if t.get("list_first_use"): exp.add("empty")
    if t.get("form"): exp.add("error")
    if "--" not in s["id"]:
        decl = set(s.get("states", []) or [])
        if decl != exp: errs.append(f'{s["id"]}: states {sorted(decl)} ≠ 파생 {sorted(exp)}')
        for st in exp:
            if f'{s["id"]}--{st}' not in ids: errs.append(f'{s["id"]}: 상태 화면 {s["id"]}--{st} 없음')
    f = out / s["file"]
    if not f.exists(): errs.append(f"파일 없음: {s['file']}"); continue
    h = f.read_text(encoding="utf-8")
    n = len(re.findall(r"<h1[\s>]", h))
    if n != 1: errs.append(f"{f.name}: h1 {n}개")
    if 'id="tokens"' not in h or "palette.js" not in h: errs.append(f"{f.name}: <link id=\"tokens\"> 또는 palette.js 없음(원클릭 팔레트 교체 불가)")
    if re.search(r'\sstyle="', h): errs.append(f"{f.name}: 인라인 style")
    if re.search(r"#[0-9a-fA-F]{3,6}\b", re.sub(r"<svg.*?</svg>", "", h, flags=re.S)): errs.append(f"{f.name}: 색 값 하드코딩")
    if PLACE.search(h): errs.append(f"{f.name}: 플레이스홀더 문구")
    if EMOJI.search(h): errs.append(f"{f.name}: 이모지 문자")
    if PASSIVE.search(re.sub(r"<[^>]+>", " ", h)): errs.append(f"{f.name}: 수동적 호칭(보기만·읽기 전용·게스트)")
    if re.search(r'\stitle="', h): errs.append(f"{f.name}: title 속성(툴팁)")
    if 'class="cta"' in h and 'class="tabbar"' in h: errs.append(f"{f.name}: 탭 첫 화면에 하단 고정 CTA")
    for href in re.findall(r'(?:href|src)="([^"#:]+\.(?:html|svg|css|js))"', h):
        if not (f.parent / href).exists(): errs.append(f"{f.name}: 깨진 참조 {href}")
print("\n".join(errs) if errs else "selfcheck OK")
sys.exit(1 if errs else 0)
