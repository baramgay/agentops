"""
위키 쓰기 헬퍼 — 에이전트가 작업 완료 시 노트를 생성·업데이트.

사용법:
  # 새 노트 생성 (이미 있으면 오류 — 업데이트는 직접 편집)
  python AGENTS_HOME/wiki/_tools/wiki_write.py create <슬러그> <type> <domain> "<제목>" "<본문>"

  # MoC에 링크 추가
  python AGENTS_HOME/wiki/_tools/wiki_write.py link <domain> <슬러그> "<설명>"

  # 기존 노트 업데이트 (내용 추가)
  python AGENTS_HOME/wiki/_tools/wiki_write.py append <슬러그> "<추가할 텍스트>"

type: feedback | project | reference | method | decision
"""
import sys
import re
from pathlib import Path
from datetime import date

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

VAULT = Path(__file__).resolve().parent.parent
MOC   = VAULT / "MoC"
NOTES = VAULT / "notes"


def create(slug, ntype, domain, title, body):
    p = NOTES / f"{slug}.md"
    if p.exists():
        print(f"[오류] '{slug}.md' 이미 존재 — 업데이트는 append 또는 직접 편집 사용", file=sys.stderr)
        sys.exit(1)
    today = date.today().isoformat()
    content = f"""---
name: {slug}
type: {ntype}
domain: {domain}
updated: {today}
---

# {title}

{body}
"""
    p.write_text(content, encoding="utf-8")
    print(f"✅ 생성: notes/{slug}.md")
    print(f"   → MoC에 링크 추가: python wiki_write.py link {domain} {slug} \"<설명>\"")


def link(domain, slug, desc=""):
    p = MOC / f"{domain}.md"
    if not p.exists():
        print(f"[오류] MoC '{domain}.md' 없음", file=sys.stderr); sys.exit(1)
    content = p.read_text(encoding="utf-8")
    entry = f"- [[{slug}]]" + (f" — {desc}" if desc else "")
    if f"[[{slug}]]" in content:
        print(f"[건너뜀] [[{slug}]] 이미 MoC에 존재"); return
    # 마지막 비어있지 않은 줄 뒤에 추가
    lines = content.rstrip().split("\n")
    lines.append(entry)
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"✅ MoC/{domain}.md 에 [[{slug}]] 링크 추가")


def append(slug, text):
    p = NOTES / f"{slug}.md"
    if not p.exists():
        print(f"[오류] '{slug}.md' 없음", file=sys.stderr); sys.exit(1)
    today = date.today().isoformat()
    addition = f"\n\n---\n*{today} 추가*\n\n{text}"
    with open(p, "a", encoding="utf-8") as f:
        f.write(addition)
    # frontmatter updated 갱신
    content = p.read_text(encoding="utf-8")
    content = re.sub(r'^updated:.*$', f'updated: {today}', content, flags=re.M)
    p.write_text(content, encoding="utf-8")
    print(f"✅ notes/{slug}.md 내용 추가 완료")


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__); return
    cmd = args[0]
    if cmd == "create" and len(args) >= 6:
        create(args[1], args[2], args[3], args[4], args[5])
    elif cmd == "link" and len(args) >= 3:
        link(args[1], args[2], args[3] if len(args) > 3 else "")
    elif cmd == "append" and len(args) >= 3:
        append(args[1], args[2])
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
