// design/theme.js 템플릿 — 토큰. references/screen-generation.md §생성 순서 2.
// 바탕은 Basecoat 기본값이다 (schema/stack.json basecoat — CSS의 :root에 이미 있음, 무채색 · --radius .625rem) = seed:basecoat.
// 여기에는 근거가 있어 **바꾸는 값만** 적는다. 값마다 근거 주석(// G3 또는 // 가정: 이유). 적지 않은 변수는 Basecoat 기본값 그대로 쓰인다.
// 화면은 이 이름의 유틸리티만 쓴다 (bg-primary, text-muted-foreground, border-border, rounded-lg, max-w-content). 기본 팔레트·임의 값 금지.
// 빈 템플릿입니다 — 바꿀 줄만 주석을 풀고 "TODO"를 값으로 바꾼다. 근거 없는 값은 적지 않는다 (기본값이 더 낫다).
(() => {
  const tokens = {
    // "--background": "TODO",          // 화면 바탕 — 근거:
    // "--foreground": "TODO",          // 본문 글자 (바탕 위 대비 4.5:1 이상)
    // "--card": "TODO",                // 카드·시트 바탕
    // "--card-foreground": "TODO",
    // "--primary": "TODO",             // 주 행동. 화면당 하나 (components.md 강조 위계 P1) — 근거:
    // "--primary-foreground": "TODO",  // primary 위 글자 (대비 4.5:1 이상)
    // "--secondary": "TODO",           // 보조 버튼·배지 바탕
    // "--secondary-foreground": "TODO",
    // "--muted": "TODO",               // 옅은 면
    // "--muted-foreground": "TODO",    // 보조 글자 (대비 4.5:1 이상 유지)
    // "--accent": "TODO",              // 선택된 칸·칩 바탕
    // "--accent-foreground": "TODO",
    // "--destructive": "TODO",         // 오류·삭제
    // "--border": "TODO",
    // "--input": "TODO",
    // "--ring": "TODO",
    // "--radius": "TODO",              // 모서리 기준 (rounded-sm/md/lg/xl이 여기서 계산) — 근거:
    // 서비스에 필요한 의미 색은 여기에 더한다 (상태·역할·분류 등, 이름은 의미로): "--success": "TODO",
    // "--content-max": "TODO",         // PC 콘텐츠 최대 폭 → max-w-content (PC를 쓰는 화면이 있을 때만) — 근거:
  };

  // Basecoat 변수 전부를 Tailwind 유틸리티 이름에 연결한다 — 위에 적지 않은 것도 (적지 않으면 Basecoat 기본값)
  const BASECOAT = ["background", "foreground", "card", "card-foreground", "popover", "popover-foreground",
    "primary", "primary-foreground", "secondary", "secondary-foreground", "muted", "muted-foreground",
    "accent", "accent-foreground", "destructive", "border", "input", "ring"];
  const NOT_COLOR = ["radius", "content-max"];
  const extra = Object.keys(tokens).map((k) => k.slice(2)).filter((k) => !BASECOAT.includes(k) && !NOT_COLOR.includes(k));
  const root = document.createElement("style");
  root.textContent = `:root{${Object.entries(tokens).map(([k, v]) => `${k}:${v}`).join(";")}}`;
  const tw = document.createElement("style");
  tw.type = "text/tailwindcss";
  tw.textContent = `@theme inline { ${[...BASECOAT, ...extra].map((k) => `--color-${k}: var(--${k});`).join(" ")}
    --radius-sm: calc(var(--radius) - 4px); --radius-md: calc(var(--radius) - 2px); --radius-lg: var(--radius); --radius-xl: calc(var(--radius) + 4px);
    --container-content: var(--content-max);
    --font-sans: "Pretendard Variable", Pretendard, system-ui, -apple-system, "Apple SD Gothic Neo", "Malgun Gothic", sans-serif; }`; // 글꼴은 Pretendard 하나 (stack.json font 계층)
  document.head.append(root, tw); // Basecoat CSS 뒤에 붙어 같은 이름을 덮어쓴다
  document.addEventListener("DOMContentLoaded", () => window.lucide && lucide.createIcons());
})();
