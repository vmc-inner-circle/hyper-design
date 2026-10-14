#!/usr/bin/env node
/**
 * build.js — run 폴더를 단일 HTML 파일로 조립한다.
 *
 *   node scripts/build.js runs/<project> --mode board   → runs/<project>/out/board.html
 *   node scripts/build.js runs/<project> --mode final   → runs/<project>/out/index.html
 *   옵션: --out <path>  --theme a|b|c  --type normal|large  --accent calm|vivid  --round <n>
 *         --open   빌드 후 사용자 기본 브라우저로 연다 (사용자에게 넘기는 마지막 빌드에만)
 *
 * 산출물 구조 (canvas.js가 기대하는 계약):
 *
 *   <html lang="ko" data-mode="board|final" data-platform="web|mobile"
 *         data-theme="<look id>" data-type="large" data-swatch="<swatch id>">   ← 분위기·버튼 색은 scripts/looks.js가 CSS로 계산
 *   <head> … <style>base + toggles + 분위기(looks.js) + components + canvas.css</style>
 *   <body>
 *     <svg id="hx-sprite" hidden><defs><symbol id="i-…">…</symbol>…</defs></svg>   ← 사용된 아이콘만 (보드는 허용 아이콘 전부)
 *     <script type="application/json" id="hx-icons">[{name,key}]</script>          ← 보드만: 아이콘 바꾸기 목록
 *     <script type="application/json" id="hx-data">{ meta, screens, flows, board }</script>
 *     <template id="hx-screens">
 *       <section class="hx-screen" data-screen="<slug>" data-role="<role>"> …조각… </section>
 *     </template>
 *     <div id="hx-app"></div>
 *     <script>/* canvas/*.js *\/</script>
 *
 * canvas.js는 #hx-data를 읽고 #hx-screens의 section을 복제해 화면을 그린다.
 * 조각은 <html>·<style>·<script> 없이 body 안쪽만이며, 영역은 data-region="<key>"로 표시된다.
 */
const fs = require("fs");
const path = require("path");
const LOOKS = require("./looks.js");
const PLATFORM = require("./platform.js");
const EXPAND = require("./expand.js");   // 안전장치: 펼치지 않은 부품 태그·셸이 남아 있어도 화면이 깨지지 않게

const ROOT = path.resolve(__dirname, "..");
const args = process.argv.slice(2);
const runDir = args.find((a) => !a.startsWith("--"));
const opt = (name, def) => {
  const i = args.indexOf(`--${name}`);
  return i >= 0 && args[i + 1] && !args[i + 1].startsWith("--") ? args[i + 1] : def;
};
const mode = opt("mode", "board");
if (!runDir || !["board", "final"].includes(mode)) {
  console.error("usage: node scripts/build.js runs/<project> --mode board|final [--out path] [--open]");
  process.exit(2);
}

const readJSON = (p) => JSON.parse(fs.readFileSync(p, "utf8"));
const read = (p) => fs.readFileSync(p, "utf8");
const exists = (p) => fs.existsSync(p);
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

// ---------- 입력 ----------
const S = readJSON(path.join(runDir, "screens.json"));
const F = readJSON(path.join(runDir, "flow.json"));
const platform = S.platform || "web";
const looks = LOOKS.getLooks(S);
const theme = opt("theme", looks.some((l) => l.id === S.theme) ? S.theme : looks[0].id);
const type = opt("type", (S.toggles && S.toggles.type) || "normal");
const look = looks.find((l) => l.id === theme) || looks[0];
const swatch = LOOKS.resolveSwatch(look, opt("swatch", (S.toggles && (S.toggles.swatch || S.toggles.accent)) || ""));
const accent = swatch;   // 예전 이름 호환
// 안내 문구(toast) 모양 — 보드 '안내 문구 모음'에서 고른다. 기본: 위쪽 · 아이콘 있음 · 흰 바탕 · 보통 글자
const TOAST_DEFAULT = { at: "top", icon: "on", tone: "light", size: "normal" };
const toast = Object.assign({}, TOAST_DEFAULT, (S.toggles && S.toggles.toast) || {});
const toastAttrs = ` data-toast-at="${esc(toast.at)}" data-toast-icon="${esc(toast.icon)}" data-toast-tone="${esc(toast.tone)}" data-toast-size="${esc(toast.size)}"`;
const round = Number(opt("round", S.round || 1));
const coreDir = path.join(ROOT, "packages/core");

// ---------- CSS ----------
const cssParts = [
  read(path.join(coreDir, "tokens/base.css")),
  read(path.join(coreDir, "tokens/toggles.css")),
  LOOKS.looksCss(looks),   // 분위기·버튼 색 토큰 (screens.json looks → 계산, 없으면 기본 분위기)
];
// 밤 화면(screen.dark)은 어두운 분위기의 색만 빌리고 글꼴은 고른 분위기를 따른다
cssParts.push(`.app[data-night] {\n${Object.entries(LOOKS.fontTokens(look)).map(([k, v]) => `  ${k}: ${v};`).join("\n")}\n}`);
const TOKEN_PARTS = cssParts.length;   // 최종 화면별 페이지에 넣을 토큰 CSS 개수
// 디렉터리 안 파일을 이름순으로 모두 읽는다 (00-, 10- 접두로 순서 제어)
const readDir = (dir, ext) =>
  exists(dir) ? fs.readdirSync(dir).filter((f) => f.endsWith(ext)).sort().map((f) => `/* ${f} */\n` + read(path.join(dir, f))) : [];
// 컴포넌트: web 위에 플랫폼 레이어를 겹친다 (mobile = web + packages/mobile — scripts/platform.js)
const compParts = PLATFORM.files(platform, "components", ".css").map((f) => `/* ${f.layer}/${f.file} */\n` + read(f.path));
if (compParts.length === 0) console.warn(`[build] WARN packages/${platform}/components/*.css 없음 — 컴포넌트 스타일 없이 조립`);
cssParts.push(...compParts);
const canvasCssParts = readDir(path.join(coreDir, "canvas"), ".css");
if (canvasCssParts.length === 0) console.warn(`[build] WARN packages/core/canvas/*.css 없음`);
cssParts.push(...canvasCssParts);
// 움직임(packages/core/motion): 보드·입구의 구역 보드에서 화면에 마우스를 올리면 재생한다(완성본 페이지는 아래에서 따로 싣는다)
cssParts.push(read(path.join(coreDir, "motion/motion.css")));
const css = cssParts.join("\n\n");

// ---------- 화면 조각 ----------
// 뜨는 창 화면(overlayOf): 조각에는 창(.modal-backdrop)만 있다 → 뒷 화면 조각의 .app 마지막 자식으로 넣어 합친다
const fragOf = (s) => {
  const p = path.join(runDir, s.file);
  if (!exists(p)) { console.error(`[build] FAIL 조각 없음: ${s.file}`); process.exit(1); }
  const own = nightTone(s, EXPAND.expandFragment(S, s, read(p)).trim());
  const base = s.overlayOf && (S.screens || []).find((x) => x.slug === s.overlayOf);
  if (!base) return own;
  const back = EXPAND.expandFragment(S, base, read(path.join(runDir, base.file))).trim().replace(/\sdata-(trigger|region|stay|back)(="[^"]*")?/g, "");   // 뒷 화면은 배경일 뿐 — 누를 곳·영역 표시는 창에만
  const cut = back.lastIndexOf("</div>");
  return cut < 0 ? back + "\n" + own : back.slice(0, cut) + own + "\n" + back.slice(cut);
};
// 밤에 쓰는 화면(screen.dark: true): 고른 분위기와 상관없이 어두운 분위기(looks 중 mode dark의 첫째)로 칠한다
// — 측정 시작·측정 중처럼 어두운 방에서 보는 화면과 아침 결과 화면의 상황 차이를 보여 주기 위해
function nightTone(s, html) {
  if (!s.dark) return html;
  const D = looks.find((l) => l.mode === "dark");
  if (!D) return html;
  return html.replace(/<div class="(app\b[^"]*)"/, `<div class="$1" data-theme="${esc(D.id)}" data-swatch="${esc(D.swatches[0].id)}" data-night`);
}
// 1턴 시안 보드(stage "concept")는 아직 전체 화면이 없다 — 시안 화면만 싣는다
const stage = mode === "board" && S.stage === "concept" ? "concept" : "draft";
if (S.stage === "concept" && mode === "final") { console.error("[build] FAIL 시안 단계(stage: concept)에서는 최종본을 만들 수 없음"); process.exit(1); }
const sections = [];
for (const s of S.screens || []) {
  if (stage === "concept") continue;
  const frag = fragOf(s);
  sections.push(
    `<section class="hx-screen" data-screen="${esc(s.slug)}" data-role="${esc(s.role || "")}" data-id="${s.id}">\n${frag}\n</section>`
  );
}

// ---------- 시안(concepts): 1턴 보드의 '시안 고르기' ----------
// 지금 화면들 = S.concept(기본 첫 시안). 시안의 메인 화면은 concepts/<id>/<slug>.html → "<id>~<slug>" 섹션
const concepts = Array.isArray(S.concepts) ? S.concepts.filter((c) => c && c.id) : [];
const mainConcept = concepts.length ? (concepts.find((c) => c.id === S.concept) || concepts[0]).id : null;
// 시안을 확정(board.locked에 concept)한 초안에는 시안 화면을 싣지 않는다 — 보이지 않는 화면으로 파일만 무거워진다
const conceptLocked = ((S.board && S.board.locked) || []).includes("concept");
if (mode === "board" && (stage === "concept" || !conceptLocked)) for (const c of concepts) {
  if (c.id === mainConcept && stage !== "concept") continue;
  for (const slug of c.screens || []) {
    const p = path.join(runDir, "concepts", c.id, slug + ".html");
    if (!exists(p)) { console.warn(`[build] WARN 시안 ${c.id} 화면 없음: concepts/${c.id}/${slug}.html`); continue; }
    const cs = (S.screens || []).find((x) => x.slug === slug) || { slug };
    sections.push(`<section class="hx-screen" data-screen="${esc(c.id + "~" + slug)}" data-concept="${esc(c.id)}">\n${EXPAND.expandFragment(S, cs, read(p), { concept: c.id }).trim()}\n</section>`);
  }
}

// 분위기의 글꼴 세트가 쓰는 웹 글꼴 (scripts/looks.js FONTS)
function fontLinkTags(ls) { return LOOKS.fontLinks(ls).map((u) => `<link rel="stylesheet" href="${esc(u)}">`).join("\n"); }

// 안내·예외: 조각에서 '누르면 뜨는 안내'(data-stay)와 입력칸 글자 수(minlength·maxlength)를 뽑아 보드 ⓘ 카드·마우스 올리기에 쓴다
const PICK_CLS = /\b(chip|segmented-item|tab|day)\b/;
function feedbackOf(html) {
  const stays = [], limits = [], outs = [];
  // 앱 밖으로 나가는 버튼(data-out="휴대폰 설정 › 드르렁 › 마이크"): 완성본에서 '앱 밖' 카드, 보드 ⓘ에 '앱 밖으로'
  for (const m of html.matchAll(/<(button|a)\b([^>]*?)\bdata-out="([^"]*)"([^>]*)>([\s\S]*?)<\/\1>/g)) {
    outs.push({ label: m[5].replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim(), text: m[3] });
  }
  for (const m of html.matchAll(/<(button|a)\b([^>]*?)\bdata-stay="([^"]*)"([^>]*)>([\s\S]*?)<\/\1>/g)) {
    const attrs = m[2] + m[4], cls = (/class="([^"]*)"/.exec(attrs) || [])[1] || "";
    if (!m[3] || PICK_CLS.test(cls)) continue;   // 고르는 버튼(칩·나눔 버튼)은 모양이 바뀌는 것으로 충분
    const label = m[5].replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();
    stays.push({ label, text: m[3], tone: (/data-stay-tone="([a-z]+)"/.exec(attrs) || [])[1] || "success" });
  }
  for (const m of html.matchAll(/<(input|textarea)\b([^>]*)>/g)) {
    const a = m[2]; if (/type="(checkbox|radio|hidden|range)"/.test(a)) continue;
    const max = (/maxlength="(\d+)"/.exec(a) || [])[1], min = (/minlength="(\d+)"/.exec(a) || [])[1];
    const lab = [...html.slice(0, m.index).matchAll(/class="field-label"[^>]*>([\s\S]*?)<\/label>/g)].pop();
    const name = lab ? lab[1].replace(/<[^>]+>/g, "").replace(/\*/g, "").trim() : (/placeholder="([^"]*)"/.exec(a) || [])[1] || "입력칸";
    limits.push({ name, min: min ? +min : null, max: max ? +max : null });
  }
  return { stays, limits, outs };
}
const FEEDBACK = {};
if (stage !== "concept") for (const s of S.screens || []) FEEDBACK[s.slug] = feedbackOf(fragOf(s));

// ---------- 데이터 ----------
const data = {
  meta: {
    project: S.project,
    title: S.title || S.project,
    platform,
    mode,
    round,
    theme,
    concept: mainConcept,
    stage,
    toggles: { type, swatch, toast },
    looks: looks.map((l) => ({ id: l.id, name: l.name, why: l.why || "", mode: l.mode, bg: l.bg, ink: LOOKS.inkOf(l), font: LOOKS.fontOf(l).name,
      swatches: l.swatches.map((s) => ({ id: s.id, name: s.name, hex: LOOKS.calmHex(s.hex, l.mode === "dark") })) })),
    roles: S.roles || [],
    generatedAt: new Date().toISOString(),
  },
  screens: (S.screens || []).map((s) => ({
    id: s.id, slug: s.slug, name: s.name, role: s.role || null, purpose: s.purpose || "",
    pattern: s.pattern || null, state: s.state || null, variantOf: s.variantOf || null, overlayOf: s.overlayOf || null,
    when: s.when || null, section: s.section || null, step: s.step || "", policy: Array.isArray(s.policy) ? s.policy : [],
    cases: Array.isArray(s.cases) ? s.cases.filter((c) => c && c.when && c.show).map((c) => ({ when: c.when, show: c.show, tone: c.tone || "danger" })) : [],
    stays: (FEEDBACK[s.slug] || {}).stays || [], limits: (FEEDBACK[s.slug] || {}).limits || [], outs: (FEEDBACK[s.slug] || {}).outs || [],
    motion: Array.isArray(s.motion) ? s.motion.filter((m) => m && m.type).map((m) => ({ type: m.type, target: m.target || null, ms: m.ms || null, level: m.level || null, note: m.note || "" })) : [],
    regions: (s.regions || []).map((r) => ({ id: r.id, key: r.key, label: r.label, why: r.why || "" })),
  })),
  sections: Array.isArray(S.sections) ? S.sections : [],
  flows: F.flows || [],
  branches: F.branches || [],
  concepts: mode === "board" ? concepts.map((c) => ({ id: c.id, name: c.name || c.id, why: c.why || "", shell: c.shell || "sidebar", look: c.look || theme,
    traits: c.traits || [], refs: c.refs || [], screens: c.screens || [] })) : [],
  references: mode === "board" ? (S.references || []) : [],
  board: mode === "board" ? (S.board || {}) : null,
  pages: mode === "final" ? Object.fromEntries(Object.entries(pageFiles(S, F)).map(([k, v]) => [k, "screens/" + v])) : null,
};
// </script> 로 JSON이 끊기지 않게
const dataJSON = JSON.stringify(data).replace(/<\//g, "<\\/");

// ---------- canvas/*.js ----------
const canvasJsParts = readDir(path.join(coreDir, "canvas"), ".js");
if (canvasJsParts.length === 0) console.warn(`[build] WARN packages/core/canvas/*.js 없음`);
const canvasJs = [read(path.join(coreDir, "motion/motion.js"))].concat(canvasJsParts.length ? canvasJsParts : ["console.warn('canvas.js 없음');"]).join("\n\n");

// ---------- 조립 (스프라이트 제외) ----------
const title = mode === "board" ? `${data.meta.title} — ${stage === "concept" ? "시안" : round + "차 보드"}` : `${data.meta.title} — 화면 지도`;
let html = `<!doctype html>
<html lang="ko" data-mode="${mode}" data-platform="${platform}" data-theme="${esc(theme)}" data-type="${esc(type)}" data-swatch="${esc(swatch)}"${toastAttrs}>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(title)}</title>
${fontLinkTags(mode === "board" ? looks : [look])}
<style>
${css}
</style>
</head>
<body>
__SPRITE__
<script type="application/json" id="hx-data">${dataJSON}</script>
<template id="hx-screens">
${sections.join("\n")}
</template>
<div id="hx-app"></div>
<script>
${canvasJs.replace(/<\/script/gi, "<\\/script")}
</script>
</body>
</html>
`;

// ---------- 아이콘 스프라이트 ----------
const sprite = read(path.join(coreDir, "icons/lucide-sprite.svg"));
const symbols = new Map();
for (const m of sprite.matchAll(/<symbol id="([^"]+)"([^>]*)>([\s\S]*?)<\/symbol>/g)) symbols.set(m[1], { attrs: m[2], body: m[3] });
const used = new Set([...html.matchAll(/#i-([a-z0-9-]+)/g)].map((m) => m[1]));
// 보드: 화면 디자인에서 아이콘을 바꿀 수 있게 허용 아이콘(core allowlist + 프로젝트 icons.json) 전부를 싣고 목록을 넘긴다
if (mode === "board") {
  const allow = readJSON(path.join(coreDir, "icons/allowlist.json"));
  const projPath = path.join(runDir, "icons.json");
  const proj = exists(projPath) ? readJSON(projPath) : {};
  const choices = [];
  for (const src of [allow, proj]) for (const [k, v] of Object.entries(src)) {
    if (k.startsWith("_") || !symbols.has(v) || choices.some((c) => c.name === v)) continue;
    choices.push({ name: v, key: k }); used.add(v);
  }
  html = html.replace('<script type="application/json" id="hx-data">',
    `<script type="application/json" id="hx-icons">${JSON.stringify(choices)}</script>\n<script type="application/json" id="hx-data">`);
}
const missing = [...used].filter((n) => !symbols.has(n));
if (missing.length) { console.error(`[build] FAIL 스프라이트에 없는 아이콘: ${missing.join(", ")}`); process.exit(1); }
const defs = [...used].sort().map((n) => `<symbol id="i-${n}"${symbols.get(n).attrs}>${symbols.get(n).body.trim()}</symbol>`).join("\n");
html = html.replace("__SPRITE__", `<svg id="hx-sprite" xmlns="http://www.w3.org/2000/svg" hidden><defs>\n${defs}\n</defs></svg>`);

// ---------- 출력 ----------
const outDefault = path.join(runDir, "out", mode === "board" ? "board.html" : "index.html");
const out = opt("out", outDefault);
fs.mkdirSync(path.dirname(out), { recursive: true });
fs.writeFileSync(out, html);
const kb = (Buffer.byteLength(html) / 1024).toFixed(0);
console.log(`[build] ${mode} → ${path.relative(process.cwd(), out)} (${kb}KB, 화면 ${sections.length}, 아이콘 ${used.size}, 분위기 ${theme}/${type}/${swatch})`);

// ---------- 최종: 화면마다 독립 HTML 완성본 (out/screens/NN-slug.html) ----------
// Figma에서 넘겨받은 화면처럼 보드 장치 없이 실제 화면만. 흐름에 있는 버튼(data-trigger)은 다음 화면 페이지로 이동한다.
if (mode === "final") {
  // 움직임(packages/core/motion) — 화면별 완성본에만. 보드에는 싣지 않는다
  const MOTION_CSS = read(path.join(coreDir, "motion/motion.css"));
  const MOTION_JS = read(path.join(coreDir, "motion/motion.js")).replace(/<\/script/gi, "<\\/script");
  const pageDir = path.join(path.dirname(out), "screens");
  fs.rmSync(pageDir, { recursive: true, force: true });
  fs.mkdirSync(pageDir, { recursive: true });
  const pageCss = cssParts.slice(0, TOKEN_PARTS + compParts.length).join("\n\n");   // 토큰 + 분위기 + 컴포넌트 (보드·캔버스 CSS 제외)
  const files = pageFiles(S, F);
  const order = Object.keys(files);
  order.forEach((slug, i) => {
    const s = (S.screens || []).find((x) => x.slug === slug);
    const frag = fragOf(s);
    const links = {}, from = [slug, s.variantOf].filter(Boolean);   // 상태만 다른 화면은 원래 화면의 버튼 연결을 그대로
    for (const f of F.flows || []) for (const st of f.steps || []) if (from.includes(st.from) && st.trigger && files[st.to] && !links[st.trigger]) links[st.trigger] = { href: files[st.to], action: st.action || "" };
    // 갈래(흐름 밖의 버튼이 여는 화면·창)도 같은 방식으로
    for (const b of F.branches || []) if (from.includes(b.from) && b.trigger && files[b.to] && !links[b.trigger]) links[b.trigger] = { href: files[b.to], action: b.action || "" };
    // 되돌아가기(data-back): 뜨는 창이면 뒷 화면으로, 아니면 브라우저 뒤로
    const backHref = s.overlayOf && files[s.overlayOf] ? files[s.overlayOf] : "";
    // 왼쪽 메뉴(roles[].nav)도 실제 화면 페이지로 — 메뉴 글자로 찾는다
    const navMap = {};
    for (const r of S.roles || []) for (const n of r.nav || []) if (files[n.slug] && !navMap[n.label]) navMap[n.label] = files[n.slug];
    const icons = new Set([...frag.matchAll(/#i-([a-z0-9-]+)/g)].map((m) => m[1]).concat(["chevron-left", "chevron-right", "layout-grid", "circle-check", "circle-alert", "info", "triangle-alert"]));
    const pdefs = [...icons].filter((n) => symbols.has(n)).sort().map((n) => `<symbol id="i-${n}"${symbols.get(n).attrs}>${symbols.get(n).body.trim()}</symbol>`).join("\n");
    const prev = order[i - 1] ? files[order[i - 1]] : null, next = order[i + 1] ? files[order[i + 1]] : null;
    const nav = `<nav class="hx-page-nav" aria-label="화면 이동">
  <a href="../index.html"><svg class="icon-sm" aria-hidden="true"><use href="#i-layout-grid"/></svg>전체 화면</a>
  <span class="hx-page-sep"></span>
  ${prev ? `<a href="${prev}#back" aria-label="이전 화면"><svg class="icon-sm" aria-hidden="true"><use href="#i-chevron-left"/></svg></a>` : `<span class="hx-page-off"><svg class="icon-sm" aria-hidden="true"><use href="#i-chevron-left"/></svg></span>`}
  <b>${i + 1} / ${order.length}</b><span class="hx-page-name">${esc(s.name)}</span>
  ${next ? `<a href="${next}" aria-label="다음 화면"><svg class="icon-sm" aria-hidden="true"><use href="#i-chevron-right"/></svg></a>` : `<span class="hx-page-off"><svg class="icon-sm" aria-hidden="true"><use href="#i-chevron-right"/></svg></span>`}
</nav>`;
    const page = `<!doctype html>
<html lang="ko" data-platform="${platform}" data-theme="${esc(theme)}" data-type="${esc(type)}" data-swatch="${esc(swatch)}"${toastAttrs}>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(s.name)} — ${esc(data.meta.title)}</title>
${fontLinkTags([look])}
<style>
${pageCss}
${platform === "mobile" ? `/* 독립 페이지(모바일): 휴대폰 크기 화면 한 장을 가운데에 */
html, body { height: 100%; }
body { margin: 0; min-height: 100vh; display: flex; align-items: center; justify-content: center; background: var(--c-surface-3); }
body > .app.app-mobile { width: ${PLATFORM.FRAME.mobile.w}px; height: min(${PLATFORM.FRAME.mobile.h}px, 100vh); border-radius: 28px; overflow: hidden; box-shadow: 0 24px 64px rgba(0, 0, 0, .18); }   /* 창이 낮으면 휴대폰 높이를 줄여 위아래가 잘리지 않게 (.app.app-mobile의 고정 높이보다 우선) */` : `/* 독립 페이지: 화면이 브라우저 전체를 채운다 */
html, body { height: 100%; }
body { margin: 0; background: var(--c-bg); }
.app { width: 100%; min-width: 1180px; height: 100vh; }`}
[data-hx-link] { cursor: pointer; }
[data-hx-link]:hover, [data-stay]:hover, [data-back]:hover { outline: 2px solid var(--c-focus); outline-offset: 2px; }
[data-stay], [data-back] { cursor: pointer; }
.hx-toast { position: fixed; left: 50%; bottom: 72px; transform: translateX(-50%); z-index: 9999; padding: 10px 16px; border-radius: 999px;
  background: rgba(17, 24, 39, .92); color: #fff; font: 600 14px/1.3 var(--font-sans); box-shadow: 0 6px 20px rgba(0, 0, 0, .25); }
.hx-toast[hidden] { display: none; }
.hx-page-nav { position: fixed; right: 16px; bottom: 16px; z-index: 9999; display: flex; align-items: center; gap: 8px; padding: 6px 10px;
  border-radius: 999px; background: rgba(17, 24, 39, .88); color: #fff; font: 600 12px/1 var(--font-sans); box-shadow: 0 6px 20px rgba(0, 0, 0, .25); }
.hx-page-nav a, .hx-page-off { display: inline-flex; align-items: center; gap: 4px; color: #fff; text-decoration: none; padding: 4px 6px; border-radius: 999px; }
.hx-page-nav a:hover { background: rgba(255, 255, 255, .15); }
.hx-page-off { opacity: .35; }
.hx-page-sep { width: 1px; height: 16px; background: rgba(255, 255, 255, .3); }
.hx-page-name { max-width: 220px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; opacity: .85; }
${MOTION_CSS}
</style>
</head>
<body>
<svg xmlns="http://www.w3.org/2000/svg" hidden><defs>
${pdefs}
</defs></svg>
${frag}
${nav}
<script>
// 흐름에 있는 버튼을 누르면 다음 화면으로 (그 밖의 버튼·링크는 동작하지 않는 정적 화면)
(function () {
  var links = ${JSON.stringify(links).replace(/<\//g, "<\\/")};
  Object.keys(links).forEach(function (k) {
    var el = document.querySelector('[data-trigger="' + k + '"]'); if (!el) return;
    el.setAttribute("data-hx-link", ""); el.setAttribute("title", links[k].action + " → 다음 화면");
    el.addEventListener("click", function (e) { e.preventDefault(); location.href = links[k].href; });
    // 같은 글자의 다른 버튼(예: 위쪽의 같은 '일정 짜기로 이동')도 같은 화면으로
    var label = (el.textContent || "").replace(/\\s+/g, " ").trim();
    if (label) document.querySelectorAll(".app button, .app a").forEach(function (b) {
      if (b === el || b.hasAttribute("data-hx-link") || (b.textContent || "").replace(/\\s+/g, " ").trim() !== label) return;
      b.setAttribute("data-hx-link", ""); b.setAttribute("title", links[k].action + " → 다음 화면");
      b.addEventListener("click", function (e) { e.preventDefault(); location.href = links[k].href; });
    });
  });
  var nav = ${JSON.stringify(navMap).replace(/<\//g, "<\\/")};
  document.querySelectorAll(".nav-item").forEach(function (a) {
    var t = (a.textContent || "").replace(/\\s+/g, " ").trim(), href = nav[t]; if (!href) return;
    a.setAttribute("href", href); a.setAttribute("data-hx-link", ""); a.setAttribute("title", t + " 화면으로");
  });
  // 그 자리에서 바뀌는 버튼(data-stay="안내 문구"): 짧은 안내만 띄운다 / 되돌아가는 버튼(data-back)
  var toast = document.createElement("div"); toast.className = "hx-toast"; toast.hidden = true; document.body.appendChild(toast);
  var tt = 0, backHref = ${JSON.stringify(backHref)};
  document.querySelectorAll("[data-stay]").forEach(function (b) {
    if (b.hasAttribute("data-hx-link")) return;
    b.addEventListener("click", function (e) {
      e.preventDefault(); var msg = b.getAttribute("data-stay"); if (!msg) return;
      if (window.HXAppToast) { window.HXAppToast(msg, b.getAttribute("data-stay-tone")); return; }   // 앱 디자인의 안내 상자 (motion.js)
      toast.textContent = msg; toast.hidden = false; clearTimeout(tt); tt = setTimeout(function () { toast.hidden = true; }, 1800);
    });
  });
  document.querySelectorAll("[data-back]").forEach(function (b) {
    if (b.hasAttribute("data-hx-link")) return;
    b.setAttribute("data-hx-link", ""); b.setAttribute("title", "이전 화면으로");
    b.addEventListener("click", function (e) { e.preventDefault(); if (backHref) location.href = backHref + "#back"; else if (history.length > 1) history.back(); });
  });
  document.addEventListener("click", function (e) { var a = e.target.closest("a[href='#'], .app a:not([data-hx-link]), .app button:not([data-hx-link])"); if (a && !a.closest(".hx-page-nav")) e.preventDefault(); }, true);
})();
</script>
<script>window.HX_MOTION = ${JSON.stringify({ overlay: !!s.overlayOf, cases: (s.cases || []).filter((c) => c && c.when && c.show), items: (s.motion || []).filter((m) => m && m.type) }).replace(/<\//g, "<\\/")};</script>
<script>
${MOTION_JS}
</script>
</body>
</html>
`;
    fs.writeFileSync(path.join(pageDir, files[slug]), page);
  });
  console.log(`[build] final → ${path.relative(process.cwd(), pageDir)}/ (화면별 독립 페이지 ${order.length}개)`);
}

// 화면 번호 순서대로 NN-slug.html 이름을 정한다 (보드의 '화면 N' = 최종본 NN, index.html의 화면 전체와 같은 순서)
// 번호가 없으면 screens.json 순서. 중간에 뺀 화면이 있어도 NN은 01부터 이어진다.
function pageFiles(S, F) {
  const list = (S.screens || []).map((s, i) => ({ slug: s.slug, k: Number.isInteger(s.id) ? s.id : 1e6 + i }));
  const seen = list.sort((a, b) => a.k - b.k).map((x) => x.slug);
  const out = {};
  seen.forEach((slug, i) => { out[slug] = String(i + 1).padStart(2, "0") + "-" + slug + ".html"; });
  return out;
}

// --open: 사용자 기본 브라우저로 결과를 띄운다 (사용자에게 보여줄 때만 쓴다. 메인의 자체 검수 빌드에는 쓰지 않는다)
if (args.includes("--open")) {
  const { spawn, spawnSync } = require("child_process");
  const abs = path.resolve(out);
  // macOS: 검수용 헤드리스 Chrome이 떠 있으면 `open`이 파일을 그쪽(보이지 않는 창)으로 넘긴다 → 새 인스턴스로 연다
  let darwinArgs = [abs];
  if (process.platform === "darwin") {
    const headless = spawnSync("pgrep", ["-f", "Google Chrome.*--headless"], { encoding: "utf8" }).stdout.trim();
    if (headless) {
      console.warn("[build] 검수용 헤드리스 Chrome이 떠 있어 새 Chrome 창으로 엽니다 (검수가 끝났으면 헤드리스 Chrome을 종료하세요)");
      darwinArgs = ["-n", "-a", "Google Chrome", abs];
    }
  }
  const [cmd, cmdArgs] =
    process.platform === "darwin" ? ["open", darwinArgs] :
    process.platform === "win32" ? ["cmd", ["/c", "start", "", abs]] :
    ["xdg-open", [abs]];
  try {
    spawn(cmd, cmdArgs, { detached: true, stdio: "ignore" }).unref();
    console.log(`[build] 브라우저로 열었습니다: ${abs}`);
  } catch (e) {
    console.warn(`[build] 브라우저 열기 실패 (${e.message}) — 직접 여세요: ${abs}`);
  }
}
