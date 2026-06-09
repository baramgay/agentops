"""
index.html 전체 이모지 교체 (2단계):
  1. MD 에디터 사이드바 정적 이모지
  2. openModal() JS - modal-emoji
  3. showAgentDetail() JS - drawer-emoji
  4. 정적 drawer-emoji 초기값
  5. modal-emoji CSS img 크기 추가
"""
import re
from pathlib import Path

HTML_PATH = Path(__file__).parent.parent / "index.html"
REL       = "assets/avatars"

# agent-id → 이모지 원본 (교체 대상 탐색용)
EMOJI_MAP = {
    "orchestrator":"🎯","lead-data":"📊","lead-dev":"💻","lead-pptx":"🎨",
    "data-collector":"🕵️","data-cleaner":"🧹","eda-analyst":"🔍","statistician":"📐",
    "ml-engineer":"🤖","deep-learning":"🧠","gis-specialist":"🗺️","text-analyst":"📝",
    "visualizer":"📊","reporter":"📋","requirements":"📋","ux-designer":"🎨",
    "frontend":"🖼️","backend":"⚙️","dba":"🗄️","security":"🔒",
    "tester-unit":"🧪","tester-qa":"✅","devops":"🚀","tech-writer":"📖",
    "statworkbench":"🔬","pptx-planner":"🗂️","pptx-content":"✍️","pptx-designer":"🖌️",
    "pptx-builder":"🔨","pptx-reviewer":"🔎",
}

def small_img(agent_id):
    """사이드바용 소형 아이콘"""
    return f'<img src="{REL}/{agent_id}.png" alt="{agent_id}" style="width:16px;height:16px;object-fit:contain;vertical-align:middle;border-radius:3px;flex-shrink:0;">'

def run():
    html = HTML_PATH.read_text(encoding="utf-8")
    total = 0

    # ── 1. MD 에디터 사이드바: id="sidebar-{agent}" 내 이모지 텍스트 교체 ──
    for agent_id, emoji in EMOJI_MAP.items():
        # 패턴: id="sidebar-agent-id" onclick="...">EMOJI agent-id<span
        # emoji 다음에 공백 있을 수도 없을 수도 있음
        pattern = (
            r'(id="sidebar-' + re.escape(agent_id) + r'"[^>]*>)'
            r'(.{1,6}?)'           # 이모지 (1~2 문자)
            r'(\s*)(' + re.escape(agent_id) + r')'
        )
        replacement = r'\1' + small_img(agent_id) + r' \4'
        new_html, n = re.subn(pattern, replacement, html)
        if n:
            html = new_html
            total += n

    # ── 2. JS openModal: textContent = a.emoji → innerHTML = img ──
    old_modal = "document.getElementById('modal-emoji').textContent = a.emoji;"
    new_modal = "document.getElementById('modal-emoji').innerHTML = `<img src=\"${REL_PATH}/${id}.png\" alt=\"${id}\" style=\"width:44px;height:44px;object-fit:contain;border-radius:10px;\">`;"
    if old_modal in html:
        # JS 내에서 REL_PATH 변수를 사용하도록 JS 변수도 선언 필요
        html = html.replace(old_modal, new_modal.replace("${REL_PATH}", f"{REL}"))
        total += 1

    # ── 3. JS showAgentDetail: textContent = emoji → innerHTML = img ──
    old_drawer_js = "document.getElementById('drawer-emoji').textContent = emoji;"
    new_drawer_js = f"document.getElementById('drawer-emoji').innerHTML = `<img src=\"{REL}/${{agentId}}.png\" alt=\"${{agentId}}\" style=\"width:48px;height:48px;object-fit:contain;border-radius:10px;\">`;"
    if old_drawer_js in html:
        html = html.replace(old_drawer_js, new_drawer_js)
        total += 1

    # ── 4. 정적 drawer-emoji 초기값 (🎯 → 비워두기) ──
    old_static = '<div class="drawer-emoji" id="drawer-emoji">🎯</div>'
    new_static  = '<div class="drawer-emoji" id="drawer-emoji"></div>'
    if old_static in html:
        html = html.replace(old_static, new_static)
        total += 1

    # ── 5. modal-emoji CSS에 img 크기 추가 ──
    old_css = "  .modal-emoji { font-size:40px; }"
    new_css = "  .modal-emoji { font-size:40px; width:52px; height:52px; display:flex; align-items:center; justify-content:center; }\n  .modal-emoji img { width:52px; height:52px; object-fit:contain; border-radius:12px; }"
    if old_css in html and ".modal-emoji img" not in html:
        html = html.replace(old_css, new_css)
        total += 1

    HTML_PATH.write_text(html, encoding="utf-8")
    print(f"완료: 총 {total}건 처리")

if __name__ == "__main__":
    run()
