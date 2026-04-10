# Feature Spec: Analytics Dashboard — "Mission Control"

## Contexto del usuario
The Frustrated Improver needs to see progress. Not just abstract statistics — concrete evidence that their Lichess rating is moving after they've been training in NeonGambit. The dashboard closes the feedback loop between "I practiced the Sicilian for 3 days" and "my Sicilian win rate went from 22% to 41%." Without this, there's no proof the app works.

**Emotion target:** "NeonGambit did this."

## Comportamiento esperado

1. Dashboard loads with a single API call (`GET /v1/analytics/dashboard`). No separate calls.
2. Shows: current Lichess rating + 30-day delta, drill queue count for today, this week's stats, opening win rate improvements vs. Glitch Report baseline, streak, and recommended next session.
3. Drill queue count is prominently displayed with a [START DRILL] CTA — **in MVP, the drill queue IS the daily mission.**
4. Opening improvements compare current sparring session win rates against the Glitch Report baseline. A green delta means the training is working.
5. "Recommended Session" is determined by the weakest opening from the Glitch Report that has a linked opening_id.
6. Tilt state: if `tilt_detected=true`, a TiltIntervention banner appears instead of the "Start Sparring" CTA.
7. Lichess rating syncs automatically on app open and on manual "Re-sync" tap.

**MVP scope — what is NOT in the dashboard:**
- No conversion failure stats (Phase 2)
- No mission system (the drill queue IS the mission)
- No full game history list (sessions count only)
- No achievement badges (streak counter is the only gamification)

## Criterios de aceptación (BDD)

```
GIVEN an authenticated user with data in the system
WHEN GET /v1/analytics/dashboard is called
THEN a single response is returned with all dashboard fields
AND the response time is < 500ms

GIVEN a user who has synced Lichess at least once
WHEN the dashboard loads
THEN lichess_rating.current shows the latest rating
AND lichess_rating.delta_30_day shows the signed delta vs 30 days ago
AND lichess_rating.trend shows up to 8 weekly snapshots

GIVEN a user with no Lichess sync history
WHEN the dashboard loads
THEN lichess_rating is null (not an error)
AND all other fields still render normally

GIVEN a user with drill cards due today
WHEN the dashboard loads
THEN drill_queue_count equals the count from GET /drill/queue/count
AND estimated_drill_minutes = max(1, int(count * 0.75))

GIVEN a user with a Glitch Report and recent sparring sessions
WHEN the dashboard loads
THEN opening_improvements shows win_rate delta per critical opening
AND status is 'improving' if delta > 5, 'declining' if delta < -5, else 'stable'

GIVEN a user with 3 consecutive losses within 25 minutes
WHEN the dashboard loads
THEN tilt_detected=true
AND the frontend shows TiltIntervention banner instead of Start Sparring CTA

GIVEN a user with 5 days of activity (drill reviews or sessions)
WHEN the dashboard loads
THEN streak=5

GIVEN a new user with no Glitch Report
WHEN the dashboard loads
THEN has_glitch_report=false
AND recommended_session is null
AND the dashboard prompts "Import Lichess games to generate your Glitch Report"
```

## Contratos de API

```
GET /v1/analytics/dashboard
  Auth:    Bearer JWT (any user)
  Response 200: {
    "lichess_rating": {
      "current": int,            // Latest rating from lichess_rating_snapshots
      "delta_30_day": int,       // Signed delta vs 4 snapshots ago (approx 30 days)
      "trend": [int, ...]        // Up to 8 weekly rating snapshots (oldest first)
    } | null,
    "this_week": {
      "sessions": int,           // Completed sparring sessions in last 7 days
      "drill_cards_reviewed": int, // Total cards reviewed (correct + incorrect)
      "win_rate": float,         // 0–100, sessions won / sessions played
      "avg_accuracy": float      // Average accuracy_score across sessions
    },
    "opening_improvements": [
      {
        "eco_code": string,
        "opening_name": string,
        "baseline_win_rate": float,   // From original Glitch Report
        "current_win_rate": float,    // From sparring sessions in last 30 days
        "delta": float,               // current - baseline
        "status": "improving" | "stable" | "declining"
      }
    ],
    "drill_queue_count": int,          // Cards due today (before free tier cap)
    "streak": int,                     // Consecutive days with activity
    "tilt_detected": bool,
    "has_glitch_report": bool,
    "critical_opening_count": int,     // Number of is_critical openings in report
    "recommended_session": {
      "opening_id": uuid,
      "opening_name": string,
      "reason": string          // e.g. "Your weakest opening this week"
    } | null,
    "estimated_drill_minutes": int     // max(1, int(drill_queue_count * 0.75))
  }

GET /v1/analytics/rating-trend
  Auth:    Bearer JWT (any user)
  Response 200: {
    "snapshots": [
      { "rating": int, "snapshotted_at": datetime },
      ...
    ]
  }
  Notes:   Used by Profile page to render the RatingChart component.
           Returns all historical snapshots (not capped to 8).
```

## Lichess rating sync

```
# Sync happens via lichess_import_worker as a side effect of import:
#   → saves LichessRatingSnapshot with latest rating from fetched games

# Additionally: on app open, if last sync > 6 hours ago:
#   → background sync: fetch last 5 games, update snapshot if rating changed

# Manual trigger: user taps "Re-sync" on dashboard
#   → POST /lichess/import with existing lichess_username
#   → Respects rate limit (3 imports/day per user)

# LichessRatingSnapshot schema:
#   user_id, rating, snapshotted_at (datetime), source ('import'|'auto')
```

## Opening improvement logic

```
For each critical opening in the current Glitch Report:
  1. baseline_win_rate = opening's win_rate in the report (calculated at generation time)
  2. Query sparring_sessions in last 30 days where:
     - session has linked opening_id matching the opening
     - session_status = 'completed'
  3. current_win_rate = (wins / total sessions) * 100
     - If no sessions for this opening: current_win_rate = baseline (delta = 0, status = 'stable')
  4. delta = current_win_rate - baseline_win_rate
  5. status:
     - delta > 5  → 'improving'
     - delta < -5 → 'declining'
     - else       → 'stable'

Note: baseline_win_rate comes from Lichess games. current_win_rate comes from NeonGambit
sparring sessions. These are different data sources — that's intentional. The comparison
shows whether sparring practice is improving the opening's mastery.
```

## Streak calculation

```
# Streak = consecutive calendar days where the user had at least one:
#   - Completed sparring session, OR
#   - Drill review (correct or incorrect)

# Stored in user_stats.current_streak (INT)
# Updated after each session completion and each drill review:
#   IF last_activity_date = today: no change
#   IF last_activity_date = yesterday: current_streak += 1
#   IF last_activity_date < yesterday: current_streak = 1

# Streak shown on dashboard with 🔥 suffix only in frontend
# No streak freeze, no streak restore in MVP
```

## Estado del frontend

```
useDashboardStore (Zustand):
  - dashboard: DashboardResponse | null
  - loading: boolean
  - error: string | null
  - lastFetched: Date | null
  - fetchDashboard(): void

MissionControl component layout:
  1. LICHESS SYNC panel (top):
     - "@username · Rating: 1,387 (+47 this month)"
     - Last synced timestamp
     - [Re-sync] button (respects 3/day limit)
     - If lichess_rating=null: "Sync your Lichess account" CTA
  2. TODAY'S DRILL panel:
     - "{drill_queue_count} moves due · Est. {estimated_drill_minutes} min"
     - [▶ START DRILL] button → navigates to /drill
     - If drill_queue_count=0: "All caught up. Next review tomorrow."
  3. THIS WEEK panel:
     - Sessions, moves drilled, win rate, streak badge
  4. OPENING PROGRESS panel:
     - One row per opening_improvement
     - delta shown as "+19%" (green) or "-8%" (red)
  5. RECOMMENDED SESSION panel:
     - If tilt_detected: TiltIntervention banner instead of CTA
     - Otherwise: opening name + reason + [▶ START SPARRING] button
     - If no Glitch Report: prompt to generate one
```

## Criterios de performance

- `GET /analytics/dashboard`: < 500ms total (multiple DB queries, all must be fast)
- All sub-queries must use indexed columns (user_id, created_at, next_review)
- Dashboard re-fetches on: app foreground event, manual pull-to-refresh, after session completion

## Edge cases

- **New user (no data at all):** Dashboard renders without errors. All numeric fields are 0. has_glitch_report=false. `this_week.sessions=0`.
- **Lichess rating data missing:** `lichess_rating=null`. Dashboard renders normally. Shows "Connect Lichess to track rating" prompt.
- **No sparring sessions this week:** `this_week.sessions=0`, `win_rate=0.0`. Does not error.
- **Glitch Report exists but no linked openings:** `recommended_session=null`. Dashboard renders without recommended session panel.
- **Tilt detected + no Glitch Report:** Show tilt banner but not the Start Sparring CTA.
- **Delta_30_day when less than 4 snapshots exist:** Use oldest available snapshot as baseline.

## Tests requeridos (antes de implementar)

```
# /backend/tests/test_analytics_service.py

test_dashboard_new_user_returns_zeros
  → new user with no data → dashboard returns without error, all counts=0

test_dashboard_lichess_rating_populated
  → user has snapshots → lichess_rating.current matches latest snapshot

test_dashboard_lichess_rating_null_when_no_snapshots
  → user with no snapshots → lichess_rating=null

test_dashboard_drill_count_matches_due_cards
  → 7 due cards → drill_queue_count=7

test_dashboard_this_week_sessions
  → 3 sessions this week → this_week.sessions=3

test_dashboard_win_rate_calculated
  → 2 wins out of 4 sessions → win_rate=50.0

test_dashboard_opening_improvements_improving
  → baseline=22.0, current sparring win_rate=45.0 → status='improving'

test_dashboard_opening_improvements_no_sessions
  → no sparring sessions for opening → status='stable', delta=0.0

test_dashboard_tilt_detected_true
  → 3 losses in 20 minutes → tilt_detected=true

test_dashboard_tilt_detected_false
  → 3 losses but >25 minutes ago → tilt_detected=false

test_dashboard_streak_calculated
  → activity yesterday and today → streak=2

test_dashboard_recommended_session_worst_opening
  → Glitch Report with 3 openings → recommended is the one with lowest win_rate

test_dashboard_has_glitch_report_true
  → report exists → has_glitch_report=true

test_dashboard_has_glitch_report_false
  → no report → has_glitch_report=false

test_rating_trend_endpoint
  → GET /analytics/rating-trend → snapshots list with correct fields
```
