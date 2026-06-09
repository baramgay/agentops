"""
다중 PC 지식 동기화 훅 설치기 — 각 PC에서 1회 실행 (멱등, 경로 자동).

settings.json은 머신별 설정이라 git 동기화에서 제외되므로,
새 PC에서 이 스크립트를 1회 실행해 ~/.claude/settings.json에
SessionStart(pull)·SessionEnd(capture+push) 훅을 주입한다.

  python scripts/install_sync_hooks.py

핵심: 이 스크립트가 있는 위치에서 **그 PC의 실제 레포 경로**를 계산해 훅에 넣는다.
      → PC마다 경로가 달라도 동작 (AGENTS_HOME, D:/work/agents 등 무관).
- python 인터프리터도 절대경로(sys.executable)로 박아 PATH 의존 제거.
- 멱등: 우리 스크립트(wiki_git_sync/session_capture)를 가리키는 기존 훅은 제거 후 재주입
  → 경로가 바뀌어도 재실행하면 자동 교정. 다른 훅은 보존. 실행 전 백업.
"""
import sys
import json
import shutil
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

SETTINGS = Path.home() / ".claude" / "settings.json"
REPO = Path(__file__).resolve().parent.parent          # 이 PC의 실제 레포 경로
PY = sys.executable                                     # 이 PC의 실제 python 경로
SCRIPTS = REPO / "scripts"

OUR_SCRIPTS = ("wiki_git_sync.py", "session_capture.py", "distill_nudge.py")  # 멱등 판별용


def _cmd(script: str, arg: str = "") -> str:
    # 경로에 공백/한글이 있어도 안전하게 따옴표 처리
    c = f'"{PY}" "{SCRIPTS / script}"'
    return f"{c} {arg}".strip()


# (이벤트 → 주입할 커맨드 목록)
WANT = {
    "SessionStart": [_cmd("wiki_git_sync.py", "pull")],
    "SessionEnd":   [_cmd("session_capture.py"), _cmd("wiki_git_sync.py", "push")],
    # 압축 직전 — 사실 기록을 위키에 먼저 저장(자동 압축에도 유실 방지, 토큰0)
    "PreCompact":   [_cmd("session_capture.py")],
    # 컨텍스트 임계 초과 시 모델에게 "/지식저장 먼저" 지시 주입(자동 증류 유도)
    "UserPromptSubmit": [_cmd("distill_nudge.py")],
}


def _is_ours(command: str) -> bool:
    return any(s in command for s in OUR_SCRIPTS)


def _strip_our_hooks(groups: list) -> list:
    """우리 스크립트를 가리키는 훅 제거(경로 교정용). 빈 그룹은 삭제. 타 훅 보존."""
    out = []
    for grp in groups or []:
        kept = [h for h in grp.get("hooks", [])
                if not (h.get("type") == "command" and _is_ours(h.get("command", "")))]
        if kept:
            ng = dict(grp)
            ng["hooks"] = kept
            out.append(ng)
        elif grp.get("hooks") and not any(_is_ours(h.get("command", "")) for h in grp["hooks"]):
            out.append(grp)
    return out


def main():
    if SETTINGS.exists():
        data = json.loads(SETTINGS.read_text(encoding="utf-8"))
        shutil.copy2(SETTINGS, SETTINGS.with_name(f"settings.json.bak_{datetime.now():%Y%m%d_%H%M%S}"))
    else:
        SETTINGS.parent.mkdir(parents=True, exist_ok=True)
        data = {}

    hooks = data.setdefault("hooks", {})
    for event, cmds in WANT.items():
        groups = _strip_our_hooks(hooks.get(event, []))   # 기존 우리 훅 제거(교정)
        groups.append({"hooks": [{"type": "command", "command": c} for c in cmds]})
        hooks[event] = groups

    SETTINGS.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ 동기화 훅 주입/교정 완료 → {SETTINGS}")
    print(f"   레포: {REPO}")
    print(f"   SessionStart=pull / SessionEnd=capture+push (이 PC 경로로 설정됨)")


if __name__ == "__main__":
    main()
