"""
위키 읽기 헬퍼 — 에이전트가 작업 시작 시 MoC + 연결 노트를 효율적으로 로드.

사용법:
  python AGENTS_HOME/wiki/_tools/wiki_read.py <도메인>           # MoC 읽기
  python AGENTS_HOME/wiki/_tools/wiki_read.py <도메인> <슬러그>  # 특정 노트 읽기
  python AGENTS_HOME/wiki/_tools/wiki_read.py --list            # 도메인 목록

예시:
  python AGENTS_HOME/wiki/_tools/wiki_read.py 경남부동산
  python AGENTS_HOME/wiki/_tools/wiki_read.py agents시스템 feedback-cp949-console-guard
"""
import sys
import re
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

VAULT = Path(__file__).resolve().parent.parent
MOC   = VAULT / "MoC"
NOTES = VAULT / "notes"
LINK  = re.compile(r'\[\[([^\]|#]+)')


def list_domains():
    print("도메인 목록:")
    for f in sorted(MOC.glob("*.md")):
        links = LINK.findall(f.read_text(encoding="utf-8"))
        print(f"  {f.stem}  ({len(links)}개 노트)")


def read_moc(domain: str):
    p = MOC / f"{domain}.md"
    if not p.exists():
        close = [f.stem for f in MOC.glob("*.md") if domain in f.stem]
        print(f"[오류] MoC '{domain}' 없음", file=sys.stderr)
        if close: print(f"유사: {close}", file=sys.stderr)
        sys.exit(1)
    body = p.read_text(encoding="utf-8")
    print(f"=== MoC: {domain} ===\n")
    print(body)
    # 링크된 노트 제목 목록도 출력 (컨텍스트 힌트)
    linked = LINK.findall(body)
    existing = [s for s in linked if (NOTES / f"{s}.md").exists()]
    if existing:
        print(f"\n--- 연결된 노트 ({len(existing)}개) ---")
        for s in existing:
            first = (NOTES / f"{s}.md").read_text(encoding="utf-8").split("\n")
            desc = next((l.strip() for l in first if l.strip() and not l.startswith("#") and not l.startswith("---")), "")
            print(f"  [[{s}]] {desc[:70]}")


def read_note(slug: str):
    p = NOTES / f"{slug}.md"
    if not p.exists():
        close = [f.stem for f in NOTES.glob("*.md") if slug.replace("-","") in f.stem.replace("-","")]
        print(f"[오류] 노트 '{slug}' 없음", file=sys.stderr)
        if close: print(f"유사: {close[:5]}", file=sys.stderr)
        sys.exit(1)
    print(f"=== {slug} ===\n")
    print(p.read_text(encoding="utf-8"))


def main():
    args = sys.argv[1:]
    if not args or args[0] == "--list":
        list_domains(); return
    if len(args) == 1:
        read_moc(args[0])
    else:
        read_note(args[1])


if __name__ == "__main__":
    main()
