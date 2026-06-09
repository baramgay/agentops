"""
압축 임박 자동 지식저장 유도 — Claude Code UserPromptSubmit 훅용. 토큰 0(훅 자체).

훅은 LLM을 직접 못 돌린다. 대신 컨텍스트(=transcript)가 임계 이상 커지면
stdout으로 모델에게 "/지식저장 먼저 실행" 지시를 주입한다(UserPromptSubmit stdout→컨텍스트).
→ 자동 압축이 오기 전에 모델이 스스로 핵심을 위키에 증류하게 유도.

- 임계 초과분만큼 1회씩만 주입(마커로 추적) → 매 턴 반복 안 함.
- 임계: env AGENTS_DISTILL_THRESHOLD_MB (기본 60MB transcript).
- 실패는 무음 — 사용자 입력 흐름을 절대 막지 않음.
"""
import sys
import os
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MARKER = REPO / "logs" / ".distill_marker"
THRESHOLD = int(float(os.environ.get("AGENTS_DISTILL_THRESHOLD_MB", "2")) * 1024 * 1024)

NUDGE = (
    "⚠️ [자동 알림] 컨텍스트가 커져 곧 자동 압축될 수 있습니다. "
    "압축으로 세부 맥락이 사라지기 전에, **사용자 요청을 처리하기 직전에 `/지식저장`을 1회 실행**해 "
    "이번 대화의 프로젝트별 핵심(결정·해결책·함정)을 위키에 증류·저장하세요. "
    "이미 이번 구간에서 저장했다면 건너뛰어도 됩니다. (이 알림은 자동 주입됨)"
)


def main():
    # stdin(JSON) 비우지 않음 — read()가 멈출 수 있어 아예 안 읽음. transcript는 인자/탐색으로.
    transcript = ""
    try:
        # UserPromptSubmit는 stdin JSON에 transcript_path를 주지만, 안전하게 비차단 읽기
        if not sys.stdin.isatty():
            import select  # POSIX 전용 — Windows면 예외 → 폴백
            try:
                r, _, _ = select.select([sys.stdin], [], [], 0.05)
                if r:
                    data = json.loads(sys.stdin.read() or "{}")
                    transcript = data.get("transcript_path", "")
            except Exception:
                transcript = ""
    except Exception:
        transcript = ""

    # transcript 경로를 못 얻으면 최신 프로젝트 transcript로 폴백
    if not transcript or not os.path.exists(transcript):
        try:
            proj = Path.home() / ".claude" / "projects"
            cands = list(proj.rglob("*.jsonl"))
            if cands:
                transcript = str(max(cands, key=lambda p: p.stat().st_mtime))
        except Exception:
            return

    try:
        size = os.path.getsize(transcript)
    except Exception:
        return

    last = 0
    try:
        if MARKER.exists():
            last = int(MARKER.read_text().strip() or "0")
    except Exception:
        last = 0

    if size - last >= THRESHOLD:
        try:
            MARKER.parent.mkdir(parents=True, exist_ok=True)
            MARKER.write_text(str(size))
        except Exception:
            pass
        print(NUDGE)  # UserPromptSubmit: stdout → 모델 컨텍스트로 주입


if __name__ == "__main__":
    main()
