"""스토어 스크린샷 라벨(labels/*.out.json)을 화면 종류별 유형으로 묶는다.

python3 classify.py            유형별 앱 수·예시 앱 표(markdown)
python3 classify.py --json     archetypes.json으로 저장
- 라벨: 에이전트가 스크린샷 한 장마다 kind·위→아래 칸 순서(slots)를 적은 것
- 규칙은 칸 이름의 위치로만 판정한다(위쪽 N칸에 무엇이 있나). 위에서부터 첫 규칙에 걸리면 그 유형
- 유형으로 인정: 서로 다른 앱 3개 이상
"""
import json, glob, sys, collections, pathlib
HERE = pathlib.Path(__file__).parent

def has(slots, names, top=None):
    s = slots[:top] if top else slots
    return any(any(n in x for n in names) for x in s)

def strip(slots):  # 앱 상단바·로고·상단 탭은 구조에서 뺀다
    return [x for x in slots if not (x.startswith("기타:상단") or x.startswith("기타:앱 상단") or x.startswith("상단 탭") or "로고" in x)]

RULES = {
 "home": [
  ("지도형",   "지도가 화면을 차지하고 그 위에 검색·목록이 뜬다", lambda s: has(s, ["지도"], 3)),
  ("일정형",   "달력·날짜 줄이 맨 위, 아래에 그날의 할 일·기록", lambda s: has(s, ["월 달력", "날짜 줄", "일정 타임라인", "오늘 할 일", "시간표"], 2)),
  ("현황형",   "내 숫자(잔액·진행·현황) 카드가 맨 위, 아래 바로가기·목록", lambda s: has(s, ["자산·잔액", "현황 카드", "진행률"], 2)),
  ("피드형",   "(동네·칩) 아래 세로 카드가 끝없이 이어진다", lambda s: has(s, ["세로 카드 피드"], 3) and not has(s, ["카테고리 아이콘", "배너"], 3)),
  ("글 목록형", "대표 글 하나 아래 제목 위주 글 목록·순위가 이어진다(뉴스·커뮤니티·글)", lambda s: has(s, ["목록 행", "대표 기사", "랭킹 목록"], 3) and not has(s, ["가로 카드 줄", "격자", "에디토리얼"], 5)),
  ("찾기형",   "(위치·검색 아래) 카테고리 아이콘 격자가 맨 위, 아래 배너·추천 줄", lambda s: has(s, ["카테고리 아이콘", "위치·주소"], 3)),
  ("진열형",   "배너 아래 제목 달린 가로 줄·상품 격자가 반복된다", lambda s: has(s, ["배너", "가로 카드 줄", "격자", "에디토리얼"], 3)),
 ],
 "detail": [
  ("읽기·재생형", "본문·영상·만화 자체가 맨 위(헤더·컨트롤만 얹힘), 아래 제목·작성자·반응", lambda s: has(s, ["본문 읽기", "뷰어", "재생 컨트롤", "만화 컷", "PDF", "영상 플레이어"], 2) and not has(s, ["사진 갤러리"], 1) and not has(s, ["가격·할인"])),
  ("진행 추적형", "지도·진행 단계가 맨 위, 아래 정보 행", lambda s: has(s, ["지도", "도착 예정"], 1)),
  ("수치형",     "숫자 요약·차트가 맨 위, 아래 정보 행·내역", lambda s: has(s, ["현황 카드", "결과 요약", "자산·잔액", "차트", "시세"], 2) and not has(s, ["사진 갤러리"], 1)),
  ("상품형",     "큰 사진 → 이름·가격 → 옵션 → 리뷰, 하단 구매 버튼", lambda s: has(s, ["가격·할인", "옵션 선택"]) and not has(s, ["시간·날짜"])),
  ("장소·예약형", "큰 사진 → 이름·평점 → 정보(위치·시간) → 날짜 고르기·예약", lambda s: has(s, ["평점·리뷰 요약", "위치·지도 미리보기", "시간·날짜"]) and has(s, ["사진 갤러리", "판매자/가게", "정보 행"])),
  ("사람형",     "프로필 → 평점·리뷰 → 하단 요청 버튼", lambda s: has(s, ["작성자/프로필"], 1) and has(s, ["평점·리뷰", "리뷰 목록"]) or has(s, ["평점·리뷰 요약"], 1)),
  ("글형",       "작성자 줄 → 사진·본문 → 반응·댓글", lambda s: has(s, ["작성자/프로필", "본문 글", "반응"]) ),
 ],
 "form": [
  ("한 질문씩",   "진행 표시 + 큰 질문 하나 + 선택지, 하단 버튼", lambda s: has(s, ["질문 하나", "숫자 키패드"])),
  ("조건 검색",   "출발·도착·장소 칸 + 날짜 → 찾기 버튼, 아래 최근·추천", lambda s: has(s, ["입력 칸 여러 개", "검색창"], 2) and has(s, ["시간·날짜", "월 달력", "다음 행동", "지도"])),
  ("날짜·시간 고르기", "달력 → 시간 칸 → 하단 버튼", lambda s: has(s, ["시간·날짜", "월 달력"], 2)),
  ("옵션·결제",   "옵션 고르기 + 가격 → 하단 결제 버튼", lambda s: has(s, ["옵션 선택", "가격·할인", "결제수단"])),
  ("한 화면 기록", "여러 칸 + 분류 격자·사진 첨부를 한 화면에", lambda s: has(s, ["입력 칸 여러 개", "사진 첨부"])),
 ],
 "result": [
  ("완료형",     "결과 큰 문구 + 요약 카드 + 다음 행동", lambda s: has(s, ["결과 큰 문구"], 2) and not has(s, ["차트", "목록 행"])),
  ("추천 결과형", "결과 문구·요약 → 그에 맞는 목록", lambda s: has(s, ["결과 큰 문구"], 2) and has(s, ["목록 행", "차트", "지도"])),
  ("리포트형",   "기간 고르기 → 큰 숫자 → 차트 → 항목별 순위·목록", lambda s: has(s, ["차트", "현황 카드", "인체"])),
  ("증표형",     "QR·바코드 + 정보 행", lambda s: has(s, ["QR", "바코드"])),
 ],
 "list": [
  ("지도+목록",  "지도 위·아래로 결과 목록, 필터 칩", lambda s: has(s, ["지도"], 3)),
  ("상품 격자",  "필터 칩·정렬 → 2~3열 상품 격자", lambda s: has(s, ["상품 격자"])),
  ("순위",      "탭·칩 → 번호 달린 랭킹 목록", lambda s: has(s, ["랭킹"], 3)),
  ("카드 피드",  "세로 큰 카드(사진+글)가 이어진다", lambda s: has(s, ["세로 카드 피드"])),
  ("행 목록",    "검색·칩 → 같은 높이의 목록 행", lambda s: has(s, ["목록 행"])),
 ],
}

def screens(src):
    """(출처, 앱 이름, 도메인, kind, slots) — store: 스토어 스크린샷(kind는 에이전트 판정), mweb: 모바일 웹(kind = 찍은 주소, 무효 장 제외)"""
    for f in sorted((HERE / "labels").glob("*.out.json")):
        mweb = f.name.startswith("mweb")
        if src not in ("all", "mweb" if mweb else "store"): continue
        for a in json.load(open(f)):
            if mweb:
                if a["valid"]: yield "mweb", a["site"], a["domain"], a["page"], a["slots"]
                continue
            name = a["name"].split(" - ")[0].split(":")[0].strip()
            for sc in a["screens"]: yield "store", name, a["domain"], sc["kind"], sc["slots"]

def main():
    src = next((x.split("=")[1] for x in sys.argv if x.startswith("--src=")), "all")
    apps = collections.defaultdict(lambda: collections.defaultdict(set)); n = collections.Counter(); miss = collections.Counter(); misses = collections.defaultdict(list)
    for o, name, dom, k, slots in screens(src):
                if k not in RULES: continue
                n[k] += 1; s = strip(slots)
                if k == "home": s = [x for x in s if x != "검색창"]  # 웹·앱 홈 대부분이 맨 위에 검색창 — 유형을 가르지 않는다
                for typ, _, fn in RULES[k]:
                    if fn(s): apps[k][typ].add(f'{name}({dom})'); break
                else: miss[k] += 1; misses[k].append(f"{o}:{name} " + " › ".join(slots[:6]))
    out = {}
    for k, rules in RULES.items():
        out[k] = [{"type": t, "shape": d, "apps": sorted(apps[k][t]), "n": len(apps[k][t])} for t, d, _ in rules]
    if "--json" in sys.argv:
        json.dump({"screens": n, "unmatched": miss, "archetypes": out}, open(HERE / "archetypes.json", "w"), ensure_ascii=False, indent=1); return
    for k in RULES:
        print(f"\n### {k} — 화면 {n[k]}장, 미분류 {miss[k]} ({miss[k] * 100 // max(n[k], 1)}%)")
        for r in out[k]:
            ok = "✅" if r["n"] >= 3 else "·"
            print(f"| {ok} {r['type']} | {r['n']} | {r['shape']} | {', '.join(x.split('(')[0] for x in r['apps'][:7])} |")
        if "--miss" in sys.argv: print("\n".join("   미분류 " + m for m in misses[k]))
main()
