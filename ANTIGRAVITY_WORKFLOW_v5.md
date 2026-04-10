# NeonGambit — Antigravity Development Workflow

**Versión:** 2.0 — Aligned with Master Guide v5.1
**Metodología:** Spec-Driven Development (SDD) + Test-Driven Development (TDD)
**IDE:** Google Antigravity v1.20.5 (AgentKit 2.0)
**Master Guide:** v5.1 (single source of truth — MVP-Scoped · Stockfish WASM · Template Coach · i18n)
**Principio rector:** No se escribe código hasta que todo está especificado, planificado y los agentes tienen contexto completo.

---

## ÍNDICE

1. [Filosofía del Workflow](#1-filosofía-del-workflow)
2. [Mapa del Sistema de Archivos de Agentes](#2-mapa-del-sistema-de-archivos-de-agentes)
3. [Fase 0 — Diseño Visual con Google Stitch](#3-fase-0--diseño-visual-con-google-stitch)
4. [Fase 1 — Especificación Pre-Código](#4-fase-1--especificación-pre-código)
5. [Los Artefactos de Configuración](#5-los-artefactos-de-configuración)
6. [Estrategia Multi-Agente por Dominio](#6-estrategia-multi-agente-por-dominio)
7. [Workflows Reutilizables](#7-workflows-reutilizables)
8. [Integración con GitHub](#8-integración-con-github)
9. [Pipeline de Testing](#9-pipeline-de-testing)
10. [Pipeline de Deployment](#10-pipeline-de-deployment)
11. [Cómo Cargar Todo a Antigravity](#11-cómo-cargar-todo-a-antigravity)
12. [Secuencia de Ejecución Completa](#12-secuencia-de-ejecución-completa)

---

## 1. Filosofía del Workflow

### Por qué SDD + TDD con Antigravity

La promesa de los agentes de IA es real pero frágil. Un agente sin contexto escribe código genérico. Un agente con contexto completo escribe código que pertenece a tu proyecto específico.

**El error que matan proyectos:** poner a Antigravity a "hacer cosas" antes de que tenga:
- Las reglas del proyecto (AGENTS.md / GEMINI.md)
- El diseño visual (DESIGN.md via Stitch MCP)
- Las specs de cada feature (Skills)
- Los tests que debe pasar (TDD)
- Los workflows que definen su proceso (Workflows)

**El orden correcto:**

```
DISEÑO      ESPECIFICACIÓN      TESTS       IMPLEMENTACIÓN      DEPLOY
(Stitch) →  (Skills + Specs) →  (TDD) → → (Agentes)       →  (CI/CD)
   [Tú]         [Tú + Claude]    [Agentes]    [Agentes]          [Agentes]
```

Los agentes **nunca deben decidir qué construir**. Solo cómo construirlo.

### Cómo Funciona Antigravity AgentKit 2.0

Antigravity opera desde dos superficies principales: Manager (mission control) y Editor (código), mientras los agentes también operan en el terminal y un browser Chromium embebido.

Los 16 agentes especializados de AgentKit 2.0 abarcan frontend, backend, seguridad, testing e infraestructura. Cada agente está pre-equipado con skills de dominio específico, permitiéndole operar autónomamente en sub-tareas complejas.

**Los tres primitivos que controlan el comportamiento de los agentes:**

| Primitivo | Archivo | Propósito |
|-----------|---------|-----------|
| **Rules** | `AGENTS.md` / `GEMINI.md` | Restricciones globales siempre activas |
| **Skills** | `.agents/skills/*/SKILL.md` | Conocimiento domain-específico cargado bajo demanda |
| **Workflows** | `.agents/workflows/*.md` | Recetas de pasos múltiples invocadas con `/comando` |

Los Rules son las restricciones base que dictan el comportamiento del agente. Los Skills son paquetes reutilizables de conocimiento. Los Workflows son los orquestadores que conectan todo — invocados con comandos precedidos de `/`.

---

## 2. Mapa del Sistema de Archivos de Agentes

Esta es la estructura completa que debe existir en el repositorio **antes** de que Antigravity escriba una sola línea de código de la aplicación.

```
neongambit/
│
├── AGENTS.md                          # Reglas globales (leído por todos los AI tools)
├── GEMINI.md                          # Overrides específicos de Antigravity
├── CLAUDE.md                          # Para uso de Claude Code en VS Code (symlink a AGENTS.md)
├── DESIGN.md                          # Design DNA exportado desde Stitch MCP
│
├── .agents/
│   ├── rules/
│   │   ├── project-context.md         # Contexto permanente: stack, arquitectura, decisiones
│   │   ├── git-workflow.md            # Convenciones de commits, branches, PRs
│   │   ├── testing-standards.md       # Criterios de calidad, cobertura mínima
│   │   └── safety-guardrails.md       # Qué NUNCA hacer (prod, DB, secrets)
│   │
│   ├── skills/
│   │   ├── backend-fastapi/
│   │   │   └── SKILL.md               # Patrones FastAPI, async, services layer
│   │   ├── frontend-nextjs/
│   │   │   └── SKILL.md               # Patrones Next.js 14, App Router, Zustand, next-intl
│   │   ├── database-neon/
│   │   │   └── SKILL.md               # SQLAlchemy async, Alembic, query patterns
│   │   ├── chess-engine/
│   │   │   └── SKILL.md               # python-chess, Stockfish (server: Glitch Report only)
│   │   ├── stockfish-wasm/
│   │   │   └── SKILL.md               # Client-side stockfish.wasm, Web Worker, move classification
│   │   ├── srs-algorithm/
│   │   │   └── SKILL.md               # SM-2 spaced repetition implementation
│   │   ├── coach-templates/
│   │   │   └── SKILL.md               # NEON template library, pattern naming, i18n, ELO adaptation
│   │   ├── lichess-api/
│   │   │   └── SKILL.md               # Lichess REST + Explorer, NDJSON streaming, degraded mode
│   │   ├── stripe-integration/
│   │   │   └── SKILL.md               # Webhook handling, subscription lifecycle
│   │   ├── redis-caching/
│   │   │   └── SKILL.md               # Cache patterns, TTLs, key naming
│   │   └── stitch-design/
│   │       └── SKILL.md               # Cómo usar DESIGN.md para implementar UI
│   │
│   └── workflows/
│       ├── new-feature.md             # /new-feature — TDD cycle completo
│       ├── new-api-endpoint.md        # /new-endpoint — endpoint + test + schema
│       ├── run-tests.md               # /test — ejecutar y verificar test suite
│       ├── db-migration.md            # /migrate — crear y aplicar migración Alembic
│       ├── deploy-backend.md          # /deploy-backend — Hostinger VPS deployment (PM2 + nginx)
│       ├── deploy-frontend.md         # /deploy-frontend — Vercel deployment
│       ├── glitch-report-debug.md     # /debug-glitch — diagnóstico específico
│       └── code-review.md             # /review — análisis de calidad pre-merge
│
├── specs/                             # Feature specs completas (fuente de verdad)
│   ├── feature-auth.md                # Guest + Firebase + link account
│   ├── feature-lichess-import.md      # Import + degraded mode + no-Lichess fallback
│   ├── feature-glitch-report.md       # Report + collapse type classification + auto-assign repertoire
│   ├── feature-sparring-session.md    # Arena + client-side eval + template coaching + tilt detection
│   ├── feature-neural-drill.md        # SM-2 + queue + shadow hint
│   ├── feature-analytics-dashboard.md # Mission Control + rating sync + recommended session
│   └── feature-subscriptions.md       # Stripe checkout + webhooks + pro gates
│
├── backend/                           # FastAPI app (construido por agentes)
├── frontend/                          # Next.js app (construido por agentes)
├── data/
│   └── neon_templates.yaml            # NEON coaching template library (EN + ES)
├── .github/
│   └── workflows/
│       ├── ci-backend.yml
│       ├── ci-frontend.yml
│       └── deploy.yml
│
└── docker-compose.yml                 # Entorno local de desarrollo
```

---

## 3. Fase 0 — Diseño Visual con Google Stitch

### Por qué Stitch antes que Antigravity

El workflow práctico para la mayoría de los equipos en 2026: explorar en Stitch, refinar en Figma (opcional), construir en Antigravity. Google ha construido los conectores para que este pipeline funcione.

Para NeonGambit con su estética cyberpunk muy específica, Stitch es la herramienta correcta porque:
- Genera HTML/CSS/Tailwind directamente (no Figma-first)
- Exporta via MCP al Stitch Agent Skill de Antigravity
- Crea `DESIGN.md` automáticamente con todos los tokens de diseño
- Los agentes leen `DESIGN.md` como referencia visual durante la implementación

### Stitch no reemplaza nuestro Design System — lo valida

Ya tenemos un Design System completo en `FRONTEND_IMPLEMENTATION_GUIDE_v5.md` (sección 3) con tokens canónicos. Stitch sirve para:
1. **Validar visualmente** que los tokens se ven bien en pantalla real
2. **Generar prototipos** de las pantallas más complejas (Glitch Report reveal, Arena)
3. **Exportar el DESIGN.md** que los agentes usan como referencia durante desarrollo

### Proceso Stitch para NeonGambit

**Paso 1 — Configurar Stitch MCP en Antigravity**

```bash
# En Antigravity > Agent Manager > MCP Servers > "..."
# Buscar "Stitch" y hacer click en Install
# Pegar Stitch API Key cuando se solicite

# Verificar en el chat del agente:
# "List my Stitch projects"
```

**Paso 2 — Prompts para generar las pantallas clave**

Generar estas pantallas en Stitch en este orden (de más a menos críticas):

```
PROMPT 1 — Mission Control (Home):
"Cyberpunk chess training app dashboard called NeonGambit.
Dark theme: background #080810, primary accent #00E5FF (cyan neon),
secondary #E0008C (magenta), font Orbitron for headers.
Mobile-first portrait layout (375px width).
Show: user Lichess rating with +47 month delta in a glowing cyan card,
two opening progress bars (Sicilian 41%, Ruy Lopez 31%), 
a 'TODAY'S DRILL' section showing '7 moves due · Est. 6 min' with cyan start button,
a 'RECOMMENDED SESSION' section showing opening name and reason,
3-tab bottom navigation (Arena, Drill, Profile).
Glassmorphism cards with subtle borders. Streak flame badge in top-right."

PROMPT 2 — The Arena (Sparring Session):
"Cyberpunk chess game screen. Background #080810.
Top: horizontal theory integrity progress bar (73%, cyan to magenta gradient).
Center: chess board with dark squares #161625, light squares #0F0F1A,
cyan glow shadow around the board. Left side: vertical eval gauge (VU meter style).
Bottom: terminal-style coach feedback box with scanlines, green cursor,
JetBrains Mono font, text '> NEON: You are off-book at move 9. Focus.'
Very bottom: [Resign] button in glassmorphism style.
Portrait mobile layout."

PROMPT 3 — Glitch Report Reveal:
"Full screen dark cyberpunk diagnostic report.
Header: '⚡ GLITCH REPORT' in Orbitron font with cyan glow, '@username' subtitle.
Three 'CRITICAL VULNERABILITY' cards (all visible, not blurred) with 3px magenta left border,
red warning icon, opening name in white Orbitron, 
small collapse type badge below win rate (e.g. 'TACTICAL BLUNDER' in red, 'POSITIONAL DRIFT' in amber),
horizontal win rate bar (22% fill, magenta), 
italic diagnosis text in smaller font.
First two cards: cyan 'DRILL THIS OPENING' button.
Third card: locked button with padlock icon '🔒 DRILL THIS — Pro'.
Below: 'STRENGTHS' section in emerald green, two rows with checkmarks.
Bottom: large gray text box showing overall pattern analysis.
Very dramatic, data-breach aesthetic."

PROMPT 4 — Neural Drill:
"Cyberpunk chess memory drill screen.
Top: 'NEURAL DRILL' header, 'Move 3/7' counter, cyan progress bar.
Center: chess board at a specific position.
Below board: large glassmorphism card showing opening name and 
question '> NEON: What is Black\'s best move here?'
Bottom: two buttons — [SHADOW HINT] with amber/warning color, [SKIP] in gray.
Minimal, focused, no distractions."

PROMPT 5 — Profile/Settings:
"Cyberpunk chess player profile and settings screen.
Top: player username, Lichess rating 1387 with flame streak icon.
Lichess rating chart (line chart, cyan line, dark background, 8 weeks data).
Stats grid: wins, accuracy, sessions, drill cards.
Settings section: ELO target slider, language selector (EN/ES toggle),
Lichess username with re-sync button, upgrade CTA for free users."
```

**Paso 3 — Exportar DESIGN.md via Stitch MCP**

Una vez generadas las pantallas, en Antigravity Agent Manager:

```
"Use the Stitch MCP to fetch my NeonGambit project.
Extract ALL design tokens: exact hex colors, typography specs,
spacing values, border-radius values, shadow definitions, animation timing.
Generate a DESIGN.md file in the project root with this structure:
- Color tokens (with variable names matching our designTokens.ts)
- Typography scale
- Spacing scale
- Shadow definitions
- Animation timing
- Component patterns observed in the designs

Cross-reference with the canonical tokens in FRONTEND_IMPLEMENTATION_GUIDE_v5.md
and flag any discrepancies."
```

**Paso 4 — Verificar DESIGN.md contra design tokens existentes**

El agente debe confirmar que `DESIGN.md` es consistente con `lib/utils/designTokens.ts`. Si hay diferencias, `designTokens.ts` gana (es nuestra fuente de verdad).

**Paso 5 — Crear neon_templates.yaml (ANTES de Antigravity)**

Este paso es trabajo humano, no de agentes. Los agentes no saben ajedrez lo suficiente para escribir coaching táctico preciso. Debes crear `data/neon_templates.yaml` con al menos 50 templates antes de que los agentes empiecen a implementar el coaching.

```
Proceso:
1. Usar Claude para generar un borrador de ~200 templates siguiendo la estructura
   del Master Guide v5.1 Sección 5, Feature 4 (consecuencia → patrón → semilla)
2. TÚ revisas cada template para verificar precisión ajedrecística
3. TÚ creas las versiones en español (no dejar esto a traducción automática —
   el tono de NEON debe sonar natural en ambos idiomas)
4. Resultado: data/neon_templates.yaml con al menos:
   - 15 templates de blunder (hanging piece, fork, pin, discovered attack, positional)
   - 10 templates de mistake (tempo loss, positional drift, pawn structure)
   - 5 templates de inaccuracy
   - 10 templates de excellent (double threat, pin exploitation, tactical vision)
   - 5 templates de theory/survival
   - 5 templates de tilt
   Cada uno con variantes low/mid/high ELO × en/es = ~400 entries mínimo
5. Validar: cargar el YAML en Python, verificar que todas las keys existen,
   que ningún template excede 20 palabras, que los placeholders son consistentes
```

Este artefacto es tan importante como DESIGN.md — sin él, NEON no tiene voz durante el sparring.

---

## 4. Fase 1 — Especificación Pre-Código

### La regla de oro: Antigravity no escribe código de aplicación hasta que existan los 6 artefactos

| # | Artefacto | Propósito | Quién lo crea |
|---|-----------|-----------|---------------|
| 1 | `AGENTS.md` | Reglas globales para todos los agentes | Tú (con template abajo) |
| 2 | `GEMINI.md` | Overrides Antigravity-específicos | Tú (con template abajo) |
| 3 | `DESIGN.md` | Tokens visuales del diseño | Stitch MCP → Agente |
| 4 | Skills en `.agents/skills/` | Conocimiento domain-específico | Tú + Claude |
| 5 | Specs en `specs/` | Qué construir exactamente | Tú + Claude |
| 6 | `data/neon_templates.yaml` | Librería de coaching NEON (EN + ES) | Tú + Claude (tú revisas) |

La implementación solo inicia cuando los 6 están completos y en el repositorio.

### Cómo construir las Feature Specs

Cada feature spec en `specs/` debe seguir este formato:

```markdown
# Feature Spec: [Nombre de la Feature]

## Contexto del usuario
¿Qué problema resuelve para el "Frustrated Improver"?
¿Qué emoción debe generar?

## Comportamiento esperado
Descripción precisa de lo que debe hacer, en términos de usuario.

## Criterios de aceptación (BDD format)
GIVEN [contexto]
WHEN [acción]
THEN [resultado verificable]

## Contratos de API
Endpoints exactos con request/response (copiar del Master Guide)

## Estado del frontend
Qué stores de Zustand se actualizan y cómo

## Criterios de performance
Tiempos de respuesta máximos, límites de carga

## Edge cases
Qué pasa cuando falla, cuando no hay datos, cuando el usuario es guest

## Tests requeridos (antes de implementar)
Lista explícita de tests unitarios e integración que deben existir
```

---

## 5. Los Artefactos de Configuración

### 5.1 — AGENTS.md (Reglas Globales)

```markdown
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
```

### 5.2 — GEMINI.md (Overrides Antigravity-Específicos)

```markdown
# NeonGambit — Antigravity-Specific Configuration

## Agent Mode Preferences
- Use Planning Mode for any task that touches more than 2 files
- Use Fast Mode only for single-file changes and bug fixes
- Always generate Implementation Plan artifact before touching code on complex tasks
- Always produce a Walkthrough artifact after completing a mission

## Multi-Agent Orchestration
For missions involving both backend and frontend:
- Assign Backend Agent to services, routers, schemas
- Assign Frontend Agent to components, stores, hooks
- Assign Test Agent to write tests for both (runs in parallel)
- Never let one agent modify both backend and frontend in the same task

## Browser Agent Instructions
- After implementing any UI component, take a screenshot
- Compare screenshot against DESIGN.md color tokens and layout specs
- Flag any deviation from designTokens.ts canonical values
- Verify all Tailwind classes match the tailwind.config.js extensions

## Knowledge Base
Update the project Knowledge Base when:
- A non-obvious architectural pattern is established
- A bug is found and fixed that could recur
- A service integration behaves differently than documented
- A performance optimization is discovered

## Model Assignment
- Complex reasoning (architecture, debugging): Claude Opus 4.6
- Standard implementation (services, components): Gemini 3.1 Pro (High)
- Fast tasks (formatting, simple fixes): Gemini 3 Flash
- Frontend visual work: Gemini 3.1 Pro (High) — better Tailwind/React output

## File Organization Rules
- Backend agent works exclusively in /backend
- Frontend agent works exclusively in /frontend
- Neither agent touches the other's directory
- Shared types go in /shared/types/ (if created)
- Migration files created by Database Agent, reviewed by you before running
```

### 5.3 — project-context.md (Rule permanente de contexto)

```markdown
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
```

### 5.4 — testing-standards.md

```markdown
# Testing Standards

## Mandatory Coverage Thresholds
- Backend services: minimum 80% coverage
- Backend routers: minimum 70% coverage
- Frontend stores: minimum 75% coverage
- Frontend hooks: minimum 60% coverage

## Test Categories and When to Write Them

### Unit Tests (write FIRST — TDD)
For every service method:
- Happy path: normal input → expected output
- Edge case: boundary values, empty inputs
- Error case: invalid input → correct exception raised

### Integration Tests (write SECOND)
For every API endpoint:
- Auth: unauthenticated request → 401
- Valid request → correct response schema
- Invalid request → correct error code and message
- Rate limit: exceeding limit → 429

### E2E Tests (write THIRD — browser agent)
Critical user journeys only:
1. Guest → sparring session → debrief
2. Lichess connect → Glitch Report reveal
3. Neural drill → complete queue → streak update
4. Upgrade modal → Stripe checkout redirect

## Test File Locations
- Backend unit: /backend/tests/test_[service_name].py
- Backend integration: /backend/tests/test_[router_name].py
- Frontend unit: /frontend/lib/[module].test.ts
- Frontend E2E: /frontend/e2e/[journey].spec.ts

## Required Test Data
See /backend/tests/conftest.py for fixtures.
Never use production Lichess usernames in tests.
Use test username: "NeonGambitTestUser" (a real account with public games).
Never use real Stripe keys in tests. Use Stripe test mode keys.

## The TDD Cycle (enforced by /new-feature workflow)
1. Write failing test that describes expected behavior
2. Run: pytest — confirm test fails
3. Write minimum code to pass the test
4. Run: pytest — confirm test passes
5. Refactor: improve code quality without breaking tests
6. Run: pytest — confirm still passes
7. Repeat for next behavior
```

### 5.5 — git-workflow.md

```markdown
# Git Workflow Rules

## Branch Strategy
- main: production. Protected. Direct pushes blocked.
- develop: integration branch. All feature PRs merge here.
- feature/[name]: agent work on new features
- fix/[name]: bug fixes
- agent/[name]: large autonomous agent tasks (refactors, migrations)
- chore/[name]: dependency updates, config changes

## Commit Format (Conventional Commits)
feat: add Glitch Report generation endpoint
fix: prevent double-move race condition in session service
test: add SM-2 edge cases for quality=0
docs: update API spec for /drill/queue endpoint
refactor: extract move quality logic to separate method
chore: upgrade python-chess to 2.0

## PR Rules
- PR title matches commit format
- PR description includes: what changed, why, how to test
- All tests must pass before PR is created
- Never merge your own PR — review the agent's diff carefully
- Agent PRs go to: feature/[name] → develop

## Agent Branch Protocol
When assigning a large task to an agent:
1. Create branch: git checkout -b agent/[task-name]
2. Tell agent: "Work on branch agent/[task-name]"
3. Agent commits incrementally with descriptive messages
4. When done: review diff carefully, then merge to develop
5. Never let agent push directly to main

## Pre-commit Checklist (enforced in CI)
- [ ] Tests pass: pytest (backend) / vitest (frontend)
- [ ] No hardcoded secrets (checked by trufflehog)
- [ ] Type check passes: mypy (backend) / tsc --noEmit (frontend)
- [ ] Lint passes: ruff (backend) / eslint (frontend)
```

---

## 6. Estrategia Multi-Agente por Dominio

### Los 6 Agentes Especializados de NeonGambit

AgentKit 2.0 organiza sus 16 agentes en cuatro dominios. Para NeonGambit usamos los más relevantes: API Design Engineer, Database Architect, Authentication & Security Specialist, Unit Test Specialist, Integration Test Master, y los agentes de Frontend.

Mapeamos los agentes de AgentKit 2.0 a roles específicos del proyecto:

```
┌─────────────────────────────────────────────────────────────────┐
│  MANAGER — Antigravity Mission Control (eres tú)                │
│  Defines missions → monitors artifacts → approves merges        │
└──────────────────────────┬──────────────────────────────────────┘
                           │ Dispatches to
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
   │  BACKEND    │  │  FRONTEND   │  │   TEST      │
   │   AGENT     │  │   AGENT     │  │   AGENT     │
   │             │  │             │  │             │
   │ API Design  │  │ UI Spec     │  │ Unit Test   │
   │ Engineer    │  │ Engineer    │  │ Specialist  │
   │ + Database  │  │ + Browser   │  │ + Integration│
   │ Architect   │  │ Agent       │  │ Test Master │
   └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
          │                │                │
          ▼                ▼                ▼
   /backend/           /frontend/        tests/
   (services,          (components,      (conftest,
    routers,            stores,           test_*.py,
    schemas,            hooks,            *.test.ts)
    models)             pages)
```

### Cómo Orquestar Múltiples Agentes en Antigravity

En el **Agent Manager**, crea una misión y asigna sub-tareas:

```
MISIÓN PRINCIPAL (Manager View):
"Implement the Neural Drill feature end-to-end.
Reference: specs/feature-neural-drill.md
Context: .agents/rules/project-context.md

Sub-tasks (run in parallel where possible):

SUB-TASK A → Backend Agent (API Design Engineer + Database Architect)
"Implement all /drill/* endpoints per spec.
Use skills: backend-fastapi, database-neon, srs-algorithm
Files: /backend/app/services/srs_service.py,
       /backend/app/api/v1/drill.py,
       /backend/app/schemas/drill.py
Do NOT touch /frontend"

SUB-TASK B → Test Agent (Unit Test Specialist)
"Write failing tests for SRS service FIRST.
Use skill: backend-fastapi (testing section)
Files: /backend/tests/test_srs_service.py
Reference: .agents/rules/testing-standards.md
Run: cd backend && pytest tests/test_srs_service.py -v
All tests should FAIL initially (TDD).
Do NOT implement — just write tests."

SUB-TASK C → Frontend Agent (UI Specialist)
"Implement Neural Drill screen per spec.
Use skills: frontend-nextjs, stitch-design
DESIGN.md reference: look at 'Neural Drill' section
Files: /frontend/app/(main)/drill/page.tsx,
       /frontend/components/drill/DrillCard.tsx,
       /frontend/components/drill/ShadowMove.tsx,
       /frontend/lib/store/useDrillStore.ts
Do NOT touch /backend"

EXECUTION ORDER:
1. Sub-task B first (tests written → all fail)
2. Sub-task A in parallel with B (backend implementation)
3. When A completes → run tests → they should pass
4. Sub-task C last (frontend, needs backend running)
5. Browser Agent: verify drill screen vs DESIGN.md"
```

### Cuándo Usar Qué Modelo

```
Gemini 3.1 Pro (High) — Tareas de implementación complejas
  ✓ Implementar session_service.py (lógica de ajedrez compleja)
  ✓ Implementar Glitch Report pipeline
  ✓ Implementar componentes React con animaciones

Gemini 3 Flash — Tareas rápidas y bien definidas
  ✓ Crear un nuevo schema Pydantic
  ✓ Actualizar un endpoint existente
  ✓ Agregar un índice a la base de datos

Claude Opus 4.6 — Debugging y arquitectura
  ✓ Debuggear un bug difícil de reproducir
  ✓ Decidir sobre un trade-off arquitectónico
  ✓ Revisar código crítico (auth, payments)

Claude Sonnet 4.6 — Revisión de código y refactoring
  ✓ Code review de un PR de agente
  ✓ Refactoring de un servicio existente
  ✓ Optimizar una query SQL compleja
```

---

## 7. Workflows Reutilizables

Los workflows son el mayor multiplicador de productividad. Son recetas que el agente sigue cada vez que ejecutas `/comando`.

### 7.1 — /new-feature (TDD cycle completo)

**Archivo:** `.agents/workflows/new-feature.md`

```markdown
---
name: new-feature
description: Implementa una nueva feature usando TDD. Ejecuta el ciclo completo:
             spec review → tests → implementación → browser verification.
---

# Procedimiento /new-feature

## Inputs requeridos
Cuando este workflow sea invocado, preguntar:
1. ¿Cuál es el nombre de la feature? (ej: "neural-drill", "glitch-report")
2. ¿Ya existe el archivo specs/feature-[name].md? Si no, DETENER.

## Fase 1 — Spec Review (no escribir código)
1. Leer specs/feature-[name].md completamente
2. Leer las secciones relevantes del Master Guide
3. Leer DESIGN.md para contexto visual
4. Generar Implementation Plan artifact con:
   - Lista de archivos a crear/modificar
   - Dependencias entre archivos
   - Riesgos identificados
   - Preguntas de aclaración si las hay
5. ESPERAR aprobación del usuario antes de continuar

## Fase 2 — Tests Primero (TDD)
1. Crear /backend/tests/test_[feature].py con todos los tests del spec
2. Todos los tests deben FALLAR (sin implementación aún)
3. Ejecutar: cd backend && pytest tests/test_[feature].py -v
4. Confirmar que todos fallan y mostrar output al usuario
5. Crear /frontend/lib/[module].test.ts si hay lógica de frontend a testear
6. Ejecutar: cd frontend && npx vitest run [module].test.ts
7. Confirmar fallos

## Fase 3 — Implementación Backend
1. Implementar schema Pydantic en /backend/app/schemas/
2. Implementar modelo SQLAlchemy si se necesita tabla nueva
3. Crear migración Alembic: alembic revision --autogenerate -m "add [feature]"
4. Revisar migración generada — NO ejecutar aún
5. Implementar service en /backend/app/services/
6. Implementar router en /backend/app/api/v1/
7. Registrar router en /backend/app/api/v1/__init__.py
8. Ejecutar: cd backend && pytest tests/test_[feature].py -v
9. Todos los tests deben PASAR — si no, debug hasta que pasen

## Fase 4 — Migración de Base de Datos
1. Mostrar el contenido de la migración al usuario
2. ESPERAR confirmación explícita para ejecutar
3. Si confirmado: alembic upgrade head
4. Verificar tablas creadas: describir tablas en Neon

## Fase 5 — Implementación Frontend
1. Crear Zustand store si se necesita estado nuevo
2. Crear módulo en /frontend/lib/api/ para los endpoints
3. Implementar componentes React (bottom-up: atoms → molecules → screen)
4. Usar DESIGN.md como referencia visual en cada componente
5. Ejecutar: cd frontend && npm run dev
6. Browser Agent: navegar a la pantalla e tomar screenshot
7. Comparar screenshot contra DESIGN.md — anotar diferencias

## Fase 6 — Integration Testing
1. Ejecutar test suite completo: cd backend && pytest
2. Ejecutar: cd frontend && npx vitest run
3. Verificar coverage: pytest --cov=app/services/[service] --cov-report=term-missing
4. Coverage debe ser >= 80% para el servicio nuevo

## Fase 7 — Commit y PR
1. git add [archivos específicos de esta feature]
2. git commit -m "feat: implement [feature-name]"
3. git push origin feature/[feature-name]
4. Crear PR: feature/[feature-name] → develop
5. Generar Walkthrough artifact con: qué se implementó, cómo probarlo
```

### 7.2 — /new-endpoint (endpoint rápido con TDD)

**Archivo:** `.agents/workflows/new-api-endpoint.md`

```markdown
---
name: new-endpoint
description: Agrega un nuevo endpoint API con schema, implementación y tests.
             Para endpoints simples que no requieren nuevo servicio.
---

# Procedimiento /new-endpoint

## Inputs: pedir al usuario
- Método HTTP y path (ej: "GET /drill/queue/count")
- Request body schema (si aplica)
- Response schema exacto
- Autenticación requerida (yes/no/pro-only)
- Rate limiting (yes/no)

## Pasos
1. Crear test de integración PRIMERO en tests/test_[router].py
   - Test: request sin auth → 401
   - Test: request válido → schema correcto
   - Test: request inválido → error correcto
2. Ejecutar tests → deben fallar
3. Agregar schema Pydantic en /backend/app/schemas/
4. Implementar función en router existente o crear nuevo router
5. Ejecutar tests → deben pasar
6. Verificar en Swagger: http://localhost:8000/docs
7. Commit: "feat: add [METHOD] [path] endpoint"
```

### 7.3 — /migrate (Alembic seguro)

**Archivo:** `.agents/workflows/db-migration.md`

```markdown
---
name: migrate
description: Crea y aplica migraciones de base de datos de forma segura.
             SIEMPRE requiere revisión humana antes de ejecutar.
---

# Procedimiento /migrate

## Regla de Seguridad
NUNCA ejecutar alembic upgrade head sin confirmación explícita del usuario.
NUNCA modificar migraciones ya ejecutadas en producción.

## Pasos
1. Verificar estado actual: alembic current
2. Generar migración: alembic revision --autogenerate -m "[descripción]"
3. Abrir el archivo generado y mostrar su contenido completo al usuario
4. ESPERAR respuesta explícita "sí, aplicar" o "no, revisar"
5. Si aprobado: alembic upgrade head
6. Verificar: alembic current (debe mostrar nueva revisión)
7. Commit: "chore: add migration [descripción]"

## Verificaciones post-migración
- Tabla existe: SELECT tablename FROM pg_tables WHERE schemaname='public'
- Columnas correctas: \d [tablename] en psql
- Índices creados: \di en psql
```

### 7.4 — /test (ejecutar y verificar)

**Archivo:** `.agents/workflows/run-tests.md`

```markdown
---
name: test
description: Ejecuta el test suite completo y reporta coverage.
---

# Procedimiento /test

## Backend
1. cd backend
2. pytest --cov=app --cov-report=term-missing -v
3. Mostrar: tests passed, tests failed, coverage %
4. Si coverage < 80% en algún servicio: identificar líneas sin cobertura
5. Si hay tests fallando: mostrar el traceback completo

## Frontend
1. cd frontend
2. npx vitest run --coverage
3. Mostrar: tests passed, tests failed, coverage %

## Reporte
Generar artifact con:
- Total: X passed / Y failed
- Coverage por módulo
- Archivos sin tests (si los hay)
- Próximos tests recomendados
```

### 7.5 — /deploy-backend

**Archivo:** `.agents/workflows/deploy-backend.md`

```markdown
---
name: deploy-backend
description: Despliega el backend a Hostinger VPS via PM2 y verifica que esté funcionando.
---

# Procedimiento /deploy-backend

## Pre-deploy checklist (DEBE pasar todo)
1. pytest — todos los tests pasan
2. mypy app/ — sin errores de tipo
3. ruff check app/ — sin errores de lint
4. git status — sin cambios sin commitear
5. Confirmar que .env está actualizado en el VPS

## Deploy
1. SSH al VPS: ssh user@hostinger-ip
2. cd /var/www/neongambit/backend
3. git pull origin main
4. pip install -r requirements.txt --break-system-packages
5. alembic upgrade head (mostrar migración y esperar confirmación)
6. pm2 restart neongambit-api
7. Verificar logs: pm2 logs neongambit-api --lines 20

## Post-deploy verification
1. GET https://api.neongambit.com/health → debe retornar {"status": "ok", "version": "5.1.0"}
2. POST https://api.neongambit.com/v1/auth/guest → debe retornar token
3. Verificar Swagger: https://api.neongambit.com/docs → debe cargar
4. Verificar nginx: systemctl status nginx

## Rollback (si algo falla)
1. git log --oneline -5 → identificar commit anterior
2. git checkout [commit-hash]
3. pm2 restart neongambit-api
4. Verificar /health
```

### 7.6 — /deploy-frontend

**Archivo:** `.agents/workflows/deploy-frontend.md`

```markdown
---
name: deploy-frontend
description: Verifica el estado del deploy en Vercel (auto-deploy desde GitHub).
---

# Procedimiento /deploy-frontend

## Nota: Vercel hace auto-deploy desde GitHub
El deploy ocurre automáticamente cuando hay un push a main.
Este workflow verifica que el deploy fue exitoso.

## Verificación post-deploy
1. Abrir Browser Agent en: https://neongambit.com
2. Verificar: página carga sin errores de consola
3. Verificar: POST /auth/guest funciona (guest session se crea)
4. Verificar: PWA manifest accesible en /manifest.json
5. Lighthouse audit: PWA score debe ser > 90
6. Screenshot: tomar y comparar con DESIGN.md

## Si el deploy falló
1. Verificar build logs en Vercel dashboard
2. Buscar errores TypeScript o de módulos
3. Correr localmente: npm run build — debe pasar
```

### 7.7 — /code-review

**Archivo:** `.agents/workflows/code-review.md`

```markdown
---
name: code-review
description: Analiza el diff del branch actual contra develop.
             Usa Claude Opus 4.6 para máxima calidad de review.
---

# Procedimiento /code-review

## Usar modelo: Claude Opus 4.6

## Análisis del diff
1. git diff develop...[current-branch] — mostrar todos los cambios
2. Analizar cada archivo modificado:

### Checklist de seguridad
- [ ] No hay secretos hardcodeados
- [ ] Autenticación correcta en todos los endpoints nuevos
- [ ] SQL injection imposible (SQLAlchemy siempre, no strings raw)
- [ ] Input validation en todos los schemas

### Checklist de arquitectura
- [ ] Lógica de negocio está en services, no en routers
- [ ] Frontend no hace validación chess como fuente de verdad
- [ ] Stores Zustand son flat (sin nesting profundo)
- [ ] No hay imports circulares

### Checklist de tests
- [ ] Tests cubren happy path Y error cases
- [ ] No hay tests que dependan de orden de ejecución
- [ ] Fixtures no usan datos de producción

### Checklist de performance
- [ ] Queries tienen índices en columnas usadas en WHERE
- [ ] No hay N+1 queries (eager loading donde corresponde)
- [ ] Cache usada para Lichess Explorer calls
- [ ] Stockfish NEVER called server-side during sparring (client WASM only)
- [ ] Gemini/LLM NEVER called during sparring gameplay (templates only)
- [ ] All user-facing strings use next-intl translation keys

## Output
Generar artifact de review con:
- Issues críticos (deben corregirse antes del merge)
- Issues menores (mejoras recomendadas)
- Puntos positivos del código
```

---

## 8. Integración con GitHub

### GitHub MCP en Antigravity

El soporte de MCP llegó en 2026, permitiendo a los agentes conectarse a GitHub, bases de datos y APIs a través del patrón estándar de configuración MCP.

**Configurar GitHub MCP:**

```json
// En Antigravity → Agent Manager → MCP Servers → "..." → Agregar servidor
{
  "servers": {
    "github": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_tu_token_aqui"
      }
    }
  }
}
```

**Qué puede hacer el agente con GitHub MCP:**
- Crear PRs automáticamente al terminar una feature
- Leer issues existentes para contexto
- Comentar en PRs con resultados de tests
- Crear releases tags

### CI/CD en GitHub Actions

**Archivo:** `.github/workflows/ci-backend.yml`

```yaml
name: Backend CI

on:
  push:
    branches: [develop, main]
    paths: ['backend/**']
  pull_request:
    branches: [develop, main]
    paths: ['backend/**']

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: neongambit_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Install Stockfish
        run: sudo apt-get install -y stockfish

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run type check
        run: cd backend && mypy app/

      - name: Run lint
        run: cd backend && ruff check app/

      - name: Run tests with coverage
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:test@localhost/neongambit_test
          REDIS_URL: redis://localhost:6379
          JWT_SECRET_KEY: test-secret-key-not-for-production
          ENVIRONMENT: test
        run: |
          cd backend
          pytest --cov=app --cov-report=xml --cov-fail-under=80 -v

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: backend/coverage.xml
          flags: backend
```

**Archivo:** `.github/workflows/ci-frontend.yml`

```yaml
name: Frontend CI

on:
  push:
    branches: [develop, main]
    paths: ['frontend/**']
  pull_request:
    branches: [develop, main]
    paths: ['frontend/**']

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: cd frontend && npm ci

      - name: Type check
        run: cd frontend && npx tsc --noEmit

      - name: Lint
        run: cd frontend && npm run lint

      - name: Run tests
        run: cd frontend && npx vitest run --coverage

      - name: Build
        run: cd frontend && npm run build
        env:
          NEXT_PUBLIC_API_URL: https://api.neongambit.com/v1
```

---

## 9. Pipeline de Testing

### La Pirámide de Tests de NeonGambit

```
        ┌───────────────┐
        │    E2E (5%)   │  Browser Agent — journeys críticos
        ├───────────────┤
        │Integration(25%)│  Endpoints completos — routers + DB
        ├───────────────┤
        │  Unit  (70%)  │  Services + Stores + Hooks — aislados
        └───────────────┘
```

### Tests que los Agentes Deben Escribir ANTES de Implementar

**Orden de escritura de tests (TDD estricto):**

Para cada misión/feature, el Test Agent escribe tests en este orden:

```
PASO 1 — Tests de Servicio (unidad)
Archivo: /backend/tests/test_[service].py

Ejemplo para srs_service.py:
  test_sm2_quality_5_first_review → interval=1, repetitions=1
  test_sm2_quality_5_second_review → interval=6, repetitions=2  
  test_sm2_quality_5_third_review → interval=escalates_by_easiness
  test_sm2_quality_below_3_resets → repetitions=0, interval=1
  test_sm2_easiness_never_below_1_3 → min easiness enforced
  test_get_due_cards_respects_cap_free_tier → max 5 for non-pro
  test_get_due_cards_unlimited_pro → no cap for pro
  test_record_review_updates_next_review → next_review in future
  test_populate_cards_creates_correct_moves → only user-color moves

PASO 2 — Tests de Router (integración)
Archivo: /backend/tests/test_drill_router.py

  test_get_drill_queue_requires_auth → 401 without token
  test_get_drill_queue_returns_due_cards → correct schema
  test_get_drill_queue_cap_free_tier → max 5 returned
  test_get_drill_count_returns_integer → count field present
  test_record_review_updates_card → next_review changes
  test_record_review_invalid_quality → 400 for quality=6
  test_get_mastery_returns_progress → mastery_percent calculated

PASO 3 — Tests de Frontend (store)
Archivo: /frontend/lib/store/useDrillStore.test.ts

  test_load_populates_queue → queue not empty after load
  test_mark_correct_records_quality_5 → API called with quality=5
  test_mark_correct_with_shadow_records_quality_3 → lower quality
  test_mark_incorrect_records_quality_1 → resets interval
  test_advance_moves_to_next_card → currentIndex increments
  test_complete_when_queue_exhausted → isComplete=true
```

### Datos de Test Estándar

**Fixtures para backend** (`/backend/tests/conftest.py`):

```python
TEST_OPENING = {
    "name": "Sicilian Defense: Dragon Variation",
    "eco_code": "B70",
    "starting_fen": chess.STARTING_FEN,
    "starting_moves": ["e4", "c5", "Nf3", "d6", "d4", "cxd4", "Nxd4"],
    "tier": "free",
    "play_style": "tactical",
    "color": "black",
}

TEST_LICHESS_GAMES = [
    # 20 games with known ECO codes and results for Glitch Report testing
    {"eco": "B70", "result": "loss", "opening_name": "Sicilian: Dragon"},
    # ... etc
]

TEST_LICHESS_USERNAME = "NeonGambitTestUser"  # Real Lichess account, public games
```

---

## 10. Pipeline de Deployment

### Arquitectura de Ambientes

```
Local Dev (docker-compose)
    ↓ git push feature/* → develop
CI (GitHub Actions)
    ↓ Tests pasan + Review aprobado → main
Production (Hostinger VPS + Vercel)
```

### docker-compose.yml (Desarrollo Local)

```yaml
# docker-compose.yml — Para desarrollo local
version: '3.9'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:dev@db/neongambit
      - REDIS_URL=redis://redis:6379
      - ENVIRONMENT=development
    env_file:
      - ./backend/.env
    volumes:
      - ./backend:/app
    depends_on:
      - db
      - redis
    command: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: neongambit
      POSTGRES_PASSWORD: dev
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

### Variables de Entorno por Ambiente

```bash
# /backend/.env.example — Copiar a .env para desarrollo
DATABASE_URL=postgresql+asyncpg://postgres:dev@localhost/neongambit
REDIS_URL=redis://localhost:6379
FIREBASE_PROJECT_ID=neongambit-dev
FIREBASE_CREDENTIALS_PATH=./firebase-admin-key-dev.json
GOOGLE_GEMINI_API_KEY=your_dev_key
LICHESS_API_TOKEN=lip_dev_token
STOCKFISH_PATH=/usr/local/bin/stockfish
JWT_SECRET_KEY=dev-only-not-for-production-change-this
STRIPE_SECRET_KEY=sk_test_your_test_key
STRIPE_WEBHOOK_SECRET=whsec_test_key
ENVIRONMENT=development

# Producción: estas van en /var/www/neongambit/backend/.env en el Hostinger VPS
# NUNCA commitear el .env real al repo
```

---

## 11. Cómo Cargar Todo a Antigravity

Este es el proceso exacto, paso a paso, para inicializar el workspace de Antigravity con todo el contexto antes de empezar a desarrollar.

### Paso 1 — Inicializar el Repositorio

```bash
# En tu terminal local
mkdir neongambit
cd neongambit
git init
git remote add origin https://github.com/tu-usuario/neongambit.git

# Crear estructura base
mkdir -p .agents/rules .agents/skills .agents/workflows
mkdir -p specs backend frontend .github/workflows
```

### Paso 2 — Crear los Artefactos de Configuración

Copia el contenido de la Sección 5 de este documento en los archivos correspondientes:

```bash
# Crear archivos de configuración
touch AGENTS.md          # Contenido: Sección 5.1
touch GEMINI.md          # Contenido: Sección 5.2
touch CLAUDE.md          # Symlink a AGENTS.md para Claude Code

# Crear rules
touch .agents/rules/project-context.md    # Sección 5.3
touch .agents/rules/testing-standards.md  # Sección 5.4
touch .agents/rules/git-workflow.md       # Sección 5.5
touch .agents/rules/safety-guardrails.md  # Ver template abajo

# Crear workflows
touch .agents/workflows/new-feature.md      # Sección 7.1
touch .agents/workflows/new-api-endpoint.md # Sección 7.2
touch .agents/workflows/db-migration.md     # Sección 7.3
touch .agents/workflows/run-tests.md        # Sección 7.4
touch .agents/workflows/deploy-backend.md   # Sección 7.5
touch .agents/workflows/deploy-frontend.md  # Sección 7.6
touch .agents/workflows/code-review.md      # Sección 7.7
```

### Paso 3 — Crear las Skills

Cada skill debe tener YAML frontmatter para que Antigravity las descubra automáticamente:

```bash
# Crear directorios de skills
mkdir -p .agents/skills/backend-fastapi
mkdir -p .agents/skills/frontend-nextjs
mkdir -p .agents/skills/database-neon
mkdir -p .agents/skills/chess-engine
mkdir -p .agents/skills/stockfish-wasm
mkdir -p .agents/skills/srs-algorithm
mkdir -p .agents/skills/coach-templates
mkdir -p .agents/skills/lichess-api
mkdir -p .agents/skills/stripe-integration
mkdir -p .agents/skills/redis-caching
mkdir -p .agents/skills/stitch-design
```

Cada `SKILL.md` debe comenzar con:

```yaml
---
name: backend-fastapi
description: Patrones para FastAPI con SQLAlchemy async, Pydantic V2, y arquitectura
             de servicios en NeonGambit. Cargar cuando se implementen routers,
             services, schemas, o modelos de base de datos.
---
```

Seguido del contenido del Backend Implementation Guide relevante para ese skill.

### Paso 4 — Crear las Feature Specs

```bash
# Crear MVP spec files (7 features — no repertoire, no achievements in MVP)
for feature in auth lichess-import glitch-report sparring-session neural-drill analytics-dashboard subscriptions; do
  touch specs/feature-$feature.md
done
```

Cada spec sigue el formato de la Sección 4 de este documento.

### Paso 5 — Commit Inicial del Contexto

```bash
# Commitear SOLO los archivos de configuración de agentes
git add AGENTS.md GEMINI.md CLAUDE.md DESIGN.md
git add .agents/
git add specs/
git add data/neon_templates.yaml
git add .github/
git add docker-compose.yml

git commit -m "chore: initialize agent context, project specs, and NEON templates"
git push origin main
```

### Paso 6 — Abrir Antigravity y Cargar el Workspace

```
1. Abrir Google Antigravity
2. File → Open Folder → seleccionar /neongambit
3. Antigravity leerá automáticamente AGENTS.md y GEMINI.md
4. Agent Manager → verificar que las Rules estén activas
5. En el chat del agente, escribir:
   "Read .agents/rules/project-context.md and confirm you understand
    the NeonGambit project architecture and constraints."
6. El agente debe responder resumiendo correctamente el proyecto
```

### Paso 7 — Configurar MCPs

En **Agent Manager → MCP Servers → "..."**:

```
Instalar:
✓ Stitch MCP (para design-to-code pipeline)
✓ GitHub MCP (para PR automation)
✓ Supabase MCP (opcional — si usas Supabase en vez de Neon directo)

Verificar:
"List my Stitch projects" — debe retornar NeonGambit
"List recent GitHub issues" — debe retornar issues del repo
```

### Paso 8 — Cargar los Documentos como Knowledge Items

En **Antigravity → Knowledge Base** (icono de libro en sidebar):

```
Agregar como Knowledge Items:
1. neongambit-master-guide-v5.md → "Master Guide v5.1"
2. BACKEND_IMPLEMENTATION_GUIDE_v5.md → "Backend Guide v5.1"
3. FRONTEND_IMPLEMENTATION_GUIDE_v5.md → "Frontend Guide v5.1"
4. DESIGN.md → "Design System" (una vez generado por Stitch)
```

Esto permite al agente buscar en estos documentos en cualquier momento sin que estén en el contexto de la conversación activa.

### Paso 9 — Verificación Final

Antes de escribir código, hacer esta verificación completa:

```
En el chat de Antigravity, pedir:

"Run a project readiness check. Verify:
1. AGENTS.md is loaded and rules are active
2. All 11 skills in .agents/skills/ have valid YAML frontmatter
3. All 7 workflows in .agents/workflows/ are discoverable
4. All 7 MVP spec files in specs/ are present (list them)
5. DESIGN.md exists and contains color tokens
6. data/neon_templates.yaml exists and has at least 50 template entries
7. Stitch MCP is connected
8. GitHub MCP is connected
9. Knowledge Base has the 4 guides loaded (Master v5.1, Backend v5.1, Frontend v5.1, Design)

Produce a readiness artifact listing: ✓ ready / ✗ missing
for each item. Do NOT proceed to implementation until all are ✓."
```

---

## 12. Secuencia de Ejecución Completa

Esta es la secuencia cronológica exacta del proyecto. **No saltar fases.**

```
┌────────────────────────────────────────────────────────────────────┐
│ SEMANA -2 a -1: ESPECIFICACIÓN (Tú + Claude, sin Antigravity)     │
├────────────────────────────────────────────────────────────────────┤
│ □ Leer Master Guide v5.1 completo                                   │
│ □ Completar los 7 archivos specs/ MVP (usar formato Sección 4)    │
│ □ Completar AGENTS.md y GEMINI.md (Sección 5)                    │
│ □ Completar las 11 Skills (extraer del Backend/Frontend Guide)    │
│ □ Completar los 7 Workflows (Sección 7)                           │
│ □ Completar project-context.md, testing-standards.md             │
│ □ Completar git-workflow.md, safety-guardrails.md                 │
│ □ Crear data/neon_templates.yaml (~200 templates EN+ES, revisados) │
└────────────────────────────────────────────────────────────────────┘
          ↓
┌────────────────────────────────────────────────────────────────────┐
│ SEMANA -1: DISEÑO (Stitch → DESIGN.md)                           │
├────────────────────────────────────────────────────────────────────┤
│ □ Generar 5 pantallas en Stitch (prompts Sección 3)              │
│ □ Configurar Stitch MCP en Antigravity                            │
│ □ Generar DESIGN.md via Stitch MCP                               │
│ □ Verificar DESIGN.md vs designTokens.ts                         │
└────────────────────────────────────────────────────────────────────┘
          ↓
┌────────────────────────────────────────────────────────────────────┐
│ SEMANA 0: INICIALIZACIÓN (Pasos 1-9 de Sección 11)               │
├────────────────────────────────────────────────────────────────────┤
│ □ Crear estructura de repositorio                                 │
│ □ Commitear todos los artefactos de configuración                │
│ □ Validar neon_templates.yaml: python3 -c "import yaml; ..."     │
│ □ Abrir workspace en Antigravity                                  │
│ □ Configurar MCPs (Stitch + GitHub)                              │
│ □ Cargar Knowledge Items                                          │
│ □ Verificación de readiness (Paso 9)                             │
└────────────────────────────────────────────────────────────────────┘
          ↓
┌────────────────────────────────────────────────────────────────────┐
│ SEMANAS 1-3: IMPLEMENTACIÓN (Antigravity Agents)                  │
├────────────────────────────────────────────────────────────────────┤
│ MISIÓN 1 (Backend Agent): Fundación + Schema                      │
│   Tests → /test (todos fallan) → Implementar → /test (pasan)     │
│   Features: MVP DB models (users con preferred_language,          │
│   openings, sparring_sessions, etc.) + Auth + /health             │
│   Create ecosystem.config.js + nginx.conf template                │
│                                                                    │
│ MISIÓN 2 (Backend Agent + Test Agent en paralelo):               │
│   Lichess Import + Background Workers                             │
│   Test Agent: test_lichess_import_worker.py (fallan)             │
│   Backend Agent: implementa worker (sin conversion failures)     │
│   Implementar degraded mode para Lichess API                      │
│   /test → pasan → /migrate → commit                              │
│                                                                    │
│ MISIÓN 3 (Backend Agent + Test Agent):                           │
│   Glitch Report Engine + Collapse Type Classification             │
│   Test Agent: test_lichess_analyzer.py (fallan)                  │
│   Backend Agent: lichess_analyzer.py (con _classify_collapse)    │
│     + coach_service.py (Gemini para narrativas, con locale)      │
│   Auto-assign top critical openings al repertorio                │
│   /test → pasan → commit                                         │
│                                                                    │
│ MISIÓN 4 (Backend + Test + Browser Agent en paralelo):           │
│   Sparring Sessions + NEON Template Library                       │
│   [Backend]: session_service (NO Stockfish server-side),         │
│     chess_service, coach_templates.py + neon_templates.yaml      │
│   [Test]: test_sessions, test_session_service,                   │
│     test_coach_templates (EN + ES)                                │
│   Server accepts prev_move_quality from client                    │
│   Tilt tracking in user_stats                                     │
│   [Browser]: verificar endpoint en Swagger                        │
│                                                                    │
│ MISIÓN 5 (Frontend Agent + Browser Agent):                       │
│   Diseño base + Shell + Auth + Stockfish WASM                     │
│   [Frontend]: next-intl setup (en.json + es.json),               │
│     design system, 3-tab BottomNav (Arena/Drill/Profile),        │
│     stockfish.wasm Web Worker + useStockfish hook                │
│   [Browser]: screenshot vs DESIGN.md. Verify locale switch.     │
│                                                                    │
│ MISIÓN 6 (Frontend + Browser Agent):                             │
│   Lichess Connect → Glitch Report Reveal                          │
│   [Frontend]: LichessConnect → LoadingTerminal → Reveal          │
│     CriticalOpeningCard con collapse_type badge                  │
│     ALL openings visible, training_unlocked lock on CTA          │
│   [Browser]: verifica secuencia de animación + Spanish locale    │
│                                                                    │
│ MISIÓN 7 (Frontend + Browser Agent):                             │
│   The Arena + Tilt Detection + Session Debrief                    │
│   [Frontend]: Arena screen + game loop con client-side eval      │
│     (useStockfish + classifyMoveQuality + prev_move_quality)     │
│     TiltIntervention component after 3rd loss                    │
│     Summary-only debrief (no move-by-move)                       │
│   [Browser]: full game flow E2E. Verify tilt intervention.       │
│                                                                    │
│ MISIÓN 8 (Backend + Test Agent):                                 │
│   Neural Drill + SRS                                              │
│   [Test]: test_srs_service (fallan) → [Backend] implementa       │
│   /test → pasan → /migrate → commit                              │
│                                                                    │
│ MISIÓN 9 (Frontend + Browser Agent):                             │
│   Neural Drill Screen + Queue                                     │
│   [Frontend]: DrillCard + ShadowMove + resultado                 │
│   All strings via next-intl keys                                 │
│   [Browser]: drill flow completo. Verify Spanish locale.         │
│                                                                    │
│ MISIÓN 10 (Backend + Frontend + Test Agent):                     │
│   Analytics Dashboard (MVP)                                       │
│   [Backend]: analytics_service (single endpoint, no missions,    │
│     no conversion failures — drill queue IS the daily mission)   │
│   [Frontend]: Mission Control screen + RatingChart (Recharts)    │
│   [Browser]: dashboard renderiza con datos reales                │
│                                                                    │
│ MISIÓN 11 (Backend + Frontend):                                  │
│   Stripe + Profile + Upgrade                                      │
│   [Backend]: subscription_service + webhooks                     │
│   [Frontend]: UpgradeModal + paywall gates + Profile screen      │
│     (language selector, Lichess re-sync, RatingChart)            │
│                                                                    │
│ MISIÓN 12 (All Agents):                                          │
│   Deploy + Polish                                                 │
│   /code-review → fix issues                                      │
│   /deploy-backend (Hostinger: PM2 + nginx + SSL)                 │
│   /deploy-frontend (Vercel auto-deploy)                          │
│   [Browser]: full E2E journey en production                      │
│   Verify: PWA install on iOS + Android. Lighthouse > 90.         │
└────────────────────────────────────────────────────────────────────┘
          ↓
┌────────────────────────────────────────────────────────────────────┐
│ ONGOING: CICLO DE MEJORA                                          │
├────────────────────────────────────────────────────────────────────┤
│ Cada nueva feature:                                               │
│   1. Crear specs/feature-[name].md                               │
│   2. /new-feature → Test Agent escribe tests → fallan            │
│   3. Backend/Frontend Agent implementa                            │
│   4. /test → pasan                                               │
│   5. /code-review → fix                                          │
│   6. PR → develop → /deploy                                      │
└────────────────────────────────────────────────────────────────────┘
```

---
## 13. Orchestrator Interface (para Claude Managed Agent)

El orquestador de Claude se comunica vía GitHub. Lee `.orchestrator/next-directive.md`
para generar el prompt que Jorge pega en el Manager View.

Schema de directive: [el mismo schema del prompt del orquestador]

Formato de reporte de resultado: al terminar una misión, el agente debe escribir
`.orchestrator/results/DIR-XXX-result.md` con:
- status: success | partial | failed
- artifacts_produced: [lista de archivos]
- tests_passing: true | false
- adrs_respected: true | false | [lista de violaciones]
- notes: [observaciones]

---

## Apéndice A — Template safety-guardrails.md

```markdown
# Safety Guardrails

## NUNCA hacer esto sin confirmación explícita del usuario

### Base de Datos
- NUNCA ejecutar alembic upgrade head sin mostrar el contenido de la migración primero
- NUNCA hacer DROP TABLE o DELETE en producción
- NUNCA modificar migraciones ya ejecutadas
- NUNCA acceder a DATABASE_URL de producción desde el entorno local

### Secrets y Credenciales
- NUNCA hardcodear API keys, tokens, o passwords en código
- NUNCA commitear archivos .env
- NUNCA loggear JWT tokens o Firebase credentials
- NUNCA exponer STRIPE_SECRET_KEY en logs o responses

### Git y Deployment
- NUNCA hacer push directamente a main
- NUNCA hacer force push en branches públicos
- NUNCA hacer deploy sin que los tests estén pasando

### Infraestructura
- NUNCA modificar configuración de PM2 o nginx en el VPS sin documentarlo
- NUNCA cambiar configuración de CORS para permitir * en producción
- NUNCA deshabilitar rate limiting
- NUNCA ejecutar Stockfish server-side durante sesiones de sparring (solo para Glitch Report)
- NUNCA llamar Gemini/LLM durante gameplay en tiempo real (solo templates)

## En caso de duda
Parar, mostrar el plan al usuario, y esperar confirmación explícita.
Mejor preguntar y perder 5 minutos que romper producción.
```

---

## Apéndice B — Cómo Depurar cuando un Agente se Atasca

Cuando un agente produce código incorrecto o loops:

```
1. DETENER al agente (Escape en la conversación)

2. Verificar contexto disponible:
   "What files have you read in this session?"
   El agente debe haber leído: AGENTS.md, GEMINI.md, el skill relevante, el spec

3. Si falta contexto, resetear y ser explícito:
   "Read .agents/skills/[relevant-skill]/SKILL.md first.
    Then read specs/feature-[name].md.
    Then try again, starting with the test file."

4. Si el error es de arquitectura (agente propone algo que viola ADRs):
   "This violates ADR-[X]. Read .agents/rules/project-context.md,
    section 'Architecture Decisions'. Propose an alternative."

5. Si el agente genera código que no pasa tests:
   "Run: pytest tests/test_[file].py -v --tb=long
    Read the full traceback. Identify the root cause.
    Fix only the failing test. Don't change other tests."

6. Para bugs difíciles, cambiar a Claude Opus 4.6:
   Model selector → Claude Opus 4.6
   "Debug this failing test. Reason step by step about
    what the code is doing vs what the test expects."
```

---

*Este workflow es un documento vivo. Actualizar cuando se descubran mejores patrones durante el desarrollo.*
*Versión 2.0: Abril 2026 — Aligned with Master Guide v5.1*
