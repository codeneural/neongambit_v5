# NeonGambit — Project Context

## What This Is
NeonGambit is a chess opening training platform targeting players rated 1000–1700 ELO.
Core value: turns a player's Lichess game history into a personalized training plan.
The Glitch Report is the product's central hook — a diagnostic that tells players
exactly which openings they keep losing and why.

## User Emotional Arc
First open → "This looks serious" → Connect Lichess → "It knows my games" →
See Glitch Report → "Oh. THAT's why I keep losing" → Retain.
Every feature decision must serve this arc.

## Architecture Decisions (ADRs)

ADR-001: Frontend is Next.js 14 (App Router) PWA, not Flutter.
Reason: Antigravity's browser agent can verify Next.js in Chrome without compilation.

ADR-002: Stockfish split — client WASM for sparring, server for Glitch Report.
Reason: Eliminates server CPU costs during sparring. stockfish.wasm at depth 12 runs in <300ms client-side. Server Stockfish (depth 15) only used for async Glitch Report generation.

ADR-003: Zustand over Redux/Jotai. Reason: Flat stores are maximally legible for AI agents.
shadcn/ui over third-party component libraries. Reason: Components live in repo.

ADR-004: NEON coaching is template-first (80%) + Gemini (20%).
Reason: In-game coaching uses ~200 curated YAML templates (instant, no LLM call). Gemini only for Glitch Report narratives and session summaries. Ensures tone consistency, zero latency, and bounded costs.

ADR-005: Hostinger VPS over Render/Railway for backend.
Reason: Zero cold starts. Existing VPS already paid for. PM2 + nginx. Stockfish native binary.

ADR-006: Internationalization EN + ES from day 1 via next-intl.
Reason: Retroactive i18n is painful. Spanish-speaking chess community is a viable acquisition channel.

## Critical Business Rules
1. Free tier: max 20 Lichess games imported. ALL critical openings visible in Glitch Report. Only top 2 openings unlocked for training.
2. Stockfish server-side: ONLY for Glitch Report (depth 15, sample of 5 worst games per opening). NEVER during sparring.
3. Gemini calls: ONLY for Glitch Report narrative + session summary. NEVER during gameplay.
4. In-game coaching: template library in data/neon_templates.yaml (bilingual EN/ES).
5. Opening cache TTL: 30 days in Redis
6. Free user data retention: 90 days for lichess_games, 30 days for sessions
7. Glitch Report classifies collapse_type per opening: opening_error, tactical_blunder, positional_drift, time_pressure

## File Naming Conventions
- Python services: snake_case_service.py
- Python models: snake_case.py (singular entity name)
- TypeScript components: PascalCase.tsx
- TypeScript stores: useCamelCaseStore.ts
- TypeScript API files: camelCase.ts
- Test files: test_[filename].py (backend), [filename].test.ts (frontend)

## The Three Documents You Must Read Before Every Session
1. specs/feature-[current-feature].md — what to build
2. Master Guide v5.1 (neongambit-master-guide-v5.md) — source of truth
3. DESIGN.md — visual reference
