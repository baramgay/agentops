"""
이슈 트래커 native CLI — GNI-N 이슈 생성·조회

사용법:
  생성: python scripts/issue_create.py "제목" "내용" [agent_id] [priority]
  목록: python scripts/issue_create.py --list [status]
  상세: python scripts/issue_create.py --get GNI-N

priority 값: urgent high medium low (기본: medium)
status  값: backlog todo in_progress in_review done cancelled

예시:
  python scripts/issue_create.py "공공데이터 API 오류" "포털 응답 500" data-collector high
  python scripts/issue_create.py --list in_progress
  python scripts/issue_create.py --get GNI-3
"""

import sys
import json
import urllib.request as _ur
import urllib.error
import urllib.parse

# Windows 콘솔(cp949)에서 이모지·한글 출력 시 UnicodeEncodeError 방지
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

API_BASE = "http://127.0.0.1:8765"


def _req(method, path, body=None):
    url = API_BASE + path
    data = json.dumps(body, ensure_ascii=False).encode() if body else None
    req = _ur.Request(url, data=data, method=method,
                      headers={"Content-Type": "application/json"})
    try:
        with _ur.urlopen(req, timeout=5) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        # 서버는 응답했으나 4xx/5xx — 상세 메시지 표시 (404=이슈 없음, 422=잘못된 값)
        try:
            detail = json.loads(e.read().decode()).get("detail", str(e))
        except Exception:
            detail = str(e)
        print(f"[오류] {detail}")
        sys.exit(1)
    except Exception as e:
        print(f"[오류] API 서버 연결 실패: {e}")
        print("  → scripts\\start_api.bat 으로 FastAPI 서버를 먼저 시작하세요.")
        sys.exit(1)


def cmd_create(args):
    if len(args) < 1:
        print("사용법: issue_create.py \"제목\" [\"내용\"] [agent_id] [priority]")
        sys.exit(1)
    title       = args[0]
    description = args[1] if len(args) > 1 else ""
    assignee_id = args[2] if len(args) > 2 else ""
    priority    = args[3] if len(args) > 3 else "medium"

    payload = {"title": title, "description": description, "priority": priority}
    if assignee_id:
        payload["assigneeId"] = assignee_id

    issue = _req("POST", "/api/issues", payload)
    print(f"✅ 이슈 생성: {issue['id']} — {issue['title']}")
    print(f"   담당자: {issue.get('assigneeId','미지정')}  우선순위: {issue.get('priority')}")


def cmd_list(status_filter=None):
    path = "/api/issues"
    if status_filter:
        path += "?" + urllib.parse.urlencode({"status": status_filter})
    issues = _req("GET", path)
    if not issues:
        print("이슈 없음.")
        return
    for iss in issues:
        tag = f"[{iss.get('status','?')}]"
        print(f"  {iss['id']:8s} {tag:14s} {iss['title'][:50]}")


def cmd_get(issue_id):
    match = _req("GET", f"/api/issues/{urllib.parse.quote(issue_id)}")
    print(json.dumps(match, ensure_ascii=False, indent=2))


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(0)

    if args[0] == "--list":
        cmd_list(args[1] if len(args) > 1 else None)
    elif args[0] == "--get":
        if len(args) < 2:
            print("사용법: issue_create.py --get GNI-N")
            sys.exit(1)
        cmd_get(args[1])
    else:
        cmd_create(args)


if __name__ == "__main__":
    main()
