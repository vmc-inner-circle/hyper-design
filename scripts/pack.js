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
    .filter((n) => !/^(app|topnav|sidebar|nav|toast|tooltip|skeleton|dropdown|popover|kbd|tabbar|toptabs|sheet)/.test(n));
  return names.length ? `- ${f.layer === "web" ? "" : f.layer + "/"}${f.file.replace(/^\d+-|\.css$/g, "")}: ${names.join(" ")}` : "";
}).filter(Boolean);
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
// 모바일 배치 힌트 — 한 열, 흰 판 쌓기, 주 행동은 아래 꽉 찬 버튼 (packages/mobile/patterns)
const LAYOUT_MOBILE = {
  dashboard: "홈 피드: x-page-header(eyebrow + 큰 제목) → 지금 할 일 x-card 한 장 → x-section 판 2~3개(목록 2~4줄). 숫자는 .grid-2 두 개까지",
  "list-detail": "목록 화면이면: 큰 제목 → x-card 안 검색·칩·나눔 → x-card flush 안 x-list(줄마다 chevron-right). 자세히 화면이면: eyebrow+제목+desc → 정보 판들 → 규정 판 → .bottom-cta. .split 금지",
  form: "x-section 판마다 입력칸(.field) → 확인할 규정 판 → 맨 끝 .bottom-cta(primary 하나). .form-actions 대신",
  board: "나눔 버튼(.segmented.w-full) → x-card 안 날짜 띠(.day-strip) + 안내 한 줄 → 칩 → 그날 목록 x-section. .week-grid·여러 열 금지",
  timeline: "날짜별 x-section 판 하나에 .timeline(시간 · 점 · 내용) 한 열",
  settings: "큰 제목 → 내 정보 x-card → 설정 x-section 판들(.switch · 줄 + chevron-right)",
  onboarding: "메뉴 없는 한 장: x-page-header(eyebrow + 인사 제목 + desc) → 핵심 정보 x-card 하나 → .bottom-cta(primary 하나)",
};
const STATE = { "first-run": "처음 켰을 때 — <x-empty>로 비워 둔다", empty: "데이터 없을 때 — <x-empty>로 비워 둔다", input: "입력할 때 — 입력칸에 예시 값을 채운다",
  error: "오류일 때 — 원래 화면(variantOf)과 같은 배치에서, 잘못된 입력칸에 .field.is-error + 고치는 방법 한 문장(.field-error), 또는 위쪽 .banner.banner-danger 한 줄. 주 버튼은 그대로 두거나 disabled",
  success: "완료됐을 때 — 원래 화면(variantOf)과 같은 배치에서, 위쪽 .banner.banner-success 한 줄(무엇이 끝났고 다음에 무엇을 하면 되는지) 또는 끝난 항목에 성공 배지. 다음 행동 버튼 하나" };
// 모바일 셸 모양 (expand.js wrapMobile과 같은 판단) — 작성자가 첫머리를 어떻게 쓸지 정하려고
function mobileShell(s) {
  const role = (S.roles || []).find((r) => r.key === s.role) || (S.roles || [])[0] || { nav: [] };
  const isTab = (role.nav || []).some((n) => n.slug === s.slug || (s.variantOf && n.slug === s.variantOf));
  if (s.shell === "none" || s.pattern === "onboarding" || (C && C.shell === "none")) return "메뉴 없는 한 장";
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
  return [
    `### ${s.name} — \`${slug}\` → RUN/${file}`,
    `- 누가: ${((S.roles || []).find((r) => r.key === s.role) || {}).label || s.role || "모두"} · 목적: ${s.purpose || ""}`,
    s.overlayOf ? `- **뜨는 창**: 파일 전체가 \`<x-modal title="…">본문 <div class="modal-footer">버튼</div></x-modal>\` 하나. 완료 버튼도 창을 닫으면 data-back(흐름에 있으면 data-trigger).${MOBILE ? " 모바일은 아래에서 올라오는 창으로 펼쳐진다 — 제목은 질문·결과 한 문장, desc 회색 1~2줄, 바닥줄 = primary 하나 + 돌아가기(data-back)." : ""}`
      : MOBILE ? `- 배치 힌트(${s.pattern || "-"}): ${mobileShell(s)} · ${LAYOUT_MOBILE[s.pattern] || "x-page-header + x-section 판들"}`
      : `- 배치 힌트(${s.pattern || "-"}): ${LAYOUT[s.pattern] || "page-header + x-section들"}`,
    s.state ? `- 상태: ${STATE[s.state] || s.state}${s.variantOf ? ` (원래 화면: ${(bySlug.get(s.variantOf) || {}).name || s.variantOf})` : ""}` : "",
    `- 영역(${(s.regions || []).length}개, 모두 한 번씩):`,
    ...(s.regions || []).map((r) => `  - \`${r.key}\` — ${r.label}: ${r.why || ""}`),
    trig.length ? `- 눌러야 하는 버튼:\n${trig.join("\n")}` : `- 눌러야 하는 버튼: 없음(글자 버튼은 data-back·data-stay)`,
  ].filter(Boolean).join("\n");
});

const shellNote = C ? `시안 ${C.id.toUpperCase()} "${C.name}" — 메뉴 구조 ${C.shell}${MOBILE ? (C.shell === "top" ? "(위 알약 탭 메뉴)" : C.shell === "none" ? "(메뉴 없음)" : "(아래 탭 메뉴)") : C.shell === "top" ? "(위쪽 탭 메뉴 — 본문이 가운데 좁게 놓인다)" : C.shell === "rail" ? "(아이콘 메뉴 — 본문 폭이 넓다)" : ""} · 첫 화면 ${C.home || "-"} · 밀도 ${C.density || "-"}` : "";
const out = `# 작업 묶음 — ${slugs.join(", ")}${C ? ` (시안 ${C.id})` : ""}

**이 파일만 읽고, 아래 화면을 하나씩 Write 한 번으로 쓴 뒤 끝낸다.** 점검은 메인이 한다. RUN = ${runDir}
${shellNote ? "\n" + shellNote + "\n" : ""}
## 규칙
${RULES.trim()}
${MOBILE && mobileRules ? `\n## 모바일 규칙 (390×844 — 위 규칙과 다르면 이쪽을 따른다)\n${mobileRules}\n` : ""}
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
