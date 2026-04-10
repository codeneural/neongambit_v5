# Skill: coach-templates

NEON coaching template system — instant in-game feedback, zero LLM latency.

**ADR-004: In-game coaching is ALWAYS template-driven. Gemini is ONLY for Glitch Report narratives and post-session summaries.**

## Template Library Structure (neon_templates.yaml)

```yaml
pattern_key:
  en:
    low:           # ELO 800–1200: immediate, concrete
      short: "≤20 words"    # Shown in NEON terminal during sparring
      detail: "≤40 words"   # Post-game debrief / tap-to-expand
    mid:           # ELO 1200–1500: pattern-based
      short: "..."
      detail: "..."
    high:          # ELO 1500–1700: strategic, layered
      short: "..."
      detail: "..."
  es:
    low/mid/high: same structure
```

## Available Pattern Keys

**Blunders:**
- `blunder_hanging_piece` — material left undefended
- `blunder_fork` — missed fork tactic by opponent
- `blunder_positional` — positional blunder (<200cp swing)

**Mistakes:**
- `mistake_tempo_loss` — loss of initiative
- `mistake_positional_drift` — gradual decline

**Excellent moves:**
- `excellent_double_threat` — created two threats simultaneously

**Theory:**
- `theory_exit` — player left opening book

**Generic:**
- `generic_good` — good move, no specific pattern

## Template Loading (coach_templates.py)

```python
def load_templates():
    """Load YAML at startup — call once in lifespan or service init."""
    path = Path(__file__).parent.parent.parent / "data" / "neon_templates.yaml"
    with open(path) as f:
        _templates = yaml.safe_load(f)

def get_template(pattern: str, elo_tier: str, locale: str = "en") -> Optional[str]:
    """Returns template string with {placeholders}, or None."""
    entry = _templates.get(pattern, {})
    localized = entry.get(locale, entry.get("en", {}))
    return localized.get(elo_tier, localized.get("all"))

def select_pattern(move_quality: str, eval_before_cp: int, eval_after_cp: int, theory_exit: bool) -> str:
    if theory_exit: return "theory_exit"
    cp_loss = abs(eval_before_cp - eval_after_cp)
    if move_quality == "blunder":
        if cp_loss > 300: return "blunder_hanging_piece"
        elif cp_loss > 200: return "blunder_fork"
        else: return "blunder_positional"
    elif move_quality == "mistake": return "mistake_tempo_loss"
    elif move_quality == "inaccuracy": return "mistake_positional_drift"
    elif move_quality == "excellent": return "excellent_double_threat"
    return "generic_good"

def elo_tier(elo: int) -> str:
    if elo < 1200: return "low"
    if elo < 1500: return "mid"
    return "high"
```

## NEON Persona Rules

- Direct, efficient, slightly cryptic. A grandmaster who's also a hacker.
- Never condescending. Never sycophantic.
- Name the specific consequence, never the shame.
- Cyberpunk terms sparingly: "calculated", "glitch", "system error"
- Never use "good job" or "well done"

## CoachService — When to Call Gemini

```python
# Gemini is ONLY called for:
# 1. Glitch Report: neon_diagnosis + overall_pattern (async background worker)
# 2. Post-session summary (after session end, non-blocking)
# NEVER called during active sparring gameplay
```

## Placeholders in Templates

`{piece}`, `{square}`, `{square1}`, `{square2}`, `{best_move}`, `{move}`,
`{valuable_piece}`, `{plan_description}`, `{threat_type}`, `{escape_move}`

Replace at render time in coach_service.py before returning to client.

## File Locations

- `data/neon_templates.yaml` — template library (~200 templates, EN + ES)
- `app/services/coach_templates.py` — loader + pattern selector
- `app/services/coach_service.py` — orchestrator (templates + Gemini fallback)
