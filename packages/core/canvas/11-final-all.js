/* 11-final-all.js — 최종본의 [화면 전체] 탭: Figma 캔버스처럼 모든 화면을 실제 크기 대지로 놓고 확대·축소·이동한다.
   역할별 구역(자녀 / 부모님 / 함께 쓰는 화면), 한 줄에 4장, 흐름에 나오는 순서.
   - Ctrl/⌘+휠 또는 −/+ : 확대·축소   · 휠·드래그 : 이동   · 0 또는 '전체 보기' : 모두 보이게
   - 대지를 누르면 그 화면으로 크게 다가간다
   (다른 파일로 가는 링크는 두지 않는다 — macOS에서 Chrome 폴더 권한이 없으면 '파일 액세스 거부됨'이 나온다) */
(function () {
  "use strict";
  var HX = window.HX, FINAL = HX.final;
  if (!FINAL) return;
  function roleName(role) { var l = HX.roleLabel(role).replace(/\(.*\)/, ""); return l === "부모" ? "부모님" : l; }
  FINAL.pageOf = function (slug) { return (HX.data.pages || {})[slug] || null; };

  var MOBILE = HX.platform === "mobile";
  var COLS = MOBILE ? 8 : 4, GX = MOBILE ? 80 : 200, GY = MOBILE ? 140 : 260, SEC = MOBILE ? 200 : 360, PAD = MOBILE ? 120 : 200;

  FINAL.buildAll = function () {
    var pages = HX.data.pages || {};
    var ord = Object.keys(pages);
    HX.data.screens.forEach(function (s) { if (ord.indexOf(s.slug) < 0) ord.push(s.slug); });
    var W = HX.frame.w;

    var vp = HX.el("div", { class: "hx-cv", tabindex: "0", "aria-label": "화면 전체 캔버스" });
    var world = HX.el("div", { class: "hx-cv-world" });
    vp.appendChild(world);
    var zoomVal = HX.el("span", { class: "hx-zoom-val", text: "100%" });
    var tools = HX.el("div", { class: "hx-cv-tools" }, [
      HX.btn("", { cls: "hx-icon-btn", aria: "축소", title: "축소 (−)", icon: HX.icon("#i-zoom-out"), onclick: function () { zoomBy(1 / 1.25); } }), zoomVal,
      HX.btn("", { cls: "hx-icon-btn", aria: "확대", title: "확대 (+)", icon: HX.icon("#i-zoom-in"), onclick: function () { zoomBy(1.25); } }),
      HX.btn("전체 보기", { icon: HX.icon("#i-maximize-2"), title: "모두 보이게 (0)", onclick: function () { fit(true); } }),
      HX.el("span", { class: "hx-cv-hint", text: "⌘/Ctrl+휠 확대 · 드래그로 이동 · 화면을 누르면 크게" })]);
    tools.addEventListener("pointerdown", function (e) { e.stopPropagation(); });
    vp.appendChild(tools);

    // ---- 구역 · 대지 ----
    var roleKeys = HX.meta.roles.map(function (r) { return r.key; });
    var groups = HX.meta.roles.map(function (r) { return { key: r.key, label: roleName(r.key) }; }).concat([{ key: null, label: "함께 쓰는 화면" }]);
    var secs = [], boards = [];
    groups.forEach(function (g) {
      var mine = ord.filter(function (slug) { var s = HX.bySlug[slug]; return g.key === null ? (!s.role || roleKeys.indexOf(s.role) < 0) : s.role === g.key; });
      if (!mine.length) return;
      var title = HX.el("div", { class: "hx-cv-sec" }, [HX.el("b", { text: g.label }), HX.el("span", { text: mine.length + "개" })]);
      world.appendChild(title);
      var sec = { title: title, boards: [] };
      mine.forEach(function (slug) {
        var s = HX.bySlug[slug], n = ord.indexOf(slug) + 1, href = pages[slug];
        var label = HX.el("div", { class: "hx-cv-label" }, [HX.el("span", { class: "hx-cv-n", text: String(n).padStart(2, "0") }), HX.el("b", { text: s.name }),
          s.state && HX.stateLabel ? HX.el("span", { class: "hx-tag hx-state", text: HX.stateLabel(s.state) }) : null]);
        var box = HX.el("div", { class: "hx-cv-board", dataset: { screen: slug }, style: "width:" + W + "px" });
        world.appendChild(label); world.appendChild(box);
        var b = { slug: slug, label: label, box: box, frame: null };
        box.addEventListener("click", function () { if (!dragged) focusBoard(b); });
        sec.boards.push(b); boards.push(b);
      });
      secs.push(sec);
    });

    // ---- 배치: 구역마다 한 줄에 4장, 줄 높이 = 그 줄에서 가장 긴 화면 ----
    var worldW = 0, worldH = 0;
    function layout() {
      var y = 0;
      secs.forEach(function (sec) {
        sec.title.style.left = "0px"; sec.title.style.top = y + "px"; y += SEC;
        for (var i = 0; i < sec.boards.length; i += COLS) {
          var row = sec.boards.slice(i, i + COLS), rowH = 0;
          row.forEach(function (b, c) {
            var x = c * (W + GX);
            b.label.style.left = x + "px"; b.label.style.top = (y - 14) + "px";
            b.box.style.left = x + "px"; b.box.style.top = y + "px";
            b.x = x; b.y = y; b.h = b.box.offsetHeight || HX.frame.h;
            rowH = Math.max(rowH, b.h);
          });
          y += rowH + GY;
        }
        y += PAD;
      });
      worldW = COLS * W + (COLS - 1) * GX; worldH = y;
      world.style.width = worldW + "px"; world.style.height = worldH + "px";
    }

    // ---- 확대·축소·이동 ----
    var z = 0.3, tx = 40, ty = 80, dragged = false, mounted = false;
    function apply(anim) {
      world.classList.toggle("hx-anim", !!anim);
      world.style.transform = "translate(" + tx + "px," + ty + "px) scale(" + z + ")";
      world.style.setProperty("--hx-inv", Math.max(1, Math.min(6, 1 / z)).toFixed(3));
      zoomVal.textContent = Math.round(z * 100) + "%";
    }
    function zoomAt(px, py, nz) { nz = HX.clamp(nz, 0.05, 2); tx = px - (px - tx) * (nz / z); ty = py - (py - ty) * (nz / z); z = nz; apply(); }
    function zoomBy(f) { zoomAt(vp.clientWidth / 2, vp.clientHeight / 2, z * f); }
    function fit(anim) {
      var vw = vp.clientWidth, vh = vp.clientHeight; if (!vw) return;
      z = HX.clamp((vw - 80) / worldW, 0.05, 1); tx = (vw - worldW * z) / 2; ty = 150; apply(anim);
    }
    function focusBoard(b) {
      var vw = vp.clientWidth, vh = vp.clientHeight;
      var nz = HX.clamp(Math.min((vw - 120) / W, (vh - 140) / Math.min(b.h, HX.frame.h * 1.4)), 0.1, 1);
      z = nz; tx = vw / 2 - (b.x + W / 2) * z; ty = 96 - b.y * z; apply(true);
    }
    vp.addEventListener("wheel", function (e) {
      e.preventDefault();
      var r = vp.getBoundingClientRect(), k = e.deltaMode === 1 ? 16 : 1;
      if (e.ctrlKey || e.metaKey) zoomAt(e.clientX - r.left, e.clientY - r.top, z * Math.exp(-e.deltaY * k * 0.01));
      else { tx -= e.deltaX * k; ty -= e.deltaY * k; apply(); }
    }, { passive: false });
    var drag = null;
    vp.addEventListener("pointerdown", function (e) { if (e.button !== 0 || e.target.closest("a")) return; drag = { x: e.clientX, y: e.clientY, tx: tx, ty: ty }; dragged = false; });
    window.addEventListener("pointermove", function (e) {
      if (!drag) return; var dx = e.clientX - drag.x, dy = e.clientY - drag.y;
      if (!dragged && Math.abs(dx) + Math.abs(dy) < 5) return;
      dragged = true; vp.classList.add("hx-dragging"); tx = drag.tx + dx; ty = drag.ty + dy; apply();
    });
    window.addEventListener("pointerup", function () { if (!drag) return; drag = null; vp.classList.remove("hx-dragging"); setTimeout(function () { dragged = false; }, 0); });

    HX.on("layout", function () { if (mounted && vp.clientWidth) layout(); });
    var pending = null;
    return {
      el: vp,
      focus: function (slug) {   // 사용 흐름에서 화면을 누르면 여기로 와서 그 화면에 다가간다
        var b = boards.filter(function (x) { return x.slug === slug; })[0]; if (!b) return;
        if (!mounted || !b.h) { pending = slug; return; }
        focusBoard(b);
      },
      onShow: function () {
        if (!mounted) {
          mounted = true;
          boards.forEach(function (b) { b.frame = HX.mountFrame(b.slug, b.box, { scale: 1, fullHeight: true, badges: false }); });
          requestAnimationFrame(function () { HX.relayout(); requestAnimationFrame(function () {
            layout(); fit(false);
            if (pending) { var p = boards.filter(function (x) { return x.slug === pending; })[0]; pending = null; if (p) focusBoard(p); }
          }); });
        } else requestAnimationFrame(HX.relayout);
      },
      onKey: function (e) {
        if (e.key === "+" || e.key === "=") zoomBy(1.25);
        else if (e.key === "-") zoomBy(1 / 1.25);
        else if (e.key === "0") fit(true);
      }
    };
  };
})();
