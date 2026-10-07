/* 08-sections.js — 사용 흐름 = 디자이너식 구역 보드 (Figma 보드처럼 한 캔버스).
   큰 구역(screens.json sections: 가입·처음 시작 / 홈 / …) → 단계 이름표(screen.step) → 화면을 순서대로 나란히.
   같은 단계의 상태 화면(빈칸·오류·완료, variantOf)은 원래 화면 옆에 붙는다. 화살표는 모든 화면을 잇지 않고
   조건이 갈리는 곳(flow.json step·branch의 when)에만 + 조건 이름표. 화면 아래에는 정책 메모(screen.policy) 검은 상자.
   화면을 눌러도 다른 곳으로 넘어가지 않는다(끌면 캔버스 이동만). 화면 위 번호·이름 줄 옆의 작은 아이콘 버튼이
   보드에서는 '의견 남기기'(화면 디자인 탭), 최종본에서는 '크게 보기'(그 화면으로 다가가기).
   HX.buildSections({ onPick(slug), pickTitle, pickIcon }) → { el, onShow, focus(slug), focusSection(key), zoomBy, fit, onKey, onZoom, mark(slug, tags) }
   보드(22-board-canvas)와 최종본(10-final)이 함께 쓴다. */
(function () {
  "use strict";
  var HX = window.HX, SVG = "http://www.w3.org/2000/svg";

  var STATE_LABEL = { "first-run": "처음 켰을 때", empty: "데이터 없을 때", input: "입력할 때", error: "오류일 때", success: "완료됐을 때" };
  HX.stateLabel = function (st) { return STATE_LABEL[st] || ""; };
  /* 정책 묶음 + 움직임(screen.motion의 note) — 움직임은 완성본에서 직접 해 볼 수 있다는 표시와 함께 마지막 묶음으로 */
  HX.policyBlocks = function (s) {
    var out = (s.policy || []).slice(), mv = (s.motion || []).filter(function (m) { return m.note; });
    // 안내·예외: 누르면 뜨는 안내(조각의 data-stay) · 글자 수(입력칸) · 이럴 땐 이렇게(screens.json cases)
    if (s.when && (s.state === "error" || s.state === "success")) out.unshift({ kind: "case", title: "언제 나오나요", items: [s.when] });
    if ((s.outs || []).length) out.push({ kind: "out", title: "앱 밖으로 나가는 버튼", items: s.outs.map(function (x) { return "'" + x.label + "' → " + x.text; }) });
    if ((s.stays || []).length) out.push({ kind: "stay", title: "누르면 뜨는 안내", items: s.stays.map(function (x) { return "'" + x.label + "' → " + x.text + (x.tone === "danger" ? " (오류)" : ""); }) });
    if ((s.limits || []).length) out.push({ kind: "limit", title: "글자 수", items: s.limits.map(function (l) { return "'" + l.name + "' " + (l.min && l.max ? l.min + "~" + l.max + "자" : l.max ? l.max + "자까지" : l.min ? l.min + "자 이상" : "제한 없음"); }) });
    if ((s.cases || []).length) out.push({ kind: "case", title: "이럴 땐 이렇게", items: s.cases.map(function (c) { return c.when + " → " + c.show; }) });
    if (mv.length) out.push({ title: "움직임 · 완성본에서 직접 해 볼 수 있어요", items: mv.map(function (m) { return m.note; }), motion: true });
    return out;
  };
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
    // 상태 화면(사용자: "모든 디테일한 화면들 하나하나"): 엣지 케이스·누르면 뜨는 안내·앱 밖 버튼마다 원래 화면 위에 얹은 한 장을 원래 화면 바로 옆에
    secs.forEach(function (x) { var S = byKey[x.key]; if (S) S.groups.forEach(function (g) {
      var out = [];
      g.items.forEach(function (s) { out.push(s); derivedOf(s).forEach(function (d) { out.push(d); }); });
      g.items = out;
    }); });
    return secs.map(function (x) { return byKey[x.key]; }).filter(function (x) { return x.groups.length; });
  }
  // 조건 화살표: 흐름 단계·갈래 중 when이 있는 것만
  var TONE_TAG = { danger: "오류", warning: "주의", info: "안내", success: "완료" };
  function eul(w) { return window.HXJosa ? window.HXJosa.eul(w) : "'" + w + "'을"; }
  function derivedOf(s) {
    var list = [];
    (s.outs || []).forEach(function (x) { list.push({ kind: "out", tag: "앱 밖", title: eul(x.label) + " 누르면", show: { out: x.text, label: x.label, cap: eul(x.label) + " 누르면" } }); });
    (s.stays || []).forEach(function (x) { list.push({ kind: x.tone || "success", tag: TONE_TAG[x.tone] || "완료", title: eul(x.label) + " 누르면", show: { text: x.text, tone: x.tone, sub: eul(x.label) + " 누르면", cap: eul(x.label) + " 누르면" } }); });
    (s.cases || []).forEach(function (c) { list.push({ kind: c.tone || "danger", tag: TONE_TAG[c.tone] || "오류", title: c.when, show: { text: c.show, tone: c.tone || "danger", sub: c.when, cap: "이럴 때 · " + c.when } }); });
    return list.map(function (d, i) { return { _derived: true, base: s, slug: s.slug + "~" + (i + 1), id: s.id, n: i + 1, name: d.title, tag: d.tag, kind: d.kind, show: d.show, section: s.section, role: s.role, overlayOf: s.overlayOf }; });
  }
  function allSteps() {
    var out = [];
    (HX.data.flows || []).forEach(function (f) { (f.steps || []).forEach(function (st) { out.push(st); }); });
    return out.concat(HX.data.branches || []).filter(function (l) { return HX.bySlug[l.from] && HX.bySlug[l.to]; });
  }
  // 화살표: 조건이 갈리는 곳(when, 초록) + 뜨는 창을 여는 버튼(회색 점선 — 어떤 버튼으로 여는지 안 보이면 헷갈린다)
  function links() {
    var all = allSteps(), out = all.filter(function (l) { return l.when; });
    HX.data.screens.forEach(function (s) {
      if (!s.overlayOf || out.some(function (l) { return l.to === s.slug; })) return;
      var l = all.filter(function (x) { return x.to === s.slug; })[0];
      if (l) out.push({ from: l.from, to: l.to, trigger: l.trigger, action: l.action, open: true });
    });
    return out;
  }
  // 지난 의견을 반영해 바뀐 점: screens.json board.changes [{ slug, said, did }]
  HX.changesOf = function (slug) { return (((HX.data.board || {}).changes) || []).filter(function (c) { return c && c.slug === slug; }); };
  HX.changeLine = function (c) { return (c.said ? "의견 '" + c.said + "' → " : "") + (c.did || ""); };
  // 이 화면에서 다른 화면으로 가는 버튼 (튜토리얼: "'측정 시작'을 누르면 → '측정 중'으로")
  HX.goesOf = function (slug) {
    var seen = {}, out = [];
    allSteps().forEach(function (l) { if (l.from !== slug || !l.trigger || seen[l.trigger]) return; seen[l.trigger] = 1; out.push({ trigger: l.trigger, action: l.action || "누르면", to: HX.bySlug[l.to].name }); });
    return out;
  };
  // 이 화면에 들어오는 길: "08 오늘에서 '밤사이 기록 보기'를 누르면" · 메뉴 '오늘'
  HX.incoming = function (slug) {
    var seen = {}, out = [];
    allSteps().forEach(function (l) {
      if (l.to !== slug || l.from === slug) return;
      var f = HX.bySlug[l.from], t = String(f.id).padStart(2, "0") + " " + f.name + "에서 " + (l.action || "누르면");
      if (!seen[t]) { seen[t] = 1; out.push(t); }
    });
    (HX.meta.roles || []).forEach(function (r) { (r.nav || []).forEach(function (n) { if (n.slug === slug) out.push((HX.platform === "mobile" ? "아래 메뉴 " : "메뉴 ") + eul(n.label) + " 누르면"); }); });
    return out;
  };

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
        HX.el("span", { text: "화면 " + sec.groups.reduce(function (n, g) { return n + g.items.filter(function (x) { return !x._derived; }).length; }, 0) + "개 · 상태 " + sec.groups.reduce(function (n, g) { return n + g.items.filter(function (x) { return x._derived; }).length; }, 0) + "개" })]);
      world.appendChild(band);
      var S = { key: sec.key, band: band, groups: [] };
      sec.groups.forEach(function (g) {
        var tag = HX.el("div", { class: "hx-sx-step", text: g.step });
        world.appendChild(tag);
        var G = { tag: tag, boards: [] };
        g.items.forEach(function (s) {
          if (s._derived) { G.boards.push(derivedBoard(s, S)); return; }
          var label = HX.el("div", { class: "hx-sx-label" }, [HX.el("span", { class: "hx-sx-n", text: String(s.id).padStart(2, "0") }), HX.el("b", { text: s.name }),
            s.state ? HX.el("span", { class: "hx-sx-state hx-st-" + s.state, text: HX.stateLabel(s.state) }) : null,
            HX.el("span", { class: "hx-sx-marks" })]);
          var pick = HX.el("button", { type: "button", class: "hx-sx-pick", title: (opts.pickTitle || "크게 보기") + " — " + s.name, "aria-label": (opts.pickTitle || "크게 보기") + " — " + s.name },
            [opts.pickIcon === "comment" ? HX.icon("#i-message-circle") : HX.icon("#i-maximize-2"), HX.el("span", { text: opts.pickTitle || "크게 보기" })]);
          label.insertBefore(pick, label.querySelector(".hx-sx-marks"));
          var blocks = HX.policyBlocks(s), info = null;
          if (blocks.length || HX.incoming(s.slug).length || HX.changesOf(s.slug).length) {   // ⓘ — 마우스를 올리면 이 화면의 규칙·오는 길·반영한 의견이 카드로 뜬다
            info = HX.el("button", { type: "button", class: "hx-sx-info", "aria-label": "이 화면의 규칙 — " + s.name }, HX.icon("#i-info"));
            label.insertBefore(info, pick);
          }
          pick.addEventListener("pointerdown", function (e) { e.stopPropagation(); });
          var box = HX.el("div", { class: "hx-cv-board hx-sx-board", dataset: { screen: s.slug }, style: "width:" + W + "px" });
          var note = blocks.length ? HX.el("div", { class: "hx-sx-note", style: "width:" + W + "px" }, blocks.map(function (p) {
            return HX.el("div", { class: "hx-sx-pol hx-k-" + (p.kind || (p.motion ? "motion" : "policy")) }, [HX.el("b", { text: p.motion ? "움직임" : p.title }), HX.el("ul", {}, (p.items || []).map(function (t) { return HX.el("li", { text: t }); }))]);
          })) : null;
          label.style.maxWidth = W + "px";   // 이름표가 옆 화면 이름표와 겹치지 않게 — 넘치는 이름은 …로
          world.appendChild(label); world.appendChild(box); if (note) world.appendChild(note);
          var b = { slug: s.slug, label: label, box: box, note: note, frame: null, sec: S, screen: s, blocks: blocks };
          if (info) wireInfo(info, b);
          // 움직임: 화면에 마우스를 올리면 그 자리에서 재생, 떼면 원래대로 (packages/core/motion)
          // 보드는 정적인 지도 — 움직임은 '흐름 재생' 탭과 화면 디자인의 '움직임 보기'에서 (사용자: "화면은 따로, 워크플로우 애니메이션은 따로")
          pick.addEventListener("click", function (e) { e.stopPropagation(); if (opts.onPick) opts.onPick(s.slug); else focusBoard(b); });
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
          var vis = G.boards.filter(function (b) { return statesOn || !b.derived; });
          var gw = vis.length * W + (vis.length - 1) * GAP;
          if (x > 0 && x + gw > MAXW) { lines.push([]); x = 0; }
          lines[lines.length - 1].push({ G: G, x: x }); x += gw + GROUP;
        });
        lines.forEach(function (ln) {
          var rowH = 0, top = y + TAG + LAB;
          ln.forEach(function (it) {
            it.G.tag.style.left = it.x + "px"; it.G.tag.style.top = y + "px";
            it.G.boards.filter(function (b) { return statesOn || !b.derived; }).forEach(function (b, i) {
              var bx = it.x + i * (W + GAP);
              b.x = bx; b.y = top; b.lineY = y; b.h = b.box.offsetHeight || HX.frame.h;
              b.label.style.left = bx + "px"; b.label.style.top = (top - LAB) + "px";
              b.box.style.left = bx + "px"; b.box.style.top = top + "px";
              var h = b.h;
              if (b.note && notesOn) { b.note.style.left = bx + "px"; b.note.style.top = (top + b.h + 28 * K) + "px"; h += 28 * K + b.note.offsetHeight; }
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
      defs.innerHTML = '<marker id="hx-sx-arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker><marker id="hx-sx-arr-open" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#6B7280"/></marker>';
      svg.appendChild(defs);
      // 화면 → 그 화면의 상태 화면들: 화면 아래에서 빗살 모양의 회색 선 (사용자: "각 화면별로 케이스들은 선으로 연결")
      boards.forEach(function (b) {
        if (b.derived || !b.h) return;
        var kids = boards.filter(function (d) { return d.derived && d.screen === b.screen && d.box.style.display !== "none" && d.h; });
        if (!kids.length) return;
        var all = [b].concat(kids), bottom = 0;
        all.forEach(function (x) { bottom = Math.max(bottom, x.y + x.h + (x.note && notesOn ? 28 * K + x.note.offsetHeight : 0)); });
        var busY = bottom + 26 * K, x0 = b.x + W / 2, x1 = kids[kids.length - 1].x + W / 2;
        var d = "M" + x0 + "," + (b.y + b.h + 6 * K) + " V" + busY + " H" + x1;
        kids.forEach(function (k) { d += " M" + (k.x + W / 2) + "," + busY + " V" + (k.y + k.h + 8 * K); });
        var p = document.createElementNS(SVG, "path"); p.setAttribute("d", d); p.setAttribute("class", "hx-sx-comb"); svg.appendChild(p);
        kids.forEach(function (k) { var c = document.createElementNS(SVG, "circle"); c.setAttribute("cx", k.x + W / 2); c.setAttribute("cy", k.y + k.h + 8 * K); c.setAttribute("r", 5 * K); c.setAttribute("class", "hx-sx-comb-dot"); svg.appendChild(c); });
      });
      links().forEach(function (l) {
        var A = bySlug[l.from], B = bySlug[l.to]; if (!A || !B || !A.h) return;
        var t = trigPoint(A, l.trigger), sx, sy, d, px, py, a = 32 * K;
        if (t) svg.appendChild(rect(t, l.open));
        var bh = Math.min(B.h, HX.frame.h);
        var between = boards.some(function (o) { return o.y === A.y && o.x > A.x && o.x < B.x; });
        if (B.x > A.x + W / 2 && Math.abs(B.y - A.y) < 4 && (between || l.open)) {   // 같은 줄, 사이에 화면이 있거나 창을 여는 버튼이면: 줄 위 빈칸으로(이름표가 화면을 가리지 않게)
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
        path.setAttribute("d", d); path.setAttribute("class", "hx-sx-path" + (l.open ? " hx-sx-open" : "")); path.setAttribute("marker-end", l.open ? "url(#hx-sx-arr-open)" : "url(#hx-sx-arr)");
        svg.appendChild(path);
        var pill = HX.el("div", { class: "hx-sx-when" + (l.open ? " hx-sx-open-pill" : ""), text: l.open ? l.action : l.when, title: (l.action || "") + " → " + HX.bySlug[l.to].name });
        pill.style.left = px + "px"; pill.style.top = py + "px";
        world.appendChild(pill);
      });
    }
    function rect(t, open) {
      var r = document.createElementNS(SVG, "rect"), p = 6 * K;
      r.setAttribute("x", t.x - p); r.setAttribute("y", t.y - p); r.setAttribute("width", t.w + p * 2); r.setAttribute("height", t.h + p * 2);
      r.setAttribute("rx", 8 * K); r.setAttribute("class", "hx-sx-trig" + (open ? " hx-sx-trig-open" : "")); return r;
    }

    // ---- 상태 화면 한 장: 원래 화면 조각에 안내 상자·'앱 밖' 카드를 얹는다 ----
    function derivedBoard(d, S) {
      var label = HX.el("div", { class: "hx-sx-label hx-sx-derived" }, [HX.el("span", { class: "hx-sx-n", text: String(d.id).padStart(2, "0") + "-" + d.n }),
        HX.el("span", { class: "hx-sx-state hx-st-d-" + d.kind, text: d.tag }), HX.el("b", { text: d.name })]);
      var pick = HX.el("button", { type: "button", class: "hx-sx-pick", title: (opts.pickTitle || "크게 보기") + " — " + d.base.name, "aria-label": (opts.pickTitle || "크게 보기") + " — " + d.base.name },
        [opts.pickIcon === "comment" ? HX.icon("#i-message-circle") : HX.icon("#i-maximize-2"), HX.el("span", { text: opts.pickTitle || "크게 보기" })]);
      var dinfo = HX.el("button", { type: "button", class: "hx-sx-info", "aria-label": "언제 나오는지 — " + d.name }, HX.icon("#i-info"));
      label.appendChild(dinfo); label.appendChild(pick);
      pick.addEventListener("pointerdown", function (e) { e.stopPropagation(); });
      var box = HX.el("div", { class: "hx-cv-board hx-sx-board hx-sx-dbox", dataset: { screen: d.slug }, style: "width:" + W + "px" });
      label.style.maxWidth = W + "px";
      world.appendChild(label); world.appendChild(box);
      var b = { slug: d.slug, mountSlug: d.base.slug, derived: true, label: label, box: box, note: null, frame: null, sec: S, screen: d.base,
        apply: function () {
          var app = b.frame && (b.frame.section.querySelector(".app") || b.frame.section); if (!app || !window.HXStatic) return;
          var sh = {}; Object.keys(d.show).forEach(function (k) { if (k !== "cap") sh[k] = d.show[k]; });   // '언제'는 화면 위가 아니라 ⓘ 카드에 텍스트로
          window.HXStatic(app, sh);
        } };
      b.dinfo = d; wireInfo(dinfo, b);
      pick.addEventListener("click", function (e) { e.stopPropagation(); if (opts.onPick) opts.onPick(d.base.slug); else focusBoard(b); });
      boards.push(b); bySlug[d.slug] = b;
      return b;
    }
    function setStates(on) {
      statesOn = on;
      boards.forEach(function (b) { if (b.derived) { b.label.style.display = b.box.style.display = on ? "" : "none"; } });
      statesBtn.classList.toggle("hx-on", on); statesBtn.setAttribute("aria-pressed", on ? "true" : "false");
      statesBtn.lastChild.textContent = on ? "상태 화면 접기" : "상태 화면 펼치기";
      layout();
    }

    // ---- ⓘ 정책 카드: 확대 비율과 상관없이 같은 크기로 읽히게 캔버스 바깥(vp)에 띄운다 ----
    var statesOn = true, notesOn = false, pop = HX.el("div", { class: "hx-sx-pop", role: "tooltip" }), popT = 0, popFor = null;
    pop.hidden = true; vp.appendChild(pop);
    pop.addEventListener("pointerdown", function (e) { e.stopPropagation(); });
    pop.addEventListener("wheel", function (e) { e.stopPropagation(); }, { passive: true });
    pop.addEventListener("mouseenter", function () { clearTimeout(popT); });
    pop.addEventListener("mouseleave", function () { hidePop(150); });
    function hidePop(ms) { clearTimeout(popT); popT = setTimeout(function () { pop.hidden = true; popFor = null; }, ms || 0); }
    function showPop(b, anchor) {
      clearTimeout(popT); popFor = b; pop.innerHTML = "";
      if (b.dinfo) {   // 상태 화면: 언제 · 보이는 문구 · 원래 화면
        var d = b.dinfo, blk = function (kind, title, items) { pop.appendChild(HX.el("div", { class: "hx-sx-pop-b" }, [HX.el("div", { class: "hx-sx-pop-t hx-k-" + kind }, [HX.icon(kind === "case" ? "#i-triangle-alert" : kind === "stay" ? "#i-message-circle" : "#i-log-in", "icon icon-sm"), title]), HX.el("ul", {}, items.map(function (t) { return HX.el("li", { text: t }); }))])); };
        pop.appendChild(HX.el("div", { class: "hx-sx-pop-h" }, [HX.el("span", { class: "hx-sx-n", text: String(d.id).padStart(2, "0") + "-" + d.n }), HX.el("b", { text: d.tag + " 상태" }), HX.el("span", { text: "언제 나오나요" })]));
        blk("case", "언제", [d.name]);
        blk("stay", d.show.out ? "앱 밖으로 나가요" : "보이는 문구", [d.show.out || d.show.text]);
        blk("in", "원래 화면", [String(d.base.id).padStart(2, "0") + " " + d.base.name]);
        pop.hidden = false; placePop(anchor); return;
      }
      pop.appendChild(HX.el("div", { class: "hx-sx-pop-h" }, [HX.el("span", { class: "hx-sx-n", text: String(b.screen.id).padStart(2, "0") }), HX.el("b", { text: b.screen.name }), HX.el("span", { text: "이 화면의 규칙" })]));
      var chg = HX.changesOf(b.screen.slug);
      if (chg.length) pop.appendChild(HX.el("div", { class: "hx-sx-pop-b hx-sx-pop-chg" }, [HX.el("div", { class: "hx-sx-pop-t" }, [HX.icon("#i-pencil", "icon icon-sm"), "지난 의견을 반영했어요"]),
        HX.el("ul", {}, chg.map(function (c) { return HX.el("li", { text: HX.changeLine(c) }); }))]));
      var inc = HX.incoming(b.screen.slug);
      if (inc.length) pop.appendChild(HX.el("div", { class: "hx-sx-pop-b hx-sx-pop-in" }, [HX.el("div", { class: "hx-sx-pop-t" }, [HX.icon("#i-log-in", "icon icon-sm"), "이 화면으로 오는 길"]),
        HX.el("ul", {}, inc.map(function (t) { return HX.el("li", { text: t }); }))]));
      b.blocks.forEach(function (p) {
        pop.appendChild(HX.el("div", { class: "hx-sx-pop-b" + (p.motion ? " hx-sx-pop-motion" : "") }, [
          HX.el("div", { class: "hx-sx-pop-t hx-k-" + (p.kind || (p.motion ? "motion" : "policy")) }, [p.motion ? HX.icon("#i-sparkles", "icon icon-sm") : p.kind === "stay" ? HX.icon("#i-message-circle", "icon icon-sm") : p.kind === "limit" ? HX.icon("#i-a-large-small", "icon icon-sm") : p.kind === "case" ? HX.icon("#i-triangle-alert", "icon icon-sm") : HX.icon("#i-circle-check", "icon icon-sm"), p.motion ? "움직임 · '흐름 재생'과 '움직임 보기'에서 볼 수 있어요" : p.title]),
          HX.el("ul", {}, (p.items || []).map(function (t) { return HX.el("li", { text: t }); }))]));
      });
      pop.hidden = false; placePop(anchor);
    }
    function placePop(anchor) {
      var vr = vp.getBoundingClientRect(), ar = anchor.getBoundingClientRect(), pw = pop.offsetWidth, ph = pop.offsetHeight;
      var x = HX.clamp(ar.left - vr.left - 12, 8, vr.width - pw - 8), y = ar.bottom - vr.top + 8;
      if (y + ph > vr.height - 8) y = Math.max(8, ar.top - vr.top - ph - 8);
      pop.style.left = x + "px"; pop.style.top = y + "px";
    }
    function wireInfo(btn, b) {
      btn.addEventListener("pointerdown", function (e) { e.stopPropagation(); });
      btn.addEventListener("mouseenter", function () { showPop(b, btn); });
      btn.addEventListener("mouseleave", function () { hidePop(200); });
      btn.addEventListener("focus", function () { showPop(b, btn); });
      btn.addEventListener("blur", function () { hidePop(200); });
      btn.addEventListener("click", function (e) { e.stopPropagation(); if (popFor === b && !pop.hidden) hidePop(0); else showPop(b, btn); });
    }
    function setNotes(on) {
      notesOn = on; world.classList.toggle("hx-sx-notes-on", on);
      notesBtn.classList.toggle("hx-on", on); notesBtn.setAttribute("aria-pressed", on ? "true" : "false");
      notesBtn.lastChild.textContent = on ? "정책 접기" : "정책 펼치기";
      layout();
    }

    // ---- 확대·축소·이동 (11-final-all과 같은 손맛) ----
    var z = 0.2, tx = 40, ty = 80, dragged = false, mounted = false, fitted = false;
    function apply(anim) {
      world.classList.toggle("hx-anim", !!anim);
      world.style.transform = "translate(" + tx + "px," + ty + "px) scale(" + z + ")";
      if (!pop.hidden) hidePop(0);
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
    var notesBtn = HX.btn("정책 펼치기", { icon: HX.icon("#i-file-text"), title: "모든 화면 아래에 규칙을 펼쳐 보기", onclick: function () { setNotes(!notesOn); } });
    notesBtn.setAttribute("aria-pressed", "false");
    var statesBtn = HX.btn("상태 화면 접기", { icon: HX.icon("#i-layers"), title: "엣지 케이스·안내 문구·앱 밖 버튼을 한 장씩 보여 주는 화면을 접거나 펼쳐요", onclick: function () { setStates(!statesOn); } });
    statesBtn.classList.add("hx-on"); statesBtn.setAttribute("aria-pressed", "true");
    var tools = HX.el("div", { class: "hx-cv-tools hx-sx-tools" }, [
      HX.el("div", { class: "hx-sx-jump", role: "group", "aria-label": "구역으로 가기" }, secEls.map(function (S, i) {
        return HX.btn(secs[i].name, { title: secs[i].name + " 구역으로", onclick: function () { focusSection(S.key); } });
      })),
      HX.el("span", { class: "hx-sx-sep" }),
      HX.btn("", { cls: "hx-icon-btn", aria: "축소", title: "축소 (−)", icon: HX.icon("#i-zoom-out"), onclick: function () { zoomBy(1 / 1.25); } }), zoomVal,
      HX.btn("", { cls: "hx-icon-btn", aria: "확대", title: "확대 (+)", icon: HX.icon("#i-zoom-in"), onclick: function () { zoomBy(1.25); } }),
      HX.btn("전체 보기", { icon: HX.icon("#i-maximize-2"), title: "모두 보이게 (0)", onclick: function () { fit(true); } }),
      HX.el("span", { class: "hx-sx-sep" }), notesBtn, statesBtn]);
    tools.addEventListener("pointerdown", function (e) { e.stopPropagation(); });
    vp.appendChild(tools);
    vp.appendChild(HX.el("div", { class: "hx-sx-legend" }, [HX.el("span", { class: "hx-sx-lg-arrow" }), "초록 = 조건이 갈리는 곳 · 회색 점선 = 버튼을 누르면 뜨는 창 · ⓘ = 그 화면의 규칙과 오는 길 · ⌘/Ctrl+휠 확대"]));

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
      /* 보드: 화면 위 이름표 옆에 '의견 반영'·'뺌'·메모 표시 */
      mark: function (slug, tags) {
        var b = bySlug[slug]; if (!b) return;
        var m = b.label.querySelector(".hx-sx-marks"); m.innerHTML = "";
        (tags || []).forEach(function (t) {
          var el = HX.el("span", { class: "hx-sx-mark hx-sx-mark-" + t.kind, text: t.text, title: t.kind === "fixed" ? null : t.title || null });
          if (t.kind === "fixed") {   // '의견 반영'에 마우스를 올리면 무엇을 바꿨는지 카드로
            el.addEventListener("mouseenter", function () { showPop(b, el); });
            el.addEventListener("mouseleave", function () { hidePop(200); });
          }
          m.appendChild(el);
        });
        b.box.classList.toggle("hx-sx-removed", (tags || []).some(function (t) { return t.kind === "removed"; }));
      },
      onShow: function () {
        if (!mounted) {
          mounted = true;
          boards.forEach(function (b) {
            b.frame = HX.mountFrame(b.mountSlug || b.slug, b.box, { scale: 1, fullHeight: true, badges: false });
            if (b.apply) b.apply();
          });
          setTimeout(function () { if (window.HXMarkSwipe) boards.forEach(function (b) { if (b.frame) window.HXMarkSwipe(b.frame.section); }); }, 400);   // 옆으로 넘치는 줄 끝을 흐리게
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
