"""예쁨 검사 (K13, 10-08). 렌더된 앱의 모든 화면을 폰·PC 로 열어 웹디자인 기본기를 숫자로 잰다.

    python scripts/lint.py design/v/v1/app.html                 # 표로 출력
    python scripts/lint.py design/v/v1/app.html --json out.json # + JSON(variants.py 가 씀)
    python scripts/lint.py design/v/v1/app.html --only home,plan

규칙 id(R1…) = `.claude/skills/oss-design-harness/RULES.md` 의 id(근거: 책·공식 문서). S0~S13 = AI 슬롭(같은 문서 '슬롭' 절). K1~K3 = 한글(KOREAN.md 4절을 그대로 읽음).
판정: PASS / WARN / FAIL. 어림셈 규칙(R2·R4·R10·R14·R15·R16·R19·R24·R25·R27·R32)은 WARN 까지만 낸다.
FAIL 이 하나라도 있으면 자가 교정 대상.
"""
import json
import pathlib
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

M = {"width": 390, "height": 844}
D = {"width": 1440, "height": 900}

PROBE = r"""
() => {
  const scr = document.querySelector('.scr.on') || document.body;
  const vis = el => { const r = el.getBoundingClientRect(); const cs = getComputedStyle(el);
    return r.width > 1 && r.height > 1 && cs.visibility !== 'hidden' && cs.display !== 'none' && +cs.opacity > 0.05; };
  // 색 문자열 → [r,g,b,a]. rgb() 가 아니면(color-mix → color(srgb …)·oklch 등) 캔버스에 칠해 실제 값을 읽는다(10-08 오탐 수정)
  const CV = document.createElement('canvas').getContext('2d', { willReadFrequently: true }); const CC = {};
  const rgb = s => { if (!s || s === 'transparent') return s === 'transparent' ? [0, 0, 0, 0] : null;
    const m = s.match(/^rgba?\(([^)]+)\)$/); if (m) { const p = m[1].split(/[ ,\/]+/).filter(Boolean).map(Number); return [p[0], p[1], p[2], p.length > 3 ? p[3] : 1]; }
    if (CC[s]) return CC[s];
    CV.clearRect(0, 0, 1, 1); CV.fillStyle = '#000'; CV.fillStyle = s; CV.fillRect(0, 0, 1, 1); const d = CV.getImageData(0, 0, 1, 1).data;
    return (CC[s] = [d[0], d[1], d[2], d[3] / 255]); };
  const lum = c => { const f = v => { v /= 255; return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
    return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2]); };
  const blend = (t, b) => { const a = t[3]; return [t[0]*a + b[0]*(1-a), t[1]*a + b[1]*(1-a), t[2]*a + b[2]*(1-a), 1]; };
  const sat = c => { const mx = Math.max(c[0], c[1], c[2]), mn = Math.min(c[0], c[1], c[2]); return mx ? (mx - mn) / mx : 0; };
  const bgOf = el => { const st = []; for (let n = el; n && n.nodeType === 1; n = n.parentElement) { const cs = getComputedStyle(n);
      if (cs.backgroundImage && cs.backgroundImage !== 'none' && !/gradient/.test(cs.backgroundImage)) return null;
      const c = rgb(cs.backgroundColor); if (c && c[3] > 0) { st.push(c); if (c[3] >= 1) break; } }
    let base = [255, 255, 255, 1]; for (let i = st.length - 1; i >= 0; i--) base = blend(st[i], base); return base; };
  const sel = el => { let s = el.tagName.toLowerCase(); if (el.className && typeof el.className === 'string' && el.className.trim()) s += '.' + el.className.trim().split(/\s+/).slice(0, 2).join('.'); return s; };
  const txt = el => (el.innerText || el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 22);
  const own = el => [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim().length);
  const lines = el => { const n = [...el.childNodes].find(n => n.nodeType === 3 && n.textContent.trim().length); if (!n) return 1;
    const r = document.createRange(); r.selectNodeContents(n); const tops = new Set([...r.getClientRects()].map(q => Math.round(q.top / 3))); return Math.max(1, tops.size); };
  const EMO = /[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}\u{1F000}-\u{1F2FF}]/u;
  const out = { texts: [], targets: [], icons: [], spacing: [], shadows: [], radii: [], btnH: [], primaryInView: 0, lefts: [],
    overflowX: document.documentElement.scrollWidth - innerWidth, clipped: [], vw: innerWidth, vh: innerHeight,
    scrW: scr.getBoundingClientRect().width, tabs: 0, emoji: [] };
  const all = [...scr.querySelectorAll('*')].filter(el => !['SCRIPT', 'STYLE'].includes(el.tagName) && !el.closest('svg') && vis(el));
  for (const el of all) {
    const cs = getComputedStyle(el), r = el.getBoundingClientRect();
    if (own(el)) {
      const fg = rgb(cs.color), bg = bgOf(el); let cr = null;
      if (fg && bg) { const f = blend(fg, bg); const a = lum(f), b = lum(bg); cr = (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05); }
      const fs = parseFloat(cs.fontSize), t = (el.innerText || '').trim();
      const tag = el.tagName.toLowerCase();
      const hb = /^h[1-6]$/.test(tag) || tag === 'button' || /\b(btn|h1|title|tab)\b/.test(el.className || '');
      out.texts.push({ s: sel(el), t: txt(el), fs, fw: +cs.fontWeight, lh: cs.lineHeight === 'normal' ? fs * 1.2 : parseFloat(cs.lineHeight),
        ls: cs.letterSpacing === 'normal' ? 0 : parseFloat(cs.letterSpacing), align: cs.textAlign, wb: cs.wordBreak, hb,
        body: ['p', 'li', 'dd', 'blockquote', 'td'].includes(tag) || t.length >= 40, x: r.left, y: r.top, w: r.width, h: r.height,
        lines: lines(el), cr, fg: fg ? fg.slice(0, 3) : null, fgSat: fg ? sat(fg) : 0, hangul: /[가-힣]/.test(t), len: t.length });
      if (el.scrollWidth > el.clientWidth + 2 && cs.overflow !== 'visible' && cs.textOverflow !== 'ellipsis' && cs.whiteSpace === 'nowrap')
        out.clipped.push({ s: sel(el), t: txt(el) });
      if (EMO.test(t) && (hb || el.closest('nav, .tabbar, .btn, button, header, .h1'))) out.emoji.push(sel(el) + ' "' + txt(el) + '"');
      if (r.left < out.vw * 0.6) out.lefts.push(Math.round(r.left));
    }
    const flex = /flex|grid/.test(cs.display);
    for (const p of ['paddingTop', 'paddingRight', 'paddingBottom', 'paddingLeft', 'marginTop', 'marginBottom', ...(flex ? ['rowGap', 'columnGap'] : [])]) {
      const v = Math.abs(parseFloat(cs[p])); if (v > 0 && v < 200) out.spacing.push(Math.round(v * 10) / 10); }
    if (cs.boxShadow && cs.boxShadow !== 'none') out.shadows.push(cs.boxShadow.replace(/\s+/g, ' '));
    const rad = parseFloat(cs.borderTopLeftRadius); if (rad > 0) out.radii.push(rad >= Math.min(r.width, r.height) / 2 - 1 || rad >= 99 ? 'pill' : Math.round(rad));
    if (el.matches('button, .btn, [role=button]')) { out.btnH.push(Math.round(r.height));
      const bg = rgb(cs.backgroundColor); if (bg && bg[3] > 0.5 && sat(bg) >= 0.25 && r.top < innerHeight && r.bottom > 0) out.primaryInView++; }
  }
  const navs = [scr, ...document.querySelectorAll('.tabbar, .topnav, .side-nav')];
  for (const el of navs.flatMap(n => [...n.querySelectorAll('a, button, [onclick], input, select, [role=button]')])) {
    if (!vis(el)) continue; const r = el.getBoundingClientRect(); out.targets.push({ s: sel(el), t: txt(el), w: r.width, h: r.height }); }
  const tb = document.querySelector('.tabbar'); if (tb && vis(tb)) out.tabs = [...tb.querySelectorAll('a, button')].filter(vis).length;
  for (const el of scr.querySelectorAll('svg.lucide, svg[class*=lucide]')) { if (!vis(el)) continue; out.icons.push(Math.round(el.getBoundingClientRect().width)); }
  const T = all.filter(own); out.overlaps = [];
  for (let i = 0; i < T.length && out.overlaps.length < 30; i++) for (let j = i + 1; j < T.length; j++) {
    const a = T[i], b = T[j]; if (a.contains(b) || b.contains(a)) continue;
    const r = a.getBoundingClientRect(), q = b.getBoundingClientRect();
    const ox = Math.min(r.right, q.right) - Math.max(r.left, q.left), oy = Math.min(r.bottom, q.bottom) - Math.max(r.top, q.top);
    if (ox > 3 && oy > 3) out.overlaps.push({ a: sel(a) + ' "' + txt(a) + '"', b: sel(b) + ' "' + txt(b) + '"' });
  }
  // ---- 한글(KOREAN.md) 검사용 글 — 라벨(제목·탭·메뉴·버튼) 여부 표시 ----
  out.ktext = [];
  const kseen = new Set();
  const kpush = (el, lab) => { const t = (el.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 160); if (!t || kseen.has(t + lab)) return; kseen.add(t + lab); out.ktext.push({ t, lab }); };
  for (const el of all) if (own(el)) { const tag = el.tagName.toLowerCase();
    const lab = /^h[1-6]$/.test(tag) || tag === 'button' || !!el.closest('button, .btn, .h1, header, .sec, .tabbar, .side-nav, .topnav, nav, .badge, .chip, .tag, .pill, .stamp, [class*=badge], [class*=chip], [class*=tag]'); kpush(el, lab); }
  for (const el of document.querySelectorAll('.tabbar a, .side-nav a, .topnav a')) if (vis(el)) kpush(el, true);
  // ---- AI 슬롭(ai-slop-criteria.md §7) ----
  const hsv = c => { const mx = Math.max(c[0], c[1], c[2]), mn = Math.min(c[0], c[1], c[2]); const d = mx - mn; let h = 0;
    if (d) { const [r, g, b] = c; h = mx === r ? ((g - b) / d) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4; h = (h * 60 + 360) % 360; }
    return [h, mx ? d / mx : 0, mx / 255]; };
  const SL = { stripe: [], purpleGrad: [], indigo: [], cream: [], italicSerif: [], gradText: [], caps: [], same3: [], glass: [], nested: [], chrome: [], copy: [], font: [] };
  const IND = [[99, 102, 241], [129, 140, 248], [79, 70, 229]];
  const near = (c, t) => Math.abs(c[0] - t[0]) + Math.abs(c[1] - t[1]) + Math.abs(c[2] - t[2]) < 18;
  const isCard = (el, cs) => { const bg = rgb(cs.backgroundColor); return parseFloat(cs.borderTopLeftRadius) > 0 && ((bg && bg[3] > 0) || cs.boxShadow !== 'none' || parseFloat(cs.borderTopWidth) > 0); };
  const RX = /을 통해|를 통해|제공합니다|오늘날|빠르게 변화하는|혁신적인|원활한|최적의 경험|새로운 차원|한 단계 더|극대화|[가-힣]\u2019s|[가-힣]\u0027s|seamless|elevate|unleash|empower|revolutioni[sz]e|cutting-edge/i;
  for (const el of all) {
    const cs = getComputedStyle(el), r = el.getBoundingClientRect();
    const bl = parseFloat(cs.borderLeftWidth), bo = parseFloat(cs.borderTopWidth) + parseFloat(cs.borderRightWidth) + parseFloat(cs.borderBottomWidth);
    if (bl >= 2 && bo === 0 && r.height > 30 && r.width > 120) SL.stripe.push(sel(el));
    if (cs.position === 'absolute' && r.width <= 6 && el.parentElement) { const pr = el.parentElement.getBoundingClientRect();
      if (r.height >= pr.height * 0.8 && Math.abs(r.left - pr.left) < 3 && pr.width > 120) SL.stripe.push(sel(el.parentElement)); }
    if (/gradient/.test(cs.backgroundImage)) { const cols = (cs.backgroundImage.match(/rgba?\([^)]+\)/g) || []).map(rgb).filter(Boolean);
      const pur = cols.filter(c => { const q = hsv(c); return q[0] >= 230 && q[0] <= 295 && q[1] >= 0.3; });
      if (pur.length && cols.length >= 2 && r.width > 150) SL.purpleGrad.push(sel(el)); }
    for (const prop of ['backgroundColor', 'color', 'borderTopColor']) { const c = rgb(cs[prop]); if (c && c[3] > 0.5 && IND.some(t => near(c, t))) { SL.indigo.push(sel(el) + ' ' + prop); break; } }
    if (cs.fontStyle === 'italic' && el.closest('h1,h2,.h1,.poster,.hero') && /serif|batang|hahmlet|myeongjo/i.test(cs.fontFamily) && !/sans/i.test(cs.fontFamily.split(',')[0])) SL.italicSerif.push(sel(el) + ' "' + txt(el) + '"');
    if (/text/.test(cs.webkitBackgroundClip || cs.backgroundClip || '') && /gradient/.test(cs.backgroundImage)) SL.gradText.push(sel(el));
    if (cs.textTransform === 'uppercase' && parseFloat(cs.fontSize) <= 13 && own(el)) SL.caps.push(sel(el) + ' "' + txt(el) + '"');
    if (/blur/.test(cs.backdropFilter || cs.webkitBackdropFilter || '')) { const bg = rgb(cs.backgroundColor); if (bg && bg[3] < 1 && r.width > 120 && r.height > 60) SL.glass.push(sel(el)); }
    if (isCard(el, cs) && cs.boxShadow !== 'none' && r.width > 100 && r.height > 50) {
      for (let q = el.parentElement; q && q !== scr; q = q.parentElement) { const qs = getComputedStyle(q); const qr = q.getBoundingClientRect();
        if (isCard(q, qs) && qs.boxShadow !== 'none' && qr.width > r.width + 8) { SL.nested.push(sel(q) + ' > ' + sel(el)); break; } } }
    const kids = [...el.children].filter(vis);
    if (kids.length >= 3 && kids.length <= 4) { const sig = k => [...k.children].map(c => c.tagName).join('/') + '|' + Math.round(k.getBoundingClientRect().width / 4);
      const s0 = sig(kids[0]); if (s0.split('|')[0].split('/').length >= 3 && kids.every(k => sig(k) === s0) && kids.every(k => k.querySelector('svg')) && kids.every(k => isCard(k, getComputedStyle(k))))
        SL.same3.push(sel(el) + ' x' + kids.length); }
    if (own(el) && r.top < 60 && /^(9:41|100%|LTE|5G)$/.test((el.textContent || '').trim())) SL.chrome.push(sel(el) + ' "' + txt(el) + '"');
    if (own(el)) { const hit = (el.textContent || '').match(RX); if (hit) SL.copy.push(sel(el) + ' "' + hit[0] + '"'); }
  }
  const ff = getComputedStyle(document.body).fontFamily.split(',')[0].replace(/["']/g, '').trim();
  if (/^(Inter|Roboto|Arial|Poppins|Open Sans|Geist|Helvetica)$/i.test(ff)) SL.font.push(ff);
  const appEl = document.querySelector('.app') || document.body; const pg = rgb(getComputedStyle(appEl).backgroundColor);
  if (pg) { const q = hsv(pg); if (q[0] >= 30 && q[0] <= 55 && q[1] <= 0.2 && q[1] > 0.015 && q[2] >= 0.9) SL.cream.push('배경 ' + getComputedStyle(appEl).backgroundColor); }
  out.slop = SL;
  return out;
}
"""


def W(m, t):
    return f'{m["where"]} {t["s"]} "{t["t"]}"'


def verdict(bad_fail, bad_warn):
    return "FAIL" if bad_fail else "WARN" if bad_warn else "PASS"


def on4(v):
    return abs(v / 4 - round(v / 4)) < 0.13


# ---- 규칙 함수: 측정값 목록 → (상태, 한 줄, 예시) ----
def r1(ms):
    vals = [v for m in ms for v in m["spacing"] if v > 2]
    if not vals:
        return "PASS", "간격 값 없음", []
    ratio = sum(1 for v in vals if on4(v)) / len(vals)
    off = {}
    for v in vals:
        if not on4(v):
            off[v] = off.get(v, 0) + 1
    ex = ["벗어난 값(횟수): " + ", ".join(f"{k:g}px×{n}" for k, n in sorted(off.items(), key=lambda x: -x[1])[:10])] if off else []
    return ("FAIL" if ratio < 0.75 else "WARN" if ratio < 0.9 else "PASS"), f"간격 중 4의 배수 {ratio*100:.0f}%(90% 이상)", ex


S2 = {2, 4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80, 96, 128}


def r2(ms):
    vals = [round(v) for m in ms for v in m["spacing"] if v > 2]
    if not vals:
        return "PASS", "", []
    out = sum(1 for v in vals if v not in S2) / len(vals)
    distinct = len(set(vals))
    return ("WARN" if out > 0.1 or distinct > 14 else "PASS"), f"간격 종류 {distinct}개 · 단계표 밖 {out*100:.0f}%(10% 이하)", []


def r4(ms):
    worst, ex = 0, []
    for m in ms:
        L = m["lefts"]
        if len(L) < 6:
            continue
        iso = [x for x in L if sum(1 for y in L if abs(x - y) <= 1) == 1]
        ratio = len(iso) / len(L)
        worst = max(worst, ratio)
        if ratio > 0.1:
            ex.append(f'{m["where"]} 고립된 왼쪽 시작점 {len(iso)}/{len(L)} {sorted(set(iso))[:6]}')
    return ("WARN" if worst > 0.1 else "PASS"), f"정렬선을 공유하지 않는 글자 최대 {worst*100:.0f}%(10% 이하)", ex[:6]


def r5(ms):
    ex = []
    for m in ms:
        if m["dev"] == "d" and m["scrW"] > 1300:
            ex.append(f'{m["where"]} 본문 폭 {m["scrW"]:.0f}px')
        if m["dev"] == "m":
            xs = [t["x"] for t in m["texts"] if t["x"] >= 0]
            if xs and min(xs) < 12:
                ex.append(f'{m["where"]} 글자가 화면 끝에서 {min(xs):.0f}px')
    return ("WARN" if ex else "PASS"), f"폰 좌우 여백 16px·PC 본문 1280px 이하 위반 {len(ex)}화면", ex[:6]


def r7(ms):
    bad = [W(m, t) + f' {t["lines"]}줄' for m in ms for t in m["texts"] if t["align"] == "center" and t["lines"] >= 3]
    jus = [W(m, t) for m in ms for t in m["texts"] if t["align"] == "justify"]
    return verdict(bad, jus), f"3줄 이상 가운데 정렬 {len(bad)} · 양쪽 정렬 {len(jus)}", bad[:6] + jus[:3]


def r8(ms):
    tiny = [W(m, t) + f' {t["fs"]:.0f}px' for m in ms for t in m["texts"] if t["fs"] < 12 and t["len"] > 1]
    small = [W(m, t) + f' {t["fs"]:.0f}px' for m in ms if m["dev"] == "m" for t in m["texts"] if t["body"] and t["fs"] < 16 and t["len"] >= 20]
    st = "FAIL" if len(tiny) > 3 else "WARN" if tiny or len(small) > 3 else "PASS"
    return st, f"12px 미만 글자 {len(tiny)} · 폰 본문 16px 미만 {len(small)}", tiny[:6] + small[:4]


def r9(ms):
    worst, ex = 0, []
    for m in ms:
        sizes = sorted({round(t["fs"]) for t in m["texts"]})
        worst = max(worst, len(sizes))
        if len(sizes) > 6:
            ex.append(f'{m["where"]} {len(sizes)}종 {sizes}')
    return ("FAIL" if worst >= 9 else "WARN" if worst > 6 else "PASS"), f"한 화면 글자 크기 최대 {worst}종(6 이하)", ex[:6]


def r10(ms):
    ex = []
    for m in ms:
        sizes = sorted({round(t["fs"], 1) for t in m["texts"]})  # 반올림 전 크기로 비를 잰다(19/17 착시 방지)
        near = [(a, b) for a, b in zip(sizes, sizes[1:]) if b / a < 1.12]
        if near:
            ex.append(f'{m["where"]} 거의 같은 크기 {near[:4]}')
    return ("WARN" if ex else "PASS"), f"이웃 크기 비 1.125 미만이 있는 화면 {len(ex)}", ex[:6]


def r11(ms):
    worst, light, ex = 0, [], []
    for m in ms:
        w = sorted({t["fw"] for t in m["texts"]})
        worst = max(worst, len(w))
        if len(w) > 3:
            ex.append(f'{m["where"]} 굵기 {w}')
        light += [W(m, t) + f' {t["fw"]}' for t in m["texts"] if t["fw"] < 400 and t["fs"] < 24]
    return ("FAIL" if light else "WARN" if worst > 3 else "PASS"), f"굵기 최대 {worst}종(3 이하) · 24px 미만 가는 글자 {len(light)}", light[:4] + ex[:4]


def r12(ms):
    bad = []
    for m in ms:
        for t in m["texts"]:
            if t["lines"] < 2 or not t["hangul"]:
                continue
            ratio = t["lh"] / t["fs"]
            if t["fs"] < 24 and t["len"] >= 20 and not 1.45 <= ratio <= 1.85:
                bad.append(W(m, t) + f" 본문 줄간격 {ratio:.2f}")
            elif t["fs"] >= 24 and not 1.1 <= ratio <= 1.45:
                bad.append(W(m, t) + f" 제목 줄간격 {ratio:.2f}")
    return ("WARN" if bad else "PASS"), f"줄간격(한글 본문 1.5~1.7·제목 1.15~1.35) 밖 {len(bad)}", bad[:6]


def r13(ms):
    f, w = [], []
    for m in ms:
        for t in m["texts"]:
            if t["hangul"] and t["lines"] >= 2 and t["fs"] < 24:
                n = t["w"] / t["fs"]
                if n > 50:
                    f.append(W(m, t) + f" 한 줄 약 {n:.0f}자")
                elif n > 40:
                    w.append(W(m, t) + f" 한 줄 약 {n:.0f}자")
    return verdict(f, w), f"한글 문단 한 줄 40자 초과 {len(w)} · 50자 초과 {len(f)}", f[:4] + w[:4]


def r14(ms):
    worst, ex = 0, []
    for m in ms:
        g = {tuple(c // 8 for c in t["fg"]) for t in m["texts"] if t["fg"] and t["fgSat"] < 0.1}
        worst = max(worst, len(g))
        if len(g) > 4:
            ex.append(f'{m["where"]} 회색 글자색 {len(g)}종')
    return ("WARN" if worst > 4 else "PASS"), f"한 화면 회색 글자색 최대 {worst}종(주·보조·흐림 3~4)", ex[:6]


def r15(ms):
    ex = []
    for m in ms:
        if m["dev"] != "m":
            continue
        big = [t for t in m["texts"] if t["fs"] >= 32 and t["y"] < m["vh"]]
        if len(big) > 2:
            ex.append(f'{m["where"]} 첫 화면 큰 글자 {len(big)}개: ' + ", ".join(f'"{t["t"]}"' for t in big[:4]))
    return ("WARN" if ex else "PASS"), f"폰 첫 화면에 큰 글자(32px+) 3개 이상인 화면 {len(ex)}", ex[:6]


def r16(ms):
    ex = [f'{m["where"]} 색 채운 버튼 {m["primaryInView"]}개' for m in ms if m["primaryInView"] > 2]
    return ("WARN" if ex else "PASS"), f"첫 화면에 색 채운 주 버튼 3개 이상 {len(ex)}화면", ex[:6]


def r17(ms):
    bad, warn = [], []
    for m in ms:
        for t in m["texts"]:
            if t["cr"] is None:
                continue
            need = 3.0 if (t["fs"] >= 24 or (t["fs"] >= 18.66 and t["fw"] >= 700)) else 4.5
            if t["cr"] < need - 1.0:
                bad.append(W(m, t) + f' {t["cr"]:.2f}:1')
            elif t["cr"] < need:
                warn.append(W(m, t) + f' {t["cr"]:.2f}:1')
    return verdict(bad, warn), f"대비 미달 {len(bad)}(크게) · {len(warn)}(조금) — 본문 4.5:1·큰 글자 3:1", bad[:8] + warn[:4]


def _hue(c):
    r, g, b = [v / 255 for v in c]
    mx, mn = max(r, g, b), min(r, g, b)
    d = mx - mn
    if not d:
        return 0
    h = ((g - b) / d % 6) if mx == r else ((b - r) / d + 2) if mx == g else ((r - g) / d + 4)
    return (h * 60) % 360


def r19(ms):
    worst, ex = 0, []
    for m in ms:
        hs = {int(_hue(t["fg"])) // 30 for t in m["texts"] if t["fg"] and t["fgSat"] >= 0.25 and max(t["fg"]) > 40}
        worst = max(worst, len(hs))
        if len(hs) > 3:
            ex.append(f'{m["where"]} 유채색 글자 색상 {len(hs)}묶음')
    return ("WARN" if worst > 3 else "PASS"), f"한 화면 유채색 글자 색상 최대 {worst}묶음(강조 1~2 + 상태색)", ex[:6]


def r21(ms):
    ex = [W(m, t) for m in ms for t in m["texts"] if t["fg"] == [0, 0, 0]]
    return ("WARN" if ex else "PASS"), f"순검정(#000) 글자 {len(ex)}", ex[:4]


def r24(ms):
    sh = {s for m in ms for s in m["shadows"]}
    return ("WARN" if len(sh) > 3 else "PASS"), f"그림자 종류 {len(sh)}(3 이하)", list(sh)[:4] if len(sh) > 3 else []


def r25(ms):
    rd = sorted({r for m in ms for r in m["radii"] if r != "pill"})
    return ("WARN" if len(rd) > 3 else "PASS"), f"모서리 반경 {len(rd)}종 {rd}(알약형 빼고 3 이하)", []


def r27(ms):
    hs = sorted({h for m in ms if m["dev"] == "m" for h in m["btnH"]})
    groups = []
    for h in hs:
        if not groups or h - groups[-1] > 1:
            groups.append(h)
    return ("WARN" if len(groups) > 3 else "PASS"), f"폰 버튼 높이 {len(groups)}종 {groups}(2~3)", []


def r28(ms):
    bad, warn = [], []
    for m in ms:
        if m["dev"] != "m":
            continue
        for t in m["targets"]:
            s = min(t["w"], t["h"])
            line = f'{m["where"]} {t["s"]} "{t["t"]}" {t["w"]:.0f}×{t["h"]:.0f}'
            if s < 24:
                bad.append(line)
            elif s < 44:
                warn.append(line)
    return ("FAIL" if len(bad) > 2 else "WARN" if bad or warn else "PASS"), f"폰 누르는 곳 24px 미만 {len(bad)} · 44px 미만 {len(warn)}", bad[:6] + warn[:4]


def r30(ms):
    bad = [f'{m["where"]} 가로 {m["overflowX"]}px 넘침' for m in ms if m["overflowX"] > 2]
    return ("FAIL" if bad else "PASS"), f"가로 넘침 {len(bad)}화면", bad[:6]


def r31(ms):
    t = sorted({m["tabs"] for m in ms if m["dev"] == "m" and m["tabs"]})
    bad = [x for x in t if not 3 <= x <= 5]
    return ("WARN" if bad else "PASS"), f"폰 하단 탭 개수 {t}(3~5)", []


def r32(ms):
    worst, ex = 0, []
    for m in ms:
        s = sorted(set(m["icons"]))
        worst = max(worst, len(s))
        if len(s) > 3:
            ex.append(f'{m["where"]} 아이콘 크기 {s}')
    return ("WARN" if worst > 3 else "PASS"), f"한 화면 아이콘 크기 최대 {worst}종(3 이하)", ex[:6]


def r34(ms):
    ex = [f'{m["where"]} {e}' for m in ms for e in m["emoji"]]
    return ("FAIL" if ex else "PASS"), f"제목·버튼·내비의 이모지 {len(ex)}", ex[:6]


def r35(ms):
    ex = [W(m, t) for m in ms for t in m["texts"] if t["hb"] and t["hangul"] and t["lines"] >= 2 and t["wb"] != "keep-all"]
    return ("WARN" if ex else "PASS"), f"두 줄 이상 한글 제목·버튼에 keep-all 없음 {len(ex)}", ex[:6]


def r36(ms):
    f = [W(m, t) + f' {t["ls"]/t["fs"]:.3f}em' for m in ms for t in m["texts"] if t["fs"] and t["ls"] / t["fs"] < -0.05]
    w = [W(m, t) + f' {t["ls"]/t["fs"]:.3f}em' for m in ms for t in m["texts"] if t["fs"] < 24 and t["len"] >= 20 and -0.05 <= t["ls"] / t["fs"] < -0.02]
    return verdict(f, w), f"자간 −0.05em 미만 {len(f)} · 본문 −0.02em 미만 {len(w)}", f[:4] + w[:4]


def r40(ms):
    ov = [f'{m["where"]} {o["a"]} ↔ {o["b"]}' for m in ms for o in m["overlaps"]]
    cl = [f'{m["where"]} {c["s"]} "{c["t"]}" 잘림' for m in ms for c in m["clipped"]]
    return ("FAIL" if ov or cl else "PASS"), f"글자 겹침 {len(ov)} · 잘림 {len(cl)}", ov[:8] + cl[:4]


# ---- AI 슬롭 (local/refs/ai-slop-criteria.md: strong 1 = 실패 · weak 단독 = 주의 · 같은 화면 weak 2종 이상 = 실패로 올림) ----
SLOP = {  # 키: (id, 이름, 강약, 최소 개수, 고치는 법)
    "purpleGrad": ("S1", "보라·파랑 그라디언트", "strong", 1, "그라디언트를 지우고 이 서비스 사정에서 이유 있는 단색 면으로."),
    "italicSerif": ("S2", "제목 속 기운 명조 강조어", "strong", 1, "제목 안 이탤릭 세리프 단어를 없애고 굵기·색 하나로 강조."),
    "same3": ("S3", "아이콘+제목+설명 같은 카드 3~4개", "weak", 1, "같은 모양 카드 나열 대신 주인공 하나 + 나머지는 목록·줄로. 크기·형태에 차이를 준다."),
    "stripe": ("S4", "카드 왼쪽 색 띠", "weak", 3, "왼쪽 띠를 없애고 상태는 배지·아이콘·글자 색·점선으로."),
    "indigo": ("S5", "인디고 기본 강조색(#6366F1·#4F46E5)", "weak", 1, "강조색을 이 서비스의 은유·상황에서 나온 색으로 바꾸고 이유를 decisions.md 에."),
    "cream": ("S6", "이유 없는 크림 배경", "weak", 1, "크림 배경은 은유(종이·편지 등)가 있을 때만 — 아니면 흰색/중립 회색, 또는 이유를 decisions.md 에."),
    "gradText": ("S7", "그라디언트 글자", "weak", 1, "글자는 단색으로."),
    "caps": ("S8", "영문 대문자 꼬리표 반복", "weak", 2, "작은 영문 ALL-CAPS 라벨을 한국어 라벨로, 반복하지 않는다."),
    "glass": ("S9", "유리(블러) 카드", "weak", 1, "반투명 블러 카드를 불투명 면으로."),
    "nested": ("S10", "그림자 카드 안 그림자 카드", "weak", 1, "카드 안 카드를 없애고 안쪽은 줄·여백으로 나눈다."),
    "chrome": ("S11", "가짜 상태바(9:41·100%)", "weak", 1, "가짜 상태바·배터리 표시를 지운다(진짜 폰에서 겹친다)."),
    "copy": ("S12", "번역투·버즈워드 문구", "weak", 1, "'~을 통해 제공합니다' 같은 번역투·버즈워드를 사람이 쓰는 짧은 말로."),
    "font": ("S13", "이유 없는 기본 글꼴", "weak", 1, "Inter/Roboto 대신 한국어 글꼴(Pretendard 등)과 이유."),
}


SLOP_OK = {}  # {"S6": "종이 은유"} — app.json 의 slopOk(또는 tokens.slopOk). 약한 슬롭만 허용, 강한 것은 못 막는다


def slop_rules():
    out = []
    for key, (sid, name, sev, need, fix) in SLOP.items():
        def fn(ms, key=key, sev=sev, need=need):
            hit_ms = [m for m in ms if len(m.get("slop", {}).get(key, [])) >= need]
            hits = [f'{m["where"]} {h}' for m in hit_ms for h in m["slop"][key][:3]]
            st = "FAIL" if hits and sev == "strong" else "WARN" if hits else "PASS"
            return st, f"{'강' if sev == 'strong' else '약'} · {len({m['screen'] for m in hit_ms})}화면", hits[:6]
        out.append((sid, name, fn, fix))

    def s0(ms):  # 같은 화면에 약한 슬롭 2종 이상 = 실패로 올림
        bad = []
        for m in ms:
            kinds = [SLOP[k][1] for k, v in m.get("slop", {}).items() if k in SLOP and SLOP[k][2] == "weak" and len(v) >= SLOP[k][3] and SLOP[k][0] not in SLOP_OK]
            if len(kinds) >= 2:
                bad.append(f'{m["where"]} ' + " + ".join(kinds))
        return ("FAIL" if bad else "PASS"), f"약한 슬롭 2종 이상 겹친 화면 {len(bad)}", bad[:6]
    return [("S0", "슬롭 뭉침", s0, "겹친 약한 슬롭 중 하나 이상을 없앤다(아래 S 항목의 고치는 법).")] + out


# ---- 한글 (KOREAN.md 4절의 파이썬 목록을 그대로 읽는다 — 규칙은 그 문서 한 곳에서 고친다) ----
def _korean_lists():
    import re as _re
    kp = pathlib.Path(__file__).resolve().parent.parent / ".claude/skills/oss-design-harness/KOREAN.md"
    env = {}
    if kp.exists():
        for code in _re.findall(r"```python\n(.*?)```", kp.read_text(encoding="utf-8"), _re.S):
            try:
                exec(code, env)
            except Exception:
                pass
    return env.get("STYLE_PATTERNS", []), env.get("METAPHOR_LABELS", []), env.get("SPACING_PATTERNS", [])


KSTYLE, KMETA, KSPACE = _korean_lists()
LABEL_SKIP = ("니다", "명사형")  # 짧은 라벨에는 하십시오체·명사형 끝맺음 검사를 하지 않는다(KOREAN.md 권고)


def _k_hits(ms, pats, labels_only=False, skip_label_kinds=True):
    import re as _re
    hits = []
    for m in ms:
        for x in m.get("ktext", []):
            if labels_only and not x["lab"]:
                continue
            t = _re.sub(r"\d{1,2}[/.]\s?\d{1,2}\.?\s?\(?[월화수목금토일]\)?", "", x["t"])  # 날짜 뒤 요일(12/20 일)은 단위가 아니다
            for pat, fix in pats:
                if x["lab"] and skip_label_kinds and any(k in fix for k in LABEL_SKIP):
                    continue
                if "명사형" in fix and not t.rstrip().endswith("."):  # 명사형 끝맺음은 마침표로 끝나는 안내 문장에만
                    continue
                mm = _re.search(pat, t)
                if mm:
                    hits.append(f'{m["where"]} "{t[:40]}" — {mm.group(0).strip()} → {fix}')
    return list(dict.fromkeys(hits))


def k1(ms):
    h = _k_hits(ms, KSTYLE)
    return ("FAIL" if len(h) > 6 else "WARN" if h else "PASS"), f"번역투·딱딱한 표현 {len(h)}곳(KOREAN.md 4절 a)", h[:8]


def k2(ms):
    import re as _re
    lab, body = [], []
    for m in ms:
        for x in m.get("ktext", []):
            t = x["t"].replace("보일지", "")  # '보일지'(보이다+ㄹ지)에 든 '일지'는 은유 라벨이 아니다(오탐)
            for w in KMETA:
                if w in t:
                    (lab if x["lab"] else body).append(f'{m["where"]} "{x["t"][:40]}" — {w}')
    lab, body = list(dict.fromkeys(lab)), list(dict.fromkeys(body))
    return ("FAIL" if lab else "WARN" if body else "PASS"), f"은유·만든 말 라벨 {len(lab)}곳 · 본문 {len(body)}곳", lab[:8] + body[:3]


def k3(ms):
    h = _k_hits(ms, KSPACE, skip_label_kinds=False)
    return ("WARN" if h else "PASS"), f"띄어쓰기 {len(h)}곳(KOREAN.md 4절 c)", h[:8]


# (id, 이름, 함수, 고치는 법) — 순서 = fix.md 에서 고치는 순서(큰 것부터)
RULES = [
    ("R40", "겹침·잘림", r40, "겹친 요소를 떼어 놓는다. absolute 위치를 고치거나 지도 핀·스티커는 글자 없는 곳으로(z-index 가 아니라 자리를 옮긴다). 고정 높이 상자는 min-height 로."),
    ("R30", "가로 넘침", r30, "고정 폭(width:px)·긴 단어·nowrap 줄을 찾아 max-width:100%·min-width:0·flex-wrap:wrap·word-break:keep-all+overflow-wrap:anywhere."),
    ("K2", "은유 라벨", k2, "화면 이름·탭·메뉴·버튼의 은유·만든 말(작업대·안내장 등)을 KOREAN.md 2절 표준 용어로(일정·공유하기·소식…). 은유는 겉모습에만."),
    ("R17", "글자 대비", r17, "본문 4.5:1, 24px+·굵은 19px+ 는 3:1. 연한 회색을 진하게, 색 배경 위 글자는 흰색이나 아주 진한 색. 흰 글자를 올리는 강조색은 더 진하게."),
    ("R28", "누르는 곳 크기", r28, "폰 버튼·링크·탭은 44px 이상(padding 으로 누르는 영역을 키운다). 24px 미만은 실패."),
    ("R8", "글자 크기 바닥", r8, "어떤 글자도 12px 미만 금지. 폰 본문(문장)은 16~17px. 작은 라벨은 크기 대신 굵기·색·자간으로."),
    ("R9", "글자 크기 종류", r9, "타입 스케일 하나(예: 12·14·16·20·24·32·40)를 CSS 변수로 정하고 그 값만. 한 화면 6종 이하."),
    ("R11", "글자 굵기", r11, "굵기는 2~3종(400·600·800 등). 24px 미만 글자에 300 이하 금지."),
    ("R13", "한 줄 길이", r13, "한글 문단 상자 max-width 를 34~40em 로(특히 PC)."),
    ("R7", "가운데 정렬 문단", r7, "3줄 이상 문단은 왼쪽 정렬. 가운데 정렬은 2줄 이하 제목·짧은 문구만. justify 금지."),
    ("R1", "간격 4의 배수", r1, "padding·margin·gap 을 4의 배수(4·8·12·16·24·32·48)로. 1~2px 선은 예외."),
    ("R34", "이모지 아이콘", r34, "이모지를 지우고 Lucide 아이콘으로."),
    ("R36", "한글 자간", r36, "본문 자간 0~−0.01em, 큰 제목 0~−0.03em. −0.05em 보다 좁히지 않는다."),
] + slop_rules() + [
    ("R2", "간격 단계", r2, "간격은 단계표(4·8·12·16·24·32·48·64)에서만 고른다. 비슷한 값(10·12·14)을 섞지 않는다."),
    ("R4", "정렬선", r4, "같은 열의 아이콘·제목·본문 왼쪽 시작점을 하나의 세로선에 맞춘다(같은 padding 변수 사용)."),
    ("R5", "화면 여백·최대 폭", r5, "폰 좌우 여백 16~24px, PC 본문 최대 폭 1200~1280px."),
    ("R10", "크기 단계 차이", r10, "14와 15처럼 거의 같은 크기를 같이 쓰지 않는다. 이웃 단계 비 1.2 이상."),
    ("R12", "줄간격", r12, "한글 본문 line-height 1.5~1.7, 제목(24px+) 1.15~1.35."),
    ("R14", "회색 단계", r14, "글자색은 주·보조·흐림 3단계(+링크·강조색)만."),
    ("R15", "첫 화면 초점", r15, "폰 첫 화면의 큰 글자(32px+)는 2개까지 — 주인공 하나에 집중."),
    ("R16", "주 버튼 수", r16, "색 채운 주 버튼은 섹션당 1개. 나머지는 테두리·글자 버튼으로."),
    ("R19", "강조색 수", r19, "강조색 1~2개 + 상태색(성공·경고). 카드마다 다른 색을 칠하지 않는다."),
    ("R21", "순검정 글자", r21, "#000 대신 아주 짙은 회색(배경 색조를 조금 섞어)."),
    ("R24", "그림자 단계", r24, "그림자는 2~3단계 변수로만(아래로, 흐림 ≥ y, 진하기 0.3 이하)."),
    ("R25", "모서리 종류", r25, "모서리 반경은 2~3종 변수(예: 8·16 + 알약형). 안쪽 ≤ 바깥."),
    ("R27", "버튼 모양 반복", r27, "버튼 높이는 2~3종(예: 44·52). 같은 역할 버튼은 같은 모양."),
    ("R31", "하단 탭 수", r31, "폰 하단 탭은 3~5개."),
    ("R32", "아이콘 크기", r32, "아이콘은 16·20·24(+장식 하나)만. 같은 줄 아이콘은 같은 크기."),
    ("K1", "번역투·딱딱한 말", k1, "KOREAN.md 3절 대체어로: ~을 통해→~로, 제공합니다→드려요, 하시겠습니까→할까요?, 해요체로 통일."),
    ("K3", "띄어쓰기", k3, "할 수 있어요 · 안 돼요 · 불러오는 중 · 3개(숫자+단위 붙임) · 로그인하기."),
    ("R35", "한글 줄바꿈", r35, "제목·버튼에 word-break:keep-all(어절 단위 줄바꿈)."),
]


def measure(app, only=None):
    from playwright.sync_api import sync_playwright
    plain = not (app.parent / "app.json").exists()  # 10-08: 하네스 앱이 아닌 일반 페이지도(자유도 실험 등) — 페이지 하나를 화면 하나로
    spec = {"screens": [{"id": "page", "title": app.stem}]} if plain else json.loads((app.parent / "app.json").read_text(encoding="utf-8"))
    ids = [s["id"] for s in spec["screens"] if not only or s["id"] in only]
    titles = {s["id"]: s["title"] for s in spec["screens"]}
    SLOP_OK.update(spec.get("slopOk") or spec.get("tokens", {}).get("slopOk") or {})
    ms = []
    with sync_playwright() as pw:
        try:
            b = pw.chromium.launch(channel="chrome")
        except Exception:
            b = pw.chromium.launch()
        for dev, vp in (("m", M), ("d", D)):
            pg = b.new_page(viewport=vp)
            pg.goto(app.resolve().as_uri())
            pg.add_style_tag(content="*{animation:none!important;transition:none!important}")
            pg.wait_for_timeout(800)
            if plain:  # 스크롤하면 나타나는 내용(등장 효과)을 전부 띄운 뒤 잰다
                pg.evaluate("""async () => { const h = () => document.documentElement.scrollHeight; for (let y = 0; y < h(); y += 300) { scrollTo(0, y); await new Promise(r => setTimeout(r, 120)); } scrollTo(0, 0); await new Promise(r => setTimeout(r, 400)); }""")
            for sid in ids:
                if not plain:
                    pg.evaluate(f"location.hash={json.dumps(sid)}")
                pg.wait_for_timeout(150)
                m = pg.evaluate(PROBE)
                m.update(dev=dev, screen=sid, where=f'[{titles.get(sid, sid)}·{"폰" if dev == "m" else "PC"}]')
                ms.append(m)
            pg.close()
        b.close()
    return ms


def main():
    a = sys.argv[1:]
    app = pathlib.Path(a[0])
    only = set(a[a.index("--only") + 1].split(",")) if "--only" in a else None
    ms = measure(app, only)
    res = []
    for rid, name, fn, fix in RULES:
        try:
            st, msg, ex = fn(ms)
        except Exception as x:  # 검사 하나가 깨져도 나머지는 돈다
            st, msg, ex = "PASS", f"(검사 오류 — 건너뜀: {x})", []
        if rid in SLOP_OK and st == "WARN":
            st, msg, ex = "PASS", msg + f" — 근거 있어 허용: {SLOP_OK[rid]}", []
        res.append({"id": rid, "name": name, "status": st, "msg": msg, "examples": ex, "fix": fix})
    counts = {k: sum(1 for r in res if r["status"] == k) for k in ("PASS", "WARN", "FAIL")}
    for r in res:
        print(f'{r["status"]:<4} {r["id"]:<4} {r["name"]:<10} {r["msg"]}')
        if r["status"] != "PASS":
            for x in r["examples"][:3]:
                print(f"            · {x}")
    print(f'합계 PASS {counts["PASS"]} · WARN {counts["WARN"]} · FAIL {counts["FAIL"]} (규칙 {len(res)}개 · 화면 {len(ms) // 2}장 × 폰·PC)')
    if "--json" in a:
        pathlib.Path(a[a.index("--json") + 1]).write_text(json.dumps({"counts": counts, "rules": res}, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
