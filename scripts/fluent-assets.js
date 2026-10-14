#!/usr/bin/env node
/**
 * fluent-assets.js — 마이크로소프트 무료 아이콘(MIT)을 하네스 자산으로 만든다. 한 번 돌려 결과를 커밋한다.
 *   - Fluent UI System Icons(@fluentui/svg-icons) → packages/core/icons/fluent-sprite.svg
 *       허용 아이콘(lucide 이름)마다 같은 뜻의 Fluent 아이콘: f-<lucide> (선) · f-<lucide>-filled (채움) · f-<lucide>-color (컬러, 있을 때)
 *       짝(lucide → fluent)은 packages/core/icons/fluent-map.json
 *   - Fluent Emoji 3D(microsoft/fluentui-emoji) → packages/core/illustrations/<이름>.png (160px)
 *       어떤 아이콘 자리에 어떤 그림을 쓸지는 packages/core/illustrations/emoji-map.json
 *
 *   npm pack @fluentui/svg-icons && tar -xzf fluentui-svg-icons-*.tgz   (아무 빈 폴더에서)
 *   node scripts/fluent-assets.js <압축을 푼 package 폴더>
 *
 * 화면에는 build.js --icons fluent(또는 screens.json toggles.icons)일 때만 쓰인다. 기본은 Lucide.
 */
const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");

const root = path.join(__dirname, "..");
const iconsDir = path.join(root, "packages/core/icons");
const illDir = path.join(root, "packages/core/illustrations");
const pkg = process.argv[2];
if (!pkg || !fs.existsSync(path.join(pkg, "icons"))) { console.error("사용법: node scripts/fluent-assets.js <@fluentui/svg-icons package 폴더>"); process.exit(1); }

// ---------- 1. Fluent UI System Icons ----------
const MAP = JSON.parse(fs.readFileSync(path.join(iconsDir, "fluent-map.json"), "utf8"));
const file = (name, style) => path.join(pkg, "icons", `${name}_24_${style}.svg`);
const out = [], miss = [];
for (const [lucide, fluent] of Object.entries(MAP)) {
  if (lucide.startsWith("_")) continue;
  if (!fs.existsSync(file(fluent, "regular"))) { miss.push(`${lucide}→${fluent}`); continue; }
  for (const [style, suffix] of [["regular", ""], ["filled", "-filled"], ["color", "-color"]]) {
    if (!fs.existsSync(file(fluent, style))) continue;
    let svg = fs.readFileSync(file(fluent, style), "utf8");
    const body = svg.replace(/^[\s\S]*?<svg[^>]*>/, "").replace(/<\/svg>\s*$/, "")
      // 선·채움은 글자색을 따른다(.icon의 stroke는 끈다). 컬러는 그라데이션 그대로 — id가 겹치지 않게 접두어
      .replace(/<path(?![^>]*fill=)/g, style === "color" ? "<path" : '<path fill="currentColor"')
      .replace(/ic_fluent_/g, "hxf_");
    out.push(`<symbol id="f-${lucide}${suffix}" viewBox="0 0 24 24" stroke="none">${body}</symbol>`);
  }
}
if (miss.length) { console.error("[fluent] FAIL Fluent에 없는 짝:", miss.join(", ")); process.exit(1); }
fs.writeFileSync(path.join(iconsDir, "fluent-sprite.svg"),
  `<!-- @license Fluent UI System Icons (MIT) © Microsoft Corporation — https://github.com/microsoft/fluentui-system-icons · scripts/fluent-assets.js로 만듦 -->\n<svg xmlns="http://www.w3.org/2000/svg"><defs>\n${out.join("\n")}\n</defs></svg>\n`);
console.log(`[fluent] 아이콘 ${Object.keys(MAP).filter((k) => !k.startsWith("_")).length}개 → 심볼 ${out.length}개 (packages/core/icons/fluent-sprite.svg)`);

// ---------- 2. Fluent Emoji 3D ----------
const EM = JSON.parse(fs.readFileSync(path.join(illDir, "emoji-map.json"), "utf8"));
const want = new Set(Object.entries(EM).filter(([k]) => !k.startsWith("_")).map(([, v]) => v));
const RAW = "https://raw.githubusercontent.com/microsoft/fluentui-emoji/main/assets/";
const SKIN = new Set(EM._skinTone || []);
const fail = [];
for (const name of want) {
  const slug = name.toLowerCase().replace(/\s+/g, "-");
  const dest = path.join(illDir, slug + ".png");
  if (fs.existsSync(dest)) continue;
  const base = name.toLowerCase().replace(/\s+/g, "_");
  const url = RAW + encodeURIComponent(name) + (SKIN.has(name) ? `/Default/3D/${base}_3d_default.png` : `/3D/${base}_3d.png`);
  try {
    const tmp = dest + ".orig";
    execFileSync("curl", ["-fsSL", "-o", tmp, url]);
    execFileSync("sips", ["-Z", "160", tmp, "--out", dest], { stdio: "ignore" });   // macOS: 256 → 160px
    fs.unlinkSync(tmp);
  } catch (e) { fail.push(name); }
}
if (fail.length) console.warn("[fluent] WARN 받지 못한 이모지:", fail.join(", "));
console.log(`[fluent] 이모지 ${want.size - fail.length}개 (packages/core/illustrations/)`);
