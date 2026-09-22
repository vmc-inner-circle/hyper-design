#!/usr/bin/env python3
"""design-rules.md A표 → design/tokens.css + design/tokens.json

사용:
  python scripts/build_tokens.py [--rules design/design-rules.md] [--out design/]

- status: confirmed 가 아니면 경고 후 종료
- CSS 변수 네이밍: color.accent → --color-accent
- radius "sm 4 / md 8 / lg 12" → --radius-sm, --radius-md, --radius-lg
- shadow "sm ... / md ..." → --shadow-sm, --shadow-md
- type.roles → --type-{role}-size, --type-{role}-weight
- space.scale → --space-{n} (인덱스 기반)
- CSS 대상이 아닌 키 (device, platform, safe-area, tap, z, motion) → json에만 담김
"""
import argparse, json, re, sys, os

NON_CSS_KEYS = {'device.frame', 'safe-area', 'tap.min', 'platform', 'z.scale', 'motion'}

def parse_rules(path):
    text = open(path, encoding='utf-8').read()
    # status 확인
    m = re.search(r'^status:\s*(\S+)', text, re.M)
    if not m or m.group(1) != 'confirmed':
        print(f"⚠ status가 confirmed가 아닙니다 ({m.group(1) if m else '없음'}). 중단합니다.", file=sys.stderr)
        sys.exit(1)
    # A표 파싱
    in_a = False
    rows = []
    for line in text.split('\n'):
        if line.strip().startswith('## A.'):
            in_a = True; continue
        if in_a and line.strip().startswith('## B'):
            break
        if in_a and line.startswith('|') and '---' not in line and '키' not in line:
            cols = [c.strip() for c in line.split('|')[1:-1]]
            if len(cols) >= 2:
                rows.append((cols[0], cols[1], cols[2] if len(cols) > 2 else ''))
    return rows

def to_css_vars(rows):
    css_lines = []
    json_dict = {}
    for key, val, src in rows:
        json_dict[key] = val
        if key in NON_CSS_KEYS:
            continue
        css_key = key.replace('.', '-')
        # radius: "sm 4 / md 8 / lg 12 / xl 16 / full 9999"
        if key == 'radius' and '/' in val:
            for pair in val.split('/'):
                pair = pair.strip()
                parts = pair.split()
                if len(parts) == 2:
                    css_lines.append(f'  --radius-{parts[0]}: {parts[1]}px;')
        # shadow: "sm ... / md ..."
        elif key == 'shadow' and ' / ' in val:
            for pair in val.split(' / '):
                pair = pair.strip()
                name = pair.split()[0]
                rest = pair[len(name):].strip()
                css_lines.append(f'  --shadow-{name}: {rest};')
        # space.scale: "4 / 8 / 12 / 16 / 24 / 32 / 48"
        elif key == 'space.scale':
            for i, v in enumerate(val.split('/')):
                v = v.strip()
                css_lines.append(f'  --space-{i+1}: {v}px;')
        # type.roles: "display 28/700 · h1 24/600 · ..."
        elif key == 'type.roles':
            for role in val.split('·'):
                role = role.strip()
                parts = role.split()
                if len(parts) >= 2:
                    name = parts[0]
                    size_weight = parts[1].split('/')
                    css_lines.append(f'  --type-{name}-size: {size_weight[0]}px;')
                    if len(size_weight) > 1:
                        css_lines.append(f'  --type-{name}-weight: {size_weight[1]};')
        # font.family
        elif key == 'font.family':
            css_lines.append(f'  --font-family: {val};')
        # space.* (단일값)
        elif key.startswith('space.') and key != 'space.scale':
            num = re.search(r'\d+', val)
            if num:
                css_lines.append(f'  --{css_key}: {num.group()}px;')
        # color.* (단일값)
        elif key.startswith('color.'):
            css_lines.append(f'  --{css_key}: {val};')
        else:
            # 기타: 값 그대로
            if val and val != '고정':
                css_lines.append(f'  --{css_key}: {val};')
    return css_lines, json_dict

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--rules', default='design/design-rules.md')
    p.add_argument('--out', default='design/')
    args = p.parse_args()

    rows = parse_rules(args.rules)
    css_lines, json_dict = to_css_vars(rows)

    css = '/* Auto-generated from design-rules.md — do not edit */\n:root {\n'
    css += '\n'.join(css_lines)
    css += '\n}\n'

    os.makedirs(args.out, exist_ok=True)
    css_path = os.path.join(args.out, 'tokens.css')
    json_path = os.path.join(args.out, 'tokens.json')

    with open(css_path, 'w', encoding='utf-8') as f:
        f.write(css)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_dict, f, ensure_ascii=False, indent=2)

    print(f"✓ {css_path} ({len(css_lines)} vars)")
    print(f"✓ {json_path} ({len(json_dict)} keys)")

if __name__ == '__main__':
    main()
