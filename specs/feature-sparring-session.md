# Feature Spec: Repertoire Sparring — "The Arena"

## Contexto del usuario
The Frustrated Improver knows their weak openings from the Glitch Report. Now they need to practice them — not against a perfect engine, but against an opponent that plays like the real humans they face on Lichess. Every move must feel meaningful. The coaching must feel earned, not generic.

**Emotion target:** "The opponent actually plays like a human, not a robot."

## Comportamiento esperado

1. User selects an opening from their auto-assigned repertoire (top 2 for Free, all critical for Pro).
2. User selects opponent ELO (800–1800) and color.
3. `POST /v1/sessions` creates the session. `neon_intro` is returned immediately.
4. **Move flow (client-server loop):**
   - Client optimistically renders the move on the board
   - Client sends `POST /v1/sessions/{id}/moves` with the move + previous move's quality (evaluated client-side via stockfish.wasm)
   - Server validates legality, updates theory tracking, returns `coach_message` from template library (instant, no LLM)
   - Client calls `POST /v1/sessions/{id}/opponent-move` to get the opponent's response
   - Opponent thinking time is randomized (400–2500ms), weighted by move popularity
5. **Theory integrity** decreases as the user deviates from the opening's theory line.
6. **Theory exit** detected when user leaves the known opening line (after move 5). NEON fires the `theory_exit` template immediately.
7. **Survival Mode** activates when the opponent plays off-book. Amber HUD shift + NEON message.
8. **Tilt tracking:** after each loss, `consecutive_sparring_losses` increments. If ≥ 3 losses in 25 minutes, tilt is flagged in the dashboard.
9. Game ends on checkmate, stalemate, or resign. Session marked `completed`.

**ADR-002 — No server-side Stockfish during sparring:**
The server NEVER calls Stockfish during a sparring session. Move quality (excellent/good/inaccuracy/mistake/blunder) is evaluated client-side via stockfish.wasm Web Worker. The client reports `prev_move_quality` on the *next* move call. The server uses that reported quality for stats tracking and coaching template selection. The server trusts the client for quality — it only validates legality.

**ADR-004 — Template-only coaching during gameplay:**
All `coach_message` values come from `neon_templates.yaml`, selected by pattern matching on `prev_move_quality`. NO Gemini calls during a live session. The only Gemini call is the `neon_intro` at session start (optional, can fall back to template).

## Criterios de aceptación (BDD)

```
GIVEN an authenticated user with openings in their repertoire
WHEN they call POST /v1/sessions with a valid opening_id
THEN a session is created with status='active'
AND current_fen is the starting position
AND neon_intro is returned (template or Gemini, ≤ 15 words)

GIVEN an active session
WHEN the user sends a legal move via POST /v1/sessions/{id}/moves
THEN valid=true is returned
AND new_fen reflects the updated position
AND theory_integrity is updated

GIVEN an active session
WHEN the user sends an illegal move
THEN valid=false is returned
AND error describes the illegal move
AND legal_moves list is included in the response

GIVEN a user move that exits the opening's theory line (after move 5)
WHEN the move is processed by the server
THEN theory_exit_detected=true is returned
AND theory_exit_move is set to the current move number
AND coach_message contains the theory_exit template text

GIVEN a move where client-reported prev_move_quality is 'blunder' or 'mistake'
WHEN the server processes the next move
THEN coach_message is populated from the appropriate template
AND the session's blunder or mistake counter is incremented

GIVEN an active session where the user's turn is complete
WHEN POST /v1/sessions/{id}/opponent-move is called
THEN a legal opponent move is returned
AND thinking_time_ms is between 400 and 2500
AND source indicates 'lichess_cache', 'lichess_api', or 'fallback'
AND out_of_book is true if the opponent deviated from theory

GIVEN an active session
WHEN POST /v1/sessions/{id}/resign is called
THEN session.result='loss', session.session_status='completed'
AND consecutive_sparring_losses increments in user_stats

GIVEN a user with 3 consecutive losses within 25 minutes
WHEN the dashboard is checked
THEN tilt_detected=true is returned

GIVEN a free-tier user
WHEN they try to create a session with an opening not in their repertoire
THEN 403 is returned with an upgrade prompt
```

## Contratos de API

```
POST /v1/sessions
  Auth:     Bearer JWT (any user)
  Request:  {
    "opening_id": uuid,
    "player_color": "white" | "black",
    "opponent_elo": int   // 800–2000
  }
  Response 200: {
    "session_id": uuid,
    "current_fen": string,       // Starting FEN
    "player_color": string,
    "opponent_elo": int,
    "opening_name": string,
    "theory_integrity": 100.0,
    "neon_intro": string         // ≤ 15 words, NEON voice
  }
  Response 403: { "detail": "Grandmaster tier required" }  // if opening not in user's repertoire

POST /v1/sessions/{session_id}/moves
  Auth:     Bearer JWT (session owner only)
  Request:  {
    "from": string,              // e.g. "e2"
    "to": string,                // e.g. "e4"
    "promotion": "q"|"r"|"b"|"n" | null,
    "prev_move_quality": "excellent"|"good"|"inaccuracy"|"mistake"|"blunder" | null,
    "prev_move_eval_cp": int | null   // Client-side centipawn eval of previous move
  }
  Response 200 (valid): {
    "valid": true,
    "new_fen": string,
    "theory_integrity": float,       // 0–100
    "theory_exit_detected": bool,
    "theory_exit_move": int | null,
    "out_of_book": bool,
    "coach_message": string | null   // Template-driven, instant
  }
  Response 200 (invalid): {
    "valid": false,
    "error": string,
    "legal_moves": ["e2e4", "d2d4", ...]  // UCI format
  }
  Response 404: { "detail": "Session not found" }
  Response 400: { "detail": "Session is not active" }

POST /v1/sessions/{session_id}/opponent-move
  Auth:     Bearer JWT (session owner only)
  Response 200: {
    "move": { "from": string, "to": string, "san": string, "uci": string },
    "new_fen": string,
    "thinking_time_ms": int,        // 400–2500
    "out_of_book": bool,
    "source": "lichess_cache" | "lichess_api" | "fallback"
  }
  Response 404: { "detail": "Session not found" }

POST /v1/sessions/{session_id}/resign
  Auth:     Bearer JWT (session owner only)
  Response 200: { "status": "completed", "result": "loss" }

GET /v1/sessions/{session_id}
  Auth:     Bearer JWT (session owner only)
  Response 200: {
    "session_id": uuid,
    "opening_name": string,
    "current_fen": string,
    "player_color": string,
    "session_status": "active" | "completed" | "abandoned",
    "result": "win" | "loss" | "draw" | null,
    "accuracy_score": float,
    "theory_integrity": float,
    "theory_exit_move": int | null,
    "excellent_moves": int,
    "good_moves": int,
    "inaccuracies": int,
    "mistakes": int,
    "blunders": int,
    "created_at": datetime,
    "completed_at": datetime | null
  }
```

## Opponent move selection (session_service.py)

```
1. Fetch moves from Lichess Explorer for current FEN + ELO bucket (±100 ELO)
2. Select move probabilistically weighted by Explorer frequency (human-like, not engine-perfect)
3. If no Explorer moves available:
   → Pick random legal move (fallback)
   → out_of_book=True, source='fallback'
4. Thinking time = max(400, min(2500, 2000 * (1 - probability) ± 200ms noise))
   (Popular moves come faster. Rare moves take longer — feels human.)
5. Apply move to board, return new_fen

NOTE: NO Stockfish calls in this path.
```

## Theory exit detection

```
- Opening has starting_moves list (e.g. ['e4', 'c5', 'Nf3', 'd6'])
- After each user move, check if new board position still matches theory line
- theory_exit_move is set once and never overwritten
- theory_integrity decreases by 10% per deviation from theory (minimum 0%)
- Only detect theory exit after move 5 (avoid false positives in very short lines)
```

## Tilt detection logic

```
# In user_stats table:
- consecutive_sparring_losses: INT DEFAULT 0
- last_sparring_loss_at: TIMESTAMP

# After session loss (resign or checkmate against user):
  consecutive_sparring_losses += 1
  last_sparring_loss_at = now()

# After session win or draw:
  consecutive_sparring_losses = 0

# Tilt condition:
  consecutive_sparring_losses >= 3
  AND (now() - last_sparring_loss_at) <= 25 minutes

# TiltIntervention component shown BEFORE "Play Again" button renders.
# Not a hard block. User can bypass.
# Counter resets after any win or 2+ hours of inactivity.
```

## Estado del frontend

```
useSessionStore (Zustand):
  - sessionId: string | null
  - currentFen: string
  - playerColor: 'white' | 'black'
  - opponentElo: int
  - openingName: string
  - theoryIntegrity: number        // 0–100
  - theoryExitMove: number | null
  - moveHistory: MoveRecord[]
  - sessionStatus: 'idle' | 'active' | 'completed'
  - result: 'win' | 'loss' | 'draw' | null
  - moveQualityCounts: { excellent, good, inaccuracy, mistake, blunder }
  - coachMessage: string | null
  - createSession(openingId, color, opponentElo): void
  - makeMove(from, to, promotion?): void
  - requestOpponentMove(): void
  - resign(): void

useStockfish (hook):
  - eval: number | null            // centipawn score for current position
  - bestMove: string | null
  - evaluatePosition(fen): void
  - classifyMoveQuality(evalBefore, evalAfter): MoveQuality

Arena page sequence:
  1. User makes move → optimistic render on board
  2. POST /sessions/{id}/moves (includes prev_move_quality from last Stockfish eval)
  3. Server response: update theory bar, show coach_message if any
  4. Client calls useStockfish.evaluatePosition(new_fen) to evaluate new position
  5. POST /sessions/{id}/opponent-move
  6. Animate opponent move after thinking_time_ms delay
  7. If out_of_book: show amber HUD flash + survival_mode template
  8. If game over: navigate to /debrief/{sessionId}

TiltIntervention component:
  - Shown after 3rd consecutive loss, BEFORE "Play Again" button
  - Not dismissible by X button — only by [GO TO DRILL] or [Play anyway]
  - Displays: consecutive loss count + time elapsed + NEON tilt template
```

## Criterios de performance

- `POST /sessions` must respond in < 300ms (DB insert + Gemini intro optional)
- `POST /sessions/{id}/moves` must respond in < 100ms (pure logic + template lookup)
- `POST /sessions/{id}/opponent-move` must respond in < 150ms (Redis cache hit) or < 500ms (API call)
- Client-side Stockfish eval must complete in < 2s per position (Web Worker, depth 12)

## Edge cases

- **User sends move out of turn:** 400 error. (Frontend should prevent this, but server validates.)
- **Session already completed:** 400 — "Session is not active."
- **Session not owned by user:** 404 (don't reveal existence).
- **Opening not in repertoire (Free tier):** 403 with upgrade prompt.
- **Lichess Explorer returns no moves:** Use random legal move fallback. Always returns a valid response.
- **Client reports prev_move_quality=null (first move):** Stats not updated. Normal.
- **Promotion not specified for pawn reaching last rank:** Server auto-promotes to queen.
- **Game ends by checkmate:** Server detects checkmate after move validation, returns `game_over: true` in the response.

## Tests requeridos (antes de implementar)

```
# /backend/tests/test_sessions.py

test_create_session_returns_fen_and_intro
  → POST /sessions → 200, has session_id + current_fen + neon_intro

test_create_session_requires_auth
  → POST /sessions without Bearer → 401

test_make_move_legal
  → POST /sessions/{id}/moves with e2→e4 → valid=true, new_fen updated

test_make_move_illegal
  → POST /sessions/{id}/moves with e2→e5 (illegal) → valid=false, error present

test_make_move_updates_theory_integrity
  → off-book move → theory_integrity decreases

test_theory_exit_detected
  → move off book after move 5 → theory_exit_detected=true in response

test_prev_move_quality_increments_counter
  → make move with prev_move_quality='blunder' → session.blunders += 1

test_opponent_move_returns_valid_move
  → POST /sessions/{id}/opponent-move → move in UCI format, new_fen valid

test_opponent_move_fallback_when_no_explorer_data
  → mock empty Explorer response → fallback=true, out_of_book=true

test_resign_completes_session
  → POST /sessions/{id}/resign → status='completed', result='loss'

test_resign_increments_tilt_counter
  → resign → user_stats.consecutive_sparring_losses += 1

test_win_resets_tilt_counter
  → session result='win' → consecutive_sparring_losses = 0

test_session_not_found_returns_404
  → moves on non-existent session → 404

# /backend/tests/test_session_service.py

test_validate_legal_move
  → chess_service.parse_move with legal move → returns Move object

test_validate_illegal_move
  → parse_move with illegal move → returns None

test_is_in_theory_true
  → board after 1.e4 matches opening starting_moves including 'e4' → True

test_is_in_theory_false
  → board after unexpected move → False

test_increment_quality_counter
  → _increment_quality_counter(session, 'blunder') → session.blunders += 1
```
