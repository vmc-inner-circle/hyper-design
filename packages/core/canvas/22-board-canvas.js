/* 22-board-canvas.js — board 진입: 상단바 · 가운데 캔버스(HX.buildMap) · 오른쪽 패널 · 넘기기(←/→) · 표시 상태를 캔버스에 칠하기. */
(function () {
  "use strict";
  var HX = window.HX, doc = document, root = doc.documentElement, B = HX.board;
  B.sel = { slug: null, key: null, inst: null };

  // ---------- 상단바 컨트롤 ----------
  function segCtl(label, key, values, labels, onpick) {
    var btns = [];
    var seg = HX.el("div", { class: "hx-bd-seg", role: "group", "aria-label": label });
    values.forEach(function (v, i) {
      var isRec = v === B.REC[key];
      var b = HX.el("button", { type: "button", class: "hx-bd-seg-btn", title: isRec ? "추천" + (B.recWhy[key] ? " — " + B.recWhy[key] : "") : null,
        onclick: function () { onpick(v); sync(); } }, [labels[i], isRec ? HX.el("span", { class: "hx-rec-tag", text: "추천" }) : null]);
      btns.push(b); seg.appendChild(b);
    });
    function sync() { btns.forEach(function (b, i) { b.setAttribute("aria-pressed", values[i] === B.state[key] ? "true" : "false"); }); }
    sync();
    var tip = { theme: "화면 전체의 배경색과 분위기예요", type: "화면 글자와 버튼의 크기예요", accent: "가장 중요한 버튼과 지금 고른 메뉴에 쓰는 색이에요" }[key];
    return HX.el("div", { class: "hx-bd-ctl", title: tip || null }, [HX.el("span", { class: "hx-bd-ctl-l", text: label }), seg]);
  }
  // 분위기: PRD에 맞춰 만든 3개 (이름 + 배경·버튼 색 미리보기)
  function lookCtl() {
    var st = B.state, btns = [];
    var seg = HX.el("div", { class: "hx-bd-seg hx-bd-looks", role: "group", "aria-label": "분위기" });
    B.looks.forEach(function (L) {
      var isRec = L.id === B.REC.theme, sw = L.swatches[0] || { hex: "#999999" };
      var b = HX.el("button", { type: "button", class: "hx-bd-seg-btn hx-bd-look", title: L.name + (L.why ? " — " + L.why : "") + (isRec && B.recWhy.theme ? " (추천: " + B.recWhy.theme + ")" : ""),
        onclick: function () { st.theme = L.id; st.accent = B.fixSwatch(L.id, L.id === B.REC.theme ? B.REC.accent : ""); B.applyTheme(); sync(); B.rebuildSwatches(); } }, [
        HX.el("span", { class: "hx-look-dot", style: "background:" + L.bg + ";box-shadow:inset 0 0 0 1px rgba(0,0,0,.12)" }, HX.el("span", { style: "background:" + sw.hex })),
        HX.el("span", { class: "hx-look-t" }, [HX.el("b", { text: L.name }), L.why ? HX.el("small", { text: L.why }) : null]), isRec ? HX.el("span", { class: "hx-rec-tag", text: "추천" }) : null]);
      btns.push([b, L.id]); seg.appendChild(b);
    });
    function sync() { btns.forEach(function (x) { x[0].setAttribute("aria-pressed", x[1] === st.theme ? "true" : "false"); }); }
    sync();
    return HX.el("div", { class: "hx-bd-ctl", title: "화면 전체의 배경과 분위기예요" }, [HX.el("span", { class: "hx-bd-ctl-l", text: "분위기" }), seg]);
  }
  // 버튼 색: 고른 분위기에 어울리는 색 5개 (첫 번째가 추천)
  function swatchCtl() {
    var st = B.state, box = HX.el("div", { class: "hx-bd-swatches", role: "radiogroup", "aria-label": "버튼 색" }), name = HX.el("span", { class: "hx-bd-swname" });
    function build() {
      box.innerHTML = "";
      var L = B.look(st.theme), rec = B.fixSwatch(st.theme, st.theme === B.REC.theme ? B.REC.accent : "");
      L.swatches.forEach(function (sw) {
        var b = HX.el("button", { type: "button", class: "hx-sw", role: "radio", title: sw.name + (sw.id === rec ? " (추천" + (B.recWhy.accent && st.theme === B.REC.theme ? " — " + B.recWhy.accent : "") + ")" : ""), "aria-label": sw.name,
          style: "--sw:" + sw.hex, onclick: function () { st.accent = sw.id; B.applyTheme(); build(); } },
          sw.id === rec ? HX.el("span", { class: "hx-rec-tag", text: "추천" }) : null);
        b.setAttribute("aria-checked", sw.id === st.accent ? "true" : "false");
        box.appendChild(b);
      });
      name.textContent = B.swatch(st.theme, st.accent).name;
    }
    B.rebuildSwatches = build; build();
    return HX.el("div", { class: "hx-bd-ctl", title: "가장 중요한 버튼과 지금 고른 메뉴에 쓰는 색이에요" }, [HX.el("span", { class: "hx-bd-ctl-l", text: "버튼 색" }), box, name]);
  }
  function feelButton() {
    var ctls = themeControls();
    if (ctls.length === 1 && ctls[0].classList.contains("hx-bd-locked")) return ctls[0];   // 모두 확정이면 글자만
    var sum = HX.el("span", { class: "hx-feel-sum" });
    var pop = HX.el("div", { class: "hx-feel", role: "dialog", "aria-label": "화면 느낌 고르기" }, [
      HX.el("div", { class: "hx-feel-h" }, [HX.el("b", { text: "화면 느낌" }), HX.el("span", { text: "고르면 모든 화면에 바로 적용돼요" })])].concat(ctls));
    var btn = HX.btn("", { cls: "hx-feel-btn", title: "분위기 · 글자 크기 · 버튼 색 고르기", onclick: function (e) { e.stopPropagation(); toggle(!pop.classList.contains("hx-open")); } });
    btn.appendChild(HX.el("span", { class: "hx-feel-k", text: "화면 느낌" })); btn.appendChild(sum); btn.appendChild(HX.icon("#i-chevron-down", "icon icon-sm"));
    function paintSum() { sum.textContent = B.look(B.state.theme).name + " · " + B.TYPE_LABEL[B.state.type] + " · " + B.swatch(B.state.theme, B.state.accent).name; }
    function toggle(on) { pop.classList.toggle("hx-open", on); btn.setAttribute("aria-expanded", on ? "true" : "false"); }
    doc.addEventListener("click", function (e) { if (!pop.contains(e.target) && e.target !== btn) toggle(false); });
    doc.addEventListener("keydown", function (e) { if (e.key === "Escape") toggle(false); });
    HX.on("board-change", paintSum); paintSum();
    return HX.el("div", { class: "hx-feel-wrap" }, [btn, pop]);
  }
  function themeControls() {
    var st = B.state, out = [];
    B.rebuildSwatches = function () {};
    if (B.isLocked("theme") && B.isLocked("type") && B.isLocked("swatch")) return [HX.el("span", { class: "hx-bd-locked", text: "확정: " + B.lookLine() })];
    if (B.isLocked("theme")) out.push(HX.el("span", { class: "hx-bd-locked", text: "확정: 분위기 " + B.look(st.theme).name }));
    else out.push(lookCtl());
    if (B.isLocked("type")) out.push(HX.el("span", { class: "hx-bd-locked", text: "확정: 글자 크기 " + B.TYPE_LABEL[st.type] }));
    else out.push(segCtl("글자 크기", "type", ["normal", "large"], ["보통", "크게"], function (v) { st.type = v; B.applyTheme(); }));
    if (B.isLocked("swatch")) out.push(HX.el("span", { class: "hx-bd-locked", text: "확정: 버튼 색 " + B.swatch(st.theme, st.accent).name }));
    else out.push(swatchCtl());
    return out;
  }
  function flowToggle() {
    var on = true;
    var b = HX.btn("화살표", { cls: "hx-on", title: "단계 화살표·누르는 곳 표시/숨김", icon: HX.icon("#i-route"), onclick: function () {
      on = !on; root.classList.toggle("hx-hide-flow", !on); b.classList.toggle("hx-on", on); b.setAttribute("aria-pressed", on ? "true" : "false");
    } });
    b.setAttribute("aria-pressed", "true");
    return b;
  }

  // ---------- 선택 · 넘기기 (인스턴스 = 시나리오 행 안의 화면 복사본) ----------
  var byId = function (a, b) { return a.id - b.id; };
  /* slug 단위 표시(선택 링·번호 강조)는 그 화면의 모든 복사본에, "지금 보는 복사본"은 hx-node-cur */
  function paintSel() {
    var V = B.view, s = B.sel;
    V.instances.forEach(function (it) {
      var mine = it.slug === s.slug, fr = V.frames[it.id];
      V.nodes[it.id].classList.toggle("hx-node-sel", mine); V.nodes[it.id].classList.toggle("hx-node-cur", it.id === s.inst);
      Object.keys(fr.boxes).forEach(function (k) { var on = mine && k === s.key; fr.boxes[k].el.classList.toggle("hx-bbox-sel", on); fr.highlight(k, on); });
    });
    V.setActiveNode(s.slug);
  }
  B.hl = function (slug, key, on) { B.view.instancesOf(slug).forEach(function (it) { B.view.frames[it.id].highlight(key, on); }); };
  B.select = function (slug, key, o) {
    o = o || {}; var V = B.view, prev = B.sel, inst = null;
    if (slug && !HX.bySlug[slug]) return;
    if (slug) {
      var hit = o.inst && V.inst(o.inst);
      if (hit && hit.slug === slug) inst = hit.id;
      else if (prev.slug === slug && prev.inst) inst = prev.inst;
      else { var all = V.instancesOf(slug), vis = all.filter(function (it) { return V.isVisible(it.id); }); inst = ((vis[0] || all[0]) || {}).id || null; }
    }
    B.sel = { slug: slug || null, key: slug ? (key || null) : null, inst: inst };
    var switched = false;
    if (inst && !V.isVisible(inst)) { V.setScope(V.inst(inst).row, { fit: false, silent: true }); switched = true; }
    paintSel();
    if (inst && o.focus) V.focusNode(inst, { animate: o.animate !== false && !switched, pair: true });
    else if (inst && key && !V.nodeInView(inst)) V.focusNode(inst, { animate: !switched });
    else if (switched) V.fitWidth();
    if (!slug && o.fit) V.fitWidth({ animate: true });
    if (slug && (key || o.open) && B.openPanel) B.openPanel();   // 번호·화면을 눌렀을 때만 패널을 연다 (넘기기는 캔버스 넓게)
    B.panel.render();
    if (key) B.panel.scrollToRow(key);
    B.paintNav();
  };
  /* d=±1 다음 인스턴스. 보이는 범위(시나리오 하나 또는 전체) 끝에서는 이웃 시나리오로 넘어간다 */
  function nextInst(d, from, skipSlug) {
    var V = B.view, order = V.visibleOrder(), sc = V.scope(), i = order.indexOf(from), guard = 0;
    if (i < 0) i = d > 0 ? -1 : order.length;
    while (guard++ < 500) {
      i += d;
      if (i < 0 || i >= order.length) {
        if (sc === null) { var r0 = V.rows[d > 0 ? 0 : V.rows.length - 1]; if (!r0 || from) return null; var ins = r0.insts; return ins.length ? V.inst(ins[d > 0 ? 0 : ins.length - 1].id) : null; }
        sc += d; if (sc < 0 || sc >= V.rows.length) return null;
        order = V.rows[sc].insts.map(function (it) { return it.id; }); i = d > 0 ? -1 : order.length; continue;
      }
      var it = V.inst(order[i]);
      if (!skipSlug || it.slug !== skipSlug(it)) return it;
    }
    return null;
  }
  B.canGo = function (d) { return !!nextInst(d, B.sel.inst); };
  B.go = function (d) {
    var it = nextInst(d, B.sel.inst); if (!it) return;
    B.select(it.slug, null, { focus: true, inst: it.id });
  };
  /* 항목 집중: 같은 화면 안 영역 id 순, 끝이면 다음(이전) 화면의 첫(끝) 번호 */
  B.stepRegion = function (d) {
    var s = HX.bySlug[B.sel.slug]; if (!s) return;
    var regs = s.regions.slice().sort(byId), i = -1;
    regs.forEach(function (r, k) { if (r.key === B.sel.key) i = k; });
    var j = i + d;
    if (j >= 0 && j < regs.length) { B.select(s.slug, regs[j].key, { inst: B.sel.inst }); return; }
    var cur = B.sel.inst, it;
    while ((it = nextInst(d, cur, function () { return s.slug; }))) {
      var rs = HX.bySlug[it.slug].regions.slice().sort(byId);
      if (rs.length) { B.select(it.slug, (d > 0 ? rs[0] : rs[rs.length - 1]).key, { inst: it.id }); return; }
      cur = it.id;
    }
  };
  B.overview = function () { B.select(null, null); if (B.view.scope() !== null) B.view.setScope(null, { user: true }); else B.view.story && B.view.story.show(); B.paintNav(); };
  /* 인스턴스 맥락: 하단 바·패널 제목용 */
  B.instInfo = function (id) {
    var V = B.view, it = V.inst(id); if (!it) return null;
    var R = V.rows[it.row], s = HX.bySlug[it.slug], f = R.flow, steps = f ? f.steps || [] : [];
    var inSt = it.stepIndex != null ? steps[it.stepIndex] : null, outSt = it.outStep != null ? steps[it.outStep] : null;
    return { it: it, row: R, screen: s, flow: f, inStep: inSt, outStep: outSt,
      head: R.kind === "other" ? "흐름에 안 나오는 화면" : "흐름 " + R.n + " · " + (it.done ? R.K + "단계 중 " + it.done + "단계" : "첫 화면") };
  };

  // ---------- 표시 상태 → 캔버스 (slug 단위 → 모든 복사본) ----------
  B.paintMarks = function () {
    var V = B.view, st = B.state;
    V.instances.forEach(function (it) {
      var s = HX.bySlug[it.slug], node = V.nodes[it.id], fr = V.frames[it.id]; if (!s || !node || !fr) return;
      var ss = st.screens[s.id], removed = !!(ss && ss.remove), memo = ss ? B.one(ss.memo) : "";
      node.classList.toggle("hx-node-removed", removed);
      var tags = node.querySelector(".hx-node-tags"); tags.innerHTML = "";
      if (B.focus.indexOf(s.slug) >= 0) tags.appendChild(HX.el("span", { class: "hx-node-tag hx-t-fixed", text: "고친 화면" }));
      if (removed) tags.appendChild(HX.el("span", { class: "hx-node-tag hx-t-removed", text: "뺌" }));
      if (memo) tags.appendChild(HX.el("span", { class: "hx-node-memo", title: "메모: " + memo }, HX.icon("#i-message-circle", "icon icon-sm")));
      s.regions.forEach(function (r) {
        var b = fr.boxes[r.key]; if (!b) return;
        var rs = st.regions[r.id], v = rs ? rs.v : "like";
        b.el.classList.toggle("hx-mark-change", v === "change"); b.el.classList.toggle("hx-mark-remove", v === "remove");
        b.el.title = r.id + " " + r.label + (v === "change" ? " — 바꿔" + (B.one(rs.memo) ? ": " + B.one(rs.memo) : "") : v === "remove" ? " — 빼기" : "");
      });
    });
  };

  // ---------- 진입 ----------
  B.start = function (app) {
    app.classList.add("hx-app"); app.classList.add("hx-bd");
    var zoomVal = HX.el("span", { class: "hx-zoom-val", text: "100%" });
    var copyBtn = HX.btn("", { cls: "hx-primary hx-bd-copy", icon: HX.icon("#i-send"), title: "무엇이 전달되는지 확인하고 복사해요 (⌘/Ctrl+Shift+C)", onclick: function () { B.openSend(); } });
    var copyLabel = HX.el("span"); copyBtn.appendChild(copyLabel);
    var bar = HX.el("div", { class: "hx-bar hx-bd-bar" }, [
      HX.el("div", { class: "hx-bar-title", title: HX.meta.title || "" }, [HX.meta.title || HX.meta.project || "", HX.el("small", { text: "초안 " + (HX.meta.round || 1) })]),
      HX.el("div", { class: "hx-bd-ctls" }, [feelButton()]),
      HX.el("span", { class: "hx-bar-spacer" }),
      // 흐름을 따라갈 때만 쓰는 보기 도구 (전체 흐름 카드 목록에서는 숨김)
      HX.el("div", { class: "hx-bd-viewtools" }, [
        flowToggle(),
        HX.el("div", { class: "hx-group" }, [
          HX.btn("", { cls: "hx-icon-btn", aria: "축소", title: "축소", icon: HX.icon("#i-zoom-out"), onclick: function () { B.view.zoomBy(1 / 1.25); } }), zoomVal,
          HX.btn("", { cls: "hx-icon-btn", aria: "확대", title: "확대", icon: HX.icon("#i-zoom-in"), onclick: function () { B.view.zoomBy(1.25); } }),
          HX.btn("", { cls: "hx-icon-btn", aria: "맞춤", title: "화면에 맞춤 (0)", icon: HX.icon("#i-maximize-2"), onclick: function () { B.view.fitWidth({ animate: true }); } })])]),
      copyBtn
    ]);
    var canvas = HX.el("div", { class: "hx-bd-canvas" });
    var collapse = HX.btn("", { cls: "hx-icon-btn", aria: "닫기", title: "의견 창 닫기", icon: HX.icon("#i-chevron-right"), onclick: function () { setPanel(false); } });
    B.panel = B.buildPanel(collapse);
    var nAsk = ((HX.data.board && HX.data.board.ask) || []).length;
    var reopen = HX.btn("의견 남기기" + (nAsk ? " · 질문 " + nAsk + "개" : ""), { cls: "hx-bd-reopen", title: "의견 남기는 창 열기", icon: HX.icon("#i-chevron-left"), onclick: function () { setPanel(true); } });
    var main = HX.el("div", { class: "hx-bd-main" }, [canvas, B.panel.el]);
    app.appendChild(bar); app.appendChild(main);

    B.view = HX.buildMap(canvas, {
      nodeScale: HX.platform === "mobile" ? 0.6 : 0.5, fullHeight: true, wheelPan: true, panKeys: false, fitPad: { b: 72, t: 60 },
      onNodeClick: function (slug) { if (B.showDesign) B.showDesign(slug); },   // 흐름에서 화면을 누르면 화면 디자인 탭의 그 화면으로
      onNodeDblClick: function (slug) { HX.openScreen(slug); },
      onRegionClick: function (slug, r, id) { B.select(slug, r.key, { inst: id }); },
      onRegionHover: function (slug, r, on) { if (slug === B.sel.slug) B.panel.rowHover(r.key, on); },
      onScope: function (sc, o) {
        // 이야기를 고르면 첫 화면부터 두 장씩 (튜토리얼처럼)
        if (sc !== null && o && o.user) { var R = B.view.rows[sc], f = R && R.insts[0]; if (f) { B.select(f.slug, null, { inst: f.id, focus: true, animate: false }); return; } }
        if (B.sel.inst && !B.view.isVisible(B.sel.inst)) B.select(null, null); else B.paintNav();
      }
    });
    B.view.onZoom = function (z) { zoomVal.textContent = Math.round(z * 100) + "%"; };

    // 하단 넘기기 바
    var prev = HX.btn("이전", { title: "이전 단계 (←)", icon: HX.icon("#i-chevron-left"), onclick: function () { B.go(-1); } });
    var next = HX.btn("다음", { title: "다음 단계 (→)", onclick: function () { B.go(1); } }); next.appendChild(HX.icon("#i-chevron-right"));
    var count = HX.el("span", { class: "hx-bd-count" });
    var all = HX.btn("전체 흐름", { title: "전체 흐름으로 (Esc)", icon: HX.icon("#i-layout-grid"), onclick: B.overview });
    canvas.appendChild(HX.el("div", { class: "hx-bd-nav" }, [prev, count, next, HX.el("span", { class: "hx-bd-nav-sep" }), all]));
    canvas.appendChild(reopen);
    B.paintNav = function () {
      var V = B.view, info = B.sel.inst ? B.instInfo(B.sel.inst) : null, sc = V.scope();
      count.innerHTML = "";
      if (info) HX.append(count, [HX.el("b", { text: info.head }), " · " + info.screen.name]);
      else {
        var R = sc === null ? null : V.rows[sc];
        if (!R) HX.append(count, [HX.el("b", { text: "전체 흐름" }), " · 흐름 " + V.rows.length + "개 · 카드를 누르거나 → 로 시작"]);
        else HX.append(count, [HX.el("b", { text: R.kind === "other" ? "흐름에 안 나오는 화면" : "흐름 " + R.n }), " · 화면 " + V.visibleOrder().length + "개 · → 로 한 장씩"]);
      }
      prev.disabled = !B.canGo(-1); next.disabled = !B.canGo(1);
    };

    function setPanel(open, o) {
      o = o || {};
      if (main.classList.contains("hx-bd-collapsed") === !open) return;
      main.classList.toggle("hx-bd-collapsed", !open);
      if (o.persist !== false) HX.storage.set("hx:board:panel", open ? 1 : 0);
      if (o.focus !== false) { if (open) collapse.focus(); else reopen.focus(); }
      HX.relayout();
    }
    // 기본은 접힘 — 캔버스를 넓게. 번호·화면을 누르면 자동으로 열린다
    B.openPanel = function () { setPanel(true, { persist: false, focus: false }); };
    if (HX.storage.get("hx:board:panel") !== 1 || window.innerWidth < 900) main.classList.add("hx-bd-collapsed");

    // 코치 팁 (처음 한 번)
    if (!HX.storage.get("hx:board:coach")) {
      var coach = HX.el("div", { class: "hx-bd-coach", role: "note" }, [
        HX.el("div", {}, [HX.el("b", { text: "이렇게 보세요" }),
          HX.el("ul", {}, [HX.el("li", { text: "'사용 흐름'에서 흐름 카드를 눌러 화면이 어떻게 이어지는지 먼저 보세요" }),
            HX.el("li", { text: "파란 화살표가 '어디를 누르면 어디로 가는지' 알려 줘요 · ← →로 한 장씩" }),
            HX.el("li", { text: "의견은 위쪽 '화면 디자인'에서 남겨요 — 화면에서 고치고 싶은 곳을 누르면 돼요" })])]),
        HX.btn("", { cls: "hx-icon-btn", aria: "닫기", title: "닫기", icon: HX.icon("#i-x"), onclick: function () { B.closeCoach(); } })]);
      canvas.appendChild(coach);
      B.closeCoach = function () { if (coach.isConnected) coach.remove(); HX.storage.set("hx:board:coach", 1); };
    } else B.closeCoach = function () {};

    function paintCopy() {
      var n = B.diffCount();
      copyLabel.textContent = "의견 보내기" + (n ? " · " + n + "개" : "");
      copyBtn.title = n ? "지금까지 남긴 의견 " + n + "개 (추천과 다르게 고른 것 포함) — 눌러서 무엇이 전달되는지 확인해요"
        : "아직 남긴 의견이 없어요 — 이대로 보내면 모두 추천대로 진행해요";
    }
    HX.on("board-change", function () { B.paintMarks(); paintCopy(); });
    B.applyTheme();

    doc.addEventListener("keydown", function (e) {
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key.toLowerCase() === "c") { e.preventDefault(); B.openSend(); return; }
      var t = e.target, typing = t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.tagName === "SELECT" || t.isContentEditable);
      if (typing || doc.querySelector(".hx-modal") || e.metaKey || e.ctrlKey || e.altKey) return;
      if (e.key === "ArrowRight") { e.preventDefault(); B.closeCoach(); B.go(1); }
      else if (e.key === "ArrowLeft") { e.preventDefault(); B.closeCoach(); B.go(-1); }
      else if (e.key === "Escape") { e.preventDefault(); B.overview(); }
    });

    // 두 탭: 사용 흐름(이해) / 화면 디자인(의견) — 24-board-screens.js
    if (B.buildDesign) B.buildDesign({ app: app, bar: bar, main: main, canvas: canvas });
    // 처음: 지난 라운드에 고친 화면이 있으면 그 화면부터, 아니면 전체가 한눈에
    if (B.focus.length) B.select(B.focus[0], null, { focus: true, animate: false });
    else { B.view.fitWidth(); B.select(null, null); }
  };
})();
