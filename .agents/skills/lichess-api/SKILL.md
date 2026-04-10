# Skill: lichess-api

Lichess REST + Explorer API integration for game import and opening theory.

## LichessService (Section 6.4)

```python
# app/services/lichess_service.py

class LichessService:

    async def fetch_user_games(self, username: str, max_games: int = 200) -> list[dict]:
        """
        Fetch recent games via NDJSON streaming API.
        Endpoint: GET /api/games/user/{username}
        Params: max, opening=true, pgnInJson=true, clocks=false, evals=false
        Returns: list of game dicts with eco, result, moves, pgn.
        Cost: free — no auth required for public games.
        """
        url = f"{self.base_url}/api/games/user/{username}"
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("GET", url, params=params, headers=self.headers) as r:
                async for line in r.aiter_lines():
                    if line.strip(): games.append(json.loads(line))

    async def fetch_current_rating(self, username: str) -> Optional[int]:
        """GET /api/user/{username} → perfs.rapid.rating"""

    async def get_explorer_moves(self, fen: str, rating_range: list[int], speeds: list[str]) -> list[dict]:
        """
        Lichess Explorer API for opening theory.
        Endpoint: GET /api/opening-explorer/lichess
        Returns: [{move, uci, san, white_wins, draws, black_wins, probability}]
        Cache: Redis 30-day TTL (check cache before HTTP call)
        """
        elo_bucket = (rating_range[0] // 200) * 200
        cache_key = f"opening:{hash_fen(fen)}:{elo_bucket}"
        cached = await redis_client.get(cache_key)
        if cached: return json.loads(cached)
        # ... HTTP call ...
        await redis_client.setex(cache_key, 2592000, json.dumps(result))  # 30 days
```

## Lichess Import Worker (Section 8)

Background task — does NOT block the HTTP response.

```python
# app/workers/lichess_import_worker.py
async def start_import_job(background_tasks, user_id, username, max_games, db) -> str:
    job_id = str(uuid.uuid4())
    await redis_client.setex(f"job:{job_id}", 3600, json.dumps({"status": "processing", "progress": 0}))
    background_tasks.add_task(_run_import, job_id, user_id, username, max_games)
    return job_id

async def _run_import(job_id, user_id, username, max_games):
    # 1. fetch_user_games(username, max_games)
    # 2. Parse ECO codes → group by opening
    # 3. Store in lichess_games table
    # 4. Update lichess_rating_snapshots
    # 5. Update job status in Redis
    # NO Stockfish calls here (that's glitch_report_worker)
    # NO conversion_failures analysis (Phase 2)
```

## Import Router (Section 7.2)

```python
# POST /lichess/import → start_import_job → return {job_id, status, estimated_seconds}
# GET  /lichess/import/status?job_id=... → get_job_status (polls Redis)
```

## Rate Limits

- Free: 20 games max per import, 3 imports/day
- Pro: 200 games max per import

## Degraded Mode

If Lichess API is unavailable (timeout/5xx), the import worker:
1. Marks job as "failed" in Redis with friendly message
2. Does NOT crash the server
3. Frontend polls status and shows error state in LoadingTerminal

## Explorer API Usage

Used during sparring sessions for opening theory:
- Called by `session_service.py` to get expected moves for current position
- Elo bucket rounded to nearest 200 (e.g., 1234 → 1200) for cache efficiency
- Speeds: typically `["rapid", "classical"]` for theory lookup
