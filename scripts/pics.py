"""사진 자리 그림 (v7 엔진, 2026-09-28). 외부 사진 서비스 없이 키워드로 그림(SVG)을 만들어 data URI 로 넣는다.

    img = "gen:<영어 키워드,쉼표로 1~3개>[:<숫자>]"   예) "gen:woman"  "gen:jeju,beach:3"  "gen:koreanfood,restaurant:7"
    옛 형식 "https://loremflickr.com/800/500/<키워드>?lock=<숫자>" 도 같은 그림으로 바뀐다(서비스가 401 로 막힘 — 09-28).
    그 밖의 http(s)·상대 경로 이미지는 그대로 둔다.

사람(woman·man·bride·groom·grandma·kid·couple·family…) = 인물 일러스트, 장소·음식 = 키워드에 맞는 장면. 글자는 넣지 않는다.
"""
import hashlib
import re
from urllib.parse import quote

SKIN = ["#F2D3BC", "#E8BFA0", "#D9A984", "#C68E6B"]
HAIR = ["#2B211C", "#3D2B22", "#5A3D2B", "#1E1B1A"]
GRAY = "#B9B4AE"
SHIRT = ["#7C8FA6", "#A67C84", "#7FA38C", "#C2A36B", "#8E7CA6", "#6F8F9E", "#B98A6E"]
PAIRS = [("#F6E3D3", "#E9B99A"), ("#DDEBF2", "#9CC3D8"), ("#E4EFE3", "#A9C8A5"), ("#F3E6EC", "#D6A9BA"),
         ("#EFE9DC", "#CDB98F"), ("#E6E4F2", "#AFA9D6"), ("#F5EBDD", "#E3B77D"), ("#E3EEF0", "#8FB8BF")]

THEMES = [
    ("person", r"woman|girl|bride|lady|man|boy|groom|guy|person|portrait|face|people|friend|couple|family|kid|child|baby|grand|parent|senior|mom|dad|mother|father|user|profile|avatar|사람|인물"),
    ("food", r"food|restaurant|cafe|coffee|dinner|lunch|meal|bbq|dessert|cake|bread|noodle|sushi|drink|wine|\bbar\b|bistro|kitchen|음식|식당|카페"),
    ("sea", r"beach|\bsea\b|ocean|island|jeju|coast|harbor|surf|lake|river|바다|해변"),
    ("mountain", r"mountain|hiking|forest|nature|park|camp|trail|valley|\btree\b|garden|산|숲|공원"),
    ("city", r"city|street|night|building|seoul|busan|tokyo|downtown|market|shop|store|alley|도시|거리"),
    ("stay", r"hotel|room|pension|resort|house|\bhome\b|interior|bed|stay|lodge|villa|숙소|호텔"),
    ("party", r"wedding|party|celebration|flower|gift|\bring\b|ceremony|event|birthday|결혼|파티|꽃"),
    ("travel", r"\bcar\b|road|drive|airport|plane|flight|train|station|\bbus\b|trip|travel|tour|luggage|여행|공항"),
]


def _seed(s):
    return int(hashlib.md5(s.encode("utf-8")).hexdigest()[:8], 16)


def _theme(words):
    w = " ".join(words).lower()
    for name, pat in THEMES:
        if re.search(pat, w):
            return name
    return "abstract"


def _person(words, r):
    w = " ".join(words).lower()
    many = re.search(r"couple|family|friends|people|group", w)
    old = re.search(r"grand|senior|elder|parent|mom|dad|mother|father", w)
    fem = re.search(r"woman|girl|bride|lady|mom|mother|grandma", w)
    male = re.search(r"\bman\b|boy|groom|guy|dad|father|grandpa", w)
    bg = PAIRS[r % len(PAIRS)][0]

    def one(cx, cy, s, k, female):
        skin = SKIN[(r >> (k + 2)) % len(SKIN)]
        hair = GRAY if old else HAIR[(r >> (k + 4)) % len(HAIR)]
        shirt = SHIRT[(r >> (k + 6)) % len(SHIRT)]
        g = f'<ellipse cx="{cx}" cy="{cy + 150 * s}" rx="{92 * s}" ry="{70 * s}" fill="{shirt}"/>'
        g += f'<rect x="{cx - 17 * s}" y="{cy + 40 * s}" width="{34 * s}" height="{40 * s}" rx="{12 * s}" fill="{skin}"/>'
        if female:
            g += f'<path d="M{cx - 62 * s},{cy + 70 * s} C{cx - 78 * s},{cy - 60 * s} {cx + 78 * s},{cy - 60 * s} {cx + 62 * s},{cy + 70 * s} Z" fill="{hair}"/>'
        g += f'<circle cx="{cx}" cy="{cy}" r="{50 * s}" fill="{skin}"/>'
        if female:
            g += f'<path d="M{cx - 52 * s},{cy - 2 * s} C{cx - 50 * s},{cy - 62 * s} {cx + 50 * s},{cy - 62 * s} {cx + 52 * s},{cy - 2 * s} C{cx + 20 * s},{cy - 30 * s} {cx - 20 * s},{cy - 30 * s} {cx - 52 * s},{cy - 2 * s} Z" fill="{hair}"/>'
        else:
            g += f'<path d="M{cx - 51 * s},{cy - 4 * s} C{cx - 54 * s},{cy - 66 * s} {cx + 54 * s},{cy - 66 * s} {cx + 51 * s},{cy - 4 * s} L{cx + 40 * s},{cy - 22 * s} L{cx - 40 * s},{cy - 24 * s} Z" fill="{hair}"/>'
        g += f'<circle cx="{cx - 17 * s}" cy="{cy + 6 * s}" r="{4 * s}" fill="#3a2e2a" opacity=".7"/><circle cx="{cx + 17 * s}" cy="{cy + 6 * s}" r="{4 * s}" fill="#3a2e2a" opacity=".7"/>'
        g += f'<path d="M{cx - 12 * s},{cy + 24 * s} Q{cx},{cy + 33 * s} {cx + 12 * s},{cy + 24 * s}" stroke="#3a2e2a" stroke-opacity=".55" stroke-width="{3 * s}" fill="none" stroke-linecap="round"/>'
        return g

    if many:
        body = one(105, 135, .78, 0, True) + one(195, 128, .82, 3, False)
    else:
        f = bool(fem) or (not male and r % 2 == 0)
        body = one(150, 125, 1, 0, f)
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 300" preserveAspectRatio="xMidYMid slice"><rect width="300" height="300" fill="{bg}"/>{body}</svg>'


def _scene(theme, r):
    a, b = PAIRS[r % len(PAIRS)]
    j = (r >> 5) % 60
    if theme == "sea":
        g = f'<rect width="800" height="500" fill="#CFE6F2"/><circle cx="{560 + j}" cy="150" r="58" fill="#FFE2B0"/><rect y="270" width="800" height="120" fill="#7FB6CF"/><path d="M0,300 Q100,285 200,300 T400,300 T600,300 T800,300" stroke="#fff" stroke-opacity=".6" stroke-width="5" fill="none"/><path d="M0,390 C200,360 500,370 800,395 L800,500 L0,500 Z" fill="#EAD7B7"/>'
    elif theme == "mountain":
        g = f'<rect width="800" height="500" fill="#E3EEE6"/><circle cx="{170 + j}" cy="120" r="46" fill="#FFF0C7"/><path d="M-20,380 L200,170 L360,330 L500,200 L820,400 L820,500 L-20,500 Z" fill="#9CBFA3"/><path d="M-20,430 L260,300 L480,420 L640,330 L820,440 L820,500 L-20,500 Z" fill="#6F9B7A"/>'
    elif theme == "city":
        bars = "".join(f'<rect x="{x}" y="{220 - (r >> (x % 13)) % 110}" width="70" height="400" fill="{c}"/>' for x, c in zip(range(20, 800, 95), ["#8A94A8", "#6E7890", "#9AA3B5", "#7B849B", "#5F687F", "#8C96AB", "#737D94", "#A0A8B8", "#687288"]))
        g = f'<rect width="800" height="500" fill="#F1DCC8"/><circle cx="{600 - j}" cy="120" r="50" fill="#F7B98B"/>{bars}<rect y="440" width="800" height="60" fill="#4E5569"/>'
    elif theme == "stay":
        g = f'<rect width="800" height="500" fill="{a}"/><rect x="0" y="360" width="800" height="140" fill="{b}"/><rect x="480" y="90" width="210" height="160" rx="8" fill="#fff" opacity=".85"/><line x1="585" y1="90" x2="585" y2="250" stroke="{b}" stroke-width="6"/><rect x="120" y="270" width="340" height="130" rx="18" fill="#fff"/><rect x="120" y="240" width="110" height="60" rx="14" fill="#F3EEE6"/><rect x="110" y="330" width="360" height="80" rx="14" fill="{b}" opacity=".75"/>'
    elif theme == "food":
        g = f'<rect width="800" height="500" fill="{a}"/><circle cx="400" cy="265" r="175" fill="#fff"/><circle cx="400" cy="265" r="130" fill="{b}" opacity=".55"/><circle cx="360" cy="235" r="34" fill="#fff" opacity=".6"/><circle cx="445" cy="290" r="26" fill="#fff" opacity=".45"/><rect x="620" y="110" width="16" height="300" rx="8" fill="#C9B79C"/><rect x="170" y="110" width="16" height="300" rx="8" fill="#C9B79C"/>'
    elif theme == "party":
        dots = "".join(f'<circle cx="{(r >> i) % 800}" cy="{(r >> (i + 3)) % 500}" r="{6 + (i % 4) * 3}" fill="{c}" opacity=".8"/>' for i, c in zip(range(18), ["#E8A0AF", "#F2C57C", "#9CC3D8", "#A9C8A5", "#C5A8D6", "#fff"] * 3))
        g = f'<rect width="800" height="500" fill="{a}"/>{dots}<circle cx="400" cy="250" r="95" fill="#fff" opacity=".7"/><circle cx="400" cy="250" r="55" fill="{b}"/>'
    elif theme == "travel":
        g = f'<rect width="800" height="500" fill="#E5EEF5"/><circle cx="{620 - j}" cy="130" r="48" fill="#FFE2B0"/><path d="M-20,330 C200,300 600,310 820,330 L820,500 L-20,500 Z" fill="#B7CDB5"/><path d="M330,500 L390,330 L410,330 L470,500 Z" fill="#8E9199"/><path d="M398,350 L402,350 L404,380 L396,380 Z M395,410 L405,410 L408,450 L392,450 Z" fill="#fff"/>'
    else:
        g = f'<rect width="800" height="500" fill="{a}"/><circle cx="{220 + j}" cy="180" r="160" fill="{b}" opacity=".55"/><circle cx="600" cy="360" r="200" fill="{b}" opacity=".35"/>'
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 500" preserveAspectRatio="xMidYMid slice">{g}</svg>'


def src(img):
    """app.py 가 <img src> 에 넣을 값."""
    s = (img or "").strip()
    m = re.match(r"gen:([^:]+)(?::(\d+))?$", s)
    if m:
        words, n = m.group(1).split(","), m.group(2) or "0"
    else:
        m = re.match(r"https?://loremflickr\.com/(?:g/)?\d+/\d+/([^?]+)(?:\?lock=(\d+))?", s)
        if not m:
            return s
        words, n = m.group(1).split(","), m.group(2) or "0"
    words = [w.strip() for w in words if w.strip()]
    r = _seed(",".join(words) + ":" + n)
    t = _theme(words)
    svg = _person(words, r) if t == "person" else _scene(t, r)
    return "data:image/svg+xml;charset=utf-8," + quote(svg, safe="=:/,;'")
