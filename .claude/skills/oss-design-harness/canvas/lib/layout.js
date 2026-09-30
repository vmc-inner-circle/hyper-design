// 배치 — board.json + 읽은 컴포넌트 + 복원 상태 → Excalidraw 요소 목록.
// 한 화면 = 그룹 하나: 기기 칸들(가로로 나란히) + 칸 제목 + 컴포넌트 이미지 + 인터랙션 표시(빨간 테두리) + 피드백 상자
import { convertToExcalidrawElements } from "https://esm.sh/@excalidraw/excalidraw@0.18.1?external=react,react-dom";
import { make, parse } from "./ids.js";

export const FONT = 5;  // Excalifont — 보드 전체 글꼴 하나
const GAP_X = 200, GAP_Y = 200, FRAME_GAP = 60, PANEL_GAP = 28, PANEL_H = 200, MARK_PAD = 4;
export const COLORS = { panel: "#fff9db", panelStroke: "#f2d56b", mark: "#e03131",
  frameStroke: "#ced4da", arrow: "#495057", backArrow: "#adb5bd", text: "#1f1f1f", rowText: "#495057",
  muted: "#868e96", live: "#1864ab", wide: "#d9480f", chip: "#7048e8" };

// 두 사각형 사이 화살표 끝점: 가로로 더 떨어져 있거나 같은 줄이면 옆면끼리, 아니면 위아래 면끼리
function endpoints(S, B, sameRow) {
  const side = sameRow || Math.abs((B.x + B.w / 2) - (S.x + S.w / 2)) > Math.abs((B.y + B.h / 2) - (S.y + S.h / 2));
  const right = B.x >= S.x + S.w, down = B.y >= S.y + S.h;
  return side
    ? [[right ? S.x + S.w : S.x, S.y + S.h / 2], [right ? B.x : B.x + B.w, B.y + B.h / 2]]
    : [[S.x + S.w / 2, down ? S.y + S.h : S.y], [B.x + B.w / 2, down ? B.y : B.y + B.h]];
}

// 줄마다 흐름 순서와 되돌아가는 관계를 정한다.
// ① 되돌아감: data-back(뒤로·취소) 링크, 또는 흐름을 따라가다 이미 지나온 화면(조상)으로 가는 관계
// ② 순서: 나머지 앞으로 가는 관계를 위상 정렬 — 앞으로 가는 화살표가 모두 왼쪽 → 오른쪽을 향한다. 동률은 board.json order 순
function flowOrder(screens, rels) {
  const rowOf = Object.fromEntries(screens.map((s) => [s.id, s.row]));
  const byOrder = [...screens].sort((a, b) => a.row - b.row || a.order - b.order), ord = Object.fromEntries(byOrder.map((s, i) => [s.id, i]));
  const same = rels.filter((r) => rowOf[r.from] === rowOf[r.to] && r.from !== r.to);
  const back = new Set(same.filter((r) => r.back).map((r) => `${r.from}>${r.to}`));
  const onStack = new Set(), done = new Set();
  const dfs = (id) => {
    onStack.add(id); done.add(id);
    same.filter((r) => r.from === id && !back.has(`${r.from}>${r.to}`)).sort((a, b) => ord[a.to] - ord[b.to]).forEach((r) => {
      if (onStack.has(r.to)) back.add(`${r.from}>${r.to}`); else if (!done.has(r.to)) dfs(r.to);
    });
    onStack.delete(id);
  };
  byOrder.forEach((s) => { if (!done.has(s.id)) dfs(s.id); });
  const fwd = same.filter((r) => !back.has(`${r.from}>${r.to}`)), indeg = Object.fromEntries(screens.map((s) => [s.id, 0]));
  fwd.forEach((r) => indeg[r.to]++);
  const seq = {}, ready = byOrder.filter((s) => !indeg[s.id]).map((s) => s.id);
  let n = 0;
  while (ready.length) {
    ready.sort((a, b) => ord[a] - ord[b]);
    const id = ready.shift(); seq[id] = n++;
    fwd.filter((r) => r.from === id).forEach((r) => { if (--indeg[r.to] === 0) ready.push(r.to); });
  }
  byOrder.forEach((s) => { if (!(s.id in seq)) seq[s.id] = n++; });
  return { seq, back };
}

/**
 * @param board       board.json 원본 (rows·arrows)
 * @param screens     loadBoard + discover를 거친 화면 목록 (discovered 포함)
 * @param frames      기기 칸 목록 (capture가 content 기기의 h를 채운 뒤)
 * @param devices     devices.json
 * @param links       discover가 모은 링크 관계
 * @param components  { frameKey: [컴포넌트] } — capture.measureFrame 결과
 * @param state       canvas-state.json (moved: 화면 그룹 이동량, components: 옮긴 컴포넌트)
 * @param view        flows가 있을 때 보기: all(모바일 구간 + PC 구간) · mobile · pc
 */
export function buildScene({ board, screens, frames, devices, links, components, state, view = "all" }) {
  const moved = state?.moved || {}, compState = state?.components || {};
  const rowTitle = Object.fromEntries((board.rows || []).map((r) => [r.row, r.title]));
  const compRect = (fr, fx, gy, c) => {  // 사용자가 옮긴 위치·크기가 있으면 그것으로
    const st = compState[make.component(fr.screen, fr.device, c.key)] || {};
    const [rx, ry] = st.rel || [c.x, c.y];
    return { x: fx + rx, y: gy + ry, w: st.w || c.w, h: st.h || c.h };
  };

  // 화면 사이 관계: ① 화면 안 링크(링크가 든 컴포넌트 → 대상 화면) ② board.json arrows(링크로 드러나지 않는 흐름).
  // 같은 쌍이면 하나로 합치고 라벨은 board.json 것을 쓴다
  const boardLabel = Object.fromEntries((board.arrows || []).map((a) => [`${a.from}>${a.to}`, a.label]));
  const rels = [], seenRel = new Set();
  links.forEach((l) => { const k = `${l.from}>${l.to}`; if (!seenRel.has(k)) { seenRel.add(k); rels.push({ ...l, label: boardLabel[k] ?? l.text }); } });
  (board.arrows || []).forEach((a) => { const k = `${a.from}>${a.to}`; if (!seenRel.has(k)) { seenRel.add(k); rels.push(a); } });
  const { seq, back: backRels } = flowOrder(screens, rels);  // seq: 화면 id → 줄 안 순서, backRels: 되돌아가는 관계

  const skel = [], first = {}, base = {}, meta = {};
  const extraGoto = {}, liveOf = {};  // 누르면 이동하는 요소(지도 상자·참조 카드·보라 글자) → 대상 / 완성본 요소 → 시작 화면 파일
  const byId = Object.fromEntries(screens.map((s) => [s.id, s]));

  // 화면 하나 놓기 — 기기 칸(only가 있으면 그 기기만) + 칸 제목 + 목적 한 줄 + 컴포넌트 + 피드백 상자(panel). 반환: 오른쪽 끝·높이
  const placeScreen = (s, x, y, row, { prefix = "", only, panel = true, purpose = false } = {}) => {
    const [dx, dy] = moved[s.id] || [0, 0];
    const sf = frames.filter((f) => f.screen === s.id && (!only || only.includes(f.device)));
    let fx = x + dx, maxH = 0;
    const gy = y + dy;
    sf.forEach((fr, i) => {
      base[fr.key] = [fx - dx, gy - dy];
      if (i === 0 && !first[s.id]) first[s.id] = { x: fx, y: gy, w: fr.w, h: fr.h, row, key: fr.key, frame: fr };
      const many = s.devices.length > 1;
      const label = (many ? `${s.title || s.id} · ${devices[fr.device].label}` : (s.title || s.id)) + (s.discovered ? " (링크에서 발견)" : "");
      const sub = purpose && i === 0 && s.purpose;
      skel.push({ type: "rectangle", id: make.frame(s.id, fr.device), x: fx, y: gy, width: fr.w, height: fr.h });
      skel.push({ type: "text", id: make.frameTitle(s.id, fr.device), x: fx, y: gy - (sub ? 76 : 40), text: `${prefix ? prefix + " " : ""}${label}  `,
        fontSize: sub ? 26 : 22, fontFamily: FONT, strokeColor: COLORS.text });
      if (sub) skel.push({ type: "text", id: `purpose:${s.id}`, x: fx, y: gy - 38, text: `${s.purpose}  `, fontSize: 18, fontFamily: FONT, strokeColor: COLORS.muted });
      (components[fr.key] || []).forEach((c) => {
        const r = compRect(fr, fx, gy, c), id = make.component(s.id, fr.device, c.key);
        meta[id] = { c, fr };
        skel.push({ type: "rectangle", id, x: r.x, y: r.y, width: r.w, height: r.h });
      });
      maxH = Math.max(maxH, fr.h);
      fx += fr.w + FRAME_GAP;
    });
    const groupW = fx - FRAME_GAP - (x + dx);
    if (!panel) return { right: fx - dx - FRAME_GAP, h: maxH };
    // 화면 바로 아래: 피드백 상자 (모든 화면 같은 자리). 상자 폭은 기기 칸 전체 폭
    let ny = gy + maxH + PANEL_GAP;
    skel.push({ type: "text", id: make.panelTitle(s.id), x: x + dx, y: ny, text: "피드백 (더블클릭해서 적기)", fontSize: 18, fontFamily: FONT, strokeColor: COLORS.text });
    skel.push({ type: "rectangle", id: make.panel(s.id), x: x + dx, y: ny + 32, width: Math.max(groupW, 390), height: PANEL_H,
      backgroundColor: COLORS.panel, fillStyle: "solid", strokeColor: COLORS.panelStroke, strokeWidth: 1, roughness: 0 });
    ny += 32 + PANEL_H;
    return { right: fx - dx - FRAME_GAP, h: ny - gy };
  };
  const title = (id, x, y, text, sub, color = COLORS.text) => {
    skel.push({ type: "text", id, x, y, text: `${text}  `, fontSize: 36, fontFamily: FONT, strokeColor: color });  // 끝 공백: Excalifont 폭 계산이 마지막 글자를 자르지 않게
    if (sub) skel.push({ type: "text", id: id + ":sub", x, y: y + 52, text: `${sub}  `, fontSize: 20, fontFamily: FONT, strokeColor: COLORS.muted });
  };
  const live = (id, x, y, s, fr, heading) => {  // 완성본: 실제로 눌리는 화면 (링크를 따라 다음 화면으로 넘어감)
    skel.push({ type: "text", id: `${id}:t`, x, y: y - 76, text: heading, fontSize: 26, fontFamily: FONT, strokeColor: COLORS.live });
    skel.push({ type: "text", id: `${id}:h`, x, y: y - 38, text: "클릭해서 켠 뒤 화면 안 버튼을 눌러 보세요", fontSize: 18, fontFamily: FONT, strokeColor: COLORS.muted });
    const h = Math.max(fr.h, devices[fr.device].height.value);
    skel.push({ type: "rectangle", id, x, y, width: fr.w, height: h });
    liveOf[id] = s.file;
    return h;
  };

  const flows = (board.flows || []).filter((f) => f.steps?.some((sid) => byId[sid]));
  const lanePos = {};  // `${흐름 순번}:${단계}` → { sid, full, rect } — 모바일 흐름 줄의 칸 (옆 화살표용)
  const home = {}, circ = (n) => "①②③④⑤⑥⑦⑧⑨⑩"[n] || `${n + 1}.`;
  const tag = (sid) => home[sid] ? `흐름${flows[home[sid].fi].id} ${circ(home[sid].si)}` : (byId[sid]?.title || sid);
  let y = 0;

  if (flows.length) {
    // ---------- 흐름 배치: 흐름 지도 + 모바일 구간 | 넓은 화면 구간(PC·태블릿) + 완성본 ----------
    // 좌표는 보기(view)와 상관없이 같다 — 보기를 바꾸면 그 구간 요소만 빠진다 (사용자가 그린 표시가 어긋나지 않게)
    flows.forEach((f, fi) => f.steps.forEach((sid, si) => { if (byId[sid]) home[sid] ??= { fi, si }; }));
    const loose = screens.filter((s) => !(s.id in home));
    const lanes = [...flows, ...(loose.length ? [{ id: "·", title: "어느 흐름에도 없는 화면", steps: loose.map((s) => s.id), loose: true }] : [])];
    const wide = (s) => s.devices.filter((d) => d !== "mobile");
    const narrow = (s) => (s.devices.includes("mobile") ? ["mobile"] : s.devices.slice(0, 1));
    const hasWide = screens.some((s) => wide(s).length && s.devices.includes("mobile"));
    const showM = view !== "pc", showW = view !== "mobile" && hasWide;
    const COL = devices.mobile.width + GAP_X, LIVE_X = Math.max(...lanes.map((f) => f.steps.length)) * COL + 160, WIDE_X = LIVE_X + devices.mobile.width + 520;
    const wideLabel = [...new Set(screens.flatMap(wide))].map((d) => devices[d].label).join("·");

    // 흐름 지도 — 칸이 아래 모바일 흐름 줄과 같은 세로줄. 상자를 누르면 그 화면으로
    title("row:map", 0, y, "흐름 지도", "상자를 누르면 그 화면으로 이동 · 아래 흐름 줄과 같은 칸");
    if (showM) title("row:livehead", LIVE_X, y, "완성본", "직접 눌러 보는 프로토타입", COLORS.live);
    y += 150;
    const BH = 96;
    flows.forEach((f, fi) => {
      skel.push({ type: "text", id: `maplane:${fi}`, x: -760, y: y + 14, text: `흐름 ${f.id}\n${f.title}  `, fontSize: 24, fontFamily: FONT, strokeColor: COLORS.text });
      f.steps.forEach((sid, si) => {
        const s = byId[sid]; if (!s) return;
        const id = `map:${fi}:${si}`, own = home[sid].fi === fi && home[sid].si === si;
        const plus = wide(s).length ? ` (+${wide(s).map((d) => devices[d].label).join("·")})` : "";
        skel.push({ type: "rectangle", id, x: si * COL, y, width: devices.mobile.width, height: BH, backgroundColor: own ? "#ffffff" : "#f1f3f5", fillStyle: "solid",
          strokeColor: own ? COLORS.arrow : COLORS.backArrow, strokeStyle: own ? "solid" : "dashed", roughness: 0,
          label: { text: `${circ(si)} ${s.title || sid}${plus}${own ? "" : `\n(${tag(sid)})`}`, fontSize: 22, fontFamily: FONT, strokeColor: own ? COLORS.text : COLORS.muted } });
        extraGoto[id] = sid;
        if (si > 0) skel.push({ type: "arrow", id: `maparrow:${fi}:${si}`, x: si * COL - GAP_X + 10, y: y + BH / 2, width: GAP_X - 20, height: 0,
          strokeColor: COLORS.arrow, strokeWidth: 2, roughness: 0, start: { id: `map:${fi}:${si - 1}` }, end: { id } });
      });
      if (showM) {
        const lid = `maplive:${fi}`;
        skel.push({ type: "rectangle", id: lid, x: LIVE_X, y, width: devices.mobile.width, height: BH, backgroundColor: "#e7f5ff", fillStyle: "solid", strokeColor: COLORS.live, roughness: 0,
          label: { text: "▶ 완성본에서 눌러보기", fontSize: 22, fontFamily: FONT, strokeColor: COLORS.live } });
        extraGoto[lid] = `live:${fi}`;
      }
      y += BH + 36;
    });
    y += 260;

    // 구간 제목 띠
    if (showM) {
      skel.push({ type: "rectangle", id: "zone:mobile", x: -40, y: y - 20, width: LIVE_X + devices.mobile.width + 80, height: 110, backgroundColor: "#f1f3f5", fillStyle: "solid", strokeColor: "transparent", roughness: 0 });
      skel.push({ type: "text", id: "zonet:mobile", x: 0, y, text: `${devices.mobile.label} 구간`, fontSize: 48, fontFamily: FONT, strokeColor: COLORS.text });
    }
    if (showW) {
      skel.push({ type: "rectangle", id: "zone:wide", x: WIDE_X - 40, y: y - 20, width: 2 * (devices.desktop.width + GAP_X) + 80, height: 110, backgroundColor: "#fff4e6", fillStyle: "solid", strokeColor: "transparent", roughness: 0 });
      skel.push({ type: "text", id: "zonet:wide", x: WIDE_X, y, text: `${wideLabel} 구간  (${wideLabel}를 쓰는 화면만 · 같은 높이 = 같은 흐름)`, fontSize: 48, fontFamily: FONT, strokeColor: COLORS.wide });
    }
    y += 200;

    lanes.forEach((f, fi) => {
      title(make.row(fi), showM ? 0 : WIDE_X, y, f.loose ? f.title : `흐름 ${f.id}   ${f.title}`, f.refs);
      y += 190;
      let laneH = 0;
      if (showM) {
        f.steps.forEach((sid, si) => {
          const s = byId[sid]; if (!s) return;
          const x = si * COL, own = f.loose || (home[sid].fi === fi && home[sid].si === si);
          if (own) {
            const r = placeScreen(s, x, y, fi, { prefix: f.loose ? "" : circ(si), only: narrow(s), purpose: true });
            lanePos[`${fi}:${si}`] = { sid, full: true, rect: { ...first[sid], id: make.frame(sid, first[sid].frame.device) } };
            laneH = Math.max(laneH, r.h);
          } else {  // 앞 흐름에 이미 나온 화면: 참조 카드 (누르면 그 화면으로)
            const id = `ref:${fi}:${si}`, w = devices.mobile.width, h = 240;
            skel.push({ type: "rectangle", id, x, y, width: w, height: h, backgroundColor: "#f1f3f5", fillStyle: "solid", strokeColor: COLORS.backArrow, strokeStyle: "dashed", roughness: 0,
              label: { text: `${circ(si)} ${s.title || sid}\n\n${tag(sid)}에 있는 화면\n(누르면 이동)`, fontSize: 20, fontFamily: FONT, strokeColor: COLORS.rowText } });
            extraGoto[id] = sid;
            lanePos[`${fi}:${si}`] = { sid, full: false, rect: { x, y, w, h, id } };
            laneH = Math.max(laneH, h);
          }
        });
        const s0 = !f.loose && byId[f.steps[0]], fr0 = s0 && frames.find((x) => x.screen === s0.id && narrow(s0).includes(x.device));
        if (fr0) laneH = Math.max(laneH, live(`live:${fi}`, LIVE_X, y, s0, fr0, `▶ 흐름 ${f.id} 완성본`));
      }
      if (showW) {  // 넓은 화면 구간: 이 흐름에서 처음 나온 화면 중 PC·태블릿을 쓰는 것. 모바일 구간이 빠진 보기에선 여기에 피드백 상자
        let px = WIDE_X, firstWide = null;
        f.steps.forEach((sid, si) => {
          const s = byId[sid];
          if (!s || !wide(s).length || (!f.loose && !(home[sid].fi === fi && home[sid].si === si))) return;
          if (!s.devices.includes("mobile") && showM) return;  // 넓은 화면 전용은 모바일 구간 줄에 이미 있음
          const r = placeScreen(s, px, y, fi, { prefix: f.loose ? "" : circ(si), only: wide(s), panel: !showM, purpose: !showM });
          firstWide ??= s;
          laneH = Math.max(laneH, r.h); px = r.right + GAP_X;
        });
        const frw = firstWide && frames.find((x) => x.screen === firstWide.id && x.device !== "mobile");
        if (frw && !f.loose) laneH = Math.max(laneH, live(`livewide:${fi}`, px + 160, y, firstWide, frw, `▶ 흐름 ${f.id} 완성본 (${devices[frw.device].label})`));
      }
      y += laneH + GAP_Y;
    });
  } else {
    // ---------- 줄 배치 (flows 없음): 역할별 줄 + 링크 흐름 순서 ----------
    [...new Set(screens.map((s) => s.row))].sort((a, b) => a - b).forEach((row) => {
      if (rowTitle[row]) { skel.push({ type: "text", id: make.row(row), x: 0, y, text: rowTitle[row], fontSize: 32, fontFamily: FONT, strokeColor: COLORS.rowText }); y += 90; }
      let x = 0, rowH = 0;
      screens.filter((s) => s.row === row).sort((a, b) => seq[a.id] - seq[b.id]).forEach((s) => {
        const r = placeScreen(s, x, y, row);
        rowH = Math.max(rowH, r.h); x = r.right + GAP_X;
      });
      y += rowH + GAP_Y;
    });
  }

  // 버튼·화살표에는 goto(이동할 화면)만 달아 두고, 선택했을 때 "→ 이동" 버튼을 띄운다 (↗ 아이콘을 늘리지 않으려고)
  const gotoOf = {}, relOf = {}, markOf = {};  // markOf: 빨간 테두리 id → 감싼 컴포넌트 id
  // 인터랙션 표시: 다른 화면으로 넘어가는 버튼마다 빨간 테두리 + goto (링크 하나하나 — 화살표는 화면 쌍마다 하나로 합쳐도)
  // 버튼은 각 화면의 첫 번째로 놓인 기기 칸 기준. 뒤로 가기는 표시하지 않는다
  links.forEach((l) => {
    const A = first[l.from]; if (!A || !byId[l.to] || l.back || backRels.has(`${l.from}>${l.to}`)) return;
    const c = l.dataId && (components[A.key] || []).find((x) => x.dataId === l.dataId); if (!c) return;
    const compId = make.component(l.from, A.frame.device, c.key), markId = make.mark(l.from, A.frame.device, c.key);
    gotoOf[compId] ??= l.to;
    if (markOf[markId]) return;
    markOf[markId] = compId;
    const r = compRect(A.frame, A.x, A.y, c);
    skel.push({ type: "rectangle", id: markId, x: r.x - MARK_PAD, y: r.y - MARK_PAD, width: r.w + MARK_PAD * 2, height: r.h + MARK_PAD * 2,
      strokeColor: COLORS.mark, strokeWidth: 2, backgroundColor: "transparent", roughness: 0, locked: true });
  });

  if (flows.length) {
    // 흐름 배치의 화살표: 같은 흐름 줄의 바로 옆 칸으로만. 그 밖의 링크는 버튼 옆 보라 글자(→ 흐름n ②)로 — 누르면 그 화면으로
    const nextOf = new Set();
    Object.entries(lanePos).forEach(([k, p]) => {
      const [fi, si] = k.split(":").map(Number), nx = lanePos[`${fi}:${si + 1}`]; if (!nx) return;
      if (p.full) nextOf.add(`${p.sid}>${nx.sid}`);
      const l = links.find((x) => x.from === p.sid && x.to === nx.sid && !x.back), A = first[p.sid];
      const c = p.full && l?.dataId && (components[A.key] || []).find((x) => x.dataId === l.dataId);
      const S = c ? { ...compRect(A.frame, A.x, A.y, c), id: make.component(p.sid, A.frame.device, c.key) } : p.rect;
      const [p1, p2] = endpoints(S, nx.rect, true), arrowId = `rel:${fi}/${p.sid}>${nx.sid}`, label = boardLabel[`${p.sid}>${nx.sid}`] ?? l?.text;
      relOf[arrowId] = { from: p.sid, to: nx.sid, back: false };
      gotoOf[arrowId] = nx.sid;
      skel.push({ type: "arrow", id: arrowId, x: p1[0], y: p1[1], width: p2[0] - p1[0], height: p2[1] - p1[1], strokeColor: COLORS.arrow, strokeWidth: 2, roughness: 0,
        start: { id: S.id }, end: { id: nx.rect.id }, label: label ? { text: label, fontSize: 16, fontFamily: FONT } : undefined });
    });
    // 같은 화면에서 같은 곳으로 가는 버튼이 여럿이면(목록의 행마다 같은 링크 등) 보라 글자는 가장 위 버튼 옆에 하나만
    const chipOf = {};
    links.forEach((l) => {
      const A = first[l.from], pair = `${l.from}>${l.to}`; if (!A || !byId[l.to] || l.back || backRels.has(pair) || nextOf.has(pair)) return;
      const c = l.dataId && (components[A.key] || []).find((x) => x.dataId === l.dataId); if (!c) return;
      const r = compRect(A.frame, A.x, A.y, c);
      if (!chipOf[pair] || r.y < chipOf[pair].r.y) chipOf[pair] = { l, A, c, r };
    });
    Object.values(chipOf).forEach(({ l, A, c, r }) => {
      const id = `chip:${l.from}:${c.key}:${l.to}`;
      skel.push({ type: "text", id, x: A.x + A.w + 14, y: r.y + r.h / 2 - 14, text: `→ ${tag(l.to)}`, fontSize: 22, fontFamily: FONT, strokeColor: COLORS.chip });
      extraGoto[id] = l.to;
    });
  } else {
    // 줄 배치의 관계 화살표. 흐름을 거슬러 가는 것(뒤로·취소 등)은 기본으로 숨기고, 화면을 고르면 보인다(canvas.html)
    rels.forEach((l) => {
      const A = first[l.from], B = first[l.to]; if (!A || !B) return;
      const c = l.dataId && (components[A.key] || []).find((x) => x.dataId === l.dataId);
      const S = c ? { ...compRect(A.frame, A.x, A.y, c), id: make.component(l.from, A.frame.device, c.key) } : { ...A, id: make.frame(l.from, A.frame.device) };
      const [p1, p2] = endpoints(S, B, A.row === B.row);
      const back = !!l.back || backRels.has(`${l.from}>${l.to}`), arrowId = `rel:${l.from}>${l.to}`;
      relOf[arrowId] = { from: l.from, to: l.to, back };
      gotoOf[arrowId] = l.to;
      skel.push({ type: "arrow", id: arrowId, x: p1[0], y: p1[1], width: p2[0] - p1[0], height: p2[1] - p1[1],
        strokeColor: back ? COLORS.backArrow : COLORS.arrow, strokeStyle: back ? "dashed" : "solid", strokeWidth: 2, roughness: 0,
        opacity: back ? 0 : 100, locked: back,
        start: { id: S.id }, end: { id: make.frame(l.to, B.frame.device) },
        label: l.label ? { text: l.label, fontSize: 16, fontFamily: FONT } : undefined });
    });
  }

  // customData: generated(AI가 만든 것) · screen · device, 칸은 embed·base, 컴포넌트는 component·rel0·w0·h0(원래 자리 — 옮김 판별 기준)
  const frameOf = Object.fromEntries(frames.map((f) => [f.key, f]));
  const hasKids = new Set(frames.flatMap((f) => (components[f.key] || []).filter((c) => c.parent).map((c) => `${f.key}:${c.parent}`)));
  return convertToExcalidrawElements(skel, { regenerateIds: false }).map((el) => {
    const { kind, screen, device } = parse(el.containerId || el.id);
    const out = { ...el, customData: { generated: true, screen, device }, groupIds: screen ? [make.group(screen)] : [] };
    const rel = relOf[el.containerId || el.id];
    if (rel) Object.assign(out, { customData: { generated: true, rel, goto: rel.to }, opacity: rel.back ? 0 : 100, locked: rel.back });
    const eg = extraGoto[el.containerId || el.id];
    if (eg) out.customData = { generated: true, goto: eg };
    if (el.containerId) return out;
    if (liveOf[el.id]) return Object.assign(out, { type: "embeddable", link: new URL(liveOf[el.id], location.href).href, backgroundColor: "transparent", roughness: 0,
      strokeColor: COLORS.live, strokeWidth: 2, customData: { generated: true, live: true } });
    if (kind === "frame") {
      const fr = frameOf[`${screen}@${device}`];
      Object.assign(out, { type: "embeddable", link: new URL(fr.file, location.href).href,
        backgroundColor: "transparent", roughness: 0, strokeColor: COLORS.frameStroke,
        customData: { generated: true, screen, device, embed: true, w: fr.w, h: fr.h, base: base[fr.key] } });
    } else if (kind === "mark") {
      out.customData = { generated: true, screen, device, markOf: markOf[el.id] };
    } else if (kind === "component") {
      const { c, fr } = meta[el.id];
      // 요소가 든 영역은 영역+요소를 한 묶음(cg)으로: 화면 클릭 → 더블클릭하면 영역 묶음 → 한 번 더 더블클릭하면 요소 하나
      const areaKey = c.parent || (hasKids.has(`${fr.key}:${c.key}`) ? c.key : null);
      if (areaKey) out.groupIds = [make.compGroup(screen, device, areaKey), make.group(screen)];
      Object.assign(out, { type: "image", fileId: c.fileId, status: "saved", scale: [1, 1], crop: null,
        strokeColor: "transparent", backgroundColor: "transparent", roughness: 0, isDeleted: !!compState[el.id]?.deleted,
        customData: { generated: true, screen, device, component: c.dataId, text: c.text, rel0: [c.x, c.y], w0: c.w, h0: c.h,
          ...(c.parent ? { parent: make.component(screen, device, c.parent) } : {}), ...(gotoOf[el.id] ? { goto: gotoOf[el.id] } : {}) } });
    }
    return out;
  });
}
