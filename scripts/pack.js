#!/usr/bin/env node
/**
 * pack.js — screen-writer 한 명이 맡은 화면에 필요한 것만 **파일 하나**로 묶는다(작업 묶음).
 * 에이전트가 지침·규칙·조각 문서·screens.json·flow.json을 하나씩 읽고 스스로 점검하느라 쓰던 시간을 없앤다
 * (셀프 테스트: 3장에 도구 호출 15~38회 · 4~8분 → 팩 하나 읽고 화면마다 한 번씩 쓰기).
 *
 *   node scripts/pack.js runs/<p> --screens a,b,c [--concept <id>] [--name <팩 이름>]
 *   → runs/<p>/packs/<팩 이름>.md 를 쓰고 경로를 출력한다. 프롬프트에 PACK=<경로>.
 *
 * 담는 것: 할 일 · 규칙 요약 · 부품 표(05-parts.md) · 쓸 수 있는 클래스 · 자주 쓰는 HTML 몇 개 · 아이콘 목록 ·
 *          화면마다(이름·목적·배치 힌트·상태·영역·눌러야 하는 버튼과 그 문구·나머지 버튼 규칙).
 * DOMAIN(더미 데이터)과 화면별 메모는 메인이 프롬프트에 직접 쓴다.
 */
const fs = require("fs");
const path = require("path");
const ROOT = path.resolve(__dirname, "..");
const args = process.argv.slice(2);
const runDir = args.find((a) => !a.startsWith("--"));
const opt = (n) => { const i = args.indexOf("--" + n); return i >= 0 ? args[i + 1] : null; };
if (!runDir || !opt("screens")) { console.error("usage: node scripts/pack.js runs/<p> --screens a,b,c [--concept id] [--name name]"); process.exit(2); }
const read = (p) => fs.readFileSync(p, "utf8");
const S = JSON.parse(read(path.join(runDir, "screens.json")));
const F = JSON.parse(read(path.join(runDir, "flow.json")));
const slugs = opt("screens").split(",").map((x) => x.trim()).filter(Boolean);
const concept = opt("concept");
const C = concept ? (S.concepts || []).find((c) => c.id === concept) : null;
const bySlug = new Map((S.screens || []).map((s) => [s.slug, s]));

// ---------- 규칙 요약 (00-rules.md의 핵심 — 바꾸면 여기도) ----------
const RULES = `
1. 파일 하나 = \`<main class="content">…</main>\` 하나. **상단바·메뉴·사이드바는 쓰지 않는다**(expand.js가 붙인다). 뜨는 창 화면은 \`<x-modal …>…</x-modal>\` 하나(뒷 화면은 쓰지 않는다).
2. **짧은 부품 태그를 쓴다**(아래 표). 부품이 없는 구조는 아래 "쓸 수 있는 클래스"의 HTML. 새 클래스·인라인 style·<style>·<script> 금지.
3. **영역**: 화면의 영역 key마다 그 덩어리를 감싸는 요소 하나에 \`data-region="<key>"\`(정확히 한 번씩, 빠짐·남김 없이). 부품에도 붙일 수 있다(\`<x-section data-region="…">\`).
4. **눌러야 하는 버튼**(아래 화면별 목록): 그 영역 안의 버튼 하나에 \`data-trigger="<key>"\`, 버튼 글자는 적힌 문구 그대로.
5. **글자가 있는 나머지 .btn**은 셋 중 하나: 이전 화면으로(취소·닫기·'~로') = \`data-back\` / 그 자리에서 바뀜(삭제·필터·다시 보내기) = \`data-stay="바뀐 뒤 안내 한 문장(해요체)"\` / 같은 일을 하는 버튼이 여러 행에 있으면 첫 행에만 data-trigger, 나머지는 **글자만 똑같이**.
6. 문구는 전부 실제 문구(DOMAIN 값). "버튼"·"텍스트"·Lorem 금지. 목록은 3~5행. 사람을 높여 부를 땐 "님".
7. 상태 표시는 배지로 통일(같은 뜻 = 같은 색). 화면당 primary 버튼은 1개 이하.
8. \`state: first-run·empty\` 화면은 \`<x-empty>\`로 비워 둔다(숫자·목록 금지, primary 버튼 하나). \`state: input\`은 입력칸에 예시 값.
9. 체크 목록·출석처럼 "보고 체크"하는 것은 체크박스 대신 아이콘: 한 것 \`<x-icon name="square-check" tone="success"/>\`, 안 한 것 \`<x-icon name="square" tone="muted"/>\`.
10. 아이콘 이름은 아래 목록에 있는 것만.
11. **읽을 것은 이 파일 하나뿐. 화면마다 Write 한 번. 쓴 뒤 다시 열어 점검하지 않는다** — 메인이 expand·lint로 본다. 다른 파일(다른 runs/*, 패턴·조각 문서)은 열지 않는다.`;

// ---------- 부품 표 (05-parts.md에서 그대로) ----------
const parts = read(path.join(ROOT, "packages/web/snippets/05-parts.md"));
const partsTable = (parts.split("## 부품")[1] || "").split("## 예")[0].trim();

// ---------- 쓸 수 있는 클래스 (components에서 자동) ----------
const compDir = path.join(ROOT, "packages", S.platform || "web", "components");
const classLines = fs.readdirSync(compDir).filter((f) => f.endsWith(".css")).sort().map((f) => {
  const names = [...new Set([...read(path.join(compDir, f)).matchAll(/^\.([a-z][a-z0-9-]*)/gm)].map((m) => m[1]))]
    .filter((n) => !/^(app|topnav|sidebar|nav|toast|tooltip|skeleton|dropdown|popover|kbd)/.test(n));
  return `- ${f.replace(/^\d+-|\.css$/g, "")}: ${names.join(" ")}`;
});
const EXAMPLES = `
\`\`\`html
<div class="grid-3">…카드 3개…</div>            <div class="row gap-2">…</div>  <div class="row-between">…</div>  <div class="stack gap-3">…</div>
<div class="split"><div class="split-list">목록</div><div class="split-detail">자세히</div></div>
<div class="field"><label class="field-label">이름</label><input class="input" value="예시 값"></div>
<div class="field"><label class="field-label">담당</label><div class="select-wrap"><select class="select"><option>예시</option></select></div></div>
<label class="switch"><input type="checkbox" checked>매주 반복</label>
<div class="chip-group"><button class="chip active">전체</button><button class="chip">예시</button></div>
<div class="segmented"><button class="segmented-item active">월</button><button class="segmented-item">화</button></div>
<div class="banner banner-warning"><x-icon name="triangle-alert"/><div class="banner-body">안내 문장</div></div>
<div class="progress-row"><div class="progress progress-warning"><div class="progress-bar w-60"></div></div><span class="progress-num">3/5</span></div>  ← 폭은 w-10 … w-100 (10 단위)
<div class="table-wrap"><table class="table"><thead><tr><th>이름</th></tr></thead><tbody><tr><td>값</td></tr></tbody></table></div>
<ol class="steps"><li class="step done"><span class="step-num"><x-icon name="check" size="sm"/></span><span class="step-label">1단계</span></li><li class="step current"><span class="step-num"></span><span class="step-label">2단계</span></li></ol>
<div class="toolbar">…검색·필터·버튼…</div>
\`\`\`
- 주간 시간표는 \`.week-grid\`(요일 7열 × 시간 줄 — \`.wg-corner\` + \`.wg-day\`×7, 줄마다 \`.wg-time\` + \`.wg-cell\`×7, 칸 안 \`<button class="wg-slot is-open|is-almost|is-full|is-mine"><span class="wg-slot-title">…</span><span class="wg-slot-meta">…</span></button>\`, 오늘 열은 \`.wg-day.today\` + \`.wg-cell.today\`). 7열 표(.table)로 만들지 않는다.
- 달력은 손으로 쓰지 않는다 — ${fs.existsSync(path.join(runDir, "snippets")) ? "RUN/snippets/의 calendar-*.html을 그대로 붙인다(이 파일은 열어도 된다)" : "필요하면 .day-strip으로 대신한다"}.`;

// ---------- 아이콘 ----------
const allow = JSON.parse(read(path.join(ROOT, "packages/core/icons/allowlist.json")));
const proj = fs.existsSync(path.join(runDir, "icons.json")) ? JSON.parse(read(path.join(runDir, "icons.json"))) : {};
const icons = [...new Set([...Object.entries(allow), ...Object.entries(proj)].filter(([k]) => !k.startsWith("_")).map(([, v]) => v))].sort();

// ---------- 화면별 ----------
const LAYOUT = {
  dashboard: "page-header + 위에 요약 숫자(x-stat 3~4개 grid) + 아래 x-section 2~3개(grid-2 가능)",
  "list-detail": "page-header + toolbar(검색·필터·주요 버튼) + .split(왼쪽 목록 / 오른쪽 고른 항목 자세히)",
  form: "page-header + 입력 x-section 2~3개(.field들) + 아래 .form-actions(취소 data-back · primary)",
  board: "page-header + toolbar + 열 3~4개(.grid-3/.grid-4, 열마다 제목과 카드들) 또는 주간 시간표(.week-grid)",
  timeline: "page-header + .timeline(날짜 머리 + 항목) 한 열",
  settings: "page-header + x-section 여러 개(각각 .field·.switch)",
  onboarding: "가운데 좁은 카드 한 장(.content-inner 안 .card): 인사 · 핵심 정보 · primary 버튼 하나",
};
const STATE = { "first-run": "처음 켰을 때 — <x-empty>로 비워 둔다", empty: "데이터 없을 때 — <x-empty>로 비워 둔다", input: "입력할 때 — 입력칸에 예시 값을 채운다" };
const quote = (a) => ((a || "").match(/'([^']+)'/) || [])[1] || "";
const blocks = slugs.map((slug) => {
  const s = bySlug.get(slug);
  if (!s) return `### ${slug}\n(screens.json에 없음)`;
  const outs = [...(F.flows || []).flatMap((f) => (f.steps || []).map((st) => ({ ...st, kind: "흐름 " + (f.name || "") }))),
    ...(F.branches || []).map((b) => ({ ...b, kind: "갈래" }))].filter((x) => x.from === slug && x.trigger);
  const seen = new Set(), trig = outs.filter((x) => !seen.has(x.trigger) && seen.add(x.trigger)).map((x) => {
    const to = bySlug.get(x.to);
    return `  - \`data-trigger="${x.trigger}"\` · 버튼 글자 **'${quote(x.action) || x.action}'** · 영역 \`${x.region}\` 안 → ${to ? to.name : x.to} (${x.kind})`;
  });
  const file = concept ? `concepts/${concept}/${slug}.html` : s.file || `screens/${slug}.html`;
  return [
    `### ${s.name} — \`${slug}\` → RUN/${file}`,
    `- 누가: ${((S.roles || []).find((r) => r.key === s.role) || {}).label || s.role || "모두"} · 목적: ${s.purpose || ""}`,
    s.overlayOf ? `- **뜨는 창**: 파일 전체가 \`<x-modal title="…">본문 <div class="modal-footer">버튼</div></x-modal>\` 하나. 완료 버튼도 창을 닫으면 data-back(흐름에 있으면 data-trigger).` : `- 배치 힌트(${s.pattern || "-"}): ${LAYOUT[s.pattern] || "page-header + x-section들"}`,
    s.state ? `- 상태: ${STATE[s.state] || s.state}` : "",
    `- 영역(${(s.regions || []).length}개, 모두 한 번씩):`,
    ...(s.regions || []).map((r) => `  - \`${r.key}\` — ${r.label}: ${r.why || ""}`),
    trig.length ? `- 눌러야 하는 버튼:\n${trig.join("\n")}` : `- 눌러야 하는 버튼: 없음(글자 버튼은 data-back·data-stay)`,
  ].filter(Boolean).join("\n");
});

const shellNote = C ? `시안 ${C.id.toUpperCase()} "${C.name}" — 메뉴 구조 ${C.shell}${C.shell === "top" ? "(위쪽 탭 메뉴 — 본문이 가운데 좁게 놓인다)" : C.shell === "rail" ? "(아이콘 메뉴 — 본문 폭이 넓다)" : ""} · 첫 화면 ${C.home || "-"} · 밀도 ${C.density || "-"}` : "";
const out = `# 작업 묶음 — ${slugs.join(", ")}${C ? ` (시안 ${C.id})` : ""}

**이 파일만 읽고, 아래 화면을 하나씩 Write 한 번으로 쓴 뒤 끝낸다.** 점검은 메인이 한다. RUN = ${runDir}
${shellNote ? "\n" + shellNote + "\n" : ""}
## 규칙
${RULES.trim()}

## 부품
${partsTable}

## 쓸 수 있는 클래스
${classLines.join("\n")}
${EXAMPLES.trim()}

## 아이콘 (이 이름만)
${icons.join(" ")}

## 화면
${blocks.join("\n\n")}
`;
const dir = path.join(runDir, "packs");
fs.mkdirSync(dir, { recursive: true });
const name = opt("name") || (concept ? concept + "-" : "") + slugs[0];
const file = path.join(dir, name + ".md");
fs.writeFileSync(file, out);
console.log(`[pack] ${file} (${slugs.length}화면, ${(out.length / 1024).toFixed(1)}KB)`);
