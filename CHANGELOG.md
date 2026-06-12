# Changelog

All notable changes to agentops are documented here.

---

## [Unreleased]

- Agent performance analytics (SLA tracking per agent)
- One-click agent scaffolding (`python scripts/new_agent.py`)
- MCP server for remote agentops access
- Web UI for wiki editing
- Agent skill import/export marketplace
- Multi-user workspace support

---

## [1.2.0] — 2026-06-04

### GitHub Issues Bidirectional Sync

- `scripts/github_sync.py`: urllib-based bidirectional sync between GNI issues and GitHub Issues
- `/api/github/status` and `/api/github/sync` endpoints (token value never logged)
- `config.local.json` (gitignored) holds PAT — committed config is always safe
- `validate.py` extended to 92 checks including PAT leak prevention
- Issue detail panel links to GitHub when `github_number` is set
- `metaverse.html`: instruction → issue creation shows bubble + log feedback

### Issue Core + Paperclip Integration

- Issue panel: switched from stale localStorage to live `/api/issues` server fetch
- `/api/instruct`: `create_issue` + `priority` options — instruction auto-creates a GNI issue in `in_progress`; inserting `(GNI-N)` in task string triggers auto-transition on `working/review/done`
- Instruction modal and metaverse instruction panel: "Register as issue" checkbox + priority selector

---

## [1.1.0] — 2026-05-29

### Dashboard & Infrastructure

- Overview tab fetches fresh data on every load
- Mobile responsive CSS (breakpoints at 480px and 768px)
- Loading overlay with progress bar
- Text ellipsis on log entries, card descriptions, and modal task text
- `/api/git-status` endpoint: branch, last commit, uncommitted files, ahead/behind
- `scripts/generate_reports_index.py`: auto-index the `/reports` folder
- Sync tab: real system-status dashboard with GitHub connection card

### Metaverse Office

- Walking animation improved (foot movement, speed 38)
- TV slide interval 5 seconds; team meeting cooldown 5 minutes
- Team zone labels in Korean (8 zones)
- Touch tap to open agent panel on mobile
- Agent panel scrolls; stays live-updated every 3 seconds while open
- `disperseAgents` coordinate fix; `agentPanel` left offset 364px

### Scripts

- `llm_provider.py`: mock responses diversified with per-agent personality prefixes
- `start_all.bat`: port conflict detection (8000/8765), venv check, auto-open browser
- `validate.yml`: tee logging + `GITHUB_STEP_SUMMARY` result digest

---

## [1.0.0] — 2026-05-28

### Initial Production Release

**Agent System**
- 33 specialist agents across Data, Dev, and PPTX teams
- Vertical command chain: OC → Lead → Agent (command) / Agent → Lead → OC (review)
- `update_status.py` CLI: `working`, `done`, `review`, `idle` transitions
- `issue_create.py` CLI: create, list, get GNI-N issues
- Native issue tracker with auto-transitions linked to agent status

**Dashboard (`index.html`)**
- Real-time kanban of all 33 agents
- Issue tracker: create, assign, pipeline stages
- Wiki browser: notes and MoC indexes
- Work log: append-only audit trail
- WebSocket live-sync across tabs
- Keyboard shortcuts + toast notifications + CSS transitions
- Manual tab v4.0 (11 sections)

**Metaverse Office (`metaverse.html`)**
- Phaser 3 pixel-art office (40x22 tiles, 48px/tile)
- 33 pixel-art agent characters
- Corridor-based pathfinding (`computeWaypoints`)
- Camera zoom/drag (mouse wheel 0.4x–2.5x, right-click drag)
- Agent status polling every 3 seconds
- SLA warnings, leaderboard, daily summary, search, bulk instruct
- Stale `working` auto-reset after 2 hours

**Knowledge Wiki**
- Obsidian-compatible vault structure
- Maps of Content (MoC) pattern for domain indexing
- `post-tool-use` hook: new notes auto-register into MoC
- `session-end` hook: transcript auto-captured to `wiki/notes/sessions/` (zero LLM cost)
- `pre-compact` hook: nudges to save to wiki before context compression

**Claude Code Integration**
- `CLAUDE.md` system instructions with full agent protocol
- `settings.example.json` with opusplan, 50k thinking tokens, autoCompact at 150k
- Hooks wired in `.claude/settings.json`

**CI/CD**
- `validate.yml`: 92-check validation suite
- `weekly_report.yml`: automated Monday 09:00 KST report
- `rotate.yml`: scheduled maintenance
- `sync.yml`: triggered on `agent_status.json` changes

---

## [0.x] — 2026-05-18 to 2026-05-27

### Foundation (Internal / Pre-release)

- Prototype: single CLAUDE.md with inline agent definitions
- Phaser 3 metaverse office prototype
- `monthly_report.py` initial version
- Basic `update_status.py` with JSON file persistence
- 8 initial agent role definitions
- PALETTE color system for metaverse rendering
