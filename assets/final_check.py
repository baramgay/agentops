import re
from pathlib import Path

html = open("index.html", encoding="utf-8").read()

emoji_desk = re.findall(r'desk-avatar">[^<]{2,10}', html)
emoji_card = re.findall(r'card-emoji">[^<]{2,10}', html)
img_desk   = len(re.findall(r'desk-avatar.*?assets/avatars', html))
img_card   = len(re.findall(r'card-emoji.*?assets/avatars', html))
img_side   = len(re.findall(r'sidebar-.*?assets/avatars', html))
backslash  = len(re.findall(r'avatars\\', html))
has_realty_desk = "desk-realty-analyst" in html
has_realty_side = "sidebar-realty-analyst" in html
avatar_count = len(list(Path("assets/avatars").glob("*.png")))

print(f"[아바타 파일]   {avatar_count}개")
print(f"[이모지 잔존]   desk:{len(emoji_desk)}건  card:{len(emoji_card)}건")
print(f"[img 태그]      desk:{img_desk}건  card:{img_card}건  sidebar:{img_side}건")
print(f"[역슬래시경로]  {backslash}건")
print(f"[realty-analyst] 데스크:{has_realty_desk}  사이드바:{has_realty_side}")
print(f"[JS modal/drawer] modal-innerHTML:{'modal-emoji' in html and 'innerHTML' in html}  drawer-innerHTML:{'drawer-emoji' in html and 'innerHTML' in html}")
