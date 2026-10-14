/* picker.js — "색 바꾸기": 다 만든 화면에서 색을 자유롭게 골라 그 자리에서 다시 칠한다.
   사용자 결정(2026-10-14): "레이아웃이나 이런거 선택후에 색상은 자유롭게 최종 다 나온 결과물에서 바로바로 바뀌게".
   쓰는 곳: 2턴 초안 보드(상단바) · 최종본 입구(index.html) · 화면별 페이지(screens/NN-slug.html).
   필요한 것: window.HXLooks(scripts/looks.js) · window.HX_LOOKS_DATA(presets.json) · window.HX_OWN_LOOKS(screens.json looks — PRD 맞춤).
   고르는 것: 스타일(맞춤 · 국내 · 해외 고정 스타일) + 그 스타일의 버튼 색 / 직접 고르기(팔레트 24색 + 그 밖의 색 + 바탕 흰·따뜻한·어두운).
   칠하는 법: <html data-theme data-swatch>를 바꾸고, 페이지에 없는 분위기 토큰은 looks.js로 계산해 <style>로 넣는다(글꼴도 불러온다).
   HXColor.mount({ project, anchor?, inline?, onChange?(sel), persist? }) — inline이면 단추 없이 anchor 안에 창을 펼쳐 둔다(시안 보드 오른쪽 사이드바) — persist면 이 브라우저에 기억(최종본 페이지끼리 함께 바뀐다).
   sel = { theme, swatch, custom: { hex, name, base, bgHex? } | null } — 바탕은 12가지(presets.json bases, tint = 고른 색으로 살짝) + 그 밖의 바탕(bgHex) */
(function () {
  "use strict";
  var LK = window.HXLooks, DATA = window.HX_LOOKS_DATA || {};
  if (!LK) return;
  var doc = document, root = doc.documentElement;
  var OWN = (window.HX_OWN_LOOKS || []).map(function (l) { return Object.assign({ kind: "own" }, l); });
  var PRE = (LK.PRESETS || []).filter(function (p) { return !OWN.some(function (o) { return o.id === p.id; }); }).map(function (p) { return Object.assign({ kind: "preset" }, p); });
  var ALL = OWN.concat(PRE);
  var byId = function (id) { return ALL.filter(function (l) { return l.id === id; })[0] || null; };

  function el(tag, attrs, kids) {
    var n = doc.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) {
      var v = attrs[k]; if (v == null || v === false) return;
      if (k === "text") n.textContent = v; else if (k.slice(0, 2) === "on") n.addEventListener(k.slice(2), v); else n.setAttribute(k, v);
    });
    (kids || []).forEach(function (c) { if (c != null) n.appendChild(typeof c === "string" ? doc.createTextNode(c) : c); });
    return n;
  }
  // ---------- 칠하기: 없는 분위기는 계산해서 넣는다 ----------
  var sheet = null, painted = {}, fontsOn = {};
  function ensure(L) {
    if (!L || painted[L.id + (L.custom ? ":" + L.swatches[0].hex + L.base : "")]) return;
    if (!sheet) sheet = doc.head.appendChild(el("style", { id: "hx-color-runtime" }));
    var have = !L.custom && getComputedStyle(root).getPropertyValue("--c-bg") && doc.querySelector("style") && [].some.call(doc.querySelectorAll("style"), function (s) { return s !== sheet && s.textContent.indexOf('[data-theme="' + L.id + '"]') >= 0; });
    if (!have) {
      if (L.custom) sheet.textContent = sheet.textContent.replace(/\/\*custom\*\/[\s\S]*?\/\*\/custom\*\//, "");
      sheet.textContent += (L.custom ? "/*custom*/" : "") + LK.looksCss([L]) + (L.custom ? "/*/custom*/" : "") + "\n";
    }
    (LK.fontOf(L).css || []).forEach(function (u) { if (fontsOn[u] || doc.querySelector('link[href="' + u + '"]')) return; fontsOn[u] = 1; doc.head.appendChild(el("link", { rel: "stylesheet", href: u })); });
    painted[L.id + (L.custom ? ":" + L.swatches[0].hex + L.base : "")] = 1;
  }
  function lookOf(sel) { return sel.theme === "custom" && sel.custom ? LK.customLook(sel.custom, window.HX_OWN_LOOKS || []) : byId(sel.theme); }
  function paint(sel) {
    var L = lookOf(sel); if (!L) return;
    ensure(L);
    root.setAttribute("data-theme", L.id);
    root.setAttribute("data-swatch", L.swatches.some(function (s) { return s.id === sel.swatch; }) ? sel.swatch : L.swatches[0].id);
  }
  function hexOf(L, sw) { return LK.primaryHex(L, sw); }
  function nameOf(sel) {
    var L = lookOf(sel); if (!L) return "";
    if (L.custom) return "직접 고른 색 " + (sel.custom.name || sel.custom.hex) + " · " + (L.why.split(" · ")[1] || "");
    var sw = L.swatches.filter(function (s) { return s.id === sel.swatch; })[0] || L.swatches[0];
    return L.name + " · " + sw.name;
  }

  var CSS = [
    ".hxp-btn{display:inline-flex;align-items:center;gap:6px;height:34px;padding:0 14px;border-radius:999px;border:1px solid rgba(0,0,0,.12);background:#fff;color:#111827;font:700 13px/1 -apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',Pretendard,sans-serif;cursor:pointer;box-shadow:0 4px 14px rgba(0,0,0,.12)}",
    ".hxp-btn i{width:14px;height:14px;border-radius:50%;box-shadow:inset 0 0 0 1px rgba(0,0,0,.15)}",
    ".hxp-float{position:fixed;left:16px;bottom:16px;z-index:10000}",
    ".hxp-panel{position:fixed;left:16px;bottom:60px;z-index:10001;width:min(640px,calc(100vw - 32px));max-height:min(72vh,640px);overflow:auto;padding:14px 16px;border-radius:14px;background:#fff;color:#111827;border:1px solid #E5E7EB;box-shadow:0 18px 48px rgba(0,0,0,.22);font:13px/1.4 -apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',Pretendard,sans-serif}",
    ".hxp-panel[hidden]{display:none}.hxp-anch .hxp-panel{left:auto;right:16px;top:64px;bottom:auto}",
    ".hxp-head{display:flex;align-items:baseline;gap:10px;margin-bottom:8px}.hxp-head b{font-size:14px}.hxp-now{color:#4B5563;font-weight:700}.hxp-sp{flex:1}",
    ".hxp-x{border:0;background:none;font-size:18px;line-height:1;cursor:pointer;color:#6B7280}",
    ".hxp-sub{margin:10px 0 6px;font-size:12px;font-weight:800;color:#6B7280}",
    ".hxp-row{display:grid;grid-template-columns:56px minmax(0,1fr);gap:6px;align-items:center;margin-bottom:6px}.hxp-row>span{font-size:12px;font-weight:700;color:#4B5563}",
    ".hxp-styles{display:grid;grid-template-columns:repeat(auto-fill,minmax(122px,1fr));gap:6px}",
    ".hxp-style{display:flex;align-items:center;gap:7px;padding:5px 7px;border:1.5px solid #E5E7EB;border-radius:9px;background:#fff;cursor:pointer;text-align:left;font:inherit;color:inherit}",
    ".hxp-style[aria-checked=true]{border-color:#2563EB;box-shadow:0 0 0 3px #DBEAFE}.hxp-style b{font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}",
    ".hxp-prev{flex:0 0 auto;position:relative;width:28px;height:22px;border-radius:5px;box-shadow:inset 0 0 0 1px rgba(0,0,0,.14);overflow:hidden}",
    ".hxp-prev em{position:absolute;left:4px;right:9px;bottom:4px;height:6px;border-radius:3px}",
    ".hxp-dots{display:flex;flex-wrap:wrap;gap:2px}",
    ".hxp-dot{display:flex;flex-direction:column;align-items:center;gap:2px;width:48px;padding:3px 0;border:0;border-radius:8px;background:none;cursor:pointer;font:inherit;color:#4B5563}",
    ".hxp-dot:hover{background:#F3F4F6}.hxp-dot i{width:24px;height:24px;border-radius:50%;box-shadow:inset 0 0 0 1px rgba(0,0,0,.14)}",
    ".hxp-dot[aria-checked=true] i{box-shadow:0 0 0 2px #fff,0 0 0 4px #111827}.hxp-dot[aria-checked=true] small{color:#111827;font-weight:800}.hxp-dot small{font-size:10.5px;white-space:nowrap;max-width:52px;overflow:hidden;text-overflow:ellipsis}",
    ".hxp-seg{display:inline-flex;gap:2px;padding:2px;border-radius:9px;background:#F3F4F6}",
    ".hxp-seg button{border:0;background:none;padding:6px 10px;border-radius:7px;font:inherit;font-weight:700;color:#4B5563;cursor:pointer}.hxp-seg button[aria-pressed=true]{background:#fff;color:#111827;box-shadow:0 1px 2px rgba(0,0,0,.12)}",
    ".hxp-other{display:inline-flex;align-items:center;gap:8px;color:#6B7280;cursor:pointer}.hxp-other input{width:30px;height:24px;padding:0;border:1px solid #E5E7EB;border-radius:6px;background:none;cursor:pointer}",
    ".hxp-grid{display:grid;grid-template-columns:repeat(12,22px);gap:3px}.hxp-chip{width:22px;height:22px;padding:0;border:0;border-radius:5px;cursor:pointer;box-shadow:inset 0 0 0 1px rgba(0,0,0,.1)}",
    ".hxp-chip:hover{transform:scale(1.15)}.hxp-chip[aria-checked=true]{box-shadow:0 0 0 2px #fff,0 0 0 4px #111827}",
    ".hxp-harm{display:flex;flex-wrap:wrap;gap:6px}.hxp-hcard{display:flex;flex-direction:column;align-items:center;gap:3px;padding:4px;border:1px solid #E5E7EB;border-radius:9px;background:#fff;cursor:pointer;font:inherit;color:#4B5563}",
    ".hxp-hcard:hover{border-color:#2563EB}.hxp-hprev{position:relative;display:block;width:56px;height:34px;border-radius:6px;box-shadow:inset 0 0 0 1px rgba(0,0,0,.1)}.hxp-hprev em{position:absolute;left:7px;right:7px;bottom:6px;height:9px;border-radius:5px}.hxp-hcard small{font-size:11px}",
    ".hxp-warn{color:#B4532A;font-weight:700;font-size:12px}.hxp-reset{border:0;background:none;color:#2563EB;font:inherit;font-weight:700;cursor:pointer;padding:0}",
    ".hxp-inline>.hxp-btn{display:none}.hxp-inline .hxp-panel{position:static;width:auto;max-height:none;padding:0;border:0;border-radius:0;box-shadow:none;background:none}",
    ".hxp-row{grid-template-columns:72px minmax(0,1fr)}.hxp-inline .hxp-x{display:none}.hxp-inline .hxp-head{flex-wrap:wrap}.hxp-inline .hxp-row{grid-template-columns:1fr}.hxp-inline .hxp-styles{grid-template-columns:repeat(2,minmax(0,1fr))}"
  ].join("\n");

  window.HXColor = {
    names: nameOf, paint: paint,
    /* 화면에 "색 바꾸기" 단추와 창을 붙인다. 처음 색 = html의 data-theme/data-swatch (persist면 이 브라우저에 기억한 색) */
    mount: function (o) {
      o = o || {};
      if (!doc.getElementById("hxp-css")) doc.head.appendChild(el("style", { id: "hxp-css", text: CSS }));
      var key = "hx-color:" + (o.project || "project");
      var first = { theme: root.getAttribute("data-theme"), swatch: root.getAttribute("data-swatch"), custom: o.custom || null };
      var sel = Object.assign({}, first);
      if (o.initial) sel = Object.assign(sel, o.initial);
      if (o.persist) { try { var saved = JSON.parse(localStorage.getItem(key) || "null"); if (saved && saved.theme) sel = saved; } catch (e) {} }
      paint(sel);
      var dotBtn = el("i"), btn = el("button", { type: "button", class: "hxp-btn", title: "색을 골라 바로 바꿔 봐요", "aria-expanded": "false" }, [dotBtn, "색 바꾸기"]);
      var now = el("span", { class: "hxp-now" }), warn = el("span", { class: "hxp-warn" });
      var panel = el("div", { class: "hxp-panel", role: "dialog", "aria-label": "색 바꾸기", hidden: "" });
      var wrap = el("div", { class: o.inline ? "hxp-inline" : o.anchor ? "hxp-anch" : "hxp-float" }, [btn, panel]);
      if (o.inline) panel.removeAttribute("hidden");
      (o.anchor || doc.body).appendChild(wrap);

      function set(next) {
        sel = next; paint(sel);
        if (o.persist) { try { localStorage.setItem(key, JSON.stringify(sel)); } catch (e) {} }
        if (o.onChange) o.onChange(sel);
        sync();
      }
      function pickLook(L, swId) { set({ theme: L.id, swatch: swId || L.swatches[0].id, custom: null }); }
      // 직접 고른 색은 지금 스타일 위에 버튼 색만 바꾼다(from) — 사용자: "직접 고르기를 하면 스타일이 사라지니까"
      function pickCustom(c) {
        var prev = sel.custom || {}, from = sel.theme === "custom" ? (prev.from || null) : sel.theme;
        var base = c.base || prev.base || "white", bgHex = c.base ? (c.bgHex || null) : (c.bgHex !== undefined ? c.bgHex : prev.bgHex || null);
        var cu = { hex: String(c.hex).toUpperCase(), name: c.name || "", base: c.base || prev.base || null };
        if (from) cu.from = from;
        if (!cu.base) delete cu.base;
        if (bgHex) cu.bgHex = String(bgHex).toUpperCase();
        set({ theme: "custom", swatch: "custom", custom: cu });
      }
      function curHex() { var L = lookOf(sel); return sel.custom ? { hex: sel.custom.hex, name: sel.custom.name } : { hex: hexOf(L, L.swatches.filter(function (s) { return s.id === sel.swatch; })[0] || L.swatches[0]), name: "" }; }
      // 스타일 목록(토스·당근… 고정 스타일)은 보이지 않는다 — 사용자: "스타일들 너무 많아서 그냥 스타일은 없애자".
      // 이 서비스에 맞춘 색 하나 + 버튼 색 + 직접 고르기만. (고정 스타일 데이터는 남겨 둔다 — 예전 보내기 글·색 계산용)
      var styleBtns = [], groups = {}, stylesBox = el("div");
      (OWN.length ? OWN : ALL.slice(0, 1)).forEach(function (L) {
        var g = "기본 색";
        if (!groups[g]) { groups[g] = el("div", { class: "hxp-styles" }); stylesBox.appendChild(el("div", { class: "hxp-row" }, [el("span", { text: g }), groups[g]])); }
        var sw = L.swatches[0];
        var b = el("button", { type: "button", class: "hxp-style", role: "radio", title: L.why || L.name, onclick: function () { pickLook(L); } },
          [el("span", { class: "hxp-prev", style: "background:" + L.bg }, [el("em", { style: "background:" + hexOf(L, sw) })]), el("b", { text: L.name })]);
        styleBtns.push([b, L.id]); groups[g].appendChild(b);
      });
      var swBox = el("div", { class: "hxp-dots" });
      function buildSw() {
        swBox.innerHTML = "";
        var L = lookOf(sel);
        if (!L || L.custom) { swBox.appendChild(el("span", { class: "hxp-now", text: "직접 고른 색을 쓰고 있어요" + (sel.custom && sel.custom.from ? " (스타일은 " + (byId(sel.custom.from) || {}).name + " 그대로)" : "") })); return; }
        L.swatches.forEach(function (sw) {
          swBox.appendChild(el("button", { type: "button", class: "hxp-dot", role: "radio", "aria-checked": sw.id === sel.swatch ? "true" : "false", title: sw.name, onclick: function () { pickLook(L, sw.id); } },
            [el("i", { style: "background:" + hexOf(L, sw) }), el("small", { text: sw.name })]));
        });
      }
      // 직접 고르기 — 색 바둑판(색상 12 × 밝기 5 + 회색) · 어울리는 배색 5가지 · 이름 있는 색 · 그 밖의 색 · 바탕
      var palBtns = [], pal = el("div");
      var grid = el("div", { class: "hxp-grid" });
      (LK.swatchGrid ? LK.swatchGrid() : []).forEach(function (row) { row.forEach(function (hx) {
        var b = el("button", { type: "button", class: "hxp-chip", title: hx, "aria-label": hx, style: "background:" + hx, onclick: function () { pickCustom({ hex: hx, name: "" }); } });
        palBtns.push([b, hx.toUpperCase()]); grid.appendChild(b);
      }); });
      pal.appendChild(el("div", { class: "hxp-row" }, [el("span", { text: "색 바둑판" }), grid]));
      var harmBox = el("div", { class: "hxp-harm" });
      pal.appendChild(el("div", { class: "hxp-row" }, [el("span", { text: "어울리는 배색" }), harmBox]));
      function buildHarm() {
        while (harmBox.firstChild) harmBox.removeChild(harmBox.firstChild);
        var base = curHex();
        (LK.harmonies ? LK.harmonies(base.hex) : []).forEach(function (h) {
          harmBox.appendChild(el("button", { type: "button", class: "hxp-hcard", title: h.name + " — 버튼 " + h.hex + " · 바탕 " + h.bgHex, onclick: function () { pickCustom({ hex: h.hex, name: h.name, bgHex: h.bgHex }); } },
            [el("span", { class: "hxp-hprev", style: "background:" + h.bgHex }, [el("em", { style: "background:" + h.hex })]), el("small", { text: h.name })]));
        });
      }
      (LK.PALETTE || []).forEach(function (g) {
        pal.appendChild(el("div", { class: "hxp-row" }, [el("span", { text: g.group }), el("div", { class: "hxp-dots" }, g.colors.map(function (c) {
          var b = el("button", { type: "button", class: "hxp-dot", role: "radio", title: c.name, onclick: function () { pickCustom(c); } }, [el("i", { style: "background:" + c.hex }), el("small", { text: c.name })]);
          palBtns.push([b, c.hex.toUpperCase()]); return b;
        }))]));
      });
      var other = el("input", { type: "color", "aria-label": "그 밖의 색", value: "#5B5BD6", oninput: function () { pickCustom({ hex: other.value, name: "" }); } });
      pal.appendChild(el("div", { class: "hxp-row" }, [el("span", { text: "그 밖의 색" }), el("label", { class: "hxp-other" }, [other, el("small", { text: "눌러서 아무 색이나" })])]));
      // 바탕: 색 조각 12가지 + 그 밖의 바탕 (사용자: "바탕색은 한정적이야?")
      var baseBtns = [], baseRow = el("div", { class: "hxp-dots" }, (LK.BASES || []).map(function (bs) {
        var sw = bs.id === "tint" ? "linear-gradient(135deg, #FFFFFF 40%, " + (sel.custom ? sel.custom.hex : "#9BB4F0") + ")" : bs.bg;
        var b = el("button", { type: "button", class: "hxp-dot", role: "radio", title: bs.name, onclick: function () { var c = curHex(); pickCustom({ hex: c.hex, name: c.name, base: bs.id }); } },
          [el("i", { style: "background:" + sw }), el("small", { text: bs.name })]);
        baseBtns.push([b, bs.id]); return b;
      }));
      var otherBg = el("input", { type: "color", "aria-label": "그 밖의 바탕", value: "#F4F1EA", oninput: function () { var c = curHex(); pickCustom({ hex: c.hex, name: c.name, bgHex: otherBg.value }); } });
      pal.appendChild(el("div", { class: "hxp-row" }, [el("span", { text: "바탕" }), baseRow]));
      pal.appendChild(el("div", { class: "hxp-row" }, [el("span", { text: "그 밖의 바탕" }), el("label", { class: "hxp-other" }, [otherBg, el("small", { text: "눌러서 아무 바탕이나" })])]));
      var reset = el("button", { type: "button", class: "hxp-reset", text: "처음 색으로", onclick: function () { set(Object.assign({}, first)); } });
      panel.appendChild(el("div", { class: "hxp-head" }, [el("b", { text: "색 바꾸기" }), now, el("span", { class: "hxp-sp" }), reset, el("button", { type: "button", class: "hxp-x", "aria-label": "닫기", text: "×", onclick: function () { toggle(false); } })]));
      panel.appendChild(warn);
      panel.appendChild(stylesBox);
      panel.appendChild(el("div", { class: "hxp-sub", text: "버튼 색" })); panel.appendChild(swBox);
      panel.appendChild(el("div", { class: "hxp-sub", text: "직접 고르기" })); panel.appendChild(pal);

      function sync() {
        var L = lookOf(sel), custom = L && L.custom;
        styleBtns.forEach(function (x) { x[0].setAttribute("aria-checked", x[1] === sel.theme ? "true" : "false"); });
        palBtns.forEach(function (x) { x[0].setAttribute("aria-checked", custom && x[1] === String(sel.custom.hex).toUpperCase() ? "true" : "false"); });
        styleBtns.forEach(function (x) { if (custom && sel.custom.from === x[1]) x[0].setAttribute("aria-checked", "true"); });
        baseBtns.forEach(function (x) { x[0].setAttribute("aria-checked", custom && !sel.custom.bgHex && x[1] === sel.custom.base ? "true" : "false"); });
        buildSw(); buildHarm();
        now.textContent = "지금: " + nameOf(sel);
        var sw = L && (L.swatches.filter(function (s) { return s.id === sel.swatch; })[0] || L.swatches[0]);
        dotBtn.style.background = L ? hexOf(L, sw) : "#999";
        warn.textContent = L && LK.contrast(hexOf(L, sw), L.bg) < 1.6 ? "바탕과 색이 비슷해서 버튼이 잘 안 보일 수 있어요" : "";
      }
      function toggle(on) { if (o.inline) return; if (on) panel.removeAttribute("hidden"); else panel.setAttribute("hidden", ""); btn.setAttribute("aria-expanded", on ? "true" : "false"); }
      btn.addEventListener("click", function (e) { e.stopPropagation(); toggle(panel.hasAttribute("hidden")); });
      // 창 안을 누르면 닫지 않는다 — 누른 단추가 다시 그려지며 사라져도(버튼 색 줄) 안쪽으로 본다 (사용자: "버튼 누르면 팝업이 닫히는데 안 닫히게")
      var inside = false;
      wrap.addEventListener("pointerdown", function () { inside = true; }, true);
      doc.addEventListener("click", function (e) {
        var path = e.composedPath ? e.composedPath() : [];
        if (inside || path.indexOf(wrap) >= 0 || wrap.contains(e.target)) { inside = false; return; }
        toggle(false);
      });
      doc.addEventListener("keydown", function (e) { if (e.key === "Escape") toggle(false); });
      sync();
      if (o.onChange && (sel.theme !== first.theme || sel.swatch !== first.swatch)) o.onChange(sel);
      return { get: function () { return sel; }, set: set, open: function () { toggle(true); } };
    }
  };
})();
