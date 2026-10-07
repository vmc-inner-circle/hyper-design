#!/usr/bin/env node
/**
 * expand.js — 화면 조각을 빠르게 쓰게 해 주는 두 가지를 실제 HTML로 펼쳐 파일에 다시 쓴다.
 *
 *   node scripts/expand.js runs/<project>            screens/*.html · concepts/<id>/*.html 전부
 *   node scripts/expand.js runs/<project> --reshell  이미 셸이 있는 화면도 셸을 새로 붙인다(시안을 바꿨을 때)
 *
 * 1) 셸 자동 조립 — 조각에 `<div class="app">`이 없으면(뜨는 창 제외) 상단바·메뉴를 붙인다.
 *    메뉴 = screens.json roles[역할].nav, 메뉴 구조 = 시안의 shell(sidebar·top·rail), 현재 화면 항목에 .active.
 *    조각은 `<main class="content">…</main>` 하나만 쓰면 된다. (pattern이 onboarding이거나 shell:"none"이면 메뉴 없는 한 장)
 * 2) 짧은 부품 태그 — <x-btn> <x-badge> <x-icon> <x-avatar> <x-item> <x-list> <x-stat> <x-empty> <x-card>
 *    <x-section> <x-page-header> <x-modal> 을 packages/web 조각과 같은 HTML로 펼친다. 형식은 packages/web/snippets/05-parts.md.
 *    data-*·aria-*·id·title·href·class는 펼친 요소의 바깥 태그로 그대로 옮긴다.
 *
 * 3) 모바일(screens.json platform: "mobile") — 셸은 .app.app-mobile: 탭 화면(roles[].nav에 있는 화면)은 아래 탭(.tabbar),
 *    그 밖의 화면은 위 제목 줄(.appbar: 뒤로 data-back · 가운데 화면 이름), 온보딩·shell "none"은 메뉴 없는 한 장.
 *    시안 shell: tabbar(기본 — web의 sidebar·rail도 이것으로) · top(서비스 이름 줄 + 위 알약 탭) · none.
 *    <x-modal>은 아래에서 올라오는 창(.modal-backdrop.sheet-backdrop > .modal.sheet)으로 펼친다. 형식은 packages/mobile/snippets.
 *
 * 펼친 결과를 파일에 다시 쓰므로 이후 lint·보드(요소 고르기 경로)·수정 에이전트는 모두 일반 HTML만 본다.
 * 한 번 펼친 파일에 다시 돌려도 바뀌지 않는다.
 */
const fs = require("fs");
const path = require("path");

const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const ico = (name, cls = "icon", extra = "") => `<svg class="${cls}${extra ? " " + extra : ""}" aria-hidden="true"><use href="#i-${name}"/></svg>`;

// ---------- 속성 ----------
function parseAttrs(s) {
  const a = {};
  for (const m of (s || "").matchAll(/([a-zA-Z_:][\w:.-]*)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'>]+)))?/g)) {
    a[m[1]] = m[2] !== undefined ? m[2] : m[3] !== undefined ? m[3] : m[4] !== undefined ? m[4] : "";
  }
  return a;
}
// 부품 고유 속성을 뺀 나머지(data-*·aria-*·id·title·href 등)를 바깥 태그로
function pass(a, own) {
  return Object.keys(a).filter((k) => !own.includes(k) && k !== "class")
    .map((k) => (a[k] === "" ? ` ${k}` : ` ${k}="${esc(a[k])}"`)).join("");
}
const cls = (...xs) => xs.filter(Boolean).join(" ");
// 머리줄 오른쪽 글자 버튼: action="전체 보기" + action-trigger="<key>" 또는 action-stay="안내 문구" 또는 action-back
function headAction(a, klass) {
  if (!a.action) return "";
  const how = a["action-trigger"] ? ` data-trigger="${esc(a["action-trigger"])}"` : a["action-back"] !== undefined ? " data-back" : ` data-stay="${esc(a["action-stay"] || "")}"`;
  return `<button class="${klass}"${how}>${esc(a.action)}</button>`;
}
const HEAD_OWN = ["action", "action-trigger", "action-stay", "action-back"];
// 부품이 모르는 속성은 경고 (조용히 사라지거나 엉뚱하게 붙지 않게)
const PASS_OK = /^(data-|aria-)|^(id|title|href|role|type|for|name|value|placeholder|target|rel|tabindex|disabled|checked|selected|src|alt)$/;
const warnings = [];
function checkAttrs(name, a, own) {
  for (const k of Object.keys(a)) if (!own.includes(k) && k !== "class" && !PASS_OK.test(k)) warnings.push(`<${name}>의 모르는 속성 '${k}' — 05-parts.md 확인`);
}

// ---------- 부품 ----------
let platformNow = "web";   // expandFragment가 screens.json platform으로 정한다 (x-modal이 모바일에서 아래 창이 된다)
const TONES = ["neutral", "primary", "success", "warning", "danger", "info"];
const PARTS = {
  "x-icon": (a) => ico(a.name || "circle", a.size === "sm" ? "icon-sm" : a.size === "lg" ? "icon-lg" : "icon", cls(a.tone ? "text-" + a.tone : "", a.class)),
  "x-btn": (a, inner) => {
    const v = a.variant || "secondary", sm = a.size === "sm", icOnly = !inner.trim() && a.icon;
    const c = cls("btn", v === "secondary" ? "btn-secondary" : "btn-" + v, sm ? "btn-sm" : a.size === "lg" ? "btn-lg" : "", icOnly ? "btn-icon" : "", a.class);
    const own = ["variant", "size", "icon", "icon-end"];
    const body = (a.icon ? ico(a.icon, sm || icOnly ? "icon-sm" : "icon") : "") + inner.trim() + (a["icon-end"] ? ico(a["icon-end"], "icon-sm") : "");
    return a.href !== undefined ? `<a class="${c}"${pass(a, own)}>${body}</a>` : `<button class="${c}"${pass(a, own)}>${body}</button>`;
  },
  "x-badge": (a, inner) => `<span class="${cls("badge", "badge-" + (TONES.includes(a.tone) ? a.tone : "neutral"), a.class)}"${pass(a, ["tone", "icon"])}>${a.icon ? ico(a.icon, "icon-sm") : ""}${inner.trim()}</span>`,
  "x-avatar": (a, inner) => `<span class="${cls("avatar", a.size ? "avatar-" + a.size : "", a.tone ? "avatar-" + a.tone : "", a.class)}"${pass(a, ["size", "tone"])}>${inner.trim()}</span>`,
  "x-list": (a, inner) => `<ul class="${cls("list", a.plain === undefined ? "list-divided" : "", a.compact !== undefined ? "list-compact" : "", a.class)}"${pass(a, ["plain", "compact"])}>${inner}</ul>`,
  "x-item": (a, inner) => {
    const lead = a.avatar ? `<span class="${cls("avatar", "avatar-sm", a["avatar-tone"] ? "avatar-" + a["avatar-tone"] : "")}">${esc(a.avatar)}</span>`
      : a.icon ? `<span class="${cls("list-icon", a.tone ? "is-" + a.tone : "")}">${ico(a.icon, a.small !== undefined ? "icon-sm" : "icon")}</span>` : "";
    const badge = a.badge ? ` <span class="badge badge-${TONES.includes(a["badge-tone"]) ? a["badge-tone"] : "neutral"}">${esc(a.badge)}</span>` : "";
    const main = `<div class="list-main"><span class="list-title">${esc(a.title || "")}${badge}</span>${a.sub ? `<span class="list-sub">${esc(a.sub)}</span>` : ""}</div>`;
    const meta = a.meta ? `<span class="list-meta">${esc(a.meta)}</span>` : "";
    const acts = inner.trim() ? `<div class="list-actions">${inner.trim()}</div>` : "";
    const own = ["avatar", "avatar-tone", "icon", "tone", "small", "title", "sub", "meta", "badge", "badge-tone", "muted", "selected"];
    return `<li class="${cls("list-item", a.muted !== undefined ? "is-muted" : "", a.selected !== undefined ? "is-selected" : "", a.class)}"${pass(a, own)}>${lead}${main}${meta}${acts}</li>`;
  },
  "x-stat": (a) => {
    const d = a.delta ? `<span class="${cls("stat-delta", a.dir)}">${a.dir === "up" ? ico("trending-up", "icon-sm") + " " : a.dir === "down" ? ico("trending-down", "icon-sm") + " " : ""}${esc(a.delta)}</span>` : "";
    return `<div class="${cls("stat", a.class)}"${pass(a, ["label", "value", "unit", "delta", "dir"])}><span class="stat-label">${esc(a.label || "")}</span><span class="stat-value">${esc(a.value || "")}${a.unit ? `<small>${esc(a.unit)}</small>` : ""}</span>${d}</div>`;
  },
  "x-empty": (a, inner) => `<div class="${cls("empty", a.size === "sm" ? "empty-sm" : "", a.class)}"${pass(a, ["icon", "title", "desc", "size"])}><span class="empty-icon">${ico(a.icon || "inbox", "icon-lg")}</span><h3 class="empty-title">${esc(a.title || "")}</h3>${a.desc ? `<p class="empty-desc">${esc(a.desc)}</p>` : ""}${inner.trim() ? `<div class="empty-actions">${inner.trim()}</div>` : ""}</div>`,
  // 카드: title이 있으면 머리줄(action 속성 = 머리줄 오른쪽 글자 버튼), flush면 본문 여백 없이(목록을 바로 넣을 때)
  "x-card": (a, inner) => {
    const head = a.title || a.action ? `<div class="card-header"><h3 class="card-title">${esc(a.title || "")}</h3>${headAction(a, "btn btn-ghost btn-sm")}</div>` : "";
    const own = ["title", "flush", "selected", "clickable"].concat(HEAD_OWN);
    return `<div class="${cls("card", a.selected !== undefined ? "is-selected" : "", a.clickable !== undefined ? "card-clickable" : "", a.class)}"${pass(a, own)}>${head}${a.flush !== undefined ? inner : `<div class="card-body">${inner}</div>`}</div>`;
  },
  "x-section": (a, inner) => `<section class="${cls("section", a.class)}"${pass(a, ["title", "icon", "desc"].concat(HEAD_OWN))}>${a.title || a.action ? `<h2 class="section-title">${a.icon ? ico(a.icon) : ""}${esc(a.title || "")}${headAction(a, "link link-muted")}</h2>` : ""}${a.desc ? `<p class="section-desc">${esc(a.desc)}</p>` : ""}${inner}</section>`,
  "x-page-header": (a, inner) => `<div class="${cls("page-header", a.class)}"${pass(a, ["title", "desc", "eyebrow"])}><div>${a.eyebrow ? `<p class="eyebrow">${esc(a.eyebrow)}</p>` : ""}<h1 class="page-title">${esc(a.title || "")}</h1>${a.desc ? `<p class="page-desc">${esc(a.desc)}</p>` : ""}</div>${inner.trim() ? `<div class="page-actions">${inner.trim()}</div>` : ""}</div>`,
  // 뜨는 창: 머리줄(제목·설명·닫기=data-back) + 본문. 안쪽에 <div class="modal-footer">가 있으면 거기부터 바닥줄
  "x-modal": (a, inner) => {
    if (platformNow === "mobile") return sheet(a, inner);
    const i = inner.indexOf('<div class="modal-footer"');
    const body = i < 0 ? inner : inner.slice(0, i), foot = i < 0 ? "" : inner.slice(i);
    const m = cls("modal", a.size ? "modal-" + a.size : "", a.center !== undefined ? "modal-center" : "", a.class);
    return `<div class="modal-backdrop"><div class="${m}" role="dialog"${pass(a, ["title", "desc", "size", "center"])}><div class="modal-header"><div><h2 class="modal-title">${esc(a.title || "")}</h2>${a.desc ? `<p class="modal-desc">${esc(a.desc)}</p>` : ""}</div><button class="btn btn-icon btn-ghost" aria-label="닫기" data-back>${ico("x")}</button></div><div class="modal-body">${body}</div>${foot}</div></div>`;
  },
};

// 모바일 아래 창: 손잡이 + 머리줄(제목·설명) + 본문 + 바닥줄(버튼 위아래로). 닫기(X)는 바닥줄에 data-back 버튼이 없을 때만
function sheet(a, inner) {
  const i = inner.indexOf('<div class="modal-footer"');
  const body = i < 0 ? inner : inner.slice(0, i), foot = i < 0 ? "" : inner.slice(i);
  const m = cls("modal", "sheet", a.center !== undefined ? "modal-center" : "", a.class);
  const close = /\sdata-back\b/.test(foot) ? "" : `<button class="btn btn-icon btn-ghost" aria-label="닫기" data-back>${ico("x")}</button>`;
  return `<div class="modal-backdrop sheet-backdrop"><div class="${m}" role="dialog"${pass(a, ["title", "desc", "size", "center"])}><span class="sheet-handle" aria-hidden="true"></span><div class="modal-header"><div><h2 class="modal-title">${esc(a.title || "")}</h2>${a.desc ? `<p class="modal-desc">${esc(a.desc)}</p>` : ""}</div>${close}</div>${body.trim() ? `<div class="modal-body">${body}</div>` : ""}${foot}</div></div>`;
}
// 모바일에서 부품 없이 직접 쓴 가운데 창(<div class="modal-backdrop"><div class="modal …">)도 아래 창으로 바꾼다 (서랍은 그대로)
function toSheet(html) {
  if (/\bsheet-backdrop\b/.test(html) || /class=["'][^"']*\bdrawer\b/.test(html)) return html;
  return html.replace(/^<div\s+class=(["'])([^"']*\bmodal-backdrop\b[^"']*)\1/, (m, q, c) => `<div class=${q}${c} sheet-backdrop${q}`)
    .replace(/class=(["'])modal((?:\s[^"']*)?)\1/, (m, q, rest) => `class=${q}modal sheet${rest}${q}`);
}

const OWN = {
  "x-icon": ["name", "size", "tone"], "x-btn": ["variant", "size", "icon", "icon-end"], "x-badge": ["tone", "icon"],
  "x-avatar": ["size", "tone"], "x-list": ["plain", "compact"],
  "x-item": ["avatar", "avatar-tone", "icon", "tone", "small", "title", "sub", "meta", "badge", "badge-tone", "muted", "selected"],
  "x-stat": ["label", "value", "unit", "delta", "dir"], "x-empty": ["icon", "title", "desc", "size"],
  "x-card": ["title", "flush", "selected", "clickable"].concat(HEAD_OWN), "x-section": ["title", "icon", "desc"].concat(HEAD_OWN),
  "x-page-header": ["title", "desc", "eyebrow"], "x-modal": ["title", "desc", "size", "center"],
};
// 가장 안쪽(마지막으로 열린) 부품부터 펼친다 — 부품 안에 부품을 넣어도 된다
function expandParts(html) {
  let guard = 0;
  for (;;) {
    const open = [...html.matchAll(/<(x-[a-z-]+)\b((?:[^>"']|"[^"]*"|'[^']*')*?)(\/?)>/g)].pop();
    if (!open || ++guard > 5000) break;
    const [tag, name, attrStr, selfClose] = open, start = open.index, fn = PARTS[name];
    if (!fn) throw new Error(`모르는 부품 <${name}> — packages/web/snippets/05-parts.md에 있는 것만`);
    let inner = "", end = start + tag.length;
    if (!selfClose && name !== "x-icon" && name !== "x-stat") {
      const close = html.indexOf(`</${name}>`, end);
      if (close < 0) throw new Error(`<${name}>의 닫는 태그가 없음`);
      inner = html.slice(end, close); end = close + name.length + 3;
    } else if (!selfClose) {
      const close = html.indexOf(`</${name}>`, end);   // <x-icon ...></x-icon> 형태도 허용
      if (close >= 0 && !/<[a-z]/i.test(html.slice(end, close))) end = close + name.length + 3;
    }
    const attrs = parseAttrs(attrStr);
    checkAttrs(name, attrs, OWN[name] || []);
    html = html.slice(0, start) + fn(attrs, inner) + html.slice(end);
  }
  return html;
}

// ---------- 셸 ----------
const SHELL_CLASS = { sidebar: "", top: "nav-top", rail: "nav-rail", none: "no-sidebar" };
function shellFor(S, s, conceptId) {
  if (S.platform === "mobile") return MOBILE_SHELL[shellRaw(S, s, conceptId)] || "tabbar";
  return shellRaw(S, s, conceptId);
}
function shellRaw(S, s, conceptId) {
  if (s.shell) return s.shell;
  if (s.pattern === "onboarding") return "none";
  const C = (S.concepts || []).find((c) => c.id === (conceptId || S.concept)) || (S.concepts || [])[0];
  return (C && C.shell) || S.shell || "sidebar";
}
function wrapShell(S, s, body, shell) {
  const role = (S.roles || []).find((r) => r.key === s.role) || (S.roles || [])[0] || { nav: [] };
  const user = role.user || {}, initials = user.initials || (role.label || "나").slice(0, 2);
  const activeSlug = s.navActive || s.slug, alt = s.variantOf;
  const items = shell === "none" ? "" : (role.nav || []).map((n) =>
    `<a class="nav-item${n.slug === activeSlug || n.slug === alt ? " active" : ""}" href="#">${ico(n.icon || "circle")}<span>${esc(n.label)}</span></a>`).join("\n      ");
  const brand = `<div class="topnav-brand">${ico(S.brandIcon || "layout-dashboard")}<span>${esc(S.brand || S.title || "")}</span></div>`;
  const actions = `<div class="topnav-actions"><button class="btn btn-ghost btn-icon" aria-label="알림">${ico("bell")}</button><div class="avatar avatar-sm">${esc(initials)}</div></div>`;
  const top = shell === "top"
    ? `<header class="topnav">\n    ${brand}\n    <nav class="topnav-nav">\n      ${items}\n    </nav>\n    ${actions}\n  </header>`
    : `<header class="topnav">\n    ${brand}\n    <div class="topnav-title">${esc(s.name || "")}</div>\n    ${actions}\n  </header>`;
  const side = shell === "sidebar" || shell === "rail"
    ? `\n  <aside class="sidebar">\n    <nav class="nav">\n      ${items}\n    </nav>\n    <div class="sidebar-footer"><a class="nav-item" href="#"><div class="avatar avatar-sm">${esc(initials)}</div><span class="truncate">${esc(user.name || role.label || "")}</span></a></div>\n  </aside>` : "";
  let main = body.trim();
  if (!/^<main\b/.test(main)) main = `<main class="content">\n${main}\n</main>`;
  if (shell === "top" && !/content-inner/.test(main)) main = main.replace(/^<main([^>]*)>/, '<main$1><div class="content-inner">').replace(/<\/main>\s*$/, "</div></main>");
  return `<div class="${cls("app", SHELL_CLASS[shell])}">\n  ${top}${side}\n  ${main}\n</div>\n`;
}
// ---------- 모바일 셸 ----------
// 시안 shell(web 값 포함) → 모바일 셸: tabbar(아래 탭) · top(위 알약 탭) · none(메뉴 없음) · back(뒤로 제목 줄 강제)
const MOBILE_SHELL = { sidebar: "tabbar", rail: "tabbar", tabbar: "tabbar", top: "top", none: "none", back: "back" };
function wrapMobile(S, s, body, shell) {
  const role = (S.roles || []).find((r) => r.key === s.role) || (S.roles || [])[0] || { nav: [] };
  const nav = role.nav || [], alt = s.variantOf;
  // 탭 화면 = 메뉴에 있는 화면(또는 그 변형). 나머지는 뒤로 가는 아래 화면
  const isTab = nav.some((n) => n.slug === s.slug || (alt && n.slug === alt));
  const mode = shell === "none" ? "none" : shell === "back" || !isTab ? "back" : shell === "top" ? "top" : "tabbar";
  const activeSlug = s.navActive || s.slug;
  const items = nav.map((n) =>
    `<a class="nav-item${n.slug === activeSlug || n.slug === alt ? " active" : ""}" href="#">${ico(n.icon || "circle")}<span>${esc(n.label)}</span></a>`).join("\n    ");
  let main = body.trim();
  if (!/^<main\b/.test(main)) main = `<main class="content">\n${main}\n</main>`;
  const title = esc(String(s.name || "").replace(/\s*\([^)]*\)\s*$/, ""));   // "스튜디오 홈 (처음)" → "스튜디오 홈"
  if (mode === "none") return `<div class="app app-mobile no-nav">\n  ${main}\n</div>\n`;
  if (mode === "back") return `<div class="app app-mobile">\n  <header class="appbar"><button class="btn btn-ghost btn-icon" aria-label="뒤로" data-back>${ico("chevron-left")}</button><div class="appbar-title">${title}</div><div class="appbar-actions"></div></header>\n  ${main}\n</div>\n`;
  if (mode === "top") return `<div class="app app-mobile nav-top">\n  <header class="appbar appbar-start"><div class="appbar-title">${esc(S.brand || S.title || "")}</div><div class="appbar-actions"><button class="btn btn-ghost btn-icon" aria-label="알림">${ico("bell")}</button></div></header>\n  <nav class="toptabs">\n    ${items}\n  </nav>\n  ${main}\n</div>\n`;
  return `<div class="app app-mobile">\n  ${main}\n  <nav class="tabbar">\n    ${items}\n  </nav>\n</div>\n`;
}

// 이미 셸이 있는 조각에서 본문(main + 그 뒤 창)만 꺼낸다 (--reshell). 모바일 아래 탭(main 뒤)은 셸이므로 뺀다
function stripShell(html) {
  const a = html.indexOf("<main"), b = html.lastIndexOf("</div>");
  return a < 0 || b < 0 ? html : html.slice(a, b).replace(/\s*<nav class="tabbar">[\s\S]*?<\/nav>/, "").trim();
}

function expandFragment(S, s, html, o = {}) {
  const mobile = S.platform === "mobile";
  platformNow = mobile ? "mobile" : "web";
  let out = expandParts(html);
  const trimmed = out.trim();
  if (s.overlayOf || /^<div\s+class=["'][^"']*\bmodal-backdrop\b/.test(trimmed)) return (mobile ? toSheet(trimmed) : trimmed) + "\n";
  const wrap = mobile ? wrapMobile : wrapShell;
  const hasApp = /^<div\s+class=["'][^"']*\bapp\b/.test(trimmed);
  if (!hasApp) return wrap(S, s, trimmed, shellFor(S, s, o.concept));
  if (o.reshell) return wrap(S, s, stripShell(trimmed), shellFor(S, s, o.concept));
  return trimmed + "\n";
}
module.exports = { expandFragment, expandParts, warnings };

// ---------- CLI ----------
if (require.main === module) {
  const args = process.argv.slice(2), runDir = args.find((x) => !x.startsWith("--")), reshell = args.includes("--reshell");
  if (!runDir) { console.error("usage: node scripts/expand.js runs/<project> [--reshell]"); process.exit(2); }
  const S = JSON.parse(fs.readFileSync(path.join(runDir, "screens.json"), "utf8"));
  const bySlug = new Map((S.screens || []).map((s) => [s.slug, s]));
  const jobs = [];
  for (const s of S.screens || []) jobs.push({ file: path.join(runDir, s.file || `screens/${s.slug}.html`), s });
  for (const c of S.concepts || []) for (const slug of c.screens || []) if (bySlug.has(slug)) jobs.push({ file: path.join(runDir, "concepts", c.id, slug + ".html"), s: bySlug.get(slug), concept: c.id });
  let n = 0, before = 0, after = 0, fails = 0;
  for (const j of jobs) {
    if (!fs.existsSync(j.file)) continue;
    const src = fs.readFileSync(j.file, "utf8");
    try {
      warnings.length = 0;
      const out = expandFragment(S, j.s, src, { concept: j.concept, reshell });
      for (const w of new Set(warnings)) console.log(`[WARN] ${path.relative(runDir, j.file)}: ${w}`);
      if (out !== src) { fs.writeFileSync(j.file, out); n++; before += src.length; after += out.length; }
    } catch (e) { fails++; console.log(`[FAIL] ${path.relative(runDir, j.file)}: ${e.message}`); }
  }
  console.log(`[expand] ${n}개 펼침${n ? ` (쓴 글자 ${before.toLocaleString()} → 펼친 글자 ${after.toLocaleString()})` : ""}${fails ? ` · FAIL ${fails}` : ""}`);
  process.exit(fails ? 1 : 0);
}
