# 이미지 — 서브에이전트 프롬프트

1.5단계에서 사진·그림 자리가 하나라도 있으면 서브에이전트 1개에 아래를 준다(`{{OUT}}` = out 절대경로, `{{SK}}` = 스킬 절대경로, screens.json·journey.md 사실 표를 같이 붙인다).

---
이 앱 화면들의 **이미지 자리**를 채운다. 시간 상한 3분.

1. **자리 목록** `{{OUT}}/image_slots.json`을 먼저 쓴다:
   `[{"slot": "studio-1", "screens": ["studio-detail"], "what": "필라테스 스튜디오 내부, 기구가 보이게", "ratio": "4:3", "kind": "photo|drawing", "query": "pilates studio reformer"}]`
   - **photo**(스톡 실사): 사람·머리카락·음식·장소·실제 제품처럼 "진짜인지"가 내용인 것.
   - **drawing**(SVG): 도식(타입 표·단계), 아이콘성 사물, 같은 사람이 시간에 따라 바뀌는 연속 기록(스톡으로 같은 사람을 못 맞춘다), 추상 배경.
   - 자리 수는 화면에서 실제로 보이는 만큼만(보통 6~12). 같은 사진을 여러 화면이 쓰면 slot 하나.
2. 바로 `python3 {{SK}}/scripts/openverse.py placeholders {{OUT}}` → photo 자리마다 `assets/photos/<slot>.jpg` 자리표시가 생긴다. drawing 자리는 `assets/domain/<slot>.svg`를 지금 바로 쓴다(아래 규칙). **여기까지 끝나면 메인에게 경로 목록을 돌려준다고 생각하고, 이어서 진짜 사진으로 교체한다.**
3. photo 자리마다: `python3 {{SK}}/scripts/openverse.py search {{OUT}} <slot> "<영어 검색어>" --ratio <비율>` → 출력된 `sheet.jpg` 한 장을 **직접 보고** 내용(what)에 맞는 번호를 고른다 → `python3 {{SK}}/scripts/openverse.py pick {{OUT}} <slot> <번호> --ratio <비율>`. 맞는 게 없으면 검색어를 한 번 바꿔 재검색, 그래도 없으면 그 자리를 drawing으로 바꾼다(자리표시 jpg는 지우고 image_slots.json의 kind도 바꾼다).
   - 사람: 얼굴이 주인공이 아닌 사진(뒷모습·손·크롭) 우선. PRD에 얼굴 가림 기능이 있으면 `--blur-faces`.
   - 워터마크·글자 많은 사진·저화질·광고 사진은 고르지 않는다.
4. drawing SVG 규칙: viewBox 지정, 고정 색 허용(사진처럼 브랜드와 무관한 자연색), 얼굴 그리지 않음, 글자 라벨 금지, 그라데이션은 은은하게 1개까지. 도식은 단순한 선·면으로.
5. 끝나면 `image_slots.json`의 최종 kind와 파일 경로, 고르지 못한 자리를 한 줄씩 보고.
---

빌드 에이전트는 `<div class="photo"><img src="../assets/photos/studio-1.jpg" alt="스튜디오 내부"></div>`처럼 경로만 쓴다(.photo 기본 4:3, 수정자 is-3x4·is-1x1·is-16x9 — 자리표시 상태여도 그대로 둔다 — 이미지 에이전트가 같은 파일을 교체한다).
