/* 원클릭 팔레트 교체 — 화면은 <link id="tokens" href="tokens.css"> 하나만 바꾼다.
   캔버스가 postMessage({type:'hd-palette', slug})를 보내거나, 마지막 선택(localStorage)·?p= 를 따른다.
   누르는 것: data-stay="안내 문구"는 화면 위쪽에 그 문구를 잠깐 띄우고(그 자리에서 바뀜),
   data-back은 앱바의 뒤로 링크로(없으면 단독으로 열린 창에서만 history.back — 캔버스 안에서는 캔버스를 떠나지 않게). */
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
  addEventListener('message', function (e) { if (e.data && e.data.type === 'hd-palette') apply(e.data.slug); });

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
})();
