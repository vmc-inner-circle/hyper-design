// 보드 불러오기 — board.json + devices.json + canvas-state.json을 읽고, 화면 안 링크를 따라 하위 페이지를 찾는다.
import { frameKey } from "./ids.js";

export const MAX_PAGES = 20;  // 링크로 찾아 올릴 수 있는 페이지 수 상한 (board.json 화면 포함)

export async function loadBoard() {
  const raw = await (await fetch("/schema/devices.json")).json();
  const devices = Object.fromEntries(Object.entries(raw).filter(([k]) => !k.startsWith("$")));
  const board = await (await fetch("board.json")).json();
  let state = null;
  try { const r = await fetch("canvas-state.json"); if (r.ok) state = await r.json(); } catch (e) {}
  const boardDevices = board.devices || ["mobile"];
  const screens = board.screens.map((s, i) => ({ ...s, row: s.row || 0, order: s.order ?? i,
    devices: (s.devices || boardDevices).filter((d) => devices[d]) }));
  return { devices, board, state, screens };
}

// 화면 × 기기 = 기기 칸
export const makeFrames = (screens, devices) => screens.flatMap((s) => s.devices.map((d) => ({
  key: frameKey(s.id, d), screen: s.id, device: d, file: s.file, w: devices[d].width, h: devices[d].height.value })));

const loadHidden = (file, width) => new Promise((ok) => {
  const f = document.createElement("iframe");
  f.src = file;
  f.style.cssText = `position:fixed;left:-40000px;top:0;width:${width}px;height:800px;border:0;visibility:hidden`;
  document.body.appendChild(f);
  const done = () => ok(f);
  f.addEventListener("load", done, { once: true });
  setTimeout(done, 5000);
});

// 화면 안 <a href>를 따라가며 ① board.json에 없는 페이지를 screens에 더하고(discovered) ② 링크 관계를 모은다.
// 반환: links = [{ from, to, back, dataId, text }] — back은 data-back(뒤로·취소) 링크, dataId는 링크를 감싼 가장 가까운 data-id
export async function discover(screens, devices) {
  const byPath = new Map(screens.map((s) => [new URL(s.file, location.href).pathname, s]));
  const queue = [...screens], links = [];
  while (queue.length) {
    const s = queue.shift();
    const f = await loadHidden(s.file, devices[s.devices[0]].width);
    const doc = f.contentDocument;
    if (s.discovered) s.title = doc?.querySelector("h1")?.innerText.trim() || doc?.title || s.id;
    let k = 0;
    for (const a of doc?.querySelectorAll("a[href]") || []) {
      const url = new URL(a.getAttribute("href"), f.src);
      if (url.origin !== location.origin || !url.pathname.endsWith(".html")) continue;
      let t = byPath.get(url.pathname);
      if (!t) {
        if (byPath.size >= MAX_PAGES) continue;
        const file = decodeURIComponent(url.pathname.slice(1));
        const base = file.replace(/^.*\//, "").replace(/\.html$/, "").toLowerCase().replace(/[^a-z0-9-]/g, "-");
        let id = base, i = 2;
        while (screens.some((x) => x.id === id)) id = `${base}-${i++}`;  // 다른 폴더의 같은 파일 이름
        // 발견한 화면의 오른쪽 바로 옆에 놓는다
        t = { id, file, title: id, row: s.row, order: s.order + 0.5 + 0.01 * ++k, devices: s.devices, discovered: true, from: s.id };
        byPath.set(url.pathname, t); screens.push(t); queue.push(t);
      }
      // 탭바 같은 전역 내비게이션(data-nav 안)은 페이지 찾기에만 쓰고 관계 화살표는 그리지 않는다 (모든 화면에서 반복되어 흐름을 가림)
      if (t.id !== s.id && !a.closest("[data-nav]")) links.push({ from: s.id, to: t.id, back: !!a.closest("[data-back]"),
        dataId: a.closest("[data-id]")?.getAttribute("data-id") || null,
        text: a.innerText.trim().replace(/\s+/g, " ").slice(0, 20) });
    }
    f.remove();
  }
  return links;
}
