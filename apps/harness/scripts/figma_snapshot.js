/*
 * figma_snapshot.js — Figma A단계 검사용 스냅샷 수집 스크립트
 *
 * 사용법
 *   이 파일의 내용을 그대로 Figma MCP `use_figma` 도구의 `code` 인자로 넘긴다.
 *   (반드시 그 전에 figma-use 스킬 = skill://figma/figma-use/SKILL.md 를 읽는다.)
 *
 *     mcp__figma-remote-mcp__use_figma({
 *       fileKey: "<build-log.md 의 figma_file>",
 *       description: "03 Screens/02 Components/01 Tokens 스냅샷 수집 (읽기 전용)",
 *       skillNames: "figma-use",
 *       code: "<이 파일 내용>"
 *     })
 *
 *   반환값(JSON 문자열)을 그대로 `design/figma-snapshot.json` 에 저장한 뒤
 *   `python3 scripts/figma_audit.py --snapshot design/figma-snapshot.json --rules design/design-rules.md`
 *   로 검사한다.
 *
 * use_figma 반환 규약 (figma-use SKILL.md §1, §3)
 *   - 데이터는 `return` 으로만 돌려준다. `figma.closePlugin()` 을 쓰지 않고,
 *     async IIFE 로 감싸지 않는다 (러너가 async 컨텍스트로 감싸 준다. top-level await 가능).
 *   - 반환값은 자동으로 JSON 직렬화된다. 여기서는 파일에 그대로 쓸 수 있도록
 *     이미 직렬화된 **JSON 문자열**을 반환한다 (마지막 표현식 = JSON.stringify(...)).
 *   - `console.log()` 출력은 절대 반환되지 않는다.
 *   - 이 스크립트는 읽기 전용이라 생성/변경 노드 ID가 없다 (SKILL.md 규칙 15 해당 없음).
 *
 * 반환 JSON 스키마 (figma_audit.py 가 읽는 형식. REST API로 만들어도 이 형식이면 통과)
 * {
 *   "file": string,                  // figma.root.name
 *   "generatedAt": string,           // ISO 8601
 *   "pagesScanned": [string],        // 실제로 순회한 페이지 이름
 *   "maxDepth": number,              // 적용된 깊이 제한
 *   "truncated": boolean,            // 깊이/노드 상한에 걸려 잘렸는지
 *   "variables": [
 *     { "id": string, "name": string, "collection": string,
 *       "type": "COLOR"|"FLOAT"|"STRING"|"BOOLEAN",
 *       "valuesByMode": { "<모드 이름>": any } }
 *   ],
 *   "textStyles": [
 *     { "id": string, "name": string, "fontSize": number|null,
 *       "fontWeight": string|null,      // Figma 는 weight 대신 style 문자열("Bold")을 준다
 *       "lineHeight": number|string|null }
 *   ],
 *   "pages": [
 *     { "name": string,
 *       "nodes": [
 *         { "id": string, "name": string, "type": string,
 *           "parentId": string|null,      // 페이지가 부모면 페이지 id
 *           "pageName": string,
 *           "depth": number,              // 페이지 직속 자식 = 0
 *           "childIndex": number,         // 부모 children 안에서의 인덱스 (z 순서. 클수록 위)
 *           "x": number, "y": number,     // 부모 기준 상대 좌표
 *           "width": number, "height": number,
 *           "visible": boolean,
 *           "layoutMode": "NONE"|"HORIZONTAL"|"VERTICAL"|null,
 *           "paddingTop": number|null, "paddingRight": number|null,
 *           "paddingBottom": number|null, "paddingLeft": number|null,
 *           "itemSpacing": number|null,
 *           "fills":   [ { "type": string, "hex": string|null, "opacity": number|null,
 *                          "boundVariable": string|null } ],   // boundVariable = 변수 id 또는 null
 *           "strokes": [ { ...fills 와 동일 형식... } ],
 *           "cornerRadius": number|"MIXED"|null,
 *           "textStyleId": string|null,   // "MIXED" 문자열일 수 있음
 *           "fontSize": number|"MIXED"|null,   // TEXT 노드에만
 *           "characters": string|null,    // TEXT 노드에만. 앞 80자
 *           "boundVariables": { "<속성>": "<변수 id>" },
 *           "isInstance": boolean,
 *           "mainComponentName": string|null,
 *           "componentPropertyValues": { "<속성>": string },   // variant 값
 *           "hasLabel": boolean,          // 이름이 "_label" 로 시작하는 자식이 있는지
 *           "insideIconComponent": boolean // 이름이 "Icon/" 로 시작하는 조상(또는 자기 자신) 아래인지
 *         }
 *       ] }
 *   ],
 *   "errors": [string]               // 노드 단위로 읽기 실패한 항목 (검사 계속 진행)
 * }
 *
 * 조정 상수 — 노드가 많으면 PAGES 로 범위를 좁히고 MAX_DEPTH 를 줄인다.
 */

// ── 조정 상수 ────────────────────────────────────────────────────────────
const PAGES = ["01 Tokens", "02 Components", "03 Screens"]; // 순회할 페이지 이름. []면 전체
const MAX_DEPTH = 8;          // 페이지 직속 자식이 depth 0. 이 값을 넘는 자손은 버린다
const MAX_NODES_PER_PAGE = 4000; // 안전 상한. 넘으면 truncated=true
const CHARACTERS_LIMIT = 80;  // 텍스트 내용 저장 길이
// ─────────────────────────────────────────────────────────────────────────

const errors = [];
let truncated = false;

function safe(fn, fallback, label) {
  try {
    const v = fn();
    return v === undefined ? fallback : v;
  } catch (e) {
    if (label) errors.push(label + ": " + String(e && e.message ? e.message : e));
    return fallback;
  }
}

function toHex(color) {
  if (!color) return null;
  const ch = function (v) {
    const n = Math.round(Math.max(0, Math.min(1, v)) * 255);
    return (n < 16 ? "0" : "") + n.toString(16);
  };
  return ("#" + ch(color.r) + ch(color.g) + ch(color.b)).toUpperCase();
}

// paint 배열 → 검사에 필요한 최소 정보. boundVariable 은 변수 id 문자열 또는 null.
function paints(list) {
  if (!list || list === figma.mixed || typeof list.length !== "number") return [];
  const out = [];
  for (let i = 0; i < list.length; i++) {
    const p = list[i];
    if (!p) continue;
    let bound = null;
    if (p.boundVariables && p.boundVariables.color && p.boundVariables.color.id) {
      bound = p.boundVariables.color.id;
    }
    out.push({
      type: p.type || null,
      hex: p.type === "SOLID" ? toHex(p.color) : null,
      opacity: typeof p.opacity === "number" ? p.opacity : null,
      boundVariable: bound,
      visible: p.visible === false ? false : true
    });
  }
  return out;
}

// node.boundVariables → { 속성: 변수 id }. fills/strokes/effects 는 위 paints 가 따로 담는다.
function boundVars(node) {
  const raw = safe(function () { return node.boundVariables; }, null);
  const out = {};
  if (!raw) return out;
  for (const key in raw) {
    const v = raw[key];
    if (!v) continue;
    if (v.id) out[key] = v.id;
    else if (typeof v.length === "number" && v.length && v[0] && v[0].id) out[key] = v[0].id;
  }
  return out;
}

function num(v) {
  return typeof v === "number" ? v : null;
}

function mixedOr(v) {
  if (v === figma.mixed) return "MIXED";
  return v === undefined ? null : v;
}

// ── 변수 ──────────────────────────────────────────────────────────────────
const variables = [];
safe(function () {
  const collections = figma.variables.getLocalVariableCollections();
  const collById = {};
  for (const c of collections) collById[c.id] = c;
  const vars = figma.variables.getLocalVariables();
  for (const v of vars) {
    const coll = collById[v.variableCollectionId];
    const valuesByMode = {};
    if (coll) {
      for (const m of coll.modes) {
        const raw = v.valuesByMode ? v.valuesByMode[m.modeId] : undefined;
        if (raw && typeof raw === "object" && "r" in raw) {
          valuesByMode[m.name] = toHex(raw) + (typeof raw.a === "number" && raw.a < 1 ? "@" + raw.a : "");
        } else if (raw && typeof raw === "object" && raw.type === "VARIABLE_ALIAS") {
          valuesByMode[m.name] = "ALIAS:" + raw.id;
        } else {
          valuesByMode[m.name] = raw === undefined ? null : raw;
        }
      }
    }
    variables.push({
      id: v.id,
      name: v.name,
      collection: coll ? coll.name : null,
      type: v.resolvedType,
      valuesByMode: valuesByMode
    });
  }
  return true;
}, null, "variables");

// ── 텍스트 스타일 ──────────────────────────────────────────────────────────
const textStyles = [];
let rawTextStyles = null;
try {
  // 신형 API. 없으면 구형 동기 API 로 폴백.
  rawTextStyles = typeof figma.getLocalTextStylesAsync === "function"
    ? await figma.getLocalTextStylesAsync()
    : figma.getLocalTextStyles();
} catch (e) {
  rawTextStyles = safe(function () { return figma.getLocalTextStyles(); }, [], "textStyles");
}
for (const s of rawTextStyles || []) {
  let lh = null;
  const raw = safe(function () { return s.lineHeight; }, null);
  if (raw && typeof raw === "object") lh = raw.unit === "AUTO" ? "AUTO" : raw.value;
  textStyles.push({
    id: s.id,
    name: s.name,
    fontSize: num(safe(function () { return s.fontSize; }, null)),
    fontWeight: safe(function () { return s.fontName && s.fontName.style; }, null),
    lineHeight: lh
  });
}

// ── 페이지 순회 ────────────────────────────────────────────────────────────
const targetPages = figma.root.children.filter(function (p) {
  return PAGES.length === 0 || PAGES.indexOf(p.name) !== -1;
});

const pages = [];
const pagesScanned = [];

for (const page of targetPages) {
  // 페이지 콘텐츠는 지연 로딩된다. setCurrentPageAsync 로만 로드된다 (동기 setter 는 throw).
  await figma.setCurrentPageAsync(page);
  pagesScanned.push(page.name);

  const nodes = [];
  const stack = [];
  const kids = page.children || [];
  for (let i = kids.length - 1; i >= 0; i--) {
    stack.push({ node: kids[i], depth: 0, index: i, parentId: page.id, insideIcon: false });
  }

  while (stack.length) {
    if (nodes.length >= MAX_NODES_PER_PAGE) { truncated = true; break; }
    const item = stack.pop();
    const n = item.node;
    if (!n) continue;

    const name = safe(function () { return n.name; }, "", null) || "";
    const type = safe(function () { return n.type; }, "UNKNOWN", null);
    const isIconRoot = name.indexOf("Icon/") === 0;
    const insideIcon = item.insideIcon || isIconRoot;

    const isInstance = type === "INSTANCE";
    let mainName = null;
    if (isInstance) {
      try {
        // dynamic-page 모드에서는 node.mainComponent 대신 async API 를 써야 한다.
        const mc = typeof n.getMainComponentAsync === "function"
          ? await n.getMainComponentAsync()
          : n.mainComponent;
        if (mc) {
          // 컴포넌트 세트 안의 variant 라면 세트 이름이 사람이 읽는 이름이다.
          mainName = (mc.parent && mc.parent.type === "COMPONENT_SET")
            ? mc.parent.name
            : mc.name;
        }
      } catch (e) {
        errors.push("mainComponent " + n.id + ": " + String(e && e.message ? e.message : e));
      }
    }

    // variant 값: 인스턴스는 componentProperties, 컴포넌트는 variantProperties
    const props = {};
    if (isInstance) {
      const cp = safe(function () { return n.componentProperties; }, null);
      if (cp) for (const k in cp) {
        const key = k.indexOf("#") >= 0 ? k.slice(0, k.indexOf("#")) : k;
        props[key] = cp[k] && cp[k].value !== undefined ? String(cp[k].value) : null;
      }
    } else if (type === "COMPONENT") {
      const vp = safe(function () { return n.variantProperties; }, null);
      if (vp) for (const k in vp) props[k] = vp[k] === null ? null : String(vp[k]);
    }

    const children = safe(function () { return n.children; }, null);
    const hasLabel = !!(children && children.some(function (c) {
      return c && typeof c.name === "string" && c.name.indexOf("_label") === 0;
    }));

    const rec = {
      id: n.id,
      name: name,
      type: type,
      parentId: item.parentId,
      pageName: page.name,
      depth: item.depth,
      childIndex: item.index,
      x: num(safe(function () { return n.x; }, null)),
      y: num(safe(function () { return n.y; }, null)),
      width: num(safe(function () { return n.width; }, null)),
      height: num(safe(function () { return n.height; }, null)),
      visible: safe(function () { return n.visible; }, true) !== false,
      layoutMode: safe(function () { return n.layoutMode; }, null),
      paddingTop: num(safe(function () { return n.paddingTop; }, null)),
      paddingRight: num(safe(function () { return n.paddingRight; }, null)),
      paddingBottom: num(safe(function () { return n.paddingBottom; }, null)),
      paddingLeft: num(safe(function () { return n.paddingLeft; }, null)),
      itemSpacing: num(safe(function () { return n.itemSpacing; }, null)),
      fills: paints(safe(function () { return n.fills; }, null)),
      strokes: paints(safe(function () { return n.strokes; }, null)),
      cornerRadius: mixedOr(safe(function () { return n.cornerRadius; }, null)),
      textStyleId: null,
      fontSize: null,
      characters: null,
      boundVariables: boundVars(n),
      isInstance: isInstance,
      mainComponentName: mainName,
      componentPropertyValues: props,
      hasLabel: hasLabel,
      insideIconComponent: insideIcon
    };

    if (type === "TEXT") {
      const tsid = safe(function () { return n.textStyleId; }, null);
      rec.textStyleId = tsid === figma.mixed ? "MIXED" : (tsid || null);
      rec.fontSize = mixedOr(safe(function () { return n.fontSize; }, null));
      const chars = safe(function () { return n.characters; }, null);
      rec.characters = typeof chars === "string" ? chars.slice(0, CHARACTERS_LIMIT) : null;
    }

    nodes.push(rec);

    if (children && item.depth + 1 <= MAX_DEPTH) {
      for (let i = children.length - 1; i >= 0; i--) {
        stack.push({
          node: children[i],
          depth: item.depth + 1,
          index: i,
          parentId: n.id,
          insideIcon: insideIcon
        });
      }
    } else if (children && children.length) {
      truncated = true;
    }
  }

  pages.push({ name: page.name, nodes: nodes });
}

const snapshot = {
  file: figma.root.name,
  generatedAt: new Date().toISOString(),
  pagesScanned: pagesScanned,
  maxDepth: MAX_DEPTH,
  truncated: truncated,
  variables: variables,
  textStyles: textStyles,
  pages: pages,
  errors: errors
};

// figma-use 규약: return 으로만 데이터를 돌려준다. 파일에 그대로 쓸 수 있게 문자열로 직렬화.
return JSON.stringify(snapshot);
