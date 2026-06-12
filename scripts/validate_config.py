#!/usr/bin/env python3
"""
Validate agentops configuration before starting the server.

Usage:
    python scripts/validate_config.py              # check config.local.json + structure
    python scripts/validate_config.py --config path/to/config.json
    python scripts/validate_config.py --env        # check environment variables only

Exit codes:
    0 -- all checks passed
    1 -- one or more checks failed
"""

import argparse
import json
import os
import sys
from pathlib import Path


# Keys that must be present in config.local.json when the file exists.
REQUIRED_KEYS = ["machine_id", "workspace_root"]

# Agent folders that should exist under <agents_home>/agents/
EXPECTED_AGENTS = [
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

# Subdirectories that must exist directly under agents_home
REQUIRED_DIRS = ["agents", "scripts", "wiki"]

# Files that must exist (relative to agents_home)
CRITICAL_FILES = ["agent_status.json", "scripts/update_status.py"]


# ---------------------------------------------------------------------------
# Individual check functions — each returns a list of error strings
# ---------------------------------------------------------------------------

def check_config_file(config_path: Path) -> list:
    """Validate config.local.json if it exists; return error messages."""
    errors = []

    if not config_path.exists():
        # Absence of config.local.json is not an error — defaults are used.
        return []

    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{config_path.name} is not valid JSON: {exc}"]

    # Required keys
    for key in REQUIRED_KEYS:
        if key not in config:
            errors.append(f"Missing required key: '{key}'")

    # workspace_root must point to an existing directory
    if "workspace_root" in config:
        ws = Path(config["workspace_root"])
        if not ws.exists():
            errors.append(f"workspace_root path does not exist: {ws}")
        elif not ws.is_dir():
            errors.append(f"workspace_root is not a directory: {ws}")

    return errors


def check_agents_home(agents_home: Path) -> list:
    """Check that the agents_home directory is properly structured."""
    errors = []

    if not agents_home.exists():
        return [f"AGENTS_HOME does not exist: {agents_home}"]

    if not agents_home.is_dir():
        return [f"AGENTS_HOME is not a directory: {agents_home}"]

    # Required subdirectories
    for dirname in REQUIRED_DIRS:
        target = agents_home / dirname
        if not target.is_dir():
            errors.append(f"Missing required directory: {target}")

    # Critical files
    for rel in CRITICAL_FILES:
        target = agents_home / rel
        if not target.exists():
            errors.append(f"Missing critical file: {target}")

    # Agent folders
    agents_dir = agents_home / "agents"
    if agents_dir.is_dir():
        missing = [a for a in EXPECTED_AGENTS if not (agents_dir / a).is_dir()]
        if missing:
            errors.append(f"Missing agent folders ({len(missing)}): {', '.join(missing)}")

    return errors


def check_env_variables() -> list:
    """Check environment variables; return warning messages (non-fatal)."""
    warnings = []
    if not os.environ.get("AGENTS_HOME"):
        warnings.append(
            "AGENTS_HOME environment variable is not set "
            "(current directory used as fallback)"
        )
    return warnings


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate agentops configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--config",
        default=None,
        metavar="PATH",
        help="Path to config file (default: <agents_home>/config.local.json)",
    )
    parser.add_argument(
        "--env",
        action="store_true",
        help="Check environment variables only",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress output when all checks pass",
    )
    args = parser.parse_args()

    # Resolve agents_home: env var > script's grandparent directory
    agents_home = Path(os.environ.get("AGENTS_HOME", Path(__file__).parent.parent))
    config_path = Path(args.config) if args.config else agents_home / "config.local.json"

    all_errors: list = []
    all_warnings: list = []

    if not args.quiet:
        print("Validating agentops configuration...")

    # 1. Environment variables
    all_warnings.extend(check_env_variables())

    if not args.env:
        # 2. config.local.json
        all_errors.extend(check_config_file(config_path))

        # 3. Directory / file structure
        all_errors.extend(check_agents_home(agents_home))

    # --- Report ---
    for w in all_warnings:
        print(f"  [WARN]  {w}")

    for e in all_errors:
        print(f"  [ERROR] {e}")

    if not all_errors:
        if not args.quiet:
            print(f"  [OK]    Configuration valid (checked {config_path})")
        return 0

    print(
        f"\n{len(all_errors)} error(s) found. "
        "Fix the issues above before starting the server."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
