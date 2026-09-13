/*
 * figma_parity.js — "Figma 생성" 지시 후 이름·개수 일치(parity) 검사용 수집 스크립트 (읽기 전용)
 *
 * 사용법
 *   이 파일 내용을 그대로 Figma MCP `use_figma` 의 `code` 인자로 넘긴다.
 *   (반드시 그 전에 figma-use 스킬 = skill://figma/figma-use/SKILL.md 를 읽는다.)
 *
 *     use_figma({
 *       fileKey: "<build-log.md 의 figma_file>",
 *       description: "parity 수집 (읽기 전용 · 이름만)",
 *       skillNames: "figma-use",
 *       code: "<이 파일 내용>"
 *     })
 *
 *   반환 문자열을 design/figma-parity.json 에 저장한 뒤
 *   python3 scripts/figma_parity.py --actual design/figma-parity.json \
 *       --rules design/design-rules.md --icons design/icons.md --screens design/screens.md
 *
 * 규약 (figma-use SKILL.md §1·§3)
 *   - 데이터는 return 으로만 나간다. console.log 는 반환되지 않는다.
 *   - figma.closePlugin() 금지, async IIFE 로 감싸지 않는다 (top-level await 사용 가능).
 *   - 읽기 전용: 노드를 만들거나 바꾸지 않는다.
 *
 * 반환 JSON (이름만 담아 20KB 안에 들어오게 한다)
 * {
 *   "file": string, "generatedAt": string,
 *   "variables":     [ { "collection": string, "name": string } ],
 *   "textStyles":    [ string ],            // 예: "Text/h1"
 *   "effectStyles":  [ string ],            // 예: "Shadow/sm"
 *   "componentSets": [ string ],            // 예: "Button", "Icon/plus"
 *   "components":    [ string ],            // 컴포넌트 세트에 속하지 않은 단독 COMPONENT
 *   "screenFrames":  [ { "name": string, "w": number, "h": number } ],  // 03 Screens 최상위(depth 0)만
 *   "truncated": boolean, "errors": [string]
 * }
 */

const SCREENS_PAGE = "03 Screens";
const MAX_ITEMS = 1500;   // 배열별 상한 (넘으면 truncated=true)

const errors = [];
let truncated = false;

function cap(list) {
  if (list.length > MAX_ITEMS) { truncated = true; return list.slice(0, MAX_ITEMS); }
  return list;
}

async function tryAsync(label, fnAsync, fnSync) {
  try {
    if (typeof fnAsync === "function") return await fnAsync();
  } catch (e) { errors.push(label + ": " + String(e && e.message ? e.message : e)); }
  try {
    if (typeof fnSync === "function") return fnSync();
  } catch (e) { errors.push(label + " (sync): " + String(e && e.message ? e.message : e)); }
  return [];
}

// ── 변수 ──────────────────────────────────────────────────────────────────
const collections = await tryAsync("collections",
  figma.variables.getLocalVariableCollectionsAsync && (() => figma.variables.getLocalVariableCollectionsAsync()),
  figma.variables.getLocalVariableCollections && (() => figma.variables.getLocalVariableCollections()));
const collName = {};
for (const c of collections || []) collName[c.id] = c.name;
const vars = await tryAsync("variables",
  figma.variables.getLocalVariablesAsync && (() => figma.variables.getLocalVariablesAsync()),
  figma.variables.getLocalVariables && (() => figma.variables.getLocalVariables()));
const variables = cap((vars || []).map(v => ({ collection: collName[v.variableCollectionId] || null, name: v.name })));

// ── 스타일 ────────────────────────────────────────────────────────────────
const textStyles = cap(((await tryAsync("textStyles",
  figma.getLocalTextStylesAsync && (() => figma.getLocalTextStylesAsync()),
  figma.getLocalTextStyles && (() => figma.getLocalTextStyles()))) || []).map(s => s.name));
const effectStyles = cap(((await tryAsync("effectStyles",
  figma.getLocalEffectStylesAsync && (() => figma.getLocalEffectStylesAsync()),
  figma.getLocalEffectStyles && (() => figma.getLocalEffectStyles()))) || []).map(s => s.name));

// ── 컴포넌트 (모든 페이지) ────────────────────────────────────────────────
const componentSets = [];
const components = [];
try {
  if (typeof figma.loadAllPagesAsync === "function") await figma.loadAllPagesAsync();
  const found = figma.root.findAllWithCriteria({ types: ["COMPONENT_SET", "COMPONENT"] });
  for (const n of found) {
    if (n.type === "COMPONENT_SET") componentSets.push(n.name);
    else if (!(n.parent && n.parent.type === "COMPONENT_SET")) components.push(n.name);
  }
} catch (e) {
  errors.push("components: " + String(e && e.message ? e.message : e));
}

// ── 03 Screens 최상위 프레임 ──────────────────────────────────────────────
const screenFrames = [];
const screensPage = figma.root.children.find(p => p.name === SCREENS_PAGE);
if (!screensPage) {
  errors.push("페이지 '" + SCREENS_PAGE + "' 없음");
} else {
  try {
    if (typeof screensPage.loadAsync === "function") await screensPage.loadAsync();
    for (const n of screensPage.children) {
      if (n.type !== "FRAME" && n.type !== "COMPONENT" && n.type !== "SECTION") continue;
      screenFrames.push({ name: n.name, w: Math.round(n.width), h: Math.round(n.height) });
    }
  } catch (e) {
    errors.push("screens: " + String(e && e.message ? e.message : e));
  }
}

return JSON.stringify({
  file: figma.root.name,
  generatedAt: new Date().toISOString(),
  variables: variables,
  textStyles: textStyles,
  effectStyles: effectStyles,
  componentSets: cap(componentSets),
  components: cap(components),
  screenFrames: cap(screenFrames),
  truncated: truncated,
  errors: errors
});
