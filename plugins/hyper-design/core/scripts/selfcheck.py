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
# 명세 목록(v13): 원문 인용 · 커버 · 규칙 → 상태
INV = {}
try: INV = json.loads((out / "spec_inventory.json").read_text(encoding="utf-8"))
except Exception as e: errs.append(f"spec_inventory.json 없음/깨짐: {e}")
PRD = (out / "prd.md").read_text(encoding="utf-8") if (out / "prd.md").exists() else ""
if not PRD: errs.append("out/prd.md 없음 — save_prd.py로 원문을 저장한다")
norm = lambda x: re.sub(r"\s+", "", x or "")
NPRD = norm(PRD)
RULE_ST = {}
for it in INV.get("items", []):
    iid, k = it.get("id"), it.get("kind")
    if PRD and it.get("quote") and norm(it["quote"])[:60] not in NPRD: errs.append(f"명세 {iid}: quote가 PRD 원문에 없음(지어낸 항목)")
    if k in ("screen", "step", "feature"):
        cov = [x for x in it.get("covered_by") or [] if x in ids]
        if not cov and not it.get("decision"): errs.append(f"명세 {iid} '{it.get('name')}': 덮는 화면도 결정(decision)도 없음")
    if k == "step" and it.get("covered_by") and not any(x in ids for x in it["covered_by"]): errs.append(f"명세 단계 {iid}: 화면 없음")
    if k == "rule":
        if it.get("target") and it.get("state"): RULE_ST.setdefault(it["target"], set()).add(it["state"])
        elif not it.get("policy"): errs.append(f"명세 규칙 {iid}: target·state(상태 화면) 또는 policy(정책 문구로 내린 화면 id) 필요")
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
PERSON = {"mother", "father", "jieun", "minsu", "hayun"}
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
    if t.get("long_task"): exp.add("progress")
    exp |= RULE_ST.get(s["id"], set())
    if m.get("stage") == "go": exp &= {"done"}          # 1차는 결과 화면만 — 나머지는 /hyper-design:max
    if "large_list" not in t and s.get("kind") == "list" and "--" not in s["id"]: errs.append(f'{s["id"]}: traits.large_list(30개 넘게 쌓이는 목록인가) 미선언')
    if "--" not in s["id"]:
        decl = set(s.get("states", []) or [])
        if decl != exp: errs.append(f'{s["id"]}: states {sorted(decl)} ≠ 파생 {sorted(exp)} — expand_states.py를 다시 돌린다')
        if len(exp) > 2: errs.append(f'{s["id"]}: 상태 {len(exp)}개 > 2(기본 포함 3)')
        for st in exp:
            if f'{s["id"]}--{st}' not in ids: errs.append(f'{s["id"]}: 상태 화면 {s["id"]}--{st} 없음')
    f = out / s["file"]
    if not f.exists(): errs.append(f"파일 없음: {s['file']}"); continue
    h = f.read_text(encoding="utf-8")
    n = len(re.findall(r"<h1[\s>]", h))
    if n != 1: errs.append(f"{f.name}: h1 {n}개")
    if 'id="tokens"' not in h or "palette.js" not in h: errs.append(f"{f.name}: <link id=\"tokens\"> 또는 palette.js 없음(원클릭 팔레트 교체 불가)")
    for st in re.findall(r'\sstyle="([^"]*)"', h):   # CSS 변수 지정(--from 등)만 예외
        if any(not d.strip().startswith("--") for d in st.split(";") if d.strip()): errs.append(f"{f.name}: 인라인 style"); break
    if re.search(r"#[0-9a-fA-F]{3,6}\b", re.sub(r"<svg.*?</svg>", "", h, flags=re.S)): errs.append(f"{f.name}: 색 값 하드코딩")
    if PLACE.search(h): errs.append(f"{f.name}: 플레이스홀더 문구")
    if EMOJI.search(h): errs.append(f"{f.name}: 이모지 문자")
    if PASSIVE.search(re.sub(r"<[^>]+>", " ", h)): errs.append(f"{f.name}: 수동적 호칭(보기만·읽기 전용·게스트)")
    if re.search(r'\stitle="', h): errs.append(f"{f.name}: title 속성(툴팁)")
    cards = re.findall(r'<section class="block">\s*<p class="(?:info|block-note)">(?:(?!</section>).)*?</p>\s*(?:<button[^>]*>[^<]*</button>\s*)?</section>', h, re.S)
    if len(cards) > 1: errs.append(f"{f.name}: 설명 카드(설명 한 줄만 든 블록) {len(cards)}개 — 설명이 필요한 구조라는 신호(화면당 1개)")
    if re.search(r'class="(?:info|block-note)"[^>]*>(?:(?!</p>).)*누르면', h, re.S): errs.append(f"{f.name}: 조작법 설명('~를 누르면') — 구조로 이해시킨다")
    if 'class="cta"' in h and 'class="tabbar"' in h: errs.append(f"{f.name}: 탭 첫 화면에 하단 고정 CTA")
    for blk in re.findall(r'<(?:div|figure|span) class="(?:photo|thumb)[^"]*"[^>]*>(.*?)</(?:div|figure|span)>', h, re.S):
        if "<img" not in blk: errs.append(f"{f.name}: 사진 자리에 이미지 없음(글자만) — assets/photos 또는 assets/domain 이미지를 넣는다")
    for tag in re.findall(r'<[a-z]+ class="row is-add[^"]*"[^>]*>', h):
        hm = re.search(r'href="([^"#]*)', tag)
        if not hm or not hm.group(1) or pathlib.Path(hm.group(1)).name == f.name:
            errs.append(f"{f.name}: '+ 추가' 행이 다른 화면·시트로 이어지지 않음(누른 뒤 모습 없음)")
    if t.get("large_list") and 'type="search"' not in h:
        errs.append(f"{f.name}: 수십 개 목록(large_list)인데 검색 칸 없음")
    for img in re.findall(r'class="avatar[^"]*">\s*<img src="[^"]*/([a-z]+)\.svg"', h):
        if img not in PERSON: errs.append(f"{f.name}: 사람 자리(avatar)에 사물 일러스트 {img} — 글자 아바타(avatar is-text)로")
    for href in re.findall(r'(?:href|src)="([^"#:]+\.(?:html|svg|css|js))"', h):
        if not (f.parent / href).exists(): errs.append(f"{f.name}: 깨진 참조 {href}")
# 흐름 고리(v14): 사용자가 만들거나 신청하는 대상마다 시작·끝이 있어야 한다
OBJ = INV.get("objects")
if OBJ is None: errs.append("spec_inventory.json: objects(흐름 고리) 없음 — 사용자가 만들·신청하는 대상마다 create/view/edit/after")
for o in OBJ or []:
    for step in ("create", "view", "edit", "after"):
        v = o.get(step)
        if not v: errs.append(f"흐름 고리 '{o.get('name')}': {step} 비어 있음"); continue
        if isinstance(v, str) and v.startswith("n/a"):
            if step in ("create", "view", "after") and "운영" not in v and "시스템" not in v: errs.append(f"흐름 고리 '{o.get('name')}': {step}는 n/a 불가(사용자가 처음 만드는 화면이 있어야 한다)")
            if len(v) < 8: errs.append(f"흐름 고리 '{o.get('name')}': {step} n/a 이유 없음")
            continue
        for x in (v if isinstance(v, list) else [v]):
            if x not in ids: errs.append(f"흐름 고리 '{o.get('name')}': {step} → 없는 화면 {x}")
        if step == "after":
            byid = {x["id"]: x for x in S}
            res = [x for x in (v if isinstance(v, list) else [v]) if x in byid and (x.endswith("--done") or byid[x].get("kind") == "result")]
            if not res: errs.append(f"흐름 고리 '{o.get('name')}': after에 결과 화면이 없음({v}) — 목록·상세가 아니라 그 행동이 끝난 모습(kind: result 또는 --done)")
# 사람 카드(v16): 이 앱이 누구를 위한 것인가 — 사람마다 처음 오는 이유·마음·알고 싶은 것(답이 보일 화면)·성공한 순간
PEOPLE = m.get("people") or []; WANTS_Q = []
if not 1 <= len(PEOPLE) <= 4: errs.append(f"people(사람 카드) {len(PEOPLE)}명 — 1~4명, journey.md 사람 카드를 옮긴다")
if PEOPLE and sum(1 for p in PEOPLE if p.get("core")) != 1: errs.append("people: 핵심 사람(core: true)은 한 명")
for p in PEOPLE:
    nm = p.get("name") or "?"
    for k in ("who", "why", "feels", "win"):
        if not p.get(k): errs.append(f"people '{nm}': {k} 없음")
    W = p.get("wants") or []
    if not 2 <= len(W) <= 5: errs.append(f"people '{nm}': wants(알고 싶은 것) {len(W)}개 — 2~5개")
    for w in W:
        at = [x for x in w.get("at") or [] if x in ids]
        if not w.get("q") or not at: errs.append(f"people '{nm}': 알고 싶은 것 '{w.get('q')}'의 답이 보일 화면(at) 없음")
        WANTS_Q.append(re.sub(r"[\s?？.]", "", w.get("q") or ""))
    for x in p.get("screens") or []:
        if x not in ids: errs.append(f"people '{nm}': 없는 화면 {x}")
    if not p.get("screens"): errs.append(f"people '{nm}': screens(주로 쓰는 화면) 없음")
for s in S:                                   # 질문은 위계에만 — 한 화면에 질문 문장이 여럿이면 질답지(큐레이션 제목 하나는 허용)
    f = out / s["file"]
    if not f.exists(): continue
    txt = re.sub(r"[\s?？.]", "", re.sub(r"<[^>]+>", " ", f.read_text(encoding="utf-8")))
    hit = [q for q in WANTS_Q if len(q) >= 8 and q in txt]
    if len(hit) >= 2: errs.append(f"{f.name}: 사람 카드의 질문 {len(hit)}개를 화면 문구로 씀(질답지) — 큐레이션 제목 하나 말고는 데이터의 자리·크기로 답한다")
# 탭·세그먼트: 칸마다 그 내용을 보여 주는 화면
for s in S:
    for t in s.get("tabs") or []:
        if t.get("screen") not in ids: errs.append(f"{s['id']}: 탭 '{t.get('label')}'의 화면 {t.get('screen')} 없음")
# 이미지: 스톡 사진은 출처 기록 필수, 라이선스 제한
photos = sorted((out / "assets/photos").glob("*.jpg")) if (out / "assets/photos").exists() else []
try: CR = {c.get("file"): c for c in json.loads((out / "credits.json").read_text(encoding="utf-8"))}
except Exception: CR = {}
for ph in photos:
    rel = f"assets/photos/{ph.name}"; c = CR.get(rel)
    if not c: errs.append(f"{rel}: credits.json에 출처 없음(자리표시 그대로면 drawing으로 바꾼다)")
dom = list((out / "assets/domain").glob("*")) if (out / "assets/domain").exists() else []
if m.get("photo_centric") and not photos and not dom: errs.append("photo_centric인데 이미지가 하나도 없음")
# 제품 판단 장부: PRD 요구사항을 빼거나 가볍게 바꿨으면 반드시 물었어야 한다
try:
    D = json.loads((out / "decisions.json").read_text(encoding="utf-8"))
    if not D.get("core"): errs.append("decisions.json: core(핵심 한 문장) 없음")
    if INV.get("mode") == "spec":
        pc = [i for i in D.get("items", []) if i.get("source") == "PRD" and i.get("verdict") == "cut"]
        if len(pc) > 3: errs.append(f"명세 모드에서 PRD 요구사항 {len(pc)}개 cut > 3 — 과삭제, 되살린다")
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
# 강조색(v17): screens.json accent에 선언한 뜻 하나 · 8자 이하 글자/점 · 화면당 2곳(목록 반복은 1곳) · 제목·버튼·배지 밖
from html.parser import HTMLParser
ACCENT = m.get("accent")
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
NO_ACCENT_TAG = {"h1", "h2", "h3", "button"}; NO_ACCENT_CLS = {"btn", "cta", "badge", "tabbar", "tab", "appbar-title", "title"}
ITEM_CLS = {"row", "card", "tile", "item"}
class AccentScan(HTMLParser):
    def __init__(self):
        super().__init__(); self.stack, self.n, self.hits, self.cur = [], 0, [], None
    def handle_starttag(self, tag, attrs):
        a = dict(attrs); cls = set((a.get("class") or "").split()); self.n += 1
        node = (tag, cls, self.n)
        kind = "accent-text" if "accent-text" in cls else "accent-dot" if "accent-dot" in cls else None
        if kind:
            chain = self.stack + [node]
            bad = next((t if t in NO_ACCENT_TAG else "/".join(c & NO_ACCENT_CLS) for t, c, _ in chain if t in NO_ACCENT_TAG or c & NO_ACCENT_CLS), None)
            items = [i for i, (t, c, _) in enumerate(self.stack) if t == "li" or c & ITEM_CLS]
            slot = ("list", self.stack[items[-1] - 1][2]) if items and items[-1] > 0 else ("one", self.n)   # 목록 반복은 그 목록 하나로 센다
            self.hits.append({"kind": kind, "bad": bad, "slot": slot, "text": "", "label": a.get("aria-label")})
            if kind == "accent-text": self.cur = (len(self.stack), self.hits[-1])
        if tag not in VOID: self.stack.append(node)
    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                if self.cur and len(self.stack) <= self.cur[0]: self.cur = None
                return
    def handle_data(self, d):
        if self.cur: self.cur[1]["text"] += d
for s in S:
    f = out / s["file"]
    if not f.exists(): continue
    h = f.read_text(encoding="utf-8")
    if any("--c-accent" in st for st in re.findall(r"<style[^>]*>(.*?)</style>", h, re.S)): errs.append(f"{f.name}: <style>에서 --c-accent 직접 사용 — 강조색은 .accent-text·.accent-dot으로만")
    sc = AccentScan(); sc.feed(h); H = sc.hits
    if not H: continue
    if not ACCENT: errs.append(f"{f.name}: 강조 부품 {len(H)}개를 썼는데 screens.json accent(뜻 하나) 미선언"); continue
    for x in H:
        if x["bad"]: errs.append(f"{f.name}: {x['kind']}가 {x['bad']} 안에 있음 — 제목·버튼·배지에는 강조색을 쓰지 않는다")
        t = re.sub(r"\s+", " ", x["text"]).strip()
        if x["kind"] == "accent-text" and not 0 < len(t) <= 8: errs.append(f"{f.name}: 강조 글자 '{t[:20]}' {len(t)}자 — 8자 이하 한 덩어리만")
        if x["kind"] == "accent-dot" and not x["label"]: errs.append(f"{f.name}: accent-dot에 aria-label 없음(점만으로 뜻을 전하지 않는다)")
    n = len({x["slot"] for x in H})
    if n > 2: errs.append(f"{f.name}: 강조색 {n}곳 > 2(목록 반복은 1곳으로 셈) — 강조가 많으면 아무것도 강조되지 않는다")
print("\n".join(errs) if errs else "selfcheck OK")
sys.exit(1 if errs else 0)
