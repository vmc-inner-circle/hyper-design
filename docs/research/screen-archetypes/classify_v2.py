"""2차 분류 — 유형 = 종류 × ①첫 화면 주인공(anchor). ②반복 단위·③마지막 행동은 같은 유형 안의 변형.

python3 classify_v2.py [--json] [--miss]
- 라벨: labels_v2/ (w*: 모바일 웹, kind=찍은 주소 / s*: 이름으로 정한 앱 37개의 스토어 스크린샷, 홈은 '탭바 첫 칸 선택'일 때만)
- 라벨러가 anchor를 정해진 값에서 고른다 → 유형은 아래 표로 기계적으로 정한다(칸 순서 규칙 없음)
- 유형으로 인정: 서로 다른 앱·사이트 3개 이상
"""
import json, sys, collections, pathlib
HERE = pathlib.Path(__file__).parent

def site_key(s):  # 같은 서비스의 웹·앱은 한 곳으로 센다(daangn-community → daangn)
    return s.split("-")[0]

HOME = {"서비스 격자": "찾기형", "진열(배너·가로 줄)": "진열형", "배너 캐러셀": "진열형", "상품 격자": "진열형", "상품 분류 격자": "진열형", "인사/큰제목": "진열형",
        "내 숫자 카드": "현황형", "글 목록(대표 글+제목 행)": "목록형", "목록 행": "목록형", "카드 피드": "피드형",
        "큰 사진(대상 하나)": "대표 콘텐츠형", "대표 글(큰 사진+제목)": "대표 콘텐츠형", "콘텐츠 자체(영상·본문·만화)": "대표 콘텐츠형", "달력·날짜": "일정형", "지도": "지도형",
        "입력 칸": "조건 입력형", "QR·바코드": "증표형"}
DETAIL = {"콘텐츠 자체(영상·본문·만화)": "읽기·재생형", "영상 플레이어": "읽기·재생형", "글(제목+작성자+본문)": "글형", "프로필(사람·가게)": "사람형",
          "지도": "진행 추적형", "차트": "수치형", "내 숫자 카드": "수치형", "QR·바코드": "증표형"}
LIST = {"목록 행": "행 목록", "글 목록(대표 글+제목 행)": "행 목록", "상품 격자": "상품 격자", "카드 피드": "카드 피드", "큰 사진(대상 하나)": "카드 피드",
        "지도": "지도+목록", "랭킹 목록": "순위", "진열(배너·가로 줄)": "진열(카테고리 홈)", "상품 분류 격자": "진열(카테고리 홈)", "서비스 격자": "진열(카테고리 홈)"}
SHAPE = {"찾기형": "서로 다른 서비스로 가는 격자가 첫 화면 주인공", "진열형": "배너·제목 달린 가로 줄·상품 격자(같은 상품의 큐레이션)",
         "현황형": "내 숫자(잔액·포인트·진행) 카드", "목록형": "첫 화면부터 같은 높이의 행(글·매물·대화)", "피드형": "사진+글 큰 카드가 세로로 끝없이",
         "대표 콘텐츠형": "지금 볼 것 하나(라이브·영상·포스터)가 크게, 아래 가로 줄", "일정형": "달력·날짜 줄", "지도형": "지도가 화면 전체",
         "조건 입력형": "출발·도착 같은 입력 칸이 홈", "증표형": "결제·멤버십 QR이 홈",
         "대상형": "대상 하나의 큰 사진 → 이름·가격·정보 → 하단 행동(구매·예약·신청·연락)", "읽기·재생형": "영상·본문·만화 자체가 맨 위",
         "글형": "제목+작성자 → 본문 → 반응", "사람형": "프로필(사람·가게) → 평점·소개"}

def typ(kind, anchor, exit_):
    a = anchor if not anchor.startswith("기타") else "기타"
    if kind == "home": return HOME.get(a)
    if kind == "list": return LIST.get(a)
    if kind == "detail":
        if a == "큰 사진(대상 하나)": return "대상형"  # 상품·장소·모임·매물 — 구매/예약/신청/연락은 ③마지막 행동으로 갈리는 변형
        return DETAIL.get(a)
    if kind == "chat": return "채팅"
    return None

def rows():
    for f in sorted((HERE / "labels_v2").glob("*.out.json")):
        for a in json.load(open(f)):
            if f.name.startswith("w"):
                if a.get("valid"): yield "웹", site_key(a["site"]), a.get("kind") or a["page"], a["anchor"], a.get("exit", "없음"), a.get("repeat", "없음")
            else:
                for s in a["screens"]:
                    if s.get("valid"): yield "앱", site_key(a["site"]), s["kind"], s["anchor"], s.get("exit", "없음"), s.get("repeat", "없음")

def main():
    apps = collections.defaultdict(lambda: collections.defaultdict(set)); n = collections.Counter(); miss = collections.defaultdict(list)
    var = collections.defaultdict(collections.Counter)  # (kind, 유형) → 변형(home·list: 반복 단위, detail: 마지막 행동)
    for src, site, kind, anchor, ex, rep in rows():
        if kind not in ("home", "list", "detail", "chat"): continue
        n[kind] += 1; t = typ(kind, anchor, ex)
        if t: apps[kind][t].add(site); var[(kind, t)][(ex if kind == "detail" else rep).split(":")[0]] += 1
        else: miss[kind].append(f"{src}:{site} {anchor}")
    out = {k: sorted(({"type": t, "n": len(v), "apps": sorted(v), "shape": SHAPE.get(t, ""), "variants": dict(var[(k, t)].most_common())} for t, v in apps[k].items()), key=lambda r: -r["n"]) for k in apps}
    if "--json" in sys.argv:
        json.dump({"screens": n, "unmatched": {k: len(v) for k, v in miss.items()}, "archetypes": out}, open(HERE / "archetypes_v2.json", "w"), ensure_ascii=False, indent=1); return
    for k in ("home", "detail", "list", "chat"):
        print(f"\n### {k} — 화면 {n[k]}장, 미분류 {len(miss[k])} ({len(miss[k]) * 100 // max(n[k], 1)}%)")
        for r in out.get(k, []):
            print(f"| {'✅' if r['n'] >= 3 else '·'} {r['type']} | {r['n']} | {', '.join(r['apps'][:9])} | {', '.join(f'{a} {c}' for a, c in list(r['variants'].items())[:4])} |")
        if "--miss" in sys.argv: print("\n".join("   미분류 " + m for m in miss[k]))

if __name__ == "__main__": main()
