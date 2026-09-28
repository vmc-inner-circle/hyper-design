/* 21-board-panel.js — board 오른쪽 패널. 선택 없음: 안내·확인할 것·더 필요한 것·지금까지 표시한 것 / 화면 선택: 맥락·영역 행·화면 빼기·메모·이전/다음
   / 번호(영역) 선택: 항목 집중(큰 버튼 3개 · 예시 칩 · 메모 · 이전/다음 번호). */
(function () {
  "use strict";
  var HX = window.HX, B = HX.board;
  var SEG = [["like", "좋아요"], ["change", "바꿔주세요"], ["remove", "빼주세요"]];

  function h(title, extra) { return HX.el("div", { class: "hx-bd-h" }, [HX.el("span", { text: title })].concat(extra || [])); }
  function recTag(why) { return [HX.el("span", { class: "hx-tag hx-rec", text: "추천" }), why ? HX.el("span", { class: "hx-why", text: why }) : null]; }
  function radio(name, value, checked, label, extra, onchange) {
    var input = HX.el("input", { type: "radio", name: name, value: value, onchange: function () { if (input.checked) onchange(value); } });
    input.checked = !!checked;
    return HX.el("label", { class: "hx-radio" }, [input, HX.el("b", { text: label })].concat(extra || []));
  }

  B.buildPanel = function (collapseBtn) {
    var title = HX.el("span", { class: "hx-bd-panel-title" });
    var body = HX.el("div", { class: "hx-bd-panel-body" });
    var el = HX.el("aside", { class: "hx-bd-panel", "aria-label": "의견 남기기" }, [HX.el("div", { class: "hx-bd-panel-head" }, [title, HX.el("span", { class: "hx-bar-spacer" }), collapseBtn]), body]);
    var P = { el: el, rows: {}, slug: undefined, sig: undefined };
    var summary = null;

    // ---------- 선택 없음 ----------
    function home() {
      title.textContent = "전체";
      body.appendChild(HX.el("p", { class: "hx-bd-hint" }, [HX.icon("#i-mouse-pointer-click", "icon icon-sm"), "화면에서 고치고 싶은 곳을 누르면 의견을 남길 수 있어요 · 질문에도 답해 주세요"]));
      if (B.asks.length) {
        var sec = HX.el("section", { class: "hx-bd-sec" }, h("몇 가지만 골라 주세요"));
        if (B.isLocked("ask")) {
          sec.appendChild(HX.el("div", { class: "hx-locked", text: "확정: " + B.asks.map(function (q) { return q.options[B.recIndex(q)]; }).join(" · ") }));
        } else B.asks.forEach(function (q) {
          var ri = B.recIndex(q), cur = B.askIndex(q);
          sec.appendChild(HX.el("div", { class: "hx-ask" }, [HX.el("div", { class: "hx-q", text: q.text }), HX.el("div", { class: "hx-radio-group hx-radio-col" }, q.options.map(function (o, i) {
            return radio("hx-ask-" + q.id, String(i), cur === i, o, i === ri ? recTag(q.why) : null, function (v) { B.state.ask[q.id] = Number(v); B.changed(); });
          }))]));
        });
        body.appendChild(sec);
      }
      var st = B.state;
      var add = HX.el("textarea", { class: "hx-ta", id: "hx-add", placeholder: "예: 짐 체크리스트 화면, 알림 설정", oninput: function () { st.add = add.value; B.changed(); } }); add.value = st.add || "";
      var memo = HX.el("textarea", { class: "hx-ta", id: "hx-memo", placeholder: "예: 부모 화면은 버튼을 더 크게", oninput: function () { st.memo = memo.value; B.changed(); } }); memo.value = st.memo || "";
      body.appendChild(HX.el("section", { class: "hx-bd-sec hx-more" }, [h("더 있었으면 하는 것"),
        HX.el("label", { for: "hx-add", text: "추가로 필요한 화면·기능" }), add, HX.el("label", { for: "hx-memo", text: "그 밖의 메모" }), memo]));
      summary = HX.el("ul", { class: "hx-bd-marks" });
      body.appendChild(HX.el("section", { class: "hx-bd-sec" }, [h("지금까지 남긴 의견"), summary]));
      paintSummary();
    }
    function paintSummary() {
      if (!summary || !summary.isConnected) return;
      summary.innerHTML = "";
      var st = B.state, R = B.REC, diffs = [];
      if (!B.isLocked("theme") && st.theme !== R.theme) diffs.push("분위기 " + B.look(st.theme).name);
      if (!B.isLocked("type") && st.type !== R.type) diffs.push("글자 크기 " + B.TYPE_LABEL[st.type]);
      if (!B.isLocked("swatch") && st.accent !== B.fixSwatch(st.theme, R.accent)) diffs.push("버튼 색 " + B.swatch(st.theme, st.accent).name);
      function del(fn) { return HX.btn("", { cls: "hx-icon-btn hx-mark-del", aria: "지우기", title: "이 의견 지우기", icon: HX.icon("#i-x"), onclick: function (e) { e.stopPropagation(); fn(); B.changed(); P.render(true); } }); }
      if (diffs.length) summary.appendChild(HX.el("li", { class: "hx-bd-markrow" }, [HX.el("div", { class: "hx-bd-mark hx-k-theme" }, [HX.el("span", { class: "hx-bd-mark-id", text: "분위기" }), HX.el("span", { text: diffs.join(" · ") + " (추천과 다름)" })]),
        del(function () { if (!B.isLocked("theme")) st.theme = R.theme; if (!B.isLocked("type")) st.type = R.type; if (!B.isLocked("swatch")) st.accent = B.fixSwatch(st.theme, R.accent); B.applyTheme(); })]));
      B.asks.forEach(function (q) {
        var v = st.ask[q.id], ri = B.recIndex(q); if (B.isLocked("ask") || typeof v !== "number" || v === ri) return;
        summary.appendChild(HX.el("li", { class: "hx-bd-markrow" }, [HX.el("div", { class: "hx-bd-mark hx-k-ask" }, [HX.el("span", { class: "hx-bd-mark-id", text: "질문" }), HX.el("span", { text: q.text + " → " + q.options[v] })]),
          del(function () { delete st.ask[q.id]; })]));
      });
      var ms = B.marks();
      ms.forEach(function (m) {
        summary.appendChild(HX.el("li", { class: "hx-bd-markrow" }, [HX.el("button", { type: "button", class: "hx-bd-mark hx-k-" + m.kind, title: "이 화면으로 이동", onclick: function () { B.select(m.slug, m.key || null, { focus: true }); } }, [
          HX.el("span", { class: "hx-bd-mark-id", text: m.id }), HX.el("span", { text: m.text })]),
          del(function () {
            var s = HX.bySlug[m.slug];
            if (m.key && /^pin:/.test(m.key)) delete st.pins[Number(m.key.slice(4))];
            else if (m.key) delete st.regions[(s.regions.filter(function (r) { return r.key === m.key; })[0] || {}).id];
            else { var ss = st.screens[s.id]; if (ss) { if (m.kind === "remove") ss.remove = false; else ss.memo = ""; } }
          })]));
      });
      var n = B.diffCount();
      if (!n) summary.appendChild(HX.el("li", { class: "hx-muted", text: "아직 없어요. 지금 보내면 모두 추천대로 가요." }));
      else {
        var armed = false, resetBtn = HX.btn("모두 지우기", { cls: "hx-bd-reset", icon: HX.icon("#i-trash"), onclick: function () {
          if (!armed) { armed = true; resetBtn.lastChild.textContent = "한 번 더 누르면 모두 지워져요"; resetBtn.classList.add("hx-armed"); return; }
          B.resetAll(); P.render(true);
        } });
        summary.appendChild(HX.el("li", {}, resetBtn));
      }
    }

    // ---------- 화면 선택 ----------
    function screen(s) {
      var info = B.instInfo(B.sel.inst);
      title.textContent = info ? info.head : "화면";
      var tags = [HX.el("span", { class: "hx-tag hx-role", text: HX.roleLabel(s.role) })];
      if (B.focus.indexOf(s.slug) >= 0) tags.push(HX.el("span", { class: "hx-tag hx-bd-tag-fixed", text: "고친 화면" }));
      body.appendChild(HX.el("div", { class: "hx-bd-screen-head" }, [
        HX.el("div", { class: "hx-bd-screen-title" }, [HX.badge(s.id), HX.el("h3", { text: s.name })]),
        HX.el("div", { class: "hx-bd-screen-tags" }, tags),
        s.purpose ? HX.el("p", { class: "hx-bd-purpose", text: s.purpose }) : null,
        HX.btn("크게 보기", { cls: "hx-bd-open", icon: HX.icon("#i-maximize-2"), title: "실제 크기로 열기 (더블클릭)", onclick: function () { HX.openScreen(s.slug); } })]));
      // 지금 보는 복사본의 맥락: 어느 시나리오의 몇 번째 단계인지
      if (info) {
        var ctx = HX.el("div", { class: "hx-bd-ctx" });
        if (!info.flow) ctx.appendChild(HX.el("div", { text: "어느 흐름에도 안 나오는 화면이에요" }));
        else {
          ctx.appendChild(HX.el("div", {}, [HX.el("span", { class: "hx-bd-ctx-k", text: "흐름" }), HX.el("b", { text: info.flow.name || "" })]));
          if (info.inStep) ctx.appendChild(HX.el("div", {}, [HX.el("span", { class: "hx-bd-ctx-k", text: "이전 단계" }), info.inStep.action || ""]));
          if (info.outStep) {
            var to = HX.bySlug[info.outStep.to];
            ctx.appendChild(HX.el("div", {}, [HX.el("span", { class: "hx-bd-ctx-k", text: "다음" }), (info.outStep.action || "") + " → ", HX.el("b", { text: to ? to.name : info.outStep.to })]));
          }
        }
        body.appendChild(ctx);
      }
      var list = HX.el("div", { class: "hx-rows" });
      P.rows = {};
      s.regions.forEach(function (r) {
        var st = B.regionState(r.id);
        var memo = HX.el("input", { class: "hx-memo", type: "text", placeholder: "어떻게 바꿀까요? (선택)", value: st.memo || "", "aria-label": r.id + " 메모",
          oninput: function () { st.memo = memo.value; B.changed(); } });
        var seg = HX.el("div", { class: "hx-seg", role: "group", "aria-label": r.label });
        var btns = SEG.map(function (o) {
          var b = HX.el("button", { type: "button", class: "hx-v-" + o[0], text: o[1], onclick: function () { st.v = o[0]; paint(); B.changed(); if (o[0] === "change") memo.focus(); } });
          seg.appendChild(b); return b;
        });
        var row = HX.el("div", { class: "hx-row", dataset: { key: r.key }, title: "눌러서 이 번호만 크게 보기" }, [
          HX.el("div", { class: "hx-row-top" }, [HX.badge(r.id), HX.el("span", { class: "hx-row-label", text: r.label, title: r.why || "" }), HX.icon("#i-chevron-right", "icon icon-sm hx-row-go")]),
          r.why ? HX.el("div", { class: "hx-why hx-row-why", text: r.why }) : null, seg, memo]);
        function paint() {
          btns.forEach(function (b, i) { b.setAttribute("aria-pressed", SEG[i][0] === st.v ? "true" : "false"); });
          row.classList.toggle("hx-v-remove", st.v === "remove"); row.classList.toggle("hx-v-change", st.v === "change");
          memo.style.display = st.v === "change" ? "" : "none";
        }
        paint();
        row.addEventListener("mouseenter", function () { B.hl(s.slug, r.key, true); });
        row.addEventListener("mouseleave", function () { B.hl(s.slug, r.key, B.sel.key === r.key); });
        row.addEventListener("click", function (e) { if (e.target === row || e.target.closest(".hx-row-top")) B.select(s.slug, r.key, { inst: B.sel.inst }); });
        P.rows[r.key] = row; list.appendChild(row);
      });
      if (!s.regions.length) list.appendChild(HX.el("div", { class: "hx-muted", text: "이 화면에는 번호가 없어요. 아래 메모로 알려 주세요." }));
      body.appendChild(HX.el("section", { class: "hx-bd-sec" }, [h("이 화면의 번호 " + s.regions.length + "개"), list]));
      var ss = B.screenState(s.id);
      var rm = HX.el("input", { type: "checkbox", onchange: function () { ss.remove = rm.checked; B.changed(); } });
      rm.checked = !!ss.remove;
      var smemo = HX.el("textarea", { class: "hx-ta hx-ta-sm", placeholder: "이 화면에 대한 메모 (선택)", "aria-label": "화면 " + s.id + " 메모", oninput: function () { ss.memo = smemo.value; B.changed(); } });
      smemo.value = ss.memo || "";
      body.appendChild(HX.el("section", { class: "hx-bd-sec" }, [HX.el("label", { class: "hx-check" }, [rm, "이 화면 자체를 빼주세요"]), smemo]));
      var prev = HX.btn("이전 단계", { icon: HX.icon("#i-chevron-left"), onclick: function () { B.go(-1); } });
      var next = HX.btn("다음 단계", { onclick: function () { B.go(1); } }); next.appendChild(HX.icon("#i-chevron-right"));
      prev.disabled = !B.canGo(-1); next.disabled = !B.canGo(1);
      body.appendChild(HX.el("div", { class: "hx-bd-pn" }, [prev, HX.el("span", { class: "hx-bar-spacer" }), next]));
    }

    // ---------- 항목 집중: 번호 하나만 크게 · 큰 버튼 3개 · 예시 칩 ----------
    var CHOICES = [["like", "좋아요", "#i-thumbs-up"], ["change", "바꿔주세요", "#i-pencil"], ["remove", "빼주세요", "#i-x"]];
    var EXAMPLES = ["글자 더 크게", "더 단순하게", "위로 올려주세요", "잘 안 보여요", "색을 바꿔주세요", "다른 모양으로", "버튼을 더 크게", "순서를 바꿔주세요"];
    function parts(m) { return String(m || "").split(/\s*,\s*/).filter(Boolean); }
    function item(s, r) {
      title.textContent = "번호 " + r.id;
      var st = B.regionState(r.id);
      body.appendChild(HX.el("div", { class: "hx-it-head" }, [
        HX.badge(r.id, "hx-badge-lg"),
        HX.el("div", { class: "hx-it-titles" }, [HX.el("h3", { class: "hx-it-label", text: r.label }), HX.el("div", { class: "hx-it-where", text: "어느 화면: " + s.name })])]));
      if (r.why) body.appendChild(HX.el("div", { class: "hx-it-why" }, [HX.el("div", { class: "hx-it-why-h", text: "이게 뭐냐면" }), HX.el("div", { text: r.why })]));
      var choice = HX.el("div", { class: "hx-it-choices", role: "group", "aria-label": r.label });
      var cbtns = CHOICES.map(function (c) {
        var b = HX.el("button", { type: "button", class: "hx-it-choice hx-v-" + c[0], onclick: function () { st.v = c[0]; paint(); B.changed(); if (c[0] === "change") memo.focus(); } },
          [HX.icon(c[2]), HX.el("span", { text: c[1] })]);
        choice.appendChild(b); return b;
      });
      // 아이콘은 빌드가 리터럴로 찾는다: "#i-thumbs-up" "#i-pencil" "#i-x"
      body.appendChild(choice);
      var memo = HX.el("textarea", { class: "hx-ta hx-it-memo", rows: "2", placeholder: "직접 적어도 돼요 (예: 날짜가 더 잘 보이게)", "aria-label": r.id + " 메모",
        oninput: function () { var v = memo.value.replace(/\s*\n+\s*/g, " "); if (v !== memo.value) memo.value = v; st.memo = v; paintChips(); B.changed(); } });
      memo.value = st.memo || "";
      var chipEls = EXAMPLES.map(function (t) {
        return HX.el("button", { type: "button", class: "hx-it-ex", text: t, onclick: function () {
          var ps = parts(st.memo), i = ps.indexOf(t);
          if (i >= 0) ps.splice(i, 1); else ps.push(t);
          st.memo = ps.join(", "); memo.value = st.memo; paintChips(); B.changed();
        } });
      });
      var change = HX.el("div", { class: "hx-it-change" }, [HX.el("div", { class: "hx-it-sub", text: "어떻게 바꿀까요? 눌러서 고르거나 직접 적어 주세요" }), HX.el("div", { class: "hx-it-exs" }, chipEls), memo]);
      body.appendChild(change);
      function paintChips() { var ps = parts(st.memo); chipEls.forEach(function (c) { c.setAttribute("aria-pressed", ps.indexOf(c.textContent) >= 0 ? "true" : "false"); }); }
      function paint() {
        cbtns.forEach(function (b, i) { b.setAttribute("aria-pressed", CHOICES[i][0] === st.v ? "true" : "false"); });
        change.style.display = st.v === "change" ? "" : "none"; paintChips();
      }
      paint();
      var pv = HX.btn("이전 번호", { icon: HX.icon("#i-chevron-left"), onclick: function () { B.stepRegion(-1); } });
      var nx = HX.btn("다음 번호", { onclick: function () { B.stepRegion(1); } }); nx.appendChild(HX.icon("#i-chevron-right"));
      body.appendChild(HX.el("div", { class: "hx-bd-pn" }, [pv, HX.el("span", { class: "hx-bar-spacer" }), nx]));
      body.appendChild(HX.btn("이 화면 전체 보기", { cls: "hx-it-all", icon: HX.icon("#i-layout-grid"), onclick: function () { B.select(s.slug, null, { inst: B.sel.inst }); } }));
    }

    P.render = function (force) {
      var sel = B.sel, sig = [sel.slug, sel.key, sel.inst].join("|");
      if (!force && sig === P.sig) { P.paintRowSel(); return; }
      P.sig = sig; P.slug = sel.slug; body.innerHTML = ""; summary = null; P.rows = {};
      var s = sel.slug && HX.bySlug[sel.slug], r = s && sel.key ? s.regions.filter(function (x) { return x.key === sel.key; })[0] : null;
      if (r) item(s, r); else if (s) screen(s); else home();
      body.scrollTop = 0; P.paintRowSel();
    };
    P.paintRowSel = function () { Object.keys(P.rows).forEach(function (k) { P.rows[k].classList.toggle("hx-sel", k === B.sel.key); }); };
    P.rowHover = function (key, on) { if (P.rows[key]) P.rows[key].classList.toggle("hx-on", on); };
    P.scrollToRow = function (key) { var r = P.rows[key]; if (r) r.scrollIntoView({ block: "nearest" }); };
    HX.on("board-change", paintSummary);
    return P;
  };
})();
