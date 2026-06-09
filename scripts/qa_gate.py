#!/usr/bin/env python3
"""
QA 게이트 관리자
각 파이프라인 Phase 완료 후 품질 체크포인트를 실행하고,
review/waiting/rework 상태를 관리

사용법:
    python scripts/qa_gate.py --phase 2 --team dev
    python scripts/qa_gate.py --agent tester-qa --review frontend
    python scripts/qa_gate.py --checklist requirements
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Windows 콘솔(cp949)에서 이모지·한글 출력 시 UnicodeEncodeError 방지
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# 공통 I/O 임포트
sys.path.insert(0, str(Path(__file__).parent))
from common_io import load_status, save_status

SCRIPT_DIR = Path(__file__).parent
STATUS_FILE = SCRIPT_DIR.parent / "agent_status.json"

# ── 품질 기준 정의 ───────────────────────────

QA_CHECKLISTS = {
    "requirements": {
        "description": "요구사항 분석 품질 기준",
        "items": [
            "기능 요구사항이 5W1H로 명확히 기술되었는가",
            "비기능 요구사항(성능, 보안, 확장성)이 정의되었는가",
            "유즈케이스 다이어그램 또는 사용자 스토리가 작성되었는가",
            "수용/거부 기준이 명확히 정의되었는가",
            "이해관계자 승인 서명이 있는가",
        ],
        "reviewer": "lead-dev",
        "min_score": 4,  # 5점 만점 중 4점 이상
    },
    "ux-designer": {
        "description": "UI/UX 설계 품질 기준",
        "items": [
            "와이어프레임이 모든 주요 화면을 커버하는가",
            "디자인 시스템(색상, 타이포그래피, 컴포넌트)이 정의되었는가",
            "사용자 흐름(UX flow)이 명확히 표현되었는가",
            "반응형/적응형 디자인이 고려되었는가",
            "접근성(a11y) 가이드라인이 반영되었는가",
        ],
        "reviewer": "lead-dev",
        "min_score": 4,
    },
    "dba": {
        "description": "DB 설계 품질 기준",
        "items": [
            "ER 다이어그램이 작성되었는가",
            "정규화가 3NF 이상으로 적용되었는가",
            "인덱스 전략이 문서화되었는가",
            "백업/복구 전략이 정의되었는가",
            "마이그레이션 스크립트가 버전 관리되는가",
        ],
        "reviewer": "lead-dev",
        "min_score": 4,
    },
    "frontend": {
        "description": "프론트엔드 개발 품질 기준",
        "items": [
            "코드 리뷰를 1회 이상 통과했는가",
            "단위 테스트 커버리지가 70% 이상인가",
            "린트(lint) 오류가 0건인가",
            "크로스 브라우저 테스트가 완료되었는가",
            "성능(Lighthouse) 점수가 80점 이상인가",
        ],
        "reviewer": "tester-unit",
        "min_score": 4,
    },
    "backend": {
        "description": "백엔드 개발 품질 기준",
        "items": [
            "API 문서(Swagger/OpenAPI)가 작성되었는가",
            "단위 테스트 커버리지가 70% 이상인가",
            "에러 핸들링 및 로깅이 구현되었는가",
            "DB 쿼리 성능이 EXPLAIN으로 검증되었는가",
            "보안 취약점 스캔을 통과했는가",
        ],
        "reviewer": "tester-unit",
        "min_score": 4,
    },
    "security": {
        "description": "보안 검토 품질 기준",
        "items": [
            "OWASP Top 10 점검표가 완료되었는가",
            "인증/인가 로직이 pentest를 통과했는가",
            "CORS 및 CSP 정책이 적절히 설정되었는가",
            "민감 데이터 암호화가 적용되었는가",
            "보안 이슈 트래킹이 문서화되었는가",
        ],
        "reviewer": "tester-qa",
        "min_score": 5,  # 보안은 만점
    },
    "tester-unit": {
        "description": "단위 테스트 품질 기준",
        "items": [
            "테스트 케이스가 요구사항 기반으로 작성되었는가",
            "모든 테스트가 CI에서 통과하는가",
            "모킹(mock)이 적절히 사용되었는가",
            "경계값 및 예외 케이스가 커버되었는가",
            "테스트 커버리지 리포트가 생성되었는가",
        ],
        "reviewer": "tester-qa",
        "min_score": 4,
    },
    "tester-qa": {
        "description": "통합 QA 품질 기준",
        "items": [
            "E2E 시나리오가 사용자 스토리 기반으로 작성되었는가",
            "회귀 테스트가 자동화되었는가",
            "버그 심각도 분류가 명확한가",
            "성능/부하 테스트가 완료되었는가",
            "릴리즈 노트가 작성되었는가",
        ],
        "reviewer": "lead-dev",
        "min_score": 4,
    },
    "devops": {
        "description": "DevOps 품질 기준",
        "items": [
            "CI/CD 파이프라인이 녹색 상태인가",
            "컨테이너 이미지가 취약점 스캔을 통과했는가",
            "모니터링/알림이 설정되었는가",
            "롤백 전략이 문서화되었는가",
            "인프라 코드(IaC)가 버전 관리되는가",
        ],
        "reviewer": "lead-dev",
        "min_score": 4,
    },
    "tech-writer": {
        "description": "기술 문서 품질 기준",
        "items": [
            "API 문서가 최신 상태를 반영하는가",
            "사용자 가이드에 스크린샷이 포함되었는가",
            "릴리즈 노트에 Breaking Change가 명시되었는가",
            "문서가 Markdown/HTML 형식으로 빌드되는가",
            "오탈자 및 링크 깨짐이 없는가",
        ],
        "reviewer": "lead-dev",
        "min_score": 4,
    },
    "realty-analyst": {
        "description": "부동산동향 월보 품질 기준",
        "items": [
            "수집 데이터가 체크리스트 기준 전항목 충족되었는가",
            "인사이트 서술에 단정적 방향 표현(오른다/내린다 등)이 없는가",
            "이슈 시군 세부 분석 섹션이 포함되었는가",
            "lead-data 2차 검토가 완료되었는가",
            "차트 라벨·단위·시군명 표기 검증이 완료되었는가",
        ],
        "reviewer": "lead-data",
        "min_score": 5,
    },
}

# ── Phase → 체크리스트 매핑 ──────────────────

PHASE_CHECKS = {
    "dev": {
        1: ["requirements"],
        2: ["ux-designer", "dba"],
        3: ["frontend", "backend"],
        4: ["security", "tester-unit"],
        5: ["tester-qa"],
        6: ["devops", "tech-writer"],
    },
    "data": {
        1: ["data-collector"],
        2: ["data-cleaner"],
        3: ["eda-analyst", "gis-specialist", "text-analyst"],
        4: ["statistician", "ml-engineer", "deep-learning"],
        5: ["visualizer"],
        6: ["reporter"],
    },
    "pptx": {
        1: ["pptx-planner"],
        2: ["pptx-content", "pptx-designer"],
        3: ["pptx-builder"],
        4: ["pptx-reviewer"],
    },
}


def run_checklist(agent_id, auto_pass=False):
    """체크리스트를 대화형으로 실행"""
    check = QA_CHECKLISTS.get(agent_id)
    if not check:
        print(f"⚠️  [{agent_id}]에 대한 QA 체크리스트가 정의되지 않음")
        return None

    print(f"\n{'='*50}")
    print(f"  QA 게이트: {agent_id}")
    print(f"  {check['description']}")
    print(f"  검토자: {check['reviewer']} | 통과 기준: {check['min_score']}/5")
    print(f"{'='*50}")

    score = 0
    for i, item in enumerate(check["items"], 1):
        print(f"  {i}. {item}")
        if auto_pass:
            score += 1
            print(f"     ✅ PASS (auto)")
        else:
            # 수동 검증 모드
            try:
                ans = input("     통과? (y/n/스킵=Enter): ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                ans = ""
            if ans in ("y", "yes", "ㅛ"):
                score += 1
                print(f"     ✅ PASS")
            else:
                print(f"     ❌ FAIL")

    passed = score >= check["min_score"]
    status_icon = "✅" if passed else "❌"
    print(f"\n  {status_icon} 총점: {score}/5 — {'통과' if passed else '불통과'}")

    return {"agent_id": agent_id, "score": score, "passed": passed, "reviewer": check["reviewer"]}


def set_review_status(agent_id, reviewer_id, result):
    """검토 결과에 따라 review 상태 설정"""
    data = load_status()

    if agent_id not in data["agents"]:
        data["agents"][agent_id] = {"status": "idle", "task": ""}
    if result["passed"]:
        # 통과 → done
        data["agents"][agent_id]["status"] = "done"
        data["agents"][agent_id]["task"] = f"QA 통과 ({result['score']}/5)"
        label = "완료"
    else:
        # 불통과 → review (재작업 필요)
        data["agents"][agent_id]["status"] = "review"
        data["agents"][agent_id]["task"] = f"QA 불통과 ({result['score']}/5) — 재작업 필요"
        label = "검토 중"

    # 검토자 로그
    now = datetime.now().strftime("%H:%M:%S")
    log_entry = {
        "time": now,
        "agent": reviewer_id,
        "status": "review" if result["passed"] else "waiting",
        "label": label,
        "task": f"{agent_id} QA 검토 결과: {result['score']}/5",
    }
    data.setdefault("log", []).insert(0, log_entry)
    data["log"] = data["log"][:30]

    save_status(data)
    print(f"  📝 {agent_id} 상태 → {data['agents'][agent_id]['status']}")


def main():
    parser = argparse.ArgumentParser(description="QA 품질 게이트 관리자")
    parser.add_argument("--phase", type=int, help="검증할 Phase 번호")
    parser.add_argument("--team", default="dev", help="팀 이름")
    parser.add_argument("--agent", help="개별 에이전트 QA 실행")
    parser.add_argument("--review", help="검토자가 지정된 에이전트 검토")
    parser.add_argument("--auto-pass", action="store_true", help="모든 항목 자동 통과 (데모용)")
    args = parser.parse_args()

    if args.agent:
        result = run_checklist(args.agent, auto_pass=args.auto_pass)
        if result:
            reviewer = QA_CHECKLISTS[args.agent]["reviewer"]
            set_review_status(args.agent, reviewer, result)
        return

    if args.phase:
        team_checks = PHASE_CHECKS.get(args.team, {})
        agents = team_checks.get(args.phase, [])
        if not agents:
            print(f"⚠️  Phase {args.phase}에 대한 체크리스트가 없음")
            return

        print(f"\n🔍 QA 게이트: {args.team.upper()} Phase {args.phase}")
        all_passed = True
        for ag in agents:
            result = run_checklist(ag, auto_pass=args.auto_pass)
            if result:
                reviewer = QA_CHECKLISTS[ag]["reviewer"]
                set_review_status(ag, reviewer, result)
                if not result["passed"]:
                    all_passed = False
            else:
                all_passed = False

        if all_passed:
            print(f"\n✅ Phase {args.phase} QA 게이트 전원 통과 — 다음 Phase 진행 가능")
        else:
            print(f"\n⚠️  Phase {args.phase} QA 게이트 일부 불통과 — 재작업 후 재검토 필요")
        return

    if args.review:
        # 수동 검토 모드
        print(f"📝 {args.review} 수동 검토 모드 (미구현)")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
