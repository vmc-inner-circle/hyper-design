# 명세 목록 — 추출 서브에이전트 프롬프트

1단계에서 메인이 여정표를 쓰는 동안 서브에이전트 1개에 아래를 그대로 준다(`{{OUT}}`는 out 폴더 절대경로).

---
`{{OUT}}/prd.md`의 PRD를 읽고 **명세 목록**을 `{{OUT}}/spec_inventory.json`으로 써라. 디자인 판단은 하지 않는다 — PRD에 적힌 것을 빠짐없이, 지어내지 않고 옮긴다.

```json
{"mode": "spec|brief",
 "items": [
  {"id": "S1", "kind": "screen", "name": "짧은 이름", "quote": "PRD 원문 그대로 한 줄(40자 이상이면 앞 60자)"},
  {"id": "P1", "kind": "step", "name": "온보딩 2/5 — 모발 상태", "quote": "…"},
  {"id": "F1", "kind": "feature", "name": "필터 초기화", "quote": "…", "screen_hint": "S3"},
  {"id": "R1", "kind": "rule", "name": "수업 24시간 전까지 무료 취소", "quote": "…", "screen_hint": "S12",
   "state_hint": "error|confirm|done|policy"}]}
```
- `screen`: PRD가 화면·페이지·탭·팝업으로 부른 것. 같은 화면의 섹션·탭은 screen이 아니라 feature.
- `step`: 여러 단계로 나뉜 흐름의 각 단계(온보딩 1/5, 결제 2단계 등).
- `feature`: 화면 안의 요소·동작(버튼·필터·정렬·검색·표시 항목).
- `rule`: 데이터 규칙·제약·예외(기한·횟수·순서·중복·권한 거부·실패 처리). `state_hint`: 사용자가 그 규칙에 부딪히는 순간이 **같은 칸의 오류**면 error, **되돌릴 수 없음·중복 경고**면 confirm, **보낸/신청한 뒤 결과**면 done, 화면에 드러나지 않고 설명으로 충분하면 policy.
- `quote`는 반드시 PRD 원문에서 복사(공백만 달라도 된다). 원문에 없는 항목은 넣지 않는다.
- `mode`: screen+step이 15개 이상이면 spec, 아니면 brief.
- PRD의 "논의점·미정" 항목은 넣지 않는다(메인이 가정 로그에서 다룬다). "MVP 제외"라고 적힌 것도 넣지 않는다.
- 끝나면 kind별 개수만 한 줄로 보고.
---

메인은 받은 목록을 병합하면서 `screen_hint`·`state_hint`를 `covered_by`·`target`·`state`(또는 `policy`)로 확정한다.
