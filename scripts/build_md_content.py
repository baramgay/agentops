import json, re, sys
from pathlib import Path

SCRIPT_DIR  = Path(__file__).parent
REPO_ROOT   = SCRIPT_DIR.parent
AGENTS_DIR  = REPO_ROOT / "agents"
WIKI_NOTES  = REPO_ROOT / "wiki" / "notes"  # memory 정본 위치 (agents/wiki/notes)
HTML_FILE   = REPO_ROOT / "index.html"
JSON_FILE   = SCRIPT_DIR / "md_content.json"

BOM = bytes([0xef, 0xbb, 0xbf])
DRY_RUN = "--dry" in sys.argv


def _strip_bom(text: str) -> str:
    """파일 어디서나 나타나는 BOM(U+FEFF) 제거."""
    return text.replace("﻿", "")


def _read_md(path: Path) -> str:
    raw = path.read_bytes()
    if raw.startswith(BOM):
        raw = raw[3:]
    return _strip_bom(raw.decode("utf-8", errors="replace"))


def scan_agents():
    result = {}
    for agent_dir in sorted(AGENTS_DIR.iterdir()):
        if not agent_dir.is_dir():
            continue
        aid = agent_dir.name
        entry = {"role": "", "memory": ""}

        # role: agents/ 원본 (미러 아님)
        rp = agent_dir / "role.md"
        if rp.exists():
            entry["role"] = _read_md(rp)

        # memory: 위키 정본 우선 → agents/ 폴백
        wiki_mem = WIKI_NOTES / "agents" / f"agent-{aid}-memory.md"
        agent_mem = agent_dir / "memory.md"
        if wiki_mem.exists():
            entry["memory"] = _read_md(wiki_mem)
        elif agent_mem.exists():
            entry["memory"] = _read_md(agent_mem)

        result[aid] = entry
    return result


def inject_html(data):
    html = HTML_FILE.read_text(encoding="utf-8")
    pat = re.compile(r"(const MD_CONTENT = )([{].*?[}])(\s*;)", re.DOTALL)
    m = pat.search(html)
    if not m:
        print("[ERROR] MD_CONTENT pattern not found")
        return False
    new_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    # HTML 파서가 </script>를 조기 종료로 해석하지 않도록 </를 <\/로 이스케이프
    new_json = new_json.replace("</", "<\\/")
    new_html = html[:m.start(1)] + m.group(1) + new_json + m.group(3) + html[m.end():]
    if new_html == html:
        return False
    if not DRY_RUN:
        HTML_FILE.write_text(new_html, encoding="utf-8")
    return True


if __name__ == "__main__":
    data = scan_agents()
    have = sum(1 for v in data.values() if v["memory"].strip())
    print(f"Scanned: {len(data)} agents, {have} with memory.md")

    if not DRY_RUN:
        JSON_FILE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        print(f"Saved: {JSON_FILE}")

    if inject_html(data):
        print(f"Updated: {HTML_FILE}")
        print("Next: git add index.html scripts/md_content.json && git commit && git push")
    else:
        print("No change in index.html.")
