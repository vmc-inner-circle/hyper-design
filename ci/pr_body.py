#!/usr/bin/env python3
"""plugins/k-style-ui-ux/ 를 고친 PR 본문에 '## go 시간 영향' 절이 채워져 있는지 확인한다.

python3 ci/pr_body.py <PR 본문 파일> <바뀐 파일 목록 파일>
템플릿의 주석(<!-- -->)만 남아 있으면 비어 있는 것으로 본다. 이유: AGENTS.md "go를 무겁게 하는 변경"
"""
import re, sys
from pathlib import Path

body = Path(sys.argv[1]).read_text(encoding="utf-8")
changed = Path(sys.argv[2]).read_text(encoding="utf-8").split()
if not any(p.startswith("plugins/k-style-ui-ux/") for p in changed):
    sys.exit(0)
m = re.search(r"^##\s*go 시간 영향\s*$(.*?)(?=^##\s|\Z)", body, re.M | re.S)
text = re.sub(r"<!--.*?-->", "", m.group(1), flags=re.S).strip() if m else ""
if not text:
    print("FAIL: plugins/k-style-ui-ux/ 를 고친 PR은 본문에 '## go 시간 영향' 절을 채운다 — 얻는 것·늘어난 시간(전후 실측), 시간과 무관하면 '영향 없음 — 이유'. AGENTS.md 참고")
    sys.exit(1)
print("OK: go 시간 영향 절 있음")
