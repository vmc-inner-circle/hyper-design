/* Model — 연결선 색(순수). 프리셋 4개 + 랜덤 · 쌍마다 직접 고른 색 · 앱 강조색 ±30° 건너뛰기 · 같은 대상 = 같은 색.
   colourOf(prefs, src, group, accent) : 쌍 하나의 색. 우선순위 custom['src>dst'] > 프리셋(강조색 근처는 건너뜀)[group.k]
   randomSet(rng)                      : 색상각을 고르게 나눈 8색(시작 각은 rng), 채도 .34–.46 · 밝기 .42–.50
   DOM 없음. */
(function () {
'use strict';
var HD = globalThis.HD = globalThis.HD || {};
var PRESETS = {
  calm:   {name: '차분 (기본)', c: ['#C46F3E', '#B08F33', '#4F9563', '#3C918B', '#5B7DB5', '#8466AE', '#B85B83', '#B9514F']},
  vivid:  {name: '선명', c: ['#F97316', '#16A34A', '#9333EA', '#DB2777', '#0D9488', '#CA8A04', '#2563EB', '#DC2626']},
  pastel: {name: '파스텔', c: ['#E39A6E', '#7DBB8C', '#AD95D6', '#E08CAB', '#78BDB6', '#D2B565', '#8FA8DB', '#DB8A87']},
  deep:   {name: '진하게', c: ['#9A3412', '#166534', '#5B21B6', '#9D174D', '#115E59', '#854D0E', '#1E3A8A', '#991B1B']}
};
var ORDER = ['calm', 'vivid', 'pastel', 'deep'], GREY = '#6B7280', N_RAND = 8;
var HEX = /^#[0-9a-f]{6}$/i;

function isHex(x) { return typeof x === 'string' && HEX.test(x); }
function hsl2hex(h, s, l) {
  var f = function (n) { var k = (n + h / 30) % 12, a = s * Math.min(l, 1 - l), c = l - a * Math.max(-1, Math.min(k - 3, 9 - k, 1)); return ('0' + Math.round(c * 255).toString(16)).slice(-2); };
  return ('#' + f(0) + f(8) + f(4)).toUpperCase();
}
function randomSet(rng) {
  rng = rng || Math.random;
  var o = rng() * 360, out = [];
  for (var i = 0; i < N_RAND; i++) out.push(hsl2hex((o + i * 360 / N_RAND) % 360, 0.34 + rng() * 0.12, 0.42 + rng() * 0.08));
  return out;
}
function hueOf(hx) {
  var m = /^#?([0-9a-f]{6})$/i.exec(String(hx || '').trim()); if (!m) return null;
  var v = parseInt(m[1], 16), r = (v >> 16 & 255) / 255, g = (v >> 8 & 255) / 255, b = (v & 255) / 255;
  var mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn;
  if (d < 0.08) return null;
  var h = mx === r ? ((g - b) / d) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4;
  return (h * 60 + 360) % 360;
}
function hueGap(a, b) { var d = Math.abs(a - b) % 360; return d > 180 ? 360 - d : d; }
// 프리셋 색 목록(random 은 prefs.rand, 없으면 차분)
function paletteOf(prefs) {
  var p = prefs || {};
  if (p.preset === 'random' && Array.isArray(p.rand) && p.rand.length && p.rand.every(isHex)) return p.rand.slice();
  return (PRESETS[p.preset] || PRESETS.calm).c.slice();
}
// 강조색 ±30° 를 뺀 목록(다 빠지면 원래 목록)
function skipAccent(pal, accent) {
  var ah = hueOf(accent);
  var out = pal.filter(function (c) { var h = hueOf(c); return ah == null || h == null || hueGap(h, ah) >= 30; });
  return out.length ? out : pal.slice();
}
// group = {to, k}(k = 대상 그룹 순서 → 같은 대상은 같은 k)
function colourOf(prefs, src, group, accent) {
  var c = prefs && prefs.custom && prefs.custom[src + '>' + group.to];
  if (isHex(c)) return c;
  var pal = skipAccent(paletteOf(prefs), accent);
  return pal[(group.k || 0) % pal.length];
}
// 쌍마다 고르는 색판: 모든 프리셋 색(겹침 없이) + 회색
function swatches() {
  var out = [];
  ORDER.forEach(function (k) { PRESETS[k].c.forEach(function (c) { if (out.indexOf(c) < 0) out.push(c); }); });
  out.push(GREY);
  return out;
}

HD.lineStyle = {PRESETS: PRESETS, ORDER: ORDER, GREY: GREY, isHex: isHex, hsl2hex: hsl2hex, randomSet: randomSet, hueOf: hueOf,
            paletteOf: paletteOf, skipAccent: skipAccent, colourOf: colourOf, swatches: swatches};
})();
