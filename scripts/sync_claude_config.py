"""
Claude 설정 동기화 스크립트

사용법:
    python sync_claude_config.py export   # .claude/ -> claude-config/
    python sync_claude_config.py import   # claude-config/ -> .claude/
"""

import sys
import shutil
from pathlib import Path
from datetime import datetime


# ── 경로 설정 ──────────────────────────────────────────────
CLAUDE_CONFIG_DIR = Path(__file__).resolve().parent.parent / "claude-config"
CLAUDE_DOT_DIR = Path.home() / ".claude"

# 동기화 제외 파일/디렉토리 (민감정보, 머신별 설정)
SKIP_NAMES = {
    "settings.json",
    "settings.local.json",
    "credentials",
    "credentials.json",
    ".credentials",
    "statsig",
    "statsig.json",
    "todo.md",
}


def find_project_dirs() -> list[Path]:
    """
    .claude/projects/ 아래의 프로젝트 디렉토리 목록을 반환한다.
    인코딩된 디렉토리명(예: C--Users------user-)도 포함.
    """
    projects_root = CLAUDE_DOT_DIR / "projects"
    if not projects_root.exists():
        return []
    return [d for d in projects_root.iterdir() if d.is_dir()]


def copy_file(src: Path, dst: Path, label: str = "") -> None:
    """파일 하나를 복사한다. 부모 디렉토리가 없으면 생성."""
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    except (IOError, OSError) as e:
        print(f"[sync_claude_config] 파일 복사 실패 ({src} -> {dst}): {e}", file=sys.stderr)
        raise
    tag = f" [{label}]" if label else ""
    print(f"  복사{tag}: {src} -> {dst}")


def backup_file(filepath: Path) -> None:
    """기존 파일이 있으면 타임스탬프 붙여 백업."""
    if filepath.exists():
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = filepath.with_name(filepath.stem + f".bak_{ts}" + filepath.suffix)
        try:
            shutil.copy2(filepath, backup)
        except (IOError, OSError) as e:
            print(f"[sync_claude_config] 백업 실패 ({filepath}): {e}", file=sys.stderr)
            raise
        print(f"  백업: {filepath} -> {backup}")


# ── export: .claude/ -> claude-config/ ────────────────────
def do_export() -> None:
    print(f"\n=== EXPORT: .claude/ -> claude-config/ ===")
    print(f"  소스: {CLAUDE_DOT_DIR}")
    print(f"  대상: {CLAUDE_CONFIG_DIR}\n")

    if not CLAUDE_DOT_DIR.exists():
        print(f"[sync_claude_config] 오류: {CLAUDE_DOT_DIR} 디렉토리가 존재하지 않습니다.", file=sys.stderr)
        sys.exit(1)

    # 1) CLAUDE.md
    claude_md = CLAUDE_DOT_DIR / "CLAUDE.md"
    if claude_md.exists():
        copy_file(claude_md, CLAUDE_CONFIG_DIR / "CLAUDE.md", "전역 설정")
    else:
        print(f"  건너뜀: {claude_md} (파일 없음)")

    # 2) 프로젝트별 memory 파일
    project_dirs = find_project_dirs()
    if not project_dirs:
        print("  프로젝트 디렉토리 없음 (memory 동기화 건너뜀)")

    for proj_dir in project_dirs:
        proj_name = proj_dir.name
        memory_dir = proj_dir / "memory"
        if not memory_dir.exists():
            continue

        for md_file in memory_dir.glob("*.md"):
            if md_file.name in SKIP_NAMES:
                continue
            dst = CLAUDE_CONFIG_DIR / "memory" / proj_name / md_file.name
            copy_file(md_file, dst, f"memory/{proj_name}")

    # 3) 커스텀 스킬 (사용자 작성 스킬만)
    skills_dir = CLAUDE_DOT_DIR / "skills"
    if skills_dir.exists():
        for skill_file in skills_dir.rglob("*"):
            if skill_file.is_file() and skill_file.name not in SKIP_NAMES:
                rel = skill_file.relative_to(skills_dir)
                dst = CLAUDE_CONFIG_DIR / "skills" / rel
                copy_file(skill_file, dst, "skill")

    print("\n=== EXPORT 완료 ===\n")


# ── import: claude-config/ -> .claude/ ────────────────────
def do_import() -> None:
    print(f"\n=== IMPORT: claude-config/ -> .claude/ ===")
    print(f"  소스: {CLAUDE_CONFIG_DIR}")
    print(f"  대상: {CLAUDE_DOT_DIR}\n")

    if not CLAUDE_CONFIG_DIR.exists():
        print(f"[sync_claude_config] 오류: {CLAUDE_CONFIG_DIR} 디렉토리가 존재하지 않습니다.", file=sys.stderr)
        sys.exit(1)

    # 1) CLAUDE.md
    src_claude_md = CLAUDE_CONFIG_DIR / "CLAUDE.md"
    dst_claude_md = CLAUDE_DOT_DIR / "CLAUDE.md"
    if src_claude_md.exists():
        backup_file(dst_claude_md)
        copy_file(src_claude_md, dst_claude_md, "전역 설정")
    else:
        print(f"  건너뜀: {src_claude_md} (파일 없음)")

    # 2) memory 파일 -> 프로젝트 디렉토리로 복원
    memory_root = CLAUDE_CONFIG_DIR / "memory"
    if memory_root.exists():
        for proj_dir in memory_root.iterdir():
            if not proj_dir.is_dir():
                continue
            proj_name = proj_dir.name

            # 대상 프로젝트 디렉토리 찾기:
            # .claude/projects/ 아래에 동일 이름이 있으면 사용
            target_memory = CLAUDE_DOT_DIR / "projects" / proj_name / "memory"

            for md_file in proj_dir.glob("*.md"):
                dst = target_memory / md_file.name
                backup_file(dst)
                copy_file(md_file, dst, f"memory/{proj_name}")
    else:
        print("  memory 디렉토리 없음 (건너뜀)")

    # 3) 스킬 복원
    skills_src = CLAUDE_CONFIG_DIR / "skills"
    if skills_src.exists():
        skills_dst = CLAUDE_DOT_DIR / "skills"
        for skill_file in skills_src.rglob("*"):
            if skill_file.is_file():
                rel = skill_file.relative_to(skills_src)
                dst = skills_dst / rel
                backup_file(dst)
                copy_file(skill_file, dst, "skill")

    print("\n=== IMPORT 완료 ===\n")


# ── 메인 ──────────────────────────────────────────────────
def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in ("export", "import"):
        print("사용법: python sync_claude_config.py [export|import]")
        print("  export  - .claude/ 내용을 claude-config/으로 내보내기")
        print("  import  - claude-config/ 내용을 .claude/에 적용")
        sys.exit(1)

    command = sys.argv[1]
    if command == "export":
        do_export()
    elif command == "import":
        do_import()


if __name__ == "__main__":
    main()
