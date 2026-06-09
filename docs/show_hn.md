# Show HN Draft

Use this when posting to Hacker News.

---

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
