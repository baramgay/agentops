"""
라이브 사무실 상태 동기화 API 서버
사용법: uv run --python .venv/bin/python scripts/api_server.py
        또는 .venv/Scripts/python.exe scripts/api_server.py (Windows)
엔드포인트:
  GET  /api/health              -> 서버 헬스 체크
  GET  /api/status              -> 전체 에이전트 상태 반환
  POST /api/status/{agent_id}   -> 특정 에이전트 상태 변경
  POST /api/approve/{agent_id}  -> 에이전트 승인 (status -> idle)
  POST /api/reject/{agent_id}   -> 에이전트 반려 (status -> idle)
  POST /api/instruct            -> 지시 명령 처리 (상태+로그+반응)
  WS   /ws                      -> 실시간 상태 브로드캐스트
"""

import asyncio
import csv
import io
import json
import os
import random
import re
import subprocess
import sys
import threading
import time
from collections import deque
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Set

# common_io의 권위 있는 에이전트 목록 공유 (에이전트 추가 시 common_io.py만 수정)
sys.path.insert(0, str(Path(__file__).parent))
try:
    from common_io import ALL_AGENT_IDS as _ALL_AGENT_IDS
except ImportError:
    _ALL_AGENT_IDS = None

# .env 파일 로드 (존재 시 환경변수 주입)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from fastapi import FastAPI, Query, Request, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel

# ── 페르소나 / LLM provider ─────────────────────────────
# 같은 scripts/ 디렉토리에 위치; 실행 시 sys.path 에 포함되어 있어야 함
try:
    from persona_loader import load_persona
    from llm_provider import get_provider
    _llm_provider = get_provider()
except Exception as _e:
    import warnings
    warnings.warn(f"LLM provider 로드 실패: {_e}")
    _llm_provider = None

try:
    import github_sync as _github_sync
except Exception as _e:
    import warnings
    warnings.warn(f"github_sync 로드 실패: {_e}")
    _github_sync = None

_gh_last_sync: Optional[str] = None  # 마지막 GitHub 동기화 시각 (KST ISO)
_gh_sync_lock = asyncio.Lock()       # 수동/자동 동기화 동시 실행 직렬화 (중복 원격 생성 방지)

app = FastAPI(title="Agent Status API", version="0.4.0")
_SERVER_START_TIME = time.time()
_server_start_dt = datetime.now()  # uptime_seconds 계산용 datetime 기준

# 타임존 상수
KST = timezone(timedelta(hours=9))

# stale 정리 마지막 실행 시각 (초기값 None)
_last_stale_cleanup: datetime | None = None

# CORS: 환경변수 기반 화이트리스트
_ALLOWED_ORIGINS_ENV = os.getenv("ALLOWED_ORIGINS", "")
if _ALLOWED_ORIGINS_ENV:
    _CORS_ORIGINS = [o.strip() for o in _ALLOWED_ORIGINS_ENV.split(",") if o.strip()]
else:
    # 로컬 개발 기본값
    _CORS_ORIGINS = [
        "http://localhost:8000",
        "http://localhost:8080",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8080",
        "null",  # file:// 프로토콜
    ]

# LAN/사설망 접속 허용 정규식 (localhost·127.0.0.1·사설 IP 대역, 임의 포트)
# 환경변수로 명시 화이트리스트를 지정하면 그쪽이 우선 — 이 regex는 로컬 개발 기본값일 때만 보조 적용
_CORS_REGEX = None if _ALLOWED_ORIGINS_ENV else (
    r"https?://(localhost|127\.0\.0\.1|"
    r"10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
    r"192\.168\.\d{1,3}\.\d{1,3}|"
    r"172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})(:\d+)?"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_origin_regex=_CORS_REGEX,
    allow_credentials=False,  # wildcard 미사용 시 False 유지
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# ── WebSocket 연결 관리 ───────────────────────────────────
_ws_clients: Set[WebSocket] = set()

# ── 로그 파일 경로 ──────────────────────────────────────
_WORK_LOG       = Path(__file__).parent.parent / "work_log.jsonl"
# 이슈 파일 경로 — 테스트 격리를 위해 env(AGENTS_ISSUES_FILE)로 재정의 가능
_ISSUES_FILE    = Path(os.environ.get("AGENTS_ISSUES_FILE",
                                      str(Path(__file__).parent.parent / "issues.json")))
_ISSUES_HISTORY = Path(os.environ.get("AGENTS_ISSUES_HISTORY",
                                      str(Path(__file__).parent.parent / "issues_history.jsonl")))
_issues_lock    = threading.Lock()

# ── 위키 경로 ── 테스트 격리를 위해 env(AGENTS_WIKI_ROOT)로 재정의 가능
_WIKI_ROOT      = Path(os.environ.get("AGENTS_WIKI_ROOT",
                                      str(Path(__file__).parent.parent / "wiki")))
_WIKI_NOTES     = _WIKI_ROOT / "notes"
_WIKI_MOC       = _WIKI_ROOT / "MoC"

# ── 프로젝트 파일 경로 ────────────────────────────────────────
_PROJECTS_FILE  = Path(__file__).parent.parent / "projects.json"
_projects_lock  = threading.Lock()

# 이슈 enum 허용값 (오타로 인한 칸반 미표시 유령 이슈 방지)
VALID_ISSUE_STATUS   = {"backlog", "todo", "in_progress", "in_review", "done", "cancelled"}
VALID_ISSUE_PRIORITY = {"urgent", "high", "medium", "low"}


async def _broadcast(message: dict) -> None:
    """연결된 모든 WebSocket 클라이언트에 메시지 브로드캐스트"""
    if not _ws_clients:
        return
    payload = json.dumps(message, ensure_ascii=False)
    disconnected = set()
    # set 복사본으로 이터레이션 — 동시성 안전 (이터레이션 중 set 변경 방지)
    for ws in list(_ws_clients):
        try:
            await ws.send_text(payload)
        except Exception:
            disconnected.add(ws)
    if disconnected:
        _ws_clients.difference_update(disconnected)


_loop_count = 0  # heartbeat 주기 카운터 (5번째마다 heartbeat 포함, 10000 주기 리셋)


async def _auto_broadcast_loop() -> None:
    """5초마다 status.json 읽어 전체 클라이언트에 브로드캐스트.
    매 5번째 루프(25초마다) heartbeat 필드를 추가로 전송한다."""
    global _loop_count
    while True:
        await asyncio.sleep(5)
        _loop_count = (_loop_count + 1) % 10000
        try:
            data = load_data()
            msg: dict = {
                "type": "status_update",
                "agents": data.get("agents", {}),
                "updated": data.get("updated", ""),
            }
            if _loop_count % 5 == 0:
                msg["heartbeat"] = datetime.now(KST).isoformat()
            await _broadcast(msg)
        except Exception:
            pass


@app.on_event("startup")
async def _startup():
    asyncio.create_task(_auto_broadcast_loop())
    asyncio.create_task(_daily_summary_scheduler())
    asyncio.create_task(_stale_working_cleanup_loop())
    asyncio.create_task(_github_autosync_loop())


async def _github_autosync_loop() -> None:
    """GitHub 자동 동기화 — 설정(token·sync_enabled·sync_interval_min>0) 시 주기 실행.
    config는 매 주기 재로딩(토큰/주기 변경 반영). 변경분 있으면 WS broadcast."""
    global _gh_last_sync
    if _github_sync is None:
        return
    cfg0 = _github_sync.get_config()
    interval = cfg0.get("sync_interval_min", 15)
    if not interval or interval <= 0 or not _github_sync.is_configured(cfg0):
        return  # 자동 동기화 비활성 (수동 버튼만 사용)
    await asyncio.sleep(min(interval, 5) * 60)  # 기동 직후 과도한 호출 방지
    while True:
        try:
            cfg = _github_sync.get_config()
            interval = cfg.get("sync_interval_min", 15)
            if interval and interval > 0 and _github_sync.is_configured(cfg) and cfg.get("sync_enabled", True):
                async with _gh_sync_lock:  # 수동 동기화와 동시 실행 방지 (중복 원격 생성 차단)
                    result = await asyncio.to_thread(
                        _github_sync.sync, cfg, _load_issues, _save_issues, _next_issue_id, _append_issue_event)
                _gh_last_sync = datetime.now(KST).strftime("%Y-%m-%dT%H:%M:%S")
                _changed = any(result.get(k) for k in (
                    "created_remote", "updated_remote", "created_local",
                    "updated_local", "pulled_comments", "pushed_comments"))
                if _changed:
                    await _broadcast({"type": "issue_update", "action": "github_autosync", "summary": result})
        except Exception as e:
            print(f"[WARN] github 자동 동기화 실패: {e}", file=sys.stderr)
        await asyncio.sleep(max(60, interval * 60))

# ── stale working 자동 복귀 ──────────────────────────────────
# working 상태가 STALE_TIMEOUT_HOURS 시간 이상 업데이트 없으면 idle 로 복귀
STALE_TIMEOUT_HOURS = float(os.getenv("STALE_TIMEOUT_HOURS", "2"))

async def _stale_working_cleanup_loop() -> None:
    """60초마다 실행: working 상태가 STALE_TIMEOUT_HOURS 시간 이상 방치된 에이전트를 idle로 복귀."""
    global _last_stale_cleanup
    while True:
        await asyncio.sleep(60)
        _last_stale_cleanup = datetime.now()
        try:
            data = load_data()
            agents = data.get("agents", {})
            changed = False
            for aid, av in agents.items():
                if av.get("status") != "working":
                    continue
                updated_str = av.get("updated", "")
                if not updated_str:
                    continue
                try:
                    # ISO 형식 파싱 — Z 접미사(UTC) 또는 naive(로컬) 모두 처리
                    updated_dt = datetime.fromisoformat(updated_str.replace("Z", "+00:00"))
                    if updated_dt.tzinfo is None:
                        updated_dt = updated_dt.replace(tzinfo=KST)
                    else:
                        updated_dt = updated_dt.astimezone(KST)
                    now_cmp = datetime.now(KST)
                except Exception:
                    continue
                elapsed_hours = (now_cmp - updated_dt).total_seconds() / 3600
                if elapsed_hours >= STALE_TIMEOUT_HOURS:
                    av["status"] = "idle"
                    av["task"] = ""
                    av["updated"] = datetime.now(KST).isoformat(timespec="seconds")
                    changed = True
            if changed:
                try:
                    save_data(data)
                    await _broadcast({
                        "type": "status_update",
                        "agents": data.get("agents", {}),
                        "updated": data.get("updated", ""),
                    })
                except Exception as _e:
                    print(f"[WARN] stale cleanup save 실패: {_e}", file=sys.stderr)
        except Exception:
            pass

# ── 파일 잠금 (멀티프로세스/멀티스레드 대응) ──────────────

try:
    import fcntl
    _has_fcntl = True
except ImportError:
    _has_fcntl = False
    import threading
    _thread_lock = threading.Lock()

# ── 유틸리티 ──────────────────────────────

def find_status_file() -> Path:
    """agent_status.json 탐색 (스크립트 위치 기준 상위)"""
    script_dir = Path(__file__).parent
    for path in [script_dir, script_dir.parent]:
        candidate = path / "agent_status.json"
        if candidate.exists():
            return candidate
    # 없으면 프로젝트 루트에 생성
    fallback = script_dir.parent / "agent_status.json"
    return fallback


def _default_status() -> dict:
    """기본 에이전트 상태 생성 (common_io.ALL_AGENT_IDS 기준)."""
    agents = _ALL_AGENT_IDS or [
        "orchestrator", "lead-data", "lead-dev", "lead-pptx",
        "data-collector", "data-cleaner", "eda-analyst", "statistician",
        "ml-engineer", "deep-learning", "gis-specialist", "text-analyst",
        "visualizer", "reporter", "realty-analyst",
        "requirements", "ux-designer", "frontend", "backend", "dba",
        "security", "tester-unit", "tester-qa", "devops", "tech-writer",
        "statworkbench", "architect", "tester",
        "pptx-planner", "pptx-content", "pptx-designer", "pptx-builder", "pptx-reviewer",
    ]
    return {
        "updated": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "agents": {a: {"status": "idle", "task": ""} for a in agents},
        "log": [],
    }


def _patch_missing_agents(data: dict) -> bool:
    """누락된 에이전트를 idle 상태로 추가. 변경 있으면 True 반환."""
    default = _default_status()
    agents = data.setdefault("agents", {})
    added = [a for a in default["agents"] if a not in agents]
    for a in added:
        agents[a] = {"status": "idle", "task": ""}
    if added:
        print(f"[INFO] agent_status.json에 누락 에이전트 추가: {added}", file=sys.stderr)
    return bool(added)


def load_data() -> dict:
    """안전한 JSON 로드. 파일 없거나 손상 시 기본 상태 반환."""
    path = find_status_file()
    if not path.exists():
        data = _default_status()
        save_data(data)
        return data

    try:
        if _has_fcntl:
            with open(path, encoding="utf-8") as f:
                fcntl.flock(f, fcntl.LOCK_SH)
                try:
                    data = json.load(f)
                finally:
                    fcntl.flock(f, fcntl.LOCK_UN)
        else:
            with _thread_lock:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
        # 누락 에이전트 자동 보완
        patched = _patch_missing_agents(data)
        # updated 필드 없는 에이전트 초기화 (stale cleanup 오작동 방지)
        now_iso = datetime.now().isoformat(timespec="seconds")
        updated_added = False
        for av in data.get("agents", {}).values():
            if "updated" not in av:
                av["updated"] = now_iso
                updated_added = True
        if patched or updated_added:
            save_data(data)
        return data
    except (json.JSONDecodeError, OSError) as e:
        # 손상된 파일 백업 후 기본 상태 반환
        backup = path.with_suffix(".json.bak")
        try:
            path.rename(backup)
        except OSError:
            pass
        data = _default_status()
        save_data(data)
        print(f"[WARN] agent_status.json 손상 감지 ({e}). 백업 후 기본 상태 재생성.", file=sys.stderr)
        return data


def save_data(data: dict) -> None:
    """원자적 파일 쓰기: temp 파일 생성 → rename (race condition 방지)."""
    path = find_status_file()
    tmp = path.with_suffix(".tmp")

    if _has_fcntl:
        with open(tmp, "w", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                json.dump(data, f, ensure_ascii=False, indent=2)
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
    else:
        with _thread_lock:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    # 원자적 교체 (Windows: PermissionError 시 기존 파일 제거 후 재시도)
    try:
        tmp.replace(path)
    except PermissionError:
        path.unlink(missing_ok=True)
        tmp.replace(path)


STATUS_LABEL = {
    "working": "작업 시작",
    "review": "검토 중",
    "waiting": "대기",
    "done": "완료",
    "idle": "유휴",
}

# ── POI 목록 (metaverse.html POI_LIST 기준) ──────────────────────────────────
# 휴식용 POI: coffee1(복도 커피머신A), coffee2(복도 커피머신B), sofa(휴게실 소파), water1/water2(정수기)
BREAK_POIS = ["coffee1", "coffee2", "sofa", "water1", "water2"]
# 회의/집합용 POI: lounge(회의실), board(회의실 스크린)
MEETING_POIS = ["lounge", "board"]

# ── Pydantic 모델 ─────────────────────────

class StatusUpdate(BaseModel):
    status: str
    task: str = ""


class InstructBody(BaseModel):
    agent_id: str
    text: str
    create_issue: bool = False   # True면 지시 내용을 GNI 이슈로 등록·연결
    priority: str = "medium"     # create_issue=True 일 때 이슈 우선순위


class SkillSaveBody(BaseModel):
    name: str      # 스킬 폴더명 (예: realty-pipeline)
    content: str   # 새 SKILL.md 내용


class GatheringBody(BaseModel):
    team: Optional[str] = None   # None이면 전체, "data"/"dev"/"pptx" 등
    action: str = "gather"       # "gather" 또는 "disperse"
    message: str = "전체 집합"


# ── 엔드포인트 ────────────────────────────

@app.get("/api/health")
def health_check():
    """서버 헬스 체크"""
    uptime_s = int(time.time() - _SERVER_START_TIME)
    data = load_data()
    agents = data.get("agents", {})
    return {
        "status": "ok",
        "timestamp": datetime.now(KST).isoformat(),
        "version": "2.0",
        "uptime_seconds": uptime_s,
        "ws_connections": len(_ws_clients),
        "agents_count": len(agents),
        "working_count": sum(1 for a in agents.values() if a.get("status") == "working"),
    }


@app.get("/api/ping")
def ping():
    """최소 헬스 체크 (부하 최소화)"""
    return {"pong": True, "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")}


@app.get("/api/stats")
def get_stats():
    """집계 통계 — 에이전트 상태 요약 (팀별 현황 포함)"""
    data = load_data()
    agents = data.get("agents", {})
    status_counts: dict = {}
    for a in agents.values():
        s = a.get("status", "idle")
        status_counts[s] = status_counts.get(s, 0) + 1

    # 팀별 현황 집계
    team_stats: dict = {}
    for aid, av in agents.items():
        team = _classify_team(aid)
        if team not in team_stats:
            team_stats[team] = {"total": 0, "working": 0, "idle": 0}
        team_stats[team]["total"] += 1
        st = av.get("status", "idle")
        if st == "working":
            team_stats[team]["working"] += 1
        elif st == "idle":
            team_stats[team]["idle"] += 1

    return {
        "total_agents": len(agents),
        "status_counts": status_counts,
        "ws_connections": len(_ws_clients),
        "uptime_seconds": (datetime.now() - _server_start_dt).total_seconds(),
        "updated": data.get("updated", ""),
        "validate_checks": 83,
        "last_stale_cleanup": _last_stale_cleanup.isoformat() if _last_stale_cleanup else None,
        "team_stats": team_stats,
        "gathering_active": bool(data.get("gathering_active", False)),
        "gathering_team": data.get("gathering_team"),
        "timestamp": datetime.now(KST).isoformat(),
    }


@app.get("/api/status")
def get_status():
    """전체 에이전트 상태 반환"""
    return load_data()


@app.post("/api/status/{agent_id}")
def update_status(agent_id: str, body: StatusUpdate):
    """특정 에이전트 상태 변경"""
    data = load_data()

    if agent_id not in data.get("agents", {}):
        raise HTTPException(status_code=404, detail=f"알 수 없는 에이전트 ID '{agent_id}'")

    status = body.status.lower()
    if status not in STATUS_LABEL:
        raise HTTPException(status_code=422, detail=f"status는 {list(STATUS_LABEL.keys())} 중 하나여야 합니다.")

    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    actual_status = "idle" if status == "done" else status

    data["agents"][agent_id] = {
        "status": actual_status,
        "task": body.task if actual_status != "idle" else "",
        "updated": now,
    }
    data["updated"] = now

    # 로그 추가 (최근 30개)
    log_entry = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "agent": agent_id,
        "status": status,
        "label": STATUS_LABEL.get(status, status),
        "task": body.task,
    }
    data.setdefault("log", []).insert(0, log_entry)
    data["log"] = data["log"][:30]

    save_data(data)
    _append_work_log({
        "ts": now, "timestamp": now,
        "agent_id": agent_id,
        "status": actual_status, "action": "status_change",
        "content": body.task or "", "task": body.task or "",
        "machine": "api-server",
    })
    # GNI-N 참조 시 이슈 자동 전이
    gni_match = re.search(r'GNI-\d+', body.task or "")
    if gni_match:
        try:
            _auto_transition_issue(gni_match.group(), status)
        except Exception:
            pass
    try:
        _check_and_alert(agent_id, status, data)
    except Exception:
        pass
    return {"ok": True, "agent_id": agent_id, "status": actual_status}


@app.post("/api/instruct")
def instruct(body: InstructBody):
    """
    지시 명령 처리:
    1. 에이전트 상태를 working으로 전환
    2. 지시 내용을 task에 기록
    3. 로그에 기록
    4. 반응 키워드 분석 결과 반환 (브라우저가 말풍선/행동 처리)
    """
    data = load_data()
    agent_id = body.agent_id.strip()
    if not agent_id:
        raise HTTPException(status_code=422, detail="agent_id가 비어있습니다")
    if not re.match(r'^[a-zA-Z0-9_-]+$', agent_id):
        raise HTTPException(status_code=422, detail="agent_id는 영문·숫자·-·_ 만 허용")
    text = body.text.strip()
    if not text:
        raise HTTPException(status_code=422, detail="지시 내용이 비어있습니다")
    if len(text) > 2000:
        raise HTTPException(status_code=413, detail="지시 내용이 2000자를 초과합니다")

    if agent_id not in data.get("agents", {}):
        raise HTTPException(status_code=404, detail=f"알 수 없는 에이전트 ID '{agent_id}'")

    # 키워드 기반 행동 분석
    action = "none"
    target_poi = None
    reaction = None  # 초기화 — LLM 미사용 시 fallback으로 덮어씀

    lower = text.lower()
    if any(k in lower for k in ["복귀", "돌아가", "데스크", "자리"]):
        reaction = "데스크로 복귀합니다."
        action = "return"
    elif any(k in lower for k in ["집합", "모여", "회의", "라운지", "미팅"]):
        reaction = "회의실로 이동합니다."
        action = "gather"
        target_poi = random.choice(MEETING_POIS)
    elif any(k in lower for k in ["커피", "휴식", "쉬어", "브레이크", "점심"]):
        reaction = "잠깐 휴식하겠습니다."
        action = "break"
        target_poi = random.choice(BREAK_POIS)
    elif any(k in lower for k in ["작업", "일해", "분석", "개발", "시작"]):
        reaction = "작업 시작하겠습니다."
        action = "work"
    elif any(k in lower for k in ["검토", "확인", "리뷰"]):
        reaction = "검토 진행하겠습니다."
        action = "review"
    elif any(k in lower for k in ["대기", "기다려", "홀드"]):
        action = "wait"

    # 페르소나 기반 반응 생성 — LLM 실패 시 키워드 매칭 결과 유지
    try:
        persona = load_persona(agent_id) if 'load_persona' in globals() else None
    except Exception:
        persona = None
    if _llm_provider is not None:
        try:
            llm_reaction = _llm_provider.generate_reaction(agent_id, text, persona, action)
            if llm_reaction is not None:
                reaction = llm_reaction  # LLM 결과 우선 적용
        except Exception:
            pass  # LLM 실패 → 키워드 매칭 reaction 유지
    if reaction is None:
        # fallback: 키워드 매칭도 없을 때 기본 반응
        _fallback_map = {
            "return": "데스크로 복귀합니다.",
            "gather": "회의실로 이동합니다.",
            "break": "잠깐 휴식하겠습니다.",
            "work": "작업 시작하겠습니다.",
            "review": "검토 진행하겠습니다.",
            "wait": "대기하겠습니다.",
        }
        reaction = _fallback_map.get(action, "지시 확인했습니다.")

    # 페이퍼클립 연동: 지시를 GNI 이슈로 등록하고 task에 참조를 삽입 (이후 상태변경 시 자동전이)
    issue_id = None
    if body.create_issue:
        try:
            summary = text.strip().splitlines()[0][:60] if text.strip() else "에이전트 지시"
            created = _create_issue_sync(title=summary, description=text,
                                         assignee_id=agent_id, priority=body.priority,
                                         status="in_progress")
            issue_id = created["id"]
            text = f"{text} ({issue_id})"  # GNI-N 참조 → _auto_transition_issue가 추후 동기화
        except Exception as e:
            print(f"[WARN] instruct 이슈 자동생성 실패: {e}", file=sys.stderr)

    # 상태 업데이트
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    data["agents"][agent_id] = {"status": "working", "task": text, "updated": now}
    data["updated"] = now

    # 로그 추가
    log_entry = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "agent": agent_id,
        "status": "working",
        "label": "지시 수행",
        "task": text,
    }
    data.setdefault("log", []).insert(0, log_entry)
    data["log"] = data["log"][:30]

    save_data(data)
    _append_work_log({
        "ts": now, "timestamp": now,
        "agent_id": agent_id,
        "status": "working", "action": "instruct",
        "content": text, "task": text,
        "machine": "api-server",
    })

    # 반복 패턴 감지: 동일 에이전트에게 같은 키워드가 3회 이상 지시된 경우 자동화 후보 태깅
    repeat_flag = _check_instruct_repeat(agent_id, text)

    return {
        "ok": True,
        "agent_id": agent_id,
        "status": "working",
        "task": text,
        "reaction": reaction,
        "action": action,
        "target_poi": target_poi,
        "persona_loaded": persona is not None,
        "automation_candidate": repeat_flag,
        "issue_id": issue_id,
    }


def _check_instruct_repeat(agent_id: str, text: str) -> bool:
    """work_log.jsonl에서 동일 에이전트의 지시 내용 키워드 반복 횟수를 확인.
    핵심 키워드가 3회 이상 반복되면 True(자동화 후보) 반환 + work_log에 태깅."""
    try:
        if not _WORK_LOG.exists():
            return False
        keywords = [w for w in text.split() if len(w) >= 3][:5]
        if not keywords:
            return False
        # 최근 500건만 확인 (성능)
        lines = _read_last_lines(_WORK_LOG, 500)
        counts: dict = {}
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except Exception:
                continue
            if e.get("agent_id") != agent_id or e.get("action") != "instruct":
                continue
            prev = (e.get("content") or e.get("task", "")).lower()
            for kw in keywords:
                if kw.lower() in prev:
                    counts[kw] = counts.get(kw, 0) + 1
        top_kw = max(counts, key=lambda k: counts[k]) if counts else None
        if top_kw and counts[top_kw] >= 3:
            _append_work_log({
                "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "agent_id": agent_id,
                "status": "automation_candidate",
                "action": "repeat_pattern",
                "content": f"자동화 후보: '{top_kw}' 키워드 {counts[top_kw]}회 반복",
                "machine": "api-server",
            })
            return True
    except Exception:
        pass
    return False


# ── Windows 토스트 알림 ──────────────────────────────────

# 알림 쿨다운 추적: { 쿨다운_키: 마지막_발송_timestamp }
_alert_cooldown: dict = {}
# 에이전트별 최근 상태 전환 이력: { agent_id: [(status, timestamp), ...] }
_agent_status_history: dict = {}
_COOLDOWN_SECONDS = 300  # 5분


def _send_toast(title: str, msg: str) -> None:
    """Windows 토스트 알림 발송. win10toast 없으면 notify_report.py 로 fallback.
    메인 흐름을 블로킹하지 않도록 Popen / threaded 방식만 사용."""
    try:
        from win10toast import ToastNotifier
        ToastNotifier().show_toast(title, msg, duration=5, threaded=True)
    except Exception:
        try:
            subprocess.Popen(
                [
                    sys.executable,
                    str(Path(__file__).parent / "notify_report.py"),
                    "--title", title,
                    "--message", msg,
                ],
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except Exception:
            pass


def _check_and_alert(agent_id: str, status: str, data: dict) -> None:
    """상태 변경 후 조건 검사하여 필요 시 Windows 알림 발송.

    조건 1: done + 리더급 에이전트 (orchestrator 또는 lead-* 접두사)
    조건 2: 동일 에이전트가 5분 내 done→working→done 사이클 2회 이상 (긴급 상황)
    조건 3: working 에이전트 수가 전체의 80% 이상 (전체 가동)
    """
    now_ts = time.time()
    agents = data.get("agents", {})
    total_agents = len(agents)

    # 이력 기록 (status 파라미터는 요청 값 그대로, done 포함)
    if agent_id not in _agent_status_history:
        _agent_status_history[agent_id] = []
    _agent_status_history[agent_id].append((status, now_ts))
    # 5분 이전 이력 제거
    _agent_status_history[agent_id] = [
        (s, t) for s, t in _agent_status_history[agent_id]
        if now_ts - t <= _COOLDOWN_SECONDS
    ]

    def _is_on_cooldown(key: str) -> bool:
        last = _alert_cooldown.get(key, 0)
        return (now_ts - last) < _COOLDOWN_SECONDS

    def _mark_cooldown(key: str) -> None:
        _alert_cooldown[key] = now_ts

    # ── 조건 1: done + 리더급 에이전트 ──────────────────
    if status == "done" and (
        agent_id == "orchestrator" or agent_id.startswith("lead-")
    ):
        key = f"cond1:{agent_id}"
        if not _is_on_cooldown(key):
            label = agents.get(agent_id, {}).get("task", "") or ""
            _send_toast(
                f"[완료] {agent_id}",
                f"리더급 에이전트 작업 완료\n{label[:80]}" if label else "리더급 에이전트 작업 완료",
            )
            _mark_cooldown(key)

    # ── 조건 2: 5분 내 done→working→done 2회 이상 ──────
    history = _agent_status_history.get(agent_id, [])
    done_count = sum(1 for s, _ in history if s == "done")
    if done_count >= 2:
        key = f"cond2:{agent_id}"
        if not _is_on_cooldown(key):
            _send_toast(
                f"[긴급] {agent_id} 반복 완료 감지",
                f"5분 내 {done_count}회 done 상태 전환 — 긴급 상황 가능성",
            )
            _mark_cooldown(key)

    # ── 조건 3: working 에이전트 비율 80% 이상 ──────────
    if total_agents > 0:
        working_count = sum(
            1 for a in agents.values() if a.get("status") == "working"
        )
        ratio = working_count / total_agents
        if ratio >= 0.8:
            key = "cond3:full_load"
            if not _is_on_cooldown(key):
                _send_toast(
                    "[전체 가동] 에이전트 부하 경고",
                    f"working 에이전트 {working_count}/{total_agents} ({ratio*100:.0f}%) — 전체 가동 상태",
                )
                _mark_cooldown(key)


def _append_work_log(entry: dict) -> None:
    """work_log.jsonl 에 한 줄 추가"""
    try:
        with open(_WORK_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[WARN] work_log.jsonl 기록 실패: {e}", file=sys.stderr)


# ════════════════════════════════════════════════════════════
# 이슈 트래커 — native 저장소 헬퍼
# ════════════════════════════════════════════════════════════

def _load_issues() -> dict:
    """issues.json 로드. 없으면 초기 구조 반환."""
    if not _ISSUES_FILE.exists():
        return {"seq": 0, "issues": {}}
    try:
        with _issues_lock:
            return json.loads(_ISSUES_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"seq": 0, "issues": {}}


def _save_issues(data: dict) -> None:
    """원자적 쓰기: tmp → rename"""
    tmp = _ISSUES_FILE.with_suffix(".tmp")
    try:
        with _issues_lock:
            tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            try:
                tmp.replace(_ISSUES_FILE)
            except PermissionError:
                _ISSUES_FILE.unlink(missing_ok=True)
                tmp.replace(_ISSUES_FILE)
    except Exception as e:
        print(f"[WARN] issues.json 쓰기 실패: {e}", file=sys.stderr)
        tmp.unlink(missing_ok=True)


def _append_issue_event(action: str, issue_id: str, payload: dict) -> None:
    """issues_history.jsonl 에 이벤트 한 줄 추가"""
    entry = {
        "ts": datetime.now(KST).strftime("%Y-%m-%dT%H:%M:%S"),
        "action": action,
        "issue_id": issue_id,
        **{k: v for k, v in payload.items() if k not in ("comments",)},
    }
    try:
        with open(_ISSUES_HISTORY, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[WARN] issues_history.jsonl 기록 실패: {e}", file=sys.stderr)


def _next_issue_id(data: dict) -> str:
    """GNI-N 형식 ID 발번 및 seq 증가"""
    data["seq"] = data.get("seq", 0) + 1
    return f"GNI-{data['seq']}"


def _auto_transition_issue(issue_id: str, agent_status: str) -> None:
    """agent status 변경에 따라 이슈 상태 자동 전이 (GNI-N 참조 시)"""
    STATUS_MAP = {"working": "in_progress", "review": "in_review", "done": "done"}
    new_status = STATUS_MAP.get(agent_status)
    if not new_status:
        return
    data = _load_issues()
    issue = data.get("issues", {}).get(issue_id)
    if not issue:
        return
    if issue.get("status") in ("done", "cancelled"):
        return
    issue["status"] = new_status
    issue["updated"] = datetime.now(KST).strftime("%Y-%m-%dT%H:%M:%S")
    data["issues"][issue_id] = issue
    _save_issues(data)
    _append_issue_event("auto_transition", issue_id, {"status": new_status, "trigger": agent_status})


def _create_issue_sync(title: str, description: str, assignee_id: str = "",
                       priority: str = "medium", status: str = "in_progress") -> dict:
    """동기 컨텍스트(instruct 등)에서 GNI 이슈 생성. WS broadcast 없음 — 클라이언트 폴링으로 반영.
    페이퍼클립(지시) → 이슈 자동 등록 연동에 사용."""
    if priority not in VALID_ISSUE_PRIORITY:
        priority = "medium"
    if status not in VALID_ISSUE_STATUS:
        status = "in_progress"
    idata = _load_issues()
    issue_id = _next_issue_id(idata)
    now = datetime.now(KST).strftime("%Y-%m-%dT%H:%M:%S")
    issue = {
        "id": issue_id,
        "title": (title or "(제목 없음)")[:120],
        "description": description or "",
        "status": status,
        "priority": priority,
        "assigneeId": assignee_id or "",
        "labels": ["에이전트지시"],
        "created": now,
        "updated": now,
        "comments": [],
    }
    idata["issues"][issue_id] = issue
    _save_issues(idata)
    _append_issue_event("create", issue_id, issue)
    return issue


# ── 이슈 Pydantic 모델 ────────────────────────────────────

class IssueCreate(BaseModel):
    title: str
    description: str = ""
    status: str = "backlog"
    priority: str = "medium"
    assigneeId: str = ""
    labels: list[str] = []
    projectId: str = ""      # 소속 프로젝트 (PRJ-N)


class IssueUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    assigneeId: str | None = None
    labels: list[str] | None = None
    projectId: str | None = None  # 소속 프로젝트 (PRJ-N)


class CommentCreate(BaseModel):
    author: str = "사용자"
    text: str


# ── 이슈 엔드포인트 ────────────────────────────────────────

@app.get("/api/issues/stats")
def get_issues_stats():
    """이슈 KPI 통계"""
    data = _load_issues()
    issues = list(data.get("issues", {}).values())
    by_status: dict = {}
    by_priority: dict = {}
    by_assignee: dict = {}
    for iss in issues:
        s = iss.get("status", "backlog")
        by_status[s] = by_status.get(s, 0) + 1
        p = iss.get("priority", "medium")
        by_priority[p] = by_priority.get(p, 0) + 1
        a = iss.get("assigneeId", "")
        if a:
            by_assignee[a] = by_assignee.get(a, 0) + 1
    active = sum(v for k, v in by_status.items() if k not in ("done", "cancelled"))
    return {
        "total": len(issues),
        "active": active,
        "by_status": by_status,
        "by_priority": by_priority,
        "by_assignee": by_assignee,
    }


@app.get("/api/issues")
def list_issues(
    status: str = "",
    assignee: str = "",
    priority: str = "",
    q: str = "",
    include_cancelled: bool = False,
):
    """이슈 목록 조회 (필터 지원). soft-delete된 cancelled는 기본 제외 —
    집계·배지 과다 카운트 방지. status=cancelled 명시 또는 include_cancelled=1 시 노출."""
    data = _load_issues()
    issues = list(data.get("issues", {}).values())
    statuses = status.split(",") if status else []
    if statuses:
        issues = [i for i in issues if i.get("status") in statuses]
    # cancelled는 명시적으로 요청하지 않는 한 제외 (soft-delete 숨김)
    if not include_cancelled and "cancelled" not in statuses:
        issues = [i for i in issues if i.get("status") != "cancelled"]
    if assignee:
        issues = [i for i in issues if i.get("assigneeId") == assignee]
    if priority:
        issues = [i for i in issues if i.get("priority") == priority]
    if q:
        q_lower = q.lower()
        issues = [i for i in issues if q_lower in i.get("title", "").lower()
                  or q_lower in i.get("description", "").lower()]
    issues.sort(key=lambda x: x.get("created", ""), reverse=True)
    return issues


@app.get("/api/issues/{issue_id}")
def get_issue(issue_id: str):
    """단일 이슈 조회 (ID 기준)"""
    data = _load_issues()
    issue = data.get("issues", {}).get(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail=f"이슈 '{issue_id}' 를 찾을 수 없습니다")
    return issue


@app.post("/api/issues")
async def create_issue(body: IssueCreate):
    """이슈 생성 — 서버가 GNI-N ID 발번"""
    if body.status not in VALID_ISSUE_STATUS:
        raise HTTPException(status_code=422, detail=f"status는 {sorted(VALID_ISSUE_STATUS)} 중 하나여야 합니다")
    if body.priority not in VALID_ISSUE_PRIORITY:
        raise HTTPException(status_code=422, detail=f"priority는 {sorted(VALID_ISSUE_PRIORITY)} 중 하나여야 합니다")
    data = _load_issues()
    issue_id = _next_issue_id(data)
    now = datetime.now(KST).strftime("%Y-%m-%dT%H:%M:%S")
    issue = {
        "id": issue_id,
        "title": body.title,
        "description": body.description,
        "status": body.status,
        "priority": body.priority,
        "assigneeId": body.assigneeId,
        "labels": body.labels,
        "created": now,
        "updated": now,
        "comments": [],
    }
    data["issues"][issue_id] = issue
    _save_issues(data)
    _append_issue_event("create", issue_id, issue)
    await _broadcast({"type": "issue_update", "action": "create", "issue": issue})
    return issue


@app.patch("/api/issues/{issue_id}")
async def update_issue(issue_id: str, body: IssueUpdate):
    """이슈 필드 부분 수정"""
    if body.status is not None and body.status not in VALID_ISSUE_STATUS:
        raise HTTPException(status_code=422, detail=f"status는 {sorted(VALID_ISSUE_STATUS)} 중 하나여야 합니다")
    if body.priority is not None and body.priority not in VALID_ISSUE_PRIORITY:
        raise HTTPException(status_code=422, detail=f"priority는 {sorted(VALID_ISSUE_PRIORITY)} 중 하나여야 합니다")
    data = _load_issues()
    issue = data.get("issues", {}).get(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail=f"이슈 '{issue_id}' 를 찾을 수 없습니다")
    for field, value in body.model_dump(exclude_none=True).items():
        issue[field] = value
    issue["updated"] = datetime.now(KST).strftime("%Y-%m-%dT%H:%M:%S")
    data["issues"][issue_id] = issue
    _save_issues(data)
    _append_issue_event("update", issue_id, body.model_dump(exclude_none=True))
    # 이슈 완료 시 위키 레슨런 자동 생성
    if issue.get("status") == "done":
        try:
            _issue_to_wiki(issue)
        except Exception:
            pass
    await _broadcast({"type": "issue_update", "action": "update", "issue": issue})
    return issue


@app.delete("/api/issues/{issue_id}")
async def delete_issue(issue_id: str):
    """이슈 soft delete (status: cancelled)"""
    data = _load_issues()
    issue = data.get("issues", {}).get(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail=f"이슈 '{issue_id}' 를 찾을 수 없습니다")
    issue["status"] = "cancelled"
    issue["updated"] = datetime.now(KST).strftime("%Y-%m-%dT%H:%M:%S")
    data["issues"][issue_id] = issue
    _save_issues(data)
    _append_issue_event("delete", issue_id, {})
    await _broadcast({"type": "issue_update", "action": "delete", "issue_id": issue_id})
    return {"ok": True, "issue_id": issue_id}


@app.post("/api/issues/{issue_id}/comments")
async def add_comment(issue_id: str, body: CommentCreate):
    """이슈에 코멘트 추가"""
    data = _load_issues()
    issue = data.get("issues", {}).get(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail=f"이슈 '{issue_id}' 를 찾을 수 없습니다")
    now = datetime.now(KST).strftime("%Y-%m-%dT%H:%M:%S")
    comment = {"author": body.author, "text": body.text, "ts": now}
    issue.setdefault("comments", []).append(comment)
    issue["updated"] = now
    data["issues"][issue_id] = issue
    _save_issues(data)
    _append_issue_event("comment", issue_id, {"author": body.author})
    await _broadcast({"type": "issue_update", "action": "comment", "issue": issue})
    return comment


# ── GitHub Issues 양방향 동기화 ────────────────────────────
@app.get("/api/github/status")
def github_status():
    """GitHub 연동 상태 — 토큰 설정 여부·repo·rate limit·마지막 동기화. 토큰 값은 미노출."""
    if _github_sync is None:
        return {"configured": False, "available": False,
                "message": "github_sync 모듈 로드 실패"}
    cfg = _github_sync.get_config()
    if not _github_sync.is_configured(cfg):
        return {"configured": False, "available": True, "repo": cfg.get("repo", ""),
                "last_sync": _gh_last_sync,
                "message": "PAT 미설정 — config.local.json의 github.token 또는 GITHUB_TOKEN 환경변수를 설정하세요."}
    try:
        rl = _github_sync.get_rate_limit(cfg)
        ok = "error" not in rl
        return {"configured": True, "available": True, "connected": ok,
                "repo": cfg["repo"], "rate_limit": rl, "last_sync": _gh_last_sync,
                "sync_enabled": cfg.get("sync_enabled", True)}
    except Exception as e:
        return {"configured": True, "available": True, "connected": False,
                "repo": cfg["repo"], "last_sync": _gh_last_sync, "error": str(e)}


@app.post("/api/github/sync")
async def github_sync_run():
    """GNI 이슈 ↔ GitHub Issues 양방향 동기화 실행."""
    global _gh_last_sync
    if _github_sync is None:
        raise HTTPException(status_code=503, detail="github_sync 모듈을 사용할 수 없습니다")
    cfg = _github_sync.get_config()
    if not _github_sync.is_configured(cfg):
        raise HTTPException(status_code=422,
                            detail="GitHub PAT 미설정 — config.local.json의 github.token 또는 GITHUB_TOKEN 환경변수를 설정하세요")
    try:
        # 블로킹 네트워크 I/O → 스레드로 위임 (이벤트 루프 보호) + 자동 동기화와 직렬화
        async with _gh_sync_lock:
            result = await asyncio.to_thread(
                _github_sync.sync, cfg, _load_issues, _save_issues, _next_issue_id, _append_issue_event)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"GitHub 동기화 실패: {e}")
    _gh_last_sync = datetime.now(KST).strftime("%Y-%m-%dT%H:%M:%S")
    try:
        await _broadcast({"type": "issue_update", "action": "github_sync", "summary": result})
    except Exception:
        pass
    return {"ok": True, "synced_at": _gh_last_sync, **result}


@app.post("/api/approve/{agent_id}")
async def approve_agent(agent_id: str):
    """에이전트 승인 — status를 idle로 변경하고 로그 기록"""
    data = load_data()
    if agent_id not in data.get("agents", {}):
        raise HTTPException(status_code=404, detail=f"에이전트 '{agent_id}' 를 찾을 수 없습니다")

    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    prev_task = data["agents"][agent_id].get("task", "")
    data["agents"][agent_id] = {"status": "idle", "task": ""}
    data["updated"] = now

    log_entry = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "agent": agent_id,
        "status": "approved",
        "label": "승인",
        "task": prev_task,
    }
    data.setdefault("log", []).insert(0, log_entry)
    data["log"] = data["log"][:30]
    save_data(data)

    _append_work_log({
        "ts": now, "timestamp": now,
        "agent_id": agent_id,
        "status": "idle", "action": "approve",
        "content": prev_task or "", "task": prev_task or "",
        "machine": "api-server",
    })

    await _broadcast({
        "type": "status_update",
        "agents": data.get("agents", {}),
        "updated": now,
    })

    return {"ok": True, "agent_id": agent_id, "action": "approve", "status": "idle"}


@app.post("/api/reject/{agent_id}")
async def reject_agent(agent_id: str):
    """에이전트 반려 — status를 idle로 변경하고 로그 기록"""
    data = load_data()
    if agent_id not in data.get("agents", {}):
        raise HTTPException(status_code=404, detail=f"에이전트 '{agent_id}' 를 찾을 수 없습니다")

    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    prev_task = data["agents"][agent_id].get("task", "")
    data["agents"][agent_id] = {"status": "idle", "task": ""}
    data["updated"] = now

    log_entry = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "agent": agent_id,
        "status": "rejected",
        "label": "반려",
        "task": prev_task,
    }
    data.setdefault("log", []).insert(0, log_entry)
    data["log"] = data["log"][:30]
    save_data(data)

    _append_work_log({
        "ts": now, "timestamp": now,
        "agent_id": agent_id,
        "status": "idle", "action": "reject",
        "content": prev_task or "", "task": prev_task or "",
        "machine": "api-server",
    })

    await _broadcast({
        "type": "status_update",
        "agents": data.get("agents", {}),
        "updated": now,
    })

    return {"ok": True, "agent_id": agent_id, "action": "reject", "status": "idle"}


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    """WebSocket 연결 — 상태 변경 실시간 브로드캐스트"""
    await ws.accept()
    _ws_clients.add(ws)
    try:
        # 연결 직후 현재 상태 즉시 전송
        try:
            data = load_data()
            await ws.send_text(json.dumps({
                "type": "status_update",
                "agents": data.get("agents", {}),
                "updated": data.get("updated", ""),
            }, ensure_ascii=False))
        except Exception:
            pass  # 초기 전송 실패해도 연결 유지
        # 클라이언트가 연결을 유지하는 동안 대기
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        _ws_clients.discard(ws)


@app.get("/api/agents/{agent_id}")
def get_agent(agent_id: str):
    """단일 에이전트 상태 조회"""
    data = load_data()
    if agent_id not in data.get("agents", {}):
        raise HTTPException(status_code=404, detail=f"알 수 없는 에이전트 ID '{agent_id}'")
    agent = data["agents"][agent_id]
    return {
        "agent_id": agent_id,
        **agent,
        "updated": agent.get("updated") or data.get("updated"),
    }


_REPO_ROOT = Path(__file__).parent.parent
_SKILLS_DIR = _REPO_ROOT / 'skills'
_SAFE_NAME   = re.compile(r'^[a-zA-Z0-9_-]{1,64}$')  # 경로 탐색 방지


def _git_is_dirty(path: Path) -> bool:
    """지정 파일이 git 기준 수정됐는지 확인 (다중 PC 충돌 경고용)."""
    try:
        rel = path.relative_to(_REPO_ROOT)
        result = subprocess.run(
            ['git', '-C', str(_REPO_ROOT), 'status', '--porcelain', str(rel)],
            capture_output=True, text=True, timeout=5
        )
        return bool(result.stdout.strip())
    except Exception:
        return False


@app.get("/api/skill/{name}")
def get_skill(name: str):
    """레포 스킬 SKILL.md 현재 내용 반환."""
    if not _SAFE_NAME.match(name):
        raise HTTPException(status_code=400, detail="유효하지 않은 스킬 이름")
    skill_md = _SKILLS_DIR / name / 'SKILL.md'
    if not skill_md.exists():
        raise HTTPException(status_code=404, detail=f"스킬 '{name}' 을 찾을 수 없습니다")
    return {"name": name, "content": skill_md.read_text(encoding='utf-8')}


@app.post("/api/skill/save")
def save_skill(body: SkillSaveBody):
    """레포 스킬 SKILL.md 저장.

    안전 절차:
    1. 스킬 이름 화이트리스트 검증 (경로 탐색 방지)
    2. 스킬 폴더가 실제 skills/ 하위인지 확인
    3. 저장 전 .bak 백업 생성
    4. git dirty 여부 확인 → 경고 포함 응답 (저장은 계속 진행)
    5. 원자적 쓰기 (tmp → rename)
    6. 커밋/푸시 없음 — 사용자가 직접 push 명령 실행
    """
    name = body.name.strip()
    if not _SAFE_NAME.match(name):
        return {"ok": False, "error": "유효하지 않은 스킬 이름 (영문·숫자·-·_ 만 허용)"}

    skill_dir = _SKILLS_DIR / name
    skill_md  = skill_dir / 'SKILL.md'

    # 실제 skills/ 하위인지 절대경로로 검증
    try:
        skill_md.resolve().relative_to(_SKILLS_DIR.resolve())
    except ValueError:
        return {"ok": False, "error": "경로 탐색 시도 감지 — 저장 거부"}

    if not skill_dir.exists():
        return {"ok": False, "error": f"스킬 폴더 '{name}' 이 존재하지 않습니다"}

    # 내용 존재 및 크기 제한
    if not body.content or not body.content.strip():
        return {"ok": False, "error": "내용이 비어있습니다"}
    if len(body.content.encode('utf-8')) > 512 * 1024:
        return {"ok": False, "error": "내용이 512KB를 초과합니다"}

    # git dirty 경고 (저장 막지 않음 — 경고만)
    was_dirty = _git_is_dirty(skill_md)

    # 기존 파일 백업 (.bak 덮어쓰기)
    if skill_md.exists():
        bak = skill_md.with_suffix('.md.bak')
        try:
            bak.write_text(skill_md.read_text(encoding='utf-8'), encoding='utf-8')
        except Exception as e:
            return {"ok": False, "error": f"백업 실패: {e}"}

    # 원자적 쓰기
    tmp = skill_md.with_suffix('.tmp')
    try:
        tmp.write_text(body.content, encoding='utf-8')
        try:
            tmp.replace(skill_md)
        except PermissionError:
            skill_md.unlink(missing_ok=True)
            tmp.replace(skill_md)
    except Exception as e:
        try:
            tmp.unlink(missing_ok=True)
        except Exception:
            pass
        return {"ok": False, "error": f"파일 쓰기 실패: {e}"}

    msg = f"{name}/SKILL.md 저장 완료"
    if was_dirty:
        msg += " (주의: 저장 전 이미 수정된 상태였습니다. push 전 git diff 확인 권장)"

    return {
        "ok": True,
        "name": name,
        "message": msg,
        "was_dirty": was_dirty,
    }


@app.get("/api/log")
def get_server_log(lines: int = 20):
    """서버 측 autopull.log 최근 N줄 반환."""
    log_file = _REPO_ROOT / "logs" / "autopull.log"
    if not log_file.exists():
        return {"lines": []}
    try:
        content = log_file.read_text(encoding="utf-8", errors="replace").splitlines()
        return {"lines": content[-min(lines, 200):]}
    except Exception as e:
        return {"lines": [f"로그 읽기 오류: {e}"]}


def _read_last_lines(path: Path, n: int) -> list:
    """대용량 파일에서 마지막 n줄 효율적으로 읽기 (deque 사용)."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return list(deque(f, maxlen=n))
    except Exception:
        return []


@app.get("/api/worklog")
def get_worklog(
    limit: int = Query(200, ge=1, le=500),
    agent_id: Optional[str] = Query(None, description="특정 에이전트 ID로 필터"),
):
    """work_log.jsonl 최근 N건 반환. agent_id 파라미터로 특정 에이전트만 조회 가능."""
    if agent_id is not None:
        agent_id = agent_id.strip()
        if not agent_id:
            agent_id = None  # 빈 문자열은 필터 없음으로 처리
        elif len(agent_id) > 128 or not re.match(r'^[a-zA-Z0-9_-]+$', agent_id):
            return {"entries": [], "error": "agent_id 형식 오류"}
    log_file = _REPO_ROOT / "work_log.jsonl"
    if not log_file.exists():
        return {"entries": []}
    cap = min(limit, 500)
    # agent_id 필터가 있으면 더 많이 읽어서 필터 후 잘라냄
    read_n = cap if agent_id is None else min(cap * 20, 10000)
    raw_lines = _read_last_lines(log_file, read_n)
    entries = []
    for line in raw_lines:
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
        except Exception:
            continue
        if agent_id is not None:
            eid = e.get("agent_id") or e.get("agent") or ""
            if str(eid) != agent_id:
                continue
        entries.append(e)
        if len(entries) >= cap:
            break
    return {"entries": entries, "agent_id": agent_id, "count": len(entries)}


@app.get("/api/export")
def export_worklog(format: str = "csv", limit: int = 1000):
    """작업 로그 CSV/JSON 내보내기"""
    log_file = _REPO_ROOT / "work_log.jsonl"
    entries = []
    if log_file.exists():
        for line in _read_last_lines(log_file, min(limit, 5000)):
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except Exception:
                continue

    today = datetime.now().strftime("%Y%m%d")

    if format == "csv":
        fields = ["ts", "agent_id", "status", "message"]
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for e in entries:
            row = {
                "ts":       e.get("ts") or e.get("timestamp", ""),
                "agent_id": e.get("agent_id", ""),
                "status":   e.get("status") or e.get("action", ""),
                "message":  e.get("message") or e.get("prev_task") or e.get("content") or e.get("task", ""),
            }
            w.writerow(row)
        content = buf.getvalue()
        return Response(
            content=content.encode("utf-8-sig"),  # BOM — Excel 호환
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="work_log_{today}.csv"'},
        )
    else:
        content = json.dumps(
            {"entries": entries, "exported": datetime.now().isoformat()},
            ensure_ascii=False,
            indent=2,
            default=str,
        )
        return Response(
            content=content.encode("utf-8"),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="work_log_{today}.json"'},
        )


@app.get("/api/activity/24h")
def activity_24h():
    """최근 24시간 시간대별 활동 집계 (KST 기준)"""
    log_file = _REPO_ROOT / "work_log.jsonl"
    now_kst = datetime.now(KST)
    cutoff_kst = now_kst - timedelta(hours=24)

    # 시간대별 카운트 초기화 (0~23)
    hourly = {
        h: {"working": 0, "done": 0, "review": 0, "waiting": 0, "idle": 0, "total": 0}
        for h in range(24)
    }

    if log_file.exists():
        for line in _read_last_lines(log_file, 10000):
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
                ts_raw = e.get("ts") or e.get("timestamp") or ""
                if not ts_raw:
                    continue
                ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
                # KST 기준으로 통일 (naive → KST 로컬로 간주, aware → KST 변환)
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=KST)
                else:
                    ts = ts.astimezone(KST)
                if ts < cutoff_kst:
                    continue
                hour = ts.hour
                status = str(e.get("status") or "idle")
                if status in hourly[hour]:
                    hourly[hour][status] += 1
                else:
                    hourly[hour]["idle"] += 1
                hourly[hour]["total"] += 1
            except Exception:
                continue

    return {
        "hourly": hourly,
        "generated": now_kst.isoformat(),
        "window_hours": 24,
        "timezone": "KST",
    }


@app.post("/api/approval")
async def post_approval(body: dict):
    """승인/반려 처리 (update_status.py 호출)."""
    agent_id = (body.get("agentId") or "").strip()
    action   = (body.get("action")  or "").strip()
    memo     = (body.get("memo")    or "").strip()
    if not agent_id or action not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="agentId / action 필수")
    if not re.match(r'^[a-zA-Z0-9_-]+$', agent_id):
        raise HTTPException(status_code=400, detail="agentId 형식 오류")
    if memo and not re.match(r'^[^\n\r]*$', memo):
        raise HTTPException(status_code=422, detail="memo는 한 줄이어야 합니다")
    if len(memo) > 500:
        raise HTTPException(status_code=413, detail="memo가 500자를 초과합니다")
    new_status = "idle" if action == "approved" else "review"
    msg = f"{'승인' if action == 'approved' else '반려'}: {memo}" if memo else action
    try:
        subprocess.run(
            [sys.executable, str(_REPO_ROOT / "scripts" / "update_status.py"), agent_id, new_status, msg],
            cwd=str(_REPO_ROOT), timeout=5, check=True, capture_output=True
        )
        status = load_data()
        await _broadcast({"type": "status", "data": status})
        return {"ok": True, "agent_id": agent_id, "action": action}
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode(errors="replace") if e.stderr else ""
        raise HTTPException(status_code=500, detail=f"update_status 실패: {stderr or str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/gathering")
async def post_gathering(body: GatheringBody):
    """에이전트 집합/해산 명령 발행 (메타버스 + 상태 동기화)"""
    data = load_data()
    agents = data.get("agents", {})
    now = datetime.now().isoformat(timespec="seconds")

    if body.action == "gather":
        # 대상 에이전트 선택
        target_ids = []
        for aid, av in agents.items():
            team = _classify_team(aid)
            if body.team is None or team == body.team:
                target_ids.append(aid)

        # work_log 기록
        _append_work_log({
            "ts": now,
            "agent_id": "system",
            "status": "gather",
            "content": f"집합 명령: {body.message} (팀: {body.team or '전체'})",
            "machine": "api-server",
        })

        await _broadcast({
            "type": "gathering",
            "action": "gather",
            "team": body.team,
            "message": body.message,
            "target_ids": target_ids,
            "timestamp": now,
        })

        return {
            "ok": True,
            "action": "gather",
            "target_count": len(target_ids),
            "team": body.team,
        }

    elif body.action == "disperse":
        await _broadcast({
            "type": "gathering",
            "action": "disperse",
            "timestamp": now,
        })
        return {"ok": True, "action": "disperse"}

    raise HTTPException(
        status_code=400,
        detail="action은 'gather' 또는 'disperse'여야 합니다",
    )


# ── 일일 요약 ─────────────────────────────────────────────

_DAILY_SUMMARIES_DIR = _REPO_ROOT / "data" / "daily_summaries"

# 에이전트 ID → 팀 분류 규칙
_TEAM_KEYWORDS: list = [
    ("data",  ["data", "eda", "ml", "gis", "text", "visuali", "report", "realty", "statwork"]),
    ("dev",   ["frontend", "backend", "dba", "devops", "tester", "arch", "ux", "req", "tech"]),
    ("pptx",  ["pptx"]),
    ("lead",  ["orchestrator", "lead"]),
]


def _classify_team(agent_id: str) -> str:
    """agent_id 문자열로 팀 분류. 일치 없으면 'other' 반환."""
    lower = agent_id.lower()
    for team, keywords in _TEAM_KEYWORDS:
        if any(kw in lower for kw in keywords):
            return team
    return "other"


def _build_daily_summary(date_str: str) -> dict:
    """work_log.jsonl 에서 date_str(YYYY-MM-DD) 해당 항목만 집계하여 요약 반환."""
    by_status: dict = {}
    by_agent: dict = {}
    by_team: dict = {}
    hourly_count: dict = {}
    total = 0

    if _WORK_LOG.exists():
        for raw in _read_last_lines(_WORK_LOG, 100000):
            raw = raw.strip()
            if not raw:
                continue
            try:
                entry = json.loads(raw)
            except Exception:
                continue

            ts_raw = entry.get("ts") or entry.get("timestamp") or ""
            if not ts_raw:
                continue
            try:
                ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
                if ts.tzinfo is not None:
                    ts = ts.astimezone(KST).replace(tzinfo=None)
            except Exception:
                continue

            if ts.strftime("%Y-%m-%d") != date_str:
                continue

            total += 1

            # 상태 집계
            status = entry.get("status", "idle")
            by_status[status] = by_status.get(status, 0) + 1

            # 에이전트 집계
            agent_id = entry.get("agent_id") or entry.get("agent") or "unknown"
            by_agent[agent_id] = by_agent.get(agent_id, 0) + 1

            # 팀 집계
            team = _classify_team(agent_id)
            by_team[team] = by_team.get(team, 0) + 1

            # 시간대 집계
            hour = ts.hour
            hourly_count[hour] = hourly_count.get(hour, 0) + 1

    most_active_agent = max(by_agent, key=lambda k: by_agent[k]) if by_agent else None
    peak_hour = max(hourly_count, key=lambda k: hourly_count[k]) if hourly_count else None

    return {
        "date": date_str,
        "total_events": total,
        "by_status": by_status,
        "by_agent": by_agent,
        "by_team": by_team,
        "most_active_agent": most_active_agent,
        "peak_hour": peak_hour,
        "generated": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    }


@app.get("/api/daily-summary")
def get_daily_summary(date: str = ""):
    """지정 날짜(기본: 오늘)의 work_log 일일 요약 반환.

    쿼리 파라미터: date=YYYY-MM-DD (생략 시 오늘)
    """
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    # 날짜 형식 검증
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="date 형식은 YYYY-MM-DD 이어야 합니다")
    return _build_daily_summary(date)


@app.get("/api/daily-summary/list")
def list_daily_summaries():
    """저장된 일일 요약 파일 목록 반환."""
    if not _DAILY_SUMMARIES_DIR.exists():
        return {"files": [], "count": 0}
    files = sorted(
        [f.stem for f in _DAILY_SUMMARIES_DIR.glob("*.json") if f.is_file()],
        reverse=True,
    )
    return {"files": files, "count": len(files)}


async def _daily_summary_scheduler() -> None:
    """매일 자정(00:00:05)에 전날 요약을 data/daily_summaries/YYYY-MM-DD.json 으로 자동 저장."""
    while True:
        now = datetime.now()
        tomorrow = (now + timedelta(days=1)).replace(
            hour=0, minute=0, second=5, microsecond=0
        )
        await asyncio.sleep(max(0.1, (tomorrow - now).total_seconds()))
        # 전날 날짜
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        try:
            summary = _build_daily_summary(yesterday)
            _DAILY_SUMMARIES_DIR.mkdir(parents=True, exist_ok=True)
            out_file = _DAILY_SUMMARIES_DIR / f"{yesterday}.json"
            out_file.write_text(
                json.dumps(summary, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"[INFO] 일일 요약 저장 완료: {out_file}", file=sys.stderr)
        except Exception as e:
            print(f"[WARN] 일일 요약 저장 실패 ({yesterday}): {e}", file=sys.stderr)


@app.get("/api/memory/search")
async def search_memory(agent_id: str = "", query: str = "", limit: int = 10):
    """에이전트 장기 메모리 검색"""
    try:
        from mem0_client import search_experience
        results = search_experience(agent_id or None, query, limit)
        return {"results": results, "query": query, "agent_id": agent_id}
    except ImportError:
        return {"results": [], "query": query, "agent_id": agent_id, "note": "mem0_client 미설치"}
    except Exception as e:
        return {"results": [], "error": str(e)}


@app.get("/api/memory/{agent_id}")
async def get_agent_memory(agent_id: str):
    """특정 에이전트의 전체 메모리 조회"""
    try:
        from mem0_client import get_all
        results = get_all(agent_id)
        return {"agent_id": agent_id, "memories": results}
    except ImportError:
        return {"agent_id": agent_id, "memories": [], "note": "mem0_client 미설치"}
    except Exception as e:
        return {"agent_id": agent_id, "memories": [], "error": str(e)}


@app.get("/api/git-status")
def get_git_status():
    """현재 git 상태 반환 (브랜치, 최근 커밋, 변경사항 수)"""
    result = {}
    try:
        # 브랜치명
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, cwd=str(_REPO_ROOT), timeout=5
        ).stdout.strip()
        result["branch"] = branch

        # 최근 커밋
        log = subprocess.run(
            ["git", "log", "--oneline", "-1"],
            capture_output=True, text=True, cwd=str(_REPO_ROOT), timeout=5
        ).stdout.strip()
        if log and not log.startswith("fatal"):
            parts = log.split(" ", 1)
            result["last_commit_hash"] = parts[0] if parts else ""
            result["last_commit_msg"]  = parts[1] if len(parts) > 1 else ""

        # 최근 커밋 시간
        log_time = subprocess.run(
            ["git", "log", "-1", "--format=%ci"],
            capture_output=True, text=True, cwd=str(_REPO_ROOT), timeout=5
        ).stdout.strip()
        result["last_commit_time"] = log_time[:16] if log_time else ""  # YYYY-MM-DD HH:MM

        # 미커밋 변경사항 수
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, cwd=str(_REPO_ROOT), timeout=5
        ).stdout.strip()
        result["uncommitted_changes"] = len(status.splitlines()) if status else 0

        # 원격과 차이
        ahead_behind = subprocess.run(
            ["git", "rev-list", "--left-right", "--count", "HEAD...@{upstream}"],
            capture_output=True, text=True, cwd=str(_REPO_ROOT), timeout=5
        ).stdout.strip()
        if ahead_behind and not ahead_behind.startswith("fatal"):
            parts = ahead_behind.split("\t")
            try:
                result["ahead"]  = int(parts[0]) if len(parts) > 0 else 0
                result["behind"] = int(parts[1]) if len(parts) > 1 else 0
            except (ValueError, IndexError):
                result["ahead"] = 0
                result["behind"] = 0

    except Exception as e:
        result["error"] = str(e)

    result["timestamp"] = datetime.now(KST).isoformat()
    return result


_USAGE_TTL_SECONDS = 1800  # 30분마다 stats-cache.json 재읽기

@app.get("/api/usage")
def get_usage():
    """Claude Code 실제 사용량 통계 — 이 머신의 stats-cache.json 기준, 30분 TTL 자동 갱신."""
    usage_file = _REPO_ROOT / "data" / "usage.json"

    # 캐시가 TTL 이내면 그대로 반환
    if usage_file.exists():
        try:
            age = time.time() - usage_file.stat().st_mtime
            if age < _USAGE_TTL_SECONDS:
                return json.loads(usage_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    # TTL 만료 or 파일 없음 → stats-cache.json 재계산 후 저장
    try:
        sys.path.insert(0, str(_REPO_ROOT / "scripts"))
        from read_usage import read_claude_stats, compute_usage
        result = compute_usage(read_claude_stats())
        if not result.get("demo"):
            try:
                usage_file.parent.mkdir(parents=True, exist_ok=True)
                usage_file.write_text(
                    json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
                )
            except Exception:
                pass
        return result
    except Exception as e:
        # 계산 실패 시 만료된 캐시라도 반환
        if usage_file.exists():
            try:
                return json.loads(usage_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"demo": True, "error": str(e)}


@app.get("/api/automation-stats")
def get_automation_stats():
    """자동화 현황 통계 — work_log.jsonl 기반.

    반환:
      today_done: 오늘 완료된 작업 수
      workflow_phases: 워크플로우 단계 완료 수 (전체)
      automation_candidates: 반복 패턴 감지 건수
      top_agents: 오늘 가장 많이 작업한 에이전트 목록 (상위 3)
    """
    today = datetime.now().strftime("%Y-%m-%d")
    today_done = 0
    workflow_phases = 0
    automation_candidates = 0
    agent_today: dict = {}

    if _WORK_LOG.exists():
        for raw in _read_last_lines(_WORK_LOG, 100000):  # 전체 읽기 → 최근 10만 줄로 제한
            raw = raw.strip()
            if not raw:
                continue
            try:
                e = json.loads(raw)
            except Exception:
                continue

            ts_raw = e.get("ts") or e.get("timestamp") or ""
            is_today = ts_raw.startswith(today)

            action = e.get("action", "")
            status = e.get("status", "")
            aid = e.get("agent_id", "unknown")

            # 오늘 완료 작업
            if is_today and status in ("done", "idle") and action in ("status_change", "instruct", ""):
                if e.get("content") or e.get("task"):
                    today_done += 1
                    agent_today[aid] = agent_today.get(aid, 0) + 1

            # 워크플로우 단계 완료 (finish_phase.py 경유 전체)
            content = e.get("content") or e.get("task", "")
            if "완료" in content and "PHASE" in content.upper():
                workflow_phases += 1

            # 자동화 후보 감지
            if status == "automation_candidate" or action == "repeat_pattern":
                automation_candidates += 1

    top_agents = sorted(agent_today.items(), key=lambda x: -x[1])[:3]

    return {
        "today_done": today_done,
        "workflow_phases": workflow_phases,
        "automation_candidates": automation_candidates,
        "top_agents": [{"agent_id": a, "count": c} for a, c in top_agents],
        "date": today,
        "generated": datetime.now(KST).isoformat(),
    }


@app.get("/api/automation-candidates")
def get_automation_candidates(limit: int = Query(20, ge=1, le=100)):
    """반복 패턴 감지(automation_candidate) 상세 목록 — 반복 업무 자동화 검토용.
    work_log.jsonl에서 status=automation_candidate/action=repeat_pattern 항목을
    에이전트+내용 기준 dedup, 최근순 반환. (_check_instruct_repeat가 기록)"""
    seen = set()
    items = []
    if _WORK_LOG.exists():
        for raw in reversed(_read_last_lines(_WORK_LOG, 100000)):  # 최근→과거
            raw = raw.strip()
            if not raw:
                continue
            try:
                e = json.loads(raw)
            except Exception:
                continue
            if e.get("status") != "automation_candidate" and e.get("action") != "repeat_pattern":
                continue
            aid = e.get("agent_id", "unknown")
            content = e.get("content") or e.get("task", "")
            key = (aid, content)
            if key in seen:
                continue
            seen.add(key)
            items.append({
                "agent_id": aid,
                "content": content,
                "ts": e.get("ts") or e.get("timestamp", ""),
            })
            if len(items) >= limit:
                break
    return {"candidates": items, "count": len(items)}


# ════════════════════════════════════════════════════════════
# 📖 위키 API
# ════════════════════════════════════════════════════════════

def _wiki_tree() -> list:
    """MoC + notes 트리 반환"""
    tree = []
    if _WIKI_MOC.exists():
        for f in sorted(_WIKI_MOC.glob("*.md")):
            tree.append({"type": "moc", "name": f.stem, "path": f"MoC/{f.name}"})
    if _WIKI_NOTES.exists():
        for f in sorted(_WIKI_NOTES.rglob("*.md")):
            rel = f.relative_to(_WIKI_NOTES).as_posix()
            tree.append({"type": "note", "name": f.stem, "path": f"notes/{rel}"})
    return tree


@app.get("/api/wiki/tree")
def wiki_tree():
    """위키 파일 트리 (MoC + notes)"""
    return _wiki_tree()


@app.get("/api/wiki/note")
def wiki_get_note(path: str):
    """위키 노트 내용 반환. path = MoC/파일.md 또는 notes/파일.md"""
    target = (_WIKI_ROOT / path).resolve()
    # path traversal 방지
    try:
        target.relative_to(_WIKI_ROOT.resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="허용되지 않는 경로")
    if not target.exists() or not target.suffix == ".md":
        raise HTTPException(status_code=404, detail="노트를 찾을 수 없습니다")
    return {"path": path, "content": target.read_text(encoding="utf-8"), "name": target.stem}


@app.put("/api/wiki/note")
async def wiki_put_note(request: Request):
    """위키 노트 저장 (PUT body: {path, content})"""
    body = await request.json()
    path = body.get("path", "").strip()
    content = body.get("content", "")
    if not path or not path.endswith(".md"):
        raise HTTPException(status_code=400, detail="유효한 .md 경로 필요")
    target = (_WIKI_ROOT / path).resolve()
    try:
        target.relative_to(_WIKI_ROOT.resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="허용되지 않는 경로")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return {"ok": True, "path": path}


@app.get("/api/wiki/search")
def wiki_search(q: str = ""):
    """위키 전문 검색 (제목·내용 매칭)"""
    if not q or len(q) < 2:
        return {"results": []}
    q_lower = q.lower()
    results = []
    for f in list(_WIKI_NOTES.rglob("*.md")) + list(_WIKI_MOC.glob("*.md")):
        try:
            text = f.read_text(encoding="utf-8")
        except Exception:
            continue
        in_title = q_lower in f.stem.lower()
        in_body  = q_lower in text.lower()
        if in_title or in_body:
            # 매칭 줄 발췌
            snippet = ""
            for line in text.splitlines():
                if q_lower in line.lower():
                    snippet = line.strip()[:120]
                    break
            if f.is_relative_to(_WIKI_NOTES):
                rel = "notes/" + f.relative_to(_WIKI_NOTES).as_posix()
            else:
                rel = f"MoC/{f.name}"
            results.append({"path": rel, "name": f.stem, "snippet": snippet,
                             "score": (2 if in_title else 0) + (1 if in_body else 0)})
    results.sort(key=lambda x: -x["score"])
    return {"results": results[:30]}


# ════════════════════════════════════════════════════════════
# 📁 프로젝트 API (issues 위의 상위 묶음)
# ════════════════════════════════════════════════════════════

def _load_projects() -> dict:
    if not _PROJECTS_FILE.exists():
        return {"seq": 0, "projects": {}}
    try:
        with _projects_lock:
            return json.loads(_PROJECTS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"seq": 0, "projects": {}}


def _save_projects(data: dict) -> None:
    tmp = _PROJECTS_FILE.with_suffix(".tmp")
    with _projects_lock:
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        try:
            tmp.replace(_PROJECTS_FILE)
        except PermissionError:
            _PROJECTS_FILE.unlink(missing_ok=True)
            tmp.replace(_PROJECTS_FILE)


def _project_wiki_path(project_id: str) -> Path:
    return _WIKI_NOTES / "projects" / f"{project_id}.md"


def _sync_project_to_wiki(proj: dict) -> None:
    """프로젝트 상태를 wiki/notes/projects/<id>.md 에 동기화"""
    p = _project_wiki_path(proj["id"])
    p.parent.mkdir(parents=True, exist_ok=True)
    issues_data = _load_issues()
    linked = [i for i in issues_data.get("issues", {}).values()
              if i.get("projectId") == proj["id"]]
    done_c    = sum(1 for i in linked if i.get("status") == "done")
    active_c  = sum(1 for i in linked if i.get("status") not in ("done", "cancelled"))
    progress  = int(done_c / len(linked) * 100) if linked else 0
    issue_lines = "\n".join(
        f"- [[issue-{i['id']}|{i['id']}]] [{i.get('status')}] {i.get('title','')[:50]}"
        for i in linked
    ) or "_이슈 없음_"
    content = f"""---
name: {proj["id"]}
type: project
domain: {proj.get("domain", "")}
status: {proj.get("status", "active")}
updated: {datetime.now(KST).strftime("%Y-%m-%d")}
tags: [project]
---

# {proj.get("title", proj["id"])}

{proj.get("description", "")}

## 진행 현황
- 전체 이슈: {len(linked)}건 / 완료: {done_c}건 / 진행중: {active_c}건
- 진행률: {progress}%

## 연결 이슈
{issue_lines}

## 로그
{proj.get("log", "_로그 없음_")}
"""
    p.write_text(content, encoding="utf-8")


class ProjectCreate(BaseModel):
    title: str
    description: str = ""
    domain: str = ""
    status: str = "active"


class ProjectUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    domain: str | None = None
    log: str | None = None


@app.get("/api/projects")
def list_projects():
    data = _load_projects()
    return list(data.get("projects", {}).values())


@app.post("/api/projects")
async def create_project(body: ProjectCreate):
    data = _load_projects()
    data["seq"] = data.get("seq", 0) + 1
    pid = f"PRJ-{data['seq']}"
    now = datetime.now(KST).strftime("%Y-%m-%dT%H:%M:%S")
    proj = {"id": pid, "title": body.title, "description": body.description,
            "domain": body.domain, "status": body.status,
            "created": now, "updated": now, "log": ""}
    data["projects"][pid] = proj
    _save_projects(data)
    _sync_project_to_wiki(proj)
    await _broadcast({"type": "project_update", "action": "create", "project": proj})
    return proj


@app.patch("/api/projects/{project_id}")
async def update_project(project_id: str, body: ProjectUpdate):
    data = _load_projects()
    proj = data.get("projects", {}).get(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail=f"프로젝트 '{project_id}' 없음")
    for field, value in body.model_dump(exclude_none=True).items():
        proj[field] = value
    proj["updated"] = datetime.now(KST).strftime("%Y-%m-%dT%H:%M:%S")
    data["projects"][project_id] = proj
    _save_projects(data)
    _sync_project_to_wiki(proj)
    await _broadcast({"type": "project_update", "action": "update", "project": proj})
    return proj


@app.get("/api/projects/{project_id}")
def get_project(project_id: str):
    data = _load_projects()
    proj = data.get("projects", {}).get(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail=f"프로젝트 '{project_id}' 없음")
    return proj


# ════════════════════════════════════════════════════════════
# 📊 보고서 → 위키 마크다운 동기화
# ════════════════════════════════════════════════════════════

@app.post("/api/wiki/sync-report")
async def wiki_sync_report(request: Request):
    """HTML 보고서 → wiki/notes/reports/<date>.md 마크다운 변환·저장.
    body: {date: 'YYYY-MM-DD', title: '...', summary: '...', sections: [{heading, content}]}"""
    body = await request.json()
    date_str = body.get("date", datetime.now(KST).strftime("%Y-%m-%d"))
    title    = body.get("title", f"{date_str} 보고서")
    summary  = body.get("summary", "")
    sections = body.get("sections", [])
    p = _WIKI_NOTES / "reports" / f"{date_str}.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"---\nname: report-{date_str}\ntype: report\ndate: {date_str}\ntags: [report]\n---\n",
             f"# {title}\n", f"{summary}\n"]
    for sec in sections:
        lines.append(f"\n## {sec.get('heading','')}\n{sec.get('content','')}\n")
    p.write_text("\n".join(lines), encoding="utf-8")
    return {"ok": True, "path": f"notes/reports/{date_str}.md"}


@app.get("/api/wiki/reports")
def wiki_reports():
    """위키에 저장된 보고서 목록"""
    rep_dir = _WIKI_NOTES / "reports"
    if not rep_dir.exists():
        return []
    return [{"path": f"notes/reports/{f.name}", "name": f.stem, "date": f.stem}
            for f in sorted(rep_dir.glob("*.md"), reverse=True)]


# ════════════════════════════════════════════════════════════
# 🔗 이슈 완료 → 위키 레슨런
# ════════════════════════════════════════════════════════════

def _issue_to_wiki(issue: dict) -> None:
    """완료 이슈를 wiki/notes/issues/<id>.md 에 기록 (레슨런)"""
    p = _WIKI_NOTES / "issues" / f"issue-{issue['id']}.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():  # 이미 있으면 업데이트만
        return
    comments_md = "\n".join(
        f"- **{c.get('author','?')}** ({c.get('ts','')[:10]}): {c.get('text','')}"
        for c in issue.get("comments", [])
    ) or "_없음_"
    content = f"""---
name: issue-{issue['id']}
type: decision
domain: {issue.get('assigneeId', '')}
issue_id: {issue['id']}
status: {issue.get('status', '')}
priority: {issue.get('priority', '')}
updated: {issue.get('updated', '')[:10]}
tags: [issue, done]
---

# [{issue['id']}] {issue.get('title', '')}

{issue.get('description', '_설명 없음_')}

## 처리 결과
- 담당: {issue.get('assigneeId', '미지정')}
- 우선순위: {issue.get('priority', '')}
- 완료일: {issue.get('updated', '')[:10]}

## 코멘트
{comments_md}
"""
    p.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    import uvicorn
    _port = int(os.environ.get("AGENTS_API_PORT", "8765"))
    print(f"Agent Status API 서버 시작: http://127.0.0.1:{_port}")
    uvicorn.run(app, host="127.0.0.1", port=_port, log_level="warning")
