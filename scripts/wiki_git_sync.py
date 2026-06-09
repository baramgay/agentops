"""
지식 파일 다중 PC 동기화 헬퍼 — Claude Code SessionStart/SessionEnd 훅용. 토큰 0.

  pull  : git pull (세션 시작 — 다른 PC 지식 받기)
  push  : 지식 파일(wiki/·memory·role)만 커밋→pull→push (세션 종료 — 내 지식 공유)

핵심 안전장치 (세션을 절대 막지 않음):
- 훅이 호출하면 즉시 백그라운드 워커를 분리(detached) 실행하고 반환 → 세션 0ms 대기.
- GIT_TERMINAL_PROMPT=0 → 자격증명/네트워크 대기로 멈추지 않고 즉시 실패.
- 모든 git 호출 timeout, 실패는 logs/knowledge_sync.log 에만 기록(컨텍스트 미주입).
- 코드(scripts/ 등)는 절대 자동 커밋 안 함 — 지식 파일만.
"""
import sys
import os
import subprocess
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO = Path(__file__).resolve().parent.parent
LOG = REPO / "logs" / "knowledge_sync.log"
KNOWLEDGE_PATHSPEC = [
    "wiki/MoC",
    "wiki/notes/feedback",
    "wiki/notes/method",
    "wiki/notes/project",
    "wiki/notes/reference",
    "wiki/notes/agents",
    "wiki/notes/sessions",
    "wiki/00_홈.md",
    "wiki/00_규칙_위키사용법.md",
    "agents/*/memory.md",
    "agents/*/role.md",
]

# git이 자격증명/프롬프트로 멈추지 않게
_GIT_ENV = dict(os.environ, GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="never")


def _log(msg: str):
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}\n")
    except Exception:
        pass


def _git(args, timeout=30):
    try:
        r = subprocess.run(["git"] + args, cwd=str(REPO), env=_GIT_ENV,
                           capture_output=True, text=True, timeout=timeout)
        return r.returncode, ((r.stdout or "") + (r.stderr or "")).strip()
    except subprocess.TimeoutExpired:
        return 1, "timeout"
    except Exception as e:
        return 1, str(e)


def do_pull():
    code, out = _git(["pull", "--no-rebase", "--quiet"])
    _log(f"[pull] {'OK' if code == 0 else 'SKIP'} {out[:150]}")


def do_push():
    code, out = _git(["status", "--porcelain", "--"] + KNOWLEDGE_PATHSPEC)
    if code != 0 or not out.strip():
        _log("[push] 변경 없음 — skip")
        return
    machine = (os.environ.get("COMPUTERNAME") or "PC").replace(" ", "-")[:20]
    _git(["add", "--"] + KNOWLEDGE_PATHSPEC)
    ccode, _ = _git(["commit", "-m", f"auto(knowledge): {machine} {datetime.now():%Y-%m-%d %H:%M}"])
    if ccode != 0:
        _log("[push] 스테이징 비어있음 — skip")
        return
    _git(["pull", "--no-rebase", "--quiet"])
    pcode, pout = _git(["push"])
    _log(f"[push] {'OK' if pcode == 0 else 'FAIL(오프라인/인증?)'} {pout[:150]}")


def _spawn_detached(mode: str):
    """워커를 분리 실행하고 즉시 반환 — 훅이 세션을 기다리지 않게."""
    flags = 0
    kwargs = {}
    if os.name == "nt":
        # DETACHED_PROCESS | CREATE_NO_WINDOW
        flags = 0x00000008 | 0x08000000
        kwargs["creationflags"] = flags
    else:
        kwargs["start_new_session"] = True
    try:
        subprocess.Popen([sys.executable, str(Path(__file__).resolve()), mode, "--worker"],
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, **kwargs)
    except Exception as e:
        _log(f"[spawn] 실패: {e}")


def main():
    # 주의: stdin(훅 JSON)을 읽지 않는다 — 미닫힘 stdin에서 read()가 멈추는 행 방지.
    # 페이로드는 사용하지 않으며, 작은 JSON은 OS 버퍼에 남았다 프로세스 종료 시 폐기됨.
    args = sys.argv[1:]
    mode = args[0] if args else ""
    if mode not in ("pull", "push"):
        print("사용법: wiki_git_sync.py [pull|push]")
        return
    if "--worker" in args:
        # 실제 작업 (분리된 워커)
        do_pull() if mode == "pull" else do_push()
    else:
        # 훅 진입점 — 워커 분리 후 즉시 종료 (세션 0ms 대기)
        _spawn_detached(mode)


if __name__ == "__main__":
    main()
