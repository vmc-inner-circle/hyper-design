# icons 계약

`python3 resolve.py <out> [--cache DIR] [--timeout 10] [--offline]`

## 입력
- `core/` — Tier 0(어느 앱에나 쓰는 UI 일반 개념 + 인물 일러스트 5개), `core/manifest.json` `[{"name","file","meaning","kind","source":"core"}]`
- `index.json` — Fluent Emoji 전체 목록(고정 커밋), `<out>/image_slots.json`의 `kind: "icon"` 슬롯. `en`은 문자열 또는 선호 순서 목록

## 출력
- `<out>/assets/fluent/<name>.svg` — Tier 0 전체 + 이번 슬롯이 고른 것만
- `<out>/icons.json` — Tier 0 항목 + 슬롯마다 `{"name","file","meaning":what,"kind","source":"resolved"|"fallback","slot"}`
- `<out>/decisions.json["icon_fallbacks"]` — fallback마다 `{"slot","wanted","used","why":"no match|network|budget"}`. 다른 키는 건드리지 않는다. 같은 슬롯의 이전 줄은 바꿔 쓴다
- stdout 한 줄 요약, 처리한 경우 모두 exit 0

## 매칭 규칙 (도메인 규칙 없음)
1. 질의를 소문자 단어로 나눈다. **마지막 단어(중심 명사)**가 이름 단어(`-`로 나눔)나 키워드 단어에 있어야 후보
2. 여러 단어 질의인데 겹친 단어가 중심 명사 하나뿐이면 거절(`washing machine` → fax-machine 방지)
3. 점수 = 3×(이름 단어 겹침) + (키워드 단어 겹침) + 2(이름 == 질의를 `-`로 이음). 동점 → Tier 0 → 짧은 이름 → 이름순
4. 목록에서 첫 번째로 후보가 나온 질의가 이긴다. Tier 0 이름도 후보다

## fallback
맞는 것 없음·네트워크 실패·시간 상한 초과 → 같은 점수(중심 명사 규칙 없이)로 가장 가까운 Tier 0, 없으면 `clipboard`. `decisions.json`에 한 줄.

## 받기·캐시
- 캐시 `~/.cache/hyper-design/fluent/<sha>/<name>.svg`(`--cache`로 바꿈). 캐시에 있으면 네트워크를 쓰지 않는다
- `.svg`만, 파일당 300 KB 상한, 전체 네트워크 `--timeout`초 상한. `--offline`은 네트워크를 절대 쓰지 않는다
- SVG 정리는 하지 않는다(`<img>`로만 쓰고 출처가 커밋 고정 저장소)

## 고정 커밋
`microsoft/fluentui-emoji` @ `1ffb34c752ecf5d402f04cfb4b392c77f57c54bc` — `index.json`의 `sha`를 그대로 쓴다.

## index.json 다시 만들기 (하네스를 만들 때만)
`python3 build_index.py [--sha <커밋>]` → `index.json`. SHA를 바꾸면 `core/LICENSE.md`의 SHA도 고치고 `pytest tests -q`를 다시 돌린다.
