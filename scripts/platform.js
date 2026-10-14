/**
 * platform.js — 플랫폼(web·mobile)별로 읽을 패키지 폴더를 한곳에서 정한다. build·lint·pack이 함께 쓴다.
 *
 * mobile은 web 위에 겹쳐 쓴다: 컴포넌트·조각은 web 것을 먼저 읽고 packages/mobile 것을 뒤에 읽는다
 * (같은 클래스는 mobile이 덮어쓰고, 모바일에만 있는 부품 — 위 제목 줄·아래 탭·꽉 찬 버튼·아래에서 올라오는 창 — 은 더한다).
 */
const fs = require("fs");
const path = require("path");
const ROOT = path.resolve(__dirname, "..");

const PLATFORMS = ["web", "mobile"];
const FRAME = { web: { w: 1280, h: 800 }, mobile: { w: 390, h: 844 } };

/** 읽을 패키지 폴더 순서 (뒤가 앞을 덮는다) */
function layers(platform) {
  return platform === "mobile" ? ["web", "mobile"] : ["web"];
}
/** <layer>/<sub> 안의 파일을 레이어 순서·이름순으로 [{ layer, file, path }] */
function files(platform, sub, ext) {
  const out = [];
  for (const layer of layers(platform)) {
    const dir = path.join(ROOT, "packages", layer, sub);
    if (!fs.existsSync(dir)) continue;
    for (const f of fs.readdirSync(dir).filter((x) => x.endsWith(ext)).sort()) out.push({ layer, file: f, path: path.join(dir, f) });
  }
  return out;
}

module.exports = { ROOT, PLATFORMS, FRAME, layers, files };
