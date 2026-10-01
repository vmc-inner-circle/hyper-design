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
    if t.get("shares"): exp.add("done")
    if "large_list" not in t and s.get("kind") == "list" and "--" not in s["id"]: errs.append(f'{s["id"]}: traits.large_list(30개 넘게 쌓이는 목록인가) 미선언')
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
    cards = re.findall(r'<section class="block">\s*<p class="(?:info|block-note)">(?:(?!</section>).)*?</p>\s*(?:<button[^>]*>[^<]*</button>\s*)?</section>', h, re.S)
    if len(cards) > 1: errs.append(f"{f.name}: 설명 카드(설명 한 줄만 든 블록) {len(cards)}개 — 설명이 필요한 구조라는 신호(화면당 1개)")
    if re.search(r'class="(?:info|block-note)"[^>]*>(?:(?!</p>).)*누르면', h, re.S): errs.append(f"{f.name}: 조작법 설명('~를 누르면') — 구조로 이해시킨다")
    if 'class="cta"' in h and 'class="tabbar"' in h: errs.append(f"{f.name}: 탭 첫 화면에 하단 고정 CTA")
    for tag in re.findall(r'<[a-z]+ class="row is-add[^"]*"[^>]*>', h):
        hm = re.search(r'href="([^"#]*)', tag)
        if not hm or not hm.group(1) or pathlib.Path(hm.group(1)).name == f.name:
            errs.append(f"{f.name}: '+ 추가' 행이 다른 화면·시트로 이어지지 않음(누른 뒤 모습 없음)")
    if t.get("large_list") and 'type="search"' not in h:
        errs.append(f"{f.name}: 수십 개 목록(large_list)인데 검색 칸 없음")
    for href in re.findall(r'(?:href|src)="([^"#:]+\.(?:html|svg|css|js))"', h):
        if not (f.parent / href).exists(): errs.append(f"{f.name}: 깨진 참조 {href}")
# 제품 판단 장부: PRD 요구사항을 빼거나 가볍게 바꿨으면 반드시 물었어야 한다
try:
    D = json.loads((out / "decisions.json").read_text(encoding="utf-8"))
    if not D.get("core"): errs.append("decisions.json: core(핵심 한 문장) 없음")
    for it in D.get("items", []):
        if it.get("source") == "PRD" and it.get("verdict") in ("cut", "lighten") and not it.get("ask"):
            errs.append(f"decisions.json: PRD 요구사항 '{it.get('name')}'을 묻지 않고 {it['verdict']}")
        if not it.get("why"): errs.append(f"decisions.json: '{it.get('name')}' 판단 이유 없음")
except Exception as e:
    errs.append(f"decisions.json 없음/깨짐: {e}")
# 배지 뜻→색 표: 선언한 표만 쓰고, 한 색에 뜻 하나
BADGES = m.get("badges") or {}
if not BADGES: errs.append("badges(뜻→색 표) 없음")
cls_seen = {}
for mean, cls in BADGES.items():
    if cls in cls_seen: errs.append(f"배지 표: '{mean}'와 '{cls_seen[cls]}'가 같은 색 {cls}")
    cls_seen.setdefault(cls, mean)
for s in S:
    f = out / s["file"]
    if not f.exists(): continue
    for cls, text in re.findall(r'<span class="badge ?([^"]*)">([^<]+)</span>', f.read_text(encoding="utf-8")):
        mean = next((k for k in BADGES if k in text), None)
        if mean is None: errs.append(f"{f.name}: 표에 없는 배지 '{text}'(시간·순서라면 배지 말고 글자로)")
        elif (BADGES[mean] or "") != cls.strip(): errs.append(f"{f.name}: '{text}' 배지 색 {cls or '회색'} ≠ 표 {BADGES[mean] or '회색'}")
print("\n".join(errs) if errs else "selfcheck OK")
sys.exit(1 if errs else 0)
