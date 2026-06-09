"""
index.html 전체에서 에이전트 아이콘 이모지를 img 태그로 교체합니다.
- desk-avatar, card-emoji, drawer-emoji 모두 처리
- onclick="openModal('agent-id')" 패턴으로 agent-id 추출
"""
import re
from pathlib import Path

HTML_PATH = Path(__file__).parent.parent / "index.html"
REL_PATH  = "assets/avatars"

AGENTS = [
    "orchestrator", "lead-data", "lead-dev", "lead-pptx",
    "data-collector", "data-cleaner", "eda-analyst", "statistician",
    "ml-engineer", "deep-learning", "gis-specialist", "text-analyst",
    "visualizer", "reporter", "requirements", "ux-designer",
    "frontend", "backend", "dba", "security",
    "tester-unit", "tester-qa", "devops", "tech-writer",
    "statworkbench", "realty-analyst",
    "pptx-planner", "pptx-content", "pptx-designer",
    "pptx-builder", "pptx-reviewer",
]

def img_tag(agent_id):
    return f'<img src="{REL_PATH}/{agent_id}.png" alt="{agent_id}">'

def apply(html, agent_id):
    tag = img_tag(agent_id)
    total = 0

    # 패턴 1: onclick="openModal('agent-id')" 블록 안의 card-emoji / desk-avatar
    for cls in ("card-emoji", "desk-avatar", "drawer-emoji"):
        # openModal('agent-id') 이후 최대 800자 안에서 해당 클래스 찾기
        pattern = (
            r"(openModal\(['\"]" + re.escape(agent_id) + r"['\"][^)]*\)[^>]*>[\s\S]{0,800}?)"
            r"(<div class=\"" + cls + r"\">)"
            r"([^<]{1,30})"
            r"(</div>)"
        )
        new_html, n = re.subn(pattern, r"\1\2" + tag + r"\4", html, flags=re.DOTALL)
        if n:
            html = new_html
            total += n

    # 패턴 2: id="desk-agent-id" 블록 안의 desk-avatar (메타버스 오피스)
    pattern = (
        r'(id="desk-' + re.escape(agent_id) + r'"[^>]*>[\s\S]{0,200}?)'
        r'(<div class="desk-avatar">)'
        r'([^<]{1,30})'
        r'(</div>)'
    )
    new_html, n = re.subn(pattern, r"\1\2" + tag + r"\4", html, flags=re.DOTALL)
    if n:
        html = new_html
        total += n

    return html, total

def run():
    html = HTML_PATH.read_text(encoding="utf-8")
    grand_total = 0

    for agent_id in AGENTS:
        html, n = apply(html, agent_id)
        if n:
            print(f"  {agent_id}: {n}건 교체")
            grand_total += n

    HTML_PATH.write_text(html, encoding="utf-8")
    print(f"\n완료: 총 {grand_total}건 교체")

if __name__ == "__main__":
    run()
