"""파운데이션 토큰 생성기 — 파라미터 몇 개로 색·타이포·여백 토큰 전체를 계산한다.

python3 derive.py --brand "#1B64DA" --tone neutral --shape normal --density comfy -o out/tokens.css

- 색: 포인트 색 1개 + 표면 톤(warm/neutral/cool)에서 글자·배경·선·틴트를 계산하고,
  모든 글자/배경 조합이 WCAG AA(4.5:1)를 넘도록 명도만 조정한다(채도는 유지 → 탁해지지 않음).
- 타이포: 폰트별 세트. 제목÷본문 ≥ 1.5, 굵기 차 ≥ 200. 큰 글자 화면(.text-large)은 본문 계열만 한 단계 크게 — 편집하지 않는 사람의 기본값. 역할 이름을 붙이지 않는다.
- 여백: 4pt 스케일 위 "넉넉한 기본값". 밀도 comfy/normal.
"""
import argparse, colorsys, sys, pathlib

def hex2rgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i+2], 16) / 255 for i in (0, 2, 4))
def rgb2hex(c): return "#" + "".join(f"{round(max(0, min(1, v)) * 255):02X}" for v in c)
def lum(c):
    f = lambda v: v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = map(f, c); return 0.2126 * r + 0.7152 * g + 0.0722 * b
def contrast(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True); return (la + 0.05) / (lb + 0.05)
def hls(h, l, s): return colorsys.hls_to_rgb(h / 360, l, s)
def darken_until(c, bg, target):
    h, l, s = colorsys.rgb_to_hls(*c)
    while contrast(colorsys.hls_to_rgb(h, l, s), bg) < target and l > 0.02: l -= 0.01
    return colorsys.hls_to_rgb(h, l, s)
def mix(a, b, t): return tuple(x * (1 - t) + y * t for x, y in zip(a, b))

TONES = {  # (hue, 채도) — 무채색에 아주 옅은 온도만 준다
    "warm": (32, 0.14), "neutral": (220, 0.03), "cool": (215, 0.14)}
SHAPES = {"sharp": (4, 8, 12), "normal": (8, 12, 16), "round": (10, 16, 24)}
DENSITY = {  # page-x, block-pad, block-gap, row-py, stack-s, stack-m, stack-l
    "comfy": (24, 24, 12, 16, 8, 16, 32), "normal": (20, 20, 12, 12, 8, 12, 24)}
FONTS = {
    "pretendard": {
        "import": "https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css",
        "family": "'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif",
        "tracking": "-0.02em",
        # 역할: (크기, 굵기, 줄간격)
        "base":   {"title": (28, 700, 1.36), "h2": (20, 700, 1.4), "body": (16, 400, 1.55),
                   "strong": (16, 600, 1.5), "sub": (14, 400, 1.5), "caption": (12, 500, 1.4)},
        "large": {"title": (28, 700, 1.36), "h2": (20, 700, 1.4), "body": (18, 400, 1.55),
                   "strong": (18, 600, 1.5), "sub": (16, 400, 1.5), "caption": (14, 500, 1.4)},
    }
}


def hue_deg(c): return colorsys.rgb_to_hls(*c)[0] * 360
def hue_gap(a, b): d = abs(hue_deg(a) - hue_deg(b)) % 360; return min(d, 360 - d)
def sat_of(c): return colorsys.rgb_to_hls(*c)[2]

STATUS = {"success": (140, "#1F9D55"), "warning": (42, "#E8A100"), "info": (215, "#2F80ED")}

def extend_roles(c, notes, S=None, P=None, mono=False):
    """13개 기본 역할 → 표면·글자·선·브랜드 상태·의미색 4종·비활성·그림자까지 확장.
    팔레트(S)에 해당 계열 스케일이 있으면 그 서비스 값을 쓰고, 없으면 공용 기본값.
    의미색이 브랜드와 색상각이 가까우면(<25°) 피해 간다 — '확정'과 '바뀜'이 같은 색이 되지 않게."""
    white, bg, ink, brand = c["surface"], c["bg"], c["text1"], c["brand"]
    order = lambda sc: sorted(sc, key=int)
    def scale_near(target):
        best = None
        for k, sc in (S or {}).items():
            if P and k in (P.get("gray"), P.get("brand")): continue
            mid = sc[order(sc)[len(sc) // 2]]
            if sat_of(mid) < .3: continue
            d = min(abs(hue_deg(mid) - target), 360 - abs(hue_deg(mid) - target))
            if d < 30 and (best is None or d < best[0]): best = (d, k)
        return best[1] if best else None
    def from_scale(k, base):
        if k:
            sc = S[k]; fg = next((sc[st] for st in order(sc) if contrast(sc[st], white) >= 4.5), sc[order(sc)[-1]])
            light = sc[order(sc)[0]]; tint = light if contrast(light, white) < 1.2 else mix(white, fg, .1)
        else:
            fg = darken_until(base, white, 4.5); tint = mix(white, base, .1)
        return fg, tint, darken_until(fg, tint, 4.5)
    out = {}
    brand_chroma = not mono and sat_of(brand) > .25
    for name, (h, default) in STATUS.items():
        k = scale_near(h); base = hex2rgb(default)
        fg, tint, tint_text = from_scale(k, base)
        if brand_chroma and hue_gap(fg, brand) < 25:
            if name == "warning":           # 주황 브랜드 → 주의는 노랑 쪽으로
                fg, tint, tint_text = from_scale(None, hex2rgb("#C9A100")); notes.append("주의색이 브랜드와 겹쳐 노랑 쪽으로 이동")
            else:                           # 파랑 브랜드의 정보, 초록 브랜드의 성공 → 무채색으로
                fg, tint, tint_text = c["text2"], bg, c["text1"]; notes.append(f"{name}색이 브랜드와 겹쳐 무채색 배지로")
        out[name], out[name + "_tint"], out[name + "_tint_text"] = fg, tint, tint_text
    out["danger_tint_text"] = darken_until(c["danger"], c["danger_tint"], 4.5)
    out["danger_icon"] = brand_chroma and hue_gap(c["danger"], brand) < 25
    if out["danger_icon"]: notes.append("브랜드와 오류 색상각이 가까움 → 오류 문구에 아이콘 필수(.field-msg 아이콘)")
    # 브랜드 눌림: 스케일의 한 단계 짙은 값, 없으면 명도 -8%
    if S and P and not mono:
        sc = S[P["brand"]]; st = order(sc); i = st.index(P["brand_step"]) if P["brand_step"] in st else -1
        out["brand_pressed"] = sc[st[min(i + 1, len(st) - 1)]] if i >= 0 else mix(brand, ink, .12)
    else:
        out["brand_pressed"] = mix(brand, white, .18) if mono else mix(brand, ink, .12)
    def gray_at(lo, hi, target):
        t = 0.0
        while t < 1 and contrast(mix(white, ink, t), white) < target: t += 0.01
        return mix(white, ink, t)
    out["line_strong"] = gray_at(1.5, 2.2, 1.8)
    out["text_disabled"] = gray_at(2.3, 3.2, 2.6)
    out["disabled_bg"] = c["line"]
    out["focus"] = c["brand_text"]
    r, g, b = (round(x * 255) for x in ink)
    out["overlay"] = f"rgba({r}, {g}, {b}, .45)"
    sh = [v for v in (P or {}).get("shadows", {}).values() if "var(" not in v][:2] if P else []
    out["shadow_1"] = sh[0] if len(sh) > 0 else f"0 2px 8px rgba({r}, {g}, {b}, .08)"
    out["shadow_2"] = sh[1] if len(sh) > 1 else f"0 8px 24px rgba({r}, {g}, {b}, .14)"
    c.update(out)
    return c

def from_palette(path):
    """실제 서비스 팔레트(palettes/*.json)에서 역할 색을 고른다. 새 값을 만들지 않고 팔레트 단계 중
    대비 기준을 통과하는 가장 밝은 단계를 쓴다. 반환: (색 dict, 버튼 큰 글자 필요 여부, 노트)"""
    import json
    P = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    S = {k: {st: hex2rgb(h) for st, h in sc.items()} for k, sc in P["scales"].items()}
    order = lambda sc: sorted(sc, key=lambda st: int(st))            # 밝음 → 짙음
    def first_pass(scale, bg, target):
        for st in order(S[scale]):
            if contrast(S[scale][st], bg) >= target: return S[scale][st]
        return S[scale][order(S[scale])[-1]]
    G = P.get("gray", "gray"); B = P["brand"]; D = P.get("danger")
    white = hex2rgb(P["white"]); bg = S[G][P["bg_step"]]; line = S[G][P["line_step"]]
    brand = S[B][P["brand_step"]]
    lightest = lambda k: S[k][order(S[k])[0]]
    if P.get("mono"):                                   # 모노: 틴트는 배경 회색, 강조 글자는 먹색
        tint = bg
    else:
        steps = order(S[B]); tint = S[B]["80"] if "80" in S[B] else (S[B][steps[1]] if contrast(lightest(B), white) < 1.1 else mix(white, brand, .1))
    danger_scale = D if D else None
    ink = hex2rgb(P["ink"])
    def gray_for(target, lo, hi):
        """팔레트 회색 중 대비가 [lo, hi]인 가장 밝은 단계. 없으면(측정 합성 팔레트에 중간 회색이 비는 경우)
        먹색과 배경 사이를 섞어 목표 대비에 맞춘다 — 보조 글자가 본문과 같은 색이 되어 위계가 무너지는 것 방지."""
        for st in order(S[G]):
            k = contrast(S[G][st], bg)
            if lo <= k <= hi: return S[G][st]
        t = 0.0
        while t < 1 and contrast(mix(bg, ink, t), bg) < target: t += 0.01
        notes.append(f"회색 {target}:1 단계가 팔레트에 없어 먹색·배경 사이에서 계산")
        return mix(bg, ink, t)
    notes = list(P.get("notes", []))
    c = {"bg": bg, "surface": white, "line": line, "text1": hex2rgb(P["ink"]),
         "text2": gray_for(7.5, 7, 10), "text3": gray_for(4.8, 4.5, 6.2),
         "brand": brand, "brand_text": first_pass(B, white, 4.5),
         "brand_tint": tint, "brand_tint_text": first_pass(B, tint, 4.5),
         "danger": first_pass(danger_scale, white, 4.5) if danger_scale else darken_until(hex2rgb("#E5484D"), white, 4.5),
         "danger_tint": lightest(danger_scale) if danger_scale else mix(white, hex2rgb("#E5484D"), .08)}
    notes += []
    big = False
    if contrast(white, brand) >= 4.5: c["on_brand"] = white
    elif contrast(white, brand) >= 3:                                   # 채워진 버튼은 흰 글자가 자연스럽다 → 큰 굵은 글자로 AA-large
        c["on_brand"] = white; big = True; notes.append(f"버튼: 흰 글자 대비 {contrast(white, brand):.2f} → 버튼 글자 19px/700(큰 글씨 기준 3:1)")
    else:
        c["on_brand"] = white; c["brand"] = first_pass(P["brand"], white, 3); big = True; notes.append("버튼 색을 팔레트 안에서 한 단계 짙게")
    extend_roles(c, notes, S, P, P.get("mono", False))
    return c, big, notes, P

def derive(brand_hex, tone, shape, density, font, palette=None):
    if palette:
        c, big, notes, P = from_palette(palette)
        return render_css(c, big, notes, f"palette {P['name']}", shape, density, font)
    th, ts = TONES[tone]
    surface = hls(th, 0.995 if tone != "neutral" else 1.0, ts)
    bg = hls(th, 0.955, ts + 0.04)
    line = hls(th, 0.915, ts + 0.02)
    text1 = darken_until(hls(th, 0.13, ts * 0.8 + 0.08), bg, 12)      # 순검정이 아닌 짙은 색
    text2 = darken_until(hls(th, 0.36, ts * 0.6 + 0.05), bg, 7)
    text3 = darken_until(hls(th, 0.47, ts * 0.5 + 0.04), bg, 4.5)     # 가장 옅은 글자도 AA
    brand = hex2rgb(brand_hex)
    notes = []
    if contrast((1, 1, 1), brand) >= 4.5: on_brand = (1, 1, 1)
    elif contrast(text1, brand) >= 4.5: on_brand = text1                   # 노랑처럼 밝은 포인트
    else:
        nb = darken_until(brand, (1, 1, 1), 4.5); notes.append(f"brand {brand_hex}→{rgb2hex(nb)} (흰 글자 대비 확보)")
        brand, on_brand = nb, (1, 1, 1)
    brand_text = darken_until(brand, surface, 4.5)                 # 포인트 색을 글자로 쓸 때
    brand_tint = mix(surface, brand, 0.10)
    brand_tint_text = darken_until(brand, brand_tint, 4.5)
    danger = darken_until(hex2rgb("#E5484D"), surface, 4.5)
    danger_tint = mix(surface, hex2rgb("#E5484D"), 0.08)
    c = {"bg": bg, "surface": surface, "line": line, "text1": text1, "text2": text2, "text3": text3,
         "brand": brand, "on_brand": on_brand, "brand_text": brand_text, "brand_tint": brand_tint,
         "brand_tint_text": brand_tint_text, "danger": danger, "danger_tint": danger_tint}
    extend_roles(c, notes)
    return render_css(c, False, notes, f"--brand {brand_hex} --tone {tone}", shape, density, font)

def render_css(c, big, notes, label, shape, density, font):
    bg, surface, line, text1, text2, text3 = c["bg"], c["surface"], c["line"], c["text1"], c["text2"], c["text3"]
    brand, on_brand, brand_text, brand_tint, brand_tint_text = c["brand"], c["on_brand"], c["brand_text"], c["brand_tint"], c["brand_tint_text"]
    danger, danger_tint = c["danger"], c["danger_tint"]
    r = SHAPES[shape]; d = DENSITY[density]; f = FONTS[font]
    checks = {
        "text-1/bg": contrast(text1, bg), "text-2/bg": contrast(text2, bg), "text-3/bg": contrast(text3, bg),
        "text-3/surface": contrast(text3, surface), ("on-brand/brand(큰 글씨 ≥3)" if big else "on-brand/brand"): contrast(on_brand, brand),
        "brand-text/surface": contrast(brand_text, surface), "tint-text/tint": contrast(brand_tint_text, brand_tint),
        "danger/surface": contrast(danger, surface),
        "success/surface": contrast(c["success"], surface), "warning-tint-text/tint": contrast(c["warning_tint_text"], c["warning_tint"]),
        "info-tint-text/tint": contrast(c["info_tint_text"], c["info_tint"]), "success-tint-text/tint": contrast(c["success_tint_text"], c["success_tint"]),
        "danger-tint-text/tint": contrast(c["danger_tint_text"], c["danger_tint"])}
    def typo(scale):
        return "\n".join(f"  --fs-{k}: {v[0]}px; --fw-{k}: {v[1]}; --lh-{k}: {v[2]};" for k, v in scale.items())
    css = f"""/* foundation tokens — derive.py {label} --shape {shape} --density {density} --font {font}
   이 파일은 생성물이다. 직접 고치지 말고 파라미터를 바꿔 다시 만든다. */
@import url('{f["import"]}');

:root {{
  /* 색 — {label} */
  --c-bg: {rgb2hex(bg)};
  --c-surface: {rgb2hex(surface)};
  --c-line: {rgb2hex(line)};
  --c-text-1: {rgb2hex(text1)};
  --c-text-2: {rgb2hex(text2)};
  --c-text-3: {rgb2hex(text3)};
  --c-brand: {rgb2hex(brand)};
  --c-on-brand: {rgb2hex(on_brand)};
  --c-brand-text: {rgb2hex(brand_text)};
  --c-brand-tint: {rgb2hex(brand_tint)};
  --c-brand-tint-text: {rgb2hex(brand_tint_text)};
  --c-danger: {rgb2hex(danger)};
  --c-danger-tint: {rgb2hex(danger_tint)};
  --c-danger-tint-text: {rgb2hex(c["danger_tint_text"])};

  /* 의미색 — 확정(브랜드)·바뀜(주의)·안내(정보)·완료(성공)가 같은 색이 되지 않게 */
  --c-success: {rgb2hex(c["success"])}; --c-success-tint: {rgb2hex(c["success_tint"])}; --c-success-tint-text: {rgb2hex(c["success_tint_text"])};
  --c-warning: {rgb2hex(c["warning"])}; --c-warning-tint: {rgb2hex(c["warning_tint"])}; --c-warning-tint-text: {rgb2hex(c["warning_tint_text"])};
  --c-info: {rgb2hex(c["info"])}; --c-info-tint: {rgb2hex(c["info_tint"])}; --c-info-tint-text: {rgb2hex(c["info_tint_text"])};

  /* 상호작용·비활성·겹침 */
  --c-brand-pressed: {rgb2hex(c["brand_pressed"])};
  --c-focus: {rgb2hex(c["focus"])};
  --c-line-strong: {rgb2hex(c["line_strong"])};
  --c-text-disabled: {rgb2hex(c["text_disabled"])};
  --c-disabled-bg: {rgb2hex(c["disabled_bg"])};
  --c-overlay: {c["overlay"]};
  --shadow-1: {c["shadow_1"]};
  --shadow-2: {c["shadow_2"]};

  /* 타이포 — {font} */
  --font: {f["family"]};
  --tracking: {f["tracking"]};
{typo(f["base"])}

  /* 여백 — {density} */
  --page-x: {d[0]}px;
  --block-pad: {d[1]}px;
  --block-gap: {d[2]}px;
  --row-py: {d[3]}px;
  --stack-s: {d[4]}px;
  --stack-m: {d[5]}px;
  --stack-l: {d[6]}px;

  /* 모양 — {shape} */
  --r-s: {r[0]}px;
  --r-m: {r[1]}px;
  --r-l: {r[2]}px;
  --r-pill: 999px;

  /* 크기 */
  --h-appbar: 56px; --h-btn: 56px; --h-btn-s: 44px; --h-tab: 64px; --h-row: 64px; --icon: 24px;
}}

/* 큰 글자: 편집하지 않는 사람의 기본값(화면에 표시 없음) */
.text-large {{
{typo(f["large"])}
}}
"""
    if big:
        css += "\n/* 버튼: 흰 글자 대비가 4.5 미만 → 큰 굵은 글자(19px/700)로 WCAG 큰 글씨 기준(3:1) 충족 */\n.btn.primary { font-size: 19px; font-weight: 700; }\n"
    return css, checks, notes

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--brand"); ap.add_argument("--palette", help="palettes/*.json — 실제 서비스 팔레트에서 역할 색을 고른다"); ap.add_argument("--tone", default="neutral", choices=TONES)
    ap.add_argument("--shape", default="normal", choices=SHAPES); ap.add_argument("--density", default="comfy", choices=DENSITY)
    ap.add_argument("--font", default="pretendard", choices=FONTS); ap.add_argument("-o", "--out", required=True)
    a = ap.parse_args()
    css, checks, notes = derive(a.brand, a.tone, a.shape, a.density, a.font, a.palette)
    pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True); pathlib.Path(a.out).write_text(css, encoding="utf-8")
    bad = {k: v for k, v in checks.items() if v < (3 if "큰 글씨" in k else 4.5)}
    print(f"wrote {a.out}", *notes, sep="\n")
    print("대비:", ", ".join(f"{k} {v:.1f}" for k, v in checks.items()))
    sys.exit(1 if bad else 0)
