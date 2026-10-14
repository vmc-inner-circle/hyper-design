// 처음부터 끝까지 — 예시 하나가 ids → pack → expand → build(board) → lint(FAIL 0)까지 이어서 돌아간다.
const fs = require("fs");
const path = require("path");
const { run, workCopy, suite } = require("../lib.js");

const t = suite("10 처음부터 끝까지");
const w = workCopy();
try {
  const step = (label, script, ...args) => {
    const r = run(script, w.run, ...args);
    if (r.code === 0) t.ok(label); else t.fail(`${label} — exit ${r.code}\n${r.out.split("\n").slice(-6).join("\n")}`);
    return r;
  };
  step("ids", "ids.js");
  step("pack", "pack.js", "--screens", "home,done");
  step("expand", "expand.js");
  step("build --mode board", "build.js", "--mode", "board");

  const board = path.join(w.run, "out", "board.html");
  if (fs.existsSync(board) && fs.statSync(board).size > 10000) t.ok("board.html 생김");
  else t.fail("out/board.html 이 없거나 너무 작음");
  const pack = path.join(w.run, "packs", "home.md");
  if (!fs.existsSync(pack)) t.fail("packs/home.md 없음");

  const lint = run("lint.js", w.run);
  const m = lint.out.match(/FAIL (\d+)/);
  if (lint.code === 0 && m && m[1] === "0") t.ok("lint FAIL 0"); else t.fail(`lint — exit ${lint.code}\n${lint.out}`);

  // 펼친 조각에 짧은 부품 태그가 남지 않았다
  const left = ["home", "done"].filter((s) => /<x-/.test(fs.readFileSync(path.join(w.run, "screens", `${s}.html`), "utf8")));
  if (left.length) t.fail(`expand 뒤에도 <x-…> 가 남음: ${left.join(", ")}`); else t.ok("expand 뒤 부품 태그 0");
} finally {
  w.done();
}
t.end();
