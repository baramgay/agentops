#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
work_log.jsonl에서 자동화 가능한 반복 패턴 분석

사용법:
  python scripts/analyze_automation.py
  python scripts/analyze_automation.py --top 5   # 에이전트별 상위 N 키워드
  python scripts/analyze_automation.py --since 7  # 최근 N일 데이터만 분석
"""
import sys
import io
import json
import argparse
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime, timedelta

# Windows 콘솔 UTF-8 강제
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

ROOT = Path(__file__).parent.parent
log_file = ROOT / 'work_log.jsonl'


def parse_args():
    p = argparse.ArgumentParser(description='work_log.jsonl 자동화 패턴 분석')
    p.add_argument('--top', type=int, default=3, help='에이전트별 상위 키워드 수 (기본 3)')
    p.add_argument('--since', type=int, default=0, help='최근 N일 데이터만 분석 (기본 전체)')
    p.add_argument('--min-repeat', type=int, default=2, help='자동화 후보 최소 반복 횟수 (기본 2)')
    return p.parse_args()


def load_log(since_days: int) -> list:
    if not log_file.exists():
        print('work_log.jsonl 없음')
        sys.exit(0)
    cutoff = None
    if since_days > 0:
        cutoff = datetime.now() - timedelta(days=since_days)
    entries = []
    for line in log_file.read_text(encoding='utf-8', errors='replace').splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
        except Exception:
            continue
        if cutoff:
            ts_raw = e.get('ts') or e.get('timestamp', '')
            if ts_raw:
                try:
                    ts = datetime.fromisoformat(ts_raw[:19])
                    if ts < cutoff:
                        continue
                except Exception:
                    pass
        entries.append(e)
    return entries


def extract_keywords(text: str) -> list:
    """텍스트에서 의미 있는 한글/영문 키워드 추출 (2글자 이상)."""
    import re
    # 한글 단어(2자 이상) + 영문 단어(3자 이상)
    kor = re.findall(r'[가-힣]{2,}', text)
    eng = re.findall(r'[a-zA-Z]{3,}', text)
    # 불용어 제거
    stopwords = {
        '완료', '작업', '시작', '중인', '이후', '처리', '진행', '확인', '사용',
        '생성', '수정', '추가', '결과', '데이터', '파일', '스크립트', '실행',
        'the', 'and', 'for', 'with', 'from', 'this', 'that', 'are', 'was',
    }
    return [k for k in kor + eng if k.lower() not in stopwords]


def classify_task(content: str) -> str:
    """작업 내용으로부터 카테고리 분류."""
    lower = content.lower()
    if any(k in lower for k in ['버그', '오류', '수정', 'fix', 'error', '예외', '충돌']):
        return '버그수정'
    if any(k in lower for k in ['신규', '추가', '새로', '기능', 'add', 'new', '구현', '개발']):
        return '신규기능'
    if any(k in lower for k in ['문서', '주석', '가이드', '매뉴얼', 'doc', 'readme', '보고서']):
        return '문서화'
    if any(k in lower for k in ['리팩', '정리', '개선', '최적화', 'refactor', 'clean']):
        return '개선'
    if any(k in lower for k in ['테스트', '검증', '확인', 'test', 'qa', '통과', '검토']):
        return '테스트'
    if any(k in lower for k in ['배포', 'deploy', '릴리즈', 'release', '동기화', 'sync']):
        return '배포'
    return '기타'


def main():
    args = parse_args()
    entries = load_log(args.since)

    # 기본 통계
    total = len(entries)
    done_entries = [e for e in entries if e.get('status') in ('done', 'idle') and (e.get('content') or e.get('task'))]
    auto_candidates = [e for e in entries if e.get('status') == 'automation_candidate']

    since_label = f'최근 {args.since}일' if args.since > 0 else '전체 기간'
    print(f'\n=== 자동화 패턴 분석 ({since_label}) ===')
    print(f'총 로그: {total:,}건 | 완료 작업: {len(done_entries):,}건 | 자동화 후보 태깅: {len(auto_candidates)}건')

    # 에이전트별 완료 작업 통계
    agent_done: dict = defaultdict(list)
    for e in done_entries:
        aid = e.get('agent_id', 'unknown')
        content = (e.get('content') or e.get('task', '')).strip()
        if content:
            agent_done[aid].append(content)

    print(f'\n--- 에이전트별 완료 작업 (상위 10) ---')
    for aid, tasks in sorted(agent_done.items(), key=lambda x: -len(x[1]))[:10]:
        print(f'  {aid}: {len(tasks)}건')

    # 에이전트별 반복 패턴 분석
    print(f'\n--- 에이전트별 반복 키워드 (상위 {args.top}개) ---')
    agent_patterns: dict = {}
    for aid, tasks in sorted(agent_done.items(), key=lambda x: -len(x[1])):
        kw_counter: Counter = Counter()
        for t in tasks:
            for kw in extract_keywords(t)[:5]:
                kw_counter[kw.lower()] += 1
        top = [(kw, cnt) for kw, cnt in kw_counter.most_common(args.top) if cnt >= args.min_repeat]
        if top:
            agent_patterns[aid] = top
            top_str = ', '.join(f'{k}({v})' for k, v in top)
            print(f'  {aid}: {top_str}')

    # 카테고리별 작업 분포
    print(f'\n--- 작업 카테고리 분포 ---')
    cat_counter: Counter = Counter()
    for e in done_entries:
        content = e.get('content') or e.get('task', '')
        cat_counter[classify_task(content)] += 1
    for cat, cnt in cat_counter.most_common():
        bar = '|' * min(cnt, 40)
        print(f'  {cat:<8}: {bar} {cnt}')

    # 자동화 후보 (min_repeat 이상 반복)
    print(f'\n--- 자동화 후보 (키워드 {args.min_repeat}회 이상 반복) ---')
    found_candidates = False
    for aid, patterns in sorted(agent_patterns.items()):
        strong = [(kw, cnt) for kw, cnt in patterns if cnt >= 3]
        if strong:
            found_candidates = True
            for kw, cnt in strong:
                print(f'  [{aid}] "{kw}" -> {cnt}회 반복 -- 자동화 검토 권장')
    if not found_candidates:
        print('  (3회 이상 반복 패턴 없음)')

    # 기존 자동화 후보 태깅 내역
    if auto_candidates:
        print(f'\n--- API 서버 자동화 후보 태깅 내역 ({len(auto_candidates)}건) ---')
        for e in auto_candidates[-5:]:
            ts = (e.get('ts') or '')[:16]
            content = e.get('content', '')
            aid = e.get('agent_id', '?')
            print(f'  {ts} [{aid}] {content}')

    print(f'\n{"="*40}')
    print(f'분석 완료: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')


if __name__ == '__main__':
    main()
