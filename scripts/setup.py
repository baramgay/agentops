"""
agentops setup script
Run once after cloning: python scripts/setup.py
"""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent


def check_python():
    if sys.version_info < (3, 9):
        print("[ERROR] Python 3.9+ required")
        sys.exit(1)
    print(f"[OK] Python {sys.version_info.major}.{sys.version_info.minor}")


def check_agents_home():
    home = os.environ.get("AGENTS_HOME")
    if home:
        print(f"[OK] AGENTS_HOME = {home}")
    else:
        print("[WARN] AGENTS_HOME not set.")
        print("       Set it before using the agent CLI:")
        if sys.platform == "win32":
            print(f'       setx AGENTS_HOME "{ROOT}"')
        else:
            print(f'       export AGENTS_HOME="{ROOT}"')


def init_agent_status():
    path = ROOT / "agent_status.json"
    if path.exists():
        print("[OK] agent_status.json already exists")
        return

    agents = [
        "orchestrator",
        "lead-data", "lead-dev", "lead-pptx",
        "data-collector", "data-cleaner", "eda-analyst", "statistician",
        "ml-engineer", "deep-learning", "gis-specialist", "text-analyst",
        "visualizer", "reporter", "realty-analyst",
        "requirements", "ux-designer", "frontend", "backend",
        "dba", "security", "tester-unit", "tester-qa",
        "devops", "tech-writer", "architect", "tester",
        "pptx-planner", "pptx-content", "pptx-designer", "pptx-builder", "pptx-reviewer",
        "statworkbench",
    ]

    data = {
        a: {"status": "idle", "task": "", "updated": ""}
        for a in agents
    }
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] Created agent_status.json ({len(agents)} agents)")


def init_issues():
    path = ROOT / "issues.json"
    if path.exists():
        print("[OK] issues.json already exists")
        return

    data = {"seq": 0, "issues": []}
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print("[OK] Created issues.json")


def init_wiki_dirs():
    for folder in ["feedback", "method", "project", "reference", "sessions"]:
        keep = ROOT / "wiki" / "notes" / folder / ".gitkeep"
        keep.parent.mkdir(parents=True, exist_ok=True)
        if not keep.exists():
            keep.write_text("")
    print("[OK] Wiki note folders ready")


def check_requirements():
    try:
        import fastapi  # noqa: F401
        import uvicorn  # noqa: F401
        print("[OK] Core dependencies installed")
    except ImportError:
        print("[WARN] Missing dependencies. Run: pip install -r requirements.txt")


def run_config_validation():
    """Run validate_config.py and surface any issues found."""
    validator = Path(__file__).parent / "validate_config.py"
    result = subprocess.run(
        [sys.executable, str(validator), "--quiet"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        # Print whatever the validator printed (errors / warnings)
        output = (result.stdout + result.stderr).strip()
        if output:
            print(output)
        print("[WARN] Configuration issues detected.")
        print("       Run 'python scripts/validate_config.py' for details.")
    else:
        print("[OK] Configuration validation passed")


def main():
    print("=== agentops setup ===\n")
    check_python()
    check_agents_home()
    init_agent_status()
    init_issues()
    init_wiki_dirs()
    check_requirements()
    run_config_validation()
    print("\n=== Setup complete ===")
    print("Next: python scripts/api_server.py")
    print("      Then open index.html in your browser")


if __name__ == "__main__":
    main()
