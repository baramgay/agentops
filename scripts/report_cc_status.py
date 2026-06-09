"""
report_cc_status.py — 이 PC의 Claude Code 스킬 현황을 cc_status/[호스트명].json 에 기록 후 push

사용법:
  python scripts/report_cc_status.py
  python scripts/report_cc_status.py --no-push   (push 생략, 로컬만 저장)

각 PC에서 스킬 정리 후 이 스크립트를 실행하면,
merge_skills.py 가 합집합을 계산해 cc_status/union.json 을 생성합니다.
"""

import json, socket, sys, subprocess
from datetime import datetime
from pathlib import Path
import re

_SCRIPT_DIR = Path(__file__).parent
_REPO_ROOT   = _SCRIPT_DIR.parent
_CC_DIR      = Path.home() / '.claude'

def collect_skills():
    skills_dir = _CC_DIR / 'skills'
    if not skills_dir.exists():
        return []
    return sorted([d.name for d in skills_dir.iterdir() if d.is_dir()])

def collect_hooks():
    settings = _CC_DIR / 'settings.json'
    if not settings.exists():
        return {}
    try:
        data = json.loads(settings.read_text(encoding='utf-8'))
        raw = data.get('hooks', {})
    except Exception:
        return {}
    hooks = {}
    for event, entries in raw.items():
        for entry in entries:
            items = []
            for h in entry.get('hooks', []):
                cmd = h.get('command', '')
                if 'memory' in cmd.lower():
                    items.append('메모리 로더')
                elif 'hookify' in cmd.lower() and 'pretooluse' in cmd.lower():
                    items.append('hookify pretooluse 분석기')
                elif 'hookify' in cmd.lower() and 'posttooluse' in cmd.lower():
                    items.append('hookify posttooluse 분석기')
                elif cmd:
                    items.append(cmd[:80].strip())
            matcher = entry.get('matcher', '')
            key = f"{event}:{matcher}" if matcher else event
            hooks[key] = items
    return hooks

def collect_recently_used(days=30):
    """최근 N일간 세션 로그에서 실제 호출된 스킬 수집."""
    from datetime import timedelta
    import glob
    cutoff = datetime.now() - timedelta(days=days)
    used = set()
    pattern = str(Path.home() / '.claude' / 'projects' / '**' / '*.jsonl')
    for jf in glob.glob(pattern, recursive=True):
        try:
            if datetime.fromtimestamp(Path(jf).stat().st_mtime) < cutoff:
                continue
            with open(jf, encoding='utf-8', errors='ignore') as f:
                for line in f:
                    hits = re.findall(r'"skill":\s*"([^"]+)"', line)
                    used.update(hits)
        except Exception:
            pass
    return sorted(used)

def main():
    no_push = '--no-push' in sys.argv

    hostname = socket.gethostname()
    skills   = collect_skills()
    hooks    = collect_hooks()
    recently = collect_recently_used(30)

    status = {
        'hostname':        hostname,
        'reported_at':     datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'skills':          skills,
        'skill_count':     len(skills),
        'hooks':           hooks,
        'hook_count':      sum(len(v) for v in hooks.values()),
        'recently_used':   recently,
    }

    out_path = _REPO_ROOT / 'cc_status' / f'{hostname}.json'
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f'[{hostname}] 스킬 {len(skills)}개 · 훅 {status["hook_count"]}개 · 최근사용 {len(recently)}개')
    print(f'저장: {out_path}')

    if not no_push:
        try:
            import os
            os.chdir(_REPO_ROOT)
            subprocess.run(['git', 'add', f'cc_status/{hostname}.json'], check=True)
            subprocess.run(['git', 'commit', '-m',
                f'cc: [{hostname}] 스킬 현황 보고 ({len(skills)}개)'], check=True)
            subprocess.run(['git', 'push', 'origin', 'master'], check=True)
            print('push 완료')
        except subprocess.CalledProcessError as e:
            print(f'push 실패 (수동으로 push 필요): {e}')
    else:
        print('--no-push: 로컬 저장만 완료')

if __name__ == '__main__':
    main()
