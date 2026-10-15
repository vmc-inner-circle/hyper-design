#!/usr/bin/env python3
"""보이스톤 '진짜 찾기' 평가 — 실제 한국 앱 문구와 구별되는가. 자동 개선 루프는 이 파일을 고치지 않는다.

같은 뜻(영어 메모)에서 프리셋으로 쓴 문구와 실제 앱 문구를 나란히 놓고 "어느 쪽이 실제 앱인가"를 묻는다.
detect = 판정이 실제를 맞힌 비율. 0.5에 가까울수록 구별이 안 된다(좋다).

python3 loop/realness_eval.py prepare        # 9개 앱 정답지 분할 + 뜻 메모 + 말투 보존 바꿔쓰기(천장 확인용) — 캐시
python3 loop/realness_eval.py run --split dev
python3 loop/realness_eval.py calibrate      # 바닥(공통 문법만)·천장(말투 보존 바꿔쓰기)·흔들림(3회)
"""
import sys, json, re, random, pathlib, argparse, statistics
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from voicetone_eval import claude, parse_json, kv, pmap, COMMON, ending, digits, Limit  # noqa: F401  (호출·파싱·규칙 공용)

ROOT = pathlib.Path(__file__).resolve().parent.parent
D = ROOT / "loop/realness"
VOICES = ROOT / "plugins/hyper-design/core/foundation/voices"
REAL = ROOT / "docs/research/ux-writing/real"
CLUSTER = {"haeyo": ["toss", "daangn", "baemin", "ohouse", "catchtable"], "hamnida": ["ridi", "musinsa", "kbstar", "gov24"]}
APP2P = {a: p for p, apps in CLUSTER.items() for a in apps}
LABEL_SLOTS = {"button", "tab", "badge", "label", "section", "row", "dialog_buttons", "marketing"}
GEN_MODEL, JUDGE_MODEL, AUX_MODEL = "claude-sonnet-5-5", "claude-opus-5-5", "claude-sonnet-5-5"


def corpus():
    out = {}
    for a in APP2P:
        for r in json.loads((REAL / f"{a}-app.json").read_text(encoding="utf-8")):
            if r.get("scope") == "app" and r["slot"] not in LABEL_SLOTS and r.get("verified", "").startswith("ocr") \
                    and not re.search(r"\[[^\]]*\]|\{[^}]*\}|가림", r["text"]):
                r["app"] = a; out[r["id"]] = r
    return out


def prepare():
    D.mkdir(parents=True, exist_ok=True)
    items = corpus(); rng = random.Random(2026); split = {}
    for a in APP2P:
        ids = sorted(i for i, r in items.items() if r["app"] == a); rng.shuffle(ids)
        k = round(len(ids) * 0.6); split[a] = {"dev": ids[:k], "test": ids[k:]}
    (D / "split.json").write_text(json.dumps(split, ensure_ascii=False, indent=1))
    old = ROOT / "loop/voicetone"                         # 1차 루프에서 만든 메모·바꿔쓰기 재사용
    memos = json.loads((old / "memos.json").read_text()) if (old / "memos.json").exists() else {}
    oracle = json.loads((old / "oracle.json").read_text()) if (old / "oracle.json").exists() else {}
    if (D / "memos.json").exists(): memos.update(json.loads((D / "memos.json").read_text()))
    if (D / "oracle.json").exists(): oracle.update(json.loads((D / "oracle.json").read_text()))
    ids = list(items)
    def memo(batch):
        q = [{"id": i, "slot": items[i]["slot"], "situation": items[i]["situation"], "text": items[i]["text"]} for i in batch if i not in memos]
        if not q: return {}
        return kv(parse_json(claude("""For each Korean app UI string, write a plain English meaning memo: what the screen tells or asks the user, keeping every fact, number, name and option, but NO tone, politeness level, sentence ending style, punctuation style or exclamation. Neutral, like a spec. Do not quote Korean.
""" + json.dumps(q, ensure_ascii=False, indent=1) + '\nJSON array only: [{"id": "...", "memo": "..."}]', AUX_MODEL)), "memo")
    def orc(batch):
        q = [{"id": i, "text": items[i]["text"]} for i in batch if i not in oracle]
        if not q: return {}
        return kv(parse_json(claude("""아래 한국어 앱 문구를 **말투는 그대로** 두고 표현만 바꿔 쓴다 — 문체(해요/합니다), 경어, 문장 끝 모양, 마침표·느낌표, 길이를 원문과 같게. 단어·어순만 다르게, 뜻과 데이터는 유지.
""" + json.dumps(q, ensure_ascii=False, indent=1) + '\nJSON 배열만: [{"id": "...", "text": "..."}]', AUX_MODEL)))
    for _ in range(2):                                  # 실패한 묶음은 한 번 더
        todo = [ids[i:i + 15] for i in range(0, len(ids), 15)]
        for m in pmap(memo, todo): memos.update(m)
        for m in pmap(orc, todo): oracle.update(m)
    (D / "memos.json").write_text(json.dumps({i: memos[i] for i in ids if i in memos}, ensure_ascii=False, indent=1))
    (D / "oracle.json").write_text(json.dumps({i: oracle[i] for i in ids if i in oracle}, ensure_ascii=False, indent=1))
    print({a: (len(s["dev"]), len(s["test"])) for a, s in split.items()}, "memos", sum(i in memos for i in ids), "oracle", sum(i in oracle for i in ids), "/", len(ids))


def fixed():
    return (json.loads((D / "split.json").read_text()), json.loads((D / "memos.json").read_text()),
            json.loads((D / "oracle.json").read_text()), corpus())


def preset_text(p):
    if p == "none": return "보이스톤 프리셋 없음 — 공통 문법만 지켜 자연스러운 한국어 앱 문구로 쓴다."
    d = json.loads((VOICES / f"{p}.json").read_text(encoding="utf-8"))
    for k in ("observed", "evidence_apps", "default"): d.pop(k, None)
    return "보이스톤 프리셋(이 말투로 쓴다 — 규칙·자리별 형태·버튼 짝·예시 쌍의 이유를 따른다):\n" + json.dumps(d, ensure_ascii=False, indent=1)


def generate(p, rows, memos):
    def one(batch):
        q = [{"id": r["id"], "slot": r["slot"], "meaning": memos.get(r["id"], r["situation"])} for r in batch]
        try: return kv(parse_json(claude(f"""너는 한국어 앱 UX 라이터다. 각 항목의 영어 뜻 메모를 그 자리(slot)에 들어갈 한국어 화면 문구로 쓴다. 영어를 옮기지 말고, 한국 앱이 실제로 쓰는 말로.

{COMMON}

{preset_text(p)}

항목:
{json.dumps(q, ensure_ascii=False, indent=1)}

JSON 배열만: [{{"id": "...", "text": "..."}}]""", GEN_MODEL)))
        except Limit: raise
        except Exception: return {}
    out = {}
    for _ in range(2):
        miss = [r for r in rows if r["id"] not in out]
        if not miss: break
        for m in pmap(one, [miss[i:i + 20] for i in range(0, len(miss), 20)]): out.update(m)
    return out


JUDGE = """각 문항에는 같은 뜻의 한국어 앱 화면 문구 두 개(A, B)가 있다. 하나는 실제 한국 앱(토스·배민·KB국민은행·정부24 같은)에 들어간 문구이고, 하나는 누군가 새로 쓴 것이다. **어느 쪽이 실제 앱 문구인지** 고르고, 판단 근거를 12자 이내로 적는다(예: "번역투", "너무 매끈함", "실제 앱식 축약", "어색한 경어").

{body}

JSON만: {{"<문항 번호>": {{"pick": "A|B", "why": "..."}}, ...}}"""


def judge(pairs, seed):
    """pairs: [{real, fake}] → [(실제를 맞혔나, 근거)]"""
    rng = random.Random(seed); Q = [(q, rng.random() < 0.5) for q in pairs]   # True면 A가 실제
    def ask(chunk):
        body = "\n".join(f"[{i+1}] A: {q['real'] if ra else q['fake']}\n    B: {q['fake'] if ra else q['real']}" for i, (q, ra) in enumerate(chunk))
        try: a = parse_json(claude(JUDGE.format(body=body), JUDGE_MODEL))
        except Limit: raise
        except Exception: a = {}
        res = []
        for i, (q, ra) in enumerate(chunk):
            x = a.get(str(i + 1)) or {}
            pk = x.get("pick") if isinstance(x, dict) else x
            res.append((None if pk not in ("A", "B") else (pk == "A") == ra, (x.get("why") if isinstance(x, dict) else "") or ""))
        return res
    return sum(pmap(ask, [Q[i:i + 12] for i in range(0, len(Q), 12)]), [])


def rule_bad(p, text):
    S = [s for s in re.split(r"(?<=[.?!])\s+|\s*/\s*|\n", text) if re.search(r"[가-힣]", s) and len(s) > 4]
    legal = re.search(r"철회|수수료|약관|법|인증서|고지|제재|제한|정지|위반", text)
    bad = []
    if p == "hamnida" and any(ending(s) == "haeyo" for s in S): bad.append("합니다체인데 해요체")
    if p == "haeyo" and any(ending(s) == "hamnida" for s in S) and not legal and not re.search(r"죄송합니다|감사합니다|고맙습니다", text): bad.append("해요체인데 합니다체")
    if re.search(r"\S\s+—\s+\S", text): bad.append("줄표")
    if re.search(r"당신|로 인한|을 통해|를 통해|유효하지 않은|처리가 완료", text): bad.append("번역투")
    return bad


def run(split_name="dev", seed=0, mode="preset", tag=None, presets=("haeyo", "hamnida")):
    """mode: preset(자기 묶음 프리셋) | none(공통 문법만 — 바닥) | oracle(말투 보존 바꿔쓰기 — 천장 확인)"""
    split, memos, oracle, items = fixed()
    rows = {p: [items[i] for a in CLUSTER[p] for i in split[a][split_name] if i in items] for p in presets}
    gens = {}
    if mode == "preset":
        for p, g in zip(presets, pmap(lambda p: generate(p, rows[p], memos), list(presets), 2)): gens[p] = g
    elif mode == "none":
        g = generate("none", sum(rows.values(), []), memos); gens = {p: g for p in presets}
    else: gens = {p: oracle for p in presets}
    pairs = [{"p": p, "app": r["app"], "id": r["id"], "real": r["text"], "fake": gens[p][r["id"]]} for p in presets for r in rows[p] if r["id"] in gens[p]]
    j1, j2 = judge(pairs, 100 + seed), judge(pairs, 200 + seed)
    res = {"split": split_name, "mode": mode, "seed": seed, "per": {}, "apps": {}}
    for key, sel in [("per", lambda q, p: q["p"] == p), ("apps", lambda q, a: q["app"] == a)]:
        for k in (presets if key == "per" else [a for p in presets for a in CLUSTER[p]]):
            v = [((a or 0) + (b or 0)) / 2 for q, (a, _), (b, _) in zip(pairs, j1, j2) if sel(q, k) and a is not None and b is not None]
            res[key][k] = {"n": len(v), "detect": sum(v) / len(v) if v else None}
    both = [(a, b) for (a, _), (b, _) in zip(j1, j2) if a is not None and b is not None]
    res["agree"] = sum(a == b for a, b in both) / max(1, len(both))
    tot = bad = dig = keep = 0
    for q in pairs:
        if mode != "preset": break
        tot += 1; bad += bool(rule_bad(q["p"], q["fake"]))
        d = digits(q["real"])
        if d: dig += 1; keep += d <= digits(q["fake"])
    res["U1"] = 1 - bad / tot if tot else None; res["U2"] = keep / dig if dig else None
    dets = [res["per"][p]["detect"] for p in presets if res["per"][p]["detect"] is not None]
    res["detect"] = sum(dets) / len(dets) if dets else None
    res["score"] = 1 - (res["detect"] or 1)                 # 높을수록 좋다(구별 안 됨). 0.5가 최대
    res["gate_ok"] = mode != "preset" or ((res["U1"] or 0) >= 0.98 and (res["U2"] or 0) >= 0.95)
    res["caught"] = [{"p": q["p"], "app": q["app"], "real": q["real"], "ours": q["fake"], "why": w}
                     for q, (a, w) in zip(pairs, j1) if a][:60]
    out = D / "runs" / f"{tag or (split_name + '-' + mode)}-{seed}.json"; out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps({k: res[k] for k in ("split", "mode", "detect", "U1", "U2", "agree")} | {p: res["per"][p] for p in presets}, ensure_ascii=False))
    return res


def calibrate():
    cur = [run("dev", s, "preset", tag="cal-current") for s in range(3)]
    none = run("dev", 8, "none", tag="cal-floor"); orc = run("dev", 7, "oracle", tag="cal-ceiling")
    out = {"current": [r["detect"] for r in cur], "current_per": [{p: r["per"][p]["detect"] for p in r["per"]} for r in cur],
           "U1": [r["U1"] for r in cur], "U2": [r["U2"] for r in cur], "agree": [r["agree"] for r in cur],
           "floor": {p: none["per"][p]["detect"] for p in none["per"]}, "ceiling": {p: orc["per"][p]["detect"] for p in orc["per"]},
           "sigma": statistics.pstdev([r["score"] for r in cur])}
    (D / "calibration.json").write_text(json.dumps(out, ensure_ascii=False, indent=1)); print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd"); ap.add_argument("--split", default="dev"); ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--mode", default="preset"); ap.add_argument("--tag")
    a = ap.parse_args()
    {"prepare": prepare, "calibrate": calibrate}.get(a.cmd, lambda: run(a.split, a.seed, a.mode, a.tag))()
