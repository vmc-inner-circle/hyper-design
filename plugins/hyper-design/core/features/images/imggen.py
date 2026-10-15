"""사진 자리(image_slots.json 의 kind=photo)를 생성 시트로 채운다 — 실패하면 회색 자리표시를 그대로 둔다.

  python3 imggen.py <out> [--placeholders-only] [--cmd "<generator command>"] [--timeout 480]

순서: ① 자리표시 즉시 생성 ② 시트 계획(최소 시트, 칸마다 슬롯 비율로 자르기)·프롬프트 ③ 생성기를 시트마다 순서대로 호출 ④ 흰 간격 감지로 자르기
⑤ 빈칸은 같은 시트 사진의 다른 구도(.images/alt/) ⑥ credits.json 병합 ⑦ .images/status.json 기록. 처리된 경우는 모두 종료 코드 0.
"""
import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image

LONG = 1200
GREY = (226, 226, 222)
AUTHOR = "AI 생성 (codex image_generation)"


# ── 비율 ─────────────────────────────────────────────────────────────
def parse_ratio(r):
    try:
        a, b = str(r).split(":")
        a, b = int(a), int(b)
        if a > 0 and b > 0:
            return a, b
    except Exception:
        pass
    return 3, 4


def size_for(ratio):
    rw, rh = ratio
    if rw >= rh:
        return LONG, max(1, round(LONG * rh / rw))
    return max(1, round(LONG * rw / rh)), LONG


# ── 자르기 (runs/imggen-test/crop_grid.py 이식) ─────────────────────────
def runs(mask):
    """True가 이어지는 구간 [(start, end)] — end는 포함하지 않음."""
    out, start = [], None
    for i, v in enumerate(mask):
        if v and start is None:
            start = i
        elif not v and start is not None:
            out.append((start, i))
            start = None
    if start is not None:
        out.append((start, len(mask)))
    return out


def bands(img, axis, n, thresh=245, ratio=0.985):
    """axis=0: 열 구간, axis=1: 행 구간. 거의 흰 줄을 간격으로 보고 내용 구간 n개와 감지 성공 여부를 돌려준다."""
    g = img.convert("L")
    w, h = g.size
    px = g.load()
    length, across = (w, h) if axis == 0 else (h, w)
    white = []
    for i in range(length):
        cnt = sum(1 for j in range(0, across, 2) if (px[i, j] if axis == 0 else px[j, i]) >= thresh)
        white.append(cnt / ((across + 1) // 2) >= ratio)
    content = [(a, b) for a, b in runs([not v for v in white]) if b - a > length * 0.03]
    if len(content) != n:
        step = length / n
        return [(round(i * step), round((i + 1) * step)) for i in range(n)], False
    return content, True


def center_crop(cell, ratio):
    rw, rh = ratio
    w, h = cell.size
    if w * rh > h * rw:
        nw, nh = max(1, round(h * rw / rh)), h
    else:
        nw, nh = w, max(1, round(w * rh / rw))
    x0, y0 = (w - nw) // 2, (h - nh) // 2
    return cell.crop((x0, y0, x0 + nw, y0 + nh))


def crop_sheet(path, cols, rows, ratio=None):
    """시트를 읽기 순서 칸 이미지 목록으로 자른다. ratio=(w,h)면 칸마다 가운데 자르기.
    돌려주는 값: (cells, detected) — detected=False면 균등 분할로 대체한 것."""
    img = Image.open(path).convert("RGB")
    cb, okc = bands(img, 0, cols)
    rb, okr = bands(img, 1, rows)
    cells = []
    for (y0, y1) in rb:
        for (x0, x1) in cb:
            c = img.crop((x0, y0, x1, y1))
            cells.append(center_crop(c, ratio) if ratio else c)
    return cells, okc and okr


# ── 슬롯·시트 ─────────────────────────────────────────────────────────
def first_en(s):
    en = s.get("en")
    if isinstance(en, list):
        en = next((x for x in en if isinstance(x, str) and x.strip()), None)
    if isinstance(en, str) and en.strip():
        return en.strip()
    return str(s.get("what", s.get("slot", "object")))


def orient(s):
    """'S' 정사각 · 'L' 가로 · 'P' 세로."""
    w, h = parse_ratio(s.get("ratio", "3:4"))
    return "S" if w == h else "L" if w > h else "P"


def _cell_ratio(chunk):
    """2×2 시트 칸 비율: 가로 ≥ 세로면 4:3, 아니면 3:4. 정사각만 있으면 1:1."""
    o = [orient(s) for s in chunk]
    nl, np_ = o.count("L"), o.count("P")
    if nl == 0 and np_ == 0:
        return "1:1"
    return "4:3" if nl >= np_ else "3:4"


def plan_sheets(photos):
    """[(cell_ratio, cols, rows, [slots])] — 시트를 최소로 만들고 칸마다 슬롯 비율로 가운데 자른다.

    규칙(같은 입력이면 같은 결과):
    1. 사진 ≤ 4장 → 2×2 시트 하나에 모두.
    2. 그 밖: 정사각은 최대 16칸(≤4 → 2×2, ≤9 → 3×3, 그 밖 4×4). 가로·세로는 방향별로 모아 최대 4칸 2×2.
    3. 1–2장만 남은 묶음(가로·세로·정사각의 마지막 묶음)은 빈칸이 충분한 다른 2×2 방향 시트에 합친다 —
       반대 방향 시트 우선, 다음 같은 방향, 동률이면 앞 시트. 작은 묶음부터, 같으면 L → P → S 순서.
    4. 2×2 방향 시트의 칸 비율은 가로 ≥ 세로면 4:3, 아니면 3:4 (정사각만이면 1:1).
    """
    if not photos:
        return []
    if len(photos) <= 4:
        return [(_cell_ratio(photos), 2, 2, list(photos))]
    pools = {"L": [], "P": [], "S": []}
    for s in photos:
        pools[orient(s)].append(s)
    groups = []  # [kind, items]
    for k in ("L", "P"):
        items = pools[k]
        for i in range(0, len(items), 4):
            groups.append([k, items[i:i + 4]])
    sq = pools["S"]
    for i in range(0, len(sq), 16):
        groups.append(["S", sq[i:i + 16]])

    order = {"L": 0, "P": 1, "S": 2}
    opposite = {"L": "P", "P": "L", "S": None}
    while True:
        small = [g for g in groups if 1 <= len(g[1]) <= 2]
        small.sort(key=lambda g: (len(g[1]), order[g[0]], groups.index(g)))
        merged = False
        for g in small:
            need = len(g[1])
            targets = [t for t in groups if t is not g and t[0] in ("L", "P") and 4 - len(t[1]) >= need]
            if not targets:
                continue
            targets.sort(key=lambda t: (0 if t[0] == opposite[g[0]] else 1, groups.index(t)))
            t = targets[0]
            t[1] = t[1] + g[1]
            groups.remove(g)
            merged = True
            break
        if not merged:
            break

    sheets = []
    for k, chunk in groups:
        if k == "S":
            gsz = 2 if len(chunk) <= 4 else 3 if len(chunk) <= 9 else 4
            sheets.append(("1:1", gsz, gsz, chunk))
        else:
            sheets.append((_cell_ratio(chunk), 2, 2, chunk))
    return sheets


def same_ratio(a, b):
    (aw, ah), (bw, bh) = parse_ratio(a), parse_ratio(b)
    return aw * bh == ah * bw


def sheet_plan(sheets):
    return [{"cells": f"{c}x{r}", "cell_ratio": cr, "slots": [s["slot"] for s in chunk]} for cr, c, r, chunk in sheets]


def build_prompt(ratio_str, cols, rows, chunk):
    n = cols * rows
    parts = [
        f"A single image laid out as an exact grid of {cols} columns x {rows} rows ({n} equal cells), "
        f"each cell with a {ratio_str} aspect ratio. Uniform pure white gutters of about 3% between cells "
        "and a pure white outer margin around the grid. Photorealistic, consistent colour grading across all cells. "
        "A single object is shown on a plain light warm-grey seamless background with soft daylight, product photography; "
        "a scene, interior or portrait is shown in its natural setting exactly as described, with natural light. "
        "No text, no labels, no numbers, no logos, no brand marks. "
        "Do not depict the face of any real, identifiable person."
    ]
    cells = []
    for i, s in enumerate(chunk):
        r = s.get("ratio", "3:4")
        line = f"{i + 1} {first_en(s)}"
        if not same_ratio(r, ratio_str):
            line += f" (keep the subject centred, it will be cropped to {r})"
        cells.append(line)
    for j in range(len(chunk), n):
        s = chunk[(j - len(chunk)) % len(chunk)]
        cells.append(f"{j + 1} alternate angle of: {first_en(s)}")
    parts.append("Cells in reading order: " + "; ".join(cells) + ".")
    return " ".join(parts)


# ── 생성기 ────────────────────────────────────────────────────────────
def _argv_for(cmd):
    toks = shlex.split(cmd, posix=(os.name != "nt"))
    toks = [t[1:-1] if len(t) >= 2 and t[0] == t[-1] and t[0] in "\"'" else t for t in toks]
    if not toks:
        return None
    head = toks[0]
    p = Path(head).expanduser()
    if p.is_file():
        head = str(p)
    elif not shutil.which(head):
        return None
    if head.lower().endswith(".py"):
        return [sys.executable, head] + toks[1:]
    if os.name == "nt" and Path(head).is_file() and Path(head).suffix == "":
        return ["bash", head] + toks[1:]
    return [head] + toks[1:]


def resolve_cmd(cli_cmd):
    for c in (cli_cmd, os.environ.get("HD_IMAGE_CMD")):
        if c:
            argv = _argv_for(c)
            if argv:
                return argv
    bridge = Path.home() / ".claude/skills/gpt-image-bridge/bin/gpt-image-2"
    if bridge.is_file():
        return (["bash", str(bridge)] if os.name == "nt" else [str(bridge)])
    return None


# ── 파일 쓰기 ─────────────────────────────────────────────────────────
def write_json(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, p)


def merge_credits(out, photos, generated):
    p = out / "credits.json"
    try:
        cur = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(cur, list):
            cur = []
    except Exception:
        cur = []
    mine = {f"assets/photos/{s['slot']}.jpg" for s in photos}
    keep = [c for c in cur if not (isinstance(c, dict) and c.get("file") in mine)]
    for s in photos:
        if s["slot"] in generated:
            keep.append({"slot": s["slot"], "file": f"assets/photos/{s['slot']}.jpg", "author": AUTHOR,
                         "license": "generated", "url": "", "title": s.get("what", "")})
    write_json(p, keep)


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="image_slots.json 의 사진 자리를 생성 시트로 채운다(실패 시 회색 자리표시 유지).")
    ap.add_argument("out", help="산출 폴더(image_slots.json 이 있는 곳)")
    ap.add_argument("--placeholders-only", action="store_true", help="자리표시만 쓰고 끝낸다")
    ap.add_argument("--cmd", default=None, help='생성기 명령 — `<cmd> "<prompt>" <abs.png>` 로 호출')
    ap.add_argument("--timeout", type=int, default=480, help="시트당 제한 시간(초)")
    a = ap.parse_args(argv)

    t0 = time.time()
    out = Path(a.out).resolve()
    photos_dir = out / "assets/photos"
    photos_dir.mkdir(parents=True, exist_ok=True)
    status_p = out / ".images/status.json"
    slots = json.loads((out / "image_slots.json").read_text(encoding="utf-8"))
    photos = [s for s in slots if isinstance(s, dict) and s.get("slot") and s.get("kind", "photo") == "photo"]

    for s in photos:
        Image.new("RGB", size_for(parse_ratio(s.get("ratio", "3:4"))), GREY).save(photos_dir / f"{s['slot']}.jpg", quality=70)

    sheets = plan_sheets(photos)
    notes, generated = [], set()
    alternates = [0]

    def status(state, **kw):
        d = {"state": state, "sheets": len(sheets), "generated": len(generated),
             "placeholders": len(photos) - len(generated), "alternates": alternates[0],
             "elapsed_s": round(time.time() - t0, 1), "notes": notes, "sheet_plan": sheet_plan(sheets)}
        d.update(kw)
        write_json(status_p, d)
        return d

    status("running")

    def finish(state, **kw):
        merge_credits(out, photos, generated)
        d = status(state, **kw)
        print(f"imggen {d['state']}: sheets {d['sheets']} · generated {d['generated']} · "
              f"placeholders {d['placeholders']} · {d['elapsed_s']}s" + (f" · {kw['reason']}" if kw.get("reason") else ""))
        return 0

    if a.placeholders_only:
        notes.append("placeholders-only")
        return finish("fallback", reason="placeholders-only")
    if not photos:
        return finish("done")
    argv_cmd = resolve_cmd(a.cmd)
    if not argv_cmd:
        notes.append("no generator")
        return finish("fallback", reason="no generator")

    for n, (r, cols, rows, chunk) in enumerate(sheets, 1):
        sheet = out / ".images" / f"sheet-{n}.png"
        if sheet.exists():
            sheet.unlink()
        prompt = build_prompt(r, cols, rows, chunk)
        try:
            pr = subprocess.run(argv_cmd + [prompt, str(sheet)], capture_output=True, timeout=a.timeout)
        except subprocess.TimeoutExpired:
            notes.append(f"sheet-{n}: timeout {a.timeout}s")
            continue
        except OSError as e:
            notes.append(f"sheet-{n}: launch failed ({e})")
            continue
        if pr.returncode != 0:
            tail = (pr.stderr or b"").decode("utf-8", "replace").strip().splitlines()[-1:] or [""]
            notes.append(f"sheet-{n}: exit {pr.returncode} {tail[0][:200]}".rstrip())
            continue
        if not sheet.is_file():
            notes.append(f"sheet-{n}: no output file")
            continue
        try:
            cells, ok = crop_sheet(sheet, cols, rows)
        except Exception as e:
            notes.append(f"sheet-{n}: crop failed ({e})")
            continue
        if not ok:
            notes.append(f"sheet {n}: equal split fallback")
        for s, cell in zip(chunk, cells):
            sr = parse_ratio(s.get("ratio", "3:4"))
            center_crop(cell, sr).resize(size_for(sr), Image.LANCZOS).save(photos_dir / f"{s['slot']}.jpg", quality=88)
            generated.add(s["slot"])
        alt_dir = out / ".images/alt"
        seen = {}
        for j, cell in enumerate(cells[len(chunk):]):
            s = chunk[j % len(chunk)]
            seen[s["slot"]] = seen.get(s["slot"], 0) + 1
            sr = parse_ratio(s.get("ratio", "3:4"))
            alt_dir.mkdir(parents=True, exist_ok=True)
            center_crop(cell, sr).resize(size_for(sr), Image.LANCZOS).save(
                alt_dir / f"{s['slot']}-alt{seen[s['slot']]}.jpg", quality=85)
            alternates[0] += 1
        status("running")

    return finish("done" if len(generated) == len(photos) else "fallback")


if __name__ == "__main__":
    sys.exit(main())
