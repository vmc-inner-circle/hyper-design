"""사람이 손으로 내린 제품 결정(정답지)을 하네스가 스스로 재현했는지 센다.
python3 loop/answer_key.py <out_dir> family-trip
정답지는 docs/scope-family-trip.md 의 10/1 결정에서 뽑았다.
"""
import sys, re, json, pathlib
out = pathlib.Path(sys.argv[1]); prd = sys.argv[2]
html = {f.stem: re.sub(r"<[^>]+>", " ", f.read_text(encoding="utf-8")) for f in (out / "screens").glob("*.html")}
raw = {f.stem: f.read_text(encoding="utf-8") for f in (out / "screens").glob("*.html")}
alltext = " ".join(html.values())
try: man = json.loads((out / "screens.json").read_text(encoding="utf-8"))
except Exception: man = {"screens": []}
try: dec = json.loads((out / "decisions.json").read_text(encoding="utf-8"))
except Exception: dec = {"items": []}
KEYS = {
 "family-trip": [
  ("변경 알림을 보내지 않는다(열면 보이는 표시로)", lambda: not re.search(r"소식 보내기|알림 보내기|바뀐 소식|소식함|묶음 소식|모아 (보내|전해)|알림 (설정|받기)|저녁 \d+시", alltext + " " + " ".join(s.get("title", "") for s in man.get("screens", [])))),
  ("수동 '소식 보내기' 없음 — 확정이 곧 공유", lambda: not re.search(r"(가족|부모님)(께|에게) (보내기|공유하기)|공유하기", alltext)),
  ("사람을 역할 이름으로 낮춰 부르지 않는다", lambda: not re.search(r"보기만|읽기 전용|게스트|확인만 하", alltext)),
  ("부모가 묻는 대신 '궁금해요' 한 번 누르기", lambda: "궁금" in alltext),
  ("홈이 시기마다 바뀐다(출발 전·임박·여행 중)", lambda: sum(1 for s in man.get("screens", []) if s["id"].startswith("home") and "--" not in s["id"] and "edit" not in s["id"]) >= 2),
  ("같이 짜지 않는 사람 화면에 탭바 없음", lambda: not any('class="tabbar"' in raw.get(s["id"], "") for s in man.get("screens", []) if s.get("role") == "everyone")),
  ("제품 판단 장부가 있고, PRD 요구사항을 가볍게 바꿨다면 물어봤다", lambda: (out / "decisions.json").exists() and all(i.get("ask") for i in dec.get("items", []) if i.get("source") == "PRD" and i.get("verdict") in ("cut", "lighten"))),
 ],
}
ok = 0
for name, fn in KEYS.get(prd, []):
    try: r = bool(fn())
    except Exception: r = False
    ok += r; print(("✅ " if r else "❌ ") + name)
print(f"정답지 재현 {ok}/{len(KEYS.get(prd, []))}")
