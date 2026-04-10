# Feature Spec: Glitch Report — "The Aha Moment"

## Contexto del usuario
The Frustrated Improver has connected their Lichess account. They've played hundreds of games and know they have weaknesses but have never seen them mapped clearly. The Glitch Report is the product's core hook — the moment where NeonGambit transforms from "a chess app" into "something that knows me." It must feel revelatory, not clinical.

**Emotion target:** "...oh. That's exactly why I keep losing."

## Comportamiento esperado

1. After Lichess import completes, frontend calls `POST /v1/glitch-report/generate`.
2. A background worker runs Stockfish analysis on the 5 worst games per critical opening, classifies the collapse type, then calls Gemini for the narrative. Job tracked by `job_id`.
3. Frontend polls `GET /v1/glitch-report/status?job_id={id}` every 2 seconds.
4. On completion, `GET /v1/glitch-report/current` returns the full report.
5. The reveal is cinematic: data loads line by line in the frontend. Critical openings appear with a red warning flash.

**Free tier visibility rule:** ALL critical openings are visible with full stats and NEON diagnosis. The lock icon appears ONLY on the "DRILL THIS NOW" CTA for openings beyond the 2 included in Free tier. The user sees the full picture; Pro unlocks the full training. Never gate the diagnosis itself.

**Regeneration:**
- Free tier: report generates once after initial import. Re-generates automatically on next Lichess sync.
- Pro: manual "Re-analyze" button available at any time.

**Fallback (no Lichess / <3 games per opening):**
- If user has no Lichess account or insufficient game history, the report cannot generate meaningfully from Lichess data.
- Alternative: after 5 completed sparring sessions in NeonGambit, generate a mini Glitch Report from session data (`source: "sessions"`).
- Mini report uses: ECO codes played, accuracy per opening, blunder patterns from session move history.

## Criterios de aceptación (BDD)

```
GIVEN an authenticated user with lichess_username set and games imported
WHEN they call POST /v1/glitch-report/generate
THEN a background job starts
AND job_id is returned immediately
AND status is 'processing'

GIVEN a report generation job in progress
WHEN GET /v1/glitch-report/status?job_id is polled
THEN status is one of: 'processing' | 'complete' | 'failed'
AND on 'complete': report is accessible via GET /v1/glitch-report/current

GIVEN a completed Glitch Report for a free-tier user
WHEN GET /v1/glitch-report/current is called
THEN all critical_openings are returned (not filtered)
AND the top 2 openings have training_unlocked=true
AND remaining openings have training_unlocked=false
AND all openings have neon_diagnosis populated

GIVEN a completed Glitch Report for a Pro user
WHEN GET /v1/glitch-report/current is called
THEN all critical_openings have training_unlocked=true

GIVEN games that follow the collapse classification rules
WHEN the analyzer processes a game with a single-move material swing ≥ 1.5 pawns
THEN collapse_type is 'tactical_blunder'
WHEN the analyzer processes a game where evaluation drifts from 0 to -1.5 over 3-5 moves
THEN collapse_type is 'positional_drift'
WHEN the analyzer processes a game where collapse is within the opening's theory range
THEN collapse_type is 'opening_error'
WHEN the analyzer detects the user had <20% time remaining at the collapse move
THEN collapse_type is 'time_pressure'

GIVEN a user with no lichess_username set
WHEN POST /v1/glitch-report/generate is called
THEN 400 is returned with "Connect your Lichess account first"

GIVEN a user with <3 games in any single opening
WHEN the report generates
THEN those openings are excluded from critical_openings (insufficient sample)
```

## Contratos de API

```
POST /v1/glitch-report/generate
  Auth:     Bearer JWT (any user)
  Request:  {} (no body)
  Response 200: {
    "job_id": string,
    "status": "processing",
    "message": "Analyzing your game history..."
  }
  Response 400: { "detail": "Connect your Lichess account first via /lichess/import" }

GET /v1/glitch-report/status
  Auth:     None (job_id is opaque)
  Query:    job_id=string
  Response 200 (processing): {
    "job_id": string,
    "status": "processing",
    "message": string   // e.g. "Running Stockfish analysis on Sicilian games..."
  }
  Response 200 (complete): {
    "job_id": string,
    "status": "complete",
    "message": "Your Glitch Report is ready."
  }
  Response 200 (failed): {
    "job_id": string,
    "status": "failed",
    "message": string
  }
  Response 404: { "detail": "Job not found" }

GET /v1/glitch-report/current
  Auth:     Bearer JWT (any user)
  Response 200: {
    "id": uuid,
    "games_analyzed": int,
    "rating_at_generation": int | null,
    "generated_at": datetime,
    "source": "lichess" | "sessions",
    "critical_openings": [
      {
        "eco_code": string,             // e.g. "B70"
        "opening_name": string,          // e.g. "Sicilian Defense"
        "games": int,
        "wins": int,
        "losses": int,
        "win_rate": float,              // 0–100
        "avg_collapse_move": int | null,
        "collapse_type": "opening_error" | "tactical_blunder" | "positional_drift" | "time_pressure" | null,
        "neon_diagnosis": string,        // Gemini-generated, NEON voice, ≤ 60 words
        "is_critical": bool,
        "linked_opening_id": uuid | null,
        "training_unlocked": bool        // Free: top 2. Pro: all.
      }
    ],
    "strengths": [
      {
        "eco_code": string,
        "opening_name": string,
        "games": int,
        "win_rate": float
      }
    ],
    "overall_pattern": string | null     // 2-sentence Gemini summary, ≤ 60 words
  }
  Response 404: { "detail": "No Glitch Report found. Run /glitch-report/generate first." }
```

## Worker behavior (glitch_report_worker.py)

```
1. Load all lichess_games for user from DB
2. Aggregate by eco_code: wins, losses, win_rate, game_count
3. Filter: eco_codes with <3 games are excluded
4. Sort by win_rate ascending → top 4 are 'critical', win_rate ≥ 55% are 'strengths'
5. For each critical opening (up to 4):
   a. Select up to 5 worst games (losses, oldest first as sample)
   b. For each game, run stockfish_service.analyze_game_collapse(pgn) → collapse_move
   c. For each game, run _classify_collapse(pgn, user_color) → collapse_type
   d. avg_collapse_move = mean of collapse_moves
   e. dominant collapse_type = Counter(collapse_types).most_common(1)[0][0]
6. For each critical opening:
   a. Call coach_service.generate_diagnosis(eco, name, stats, elo, collapse_type, locale)
   b. Lookup linked_opening_id from openings table (match on eco_code)
   c. training_unlocked = (i < 2) for free users; True for all if pro
7. Generate overall_pattern via coach_service.generate_overall_pattern(critical_openings, elo, locale)
8. Write GlitchReport row (is_current=True), set previous reports is_current=False
9. Auto-assign top 2 critical openings to user_repertoire (upsert)
10. Update job status: 'complete'
```

## Collapse type classification rules

```python
# _classify_collapse(pgn, user_color) → collapse_type:
#
# 1. 'time_pressure'   — collapse_move timestamp has user with <20% clock remaining
#                        (requires clock data in PGN; skip if not available)
# 2. 'opening_error'   — collapse_move <= opening's theory depth AND move not in
#                        top-3 Lichess Explorer moves for that position
# 3. 'tactical_blunder'— eval_before - eval_after >= 150 centipawns in a single move
#                        (concrete material swing, not gradual)
# 4. 'positional_drift'— no single move loses >= 150cp, but cumulative drift from
#                        ~0.0 to <= -1.5 over 3-5 consecutive moves
#
# Precedence: time_pressure > opening_error > tactical_blunder > positional_drift
# Default: 'positional_drift' if classification fails
```

## Estado del frontend

```
useGlitchReportStore (Zustand):
  - reportStatus: 'idle' | 'generating' | 'ready' | 'failed'
  - jobId: string | null
  - report: GlitchReport | null
  - generateReport(): void
  - pollStatus(jobId: string): void
  - clearReport(): void

GlitchReportReveal component:
  - Cinematic reveal: dark background, data loads line by line with typewriter effect
  - Critical openings appear one by one with a red warning flash animation
  - collapse_type badge shown on each opening (color-coded):
      - opening_error: amber
      - tactical_blunder: magenta
      - positional_drift: violet
      - time_pressure: amber
  - "DRILL THIS NOW" CTA:
      - training_unlocked=true → navigates to /drill with opening pre-selected
      - training_unlocked=false → opens UpgradeModal
  - Strengths section shown below critical openings
  - overall_pattern shown at the bottom in NEON terminal style

CriticalOpeningCard props:
  - All visible in Free tier (no blur, no placeholder)
  - Lock icon ONLY on the CTA button for locked openings
  - Never lock or hide the stats or neon_diagnosis
```

## Criterios de performance

- `POST /glitch-report/generate` must respond in < 300ms (job queued, not blocking)
- Status poll: < 100ms (Redis read)
- Full report generation: < 90 seconds (Stockfish analysis on up to 20 games + Gemini)
- `GET /glitch-report/current` (cached from DB): < 200ms

## Edge cases

- **No games imported:** 400 error. Frontend shows "Import your Lichess games first."
- **All openings have <3 games:** Report generates with empty critical_openings + empty strengths. overall_pattern: "Not enough data yet. Play more games and sync again."
- **Stockfish unavailable on VPS:** Skip collapse analysis, set collapse_type=null, set avg_collapse_move=null. Report still generates with Gemini diagnosis.
- **Gemini API unavailable:** Use hardcoded fallback: "You lose {loss_rate}% of {opening_name} games. This pattern is fixable."
- **User triggers generate twice:** Cancel first job if still processing, start new one.
- **Re-generate (Pro):** Previous report's is_current set to False before new report saves.

## Tests requeridos (antes de implementar)

```
# /backend/tests/test_lichess_analyzer.py

test_report_generates_critical_openings
  → mock games with known win rates → report has correct critical_openings list

test_report_excludes_openings_with_fewer_than_3_games
  → eco with 2 games → not in critical_openings

test_report_classifies_tactical_blunder
  → game where collapse move loses ≥ 150cp → collapse_type='tactical_blunder'

test_report_classifies_positional_drift
  → game with gradual eval drop → collapse_type='positional_drift'

test_report_classifies_opening_error
  → game where collapse is off-theory in opening range → collapse_type='opening_error'

test_report_free_tier_training_unlocked
  → free user → top 2 openings training_unlocked=True, rest False

test_report_pro_all_training_unlocked
  → pro user → all openings training_unlocked=True

test_report_auto_assigns_top_2_to_repertoire
  → after generate → user_repertoire has top 2 critical openings

test_generate_without_lichess_username
  → POST /glitch-report/generate without lichess_username → 400

test_current_report_404_when_none
  → GET /glitch-report/current with no report → 404

test_strengths_populated
  → openings with win_rate ≥ 55% appear in strengths list

# /backend/tests/test_glitch_report_worker.py

test_worker_updates_job_status_on_complete
  → worker finishes → job status='complete' in Redis

test_worker_handles_stockfish_failure
  → stockfish unavailable → report still generates, collapse_type=null

test_worker_handles_gemini_failure
  → Gemini throws → fallback diagnosis used, report still saves
```
