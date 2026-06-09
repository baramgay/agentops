"""
index.html의 이모지 아바타를 슬라이싱된 PNG 이미지로 교체합니다.
desk-avatar / drawer-emoji / card-emoji 세 곳 모두 처리.
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
    "statworkbench", "pptx-planner", "pptx-content", "pptx-designer",
    "pptx-builder", "pptx-reviewer",
]

def img_tag(agent_id):
    return f'<img src="{REL_PATH}/{agent_id}.png" alt="{agent_id}">'

def apply():
    html = HTML_PATH.read_text(encoding="utf-8")
    total = 0

    for agent_id in AGENTS:
        tag = img_tag(agent_id)

        # 1) desk-avatar: id="desk-{agent}" 안의 첫 번째 desk-avatar 내용
        pattern = (
            r'(id="desk-' + re.escape(agent_id) + r'"[^>]*>\s*)'
            r'(<div class="desk-avatar">)(.+?)(</div>)'
        )
        new_html, n = re.subn(pattern, r'\1\2' + tag + r'\4', html, flags=re.DOTALL)
        if n:
            html = new_html
            total += n

        # 2) drawer-emoji: data-id="{agent}" 컨텍스트 내
        pattern2 = (
            r'(data-id=["\']' + re.escape(agent_id) + r'["\'][\s\S]{0,600}?)'
            r'(<div class="drawer-emoji">)(.{1,20}?)(</div>)'
        )
        new_html, n = re.subn(pattern2, r'\1\2' + tag + r'\4', html, flags=re.DOTALL)
        if n:
            html = new_html
            total += n

        # 3) card-emoji: 같은 data-id 컨텍스트
        pattern3 = (
            r'(data-id=["\']' + re.escape(agent_id) + r'["\'][\s\S]{0,600}?)'
            r'(<div class="card-emoji">)(.{1,20}?)(</div>)'
        )
        new_html, n = re.subn(pattern3, r'\1\2' + tag + r'\4', html, flags=re.DOTALL)
        if n:
            html = new_html
            total += n

    HTML_PATH.write_text(html, encoding="utf-8")
    print(f"완료: 총 {total}건 교체 ({HTML_PATH.name})")

if __name__ == "__main__":
    apply()
