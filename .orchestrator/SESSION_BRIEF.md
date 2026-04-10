# SESSION BRIEF — Session 1
**Date:** 2026-04-10
**Orchestrator:** NeonGambit Build Orchestrator
**Branch base:** master
**Repo:** https://github.com/codeneural/neongambit_v5

---

## State on Entry

Repository initialized. No application code exists. All foundational documents present:
- `.agents/rules/project-context.md` ✅
- `.agents/rules/safety-guardrails.md` ✅
- `.agents/rules/git-workflow.md` ✅
- `.agents/rules/testing-standards.md` ✅
- `.agents/skills/*` (10 skill files) ✅
- `specs/feature-*.md` (6 feature specs) ✅
- `data/neon_templates.yaml` (200+ coaching templates, bilingual EN/ES) ✅
- `PROGRESS.md` — CREATED this session ✅
- `.orchestrator/SESSION_BRIEF.md` — this file ✅

---

## Key Architecture Decisions Confirmed (from project-context.md)

| ADR | Decision | Impact on build order |
|-----|----------|-----------------------|
| ADR-001 (project) | Next.js 14 App Router + FastAPI on VPS | Two separate scaffolds needed |
| ADR-002 (project) | Stockfish: client WASM for sparring, server for Glitch Report | Never call Stockfish in session service |
| ADR-003 (project) | Zustand flat stores, shadcn/ui | No Redux, no React Context for shared state |
| ADR-004 (project) | NEON templates 80% + Gemini 20% | Gemini only in glitch_report_worker + coach_service.generate_* |
| ADR-005 (project) | Hostinger VPS, PM2 + nginx | Backend deploy is NOT Vercel; separate deploy directive needed |
| ADR-006 (project) | i18n EN + ES from day 1 via next-intl | Every user-facing string needs en.json + es.json keys |

---

## Build Order Decided

### Phase 0 (Current — no dependencies)
1. **D-001: Backend Scaffold** — `/backend/` directory, all MVP DB models, Alembic, main.py, config.py, dependencies.py, /health endpoint, conftest.py
2. **D-002: Frontend Scaffold** — `/frontend/` Next.js 14, Tailwind + design tokens, shadcn/ui, all Zustand stores (empty), i18n setup, BottomNav shell, API client

### Phase 1 (depends on Phase 0)
3. D-003: Auth Backend — `/auth/guest`, `/auth/validate`, `/auth/link-account`, JWT service, Firebase Admin init
4. D-004: Auth Frontend — useAuthStore boot sequence, sessionStorage JWT flow, Firebase Auth SDK, LichessConnectPrompt component

### Phase 2 (depends on Phase 1)
5. D-005: Lichess Import Backend — lichess_import_worker, `/lichess/import`, `/lichess/import/status`, Redis job tracking
6. D-006: Lichess Import Frontend — useLichessStore, LoadingTerminal component, username entry

### Phase 3 (depends on Phase 2)
7. D-007: Glitch Report Backend — glitch_report_worker, Stockfish analysis, Gemini narrative, collapse classification, `/glitch-report/*` endpoints
8. D-008: Glitch Report Frontend — useGlitchReportStore, GlitchReportReveal, CriticalOpeningCard, cinematic reveal

### Phase 4 (depends on Phase 1 + openings data)
9. D-009: Sparring Backend — session_service, chess move validation (python-chess), opponent move selection (Lichess Explorer), theory tracking, tilt detection
10. D-010: Sparring Frontend — Arena page, NeonChessboard, useSessionStore, useStockfish WASM hook (Web Worker), TheoryBar, TiltIntervention

### Phase 5 (depends on Phase 3 — openings must be in repertoire)
11. D-011: Neural Drill Backend — srs_service (SM-2), populate_cards_for_opening, `/drill/*` endpoints, free-tier 429 cap
12. D-012: Neural Drill Frontend — DrillCard, ShadowMove, useDrillStore, 5-second timer logic

### Phase 6 (depends on Phase 1, Phase 2, Phase 3, Phase 4, Phase 5)
13. D-013: Analytics Dashboard Backend — analytics_service, single `/analytics/dashboard` query, streak logic, opening improvements delta
14. D-014: Analytics Dashboard Frontend — MissionControl, RatingChart, OpeningImprovementRow, StreakBadge, useDashboardStore

### Phase 7 (depends on Phase 1)
15. D-015: Subscriptions Backend — Stripe checkout, webhooks (raw body), subscription model enforcement ⚠️ HUMAN REVIEW REQUIRED
16. D-016: Subscriptions Frontend — UpgradeModal, useSubscriptionStore, upgrade triggers ⚠️ HUMAN REVIEW REQUIRED

---

## Active Directive This Session

**D-001: Backend Scaffold** — see `.orchestrator/directives/D-001-backend-scaffold.md`

---

## Session Decisions Made

1. **Build order fixed** as above. No deviation without new directive.
2. **MVP models only** in D-001 — no Phase 2 tables (conversion_failures, endgame_drill_cards, achievements). Alembic migration is SHOWN but NOT RUN — human confirms before executing.
3. **Alembic initial migration** uses psycopg2 sync driver (as documented in database-neon SKILL.md).
4. **conftest.py** uses pytest-asyncio + httpx AsyncClient + in-memory SQLite for tests. Never uses production DATABASE_URL.
5. **D-001 does not include auth logic** — that is D-003. D-001 only scaffolds structure and models.
6. **Stripe and auth** directives (D-003, D-015, D-016) will be flagged ⚠️ HUMAN REVIEW REQUIRED before issuing.

---

## STOP_AND_ASK Triggers (none this session)

None encountered. Project context is clear. Proceeding with D-001.
