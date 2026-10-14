#!/usr/bin/env node
/**
 * pack.js — screen-writer 한 명이 맡은 화면에 필요한 것만 **파일 하나**로 묶는다(작업 묶음).
 * 에이전트가 지침·규칙·조각 문서·screens.json·flow.json을 하나씩 읽고 스스로 점검하느라 쓰던 시간을 없앤다
 * (셀프 테스트: 3장에 도구 호출 15~38회 · 4~8분 → 팩 하나 읽고 화면마다 한 번씩 쓰기).
 *
 *   node scripts/pack.js runs/<p> --screens a,b,c [--concept <id>] [--name <팩 이름>]
 *   → runs/<p>/packs/<팩 이름>.md 를 쓰고 경로를 출력한다. 프롬프트에 PACK=<경로>.
 *
 * 담는 것: 할 일 · 규칙 요약 · 위계 · 영역 모양 → 부품 표(00-rules.md 9번과 같은 표) · 부품 표(05-parts.md) ·
 *          쓸 수 있는 클래스 · 자주 쓰는 HTML 몇 개 · 아이콘 목록 ·
 *          화면마다(이름 · 목적(goal) · 겪는 문제(problem) · 쓸 사실(data → facts 문장) · 덜어낼 것(defer) · 1순위 ·
 *          상태 · 영역(순위 · 모양 · 들어갈 것) · 눌러야 하는 버튼과 그 문구).
 * 배치는 화면 패턴(pattern — KRDS 이름)이 아니라 영역 모양(regions[].form)이 정한다.
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
10-1. **안내·예외**: 글자 칸(input·textarea)에는 화면별 메모의 글자 수로 \`maxlength\`(필요하면 \`minlength\`) — 완성본에서 '3/20'이 보인다. 그 자리에서 바뀌는 버튼의 \`data-stay\`는 무엇이 됐는지 한 문장, 실패·오류 안내면 \`data-stay-tone="danger"\`. 지우기·삭제처럼 되돌릴 수 없는 버튼은 바로 끝내지 않고 확인 창(갈래)을 연다.
11. **읽을 것은 이 파일 하나뿐. 화면마다 Write 한 번. 쓴 뒤 다시 열어 점검하지 않는다** — 메인이 expand·lint로 본다. 다른 파일(다른 runs/*, 패턴·조각 문서)은 열지 않는다.`;

// ---------- 부품 표 (05-parts.md에서 그대로) ----------
const parts = read(path.join(ROOT, "packages/web/snippets/05-parts.md"));
const partsTable = (parts.split("## 부품")[1] || "").split("## 예")[0].trim();

// ---------- 모바일 (screens.json platform: "mobile") — web 위에 겹친다 ----------
const MOBILE = S.platform === "mobile";
const mobileDoc = (f) => { const p = path.join(ROOT, "packages/mobile/snippets", f); return MOBILE && fs.existsSync(p) ? read(p) : ""; };
const section = (md, head) => ((md.split(head)[1] || "").split(/\n## /)[0] || "").trim();
const mobileRules = section(mobileDoc("00-rules.md"), "## 반드시 지킬 것");
const mobileParts = mobileDoc("05-parts.md");
const mobilePartsTable = [section(mobileParts, "## 부품\n"), section(mobileParts, "## 부품이 없는 모바일 조각 (HTML 그대로)")].filter(Boolean).join("\n\n");

// ---------- 쓸 수 있는 클래스 (components에서 자동) ----------
const PLATFORM = require("./platform.js");
const classLines = PLATFORM.files(S.platform || "web", "components", ".css").map((f) => {
  const names = [...new Set([...read(f.path).matchAll(/^\.([a-z][a-z0-9-]*)/gm)].map((m) => m[1]))]
    .filter((n) => !/^(app|topnav|sidebar|nav|toast|tooltip|skeleton|dropdown|popover|kbd|tabbar|toptabs|sheet)/.test(n))
    .filter((n) => !MOBILE || !/^(split|table|week-grid|wg-|grid-3|grid-4|form-actions|form-grid)/.test(n));
  return names.length ? `- ${f.layer === "web" ? "" : f.layer + "/"}${f.file.replace(/^\d+-|\.css$/g, "")}: ${names.join(" ")}` : "";
}).filter(Boolean);
const EXAMPLES = `
\`\`\`html
<div class="grid-3">…카드 3개…</div>            <div class="row gap-2">…</div>  <div class="row-between">…</div>  <div class="stack">…묶음 안…</div>
<div class="stack-group">…날짜 묶음·카드 묶음끼리…</div>  <div class="stack-page">…큰 덩어리끼리…</div>
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

const MOBILE_EXAMPLES = `
\`\`\`html
<x-page-header eyebrow="다음 수업 · 10월 13일(화)" title="오늘 20:00 리포머 중급" desc="숨결필라테스 망원 · 오지훈 강사"></x-page-header>
<x-card>…</x-card>  <x-section title="취소 규정">…목록·줄·문장 (안에 x-card 금지)…</x-section>   ← 회색 바탕 위 흰 판을 12px 간격으로 쌓는다
<div class="row-between">…</div>  <div class="stack gap-1">…</div>  <div class="grid-2">숫자 둘</div>
<p class="big-num">잔여 3회 <small>/ 10</small></p>   <p class="text-sm text-2">회색 한 줄</p>
<div class="segmented w-full"><button class="segmented-item active">예정 2</button><button class="segmented-item">대기 중 2</button></div>
<div class="chip-group"><button class="chip active">기구 필라테스</button><button class="chip">매트</button></div>
<label class="switch"><input type="checkbox" checked>알람을 끄면 측정도 끝내기</label>   ← 켜고 끄는 줄은 이 모양 하나 (input에 클래스를 붙이지 않는다)
<div class="search"><x-icon name="search"/><input class="input" type="search" placeholder="스튜디오 이름으로 찾기"></div>
<div class="field"><label class="field-label">이름</label><input class="input" value="예시 값"></div>
<div class="day-strip"><button class="day active"><span class="day-name">수</span><span class="day-num">14</span></button>…</div>
<x-item title="…" sub="…" badge="확정 필요" badge-tone="warning"><x-icon name="chevron-right" size="sm"/></x-item>   ← 눌러서 들어가는 줄
<div class="bottom-cta" data-region="…"><x-btn variant="primary" data-trigger="…">예약 확정</x-btn></div>   ← 본문 맨 마지막, 화면당 하나
\`\`\`
- 쓰지 않는다: .split · .table · .week-grid · .grid-3 · .grid-4 · .form-actions · .page-actions의 primary (모바일 규칙 참고).`;

// ---------- 아이콘 ----------
const allow = JSON.parse(read(path.join(ROOT, "packages/core/icons/allowlist.json")));
const proj = fs.existsSync(path.join(runDir, "icons.json")) ? JSON.parse(read(path.join(runDir, "icons.json"))) : {};
const icons = [...new Set([...Object.entries(allow), ...Object.entries(proj)].filter(([k]) => !k.startsWith("_")).map(([, v]) => v))].sort();

// ---------- 영역 모양 → 부품 (regions[].form — 00-rules.md 9번 표와 같은 표) ----------
// 배치는 영역 모양이 정한다. 00-rules.md(모바일은 모바일 00-rules.md)에 `| hero | … |` 줄이 있으면 그 말을 쓴다 — 표는 한 곳에서 고친다
const FORM_KEYS = ["hero", "list", "table", "calendar", "form", "timeline", "cards", "stat-row", "split", "actions"];
const hasCalendarSnippet = fs.existsSync(path.join(runDir, "snippets"));
const FORMS_WEB = {
  hero: "한 칸 큰 글 — 영역 가로 전체. `.t-display` 1순위 문장 → `.t-subtitle` 넘친 한 줄 → 사실 한두 줄(`.t-body`) → 버튼(주 버튼은 여기 또는 actions 줄). `.split`·`.grid-*`·`.card`·옆 숫자 칸(`.stat`) 금지",
  list: "목록 — `<x-list>` 안 `<x-item>` 한 줄씩(아래 '한 줄 모양'). 줄 안에 `.t-title`·`.card-title` 금지",
  table: "표 — `.table-wrap` 안 `<table class=\"table\">` 하나. 머리줄은 짧은 말, 칸 글자는 본문 크기(`.t-title` 금지)",
  calendar: `달력 — 칸을 손으로 쓰지 않는다. ${hasCalendarSnippet ? "RUN/snippets/의 calendar-*.html을 그대로 붙인다" : "며칠만 보이면 `.day-strip`(날짜 띠)"}. 오늘 · 고른 날 · 일정 있는 날은 색과 함께 굵기 · 표식으로`,
  form: "입력 — `.field`(라벨 + 입력칸) 한 열 묶음. 주 버튼은 폼 끝 버튼 줄(actions 영역이 있으면 그 영역, 없으면 이 영역 맨 아래 `.form-actions`)",
  timeline: "타임라인 — `.timeline` 안 `.timeline-item`(시간 `.timeline-time` · 점 `.timeline-dot` · 내용 `.timeline-content`), 날짜 머리는 `.timeline-date`(아래 '한 줄 모양'). 시간이 없으면 시간 칸을 뺀다. `.timeline-compact`(점 · 내용 두 칸)에는 `.timeline-time`을 넣지 않는다 — 넣으면 좁은 칸에 글자가 한 자씩 세로로 쌓인다. 시간은 `.timeline-title` 안 글자로",
  cards: "카드 — `.grid-2`·`.grid-3` 안 `<x-card>` 2~6장. 카드 한 장에 제목 하나만(`.card-title` **또는** 굵은 본문 — 둘 다 쓰지 않는다). 날짜 같은 머리글은 `.t-caption`",
  "stat-row": "숫자 줄 — `.stat-row` 안 `<x-stat>` 2~4개. 1순위 영역에는 쓰지 않는다",
  actions: "주 행동 줄 — 폼 끝 버튼 줄 `.form-actions`(취소 data-back · 주 버튼 하나). 웹의 주 버튼은 1순위 hero 안 또는 이 줄 — 둘 중 한 곳",
  split: "목록-상세 — `.split`(왼쪽 `.split-list` 목록, 오른쪽 `.split-detail` 고른 것의 상세). 고르는 화면에만, 1순위 영역에는 쓰지 않는다",
};
// 모바일은 한 열 · 흰 판 쌓기 · 주 행동은 맨 끝 꽉 찬 버튼 — web과 다른 것만
const FORMS_MOBILE = {
  hero: "한 칸 큰 글 — 본문 맨 위 판 하나(`<x-section>`, 카드 · 숫자 칸 없이): `.t-display` 1순위 문장 → `.t-subtitle` 넘친 한 줄 → 사실 한두 줄. **판 안에 주 버튼을 두지 않는다**(주 버튼은 actions 영역)",
  list: "목록 — `<x-card flush><x-list>` 안 `<x-item>` 한 줄씩(아래 '한 줄 모양'), 눌러서 들어가는 줄은 chevron-right",
  table: "표 — 모바일은 `.table`을 쓰지 않는다. 항목 하나 = `<x-item>` 한 줄(값 두세 개는 sub에)",
  calendar: `달력 — \`<x-card>\` 안 날짜 띠 \`.day-strip\` + 그날 목록${hasCalendarSnippet ? "(한 달을 다 보여야 하면 RUN/snippets/의 calendar-*.html)" : ""}`,
  form: "입력 — `<x-section>` 판마다 `.field`. 주 버튼은 이 영역이 아니라 actions 영역(`.bottom-cta`). `.form-actions` 쓰지 않는다",
  timeline: "타임라인 — `<x-section>` 판 안 `.timeline` 한 열(시간 `.timeline-time` · 점 `.timeline-dot` · 내용 `.timeline-content`). `.timeline-compact`(점 · 내용 두 칸)에는 `.timeline-time`을 넣지 않는다 — 넣으면 좁은 칸에 글자가 한 자씩 세로로 쌓인다. 시간은 `.timeline-title` 안 글자로",
  cards: "카드 — `<x-card>`를 한 열로 쌓는다(`.grid-3` 금지). 카드 한 장에 제목 하나만",
  "stat-row": "숫자 — `.grid-2` 안 숫자 둘까지(`.big-num`). 1순위 영역에는 쓰지 않는다",
  actions: "주 행동 줄 — 본문 마지막 영역(2순위). `<div class=\"bottom-cta\" data-region=\"<이 영역 key>\">` 안 `<x-btn variant=\"primary\">`(`.btn-primary`) 꽉 찬 버튼 하나. 보조 버튼이 꼭 필요하면 그 아래 secondary 하나. 흐름에서 주 버튼을 누르는 영역(region)이 이 key",
  split: "목록-상세 — 모바일은 `.split` 금지. 목록 화면과 자세히 화면 두 장으로 나눈다(이 영역은 목록만)",
};
function formRows(md) {
  const rows = {};
  for (const line of (md || "").split("\n")) {
    const m = /^\|\s*`?([a-z-]+)`?\s*\|(.+)\|\s*$/.exec(line);
    if (m && FORM_KEYS.includes(m[1])) rows[m[1]] = m[2].split("|").map((c) => c.trim()).filter(Boolean).join(" — ");
  }
  return rows;
}
// 모양마다 지킬 규칙 — 문장은 rules.json의 says를 그대로
const rulesFile = path.join(ROOT, "packages/core/schema/rules.json");
const SAYS = new Map(fs.existsSync(rulesFile) ? (JSON.parse(read(rulesFile)).rules || []).map((r) => [r.id, r.says]) : []);
const FORM_RULES = { hero: ["rank1-hero"], list: ["repeat-unit"], timeline: ["repeat-unit"], table: ["table-plain", "table-empty-dash"], calendar: ["calendar-state"] };
const FORMS = { ...FORMS_WEB, ...formRows(read(path.join(ROOT, "packages/web/snippets/00-rules.md"))), ...(MOBILE ? { ...FORMS_MOBILE, ...formRows(mobileDoc("00-rules.md")) } : {}) };
const formTable = FORM_KEYS.map((k) => {
  const rules = (FORM_RULES[k] || []).filter((id) => SAYS.has(id)).map((id) => `${id}: ${SAYS.get(id)}`);
  return `| \`${k}\` | ${(FORMS[k] + (rules.length ? ` (규칙 ${rules.join(" / ")})` : "")).replace(/\|/g, "\\|")} |`;
});
// 한 줄 모양(repeat-unit) — 목록 · 타임라인 한 줄의 자리 순서: 상태 → 제목 → 설명 → 기간 → 행동 → 태그
const REPEAT = `
\`\`\`html
<x-list><x-item badge="확정" badge-tone="success" title="10월 15일(수) 워크숍 장소 확정" sub="3층 회의실 A · 오전 10:00~12:00"><x-btn size="sm" data-stay="…">…</x-btn></x-item>…</x-list>
<div class="timeline">
  <div class="timeline-date">10월 15일 (수) · 오늘</div>
  <div class="timeline-item">
    <span class="timeline-time">09:30</span>
    <span class="timeline-dot dot-success"></span>
    <div class="timeline-content"><div class="timeline-title">주간 계획 회의 <span class="badge badge-success">완료</span></div><p class="timeline-desc">3층 회의실 B · 참석 6명</p></div>
  </div>
</div>
\`\`\`
- 모든 줄이 같은 순서, 중요한 항목이 위. 뼈대 칸(\`.timeline-time\`·\`.timeline-dot\`·\`.timeline-content\`)에 배치 클래스를 붙이지 않는다. 시간 칸 없는 \`.timeline-compact\`에는 \`.timeline-time\`을 쓰지 않는다.`;

// ---------- 화면별 ----------
// 메뉴 없는 화면 — KRDS 이름 '처음 시작'과 옛 값 onboarding을 같이 본다
const NO_MENU_PATTERNS = ["처음 시작", "onboarding"];
const facts = S.facts && !Array.isArray(S.facts) && typeof S.facts === "object" ? S.facts : {};
const asList = (v) => (Array.isArray(v) ? v : v ? [v] : []);
const STATE = { "first-run": "처음 켰을 때 — <x-empty>로 비워 둔다", empty: "데이터 없을 때 — <x-empty>로 비워 둔다", input: "입력할 때 — 입력칸에 예시 값을 채운다",
  error: "오류일 때 — 원래 화면(variantOf)과 같은 배치에서, 잘못된 입력칸에 .field.is-error + 고치는 방법 한 문장(.field-error), 또는 위쪽 .banner.banner-danger 한 줄. 주 버튼은 그대로 두거나 disabled",
  success: "완료됐을 때 — 원래 화면(variantOf)과 같은 배치에서, 위쪽 .banner.banner-success 한 줄(무엇이 끝났고 다음에 무엇을 하면 되는지) 또는 끝난 항목에 성공 배지. 다음 행동 버튼 하나" };
// 모바일 셸 모양 (expand.js wrapMobile과 같은 판단) — 작성자가 첫머리를 어떻게 쓸지 정하려고
function mobileShell(s) {
  const role = (S.roles || []).find((r) => r.key === s.role) || (S.roles || [])[0] || { nav: [] };
  const isTab = (role.nav || []).some((n) => n.slug === s.slug || (s.variantOf && n.slug === s.variantOf));
  if (s.shell === "none" || NO_MENU_PATTERNS.includes(s.pattern) || (C && C.shell === "none")) return "메뉴 없는 한 장";
  return isTab && s.shell !== "back" ? "탭 화면(아래 탭이 붙는다 — 큰 제목으로 시작)" : "아래 화면(위에 뒤로 · 화면 이름 줄이 붙는다 — 화면 이름을 본문에 다시 쓰지 않고 eyebrow + 대상 이름으로 시작)";
}
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
  // 1턴(시안 단계)만 concepts/<id>/에 쓴다. 2턴부터 --concept는 시안의 메뉴 구조·첫 화면·밀도를 담기 위한 것 — 화면은 screens/로
  const file = concept && S.stage === "concept" ? `concepts/${concept}/${slug}.html` : s.file || `screens/${slug}.html`;
  const role = (S.roles || []).find((r) => r.key === s.role) || {};
  // data = facts 이름표 목록 → 사실 문장으로 푼다(옛 모양 문장은 그대로)
  const data = Array.isArray(s.data) ? s.data.map((k) => `  - ${facts[k] || `${k} (facts에 없는 이름표 — 쓰지 않는다)`}`) : s.data ? [`  - ${s.data}`] : [];
  const defer = asList(s.defer);
  const actionsKey = ((s.regions || []).find((r) => r.form === "actions") || {}).key;
  // 영역 content에 facts 이름표가 있으면 문장으로
  const content = (c) => c.split(/\s*·\s*/).map((x) => facts[x] || x).join(" · ");
  return [
    `### ${s.name} — \`${slug}\` → RUN/${file}`,
    `- 누가: ${role.label || s.role || "모두"}${role.goal ? ` — ${role.goal}` : ""}`,
    `- 목적: ${s.goal || s.purpose || ""}`,
    s.problem ? `- 겪는 문제: ${s.problem} — 1순위 문장은 이 걱정에 답하는 사실로` : "",
    s.pattern ? `- 화면 패턴: ${s.pattern}${MOBILE && !s.overlayOf ? ` · ${mobileShell(s)}` : ""} — 배치는 아래 영역 모양이 정한다` : MOBILE && !s.overlayOf ? `- 화면 틀: ${mobileShell(s)}` : "",
    s.overlayOf ? `- **뜨는 창**: 파일 전체가 \`<x-modal title="…">본문 <div class="modal-footer">버튼</div></x-modal>\` 하나. 완료 버튼도 창을 닫으면 data-back(흐름에 있으면 data-trigger).${MOBILE ? " 모바일은 아래에서 올라오는 창으로 펼쳐진다 — 제목은 질문·결과 한 문장, desc 회색 1~2줄, 바닥줄 = primary 하나 + 돌아가기(data-back)." : ""}` : "",
    s.state ? `- 상태: ${STATE[s.state] || s.state}${s.variantOf ? ` (원래 화면: ${(bySlug.get(s.variantOf) || {}).name || s.variantOf})` : ""}` : "",
    s.emphasize ? `- **크게 할 내용**(\`<p class="t-display">\` — 제목 태그 h1~h3이 아니라 문장으로, .t-display는 이 문장에만): ${s.emphasize}` : "",
    s.emphasize2 ? `- **바로 아래 한 줄**(\`.t-subtitle\` — 큰 글자 아님, 굵기로): ${s.emphasize2}` : "",
    data.length ? `- 쓸 사실: 이것만 쓴다 — 없는 이름·시간·할 일을 지어내지 않는다\n${data.join("\n")}` : "",
    defer.length ? `- 덜어낼 것: 이 화면에 넣지 않는다(자세히 · 다른 화면으로 미룬다)\n${defer.map((x) => `  - ${x}`).join("\n")}` : "",
    s.focus ? `- **1순위 한 가지**: \`${s.focus}\` — 화면 맨 위. 1순위 문장(크게 할 내용) → 넘친 한 줄 → 사실${MOBILE ? "" : " → 버튼"} 차례로 시작하고, 이 영역 모양이 hero가 아니면(입력 등) 그 아래에 그 모양을 놓는다` : "",
    MOBILE && !s.overlayOf ? `- 주 버튼은 actions 영역에: ${actionsKey ? `\`${actionsKey}\` — 본문 마지막 \`.bottom-cta\` 꽉 찬 버튼 하나` : "이 화면엔 actions 영역이 없다 — 주 버튼이 필요하면 본문 맨 끝 `.bottom-cta`(hero 판 밖)"}. 1순위 hero 판 안에는 두지 않는다` : "",
    `- 영역(${(s.regions || []).length}개, 모두 한 번씩):`,
    ...(s.regions || []).map((r) => `  - \`${r.key}\`${r.level ? ` **[${r.level}순위]**` : ""}${r.form ? ` **모양 ${r.form}**` : " (모양 없음 — 영역 모양 표에서 가장 가까운 것)"} — ${r.label}: ${r.why || ""}${r.content ? `\n    - 들어갈 것(이것만): ${content(r.content)}` : ""}${(r.stays || []).length ? `\n    - 그 자리에서 바뀌는 버튼(이것만 data-stay): ${r.stays.map((x) => `'${x.label}' → data-stay="${x.msg}"`).join(", ")}` : ""}`),
    trig.length ? `- 눌러야 하는 버튼:\n${trig.join("\n")}` : `- 눌러야 하는 버튼: 없음(글자 버튼은 data-back·data-stay)`,
  ].filter(Boolean).join("\n");
});

const shellNote = C ? `시안 ${C.id.toUpperCase()} "${C.name}" — 메뉴 구조 ${C.shell}${MOBILE ? (C.shell === "top" ? "(위 알약 탭 메뉴)" : C.shell === "none" ? "(메뉴 없음)" : "(아래 탭 메뉴)") : C.shell === "top" ? "(위쪽 탭 메뉴 — 본문이 가운데 좁게 놓인다)" : C.shell === "rail" ? "(아이콘 메뉴 — 본문 폭이 넓다)" : ""} · 첫 화면 ${C.home || "-"} · 밀도 ${C.density || "-"}${MOBILE ? " — 메뉴 모양과 상관없이 모바일 화면이다(모바일 규칙만 따른다, 주 버튼은 본문 맨 끝 .bottom-cta)" : ""}` : "";
const out = `# 작업 묶음 — ${slugs.join(", ")}${C ? ` (시안 ${C.id})` : ""}

**이 파일만 읽고, 아래 화면을 하나씩 Write 한 번으로 쓴 뒤 끝낸다.** 점검은 메인이 한다. RUN = ${runDir}
${shellNote ? "\n" + shellNote + "\n" : ""}
${MOBILE ? `## 모바일 규칙 (이 묶음은 모바일 390×844 화면 — 메뉴가 아래 탭 · 위 탭 · 없음 어느 것이든 이 규칙을 따른다. 웹 배치는 쓰지 않는다)\n${mobileRules}\n\n## 조각 쓰는 법 (web · mobile 같음 — 배치는 위 모바일 규칙)` : "## 규칙"}
${RULES.trim()}

## 위계 (화면마다 정해진 1순위 · 영역 순위를 따른다 — 어기면 lint가 잡는다)
- 글자는 역할 클래스로 고른다: \`.t-display\`(1순위 문장) · \`.t-title\`(제목) · \`.t-subtitle\`(목록 한 줄 이름) · \`.t-body\`(본문) · \`.t-caption\`(날짜·상태·보조). \`.text-lg\`·\`.text-xl\`로 크기를 따로 키우지 않는다.
- **1순위 영역에만** \`.t-display\` 하나. 2순위는 \`.t-title\`·\`.t-body\`. 3순위는 \`.t-caption\`·글자 링크 모양 버튼(\`btn-ghost\`)만, 목록이 길면 3줄 + '더 보기'.
- 영역 안에는 '들어갈 것'에 적힌 것만 둔다. 요약 숫자·필터·일정·안내 문장을 스스로 덧붙이지 않는다.
- 글자 버튼은 '눌러야 하는 버튼' + 영역의 '그 자리에서 바뀌는 버튼' + 되돌아가기(data-back)만. 그 밖의 버튼을 만들지 않는다.
- 화면 하나에 강조 버튼 1개, 영역 하나에 보조 버튼 최대 2개. 나란히 놓는 버튼은 2개까지.${MOBILE ? " 모바일의 강조 버튼은 본문 맨 끝 actions 영역의 `.bottom-cta` 하나다." : ""}
- **세로 간격은 숫자로 고르지 않는다**: 묶음 안 = \`.stack\`, 묶음 사이(날짜 묶음·카드 묶음끼리) = \`.stack-group\`, 큰 덩어리 사이 = \`.stack-page\`. \`.stack\`에 \`gap-4\`·\`gap-6\`을 붙이지 않는다(\`gap-1~3\`은 한 줄 안의 작은 간격에만).
- 구분은 단계로: 같은 묶음 안 = 얇은 선, 묶음 사이 = 여백, 의미가 바뀌는 경계선은 화면에 한두 번.
- 상태(확정·바뀜·위험)는 색만으로 말하지 않는다 — 아이콘·글자를 함께.

## 영역 모양 → 부품 (배치는 화면 패턴이 아니라 영역 모양이 정한다)
1순위(focus · level 1) 영역은 화면 맨 위 \`hero\` — 1순위 문장 → 넘친 한 줄 → 사실${MOBILE ? ". **모바일은 hero 판 안에 주 버튼을 두지 않는다** — 주 버튼은 본문 마지막 \`actions\` 영역(.bottom-cta)" : " → 버튼(주 버튼은 hero 안 또는 폼 끝 \`actions\` 줄 — 한 곳)"}. 나머지 영역은 영역 목록 차례대로 그 아래에 놓는다.

| 모양 | 쓸 부품 |
|---|---|
${formTable.join("\n")}

한 줄 모양(목록 · 타임라인 — 상태 → 제목 → 설명 → 기간 → 행동 → 태그):
${REPEAT.trim()}

## 부품
${partsTable}
${MOBILE && mobilePartsTable ? `\n### 모바일에서 달라지는 부품\n${mobilePartsTable}\n` : ""}
## 쓸 수 있는 클래스
${classLines.join("\n")}
${(MOBILE ? MOBILE_EXAMPLES : EXAMPLES).trim()}

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
