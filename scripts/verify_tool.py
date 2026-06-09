"""
검증 도구 — Claude Code PostToolUse 훅용 (Bash 대상).

Bash 명령 실행 후 exit code가 0이 아닌 경우 경고를 주입한다.
모델이 실패를 인지하고 자동 수정하도록 유도한다.

원칙: 검증 가능한 환경 (Harness Engineering 4원칙)
  AI가 직접 테스트/로그/메트릭을 확인할 수 있어야 한다.

무음 처리:
  - git 명령의 경고(exit 1)처럼 정상 범위 exit는 노이즈가 많아 제외
  - python -c 단순 스크립트는 제외
  - 실패가 명백한 exit 2+ 만 경고
"""
import sys
import json


SKIP_PREFIXES = (
    "python -c",
    "echo ",
    "ls ",
    "cat ",
    "head ",
    "tail ",
    "wc ",
)


def main():
    try:
        data = json.load(sys.stdin) if not sys.stdin.isatty() else {}
    except Exception:
        sys.exit(0)

    tool = data.get("tool_name", "")
    if tool != "Bash":
        sys.exit(0)

    exit_code = data.get("tool_response", {}).get("exit_code")
    if exit_code is None or exit_code == 0:
        sys.exit(0)

    command = str(data.get("tool_input", {}).get("command", ""))

    # 노이즈성 명령 제외
    for prefix in SKIP_PREFIXES:
        if command.strip().startswith(prefix):
            sys.exit(0)

    # git 관련은 exit 1도 정보성이 많아 exit 2+만 경고
    if "git " in command and exit_code == 1:
        sys.exit(0)

    print(
        f"⚠️ [검증 실패] Bash exit {exit_code}\n"
        f"명령: {command[:120]}{'...' if len(command) > 120 else ''}\n"
        "실패 원인을 확인하고 수정하세요. 'done' 선언 전 반드시 성공을 확인합니다.",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
