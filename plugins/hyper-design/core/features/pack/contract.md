# pack — 계약

```
python3 $SK/features/pack/pack.py <out> [--max-agents 5] [--screens id1,id2,...] [--mode build|state|revise]
```

## 입력 (out 안, 없으면 그 절을 건너뛴다 — screens.json만 필수)
- `screens.json` — 화면 항목·`groups`·`people`
- `journey.md` — `## 시나리오 데이터 표`, `## 사실 표…` 절(그대로 옮긴다)
- `spec_inventory.json` — `covered_by`·rule `target`/`policy`(원문 인용 포함)
- `conventions.json` + `decisions.json` — `source: 시장` 판정이 keep·lighten인 `follow`, 모든 `avoid`(묶음 단위)
- `decisions.json` `voice` — 값에 먼저 나오는 `haeyo`/`hamnida`, 없으면 haeyo
- `image_slots.json` — `kind: photo` → `../assets/photos/<slot>.jpg`, `kind: icon` → `icons.json`의 그 slot 이름
- `icons.json` — 있으면 COMPONENTS "## 일러스트" 이름 목록을 이것으로 바꾼다
- 플러그인 쪽: `references/principles.md` 전문, `foundation/COMPONENTS.md` 전문, `foundation/voices/<slug>.json` 전문, `foundation/examples/*.html`(kind → 예시: home·list=checklist·detail=day·form=item-edit·result=join)

## 묶는 규칙
- 상태 화면(`<기본>--<상태>` 또는 `state_of`)은 기본 화면과 같은 묶음
- 묶음 수 = min(max-agents, ceil(화면 수 / 4)), 묶음 크기 차이 최소(≤ 2 목표)
- `groups` 순서로 늘어놓고 연속으로 자른다 — 같은 group이 갈리는 횟수 최소

## 출력
- `out/packs/<n>.md` — 1 할 일 · 2 원칙 · 3 COMPONENTS · 4 보이스톤 · 5 사실 표 · 6 화면별(항목·사람·명세·사진·아이콘) · 7 구조 예시 · 8 셀프체크 요약
- `--mode state`: 같은 구성, 할 일 = "기본 화면 파일을 복사해 바뀐 부분만 고친다"
- `--mode revise`: 할 일 · COMPONENTS · 보이스톤 · 고칠 화면 경로만. 요청은 에이전트 프롬프트로
- `out/packs/plan.json` — `{"mode", "agents":[{"pack":"<절대 경로>","screens":[…]}]}`
- 이전 `packs/<숫자>.md`는 지우고 다시 쓴다. 같은 입력 → 같은 바이트(UTF-8)

## 쓰는 쪽
- `agents/screen-writer.md`(build) · `agents/state-writer.md`(state) · `agents/screen-reviser.md`(revise)
- 작성 규칙 원본: `features/pack/writer.md`
