# loop — 하네스 자동 개선 루프

사람 개입 없이 **구동 → 채점 → 비평 → 하네스 수정**을 반복하기 위한 도구.

```
python3 loop/run.py prd/family-trip.md /tmp/hd/runN          # 격리 폴더에서 하네스 1회 구동
python3 loop/evaluate.py /tmp/hd/runN prd/family-trip.md /tmp/hd/baseline-family-trip
```

- `run.py` — 하네스(`plugins/hyper-design/core`)만 빈 폴더에 복사해 `claude -p` 헤드리스로 돌린다. 하네스가 `[[ASK 페이지]]`로 질문하면 페이지를 캡처해 **가상 사용자**(`sim_user.md`, 비개발자 페르소나, 선택형으로만 답함)가 답한다. `prompt-log.md`·`elapsed.txt`(가상 사용자 응답 시간 제외)를 남긴다.
- `score.py` — [성공 기준](../docs/success-criteria.md) 기계 채점(Playwright, 렌더링된 computed style 측정). 하네스 안에도 `audit.py`로 같은 파일이 들어가 자가 수정에 쓰인다.
- `evaluate.py` — 기계 채점 + 평가 에이전트(`judge.md`: P0~P3 비평, 루브릭 6항목) + 바닐라 대비 블라인드 비교 5회(`compare.md`).
- 바닐라 비교군: 같은 PRD를 하네스 없이 Claude Code에 넣은 결과(`/tmp/hd/baseline-*`).

## 과적합 방지

- 구동마다 빈 폴더에서 하네스만 복사한다(이전 결과·채점 기준 비노출, 상위 CLAUDE.md 차단).
- 평가 에이전트의 비평은 **PRD 고유 내용이 아니라 하네스 규칙으로 일반화된 원인(cause)** 만 하네스에 반영한다.
- 청첩장 PRD(연습용)와 가족여행 PRD(결과물용)를 같은 버전으로 함께 돌려 한쪽에만 맞춰지지 않았는지 본다.
