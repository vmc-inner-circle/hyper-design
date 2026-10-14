// 스키마 — 정본 자체 검사(규칙 연결 · 관계 범위 · 생성 단계 · 읽는 곳 · docs 최신)와 고정 입력 검사가 통과하고,
// 일부러 틀린 입력은 잡는다(형식 · 범위 관계 · 하나뿐 칸 · 조건 필수 · 화면 사이 규칙). 옛 칸 · 옛 값은 받지 않고, 새 칸이 빠져도 실패한다.
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
const CONCEPT = { id: "a", name: "오늘 할 일부터 보기", why: "열자마자 할 일이 보여요", shell: "sidebar", home: "오늘 요약 + 최근 변경", density: "normal", look: "warm", traits: ["숫자 하나가 크게"], refs: [], screens: ["home"] };
const REF = { name: "동네 책방 앱", url: "https://example.com", borrow: "요약 숫자", layout: { nav: "왼쪽 메뉴", home: "위에 숫자 하나, 아래 목록", density: "보통", signature: "큰 숫자 카드" } };
const cases = [
  ["없는 칸 → 실패", 1, "스키마에 없는 항목", (S) => { scr(S, "home").content = "실험 칸"; }],
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
  ["조건 필수 — reorder에 region 없음 → 실패", 1, "motion[0].region: 필수 항목 없음", (S) => { scr(S, "home").motion = [{ type: "reorder", note: "끌어서 순서를 바꿔요" }]; }],
  ["조건 필수 — hold에 trigger 있음 → 통과", 0, null, (S) => { scr(S, "home").motion = [{ type: "hold", trigger: "create", ms: 2000, note: "길게 누르면 만들어요" }]; }],
  ["플랫폼별 메뉴 틀 — mobile에 sidebar → 실패", 1, "tabbar|top|none", (S) => {
    S.platform = "mobile";
    S.concepts = [{ ...CONCEPT, shell: "sidebar" }];
  }],
  ["플랫폼별 메뉴 틀 — web 화면에 tabbar → 실패", 1, "sidebar|top|rail|none", (S) => { scr(S, "home").shell = "tabbar"; }],
  ["플랫폼별 메뉴 틀 — mobile 화면에 sidebar → 실패", 1, "tabbar|top|none", (S) => { S.platform = "mobile"; scr(S, "home").shell = "sidebar"; }],
  ["플랫폼별 메뉴 틀 — 화면 하나만 none은 web · mobile 모두 → 통과", 0, null, (S) => { scr(S, "create").shell = "none"; }],
  ["관계 doc — role이 roles에 없음 → 실패", 1, "role.key", (S) => { scr(S, "home").role = "nobody"; }],
  ["관계 role — variantOf가 없는 화면 → 실패", 1, "screen.slug (role 안)", (S) => { scr(S, "done").variantOf = "nowhere"; }],
  ["관계 doc — 무드보드 항목의 look이 looks에 없음 → 실패", 1, "look.id", (S) => {
    S.mood.board = [{ id: "m1", name: "동네 책방", url: "https://example.com", take: "color", what: "종이 같은 바탕", keyword: "포근한", look: "nope" }];
  }],
  ["관계 doc — 시안 refs의 이름이 references에 없음 → 실패", 1, "reference.name", (S) => {
    S.concepts = [{ ...CONCEPT, refs: [{ name: "없는 곳", borrow: "요약 숫자" }] }];
  }],
  ["관계 doc — 기준어 from이 역할 · 사실 이름표가 아님 → 실패", 1, "role.key 또는 facts.key", (S) => { S.mood.keywords[0].from = ["d1"]; }],
  ["state-pair — 오류 · 완료가 아닌 화면에 when → 경고", 0, "state가 error · success인 화면에만", (S) => { scr(S, "home").when = "처음 열었을 때"; }],
  ["board-ask — 질문 4개 → 실패", 1, "항목 3개 이하", (S) => { S.board.ask = [0, 1, 2, 3].map((i) => ({ id: `q${i}`, text: "어떻게 둘까요?", options: ["가 (추천)", "나"], recommended: 0 })); }],
  ["규칙 variant-target — 자기 자신의 변형 → 실패", 1, "variant-target", (S) => { scr(S, "done").variantOf = "done"; }],
  ["규칙 overlay-reached — 아무도 열지 않는 뜨는 창 → 실패", 1, "overlay-reached", (S) => {
    S.screens.push({ ...scr(S, "home"), slug: "confirm-dialog", name: "지우기 확인 창", overlayOf: "home" });
  }],
  ["규칙 split-when — 같은 화면 · 버튼이 두 번인데 when 없음 → 실패", 1, "split-when", (S, F) => {
    F.branches.push({ from: "create", region: "item-form", trigger: "save", action: "'만들기'를 누르면", to: "create-error" });
  }],
  ["규칙 split-when — 둘 다 when → 통과", 0, null, (S, F) => {
    F.flows[0].steps[1].when = "이름을 적었으면";
    F.branches.push({ from: "create", region: "item-form", trigger: "save", action: "'만들기'를 누르면", to: "create-error", when: "이름이 비었으면" });
  }],
  ["새 형식 시안 · 레퍼런스(refs는 이름만) → 통과", 0, null, (S) => { S.references = [REF]; S.concepts = [{ ...CONCEPT, refs: [{ name: REF.name, borrow: "요약 숫자" }] }]; }],
  // 옛 칸 · 옛 객체 — 이제 정본에 없다
  ...[
    ["최상위 purpose", "$.purpose", (S) => { S.purpose = { domain: [] }; }],
    ["최상위 shell", "$.shell", (S) => { S.shell = "sidebar"; }],
    ["화면 purpose", ".purpose", (S) => { scr(S, "home").purpose = "오늘 할 일을 본다"; }],
    ["화면 scene", ".scene", (S) => { scr(S, "home").scene = "관리자로서 오늘 할 일을 본다"; }],
    ["역할 frequency", "$.roles[0].frequency", (S) => { S.roles[0].frequency = "하루 한두 번"; }],
    ["영역 prd", ".regions[0].prd", (S) => { scr(S, "home").regions[0].prd = "PRD 2절"; }],
    ["움직임 target", ".motion[0].target", (S) => { scr(S, "home").motion = [{ type: "countup", target: "summary", note: "숫자가 올라가요" }]; }],
    ["분위기 refs", "$.looks[0].refs", (S) => { S.looks[0].refs = []; }],
    ["분위기 type.font", "$.looks[0].type.font", (S) => { S.looks[0].type.font = "pretendard"; }],
    ["시안 lean", "$.concepts[0].lean", (S) => { S.concepts = [{ ...CONCEPT, lean: "warm" }]; }],
    ["시안 refs[].url", "$.concepts[0].refs[0].url", (S) => { S.references = [REF]; S.concepts = [{ ...CONCEPT, refs: [{ name: REF.name, url: REF.url, borrow: "요약 숫자" }] }]; }],
    ["레퍼런스 kind", "$.references[0].kind", (S) => { S.references = [{ ...REF, kind: "app" }]; }],
    ["무드보드 항목 fetched", "$.mood.board[0].fetched", (S) => { S.mood.board = [{ id: "m1", name: "동네 책방", url: "https://example.com", fetched: true, take: "color", what: "종이 같은 바탕", keyword: "포근한", look: "warm" }]; }],
    ["toggles.accent", "$.toggles.accent", (S) => { S.toggles.accent = "terracotta"; }],
    ["board.recommend.accent", "$.board.recommend.accent", (S) => { S.board.recommend.accent = "terracotta"; }],
  ].map(([what, at, change]) => [`옛 칸 ${what} → 실패`, 1, `${at}: 스키마에 없는 항목`, change]),
  // 옛 값 · 옛 모양
  ["옛 값 pattern 영문(dashboard) → 실패", 1, "중 하나여야 함", (S) => { scr(S, "home").pattern = "dashboard"; }],
  ["옛 값 시안 density 한국어(보통) → 실패", 1, "허용 형식 중 어느 것과도 맞지 않음", (S) => { S.concepts = [{ ...CONCEPT, density: "보통" }]; }],
  ["옛 값 board.locked 'toggles' → 실패", 1, "중 하나여야 함", (S) => { S.board.locked = ["toggles"]; }],
  ["옛 값 질문 recommended 문자열 → 실패", 1, "integer 이어야 함", (S) => { S.board.ask = [{ id: "q1", text: "어떻게 둘까요?", options: ["가 (추천)", "나"], recommended: "가 (추천)" }]; }],
  ["옛 모양 facts 배열 → 실패", 1, "object 이어야 함", (S) => { S.facts = ["우유 6팩 남음"]; }],
  ["옛 모양 data 문장 → 실패", 1, "array 이어야 함", (S) => { scr(S, "home").data = "오늘 할 일 목록"; }],
  ["옛 모양 defer 문장 → 실패", 1, "array 이어야 함", (S) => { scr(S, "home").defer = "지난 기록은 나중에"; }],
  // 새 칸은 필수
  ...[
    ["sections", "$.sections", (S) => { delete S.sections; }],
    ["역할 goal", "$.roles[0].goal", (S) => { delete S.roles[0].goal; }],
    ["역할 inclusion", "$.roles[0].inclusion", (S) => { delete S.roles[0].inclusion; }],
    ["화면 goal", ".goal", (S) => { delete scr(S, "home").goal; }],
    ["화면 problem", ".problem", (S) => { delete scr(S, "home").problem; }],
    ["화면 section", ".section", (S) => { delete scr(S, "home").section; }],
    ["영역 level", ".regions[0].level", (S) => { delete scr(S, "home").regions[0].level; }],
    ["분위기 font", "$.looks[0].font", (S) => { delete S.looks[0].font; }],
    ["오류 화면 when", ".when", (S) => { delete scr(S, "create-error").when; }],
    ["상태 변형이 아닌 화면 policy", ".policy", (S) => { delete scr(S, "home").policy; }],
  ].map(([what, at, change]) => [`새 칸 ${what} 없음 → 실패`, 1, `${at}: 필수 항목 없음`, change]),
  ["sections 빈 목록 → 실패", 1, "항목 1개 이상 필요", (S) => { S.sections = []; }],
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
