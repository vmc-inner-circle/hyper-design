/* 90-boot.js — data-mode를 보고 진입. */
(function () {
  "use strict";
  var HX = window.HX;
  function boot() {
    var app = document.getElementById("hx-app") || document.body.appendChild(document.createElement("div"));
    var mode = HX.mode;
    try {
      if (mode === "board" && HX.board && HX.board.stage === "concept" && HX.board.startConcept) HX.board.startConcept(app);
      else if (mode === "board" && HX.board) HX.board.start(app);
      else if (HX.final) HX.final.start(app);
      else app.textContent = "렌더러를 찾을 수 없어요 (mode=" + mode + ")";
    } catch (e) {
      console.error("[hx] 부팅 실패", e);
      app.textContent = "화면을 그리는 중 오류가 났어요: " + (e && e.message ? e.message : e);
    }
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot); else boot();
})();
