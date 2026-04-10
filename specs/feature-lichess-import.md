# Feature Spec: Lichess Game Import

## Contexto del usuario
The user has played hundreds of games on Lichess but has never had them analyzed as a coherent dataset. The import step is the moment NeonGambit transforms from "a chess app" into "something that knows me." It must feel fast (background worker) and trustworthy (progress feedback).

**Emotion target:** "It actually knows my games. It knows what I keep doing."

## Comportamiento esperado

1. User enters their Lichess username in the LichessConnectPrompt component.
2. `POST /v1/lichess/import` triggers a background job and immediately returns a `job_id`.
3. Frontend polls `GET /v1/lichess/import/status?job_id={id}` every 2 seconds.
4. A `LoadingTerminal` screen shows streaming progress lines: "Fetching games... Parsing ECO codes... Identifying patterns..."
5. On completion, `status: "complete"` triggers the Glitch Report generation flow.
6. **Free tier:** max 20 games. **Pro:** max 200 games.

**Degraded mode (Lichess API unavailable):**
- If Lichess API is down/rate-limited: show cached Glitch Report if one exists.
- Queue background retry every 15 minutes (max 8 retries).
- All sparring/drill features continue to work with already-imported data.
- Never show an error screen that blocks the user from training.

**Fallback (no Lichess or <20 games):**
- Prompt: "Play 5 sparring games and we'll generate your first report."
- After 5 sessions: mini Glitch Report from NeonGambit session data only.

## Criterios de aceptación (BDD)

```
GIVEN an authenticated user with lichess_username not yet set
WHEN they call POST /v1/lichess/import with a valid lichess_username
THEN a background job starts
AND job_id is returned immediately
AND user.lichess_username is updated in the DB
AND the response includes estimated_seconds

GIVEN a pending import job
WHEN GET /v1/lichess/import/status?job_id is polled
THEN status is one of: 'processing' | 'complete' | 'failed'
AND on 'processing': games_fetched count is included
AND on 'complete': games_fetched total and eco_codes_found are included

GIVEN a free-tier user
WHEN an import is triggered
THEN max_games is capped at 20 regardless of request body value

GIVEN a Pro user
WHEN an import is triggered
THEN max_games can be up to 200

GIVEN a Lichess username with no public games
WHEN the import job runs
THEN status becomes 'failed' with message: "No public games found for this username."

GIVEN the Lichess API returns 429 or 5xx
WHEN the import worker encounters the error
THEN job status becomes 'failed' with degraded_mode: true
AND background retries are queued (max 8, every 15 minutes)
AND cached data (if any) is served immediately
```

## Contratos de API

```
POST /v1/lichess/import
  Auth:    Bearer JWT (any user)
  Request: {
    "lichess_username": string,   // required
    "max_games": int              // optional, ignored for free tier (capped at 20)
  }
  Response 200: {
    "job_id": string,
    "status": "processing",
    "message": "Fetching up to 20 games from Lichess...",
    "estimated_seconds": int
  }
  Response 400: { "detail": "lichess_username is required" }

GET /v1/lichess/import/status
  Auth:    None (job_id is opaque)
  Query:   job_id=string
  Response 200 (processing): {
    "job_id": string,
    "status": "processing",
    "games_fetched": int,
    "message": string
  }
  Response 200 (complete): {
    "job_id": string,
    "status": "complete",
    "games_fetched": int,
    "eco_codes_found": int,
    "message": "Import complete. Ready for Glitch Report."
  }
  Response 200 (failed): {
    "job_id": string,
    "status": "failed",
    "degraded_mode": bool,
    "message": string
  }
  Response 404: { "detail": "Job not found" }
```

## Worker behavior (lichess_import_worker.py)

```
1. Fetch games via GET https://lichess.org/api/games/user/{username}
   ?max={max_games}&opening=true&pgnInJson=true&rated=true
2. Parse NDJSON stream → LichessGame objects
3. Extract per game: eco, opening_name, winner, user_color, moves, played_at, ratings
4. Upsert to lichess_games table (UNIQUE on user_id + lichess_game_id)
5. Update LichessRatingSnapshot with latest rating from fetched games
6. Update job status at each step (Redis key: job:{job_id})
7. On complete: set status='complete' with final counts

NOTE: No Stockfish analysis in this worker.
      Stockfish analysis happens in glitch_report_worker.py.
      No conversion_failure analysis (Phase 2).
```

## Estado del frontend

```
useLichessStore (Zustand):
  - importStatus: 'idle' | 'processing' | 'complete' | 'failed'
  - jobId: string | null
  - gamesImported: number
  - degradedMode: boolean
  - startImport(username: string): void
  - pollStatus(jobId: string): void

LoadingTerminal component:
  - Cycles through progress messages from API status responses
  - Shows typewriter effect on each new message
  - On 'complete': auto-navigates to Glitch Report generate flow
  - On 'failed' + degradedMode: shows "Using cached data" banner, continues to app
```

## Criterios de performance

- `POST /lichess/import` must respond in < 300ms (job queued, not blocking)
- Status poll latency: < 100ms (reading from Redis)
- Full import of 20 games: < 30 seconds end-to-end
- Lichess API timeout: 10 seconds per request, retry once before marking degraded

## Edge cases

- **Username with only private games:** status=failed, message: "No public games found."
- **Username doesn't exist on Lichess:** status=failed, message: "Lichess account not found."
- **User submits import twice:** Second import cancels/replaces the first job.
- **Import while previous import is processing:** Return existing job_id, don't start new job.
- **Rate limit (3 imports/day):** Return 429 with "Import limit reached. Try again tomorrow."

## Tests requeridos (antes de implementar)

```
# /backend/tests/test_lichess_import.py

test_import_starts_background_job
  → POST /lichess/import → 200, job_id in response

test_import_caps_free_tier_at_20_games
  → free user requests 200 games → max_games capped to 20

test_import_allows_200_for_pro
  → pro user → max_games=200 accepted

test_import_requires_username
  → POST /lichess/import with empty username → 400

test_import_status_returns_processing
  → poll immediately after start → status='processing'

test_import_status_not_found
  → GET /lichess/import/status?job_id=invalid → 404

test_worker_saves_games_to_db
  → mock Lichess API → worker runs → lichess_games rows created

test_worker_handles_lichess_429
  → mock Lichess 429 → job status becomes 'failed', degraded_mode=true

test_worker_deduplicates_games
  → import same games twice → no duplicate rows in lichess_games

test_import_updates_lichess_username_on_user
  → after import → user.lichess_username matches submitted username
```
