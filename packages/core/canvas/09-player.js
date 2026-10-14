/* 09-player.js — '흐름 재생' 탭: 흐름(flow.json) 하나를 영상처럼 처음부터 끝까지 재생한다.
   사용자 결정(2026-10-07): "화면은 따로, 전체 워크플로우를 애니메이션으로 모은 영역도 따로" → 구역 보드는 정적인 지도, 움직임은 여기서.
   왼쪽 흐름 목록 · 가운데 화면(휴대폰/데스크톱) · 아래 단계 설명과 재생/멈춤 · 이전/다음 · 속도.
   단계마다: 화면이 나타남 → (오류·완료 화면) → 그 화면의 동작을 빠짐없이 한 번씩(HXMotion once: 스크롤·고르기·타이핑·밀기·안내 문구·엣지 케이스…)
   → 손가락(데스크톱은 커서)이 그 단계의 버튼을 누름(가려져 있으면 내려가서 · 길게 누르기면 길게) → 다음 화면으로 넘어감.
   HX.buildPlayer() → { el, onShow, onHide, onKey } — 보드(24)와 최종 입구(10)가 함께 쓴다. */
(function () {
  "use strict";
  var HX = window.HX, doc = document;
  function roleName(role) { var l = HX.roleLabel(role).replace(/\(.*\)/, ""); return l === "부모" ? "부모님" : l; }
  function eul(w) { return window.HXJosa ? window.HXJosa.eul(w) : "'" + w + "'을"; }
  function ro(w) { return window.HXJosa ? window.HXJosa.ro(w) : "'" + w + "'(으)로"; }
  function quoteOf(action) { return (String(action || "").match(/'([^']+)'/) || [])[1] || ""; }

  HX.buildPlayer = function () {
    var mobile = HX.platform === "mobile";
    var flows = (HX.data.flows || []).filter(function (f) { return (f.steps || []).some(function (st) { return HX.bySlug[st.from] && HX.bySlug[st.to]; }); });
    var el = HX.el("div", { class: "hx-pl" });
    var list = HX.el("nav", { class: "hx-pl-list", "aria-label": "흐름 목록" });
    var stage = HX.el("div", { class: "hx-pl-stage" });
    var screenBox = HX.el("div", { class: "hx-pl-screen" + (mobile ? " is-mobile" : "") });
    var cap = HX.el("div", { class: "hx-pl-cap" }), stepNo = HX.el("b", { class: "hx-pl-no" }), stepTxt = HX.el("span");
    cap.appendChild(stepNo); cap.appendChild(stepTxt);
    var prevB = HX.btn("", { cls: "hx-icon-btn", aria: "이전 단계", title: "이전 단계 (←)", icon: HX.icon("#i-chevron-left"), onclick: function () { jump(cur - 1); } });
    var playB = HX.btn("멈춤", { cls: "hx-pl-play", title: "재생 / 멈춤 (스페이스)", icon: HX.icon("#i-pause"), onclick: function () { toggle(); } });
    var nextB = HX.btn("", { cls: "hx-icon-btn", aria: "다음 단계", title: "다음 단계 (→)", icon: HX.icon("#i-chevron-right"), onclick: function () { jump(cur + 1); } });
    var againB = HX.btn("처음부터", { icon: HX.icon("#i-rotate-ccw-clock"), onclick: function () { start(fi); } });
    var speedB = HX.btn("1×", { cls: "hx-pl-speed", title: "속도", onclick: function () { speed = speed === 1 ? 1.6 : speed === 1.6 ? 0.6 : 1; speedB.lastChild.textContent = speed === 1 ? "1×" : speed > 1 ? "빠르게" : "천천히"; } });
    // 오류·예외 보기: 버튼을 누르기 전에 그 화면의 오류·완료 화면과 엣지 케이스 문구를 먼저 (사용자: "에러나 이런 것들 없는 건가")
    var errB = HX.btn("오류·예외 보기", { cls: "hx-on", title: "각 화면의 오류·완료 상태와 엣지 케이스도 재생해요", icon: HX.icon("#i-triangle-alert"), onclick: function () {
      showErr = !showErr; errB.classList.toggle("hx-on", showErr); errB.setAttribute("aria-pressed", showErr ? "true" : "false");
    } });
    errB.setAttribute("aria-pressed", "true");
    // 화면 동작 보기: 화면마다 스크롤·고르기·타이핑·밀기 같은 실제 동작을 먼저 해 보고 넘어간다 (끄면 버튼만 눌러 빠르게)
    var moveB = HX.btn("화면 동작 보기", { cls: "hx-on", title: "화면마다 스크롤·고르기·타이핑·밀기 같은 동작을 해 보고 넘어가요", icon: HX.icon("#i-hand"), onclick: function () {
      moveOn = !moveOn; moveB.classList.toggle("hx-on", moveOn); moveB.setAttribute("aria-pressed", moveOn ? "true" : "false");
    } });
    moveB.setAttribute("aria-pressed", "true");
    var controls = HX.el("div", { class: "hx-pl-ctl" }, [prevB, playB, nextB, HX.el("span", { class: "hx-pl-sep" }), againB, speedB, moveB, errB]);
    var bubble = HX.el("div", { class: "hx-pl-bubble" }); bubble.hidden = true;
    // 말풍선에서 화면 속 문구까지 잇는 화살표 + 문구 둘레 표시 (사용자: "말풍선의 화살표로 에러 문구 위치를 보여 주자")
    var SVGNS = "http://www.w3.org/2000/svg";
    var link = doc.createElementNS(SVGNS, "svg"); link.setAttribute("class", "hx-pl-link"); link.style.display = "none";
    stage.appendChild(screenBox); stage.appendChild(cap); stage.appendChild(controls);
    el.appendChild(list); el.appendChild(stage);

    var items = [];
    flows.forEach(function (f, i) {
      var who = roleName(f.role);
      var b = HX.el("button", { type: "button", class: "hx-pl-item", onclick: function () { start(i); } }, [
        HX.el("span", { class: "hx-pl-n", text: String(i + 1) }),
        HX.el("span", { class: "hx-pl-t" }, [HX.el("b", { text: f.name }), HX.el("small", { text: who + " · " + (f.steps || []).length + "단계" })])]);
      items.push(b); list.appendChild(b);
    });

    // ---- 재생 상태 ----
    var showErr = true, moveOn = true, mo = null, ended = false, fi = 0, seq = [], cur = 0, playing = true, speed = 1, timers = [], frame = null, app = null, fg = null, token = 0;
    function later(fn, ms) { var my = token, t = setTimeout(function () { if (my === token) fn(); }, ms / speed); timers.push(t); return t; }
    function clear() { token++; timers.forEach(clearTimeout); timers = []; if (mo) { mo.stop(); mo = null; } bubble.hidden = true; link.style.display = "none"; }
    function seqOf(f) {   // [{ slug, step(이 화면에서 누를 단계) }]
      var out = [], ok = (f.steps || []).filter(function (st) { return HX.bySlug[st.from] && HX.bySlug[st.to]; });
      ok.forEach(function (st, i) { if (i === 0 || ok[i - 1].to !== st.from) out.push({ slug: st.from, step: st }); else out[out.length - 1].step = st; out.push({ slug: st.to, step: null }); });
      return out;
    }
    function holdOf(slug, trigger) { var s = HX.bySlug[slug]; return ((s && s.motion) || []).filter(function (m) { return m.type === "hold" && m.target === trigger; })[0] || null; }

    function mount(slug, how) {
      var old = screenBox.querySelector(".hx-pl-frame");
      var holder = HX.el("div", { class: "hx-pl-frame" + (how ? " in-" + how : "") });
      screenBox.appendChild(holder);
      frame = HX.mountFrame(slug, holder, { fit: "contain", badges: false, pad: 0 });
      app = frame.section.querySelector(".app") || frame.section;
      fg = HX.el("div", { class: "mo-finger" + (mobile ? "" : " mo-finger-desk") }); fg.hidden = true; app.appendChild(fg);
      var s = HX.bySlug[slug];
      if (s && s.overlayOf) { var bd = app.querySelector(".modal-backdrop"); if (bd) { bd.classList.remove("mo-in"); void bd.offsetWidth; bd.classList.add("mo-in"); } }
      if (old) { old.classList.add("out-" + (how || "fade")); setTimeout(function () { if (old.parentNode) old.remove(); }, 420); }
      HX.relayout();
    }
    function sc() { var r = app.getBoundingClientRect(); return (r.width / app.offsetWidth) || 1; }
    function center(t) { var a = app.getBoundingClientRect(), r = t.getBoundingClientRect(), k = sc(); return { x: (r.left - a.left + r.width / 2) / k, y: (r.top - a.top + r.height / 2) / k }; }
    function moveTo(p, ms) { fg.hidden = false; fg.style.transition = "left " + ms / speed + "ms cubic-bezier(.2,.8,.2,1), top " + ms / speed + "ms cubic-bezier(.2,.8,.2,1), transform .15s ease"; fg.style.left = p.x + "px"; fg.style.top = p.y + "px"; }
    function say(no, txt) { stepNo.textContent = no; stepTxt.textContent = txt; }
    // 화면 옆 말풍선: 이 화면이 언제 나오는지 · 이 안내가 언제 뜨는지 — 자리가 없으면 화면 위 오른쪽 위에
    var KIND = { danger: "오류", warning: "주의", info: "안내", success: "완료" };
    var TONE_HEX = { danger: "#D92D20", warning: "#DC6803", success: "#16A34A", info: "#2563EB" };
    function note(text, tone, target) {
      if (!text) { bubble.hidden = true; link.style.display = "none"; return; }
      tone = KIND[tone] ? tone : "danger";
      bubble.innerHTML = ""; bubble.className = "hx-pl-bubble";
      bubble.appendChild(HX.el("span", { class: "hx-pl-bubble-k is-" + tone, text: KIND[tone] === "완료" ? "이렇게 되면" : "이런 경우" }));
      bubble.appendChild(HX.el("p", { text: text }));
      if (bubble.parentNode !== screenBox) screenBox.appendChild(bubble);
      if (link.parentNode !== screenBox) screenBox.appendChild(link);
      bubble.hidden = false;
      var b = screenBox.getBoundingClientRect(), fr = frame && frame.el.getBoundingClientRect(); if (!fr) return;
      var tr = target && target.isConnected ? target.getBoundingClientRect() : null;
      if (tr && !tr.width) tr = null;
      var W = 240, gap = 28, H = bubble.offsetHeight || 80, side;
      var ty = tr ? tr.top - b.top + tr.height / 2 : fr.top - b.top + 64;
      var top = Math.max(8, Math.min(b.height - H - 8, ty - 26));
      if (b.right - fr.right >= W + gap + 8) { side = "right"; bubble.style.left = (fr.right - b.left + gap) + "px"; }
      else if (fr.left - b.left >= W + gap + 8) { side = "left"; bubble.style.left = (fr.left - b.left - gap - W) + "px"; }
      else { side = "in"; bubble.style.left = Math.max(8, fr.right - b.left - W - 12) + "px"; top = Math.max(8, fr.top - b.top + 12); }
      bubble.classList.add("at-" + side); bubble.style.top = top + "px";
      if (!tr) { link.style.display = "none"; return; }
      // 화살표: 말풍선 꼬리 → 문구 가장자리 · 문구 둘레에 색 테두리
      var c = TONE_HEX[tone], bx = bubble.offsetLeft, tail = top + 24, sx, sy, ex, ey;
      if (side === "right") { sx = bx - 7; sy = tail; ex = tr.right - b.left + 6; ey = ty; }
      else if (side === "left") { sx = bx + W + 7; sy = tail; ex = tr.left - b.left - 6; ey = ty; }
      else { sx = bx + W / 2; sy = top + H; ex = tr.left - b.left + tr.width / 2; ey = tr.top - b.top - 6; }
      link.innerHTML = "";
      link.setAttribute("viewBox", "0 0 " + b.width + " " + b.height); link.setAttribute("width", b.width); link.setAttribute("height", b.height);
      var defs = doc.createElementNS(SVGNS, "defs"), mk = doc.createElementNS(SVGNS, "marker");
      mk.setAttribute("id", "hx-pl-arrow"); mk.setAttribute("viewBox", "0 0 10 10"); mk.setAttribute("refX", "8"); mk.setAttribute("refY", "5");
      mk.setAttribute("markerWidth", "7"); mk.setAttribute("markerHeight", "7"); mk.setAttribute("orient", "auto-start-reverse");
      var head = doc.createElementNS(SVGNS, "path"); head.setAttribute("d", "M0 0 L10 5 L0 10 z"); head.setAttribute("fill", c);
      mk.appendChild(head); defs.appendChild(mk); link.appendChild(defs);
      var mx = (sx + ex) / 2, path = doc.createElementNS(SVGNS, "path");
      path.setAttribute("d", side === "in" ? "M" + sx + " " + sy + " L" + ex + " " + ey : "M" + sx + " " + sy + " C" + mx + " " + sy + " " + mx + " " + ey + " " + ex + " " + ey);
      path.setAttribute("fill", "none"); path.setAttribute("stroke", c); path.setAttribute("stroke-width", "2.5"); path.setAttribute("stroke-linecap", "round"); path.setAttribute("marker-end", "url(#hx-pl-arrow)");
      path.setAttribute("class", "hx-pl-link-line");
      var ring = doc.createElementNS(SVGNS, "rect");
      ring.setAttribute("x", tr.left - b.left - 4); ring.setAttribute("y", tr.top - b.top - 4); ring.setAttribute("width", tr.width + 8); ring.setAttribute("height", tr.height + 8);
      ring.setAttribute("rx", "12"); ring.setAttribute("fill", "none"); ring.setAttribute("stroke", c); ring.setAttribute("stroke-width", "2.5"); ring.setAttribute("class", "hx-pl-link-ring");
      link.appendChild(path); link.appendChild(ring); link.style.display = "";
    }
    // 오류·완료 화면에서 그 문구가 있는 곳: 경고 띠 · 틀린 입력칸 · 안내 상자
    function msgEl(root) {
      return [].filter.call(root.querySelectorAll('[role="alert"], .banner-danger, .banner-warning, .banner-success, .banner, .field.is-error, .field-error, .toast, .alert'), function (x) { return x.offsetWidth > 0; })[0] || null;
    }
    function paintList() { items.forEach(function (b, i) { b.classList.toggle("hx-on", i === fi); b.setAttribute("aria-current", i === fi ? "true" : "false"); }); }
    function paintCtl() { prevB.disabled = cur <= 0; nextB.disabled = cur >= seq.length - 1; playB.lastChild.textContent = playing ? "멈춤" : "재생"; playB.querySelector("use").setAttribute("href", playing ? "#i-pause" : "#i-play"); }

    // 한 단계: 화면을 보여 주고 → (타이핑) → 버튼을 눌러 → 다음 화면
    function runStep(i, how) {
      clear(); cur = i; ended = false; paintCtl();
      var item = seq[i], s = HX.bySlug[item.slug], total = seq.length;
      mount(item.slug, how);
      fg.style.left = (app.offsetWidth / 2) + "px"; fg.style.top = (Math.min(app.offsetHeight, HX.frame.h) - 90) + "px";
      // 마지막 화면도 그 화면의 동작을 다 보여 준 뒤 끝낸다
      var st = item.step, label = st ? quoteOf(st.action) : "", to = st ? HX.bySlug[st.to] : null, no = (i + 1) + "/" + total;
      function finish() { say(no, "'" + s.name + "' — 흐름 끝이에요"); playing = false; ended = true; paintCtl(); }
      say(no, "'" + s.name + "' 화면");
      if (!st && !playing) { finish(); return; }
      if (!playing) return;
      var t0 = 900;
      if (showErr) {
        // 이 화면의 오류·완료 화면: 잠깐 바꿔 보여 주고 다시 원래 화면으로
        HX.data.screens.filter(function (v) { return v.variantOf === item.slug && (v.state === "error" || v.state === "success"); }).forEach(function (v) {
          // 화면을 바꾸고 → 문구가 가려져 있으면 그 위치로 내려가고 → 말풍선 + 화살표 → 1초 더 머문다
          var tg = null;
          later(function () { mount(v.slug, "fade"); say(no, v.state === "error" ? "오류 화면이에요" : "끝나면 이 화면이에요"); tg = msgEl(app); if (tg && window.HXReveal) window.HXReveal(app, tg, true); }, t0); t0 += 500;
          later(function () { note(v.when || v.name, v.state === "error" ? "danger" : "success", tg); }, t0); t0 += 3300;
          later(function () { note(null); mount(item.slug, "fade"); say(no, "다시 '" + s.name + "' 화면"); }, t0); t0 += 900;
        });
      }
      // 이 화면에서 할 수 있는 동작을 빠짐없이 한 번씩: 위아래 스크롤 · 고르기 · 스위치 · 타이핑 · 옆으로 밀기 · 길게 누르기 · 순서 바꾸기 · 재생 ·
      // 어두워짐 · 안내 문구 · 앱 밖으로 · 다른 길 버튼 · 엣지 케이스(오류·예외 보기가 켜져 있을 때) → 끝나면 이 단계의 버튼을 누른다
      // (사용자: "흐름 재생에 이전에 있던 스크롤이나 이런 것들이 다 안 보이는데" · "하나도 빼먹지 말고 다 넣어라")
      later(function () {
        if (!window.HXMotion || !moveOn) { next(); return; }
        mo = window.HXMotion(app, { overlay: false, items: s.motion || [], stays: s.stays || [], cases: showErr ? s.cases || [] : [], outs: s.outs || [], goes: HX.goesOf(item.slug) },
          { once: true, finger: fg, skip: st && st.trigger, speed: function () { return speed; }, say: function (t) { say(no, t); }, note: note, done: function () { mo = null; next(); } });
        function next() { if (st) tapStep(); else later(finish, 300); }
      }, t0);
      function btnNow() { return app.querySelector('[data-trigger="' + st.trigger + '"]'); }   // 오류 화면을 보여 주고 돌아오면 화면이 새로 붙으므로 그때 찾는다
      function tapStep() {
        var btn = btnNow(); if (!btn) { later(function () { advance(); }, 600); return; }
        var hold = holdOf(item.slug, st.trigger), holdMs = hold ? hold.ms || 2000 : 0;
        var d = window.HXReveal ? window.HXReveal(app, btn, true) : 0;   // 화면 아래에 가려진 버튼이면 먼저 내려간다
        if (d) say(no, "아래로 내려가요");
        later(function () {
          say(no, (label ? eul(label) + (hold ? " " + Math.round(holdMs / 1000) + "초 길게" : "") + " 누르면" : st.action) + " → " + ro(to.name) + " 넘어가요");
          moveTo(center(btn), 650);
        }, d);
        later(function () {
          fg.classList.add("down");
          if (hold) { fg.classList.add("hold"); var fill = doc.createElement("span"); fill.className = "mo-hold-fill"; btn.classList.add("mo-hold"); btn.appendChild(fill); requestAnimationFrame(function () { fill.style.transition = "transform " + holdMs / speed + "ms linear"; fill.style.transform = "scaleX(1)"; }); }
        }, d + 750);
        later(function () { fg.classList.remove("down", "hold"); }, d + 750 + (hold ? holdMs : 180));
        later(function () { advance(); }, d + 1250 + (hold ? holdMs : 0));
      }
    }
    function advance() { if (cur < seq.length - 1) runStep(cur + 1, HX.bySlug[seq[cur + 1].slug].overlayOf ? "fade" : "slide"); }
    function jump(i) { if (i < 0 || i >= seq.length) return; runStep(i, null); }   // 재생 중이면 그 단계부터 이어서, 멈춤이면 그 화면만
    function toggle() { playing = !playing; if (playing && ended) { start(fi); return; } paintCtl(); if (playing) runStep(cur, null); else clear(); }
    function start(i) { fi = i; seq = seqOf(flows[i]); playing = true; paintList(); runStep(0, null); }

    var shown = false;
    return {
      el: el,
      onShow: function () { if (!flows.length) { say("", "흐름이 없어요"); return; } if (!shown) { shown = true; start(0); } else if (playing) runStep(cur, null); HX.relayout(); },
      onHide: function () { clear(); },
      onKey: function (e) {
        if (e.key === " ") { e.preventDefault(); toggle(); }
        else if (e.key === "ArrowRight") { e.preventDefault(); jump(cur + 1); }
        else if (e.key === "ArrowLeft") { e.preventDefault(); jump(cur - 1); }
      }
    };
  };
})();
