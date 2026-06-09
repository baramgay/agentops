#!/usr/bin/env python3
"""
에이전트 협업 메모리 관리자
파이프라인 단계 간 산출물을 전달하고, 병렬 작업 동기화를 지원

사용법:
    # 산출물 기록 (작업 완료 시)
    python scripts/agent_collab.py handoff --from frontend --to tester-unit \
        --artifact "component/Button.tsx" --type "source"

    # 산출물 조회 (다음 단계 시작 시)
    python scripts/agent_collab.py artifacts --agent tester-unit

    # 동기화 포인트 설정 (병렬 작업 완료 대기)
    python scripts/agent_collab.py sync --phase 3 --team dev

    # 메모리 전체 보기
    python scripts/agent_collab.py list
"""

import json
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

SCRIPT_DIR = Path(__file__).parent
COLLAB_FILE = SCRIPT_DIR.parent / "agent_collab.json"

# ── 협업 메모리 구조 ─────────────────────────
#
# {
#   "sync_points": {
#     "dev:phase3": {"waiting": ["frontend", "backend"], "completed": [], "ready": false}
#   },
#   "artifacts": {
#     "frontend": [
#       {"type": "source", "path": "src/App.tsx", "desc": "메인 앱 컴포넌트", "ts": "2026-05-19T11:00:00"}
#     ]
#   },
#   "handoffs": [
#     {"from": "frontend", "to": "tester-unit", "artifact": "src/App.tsx", "ts": "2026-05-19T11:00:00"}
#   ]
# }


def load_collab():
    if COLLAB_FILE.exists():
        try:
            with open(COLLAB_FILE, encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"[agent_collab] {COLLAB_FILE.name} 손상 — 기본값으로 초기화", file=sys.stderr)
    return {"sync_points": {}, "artifacts": {}, "handoffs": []}


def save_collab(data):
    # defaultdict을 일반 dict로 변환
    data["artifacts"] = dict(data.get("artifacts", {}))
    with open(COLLAB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def handoff(from_agent, to_agent, artifact, artifact_type="file", description=""):
    """산출물 핸드오프 기록"""
    data = load_collab()
    ts = datetime.now().isoformat()

    entry = {
        "type": artifact_type,
        "path": artifact,
        "desc": description or f"{from_agent} → {to_agent} 핸드오프",
        "ts": ts,
        "to": to_agent,
    }
    data["artifacts"].setdefault(from_agent, []).append(entry)

    handoff_entry = {
        "from": from_agent,
        "to": to_agent,
        "artifact": artifact,
        "type": artifact_type,
        "ts": ts,
    }
    data["handoffs"].insert(0, handoff_entry)
    data["handoffs"] = data["handoffs"][:100]  # 최근 100개 유지

    save_collab(data)
    print(f"📦 핸드오프 기록: {from_agent} → {to_agent}")
    print(f"   산출물: {artifact} ({artifact_type})")


def list_artifacts(agent=None):
    """산출물 목록 조회"""
    data = load_collab()
    artifacts = data.get("artifacts", {})

    if agent:
        items = artifacts.get(agent, [])
        print(f"\n📁 {agent}의 산출물 ({len(items)}개)")
        for item in items:
            print(f"   [{item['type']}] {item['path']}")
            print(f"   설명: {item['desc']}")
            print(f"   시간: {item['ts']}")
            print()
    else:
        print(f"\n📁 전체 산출물 목록")
        for ag, items in artifacts.items():
            print(f"\n   [{ag}] {len(items)}개")
            for item in items[:3]:  # 최근 3개만
                print(f"      - {item['path']} ({item['type']})")


def create_sync_point(phase, team, agents):
    """동기화 포인트 생성"""
    data = load_collab()
    key = f"{team}:phase{phase}"

    data["sync_points"][key] = {
        "waiting": list(agents),
        "completed": [],
        "ready": False,
        "created": datetime.now().isoformat(),
    }
    save_collab(data)
    print(f"🔄 동기화 포인트 생성: {key}")
    print(f"   대기 에이전트: {', '.join(agents)}")


def complete_sync(agent, phase, team):
    """에이전트가 동기화 포인트 완료"""
    data = load_collab()
    key = f"{team}:phase{phase}"
    sp = data["sync_points"].get(key)

    if not sp:
        print(f"⚠️  동기화 포인트 {key}가 존재하지 않음")
        return False

    if agent in sp["waiting"]:
        sp["waiting"].remove(agent)
        sp["completed"].append(agent)
        print(f"✅ {agent} 동기화 완료 ({key})")

    if not sp["waiting"]:
        sp["ready"] = True
        print(f"\n🚀 {key} 모든 에이전트 동기화 완료 — 다음 Phase 진행 가능!")

    save_collab(data)
    return sp["ready"]


def check_sync(phase, team):
    """동기화 포인트 상태 확인"""
    data = load_collab()
    key = f"{team}:phase{phase}"
    sp = data["sync_points"].get(key)

    if not sp:
        print(f"⚠️  동기화 포인트 {key} 없음")
        return False

    print(f"\n🔄 동기화 포인트: {key}")
    print(f"   완료: {', '.join(sp['completed']) or '(없음)'}")
    print(f"   대기: {', '.join(sp['waiting']) or '(없음)'}")
    print(f"   상태: {'✅ 준비 완료' if sp['ready'] else '⏳ 대기 중'}")
    return sp["ready"]


def show_handoffs(limit=10):
    """최근 핸드오프 내역"""
    data = load_collab()
    handoffs = data.get("handoffs", [])[:limit]

    print(f"\n📦 최근 핸드오프 내역 ({len(handoffs)}개)")
    for h in handoffs:
        print(f"   [{h['ts'][:16]}] {h['from']} → {h['to']}: {h['artifact']}")


def main():
    parser = argparse.ArgumentParser(description="에이전트 협업 메모리 관리자")
    sub = parser.add_subparsers(dest="command", help="명령")

    # handoff
    p_handoff = sub.add_parser("handoff", help="산출물 핸드오프 기록")
    p_handoff.add_argument("--from", required=True, dest="from_agent")
    p_handoff.add_argument("--to", required=True)
    p_handoff.add_argument("--artifact", required=True)
    p_handoff.add_argument("--type", default="file")
    p_handoff.add_argument("--desc", default="")

    # artifacts
    p_artifacts = sub.add_parser("artifacts", help="산출물 조회")
    p_artifacts.add_argument("--agent", help="특정 에이전트 조회")

    # sync
    p_sync = sub.add_parser("sync", help="동기화 포인트 관리")
    p_sync.add_argument("--phase", type=int, required=True)
    p_sync.add_argument("--team", required=True)
    p_sync.add_argument("--agents", nargs="+", help="동기화 대상 에이전트 목록")
    p_sync.add_argument("--complete", help="완료한 에이전트 표시")
    p_sync.add_argument("--check", action="store_true", help="상태만 확인")

    # handoffs
    p_handoffs = sub.add_parser("handoffs", help="최근 핸드오프 내역")
    p_handoffs.add_argument("--limit", type=int, default=10)

    # list
    sub.add_parser("list", help="전체 협업 메모리 요약")

    args = parser.parse_args()

    if args.command == "handoff":
        handoff(args.from_agent, args.to, args.artifact, args.type, args.desc)

    elif args.command == "artifacts":
        list_artifacts(args.agent)

    elif args.command == "sync":
        if args.check:
            check_sync(args.phase, args.team)
        elif args.complete:
            complete_sync(args.complete, args.phase, args.team)
        elif args.agents:
            create_sync_point(args.phase, args.team, args.agents)
        else:
            check_sync(args.phase, args.team)

    elif args.command == "handoffs":
        show_handoffs(args.limit)

    elif args.command == "list":
        data = load_collab()
        print("\n📋 에이전트 협업 메모리 요약")
        print(f"   동기화 포인트: {len(data.get('sync_points', {}))}개")
        print(f"   산출물: {sum(len(v) for v in data.get('artifacts', {}).values())}개")
        print(f"   핸드오프: {len(data.get('handoffs', []))}개")
        for sp_key, sp in data.get("sync_points", {}).items():
            status = "✅" if sp["ready"] else "⏳"
            print(f"   {status} {sp_key}: 완료 {len(sp['completed'])}/{len(sp['completed'])+len(sp['waiting'])}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
