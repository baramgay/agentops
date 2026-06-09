#!/usr/bin/env python3
"""
Agent Auto Sync - Git auto-sync for multi-agent system.

Features:
- File change detection via watchdog (graceful fallback to polling)
- 30-second debounce after file changes -> auto git add/commit/push
- 30-minute interval for auto git pull
- Conflict handling with .conflict-<timestamp> backup
- --dry-run mode for testing
- --interval option to customize pull interval
"""

import argparse
import json
import logging
import os
import platform
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

WATCH_PATTERNS = [
    "agents/*/memory.md",
    "agents/*/role.md",
    # agent_status.json: merge=ours로 충돌 자동 해결되므로 watch 제외
    # 직접 push가 필요할 때는 수동 git push 사용
    "claude-config/**",
]

WATCH_GLOBS = [
    "agents/*/memory.md",
    "agents/*/role.md",
    "claude-config/*",
    "claude-config/**/*",
    "wiki/**/*.md",
]

IGNORE_PATTERNS = {
    ".git",
    "__pycache__",
    ".tmp",
    "config.local.json",
}

DEBOUNCE_SECONDS = 30
DEFAULT_PULL_INTERVAL = 1800  # 30 minutes

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("auto_sync")

# ---------------------------------------------------------------------------
# Globals for graceful shutdown
# ---------------------------------------------------------------------------

shutdown_event = threading.Event()


def _signal_handler(signum, frame):
    log.info("Shutdown signal received. Exiting gracefully...")
    shutdown_event.set()


signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def get_repo_root() -> Path:
    """Return the repository root (parent of scripts/)."""
    return Path(__file__).resolve().parent.parent


def get_machine_id(repo_root: Path) -> str:
    """Read machine_id from config.local.json, fallback to hostname."""
    config_path = repo_root / "config.local.json"
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            mid = data.get("machine_id")
            if mid:
                return str(mid)
        except (json.JSONDecodeError, OSError):
            pass
    return platform.node()


def is_ignored(path: Path, repo_root: Path) -> bool:
    """Check if a path matches any ignore pattern."""
    try:
        rel = path.relative_to(repo_root)
    except ValueError:
        return False
    parts = rel.parts
    for part in parts:
        if part in IGNORE_PATTERNS:
            return True
        for pat in IGNORE_PATTERNS:
            if pat.startswith("*.") and part.endswith(pat[1:]):
                return True
    return False


def matches_watch(path: Path, repo_root: Path) -> bool:
    """Check if a path matches any watch pattern (glob-style)."""
    try:
        rel = path.relative_to(repo_root)
    except ValueError:
        return False
    rel_posix = rel.as_posix()
    if rel_posix.startswith("claude-config/"):
        return True
    # 위키 지식 노트(.md) — 다중 PC 지식 공유 대상 (.obsidian 휘발 설정은 제외)
    if rel_posix.startswith("wiki/") and rel_posix.endswith(".md"):
        return True
    parts = rel.parts
    if len(parts) == 3 and parts[0] == "agents" and parts[2] in ("memory.md", "role.md"):
        return True
    return False


def git_run(repo_root: Path, args: list, dry_run: bool = False) -> subprocess.CompletedProcess | None:
    """Run a git command in the repo root."""
    cmd = ["git"] + args
    cmd_str = " ".join(cmd)
    if dry_run:
        log.info("[DRY-RUN] Would run: %s", cmd_str)
        return None
    log.info("Running: %s", cmd_str)
    try:
        result = subprocess.run(
            cmd,
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            stderr = result.stderr.strip()
            if stderr:
                log.warning("git stderr: %s", stderr)
        return result
    except subprocess.TimeoutExpired:
        log.error("git command timed out: %s", cmd_str)
        return None
    except FileNotFoundError:
        log.error("git not found. Is git installed and in PATH?")
        return None


def collect_watched_changes(repo_root: Path, dry_run: bool = False) -> list[str]:
    """Get list of changed files that match watch patterns (staged + unstaged + untracked)."""
    changed = set()

    # Unstaged / staged changes
    result = git_run(repo_root, ["status", "--porcelain"], dry_run=dry_run)
    if dry_run or result is None:
        return []
    for line in result.stdout.strip().splitlines():
        if not line or len(line) < 4:
            continue
        filepath = line[3:].strip()
        # Handle renames: "R  old -> new"
        if " -> " in filepath:
            filepath = filepath.split(" -> ")[-1]
        full = repo_root / filepath
        if not is_ignored(full, repo_root) and matches_watch(full, repo_root):
            changed.add(filepath)

    return sorted(changed)


def make_commit_message(changed_files: list[str], machine_id: str) -> str:
    """Create a commit message summarizing changes."""
    if len(changed_files) <= 3:
        summary = ", ".join(changed_files)
    else:
        summary = f"{', '.join(changed_files[:3])} +{len(changed_files) - 3} more"
    return f"auto: sync [{summary}] from {machine_id}"


def handle_conflicts(repo_root: Path, dry_run: bool = False):
    """After a pull, check for merge conflicts and create .conflict backups."""
    result = git_run(repo_root, ["diff", "--name-only", "--diff-filter=U"], dry_run=dry_run)
    if dry_run or result is None:
        return
    conflicted = [f.strip() for f in result.stdout.strip().splitlines() if f.strip()]
    if not conflicted:
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    for filepath in conflicted:
        full = repo_root / filepath
        if not full.exists():
            continue
        backup_name = f"{full.stem}.conflict-{timestamp}{full.suffix}"
        backup_path = full.parent / backup_name
        log.warning("Conflict detected: %s -> backup to %s", filepath, backup_name)
        if not dry_run:
            # 충돌 내용 백업
            backup_path.write_bytes(full.read_bytes())
            # agent_status.json은 로컬 우선 (merge=ours와 일관성 유지)
            if filepath == "agent_status.json":
                git_run(repo_root, ["checkout", "--ours", filepath])
                log.info("agent_status.json: kept local version (ours)")
            else:
                git_run(repo_root, ["checkout", "--theirs", filepath])
            git_run(repo_root, ["add", filepath])

    if not dry_run and conflicted:
        git_run(repo_root, ["commit", "-m", f"auto: resolve conflicts (backups created) at {timestamp}"])
        log.info("Conflicts resolved. Backup files created with .conflict-%s suffix.", timestamp)


# ---------------------------------------------------------------------------
# Sync operations
# ---------------------------------------------------------------------------


def do_push(repo_root: Path, machine_id: str, dry_run: bool = False):
    """Stage watched changed files, commit, and push."""
    changed = collect_watched_changes(repo_root, dry_run=dry_run)
    if not changed:
        log.debug("No watched files changed. Skipping push.")
        return

    log.info("Changed watched files: %s", changed)
    for f in changed:
        git_run(repo_root, ["add", f], dry_run=dry_run)

    msg = make_commit_message(changed, machine_id)
    git_run(repo_root, ["commit", "-m", msg], dry_run=dry_run)
    git_run(repo_root, ["push"], dry_run=dry_run)
    log.info("Push complete.")


def do_pull(repo_root: Path, dry_run: bool = False):
    """Pull from remote and handle conflicts."""
    log.info("Pulling from remote...")
    result = git_run(repo_root, ["pull", "--no-rebase"], dry_run=dry_run)
    if dry_run:
        return
    if result and result.returncode != 0:
        log.warning("Pull encountered issues. Checking for conflicts...")
        handle_conflicts(repo_root, dry_run=dry_run)
    else:
        log.info("Pull complete.")


_weekly_last_run_date: str = ""  # YYYY-MM-DD 형식, 당일 중복 실행 방지


def _maybe_run_weekly(repo_root: Path, dry_run: bool = False):
    """월요일에 weekly_report.py 를 한 번 실행한다."""
    global _weekly_last_run_date
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    if now.weekday() != 0:  # 0 = 월요일
        return
    if _weekly_last_run_date == today_str:
        return  # 이미 오늘 실행함
    _weekly_last_run_date = today_str
    weekly_script = repo_root / "scripts" / "weekly_report.py"
    if not weekly_script.exists():
        log.warning("weekly_report.py 를 찾을 수 없습니다: %s", weekly_script)
        return
    if dry_run:
        log.info("[DRY-RUN] Would run: %s %s", sys.executable, weekly_script)
        return
    log.info("월요일 감지 — 주간 보고서 생성 시작")
    try:
        subprocess.Popen(
            [sys.executable, str(weekly_script)],
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except Exception:
        log.exception("weekly_report.py 실행 중 오류 발생")


# ---------------------------------------------------------------------------
# Watchdog-based file watcher (with polling fallback)
# ---------------------------------------------------------------------------

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler

    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False


class SyncEventHandler:
    """Handles file change events with debounce."""

    def __init__(self, repo_root: Path, machine_id: str, dry_run: bool = False):
        self.repo_root = repo_root
        self.machine_id = machine_id
        self.dry_run = dry_run
        self._timer: threading.Timer | None = None
        self._lock = threading.Lock()

    def _on_change(self, path: Path):
        if is_ignored(path, self.repo_root):
            return
        if not matches_watch(path, self.repo_root):
            return
        rel = path.relative_to(self.repo_root)
        log.info("Change detected: %s (debounce %ds)", rel, DEBOUNCE_SECONDS)
        self._schedule_push()

    def _schedule_push(self):
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
            self._timer = threading.Timer(
                DEBOUNCE_SECONDS,
                self._do_push,
            )
            self._timer.daemon = True
            self._timer.start()

    def _do_push(self):
        try:
            do_push(self.repo_root, self.machine_id, self.dry_run)
        except Exception:
            log.exception("Error during auto-push")

    def cancel(self):
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()


if WATCHDOG_AVAILABLE:

    class _WatchdogHandler(FileSystemEventHandler):
        def __init__(self, sync_handler: SyncEventHandler):
            super().__init__()
            self.sync_handler = sync_handler

        def on_any_event(self, event):
            if event.is_directory:
                return
            path = Path(event.src_path)
            self.sync_handler._on_change(path)


def run_with_watchdog(repo_root: Path, handler: SyncEventHandler):
    """Use watchdog Observer for efficient file watching."""
    observer = Observer()
    wd_handler = _WatchdogHandler(handler)

    # Watch specific directories
    watch_dirs = [
        repo_root / "agents",
        repo_root / "claude-config",
    ]
    # Also watch repo root for agent_status.json
    observer.schedule(wd_handler, str(repo_root), recursive=False)
    for d in watch_dirs:
        if d.exists():
            observer.schedule(wd_handler, str(d), recursive=True)

    observer.start()
    log.info("Watchdog observer started.")
    return observer


def run_with_polling(repo_root: Path, handler: SyncEventHandler, poll_interval: int = 5):
    """Fallback: poll for changes using git status."""
    log.info("Polling mode (every %ds)...", poll_interval)
    last_status = ""
    while not shutdown_event.is_set():
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=str(repo_root),
                capture_output=True,
                text=True,
                timeout=30,
            )
            current_status = result.stdout.strip()
            if current_status != last_status and current_status:
                # Something changed - trigger handler for each changed file
                for line in current_status.splitlines():
                    if len(line) >= 4:
                        filepath = line[3:].strip()
                        if " -> " in filepath:
                            filepath = filepath.split(" -> ")[-1]
                        full = repo_root / filepath
                        handler._on_change(full)
                last_status = current_status
            elif not current_status:
                last_status = ""
        except Exception:
            log.exception("Polling error")
        shutdown_event.wait(poll_interval)


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Agent Auto Sync - Git auto-sync for multi-agent system")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would happen without executing git commands",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=DEFAULT_PULL_INTERVAL,
        help=f"Pull interval in seconds (default: {DEFAULT_PULL_INTERVAL})",
    )
    args = parser.parse_args()

    repo_root = get_repo_root()
    machine_id = get_machine_id(repo_root)

    log.info("=" * 60)
    log.info("Agent Auto Sync")
    log.info("  Repo root   : %s", repo_root)
    log.info("  Machine ID  : %s", machine_id)
    log.info("  Pull interval: %ds (%dm)", args.interval, args.interval // 60)
    log.info("  Dry-run     : %s", args.dry_run)
    log.info("  Watchdog    : %s", "available" if WATCHDOG_AVAILABLE else "fallback to polling")
    log.info("=" * 60)

    # Verify git repo
    result = git_run(repo_root, ["rev-parse", "--is-inside-work-tree"])
    if result is None or result.returncode != 0:
        log.error("Not a git repository: %s", repo_root)
        sys.exit(1)

    handler = SyncEventHandler(repo_root, machine_id, dry_run=args.dry_run)

    # Start file watcher
    observer = None
    poll_thread = None
    if WATCHDOG_AVAILABLE:
        observer = run_with_watchdog(repo_root, handler)
    else:
        log.warning("watchdog not installed. Using polling fallback.")
        log.warning("Install watchdog for better performance: pip install watchdog")
        poll_thread = threading.Thread(
            target=run_with_polling,
            args=(repo_root, handler),
            daemon=True,
        )
        poll_thread.start()

    # Periodic pull loop
    log.info("Starting periodic pull loop (every %ds)...", args.interval)
    try:
        # Initial pull
        do_pull(repo_root, dry_run=args.dry_run)
        _maybe_run_weekly(repo_root, args.dry_run)

        while not shutdown_event.is_set():
            shutdown_event.wait(args.interval)
            if not shutdown_event.is_set():
                do_pull(repo_root, dry_run=args.dry_run)
                _maybe_run_weekly(repo_root, args.dry_run)
    except KeyboardInterrupt:
        pass
    finally:
        log.info("Shutting down...")
        handler.cancel()
        if observer is not None:
            observer.stop()
            observer.join(timeout=5)
        shutdown_event.set()
        log.info("Auto Sync stopped.")


if __name__ == "__main__":
    main()
