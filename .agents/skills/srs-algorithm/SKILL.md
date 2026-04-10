# Skill: srs-algorithm

SM-2 Spaced Repetition System for Neural Drill (opening move memorization).

## SRSService (Section 6.8)

```python
# app/services/srs_service.py

class SRSService:

    def calculate_next_review(self, repetitions: int, easiness: float, interval: int, quality: int) -> dict:
        """
        SM-2 algorithm.
        quality: 0=complete blackout, 3=correct with hint, 5=perfect recall.
        """
        if quality < 3:
            repetitions = 0
            interval = 1
        else:
            if repetitions == 0:   interval = 1
            elif repetitions == 1: interval = 6
            else:                  interval = round(interval * easiness)
            repetitions += 1

        easiness = max(1.3, easiness + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))

        return {
            "interval_days": interval,
            "repetitions": repetitions,
            "easiness_factor": round(easiness, 3),
            "next_review": datetime.utcnow() + timedelta(days=interval),
        }

    async def get_due_cards(self, user_id: str, limit: int, db: AsyncSession) -> list[UserMoveMastery]:
        """Fetch moves due for review, ordered by most overdue first."""
        result = await db.execute(
            select(UserMoveMastery)
            .where(UserMoveMastery.user_id == user_id,
                   UserMoveMastery.next_review <= datetime.utcnow())
            .order_by(UserMoveMastery.next_review)
            .limit(limit)
        )
        return result.scalars().all()

    async def record_review(self, user_id: str, move_sequence_hash: str, quality: int, db: AsyncSession) -> UserMoveMastery:
        """Apply SM-2 result to a card after the user answers."""
        card = ... # fetch by user_id + move_sequence_hash
        next_state = self.calculate_next_review(card.repetitions, card.easiness_factor, card.interval_days, quality)
        # Update card fields from next_state
        if quality >= 3: card.correct_count += 1
        else: card.incorrect_count += 1
        return card

    async def populate_cards_for_opening(self, user_id: str, opening_id: str, depth: int, db: AsyncSession):
        """
        When user adds an opening to repertoire → create SRS cards for each
        user-color move in the theory line up to `depth` moves.
        Skip if card already exists (idempotent).
        """
        # Iterates opening.starting_moves[:depth]
        # Only creates cards for moves where it's the user's turn
        # Card key: move_sequence_hash from chess_service.move_sequence_hash()
```

## SM-2 Intervals

| Repetitions | Interval |
|-------------|---------|
| 0 (first time) | 1 day |
| 1 | 6 days |
| 2+ | prev_interval × easiness_factor |

Initial easiness_factor = 2.5. Min 1.3.

## Free Tier Cap

`RATE_LIMIT_DRILLS_FREE_PER_DAY = 5` (from config)

`get_due_cards(limit=5)` for free users, `limit=unlimited` for Pro.

## Drill API Endpoints (Section 7.5)

```
GET  /drill/queue          → get_due_cards (respects free tier cap)
POST /drill/answer         → record_review + return next card
GET  /drill/stats          → mastery progress per opening
```

## SRS Card Key

Cards are keyed by `move_sequence_hash` (MD5 of pipe-joined move list).
This is stable even if opening names change.

Example: `e4|e5|Nf3|Nc6|Bc4` → hash → SRS card for Bc4

## Neural Drill Frontend Flow

1. Fetch queue → show count in Drill tab badge
2. Show DrillCard: position on board, hide expected move
3. After 5s: show ShadowMove ghost hint
4. User plays move → if correct: quality=5, if needed hint: quality=3, if wrong: quality=1
5. Show DrillResult (correct/incorrect) + streak increment on correct
6. Advance to next card
