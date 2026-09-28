/* 10-final.js — final 모드: 상단 바 + 탭 [화면 전체][사용 흐름].
   화면 전체 = 11-final-all.js (Figma 페이지처럼 모든 화면 대지, 누르면 screens/NN-slug.html 독립 완성본).
   사용 흐름 = 05~07의 전체 흐름 카드 → 카드를 누르면 두 장씩 넘겨 보기(←/→, 아래 이전·다음).
   (예전 [따라가기] 탭은 사용 흐름의 두 장씩 보기와 역할이 겹쳐 뺐다 — buildFollow 코드는 남겨 둠) */
(function () {
  "use strict";
  var HX = window.HX, doc = document;
  var FINAL = HX.final = {};
  var NODE_SCALE = HX.platform === "mobile" ? 0.35 : 0.22;

  FINAL.start = function (app) {
    app.classList.add("hx-app"); app.classList.add("hx-final");
    var views = { all: FINAL.buildAll(), map: FINAL.buildMap() };
    FINAL.views = views;
    var tabBtns = {}, current = null;
    var zoomVal = HX.el("span", { class: "hx-zoom-val", text: "100%" });
    var zoomGroup = HX.el("div", { class: "hx-group" }, [
      HX.btn("", { cls: "hx-icon-btn", aria: "축소", title: "축소", icon: HX.icon("#i-zoom-out"), onclick: function () { views.map.zoomBy(1 / 1.25); } }),
      zoomVal,
      HX.btn("", { cls: "hx-icon-btn", aria: "확대", title: "확대", icon: HX.icon("#i-zoom-in"), onclick: function () { views.map.zoomBy(1.25); } }),
      HX.btn("맞춤", { title: "전체가 보이게", icon: HX.icon("#i-maximize-2"), onclick: function () { views.map.fit(); } })
    ]);
    views.map.onZoom = function (z) { zoomVal.textContent = Math.round(z * 100) + "%"; };
    var tablist = HX.el("div", { class: "hx-tabs", role: "tablist", "aria-label": "보기" });
    [["all", "화면 전체", HX.icon("#i-layout-grid")], ["map", "사용 흐름", HX.icon("#i-workflow")]].forEach(function (t) {
      var b = HX.el("button", { type: "button", class: "hx-tab", role: "tab", id: "hx-tab-" + t[0], "aria-selected": "false", tabindex: "-1", onclick: function () { select(t[0]); } }, [t[2], t[1]]);
      tabBtns[t[0]] = b; tablist.appendChild(b);
    });
    tablist.addEventListener("keydown", function (e) {
      if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
      var ks = Object.keys(tabBtns), i = ks.indexOf(current);
      e.preventDefault(); select(ks[(i + (e.key === "ArrowRight" ? 1 : ks.length - 1)) % ks.length]); tabBtns[current].focus();
    });
    app.appendChild(HX.el("div", { class: "hx-bar" }, [
      HX.el("div", { class: "hx-bar-title" }, [HX.meta.title || HX.meta.project || "화면 지도", HX.el("small", { text: "화면 " + HX.data.screens.length + " · 흐름 " + HX.data.flows.length })]),
      tablist, HX.el("span", { class: "hx-bar-spacer" }), zoomGroup
    ]));
    Object.keys(views).forEach(function (k) { views[k].el.style.display = "none"; views[k].el.setAttribute("role", "tabpanel"); views[k].el.setAttribute("aria-labelledby", "hx-tab-" + k); app.appendChild(views[k].el); });
    function select(name) {
      if (current === name) return;
      current = name;
      Object.keys(views).forEach(function (k) {
        var on = k === name; views[k].el.style.display = on ? "" : "none";
        tabBtns[k].setAttribute("aria-selected", on ? "true" : "false"); tabBtns[k].tabIndex = on ? 0 : -1;
        if (on && views[k].onShow) views[k].onShow(); else if (!on && views[k].onHide) views[k].onHide();
      });
      zoomGroup.style.display = name === "map" ? "" : "none";
      try { history.replaceState(null, "", "#" + name); } catch (e) { /* file:// */ }
    }
    FINAL.select = select;
    select(location.hash === "#map" ? "map" : "all");
    doc.addEventListener("keydown", function (e) {
      var t = e.target, typing = t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.isContentEditable);
      if (typing || doc.querySelector(".hx-modal")) return;
      if (views[current].onKey) views[current].onKey(e);
    });
  };

  // ================= 지도 (05-map.js 공용) =================
  FINAL.buildMap = function () {
    var cur = null, V;
    function info(id) {
      var it = V.inst(id), R = it && V.rows[it.row]; if (!R) return "";
      return (R.kind === "other" ? "흐름에 안 나오는 화면" : "흐름 " + R.n + " · " + (it.done ? R.K + "단계 중 " + it.done + "단계" : "첫 화면")) + " · " + HX.bySlug[it.slug].name;
    }
    function go(id) { cur = id; V.focusNode(id, { animate: true, pair: true }); paint(); }
    function stepBy(d) {
      if (V.scope() === null) { if (d > 0 && V.rows[0]) { V.setScope(0, { fit: false, silent: true }); go(V.rows[0].insts[0].id); } return; }
      var ord = V.visibleOrder(), i = ord.indexOf(cur) + d;
      if (i >= 0 && i < ord.length) return go(ord[i]);
      var ri = V.scope() + d;                             // 흐름 끝 → 다음(이전) 흐름으로
      if (ri >= 0 && ri < V.rows.length) { V.setScope(ri, { fit: false, silent: true }); var ins = V.rows[ri].insts; go(ins[d > 0 ? 0 : ins.length - 1].id); }
    }
    V = HX.buildMap(null, { nodeScale: NODE_SCALE, fullHeight: true, wheelPan: true,
      // 흐름 속 화면을 누르면 화면 전체 캔버스에서 그 화면으로 (한 파일 안에서만 이동)
      onNodeClick: function (slug) { FINAL.select("all"); FINAL.views.all.focus(slug); },
      onScope: function (sc, o) { if (sc !== null && o && o.user) { go(V.rows[sc].insts[0].id); } else if (sc === null) { cur = null; paint(); } } });
    var prev = HX.btn("이전", { icon: HX.icon("#i-chevron-left"), onclick: function () { stepBy(-1); } });
    var next = HX.btn("다음", { onclick: function () { stepBy(1); } }); next.appendChild(HX.icon("#i-chevron-right"));
    var label = HX.el("span", { class: "hx-bd-count" });
    var all = HX.btn("전체 흐름", { icon: HX.icon("#i-layout-grid"), onclick: function () { V.setScope(null, { user: true }); } });
    V.el.appendChild(HX.el("div", { class: "hx-bd-nav" }, [prev, label, next, HX.el("span", { class: "hx-bd-nav-sep" }), all]));
    function paint() {
      label.textContent = cur ? info(cur) : "전체 흐름 · 흐름 " + V.rows.length + "개 · 카드를 누르거나 → 로 시작";
      all.style.display = V.scope() === null ? "none" : "";
    }
    paint();
    V.onKey = function (e) {
      if (e.key === "ArrowRight") { e.preventDefault(); stepBy(1); }
      else if (e.key === "ArrowLeft") { e.preventDefault(); stepBy(-1); }
      else if (e.key === "Escape") { V.setScope(null, { user: true }); }
    };
    V.showFlow = function (fi) { V.setScope(fi, { fit: false, silent: true }); go(V.rows[fi].insts[0].id); };
    return V;
  };
})();

/* ================= 따라가기 ================= */
(function () {
  "use strict";
  var HX = window.HX, FINAL = HX.final;
  FINAL.buildFollow = function () {
    var el = HX.el("div", { class: "hx-follow" });
    var view = { el: el };
    var flows = HX.data.flows;
    if (!flows.length) { el.appendChild(HX.el("div", { class: "hx-empty", text: "플로우가 없어요. flow.json에 steps를 적어 주세요." })); return view; }
    var chips = HX.el("div", { class: "hx-flow-chips", role: "tablist", "aria-label": "플로우 선택" });
    var stage = HX.el("div", { class: "hx-follow-stage" });
    var caption = HX.el("div", { class: "hx-caption", "aria-live": "polite" });
    var counter = HX.el("span", { class: "hx-counter" });
    var dots = HX.el("div", { class: "hx-dots", "aria-label": "진행" });
    var prev = HX.btn("이전", { title: "이전 (←)", icon: HX.icon("#i-chevron-left"), onclick: function () { go(step - 1); } });
    var next = HX.btn("다음", { cls: "hx-primary", title: "다음 (→)", onclick: function () { go(step + 1); } });
    next.appendChild(HX.icon("#i-chevron-right"));
    el.appendChild(chips); el.appendChild(stage);
    el.appendChild(HX.el("div", { class: "hx-follow-foot" }, [prev, caption, dots, counter, next]));

    var fi = 0, step = 0, frame = null, chipEls = [], dotEls = [];
    flows.forEach(function (f, i) {
      var c = HX.el("button", { type: "button", class: "hx-chip", role: "tab", "aria-selected": "false", onclick: function () { selectFlow(i); } }, [
        f.name, f.role ? HX.el("small", { text: HX.roleLabel(f.role) }) : null, HX.el("small", { text: (f.steps || []).length + "단계" })]);
      chipEls.push(c); chips.appendChild(c);
    });
    function selectFlow(i) {
      fi = i; step = 0;
      chipEls.forEach(function (c, j) { c.classList.toggle("hx-on", j === i); c.setAttribute("aria-selected", j === i ? "true" : "false"); });
      dots.innerHTML = ""; dotEls = [];
      var N = (flows[fi].steps || []).length;
      for (var k = 0; k <= N; k++) (function (k) {
        var d = HX.el("button", { type: "button", class: "hx-dot", title: k < N ? (k + 1) + "단계" : "끝", "aria-label": k < N ? (k + 1) + "단계" : "끝", onclick: function () { go(k); } });
        dotEls.push(d); dots.appendChild(d);
      })(k);
      render();
    }
    function go(i) { var N = (flows[fi].steps || []).length; if (i < 0 || i > N) return; step = i; render(); }
    function render() {
      var f = flows[fi], steps = f.steps || [], N = steps.length;
      var st = step < N ? steps[step] : null;
      var slug = st ? st.from : (N ? steps[N - 1].to : null);
      if (frame) { frame.destroy(); frame = null; }
      if (slug) {
        frame = HX.mountFrame(slug, stage, { fit: "contain", maxScale: 1, pad: 16, fitTo: stage, triggers: st && st.trigger ? [st.trigger] : null });
        if (st) frame.spotlight(st.region, st.trigger);
      }
      caption.innerHTML = "";
      if (st) {
        var from = HX.bySlug[st.from], to = HX.bySlug[st.to];
        var reg = from ? from.regions.filter(function (r) { return r.key === st.region; })[0] : null;
        HX.append(caption, [HX.el("b", { text: st.action }), " ", HX.el("span", { class: "hx-arrow-to", text: "→ " + (to ? to.name : st.to) }),
          HX.el("span", { class: "hx-caption-sub", text: (from ? from.name : st.from) + (reg ? " · " + reg.id + " " + reg.label : "") })]);
        counter.textContent = (step + 1) + " / " + N;
      } else {
        var last = N ? HX.bySlug[steps[N - 1].to] : null;
        HX.append(caption, ["끝 — ", HX.el("b", { text: last ? last.name : "" }), HX.el("span", { class: "hx-caption-sub", text: "'" + f.name + "' 플로우가 여기서 끝나요. ← 로 되돌아가거나 다른 플로우를 골라 주세요." })]);
        counter.textContent = "끝";
      }
      prev.disabled = step === 0; next.disabled = step === N;
      dotEls.forEach(function (d, i) { d.classList.toggle("hx-on", i === step); d.classList.toggle("hx-done", i < step); });
    }
    view.onKey = function (e) {
      if (e.key === "ArrowRight") { e.preventDefault(); go(step + 1); }
      else if (e.key === "ArrowLeft") { e.preventDefault(); go(step - 1); }
      else if (e.key === "Home") { e.preventDefault(); go(0); }
      else if (e.key === "End") { e.preventDefault(); go((flows[fi].steps || []).length); }
    };
    view.onShow = function () { requestAnimationFrame(HX.relayout); };
    view.selectFlow = function (i) { selectFlow(i); go(0); };
    selectFlow(0);
    return view;
  };
})();
