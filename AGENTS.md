# k-style-ui-ux — 에이전트 작업 규칙

- 절대로 main에 push하지 않는다. branch를 만들고, GitHub에서 PR을 병합해야한다.
- PR 본문에는 웬만하면 이미지를 붙인다(화면 전후 비교·캔버스·측정 결과 캡처). 이미지는 `docs/pr/<주제>/`에 커밋하고 본문에서 `https://github.com/vmc-inner-circle/k-style-ui-ux/blob/<커밋 SHA>/docs/pr/<주제>/<파일>?raw=true`로 건다 — 브랜치 이름 대신 SHA로 걸어 브랜치를 지워도 안 깨지게.
- 하네스는 `plugins/k-style-ui-ux/` 폴더 하나를 Claude Code·Codex·Cursor가 함께 설치한다(사본·빌드 없음). 버전은 그 안의 manifest 4개와 `CHANGELOG.md` 맨 위가 같아야 한다(CI `ci/verify.py`).
- 스킬 문구는 특정 에이전트에 묶지 않는다. Claude Code·Codex·Cursor 차이(동시 실행·모델 등급·스킬 부르는 법)는 `plugins/k-style-ui-ux/skills/go/SKILL.md`의 "에이전트마다 다른 것"에만 적는다.
- 구조·설치: `plugins/k-style-ui-ux/README.md`

## go를 무겁게 하는 변경 — 얻는 것과 잃는 시간을 같이 낸다

`go`의 가치는 "PRD 한 장 → 15분 안에 완성된 디자인"이다. 단계·검사·화면·서브에이전트를 더하면 결과는 나아질 수 있지만 그만큼 느려지고 토큰이 든다. 더하는 게 언제나 좋은 게 아니다.

- `plugins/k-style-ui-ux/`를 고치는 PR은 본문에 `## go 시간 영향` 절을 쓴다(CI `ci/pr_body.py`가 확인한다). 템플릿: `.github/pull_request_template.md`
- 시간이 늘 수 있는 변경이면 같은 PRD로 전후를 실측한다 — `python3 loop/run.py <prd> <폴더>`가 `elapsed.txt`를 남긴다. PRD 2개 이상을 권한다.
- 늘어난 시간이 얻는 것에 비해 크면 `go` 대신 `max`나 별도 스킬로 보내는 것을 먼저 검토하고, 그러지 않은 이유를 적는다.
- 시간과 무관한 변경(문서·검사 스크립트 버그 수정 등)이면 "영향 없음 — 이유" 한 줄이면 된다.
