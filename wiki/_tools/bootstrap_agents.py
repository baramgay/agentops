"""
에이전트 role.md(미러) + memory.md(원본 전환) → wiki 부트스트랩.

role.md   → wiki/notes/agent-<id>-role.md     (미러, agents/ 가 원본)
memory.md → wiki/notes/agent-<id>-memory.md   (원본, 위키가 정본)
MoC/에이전트.md 자동 생성 (팀별 분류)
"""
import re, shutil
from pathlib import Path

try:
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

AGENTS_DIR = Path(__file__).resolve().parent.parent.parent / "agents"
VAULT      = Path(__file__).resolve().parent.parent
NOTES      = VAULT / "notes"
MOC_DIR    = VAULT / "MoC"
NOTES.mkdir(parents=True, exist_ok=True)
MOC_DIR.mkdir(parents=True, exist_ok=True)

# 팀별 에이전트 분류
TEAMS = {
    "총괄": ["orchestrator"],
    "빅데이터팀": ["lead-data","data-collector","data-cleaner","eda-analyst",
                   "statistician","ml-engineer","deep-learning","gis-specialist",
                   "text-analyst","visualizer","reporter","realty-analyst"],
    "개발팀":     ["lead-dev","requirements","ux-designer","frontend","backend",
                   "dba","security","tester-unit","tester-qa","devops",
                   "tech-writer","statworkbench","architect","tester"],
    "PPTX팀":    ["lead-pptx","pptx-planner","pptx-content","pptx-designer",
                   "pptx-builder","pptx-reviewer"],
}
ALL_TEAMS = {aid: team for team, aids in TEAMS.items() for aid in aids}

def add_frontmatter(content: str, agent_id: str, ftype: str) -> str:
    """frontmatter가 없으면 추가, 있으면 그대로."""
    if content.startswith("---"):
        return content
    team = ALL_TEAMS.get(agent_id, "기타")
    fm = (f"---\nname: agent-{agent_id}-{ftype}\n"
          f"type: {'reference' if ftype=='role' else 'project'}\n"
          f"domain: agents시스템\nagent: {agent_id}\nteam: {team}\n"
          f"tags: [agent, {ftype}]\n---\n\n")
    return fm + content

def sanitize_links(text: str) -> str:
    """밑줄 위키링크 → 하이픈 (파일명 일관성)."""
    return re.sub(r'\[\[([^\]|#`]+)', lambda m: '[[' + m.group(1).replace('_','-'), text)

copied_role = copied_mem = 0
for agent_dir in sorted(AGENTS_DIR.iterdir()):
    if not agent_dir.is_dir():
        continue
    aid = agent_dir.name

    # role.md → 미러
    rp = agent_dir / "role.md"
    if rp.exists():
        body = sanitize_links(rp.read_text(encoding="utf-8"))
        body = add_frontmatter(body, aid, "role")
        (NOTES / f"agent-{aid}-role.md").write_text(body, encoding="utf-8")
        copied_role += 1

    # memory.md → 위키 원본
    mp = agent_dir / "memory.md"
    if mp.exists():
        body = sanitize_links(mp.read_text(encoding="utf-8"))
        body = add_frontmatter(body, aid, "memory")
        (NOTES / f"agent-{aid}-memory.md").write_text(body, encoding="utf-8")
        copied_mem += 1

# MoC/에이전트.md 생성
lines = ["---", "type: moc", "domain: agents시스템", "tags: [moc, agent]", "---",
         "", "# 에이전트 — 지도(MoC)", "",
         "> 33개 에이전트의 역할·메모리 허브. 팀별로 분류.", ""]
for team, aids in TEAMS.items():
    lines += [f"## {team}", ""]
    for aid in aids:
        rn = f"agent-{aid}-role.md"
        mn = f"agent-{aid}-memory.md"
        has_r = (NOTES / rn).exists()
        has_m = (NOTES / mn).exists()
        parts = []
        if has_r: parts.append(f"[[agent-{aid}-role|role]]")
        if has_m: parts.append(f"[[agent-{aid}-memory|memory]]")
        lines.append(f"- **{aid}** — " + " · ".join(parts) if parts else f"- **{aid}**")
    lines.append("")

(MOC_DIR / "에이전트.md").write_text("\n".join(lines), encoding="utf-8")
print(f"role 미러: {copied_role}개 | memory 원본 전환: {copied_mem}개")
print("MoC/에이전트.md 생성 완료")
