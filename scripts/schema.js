#!/usr/bin/env node
/**
 * schema.js — 정본 스키마(packages/core/schema/)의 검사기 · 사전 생성기. 외부 패키지 없이 Node 내장만.
 *
 *   node scripts/schema.js                  정본 자체 검사 — 규칙 연결 · 관계(범위) · 생성 단계 · 읽는 곳 · docs/ 최신
 *   node scripts/schema.js runs/<p>         실행물 검사 — screens.json · flow.json의 형식 · 값 · 관계(범위) · 하나뿐
 *   node scripts/schema.js --doc            칸 사전 마크다운 → 표준 출력
 *   node scripts/schema.js --relations      객체와 관계 마크다운 → 표준 출력 (대상 · 범위 검사 포함)
 *   node scripts/schema.js --rules          규칙 사전 마크다운 → 표준 출력 (칸 ↔ 규칙 연결 검사 포함)
 *   node scripts/schema.js --stages         생성 단계 — 앞 단계만 가리키나 · Claude 구조화 출력 한도
 *   node scripts/schema.js --feeds          읽는 곳 — 칸마다 코드 · 보드 · 생성 중 읽는 곳이 있나
 *   node scripts/schema.js --docs           docs/fields.md · relations.md · rules.md 다시 쓰기
 *
 * 실행물 검사: FAIL = 형식 · 값 · 관계 오류(exit 1). 경고 = 옛 칸 · 옛 값(x-status legacy) · 권장 칸 없음(x-recommended).
 * exit 0 = 통과, 1 = 실패, 2 = 쓰는 법 오류.
 */
const fs = require("fs");
const path = require("path");

const DIR = path.resolve(__dirname, "..", "packages", "core", "schema");
const load = (f) => JSON.parse(fs.readFileSync(path.join(DIR, f), "utf8"));
const DOCS = { screens: load("screens.schema.json"), flow: load("flow.schema.json") };
const { rules: RULES } = load("rules.json");
const STAGES = ["S1 의도", "S2 여정 · 화면 목록", "S3 화면 하나씩", "S4 성격", "S5 시안", "하네스"];
const STATUS = { adopted: "✔", proposed: "○", draft: "△", legacy: "✕" };
const STRENGTH = { "krds-must": "KRDS 필수", "krds-should": "KRDS 권장", "krds-best": "KRDS 우수", ours: "우리 규칙", case: "사례 참고" };
const CODE = ["pack", "expand", "build", "lint", "looks", "ids"];   // ① 코드가 읽는다
const BOARD = "보드";                                                // ② 사람이 보드에서 본다
const WITHIN = ["doc", "screen", "from", "role", "theme"];           // x-ref 범위
const UNIQUE = { doc: null, screen: "screen", look: "look" };        // x-unique 범위 → 그 칸이 들어 있어야 할 객체

const refDef = (ref) => ref.split("/").pop();
const resolve = (s, root) => (s && s.$ref ? root.$defs[refDef(s.$ref)] : s);
/** x-ref 하나를 { doc, def, path, to, within, also }로 — 문자열이면 within doc */
const parseRef = (x, doc) => {
  const o = typeof x === "string" ? { to: x } : x;
  const [d, p] = o.to.includes("#") ? o.to.split("#") : [doc, o.to];
  const [def, ...rest] = p.split(".");
  return { doc: d, def, path: rest, to: o.to, within: o.within || "doc", also: o.also || [], legacy: o["x-status"] === "legacy", warnWith: o.warnWith || [] };
};
const refsOf = (node, doc) => [].concat(node["x-ref"] || []).map((x) => parseRef(x, doc));
/** 옛 칸 · 옛 값 경고 — 설명이 이미 '옛 …'으로 시작하면 머리말을 겹쳐 쓰지 않는다 */
const oldMsg = (at, head, desc) => `${at}: ${desc && /^(옛|뺌)/.test(desc) ? desc : `${head} — ${desc || "다음 판에서 지움"}`}`;
const refLabel = (r) => `${r.to}${r.within !== "doc" ? ` (${r.within} 안)` : ""}${r.also.length ? ` ∪ ${r.also.join(" · ")}` : ""}${r.legacy ? "(옛 대상)" : ""}`;

// ---------------------------------------------------------------------------
// 형식 검사 — JSON Schema 일부(type · enum · const · pattern · min/max · items · properties · additionalProperties ·
// required · anyOf · allOf if/then/else · not · $ref)에 정본 표시(x-status legacy · x-recommended)를 더한다
// ---------------------------------------------------------------------------
const typeOk = (t, v) =>
  t === "array" ? Array.isArray(v)
  : t === "object" ? v !== null && typeof v === "object" && !Array.isArray(v)
  : t === "integer" ? Number.isInteger(v)
  : typeof v === t;
const isObj = (v) => v !== null && typeof v === "object" && !Array.isArray(v);

function check(schema, v, at, root, out) {
  schema = resolve(schema, root);
  if (schema.const !== undefined && v !== schema.const) out.errs.push(`${at}: ${JSON.stringify(schema.const)} 이어야 함`);
  if (schema.enum && !schema.enum.includes(v)) out.errs.push(`${at}: ${schema.enum.join("|")} 중 하나여야 함 (지금 ${JSON.stringify(v)})`);
  if (schema.type && !typeOk(schema.type, v)) return out.errs.push(`${at}: ${schema.type} 이어야 함`);
  if (typeof v === "string") {
    if (schema.pattern && !new RegExp(schema.pattern).test(v)) out.errs.push(`${at}: 형식 불일치 (${schema.pattern})`);
    if (schema.minLength && v.length < schema.minLength) out.errs.push(`${at}: 너무 짧음`);
    if (schema.maxLength && v.length > schema.maxLength) out.errs.push(`${at}: ${schema.maxLength}자 초과`);
  }
  if (typeof v === "number" && schema.minimum !== undefined && v < schema.minimum) out.errs.push(`${at}: ${schema.minimum} 이상이어야 함`);
  if (typeof v === "number" && schema.maximum !== undefined && v > schema.maximum) out.errs.push(`${at}: ${schema.maximum} 이하여야 함`);
  if (schema.anyOf) {
    const tries = schema.anyOf.map((s) => { const o = { errs: [], warns: [] }; check(s, v, at, root, o); return { s: resolve(s, root), o }; });
    const pass = tries.filter((t) => !t.o.errs.length);
    if (!pass.length) out.errs.push(`${at}: 허용 형식 중 어느 것과도 맞지 않음 — ${tries.map((t) => t.o.errs[0]).join(" / ")}`);
    else {
      const now = pass.find((t) => t.s["x-status"] !== "legacy");
      if (now) out.warns.push(...now.o.warns);
      else { out.warns.push(oldMsg(at, "옛 값", pass[0].s.description)); out.warns.push(...pass[0].o.warns); }
    }
  }
  if (schema.not) { const o = { errs: [], warns: [] }; check(schema.not, v, at, root, o); if (!o.errs.length) out.errs.push(`${at}: 허용하지 않는 형식`); }
  if (Array.isArray(v)) {
    if (schema.minItems && v.length < schema.minItems) out.errs.push(`${at}: 항목 ${schema.minItems}개 이상 필요`);
    if (schema.maxItems !== undefined && v.length > schema.maxItems) out.errs.push(`${at}: 항목 ${schema.maxItems}개 이하`);
    if (schema.items) v.forEach((x, i) => check(schema.items, x, `${at}[${i}]`, root, out));
  }
  if (isObj(v)) {
    for (const k of schema.required || []) if (!(k in v)) out.errs.push(`${at}.${k}: 필수 항목 없음`);
    for (const k of schema["x-recommended"] || []) if (!(k in v)) out.warns.push(`${at}.${k}: 권장 칸 없음 — 다음 판에서 필수`);
    const props = schema.properties || {};
    for (const [k, x] of Object.entries(v)) {
      if (props[k]) {
        const p = resolve(props[k], root);
        if (props[k]["x-status"] === "legacy" || (p && p["x-status"] === "legacy")) out.warns.push(oldMsg(`${at}.${k}`, "옛 칸", props[k].description || p.description));
        check(props[k], x, `${at}.${k}`, root, out);
      } else if (schema.additionalProperties === false) out.errs.push(`${at}.${k}: 스키마에 없는 항목`);
      else if (isObj(schema.additionalProperties)) check(schema.additionalProperties, x, `${at}.${k}`, root, out);
    }
  }
  for (const rule of schema.allOf || []) {
    const probe = { errs: [], warns: [] };
    if (rule.if) check(rule.if, v, at, root, probe);
    if (!rule.if || !probe.errs.length) { if (rule.then) check(rule.then, v, at, root, out); else if (!rule.if) check(rule, v, at, root, out); }
    else if (rule.else) check(rule.else, v, at, root, out);
  }
}

// ---------------------------------------------------------------------------
// 스키마 펴기 — 칸마다 { doc, def, local, path, stage, required, recommended, node } — 사전 · 관계 · 단계 · 읽는 곳이 함께 쓴다
// ---------------------------------------------------------------------------
function walkSchema(doc) {
  const root = DOCS[doc], rows = [], defStage = {}, defPaths = {};
  const visitObj = (obj, ctx, seen) => {
    const req = new Set(obj.required || []), rec = new Set(obj["x-recommended"] || []);
    for (const [k, v] of Object.entries(obj.properties || {})) {
      if (k === "$schema") continue;
      const stage = v["x-stage"] || ctx.stage;
      const row = { doc, def: ctx.def, chain: ctx.chain, local: ctx.local ? `${ctx.local}.${k}` : k, path: ctx.path ? `${ctx.path}.${k}` : k,
        stage, ownStage: v["x-stage"] || "", required: req.has(k), recommended: rec.has(k), node: v, res: resolve(v, root) };
      rows.push(row);
      descend(v, row, seen);
    }
  };
  const descend = (v, row, seen) => {
    const found = [];
    const collect = (n, arr) => {
      if (!n || typeof n !== "object") return;
      if (n.$ref) found.push({ def: refDef(n.$ref), arr });
      else if (n.items) collect(n.items, true);
      else if (n.properties) found.push({ inline: n, arr });
      for (const x of n.anyOf || []) collect(x, arr);
    };
    collect(v, false);
    for (const f of found) {
      const p = `${row.path}${f.arr ? "[]" : ""}`;
      if (f.inline) { visitObj(f.inline, { ...row, path: p }, seen); continue; }
      const d = root.$defs[f.def];
      if (!d || (!d.properties && !isObj(d.additionalProperties)) || seen.has(f.def)) continue;
      if (!defStage[f.def]) defStage[f.def] = row.stage;
      (defPaths[f.def] = defPaths[f.def] || []).push(p);
      visitObj(d, { def: f.def, chain: [...row.chain, f.def], local: "", path: p, stage: row.stage }, new Set([...seen, f.def]));
    }
  };
  visitObj(root, { def: "$root", chain: ["$root"], local: "", path: "", stage: "" }, new Set());
  return { rows, defStage, defPaths };
}
const WALK = { screens: walkSchema("screens"), flow: walkSchema("flow") };
const ROWS = [...WALK.screens.rows, ...WALK.flow.rows];
const objName = (doc, def) => (def === "$root" ? `${doc}.json` : (DOCS[doc].$defs[def] || {})["x-object"] || def);

/** 대상 칸이 스키마에 있나, 그 칸의 생성 단계는 무엇인가 */
function target(r) {
  const root = DOCS[r.doc];
  let node = root && root.$defs[r.def];
  if (!node) return { ok: false };
  let stage = WALK[r.doc].defStage[r.def] || "";
  for (const k of r.path) {
    if (node.items) node = resolve(node.items, root);
    if (node && node.$ref) node = resolve(node, root);
    if (k === "key" && node && isObj(node.additionalProperties)) return { ok: true, stage };   // 이름표 → 값 묶음(facts)
    node = node && node.properties && node.properties[k];
    if (node && node["x-stage"]) stage = node["x-stage"];
  }
  return { ok: !!node, stage };
}

/** x-ref를 모아 관계 목록으로 — 대상이 있나 · 범위가 그 자리에서 뜻이 있나 · 앞 단계를 가리키나 */
/** x-unique 범위 값이 허용 목록 안이고, 그 범위 객체 안의 칸인가 */
function uniqueProblems() {
  return ROWS.filter((row) => row.node["x-unique"]).flatMap((row) => {
    const u = row.node["x-unique"];
    if (!(u in UNIQUE)) return [`${row.path}: x-unique '${u}'는 없는 범위 (${Object.keys(UNIQUE).join(" · ")})`];
    if (UNIQUE[u] && !row.chain.includes(UNIQUE[u])) return [`${row.path}: x-unique '${u}'인데 ${UNIQUE[u]} 안 칸이 아님`];
    return [];
  });
}

function relations() {
  const out = [];
  for (const row of ROWS) for (const r of refsOf(row.node, row.doc)) {
    const t = target(r), probs = [];
    if (!t.ok) probs.push("대상 없음");
    if (!WITHIN.includes(r.within)) probs.push(`범위 '${r.within}'는 없는 값`);
    if (r.within === "screen" && !row.chain.includes("screen")) probs.push("범위 screen인데 화면 안 칸이 아님");
    if (r.within === "from" && row.def !== "step") probs.push("범위 from은 흐름 단계(step) 칸만");
    if (r.within === "role" && !row.chain.some((d) => d === "screen" || d === "role")) probs.push("범위 role인데 화면 · 역할 안 칸이 아님");
    if (r.within === "theme" && r.def !== "look") probs.push("범위 theme은 분위기(look) 칸만 가리킨다");
    const si = STAGES.indexOf(row.stage), ti = STAGES.indexOf(t.stage);
    const later = si >= 0 && ti >= 0 && row.stage !== "하네스" && ti > si;
    out.push({ from: objName(row.doc, row.def), field: row.local, path: row.path, doc: row.doc, ref: r, stage: row.stage, tstage: t.stage, to: objName(r.doc, r.def), ok: !probs.length, probs, later });
  }
  return out;
}

// ---------------------------------------------------------------------------
// 실행물 검사 — 형식(check) 다음 관계: 데이터를 스키마와 나란히 걸으며 객체 · 가리킴 · 하나뿐 칸을 모은다
// ---------------------------------------------------------------------------
function collect(doc, data, index, refs, uniques) {
  const root = DOCS[doc];
  const walk = (s, v, at, ctx) => {
    if (s.$ref) {
      const def = refDef(s.$ref);
      s = root.$defs[def];
      if (isObj(v) && s && (s.properties || isObj(s.additionalProperties))) {
        ctx = { ...ctx, $def: def, [def]: v };
        (index[`${doc}#${def}`] = index[`${doc}#${def}`] || []).push({ value: v, ctx });
      }
    }
    if (!s) return;
    if (s.anyOf) { const hit = s.anyOf.find((x) => { const o = { errs: [], warns: [] }; check(x, v, at, root, o); return !o.errs.length; }); if (hit) walk(hit, v, at, ctx); }
    if (Array.isArray(v) && s.items) v.forEach((x, i) => walk(s.items, x, `${at}[${i}]`, ctx));
    if (isObj(v) && s.properties) for (const [k, x] of Object.entries(v)) {
      const p = s.properties[k];
      if (!p) continue;
      if (p["x-ref"]) refs.push({ doc, at: `${at}.${k}`, value: x, refs: refsOf(p, doc), ctx, owner: v, ownerSchema: s });
      if (p["x-unique"]) uniques.push({ key: `${ctx.$def || "$root"}.${k}`, scope: p["x-unique"], at: `${at}.${k}`, value: x, ctx });
      walk(p, x, `${at}.${k}`, ctx);
    }
  };
  walk(root, data, "$", { $doc: doc });
}

function validateRun(runDir) {
  const data = {};
  for (const doc of Object.keys(DOCS)) {
    const p = path.join(runDir, `${doc}.json`);
    if (fs.existsSync(p)) data[doc] = JSON.parse(fs.readFileSync(p, "utf8"));
  }
  const report = [];
  let fails = 0;
  const show = (label, errs, warns) => {
    fails += errs.length;
    console.log(`${errs.length ? "FAIL" : "ok  "} ${label}${warns.length ? ` — 경고 ${warns.length}` : ""}`);
    for (const e of errs) console.log(`  - ${e}`);
    // 경고는 같은 칸끼리 묶는다(배열 번호를 지우고 센다)
    const groups = new Map();
    for (const w of warns) { const k = w.replace(/\[\d+\]/g, "[]"); groups.set(k, (groups.get(k) || 0) + 1); }
    for (const [w, n] of groups) console.log(`  · ${w}${n > 1 ? ` (${n}곳)` : ""}`);
  };
  for (const doc of Object.keys(DOCS)) {
    if (!data[doc]) { console.log(`skip ${doc}.json (없음)`); continue; }
    const out = { errs: [], warns: [] };
    check(DOCS[doc], data[doc], "$", DOCS[doc], out);
    show(`${doc}.json 형식 · 값`, out.errs, out.warns);
  }

  // 관계 — x-ref(범위 안) · x-unique · 화면 사이 규칙
  const index = {}, refs = [], uniques = [], errs = [], warns = [];
  for (const doc of Object.keys(data)) collect(doc, data[doc], index, refs, uniques);
  const S = data.screens || {}, F = data.flow || {};
  const objId = new WeakMap(); let seq = 0;
  const idOf = (o) => { if (!o) return "-"; if (!objId.has(o)) objId.set(o, ++seq); return objId.get(o); };
  const pick = (v, keys) => keys.reduce((acc, k) => acc.flatMap((x) => (Array.isArray(x) ? x : [x])).flatMap((x) => (isObj(x) && k in x ? [x[k]] : [])), [v]).flat();
  const valuesFor = (r, at) => {
    let list = index[`${r.doc}#${r.def}`] || [];
    if (r.within === "screen") list = list.filter((e) => e.ctx.screen === at.ctx.screen);
    if (r.within === "from") list = list.filter((e) => e.ctx.screen && at.ctx.step && e.ctx.screen.slug === at.ctx.step.from);
    if (r.within === "role") {
      const role = at.ctx.screen ? at.ctx.screen.role : at.ctx.role && at.ctx.role.key;
      list = list.filter((e) => e.ctx.screen && e.ctx.screen.role === role);
    }
    if (r.within === "theme") {
      const theme = (at.owner && at.owner.theme) || S.theme;
      const hit = list.filter((e) => e.value.id === theme);
      list = hit.length ? hit : list.slice(0, 1);
    }
    const keyMap = isObj(DOCS[r.doc].$defs[r.def].additionalProperties) && r.path.join(".") === "key";
    const vals = list.flatMap((e) => (keyMap ? Object.keys(e.value) : pick(e.value, r.path)));
    return { vals: new Set([...vals, ...r.also]), none: !list.length && r.within === "theme" };
  };
  for (const at of refs) {
    const items = Array.isArray(at.value) ? at.value : [at.value];
    // x-ref의 warnWith에 적힌 옛 칸이 같은 객체에 있을 때만 경고 — 옛 모양과만 생기는 어긋남(url을 복사한 시안 refs · target을 쓴 움직임)
    const old = at.refs.flatMap((r) => r.warnWith).find((k) => k in at.owner);
    for (const v of items) {
      if (typeof v !== "string") continue;
      const tries = at.refs.map((r) => ({ r, ...valuesFor(r, at) }));
      if (tries.some((t) => t.none)) continue;   // 분위기가 하나도 없으면 고를 대상이 없다(looks.js 기본 분위기)
      if (tries.some((t) => !t.r.legacy && t.vals.has(v))) continue;
      const viaOld = tries.find((t) => t.r.legacy && t.vals.has(v));
      if (viaOld) { warns.push(`${at.at}: '${v}' — 옛 대상 ${viaOld.r.to}를 가리킴(다음 판에서 지움)`); continue; }
      const msg = `${at.at}: '${v}'이(가) ${tries.map((t) => refLabel(t.r)).join(" 또는 ")}에 없음`;
      (old ? warns : errs).push(old ? `${msg} — 옛 칸 ${old}이 함께 있어 경고` : msg);
    }
  }
  const seen = new Map();
  for (const u of uniques) {
    const scope = u.scope === "doc" ? `${u.ctx.$doc}` : idOf(u.ctx[u.scope]);
    const k = `${u.key}|${u.scope}|${scope}|${JSON.stringify(u.value)}`;
    if (seen.has(k)) errs.push(`${u.at}: '${u.value}' 겹침 — ${seen.get(k)}와 같은 값(${u.scope === "doc" ? "문서 전체" : u.scope === "screen" ? "같은 화면" : "같은 분위기"} 안에서 하나뿐)`);
    else seen.set(k, u.at);
  }
  // 화면 사이 규칙(rules.json variant-target · overlay-reached · split-when)
  const screens = Array.isArray(S.screens) ? S.screens : [];
  const bySlug = new Map(screens.map((s) => [s.slug, s]));
  screens.forEach((s, i) => {
    for (const k of ["variantOf", "overlayOf"]) {
      if (!s[k]) continue;
      if (s[k] === s.slug) errs.push(`$.screens[${i}].${k}: 자기 자신을 가리킴 (규칙 variant-target)`);
      const t = bySlug.get(s[k]);
      if (t && t[k]) errs.push(`$.screens[${i}].${k}: '${s[k]}'도 ${k}가 있음 — ${k === "variantOf" ? "변형의 변형" : "창 위의 창"}은 안 된다 (규칙 variant-target)`);
    }
  });
  if (data.flow) {
    const steps = [...(F.flows || []).flatMap((f, i) => (f.steps || []).map((x, j) => ({ x, at: `$.flows[${i}].steps[${j}]` }))), ...(F.branches || []).map((x, j) => ({ x, at: `$.branches[${j}]` }))];
    const tos = new Set(steps.map((s) => s.x.to));
    screens.forEach((s, i) => { if (s.overlayOf && !tos.has(s.slug)) errs.push(`$.screens[${i}]: 뜨는 창 '${s.slug}'을 여는 흐름 단계 · 갈래(to)가 없음 (규칙 overlay-reached)`); });
    const groups = new Map();
    for (const s of steps.filter((x) => x.x.trigger)) { const k = `${s.x.from}|${s.x.trigger}`; groups.set(k, [...(groups.get(k) || []), s]); }
    for (const [k, list] of groups) if (list.length > 1) for (const s of list) if (!s.x.when) errs.push(`flow ${s.at}: 같은 화면 · 버튼(${k.replace("|", " · ")})이 ${list.length}번 — 갈래 이름표 when 필요 (규칙 split-when)`);
  }
  // when은 오류 · 완료 화면에만(rules.json state-pair) — 다른 상태에 있으면 경고
  screens.forEach((s, i) => { if (s.when !== undefined && s.state !== "error" && s.state !== "success") warns.push(`$.screens[${i}].when: state가 error · success인 화면에만 — 지금 state ${s.state === undefined ? "없음" : s.state} (규칙 state-pair)`); });
  show("관계 · 하나뿐 칸", errs, warns);
  return fails;
}

// ---------------------------------------------------------------------------
// 사전 · 정본 검사
// ---------------------------------------------------------------------------
const cell = (s) => String(s == null ? "" : s).replace(/\|/g, "/").replace(/\n/g, " ");
const valuesOf = (row) => {
  const n = row.res || {};
  if (n.anyOf && n.anyOf.every((x) => "const" in x)) return n.anyOf.map((x) => `${x.const}${x["x-status"] === "legacy" ? "(옛 값)" : ""}${x["x-krds"] ? `(KRDS ${x["x-krds"]})` : ""}`);
  if (n.enum) return n.enum.map(String);
  if (n.anyOf) { const e = n.anyOf.flatMap((x) => (x.enum ? x.enum.map((y) => `${y}${x["x-status"] === "legacy" ? "(옛 값)" : ""}`) : "const" in x ? [`${x.const}${x["x-status"] === "legacy" ? "(옛 값)" : ""}`] : [])); return e; }
  if (n.items && resolve(n.items, DOCS[row.doc]) && resolve(n.items, DOCS[row.doc]).anyOf) return valuesOf({ ...row, res: resolve(n.items, DOCS[row.doc]) });
  return [];
};
const statusOf = (row) => row.node["x-status"] || (row.res && row.res["x-status"]) || "";

function fieldsDoc() {
  const out = [
    "# 칸 사전 — screens.json · flow.json",
    "",
    "> `node scripts/schema.js --docs`가 정본 스키마(packages/core/schema/)에서 만든다. 손으로 고치지 않는다.",
    "> 상태: ✔ 쓰는 칸 · ○ 제안 · ✕ 옛 칸(받되 경고, 다음 판에서 지움). 필수: 필수 · 권장(없으면 경고, 다음 판에서 필수).",
    "> 단계는 그 칸을 쓰는 생성 단계 — 칸에 따로 적힌 단계(굵게)가 객체 단계보다 앞선다.",
    "",
  ];
  for (const doc of Object.keys(DOCS)) {
    const schema = DOCS[doc];
    out.push(`## ${doc}.json (v${schema["x-version"] || "?"})`, "", schema.description, "",
      "| 칸 | 상태 | 필수 | 단계 | 뜻 | 관계 · 규칙 · 읽는 곳 | 칸이 왜 있나 |", "|---|---|---|---|---|---|---|");
    const old = [];   // 옛 칸 아래 칸은 모두 옛 칸
    for (const row of WALK[doc].rows) {
      const n = row.node, vals = valuesOf(row);
      const inOld = old.some((p) => row.path.startsWith(`${p}.`) || row.path.startsWith(`${p}[]`));
      if (statusOf(row) === "legacy" || (row.def !== "$root" && DOCS[doc].$defs[row.def]["x-status"] === "legacy" && !row.local.includes("."))) old.push(row.path);
      const rel = [
        ...refsOf(n, doc).map((r) => `→ \`${refLabel(r)}\`${r.warnWith.length ? `(옛 칸 ${r.warnWith.join(" · ")}과 함께면 경고)` : ""}`),
        ...(n["x-unique"] ? [`하나뿐(${n["x-unique"]})`] : []),
        ...(n["x-rules"] || []).map((r) => `\`${r}\``),
        ...(n["x-feeds"] || []).map((f) => (CODE.includes(f) || f === BOARD ? f : `생성 → ${f}`)),
      ];
      out.push(`| \`${row.path}\` | ${inOld ? STATUS.legacy : STATUS[statusOf(row)] || ""} | ${row.required ? "필수" : row.recommended ? "권장" : ""} | ${row.ownStage ? `**${row.ownStage}**` : row.stage} | ${cell(n.description || (row.res || {}).description || "")}${vals.length ? ` — 값: ${cell(vals.join(" · "))}` : ""} | ${cell(rel.join(" · "))} | ${cell([n["x-why"], n["x-source"]].filter(Boolean).join(" · "))} |`);
    }
    out.push("");
  }
  return out.join("\n");
}

function relationsDoc(rels) {
  const objs = Object.entries(DOCS).flatMap(([doc, schema]) => Object.entries(schema.$defs || {}).filter(([, d]) => d["x-object"]).map(([key, d]) => ({ doc, key, d })));
  const id = (s) => s.replace(/[^가-힣A-Za-z0-9]/g, "_");
  const W = { doc: "문서 전체", screen: "같은 화면", from: "출발 화면", role: "같은 역할", theme: "고른 분위기" };
  return [
    "# 객체와 관계 — screens.json · flow.json",
    "",
    "> `node scripts/schema.js --docs`가 정본 스키마의 `x-object` · `x-layer` · `x-stage` · `x-ref`에서 만든다. 손으로 고치지 않는다.",
    "> 범위: 문서 전체 · 같은 화면(그 화면의 영역) · 출발 화면(흐름 단계 from의 영역) · 같은 역할(같은 role의 화면) · 고른 분위기(theme의 버튼 색).",
    "",
    "## 객체",
    "",
    "| 객체 | 정의 | 층 | 생성 단계 | 파일 | 뜻 |",
    "|---|---|---|---|---|---|",
    ...objs.map((o) => `| ${o.d["x-object"]} | \`${o.key}\`${o.d["x-status"] === "legacy" ? " ✕" : ""} | ${o.d["x-layer"] || ""} | ${WALK[o.doc].defStage[o.key] || ""} | ${o.doc}.json | ${cell(o.d.description || "")} |`),
    "",
    "## 관계",
    "",
    "```mermaid",
    "erDiagram",
    ...rels.map((r) => `  ${id(r.from)} }o--|| ${id(r.to)} : "${r.field}"`),
    "```",
    "",
    "| 가리키는 객체 | 칸 | 가리키는 곳 | 범위 | 단계 | 대상이 스키마에 있나 |",
    "|---|---|---|---|---|---|",
    ...rels.map((r) => `| ${r.from} | \`${r.field}\` | \`${r.ref.to}\`${r.ref.also.length ? ` ∪ ${r.ref.also.join(" · ")}` : ""}${r.ref.legacy ? " ✕ 옛 대상" : ""} | ${W[r.ref.within] || r.ref.within} | ${r.stage} → ${r.tstage || "?"}${r.later ? " ✕" : ""} | ${r.ok ? "○" : `✕ ${r.probs.join(" · ")}`} |`),
    "",
  ].join("\n");
}

/** 규칙 ↔ 칸 연결 검사 — 규칙은 fields로 칸을(또는 where로 파일을), 칸은 x-rules로 규칙을 가리킨다 */
function ruleLinks() {
  const byPath = new Map(ROWS.map((r) => [r.path, r]));
  const errs = [], ids = new Set();
  for (const r of RULES) {
    if (ids.has(r.id)) errs.push(`규칙 id 중복: ${r.id}`);
    ids.add(r.id);
    if (!STRENGTH[r.strength]) errs.push(`${r.id}: 강도 '${r.strength}'는 없는 값`);
    if (!(r.fields || []).length && !(r.where || []).length) errs.push(`${r.id}: fields도 where도 없음 — 규칙이 보는 곳이 있어야 한다`);
    for (const w of r.where || []) if (!fs.existsSync(path.join(DIR, "..", "..", "..", w))) errs.push(`${r.id}: where '${w}'이 저장소에 없음`);
    for (const f of r.fields || []) {
      if (!byPath.has(f)) errs.push(`${r.id}: 칸 '${f}'이 스키마에 없음`);
      else if (!(byPath.get(f).node["x-rules"] || []).includes(r.id)) errs.push(`${r.id}: 칸 '${f}'의 x-rules에 이 규칙이 없음`);
    }
  }
  for (const row of ROWS) for (const id of row.node["x-rules"] || []) {
    if (!ids.has(id)) errs.push(`칸 '${row.path}'의 x-rules '${id}'가 규칙 목록에 없음`);
    else if (!(RULES.find((r) => r.id === id).fields || []).includes(row.path)) errs.push(`칸 '${row.path}'이 규칙 '${id}'를 가리키는데 규칙의 fields에 이 칸이 없음`);
  }
  return errs;
}

function rulesDoc() {
  return [
    "# 규칙 사전 — 권장 · 규칙의 유일한 자리",
    "",
    "> `node scripts/schema.js --docs`가 packages/core/schema/rules.json에서 만든다. 손으로 고치지 않는다.",
    "> 칸이 무엇인지는 [칸 사전](fields.md) · [객체와 관계](relations.md), 규칙이 얼마나 지켜야 하는지는 여기. ○ = 제안(리뷰 대상).",
    "",
    "| 규칙 | 말 | 강도 | 칸 · 파일 | 값 | 검사 | 근거 |",
    "|---|---|---|---|---|---|---|",
    ...RULES.map((r) => `| \`${r.id}\`${r.status === "proposed" ? " ○" : ""} | ${cell(r.says)} | ${STRENGTH[r.strength] || r.strength} | ${[...(r.fields || []).map((f) => `\`${f}\``), ...(r.where || []).map((w) => `${w}`)].join(" ")} | ${cell(r.value && JSON.stringify(r.value))} | ${r.check.by}${r.check.level ? " " + r.check.level : ""}${r.check.status ? ` (아직 — ${cell(r.check.status)})` : ""} | ${cell(r.source)} |`),
    "",
  ].join("\n");
}

/** 생성 단계 — x-ref가 뒤 단계를 가리키면 오류 + 단계마다 한 요청의 구조화 출력 한도(선택 칸 24 · 유니온 16) */
function stagesReport() {
  const rels = relations();
  const lines = ["| 생성 단계 | 칸 | 선택 칸 | 유니온 | 닫히지 않은 객체 | strict 가능 |", "|---|---|---|---|---|---|"];
  let over = 0;
  const units = new Map();
  for (const [doc, schema] of Object.entries(DOCS)) for (const [k, v] of Object.entries(schema.properties)) {
    if (!v["x-stage"] || v["x-status"] === "legacy" || v["x-stage"] === "하네스") continue;
    const one = v.items && v.items.$ref && v["x-stage"].startsWith("S3");   // S3는 화면 하나가 한 요청
    if (!units.has(v["x-stage"])) units.set(v["x-stage"], []);
    units.get(v["x-stage"]).push({ label: `${doc}.json:${k}${one ? "[] 하나" : ""}`, node: one ? v.items : v, root: schema });
  }
  for (const stage of STAGES) {
    const list = units.get(stage);
    if (!list) continue;
    let optional = 0, unions = 0; const open = [], seen = new Set();
    const walk = (n, root, at) => {
      n = resolve(n, root); if (!n || typeof n !== "object") return;
      if (n.anyOf) { unions++; n.anyOf.forEach((x) => walk(x, root, at)); }
      if (n.items) walk(n.items, root, at + "[]");
      if (n.properties) {
        if (n.additionalProperties !== false) open.push(at || "(최상위)");
        const req = new Set([...(n.required || []), ...(n["x-recommended"] || [])]);   // 권장은 생성 요청에서는 필수로 묻는다
        for (const [k, v] of Object.entries(n.properties)) {
          if (k === "$schema" || v["x-status"] === "legacy") continue;
          if (v["x-stage"] && v["x-stage"] !== stage) continue;   // 칸 단위 단계는 그 단계 요청으로
          if (!req.has(k)) optional++;
          const key = (v.$ref || "") + at + "." + k;
          if (!seen.has(key)) { seen.add(key); walk(v, root, `${at}.${k}`); }
        }
      } else if (n.type === "object" && n.additionalProperties !== false) open.push(at || "(최상위)");
    };
    for (const u of list) walk(u.node, u.root, u.label);
    const ok = optional <= 24 && unions <= 16 && !open.length;
    if (optional > 24 || unions > 16) over++;
    lines.push(`| ${stage} | ${list.map((u) => u.label).join(" · ")} | ${optional}${optional > 24 ? " ✕" : ""} | ${unions}${unions > 16 ? " ✕" : ""} | ${open.join(" · ") || "—"} | ${ok ? "○" : open.length && optional <= 24 && unions <= 16 ? "△ 묶음은 비strict로 쓰고 검사" : "✕"} |`);
  }
  const later = rels.filter((r) => r.later);
  const missing = ROWS.filter((r) => !r.stage && r.def === "$root" && r.node["x-status"] !== "legacy" && r.local !== "$schema");
  return { lines, over, later, missing };
}

/** 읽는 곳 — 객체의 칸마다 ① 코드 ② 보드 중 하나 이상(규칙 · 관계도 코드가 본다). ③ 생성만 있는 칸은 경고 */
function feedsReport() {
  const rels = relations();
  const paths = new Set(ROWS.map((r) => r.path));
  const lines = ["| 객체 | 칸 | 읽는 곳 | |", "|---|---|---|---|"];
  let miss = 0, bad = 0, genOnly = 0;
  for (const row of ROWS) {
    const def = row.def === "$root" ? null : DOCS[row.doc].$defs[row.def];
    if (row.local.includes(".") || (def && !def["x-object"]) || statusOf(row) === "legacy" || (def && def["x-status"] === "legacy")) continue;
    const feeds = row.node["x-feeds"] || [];
    for (const f of feeds) if (!CODE.includes(f) && f !== BOARD && !paths.has(f)) { bad++; console.error(`FAIL ${objName(row.doc, row.def)}.${row.local}: x-feeds '${f}' — 코드 이름 · 보드 · 칸 경로가 아님`); }
    const into = rels.filter((r) => r.ref.doc === row.doc && r.ref.def === row.def && r.ref.path.join(".") === row.local);
    const code = [...(row.node["x-rules"] || []).map((r) => `규칙 ${r}`), ...into.map((r) => `← ${r.from}.${r.field}`), ...refsOf(row.node, row.doc).map((r) => `잇기 ${r.to}`), ...feeds.filter((f) => CODE.includes(f))];
    const board = feeds.filter((f) => f === BOARD);
    const gen = feeds.filter((f) => !CODE.includes(f) && f !== BOARD).map((f) => `생성 → ${f}`);
    const mark = code.length || board.length ? "○" : gen.length ? "△ 생성만" : "✕";
    if (mark === "✕") miss++; else if (mark !== "○") genOnly++;
    lines.push(`| ${objName(row.doc, row.def)} | \`${row.local}\` | ${[...code, ...board, ...gen].join(" · ") || "—"} | ${mark} |`);
  }
  return { lines, miss, bad, genOnly };
}

const DOC_FILES = { "fields.md": () => fieldsDoc(), "relations.md": () => relationsDoc(relations()), "rules.md": () => rulesDoc() };

module.exports = { check, relations, validateRun, DOCS, RULES, ROWS };
if (require.main !== module) return;

const args = process.argv.slice(2);
const has = (f) => args.includes(f);

if (has("--doc")) { process.stdout.write(fieldsDoc()); process.exit(0); }
if (has("--rules")) {
  process.stdout.write(rulesDoc());
  const errs = ruleLinks(); for (const e of errs) console.error(`FAIL ${e}`);
  process.exit(errs.length ? 1 : 0);
}
if (has("--relations")) {
  const rels = relations();
  process.stdout.write(relationsDoc(rels));
  for (const r of rels.filter((x) => !x.ok)) console.error(`FAIL ${r.from}.${r.field} → ${r.ref.to}: ${r.probs.join(" · ")}`);
  for (const p of uniqueProblems()) console.error(`FAIL ${p}`);
  process.exit(rels.some((r) => !r.ok) || uniqueProblems().length ? 1 : 0);
}
if (has("--stages")) {
  const { lines, over, later, missing } = stagesReport();
  console.log(lines.join("\n"));
  for (const r of later) console.log(`FAIL ${r.from}.${r.field}(${r.stage}) → ${r.ref.to}(${r.tstage}) — 뒤 단계 칸을 가리킴`);
  for (const r of missing) console.log(`FAIL ${r.path}: x-stage 없음`);
  console.log(`\n뒤 단계를 가리키는 관계 ${later.length} · 단계 없는 칸 ${missing.length} · 한도 넘는 단계 ${over} (선택 칸 24 · 유니온 16 — 옛 칸은 세지 않고, 권장 칸은 필수로 센다)`);
  process.exit(later.length || missing.length || over ? 1 : 0);
}
if (has("--feeds")) {
  const { lines, miss, bad, genOnly } = feedsReport();
  console.log(lines.join("\n"));
  console.log(`\n읽는 곳 없는 칸 ${miss} · 생성만 있는 칸 ${genOnly}(경고 — 안내문 시험이 확인할 때까지) · 틀린 x-feeds ${bad}`);
  process.exit(miss || bad ? 1 : 0);
}
if (has("--docs")) {
  for (const [f, make] of Object.entries(DOC_FILES)) { fs.mkdirSync(path.join(DIR, "docs"), { recursive: true }); fs.writeFileSync(path.join(DIR, "docs", f), make()); console.log(`썼음 packages/core/schema/docs/${f}`); }
  process.exit(0);
}
const flag = args.find((a) => a.startsWith("--"));
if (flag) { console.error(`모르는 옵션 ${flag} — 파일 머리 주석의 쓰는 법을 본다`); process.exit(2); }

if (args[0]) {
  if (!fs.existsSync(args[0])) { console.error(`없는 폴더: ${args[0]}`); process.exit(2); }
  process.exit(validateRun(args[0]) ? 1 : 0);
}

// 인자 없음 — 정본 자체 검사
let bad = 0;
const say = (ok, label, detail = []) => { if (!ok) bad++; console.log(`${ok ? "ok  " : "FAIL"} ${label}`); for (const d of detail) console.log(`  - ${d}`); };
const linkErrs = ruleLinks();
say(!linkErrs.length, `규칙 연결 — 규칙 ${RULES.length} · 규칙을 가리키는 칸 ${ROWS.filter((r) => (r.node["x-rules"] || []).length).length}`, linkErrs);
const rels = relations();
const uq = uniqueProblems();
say(rels.every((r) => r.ok) && !uq.length, `관계 — ${rels.length}개 (범위 있는 것 ${rels.filter((r) => r.ref.within !== "doc").length}) · 하나뿐 칸 ${ROWS.filter((r) => r.node["x-unique"]).length}`, [...rels.filter((r) => !r.ok).map((r) => `${r.from}.${r.field} → ${r.ref.to}: ${r.probs.join(" · ")}`), ...uq]);
const st = stagesReport();
say(!st.later.length && !st.missing.length && !st.over, `생성 단계 — 뒤 단계를 가리키는 관계 ${st.later.length} · 단계 없는 칸 ${st.missing.length} · 한도 넘는 단계 ${st.over}`, [...st.later.map((r) => `${r.from}.${r.field}(${r.stage}) → ${r.ref.to}(${r.tstage})`), ...st.missing.map((r) => `${r.path}: x-stage 없음`)]);
const fd = feedsReport();
say(!fd.miss && !fd.bad, `읽는 곳 — 없는 칸 ${fd.miss} · 생성만 ${fd.genOnly}(경고) · 틀린 x-feeds ${fd.bad}`);
const stale = Object.entries(DOC_FILES).filter(([f, make]) => { const p = path.join(DIR, "docs", f); return !fs.existsSync(p) || fs.readFileSync(p, "utf8") !== make(); }).map(([f]) => f);
say(!stale.length, `docs/ 최신${stale.length ? ` — 다시 만들기: node scripts/schema.js --docs` : ""}`, stale);
process.exit(bad ? 1 : 0);
