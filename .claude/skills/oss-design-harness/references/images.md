# 이미지 — 자리 목록 · 탐색(빠른 모델 여럿) · 선택(Sonnet 1)

내부 검토용이다 — 저작권 사진도 쓴다(출처는 credits.json에 남긴다). 검색 도구: `$SK/scripts/imgsearch.py`(빙 이미지 → 위키미디어 커먼즈 → Openverse, 워터마크 스톡 사이트는 자동 제외).

## 1. 자리 목록 — 메인이 1.5단계에서 직접 쓴다(1분)

`out/image_slots.json`:
```json
[{"slot": "studio-1", "screens": ["studio", "find"], "what": "리포머 기구가 줄지어 있는 밝은 필라테스 스튜디오", "ratio": "4:3", "kind": "photo",
  "queries": ["필라테스 리포머 스튜디오", "pilates reformer studio bright"]}]
```
- **photo**(실사): 사람·머리카락·몸·음식·장소·실제 제품처럼 "진짜인지"가 내용인 것 — **사람·머리 자리는 무조건 photo**(같은 사람이 아니어도 된다).
- **drawing**(SVG, 메인이나 빌드 에이전트가 그린다): 도식(타입 표·단계), 지도(도로 + 핀), QR, 아이콘성 사물. 사람·머리·얼굴·동물 형상은 그리지 않는다.
- 목록·피드·격자에 보이는 항목 수만큼 **서로 다른 slot** — 같은 사진 반복 금지.
- queries: 한국어 1개 + 영어 1개 이상, 구도까지(뒷모습·크롭·실내·위에서).
- 바로 `python3 $SK/scripts/imgsearch.py placeholders out` → 빌드는 `../assets/photos/<slot>.jpg` 경로만 쓴다.

## 2. 탐색 에이전트 — `model: "haiku"`, 자리 4개당 1개(최대 6), 빌드와 같은 메시지에서

프롬프트(`{{OUT}}`·`{{SK}}` 절대경로, 맡은 slot 항목을 붙인다):
---
맡은 이미지 자리마다 사진 후보를 찾아 4장 이내로 추린다. 자리당 2분 이내.
1. `python3 {{SK}}/scripts/imgsearch.py search {{OUT}} <slot> "<검색어1>" "<검색어2>" --ratio <비율>` → 출력된 sheet 이미지를 Read로 본다.
2. what(무엇이 보여야 하나)에 **분명히** 맞는 번호를 고른다. 거를 것: 일러스트·만화·도식(사진 자리인데), 글자·로고가 크게 박힌 것, 콜라주, 워터마크, 흐리거나 작은 것, 엉뚱한 소재.
3. 맞는 게 2장 미만이면 검색어를 바꿔(동의어·구도·영어↔한국어) 한 번 더 search(새 시트가 생긴다).
4. `python3 {{SK}}/scripts/imgsearch.py shortlist {{OUT}} <slot> <번호…>`(최대 4개).
5. 끝나면 `{"slot": [번호…]}` 한 줄씩만 보고. 못 찾은 자리는 `{"slot": []}`.
---

## 3. 선택 에이전트 — `model: "sonnet"`, 1개, 탐색이 모두 돌아오면

프롬프트(slot 목록 + 탐색 결과 + PRD에 얼굴 가림 기능이 있는지 한 줄):
---
자리마다 `{{OUT}}/.cands/<slot>/shortlist.jpg`를 Read로 보고 1장을 고른다.
- 기준: what에 맞는가 > 화면들끼리 톤이 어울리는가 > 같은 사람·같은 사진이 여러 자리에 겹치지 않는가.
- `python3 {{SK}}/scripts/imgsearch.py pick {{OUT}} <slot> <번호> --ratio <비율>` (얼굴이 보이고 PRD에 얼굴 가림 기능이 있으면 `--blur-face`).
- shortlist가 비었거나 다 틀리면 직접 `search` 한 번 더(검색어를 바꿔) → 그래도 없으면 가장 가까운 것을 고르고 보고에 적는다(자리표시 회색으로 남기지 않는다).
- 끝나면 자리별 고른 사진 제목 한 줄씩 보고.
---

빌드 에이전트는 `<div class="photo"><img src="../assets/photos/studio-1.jpg" alt="스튜디오 내부"></div>`처럼 경로만 쓴다(.photo 기본 4:3, 수정자 is-3x4·is-1x1·is-16x9). 자리표시 상태여도 그대로 둔다 — 선택 에이전트가 같은 파일을 교체한다.
