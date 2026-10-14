/**
 * lint-rules.js — rules.json에서 check.by가 lint인 규칙 중 lint.js 본문에 없는 것의 검사 코드.
 *
 *   const { check } = require("./lint-rules.js");
 *   check({ dir, screens, flow, html: { <slug>: 조각 HTML }, rules, report(level, ruleId, where, msg) });
 *
 * 규칙의 값(value)과 단계(check.level)는 rules.json에서 읽는다. 규칙 문장(says)은 lint.js가 규칙 id로 붙이므로
 * 여기 메시지는 "무엇이 몇 개 · 어디"만 적는다. rules.json에서 규칙을 지우면 그 검사도 꺼진다.
 */
const fs = require("fs");
const path = require("path");

const SCHEMA = path.join(__dirname, "..", "packages", "core", "schema", "screens.schema.json");
const PICK_CLS = /\b(chip|segmented-item|tab|day)\b/;   // 고르는 버튼은 모양이 바뀌는 것으로 충분 — build.js와 같은 기준
const VOIDS = new Set(["area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr", "use", "path", "circle", "rect", "line", "polyline", "polygon"]);

const attr = (attrs, name) => (new RegExp(`\\s${name}\\s*=\\s*["']([^"']*)["']`).exec(attrs) || [])[1];
const classesOf = (attrs) => (attr(attrs, "class") || "").split(/\s+/).filter(Boolean);
const textOf = (h) => h.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();

// 조각의 여는 태그마다 { tag, attrs, at, region(자기 것 또는 가장 가까운 바깥 data-region) } — 주석은 같은 길이 공백으로 지워 위치를 지킨다
function tagsOf(html) {
  const src = html.replace(/<!--[\s\S]*?-->/g, (c) => " ".repeat(c.length));
  const out = [], stack = [];
  for (const m of src.matchAll(/<(\/?)([a-zA-Z][\w-]*)([^>]*?)(\/?)>/g)) {
    const [, close, tagRaw, attrs, selfClose] = m, tag = tagRaw.toLowerCase();
    if (close) { for (let i = stack.length - 1; i >= 0; i--) if (stack[i].tag === tag) { stack.length = i; break; } continue; }
    const region = attr(attrs, "data-region") || [...stack].reverse().find((s) => s.region)?.region || null;
    out.push({ tag, attrs, at: m.index, region });
    if (!selfClose && !VOIDS.has(tag)) stack.push({ tag, region: attr(attrs, "data-region") || null });
  }
  return { src, tags: out };
}

// 그 자리에서 바뀌는 버튼(data-stay가 있는 button · a) — { label, msg, region, pick(고르는 버튼) }
function stayButtons(html) {
  const { src, tags } = tagsOf(html);
  const regionAt = new Map(tags.map((t) => [t.at, t.region]));
  const out = [];
  for (const m of src.matchAll(/<(button|a)\b([^>]*)>([\s\S]*?)<\/\1>/g)) {
    const msg = attr(m[2], "data-stay");
    if (msg === undefined) continue;
    out.push({ label: textOf(m[3]), msg, region: regionAt.get(m.index) || null, pick: PICK_CLS.test(classesOf(m[2]).join(" ")) });
  }
  return out;
}

// 스키마에서 이 규칙을 가리키는 칸의 값 중 강도가 case(사례)인 것 — tone-spread의 '사례 바탕'
function caseValues(ruleId) {
  let schema;
  try { schema = JSON.parse(fs.readFileSync(SCHEMA, "utf8")); } catch { return new Set(); }
  const found = new Set();
  (function walk(n) {
    if (!n || typeof n !== "object") return;
    if (Array.isArray(n["x-rules"]) && n["x-rules"].includes(ruleId) && Array.isArray(n.anyOf))
      for (const v of n.anyOf) if (v && v["x-strength"] === "case" && v.const !== undefined) found.add(v.const);
    for (const v of Object.values(n)) walk(v);
  })(schema);
  return found;
}

function check(ctx) {
  const S = ctx.screens || {}, F = ctx.flow || {}, HTML = ctx.html || {};
  const rules = new Map((ctx.rules || []).map((r) => [r.id, r]));
  const screens = Array.isArray(S.screens) ? S.screens : [];
  const bySlug = new Map(screens.map((s) => [s.slug, s]));
  const flows = Array.isArray(F.flows) ? F.flows : [];
  const branches = Array.isArray(F.branches) ? F.branches : [];
  const steps = flows.flatMap((f) => (f.steps || []).map((st) => ({ ...st, flow: f.key })));

  // 규칙이 rules.json에 있을 때만 돈다. 단계는 check.level, 없으면 fallback
  const rule = (id, fallback, fn) => {
    const r = rules.get(id);
    if (!r && !fallback) return;
    const level = (r && r.check && r.check.level) || fallback || "WARN";
    fn((where, msg) => ctx.report(level, id, where, msg), (r && r.value) || {});
  };

  // ---------- 화면마다 1순위 영역 하나, 그 key가 focus — 뜨는 창 · 입력 · 상태 변형 모두 ----------
  rule("rank1-one", null, (report, value) => {
    const top = Number(value) || 1;
    for (const s of screens) {
      const ones = (s.regions || []).filter((r) => r.level === top).map((r) => r.key);
      if (ones.length !== 1) report(`화면 ${s.slug}`, `${top}순위 영역 ${ones.length}개${ones.length ? ` (${ones.join(", ")})` : ""} — 하나로`);
      else if (s.focus !== ones[0]) report(`화면 ${s.slug}`, `focus ${s.focus ? `'${s.focus}'` : "없음"} — ${top}순위 영역은 '${ones[0]}'`);
    }
  });

  // ---------- 3순위 영역은 화면당 value.max 이하 ----------
  rule("rank3-max", null, (report, value) => {
    const max = Number.isInteger(value.max) ? value.max : 1;
    for (const s of screens) {
      const threes = (s.regions || []).filter((r) => r.level === 3).map((r) => r.key);
      if (threes.length > max) report(`화면 ${s.slug}`, `3순위 영역 ${threes.length}개 (${threes.join(", ")}) — ${max}개 이하`);
    }
  });

  // ---------- data 이름표는 facts에 ----------
  rule("data-key-exists", null, (report) => {
    if (Array.isArray(S.facts)) return;   // 옛 모양(배열) facts는 이름표가 없다 — schema.js가 옛 칸으로 알린다
    const keys = new Set(S.facts && typeof S.facts === "object" ? Object.keys(S.facts) : []);   // facts가 없으면 모든 이름표가 없는 것
    for (const s of screens) {
      if (!Array.isArray(s.data)) continue;   // 옛 모양(문장) data
      const missing = s.data.filter((k) => !keys.has(k));
      if (missing.length) report(`화면 ${s.slug}`, `facts에 없는 data 이름표: ${missing.map((k) => `'${k}'`).join(", ")}`);
    }
  });

  // ---------- 흐름마다 주인 역할 · 역할마다 처음 시작 흐름 하나 · goal을 이루는 흐름 하나 이상 ----------
  // 처음 시작 흐름 = 그 역할의 첫 흐름(역할별 처음 시작 흐름이 맨 앞) — 그 역할의 처음(first-run) · 빈(empty) 화면을 지나야 한다. goal 흐름 = 그 밖의 흐름
  rule("flow-role", null, (report) => {
    const roles = Array.isArray(S.roles) ? S.roles : [];
    const roleKeys = new Set(roles.map((r) => r.key));
    for (const f of flows) {
      if (!f.role) report(`흐름 ${f.key}`, `주인 역할(role) 없음`);
      else if (roleKeys.size && !roleKeys.has(f.role)) report(`흐름 ${f.key}`, `roles에 없는 role: '${f.role}'`);
    }
    const isStart = (slug, role) => { const s = bySlug.get(slug); return !!s && (s.state === "first-run" || s.state === "empty") && (!s.role || s.role === role); };
    for (const r of roles) {
      const mine = flows.filter((f) => f.role === r.key);
      const first = mine[0];
      const started = !!first && (first.steps || []).some((st) => isStart(st.from, r.key) || isStart(st.to, r.key));
      const goals = started ? mine.slice(1) : mine;
      const goal = r.goal ? ` — goal '${r.goal}'` : "";
      if (!first) report(`역할 ${r.key}`, `흐름 없음${goal}`);
      else {
        if (!started) report(`역할 ${r.key}`, `첫 흐름 '${first.key}'이 이 역할의 처음 · 빈 상태 화면을 지나지 않음`);
        if (!goals.length) report(`역할 ${r.key}`, `goal을 이루는 흐름 없음${goal}`);
      }
    }
  });

  // ---------- 채운 버튼(btn-primary)은 화면당 value.max 이하 ----------
  rule("primary-action-one", null, (report, value) => {
    const max = Number.isInteger(value.max) ? value.max : 1;
    for (const [slug, html] of Object.entries(HTML)) {
      const n = tagsOf(html).tags.filter((t) => classesOf(t.attrs).includes("btn-primary")).length;
      if (n > max) report(`화면 ${slug}`, `채운 버튼(.btn-primary) ${n}개 — ${max}개 이하`);
    }
  });

  // ---------- 분위기 바탕 톤: value.min_tones가지 이상(tone 있는 분위기가 그보다 적으면 모두 다르게) · 사례 바탕 value.max_case개까지 ----------
  rule("tone-spread", null, (report, value) => {
    const looks = (Array.isArray(S.looks) ? S.looks : []).filter((L) => L && L.tone);   // tone 없는 분위기는 세지 않는다 — 칸 없음은 schema.js 몫
    if (!looks.length) return;
    const need = Math.min(Number.isInteger(value.min_tones) ? value.min_tones : 3, looks.length);
    const kinds = new Set(looks.map((L) => L.tone));
    if (kinds.size < need) report(`tone 있는 분위기 ${looks.length}개`, `바탕 톤 ${kinds.size}가지(${[...kinds].join(" · ") || "없음"}) — ${need}가지 이상`);
    const caseTones = caseValues("tone-spread");
    const cases = looks.filter((L) => caseTones.has(L.tone));
    const maxCase = Number.isInteger(value.max_case) ? value.max_case : 1;
    if (cases.length > maxCase) report(`분위기 ${cases.map((L) => L.id).join(", ")}`, `사례 바탕(${[...caseTones].join(" · ")}) ${cases.length}개 — ${maxCase}개까지`);
  });

  // ---------- 계획(regions[].stays) ↔ 결과(조각의 data-stay) ----------
  // rules.json에 아직 규칙 id가 없다 — 있으면 그 단계, 없으면 WARN
  rule("stays-match", "WARN", (report) => {
    const planned = screens.some((s) => (s.regions || []).some((r) => Array.isArray(r.stays) && r.stays.length));
    for (const s of screens) {
      const html = HTML[s.slug];
      if (typeof html !== "string") continue;   // 조각 전(시안 단계)
      const got = stayButtons(html);
      for (const r of s.regions || []) for (const x of r.stays || []) {
        const hit = got.find((b) => b.label === x.label);
        if (!hit) report(`화면 ${s.slug} / ${r.key}`, `조각에 data-stay 버튼이 없는 stays: '${x.label}'`);
        else if (hit.region !== r.key) report(`화면 ${s.slug} / ${r.key}`, `data-stay 버튼 '${x.label}'이 영역 '${hit.region || "영역 밖"}'에 있음`);
        else if (x.msg && hit.msg !== x.msg) report(`화면 ${s.slug} / ${r.key}`, `'${x.label}' 문구가 다름 — stays "${x.msg}" · 조각 "${hit.msg}"`);
      }
      if (!planned) continue;   // 계획을 아예 안 쓴 실행물(옛 형식)은 조각 쪽만 있는 버튼을 묻지 않는다
      const known = new Set((s.regions || []).flatMap((r) => (r.stays || []).map((x) => x.label)));
      const extra = got.filter((b) => !b.pick && !known.has(b.label)).map((b) => b.label);   // 고르는 버튼은 계획에 없어도 된다
      if (extra.length) report(`화면 ${s.slug}`, `stays에 없는 data-stay 버튼: ${[...new Set(extra)].map((t) => `'${t}'`).join(", ")}`);
    }
  });

  // ---------- 처음 시작 화면에서 흐름 · 갈래 · 메뉴로 모든 화면에 닿는다 ----------
  // 변형(variantOf)은 바탕 화면으로 접어 센다(바탕의 버튼을 그대로 쓴다). 뜨는 창은 대상에서 빼지만, 닿으면 그 창의 버튼도 길이 된다.
  // 시작 = 역할마다 메뉴 첫 화면 · 첫 흐름의 출발 화면, 그리고 처음 · 빈 상태 화면. 메뉴 틀이 none인 화면에서는 메뉴로 갈 수 없다
  rule("reachable", null, (report) => {
    const node = (slug) => { const s = bySlug.get(slug); return s && s.variantOf && bySlug.has(s.variantOf) ? s.variantOf : slug; };
    const concepts = Array.isArray(S.concepts) ? S.concepts : [];
    const main = concepts.find((c) => c.id === S.concept) || concepts[0];
    const shellOf = (s) => s.shell || (main && main.shell) || null;
    const roles = Array.isArray(S.roles) ? S.roles : [];
    const navOf = new Map(roles.map((r) => [r.key, (r.nav || []).map((n) => n.slug).filter((x) => bySlug.has(x))]));
    const next = new Map();
    const edge = (a, b) => { if (!bySlug.has(a) || !bySlug.has(b)) return; a = node(a); if (!next.has(a)) next.set(a, new Set()); next.get(a).add(node(b)); };
    for (const x of [...steps, ...branches]) edge(x.from, x.to);
    for (const s of screens) if (!s.overlayOf && shellOf(s) !== "none") for (const n of navOf.get(s.role) || []) edge(s.slug, n);
    const starts = new Set();
    for (const r of roles) {
      if ((navOf.get(r.key) || [])[0]) starts.add(node(navOf.get(r.key)[0]));
      const first = flows.find((f) => f.role === r.key);
      if (first && first.steps && first.steps[0] && bySlug.has(first.steps[0].from)) starts.add(node(first.steps[0].from));
    }
    for (const s of screens) if (s.state === "first-run" || s.state === "empty") starts.add(node(s.slug));
    if (!starts.size) return;   // 시작을 정할 수 없는 실행물(역할 · 흐름 없음)은 다른 검사가 알린다
    const seen = new Set(starts), queue = [...starts];
    while (queue.length) for (const b of next.get(queue.shift()) || []) if (!seen.has(b)) { seen.add(b); queue.push(b); }
    const noneShell = (main && main.shell === "none") || [...starts].some((x) => shellOf(bySlug.get(x)) === "none");
    const lost = screens.filter((s) => !s.variantOf && !s.overlayOf && !seen.has(s.slug)).map((s) => s.slug);
    for (const slug of lost) report(`화면 ${slug}`, `처음 시작 화면(${[...starts].join(", ")})에서 흐름 · 갈래 · 메뉴로 닿지 않음${noneShell ? " — 메뉴 없는 틀(none)이라 홈에 갈래가 필요" : ""}`);
  });

  // ---------- 뜨는 창 화면은 흐름 단계 · 갈래의 도착(to) ----------
  rule("overlay-reached", null, (report) => {
    const tos = new Set([...steps, ...branches].map((x) => x.to));
    for (const s of screens) if (s.overlayOf && !tos.has(s.slug)) report(`화면 ${s.slug}`, `뜨는 창인데 도착(to)으로 삼는 흐름 단계 · 갈래가 없음`);
  });

  // ---------- 같은 from + trigger가 두 번 이상이면 그 모두에 when ----------
  rule("split-when", null, (report) => {
    const groups = new Map();
    for (const x of [...steps.map((st) => ({ ...st, at: `흐름 ${st.flow}` })), ...branches.map((b, i) => ({ ...b, at: `갈래 ${i + 1}` }))]) {
      if (!x.from || !x.trigger) continue;
      const k = x.from + "|" + x.trigger;
      if (!groups.has(k)) groups.set(k, []);
      groups.get(k).push(x);
    }
    for (const [k, xs] of groups) {
      if (xs.length < 2) continue;
      const bare = xs.filter((x) => typeof x.when !== "string" || !x.when.trim());
      if (bare.length) report(k.replace("|", " / "), `${xs.length}번 나옴(${xs.map((x) => `${x.at} → ${x.to}`).join(" · ")}) — when 없는 곳: ${bare.map((x) => x.at).join(", ")}`);
    }
  });
}

module.exports = { check };
