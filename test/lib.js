// 시험 공용 도구 — Node 내장만 쓴다. 검사 파일(test/checks/NN-이름.js)이 가져다 쓴다.
const fs = require("fs");
const os = require("os");
const path = require("path");
const { spawnSync } = require("child_process");

const ROOT = path.resolve(__dirname, "..");
const UPDATE = process.argv.includes("--update");

// scripts/<이름>을 실제로 돌린다. 출력은 붙여서 돌려준다.
const run = (script, ...args) => {
  const r = spawnSync(process.execPath, [path.join(ROOT, "scripts", script), ...args], { cwd: ROOT, encoding: "utf8", timeout: 120000 });
  return { code: r.status, out: (r.stdout || "") + (r.stderr || "") };
};

// 고정 입력을 임시 폴더로 복사해서 돌린다 — 저장소 안은 건드리지 않는다.
const workCopy = (name = "sample") => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "oss-test-"));
  const dest = path.join(dir, name);
  fs.cpSync(path.join(__dirname, "fixtures", name), dest, { recursive: true });
  return { dir, run: dest, done: () => fs.rmSync(dir, { recursive: true, force: true }) };
};

// 검사 하나의 결과 모으기 — fail()이 하나라도 있으면 exit 1, skip()만 있으면 0.
const suite = (title) => {
  const fails = [];
  let passed = 0;
  return {
    ok: (msg) => { passed++; console.log(`  ok   ${msg}`); },
    fail: (msg) => { fails.push(msg); console.log(`  FAIL ${msg}`); },
    skip: (msg) => console.log(`  skip ${msg}`),
    end: () => { console.log(`${title}: 통과 ${passed} · 실패 ${fails.length}`); process.exit(fails.length ? 1 : 0); },
  };
};

const walk = (rel, filter = () => true) => {
  const abs = path.join(ROOT, rel);
  if (!fs.existsSync(abs)) return [];
  if (fs.statSync(abs).isFile()) return filter(rel) ? [rel] : [];
  return fs.readdirSync(abs).sort().flatMap((n) => (n === "node_modules" || (n.startsWith(".") && n !== ".claude") ? [] : walk(path.join(rel, n), filter)));
};

// 단계 스위치 — test/stages.json. 꺼져 있으면 그 검사는 건너뛴다.
const stageOn = (name) => { try { return JSON.parse(require("fs").readFileSync(require("path").join(ROOT, "test", "stages.json"), "utf8"))[name] === true; } catch { return false; } };

module.exports = { ROOT, UPDATE, run, workCopy, suite, walk, stageOn };
