/* 06-map-edges.js — HX.buildMap의 연결선(파란 단계 화살표 + 라벨 pill, 회색 "돌아와서" 점선)과 줌/팬/맞춤/포커스. 05-map.js가 호출한다. */
(function () {
  "use strict";
  var HX = window.HX, doc = document;
  var SVG = "http://www.w3.org/2000/svg";
  function svgEl(tag, attrs) { var e = doc.createElementNS(SVG, tag); Object.keys(attrs || {}).forEach(function (k) { e.setAttribute(k, attrs[k]); }); return e; }
  function r1(v) { return Math.round(v * 10) / 10; }
  function cubic(a, c1, c2, b, t) {
    var u = 1 - t;
    return { x: u * u * u * a.x + 3 * u * u * t * c1.x + 3 * u * t * t * c2.x + t * t * t * b.x, y: u * u * u * a.y + 3 * u * u * t * c1.y + 3 * u * t * t * c2.y + t * t * t * b.y };
  }

  // ================= 연결선 =================
  HX.mapEdges = function (view, opts) {
    var I = view._int, frames = view.frames, tip = I.tip, svg = I.svg;
    var links = []; I.rows.forEach(function (R) { R.links.forEach(function (L) { links.push(L); }); });
    var drawn = [], activeSlug = null;
    function midY(box, FH) { return box.y + Math.min(box.h, FH) / 2; }
    function geom(L) {
      var d0 = I.dims(), A = I.frameBox(L.a.id), B = I.frameBox(L.b.id), an = I.nodeBox(L.a.id), bn = I.nodeBox(L.b.id);
      var gx = (an.x + an.w + bn.x) / 2, b = { x: B.x, y: midY(B, d0.FH) }, a, viaTrig = false;
      if (L.kind === "back") {
        a = { x: A.x + A.w, y: midY(A, d0.FH) };
        return { d: "M" + r1(a.x) + "," + r1(a.y) + " L" + r1(b.x) + "," + r1(b.y), a: a, px: gx, py: (a.y + b.y) / 2 };
      }
      var fa = frames[L.a.id], st = L.step;
      var src = st.trigger ? fa.triggerRect(st.trigger) : null; viaTrig = !!src;
      if (!src && st.region) src = fa.regionRect(st.region);             // 폴백: 영역 bbox
      a = src ? { x: A.x + A.cl + src.x + src.w, y: A.y + A.ct + src.y + src.h / 2 } : { x: A.x + A.w, y: midY(A, d0.FH) };
      var dx = Math.max(40, (b.x - a.x) / 2), c1 = { x: a.x + dx, y: a.y }, c2 = { x: b.x - dx, y: b.y };
      // 라벨은 노드 사이 틈 한가운데, 곡선이 그 x를 지나는 높이에
      var lo = 0, hi = 1, p = cubic(a, c1, c2, b, 0.5);
      for (var k = 0; k < 24; k++) { var t = (lo + hi) / 2; p = cubic(a, c1, c2, b, t); if (p.x < gx) lo = t; else hi = t; }
      return { d: "M" + r1(a.x) + "," + r1(a.y) + " C" + r1(c1.x) + "," + r1(c1.y) + " " + r1(c2.x) + "," + r1(c2.y) + " " + r1(b.x) + "," + r1(b.y),
        a: a, px: gx, py: p.y, viaTrig: viaTrig, fa: fa };
    }
    function draw() {
      if (!I.vp.clientWidth) return;
      I.edgeLayer.innerHTML = ""; I.pillLayer.innerHTML = ""; drawn = [];
      links.forEach(function (L) {
        if (!I.visible(L.row) || !frames[L.a.id] || !frames[L.b.id]) return;
        var P = geom(L), back = L.kind === "back";
        var p = svgEl("path", { class: back ? "hx-link-back" : "hx-edge" + (P.viaTrig ? " hx-edge-trig" : ""), d: P.d, "marker-end": back ? "url(#hx-arrow-back)" : "url(#hx-arrow)" });
        var pill = HX.el("div", { class: "hx-wf-pill" + (back ? " hx-wf-pill-back" : ""), style: "left:" + r1(P.px) + "px;top:" + r1(P.py) + "px" },
          back ? "돌아와서" : [HX.el("b", { text: (L.index + 1) + "단계" }), HX.el("span", { class: "hx-pill-act", text: " · " + (L.step.action || "") })]);
        if (!back) pill.title = (L.index + 1) + "단계 · " + (L.step.action || "");
        I.edgeLayer.appendChild(p); I.pillLayer.appendChild(pill);
        var rec = { L: L, p: p, pill: pill, dot: null };
        if (!back) {
          var dot = svgEl("circle", { class: "hx-edge-dot", cx: r1(P.a.x), cy: r1(P.a.y), r: 4 });
          var hit = svgEl("path", { class: "hx-edge-hit", d: P.d });
          hit.addEventListener("mouseenter", function (ev) {
            svg.classList.add("hx-hover"); p.classList.add("hx-active"); pill.classList.add("hx-active");
            if (P.viaTrig) P.fa.highlightTrigger(L.step.trigger, true);
            showTip(L, ev);
          });
          hit.addEventListener("mousemove", moveTip);
          hit.addEventListener("mouseleave", function () {
            svg.classList.remove("hx-hover"); p.classList.remove("hx-active"); pill.classList.remove("hx-active");
            if (P.viaTrig) P.fa.highlightTrigger(L.step.trigger, false);
            tip.style.display = "none";
          });
          I.edgeLayer.appendChild(dot); I.edgeLayer.appendChild(hit); rec.dot = dot;
        }
        drawn.push(rec);
      });
      paintActive();
    }
    function showTip(L, ev) {
      var to = HX.bySlug[L.b.slug];
      tip.innerHTML = "";
      tip.appendChild(HX.el("div", {}, [HX.el("b", { text: L.step.action }), " → " + (to ? to.name : L.b.slug), HX.el("div", { class: "hx-tip-flow", text: "흐름 " + L.row.n + " · " + (L.flow.name || "") })]));
      tip.style.display = ""; moveTip(ev);
    }
    function moveTip(ev) { tip.style.left = Math.min(ev.clientX + 14, window.innerWidth - 340) + "px"; tip.style.top = (ev.clientY + 14) + "px"; }
    /* 선택한 화면(모든 복사본)에 닿는 화살표만 진하게 (보드용) */
    function paintActive() {
      svg.classList.toggle("hx-has-sel", !!activeSlug); I.pillLayer.classList.toggle("hx-has-sel", !!activeSlug);
      drawn.forEach(function (x) {
        var on = !!activeSlug && x.L.kind === "step" && (x.L.a.slug === activeSlug || x.L.b.slug === activeSlug);
        x.p.classList.toggle("hx-sel", on); x.pill.classList.toggle("hx-sel", on); if (x.dot) x.dot.classList.toggle("hx-sel", on);
      });
    }
    view.drawEdges = draw;
    view.setActiveNode = function (slug) { activeSlug = slug || null; paintActive(); };
    view.links = links;
  };

  // ================= 줌 · 팬 · 맞춤 · 포커스 =================
  HX.mapZoom = function (view, opts) {
    var I = view._int, vp = I.vp, world = I.world;
    var z = 1, tx = 0, ty = 0, mode = null, animT = 0;
    var pad = { l: 24, r: 24, t: 112, b: 16 };   // 위: 흐름 칩 + 흐름 제목
    Object.keys(opts.fitPad || {}).forEach(function (k) { pad[k] = opts.fitPad[k]; });
    function inv(cap) { return Math.max(1, Math.min(cap, 1 / z)); }
    function apply(anim) {
      if (anim) { vp.classList.add("hx-anim"); clearTimeout(animT); animT = setTimeout(function () { vp.classList.remove("hx-anim"); }, 260); }
      world.style.transform = "translate(" + tx + "px," + ty + "px) scale(" + z + ")";
      // 멀리서 봐도 이름·번호·라벨이 읽히게 (월드 배율의 역수, 상한)
      world.style.setProperty("--hx-inv", inv(7).toFixed(3));
      world.style.setProperty("--hx-inv-b", inv(4).toFixed(3));
      world.style.setProperty("--hx-inv-h", inv(7).toFixed(3));
      // 멀리서 볼 때 화살표 라벨은 "n단계"만 (마우스를 올리면 전체 문장)
      world.classList.toggle("hx-zoom-far", z < 0.42);
      if (view.onZoom) view.onZoom(z);
    }
    function zoomAt(px, py, nz) {
      nz = HX.clamp(nz, 0.05, 3); tx = px - (px - tx) * (nz / z); ty = py - (py - ty) * (nz / z); z = nz; mode = null; apply();
    }
    view.zoom = function () { return z; };
    view.zoomBy = function (f) { zoomAt(vp.clientWidth / 2, vp.clientHeight / 2, z * f); };
    view.fit = function (o) {
      var vw = vp.clientWidth, vh = vp.clientHeight; mode = "fit"; if (!vw || !vh) return;
      var d = I.dims(), aw = vw - pad.l - pad.r, ah = vh - pad.t - pad.b;
      z = HX.clamp(Math.min(aw / d.worldW, ah / Math.max(1, d.worldH)), 0.05, 1.5);
      tx = pad.l + Math.max(0, (aw - d.worldW * z) / 2); ty = pad.t + Math.max(0, (ah - d.worldH * z) / 2);
      apply(o && o.animate);
    };
    /* 가로 맞춤 + 위 정렬: 모든 열이 보이게, 세로가 넘치면 휠/드래그로 이동 */
    view.fitWidth = function (o) {
      var vw = vp.clientWidth, vh = vp.clientHeight; mode = "fitw"; if (!vw || !vh) return;
      var d = I.dims(), aw = vw - pad.l - pad.r, ah = vh - pad.t - pad.b;
      if (view.scope && view.scope() !== null) {
        // 시나리오 하나: 줄 높이에 맞춰 크게 보고, 넘치는 오른쪽은 가로로 넘겨 본다 (왼→오 읽기)
        z = HX.clamp(Math.min(ah / Math.max(1, d.worldH), 1), 0.05, 1);
        tx = pad.l + Math.max(0, (aw - d.worldW * z) / 2); ty = pad.t + Math.max(0, (ah - d.worldH * z) / 2);
      } else {
        // 전체 시나리오: 한 캔버스에 전부 들어오게 (가로·세로 모두 맞춤)
        z = HX.clamp(Math.min(aw / d.worldW, ah / Math.max(1, d.worldH)), 0.03, 1.2);
        tx = pad.l + Math.max(0, (aw - d.worldW * z) / 2); ty = pad.t + Math.max(0, (ah - d.worldH * z) / 2);
      }
      apply(o && o.animate);
    };
    /* 노드(인스턴스)가 뷰포트의 약 75%를 차지하도록 줌·팬. slug를 주면 그 화면의 첫 복사본 */
    /* o.pair: 지금 화면과 다음 화면 두 장을 나란히 (튜토리얼처럼 한 단계씩) */
    view.focusNode = function (idOrSlug, o) {
      o = o || {};
      var it = view.resolve(idOrSlug); if (!it || !view.nodes[it.id]) return;
      var vw = vp.clientWidth, vh = vp.clientHeight; mode = { id: it.id, pair: !!o.pair }; if (!vw || !vh) return;
      var nb = I.nodeBox(it.id), ah = vh - pad.t - pad.b, fw = 0.75;
      if (o.pair) {
        var nx = view.instances.filter(function (x) { return x.row === it.row && x.pos === it.pos + 1; })[0];
        if (nx && view.nodes[nx.id]) {
          var b2 = I.nodeBox(nx.id), y0 = Math.min(nb.y, b2.y), y1 = Math.max(nb.y + nb.h, b2.y + b2.h);
          nb = { x: nb.x, y: y0, w: b2.x + b2.w - nb.x, h: y1 - y0 };
        }
        fw = 0.94;
      }
      var nz = HX.clamp(Math.min(vw * fw / nb.w, ah * 0.84 / nb.h), 0.05, 3);
      var head = 34 * Math.max(1, Math.min(3, 1 / nz)), cy = nb.y - head + (nb.h + head) / 2;
      z = nz; tx = vw / 2 - (nb.x + nb.w / 2) * z; ty = pad.t + ah / 2 - cy * z;
      apply(o && o.animate);
    };
    /* 노드가 지금 뷰포트 안에 (대부분) 보이는지 */
    view.nodeInView = function (id) {
      if (!view.isVisible(id)) return false;
      var nb = I.nodeBox(id), vw = vp.clientWidth, vh = vp.clientHeight;
      var x0 = nb.x * z + tx, y0 = nb.y * z + ty, x1 = x0 + nb.w * z, y1 = y0 + Math.min(nb.h, I.dims().FH * 1.5) * z;
      return x0 >= -8 && y0 >= pad.t - 40 && x1 <= vw + 8 && y1 <= vh + 8;
    };
    view.reframe = function (o) { if (mode === "fit") view.fit(o); else if (mode === "fitw") view.fitWidth(o); else if (mode && mode.id) view.focusNode(mode.id, { animate: o && o.animate, pair: mode.pair }); };
    view.mode = function () { return mode; };

    vp.addEventListener("wheel", function (e) {
      if (vp.classList.contains("hx-mode-story")) return;   // 전체 흐름(카드 목록)은 보통 스크롤
      e.preventDefault();
      var k = e.deltaMode === 1 ? 16 : 1, r = vp.getBoundingClientRect();
      if (opts.wheelPan && !e.ctrlKey && !e.metaKey) {
        // 시나리오 하나를 볼 때는 세로 휠도 가로 이동 (왼→오로 넘겨 보기)
        var single = view.scope && view.scope() !== null && Math.abs(e.deltaX) < Math.abs(e.deltaY);
        if (single) tx -= e.deltaY * k; else { tx -= e.deltaX * k; ty -= e.deltaY * k; }
        mode = null; apply(); return;
      }
      zoomAt(e.clientX - r.left, e.clientY - r.top, z * Math.exp(-e.deltaY * k * (e.ctrlKey ? 0.01 : 0.0015)));
    }, { passive: false });
    var drag = null;
    vp.addEventListener("pointerdown", function (e) { if (e.button !== 0) return; drag = { x: e.clientX, y: e.clientY, tx: tx, ty: ty }; I.setDragged(false); });
    window.addEventListener("pointermove", function (e) {
      if (!drag) return; var dx = e.clientX - drag.x, dy = e.clientY - drag.y;
      if (!I.isDragged() && Math.abs(dx) + Math.abs(dy) < 5) return;
      I.setDragged(true); vp.classList.add("hx-dragging"); tx = drag.tx + dx; ty = drag.ty + dy; mode = null; apply();
    });
    window.addEventListener("pointerup", function () {
      if (!drag) return; drag = null; vp.classList.remove("hx-dragging");
      setTimeout(function () { I.setDragged(false); }, 0);
    });
    vp.addEventListener("keydown", function (e) {
      var step = 60, map = { ArrowLeft: [step, 0], ArrowRight: [-step, 0], ArrowUp: [0, step], ArrowDown: [0, -step] };
      if (map[e.key] && e.target === vp && opts.panKeys !== false) { e.preventDefault(); tx += map[e.key][0]; ty += map[e.key][1]; mode = null; apply(); }
      else if (e.key === "+" || e.key === "=") view.zoomBy(1.25); else if (e.key === "-") view.zoomBy(1 / 1.25); else if (e.key === "0") view.fitWidth();
    });

    // 프레임이 늘어나면(fullHeight) 행 높이 → 연결선 → 보던 자리(맞춤/포커스) 순으로 다시
    HX.on("layout", function () {
      if (!vp.clientWidth) return;
      I.layoutWorld(); view.drawEdges();
      if (mode) view.reframe(); else apply();
    });
    var shown = false;
    view.onShow = function () { requestAnimationFrame(function () { if (!shown) { shown = true; view.fitWidth(); } HX.relayout(); }); };
    view.onHide = function () { I.tip.style.display = "none"; };
  };
})();
