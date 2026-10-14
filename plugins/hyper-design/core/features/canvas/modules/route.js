/* Model — 연결선 모양(순수 기하). 둥근 직각선: 가로·세로만, 꺾이는 곳마다 원호(Q) 하나. */
(function () {
'use strict';
var HD = globalThis.HD = globalThis.HD || {};
var RADIUS = 18;                                   // 꺾이는 곳 둥근 반지름(짧은 쪽 선의 절반까지 줄어듦)

// 꺾은선 → 꺾는 곳마다 원호(Q) 하나. 반지름은 짧은 쪽 선의 절반까지.
function roundPath(pts, r) {
  var p = [];
  pts.forEach(function (q) {
    var a = [Math.round(q[0] * 10) / 10, Math.round(q[1] * 10) / 10], l = p[p.length - 1];
    if (l && l[0] === a[0] && l[1] === a[1]) return;
    var l2 = p[p.length - 2];
    if (l2 && ((l2[0] === l[0] && l[0] === a[0]) || (l2[1] === l[1] && l[1] === a[1]))) p.pop();   // 한 줄 위의 가운데 점은 뺀다
    p.push(a);
  });
  var f = function (v) { return String(Math.round(v * 10) / 10); };
  var d = 'M' + f(p[0][0]) + ',' + f(p[0][1]);
  for (var i = 1; i < p.length - 1; i++) {
    var a = p[i - 1], c = p[i], n = p[i + 1];
    var l1 = Math.hypot(c[0] - a[0], c[1] - a[1]), l2 = Math.hypot(n[0] - c[0], n[1] - c[1]);
    var rr = Math.min(r, l1 / 2, l2 / 2);
    if (rr < 0.5) { d += ' L' + f(c[0]) + ',' + f(c[1]); continue; }
    var s = [c[0] - (c[0] - a[0]) / l1 * rr, c[1] - (c[1] - a[1]) / l1 * rr];
    var e = [c[0] + (n[0] - c[0]) / l2 * rr, c[1] + (n[1] - c[1]) / l2 * rr];
    d += ' L' + f(s[0]) + ',' + f(s[1]) + ' Q' + f(c[0]) + ',' + f(c[1]) + ' ' + f(e[0]) + ',' + f(e[1]);
  }
  var z = p[p.length - 1];
  return d + ' L' + f(z[0]) + ',' + f(z[1]);
}
/* 둥근 직각 연결선(가로·세로만, 되돌아가는 고리 없음). 끝은 늘 아래로 대상 카드 위 가운데에 들어간다.
   세로선은 카드 사이 틈(gutter)·줄 위 통로·왼쪽 통로에서만 — 카드 상자 안을 세로로 지나지 않는다.
   src.dir 'up'            : 카드 위에서 위로 → 줄 위 통로(lift+apex) → 가로 → 아래로 (꺾임 2)
   src.dir 'up' + o.laneX  : 다른 줄 — 위로 → 왼쪽 통로로 가로 → 통로 따라 세로 → 대상 줄 위에서 가로 → 아래로 (꺾임 4)
   src.dir 'right'         : 출발 카드 오른쪽 가장자리에서 가로로 틈(o.gx)까지 → 틈 따라 세로 → 대상 줄 위 통로 → 가로 → 아래로 (꺾임 3) */
function routeCurve(src, dst, o) {
  o = o || {};
  var r = o.r || RADIUS, lift = o.lift == null ? 44 : o.lift, apex = o.apex || 0, k = o.k || 0;
  var sx = src.x, sy = src.y, tx = dst.x, ty = dst.y, pts;
  if (src.dir === 'up' && o.laneX != null) {
    var sg = sy - lift - apex, tg = ty - lift - apex;
    pts = [[sx, sy], [sx, sg], [o.laneX, sg], [o.laneX, tg], [tx, tg], [tx, ty]];
  } else if (src.dir === 'up') {
    var top = Math.min(sy, ty) - lift - apex;
    pts = [[sx, sy], [sx, top], [tx, top], [tx, ty]];
  } else {
    var gx = o.gx == null ? sx + 18 + 14 * k : o.gx, lane = ty - lift - apex;
    pts = [[sx, sy], [gx, sy], [gx, lane], [tx, lane], [tx, ty]];
  }
  return roundPath(pts, r);
}

/* ---------- 연결 보기 색 링크 경로(계획) — 옆면 출발 · 바깥 통로 · 줄 위 차선 · 대상 카드 위 가운데
   모든 값은 판(stage) 단위. 카드는 판에서 배율 1(375×812)로 그려지므로 px 상수는 그대로 쓴다(판 확대는 transform 이 한다). */
var LINK_R = 16, GUT0 = 14, GUT_STEP = 12, LANE_LIFT = 46, LANE_STEP = 30, LANE_PAD = 30, CAP_GAP = 12, CAP_LIFT = 24;
var XLANE0 = 56, XLANE_STEP = 22;                 // 왼쪽 통로: left − 56 − 22·k (회색 갈래 화살표와 같은 자리)

// 요소 가운데(카드 왼쪽에서 cx)가 카드 폭의 30% 보다 왼쪽이면 L, 70% 보다 오른쪽이면 R, 아니면 대상 쪽(facing)
function sideOf(cx, w, facing) { return cx < 0.3 * w ? 'L' : cx > 0.7 * w ? 'R' : facing; }

// 줄 위 차선 i 의 y: 카드 위 46 + 30·i. 줄 제목(cap)에 닿으면 그 차선부터는 줄 제목 위로.
// 줄 제목과 카드 사이 자리를 먼저 다 쓴다: 30px 간격 자리 → 그 사이 15px 자리(세로선이 줄 제목 글자를 지나지 않게). 그래도 모자라면 줄 제목 위로.
function laneY(rowTop, cap, i) {
  var y = rowTop - LANE_LIFT - LANE_STEP * i;
  if (!cap) return y;
  var top = rowTop - LANE_LIFT, lim = cap.bottom + CAP_GAP, slots = [], k;
  for (k = 0; top - LANE_STEP * k >= lim; k++) slots.push(top - LANE_STEP * k);
  for (k = 0; top - LANE_STEP * k - LANE_STEP / 2 >= lim; k++) slots.push(top - LANE_STEP * k - LANE_STEP / 2);
  if (i < slots.length) return slots[i];
  return cap.top - CAP_LIFT - LANE_STEP * (i - slots.length);
}

// 출발 가로선(요소 → 바깥 통로)이 다른 그룹의 출발 가로선과 같은 높이로 겹치면(탭 막대처럼 나란한 요소) 요소 높이 안에서 8px씩 비켜 선다
function stubY(stubs, k, side, x0, x1, y, h) {
  var lo = Math.min(x0, x1), hi = Math.max(x0, x1), lim = Math.max(0, h / 2 - 3), cand = [0];
  for (var d = 8; d <= lim; d += 8) cand.push(-d, d);
  var free = function (yy) { return !stubs.some(function (t) { return t.k !== k && Math.abs(t.y - yy) < 4 && t.lo < hi && lo < t.hi; }); };
  var yy = y;
  for (var i = 0; i < cand.length; i++) if (free(y + cand[i])) { yy = y + cand[i]; break; }
  stubs.push({k: k, y: yy, lo: lo, hi: hi});
  return yy;
}

/* plan(o) — o = {src:{x,y,w,h}, rowTop, cap:{top,bottom}|null, left(왼쪽 통로 기준 x),
                  groups:[{k, to, members:[{x,y,w,h}](판 좌표), target:{x,y,w,h,rowTop,cap,row}, sameRow}]}
   → 그룹마다 {k, to, side, dir, rev, gx, lane, ly, tx(차선 끝), laneSeg:{a,b,y}, laneSegs(태그 후보 구간: 출발 줄 차선[, 대상 줄 차선]), pts:[[x,y]…](멤버마다), d:[…], verticals:[{x,y0,y1}]} */
function plan(o) {
  var S = o.src, cx = S.x + S.w / 2, left = o.left || 0, xk = 0, trow = {};
  var gs = (o.groups || []).map(function (g) {
    var T = g.target, tcx = T.x + T.w / 2, same = g.sameRow !== false;
    var dir = same ? (tcx < cx ? 'L' : 'R') : 'L';                     // 다른 줄은 늘 왼쪽 통로로
    var sides = g.members.map(function (m) { return sideOf(m.x + m.w / 2 - S.x, S.w, dir); });
    var side = sides.every(function (s) { return s === sides[0]; }) ? sides[0] : dir;
    var edge = side === 'L' ? S.x : S.x + S.w;
    var r = {k: g.k, to: g.to, side: side, dir: dir, rev: side !== dir, edge: edge, same: same, T: T, tcx: tcx, members: g.members};
    if (!same) {
      r.xk = xk++; r.laneX = left - XLANE0 - XLANE_STEP * r.xk;                  // 잠정(바깥 통로 정한 뒤 다시)
      var rk = String(T.row != null ? T.row : T.rowTop);
      r.tlane = trow[rk] = trow[rk] == null ? 0 : trow[rk] + 1;
      r.tly = laneY(T.rowTop, T.cap, r.tlane);
    }
    r.tx = same ? tcx : r.laneX;
    r.span = Math.abs(r.tx - edge);
    return r;
  });
  var order = function (a, b) { return (a.rev - b.rev) || (a.span - b.span) || (a.k - b.k); };
  ['L', 'R'].forEach(function (s) {                 // 가까운 대상일수록 바깥 통로, 반대 방향은 가장 안쪽
    var list = gs.filter(function (g) { return g.side === s; }).sort(order);
    list.forEach(function (g, i) { var off = GUT0 + (list.length - 1 - i) * GUT_STEP; g.gx = s === 'L' ? g.edge - off : g.edge + off; });
  });
  // 왼쪽 통로는 이 카드의 왼쪽 바깥 통로들보다 더 왼쪽(줄 맨 앞 카드면 통로가 겹치지 않게 밀어낸다)
  var minG = Math.min.apply(null, [left - XLANE0].concat(gs.filter(function (g) { return g.side === 'L'; }).map(function (g) { return g.gx - XLANE_STEP; })));
  gs.forEach(function (g) { if (!g.same) { g.laneX = minG - XLANE_STEP * g.xk; g.tx = g.laneX; } });
  var placed = [];                                  // 차선: 가로 구간이 겹치면 다른 차선(반대 방향은 겹치는 것들 위로)
  gs.slice().sort(order).forEach(function (g) {
    var lo = Math.min(g.gx, g.tx) - LANE_PAD, hi = Math.max(g.gx, g.tx) + LANE_PAD;
    var ov = placed.filter(function (p) { return p.lo < hi && lo < p.hi; }), lane = 0;
    if (g.rev) lane = ov.reduce(function (mx, p) { return Math.max(mx, p.lane + 1); }, 0);
    else while (ov.some(function (p) { return p.lane === lane; })) lane++;
    g.lane = lane; g.ly = laneY(o.rowTop, o.cap, lane);
    placed.push({lo: lo, hi: hi, lane: lane});
  });
  var stubs = [];
  return gs.map(function (g) {
    var ty = g.T.y - 10, ys = [];
    var pts = g.members.map(function (m) {
      var sx = g.side === 'L' ? m.x : m.x + m.w;
      var sy = stubY(stubs, g.k, g.side, sx, g.gx, Math.max(S.y + 8, Math.min(S.y + S.h - 8, m.y + m.h / 2)), m.h);
      ys.push(sy);
      var p = [[sx, sy], [g.gx, sy], [g.gx, g.ly], [g.tx, g.ly]];
      if (g.same) p.push([g.tx, ty]);
      else p.push([g.laneX, g.tly], [g.tcx, g.tly], [g.tcx, ty]);
      return p;
    });
    var v = [{x: g.gx, y0: g.ly, y1: Math.max.apply(null, ys)}];
    if (g.same) v.push({x: g.tx, y0: g.ly, y1: ty});
    else v.push({x: g.laneX, y0: Math.min(g.ly, g.tly), y1: Math.max(g.ly, g.tly)}, {x: g.tcx, y0: g.tly, y1: ty});
    return {k: g.k, to: g.to, side: g.side, dir: g.dir, rev: g.rev, same: g.same, gx: g.gx, lane: g.lane, ly: g.ly, tx: g.tx,
            laneX: g.laneX, tly: g.tly, laneSeg: {a: Math.min(g.gx, g.tx), b: Math.max(g.gx, g.tx), y: g.ly},
            laneSegs: [{a: Math.min(g.gx, g.tx), b: Math.max(g.gx, g.tx), y: g.ly}].concat(g.same ? [] : [{a: Math.min(g.laneX, g.tcx), b: Math.max(g.laneX, g.tcx), y: g.tly}]),
            pts: pts, d: pts.map(function (p) { return roundPath(p, LINK_R); }), verticals: v};
  });
}

HD.route = {RADIUS: RADIUS, roundPath: roundPath, routeCurve: routeCurve, sideOf: sideOf, laneY: laneY, plan: plan, LINK_R: LINK_R};
})();
