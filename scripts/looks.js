/**
 * looks.js — 분위기(look)와 버튼 색(swatch)을 CSS 토큰으로 바꾼다. build.js·lint.js가 함께 쓴다.
 *
 * screens.json:
 *   "looks": [
 *     { "id": "cream", "name": "따뜻한 크림", "why": "가족이 함께 보는 화면이라 포근한 톤",
 *       "mode": "light", "bg": "#FBF8F3", "ink": "#1F1B16", "shape": "round", "font": "nanum-square-round",
 *       "palette": { "brand": { "name": "테라코타", "hex": "#D9562B" }, "support": { … }, "accent": { … } },
 *       "swatches": [ { "id": "teal", "name": "청록", "hex": "#0F9D8A" }, … 대안 4개 ] }   ← 대표색은 palette.brand 한 칸(버튼 색 첫 번째로 붙인다)
 *   ]   ← 3~5개. PRD마다 메인이 정한다 (references/prd-to-screens.md §6)
 *   "theme": "<look id>", "toggles": { "type": "large", "swatch": "<swatch id> | brand" }
 *   look.font = 글꼴 세트 id(FONT_ALIAS) — 글꼴의 주인은 이 한 칸. look.type은 제목 성격(heading · ratio)만, 밀도는 concepts[].density
 *
 * 메인은 배경(bg)·글자(ink)·모양(shape)·역할 색(palette)·글꼴 세트(font)만 정한다. 표면·테두리·흐린 글자·눌림색·옅은 면은 여기서 계산한다.
 * 디자이너 기준으로 자동 보정한다(사용자 선택지를 늘리지 않는다) — 보정 뒤에도 KRDS 대비(글자 4.5 · 아이콘 3)를 지킨다(lookPairs):
 *   - 본문 글자는 순수 검정·순수 흰색이 아니게: 바탕과의 대비가 글꼴의 inkMax를 넘으면 바탕 쪽으로 섞어 눌러 준다(#000 → #2E2E2E 수준)
 *   - 버튼 색은 형광처럼 쨍하지 않게: OKLCH 채도(chroma)만 상한까지 낮춘다(밝기·색상은 그대로). 버튼 글자가 4.5 미만이면 면을 한 단계씩 옮긴다
 *   - 상태색(완료·주의·오류·안내)은 원색 대신 차분한 색, 분위기와 상관없이 고정(KRDS System). 옅은 면은 그 바탕에 섞는다(투명도 대신)
 * 굵기 · 줄 간격 · 자간의 바닥은 base.css(KRDS 본문 400/700 · 150% · 자간 0). 글꼴 세트는 그 위에서 제목 굵기 · 제목 줄 간격만 정한다.
 * looks가 없으면 DEFAULT_LOOKS(예전 A/B/C 테마와 같은 값)를 쓴다.
 */

// ---------- 글꼴 — 표 하나: 글자꼴(FONTS)과 글꼴 세트(FONT_ALIAS) ----------
// FONTS: 글자꼴 하나 = 이름 · CSS font-family · 웹 글꼴 주소 · inkMax(본문 글자와 바탕의 최대 대비 — 가는 글꼴일수록 조금 더 진하게) · gothic.
// 본문은 고딕만(KRDS 본문 고딕) — 명조는 제목에만.
const PRETENDARD_CSS = "https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css";
const FALLBACK = '-apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Noto Sans KR", system-ui, sans-serif';
const FONTS = {
  sans: { name: "프리텐다드", stack: `Pretendard, ${FALLBACK}`, css: PRETENDARD_CSS, inkMax: 14, gothic: true },   // 중립 고딕
  suit: { name: "수트", stack: `SUIT, Pretendard, ${FALLBACK}`, css: "https://cdn.jsdelivr.net/gh/sun-typeface/SUIT@2/fonts/static/woff2/SUIT.css", inkMax: 13.5, gothic: true },   // 폭이 고른 고딕
  plex: { name: "IBM 플렉스", stack: `"IBM Plex Sans KR", Pretendard, ${FALLBACK}`, css: "https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@400;600;700&display=swap", inkMax: 14, gothic: true },   // 곧고 단정한 고딕
  round: { name: "나눔스퀘어라운드", stack: `NanumSquareRound, Pretendard, ${FALLBACK}`, css: "https://cdn.jsdelivr.net/gh/innks/NanumSquareRound@master/nanumsquareround.min.css", inkMax: 15, gothic: true },   // 둥근 고딕
  soft: { name: "고운돋움", stack: `"Gowun Dodum", Pretendard, ${FALLBACK}`, css: "https://fonts.googleapis.com/css2?family=Gowun+Dodum&display=swap", inkMax: 14, gothic: true },   // 부드러운 고딕
  serif: { name: "본명조", stack: '"Noto Serif KR", "AppleMyungjo", "Nanum Myeongjo", serif', css: "https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;700&display=swap", inkMax: 13.5, gothic: false },   // 단정한 명조
  "serif-soft": { name: "고운바탕", stack: '"Gowun Batang", "Noto Serif KR", "AppleMyungjo", serif', css: "https://fonts.googleapis.com/css2?family=Gowun+Batang:wght@400;700&display=swap", inkMax: 13.5, gothic: false },   // 부드러운 명조
};
// FONT_ALIAS: 글꼴 세트(look.font 값) → 본문 글자꼴 · 제목 글자꼴 · 제목 굵기(wHead) · 제목 줄 간격(lhHead) · 제목 자간(tracking, 있을 때만).
// 글꼴마다 어울리는 제목 굵기 · 줄 간격이 다르다 — 이 둘만 세트가 정하고, 본문은 KRDS 바닥선을 따른다.
// 제목 자간은 base.css KRDS 값(--tracking-krds)이 바닥선 — 세트가 정해도 그보다 좁히지 못한다(fontTokens가 max로 묶는다).
const FONT_ALIAS = {
  pretendard: { name: "프리텐다드", why: "반듯하고 중립적이라 어떤 서비스에도 무난해요", font: "sans", wHead: 700, lhHead: 1.35 },
  suit: { name: "수트", why: "글자 폭이 고르고 또렷해 숫자·정보가 많은 화면에 좋아요", font: "suit", wHead: 800, lhHead: 1.35 },
  "nanum-square-round": { name: "나눔스퀘어라운드", why: "둥글고 친근해 생활·가족·아이 서비스에 어울려요", font: "round", wHead: 800, lhHead: 1.4 },
  "ibm-plex": { name: "IBM 플렉스", why: "곧고 단정해 업무 도구·관리 화면에 어울려요", font: "plex", wHead: 600, lhHead: 1.4 },
  "serif-title": { name: "명조 제목", why: "제목만 명조라 기록·읽을거리·감성 서비스에 어울려요", font: "sans", heading: "serif", wHead: 700, lhHead: 1.4 },
};
/** 분위기의 글꼴 → { name, body, heading, wHead?, lhHead? }. look.font(세트 id)가 주인 — 없을 때만 옛 칸 type.font · type.heading(글자꼴 id)을 읽는다 */
function resolveFont(L) {
  const T = (L && L.type) || {};
  const set = FONT_ALIAS[L && L.font] || (!(L && L.font) && FONT_ALIAS[T.font]);
  if (set) return { name: set.name, body: set.font, heading: set.heading || null, wHead: set.wHead, lhHead: set.lhHead, tracking: set.tracking };
  const face = FONTS[L && L.font] ? L.font : FONTS[T.font] ? T.font : "sans";
  const body = FONTS[face].gothic ? face : "sans";   // 본문은 고딕만
  const heading = FONTS[T.heading] ? T.heading : (FONTS[face].gothic ? null : face);
  return { name: FONTS[heading || body].name, body, heading };
}
/** 글꼴 세트 요약 — build.js가 보드에 이름을 보인다 */
function fontOf(L) {
  const r = resolveFont(L), faces = [r.body, r.heading].filter(Boolean);
  return Object.assign(r, { css: [...new Set(faces.map((k) => FONTS[k].css))], inkMax: Math.min(...faces.map((k) => FONTS[k].inkMax)) });
}
/** 분위기들이 쓰는 웹 글꼴 CSS 주소 (중복 없이) */
function fontLinks(looks) { return [...new Set((looks || []).flatMap((L) => fontOf(L).css))]; }

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
/** 본문 글자색: 바탕과 대비가 max를 넘으면(순수 검정·순수 흰색) 바탕 쪽으로 섞어 눌러 준다 — max는 4.5보다 훨씬 커서 KRDS 대비는 그대로 */
function softInk(ink, bg, max) {
  if (contrast(ink, bg) <= max) return String(ink).toUpperCase();
  let lo = 0, hi = 0.6;
  for (let i = 0; i < 24; i++) { const t = (lo + hi) / 2; if (contrast(mix(ink, bg, t), bg) > max) lo = t; else hi = t; }
  return mix(ink, bg, hi);
}
/** 흐린 글자 — 바탕 · 면 둘 다에서 대비 4.5를 지키는 한에서 가장 흐리게(최대 t) */
function mutedInk(ink, bg, surface, t) {
  while (t > 0 && (contrast(mix(ink, bg, t), bg) < 4.5 || contrast(mix(ink, bg, t), surface) < 4.5)) t -= 0.01;
  return mix(ink, bg, Math.max(t, 0));
}
/** 진한 면 위 글자 — 흰 글자가 어울리는 면(대비 3 이상)은 흰 글자로 두고 면을 한 단계씩 진하게, 밝은 면(노랑 · 민트)은 어두운 글자로 두고 면을 밝게 —
 *  대비 4.5가 될 때까지 (KRDS: 글자를 올리는 면은 4.5:1 단계로 옮긴다 — https://www.krds.go.kr/html/site/style/style_02.html) */
function readable(hex, dark, bg) {
  const white = contrast(hex, "#FFFFFF") >= 3, fg = white ? "#FFFFFF" : (dark ? bg : "#111827");
  let h = hex;
  for (let i = 0; i < 12 && contrast(h, fg) < 4.5; i++) h = mix(h, white ? "#000000" : "#FFFFFF", 0.06);
  return { hex: h, fg };
}

// ---------- 역할 색 하나의 계산 — 대표색(primary) · support · accent · 상태색이 모두 이것을 쓴다 ----------
/** 옅은 면 위 글자: 대비 4.5가 될 때까지 진하게(밝은 바탕) / 밝게(어두운 바탕) */
function softFg(dark, hex, soft) {
  const to = dark ? "#FFFFFF" : "#000000";
  for (let t = 0.2; t <= 0.9; t += 0.05) { const c = mix(hex, to, t); if (contrast(c, soft) >= 4.5) return c; }
  return dark ? "#FFFFFF" : "#111111";
}
/** 진한 면 위 글자 — 흰 글자가 4.5 이상이면 흰 글자, 아니면 흰 글자와 어두운 글자 중 대비가 큰 쪽(주황 · 노랑 면은 어두운 글자) */
function solidFg(hex, dark, bg) {
  const ink = dark ? bg : "#111827", w = contrast(hex, "#FFFFFF");
  return w >= 4.5 || w >= contrast(hex, ink) ? "#FFFFFF" : ink;
}
/** 색 하나 → { hex, fg(진한 면 위 글자), soft(옅은 면), softFg(옅은 면 위 글자) }.
 *  이미 옅은 색(바탕과 대비 1.25 미만)이면 그 색을 그대로 면으로 — 또 섞으면 바탕과 같아진다 */
function roleColors(bg, dark, hex, t = dark ? 0.2 : 0.16) {
  const soft = contrast(bg, hex) < 1.25 ? hex : mix(bg, hex, t);
  return { hex, fg: solidFg(hex, dark, bg), soft, softFg: softFg(dark, hex, soft) };
}
const roleVars = (name, c) => ({ [`--c-${name}`]: c.hex, [`--c-${name}-fg`]: c.fg, [`--c-${name}-soft`]: c.soft, [`--c-${name}-soft-fg`]: c.softFg });

// 상태색 — 원색 대신 차분한 색, 분위기와 상관없이 고정. 옅은 면은 그 분위기의 바탕에 섞어 만든다
const STATUS_HEX = {
  light: { success: "#2F7D4F", warning: "#B7791F", danger: "#C2412B", info: "#3A6EA5" },
  dark: { success: "#5CC08A", warning: "#E3B341", danger: "#F08A74", info: "#7FAEE0" },
};
/** 아이콘 · 큰 글자 색: 바탕과 대비 3이 안 되면(색 바탕) 한 단계씩 진하게/밝게 — 흰 · 종이 바탕에서는 고정 값 그대로 */
function iconSafe(hex, bg, dark) {
  let h = hex;
  for (let i = 0; i < 12 && contrast(h, bg) < 3; i++) h = mix(h, dark ? "#FFFFFF" : "#000000", 0.08);
  return h;
}
function statusTokens(bg, dark) {
  const t = {}, P = {};
  for (const [k, c] of Object.entries(STATUS_HEX[dark ? "dark" : "light"])) P[k] = iconSafe(c, bg, dark);
  for (const [k, c] of Object.entries(P)) Object.assign(t, roleVars(k, roleColors(bg, dark, c, dark ? 0.16 : 0.12)));
  t["--c-danger-hover"] = dark ? mix(P.danger, "#FFFFFF", 0.16) : mix(P.danger, "#000000", 0.12);
  t["--c-danger-active"] = dark ? P.danger : mix(P.danger, "#000000", 0.24);
  return t;
}
const SHAPE = {
  soft: { "--r-card": "var(--r-lg)", "--r-control": "var(--r-md)", "--shadow-card": "var(--shadow-sm)", "--border-card": "1px solid var(--c-border)" },
  round: { "--r-card": "var(--r-xl)", "--r-control": "12px",   // KRDS 모서리: 버튼 · 입력은 알약 대신 12px — 알약은 칩 · 배지 · 원형 버튼만
    "--shadow-card": "var(--shadow-md)", "--border-card": "1px solid transparent" },
  sharp: { "--r-card": "var(--r-sm)", "--r-control": "var(--r-sm)", "--shadow-card": "none", "--border-card": "1px solid var(--c-border)" },
};

// ---------- 강조색(accent) 기준 — 색상 계열을 가리지 않는다 ----------
// accent는 '오늘 · 새로' 한두 곳에만 쓰고 배지 · 글자와 함께 나오므로, 상태색 계열(초록 · 주황 · 빨강)을 통째로 피하게 하면
// 대비 3을 넘는 남은 자리(보라 · 분홍)로 몰린다. 그래서 기준은 둘뿐: 대표색과 눈에 띄게 다른가(OKLab 거리) · 바탕 위에서 보이는가(대비 3).
const ACCENT_MIN_DIST = 0.1;   // OKLab 거리 — 같은 색의 밝기 차이만으로는 넘지 못하는 정도
function oklab(h) { const [L, C, H] = hex2oklch(h); return [L, C * Math.cos(H), C * Math.sin(H)]; }
const labDist = (a, b) => { const x = oklab(a), y = oklab(b); return Math.hypot(x[0] - y[0], x[1] - y[1], x[2] - y[2]); };
/** accent 후보 hex가 이 분위기에 맞는지 → { brandDistance, contrast, ok, why } — lint와 시험이 쓴다 */
function accentFit(L, hex) {
  const B = (L.palette && L.palette.brand && L.palette.brand.hex) || ((L.swatches || [])[0] || {}).hex;
  const brandDistance = B ? labDist(hex, B) : 1, c = contrast(hex, L.bg);
  const why = [brandDistance < ACCENT_MIN_DIST ? `대표색과 너무 비슷함(거리 ${brandDistance.toFixed(2)} < ${ACCENT_MIN_DIST})` : null, c < 3 ? `바탕 대비 ${c.toFixed(1)} < 3` : null].filter(Boolean);
  return { brandDistance, contrast: c, ok: !why.length, why };
}

// ---------- 바탕 톤 — 시안끼리 갈리는 첫째 축 (lint가 센다) ----------
// bg 색에서 계산한다: dark(어두운) · white(흰) · paper(따뜻한 옅은 종이) · tint(색이 옅게 든) · color(색 바탕)
const TONES = { white: "흰 바탕", paper: "종이색 바탕", tint: "옅은 색 바탕", color: "색 바탕", dark: "어두운 바탕" };
function toneOf(bg) {
  const [r, g, b] = hex2rgb(bg), L = lum(bg), d = Math.max(r, g, b) - Math.min(r, g, b);
  if (L < 0.2) return "dark";
  if (d <= 6 && L > 0.85) return "white";
  if (d > 40 || L < 0.6) return "color";
  if (r >= b && r - b >= 6) return "paper";
  return "tint";
}

// ---------- 글자 단계 · 밀도 ----------
// 글자 단계의 바닥은 base.css(KRDS 표: 본문 17 · 크게 19). look.type.ratio가 normal이 아니면 여기서 단계를 다시 계산한다(web만 — 모바일은 자기 단계).
const RATIOS = { tight: 1.125, normal: 1.2, wide: 1.25 };
const BASE_PX = { normal: 17, large: 19 };   // KRDS 본문 기본 17px(최소 16) · 크게 19px
const KRDS_STEPS = { normal: [13, 15, 17, 19, 24, 32, 40], large: [15, 17, 19, 24, 32, 40, 44] };
const STEPS = ["xs", "sm", "md", "lg", "xl", "2xl", "3xl"];
/** normal 비율은 KRDS 단계 그대로. tight·wide도 본문(md)은 KRDS 본문(17 · 크게 19)에 고정하고,
 *  위 단계는 본문 × 비율^단계 → 짝수 px · 바로 아래보다 2px 이상, 아래 단계는 본문에서 깎는다 → 짝수 px · 바로 위보다 2px 이상 작게 · 12px 이상 */
function typeScale(size, ratio) {
  const base = BASE_PX[size] || BASE_PX.normal;
  if (!RATIOS[ratio] || ratio === "normal") return KRDS_STEPS[size === "large" ? "large" : "normal"].slice();
  const at = (i) => Math.round((base * Math.pow(RATIOS[ratio], i - 2)) / 2) * 2, out = [];
  out[2] = base;
  for (let i = 3; i < STEPS.length; i++) out[i] = Math.max(at(i), out[i - 1] + 2);
  for (let i = 1; i >= 0; i--) out[i] = Math.max(Math.min(at(i), out[i + 1] - 2), 12);
  return out;
}
/** 이 분위기 · 글자 크기에서 허용되는 글자 크기(px) */
function allowedFontSizes(L, size) { return typeScale(size, ((L && L.type) || {}).ratio); }
// 밀도의 주인은 시안(concepts[].density) — 한국어 옛 값도 받는다. 빽빽함은 여백으로만: 본문 줄 간격은 어느 밀도든 KRDS 150% 이상
const DENSITY_ALIAS = { "넓게": "airy", "보통": "normal", "빽빽하게": "compact" };
const DENSITY = {
  compact: { "--gutter": "var(--sp-6)", "--lh-normal": "1.5" },
  normal: { "--gutter": "var(--sp-8)", "--lh-normal": "1.5" },
  airy: { "--gutter": "var(--sp-10)", "--lh-normal": "1.6" },
};
const densityOf = (L) => (DENSITY[L._density] ? L._density : DENSITY[(L.type || {}).density] ? L.type.density : "normal");   // _density = 이 분위기를 쓰는 시안의 밀도(getLooks), 없으면 옛 칸 type.density

/** 글꼴 세트 → 글꼴 · 제목 굵기 · 제목 줄 간격 토큰 (본문 굵기 · 줄 간격 · 자간은 base.css KRDS 값 그대로).
 *  세트가 제목 자간을 정했을 때만 --tracking-heading = max(KRDS 바닥선, 세트 값) */
function fontTokens(L) {
  const f = resolveFont(L);
  return Object.assign({ "--font-sans": FONTS[f.body].stack, "--font-heading": FONTS[f.heading || f.body].stack,
    "--fw-head": f.wHead ? String(f.wHead) : "var(--fw-bold)", "--lh-head": f.lhHead ? String(f.lhHead) : "var(--lh-tight)" },
    f.tracking ? { "--tracking-heading": `max(var(--tracking-krds), ${f.tracking})` } : {});
}
/** 본문 글자색 — 쓰는 글자꼴의 inkMax로 누른 값 */
function inkOf(L) { const max = fontOf(L).inkMax; return softInk(L.ink, L.bg, L.mode === "dark" ? Math.min(max, 14) : max); }

/** 배경·글자·모양·글꼴 → 바탕 토큰 */
function lookTokens(L) {
  const dark = L.mode === "dark", bg = L.bg, ink = inkOf(L);
  const surface = dark ? mix(bg, "#FFFFFF", 0.04) : mix(bg, "#FFFFFF", 0.75);
  const t = dark ? {
    "--c-bg": bg, "--c-surface": surface, "--c-surface-2": mix(bg, "#FFFFFF", 0.08), "--c-surface-3": mix(bg, "#FFFFFF", 0.12),
    "--c-border": mix(bg, "#FFFFFF", 0.14), "--c-border-strong": mix(bg, "#FFFFFF", 0.22),
    "--c-text": ink, "--c-text-2": mutedInk(ink, bg, surface, 0.3), "--c-text-muted": mutedInk(ink, bg, surface, 0.52), "--c-text-inverse": bg,
    "--c-overlay": "rgba(0, 0, 0, .6)", "--c-skeleton": mix(bg, "#FFFFFF", 0.12),
  } : {
    "--c-bg": bg, "--c-surface": surface, "--c-surface-2": mix(bg, ink, 0.035), "--c-surface-3": mix(bg, ink, 0.07),
    "--c-border": mix(bg, ink, 0.11), "--c-border-strong": mix(bg, ink, 0.2),
    "--c-text": ink, "--c-text-2": mutedInk(ink, bg, surface, 0.3), "--c-text-muted": mutedInk(ink, bg, surface, 0.54), "--c-text-inverse": "#FFFFFF",
    "--c-overlay": "rgba(17, 24, 39, .45)", "--c-skeleton": mix(bg, ink, 0.07),
  };
  return Object.assign(t, statusTokens(bg, dark), SHAPE[L.shape] || SHAPE.soft, fontTokens(L));
}
/** 버튼 색 → 강조 토큰 (눌림·옅은 면·위 글자색까지) */
function swatchTokens(L, sw) {
  const dark = L.mode === "dark", r = readable(calmHex(sw.hex, dark), dark, L.bg), p = r.hex;
  return {
    ...roleVars("primary", Object.assign(roleColors(L.bg, dark, p, dark ? 0.18 : 0.12), { fg: r.fg })),
    "--c-primary-hover": dark ? mix(p, "#FFFFFF", 0.16) : mix(p, "#000000", 0.12),
    "--c-primary-active": dark ? mix(p, "#000000", 0.12) : mix(p, "#000000", 0.24),
    "--c-focus": p,
    // 강조색이 따로 없을 때만 대표색 별칭 (있으면 토글로 대표색을 바꿔도 강조색은 그대로)
    ...(L.palette && L.palette.accent && L.palette.accent.hex ? {} : { "--c-accent": "var(--c-primary)", "--c-accent-fg": "var(--c-primary-fg)", "--c-accent-soft": "var(--c-primary-soft)", "--c-accent-soft-fg": "var(--c-primary-soft-fg)" }),
  };
}
// ---------- 역할 팔레트 ----------
// brand = 누르는 것·선택(--c-primary, 버튼 색 토글) · support = 누르지 않는 정보 면 · accent = '오늘·지금' 한두 곳 — 계산은 roleColors 하나
const roleTokens = (L, name, hex) => roleVars(name, roleColors(L.bg, L.mode === "dark", hex));
/** palette.support·accent → CSS 변수. 없으면 support는 대표색의 옅은 면, accent는 대표색 별칭(swatchTokens) */
function paletteTokens(L) {
  const P = L.palette || {}, v = {};
  if (P.support && P.support.hex) Object.assign(v, roleTokens(L, "support", P.support.hex));
  else Object.assign(v, { "--c-support": "var(--c-primary)", "--c-support-fg": "var(--c-primary-fg)", "--c-support-soft": "var(--c-primary-soft)", "--c-support-soft-fg": "var(--c-primary-soft-fg)" });
  if (P.accent && P.accent.hex) Object.assign(v, roleTokens(L, "accent", P.accent.hex));
  return v;
}
/** 밀도 → 가장자리 여백 · 본문 줄 간격 */
function densityTokens(L) { return Object.assign({}, DENSITY[densityOf(L)]); }
/** 글자 단계 — look.type.ratio가 normal이 아닐 때만 (normal은 base.css · toggles.css의 KRDS 단계 그대로).
 *  역할 크기도 다시 잇는다 — 보드 시안 틀(div[data-theme])처럼 html이 아닌 곳에 걸려도 새 단계를 따르게 */
const ROLE_SIZES = { "--fs-caption": "var(--fs-sm)", "--fs-body": "var(--fs-md)", "--fs-title": "var(--fs-xl)", "--fs-display": "var(--fs-3xl)" };
function typeTokens(L, size) {
  const r = (L.type || {}).ratio;
  return RATIOS[r] && r !== "normal" ? Object.assign(Object.fromEntries(STEPS.map((k, i) => [`--fs-${k}`, typeScale(size, r)[i] + "px"])), ROLE_SIZES) : {};
}

const block = (sel, vars) => `${sel} {\n${Object.entries(vars).map(([k, v]) => `  ${k}: ${v};`).join("\n")}\n}`;
function looksCss(looks) {
  const out = ["/* looks — scripts/looks.js가 screens.json의 looks에서 계산한 토큰 */"];
  for (const L of looks) {
    out.push(block(`[data-theme="${L.id}"]`, Object.assign(lookTokens(L), swatchTokens(L, L.swatches[0]), paletteTokens(L))));
    // 밀도 · 글자 단계는 web만 — 화면 전체(html)와 그 안의 시안 틀(보드 미리보기 div[data-theme])에. 모바일은 자기 여백 · 단계를 쓰고,
    // 밤 화면(.app[data-night])은 빌린 분위기의 색만 쓰므로 뺀다
    const web = (extra = "") => `[data-platform="web"][data-theme="${L.id}"]${extra}, [data-platform="web"] [data-theme="${L.id}"]${extra}:not([data-night])`;
    out.push(block(web(), Object.assign(densityTokens(L), typeTokens(L, "normal"))));
    const large = typeTokens(L, "large");
    if (Object.keys(large).length) out.push(block(web('[data-type="large"]'), large));
    for (const sw of L.swatches) out.push(block(`[data-theme="${L.id}"][data-swatch="${sw.id}"]`, swatchTokens(L, sw)));
  }
  return out.join("\n");
}

// ---------- 대비 — 자동 보정 뒤에도 KRDS 대비를 지키는지 (규칙 text-contrast: 글자 4.5 · 아이콘 3) ----------
const PAIRS = [   // [이름, 글자(앞), 바탕(뒤), 최소]
  ["본문", "--c-text", "--c-bg", 4.5], ["본문 · 면", "--c-text", "--c-surface", 4.5],
  ["보조 글자", "--c-text-2", "--c-bg", 4.5], ["보조 글자 · 면", "--c-text-2", "--c-surface", 4.5],
  ["흐린 글자", "--c-text-muted", "--c-bg", 4.5], ["흐린 글자 · 면", "--c-text-muted", "--c-surface", 4.5],
  ["주 버튼 글자", "--c-primary-fg", "--c-primary", 4.5], ["옅은 대표 면 글자", "--c-primary-soft-fg", "--c-primary-soft", 4.5],
  ...["support", "accent"].flatMap((k) => [[`${k} 면 글자`, `--c-${k}-soft-fg`, `--c-${k}-soft`, 4.5], [`${k} 진한 면 글자`, `--c-${k}-fg`, `--c-${k}`, 4.5]]),
  ...["success", "warning", "danger", "info"].flatMap((k) => [[`${k} 면 글자`, `--c-${k}-soft-fg`, `--c-${k}-soft`, 4.5], [`${k} 진한 면 글자`, `--c-${k}-fg`, `--c-${k}`, 4.5], [`${k} 아이콘`, `--c-${k}`, "--c-bg", 3]]),
];
/** 분위기 하나(getLooks가 돌려준 것)의 색 짝 대비 → [{ n, fg, bg, c, min }]. 버튼 색 sw를 주면 그 색으로(기본은 첫 번째) */
function lookPairs(L, sw = L.swatches[0]) {
  const v = Object.assign(lookTokens(L), swatchTokens(L, sw), paletteTokens(L));
  const hex = (k) => { let x = v[k]; for (let i = 0; i < 4 && /^var\(/.test(x || ""); i++) x = v[x.slice(4, -1)]; return /^#[0-9A-F]{6}$/i.test(x || "") ? x : null; };
  return PAIRS.map(([n, a, b, min]) => { const A = hex(a), B = hex(b); return A && B ? { n, fg: a, bg: b, c: contrast(A, B), min } : null; }).filter(Boolean);
}

// ---------- 분위기 목록 ----------
/** 버튼 색 후보 전체 = 대표색(palette.brand) + 대안(swatches) — 대표색은 한 칸에만 적는다.
 *  옛 실행물처럼 swatches 안에 brand와 같은 색이 있으면 그것을 첫 번째로 옮긴다(겹치지 않게). */
function swatchesOf(L) {
  const B = L.palette && L.palette.brand && L.palette.brand.hex ? L.palette.brand : null, alt = L.swatches || [];
  if (!B) return alt;
  const same = alt.find((s) => String(s.hex).toUpperCase() === String(B.hex).toUpperCase());
  const brand = { id: (same && same.id) || "brand", name: B.name || (same && same.name) || "대표색", hex: B.hex };
  return [brand, ...alt.filter((s) => s !== same && s.id !== brand.id)].slice(0, 5);
}
/** 화면에 쓰는 분위기 목록 — 대표색을 버튼 색 첫 번째로, 그 분위기를 쓰는 시안의 밀도를 붙인다 */
function getLooks(S) {
  if (!(Array.isArray(S.looks) && S.looks.length)) return DEFAULT_LOOKS;
  return S.looks.map((L) => {
    const C = (S.concepts || []).find((c) => c.look === L.id), d = C && (DENSITY_ALIAS[C.density] || C.density);
    return Object.assign({}, L, { swatches: swatchesOf(L) }, DENSITY[d] ? { _density: d } : {});
  });
}
/** toggles.swatch → 그 분위기의 버튼 색 id. "brand"는 대표색(첫 번째), 예전 값(calm/vivid)도 받는다 */
function resolveSwatch(L, v) {
  if (!L || !L.swatches || !L.swatches.length) return null;
  if (L.swatches.some((s) => s.id === v)) return v;
  if (v === "vivid" && L.swatches[1]) return L.swatches[1].id;
  return L.swatches[0].id;
}

module.exports = {
  DEFAULT_LOOKS, FONTS, FONT_ALIAS, resolveFont, fontOf, fontLinks, fontTokens, inkOf, calmHex, softInk, mutedInk, readable,
  roleColors, softFg, statusTokens, paletteTokens, TONES, toneOf, RATIOS, KRDS_STEPS, typeScale, allowedFontSizes, DENSITY, DENSITY_ALIAS,
  ACCENT_MIN_DIST, accentFit, getLooks, swatchesOf, looksCss, lookTokens, densityTokens, typeTokens, swatchTokens, resolveSwatch, PAIRS, lookPairs, contrast, mix, hex2rgb,
};
