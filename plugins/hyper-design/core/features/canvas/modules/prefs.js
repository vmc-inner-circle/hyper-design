/* ViewModel — 캔버스 설정 하나(버전 붙음). 저장소 함수는 밖에서 받는다(getItem(key) / setItem(key, value)).
   키 hd-canvas-prefs = {v:2, arrows:bool, preset:'calm'|'vivid'|'pastel'|'deep'|'random', rand:[hex…]|null,
                         custom:{'src>dst':'#hex'}, width:1..6(.5 단위), motion:bool}
   v1({v:1, arrows, sat}) 은 arrows 만 옮기고 sat 는 버린다. 더 예전 키(hd-arrows)도 읽어 옮긴다(예전 키엔 더 쓰지 않음).
   잘못된 값은 기본값으로. 메모(hd-notes:*)·팔레트(hd-palette) 키는 여기서 다루지 않는다. */
(function () {
'use strict';
var HD = globalThis.HD = globalThis.HD || {};
var KEY = 'hd-canvas-prefs', V = 2, PRESET_KEYS = ['calm', 'vivid', 'pastel', 'deep', 'random'];
var HEX = /^#[0-9a-f]{6}$/i;

function defaults() { return {v: V, arrows: true, preset: 'calm', rand: null, custom: {}, width: 2.5, motion: true}; }
function safe(get, k) { try { return get(k); } catch (e) { return null; } }
function okRand(r) { return Array.isArray(r) && r.length >= 6 && r.length <= 8 && r.every(function (c) { return typeof c === 'string' && HEX.test(c); }); }
function okWidth(w) { return typeof w === 'number' && isFinite(w) && w >= 1 && w <= 6; }
function cleanCustom(c) {
  var out = {};
  if (c && typeof c === 'object' && !Array.isArray(c)) Object.keys(c).forEach(function (k) {
    if (k.indexOf('>') > 0 && typeof c[k] === 'string' && HEX.test(c[k])) out[k] = c[k];
  });
  return out;
}
// 아무 객체 → 올바른 v2 설정(모르는 값·틀린 값은 기본값)
function normalize(o) {
  var p = defaults();
  if (!o || typeof o !== 'object') return p;
  if (typeof o.arrows === 'boolean') p.arrows = o.arrows;
  if (okRand(o.rand)) p.rand = o.rand.slice();
  if (PRESET_KEYS.indexOf(o.preset) >= 0 && (o.preset !== 'random' || p.rand)) p.preset = o.preset;
  p.custom = cleanCustom(o.custom);
  if (okWidth(o.width)) p.width = Math.round(o.width * 2) / 2;
  if (typeof o.motion === 'boolean') p.motion = o.motion;
  return p;
}

function load(getItem) {
  var raw = getItem ? safe(getItem, KEY) : null, o = null;
  if (raw != null) { try { o = JSON.parse(raw); } catch (e) { o = null; } }
  if (o && typeof o === 'object' && o.v === V) return normalize(o);
  if (o && typeof o === 'object' && o.v === 1) return normalize({arrows: o.arrows});   // v1 → v2(sat 버림)
  var p = defaults();
  if (!getItem) return p;                          // 예전 키 옮기기
  p.arrows = safe(getItem, 'hd-arrows') !== '0';
  return p;
}

function save(prefs, setItem) {
  var o = normalize(prefs);
  try { setItem(KEY, JSON.stringify(o)); } catch (e) {}
  return o;
}

HD.prefs = {KEY: KEY, defaults: defaults, normalize: normalize, load: load, save: save};
})();
