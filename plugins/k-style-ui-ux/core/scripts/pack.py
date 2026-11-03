#!/usr/bin/env python3
"""빌드 에이전트마다 읽을 묶음 파일 하나를 미리 조립한다 — 메인은 경로만 넘긴다.

python3 pack.py out [--max-agents 10] [--per 4]
- 화면 나누기: 에이전트 수 = ceil(전체 화면 수 / per)(최대 max-agents). 상태 화면(`<id>--<상태>`·state_of)은 기본 화면과 같은 묶음,
  screens.json `groups` 순서로 늘어놓고 연속으로 자른다 — 묶음 크기 차이 최소, 같은 group이 갈리는 횟수 최소. 결정적.
- 묶음 내용(go 2단계가 붙이라던 것 전부): 지시문(references/build.md) · 원칙 전문 · COMPONENTS.md 전문 · 공통 표(badges·accent·promos 등과
  전체 화면 목록) · journey.md의 시나리오 데이터 표·사실 표 · 사람 카드 · 시장 관례(follow 중 keep·lighten + 근거 시트, avoid) ·
  맡은 화면마다 screens.json 항목·화면 유형 행·명세 항목(원문 인용)·이미지 자리 경로 · 모범 답안 경로 · 확인 문구
출력: out/packs/<n>.md, out/packs/plan.json({"agents": [{"n", "pack", "screens", "confirm"}]})
없는 입력 파일은 그 절을 건너뛴다(screens.json만 필수). 표준 라이브러리만.
원작: eungshin/hyper-design features/pack/pack.py(PR #29) — 묶는 규칙·명세/사람/이미지 고르기를 가져왔다.
"""
import argparse, hashlib, json, math, re, sys
from pathlib import Path

SK = Path(__file__).resolve().parent.parent
PRINCIPLES = SK / "references/principles.md"
COMPONENTS = SK / "foundation/COMPONENTS.md"
BRIEF = SK / "references/build.md"
KINDS = SK / "references/screen-kinds.md"
EXAMPLES = SK / "foundation/examples"
SHARED = ("badges", "accent", "promos", "avatar_style", "photo_centric")


def read(p):
    return Path(p).read_text(encoding="utf-8")


def load(p, default=None):
    try:
        return json.loads(read(p))
    except Exception:
        return default


# ---------- 화면 나누기 ----------

def base_of(s, ids):
    if s.get("state_of"):
        return s["state_of"]
    b = s["id"].split("--", 1)[0]
    return b if b in ids else s["id"]


def make_units(screens):
    """기본 화면 + 그 상태 화면을 한 단위로. screens.json 순서 유지, group은 기본 화면 것."""
    ids = {s["id"] for s in screens}
    group = {s["id"]: s.get("group") or "" for s in screens}
    units, index = [], {}
    for s in screens:
        b = base_of(s, ids)
        if b in index:
            units[index[b]]["ids"].append(s["id"])
        else:
            index[b] = len(units)
            units.append({"base": b, "group": group.get(b) or group[s["id"]], "ids": [s["id"]]})
    for u in units:  # 기본 화면을 먼저(상태 화면은 그 파일을 복사한다)
        u["ids"].sort(key=lambda x: x != u["base"])
    return units


def order_by_group(units, group_order):
    rank = {g: i for i, g in enumerate(group_order)}
    first = {}
    for i, u in enumerate(units):
        first.setdefault(u["group"], i)
    return sorted(units, key=lambda u: (rank.get(u["group"], len(rank) + first[u["group"]]), first[u["group"]]))


def partition(units, k):
    """단위를 순서대로 k개의 연속 묶음으로. 1순위 크기 차이(max-min) 최소, 2순위 같은 group이 갈리는 횟수 최소."""
    n = len(units)
    k = max(1, min(k, n))
    pre = [0]
    for u in units:
        pre.append(pre[-1] + len(u["ids"]))
    total = pre[-1]
    cut = [0] + [1 if units[i - 1]["group"] == units[i]["group"] else 0 for i in range(1, n)] + [0]
    INF = float("inf")
    for d in range(total + 1):
        best = None
        for lo in range(1, total // k + 1):
            hi = lo + d
            dp = [[INF] * (n + 1) for _ in range(k + 1)]
            back = [[-1] * (n + 1) for _ in range(k + 1)]
            dp[0][0] = 0
            for j in range(1, k + 1):
                for i in range(1, n + 1):
                    for p in range(j - 1, i):
                        if dp[j - 1][p] == INF or not lo <= pre[i] - pre[p] <= hi:
                            continue
                        c = dp[j - 1][p] + (cut[p] if p > 0 else 0)
                        if c < dp[j][i]:
                            dp[j][i], back[j][i] = c, p
            if dp[k][n] < INF and (best is None or dp[k][n] < best[0]):
                cuts, i = [], n
                for j in range(k, 0, -1):
                    p = back[j][i]
                    cuts.append((p, i))
                    i = p
                best = (dp[k][n], cuts[::-1])
        if best:
            return [[sid for u in units[a:b] for sid in u["ids"]] for a, b in best[1]]
    return [[sid for u in units for sid in u["ids"]]]


def plan(screens, group_order, per, max_agents):
    units = order_by_group(make_units(screens), group_order)
    k = min(max(1, min(max_agents, math.ceil(len(screens) / per))), len(units))
    return partition(units, k)


# ---------- 조각 ----------

def md_sections(md, pat):
    """제목에 pat이 들어간 절(어느 단계든)을 같은 단계 이상의 다음 제목 전까지."""
    out, level = [], 0
    for ln in md.splitlines():
        m = re.match(r"(#{1,6})\s", ln)
        if m:
            lv = len(m.group(1))
            if level and lv <= level:
                level = 0
            if not level and re.search(pat, ln):
                level = lv
        if level:
            out.append(ln)
    return "\n".join(out).strip()


def kind_rows():
    """screen-kinds.md 표에서 {(home|detail|list, 유형): (머리줄, 행)}."""
    md, res = read(KINDS), {}
    for kind, head in (("home", "## 홈"), ("detail", "## 상세"), ("list", "## 목록")):
        if head not in md:
            continue
        rows = [l for l in md.split(head, 1)[1].split("\n## ", 1)[0].splitlines() if l.startswith("|")]
        if len(rows) < 3:
            continue
        cols = [c.strip() for c in rows[0].strip().strip("|").split("|")]
        if "유형" not in cols:
            continue
        for r in rows[2:]:
            cells = [c.strip() for c in r.strip().strip("|").split("|")]
            if len(cells) == len(cols):
                res[(kind, cells[cols.index("유형")].strip("*"))] = (rows[0] + "\n" + rows[1], r)
    return res


def people_for(people, sid):
    return [p for p in people or [] if sid in (p.get("screens") or [])
            or any(sid in (w.get("at") or []) for w in p.get("wants") or [])]


def spec_for(spec, sid, base, state):
    res = []
    for it in (spec or {}).get("items", []) if isinstance(spec, dict) else []:
        if sid in (it.get("covered_by") or []):
            res.append(it)
        elif it.get("kind") == "rule":
            if sid in (it.get("target"), it.get("policy")) or (state and it.get("target") == base and it.get("state") == state):
                res.append(it)
    return res


def slots_for(slots, sids):
    return [s for s in slots if any(x in (s.get("screens") or []) for x in sids)]


def market_text(out):
    conv = load(out / "conventions.json")
    if not isinstance(conv, dict):
        return ""
    dec = load(out / "decisions.json", {}) or {}
    verdict = {it.get("id"): it for it in dec.get("items") or [] if isinstance(it, dict)} if isinstance(dec, dict) else {}
    apps = (load(out / "market/apps.json", {}) or {}).get("apps") or []
    def sheets(names):
        return [a["sheet"] for a in apps if a.get("sheet") and any(n and (n in a.get("name", "") or a.get("name", "") in n) for n in names)]
    lines = []
    keep = []
    for f in conv.get("follow") or []:
        d = verdict.get(f.get("id")) or {}
        if d.get("verdict") not in ("keep", "lighten"):
            continue
        how = f" — 이 앱에서는: {d['how']}" if d.get("how") else ""
        sh = sheets(f.get("seen_in") or [])
        keep.append(f"- [{f.get('id')} · {f.get('area', '')}] {f.get('what', '')}{how}"
                    + (f" (근거: {f.get('evidence', '')}" + (" · 시트 " + ", ".join(f"`{x}`" for x in sh) if sh else "") + ")" if f.get("evidence") or sh else ""))
    if keep:
        lines += ["따르는 관례(follow 중 keep·lighten) — 맡은 화면의 영역(area)에 해당하는 것만 적용. 구조만 참고, 문구·그림·색은 베끼지 말 것:", *keep]
    avoid = [f"- [{a.get('id')}] {a.get('what', '')}" for a in conv.get("avoid") or []]
    if avoid:
        lines += ["", "피할 것(리뷰 불만 — 맡은 화면에 해당하면 정책·문구로 막는다):", *avoid]
    return "\n".join(lines).strip()


def jblock(x):
    return "```json\n" + json.dumps(x, ensure_ascii=False) + "\n```"


def demote(md, by=1):
    """붙여 넣는 문서의 제목을 한 단계씩 내린다(묶음의 ## 절과 섞이지 않게). 코드 블록 안은 그대로."""
    res, code = [], False
    for ln in md.splitlines():
        if ln.startswith("```"):
            code = not code
        res.append("#" * by + ln if not code and re.match(r"#{1,5}\s", ln) else ln)
    return "\n".join(res)


def screen_block(sid, smap, ctx):
    s, out = smap[sid], ctx["out"]
    base = base_of(s, set(smap))
    state = s.get("state") or (sid.split("--", 1)[1] if "--" in sid else None)
    P = [f"### `{sid}` → `{out / (s.get('file') or f'screens/{sid}.html')}`", ""]
    if base != sid:
        P += [f"상태 화면 — 기본 화면 `{base}`(`{out / (smap[base].get('file') or f'screens/{base}.html')}`)을 복사해 바뀐 부분만 고친다. 해결 행동이 주 버튼.", ""]
    P += [jblock(s), ""]
    row = ctx["kinds"].get((s.get("kind"), s.get("archetype")))
    if row and base == sid:
        P += [f"화면 유형 `{s['archetype']}` (screen-kinds.md) — 주인공 요소에 `data-anchor`:", "", row[0], row[1], ""]
    elif s.get("archetype") and base == sid:
        P += [f"화면 유형 `{s['archetype']}` — screen-kinds.md 표에 없는 이름. `{SK / 'references/screen-kinds.md'}`에서 가장 가까운 행을 찾는다.", ""]
    qs = [(p.get("name", ""), w.get("q", "")) for p in ctx["people"] for w in p.get("wants") or [] if sid in (w.get("at") or [])]
    if qs:
        P += ["이 화면이 답하는 질문(첫 화면에서 답을 가장 크게, 질문 문장을 제목으로 달지 않는다):", *[f"- {n}: {q}" for n, q in qs], ""]
    sp = spec_for(ctx["spec"], sid, base, state)
    if sp:
        P += ["명세 항목(PRD 원문 인용):"]
        for it in sp:
            ex = f" (규칙 · {it.get('state') or ('정책 문구' if it.get('policy') == sid else '-')})" if it.get("kind") == "rule" else ""
            P.append(f"- {it.get('id')} {it.get('name', '')}{ex} — \"{it.get('quote', '')}\"")
        P.append("")
    sl = slots_for(ctx["slots"], [sid] + ([base] if base != sid else []))
    if sl:
        P += ["이미지 자리(이 경로만 쓴다):"]
        for x in sl:
            if (x.get("kind") or "photo") == "photo":
                P.append(f"- `../assets/photos/{x['slot']}.jpg` — {x.get('what', '')} ({x.get('ratio', '')})")
            else:
                P.append(f"- {x['slot']} (직접 그린다 — 선과 토큰 색만) — {x.get('what', '')}")
        P.append("")
    return "\n".join(P).rstrip()


def build(n, sids, smap, ctx):
    out = ctx["out"]
    H = [f"# 빌드 묶음 {n} — 화면 {len(sids)}장", "",
         "맡은 화면: " + " · ".join(f"`{x}`" for x in sids), "",
         "## 1. 지시문", "", ctx["brief"], "",
         "## 2. 원칙 (principles.md 전문)", "", ctx["principles"], "",
         "## 3. 부품 (COMPONENTS.md 전문)", "", ctx["components"], "",
         "## 4. 앱 전체 공통", "", jblock(ctx["shared"]), "",
         "전체 화면 목록(링크는 같은 폴더의 `<id>.html`):", "", *ctx["index"], ""]
    H += ["## 5. 시나리오 데이터 표 · 사실 표", "", ctx["facts"] or "(journey.md에 없음)", "",
          "**표에 없는 날짜·숫자·상태를 지어내지 말 것.**", ""]
    ppl = [p for p in ctx["people"] if any(p in people_for(ctx["people"], x) for x in sids)] or ctx["people"]
    if ppl:
        H += ["## 6. 사람 카드 (맡은 화면을 쓰는 사람)", "", jblock(ppl), ""]
    if ctx["market"]:
        H += ["## 7. 시장 관례", "", ctx["market"], ""]
    H += ["## 8. 맡은 화면", ""]
    for sid in sids:
        H += [screen_block(sid, smap, ctx), ""]
    H += ["## 9. 더 열어 볼 것", "",
          f"- PRD: `{out / 'prd.md'}` — 맡은 화면의 절만",
          f"- 모범 답안(구조만 참고, 내용 베끼지 말 것) `{EXAMPLES}/`: " + ", ".join(ctx["examples"]), ""]
    body = "\n".join(H).rstrip() + "\n"
    confirm = f"묶음{n}-{hashlib.sha1(body.encode('utf-8')).hexdigest()[:8]}"
    return body + f"\n## 끝\n\n확인 문구: `{confirm}` — 결과 보고 첫 줄에 이 문구를 그대로 쓴다.\n", confirm


def main(argv=None):
    ap = argparse.ArgumentParser(description="빌드 에이전트별 묶음 파일(out/packs/<n>.md + plan.json)")
    ap.add_argument("out")
    ap.add_argument("--max-agents", type=int, default=10)
    ap.add_argument("--per", type=int, default=4, help="에이전트 하나가 맡는 화면 수(ceil 기준)")
    a = ap.parse_args(argv)
    out = Path(a.out).resolve()
    sj = load(out / "screens.json")
    if not isinstance(sj, dict) or not sj.get("screens"):
        print(f"screens.json 없음/비어 있음: {out / 'screens.json'}", file=sys.stderr)
        return 1
    screens = sj["screens"]
    smap = {s["id"]: s for s in screens}
    groups = plan(screens, sj.get("groups") or [], max(1, a.per), max(1, a.max_agents))
    journey = read(out / "journey.md") if (out / "journey.md").exists() else ""
    facts = md_sections(journey, r"시나리오|사실") or journey.strip()
    slots = load(out / "image_slots.json", []) or []
    if isinstance(slots, dict):
        slots = slots.get("slots") or []
    ctx = {
        "out": out,
        "brief": read(BRIEF)[read(BRIEF).find("\n- ") + 1:].strip(),  # 머리말 빼고 목록부터
        "principles": demote(read(PRINCIPLES).strip(), 2),
        "components": demote(read(COMPONENTS).strip(), 2),
        "shared": {k: sj[k] for k in SHARED if k in sj},
        "index": [f"- `{s['id']}` {s.get('title', '')} ({s.get('kind', '')})" for s in screens],
        "facts": demote(facts, 3 - min((len(m) for m in re.findall(r"(?m)^(#+)\s", facts)), default=3)) if facts else "",
        "people": sj.get("people") or [],
        "spec": load(out / "spec_inventory.json", {}) or {},
        "slots": [s for s in slots if isinstance(s, dict) and s.get("slot")],
        "market": market_text(out),
        "kinds": kind_rows(),
        "examples": sorted(p.name for p in EXAMPLES.glob("*.html")),
    }
    pdir = out / "packs"
    pdir.mkdir(parents=True, exist_ok=True)
    for old in pdir.glob("*.md"):
        old.unlink()
    res = {"agents": []}
    for i, sids in enumerate(groups, 1):
        text, confirm = build(i, sids, smap, ctx)
        p = pdir / f"{i}.md"
        p.write_text(text, encoding="utf-8")
        res["agents"].append({"n": i, "pack": str(p), "screens": sids, "confirm": confirm})
        print(f"{p}  {len(sids)}장  {len(text.encode('utf-8')) // 1024}KB  확인 {confirm}  {','.join(sids)}")
    (pdir / "plan.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"pack: 화면 {len(screens)}장 → 에이전트 {len(groups)}개 · {pdir / 'plan.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
