"""
에이전트 상태 파일 공통 I/O 유틸리티
모든 스크립트가 동일한 파일 잠금 + 원자적 쓰기 메커니즘을 공유
"""

import json
import sys
from datetime import datetime
from pathlib import Path

try:
    import fcntl
    _HAS_FCNTL = True
except ImportError:
    _HAS_FCNTL = False
    import threading
    _THREAD_LOCK = threading.Lock()


def find_status_file() -> Path:
    """agent_status.json 탐색 (스크립트 위치 기준 상위)"""
    script_dir = Path(__file__).parent
    for path in [script_dir, script_dir.parent]:
        candidate = path / "agent_status.json"
        if candidate.exists():
            return candidate
    fallback = script_dir.parent / "agent_status.json"
    return fallback


# 권위 있는 에이전트 목록 — 에이전트 추가/제거 시 여기만 수정
ALL_AGENT_IDS = [
    "orchestrator", "lead-data", "lead-dev", "lead-pptx",
    "data-collector", "data-cleaner", "eda-analyst", "statistician",
    "ml-engineer", "deep-learning", "gis-specialist", "text-analyst",
    "visualizer", "reporter", "realty-analyst",
    "requirements", "ux-designer", "frontend", "backend", "dba",
    "security", "tester-unit", "tester-qa", "devops", "tech-writer",
    "statworkbench", "architect", "tester",
    "pptx-planner", "pptx-content", "pptx-designer", "pptx-builder", "pptx-reviewer",
]


def default_status() -> dict:
    """기본 에이전트 상태 생성 (ALL_AGENT_IDS 기준)."""
    return {
        "updated": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "agents": {a: {"status": "idle", "task": ""} for a in ALL_AGENT_IDS},
        "log": [],
    }


def _patch_missing_agents(data: dict) -> bool:
    """ALL_AGENT_IDS 기준으로 누락된 에이전트를 idle로 보완. 변경 있으면 True."""
    agents = data.setdefault("agents", {})
    added = [a for a in ALL_AGENT_IDS if a not in agents]
    for a in added:
        agents[a] = {"status": "idle", "task": ""}
    if added:
        print(f"[INFO] agent_status.json 누락 에이전트 자동 보완: {added}", file=sys.stderr)
    return bool(added)


def load_status() -> dict:
    """안전한 JSON 로드. 파일 없거나 손상 시 기본 상태 반환. 누락 에이전트 자동 보완."""
    path = find_status_file()
    if not path.exists():
        data = default_status()
        save_status(data)
        return data

    try:
        if _HAS_FCNTL:
            lock_path = path.with_suffix(".lock")
            with open(lock_path, "w") as lock_f:
                fcntl.flock(lock_f, fcntl.LOCK_SH)
                try:
                    with open(path, encoding="utf-8") as f:
                        data = json.load(f)
                finally:
                    fcntl.flock(lock_f, fcntl.LOCK_UN)
        else:
            with _THREAD_LOCK:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
        if _patch_missing_agents(data):
            save_status(data)
        return data
    except (json.JSONDecodeError, OSError) as e:
        backup = path.with_suffix(".json.bak")
        try:
            path.rename(backup)
        except OSError:
            pass
        data = default_status()
        save_status(data)
        print(f"[WARN] agent_status.json 손상 감지 ({e}). 백업 후 기본 상태 재생성.", file=sys.stderr)
        return data


def save_status(data: dict) -> None:
    """원자적 파일 쓰기: 전용 lockfile로 상호배제 후 temp 파일 생성 → rename."""
    path = find_status_file()
    tmp = path.with_suffix(".tmp")
    try:
        if _HAS_FCNTL:
            lock_path = path.with_suffix(".lock")
            with open(lock_path, "w") as lock_f:
                fcntl.flock(lock_f, fcntl.LOCK_EX)
                try:
                    with open(tmp, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    tmp.replace(path)
                finally:
                    fcntl.flock(lock_f, fcntl.LOCK_UN)
        else:
            with _THREAD_LOCK:
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                tmp.replace(path)
    except OSError as e:
        print(f"[WARN] agent_status.json 쓰기 실패: {e}", file=sys.stderr)
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
