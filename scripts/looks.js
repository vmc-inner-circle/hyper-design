/**
 * looks.js — 분위기(look)와 버튼 색(swatch)을 CSS 토큰으로 바꾼다. build.js·lint.js가 함께 쓴다.
 *
 * screens.json:
 *   "looks": [
 *     { "id": "cream", "name": "따뜻한 크림", "why": "가족이 함께 보는 화면이라 포근한 톤",
 *       "mode": "light", "bg": "#FBF8F3", "ink": "#1F1B16", "shape": "round",
 *       "swatches": [ { "id": "terracotta", "name": "테라코타", "hex": "#D9562B" }, … 5개 ] }
 *   ]   ← 3개. PRD마다 메인이 정한다 (references/prd-to-screens.md §6)
 *   "theme": "<look id>", "toggles": { "type": "large", "swatch": "<swatch id>" }
 *
 * 메인은 배경(bg)·글자(ink)·모양(shape)·버튼 색(hex)만 정한다. 표면·테두리·흐린 글자·눌림색·연한 강조는 여기서 계산한다.
 * looks가 없으면 DEFAULT_LOOKS(예전 A/B/C 테마와 같은 값)를 쓴다.
 */

const DEFAULT_LOOKS = [
  { id: "a", name: "깔끔한 흰색", why: "어떤 서비스에도 무난한 밝고 중립적인 톤", mode: "light", bg: "#F7F7F8", ink: "#111827", shape: "soft",
    swatches: [
      { id: "blue", name: "파랑", hex: "#2563EB" }, { id: "orange", name: "주황", hex: "#EA580C" }, { id: "green", name: "초록", hex: "#15803D" },
      { id: "violet", name: "보라", hex: "#7C3AED" }, { id: "ink", name: "먹색", hex: "#1F2937" }] },
  { id: "b", name: "따뜻한 크림", why: "생활·가족·기록처럼 포근해야 하는 서비스에 어울리는 톤", mode: "light", bg: "#FBF8F3", ink: "#1F1B16", shape: "round",
    swatches: [
      { id: "terracotta", name: "테라코타", hex: "#D9562B" }, { id: "teal", name: "청록", hex: "#0F9D8A" }, { id: "olive", name: "올리브", hex: "#5B7A1F" },
      { id: "brick", name: "벽돌색", hex: "#A1432A" }, { id: "cocoa", name: "코코아", hex: "#4A3B2F" }] },
  { id: "c", name: "차분한 밤", why: "밤에 보거나 도구처럼 오래 켜 두는 서비스에 어울리는 어두운 톤", mode: "dark", bg: "#0F1115", ink: "#E6E8EC", shape: "sharp",
    swatches: [
      { id: "mint", name: "민트", hex: "#2DD4BF" }, { id: "pink", name: "분홍", hex: "#F472B6" }, { id: "sky", name: "하늘", hex: "#60A5FA" },
      { id: "yellow", name: "노랑", hex: "#FACC15" }, { id: "white", name: "흰색", hex: "#E5E7EB" }] },
];

// ---------- 색 계산 ----------
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
function hex2rgb(h) {
  const m = /^#?([0-9a-f]{6})$/i.exec(String(h || "").trim());
  if (!m) throw new Error(`색 형식 오류: ${h} (#RRGGBB)`);
  const n = parseInt(m[1], 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}
const rgb2hex = (c) => "#" + c.map((v) => clamp(Math.round(v), 0, 255).toString(16).padStart(2, "0")).join("").toUpperCase();
/** a와 b를 섞는다. t = b의 비율(0~1) */
const mix = (a, b, t) => { const x = hex2rgb(a), y = hex2rgb(b); return rgb2hex(x.map((v, i) => v + (y[i] - v) * t)); };
function lum(h) {
  return hex2rgb(h).map((v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); })
    .reduce((s, v, i) => s + v * [0.2126, 0.7152, 0.0722][i], 0);
}
const contrast = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); };

const STATUS = {
  light: {
    "--c-success": "#16A34A", "--c-success-soft": "#E7F7EC", "--c-success-soft-fg": "#14532D",
    "--c-warning": "#D97706", "--c-warning-soft": "#FEF3E2", "--c-warning-soft-fg": "#92400E",
    "--c-danger": "#DC2626", "--c-danger-hover": "#B91C1C", "--c-danger-active": "#991B1B", "--c-danger-soft": "#FDECEC", "--c-danger-soft-fg": "#991B1B",
    "--c-info": "#0284C7", "--c-info-soft": "#E6F4FB", "--c-info-soft-fg": "#075985",
  },
  dark: {
    "--c-success": "#4ADE80", "--c-success-soft": "rgba(74, 222, 128, .14)", "--c-success-soft-fg": "#BBF7D0",
    "--c-warning": "#FBBF24", "--c-warning-soft": "rgba(251, 191, 36, .14)", "--c-warning-soft-fg": "#FDE68A",
    "--c-danger": "#F87171", "--c-danger-hover": "#FCA5A5", "--c-danger-active": "#F87171", "--c-danger-soft": "rgba(248, 113, 113, .14)", "--c-danger-soft-fg": "#FECACA",
    "--c-info": "#60A5FA", "--c-info-soft": "rgba(96, 165, 250, .14)", "--c-info-soft-fg": "#BFDBFE",
  },
};
const SHAPE = {
  soft: { "--r-card": "var(--r-lg)", "--r-control": "var(--r-md)", "--shadow-card": "var(--shadow-sm)", "--border-card": "1px solid var(--c-border)" },
  round: { "--r-card": "var(--r-xl)", "--r-control": "var(--r-pill)", "--shadow-card": "var(--shadow-md)", "--border-card": "1px solid transparent" },
  sharp: { "--r-card": "var(--r-sm)", "--r-control": "var(--r-sm)", "--shadow-card": "none", "--border-card": "1px solid var(--c-border)" },
};

/** 배경·글자·모양 → 바탕 토큰 */
function lookTokens(L) {
  const dark = L.mode === "dark", bg = L.bg, ink = L.ink;
  const t = dark ? {
    "--c-bg": bg, "--c-surface": mix(bg, "#FFFFFF", 0.04), "--c-surface-2": mix(bg, "#FFFFFF", 0.08), "--c-surface-3": mix(bg, "#FFFFFF", 0.12),
    "--c-border": mix(bg, "#FFFFFF", 0.14), "--c-border-strong": mix(bg, "#FFFFFF", 0.22),
    "--c-text": ink, "--c-text-2": mix(ink, bg, 0.3), "--c-text-muted": mix(ink, bg, 0.52), "--c-text-inverse": bg,
    "--c-overlay": "rgba(0, 0, 0, .6)", "--c-skeleton": mix(bg, "#FFFFFF", 0.12),
  } : {
    "--c-bg": bg, "--c-surface": mix(bg, "#FFFFFF", 0.75), "--c-surface-2": mix(bg, ink, 0.035), "--c-surface-3": mix(bg, ink, 0.07),
    "--c-border": mix(bg, ink, 0.11), "--c-border-strong": mix(bg, ink, 0.2),
    "--c-text": ink, "--c-text-2": mix(ink, bg, 0.3), "--c-text-muted": mix(ink, bg, 0.45), "--c-text-inverse": "#FFFFFF",
    "--c-overlay": "rgba(17, 24, 39, .45)", "--c-skeleton": mix(bg, ink, 0.07),
  };
  return Object.assign(t, STATUS[dark ? "dark" : "light"], SHAPE[L.shape] || SHAPE.soft);
}
/** 버튼 색 → 강조 토큰 (눌림·연한 배경·위 글자색까지) */
function swatchTokens(L, sw) {
  const dark = L.mode === "dark", p = sw.hex;
  const fg = contrast(p, "#FFFFFF") >= 3 ? "#FFFFFF" : (dark ? L.bg : "#111827");
  return {
    "--c-primary": p,
    "--c-primary-hover": dark ? mix(p, "#FFFFFF", 0.16) : mix(p, "#000000", 0.12),
    "--c-primary-active": dark ? mix(p, "#000000", 0.12) : mix(p, "#000000", 0.24),
    "--c-primary-fg": fg,
    "--c-primary-soft": dark ? mix(L.bg, p, 0.18) : mix(L.bg, p, 0.12),
    "--c-primary-soft-fg": dark ? mix(p, "#FFFFFF", 0.45) : mix(p, "#000000", 0.35),
    "--c-accent": "var(--c-primary)", "--c-accent-soft": "var(--c-primary-soft)", "--c-accent-soft-fg": "var(--c-primary-soft-fg)",
    "--c-focus": p,
  };
}
const block = (sel, vars) => `${sel} {\n${Object.entries(vars).map(([k, v]) => `  ${k}: ${v};`).join("\n")}\n}`;
function looksCss(looks) {
  const out = ["/* looks — scripts/looks.js가 screens.json의 looks에서 계산한 토큰 */"];
  for (const L of looks) {
    out.push(block(`[data-theme="${L.id}"]`, Object.assign(lookTokens(L), swatchTokens(L, L.swatches[0]))));
    for (const sw of L.swatches) out.push(block(`[data-theme="${L.id}"][data-swatch="${sw.id}"]`, swatchTokens(L, sw)));
  }
  return out.join("\n");
}
function getLooks(S) { return Array.isArray(S.looks) && S.looks.length ? S.looks : DEFAULT_LOOKS; }
/** 예전 값(calm/vivid)도 받아서 그 분위기의 버튼 색 id로 */
function resolveSwatch(L, v) {
  if (!L || !L.swatches || !L.swatches.length) return null;
  if (L.swatches.some((s) => s.id === v)) return v;
  if (v === "vivid" && L.swatches[1]) return L.swatches[1].id;
  return L.swatches[0].id;
}

module.exports = { DEFAULT_LOOKS, getLooks, looksCss, lookTokens, swatchTokens, resolveSwatch, contrast, mix, hex2rgb };
