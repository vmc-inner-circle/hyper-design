/* 07-story.js — 전체 흐름(카드 목록). 캔버스를 처음 열면 보이는 화면.
   시나리오 하나 = 흐름 하나 = 카드 한 장: 번호 · 제목 문장 · 누구의 흐름 · 첫 화면 미리보기 · 화면 순서.
   카드를 누르면(따라가 보기) 그 흐름을 두 장씩 넘겨 본다. 빨간 번호(피드백)는 목록에서는 보이지 않는다.
   05-map.js의 HX.buildMap 끝에서 HX.buildStory(view)로 붙는다. */
(function () {
  "use strict";
  var HX = window.HX;

  var STATE_LABEL = { "first-run": "처음 켰을 때", empty: "데이터 없을 때", input: "입력할 때" };
  HX.stateLabel = function (st) { return STATE_LABEL[st] || ""; };

  // 이 이야기에 나오는 사람들: 역할이 바뀌는 순서대로 ("자녀 → 부모님")
  function whoOf(R) {
    var seq = [];
    R.insts.forEach(function (it) {
      var s = HX.bySlug[it.slug], lab = s && s.role ? HX.roleLabel(s.role).replace(/\(.*\)/, "") : "가족 모두";
      if (seq[seq.length - 1] !== lab) seq.push(lab);
    });
    if (!seq.length) seq.push(R.flow && R.flow.role ? HX.roleLabel(R.flow.role).replace(/\(.*\)/, "") : "가족 모두");
    return seq.map(function (x) { return x === "부모" ? "부모님" : x; }).join(" → ");
  }

  HX.buildStory = function (view) {
    var I = view._int, vp = I.vp, rows = view.rows, built = false;
    var story = HX.el("div", { class: "hx-story", role: "list", "aria-label": "전체 흐름" });
    var grid = HX.el("div", { class: "hx-story-grid" });
    story.appendChild(HX.el("div", { class: "hx-story-intro" }, [
      HX.el("b", { text: "이 서비스는 이렇게 써요" }),
      HX.el("span", { text: "흐름을 하나 골라 누르면 화면을 순서대로 따라가 볼 수 있어요." })]));
    story.appendChild(grid);
    vp.insertBefore(story, I.chipBar || null);
    // 목록 안에서는 캔버스 드래그·휠 대신 보통 스크롤
    story.addEventListener("pointerdown", function (e) { e.stopPropagation(); });
    story.addEventListener("wheel", function (e) { e.stopPropagation(); }, { passive: true });

    function build() {
      if (built) return; built = true;
      rows.forEach(function (R, ri) {
        if (!R.insts.length) return;
        var first = HX.bySlug[R.insts[0].slug];
        var title = R.kind === "other" ? "흐름에 안 나오는 화면" : (R.flow.name || R.key);
        var stTag = first && first.state ? HX.el("span", { class: "hx-tag hx-state", text: HX.stateLabel(first.state) }) : null;
        var thumb = HX.el("div", { class: "hx-story-thumb" });
        // 화면 순서: 같은 화면이 연달아 나오면 한 번만
        var names = [];
        R.insts.forEach(function (it) { var n = HX.bySlug[it.slug].name; if (names[names.length - 1] !== n) names.push(n); });
        var card = HX.el("button", { type: "button", class: "hx-story-card", role: "listitem", dataset: { row: R.key },
          "aria-label": (R.n ? "흐름 " + R.n + ", " : "") + title,
          onclick: function () { view.setScope(ri, { fit: true, user: true }); } }, [
          HX.el("div", { class: "hx-story-top" }, [
            R.n ? HX.el("span", { class: "hx-story-n", text: String(R.n) }) : null,
            HX.el("span", { class: "hx-tag hx-role", text: whoOf(R) }), stTag]),
          HX.el("div", { class: "hx-story-title", text: title }),
          thumb,
          HX.el("ol", { class: "hx-story-path" }, names.map(function (n) { return HX.el("li", { text: n }); })),
          HX.el("div", { class: "hx-story-foot" }, [
            HX.el("span", { text: "화면 " + R.insts.length + "개" }),
            HX.el("span", { class: "hx-story-go" }, ["따라가 보기", HX.icon("#i-chevron-right")])])]);
        grid.appendChild(card);
        HX.mountFrame(R.insts[0].slug, thumb, { fit: "width", badges: false });
      });
    }
    view.story = {
      el: story,
      show: function () { build(); story.scrollTop = 0; HX.relayout(); },
      isOn: function () { return vp.classList.contains("hx-mode-story"); }
    };
  };
})();
