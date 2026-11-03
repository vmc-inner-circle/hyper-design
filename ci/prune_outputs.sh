#!/usr/bin/env bash
# .gitignore에 걸리는데 추적 중인 파일(산출물)을 git에서 뺀다. 로컬 파일은 남는다.
# 멤버 PR 브랜치에 main을 merge한 뒤에도 같은 기준으로 돌린다. 기준은 .gitignore 한 곳.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
n=$(git ls-files -ci --exclude-standard | wc -l | tr -d ' ')
[ "$n" = 0 ] && { echo "정리할 산출물 없음"; exit 0; }
git ls-files -ci --exclude-standard -z | xargs -0 git rm -q --cached --
echo "산출물 ${n}개를 추적에서 뺐다 — 커밋하면 된다"
