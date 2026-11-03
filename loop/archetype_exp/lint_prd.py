"""익명 PRD 검사 — 원본 앱 이름·화면 구조 낱말이 있으면 실패(종료 코드 1).
python3 lint_prd.py <prd.md> <app id>
"""
import sys, json, re, pathlib
BAN = "홈 메인 첫\\s*화면 화면 탭 격자 아이콘 배너 캐러셀 카드 피드 목록 리스트 레이아웃 스크롤 버튼 위젯 큐레이션 대시보드 타임라인 썸네일 그리드 메뉴 섹션 페이지 상단 하단 팝업".split()
OK = ["카드사", "신용카드", "체크카드", "카드 결제", "카드결제", "교통카드", "카드 대금", "카드값", "메인 요리"]  # 결제 수단으로서의 카드 등은 허용
txt = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"); app = sys.argv[2]
apps = {a["id"]: a for a in json.load(open(pathlib.Path(__file__).parent / "apps.json"))}
names = [x.strip() for x in apps[app]["exclude"].split(",")] + [a["exclude"].split(",")[0] for a in apps.values()]
clean = txt
for w in OK: clean = clean.replace(w, "")
hits = [w for w in BAN if re.search(w, clean)] + [n for n in names if n.lower() in txt.lower()]
if hits: print("FAIL", app, sorted(set(hits))); sys.exit(1)
print("OK", app, len(txt), "자")
