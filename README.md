# agentops

> **Stop re-explaining your project. Give Claude Code a persistent team.**

agentops turns Claude Code from a solo assistant into a **coordinated team of 33 specialized agents** — each with its own memory, role, and audit trail. Complex multi-week projects stay coherent. Claude gets better at your specific work over time.

[![CI](https://github.com/baramgay/agentops/actions/workflows/validate.yml/badge.svg)](https://github.com/baramgay/agentops/actions) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE) [![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org) [![Agents](https://img.shields.io/badge/agents-33-blueviolet)](#-the-agent-team) [![Docker](https://img.shields.io/badge/docker-ready-2496ED?logo=docker&logoColor=white)](#-docker-quick-start) [![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

---

## Why agentops?

You open Claude Code. You explain the project. You get work done. You close the session.

Next day: explain the project again.

**agentops fixes this.** Every decision, every lesson, every bug fix lands in a structured wiki and a live dashboard. Your agents remember. Your team grows.

---

## Comparison

| Feature | Claude Code alone | AutoGen | CrewAI | **agentops** |
|---------|:-----------------:|:-------:|:------:|:------------:|
| Persistent agent state across sessions | No | Partial | Partial | **Yes** |
| Real-time dashboard + kanban | No | No | No | **Yes** |
| Claude Code native (CLAUDE.md hooks) | — | No | No | **Yes** |
| Built-in wiki with MoC indexing | No | No | No | **Yes** |
| Native issue tracker (no Jira/Linear) | No | No | No | **Yes** |
| Token-efficient context loading | Manual | Manual | Manual | **Auto (MoC)** |
| Zero extra API cost | Yes | No | No | **Yes** |
| Vertical command chain (OC→Lead→Agent) | No | Partial | Partial | **Yes** |
| Session transcript auto-capture | No | No | No | **Yes** |
| Metaverse office visualization | No | No | No | **Yes** |

---

## How It Works

```
User
  |
  v
CLAUDE.md (system rules + agent registry)
  |
  v
Orchestrator (OC) ---- coordinates ---> Wiki
  |                                      |
  v                                      |
Team Lead (lead-data / lead-dev / lead-pptx)
  |                                      |
  v                                      v
Specialist Agent ----- result -------> Dashboard
(eda-analyst, backend, gis-specialist, ...)

Issue Tracker auto-transitions:
  working -> in_progress -> review -> done
```

Every status update writes to `agent_status.json`, broadcasts via WebSocket to the dashboard, and optionally transitions a linked issue.

---

## 30-Second Demo

```bash
# Declare work -- the agent system takes over
$ python scripts/update_status.py eda-analyst working "Analyzing Q1 sales"
[eda-analyst] working: Analyzing Q1 sales

# ... Claude does the actual work here ...

$ python scripts/update_status.py eda-analyst done "Found 3 anomalies in March data"
[eda-analyst] done: Found 3 anomalies in March data
```

Complex task with full chain:

```bash
$ python scripts/update_status.py orchestrator working "Q1 sales deep-dive report"
$ python scripts/update_status.py lead-data working "Coordinating: collector -> cleaner -> EDA -> reporter"
$ python scripts/update_status.py data-collector working "Fetching Q1 raw sales data"
[data-collector] done: 142,000 rows pulled
$ python scripts/update_status.py data-cleaner working "Removing duplicates, fixing dtypes"
[data-cleaner] done: 98.7% data quality score
$ python scripts/update_status.py eda-analyst working "Trend + anomaly detection"
[eda-analyst] done: 3 anomalies in March, regional breakdown ready
$ python scripts/update_status.py reporter working "Building executive summary"
[reporter] done: PPTX + PDF delivered to /reports/
```

---

## Docker Quick Start

The fastest way to get the dashboard running:

```bash
docker run -p 8000:8000 \
  -v $(pwd)/agents:/app/agents \
  -v $(pwd)/wiki:/app/wiki \
  ghcr.io/baramgay/agentops:latest
```

Dashboard opens at **http://localhost:8000**

**Or with docker compose:**

```bash
git clone https://github.com/baramgay/agentops.git
cd agentops
docker compose up
```

---

## Real-World Use Cases

- **Monthly policy reports at scale** -- A public data center uses agentops to run a 6-agent pipeline (data-collector -> data-cleaner -> statistician -> gis-specialist -> visualizer -> reporter) that produces a 30-page regional housing report every month. The wiki retains every analytical decision, so the next month's run needs zero re-briefing.

- **Full-stack web app from spec to deploy** -- A dev team routes requirements -> ux-designer -> frontend -> backend -> dba -> tester-qa -> devops through the vertical chain. Each agent's output is linked to a GNI issue. When the PR merges, the issue auto-closes.

- **GIS + machine learning research** -- A spatial analyst queries the gis-specialist for boundary data, hands off to ml-engineer for clustering, and gets a choropleth map back -- all with a two-line audit trail in the dashboard and the methodology saved to `wiki/notes/method/`.

---

## Manual Setup

```bash
git clone https://github.com/baramgay/agentops.git
cd agentops
pip install -r requirements.txt
python scripts/setup.py
python scripts/api_server.py
# Dashboard -> http://localhost:8000
```

Add to your project's `CLAUDE.md`:

```markdown
# Agent System
- Home: /path/to/agentops
- Every task flows through update_status.py
- See CLAUDE.md in agentops/ for full protocol
```

---

## The Agent Team

33 specialized agents across three teams:

| Team | Lead | Agents |
|------|------|--------|
| **Data** | `lead-data` | data-collector, data-cleaner, eda-analyst, statistician, ml-engineer, deep-learning, gis-specialist, text-analyst, visualizer, reporter, realty-analyst |
| **Dev** | `lead-dev` | requirements, ux-designer, frontend, backend, dba, security, tester-unit, tester-qa, devops, tech-writer, statworkbench, architect, tester |
| **PPTX** | `lead-pptx` | pptx-planner, pptx-content, pptx-designer, pptx-builder, pptx-reviewer |

Quick lookup:

| Task | Agent ID |
|------|----------|
| Exploratory analysis | `eda-analyst` |
| Machine learning | `ml-engineer` |
| GIS / spatial | `gis-specialist` |
| Frontend / UI | `frontend` |
| Backend / API | `backend` |
| Database | `dba` |
| Architecture | `architect` |
| Slide deck | `pptx-builder` |
| Multi-domain | `orchestrator` |

---

## Token Efficiency

agentops is designed to work *within* Claude's context window, not fight it:

- **opusplan model**: Opus reasons (50k thinking tokens) + Sonnet outputs -- best quality per token
- **MoC-based reading**: Load only the relevant domain index + 1-2 notes. Never the whole wiki.
- **autoCompact at 150k**: Context auto-compresses at the right threshold
- **Session capture hook**: Zero-LLM-cost transcript logging at session end
- **Pointer pattern**: Compressed context keeps `[[wiki-slug]]` references, not full content

---

## Knowledge Wiki

Every agent decision, bug fix, and methodology lands in a structured wiki:

```
wiki/
├── MoC/                    # Maps of Content -- domain indexes
│   ├── agents-system.md
│   ├── data-analysis.md
│   └── development.md
└── notes/
    ├── feedback/           # Behavior corrections
    ├── method/             # Reusable methodologies
    ├── project/            # Project state & decisions
    └── reference/          # External tools & resources
```

New notes auto-register into MoC via a `post-tool-use` hook -- zero manual indexing.

---

## Claude Code Hooks

```
session-start   -> Health check + load relevant wiki context
post-tool-use   -> Auto-register new wiki notes into MoC
pre-compact     -> Nudge to save key decisions to wiki first
session-end     -> Capture full transcript to wiki/notes/sessions/
```

---

## Roadmap

- [x] 33 specialist agents with role definitions
- [x] Real-time dashboard (kanban + issue tracker + wiki browser)
- [x] WebSocket live sync across browser tabs
- [x] Native issue tracker (GNI-N) with auto-transitions
- [x] GitHub Issues bidirectional sync
- [x] Metaverse office visualization (Phaser 3)
- [x] Claude Code hooks (session capture, MoC auto-register)
- [x] opusplan token efficiency system
- [x] Docker support
- [ ] Agent performance analytics (SLA tracking per agent)
- [ ] One-click agent scaffolding (`python scripts/new_agent.py`)
- [ ] MCP server for remote agentops access
- [ ] Web UI for wiki editing (not just browsing)
- [ ] Agent skill import/export marketplace
- [ ] Multi-user workspace support

---

## Project Structure

```
agentops/
├── agents/              # 33 agent definitions (role.md + memory.md each)
│   ├── orchestrator/
│   ├── lead-data/
│   ├── lead-dev/
│   └── ...
├── scripts/
│   ├── api_server.py    # FastAPI server (dashboard + WebSocket + issue API)
│   ├── update_status.py # CLI: declare agent working/done
│   ├── issue_create.py  # CLI: create & query issues
│   └── setup.py         # First-time initialization
├── wiki/
│   ├── MoC/             # Domain indexes
│   └── notes/           # Atomic notes
├── index.html           # Dashboard
├── metaverse.html       # Office visualization
├── CLAUDE.md            # Claude Code system instructions
└── examples/
    ├── 01-data-pipeline/ # Data team workflow example
    └── 02-web-app/       # Dev team workflow example
```

---

## Contributing

1. Fork the repo
2. `git checkout -b feat/your-feature`
3. Document decisions in `wiki/notes/`
4. Submit a PR -- see [CONTRIBUTING.md](CONTRIBUTING.md)

---

## License

MIT -- see [LICENSE](LICENSE)

---

[![Star History Chart](https://api.star-history.com/svg?repos=baramgay/agentops&type=Date)](https://star-history.com/#baramgay/agentops&Date)
