/* 23-board-send.js — "의견 보내기": 복사하기 전에 무엇이 전달되는지 사람이 읽는 말로 먼저 보여준다.
   실제로 복사되는 글은 B.answer()(형식 고정, answer-parsing.md가 읽음)이고, 이 창은 그것을 풀어서 보여줄 뿐이다. */
(function () {
  "use strict";
  var HX = window.HX, B = HX.board, doc = document;
  if (!B) return;

  function one(s) { return String(s || "").replace(/\s*\n+\s*/g, " ").trim(); }
  function screenOf(regionId) {
    var hit = null;
    HX.data.screens.forEach(function (s) { s.regions.forEach(function (r) { if (r.id === regionId) hit = s; }); });
    return hit;
  }

  /* 사람이 읽는 요약: [{title, items:[문장]}] */
  B.summary = function () {
    var st = B.state, board = HX.data.board || {}, groups = [];
    var locked = Array.isArray(board.locked) ? board.locked : [];
    // 1) 화면 느낌
    var look = B.lookLine();
    var same = st.theme === B.REC.theme && st.type === B.REC.type && st.accent === B.fixSwatch(st.theme, B.REC.accent);
    groups.push({ title: "화면 느낌", items: [look + (locked.indexOf("theme") >= 0 ? " (이미 정해짐)" : same ? " — 추천 그대로" : " — 직접 고름")] });
    // 2) 확인 질문 중 추천과 다르게 고른 것
    var asks = [];
    if (locked.indexOf("ask") < 0) (board.ask || []).forEach(function (q) {
      var ri = typeof q.recommended === "number" ? q.recommended : 0, v = st.ask[q.id];
      if (typeof v === "number" && v !== ri && q.options[v] != null) asks.push(q.text + " → " + String(q.options[v]).replace(/\s*\(추천\)/, ""));
    });
    if (asks.length) groups.push({ title: "다르게 고른 질문", items: asks });
    // 3) 번호별 의견
    var regs = [];
    Object.keys(st.regions).map(Number).sort(function (a, b) { return a - b; }).forEach(function (id) {
      var r = st.regions[id], s = screenOf(id); if (!r || !s) return;
      var reg = s.regions.filter(function (x) { return x.id === id; })[0];
      var where = "'" + s.name + "' 화면의 " + id + "번 " + (reg ? reg.label : "");
      if (r.v === "change") regs.push(where + " — 바꿔 주세요" + (one(r.memo) ? ": " + one(r.memo) : ""));
      else if (r.v === "remove") regs.push(where + " — 빼 주세요");
    });
    Object.keys(st.pins || {}).map(Number).sort(function (a, b) { return a - b; }).forEach(function (id) {
      var p = st.pins[id], s = p && HX.bySlug[p.slug]; if (!s || (p.v !== "change" && p.v !== "remove")) return;
      regs.push("'" + s.name + "' 화면의 " + p.desc + (p.where ? " ('" + p.where + "' 안)" : "") + (p.v === "change" && p.icon ? " — 아이콘을 " + p.icon.to + "(으)로 바꿔 주세요" + (one(p.memo) ? " · " + one(p.memo) : "") : p.v === "change" ? " — 바꿔 주세요" + (one(p.memo) ? ": " + one(p.memo) : "") : " — 빼 주세요"));
    });
    if (regs.length) groups.push({ title: "고쳐 달라고 한 곳", items: regs });
    // 4) 화면 단위
    var scr = [];
    HX.data.screens.forEach(function (s) {
      var x = st.screens[s.id]; if (!x) return;
      if (x.remove) scr.push("'" + s.name + "' 화면을 빼 주세요");
      if (one(x.memo)) scr.push("'" + s.name + "' 화면: " + one(x.memo));
    });
    if (scr.length) groups.push({ title: "화면 전체에 대한 의견", items: scr });
    // 5) 더 필요한 것
    var more = [];
    if (one(st.add)) more.push("추가로 필요한 것: " + one(st.add));
    if (one(st.memo)) more.push("그 밖의 메모: " + one(st.memo));
    if (more.length) groups.push({ title: "더 필요한 것", items: more });
    return groups;
  };

  B.openSend = function () {
    var text = B.answer(), groups = B.summary(), n = B.diffCount();
    var close = HX.btn("닫기", { onclick: function () { done(); } });
    var copy = HX.btn("복사하기", { cls: "hx-primary", icon: HX.icon("#i-copy"), onclick: function () {
      HX.copyText(text).then(function (ok) {
        if (ok) { done(); HX.toast("복사했어요. 채팅창에 붙여넣어 주세요."); return; }
        raw.open = true; ta.focus(); ta.select();
        HX.toast("자동 복사가 안 됐어요. 아래 글을 직접 복사해 주세요.");
      });
    } });
    var ta = HX.el("textarea", { class: "hx-ta hx-copy-box", readonly: true, rows: "6" }); ta.value = text;
    var raw = HX.el("details", { class: "hx-send-raw" }, [HX.el("summary", { text: "실제로 복사되는 글 보기" }), ta]);
    var body = HX.el("div", { class: "hx-send-body" }, [
      HX.el("p", { class: "hx-send-lead", text: n ? "아래 " + n + "가지를 전달해요. 나머지는 모두 추천대로 진행해요." : "아직 고친 곳이 없어요. 이대로 보내면 모두 추천대로 진행해요." })]);
    groups.forEach(function (g) {
      body.appendChild(HX.el("div", { class: "hx-send-group" }, [HX.el("h3", { text: g.title }),
        HX.el("ul", {}, g.items.map(function (t) { return HX.el("li", { text: t }); }))]));
    });
    body.appendChild(raw);
    var esc = function (e) { if (e.key === "Escape") done(); };
    var m = HX.el("div", { class: "hx-modal hx-app" }, [HX.el("div", { class: "hx-modal-backdrop", onclick: function () { done(); } }),
      HX.el("div", { class: "hx-modal-panel hx-send", role: "dialog", "aria-modal": "true", "aria-label": "의견 보내기" }, [
        HX.el("div", { class: "hx-modal-head" }, [HX.el("h2", { text: "이렇게 전달돼요" }), HX.el("span", { class: "hx-bar-spacer" })]),
        body,
        HX.el("div", { class: "hx-send-foot" }, [HX.el("span", { class: "hx-send-hint", text: "복사한 뒤 채팅창에 붙여넣으면 다음 초안에 반영돼요" }), HX.el("span", { class: "hx-bar-spacer" }), close, copy])])]);
    function done() { if (m.isConnected) m.remove(); doc.removeEventListener("keydown", esc); }
    doc.body.appendChild(m); doc.addEventListener("keydown", esc); copy.focus();
  };
})();
