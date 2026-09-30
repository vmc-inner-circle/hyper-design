/* 20-board.js — board 모드 상태·테마·"답변 복사" 텍스트. 화면 배치는 22-board-canvas.js, 오른쪽 패널은 21-board-panel.js.
   data.board = { hero, recommend:{theme,themeWhy,type,typeWhy,accent,accentWhy}, ask:[{id,text,options[],recommended}],
                  locked:["theme","toggles","ask"], focus:["slug"] }  — 전부 없을 수 있음(방어). */
(function () {
  "use strict";
  var HX = window.HX, doc = document, root = doc.documentElement;
  var B = HX.board = {};
  var board = HX.data.board || {};
  var rec = board.recommend || {};
  var locked = Array.isArray(board.locked) ? board.locked : [];
  // "toggles"는 글자 크기(type)와 버튼 색(swatch)을 함께 잠근다 (예전 형식)
  var isLocked = B.isLocked = function (k) {
    if (locked.indexOf(k) >= 0) return true;
    if ((k === "type" || k === "swatch") && locked.indexOf("toggles") >= 0) return true;
    return k === "toggles" && locked.indexOf("type") >= 0 && locked.indexOf("swatch") >= 0;
  };
  var toggles = HX.meta.toggles || {};
  // 분위기(look)와 버튼 색(swatch): build.js가 screens.json looks에서 넘긴다
  var LOOKS = B.looks = HX.meta.looks || [];
  B.look = function (id) { return LOOKS.filter(function (l) { return l.id === id; })[0] || LOOKS[0] || { id: id, name: id, swatches: [] }; };
  B.swatch = function (lookId, id) { var L = B.look(lookId); return L.swatches.filter(function (s) { return s.id === id; })[0] || L.swatches[0] || { id: id, name: id, hex: "#999999" }; };
  function fixSwatch(lookId, v) { var L = B.look(lookId); return L.swatches.some(function (s) { return s.id === v; }) ? v : (v === "vivid" && L.swatches[1] ? L.swatches[1].id : (L.swatches[0] || {}).id); }
  // 확정(잠금)된 값은 1턴 추천(board.recommend)이 아니라 확정값(theme · toggles)을 쓴다
  var validLook = function (id) { return LOOKS.some(function (l) { return l.id === id; }); };
  var recTheme = isLocked("theme") && validLook(HX.meta.theme) ? HX.meta.theme : (validLook(rec.theme) ? rec.theme : HX.meta.theme);
  var recType = isLocked("type") && toggles.type ? toggles.type : (rec.type || toggles.type || "normal");
  var recSwatch = isLocked("swatch") && toggles.swatch ? toggles.swatch : (rec.swatch || rec.accent || toggles.swatch);
  var REC = B.REC = { theme: recTheme, type: recType, accent: fixSwatch(recTheme, recSwatch) };
  // 단계: "concept"(1턴 — 시안만 보여주고 고르게) / "draft"(2턴부터 — 고른 시안으로 만든 전체 화면)
  var STAGE = B.stage = HX.meta.stage === "concept" ? "concept" : "draft";
  // 시안(concepts): 레퍼런스 조사로 만든 방향 5개. draft 단계의 화면들은 HX.meta.concept(고른 시안)으로 만든 것
  var CONCEPTS = B.concepts = (HX.data.concepts || []).filter(function (c) { return c && c.id; });
  B.concept = function (id) { return CONCEPTS.filter(function (c) { return c.id === id; })[0] || CONCEPTS[0] || null; };
  REC.concept = CONCEPTS.length ? (B.concept(HX.meta.concept || rec.concept) || CONCEPTS[0]).id : null;
  B.recWhy = { theme: rec.themeWhy || "", type: rec.typeWhy || "", accent: rec.swatchWhy || rec.accentWhy || "" };
  B.fixSwatch = fixSwatch;
  var TYPE_LABEL = B.TYPE_LABEL = { normal: "보통", large: "크게" }, ACCENT_LABEL = B.ACCENT_LABEL = { calm: "차분", vivid: "선명" };
  var storeKey = "hx:" + (HX.meta.project || "project") + ":" + (HX.meta.stage === "concept" ? "concept" : HX.meta.round || 1);
  B.data = board;
  B.asks = Array.isArray(board.ask) ? board.ask.filter(function (q) { return q && q.id && Array.isArray(q.options); }) : [];
  B.focus = Array.isArray(board.focus) ? board.focus.filter(function (k) { return HX.bySlug[k]; }) : [];

  // ---------- 상태 ----------
  // pins: 화면 디자인 탭에서 사용자가 화면 아무 곳이나 골라 단 의견 { id: {id, sid, slug, path, desc, where, v, memo} }
  var state = { concept: REC.concept, cmemo: {}, theme: REC.theme, type: REC.type, accent: REC.accent, ask: {}, regions: {}, screens: {}, pins: {}, pinSeq: 0, add: "", memo: "" };
  (function restore() {
    var saved = HX.storage.get(storeKey); if (!saved || typeof saved !== "object") return;
    ["concept", "theme", "type", "accent", "add", "memo"].forEach(function (k) { if (typeof saved[k] === "string") state[k] = saved[k]; });
    if (isLocked("concept") || !B.concept(state.concept) || (CONCEPTS.length && B.concept(state.concept).id !== state.concept)) state.concept = REC.concept;
    // regions(미리 정한 번호로 남긴 의견)는 지금 보드에서 보이지도 지울 수도 없으므로 불러오지 않는다
    ["ask", "screens", "pins", "cmemo"].forEach(function (k) { if (saved[k] && typeof saved[k] === "object") state[k] = saved[k]; });
    if (typeof saved.pinSeq === "number") state.pinSeq = saved.pinSeq;
    if (isLocked("theme") || !LOOKS.some(function (l) { return l.id === state.theme; })) state.theme = REC.theme;
    if (isLocked("type")) state.type = REC.type;
    if (isLocked("swatch")) state.accent = REC.accent;
    state.accent = fixSwatch(state.theme, state.accent);
    if (isLocked("ask")) state.ask = {};
  })();
  B.state = state;
  B.resetAll = function () {
    state.ask = {}; state.regions = {}; state.screens = {}; state.pins = {}; state.add = ""; state.memo = "";
    if (!isLocked("concept")) { state.concept = REC.concept; state.cmemo = {}; }
    if (!isLocked("theme")) state.theme = REC.theme;
    if (!isLocked("type")) state.type = REC.type;
    if (!isLocked("swatch")) state.accent = fixSwatch(state.theme, REC.accent);
    if (B.applyTheme) B.applyTheme();
    B.changed();
  };
  var saveT = 0;
  B.save = function () { clearTimeout(saveT); saveT = setTimeout(function () { HX.storage.set(storeKey, state); }, 150); };
  /* 상태가 바뀔 때마다: 저장 + 캔버스 표시·패널 요약·복사 버튼 갱신 */
  B.changed = function () { B.save(); HX.emit("board-change"); };
  B.regionState = function (id) { return state.regions[id] || (state.regions[id] = { v: "like", memo: "" }); };
  B.screenState = function (id) { return state.screens[id] || (state.screens[id] = { remove: false, memo: "" }); };
  B.recIndex = function (q) {
    if (typeof q.recommended === "number") return q.recommended;
    var i = (q.options || []).indexOf(q.recommended); return i < 0 ? 0 : i;
  };
  B.askIndex = function (q) { var v = state.ask[q.id]; return typeof v === "number" ? v : B.recIndex(q); };
  // 사람이 읽는 한 줄 / 복사 글 첫 줄(answer-parsing.md: "테마 <look id>(이름) · 글자 <보통|크게> · 버튼색 <swatch id>(이름)")
  B.lookLine = function () { return "분위기 " + B.look(state.theme).name + " · 글자 크기 " + (TYPE_LABEL[state.type] || state.type) + " · 버튼 색 " + B.swatch(state.theme, state.accent).name; };
  B.themeLine = function () {
    var L = B.look(state.theme), sw = B.swatch(state.theme, state.accent);
    return "테마 " + L.id + "(" + L.name + ") · 글자 " + (TYPE_LABEL[state.type] || state.type) + " · 버튼색 " + sw.id + "(" + sw.name + ")";
  };
  B.one = function (s) { return String(s || "").replace(/\s*\n+\s*/g, " / ").trim(); };

  // ---------- 테마 적용: 문서 전체(=캔버스 모든 화면)를 다시 칠한다 ----------
  B.applyTheme = function () {
    state.accent = fixSwatch(state.theme, state.accent);
    root.setAttribute("data-theme", state.theme); root.setAttribute("data-type", state.type); root.setAttribute("data-swatch", state.accent); root.removeAttribute("data-accent");
    // 글자 크기가 바뀌면 화면 길이가 달라진다 → 늘린 프레임을 되돌리고 다시 늘린다
    if (B.view) Object.keys(B.view.frames).forEach(function (k) { B.view.frames[k].resetHeight(); });
    HX.relayout(); B.changed();
  };

  // ---------- 답변 텍스트 (추천과 다른 것만, 순서 고정) — answer-parsing.md와 묶인 형식, 바꾸지 말 것 ----------
  // 시안 단계의 복사 글: "시안 <id>(이름)" · "시안 <id> 메모: …" · 추가 · 메모 (answer-parsing.md §1)
  B.conceptLine = function () { var C = B.concept(state.concept); return C ? "시안 " + C.id + "(" + C.name + ")" : ""; };
  B.conceptMemos = function () {
    return CONCEPTS.filter(function (c) { return B.one((state.cmemo || {})[c.id]); }).map(function (c) { return { c: c, text: B.one(state.cmemo[c.id]) }; });
  };
  B.answer = function () {
    if (STAGE === "concept") {
      var cl = [B.conceptLine()];
      B.conceptMemos().forEach(function (m) { cl.push("시안 " + m.c.id + " 메모: " + m.text); });
      if (B.one(state.add)) cl.push("추가: " + B.one(state.add));
      if (B.one(state.memo)) cl.push("메모: " + B.one(state.memo));
      cl.push("(나머지는 추천대로)");
      return cl.join("\n");
    }
    var locked = Array.isArray(board.locked) ? board.locked : [];
    var lines = [B.themeLine() + (isLocked("theme") && isLocked("type") && isLocked("swatch") ? " (확정)" : "")];
    var one = function (s) { return String(s || "").replace(/\s*\n+\s*/g, " / ").trim(); };
    if (locked.indexOf("ask") < 0) (board.ask || []).forEach(function (q) {
      if (!q || !Array.isArray(q.options)) return;
      var ri = typeof q.recommended === "number" ? q.recommended : Math.max(0, q.options.indexOf(q.recommended));
      var v = state.ask[q.id]; if (typeof v === "number" && v !== ri && q.options[v] != null) lines.push("확인: " + q.id + "=" + q.options[v]);
    });
    var byId = function (a, b) { return a.id - b.id; };
    var regions = []; HX.data.screens.forEach(function (s) { s.regions.forEach(function (r) { regions.push(r); }); });
    regions.sort(byId).forEach(function (r) {
      var st = state.regions[r.id]; if (!st) return;
      if (st.v === "change") lines.push(r.id + " 바꿔" + (one(st.memo) ? ": " + one(st.memo) : ""));
      else if (st.v === "remove") lines.push(r.id + " 빼기");
    });
    HX.data.screens.slice().sort(byId).forEach(function (s) {
      var st = state.screens[s.id]; if (!st) return;
      if (st.remove) lines.push("화면 " + s.id + " 빼기");
      if (one(st.memo)) lines.push("화면 " + s.id + " 메모: " + one(st.memo));
    });
    // 화면 아무 곳이나 골라 단 의견: "화면 <id> · <무엇> 바꿔: 메모 [<위치 경로>]"
    Object.keys(state.pins).map(Number).sort(function (a, b) { return a - b; }).forEach(function (id) {
      var p = state.pins[id]; if (!p || (p.v !== "change" && p.v !== "remove")) return;
      var head = "화면 " + p.sid + " · " + p.desc;
      if (p.v === "change" && p.icon) lines.push(head + " 바꿔: 아이콘 " + p.icon.from + " → " + p.icon.to + (one(p.memo) ? ", " + one(p.memo) : "") + " [" + p.path + "]");
      else lines.push(p.v === "change" ? head + " 바꿔" + (one(p.memo) ? ": " + one(p.memo) : "") + " [" + p.path + "]" : head + " 빼기 [" + p.path + "]");
    });
    if (one(state.add)) lines.push("추가: " + one(state.add));
    if (one(state.memo)) lines.push("메모: " + one(state.memo));
    lines.push("(나머지는 추천대로)");
    return lines.join("\n");
  };
  /* 추천과 다르게 표시한 항목 수 (복사 버튼 숫자) */
  B.diffCount = function () {
    var n = B.answer().split("\n").length - 2;
    if (STAGE === "concept") return n + (state.concept !== REC.concept ? 1 : 0);
    if (!isLocked("theme") && state.theme !== REC.theme) n++;
    if (!isLocked("type") && state.type !== REC.type) n++;
    if (!isLocked("swatch") && state.accent !== fixSwatch(state.theme, REC.accent)) n++;
    return n;
  };
  B.copy = function () {
    var text = B.answer();
    HX.copyText(text).then(function (ok) {
      if (ok) { HX.toast("답변을 복사했어요. 채팅에 붙여넣어 주세요."); return; }
      var ta = HX.el("textarea", { class: "hx-ta hx-copy-box", readonly: true }); ta.value = text;
      var close = HX.btn("닫기", { onclick: function () { m.remove(); doc.removeEventListener("keydown", esc); } });
      var esc = function (e) { if (e.key === "Escape") close.click(); };
      var m = HX.el("div", { class: "hx-modal hx-app" }, [HX.el("div", { class: "hx-modal-backdrop", onclick: function () { close.click(); } }),
        HX.el("div", { class: "hx-modal-panel", role: "dialog", "aria-modal": "true", style: "width:min(640px,100%);height:auto" }, [
          HX.el("div", { class: "hx-modal-head" }, [HX.el("h2", { text: "복사가 안 됐어요 — 아래 글을 직접 복사해 주세요" }), HX.el("span", { class: "hx-bar-spacer" }), close]),
          HX.el("div", { style: "padding:16px" }, ta)])]);
      doc.body.appendChild(m); doc.addEventListener("keydown", esc); ta.focus(); ta.select();
    });
  };

  /* 지금까지 표시한 것 (패널 요약): 화면 id → 영역 id 순 */
  B.marks = function () {
    var out = [], byId = function (a, b) { return a.id - b.id; };
    HX.data.screens.slice().sort(byId).forEach(function (s) {
      var ss = state.screens[s.id];
      if (ss && ss.remove) out.push({ slug: s.slug, kind: "remove", id: "화면 " + s.id, text: s.name + " — 화면 빼기" });
      if (ss && B.one(ss.memo)) out.push({ slug: s.slug, kind: "memo", id: "화면 " + s.id, text: s.name + " — " + B.one(ss.memo) });
      s.regions.slice().sort(byId).forEach(function (r) {
        var st = state.regions[r.id]; if (!st) return;
        if (st.v === "change") out.push({ slug: s.slug, key: r.key, kind: "change", id: String(r.id), text: r.label + " — 바꿔" + (B.one(st.memo) ? ": " + B.one(st.memo) : "") });
        else if (st.v === "remove") out.push({ slug: s.slug, key: r.key, kind: "remove", id: String(r.id), text: r.label + " — 빼기" });
      });
      Object.keys(state.pins).map(Number).sort(function (a, b) { return a - b; }).forEach(function (id) {
        var p = state.pins[id]; if (!p || p.slug !== s.slug || (p.v !== "change" && p.v !== "remove")) return;
        out.push({ slug: s.slug, key: "pin:" + id, kind: p.v, id: "의견 " + id, text: s.name + " · " + p.desc + (p.v === "change" ? " — 바꿔" + (B.one(p.memo) ? ": " + B.one(p.memo) : "") : " — 빼기") });
      });
    });
    return out;
  };
})();
