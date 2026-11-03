"""국내 서비스 모바일 웹의 실제 화면 캡처 — 홈·목록(검색 결과)·상세를 페이지 종류를 알고 찍는다.

python3 capture_mweb.py <출력 폴더> [--only 29cm,kurly]
- 아이폰 13 화면(390×844), 각 페이지 위쪽 2화면 높이(390×1688)만 찍는다
- 상세는 목록(없으면 홈)에서 사진이 든 같은 사이트 링크 중 상세 주소처럼 보이는 첫 링크를 연다
- 출력: <폴더>/<사이트>-<home|list|detail>.png, <폴더>/manifest.json(사이트·도메인·페이지별 URL·실패 이유)
"""
import sys, json, re, pathlib, argparse
from concurrent.futures import ThreadPoolExecutor
from playwright.sync_api import sync_playwright

# (id, 도메인, 홈, 검색 결과 URL — 없으면 None. 홈이 None이면 목록·상세만(당근처럼 한 앱 안의 서비스별 목록))
SITES = [
 ("29cm", "패션 쇼핑", "https://www.29cm.co.kr", "https://www.29cm.co.kr/search?keyword=니트"),
 ("musinsa", "패션 쇼핑", "https://www.musinsa.com/main/musinsa/recommend", "https://www.musinsa.com/search/goods?keyword=니트"),
 ("zigzag", "패션 쇼핑", "https://zigzag.kr", "https://zigzag.kr/search?keyword=니트"),
 ("kream", "리셀", "https://kream.co.kr", "https://kream.co.kr/search?keyword=나이키"),
 ("kurly", "장보기", "https://www.kurly.com/main", "https://www.kurly.com/search?sword=사과"),
 ("11st", "종합 쇼핑", "https://m.11st.co.kr", "https://search.11st.co.kr/MW/search?searchKeyword=사과"),
 ("gmarket", "종합 쇼핑", "https://m.gmarket.co.kr", "https://msearch.gmarket.co.kr/search.mall?keyword=사과"),
 ("ohou", "인테리어", "https://ohou.se", "https://ohou.se/search/index?query=의자"),
 ("bunjang", "중고거래", "https://m.bunjang.co.kr", "https://m.bunjang.co.kr/search/products?q=아이폰"),
 ("joongna", "중고거래", "https://web.joongna.com", "https://web.joongna.com/search/아이폰"),
 ("daangn", "중고거래", "https://www.daangn.com/kr/buy-sell/", None),
 ("myrealtrip", "여행", "https://www.myrealtrip.com", "https://www.myrealtrip.com/search?q=오사카"),
 ("yeogi", "숙소", "https://www.yeogi.com", None),
 ("nol", "숙소", "https://nol.yanolja.com", None),
 ("triple", "여행", "https://triple.guide", None),
 ("klook", "여행", "https://www.klook.com/ko/", "https://www.klook.com/ko/search/result/?query=오사카"),
 ("airbnb", "숙소", "https://www.airbnb.co.kr", None),
 ("catchtable", "식당 예약", "https://app.catchtable.co.kr", None),
 ("kakaomap", "지도", "https://m.map.kakao.com", "https://m.map.kakao.com/actions/searchView?q=카페"),
 ("hogangnono", "부동산", "https://hogangnono.com", None),
 ("dabang", "부동산", "https://www.dabangapp.com", None),
 ("soomgo", "전문가 찾기", "https://soomgo.com", None),
 ("class101", "클래스", "https://class101.net/ko", "https://class101.net/ko/search?query=드로잉"),
 ("frip", "취미", "https://www.frip.co.kr", None),
 ("munto", "모임", "https://www.munto.kr", None),
 ("ridi", "전자책", "https://ridibooks.com", "https://ridibooks.com/search?q=소설"),
 ("yes24", "책", "https://m.yes24.com", "https://m.yes24.com/Search?query=소설"),
 ("kakaopage", "웹소설", "https://page.kakao.com", None),
 ("navercomic", "웹툰", "https://m.comic.naver.com", None),
 ("navernews", "뉴스", "https://m.news.naver.com", None),
 ("daumnews", "뉴스", "https://news.daum.net", None),
 ("youtube", "영상", "https://m.youtube.com", "https://m.youtube.com/results?search_query=요리"),
 ("melon", "음악", "https://m2.melon.com", None),
 ("brunch", "글", "https://brunch.co.kr", None),
 ("velog", "글", "https://velog.io", None),
 ("blind", "커뮤니티", "https://www.teamblind.com/kr", None),
 ("inflearn", "강의", "https://www.inflearn.com", "https://www.inflearn.com/courses?s=파이썬"),
 ("wanted", "채용", "https://www.wanted.co.kr", None),
 ("saramin", "채용", "https://m.saramin.co.kr", None),
 ("10000recipe", "레시피", "https://m.10000recipe.com", "https://m.10000recipe.com/recipe/list.html?q=김치찌개"),
 # 2차 — 이름으로 정한 대표 서비스, 당근은 서비스별
 ("daangn-main", "동네 생활", "https://www.daangn.com/kr/", "https://www.daangn.com/kr/search/buy-sell/"),
 ("daangn-community", "동네 생활", None, "https://www.daangn.com/kr/search/community/"),
 ("daangn-group", "모임", None, "https://www.daangn.com/kr/search/group/"),
 ("daangn-local", "동네 가게", None, "https://www.daangn.com/kr/search/local-profile/?q=맛집"),
 ("daangn-cars", "중고차", None, "https://www.daangn.com/kr/search/cars/"),
 ("daangn-jobs", "알바", None, "https://www.daangn.com/kr/jobs/"),
 ("daangn-realty", "부동산", None, "https://www.daangn.com/kr/realty/"),
 ("chzzk", "라이브 방송", "https://chzzk.naver.com", None),
 ("soop", "라이브 방송", "https://www.sooplive.co.kr", None),
 ("naver", "포털", "https://m.naver.com", None),
 ("navermap", "지도", "https://m.map.naver.com", None),
 ("oliveyoung", "뷰티 쇼핑", "https://m.oliveyoung.co.kr", "https://m.oliveyoung.co.kr/m/mtn/search/result?query=선크림"),
 ("daiso", "생활 쇼핑", "https://www.daisomall.co.kr", None),
 ("cgv", "영화 예매", "https://m.cgv.co.kr", None),
 ("albamon", "알바", "https://m.albamon.com", None),
 ("kmong", "전문가 찾기", "https://kmong.com", "https://kmong.com/search?keyword=로고"),
 ("coupang", "종합 쇼핑", "https://m.coupang.com", "https://m.coupang.com/nm/search?q=사과"),
 # 실험(loop/archetype_exp) 정답 보강 — 스토어 화면만으로 홈이 불분명했던 앱
 ("ssg", "종합 쇼핑", "https://m.ssg.com", None),
 ("finda", "금융", "https://www.finda.co.kr", None),
 ("everytime", "대학 커뮤니티", "https://everytime.kr", None),
 ("pinterest", "아이디어", "https://www.pinterest.co.kr", None),
 ("gcar", "카셰어링", "https://www.greencar.co.kr", None),
 ("wavve", "영상", "https://www.wavve.com", None),
]
DETAIL = re.compile(r"/(products?|goods|item|catalog|detail|p|recipe|course|courses|books?|v2/title|content|watch|articles?|room|rooms|place|places|offers|activity|activities|tna|classes|stays?|deals?|jobs?|wd|read|post|accommodations?|socialing|v|@[^/]+/[^/]+)(/|\?|$|\d)|\?id=\d+", re.I)
SKIP = re.compile(r"login|signin|join|event|cart|order|mypage|notice|help|policy|terms|app|download", re.I)
W, H = 390, 844

def close_popups(pg):
    pg.keyboard.press("Escape")
    for t in ["닫기", "오늘 하루 보지 않기", "다음에 할게요", "모바일 웹으로 볼게요", "웹으로 볼게요", "괜찮아요", "그냥 볼게요"]:
        try:
            el = pg.get_by_text(t, exact=True).first
            if el.is_visible(timeout=300): el.click(timeout=800)
        except Exception: pass

def shot(pg, url, path):
    pg.goto(url, wait_until="domcontentloaded", timeout=25000)
    pg.wait_for_timeout(2500); close_popups(pg)
    pg.evaluate("window.scrollTo(0, %d)" % H); pg.wait_for_timeout(700); pg.evaluate("window.scrollTo(0, 0)"); pg.wait_for_timeout(500)
    pg.screenshot(path=str(path), clip={"x": 0, "y": 0, "width": W, "height": H * 2}, full_page=True)
    return pg.url

def detail_link(pg, host):
    base = pg.url.split("?")[0].rstrip("/")
    svc = re.search(r"/search/([^/?]+)", base)  # 당근: /search/community/ 결과 → 상세는 /community/<글>/
    under = [base] + ([base.split("/search/")[0] + "/" + svc.group(1)] if svc else [])
    # 사진이 든 링크 먼저, 없으면 글자만 있는 행(알바·동네생활)
    for sel in ("a.querySelector('img') && a.getBoundingClientRect().width > 60", "a.getBoundingClientRect().width > 200"):
        for h in pg.evaluate("() => [...document.querySelectorAll('a[href]')].filter(a => %s).map(a => a.href)" % sel):
            if host.split(".")[-2] not in h or SKIP.search(h) or "/search/" in h: continue
            if DETAIL.search(h) or any(h.startswith(u + "/") and len(h) > len(u) + 8 for u in under): return h  # 목록 주소 아래 한 단계(당근 /buy-sell/<글>)

def click_card(pg):
    """링크 없이 스크립트로 여는 카드 — 첫 화면 아래쪽의 가장 큰 사진을 눌러 주소가 바뀌면 그 주소"""
    before = pg.url
    box = pg.evaluate("""() => { const ims = [...document.querySelectorAll('img')].map(i => [i, i.getBoundingClientRect()])
        .filter(([i, r]) => r.width >= 100 && r.width < 380 && r.top > 150 && r.top < 1400);
      ims.sort((a, b) => a[1].top - b[1].top); const r = ims.length && ims[0][1]; return r ? {x: r.x + r.width / 2, y: r.y + r.height / 2} : null }""")
    if not box: return None
    pg.mouse.click(box["x"], box["y"]); pg.wait_for_timeout(3000)
    return pg.url if pg.url != before else None

def run(site, out):
    sid, dom, home, search = site
    rec = {"id": sid, "domain": dom, "pages": {}}
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(**p.devices["iPhone 13"], locale="ko-KR")
        pg = ctx.new_page()
        host = re.sub(r"^https?://([^/]+).*", r"\1", home or search)
        for kind, url in (("home", home), ("list", search)):
            if not url: continue
            try: rec["pages"][kind] = shot(pg, url, out / f"{sid}-{kind}.png")
            except Exception as e: rec["pages"][kind] = f"ERR {type(e).__name__}"
        try:
            src = search or home
            if pg.url.rstrip("/") != (rec["pages"].get("list") or rec["pages"].get("home") or "").rstrip("/"): pg.goto(src, timeout=25000); pg.wait_for_timeout(2500)
            close_popups(pg)
            link = detail_link(pg, host) or click_card(pg)
            rec["pages"]["detail"] = shot(pg, link, out / f"{sid}-detail.png") if link else "ERR 상세 링크 못 찾음"
        except Exception as e: rec["pages"]["detail"] = f"ERR {type(e).__name__}"
        b.close()
    return rec

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("--only", default="")
    a = ap.parse_args(); out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    sites = [s for s in SITES if not a.only or s[0] in a.only.split(",")]
    with ThreadPoolExecutor(8) as ex: recs = list(ex.map(lambda s: run(s, out), sites))
    json.dump(recs, open(out / "manifest.json", "w"), ensure_ascii=False, indent=1)
    for r in recs: print(r["id"], {k: ("ok" if not v.startswith("ERR") else v) for k, v in r["pages"].items()})

if __name__ == "__main__": main()
