// 저장소 검사 — 나가는 파일에 내부 작업 기록(인터뷰 번호 · ADR · 기록 id · 작업 번호 · 내부 경로 …)이 0이다.
const fs = require("fs");
const path = require("path");
const { ROOT, suite, walk } = require("../lib.js");

const t = suite("90 내부 기록");
// 나가면 안 되는 경로
const NEVER = [/^tmp\//, /^docs\/study\//, /^runs\//, /^research\//, /^upstream\//];
// 내용 패턴 (사람 이름은 넣지 않는다)
const PATTERNS = [
  ["인터뷰 번호", /인터뷰 ?\d+/g],
  ["ADR", /ADR ?`?\d{8,}(-\d+)?`?/g],
  ["기록 id", /\b20\d{10}-\d{2}\b/g],
  ["내부 기록 경로", /tmp\/(domain|tasks|runs)|docs\/study/g],
  ["작업 번호", /\bT\d{2}\b(?=[^a-zA-Z])/g],
];
const ROOTS = ["scripts", "packages", ".claude/skills", ".claude/agents", "docs", "templates", "test", "README.md"];
const SELF = "test/checks/90-internal-notes.js";   // 패턴 글자가 자기 자신에 걸리지 않게
const files = ROOTS.flatMap((r) => walk(r, (f) => /\.(js|json|md|css|html|txt|ya?ml)$/.test(f))).filter((f) => f !== SELF);

let bad = 0;
for (const f of files) {
  if (NEVER.some((re) => re.test(f))) { bad++; t.fail(`${f}: 나가면 안 되는 경로`); continue; }
  const s = fs.readFileSync(path.join(ROOT, f), "utf8");
  for (const [name, re] of PATTERNS) {
    const hits = s.match(re);
    if (hits) { bad += hits.length; t.fail(`${f}: ${name} ${hits.length}곳 (예: ${hits[0]})`); }
  }
}
if (!bad) t.ok(`내부 기록 0 (파일 ${files.length}개)`);
t.end();
