"""
issue_bot.py - Automated GitHub issue triage and resolution via Claude API.

Subcommands:
  triage   - Classify an issue, apply GitHub labels, post an AI-generated response.
  autofix  - Attempt to implement a simple fix automatically, then open a PR.
"""

import sys
import os
import argparse
import subprocess
import json

# Windows console encoding guard - must be first
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LABEL_BUG = "bug"
LABEL_ENHANCEMENT = "enhancement"
LABEL_QUESTION = "question"

# Labels that must exist in the repository before they can be applied.
KNOWN_LABELS = {LABEL_BUG, LABEL_ENHANCEMENT, LABEL_QUESTION}

# ---------------------------------------------------------------------------
# Claude helpers
# ---------------------------------------------------------------------------

def _build_triage_prompt(title: str, body: str) -> str:
    return f"""You are a helpful open-source maintainer triaging GitHub issues.

Given the issue below, respond with a JSON object that has exactly two keys:
  "label"    - one of: "bug", "enhancement", "question"
  "comment"  - a short, friendly Markdown comment (2-4 sentences) to post on the issue.

Issue title: {title}

Issue body:
{body}

Respond ONLY with the JSON object. No extra text, no code fences."""


def _build_autofix_prompt(title: str, body: str) -> str:
    return f"""You are an experienced software engineer.

A GitHub issue has been tagged for automated fixing. Read the issue and produce a
unified diff (git diff format) that resolves it, OR respond with the text
"CANNOT_AUTOFIX" if it is too complex, ambiguous, or requires human judgment.

Issue title: {title}

Issue body:
{body}

If you can fix it, output ONLY the unified diff with no extra explanation.
If you cannot, output ONLY the text: CANNOT_AUTOFIX"""


def call_claude(prompt: str) -> str:
    """
    Call Claude via the Anthropic Python client.
    Returns the assistant's text response.
    Raises RuntimeError if the API key is missing.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY environment variable is not set.")

    import anthropic  # imported here so the script can still parse without the package

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()


# ---------------------------------------------------------------------------
# GitHub CLI helpers
# ---------------------------------------------------------------------------

def gh(*args: str) -> str:
    """Run a gh CLI command and return stdout. Raises on non-zero exit."""
    cmd = ["gh", *args]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(f"gh command failed: {' '.join(cmd)}\n{result.stderr}")
    return result.stdout.strip()


def ensure_label_exists(label: str) -> None:
    """Create the label in the repo if it does not already exist."""
    try:
        gh("label", "list", "--search", label, "--json", "name")
    except RuntimeError:
        pass  # Best-effort; gh label create will fail gracefully if it already exists.

    color_map = {
        LABEL_BUG: "d73a4a",
        LABEL_ENHANCEMENT: "a2eeef",
        LABEL_QUESTION: "d876e3",
    }
    color = color_map.get(label, "ededed")
    try:
        gh("label", "create", label, "--color", color, "--force")
    except RuntimeError:
        pass  # Already exists or no permission - non-fatal.


def apply_label(issue_number: int, label: str) -> None:
    """Apply a label to a GitHub issue (creates it first if needed)."""
    if label in KNOWN_LABELS:
        ensure_label_exists(label)
    gh("issue", "edit", str(issue_number), "--add-label", label)


def post_comment(issue_number: int, body: str) -> None:
    """Post a comment on a GitHub issue."""
    gh("issue", "comment", str(issue_number), "--body", body)


# ---------------------------------------------------------------------------
# Triage subcommand
# ---------------------------------------------------------------------------

STATIC_TRIAGE_RESPONSES = {
    "bug": {
        "label": "bug",
        "comment": (
            "Thank you for reporting this issue! It looks like a **bug**. "
            "A maintainer will investigate and follow up shortly. "
            "In the meantime, please share any additional reproduction steps if possible."
        ),
    },
    "enhancement": {
        "label": "enhancement",
        "comment": (
            "Thanks for the suggestion! This has been classified as an **enhancement request**. "
            "We will review it as part of our roadmap planning. "
            "Feel free to add more context or use-cases if it helps."
        ),
    },
    "question": {
        "label": "question",
        "comment": (
            "Thanks for reaching out! This looks like a **question**. "
            "A maintainer will respond as soon as possible. "
            "You may also find answers in our documentation or existing issues."
        ),
    },
}


def _static_triage(title: str) -> dict:
    """Fallback classification based on simple keyword matching."""
    title_lower = title.lower()
    if any(kw in title_lower for kw in ("bug", "error", "fail", "crash", "broken", "fix")):
        return STATIC_TRIAGE_RESPONSES["bug"]
    if any(kw in title_lower for kw in ("add", "feat", "feature", "improve", "enhance", "request")):
        return STATIC_TRIAGE_RESPONSES["enhancement"]
    return STATIC_TRIAGE_RESPONSES["question"]


def cmd_triage(args: argparse.Namespace) -> int:
    """
    Classify the issue, apply the appropriate label, and post a comment.
    Returns 0 on success, 1 on failure.
    """
    issue_number: int = args.issue_number
    title: str = args.title
    body: str = args.body or ""

    print(f"[triage] Processing issue #{issue_number}: {title!r}", flush=True)

    # --- Try Claude, fall back to static response ---
    label = "question"
    comment_body = ""
    try:
        prompt = _build_triage_prompt(title, body)
        raw = call_claude(prompt)
        # Strip potential markdown code fences that the model may include.
        raw = raw.strip().strip("`").lstrip("json").strip()
        data = json.loads(raw)
        label = data.get("label", "question")
        if label not in KNOWN_LABELS:
            label = "question"
        comment_body = data.get("comment", "")
        print(f"[triage] Claude classified as '{label}'.", flush=True)
    except RuntimeError as exc:
        print(f"[triage] API unavailable ({exc}). Using static response.", flush=True)
        result = _static_triage(title)
        label = result["label"]
        comment_body = result["comment"]
    except (json.JSONDecodeError, KeyError) as exc:
        print(f"[triage] Could not parse Claude response ({exc}). Using static response.", flush=True)
        result = _static_triage(title)
        label = result["label"]
        comment_body = result["comment"]

    if not comment_body:
        comment_body = STATIC_TRIAGE_RESPONSES.get(label, STATIC_TRIAGE_RESPONSES["question"])["comment"]

    # --- Apply label ---
    try:
        apply_label(issue_number, label)
        print(f"[triage] Applied label '{label}' to issue #{issue_number}.", flush=True)
    except RuntimeError as exc:
        print(f"[triage] WARNING: Could not apply label: {exc}", flush=True)

    # --- Post comment ---
    try:
        post_comment(issue_number, comment_body)
        print(f"[triage] Posted comment on issue #{issue_number}.", flush=True)
    except RuntimeError as exc:
        print(f"[triage] WARNING: Could not post comment: {exc}", flush=True)
        return 1

    return 0


# ---------------------------------------------------------------------------
# Autofix subcommand
# ---------------------------------------------------------------------------

def cmd_autofix(args: argparse.Namespace) -> int:
    """
    Attempt to automatically fix a simple issue.
    Creates a branch with the patch and opens a PR.
    Returns 0 on success, 1 on failure or when fix is not possible.
    """
    issue_number: int = args.issue_number
    title: str = args.title
    body: str = args.body or ""

    print(f"[autofix] Processing issue #{issue_number}: {title!r}", flush=True)

    # --- Get diff from Claude ---
    diff_text = ""
    try:
        prompt = _build_autofix_prompt(title, body)
        raw = call_claude(prompt)
        if raw.strip() == "CANNOT_AUTOFIX":
            msg = (
                "I attempted an automated fix for this issue, but it appears too complex "
                "or ambiguous for an automated approach. A human maintainer will need to "
                "review and address it manually.\n\nThank you for your patience!"
            )
            try:
                post_comment(issue_number, msg)
            except RuntimeError:
                pass
            print("[autofix] Claude indicated the issue cannot be auto-fixed.", flush=True)
            return 1
        diff_text = raw
    except RuntimeError as exc:
        print(f"[autofix] API unavailable ({exc}). Cannot proceed without Claude.", flush=True)
        try:
            post_comment(
                issue_number,
                "Automated fix attempted but the AI service is currently unavailable. "
                "A maintainer will review this issue manually.",
            )
        except RuntimeError:
            pass
        return 1

    # --- Apply diff to a new branch ---
    branch_name = f"autofix/issue-{issue_number}"
    try:
        subprocess.run(["git", "checkout", "-b", branch_name], check=True)
    except subprocess.CalledProcessError as exc:
        print(f"[autofix] Could not create branch '{branch_name}': {exc}", flush=True)
        return 1

    try:
        patch_file = f"/tmp/autofix_{issue_number}.patch"
        with open(patch_file, "w", encoding="utf-8") as f:
            f.write(diff_text)
        result = subprocess.run(
            ["git", "apply", "--check", patch_file],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"[autofix] Patch does not apply cleanly:\n{result.stderr}", flush=True)
            _post_autofix_failure(issue_number, "The generated patch could not be applied cleanly.")
            return 1

        subprocess.run(["git", "apply", patch_file], check=True)
        subprocess.run(["git", "add", "-A"], check=True)
        subprocess.run(
            ["git", "commit", "-m", f"fix: automated resolution for issue #{issue_number}"],
            check=True,
        )
        subprocess.run(["git", "push", "origin", branch_name], check=True)
    except subprocess.CalledProcessError as exc:
        print(f"[autofix] Error during patch/commit/push: {exc}", flush=True)
        _post_autofix_failure(issue_number, str(exc))
        return 1

    # --- Open PR ---
    pr_title = f"fix: automated resolution for issue #{issue_number}"
    pr_body = (
        f"Closes #{issue_number}\n\n"
        "This PR was generated automatically by the issue-autofix workflow using Claude AI.\n\n"
        "**Please review carefully before merging.**"
    )
    try:
        pr_url = gh(
            "pr", "create",
            "--title", pr_title,
            "--body", pr_body,
            "--head", branch_name,
        )
        print(f"[autofix] PR created: {pr_url}", flush=True)
        post_comment(
            issue_number,
            f"An automated fix has been proposed in {pr_url}. "
            "Please review and merge if it looks correct.",
        )
    except RuntimeError as exc:
        print(f"[autofix] Could not create PR: {exc}", flush=True)
        return 1

    return 0


def _post_autofix_failure(issue_number: int, reason: str) -> None:
    try:
        post_comment(
            issue_number,
            f"Automated fix attempted but could not be completed. Reason: {reason}\n\n"
            "A maintainer will address this issue manually.",
        )
    except RuntimeError:
        pass


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="issue_bot",
        description="GitHub issue automation via Claude AI.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # --- triage ---
    p_triage = sub.add_parser("triage", help="Classify issue and post AI response.")
    p_triage.add_argument("--issue-number", type=int, required=True)
    p_triage.add_argument("--title", required=True)
    p_triage.add_argument("--body", default="")

    # --- autofix ---
    p_autofix = sub.add_parser("autofix", help="Attempt automated fix and open PR.")
    p_autofix.add_argument("--issue-number", type=int, required=True)
    p_autofix.add_argument("--title", required=True)
    p_autofix.add_argument("--body", default="")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "triage":
        return cmd_triage(args)
    if args.command == "autofix":
        return cmd_autofix(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
