/* 10-final.js — final 모드: 상단 바 + 탭 [사용 흐름][화면 전체].
   사용 흐름 = 08-sections.js 구역 보드(큰 구역 → 단계 이름표 → 화면 나란히 · 조건 화살표 · 화면 아래 정책 메모). 처음 열리는 탭.
   화면 전체 = 11-final-all.js (모든 화면 대지를 역할별로, 누르면 크게).
   (예전 흐름 카드 → 두 장씩 따라가 보기는 구역 보드로 바꿨다 — 디자이너 보드처럼 주요 분기만 화살표) */
(function () {
  "use strict";
  var HX = window.HX, doc = document;
  var FINAL = HX.final = {};

  FINAL.start = function (app) {
    app.classList.add("hx-app"); app.classList.add("hx-final");
    var views = { map: HX.buildSections(), all: FINAL.buildAll() };
    FINAL.views = views;
    var tabBtns = {}, current = null;
    var tablist = HX.el("div", { class: "hx-tabs", role: "tablist", "aria-label": "보기" });
    [["map", "사용 흐름", HX.icon("#i-workflow")], ["all", "화면 전체", HX.icon("#i-layout-grid")]].forEach(function (t) {
      var b = HX.el("button", { type: "button", class: "hx-tab", role: "tab", id: "hx-tab-" + t[0], "aria-selected": "false", tabindex: "-1", onclick: function () { select(t[0]); } }, [t[2], t[1]]);
      tabBtns[t[0]] = b; tablist.appendChild(b);
    });
    tablist.addEventListener("keydown", function (e) {
      if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
      var ks = Object.keys(tabBtns), i = ks.indexOf(current);
      e.preventDefault(); select(ks[(i + (e.key === "ArrowRight" ? 1 : ks.length - 1)) % ks.length]); tabBtns[current].focus();
    });
    var nSec = (HX.data.sections || []).length;
    app.appendChild(HX.el("div", { class: "hx-bar" }, [
      HX.el("div", { class: "hx-bar-title" }, [HX.meta.title || HX.meta.project || "화면 지도", HX.el("small", { text: "화면 " + HX.data.screens.length + (nSec ? " · 구역 " + nSec : "") })]),
      tablist, HX.el("span", { class: "hx-bar-spacer" })
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
      try { history.replaceState(null, "", "#" + name); } catch (e) { /* file:// */ }
    }
    FINAL.select = select;
    select(location.hash === "#all" ? "all" : "map");
    doc.addEventListener("keydown", function (e) {
      var t = e.target, typing = t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.isContentEditable);
      if (typing || doc.querySelector(".hx-modal")) return;
      if (views[current].onKey) views[current].onKey(e);
    });
  };
})();
