# Skill: stockfish-wasm

Client-side Stockfish WASM Web Worker for move quality evaluation during sparring.

**ADR-002: This is the architecture that eliminates server CPU costs during sparring.**
The server NEVER runs Stockfish during a sparring session. Move eval is client-side only.

## Web Worker (Section 7)

```typescript
// lib/stockfish/worker.ts
let engine: Worker | null = null;
let resolveEval: ((result: { score_cp: number; best_move: string }) => void) | null = null;
let lastScoreCp = 0;

export function initStockfish(): Promise<void> {
  return new Promise((resolve) => {
    engine = new Worker('/stockfish/stockfish.js'); // WASM loaded by the JS wrapper
    engine.onmessage = (e: MessageEvent) => {
      const line = e.data as string;
      if (line === 'uciok') resolve();
      if (resolveEval && line.startsWith('bestmove')) {
        const bestMove = line.split(' ')[1];
        resolveEval({ score_cp: lastScoreCp, best_move: bestMove });
        resolveEval = null;
      }
      if (line.includes('score cp')) {
        const match = line.match(/score cp (-?\d+)/);
        if (match) lastScoreCp = parseInt(match[1]);
      }
    };
    engine.postMessage('uci');
  });
}

export function evaluate(fen: string, depth = 12): Promise<{ score_cp: number; best_move: string }> {
  return new Promise((resolve) => {
    if (!engine) throw new Error('Stockfish not initialized');
    resolveEval = resolve;
    engine.postMessage(`position fen ${fen}`);
    engine.postMessage(`go depth ${depth}`);
  });
}

export function terminate() { engine?.terminate(); engine = null; }
```

## React Hook (Section 7)

```typescript
// lib/stockfish/useStockfish.ts
export function useStockfish() {
  const initialized = useRef(false);

  useEffect(() => {
    if (!initialized.current) {
      initStockfish().then(() => { initialized.current = true; });
    }
    return () => { terminate(); initialized.current = false; };
  }, []);

  const evaluate = useCallback(async (fen: string, depth = 12) => {
    if (!initialized.current) await initStockfish();
    return sfEvaluate(fen, depth);
  }, []);

  return { evaluate };
}
```

## WASM Fallback (Section 7)

```typescript
// Graceful degradation if WebAssembly not supported
if (typeof WebAssembly === 'undefined') {
  // wasmSupported = false
  // Move quality display is hidden (board still works, coaching still fires from templates)
  // Server is NOT called for Stockfish — feature degrades silently
}
```

## classifyMoveQuality (Arena Screen)

After each move, client evaluates position and classifies quality:

```typescript
function classifyMoveQuality(cpBefore: number, cpAfter: number): MoveQuality {
  const loss = cpBefore - cpAfter; // from player's perspective
  if (loss < 0) return 'excellent';   // gained eval
  if (loss < 25) return 'good';
  if (loss < 75) return 'inaccuracy';
  if (loss < 150) return 'mistake';
  return 'blunder';
}
```

## Usage in Arena

1. `useStockfish()` hook initialized on arena mount
2. Before player's move: `evaluate(currentFen)` → store `cpBefore`
3. After player's move: `evaluate(newFen)` → store `cpAfter`
4. Classify quality → display colored dot in EvalGauge
5. Send `prev_move_quality` to server with next move request

## File Locations

- `lib/stockfish/worker.ts` — Web Worker code
- `lib/stockfish/useStockfish.ts` — React hook
- `public/stockfish/stockfish.wasm` — WASM binary (load from /public or CDN)
- Depth cap: **12** client-side (fast enough for real-time, <300ms on modern devices)
