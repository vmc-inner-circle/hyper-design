#!/usr/bin/env node
/**
 * lint.js — run 폴더의 데이터·조각이 계약(docs/harness-design.md §10)을 지키는지 검사한다.
 *
 *   node scripts/lint.js runs/<project> [--strict]
 *
 * exit 0 = 통과. FAIL이 하나라도 있으면 exit 1. WARN은 exit에 영향 없음(--strict면 실패).
 * LLM 자기보고 대신 이 스크립트가 "끝났다"를 판정한다.
 */
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const args = process.argv.slice(2);
const runDir = args.find((a) => !a.startsWith("--"));
const strict = args.includes("--strict");
if (!runDir) {
  console.error("usage: node scripts/lint.js runs/<project> [--strict]");
  process.exit(2);
}

const fails = [];
const warns = [];
const fail = (m) => fails.push(m);
const warn = (m) => warns.push(m);
const readJSON = (p) => JSON.parse(fs.readFileSync(p, "utf8"));
const exists = (p) => fs.existsSync(p);

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

// ---------- 메타 ----------
if (!["web", "mobile"].includes(platform)) fail(`screens.json platform은 web|mobile 여야 함 (지금: ${platform})`);
if (!S.toggles || !["normal", "large"].includes(S.toggles.type)) fail(`toggles.type은 normal|large 여야 함`);
// ---------- 분위기(looks)·버튼 색(swatches) — references/prd-to-screens.md §6 ----------
{
  const LK = require("./looks.js");
  if (!Array.isArray(S.looks) || !S.looks.length) warn(`looks 없음 — 기본 분위기(깔끔한 흰색/따뜻한 크림/차분한 밤)를 쓴다. PRD에 맞춘 분위기 3개와 버튼 색을 만든다`);
  const looks = LK.getLooks(S);
  if (S.looks && (S.looks.length < 3 || S.looks.length > 5)) warn(`분위기는 3~5개 (지금 ${S.looks.length}개, 시안마다 하나씩)`);
  const lookIds = new Set();
  for (const L of looks) {
    const ld = `분위기 '${L.name || L.id}'`;
    if (!L.id || !/^[a-z0-9-]+$/.test(L.id)) fail(`${ld}: id는 영문 소문자`);
    if (lookIds.has(L.id)) fail(`${ld}: id 중복`); lookIds.add(L.id);
    if (!L.name) fail(`${ld}: name 없음 (사용자에게 보이는 이름, 예: "따뜻한 크림")`);
    else if (/[a-z]|#|테마|톤$/i.test(L.name)) warn(`${ld}: 이름은 한국어 일상어로 (예: "따뜻한 크림", "밤 바다")`);
    if (!["light", "dark"].includes(L.mode)) fail(`${ld}: mode는 light|dark`);
    if (!["soft", "round", "sharp"].includes(L.shape)) fail(`${ld}: shape는 soft|round|sharp`);
    let ok = true;
    try { LK.hex2rgb(L.bg); LK.hex2rgb(L.ink); } catch (e) { fail(`${ld}: bg·ink는 #RRGGBB`); ok = false; }
    if (ok) {
      const c = LK.contrast(L.ink, L.bg);
      if (c < 4.5) fail(`${ld}: 글자와 배경 대비 ${c.toFixed(1)} (4.5 이상)`); else if (c < 7) warn(`${ld}: 글자와 배경 대비 ${c.toFixed(1)} (7 이상 권장)`);
      if (L.mode === "dark" && LK.contrast(L.bg, "#000000") > 3) warn(`${ld}: mode dark인데 배경이 밝음`);
      if (L.mode === "light" && LK.contrast(L.bg, "#FFFFFF") > 1.4) warn(`${ld}: mode light인데 배경이 어두움`);
    }
    const sws = L.swatches || [];
    if (sws.length !== 5) warn(`${ld}: 버튼 색은 5개 (지금 ${sws.length}개, 첫 번째가 추천)`);
    const swIds = new Set();
    for (const sw of sws) {
      const sd = `${ld} 버튼 색 '${sw.name || sw.id}'`;
      if (!sw.id || !/^[a-z0-9-]+$/.test(sw.id)) fail(`${sd}: id는 영문 소문자`);
      if (swIds.has(sw.id)) fail(`${sd}: id 중복`); swIds.add(sw.id);
      if (!sw.name || /#|[a-z]/i.test(sw.name)) warn(`${sd}: 이름은 한국어 색 이름으로 (예: "테라코타", "바다 파랑")`);
      try {
        const fg = LK.swatchTokens(L, sw)["--c-primary-fg"];
        const c = LK.contrast(sw.hex, fg);
        if (c < 3) fail(`${sd}: 버튼 위 글자 대비 ${c.toFixed(1)} (3 이상)`);
        if (ok && LK.contrast(sw.hex, L.bg) < 1.6) warn(`${sd}: 배경과 너무 비슷해 버튼이 안 보일 수 있음`);
      } catch (e) { fail(`${sd}: hex는 #RRGGBB`); }
    }
  }
  if (!lookIds.has(S.theme)) fail(`screens.json theme '${S.theme}'이 looks에 없음`);
  const cur = looks.find((l) => l.id === S.theme);
  const sw = S.toggles && (S.toggles.swatch || S.toggles.accent);
  if (cur && sw && !["calm", "vivid"].includes(sw) && !(cur.swatches || []).some((x) => x.id === sw)) fail(`toggles.swatch '${sw}'이 분위기 '${cur.id}'의 버튼 색에 없음`);
  const rec = S.board && S.board.recommend;
  if (rec && rec.theme && !lookIds.has(rec.theme)) fail(`board.recommend.theme '${rec.theme}'이 looks에 없음`);
}
if (!Array.isArray(S.screens) || S.screens.length === 0) fail(`screens가 비어 있음`);
const roleKeys = new Set((S.roles || []).map((r) => r.key));

// ---------- 화면·영역·id ----------
const ids = new Map(); // id → 설명
const slugs = new Map(); // slug → screen
const regionKeysBySlug = new Map();
const triggersBySlug = new Map(); // slug → Map(triggerKey → 속한 region key | null)
const buttonsBySlug = new Map(); // slug → [{ text, trigger, stay, back }] — 글자가 있는 .btn

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

const STATES = ["first-run", "empty", "input", "error", "success"];
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
}
// 조건 이름표(when): 구역 보드는 화면을 순서대로 나란히 놓고, 조건이 갈리는 곳에만 화살표 + 이 이름표를 단다
function checkWhen(x, d) {
  if (x.when === undefined) return;
  if (typeof x.when !== "string" || !x.when.trim()) fail(`${d}: when은 조건 한 마디 (예: "처음 가입이면")`);
  else if (x.when.length > 16) warn(`${d}: 조건 이름표 "${x.when}" — 16자 이내로`);
}
// 사용자는 컴포넌트를 모른다 — 보이는 이름·정책 메모에 컴포넌트 용어 금지
const JARGON = /카드|띠|배너|스트립|패널|서랍|드로어|모달|바텀시트|탭|칩|배지|세그먼트|토글|스위치|리스트|타임라인|섹션|영역|위젯|컴포넌트|CTA|랜딩/;
for (const s of S.screens || []) {
  const desc = `화면 ${s.slug || "(slug 없음)"}`;
  if (!s.slug || !/^[a-z0-9]+(-[a-z0-9]+)*$/.test(s.slug)) fail(`${desc}: slug는 케밥케이스 영문이어야 함`);
  if (slugs.has(s.slug)) fail(`slug 중복: ${s.slug}`);
  slugs.set(s.slug, s);
  if (!s.name) fail(`${desc}: name 없음`);
  if (!s.file) fail(`${desc}: file 없음`);
  if (s.role && roleKeys.size && !roleKeys.has(s.role)) fail(`${desc}: role '${s.role}'이 roles에 없음`);
  if (s.state && !STATES.includes(s.state)) fail(`${desc}: state는 ${STATES.join("|")} 중 하나`);
  if ((s.state === "error" || s.state === "success") && !s.when) warn(`${desc}: ${s.state === "error" ? "오류" : "완료"} 화면이 언제 나오는지(when) 없음 — 예: "마이크를 허용하지 않았을 때" (보드에서 화면 위 말풍선으로 보인다)`);
  if ((s.state === "error" || s.state === "success") && !s.variantOf) fail(`${desc}: ${s.state === "error" ? "오류" : "완료"} 상태 화면은 원래 화면을 variantOf로 가리킨다 (구역 보드에서 원래 화면 옆에 놓인다)`);
  noteId(s.id, desc);
  if (Number.isInteger(s.id) && s.id > 100) warn(`${desc}: 화면 번호 ${s.id} — 화면은 1, 2, 3…으로 (node scripts/ids.js가 발급)`);

  const regions = s.regions || [];
  if (regions.length === 0) warn(`${desc}: 영역이 0개 — 사용자가 가리킬 곳이 없음`);
  if (regions.length > 6) fail(`${desc}: 영역 ${regions.length}개 (최대 6)`);
  const keys = new Set();
  for (const r of regions) {
    const rd = `${s.slug} / ${r.key || "(key 없음)"}`;
    if (!r.key || !/^[a-z0-9]+(-[a-z0-9]+)*$/.test(r.key)) fail(`${rd}: region key는 케밥케이스 영문이어야 함`);
    if (keys.has(r.key)) fail(`${rd}: 같은 화면 안 key 중복`);
    keys.add(r.key);
    if (!r.label) fail(`${rd}: label 없음 (보드에 보이는 한글 이름)`);
    // 사용자는 컴포넌트를 모른다 — 번호를 누르면 보이는 이름에 컴포넌트 용어 금지
    const jargon = (r.label || "").match(JARGON);
    if (jargon) warn(`${rd}: label에 컴포넌트 용어 '${jargon[0]}' — '무엇이 보이는/하는 곳'으로 (예: "날짜 고르기")`);
    if (!r.why) warn(`${rd}: why 없음 — 번호를 누르면 보이는 "이게 뭐냐면" 한 문장`);
    noteId(r.id, `영역 ${rd}`);
    if (Number.isInteger(r.id) && r.id <= 100 && !Number.isInteger(S.nextId)) warn(`${rd}: 영역 번호 ${r.id} — 영역은 101부터 (화면 번호와 섞이지 않게)`);
  }
  regionKeysBySlug.set(s.slug, keys);

  // ----- 조각 파일 -----
  const fragPath = path.join(runDir, s.file || "");
  if (S.stage === "concept" && (!s.file || !exists(fragPath))) continue;   // 1턴 시안 단계: 전체 화면은 2턴에 만든다
  if (!s.file || !exists(fragPath)) { fail(`${desc}: 조각 파일 없음 (${s.file})`); continue; }
  const html = fs.readFileSync(fragPath, "utf8");

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

// ---------- roles[].nav ----------
for (const r of S.roles || []) {
  if (!r.nav) { warn(`역할 '${r.key}': nav 없음 — 화면마다 사이드바가 제각각이 된다 (references/prd-to-screens.md §2)`); continue; }
  for (const n of r.nav) {
    if (!slugs.has(n.slug)) fail(`역할 '${r.key}' nav: 화면 '${n.slug}' 없음`);
    if (!n.label) fail(`역할 '${r.key}' nav '${n.slug}': label 없음`);
    if (n.icon && !spriteIds.has(n.icon)) fail(`역할 '${r.key}' nav '${n.slug}': 아이콘 '${n.icon}' 스프라이트에 없음`);
    else if (n.icon && !allowed.has(n.icon)) fail(`역할 '${r.key}' nav '${n.slug}': 아이콘 '${n.icon}' allowlist/icons.json에 없음`);
  }
}

// ---------- flow ----------
if (!Array.isArray(F.flows) || F.flows.length === 0) fail(`flow.json flows가 비어 있음`);
const flowKeys = new Set();
const reached = new Set();
for (const f of F.flows || []) {
  const fd = `플로우 ${f.key || "(key 없음)"}`;
  if (!f.key) fail(`${fd}: key 없음`);
  if (flowKeys.has(f.key)) fail(`${fd}: key 중복`);
  flowKeys.add(f.key);
  if (!f.name) fail(`${fd}: name 없음`);
  // 흐름 제목은 디자인 산출물의 작업 이름: 짧은 '~하기' (문장·해요체·주어 금지)
  else if (!/기$/.test(f.name.trim())) warn(`${fd}: 제목 "${f.name}" — 짧은 '~하기' 작업 이름으로 (예: "첫 모임 만들기", "책 고르고 투표하기")`);
  else if (f.name.trim().length > 18) warn(`${fd}: 제목 "${f.name}" — 18자 이내로 짧게`);
  else if (/[·()]/.test(f.name)) warn(`${fd}: 제목에 가운뎃점·괄호 — 자연스러운 문장으로 ("비행기·숙소" → "비행기와 숙소")`);
  if (f.role && roleKeys.size && !roleKeys.has(f.role)) fail(`${fd}: role '${f.role}'이 roles에 없음`);
  if (!Array.isArray(f.steps) || f.steps.length === 0) { fail(`${fd}: steps 비어 있음`); continue; }
  f.steps.forEach((st, i) => {
    const sd = `${fd} step ${i + 1}`;
    // 흐름은 끊기지 않는 한 줄이어야 한다: 이번 step의 출발 화면 = 직전 step의 도착 화면
    if (i > 0 && st.from !== f.steps[i - 1].to) warn(`${sd}: 흐름이 끊김 ('${f.steps[i - 1].to}' 다음에 '${st.from}'에서 시작) — 별도 흐름으로 나눈다`);
    if (!slugs.has(st.from)) fail(`${sd}: from '${st.from}' 화면 없음`);
    if (!slugs.has(st.to)) fail(`${sd}: to '${st.to}' 화면 없음`);
    if (st.from && slugs.has(st.from)) {
      const keys = regionKeysBySlug.get(st.from) || new Set();
      if (!st.region) fail(`${sd}: region 없음 (어디를 누르는지)`);
      else if (!keys.has(st.region)) fail(`${sd}: region '${st.region}'이 '${st.from}' 화면 영역에 없음`);
    }
    if (!st.action) fail(`${sd}: action 문장 없음 ("'…'을 누르면")`);
    checkWhen(st, sd);
    // trigger: 화살표가 출발하는 실제 버튼/항목. 조각에 data-trigger="<key>"가 있어야 한다
    if (!st.trigger) warn(`${sd}: trigger 없음 — 화살표가 영역 덩어리에서 출발한다. 누르는 요소에 data-trigger를 붙이고 step.trigger로 지정`);
    else if (triggersBySlug.has(st.from)) {   // 조각을 아직 안 썼으면(1.2 단계) 건너뛴다
      const trig = triggersBySlug.get(st.from);
      if (!trig.has(st.trigger)) fail(`${sd}: trigger '${st.trigger}'가 '${st.from}' 조각에 data-trigger로 없음`);
      else if (st.region && trig.get(st.trigger) !== st.region) warn(`${sd}: trigger '${st.trigger}'가 region '${st.region}' 안에 있지 않음 (실제: ${trig.get(st.trigger) || "영역 밖"})`);
    }
    reached.add(st.from); reached.add(st.to);
  });
}
// 처음 시작 흐름: 빈 상태/첫 진입 화면이 하나도 없으면 비디자이너가 "처음엔 어떻게 보이지?"를 알 수 없다
if (![...slugs.values()].some((s) => s.state === "first-run" || s.state === "empty")) {
  warn(`처음 켰을 때·데이터 없을 때 화면이 없음 — 역할마다 '처음 시작' 흐름을 맨 앞에 (references/prd-to-screens.md §3)`);
}
for (const s of slugs.values()) {
  if (s.variantOf && !slugs.has(s.variantOf)) fail(`화면 ${s.slug}: variantOf '${s.variantOf}' 화면 없음`);
  if (s.overlayOf) {
    const base = slugs.get(s.overlayOf);
    if (!base) fail(`화면 ${s.slug}: overlayOf '${s.overlayOf}' 화면 없음`);
    else if (base.overlayOf) fail(`화면 ${s.slug}: overlayOf '${s.overlayOf}'도 뜨는 창 — 뒷 화면은 보통 화면이어야 함`);
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
  if (!SEC.length) fail(`sections 없음 — 사용 흐름(구역 보드)을 그릴 큰 구역 2~6개 (예: [{ "key": "start", "name": "가입·처음 시작" }, { "key": "home", "name": "홈" }])`);
  else if (SEC.length > 7) warn(`구역 ${SEC.length}개 — 2~6개로 크게 묶는다(온보딩·홈·예약처럼)`);
  const secKeys = new Set();
  for (const x of SEC) {
    if (!x.key || !/^[a-z0-9]+(-[a-z0-9]+)*$/.test(x.key)) fail(`구역 '${x.name || "?"}': key는 케밥케이스 영문`);
    if (secKeys.has(x.key)) fail(`구역 key 중복: ${x.key}`); secKeys.add(x.key);
    if (!x.name) fail(`구역 '${x.key}': name 없음`); else if (x.name.length > 12) warn(`구역 '${x.name}': 12자 이내로`);
  }
  const used = new Set(), lastStep = new Map();   // 같은 단계 이름표는 한 구역 안에서 붙어 있어야 한다
  for (const s of S.screens || []) {
    const desc = `화면 ${s.slug}`;
    if (!s.section) fail(`${desc}: section 없음 — 어느 구역에 놓일지`);
    else if (SEC.length && !secKeys.has(s.section)) fail(`${desc}: section '${s.section}'이 sections에 없음`);
    used.add(s.section);
    if (!s.step) fail(`${desc}: step 없음 — 화면 위 단계 이름표 (예: "약관 동의", "닉네임 입력"). 상태만 다른 화면은 원래 화면과 같은 이름표`);
    else {
      if (s.step.length > 14) warn(`${desc}: 단계 이름표 "${s.step}" — 14자 이내로`);
      const k = s.section + "|" + s.step, prev = lastStep.get(s.section);
      if (prev && prev !== k && [...lastStep.values()].includes(k)) warn(`${desc}: 단계 '${s.step}' 화면들이 떨어져 있음 — screens.json에서 같은 단계 화면을 붙여 둔다`);
      lastStep.set(s.section, k);
    }
    // 정책 메모: 화면 아래 검은 상자. 상태만 다른 화면(variantOf)은 선택
    const P = s.policy;
    if (P === undefined || (Array.isArray(P) && !P.length)) { if (!s.variantOf) fail(`${desc}: policy 없음 — 이 화면의 규칙(처음 상태·제한·예외·표기)을 [{ "title": "기본 정의", "items": ["…"] }]로`); continue; }
    if (!Array.isArray(P)) { fail(`${desc}: policy는 [{ title, items[] }] 배열`); continue; }
    if (P.length > 4) warn(`${desc}: 정책 묶음 ${P.length}개 — 4개 이하로`);
    for (const b of P) {
      if (!b || !b.title || !Array.isArray(b.items) || !b.items.length) { fail(`${desc}: policy 묶음 형식 { "title": "…", "items": ["…"] }`); continue; }
      if (b.items.length > 6) warn(`${desc}: 정책 '${b.title}' 줄 ${b.items.length}개 — 6줄 이하로`);
      for (const it of b.items) {
        if (typeof it !== "string" || !it.trim()) { fail(`${desc}: 정책 '${b.title}'에 빈 줄`); continue; }
        if (it.length > 70) warn(`${desc}: 정책 줄이 김(${it.length}자) — 한 줄에 규칙 하나, 70자 이내 "${it.slice(0, 24)}…"`);
        const j = it.match(JARGON); if (j) warn(`${desc}: 정책 줄에 컴포넌트 용어 '${j[0]}' — 일상어로 ("바텀시트" → "아래에서 올라오는 창")`);
      }
    }
  }
  for (const x of SEC) if (!used.has(x.key)) warn(`구역 '${x.name}': 화면이 하나도 없음`);
  // 안내·예외 (사용자: "지우기 같은 행동에 안내·오류 문구가 없다", "엣지 케이스나 글자 수 제한도") — prd-to-screens §5-4
  for (const s of S.screens || []) {
    const desc = `화면 ${s.slug}`;
    if (s.cases !== undefined) {
      if (!Array.isArray(s.cases)) fail(`${desc}: cases는 [{ when, show, tone }] 배열`);
      else for (const c of s.cases) {
        if (!c || !c.when || !c.show) { fail(`${desc}: cases 항목은 { "when": "이럴 때", "show": "보여 줄 문구" }`); continue; }
        if (c.tone && !["danger", "warning", "info", "success"].includes(c.tone)) fail(`${desc}: cases tone은 danger|warning|info|success`);
        if (c.show.length > 50) warn(`${desc}: 안내 문구 50자 이내로 "${c.show.slice(0, 20)}…"`);
      }
    }
    const html = s.file && exists(path.join(runDir, s.file)) ? fs.readFileSync(path.join(runDir, s.file), "utf8") : "";
    for (const m of html.matchAll(/<(input|textarea)\b([^>]*)>/g)) {
      if (/type="(checkbox|radio|hidden|range|date|time)"/.test(m[2])) continue;
      if (!/maxlength="\d+"/.test(m[2])) warn(`${desc}: 글자 칸에 maxlength 없음 — 글자 수 제한을 정해 maxlength(필요하면 minlength)로 (완성본에서 '3/20'이 보인다)`);
    }
    for (const m of html.matchAll(/data-stay-tone="([^"]*)"/g)) if (!["danger", "warning", "info", "success"].includes(m[1])) fail(`${desc}: data-stay-tone은 danger|warning|info|success`);
    if (!s.overlayOf) for (const m of html.matchAll(/<(button|a)\b([^>]*\bdata-stay="[^"]*"[^>]*)>([\s\S]*?)<\/\1>/g)) {
      const t = m[3].replace(/<[^>]+>/g, "").trim();
      if (/btn-danger/.test(m[2]) || /지우기|삭제|탈퇴|해지|초기화/.test(t)) warn(`${desc}: 되돌릴 수 없는 버튼 '${t}'이 바로 끝남 — 확인 창(뜨는 창 화면 + 갈래)을 거치게`);
    }
    if (s.pattern === "form" && !s.variantOf && !s.state && !(s.cases || []).length) warn(`${desc}: 입력 화면인데 cases(엣지 케이스: 빈칸·너무 김·겹침·실패) 없음 — 그때 보여 줄 문구를 정한다`);
  }
  // 움직임(motion): 완성본에서 실제로 재현된다(packages/core/motion). 정책에 글로만 적지 않는다
  const MOTION = ["hold", "breathe", "dim", "countup", "stagger", "reorder", "carousel", "play"];
  const NEEDS = { hold: "trigger", breathe: "any", reorder: "region", carousel: "region", play: "region" };
  for (const s of S.screens || []) {
    const desc = `화면 ${s.slug}`;
    if ((s.policy || []).some((b) => /움직임/.test(b.title || ""))) warn(`${desc}: 정책에 [움직임]이 글로만 있음 — motion으로 옮기면 완성본에서 실제로 움직인다 (prd-to-screens §5-3)`);
    if (s.motion === undefined) continue;
    if (!Array.isArray(s.motion)) { fail(`${desc}: motion은 [{ type, target, ms, note }] 배열`); continue; }
    const html = s.file && exists(path.join(runDir, s.file)) ? fs.readFileSync(path.join(runDir, s.file), "utf8") : "";
    for (const m of s.motion) {
      const md = `${desc} 움직임 ${m && m.type}`;
      if (!m || !MOTION.includes(m.type)) { fail(`${desc}: motion type은 ${MOTION.join("|")}`); continue; }
      if (!m.note) fail(`${md}: note 없음 — 완성본 '움직임' 안내에 보이는 한 문장 (예: "'측정 끝내기'를 2초 길게 누르면 끝나요")`);
      else if (m.note.length > 44) warn(`${md}: note 44자 이내로`);
      const need = NEEDS[m.type];
      if (need && !m.target) { fail(`${md}: target 없음 (${need === "trigger" ? "버튼 key(data-trigger)" : "영역 key(data-region)"})`); continue; }
      if (m.target && html) {
        const hasReg = html.includes(`data-region="${m.target}"`), hasTrig = html.includes(`data-trigger="${m.target}"`);
        if (need === "trigger" ? !hasTrig : need === "region" ? !hasReg : !(hasReg || hasTrig)) fail(`${md}: target '${m.target}'이 조각에 없음`);
      }
      if (m.ms !== undefined && !(Number.isFinite(m.ms) && m.ms >= 100 && m.ms <= 60000)) fail(`${md}: ms는 100~60000`);
    }
  }
  // 오류·완료 상태: 사용자가 밟게 될 상태는 반드시 그린다
  const all = [...slugs.values()];
  const inputs = all.filter((s) => !s.state && s.pattern === "form" && !s.variantOf);
  if (inputs.length && !all.some((s) => s.state === "error")) fail(`오류 상태 화면이 없음 — 입력하는 화면(${inputs.slice(0, 3).map((s) => s.slug).join(", ")}…) 중 핵심 하나 이상에 state "error" 변형(variantOf)`);
  if (!all.some((s) => s.state === "success")) fail(`완료 상태 화면이 없음 — 핵심 작업이 끝났을 때(저장·예약·보내기 완료) state "success" 변형(variantOf) 하나 이상`);
  for (const s of inputs.filter((x) => !x.overlayOf)) if (!all.some((v) => v.variantOf === s.slug && v.state === "error")) warn(`화면 ${s.slug}: 입력하는 화면인데 오류 상태가 없음 — 틀리기 쉬운 입력이면 state "error" 변형을 더한다`);
}

// ---------- branches (갈래: 흐름 밖의 버튼이 여는 화면) ----------
const branchTo = new Map(); // "from|trigger" → to
const stepTo = new Map();   // "from|trigger" → to
for (const f of F.flows || []) for (const st of f.steps || []) if (st.trigger) stepTo.set(st.from + "|" + st.trigger, st.to);
if (F.branches !== undefined && !Array.isArray(F.branches)) fail(`flow.json branches는 배열이어야 함`);
(F.branches || []).forEach((b, i) => {
  const bd = `갈래 ${i + 1} (${b.from || "?"} → ${b.to || "?"})`;
  if (!slugs.has(b.from)) { fail(`${bd}: from '${b.from}' 화면 없음`); return; }
  if (!slugs.has(b.to)) fail(`${bd}: to '${b.to}' 화면 없음`);
  if (b.from === b.to) fail(`${bd}: 같은 화면으로 가는 갈래 — 그 자리에서 바뀌는 버튼은 조각에 data-stay`);
  if (!b.action) fail(`${bd}: action 문장 없음 ("'…'을 누르면")`);
  checkWhen(b, bd);
  const keys = regionKeysBySlug.get(b.from) || new Set();
  if (!b.region) fail(`${bd}: region 없음`); else if (!keys.has(b.region)) fail(`${bd}: region '${b.region}'이 '${b.from}' 화면 영역에 없음`);
  if (!b.trigger) { fail(`${bd}: trigger 없음 — 누르는 버튼에 data-trigger`); return; }
  const trig = triggersBySlug.get(b.from) || new Map();
  if (!triggersBySlug.has(b.from)) { /* 조각 전 — 건너뜀 */ }
  else if (!trig.has(b.trigger)) fail(`${bd}: trigger '${b.trigger}'가 '${b.from}' 조각에 data-trigger로 없음`);
  else if (b.region && trig.get(b.trigger) !== b.region) warn(`${bd}: trigger '${b.trigger}'가 region '${b.region}' 안에 있지 않음 (실제: ${trig.get(b.trigger) || "영역 밖"})`);
  const k = b.from + "|" + b.trigger;
  if (stepTo.has(k)) fail(`${bd}: trigger '${b.trigger}'는 이미 흐름 단계에 있음 — 갈래에서 뺀다`);
  if (branchTo.has(k)) fail(`${bd}: trigger '${b.trigger}' 갈래 중복`);
  branchTo.set(k, b.to);
  reached.add(b.from); reached.add(b.to);
});
for (const s of slugs.values()) {
  if (s.overlayOf && ![...branchTo.values(), ...stepTo.values()].includes(s.slug)) fail(`화면 ${s.slug}: 뜨는 창인데 이 창을 여는 버튼(갈래)이 없음 — flow.json branches에 추가`);
}

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

// ---------- board 설정 (있으면) ----------
if (S.board) {
  if (S.board.hero && !slugs.has(S.board.hero)) fail(`board.hero '${S.board.hero}' 화면 없음`);
  for (const q of S.board.ask || []) {
    if (!q.id || !q.text || !Array.isArray(q.options) || q.options.length < 2) fail(`board.ask 항목 형식 오류: ${JSON.stringify(q)}`);
    if (q.recommended === undefined) fail(`board.ask '${q.id}': recommended 없음 — 모든 질문에 추천값`);
  }
}

// ---------- 시안(concepts) · 레퍼런스 — references/prd-to-screens.md §7 ----------
if (S.concepts !== undefined) {
  const C = Array.isArray(S.concepts) ? S.concepts : [];
  // 메뉴 구조: web = 왼쪽 메뉴·위쪽 탭·아이콘 메뉴 / mobile = 아래 탭·위쪽 탭·메뉴 없음 (scripts/expand.js)
  const SHELLS = platform === "mobile" ? { tabbar: null, top: "nav-top", none: "no-nav" } : { sidebar: null, top: "nav-top", rail: "nav-rail" };
  if (C.length !== 5) warn(`시안은 5개 (지금 ${C.length}개)`);
  const lookIds = new Set(require("./looks.js").getLooks(S).map((l) => l.id));
  const cids = new Set();
  for (const c of C) {
    const cd = `시안 ${c.id || "?"}`;
    if (!c.id || !/^[a-z]$/.test(c.id)) fail(`${cd}: id는 a·b·c`);
    if (cids.has(c.id)) fail(`${cd}: id 중복`); cids.add(c.id);
    if (!c.name) fail(`${cd}: name 없음 (예: "달력 한 장으로 보기")`);
    else if (/[a-z]{3,}|시안|레이아웃|대시보드형|타입/i.test(c.name)) warn(`${cd}: 이름 "${c.name}" — 무엇이 먼저 보이는지 일상어로 (예: "오늘 할 일부터 보기")`);
    if (!c.why) warn(`${cd}: why 없음 — 이 안이 누구에게 왜 좋은지 한 문장`);
    if (!(c.shell in SHELLS)) fail(`${cd}: shell은 ${Object.keys(SHELLS).join("|")}`);
    if (!lookIds.has(c.look)) fail(`${cd}: look '${c.look}'이 looks에 없음`);
    if (!Array.isArray(c.refs) || !c.refs.length) warn(`${cd}: 참고한 곳(refs) 없음 — 레퍼런스에서 무엇을 가져왔는지`);
    for (const r of c.refs || []) if (!r.name || !r.borrow) warn(`${cd}: refs 항목에 name·borrow 필요`);
    const scr = Array.isArray(c.screens) ? c.screens : [];
    if (scr.length < 3) warn(`${cd}: 보여줄 메인 화면은 3~6장 (지금 ${scr.length}장) — 역할별 메뉴 화면부터`);
    if (scr.length > 6) fail(`${cd}: 보여줄 메인 화면은 최대 6장 (지금 ${scr.length}장) — 1턴이 길어지고 비교하기 어렵다`);
    for (const slug of scr) if (!slugs.has(slug)) fail(`${cd}: 화면 '${slug}' 없음`);
  }
  const main = C.find((c) => c.id === S.concept) || C[0];
  if (S.concept && !cids.has(S.concept)) fail(`screens.json concept '${S.concept}'이 concepts에 없음`);
  if (C.length > 1 && new Set(C.map((c) => c.shell)).size < Math.min(3, C.length))
    warn(`시안끼리 메뉴 구조(shell)가 ${new Set(C.map((c) => c.shell)).size}가지뿐 — ${Object.keys(SHELLS).join("·")}을 모두 쓴다`);
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
      const want = SHELLS[c.shell];
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
  if (main && SHELLS[main.shell]) for (const s of slugs.values()) {
    if (s.overlayOf || !s.file || !exists(path.join(runDir, s.file))) continue;
    const html = fs.readFileSync(path.join(runDir, s.file), "utf8");
    if (!/class=["'][^"']*\bnav-item\b/.test(html)) continue;   // 메뉴 없는 화면(초대 받았을 때 등 가운데 한 장)은 제외
    const appCls = ((/<div\s+class=["']([^"']*\bapp\b[^"']*)["']/.exec(html) || [])[1] || "").split(/\s+/);
    if (!appCls.includes(SHELLS[main.shell])) warn(`화면 ${s.slug}: 시안 ${main.id}의 메뉴 구조(${main.shell})인데 .app에 ${SHELLS[main.shell]} 없음`);
  }
  const R = Array.isArray(S.references) ? S.references : [];
  if (R.length < 3) warn(`살펴본 서비스(references) ${R.length}곳 — 5곳 정도 조사해 시안의 근거로 (ref-scout)`);
  for (const r of R) if (!r.name || !r.url || !r.borrow) warn(`references '${r.name || "?"}': name·url·borrow 필요`);
}

// ---------- 출력 ----------
for (const w of warns) console.log(`[WARN] ${w}`);
for (const f of fails) console.log(`[FAIL] ${f}`);
const nScreens = (S.screens || []).length;
const nRegions = (S.screens || []).reduce((n, s) => n + (s.regions || []).length, 0);
console.log(`[lint] 화면 ${nScreens} · 영역 ${nRegions} · 구역 ${(S.sections || []).length} · 플로우 ${(F.flows || []).length} · 갈래 ${(F.branches || []).length} · FAIL ${fails.length} · WARN ${warns.length}`);
process.exit(fails.length || (strict && warns.length) ? 1 : 0);
