/* 08-sections.js — 사용 흐름 = 디자이너식 구역 보드 (Figma 보드처럼 한 캔버스).
   큰 구역(screens.json sections: 가입·처음 시작 / 홈 / …) → 단계 이름표(screen.step) → 화면을 순서대로 나란히.
   같은 단계의 상태 화면(빈칸·오류·완료, variantOf)은 원래 화면 옆에 붙는다. 화살표는 모든 화면을 잇지 않고
   조건이 갈리는 곳(flow.json step·branch의 when)에만 + 조건 이름표. 화면 아래에는 정책 메모(screen.policy) 검은 상자.
   HX.buildSections({ onPick(slug) }) → { el, onShow, focus(slug), focusSection(key), zoomBy, fit, onKey, onZoom, mark(slug, tags) }
   보드(22-board-canvas)와 최종본(10-final)이 함께 쓴다. */
(function () {
  "use strict";
  var HX = window.HX, SVG = "http://www.w3.org/2000/svg";

  var STATE_LABEL = { "first-run": "처음 켰을 때", empty: "데이터 없을 때", input: "입력할 때", error: "오류일 때", success: "완료됐을 때" };
  HX.stateLabel = function (st) { return STATE_LABEL[st] || ""; };
  function roleName(role) { var l = HX.roleLabel(role).replace(/\(.*\)/, ""); return l === "부모" ? "부모님" : l; }

  // 화면 번호 순서(= 사용자가 만나는 순서). 상태만 다른 화면(variantOf)은 번호가 뒤여도 원래 화면 바로 옆에
  function order() {
    var byNum = HX.data.screens.map(function (s, i) { return { s: s, k: typeof s.id === "number" ? s.id : 1e6 + i }; })
      .sort(function (a, b) { return a.k - b.k; }).map(function (x) { return x.s; });
    var out = [], placed = {};
    function put(s) {
      if (placed[s.slug]) return; placed[s.slug] = true; out.push(s);
      byNum.forEach(function (v) { if (pulled(v) && v.variantOf === s.slug) put(v); });
    }
    // 오류·완료 상태만 원래 화면 옆으로 당긴다 (처음 켰을 때·데이터 없을 때는 원래 화면보다 먼저 만나므로 제자리)
    function pulled(v) { var b = v.variantOf && HX.bySlug[v.variantOf]; return !!b && b.section === v.section && (v.state === "error" || v.state === "success"); }
    byNum.forEach(function (s) { if (!pulled(s)) put(s); });
    byNum.forEach(put);
    return out;
  }
  // 구역 → 단계 묶음. sections가 없는 예전 실행물은 역할을 구역으로, 화면 이름을 단계로
  function model() {
    var all = order(), secs = (HX.data.sections || []).slice(), byKey = {};
    if (!secs.length) {
      secs = HX.meta.roles.map(function (r) { return { key: r.key, name: roleName(r.key) }; });
      all.forEach(function (s) { s._sec = s.role || "_etc"; });
      if (all.some(function (s) { return s._sec === "_etc"; })) secs.push({ key: "_etc", name: "함께 쓰는 화면" });
    } else all.forEach(function (s) { s._sec = s.section; });
    secs.forEach(function (x) { byKey[x.key] = { key: x.key, name: x.name, groups: [] }; });
    all.forEach(function (s) {
      var sec = byKey[s._sec] || byKey[secs[0].key], step = s.step || (s.variantOf && HX.bySlug[s.variantOf] ? HX.bySlug[s.variantOf].step || HX.bySlug[s.variantOf].name : s.name);
      var g = sec.groups[sec.groups.length - 1];
      if (!g || g.step !== step) { g = { step: step, items: [] }; sec.groups.push(g); }
      g.items.push(s);
    });
    return secs.map(function (x) { return byKey[x.key]; }).filter(function (x) { return x.groups.length; });
  }
  // 조건 화살표: 흐름 단계·갈래 중 when이 있는 것만
  function links() {
    var out = [];
    (HX.data.flows || []).forEach(function (f) { (f.steps || []).forEach(function (st) { if (st.when) out.push(st); }); });
    (HX.data.branches || []).forEach(function (b) { if (b.when) out.push(b); });
    return out.filter(function (l) { return HX.bySlug[l.from] && HX.bySlug[l.to]; });
  }

  HX.buildSections = function (opts) {
    opts = opts || {};
    var mobile = HX.platform === "mobile", W = HX.frame.w, K = mobile ? 1.3 : 2.2;   // K: 이름표·메모 글자 배율 (화면 폭에 맞춰)
    var GAP = mobile ? 40 : 120, GROUP = mobile ? 140 : 360, LINE = mobile ? 120 : 260, SECGAP = mobile ? 220 : 520, MAXW = mobile ? 12 * W : 6 * W + 5 * GAP;
    var vp = HX.el("div", { class: "hx-cv hx-sx", tabindex: "0", "aria-label": "사용 흐름 — 구역 보드" });
    var world = HX.el("div", { class: "hx-cv-world" }); world.style.setProperty("--k", K);
    var svg = document.createElementNS(SVG, "svg"); svg.setAttribute("class", "hx-sx-links");
    world.appendChild(svg); vp.appendChild(world);

    var secs = model(), boards = [], bySlug = {}, secEls = [];
    secs.forEach(function (sec) {
      var band = HX.el("div", { class: "hx-sx-band" }, [HX.el("b", { text: sec.name }),
        HX.el("span", { text: "화면 " + sec.groups.reduce(function (n, g) { return n + g.items.length; }, 0) + "개" })]);
      world.appendChild(band);
      var S = { key: sec.key, band: band, groups: [] };
      sec.groups.forEach(function (g) {
        var tag = HX.el("div", { class: "hx-sx-step", text: g.step });
        world.appendChild(tag);
        var G = { tag: tag, boards: [] };
        g.items.forEach(function (s) {
          var label = HX.el("div", { class: "hx-sx-label" }, [HX.el("span", { class: "hx-sx-n", text: String(s.id).padStart(2, "0") }), HX.el("b", { text: s.name }),
            s.state ? HX.el("span", { class: "hx-sx-state hx-st-" + s.state, text: HX.stateLabel(s.state) }) : null,
            HX.el("span", { class: "hx-sx-marks" })]);
          var box = HX.el("div", { class: "hx-cv-board hx-sx-board", dataset: { screen: s.slug }, title: opts.pickTitle || "크게 보기", style: "width:" + W + "px" });
          var note = s.policy && s.policy.length ? HX.el("div", { class: "hx-sx-note", style: "width:" + W + "px" }, s.policy.map(function (p) {
            return HX.el("div", { class: "hx-sx-pol" }, [HX.el("b", { text: p.title }), HX.el("ul", {}, (p.items || []).map(function (t) { return HX.el("li", { text: t }); }))]);
          })) : null;
          world.appendChild(label); world.appendChild(box); if (note) world.appendChild(note);
          var b = { slug: s.slug, label: label, box: box, note: note, frame: null, sec: S };
          box.addEventListener("click", function () { if (dragged) return; if (opts.onPick) opts.onPick(s.slug); else focusBoard(b); });
          G.boards.push(b); boards.push(b); bySlug[s.slug] = b;
        });
        S.groups.push(G);
      });
      secEls.push(S);
    });

    // ---- 배치: 구역마다 단계 묶음을 왼→오로, 너무 길면 다음 줄 ----
    var worldW = 0, worldH = 0, LAB = 44 * K, TAG = 56 * K;
    function layout() {
      var y = 0;
      worldW = 0;
      secEls.forEach(function (S) {
        S.y = y; S.band.style.top = y + "px"; S.band.style.left = "0px";
        y += 64 * K + 72 * K;
        var lines = [[]], x = 0;
        S.groups.forEach(function (G) {
          var gw = G.boards.length * W + (G.boards.length - 1) * GAP;
          if (x > 0 && x + gw > MAXW) { lines.push([]); x = 0; }
          lines[lines.length - 1].push({ G: G, x: x }); x += gw + GROUP;
        });
        lines.forEach(function (ln) {
          var rowH = 0, top = y + TAG + LAB;
          ln.forEach(function (it) {
            it.G.tag.style.left = it.x + "px"; it.G.tag.style.top = y + "px";
            it.G.boards.forEach(function (b, i) {
              var bx = it.x + i * (W + GAP);
              b.x = bx; b.y = top; b.lineY = y; b.h = b.box.offsetHeight || HX.frame.h;
              b.label.style.left = bx + "px"; b.label.style.top = (top - LAB) + "px";
              b.box.style.left = bx + "px"; b.box.style.top = top + "px";
              var h = b.h;
              if (b.note) { b.note.style.left = bx + "px"; b.note.style.top = (top + b.h + 28 * K) + "px"; h += 28 * K + b.note.offsetHeight; }
              rowH = Math.max(rowH, h);
              worldW = Math.max(worldW, bx + W);
            });
          });
          y = top + rowH + LINE;
        });
        S.h = y - S.y;
        y += SECGAP - LINE;
      });
      secEls.forEach(function (S) { S.band.style.width = worldW + "px"; });
      worldH = y;
      world.style.width = worldW + "px"; world.style.height = worldH + "px";
      drawLinks();
      if (!fitted && vp.clientWidth) { fitted = true; fit(false); }   // 숨은 탭에서 붙였으면 처음 보일 때 맞춘다
    }

    // ---- 조건 화살표 ----
    function trigPoint(b, key) {
      var el = key && b.frame && b.frame.section.querySelector('[data-trigger="' + key + '"]');
      if (!el) return null;
      var fr = b.box.getBoundingClientRect(), r = el.getBoundingClientRect(), s = fr.width / W || 1;
      return { x: b.x + (r.left - fr.left) / s, y: b.y + (r.top - fr.top) / s, w: r.width / s, h: r.height / s };
    }
    function drawLinks() {
      while (svg.firstChild) svg.removeChild(svg.firstChild);
      world.querySelectorAll(".hx-sx-when").forEach(function (e) { e.remove(); });
      svg.setAttribute("width", worldW); svg.setAttribute("height", worldH);
      var defs = document.createElementNS(SVG, "defs");
      defs.innerHTML = '<marker id="hx-sx-arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker>';
      svg.appendChild(defs);
      links().forEach(function (l) {
        var A = bySlug[l.from], B = bySlug[l.to]; if (!A || !B || !A.h) return;
        var t = trigPoint(A, l.trigger), sx, sy, d, px, py, a = 32 * K;
        if (t) svg.appendChild(rect(t));
        var bh = Math.min(B.h, HX.frame.h);
        var between = boards.some(function (o) { return o.y === A.y && o.x > A.x && o.x < B.x; });
        if (B.x > A.x + W / 2 && Math.abs(B.y - A.y) < 4 && between) {      // 같은 줄, 사이에 화면이 있으면: 줄 위 빈칸으로 넘어간다
          sx = t ? t.x + t.w : A.x + W; sy = t ? t.y + t.h / 2 : A.y + Math.min(A.h, HX.frame.h) / 2;
          var oy = A.lineY - 28 * K, cx = B.x + W / 2;
          d = "M" + sx + "," + sy + " H" + (A.x + W + a) + " V" + oy + " H" + cx + " V" + (B.y - LAB - 6);
          px = (A.x + W + a + cx) / 2; py = oy;
        } else if (B.x > A.x + W / 2 && Math.abs(B.y - A.y) < 4) {           // 같은 줄 바로 오른쪽
          sx = t ? t.x + t.w : A.x + W; sy = t ? t.y + t.h / 2 : A.y + Math.min(A.h, HX.frame.h) / 2;
          var ex = B.x, ey = B.y + bh / 2, mx = Math.max(sx + a, (A.x + W + B.x) / 2);
          d = "M" + sx + "," + sy + " H" + mx + " V" + ey + " H" + (ex - 6);
          px = mx; py = (sy + ey) / 2;
        } else if (B.y > A.y + 4) {                                            // 아래 줄·다른 구역
          sx = t ? t.x + t.w / 2 : A.x + W / 2; sy = t ? t.y + t.h : A.y + Math.min(A.h, HX.frame.h);
          var gy = B.y - LAB - TAG - 24 * K, tx = B.x + W / 2;
          if (t) { sx = t.x + t.w; sy = t.y + t.h / 2; d = "M" + sx + "," + sy + " H" + (A.x + W + a) + " V" + gy + " H" + tx + " V" + (B.y - LAB - 6); px = (A.x + W + a + tx) / 2; }
          else { d = "M" + sx + "," + sy + " V" + gy + " H" + tx + " V" + (B.y - LAB - 6); px = (sx + tx) / 2; }
          py = gy;
        } else {                                                               // 왼쪽·위로 되돌아가기: 아래로 돌아서
          sx = A.x + W / 2; sy = A.y + A.h + (A.note ? A.note.offsetHeight + 28 * K : 0);
          var by = Math.max(sy, B.y + B.h) + 60 * K, bx = B.x + W / 2;
          d = "M" + sx + "," + sy + " V" + by + " H" + bx + " V" + (B.y + bh + 6); px = (sx + bx) / 2; py = by;
        }
        var path = document.createElementNS(SVG, "path");
        path.setAttribute("d", d); path.setAttribute("class", "hx-sx-path"); path.setAttribute("marker-end", "url(#hx-sx-arr)");
        svg.appendChild(path);
        var pill = HX.el("div", { class: "hx-sx-when", text: l.when, title: (l.action || "") + " → " + HX.bySlug[l.to].name });
        pill.style.left = px + "px"; pill.style.top = py + "px";
        world.appendChild(pill);
      });
    }
    function rect(t) {
      var r = document.createElementNS(SVG, "rect"), p = 6 * K;
      r.setAttribute("x", t.x - p); r.setAttribute("y", t.y - p); r.setAttribute("width", t.w + p * 2); r.setAttribute("height", t.h + p * 2);
      r.setAttribute("rx", 8 * K); r.setAttribute("class", "hx-sx-trig"); return r;
    }

    // ---- 확대·축소·이동 (11-final-all과 같은 손맛) ----
    var z = 0.2, tx = 40, ty = 80, dragged = false, mounted = false, fitted = false;
    function apply(anim) {
      world.classList.toggle("hx-anim", !!anim);
      world.style.transform = "translate(" + tx + "px," + ty + "px) scale(" + z + ")";
      if (api.onZoom) api.onZoom(z);
    }
    function zoomAt(px, py, nz) { nz = HX.clamp(nz, 0.03, 2); tx = px - (px - tx) * (nz / z); ty = py - (py - ty) * (nz / z); z = nz; apply(); }
    function zoomBy(f) { zoomAt(vp.clientWidth / 2, vp.clientHeight / 2, z * f); }
    function fit(anim) {
      var vw = vp.clientWidth, vh = vp.clientHeight; if (!vw || !worldW) return;
      // 폭에 맞추되, 좁고 긴 보드(모바일)는 높이도 보고 한눈에 여러 구역이 들어오게
      z = HX.clamp(Math.min((vw - 80) / worldW, Math.max((vh - 120) / worldH, 0.18)), 0.03, 1); tx = Math.max(40, (vw - worldW * z) / 2); ty = 72; apply(anim);
    }
    function focusBoard(b) {
      var vw = vp.clientWidth, vh = vp.clientHeight;
      z = HX.clamp(Math.min((vw - 120) / W, (vh - 140) / Math.min(b.h, HX.frame.h * 1.4)), 0.08, 1);
      tx = vw / 2 - (b.x + W / 2) * z; ty = 96 - b.y * z; apply(true);
    }
    function focusSection(key) {
      var S = secEls.filter(function (x) { return x.key === key; })[0]; if (!S) return;
      var vw = vp.clientWidth, vh = vp.clientHeight;
      z = HX.clamp(Math.min((vw - 80) / worldW, (vh - 120) / S.h), 0.03, 1); tx = (vw - worldW * z) / 2; ty = 64 - S.y * z; apply(true);
    }
    vp.addEventListener("wheel", function (e) {
      e.preventDefault();
      var r = vp.getBoundingClientRect(), k = e.deltaMode === 1 ? 16 : 1;
      if (e.ctrlKey || e.metaKey) zoomAt(e.clientX - r.left, e.clientY - r.top, z * Math.exp(-e.deltaY * k * 0.01));
      else { var wx = e.deltaX, wy = e.deltaY; if (e.shiftKey && !wx) { wx = wy; wy = 0; } tx -= wx * k; ty -= wy * k; apply(); }
    }, { passive: false });
    var drag = null;
    vp.addEventListener("pointerdown", function (e) { if (e.button !== 0 || e.target.closest(".hx-cv-tools")) return; drag = { x: e.clientX, y: e.clientY, tx: tx, ty: ty }; dragged = false; });
    window.addEventListener("pointermove", function (e) {
      if (!drag) return; var dx = e.clientX - drag.x, dy = e.clientY - drag.y;
      if (!dragged && Math.abs(dx) + Math.abs(dy) < 5) return;
      dragged = true; vp.classList.add("hx-dragging"); tx = drag.tx + dx; ty = drag.ty + dy; apply();
    });
    window.addEventListener("pointerup", function () { if (!drag) return; drag = null; vp.classList.remove("hx-dragging"); setTimeout(function () { dragged = false; }, 0); });

    // ---- 도구: 구역 바로가기 · 확대 · 전체 보기 ----
    var zoomVal = HX.el("span", { class: "hx-zoom-val", text: "20%" });
    var tools = HX.el("div", { class: "hx-cv-tools hx-sx-tools" }, [
      HX.el("div", { class: "hx-sx-jump", role: "group", "aria-label": "구역으로 가기" }, secEls.map(function (S, i) {
        return HX.btn(secs[i].name, { title: secs[i].name + " 구역으로", onclick: function () { focusSection(S.key); } });
      })),
      HX.el("span", { class: "hx-sx-sep" }),
      HX.btn("", { cls: "hx-icon-btn", aria: "축소", title: "축소 (−)", icon: HX.icon("#i-zoom-out"), onclick: function () { zoomBy(1 / 1.25); } }), zoomVal,
      HX.btn("", { cls: "hx-icon-btn", aria: "확대", title: "확대 (+)", icon: HX.icon("#i-zoom-in"), onclick: function () { zoomBy(1.25); } }),
      HX.btn("전체 보기", { icon: HX.icon("#i-maximize-2"), title: "모두 보이게 (0)", onclick: function () { fit(true); } })]);
    tools.addEventListener("pointerdown", function (e) { e.stopPropagation(); });
    vp.appendChild(tools);
    vp.appendChild(HX.el("div", { class: "hx-sx-legend" }, [HX.el("span", { class: "hx-sx-lg-arrow" }), "조건이 갈리는 곳만 화살표 · 화면은 왼쪽부터 순서대로 · 검은 상자는 정책 · ⌘/Ctrl+휠 확대"]));

    HX.on("layout", function () { if (mounted && vp.clientWidth) layout(); });
    var pending = null;
    var api = {
      el: vp,
      zoomBy: zoomBy, fit: fit, focusSection: focusSection,
      zoom: function () { return z; },
      resetHeights: function () { boards.forEach(function (b) { if (b.frame) b.frame.resetHeight(); }); },
      focus: function (slug) {
        var b = bySlug[slug]; if (!b) return;
        if (!mounted || !b.h) { pending = slug; return; }
        focusBoard(b);
      },
      /* 보드: 화면 위 이름표 옆에 '고친 화면'·'뺌'·메모 표시 */
      mark: function (slug, tags) {
        var b = bySlug[slug]; if (!b) return;
        var m = b.label.querySelector(".hx-sx-marks"); m.innerHTML = "";
        (tags || []).forEach(function (t) { m.appendChild(HX.el("span", { class: "hx-sx-mark hx-sx-mark-" + t.kind, text: t.text, title: t.title || null })); });
        b.box.classList.toggle("hx-sx-removed", (tags || []).some(function (t) { return t.kind === "removed"; }));
      },
      onShow: function () {
        if (!mounted) {
          mounted = true;
          boards.forEach(function (b) { b.frame = HX.mountFrame(b.slug, b.box, { scale: 1, fullHeight: true, badges: false }); });
          requestAnimationFrame(function () { HX.relayout(); requestAnimationFrame(function () {
            layout();
            if (pending) { var p = bySlug[pending]; pending = null; if (p) focusBoard(p); }
          }); });
        } else requestAnimationFrame(HX.relayout);
      },
      onKey: function (e) {
        if (e.key === "+" || e.key === "=") zoomBy(1.25);
        else if (e.key === "-") zoomBy(1 / 1.25);
        else if (e.key === "0") fit(true);
      }
    };
    var onZoomUser = null;
    Object.defineProperty(api, "onZoom", { get: function () { return function (zz) { zoomVal.textContent = Math.round(zz * 100) + "%"; if (onZoomUser) onZoomUser(zz); }; },
      set: function (fn) { onZoomUser = fn; } });
    return api;
  };
})();
