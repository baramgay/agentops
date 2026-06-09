"""
세션 자동 캡처 — Claude Code SessionEnd 훅용. 토큰 0 (LLM 미호출, transcript 기계적 파싱).

세션 종료 시 transcript를 1회 파싱해 "참고 파일·변경 파일·작업·스킬"을 추출,
wiki/notes/sessions/세션-YYYY-MM-DD.md 에 사실 기록으로 누적한다.

입력: stdin JSON (SessionEnd 훅) — {session_id, transcript_path, cwd, reason}
출력: 없음(컨텍스트 미주입). 어떤 경우에도 예외로 세션을 막지 않는다.

한계: "참고/변경 파일이 무엇인지"는 기록하지만 내용 산문 요약은 하지 않음(그건 LLM=토큰 필요).
"""
import sys
import os
import json
from datetime import datetime
from pathlib import Path

WIKI_SESSIONS = Path(__file__).resolve().parent.parent / "wiki" / "notes" / "sessions"

# cwd basename → 보기 좋은 프로젝트명 (없으면 basename 그대로)
PROJECT_ALIASES = {
    "agents": "agents시스템",
    "합성데이터스튜디오": "합성데이터스튜디오",
    "nuristat": "누리스탯",
    "누리스탯": "누리스탯",
    "webapp": "이음지도",
    "장애인이동지원플랫폼": "이음지도",
    "estate": "부동산동향",
}


def _project_name(cwd: str) -> str:
    base = os.path.basename(cwd.rstrip("\\/")) if cwd else ""
    return PROJECT_ALIASES.get(base, base or "기타")


def _parse_transcript(path: str):
    """transcript JSONL에서 tool 사용 추출 → (참고파일, 변경파일, 작업, 스킬)."""
    reads, edits, tasks, skills = [], [], [], []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                # assistant 메시지 안의 tool_use 블록 탐색
                msg = rec.get("message") or rec
                content = msg.get("content") if isinstance(msg, dict) else None
                if not isinstance(content, list):
                    continue
                for block in content:
                    if not isinstance(block, dict) or block.get("type") != "tool_use":
                        continue
                    name = block.get("name", "")
                    inp = block.get("input", {}) or {}
                    if name == "Read":
                        fp = inp.get("file_path", "")
                        if fp:
                            reads.append(fp)
                    elif name in ("Edit", "Write", "NotebookEdit"):
                        fp = inp.get("file_path", "") or inp.get("notebook_path", "")
                        if fp:
                            edits.append(fp)
                    elif name == "Skill":
                        s = inp.get("skill", "")
                        if s:
                            skills.append(s)
                    elif name in ("Bash", "PowerShell"):
                        cmd = inp.get("command", "")
                        if "update_status.py" in cmd:
                            # task 인자 추출 (따옴표 안)
                            import re
                            m = re.search(r'update_status\.py\s+\S+\s+\S+\s+"([^"]+)"', cmd)
                            if m:
                                tasks.append(m.group(1))
    except Exception:
        pass
    return reads, edits, tasks, skills


def _dedup_keep_order(items, limit=None):
    seen, out = set(), []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out[:limit] if limit else out


def main():
    try:
        raw = sys.stdin.read() if not sys.stdin.isatty() else "{}"
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        data = {}

    transcript = data.get("transcript_path", "")
    cwd = data.get("cwd", "")
    if not transcript or not os.path.exists(transcript):
        return

    reads, edits, tasks, skills = _parse_transcript(transcript)
    reads = _dedup_keep_order(reads, 15)
    edits = _dedup_keep_order(edits, 15)
    tasks = _dedup_keep_order(tasks, 10)
    skills = _dedup_keep_order(skills, 8)

    # 의미 있는 활동이 없으면 기록 안 함(노이즈 방지)
    if not (edits or tasks or len(reads) >= 3):
        return

    now = datetime.now()
    project = _project_name(cwd)

    def _fmt(paths):
        return "\n".join(f"  - `{os.path.basename(p)}` ({p})" for p in paths) if paths else "  - (없음)"

    section = [
        f"\n### {now:%H:%M} — {project}",
        f"- 세션: `{data.get('session_id','?')[:8]}` / 종료: {data.get('reason','?')}",
    ]
    if tasks:
        section.append("- 작업:")
        section += [f"  - {t}" for t in tasks]
    if skills:
        section.append(f"- 사용 스킬: {', '.join(skills)}")
    section.append(f"- 참고 문서({len(reads)}):")
    section.append(_fmt(reads))
    section.append(f"- 변경 파일({len(edits)}):")
    section.append(_fmt(edits))
    section.append("")

    # PC별 파일명 → 다중 PC 동시 작업 시 git 충돌 원천 차단
    machine = os.environ.get("COMPUTERNAME") or os.uname().nodename if hasattr(os, "uname") else os.environ.get("COMPUTERNAME", "PC")
    machine = (machine or "PC").replace(" ", "-")[:20]
    try:
        WIKI_SESSIONS.mkdir(parents=True, exist_ok=True)
        note = WIKI_SESSIONS / f"세션-{now:%Y-%m-%d}-{machine}.md"
        if not note.exists():
            header = (f"---\nname: 세션-{now:%Y-%m-%d}-{machine}\ntype: session-log\n"
                      f"date: {now:%Y-%m-%d}\nmachine: {machine}\ntags: [session]\n---\n\n"
                      f"# {now:%Y-%m-%d} 세션 활동 기록 ({machine})\n\n"
                      f"> 자동 캡처(토큰 0). 참고·변경 파일과 작업의 사실 기록. "
                      f"내용 요약은 별도 명령 필요.\n")
            note.write_text(header, encoding="utf-8")
        with open(note, "a", encoding="utf-8") as f:
            f.write("\n".join(section))
    except Exception:
        pass

    # 메모리 → Obsidian 볼트 동기화 (멱등 bootstrap; 실패해도 세션 캡처에 영향 없음).
    # 로컬 볼트만 최신화하고 git push는 하지 않는다(기존 동작과 일관, 다중 PC 충돌 방지).
    try:
        import subprocess
        boot = Path(__file__).resolve().parent.parent / "wiki" / "_tools" / "bootstrap_from_memory.py"
        if boot.exists():
            subprocess.run([sys.executable, str(boot)], timeout=60, capture_output=True)
    except Exception:
        pass


if __name__ == "__main__":
    main()
