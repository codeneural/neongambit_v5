# NeonGambit — Agent Rules

## Project Identity
This is NeonGambit: a cyberpunk chess sparring and analysis platform.
Backend: FastAPI (Python 3.11+) in /backend
Frontend: Next.js 14 (TypeScript) in /frontend
Database: Neon PostgreSQL via SQLAlchemy async
Cache: Upstash Redis
Deployment: Backend → Hostinger KVM VPS (PM2 + nginx) | Frontend → Vercel

## Core Architecture Rules
- Backend is the source of truth for game state and move legality. Frontend is a dumb client.
- All business logic lives in /backend/app/services/. Routers are thin.
- All chess move VALIDATION is server-side. Never trust client FEN for legality.
- Move QUALITY EVALUATION runs client-side via stockfish.wasm (Web Worker). Server does NOT run Stockfish during sparring. See ADR-002 in project-context.md.
- In-game coaching uses the NEON template library (YAML). Gemini is only for Glitch Report narratives and session summaries. See ADR-004.
- Frontend state lives in Zustand flat stores only. No Redux, no Context.
- All colors must be imported from lib/utils/designTokens.ts. Never hardcode hex.
- All user-facing strings must use next-intl translation keys. Never hardcode text. Supported locales: en, es.

## Code Standards
- Python: PEP 8. Use Black formatting. Type hints on all function signatures.
- TypeScript: strict mode. No 'any'. Prefer const. Arrow functions for callbacks.
- All async Python functions must use async/await. No sync I/O in async context.
- All database operations go through SQLAlchemy sessions from get_db() dependency.
- Commits: conventional commits format (feat:, fix:, test:, docs:, refactor:)

## TDD Mandate
- Tests are written BEFORE implementation code. Always.
- No PR merges if test coverage drops below 80% for services.
- Every new API endpoint requires at least: happy path test, error test, auth test.
- pytest for backend. vitest for frontend.

## Safety Guardrails — NEVER do these without explicit confirmation
- Never run database migrations in production without asking
- Never delete files without explicit user confirmation
- Never push directly to main branch
- Never hardcode secrets, API keys, or credentials
- Never call Stockfish server-side during sparring sessions (use client WASM only)
- Never call Gemini/LLM during sparring gameplay (use template library only)
- Never bypass authentication on any endpoint except /auth/guest and /auth/validate
- Never modify PM2 or nginx config on the VPS without documenting changes

## Response Style
- Be concise. Skip basic explanations unless asked.
- When suggesting changes, explain the WHY, not just the WHAT.
- If you see a bug outside your current task, note it as a TODO comment.
- Always suggest the simplest solution first.
- When uncertain, ask rather than guessing.

## Git Workflow
- Feature branches: feature/[feature-name]
- Agent branches for large tasks: agent/[task-name]
- PR titles: "[type]: brief description (under 72 chars)"
- Always run tests before marking work complete.
