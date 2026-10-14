// 값 — scripts/looks.js가 계산한 분위기 값이 KRDS 바닥을 지킨다: 색 짝 대비(text-contrast) · 본문 줄 간격(leading-min) ·
// 본문 크기(body-size-min) · 대표색은 palette.brand 한 칸 · 글꼴 세트 이름(look.font)이 정본 값 목록과 같다.
// 규칙 값은 packages/core/schema/rules.json에서 읽는다. 고정 입력 · 기본 분위기 · 일부러 거친 분위기(순검정 · 형광 · 아주 옅은 색)를 모두 본다.
const fs = require("fs");
const path = require("path");
const { ROOT, suite } = require("../lib.js");
const LK = require(path.join(ROOT, "scripts", "looks.js"));

const t = suite("30 값");
const { rules } = JSON.parse(fs.readFileSync(path.join(ROOT, "packages", "core", "schema", "rules.json"), "utf8"));
const R = (id) => (rules.find((r) => r.id === id) || {}).value || {};
const SCHEMA = JSON.parse(fs.readFileSync(path.join(ROOT, "packages", "core", "schema", "screens.schema.json"), "utf8"));
const SAMPLE = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "fixtures", "sample", "screens.json"), "utf8"));

// 일부러 거친 분위기 — 자동 보정(본문 누르기 · 채도 상한 · 버튼 면 옮기기 · 옅은 면 글자)이 대비를 지키는지
const ROUGH = [
  { id: "pure-white", name: "순백", why: "-", mode: "light", bg: "#FFFFFF", ink: "#000000", shape: "soft", font: "suit",
    palette: { brand: { hex: "#00FF66" }, support: { hex: "#F7F7F7" }, accent: { hex: "#FFD400" } },
    swatches: [{ id: "lime", hex: "#C6FF00" }, { id: "sky", hex: "#7DD3FC" }, { id: "gray", hex: "#9CA3AF" }] },
  { id: "pure-black", name: "순흑", why: "-", mode: "dark", bg: "#000000", ink: "#FFFFFF", shape: "sharp", font: "serif-title",
    palette: { brand: { hex: "#1E3A8A" }, support: { hex: "#333333" }, accent: { hex: "#FF2D55" } },
    swatches: [{ id: "yellow", hex: "#FFFF00" }, { id: "navy", hex: "#0B1A3A" }] },
  { id: "color-bg", name: "색 바탕", why: "-", mode: "light", bg: "#E8D5B5", ink: "#3A2E1F", shape: "round", font: "ibm-plex",
    palette: { brand: { hex: "#C2410C" }, support: { hex: "#D9C3A0" } }, swatches: [{ id: "olive", hex: "#808000" }] },
];
const sets = [["고정 입력", LK.getLooks(SAMPLE)], ["기본 분위기", LK.getLooks({})], ["거친 분위기", LK.getLooks({ looks: ROUGH })]];

// text-contrast — 분위기 × 버튼 색마다 색 짝 전부. 짝의 최소값은 규칙 값(글자 min · 아이콘 large)과 같아야 한다
{
  const tc = R("text-contrast"), mins = new Set([tc.min, tc.large]);
  const off = LK.PAIRS.filter(([, , , m]) => !mins.has(m));
  if (off.length) t.fail(`text-contrast: looks.js PAIRS 최소값이 규칙 값(${[...mins].join(" · ")})과 다름 — ${off.map((p) => p[0]).join(", ")}`);
  for (const [label, looks] of sets) {
    let n = 0;
    const bad = [];
    for (const L of looks) for (const sw of L.swatches) for (const p of LK.lookPairs(L, sw)) {
      n++;
      if (p.c < p.min) bad.push(`${L.id}/${sw.id} ${p.n} ${p.c.toFixed(2)} < ${p.min}`);
    }
    if (bad.length) t.fail(`text-contrast (${label}): 기준 미달 ${bad.length}\n    ${bad.join("\n    ")}`);
    else t.ok(`text-contrast (${label}) — 짝 ${n}개 모두 기준 이상`);
  }
}

// leading-min · font-weight-krds — 분위기가 덮어쓰는 본문 줄 간격은 바닥 이상, 글꼴 세트는 본문 굵기 · 자간을 덮지 않는다
{
  const min = R("leading-min").min, bad = [];
  for (const [label, looks] of sets) for (const L of looks) {
    const v = Object.assign(LK.lookTokens(L), LK.densityTokens(L), LK.typeTokens(L, "normal"));
    if (v["--lh-normal"] && Number(v["--lh-normal"]) < min) bad.push(`${label} ${L.id}: --lh-normal ${v["--lh-normal"]}`);
    for (const k of ["--fw-body", "--fw-regular", "--fw-bold", "--fw-semibold", "--fw-medium", "--lh-tight"]) if (k in v) bad.push(`${label} ${L.id}: 분위기가 ${k}를 덮음 (본문 바닥은 base.css)`);
    for (const k of Object.keys(v).filter((x) => /^--(ls|tracking)-/.test(x))) if (!(k === "--tracking-heading" && /^max\(var\(--tracking-krds\), /.test(v[k]))) bad.push(`${label} ${L.id}: 분위기가 자간 ${k}를 KRDS 바닥선 없이 덮음`);
  }
  for (const [d, v] of Object.entries(LK.DENSITY)) if (Number(v["--lh-normal"]) < min) bad.push(`밀도 ${d}: --lh-normal ${v["--lh-normal"]}`);
  if (bad.length) t.fail(`leading-min · font-weight-krds (분위기 값)\n    ${bad.join("\n    ")}`); else t.ok(`leading-min · font-weight-krds — 분위기 본문 줄 간격 ${min} 이상, 본문 굵기 · 자간은 덮지 않음`);
}

// body-size-min — 분위기가 글자 단계를 다시 계산해도(type.ratio) 본문은 바닥 이상
{
  const min = R("body-size-min").min, body = { normal: R("body-size-min").krds_default, large: LK.KRDS_STEPS.large[2] }, bad = [];
  for (const size of ["normal", "large"]) for (const ratio of Object.keys(LK.RATIOS)) {
    const s = LK.typeScale(size, ratio);
    if (s[2] < min) bad.push(`${size} · ${ratio}: 본문 ${s[2]}px`);
    if (s[2] !== body[size]) bad.push(`${size} · ${ratio}: 본문 ${s[2]}px — 비율과 상관없이 ${body[size]}px이어야 함`);
    if (s[0] < 12) bad.push(`${size} · ${ratio}: 가장 작은 글자 ${s[0]}px < 12`);
    if (s.some((v, i) => i && v < s[i - 1] + 2)) bad.push(`${size} · ${ratio}: 단계 사이가 2px 미만 (${s.join(" ")})`);
  }
  if (bad.length) t.fail(`body-size-min (글자 단계)\n    ${bad.join("\n    ")}`); else t.ok(`body-size-min — 글자 단계 본문 ${body.normal} · 크게 ${body.large}px 고정 (보통 · 크게 × 비율 ${Object.keys(LK.RATIOS).length})`);
}

// tracking-krds — base.css --tracking-krds 식이 규칙 값 그대로(본문 · 작은 제목 body, 큰 제목 large_heading_px, 문턱은 규칙 문장의 'NNpx 이상'),
// 부품이 쓰는 --tracking-heading은 그 식, 글꼴 세트가 자간을 정해도 max(바닥선, 세트 값)
{
  const rule = rules.find((r) => r.id === "tracking-krds") || {}, val = rule.value || {}, th = Number((/(\d+)px 이상/.exec(rule.says || "") || [])[1]);
  const css = fs.readFileSync(path.join(ROOT, "packages", "core", "tokens", "base.css"), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
  const m = /--tracking-krds:\s*clamp\((-?[\d.]+)px,\s*\(1em - ([\d.]+)px\) \* 1000,\s*(-?[\d.]+)px\);/.exec(css);
  const bad = [];
  if (!m) bad.push("base.css --tracking-krds 식(clamp(0px, (1em - …px) * 1000, …px))을 찾지 못함");
  else {
    // 식을 글자 단계마다 풀어 본다 — 문턱 이상은 large_heading_px, 아래는 body
    const at = (px) => Math.min(Math.max(Number(m[1]), (px - Number(m[2])) * 1000), Number(m[3]));
    const sizes = [...new Set([...LK.KRDS_STEPS.normal, ...LK.KRDS_STEPS.large])];
    for (const px of sizes) { const want = px >= th ? val.large_heading_px : val.body; if (at(px) !== want) bad.push(`${px}px 제목 자간 ${at(px)}px — 규칙은 ${want}px`); }
  }
  if (!/--tracking-heading:\s*var\(--tracking-krds\);/.test(css)) bad.push("base.css --tracking-heading이 var(--tracking-krds)가 아님");
  LK.FONT_ALIAS.__t = { name: "시험", font: "sans", tracking: "-0.02em" };
  const ft = LK.fontTokens({ font: "__t" })["--tracking-heading"];
  delete LK.FONT_ALIAS.__t;
  if (ft !== "max(var(--tracking-krds), -0.02em)") bad.push(`글꼴 세트 자간이 바닥선 없이 나감: ${ft}`);
  if (!th || val.large_heading_px === undefined) bad.push("rules.json tracking-krds에서 문턱 · 값을 읽지 못함");
  if (bad.length) t.fail(`tracking-krds\n    ${bad.join("\n    ")}`); else t.ok(`tracking-krds — ${th}px 이상 제목 ${val.large_heading_px}px · 그 아래 ${val.body}, 글꼴 세트 자간은 바닥선 위로만`);
}

// accent 기준은 색상 계열을 가리지 않는다 — 상태색이 많은 분위기(대표색 · support가 초록 · 빨강 · 주황)에서도
// 색상환을 돌며 같은 밝기의 후보 24개를 넣으면, 떨어지는 후보는 대표색 이웃(색상각 ±60° 안, 많아야 9개)뿐이고 15개 이상이 붙는다
{
  const ring = (Lk, C) => Array.from({ length: 24 }, (_, i) => { const H = (i * 15 * Math.PI) / 180, a = C * Math.cos(H), b = C * Math.sin(H);
    const l = (Lk + 0.3963377774 * a + 0.2158037573 * b) ** 3, m = (Lk - 0.1055613458 * a - 0.0638541728 * b) ** 3, s = (Lk - 0.0894841775 * a - 1.291485548 * b) ** 3;
    const lin = [4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s, -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s, -0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s];
    const g = (v) => Math.round(255 * Math.min(1, Math.max(0, v <= 0.0031308 ? 12.92 * v : 1.055 * Math.pow(v, 1 / 2.4) - 0.055)));
    return { deg: i * 15, hex: "#" + lin.map(g).map((v) => v.toString(16).padStart(2, "0")).join("").toUpperCase() }; });
  const hueDeg = (hex) => { const n = parseInt(hex.slice(1), 16), [r, g, b] = [n >> 16, (n >> 8) & 255, n & 255].map((v) => { v /= 255; return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; });
    const l = Math.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b), m = Math.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b), s = Math.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b);
    return ((Math.atan2(0.0259040371 * l + 0.7827717662 * m - 0.808675766 * s, 1.9779984951 * l - 2.428592205 * m + 0.4505937099 * s) * 180) / Math.PI + 360) % 360; };
  const look = (id, mode, bg, brand, support) => ({ id, mode, bg, ink: mode === "dark" ? "#E6E8EC" : "#1F1B16", shape: "soft", palette: { brand: { hex: brand }, support: { hex: support } }, swatches: [] });
  const LOOKS = [
    look("brand-green", "light", "#FFFFFF", "#2F7D4F", "#C2412B"), look("brand-red", "light", "#FBF8F3", "#C2412B", "#B7791F"),
    look("brand-amber", "light", "#F7F7F8", "#B7791F", "#2F7D4F"), look("brand-blue", "light", "#FFFFFF", "#2563EB", "#3A6EA5"),
    look("dark-green", "dark", "#0F1115", "#5CC08A", "#F08A74"),
  ];
  const bad = [];
  for (const L of LOOKS) {
    const cand = ring(L.mode === "dark" ? 0.75 : 0.52, 0.12), bh = hueDeg(L.palette.brand.hex);
    const res = cand.map((c) => Object.assign(c, LK.accentFit(L, c.hex)));
    const far = res.filter((c) => !c.ok && Math.min(Math.abs(hueDeg(c.hex) - bh), 360 - Math.abs(hueDeg(c.hex) - bh)) > 60);
    const ok = res.filter((c) => c.ok).length;
    if (far.length) bad.push(`${L.id}: 대표색 이웃이 아닌 후보가 떨어짐 — ${far.map((c) => `${c.deg}° ${c.hex} (${c.why.join(", ")})`).join(" · ")}`);
    if (ok < 15) bad.push(`${L.id}: 붙은 후보 ${ok}/24 — 한 범위로 몰림`);
  }
  if (bad.length) t.fail(`accent 기준 쏠림\n    ${bad.join("\n    ")}`); else t.ok(`accent 기준 — 상태색이 많은 분위기 ${LOOKS.length}개에서 색상환 후보 24개 중 대표색 이웃만 떨어짐`);
}

// 대표색은 palette.brand 한 칸 — 버튼 색 첫 번째로 붙고 겹치지 않는다(옛 실행물처럼 swatches에도 있어도)
{
  const base = SAMPLE.looks[0], B = base.palette.brand.hex.toUpperCase(), alt = base.swatches.filter((s) => s.hex.toUpperCase() !== B);
  const cases = [
    ["대표색이 swatches 둘째에도 있음(옛 형식)", Object.assign({}, base, { swatches: [alt[0], { id: "old-brand", name: "대표색", hex: base.palette.brand.hex }, ...alt.slice(1)] })],
    ["대표색이 palette.brand에만 있음", Object.assign({}, base, { swatches: alt })],
  ];
  for (const [label, L] of cases) {
    const [G] = LK.getLooks({ looks: [L] }), hexes = G.swatches.map((s) => s.hex.toUpperCase());
    const okFirst = hexes[0] === B && hexes.filter((h) => h === B).length === 1 && hexes.length <= 5;
    const okBrand = LK.resolveSwatch(G, "brand") === G.swatches[0].id;
    if (okFirst && okBrand) t.ok(`대표색 한 칸 — ${label}`); else t.fail(`대표색 한 칸 — ${label}: ${G.swatches.map((s) => `${s.id} ${s.hex}`).join(", ")}`);
  }
}

// 글꼴 세트 — 정본 looks[].font 값 목록 = looks.js FONT_ALIAS, 세트마다 웹 글꼴 · 본문 고딕
{
  const enumOf = (o) => (o.anyOf || o.oneOf || []).map((x) => x.const).concat(o.enum || []);
  const want = enumOf(SCHEMA.$defs.look.properties.font).sort(), have = Object.keys(LK.FONT_ALIAS).sort();
  if (JSON.stringify(want) === JSON.stringify(have)) t.ok(`글꼴 세트 ${have.length}개 — 정본 값 목록과 같음`);
  else t.fail(`글꼴 세트 값이 다름 — 정본 ${want.join(" · ")} / looks.js ${have.join(" · ")}`);
  const bad = have.filter((id) => { const f = LK.fontOf({ font: id }); return !f.css.length || !LK.FONTS[f.body].gothic; });
  if (bad.length) t.fail(`글꼴 세트 ${bad.join(", ")}: 웹 글꼴이 없거나 본문이 고딕이 아님`); else t.ok("글꼴 세트 — 웹 글꼴 있음 · 본문 고딕");
}

t.end();
