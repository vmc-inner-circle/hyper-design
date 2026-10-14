// 회귀 — 분위기 CSS([data-theme] 블록)와 펼친 화면 조각이 test/expected/ 기준과 같다.
// 기준을 바꾸는 게 맞을 때만 `node scripts/test.js --update` (커밋 글에 이유를 적는다).
const fs = require("fs");
const path = require("path");
const { run, workCopy, suite, UPDATE } = require("../lib.js");

const t = suite("15 회귀");
const EXPECTED = path.join(__dirname, "..", "expected");
const w = workCopy();
try {
  for (const s of ["ids.js", "expand.js"]) run(s, w.run);
  const b = run("build.js", w.run, "--mode", "board");
  if (b.code !== 0) { t.fail(`build 실패\n${b.out}`); t.end(); }
  const board = fs.readFileSync(path.join(w.run, "out", "board.html"), "utf8");

  const actual = { "looks.css": (board.match(/^\[data-theme="[^"]*"\][^{\n]*\{[^}]*\}/gm) || []).join("\n\n") + "\n" };
  for (const s of ["home", "done"]) actual[`screens/${s}.html`] = fs.readFileSync(path.join(w.run, "screens", `${s}.html`), "utf8");
  if (!actual["looks.css"].includes("[data-theme=")) t.fail("분위기 CSS 블록을 찾지 못함");

  for (const [name, text] of Object.entries(actual)) {
    const file = path.join(EXPECTED, name);
    if (UPDATE) {
      fs.mkdirSync(path.dirname(file), { recursive: true });
      fs.writeFileSync(file, text);
      t.ok(`기준 갱신 ${name}`);
    } else if (!fs.existsSync(file)) {
      t.fail(`기준 없음 ${name} — 처음이면 --update`);
    } else {
      const want = fs.readFileSync(file, "utf8");
      if (want === text) { t.ok(name); continue; }
      const a = want.split("\n"), b2 = text.split("\n");
      const i = a.findIndex((l, k) => l !== b2[k]);
      t.fail(`${name} 가 기준과 다름 (${i + 1}째 줄)\n    기준: ${a[i]}\n    지금: ${b2[i]}`);
    }
  }
} finally {
  w.done();
}
t.end();
