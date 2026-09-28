/* 00-core.js — 전역 window.HX: 데이터·프레임·배지·모달·유틸.
   바닐라 JS, 의존성 0, file:// 오프라인. 아이콘은 반드시 리터럴 "#i-…" 문자열로 호출한다(빌드가 정규식 추출). */
(function () {
  "use strict";
  var doc = document, root = doc.documentElement;
  var HX = window.HX = {};

  // ---------- 데이터 ----------
  function parseData() {
    var el = doc.getElementById("hx-data");
    try { return el ? JSON.parse(el.textContent) : null; } catch (e) { console.error("[hx] hx-data 파싱 실패", e); return null; }
  }
  var data = parseData() || {};
  data.meta = data.meta || {}; data.screens = data.screens || []; data.flows = data.flows || [];
  data.meta.roles = data.meta.roles || [];
  HX.data = data; HX.meta = data.meta;
  HX.mode = root.getAttribute("data-mode") || data.meta.mode || "final";
  HX.platform = root.getAttribute("data-platform") || data.meta.platform || "web";
  HX.frame = HX.platform === "mobile" ? { w: 390, h: 844 } : { w: 1280, h: 800 };
  HX.bySlug = {};
  data.screens.forEach(function (s) { s.regions = s.regions || []; HX.bySlug[s.slug] = s; });
  HX.roleLabel = function (key) {
    if (!key) return "공통";
    var hit = data.meta.roles.filter(function (r) { return r.key === key; })[0];
    return hit ? hit.label : key;
  };

  // ---------- 유틸 ----------
  HX.esc = function (s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  };
  HX.append = function (parent, ch) {
    if (ch == null) return parent;
    if (!Array.isArray(ch)) ch = [ch];
    ch.forEach(function (c) {
      if (c == null || c === false) return;
      parent.appendChild(typeof c === "string" || typeof c === "number" ? doc.createTextNode(String(c)) : c);
    });
    return parent;
  };
  HX.el = function (tag, attrs, children) {
    var e = doc.createElement(tag); attrs = attrs || {};
    Object.keys(attrs).forEach(function (k) {
      var v = attrs[k];
      if (v == null || v === false) return;
      if (k === "class") e.className = v;
      else if (k === "text") e.textContent = v;
      else if (k === "style") e.style.cssText = v;
      else if (k === "dataset") Object.keys(v).forEach(function (d) { e.dataset[d] = v[d]; });
      else if (k.slice(0, 2) === "on" && typeof v === "function") e.addEventListener(k.slice(2), v);
      else e.setAttribute(k, v === true ? "" : v);
    });
    return HX.append(e, children);
  };
  HX.icon = function (href, cls) {
    var ns = "http://www.w3.org/2000/svg";
    var svg = doc.createElementNS(ns, "svg"); svg.setAttribute("class", cls || "icon"); svg.setAttribute("aria-hidden", "true");
    var use = doc.createElementNS(ns, "use"); use.setAttribute("href", href); svg.appendChild(use);
    return svg;
  };
  HX.badge = function (id, cls) { return HX.el("span", { class: "hx-badge" + (cls ? " " + cls : ""), text: String(id) }); };
  HX.btn = function (label, opts) {
    opts = opts || {};
    var b = HX.el("button", { type: "button", class: "hx-btn" + (opts.cls ? " " + opts.cls : ""), title: opts.title, "aria-label": opts.aria, onclick: opts.onclick });
    if (opts.icon) b.appendChild(opts.icon);
    if (label) b.appendChild(doc.createTextNode(label));
    return b;
  };
  HX.clamp = function (v, lo, hi) { return Math.min(hi, Math.max(lo, v)); };
  HX.storage = {
    get: function (k) { try { var v = localStorage.getItem(k); return v ? JSON.parse(v) : null; } catch (e) { return null; } },
    set: function (k, v) { try { localStorage.setItem(k, JSON.stringify(v)); return true; } catch (e) { return false; } }
  };
  var toastT = 0;
  HX.toast = function (msg) {
    var old = doc.querySelector(".hx-toast"); if (old) old.remove();
    var t = HX.el("div", { class: "hx-toast", role: "status", text: msg });
    doc.body.appendChild(t); clearTimeout(toastT);
    toastT = setTimeout(function () { t.remove(); }, 2200);
  };
  HX.copyText = function (text) {
    return new Promise(function (resolve) {
      if (navigator.clipboard && window.isSecureContext !== false) {
        navigator.clipboard.writeText(text).then(function () { resolve(true); }, function () { resolve(fallback()); });
      } else resolve(fallback());
    });
    function fallback() {
      try {
        var ta = HX.el("textarea", { class: "hx-sr", text: text }); doc.body.appendChild(ta); ta.select();
        var ok = doc.execCommand && doc.execCommand("copy"); ta.remove(); return !!ok;
      } catch (e) { return false; }
    }
  };

  // ---------- 이벤트 버스 ----------
  var handlers = {};
  HX.on = function (name, fn) { (handlers[name] = handlers[name] || []).push(fn); };
  HX.off = function (name, fn) { handlers[name] = (handlers[name] || []).filter(function (f) { return f !== fn; }); };
  HX.emit = function (name, arg) { (handlers[name] || []).slice().forEach(function (f) { try { f(arg); } catch (e) { console.error(e); } }); };

  // ---------- 그래프 ----------
  HX.outgoing = function (slug) {
    var out = [];
    data.flows.forEach(function (f) { (f.steps || []).forEach(function (st, i) { if (st.from === slug) out.push({ flow: f, step: st, index: i }); }); });
    return out;
  };
  HX.edges = function () {
    var map = {}, list = [];
    data.flows.forEach(function (f) {
      (f.steps || []).forEach(function (st, i) {
        var k = st.from + "\u0000" + st.to;
        if (!map[k]) { map[k] = { from: st.from, to: st.to, steps: [] }; list.push(map[k]); }
        map[k].steps.push({ flow: f, step: st, index: i });
      });
    });
    return list;
  };
  HX.bfsOrder = function () {
    var adj = {}, order = [], seen = {};
    data.screens.forEach(function (s) { adj[s.slug] = []; });
    data.flows.forEach(function (f) { (f.steps || []).forEach(function (st) { if (adj[st.from] && adj[st.to] !== undefined) adj[st.from].push(st.to); }); });
    function bfs(start) {
      if (seen[start] || !adj[start]) return;
      var q = [start]; seen[start] = true;
      while (q.length) { var cur = q.shift(); order.push(cur); adj[cur].forEach(function (n) { if (!seen[n]) { seen[n] = true; q.push(n); } }); }
    }
    var first = data.flows[0] && data.flows[0].steps && data.flows[0].steps[0];
    if (first) bfs(first.from);
    data.flows.forEach(function (f) { (f.steps || []).forEach(function (st) { bfs(st.from); bfs(st.to); }); });
    data.screens.forEach(function (s) { bfs(s.slug); });
    return order;
  };

  // ---------- 배지 토글 ----------
  HX.badgesOn = true;
  HX.setBadges = function (on) {
    HX.badgesOn = !!on; root.classList.toggle("hx-hide-badges", !HX.badgesOn); HX.emit("badges", HX.badgesOn);
  };
  HX.badgeToggle = function () {
    var b = HX.btn("번호", { cls: "hx-on", title: "화면 위 빨간 번호 보이기/숨기기", onclick: function () { HX.setBadges(!HX.badgesOn); } });
    function sync(on) {
      b.classList.toggle("hx-on", on); b.setAttribute("aria-pressed", on ? "true" : "false");
      var old = b.querySelector("svg"); if (old) old.remove();
      b.insertBefore(HX.icon(on ? "#i-eye" : "#i-eye-off"), b.firstChild);
    }
    HX.on("badges", sync); sync(HX.badgesOn); return b;
  };
})();

/* ---- 프레임 · relayout · 모달 ---- */
(function () {
  "use strict";
  var doc = document, HX = window.HX;
  var frames = [];

  function applySize(f) {
    var W = HX.frame.w, H = f.h || HX.frame.h, s = f.scale;
    f.stage.style.width = W + "px"; f.stage.style.height = H + "px"; f.stage.style.transform = "scale(" + s + ")";
    f.el.style.width = (W * s) + "px"; f.el.style.height = (H * s) + "px";
  }
  function fitScale(f) {
    var p = f.fitTo || f.el.parentNode; if (!p) return;
    // 부모 폭이 프레임 자신(1280px) 때문에 늘어나 있으면 배율이 1로 잘못 잡힌다 → 측정 동안만 0으로
    var prevW = f.el.style.width, prevH = f.el.style.height;
    if (!f.fitTo) { f.el.style.width = "0px"; f.el.style.height = "0px"; }
    var pw = p.clientWidth - (f.pad || 0) * 2, ph = p.clientHeight - (f.pad || 0) * 2;
    if (!f.fitTo) { f.el.style.width = prevW; f.el.style.height = prevH; }
    if (pw <= 0) return;
    var s = f.fit === "width" ? pw / HX.frame.w : Math.min(pw / HX.frame.w, (ph > 0 ? ph : 1e9) / (f.h || HX.frame.h));
    s = HX.clamp(s, 0.04, f.maxScale);
    if (Math.abs(s - f.scale) > 0.0005) { f.scale = s; applySize(f); }
  }
  /* fullHeight: 내부 스크롤(.content 등)로 가려진 만큼 프레임을 늘려 모든 영역이 보이게 한다 (보드·확대 모달용) */
  function growToContent(f) {
    var over = 0;
    f.section.querySelectorAll(".content, .split-list, .split-detail, .drawer-body, .modal-body").forEach(function (c) {
      var d = c.scrollHeight - c.clientHeight; if (d > over) over = d;
    });
    if (over <= 2) return;
    var nh = Math.min((f.h || HX.frame.h) + over, HX.frame.h * 3);
    if (nh === f.h) return;
    f.h = nh; f.section.style.setProperty("--frame-h", nh + "px"); applySize(f);
  }
  function layoutFrame(f) {
    if (!f.el.isConnected) return;
    if (f.opts.fullHeight) growToContent(f);
    if (f.fit) fitScale(f);
    var sr = f.stage.getBoundingClientRect();
    var eff = sr.width / HX.frame.w;       // 화면px → 원본px 비율 (외부 zoom 포함)
    if (!eff) return;
    var s = f.scale;
    Object.keys(f.boxes).forEach(function (k) {
      var b = f.boxes[k];
      var t = f.section.querySelector('[data-region="' + k + '"]');
      if (!t) { b.el.style.display = "none"; b.rect = null; return; }
      var r = t.getBoundingClientRect();
      b.rect = { x: (r.left - sr.left) / eff * s, y: (r.top - sr.top) / eff * s, w: r.width / eff * s, h: r.height / eff * s };
      b.el.style.display = "";
      b.el.style.left = b.rect.x + "px"; b.el.style.top = b.rect.y + "px";
      b.el.style.width = Math.max(4, b.rect.w) + "px"; b.el.style.height = Math.max(4, b.rect.h) + "px";
    });
    // 트리거 박스: 실제로 누르는 요소 [data-trigger] (영역 bbox와 별개 레이어, 위)
    var TP = 3;
    Object.keys(f.tboxes).forEach(function (k) {
      var tb = f.tboxes[k], t = findTrigger(f, k);
      var r = t ? t.getBoundingClientRect() : null;
      if (!r || (!r.width && !r.height)) { tb.el.style.display = "none"; tb.rect = null; tb.region = null; return; }
      tb.rect = { x: (r.left - sr.left) / eff * s - TP, y: (r.top - sr.top) / eff * s - TP, w: r.width / eff * s + TP * 2, h: r.height / eff * s + TP * 2 };
      var reg = t.closest ? t.closest("[data-region]") : null;
      tb.region = reg ? reg.getAttribute("data-region") : null;
      tb.el.style.display = "";
      tb.el.style.left = tb.rect.x + "px"; tb.el.style.top = tb.rect.y + "px";
      tb.el.style.width = Math.max(6, tb.rect.w) + "px"; tb.el.style.height = Math.max(6, tb.rect.h) + "px";
      tb.el.classList.toggle("hx-badge-left", tb.rect.x + tb.rect.w + 34 > HX.frame.w * s);
    });
    applySpot(f);
    if (f.opts.onLayout) f.opts.onLayout(f);
  }
  function findTrigger(f, key) {
    var q = window.CSS && CSS.escape ? CSS.escape(key) : String(key).replace(/["\\]/g, "\\$&");
    return f.section.querySelector('[data-trigger="' + q + '"]');
  }
  /* 스포트라이트: 트리거 박스가 있으면 그것만 밝히고 그 요소가 속한 영역 배지를 옆에, 없으면 영역 bbox */
  function applySpot(f) {
    var tb = f.spotTrig && f.tboxes[f.spotTrig] && f.tboxes[f.spotTrig].rect ? f.tboxes[f.spotTrig] : null;
    var key = f.spot;
    f.el.classList.toggle("hx-spot", !!(key || tb));
    Object.keys(f.boxes).forEach(function (k) { f.boxes[k].el.classList.toggle("hx-spot-on", !tb && k === key); });
    Object.keys(f.tboxes).forEach(function (k) {
      var on = !!tb && f.tboxes[k] === tb, el = f.tboxes[k].el;
      el.classList.toggle("hx-spot-on", on);
      var old = el.querySelector(".hx-badge"); if (old) old.remove();
      if (on) {
        var rk = tb.region || key, reg = rk && f.boxes[rk] ? f.boxes[rk].region : null;
        if (reg) el.appendChild(HX.badge(reg.id));
      }
    });
  }

  /* HX.mountFrame(slug, container, {scale, fit:'width'|'contain', maxScale, pad, fitTo, badges, onRegionHover, onRegionClick, onLayout}) */
  HX.mountFrame = function (slug, container, opts) {
    opts = opts || {};
    var screen = HX.bySlug[slug];
    var tpl = doc.getElementById("hx-screens");
    var src = tpl && tpl.content ? tpl.content.querySelector('section[data-screen="' + slug + '"]') : null;
    var section = src ? doc.importNode(src, true) : HX.el("section", { class: "hx-screen hx-screen-missing", text: "조각 없음: " + slug });
    var stage = HX.el("div", { class: "hx-stage" }, section);
    var overlay = HX.el("div", { class: "hx-overlay" });
    var tlayer = HX.el("div", { class: "hx-toverlay" });
    var el = HX.el("div", { class: "hx-frame" + (opts.badges === false ? " hx-frame-nobadge" : ""), dataset: { screen: slug } }, [stage, overlay, tlayer]);
    var f = { el: el, stage: stage, overlay: overlay, tlayer: tlayer, section: section, screen: screen, slug: slug, opts: opts,
      h: HX.frame.h, scale: opts.scale || 1, fit: opts.fit || null, maxScale: opts.maxScale || 1, pad: opts.pad || 0, fitTo: opts.fitTo || null,
      boxes: {}, tboxes: {}, spot: null, spotTrig: null };
    (opts.triggers || []).forEach(function (k) {
      if (!k || f.tboxes[k]) return;
      var tb = HX.el("div", { class: "hx-tbox", dataset: { trigger: k }, style: "display:none" });
      tlayer.appendChild(tb); f.tboxes[k] = { el: tb, rect: null, region: null };
    });
    ((screen && screen.regions) || []).forEach(function (r) {
      var b = HX.el("div", { class: "hx-bbox", dataset: { key: r.key, id: r.id }, title: r.id + " " + r.label }, HX.badge(r.id));
      b.addEventListener("mouseenter", function () { b.classList.add("hx-hover"); if (opts.onRegionHover) opts.onRegionHover(r, true); });
      b.addEventListener("mouseleave", function () { b.classList.remove("hx-hover"); if (opts.onRegionHover) opts.onRegionHover(r, false); });
      if (opts.onRegionClick) b.addEventListener("click", function (e) { e.stopPropagation(); opts.onRegionClick(r); });
      overlay.appendChild(b); f.boxes[r.key] = { el: b, region: r, rect: null };
    });
    f.setScale = function (s) { f.fit = null; f.scale = s; applySize(f); HX.relayout(); };
    f.layout = function () { layoutFrame(f); };
    f.highlight = function (key, on) { var b = f.boxes[key]; if (b) b.el.classList.toggle("hx-on", !!on); };
    f.spotlight = function (key, trigger) { f.spot = key || null; f.spotTrig = trigger || null; applySpot(f); };
    f.regionRect = function (key) { return f.boxes[key] ? f.boxes[key].rect : null; };
    f.triggerRect = function (key) { return f.tboxes[key] ? f.tboxes[key].rect : null; };
    f.highlightTrigger = function (key, on) { var t = f.tboxes[key]; if (t) t.el.classList.toggle("hx-active", !!on); };
    /* fullHeight 프레임을 기본 높이로 되돌린다 (글자 크기 등이 바뀐 뒤 다시 늘리기 위해) */
    f.resetHeight = function () { f.h = HX.frame.h; section.style.removeProperty("--frame-h"); applySize(f); };
    f.destroy = function () { var i = frames.indexOf(f); if (i >= 0) frames.splice(i, 1); if (el.parentNode) el.parentNode.removeChild(el); };
    applySize(f); frames.push(f);
    if (container) container.appendChild(el);
    HX.relayout();
    return f;
  };

  var raf = 0;
  HX.relayout = function () {
    if (raf) return;
    raf = requestAnimationFrame(function () {
      raf = 0;
      frames = frames.filter(function (f) { return f.el.isConnected; });
      frames.forEach(layoutFrame);
      HX.emit("layout");
    });
  };
  window.addEventListener("resize", HX.relayout);
  window.addEventListener("load", HX.relayout);
  if (doc.fonts && doc.fonts.ready) doc.fonts.ready.then(function () { HX.relayout(); setTimeout(HX.relayout, 300); });

  // ---------- 모달: 화면 100% + 영역 목록 + 나가는 step ----------
  var modal = null, modalKey = null;
  HX.closeModal = function () {
    if (!modal) return;
    modal.remove(); modal = null; doc.body.style.overflow = "";
    if (modalKey) { doc.removeEventListener("keydown", modalKey); modalKey = null; }
    HX.emit("modal", null);
  };
  HX.openScreen = function (slug) {
    var s = HX.bySlug[slug]; if (!s) return;
    HX.closeModal();
    var frameBox = HX.el("div", { class: "hx-modal-frame" });
    var lis = {};
    var regionUl = HX.el("ul", {}, s.regions.map(function (r) {
      var li = HX.el("li", { class: "hx-region-li" }, [HX.badge(r.id), HX.el("div", {}, [HX.el("b", { text: r.label }), r.why ? HX.el("div", { class: "hx-why", text: r.why }) : null])]);
      li.addEventListener("mouseenter", function () { fr.highlight(r.key, true); });
      li.addEventListener("mouseleave", function () { fr.highlight(r.key, false); });
      lis[r.key] = li; return li;
    }));
    var outs = HX.outgoing(slug);
    var stepUl = HX.el("ul", {}, outs.length ? outs.map(function (o) {
      var reg = s.regions.filter(function (r) { return r.key === o.step.region; })[0];
      var to = HX.bySlug[o.step.to];
      return HX.el("li", {}, HX.el("button", { type: "button", class: "hx-step-btn", onclick: function () { HX.openScreen(o.step.to); } }, [
        reg ? HX.badge(reg.id) : null,
        HX.el("div", {}, [HX.el("div", {}, [o.step.action + " ", HX.el("span", { class: "hx-to", text: "→ " + (to ? to.name : o.step.to) })]),
          HX.el("div", { class: "hx-why", text: o.flow.name })])
      ]));
    }) : HX.el("li", { class: "hx-muted", text: "이 화면에서 나가는 단계가 없어요." }));
    var closeBtn = HX.btn("", { cls: "hx-icon-btn", aria: "닫기", title: "닫기 (Esc)", icon: HX.icon("#i-x"), onclick: HX.closeModal });
    var panel = HX.el("div", { class: "hx-modal-panel", role: "dialog", "aria-modal": "true", "aria-label": s.name }, [
      HX.el("div", { class: "hx-modal-head" }, [HX.badge(s.id), HX.el("h2", { text: s.name }), HX.el("span", { class: "hx-tag hx-role", text: HX.roleLabel(s.role) }),
        HX.el("span", { class: "hx-purpose", text: s.purpose }), HX.el("span", { class: "hx-bar-spacer" }), closeBtn]),
      HX.el("div", { class: "hx-modal-body" }, [frameBox, HX.el("aside", { class: "hx-modal-side" }, [
        HX.el("section", {}, [HX.el("div", { class: "hx-side-h", text: "이 화면의 번호 " + s.regions.length + "개" }), regionUl]),
        HX.el("section", {}, [HX.el("div", { class: "hx-side-h", text: "여기서 가는 곳" }), stepUl])])])
    ]);
    modal = HX.el("div", { class: "hx-modal hx-app" }, [HX.el("div", { class: "hx-modal-backdrop", onclick: HX.closeModal }), panel]);
    doc.body.appendChild(modal); doc.body.style.overflow = "hidden";
    var fr = HX.mountFrame(slug, frameBox, { scale: 1, fullHeight: true, onRegionHover: function (r, on) { if (lis[r.key]) lis[r.key].classList.toggle("hx-on", on); } });
    modalKey = function (e) { if (e.key === "Escape") { e.preventDefault(); HX.closeModal(); } };
    doc.addEventListener("keydown", modalKey);
    closeBtn.focus();
    HX.emit("modal", slug);
  };
})();
