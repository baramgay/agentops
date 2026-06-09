# -*- coding: utf-8 -*-
"""
커밋 전 자동 동기화 스크립트
사용법: python scripts/sync.py

수행 작업:
  1. agents/ 폴더 스캔 → scripts/md_content.json 갱신
  2. md_content.json → index.html MD_CONTENT 갱신
  3. scripts/stamp.py → metaverse.html 타임스탬프 갱신
  4. scripts/validate.py → 전체 검증
"""
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent

def run(cmd, label):
    print(f'\n[sync] {label}...')
    result = subprocess.run(
        [sys.executable] + cmd,
        cwd=ROOT,
        capture_output=False
    )
    if result.returncode != 0:
        print(f'[FAIL] {label}')
        sys.exit(1)

run(['scripts/update_md_content.py'], 'memory.md/role.md → MD_CONTENT 동기화')
run(['scripts/stamp.py'],             'metaverse.html 타임스탬프 갱신')
run(['scripts/validate.py'],          '전체 검증')

print('\n[sync] OK - ready to commit')
