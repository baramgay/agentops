"""
통합 빌드 스크립트
사용법: python scripts/build_all.py

memory.md 수정 후 반드시 실행 — index.html MD_CONTENT에 주입됩니다.
"""

import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent


def run_step(description, script_name):
    script_path = SCRIPT_DIR / script_name
    if not script_path.exists():
        print(f"  SKIP: {script_name}")
        return True
    print(f"
{'='*50}
  {description}
  -> {script_name}
{'='*50}")
    result = subprocess.run([sys.executable, str(script_path)], cwd=str(REPO_ROOT))
    if result.returncode != 0:
        print(f"  FAIL: {script_name} (exit {result.returncode})")
        return False
    print("  OK")
    return True


def main():
    print("=" * 50)
    print("  멀티 에이전트 시스템 통합 빌드")
    print("=" * 50)

    # build_html.py는 MD 에디터 탭을 추가할 때쓴 1회성 스크립트
    # 반복 실행 불가 — build_md_content.py만 사용
    steps = [
        ("MD 콘텐츠 주입 (agents/*/memory.md -> index.html)", "build_md_content.py"),
    ]

    failed = []
    for desc, script in steps:
        if not run_step(desc, script):
            failed.append(script)

    print(f"
{'='*50}")
    if failed:
        print(f"  빌드 실패: {', '.join(failed)}")
        sys.exit(1)
    else:
        print("  완료! index.html이 최신 memory.md로 업데이트되었습니다.")
        print(f"  -> {REPO_ROOT / 'index.html'}")
        print("  
  git add index.html scripts/md_content.json && git commit && git push")
    print("=" * 50)


if __name__ == "__main__":
    main()
