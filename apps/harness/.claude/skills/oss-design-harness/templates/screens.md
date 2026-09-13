<!--
5단계 HTML 산출물(최종 미리보기)의 구성표. 프로젝트의 design/screens.md로 복사해서 채운다.
스킬이 brief.md §1로 초안을 만들고, 최종 미리보기 탭에서 사용자가 "빼요 / 다른 걸로"로 고친 뒤 확정한다.
최종 HTML(final-preview.html)은 이 표를 그대로 마크업한다: slug = data-screen, 구성 열 컴포넌트명 = data-component, 상태 프레임 열 = data-state.
html_audit.py 가 이 표와 HTML을 대조한다 (component.manifest, state.frames). Figma 생성 시에는 figma_parity.py 가 같은 표로 대조하고, figma-builder 화면 STAGE는 이 표의 "구성" 열만 보고 인스턴스를 배치한다.
-->

status: draft
confirmed_at:

# Screens

구성은 위→아래 순서. 원문자 번호는 최종 미리보기 default 폰 프레임의 라벨과 같다 (화면당 최대 5개). **구성 열의 컴포넌트명은 HTML `data-component` 값과 1:1로 정확히 같아야 한다**(규칙 미리보기의 컴포넌트 견본 이름, Figma 생성 시 02 Components 페이지 이름과도 같다). 상태 프레임 열에는 **필수 7종(default·empty·loading·error·long-title·many-items·text-120)을 모든 행에 전부 적는다.** FormField가 있는 폼 화면은 `keyboard`, 웹 예외 화면은 `guest-name`을 더한다(html_audit `state.frames`가 이 열의 추가 상태까지 요구한다).

| 순번 | 화면 | slug | 구성 (위→아래) | 상태 프레임 |
|---|---|---|---|---|
| 1 | 홈 | home | ① AppBar(제목) · ② Card×n · ③ BottomCTA(첫 액션) · ④ TabBar | default·empty·loading·error·long-title·many-items·text-120 |
| 2 | <폼 화면> | <slug> | ① AppBar(제목) · ② FormField · ③ BottomCTA(primary 액션) | default·empty·loading·error·long-title·many-items·text-120·keyboard |
| 3 | <웹 예외 화면> | <slug> | ① AppBar(제목) · ② FormField · ③ BottomCTA(primary 액션) | default·empty·loading·error·long-title·many-items·text-120·keyboard·guest-name |

## 사용자 수정 이력

최종 미리보기 탭에서 들어온 remove / swap 을 그대로 적는다. 출처는 `feedback/screen-<slug>`.

| 화면 | 변경 | 원문 | 회차 |
|---|---|---|---|
