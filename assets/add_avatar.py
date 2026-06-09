import re
import sys
from pathlib import Path
from PIL import Image

OUTPUT_SIZE = 64
OUTPUT_DIR  = Path(__file__).parent / "avatars"
HTML_PATH   = Path(__file__).parent.parent / "index.html"
REL_PATH    = "assets/avatars"

def save_avatar(agent_id, src_path):
    img = Image.open(src_path).convert("RGBA")
    img = img.resize((OUTPUT_SIZE, OUTPUT_SIZE), Image.LANCZOS)
    out = OUTPUT_DIR / f"{agent_id}.png"
    img.save(out, "PNG", optimize=True)
    print(f"아바타 저장: {out}")

def patch_html(agent_id):
    html = HTML_PATH.read_text(encoding="utf-8")
    img_tag = f'<img src="{REL_PATH}/{agent_id}.png" alt="{agent_id}">'
    count = 0
    for cls in ("desk-avatar", "drawer-emoji", "card-emoji"):
        pattern = (
            r"((?:id|data-id)=[\"'](?:desk-)?" + re.escape(agent_id) + r"[\"'][\s\S]{0,600}?)"
            r"(<div class=\"" + cls + r"\">)(.{0,30}?)(</div>)"
        )
        new_html, n = re.subn(pattern, r"\1\2" + img_tag + r"\4", html, flags=re.DOTALL)
        if n:
            html = new_html
            count += n
    HTML_PATH.write_text(html, encoding="utf-8")
    print(f"index.html 패치: {count}건")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("사용법: python assets/add_avatar.py [agent-id] [image-path]")
        sys.exit(1)
    save_avatar(sys.argv[1], sys.argv[2])
    patch_html(sys.argv[1])
    print(f"완료: {sys.argv[1]}")
