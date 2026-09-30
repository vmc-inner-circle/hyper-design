"""빠른 자가 점검 (파일·링크·상태 규칙·금칙어). 실패 항목을 출력하고 종료코드 1."""
import sys, json, re, pathlib
out = pathlib.Path(sys.argv[1]); errs = []
try: m = json.loads((out / "screens.json").read_text(encoding="utf-8"))
except Exception as e: print("screens.json 읽기 실패:", e); sys.exit(1)
ids = {s["id"] for s in m["screens"]}
if len(ids) < 12: errs.append(f"화면 수 {len(ids)} < 12")
for k, v in m.get("prd_coverage", {}).items():
    if not v: errs.append(f"PRD 커버리지 비어 있음: {k}")
PLACE = re.compile(r"lorem|TODO|>\s*(텍스트|제목|내용)\s*<|여행\s*1\b", re.I)
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")
for s in m["screens"]:
    exp = set()
    t = s.get("traits", {})
    if t.get("list_first_use"): exp.add("empty")
    if t.get("form") or t.get("sends"): exp.add("error")
    if t.get("readonly_role"): exp.add("disabled")
    decl = set(s.get("states", []))
    if decl != exp: errs.append(f'{s["id"]}: states {sorted(decl)} ≠ 파생 {sorted(exp)}')
    files = [out / s["file"]] + [out / "screens" / f'{s["id"]}--{st}.html' for st in exp]
    for f in (out / "screens").glob(f'{s["id"]}--*.html'):
        if f.stem.split("--")[1] not in exp: errs.append(f"규칙에 없는 상태 파일: {f.name}")
    for f in files:
        if not f.exists(): errs.append(f"파일 없음: {f.relative_to(out)}"); continue
        h = f.read_text(encoding="utf-8")
        n = len(re.findall(r"<h1[\s>]", h))
        if n != 1: errs.append(f"{f.name}: h1 {n}개")
        if PLACE.search(h): errs.append(f"{f.name}: 플레이스홀더 문구")
        if EMOJI.search(h): errs.append(f"{f.name}: 이모지")
        if re.search(r'\stitle="', h): errs.append(f"{f.name}: title 속성(툴팁)")
        if "gradient" in h: errs.append(f"{f.name}: 그라데이션")
        for href in re.findall(r'href="([^"#:]+\.html)"', h):
            if not (f.parent / href).exists(): errs.append(f"{f.name}: 깨진 링크 {href}")
    for l in s.get("links", []):
        if l not in ids: errs.append(f'{s["id"]}: 없는 화면으로 연결 {l}')
print("\n".join(errs) if errs else "selfcheck OK")
sys.exit(1 if errs else 0)
