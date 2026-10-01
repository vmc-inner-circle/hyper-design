"""도형 (v7 엔진, 09-28). 색을 바꿀 수 있는 도형 15종 — CSS mask 로 쓰므로 색은 background 로 정한다.

HTML·style.css 에서:  <i class="sh sh-star" style="--c:var(--a3);width:40px;height:40px"></i>
                     .app .x:after{content:"";…;background:var(--a2);-webkit-mask:var(--m-blob) center/contain no-repeat;mask:var(--m-blob) center/contain no-repeat}
블록:                {"t":"art","height":180,"items":[{"s":"blob","c":"a2","x":10,"y":20,"w":40,"rot":15}],"title":"…","text":"…"}
도형 이름: circle ring half quarter blob blob2 star sparkle flower triangle plus dots squiggle zigzag arc wave pill
색 이름: a1(=accent) a2 a3 a4 ink muted line surface 또는 #hex
"""
from urllib.parse import quote

S = {
    "circle": '<circle cx="50" cy="50" r="50"/>',
    "ring": '<path fill-rule="evenodd" d="M50 0a50 50 0 1 1 0 100a50 50 0 1 1 0-100zm0 18a32 32 0 1 0 0 64a32 32 0 1 0 0-64z"/>',
    "half": '<path d="M0 100a50 50 0 0 1 100 0z"/>',
    "quarter": '<path d="M0 100V0a100 100 0 0 1 100 100z"/>',
    "blob": '<path d="M50 4c25 0 47 18 45 46s-23 47-48 45S3 74 5 48 25 4 50 4z"/>',
    "blob2": '<path d="M60 3c25 5 39 32 32 57S58 99 34 92 -2 58 6 35 36-2 60 3z"/>',
    "star": '<polygon points="50,3 61,38 98,38 68,59 79,95 50,73 21,95 32,59 2,38 39,38"/>',
    "sparkle": '<path d="M50 0c4 36 14 46 50 50-36 4-46 14-50 50-4-36-14-46-50-50 36-4 46-14 50-50z"/>',
    "flower": "".join(f'<circle cx="{50 + 26 * c}" cy="{50 + 26 * s}" r="24"/>' for c, s in ((1, 0), (.5, .87), (-.5, .87), (-1, 0), (-.5, -.87), (.5, -.87))) + '<circle cx="50" cy="50" r="24"/>',
    "triangle": '<polygon points="50,5 97,92 3,92"/>',
    "plus": '<path d="M38 0h24v38h38v24H62v38H38V62H0V38h38z"/>',
    "dots": "".join(f'<circle cx="{x}" cy="{y}" r="7"/>' for x in (12, 50, 88) for y in (12, 50, 88)),
    "squiggle": '<path d="M2 50q12-30 24 0t24 0 24 0 24 0" fill="none" stroke="#000" stroke-width="11" stroke-linecap="round"/>',
    "zigzag": '<polyline points="2,65 18,35 34,65 50,35 66,65 82,35 98,65" fill="none" stroke="#000" stroke-width="10" stroke-linejoin="round" stroke-linecap="round"/>',
    "arc": '<path d="M8 92a42 42 0 0 1 84 0" fill="none" stroke="#000" stroke-width="12" stroke-linecap="round"/>',
    "wave": '<path d="M0 55c17-18 33-18 50 0s33 18 50 0v45H0z"/>',
    "pill": '<rect x="0" y="30" width="100" height="40" rx="20"/>',
}


def uri(k):
    return "url(\"data:image/svg+xml;utf8," + quote(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">{S[k]}</svg>', safe=" =:/,;'") + "\")"


def css():
    v = ":root{" + ";".join(f"--m-{k}:{uri(k)}" for k in S) + "}"
    cls = " ".join(f".sh-{k}{{--m:var(--m-{k})}}" for k in S)
    return (v + "\n.sh{display:inline-block;background:var(--c,var(--accent));-webkit-mask:var(--m) center/contain no-repeat;mask:var(--m) center/contain no-repeat}\n" + cls +
            "\n.art{position:relative;overflow:hidden;border-radius:var(--r);background:color-mix(in srgb,var(--a2) 10%,var(--surface))}"
            ".art .sh{position:absolute} .art .cap{position:absolute;left:18px;bottom:16px;right:18px} .art .cap b{display:block;font-size:1.35em} .art .cap div{color:var(--muted)}\n")


def color(c):
    if not c:
        return "var(--accent)"
    return c if c.startswith("#") or c.startswith("var(") else f"var(--{c})"


def art(b, e):
    items = "".join(
        f'<i class="sh sh-{e(i.get("s", "circle"))}" style="--c:{e(color(i.get("c")))};left:{i.get("x", 0)}%;top:{i.get("y", 0)}%;width:{i.get("w", 20)}%;aspect-ratio:1;'
        f'transform:rotate({i.get("rot", 0)}deg);opacity:{i.get("o", 1)}"></i>' for i in b.get("items", []))
    cap = f'<div class="cap"><b>{e(b["title"])}</b><div>{e(b.get("text", ""))}</div></div>' if b.get("title") else ""
    return f'<div class="art" style="height:{b.get("height", 180)}px">{items}{cap}</div>'
