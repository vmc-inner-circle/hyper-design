#!/usr/bin/env node
/**
 * lint.js — run 폴더의 데이터·조각이 계약(packages/core/schema/)을 지키는지 검사한다.
 *
 *   node scripts/lint.js runs/<project> [--strict]
 *
 * exit 0 = 통과. FAIL이 하나라도 있으면 exit 1. WARN은 exit에 영향 없음(--strict면 실패).
 * LLM 자기보고 대신 이 스크립트가 "끝났다"를 판정한다.
 *
 * 나눠 맡는 곳:
 *   형식 · 값        scripts/schema.js의 check — 정본 스키마(필수 · 값 목록 · 형식 · 옛 칸 · 권장 칸)
 *   색 대비          scripts/looks.js의 lookPairs — 자동 보정 뒤 실제로 쓰이는 색 짝
 *   새 규칙          scripts/lint-rules.js의 check(ctx) — 있으면 부른다
 *   규칙 문장 · 값   packages/core/schema/rules.json — 메시지 앞의 규칙 id로 찾고, 끝에 그 규칙의 says를 한 번씩 적는다
 * 이 파일은 그 밖의 관계(화면 · 영역 · 버튼 · 흐름이 서로 맞는지)와 조각 HTML을 본다.
 */
const fs = require("fs");
const path = require("path");
const SCHEMA = require("./schema.js");
const LK = require("./looks.js");

const ROOT = path.resolve(__dirname, "..");
const args = process.argv.slice(2);
const runDir = args.find((a) => !a.startsWith("--"));
const strict = args.includes("--strict");
if (!runDir) {
  console.error("usage: node scripts/lint.js runs/<project> [--strict]");
  process.exit(2);
}

// 메시지 — 규칙 id가 있으면 앞에 붙이고, 끝에 rules.json의 says를 한 번씩 적는다
const RULES = new Map(SCHEMA.RULES.map((r) => [r.id, r]));
const fails = [];
const warns = [];
const ruleHit = new Set();
const say = (list, m, id) => { if (id) ruleHit.add(id); list.push(id ? `${id} · ${m}` : m); };
const fail = (m, id) => say(fails, m, id);
const warn = (m, id) => say(warns, m, id);
/** rules.json 규칙 값 — 없으면 fallback */
const V = (id, key, fallback) => { const v = (RULES.get(id) || {}).value; return v && v[key] !== undefined ? v[key] : fallback; };
const readJSON = (p) => JSON.parse(fs.readFileSync(p, "utf8"));
const exists = (p) => fs.existsSync(p);

// ---------- 정본 값 목록 — 옛 값(x-status legacy)은 빼고 ----------
const DEFS = SCHEMA.DOCS.screens.$defs;
const valuesOf = (n) => [...(n.enum || []), ...(n.anyOf || []).filter((x) => x["x-status"] !== "legacy").flatMap((x) => x.enum || (x.const !== undefined ? [x.const] : []))];
const FORMS = valuesOf(DEFS.region.properties.form);
const TONES = valuesOf(DEFS.tone);
const MOTION = valuesOf(DEFS.motion.properties.type);
const TAKES = valuesOf(DEFS.moodItem.properties.take);
// 움직임 종류마다 대상 칸(region · trigger) — 정본 motion allOf if/then에서
const MOTION_NEEDS = {};
for (const r of DEFS.motion.allOf || []) {
  const t = (r.if && r.if.properties && r.if.properties.type) || {};
  const need = ((r.then && r.then.anyOf) || []).filter((x) => x["x-status"] !== "legacy").flatMap((x) => x.required || []);
  for (const ty of t.enum || [t.const]) MOTION_NEEDS[ty] = need;
}
// 시안 메뉴 틀 — 플랫폼별 값은 정본 최상위 allOf(shell-platform), .app에 붙는 클래스는 expand.js와 같게
function conceptShells(platform) {
  const r = (SCHEMA.DOCS.screens.allOf || []).find((x) => x.if && x.if.properties && x.if.properties.platform);
  const br = r && (r.if.properties.platform.const === platform ? r.then : r.else);
  try { return br.properties.concepts.items.properties.shell.enum; } catch { return platform === "mobile" ? ["tabbar", "top", "none"] : ["sidebar", "top", "rail"]; }
}
const SHELL_CLASS = { web: { sidebar: null, top: "nav-top", rail: "nav-rail" }, mobile: { tabbar: null, top: "nav-top", none: "no-nav" } };

// ---------- 색 계열 — 대표색이 한 계열로 몰리지 않게 (palette-roles) ----------
const HUES = { red: "빨강", orange: "주황", yellow: "노랑", green: "초록", teal: "청록", blue: "파랑", purple: "보라", pink: "분홍", neutral: "무채" };
function hsl(hex) {
  const [r, g, b] = LK.hex2rgb(hex).map((x) => x / 255), mx = Math.max(r, g, b), mn = Math.min(r, g, b), l = (mx + mn) / 2, d = mx - mn;
  if (d === 0) return [0, 0, l];
  const s = d / (1 - Math.abs(2 * l - 1));
  let h = mx === r ? ((g - b) / d) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4;
  return [(h * 60 + 360) % 360, s, l];
}
function hueOf(hex) {
  const [h, s] = hsl(hex);
  if (s < 0.12) return "neutral";
  if (h < 12 || h >= 345) return "red";
  if (h < 40) return "orange";
  if (h < 65) return "yellow";
  if (h < 160) return "green";
  if (h < 195) return "teal";
  if (h < 255) return "blue";
  if (h < 300) return "purple";
  return "pink";
}
const hueDist = (a, b) => { const d = Math.abs(hsl(a)[0] - hsl(b)[0]); return Math.min(d, 360 - d); };

// ---------- 입력 ----------
const screensPath = path.join(runDir, "screens.json");
const flowPath = path.join(runDir, "flow.json");
const iconsPath = path.join(runDir, "icons.json");
if (!exists(screensPath)) { console.error(`[FAIL] ${screensPath} 없음`); process.exit(1); }
if (!exists(flowPath)) { console.error(`[FAIL] ${flowPath} 없음`); process.exit(1); }

const S = readJSON(screensPath);
const F = readJSON(flowPath);
const projectIcons = exists(iconsPath) ? readJSON(iconsPath) : {};
const platform = S.platform || "web";
const PLATFORM = require("./platform.js");

// ---------- 형식 · 값 — 정본 스키마(scripts/schema.js) ----------
// 오류는 하나씩(배열 번호를 화면 slug · 분위기 id로), 경고는 같은 칸끼리 묶어 센다.
// section · step · goal 없음은 아래에서 이 파일이 규칙과 함께 알리므로 권장 칸 경고에서 뺀다.
{
  const named = (data, at) => at.replace(/^\$\.(screens|looks|flows|concepts|roles|sections)\[(\d+)\]/, (m, k, i) => {
    const x = (Array.isArray(data[k]) && data[k][+i]) || {};
    const n = x.slug || x.id || x.key;
    return n ? `${k}[${n}]` : m.slice(2);
  }).replace(/^\$\.?/, "");
  const OWN = /^\$\.screens\[\d+\]\.(section|step|goal): 권장 칸 없음/;
  for (const [doc, data] of [["screens", S], ["flow", F]]) {
    const o = { errs: [], warns: [] };
    SCHEMA.check(SCHEMA.DOCS[doc], data, "$", SCHEMA.DOCS[doc], o);
    for (const e of o.errs) fail(`${doc}.json ${named(data, e)}`);
    const groups = new Map();
    for (const w of o.warns.filter((x) => !OWN.test(x))) { const k = w.replace(/\[\d+\]/g, "[]"); groups.set(k, (groups.get(k) || 0) + 1); }
    for (const [w, n] of groups) warn(`${doc}.json ${w.replace(/^\$\.?/, "")}${n > 1 ? ` (${n}곳)` : ""}`);
  }
}

const sprite = fs.readFileSync(path.join(ROOT, "packages/core/icons/lucide-sprite.svg"), "utf8");
const spriteIds = new Set([...sprite.matchAll(/<symbol id="([^"]+)"/g)].map((m) => m[1]));
const coreAllow = readJSON(path.join(ROOT, "packages/core/icons/allowlist.json"));
const allowed = new Set([
  ...Object.entries(coreAllow).filter(([k]) => !k.startsWith("_")).map(([, v]) => v),
  ...Object.entries(projectIcons).filter(([k]) => !k.startsWith("_")).map(([, v]) => v),
]);

// 알려진 클래스 목록: base.css + components.css + patterns/*.html 에 등장하는 클래스
const knownClasses = new Set();
const collectClasses = (css) => {
  for (const m of css.matchAll(/\.([a-zA-Z_][\w-]*)/g)) knownClasses.add(m[1]);
};
collectClasses(fs.readFileSync(path.join(ROOT, "packages/core/tokens/base.css"), "utf8"));
const compFiles = PLATFORM.files(platform, "components", ".css");   // mobile = web + packages/mobile
if (compFiles.length) for (const f of compFiles) collectClasses(fs.readFileSync(f.path, "utf8"));
else warn(`packages/${platform}/components/*.css 없음 — 클래스 검사 생략`);

// ---------- 분위기(looks)·버튼 색(swatches) — references/prd-to-screens.md §6 ----------
// 대비는 looks.js lookPairs 한 곳에서 계산한다 — 자동 보정 뒤 실제로 쓰이는 색 짝(본문 · 흐린 글자 · 버튼 글자 · 옅은 면 위 글자)
const lowPairs = (L, sw) => LK.lookPairs(L, sw)
  .map((r) => ({ name: r.where || r.n, fg: r.fg, bg: r.bg, need: r.need || r.min, c: r.c !== undefined ? r.c : LK.contrast(r.fg, r.bg) }))
  .filter((r) => r.c < r.need);
{
  if (!Array.isArray(S.looks) || !S.looks.length) warn(`looks 없음 — 기본 분위기(깔끔한 흰색/따뜻한 크림/차분한 밤)를 쓴다. PRD에 맞춘 분위기 3개와 버튼 색을 만든다`);
  const looks = LK.getLooks(S);
  if (S.looks && (S.looks.length < 3 || S.looks.length > 5)) warn(`분위기는 3~5개 (지금 ${S.looks.length}개, 시안마다 하나씩)`);
  const lookIds = new Set();
  for (const L of looks) {
    const ld = `분위기 '${L.name || L.id}'`;
    if (lookIds.has(L.id)) fail(`${ld}: id 중복`); lookIds.add(L.id);
    if (L.name && /[a-z]|#|테마|톤$/i.test(L.name)) warn(`${ld}: 이름은 한국어 일상어로 (예: "따뜻한 크림", "밤 바다")`);
    let ok = true;
    try { LK.hex2rgb(L.bg); LK.hex2rgb(L.ink); } catch { ok = false; }   // 형식 오류는 schema가 알린다
    if (ok) {
      if (L.mode === "dark" && LK.contrast(L.bg, "#000000") > 3) warn(`${ld}: mode dark인데 배경이 밝음`);
      if (L.mode === "light" && LK.contrast(L.bg, "#FFFFFF") > 1.4) warn(`${ld}: mode light인데 배경이 어두움`);
      // 바탕 톤(tone)은 실제 바탕색과 맞아야 한다 — 톤 갈림 · 사례 바탕 수는 lint-rules.js tone-spread가 센다
      if (L.tone) { const real = LK.toneOf(L.bg); if (real !== L.tone) fail(`${ld}: tone '${L.tone}'인데 bg ${L.bg}는 '${real}'(${LK.TONES[real]}) — bg를 톤에 맞게`, "tone-spread"); }
    }
    const sws = L.swatches || [];
    if (sws.length !== 5) warn(`${ld}: 버튼 색은 5개 (지금 ${sws.length}개, 첫 번째가 추천)`);
    if (ok && sws.length) {
      try { for (const r of lowPairs(L, sws[0])) fail(`${ld}: ${r.name} 대비 ${r.c.toFixed(1)} (${r.need} 이상)`, "text-contrast"); }
      catch (e) { fail(`${ld}: 대비 계산 실패 — ${e.message}`, "text-contrast"); }
    }
    const swIds = new Set();
    sws.forEach((sw, i) => {
      const sd = `${ld} 버튼 색 '${sw.name || sw.id}'`;
      if (swIds.has(sw.id)) fail(`${sd}: id 중복`); swIds.add(sw.id);
      if (!sw.name || /#|[a-z]/i.test(sw.name)) warn(`${sd}: 이름은 한국어 색 이름으로 (예: "테라코타", "바다 파랑")`);
      if (!ok) return;
      try {
        // 첫 번째 색은 위에서 모든 짝을 봤다 — 나머지는 이 색이 바꾸는 짝(주 버튼 · 옅은 대표 면)만
        if (i > 0) for (const r of lowPairs(L, sw).filter((x) => /primary/.test(x.fg + x.bg))) fail(`${sd}: ${r.name} 대비 ${r.c.toFixed(1)} (${r.need} 이상)`, "text-contrast");
        if (LK.contrast(sw.hex, L.bg) < 1.6) warn(`${sd}: 배경과 너무 비슷해 버튼이 안 보일 수 있음`);
      } catch (e) { /* hex 형식 오류는 schema가 알린다 */ }
    });
  }
  if (!lookIds.has(S.theme)) fail(`screens.json theme '${S.theme}'이 looks에 없음`);
  const cur = looks.find((l) => l.id === S.theme);
  const sw = S.toggles && S.toggles.swatch;
  if (cur && sw && sw !== "brand" && !(cur.swatches || []).some((x) => x.id === sw)) {
    if (["calm", "vivid"].includes(sw)) warn(`toggles.swatch '${sw}' — 옛 값, 분위기 '${cur.id}'의 버튼 색 id나 brand로`);
    else fail(`toggles.swatch '${sw}'이 분위기 '${cur.id}'의 버튼 색에 없음`);
  }
  const rec = S.board && S.board.recommend;
  if (rec && rec.theme && !lookIds.has(rec.theme)) fail(`board.recommend.theme '${rec.theme}'이 looks에 없음`);

  // 역할 팔레트 — brand(누르는 것) · support(정보 면) · accent(오늘·지금). 분위기를 다 만든 뒤(4개 이상)에 본다
  if (Array.isArray(S.looks) && S.looks.length >= 4) {
    const STATUS_HUES = new Set(["green", "orange", "red"]);
    const brands = [];
    for (const L of S.looks) {
      const ld = `분위기 '${L.id}'`, P = L.palette;
      if (!P || !P.brand || !P.brand.hex || !P.support || !P.support.hex) { fail(`${ld}: palette.brand·palette.support 없음 (역할 팔레트 — 버튼 색 후보만으로는 역할이 없다)`, "palette-roles"); continue; }
      let ok = true;
      for (const r of ["brand", "support", "accent"]) if (P[r]) {
        try { LK.hex2rgb(P[r].hex); } catch { ok = false; }
        if (!P[r].why) warn(`${ld}: palette.${r}.why 없음 — 어느 기준어·역할 때문인지 한 줄`, "palette-roles");
      }
      if (!P.why) warn(`${ld}: palette.why 없음 — 색 조합을 한 줄로`, "palette-roles");
      if (!ok) continue;   // 형식 오류는 schema가 알린다
      brands.push(P.brand.hex);
      const bh = hueOf(P.brand.hex), sh = hueOf(P.support.hex);
      if (sh !== "neutral" && bh !== "neutral" && hueDist(P.brand.hex, P.support.hex) > 60) warn(`${ld}: support(${HUES[sh]})가 brand(${HUES[bh]})의 이웃 색이 아님(색상각 ${Math.round(hueDist(P.brand.hex, P.support.hex))}°) — 보색이면 한 색만 넓게`, "palette-roles");
      if (P.accent && P.accent.hex) {
        if (STATUS_HUES.has(hueOf(P.accent.hex))) warn(`${ld}: accent가 상태색 계열(${HUES[hueOf(P.accent.hex)]}) — 확정·바뀜·삭제와 헷갈릴 수 있음`, "palette-roles");
        const c = LK.contrast(P.accent.hex, L.bg), need = V("text-contrast", "large", 3);
        if (c < need) fail(`${ld}: accent와 바탕 대비 ${c.toFixed(1)} (${need} 이상)`, "text-contrast");
      }
    }
    if (brands.length >= 4) {
      const fam = brands.map(hueOf), fset = new Set(fam), blues = fam.filter((h) => h === "blue").length;
      const minHues = V("palette-roles", "hues", 3), maxBlue = V("palette-roles", "blue_max", 2);
      if (fset.size < minHues) fail(`대표색(palette.brand) 계열이 ${fset.size}가지(${[...fset].map((h) => HUES[h]).join("·")}) — ${minHues}가지 이상으로 (같은 기준어 안에서도 색으로 갈리게)`, "palette-roles");
      if (blues > maxBlue) fail(`대표색 중 파랑 계열이 ${blues}개 — ${maxBlue}개 이하 (파랑은 기본값이 아니다: 따뜻함은 따뜻한 계열, 신뢰·평온은 파랑)`, "palette-roles");
    }
    for (const L of S.looks) if (L.type && L.type.heading && !L.type.headingWhy) warn(`분위기 '${L.id}': type.headingWhy 없음 — 제목 서체를 어느 기준어·말투 때문에 골랐는지 한 줄`);
  }
}
// ---------- 기준어·표현용 무드보드(mood) — prd-to-screens §6-0 ----------
if (S.mood) {
  const M = S.mood;
  const lookIds = new Set((S.looks || []).map((l) => l.id));
  const K = Array.isArray(M.keywords) ? M.keywords : [];
  const nKey = V("mood-keywords-3", "count", 3);
  if (K.length !== nKey) fail(`mood.keywords는 ${nKey}개 (지금 ${K.length}개)`, "mood-keywords-3");
  const words = new Set(K.map((k) => k && k.word).filter(Boolean));   // word · not · prd 필수는 schema가 본다
  for (const w of words) if (/모던|깔끔|세련|심플|미니멀/.test(w)) warn(`mood.keywords '${w}': 어느 서비스에나 맞는 말 — 반대로 짐작하면 틀리는 말을 고른다`, "mood-keywords-3");
  // 표현용 무드보드는 선택 칸 — 있을 때만 개수 · 기준어마다 항목 · 분위기마다 근거를 본다
  const Bd = Array.isArray(M.board) ? M.board : [];
  if (Bd.length && (Bd.length < 10 || Bd.length > 15)) (Bd.length < 6 ? fail : warn)(`mood.board는 10~15개 (지금 ${Bd.length}개)`);
  const ids = new Set(), takes = new Set(), perLook = {}, perWord = {};
  for (const m of Bd) {
    if (!m) continue;
    const md = `mood.board '${m.id || m.name || "?"}'`;
    if (m.id && ids.has(m.id)) fail(`${md}: id 중복`); ids.add(m.id);
    if (TAKES.includes(m.take)) takes.add(m.take);
    if (m.keyword !== undefined) { if (!words.has(m.keyword)) fail(`${md}: keyword '${m.keyword}'이 기준어에 없음`); else perWord[m.keyword] = (perWord[m.keyword] || 0) + 1; }
    if (m.look) { if (!lookIds.has(m.look)) fail(`${md}: look '${m.look}'이 looks에 없음`); else perLook[m.look] = (perLook[m.look] || 0) + 1; }
    if (m.take === "color" && !(m.colors || []).length) warn(`${md}: 색을 가져오면 colors(잰 값)를 적는다`);
  }
  if (Bd.length) for (const w of words) if (!perWord[w]) warn(`기준어 '${w}'에서 나온 무드보드 항목이 없음`);
  if (Bd.length && takes.size < 3) warn(`무드보드가 ${[...takes].join("·")}뿐 — 서체·모양·여백·그래픽도 (take 3종 이상)`);
  for (const L of S.looks || []) {
    if (L.lean && !words.has(L.lean)) fail(`분위기 '${L.id}': lean '${L.lean}'이 기준어에 없음`);
    if (Bd.length && (perLook[L.id] || 0) < 2) warn(`분위기 '${L.id}': 무드보드 항목 ${perLook[L.id] || 0}개 (2~3개 — 분위기 값의 근거)`);
  }
}
const roleKeys = new Set((S.roles || []).map((r) => r.key));

// ---------- 화면·영역·id ----------
const ids = new Map(); // id → 설명
const slugs = new Map(); // slug → screen
const regionKeysBySlug = new Map();
const triggersBySlug = new Map(); // slug → Map(triggerKey → 속한 region key | null)
const buttonsBySlug = new Map(); // slug → [{ text, trigger, stay, back }] — 글자가 있는 .btn
const htmlBySlug = {}; // slug → 조각 HTML (lint-rules.js ctx.html)

// 조각 HTML에서 data-trigger마다 가장 가까운 바깥 data-region을 찾는다 (가벼운 태그 스택 파서)
function scanTriggers(html) {
  const out = new Map();
  const stack = []; // {tag, region}
  const voids = new Set(["area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr", "use", "path", "circle", "rect", "line", "polyline", "polygon"]);
  for (const m of html.matchAll(/<(\/?)([a-zA-Z][\w-]*)([^>]*?)(\/?)>/g)) {
    const [, close, tagRaw, attrs, selfClose] = m;
    const tag = tagRaw.toLowerCase();
    if (close) { for (let i = stack.length - 1; i >= 0; i--) if (stack[i].tag === tag) { stack.length = i; break; } continue; }
    const region = (/data-region\s*=\s*["']([^"']+)["']/.exec(attrs) || [])[1] || null;
    const trig = (/data-trigger\s*=\s*["']([^"']+)["']/.exec(attrs) || [])[1] || null;
    const parentRegion = [...stack].reverse().find((s) => s.region)?.region || null;
    if (trig) out.set(trig, region || parentRegion);
    if (!selfClose && !voids.has(tag)) stack.push({ tag, region });
  }
  return out;
}
// 글자가 있는 .btn(버튼·링크)마다: 누르면 어디로 가는지(data-trigger) · 그 자리에서 바뀌는지(data-stay) · 되돌아가는지(data-back)
function scanButtons(html) {
  const out = [];
  for (const m of html.matchAll(/<(button|a)\b([^>]*)>([\s\S]*?)<\/\1>/g)) {
    const attrs = m[2], cls = (/class\s*=\s*["']([^"']*)["']/.exec(attrs) || [])[1] || "";
    const list = cls.split(/\s+/);
    if (!list.includes("btn") || list.includes("btn-icon") || list.includes("nav-item")) continue;
    const text = m[3].replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();
    if (!text) continue;
    out.push({ text, trigger: (/data-trigger\s*=\s*["']([^"']+)["']/.exec(attrs) || [])[1] || null,
      stay: /\sdata-stay\b/.test(attrs), back: /\sdata-back\b/.test(attrs), out: /\sdata-out\b/.test(attrs) });
  }
  return out;
}
const noteId = (id, desc) => {
  if (!Number.isInteger(id)) { fail(`${desc}: id 누락 (node scripts/ids.js ${runDir} 실행)`); return; }
  if (ids.has(id)) fail(`id ${id} 중복: ${ids.get(id)} ↔ ${desc}`);
  ids.set(id, desc);
};

// 모바일(390×844) — 한 줄짜리 화면에 맞지 않는 부품 금지, 맨 아래 주 버튼·아래에서 올라오는 창 규칙 (packages/mobile/snippets/00-rules.md)
const MOBILE_BAN = /^(split|split-list|split-detail|table|table-wrap|week-grid|wg-[a-z-]+|sidebar|topnav|grid-3|grid-4|drawer|form-actions)$/;
function mobileChecks(desc, s, html) {
  const cls = [...html.matchAll(/class\s*=\s*["']([^"']+)["']/g)].flatMap((m) => m[1].split(/\s+/));
  const banned = [...new Set(cls.filter((c) => MOBILE_BAN.test(c)))];
  if (banned.length) fail(`${desc}: 모바일 화면에 쓰지 않는 부품 ${banned.map((c) => `'${c}'`).join(", ")} — 한 줄 카드·목록으로 (packages/mobile/snippets/00-rules.md)`);
  const ctas = (html.match(/class=["'][^"']*\bbottom-cta\b/g) || []).length;
  if (ctas > 1) warn(`${desc}: 맨 아래 주 버튼 묶음(.bottom-cta)이 ${ctas}개 — 하나만`);
  else if (ctas === 1 && !/<div class=["'][^"']*\bbottom-cta\b[^]*?<\/div>\s*<\/main>/.test(html)) warn(`${desc}: .bottom-cta는 main.content의 마지막에`);
  if (!s.overlayOf) {
    const app = /<div\s+class=["']([^"']*\bapp\b[^"']*)["']/.exec(html);
    if (app && !/\bapp-mobile\b/.test(app[1])) warn(`${desc}: .app에 app-mobile 없음 — node scripts/expand.js --reshell`);
    const outside = html.replace(/<div class=["'][^"']*\b(bottom-cta|modal)\b[^]*?<\/div>/g, "");
    if (/class=["'][^"']*\bbtn-primary\b/.test(outside)) warn(`${desc}: 주 버튼(btn-primary)은 맨 아래 .bottom-cta 안에`);
  } else if (!/^<div\s+class=["'][^"']*\bsheet-backdrop\b/.test(html.trim())) warn(`${desc}: 모바일 뜨는 창은 아래에서 올라오는 창(sheet-backdrop) — <x-modal>로 쓰면 expand가 바꿔 준다`);
  if (/<section class=["'][^"']*\bsection\b[^>]*>(?:(?!<\/section>)[^])*class=["'][^"']*\bcard\b/.test(html)) warn(`${desc}: 모바일 묶음(.section)은 그 자체가 흰 카드 — 안에 .card를 겹치지 않는다`);
  // 주 행동 줄(영역 모양 actions): 맨 아래 주 버튼은 actions 영역(본문 마지막 영역) 안에 — 흐름 단계의 region도 그 영역 key.
  // 정본 영역 모양에 actions가 있을 때만 본다(없으면 따를 수 없는 경고가 된다)
  if (FORMS.includes("actions")) {
    const forms = new Map((s.regions || []).map((r) => [r.key, r.form]));
    const outside = primaryInCta(html).filter((p) => !(p.dataForm === "actions" || (p.region && forms.get(p.region) === "actions")));
    if (outside.length) warn(`${desc}: 맨 아래 주 버튼(.bottom-cta .btn-primary) ${outside.length}개가 주 행동 줄(form actions) 영역 밖에 있음 (지금: ${[...new Set(outside.map((p) => p.region || "영역 밖"))].join(", ")}) — 본문 마지막 영역을 form "actions"(level 2)로 두고 그 안에`, "actions-mobile");
  }
}
// .bottom-cta 안의 .btn-primary마다 { region(가장 가까운 바깥 data-region), dataForm(그 영역의 data-form) }
function primaryInCta(html) {
  const out = [], stack = [];
  const voids = new Set(["br", "hr", "img", "input", "use", "path", "circle", "rect", "line", "polyline", "polygon", "meta", "link"]);
  for (const m of html.replace(/<!--[\s\S]*?-->/g, "").matchAll(/<(\/?)([a-zA-Z][\w-]*)([^>]*?)(\/?)>/g)) {
    const [, close, tagRaw, attrs, selfClose] = m, tag = tagRaw.toLowerCase();
    if (close) { for (let i = stack.length - 1; i >= 0; i--) if (stack[i].tag === tag) { stack.length = i; break; } continue; }
    const cls = ((/class\s*=\s*["']([^"']*)["']/.exec(attrs) || [])[1] || "").split(/\s+/);
    const region = (/data-region\s*=\s*["']([^"']+)["']/.exec(attrs) || [])[1] || null;
    const dataForm = (/data-form\s*=\s*["']([^"']+)["']/.exec(attrs) || [])[1] || null;
    if (cls.includes("btn-primary") && stack.some((x) => x.cta)) {
      const reg = [...stack].reverse().find((x) => x.region);
      out.push({ region: region || (reg && reg.region) || null, dataForm: (reg && reg.dataForm) || dataForm });
    }
    if (!selfClose && !voids.has(tag)) stack.push({ tag, region, dataForm, cta: cls.includes("bottom-cta") });
  }
  return out;
}
// 조건 이름표(when): 구역 보드는 화면을 순서대로 나란히 놓고, 조건이 갈리는 곳에만 화살표 + 이 이름표를 단다
function checkWhen(x, d) {
  if (typeof x.when !== "string") return;   // 형식은 schema가 본다
  const max = V("split-when", "max", 16);
  if (!x.when.trim()) fail(`${d}: when은 조건 한 마디 (예: "처음 가입이면")`, "split-when");
  else if (x.when.length > max) warn(`${d}: 조건 이름표 "${x.when}" — ${max}자 이내로`, "split-when");
}
// 사용자는 컴포넌트를 모른다 — 보이는 이름·정책 메모에 컴포넌트 용어 금지
const JARGON = /카드|띠|배너|스트립|패널|서랍|드로어|모달|바텀시트|탭|칩|배지|세그먼트|토글|스위치|리스트|타임라인|섹션|영역|위젯|컴포넌트|CTA|랜딩/;
const [SCREEN_MIN, SCREEN_MAX] = V("ids-range", "screen", [1, 100]);
const REGION_MIN = V("ids-range", "region_min", 101);
for (const s of S.screens || []) {
  const desc = `화면 ${s.slug || "(slug 없음)"}`;
  if (slugs.has(s.slug)) fail(`slug 중복: ${s.slug}`);
  slugs.set(s.slug, s);
  if (!s.file && S.stage !== "concept") fail(`${desc}: file 없음`);   // 1턴 시안 단계: 화면 조각 자리는 2턴에 정한다 — 이때 FAIL은 시안 조각 없음만
  if (s.role && roleKeys.size && !roleKeys.has(s.role)) fail(`${desc}: role '${s.role}'이 roles에 없음`);
  // 목적(goal): 뜨는 창 · 상태 화면까지 모든 화면에 한 문장 — 1순위 문장(emphasize)이 이 목적을 실제 사실로 말한다
  if (typeof s.goal !== "string" || !s.goal.trim()) warn(`${desc}: 목적(goal) 없음 — 이 화면에서 사용자가 이루려는 것 한 문장 (뜨는 창 · 상태 화면 포함)`);
  if ((s.state === "error" || s.state === "success") && !s.when) warn(`${desc}: ${s.state === "error" ? "오류" : "완료"} 화면이 언제 나오는지(when) 없음 — 예: "마이크를 허용하지 않았을 때" (보드에서 화면 위 말풍선으로 보인다)`, "state-pair");
  if ((s.state === "error" || s.state === "success") && !s.variantOf) fail(`${desc}: ${s.state === "error" ? "오류" : "완료"} 상태 화면은 원래 화면을 variantOf로 가리킨다 (구역 보드에서 원래 화면 옆에 놓인다)`, "state-pair");
  noteId(s.id, desc);
  if (Number.isInteger(s.id) && (s.id < SCREEN_MIN || s.id > SCREEN_MAX)) warn(`${desc}: 화면 번호 ${s.id} — 화면은 ${SCREEN_MIN}, ${SCREEN_MIN + 1}, ${SCREEN_MIN + 2}…으로 (node scripts/ids.js가 발급)`, "ids-range");

  const regions = Array.isArray(s.regions) ? s.regions : [];   // 0개 · 필수 칸은 schema가 본다
  const maxRegions = V("regions-count", "max", 6);
  if (regions.length > maxRegions) fail(`${desc}: 영역 ${regions.length}개 (최대 ${maxRegions})`, "regions-count");
  const keys = new Set();
  for (const r of regions) {
    const rd = `${s.slug} / ${r.key || "(key 없음)"}`;
    if (keys.has(r.key)) fail(`${rd}: 같은 화면 안 key 중복`);
    keys.add(r.key);
    // 사용자는 컴포넌트를 모른다 — 번호를 누르면 보이는 이름에 컴포넌트 용어 금지
    const jargon = (r.label || "").match(JARGON);
    if (jargon) warn(`${rd}: label에 컴포넌트 용어 '${jargon[0]}' — '무엇이 보이는/하는 곳'으로 (예: "날짜 고르기")`, "label-plain");
    noteId(r.id, `영역 ${rd}`);
    if (Number.isInteger(r.id) && r.id < REGION_MIN && !Number.isInteger(S.nextId)) warn(`${rd}: 영역 번호 ${r.id} — 영역은 ${REGION_MIN}부터 (화면 번호와 섞이지 않게)`, "ids-range");
  }
  regionKeysBySlug.set(s.slug, keys);

  // ----- 조각 파일 -----
  const fragPath = path.join(runDir, s.file || "");
  if (S.stage === "concept" && (!s.file || !exists(fragPath))) continue;   // 1턴 시안 단계: 전체 화면은 2턴에 만든다
  if (!s.file || !exists(fragPath)) { fail(`${desc}: 조각 파일 없음 (${s.file})`); continue; }
  const html = fs.readFileSync(fragPath, "utf8");
  htmlBySlug[s.slug] = html;

  if (/<x-[a-z]/.test(html)) fail(`${desc}: 펼치지 않은 부품 태그(<x-…>) — node scripts/expand.js ${runDir} 먼저`);
  if (/<\s*(html|head|body|style|script|link)\b/i.test(html)) fail(`${desc}: 조각에 <html|head|body|style|script|link> 금지`);
  if (/\sstyle\s*=\s*["']/i.test(html)) fail(`${desc}: 인라인 style 금지 — 컴포넌트 클래스만 사용`);
  if (/lorem ipsum|dolor sit amet/i.test(html)) fail(`${desc}: Lorem ipsum 금지 — 도메인 더미 텍스트 사용`);
  // 자리표시 문구: 요소 내용이 통째로 "버튼"/"텍스트"뿐인 경우만 (라벨 "설명 (선택)" 같은 실제 문구는 제외)
  if (/>\s*(버튼|텍스트|제목|내용|본문|더미)\s*<\/(button|a|h[1-6]|p|span|td|th|li)>/.test(html)) warn(`${desc}: 자리표시 문구("버튼"·"텍스트" 등) 발견 — 실제 문구로`);

  // data-region 양방향 대조
  const inHtml = [...html.matchAll(/data-region\s*=\s*["']([^"']+)["']/g)].map((m) => m[1]);
  const inHtmlSet = new Set(inHtml);
  const dupInHtml = inHtml.filter((k, i) => inHtml.indexOf(k) !== i);
  for (const k of new Set(dupInHtml)) fail(`${desc}: data-region="${k}" 가 조각에 2번 이상 등장`);
  for (const k of keys) if (!inHtmlSet.has(k)) fail(`${desc}: screens.json 영역 '${k}'이 조각에 data-region으로 없음`);
  for (const k of inHtmlSet) if (!keys.has(k)) fail(`${desc}: 조각의 data-region='${k}'이 screens.json에 없음`);

  // data-trigger (흐름 화살표 출발점) — 화면 안에서 유일해야 한다
  const trigAll = [...html.matchAll(/data-trigger\s*=\s*["']([^"']+)["']/g)].map((m) => m[1]);
  for (const k of new Set(trigAll.filter((k, i) => trigAll.indexOf(k) !== i))) fail(`${desc}: data-trigger="${k}" 가 2번 이상 등장`);
  triggersBySlug.set(s.slug, scanTriggers(html));
  buttonsBySlug.set(s.slug, scanButtons(html));

  // 뜨는 창 화면: 조각은 창(.modal-backdrop) 하나뿐 — 뒷 화면은 build.js가 overlayOf 화면을 깔아 합친다
  if (s.overlayOf) {
    const body = html.replace(/<!--[\s\S]*?-->/g, "").trim();
    if (!/^<div\s+class=["'][^"']*\bmodal-backdrop\b/.test(body)) fail(`${desc}: 뜨는 창 화면(overlayOf)의 조각은 <div class="modal-backdrop">…</div> 하나로 시작해야 함 — 뒷 화면은 쓰지 않는다`);
  }

  // 아이콘
  for (const m of html.matchAll(/href\s*=\s*["']#i-([a-z0-9-]+)["']/g)) {
    const name = m[1];
    if (!spriteIds.has(name)) fail(`${desc}: 아이콘 '${name}' 은 lucide 스프라이트에 없음`);
    else if (!allowed.has(name)) fail(`${desc}: 아이콘 '${name}' 은 allowlist/icons.json에 없음 — icons.json에 의미와 함께 등록`);
  }
  for (const m of html.matchAll(/<svg\b(?![^>]*class=["'][^"']*\bicon(-sm|-lg)?\b)[^>]*>\s*<use/g)) {
    warn(`${desc}: <svg><use> 에 .icon/.icon-sm/.icon-lg 클래스 없음`);
  }
  for (const m of html.matchAll(/<button\b([^>]*)>\s*<svg[^>]*>\s*<use[^>]*>\s*<\/svg>\s*<\/button>/g)) {
    if (!/aria-label\s*=/.test(m[1])) fail(`${desc}: 아이콘만 있는 버튼에 aria-label 없음`);
  }

  // 알려지지 않은 클래스 (경고)
  if (platform === "mobile") mobileChecks(desc, s, html);
  if (knownClasses.size) {
    const unknown = new Set();
    for (const m of html.matchAll(/class\s*=\s*["']([^"']+)["']/g)) {
      for (const c of m[1].split(/\s+/).filter(Boolean)) {
        if (!knownClasses.has(c) && !c.startsWith("hx-")) unknown.add(c);
      }
    }
    if (unknown.size) warn(`${desc}: components.css에 없는 클래스 ${[...unknown].map((c) => `'${c}'`).join(", ")} — 스타일이 안 먹는다`);
  }
}

// ---------- roles[].nav · inclusion ----------
for (const r of S.roles || []) {
  if (!r.nav) { warn(`역할 '${r.key}': nav 없음 — 화면마다 사이드바가 제각각이 된다 (references/prd-to-screens.md §2)`); continue; }
  for (const n of r.nav) {
    if (!slugs.has(n.slug)) fail(`역할 '${r.key}' nav: 화면 '${n.slug}' 없음`);
    if (!n.label) fail(`역할 '${r.key}' nav '${n.slug}': label 없음`);
    if (n.icon && !spriteIds.has(n.icon)) fail(`역할 '${r.key}' nav '${n.slug}': 아이콘 '${n.icon}' 스프라이트에 없음`);
    else if (n.icon && !allowed.has(n.icon)) fail(`역할 '${r.key}' nav '${n.slug}': 아이콘 '${n.icon}' allowlist/icons.json에 없음`);
  }
}
// 누가 어떤 상황에서 읽는지(roles[].inclusion) → 글자 크기 추천(board.recommend.type) + 이유 → 사람이 고름(toggles.type)
{
  const incl = (S.roles || []).filter((r) => typeof r.inclusion === "string" && r.inclusion.trim());
  const rec = (S.board && S.board.recommend) || {};
  if (incl.length && !rec.type) warn(`역할 ${incl.map((r) => `'${r.key}'`).join(", ")}에 inclusion이 있는데 글자 크기 추천(board.recommend.type) 없음 — 읽는 사람 · 상황을 보고 normal|large와 이유(typeWhy)를 적는다`, "body-size-min");
  else if (rec.type && !rec.typeWhy) warn(`board.recommend.type '${rec.type}'에 이유(typeWhy) 없음 — 어느 역할의 inclusion 때문인지 한 줄`, "body-size-min");
}

// ---------- flow ----------
const flowKeys = new Set();
const reached = new Set();
for (const f of F.flows || []) {
  const fd = `플로우 ${f.key || "(key 없음)"}`;
  if (flowKeys.has(f.key)) fail(`${fd}: key 중복`);
  flowKeys.add(f.key);
  // 흐름 제목은 디자인 산출물의 작업 이름: 짧은 '~하기' (문장·해요체·주어 금지)
  if (typeof f.name === "string") {
    if (!/기$/.test(f.name.trim())) warn(`${fd}: 제목 "${f.name}" — 짧은 '~하기' 작업 이름으로 (예: "첫 모임 만들기", "책 고르고 투표하기")`);
    else if (f.name.trim().length > 18) warn(`${fd}: 제목 "${f.name}" — 18자 이내로 짧게`);
    else if (/[·()]/.test(f.name)) warn(`${fd}: 제목에 가운뎃점·괄호 — 자연스러운 문장으로 ("비행기·숙소" → "비행기와 숙소")`);
  }
  if (f.role && roleKeys.size && !roleKeys.has(f.role)) fail(`${fd}: role '${f.role}'이 roles에 없음`);
  if (!Array.isArray(f.steps)) continue;   // 필수 · 빈 배열은 schema가 본다
  f.steps.forEach((st, i) => {
    const sd = `${fd} step ${i + 1}`;
    // 흐름은 끊기지 않는 한 줄이어야 한다: 이번 step의 출발 화면 = 직전 step의 도착 화면
    if (i > 0 && st.from !== f.steps[i - 1].to) warn(`${sd}: 흐름이 끊김 ('${f.steps[i - 1].to}' 다음에 '${st.from}'에서 시작) — 별도 흐름으로 나눈다`, "flow-steps");
    if (!slugs.has(st.from)) fail(`${sd}: from '${st.from}' 화면 없음`);
    if (!slugs.has(st.to)) fail(`${sd}: to '${st.to}' 화면 없음`);
    if (st.from && slugs.has(st.from) && st.region) {
      const keys = regionKeysBySlug.get(st.from) || new Set();
      if (!keys.has(st.region)) fail(`${sd}: region '${st.region}'이 '${st.from}' 화면 영역에 없음`);
    }
    checkWhen(st, sd);
    // trigger: 화살표가 출발하는 실제 버튼/항목. 조각에 data-trigger="<key>"가 있어야 한다
    if (st.trigger && triggersBySlug.has(st.from)) {   // 조각을 아직 안 썼으면(1.2 단계) 건너뛴다
      const trig = triggersBySlug.get(st.from);
      if (!trig.has(st.trigger)) fail(`${sd}: trigger '${st.trigger}'가 '${st.from}' 조각에 data-trigger로 없음`);
      else if (st.region && trig.get(st.trigger) !== st.region) warn(`${sd}: trigger '${st.trigger}'가 region '${st.region}' 안에 있지 않음 (실제: ${trig.get(st.trigger) || "영역 밖"})`);
    }
    reached.add(st.from); reached.add(st.to);
  });
}
// 처음 시작 흐름: 역할이 있으면 lint-rules.js flow-role이 역할마다 본다 — 역할이 하나뿐(roles 빈 배열)일 때만 여기서
if (!roleKeys.size && ![...slugs.values()].some((s) => s.state === "first-run" || s.state === "empty")) {
  warn(`처음 켰을 때·데이터 없을 때 화면이 없음 — '처음 시작' 흐름을 맨 앞에 (references/prd-to-screens.md §3)`, "flow-role");
}
for (const s of slugs.values()) {
  if (s.variantOf && !slugs.has(s.variantOf)) fail(`화면 ${s.slug}: variantOf '${s.variantOf}' 화면 없음`);
  if (s.overlayOf) {
    const base = slugs.get(s.overlayOf);
    if (!base) fail(`화면 ${s.slug}: overlayOf '${s.overlayOf}' 화면 없음`);
    else if (base.overlayOf) fail(`화면 ${s.slug}: overlayOf '${s.overlayOf}'도 뜨는 창 — 뒷 화면은 보통 화면이어야 함`, "variant-target");
    if (!/창$/.test(s.name || "")) warn(`화면 ${s.slug}: 뜨는 창 화면 이름은 '~ 창'으로 (예: "날짜 더하기 창")`);
  }
}
{
  const n = [...slugs.values()].filter((s) => s.overlayOf).length;
  if (n > 6) warn(`뜨는 창 화면 ${n}개 — 6개 이하로 (핵심 작업에 닿는 창만 화면으로, 나머지는 data-stay)`);
}

// ---------- 구역 보드: 구역(sections) · 단계 이름표(step) · 정책 메모(policy) — references/prd-to-screens.md §8 ----------
{
  const SEC = Array.isArray(S.sections) ? S.sections : [];
  const secMax = V("sections-count", "max", 6), secWarn = V("sections-count", "warnOver", 7);
  const secName = V("sections-count", "name", 12), secDesc = V("sections-count", "desc", 40);
  if (!SEC.length) fail(`sections 없음 — 사용 흐름(구역 보드)을 그릴 큰 구역 2~${secMax}개 (예: [{ "key": "start", "name": "가입·처음 시작" }, { "key": "home", "name": "홈" }])`, "sections-count");
  else if (SEC.length >= secWarn) warn(`구역 ${SEC.length}개 — 2~${secMax}개로 크게 묶는다(온보딩·홈·예약처럼)`, "sections-count");
  const secKeys = new Set();
  for (const x of SEC) {
    if (secKeys.has(x.key)) fail(`구역 key 중복: ${x.key}`); secKeys.add(x.key);
    // key 형식 · name · desc 필수는 schema가 본다
    if (typeof x.name === "string") {
      if (x.name.length > secName) warn(`구역 '${x.name}': ${secName}자 이내로`, "sections-count");
      // 구역 이름은 하는 일을 일상어로("아침에 결과 보기") — 줄임말·기호로 잇지 않는다 (사용자: "아침 결과, 추이 병원 이런 거 잘 모르겠어 뭔지")
      if (/[—–\-]|·/.test(x.name)) warn(`구역 '${x.name}': 줄표·가운뎃점으로 잇지 말고 하는 일을 한 말로 ("밤 — 측정" → "밤에 재기", "추이·병원" → "기록 살펴보기")`, "sections-count");
      if (/추이|현황|관리|통계|대시보드|온보딩|피드/.test(x.name)) warn(`구역 '${x.name}': 어려운 말 — 사용자가 하는 일로 ("추이" → "기록 살펴보기", "온보딩" → "처음 시작하기")`, "sections-count");
    }
    if (typeof x.desc === "string" && x.desc.length > secDesc) warn(`구역 '${x.name}': desc는 ${secDesc}자 이내 한 줄로`, "sections-count");
  }
  const stepMax = V("step-label", "max", 14);
  const pBlocks = V("policy-required", "blocks", 4), pLines = V("policy-required", "lines", 6), pChars = V("policy-required", "chars", 70);
  const used = new Set(), lastStep = new Map();   // 같은 단계 이름표는 한 구역 안에서 붙어 있어야 한다
  for (const s of S.screens || []) {
    const desc = `화면 ${s.slug}`;
    if (!s.section) fail(`${desc}: section 없음 — 어느 구역에 놓일지`, "sections-count");
    else if (SEC.length && !secKeys.has(s.section)) fail(`${desc}: section '${s.section}'이 sections에 없음`, "sections-count");
    used.add(s.section);
    if (!s.step) fail(`${desc}: step 없음 — 화면 위 단계 이름표 (예: "약관 동의", "닉네임 입력"). 상태만 다른 화면은 원래 화면과 같은 이름표`, "step-label");
    else {
      if (s.step.length > stepMax) warn(`${desc}: 단계 이름표 "${s.step}" — ${stepMax}자 이내로`, "step-label");
      const k = s.section + "|" + s.step, prev = lastStep.get(s.section);
      if (prev && prev !== k && [...lastStep.values()].includes(k)) warn(`${desc}: 단계 '${s.step}' 화면들이 떨어져 있음 — screens.json에서 같은 단계 화면을 붙여 둔다`, "step-label");
      lastStep.set(s.section, k);
    }
    // 정책 메모: 화면 아래 검은 상자. 상태만 다른 화면(variantOf)은 선택 — 묶음 형식은 schema가 본다
    const P = s.policy;
    if (P === undefined || (Array.isArray(P) && !P.length)) { if (!s.variantOf) fail(`${desc}: policy 없음 — 이 화면의 규칙(처음 상태·제한·예외·표기)을 [{ "title": "기본 정의", "items": ["…"] }]로`, "policy-required"); continue; }
    if (!Array.isArray(P)) continue;
    if (P.length > pBlocks) warn(`${desc}: 정책 묶음 ${P.length}개 — ${pBlocks}개 이하로`, "policy-required");
    for (const b of P) {
      if (!b || !Array.isArray(b.items)) continue;
      if (b.items.length > pLines) warn(`${desc}: 정책 '${b.title}' 줄 ${b.items.length}개 — ${pLines}줄 이하로`, "policy-required");
      for (const it of b.items) {
        if (typeof it !== "string") continue;
        if (it.length > pChars) warn(`${desc}: 정책 줄이 김(${it.length}자) — 한 줄에 규칙 하나, ${pChars}자 이내 "${it.slice(0, 24)}…"`, "policy-required");
        const j = it.match(JARGON); if (j) warn(`${desc}: 정책 줄에 컴포넌트 용어 '${j[0]}' — 일상어로 ("바텀시트" → "아래에서 올라오는 창")`, "label-plain");
      }
    }
  }
  for (const x of SEC) if (!used.has(x.key)) warn(`구역 '${x.name}': 화면이 하나도 없음`, "sections-count");
  // 안내·예외 (사용자: "지우기 같은 행동에 안내·오류 문구가 없다", "엣지 케이스나 글자 수 제한도") — prd-to-screens §5-4
  const caseChars = V("cases-edge", "chars", 50);
  const isForm = (s) => s.pattern === "입력폼" || s.pattern === "form";   // form은 옛 값
  for (const s of S.screens || []) {
    const desc = `화면 ${s.slug}`;
    // cases 형식 · tone 값은 schema가 본다
    for (const c of Array.isArray(s.cases) ? s.cases : []) if (c && typeof c.show === "string" && c.show.length > caseChars) warn(`${desc}: 안내 문구 ${caseChars}자 이내로 "${c.show.slice(0, 20)}…"`, "cases-edge");
    const html = htmlBySlug[s.slug] || "";
    for (const m of html.matchAll(/<(input|textarea)\b([^>]*)>/g)) {
      if (/type="(checkbox|radio|hidden|range|date|time)"/.test(m[2])) continue;
      if (!/maxlength="\d+"/.test(m[2])) warn(`${desc}: 글자 칸에 maxlength 없음 — 글자 수 제한을 정해 maxlength(필요하면 minlength)로 (완성본에서 '3/20'이 보인다)`);
    }
    for (const m of html.matchAll(/data-stay-tone="([^"]*)"/g)) if (!TONES.includes(m[1])) fail(`${desc}: data-stay-tone은 ${TONES.join("|")}`);
    if (!s.overlayOf) for (const m of html.matchAll(/<(button|a)\b([^>]*\bdata-stay="[^"]*"[^>]*)>([\s\S]*?)<\/\1>/g)) {
      const t = m[3].replace(/<[^>]+>/g, "").trim();
      if (/btn-danger/.test(m[2]) || /지우기|삭제|탈퇴|해지|초기화/.test(t)) warn(`${desc}: 되돌릴 수 없는 버튼 '${t}'이 바로 끝남 — 확인 창(뜨는 창 화면 + 갈래)을 거치게`);
    }
    if (isForm(s) && !s.variantOf && !s.state && !(s.cases || []).length) warn(`${desc}: 입력 화면인데 cases(엣지 케이스: 빈칸·너무 김·겹침·실패) 없음 — 그때 보여 줄 문구를 정한다`, "cases-edge");
  }
  // 움직임(motion): 완성본에서 실제로 재현된다(packages/core/motion). 정책에 글로만 적지 않는다
  // 종류 · note · 종류별 대상 칸(region · trigger) · ms 범위는 schema가 본다 — 여기서는 대상이 조각에 있는지
  for (const s of S.screens || []) {
    const desc = `화면 ${s.slug}`;
    if ((Array.isArray(s.policy) ? s.policy : []).some((b) => b && /움직임/.test(b.title || ""))) warn(`${desc}: 정책에 [움직임]이 글로만 있음 — motion으로 옮기면 완성본에서 실제로 움직인다 (prd-to-screens §5-3)`);
    if (!Array.isArray(s.motion)) continue;
    const html = htmlBySlug[s.slug] || "";
    for (const m of s.motion) {
      if (!m || !MOTION.includes(m.type)) continue;
      const md = `${desc} 움직임 ${m.type}`;
      if (typeof m.note === "string" && m.note.length > 44) warn(`${md}: note 44자 이내로`);
      if (!html) continue;
      const hasReg = (k) => html.includes(`data-region="${k}"`), hasTrig = (k) => html.includes(`data-trigger="${k}"`);
      if (m.region && !hasReg(m.region)) fail(`${md}: region '${m.region}'이 조각에 data-region으로 없음`, "motion-target");
      if (m.trigger && !hasTrig(m.trigger)) fail(`${md}: trigger '${m.trigger}'가 조각에 data-trigger로 없음`, "motion-target");
      // 옛 칸 target — 새 칸(region · trigger)이 없을 때만 읽는다
      if (m.target && !m.region && !m.trigger) {
        const need = MOTION_NEEDS[m.type] || [];
        const ok = need.length === 1 ? (need[0] === "trigger" ? hasTrig(m.target) : hasReg(m.target)) : hasReg(m.target) || hasTrig(m.target);
        if (!ok) fail(`${md}: target '${m.target}'이 조각에 없음`, "motion-target");
      }
    }
  }
  // 오류·완료 상태: 사용자가 밟게 될 상태는 반드시 그린다
  const all = [...slugs.values()];
  const inputs = all.filter((s) => !s.state && isForm(s) && !s.variantOf);
  if (inputs.length && !all.some((s) => s.state === "error")) fail(`오류 상태 화면이 없음 — 입력하는 화면(${inputs.slice(0, 3).map((s) => s.slug).join(", ")}…) 중 핵심 하나 이상에 state "error" 변형(variantOf)`, "state-pair");
  if (!all.some((s) => s.state === "success")) fail(`완료 상태 화면이 없음 — 핵심 작업이 끝났을 때(저장·예약·보내기 완료) state "success" 변형(variantOf) 하나 이상`, "state-pair");
  for (const s of inputs.filter((x) => !x.overlayOf)) if (!all.some((v) => v.variantOf === s.slug && v.state === "error")) warn(`화면 ${s.slug}: 입력하는 화면인데 오류 상태가 없음 — 틀리기 쉬운 입력이면 state "error" 변형을 더한다`, "state-pair");
}

// ---------- branches (갈래: 흐름 밖의 버튼이 여는 화면) ----------
// 뜨는 창을 여는 갈래가 있는지(overlay-reached) · 같은 버튼 갈래의 when(split-when)은 lint-rules.js가 본다
const branchTo = new Map(); // "from|trigger" → to
const stepTo = new Map();   // "from|trigger" → to
for (const f of F.flows || []) for (const st of f.steps || []) if (st.trigger) stepTo.set(st.from + "|" + st.trigger, st.to);
(Array.isArray(F.branches) ? F.branches : []).forEach((b, i) => {
  const bd = `갈래 ${i + 1} (${b.from || "?"} → ${b.to || "?"})`;
  if (!slugs.has(b.from)) { fail(`${bd}: from '${b.from}' 화면 없음`); return; }
  if (!slugs.has(b.to)) fail(`${bd}: to '${b.to}' 화면 없음`);
  if (b.from === b.to) fail(`${bd}: 같은 화면으로 가는 갈래 — 그 자리에서 바뀌는 버튼은 조각에 data-stay`);
  checkWhen(b, bd);
  const keys = regionKeysBySlug.get(b.from) || new Set();
  if (b.region && !keys.has(b.region)) fail(`${bd}: region '${b.region}'이 '${b.from}' 화면 영역에 없음`);
  if (!b.trigger) return;   // 필수 칸은 schema가 본다
  const trig = triggersBySlug.get(b.from) || new Map();
  if (!triggersBySlug.has(b.from)) { /* 조각 전 — 건너뜀 */ }
  else if (!trig.has(b.trigger)) fail(`${bd}: trigger '${b.trigger}'가 '${b.from}' 조각에 data-trigger로 없음`);
  else if (b.region && trig.get(b.trigger) !== b.region) warn(`${bd}: trigger '${b.trigger}'가 region '${b.region}' 안에 있지 않음 (실제: ${trig.get(b.trigger) || "영역 밖"})`);
  const k = b.from + "|" + b.trigger;
  if (stepTo.has(k) && !b.when) fail(`${bd}: trigger '${b.trigger}'는 이미 흐름 단계에 있음 — 갈래에서 빼거나, 조건이 갈리면 둘 다 when`);
  if (branchTo.has(k) && !b.when) fail(`${bd}: trigger '${b.trigger}' 갈래 중복`);
  branchTo.set(k, b.to);
  reached.add(b.from); reached.add(b.to);
});

// ---------- 버튼마다 누르면 어떻게 되는지 (계약 §6.2) ----------
// 글자가 있는 .btn은 셋 중 하나: data-trigger(흐름 단계·갈래로 다른 화면) / data-back(되돌아가기) / data-stay(그 자리에서 바뀜)
for (const [slug, btns] of buttonsBySlug) {
  const lost = [], orphan = [];
  // 같은 일을 하는 버튼이 여러 개(목록 행마다 '예약하기')면 트리거는 한 곳에만 — 글자가 같은 트리거 버튼이 있으면 통과(00-rules 3-2)
  const trigTexts = new Set(btns.filter((b) => b.trigger).map((b) => b.text));
  // 상태만 다른 화면(variantOf)은 원래 화면의 버튼 연결을 그대로 쓴다
  const from = [slug, (slugs.get(slug) || {}).variantOf].filter(Boolean);
  for (const b of btns) {
    if (b.trigger) { if (!from.some((f) => stepTo.has(f + "|" + b.trigger) || branchTo.has(f + "|" + b.trigger))) orphan.push(b.text); }
    else if (!b.stay && !b.back && !b.out && !trigTexts.has(b.text)) lost.push(b.text);
  }
  if (lost.length) fail(`화면 ${slug}: 누르면 어떻게 되는지 없는 버튼 ${lost.map((t) => `'${t}'`).join(", ")} — 다른 화면이면 data-trigger + flow.json branches, 되돌아가면 data-back, 그 자리에서 바뀌면 data-stay="바뀐 뒤 안내 문구"`);
  if (orphan.length) warn(`화면 ${slug}: data-trigger가 있는데 흐름·갈래에 없는 버튼 ${orphan.map((t) => `'${t}'`).join(", ")}`);
}
for (const slug of slugs.keys()) {
  if (!reached.has(slug) && !slugs.get(slug).variantOf) warn(`화면 '${slug}' 은 어떤 플로우에도 등장하지 않음 — 구역 보드에는 놓이지만 어떤 버튼으로 오는지 알 수 없음`);
}

// ---------- 위계 — 1순위 문장 · 영역 모양(regions[].form) · 큰 글자 ----------
// 1순위 영역이 하나인지 · focus와 같은지(rank1-one) · 3순위 수(rank3-max)는 lint-rules.js가 본다
function regionOfClass(html, clsName) {
  const out = [], stack = [];
  const voids = new Set(["br", "hr", "img", "input", "use", "path", "circle", "rect", "line", "polyline", "polygon", "meta", "link"]);
  for (const m of html.matchAll(/<(\/?)([a-zA-Z][\w-]*)([^>]*?)(\/?)>/g)) {
    const [, close, tagRaw, attrs, selfClose] = m, tag = tagRaw.toLowerCase();
    if (close) { for (let i = stack.length - 1; i >= 0; i--) if (stack[i].tag === tag) { stack.length = i; break; } continue; }
    const region = (/data-region\s*=\s*["']([^"']+)["']/.exec(attrs) || [])[1] || null;
    const cls = ((/class\s*=\s*["']([^"']*)["']/.exec(attrs) || [])[1] || "").split(/\s+/);
    if (cls.includes(clsName)) out.push(region || [...stack].reverse().find((x) => x.region)?.region || null);
    if (!selfClose && !voids.has(tag)) stack.push({ tag, region });
  }
  return out;
}
const CALENDAR_CLS = ["calendar", "calendar-month", "week-grid"];
function checkHierarchy(sc, html, desc) {
  const levels = new Map((sc.regions || []).filter((r) => r.level).map((r) => [r.key, r.level]));
  const len = (t) => t.replace(/\s/g, "").length;
  const e1 = V("emphasize-length", "emphasize", 30), e2 = V("emphasize-length", "emphasize2", 40);
  if (typeof sc.emphasize === "string" && len(sc.emphasize) > e1) warn(`${desc}: 1순위 문장(emphasize)이 ${len(sc.emphasize)}자 — ${e1}자 안팎 한 줄로, 넘치면 뒷부분을 emphasize2로`, "emphasize-length");
  if (typeof sc.emphasize2 === "string" && len(sc.emphasize2) > e2) warn(`${desc}: 1순위 아래 한 줄(emphasize2)이 ${len(sc.emphasize2)}자 — 한 줄로(${e2}자 안팎)`, "emphasize-length");
  // 세로 간격은 의미 클래스로: .stack에 큰 숫자 간격을 붙이면 간격 단계를 우회한다
  const numGap = [...html.matchAll(/class=["'][^"']*\bstack\b[^"']*\bgap-(4|6)\b/g)].length;
  if (numGap) warn(`${desc}: .stack에 숫자 간격(gap-4·gap-6) ${numGap}곳 — 묶음 사이는 .stack-group, 큰 덩어리 사이는 .stack-page`);
  // 영역 모양 — 없음 · 없는 값은 schema가 알린다(값 목록은 정본 region.form)
  const inRegion = (cls) => { const m = new Map(); for (const k of regionOfClass(html, cls)) if (k) m.set(k, (m.get(k) || 0) + 1); return m; };
  const cnt = Object.fromEntries(["split", "grid-2", "grid-3", "card", "stat", "card-title", "t-title", "list-item", "table", "timeline-item", ...CALENDAR_CLS].map((c) => [c, inRegion(c)]));
  for (const r of sc.regions || []) {
    if (!r || !FORMS.includes(r.form)) continue;
    const rd = `${desc} 영역 '${r.key}'`, n = (c) => cnt[c].get(r.key) || 0;
    // 입력 화면의 1순위는 입력폼 그 자체(KRDS 입력폼 패턴) — hero 요구에서 뺀다
    if (r.level === 1 && r.form !== "hero" && r.form !== "form" && !r.signature) fail(`${rd}: 1순위 영역은 모양 hero(한 칸 큰 글) — 지금 ${r.form}`, "rank1-hero");
    // 숫자 칸 하나는 한 칸 큰 글 — 둘 이상이면 칸 나누기(stat-row)
    if (r.form === "hero" && (n("split") || n("grid-2") || n("grid-3") || n("card") || n("stat") > 1)) fail(`${rd}: hero인데 칸 나누기·카드·숫자 칸이 있음(split ${n("split")} · grid ${n("grid-2") + n("grid-3")} · card ${n("card")} · stat ${n("stat")}) — 한 칸 큰 글로`, "rank1-hero");
    if (r.form === "cards" && n("card") && n("card-title") + n("t-title") > n("card") + 1) fail(`${rd}: 카드 ${n("card")}장에 제목 ${n("card-title") + n("t-title")}개 — 카드 한 장에 제목 하나 + 영역 제목 하나(머리글은 .t-caption)`);
    if (r.form === "list" && !n("list-item")) warn(`${rd}: 모양 list인데 .list-item 없음`);
    if (r.form === "list" && n("t-title") + n("card-title") > 1) fail(`${rd}: 목록에 제목 크기 글자(.t-title·card-title) ${n("t-title") + n("card-title")}개 — 영역 제목 하나만, 줄 제목은 .list-title`);
    if (r.form === "table" && !n("table")) warn(`${rd}: 모양 table인데 표(.table) 없음`);
    if (r.form === "timeline" && !n("timeline-item")) warn(`${rd}: 모양 timeline인데 .timeline-item 없음 — 한 줄은 시각(.timeline-time) · 점(.timeline-dot) · 내용(.timeline-content)`, "repeat-unit");
    if (r.form === "calendar" && !CALENDAR_CLS.some((c) => n(c))) warn(`${rd}: 모양 calendar인데 달력(.calendar-month · .week-grid) 없음 — 월 달력은 node scripts/calendar.js로`, "calendar-state");
  }
  // 화면당 제목급 글자 수 — 제목이 많으면 아무것도 제목이 아니다
  const titles = [...html.matchAll(/class=["'][^"']*\b(t-title|card-title)\b/g)].length;
  const nReg = (sc.regions || []).length;
  if (nReg && titles > nReg + 2) warn(`${desc}: 제목급 글자(.t-title·card-title) ${titles}개 — 영역 ${nReg}개 + 2 이하로 (반복 줄의 제목은 .list-title·굵은 본문)`);
  if (!levels.size) return;
  for (const k of regionOfClass(html, "t-display")) {
    const sig = (sc.regions || []).some((r) => r.key === k && r.signature);   // 시안 특징 장치 영역은 핵심 값 하나를 크게 쓸 수 있다
    if (!k || (levels.get(k) !== 1 && !sig)) fail(`${desc}: 큰 제목(.t-display)이 1순위가 아닌 곳(${k || "영역 밖"})에 있음`, "display-only-emphasize");
  }
  // 큰 제목은 내용에 쓴다 — 영역·페이지 제목(h1~h3)에 .t-display를 쓰면 제목이 내용을 이긴다
  const headDisplay = [...html.matchAll(/<h[1-3]\b[^>]*class=["'][^"']*\bt-display\b[^"']*["'][^>]*>([\s\S]*?)<\/h[1-3]>/g)].map((m) => m[1].replace(/<[^>]+>/g, "").trim());
  if (headDisplay.length) warn(`${desc}: 큰 제목(.t-display)이 제목 줄에 쓰임 ${headDisplay.map((t) => `'${t}'`).join(", ")} — 큰 글자는 1순위 내용(예: 다음 일정·바뀐 값)에`, "display-only-emphasize");
}
for (const sc of slugs.values()) if (htmlBySlug[sc.slug] !== undefined) checkHierarchy(sc, htmlBySlug[sc.slug], `화면 ${sc.slug}`);
for (const c of S.concepts || []) for (const slug of c.screens || []) {
  const fp = path.join(runDir, "concepts", c.id || "", slug + ".html");
  if (slugs.has(slug) && exists(fp)) checkHierarchy(slugs.get(slug), fs.readFileSync(fp, "utf8"), `시안 ${c.id} / ${slug}`);
}

// ---------- icons.json ----------
{
  const seen = new Map();
  for (const [k, v] of Object.entries(projectIcons)) {
    if (k.startsWith("_")) continue;
    if (!spriteIds.has(v)) fail(`icons.json '${k}': '${v}' 은 lucide 스프라이트에 없음`);
    if (seen.has(v)) fail(`icons.json: 아이콘 '${v}' 이 두 의미(${seen.get(v)}, ${k})에 쓰임`);
    seen.set(v, k);
  }
}

// ---------- board 설정 (있으면) — 질문 형식 · 수(board-ask)는 schema가 본다 ----------
if (S.board && S.board.hero && !slugs.has(S.board.hero)) fail(`board.hero '${S.board.hero}' 화면 없음`);

// ---------- 시안(concepts) · 레퍼런스 — references/prd-to-screens.md §7 ----------
// 필수 칸 · 시안 id 형식 · 플랫폼별 메뉴 틀 값(shell-platform)은 schema가 본다
if (S.concepts !== undefined) {
  const C = Array.isArray(S.concepts) ? S.concepts : [];
  const SHELLS = conceptShells(platform);
  const shellClass = SHELL_CLASS[platform] || SHELL_CLASS.web;
  const nConcepts = V("concepts-count", "count", 5);
  if (C.length !== nConcepts) warn(`시안은 ${nConcepts}개 (지금 ${C.length}개)`, "concepts-count");
  const lookIds = new Set(LK.getLooks(S).map((l) => l.id));
  const cids = new Set();
  const [scrMin, scrMax] = [V("concept-screens", "min", 3), V("concept-screens", "max", 6)];
  for (const c of C) {
    const cd = `시안 ${c.id || "?"}`;
    if (cids.has(c.id)) fail(`${cd}: id 중복`); cids.add(c.id);
    if (typeof c.name === "string" && /[a-z]{3,}|시안|레이아웃|대시보드형|타입/i.test(c.name)) warn(`${cd}: 이름 "${c.name}" — 무엇이 먼저 보이는지 일상어로 (예: "오늘 할 일부터 보기")`);
    if (c.look !== undefined && !lookIds.has(c.look)) fail(`${cd}: look '${c.look}'이 looks에 없음`);
    if (Array.isArray(c.refs) && !c.refs.length) warn(`${cd}: 참고한 곳(refs) 없음 — 레퍼런스에서 무엇을 가져왔는지`);
    const scr = Array.isArray(c.screens) ? c.screens : [];
    if (scr.length < scrMin) warn(`${cd}: 보여줄 메인 화면은 ${scrMin}~${scrMax}장 (지금 ${scr.length}장) — 역할별 메뉴 화면부터`, "concept-screens");
    if (scr.length > scrMax) fail(`${cd}: 보여줄 메인 화면은 최대 ${scrMax}장 (지금 ${scr.length}장) — 1턴이 길어지고 비교하기 어렵다`, "concept-screens");
    for (const slug of scr) if (!slugs.has(slug)) fail(`${cd}: 화면 '${slug}' 없음`);
  }
  const main = C.find((c) => c.id === S.concept) || C[0];
  if (S.concept && !cids.has(S.concept)) fail(`screens.json concept '${S.concept}'이 concepts에 없음`);
  if (C.length > 1 && new Set(C.map((c) => c.shell)).size < Math.min(SHELLS.length, C.length))
    warn(`시안끼리 메뉴 구조(shell)가 ${new Set(C.map((c) => c.shell)).size}가지뿐 — ${SHELLS.join("·")}을 모두 쓴다`, "shell-spread");
  const combo = new Set(C.map((c) => c.shell + "|" + c.look));
  if (combo.size < C.length) warn(`메뉴 구조와 분위기가 똑같은 시안이 있음 — 첫 화면 구성·밀도까지 다르게`);
  const names = C.map((c) => c.home || "").filter(Boolean);
  if (names.length === C.length && new Set(names).size < C.length) warn(`첫 화면 구성(home)이 겹치는 시안이 있음`);
  // 시안의 메인 화면 조각
  for (const c of C) {
    if (!main || (c.id === main.id && S.stage !== "concept")) continue;   // 시안 단계에서는 추천 시안도 concepts/<id>/에
    for (const slug of c.screens || []) {
      const fp = path.join(runDir, "concepts", c.id || "", slug + ".html"), cd = `시안 ${c.id} / ${slug}`;
      if (!exists(fp)) { fail(`${cd}: 조각 없음 (concepts/${c.id}/${slug}.html)`); continue; }
      const html = fs.readFileSync(fp, "utf8");
      if (/<\s*(html|head|body|style|script|link)\b/i.test(html)) fail(`${cd}: <html|head|body|style|script|link> 금지`);
      if (/\sstyle\s*=\s*["']/i.test(html)) fail(`${cd}: 인라인 style 금지`);
      for (const m of html.matchAll(/href\s*=\s*["']#i-([a-z0-9-]+)["']/g)) if (!allowed.has(m[1])) fail(`${cd}: 아이콘 '${m[1]}' 허용 목록에 없음`);
      // 2턴에 screens/로 그대로 옮겨 쓰므로 영역·연결도 원래 화면 기준으로 본다
      const sc = slugs.get(slug), keys = new Set(((sc && sc.regions) || []).map((r) => r.key));
      const regs = [...html.matchAll(/data-region\s*=\s*["']([^"']+)["']/g)].map((m) => m[1]);
      for (const k of keys) if (!regs.includes(k)) warn(`${cd}: 영역 '${k}'이 없음 — 고르면 옮겨 쓸 때 다시 붙여야 함`);
      const trigs = [...html.matchAll(/data-trigger\s*=\s*["']([^"']+)["']/g)].map((m) => m[1]);
      for (const k of new Set(trigs.filter((k, i) => trigs.indexOf(k) !== i))) fail(`${cd}: data-trigger="${k}" 가 2번 이상 — 같은 버튼이 여럿이면 한 곳에만(00-rules 3-2)`);
      const want = shellClass[c.shell];
      const appCls = ((/<div\s+class=["']([^"']*\bapp\b[^"']*)["']/.exec(html) || [])[1] || "").split(/\s+/);
      const hasNav = /class=["'][^"']*\bnav-item\b/.test(html);   // 모바일에서 메뉴 밖 화면은 뒤로 버튼만 — 메뉴 구조를 보지 않는다
      if (want && !appCls.includes(want) && (platform !== "mobile" || hasNav)) warn(`${cd}: 시안 메뉴 구조가 ${c.shell}인데 .app에 ${want} 없음`);
      if (knownClasses.size) {
        const unknown = new Set();
        for (const m of html.matchAll(/class\s*=\s*["']([^"']+)["']/g)) for (const k of m[1].split(/\s+/).filter(Boolean)) if (!knownClasses.has(k) && !k.startsWith("hx-")) unknown.add(k);
        if (unknown.size) warn(`${cd}: components.css에 없는 클래스 ${[...unknown].map((k) => `'${k}'`).join(", ")}`);
      }
    }
  }
  // 지금 화면들이 고른 시안의 메뉴 구조를 따르는지
  if (main && shellClass[main.shell]) for (const s of slugs.values()) {
    const html = htmlBySlug[s.slug];
    if (s.overlayOf || html === undefined) continue;
    if (!/class=["'][^"']*\bnav-item\b/.test(html)) continue;   // 메뉴 없는 화면(초대 받았을 때 등 가운데 한 장)은 제외
    const appCls = ((/<div\s+class=["']([^"']*\bapp\b[^"']*)["']/.exec(html) || [])[1] || "").split(/\s+/);
    if (!appCls.includes(shellClass[main.shell])) warn(`화면 ${s.slug}: 시안 ${main.id}의 메뉴 구조(${main.shell})인데 .app에 ${shellClass[main.shell]} 없음`);
  }
  const R = Array.isArray(S.references) ? S.references : [];
  if (R.length < 3) warn(`살펴본 서비스(references) ${R.length}곳 — 5곳 정도 조사해 시안의 근거로 (ref-scout)`);
}

// ---------- 새 규칙 — scripts/lint-rules.js check(ctx) (rules.json의 값 · 단계로) ----------
if (exists(path.join(__dirname, "lint-rules.js"))) {
  const { check } = require("./lint-rules.js");
  check({
    dir: runDir, screens: S, flow: F, html: htmlBySlug, rules: SCHEMA.RULES,
    report: (level, ruleId, where, msg) => (level === "FAIL" ? fail : warn)(`${where}: ${msg}`, ruleId),
  });
}

// ---------- 출력 ----------
for (const w of warns) console.log(`[WARN] ${w}`);
for (const f of fails) console.log(`[FAIL] ${f}`);
const said = [...ruleHit].filter((id) => RULES.has(id) && RULES.get(id).says);
if (said.length) {
  console.log(`[규칙] 위 메시지 앞의 규칙 id — packages/core/schema/rules.json`);
  for (const id of said) console.log(`  ${id}: ${RULES.get(id).says}`);
}
const nScreens = (S.screens || []).length;
const nRegions = (S.screens || []).reduce((n, s) => n + (s.regions || []).length, 0);
console.log(`[lint] 화면 ${nScreens} · 영역 ${nRegions} · 구역 ${(S.sections || []).length} · 플로우 ${(F.flows || []).length} · 갈래 ${(F.branches || []).length} · FAIL ${fails.length} · WARN ${warns.length}`);
process.exit(fails.length || (strict && warns.length) ? 1 : 0);
