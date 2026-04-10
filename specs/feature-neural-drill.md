# Feature Spec: Neural Drill — "Move-Level Spaced Repetition"

## Contexto del usuario
The Frustrated Improver knows their weak openings. They've sparred. Now they need to engrave the correct moves into memory — not by grinding, but by practicing at the exact moment before they forget. The drill must feel like quick, satisfying practice (5–7 minutes), not homework.

**Emotion target:** "I actually remember that move now."

## Comportamiento esperado

1. The drill queue shows all moves due for review today.
2. For each card: board appears at the position BEFORE the move to learn. NEON asks: "What's the correct move here?"
3. User plays the move directly on the board (no multiple choice).
4. If correct → brief success animation → next card.
5. If user hesitates > 5s → "Shadow Move" ghost appears (correct piece target, semi-transparent).
6. If wrong → board resets, correct move plays automatically, NEON explains in 1 sentence.
7. SM-2 algorithm updates: correct (quality ≥ 3) = interval grows; wrong (quality < 3) = reset to 1 day.
8. Completing the full daily queue earns a streak day.

**Free tier cap:** 5 drill cards/day max. The queue screen shows total due count but only serves 5.
**Pro:** Unlimited daily cards + custom cards from sparring session blunder positions.

**Cards are populated when an opening is added to the user's repertoire** (after Glitch Report assigns it). `populate_cards_for_opening` creates one card per user-color move in the opening's theory line.

**In MVP, the drill queue IS the daily mission.** The dashboard shows: "7 moves due today · ~6 min" with a start button. No separate mission system.

## Criterios de aceptación (BDD)

```
GIVEN an authenticated user with openings in their repertoire
WHEN GET /v1/drill/queue is called
THEN a list of due cards is returned (next_review <= now)
AND each card contains: fen_before_move, expected_move, move_number, opening name
AND free-tier users receive at most 5 cards
AND Pro users receive up to the requested limit

GIVEN no cards due today
WHEN GET /v1/drill/queue is called
THEN an empty list is returned (not an error)

GIVEN a user plays the correct move (quality 4)
WHEN POST /v1/drill/review is called with quality=4
THEN next_review is scheduled further in the future (SM-2 interval grows)
AND repetitions increments

GIVEN a user plays the wrong move (quality 0)
WHEN POST /v1/drill/review is called with quality=0
THEN interval_days resets to 1
AND repetitions resets to 0
AND next_review is tomorrow

GIVEN a user who answered correctly on first try (quality 5)
WHEN GET /v1/drill/mastery/{opening_id} is called
THEN mastered_moves increments after 3 correct repetitions with easiness_factor ≥ 2.0

GIVEN an opening added to user's repertoire
WHEN populate_cards_for_opening is called for that opening
THEN one UserMoveMastery card is created for each user-color move in the theory line
AND no duplicate cards are created on repeated calls (upsert behavior)

GIVEN a free-tier user who has reviewed 5 cards today
WHEN they try to review a 6th card
THEN 429 is returned with message: "Daily drill limit reached. Unlock Pro for unlimited."

GIVEN a move_sequence_hash that doesn't exist for the user
WHEN POST /v1/drill/review is called with that hash
THEN 404 is returned
```

## Contratos de API

```
GET /v1/drill/queue
  Auth:    Bearer JWT (any user)
  Query:   limit=int (optional, default 8; ignored for free tier, capped at 5)
  Response 200: [
    {
      "opening_id": uuid,
      "move_number": int,
      "expected_move": string,     // SAN notation, e.g. "Nf3"
      "fen_before_move": string,   // Board position to show on the drill board
      "move_sequence_hash": string, // Unique card identifier
      "repetitions": int,
      "correct_count": int
    },
    ...
  ]

GET /v1/drill/queue/count
  Auth:    Bearer JWT (any user)
  Response 200: { "count": int }   // Total due cards (before free tier cap)
  Notes:   Used by dashboard to display "7 moves due today"

POST /v1/drill/review
  Auth:    Bearer JWT (any user)
  Request: {
    "move_sequence_hash": string,
    "quality": int    // SM-2 scale: 0 (complete blackout) to 5 (perfect recall)
  }
  Response 200: {
    "next_review": datetime,   // ISO 8601
    "interval_days": int,
    "repetitions": int
  }
  Response 400: { "detail": "Quality must be 0-5" }
  Response 404: { "detail": "Card not found" }
  Response 429: { "detail": "Daily drill limit reached. Unlock Pro for unlimited." }

GET /v1/drill/mastery/{opening_id}
  Auth:    Bearer JWT (any user)
  Response 200: {
    "opening_id": uuid,
    "total_moves": int,
    "mastered_moves": int,      // repetitions >= 3 AND easiness_factor >= 2.0
    "mastery_percent": int,     // 0–100
    "next_due_at": datetime | null
  }
  Response 404: { "detail": "No cards found for this opening" }
```

## SM-2 Algorithm Implementation

```python
# app/services/srs_service.py — SM-2 core

def update_card(card: UserMoveMastery, quality: int) -> UserMoveMastery:
    """
    SM-2 algorithm. quality: 0-5 (0=total fail, 5=perfect recall).
    Below quality 3 = failed review → reset.
    """
    if quality >= 3:
        if card.repetitions == 0:
            card.interval_days = 1
        elif card.repetitions == 1:
            card.interval_days = 6
        else:
            card.interval_days = round(card.interval_days * card.easiness_factor)

        # Update easiness factor (never below 1.3)
        card.easiness_factor = max(
            1.3,
            card.easiness_factor + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
        )
        card.repetitions += 1
        card.correct_count += 1
    else:
        # Failed — reset to beginning
        card.repetitions = 0
        card.interval_days = 1
        card.incorrect_count += 1

    from datetime import datetime, timedelta
    card.last_reviewed = datetime.utcnow()
    card.next_review = datetime.utcnow() + timedelta(days=card.interval_days)
    return card

# Quality mapping from frontend:
# 5: correct on first try, no hesitation
# 4: correct (normal)
# 3: correct after Shadow Move hint
# 0: wrong (any incorrect move)
# Note: 1, 2 not used in MVP — simplified to correct/hint/wrong
```

## Cards population logic

```
populate_cards_for_opening(user_id, opening_id, depth=20):
  1. Load opening from DB (has starting_moves: list[str] and color: 'white'|'black')
  2. Replay opening moves on a chess.Board from starting position
  3. For each move in starting_moves[:depth]:
     a. Determine if it's the user's turn (board.turn == WHITE if color=='white')
     b. If yes: compute move_sequence_hash from all moves up to this point
     c. Check if card already exists for (user_id, move_sequence_hash)
     d. If not: create UserMoveMastery card with:
        - fen_before = current board.fen() BEFORE this move
        - expected_move = san notation of this move
        - move_number = board.fullmove_number
        - next_review = now() (due immediately)
     e. Push move onto board
  4. Flush to DB
```

## Estado del frontend

```
useDrillStore (Zustand):
  - queue: DrillCard[]
  - currentIndex: number
  - sessionComplete: boolean
  - streak: number
  - loadQueue(): void
  - submitReview(hash: string, quality: number): void
  - nextCard(): void

DrillCard component:
  - Shows chessboard at fen_before_move (react-chessboard)
  - Board is interactive: user plays directly by dragging/clicking
  - 5-second timer (no visible countdown — Shadow Move appears after 5s)
  - ShadowMove: ghost overlay on the correct destination square after 5s
    (CSS: opacity-40, cyan tint on destination square)
  - On correct move:
    → brief cyan flash animation
    → NEON: "Calculated." (or random positive template)
    → submitReview(hash, quality=5 if <5s else 4)
    → auto-advance to next card after 600ms
  - On incorrect move:
    → board resets to fen_before_move
    → correct move plays automatically (500ms animation)
    → NEON: 1-sentence explanation from template
    → submitReview(hash, quality=0)
    → "Try again" button (same card replays immediately)
  - On Shadow Move shown then correct:
    → submitReview(hash, quality=3)

DrillQueue screen:
  - Shows: "{count} moves due today · Est. {minutes} min"
  - Each card listed: Opening name, move number, days-since-review badge
  - [START DRILL] button
  - Free tier: shows total due count but caps session at 5 cards
    → after 5th card: "You've completed today's free drills. Unlock Pro for unlimited."

Streak logic (frontend):
  - After completing all cards in session (or daily cap):
    → call GET /analytics/dashboard to get updated streak
    → show streak animation if streak incremented
```

## Criterios de performance

- `GET /drill/queue`: < 150ms (indexed query on next_review)
- `POST /drill/review`: < 100ms (single row update + SM-2 calculation)
- `GET /drill/mastery/{opening_id}`: < 200ms (count query with filters)
- Shadow Move hint appears at exactly 5s (frontend timer, no server call)
- Card-to-card transition: < 700ms including animation

## Edge cases

- **No cards due:** Empty queue returned. Frontend shows "Nothing due today. Your next review is tomorrow." with a streak badge.
- **Opening added but no cards yet:** `populate_cards_for_opening` runs when opening is added to repertoire. If it hasn't run (edge case), queue is empty.
- **User plays move in wrong direction (flipped board):** Frontend normalizes input. Server returns card not found if hash doesn't match.
- **Free tier limit reached mid-session:** Server returns 429. Frontend shows upgrade prompt, not an error screen.
- **Duplicate card creation:** `populate_cards_for_opening` uses upsert semantics — existing cards not overwritten.
- **Opening with only opponent moves in theory:** No cards created (user has nothing to memorize for those positions). This is correct behavior.

## Tests requeridos (antes de implementar)

```
# /backend/tests/test_srs_service.py

test_sm2_correct_first_rep
  → quality=4, repetitions=0 → interval_days=1, repetitions=1

test_sm2_correct_second_rep
  → quality=4, repetitions=1 → interval_days=6

test_sm2_correct_third_rep_interval_grows
  → quality=4, repetitions=2, easiness_factor=2.5 → interval_days=15

test_sm2_failed_review_resets
  → quality=0 → interval_days=1, repetitions=0

test_sm2_easiness_never_below_1_3
  → repeated quality=0 reviews → easiness_factor stays >= 1.3

test_sm2_next_review_scheduled_correctly
  → after quality=4 on rep=2 → next_review ~15 days from now

test_populate_cards_creates_correct_count
  → opening with 10 moves, user plays white → 5 cards created (white's moves only)

test_populate_cards_is_idempotent
  → populate twice → still only 5 cards, no duplicates

# /backend/tests/test_drill_router.py

test_get_queue_returns_due_cards
  → cards with next_review <= now() → returned in queue

test_get_queue_free_tier_cap
  → 10 due cards, free user → only 5 returned

test_get_queue_empty
  → no due cards → empty list (not 404)

test_review_correct_updates_interval
  → POST /drill/review quality=4 → interval_days grows

test_review_wrong_resets_interval
  → POST /drill/review quality=0 → interval_days=1, repetitions=0

test_review_invalid_quality
  → quality=6 → 400

test_review_card_not_found
  → unknown hash → 404

test_free_tier_limit_429
  → 5 reviews done → 6th → 429

test_mastery_correct_counts
  → 3 cards mastered, 2 not → mastery_percent=60

test_queue_count_endpoint
  → GET /drill/queue/count → {"count": N}
```
