"""캔버스 모듈(modules/*.js) — Model·ViewModel 순수 함수 단위 테스트(node). 브라우저 없음.

graph.js · route.js · labels.js · style.js · camera.js · focus.js · prefs.js 를 순서대로 node 에서 읽어 확인한다.
D 는 runs/gym-v2/out 임시 복사본을 build_canvas.py 로 만든 index.html 의 hd-data 에서 꺼낸다.
"""
import colorsys, json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent
MOD = SCRIPTS / "modules"
REPO = SCRIPTS.parents[4]
GYM = REPO / "runs" / "gym-v2" / "out"
PURE = ["graph", "route", "labels", "style", "camera", "focus", "prefs"]
ALL_MODULES = ["graph", "route", "labels", "style", "camera", "focus", "prefs", "view-links", "view-motion"]
NODE = shutil.which("node")

HARNESS = r"""
const fs = require('fs'), vm = require('vm');
const [dir, names, inPath] = [process.argv[2], process.argv[3].split(','), process.argv[4]];
for (const n of names) vm.runInThisContext(fs.readFileSync(dir + '/' + n + '.js', 'utf8'), {filename: n + '.js'});
const HD = globalThis.HD, F = HD.focus, out = {};
const input = JSON.parse(fs.readFileSync(inPath, 'utf8'));

// 1. graph.fromData
const g = HD.graph.fromData(input.D);
out.flow = HD.graph.edgesFrom(g, null, 'flow').length;
out.flowKinds = [...new Set(g.edges.map(e => e.kind))];
out.screens = g.screens.length;
out.sameAsArrows = JSON.stringify(g.edges.map(e => [e.from, e.to, e.label])) === JSON.stringify((input.D.arrows || []).map(a => [a.from, a.to, a.label || '']));

// 2. addLinks 교체 · groupByTarget
const L1 = [{to: 'b', path: 'p1', text: 't1', rect: {x: 0, y: 0, w: 1, h: 1}}, {to: 'c', path: 'p2', text: 't2', rect: {x: 0, y: 5, w: 1, h: 1}}];
const L2 = [{to: 'c', path: 'q1', text: 'u1', rect: {x: 0, y: 0, w: 1, h: 1}}, {to: 'b', path: 'q2', text: 'u2', rect: {x: 0, y: 1, w: 1, h: 1}},
            {to: 'c', path: 'q3', text: 'u3', rect: {x: 0, y: 2, w: 1, h: 1}}];
let g2 = HD.graph.addLinks(g, 'a', L1);
g2 = HD.graph.addLinks(g2, 'a', L2);
g2 = HD.graph.addLinks(g2, 'z', L1);
const la = HD.graph.edgesFrom(g2, 'a', 'link');
out.linkCountA = la.length;
out.linkPathsA = la.map(e => e.via.path);
out.linkCountZ = HD.graph.edgesFrom(g2, 'z', 'link').length;
out.flowAfter = HD.graph.edgesFrom(g2, null, 'flow').length;
out.groups = HD.graph.groupByTarget(la).map(x => [x.to, x.k, x.edges.map(e => e.via.path)]);

// 3. focus.reduce 와 cycleNext
out.cycle = {};
for (const n of [1, 3, 5]) {
  const links = []; for (let i = 0; i < n; i++) links.push({to: 't' + i, path: 'p' + i, text: 'x' + i, rect: {x: 0, y: i, w: 1, h: 1}});
  const m = F.assignColors(links, '', F.LINK_COLORS); m.from = 'src';
  let s = F.reduce(F.reduce(F.initial(), {type: 'focus', id: 'src'}), {type: 'links', links: m});
  const got = [F.deriveView(m, s).stage], want = [F.deriveView(m, s).stage];
  let w = want[0];
  for (let i = 0; i < 2 * n + 3; i++) {
    s = F.reduce(s, {type: 'cycle'}); got.push(F.deriveView(m, s).stage);
    w = F.cycleNext(w, n); want.push(w);
  }
  out.cycle[n] = {got, want};
}
{
  const links = [0, 1, 2].map(i => ({to: 't' + i, path: 'p' + i, text: 'x' + i, rect: {x: 0, y: i, w: 1, h: 1}}));
  const m = F.assignColors(links, '', F.LINK_COLORS); m.from = 'src';
  let s = F.reduce(F.reduce(F.initial({preset: 'deep'}), {type: 'focus', id: 'src'}), {type: 'links', links: m});
  s = F.reduce(s, {type: 'cycle'});                       // 전체 → 그룹 1
  const t = F.reduce(s, {type: 'toggle', k: 0});
  out.toggle = {on: t.on, visible: F.deriveView(m, t).visible, before: F.deriveView(m, s).visible, hover: t.hover};
  const t2 = F.reduce(t, {type: 'cycle'});
  out.cycleClearsManual = t2.on === null;
  const h = F.reduce(t, {type: 'hover', k: 1});
  out.hoverSame = F.reduce(h, {type: 'hover', k: 1}) === h;
  const x = F.reduce(h, {type: 'exitFocus'});
  out.exit = {focusId: x.focusId, links: x.links, stage: x.stage, on: x.on, hover: x.hover, colors: x.colors, pair: x.pair};
  const i0 = F.initial(); out.cycleNoLinksSame = F.reduce(i0, {type: 'cycle'}) === i0;
  out.styleIntent = F.reduce(i0, {type: 'style', colors: {preset: 'vivid'}}).colors;
  // Ctrl+클릭(연결 보기 밖): pair → 링크 답이 오면 그 그룹 하나만
  const pr = F.reduce(F.reduce(F.initial(), {type: 'pair', id: 'src', to: 't1'}), {type: 'links', links: m});
  out.pair = {focusId: pr.focusId, on: pr.on, visible: F.deriveView(m, pr).visible};
}

// 3b. 순환(전체 먼저) · 모두 표시 · 범례 제목 · 같은 대상 합치기
{
  const links = [{to: 'a', path: 'p0', text: '뒤로', rect: {x: 8, y: 10, w: 40, h: 40}},
                 {to: 'b', path: 'p1', text: '일시정지 신청', rect: {x: 20, y: 300, w: 335, h: 48}},
                 {to: 'c', path: 'p2', text: '연장하기', rect: {x: 20, y: 500, w: 335, h: 48}},
                 {to: 'b', path: 'p3', text: '정지 문의', rect: {x: 20, y: 700, w: 335, h: 48}}];
  const m = F.assignColors(links, '', F.LINK_COLORS); m.from = 'src'; m.titles = {src: '회원권'};
  let s = F.reduce(F.reduce(F.initial(), {type: 'focus', id: 'src'}), {type: 'links', links: m});
  const seq = [];
  const snap = st => { const v = F.deriveView(m, st); return {stage: v.stage, vis: v.visible, title: v.legend.title, all: v.legend.all, rows: v.legend.rows.length}; };
  seq.push(snap(s));
  for (let i = 0; i < 5; i++) { s = F.reduce(s, {type: 'cycle'}); seq.push(snap(s)); }
  out.cycle3 = seq;
  out.groups4 = F.groupsOf(m).map(g => [g.to, g.items, g.text, g.tag]);
  const dup = F.assignColors(['반품 신청', '수리 신청', '수리 신청'].map((x, i) => ({to: 'r', path: 'q' + i, text: x, rect: {x: 0, y: i * 60, w: 300, h: 48}})), '', F.LINK_COLORS);
  out.dupTag = F.groupsOf(dup)[0].tag;
  let t = F.reduce(s, {type: 'toggle', k: 2});          // s = 단계 1(그룹 a 만) → c 도 켬
  out.manual = snap(t);
  out.allOff = snap(F.reduce(t, {type: 'all', on: false}));
  out.allOn = snap(F.reduce(t, {type: 'all', on: true}));
  out.manualThenCycle = snap(F.reduce(t, {type: 'cycle'}));
}
// 3c. 옆면 규칙 · 경로 계획 · 태그 자리
out.side = [0.25, 0.5, 0.8].map(f => [HD.route.sideOf(f * 375, 375, 'R'), HD.route.sideOf(f * 375, 375, 'L')]);
{
  const S = {x: 1000, y: 1000, w: 375, h: 812}, cap = {top: 855, bottom: 896};
  const T = (x, row, rowTop) => ({x, y: rowTop, w: 375, h: 812, rowTop, cap: {top: rowTop - 145, bottom: rowTop - 104}, row});
  const groups = [
    {k: 0, to: 'back', target: T(541, 1, 1000), sameRow: true, members: [{x: 1008, y: 1010, w: 40, h: 40}]},
    {k: 1, to: 'far', target: T(1918, 1, 1000), sameRow: true, members: [{x: 1020, y: 1300, w: 335, h: 48}, {x: 1020, y: 1700, w: 335, h: 48}]},
    {k: 2, to: 'near', target: T(1459, 1, 1000), sameRow: true, members: [{x: 1020, y: 1500, w: 335, h: 48}]},
    {k: 3, to: 'bell', target: T(82, 1, 1000), sameRow: true, members: [{x: 1330, y: 1010, w: 40, h: 40}]},
    {k: 4, to: 'up', target: T(1459, 0, 0), sameRow: false, members: [{x: 1030, y: 1100, w: 300, h: 40}]}];
  const pl = HD.route.plan({src: S, rowTop: 1000, cap, left: 300, groups});
  out.plan = pl.map(p => ({k: p.k, side: p.side, rev: p.rev, gx: p.gx, lane: p.lane, ly: p.ly, pts: p.pts, d: p.d, segs: p.laneSegs, laneX: p.laneX}));
  const verts = [];
  pl.forEach(p => p.verticals.forEach(v => verts.push({k: p.k, x: v.x, y0: v.y0, y1: v.y1})));
  out.verts = verts;
  out.tags = HD.labels.placeTags(pl.map(p => ({k: p.k, segs: p.laneSegs, w: 90, h: 27})), verts);
  out.tagFallback = HD.labels.placeTags([{k: 0, segs: [{a: 0, b: 40, y: 0}], w: 90, h: 27}], []);
}

// 4. prefs (v2: 색 프리셋 · 랜덤 · 쌍 색 · 굵기 · 움직임, v1 sat 는 버림)
const mk = o => k => (k in o ? o[k] : null);
const RS = ['#AA3344', '#33AA44', '#3344AA', '#AAAA33', '#33AAAA', '#AA33AA'];
out.prefs = {
  migrate: HD.prefs.load(mk({'hd-arrows': '0', 'hd-link-sat': '0.5'})),
  fresh: HD.prefs.load(mk({})),
  badJson: HD.prefs.load(mk({'hd-canvas-prefs': '{bad', 'hd-arrows': '0'})),
  v1: HD.prefs.load(mk({'hd-canvas-prefs': JSON.stringify({v: 1, arrows: false, sat: 1.1}), 'hd-arrows': '1'})),
  stored: HD.prefs.load(mk({'hd-canvas-prefs': JSON.stringify({v: 2, arrows: false, preset: 'random', rand: RS, custom: {'a>b': '#ABCDEF'}, width: 4.5, motion: false})})),
  badFields: HD.prefs.load(mk({'hd-canvas-prefs': JSON.stringify({v: 2, arrows: 'no', preset: 'random', rand: [1], custom: {x: '#ABCDEF', 'a>b': 'red', 'c>d': '#123456'}, width: 9, motion: 'x'})})),
  throws: HD.prefs.load(() => { throw new Error('denied'); }),
};
const writes = {};
HD.prefs.save({v: 1, arrows: false, sat: 0.5, width: 5}, (k, v) => { writes[k] = v; });
out.prefs.writes = writes;

// 5. 카메라 계획(S4)
{
  const C = HD.camera, T = {x: 2000, y: 100, w: 375, h: 812}, from = {x: 300, y: 400};
  const view = {w: 1200, h: 800, z: 0.5, tx: 10, ty: 20}, small = {w: 1200, h: 500, z: 0.9, tx: 0, ty: 0};
  const ease = C.parseEase('cubic-bezier(0.22, 1, 0.36, 1)');
  const fits = C.plan(from, T, view, {centre: 250, glide: 600});
  out.camera = {fits, big: C.plan(from, T, small, {centre: 250, glide: 600}), red: C.plan(from, T, view, {centre: 250, glide: 600, reduced: true}),
                mid: C.at(fits, 700, ease, view), end: C.at(fits, 1e6, ease, view), e: [ease(0), ease(0.25), ease(0.5), ease(1)], ms: [C.ms('250ms'), C.ms('0.6s'), C.ms('x', 9)]};
}
// 6. 선 색(S5): 쌍 색 > 프리셋 · 강조색 건너뛰기(프리셋마다) · 랜덤(시드 RNG)
{
  const S = HD.lineStyle;
  let seed = 7; const rng = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  const rs = S.randomSet(rng), rs2 = S.randomSet(rng);
  const pc = {preset: 'deep', rand: null, custom: {'a>b': '#123456'}};
  out.colour = {custom: S.colourOf(pc, 'a', {to: 'b', k: 0}, ''), preset: S.colourOf(pc, 'a', {to: 'c', k: 1}, ''), otherSrc: S.colourOf(pc, 'x', {to: 'b', k: 0}, ''),
                deep: S.PRESETS.deep.c, rand: rs, rand2: rs2, skip: {}};
  for (const k of ['calm', 'vivid', 'pastel', 'deep', 'random']) {
    const p = {preset: k, rand: rs, custom: {}}, acc = S.paletteOf(p)[0];
    out.colour.skip[k] = {acc, cols: [0, 1, 2, 3, 4, 5, 6, 7].map(i => S.colourOf(p, 's', {to: 't' + i, k: i}, acc))};
  }
}
console.log(JSON.stringify(out));
"""


def gym_data():
    tmp = Path(tempfile.mkdtemp(prefix="hd-canvas-mod-"))
    try:
        out = tmp / "out"
        shutil.copytree(GYM, out)
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        r = subprocess.run([sys.executable, str(SCRIPTS / "build_canvas.py"), str(out)], capture_output=True, text=True, encoding="utf-8", env=env)
        assert r.returncode == 0, r.stderr
        html = (out / "index.html").read_text(encoding="utf-8")
        m = re.search(r'<script id="hd-data" type="application/json">(.*?)</script>', html, re.S)
        assert m, "hd-data 없음"
        D = json.loads(m.group(1).replace("<\\!--", "<!--"))
        screens = json.loads((out / "screens.json").read_text(encoding="utf-8"))
        assert "<!-- hd-modules -->" not in html and "data-hd-module=\"view-links\"" in html
        return D, screens, html
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture(scope="module")
def res():
    if not NODE:
        pytest.skip("node 가 PATH 에 없음 — modules/*.js 단위 테스트는 node 로 돌린다")
    if not GYM.exists():
        pytest.skip(f"fixture 없음: {GYM}")
    D, screens, html = gym_data()
    tmp = Path(tempfile.mkdtemp(prefix="hd-canvas-mod-js-"))
    try:
        (tmp / "h.js").write_text(HARNESS, encoding="utf-8")
        (tmp / "in.json").write_text(json.dumps({"D": D}, ensure_ascii=False), encoding="utf-8")
        r = subprocess.run([NODE, str(tmp / "h.js"), str(MOD), ",".join(PURE), str(tmp / "in.json")], capture_output=True, text=True, encoding="utf-8")
        assert r.returncode == 0, r.stderr
        out = json.loads(r.stdout)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    out["_branches"] = sum(len(s.get("branches") or []) for s in screens["screens"])
    out["_html"] = html
    return out


def test_graph_from_data(res):
    assert res["flow"] == res["_branches"] == 9
    assert res["flowKinds"] == ["flow"] and res["sameAsArrows"]
    assert res["screens"] == 28


def test_add_links_replaces_and_groups(res):
    assert res["linkCountA"] == 3 and res["linkPathsA"] == ["q1", "q2", "q3"]   # 두 번째 답이 첫 답을 바꿔 낌
    assert res["linkCountZ"] == 2 and res["flowAfter"] == 9
    assert res["groups"] == [["c", 0, ["q1", "q3"]], ["b", 1, ["q2"]]]


def test_focus_reducer(res):
    for n in ("1", "3", "5"):
        assert res["cycle"][n]["got"] == res["cycle"][n]["want"], n
    assert res["cycle"]["3"]["got"][:6] == [0, 1, 2, 3, 0, 1]          # v3: Shift+클릭 = 전체 먼저, 다시 누르면 하나씩 → 전체
    assert res["cycle"]["1"]["got"] == [0] * len(res["cycle"]["1"]["got"])
    t = res["toggle"]
    assert t["before"] == [True, False, False]
    assert t["on"] == {"0": False, "1": False, "2": False} and t["visible"] == [False, False, False] and t["hover"] is None
    assert res["cycleClearsManual"] and res["hoverSame"] and res["cycleNoLinksSame"]
    assert res["exit"] == {"focusId": None, "links": None, "stage": 0, "on": None, "hover": None, "colors": {"preset": "deep"}, "pair": None}
    assert res["styleIntent"] == {"preset": "vivid"}
    assert res["pair"] == {"focusId": "src", "on": {"0": False, "1": True, "2": False}, "visible": [False, True, False]}   # Ctrl+클릭 쌍 하나만


DEF = {"v": 2, "arrows": True, "preset": "calm", "rand": None, "custom": {}, "width": 2.5, "motion": True}


def test_prefs(res):
    p = res["prefs"]
    assert p["migrate"] == dict(DEF, arrows=False)                                   # 예전 키(hd-link-sat 는 버림)
    assert p["fresh"] == DEF and p["throws"] == DEF
    assert p["badJson"] == dict(DEF, arrows=False)
    assert p["v1"] == dict(DEF, arrows=False)                                        # v1 → v2: sat 버림
    assert p["stored"] == {"v": 2, "arrows": False, "preset": "random", "rand": ["#AA3344", "#33AA44", "#3344AA", "#AAAA33", "#33AAAA", "#AA33AA"],
                           "custom": {"a>b": "#ABCDEF"}, "width": 4.5, "motion": False}
    assert p["badFields"] == dict(DEF, custom={"c>d": "#123456"})                     # 틀린 값은 기본값(랜덤인데 rand 없음 → 차분)
    assert list(p["writes"]) == ["hd-canvas-prefs"] and json.loads(p["writes"]["hd-canvas-prefs"]) == dict(DEF, arrows=False, width=5)


def test_camera_plan(res):
    """S4: 키프레임 시간은 늘 커지고, 끝은 정확히 대상 카드 가운데. 대상이 들어가면 배율 그대로, 안 들어가면 그만큼만 축소. reduced → 하나."""
    c = res["camera"]
    T = (2000 + 375 / 2, 100 + 812 / 2)
    for keys, vw, vh in ((c["fits"], 1200, 800), (c["big"], 1200, 500)):
        ts = [k["t"] for k in keys]
        assert ts == sorted(ts) and len(set(ts)) == len(ts) and ts[0] == 0 and ts[-1] == 850, ts
        e = keys[-1]
        assert abs(T[0] * e["z"] + e["tx"] - vw / 2) < 1e-6 and abs(T[1] * e["z"] + e["ty"] - vh / 2) < 1e-6, e
        m = keys[1]                                                                 # 1단계: 출발 요소를 가운데(배율 그대로)
        assert abs(300 * m["z"] + m["tx"] - vw / 2) < 1e-6 and abs(400 * m["z"] + m["ty"] - vh / 2) < 1e-6 and m["z"] == keys[0]["z"]
    assert all(k["z"] == 0.5 for k in c["fits"])                                     # 들어감 → 배율 그대로
    assert abs(c["big"][-1]["z"] - (500 - 48) / 812) < 1e-9 and c["big"][0]["z"] == 0.9   # 안 들어감 → 들어갈 만큼만 축소
    assert len(c["red"]) == 1 and c["red"][0] == dict(c["fits"][-1], t=0)
    assert c["end"] == {k: c["fits"][-1][k] for k in ("z", "tx", "ty")}
    assert c["e"][0] == 0 and c["e"][3] == 1 and 0.5 < c["e"][1] < c["e"][2] < 1    # smooth-out: 앞에서 빠르게
    assert c["ms"] == [250, 600, 9]


def _hue(hx):
    r, g, b = (int(hx[i:i + 2], 16) / 255 for i in (1, 3, 5))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return h * 360, s, l


def test_line_colours(res):
    """S5: colourOf 우선순위 custom > preset · 모든 프리셋(랜덤 포함)에서 강조색 ±30° 건너뜀 · randomSet(시드) 6–8 개 다른 색상각 · 채도/밝기 범위."""
    c = res["colour"]
    assert c["custom"] == "#123456" and c["preset"] == c["deep"][1] and c["otherSrc"] == c["deep"][0]
    for k, v in c["skip"].items():
        ah = _hue(v["acc"])[0]
        for col in v["cols"]:
            gap = abs(_hue(col)[0] - ah) % 360
            assert min(gap, 360 - gap) >= 30, (k, v["acc"], col)
    for rs in (c["rand"], c["rand2"]):
        assert 6 <= len(rs) <= 8 and len(set(rs)) == len(rs)
        hs = [_hue(x) for x in rs]
        assert len({round(h) for h, _, _ in hs}) == len(rs)
        for h, s, l in hs:
            assert 0.33 <= s <= 0.47 and 0.41 <= l <= 0.51, (h, s, l)
    assert c["rand"] != c["rand2"]


FORBIDDEN = re.compile(r"\bdocument\b|\bwindow\.|querySelector|\.style\b|localStorage|postMessage")


@pytest.mark.parametrize("name", PURE)
def test_purity(name):
    src = (MOD / f"{name}.js").read_text(encoding="utf-8")
    assert "globalThis.HD = globalThis.HD || {}" in src
    hits = FORBIDDEN.findall(src)
    assert not hits, f"{name}.js: {hits}"


def test_single_file_output(res):
    html = res["_html"]
    for n in ALL_MODULES:
        assert f'data-hd-module="{n}"' in html
    order = [html.index(f'data-hd-module="{n}"') for n in ALL_MODULES]
    assert order == sorted(order) and order[-1] < html.index("// ── Canvas shell")
    assert "/* hd-motion */" not in html and "--duration-fast: 250ms" in html and html.index("--camera-glide-dur") < html.index("</style>")   # motion.css 인라인
    assert not re.search(r"<script[^>]+\bsrc=", html), "외부 스크립트 참조 없음"


def test_cycle_all_first_and_legend(res):
    """S1: 첫 Shift+클릭 = 전체(그룹 n개), 다시 = 1 … n → 전체. 제목 · 모두 표시 체크 상태."""
    seq = res["cycle3"]
    assert [x["stage"] for x in seq] == [0, 1, 2, 3, 0, 1]
    assert seq[0]["title"] == "회원권 · 전체 3개" and seq[0]["all"] == "on" and seq[0]["vis"] == [True, True, True]
    assert seq[1]["title"] == "회원권 · 1/3 뒤로" and seq[1]["vis"] == [True, False, False] and seq[1]["all"] == "mixed"
    assert seq[2]["title"] == "회원권 · 2/3 일시정지 신청 · 정지 문의"
    assert seq[3]["title"] == "회원권 · 3/3 연장하기"
    assert all(x["rows"] == 3 for x in seq)                          # 범례 줄 = 대상 그룹 하나에 한 줄
    assert res["manual"]["title"] == "회원권 · 직접 선택 2/3" and res["manual"]["vis"] == [True, False, True] and res["manual"]["all"] == "mixed"
    assert res["allOff"]["vis"] == [False] * 3 and res["allOff"]["all"] == "off" and res["allOff"]["title"] == "회원권 · 직접 선택 0/3"
    assert res["allOn"]["vis"] == [True] * 3 and res["allOn"]["all"] == "on"
    assert res["manualThenCycle"]["title"] == "회원권 · 2/3 일시정지 신청 · 정지 문의"   # 수동 선택은 다음 Shift+클릭까지만


def test_same_target_merge(res):
    g = res["groups4"]
    assert [x[0] for x in g] == ["a", "b", "c"] and g[1][1] == [1, 3]
    assert g[1][2] == "일시정지 신청 · 정지 문의 (2)" and g[1][3] == "일시정지 신청 · 정지 문의 (2)"
    assert g[0][2] == "뒤로"
    assert res["dupTag"] == "반품 신청 · 수리 신청 (3)"   # 같은 글 버튼 여럿 → 글은 한 번, 개수는 (n)


def test_side_rule(res):
    assert res["side"] == [["L", "L"], ["R", "L"], ["R", "R"]]       # 25% → 왼쪽 · 50% → 대상 쪽 · 80% → 오른쪽


def segs_of(pts):
    return [(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]


def collinear_overlap(s1, s2):
    (a, b), (c, d) = s1, s2
    if a[1] == b[1] == c[1] == d[1]:
        lo, hi = max(min(a[0], b[0]), min(c[0], d[0])), min(max(a[0], b[0]), max(c[0], d[0]))
        return max(0, hi - lo)
    if a[0] == b[0] == c[0] == d[0]:
        lo, hi = max(min(a[1], b[1]), min(c[1], d[1])), min(max(a[1], b[1]), max(c[1], d[1]))
        return max(0, hi - lo)
    return 0


def test_plan_routes(res):
    P = {p["k"]: p for p in res["plan"]}
    back, far, near, bell, up = P[0], P[1], P[2], P[3], P[4]
    assert back["side"] == "L" and back["pts"][0][0][0] == 1008 and back["pts"][0][1][0] < 1000   # 왼쪽 위 뒤로: 왼쪽 옆면으로 나감
    assert near["side"] == far["side"] == "R" and not near["rev"]
    assert near["gx"] == 1375 + 38 and far["gx"] == 1375 + 26                      # 가까운 대상 = 바깥 통로
    assert bell["side"] == "R" and bell["rev"] and bell["gx"] == 1375 + 14          # 반대 방향 = 가장 안쪽
    assert near["lane"] == 0 and far["lane"] == 1
    assert bell["lane"] > max(P[k]["lane"] for k in (0, 1, 2))                      # 반대 방향 = 겹치는 것들 위
    assert up["laneX"] < min(p["gx"] for p in res["plan"]) and len(up["segs"]) == 2
    for p in res["plan"]:
        for pts in p["pts"]:
            for (a, b) in segs_of(pts):
                assert a[0] == b[0] or a[1] == b[1], ("가로·세로만", p["k"], pts)
            corners = len(pts) - 2
            assert corners <= (5 if p["k"] == 4 else 3), (p["k"], pts)
        for d in p["d"]:
            assert set(re.findall(r"[A-Z]", d)) <= {"M", "L", "Q"}
    for p in res["plan"]:                                                          # 서로 다른 그룹은 20px 넘게 겹치지 않는다
        for q in res["plan"]:
            if p["k"] >= q["k"]:
                continue
            for s1 in (s for pts in p["pts"] for s in segs_of(pts)):
                for s2 in (s for pts in q["pts"] for s in segs_of(pts)):
                    assert collinear_overlap(s1, s2) <= 20, (p["k"], q["k"], s1, s2)


def test_place_tags(res):
    tags, P = res["tags"], {p["k"]: p for p in res["plan"]}
    W, H = 90 + 8, 27 + 8
    for t in tags:
        assert not t["fallback"], t
        seg = [s for s in P[t["k"]]["segs"] if abs(s["y"] - t["y"]) < 0.01][0]
        assert seg["a"] + 10 + 45 <= t["x"] + 1e-6 and t["x"] + 45 <= seg["b"] - 10 + 1e-6, (t, seg)
        for v in res["verts"]:
            if v["k"] == t["k"]:
                continue
            assert not (v["x"] - 3 < t["x"] + W / 2 and t["x"] - W / 2 < v["x"] + 3 and min(v["y0"], v["y1"]) < t["y"] + H / 2 and t["y"] - H / 2 < max(v["y0"], v["y1"])), (t, v)
    for i, a in enumerate(tags):
        for b in tags[i + 1:]:
            assert not (abs(a["x"] - b["x"]) < W and abs(a["y"] - b["y"]) < H), (a, b)
    fb = res["tagFallback"][0]
    assert fb["fallback"] and fb["x"] == 20                                         # 자리가 없으면 50%
