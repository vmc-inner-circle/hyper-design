#!/usr/bin/env node
/**
 * ids.js — screens.json의 빠진 id를 이어서 채운다.
 *
 *   node scripts/ids.js runs/<project>
 *
 * 규칙 (docs/harness-design.md §3):
 * - 화면과 영역은 하나의 정수 id 공간을 공유한다.
 * - 이미 있는 id는 절대 바꾸지 않는다. 라운드가 바뀌어도 번호가 유지되어야 한다.
 * - 새 id는 `nextId`부터 이어서 준다. 삭제된 번호는 재사용하지 않는다
 *   (`nextId`는 지금까지 발급된 최대값+1을 항상 기억한다).
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

const used = new Set();
let maxSeen = 0;
for (const s of data.screens || []) {
  if (Number.isInteger(s.id)) { used.add(s.id); maxSeen = Math.max(maxSeen, s.id); }
  for (const r of s.regions || []) {
    if (Number.isInteger(r.id)) { used.add(r.id); maxSeen = Math.max(maxSeen, r.id); }
  }
}

let next = Math.max(Number.isInteger(data.nextId) ? data.nextId : 1, maxSeen + 1);
const issued = [];
const take = () => { while (used.has(next)) next++; used.add(next); return next++; };

for (const s of data.screens || []) {
  if (!Number.isInteger(s.id)) { s.id = take(); issued.push(`${s.id} ← 화면 ${s.slug}`); }
  for (const r of s.regions || []) {
    if (!Number.isInteger(r.id)) { r.id = take(); issued.push(`${r.id} ← ${s.slug} / ${r.key}`); }
  }
}
data.nextId = next;

fs.writeFileSync(file, JSON.stringify(data, null, 2) + "\n");
if (issued.length) {
  console.log(`[ids] ${issued.length}개 발급, nextId=${next}`);
  for (const line of issued) console.log("  " + line);
} else {
  console.log(`[ids] 발급할 id 없음, nextId=${next}`);
}
