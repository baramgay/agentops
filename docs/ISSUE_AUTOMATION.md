# Issue Automation

This repository uses GitHub Actions and Claude AI to automatically triage, respond to, and attempt fixes for GitHub issues.

## What Happens When You Open an Issue

1. The **Issue Triage** workflow (`issue-triage.yml`) triggers immediately.
2. It calls `scripts/issue_bot.py triage`, which:
   - Sends the issue title and body to Claude (claude-opus-4-5).
   - Receives a classification: `bug`, `enhancement`, or `question`.
   - Applies the matching label to the issue.
   - Posts a friendly AI-generated comment explaining next steps.
3. If the `ANTHROPIC_API_KEY` secret is not configured, the bot falls back to a keyword-based static classifier — no AI, but still functional.

## How to Trigger Automated Fixing

There are two ways to request an automated fix:

### Option 1 — Add the `autofix` label

Add the `autofix` label to any open issue. The **Issue Autofix** workflow will start automatically.

### Option 2 — Post `/autofix` as a comment

The repository owner can comment `/autofix` (exactly, on its own line) on any issue. The workflow will detect this and begin.

### What Autofix Does

1. Calls `scripts/issue_bot.py autofix` with the issue title and body.
2. Asks Claude to produce a unified diff that resolves the issue.
3. If Claude returns a valid patch:
   - Creates a new branch `autofix/issue-<N>`.
   - Applies and commits the patch.
   - Pushes the branch and opens a Pull Request.
   - Posts a comment on the issue linking to the PR.
4. If Claude responds with `CANNOT_AUTOFIX` (issue too complex), a comment is posted explaining that manual review is needed.

> **Note:** Always review auto-generated PRs carefully before merging. The AI may misunderstand intent or make incorrect assumptions.

## Stale Issue Management

The **Stale** workflow (`issue-stale.yml`) runs every Monday at 09:00 UTC.

| Threshold | Value |
|-----------|-------|
| Days before marked stale | 60 |
| Days before closed (after stale) | 14 |

Issues and PRs with the labels `pinned`, `security`, `in-progress`, or `blocked` are **never** marked stale.

## Required Secrets

| Secret | Required | Description |
|--------|----------|-------------|
| `ANTHROPIC_API_KEY` | Recommended | Enables AI-powered triage and autofix. Without it, triage falls back to keyword matching and autofix is unavailable. |
| `GITHUB_TOKEN` | Auto-provided | Standard GitHub Actions token used for labeling, commenting, and opening PRs. No manual setup needed. |

### Setting Up `ANTHROPIC_API_KEY`

1. Obtain an API key from [console.anthropic.com](https://console.anthropic.com).
2. In your repository, go to **Settings > Secrets and variables > Actions**.
3. Click **New repository secret**.
4. Name: `ANTHROPIC_API_KEY`, Value: your key.

## File Reference

| File | Purpose |
|------|---------|
| `scripts/issue_bot.py` | Core automation script (triage + autofix logic) |
| `.github/workflows/issue-triage.yml` | Triggers on issue open/reopen |
| `.github/workflows/issue-autofix.yml` | Triggers on `autofix` label or `/autofix` comment |
| `.github/workflows/issue-stale.yml` | Weekly stale issue sweep |
