// 스키마 — 정본 자체 검사(규칙 연결 · 관계 범위 · 생성 단계 · 읽는 곳 · docs 최신)와 고정 입력 검사가 통과하고,
// 일부러 틀린 입력은 잡는다(형식 · 범위 관계 · 하나뿐 칸 · 조건 필수 · 화면 사이 규칙). 옛 칸 · 옛 값 · 권장 칸 없음은 경고만.
const fs = require("fs");
const path = require("path");
const { run, workCopy, suite } = require("../lib.js");

const t = suite("20 스키마");

const self = run("schema.js");
if (self.code === 0) t.ok("정본 자체 검사 (node scripts/schema.js)"); else t.fail(`정본 자체 검사\n${self.out}`);

const sample = run("schema.js", "test/fixtures/sample");
if (sample.code === 0 && !/경고/.test(sample.out)) t.ok("고정 입력 — 오류 0 · 경고 0 (새 형식)");
else t.fail(`고정 입력은 새 형식이라 오류 · 경고가 없어야 함\n${sample.out}`);

// 기준 문서(README) 7절 예시 — screens.json · flow.json 블록이 오류 · 경고 없이 통과한다
{
  const readme = fs.readFileSync(path.join(__dirname, "..", "..", "packages", "core", "schema", "README.md"), "utf8");
  const block = (name) => { const m = readme.match(new RegExp("### " + name.replace(".", "\\.") + "\\s+```json\\n([\\s\\S]*?)\\n```")); return m && m[1]; };
  const ex = workCopy();
  try {
    for (const f of ["screens.json", "flow.json"]) { const b = block(f); if (b) fs.writeFileSync(path.join(ex.run, f), b); else t.fail(`README 예시 ${f} 블록을 찾지 못함`); }
    const r = run("schema.js", ex.run);
    if (r.code === 0 && !/경고/.test(r.out)) t.ok("README 예시 — 오류 0 · 경고 0"); else t.fail(`README 예시\n${r.out}`);
  } finally {
    ex.done();
  }
}

// 고정 입력을 고쳐서 돌린다: change(screens, flow)가 두 파일을 고친다. want = 0(통과) | 1(실패), see = 출력에 있어야 할 말
const SCREENS = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "fixtures", "sample", "screens.json"), "utf8"));
const FLOW = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "fixtures", "sample", "flow.json"), "utf8"));
const scr = (S, slug) => S.screens.find((s) => s.slug === slug);
const cases = [
  ["없는 칸 → 실패", 1, "스키마에 없는 항목", (S) => { scr(S, "home").content = "실험 칸"; }],
  ["옛 칸(purpose) → 경고만", 0, "옛 칸", (S) => { scr(S, "home").purpose = "오늘 할 일을 본다"; }],
  ["옛 값(pattern 영문) → 경고만", 0, "옛 값", (S) => { scr(S, "home").pattern = "dashboard"; }],
  ["옛 값(motion target) → 경고만", 0, "옛 칸", (S) => { scr(S, "home").motion = [{ type: "reorder", target: "recent", note: "끌어서 순서를 바꿔요" }]; }],
  ["권장 칸 없음(goal) → 경고만", 0, "권장 칸 없음", (S) => { delete scr(S, "home").goal; }],
  ["값 목록 밖(cases tone) → 실패", 1, "danger|warning|info|success", (S) => { scr(S, "create").cases[0].tone = "red"; }],
  ["범위 screen — focus가 다른 화면의 영역 → 실패", 1, "region.key (screen 안)", (S) => { scr(S, "home").focus = "item-form"; }],
  ["범위 screen — motion.region이 다른 화면의 영역 → 실패", 1, "region.key (screen 안)", (S) => { scr(S, "home").motion[0].region = "result"; }],
  ["범위 from — 흐름 단계 region이 출발 화면에 없음 → 실패", 1, "region.key (from 안)", (S, F) => { F.flows[0].steps[1].region = "summary"; }],
  ["범위 theme — toggles.swatch가 분위기에 없음 → 실패", 1, "look.swatches.id (theme 안)", (S) => { S.toggles.swatch = "nope"; }],
  ["범위 theme — toggles.swatch brand(대표색) → 통과", 0, null, (S) => { S.toggles.swatch = "brand"; }],
  ["범위 role — 다른 역할 화면의 변형 → 실패", 1, "screen.slug (role 안)", (S) => {
    S.roles.push({ key: "member", label: "구성원", goal: "모임 소식을 본다", inclusion: "휴대폰", nav: [] });
    Object.assign(scr(S, "done"), { role: "member" });
  }],
  ["관계 doc — section이 sections에 없음 → 실패", 1, "section.key", (S) => { scr(S, "home").section = "nowhere"; }],
  ["하나뿐(screen) — 같은 화면에 영역 key 두 번 → 실패", 1, "같은 화면 안에서 하나뿐", (S) => { const h = scr(S, "home"); h.regions.push({ ...h.regions[1] }); }],
  ["하나뿐(doc) — 화면 slug 두 번 → 실패", 1, "문서 전체 안에서 하나뿐", (S) => { S.screens.push({ ...scr(S, "create-error") }); }],
  ["조건 필수 — 오류 화면에 variantOf 없음 → 실패", 1, "variantOf: 필수 항목 없음", (S) => { delete scr(S, "create-error").variantOf; }],
  ["조건 필수 — reorder에 region 없음 → 실패", 1, "허용 형식 중 어느 것과도 맞지 않음", (S) => { scr(S, "home").motion = [{ type: "reorder", note: "끌어서 순서를 바꿔요" }]; }],
  ["조건 필수 — hold에 trigger 있음 → 통과", 0, null, (S) => { scr(S, "home").motion = [{ type: "hold", trigger: "create", ms: 2000, note: "길게 누르면 만들어요" }]; }],
  ["플랫폼별 메뉴 틀 — mobile에 sidebar → 실패", 1, "tabbar|top|none", (S) => {
    S.platform = "mobile";
    S.concepts = [{ id: "a", name: "오늘 할 일부터 보기", why: "열자마자 할 일이 보여요", shell: "sidebar", home: "오늘 요약 + 최근 변경", density: "normal", look: "warm", traits: ["숫자 하나가 크게"], refs: [], screens: ["home"] }];
  }],
  ["플랫폼별 메뉴 틀 — web 화면에 tabbar → 실패", 1, "sidebar|top|rail|none", (S) => { scr(S, "home").shell = "tabbar"; }],
  ["플랫폼별 메뉴 틀 — mobile 화면에 sidebar → 실패", 1, "tabbar|top|none", (S) => { S.platform = "mobile"; scr(S, "home").shell = "sidebar"; }],
  ["플랫폼별 메뉴 틀 — 화면 하나만 none은 web · mobile 모두 → 통과", 0, null, (S) => { scr(S, "create").shell = "none"; }],
  // 옛 칸이 있어도 관계 오류는 오류 — 경고로 내리는 것은 x-ref warnWith에 적힌 옛 칸이 함께 있을 때만
  ...[["role", "nobody", "role.key"], ["section", "nowhere", "section.key"], ["focus", "item-form", "region.key (screen 안)"], ["variantOf", "nowhere", "screen.slug (role 안)"]].map(([k, v, see]) =>
    [`옛 칸 purpose가 있는 화면에서 ${k}가 틀림 → 실패`, 1, see, (S) => { Object.assign(scr(S, "home"), { purpose: "오늘 할 일을 본다", [k]: v }); }]),
  ["옛 칸 fetched가 있는 무드보드 항목의 look이 틀림 → 실패", 1, "look.id", (S) => {
    S.mood.board = [{ id: "m1", name: "동네 책방", url: "https://example.com", fetched: true, take: "color", what: "종이 같은 바탕", keyword: "포근한", look: "nope" }];
  }],
  ["warnWith — url을 복사한 옛 시안 refs의 이름이 references에 없음 → 경고만", 0, "옛 칸 url이 함께 있어 경고", (S) => {
    S.concepts = [{ id: "a", name: "오늘 할 일부터 보기", why: "열자마자 할 일이 보여요", shell: "sidebar", home: "오늘 요약 + 최근 변경", density: "normal", look: "warm", traits: ["숫자 하나가 크게"], refs: [{ name: "없는 곳", url: "https://example.com", borrow: "요약 숫자" }], screens: ["home"] }];
  }],
  ["warnWith 없음 — url 없는 시안 refs의 이름이 references에 없음 → 실패", 1, "reference.name", (S) => {
    S.concepts = [{ id: "a", name: "오늘 할 일부터 보기", why: "열자마자 할 일이 보여요", shell: "sidebar", home: "오늘 요약 + 최근 변경", density: "normal", look: "warm", traits: ["숫자 하나가 크게"], refs: [{ name: "없는 곳", borrow: "요약 숫자" }], screens: ["home"] }];
  }],
  ["warnWith — target이 함께 있는 움직임의 region이 다른 화면 영역 → 경고만", 0, "옛 칸 target이 함께 있어 경고", (S) => { scr(S, "home").motion = [{ type: "countup", region: "result", target: "summary", note: "숫자가 올라가요" }]; }],
  ["state-pair — 오류 · 완료가 아닌 화면에 when → 경고", 0, "state가 error · success인 화면에만", (S) => { scr(S, "home").when = "처음 열었을 때"; }],
  ["board-ask — 질문 4개 → 실패", 1, "항목 3개 이하", (S) => { S.board.ask = [0, 1, 2, 3].map((i) => ({ id: `q${i}`, text: "어떻게 둘까요?", options: ["가 (추천)", "나"], recommended: 0 })); }],
  ["규칙 variant-target — 자기 자신의 변형 → 실패", 1, "variant-target", (S) => { scr(S, "done").variantOf = "done"; }],
  ["규칙 overlay-reached — 아무도 열지 않는 뜨는 창 → 실패", 1, "overlay-reached", (S) => {
    S.screens.push({ slug: "confirm-dialog", name: "지우기 확인 창", role: "owner", overlayOf: "home", regions: [{ key: "confirm", label: "지울까요" }] });
  }],
  ["규칙 split-when — 같은 화면 · 버튼이 두 번인데 when 없음 → 실패", 1, "split-when", (S, F) => {
    F.branches.push({ from: "create", region: "item-form", trigger: "save", action: "'만들기'를 누르면", to: "create-error" });
  }],
  ["규칙 split-when — 둘 다 when → 통과", 0, null, (S, F) => {
    F.flows[0].steps[1].when = "이름을 적었으면";
    F.branches.push({ from: "create", region: "item-form", trigger: "save", action: "'만들기'를 누르면", to: "create-error", when: "이름이 비었으면" });
  }],
];

const w = workCopy();
try {
  for (const [label, want, see, change] of cases) {
    const S = JSON.parse(JSON.stringify(SCREENS)), F = JSON.parse(JSON.stringify(FLOW));
    change(S, F);
    fs.writeFileSync(path.join(w.run, "screens.json"), JSON.stringify(S, null, 2));
    fs.writeFileSync(path.join(w.run, "flow.json"), JSON.stringify(F, null, 2));
    const r = run("schema.js", w.run);
    const code = r.code === 0 ? 0 : 1;
    if (code === want && (!see || r.out.includes(see))) t.ok(label);
    else t.fail(`${label} — exit ${r.code}${see ? `, '${see}' ${r.out.includes(see) ? "있음" : "없음"}` : ""}\n${r.out.split("\n").slice(0, 12).join("\n")}`);
  }
} finally {
  w.done();
}
t.end();
