#!/usr/bin/env node
/**
 * dress.js — 꾸밈 카테고리 9개(배경 · 판 모양 · 제목 · 모서리 · 간격 · 글꼴 · 아이콘 · 색 쓰는 방식 · 그라데이션)의 값·과감함 점수·이름.
 * 사용자 결정(2026-10-14): "너무 다 비슷함", "1~10단계 다른 형태를 다 보여주자" → 시안 10개 = 과감함 1~10단계, 카테고리를 섞어 다르게.
 *
 *   node scripts/dress.js runs/<p>   → screens.json concepts[]마다 dress가 없으면 level(1~10)로 채우고 표를 찍는다
 *                                       (level 1 = 모두 기본값, 10 = 가장 과감. 시안끼리 4개 이상 카테고리가 다르게)
 * 화면에는 packages/core/tokens/dress.css가 data-* 로 입힌다(시안 보드 = 시안 화면 상자, 초안·최종본 = <html>, screens.json dress).
 * build.js · lint.js · 시안 보드가 CATS를 같이 쓴다.
 */
const CATS = {
  bg: { name: "배경", values: { plain: [0, "단색 바탕"], tint: [1, "연한 색 바탕"], glow: [1, "은은한 번짐"], dots: [2, "점무늬"], band: [3, "위쪽 색 띠"], mesh: [3, "색 번짐"], dark: [4, "어두운 머리"] } },
  cards: { name: "판 모양", values: { base: [0, "기본 판"], boxed: [1, "테두리 판"], flat: [1, "테두리 없는 판"], line: [2, "선으로 나눔"], float: [2, "떠 있는 판"], outline: [3, "굵은 선 판"] } },
  // 가운데 제목은 뺐다 — 왼쪽 정렬 판 위에 가운데 제목이 오면 정렬이 어긋나 보인다(사용자: "실제 앱처럼 정렬")
  head: { name: "제목", values: { normal: [0, "보통 제목"], big: [1, "큰 제목"], huge: [3, "아주 큰 제목"] } },
  radius: { name: "모서리", values: { base: [0, "기본 모서리"], soft: [1, "살짝 둥글게"], round: [1, "둥글게"], sharp: [2, "각지게"], pill: [3, "아주 둥글게"] } },
  space: { name: "간격", values: { normal: [0, "보통 간격"], airy: [1, "넉넉하게"], tight: [2, "촘촘하게"], extra: [3, "아주 넉넉하게"] } },
  font: { name: "글꼴", values: { base: [0, "분위기 글꼴"], pretendard: [1, "프리텐다드"], suit: [1, "수트"], "ibm-plex": [1, "IBM 플렉스"], "nanum-square-round": [1, "나눔스퀘어라운드"], "serif-title": [2, "명조 제목"] } },
  icons: { name: "아이콘", values: { line: [0, "선 아이콘"], fluent: [2, "입체 아이콘"] } },
  tone: { name: "색 쓰는 방식", values: { neutral: [0, "무채색 판"], soft: [1, "연한 색 판"], bold: [3, "진한 색 판"] } },
  // 그라데이션 — 배경 · 주 버튼과 큰 색 머리 · 큰 제목 글자에 한꺼번에 (사용자 결정 2026-10-14)
  grad: { name: "그라데이션", values: { none: [0, "단색"], fade: [1, "은은한 그라데이션"], sunset: [2, "노을 그라데이션"], aurora: [3, "오로라 그라데이션"] } },
};
const KEYS = Object.keys(CATS);
const BASE = { bg: "plain", cards: "base", head: "normal", radius: "base", space: "normal", font: "base", icons: "line", tone: "neutral", grad: "none" };
const MAX = KEYS.reduce((n, k) => n + Math.max(...Object.values(CATS[k].values).map((v) => v[0])), 0);
const score = (d) => KEYS.reduce((n, k) => n + ((CATS[k].values[d[k]] || [0])[0]), 0);
const diff = (a, b) => KEYS.filter((k) => (a[k] || BASE[k]) !== (b[k] || BASE[k])).length;
/** 사람이 읽는 이름 — 기본값은 빼고 */
const words = (d) => KEYS.filter((k) => d && d[k] && d[k] !== BASE[k] && CATS[k].values[d[k]]).map((k) => CATS[k].values[d[k]][1]);
/** html/상자에 붙일 data-* (아이콘은 build.js가 조각을 바꾸므로 빼고, 기본값도 뺀다) */
const attrs = (d) => KEYS.filter((k) => k !== "icons" && d && d[k] && d[k] !== BASE[k]).map((k) => ` data-${k}="${d[k]}"`).join("");
function check(d) {
  const bad = [];
  for (const [k, v] of Object.entries(d || {})) if (!CATS[k]) bad.push(`카테고리 '${k}' 없음`); else if (!CATS[k].values[v]) bad.push(`${CATS[k].name} '${v}' 없음 (${Object.keys(CATS[k].values).join("|")})`);
  return bad;
}
// 같은 입력이면 같은 결과 (mulberry32)
function rng(seed) { return () => { seed |= 0; seed = (seed + 0x6d2b79f5) | 0; let t = Math.imul(seed ^ (seed >>> 15), 1 | seed); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
/** level(1~10)에 맞는 꾸밈 — 과감함 합이 목표에 가깝고, 이미 정한 시안들과 4개 이상 다르게 */
function pick(level, taken, seed) {
  if (level <= 1) return Object.assign({}, BASE);
  const target = Math.round(((level - 1) / 9) * MAX), r = rng(seed || level * 7919);
  let best = null, bestCost = Infinity;
  for (let i = 0; i < 6000; i++) {
    const d = {};
    for (const k of KEYS) { const vs = Object.keys(CATS[k].values); d[k] = vs[Math.floor(r() * vs.length)]; }
    const near = taken.length ? Math.min(...taken.map((t) => diff(t, d))) : 8;
    // 같은 값이 여러 시안에 몰리지 않게(사용자: "배경도 더 다이나믹하게 다양하게") — 이미 쓴 값일수록 비싸다, 배경은 더
    const reuse = KEYS.reduce((n, k) => n + taken.filter((t) => t[k] === d[k] && d[k] !== BASE[k]).length * (k === "bg" ? 12 : 4), 0);
    // 강조색을 크게 쓰는 꾸밈은 한 안에 두 개까지(색 띠·색 번짐·연한 색 바탕 / 진한 색 판 / 그라데이션) — 버튼 색과 겹쳐 시끄러워지지 않게
    const loud = [["band", "mesh", "tint"].includes(d.bg), d.tone === "bold", d.grad !== "none"].filter(Boolean).length;
    const clash = (loud > 2 ? 300 : 0) + (d.bg === "band" && d.tone === "bold" ? 300 : 0) + (d.bg === "dark" && d.grad === "aurora" ? 150 : 0);
    const cost = Math.abs(score(d) - target) * 10 + Math.max(0, 4 - near) * 100 + reuse + clash;
    if (cost < bestCost) { best = d; bestCost = cost; if (cost === 0) break; }
  }
  return best;
}
module.exports = { CATS, KEYS, BASE, MAX, score, diff, words, attrs, check, pick };

if (require.main === module) {
  const fs = require("fs"), path = require("path");
  const runDir = process.argv[2];
  if (!runDir) { console.error("usage: node scripts/dress.js runs/<project>"); process.exit(2); }
  const p = path.join(runDir, "screens.json"), S = JSON.parse(fs.readFileSync(p, "utf8"));
  const C = Array.isArray(S.concepts) ? S.concepts : [];
  const taken = C.filter((c) => c.dress).map((c) => c.dress);
  let n = 0;
  C.slice().sort((a, b) => (a.level || 0) - (b.level || 0)).forEach((c, i) => {
    if (c.dress) return;
    c.dress = pick(c.level || i + 1, taken, (c.level || i + 1) * 7919 + c.id.charCodeAt(0)); taken.push(c.dress); n++;
  });
  fs.writeFileSync(p, JSON.stringify(S, null, 2) + "\n");
  for (const c of C) console.log(`시안 ${c.id} · ${c.level || "?"}단계 · 과감함 ${score(c.dress)}/${MAX} · ${words(c.dress).join(" · ") || "기본 그대로"}`);
  console.log(`[dress] ${n}개 채움`);
}
