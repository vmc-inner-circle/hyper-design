/* Model — Ctrl+클릭 "어디로 가나" 카메라 이동 계획(순수). 시간·배율·이동량은 숫자로만 받는다(CSS 변수는 View 가 읽는다).
   plan(from, to, view, o) → 키프레임 [{t, z, tx, ty}] (t = ms, 늘 커짐)
     from = {x, y}            출발 요소 가운데(판 좌표)
     to   = {x, y, w, h}      대상 카드 상자(판 좌표)
     view = {w, h, z, tx, ty} 판(pane) 크기 · 지금 배율 · 이동
     o    = {centre, glide, margin, reduced, zMin}
   1) 지금 배율로 출발 요소를 가운데(centre ms) → 2) 대상 카드 가운데로(glide ms). 대상이 안 들어가면 그만큼만 축소.
   reduced(움직임 줄이기 · 애니메이션 끄기) → 끝 상태 하나.
   at(keys, t, ease, view) → {z, tx, ty}: 구간마다 ease(0..1) 를 걸고, 판 가운데 점과 배율을 보간(직선으로 미끄러짐).
   bezier(x1, y1, x2, y2) / parseEase(css) → (p ∈ 0..1) → 0..1 */
(function () {
'use strict';
var HD = globalThis.HD = globalThis.HD || {};

function centred(view, x, y, z) { return {z: z, tx: view.w / 2 - x * z, ty: view.h / 2 - y * z}; }

function plan(from, to, view, o) {
  o = o || {};
  var m = o.margin == null ? 24 : o.margin, z = view.z;
  var fz = Math.min((view.w - 2 * m) / to.w, (view.h - 2 * m) / to.h);
  var z2 = Math.min(z, fz);
  if (o.zMin != null) z2 = Math.max(o.zMin, z2);
  var end = centred(view, to.x + to.w / 2, to.y + to.h / 2, z2);
  if (o.reduced) return [{t: 0, z: end.z, tx: end.tx, ty: end.ty}];
  var c = Math.max(1, +o.centre || 250), g = Math.max(1, +o.glide || 600);
  var mid = centred(view, from.x, from.y, z);
  return [{t: 0, z: z, tx: view.tx, ty: view.ty},
          {t: c, z: mid.z, tx: mid.tx, ty: mid.ty},
          {t: c + g, z: end.z, tx: end.tx, ty: end.ty}];
}

function at(keys, t, ease, view) {
  var last = keys[keys.length - 1];
  if (keys.length === 1 || t >= last.t) return {z: last.z, tx: last.tx, ty: last.ty};
  if (t <= keys[0].t) return {z: keys[0].z, tx: keys[0].tx, ty: keys[0].ty};
  var i = 1;
  while (i < keys.length - 1 && keys[i].t <= t) i++;
  var a = keys[i - 1], b = keys[i], p = (t - a.t) / (b.t - a.t), e = ease ? ease(p) : p;
  var ca = {x: (view.w / 2 - a.tx) / a.z, y: (view.h / 2 - a.ty) / a.z}, cb = {x: (view.w / 2 - b.tx) / b.z, y: (view.h / 2 - b.ty) / b.z};
  var z = a.z + (b.z - a.z) * e;
  return centred(view, ca.x + (cb.x - ca.x) * e, ca.y + (cb.y - ca.y) * e, z);
}

function bezier(x1, y1, x2, y2) {
  var cx = 3 * x1, bx = 3 * (x2 - x1) - cx, ax = 1 - cx - bx, cy = 3 * y1, by = 3 * (y2 - y1) - cy, ay = 1 - cy - by;
  var X = function (t) { return ((ax * t + bx) * t + cx) * t; }, Y = function (t) { return ((ay * t + by) * t + cy) * t; };
  var dX = function (t) { return (3 * ax * t + 2 * bx) * t + cx; };
  return function (p) {
    if (p <= 0) return 0; if (p >= 1) return 1;
    var t = p, i;
    for (i = 0; i < 8; i++) { var e = X(t) - p, d = dX(t); if (Math.abs(e) < 1e-6) return Y(t); if (Math.abs(d) < 1e-6) break; t -= e / d; }
    var lo = 0, hi = 1; t = p;
    for (i = 0; i < 30; i++) { var v = X(t); if (Math.abs(v - p) < 1e-6) break; if (v < p) lo = t; else hi = t; t = (lo + hi) / 2; }
    return Y(t);
  };
}
var KEYWORDS = {linear: [0, 0, 1, 1], ease: [0.25, 0.1, 0.25, 1], 'ease-in': [0.42, 0, 1, 1], 'ease-out': [0, 0, 0.58, 1], 'ease-in-out': [0.42, 0, 0.58, 1]};
function parseEase(s) {
  s = String(s || '').trim();
  var m = /^cubic-bezier\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*,\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)$/.exec(s);
  var a = m ? [+m[1], +m[2], +m[3], +m[4]] : KEYWORDS[s] || [0.22, 1, 0.36, 1];
  return bezier(a[0], a[1], a[2], a[3]);
}
function ms(s, dflt) {                              // '250ms' / '0.25s' → 250
  s = String(s || '').trim(); var v = parseFloat(s);
  if (!isFinite(v)) return dflt;
  return /ms$/.test(s) ? v : /s$/.test(s) ? v * 1000 : v;
}

HD.camera = {plan: plan, at: at, bezier: bezier, parseEase: parseEase, ms: ms};
})();
