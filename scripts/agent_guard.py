"""
에이전트 가드 — Claude Code PreToolUse 훅용.

Write/Edit 도구 실행 전, agent_status.json에 working 상태인 에이전트가
있는지 확인한다. 없으면 exit 2로 도구를 차단한다.

원칙: 규칙보다 강제 (Harness Engineering 2원칙)
  "하지 마"라고 말하지 않는다. 시스템적으로 못 하게 만든다.

예외 (항상 허용):
  - wiki/notes/<type>/ 하위 폴더 : PreCompact 자동저장 및 지식저장은 선언 없이 가능
    (단, wiki/notes/ 루트 직접 쓰기는 차단 — 반드시 type 하위 폴더에 저장)
  - agent_status.json : update_status.py가 직접 쓰는 파일
  - logs/             : 로그 파일은 비작업성
"""
import sys
import json
from datetime import datetime
from pathlib import Path

STATUS_FILE = Path(__file__).resolve().parent.parent / "agent_status.json"

# working 선언 후 이 시간이 지나면 스테일로 간주 (분)
STALE_MINUTES = 120

# 이 경로들은 working 선언 없이도 Write/Edit 허용
EXEMPT_FRAGMENTS = [
    "wiki/notes/",
    "wiki\\notes\\",
    "agent_status.json",
    "/logs/",
    "\\logs\\",
    "sessions/",
    "sessions\\",
    ".claude/memory/",
    ".claude\\memory\\",
]


def parse_ts(ts_str: str):
    """ISO 타임스탬프 → datetime (tz-naive UTC 기준)."""
    try:
        ts_str = ts_str.replace("+09:00", "").replace("Z", "").strip()
        return datetime.fromisoformat(ts_str)
    except Exception:
        return None


def any_agent_working() -> tuple[bool, str]:
    """스테일하지 않은 working 에이전트 존재 여부와 agent_id 반환."""
    try:
        data = json.loads(STATUS_FILE.read_text(encoding="utf-8"))
        now = datetime.now()
        for agent_id, info in data.get("agents", {}).items():
            if info.get("status") != "working":
                continue
            ts = parse_ts(info.get("updated", ""))
            if ts is None:
                continue
            age_min = (now - ts).total_seconds() / 60
            if age_min <= STALE_MINUTES:
                return True, agent_id
    except Exception:
        pass
    return False, ""


def is_wiki_notes_root(file_path: str) -> bool:
    """wiki/notes/ 루트에 직접 쓰는 경우 True (하위 폴더면 False).

    판단 기준: wiki/notes/ 이후 경로에 디렉터리 구분자가 없으면 루트 직접 저장.
    예) wiki/notes/feedback-test.md        → True  (차단)
        wiki/notes/feedback/feedback-test.md → False (허용)
    """
    fp = file_path.replace("\\", "/")
    marker = "wiki/notes/"
    idx = fp.find(marker)
    if idx == -1:
        return False
    remainder = fp[idx + len(marker):]  # e.g. "feedback-test.md" or "feedback/feedback-test.md"
    return "/" not in remainder  # 슬래시 없음 = 루트 직접 저장


def is_exempt(file_path: str) -> bool:
    # wiki/notes/ 루트 직접 쓰기는 면제 불가 (아래 main에서 별도 차단)
    for frag in EXEMPT_FRAGMENTS:
        if frag in file_path:
            return True
    return False


def main():
    try:
        data = json.load(sys.stdin) if not sys.stdin.isatty() else {}
    except Exception:
        sys.exit(0)

    tool = data.get("tool_name", "")
    if tool not in ("Write", "Edit"):
        sys.exit(0)

    file_path = str(data.get("tool_input", {}).get("file_path", ""))

    # wiki/notes/ 루트 직접 쓰기 차단 (working 선언 여부 무관)
    if is_wiki_notes_root(file_path):
        print(
            "🚫 [wiki 가드] wiki/notes/ 루트에 직접 저장할 수 없습니다.\n\n"
            "반드시 type 하위 폴더에 저장하세요:\n"
            "  feedback/   → 행동 교정·확인된 접근법\n"
            "  project/    → 프로젝트 상태·결정\n"
            "  reference/  → 외부 자료·도구 참조\n"
            "  method/     → 재사용 가능한 방법론\n"
            "  agents/     → 에이전트 role·memory (자동 관리)\n\n"
            f"올바른 경로 예시: wiki/notes/feedback/{Path(file_path).name}",
            file=sys.stderr,
        )
        sys.exit(2)

    if is_exempt(file_path):
        sys.exit(0)

    working, agent_id = any_agent_working()
    if working:
        sys.exit(0)  # 정상: 작업 선언됨

    # 차단
    print(
        "🚫 [에이전트 가드] 파일 수정이 차단됐습니다.\n\n"
        "모든 작업은 에이전트 시스템을 거쳐야 합니다. 먼저 담당 에이전트를 선언하세요:\n\n"
        "  python AGENTS_HOME\\scripts\\update_status.py <agent_id> working \"<작업내용>\"\n\n"
        "담당 에이전트 → AGENTS_HOME\\CLAUDE.md 빠른 참조표\n"
        f"대상 파일: {file_path}",
        file=sys.stderr,
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
