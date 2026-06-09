"""
weekly_report.py — 주간 업무 보고서 생성기

실행 조건:
  - 매주 월요일 09:00 (auto_sync.py 또는 Task Scheduler에서 호출)
  - 수동 실행: python scripts/weekly_report.py [--week YYYY-WNN]

파이프라인:
  daily_report.py (매일) -> notify_report.py (완료 알림)
  weekly_report.py (매주 월요일) -> notify_report.py (주간 알림)
"""
import json
import argparse
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from collections import defaultdict


def get_week_range(week_str: str | None = None):
    if week_str:
        try:
            year, w = week_str.split("-W", 1)
            d = datetime.strptime(f"{year}-W{int(w):02d}-1", "%Y-W%W-%w").date()
        except (ValueError, IndexError) as e:
            print(f"[weekly_report] 주차 형식 오류 ({week_str}): {e}", file=sys.stderr)
            sys.exit(1)
    else:
        today = date.today()
        d = today - timedelta(days=today.weekday())
    return d, d + timedelta(days=6)


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
            # ts 우선, 없으면 timestamp/time/date 폴백 (daily_report·rotate_worklog와 동일)
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


def build_stats(entries):
    agent_stats = defaultdict(lambda: {"done": 0, "working": 0, "review": 0, "tasks": []})
    daily = defaultdict(lambda: defaultdict(int))  # date -> status -> count

    for e in entries:
        aid = e.get("agent_id", "unknown")
        status = e.get("status", "")
        raw_ts = e.get("ts") or e.get("timestamp") or e.get("time") or e.get("date") or ""
        ts = raw_ts[:10]
        agent_stats[aid][status] = agent_stats[aid].get(status, 0) + 1
        if status == "done":
            agent_stats[aid]["tasks"].append(e.get("message", ""))
        daily[ts][status] += 1

    return agent_stats, daily


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


def generate_html(start: date, end: date, agent_stats, daily, out_path: Path):
    total_done = sum(s["done"] for s in agent_stats.values())
    total_working = sum(s.get("working", 0) for s in agent_stats.values())

    # 팀별 집계
    team_stats = defaultdict(lambda: {"done": 0, "agents": 0})
    for aid, s in agent_stats.items():
        team = TEAM_MAP.get(aid, "OC")
        team_stats[team]["done"] += s["done"]
        team_stats[team]["agents"] += 1

    # 상위 기여자
    top = sorted(agent_stats.items(), key=lambda x: x[1]["done"], reverse=True)[:10]

    days = [(start + timedelta(days=i)).isoformat() for i in range(7)]
    daily_done = [daily[d].get("done", 0) for d in days]

    bars = ""
    max_d = max(daily_done) or 1
    for i, (d, cnt) in enumerate(zip(days, daily_done)):
        h = int(cnt / max_d * 80) if cnt else 2
        day_name = ["월", "화", "수", "목", "금", "토", "일"][i]
        bars += f'<div class="bar-wrap"><div class="bar" style="height:{h}px" title="{cnt}건"></div><div class="bar-label">{day_name}<br>{cnt}</div></div>'

    rows = ""
    for aid, s in top:
        team = TEAM_MAP.get(aid, "OC")
        color = TEAM_COLORS.get(team, "#666")
        rows += f'<tr><td><span class="team-dot" style="background:{color}"></span>{aid}</td><td>{team}</td><td class="num">{s["done"]}</td><td class="num">{s.get("working", 0)}</td></tr>'

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>주간 보고서 {start} ~ {end}</title>
<style>
body{{font-family:'Pretendard',sans-serif;background:#0f172a;color:#e2e8f0;margin:0;padding:24px}}
h1{{font-size:22px;color:#f8fafc;margin-bottom:4px}}
.sub{{color:#64748b;font-size:13px;margin-bottom:24px}}
.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:32px}}
.card{{background:#1e293b;border-radius:12px;padding:20px;text-align:center}}
.card .n{{font-size:36px;font-weight:700;color:#38bdf8}}
.card .l{{font-size:12px;color:#64748b;margin-top:4px}}
.section{{background:#1e293b;border-radius:12px;padding:20px;margin-bottom:24px}}
h2{{font-size:15px;color:#94a3b8;margin:0 0 16px}}
.chart{{display:flex;align-items:flex-end;gap:8px;height:100px}}
.bar-wrap{{display:flex;flex-direction:column;align-items:center;gap:4px}}
.bar{{width:28px;background:#3B82F6;border-radius:4px 4px 0 0;min-height:2px;transition:height .3s}}
.bar-label{{font-size:11px;color:#64748b;text-align:center}}
table{{width:100%;border-collapse:collapse}}
th{{text-align:left;padding:8px;font-size:12px;color:#64748b;border-bottom:1px solid #334155}}
td{{padding:8px;font-size:13px;border-bottom:1px solid #1e293b}}
.num{{text-align:right;color:#38bdf8;font-weight:600}}
.team-dot{{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px}}
.team-bars{{display:flex;flex-direction:column;gap:10px}}
.tbar-row{{display:flex;align-items:center;gap:10px}}
.tbar-name{{width:60px;font-size:13px;color:#94a3b8}}
.tbar{{flex:1;height:14px;background:#0f172a;border-radius:4px;overflow:hidden}}
.tbar-fill{{height:100%;border-radius:4px;transition:width .4s}}
.tbar-val{{width:40px;font-size:12px;color:#64748b;text-align:right}}
</style>
</head>
<body>
<h1>주간 성과 보고서</h1>
<div class="sub">{start} ~ {end} · Your Organization 에이전트 시스템</div>

<div class="cards">
  <div class="card"><div class="n">{total_done}</div><div class="l">총 완료 작업</div></div>
  <div class="card"><div class="n">{total_working}</div><div class="l">총 진행 이력</div></div>
  <div class="card"><div class="n">{len(agent_stats)}</div><div class="l">활동 에이전트</div></div>
  <div class="card"><div class="n">{int(total_done/(total_done+total_working)*100) if total_done+total_working else 0}%</div><div class="l">완료율</div></div>
</div>

<div class="section">
  <h2>일별 완료 현황</h2>
  <div class="chart">{bars}</div>
</div>

<div class="section">
  <h2>팀별 완료 현황</h2>
  <div class="team-bars">
    {"".join(f'<div class="tbar-row"><div class="tbar-name">{t}</div><div class="tbar"><div class="tbar-fill" style="width:{min(100,int(s["done"]/(max(1,max(ts["done"] for ts in team_stats.values())))*100))}%;background:{TEAM_COLORS.get(t,"#666")}"></div></div><div class="tbar-val">{s["done"]}건</div></div>' for t, s in team_stats.items())}
  </div>
</div>

<div class="section">
  <h2>상위 기여 에이전트 (완료 기준)</h2>
  <table>
    <tr><th>에이전트</th><th>팀</th><th>완료</th><th>진행</th></tr>
    {rows}
  </table>
</div>

<div style="color:#334155;font-size:11px;text-align:right">생성: {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
</body></html>"""

    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    print(f"[weekly] 보고서 저장: {out_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--week", default=None, help="YYYY-WNN 형식 (예: 2026-W22)")
    args = parser.parse_args()

    repo = Path(__file__).parent.parent
    start, end = get_week_range(args.week)
    week_label = start.strftime("%Y-W%W")

    entries = load_logs(repo, start, end)
    agent_stats, daily = build_stats(entries)

    out_path = repo / "reports" / f"weekly-{week_label}.html"
    generate_html(start, end, agent_stats, daily, out_path)

    # 보고서 목록 갱신
    index_path = repo / "reports" / "index.html"
    if index_path.exists():
        idx = index_path.read_text(encoding="utf-8")
        link = f'<li><a href="weekly-{week_label}.html">주간 {start} ~ {end}</a></li>'
        if link not in idx:
            idx = idx.replace("</ul>", f"{link}\n</ul>", 1)
            index_path.write_text(idx, encoding="utf-8")

    # 위키 동기화
    try:
        from wiki_sync_report import sync_to_wiki
        top5 = sorted(agent_stats.items(), key=lambda x: -x[1].get("done", 0))[:5]
        top5_md = "\n".join(f"- {aid}: {v.get('done',0)}건 완료" for aid, v in top5)
        sync_to_wiki(
            date_str=start.isoformat(),
            title=f"주간 보고서 {start} ~ {end}",
            summary=f"기간: {start} ~ {end} ({len(entries)}개 로그)",
            sections=[
                {"heading": "Top 5 에이전트", "content": top5_md or "활동 없음"},
                {"heading": "일별 활동", "content": "\n".join(f"- {d}: {c}건" for d, c in sorted(daily.items()))},
            ],
            report_type="weekly",
        )
    except Exception:
        pass

    # 주간 보고서 생성 완료 후 알림 발송
    try:
        subprocess.Popen(
            [sys.executable, str(Path(__file__).parent / "notify_report.py"),
             "--date", start.isoformat()],
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except Exception:
        pass  # 알림 실패 시 조용히 무시


if __name__ == "__main__":
    main()
