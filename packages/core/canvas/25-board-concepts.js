/* 25-board-concepts.js — 시안 고르기. 1턴 보드(meta.stage = "concept")는 이 화면 하나뿐이다(B.startConcept).
   시안 10개 = 과감함 1~10단계 — 레이아웃 패턴(+섞은 패턴)과 꾸밈 카테고리(scripts/dress.js)가 단계마다 다르다. 시안마다 메인 화면 5~6장.
   사용자 결정(2026-10-14): "10개 다양한 것을 한 번에 다 보여주고 사용자는 색상만 선택", "안마다 메인 화면 5~6장",
     "그 초안처럼 캔버스에 다 보여주는 형태로" — 사용 흐름(08-sections.js)과 같은 캔버스 한 장:
     시안마다 한 줄 = 시안 띠(시안 X · 단계 · 이름 · 이유 · 화면 구성 · 꾸밈 · '이 안으로 할게요') → 화면 이름표 → 메인 화면 5~6장 나란히(화면 전체 길이, 보기만).
     화면 안 스크롤·밀기는 넣지 않는다 — 사용자: "스크롤이나 이런 거 그냥 없애자, 화면만 봐도 될 듯". 끌기·휠은 언제나 캔버스 이동, ↑↓ = 이전·다음 시안 줄.
     끌어서 이동 · ⌘/Ctrl+휠 확대 · 위쪽 도구 = 시안 바로가기(A~J) · 축소/확대 · 전체 보기. 화면 이름 옆 '크게 보기'.
   맨 위 고정 상단바 = 제목 · '색 바꾸기'(packages/core/color/picker.js — 고르면 모든 시안이 그 색으로) · 보내기.
   고른 뒤 흐름: 그 안 + 색 → 2턴 전체 화면 1차안 → 3턴 의견 반영 최종.
   다른 시안의 화면은 build.js가 "<시안 id>~<slug>" 섹션으로 싣고, 꾸밈은 화면 상자의 data-*(dress.css)로 입힌다.
   복사 글: "시안 <id>(이름)" + (색을 바꿨으면) "테마 …" (20-board.js) */
(function () {
  "use strict";
  var HX = window.HX, B = HX.board, doc = document;
  if (!B) return;
  var SHELL = { sidebar: "왼쪽 메뉴", top: "위쪽 탭 메뉴", rail: "아이콘 메뉴", tabbar: "아래 탭 메뉴", none: "메뉴 없이" };
  var DC = HX.data.dressCats || { cats: {}, base: {} };
  var KEYS = Object.keys(DC.cats);

  function frameKey(c, slug) { return B.stage !== "concept" && c.id === B.mainConcept ? slug : c.id + "~" + slug; }
  function full(d) { var o = {}; KEYS.forEach(function (k) { o[k] = (d && d[k]) || DC.base[k]; }); return o; }
  /* 꾸밈 → 화면 상자의 data-* (dress.css) + 아이콘(선 ↔ 입체: 스프라이트의 #i- ↔ #f-) */
  function dressBox(box, d) {
    KEYS.forEach(function (k) { if (k === "icons") return; if (d[k] && d[k] !== DC.base[k]) box.setAttribute("data-" + k, d[k]); else box.removeAttribute("data-" + k); });
    var fluent = d.icons === "fluent";
    box.querySelectorAll("use").forEach(function (u) {
      var h = u.getAttribute("href") || "";
      if (fluent && h.indexOf("#i-") === 0 && doc.getElementById("f-" + h.slice(3))) u.setAttribute("href", "#f-" + h.slice(3));
      else if (!fluent && h.indexOf("#f-") === 0) { var n = h.slice(3).replace(/-(filled|color)$/, ""); if (doc.getElementById("i-" + n)) u.setAttribute("href", "#i-" + n); }
    });
  }
  function levelText(c) { return c.level ? c.level + "단계" + (c.level <= 2 ? " · 무난" : c.level >= 9 ? " · 과감" : "") : ""; }
  function layoutText(c) { return [c.layout && c.layout.name, c.mix && c.mix.name].filter(Boolean).join(" + "); }

  function zoomModal(c, slug, title) {
    var close = HX.btn("", { cls: "hx-icon-btn", aria: "닫기", title: "닫기 (Esc)", icon: HX.icon("#i-x"), onclick: function () { done(); } });
    var box = HX.el("div", { class: "hx-cc-zoom-frame" });
    var m = HX.el("div", { class: "hx-modal hx-app" }, [HX.el("div", { class: "hx-modal-backdrop", onclick: function () { done(); } }),
      HX.el("div", { class: "hx-modal-panel", role: "dialog", "aria-modal": "true", "aria-label": title }, [
        HX.el("div", { class: "hx-modal-head" }, [HX.el("span", { class: "hx-cc-id", text: "시안 " + c.id.toUpperCase() }), HX.el("span", { class: "hx-cc-lv", text: levelText(c) }), HX.el("h2", { text: title }), HX.el("span", { class: "hx-bar-spacer" }), close]),
        HX.el("div", { class: "hx-modal-body hx-cc-zoom" }, box)])]);
    function key(e) { if (e.key === "Escape") { e.preventDefault(); done(); } }
    function done() { m.remove(); doc.removeEventListener("keydown", key); doc.body.style.overflow = ""; }
    doc.body.appendChild(m); doc.addEventListener("keydown", key); doc.body.style.overflow = "hidden";
    HX.mountFrame(frameKey(c, slug), box, { scale: 1, fullHeight: true, badges: false });
    dressBox(box, full(c.dress));
    close.focus();
  }

  B.buildConcepts = function () {
    var C = B.concepts;
    B.mainConcept = (B.concept(HX.meta.concept) || C[0]).id;
    var mobile = HX.platform === "mobile", W = HX.frame.w, K = mobile ? 1.3 : 2.2;
    var GAP = mobile ? 40 : 120, ROWGAP = mobile ? 200 : 420;
    var vp = HX.el("div", { class: "hx-cv hx-sx hx-ccv", tabindex: "0", "aria-label": "시안 " + C.length + "개 — 캔버스" });
    var world = HX.el("div", { class: "hx-cv-world" }); world.style.setProperty("--k", K);
    vp.appendChild(world);

    var rows = [], picks = {};
    C.forEach(function (c) {
      var d = full(c.dress);
      var pick = HX.btn("", { cls: "hx-primary hx-ccv-pick", onclick: function (e) { e.stopPropagation(); B.state.concept = c.id; B.state.picked = true; B.changed(); HX.toast("시안 " + c.id.toUpperCase() + "으로 골랐어요. 오른쪽 위 보내기로 복사해 주세요."); } });
      pick.addEventListener("pointerdown", function (e) { e.stopPropagation(); });
      picks[c.id] = pick;
      var traits = [SHELL[c.shell] || null, c.density ? "밀도 " + c.density : null].concat(c.dressWords || []).filter(Boolean);
      var band = HX.el("div", { class: "hx-ccv-band", dataset: { concept: c.id } }, [
        HX.el("div", { class: "hx-ccv-bt" }, [
          HX.el("div", { class: "hx-ccv-top" }, [HX.el("span", { class: "hx-cc-id", text: "시안 " + c.id.toUpperCase() }), HX.el("span", { class: "hx-cc-lv", text: levelText(c) }),
            HX.el("b", { text: c.name })]),   // 레이아웃은 추천하지 않는다(사용자: "레이아웃은 추천은 없애자")
          HX.el("div", { class: "hx-ccv-why" }, [c.why || "", layoutText(c) ? HX.el("span", { text: " · 화면 구성 " + layoutText(c) }) : null]),
          traits.length ? HX.el("div", { class: "hx-ccv-traits", text: traits.join(" · ") }) : null]),
        pick]);
      world.appendChild(band);
      var R = { c: c, band: band, boards: [] };
      (c.screens || []).forEach(function (slug) {
        var s = HX.bySlug[slug], title = s ? s.name : slug;
        var open = HX.el("button", { type: "button", class: "hx-sx-pick", title: "크게 보기 — " + title }, [HX.icon("#i-maximize-2"), HX.el("span", { text: "크게 보기" })]);
        open.addEventListener("pointerdown", function (e) { e.stopPropagation(); });
        open.addEventListener("click", function (e) { e.stopPropagation(); zoomModal(c, slug, title); });
        var label = HX.el("div", { class: "hx-sx-label", style: "width:" + W + "px" }, [HX.el("b", { text: title }), open]);
        var box = HX.el("div", { class: "hx-cv-board hx-sx-board hx-ccv-board", style: "width:" + W + "px" });
        world.appendChild(label); world.appendChild(box);
        R.boards.push({ slug: slug, label: label, box: box, d: d, frame: null });
      });
      rows.push(R);
    });

    // ---- 배치: 시안마다 한 줄 — 띠 → 이름표 → 화면 나란히(화면 전체 길이) ----
    var worldW = 0, worldH = 0, BAND = 92 * K, LAB = 44 * K;
    function layout() {
      var y = 0; worldW = 0;
      rows.forEach(function (R) {
        var rowW = R.boards.length * W + (R.boards.length - 1) * GAP;
        R.y = y; R.band.style.top = y + "px"; R.band.style.left = "0px"; R.band.style.width = rowW + "px";
        var top = y + BAND + 24 * K + LAB, h = 0;
        R.boards.forEach(function (b, i) {
          var x = i * (W + GAP);
          b.x = x; b.y = top;
          b.label.style.left = x + "px"; b.label.style.top = (top - 10 * K - b.label.offsetHeight) + "px";
          b.box.style.left = x + "px"; b.box.style.top = top + "px";
          h = Math.max(h, b.box.offsetHeight || HX.frame.h);
        });
        R.h = top + h - y;
        worldW = Math.max(worldW, rowW);
        y = top + h + ROWGAP;
      });
      worldH = y;
      world.style.width = worldW + "px"; world.style.height = worldH + "px";
    }

    // ---- 확대·축소·이동 (사용 흐름 캔버스와 같은 손맛) ----
    var z = 0.3, tx = 40, ty = 80, drag = null, dragged = false, mounted = false;
    var zoomVal = HX.el("span", { class: "hx-zoom-val", text: "30%" });
    function apply(anim) { world.classList.toggle("hx-anim", !!anim); world.style.transform = "translate(" + tx + "px," + ty + "px) scale(" + z + ")"; zoomVal.textContent = Math.round(z * 100) + "%"; }
    function zoomAt(px, py, nz) { nz = HX.clamp(nz, 0.03, 2); tx = px - (px - tx) * (nz / z); ty = py - (py - ty) * (nz / z); z = nz; apply(); }
    function zoomBy(f) { zoomAt(vp.clientWidth / 2, vp.clientHeight / 2, z * f); }
    function fit(anim) {   // 한 줄(시안 하나)의 폭이 화면에 꽉 차게 — 아래로 넘기며 다음 시안
      var vw = vp.clientWidth; if (!vw || !worldW) return;
      z = HX.clamp((vw - 80) / worldW, 0.03, 1); tx = Math.max(40, (vw - worldW * z) / 2); ty = 72; apply(anim);
    }
    function focusRow(id) {
      var R = rows.filter(function (r) { return r.c.id === id; })[0]; if (!R) return;
      var vw = vp.clientWidth, vh = vp.clientHeight;
      z = HX.clamp(Math.min((vw - 80) / worldW, (vh - 100) / R.h), 0.03, 1); tx = Math.max(40, (vw - worldW * z) / 2); ty = 64 - R.y * z; apply(true);
    }
    // ---- 화면은 보기만 — 휠·끌기는 언제나 캔버스 이동 (사용자: "스크롤이나 이런 거 없애자, 화면만 봐도 될 듯") ----
    vp.addEventListener("wheel", function (e) {
      e.preventDefault();
      var r = vp.getBoundingClientRect(), k = e.deltaMode === 1 ? 16 : 1;
      if (e.ctrlKey || e.metaKey) { zoomAt(e.clientX - r.left, e.clientY - r.top, z * Math.exp(-e.deltaY * k * 0.01)); return; }
      var wx = e.deltaX, wy = e.deltaY; if (e.shiftKey && !wx) { wx = wy; wy = 0; } tx -= wx * k; ty -= wy * k; apply();
    }, { passive: false });
    vp.addEventListener("pointerdown", function (e) {
      if (e.button !== 0 || e.target.closest(".hx-cv-tools, .hx-ccv-pick")) return;
      drag = { x: e.clientX, y: e.clientY, tx: tx, ty: ty }; dragged = false;
    });
    window.addEventListener("pointermove", function (e) {
      if (!drag) return; var ddx = e.clientX - drag.x, ddy = e.clientY - drag.y;
      if (!dragged && Math.abs(ddx) + Math.abs(ddy) < 5) return;
      dragged = true; vp.classList.add("hx-dragging"); tx = drag.tx + ddx; ty = drag.ty + ddy; apply();
    });
    window.addEventListener("pointerup", function () { if (!drag) return; drag = null; vp.classList.remove("hx-dragging"); });
    // 키보드: ↑↓ 이전·다음 시안 줄 · +/− 확대 · 0 전체
    var curRow = 0;
    doc.addEventListener("keydown", function (e) {
      if (doc.querySelector(".hx-modal, .hxp-panel:not([hidden])") || /^(INPUT|TEXTAREA)$/.test((e.target || {}).tagName || "")) return;
      if (e.key === "+" || e.key === "=") zoomBy(1.25); else if (e.key === "-") zoomBy(1 / 1.25); else if (e.key === "0") fit(true);
      else if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        e.preventDefault();
        var mid = (vp.clientHeight / 2 - ty) / z;   // 지금 화면 가운데 있는 줄에서 시작
        curRow = rows.reduce(function (best, R, i) { return Math.abs(R.y + R.h / 2 - mid) < Math.abs(rows[best].y + rows[best].h / 2 - mid) ? i : best; }, 0);
        curRow = Math.max(0, Math.min(rows.length - 1, curRow + (e.key === "ArrowDown" ? 1 : -1)));
        focusRow(rows[curRow].c.id);
      }
    });

    // ---- 도구: 시안 바로가기 · 축소/확대 · 전체 보기 ----
    var tools = HX.el("div", { class: "hx-cv-tools hx-sx-tools" }, [
      HX.el("div", { class: "hx-sx-jump", role: "group", "aria-label": "시안으로 가기" }, C.map(function (c) {
        var b = HX.btn(c.id.toUpperCase() + (c.level ? " " + c.level + "단계" : ""), { title: c.name, onclick: function () { focusRow(c.id); } });
        b.classList.add("hx-ccv-jump"); b.dataset.concept = c.id; return b;
      })),
      HX.el("span", { class: "hx-sx-sep" }),
      HX.btn("", { cls: "hx-icon-btn", aria: "축소", title: "축소 (−)", icon: HX.icon("#i-zoom-out"), onclick: function () { zoomBy(1 / 1.25); } }), zoomVal,
      HX.btn("", { cls: "hx-icon-btn", aria: "확대", title: "확대 (+)", icon: HX.icon("#i-zoom-in"), onclick: function () { zoomBy(1.25); } }),
      HX.btn("전체 보기", { icon: HX.icon("#i-maximize-2"), title: "한 줄이 꽉 차게 (0)", onclick: function () { fit(true); } })]);
    tools.addEventListener("pointerdown", function (e) { e.stopPropagation(); });
    vp.appendChild(tools);
    vp.appendChild(HX.el("div", { class: "hx-sx-legend" }, ["끌거나 휠 = 캔버스 이동 · ↑↓ 다음 안 · ⌘/Ctrl+휠 확대 · 화면 이름 옆 '크게 보기'"]));

    function paint() {
      C.forEach(function (c) {
        var on = !!B.state.picked && B.state.concept === c.id, b = picks[c.id];
        while (b.firstChild) b.removeChild(b.firstChild);
        b.appendChild(HX.icon(on ? "#i-circle-check" : "#i-circle"));
        b.appendChild(doc.createTextNode(on ? "이 안으로 할게요 (고름)" : "이 안으로 할게요"));
        b.setAttribute("aria-pressed", on ? "true" : "false");
        rows.forEach(function (R) { if (R.c.id === c.id) R.band.classList.toggle("hx-on", on); });
        var j = tools.querySelector('.hx-ccv-jump[data-concept="' + c.id + '"]'); if (j) j.classList.toggle("hx-on", on);
      });
    }
    HX.on("board-change", paint);
    HX.on("layout", function () { if (mounted && vp.clientWidth) layout(); });
    // 붙인 뒤에 화면을 싣고 배치 (화면 전체 길이를 재야 줄 높이가 정해진다)
    requestAnimationFrame(function () {
      rows.forEach(function (R) { R.boards.forEach(function (b) {
        b.frame = HX.mountFrame(frameKey(R.c, b.slug), b.box, { scale: 1, fullHeight: true, badges: false });   // 화면 전체 길이 — 보기만
        dressBox(b.box, b.d);
      }); });
      mounted = true;
      requestAnimationFrame(function () { HX.relayout(); requestAnimationFrame(function () { layout(); fit(false); }); });
    });
    paint();
    return vp;
  };

  /* 1턴 보드: 상단바(제목 · 색 바꾸기 · 보내기) + 시안 캔버스 */
  B.startConcept = function (app) {
    app.classList.add("hx-app"); app.classList.add("hx-bd"); app.classList.add("hx-tab-concept");
    var copyBtn = HX.btn("", { cls: "hx-primary hx-bd-copy", icon: HX.icon("#i-send"), title: "무엇이 전달되는지 확인하고 복사해요", onclick: function () { B.openSend(); } });
    var copyLabel = HX.el("span"); copyBtn.appendChild(copyLabel);
    var colorSlot = HX.el("span", { class: "hx-bd-color" });
    app.appendChild(HX.el("div", { class: "hx-bar hx-bd-bar" }, [
      HX.el("div", { class: "hx-bar-title", title: HX.meta.title || "" }, [HX.meta.title || HX.meta.project || "", HX.el("small", { text: "시안 " + B.concepts.length + "개 고르기" })]),
      HX.el("span", { class: "hx-bar-spacer" }), colorSlot, copyBtn]));
    app.appendChild(B.buildConcepts());
    if (B.mountColor) B.mountColor(colorSlot);
    function paintCopy() {   // 레이아웃을 고르기 전에는 보낼 수 없다(추천 없음)
      var n = B.diffCount(), C = B.concept(B.state.concept), picked = !!B.state.picked;
      copyLabel.textContent = picked ? "시안 " + (C ? C.id.toUpperCase() : "") + "(으)로 보내기" + (n ? " · " + n + "개" : "") : "마음에 드는 안을 골라 주세요";
      copyBtn.disabled = !picked;
    }
    HX.on("board-change", paintCopy); paintCopy();
  };
})();
