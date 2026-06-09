"""
GitHub Issues 양방향 동기화 — GNI 이슈 트래커 ↔ GitHub Issues

설계:
- 인증: Fine-grained PAT. config.local.json의 github.token 또는 환경변수 GITHUB_TOKEN.
  repo: github.repo 또는 환경변수 GITHUB_REPO ("owner/name").
- 의존성 없음(stdlib urllib). api_server가 이슈 load/save 함수를 주입(sync 시).
- 연결: GNI 이슈 body에 `<!-- gni-id:GNI-N -->` 마커 삽입 + GNI 이슈에 github_number 저장.
- 매핑: status→state(done/cancelled=closed, 그 외 open) + labels(gni:status:*, gni:priority:*, gni:assignee:*).
- 충돌: 이슈 단위 last-write-wins (GitHub updated_at vs GNI updated, 둘 다 UTC epoch 비교).
- 보안: 토큰은 반환·로그에 절대 미포함.

CLI(테스트용):
  python scripts/github_sync.py --status
  python scripts/github_sync.py --sync
"""

import os
import re
import sys
import json
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

_API = "https://api.github.com"
_KST = timezone(timedelta(hours=9))
_MARKER_RE = re.compile(r"<!--\s*gni-id:\s*(GNI-\d+)\s*-->")
_COMMENT_MARKER_RE = re.compile(r"<!--\s*gni-comment:\s*([0-9T:\-]+)\s*-->")
_REPO_ROOT = Path(__file__).resolve().parent.parent


def _gh_ts_to_kst(ts: str) -> str:
    """GitHub ISO8601(UTC 'Z') → KST 'YYYY-MM-DDTHH:MM:SS' 문자열."""
    try:
        dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        return dt.astimezone(_KST).strftime("%Y-%m-%dT%H:%M:%S")
    except Exception:
        return datetime.now(_KST).strftime("%Y-%m-%dT%H:%M:%S")


# ── 설정 ────────────────────────────────────────────────
def get_config() -> dict:
    """github 설정 반환: {token, repo, sync_enabled, sync_interval_min}. 환경변수가 config보다 우선.
    sync_interval_min: 자동 동기화 주기(분). 0이면 자동 동기화 비활성(수동만)."""
    cfg = {"token": "", "repo": "", "sync_enabled": True, "sync_interval_min": 15}
    try:
        local = _REPO_ROOT / "config.local.json"
        if local.exists():
            data = json.loads(local.read_text(encoding="utf-8"))
            gh = data.get("github", {}) or {}
            cfg["token"] = gh.get("token", "") or ""
            cfg["repo"] = gh.get("repo", "") or ""
            if "sync_enabled" in gh:
                cfg["sync_enabled"] = bool(gh.get("sync_enabled"))
            if "sync_interval_min" in gh:
                try:
                    cfg["sync_interval_min"] = int(gh.get("sync_interval_min"))
                except (TypeError, ValueError):
                    pass
    except Exception:
        pass
    cfg["token"] = os.getenv("GITHUB_TOKEN", cfg["token"]) or cfg["token"]
    cfg["repo"] = os.getenv("GITHUB_REPO", cfg["repo"]) or cfg["repo"]
    _env_iv = os.getenv("GITHUB_SYNC_INTERVAL_MIN")
    if _env_iv:
        try:
            cfg["sync_interval_min"] = int(_env_iv)
        except ValueError:
            pass
    return cfg


def is_configured(cfg: dict | None = None) -> bool:
    cfg = cfg or get_config()
    return bool(cfg.get("token")) and bool(cfg.get("repo"))


# ── GitHub REST 호출 ────────────────────────────────────
def gh_request(method: str, path: str, token: str, body: dict | None = None):
    """GitHub API 호출 → (status_code, parsed_json). 네트워크 오류 시 예외."""
    url = path if path.startswith("http") else _API + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "gni-agent-sync",
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read().decode()
            return r.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors="ignore")
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = {"message": raw}
        return e.code, parsed


def get_rate_limit(cfg: dict) -> dict:
    status, body = gh_request("GET", "/rate_limit", cfg["token"])
    if status == 200 and isinstance(body, dict):
        core = body.get("resources", {}).get("core", {})
        return {"remaining": core.get("remaining"), "limit": core.get("limit"), "reset": core.get("reset")}
    return {"error": f"HTTP {status}"}


def list_remote(cfg: dict) -> list:
    """repo의 모든 이슈(state=all) — PR 제외. 페이지네이션."""
    out = []
    for page in range(1, 11):  # 최대 1000건
        status, body = gh_request(
            "GET", f"/repos/{cfg['repo']}/issues?state=all&per_page=100&page={page}", cfg["token"])
        if status != 200 or not isinstance(body, list) or not body:
            break
        for it in body:
            if "pull_request" in it:  # PR 제외
                continue
            out.append(it)
        if len(body) < 100:
            break
    return out


# ── 매핑 헬퍼 ────────────────────────────────────────────
def _gni_to_state(status: str) -> str:
    return "closed" if status in ("done", "cancelled") else "open"


def _gni_labels(issue: dict) -> list:
    labels = [f"gni:status:{issue.get('status','backlog')}",
              f"gni:priority:{issue.get('priority','medium')}"]
    if issue.get("assigneeId"):
        labels.append(f"gni:assignee:{issue['assigneeId']}")
    return labels


def _body_with_marker(issue: dict) -> str:
    desc = issue.get("description", "") or ""
    return f"{desc}\n\n<!-- gni-id:{issue['id']} -->"


def _parse_marker(body: str) -> str | None:
    m = _MARKER_RE.search(body or "")
    return m.group(1) if m else None


def _label_value(labels: list, prefix: str) -> str | None:
    for l in labels:
        name = l.get("name", "") if isinstance(l, dict) else str(l)
        if name.startswith(prefix):
            return name[len(prefix):]
    return None


def _epoch_utc_from_github(ts: str) -> float:
    # "2026-06-02T10:00:00Z"
    try:
        return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()
    except Exception:
        return 0.0


def _epoch_utc_from_gni(ts: str) -> float:
    # "2026-06-02T19:00:00" (KST naive)
    try:
        return datetime.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=_KST).timestamp()
    except Exception:
        return 0.0


def _remote_to_gni_fields(remote: dict) -> dict:
    """GitHub 이슈 → GNI 필드(부분).
    상태 매핑: 네이티브 state(open/closed)를 우선 — 사용자가 GitHub UI에서 열기/닫기를
    토글하면 gni:status 라벨이 stale될 수 있으므로, state와 라벨이 모순되면 state를 따른다."""
    labels = remote.get("labels", [])
    status_label = _label_value(labels, "gni:status:")
    if remote.get("state") == "closed":
        # 닫힘 → 종료 상태. 라벨이 done/cancelled면 유지, 아니면 done.
        status = status_label if status_label in ("done", "cancelled") else "done"
    else:
        # 열림 → 비종료 상태. 라벨이 비종료면 유지, done/cancelled(stale)·없음이면 todo.
        status = status_label if (status_label and status_label not in ("done", "cancelled")) else "todo"
    priority = _label_value(labels, "gni:priority:") or "medium"
    assignee = _label_value(labels, "gni:assignee:") or ""
    body = remote.get("body", "") or ""
    desc = _MARKER_RE.sub("", body).rstrip()
    return {
        "title": remote.get("title", "(제목 없음)"),
        "description": desc,
        "status": status,
        "priority": priority,
        "assigneeId": assignee,
    }


def _sync_comments(cfg, number, issue, result):
    """링크된 이슈의 댓글 양방향 동기화. 로컬 데이터를 변경했으면 True 반환(touched 추적용).
    - pull: 로컬에 없는 GitHub 댓글 가져오기 (우리가 푸시한 marker 댓글은 gh_id만 연결).
    - push: gh_id 없는 로컬 댓글을 GitHub에 게시 (marker로 echo 재유입 방지).
    중복 방지는 로컬 댓글의 gh_id 추적 + gni-comment marker(ts)로 수행."""
    token, repo = cfg["token"], cfg["repo"]
    status, gh_comments = gh_request(
        "GET", f"/repos/{repo}/issues/{number}/comments?per_page=100", token)
    if status != 200 or not isinstance(gh_comments, list):
        return False
    changed = False
    local = issue.setdefault("comments", [])
    local_gh_ids = set(c.get("gh_id") for c in local if c.get("gh_id"))
    # pull
    for gc in gh_comments:
        gid = gc.get("id")
        if gid in local_gh_ids:
            continue
        body = gc.get("body", "") or ""
        mk = _COMMENT_MARKER_RE.search(body)
        if mk:
            # 우리가 푸시했던 댓글 — 해당 로컬 댓글에 gh_id 연결 (재유입 금지)
            ts = mk.group(1)
            for c in local:
                if c.get("ts") == ts and not c.get("gh_id"):
                    c["gh_id"] = gid
                    changed = True
                    break
            continue
        # GitHub에서 직접 작성된 댓글 → 로컬로 가져오기
        local.append({
            "author": (gc.get("user") or {}).get("login", "github"),
            "text": body.rstrip(),
            "ts": _gh_ts_to_kst(gc.get("created_at", "")),
            "gh_id": gid,
        })
        changed = True
        result["pulled_comments"] = result.get("pulled_comments", 0) + 1
    # push — gh_id 없는 로컬 댓글
    for c in local:
        if c.get("gh_id"):
            continue
        marker = f"\n\n<!-- gni-comment:{c.get('ts', '')} -->"
        st, created = gh_request(
            "POST", f"/repos/{repo}/issues/{number}/comments", token,
            {"body": (c.get("text", "") or "") + marker})
        if st in (200, 201) and isinstance(created, dict):
            c["gh_id"] = created.get("id")
            changed = True
            result["pushed_comments"] = result.get("pushed_comments", 0) + 1
    return changed


# ── 동기화 오케스트레이션 ────────────────────────────────
def sync(cfg, load_issues, save_issues, next_issue_id, append_event):
    """양방향 동기화. 의존성 주입(api_server의 이슈 load/save/id/event).
    반환: 요약 카운트 dict."""
    result = {"created_remote": 0, "updated_remote": 0, "created_local": 0,
              "updated_local": 0, "linked": 0, "pulled_comments": 0,
              "pushed_comments": 0, "errors": []}
    token = cfg["token"]
    repo = cfg["repo"]

    remotes = list_remote(cfg)
    # 마커 기준 인덱스 (GNI-N → remote)
    remote_by_gni = {}
    remote_unlinked = []
    for r in remotes:
        gid = _parse_marker(r.get("body", ""))
        if gid:
            remote_by_gni[gid] = r
        else:
            remote_unlinked.append(r)

    data = load_issues()
    issues = data.get("issues", {})
    touched = set()  # 동기화가 로컬을 변경한 이슈 id (저장 시 병합 대상)

    # 1) 로컬 → 원격 (생성/갱신) + 링크된 항목 충돌 해결
    for gid, issue in list(issues.items()):
        num = issue.get("github_number")
        remote = remote_by_gni.get(gid) or (
            next((r for r in remotes if r.get("number") == num), None) if num else None)
        try:
            if not remote:
                # 원격에 없음 → 생성 (cancelled는 closed로 생성)
                status, created = gh_request("POST", f"/repos/{repo}/issues", token, {
                    "title": issue.get("title", "(제목 없음)"),
                    "body": _body_with_marker(issue),
                    "labels": _gni_labels(issue),
                })
                if status in (200, 201) and isinstance(created, dict):
                    issue["github_number"] = created["number"]
                    touched.add(gid)
                    if _gni_to_state(issue.get("status", "")) == "closed":
                        gh_request("PATCH", f"/repos/{repo}/issues/{created['number']}", token, {"state": "closed"})
                    result["created_remote"] += 1
                    # D: cancelled(소프트삭제)는 댓글 동기화 스킵 (불필요한 호출 축소)
                    if issue.get("status") != "cancelled":
                        _sync_comments(cfg, created["number"], issue, result)
                else:
                    result["errors"].append(f"{gid} 원격생성 실패 HTTP {status}")
                continue
            # 링크됨 — 타임스탬프 last-write-wins (동일하면 skip → pull/push 핑퐁 방지)
            if issue.get("github_number") != remote["number"]:
                issue["github_number"] = remote["number"]
                touched.add(gid)
            result["linked"] += 1
            r_epoch = _epoch_utc_from_github(remote.get("updated_at", ""))
            l_epoch = _epoch_utc_from_gni(issue.get("updated", ""))
            if r_epoch > l_epoch:
                # 원격이 최신 → 로컬 갱신. updated를 원격 시각에 맞춰 핑퐁 방지.
                fields = _remote_to_gni_fields(remote)
                changed = any(issue.get(k) != v for k, v in fields.items())
                if changed:
                    issue.update(fields)
                    # 원격 updated_at(UTC) → KST 문자열로 저장해 다음 동기화에서 동일 판정
                    issue["updated"] = datetime.fromtimestamp(r_epoch, _KST).strftime("%Y-%m-%dT%H:%M:%S")
                    append_event("github_pull", gid, {"github_number": remote["number"]})
                    result["updated_local"] += 1
                    touched.add(gid)
            elif l_epoch > r_epoch:
                # 로컬이 최신 → 원격 갱신
                gh_request("PATCH", f"/repos/{repo}/issues/{remote['number']}", token, {
                    "title": issue.get("title", "(제목 없음)"),
                    "body": _body_with_marker(issue),
                    "state": _gni_to_state(issue.get("status", "")),
                    "labels": _gni_labels(issue),
                })
                result["updated_remote"] += 1
            # r_epoch == l_epoch → 동기화됨, 아무것도 안 함
            # 댓글 동기화 (링크된 이슈, cancelled 제외 — D)
            if issue.get("status") != "cancelled":
                if _sync_comments(cfg, remote["number"], issue, result):
                    touched.add(gid)
        except Exception as e:
            result["errors"].append(f"{gid}: {e}")

    # 2) 원격 전용(마커 없음) → 로컬 생성 (GitHub에서 직접 만든 이슈 가져오기)
    for r in remote_unlinked:
        try:
            new_id = next_issue_id(data)
            now = datetime.now(_KST).strftime("%Y-%m-%dT%H:%M:%S")
            fields = _remote_to_gni_fields(r)
            issue = {"id": new_id, **fields, "labels": ["github"],
                     "created": now, "updated": now, "comments": [],
                     "github_number": r["number"]}
            data["issues"][new_id] = issue
            touched.add(new_id)
            append_event("github_import", new_id, {"github_number": r["number"]})
            # 마커를 원격 body에 주입(다음 동기화부터 링크 인식)
            gh_request("PATCH", f"/repos/{repo}/issues/{r['number']}", token, {
                "body": _body_with_marker(issue)})
            result["created_local"] += 1
            # GitHub에서 작성된 기존 댓글 가져오기
            _sync_comments(cfg, r["number"], issue, result)
        except Exception as e:
            result["errors"].append(f"remote#{r.get('number')}: {e}")

    # 저장 직전 재로딩 후 병합 — 동기화 네트워크 구간(수초) 동안 발생한 외부 CRUD 변경 보존.
    # 동기화가 실제로 만진 이슈(touched)만 동기화 결과로 덮어쓰고,
    # 그 사이 새로 생성/변경된 다른 이슈는 fresh 버전을 유지. seq는 양쪽 최대값.
    try:
        fresh = load_issues()
        fresh_issues = dict(fresh.get("issues", {}))
        for tid in touched:
            if tid in data["issues"]:
                fresh_issues[tid] = data["issues"][tid]
        merged = {"seq": max(data.get("seq", 0), fresh.get("seq", 0)), "issues": fresh_issues}
        # data의 기타 최상위 키 보존
        for k, v in data.items():
            if k not in ("seq", "issues"):
                merged.setdefault(k, v)
        save_issues(merged)
    except Exception:
        save_issues(data)  # 병합 실패 시 폴백 (기존 동작)
    return result


# ── CLI (standalone 테스트) ─────────────────────────────
def _standalone_io():
    """CLI 단독 실행 시 issues.json 직접 read/write."""
    ipath = _REPO_ROOT / "issues.json"

    def _load():
        if ipath.exists():
            return json.loads(ipath.read_text(encoding="utf-8"))
        return {"seq": 0, "issues": {}}

    def _save(d):
        ipath.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")

    def _next(d):
        d["seq"] = d.get("seq", 0) + 1
        return f"GNI-{d['seq']}"

    def _event(action, gid, payload):
        pass

    return _load, _save, _next, _event


def main():
    args = sys.argv[1:]
    cfg = get_config()
    if not is_configured(cfg):
        print("[오류] GitHub 미설정 — config.local.json의 github.token/repo 또는 GITHUB_TOKEN/GITHUB_REPO 환경변수 필요")
        sys.exit(1)
    if args and args[0] == "--status":
        print(json.dumps({"repo": cfg["repo"], "rate_limit": get_rate_limit(cfg)}, ensure_ascii=False, indent=2))
    elif args and args[0] == "--sync":
        load, save, nxt, ev = _standalone_io()
        res = sync(cfg, load, save, nxt, ev)
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
