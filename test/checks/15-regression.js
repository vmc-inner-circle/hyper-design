// 회귀 — 분위기 CSS([data-theme] · [data-platform] 블록), 펼친 화면 조각(web · mobile), 부품 CSS 해시가 test/expected/ 기준과 같다.
// 기준을 바꾸는 게 맞을 때만 `node scripts/test.js --update` (커밋 글에 이유를 적는다).
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
const { ROOT, run, workCopy, suite, walk, UPDATE } = require("../lib.js");

const t = suite("15 회귀");
const EXPECTED = path.join(__dirname, "..", "expected");
const CSS_BLOCK = /^\[data-(?:theme|platform)="[^"]*"\][^{\n]*\{[^}]*\}/gm;   // 분위기 · 밀도 · 글자 단계 블록

// 고정 입력 하나를 펼쳐서 기준 후보 { 파일 이름: 내용 }로 — prefix는 기준 파일의 폴더
const expandFixture = (name, prefix, screens, withLooks) => {
  const w = workCopy(name);
  try {
    for (const s of ["ids.js", "expand.js"]) run(s, w.run);
    const out = {};
    if (withLooks) {
      const b = run("build.js", w.run, "--mode", "board");
      if (b.code !== 0) { t.fail(`build 실패 (${name})\n${b.out}`); t.end(); }
      const board = fs.readFileSync(path.join(w.run, "out", "board.html"), "utf8");
      out["looks.css"] = (board.match(CSS_BLOCK) || []).join("\n\n") + "\n";
      if (!out["looks.css"].includes("[data-theme=")) t.fail("분위기 CSS 블록을 찾지 못함");
      if (!out["looks.css"].includes("[data-platform=")) t.fail("밀도 · 글자 단계([data-platform]) 블록을 찾지 못함");
    }
    for (const s of screens) out[`${prefix}screens/${s}.html`] = fs.readFileSync(path.join(w.run, "screens", `${s}.html`), "utf8");
    return out;
  } finally {
    w.done();
  }
};

// 부품 CSS(web · mobile components)를 파일 이름과 함께 합친 해시 — 부품이 바뀌면 잡힌다
const partsHash = () => {
  const h = crypto.createHash("sha256");
  const files = [...walk("packages/web/components", (f) => f.endsWith(".css")), ...walk("packages/mobile/components", (f) => f.endsWith(".css"))];
  for (const f of files) h.update(`${f}\n${fs.readFileSync(path.join(ROOT, f), "utf8")}\n`);
  return h.digest("hex") + "\n";
};

const actual = Object.assign(
  expandFixture("sample", "", ["home", "done"], true),
  expandFixture("sample-mobile", "mobile/", ["home", "list"], false),
  { "components.sha256": partsHash() },
);

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
t.end();
