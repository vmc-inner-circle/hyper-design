// 캔버스 요소 id 규칙 — 배치(layout)·해석(feedback)·복원(canvas-state.components 키)이 모두 이 형식을 쓴다.
// id를 만들 땐 make, 읽을 땐 parse만 쓴다. 문자열을 직접 조립하거나 startsWith로 가르지 않는다.

export const frameKey = (screen, device) => `${screen}@${device}`;

export const make = {
  frame: (screen, device) => `screen:${frameKey(screen, device)}`,        // 기기 칸 (embeddable)
  frameTitle: (screen, device) => `title:${frameKey(screen, device)}`,    // 기기 칸 제목
  component: (screen, device, key) => `img:${frameKey(screen, device)}:${key}`,  // 컴포넌트 이미지 (key = data-id, 겹치면 id#2)
  file: (screen, device, key) => `f:${frameKey(screen, device)}:${key}`,  // 컴포넌트 이미지 파일
  panel: (screen) => `panel:${screen}`,            // 피드백 상자
  panelTitle: (screen) => `ptitle:${screen}`,
  mark: (screen, device, key) => `mark:${frameKey(screen, device)}:${key}`,     // 인터랙션 표시 (다른 화면으로 넘어가는 버튼의 빨간 테두리)
  row: (row) => `row:${row}`,                      // 줄 제목
  group: (screen) => `g:${screen}`,                // 화면 그룹
  compGroup: (screen, device, key) => `cg:${frameKey(screen, device)}:${key}`,  // 영역 + 그 안의 요소 묶음 (화면 그룹 안의 그룹)
};

const KIND = { screen: "frame", title: "frameTitle", img: "component", mark: "mark", panel: "panel", ptitle: "panelTitle", row: "row" };

// id → { kind, screen, device, key }. AI가 만든 요소가 아니면 kind: null
export function parse(id = "") {
  const [prefix, ...rest] = id.split(":");
  const kind = KIND[prefix] || null;
  if (!kind) return { kind: null };
  if (kind === "row") return { kind, row: Number(rest[0]) };
  if (["frame", "frameTitle", "component", "mark"].includes(kind)) {
    const [screen, device] = rest[0].split("@");
    return { kind, screen, device, key: rest.length > 1 ? rest.slice(1).join(":") : undefined };
  }
  return { kind, screen: rest.join(":") };
}
