/* 원클릭 팔레트 교체 — 화면은 <link id="tokens" href="tokens.css"> 하나만 바꾼다.
   캔버스가 postMessage({type:'hd-palette', slug})를 보내거나, 마지막 선택(localStorage)·?p= 를 따른다.
   누르는 것: data-stay="안내 문구"는 화면 위쪽에 그 문구를 잠깐 띄우고(그 자리에서 바뀜),
   data-back은 앱바의 뒤로 링크로(없으면 단독으로 열린 창에서만 history.back — 캔버스 안에서는 캔버스를 떠나지 않게).
   의견 고르기 — 캔버스가 postMessage({type:'hd-pick', on:true})를 보내면 마우스 올린 요소에 외곽선, 누르면 기본 동작을 막고
   parent 로 {type:'hd-picked', screen, path, text}를 보낸다(file:// 에서는 부모가 iframe 안을 직접 못 보므로 반드시 메시지). */
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
  var timer;
  function toast(msg) {
    var t = document.querySelector('.toast');
    if (!t) { t = document.createElement('div'); t.className = 'toast'; t.setAttribute('role', 'status'); document.body.appendChild(t); }
    t.textContent = msg; t.classList.add('is-on');
    clearTimeout(timer); timer = setTimeout(function () { t.classList.remove('is-on'); }, 2400);
  }
  document.addEventListener('click', function (e) {
    var el = e.target.closest && e.target.closest('[data-stay], [data-back]'); if (!el) return;
    e.preventDefault();
    if (el.hasAttribute('data-stay')) { var m = el.getAttribute('data-stay'); if (m) toast(m); return; }
    var back = document.querySelector('.appbar-btn[href]');
    if (back && back !== el) location.href = back.getAttribute('href');
    else if (window.top === window) history.back();
  });

  /* ---------- 의견 고르기 ---------- */
  var picking = false, hover = null, style = null;
  var screen = decodeURIComponent((location.pathname.split('/').pop() || '').replace(/\.html?$/, ''));
  function seg(el) {
    var t = el.tagName.toLowerCase(), c = (el.classList && el.classList[0]) || '';
    var s = t + (c ? '.' + (window.CSS && CSS.escape ? CSS.escape(c) : c) : '');
    var p = el.parentElement; if (!p) return s;
    var same = Array.prototype.filter.call(p.children, function (x) { return x.tagName === el.tagName; });
    return same.length > 1 ? s + ':nth-of-type(' + (same.indexOf(el) + 1) + ')' : s;
  }
  function cssPath(el) {                           // 문서에서 하나로 집히는 가장 짧은 경로(최대 6칸)
    var parts = [];
    for (var n = el; n && n.nodeType === 1 && n !== document.body && parts.length < 6; n = n.parentElement) {
      if (n.id) { parts.unshift('#' + (window.CSS && CSS.escape ? CSS.escape(n.id) : n.id)); break; }
      parts.unshift(seg(n));
      try { if (document.querySelectorAll(parts.join(' > ')).length === 1) break; } catch (e) {}
    }
    return parts.join(' > ');
  }
  function label(el) {
    var t = (el.innerText || el.getAttribute('aria-label') || el.getAttribute('alt') || el.getAttribute('title') || '');
    return t.replace(/\s+/g, ' ').trim().slice(0, 30);
  }
  function mark(el, on) { if (el && el.nodeType === 1) { if (on) el.setAttribute('data-hd-hover', ''); else el.removeAttribute('data-hd-hover'); } }
  function onOver(e) { if (hover !== e.target) { mark(hover, false); hover = e.target; mark(hover, true); } }
  function onOut() { mark(hover, false); hover = null; }
  function onBlock(e) { e.preventDefault(); e.stopPropagation(); }
  function onClick(e) {
    e.preventDefault(); e.stopPropagation();
    var el = e.target; if (!el || el.nodeType !== 1) return;
    var old = document.querySelector('[data-hd-picked]'); if (old) old.removeAttribute('data-hd-picked');
    el.setAttribute('data-hd-picked', '');
    try { parent.postMessage({type: 'hd-picked', screen: screen, path: cssPath(el), text: label(el)}, '*'); } catch (err) {}
  }
  function setPick(on) {
    var p0 = document.querySelector('[data-hd-picked]'); if (p0) p0.removeAttribute('data-hd-picked');   // 다시 받으면 고른 표시만 지운다
    if (on === picking) return; picking = on;
    if (on && !style) {
      style = document.createElement('style');
      style.textContent = '[data-hd-hover]{outline:2px solid #2563eb!important;outline-offset:-2px;cursor:crosshair!important}' +
        '[data-hd-picked]{outline:3px solid #f59e0b!important;outline-offset:-3px}';
    }
    var m = on ? 'addEventListener' : 'removeEventListener';
    document[m]('mouseover', onOver, true); document[m]('mouseout', onOut, true);
    document[m]('click', onClick, true); document[m]('submit', onBlock, true);
    if (on) document.head.appendChild(style);
    else { onOut(); if (style && style.parentNode) style.parentNode.removeChild(style); }
  }

  addEventListener('message', function (e) {
    var d = e.data; if (!d) return;
    if (d.type === 'hd-palette') apply(d.slug);
    else if (d.type === 'hd-pick') setPick(!!d.on);
  });
})();
