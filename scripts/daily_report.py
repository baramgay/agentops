"""
daily_report.py — Your Organization AI 에이전트 일간 업무 보고서 생성기
실행: python scripts/daily_report.py [--date YYYY-MM-DD]
"""

import json
import sys
import argparse
from datetime import datetime, date, timedelta
from pathlib import Path
from collections import defaultdict

# ── 경로 설정 ──────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
WORK_LOG = ROOT / "work_log.jsonl"
STATUS_JSON = ROOT / "agent_status.json"
REPORTS_DIR = ROOT / "reports"

# ── 에이전트 한글 레이블 ────────────────────────────────────────────────────────
AGENT_LABELS = {
    "orchestrator": "총괄 지휘관",
    "lead-data": "데이터 팀 리드",
    "lead-dev": "개발 팀 리드",
    "lead-pptx": "PPTX 팀 리드",
    "data-collector": "데이터 수집",
    "data-cleaner": "데이터 정제",
    "eda-analyst": "탐색 분석",
    "statistician": "통계 분석",
    "ml-engineer": "기계학습",
    "deep-learning": "딥러닝",
    "gis-specialist": "GIS 분석",
    "text-analyst": "텍스트 분석",
    "visualizer": "시각화",
    "reporter": "보고서 작성",
    "requirements": "요구사항 정의",
    "ux-designer": "UX 설계",
    "frontend": "프론트엔드",
    "backend": "백엔드",
    "dba": "데이터베이스",
    "security": "보안 검토",
    "tester-unit": "단위 테스트",
    "tester-qa": "QA 테스트",
    "tester": "통합 테스트",
    "devops": "배포/CI-CD",
    "tech-writer": "기술 문서",
    "architect": "시스템 설계",
    "statworkbench": "통계 패키지",
    "pptx-planner": "PPTX 기획",
    "pptx-content": "PPTX 콘텐츠",
    "pptx-designer": "PPTX 디자인",
    "pptx-builder": "PPTX 빌드",
    "pptx-reviewer": "PPTX 검토",
    "realty-analyst": "부동산 분석",
}

TEAM_MAP = {
    "orchestrator": "총괄",
    "lead-data": "데이터팀",
    "lead-dev": "개발팀",
    "lead-pptx": "PPTX팀",
    "data-collector": "데이터팀",
    "data-cleaner": "데이터팀",
    "eda-analyst": "데이터팀",
    "statistician": "데이터팀",
    "ml-engineer": "데이터팀",
    "deep-learning": "데이터팀",
    "gis-specialist": "데이터팀",
    "text-analyst": "데이터팀",
    "visualizer": "데이터팀",
    "reporter": "데이터팀",
    "realty-analyst": "데이터팀",
    "requirements": "개발팀",
    "ux-designer": "개발팀",
    "frontend": "개발팀",
    "backend": "개발팀",
    "dba": "개발팀",
    "security": "개발팀",
    "tester-unit": "개발팀",
    "tester-qa": "개발팀",
    "tester": "개발팀",
    "devops": "개발팀",
    "tech-writer": "개발팀",
    "architect": "개발팀",
    "statworkbench": "개발팀",
    "pptx-planner": "PPTX팀",
    "pptx-content": "PPTX팀",
    "pptx-designer": "PPTX팀",
    "pptx-builder": "PPTX팀",
    "pptx-reviewer": "PPTX팀",
}

STATUS_KO = {
    "working": "진행",
    "done": "완료",
    "review": "검토",
    "idle": "대기",
}

WEEKDAY_KO = ["월", "화", "수", "목", "금", "토", "일"]


# ── 데이터 로드 ─────────────────────────────────────────────────────────────────
def load_logs(target_date: date) -> list[dict]:
    """work_log.jsonl에서 대상 날짜 항목만 필터링"""
    if not WORK_LOG.exists():
        return []
    logs = []
    date_str = target_date.isoformat()
    with WORK_LOG.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                # ts 우선, 없으면 timestamp/time/date 폴백 (rotate_worklog와 동일)
                ts = (
                    entry.get("ts")
                    or entry.get("timestamp")
                    or entry.get("time")
                    or entry.get("date")
                    or ""
                )
                if ts.startswith(date_str):
                    logs.append(entry)
            except json.JSONDecodeError:
                continue
    return logs


def load_status() -> dict:
    """agent_status.json 로드"""
    if not STATUS_JSON.exists():
        return {}
    try:
        with STATUS_JSON.open(encoding="utf-8") as f:
            data = json.load(f)
        return data.get("agents", {})
    except Exception:
        return {}


# ── 분석 ────────────────────────────────────────────────────────────────────────
def analyze(logs: list[dict], agents: dict) -> dict:
    done_logs = [l for l in logs if l.get("status") == "done"]
    working_logs = [l for l in logs if l.get("status") == "working"]

    # 에이전트별 작업 건수
    agent_done_count: dict[str, int] = defaultdict(int)
    agent_done_tasks: dict[str, list] = defaultdict(list)
    for l in done_logs:
        aid = l.get("agent_id", "unknown")
        agent_done_count[aid] += 1
        agent_done_tasks[aid].append(l)

    agent_working_count: dict[str, int] = defaultdict(int)
    for l in working_logs:
        aid = l.get("agent_id", "unknown")
        agent_working_count[aid] += 1

    # 팀별 집계
    team_stats: dict[str, dict] = defaultdict(lambda: {"done": 0, "working": 0, "agents": set()})
    for l in done_logs:
        aid = l.get("agent_id", "")
        team = TEAM_MAP.get(aid, "기타")
        team_stats[team]["done"] += 1
        team_stats[team]["agents"].add(aid)
    for l in working_logs:
        aid = l.get("agent_id", "")
        team = TEAM_MAP.get(aid, "기타")
        team_stats[team]["working"] += 1
        team_stats[team]["agents"].add(aid)

    # 가장 활발한 에이전트
    most_active = max(agent_done_count, key=lambda k: agent_done_count[k], default=None)

    # 시간대별 활동 (0~23시)
    hour_activity: dict[int, int] = defaultdict(int)
    for l in logs:
        ts = l.get("ts", "")
        try:
            hour = int(ts[11:13])
            hour_activity[hour] += 1
        except (ValueError, IndexError):
            pass

    total_tasks = len(working_logs)
    total_done = len(done_logs)
    # 착수(working) + 완료(done) 합계 대비 완료 비율
    completion_rate = (total_done / (total_done + total_tasks) * 100) if (total_done + total_tasks) > 0 else 0

    return {
        "total_tasks": total_tasks,
        "total_done": total_done,
        "completion_rate": completion_rate,
        "most_active": most_active,
        "most_active_count": agent_done_count.get(most_active, 0) if most_active else 0,
        "agent_done_count": dict(agent_done_count),
        "agent_done_tasks": dict(agent_done_tasks),
        "agent_working_count": dict(agent_working_count),
        "team_stats": {k: {**v, "agents": list(v["agents"])} for k, v in team_stats.items()},
        "hour_activity": dict(hour_activity),
        "active_teams": len(team_stats),
    }


# ── SVG 히트맵 ──────────────────────────────────────────────────────────────────
def build_heatmap_svg(hour_activity: dict[int, int]) -> str:
    if not hour_activity:
        max_val = 1
    else:
        max_val = max(hour_activity.values()) or 1

    cell_w, cell_h = 36, 36
    cols = 24
    pad_x, pad_y = 8, 28
    width = cols * cell_w + pad_x * 2
    height = cell_h + pad_y + 20

    cells = []
    for h in range(24):
        cnt = hour_activity.get(h, 0)
        intensity = cnt / max_val
        # 파란색 계열: 낮으면 연하게, 높으면 진하게
        r = int(235 - intensity * 180)
        g = int(245 - intensity * 160)
        b = int(255 - intensity * 80)
        color = f"rgb({r},{g},{b})"
        x = pad_x + h * cell_w
        y = pad_y
        label = str(cnt) if cnt > 0 else ""
        cells.append(
            f'<rect x="{x}" y="{y}" width="{cell_w - 2}" height="{cell_h - 2}" '
            f'rx="4" fill="{color}" stroke="#ddd" stroke-width="1"/>'
        )
        cells.append(
            f'<text x="{x + (cell_w - 2) // 2}" y="{y + (cell_h - 2) // 2 + 5}" '
            f'text-anchor="middle" font-size="11" fill="#333">{label}</text>'
        )
        # 시간 레이블
        cells.append(
            f'<text x="{x + (cell_w - 2) // 2}" y="{pad_y - 6}" '
            f'text-anchor="middle" font-size="10" fill="#666">{h}</text>'
        )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'style="max-width:100%;overflow:visible">'
        + "".join(cells)
        + "</svg>"
    )


# ── HTML 생성 ───────────────────────────────────────────────────────────────────
def build_html(target_date: date, logs: list[dict], stats: dict) -> str:
    weekday = WEEKDAY_KO[target_date.weekday()]
    date_ko = f"{target_date.year}년 {target_date.month}월 {target_date.day}일 ({weekday})"
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    # KPI 카드
    kpi_most_active_label = (
        AGENT_LABELS.get(stats["most_active"], stats["most_active"])
        if stats["most_active"]
        else "해당 없음"
    )
    kpi_most_active_detail = (
        f'{stats["most_active_count"]}건 완료'
        if stats["most_active"]
        else "활동 없음"
    )

    kpi_html = f"""
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-value">{stats["total_tasks"]}</div>
        <div class="kpi-label">총 착수 건수</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-value">{stats["total_done"]}</div>
        <div class="kpi-label">완료 건수</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-value">{stats["completion_rate"]:.1f}%</div>
        <div class="kpi-label">완료율</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-value">{stats["active_teams"]}</div>
        <div class="kpi-label">활동 팀 수</div>
      </div>
    </div>
    <div class="kpi-highlight">
      <span class="badge">최다 활동 에이전트</span>
      <strong>{kpi_most_active_label}</strong>
      <span class="muted">— {kpi_most_active_detail}</span>
    </div>
"""

    # 팀별 활동 테이블
    team_rows = ""
    team_order = ["총괄", "데이터팀", "개발팀", "PPTX팀", "기타"]
    for team in team_order:
        ts = stats["team_stats"].get(team)
        if not ts:
            continue
        agent_names = ", ".join(
            AGENT_LABELS.get(a, a) for a in sorted(ts["agents"])
        )
        total = ts["done"] + ts["working"]
        rate = (ts["done"] / total * 100) if total > 0 else 0
        bar_w = int(rate)
        team_rows += f"""
      <tr>
        <td><strong>{team}</strong></td>
        <td class="center">{total}</td>
        <td class="center">{ts["done"]}</td>
        <td class="center">{ts["working"]}</td>
        <td>
          <div class="progress-wrap">
            <div class="progress-bar" style="width:{bar_w}%"></div>
            <span class="progress-label">{rate:.0f}%</span>
          </div>
        </td>
        <td class="small">{agent_names}</td>
      </tr>"""

    team_table = f"""
    <table class="data-table">
      <thead>
        <tr>
          <th>팀</th><th>착수</th><th>완료</th><th>진행중</th><th>완료율</th><th>참여 에이전트</th>
        </tr>
      </thead>
      <tbody>{team_rows}</tbody>
    </table>
"""

    # 에이전트별 완료 작업
    agent_detail_html = ""
    sorted_agents = sorted(
        stats["agent_done_tasks"].items(),
        key=lambda x: -len(x[1])
    )
    for agent_id, tasks in sorted_agents:
        label = AGENT_LABELS.get(agent_id, agent_id)
        team = TEAM_MAP.get(agent_id, "기타")
        rows = ""
        for t in tasks:
            ts_str = t.get("ts", "")
            time_str = ts_str[11:16] if len(ts_str) >= 16 else ""
            content = t.get("content", "")[:120]
            if len(t.get("content", "")) > 120:
                content += "…"
            rows += f"<tr><td class='time-cell'>{time_str}</td><td>{content}</td></tr>"
        agent_detail_html += f"""
    <div class="agent-section">
      <div class="agent-header">
        <span class="agent-name">{label}</span>
        <span class="agent-id">({agent_id})</span>
        <span class="team-badge">{team}</span>
        <span class="count-badge">{len(tasks)}건 완료</span>
      </div>
      <table class="task-table"><tbody>{rows}</tbody></table>
    </div>
"""

    if not agent_detail_html:
        agent_detail_html = '<p class="empty-msg">당일 완료된 작업이 없습니다.</p>'

    # 히트맵
    heatmap_svg = build_heatmap_svg(stats["hour_activity"])

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Your Organization 일간 업무 보고 — {date_ko}</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: "Malgun Gothic", "Apple SD Gothic Neo", sans-serif;
      font-size: 14px;
      color: #1a1a2e;
      background: #f5f7fa;
      line-height: 1.6;
    }}
    .page-wrap {{
      max-width: 1100px;
      margin: 0 auto;
      padding: 24px 20px 60px;
    }}
    /* 헤더 */
    .report-header {{
      background: linear-gradient(135deg, #1a3a6e 0%, #2557a7 100%);
      color: #fff;
      border-radius: 10px;
      padding: 28px 32px 22px;
      margin-bottom: 28px;
    }}
    .report-header h1 {{
      font-size: 20px;
      font-weight: 700;
      letter-spacing: -0.3px;
      margin-bottom: 6px;
    }}
    .report-header .subtitle {{
      font-size: 13px;
      opacity: 0.85;
    }}
    .report-header .meta {{
      font-size: 12px;
      opacity: 0.7;
      margin-top: 8px;
    }}
    /* 섹션 */
    .section {{
      background: #fff;
      border-radius: 8px;
      padding: 22px 24px;
      margin-bottom: 20px;
      box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    }}
    .section-title {{
      font-size: 15px;
      font-weight: 700;
      color: #1a3a6e;
      border-left: 4px solid #2557a7;
      padding-left: 10px;
      margin-bottom: 16px;
    }}
    /* KPI */
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 14px;
      margin-bottom: 14px;
    }}
    .kpi-card {{
      background: #f0f4ff;
      border-radius: 8px;
      padding: 16px;
      text-align: center;
      border: 1px solid #d0daf5;
    }}
    .kpi-value {{
      font-size: 28px;
      font-weight: 700;
      color: #2557a7;
      line-height: 1.2;
    }}
    .kpi-label {{
      font-size: 12px;
      color: #555;
      margin-top: 4px;
    }}
    .kpi-highlight {{
      background: #fff8e1;
      border: 1px solid #ffd54f;
      border-radius: 6px;
      padding: 10px 16px;
      font-size: 13px;
    }}
    .badge {{
      background: #ffd54f;
      color: #5d4037;
      border-radius: 4px;
      padding: 2px 7px;
      font-size: 11px;
      font-weight: 600;
      margin-right: 8px;
    }}
    .muted {{ color: #777; }}
    /* 테이블 */
    .data-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }}
    .data-table th {{
      background: #1a3a6e;
      color: #fff;
      padding: 8px 12px;
      text-align: left;
      font-weight: 600;
    }}
    .data-table td {{
      padding: 8px 12px;
      border-bottom: 1px solid #eee;
      vertical-align: top;
    }}
    .data-table tr:last-child td {{ border-bottom: none; }}
    .data-table tr:nth-child(even) td {{ background: #f8f9fc; }}
    .center {{ text-align: center; }}
    .small {{ font-size: 12px; color: #555; }}
    /* 진행률 바 */
    .progress-wrap {{
      background: #eee;
      border-radius: 4px;
      height: 18px;
      position: relative;
      min-width: 80px;
    }}
    .progress-bar {{
      background: linear-gradient(90deg, #2557a7, #42a5f5);
      border-radius: 4px;
      height: 100%;
    }}
    .progress-label {{
      position: absolute;
      right: 4px;
      top: 1px;
      font-size: 11px;
      font-weight: 600;
      color: #333;
    }}
    /* 에이전트 섹션 */
    .agent-section {{
      border: 1px solid #e0e8f0;
      border-radius: 6px;
      margin-bottom: 12px;
      overflow: hidden;
    }}
    .agent-header {{
      background: #f0f4ff;
      padding: 8px 14px;
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }}
    .agent-name {{ font-weight: 700; font-size: 13px; color: #1a3a6e; }}
    .agent-id {{ font-size: 11px; color: #888; }}
    .team-badge {{
      background: #e3f2fd;
      color: #1565c0;
      border-radius: 4px;
      padding: 2px 7px;
      font-size: 11px;
      font-weight: 600;
    }}
    .count-badge {{
      background: #e8f5e9;
      color: #2e7d32;
      border-radius: 4px;
      padding: 2px 7px;
      font-size: 11px;
      font-weight: 600;
      margin-left: auto;
    }}
    .task-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 12px;
    }}
    .task-table td {{
      padding: 6px 14px;
      border-top: 1px solid #f0f0f0;
      vertical-align: top;
    }}
    .task-table tr:nth-child(even) td {{ background: #fafbff; }}
    .time-cell {{
      color: #888;
      width: 52px;
      white-space: nowrap;
      font-variant-numeric: tabular-nums;
    }}
    .empty-msg {{ color: #aaa; font-style: italic; padding: 10px 0; }}
    /* 히트맵 */
    .heatmap-wrap {{
      overflow-x: auto;
      padding-bottom: 4px;
    }}
    /* 푸터 */
    .report-footer {{
      text-align: center;
      font-size: 11px;
      color: #aaa;
      margin-top: 32px;
    }}
    @media (max-width: 700px) {{
      .kpi-grid {{ grid-template-columns: repeat(2, 1fr); }}
    }}
  </style>
</head>
<body>
<div class="page-wrap">
  <!-- 헤더 -->
  <div class="report-header">
    <h1>Your Organization AI 에이전트 일간 업무 보고</h1>
    <div class="subtitle">기준일: {date_ko}</div>
    <div class="meta">생성 시각: {generated_at} | 데이터 출처: work_log.jsonl</div>
  </div>

  <!-- KPI 요약 -->
  <div class="section">
    <div class="section-title">주요 지표 (KPI)</div>
    {kpi_html}
  </div>

  <!-- 팀별 활동 -->
  <div class="section">
    <div class="section-title">팀별 활동 요약</div>
    {team_table}
  </div>

  <!-- 에이전트별 완료 작업 -->
  <div class="section">
    <div class="section-title">에이전트별 완료 작업 목록</div>
    {agent_detail_html}
  </div>

  <!-- 시간대별 활동 히트맵 -->
  <div class="section">
    <div class="section-title">시간대별 활동 분포 (건수)</div>
    <div class="heatmap-wrap">{heatmap_svg}</div>
    <p class="small" style="margin-top:8px;">* 가로축: 0~23시, 셀 값은 해당 시간대 전체 상태 변경 건수</p>
  </div>

  <div class="report-footer">
    Your Organization 에이전트 시스템 — 자동 생성 보고서 &nbsp;|&nbsp; {generated_at}
  </div>
</div>
</body>
</html>
"""


# ── reports/index.html 갱신 ────────────────────────────────────────────────────
def update_reports_index(reports_dir: Path) -> None:
    html_files = sorted(
        [p for p in reports_dir.glob("????-??-??.html")],
        reverse=True
    )
    rows = ""
    for p in html_files:
        name = p.stem  # YYYY-MM-DD
        try:
            d = date.fromisoformat(name)
            weekday = WEEKDAY_KO[d.weekday()]
            label = f"{d.year}년 {d.month}월 {d.day}일 ({weekday})"
        except ValueError:
            label = name
        size_kb = p.stat().st_size // 1024
        rows += f'<tr><td><a href="{p.name}">{label}</a></td><td class="center">{size_kb} KB</td></tr>\n'

    if not rows:
        rows = '<tr><td colspan="2" class="center muted">보고서가 없습니다.</td></tr>\n'

    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    index_html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <title>일간 보고서 목록 — Your Organization</title>
  <style>
    body {{ font-family: "Malgun Gothic", sans-serif; font-size: 14px; background: #f5f7fa; color: #1a1a2e; }}
    .wrap {{ max-width: 680px; margin: 40px auto; background: #fff; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); overflow: hidden; }}
    .hd {{ background: linear-gradient(135deg, #1a3a6e 0%, #2557a7 100%); color: #fff; padding: 22px 28px; }}
    .hd h1 {{ font-size: 17px; margin-bottom: 4px; }}
    .hd p {{ font-size: 12px; opacity: 0.8; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th {{ background: #f0f4ff; color: #1a3a6e; padding: 10px 20px; text-align: left; font-weight: 700; }}
    td {{ padding: 9px 20px; border-bottom: 1px solid #eee; }}
    tr:last-child td {{ border-bottom: none; }}
    a {{ color: #2557a7; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .center {{ text-align: center; }}
    .muted {{ color: #aaa; font-style: italic; }}
    .footer {{ text-align: center; font-size: 11px; color: #bbb; padding: 14px; }}
  </style>
</head>
<body>
<div class="wrap">
  <div class="hd">
    <h1>Your Organization 일간 업무 보고서 목록</h1>
    <p>최종 갱신: {updated_at}</p>
  </div>
  <table>
    <thead><tr><th>보고서 날짜</th><th class="center">파일 크기</th></tr></thead>
    <tbody>
{rows}    </tbody>
  </table>
  <div class="footer">에이전트 시스템 자동 생성</div>
</div>
</body>
</html>
"""
    index_path = reports_dir / "index.html"
    index_path.write_text(index_html, encoding="utf-8")
    print(f"  [index] reports/index.html 갱신 완료 ({len(html_files)}개 보고서)")


# ── 메인 ────────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="일간 업무 보고서 생성기")
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="보고서 날짜 (YYYY-MM-DD). 기본값: 오늘",
    )
    args = parser.parse_args()

    if args.date:
        try:
            target_date = date.fromisoformat(args.date)
        except ValueError:
            print(f"[오류] 날짜 형식이 잘못되었습니다: {args.date} (YYYY-MM-DD)")
            sys.exit(1)
    else:
        target_date = date.today()

    print(f"\nYour Organization 일간 보고서 생성기")
    print(f"  대상 날짜: {target_date.isoformat()}")
    print(f"  로그 파일: {WORK_LOG}")

    # 데이터 로드
    logs = load_logs(target_date)
    agents = load_status()
    print(f"  로그 건수: {len(logs)}건")

    # 분석
    stats = analyze(logs, agents)

    # 보고서 폴더 생성
    REPORTS_DIR.mkdir(exist_ok=True)

    # HTML 생성
    html = build_html(target_date, logs, stats)
    out_path = REPORTS_DIR / f"{target_date.isoformat()}.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"  [완료] 보고서 저장: {out_path}")

    # index.html 갱신
    update_reports_index(REPORTS_DIR)

    # 보고서 생성 완료 후 알림 발송
    try:
        import subprocess as _sp
        _sp.Popen(
            [sys.executable, str(Path(__file__).parent / "notify_report.py"),
             "--date", target_date.isoformat()],
            creationflags=getattr(_sp, "CREATE_NO_WINDOW", 0),
        )
    except Exception:
        pass  # 알림 실패 시 조용히 무시

    # 위키 동기화
    try:
        from wiki_sync_report import sync_to_wiki
        sync_to_wiki(
            date_str=target_date.isoformat(),
            title=f"{target_date.isoformat()} 일간 업무 보고서",
            summary=f"총 착수 {stats['total_tasks']}건 / 완료 {stats['total_done']}건 / 완료율 {stats['completion_rate']:.1f}%",
            sections=[
                {"heading": "KPI", "content": f"- 총 착수: {stats['total_tasks']}건\n- 완료: {stats['total_done']}건\n- 완료율: {stats['completion_rate']:.1f}%\n- 활동 팀: {stats['active_teams']}팀"},
                {"heading": "최다 활동", "content": f"{AGENT_LABELS.get(stats.get('most_active',''), stats.get('most_active','없음'))} — {stats.get('most_active_count', 0)}건"},
            ],
            report_type="daily",
        )
    except Exception:
        pass

    # 콘솔 요약
    print("\n  ── 요약 ──────────────────────────────────")
    print(f"  총 착수 건수  : {stats['total_tasks']}건")
    print(f"  완료 건수     : {stats['total_done']}건")
    print(f"  완료율        : {stats['completion_rate']:.1f}%")
    print(f"  활동 팀 수    : {stats['active_teams']}팀")
    if stats["most_active"]:
        label = AGENT_LABELS.get(stats["most_active"], stats["most_active"])
        print(f"  최다 활동     : {label} ({stats['most_active_count']}건)")
    print("  ─────────────────────────────────────────\n")


if __name__ == "__main__":
    main()
