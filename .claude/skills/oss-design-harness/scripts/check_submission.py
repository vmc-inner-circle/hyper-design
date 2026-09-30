"""제출 폴더 점검 — HARNESSTON.md 제출 조건. [FAIL]이 없어야 제출할 수 있다.

    submissions/{github_id}/
    ├── index.html      # 결과물 (여러 파일이면 index.html에서 진입)
    ├── prompt-log.md   # 사용자 개입 원문과 횟수
    └── elapsed.txt     # PRD 입력부터 완성까지 걸린 시간

사용법:
    python .claude/skills/oss-design-harness/scripts/check_submission.py --root submissions/{github_id}
"""

import argparse
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
MAX_TURNS = 5


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    root = Path(ap.parse_args().root)
    fails, warns = [], []

    if not root.is_dir():
        print(f"[FAIL] 제출 폴더 없음: {root}")
        sys.exit(1)

    # index.html: 있고, 여기서 이어지는 화면 링크가 살아 있어야 한다 (파일을 바로 열어 쓰는 프로토타입)
    index = root / "index.html"
    if not index.exists():
        fails.append("index.html 없음 — 결과물 진입점")
    else:
        html = index.read_text(encoding="utf-8-sig")
        hrefs = re.findall(r'href="([^"#:?]+\.html)"', html)
        if not hrefs:
            fails.append("index.html에 화면 링크가 없음")
        seen = set()
        queue = [index.parent / h for h in hrefs]
        while queue:
            f = queue.pop().resolve()
            if f in seen:
                continue
            seen.add(f)
            if not f.exists():
                fails.append(f"깨진 링크: {f.relative_to(root.resolve()) if root.resolve() in f.parents else f}")
                continue
            page = f.read_text(encoding="utf-8-sig")
            queue += [f.parent / h for h in re.findall(r'href="(?!//)([^"#:?]+\.html)"', page)]
            for src in re.findall(r'src="(?!//)(\.\./[^"]+|[^":]+\.js)"', page):
                if not (f.parent / src).resolve().exists():
                    fails.append(f"{f.name}: 없는 파일 {src} (theme.js 등을 함께 복사했는지)")
        if seen:
            print(f"index.html에서 이어지는 화면 {len(seen)}개 확인")

    # prompt-log.md: 회차 원문과 총 개입 수 n / 5, 회차 수와 n이 같아야 한다
    log = root / "prompt-log.md"
    if not log.exists():
        fails.append("prompt-log.md 없음 — 사용자 개입 원문과 횟수")
    else:
        text = log.read_text(encoding="utf-8-sig")
        m = re.search(r"총\s*개입\s*횟수\s*[:：]\s*(\d+)\s*/\s*5", text)
        turns = len(re.findall(r"^##\s*\d+\s*회", text, re.M))
        if not m:
            fails.append("prompt-log.md: '총 개입 횟수: n / 5' 줄 없음 (submissions/README.md 형식)")
        else:
            n = int(m.group(1))
            if n > MAX_TURNS:
                fails.append(f"prompt-log.md: 개입 {n}회 — 5회 이하여야 함")
            if turns and n != turns:
                fails.append(f"prompt-log.md: 총 개입 {n}회라고 적었는데 회차 제목(## n회)은 {turns}개")
        if turns == 0:
            fails.append("prompt-log.md: 회차 기록(## 1회 …)이 없음")
        if not re.search(r"^##\s*1\s*회[^\n]*\n(?:.*\n){0,3}?.*(PRD|prd|\.md)", text, re.M):
            warns.append("prompt-log.md: 1회가 PRD 입력인지 확인할 수 없음 (첫 프롬프트는 PRD만)")

    # elapsed.txt: 시작·종료·소요
    el = root / "elapsed.txt"
    if not el.exists():
        fails.append("elapsed.txt 없음 — PRD 입력부터 완성까지 걸린 시간")
    else:
        t = el.read_text(encoding="utf-8-sig")
        for key in ("시작", "종료", "소요"):
            if not re.search(rf"^{key}\s*[:：]\s*\S", t, re.M):
                fails.append(f"elapsed.txt: '{key}: …' 줄 없음 (submissions/README.md 형식)")

    for w in warns:
        print(f"[WARN] {w}")
    for f in fails:
        print(f"[FAIL] {f}")
    print(f"제출 폴더 {root} · FAIL {len(fails)} · WARN {len(warns)}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
