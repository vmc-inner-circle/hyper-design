---
name: fix
description: hyper-design 캔버스에서 '보내기'로 복사한 메모를 화면에 반영한다. 사용자가 `[hyper-design 수정 요청]`으로 시작하는 글을 붙여넣거나 "캔버스 메모 반영해줘"처럼 캔버스 메모를 적용하라고 할 때 트리거.
---

# hyper-design:fix — 캔버스 메모 반영

**붙여넣은 요청문 → 질문은 답하고, 고칠 것은 화면별 수정 에이전트가 그 요소만 고친다.** 다른 요소·다른 화면은 건드리지 않는다.

**경로**: 이 스킬을 불러올 때 표시되는 Base directory의 `../../core`가 공용 폴더다. 맨 처음 한 번 `SK=$(cd "<Base directory>/../../core" && pwd)`로 절대경로를 정하고, 모든 명령·서브에이전트 프롬프트에 그 절대경로를 쓴다.

## 요청문 형식 (캔버스 '보내기'가 만든다)

```
[hyper-design 수정 요청] out=C:/Code/demo/out · 2건
1. screen=order-items · path=main > section.block:nth-of-type(2) > a.row:nth-of-type(1)
   text="와이셔츠 · 1벌 2,500원" · intent=change
   요청: 가격을 오른쪽 끝으로 붙이고 굵게
2. screen=home · path=main > div.badge:nth-of-type(1)
   text="바뀜" · intent=question
   요청: 이 배지는 무슨 뜻?
```

## 진행 — 한 턴

### 1. 읽기
- `SK`를 정한다. 첫 줄에서 `out=` 경로(아래 `<out>`)를 읽고, 번호 항목마다 `screen`·`path`·`text`·`intent`·`요청`을 뽑는다.
- `out=`이 없으면 한 번만 묻고 턴을 끝낸다: "어느 결과 폴더(out)의 화면인가요? 경로를 알려주세요." `[[ASK]]`

### 2. 질문 (`intent=question`)
- 메인이 채팅으로 바로 답한다 — 항목마다 짧은 한 문단. 파일은 고치지 않는다.
- 답할 때 `<out>/screens/<screen>.html`·`<out>/screens.json`·`<out>/decisions.json`을 필요한 만큼만 읽는다. 전문 용어 금지.

### 3. 고치기 (`intent=change`)
- 화면별로 묶는다. 고칠 화면 id를 모아 `python3 $SK/features/pack/pack.py <out> --mode revise --screens <id1,id2,…>` → `<out>/packs/plan.json`의 pack마다 하나씩.
- pack마다 서브에이전트 `hyper-design:screen-reviser`를 띄운다 — **한 메시지에 최대 5개, `model` 인자는 넣지 않는다**(정의 파일이 haiku로 정한다). 5개를 넘으면 다음 메시지에서 나머지.
- 프롬프트 형식:

```
PACK=<pack 절대경로>
화면 파일: <out>/screens/<screen>.html
요청:
<번호>. CSS 경로: <path>
   원래 글자: "<text>"
   할 것: <요청>
```
- `hyper-design:screen-reviser`를 서브에이전트 종류로 쓸 수 없으면 일반 서브에이전트를 `model: "haiku"`로 띄우고, 프롬프트 맨 위에 `$SK/../agents/screen-reviser.md`의 본문(입력·순서·규칙·보고)을 그대로 붙인다.

### 4. 확인
- 모두 돌아오면 같은 메시지에서 포그라운드로: `python3 $SK/scripts/selfcheck.py <out>` · `python3 $SK/features/canvas/build_canvas.py <out>`.
- selfcheck ❌가 이번 수정 때문이면 메인이 Edit 도구로 고친다(1회). 에이전트가 `not found`로 보고한 요청은 메인이 화면 파일을 읽고 직접 고치거나, 못 찾으면 그대로 보고한다.

### 5. 마지막 메시지
- 항목마다 한 줄: `<번호> · done` / `<번호> · answered` / `<번호> · not found (이유 한마디)`.
- 안내 한 줄: "캔버스에서 '보낸 것 지우기'를 누르면 반영된 메모가 정리돼요."
- 마지막 줄: `[[DONE <out>/index.html]]` — 이 줄 없이 턴을 끝내면 미완성으로 처리된다.

## 참고
- 요청문 형식 원본: `$SK/features/canvas/canvas_template.html`의 `requestText` · 수정 에이전트: `plugins/hyper-design/agents/screen-reviser.md` · 설계: `docs/eungshin/tdr-v2.md` 14-3·14-4
