#!/usr/bin/env python3
"""보이스톤 프리셋 고정 평가 — docs/voicetone-criteria.md. 자동 개선 루프는 이 파일을 고치지 않는다.

python3 loop/voicetone_eval.py prepare            # 1회: dev/test 분할 + 영어 뜻 메모 + 천장용 말투 보존 바꿔쓰기 (캐시, 고정)
python3 loop/voicetone_eval.py run --split dev    # 프리셋으로 생성 → 같은 상황 비교 판정 2회 → 점수 JSON
python3 loop/voicetone_eval.py calibrate          # 바닥(공통만)·천장(말투 보존 바꿔쓰기)·흔들림(3회) 실측
"""
import sys, json, re, random, subprocess, pathlib, hashlib, argparse, statistics, concurrent.futures as cf

ROOT = pathlib.Path(__file__).resolve().parent.parent
D = ROOT / "loop/voicetone"
VOICES = pathlib.Path(sys.argv[sys.argv.index("--voices") + 1]) if "--voices" in sys.argv else ROOT / "plugins/hyper-design/core/foundation/voices"
REAL = ROOT / "docs/research/ux-writing/real"
SLUGS = ["toss", "daangn", "ridi"]
LABEL_SLOTS = {"button", "tab", "badge", "label", "section", "row", "dialog_buttons", "marketing"}
GEN_MODEL, JUDGE_MODEL, AUX_MODEL = "claude-sonnet-5-5", "claude-opus-5-5", "claude-sonnet-5-5"
SIZE_CAP = 9000  # 프리셋 JSON 바이트 상한 — 정답을 외워 넣는 과적합 방지


class Limit(Exception): pass


LEAN = ["--system-prompt", "You are a careful Korean UX writing assistant. Follow the user's instructions exactly.",
        "--tools", "", "--strict-mcp-config", "--setting-sources", "", "--no-session-persistence"]   # 호출당 고정 비용 2만→600 토큰


def claude(prompt, model, cwd="/tmp", tools=False):
    extra = ["--strict-mcp-config", "--setting-sources", "", "--no-session-persistence", "--dangerously-skip-permissions"] if tools else LEAN
    r = subprocess.run(["claude", "-p", "--model", model, *extra, "--output-format", "json"],
                       input=prompt, capture_output=True, text=True, cwd=cwd)
    try: d = json.loads(r.stdout)
    except Exception: return r.stdout + r.stderr
    if d.get("is_error") and (d.get("api_error_status") == 429 or "limit" in str(d.get("result", "")).lower()):
        raise Limit(d.get("result"))                        # 사용 한도 — 조용히 0점으로 넘어가지 않고 멈춘다
    return d.get("result", "")


def parse_json(txt):
    m = re.search(r"```(?:json)?\s*(.*?)```", txt, re.S)
    s = m.group(1) if m else txt
    starts = [i for i in (s.find("["), s.find("{")) if i >= 0]
    return json.JSONDecoder().raw_decode(s[min(starts):])[0]


def kv(xs, val="text"):
    """[{"id":..., "text":...}] → dict. 모델이 키를 조금 틀려도(" text") 읽는다."""
    out = {}
    for x in xs if isinstance(xs, list) else []:
        if not isinstance(x, dict): continue
        k = {re.sub(r"\s", "", kk): v for kk, v in x.items()}
        v = k.get(val) or next((vv for kk, vv in k.items() if kk != "id" and isinstance(vv, str)), None)
        if k.get("id") and v: out[k["id"]] = v
    return out


def pmap(f, xs, n=8):
    with cf.ThreadPoolExecutor(n) as ex: return list(ex.map(f, xs))


# ---------- 고정 데이터 ----------
def prepare():
    D.mkdir(parents=True, exist_ok=True)
    rng = random.Random(2026)
    split = {}
    for co in SLUGS:
        R = [r for r in json.loads((REAL / f"{co}-app.json").read_text(encoding="utf-8"))
             if r.get("scope") == "app" and r["slot"] not in LABEL_SLOTS and r.get("verified", "").startswith("ocr")]
        R.sort(key=lambda r: r["id"]); rng.shuffle(R)
        k = round(len(R) * 0.6) if len(R) >= 50 else len(R)          # 표본이 작은 회사(리디)는 전부 dev, 잠정
        split[co] = {"dev": [r["id"] for r in R[:k]], "test": [r["id"] for r in R[k:]], "provisional": len(R) < 50}
    (D / "split.json").write_text(json.dumps(split, ensure_ascii=False, indent=1), encoding="utf-8")
    items = {r["id"]: r for co in SLUGS for r in json.loads((REAL / f"{co}-app.json").read_text(encoding="utf-8"))}
    ids = [i for co in SLUGS for s in ("dev", "test") for i in split[co][s]]
    memo_p, orc_p = D / "memos.json", D / "oracle.json"
    memos = json.loads(memo_p.read_text()) if memo_p.exists() else {}
    oracle = json.loads(orc_p.read_text()) if orc_p.exists() else {}
    todo = [ids[i:i + 15] for i in range(0, len(ids), 15)]

    def memo(batch):
        q = [{"id": i, "slot": items[i]["slot"], "situation": items[i]["situation"], "text": items[i]["text"]} for i in batch if i not in memos]
        if not q: return {}
        txt = claude("""For each Korean app UI string, write a plain English meaning memo: what the screen tells or asks the user, keeping every fact, number, name and option, but NO tone, politeness level, sentence ending style, punctuation style or exclamation. Neutral, like a spec. Do not quote Korean.
""" + json.dumps(q, ensure_ascii=False, indent=1) + '\nJSON array only: [{"id": "...", "memo": "..."}]', AUX_MODEL)
        try: return kv(parse_json(txt), "memo")
        except Exception: return {}

    def orc(batch):
        q = [{"id": i, "text": items[i]["text"]} for i in batch if i not in oracle]
        if not q: return {}
        txt = claude("""아래 한국어 앱 문구를 **말투는 그대로** 두고 표현만 바꿔 쓴다 — 문체(해요/합니다), 경어, 문장 끝 모양, 마침표·느낌표, 길이, 버튼 짝 형식을 원문과 같게. 단어·어순만 다르게, 뜻과 데이터는 유지.
""" + json.dumps(q, ensure_ascii=False, indent=1) + '\nJSON 배열만: [{"id": "...", "text": "..."}]', AUX_MODEL)
        try: return kv(parse_json(txt))
        except Exception: return {}
    for m in pmap(memo, todo): memos.update(m)
    for m in pmap(orc, todo): oracle.update(m)
    memo_p.write_text(json.dumps(memos, ensure_ascii=False, indent=1), encoding="utf-8")
    orc_p.write_text(json.dumps(oracle, ensure_ascii=False, indent=1), encoding="utf-8")
    print({co: {k: len(v) if isinstance(v, list) else v for k, v in s.items()} for co, s in split.items()}, "memos", len(memos), "oracle", len(oracle))


def load_fixed():
    split = json.loads((D / "split.json").read_text(encoding="utf-8"))
    memos = json.loads((D / "memos.json").read_text(encoding="utf-8"))
    oracle = json.loads((D / "oracle.json").read_text(encoding="utf-8"))
    items = {r["id"]: r for co in SLUGS for r in json.loads((REAL / f"{co}-app.json").read_text(encoding="utf-8"))}
    return split, memos, oracle, items


# ---------- 생성 ----------
COMMON = """공통 문법(보이스톤과 무관하게 항상 지킨다):
- 이름표 자리(섹션 제목·라벨·배지·탭)는 명사구. 조건절(~하면)·조사(은/는/을/를)로 끝내지 않는다.
- 한 문장에 메시지 하나. 줄표(—)로 두 문장을 잇지 않는다.
- 번역투 금지: ~로 인한, ~을 통해, ~에 대한, ~이 가능합니다, 유효하지 않은, 처리가 완료되었습니다, 당신.
- 날짜·숫자·이름·선택지 같은 데이터는 그대로 옮긴다.
- 한 앱 안에서 문체를 섞지 않는다(보이스톤이 정한 예외 자리만)."""


def preset_text(slug):
    if slug == "none": return "보이스톤 프리셋 없음 — 공통 문법만 지켜 자연스러운 한국어 앱 문구(해요체)로 쓴다."
    d = json.loads((VOICES / f"{slug}.json").read_text(encoding="utf-8"))
    for k in ("sources", "observed", "collected", "evidence", "verified", "version"): d.pop(k, None)
    return "보이스톤 프리셋(이 회사의 말투로 — 규칙·자리별 형태·버튼 짝·예시 쌍의 이유를 따른다):\n" + json.dumps(d, ensure_ascii=False, indent=1)


def generate(slug, rows, memos):
    out = {}
    def one(batch):
        q = [{"id": r["id"], "slot": r["slot"], "meaning": memos.get(r["id"], r["situation"])} for r in batch]
        txt = claude(f"""너는 한국어 앱 UX 라이터다. 각 항목의 영어 뜻 메모를 그 자리(slot)에 들어갈 한국어 화면 문구로 쓴다. 영어를 옮기지 말고, 한국 앱이 실제로 쓰는 말로.

{COMMON}

{preset_text(slug)}

항목:
{json.dumps(q, ensure_ascii=False, indent=1)}

JSON 배열만: [{{"id": "...", "text": "..."}}]""", GEN_MODEL)
        try: return kv(parse_json(txt))
        except Exception: return {}
    batches = [rows[i:i + 20] for i in range(0, len(rows), 20)]
    for m in pmap(one, batches): out.update(m)
    miss = [r for r in rows if r["id"] not in out]                # 실패한 묶음은 한 번 더
    if miss:
        for m in pmap(one, [miss[i:i + 20] for i in range(0, len(miss), 20)]): out.update(m)
    return out


# ---------- 판정 ----------
JUDGE = """각 문항에는 한국 앱의 실제 화면 문구(원문) 하나와, 같은 뜻을 다른 사람들이 쓴 후보들이 있다. 후보들의 내용은 거의 같다 — **말투**(문체·경어·문장 끝·마침표·느낌표·길이·어휘 선택·버튼 짝 형식)가 원문과 가장 닮은 후보 하나를 고른다.

{body}

JSON만: {{"<문항 번호>": "A|B|C", ...}}"""


def judge(questions, seed):
    """questions: [{real, cands: {name: text}}] → [고른 name]"""
    rng = random.Random(seed); Q = []
    for q in questions:
        names = list(q["cands"]); rng.shuffle(names); Q.append((q, names))
    def ask(chunk):
        body = "\n\n".join(f"[{i+1}] 원문: {q['real']}\n" + "\n".join(f"  {L}. {q['cands'][n]}" for L, n in zip("ABC", names)) for i, (q, names) in enumerate(chunk))
        try: a = parse_json(claude(JUDGE.format(body=body), JUDGE_MODEL))
        except Exception: a = {}
        return [names["ABC".index(a.get(str(i + 1)))] if a.get(str(i + 1)) in ("A", "B", "C") else None for i, (q, names) in enumerate(chunk)]
    return sum(pmap(ask, [Q[i:i + 10] for i in range(0, len(Q), 10)]), [])


# ---------- 규칙 (U1·U2) ----------
def ending(t):
    t = t.strip().rstrip(".!?…~ ")
    if re.search(r"(주세요|보세요|세요)$", t): return "req"
    if re.search(r"(니다|니까|십시오)$", t): return "hamnida"
    if re.search(r"요$", t): return "haeyo"
    return "other"


def rule_bad(slug, text):
    S = [s for s in re.split(r"(?<=[.?!])\s+|\s*/\s*|\n", text) if re.search(r"[가-힣]", s) and len(s) > 4]
    legal = re.search(r"철회|수수료|약관|법|인증서|고지", text); sanction = re.search(r"제재|제한|정지|위반", text)
    bad = []
    if slug == "ridi" and any(ending(s) == "haeyo" for s in S): bad.append("리디인데 해요체")
    if slug in ("toss", "daangn") and any(ending(s) == "hamnida" for s in S) and not re.search(r"죄송합니다|고맙습니다|감사합니다", text) \
            and not (slug == "toss" and legal) and not (slug == "daangn" and sanction): bad.append("해요체 프리셋인데 합니다체")
    if re.search(r"\S\s+—\s+\S", text): bad.append("줄표로 문장 잇기")
    if re.search(r"당신|로 인한|을 통해|를 통해|유효하지 않은|처리가 완료", text): bad.append("번역투")
    return bad


def digits(s):
    """숫자 값 집합 — 표기 차이(1천=1,000, 쉼표)는 같게 본다. 시각을 다른 체계로 바꾸면(11시→23:) 다르게 잡힌다."""
    s = re.sub(r"(\d+)\s*천", lambda m: str(int(m.group(1)) * 1000), s)
    s = re.sub(r"(\d+)\s*만", lambda m: str(int(m.group(1)) * 10000), s)
    return set(x.replace(",", "").lstrip("0") or "0" for x in re.findall(r"\d[\d,]*", s))


def leak_check(slug, split, items):
    """프리셋에 정답지(dev·test) 문구가 6글자 이상 그대로 들어갔는가"""
    raw = (VOICES / f"{slug}.json").read_text(encoding="utf-8")
    n = lambda s: re.sub(r"\s", "", s); P = n(raw); hits = []
    for co in SLUGS:
        for i in split[co]["dev"] + split[co]["test"]:
            t = n(items[i]["text"])
            for k in range(0, max(1, len(t) - 7)):
                if len(t) >= 8 and t[k:k + 8] in P: hits.append(i); break
    return hits, len(raw.encode())


# ---------- 평가 1회 ----------
def run(split_name="dev", seed=0, cands=("toss", "daangn", "ridi"), tag=None, only=None):
    split, memos, oracle, items = load_fixed()
    rows = {co: [items[i] for i in split[co][split_name]] if not only or co in only else [] for co in SLUGS}
    allrows = sum(rows.values(), [])
    gens = {}
    def g(slug): return slug, generate(slug, allrows, memos) if slug != "oracle" else {}
    for slug, out in pmap(g, [c for c in set(cands) if c != "oracle"], 4): gens[slug] = out
    res = {"split": split_name, "seed": seed, "cands": list(cands), "per": {}}
    Qall = []
    for co in SLUGS:
        for r in rows[co]:
            c = {}
            for name in cands:
                src = oracle if name == "oracle" else gens[name]
                if r["id"] in src: c[name if name != "oracle" else "oracle"] = src[r["id"]]
            if len(c) == len(cands): Qall.append({"co": co, "id": r["id"], "real": r["text"], "cands": c})
    p1, p2 = judge(Qall, 100 + seed), judge(Qall, 200 + seed)
    agree = sum(a == b for a, b in zip(p1, p2) if a and b) / max(1, sum(1 for a, b in zip(p1, p2) if a and b))
    target = lambda co: "oracle" if "oracle" in cands else ("none" if "none" in cands and co not in cands else co)
    for co in SLUGS:
        Q = [(q, a, b) for q, a, b in zip(Qall, p1, p2) if q["co"] == co]
        own = [((a == target(co)) + (b == target(co))) / 2 for q, a, b in Q]
        res["per"][co] = {"n": len(Q), "V1": sum(own) / len(own) if own else None}
    # U1·U2 (자기 프리셋 결과)
    tot = bad = keep = dig = 0; viol = []
    for slug in [c for c in cands if c in SLUGS]:
        for r in allrows:
            t = gens[slug].get(r["id"])
            if t is None: continue
            tot += 1; b = rule_bad(slug, t)
            if b: bad += 1; viol.append((slug, r["id"], t, b))
            d = digits(r["text"])
            if d and not re.search(r"\[[^\]]*\]|\{[^}]*\}|가림", r["text"]): dig += 1; keep += d <= digits(t)
    res.update({"agree": agree, "U1": 1 - bad / max(1, tot), "U2": keep / max(1, dig), "violations": viol[:20]})
    cores = [res["per"][co]["V1"] for co in ("toss", "daangn") if res["per"][co]["V1"] is not None]
    res["V1_core"] = sum(cores) / len(cores) if cores else None
    res["score"] = res["V1_core"] or 0                      # 점수는 회사다움만. U1·U2는 루프에서 관문(미달이면 거절)
    res["gate_ok"] = res["U1"] >= 0.98 and res["U2"] >= 0.95
    res["fails"] = [{"co": q["co"], "real": q["real"], "own": q["cands"].get(q["co"]), "picked": q["cands"].get(a) if a else None, "picked_name": a}
                    for q, a in zip(Qall, p1) if q["co"] in cands and a != q["co"]][:40]
    out = D / "runs" / f"{tag or split_name}-{seed}.json"
    out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: res[k] for k in ("split", "cands", "V1_core", "U1", "U2", "agree", "score")} | {co: res["per"][co] for co in SLUGS}, ensure_ascii=False))
    return res


def calibrate():
    """기준을 실측으로 정한다: 바닥 = '공통만' 결과를 자기 자리에 넣었을 때, 천장 = 말투 보존 바꿔쓰기를 넣었을 때, 흔들림 = 현재 프리셋 3회."""
    out = {}
    cur = [run("dev", s, ("toss", "daangn", "ridi"), tag=f"cal-current") for s in range(3)]
    out["current"] = {"V1_core": [r["V1_core"] for r in cur], "per": [{co: r["per"][co]["V1"] for co in SLUGS} for r in cur],
                      "U1": [r["U1"] for r in cur], "U2": [r["U2"] for r in cur], "agree": [r["agree"] for r in cur]}
    # 천장: 자기 회사 자리에 '말투 보존 바꿔쓰기'(원문 말투 그대로) — 다른 두 후보는 다른 회사 프리셋
    ceil = {}
    for co in ("toss", "daangn"):
        others = [s for s in SLUGS if s != co]
        r = run("dev", 7, ("oracle", *others), tag=f"cal-ceiling-{co}", only=[co])
        ceil[co] = r["per"][co]["V1"]
    out["ceiling"] = ceil
    # 바닥: 자기 회사 자리에 '공통만'(보이스톤 없음)
    floor = {}
    for co in ("toss", "daangn"):
        others = [s for s in SLUGS if s != co]
        r = run("dev", 8, ("none", *others), tag=f"cal-floor-{co}", only=[co])
        floor[co] = r["per"][co]["V1"]
    out["floor"] = floor
    v = out["current"]["V1_core"]
    out["sigma"] = statistics.pstdev(v) if len(v) > 1 else None
    (D / "calibration.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd"); ap.add_argument("--split", default="dev"); ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--tag"); ap.add_argument("--voices")
    a = ap.parse_args()
    if a.cmd == "prepare": prepare()
    elif a.cmd == "run": run(a.split, a.seed, tag=a.tag)
    elif a.cmd == "calibrate": calibrate()
    elif a.cmd == "leak":
        split, memos, oracle, items = load_fixed()
        for s in SLUGS: print(s, *leak_check(s, split, items))
