"""
PreCompact 훅 — compact 발생 기록 및 경고 플래그 생성.

[중요] PreCompact 훅의 stdout은 압축 LLM에 주입되지 않는다 (Claude Code 사양).
따라서 LLM에 "저장하라" 지시하는 방식은 효과 없음.

대신:
1. hooks_log에 PreCompact 이벤트 기록 (진단용)
2. .compact_pending 플래그 파일 생성
   → SessionStart의 token_health.py가 감지하여 "지식 저장 없이 compact 발생" 경고 표시
"""
import sys
import json
import datetime
from pathlib import Path

AGENTS_ROOT = Path(__file__).resolve().parent.parent
HOOKS_LOG = Path.home() / ".claude" / "hooks_log.txt"
FLAG_FILE = AGENTS_ROOT / ".compact_pending"


def main():
    try:
        if not sys.stdin.isatty():
            data = json.loads(sys.stdin.read() or "{}")
        else:
            data = {}
    except Exception:
        data = {}

    transcript_path = data.get("transcript_path", "")
    compaction_reason = data.get("compaction_reason", "unknown")
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 1. hooks_log 기록
    try:
        with open(HOOKS_LOG, "a", encoding="utf-8") as f:
            f.write(f"[PreCompact] {now} reason={compaction_reason}\n")
    except Exception:
        pass

    # 2. 플래그 파일 생성 (SessionStart에서 감지)
    try:
        FLAG_FILE.write_text(
            json.dumps({
                "ts": now,
                "reason": compaction_reason,
                "transcript": transcript_path,
            }, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception:
        pass


if __name__ == "__main__":
    main()
