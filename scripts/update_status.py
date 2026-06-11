"""
Agent status update utility

Usage:
  basic:  python scripts/update_status.py [agent_id] [status] "[task]"
  learn:  python scripts/update_status.py [agent_id] done "[task]" --learn "[memo]"

status values:
  working  - in progress (green)
  review   - under review (yellow)
  waiting  - waiting (orange)
  done     - complete (returns to idle)
  idle     - idle

examples:
  python scripts/update_status.py data-collector working "Collecting population data"
  python scripts/update_status.py data-collector done "Collected population data (3,842 records)"
  python scripts/update_status.py reporter done "Report complete" --learn "4 bullets per section fits one page"
"""

import sys
import json
import os
import argparse
from datetime import datetime
from pathlib import Path

# Optional argcomplete support for shell tab-completion
try:
    import argcomplete
    HAS_ARGCOMPLETE = True
except ImportError:
    HAS_ARGCOMPLETE = False

# Windows 콘솔(cp949)에서 이모지·한글 출력 시 UnicodeEncodeError 방지
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# 공통 I/O 임포트
sys.path.insert(0, str(Path(__file__).parent))
from common_io import load_status, save_status, find_status_file


def append_work_log(agent_id, status, content):
    """감사 로그: AGENTS_HOME\\work_log.jsonl 에 상태 변경 기록을 추가한다."""
    try:
        log_path = Path(__file__).parent.parent / 'work_log.jsonl'
        entry = {
            "ts": datetime.now().isoformat(),
            "agent_id": agent_id,
            "status": status,
            "content": content,
            "machine": os.environ.get('COMPUTERNAME', 'unknown'),
        }
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    except Exception:
        pass  # 로그 실패해도 메인 기능에 영향 없음

VALID_STATUSES = {"working", "review", "waiting", "idle", "done"}
STATUS_LABEL = {
    "working": "작업 시작",
    "review": "검토 중",
    "waiting": "대기",
    "done": "완료",
    "idle": "유휴",
}
STATUS_ICON = {
    "working": "🟢",
    "review": "🟡",
    "waiting": "🟠",
    "done": "✅",
    "idle": "⚪",
}


def get_agent_ids():
    """Return list of valid agent IDs from agent_status.json for shell completion."""
    try:
        find_status_file()
        data = load_status()
        return list(data.get("agents", {}).keys())
    except Exception:
        return []


def main():
    # Build argparse parser with dynamic agent ID choices for completion
    _agent_ids = get_agent_ids()

    parser = argparse.ArgumentParser(
        description="Update agent status in the agentops system.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "status values:\n"
            "  working  in progress\n"
            "  review   under review\n"
            "  waiting  waiting on dependency\n"
            "  done     complete (transitions to idle)\n"
            "  idle     idle / standby\n\n"
            "examples:\n"
            "  python scripts/update_status.py eda-analyst working \"Analyzing Q1 data\"\n"
            "  python scripts/update_status.py eda-analyst done \"Analysis complete\"\n"
            "  python scripts/update_status.py reporter done \"Report done\" --learn \"4 bullets fits one page\""
        ),
    )
    parser.add_argument(
        "agent_id",
        choices=_agent_ids if _agent_ids else None,
        metavar="agent_id",
        help="Agent ID (e.g. orchestrator, backend, eda-analyst). Tab-complete for full list.",
    )
    parser.add_argument(
        "status",
        choices=["working", "review", "waiting", "done", "idle"],
        help="New status for the agent.",
    )
    parser.add_argument(
        "task",
        nargs="?",
        default="",
        help="Task description (optional, quoted string).",
    )
    parser.add_argument(
        "--learn",
        metavar="MEMO",
        help="Learning memo to append to agent memory.md (used with status=done).",
    )

    # Register completion handler before parsing — no-op when argcomplete is absent
    if HAS_ARGCOMPLETE:
        argcomplete.autocomplete(parser)

    args = parser.parse_args()
    agent_id = args.agent_id
    status = args.status.lower()
    task = args.task or ""
    learn_text = args.learn

    if status not in VALID_STATUSES:
        print(f"Error: status must be one of {VALID_STATUSES}")
        sys.exit(1)

    # Ensure status file exists
    find_status_file()

    data = load_status()

    if agent_id not in data.get("agents", {}):
        print(f"Error: unknown agent ID '{agent_id}'")
        sys.exit(1)

    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    # done → idle 처리
    actual_status = "idle" if status == "done" else status
    data["agents"][agent_id] = {
        "status": actual_status,
        "task": task if actual_status != "idle" else "",
        "updated": now,
    }
    data["updated"] = now

    # 로그 추가 (최근 30개 유지)
    log_entry = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "agent": agent_id,
        "status": status,
        "label": STATUS_LABEL.get(status, status),
        "task": task,
    }
    data.setdefault("log", []).insert(0, log_entry)
    data["log"] = data["log"][:30]

    # Process --learn option (only when status is done)
    if learn_text and status == 'done':
        import re
        hanja_re = re.compile(r'[㐀-䶿一-鿿]')
        if any(hanja_re.match(ch) for ch in learn_text):
            print(f'[오류] --learn 본문에 한자 발견 — memory.md 미수정')
            sys.exit(1)

        # 위키 정본 우선 → agents/ 폴백 (wiki = agents/wiki/)
        _wiki_mem = Path(__file__).parent.parent / 'wiki' / 'notes' / 'agents' / f'agent-{agent_id}-memory.md'
        mem_path = _wiki_mem if _wiki_mem.exists() else Path(__file__).parent.parent / agent_id / 'memory.md'
        if not mem_path.exists():
            print(f'[오류] {mem_path} 없음 — memory.md 미수정')
            sys.exit(1)

        content = mem_path.read_text(encoding='utf-8')

        # 중복 체크: 동일 learn_text가 이미 memory.md에 있으면 건너뜀
        learn_text_stripped = learn_text.strip()
        if learn_text_stripped and learn_text_stripped in content:
            print(f'  [건너뜀] [{agent_id}] 동일 학습 패턴이 memory.md에 이미 존재 — 중복 추가 방지')
        else:
            # 패턴 자동 분류 (카테고리별 태그)
            _cat = '기타'
            _lower = learn_text_stripped.lower()
            if any(k in _lower for k in ['버그', '오류', '수정', '수정', 'fix', 'error', '예외']):
                _cat = '버그수정'
            elif any(k in _lower for k in ['신규', '추가', '새로', '기능', 'add', 'new', '구현']):
                _cat = '신규기능'
            elif any(k in _lower for k in ['문서', '주석', '가이드', '매뉴얼', 'doc', 'readme']):
                _cat = '문서화'
            elif any(k in _lower for k in ['리팩', '정리', '개선', '최적화', 'refactor', 'clean']):
                _cat = '개선'
            elif any(k in _lower for k in ['테스트', '검증', '확인', 'test', 'qa', '통과']):
                _cat = '테스트'

            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
            title_part = (task or '학습')[:40].strip()
            entry = f'\n### {timestamp} — [{_cat}] {title_part}\n{learn_text}\n'

            marker = '<!-- 작업 완료 후 새로운 패턴·실수·해결책을 여기에 자동 축적 -->'
            if marker in content:
                new_content = content.replace(marker, marker + entry, 1)
            else:
                # 섹션 없으면 끝에 신규 추가
                if not content.endswith('\n'):
                    content += '\n'
                new_content = content + f'\n---\n## 학습 예정 패턴\n{marker}{entry}'

            mem_path.write_text(new_content, encoding='utf-8')
            print(f'  [{agent_id}] memory.md 패턴 축적 [{_cat}]: {title_part}')

    save_status(data)

    # 감사 로그 기록
    append_work_log(agent_id, status, task)

    # GNI-N 참조 시 이슈 자동 전이 (서버 켜진 경우만, 비차단)
    import re as _re
    _gni = _re.search(r'GNI-\d+', task or '')
    if _gni:
        try:
            import urllib.request as _ur
            _new_status = {"working": "in_progress", "review": "in_review", "done": "done"}.get(status, "")
            if _new_status:
                _issue_id = _gni.group()
                # 완료·취소된 이슈는 자동 reopen 하지 않음 (서버 핸들러 가드와 동일 동작)
                _cur = None
                try:
                    with _ur.urlopen(f"http://127.0.0.1:8765/api/issues/{_issue_id}", timeout=2) as _r:
                        _cur = json.loads(_r.read().decode()).get("status")
                except Exception:
                    _cur = None  # 조회 실패 시 전이 진행 (서버 미실행 또는 신규 이슈)
                if _cur not in ("done", "cancelled"):
                    _req = _ur.Request(
                        f"http://127.0.0.1:8765/api/issues/{_issue_id}",
                        data=json.dumps({"status": _new_status}).encode(), method="PATCH",
                        headers={"Content-Type": "application/json"},
                    )
                    _ur.urlopen(_req, timeout=2)
        except Exception:
            pass  # 서버 미실행 시 무음 처리

    # mem0 장기 메모리 — done 시 비동기로 작업 경험 저장 (모델 로드 오버헤드 분리)
    if status == "done" and task:
        try:
            import subprocess
            script = (
                "import sys; sys.path.insert(0,r'" + str(Path(__file__).parent) + "');"
                "from mem0_client import add_experience;"
                "add_experience('" + agent_id.replace("'", "") + "', '''" + task.replace("'", "").replace("\n", " ") + " [" + agent_id + "]''')"
            )
            subprocess.Popen([sys.executable, "-c", script],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

    icon = STATUS_ICON.get(status, "·")
    print(f"{icon} [{agent_id}] {STATUS_LABEL.get(status, status)}: {task}")

    # done 시 위키 강화 루프 힌트 (리드 에이전트는 MoC 참조 안내 포함)
    if status == "done" and not learn_text:
        is_lead = agent_id in ("orchestrator", "lead-data", "lead-dev", "lead-pptx")
        if is_lead:
            print(f"  💡 [강화루프] 이번 작업에서 새 패턴·결정이 있었다면:")
            print(f"     → wiki/notes/<type>/<슬러그>.md 업데이트 (없으면 skip)")
            print(f"     → 있다면: python update_status.py {agent_id} done \"...\" --learn \"패턴 요약\"")
        else:
            # 담당 에이전트는 도메인 힌트 포함
            _domain_hint = {
                "frontend": "agents시스템·이음지도", "backend": "agents시스템",
                "eda-analyst": "경남부동산·이음지도", "reporter": "경남부동산",
                "gis-specialist": "공공데이터소스", "realty-analyst": "경남부동산",
                "statworkbench": "누리스탯", "visualizer": "경남부동산",
            }.get(agent_id, "")
            hint = f" (도메인: {_domain_hint})" if _domain_hint else ""
            print(f"  💡 [강화루프] 새 패턴 있으면: --learn \"한 줄 요약\"{hint}")


if __name__ == "__main__":
    main()
