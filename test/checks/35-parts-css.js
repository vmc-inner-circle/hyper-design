// 저장소 검사 — 화면 부품 CSS(packages/web/components)가 KRDS 색 규칙을 지킨다.
// 규칙 값은 packages/core/schema/rules.json에서 읽는다(규칙 문장을 여기 복사하지 않는다).
// rules.json이 아직 없으면 건너뛴다 — 규칙 정본이 생기면 저절로 켜진다.
const fs = require("fs");
const path = require("path");
const { ROOT, suite, stageOn } = require("../lib.js");

const t = suite("40 부품 CSS");
const rulesFile = path.join(ROOT, "packages", "core", "schema", "rules.json");
const DIR = path.join(ROOT, "packages", "web", "components");
if (!stageOn("parts-krds")) { t.skip("단계 스위치 parts-krds 꺼짐 — [3/5]에서 켠다"); t.end(); }
if (!fs.existsSync(rulesFile)) { t.skip("packages/core/schema/rules.json 없음 — 규칙 정본이 생기면 켜진다"); t.end(); }

const { rules } = JSON.parse(fs.readFileSync(rulesFile, "utf8"));
const R = (id) => rules.find((r) => r.id === id) || { value: {} };

// 아주 단순한 CSS 읽기 — 주석을 지우고 '선택자 { 선언 }'만 모은다
const blocks = [];
for (const f of fs.readdirSync(DIR).filter((x) => x.endsWith(".css")).sort()) {
  const src = fs.readFileSync(path.join(DIR, f), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
  for (const m of src.matchAll(/([^{}]+)\{([^{}]*)\}/g)) blocks.push({ file: f, sel: m[1].trim().replace(/^@[^{]*$/, ""), body: m[2] });
}
// 괄호 밖 쉼표로만 나눈다 — ':is(.input, .select)'가 쪼개지지 않게
const top = (sel) => { const out = []; let depth = 0, cur = ""; for (const ch of sel) { if (ch === "(") depth++; if (ch === ")") depth--; if (ch === "," && !depth) { out.push(cur); cur = ""; } else cur += ch; } return [...out, cur].map((x) => x.trim()); };

// color-role-use — 역할마다 쓰는 곳(선택자 패턴) 밖에서 쓰면 실패
let roleFails = 0;
for (const [role, def] of Object.entries(R("color-role-use").value.roles || {})) {
  const re = new RegExp(`var\\(--c-${role}(-soft|-fg|-soft-fg|-hover|-active)?\\)`);
  const allow = def.where ? new RegExp(def.where) : null;
  if (!allow) continue;
  // 배지 배경의 Primary는 badge-not-primary가 맡는다
  const owned = (b) => role === "primary" && top(b.sel).every((s) => /badge/.test(s));
  for (const b of blocks.filter((x) => re.test(x.body) && x.sel && !owned(x) && !top(x.sel).every((s) => allow.test(s)))) {
    roleFails++;
    t.fail(`color-role-use: ${role}를 '${b.sel}'(${b.file})에서 씀 — 이 역할의 자리: ${def.says}`);
  }
}
if (!roleFails) t.ok("color-role-use");

let n = 0;
for (const b of blocks) if (/badge/.test(b.sel) && /background[^;]*var\(--c-primary/.test(b.body)) { n++; t.fail(`badge-not-primary: '${b.sel}'(${b.file}) 배경이 Primary`); }
if (!n) t.ok("badge-not-primary");
n = 0;
for (const b of blocks) if (/:disabled|is-disabled/.test(b.sel) && /(^|;|\s)opacity\s*:|rgba\(/.test(b.body)) { n++; t.fail(`disabled-no-alpha: '${b.sel}'(${b.file}) 비활성에 투명도`); }
if (!n) t.ok("disabled-no-alpha");
t.end();
