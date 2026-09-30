#!/usr/bin/env node
/**
 * ids.js — screens.json의 빠진 id를 이어서 채운다.
 *
 *   node scripts/ids.js runs/<project>
 *
 * 규칙 (docs/harness-design.md §6.1):
 * - 화면 번호는 1, 2, 3 … 으로 이어진다 (사용자가 "화면 5"라고 부르는 번호, 최종본 NN-slug.html 번호와 같다).
 *   screens.json 순서 = 사용자가 만나는 순서로 적으면 번호도 그 순서가 된다.
 * - 영역 번호는 101부터 따로 센다 (화면 번호와 섞이지 않게 — 예전처럼 화면 번호가 1, 5, 10으로 띄엄띄엄 되지 않는다).
 * - 이미 있는 id는 절대 바꾸지 않는다. 라운드가 바뀌어도 번호가 유지되어야 한다.
 * - 삭제된 번호는 재사용하지 않는다 (nextScreenId·nextRegionId가 지금까지 발급된 최대값+1을 기억한다).
 */
const fs = require("fs");
const path = require("path");

const runDir = process.argv[2];
if (!runDir) {
  console.error("usage: node scripts/ids.js runs/<project>");
  process.exit(2);
}
const file = path.join(runDir, "screens.json");
const data = JSON.parse(fs.readFileSync(file, "utf8"));

const REGION_BASE = 101;
const used = new Set();
let maxScreen = 0, maxRegion = REGION_BASE - 1;
for (const s of data.screens || []) {
  if (Number.isInteger(s.id)) { used.add(s.id); maxScreen = Math.max(maxScreen, s.id); }
  for (const r of s.regions || []) {
    if (Number.isInteger(r.id)) { used.add(r.id); maxRegion = Math.max(maxRegion, r.id); }
  }
}

const counter = (start) => { let n = start; return () => { while (used.has(n)) n++; used.add(n); return n++; }; };
const nextScreen = counter(Math.max(Number.isInteger(data.nextScreenId) ? data.nextScreenId : 1, maxScreen + 1));
const nextRegion = counter(Math.max(Number.isInteger(data.nextRegionId) ? data.nextRegionId : REGION_BASE, maxRegion + 1));
const issued = [];

for (const s of data.screens || []) {
  if (!Number.isInteger(s.id)) { s.id = nextScreen(); issued.push(`화면 ${s.id} ← ${s.slug}`); }
}
for (const s of data.screens || []) {
  for (const r of s.regions || []) {
    if (!Number.isInteger(r.id)) { r.id = nextRegion(); issued.push(`영역 ${r.id} ← ${s.slug} / ${r.key}`); }
  }
}
let ns = 1, nr = REGION_BASE;
for (const v of used) { if (v < REGION_BASE) ns = Math.max(ns, v + 1); else nr = Math.max(nr, v + 1); }
data.nextScreenId = Math.max(ns, data.nextScreenId || 1);
data.nextRegionId = Math.max(nr, data.nextRegionId || REGION_BASE);
delete data.nextId;
const next = `화면 ${data.nextScreenId} · 영역 ${data.nextRegionId}`;

fs.writeFileSync(file, JSON.stringify(data, null, 2) + "\n");
if (issued.length) {
  console.log(`[ids] ${issued.length}개 발급, 다음 번호 ${next}`);
  for (const line of issued) console.log("  " + line);
} else {
  console.log(`[ids] 발급할 id 없음, 다음 번호 ${next}`);
}
