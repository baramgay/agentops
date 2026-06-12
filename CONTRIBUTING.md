# Contributing to agentops

Thank you for helping make agentops better!

## Quick start for contributors

```bash
git clone https://github.com/baramgay/agentops.git
cd agentops
pip install -r requirements.txt
python scripts/api_server.py   # verify dashboard loads at http://localhost:8000
```

## What to work on

- Issues labeled [`good first issue`](https://github.com/baramgay/agentops/labels/good%20first%20issue) are a great entry point
- Issues labeled [`help wanted`](https://github.com/baramgay/agentops/labels/help%20wanted) are higher priority

## Branch naming

| Type | Pattern | Example |
|------|---------|---------|
| Feature | `feat/description` | `feat/slack-notifications` |
| Bug fix | `fix/description` | `fix/websocket-reconnect` |
| Docs | `docs/description` | `docs/docker-setup` |

## Commit style

Use conventional commits:
```
feat: add webhook notifications
fix: handle missing agent_status.json gracefully
docs: improve Docker quick start
```

## Adding a new agent

1. Create `agents/<agent-id>/role.md` — describe the agent's identity, responsibilities, and principles
2. Add the agent ID to `agent_status.json` with status `"idle"`
3. Document it in `wiki/MoC/agents-system.md`

**role.md template:**
```markdown
# Agent: <Name>

## Role
One sentence: what this agent is responsible for.

## Responsibilities
- Bullet list of core tasks

## Input / Output
- Input: what triggers this agent
- Output: what it produces

## Team
- Reports to: `lead-<team>`
- Collaborates with: `agent-id-1`, `agent-id-2`
```

**Existing agents to model after:** `agents/eda-analyst/`, `agents/backend/`, `agents/reporter/`

## Adding a wiki note

```markdown
---
name: my-note-slug
type: method          # feedback | project | reference | method
domain: development   # matches a MoC file name
updated: 2026-01-01
---

# Title

Conclusion. Why. How to apply.
```

Then run `python scripts/wiki_cleanup.py` to auto-register in MoC.

## Code style

- Python: follow PEP 8, use type hints where practical
- All code and comments in English
- No hard-coded paths — use `AGENTS_HOME` env var or `Path(__file__).parent`

## Testing

```bash
python scripts/validate_config.py   # config health check
python -c "import json; json.load(open('agent_status.json'))"   # JSON integrity
```

## Need help?

Open an issue or start a [discussion](https://github.com/baramgay/agentops/discussions).
