# Skill: redis-caching

Upstash Redis caching strategy for NeonGambit (async, via redis.asyncio).

## Redis Client (Section 9)

```python
# app/utils/cache.py
import redis.asyncio as aioredis
import json
from app.config import settings

redis_client = aioredis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
```

## Cache Key Patterns

```python
CACHE_KEYS = {
    # Opening Explorer responses: 30-day TTL
    "opening_position": "opening:{fen_hash}:{elo_bucket}",
    # Background job status: 1-hour TTL
    "import_job":       "job:{job_id}",
    "report_job":       "report_job:{job_id}",
    # Rate limiting: sliding window per user
    "rate_moves":       "rate:moves:{user_id}:{minute}",
    "rate_analyses":    "rate:analyses:{user_id}:{day}",
    "rate_drills":      "rate:drills:{user_id}:{day}",
    # Session locking: prevent concurrent moves
    "session_lock":     "lock:session:{session_id}",
}
```

## TTLs by Data Type

| Data | TTL | Reason |
|------|-----|--------|
| Lichess Explorer moves | 30 days (2592000s) | Changes very slowly; free API |
| Background job status | 1 hour (3600s) | Frontend polls for ~30s max |
| Session lock | 5 seconds | Prevents double-move race conditions |
| Rate limit counters | 60s (moves) / 86400s (daily) | Sliding windows |

## Common Patterns

### Cache-Aside (Opening Explorer)
```python
cached = await redis_client.get(cache_key)
if cached: return json.loads(cached)
result = await fetch_from_lichess(...)
await redis_client.setex(cache_key, 2592000, json.dumps(result))
return result
```

### Job Status (Background Workers)
```python
# Write
await redis_client.setex(f"job:{job_id}", 3600, json.dumps({"status": "processing", "progress": 0}))

# Update progress
async def update_job(job_id: str, status: str, progress: int, **kwargs):
    data = {"status": status, "progress": progress, **kwargs}
    await redis_client.setex(f"job:{job_id}", 3600, json.dumps(data))

# Read (frontend polls this)
async def get_job_status(job_id: str) -> Optional[dict]:
    val = await redis_client.get(f"job:{job_id}")
    return json.loads(val) if val else None
```

### Rate Limiting (Sliding Window)
```python
# app/core/rate_limiter.py
async def check_rate_limit(user_id: str, limit: int, window_seconds: int, key_suffix: str) -> bool:
    import time
    window = int(time.time()) // window_seconds
    key = f"rate:{key_suffix}:{user_id}:{window}"
    count = await redis_client.incr(key)
    if count == 1:
        await redis_client.expire(key, window_seconds * 2)
    return count <= limit
```

### Session Lock (Prevents Double-Move)
```python
lock_key = f"lock:session:{session_id}"
acquired = await redis_client.set(lock_key, "1", nx=True, ex=5)
if not acquired:
    raise HTTPException(429, "Move already being processed")
try:
    result = await process_move(...)
finally:
    await redis_client.delete(lock_key)
```

## Cost Optimization (Section 10)

**Rule 3:** All Lichess Explorer calls check Redis first. After 2–3 weeks of usage, >90% of common positions are cached. This eliminates most Lichess API calls.

**Rule 1:** Redis stores background job status (import + report jobs) — no DB polling needed.

## Upstash Connection

`REDIS_URL` format: `redis://default:{password}@{host}:{port}`

For Upstash, use TLS: `rediss://default:{password}@{host}:{port}`
