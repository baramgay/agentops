# Example: Dev Team Web App

This example shows how to build a web application from spec to deployment using agentops' dev team agents.

## Scenario

Internal dashboard for tracking regional public service usage. Requirements come in on Monday; the app is in staging by Friday.

## Agent Chain

```
orchestrator
  └── lead-dev
        ├── requirements    → spec document, user stories
        ├── ux-designer     → wireframes, component map
        ├── architect       → tech stack ADR, data model
        ├── dba             → schema, migrations
        ├── backend         → FastAPI endpoints, auth
        ├── frontend        → React UI, charts
        ├── tester-unit     → pytest + vitest suites
        ├── tester-qa       → integration + E2E
        └── devops          → Docker, CI/CD, staging deploy
```

## Step-by-Step

```bash
# 1. Kick off
python scripts/update_status.py orchestrator working "Build public-service dashboard — sprint 1"
python scripts/update_status.py lead-dev working "Coordinating full-stack build"

# 2. Requirements
python scripts/update_status.py requirements working "Drafting spec from stakeholder notes"
python scripts/update_status.py requirements done "12 user stories, 3 epics — saved to docs/spec.md"

# 3. UX
python scripts/update_status.py ux-designer working "Wireframes for dashboard + detail views"
python scripts/update_status.py ux-designer done "5 screen wireframes in docs/wireframes/"

# 4. Architecture
python scripts/update_status.py architect working "ADR: Next.js + FastAPI + PostgreSQL"
python scripts/update_status.py architect done "ADR saved to wiki/notes/project/dashboard-adr.md"

# 5. Database
python scripts/update_status.py dba working "Schema design + Alembic migrations"
python scripts/update_status.py dba done "4 tables, 2 indexes, migrations in db/migrations/"

# 6. Backend
python scripts/update_status.py backend working "REST API: /services, /regions, /stats endpoints"
python scripts/update_status.py backend done "11 endpoints with auth, 100% coverage"

# 7. Frontend
python scripts/update_status.py frontend working "React dashboard: map + charts + filters"
python scripts/update_status.py frontend done "Dashboard live at localhost:3000, mobile-responsive"

# 8. Testing
python scripts/update_status.py tester-unit working "pytest backend + vitest frontend"
python scripts/update_status.py tester-unit done "247/247 tests passing"
python scripts/update_status.py tester-qa working "Integration + Playwright E2E"
python scripts/update_status.py tester-qa done "All 18 user journeys pass"

# 9. Deploy
python scripts/update_status.py devops working "Docker build + push + staging deploy"
python scripts/update_status.py devops done "Deployed to staging.internal — health check green"

# 10. Close the chain
python scripts/update_status.py lead-dev done "Sprint 1 complete — all 9 agents done"
python scripts/update_status.py orchestrator done "Dashboard in staging — ready for stakeholder review"
```

## What Gets Persisted

- The architecture decision record (ADR) lives in `wiki/notes/project/dashboard-adr.md`
- Next project that uses FastAPI + Next.js reads the ADR — no re-deciding the same trade-offs
- Tester-qa's E2E patterns go to `wiki/notes/method/playwright-e2e-patterns.md`
- Dashboard shows the full week's audit trail — every agent, every task, timestamped

## Issue Tracking

```bash
# Bug found in QA
python scripts/issue_create.py "Map z-index overlaps nav bar on mobile" \
  "Repro: iPhone 14 Safari, /dashboard route" frontend medium

# GNI-7 auto-transitions as frontend fixes and tester-qa verifies:
#   created → in_progress (frontend working)
#   in_progress → in_review (tester-qa reviewing)
#   in_review → done (tester-qa done)
```

## Result

A production-ready app with a complete audit trail, architecture decisions in the wiki, and a test suite — built by a coordinated agent team that remembers everything.
