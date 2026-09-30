// 피드백 해석(lib/feedback.js) 테스트 — 브라우저 없이 실행: node --test .claude/skills/oss-design-harness/canvas/tests/feedback.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { interpret, componentsOf, movedOf } from "../lib/feedback.js";
import { make, parse } from "../lib/ids.js";

// 가짜 보드: detail 화면(모바일 칸 하나) + 컴포넌트 둘 + 피드백 상자 + 사용자 표시
const frame = { id: make.frame("detail", "mobile"), type: "embeddable", x: 1000, y: 0, width: 390, height: 844,
  customData: { generated: true, embed: true, screen: "detail", device: "mobile", w: 390, h: 844, base: [1000, 0] } };
const comp = (key, rel, extra = {}) => ({ id: make.component("detail", "mobile", key), type: "image", x: 1000 + rel[0], y: rel[1], width: 350, height: 48,
  customData: { generated: true, screen: "detail", device: "mobile", component: key, text: key, rel0: rel, w0: 350, h0: 48 }, ...extra });
const panel = { id: make.panel("detail"), type: "rectangle", x: 1000, y: 872, width: 390, height: 200, boundElements: [{ type: "text", id: "t-panel" }],  // 화면 아래
  customData: { generated: true, screen: "detail" } };

const scene = [
  frame,
  comp("item-date", [20, 160], { y: 104 }),                 // 위로 56 옮김
  comp("item-status", [20, 104], { isDeleted: true }),       // 지움
  comp("item-note", [20, 220], { width: 525 }),              // 가로 1.5배
  panel,
  { id: "t-panel", type: "text", text: "날짜는 덜 눈에 띄게", containerId: panel.id, strokeColor: "#1e1e1e", x: 1012, y: 884, width: 200, height: 20 },
  { id: "t-free", type: "text", text: "이거 확인", x: 1600, y: 900, width: 80, height: 20, strokeColor: "#e03131" },
  { id: "a-1", type: "arrow", x: 1600, y: 910, width: -400, height: -780, points: [[0, 0], [-400, -780]], strokeColor: "#1971c2",
    startBinding: { elementId: "t-free" }, endBinding: { elementId: make.component("detail", "mobile", "item-date") } },
  { id: "r-out", type: "rectangle", x: 5000, y: 5000, width: 100, height: 100, strokeColor: "#000" },  // 빈 캔버스
];
// 화면 안 좌표 → 요소: 위쪽 100px 안은 item-status, 그 아래는 빈 곳
const elementAt = (screen, device, x, y) => y < 130 ? { dataId: "item-status", text: "완료 표시" } : { near: { dataId: "item-date", distance: 8 } };

const { items, mine } = interpret(scene, elementAt);
const byType = (t) => items.filter((i) => i.type === t);

test("id 규칙: make ↔ parse", () => {
  assert.deepEqual(parse(make.component("home", "desktop", "summary-card#2")), { kind: "component", screen: "home", device: "desktop", key: "summary-card#2" });
  assert.deepEqual(parse(make.panel("home")), { kind: "panel", screen: "home" });
  assert.equal(parse("사용자가-그린-것").kind, null);
});

test("컴포넌트를 옮기면 move — 이동량과 옮긴 자리의 요소", () => {
  const [m] = byType("move");
  assert.equal(m.on.dataId, "item-date");
  assert.deepEqual([m.dx, m.dy], [0, -56]);
  assert.equal(m.to.dataId, "item-status");
});

test("컴포넌트를 지우면 remove, 크기를 바꾸면 resize", () => {
  assert.equal(byType("remove")[0].on.dataId, "item-status");
  assert.deepEqual(byType("resize")[0].scale, [1.5, 1]);
});

test("피드백 상자에 적은 글은 panel comment", () => {
  const [c] = byType("comment");
  assert.equal(c.text, "날짜는 덜 눈에 띄게");
  assert.deepEqual(c.on, { screen: "detail", panel: true });
});

test("글에서 컴포넌트로 이은 화살표는 userElement → 그 컴포넌트", () => {
  const [a] = byType("arrow");
  assert.equal(a.from.userElement, "t-free");
  assert.equal(a.to.dataId, "item-date");
  assert.equal(a.to.device, "mobile");
});

test("빈 캔버스 위 표시는 on: null, 화면 빈 곳은 near", () => {
  assert.equal(byType("rectangle")[0].on, null);
  assert.equal(byType("text")[0].on, null);  // 캔버스 (1600,900)은 칸 밖
});

test("영역(탭바)과 함께 움직인 요소(탭 버튼)는 따로 기록하지 않고, 요소만 옮기면 기록한다", () => {
  const bar = { id: make.component("detail", "mobile", "tab-bar"), type: "image", x: 1000, y: 700, width: 390, height: 80,
    customData: { generated: true, screen: "detail", device: "mobile", component: "tab-bar", text: "", rel0: [0, 760], w0: 390, h0: 80 } };
  const kid = (key, x, rel0x) => ({ id: make.component("detail", "mobile", key), type: "image", x: 1000 + x, y: 700, width: 97, height: 60,
    customData: { generated: true, screen: "detail", device: "mobile", component: key, text: key, rel0: [rel0x, 760], w0: 97, h0: 60, parent: bar.id } });
  const s = [frame, bar, kid("tab-home", 0, 0), kid("tab-new", 150, 293)];  // 탭바 -60, 홈 탭은 함께, 새 모임 탭은 따로 왼쪽으로
  const it = interpret(s, elementAt).items.filter((i) => i.type === "move");
  assert.deepEqual(it.map((i) => i.on.dataId).sort(), ["tab-bar", "tab-new"]);
  // 영역 크기를 줄이면 안의 요소도 따라 줄고 밀린다 — 영역 resize 한 건만
  const shrunk = interpret([frame, { ...bar, y: 760, width: 367, height: 75 }, { ...kid("tab-home", 0, 0), y: 760, width: 91, height: 56 }], elementAt).items;
  assert.deepEqual(shrunk.map((i) => `${i.type}:${i.on.dataId}`), ["resize:tab-bar"]);
  const removed = interpret([frame, { ...bar, isDeleted: true }, { ...kid("tab-home", 0, 0), isDeleted: true }], elementAt).items.filter((i) => i.type === "remove");
  assert.deepEqual(removed.map((i) => i.on.dataId), ["tab-bar"]);
});

test("복원 상태: 바뀐 컴포넌트만, 화면 이동 없음", () => {
  const st = componentsOf(scene);
  assert.deepEqual(Object.keys(st).sort(), [make.component("detail", "mobile", "item-status"), make.component("detail", "mobile", "item-date"),
    make.component("detail", "mobile", "item-note")].sort());
  assert.equal(st[make.component("detail", "mobile", "item-status")].deleted, true);
  assert.deepEqual(movedOf(scene), {});
  assert.ok(mine.every((e) => !e.customData?.generated));
});
