"""pack.py 불변식 (TDR v2 8절 pack 행) — 도메인 규칙이 아니라 모든 도메인에 성립하는 것만."""
import importlib.util
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
PACK_PY = HERE.parent / "pack.py"
FIX = HERE / "fixtures" / "laundry"

spec = importlib.util.spec_from_file_location("pack", PACK_PY)
pack = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pack)

ICON_SLOTS = [
    {"slot": "ic-basket", "kind": "icon", "screens": ["home", "order-items"], "what": "세탁물 바구니", "en": ["laundry basket", "basket"]},
    {"slot": "ic-truck", "kind": "icon", "screens": ["delivered"], "what": "배송 차량", "en": ["delivery truck"]},
]


def make_out(tmp_path, icons=True):
    out = tmp_path / "out"
    shutil.copytree(FIX, out)
    if not icons:
        (out / "icons.json").unlink()
    else:
        slots = json.loads((out / "image_slots.json").read_text(encoding="utf-8"))
        (out / "image_slots.json").write_text(json.dumps(slots + ICON_SLOTS, ensure_ascii=False), encoding="utf-8")
    return out


def run(out, *args):
    r = subprocess.run([sys.executable, str(PACK_PY), str(out), *args], capture_output=True)
    assert r.returncode == 0, r.stderr.decode("utf-8", "replace")
    plan = json.loads((out / "packs" / "plan.json").read_text(encoding="utf-8"))
    texts = {a["pack"]: Path(a["pack"]).read_text(encoding="utf-8") for a in plan["agents"]}
    return plan, texts


def screens(out):
    return json.loads((out / "screens.json").read_text(encoding="utf-8"))["screens"]


def base(sid):
    return sid.split("--", 1)[0]


def components_core_lines():
    """COMPONENTS.md에서 일러스트 이름 목록(바뀌는 문단)을 뺀 모든 줄."""
    lines = pack.COMPONENTS.read_text(encoding="utf-8").splitlines()
    keep, i = [], 0
    while i < len(lines):
        ln = lines[i]
        keep.append(ln)
        i += 1
        if ln.startswith("## 일러스트"):
            while i < len(lines) and not lines[i].strip():
                i += 1
            while i < len(lines) and lines[i].strip() and not lines[i].startswith(("용도", "## ")):
                i += 1
    return [l for l in keep if l.strip()]


@pytest.fixture
def built(tmp_path):
    out = make_out(tmp_path)
    plan, texts = run(out)
    return out, plan, texts


def test_every_screen_in_exactly_one_pack(built):
    out, plan, _ = built
    got = [s for a in plan["agents"] for s in a["screens"]]
    assert sorted(got) == sorted(s["id"] for s in screens(out))
    assert len(got) == len(set(got))


def test_states_with_base_and_agent_limit(built):
    out, plan, _ = built
    owner = {s: i for i, a in enumerate(plan["agents"]) for s in a["screens"]}
    for sid in owner:
        if "--" in sid and base(sid) in owner:
            assert owner[sid] == owner[base(sid)], sid
    n = len(screens(out))
    assert len(plan["agents"]) <= 5
    assert len(plan["agents"]) == min(5, math.ceil(n / 4))
    sizes = [len(a["screens"]) for a in plan["agents"]]
    assert max(sizes) - min(sizes) <= 2


def test_max_agents_option(tmp_path):
    out = make_out(tmp_path)
    plan, _ = run(out, "--max-agents", "2")
    assert len(plan["agents"]) == 2


def test_full_principles_components_facts(built):
    out, plan, texts = built
    principles = pack.PRINCIPLES.read_text(encoding="utf-8").rstrip()
    comp_lines = components_core_lines()
    journey = (out / "journey.md").read_text(encoding="utf-8")
    facts = pack.section(journey, "사실 표")
    scenario = pack.section(journey, "시나리오 데이터 표")
    assert len(facts) > 200 and len(scenario) > 50
    for t in texts.values():
        assert principles in t
        for ln in comp_lines:
            assert ln in t, ln
        assert facts in t and scenario in t
        assert "표에 없는 날짜·숫자·상태를 지어내지 말 것" in t
        # 일러스트 목록이 icons.json으로 바뀌었다
        assert "delivery-truck — 배송 차량" in t
        assert "beach · calendar · car" not in t


def test_components_list_kept_without_icons(tmp_path):
    out = make_out(tmp_path, icons=False)
    _, texts = run(out)
    full = pack.COMPONENTS.read_text(encoding="utf-8").rstrip()
    for t in texts.values():
        assert full in t


def test_spec_quotes_images_icons_per_screen(built):
    out, plan, texts = built
    inv = json.loads((out / "spec_inventory.json").read_text(encoding="utf-8"))
    slots = json.loads((out / "image_slots.json").read_text(encoding="utf-8"))
    icons = {i["slot"]: i["name"] for i in json.loads((out / "icons.json").read_text(encoding="utf-8")) if i.get("slot")}
    for a in plan["agents"]:
        t = texts[a["pack"]]
        own = set(a["screens"]) | {base(s) for s in a["screens"]}
        for sid in a["screens"]:
            for it in inv["items"]:
                if sid in (it.get("covered_by") or []) or it.get("target") == sid:
                    assert it["quote"] in t, (sid, it["id"])
        for sl in slots:
            mine = any(x in own for x in sl["screens"])
            if sl["kind"] == "photo":
                path = f"../assets/photos/{sl['slot']}.jpg"
                assert (path in t) == mine, (a["screens"], sl["slot"])
            elif sl["kind"] == "icon" and mine:
                assert f"`{icons[sl['slot']]}`" in t


def test_market_and_examples(built):
    _, plan, texts = built
    for a in plan["agents"]:
        t = texts[a["pack"]]
        assert "구조만 참고, 내용 베끼지 말 것" in t
        assert "[M2·" in t  # keep한 follow
        assert "[M1·" not in t  # cut한 follow
        assert "## 8. 셀프체크 규칙 요약" in t


def test_deterministic(tmp_path):
    out = make_out(tmp_path)
    _, t1 = run(out)
    b1 = {p: Path(p).read_bytes() for p in t1}
    plan1 = (out / "packs" / "plan.json").read_bytes()
    _, t2 = run(out)
    assert {p: Path(p).read_bytes() for p in t2} == b1
    assert (out / "packs" / "plan.json").read_bytes() == plan1


def test_mode_state(tmp_path):
    out = make_out(tmp_path)
    want = ["area-out--done", "order-cancel--done", "routine--done", "chat--done"]
    plan, texts = run(out, "--mode", "state", "--screens", ",".join(want))
    assert plan["mode"] == "state"
    assert sorted(s for a in plan["agents"] for s in a["screens"]) == sorted(want)
    for t in texts.values():
        assert "기본 화면 파일을 복사해 바뀐 부분만 고친다" in t


def test_mode_revise(tmp_path):
    out = make_out(tmp_path)
    want = ["home", "order-detail"]
    plan, texts = run(out, "--mode", "revise", "--screens", ",".join(want))
    assert plan["mode"] == "revise"
    assert sorted(s for a in plan["agents"] for s in a["screens"]) == sorted(want)
    principles = pack.PRINCIPLES.read_text(encoding="utf-8").rstrip()
    for a in plan["agents"]:
        t = texts[a["pack"]]
        assert "요청된 경로의 요소만, 요청만 반영" in t
        assert principles not in t
        for sid in a["screens"]:
            assert (out / "screens" / f"{sid}.html").resolve().as_posix() in t


def test_missing_optional_inputs(tmp_path):
    out = make_out(tmp_path)
    for f in ("icons.json", "conventions.json", "spec_inventory.json", "image_slots.json"):
        (out / f).unlink()
    plan, _ = run(out)
    assert sum(len(a["screens"]) for a in plan["agents"]) == len(screens(out))
