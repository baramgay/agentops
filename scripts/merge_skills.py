"""
merge_skills.py — cc_status/*.json 읽어 합집합 계산 → cc_status/union.json 생성

사용법:
  python scripts/merge_skills.py            # 합집합 계산 + push
  python scripts/merge_skills.py --no-push  # push 생략
  python scripts/merge_skills.py --show     # 결과 출력만 (파일 변경 없음)

각 PC에서 report_cc_status.py 를 실행한 뒤 이 스크립트를 실행하세요.
합집합 결과는 cc_status/union.json 에 저장되며,
build_html.py 가 이 파일을 읽어 index.html 의 스킬 KPI 를 갱신합니다.
"""

import json, sys, subprocess
from datetime import datetime
from pathlib import Path

_SCRIPT_DIR = Path(__file__).parent
_REPO_ROOT   = _SCRIPT_DIR.parent
_CC_STATUS   = _REPO_ROOT / 'cc_status'

def load_reports():
    reports = {}
    for f in sorted(_CC_STATUS.glob('*.json')):
        if f.stem == 'union':
            continue
        try:
            data = json.loads(f.read_text(encoding='utf-8'))
            reports[data['hostname']] = data
        except Exception as e:
            print(f'  경고: {f.name} 읽기 실패 — {e}')
    return reports

def compute_union(reports):
    union_skills = set()
    all_recently  = set()
    machines = []
    for hostname, data in reports.items():
        skills = set(data.get('skills', []))
        union_skills |= skills
        all_recently |= set(data.get('recently_used', []))
        machines.append({
            'hostname':    hostname,
            'reported_at': data.get('reported_at', ''),
            'skill_count': data.get('skill_count', 0),
            'skills':      sorted(skills),
        })

    # 각 스킬이 몇 개 PC에 설치돼 있는지
    skill_presence = {}
    for s in sorted(union_skills):
        present = [m['hostname'] for m in machines if s in m['skills']]
        skill_presence[s] = present

    return {
        'computed_at':    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'machines':       machines,
        'machine_count':  len(machines),
        'union_skills':   sorted(union_skills),
        'union_count':    len(union_skills),
        'recently_used':  sorted(all_recently),
        'skill_presence': skill_presence,
    }

def print_report(union):
    print(f'\n=== 스킬 합집합 결과 ({union["machine_count"]}개 PC) ===')
    for m in union['machines']:
        print(f'  {m["hostname"]}: {m["skill_count"]}개  (보고: {m["reported_at"]})')
    print(f'\n합집합 총 {union["union_count"]}개:')

    # PC별 설치 현황
    print(f'\n{"스킬":<40} {"설치된 PC"}')
    print('-' * 65)
    for skill, hosts in sorted(union['skill_presence'].items()):
        indicator = '★ 모든 PC' if len(hosts) == union['machine_count'] else f'{", ".join(hosts)}'
        print(f'  {skill:<38} {indicator}')

    if union['recently_used']:
        print(f'\n최근 1달 사용 스킬 (전체 합집합):')
        for s in union['recently_used']:
            print(f'  - {s}')

def main():
    no_push = '--no-push' in sys.argv
    show_only = '--show' in sys.argv

    if not _CC_STATUS.exists():
        print('cc_status/ 폴더가 없습니다. git pull 후 재시도하세요.')
        sys.exit(1)

    reports = load_reports()
    if not reports:
        print('보고된 PC가 없습니다. 각 PC에서 report_cc_status.py 를 먼저 실행하세요.')
        sys.exit(1)

    print(f'보고된 PC: {", ".join(reports.keys())}')
    union = compute_union(reports)
    print_report(union)

    if show_only:
        return

    out = _CC_STATUS / 'union.json'
    out.write_text(json.dumps(union, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'\nunion.json 저장 완료: {out}')

    # build_html.py 실행해서 index.html 갱신
    import os, subprocess as sp
    os.chdir(_REPO_ROOT)
    sp.run(['python', 'scripts/build_html.py'], check=True)
    print('index.html 갱신 완료')

    if not no_push:
        try:
            sp.run(['git', 'add', 'cc_status/union.json', 'index.html'], check=True)
            sp.run(['git', 'commit', '-m',
                f'cc: 스킬 합집합 갱신 — {union["union_count"]}개 ({union["machine_count"]}개 PC)'], check=True)
            sp.run(['git', 'push', 'origin', 'master'], check=True)
            print('push 완료')
        except sp.CalledProcessError as e:
            print(f'push 실패: {e}')
    else:
        print('--no-push: 로컬 변경만 완료')

if __name__ == '__main__':
    main()
