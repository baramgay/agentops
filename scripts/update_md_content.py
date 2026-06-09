# -*- coding: utf-8 -*-
"""
index.html의 MD_CONTENT를 실제 memory.md/role.md 내용으로 갱신
idempotent — 몇 번을 실행해도 중복 발생 없음

사용법: python scripts/update_md_content.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
AGENTS_DIR = ROOT / 'agents'
INDEX_HTML = ROOT / 'index.html'
MC_JSON = Path(__file__).parent / 'md_content.json'


def scan_agents():
    if not AGENTS_DIR.exists():
        print(f"[update_md_content] 에이전트 디렉터리 없음: {AGENTS_DIR}", file=sys.stderr)
        sys.exit(1)
    result = {}
    for d in sorted(AGENTS_DIR.iterdir()):
        if not d.is_dir():
            continue
        role = (d / 'role.md').read_text(encoding='utf-8') if (d / 'role.md').exists() else ''
        mem  = (d / 'memory.md').read_text(encoding='utf-8') if (d / 'memory.md').exists() else ''
        result[d.name] = {'role': role, 'memory': mem}
    return result


def main():
    data = scan_agents()
    md_json_str = json.dumps(data, ensure_ascii=False)

    # md_content.json 갱신
    MC_JSON.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')

    # index.html의 MD_CONTENT 값만 교체 — 줄 단위 교체로 greedy 정규식 버그 방지
    # (re.DOTALL + greedy .*가 뒤쪽 IIFE 코드의 }; 까지 삼키는 문제 수정)
    if not INDEX_HTML.exists():
        print(f"[update_md_content] index.html 없음: {INDEX_HTML}", file=sys.stderr)
        sys.exit(1)
    html = INDEX_HTML.read_text(encoding='utf-8')
    replacement_line = f'const MD_CONTENT = {md_json_str};'
    lines = html.splitlines(keepends=True)
    new_lines = []
    replaced = 0
    skip_to_close = False
    brace_depth = 0
    for line in lines:
        if skip_to_close:
            brace_depth += line.count('{') - line.count('}')
            if brace_depth <= 0:
                skip_to_close = False
            continue
        stripped = line.strip()
        if not replaced and stripped.startswith('const MD_CONTENT = {'):
            new_lines.append(replacement_line + '\n')
            replaced += 1
            depth = stripped.count('{') - stripped.count('}')
            if depth > 0:
                skip_to_close = True
                brace_depth = depth
        else:
            new_lines.append(line)
    if not replaced:
        print('[WARN] MD_CONTENT 패턴을 찾지 못했습니다.')
        sys.exit(1)

    INDEX_HTML.write_text(''.join(new_lines), encoding='utf-8')
    with_mem = sum(1 for v in data.values() if v['memory'].strip())
    print(f'[OK] MD_CONTENT {len(data)} agents, memory {with_mem}')


if __name__ == '__main__':
    main()
