# Sharing agentops — Ready-to-Use Posts

## Hacker News — "Show HN"

Title:
> Show HN: agentops – multi-agent orchestration for Claude Code with dashboard and wiki

Body (600 chars):
> agentops treats Claude Code like a real team rather than a single assistant.
> 
> You get 33 specialist agents (data, dev, pptx, GIS, ML...), a live WebSocket dashboard showing who's doing what, a knowledge wiki that gets smarter every session, and a native issue tracker — all wired together via CLAUDE.md hooks.
> 
> The key insight: AI productivity is determined by context management, not model power. agentops solves this with the MoC pattern (load only the relevant domain index + 1-2 notes, never the whole wiki) and session capture hooks that cost zero tokens.
> 
> Docker: `docker compose up` and dashboard is at :8000. No Python required.
> 
> GitHub: https://github.com/baramgay/agentops

## Reddit — r/ClaudeAI, r/LocalLLaMA, r/SideProject

Title:
> I built a multi-agent framework specifically for Claude Code — 33 agents, live dashboard, and a wiki that accumulates knowledge across sessions

Body:
> Tired of re-explaining your project to Claude every session? I built agentops to solve this.
> 
> The idea: instead of one Claude assistant with a massive CLAUDE.md, you have a team:
> - Orchestrator assigns work to team leads
> - Team leads dispatch to specialists (eda-analyst, backend, frontend, etc.)
> - Work is logged, decisions go in the wiki, issues go in the tracker
> - Every session starts by reading only the relevant wiki section — not the whole history
> 
> The result: complex multi-week projects stay coherent, and Claude gets progressively better at your specific domain.
> 
> 🐳 Zero-dependency start: `docker compose up` → dashboard at http://localhost:8000
> 
> GitHub: https://github.com/baramgay/agentops
> 
> Happy to answer questions about the architecture!

## Twitter/X thread (7 tweets)

Tweet 1:
> I built agentops: multi-agent orchestration for Claude Code 🧵
> 
> The problem: Claude forgets everything between sessions. The fix: give it a persistent team structure.
> 
> github.com/baramgay/agentops

Tweet 2:
> Instead of one assistant re-reading a huge CLAUDE.md every time, you have:
> 
> ↳ Orchestrator → Team Lead → Specialist
> 
> Each specialist has memory. Work is logged. Knowledge accumulates in a wiki.

Tweet 3:
> The dashboard shows your entire AI team in real-time:
> - Who's working on what
> - Issue tracker (create, assign, move)
> - Wiki browser
> - Audit log of all agent activity

Tweet 4:
> Token efficiency is built in:
> 
> The wiki uses Maps of Content (MoC) — you load ONE domain index + 1-2 target notes instead of the whole wiki.
> 
> At 150k tokens Claude auto-compacts — but only AFTER you've saved key decisions to the wiki.

Tweet 5:
> Getting started is 3 commands:
> 
> git clone github.com/baramgay/agentops
> cp .env.example .env
> docker compose up
> 
> Dashboard → localhost:8000. No Python needed.

Tweet 6:
> The framework comes with 33 pre-built specialist agents:
> data-collector, eda-analyst, ml-engineer, gis-specialist, frontend, backend, dba, architect, devops, reporter, pptx-builder, and more.
> 
> Each has a role definition you can customize.

Tweet 7:
> Open source, MIT license, PRs welcome.
> 
> github.com/baramgay/agentops ⭐

## LinkedIn post

> I've been building something for developers who use Claude Code heavily.
> 
> The problem: Claude Code resets every session. You re-explain your architecture, your conventions, your in-progress work — every time. For a 2-hour task, fine. For a 2-week project, brutal.
> 
> agentops solves this with a persistent multi-agent system:
> • 33 specialized agents, each with memory and a defined role
> • A live dashboard showing real-time agent status
> • A knowledge wiki that accumulates learnings automatically
> • A native issue tracker — no Jira, no Linear needed
> 
> The framework uses a vertical chain (Orchestrator → Team Lead → Specialist) so complex work flows predictably without losing context.
> 
> Built for Claude Code specifically. Open source, MIT, Docker-first.
> 
> Link in comments 👇
