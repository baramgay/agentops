# agentops 🤖

> **Production-ready multi-agent orchestration framework for Claude Code**

Stop juggling multiple AI sessions. agentops gives Claude Code a **persistent chain of specialized agents**, a live dashboard, a built-in wiki, and a native issue tracker — all wired together so complex work flows smoothly without losing context.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude-Code-orange)](https://claude.ai/code)
[![Agents](https://img.shields.io/badge/agents-33-blueviolet)](#-the-agent-system)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

---

![agentops dashboard](assets/dashboard-preview.png)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎯 **33 Specialized Agents** | Pre-built agents for data analysis, dev, PPTX, GIS, ML, and more |
| 📊 **Real-time Dashboard** | Live kanban board, agent status, issue tracker with WebSocket sync |
| 🧠 **Knowledge Wiki** | Obsidian-compatible wiki with auto-indexing (MoC pattern) |
| 🔗 **Native Issue Tracker** | Built-in GNI-N tracking — no Jira, no Linear needed |
| 🪝 **Claude Code Hooks** | Auto-register wiki notes, session capture, health checks |
| ⚡ **Token Efficiency** | opusplan + MoC-based context loading + autoCompact at 150k tokens |
| 🔄 **Vertical Chain** | OC → Lead → Agent command hierarchy with zero skipping |
| 🌐 **Multi-PC Sync** | Git-based wiki sync across machines |

---

## 🚀 Quick Start

### 🐳 Docker — zero-dependency (recommended)

No Python install required:

```bash
git clone https://github.com/baramgay/agentops.git
cd agentops
cp .env.example .env   # optional: fill in OPENAI_API_KEY for LLM features
docker compose up
# Dashboard → http://localhost:8000
```

> `agents/`, `wiki/`, `issues.json`, `agent_status.json`, and `projects.json` are mounted as volumes — edits on the host are reflected live and state persists across restarts.

---

### Manual setup

#### 1. Clone & set up

```bash
git clone https://github.com/baramgay/agentops.git
cd agentops
```

#### 2. Set the home path

**Windows (PowerShell)**:
```powershell
setx AGENTS_HOME "C:\path\to\agentops"
```

**macOS / Linux**:
```bash
echo 'export AGENTS_HOME="$HOME/agentops"' >> ~/.bashrc
source ~/.bashrc
```

#### 3. Install dependencies & initialize

```bash
pip install -r requirements.txt
python scripts/setup.py
```

#### 4. Start the server

```bash
python scripts/api_server.py
# Dashboard → http://localhost:8000
```

#### 5. Add to your Claude Code project

Copy `CLAUDE.md` into your project root (or merge with your existing one) and configure the `AGENTS_HOME` path.

---

## 🗂️ Project Structure

```
agentops/
├── agents/              # 33 specialized agent definitions
│   ├── orchestrator/    # Master coordinator
│   ├── lead-data/       # Data team lead
│   ├── lead-dev/        # Dev team lead
│   ├── eda-analyst/     # Exploratory data analysis
│   ├── backend/         # API & backend development
│   ├── frontend/        # UI & web development
│   └── ...              # 27 more agents
├── scripts/
│   ├── api_server.py    # FastAPI server (dashboard + WebSocket + issue API)
│   ├── update_status.py # CLI: declare agent working/done
│   ├── issue_create.py  # CLI: create & query issues
│   ├── wiki_cleanup.py  # Wiki MoC coverage maintenance
│   └── setup.py         # First-time initialization
├── wiki/
│   ├── 00_home.md       # Wiki index
│   ├── MoC/             # Maps of Content (domain indexes)
│   └── notes/           # Atomic notes (feedback/project/method/reference)
├── index.html           # Dashboard (open in browser)
├── CLAUDE.md            # Claude Code system instructions
└── settings.example.json
```

---

## 🤖 The Agent System

Every task — large or small — flows through the agent chain:

```
User → Orchestrator → Team Lead → Specialist Agent
                                        ↓
User ← Orchestrator ← Team Lead ← (review)
```

### Declare work (CLI)

```bash
# Simple task (single agent)
python scripts/update_status.py eda-analyst working "Analyzing sales data"
# ... do the work ...
python scripts/update_status.py eda-analyst done "EDA complete, 3 key findings"

# Complex task (full chain)
python scripts/update_status.py orchestrator working "Multi-domain analysis"
python scripts/update_status.py lead-data working "Coordinating data pipeline"
python scripts/update_status.py data-cleaner working "Cleaning Q1 dataset"
```

### Quick agent reference

| Task Type | Agent ID |
|-----------|----------|
| Data collection | `data-collector` |
| Data cleaning | `data-cleaner` |
| EDA / exploration | `eda-analyst` |
| Statistics | `statistician` |
| Machine learning | `ml-engineer` |
| GIS / spatial | `gis-specialist` |
| Frontend / UI | `frontend` |
| Backend / API | `backend` |
| Database | `dba` |
| Reporting | `reporter` |
| PPTX creation | `pptx-builder` |
| Architecture | `architect` |
| Multi-domain | `orchestrator` |

---

## 📋 Issue Tracker

Issues are tracked natively — no external tools required.

```bash
# Create an issue
python scripts/issue_create.py "Bug in data pipeline" "Description here" eda-analyst high

# List open issues
python scripts/issue_create.py --list open

# Get issue detail
python scripts/issue_create.py --get GNI-1
```

Issues auto-transition when agents report status:
- `working` → `in_progress`
- `review` → `in_review`
- `done` → `done`

---

## 🧠 Knowledge Wiki

The wiki uses **Maps of Content (MoC)** to keep knowledge organized without loading everything into context.

```
wiki/
├── MoC/
│   ├── agents-system.md    # Index of all agent-related notes
│   ├── data-analysis.md    # Data & statistics notes
│   └── development.md      # Dev patterns & decisions
└── notes/
    ├── feedback/           # Behavior corrections & confirmed approaches
    ├── method/             # Reusable methodologies
    ├── project/            # Project state & decisions
    └── reference/          # External tools & resources
```

**Write a note** (frontmatter required):

```markdown
---
name: my-decision-slug
type: method          # feedback | project | reference | method
domain: development   # matches a MoC file
updated: 2026-01-01
---

# Decision Title

Conclusion. Why. How to apply.
```

Run `python scripts/wiki_cleanup.py` to auto-register new notes into MoC files.

---

## ⚡ Token Efficiency

agentops is designed to work within Claude Code's context limits:

- **opusplan model**: Opus reasons (50k thinking tokens) + Sonnet outputs — quality at lower cost
- **MoC-based reading**: Load only the relevant domain index, then 1-2 target notes — never the whole wiki
- **autoCompact at 150k**: Automatically compresses context at the right threshold
- **Session capture hook**: Zero-cost transcript logging at session end (no LLM calls)

---

## 🪝 Claude Code Hooks

agentops registers hooks in `.claude/settings.json`:

| Hook | Trigger | Action |
|------|---------|--------|
| `session-start` | New session | Health check + wiki status |
| `session-end` | Session closes | Auto-capture transcript to wiki |
| `post-tool-use` (Write) | New wiki note saved | Auto-register in MoC |
| `pre-compact` | Context limit approaching | Nudge to save to wiki first |

---

## 🛠️ Configuration

Copy `settings.example.json` → `.claude/settings.json`:

```json
{
  "model": "claude-sonnet-4-6",
  "env": {
    "AGENTS_HOME": "/path/to/agentops"
  }
}
```

See `settings.example.json` for all options including opusplan, thinking tokens, and autoCompact.

---

## 📡 Dashboard

The dashboard (`index.html`) provides:

- **Agent Status**: Real-time kanban of all 33 agents
- **Issue Tracker**: Create, assign, move issues through pipeline stages
- **Wiki Browser**: Browse notes and MoC indexes
- **Work Log**: Append-only audit trail of all agent activity
- **Metaverse View**: Visual office layout with agent presence

Start the API server, then open `index.html` in your browser. WebSocket keeps everything live-synced.

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Follow the agent system pattern — document decisions in `wiki/notes/`
4. Submit a PR with a clear description

---

## 📄 License

MIT © agentops contributors. See [LICENSE](LICENSE).

---

## 🌟 Why agentops?

Most Claude Code setups are a single assistant with a long CLAUDE.md. agentops treats your AI work like a real team:

- Each domain has an **expert** (not a generalist wearing every hat)
- Work is **logged and audited** (not lost when the session ends)
- Knowledge **accumulates** in a searchable wiki (not repeated every session)
- Issues are **tracked natively** (not in a separate tool)

The result: complex multi-week projects stay coherent, and Claude gets better at your specific work over time.
