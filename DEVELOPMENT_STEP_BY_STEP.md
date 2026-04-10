# NeonGambit — Guía de Desarrollo: De Cero a Producción

**Para:** Solo-developer usando AI agents (Antigravity + Claude)
**Tiempo estimado:** 4-5 semanas
**Pre-requisitos:** Node.js 20+, Python 3.11+, Git, cuenta GitHub, cuenta Vercel, VPS Hostinger con SSH

---
## Estado Actual (para el orquestador)
current_phase: FASE 1
current_mission: Paso 6
last_updated: 2026-04-10

## Los 5 Documentos que Controlan Todo

Antes de hacer cualquier cosa, entiende qué es cada archivo:

| Documento | Qué decide | Cuándo consultarlo |
|-----------|-----------|-------------------|
| `neongambit-master-guide-v5.md` | Qué construir y por qué | Antes de cada feature |
| `BACKEND_IMPLEMENTATION_GUIDE_v5.md` | Cómo construir el API | Cuando trabajes en backend |
| `FRONTEND_IMPLEMENTATION_GUIDE_v5.md` | Cómo construir la UI | Cuando trabajes en frontend |
| `ANTIGRAVITY_WORKFLOW_v5.md` | Cómo usar los agentes | Cuando configures Antigravity |
| `neon_templates.yaml` | Qué dice NEON durante el juego | Cuando implementes coaching |

**Regla de oro:** Si un agente propone algo que contradice estos documentos, el documento gana.

---

## FASE 0 — Preparación (Días 1-3)

### Paso 1: Crear el repositorio

```bash
mkdir neongambit && cd neongambit && git init
git remote add origin https://github.com/TU-USUARIO/neongambit.git

# Estructura base
mkdir -p backend/app/{core,db/models,schemas,api/v1,services,workers,utils}
mkdir -p backend/{alembic,tests,scripts}
mkdir -p frontend
mkdir -p data
mkdir -p .agents/{rules,skills,workflows}
mkdir -p .github/workflows
mkdir -p specs
```

### Paso 2: Colocar los artefactos de configuración

Copia estos archivos desde el Antigravity Workflow v5 (Sección 5):

```bash
# Desde las plantillas en ANTIGRAVITY_WORKFLOW_v5.md:
# → AGENTS.md                    (Sección 5.1)
# → GEMINI.md                    (Sección 5.2)
# → .agents/rules/project-context.md    (Sección 5.3)
# → .agents/rules/testing-standards.md  (Sección 5.4)
# → .agents/rules/git-workflow.md       (Sección 5.5)
# → .agents/rules/safety-guardrails.md  (Apéndice A)

# Workflows (Sección 7):
# → .agents/workflows/new-feature.md
# → .agents/workflows/new-api-endpoint.md
# → .agents/workflows/db-migration.md
# → .agents/workflows/run-tests.md
# → .agents/workflows/deploy-backend.md
# → .agents/workflows/deploy-frontend.md
# → .agents/workflows/code-review.md

# Template library:
cp neon_templates.yaml data/

# Symlink para Claude Code:
ln -s AGENTS.md CLAUDE.md
```

### Paso 3: Crear los Feature Specs (MVP)

Crea 7 archivos en `specs/` siguiendo el formato de la Sección 4 del Workflow. Para cada uno, extrae la información del Master Guide v5.1:

```bash
specs/feature-auth.md               # ← Master Guide Feature 6
specs/feature-lichess-import.md      # ← Master Guide Feature 1 (import part)
specs/feature-glitch-report.md       # ← Master Guide Feature 1 (report part)
specs/feature-sparring-session.md    # ← Master Guide Feature 2
specs/feature-neural-drill.md        # ← Master Guide Feature 3
specs/feature-analytics-dashboard.md # ← Master Guide Feature 7
specs/feature-subscriptions.md       # ← Master Guide Section 4 (monetization)
```

Cada spec debe tener: contexto de usuario, comportamiento esperado, criterios de aceptación (GIVEN/WHEN/THEN), contratos de API (copiar del Backend Guide), y tests requeridos.

### Paso 4: Crear las Skills de Antigravity

Crea 11 directorios en `.agents/skills/`, cada uno con un `SKILL.md` que contenga el conocimiento relevante extraído de los Implementation Guides:

```
backend-fastapi/    → Patrones de Backend Guide Secciones 3-7
frontend-nextjs/    → Patrones de Frontend Guide Secciones 2-5
database-neon/      → Backend Guide Sección 4 (modelos) + 6.3 (migrations)
chess-engine/       → Backend Guide Sección 6.2-6.3
stockfish-wasm/     → Frontend Guide Sección 7 (Web Worker + hook)
srs-algorithm/      → Backend Guide Sección 6.8
coach-templates/    → neon_templates.yaml estructura + coach_service.py
lichess-api/        → Backend Guide Sección 6.4
stripe-integration/ → Backend Guide Sección 6.10
redis-caching/      → Backend Guide Sección 9
stitch-design/      → Frontend Guide Sección 3 (design system)
```

### Paso 5: Commit inicial

```bash
git add AGENTS.md GEMINI.md CLAUDE.md .agents/ specs/ data/ .github/
git commit -m "chore: initialize agent context, specs, and NEON templates"
git push origin main
```

---

## FASE 1 — Diseño Visual (Día 4)

### Paso 6: Generar pantallas en Google Stitch

Abre Stitch y genera 5 pantallas usando los prompts exactos del Workflow v5 Sección 3:
1. Mission Control (Home)
2. The Arena (Sparring)
3. Glitch Report Reveal
4. Neural Drill
5. Profile/Settings

### Paso 7: Exportar DESIGN.md

En Antigravity, conecta Stitch MCP y exporta los tokens de diseño. Verifica que coincidan con `designTokens.ts` del Frontend Guide. Si hay conflictos, `designTokens.ts` gana.

---

## FASE 2 — Inicializar Antigravity (Día 5)

### Paso 8: Configurar el workspace

1. Abrir Antigravity → File → Open Folder → `/neongambit`
2. Agent Manager → verificar que AGENTS.md y GEMINI.md están activos
3. Configurar MCPs: Stitch + GitHub
4. Knowledge Base → cargar los 4 guides como Knowledge Items:
   - `neongambit-master-guide-v5.md`
   - `BACKEND_IMPLEMENTATION_GUIDE_v5.md`
   - `FRONTEND_IMPLEMENTATION_GUIDE_v5.md`
   - `DESIGN.md`

### Paso 9: Verificar readiness

Pedir al agente:

```
"Run a project readiness check. Verify all skills, workflows, specs, 
DESIGN.md, neon_templates.yaml, and Knowledge Base items are loaded. 
Produce a ✓/✗ readiness artifact."
```

**No avances hasta que todo sea ✓.**

---

## FASE 3 — Backend (Días 6-14)

Cada misión sigue el ciclo TDD: **tests primero → fallan → implementar → pasan → commit.**

### Misión 1: Fundación (4h)

**Qué:** Proyecto FastAPI, modelos de DB, auth, /health.

Dile al Backend Agent:
```
"Read specs/feature-auth.md and BACKEND_IMPLEMENTATION_GUIDE_v5.md Sections 2-4.
Create the FastAPI project structure, all SQLAlchemy models (MVP only — no 
conversion_failures, no endgame_drill_cards, no achievements), Alembic setup,
and GET /health endpoint. Create ecosystem.config.js for PM2."
```

**Verifica:** `alembic upgrade head` funciona. `GET /health` retorna `{"status": "ok"}`.

### Misión 2: Auth + Lichess Import (4h)

**Qué:** Guest login, Firebase validation, Lichess game import con background worker.

Dile al Test Agent primero:
```
"Write failing tests for auth_service and lichess_import_worker per 
specs/feature-auth.md and specs/feature-lichess-import.md."
```

Luego al Backend Agent:
```
"Implement AuthService, LichessService, and lichess_import_worker.
Include Lichess API degraded mode. NO conversion failure analysis in the worker."
```

**Verifica:** `POST /auth/guest` retorna JWT. Import de un username real de Lichess funciona.

### Misión 3: Glitch Report Engine (5h)

**Qué:** Análisis de partidas, clasificación de collapse_type, diagnóstico con Gemini.

```
"Implement StockfishService (server-side, Glitch Report ONLY), 
LichessAnalyzer with _classify_collapse (opening_error, tactical_blunder, 
positional_drift, time_pressure), and CoachService (Gemini for narratives).
Auto-assign top 2 critical openings to repertoire. Include locale parameter."
```

**Verifica:** Reporte generado para un username real con collapse_type por apertura.

### Misión 4: Sparring Sessions + NEON Templates (5h)

**Qué:** Session service SIN Stockfish server-side, template coaching, tilt tracking.

```
"Read specs/feature-sparring-session.md.
Implement SessionService — server validates legality and tracks theory only.
NO Stockfish calls during sparring (ADR-002). Accept prev_move_quality from client.
Implement coach_templates.py loading data/neon_templates.yaml.
Implement tilt tracking (consecutive losses counter in user_stats)."
```

**Verifica:** Sesión completa E2E. Theory exit detectado. Coach message viene de template (instant, no LLM).

### Misión 5: Neural Drill + SRS (3h)

**Qué:** SM-2 algorithm, drill queue, mastery tracking.

```
"Implement SRSService (SM-2), all /drill/* endpoints, and 
populate_cards_for_opening. Free tier cap: 5 cards/day."
```

**Verifica:** SM-2 avanza intervalos correctamente. Queue respeta cap de free tier.

### Misión 6: Analytics + Subscriptions (3h)

**Qué:** Dashboard endpoint, Stripe checkout, webhooks.

```
"Implement AnalyticsService (single /analytics/dashboard endpoint, MVP version — 
no conversion failures, drill queue IS the daily mission).
Implement SubscriptionService with Stripe checkout and webhook handling."
```

**Verifica:** Dashboard retorna todos los campos. Stripe webhook actualiza `is_pro`.

### Misión 7: Deploy Backend (2h)

```bash
# En tu VPS Hostinger:
ssh user@tu-vps-ip
git clone https://github.com/TU-USUARIO/neongambit.git /var/www/neongambit
cd /var/www/neongambit/backend
pip install -r requirements.txt
apt install stockfish
cp .env.example .env  # → editar con credenciales de producción
alembic upgrade head
python scripts/seed_openings.py
pm2 start ecosystem.config.js
# Configurar nginx (ver Backend Guide Sección 12)
certbot --nginx -d api.neongambit.com
```

**Verifica:** `curl https://api.neongambit.com/health` → `{"status": "ok"}`.

---

## FASE 4 — Frontend (Días 15-23)

### Misión 8: Foundation + Stockfish WASM (3h)

Dile al Frontend Agent:
```
"Initialize Next.js 14 with TypeScript strict, Tailwind, shadcn/ui, next-pwa, 
next-intl (en.json + es.json), and Framer Motion.
Set up lib/stockfish/worker.ts and useStockfish.ts per Frontend Guide Section 7.
Create designTokens.ts, globals.css with all cyberpunk effects.
Create 3-tab BottomNav (Arena, Drill, Profile)."
```

**Verifica:** `npm run build` pasa. Stockfish WASM evalúa una posición test. Locale switching funciona.

### Misión 9: Lichess Connect + Glitch Report Reveal (4h)

```
"Implement LichessConnectPrompt (username input → LoadingTerminal → polling).
Implement GlitchReportReveal with cinematic timed sequence.
CriticalOpeningCard shows collapse_type badge and training_unlocked lock.
ALL openings visible in Free tier — lock on CTA, not on card.
All strings via next-intl keys."
```

**Verifica:** Flow completo: username → procesamiento → reveal cinematográfico. Collapse type badges visibles. Switch a español funciona.

### Misión 10: The Arena + Tilt (5h)

```
"Implement /arena/page.tsx with full game loop per Frontend Guide Section 6.5.
Client-side eval via useStockfish hook. classifyMoveQuality from client eval.
makeMove sends prev_move_quality to server. Server returns theory + template coaching.
Implement TiltIntervention component (shown after 3rd consecutive loss).
Pre-session selector: openings from auto-assigned repertoire only."
```

**Verifica:** Partida completa E2E. Move quality display funciona (client-side). Tilt intervention aparece después de 3 derrotas.

### Misión 11: Debrief + Neural Drill (4h)

```
"Implement /debrief/[sessionId] — summary card only (accuracy, theory, quality breakdown).
Implement /drill/page.tsx — queue screen, DrillCard with ShadowMove hint after 5s,
correct/incorrect feedback, streak increment on completion."
```

**Verifica:** Drill queue muestra count correcto. Shadow hint aparece a los 5s. Streak incrementa.

### Misión 12: Dashboard + Profile + Polish (3h)

```
"Implement Mission Control dashboard (single API call), Profile with language 
selector and RatingChart, UpgradeModal for locked features.
Implement LichessConnectPrompt trigger after first session."
```

**Verifica:** Dashboard renderiza en <1s. Language switch funciona. Upgrade modal aparece en features bloqueadas.

### Misión 13: Deploy Frontend (1h)

```bash
# Conectar repo a Vercel:
# vercel.com → New Project → Import GitHub repo → neongambit/frontend
# Environment variables: NEXT_PUBLIC_API_URL=https://api.neongambit.com/v1
# Deploy automático en cada push a main
```

**Verifica:** PWA se instala en iOS Safari y Android Chrome. Lighthouse PWA > 90.

---

## FASE 5 — Validación (Días 24-30)

### Paso 10: E2E Journey Test

Ejecuta el journey completo manualmente:

```
1. Abrir https://neongambit.com → guest session creada automáticamente
2. Jugar una partida de sparring → move quality display funciona
3. Conectar Lichess → username real → import completo
4. Glitch Report genera → reveal cinematográfico → collapse types visibles
5. Tap "DRILL THIS NOW" → drill queue cargada → completar 3 cards
6. Dashboard → rating visible, opening progress, drill count, streak
7. Switch to Spanish → toda la UI cambia
8. 3 derrotas seguidas → tilt intervention aparece
9. Profile → settings, re-sync Lichess, upgrade CTA
```

### Paso 11: Adquisición de primeros usuarios

Ejecutar la estrategia del Master Guide v5.1 Sección 12:

1. **Semana 1 post-launch:** Post en r/chess y r/lichess con Glitch Report real (anonimizado)
2. **Semana 2:** Video de 60 segundos del reveal animation → Twitter/X + Reddit
3. **Ongoing:** Post semanal "Glitch Report of the Week" + responder threads de "how do I improve"
4. **Español:** Posts en r/ajedrez + YouTube ajedrez en español

**Meta:** 50 usuarios activos en 30 días. Primer pago en 45 días.

---

## Después del MVP — Cuándo Construir Phase 2

No construyas nada de Phase 2 hasta tener señales claras:

| Feature | Señal para construir |
|---------|---------------------|
| Conversion Failures + Endgame Drill | Usuarios preguntan "¿y mis finales?" |
| Full Game Review | Usuarios piden análisis jugada por jugada |
| Achievement System | Retención D7 necesita gamificación |
| Daily Mission System | Drill queue sola no genera retorno diario |
| Repertoire Builder | Usuarios quieren entrenar más allá del Glitch Report |

Para cada feature de Phase 2, sigue el ciclo: `spec → /new-feature → tests fallan → implementar → tests pasan → /code-review → deploy`.

---

## Referencia Rápida: Comandos Frecuentes

```bash
# Backend
cd backend && pytest --cov=app -v          # Correr tests
cd backend && alembic upgrade head          # Aplicar migraciones
cd backend && uvicorn app.main:app --reload # Dev server

# Frontend
cd frontend && npm run dev                  # Dev server
cd frontend && npm run build                # Build production
cd frontend && npx vitest run               # Correr tests

# Deploy
ssh user@vps "cd /var/www/neongambit/backend && git pull && pm2 restart neongambit-api"
git push origin main                        # Auto-deploy frontend en Vercel

# Antigravity workflows
/new-feature                                # TDD cycle completo
/test                                       # Ejecutar test suite
/migrate                                    # Migración segura
/deploy-backend                             # Deploy a Hostinger
/code-review                                # Review pre-merge
```

---

*Total: 13 misiones de implementación. ~4 semanas de trabajo para un solo developer asistido por AI agents.*
*El código lo escriben los agentes. Las decisiones las tomas tú. Los documentos son la ley.*
