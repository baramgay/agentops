import re
from pathlib import Path

html = Path("index.html").read_text(encoding="utf-8")

pattern = r'(<span class="status-dot" id="dot-[^"]+")(\s*>)'
replacement = r'\1 data-label="대기 중" title="대기 중"\2'
new_html, n = re.subn(pattern, replacement, html)

Path("index.html").write_text(new_html, encoding="utf-8")
print(f"{n}개 status-dot 초기값 설정 완료")
