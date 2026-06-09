"""
stamp.py — metaverse.html 의 METAVERSE_UPDATED 상수를 현재 시각으로 갱신합니다.
push 전에 자동 실행됩니다 (CLAUDE.md push 절차 참고).

사용법:
  python scripts/stamp.py
"""
import re
import sys
from datetime import datetime
from pathlib import Path

TARGET = Path(__file__).parent.parent / "metaverse.html"

def stamp():
    if not TARGET.exists():
        print(f"[stamp] 오류: 대상 파일 없음 ({TARGET})", file=sys.stderr)
        sys.exit(1)

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    try:
        text = TARGET.read_text(encoding="utf-8")
    except (IOError, OSError) as e:
        print(f"[stamp] 파일 읽기 실패 ({TARGET}): {e}", file=sys.stderr)
        sys.exit(1)

    pattern = r'(const METAVERSE_UPDATED = ")[^"]*(")'
    new_text, count = re.subn(pattern, rf'\g<1>{now}\g<2>', text)
    if count == 0:
        print("[stamp] ERROR: METAVERSE_UPDATED 상수를 찾지 못했습니다.", file=sys.stderr)
        sys.exit(1)

    try:
        TARGET.write_text(new_text, encoding="utf-8")
    except (IOError, OSError) as e:
        print(f"[stamp] 파일 쓰기 실패 (원본 보존됨) ({TARGET}): {e}", file=sys.stderr)
        sys.exit(1)

    print(f"[stamp] METAVERSE_UPDATED = {now}")

if __name__ == "__main__":
    stamp()
