/* 22-board-canvas.js — board 진입: 상단바(화면 느낌 · 의견 보내기) · 사용 흐름 = 구역 보드(08-sections.js) · 표시 상태를 보드에 칠하기.
   사용 흐름은 이해하는 곳 — 화면을 누르면 화면 디자인 탭의 그 화면으로 가서 의견을 남긴다(24-board-screens.js). */
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
        HX.el("span", { class: "hx-look-t" }, [HX.el("b", { text: L.name }), L.why || L.font ? HX.el("small", { text: (L.why || "") + (L.font ? (L.why ? " · " : "") + "글꼴 " + L.font : "") }) : null]), isRec ? HX.el("span", { class: "hx-rec-tag", text: "추천" }) : null]);
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
  // ---------- 선택: 사용 흐름에서는 고르지 않는다 — 화면을 누르면 화면 디자인 탭으로 ----------
  B.hl = function () {};
  B.go = function () {};
  B.select = function (slug, key) {
    B.sel = { slug: null, key: null, inst: null };
    if (slug && HX.bySlug[slug] && B.showDesign) { B.showDesign(slug, key); return; }
    if (B.panel) B.panel.render();
  };
  B.overview = function () { if (B.view) B.view.fit(true); };

  // ---------- 표시 상태 → 구역 보드 이름표 ('고친 화면' · '뺌' · 메모) ----------
  B.paintMarks = function () {
    var st = B.state;
    HX.data.screens.forEach(function (s) {
      var ss = st.screens[s.id], tags = [], memo = ss ? B.one(ss.memo) : "";
      if (B.focus.indexOf(s.slug) >= 0) tags.push({ kind: "fixed", text: "고친 화면" });
      if (ss && ss.remove) tags.push({ kind: "removed", text: "뺌" });
      if (memo) tags.push({ kind: "memo", text: "메모", title: "메모: " + memo });
      B.view.mark(s.slug, tags);
    });
  };

  // ---------- 진입 ----------
  B.start = function (app) {
    app.classList.add("hx-app"); app.classList.add("hx-bd");
    var copyBtn = HX.btn("", { cls: "hx-primary hx-bd-copy", icon: HX.icon("#i-send"), title: "무엇이 전달되는지 확인하고 복사해요 (⌘/Ctrl+Shift+C)", onclick: function () { B.openSend(); } });
    var copyLabel = HX.el("span"); copyBtn.appendChild(copyLabel);
    var bar = HX.el("div", { class: "hx-bar hx-bd-bar" }, [
      HX.el("div", { class: "hx-bar-title", title: HX.meta.title || "" }, [HX.meta.title || HX.meta.project || "", HX.el("small", { text: "초안 " + (HX.meta.round || 1) })]),
      HX.el("div", { class: "hx-bd-ctls" }, [feelButton()]),
      HX.el("span", { class: "hx-bar-spacer" }),
      copyBtn
    ]);
    var canvas = HX.el("div", { class: "hx-bd-canvas" });
    B.panel = B.buildPanel(HX.el("span"));   // '전체'(질문·남긴 의견) — 화면 디자인 탭 오른쪽이 이 패널을 그대로 쓴다
    var main = HX.el("div", { class: "hx-bd-main" }, [canvas]);
    app.appendChild(bar); app.appendChild(main);

    B.view = HX.buildSections({ pickTitle: "눌러서 이 화면에 의견 남기기", onPick: function (slug) { if (B.showDesign) B.showDesign(slug); } });
    canvas.appendChild(B.view.el);

    // 코치 팁 (처음 한 번)
    if (!HX.storage.get("hx:board:coach2")) {
      var coach = HX.el("div", { class: "hx-bd-coach", role: "note" }, [
        HX.el("div", {}, [HX.el("b", { text: "이렇게 보세요" }),
          HX.el("ul", {}, [HX.el("li", { text: "구역(가입·홈 …)마다 화면이 사용하는 순서대로 왼쪽부터 놓여 있어요" }),
            HX.el("li", { text: "초록 화살표는 조건에 따라 길이 갈리는 곳이에요 · 화면 아래 검은 상자는 그 화면의 규칙이에요" }),
            HX.el("li", { text: "화면을 누르면 '화면 디자인'으로 가서 고치고 싶은 곳에 의견을 남길 수 있어요" })])]),
        HX.btn("", { cls: "hx-icon-btn", aria: "닫기", title: "닫기", icon: HX.icon("#i-x"), onclick: function () { B.closeCoach(); } })]);
      canvas.appendChild(coach);
      B.closeCoach = function () { if (coach.isConnected) coach.remove(); HX.storage.set("hx:board:coach2", 1); };
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
      if (!B.tab || B.tab() !== "flow") return;
      if (e.key === "Escape") { e.preventDefault(); B.closeCoach(); B.overview(); }
      else B.view.onKey(e);
    });

    // 두 탭: 사용 흐름(이해) / 화면 디자인(의견) — 24-board-screens.js
    if (B.buildDesign) B.buildDesign({ app: app, bar: bar, main: main, canvas: canvas });
    B.view.onShow();
    // 지난 라운드에 고친 화면이 있으면 그 화면에 다가간다
    if (B.focus.length) B.view.focus(B.focus[0]);
  };
})();
