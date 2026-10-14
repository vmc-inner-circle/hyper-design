#!/usr/bin/env node
/**
 * test.js — 저장소 시험. test/checks/NN-이름.js 를 번호 순서대로 하나씩 돌린다(이 파일은 부르기만 한다).
 *
 *   node scripts/test.js              전부
 *   node scripts/test.js 15           번호나 이름에 '15'가 든 검사만
 *   node scripts/test.js --update     회귀 기준(test/expected/)을 지금 결과로 갱신 — 커밋 글에 이유를 적는다
 *
 * 번호: 10 처음부터 끝까지 · 15 회귀 · 20 스키마 · 30 값 · 40 검사 · 50 안내문 · 90 내부 기록
 * 검사 하나 = 파일 하나. 새 검사는 파일만 더하면 된다. exit 0 = 모두 통과, 1 = 실패 있음.
 */
const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const DIR = path.join(__dirname, "..", "test", "checks");
const args = process.argv.slice(2);
const only = args.filter((a) => !a.startsWith("--"));
const checks = fs.readdirSync(DIR).filter((f) => /^\d\d-.*\.js$/.test(f)).sort().filter((f) => !only.length || only.some((o) => f.includes(o)));

const failed = [];
for (const f of checks) {
  console.log(`\n# ${f}`);
  const r = spawnSync(process.execPath, [path.join(DIR, f), ...args.filter((a) => a.startsWith("--"))], { stdio: "inherit" });
  if (r.status !== 0) failed.push(f);
}
console.log(`\n시험 ${checks.length}개 · 실패 ${failed.length}${failed.length ? ` (${failed.join(", ")})` : ""}`);
process.exit(failed.length || !checks.length ? 1 : 0);
