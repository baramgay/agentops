"""
위키 주기적 정리 스크립트 — 매주 월요일 자동 실행 (CronCreate 등록)

수행 작업:
1. MoC 커버리지 점검 → 미등록 노트 일괄 등록 시도
2. 중복 slug 탐지 → 보고
3. domain 없는 노트 탐지 → 보고
4. 오래된 노트(90일 이상 미수정, 내용 10줄 이하) 탐지 → 보고
5. notes/ 루트 파일 잔존 여부 확인 → 있으면 경고
6. 정리 보고서 출력
"""
import sys
import re
from pathlib import Path
from datetime import datetime, date

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

WIKI = Path(__file__).resolve().parent.parent / "wiki"
NOTES_DIR = WIKI / "notes"
MOC_DIR = WIKI / "MoC"


def run_moc_registration():
    """moc_auto_register.py로 미등록 노트 일괄 등록."""
    import subprocess
    files = [str(f) for f in NOTES_DIR.rglob("*.md")
             if f.parent != NOTES_DIR  # 루트 제외
             and "sessions" not in f.parts
             and not f.stem.startswith("agent-")]
    if not files:
        return 0, 0
    result = subprocess.run(
        [sys.executable, str(Path(__file__).parent / "moc_auto_register.py")] + files,
        capture_output=True, text=True, encoding="utf-8"
    )
    registered = result.stdout.count("등록됨:")
    skipped = result.stdout.count("skip:")
    return registered, skipped


def check_root_files():
    """notes/ 루트 직접 저장 파일 탐지."""
    root_mds = [f for f in NOTES_DIR.glob("*.md")]
    return root_mds


def check_no_domain():
    """domain 필드 없는 노트 탐지 (세션·agent 제외)."""
    missing = []
    for note in NOTES_DIR.rglob("*.md"):
        if note.parent == NOTES_DIR:
            continue
        if "sessions" in note.parts or note.stem.startswith("agent-"):
            continue
        text = note.read_text(encoding="utf-8", errors="replace")
        m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
        if m and "domain:" not in m.group(1):
            missing.append(note)
    return missing


def check_duplicate_slugs():
    """같은 slug를 가진 노트 탐지."""
    slug_map: dict[str, list[Path]] = {}
    for note in NOTES_DIR.rglob("*.md"):
        if note.parent == NOTES_DIR:
            continue
        text = note.read_text(encoding="utf-8", errors="replace")
        m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
        if m:
            for line in m.group(1).splitlines():
                if line.startswith("name:"):
                    slug = line.split(":", 1)[1].strip()
                    slug_map.setdefault(slug, []).append(note)
    return {k: v for k, v in slug_map.items() if len(v) > 1}


def check_stale_notes(days=90, max_lines=10):
    """오래되고 내용이 적은 노트 탐지."""
    stale = []
    today = date.today()
    for note in NOTES_DIR.rglob("*.md"):
        if note.parent == NOTES_DIR:
            continue
        if "sessions" in note.parts or note.stem.startswith("agent-"):
            continue
        text = note.read_text(encoding="utf-8", errors="replace")
        # updated 날짜 파싱
        m_updated = re.search(r"updated:\s*(\d{4}-\d{2}-\d{2})", text)
        if m_updated:
            try:
                updated = date.fromisoformat(m_updated.group(1))
                age = (today - updated).days
                content_lines = [l for l in text.split("\n") if l.strip() and not l.startswith("---") and ":" not in l[:20]]
                if age >= days and len(content_lines) <= max_lines:
                    stale.append((note, age, len(content_lines)))
            except ValueError:
                pass
    return stale


def main():
    today_str = date.today().isoformat()
    print(f"\n{'='*60}")
    print(f"🧹 위키 주기적 정리 보고서 — {today_str}")
    print(f"{'='*60}\n")

    # 1. MoC 자동 등록
    print("[ 1/5 ] MoC 미등록 노트 자동 등록...")
    registered, skipped = run_moc_registration()
    print(f"  → 신규 등록: {registered}개 / 이미 등록: {skipped}개\n")

    # 2. 루트 파일 자동 삭제 (Obsidian이 재생성하는 경우 대비)
    print("[ 2/5 ] notes/ 루트 파일 잔존 확인 및 자동 삭제...")
    root_files = check_root_files()
    if root_files:
        deleted = []
        for f in root_files:
            try:
                f.unlink()
                deleted.append(f.name)
            except Exception as e:
                print(f"     삭제 실패: {f.name} — {e}")
        print(f"  🗑️  루트 파일 {len(deleted)}개 자동 삭제 완료")
        if len(deleted) <= 5:
            for name in deleted:
                print(f"     - {name}")
        else:
            for name in deleted[:3]:
                print(f"     - {name}")
            print(f"     ... 외 {len(deleted)-3}개")
        print()
    else:
        print("  ✅ 루트 파일 없음 — 정상\n")

    # 3. domain 없는 노트
    print("[ 3/5 ] domain 미설정 노트 탐지...")
    no_domain = check_no_domain()
    if no_domain:
        print(f"  ⚠️  domain 없는 노트 {len(no_domain)}개:")
        for f in no_domain[:5]:
            print(f"     - {f.relative_to(NOTES_DIR)}")
        if len(no_domain) > 5:
            print(f"     ... 외 {len(no_domain)-5}개")
        print(f"  → 수동으로 frontmatter에 'domain: <MoC명>' 추가 필요\n")
    else:
        print("  ✅ 모든 노트에 domain 설정됨\n")

    # 4. 중복 slug
    print("[ 4/5 ] 중복 slug 탐지...")
    dupes = check_duplicate_slugs()
    if dupes:
        print(f"  ⚠️  중복 slug {len(dupes)}개:")
        for slug, paths in list(dupes.items())[:3]:
            print(f"     [[{slug}]]: {[str(p.relative_to(NOTES_DIR)) for p in paths]}")
    else:
        print("  ✅ 중복 slug 없음\n")

    # 5. 낡은 노트
    print("[ 5/5 ] 낡은 노트 탐지 (90일 이상 미수정 + 10줄 이하)...")
    stale = check_stale_notes()
    if stale:
        print(f"  ⚠️  낡은 노트 {len(stale)}개 (병합·삭제 검토):")
        for note, age, lines in sorted(stale, key=lambda x: -x[1])[:5]:
            print(f"     - {note.name} ({age}일 전, {lines}줄)")
    else:
        print("  ✅ 낡은 노트 없음\n")

    # 요약
    issues = len(root_files) + len(no_domain) + len(dupes) + len(stale)
    print(f"\n{'='*60}")
    print(f"📊 요약: 신규 MoC 등록 {registered}개 / 조치 필요 항목 {issues}개")
    if issues == 0:
        print("✅ 위키 상태 양호 — 추가 조치 불필요")
    else:
        print("→ 위 항목을 순서대로 처리하면 MoC 커버리지가 개선됩니다.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
