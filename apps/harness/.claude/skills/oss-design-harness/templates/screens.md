<!--
4.5단계(최종 미리보기) 산출물. 프로젝트의 design/screens.md로 복사해서 채운다.
스킬이 brief.md §1로 초안을 만들고, 최종 미리보기 탭에서 사용자가 "빼요 / 다른 걸로"로 고친 뒤 확정한다.
figma-builder 화면 STAGE는 이 표의 "구성" 열만 보고 인스턴스를 배치한다. 표에 없는 컴포넌트는 만들지 않는다.
figma_audit.py --screens 가 이 표와 실제 화면을 대조한다 (component.manifest).
-->

status: draft
confirmed_at:

# Screens

구성은 위→아래 순서. 원문자 번호는 최종 미리보기 폰 프레임의 라벨과 같다 (화면당 최대 5개). 컴포넌트 이름은 02 Components 페이지의 이름과 정확히 같아야 한다.

| 순번 | 화면 | slug | 구성 (위→아래) | 상태 프레임 |
|---|---|---|---|---|
| 1 | 홈 | home | ① AppBar(제목) · ② Card×n · ③ BottomCTA(첫 액션) · ④ TabBar | default·empty·loading·error·long-title·many-items·text-120 |
| 2 | | | | |

## 사용자 수정 이력

최종 미리보기 탭에서 들어온 remove / swap 을 그대로 적는다. 출처는 `feedback/screen-<slug>`.

| 화면 | 변경 | 원문 | 회차 |
|---|---|---|---|
