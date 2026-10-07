/* 24-board-screens.js — 보드의 두 탭.
   [사용 흐름]  흐름을 이해하는 곳 (05~07 캔버스). 빨간 번호·의견 창은 숨긴다. 화면을 누르면 화면 디자인 탭의 그 화면으로.
   [화면 디자인] 화면마다 한 번씩, 크게 보고 의견을 남기는 곳: 왼쪽 화면 목록 · 가운데 화면 한 장 · 오른쪽 그 화면의 번호 전부.
   목록 맨 위 "전체"는 질문·더 있었으면 하는 것·지금까지 남긴 의견(21-board-panel의 home)을 그대로 보여준다.
   상태 저장·복사 형식은 20-board.js 그대로 — 이 파일은 보여주는 방식만 바꾼다. */
(function () {
  "use strict";
  var HX = window.HX, B = HX.board, doc = document;
  if (!B) return;
  var CHOICES = [["like", "좋아요", "#i-thumbs-up"], ["change", "바꿔주세요", "#i-pencil"], ["remove", "빼주세요", "#i-x"]];
  var EXAMPLES = ["글자 더 크게", "더 단순하게", "위로 올려주세요", "잘 안 보여요", "색을 바꿔주세요", "다른 모양으로", "버튼을 더 크게", "순서를 바꿔주세요"];
  var ALL = "__all";
  function parts(m) { return String(m || "").split(/\s*,\s*/).filter(Boolean); }

  // 흐름에 나오는 순서대로 화면을 늘어놓는다 (처음 시작 흐름이 앞)
  // 화면 번호 순서(= 사용자가 만나는 순서, ids.js). 번호가 없으면 screens.json 순서
  function screenOrder() {
    return HX.data.screens.map(function (s, i) { return { slug: s.slug, k: typeof s.id === "number" ? s.id : 1e6 + i }; })
      .sort(function (a, b) { return a.k - b.k; }).map(function (x) { return x.slug; });
  }
  function hasMark(s) {
    var st = B.state, ss = st.screens[s.id];
    if (ss && (ss.remove || (ss.memo || "").trim())) return true;
    if (Object.keys(st.pins || {}).some(function (k) { var p = st.pins[k]; return p && p.slug === s.slug && (p.v === "change" || p.v === "remove"); })) return true;
    return s.regions.some(function (r) { var x = st.regions[r.id]; return x && x.v && x.v !== "like"; });
  }
  function roleName(role) { var l = HX.roleLabel(role).replace(/\(.*\)/, ""); return l === "부모" ? "부모님" : l; }

  B.buildDesign = function (ctx) {
    var app = ctx.app, bar = ctx.bar;
    // ---------- 탭 ----------
    var tabBtns = {};
    function tab(key, label, icon) {
      var b = HX.el("button", { type: "button", class: "hx-bd-tab", role: "tab", onclick: function () { B.setTab(key); } }, [HX.icon(icon), label]);
      tabBtns[key] = b; return b;
    }
    // 시안이 있고 아직 고르지 않았으면 맨 앞에 '시안 비교' (25-board-concepts.js)
    var hasConcepts = !!(B.buildConcepts && B.concepts && B.concepts.length > 1 && !B.isLocked("concept"));
    var tabs = HX.el("div", { class: "hx-bd-tabs", role: "tablist", "aria-label": "보기" }, [
      hasConcepts ? tab("concept", "시안 비교", "#i-columns-3") : null, tab("flow", "사용 흐름", "#i-workflow"), tab("design", "화면 디자인", "#i-layout-grid")]);
    bar.insertBefore(tabs, bar.children[1] || null);

    // ---------- 화면 디자인 뷰 ----------
    var list = HX.el("nav", { class: "hx-sd-list", "aria-label": "화면 목록" });
    var stage = HX.el("div", { class: "hx-sd-stage" });
    var side = HX.el("aside", { class: "hx-sd-side", "aria-label": "의견 남기기" });
    var sideAll = HX.el("div", { class: "hx-sd-all" }, [B.panel.el]);   // "전체": 기존 패널의 home을 그대로
    var sideScreen = HX.el("div", { class: "hx-sd-screen" });
    side.appendChild(sideAll); side.appendChild(sideScreen);
    var view = HX.el("div", { class: "hx-sd" }, [list, stage, side]);
    app.appendChild(view);
    if (hasConcepts) app.appendChild(B.buildConcepts());

    var order = screenOrder(), cur = null, frame = null, itemEls = {};

    // 왼쪽 목록
    function buildList() {
      list.innerHTML = "";
      var nAsk = (B.asks || []).length;
      var allBtn = HX.el("button", { type: "button", class: "hx-sd-item hx-sd-item-all", onclick: function () { show(ALL); } }, [
        HX.icon("#i-list"), HX.el("span", { class: "hx-sd-name", text: "전체" }),
        HX.el("span", { class: "hx-sd-meta", text: (nAsk ? "질문 " + nAsk + "개 · " : "") + "남긴 의견" })]);
      itemEls[ALL] = allBtn; list.appendChild(allBtn);
      var groups = [];
      HX.meta.roles.forEach(function (r) { groups.push({ key: r.key, label: roleName(r.key) }); });
      groups.push({ key: null, label: "함께 쓰는 화면" });
      var roleKeys = HX.meta.roles.map(function (r) { return r.key; });
      groups.forEach(function (g) {
        var mine = order.filter(function (slug) { var s = HX.bySlug[slug]; return g.key === null ? (!s.role || roleKeys.indexOf(s.role) < 0) : s.role === g.key; });
        if (!mine.length) return;
        list.appendChild(HX.el("div", { class: "hx-sd-group", text: g.label + " · " + mine.length }));
        mine.forEach(function (slug) {
          var s = HX.bySlug[slug];
          var b = HX.el("button", { type: "button", class: "hx-sd-item", dataset: { screen: slug }, onclick: function () { show(slug); } }, [
            HX.badge(s.id), HX.el("span", { class: "hx-sd-name", text: s.name }),
            s.state ? HX.el("span", { class: "hx-tag hx-state", text: HX.stateLabel(s.state) }) : null,
            (B.focus || []).indexOf(slug) >= 0 ? HX.el("span", { class: "hx-tag hx-bd-tag-fixed", text: "고친 화면" }) : null,
            HX.el("span", { class: "hx-sd-dot", title: "의견을 남긴 화면" })]);
          itemEls[slug] = b; list.appendChild(b);
        });
      });
      paintList();
    }
    function paintList() {
      Object.keys(itemEls).forEach(function (k) {
        var el = itemEls[k]; el.classList.toggle("hx-on", k === cur); el.setAttribute("aria-current", k === cur ? "true" : "false");
        if (k !== ALL) el.classList.toggle("hx-marked", hasMark(HX.bySlug[k]));
      });
    }

    // 가운데 화면 + 오른쪽 번호 목록
    function paintFrame() {
      if (!frame || !cur || cur === ALL) return;
      var ss = B.state.screens[HX.bySlug[cur].id];
      stage.classList.toggle("hx-sd-removed", !!(ss && ss.remove));
    }
    // ---------- 화면 아무 곳이나 고르기 (번호를 미리 정하지 않는다) ----------
    var hov = HX.el("div", { class: "hx-pick-hov" }), hovLab = HX.el("div", { class: "hx-pick-lab" });
    var selBox = HX.el("div", { class: "hx-pick-sel" }), pinLayer = HX.el("div", { class: "hx-pick-pins" });
    var box = null, picked = null;   // picked = { el, path, desc, where, pinId }
    var editor = HX.el("div", { class: "hx-sd-editor" }), pinList = HX.el("div", { class: "hx-sd-pins" });

    function kindOf(el) {
      var t = el.tagName.toLowerCase(), c = el.classList;
      if (t === "svg") return "아이콘";
      if (c.contains("app")) return "화면 전체";
      if (t === "button" || c.contains("btn")) return "버튼";
      if (t === "input" || t === "textarea" || t === "select" || c.contains("input") || c.contains("select") || c.contains("textarea") || c.contains("search")) return "입력칸";
      if (t === "label" || c.contains("checkbox") || c.contains("radio") || c.contains("switch")) return "선택 항목";
      if (c.contains("nav-item")) return "메뉴";
      if (t === "a") return "링크";
      if (t === "img") return "이미지";
      if (/^h[1-6]$/.test(t) || c.contains("page-title") || c.contains("card-title") || c.contains("section-title")) return "제목";
      if (c.contains("badge") || c.contains("chip")) return "표시";
      if (c.contains("avatar") || c.contains("avatar-group")) return "사람 표시";
      if (c.contains("sidebar") || t === "nav") return "메뉴 묶음";
      if (c.contains("topnav")) return "맨 위 줄";
      if (t === "li" || t === "tr" || c.contains("list-item") || c.contains("timeline-item")) return "목록 한 줄";
      if (!el.querySelector("div,section,ul,ol,table,form,header,footer,aside,nav,li") && (el.textContent || "").trim()) return "글자";
      return "부분";
    }
    // 화면에 보이는 글자로(줄·칸 사이를 띄어서) — textContent는 "지현김지현2/3"처럼 글자가 붙어 버린다
    function seen(el) { return (el.innerText || el.textContent || "").split(/\n+/).map(function (x) { return x.replace(/\s+/g, " ").trim(); }).filter(Boolean); }
    function textOf(el) {
      if (el.tagName.toLowerCase() === "svg") return "";
      var attr = el.getAttribute("aria-label") || el.getAttribute("placeholder") || (el.tagName === "INPUT" ? el.getAttribute("value") : "");
      var tx = attr;
      if (!tx) {
        // 묶음(부분·목록 한 줄·메뉴 묶음)은 제목이 있으면 제목, 없으면 첫 줄만
        var head = kindOf(el) !== "글자" && el.querySelector && el.querySelector("h1,h2,h3,h4,.card-title,.page-title,.section-title,.fw-semibold");
        var lines = head ? seen(head) : seen(el);
        tx = lines.length > 1 && !head ? lines[0] + " · " + lines[1] : (lines[0] || "");
      }
      tx = String(tx).replace(/\s+/g, " ").trim();
      return tx.length > 24 ? tx.slice(0, 24) + "…" : tx;
    }
    function descOf(el) { var k = kindOf(el), t = k === "아이콘" ? iconNameOf(el) : textOf(el); return k + (t && k !== "화면 전체" ? " '" + t + "'" : ""); }
    function whereOf(el) {
      var host = el.closest("[data-region]"); if (!host) return "";
      var r = HX.bySlug[cur].regions.filter(function (x) { return x.key === host.getAttribute("data-region"); })[0];
      return r ? r.label : "";
    }
    // 위치 경로: 가장 가까운 data-region(@key)부터 태그:순번. 다음 초안에서 AI가 조각 파일에서 이 요소를 찾는 좌표
    function pathOf(el) {
      var segs = [], n = el, sec = frame.section;
      while (n && n !== sec) {
        if (n.hasAttribute && n.hasAttribute("data-region")) { segs.unshift("@" + n.getAttribute("data-region")); return segs.join(" > "); }
        var par = n.parentElement; if (!par) break;
        var same = [].filter.call(par.children, function (c) { return c.tagName === n.tagName; });
        segs.unshift(n.tagName.toLowerCase() + (same.length > 1 ? ":" + (same.indexOf(n) + 1) : ""));
        n = par;
      }
      return segs.join(" > ");
    }
    function resolve(path) {
      if (!frame || !path) return null;
      var segs = path.split(" > "), n = frame.section;
      for (var i = 0; i < segs.length && n; i++) {
        var sg = segs[i];
        if (sg.charAt(0) === "@") { n = n.querySelector('[data-region="' + sg.slice(1) + '"]'); continue; }
        var m = /^([a-z0-9-]+)(?::(\d+))?$/.exec(sg); if (!m) return null;
        var kids = [].filter.call(n.children, function (c) { return c.tagName.toLowerCase() === m[1]; });
        n = kids[(m[2] ? Number(m[2]) : 1) - 1] || null;
      }
      return n;
    }
    function targetOf(el) {
      if (!frame || !el || !frame.section.contains(el) || el === frame.section) return null;
      var svg = el.closest && el.closest("svg"); if (svg && frame.section.contains(svg)) el = svg;
      return el.nodeType === 1 ? el : el.parentElement;
    }
    function rectIn(el) { var r = el.getBoundingClientRect(), b = box.getBoundingClientRect(); return { x: r.left - b.left, y: r.top - b.top, w: r.width, h: r.height }; }
    function place(div, el, pad) {
      if (!el) { div.style.display = "none"; return; }
      var q = rectIn(el), p = pad || 0;
      div.style.display = ""; div.style.left = (q.x - p) + "px"; div.style.top = (q.y - p) + "px"; div.style.width = (q.w + p * 2) + "px"; div.style.height = (q.h + p * 2) + "px";
    }
    function paintPins() {
      pinLayer.innerHTML = "";
      if (!frame || !cur || cur === ALL) return;
      pinsOf(cur).forEach(function (p) {
        var el = resolve(p.path); if (!el) return;
        var q = rectIn(el);
        var dot = HX.el("button", { type: "button", class: "hx-pin hx-pin-" + p.v + (picked && picked.pinId === p.id ? " hx-on" : ""), text: String(p.id), title: "의견 " + p.id + " · " + p.desc,
          style: "left:" + Math.max(0, q.x + q.w - 12) + "px;top:" + Math.max(0, q.y - 12) + "px", onclick: function (e) { e.stopPropagation(); pick(el, p.id); } });
        pinLayer.appendChild(dot);
      });
      place(selBox, picked && picked.el, 2);
    }
    function pinsOf(slug) {
      var st = B.state;
      return Object.keys(st.pins || {}).map(function (k) { return st.pins[k]; }).filter(function (p) { return p && p.slug === slug; }).sort(function (a, b) { return a.id - b.id; });
    }
    function pick(el, pinId) {
      if (!el) { picked = null; renderEditor(); paintPins(); return; }
      var path = pathOf(el);
      if (!pinId) { var ex = pinsOf(cur).filter(function (p) { return p.path === path; })[0]; if (ex) pinId = ex.id; }
      picked = { el: el, path: path, desc: descOf(el), where: whereOf(el), pinId: pinId || null };
      renderEditor(); paintPins();
      editor.scrollIntoView({ block: "nearest", behavior: "smooth" });
    }
    function renderEditor() {
      editor.innerHTML = "";
      if (!picked) {
        editor.appendChild(HX.el("div", { class: "hx-sd-empty" }, [HX.icon("#i-mouse-pointer-click"),
          HX.el("span", { text: "화면에서 고치고 싶은 곳을 눌러 주세요. 버튼·글자·아이콘·묶음 어디든 골라져요." })]));
        return;
      }
      var st = B.state, p = picked.pinId ? st.pins[picked.pinId] : null;
      var parent = picked.el.parentElement && picked.el.parentElement !== frame.section ? picked.el.parentElement : null;
      editor.appendChild(HX.el("div", { class: "hx-sd-picked" }, [
        HX.el("div", { class: "hx-sd-k", text: p ? "의견 " + p.id : "고른 곳" }),
        HX.el("div", { class: "hx-sd-picked-name", text: picked.desc }),
        picked.where ? HX.el("div", { class: "hx-sd-picked-where", text: "'" + picked.where + "' 안에 있어요" }) : null,
        HX.el("div", { class: "hx-sd-picked-acts" }, [
          HX.btn("더 넓게 고르기", { icon: HX.icon("#i-maximize-2"), title: "이것을 감싸는 묶음으로 넓혀요", onclick: function () { if (parent) pick(parent); } }),
          HX.btn("선택 취소", { onclick: function () { pick(null); } })])]));
      editor.querySelector(".hx-sd-picked-acts .hx-btn").disabled = !parent || !!p;
      var memo = HX.el("textarea", { class: "hx-ta hx-sd-memo", rows: "2", placeholder: "직접 적어도 돼요 (예: 날짜가 더 잘 보이게)", "aria-label": "의견 메모",
        oninput: function () { var v = memo.value.replace(/\s*\n+\s*/g, " "); if (v !== memo.value) memo.value = v; ensure("change").memo = v; paintChips(); B.changed(); } });
      memo.value = p ? p.memo || "" : "";
      function ensure(v) {
        if (!picked.pinId) {
          st.pinSeq = (st.pinSeq || 0) + 1;
          var np = { id: st.pinSeq, sid: HX.bySlug[cur].id, slug: cur, path: picked.path, desc: picked.desc, where: picked.where, v: v, memo: "" };
          st.pins[np.id] = np; picked.pinId = np.id;
        }
        var q = st.pins[picked.pinId]; if (q.v !== v && v) q.v = v; return q;
      }
      var choice = HX.el("div", { class: "hx-sd-choices", role: "group", "aria-label": "고른 곳에 대한 의견" });
      var CH = [["change", "바꿔주세요", "#i-pencil"], ["remove", "빼주세요", "#i-x"]];
      var cbtns = CH.map(function (c) {
        var b = HX.el("button", { type: "button", class: "hx-sd-choice hx-v-" + c[0], onclick: function () { ensure(c[0]); renderEditor(); paintPins(); renderPinList(); B.changed(); } }, [HX.icon(c[2]), HX.el("span", { text: c[1] })]);
        b.setAttribute("aria-pressed", p && p.v === c[0] ? "true" : "false"); choice.appendChild(b); return b;
      });
      editor.appendChild(choice);
      if (kindOf(picked.el) === "아이콘") editor.appendChild(iconPicker(p, ensure));
      var chips = EXAMPLES.map(function (t) {
        return HX.el("button", { type: "button", class: "hx-it-ex", text: t, onclick: function () {
          var q = ensure("change"), ps = parts(q.memo), i = ps.indexOf(t); if (i >= 0) ps.splice(i, 1); else ps.push(t);
          q.memo = ps.join(", "); memo.value = q.memo; paintChips(); renderPinList(); paintPins(); B.changed();
          cbtns[0].setAttribute("aria-pressed", "true"); cbtns[1].setAttribute("aria-pressed", "false");
        } });
      });
      function paintChips() { var q = picked && picked.pinId ? st.pins[picked.pinId] : null, ps = parts(q && q.memo); chips.forEach(function (c) { c.setAttribute("aria-pressed", ps.indexOf(c.textContent) >= 0 ? "true" : "false"); }); }
      paintChips();
      if (!p || p.v === "change") editor.appendChild(HX.el("div", { class: "hx-sd-change" }, [HX.el("div", { class: "hx-it-sub", text: "어떻게 바꿀까요? 눌러서 고르거나 직접 적어 주세요" }), HX.el("div", { class: "hx-it-exs" }, chips), memo]));
      if (p) editor.appendChild(HX.btn("이 의견 지우기", { cls: "hx-sd-del", icon: HX.icon("#i-trash"), onclick: function () { delete st.pins[p.id]; picked.pinId = null; renderEditor(); paintPins(); renderPinList(); B.changed(); } }));
    }
    // ---------- 아이콘 바꾸기: 허용된 Lucide 아이콘 중에서 고르면 화면에 바로 반영 ----------
    var ICONS = (function () { try { return JSON.parse((doc.getElementById("hx-icons") || {}).textContent || "[]"); } catch (e) { return []; } })();
    function iconNameOf(svg) { var u = svg && svg.querySelector("use"); var h = u && (u.getAttribute("href") || u.getAttribute("xlink:href")) || ""; return h.replace(/^#i-/, ""); }
    function setIcon(svg, name) { var u = svg && svg.querySelector("use"); if (u) { u.setAttribute("href", "#i-" + name); } }
    function applyIconPins() {   // 저장된 아이콘 교체를 화면에 다시 입힌다
      pinsOf(cur).forEach(function (p) { if (p.icon) { var el = resolve(p.path); if (el) setIcon(el, p.icon.to); } });
    }
    function iconPicker(p, ensure) {
      var original = p && p.icon ? p.icon.from : iconNameOf(picked.el), now = iconNameOf(picked.el);
      var q = HX.el("input", { class: "hx-input hx-ip-search", type: "search", placeholder: "아이콘 찾기 (예: calendar, bell, user)", "aria-label": "아이콘 찾기" });
      var grid = HX.el("div", { class: "hx-ip-grid", role: "listbox", "aria-label": "Lucide 아이콘" });
      function paint() {
        grid.innerHTML = "";
        var t = q.value.trim().toLowerCase();
        ICONS.filter(function (c) { return !t || c.name.indexOf(t) >= 0 || c.key.indexOf(t) >= 0; }).slice(0, 120).forEach(function (c) {
          var b = HX.el("button", { type: "button", class: "hx-ip-item" + (c.name === now ? " hx-on" : ""), title: c.name, "aria-label": c.name, onclick: function () {
            var pin = ensure("change");
            pin.icon = { from: original, to: c.name }; pin.memo = pin.memo || "";
            if (c.name === original) { delete st0().pins[pin.id]; picked.pinId = null; }
            setIcon(picked.el, c.name); now = c.name;
            renderEditor(); paintPins(); renderPinList(); B.changed();
          } }, HX.icon("#i-" + c.name));
          grid.appendChild(b);
        });
        if (!grid.children.length) grid.appendChild(HX.el("div", { class: "hx-muted", text: "맞는 아이콘이 없어요" }));
      }
      q.addEventListener("input", paint); paint();
      return HX.el("div", { class: "hx-ip" }, [
        HX.el("div", { class: "hx-it-sub", text: "다른 아이콘으로 바꾸기 · 지금: " + now + (now !== original ? " (원래 " + original + ")" : "") }), q, grid]);
    }
    function st0() { return B.state; }
    function renderPinList() {
      pinList.innerHTML = "";
      if (!cur || cur === ALL) return;
      var ps = pinsOf(cur);
      pinList.appendChild(HX.el("div", { class: "hx-sd-h", text: "이 화면에 남긴 의견 " + ps.length + "개" }));
      if (!ps.length) pinList.appendChild(HX.el("div", { class: "hx-muted", text: "아직 없어요." }));
      ps.forEach(function (p) {
        pinList.appendChild(HX.el("button", { type: "button", class: "hx-sd-pinrow hx-pin-" + p.v, onclick: function () { pick(resolve(p.path), p.id); } }, [
          HX.el("span", { class: "hx-pin hx-pin-" + p.v, text: String(p.id) }),
          HX.el("span", { class: "hx-sd-pinrow-t" }, [HX.el("b", { text: p.desc }), HX.el("span", { text: p.icon ? "아이콘 " + p.icon.from + " → " + p.icon.to + (B.one(p.memo) ? " · " + B.one(p.memo) : "") : p.v === "change" ? "바꿔 주세요" + (B.one(p.memo) ? ": " + B.one(p.memo) : "") : "빼 주세요" })])]));
      });
    }
    function wirePicking() {
      var sec = frame.section;
      sec.addEventListener("mousemove", function (e) {
        var t = targetOf(e.target); if (!t) { hov.style.display = hovLab.style.display = "none"; return; }
        place(hov, t); var q = rectIn(t);
        hovLab.textContent = descOf(t); hovLab.style.display = ""; hovLab.style.left = Math.max(0, q.x) + "px"; hovLab.style.top = Math.max(0, q.y - 24) + "px";
      });
      sec.addEventListener("mouseleave", function () { hov.style.display = hovLab.style.display = "none"; });
      // 화면 속 버튼·링크·입력칸이 실제로 동작하지 않게 막고, 누른 요소를 고른다
      sec.addEventListener("mousedown", function (e) { e.preventDefault(); }, true);
      sec.addEventListener("click", function (e) { e.preventDefault(); e.stopPropagation(); var t = targetOf(e.target); if (t) pick(t); }, true);
    }
    function show(slug, key) {
      cur = slug; paintList();
      stage.innerHTML = ""; sideScreen.innerHTML = ""; frame = null; picked = null;
      view.classList.toggle("hx-sd-mode-all", slug === ALL);
      if (slug === ALL) {
        stage.appendChild(HX.el("div", { class: "hx-sd-all-hint" }, [
          HX.el("b", { text: "화면마다 의견을 남겨 주세요" }),
          HX.el("span", { text: "왼쪽에서 화면을 고르면 크게 보여요. 화면에서 고치고 싶은 곳(버튼·글자·아이콘·묶음)을 누르고 바꿔주세요 · 빼주세요를 골라 주세요." }),
          HX.el("span", { text: "오른쪽의 질문에도 답해 주시고, 다 되면 위쪽 '의견 보내기'를 눌러 주세요." })]));
        B.selectFlow(null, null); B.panel.render(true);
        return;
      }
      var s = HX.bySlug[slug]; if (!s) return;
      // 가운데: 화면 한 장 (폭에 맞춤, 길면 세로 스크롤)
      box = HX.el("div", { class: "hx-sd-frame" });
      stage.appendChild(HX.el("div", { class: "hx-sd-stage-head" }, [HX.badge(s.id), HX.el("h2", { text: s.name }),
        HX.btn("크게 보기", { icon: HX.icon("#i-maximize-2"), title: "실제 크기로 열기", onclick: function () { HX.openScreen(slug); } })]));
      stage.appendChild(box);
      frame = HX.mountFrame(slug, box, { fit: "width", fullHeight: true, maxScale: 1, pad: 0, badges: false, onLayout: function () { paintPins(); } });
      box.appendChild(hov); box.appendChild(hovLab); box.appendChild(selBox); box.appendChild(pinLayer);
      hov.style.display = hovLab.style.display = selBox.style.display = "none";
      picked = null; wirePicking(); applyIconPins();
      // 오른쪽: 이 화면 정보 + 고른 곳 + 남긴 의견
      var tags = [HX.el("span", { class: "hx-tag hx-role", text: roleName(s.role) })];
      if (s.state) tags.push(HX.el("span", { class: "hx-tag hx-state", text: HX.stateLabel(s.state) }));
      sideScreen.appendChild(HX.el("div", { class: "hx-sd-head" }, [HX.el("div", { class: "hx-sd-tags" }, tags),
        s.purpose ? HX.el("p", { class: "hx-sd-purpose", text: s.purpose }) : null]));
      // 이 화면의 정책(규칙) — 구역 보드의 검은 상자와 같은 내용. 틀렸으면 화면 메모로 고쳐 달라고 한다
      if (s.policy && s.policy.length) sideScreen.appendChild(HX.el("div", { class: "hx-sd-policy" }, [HX.el("span", { class: "hx-sd-k", text: "이 화면의 규칙" })].concat(s.policy.map(function (p) {
        return HX.el("div", { class: "hx-sd-pol" }, [HX.el("b", { text: p.title }), HX.el("ul", {}, (p.items || []).map(function (t) { return HX.el("li", { text: t }); }))]);
      })).concat([HX.el("span", { class: "hx-muted", text: "규칙이 틀렸으면 아래 화면 메모에 적어 주세요" })])));
      sideScreen.appendChild(HX.btn("사용 흐름에서 보기", { cls: "hx-sd-inflow", icon: HX.icon("#i-workflow"), onclick: function () { B.showInFlow(slug); } }));
      sideScreen.appendChild(editor); sideScreen.appendChild(pinList);
      var ss = B.screenState(s.id);
      var rm = HX.el("input", { type: "checkbox", onchange: function () { ss.remove = rm.checked; B.changed(); } }); rm.checked = !!ss.remove;
      var smemo = HX.el("textarea", { class: "hx-ta hx-ta-sm", rows: "2", placeholder: "이 화면 전체에 대한 메모 (선택)", "aria-label": "화면 " + s.id + " 메모",
        oninput: function () { ss.memo = smemo.value; B.changed(); } });
      smemo.value = ss.memo || "";
      sideScreen.appendChild(HX.el("div", { class: "hx-sd-screen-opts" }, [HX.el("label", { class: "hx-check" }, [rm, "이 화면 자체를 빼주세요"]), smemo]));
      var i = order.indexOf(slug);
      var pv = HX.btn("이전 화면", { icon: HX.icon("#i-chevron-left"), onclick: function () { step(-1); } }); pv.disabled = i <= 0;
      var nx = HX.btn("다음 화면", { onclick: function () { step(1); } }); nx.appendChild(HX.icon("#i-chevron-right")); nx.disabled = i >= order.length - 1;
      sideScreen.appendChild(HX.el("div", { class: "hx-bd-pn" }, [pv, HX.el("span", { class: "hx-bar-spacer" }), nx]));
      renderEditor(); renderPinList(); paintFrame();
      side.scrollTop = 0; stage.scrollTop = 0;
      HX.relayout();
      if (key && /^pin:/.test(key)) setTimeout(function () { var p = B.state.pins[Number(key.slice(4))]; if (p) pick(resolve(p.path), p.id); }, 80);
    }
    function step(d) {
      if (cur === ALL) { if (d > 0) show(order[0]); return; }
      var i = order.indexOf(cur) + d;
      if (i < 0) show(ALL); else if (i < order.length) show(order[i]);
    }

    // ---------- 탭 전환 ----------
    var tabNow = "flow";
    B.tab = function () { return tabNow; };
    B.setTab = function (t, o) {
      tabNow = t === "design" || (t === "concept" && hasConcepts) ? t : "flow";
      app.classList.toggle("hx-tab-design", tabNow === "design");
      app.classList.toggle("hx-tab-concept", tabNow === "concept");
      Object.keys(tabBtns).forEach(function (k) { tabBtns[k].setAttribute("aria-selected", k === tabNow ? "true" : "false"); tabBtns[k].classList.toggle("hx-on", k === tabNow); });
      if (tabNow === "design" && !cur && !(o && o.slug)) show(order[0] || ALL);
      if (tabNow === "flow" && B.view) B.view.onShow();
      HX.relayout();
    };
    B.showDesign = function (slug, key) { B.setTab("design", { slug: slug }); show(slug || ALL, key); };
    B.showInFlow = function (slug, flowIndex) {
      B.setTab("flow");
      B.view.focus(slug);
    };
    // 화면 디자인 탭에서 다른 곳(지금까지 남긴 의견 등)이 화면을 고르면 → 이 탭 안에서 보여준다
    B.selectFlow = B.select;
    B.select = function (slug, key, o) {
      if (tabNow === "design" && slug) { show(slug, key); return; }
      return B.selectFlow(slug, key, o);
    };

    HX.on("board-change", function () { paintList(); paintFrame(); if (cur && cur !== ALL) { if (picked && picked.pinId && !B.state.pins[picked.pinId]) picked.pinId = null; paintPins(); renderPinList(); } });
    window.addEventListener("resize", function () { paintPins(); });
    // 화면 디자인 탭 키보드: ↑/↓ · ←/→ 로 화면 넘기기
    doc.addEventListener("keydown", function (e) {
      if (tabNow !== "design") return;
      var t = e.target; if (t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.isContentEditable) || doc.querySelector(".hx-modal") || e.metaKey || e.ctrlKey || e.altKey) return;
      var d = e.key === "ArrowDown" || e.key === "ArrowRight" ? 1 : e.key === "ArrowUp" || e.key === "ArrowLeft" ? -1 : 0;
      if (d) { e.preventDefault(); e.stopImmediatePropagation(); step(d); }
      else if (e.key === "Escape") { e.stopImmediatePropagation(); }
    }, true);

    buildList();
    B.setTab(hasConcepts && !B.focus.length ? "concept" : "flow");
  };
})();
