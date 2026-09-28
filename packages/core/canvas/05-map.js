/* 05-map.js — 공용 지도 캔버스(와이어플로우): HX.buildMap(container, opts). final 지도와 board 캔버스가 함께 쓴다.
   행 = 시나리오(flow) 하나. 행 안에서 화면을 단계 순서대로 펼친다(같은 화면이 여러 번 나와도 복사본 노드).
   흐름에 한 번도 안 나오는 화면은 마지막 행 "그 밖의 화면". 캔버스 왼쪽 위 칩으로 시나리오 하나/전체를 고른다.
   opts: { nodeScale, fullHeight, onNodeClick(slug, id), onNodeDblClick(slug, id), onRegionClick(slug, region, id),
           onRegionHover(slug, region, on, id), onScope(rowIndex|null), scope(기본 0), wheelPan, panKeys, fitPad:{l,r,t,b} }
   view: { el, rows, instances, order, frames[id], nodes[id], inst(id), instancesOf(slug), scope(), setScope(i,{fit}), visibleOrder(),
           fit(), fitWidth(), zoomBy(f), focusNode(idOrSlug,{animate}), reframe(), nodeInView(id), onZoom, onShow, onHide, zoom() } */
(function () {
  "use strict";
  var HX = window.HX, doc = document;
  var SVG = "http://www.w3.org/2000/svg";
  function svgEl(tag, attrs) { var e = doc.createElementNS(SVG, tag); Object.keys(attrs || {}).forEach(function (k) { e.setAttribute(k, attrs[k]); }); return e; }
  HX.shortName = function (s, n) { s = String(s || ""); n = n || 14; return s.length > n ? s.slice(0, n) + "…" : s; };

  /* 행·인스턴스 모델: 행마다 nodes = [steps[0].from], step마다 (from이 마지막 노드와 다르면 복사본 + "돌아와서") → to 복사본 */
  HX.wireflow = function () {
    var rows = [], instances = [], used = {}, seenKey = {};
    function add(row, slug, x) {
      var pos = row.insts.length, id = row.key + "#" + (row.kind === "other" ? slug : pos);
      var it = { id: id, slug: slug, flowKey: row.key, flowIndex: row.flowIndex, stepIndex: null, row: rows.length, pos: pos,
        done: 0, outStep: null, same: false, first: !used[slug] };
      Object.keys(x || {}).forEach(function (k) { it[k] = x[k]; });
      used[slug] = true; row.insts.push(it); instances.push(it); return it;
    }
    HX.data.flows.forEach(function (f, fi) {
      var all = f.steps || [], ok = all.filter(function (st) { return HX.bySlug[st.from] && HX.bySlug[st.to]; });
      if (!ok.length) return;
      var key = String(f.key || f.id || "flow" + (fi + 1)); if (seenKey[key] || key === "other") key += "-" + (fi + 1); seenKey[key] = true;
      var row = { kind: "flow", key: key, flow: f, flowIndex: fi, n: fi + 1, K: all.length, insts: [], links: [] };
      add(row, ok[0].from, { done: 0 });
      all.forEach(function (st, i) {
        if (!HX.bySlug[st.from] || !HX.bySlug[st.to]) return;
        var last = row.insts[row.insts.length - 1], from = last;
        if (st.from !== last.slug) { from = add(row, st.from, { done: i }); row.links.push({ kind: "back", a: last, b: from, row: row }); }
        from.outStep = i;
        var to = add(row, st.to, { stepIndex: i, done: i + 1, same: st.to === st.from });
        row.links.push({ kind: "step", a: from, b: to, step: st, index: i, flow: f, row: row });
      });
      rows.push(row);
    });
    var rest = HX.data.screens.filter(function (s) { return !used[s.slug]; });
    if (rest.length) {
      var orow = { kind: "other", key: "other", flow: null, flowIndex: null, n: null, K: 0, insts: [], links: [] };
      rest.forEach(function (s) { add(orow, s.slug); });
      rows.push(orow);
    }
    return { rows: rows, instances: instances };
  };

  HX.buildMap = function (container, opts) {
    opts = opts || {};
    var NS = opts.nodeScale || (HX.platform === "mobile" ? 0.35 : 0.22);
    var vp = HX.el("div", { class: "hx-map", tabindex: "0", "aria-label": "화면 지도 (시나리오마다 한 줄)" });
    var world = HX.el("div", { class: "hx-map-world" });
    var svg = svgEl("svg", { class: "hx-edges" });
    var defs = svgEl("defs");
    [["hx-arrow", "var(--hx-arrow, #2563EB)"], ["hx-arrow-muted", "var(--hx-arrow-muted, rgba(37,99,235,.35))"], ["hx-arrow-active", "var(--hx-arrow, #2563EB)"], ["hx-arrow-back", "#9CA3AF"]].forEach(function (m) {
      var mk = svgEl("marker", { id: m[0], viewBox: "0 0 10 10", refX: "9", refY: "5", markerWidth: "7", markerHeight: "7", orient: "auto-start-reverse", markerUnits: "strokeWidth" });
      mk.appendChild(svgEl("path", { d: "M0,0.5 L10,5 L0,9.5 Z", fill: m[1] })); defs.appendChild(mk);
    });
    svg.appendChild(defs);
    var edgeLayer = svgEl("g"); svg.appendChild(edgeLayer);
    var pillLayer = HX.el("div", { class: "hx-wf-pills" });
    var tip = HX.el("div", { class: "hx-tip", style: "display:none" });
    var chipBar = HX.el("div", { class: "hx-wf-chips", role: "tablist", "aria-label": "사용 흐름" });
    var rail = HX.el("div", { class: "hx-wf-rail", "aria-hidden": "true" });   // 시나리오 제목: 확대와 무관하게 왼쪽 고정 칸
    world.appendChild(svg); world.appendChild(pillLayer); vp.appendChild(world); vp.appendChild(rail); vp.appendChild(chipBar); doc.body.appendChild(tip);
    chipBar.addEventListener("pointerdown", function (e) { e.stopPropagation(); });

    var wf = HX.wireflow(), rows = wf.rows, instances = wf.instances;
    var frames = {}, nodes = {}, byId = {};
    instances.forEach(function (it) { byId[it.id] = it; });
    var view = { el: vp, onZoom: null, frames: frames, nodes: nodes, rows: rows, instances: instances };
    view.order = instances.map(function (it) { return it.id; });
    view.inst = function (id) { return byId[id] || null; };
    view.instancesOf = function (slug) { return instances.filter(function (it) { return it.slug === slug; }); };
    view.resolve = function (idOrSlug) { if (byId[idOrSlug]) return byId[idOrSlug]; return view.instancesOf(idOrSlug)[0] || null; };

    // ---- 배치 상수 (월드 px) ----
    var W = HX.frame.w * NS, FH = HX.frame.h * NS, GAP = Math.max(240, Math.round(W * 0.75)), LEFT = 96, RIGHT = 160, PADT = 120, PADB = 160;
    var PITCH = W + GAP, worldW = 0, worldH = 0;
    world.style.setProperty("--hx-gap", GAP + "px");

    // ---- 행 · 노드 ----
    var dragged = false;
    rows.forEach(function (R, ri) {
      R.el = HX.el("div", { class: "hx-wf-row" + (ri % 2 ? " hx-wf-alt" : "") + (R.kind === "other" ? " hx-wf-other" : ""), dataset: { row: R.key } });
      var f = R.flow;
      R.head = HX.el("div", { class: "hx-wf-head" }, R.kind === "other"
        ? [HX.el("span", { class: "hx-wf-num", text: "흐름에 안 나오는 화면" }), HX.el("span", { class: "hx-wf-meta", text: "화면 " + R.insts.length + "개" })]
        : [HX.el("span", { class: "hx-wf-num", text: "흐름 " + R.n }), HX.el("b", { class: "hx-wf-name", text: f.name || R.key }),
          HX.el("span", { class: "hx-wf-meta" }, [HX.el("span", { class: "hx-tag hx-role", text: HX.roleLabel(f.role) }), " " + R.K + "단계"])]);
      rail.appendChild(R.head);
      R.insts.forEach(function (it) {
        var s = HX.bySlug[it.slug];
        var outSt = it.outStep != null ? f.steps[it.outStep] : null;
        var head = HX.el("div", { class: "hx-node-head" }, [HX.badge(s.id), HX.el("span", { class: "hx-node-name", text: s.name }),
          it.same ? HX.el("span", { class: "hx-node-same", text: "같은 화면" }) : null,
          s.state && HX.stateLabel ? HX.el("span", { class: "hx-tag hx-state", text: HX.stateLabel(s.state) }) : null,
          HX.el("span", { class: "hx-node-tags" })]);
        var node = HX.el("div", { class: "hx-node", role: "button", tabindex: "0", "aria-label": s.id + " " + s.name, dataset: { screen: s.slug, inst: it.id },
          style: "left:" + (LEFT + it.pos * PITCH) + "px;top:" + PADT + "px;width:" + W + "px" }, head);
        frames[it.id] = HX.mountFrame(s.slug, node, { scale: NS, fullHeight: !!opts.fullHeight, triggers: outSt && outSt.trigger ? [outSt.trigger] : null,
          onRegionHover: opts.onRegionHover ? function (r, on) { opts.onRegionHover(s.slug, r, on, it.id); } : null,
          onRegionClick: opts.onRegionClick ? function (r) { if (!dragged) opts.onRegionClick(s.slug, r, it.id); } : null });
        if (it.first) node.appendChild(HX.el("div", { class: "hx-node-purpose", text: s.purpose || " ", title: s.purpose }));
        node.addEventListener("click", function () { if (!dragged && opts.onNodeClick) opts.onNodeClick(s.slug, it.id); });
        node.addEventListener("dblclick", function (e) { if (opts.onNodeDblClick) { e.preventDefault(); opts.onNodeDblClick(s.slug, it.id); } });
        node.addEventListener("keydown", function (e) {
          if ((e.key === "Enter" || e.key === " ") && e.target === node) { e.preventDefault(); if (opts.onNodeClick) opts.onNodeClick(s.slug, it.id); }
        });
        nodes[it.id] = node; R.el.appendChild(node);
      });
      R.w = LEFT + Math.max(1, R.insts.length) * PITCH - GAP + RIGHT;
      world.appendChild(R.el);
    });

    // ---- 시나리오 범위 (칩) ----
    // 기본 = 전체(모든 시나리오를 한 캔버스에). opts.scope에 숫자를 주면 그 시나리오만
    var scope = rows.length && typeof opts.scope === "number" ? HX.clamp(opts.scope, 0, rows.length - 1) : null, chipEls = [];
    function chip(label, idx, title) {
      var b = HX.el("button", { type: "button", class: "hx-wf-chip", role: "tab", title: title || null, onclick: function () { view.setScope(idx, { fit: true, user: true }); } }, label);
      chipEls.push({ el: b, idx: idx }); chipBar.appendChild(b);
    }
    if (rows.length > 1) chip([HX.icon("#i-layout-grid"), "전체 흐름"], null); else chipBar.style.display = "none";
    rows.forEach(function (R, ri) {
      if (R.kind === "other") chip([HX.el("b", { text: "+" }), "그 밖의 화면"], ri);
      else chip([HX.el("b", { text: String(R.n) }), HX.shortName(R.flow.name || R.key, 20)], ri, R.flow.name);
    });
    var STORY = opts.story !== false && rows.length > 1;   // scope === null 이면 전체 흐름(카드)을 보여준다
    function visible(R, ri) { return scope === null ? !STORY : scope === ri; }
    function paintScope() {
      rows.forEach(function (R, ri) { R.el.style.display = R.head.style.display = visible(R, ri) ? "" : "none"; });
      vp.classList.toggle("hx-mode-story", STORY && scope === null);
      chipEls.forEach(function (c) { var on = c.idx === scope; c.el.classList.toggle("hx-on", on); c.el.setAttribute("aria-selected", on ? "true" : "false"); });
    }
    view.scope = function () { return scope; };
    view.visibleRows = function () { return rows.filter(visible); };
    view.visibleOrder = function () { return instances.filter(function (it) { return visible(rows[it.row], it.row); }).map(function (it) { return it.id; }); };
    view.isVisible = function (id) { var it = byId[id]; return !!it && visible(rows[it.row], it.row); };
    view.setScope = function (idx, o) {
      o = o || {}; scope = idx == null ? null : HX.clamp(idx, 0, rows.length - 1);
      paintScope(); layoutWorld(); view.drawEdges();
      if (STORY && scope === null && view.story) view.story.show();
      else if (o.fit !== false) view.fitWidth();
      HX.relayout();
      if (opts.onScope && o.silent !== true) opts.onScope(scope, o);
    };

    /* 행 높이 = 그 행에서 가장 긴 노드 (fullHeight로 늘어난 프레임 반영). 보이는 행만 위에서부터 쌓는다 */
    function layoutWorld() {
      var y = 0; worldW = 0;
      rows.forEach(function (R, ri) {
        if (!visible(R, ri)) return;
        var maxH = 0;
        R.insts.forEach(function (it) { maxH = Math.max(maxH, nodes[it.id].offsetHeight); });
        R.top = y; R.h = PADT + (maxH || FH + 24) + PADB;
        R.el.style.top = y + "px"; R.el.style.height = R.h + "px"; y += R.h; worldW = Math.max(worldW, R.w);
      });
      worldW = Math.max(worldW, 400); worldH = Math.max(1, y);
      rows.forEach(function (R) { R.el.style.width = worldW + "px"; });
      world.style.width = worldW + "px"; world.style.height = worldH + "px"; svg.setAttribute("width", worldW); svg.setAttribute("height", worldH);
    }
    function nodeBox(id) {
      var it = byId[id], R = rows[it.row], n = nodes[id];
      return { x: LEFT + it.pos * PITCH, y: (R.top || 0) + PADT, w: W, h: n.offsetHeight || FH };
    }
    function frameBox(id) {
      var nb = nodeBox(id), fe = frames[id].el;
      return { x: nb.x + fe.offsetLeft, y: nb.y + fe.offsetTop, w: fe.offsetWidth || W, h: fe.offsetHeight || FH, cl: fe.clientLeft || 0, ct: fe.clientTop || 0 };
    }
    view.nodeBox = nodeBox;
    view._int = { chipBar: chipBar, rail: rail, vp: vp, world: world, svg: svg, edgeLayer: edgeLayer, pillLayer: pillLayer, tip: tip, rows: rows, frameBox: frameBox, nodeBox: nodeBox,
      layoutWorld: layoutWorld, visible: function (R) { return visible(R, rows.indexOf(R)); },
      dims: function () { return { W: W, FH: FH, GAP: GAP, worldW: worldW, worldH: worldH, PADT: PADT }; },
      setDragged: function (v) { dragged = v; }, isDragged: function () { return dragged; } };
    paintScope(); layoutWorld();
    HX.mapEdges(view, opts);
    HX.mapZoom(view, opts);
    if (HX.buildStory && STORY) { HX.buildStory(view); if (scope === null) view.story.show(); }
    if (container) container.appendChild(vp);
    return view;
  };
})();
