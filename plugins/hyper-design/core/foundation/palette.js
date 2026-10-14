/* 원클릭 팔레트 교체 — 화면은 <link id="tokens" href="tokens.css"> 하나만 바꾼다.
   캔버스가 postMessage({type:'hd-palette', slug})를 보내거나, 마지막 선택(localStorage)·?p= 를 따른다.
   요소 고르기(캔버스 크게 보기): {type:'hd-pick', on} 을 받으면 마우스 올린 요소에 테두리를 그리고
   {type:'hd-hover', rect} / 클릭 시 {type:'hd-picked', screen, path, text, rect, add} 를 부모에게 보낸다(add = Shift 로 여러 개 고르기).
   연결 보기: {type:'hd-links', on:true} 를 받으면 다른 화면으로 가는 링크 목록을
   {type:'hd-links', screen, accent, docHeight, links:[{to, path, text, rect}]} 로 답하고(docHeight = 화면 전체 높이),
   {type:'hd-links-paint', items:[{path, color, n}]} 로 그 요소들에 색 테두리·번호를 그린다(items:[] 이면 지움).
   한 요소에 쌍이 여럿이면 테두리를 3px 간격 동심으로 겹친다.
   어디로 가나(Ctrl/Cmd+클릭): 링크 요소를 Ctrl/Cmd+클릭하면 이동하지 않고 {type:'hd-link-go', screen, to, path, rect} 를 보낸다.
   캔버스가 {type:'hd-link-at', x, y} 를 보내면 그 자리의 링크로 같은 답을 보낸다(링크가 없으면 to:null). 그냥 클릭은 그대로. */
(function () {
  var KEY = 'hd-palette';
  function apply(slug) {
    var l = document.getElementById('tokens'); if (!l || !slug) return;
    var base = l.getAttribute('data-base') || l.getAttribute('href'); l.setAttribute('data-base', base);
    l.setAttribute('href', base.replace(/tokens(-[^/]*)?\.css$/, 'tokens-' + slug + '.css'));
  }
  var s = new URLSearchParams(location.search).get('p');
  try { s = s || localStorage.getItem(KEY); } catch (e) {}
  if (s) apply(s);

  /* ---------- 요소 고르기 ---------- */
  var picking = false, box = null, last = null;
  function send(msg) { try { if (window.parent && window.parent !== window) window.parent.postMessage(msg, '*'); } catch (e) {} }
  function rectOf(el) { var r = el.getBoundingClientRect(); return {x: Math.round(r.left), y: Math.round(r.top), w: Math.round(r.width), h: Math.round(r.height)}; }
  function cssEsc(v) { return window.CSS && CSS.escape ? CSS.escape(v) : String(v).replace(/[^\w-]/g, '\\$&'); }
  function unique(sel, el) { try { var m = document.querySelectorAll(sel); return m.length === 1 && m[0] === el; } catch (e) { return false; } }
  function pathOf(el) {
    var segs = [], n = el;
    while (n && n.nodeType === 1 && n !== document.body && n !== document.documentElement) {
      var tag = n.tagName.toLowerCase();
      if (n.id) { segs.unshift('#' + cssEsc(n.id)); break; }
      var reg = n.getAttribute('data-region');
      if (reg != null) { segs.unshift(tag + '[data-region="' + reg.replace(/"/g, '\\"') + '"]'); break; }
      var cls = (n.getAttribute('class') || '').trim().split(/\s+/)[0];
      var i = 1, p = n.previousElementSibling;
      for (; p; p = p.previousElementSibling) if (p.tagName === n.tagName) i++;
      segs.unshift(tag + (cls ? '.' + cssEsc(cls) : '') + ':nth-of-type(' + i + ')');
      n = n.parentElement;
    }
    if (!segs.length) return 'body';
    for (var k = 1; k <= segs.length; k++) {           // 끝에서부터 가장 짧은 유일한 경로
      var sel = segs.slice(segs.length - k).join(' > ');
      if (unique(sel, el)) return sel;
    }
    var full = segs.join(' > ');
    return segs[0].charAt(0) === '#' || segs[0].indexOf('[data-region') > 0 ? full : 'body > ' + full;
  }
  function textOf(el) {
    var t = el.innerText || el.value || el.getAttribute('aria-label') || el.getAttribute('alt') || '';
    return String(t).replace(/\s+/g, ' ').trim().slice(0, 60);
  }
  function screenId() {
    var f = decodeURIComponent(location.pathname.split('/').pop() || '');
    return f.replace(/\.html?$/i, '');
  }
  function showBox(el) {
    if (!box) {
      box = document.createElement('div');
      box.setAttribute('data-hd-pick', '');
      box.style.cssText = 'position:fixed;z-index:2147483647;pointer-events:none;border:2px solid #2563eb;background:rgba(37,99,235,.10);border-radius:4px;display:none';
      document.documentElement.appendChild(box);
    }
    var r = rectOf(el);
    box.style.left = r.x + 'px'; box.style.top = r.y + 'px'; box.style.width = r.w + 'px'; box.style.height = r.h + 'px';
    box.style.display = 'block';
    return r;
  }
  function target(e) { var t = e.target; return t && t.nodeType === 1 && t !== box ? t : null; }
  document.addEventListener('mousemove', function (e) {
    if (!picking) return;
    var t = target(e); if (!t || t === last) return;
    last = t; send({type: 'hd-hover', rect: showBox(t)});
  }, true);
  function block(e) { if (!picking) return; e.preventDefault(); e.stopPropagation(); if (e.stopImmediatePropagation) e.stopImmediatePropagation(); }
  ['mousedown', 'mouseup', 'pointerdown', 'pointerup', 'submit', 'dblclick'].forEach(function (ev) { document.addEventListener(ev, block, true); });
  document.addEventListener('click', function (e) {
    if (!picking) return;
    block(e);
    var t = target(e); if (!t) return;
    send({type: 'hd-picked', screen: screenId(), path: pathOf(t), text: textOf(t), rect: showBox(t), add: !!e.shiftKey});
  }, true);

  /* ---------- 연결 보기: 다른 화면으로 가는 링크 ---------- */
  function hex(v) {
    v = String(v || '').trim(); if (!v) return '';
    var t = document.createElement('i'); t.style.color = v; document.documentElement.appendChild(t);
    var c = getComputedStyle(t).color; t.remove();
    var m = c.match(/\d+(\.\d+)?/g); if (!m || m.length < 3) return '';
    return '#' + m.slice(0, 3).map(function (x) { return ('0' + Math.round(+x).toString(16)).slice(-2); }).join('');
  }
  function accent() {
    var cs = getComputedStyle(document.documentElement);
    var names = ['--c-brand', '--c-accent', '--c-primary', '--primary', '--accent'];
    for (var i = 0; i < names.length; i++) { var v = hex(cs.getPropertyValue(names[i])); if (v) return v; }
    return '';
  }
  function hrefOf(el) {
    var h = el.getAttribute('href') || el.getAttribute('data-href');
    if (!h) { var m = (el.getAttribute('onclick') || '').match(/['"]([^'"]+\.html?)(?:[?#][^'"]*)?['"]/i); h = m && m[1]; }
    return h;
  }
  var LINK_SEL = 'a[href], [data-href], [onclick]';
  function toOf(el) {                                 // 같은 폴더의 다른 화면으로 가는 링크면 그 화면 id
    var h = hrefOf(el); if (!h || /^(#|javascript:|mailto:|tel:)/i.test(h)) return null;
    var here = location.href.split(/[?#]/)[0], dir = here.replace(/[^\/]*$/, ''), u;
    try { u = new URL(h, here).href.split(/[?#]/)[0]; } catch (e) { return null; }
    if (u.indexOf(dir) !== 0 || !/\.html?$/i.test(u)) return null;
    var rest = decodeURIComponent(u.slice(dir.length)); if (rest.indexOf('/') >= 0) return null;   // 같은 폴더의 화면만
    var to = rest.replace(/\.html?$/i, ''); return !to || to === screenId() ? null : to;
  }
  function links() {
    var res = [];
    document.querySelectorAll(LINK_SEL).forEach(function (el) {
      var to = toOf(el); if (!to) return;
      res.push({to: to, path: pathOf(el), text: textOf(el).slice(0, 40), rect: rectOf(el)});
    });
    return res;
  }
  function linkAt(el) {                               // el 또는 그 조상 중 화면 링크
    for (var n = el; n && n.nodeType === 1; n = n.parentElement) { if (n.matches && n.matches(LINK_SEL) && toOf(n)) return n; }
    return null;
  }
  function sendGo(el) {
    send(el ? {type: 'hd-link-go', screen: screenId(), to: toOf(el), path: pathOf(el), rect: rectOf(el)} : {type: 'hd-link-go', screen: screenId(), to: null});
  }
  document.addEventListener('click', function (e) {    // Ctrl/Cmd+클릭: 이동 대신 '어디로 가나'
    if (picking || !(e.ctrlKey || e.metaKey) || !window.parent || window.parent === window) return;
    var el = linkAt(e.target); if (!el) return;
    e.preventDefault(); e.stopPropagation();
    sendGo(el);
  }, true);
  function docHeight() {
    var de = document.documentElement, b = document.body;
    return Math.max(de.scrollHeight, de.offsetHeight, b ? b.scrollHeight : 0, b ? b.offsetHeight : 0);
  }
  var paints = [];
  function paint(items) {
    paints.forEach(function (n) { n.remove(); }); paints = [];
    var seen = {};
    (items || []).forEach(function (it) {
      var el; try { el = document.querySelector(it.path); } catch (e) { el = null; }
      if (!el) return;
      var o = 3 + 6 * (seen[it.path] || 0);            // 같은 요소의 두 번째 쌍부터 바깥으로(3px 틈)
      seen[it.path] = (seen[it.path] || 0) + 1;
      var r = el.getBoundingClientRect(), d = document.createElement('div');
      d.setAttribute('data-hd-links', '');
      d.style.cssText = 'position:absolute;z-index:2147483646;pointer-events:none;border-radius:6px;box-sizing:border-box;' +
        'left:' + (r.left + scrollX - o) + 'px;top:' + (r.top + scrollY - o) + 'px;width:' + (r.width + 2 * o) + 'px;height:' + (r.height + 2 * o) + 'px;' +
        'border:3px solid ' + it.color + ';box-shadow:0 0 0 2px rgba(255,255,255,.85)';
      if (it.n) {
        var b = document.createElement('span');
        b.textContent = it.n <= 20 ? String.fromCharCode(0x245F + it.n) : '(' + it.n + ')';
        b.style.cssText = 'position:absolute;right:-10px;top:-12px;min-width:22px;height:22px;padding:0 3px;border-radius:999px;background:' + it.color +
          ';color:#fff;font:700 14px/22px sans-serif;text-align:center';
        d.appendChild(b);
      }
      document.documentElement.appendChild(d); paints.push(d);
    });
  }

  addEventListener('message', function (e) {
    var d = e.data; if (!d) return;
    if (d.type === 'hd-palette') apply(d.slug);
    else if (d.type === 'hd-links') { if (d.on) send({type: 'hd-links', screen: screenId(), accent: accent(), docHeight: docHeight(), links: links()}); else paint([]); }
    else if (d.type === 'hd-links-paint') paint(d.items);
    else if (d.type === 'hd-link-at') sendGo(linkAt(document.elementFromPoint(+d.x || 0, +d.y || 0)));
    else if (d.type === 'hd-pick') {
      picking = !!d.on; last = null;
      if (!picking && box) box.style.display = 'none';
      document.documentElement.style.cursor = picking ? 'crosshair' : '';
    }
  });
})();
