// lint 새 규칙(scripts/lint-rules.js) — ctx를 직접 만들어 규칙마다 통과 · 실패 한 쌍을 본다.
// 고정 입력(test/fixtures/sample)을 고쳐서 넣는다: change(S, F, html)가 세 가지를 고친다.
// 통과 = 그 규칙 id로 보고가 없음, 실패 = 그 규칙 id로 rules.json의 단계(check.level) 보고가 하나 이상.
const fs = require("fs");
const path = require("path");
const { ROOT, suite } = require("../lib.js");

const t = suite("40 lint 새 규칙");
const FIX = path.join(__dirname, "..", "fixtures", "sample");
const RULES_FILE = JSON.parse(fs.readFileSync(path.join(ROOT, "packages", "core", "schema", "rules.json"), "utf8")).rules;
// reachable은 다른 일감이 rules.json에 넣는다 — 아직 없으면 시험에서만 FAIL 규칙으로 더해 검사 코드를 본다
const RULES = RULES_FILE.some((r) => r.id === "reachable") ? RULES_FILE : [...RULES_FILE, { id: "reachable", check: { by: "lint", level: "FAIL" } }];
const levelOf = (id) => ((RULES.find((r) => r.id === id) || {}).check || {}).level || "WARN";   // stays-match는 rules.json에 아직 없다 → WARN

let check;
try { ({ check } = require(path.join(ROOT, "scripts", "lint-rules.js"))); }
catch (e) { t.fail(`scripts/lint-rules.js를 불러오지 못함 — ${e.message}`); t.end(); }
if (typeof check !== "function") { t.fail("scripts/lint-rules.js가 check(ctx)를 내보내지 않음"); t.end(); }

// 고정 입력으로 ctx를 만들고 change로 고친 뒤 돌려 보고를 모은다
const baseHtml = () => {
  const S = JSON.parse(fs.readFileSync(path.join(FIX, "screens.json"), "utf8"));
  return Object.fromEntries(S.screens.map((s) => [s.slug, fs.readFileSync(path.join(FIX, s.file), "utf8")]));
};
function runCheck(change, rules = RULES) {
  const S = JSON.parse(fs.readFileSync(path.join(FIX, "screens.json"), "utf8"));
  const F = JSON.parse(fs.readFileSync(path.join(FIX, "flow.json"), "utf8"));
  const html = baseHtml();
  if (change) change(S, F, html);
  const out = [];
  check({ dir: FIX, screens: S, flow: F, html, rules, report: (level, ruleId, where, msg) => out.push({ level, ruleId, where, msg }) });
  return out;
}
const scr = (S, slug) => S.screens.find((s) => s.slug === slug);
const say = (r) => `[${r.level}] ${r.ruleId} ${r.where}: ${r.msg}`;

// 처음 시작 흐름 — 빈 상태 화면(home-empty)과 그 화면을 지나는 흐름. flow-role 통과에 쓴다
const withStart = (S, F, html) => {
  const home = scr(S, "home");
  S.screens.splice(1, 0, { ...JSON.parse(JSON.stringify(home)), slug: "home-empty", name: "홈 (처음)", file: "screens/home-empty.html", state: "empty", variantOf: "home", when: "아직 만든 항목이 없을 때", data: [] });
  html["home-empty"] = html.home;
  F.flows.unshift({ key: "start", name: "처음 항목 만들기", role: "owner", steps: [{ from: "home-empty", region: "new", trigger: "create", action: "'새로 만들기'를 누르면", to: "create" }] });
};
// 뜨는 창 화면 — 홈에서 여는 '지우기 확인 창'
const withOverlay = (S, F, html) => {
  S.screens.push({ slug: "delete-confirm", name: "지우기 확인 창", role: "owner", section: "home", step: "오늘 보기", file: "screens/delete-confirm.html", overlayOf: "home",
    goal: "지울지 한 번 더 확인한다", problem: "잘못 지우면 되돌릴 수 없다", emphasize: "정말 지울까요?", data: [], defer: [], focus: "ask",
    regions: [{ key: "ask", label: "지울지 묻기", why: "되돌릴 수 없어서 한 번 더 물어요", level: 1, form: "hero", content: "지울 항목 이름 · 지우기 · 그만두기" }], policy: [{ title: "기본 정의", items: ["지우면 되돌릴 수 없다"] }] });
  html["delete-confirm"] = `<div class="modal-backdrop"><div class="modal" data-region="ask"><button class="btn btn-danger" data-stay="지웠어요">지우기</button><button class="btn btn-secondary" data-back>그만두기</button></div></div>`;
  html.home = html.home.replace("</main>", `  <button class="btn btn-tertiary" data-trigger="delete">지우기</button>\n</main>`);
};
const looks = (S, tones) => {
  const L = S.looks[0];
  S.looks = tones.map((tone, i) => ({ ...L, id: `look-${i + 1}`, name: `분위기 ${i + 1}`, tone }));
};

// 메뉴 없는 틀(none) 시안 + 메뉴에 없는 알림 화면 — reachable에 쓴다
const withAlerts = (S, F, h) => {
  S.concepts = [{ id: "a", name: "오늘 할 일부터 보기", why: "열자마자 할 일이 보여요", shell: "none", home: "오늘 요약", look: "warm", screens: ["home"] }];
  S.concept = "a";
  S.screens.push({ ...JSON.parse(JSON.stringify(scr(S, "home"))), slug: "alerts", name: "알림", step: "알림 보기", file: "screens/alerts.html" });
  h.alerts = h.home;
};
// 고르는 버튼(칩) — create 화면 item-form 안에
const withChips = (h, msg = "이번 주를 골랐어요") => { h.create = h.create.replace(`<button class="btn btn-primary"`, `<button class="chip" data-stay="${msg}">이번 주</button>\n      <button class="chip" data-stay="다음 주를 골랐어요">다음 주</button>\n      <button class="btn btn-primary"`); };

// [규칙 id, 이름, 통과 change, 실패 [이름, change, 보고에 있어야 할 말?]들] — 같은 규칙이 여러 쌍일 수 있다
const pairs = [
  ["rank1-one", "1순위 영역은 화면마다 하나 · focus와 같음", null, [
    ["1순위 영역 0개", (S) => { scr(S, "home").regions[0].level = 2; }],
    ["1순위 영역 2개", (S) => { scr(S, "home").regions[1].level = 1; }],
    ["focus가 1순위가 아님", (S) => { scr(S, "home").focus = "recent"; }],
    ["뜨는 창도 본다", (S, F, h) => { withOverlay(S, F, h); scr(S, "delete-confirm").regions[0].level = 2; }],
  ]],
  ["rank3-max", "3순위 영역은 화면당 value.max 이하", null, [
    ["3순위 2개", (S) => { scr(S, "home").regions[1].level = 3; }],
  ]],
  ["data-key-exists", "data 이름표는 facts에", null, [
    ["facts에 없는 이름표", (S) => { scr(S, "home").data.push("weather-today"); }],
  ]],
  ["data-key-exists", "facts가 옛 모양(배열)이면 건너뜀", (S) => { S.facts = ["오늘 할 일 5건"]; }, [
    ["facts 칸이 없으면 data 이름표가 모두 없는 것", (S) => { delete S.facts; }, "'todo-today', 'recent-changes'"],
  ]],
  ["flow-role", "흐름 주인 · 처음 시작 흐름 · goal 흐름", withStart, [
    ["처음 시작 흐름 없음", null],
    ["흐름에 role 없음", (S, F, h) => { withStart(S, F, h); delete F.flows[1].role; }],
    ["goal 흐름 없음(처음 시작 흐름뿐)", (S, F, h) => { withStart(S, F, h); F.flows.pop(); }],
  ]],
  ["flow-role", "역할의 첫 흐름이 그 역할의 처음 · 빈 화면을 지남", withStart, [
    ["시작 흐름이 맨 앞이 아님", (S, F, h) => { withStart(S, F, h); F.flows.push(F.flows.shift()); }, "역할 owner: 첫 흐름 'make-item'"],
    ["첫 흐름이 다른 역할의 빈 화면을 지남", (S, F, h) => {
      withStart(S, F, h);
      S.roles.push({ key: "member", label: "구성원", goal: "모임 소식을 본다", inclusion: "휴대폰", nav: [] });
      scr(S, "home-empty").role = "member";
    }, "역할 owner: 첫 흐름 'start'"],
  ]],
  ["primary-action-one", "채운 버튼은 화면당 value.max 이하", null, [
    ["채운 버튼 2개", (S, F, h) => { h.home = h.home.replace("</main>", `  <button class="btn btn-primary" data-stay="보냈어요">알림 보내기</button>\n</main>`); }],
  ]],
  ["tone-spread", "바탕 톤 value.min_tones가지 이상 · 사례 바탕 value.max_case개까지", (S) => looks(S, ["white", "paper", "tint", "dark", "white"]), [
    ["톤 2가지뿐", (S) => looks(S, ["white", "white", "paper", "paper", "white"])],
    ["사례 바탕 2개", (S) => looks(S, ["white", "paper", "tint", "dark", "color"])],
  ]],
  ["tone-spread", "tone 있는 분위기만 센다 — 하나도 없으면 건너뜀", (S) => { looks(S, ["white", "paper", "tint", "dark", "white"]); for (const L of S.looks) delete L.tone; }, [
    ["tone 있는 3개가 모두 같음", (S) => { looks(S, ["white", "white", "white", "paper", "tint"]); delete S.looks[3].tone; delete S.looks[4].tone; }, "tone 있는 분위기 3개"],
  ]],
  ["stays-match", "regions[].stays ↔ 조각 data-stay", (S, F, h) => {
    scr(S, "create").regions[0].stays = [{ label: "임시 저장", msg: "임시 저장했어요" }];
    h.create = h.create.replace(`<button class="btn btn-primary"`, `<button class="btn btn-secondary" data-stay="임시 저장했어요">임시 저장</button>\n      <button class="btn btn-primary"`);
  }, [
    ["계획만 있고 조각에 없음", (S) => { scr(S, "create").regions[0].stays = [{ label: "임시 저장", msg: "임시 저장했어요" }]; }],
    ["조각에만 있음(계획을 쓰는 실행물)", (S, F, h) => {
      scr(S, "create").regions[0].stays = [{ label: "임시 저장", msg: "임시 저장했어요" }];
      h.create = h.create.replace(`<button class="btn btn-primary"`, `<button class="btn btn-secondary" data-stay="임시 저장했어요">임시 저장</button>\n      <button class="btn btn-secondary" data-stay="복사했어요">복사</button>\n      <button class="btn btn-primary"`);
    }],
    ["문구가 다름", (S, F, h) => {
      scr(S, "create").regions[0].stays = [{ label: "임시 저장", msg: "임시 저장했어요" }];
      h.create = h.create.replace(`<button class="btn btn-primary"`, `<button class="btn btn-secondary" data-stay="저장됨">임시 저장</button>\n      <button class="btn btn-primary"`);
    }],
  ]],
  ["stays-match", "고르는 버튼 — 계획에 있으면 조각에서 찾고, 조각에만 있으면 묻지 않음", (S, F, h) => {
    scr(S, "create").regions[0].stays = [{ label: "이번 주", msg: "이번 주를 골랐어요" }];
    withChips(h);
  }, [
    ["계획의 고르는 버튼 문구가 다름", (S, F, h) => {
      scr(S, "create").regions[0].stays = [{ label: "이번 주", msg: "이번 주를 골랐어요" }];
      withChips(h, "골랐어요");
    }, "'이번 주' 문구가 다름"],
  ]],
  ["reachable", "처음 시작 화면에서 흐름 · 갈래 · 메뉴로 모든 화면에 닿음", (S, F, h) => { withAlerts(S, F, h); F.branches.push({ from: "home", region: "new", trigger: "alerts", action: "'알림'을 누르면", to: "alerts" }); }, [
    ["메뉴 없는 틀에서 알림 화면으로 갈 길 없음", withAlerts, "홈에 갈래가 필요"],
    ["메뉴에도 흐름에도 없는 화면", (S, F, h) => { withAlerts(S, F, h); S.concepts[0].shell = "sidebar"; }, "화면 alerts"],
  ]],
  ["reachable", "메뉴 틀이 있으면 메뉴로 닿음", (S, F, h) => { withAlerts(S, F, h); S.concepts[0].shell = "sidebar"; S.roles[0].nav.push({ slug: "alerts", label: "알림", icon: "bell" }); }, [
    ["메뉴에 있어도 틀이 none이면 메뉴로 못 감", (S, F, h) => { withAlerts(S, F, h); S.roles[0].nav.push({ slug: "alerts", label: "알림", icon: "bell" }); }, "홈에 갈래가 필요"],
  ]],
  ["overlay-reached", "뜨는 창은 흐름 단계 · 갈래의 도착", (S, F, h) => {
    withOverlay(S, F, h);
    F.branches.push({ from: "home", region: "new", trigger: "delete", action: "'지우기'를 누르면", to: "delete-confirm" });
  }, [
    ["여는 갈래 없음", withOverlay],
  ]],
  ["split-when", "같은 from + trigger가 두 번이면 모두 when", (S, F) => {
    F.flows[0].steps[1].when = "이름을 적었으면";
    F.branches.push({ from: "create", region: "item-form", trigger: "save", action: "'만들기'를 누르면", to: "create-error", when: "이름이 비었으면" });
  }, [
    ["갈래에만 when", (S, F) => { F.branches.push({ from: "create", region: "item-form", trigger: "save", action: "'만들기'를 누르면", to: "create-error", when: "이름이 비었으면" }); }],
  ]],
];

// rules.json에 reachable이 없으면 검사도 돌지 않는다
{
  const out = runCheck(withAlerts, RULES_FILE.filter((r) => r.id !== "reachable")).filter((r) => r.ruleId === "reachable");
  if (!out.length) t.ok("reachable — rules.json에 규칙이 없으면 건너뜀"); else t.fail(`reachable 규칙 없이 보고가 나옴\n    ${out.map(say).join("\n    ")}`);
}

// 고정 입력 그대로는 flow-role(처음 시작 흐름 없음) 말고는 보고가 없어야 한다
{
  const out = runCheck(null).filter((r) => r.ruleId !== "flow-role");
  if (!out.length) t.ok("고정 입력 — flow-role 말고 보고 0");
  else t.fail(`고정 입력에서 보고가 나옴\n    ${out.map(say).join("\n    ")}`);
}

for (const [id, title, pass, failsWith] of pairs) {
  const rule = RULES.find((r) => r.id === id);
  if (!rule && id !== "stays-match") { t.fail(`${id}: rules.json에 없음`); continue; }
  const want = levelOf(id);
  const mine = (out) => out.filter((r) => r.ruleId === id);
  const p = mine(runCheck(pass));
  if (!p.length) t.ok(`${id} 통과 — ${title}`); else t.fail(`${id} 통과 쪽에서 보고가 나옴\n    ${p.map(say).join("\n    ")}`);
  for (const [name, change, see] of failsWith) {
    const f = mine(runCheck(change));
    if (!f.length) t.fail(`${id} 실패 — ${name}: 보고가 없음`);
    else if (see && !f.some((r) => `${r.where}: ${r.msg}`.includes(see))) t.fail(`${id} 실패 — ${name}: '${see}' 보고가 없음\n    ${f.map(say).join("\n    ")}`);
    else if (f.some((r) => r.level !== want)) t.fail(`${id} 실패 — ${name}: 단계가 ${want}가 아님\n    ${f.map(say).join("\n    ")}`);
    else t.ok(`${id} 실패 — ${name} [${want}]`);
  }
}

// 메시지는 규칙 문장을 복사하지 않는다(lint.js가 규칙 id · says를 붙인다) · where는 비지 않는다
{
  const all = pairs.flatMap(([, , pass, failsWith]) => [pass, ...failsWith.map((x) => x[1])]).flatMap((c) => runCheck(c));
  const copied = all.filter((r) => { const s = (RULES.find((x) => x.id === r.ruleId) || {}).says; return s && r.msg.includes(s); });
  const noWhere = all.filter((r) => !r.where || !r.msg);
  if (!copied.length && !noWhere.length) t.ok(`보고 ${all.length}개 — 규칙 문장 복사 0 · 빈 where/msg 0`);
  else t.fail(`메시지 형식\n    ${[...copied, ...noWhere].map(say).join("\n    ")}`);
}

t.end();
