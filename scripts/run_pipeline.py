#!/usr/bin/env python3
"""
DAG 기반 병렬 파이프라인 실행기
개발팀 파이프라인을 위상 정렬로 분석하여 병렬 단계를 식별하고 순차 실행

사용법:
    python scripts/run_pipeline.py dev [--dry-run] [--phase PHASE]

예시:
    python scripts/run_pipeline.py dev              # 전체 파이프라인 실행
    python scripts/run_pipeline.py dev --dry-run    # 실행 계획만 출력
    python scripts/run_pipeline.py dev --phase 2    # 2단계만 실행
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from collections import deque, defaultdict

# Windows 콘솔(cp949)에서 이모지·한글 출력 시 UnicodeEncodeError 방지
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# 공통 I/O 임포트
sys.path.insert(0, str(Path(__file__).parent))
from common_io import load_status, save_status

# ── 설정 ────────────────────────────────────

PIPELINE = {
    'data-collector': ['data-cleaner'],
    'data-cleaner':   ['eda-analyst', 'gis-specialist', 'text-analyst'],
    'eda-analyst':    ['statistician', 'ml-engineer', 'deep-learning'],
    'gis-specialist': ['statistician'],
    'text-analyst':   ['ml-engineer'],
    'statistician':   ['visualizer'],
    'ml-engineer':    ['visualizer'],
    'deep-learning':  ['visualizer'],
    'visualizer':     ['reporter'],
    'reporter':       ['orchestrator'],
    # 개발팀 파이프라인
    'requirements':   ['ux-designer', 'dba'],
    'ux-designer':    ['frontend'],
    'dba':            ['backend'],
    'frontend':       ['security', 'tester-unit'],
    'backend':        ['security', 'tester-unit'],
    'security':       ['tester-qa'],
    'tester-unit':    ['tester-qa'],
    'tester-qa':      ['devops', 'tech-writer'],
    # 부동산동향 월보 파이프라인 (realty-analyst 독자 운영)
    'realty-analyst': ['lead-data'],
    # PPTX 팀 파이프라인
    'pptx-planner':   ['pptx-content', 'pptx-designer'],
    'pptx-content':   ['pptx-builder'],
    'pptx-designer':  ['pptx-builder'],
    'pptx-builder':   ['pptx-reviewer'],
    'pptx-reviewer':  ['orchestrator'],
}

TEAM_PIPELINE = {
    'dev': [
        'requirements',
        'ux-designer', 'dba',
        'frontend', 'backend',
        'security', 'tester-unit',
        'tester-qa',
        'devops', 'tech-writer'
    ],
    'data': [
        'data-collector', 'data-cleaner',
        'eda-analyst', 'gis-specialist', 'text-analyst',
        'statistician', 'ml-engineer', 'deep-learning',
        'visualizer', 'reporter'
    ],
    'pptx': [
        'pptx-planner', 'pptx-content', 'pptx-designer',
        'pptx-builder', 'pptx-reviewer'
    ],
    'realty': [
        'realty-analyst'
    ],
}

STATUS_LABEL = {
    "working": "작업 시작",
    "review":  "검토 중",
    "waiting": "대기",
    "done":    "완료",
    "idle":    "유휴",
}

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
STATUS_FILE = PROJECT_DIR / "agent_status.json"

# ── 유틸리티 ─────────────────────────────────

def update_agent(agent_id, status, task=""):
    """update_status.py를 호출하여 단일 에이전트 상태 변경"""
    update_script = SCRIPT_DIR / "update_status.py"
    if not update_script.exists():
        print(f"[run_pipeline] 오류: update_status.py 없음 ({update_script})", file=sys.stderr)
        return False
    cmd = [sys.executable, str(update_script), agent_id, status, task]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
    except (OSError, FileNotFoundError) as e:
        print(f"[run_pipeline] 서브프로세스 실행 실패 ({agent_id}): {e}", file=sys.stderr)
        return False
    if result.returncode != 0:
        print(f"  [{agent_id}] 상태 변경 실패: {result.stderr.strip()}", file=sys.stderr)
        return False
    print(f"  {result.stdout.strip()}")
    return True


def topological_sort_phases(dag, team_nodes):
    """
    위상 정렬을 수행하여 phase 단위로 그룹화
    반환: list of list, 낮은 인덱스가 먼저 실행되는 phase
    """
    # 팀에 속한 노드만 필터링
    nodes = set(team_nodes)
    filtered_dag = {k: [v for v in deps if v in nodes] for k, deps in dag.items() if k in nodes}

    # 진입차수 계산
    in_degree = {n: 0 for n in nodes}
    for deps in filtered_dag.values():
        for d in deps:
            in_degree[d] += 1

    # 위상 정렬 (BFS)
    phases = []
    queue = deque([n for n in nodes if in_degree[n] == 0])
    remaining = set(nodes)

    while queue:
        current_phase = list(queue)
        phases.append(current_phase)
        queue = deque()
        for node in current_phase:
            remaining.discard(node)
            for dep in filtered_dag.get(node, []):
                in_degree[dep] -= 1
                if in_degree[dep] == 0:
                    queue.append(dep)

    if remaining:
        raise ValueError(f"순환 의존성 발견: {remaining}")

    return phases


def get_team_dag(team):
    """팀별 서브 DAG 생성"""
    nodes = TEAM_PIPELINE.get(team, [])
    return {k: [v for v in PIPELINE.get(k, []) if v in nodes] for k in nodes}


def run_phase(agents, phase_num, task_template, dry_run=False):
    """단일 phase 실행 (병렬)"""
    print(f"\n{'='*50}")
    print(f"  Phase {phase_num}: {', '.join(agents)}")
    print(f"{'='*50}")

    if dry_run:
        for ag in agents:
            print(f"  [DRY-RUN] {ag} -> working (테스트 모드)")
        return True

    success = True
    for ag in agents:
        task = task_template.get(ag, f"Phase {phase_num} 작업 중")
        ok = update_agent(ag, "working", task)
        if not ok:
            success = False
    return success


# ── 메인 ─────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="DAG 병렬 파이프라인 실행기")
    parser.add_argument("team", choices=["dev", "data", "pptx", "all"], help="실행할 팀")
    parser.add_argument("--dry-run", action="store_true", help="실제 실행 없이 계획만 출력")
    parser.add_argument("--phase", type=int, default=None, help="특정 phase만 실행 (1-based)")
    parser.add_argument("--qa-gate", action="store_true", default=True, help="각 phase 완료 후 QA 게이트 실행")
    args = parser.parse_args()

    teams = ["dev", "data", "pptx"] if args.team == "all" else [args.team]

    # Phase별 작업 내용 템플릿 (개발팀 기준)
    DEV_TASKS = {
        1: {
            "requirements": "라이브 사무실 기능 확장 요구사항 정의",
        },
        2: {
            "ux-designer":  "신규 패널 UI/UX 설계 및 인터랙션 정의",
            "dba":          "에이전트 활동 로그 스키마 설계 및 마이그레이션",
        },
        3: {
            "frontend":     "Phaser 3 신규 씬 및 모달 컴포넌트 개발",
            "backend":      "FastAPI 신규 엔드포인트 및 WebSocket 구현",
        },
        4: {
            "security":     "API 인증 및 CORS 정책 강화",
            "tester-unit":  "지시 기능 단위 테스트 작성",
        },
        5: {
            "tester-qa":    "E2E 테스트 시나리오 및 통합 검증",
        },
        6: {
            "devops":       "Docker화 및 배포 파이프라인 구축",
            "tech-writer":  "API 명세서 및 개발 가이드 작성",
        },
    }

    DATA_TASKS = {
        1: {"data-collector": "데이터 수집"},
        2: {"data-cleaner": "데이터 정제"},
        3: {"eda-analyst": "탐색적 분석", "gis-specialist": "공간 분석", "text-analyst": "텍스트 분석"},
        4: {"statistician": "통계 분석", "ml-engineer": "ML 모델링", "deep-learning": "딥러닝"},
        5: {"visualizer": "시각화"},
        6: {"reporter": "보고서 작성"},
    }

    PPTX_TASKS = {
        1: {"pptx-planner": "슬라이드 기획"},
        2: {"pptx-content": "콘텐츠 작성", "pptx-designer": "디자인"},
        3: {"pptx-builder": "PPTX 빌드"},
        4: {"pptx-reviewer": "검토"},
    }

    for team in teams:
        print(f"\n{'#'*60}")
        print(f"# 팀: {team.upper()} 파이프라인 실행")
        print(f"{'#'*60}")

        dag = get_team_dag(team)
        try:
            phases = topological_sort_phases(dag, TEAM_PIPELINE[team])
        except ValueError as e:
            print(f"[run_pipeline] DAG 위상 정렬 실패 (팀: {team}): {e}", file=sys.stderr)
            sys.exit(1)

        print(f"\n📋 총 {len(phases)}개 Phase, {sum(len(p) for p in phases)}개 에이전트")
        for i, phase in enumerate(phases, 1):
            marker = "병렬" if len(phase) > 1 else "순차"
            print(f"   Phase {i} [{marker}]: {', '.join(phase)}")

        if args.dry_run:
            print("\n🏃 DRY-RUN 모드: 실제 실행 없이 종료")
            continue

        # Phase 선택
        start_phase = (args.phase - 1) if args.phase is not None else 0
        end_phase = args.phase if args.phase is not None else len(phases)

        for i, phase in enumerate(phases[start_phase:end_phase], start=start_phase+1):
            task_map = {}
            if team == "dev":
                task_map = DEV_TASKS.get(i, {})
            elif team == "data":
                task_map = DATA_TASKS.get(i, {})
            elif team == "pptx":
                task_map = PPTX_TASKS.get(i, {})

            ok = run_phase(phase, i, task_map, dry_run=False)
            if not ok:
                print(f"\n❌ Phase {i} 실행 중 오류. 파이프라인 중단.")
                break

            # QA 게이트
            if args.qa_gate and i < len(phases):
                print(f"\n QA 게이트: Phase {i} 산출물 검증 중...")
                qa_script = SCRIPT_DIR / "qa_gate.py"
                if not qa_script.exists():
                    print(f"[run_pipeline] QA 게이트 건너뜀: qa_gate.py 없음", file=sys.stderr)
                else:
                    try:
                        qa_result = subprocess.run(
                            [sys.executable, str(qa_script), "--phase", str(i), "--team", team],
                            capture_output=True, text=True
                        )
                        print(qa_result.stdout)
                        if qa_result.returncode != 0:
                            print(f"[run_pipeline] QA 게이트 경고 (Phase {i}): {qa_result.stderr}", file=sys.stderr)
                            # QA 불통과 시에도 계속 진행 (경고만)
                    except (OSError, FileNotFoundError) as e:
                        print(f"[run_pipeline] QA 게이트 실행 실패 (Phase {i}): {e}", file=sys.stderr)

        print(f"\n✅ {team.upper()} 파이프라인 Phase {start_phase+1}~{end_phase} 실행 완료")


if __name__ == "__main__":
    main()
