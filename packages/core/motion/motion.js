/* motion.js — 움직임 재현(피그마로는 못 그리는 것 — HTML이라 가능한 것). 완성본 페이지와 보드가 함께 쓴다.
   window.HXMotion(app, { overlay, items: [{ type, target, ms, level, note }] }, demo) → { stop() }
   - 완성본 화면별 페이지: window.HX_MOTION이 있으면 그 화면에서 바로 재현(누르는 동작은 실제로 눌러서).
     기본: 화면 들어오기(#back이면 반대 방향) · 뜨는 창 올라오기 · 누름 반응 · 고르는 버튼(칩·나눔 버튼·탭·날짜 칸)이 실제로 골라짐.
   - 보드(demo): 화면에 마우스를 올리면 그 자리에서 재생, 떼면 원래대로. 누르는 동작(길게 누르기·끌어서 순서 바꾸기)은 보여 주기만.
   type: hold(길게 누르기) · breathe(숨 쉬듯 깜빡임) · dim(몇 초 뒤 어두워짐) · countup(숫자 올라가기) · stagger(차례로 나타나기)
         reorder(길게 눌러 끌어 순서 바꾸기) · carousel(자동으로 넘어가는 띠) · play(재생 막대)
   target = 영역 key(data-region) 또는 버튼 key(data-trigger). 화면에 안내 UI는 두지 않는다 — 설명은 보드의 ⓘ 규칙 카드('움직임' 묶음). */
(function () {
  "use strict";
  var doc = document;
  var reduce = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  var toastEl = null, tt = 0;
  function toast(msg) {
    if (!toastEl) { toastEl = doc.createElement("div"); toastEl.className = "hx-mo-toast"; doc.body.appendChild(toastEl); }
    toastEl.textContent = msg; toastEl.hidden = false; clearTimeout(tt); tt = setTimeout(function () { toastEl.hidden = true; }, 1800);
  }
  // 옆으로 넘치는 줄: 끝을 흐리게(더 있다는 표시)
  function swipers(root) {
    return [].filter.call(root.querySelectorAll("*"), function (x) {
      if (x.scrollWidth <= x.clientWidth + 4 || x.clientWidth < 40) return false;
      var o = getComputedStyle(x).overflowX; return o === "auto" || o === "scroll";
    });
  }
  function markSwipe(root) { swipers(root).forEach(function (x) { x.classList.add("mo-fade"); }); }
  window.HXMarkSwipe = markSwipe;
  function HXFrameH() { return (doc.documentElement.getAttribute("data-platform") === "mobile") ? 844 : 800; }
  // 조사: 받침에 맞춰 '을/를' · '(으)로' — "'운동했어요'를", "'측정 중'으로"
  function batchim(w) { var c = String(w || "").trim().replace(/['"’”)\]]+$/, ""), k = c.charCodeAt(c.length - 1) - 0xAC00; return k >= 0 && k <= 11171 ? k % 28 : -1; }
  function eul(w) { return "'" + w + "'" + (batchim(w) > 0 ? "을" : "를"); }
  function ro(w) { var b = batchim(w); return "'" + w + "'" + (b > 0 && b !== 8 ? "으로" : "로"); }
  window.HXJosa = { eul: eul, ro: ro };
  function restart(el, cls) { el.classList.remove(cls); void el.offsetWidth; el.classList.add(cls); }
  // 앱 디자인의 안내 상자(.toast) — 완료 success · 오류 danger · 주의 warning · 안내 info
  var TONE_ICON = { success: "circle-check", danger: "circle-alert", warning: "triangle-alert", info: "info" };
  function appToast(app, msg, tone, sub) {
    tone = TONE_ICON[tone] ? tone : "success";
    var old = app.querySelector(".toast.mo-toast"); if (old) old.remove();
    var t = doc.createElement("div"); t.className = "toast toast-" + tone + " mo-toast"; t.setAttribute("role", "status");
    t.innerHTML = '<svg class="icon" aria-hidden="true"><use href="#i-' + TONE_ICON[tone] + '"/></svg><div class="toast-body"><span class="toast-title"></span>' + (sub ? '<span class="toast-desc"></span>' : "") + "</div>";
    t.querySelector(".toast-title").textContent = msg; if (sub) t.querySelector(".toast-desc").textContent = sub;
    app.appendChild(t); return t;
  }
  // 앱 밖으로 나가는 버튼: 실제 앱에서는 휴대폰 설정 등이 열린다 — 어디로 가는지 카드로
  function appOut(app, path, label) {
    var old = app.querySelector(".mo-out"); if (old) old.remove();
    var c = doc.createElement("div"); c.className = "mo-out";
    c.innerHTML = '<div class="mo-out-card"><span class="mo-out-k">앱 밖으로 나가요</span><b></b><p></p><button type="button" class="btn btn-secondary">돌아오기</button></div>';
    c.querySelector("b").textContent = path;
    c.querySelector("p").textContent = (label ? eul(label) + " 누르면 " : "") + "실제 앱에서는 이 화면이 열려요";
    c.querySelector("button").addEventListener("click", function (e) { e.stopPropagation(); c.remove(); });
    app.appendChild(c); return c;
  }
  window.HXAppOut = appOut;
  // 보드의 상태 화면: 원래 화면 위에 안내 상자나 '앱 밖' 카드를 얹어 둔다(움직이지 않는 한 장)
  window.HXStatic = function (app, x) {
    var el = x.out ? appOut(app, x.out, x.label) : appToast(app, x.text, x.tone, x.sub); el.classList.add("mo-static");
    if (x.cap) window.HXCaption(app, x.cap);
    return el;
  };
  // 상태 화면 위쪽에 고정하는 '언제' 말풍선 — 화면만 봐도 언제 나오는지 알게 (사용자: "에러는 언제 나오는지 설명이 필요")
  window.HXCaption = function (app, text) {
    var c = doc.createElement("div"); c.className = "mo-cap mo-cap-when"; c.textContent = text; app.appendChild(c); return c;
  };
  window.HXAppToast = function (msg, tone) {
    var app = doc.querySelector(".app"); if (!app) return;
    var t = appToast(app, msg, tone); clearTimeout(window.__hxAppToastT); window.__hxAppToastT = setTimeout(function () { t.remove(); }, 2400);
  };

  // 화면 안 스크롤(.content 등)에 가려진 요소면 그 위치까지 부드럽게 내린다 → 기다릴 ms(가려지지 않았으면 0). el이 없으면 맨 위로.
  function revealIn(app, el, smooth) {
    if (!el) { [].forEach.call(app.querySelectorAll("*"), function (x) { if (x.scrollTop > 0 && x.scrollHeight > x.clientHeight + 4) x.scrollTo({ top: 0, behavior: smooth ? "smooth" : "auto" }); }); return 0; }
    var box = null;
    for (var x = el.parentElement; x && x !== app.parentElement; x = x.parentElement) {
      if (x.scrollHeight > x.clientHeight + 4) { var o = getComputedStyle(x).overflowY; if (o === "auto" || o === "scroll") { box = x; break; } }
    }
    if (!box) return 0;
    var a = box.getBoundingClientRect(), r = el.getBoundingClientRect(), k = (a.height / box.clientHeight) || 1;
    if (r.top >= a.top - 2 && r.bottom <= a.bottom + 2) return 0;
    box.scrollTo({ top: box.scrollTop + (r.top + r.height / 2 - (a.top + a.height / 2)) / k, behavior: smooth ? "smooth" : "auto" });
    return 750;
  }
  window.HXReveal = revealIn;

  window.HXMotion = function (app, M, demo) {
    M = M || {};
    var O = demo && typeof demo === "object" ? demo : {}, once = !!O.once;
    function spd() { return O.speed ? O.speed() || 1 : 1; }
    var undo = [], timers = [], alive = true;
    function later(fn, ms) { var t = setTimeout(function () { if (alive) fn(); }, ms / spd()); timers.push(t); return t; }
    function every(fn, ms) { var t = setInterval(function () { if (alive) fn(); }, ms); timers.push(t); return t; }
    function q(t) { return t ? app.querySelector('[data-region="' + t + '"]') || app.querySelector('[data-trigger="' + t + '"]') : null; }
    function styleOf(el) { var keep = el.getAttribute("style"); undo.push(function () { if (keep === null) el.removeAttribute("style"); else el.setAttribute("style", keep); }); }

    // ---- 보여 주기(보드): 실제 휴대폰을 쓰듯 손가락(데스크톱은 커서)이 동작을 하나씩 — 튜토리얼처럼 ----
    // demo가 객체 { once, done, say, finger, speed, skip }이면 '흐름 재생'용: 동작을 빠짐없이 한 번씩만 하고 done()을 부른다.
    function tutorial() {
      var mobile = (doc.documentElement.getAttribute("data-platform") || "") === "mobile";
      var items = M.items || [];
      // 뜨는 창 화면이면 창 안의 것만 (뒤 화면의 칩·스위치를 누르지 않게)
      var scope = app.querySelector(".modal-backdrop .modal") || app;
      function all(arr, n) { return once ? arr : arr.slice(0, n); }   // 흐름 재생은 하나도 빼지 않는다 (사용자: "하나도 빼먹지 말고 다 넣어라")
      ["breathe", "countup", "stagger", "carousel"].forEach(function (t) { items.filter(function (i) { return i.type === t; }).forEach(function (i) { RUN[t](i); }); });
      if (M.overlay) { var bd0 = app.querySelector(".modal-backdrop"); if (bd0) { restart(bd0, "mo-in"); undo.push(function () { bd0.classList.remove("mo-in"); }); } }
      markSwipe(app);
      var fg = O.finger || doc.createElement("div"), cap = doc.createElement("div");
      if (!O.finger) { fg.className = "mo-finger" + (mobile ? "" : " mo-finger-desk"); fg.hidden = true; app.appendChild(fg); undo.push(function () { fg.remove(); }); }
      cap.className = "mo-cap"; cap.hidden = true;
      if (!O.say) { app.appendChild(cap); undo.push(function () { cap.remove(); }); }
      function sc() { var r = app.getBoundingClientRect(); return (r.width / app.offsetWidth) || 1; }
      function center(el, fx, fy) { var a = app.getBoundingClientRect(), r = el.getBoundingClientRect(), k = sc(); return { x: (r.left - a.left + r.width * (fx == null ? 0.5 : fx)) / k, y: (r.top - a.top + r.height * (fy == null ? 0.5 : fy)) / k }; }
      function moveTo(p, ms) { ms = ms / spd(); fg.hidden = false; fg.style.transition = "left " + ms + "ms cubic-bezier(.2,.8,.2,1), top " + ms + "ms cubic-bezier(.2,.8,.2,1), transform .15s ease"; fg.style.left = p.x + "px"; fg.style.top = p.y + "px"; }
      function down(on) { fg.classList.toggle("down", !!on); }
      function say(t) { if (O.say) { if (t) O.say(t); return; } cap.textContent = t || ""; cap.hidden = !t; }
      function byLabel(label) { return [].filter.call(scope.querySelectorAll("button, a"), function (b) { return (b.textContent || "").replace(/\s+/g, " ").trim() === label; })[0] || null; }
      // 화면 안 스크롤에 가려진 요소면 먼저 그 위치까지 내려간다
      function add(el, fn) { steps.push(function (done) { var d = revealIn(app, el, true); if (d) { say("아래로 내려가요"); later(function () { fn(done); }, d); } else fn(done); }); }
      function tap(el, caption, after) {
        if (!el) return;
        add(el, function (done) {
          say(caption); moveTo(center(el), 600);
          later(function () { down(true); later(function () { down(false); var t = after ? after() : null; later(function () { if (t) t.remove(); say(""); done(); }, 1900); }, 180); }, 680);
        });
      }
      var steps = [];
      function labelOf(inp) {
        var f = inp.closest(".field"), l = f && f.querySelector(".field-label");
        return l ? l.textContent.replace(/\(선택\)|\*/g, "").trim() : (inp.getAttribute("aria-label") || "입력칸");
      }
      function visible(el) { return el && el.offsetWidth > 0 && el.offsetHeight > 0; }
      // 위아래로 긴 화면: 손가락으로 밀어 올려 아래 내용을 보고 다시 위로
      var vs = [].filter.call(scope.querySelectorAll("*"), function (x) {
        if (x.scrollHeight <= x.clientHeight + 24 || x.clientHeight < 120) return false;
        var o = getComputedStyle(x).overflowY; return o === "auto" || o === "scroll";
      }).sort(function (a, b) { return b.clientHeight - a.clientHeight; });
      all(vs, 1).forEach(function (box) { steps.push(function (done) {
        var top0 = box.scrollTop, max = box.scrollHeight - box.clientHeight, p = center(box, 0.5, 0.78), h = box.getBoundingClientRect().height / sc();
        undo.push(function () { box.scrollTop = top0; });
        say(mobile ? "위로 밀어 올리면 아래 내용이 보여요" : "아래로 내려 더 볼 수 있어요"); moveTo(p, 600);
        later(function () { down(true); moveTo({ x: p.x, y: p.y - h * 0.45 }, 900); box.scrollTo({ top: max, behavior: "smooth" }); }, 700);
        later(function () { down(false); }, 1650);
        later(function () { say(mobile ? "내려 당기면 다시 위로" : "다시 위로"); moveTo({ x: p.x, y: p.y - h * 0.45 }, 400); }, 2700);
        later(function () { down(true); moveTo(p, 900); box.scrollTo({ top: top0, behavior: "smooth" }); }, 3150);
        later(function () { down(false); say(""); done(); }, 4200);
      }); });
      // 고르기: 칩·나눔 버튼에서 아직 안 고른 것을 눌러 골라지는 모습
      all([].filter.call(scope.querySelectorAll(".chip-group, .segmented, .tabs"), visible), 2).forEach(function (grp) {
        var pickEl = [].filter.call(grp.querySelectorAll(".chip, .segmented-item, .tab"), function (c) { return !c.classList.contains("active") && visible(c); })[0];
        if (!pickEl) return;
        add(pickEl, function (done) {
          var kids = [].slice.call(grp.querySelectorAll(".chip, .segmented-item, .tab")), was = kids.map(function (c) { return c.classList.contains("active"); });
          undo.push(function () { kids.forEach(function (c, i) { c.classList.toggle("active", was[i]); }); });
          say(eul(pickEl.textContent.trim()) + " 누르면 골라져요"); moveTo(center(pickEl), 600);
          later(function () { down(true); later(function () { down(false);
            if (pickEl.classList.contains("chip")) pickEl.classList.add("active"); else kids.forEach(function (c) { c.classList.toggle("active", c === pickEl); });
          }, 180); }, 680);
          later(function () { kids.forEach(function (c, i) { c.classList.toggle("active", was[i]); }); say(""); done(); }, 2400);
        });
      });
      // 켜고 끄기: 스위치
      all([].filter.call(scope.querySelectorAll("label.switch"), visible), 1).forEach(function (sw) {
        var box = sw.querySelector("input"); if (!box) return;
        add(sw, function (done) {
          var was = box.checked; undo.push(function () { box.checked = was; });
          say(eul(sw.textContent.trim() || "켜기") + " 켜고 끌 수 있어요"); moveTo(center(box), 600);
          later(function () { down(true); later(function () { down(false); box.checked = !was; }, 180); }, 680);
          later(function () { box.checked = was; say(""); done(); }, 2200);
        });
      });
      // 타이핑: 입력칸을 누르고 한 글자씩 — 글자 수가 올라가고, 넘치면 안내 (흐름 재생은 적은 글자를 남겨 두고 다음 버튼을 누른다)
      all([].filter.call(scope.querySelectorAll("input:not([type=checkbox]):not([type=radio]):not([type=hidden]), textarea"), visible), 2).forEach(function (inp) {
        add(inp, function (done) {
          var old = inp.value, max = +inp.getAttribute("maxlength") || 0, min = +inp.getAttribute("minlength") || 0, name = labelOf(inp);
          var sample = (inp.getAttribute("placeholder") || "").replace(/^예\s*[:：]\s*/, "") || old || "예시로 적어 볼게요";
          var cnt = inp.parentNode.querySelector(".field-count"), made = false;
          if (max && !cnt) { cnt = doc.createElement("span"); cnt.className = "field-count"; inp.insertAdjacentElement("afterend", cnt); made = true; }
          var field = inp.closest(".field");
          function paint() { if (cnt) { cnt.textContent = inp.value.length + "/" + max; cnt.classList.toggle("is-full", inp.value.length >= max); } }
          function restore() { inp.value = old; inp.classList.remove("mo-focus"); if (made && cnt) cnt.remove(); else paint(); if (field) field.classList.remove("is-error"); }
          function finish() { if (once) { inp.value = max ? sample.slice(0, max) : sample; inp.classList.remove("mo-focus"); paint(); if (field) field.classList.remove("is-error"); } else restore(); say(""); done(); }
          undo.push(restore);
          say("'" + name + "'에 적어 볼게요"); moveTo(center(inp, 0.25), 600);
          later(function () { down(true); later(function () { down(false); inp.classList.add("mo-focus"); inp.value = ""; paint(); typeTo(sample, afterTyped); }, 160); }, 680);
          function typeTo(text, then) { var i = text.indexOf(inp.value) === 0 ? inp.value.length : 0; (function step() { if (!alive) return; inp.value = text.slice(0, ++i); paint(); if (i < text.length) later(step, 85); else later(then, 600); })(); }
          function afterTyped() {
            if (max && sample.length < max) {   // 끝까지 적어 보면: 글자 수가 차고 더는 안 써진다
              say(max + "자까지 적을 수 있어요");
              var more = sample + " 그리고 조금 더 길게 적어 보면 어떻게 될까요";
              typeTo(more.slice(0, max), function () {
                var c = (M.cases || []).filter(function (x) { return /자/.test(x.when) && /넘|길/.test(x.when); })[0];
                var t = appToast(app, c ? c.show : max + "자까지 적을 수 있어요", c ? c.tone || "danger" : "warning", c ? c.when : null);
                if (O.note) later(function () { O.note(c ? c.when : max + "자를 넘게 적으면", c ? c.tone || "danger" : "warning", t); }, 350);
                later(function () { if (O.note) O.note(null); t.remove(); if (once) { say("다시 알맞게 적어요"); inp.value = sample; paint(); later(finish, 700); } else finish(); }, 1700);
              });
            } else if (min) {
              say(min + "자보다 짧으면 안내가 떠요"); inp.value = sample.slice(0, Math.max(1, min - 1)); paint();
              if (field) { field.classList.add("is-error"); }
              later(function () { if (once) { if (field) field.classList.remove("is-error"); typeTo(sample, finish); } else finish(); }, 1800);
            } else later(finish, 800);
          }
        });
      });
      items.forEach(function (it) {
        if (it.type === "dim") steps.push(function (done) {
          var layer = doc.createElement("div"); layer.className = "mo-dim"; app.appendChild(layer); undo.push(function () { layer.remove(); });
          say("가만두면 " + Math.round((it.ms || 3000) / 1000) + "초 뒤 화면이 어두워져요");
          later(function () { layer.classList.add("on"); layer.style.opacity = String(it.level || 0.82); }, 500);
          later(function () { say(mobile ? "화면을 톡 치면 잠깐 밝아져요" : "화면을 누르면 잠깐 밝아져요"); moveTo(center(app), 500); }, 2100);
          later(function () { down(true); later(function () { down(false); layer.style.opacity = "0"; }, 180); }, 2700);
          later(function () { layer.remove(); say(""); done(); }, 3900);
        });
        // 길게 누르기: 흐름 재생에서 이 화면의 다음 버튼이면 재생 쪽이 길게 눌러 넘어간다(두 번 하지 않게)
        if (it.type === "hold" && it.target !== O.skip) { var btn = app.querySelector('[data-trigger="' + it.target + '"]'); if (btn) add(btn, function (done) {
          var ms = it.ms || 2000, fill = doc.createElement("span"); fill.className = "mo-hold-fill"; btn.classList.add("mo-hold"); btn.appendChild(fill);
          undo.push(function () { fill.remove(); btn.classList.remove("mo-hold"); });
          say(it.note || "길게 눌러요"); moveTo(center(btn), 600);
          later(function () { down(true); fg.classList.add("hold"); fill.style.transition = "transform " + ms / spd() + "ms linear"; fill.style.transform = "scaleX(1)"; }, 700);
          later(function () { down(false); fg.classList.remove("hold"); }, 700 + ms);
          later(function () { fill.remove(); btn.classList.remove("mo-hold"); say(""); done(); }, 1300 + ms);
        }); }
        if (it.type === "reorder") { var root = q(it.target), list = root && (root.matches("ul, ol") ? root : root.querySelector("ul, ol")); if (list && list.children[1]) add(list.children[1], function (done) {
          var a = list.children[0], b = list.children[1]; styleOf(a); styleOf(b);
          say(it.note || "길게 눌러 끌면 순서가 바뀌어요"); moveTo(center(b, 0.3), 600);
          later(function () { down(true); fg.classList.add("hold"); }, 700);
          later(function () { b.classList.add("mo-lift"); b.style.transition = "transform .2s ease"; b.style.transform = "scale(1.02)"; }, 1100);
          later(function () { var h = a.offsetHeight, p = center(b, 0.3); b.style.transition = a.style.transition = "transform .6s cubic-bezier(.2,.8,.2,1)"; b.style.transform = "translateY(" + -h + "px) scale(1.02)"; a.style.transform = "translateY(" + b.offsetHeight + "px)"; moveTo({ x: p.x, y: p.y - h }, 600); }, 1400);
          later(function () { down(false); fg.classList.remove("hold"); b.classList.remove("mo-lift"); }, 2200);
          later(function () { a.style.transition = b.style.transition = "transform .3s ease"; a.style.transform = b.style.transform = ""; say(""); done(); }, 3200);
        }); }
        if (it.type === "play") { var r2 = q(it.target), pb = r2 && r2.querySelector("button"), bar = r2 && r2.querySelector(".progress-bar"); if (pb && bar) add(pb, function (done) {
          styleOf(bar); say(it.note || "재생을 누르면 들려요"); moveTo(center(pb), 600);
          later(function () { down(true); later(function () { down(false); bar.style.transition = "none"; bar.style.width = "0%"; requestAnimationFrame(function () { requestAnimationFrame(function () { bar.style.transition = "width " + 2600 / spd() + "ms linear"; bar.style.width = "100%"; }); }); }, 180); }, 680);
          later(function () { say(""); done(); }, 3700);
        }); }
      });
      // 옆으로 넘치는 줄(칩·날짜 띠 등): 밀어서 더 보기
      all(swipers(scope), 2).forEach(function (row) { add(row, function (done) {
        var left0 = row.scrollLeft, p = center(row, 0.8);
        say(mobile ? "옆으로 밀어서 더 볼 수 있어요" : "옆으로 넘겨서 더 볼 수 있어요"); moveTo(p, 600);
        later(function () { down(true); moveTo({ x: p.x - 150, y: p.y }, 700); row.scrollTo({ left: left0 + 200, behavior: "smooth" }); }, 700);
        later(function () { down(false); }, 1450);
        later(function () { row.scrollTo({ left: left0, behavior: "smooth" }); say(""); done(); }, 2400);
      }); });
      (M.outs || []).forEach(function (x) { tap(byLabel(x.label), eul(x.label) + " 누르면", function () { return appOut(app, x.text, x.label); }); });
      (M.stays || []).forEach(function (x) { tap(byLabel(x.label), eul(x.label) + " 누르면", function () { return appToast(app, x.text, x.tone); }); });
      // 다음 화면으로: 흐름·갈래 버튼을 누르면 어디로 가는지 (흐름 재생은 지금 단계의 버튼을 빼고 전부 — 그 버튼은 재생 쪽이 눌러 실제로 넘어간다)
      all((M.goes || []).filter(function (g) { return g.trigger !== O.skip; }), 2).forEach(function (g) {
        var el = scope.querySelector('[data-trigger="' + g.trigger + '"]'); if (!visible(el)) return;
        tap(el, (once ? "다른 길 · " : "") + g.action + " → " + ro(g.to) + " 넘어가요", null);
      });
      // 엣지 케이스: 흐름 재생은 조건을 화면 옆 말풍선(O.note)으로, 보드는 위쪽 말풍선으로
      (M.cases || []).forEach(function (c) { steps.push(function (done) {
        // 흐름 재생: 안내가 뜬 뒤 말풍선의 화살표가 그 안내를 가리키고, 읽을 수 있게 1초 더 머문다
        say(O.note ? "이런 경우엔 이 안내가 떠요" : c.when);
        var t = null;
        later(function () { t = appToast(app, c.show, c.tone || "danger"); }, 400);
        if (O.note) later(function () { O.note(c.when, c.tone || "danger", t); }, 750);
        later(function () { if (t) t.remove(); if (O.note) O.note(null); say(""); done(); }, O.note ? 3600 : 2400);
      }); });
      var si = 0;
      function next() {
        if (!alive) return;
        if (once && si >= steps.length) { revealIn(app, null, true); if (O.done) O.done(); return; }
        if (!steps.length) return;
        var st = steps[si++ % steps.length]; st(function () { later(next, 450); });
      }
      if (!O.finger) { fg.style.left = (app.offsetWidth / 2) + "px"; fg.style.top = (Math.min(app.offsetHeight, HXFrameH()) - 90) + "px"; }
      later(next, once ? 200 : 500);
      return { stop: stopAll, count: steps.length };
    }
    var RUN = {
      breathe: function (it) {
        var el = q(it.target); if (!el) return;
        el.classList.add("mo-breathe"); undo.push(function () { el.classList.remove("mo-breathe"); });
      },
      countup: function (it) {
        if (reduce) return;
        var root = q(it.target) || app, ms = it.ms || 900, nodes = [];
        root.querySelectorAll(".big-num, .stat-value").forEach(function (el) {
          var w = doc.createTreeWalker(el, NodeFilter.SHOW_TEXT), n;
          while ((n = w.nextNode())) if (/\d/.test(n.nodeValue)) { nodes.push({ n: n, text: n.nodeValue }); break; }
        });
        undo.push(function () { nodes.forEach(function (x) { x.n.nodeValue = x.text; }); });
        var t0 = performance.now();
        (function tick(now) {
          if (!alive) return;
          var p = Math.min(1, (now - t0) / ms), e = 1 - Math.pow(1 - p, 3);
          nodes.forEach(function (x) { x.n.nodeValue = x.text.replace(/\d+(\.\d+)?/g, function (m, d) { var v = parseFloat(m) * e; return d ? v.toFixed(d.length - 1) : String(Math.round(v)); }); });
          if (p < 1) requestAnimationFrame(tick);
        })(t0);
      },
      stagger: function (it) {
        if (reduce) return;
        var root = q(it.target) || app.querySelector(".content"); if (!root) return;
        [].slice.call(root.children).filter(function (k) { return !k.classList.contains("bottom-cta"); }).forEach(function (k, i) {
          styleOf(k);
          k.style.transition = "none"; k.style.opacity = "0"; k.style.transform = "translateY(14px)";
          requestAnimationFrame(function () { requestAnimationFrame(function () {
            if (!alive) return;
            k.style.transition = "opacity .45s ease " + (i * 80) + "ms, transform .45s cubic-bezier(.2,.8,.2,1) " + (i * 80) + "ms";
            k.style.opacity = "1"; k.style.transform = "none";
          }); });
        });
      },
      dim: function (it) {
        var layer = doc.createElement("div"); layer.className = "mo-dim"; app.appendChild(layer);
        undo.push(function () { layer.remove(); });
        var level = it.level || 0.82;
        function dark() { layer.classList.add("on"); layer.style.opacity = String(level); }
        if (demo) { later(dark, 700); return; }
        var t = 0;
        function arm(ms) { clearTimeout(t); layer.style.opacity = "0"; layer.classList.remove("on"); t = later(dark, ms); }
        layer.addEventListener("pointerdown", function () { arm(4000); });   // 누르면 잠깐 밝아졌다가 다시 어두워진다
        arm(it.ms || 3000);
      },
      hold: function (it) {
        var btn = app.querySelector('[data-trigger="' + it.target + '"]'); if (!btn) return;
        var ms = it.ms || 2000, fill = doc.createElement("span");
        fill.className = "mo-hold-fill"; btn.classList.add("mo-hold"); btn.appendChild(fill);
        undo.push(function () { fill.remove(); btn.classList.remove("mo-hold", "mo-pulse"); });
        if (demo) {   // 보여 주기: 버튼이 2초 동안 차오르는 모습을 되풀이
          var loop = function () { fill.style.transition = "none"; fill.style.transform = "scaleX(0)"; void fill.offsetWidth; fill.style.transition = "transform " + ms + "ms linear"; fill.style.transform = "scaleX(1)"; };
          later(loop, 300); every(loop, ms + 900); return;
        }
        var t = 0, held = false;
        function reset() { clearTimeout(t); fill.style.transition = "transform .2s ease"; fill.style.transform = "scaleX(0)"; }
        btn.addEventListener("pointerdown", function (e) {
          e.preventDefault(); held = false;
          fill.style.transition = "transform " + ms + "ms linear"; fill.style.transform = "scaleX(1)";
          t = later(function () { held = true; btn.click(); }, ms);
        });
        ["pointerup", "pointerleave", "pointercancel"].forEach(function (ev) { btn.addEventListener(ev, function () { if (!held) reset(); }); });
        doc.addEventListener("click", function (e) {   // 짧게 누르면 이동하지 않는다 (흐름 버튼의 이동보다 먼저 가로챈다)
          if (!e.target.closest || e.target.closest('[data-trigger="' + it.target + '"]') !== btn || held) return;
          e.preventDefault(); e.stopImmediatePropagation(); reset(); toast(it.note || "길게 눌러 주세요");
        }, true);
      },
      reorder: function (it) {
        var root = q(it.target); if (!root) return;
        var list = root.matches("ul, ol") ? root : root.querySelector("ul, ol"); if (!list) return;
        if (demo) {   // 보여 주기: 둘째 줄을 들어서 첫째 줄 위로 옮기는 모습
          var a = list.children[0], b = list.children[1]; if (!a || !b) return;
          styleOf(a); styleOf(b); undo.push(function () { b.classList.remove("mo-lift"); });
          later(function () { b.classList.add("mo-lift"); b.style.transition = "transform .25s ease"; b.style.transform = "scale(1.02)"; }, 400);
          later(function () { var h = a.offsetHeight; b.style.transition = a.style.transition = "transform .5s cubic-bezier(.2,.8,.2,1)"; b.style.transform = "translateY(" + -h + "px) scale(1.02)"; a.style.transform = "translateY(" + b.offsetHeight + "px)"; }, 900);
          later(function () { b.classList.remove("mo-lift"); b.style.transform = "translateY(" + -a.offsetHeight + "px)"; }, 1600);
          return;
        }
        var drag = null, t = 0;
        list.addEventListener("pointerdown", function (e) {
          var row = e.target.closest("li"); if (!row || row.parentNode !== list) return;
          var y0 = e.clientY;
          t = later(function () { drag = { row: row, y0: y0 }; row.classList.add("mo-lift"); try { row.setPointerCapture(e.pointerId); } catch (x) {} }, 350);
        });
        list.addEventListener("pointermove", function (e) {
          if (!drag) return; e.preventDefault();
          var dy = e.clientY - drag.y0, row = drag.row; row.style.transform = "translateY(" + dy + "px)";
          var sib = dy < 0 ? row.previousElementSibling : row.nextElementSibling;
          if (sib && Math.abs(dy) > sib.offsetHeight / 2) {
            if (dy < 0) list.insertBefore(row, sib); else list.insertBefore(sib, row);
            drag.y0 += (dy < 0 ? -1 : 1) * sib.offsetHeight; row.style.transform = "translateY(" + (e.clientY - drag.y0) + "px)"; drag.moved = true;
          }
        });
        function end() { clearTimeout(t); if (!drag) return; drag.row.classList.remove("mo-lift"); drag.row.style.transform = ""; if (drag.moved) toast("순서를 바꿨어요"); drag = null; }
        ["pointerup", "pointercancel", "pointerleave"].forEach(function (ev) { list.addEventListener(ev, end); });
      },
      carousel: function (it) {
        var root = q(it.target); if (!root || reduce) return;
        var sc = [root].concat([].slice.call(root.querySelectorAll("*"))).filter(function (x) { return x.scrollWidth > x.clientWidth + 4; })[0]; if (!sc) return;
        var paused = 0, left0 = sc.scrollLeft;
        undo.push(function () { sc.scrollLeft = left0; });
        if (!demo) sc.addEventListener("pointerdown", function () { paused = Date.now() + 5000; });
        every(function () {
          if (Date.now() < paused) return;
          var step = (sc.firstElementChild ? sc.firstElementChild.offsetWidth : 80) + 8;
          sc.scrollTo({ left: sc.scrollLeft + sc.clientWidth >= sc.scrollWidth - 4 ? 0 : sc.scrollLeft + step, behavior: "smooth" });
        }, demo ? 1200 : it.ms || 2500);
      },
      play: function (it) {
        var root = q(it.target); if (!root) return;
        var bar = root.querySelector(".progress-bar"), btn = root.querySelector("button"); if (!bar) return;
        var ms = demo ? Math.min(it.ms || 18000, 4000) : it.ms || 18000, on = false;
        styleOf(bar);
        function start() {
          on = true; bar.style.transition = "none"; bar.style.width = "0%";
          requestAnimationFrame(function () { requestAnimationFrame(function () { if (!alive) return; bar.style.transition = "width " + ms + "ms linear"; bar.style.width = "100%"; }); });
          later(function () { on = false; }, ms);
        }
        function stop() { on = false; bar.style.transition = "none"; bar.style.width = getComputedStyle(bar).width; }
        if (demo) { later(start, 300); return; }
        if (btn) btn.addEventListener("click", function () { if (on) stop(); else start(); });
      }
    };

    if (demo) return tutorial();
    if (M.overlay) {   // 뜨는 창: 아래에서(또는 가운데서) 올라온다
      var bd = app.querySelector(".modal-backdrop");
      if (bd) { restart(bd, "mo-in"); undo.push(function () { bd.classList.remove("mo-in"); }); }
    }
    (M.items || []).forEach(function (it) { var f = it && RUN[it.type]; if (f) f(it); });

    function stopAll() { alive = false; timers.forEach(function (t) { clearTimeout(t); clearInterval(t); }); undo.reverse().forEach(function (f) { try { f(); } catch (e) {} }); undo = []; }
    return { stop: stopAll };
  };

  // ---- 완성본 화면별 페이지 ----
  var M = window.HX_MOTION; if (!M) return;
  var app = doc.querySelector(".app"); if (!app) return;
  if (!M.overlay) app.classList.add(location.hash === "#back" ? "mo-enter-back" : "mo-enter");
  // 고르는 버튼은 눌렀을 때 실제로 골라진다 (칩은 켜고 끄기, 나머지는 묶음에서 하나만) — 안내 문구 대신 모양이 바뀐다
  var PICK = ".chip, .segmented-item, .tab, .day";
  [].forEach.call(app.querySelectorAll(PICK), function (b) {
    if (b.hasAttribute("data-stay") && !b.hasAttribute("data-trigger")) { b.setAttribute("data-mo-stay", b.getAttribute("data-stay")); b.removeAttribute("data-stay"); }
  });
  app.addEventListener("click", function (e) {
    var t = e.target.closest && e.target.closest(PICK);
    if (!t || !app.contains(t) || t.hasAttribute("data-hx-link") || t.hasAttribute("data-trigger") || t.classList.contains("nav-item")) return;
    if (t.classList.contains("chip")) { t.classList.toggle("active"); t.setAttribute("aria-pressed", t.classList.contains("active") ? "true" : "false"); return; }
    [].forEach.call(t.parentElement.children, function (c) { if (c.matches(PICK)) { c.classList.toggle("active", c === t); c.setAttribute("aria-pressed", c === t ? "true" : "false"); } });
  });
  app.addEventListener("click", function (e) {
    var b = e.target.closest && e.target.closest("[data-out]"); if (!b || !app.contains(b)) return;
    e.preventDefault(); appOut(app, b.getAttribute("data-out"), (b.textContent || "").trim());
  });
  // 옆으로 넘치는 줄: 끝을 흐리게 + 마우스로 끌어서 밀기 (컴퓨터에서는 스와이프가 없으니)
  markSwipe(app);
  swipers(app).forEach(function (row) {
    var d = null;
    row.addEventListener("pointerdown", function (e) { if (e.pointerType !== "mouse") return; d = { x: e.clientX, l: row.scrollLeft, moved: false }; });
    window.addEventListener("pointermove", function (e) { if (!d) return; var dx = e.clientX - d.x; if (Math.abs(dx) > 4) d.moved = true; row.scrollLeft = d.l - dx; });
    window.addEventListener("pointerup", function () { if (d && d.moved) row.addEventListener("click", function stop(ev) { ev.stopPropagation(); ev.preventDefault(); row.removeEventListener("click", stop, true); }, true); d = null; });
  });
  // 입력칸 글자 수: maxlength면 "3/20"이 실시간으로, minlength보다 짧으면 칸 아래 빨간 안내
  [].forEach.call(app.querySelectorAll("input[maxlength], textarea[maxlength], input[minlength], textarea[minlength]"), function (inp) {
    var field = inp.closest(".field") || inp.parentElement, max = +inp.getAttribute("maxlength") || 0, min = +inp.getAttribute("minlength") || 0, cnt = null;
    if (max) { cnt = doc.createElement("span"); cnt.className = "field-count"; inp.insertAdjacentElement("afterend", cnt); }
    var err = field.querySelector(".field-error");
    function paint() {
      var n = inp.value.length;
      if (cnt) { cnt.textContent = n + "/" + max; cnt.classList.toggle("is-full", n >= max); }
      if (min && field.classList.contains("is-error") && n >= min) field.classList.remove("is-error");
    }
    inp.addEventListener("input", paint);
    inp.addEventListener("blur", function () {
      if (!min || !inp.value || inp.value.length >= min) return;
      if (!err) { err = doc.createElement("p"); err.className = "field-error"; field.appendChild(err); }
      err.textContent = min + "자 이상 적어 주세요"; field.classList.add("is-error");
    });
    paint();
  });
  window.HXMotion(app, M, false);
})();
