// 저장소 검사 — 안내문(.claude/skills · .claude/agents · packages/*/snippets · docs)이 적어 둔 규칙 id가 정본에 있다.
// 안내문에서 규칙을 가리킬 때는 "규칙 `<id>`" 모양으로 적는다. 규칙 정본(rules.json)이 아직 없으면 건너뛴다.
const fs = require("fs");
const path = require("path");
const { ROOT, suite, walk, stageOn } = require("../lib.js");

const t = suite("50 안내문");
const rulesFile = path.join(ROOT, "packages", "core", "schema", "rules.json");
if (!stageOn("guides")) { t.skip("단계 스위치 guides 꺼짐 — [5/5]에서 켠다"); t.end(); }
if (!fs.existsSync(rulesFile)) { t.skip("packages/core/schema/rules.json 없음 — 규칙 정본이 생기면 켜진다"); t.end(); }

const ids = new Set(JSON.parse(fs.readFileSync(rulesFile, "utf8")).rules.map((r) => r.id));
const files = [".claude/skills", ".claude/agents", "packages/web/snippets", "packages/mobile/snippets", "docs"].flatMap((d) => walk(d, (f) => f.endsWith(".md")));
let refs = 0, bad = 0;
for (const f of files) {
  const text = fs.readFileSync(path.join(ROOT, f), "utf8");
  for (const m of text.matchAll(/규칙 `([a-z0-9][a-z0-9-]*)`/g)) {
    refs++;
    if (!ids.has(m[1])) { bad++; t.fail(`${f}: 규칙 id '${m[1]}' 가 rules.json에 없음`); }
  }
}
if (!bad) t.ok(`규칙 id ${refs}곳 모두 정본에 있음 (안내문 ${files.length}개)`);
t.end();
