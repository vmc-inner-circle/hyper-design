# 이미지 — 자리 목록 · 사진 생성(imggen) · 아이콘 고르기(resolve)

사진은 `$SK/features/images/imggen.py`가 시트로 생성·자르기(계약: `features/images/contract.md`), 아이콘은 `$SK/features/icons/resolve.py`(계약: `features/icons/contract.md`). 메인은 자리 목록만 쓴다.

## 1. 자리 목록 — 메인이 1.5단계에서 직접 쓴다(1분)

`out/image_slots.json`:
```json
[{"slot": "studio-1", "kind": "photo", "screens": ["studio", "find"], "what": "리포머 기구가 줄지어 있는 밝은 필라테스 스튜디오", "ratio": "4:3",
  "en": "a bright pilates studio with rows of reformer machines"},
 {"slot": "ic-basket", "kind": "icon", "screens": ["home", "order-items"], "what": "세탁물 바구니", "en": ["laundry basket", "basket"]},
 {"slot": "map-area", "kind": "drawing", "screens": ["area-out"], "what": "서비스 지역 지도"}]
```
- `kind`는 셋 중 하나:
  - **photo**(실사 → imggen): 사람·머리카락·몸·음식·장소·실제 제품처럼 "진짜인지"가 내용인 것 — **사람·머리 자리는 무조건 photo**(같은 사람이 아니어도 된다). `ratio` 필수(`1:1`·`4:3`·`3:4`·`16:9`).
  - **icon**(Fluent 컬러 일러스트 → resolve): 아이콘성 사물(바구니·트럭·영수증·열쇠처럼 물건 하나). 결과 이름은 `out/icons.json`의 그 slot 항목.
  - **drawing**(SVG, 빌드 에이전트가 그린다): 도식(타입 표·단계)·지도(도로 + 핀)·QR만. 사람·머리·얼굴·동물 형상은 그리지 않는다.
- `en`은 photo·icon에 필수:
  - photo: 영어 한 문장 묘사, 구도까지(뒷모습·크롭·실내·위에서). 생성 프롬프트로 쓴다.
  - icon: 영어 사물 이름 **선호 순서 목록** — 대안을 함께 적는다(`["washing machine", "bubbles"]`). 마지막 단어(중심 명사)가 맞는 이모지만 고른다.
- 목록·피드·격자에 보이는 항목 수만큼 **서로 다른 slot** — 같은 사진 반복 금지.
- **사람·머리 자리는 사람 카드(`screens.json` people)의 대상과 닮게**: 국적·나이·성별을 what과 en에 넣는다(예: 한국 20대 여성 사용자 → "korean woman in her 20s with natural curly hair"). 얼굴 가림 기능이 켜진 화면은 얼굴 없는 크롭(머리카락·뒷모습)으로 적는다.
- 같은 메시지에서: `python3 $SK/features/images/imggen.py out` **백그라운드**(자리표시를 먼저 쓰고 생성이 끝나면 덮어쓴다) + `python3 $SK/features/icons/resolve.py out`(몇 초).

빌드 에이전트는 `<div class="photo"><img src="../assets/photos/studio-1.jpg" alt="스튜디오 내부"></div>`처럼 경로만 쓴다(.photo 기본 4:3, 수정자 is-3x4·is-1x1·is-16x9). 자리표시 상태여도 그대로 둔다 — imggen이 같은 파일을 교체한다. 아이콘은 `../assets/fluent/<이름>.svg`.
