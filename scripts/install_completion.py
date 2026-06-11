#!/usr/bin/env python3
"""Install shell completion for update_status.py.

Generates tab-completion scripts for bash, zsh, and fish using
register-python-argcomplete (ships with argcomplete).

Usage:
    python scripts/install_completion.py --bash   # append snippet to ~/.bashrc
    python scripts/install_completion.py --zsh    # append snippet to ~/.zshrc
    python scripts/install_completion.py --fish   # write fish completion file
    python scripts/install_completion.py --print  # print snippet, no changes

After running, open a new shell (or source the config file) and tab away:

    python scripts/update_status.py [TAB]
    # orchestrator  lead-data  lead-dev  eda-analyst  backend ...
"""

import subprocess
import sys
import os
from pathlib import Path


SCRIPT_PATH = Path(__file__).parent / "update_status.py"
COMPLETION_CMD = "python " + str(SCRIPT_PATH)


def check_argcomplete():
    """Check argcomplete is installed; offer to install it if missing."""
    try:
        import argcomplete  # noqa: F401
        return True
    except ImportError:
        print("argcomplete is not installed.")
        answer = input("Install it now with pip? [Y/n]: ").strip().lower()
        if answer in ("", "y", "yes"):
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "argcomplete>=3.0.0"],
                check=False,
            )
            if result.returncode == 0:
                print("argcomplete installed successfully.")
                return True
            else:
                print("Installation failed. Please run: pip install argcomplete")
                return False
        else:
            print("Skipped. Run 'pip install argcomplete' when ready.")
            return False


def generate_bash_snippet():
    """Return the bash/zsh eval snippet for update_status.py completion."""
    return (
        f'\n# agentops shell completion (update_status.py)\n'
        f'eval "$(register-python-argcomplete \'{COMPLETION_CMD}\')"\n'
    )


def generate_fish_snippet():
    """Return the fish completion script content."""
    return (
        f"# agentops shell completion (update_status.py)\n"
        f"complete -c update_status.py -f\n"
        f"# Use register-python-argcomplete for full dynamic completion:\n"
        f"register-python-argcomplete --shell fish '{COMPLETION_CMD}' | source\n"
    )


def append_to_file(path: Path, snippet: str, label: str):
    """Append snippet to a shell config file if not already present."""
    path = path.expanduser()
    marker = "agentops shell completion"
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if marker in existing:
            print(f"Completion already registered in {path} — skipping.")
            return
    with open(path, "a", encoding="utf-8") as f:
        f.write(snippet)
    print(f"Completion snippet appended to {path}")
    print(f"Run:  source {path}  (or open a new {label} shell)")


def install_fish():
    """Write fish completion file to the standard completions directory."""
    fish_dir = Path("~/.config/fish/completions").expanduser()
    fish_dir.mkdir(parents=True, exist_ok=True)
    target = fish_dir / "update_status.py.fish"
    snippet = generate_fish_snippet()
    if target.exists():
        existing = target.read_text(encoding="utf-8")
        if "agentops shell completion" in existing:
            print(f"Fish completion already installed at {target} — skipping.")
            return
    target.write_text(snippet, encoding="utf-8")
    print(f"Fish completion installed at {target}")
    print("It will be active in new fish shells automatically.")


def print_snippet(shell: str):
    """Print the completion snippet without making any file changes."""
    if shell == "fish":
        snippet = generate_fish_snippet()
        print(f"\n--- fish completion (save to ~/.config/fish/completions/update_status.py.fish) ---")
    else:
        snippet = generate_bash_snippet()
        print(f"\n--- bash/zsh completion snippet (append to ~/.bashrc or ~/.zshrc) ---")
    print(snippet)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Install shell completion for update_status.py.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--bash", action="store_true", help="Install for bash (~/.bashrc)")
    group.add_argument("--zsh", action="store_true", help="Install for zsh (~/.zshrc)")
    group.add_argument("--fish", action="store_true", help="Install for fish (~/.config/fish/completions/)")
    group.add_argument("--print", action="store_true", help="Print snippet only — no files modified")

    args = parser.parse_args()

    if args.print:
        shell = "fish" if args.fish else "bash"
        print_snippet(shell)
        return

    if not check_argcomplete():
        sys.exit(1)

    if args.bash:
        append_to_file(Path("~/.bashrc"), generate_bash_snippet(), "bash")
    elif args.zsh:
        append_to_file(Path("~/.zshrc"), generate_bash_snippet(), "zsh")
    elif args.fish:
        install_fish()


if __name__ == "__main__":
    main()
