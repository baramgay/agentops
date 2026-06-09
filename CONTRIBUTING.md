# Contributing to agentops

Thank you for your interest in agentops! This project is built on the idea that AI tools work better with **structure**, and contributions that add structure, clarity, or new agent definitions are especially welcome.

## Ways to contribute

### Add a new agent definition

The fastest way to contribute. Create two files:

```
agents/<your-agent-id>/
├── role.md    # Who the agent is and what it does
└── memory.md  # Accumulated knowledge (starts empty)
```

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

### Improve the dashboard

`index.html` is a single-file dashboard. Improvements welcome:
- Better mobile responsiveness
- New views (timeline, agent dependency graph)
- Dark mode

### Add wiki content

`wiki/notes/method/` is the best place for reusable methodology notes. Format:

```markdown
---
name: your-method-slug
type: method
domain: development   # agents시스템 | development | data-analysis
updated: YYYY-MM-DD
---

# Method Title

Conclusion. Why. How to apply.
```

Run `python scripts/wiki_cleanup.py` after adding notes to auto-register in MoC.

### Fix bugs / improve scripts

Scripts are in `scripts/`. Core ones:
- `update_status.py` — agent status CLI
- `api_server.py` — FastAPI server (dashboard + WebSocket + issues API)
- `wiki_cleanup.py` — MoC coverage maintenance

## Development setup

```bash
git clone https://github.com/your-github-username/agentops.git
cd agentops
pip install -r requirements.txt
python scripts/setup.py
python scripts/api_server.py   # http://localhost:8000
```

## Pull request checklist

- [ ] Tested locally (`python scripts/validate.py`)
- [ ] No personal data or hardcoded paths
- [ ] Use `AGENTS_HOME` environment variable for all paths
- [ ] New agents include both `role.md` and `memory.md`
- [ ] Wiki notes follow the frontmatter format

## Questions?

Open an issue with the `question` label. We respond to all issues.
