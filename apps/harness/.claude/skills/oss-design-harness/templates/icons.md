<!--
4단계 산출물. 프로젝트의 design/icons.md로 복사해서 채운다.
아이콘 이름은 lucide 공식 이름(kebab-case)만. https://lucide.dev/icons
figma-builder는 이 표에 있는 아이콘만 Icon/<name> 컴포넌트로 만든다. 표에 없는 아이콘은 만들지 않는다.
-->

# Icons

- 세트: lucide-react
- 크기 규칙: 옆 텍스트 역할이 정함. caption·label → 16 / body → 20 / h3·앱바·탭바 → 24
- 선 두께: 16→1.5 / 20→1.75 / 24→2

## 허용 목록

의미 1개 = 아이콘 1개. 같은 행의 "쓰이는 곳"이 여러 화면이어도 아이콘은 하나다.

| 의미 | lucide 이름 | 크기 | 쓰이는 곳 | 라벨 동반 |
|---|---|---|---|---|
| 뒤로 | chevron-left | 24 | 앱바 | 아니오 (접근성 라벨) |
| 닫기 | x | 24 | 시트·다이얼로그 | 아니오 |
| 새로 만들기 | plus | 24 | 탭바 가운데 | 예 |
| 더보기 | ellipsis-vertical | 20 | 목록 행 | 아니오 |
| 삭제 | trash-2 | 20 | 시트 액션 | 예 |
| 공유 | share-2 | 20 | 앱바 액션 | 아니오 |
| 저장 | check | 20 | 하단 CTA | 예 |
| 검색 | search | 20 | 앱바·입력 | 아니오 |
| 설정 | settings | 24 | 탭바 | 예 |
| 홈 | house | 24 | 탭바 | 예 |
| 이미지 로드 실패 | image-off | 24 | 썸네일 실패 상태 | 아니오 |
| 빈 상태 | inbox | 48 | 빈 상태 (예외 크기, 장식) | 예 |
| 오류 | circle-alert | 20 | 에러 문구 옆 | 예 |
| 오프라인 | wifi-off | 16 | 오프라인 배너 | 예 |

## 제외 목록

비슷해서 헷갈리는 아이콘. 쓰지 않는다.

| 쓰지 않음 | 이유 |
|---|---|
| arrow-left | 뒤로는 chevron-left 하나만 |
| x-circle | 닫기는 x 하나만 |
| more-horizontal | 더보기는 ellipsis-vertical 하나만 |
