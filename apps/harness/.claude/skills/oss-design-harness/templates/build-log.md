<!-- 5~7단계 기록. 메인 대화(html-audit), design-auditor(오디트), probe-renderer(fix), figma-builder(figma, 선택)가 이어서 쓴다. -->

# Build Log

## html-audit
- 실행: <날짜>
- 정적: `html_audit.py --design-dir design` exit <n>
- 렌더: `html_audit.py --design-dir design --render` exit <n>
- 실패 규칙: <규칙 키 / 화면·상태 / 요소> (없으면 없음)
- 스크린샷: design/screenshots/html/ (<n>장)

## 오디트 #1
- 대상: HTML
- A단계: html_audit --render 결과 요약
- C단계 실패:
- 진단: 통과 | 국소 결함 | 방향 오류 | 반복 실패
- 다음 행동:

## fix #1
- 입력: design/html-fix-list.md | 오디트 #1 결함 표
- fixed: <규칙 키> <화면/상태/요소> <전 → 후>
- 영향 화면:
- 재검: html_audit 정적 exit <n> · 렌더 exit <n>

## figma (선택 — 사용자가 "Figma 생성"을 지시했을 때만)

figma_file: <파일 키 또는 URL>
figma_read_calls_today: 0

### STAGE=tokens
- 실행: <날짜>
- 변수·스타일 ID 표
- parity:

### STAGE=components
- 컴포넌트 ID 표
- 누락·질문:
- parity:

### STAGE=screens
- 프레임 ID 표 (화면 × default, STATES= 요청분)
- 누락 컴포넌트:
- parity: figma_parity.py exit <n>

### STAGE=fix #1
- fixed: <결함> → <노드> <전/후>
