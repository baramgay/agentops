#!/usr/bin/env python3
"""reports/ 폴더의 HTML 보고서 목록을 index.html로 자동 생성"""
from pathlib import Path
from datetime import datetime

REPORTS_DIR = Path(__file__).parent.parent / "reports"


def _fmt_label(name: str) -> tuple[str, str]:
    """파일명 줄기에서 (아이콘, 레이블) 반환"""
    if name.startswith("monthly-"):
        return "📅", f"월간 보고서 ({name.replace('monthly-', '')})"
    if name.startswith("weekly-"):
        return "📋", f"주간 보고서 ({name.replace('weekly-', '')})"
    # 날짜형 파일명(2026-05-28)은 보기 좋게 변환
    try:
        dt = datetime.strptime(name, "%Y-%m-%d")
        weekdays = ["월", "화", "수", "목", "금", "토", "일"]
        wd = weekdays[dt.weekday()]
        return "📊", f"일간 보고서 ({dt.year}년 {dt.month}월 {dt.day}일 ({wd}))"
    except ValueError:
        pass
    return "📊", f"일간 보고서 ({name})"


def generate_index():
    reports = sorted(
        [f for f in REPORTS_DIR.glob("*.html") if f.name != "index.html"],
        reverse=True,
    )

    rows = []
    for r in reports:
        icon, label = _fmt_label(r.stem)
        size_kb = r.stat().st_size // 1024
        mtime = datetime.fromtimestamp(r.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        rows.append(
            f"<tr>"
            f'<td>{icon} <a href="{r.name}">{label}</a></td>'
            f'<td class="center">{mtime}</td>'
            f'<td class="center">{size_kb} KB</td>'
            f"</tr>"
        )

    rows_html = "\n".join(rows) if rows else (
        '<tr><td colspan="3" class="muted">보고서 없음</td></tr>'
    )
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>일간 보고서 목록 — Your Organization</title>
<style>
  body {{ font-family: "Malgun Gothic", sans-serif; font-size: 14px; background: #f5f7fa; color: #1a1a2e; }}
  .wrap {{ max-width: 720px; margin: 40px auto; background: #fff; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); overflow: hidden; }}
  .hd {{ background: linear-gradient(135deg, #1a3a6e 0%, #2557a7 100%); color: #fff; padding: 22px 28px; }}
  .hd h1 {{ font-size: 17px; margin-bottom: 4px; }}
  .hd p {{ font-size: 12px; opacity: 0.8; margin: 0; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th {{ background: #f0f4ff; color: #1a3a6e; padding: 10px 20px; text-align: left; font-weight: 700; font-size: 13px; }}
  td {{ padding: 9px 20px; border-bottom: 1px solid #eee; }}
  tr:last-child td {{ border-bottom: none; }}
  a {{ color: #2557a7; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  .center {{ text-align: center; }}
  .muted {{ color: #aaa; font-style: italic; }}
  .badge {{ background: #e8f0fe; color: #2557a7; border-radius: 10px; padding: 1px 8px; font-size: 11px; font-weight: 700; }}
  .footer {{ text-align: center; font-size: 11px; color: #bbb; padding: 14px; }}
</style>
</head>
<body>
<div class="wrap">
  <div class="hd">
    <h1>Your Organization 일간 업무 보고서 목록
      <span class="badge">{len(reports)}개</span>
    </h1>
    <p>최종 갱신: {now_str}</p>
  </div>
  <table>
    <thead>
      <tr>
        <th>보고서</th>
        <th class="center">생성 시각</th>
        <th class="center">크기</th>
      </tr>
    </thead>
    <tbody>
{rows_html}
    </tbody>
  </table>
  <div class="footer">에이전트 시스템 자동 생성</div>
</div>
</body>
</html>"""

    out = REPORTS_DIR / "index.html"
    out.write_text(html, encoding="utf-8")
    print(f"[reports_index] {len(reports)}개 보고서 인덱스 생성: {out}")


if __name__ == "__main__":
    generate_index()
