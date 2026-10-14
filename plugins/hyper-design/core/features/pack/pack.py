#!/usr/bin/env python3
"""pack.py — 작성 에이전트 한 명이 맡은 화면에 필요한 것을 파일 하나(PACK)로 묶는다.

    python3 pack.py <out> [--max-agents 5] [--screens id1,id2,...] [--mode build|state|revise]

출력: <out>/packs/<n>.md, <out>/packs/plan.json
계약: contract.md. 표준 라이브러리만. 같은 입력 → 같은 바이트.
"""
import argparse
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SK = HERE.parent.parent  # plugins/hyper-design/core
PRINCIPLES = SK / "references" / "principles.md"
COMPONENTS = SK / "foundation" / "COMPONENTS.md"
VOICES = SK / "foundation" / "voices"
EXAMPLES = SK / "foundation" / "examples"

# kind → 예시 화면 id. examples/screens.json 항목에 "kind"가 있으면 그것이 우선한다.
# (현재 examples/screens.json에는 kind가 없어 아래 표가 쓰인다 — id는 그 파일에 있는지 확인한다)
KIND_EXAMPLE_DEFAULT = {
    "home": "home",
    "list": "checklist",
    "detail": "day",
    "form": "item-edit",
    "result": "join",
}

SELFCHECK_RULES = """\
메인이 끝난 뒤 selfcheck.py로 검사한다. 이 규칙에 걸리면 다시 써야 한다 — 처음부터 지킨다.

- `h1`은 화면당 정확히 1개.
- `<link id="tokens" rel="stylesheet" href="../tokens.css">`와 `../palette.js`를 반드시 넣는다(COMPONENTS 뼈대 그대로).
- 인라인 `style` 금지. 예외는 `.range`의 `style="--from:…;--to:…"` 하나.
- 색 값 하드코딩 금지(`#fff` 같은 값). 색·글자·여백은 토큰 클래스로만.
- 모든 `href`·`src`는 실제로 있는 파일이어야 한다(깨진 참조 금지). 이미지는 아래에 준 경로만.
- 플레이스홀더 문구("사진 1"·"이미지"·Lorem) 금지, 유니코드 이모지 문자 금지, `title=` 속성(툴팁) 금지.
- 수동적 호칭(보기만·읽기 전용·게스트) 금지.
- 설명 한 줄만 든 블록은 화면당 1개 이하. "~를 누르면" 같은 조작법 설명 금지.
- 탭바가 있는 화면에 하단 고정 CTA 금지.
- 사진 자리(`.photo`·`.thumb`·`.photo-grid`·`.compare`)에는 반드시 `<img>`.
- `row is-add`는 다른 화면·시트로 가는 `<a href>`여야 한다.
- `large_list`가 true인 목록 화면은 검색 칸(`<label class="search">`) 필수.
- 사람 자리(`avatar`)에 사물 일러스트 금지 — 글자 아바타(`avatar is-text`).
- 사람 카드의 질문 문장을 화면 문구로 2개 이상 쓰지 않는다(질답지 금지) — 답은 데이터의 자리·크기로.
- 배지는 screens.json `badges` 표에 있는 이름·색만. 시간·순서는 배지가 아니라 글자.
- 강조 부품(`accent-text`·`accent-dot`)은 screens.json `accent`가 있을 때만, 화면당 2곳 이하, 제목·버튼·배지 안 금지.
- 흐름의 끝에는 결과 화면(`kind: result` 또는 `<id>--done`)이 있다 — 결과 화면은 그 행동이 끝난 모습을 보여 준다.
"""

TASK_RULES = "이 파일 하나만 읽는다 · 화면마다 Write 한 번 · 다시 열지 않는다 · 화면당 3분 상한"


# ---------- 읽기 ----------

def read_text(p):
    return Path(p).read_text(encoding="utf-8")


def load_json(p, default=None):
    p = Path(p)
    if not p.exists():
        return default
    try:
        return json.loads(read_text(p))
    except Exception:
        return default


def dumps(x):
    return json.dumps(x, ensure_ascii=False, indent=1, sort_keys=False)


# ---------- 묶기 ----------

def base_of(s, ids):
    """상태 화면이면 기본 화면 id, 아니면 자기 id."""
    if s.get("state_of"):
        return s["state_of"]
    sid = s["id"]
    if "--" in sid:
        b = sid.split("--", 1)[0]
        if b in ids:
            return b
    return sid


def make_units(screens):
    """기본 화면 + 그 상태 화면을 한 단위로. screens.json 순서 유지."""
    ids = {s["id"] for s in screens}
    units, index = [], {}
    for s in screens:
        b = base_of(s, ids)
        if b in index:
            units[index[b]]["ids"].append(s["id"])
        else:
            index[b] = len(units)
            group = s.get("group") or ""
            # 상태 화면이 먼저 나와도 기본 화면의 group을 쓴다
            for t in screens:
                if t["id"] == b and t.get("group"):
                    group = t["group"]
            units.append({"base": b, "group": group, "ids": [s["id"]]})
    return units


def order_by_group(units, group_order):
    rank = {g: i for i, g in enumerate(group_order)}
    first_seen = {}
    for i, u in enumerate(units):
        first_seen.setdefault(u["group"], i)
    return sorted(units, key=lambda u: (rank.get(u["group"], len(rank) + first_seen[u["group"]]), first_seen[u["group"]]))


def partition(units, k):
    """단위를 순서대로 k개의 연속 묶음으로 나눈다.
    1순위: 크기 차이(max-min) 최소, 2순위: 같은 group이 갈리는 횟수 최소. 결정적."""
    n = len(units)
    k = max(1, min(k, n))
    sizes = [len(u["ids"]) for u in units]
    pre = [0]
    for x in sizes:
        pre.append(pre[-1] + x)
    total = pre[-1]
    # cut 비용: units[i-1]과 units[i] 사이를 자르면 같은 group일 때 1
    cut_cost = [0] * (n + 1)
    for i in range(1, n):
        cut_cost[i] = 1 if units[i - 1]["group"] == units[i]["group"] else 0
    INF = float("inf")
    for d in range(0, total + 1):
        best = None
        for lo in range(1, total // k + 1):
            hi = lo + d
            # dp[j][i] = 앞 i개 단위를 j묶음으로 나눌 때 최소 비용, 경로 기록
            dp = [[INF] * (n + 1) for _ in range(k + 1)]
            back = [[-1] * (n + 1) for _ in range(k + 1)]
            dp[0][0] = 0
            for j in range(1, k + 1):
                for i in range(1, n + 1):
                    for p in range(j - 1, i):
                        if dp[j - 1][p] == INF:
                            continue
                        sz = pre[i] - pre[p]
                        if sz < lo or sz > hi:
                            continue
                        c = dp[j - 1][p] + (cut_cost[p] if p > 0 else 0)
                        if c < dp[j][i]:
                            dp[j][i] = c
                            back[j][i] = p
            if dp[k][n] < INF and (best is None or dp[k][n] < best[0]):
                cuts, i = [], n
                for j in range(k, 0, -1):
                    p = back[j][i]
                    cuts.append((p, i))
                    i = p
                best = (dp[k][n], list(reversed(cuts)))
        if best is not None:
            return [[sid for u in units[a:b] for sid in u["ids"]] for a, b in best[1]]
    return [[sid for u in units for sid in u["ids"]]]


def plan_packs(screens, group_order, max_agents):
    n = len(screens)
    k = max(1, min(max_agents, math.ceil(n / 4)))
    units = order_by_group(make_units(screens), group_order)
    k = min(k, len(units))
    return partition(units, k)


# ---------- 내용 조각 ----------

def section(md, heading_prefix):
    """'## <prefix>…'로 시작하는 절을 다음 '## ' 절 전까지 그대로."""
    lines = md.splitlines()
    out, on = [], False
    for ln in lines:
        if ln.startswith("## "):
            if on:
                break
            if ln.startswith("## " + heading_prefix):
                on = True
        if on:
            out.append(ln)
    return "\n".join(out).rstrip()


def components_text(out):
    text = read_text(COMPONENTS)
    icons = load_json(out / "icons.json")
    if not isinstance(icons, list) or not icons:
        return text
    names = []
    for ic in icons:
        if not isinstance(ic, dict) or not ic.get("name"):
            continue
        m = ic.get("meaning") or ""
        kind = " (사람)" if ic.get("kind") == "person" else ""
        names.append(f"- {ic['name']} — {m}{kind}".rstrip(" —"))
    listing = "이번 실행에서 쓸 수 있는 일러스트(`out/icons.json`) — 이 이름만 `../assets/fluent/<이름>.svg`로 쓴다:\n" + "\n".join(names)
    lines = text.splitlines()
    res, i = [], 0
    while i < len(lines):
        ln = lines[i]
        res.append(ln)
        i += 1
        if ln.startswith("## 일러스트"):
            # 첫 문단(이름 목록)을 icons.json 목록으로 바꾼다
            while i < len(lines) and not lines[i].strip():
                res.append(lines[i]); i += 1
            replaced = False
            while i < len(lines) and lines[i].strip() and not lines[i].startswith("## "):
                if not lines[i].startswith("용도"):
                    i += 1
                    replaced = True
                    continue
                break
            if replaced:
                res.append(listing)
                if i < len(lines) and lines[i].strip():
                    res.append("")
    return "\n".join(res) + ("\n" if text.endswith("\n") else "")


def voice_text(out):
    d = load_json(out / "decisions.json", {}) or {}
    v = str(d.get("voice") or "") if isinstance(d, dict) else ""
    # 값에 먼저 나오는 프리셋 이름을 쓴다(예: "haeyo — … 합니다체 예외" → haeyo)
    hits = [(v.find(x), x) for x in ("haeyo", "hamnida") if x in v]
    slug = min(hits)[1] if hits else "haeyo"
    p = VOICES / f"{slug}.json"
    if not p.exists():
        slug, p = "haeyo", VOICES / "haeyo.json"
    return slug, read_text(p).rstrip()


def example_map():
    ex = load_json(EXAMPLES / "screens.json", {}) or {}
    entries = ex.get("screens", []) if isinstance(ex, dict) else []
    ids = {e.get("id"): e for e in entries}
    m = {}
    for e in entries:
        if e.get("kind") and e["kind"] not in m:
            m[e["kind"]] = e.get("file") or f"{e['id']}.html"
    for kind, sid in KIND_EXAMPLE_DEFAULT.items():
        if kind in m:
            continue
        e = ids.get(sid)
        if e is not None:
            m[kind] = e.get("file") or f"{sid}.html"
    return m


def people_for(people, sid):
    res = []
    for p in people or []:
        at = [x for w in p.get("wants") or [] for x in (w.get("at") or [])]
        if sid in (p.get("screens") or []) or sid in at:
            res.append(p)
    return res


def spec_for(spec, sid, base, state):
    res = []
    for it in (spec or {}).get("items", []) if isinstance(spec, dict) else []:
        if sid in (it.get("covered_by") or []):
            res.append(it)
        elif it.get("kind") == "rule":
            if it.get("target") == sid or it.get("policy") == sid:
                res.append(it)
            elif state and it.get("target") == base and it.get("state") == state:
                res.append(it)
    return res


def slots_for(slots, sids, kind):
    return [s for s in slots if (s.get("kind") or "photo") == kind and any(x in (s.get("screens") or []) for x in sids)]


def market_text(out):
    conv = load_json(out / "conventions.json")
    if not isinstance(conv, dict):
        return ""
    dec = load_json(out / "decisions.json", {}) or {}
    verdict = {it.get("id"): it for it in (dec.get("items") or []) if it.get("source") == "시장"} if isinstance(dec, dict) else {}
    lines = []
    keep = []
    for f in conv.get("follow") or []:
        d = verdict.get(f.get("id"))
        if d and d.get("verdict") in ("keep", "lighten"):
            how = f" — 이 앱에서는: {d['how']}" if d.get("how") else ""
            keep.append(f"- [{f.get('id')}·{f.get('area', '')}] {f.get('what', '')}{how}")
    if keep:
        lines.append("따르는 관례(follow 중 keep·lighten) — 구조만 참고, 문구·그림·색은 베끼지 말 것:")
        lines += keep
    avoid = [f"- [{a.get('id')}] {a.get('what', '')}" for a in conv.get("avoid") or []]
    if avoid:
        lines.append("")
        lines.append("피할 것(리뷰 불만 — 해당 화면이면 정책·문구로 막는다):")
        lines += avoid
    return "\n".join(lines).strip()


# ---------- 쓰기 ----------

def screen_block(sid, smap, ctx, mode):
    s = smap[sid]
    ids = set(smap)
    base = base_of(s, ids)
    state = s.get("state") or (sid.split("--", 1)[1] if "--" in sid else None)
    out = ctx["out"]
    parts = [f"### 화면 `{sid}` → `{(out / 'screens' / (sid + '.html')).as_posix()}`", ""]
    if base != sid:
        parts.append(f"상태 화면 — 기본 화면 `{base}`(`{(out / 'screens' / (base + '.html')).as_posix()}`)과 구조가 같아야 한다. 바뀐 부분만 고친다. 해결 행동이 주 버튼.")
        parts.append("")
    parts += ["screens.json 항목:", "```json", json.dumps(s, ensure_ascii=False), "```", ""]
    ppl = people_for(ctx["people"], sid)
    if ppl:
        parts.append("이 화면을 쓰는 사람(카드 전문은 위 '사람 카드') — 이 화면에서 답할 질문을 첫 화면에서 가장 크게, 질문 문장을 제목으로 달지 않는다:")
        for p in ppl:
            qs = [w.get("q", "") for w in p.get("wants") or [] if sid in (w.get("at") or [])]
            parts.append(f"- {p.get('name', '')}" + (f" — 이 화면의 질문: " + " / ".join(qs) if qs else ""))
        parts.append("")
    sp = spec_for(ctx["spec"], sid, base, state)
    if sp:
        parts.append("명세 항목(PRD 원문 인용):")
        for it in sp:
            extra = ""
            if it.get("kind") == "rule":
                extra = f" (규칙 · state: {it.get('state') or it.get('state_hint') or '-'}" + (f" · policy" if it.get("policy") == sid else "") + ")"
            parts.append(f"- {it.get('id')} {it.get('name', '')}{extra} — 인용: \"{it.get('quote', '')}\"")
        parts.append("")
    sids = [sid] + ([base] if base != sid else [])
    photos = slots_for(ctx["slots"], sids, "photo")
    if photos:
        parts.append("사진 경로(이 경로만 쓴다):")
        for p in photos:
            parts.append(f"- `../assets/photos/{p['slot']}.jpg` — {p.get('what', '')} ({p.get('ratio', '')})")
        parts.append("")
    icon_slots = slots_for(ctx["slots"], sids, "icon")
    if icon_slots:
        parts.append("아이콘(일러스트) 이름:")
        for sl in icon_slots:
            name = ctx["icon_by_slot"].get(sl["slot"])
            if name:
                parts.append(f"- `{name}` → `../assets/fluent/{name}.svg` — {sl.get('what', '')}")
            else:
                parts.append(f"- (해결 안 됨: {sl['slot']}) — {sl.get('what', '')} · 위 일러스트 목록에서 가장 가까운 것을 쓴다")
        parts.append("")
    drawings = slots_for(ctx["slots"], sids, "drawing")
    if drawings:
        parts.append("직접 그리는 자리(도식·지도·QR — 선과 토큰 색만):")
        for d in drawings:
            parts.append(f"- {d['slot']} — {d.get('what', '')}")
        parts.append("")
    return "\n".join(parts).rstrip()


def build_pack(n, sids, smap, ctx, mode):
    out = ctx["out"]
    H = []
    # 1. 할 일
    H.append(f"# PACK {n} — 화면 {len(sids)}장 ({mode})")
    H.append("")
    H.append("## 1. 할 일")
    H.append("")
    if mode == "build":
        H.append("아래 화면을 새로 쓴다.")
    elif mode == "state":
        H.append("상태 화면을 쓴다 — 기본 화면 파일을 복사해 바뀐 부분만 고친다. 구조(제목 위치·블록 묶음·사진 크기)는 그대로, 주 버튼은 그 상태를 푸는 행동.")
    else:
        H.append("기존 화면을 고친다 — 요청된 경로의 요소만, 요청만 반영. 요청은 프롬프트에 있다. 나머지는 건드리지 않는다.")
    H.append("")
    for sid in sids:
        H.append(f"- `{sid}` → `{(out / 'screens' / (sid + '.html')).as_posix()}`")
    H.append("")
    H.append(TASK_RULES)
    H.append("")
    if mode == "revise":
        H.append("## 2. 부품 (COMPONENTS.md 전문)")
        H.append("")
        H.append(ctx["components"].rstrip())
        H.append("")
        H.append(f"## 3. 보이스톤 프리셋 ({ctx['voice_slug']})")
        H.append("")
        H.append("```json")
        H.append(ctx["voice"])
        H.append("```")
        H.append("")
        H.append("## 4. 고칠 화면의 현재 파일")
        H.append("")
        for sid in sids:
            H.append(f"- `{sid}`: `{(out / 'screens' / (sid + '.html')).as_posix()}`")
        return "\n".join(H).rstrip() + "\n"
    # 2. 원칙
    H.append("## 2. 원칙 (principles.md 전문)")
    H.append("")
    H.append(ctx["principles"].rstrip())
    H.append("")
    # 3. 부품
    H.append("## 3. 부품 (COMPONENTS.md 전문)")
    H.append("")
    H.append(ctx["components"].rstrip())
    H.append("")
    # 4. 보이스톤
    H.append(f"## 4. 보이스톤 프리셋 ({ctx['voice_slug']}) — 모든 문구가 이 규칙을 따른다")
    H.append("")
    H.append("```json")
    H.append(ctx["voice"])
    H.append("```")
    H.append("")
    # 5. 사실 표
    H.append("## 5. 시나리오 데이터 · 사실 표")
    H.append("")
    if ctx["scenario"]:
        H.append(ctx["scenario"])
        H.append("")
    if ctx["facts"]:
        H.append(ctx["facts"])
        H.append("")
    H.append("**표에 없는 날짜·숫자·상태를 지어내지 말 것.**")
    H.append("")
    # 6. 화면별
    H.append("## 6. 화면별 자료")
    H.append("")
    if ctx["market"]:
        H.append("시장 관례(이 묶음 전체):")
        H.append("")
        H.append(ctx["market"])
        H.append("")
    ppl_all = [p for p in ctx["people"] if any(p in people_for(ctx["people"], x) for x in sids)]
    if ppl_all:
        H.append("사람 카드(이 묶음의 화면을 쓰는 사람):")
        H.append("")
        H.append("```json")
        H.append(dumps(ppl_all))
        H.append("```")
        H.append("")
    for sid in sids:
        H.append(screen_block(sid, smap, ctx, mode))
        H.append("")
    # 7. 구조 예시
    H.append("## 7. 구조 예시 — 구조만 참고, 내용 베끼지 말 것")
    H.append("")
    kinds = []
    for sid in sids:
        k = smap[sid].get("kind")
        if k and k not in kinds:
            kinds.append(k)
    shown = False
    for k in kinds:
        f = ctx["examples"].get(k)
        if not f or not (EXAMPLES / f).exists():
            continue
        shown = True
        H.append(f"### kind `{k}` — 예시 `{f}` (구조만 참고, 내용 베끼지 말 것)")
        H.append("")
        H.append("```html")
        H.append(read_text(EXAMPLES / f).rstrip())
        H.append("```")
        H.append("")
    if not shown:
        H.append("(이 묶음의 kind에 맞는 예시 없음 — COMPONENTS 뼈대를 따른다)")
        H.append("")
    # 8. 셀프체크
    H.append("## 8. 셀프체크 규칙 요약")
    H.append("")
    H.append(SELFCHECK_RULES.rstrip())
    return "\n".join(H).rstrip() + "\n"


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except Exception:
            pass
    ap =argparse.ArgumentParser(description="작성 에이전트용 PACK 파일을 만든다 (out/packs/<n>.md + plan.json).")
    ap.add_argument("out", help="실행 산출물 폴더 (screens.json이 있는 out)")
    ap.add_argument("--max-agents", type=int, default=5, help="에이전트(묶음) 수 상한, 기본 5")
    ap.add_argument("--screens", default="", help="쉼표로 구분한 화면 id (state·revise 모드에서 필수)")
    ap.add_argument("--mode", choices=["build", "state", "revise"], default="build")
    a = ap.parse_args(argv)

    out = Path(a.out).resolve()
    sj = load_json(out / "screens.json")
    if not isinstance(sj, dict) or not sj.get("screens"):
        print(f"screens.json 없음/비어 있음: {out / 'screens.json'}", file=sys.stderr)
        return 1
    all_screens = sj["screens"]
    smap = {s["id"]: s for s in all_screens}
    want = [x.strip() for x in a.screens.split(",") if x.strip()]
    if a.mode in ("state", "revise") and not want:
        print(f"--mode {a.mode}에는 --screens가 필요하다", file=sys.stderr)
        return 2
    missing = [x for x in want if x not in smap]
    if missing:
        print(f"screens.json에 없는 화면: {', '.join(missing)}", file=sys.stderr)
        return 2
    screens = [s for s in all_screens if s["id"] in set(want)] if want else list(all_screens)

    groups = plan_packs(screens, sj.get("groups") or [], max(1, a.max_agents))

    journey = read_text(out / "journey.md") if (out / "journey.md").exists() else ""
    slots = load_json(out / "image_slots.json", [])
    if isinstance(slots, dict):
        slots = slots.get("slots") or []
    icons = load_json(out / "icons.json", [])
    icon_by_slot = {}
    for ic in icons if isinstance(icons, list) else []:
        if isinstance(ic, dict) and ic.get("slot") and ic.get("name"):
            icon_by_slot.setdefault(ic["slot"], ic["name"])
    voice_slug, voice = voice_text(out)
    ctx = {
        "out": out,
        "principles": read_text(PRINCIPLES),
        "components": components_text(out),
        "voice_slug": voice_slug,
        "voice": voice,
        "scenario": section(journey, "시나리오 데이터 표"),
        "facts": section(journey, "사실 표"),
        "people": sj.get("people") or [],
        "spec": load_json(out / "spec_inventory.json", {}) or {},
        "slots": [s for s in (slots or []) if isinstance(s, dict) and s.get("slot")],
        "icon_by_slot": icon_by_slot,
        "market": market_text(out),
        "examples": example_map(),
    }

    pdir = out / "packs"
    pdir.mkdir(parents=True, exist_ok=True)
    for old in pdir.glob("*.md"):
        if old.stem.isdigit():
            old.unlink()
    plan = {"mode": a.mode, "agents": []}
    for i, sids in enumerate(groups, 1):
        p = pdir / f"{i}.md"
        p.write_bytes(build_pack(i, sids, smap, ctx, a.mode).encode("utf-8"))
        plan["agents"].append({"pack": p.as_posix(), "screens": sids})
    (pdir / "plan.json").write_bytes((json.dumps(plan, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
    for ag in plan["agents"]:
        print(f"{ag['pack']}  {len(ag['screens'])}장  {','.join(ag['screens'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
