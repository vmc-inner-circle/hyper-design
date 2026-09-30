// 피드백 해석 — Excalidraw 요소 목록 → feedback.schema.json의 items, canvas-state의 moved·components.
// 순수 함수만 둔다 (DOM·Excalidraw 없음). 화면 안 요소 판별은 주입받은 elementAt(screen, device, x, y)로 한다.
import { frameKey, parse } from "./ids.js";

const MOVE_PX = 2, SCALE_EPS = 0.02;  // 이만큼 넘게 바뀌어야 옮김·크기 변경으로 본다
// 사용자가 그릴 수 있는 것 중 feedback.schema.json이 받는 유형 (frame 등 단축키로 생기는 것은 뺀다)
const DRAWN = new Set(["text", "arrow", "line", "rectangle", "ellipse", "diamond", "freedraw", "image"]);

const framesOf = (all) => Object.fromEntries(all.filter((e) => e.customData?.embed && !e.isDeleted)
  .map((e) => [frameKey(e.customData.screen, e.customData.device), e]));

// 캔버스 좌표 → 대상 { screen, device, x, y, dataId | near }. 기기 칸 밖이면 null
export function hitAt(px, py, all, elementAt) {
  const fr = all.find((e) => !e.isDeleted && e.customData?.embed && px >= e.x && px <= e.x + e.width && py >= e.y && py <= e.y + e.height);
  if (!fr) return null;
  const cd = fr.customData;
  const x = Math.round((px - fr.x) * cd.w / fr.width), y = Math.round((py - fr.y) * cd.h / fr.height);
  return { screen: cd.screen, device: cd.device, x, y, ...elementAt(cd.screen, cd.device, x, y) };
}

const labelOf = (el, all) => el.type === "text" ? el.text
  : all.find((t) => t.type === "text" && t.containerId === el.id && !t.isDeleted)?.text || "";

// AI가 만든 요소를 가리킬 때: 컴포넌트 → 그 data-id, 피드백 상자 → panel, 그 밖 → 좌표로 판별
function targetOf(el, px, py, all, elementAt) {
  const cd = el.customData, { kind } = parse(el.id);
  if (kind === "component") return { screen: cd.screen, device: cd.device, dataId: cd.component, text: cd.text };
  if (kind === "panel") return { screen: cd.screen, panel: true };
  return hitAt(px, py, all, elementAt) || (cd.screen && cd.device ? { screen: cd.screen, device: cd.device } : null);
}

// 화살표·선의 한쪽 끝: 붙은 요소가 있으면 그것, 없으면 끝점 좌표로
function endpointOf(el, which, all, elementAt) {
  const b = which === "start" ? el.startBinding : el.endBinding;
  const target = b && all.find((e) => e.id === b.elementId && !e.isDeleted);
  const p = which === "start" ? el.points[0] : el.points[el.points.length - 1];
  const px = el.x + p[0], py = el.y + p[1];
  if (target && !target.customData?.generated) return { userElement: target.id, text: labelOf(target, all) };
  if (target) return targetOf(target, px, py, all, elementAt);
  return hitAt(px, py, all, elementAt);
}

/**
 * @param all        Excalidraw 요소 전체 (지운 것 포함 — 컴포넌트 remove 판별에 필요)
 * @param elementAt  (screen, device, x, y) → { dataId, text } | { near } | {}
 * @returns { mine: 사용자가 그린 요소(복원용), items: feedback.json items }
 */
export function interpret(all, elementAt) {
  const mine = all.filter((e) => !e.isDeleted && !e.customData?.generated);
  const byId = Object.fromEntries(all.map((e) => [e.id, e]));
  const items = mine.flatMap((e) => {
    if (e.type === "text" && e.containerId) {
      // 사용자 도형의 라벨은 도형 쪽에서 읽는다. AI가 만든 피드백 상자에 적은 글은 그 화면에 대한 comment
      const box = byId[e.containerId];
      if (!box?.customData?.generated) return [];
      return [{ id: e.id, type: "comment", text: e.text, color: e.strokeColor, on: targetOf(box, box.x, box.y, all, elementAt) }];
    }
    if (!DRAWN.has(e.type)) return [];
    const it = { id: e.id, type: e.type, color: e.strokeColor };
    const text = labelOf(e, all); if (text) it.text = text;
    if (e.type === "arrow" || e.type === "line") { it.from = endpointOf(e, "start", all, elementAt); it.to = endpointOf(e, "end", all, elementAt); }
    else it.on = hitAt(e.x + e.width / 2, e.y + e.height / 2, all, elementAt);
    return [it];
  });

  // 컴포넌트를 옮기거나 키우거나 지운 것 (원래 자리·크기 rel0·w0·h0와 비교)
  const frames = framesOf(all);
  const deltaOf = (e) => { const f = frames[frameKey(e.customData.screen, e.customData.device)];
    return f ? [Math.round(e.x - f.x - e.customData.rel0[0]), Math.round(e.y - f.y - e.customData.rel0[1])] : [0, 0]; };
  const changed = (e) => { const [dx, dy] = deltaOf(e);
    return Math.abs(dx) > MOVE_PX || Math.abs(dy) > MOVE_PX || Math.abs(e.width / e.customData.w0 - 1) > SCALE_EPS || Math.abs(e.height / e.customData.h0 - 1) > SCALE_EPS; };
  // 요소가 영역의 이동·배율을 그대로 따라갔는가: 영역 기준 상대 위치 × 영역 배율 = 지금 위치, 크기 배율도 같음
  const followed = (e, p) => {
    const cd = e.customData, pd = p.customData, [pdx, pdy] = deltaOf(p), [dx, dy] = deltaOf(e);
    const psx = p.width / pd.w0, psy = p.height / pd.h0;
    const ex = pd.rel0[0] + pdx + (cd.rel0[0] - pd.rel0[0]) * psx, ey = pd.rel0[1] + pdy + (cd.rel0[1] - pd.rel0[1]) * psy;
    return Math.abs(cd.rel0[0] + dx - ex) <= MOVE_PX * 2 && Math.abs(cd.rel0[1] + dy - ey) <= MOVE_PX * 2
      && Math.abs(e.width / cd.w0 - psx) <= SCALE_EPS && Math.abs(e.height / cd.h0 - psy) <= SCALE_EPS;
  };
  all.filter((e) => e.customData?.component).forEach((e) => {
    const cd = e.customData, on = { screen: cd.screen, device: cd.device, dataId: cd.component, text: cd.text };
    const parent = cd.parent && byId[cd.parent];
    if (e.isDeleted) { if (!parent?.isDeleted) items.push({ id: e.id, type: "remove", on }); return; }  // 영역째 지웠으면 영역만
    const fr = frames[frameKey(cd.screen, cd.device)]; if (!fr) return;
    const [dx, dy] = deltaOf(e);
    // 영역을 옮기거나 크기를 바꿨고 요소가 그만큼만 따라갔으면 그 결과일 뿐이다 — 영역 한 건만 남긴다 (따로 움직인 요소는 기록)
    if (parent && !parent.isDeleted && changed(parent) && followed(e, parent)) return;
    const sx = +(e.width / cd.w0).toFixed(2), sy = +(e.height / cd.h0).toFixed(2);
    if (Math.abs(dx) > MOVE_PX || Math.abs(dy) > MOVE_PX)
      items.push({ id: e.id, type: "move", dx, dy, on, to: hitAt(e.x + e.width / 2, e.y + e.height / 2, all, elementAt) });
    if (Math.abs(sx - 1) > SCALE_EPS || Math.abs(sy - 1) > SCALE_EPS) items.push({ id: e.id, type: "resize", scale: [sx, sy], on });
  });
  return { mine, items };
}

// canvas-state.components — 원래와 달라진 컴포넌트만 (키는 컴포넌트 요소 id)
export function componentsOf(all) {
  const frames = framesOf(all), out = {};
  all.filter((e) => e.customData?.component).forEach((e) => {
    const cd = e.customData, fr = frames[frameKey(cd.screen, cd.device)]; if (!fr) return;
    const rel = [Math.round(e.x - fr.x), Math.round(e.y - fr.y)];
    const changed = e.isDeleted || Math.abs(rel[0] - cd.rel0[0]) > MOVE_PX || Math.abs(rel[1] - cd.rel0[1]) > MOVE_PX
      || Math.abs(e.width - cd.w0) > 1 || Math.abs(e.height - cd.h0) > 1;
    if (changed) out[e.id] = { rel, w: Math.round(e.width), h: Math.round(e.height), ...(e.isDeleted ? { deleted: true } : {}) };
  });
  return out;
}

// canvas-state.moved — 화면 그룹 이동량 (그룹의 첫 칸 기준)
export function movedOf(all) {
  const out = {};
  all.filter((e) => e.customData?.embed && !e.isDeleted).forEach((e) => {
    const d = [Math.round(e.x - e.customData.base[0]), Math.round(e.y - e.customData.base[1])];
    if (!(e.customData.screen in out) && (d[0] || d[1])) out[e.customData.screen] = d;
  });
  return out;
}

// 저장이 필요한 변화가 있는지 비교할 키 (사용자 요소 버전 + 화면 이동 + 컴포넌트 상태)
export const changeKey = (all) => all.filter((e) => !e.isDeleted && !e.customData?.generated).map((e) => e.id + ":" + e.version).join("|")
  + JSON.stringify(movedOf(all)) + JSON.stringify(componentsOf(all));
