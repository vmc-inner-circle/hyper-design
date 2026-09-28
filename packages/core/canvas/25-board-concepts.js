/* 25-board-concepts.js — 시안 고르기. 디자이너가 고객에게 안을 보여주듯:
   1턴 보드(meta.stage = "concept")는 이 화면 하나뿐이다(B.startConcept). 시안을 고른 뒤 2턴에 그 시안으로 전체 화면·흐름을 만든다.
   살펴본 레퍼런스(HX.data.references) → 시안 5개를(이름 · 이유 · 특징 · 참고한 곳 · 핵심 화면 2~3장) → "이 안으로 할게요".
   지금 화면들(사용 흐름·화면 디자인)은 HX.meta.concept 시안으로 만든 것. 다른 시안의 화면은 build.js가 "<시안 id>~<slug>" 섹션으로 싣는다.
   시안을 고르면 그 시안의 분위기(look)도 함께 바뀐다(화면 느낌에서 다시 바꿀 수 있다). 복사 글 첫 줄: "시안 <id>(이름) · 테마 …" */
(function () {
  "use strict";
  var HX = window.HX, B = HX.board, doc = document;
  if (!B) return;
  var SHELL = { sidebar: "왼쪽 메뉴", top: "위쪽 탭 메뉴", rail: "아이콘 메뉴" };

  // 지금 화면들의 시안은 원래 화면(slug) 그대로, 다른 시안은 build.js가 실은 "<시안 id>~<slug>" 섹션
  function frameKey(c, slug) { return B.stage !== "concept" && c.id === B.mainConcept ? slug : c.id + "~" + slug; }

  // 화면을 누르면 크게 (시안 화면은 보드 데이터에 없는 화면이라 전용 확대 창)
  function zoom(c, slug, title) {
    var close = HX.btn("", { cls: "hx-icon-btn", aria: "닫기", title: "닫기 (Esc)", icon: HX.icon("#i-x"), onclick: function () { done(); } });
    var box = HX.el("div", { class: "hx-cc-zoom-frame", "data-theme": c.look, "data-swatch": (B.look(c.look).swatches[0] || {}).id || "", "data-type": B.state.type });
    var m = HX.el("div", { class: "hx-modal hx-app" }, [HX.el("div", { class: "hx-modal-backdrop", onclick: function () { done(); } }),
      HX.el("div", { class: "hx-modal-panel", role: "dialog", "aria-modal": "true", "aria-label": title }, [
        HX.el("div", { class: "hx-modal-head" }, [HX.el("span", { class: "hx-cc-id", text: "시안 " + c.id.toUpperCase() }), HX.el("h2", { text: title }), HX.el("span", { class: "hx-bar-spacer" }), close]),
        HX.el("div", { class: "hx-modal-body hx-cc-zoom" }, box)])]);
    function key(e) { if (e.key === "Escape") { e.preventDefault(); done(); } }
    function done() { m.remove(); doc.removeEventListener("keydown", key); doc.body.style.overflow = ""; }
    doc.body.appendChild(m); doc.addEventListener("keydown", key); doc.body.style.overflow = "hidden";
    HX.mountFrame(frameKey(c, slug), box, { scale: 1, fullHeight: true, badges: false });
    close.focus();
  }

  B.buildConcepts = function () {
    var C = B.concepts, main = B.mainConcept = (B.concept(HX.meta.concept) || C[0]).id;
    var refs = (HX.data.references || []).filter(function (r) { return r && r.name; });
    var el = HX.el("div", { class: "hx-cc", role: "tabpanel", "aria-label": "시안 비교" });
    el.appendChild(HX.el("div", { class: "hx-cc-intro" }, [
      HX.el("b", { text: "이런 방향으로 만들어 봤어요" }),
      HX.el("span", { text: (refs.length ? "비슷한 서비스 " + refs.length + "곳을 살펴보고 " : "") + "화면 구성이 다른 안 " + C.length + "개를 만들었어요. 마음에 드는 안 하나를 골라 주세요. 다른 안에서 가져오고 싶은 점은 그 안의 칸에 적어 주세요. 고른 안으로 모든 화면과 사용 흐름을 만들어요." })]));

    if (refs.length) {
      el.appendChild(HX.el("section", { class: "hx-cc-refs", "aria-label": "살펴본 서비스" }, [
        HX.el("div", { class: "hx-cc-h", text: "살펴본 서비스" }),
        HX.el("div", { class: "hx-cc-refgrid" }, refs.map(function (r) {
          return HX.el("div", { class: "hx-cc-ref" }, [
            HX.el("div", { class: "hx-cc-ref-top" }, [
              r.url ? HX.el("a", { href: r.url, target: "_blank", rel: "noopener", text: r.name }) : HX.el("b", { text: r.name }),
              r.kind ? HX.el("span", { class: "hx-tag", text: r.kind }) : null]),
            r.borrow ? HX.el("div", { class: "hx-cc-ref-borrow", text: r.borrow }) : null]);
        }))]));
    }

    var cols = HX.el("div", { class: "hx-cc-cols", style: "--hx-cc-n:" + C.length });
    var cards = {};
    C.forEach(function (c) {
      var L = B.look(c.look), isRec = c.id === B.REC.concept;
      var pick = HX.btn("", { cls: "hx-cc-pick", onclick: function () { choose(c.id); } });
      var memo = HX.el("textarea", { class: "hx-ta hx-cc-memo", rows: "2", placeholder: "이 안에서 좋은 점·바꿀 점 (선택) — 예: 달력은 이 안처럼", "aria-label": "시안 " + c.id.toUpperCase() + "에 남길 말",
        oninput: function () { (B.state.cmemo || (B.state.cmemo = {}))[c.id] = memo.value; B.changed(); } });
      memo.value = (B.state.cmemo || {})[c.id] || "";
      var shots = HX.el("div", { class: "hx-cc-shots" });
      var card = HX.el("article", { class: "hx-cc-col", dataset: { concept: c.id } }, [
        HX.el("header", { class: "hx-cc-head" }, [
          HX.el("div", { class: "hx-cc-top" }, [HX.el("span", { class: "hx-cc-id", text: "시안 " + c.id.toUpperCase() }), isRec ? HX.el("span", { class: "hx-tag hx-rec", text: "추천" }) : null,
            B.stage !== "concept" && c.id === main ? HX.el("span", { class: "hx-tag", text: "지금 화면들" }) : null]),
          HX.el("h3", { class: "hx-cc-name", text: c.name }),
          c.why ? HX.el("p", { class: "hx-cc-why", text: c.why }) : null,
          HX.el("ul", { class: "hx-cc-traits" }, [SHELL[c.shell] || null, L && L.name ? "분위기 " + L.name : null].concat(c.traits || []).filter(Boolean).map(function (t) { return HX.el("li", { text: t }); })),
          (c.refs || []).length ? HX.el("div", { class: "hx-cc-from" }, [HX.el("span", { class: "hx-cc-from-h", text: "참고한 곳" })].concat((c.refs || []).map(function (r) {
            return HX.el("div", { class: "hx-cc-from-row" }, [r.url ? HX.el("a", { href: r.url, target: "_blank", rel: "noopener", text: r.name }) : HX.el("b", { text: r.name }), r.borrow ? " — " + r.borrow : ""]);
          }))) : null,
          pick,
          memo]),
        HX.el("div", { class: "hx-cc-right" }, [
          HX.el("div", { class: "hx-cc-shots-h", text: "메인 화면 " + (c.screens || []).length + "장 · 옆으로 넘겨 더 보기 · 화면은 끝까지 보여요 · 누르면 크게" }), shots])]);
      (c.screens || []).forEach(function (slug) {
        var s = HX.bySlug[slug], title = s ? s.name : slug;
        var box = HX.el("div", { class: "hx-cc-shot-frame", "data-theme": c.look, "data-swatch": (L.swatches[0] || {}).id || "", "data-type": B.state.type });
        var shot = HX.el("button", { type: "button", class: "hx-cc-shot", title: "크게 보기", onclick: function () { zoom(c, slug, title); } }, [HX.el("span", { class: "hx-cc-shot-name", text: title }), box]);
        shots.appendChild(shot);
        HX.mountFrame(frameKey(c, slug), box, { fit: "width", fullHeight: true, badges: false });   // 내용 끝까지 — 화면 안에서 스크롤하지 않게
      });
      cards[c.id] = { el: card, pick: pick }; cols.appendChild(card);
    });
    el.appendChild(cols);
    el.addEventListener("wheel", function (e) { e.stopPropagation(); }, { passive: true });

    function choose(id) {
      var c = B.concept(id); if (!c) return;
      B.state.concept = c.id;
      if (c.look && !B.isLocked("theme") && B.looks.some(function (l) { return l.id === c.look; })) { B.state.theme = c.look; B.state.accent = B.fixSwatch(c.look, ""); }
      B.applyTheme();   // → board-change
      HX.toast("시안 " + c.id.toUpperCase() + "을 골랐어요. 의견 보내기에 함께 담겨요.");
    }
    function paint() {
      Object.keys(cards).forEach(function (id) {
        var on = B.state.concept === id, k = cards[id];
        k.el.classList.toggle("hx-on", on);
        k.pick.innerHTML = ""; k.pick.appendChild(HX.icon(on ? "#i-circle-check" : "#i-circle"));
        k.pick.appendChild(doc.createTextNode(on ? "이 안으로 할게요 (고름)" : "이 안으로 할게요"));
        k.pick.setAttribute("aria-pressed", on ? "true" : "false");
      });
    }
    HX.on("board-change", paint);
    paint();
    return el;
  };

  /* 1턴 보드: 시안 고르기만 — 상단바(제목 · 의견 보내기) + 시안 목록 */
  B.startConcept = function (app) {
    app.classList.add("hx-app"); app.classList.add("hx-bd"); app.classList.add("hx-tab-concept");
    var copyBtn = HX.btn("", { cls: "hx-primary hx-bd-copy", icon: HX.icon("#i-send"), title: "무엇이 전달되는지 확인하고 복사해요", onclick: function () { B.openSend(); } });
    var copyLabel = HX.el("span"); copyBtn.appendChild(copyLabel);
    app.appendChild(HX.el("div", { class: "hx-bar hx-bd-bar" }, [
      HX.el("div", { class: "hx-bar-title", title: HX.meta.title || "" }, [HX.meta.title || HX.meta.project || "", HX.el("small", { text: "시안 고르기" })]),
      HX.el("span", { class: "hx-bar-spacer" }), copyBtn]));
    app.appendChild(B.buildConcepts());
    function paintCopy() {
      var n = B.diffCount(), C = B.concept(B.state.concept);
      copyLabel.textContent = "시안 " + (C ? C.id.toUpperCase() : "") + "(으)로 보내기" + (n ? " · " + n + "개" : "");
    }
    HX.on("board-change", paintCopy); paintCopy();
  };
})();
