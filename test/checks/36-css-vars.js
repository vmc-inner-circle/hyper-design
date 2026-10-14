// 저장소 검사 — 부품 CSS · core/canvas · core/tokens에서 쓰는 var(--이름)이 어딘가에 정의돼 있는가.
// 정의 출처: base.css · toggles.css · 부품 CSS의 정의 · scripts/looks.js가 내보내는 변수(고정 입력 looks로 CSS를 만들어 모은다).
// 대체값이 있는 var(--x, 대체값)은 WARN(통과, 목록만), 없는 것은 FAIL. 이름 바꾸기 표의 옛 이름이 남아 있어도 FAIL.
const fs = require("fs");
const path = require("path");
const { ROOT, suite, walk } = require("../lib.js");
const looks = require(path.join(ROOT, "scripts", "looks.js"));

const t = suite("36 CSS 변수");
const read = (rel) => fs.readFileSync(path.join(ROOT, rel), "utf8");
const strip = (s) => s.replace(/\/\*[\s\S]*?\*\//g, "");

const USERS = [
  ...walk("packages/web/components", (f) => f.endsWith(".css")),
  ...walk("packages/mobile/components", (f) => f.endsWith(".css")),
  ...walk("packages/core/canvas", (f) => /\.(css|js)$/.test(f)),
  ...walk("packages/core/tokens", (f) => f.endsWith(".css")),
];
const OLD = { "--font-head": "--font-heading", "--ls-head": "--tracking-heading", "--space-section": "--space-page", "--space-block": "--space-item" };

// 고정 입력 — 밝은 분위기 하나, 어두운 분위기 하나. 글자 단계(ratio는 looks.RATIOS의 tight · normal · wide 중 하나) · 밀도 · 대표색까지 다 나오도록 type · palette를 채운다.
const FIXED = [
  { id: "fx-light", mode: "light", bg: "#FFFFFF", ink: "#1A1A1A", palette: { brand: { name: "대표", hex: "#2F5BEA" } }, swatches: [{ id: "a", name: "a", hex: "#2F5BEA" }, { id: "b", name: "b", hex: "#D9480F" }], type: { ratio: "wide", density: "normal" } },
  { id: "fx-dark", mode: "dark", bg: "#14161A", ink: "#F2F2F2", palette: { brand: { name: "대표", hex: "#7C9CFF" } }, swatches: [{ id: "a", name: "a", hex: "#7C9CFF" }], type: { ratio: "wide", density: "compact" } },
];
const fixedLooks = looks.getLooks({ looks: FIXED, concepts: FIXED.map((L) => ({ look: L.id, density: L.type.density })) });
let generated = "";
try { generated = looks.looksCss(fixedLooks); } catch (e) { t.fail(`looks.js로 CSS를 만들지 못함: ${e.message}`); }

const defined = new Set();
const collect = (src) => { for (const m of src.matchAll(/(?<![\w-])(--[\w-]+)\s*:/g)) defined.add(m[1]); };
collect(strip(generated));
// 고정 입력이 글자 단계를 실제로 내보내는지 — 아니면 base.css가 --fs-* 정의를 우연히 가려 준다
if (generated) {
  for (const n of ["--fs-md", "--fs-body", "--fs-caption", "--fs-title", "--fs-display"]) if (!new RegExp(`${n}\\s*:`).test(generated)) t.fail(`고정 입력의 looks.js 출력에 ${n}이 없음 — type.ratio를 확인`);
  if (!/data-type="large"/.test(generated)) t.fail('고정 입력의 looks.js 출력에 [data-type="large"] 블록이 없음');
}
for (const f of USERS.filter((f) => f.endsWith(".css"))) collect(strip(read(f)));
// canvas JS가 setProperty("--x") · style="--x:…"로 정의하는 것도 정의로 센다
for (const f of USERS.filter((f) => f.endsWith(".js"))) {
  const src = read(f);
  for (const m of src.matchAll(/setProperty\(\s*["'`](--[\w-]+)/g)) defined.add(m[1]);
  collect(src);
}
if (defined.size < 20) t.fail(`정의된 변수가 ${defined.size}개뿐 — looks.js 출력이나 base.css를 못 읽은 듯`);

// 쓰는 곳 모으기 — var(--x) / var(--x, 대체값)
const uses = new Map();   // 이름 → { fallback: bool, where: Set }
const olds = [];
for (const f of USERS) {
  const lines = (f.endsWith(".css") ? strip(read(f)) : read(f)).split("\n");
  lines.forEach((line, i) => {
    for (const m of line.matchAll(/var\(\s*(--[\w-]+)\s*(,)?/g)) {
      const u = uses.get(m[1]) || { fb: true, where: new Set() };
      if (!m[2]) u.fb = false;
      u.where.add(`${f}:${i + 1}`);
      uses.set(m[1], u);
    }
    for (const o of Object.keys(OLD)) if (new RegExp(`${o}(?![\\w-])`).test(line)) olds.push(`${f}:${i + 1} ${o} → ${OLD[o]}`);
  });
}

const show = (u) => [...u.where].slice(0, 3).join(", ") + (u.where.size > 3 ? ` 외 ${u.where.size - 3}곳` : "");
let bad = 0, warn = 0;
for (const [name, u] of [...uses].sort()) {
  if (defined.has(name)) continue;
  if (u.fb) { warn++; console.log(`  WARN ${name} — 정의 없음, 대체값으로 버팀 (${show(u)})`); }
  else { bad++; t.fail(`${name} — 정의 없음, 대체값도 없음 (${show(u)})`); }
}
for (const o of olds) t.fail(`옛 이름이 남아 있음: ${o}`);
if (!bad && !olds.length) t.ok(`var() ${uses.size}종 모두 정의됨(대체값에만 기대는 것 ${warn}종은 WARN)`);
t.end();
