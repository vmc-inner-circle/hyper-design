/**
 * looks.js — 분위기(look)와 버튼 색(swatch)을 CSS 토큰으로 바꾼다. build.js·lint.js가 함께 쓴다.
 *
 * screens.json:
 *   "looks": [
 *     { "id": "cream", "name": "따뜻한 크림", "why": "가족이 함께 보는 화면이라 포근한 톤",
 *       "mode": "light", "bg": "#FBF8F3", "ink": "#1F1B16", "shape": "round",
 *       "swatches": [ { "id": "terracotta", "name": "테라코타", "hex": "#D9562B" }, … 5개 ] }
 *   ]   ← 3~5개. PRD마다 메인이 정한다 (references/prd-to-screens.md §6)
 *   "theme": "<look id>", "toggles": { "type": "large", "swatch": "<swatch id>" }
 *   look에 "font": "<FONTS id>" — 분위기마다 글꼴 세트 하나(없으면 pretendard)
 *
 * 메인은 배경(bg)·글자(ink)·모양(shape)·버튼 색(hex)·글꼴(font)만 정한다. 표면·테두리·흐린 글자·눌림색·연한 강조는 여기서 계산한다.
 * 디자이너 기준으로 자동 보정한다(사용자 선택지를 늘리지 않는다):
 *   - 본문 글자는 순수 검정·순수 흰색이 아니게: 바탕과의 대비가 글꼴 세트의 inkMax를 넘으면 바탕 쪽으로 섞어 눌러 준다(#000 → #2E2E2E 수준)
 *   - 버튼 색은 형광처럼 쨍하지 않게: OKLCH 채도(chroma)를 상한까지 낮춘다(밝기·색상은 그대로)
 *   - 상태색(완료·주의·오류·안내)도 원색 대신 차분한 색(흙빛 빨강 등)을 바탕에 맞춰 섞는다
 * looks가 없으면 DEFAULT_LOOKS(예전 A/B/C 테마와 같은 값)를 쓴다.
 */

// ---------- 글꼴 세트 — 글꼴마다 어울리는 굵기·자간·줄간격·글자 진하기가 다르다 ----------
// css: 불러올 웹 글꼴. sans: 본문 글꼴, head: 제목 글꼴(없으면 sans). w*: 굵기, ls*: 자간, lh*: 줄간격,
// inkMax: 본문 글자와 바탕의 최대 대비(가는 글꼴일수록 조금 더 진하게 둔다)
const PRETENDARD_CSS = "https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css";
const FALLBACK = '-apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Noto Sans KR", system-ui, sans-serif';
const FONTS = {
  pretendard: { name: "프리텐다드", why: "반듯하고 중립적이라 어떤 서비스에도 무난해요", css: [PRETENDARD_CSS],
    sans: `Pretendard, ${FALLBACK}`, wBody: 400, wStrong: 600, wHead: 700, lsHead: "-0.02em", lsBody: "-0.01em", lhHead: 1.35, lhBody: 1.55, inkMax: 14 },
  suit: { name: "수트", why: "글자 폭이 고르고 또렷해 숫자·정보가 많은 화면에 좋아요", css: ["https://cdn.jsdelivr.net/gh/sun-typeface/SUIT@2/fonts/static/woff2/SUIT.css"],
    sans: `SUIT, Pretendard, ${FALLBACK}`, wBody: 400, wStrong: 600, wHead: 800, lsHead: "-0.015em", lsBody: "0em", lhHead: 1.35, lhBody: 1.6, inkMax: 13.5 },
  "nanum-square-round": { name: "나눔스퀘어라운드", why: "둥글고 친근해 생활·가족·아이 서비스에 어울려요", css: ["https://cdn.jsdelivr.net/gh/innks/NanumSquareRound@master/nanumsquareround.min.css"],
    sans: `NanumSquareRound, Pretendard, ${FALLBACK}`, wBody: 400, wStrong: 700, wHead: 800, lsHead: "-0.01em", lsBody: "0em", lhHead: 1.4, lhBody: 1.65, inkMax: 15 },
  "ibm-plex": { name: "IBM 플렉스", why: "곧고 단정해 업무 도구·관리 화면에 어울려요", css: ["https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@400;500;600;700&display=swap"],
    sans: `"IBM Plex Sans KR", Pretendard, ${FALLBACK}`, wBody: 400, wStrong: 500, wHead: 600, lsHead: "-0.01em", lsBody: "-0.005em", lhHead: 1.4, lhBody: 1.6, inkMax: 14 },
  "serif-title": { name: "명조 제목", why: "제목만 명조라 기록·읽을거리·감성 서비스에 어울려요",
    css: ["https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@500;700&display=swap", PRETENDARD_CSS],
    sans: `Pretendard, ${FALLBACK}`, head: `"Noto Serif KR", "Nanum Myeongjo", serif`, wBody: 400, wStrong: 600, wHead: 700, lsHead: "-0.01em", lsBody: "-0.01em", lhHead: 1.4, lhBody: 1.6, inkMax: 13.5 },
};
const fontOf = (L) => FONTS[L && L.font] || FONTS.pretendard;
/** 분위기들이 쓰는 웹 글꼴 CSS 주소 (중복 없이) */
function fontLinks(looks) { return [...new Set(looks.flatMap((L) => fontOf(L).css))]; }

const DEFAULT_LOOKS = [
  { id: "a", name: "깔끔한 흰색", why: "어떤 서비스에도 무난한 밝고 중립적인 톤", mode: "light", bg: "#F7F7F8", ink: "#111827", shape: "soft", font: "pretendard",
    swatches: [
      { id: "blue", name: "파랑", hex: "#2563EB" }, { id: "orange", name: "주황", hex: "#EA580C" }, { id: "green", name: "초록", hex: "#15803D" },
      { id: "violet", name: "보라", hex: "#7C3AED" }, { id: "ink", name: "먹색", hex: "#1F2937" }] },
  { id: "b", name: "따뜻한 크림", why: "생활·가족·기록처럼 포근해야 하는 서비스에 어울리는 톤", mode: "light", bg: "#FBF8F3", ink: "#1F1B16", shape: "round", font: "nanum-square-round",
    swatches: [
      { id: "terracotta", name: "테라코타", hex: "#D9562B" }, { id: "teal", name: "청록", hex: "#0F9D8A" }, { id: "olive", name: "올리브", hex: "#5B7A1F" },
      { id: "brick", name: "벽돌색", hex: "#A1432A" }, { id: "cocoa", name: "코코아", hex: "#4A3B2F" }] },
  { id: "c", name: "차분한 밤", why: "밤에 보거나 도구처럼 오래 켜 두는 서비스에 어울리는 어두운 톤", mode: "dark", bg: "#0F1115", ink: "#E6E8EC", shape: "sharp", font: "suit",
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

// ---------- OKLCH (채도만 낮추고 밝기·색상은 지킨다) ----------
const toLin = (v) => { v /= 255; return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
const fromLin = (v) => 255 * (v <= 0.0031308 ? 12.92 * v : 1.055 * Math.pow(v, 1 / 2.4) - 0.055);
function hex2oklch(h) {
  const [r, g, b] = hex2rgb(h).map(toLin);
  const l = Math.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b);
  const m = Math.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b);
  const s = Math.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b);
  const L = 0.2104542553 * l + 0.793617785 * m - 0.0040720468 * s;
  const A = 1.9779984951 * l - 2.428592205 * m + 0.4505937099 * s;
  const B = 0.0259040371 * l + 0.7827717662 * m - 0.808675766 * s;
  return [L, Math.hypot(A, B), Math.atan2(B, A)];
}
function oklch2hex([L, C, H]) {
  const A = C * Math.cos(H), B = C * Math.sin(H);
  const l = Math.pow(L + 0.3963377774 * A + 0.2158037573 * B, 3);
  const m = Math.pow(L - 0.1055613458 * A - 0.0638541728 * B, 3);
  const s = Math.pow(L - 0.0894841775 * A - 1.291485548 * B, 3);
  return rgb2hex([4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
    -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
    -0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s].map(fromLin));
}
const CHROMA_MAX = { light: 0.165, dark: 0.14 };
/** 버튼 색이 형광처럼 쨍하면 채도만 상한까지 낮춘다 */
function calmHex(h, dark) {
  const c = hex2oklch(h), max = CHROMA_MAX[dark ? "dark" : "light"];
  return c[1] <= max ? String(h).toUpperCase() : oklch2hex([c[0], max, c[2]]);
}
/** 본문 글자색: 바탕과 대비가 max를 넘으면(순수 검정·순수 흰색) 바탕 쪽으로 섞어 눌러 준다 */
function softInk(ink, bg, max) {
  if (contrast(ink, bg) <= max) return String(ink).toUpperCase();
  let lo = 0, hi = 0.6;
  for (let i = 0; i < 24; i++) { const t = (lo + hi) / 2; if (contrast(mix(ink, bg, t), bg) > max) lo = t; else hi = t; }
  return mix(ink, bg, hi);
}

// 상태색 — 원색 대신 차분한 색. 연한 바탕은 그 분위기의 바탕에 섞어 만든다
const STATUS_HEX = {
  light: { success: "#2F7D4F", warning: "#B7791F", danger: "#C2412B", info: "#3A6EA5" },
  dark: { success: "#5CC08A", warning: "#E3B341", danger: "#F08A74", info: "#7FAEE0" },
};
function statusTokens(bg, dark) {
  const t = {}, P = STATUS_HEX[dark ? "dark" : "light"];
  for (const [k, c] of Object.entries(P)) {
    t[`--c-${k}`] = c;
    t[`--c-${k}-soft`] = mix(bg, c, dark ? 0.16 : 0.12);
    t[`--c-${k}-soft-fg`] = dark ? mix(c, "#FFFFFF", 0.4) : mix(c, "#000000", 0.32);
  }
  t["--c-danger-hover"] = dark ? mix(P.danger, "#FFFFFF", 0.16) : mix(P.danger, "#000000", 0.12);
  t["--c-danger-active"] = dark ? P.danger : mix(P.danger, "#000000", 0.24);
  return t;
}
const SHAPE = {
  soft: { "--r-card": "var(--r-lg)", "--r-control": "var(--r-md)", "--shadow-card": "var(--shadow-sm)", "--border-card": "1px solid var(--c-border)" },
  round: { "--r-card": "var(--r-xl)", "--r-control": "var(--r-pill)", "--shadow-card": "var(--shadow-md)", "--border-card": "1px solid transparent" },
  sharp: { "--r-card": "var(--r-sm)", "--r-control": "var(--r-sm)", "--shadow-card": "none", "--border-card": "1px solid var(--c-border)" },
};

/** 글꼴 세트 → 글꼴·굵기·자간·줄간격 토큰 */
function fontTokens(L) {
  const f = fontOf(L);
  return { "--font-sans": f.sans, "--font-head": f.head || "var(--font-sans)",
    "--fw-body": String(f.wBody), "--fw-semibold": String(f.wStrong), "--fw-head": String(f.wHead), "--fw-bold": String(Math.max(700, f.wHead)),
    "--ls-head": f.lsHead, "--ls-body": f.lsBody, "--lh-tight": String(f.lhHead), "--lh-normal": String(f.lhBody) };
}
/** 본문 글자색 — 글꼴 세트의 inkMax로 보정한 값 */
function inkOf(L) { return softInk(L.ink, L.bg, L.mode === "dark" ? Math.min(fontOf(L).inkMax, 14) : fontOf(L).inkMax); }

/** 배경·글자·모양·글꼴 → 바탕 토큰 */
function lookTokens(L) {
  const dark = L.mode === "dark", bg = L.bg, ink = inkOf(L);
  const t = dark ? {
    "--c-bg": bg, "--c-surface": mix(bg, "#FFFFFF", 0.04), "--c-surface-2": mix(bg, "#FFFFFF", 0.08), "--c-surface-3": mix(bg, "#FFFFFF", 0.12),
    "--c-border": mix(bg, "#FFFFFF", 0.14), "--c-border-strong": mix(bg, "#FFFFFF", 0.22),
    "--c-text": ink, "--c-text-2": mix(ink, bg, 0.3), "--c-text-muted": mix(ink, bg, 0.52), "--c-text-inverse": bg,
    "--c-overlay": "rgba(0, 0, 0, .6)", "--c-skeleton": mix(bg, "#FFFFFF", 0.12),
  } : {
    "--c-bg": bg, "--c-surface": mix(bg, "#FFFFFF", 0.75), "--c-surface-2": mix(bg, ink, 0.035), "--c-surface-3": mix(bg, ink, 0.07),
    "--c-border": mix(bg, ink, 0.11), "--c-border-strong": mix(bg, ink, 0.2),
    "--c-text": ink, "--c-text-2": mix(ink, bg, 0.36), "--c-text-muted": mix(ink, bg, 0.54), "--c-text-inverse": "#FFFFFF",
    "--c-overlay": "rgba(17, 24, 39, .45)", "--c-skeleton": mix(bg, ink, 0.07),
  };
  return Object.assign(t, statusTokens(bg, dark), SHAPE[L.shape] || SHAPE.soft, fontTokens(L));
}
/** 버튼 색 → 강조 토큰 (눌림·연한 배경·위 글자색까지) */
function swatchTokens(L, sw) {
  const dark = L.mode === "dark", p = calmHex(sw.hex, dark);
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

module.exports = { DEFAULT_LOOKS, FONTS, fontOf, fontLinks, fontTokens, inkOf, calmHex, getLooks, looksCss, lookTokens, swatchTokens, resolveSwatch, contrast, mix, hex2rgb };
