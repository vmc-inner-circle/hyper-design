/* Model — 연결 보기 이름 자리(순수 기하).
   placeTags : 선 위 태그 — 그룹마다 자기 차선(가로 구간) 위, 다른 태그·다른 그룹 세로선과 안 겹치는 자리. */
(function () {
'use strict';
var HD = globalThis.HD = globalThis.HD || {};
var FRACS = [0.5, 0.35, 0.65, 0.2, 0.8, 0.1, 0.9], MARGIN = 4, INSET = 10, VHALF = 3;

function hit(a, b) { return a.x0 < b.x1 && b.x0 < a.x1 && a.y0 < b.y1 && b.y0 < a.y1; }

/* tags = [{k, segs:[{a, b, y}], w, h}] (차선 구간들 — 앞의 것부터 시도, 태그 크기 w×h) · verticals = [{k, x, y0, y1}]
   → [{k, x, y, box:{x0,x1,y0,y1}, fallback}] (x,y = 태그 가운데). 구간마다 50% → 35 → 65 → 20 → 80 → 10 → 90%, 끝에서 10px 안쪽,
   태그+4px 상자가 다른 태그·다른 그룹 세로선에 닿지 않는 첫 자리. 어디에도 없으면 첫 구간 50%.
   (다른 줄로 가는 그룹은 출발 줄 차선이 짧을 수 있어 대상 줄 차선을 두 번째 구간으로 준다.) */
function placeTags(tags, verticals) {
  var placed = [], vs = (verticals || []).map(function (v) {
    return {k: v.k, x0: v.x - VHALF, x1: v.x + VHALF, y0: Math.min(v.y0, v.y1), y1: Math.max(v.y0, v.y1)};
  });
  return (tags || []).map(function (t) {
    var w = t.w + 2 * MARGIN, h = t.h + 2 * MARGIN, segs = t.segs || [{a: t.a, b: t.b, y: t.y}], best = null, at = null;
    var boxAt = function (x, y) { return {x0: x - w / 2, x1: x + w / 2, y0: y - h / 2, y1: y + h / 2}; };
    for (var s = 0; s < segs.length && !best; s++) {
      var a = Math.min(segs[s].a, segs[s].b), b = Math.max(segs[s].a, segs[s].b), y = segs[s].y;
      for (var i = 0; i < FRACS.length && !best; i++) {
        var x = a + (b - a) * FRACS[i];
        if (x - t.w / 2 < a + INSET || x + t.w / 2 > b - INSET) continue;
        var R = boxAt(x, y);
        if (placed.some(function (q) { return hit(q, R); })) continue;
        if (vs.some(function (q) { return q.k !== t.k && hit(q, R); })) continue;
        best = R; at = y;
      }
    }
    var fb = !best;
    if (fb) { at = segs[0].y; best = boxAt((segs[0].a + segs[0].b) / 2, at); }
    placed.push(best);
    return {k: t.k, x: (best.x0 + best.x1) / 2, y: at, box: best, fallback: fb};
  });
}

HD.labels = {placeTags: placeTags};
})();
