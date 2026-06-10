# Promotion Drafts

## Hacker News — Show HN

**Title:**
Show HN: agentops – Multi-agent orchestration framework for Claude Code (33 agents, live dashboard, built-in wiki)

**Body:**

I've been using Claude Code heavily for real work (data analysis, report generation, GIS, PPTX automation) and kept hitting the same wall: complex, multi-week projects don't stay coherent across sessions. Claude ends up being a generalist juggling everything at once, repeating context every session.

So I built agentops: a structured multi-agent framework that treats your AI work like a real team.

**Core architecture:**

- 33 specialized agents (data analyst, backend dev, GIS specialist, PPTX builder, statistician, etc.)
- Vertical command chain: Orchestrator → Team Lead → Specialist. No skipping. This prevents context pollution between domains.
- Every task goes through `update_status.py [agent_id] working/done "[description]"` — creating an append-only audit trail.

**What's included out of the box:**

- FastAPI server with WebSocket real-time sync
- Live kanban dashboard (single `index.html`, no build step)
- Native issue tracker with GNI-N numbering — auto-transitions on agent status updates
- Obsidian-compatible wiki with Maps of Content (MoC) — loads only 1-2 relevant notes per task, not the whole KB
- Session capture hooks: zero LLM cost, appends facts to wiki automatically at session end
- Claude Code hooks for auto-MoC registration, health checks, pre-compact wiki save nudge

**Token efficiency is a first-class concern:**

- opusplan model: Opus reasons (50k thinking tokens) + Sonnet outputs
- MoC-based reading: Claude reads domain index first, then only the notes it needs
- autoCompact at 150k tokens
- Subagent searches use Haiku to minimize cost

I've been running this in production for ~3 months. It handles multi-week projects with 5+ domains without losing coherence.

GitHub: https://github.com/baramgay/agentops

Happy to answer questions about the architecture, especially the vertical chain pattern and the wiki/MoC approach.

---

**Timing tip:** Post Tuesday–Thursday 8–10am ET for maximum HN visibility.

---

## Reddit — r/ClaudeAI

**Title:**
I built a multi-agent orchestration system for Claude Code after getting frustrated with context loss on complex projects

**Body:**

Like a lot of you, I use Claude Code heavily for real work — data analysis, report generation, GIS mapping, PPTX automation. The problem: complex, multi-week projects fall apart across sessions. Claude becomes a generalist juggling everything, re-explaining context every time.

So I built **agentops**: a structured framework that gives Claude Code a team of 33 specialized agents, a vertical command chain, a live dashboard, a built-in wiki, and a native issue tracker.

**The core idea:**

Instead of one Claude doing everything, tasks route through:
```
User → Orchestrator → Team Lead → Specialist Agent
                                       ↓
User ← Orchestrator ← Team Lead ← (review)
```

No skipping levels. This keeps context clean between domains (your data analysis agent doesn't know about your frontend code, and vice versa).

**What's in the box:**

- 33 pre-built agents (data analyst, backend dev, GIS specialist, statistician, PPTX builder, etc.)
- FastAPI server + WebSocket live kanban dashboard
- Native issue tracker (GNI-N format, auto-transitions on agent status)
- Obsidian-compatible wiki with Maps of Content — Claude reads only the relevant domain index + 1-2 notes per task
- Hooks for session capture (zero LLM cost), pre-compact wiki nudge, health checks

**Token efficiency:**

The wiki uses a "MoC-based reading" pattern: Claude reads the domain index first (`wiki/MoC/data-analysis.md`), then dives into only the specific notes it needs. This keeps context lean across long projects.

**GitHub:** https://github.com/baramgay/agentops (MIT license)

Happy to answer questions — especially about the vertical chain pattern, the wiki MoC approach, or how to adapt the agent roster to your own work.

---

## Reddit — r/LocalLLaMA

**Title:**
Claude Code orchestration framework with 33 specialized agents, vertical command chain, and built-in wiki — open source

**Body:**

Built this after months of using Claude Code for serious multi-domain work (data analysis + GIS + report generation + web apps). The context management problem gets real when you're running complex projects across weeks.

**agentops** is an open-source framework that adds structure on top of Claude Code:

**The vertical chain:**
```
Orchestrator → Team Lead → Specialist
```
Every task flows down, every result flows back up for review. No agent skips the chain. This is the key insight: it's not just about having multiple agents — it's about having *controlled* handoffs.

**Technical bits:**
- FastAPI server (port 8765) + static HTML dashboard — no Node.js, no build step
- WebSocket for real-time agent status + issue updates across tabs/sessions
- `agent_status.json` as the single source of truth (append-only `work_log.jsonl` audit trail)
- Obsidian-compatible wiki with Maps of Content (MoC): `wiki/MoC/domain.md` → links to atomic notes
- Session capture hook: at session end, transcript → wiki facts. Zero LLM calls. Zero tokens.
- Claude Code hooks: PostToolUse Write → auto-register notes in MoC, PreCompact → nudge to save to wiki first

**The opusplan model trick:**
Settings use `model=opusplan` which routes planning/reasoning to Opus (50k thinking tokens) and output to Sonnet. Exploration subagents use Haiku. Keeps costs sane on long projects.

33 agents pre-built (data analyst, backend dev, GIS specialist, PPTX builder, statistician, text analyst, etc.). Each has `role.md` + `memory.md`. The framework is model-agnostic at the agent level — you wire in whatever you want.

**GitHub:** https://github.com/baramgay/agentops

MIT. No cloud dependency. Runs entirely locally.

---

## Twitter/X

**Short version (under 280 chars):**

I got frustrated with Claude Code losing context on complex multi-week projects, so I built a multi-agent orchestration system: 33 specialized agents, vertical command chain, live dashboard, built-in wiki.

Open source. MIT. https://github.com/baramgay/agentops

**Thread opener:**

1/ Claude Code is great for one-off tasks. But complex, multi-domain projects across weeks? Context falls apart.

I built agentops to fix that. Here's how it works 🧵
