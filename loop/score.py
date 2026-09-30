#!/usr/bin/env python3
"""하네스 산출물(OUT) 정량 채점기. docs/success-criteria.md 기준.

usage: python3 loop/score.py OUT [--shots SHOTDIR] [--json out.json]
"""
import argparse, colorsys, json, os, re, sys
from collections import deque
from pathlib import Path
from urllib.parse import urlparse, unquote

ALLOWED_STATES = {"empty", "error", "disabled"}
VIEWPORT = {"width": 375, "height": 812}

MEASURE_JS = r"""
() => {
  const W = 375;
  const parseColor = (s) => {
    if (!s) return null;
    let m = s.match(/rgba?\(([^)]+)\)/);
    if (m) {
      const p = m[1].split(/[\s,\/]+/).filter(Boolean).map(parseFloat);
      return [p[0], p[1], p[2], p.length > 3 ? p[3] : 1];
    }
    m = s.match(/color\(srgb ([^)]+)\)/);
    if (m) {
      const p = m[1].split(/[\s\/]+/).filter(Boolean).map(parseFloat);
      return [p[0]*255, p[1]*255, p[2]*255, p.length > 3 ? p[3] : 1];
    }
    return null;
  };
  const allColors = (s) => {
    const out = [];
    const re = /rgba?\([^)]+\)|color\(srgb [^)]+\)/g; let m;
    while ((m = re.exec(s||''))) { const c = parseColor(m[0]); if (c) out.push(c); }
    return out;
  };
  const isChroma = (c) => {
    const r=c[0]/255,g=c[1]/255,b=c[2]/255, mx=Math.max(r,g,b), mn=Math.min(r,g,b), l=(mx+mn)/2;
    const s = mx===mn ? 0 : (l > 0.5 ? (mx-mn)/(2-mx-mn) : (mx-mn)/(mx+mn));
    return c[3] > 0 && s > 0.2 && l >= 0.1 && l <= 0.95;
  };
  const lum = (c) => { const f = v => { v/=255; return v <= 0.03928 ? v/12.92 : Math.pow((v+0.055)/1.055, 2.4); };
    return 0.2126*f(c[0]) + 0.7152*f(c[1]) + 0.0722*f(c[2]); };
  const blend = (fg, bg) => { const a = fg[3]; return [fg[0]*a+bg[0]*(1-a), fg[1]*a+bg[1]*(1-a), fg[2]*a+bg[2]*(1-a), 1]; };
  const px = v => parseFloat(v) || 0;
  const visible = (el, cs) => {
    if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) === 0) return false;
    const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0;
  };
  const directText = (el) => { let t = ''; for (const n of el.childNodes) if (n.nodeType === 3) t += n.textContent; return t.trim(); };

  const res = { colors: [], fontSizes: [], weights: [], families: [], spacing: [], radii: [], shadows: [],
    textSizes: [], contrastFails: [], touch: {total: 0, ok: 0, fails: []}, primary: [], h1: 0, help: [],
    emoji: [], gradients: [], textGradient: 0, cardDeep: 0, boxTotal: 0, boxRadius: 0,
    placeholders: [], brokenImgs: [], scrollWidth: document.documentElement.scrollWidth };
  const cardSet = new Set();
  const els = Array.from(document.body ? document.body.querySelectorAll('*') : []);
  els.unshift(document.body);
  const emojiRe = /[\u{1F300}-\u{1FAFF}\u{1F000}-\u{1F2FF}\u{2600}-\u{27BF}\u{1F900}-\u{1F9FF}\u{FE0F}]/u;
  const phRe = /lorem|ipsum|\bTODO\b|\bTBD\b|placeholder|플레이스홀더/i;
  const phExact = /^(텍스트|제목|내용|Title|Text|Heading|(여행|항목|아이템|Item|카드|Card|User|사용자) ?\d+)$/i;

  for (const el of els) {
    if (!el || ['SCRIPT','STYLE','NOSCRIPT','TEMPLATE','HEAD','META','LINK','TITLE'].includes(el.tagName)) continue;
    const cs = getComputedStyle(el);
    if (!visible(el, cs)) continue;
    const tag = el.tagName;
    const txt = directText(el);
    // colors
    const bg = parseColor(cs.backgroundColor);
    if (bg && bg[3] > 0) res.colors.push(bg);
    if (px(cs.borderTopWidth)+px(cs.borderRightWidth)+px(cs.borderBottomWidth)+px(cs.borderLeftWidth) > 0) {
      for (const k of ['borderTopColor','borderRightColor','borderBottomColor','borderLeftColor']) {
        const w = px(cs[k.replace('Color','Width')]); const c = parseColor(cs[k]); if (w > 0 && c && c[3] > 0) res.colors.push(c);
      }
    }
    if (txt) {
      const fc = parseColor(cs.color); if (fc) res.colors.push(fc);
      const fs = px(cs.fontSize);
      res.fontSizes.push(fs); res.weights.push(cs.fontWeight);
      res.families.push((cs.fontFamily.split(',')[0] || '').replace(/["']/g, '').trim().toLowerCase());
      res.textSizes.push(fs);
      if (emojiRe.test(txt)) res.emoji.push(txt.slice(0, 30));
      if (phRe.test(txt) || phExact.test(txt)) res.placeholders.push(txt.slice(0, 40));
      if (txt === '?' || txt === '？') res.help.push('text:?');
      // contrast
      let a = el, bgc = null, img = false;
      while (a && a.nodeType === 1) {
        const acs = getComputedStyle(a);
        if (acs.backgroundImage && acs.backgroundImage !== 'none') { img = true; break; }
        const c = parseColor(acs.backgroundColor);
        if (c && c[3] >= 0.99) { bgc = c; break; }
        a = a.parentElement;
      }
      if (!img && fc) {
        bgc = bgc || [255,255,255,1];
        const f = fc[3] < 1 ? blend(fc, bgc) : fc;
        const L1 = lum(f), L2 = lum(bgc);
        const ratio = (Math.max(L1,L2)+0.05)/(Math.min(L1,L2)+0.05);
        const bold = parseInt(cs.fontWeight) >= 700;
        const need = (fs >= 24 || (bold && fs >= 18.66)) ? 3 : 4.5;
        if (ratio + 1e-6 < need) res.contrastFails.push(`${tag.toLowerCase()} "${txt.slice(0,20)}" ${ratio.toFixed(2)}<${need}`);
      }
    }
    // spacing
    for (const k of ['paddingTop','paddingRight','paddingBottom','paddingLeft','marginTop','marginBottom','rowGap','columnGap']) {
      const v = px(cs[k]); if (v) res.spacing.push(v);
    }
    const ml = px(cs.marginLeft), mr = px(cs.marginRight);
    const autoCenter = ml > 0 && Math.abs(ml - mr) < 1 && el.parentElement &&
      Math.abs(el.getBoundingClientRect().width + ml + mr - el.parentElement.clientWidth
        + px(getComputedStyle(el.parentElement).paddingLeft) + px(getComputedStyle(el.parentElement).paddingRight)) < 2;
    if (!autoCenter) { if (ml) res.spacing.push(ml); if (mr) res.spacing.push(mr); }
    // radius / shadow / box
    const rad = px(cs.borderTopLeftRadius);
    const radKey = [cs.borderTopLeftRadius, cs.borderTopRightRadius, cs.borderBottomRightRadius, cs.borderBottomLeftRadius].join(' ');
    if (rad > 0 || px(cs.borderBottomRightRadius) > 0) res.radii.push(radKey);
    if (cs.boxShadow && cs.boxShadow !== 'none') res.shadows.push(cs.boxShadow);
    const hasBg = bg && bg[3] > 0, hasBorder = px(cs.borderTopWidth)+px(cs.borderLeftWidth)+px(cs.borderRightWidth)+px(cs.borderBottomWidth) > 0;
    const hasShadow = cs.boxShadow && cs.boxShadow !== 'none';
    const isBox = (hasBg || hasBorder || hasShadow) && el !== document.body;
    const anyRad = rad > 0 || px(cs.borderTopRightRadius) > 0 || px(cs.borderBottomRightRadius) > 0 || px(cs.borderBottomLeftRadius) > 0;
    if (isBox) { res.boxTotal++; if (anyRad) res.boxRadius++; }
    if (isBox && anyRad && !['BUTTON','INPUT','SELECT','TEXTAREA','IMG','A','LABEL','SPAN'].includes(tag)) {
      cardSet.add(el);
      let d = 1, p = el.parentElement; while (p) { if (cardSet.has(p)) d++; p = p.parentElement; }
      if (d >= 3) res.cardDeep++;
    }
    // gradients
    if (cs.backgroundImage && /gradient/.test(cs.backgroundImage) && allColors(cs.backgroundImage).some(isChroma))
      res.gradients.push(tag.toLowerCase());
    if ((cs.webkitBackgroundClip || cs.backgroundClip || '').includes('text')) res.textGradient++;
    // h1 / help
    if (tag === 'H1') res.h1++;
    if (el.hasAttribute('title') && el !== document.body) res.help.push('title:' + tag.toLowerCase());
    if (/tooltip|help/i.test(el.getAttribute('class') || '')) res.help.push('class:' + el.getAttribute('class'));
    if (/(^|\s)badge(\s|$)/.test(el.getAttribute('class') || '')) { res.badges = res.badges || []; res.badges.push([(el.innerText||'').trim().slice(0,20), cs.backgroundColor]); }
    // touch
    const interactive = el.matches('a[href],button,[role=button],input:not([type=hidden]),select,textarea');
    if (interactive) {
      let inlineLink = false;
      if (tag === 'A' && cs.display === 'inline' && el.parentElement) {
        const sib = directText(el.parentElement); if (sib.length > 0) inlineLink = true;
      }
      if (!inlineLink) {
        const r = el.getBoundingClientRect();
        res.touch.total++;
        if (r.width >= 43.5 && r.height >= 43.5) res.touch.ok++;
        else res.touch.fails.push(`${tag.toLowerCase()} "${(el.innerText||el.value||'').trim().slice(0,15)}" ${Math.round(r.width)}x${Math.round(r.height)}`);
      }
      if (el.matches('button,a,[role=button],input[type=submit],input[type=button]') && !el.matches('[aria-pressed=true],[aria-selected=true],[aria-checked=true],[aria-current],.is-selected,.selected') && bg && isChroma(bg))
        res.primary.push((el.innerText || el.value || '').trim().slice(0, 20));
    }
    if (tag === 'IMG' && el.complete && el.naturalWidth === 0) res.brokenImgs.push(el.getAttribute('src') || '');
  }
  // 하단 고정 영역: 링크 3개 이상이면 탭바, 강조색 버튼이 있으면 고정 CTA
  res.fixedCta = []; res.hasTabbar = false;
  for (const el of document.querySelectorAll('body *')) {
    const pcs = getComputedStyle(el);
    if (pcs.position !== 'fixed') continue;
    const r = el.getBoundingClientRect();
    if (r.top < innerHeight - 200) continue;
    const acts = el.querySelectorAll('a,button');
    if (acts.length >= 3) { res.hasTabbar = true; continue; }
    for (const b of acts) {
      const bg = parseColor(getComputedStyle(b).backgroundColor);
      if (bg && bg[3] > 0.5 && isChroma(bg)) res.fixedCta.push((b.innerText || '').trim().slice(0, 30));
    }
  }
  return res;
}
"""


def rgb_hsl(c):
    h, l, s = colorsys.rgb_to_hls(c[0] / 255, c[1] / 255, c[2] / 255)
    return h * 360, s, l


def is_chroma(c):
    h, s, l = rgb_hsl(c)
    return c[3] > 0 and s > 0.2 and 0.1 <= l <= 0.95


def parse_css_color(v):
    """'rgb(1, 2, 3)' / 'rgba(1, 2, 3, .5)' → (r, g, b, a)"""
    m = re.findall(r"[\d.]+", v or "")
    if len(m) < 3: return None
    return (float(m[0]), float(m[1]), float(m[2]), float(m[3]) if len(m) > 3 else 1.0)


HREF_RE = re.compile(r'''(?:href|src)\s*=\s*["']([^"']+)["']''', re.I)


def local_refs(path: Path):
    """html 파일 안의 a[href] / iframe[src] 로컬 참조 (절대경로 Path 목록)."""
    try:
        html = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []
    out = []
    for m in re.finditer(r'<(a|iframe)\b[^>]*?(?:href|src)\s*=\s*["\']([^"\']+)["\']', html, re.I):
        u = m.group(2).strip()
        if not u or u.startswith(("#", "javascript:", "mailto:", "tel:", "data:")):
            continue
        pu = urlparse(u)
        if pu.scheme in ("http", "https"):
            continue
        p = unquote(pu.path)
        if not p:
            continue
        out.append((u, (path.parent / p).resolve()))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--shots")
    ap.add_argument("--json")
    args = ap.parse_args()
    OUT = Path(args.out).resolve()
    checks = []

    def add(group, cid, value, threshold, ok, detail=""):
        checks.append(dict(id=cid, group=group, value=value, threshold=threshold, pass_=bool(ok), detail=detail))

    # ---------- manifest ----------
    manifest, mf_err = None, ""
    try:
        manifest = json.loads((OUT / "screens.json").read_text(encoding="utf-8"))
        assert isinstance(manifest.get("screens"), list)
    except Exception as e:
        manifest, mf_err = None, f"manifest 오류: {e}"
    mscreens = {}
    if manifest:
        for s in manifest["screens"]:
            if isinstance(s, dict) and s.get("id"):
                mscreens[s["id"]] = s

    screens_dir = OUT / "screens"
    files = sorted(screens_dir.glob("*.html")) if screens_dir.is_dir() else []
    base_files = [f for f in files if "--" not in f.stem]
    variants = {}  # base id -> set(states)
    for f in files:
        if "--" in f.stem:
            b, st = f.stem.split("--", 1)
            variants.setdefault(b, set()).add(st)

    # ---------- 완결성 (정적) ----------
    add("완결성", "screen_count", len(base_files), ">=10", len(base_files) >= 10,
        ", ".join(f.stem for f in base_files))
    cov = (manifest or {}).get("prd_coverage")
    if isinstance(cov, dict) and cov:
        empty = [k for k, v in cov.items() if not v]
        add("완결성", "prd_coverage", f"{len(cov)-len(empty)}/{len(cov)}", "100%", not empty,
            "비어있음: " + ",".join(empty) if empty else "")
    else:
        add("완결성", "prd_coverage", "n/a", "100%", False, mf_err or "prd_coverage 없음")

    index = OUT / "index.html"
    seen, q = set(), deque()
    dead = []
    if index.exists():
        q.append(index.resolve()); seen.add(index.resolve())
    while q:
        cur = q.popleft()
        for u, tgt in local_refs(cur):
            if not tgt.exists():
                dead.append(f"{cur.name}->{u}")
                continue
            if tgt.suffix == ".html" and tgt not in seen:
                seen.add(tgt); q.append(tgt)
    unreached = [f.stem for f in base_files if f.resolve() not in seen]
    add("완결성", "reachability", f"{len(base_files)-len(unreached)}/{len(base_files)}", "100%",
        index.exists() and not unreached and base_files,
        ("index.html 없음 " if not index.exists() else "") + ("미도달: " + ",".join(unreached) if unreached else ""))
    # 도달 못한 파일도 데드링크 검사
    for f in files:
        if f.resolve() not in seen:
            for u, tgt in local_refs(f):
                if not tgt.exists():
                    dead.append(f"{f.name}->{u}")
    dead = sorted(set(dead))
    add("완결성", "dead_links", len(dead), "0", not dead, "; ".join(dead[:10]))

    # ---------- 상태 (정적) ----------
    if manifest:
        missing, excess, over = [], [], []
        for f in base_files:
            s = mscreens.get(f.stem, {})
            tr = s.get("traits") or {}
            exp = set()
            if tr.get("list_first_use"): exp.add("empty")
            if tr.get("form") or tr.get("sends"): exp.add("error")
            if tr.get("readonly_role"): exp.add("disabled")
            have = variants.get(f.stem, set())
            declared = set(s.get("states") or [])
            for st in exp - have:
                missing.append(f"{f.stem}--{st}")
            for st in (have | declared) - exp:
                excess.append(f"{f.stem}--{st}")
            if 1 + len(have | declared) > 3:
                over.append(f.stem)
        for b, sts in variants.items():
            for st in sts:
                if st not in ALLOWED_STATES:
                    excess.append(f"{b}--{st}(금지)")
                if b not in {f.stem for f in base_files}:
                    excess.append(f"{b}--{st}(기본화면 없음)")
        excess = sorted(set(excess))
        add("상태", "state_missing", len(missing), "0", not missing, ", ".join(missing))
        add("상태", "state_excess", len(excess), "0", not excess, ", ".join(excess))
        add("상태", "state_cap", len(over), "0 (화면당 ≤3)", not over, ", ".join(over))
    else:
        for cid in ("state_missing", "state_excess", "state_cap"):
            add("상태", cid, "n/a", "0", False, mf_err)

    # ---------- 렌더 측정 ----------
    from playwright.sync_api import sync_playwright
    per = {}
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome")
        except Exception:
            browser = p.chromium.launch()
        ctx = browser.new_context(viewport=VIEWPORT, device_scale_factor=1)
        shots = Path(args.shots) if args.shots else None
        if shots:
            shots.mkdir(parents=True, exist_ok=True)
        for f in files:
            page = ctx.new_page()
            errs = []
            page.on("console", lambda m, errs=errs: errs.append(m.text[:80]) if m.type == "error" else None)
            page.on("pageerror", lambda e, errs=errs: errs.append(str(e)[:80]))
            try:
                page.goto(f.resolve().as_uri(), wait_until="load", timeout=15000)
                page.wait_for_timeout(150)
                r = page.evaluate(MEASURE_JS)
                if shots:
                    page.screenshot(path=str(shots / f"{f.stem}.png"), full_page=True)
            except Exception as e:
                r = None
                errs.append(f"측정 실패: {e}"[:120])
            r = r or {}
            r["errors"] = errs
            per[f.stem] = r
            page.close()
        if shots and index.exists():
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            try:
                page.goto(index.resolve().as_uri(), wait_until="load", timeout=30000)
                page.wait_for_timeout(800)
                hgt = min(page.evaluate("document.documentElement.scrollHeight"), 16000)
                page.set_viewport_size({"width": 1440, "height": hgt})  # 화면 밖 iframe 도 그리게
                page.wait_for_timeout(2500)
                page.screenshot(path=str(shots / "index.png"), full_page=True)
            except Exception as e:
                print(f"index 스크린샷 실패: {e}", file=sys.stderr)
            page.close()
        browser.close()

    def agg(key):
        out = []
        for r in per.values():
            out += r.get(key, []) or []
        return out

    # placeholders
    ph = []
    for sid, r in per.items():
        ph += [f"{sid}: \"{t}\"" for t in r.get("placeholders", [])]
        ph += [f"{sid}: 깨진img {s}" for s in r.get("brokenImgs", [])]
        ph += [f"{sid}: console {e}" for e in r.get("errors", [])]
    add("완결성", "placeholders", len(ph), "0", not ph, "; ".join(ph[:8]))

    # 일관성
    colors = agg("colors")
    hues, grays = set(), set()
    for c in colors:
        if is_chroma(c):
            hues.add(int(rgb_hsl(c)[0] // 20))
        else:
            grays.add(tuple(int(round(v / 4) * 4) for v in c[:3]) + (round(c[3], 2),))
    add("일관성", "chromatic_colors", len(hues), "<=6", len(hues) <= 6,   # 브랜드 1 + 의미색 4(틴트가 인접 구간으로 갈릴 여유)
        "hue 구간: " + ",".join(f"{h*20}-{h*20+19}" for h in sorted(hues)))
    # 토큰 밖 유채색: 화면의 유채색은 전부 tokens*.css 값이어야 한다
    tok = set()
    for tf in OUT.rglob("tokens*.css"):
        for h in re.findall(r"#([0-9a-fA-F]{6})\b", tf.read_text(encoding="utf-8")):
            tok.add(tuple(int(h[k:k + 2], 16) for k in (0, 2, 4)))
    if tok:
        off = sorted({c[:3] for c in colors if is_chroma(c) and min(sum((a - b) ** 2 for a, b in zip(c[:3], t)) for t in tok) > 36})
        add("일관성", "off_token_colors", len(off), "0", not off, " ".join(f"rgb{x}" for x in off[:6]))
    # 의미 배지: 서로 다른 뜻의 배지 3개 이상이 한 색이면 실패(확정·바뀜·궁금해요가 전부 브랜드 틴트였던 문제)
    bmap = {}
    for sid, r in per.items():
        for t, bgc in r.get("badges", []) or []:
            if t: bmap.setdefault(bgc, set()).add(re.sub(r"\s*\d+$", "", t))
    worst = max(((bgc, v) for bgc, v in bmap.items() if (pc := parse_css_color(bgc)) and is_chroma(pc)), key=lambda x: len(x[1]), default=(None, set()))
    add("위계", "badge_semantic", len(worst[1]), "<=2 뜻/색", len(worst[1]) <= 2, f"{worst[0]}: {', '.join(sorted(worst[1]))}" if worst[0] else "")
    add("일관성", "gray_steps", len(grays), "<=6", len(grays) <= 6,
        " ".join(f"rgb{g[:3]}" + (f"a{g[3]}" if g[3] < 1 else "") for g in sorted(grays))[:300])
    fs = sorted({round(v, 1) for v in agg("fontSizes")})
    add("일관성", "font_sizes", len(fs), "<=7", len(fs) <= 7, ",".join(str(v) for v in fs))
    fw = sorted(set(agg("weights")))
    add("일관성", "font_weights", len(fw), "<=3", len(fw) <= 3, ",".join(fw))
    ff = sorted(set(agg("families")))
    add("일관성", "font_families", len(ff), "<=2", len(ff) <= 2, ",".join(ff))
    sp = [round(v) for v in agg("spacing") if round(v) != 0]
    bad = sorted({v for v in sp if v % 4})
    ratio = (sum(1 for v in sp if v % 4 == 0) / len(sp)) if sp else 1.0
    add("일관성", "spacing_4x", f"{ratio*100:.1f}%", ">=95%", ratio >= 0.95, "비4배수: " + ",".join(map(str, bad[:15])))
    rk = sorted(set(agg("radii")))
    add("일관성", "radius_kinds", len(rk), "<=4", len(rk) <= 4, " | ".join(rk)[:200])
    sk = sorted(set(agg("shadows")))
    add("일관성", "shadow_kinds", len(sk), "<=3", len(sk) <= 3, " | ".join(sk)[:200])

    # 가독성
    cf = [f"{sid}: {x}" for sid, r in per.items() for x in r.get("contrastFails", [])]
    add("가독성", "contrast_aa", len(cf), "0", not cf, "; ".join(cf[:6]))
    ts = agg("textSizes")
    mn = min(ts) if ts else 0
    add("가독성", "min_font", f"{mn}px", ">=12px", bool(ts) and mn >= 12)
    vsz = []
    for sid, r in per.items():
        base = sid.split("--")[0]
        if (mscreens.get(base) or {}).get("role") in ("viewer", "everyone"):
            vsz += r.get("textSizes", [])
    if vsz:
        vr = sum(1 for v in vsz if v >= 16) / len(vsz)
        add("가독성", "large_text_body_font", f"{vr*100:.1f}%", ">=90%", vr >= 0.9)
    else:
        add("가독성", "large_text_body_font", "n/a", ">=90%", True, "큰 글자 화면 없음")
    tt = sum(r.get("touch", {}).get("total", 0) for r in per.values())
    tok = sum(r.get("touch", {}).get("ok", 0) for r in per.values())
    tf = [f"{sid}: {x}" for sid, r in per.items() for x in r.get("touch", {}).get("fails", [])]
    add("가독성", "touch_target", f"{(tok/tt*100 if tt else 100):.1f}%", "100%", tok == tt, "; ".join(tf[:6]))
    ov = [f"{sid}({r.get('scrollWidth')})" for sid, r in per.items() if (r.get("scrollWidth") or 0) > 375]
    add("가독성", "h_overflow", len(ov), "0", not ov, ", ".join(ov))

    # 위계
    pc = [f"{sid}({len(r['primary'])}: {'/'.join(r['primary'][:3])})" for sid, r in per.items() if len(r.get("primary", [])) > 1]
    add("위계", "primary_cta", len(pc), "0화면 (화면당 ≤1)", not pc, "; ".join(pc[:6]))
    h1 = [f"{sid}({r.get('h1', 0)})" for sid, r in per.items() if r.get("h1", 0) != 1]
    add("위계", "h1_count", len(h1), "0화면 (화면당 =1)", not h1, ", ".join(h1))
    # 하단 고정 CTA: 탭 첫 화면(탭바 있음)에는 0, 문구는 확정 동사(보기·가기·열기로 끝나면 이동 링크)
    ct = [f"{sid}: {'/'.join(r['fixedCta'])}" for sid, r in per.items() if r.get("hasTabbar") and r.get("fixedCta")]
    add("위계", "cta_on_tab_root", len(ct), "0화면", not ct, "; ".join(ct[:6]))
    cl = [f"{sid}: {t}" for sid, r in per.items() for t in r.get("fixedCta", []) if re.search(r"(보기|가기|열기|이동)$", t)]
    add("위계", "cta_label_verb", len(cl), "0", not cl, "; ".join(cl[:6]))
    hi = [f"{sid}: {x}" for sid, r in per.items() for x in r.get("help", [])]
    add("위계", "help_icons", len(hi), "0", not hi, "; ".join(hi[:6]))

    # 슬롭
    em = [f"{sid}: {x}" for sid, r in per.items() for x in r.get("emoji", [])]
    add("슬롭", "emoji", len(em), "0", not em, "; ".join(em[:6]))
    gr = [f"{sid}: {x}" for sid, r in per.items() for x in r.get("gradients", [])]
    add("슬롭", "gradients", len(gr), "0", not gr, "; ".join(gr[:6]))
    tg = sum(r.get("textGradient", 0) for r in per.values())
    add("슬롭", "text_gradient", tg, "0", tg == 0)
    cn = [f"{sid}({r['cardDeep']})" for sid, r in per.items() if r.get("cardDeep", 0) > 0]
    add("슬롭", "card_nesting", len(cn), "0", not cn, ", ".join(cn))
    bt = sum(r.get("boxTotal", 0) for r in per.values())
    br = sum(r.get("boxRadius", 0) for r in per.values())
    add("슬롭", "radius_ratio", f"{(br/bt*100 if bt else 0):.1f}%", "(보고만)", True, f"{br}/{bt}")

    # ---------- 출력 ----------
    order = ["완결성", "상태", "일관성", "가독성", "위계", "슬롭"]
    checks.sort(key=lambda c: order.index(c["group"]))
    group = None
    for c in checks:
        if c["group"] != group:
            group = c["group"]; print(f"\n[{group}]")
        mark = "✅" if c["pass_"] else "❌"
        line = f"  {mark} {c['id']}: {c['value']} (기준 {c['threshold']})"
        if c["detail"] and not c["pass_"]:
            line += f"  — {c['detail']}"
        print(line)
    passed = sum(1 for c in checks if c["pass_"])
    total = len(checks)
    if args.json:
        data = {"checks": [{**{k: v for k, v in c.items() if k != "pass_"}, "pass": c["pass_"]} for c in checks],
                "passed": passed, "total": total}
        Path(args.json).write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"\nPASS {passed}/{total}")


if __name__ == "__main__":
    main()
