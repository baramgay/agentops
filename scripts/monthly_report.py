"""
monthly_report.py — 월간 업무 보고서 생성기

실행 조건:
  - 매월 1일 09:00 (auto_sync.py 또는 Task Scheduler에서 호출)
  - 수동 실행: python scripts/monthly_report.py [--month YYYY-MM]

파이프라인:
  weekly_report.py (매주) -> monthly_report.py (매월 1일) -> notify_report.py (알림)
"""
import json
import argparse
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from collections import defaultdict


def get_month_range(month_str: str | None = None):
    if month_str:
        year, month = map(int, month_str.split("-"))
    else:
        today = date.today()
        # 전월 기준
        first = today.replace(day=1)
        prev = first - timedelta(days=1)
        year, month = prev.year, prev.month
    start = date(year, month, 1)
    # 다음 달 1일 - 1일 = 말일
    if month == 12:
        end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(year, month + 1, 1) - timedelta(days=1)
    return start, end


def load_logs(repo: Path, start: date, end: date):
    log_file = repo / "work_log.jsonl"
    entries = []
    if not log_file.exists():
        return entries
    for line in log_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
            raw_ts = (
                e.get("ts")
                or e.get("timestamp")
                or e.get("time")
                or e.get("date")
                or ""
            )
            ts = datetime.fromisoformat(raw_ts).date()
            if start <= ts <= end:
                entries.append(e)
        except Exception:
            continue
    return entries


def build_stats(entries, start: date, end: date):
    agent_stats = defaultdict(lambda: {"done": 0, "working": 0, "review": 0, "tasks": []})
    weekly = defaultdict(lambda: defaultdict(int))   # week_label -> status -> count
    daily = defaultdict(lambda: defaultdict(int))    # date -> status -> count

    for e in entries:
        aid = e.get("agent_id", "unknown")
        status = e.get("status", "")
        raw_ts = e.get("ts") or e.get("timestamp") or e.get("time") or e.get("date") or ""
        ts_date = raw_ts[:10]
        try:
            d = datetime.fromisoformat(raw_ts).date()
            week_label = d.strftime("%Y-W%W")
        except Exception:
            week_label = "unknown"
        agent_stats[aid][status] = agent_stats[aid].get(status, 0) + 1
        if status == "done":
            agent_stats[aid]["tasks"].append(e.get("message", ""))
        weekly[week_label][status] += 1
        daily[ts_date][status] += 1

    return agent_stats, weekly, daily


TEAM_MAP = {
    "data-collector": "Data", "data-cleaner": "Data", "eda-analyst": "Data",
    "statistician": "Data", "ml-engineer": "Data", "deep-learning": "Data",
    "gis-specialist": "Data", "text-analyst": "Data", "visualizer": "Data",
    "reporter": "Data", "realty-analyst": "Data", "lead-data": "Data",
    "requirements": "Dev", "ux-designer": "Dev", "frontend": "Dev",
    "backend": "Dev", "dba": "Dev", "security": "Dev", "tester-unit": "Dev",
    "tester-qa": "Dev", "devops": "Dev", "tech-writer": "Dev",
    "statworkbench": "Dev", "lead-dev": "Dev", "architect": "Dev", "tester": "Dev",
    "pptx-planner": "PPTX", "pptx-content": "PPTX", "pptx-designer": "PPTX",
    "pptx-builder": "PPTX", "pptx-reviewer": "PPTX", "lead-pptx": "PPTX",
    "orchestrator": "OC",
}

TEAM_COLORS = {"Data": "#3B82F6", "Dev": "#10B981", "PPTX": "#F59E0B", "OC": "#8B5CF6"}


def generate_html(start: date, end: date, agent_stats, weekly, daily, out_path: Path):
    total_done = sum(s["done"] for s in agent_stats.values())
    total_working = sum(s.get("working", 0) for s in agent_stats.values())
    completion_rate = int(total_done / (total_done + total_working) * 100) if (total_done + total_working) else 0

    # 팀별 집계
    team_stats = defaultdict(lambda: {"done": 0, "agents": 0})
    for aid, s in agent_stats.items():
        team = TEAM_MAP.get(aid, "OC")
        team_stats[team]["done"] += s["done"]
        team_stats[team]["agents"] += 1

    # 주별 완료 추이 막대 (최대 5주)
    sorted_weeks = sorted(weekly.keys())[-5:]
    week_bars = ""
    max_w = max((weekly[w].get("done", 0) for w in sorted_weeks), default=1) or 1
    for w in sorted_weeks:
        cnt = weekly[w].get("done", 0)
        h = int(cnt / max_w * 80) if cnt else 2
        week_bars += f'<div class="bar-wrap"><div class="bar" style="height:{h}px" title="{cnt}건"></div><div class="bar-label">{w[5:]}<br>{cnt}</div></div>'

    # 일별 히트맵 (해당 월 전체)
    num_days = (end - start).days + 1
    all_days = [(start + timedelta(days=i)).isoformat() for i in range(num_days)]
    max_d = max((daily[d].get("done", 0) for d in all_days), default=1) or 1
    heatmap_cells = ""
    for d in all_days:
        cnt = daily[d].get("done", 0)
        alpha = min(1.0, cnt / max_d) if cnt else 0
        color = f"rgba(59,130,246,{alpha:.2f})" if cnt else "#161B22"
        day_num = datetime.fromisoformat(d).day
        heatmap_cells += f'<div class="hm-cell" style="background:{color}" title="{d}: {cnt}건"><span>{day_num}</span></div>'

    # 상위 기여자 Top 10
    top = sorted(agent_stats.items(), key=lambda x: x[1]["done"], reverse=True)[:10]
    rows = ""
    for aid, s in top:
        team = TEAM_MAP.get(aid, "OC")
        color = TEAM_COLORS.get(team, "#666")
        rows += f'<tr><td><span class="team-dot" style="background:{color}"></span>{aid}</td><td>{team}</td><td class="num">{s["done"]}</td><td class="num">{s.get("working", 0)}</td><td class="num">{s.get("review", 0)}</td></tr>'

    # 팀별 막대
    max_team = max((ts["done"] for ts in team_stats.values()), default=1) or 1
    team_bar_html = "".join(
        f'<div class="tbar-row"><div class="tbar-name">{t}</div>'
        f'<div class="tbar"><div class="tbar-fill" style="width:{min(100,int(s["done"]/max_team*100))}%;background:{TEAM_COLORS.get(t,"#666")}"></div></div>'
        f'<div class="tbar-val">{s["done"]}건</div></div>'
        for t, s in team_stats.items()
    )

    month_label = start.strftime("%Y년 %m월")

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>월간 보고서 {month_label}</title>
<style>
body{{font-family:'Pretendard','Malgun Gothic',sans-serif;background:#0f172a;color:#e2e8f0;margin:0;padding:24px}}
h1{{font-size:24px;color:#f8fafc;margin-bottom:4px}}
.sub{{color:#64748b;font-size:13px;margin-bottom:28px}}
.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:32px}}
.card{{background:#1e293b;border-radius:12px;padding:20px;text-align:center}}
.card .n{{font-size:38px;font-weight:700;color:#38bdf8}}
.card .l{{font-size:12px;color:#64748b;margin-top:4px}}
.section{{background:#1e293b;border-radius:12px;padding:20px;margin-bottom:24px}}
h2{{font-size:15px;color:#94a3b8;margin:0 0 16px}}
.chart{{display:flex;align-items:flex-end;gap:8px;height:100px}}
.bar-wrap{{display:flex;flex-direction:column;align-items:center;gap:4px}}
.bar{{width:36px;background:#3B82F6;border-radius:4px 4px 0 0;min-height:2px}}
.bar-label{{font-size:10px;color:#64748b;text-align:center}}
table{{width:100%;border-collapse:collapse}}
th{{text-align:left;padding:8px;font-size:12px;color:#64748b;border-bottom:1px solid #334155}}
td{{padding:8px;font-size:13px;border-bottom:1px solid #1e293b}}
.num{{text-align:right;color:#38bdf8;font-weight:600}}
.team-dot{{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px}}
.team-bars{{display:flex;flex-direction:column;gap:10px}}
.tbar-row{{display:flex;align-items:center;gap:10px}}
.tbar-name{{width:60px;font-size:13px;color:#94a3b8}}
.tbar{{flex:1;height:14px;background:#0f172a;border-radius:4px;overflow:hidden}}
.tbar-fill{{height:100%;border-radius:4px}}
.tbar-val{{width:40px;font-size:12px;color:#64748b;text-align:right}}
.heatmap{{display:grid;grid-template-columns:repeat(7,1fr);gap:3px}}
.hm-cell{{aspect-ratio:1;border-radius:3px;display:flex;align-items:center;justify-content:center;font-size:9px;color:#64748b;cursor:default}}
.hm-cell span{{pointer-events:none}}
</style>
</head>
<body>
<h1>월간 성과 보고서</h1>
<div class="sub">{start} ~ {end} · {month_label} · Your Organization 에이전트 시스템</div>

<div class="cards">
  <div class="card"><div class="n">{total_done}</div><div class="l">총 완료 작업</div></div>
  <div class="card"><div class="n">{total_working}</div><div class="l">총 진행 이력</div></div>
  <div class="card"><div class="n">{len(agent_stats)}</div><div class="l">활동 에이전트</div></div>
  <div class="card"><div class="n">{completion_rate}%</div><div class="l">완료율</div></div>
</div>

<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:24px;">
  <div class="section">
    <h2>주별 완료 추이</h2>
    <div class="chart">{week_bars}</div>
  </div>
  <div class="section">
    <h2>팀별 완료 현황</h2>
    <div class="team-bars">{team_bar_html}</div>
  </div>
</div>

<div class="section" style="margin-bottom:24px;">
  <h2>일별 활동 히트맵</h2>
  <div style="font-size:11px;color:#64748b;margin-bottom:8px;">일별 완료 작업 수 (진할수록 많음)</div>
  <div class="heatmap">{heatmap_cells}</div>
</div>

<div class="section">
  <h2>상위 기여 에이전트 (완료 기준 Top 10)</h2>
  <table>
    <tr><th>에이전트</th><th>팀</th><th>완료</th><th>진행</th><th>검토</th></tr>
    {rows}
  </table>
</div>

<div style="color:#334155;font-size:11px;text-align:right">생성: {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
</body></html>"""

    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    print(f"[monthly] 보고서 저장: {out_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--month", default=None, help="YYYY-MM 형식 (예: 2026-04)")
    args = parser.parse_args()

    repo = Path(__file__).parent.parent
    start, end = get_month_range(args.month)
    month_label = start.strftime("%Y-%m")

    entries = load_logs(repo, start, end)
    agent_stats, weekly, daily = build_stats(entries, start, end)

    out_path = repo / "reports" / f"monthly-{month_label}.html"
    generate_html(start, end, agent_stats, weekly, daily, out_path)

    # 보고서 목록 갱신
    index_path = repo / "reports" / "index.html"
    if index_path.exists():
        idx = index_path.read_text(encoding="utf-8")
        link = f'<li><a href="monthly-{month_label}.html">월간 {start.strftime("%Y년 %m월")} ({start} ~ {end})</a></li>'
        if link not in idx:
            idx = idx.replace("</ul>", f"{link}\n</ul>", 1)
            index_path.write_text(idx, encoding="utf-8")

    # 위키 동기화
    try:
        from wiki_sync_report import sync_to_wiki
        top5 = sorted(agent_stats.items(), key=lambda x: -x[1].get("done", 0))[:5]
        top5_md = "\n".join(f"- {aid}: {v.get('done',0)}건 완료" for aid, v in top5)
        weekly_md = "\n".join(f"- {w}: {c}건" for w, c in sorted(weekly.items()))
        sync_to_wiki(
            date_str=f"monthly-{month_label}",
            title=f"월간 보고서 {start.strftime('%Y년 %m월')} ({start} ~ {end})",
            summary=f"기간: {start} ~ {end} (총 {len(entries)}개 로그)",
            sections=[
                {"heading": "Top 5 에이전트", "content": top5_md or "활동 없음"},
                {"heading": "주차별 활동", "content": weekly_md or "없음"},
            ],
            report_type="monthly",
        )
    except Exception:
        pass

    # 알림 발송
    try:
        subprocess.Popen(
            [sys.executable, str(Path(__file__).parent / "notify_report.py"),
             "--date", start.isoformat()],
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except Exception:
        pass


if __name__ == "__main__":
    main()
