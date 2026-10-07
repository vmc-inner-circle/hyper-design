#!/usr/bin/env node
/**
 * calendar.js — 월 달력 격자 HTML(.calendar-month 조각)을 만든다.
 * 손으로 35~42칸을 쓰는 시간을 없애기 위한 도구. 메인이 실행해 결과 파일 경로를 screen-writer에게 넘긴다.
 *
 *   node scripts/calendar.js 2026-10 [--today 2026-09-27] [--selected 2026-10-15]
 *        [--event 2026-10-15="워크숍 1일차":success] [--event 2026-10-16="워크숍 2일차":neutral] …
 *        [--out runs/<p>/snippets/calendar-2026-10.html]
 *
 * 이벤트 상태: success(확정) · warning(변경됨) · neutral(후보). 하루 최대 2개, 넘치면 "+n".
 * 출력 클래스는 packages/web/snippets/50-data.md의 .calendar-month 조각과 동일하다.
 */
const fs = require("fs");
const path = require("path");

const args = process.argv.slice(2);
const ym = args.find((a) => /^\d{4}-\d{2}$/.test(a));
if (!ym) { console.error("usage: node scripts/calendar.js YYYY-MM [--today D] [--selected D] [--event D=제목:상태]… [--out path]"); process.exit(2); }
const opt = (n) => { const i = args.indexOf(`--${n}`); return i >= 0 ? args[i + 1] : null; };
const today = opt("today") || new Date().toISOString().slice(0, 10);
const selected = opt("selected");
const out = opt("out");
const events = {};
args.forEach((a, i) => {
  if (a !== "--event") return;
  const m = /^(\d{4}-\d{2}-\d{2})="?([^":]+)"?(?::(success|warning|neutral|danger|info))?$/.exec(args[i + 1] || "");
  if (!m) { console.error(`--event 형식 오류: ${args[i + 1]}`); process.exit(2); }
  (events[m[1]] ||= []).push({ title: m[2], state: m[3] || "neutral" });
});

const [Y, M] = ym.split("-").map(Number);
const first = new Date(Date.UTC(Y, M - 1, 1));
const startDow = first.getUTCDay(); // 0=일
const daysIn = new Date(Date.UTC(Y, M, 0)).getUTCDate();
const prevDays = new Date(Date.UTC(Y, M - 1, 0)).getUTCDate();
const totalCells = Math.ceil((startDow + daysIn) / 7) * 7;
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const pad = (n) => String(n).padStart(2, "0");

const weekdays = ["일", "월", "화", "수", "목", "금", "토"].map((d) => `      <div class="calendar-weekday">${d}</div>`).join("\n");
const cells = [];
for (let i = 0; i < totalCells; i++) {
  let d, other = false, iso;
  if (i < startDow) { d = prevDays - startDow + i + 1; other = true; iso = null; }
  else if (i - startDow < daysIn) { d = i - startDow + 1; iso = `${Y}-${pad(M)}-${pad(d)}`; }
  else { d = i - startDow - daysIn + 1; other = true; iso = null; }
  const cls = ["calendar-day"];
  if (other) cls.push("is-other-month");
  if (iso && iso === today) cls.push("today");
  if (iso && iso === selected) cls.push("selected");
  const evs = iso ? events[iso] || [] : [];
  if (evs.length) cls.push("has-event");
  const shown = evs.slice(0, 2).map((e) => `        <span class="calendar-event is-${e.state}">${esc(e.title)}</span>`);
  if (evs.length > 2) shown.push(`        <span class="calendar-more">+${evs.length - 2}</span>`);
  cells.push(`      <div class="${cls.join(" ")}"${iso ? ` data-date="${iso}"` : ""}>\n        <span class="calendar-daynum">${d}</span>\n${shown.join("\n")}${shown.length ? "\n" : ""}      </div>`);
}

const html = `<div class="calendar calendar-month">
  <div class="calendar-header">
    <div class="calendar-title">${Y}년 ${M}월</div>
    <div class="calendar-nav">
      <button class="btn btn-icon btn-ghost btn-sm" type="button" aria-label="이전 달"><svg class="icon-sm" aria-hidden="true"><use href="#i-chevron-left"/></svg></button>
      <button class="btn btn-icon btn-ghost btn-sm" type="button" aria-label="다음 달"><svg class="icon-sm" aria-hidden="true"><use href="#i-chevron-right"/></svg></button>
    </div>
  </div>
  <div class="calendar-grid">
${weekdays}
${cells.join("\n")}
  </div>
</div>
`;

if (out) { fs.mkdirSync(path.dirname(out), { recursive: true }); fs.writeFileSync(out, html); console.log(`[calendar] ${ym} → ${out} (${totalCells}칸, 이벤트 ${Object.keys(events).length}일)`); }
else process.stdout.write(html);
