<!--
4.5단계(최종 미리보기) 산출물. 프로젝트의 design/screens.md로 복사해서 채운다.
스킬이 brief.md §1로 초안을 만들고, 최종 미리보기 탭에서 사용자가 "빼요 / 다른 걸로"로 고친 뒤 확정한다.
figma-builder 화면 STAGE는 이 표의 "구성" 열만 보고 인스턴스를 배치한다. 표에 없는 컴포넌트는 만들지 않는다.
figma_audit.py --screens 가 이 표와 실제 화면을 대조한다 (component.manifest, state.frames).

상태 프레임 열:
  - 이 표가 상태 프레임의 **유일한 출처**다. 여기 없는 프레임은 만들지 않는다(state.excess 로 실패).
  - default 는 항상. 나머지는 brief.md §1 '정의된 상태'에서 파생된 것만. 화면당 default 포함 최대 3개.
  - loading / success 를 쓰지 않는다 — 짧은 대기는 Skeleton 컴포넌트, 긴 작업은 독립 화면(행 추가).
  - long-title · many-items · text-120 같은 경계값은 상태가 아니다. default 화면의 콘텐츠로 확인한다.
  - 해당 상태가 없는 화면은 default 하나로 끝낸다. 칸을 채우려고 늘리지 않는다.
-->

status: draft
confirmed_at:

# Screens

구성은 위→아래 순서. 원문자 번호는 최종 미리보기 폰 프레임의 라벨과 같다 (화면당 최대 5개). 컴포넌트 이름은 02 Components 페이지의 이름과 정확히 같아야 한다.

| 순번 | 화면 | slug | 구성 (위→아래) | 상태 프레임 |
|---|---|---|---|---|
| 1 | 홈 | home | ① AppBar(제목) · ② Card×n · ③ BottomCTA(첫 액션) · ④ TabBar | default·empty |
| 2 | | | | |

## 사용자 수정 이력

최종 미리보기 탭에서 들어온 remove / swap 을 그대로 적는다. 출처는 `feedback/screen-<slug>`.

| 화면 | 변경 | 원문 | 회차 |
|---|---|---|---|
