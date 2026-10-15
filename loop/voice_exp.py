#!/usr/bin/env python3
"""보이스톤 프리셋 검증 1단계(기계) + Q5 회사다움 — docs/voice-experiment.md.

python3 loop/voice_exp.py gen      # 다시 쓰기(v18 재료) + 상황만 주고 쓰기(실제 문구 상황) — claude -p 병렬
python3 loop/voice_exp.py judge    # Q1 보이스톤 맞히기 · Q5 회사 맞히기(실제 문구 기준선 포함)
python3 loop/voice_exp.py report   # Q2 규칙 준수 · Q5 말투 지문 · 판정 표 → loop/voice_exp/REPORT.md
"""
import sys, json, re, random, subprocess, pathlib, collections, concurrent.futures as cf

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "loop/voice_exp"
VOICES = ROOT / "plugins/hyper-design/core/foundation/voices"
REAL = ROOT / "docs/research/ux-writing/real"
SLUGS = ["toss", "daangn", "ridi"]
COMPANY = {"toss": "토스", "daangn": "당근", "ridi": "리디"}
GEN_MODEL, JUDGE_MODEL = "claude-sonnet-5-5", "claude-opus-5-5"
LABEL_SLOTS = {"button", "tab", "badge", "label", "section", "row", "dialog_buttons", "marketing"}

COMMON = """공통 문법(보이스톤과 무관하게 항상 지킨다):
- 이름표 자리(화면 제목이 이름일 때·섹션 제목·라벨·배지·탭·큰 숫자의 라벨)는 명사구로 끝낸다. 조건절(~하면/~나면)·조사(은/는/을/를)로 끝내지 않는다.
- 한 문장에는 메시지 하나. 줄표(—)로 두 문장을 잇지 않는다 — 제목과 본문으로 나누거나 '·'로 사실을 잇는다.
- 번역투를 쓰지 않는다: ~로 인한, ~을 통해, ~에 대한, ~이 가능합니다, 유효하지 않은, 처리가 완료되었습니다, 당신.
- 날짜·숫자·이름 같은 데이터는 바꾸지 않는다. 데이터뿐인 문구는 그대로 둔다.
- 한 앱 안에서 문체를 섞지 않는다(프리셋이 정한 예외 자리만)."""


def claude(prompt, model):
    r = subprocess.run(["claude", "-p", "--model", model, "--dangerously-skip-permissions", "--output-format", "json"],
                       input=prompt, capture_output=True, text=True, cwd="/tmp")
    try: return json.loads(r.stdout).get("result", "")
    except Exception: return r.stdout + r.stderr


def parse_json(txt):
    m = re.search(r"```(?:json)?\s*(.*?)```", txt, re.S)
    s = m.group(1) if m else txt
    starts = [i for i in (s.find("["), s.find("{")) if i >= 0]
    return json.JSONDecoder().raw_decode(s[min(starts):])[0]


def preset(slug):
    d = json.loads((VOICES / f"{slug}.json").read_text(encoding="utf-8"))
    for k in ("sources", "observed", "collected", "evidence"): d.pop(k, None)
    return d


def voice_block(v):
    if v == "none": return "보이스톤 프리셋 없음 — 공통 문법만 지켜 자연스러운 한국어 앱 문구로 쓴다(해요체)."
    return "보이스톤 프리셋(이 회사의 말투로 쓴다 — 규칙·자리별 형태·버튼 쌍·예시 쌍의 이유를 따른다):\n" + json.dumps(preset(v), ensure_ascii=False, indent=1)


GEN_PROMPT = """너는 한국어 앱 UX 라이터다. 아래 항목들의 화면 문구를 쓴다.

{common}

{voice}

항목: `original`이 있으면 그 문구를 다시 쓴다(뜻·데이터는 유지, 말투·형태만). `situation`만 있으면 그 상황에 실제 앱 화면에 들어갈 문구를 새로 쓴다.
slot이 dialog면 "제목 / 본문 / 보조 버튼 | 주 버튼" 형식 한 줄로 쓴다.
{items}

JSON 배열만 출력: [{{"id": "...", "text": "..."}}]"""


def gen():
    OUT.mkdir(exist_ok=True)
    M = json.loads((OUT / "materials.json").read_text(encoding="utf-8"))
    jobs = []
    for app, items in M.items():                       # Q1·Q2·Q3: v18 재료 × {공통만, 세 프리셋}
        for v in ["none"] + SLUGS:
            jobs.append((f"rewrite/{app}/{v}", items, v))
    random.seed(5)                                       # Q5: 회사마다 실제 문장 문구 상황(원문 숨김) × 세 프리셋
    sit = {}
    for co in SLUGS:
        R = [r for r in json.loads((REAL / f"{co}-app.json").read_text(encoding="utf-8"))
             if r.get("scope") == "app" and r["slot"] not in LABEL_SLOTS and r.get("verified", "").startswith("ocr")]
        R = [r for r in R if not leaks(r["situation"], r["text"])]
        R = random.sample(R, min(20, len(R)))
        sit[co] = [{"id": r["id"], "slot": r["slot"], "situation": r["situation"]} for r in R]
        for v in SLUGS:
            jobs.append((f"q5/{co}/{v}", sit[co], v))
    (OUT / "q5_situations.json").write_text(json.dumps(sit, ensure_ascii=False, indent=1), encoding="utf-8")

    def run(job):
        key, items, v = job
        p = OUT / f"gen/{key.replace('/', '__')}.json"
        if p.exists(): return key, "cached"
        txt = claude(GEN_PROMPT.format(common=COMMON, voice=voice_block(v), items=json.dumps(items, ensure_ascii=False, indent=1)), GEN_MODEL)
        try: res = parse_json(txt)
        except Exception: return key, "PARSE FAIL: " + txt[:200]
        p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        return key, f"{len(res)}개"
    with cf.ThreadPoolExecutor(6) as ex:
        for k, s in ex.map(run, jobs): print(k, s, flush=True)


def leaks(situation, text):
    n = lambda s: re.sub(r"[^가-힣A-Za-z0-9]", "", s)
    t, s = n(text), n(situation)
    bg = [t[i:i + 3] for i in range(len(t) - 2)]
    return bool(bg) and sum(b in s for b in bg) / len(bg) > 0.4


def load_gen(key):
    p = OUT / f"gen/{key.replace('/', '__')}.json"
    return {x["id"]: x["text"] for x in json.loads(p.read_text(encoding="utf-8"))} if p.exists() else {}


def groups(texts, k=5):
    return [texts[i:i + k] for i in range(0, len(texts) - k + 1, k)] or ([texts] if texts else [])


JUDGE_Q1 = """아래 문구 묶음들은 각각 어떤 앱 하나의 화면 문구다. 묶음마다 어느 보이스톤으로 쓰였는지 고른다.
보이스톤:
{voices}

묶음:
{groups}

JSON만: {{"<묶음 번호>": "<보이스톤 기호 A/B/C>", ...}}"""

JUDGE_Q5 = """아래 문구 묶음들은 각각 한국 앱 하나의 실제 화면 문구다(오류·확인창·토스트·안내 등). 묶음마다 토스·당근·리디 중 어느 회사 앱의 문구인지 고른다. 앱마다 말투가 다르다 — 문체·경어·버튼 짝·마침표·어휘로 판단한다.

묶음:
{groups}

JSON만: {{"<묶음 번호>": "토스|당근|리디", ...}}"""


JUDGE_Q5B = """각 문항에는 한국 앱의 실제 화면 문구(정답 원문) 하나와, 같은 상황을 다른 사람들이 쓴 후보 A·B·C가 있다. 후보들의 내용은 거의 같다 — **말투**(문체·경어·문장 끝·버튼 짝·마침표·느낌표·길이·어휘 선택)가 원문과 가장 닮은 후보 하나를 고른다.

{groups}

JSON만: {{"<문항 번호>": "A|B|C", ...}}"""


def judge_same():
    """Q5(수정): 같은 상황 — 실제 원문과 말투가 가장 닮은 프리셋 결과 고르기. 내용 단서가 같아 말투만 남는다."""
    random.seed(23)
    sit = json.loads((OUT / "q5_situations.json").read_text(encoding="utf-8"))
    items = []
    for co in SLUGS:
        real = {r["id"]: r["text"] for r in json.loads((REAL / f"{co}-app.json").read_text(encoding="utf-8"))}
        G = {v: load_gen(f"q5/{co}/{v}") for v in SLUGS}
        for x in sit[co]:
            if not all(x["id"] in G[v] for v in SLUGS): continue
            order = SLUGS[:]; random.shuffle(order)
            items.append({"co": co, "id": x["id"], "real": real[x["id"]], "order": order, "cands": [G[v][x["id"]] for v in order]})
    random.shuffle(items)
    def ask(batch):
        body = "\n\n".join(f"[{i+1}] 원문: {it['real']}\n" + "\n".join(f"  {L}. {c}" for L, c in zip("ABC", it["cands"])) for i, it in enumerate(batch))
        txt = claude(JUDGE_Q5B.format(groups=body), JUDGE_MODEL)
        try: ans = parse_json(txt)
        except Exception: ans = {}
        return [ans.get(str(i + 1), "?") for i in range(len(batch))]
    chunks = [items[i:i + 9] for i in range(0, len(items), 9)]
    with cf.ThreadPoolExecutor(6) as ex: preds = sum(ex.map(ask, chunks), [])
    for it, p in zip(items, preds): it["pick"] = it["order"]["ABC".index(p)] if p in "ABC" and p else "?"
    (OUT / "judge_same.json").write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
    print("judge_same done", len(items))


def judge():
    random.seed(11)
    M = json.loads((OUT / "materials.json").read_text(encoding="utf-8"))
    pitch = {s: json.loads((VOICES / f"{s}.json").read_text(encoding="utf-8")) for s in SLUGS}
    sym = dict(zip(SLUGS, "ABC"))
    vdesc = "\n".join(f"{sym[s]}. {pitch[s]['label']} — {pitch[s]['pitch']}" for s in SLUGS)
    q1 = []                                              # (정답, 문구들)
    for app in M:
        for v in SLUGS:
            g = load_gen(f"rewrite/{app}/{v}")
            ids = [x["id"] for x in M[app]]
            texts = [g[i] for i in ids if i in g]
            random.shuffle(texts)
            q1 += [(sym[v], t) for t in groups(texts)]
    sit = json.loads((OUT / "q5_situations.json").read_text(encoding="utf-8"))
    q5 = []                                              # (정답, 종류, 문구들)
    for co in SLUGS:
        real = {r["id"]: r["text"] for r in json.loads((REAL / f"{co}-app.json").read_text(encoding="utf-8"))}
        texts = [real[x["id"]] for x in sit[co]]; random.shuffle(texts)
        q5 += [(COMPANY[co], "real", t) for t in groups(texts)]
        for v in SLUGS:
            g = load_gen(f"q5/{co}/{v}"); texts = list(g.values()); random.shuffle(texts)
            q5 += [(COMPANY[v], f"gen:{v}<-{co}", t) for t in groups(texts)]
    random.shuffle(q1); random.shuffle(q5)

    def ask(batch, tmpl, **kw):
        body = "\n\n".join(f"[{i+1}]\n" + "\n".join(f"- {t}" for t in b[-1]) for i, b in enumerate(batch))
        txt = claude(tmpl.format(groups=body, **kw), JUDGE_MODEL)
        try: ans = parse_json(txt)
        except Exception: ans = {}
        return [ans.get(str(i + 1), "?") for i in range(len(batch))]
    chunks = lambda L, n=9: [L[i:i + n] for i in range(0, len(L), n)]
    with cf.ThreadPoolExecutor(6) as ex:
        a1 = sum(ex.map(lambda b: ask(b, JUDGE_Q1, voices=vdesc), chunks(q1)), [])
        a5 = sum(ex.map(lambda b: ask(b, JUDGE_Q5), chunks(q5)), [])
    res = {"q1": [{"truth": t, "pred": p, "texts": x} for (t, x), p in zip(q1, a1)],
           "q5": [{"truth": t, "kind": k, "pred": p, "texts": x} for (t, k, x), p in zip(q5, a5)],
           "sym": sym}
    (OUT / "judge.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print("judge done", len(q1), len(q5))


# ---------- Q2 규칙 준수 · Q5 지문 ----------
def ending(t):
    t = t.strip().rstrip(".!?…~ ")
    if re.search(r"(주세요|보세요|세요)$", t): return "req"
    if re.search(r"(니다|니까|십시오)$", t): return "hamnida"
    if re.search(r"요$", t): return "haeyo"
    return "other"


def sentences(text):
    return [s for s in re.split(r"\s*/\s*|\n", text.split("|")[0]) if re.search(r"[가-힣]", s) and len(s) > 4]


def fingerprint(texts):
    S = [s for t in texts for s in sentences(t)]
    n = len(S) or 1
    c = collections.Counter(ending(s) for s in S)
    return {"해요": c["haeyo"] / n, "요청": c["req"] / n, "합니다": c["hamnida"] / n,
            "경어": sum(bool(re.search(r"(시겠|하신|으신|드릴|드려|께서)", s)) for s in S) / n,
            "느낌표": sum("!" in s for s in S) / n, "마침표": sum(s.strip().endswith(".") for s in S) / n,
            "길이": sum(len(s) for s in S) / n / 40}


def dist(a, b): return sum((a[k] - b[k]) ** 2 for k in a) ** .5


def q2_check(v, slot, text):
    """프리셋 규칙 + 공통 문법 위반 목록"""
    bad = []
    S = sentences(text)
    if v == "ridi" and any(ending(s) == "haeyo" for s in S): bad.append("리디인데 해요체")
    legal = re.search(r"철회|수수료|약관|법|인증서|고지", text)            # 토스 예외: 법률·금융 효력이 있는 안내
    sanction = re.search(r"제재|제한|정지|위반", text)                     # 당근 예외: 제재·경고
    if v in ("toss", "daangn") and any(ending(s) == "hamnida" for s in S) and not re.search(r"죄송합니다|고맙습니다|감사합니다", text) \
            and not (v == "toss" and legal) and not (v == "daangn" and sanction): bad.append("해요체 프리셋인데 합니다체")
    if v == "toss" and re.search(r"(시겠|하신|으신|계시|여쭈|님께|께서)", text): bad.append("토스인데 경어")
    if slot == "dialog" and "|" in text:
        sec = text.split("|")[0].split("/")[-1].strip()
        want = {"toss": "닫기", "daangn": "취소", "ridi": "취소"}.get(v)
        if want and want not in sec and not (v == "toss" and "다음에" in sec): bad.append(f"확인창 보조 버튼 '{sec}' ≠ {want}")
    if re.search(r"\S\s+—\s+\S", text): bad.append("줄표로 문장 잇기")
    if slot in ("section", "big_title") and re.search(r"(하면|나면|으면|[은는을를])$", text.strip()): bad.append("이름표가 조건절·조사로 끝남")
    if re.search(r"당신|로 인한|을 통해|를 통해|유효하지 않은|처리가 완료", text): bad.append("번역투 어휘")
    return bad


def report():
    M = json.loads((OUT / "materials.json").read_text(encoding="utf-8"))
    L = ["# 보이스톤 프리셋 검증 결과\n", "계획: `docs/voice-experiment.md`. 생성 sonnet, 판정 opus, `claude -p`.\n"]
    # Q2
    L.append("## Q2 충실 — 프리셋 규칙·공통 문법 준수\n\n| 보이스톤 | 문구 | 위반 | 준수율 |\n|---|---|---|---|")
    viol = []
    for v in ["none"] + SLUGS:
        n = bad = 0
        for app, items in M.items():
            g = load_gen(f"rewrite/{app}/{v}")
            for x in items:
                if x["id"] not in g: continue
                n += 1; b = q2_check(v if v != "none" else "", x["slot"], g[x["id"]])
                if b: bad += 1; viol.append((v, x["id"], g[x["id"]], b))
        for co in SLUGS:
            if v == "none": continue
            g = load_gen(f"q5/{co}/{v}")
            sit = {s["id"]: s for s in json.loads((OUT / "q5_situations.json").read_text(encoding="utf-8"))[co]}
            for i, t in g.items():
                n += 1; b = q2_check(v, "dialog" if "dialog" in sit.get(i, {}).get("slot", "") else sit.get(i, {}).get("slot", ""), t)
                if b: bad += 1; viol.append((v, i, t, b))
        L.append(f"| {v} | {n} | {bad} | {(1 - bad / n) * 100 if n else 0:.0f}% |")
    L.append("\n위반 예:\n" + "\n".join(f"- `{v}` {i}: {t!r} — {', '.join(b)}" for v, i, t, b in viol[:15]))
    # 원본 vs 다시 쓴 것 (사람이 볼 표)
    L.append("\n## 다시 쓰기 비교 (v18 원본 → 공통만 / 토스 / 당근 / 리디)\n")
    for app, items in M.items():
        G = {v: load_gen(f"rewrite/{app}/{v}") for v in ["none"] + SLUGS}
        L.append(f"\n### {app}\n\n| id | 원본·상황 | 공통만 | 짧고 담백하게 | 다정하게 | 정중하게 |\n|---|---|---|---|---|---|")
        for x in items:
            src = x.get("original") or f"({x['situation']})"
            L.append(f"| {x['id']} | {src} | " + " | ".join(G[v].get(x['id'], '').replace('|', '\\|').replace('\n', ' ') for v in ["none"] + SLUGS) + " |")
    # Q1·Q5 판정
    J = json.loads((OUT / "judge.json").read_text(encoding="utf-8"))
    inv = {v: k for k, v in J["sym"].items()}
    acc = lambda R: (sum(r["truth"] == r["pred"] for r in R) / len(R) * 100) if R else 0
    L.append("\n## Q1 구별 — 보이스톤 이름·한 줄 설명만 보고 맞히기(문구 5개 묶음)\n")
    L.append(f"정답률 **{acc(J['q1']):.0f}%** (우연 33%, {len(J['q1'])}묶음)\n\n| 정답 \\ 예측 | " + " | ".join(COMPANY[s] for s in SLUGS) + " |\n|---|---|---|---|")
    for s in SLUGS:
        row = [sum(1 for r in J["q1"] if inv.get(r["truth"]) == s and inv.get(r["pred"]) == p) for p in SLUGS]
        L.append(f"| {COMPANY[s]} | " + " | ".join(map(str, row)) + " |")
    L.append("\n## Q5 회사다움\n\n### 회사 맞히기 (opus, 문구 5개 묶음)\n\n| 묶음 | 정답률 | n |\n|---|---|---|")
    real = [r for r in J["q5"] if r["kind"] == "real"]
    L.append(f"| **실제 문구(기준선)** | {acc(real):.0f}% | {len(real)} |")
    for v in SLUGS:
        R = [r for r in J["q5"] if r["kind"].startswith(f"gen:{v}<-")]
        L.append(f"| {COMPANY[v]} 프리셋 결과 | {acc(R):.0f}% | {len(R)} |")
    for co in SLUGS:
        R = [r for r in real if r["truth"] == COMPANY[co]]
        L.append(f"| (기준선 중 {COMPANY[co]}) | {acc(R):.0f}% | {len(R)} |")
    L.append("\n이 표는 **내용으로 맞힌 것**이다 — 판정이 상황 출처(어느 서비스 이야기인가)를 따라갔다(예: 토스 상황을 어떤 프리셋으로 써도 '토스'). 회사다움의 측정으로 쓰지 않는다. 아래 '같은 상황 비교'가 본 측정.\n")
    S = json.loads((OUT / "judge_same.json").read_text(encoding="utf-8")) if (OUT / "judge_same.json").exists() else []
    if S:
        L.append("### 같은 상황 비교 — 실제 원문과 말투가 가장 닮은 프리셋 결과 고르기 (우연 33%)\n\n| 실제 출처 | 자기 프리셋을 고름 | 토스 프리셋 | 당근 프리셋 | 리디 프리셋 | n |\n|---|---|---|---|---|---|")
        for co in SLUGS:
            R = [x for x in S if x["co"] == co]; c = collections.Counter(x["pick"] for x in R)
            L.append(f"| {COMPANY[co]} | **{c[co]/len(R)*100:.0f}%** | {c['toss']} | {c['daangn']} | {c['ridi']} | {len(R)} |")
        L.append(f"| 전체 | **{sum(x['pick']==x['co'] for x in S)/len(S)*100:.0f}%** | | | | {len(S)} |")
    # 지문
    sit = json.loads((OUT / "q5_situations.json").read_text(encoding="utf-8"))
    FP = {}
    for co in SLUGS:
        realtx = [r["text"] for r in json.loads((REAL / f"{co}-app.json").read_text(encoding="utf-8"))
                  if r.get("scope") == "app" and r["slot"] not in LABEL_SLOTS and r.get("verified", "").startswith("ocr")]
        FP[co] = fingerprint(realtx)
    L.append("\n### 말투 지문 (문장 비율 — 실제 본앱 vs 프리셋 결과)\n\n| | 해요 | 요청 | 합니다 | 경어 | 느낌표 | 마침표 | 가장 가까운 실제 |\n|---|---|---|---|---|---|---|---|")
    fmt = lambda f: " | ".join(f"{f[k]*100:.0f}%" for k in ["해요", "요청", "합니다", "경어", "느낌표", "마침표"])
    for co in SLUGS: L.append(f"| 실제 {COMPANY[co]} | {fmt(FP[co])} | — |")
    for v in SLUGS:
        tx = sum((list(load_gen(f"q5/{co}/{v}").values()) for co in SLUGS), [])
        f = fingerprint(tx); near = min(SLUGS, key=lambda c: dist(f, FP[c]))
        L.append(f"| {COMPANY[v]} 프리셋 | {fmt(f)} | **{COMPANY[near]}** {'✓' if near == v else '✗'} |")
    (OUT / "REPORT.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[:40]))


if __name__ == "__main__":
    {"gen": gen, "judge": judge, "judge_same": judge_same, "report": report}[sys.argv[1]]()
