"""파운데이션 토큰 생성기 — 파라미터 몇 개로 색·타이포·여백 토큰 전체를 계산한다.

python3 derive.py --brand "#1B64DA" --tone neutral --shape normal --density comfy -o out/tokens.css

- 색: 포인트 색 1개 + 표면 톤(warm/neutral/cool)에서 글자·배경·선·틴트를 계산하고,
  모든 글자/배경 조합이 WCAG AA(4.5:1)를 넘도록 명도만 조정한다(채도는 유지 → 탁해지지 않음).
- 타이포: 폰트별 세트. 제목÷본문 ≥ 1.5, 굵기 차 ≥ 200. 보기 전용 역할(.is-viewer)은 본문 계열만 한 단계 크게.
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
        "viewer": {"title": (28, 700, 1.36), "h2": (20, 700, 1.4), "body": (18, 400, 1.55),
                   "strong": (18, 600, 1.5), "sub": (16, 400, 1.5), "caption": (14, 500, 1.4)},
    }
}

def derive(brand_hex, tone, shape, density, font):
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
    r = SHAPES[shape]; d = DENSITY[density]; f = FONTS[font]
    checks = {
        "text-1/bg": contrast(text1, bg), "text-2/bg": contrast(text2, bg), "text-3/bg": contrast(text3, bg),
        "text-3/surface": contrast(text3, surface), "on-brand/brand": contrast(on_brand, brand),
        "brand-text/surface": contrast(brand_text, surface), "tint-text/tint": contrast(brand_tint_text, brand_tint),
        "danger/surface": contrast(danger, surface)}
    def typo(scale):
        return "\n".join(f"  --fs-{k}: {v[0]}px; --fw-{k}: {v[1]}; --lh-{k}: {v[2]};" for k, v in scale.items())
    css = f"""/* foundation tokens — derive.py --brand {brand_hex} --tone {tone} --shape {shape} --density {density} --font {font}
   이 파일은 생성물이다. 직접 고치지 말고 파라미터를 바꿔 다시 만든다. */
@import url('{f["import"]}');

:root {{
  /* 색 — 포인트 1 + 표면 톤({tone}) */
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

/* 보기 전용 역할: 본문 계열만 한 단계 크게 */
.is-viewer {{
{typo(f["viewer"])}
}}
"""
    return css, checks, notes

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--brand", required=True); ap.add_argument("--tone", default="neutral", choices=TONES)
    ap.add_argument("--shape", default="normal", choices=SHAPES); ap.add_argument("--density", default="comfy", choices=DENSITY)
    ap.add_argument("--font", default="pretendard", choices=FONTS); ap.add_argument("-o", "--out", required=True)
    a = ap.parse_args()
    css, checks, notes = derive(a.brand, a.tone, a.shape, a.density, a.font)
    pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True); pathlib.Path(a.out).write_text(css, encoding="utf-8")
    bad = {k: v for k, v in checks.items() if v < 4.5}
    print(f"wrote {a.out}", *notes, sep="\n")
    print("대비:", ", ".join(f"{k} {v:.1f}" for k, v in checks.items()))
    sys.exit(1 if bad else 0)
