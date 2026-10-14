// 저장소 검사 — 화면 부품 CSS(packages/web/components · packages/mobile/components)와 토큰(base.css)이 KRDS 규칙을 지킨다.
// 규칙 값은 packages/core/schema/rules.json에서 읽는다(규칙 문장을 여기 복사하지 않는다).
// rules.json이 아직 없으면 건너뛴다 — 규칙 정본이 생기면 저절로 켜진다.
const fs = require("fs");
const path = require("path");
const { ROOT, suite, stageOn } = require("../lib.js");

const t = suite("40 부품 CSS");
const rulesFile = path.join(ROOT, "packages", "core", "schema", "rules.json");
const TOKENS = path.join(ROOT, "packages", "core", "tokens", "base.css");
const PLATFORMS = {
  web: { dir: path.join(ROOT, "packages", "web", "components"), tokens: [TOKENS] },
  // 모바일은 web 토큰 위에 모바일 토큰 파일이 덮어쓴다(scripts/platform.js)
  mobile: { dir: path.join(ROOT, "packages", "mobile", "components"), tokens: [TOKENS, path.join(ROOT, "packages", "mobile", "components", "00-mobile-tokens.css")] },
};
if (!stageOn("parts-krds")) { t.skip("단계 스위치 parts-krds 꺼짐 — [3/5]에서 켠다"); t.end(); }
if (!fs.existsSync(rulesFile)) { t.skip("packages/core/schema/rules.json 없음 — 규칙 정본이 생기면 켜진다"); t.end(); }

const { rules } = JSON.parse(fs.readFileSync(rulesFile, "utf8"));
const R = (id) => { const r = rules.find((x) => x.id === id); return { ...r, value: (r && r.value) || {} }; };

// 아주 단순한 CSS 읽기 — 주석을 지우고 '선택자 { 선언 }'만 모은다
const readBlocks = (file, platform) => {
  if (!fs.existsSync(file)) return [];
  const src = fs.readFileSync(file, "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
  return [...src.matchAll(/([^{}]+)\{([^{}]*)\}/g)].map((m) => ({ file: path.basename(file), platform, sel: m[1].trim().replace(/^@[^{]*$/, ""), body: m[2] }));
};
const cssFiles = (dir) => (fs.existsSync(dir) ? fs.readdirSync(dir).filter((x) => x.endsWith(".css")).sort().map((x) => path.join(dir, x)) : []);
const blocks = [];
for (const [platform, p] of Object.entries(PLATFORMS)) for (const f of cssFiles(p.dir)) blocks.push(...readBlocks(f, platform));
const at = (b) => `${b.platform}/${b.file}`;
// 괄호 밖 쉼표로만 나눈다 — ':is(.input, .select)'가 쪼개지지 않게
const top = (sel) => { const out = []; let depth = 0, cur = ""; for (const ch of sel) { if (ch === "(") depth++; if (ch === ")") depth--; if (ch === "," && !depth) { out.push(cur); cur = ""; } else cur += ch; } return [...out, cur].map((x) => x.trim()); };

// ---- 토큰 값 읽기 — 플랫폼마다 변수를 모아(뒤 파일이 앞을 덮어씀) var()를 풀어 숫자로 ----
const decls = (body) => Object.fromEntries([...body.matchAll(/([\w-]+)\s*:\s*([^;]+)/g)].map((m) => [m[1], m[2].trim()]));
const platformTokens = (platform) => {
  const vars = {}, body = {};
  for (const f of PLATFORMS[platform].tokens) for (const b of readBlocks(f, platform)) {
    if (b.sel === ":root") Object.assign(vars, decls(b.body));
    if (b.sel === "body") Object.assign(body, decls(b.body));
  }
  return { vars, body };
};
// "var(--a)" · "16px" · "1.5" → 숫자(px 또는 배수). 풀 수 없으면(calc 등) null
const num = (val, vars, depth = 0) => {
  if (val == null || depth > 8) return null;
  const v = /^var\(\s*(--[\w-]+)\s*(?:,\s*([^)]+))?\)$/.exec(val.trim());
  if (v) return num(vars[v[1]] ?? v[2], vars, depth + 1);
  const m = /^(-?[\d.]+)(px|em|rem)?$/.exec(val.trim());
  return m ? parseFloat(m[1]) * (m[2] === "rem" ? 16 : 1) : null;
};
const minMsg = (what, got, min, unit = "") => `${what} ${got}${unit} — ${min}${unit} 이상이어야 함`;

// color-role-use — 역할마다 쓰는 곳(선택자 패턴) 밖에서 쓰면 실패
let roleFails = 0;
for (const [role, def] of Object.entries(R("color-role-use").value.roles || {})) {
  const re = new RegExp(`var\\(--c-${role}(-soft|-fg|-soft-fg|-hover|-active)?\\)`);
  const allow = def.where ? new RegExp(def.where) : null;
  if (!allow) continue;
  // 배지 배경의 Primary는 badge-not-primary가 맡는다
  const owned = (b) => role === "primary" && top(b.sel).every((s) => /badge/.test(s));
  for (const b of blocks.filter((x) => re.test(x.body) && x.sel && !owned(x) && !top(x.sel).every((s) => allow.test(s)))) {
    roleFails++;
    t.fail(`color-role-use: ${role}를 '${b.sel}'(${at(b)})에서 씀 — 이 역할의 자리: ${def.says}`);
  }
}
if (!roleFails) t.ok("color-role-use");

let n = 0;
for (const b of blocks) if (/badge/.test(b.sel) && /background[^;]*var\(--c-primary/.test(b.body)) { n++; t.fail(`badge-not-primary: '${b.sel}'(${at(b)}) 배경이 Primary`); }
if (!n) t.ok("badge-not-primary");
n = 0;
for (const b of blocks) if (/:disabled|is-disabled/.test(b.sel) && /(^|;|\s)opacity\s*:|rgba\(/.test(b.body)) { n++; t.fail(`disabled-no-alpha: '${b.sel}'(${at(b)}) 비활성에 투명도`); }
if (!n) t.ok("disabled-no-alpha");

// ---- 토큰 검사 (base.css + 모바일 토큰) — 플랫폼마다 ----
const bodyMin = R("body-size-min").value.min ?? 16;
const leadMin = R("leading-min").value.min ?? 1.5;
const fw = R("font-weight-krds").value;
const check = (id, fails) => { if (fails.length) fails.forEach((m) => t.fail(`${id}: ${m}`)); else t.ok(id); };
const out = { "body-size-min": [], "leading-min": [], "font-weight-krds": [], "type-scale": [], "space-scale": [], "tracking-krds": [], "error-hint-size": [] };
const allowedPx = Array.isArray(R("space-scale").value.allowed_px) && R("space-scale").value.allowed_px.length ? R("space-scale").value.allowed_px : null;
const hasHintRule = rules.some((r) => r.id === "error-hint-size"); // 정본에 규칙이 생기면 켜진다
for (const platform of Object.keys(PLATFORMS)) {
  const { vars, body } = platformTokens(platform);
  const P = (m) => `${platform}: ${m}`;

  // body-size-min — body 글자 크기
  const size = num(body["font-size"], vars);
  if (size == null) out["body-size-min"].push(P("body font-size를 읽지 못함"));
  else if (size < bodyMin) out["body-size-min"].push(P(minMsg(`본문 글자 ${body["font-size"]} =`, size, bodyMin, "px")));

  // leading-min — 본문 줄 간격(body · --lh-normal). 제목 줄 간격(--lh-tight · --lh-head)은 글꼴 세트가 정하므로 보지 않는다
  const lead = num(body["line-height"], vars);
  if (lead == null) out["leading-min"].push(P("body line-height를 읽지 못함"));
  else if (lead < leadMin) out["leading-min"].push(P(minMsg(`본문 줄 간격 ${body["line-height"]} =`, lead, leadMin)));
  for (const k of ["--lh-normal"]) {
    const v = num(vars[k], vars);
    if (v != null && v < leadMin) out["leading-min"].push(P(minMsg(`${k}: ${vars[k]} =`, v, leadMin)));
  }

  // font-weight-krds — 보통 400 · 굵게 700. 본문 굵기는 400. 부품 CSS의 숫자 굵기는 400·700만
  const reg = num(vars["--fw-regular"], vars), bold = num(vars["--fw-bold"], vars), bw = num(body["font-weight"] ?? vars["--fw-body"], vars);
  if (reg != null && reg !== fw.regular) out["font-weight-krds"].push(P(`--fw-regular ${reg} — ${fw.regular}여야 함`));
  if (bold != null && bold !== fw.strong) out["font-weight-krds"].push(P(`--fw-bold ${bold} — ${fw.strong}여야 함`));
  if (bw != null && bw !== fw.regular) out["font-weight-krds"].push(P(`본문 굵기 ${bw} — ${fw.regular}여야 함`));
  // 쓰이지 않아도 토큰으로 남은 500·600 단계도 걸린다(굵기는 두 가지뿐)
  for (const k of ["--fw-medium", "--fw-semibold"]) {
    const v = num(vars[k], vars);
    if (v != null && v !== fw.regular && v !== fw.strong) out["font-weight-krds"].push(P(`${k} ${v} — ${fw.regular}·${fw.strong}만`));
  }
  // 부품 CSS의 굵기 선언 — var()를 풀어서 본다. 제목 굵기 --fw-head는 글꼴 세트가 정하므로 제외
  for (const b of blocks.filter((x) => x.platform === platform))
    for (const m of b.body.matchAll(/(?:^|[;\s])font-weight\s*:\s*([^;]+)/g)) {
      const raw = m[1].trim();
      if (/var\(\s*--fw-head\b/.test(raw)) continue;
      const v = num(raw, vars);
      if (v != null && v !== fw.regular && v !== fw.strong) out["font-weight-krds"].push(P(`'${b.sel}'(${at(b)}) 굵기 ${raw} = ${v} — ${fw.regular}·${fw.strong}만`));
    }

  // type-scale — 글자 단계가 작은 것에서 큰 것으로 올라간다(--fs-caption<body<title<display, 옛 이름 xs<…<3xl)
  const steps = ["--fs-caption", "--fs-body", "--fs-title", "--fs-display"].filter((k) => vars[k] != null);
  const legacy = ["--fs-xs", "--fs-sm", "--fs-md", "--fs-lg", "--fs-xl", "--fs-2xl", "--fs-3xl"].filter((k) => vars[k] != null);
  for (const list of [steps, legacy]) {
    const vals = list.map((k) => num(vars[k], vars));
    vals.forEach((v, i) => { if (v == null) out["type-scale"].push(P(`${list[i]} 값을 읽지 못함`)); else if (i && vals[i - 1] != null && v <= vals[i - 1]) out["type-scale"].push(P(`${list[i]} ${v}px가 ${list[i - 1]} ${vals[i - 1]}px보다 커야 함`)); });
  }
  if (!steps.length && !legacy.length) out["type-scale"].push(P("글자 단계 변수(--fs-*)가 없음"));

  // space-scale — 간격 item < group < page이고, 값은 rules.json space-scale value.allowed_px 목록 안에서.
  // 목록이 아직 없으면 base.css의 4px 격자(4의 배수)로 둔다 — 12px(KRDS gap-4)가 걸리지 않게. 변수가 아직 없으면 건너뜀
  const sp = ["--space-item", "--space-group", "--space-page"];
  if (sp.every((k) => vars[k] == null)) out["space-scale"].push(P("--space-item · --space-group · --space-page 아직 없음"));
  else {
    const vals = sp.map((k) => num(vars[k], vars));
    vals.forEach((v, i) => {
      if (vars[sp[i]] == null) out["space-scale"].push(P(`${sp[i]} 없음`));
      else if (v == null) out["space-scale"].push(P(`${sp[i]} 값을 읽지 못함`));
      else {
        if (allowedPx) { if (!allowedPx.includes(v)) out["space-scale"].push(P(`${sp[i]} ${v}px — 허용 목록(${allowedPx.join("·")}px)에 없음`)); }
        else if (v % 4) out["space-scale"].push(P(`${sp[i]} ${v}px — 4의 배수가 아님`));
        if (i && vals[i - 1] != null && v <= vals[i - 1]) out["space-scale"].push(P(`${sp[i]} ${v}px가 ${sp[i - 1]} ${vals[i - 1]}px보다 커야 함`));
      }
    });
  }

  // tracking-krds — 본문 자간 0 · 32px 이상 큰 제목 1px · 음수 자간 금지. em은 그 글자 크기(없으면 본문)로 px로 바꾼다
  const T = R("tracking-krds").value, bigPx = T.large_heading_px_from ?? 32;
  const track = (val, fs) => { const m = /^(-?[\d.]+)(px|em)?$/.exec(String(val).trim().replace(/^var\(.+\)$/, (x) => vars[x.slice(4, -1).split(",")[0].trim()] ?? x)); return m ? parseFloat(m[1]) * (m[2] === "em" ? fs : 1) : null; };
  const bodyFs = size ?? 16;
  for (const k of Object.keys(vars).filter((x) => /^--(ls|tracking)-/.test(x))) {
    const v = track(vars[k], bodyFs);
    if (v != null && v < 0) out["tracking-krds"].push(P(`${k}: ${vars[k]} — 음수 자간 금지`));
  }
  const bodyTrack = track(body["letter-spacing"] ?? vars["--ls-body"] ?? "0", bodyFs);
  if (bodyTrack != null && bodyTrack !== T.body) out["tracking-krds"].push(P(`본문 자간 ${body["letter-spacing"] ?? vars["--ls-body"]} = ${bodyTrack}px — ${T.body}이어야 함`));
  for (const b of blocks.filter((x) => x.platform === platform)) {
    const ls = /(?:^|[;\s])letter-spacing\s*:\s*([^;]+)/.exec(b.body); if (!ls) continue;
    const fm = /(?:^|[;\s])font-size\s*:\s*([^;]+)/.exec(b.body), bfs = fm ? num(fm[1], vars) : null;
    const v = track(ls[1], bfs ?? bodyFs);
    if (v == null) continue;
    if (v < 0) out["tracking-krds"].push(P(`'${b.sel}'(${at(b)}) 자간 ${ls[1].trim()} = ${+v.toFixed(2)}px — 음수 자간 금지`));
    else if (bfs != null && bfs >= bigPx && v !== T.large_heading_px) out["tracking-krds"].push(P(`'${b.sel}'(${at(b)}) ${bfs}px 큰 제목 자간 ${+v.toFixed(2)}px — ${T.large_heading_px}px이어야 함`));
  }

  // error-hint-size — 오류 · 안내 문구는 본문 크기 이상(작은 글자로 줄이지 않는다)
  for (const b of blocks.filter((x) => x.platform === platform && top(x.sel).some((s) => /(^|[.\s-])(error|help|hint)\b/.test(s) && !/:is\(|:not\(/.test(s) || /-(error|help|hint)$/.test(s)))) {
    const m = /(?:^|[;\s])font-size\s*:\s*([^;]+)/.exec(b.body);
    const v = m && num(m[1], vars);
    if (v != null && v < bodyMin) out["error-hint-size"].push(P(`'${b.sel}'(${at(b)}) 글자 ${m[1].trim()} = ${v}px — 본문(${bodyMin}px) 이상이어야 함`));
  }
}
for (const [id, fails] of Object.entries(out)) {
  if (id === "error-hint-size" && !hasHintRule) { t.skip("error-hint-size: rules.json에 규칙 없음 — 정본에 생기면 켜진다"); continue; }
  if (id === "space-scale" && fails.length && fails.every((m) => /아직 없음/.test(m))) t.skip(`space-scale: ${fails[0]} — 값 층에서 생기면 켜진다`);
  else check(id, fails);
}
t.end();
