"""상태 화면 항목을 자동으로 펼친다 — 메인은 기본 화면만 쓰고, 상태는 traits·규칙에서 파생한다.

python3 expand_states.py out [--stage go|max]
- go(1차): 결과 화면(done)만 펼치고, max가 더할 상태 수를 pending_states로 남긴다 · max(2차): 전부
입력: out/screens.json(기본 화면) + out/spec_inventory.json(있으면, kind=rule 의 target·state)
파생: list_first_use→empty · form→error · shares→done · long_task→progress · rule(state=error|confirm|done)
- 같은 화면·같은 상태의 규칙 여럿은 상태 화면 하나로 묶고, 규칙 이름은 그 화면 policies에 한 줄씩
- 기본 화면의 states를 채우고 <id>--<state> 항목을 추가(이미 있으면 필요한 필드만 보충), 파생되지 않는 상태 항목은 지운다
- 화면당 상태 > 2(기본 포함 3)면 종료코드 1(규칙 일부를 정책 문구로 내린다)
"""
import sys, json, pathlib
out = pathlib.Path(sys.argv[1])
STAGE = sys.argv[sys.argv.index("--stage") + 1] if "--stage" in sys.argv else "max"
GO_ONLY = {"done"}
M = json.loads((out / "screens.json").read_text(encoding="utf-8"))
inv = {}
if (out / "spec_inventory.json").exists():
    inv = json.loads((out / "spec_inventory.json").read_text(encoding="utf-8"))
KO = {"empty": "처음(비어 있음)", "error": "오류", "done": "보낸 뒤", "confirm": "확인", "progress": "진행 중"}
TRAIT = {"list_first_use": "empty", "form": "error", "shares": "done", "long_task": "progress"}
base = [s for s in M["screens"] if "--" not in s["id"]]
old = {s["id"]: s for s in M["screens"] if "--" in s["id"]}
ids = {s["id"] for s in base}
rules = {}
errs = []
for it in inv.get("items", []):
    if it.get("kind") != "rule" or not it.get("target"): continue
    st = it.get("state") or "error"
    if st not in ("error", "confirm", "done"): errs.append(f"규칙 {it.get('id')}: state {st} 불가(error|confirm|done)"); continue
    if it["target"] not in ids: errs.append(f"규칙 {it.get('id')}: 없는 화면 {it['target']}"); continue
    rules.setdefault((it["target"], st), []).append(it)
new = []; pending = 0
for s in base:
    t = s.get("traits") or {}
    states = [v for k, v in TRAIT.items() if t.get(k)]
    for (tid, st) in rules:
        if tid == s["id"] and st not in states: states.append(st)
    full = list(states)
    if STAGE == "go": states = [x for x in states if x in GO_ONLY]
    pending += len(full) - len(states)
    if len(full) > 2: errs.append(f"{s["id"]}: 상태 {len(full)}개 > 2(기본 포함 3) — 규칙 일부를 정책 문구로 내릴 것")
    s["states"] = states
    new.append(s)
    for st in states:
        sid = f"{s['id']}--{st}"
        r = rules.get((s["id"], st), [])
        e = old.get(sid, {})
        e.update({"id": sid, "file": e.get("file") or f"screens/{sid}.html", "group": s.get("group"),
                  "title": e.get("title") or f"{s.get('title', s['id'])} · {KO[st]}",
                  "purpose": e.get("purpose") or (" · ".join(x["name"] for x in r) if r else f"{KO[st]} 모습"),
                  "role": s.get("role"), "kind": s.get("kind"), "state_of": s["id"], "state": st})
        if r:
            e["rules"] = [x.get("id") for x in r]
            pol = list(e.get("policies") or [])
            for x in r:
                line = f"[{x.get('id')}] {x['name']}"
                if line not in pol: pol.append(line)
            e["policies"] = pol
        new.append(e)
M["screens"] = new; M["stage"] = STAGE; M["pending_states"] = pending
(out / "screens.json").write_text(json.dumps(M, ensure_ascii=False, indent=1), encoding="utf-8")
n = sum(1 for s in new if "--" in s["id"])
print(f"[{STAGE}] 기본 {len(base)} · 상태 {n} · 2차에서 더할 상태 {pending} · 규칙 묶음 {len(rules)}")
if errs: print("\n".join(errs)); sys.exit(1)
