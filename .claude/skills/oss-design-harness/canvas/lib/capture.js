// 화면 읽기 — 기기 칸마다 숨은 원본 크기 iframe(probe)을 열어
// ① 높이 결정 ② data-id 컴포넌트 측정·이미지 뜨기 ③ 자동 점검(renderChecks) ④ 좌표 → 요소 판별(elementAt)을 한다.
// (Excalidraw는 화면 밖 embeddable을 렌더하지 않으므로 보이는 칸이 아니라 probe를 쓴다)
import { toPng } from "https://esm.sh/html-to-image@1.11.13";
import { frameKey, make } from "./ids.js";

const INTERACTIVE = "a,button,input,select,textarea,label,[role=button],[onclick]";
const textOf = (n, max) => (n.innerText || n.getAttribute("aria-label") || n.alt || "").trim().replace(/\s+/g, " ").slice(0, max);

export function createCapture(devices, status) {
  const probes = {}, files = {}, renderChecks = [];

  // 탭이 안 보이면 브라우저가 이미지 로딩을 미뤄 뜨기가 멈추므로, 보일 때까지 기다린다
  const visible = () => document.visibilityState === "visible" ? Promise.resolve() : new Promise((ok) => {
    status("이 탭이 화면에 보이면 준비를 이어갑니다…");
    const on = () => { if (document.visibilityState === "visible") { document.removeEventListener("visibilitychange", on); status("화면 구조를 읽는 중…"); ok(); } };
    document.addEventListener("visibilitychange", on);
  });
  // 컴포넌트 하나를 PNG로. 웹 글꼴 자동 넣기는 끈다(켜면 부모 페이지 글꼴까지 받느라 멈춤).
  // 화면이 Pretendard를 쓰면 그 글꼴 파일 하나만 한 번 받아 모든 그림에 넣는다 — 그림 안에서는 CDN 글꼴을 못 읽어 다른 글꼴로 보이므로
  // 떠낸 사본은 제자리에 두고 뜬다(fixed·margin이 남으면 그림 밖으로 밀려 빈 이미지가 됨). 넘으면 포기
  let fontCSS = null;
  // 글꼴 파일 주소는 schema/stack.json의 font 계층(active)의 file — 화면 머리와 같은 곳에서 관리
  const fontFile = fetch("/schema/stack.json").then((r) => r.json())
    .then((s) => s.resources.find((x) => x.layer === "font" && x.status === "active")?.file || null).catch(() => null);
  const fontFor = async (doc) => {
    if (!/pretendard/i.test([...doc.querySelectorAll("link[href],style")].map((e) => e.href || e.textContent).join(" "))) return null;
    fontCSS ??= fontFile.then((u) => u ? fetch(u) : Promise.reject(new Error("no font file"))).then((r) => r.blob()).then((b) => new Promise((ok) => { const fr = new FileReader(); fr.onload = () => ok(fr.result); fr.readAsDataURL(b); }))
      .then((url) => ["Pretendard Variable", "Pretendard"].map((f) => `@font-face{font-family:'${f}';font-weight:45 920;font-style:normal;src:url(${url}) format('woff2');}`).join(""))
      .catch(() => null);
    return fontCSS;
  };
  const snapshot = async (n, height) => {
    await visible();
    const fontEmbedCSS = await fontFor(n.ownerDocument);
    return Promise.race([
      toPng(n, { pixelRatio: 2, skipFonts: true, ...(fontEmbedCSS ? { fontEmbedCSS } : {}), ...(height ? { height } : {}), style: { position: "static", margin: "0", inset: "auto", transform: "none" } }),
      new Promise((_, no) => setTimeout(() => no(new Error("timeout")), fontEmbedCSS ? 8000 : 4000)),
    ]);
  };
  const loaded = (f) => new Promise((ok) => {
    f.addEventListener("load", () => {  // Tailwind CDN이 스타일을 입히고 웹 글꼴이 들어올 시간
      const fonts = f.contentDocument?.fonts?.ready || Promise.resolve();
      Promise.race([fonts, new Promise((r) => setTimeout(r, 2500))]).then(() => setTimeout(ok, 400));
    }, { once: true });
    setTimeout(ok, 6000);
  });

  // 기기 칸 하나를 읽는다. fr.h는 content 기기면 내용 길이로 바뀐다. 반환: 옮길 수 있는 컴포넌트 목록
  async function measureFrame(fr) {
    const dev = devices[fr.device];
    const f = document.createElement("iframe");
    f.src = fr.file;
    f.style.cssText = `position:fixed;left:-30000px;top:0;width:${fr.w}px;height:${fr.h}px;border:0;visibility:hidden`;
    document.body.appendChild(f);
    probes[fr.key] = f;
    await loaded(f);
    const doc = f.contentDocument;
    if (!doc?.documentElement) return [];
    if (dev.height.mode === "content") {
      fr.h = Math.min(Math.max(doc.documentElement.scrollHeight, dev.height.value), dev.height.max || 3000);
      f.style.height = fr.h + "px";
      await new Promise((r) => setTimeout(r, 150));
    }

    const check = (type, extra) => renderChecks.push({ type, screen: fr.screen, device: fr.device, ...extra });
    const declared = (doc.documentElement.getAttribute("data-devices") || "").split(/\s+/).filter(Boolean);
    if (!declared.includes(fr.device)) check("devices-mismatch", { detail: `data-devices="${declared.join(" ")}"` });
    if (doc.documentElement.scrollWidth > fr.w + 1) check("overflow-x", { detail: `폭 ${doc.documentElement.scrollWidth} > ${fr.w}` });

    // 옮길 수 있는 컴포넌트는 2단계: 영역(가장 바깥 data-id) → 요소(그 안의 data-id). 더 깊은 것은 요소 그림에 포함되고 가리키기만 된다
    const seen = {}, comps = [], keyOf = new Map();
    const parentOf = (n) => n.parentElement?.closest("[data-id]") || null;
    for (const n of doc.querySelectorAll("[data-id]")) {
      const r = n.getBoundingClientRect(), dataId = n.getAttribute("data-id");
      if (r.width <= 4 || r.height <= 4) continue;  // 이 기기에서 숨겨진 요소
      if (r.top >= fr.h) { check("below-fold", { dataId, detail: `y ${Math.round(r.top)} ≥ ${fr.h}` }); continue; }
      if (dev.input === "touch" && n.matches(INTERACTIVE) && (r.width < dev.minTouch || r.height < dev.minTouch))
        check("touch-target", { dataId, detail: `${Math.round(r.width)}×${Math.round(r.height)} < ${dev.minTouch}` });
      const p = parentOf(n);
      if (p && parentOf(p)) continue;  // 3단계 이상
      seen[dataId] = (seen[dataId] || 0) + 1;
      const key = seen[dataId] > 1 ? `${dataId}#${seen[dataId]}` : dataId, fileId = make.file(fr.screen, fr.device, key);
      // 영역을 뜰 때는 안의 요소를 잠시 숨긴다 — 요소는 따로 뜨므로, 요소를 옮겼을 때 영역 그림에 같은 것이 남지 않게
      const kids = p ? [] : [...n.querySelectorAll("[data-id]")].filter((k) => parentOf(k) === n);
      kids.forEach((k) => { k.dataset.v = k.style.visibility; k.style.visibility = "hidden"; });
      try {
        files[fileId] = { id: fileId, mimeType: "image/png", dataURL: await snapshot(n, r.bottom > fr.h ? Math.floor(fr.h - r.top) : 0), created: Date.now() };
      } catch (e) { continue; }  // 이미지로 못 뜨면 그 요소는 화면에 그대로 둔다
      finally { kids.forEach((k) => { k.style.visibility = k.dataset.v; delete k.dataset.v; }); }
      keyOf.set(n, key);
      comps.push({ dataId, key, fileId, parent: p ? keyOf.get(p) || null : null,
        x: r.left, y: r.top, w: r.width, h: Math.min(r.bottom, fr.h) - r.top, text: textOf(n, 60) });
    }
    // 영역 먼저, 요소는 그 위에 (같은 단계에서는 큰 것부터 — 작은 것이 위에 와야 선택된다)
    return comps.sort((a, b) => (!!a.parent - !!b.parent) || (b.w * b.h - a.w * a.h));
  }

  // 기기 칸 안 좌표 → { dataId, text } 또는 빈 곳이면 { near: { dataId, distance } }
  function elementAt(screen, device, x, y) {
    try {
      const doc = probes[frameKey(screen, device)].contentDocument, node = doc.elementFromPoint(x, y);
      const tagged = node?.closest("[data-id]");
      if (tagged) return { dataId: tagged.getAttribute("data-id"), text: textOf(node, 80) };
      let best = null, bd = Infinity;
      doc.querySelectorAll("[data-id]").forEach((n) => {
        const r = n.getBoundingClientRect();
        if (r.width <= 4 || r.height <= 4) return;
        const d = Math.hypot(Math.max(r.left - x, 0, x - r.right), Math.max(r.top - y, 0, y - r.bottom));
        if (d < bd) { bd = d; best = n; }
      });
      return best ? { near: { dataId: best.getAttribute("data-id"), distance: Math.round(bd) } } : {};
    } catch (e) { return { error: "요소를 읽지 못함" }; }
  }

  return { measureFrame, elementAt, renderChecks, files };
}
