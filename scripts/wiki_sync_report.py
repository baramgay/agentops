"""
보고서 → 위키 마크다운 동기화 공통 헬퍼.

각 보고서 스크립트 끝에서 호출:
    from wiki_sync_report import sync_to_wiki
    sync_to_wiki(date_str, title, summary, sections)

sections = [{"heading": "KPI", "content": "..."}, ...]
API 서버가 꺼져 있으면 조용히 무시(보고서 생성에 영향 없음).
"""
import sys
import json
import urllib.request
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

_API = "http://127.0.0.1:8765"
_WIKI_REPORTS = Path(__file__).parent.parent / "wiki" / "notes" / "reports"


def sync_to_wiki(date_str: str, title: str, summary: str, sections: list,
                 report_type: str = "daily") -> bool:
    """
    보고서를 wiki/notes/reports/<date>.md 에 동기화.
    API 서버 경유 우선 → 실패 시 파일 직접 쓰기 폴백.
    반환: 성공 여부.
    """
    # 1) API 서버 경유
    try:
        payload = json.dumps({
            "date": date_str, "title": title,
            "summary": summary, "sections": sections,
        }, ensure_ascii=False).encode()
        req = urllib.request.Request(
            f"{_API}/api/wiki/sync-report",
            data=payload, method="POST",
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=5)
        print(f"  [위키] {date_str}.md 동기화 완료 (API)")
        return True
    except Exception:
        pass  # 서버 꺼짐 → 파일 직접 쓰기

    # 2) 직접 파일 쓰기 폴백
    try:
        _WIKI_REPORTS.mkdir(parents=True, exist_ok=True)
        lines = [
            f"---\nname: report-{date_str}\ntype: report",
            f"report_type: {report_type}\ndate: {date_str}\ntags: [report]\n---\n",
            f"# {title}\n", f"{summary}\n",
        ]
        for sec in sections:
            lines.append(f"\n## {sec.get('heading','')}\n{sec.get('content','')}\n")
        (_WIKI_REPORTS / f"{date_str}.md").write_text("\n".join(lines), encoding="utf-8")
        print(f"  [위키] {date_str}.md 동기화 완료 (직접 쓰기)")
        return True
    except Exception as e:
        print(f"  [위키] 동기화 실패(무시): {e}", file=sys.stderr)
        return False
