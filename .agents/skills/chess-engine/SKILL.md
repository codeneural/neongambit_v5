# Skill: chess-engine

Server-side chess logic with python-chess. Used for move validation, theory tracking, and Glitch Report analysis.

## ChessService (Section 6.2)

```python
# app/services/chess_service.py
import chess, hashlib
from typing import Optional

class ChessService:

    def parse_move(self, board: chess.Board, from_sq: str, to_sq: str, promotion: Optional[str] = None) -> Optional[chess.Move]:
        """Parse and validate a move. Returns None if illegal. Auto-promotes to queen if unspecified."""
        try:
            move = chess.Move(chess.parse_square(from_sq), chess.parse_square(to_sq),
                              promotion=chess.Piece.from_symbol(promotion.upper()).piece_type if promotion else None)
            if move not in board.legal_moves and not promotion:
                pawn_promo = chess.Move(chess.parse_square(from_sq), chess.parse_square(to_sq), promotion=chess.QUEEN)
                if pawn_promo in board.legal_moves: return pawn_promo
            return move if move in board.legal_moves else None
        except (ValueError, KeyError):
            return None

    def is_in_theory(self, board: chess.Board, opening_moves: list[str]) -> bool:
        """Check if current board position matches any position in the opening line."""
        test_board = chess.Board()
        for san in opening_moves:
            try: test_board.push_san(san)
            except Exception: return False
            if test_board.fen().split(" ")[0] == board.fen().split(" ")[0]:
                return True
        return test_board.fen().split(" ")[0] == board.fen().split(" ")[0]

    def hash_fen(self, fen: str) -> str:
        """MD5 of position-only FEN (strip move clocks for cache key stability)."""
        return hashlib.md5(fen.split(" ")[0].encode()).hexdigest()

    def get_legal_moves_uci(self, board: chess.Board) -> list[str]:
        return [m.uci() for m in board.legal_moves]

    def is_game_over(self, board: chess.Board) -> tuple[bool, Optional[str]]:
        """Returns (is_over, result) — result is 'win'|'loss'|'draw'|None."""
        if board.is_game_over():
            outcome = board.outcome()
            if outcome.winner is None: return True, "draw"
            return True, "win" if outcome.winner == chess.WHITE else "loss"
        return False, None

    def move_sequence_hash(self, moves: list[str]) -> str:
        """Stable hash for a move sequence — used as SRS card key."""
        return hashlib.md5("|".join(moves).encode()).hexdigest()
```

## StockfishService — Glitch Report ONLY (Section 6.3)

**ADR-002: NEVER call StockfishService during sparring sessions.**
Stockfish only runs in the background `glitch_report_worker.py`.

```python
class StockfishService:
    """Async wrapper. Single persistent process. Depth capped at STOCKFISH_MAX_DEPTH (15)."""

    async def analyze(self, fen: str, depth: int = 15) -> dict:
        """Returns {"score_cp": int, "best_move": str}"""

    async def analyze_game_collapse(self, pgn_moves: str) -> Optional[int]:
        """Find move number where evaluation swings >150cp against user. Used in Glitch Report."""
        # Skips opening moves (first 4 half-moves)
        # Only analyzes user's moves (i % 2 == 0 for white)
        # Returns collapse move number or None
```

## Architecture Rules

- Server validates move **legality** via python-chess on every `/sessions/{id}/move` call
- Server tracks **theory** (is_in_theory) and theory_exit_move
- Move **quality** (excellent/good/inaccuracy/mistake/blunder) is evaluated **client-side** via stockfish.wasm
- Client sends `prev_move_quality` to server with each move request
- Server uses `prev_move_quality` for coaching template selection and accuracy tracking

## Collapse Type Classification (Section 6.7)

Used in `lichess_analyzer.py` for Glitch Report:
- `opening_error` — collapse before move 15 (user played out of theory early)
- `tactical_blunder` — eval swing > 200cp from a tactic (hanging piece, fork missed)
- `positional_drift` — gradual eval decline across 5+ moves, no single blunder
- `time_pressure` — multiple mistakes after move 30 in rapid/blitz games
