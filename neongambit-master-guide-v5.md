# NeonGambit: Master Development Guide

**Version:** 5.1 — MVP-Scoped · Tactical Context Layer · i18n · Stockfish WASM · Hostinger Deploy
**Strategy:** Multi-Agent Development (Google Antigravity IDE) · Next.js PWA + FastAPI Backend
**Role:** Single Source of Truth
**Last Updated:** April 2026

---

## PART 0 — PRODUCT SOUL: WHO IS THIS FOR AND WHY WILL THEY CARE

Before a single line of code, a single screen, a single API endpoint — this section defines the human being we are building for. Every feature decision in this document flows from here.

---

### 0.1 The User We're Building For

**Primary persona: "The Frustrated Improver"**

Age 22–40. Plays chess regularly on Lichess (or Chess.com). Has a rating between 1000 and 1700. Has been at roughly the same rating for months — sometimes years. Watches YouTube videos. Does puzzles. Reads Reddit threads. Still plateaus.

They feel something specific and painful: **they know they should be better than their rating, but they can't figure out what's actually holding them back.** The gap between "I understand chess" and "I win chess games" is invisible to them.

**What they experience daily:**
- They play an opening they half-know, opponent plays something unexpected on move 7, and they spend 4 minutes panicking — burning clock, burning confidence — then blunder.
- They run their game through Stockfish after and see a sea of red arrows. They stare at the best moves and don't understand *why* those are better. They close the tab.
- They go to Chessable, start a course, memorize 40 moves, then return 3 days later to 80 due reviews and quit.
- They ask Reddit "how do I improve" and get the same advice: "study your games." They don't know how.
- They lose a game they were winning and feel genuine frustration — at themselves, at the randomness, at the game.
- They have a vague sense that their openings are a weakness, but don't know *which* openings or *why*.

**What they actually want (not what they say they want):**
- Not "a complete opening repertoire." They want to *stop feeling lost* in the first 10 moves.
- Not "AI analysis." They want to understand what they keep doing wrong — specifically, not generically.
- Not "more puzzles." They want to feel like they're getting better — *measurably* — without a coach.
- Not "a training tool." They want something that makes chess feel exciting again.

**The insight that drives this entire product:**

> Their game history on Lichess is a goldmine they have never properly mined. Every game they've played is a data point. Their losses cluster around predictable patterns — specific openings, specific move numbers, specific mistakes — but no tool has ever shown them this clearly and told them exactly what to do about it.

NeonGambit turns their personal Lichess history into a personalized improvement engine. Their past games aren't defeats to be forgotten. They're intelligence to be weaponized.

---

### 0.2 The Emotional Arc We're Designing

A great product creates a specific emotional journey. This is the arc we are engineering:

| Moment | Emotion we want to create |
|--------|--------------------------|
| First open | *"This looks different. This looks serious."* |
| Connecting Lichess account | *"It actually knows my games. It knows what I keep doing."* |
| Seeing the Glitch Report for the first time | *"...oh. That's exactly why I keep losing."* |
| First sparring session | *"The opponent actually plays like a human, not a robot."* |
| NEON gives feedback after a blunder | *"That's exactly what I needed to hear."* |
| Completing a Neural Drill perfectly | *"I actually remember that move now."* |
| Seeing ELO go up on Lichess after training | *"NeonGambit did this."* |

The last emotion is the retention engine. If a user gains 50 ELO on Lichess after a week of using NeonGambit, they will tell every chess friend they have.

---

### 0.3 What Makes NeonGambit Different (Honest Competitive Analysis)

| Product | What it does well | Why users still struggle |
|---------|------------------|--------------------------|
| Lichess | Free, powerful, huge database | No personalized guidance; analysis is raw engine output |
| Chess.com | Polished, great lessons | Generic — not based on *your* games |
| Chessable | Best SRS for openings | Memorization without context; review debt kills motivation |
| Chess Prep Pro | Opening + spaced rep | Dry UI; no sparring against human-like play |
| Chessstack | Import games, spot deviations | Technical and sparse; no coaching layer |
| Stockfish analysis | Perfect engine output | Tells you *what* the best move is, not *why* you missed it |

**NeonGambit's unique combination — none of the above does all of this together:**
1. **Your games → your training plan.** Lichess history directly generates a personalized weak-spot curriculum. Not generic openings. *Your* openings that *you* keep losing.
2. **Human-like sparring.** Opponent plays at your ELO using real Lichess statistical frequencies, not engine-perfect moves. You practice against the mistakes *real opponents at your level* make — and learn to punish them.
3. **Coaching that explains, not just evaluates.** NEON doesn't say "best move was Nf3." NEON says "you gave your opponent a free tempo — that's why this position collapsed."
4. **Cyberpunk aesthetic that makes studying feel like play.** Not another clinical chess interface. A world you want to enter.

---

### 0.4 Core Product Principles (Every Feature Is Filtered Through These)

1. **Personalization over comprehensiveness.** 3 openings deeply understood beat 50 openings memorized. Features that use the user's own data are worth 10x generic features.
2. **Show progress, not just problems.** Every training session must end with a clear signal that something improved. Mastery gauges, ELO projections, streak milestones.
3. **Explain the *why*, not just the *what*.** NEON's coaching must always connect the tactical event to a principle the user can carry to their next game.
4. **Human-like over perfect.** The opponent should feel like a real person, not an engine. Hesitations, probabilities, occasional suboptimal moves. This is what they'll face on Lichess.
5. **Never shame, always coach.** Blunders are "system errors," not failures. The tone is always: "here's what the position demanded — now you know."
6. **Make the history sacred.** Lichess games are treated as a valuable personal dataset, not just a sync feature. The user should feel their history is being honored and studied on their behalf.

---

### 0.5 MVP Scope Philosophy

**Build what proves the thesis. Defer everything else.**

NeonGambit's thesis is: *"If we show a chess player exactly where they keep losing and let them practice those specific positions against human-like opponents, they will measurably improve — and they'll pay for more."*

Three features prove or disprove this thesis. Everything else is Phase 2.

**MVP (Phase 1) — Ship this:**
| Feature | Why it's in MVP |
|---------|----------------|
| Lichess Import + Glitch Report | The hook. Without the "aha" moment, no one stays. |
| Repertoire Sparring (The Arena) | The core loop. This is what users come back to do daily. |
| Neural Drill (SM-2) | The habit engine. Short daily sessions create retention. |
| Tilt Detection | 20 lines of code, massive emotional impact. Included. |
| Streak Counter | Simple daily counter on dashboard. No full achievement system. |
| Mission Control Dashboard | Lightweight: rating sync + drill queue count + recommended session. |

**Phase 2 — Build after 50+ active users validate the loop:**
| Feature | Why it's deferred |
|---------|------------------|
| Conversion Failures + Endgame Drill | Excellent feature, but the Stockfish pipeline for eval-swing detection is CPU-heavy and complex. Build when the core loop is validated. |
| Full Game Review / Debrief | Move-by-move NEON narration is expensive (Gemini calls per move). MVP ships a summary-only debrief. |
| Repertoire Builder (full browse) | In MVP, NEON assigns your top 2-3 weak openings from the Glitch Report. No manual browsing needed yet. |
| Achievement System | Streak counter is enough for MVP. Full gamification is a retention optimization, not a launch requirement. |
| Daily Mission System | In MVP, the drill queue IS the daily mission. No separate mission generation logic needed. |
| Opponent Preparation Mode | Cool feature, clear Phase 2. |
| Voice TTS for NEON | Pro-only luxury. Text is sufficient for MVP. |
| Replay Analyzer (upload PGN) | Pro Phase 2. The sparring debrief covers this use case partially. |

**The rule:** If a feature doesn't directly contribute to the loop of *Diagnose → Practice → Measure*, it waits.

---

## PART 1 — PRODUCT SPECIFICATION

### 1. Project Overview

**Name:** NeonGambit
**Tagline:** *Your games. Your weaknesses. Eliminated.*
**Concept:** A cyberpunk chess sparring and analysis platform that turns a player's Lichess (and future Chess.com) game history into a personalized opening improvement engine.

**Target Audience:** Lichess players rated 1000–1700 who have plateaued and want to break through.

**Platform:** Next.js PWA — Mobile-First, deployable to iOS and Android via "Add to Home Screen"
**Future:** Capacitor native wrapper only if retention data shows PWA install rates are a bottleneck after 1,000+ active users. Not before.

**Architecture:** Backend-first. All business logic, game state, and move validation lives on the server. Frontend is a dumb client: renders state, captures input. Exception: Stockfish analysis during sparring runs client-side via WASM for cost and latency reasons (see ADR-002).

**Monetization:** Freemium — "Recruit" (Free) vs. "Grandmaster" (Pro) at $4.99/month or $39.99/year

---

### 2. Technical Architecture

#### A. Backend

**Framework:** FastAPI (Python 3.11+)
**Why:** Async-first, automatic Swagger/OpenAPI docs (critical for Antigravity API discovery), excellent `python-chess` integration, Pydantic V2 type safety.

**Database:**
- **Primary:** Neon (Serverless PostgreSQL)
- **Cache:** Upstash Redis (Free tier: 10k commands/day)
  - Session tokens, rate limiting
  - Opening position cache (FEN hash + ELO bucket)
  - Lichess API response caching

**ORM:** SQLAlchemy 2.0 (Async) · **Migrations:** Alembic

**AI Services:**
- **Primary:** Google Gemini 1.5 Flash (sub-second latency, generous free tier)
- **Fallback:** Hardcoded template library (see Section 5, Feature 4: NEON Coach)
- **Chess Engine — Server:** Stockfish 16 (server-side, depth capped at 15) — **only for Glitch Report generation** (async background worker)
- **Chess Engine — Client:** stockfish.wasm (browser-side) — **for real-time sparring analysis** (see ADR-002)

**Authentication:** Firebase Admin SDK (token validation) + Guest Mode (UUID in Redis, 30-day TTL)

**External APIs:**
- Lichess REST API: game history fetch (`GET /api/games/user/{username}`)
- Lichess Explorer API: opening book data (aggressively cached)
- Stripe API: subscription management

**Hosting:**
- **Application:** Hostinger KVM 1 VPS — FastAPI via PM2 + nginx reverse proxy. Always-on, no cold starts. Same VPS infrastructure already in use for Singular Mind.
- **Database:** Neon (0.5GB free tier)
- **Cache:** Upstash Redis
- **Frontend:** Vercel (free tier, auto-deploy from GitHub)
- **CDN:** Cloudflare

#### B. Frontend

**Framework:** Next.js 14 (App Router) · **Language:** TypeScript strict mode
**Styling:** Tailwind CSS + shadcn/ui · **Animations:** Framer Motion
**Chess UI:** react-chessboard · **Chess Logic:** chess.js (optimistic UI only — server validates)
**Chess Engine (client):** stockfish.wasm via Web Worker (real-time move analysis during sparring)
**State:** Zustand (flat stores — maximally legible for Antigravity agents)
**Auth:** Firebase Auth + NextAuth.js · **HTTP:** Axios with interceptors
**i18n:** next-intl (lightweight, App Router native) — English (default) + Spanish at launch
**Audio:** Howler.js · **Haptics:** Web Vibration API · **Deployment:** Vercel

#### C. Notification Strategy (MVP)

PWA push notifications on iOS are limited and unreliable. For MVP, notifications are delivered via:
- **Email:** Weekly progress digest + streak-at-risk alerts (via Resend or similar transactional email service, free tier)
- **Telegram Bot (optional Phase 1.5):** Real-time alerts for "your ELO went up" and "drill due" — opt-in via settings

Native push notifications are deferred until Capacitor wrapper is justified by user data.

---

### 3. Design System

#### Color Palette — "Cyberpunk Command Terminal" (Canonical Values)

```typescript
// lib/utils/designTokens.ts — Single source of truth. Import only from here.

export const colors = {
  // BACKGROUNDS
  void:        '#080810',   // Page background
  surface:     '#0F0F1A',   // Cards, panels
  elevated:    '#161625',   // Modals, dropdowns
  border:      '#1E1E35',   // Dividers, outlines

  // PRIMARY BRAND
  cyan:        '#00E5FF',   // Main accent — white pieces, CTAs, links
  cyanDim:     '#00A3B5',   // Hover, secondary
  cyanGlow:    'rgba(0, 229, 255, 0.15)',

  magenta:     '#E0008C',   // Opponent, destructive, black pieces
  magentaDim:  '#9A006E',
  magentaGlow: 'rgba(224, 0, 140, 0.15)',

  // ACCENT
  violet:      '#7C3AED',   // Pro tier, premium elements
  amber:       '#F59E0B',   // Warnings, out-of-book
  emerald:     '#10B981',   // Success, wins, excellent moves

  // MOVE QUALITY
  excellent:   '#10B981',
  good:        '#34D399',
  inaccuracy:  '#F59E0B',
  mistake:     '#F97316',
  blunder:     '#EF4444',

  // TEXT
  textPrimary:   '#F0F0F5',
  textSecondary: '#8B8BA0',
  textMuted:     '#4B4B65',

  // ACHIEVEMENT TIERS (Phase 2 — keep tokens defined)
  bronze:    '#CD7F32',
  silver:    '#A8A8B0',
  gold:      '#F5C518',
  platinum:  '#D0D0E0',
  neon:      '#00E5FF',
} as const;
```

**Typography:**
- **Headers / UI:** `Orbitron` (Google Fonts) — geometric, futuristic
- **Terminal / notation / coach text:** `JetBrains Mono` — professional, readable
- **Body text:** `Inter` — neutral, legible on mobile

**Visual FX:**

| Effect | Trigger | Feel |
|--------|---------|------|
| Blunder Glitch | Blunder detected | 200ms chromatic aberration on board — the position "breaks" |
| Excellent Pulse | Excellent move | Cyan glow emanating from moved piece — satisfying validation |
| Capture Burst | Any capture | Neon particle explosion from target square |
| Coach Typewriter | NEON new message | Text appears letter-by-letter with blinking cursor |
| Out-of-Book Flash | Opponent off theory | Full-screen amber tint, banner materializes |
| Glassmorphism | All cards/panels | `backdrop-blur bg-white/5 border border-white/10` |
| Scanlines | NEON terminal | CSS `repeating-linear-gradient` overlay — CRT monitor feel |

---

### 4. Monetization

**Core strategy:** The Glitch Report is fully visible in Free tier. The user *sees* all their weaknesses. Pro unlocks the depth of *fixing* them.

| Feature | Free — "Recruit" | Pro — "Grandmaster" |
|---------|-----------------|---------------------|
| **Lichess Sync** | Last 20 games | Last 200 games (full history) |
| **Glitch Report** | **Full diagnostic — all critical openings visible** | Full diagnostic + regenerate on demand |
| **Repertoire Sparring** | 2 openings (NEON-assigned from Glitch Report) | Unlimited openings |
| **Opponent Depth** | 10 moves theory | 20+ moves theory |
| **NEON Coach** | Text only, 3 analyses/day | Unlimited analyses |
| **Neural Drill** | 5 positions/day | Unlimited + custom positions |
| **Session Debrief** | Summary only (accuracy + theory integrity) | Move-by-move with NEON narration (Phase 2) |
| **Retry from Position** | — | Retry any blunder position mid-game |
| **Stockfish Deep Analysis** | 1 per game (client-side WASM) | Unlimited |
| **Game History** | Last 10 sessions | Unlimited + export PGN |
| **Price** | Free | **$4.99/month · $39.99/year** |

**Upgrade triggers (natural, not intrusive):**
- Lichess sync reaches 20-game limit → "You have 847 more games. Unlock your full pattern history."
- Glitch Report shows all critical openings → user taps "DRILL THIS NOW" on the 3rd opening → "Recruit tier includes 2 openings. Unlock this one?"
- Neural Drill daily limit reached → "Your next due review is Ruy Lopez move 8. See it tomorrow or unlock now."
- After a sparring blunder → "Retry from this position? [Pro feature]" — the highest-intent moment

**Why the Glitch Report is fully free:** This is the product's "aha" moment. Gating it behind a paywall kills the emotional hook. A user who sees *all* their weaknesses but can only train 2 of them is a user who *knows exactly what they're paying for* when they upgrade. That's the highest-converting paywall design: show the full problem, gate the full solution.

---

### 5. Feature Specifications (MVP Scope)

---

#### FEATURE 1: Lichess Game Import & The Glitch Report

**This is the product's core hook. Everything else extends from it.**

**Concept:** The first time a user connects their Lichess account, NeonGambit analyzes their game history and produces a "Glitch Report" — a personalized map of where they keep losing, why, and what to do about it. This report should feel revelatory: *"It knows exactly what my problem is."*

**User flow:**
1. Prompted after guest session's first game: "Connect Lichess to discover why you keep losing the same games."
2. User enters Lichess username. Backend fetches last 20 games (free) or 200 games (Pro).
3. Processing screen: "Scanning your game history... Identifying patterns..."
4. Glitch Report generates. Full-screen reveal moment.

**Fallback for users without Lichess (or with <20 games):**
If the user has no Lichess account or fewer than 20 games, the Glitch Report cannot generate meaningfully. Instead:
- Prompt: "Play 5 sparring games here and we'll generate your first report."
- After 5 completed sessions, generate a mini Glitch Report from NeonGambit session data only (ECO codes played, accuracy per opening, blunder patterns).
- This expands the acquisition funnel to users who are new to Lichess or use Chess.com (where API access is pending).

**What the Glitch Report shows:**

```
┌──────────────────────────────────────────────────────────┐
│  ⚡ GLITCH REPORT — @your_username                        │
│  Analyzed 47 games · Rapid 1340 ELO                      │
├──────────────────────────────────────────────────────────┤
│  ── CRITICAL VULNERABILITIES ──────────────────────────  │
│                                                          │
│  🔴 SICILIAN DEFENSE (B70)                               │
│     22% win rate · 18 games · You lose in 12 moves avg  │
│     Collapse type: TACTICAL BLUNDER (11 of 18 games)    │
│     "You reach a good position then drop material on    │
│      move 9. Undefended pieces — same pattern, 4 games."│
│     [▶ DRILL THIS NOW]                                   │
│                                                          │
│  🟠 RUY LOPEZ — Berlin (C67)                             │
│     31% win rate · 13 games · Avg loss on move 14       │
│     Collapse type: POSITIONAL DRIFT (8 of 13 games)     │
│     "No single blunder — you lose the thread after       │
│      move 10. The middlegame demands a plan."            │
│     [▶ PRACTICE DEVIATIONS]                              │
│                                                          │
│  🟡 QUEEN'S GAMBIT ACCEPTED (D20)                        │
│     35% win rate · 9 games · Avg loss on move 11        │
│     Collapse type: OPENING ERROR (6 of 9 games)         │
│     "You go off-book at move 8 and the center collapses."│
│     [🔒 UNLOCK — Pro]                                    │
│                                                          │
│  ── STRENGTHS TO BUILD ON ─────────────────────────────  │
│  ✅ Italian Game: 67% · 15 games — Keep playing this     │
│  ✅ Queen's Gambit declined: 58% · 8 games               │
│                                                          │
│  ── YOUR PATTERN ──────────────────────────────────────  │
│  "You play well through move 8-10, then lose direction.  │
│   The opening is not your problem. The transition to     │
│   middlegame is. Sparring past move 10 will fix this."   │
└──────────────────────────────────────────────────────────┘
```

**Note on Free tier:** All critical openings are visible with full stats and NEON diagnosis. The lock icon appears only on the "DRILL THIS NOW" CTA for openings beyond the 2 included in Free tier. The user sees the full picture; Pro unlocks the full training.

**Backend logic (`lichess_analyzer.py`):**
1. Fetch games from `GET https://lichess.org/api/games/user/{username}?max=200&opening=true&pgnInJson=true`
2. Extract per game: `opening.eco`, `opening.name`, `winner`, `moves` (PGN), `lastMoveAt`
3. Aggregate by ECO code: win rate, avg game length when losing, deviation move number
4. Identify "collapse move" — avg move number when the position evaluation swings decisively (via Stockfish analysis on a sample of 5 worst games — **server-side only**)
5. **Classify collapse type** for each collapse move. This is critical — the Glitch Report must tell the user not just *where* they collapse but *why*. Classification uses Stockfish eval + position features at the collapse moment:
   - **`opening_error`** — collapse move is within the opening's `starting_moves` range AND the played move deviates from theory (move not in top-3 Explorer moves for this position). *"You went off-book at move 7 and the position fell apart."*
   - **`tactical_blunder`** — collapse move causes a material swing ≥ 1.5 pawns in a single move AND a concrete tactic existed (fork, pin, skewer, discovered attack, hanging piece). Detected by comparing eval_before vs eval_after on the collapse move. *"You left your knight undefended on d4 — that's a pattern. It happened in 4 of your 18 Sicilian games."*
   - **`positional_drift`** — collapse is gradual: no single move loses ≥ 1.5 pawns, but eval drifts from ~0.0 to ≤ -1.5 over 3-5 moves. This signals aimless play or plan breakdown in the middlegame transition. *"No single blunder, but you lost the thread between moves 9-13. The position demanded a plan and you moved without one."*
   - **`time_pressure`** — collapse move occurs when the game's move timestamps (available in Lichess PGN) show the user had <20% of their time remaining. *"This wasn't a chess mistake — you ran out of time. Your Sicilian games average 4 minutes of think time on moves 7-10."*
   - For each critical opening in the report, the dominant collapse type (most frequent across sampled games) is included alongside the neon_diagnosis. This allows NEON to tailor the narrative and, crucially, connect the user's pattern to the correct training approach.
6. Send structured data to Gemini for narrative generation (neon_diagnosis + overall_pattern). The collapse type classification is included in the Gemini prompt so the narrative addresses the actual root cause, not just the symptom.
7. Cache full report in `glitch_reports` table. Invalidate on next sync.

**Lichess API resilience — degraded mode:**
If the Lichess API is unavailable (rate-limited, down, or token revoked):
- Display cached Glitch Report if one exists: "Last synced 3 days ago. Lichess is temporarily unavailable."
- All sparring, drill, and session features continue to work normally using already-imported data.
- Queue a background retry every 15 minutes (max 8 retries, then stop until next user-initiated sync).
- Never show an error screen that blocks the user from training.

**Emotional design note:** The Glitch Report reveal must feel like a plot twist. Dark background, data loads in line by line, the critical openings appear with a red warning flash. The user should feel seen.

---

#### FEATURE 2: Repertoire Sparring ("The Arena")

**Concept:** Practice your openings against an opponent that plays like a real human at your ELO — not a perfect engine. After the opening phase, NEON guides you through the middlegame transition (the most common failure point).

**What makes the opponent feel human:**
- Move selection is probabilistic, weighted by Lichess Explorer frequency at the user's ELO bucket
- Thinking time is randomized (600–2500ms) and scales inversely with move popularity (common moves come faster)
- The opponent makes statistically realistic mistakes — not engine-perfect play
- When the opponent plays an "inaccuracy" (by engine standards), NEON notes it: "Your opponent just weakened their kingside. Do you see it?"

**MVP repertoire assignment (no manual builder):**
Instead of a full browse-and-select Repertoire Builder, MVP assigns openings automatically:
- After Glitch Report generates: the top 2 critical openings (worst win rate with sufficient sample) are auto-added to the user's repertoire for Free tier.
- Pro users get all critical openings auto-added + can request additional openings via a simple search/add interface (not the full Builder).
- "Let NeonGambit pick" is the default and only option in MVP. Manual repertoire building is Phase 2.

**The Arena experience — moment by moment:**

*Before the game:*
- User selects from their assigned openings (2 for Free, all critical for Pro)
- Selects opponent ELO (800 / 1000 / 1200 / 1400 / 1600 / 1800)
- Selects color
- Optionally: "Let NeonGambit pick — train your weakest opening"

*During the game:*
- **Theory Integrity Bar** at top: starts at 100%, drains on deviations. Visual pressure to stay in book.
- **Move 8+ Transition Alert:** When theory runs out, NEON announces: "You're out of book. This is where you usually struggle. Focus." This is the key teaching moment — the transition to middlegame the user chronically misplays.
- **NEON Terminal** (bottom): brief coaching after each significant move. Not every move — only when something meaningful happened.
- **Opponent "Off-Book" Detection:** If opponent deviates, Survival Mode activates (amber HUD shift). NEON: "Non-standard move. Don't panic. What's the threat?"
- **Client-side Stockfish (WASM):** Move quality evaluation runs in the browser via Web Worker. The server receives the move, validates legality, updates game state, and returns the opponent's response. The client independently evaluates move quality for display purposes. See ADR-002.

*After a blunder:*
- Chromatic aberration glitch effect on board
- NEON explains in <20 words, ELO-calibrated
- "Retry from this position" button (Pro only) — the most powerful learning feature

*End of game:*
- Session summary card: accuracy, theory integrity, move quality breakdown
- "Your opening was solid through move 10. The middlegame transition cost you." — specific, actionable
- [Practice this position again] [Move to next opening]

---

#### FEATURE 3: Neural Drill System — Move-Level Spaced Repetition

**Concept:** Each theoretical move in each opening is a "memory card." The system tracks which exact moves you forget and resurfaces them at the optimal interval using the SM-2 algorithm. Not "practice this opening." "Practice move 9 of the Ruy Lopez Berlin where you keep going wrong."

**Key UX principle:** The drill must feel like quick practice, not homework. Sessions should complete in 5–7 minutes.

**Drill flow:**

1. Board appears at the position BEFORE the move to learn
2. NEON: "What's the correct move here?" (no pressure, no timer)
3. If user plays correctly → brief cyan flash + "Calculated." → next card
4. If user hesitates >5s → "Shadow Move" appears: ghost of the correct piece target
5. If user plays wrong → board resets, correct move plays automatically, NEON explains in 1 sentence
6. SM-2 updates: correct = interval doubles; wrong = resets to 1 day

**The Queue screen:**
- "7 moves due today" displayed like a task list
- Each card shows: Opening name, move number, days since last review
- Estimated time: "~6 minutes"
- Completing the full queue earns a streak day increment

**Why this beats Chessable:** No review debt spiral. The queue is capped. Free tier users see 5 cards/day max — enough to maintain without overwhelming. Pro users get unlimited + they can create custom cards from positions in their own sparring sessions.

**In MVP, the drill queue IS the daily mission.** No separate mission system. The dashboard shows: "7 moves due today · ~6 min" with a start button. That's it.

---

#### FEATURE 4: NEON — The Coaching Persona

**NEON is not a chatbot. NEON is a character.**

NEON is an AI chess entity that lives in the system. Direct, efficient, slightly cryptic. Like a grandmaster who's also a hacker. Never condescending. Never sycophantic. Always useful.

**NEON's voice rules:**
- Under 20 words for in-game coaching (text display)
- Under 40 words for post-game review narration
- Uses cyberpunk terminology sparingly and naturally: "calculated," "glitch," "system error," "the grid"
- Never says "good job" generically. Either names the specific achievement or says nothing.
- When ELO is low (1000–1200): tactical, immediate, concrete. "Your knight is hanging. Move it."
- When ELO is higher (1500–1700): strategic, layered. "That square on d5 will be dominated for the rest of the game."
- On excellent moves: brief but specific praise. "Clean. You created two threats simultaneously."
- On blunders: names the consequence, not the shame. "That gives them a passed pawn. Difficult to stop from here."

**Implementation — Template-First Architecture (80/20 rule):**

To ensure tone consistency, reduce LLM costs, and eliminate the risk of NEON giving tactically incorrect advice during sparring:

**80% Template Library (in-game coaching):**
A curated library of ~200 pre-written NEON messages, mapped to specific patterns:
- Move quality (blunder / mistake / inaccuracy / excellent) × tactical pattern (hanging piece, fork, pin, discovered attack, pawn structure, tempo loss, etc.)
- Each template has ELO-adaptive variants: low (1000–1200), mid (1200–1500), high (1500–1700)
- Templates are stored in a JSON/YAML file, loaded at startup, selected by pattern matching on the Stockfish evaluation + position features

**Critical design rule — Tactical Pattern Naming:**
Research (Pain #1 in the user research report) shows that the #1 blocker for sub-1800 players is tactical inconsistency: they solve puzzles but can't transfer pattern recognition to real games. The fix is *contextual pattern naming* — NEON doesn't just say what went wrong, it names the tactical pattern and tells the user where to look for it again. Every blunder/mistake template MUST follow this structure:

1. **Name the consequence** (what happened to the position)
2. **Name the pattern** (the tactical or positional concept)
3. **Plant a forward-looking seed** (when to watch for this pattern again)

This turns every sparring blunder into a micro-lesson that builds tactical vocabulary in context — exactly what puzzles alone fail to do.

Example template entries:
```yaml
# === BLUNDERS — consequence + pattern name + forward seed ===

blunder_hanging_piece:
  low: "Your {piece} on {square} is undefended. That's a hanging piece — scan for undefended pieces before every move."
  mid: "Leaving {piece} on {square} drops material. Hanging piece pattern. {best_move} keeps it protected. After every trade, recheck what's left undefended."
  high: "That {piece} was overloaded — defending {square1} and covering {square2}. Overloaded piece motif. When one piece has two jobs, your opponent only needs one move to exploit it."

blunder_fork:
  low: "Their {piece} attacks two of your pieces at once. That's a fork — watch for knight jumps to squares that touch multiple targets."
  mid: "Fork on {square}. Your {target1} and {target2} are both hit. This pattern appears when pieces cluster on the same rank or around the king."
  high: "Classic fork geometry. The {square} square was available because you left {target1} on {file}. In positions with knights in the center, always ask: can it jump to a double-attack square?"

blunder_pin:
  low: "Your {piece} can't move — it's pinned to your {valuable_piece}. Pins happen when pieces line up. Watch for enemy bishops and rooks aiming through your pieces."
  mid: "Absolute pin on the {file} file. Your {piece} is frozen. Before developing, check if any piece will land on a line between your king and an enemy long-range piece."
  high: "That pin was avoidable. The {file}-file alignment was visible two moves ago. In these structures, prophylactic moves like {escape_move} break the pin geometry before it activates."

blunder_discovered_attack:
  low: "They moved one piece and attacked with another behind it. That's a discovered attack — two threats from one move."
  mid: "Discovered attack. The {moving_piece} unmasked {attacking_piece} onto your {target}. This pattern shows up when a piece moves off a file, rank, or diagonal that a friendly piece was already aiming down."
  high: "The discovery was set up two moves ago when {attacking_piece} landed on {setup_square}. In open positions with aligned long-range pieces, every move that steps off the alignment is a potential discovery. Catalog those lines."

# === EXCELLENT MOVES — reinforce the pattern they used ===

excellent_double_threat:
  low: "Nice. Two threats at once — they can't stop both. That's a double attack. Look for these whenever your opponent's pieces are on the same rank or diagonal."
  mid: "Clean. Fork on {square} hits both {target1} and {target2}. You spotted the geometry. This pattern recurs in positions with centralized knights."
  high: "Dual-purpose. That creates problems on the {side} while improving your {piece}. You provoked the tactic by first creating the conditions. That's the difference between finding tactics and creating them."

excellent_pin_exploitation:
  low: "Good eye. You used the pin to win material. Pins are everywhere — keep scanning for them."
  mid: "You exploited the pin on {file}. When your opponent leaves pieces aligned with their king, that's your signal."
  high: "Textbook pin exploitation. You first restricted the pinned piece's escape squares, then increased pressure. That sequencing is what separates strong execution from lucky tactics."

# === POSITIONAL / STRUCTURAL ===

mistake_tempo_loss:
  low: "You moved the same piece twice in the opening. That's a lost tempo — they developed a new piece while you shuffled."
  mid: "Tempo loss. Moving {piece} to {square1} then {square2} gave your opponent a free developing move. In the opening, every move should bring a new piece into the game."
  high: "That tempo concession shifted the initiative. In these structures, the extra move lets them execute {threat_type} before you're castled. Tempo discipline in the opening is non-negotiable."

mistake_positional_drift:
  low: "No single bad move, but you lost direction in the last 3 moves. Every move needs a purpose — even a small one."
  mid: "Positional drift. Your last 3 moves didn't improve anything. When you're out of book, ask: what is my worst-placed piece? Improve that one."
  high: "The position demanded a concrete plan and you temporized. In this structure, the standard plan is {plan_description}. Without a plan, even equal positions decay."

# === THEORY / SURVIVAL ===

theory_exit:
  all: "You're off-book at move {move}. This is your critical zone. What's the plan?"

survival_mode:
  all: "Non-standard move. Don't panic. What's the threat?"

tilt_intervention:
  all: "Three losses in {minutes} minutes. The position data looks fine. This is a pattern issue, not a knowledge issue. Switch to Drill mode — let it reset."
```

**20% Gemini (narrative generation):**
LLM is used only for:
- Glitch Report narrative (neon_diagnosis per opening + overall_pattern) — one-time generation, cached. The collapse type classification is included in the Gemini prompt so the narrative addresses the root cause (tactical blunder vs positional drift vs opening error).
- Post-session summary narrative (1 call per session end, not per move)
- The user never waits for an LLM call during gameplay. All in-game coaching is template-driven and instant.

**Fallback chain:** Template match → Gemini 1.5 Flash → Generic fallback ("System processing. Review this position after the game.")

---

#### FEATURE 5: Tilt Detection

**Logic (in `user_stats`):**
- Track: `consecutive_sparring_losses INT DEFAULT 0`, `last_sparring_loss_at TIMESTAMP`
- After each sparring session loss: increment counter, update timestamp
- After each sparring session win or draw: reset to 0
- If `consecutive_losses >= 3` AND `time_since_first_loss < 25 minutes`: set `tilt_detected = true`

**NEON intervention (shown before "Play Again" button renders):**

```
> NEON: "Three losses in 22 minutes. The position data looks fine.
  This is a pattern issue, not a knowledge issue.
  Switch to Drill mode — let it reset.
  [▶ GO TO DRILL]    [Play anyway]"
```

- Not a hard block. User can always bypass.
- NEON speaks first, then the Play Again button appears.
- Counter resets on any non-loss session or after 2 hours.

---

#### FEATURE 6: Authentication — "Play First, Understand Later"

**Philosophy:** Zero friction to enter. Maximum motivation to stay.

**Flow:**
1. App opens → no login screen. Guest session created automatically.
2. User plays one game with NEON.
3. Post-game: "Connect your Lichess account to see why you keep losing the same openings." This prompt appears at the moment of highest motivation — right after a loss or a close game.
4. User enters Lichess username (no password needed — read-only public API).
5. Glitch Report generates. User is now invested.
6. Account creation (email/Google/Apple) is triggered only when user wants to save progress or subscribe.

**Fallback for no-Lichess users:**
- If user skips Lichess connection or has no account: allow unlimited guest sparring.
- After 5 completed sessions: "You've played enough games for NeonGambit to analyze your patterns. [Generate My Report]"
- Mini Glitch Report generates from NeonGambit session data only.
- Lichess connection remains available for deeper analysis at any time.

**Token security:**
- Guests: `sessionStorage` (cleared on tab close)
- Authenticated users: httpOnly cookie via Next.js API route
- Lichess username: stored in DB — no OAuth needed (public API is read-only)

---

#### FEATURE 7: ELO Progress Tracking & Mission Control Dashboard

**The most important psychological feature in the product.**

**Concept:** Users don't improve at NeonGambit — they improve at chess, and NeonGambit shows them the evidence. The product must close the loop between training sessions and real Lichess results.

**The "Mission Control" dashboard shows (MVP — lightweight version):**

```
┌──────────────────────────────────────────────────────────┐
│  MISSION CONTROL                                          │
├──────────────────────────────────────────────────────────┤
│  📡 LICHESS SYNC — @username                              │
│  Current Rating: 1,387 (+47 this month) 📈                │
│  Last synced: 2 hours ago                                 │
│                                                          │
│  ── TODAY'S DRILL ───────────────────────────────────────│
│  7 moves due · Est. 6 min                                │
│  [▶ START DRILL]                                         │
│                                                          │
│  ── THIS WEEK ─────────────────────────────────────────  │
│  Sessions: 6 · Moves drilled: 84                         │
│  Openings improved: Sicilian 22%→41% ✅                  │
│  Streak: 5 days 🔥                                       │
│                                                          │
│  ── RECOMMENDED SESSION ─────────────────────────────────│
│  Sparring: Sicilian Defense at 1400 ELO                  │
│  "Your weakest opening this week"                        │
│  [▶ START SPARRING]                                      │
└──────────────────────────────────────────────────────────┘
```

**Technical implementation:**
- Periodic Lichess sync (on app open + manual trigger): fetch last 20 games, update `lichess_sync_history` table
- Track win rate per opening over time (compare to Glitch Report baseline)
- When a "critical" opening from the original Glitch Report shows win rate improvement, surface it in the dashboard: "Sicilian win rate: 22% → 41% ✅"
- Email notification (weekly digest): "Your Lichess rating went up 47 points this month. Here's what improved."

**Why this creates retention:** The moment a user sees their Lichess rating go up and makes the connection to NeonGambit training, they become loyal. This loop closure is the entire business. It must be prominent, beautiful, and emotionally resonant.

---

### 6. Database Schema (Neon PostgreSQL)

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- USERS
-- ============================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE,
    firebase_uid TEXT UNIQUE,
    guest_token TEXT UNIQUE,
    lichess_username TEXT,           -- No password — read-only public API
    target_elo INT DEFAULT 1200,
    play_style TEXT,                 -- 'tactical' | 'positional' | 'unknown'
    is_pro BOOLEAN DEFAULT FALSE,
    pro_expires_at TIMESTAMP,
    preferred_language TEXT DEFAULT 'en' CHECK (preferred_language IN ('en', 'es')),
    created_at TIMESTAMP DEFAULT NOW(),
    last_active_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT valid_elo CHECK (target_elo BETWEEN 800 AND 3000)
);

CREATE INDEX idx_users_firebase ON users(firebase_uid);
CREATE INDEX idx_users_guest ON users(guest_token);
CREATE INDEX idx_users_lichess ON users(lichess_username);

-- ============================================
-- OPENINGS (Curated Library)
-- ============================================
CREATE TABLE openings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL UNIQUE,          -- "Sicilian Defense: Dragon Variation"
    eco_code TEXT NOT NULL,             -- "B70"
    starting_fen TEXT NOT NULL,
    starting_moves TEXT[] NOT NULL,     -- ["e4", "c5", "Nf3"]
    tier TEXT NOT NULL CHECK (tier IN ('free', 'pro')),
    play_style TEXT NOT NULL CHECK (play_style IN ('tactical', 'positional', 'both')),
    popularity_rank INT,
    description TEXT,
    color TEXT NOT NULL CHECK (color IN ('white', 'black', 'both')),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_openings_tier ON openings(tier);
CREATE INDEX idx_openings_eco ON openings(eco_code);

-- ============================================
-- USER REPERTOIRE
-- ============================================
CREATE TABLE user_repertoire (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    opening_id UUID REFERENCES openings(id) ON DELETE CASCADE,
    added_at TIMESTAMP DEFAULT NOW(),
    target_depth INT DEFAULT 12,        -- How many moves deep to train
    is_active BOOLEAN DEFAULT TRUE,
    source TEXT DEFAULT 'glitch_report' CHECK (source IN ('glitch_report', 'manual', 'recommended')),
    PRIMARY KEY (user_id, opening_id)
);

-- ============================================
-- LICHESS GAME IMPORTS
-- ============================================
CREATE TABLE lichess_games (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    lichess_game_id TEXT NOT NULL,      -- Lichess native ID
    eco_code TEXT,
    opening_name TEXT,
    result TEXT CHECK (result IN ('win', 'loss', 'draw')),
    user_color TEXT CHECK (user_color IN ('white', 'black')),
    opponent_rating INT,
    user_rating_at_time INT,
    move_count INT,
    pgn TEXT,                           -- Full PGN for replay analysis
    deviation_move INT,                 -- Move where user deviated from their repertoire
    collapse_move INT,                  -- Move where eval swung decisively against user
    played_at TIMESTAMP,
    imported_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (user_id, lichess_game_id)
);

CREATE INDEX idx_lichess_games_user ON lichess_games(user_id);
CREATE INDEX idx_lichess_games_eco ON lichess_games(user_id, eco_code);
CREATE INDEX idx_lichess_games_played ON lichess_games(user_id, played_at DESC);

-- ============================================
-- GLITCH REPORTS (Diagnostic Analysis)
-- ============================================
CREATE TABLE glitch_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    generated_at TIMESTAMP DEFAULT NOW(),
    games_analyzed INT NOT NULL,
    rating_at_generation INT,
    source TEXT DEFAULT 'lichess' CHECK (source IN ('lichess', 'sessions')),

    -- Structured findings (JSONB for flexibility)
    critical_openings JSONB NOT NULL DEFAULT '[]',
    -- [{eco_code, opening_name, games, wins, losses, win_rate, avg_collapse_move,
    --   collapse_type ('opening_error'|'tactical_blunder'|'positional_drift'|'time_pressure'),
    --   neon_diagnosis, is_critical: bool, linked_opening_id}]

    strengths JSONB NOT NULL DEFAULT '[]',
    -- [{eco_code, opening_name, games, win_rate}]

    overall_pattern TEXT,               -- NEON's 2-sentence narrative summary
    is_current BOOLEAN DEFAULT TRUE,    -- Only one current report per user
    UNIQUE (user_id, is_current)        -- Enforced via partial index
);

CREATE UNIQUE INDEX idx_glitch_current ON glitch_reports(user_id) WHERE is_current = TRUE;

-- ============================================
-- LICHESS RATING HISTORY (for loop closure)
-- ============================================
CREATE TABLE lichess_rating_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    lichess_username TEXT NOT NULL,
    rating INT NOT NULL,
    rating_type TEXT DEFAULT 'rapid',   -- 'bullet' | 'blitz' | 'rapid' | 'classical'
    snapshotted_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_ratings_user ON lichess_rating_snapshots(user_id, snapshotted_at DESC);

-- ============================================
-- SPARRING SESSIONS (Games played in NeonGambit)
-- ============================================
CREATE TABLE sparring_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    opening_id UUID REFERENCES openings(id),
    player_color TEXT NOT NULL CHECK (player_color IN ('white', 'black')),
    opponent_elo INT NOT NULL,
    current_fen TEXT NOT NULL,
    move_history JSONB NOT NULL DEFAULT '[]',
    -- [{move, from, to, san, quality, eval_cp, timestamp}]
    accuracy_score FLOAT DEFAULT 100.0,
    theory_integrity FLOAT DEFAULT 100.0,
    theory_exit_move INT,               -- Move number where user left book
    excellent_moves INT DEFAULT 0,
    good_moves INT DEFAULT 0,
    inaccuracies INT DEFAULT 0,
    mistakes INT DEFAULT 0,
    blunders INT DEFAULT 0,
    session_status TEXT DEFAULT 'active' CHECK (session_status IN ('active', 'completed', 'abandoned')),
    result TEXT CHECK (result IN ('win', 'loss', 'draw', NULL)),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    CONSTRAINT valid_accuracy CHECK (accuracy_score >= 0 AND accuracy_score <= 100)
);

CREATE INDEX idx_sessions_user ON sparring_sessions(user_id);
CREATE INDEX idx_sessions_status ON sparring_sessions(session_status);
CREATE INDEX idx_sessions_opening ON sparring_sessions(user_id, opening_id);

-- ============================================
-- OPENING BOOK CACHE (Self-building from Lichess Explorer)
-- ============================================
CREATE TABLE opening_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    fen_hash TEXT NOT NULL,
    fen TEXT NOT NULL,
    elo_bucket INT NOT NULL,            -- Rounded to nearest 200 (1200, 1400...)
    candidate_moves JSONB NOT NULL,
    -- [{move, uci, san, white_wins, draws, black_wins, probability}]
    total_games INT NOT NULL,
    last_updated TIMESTAMP DEFAULT NOW(),
    cache_hits INT DEFAULT 0,
    UNIQUE(fen_hash, elo_bucket)
);

CREATE INDEX idx_cache_fen_elo ON opening_cache(fen_hash, elo_bucket);

-- ============================================
-- AI COACH LOG
-- ============================================
CREATE TABLE coach_analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES sparring_sessions(id) ON DELETE CASCADE,
    move_number INT NOT NULL,
    fen_before TEXT NOT NULL,
    user_move TEXT NOT NULL,
    move_quality TEXT NOT NULL CHECK (move_quality IN ('excellent', 'good', 'inaccuracy', 'mistake', 'blunder')),
    coach_text TEXT NOT NULL,           -- Display text (<20 words)
    eval_before FLOAT,
    eval_after FLOAT,
    source TEXT DEFAULT 'template' CHECK (source IN ('template', 'gemini', 'fallback')),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_analyses_session ON coach_analyses(session_id);

-- ============================================
-- NEURAL DRILL — SPACED REPETITION
-- ============================================
CREATE TABLE user_move_mastery (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    opening_id UUID REFERENCES openings(id) ON DELETE CASCADE,
    move_sequence_hash TEXT NOT NULL,   -- MD5 of move sequence to this position
    move_number INT NOT NULL,
    expected_move TEXT NOT NULL,        -- SAN notation
    fen_before TEXT NOT NULL,
    easiness_factor FLOAT DEFAULT 2.5,  -- SM-2
    interval_days INT DEFAULT 0,
    repetitions INT DEFAULT 0,
    next_review TIMESTAMP DEFAULT NOW(),
    last_reviewed TIMESTAMP,
    correct_count INT DEFAULT 0,
    incorrect_count INT DEFAULT 0,
    PRIMARY KEY (user_id, move_sequence_hash)
);

CREATE INDEX idx_mastery_due ON user_move_mastery(user_id, next_review);

-- ============================================
-- USER STATISTICS (Aggregated)
-- ============================================
CREATE TABLE user_stats (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    total_sparring_sessions INT DEFAULT 0,
    total_moves_made INT DEFAULT 0,
    sparring_wins INT DEFAULT 0,
    sparring_losses INT DEFAULT 0,
    sparring_draws INT DEFAULT 0,
    average_accuracy FLOAT DEFAULT 0,
    peak_accuracy FLOAT DEFAULT 0,
    current_streak INT DEFAULT 0,
    longest_streak INT DEFAULT 0,
    last_session_date DATE,
    total_drill_cards_reviewed INT DEFAULT 0,
    -- Opening-level aggregates (keyed by ECO code)
    opening_stats JSONB DEFAULT '{}',
    -- {"B70": {sessions: 10, wins: 4, avg_accuracy: 74.2, avg_theory_exit_move: 9}}
    -- Tilt tracking
    consecutive_sparring_losses INT DEFAULT 0,
    last_sparring_loss_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- SUBSCRIPTIONS
-- ============================================
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    stripe_subscription_id TEXT UNIQUE,
    status TEXT NOT NULL CHECK (status IN ('active', 'canceled', 'expired', 'past_due')),
    plan TEXT NOT NULL CHECK (plan IN ('monthly', 'yearly')),
    current_period_start TIMESTAMP NOT NULL,
    current_period_end TIMESTAMP NOT NULL,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_subs_user ON subscriptions(user_id);
CREATE INDEX idx_subs_stripe ON subscriptions(stripe_subscription_id);

-- ============================================
-- TRIGGERS
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER sessions_updated_at BEFORE UPDATE ON sparring_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER stats_updated_at BEFORE UPDATE ON user_stats
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

**Phase 2 tables (not created in MVP):** `conversion_failures`, `endgame_drill_cards`, `achievements`, `user_achievements`.

---

### 7. API Specification

**Base URL:** `https://api.neongambit.com/v1`
**Auth:** `Authorization: Bearer <JWT>` on all endpoints except `/auth/guest` and `/auth/validate`

#### MVP Endpoint Registry

```
Authentication
├── POST   /auth/guest              # Create anonymous session
├── POST   /auth/validate           # Validate Firebase token
└── POST   /auth/link-account       # Link guest → Firebase user

User & Profile
├── GET    /user/profile            # Get full user profile
├── PATCH  /user/profile            # Update username, target_elo, lichess_username
└── GET    /user/lichess-rating     # Fetch current Lichess rating (live)

Lichess Integration
├── POST   /lichess/import          # Import games (triggers async job)
├── GET    /lichess/import/status   # Check import job status
└── GET    /lichess/games           # List imported games (paginated)

Glitch Report
├── POST   /glitch-report/generate  # Generate or regenerate report (async)
└── GET    /glitch-report/current   # Get current Glitch Report

Repertoire (MVP — simplified)
├── GET    /repertoire              # User's active repertoire (auto-assigned)
└── POST   /repertoire              # Add opening to repertoire (Pro: manual add)

Sparring Sessions
├── POST   /sessions                # Create new sparring session
├── GET    /sessions/{id}           # Get session state
├── POST   /sessions/{id}/moves     # Submit user move (server validates)
├── POST   /sessions/{id}/opponent-move  # Request opponent's response
├── POST   /sessions/{id}/resign    # End session
└── GET    /sessions/history        # Paginated session history

Neural Drill
├── GET    /drill/queue             # Today's due moves
├── GET    /drill/queue/count       # Count due (for dashboard badge)
├── POST   /drill/review            # Record result + update SM-2
└── GET    /drill/mastery/{opening_id}  # Per-opening mastery progress

Tilt Detection
└── GET    /user/tilt-status        # {tilt_detected: bool, consecutive_losses: int}

Analytics & Dashboard
├── GET    /analytics/dashboard     # All dashboard data in one call
└── GET    /analytics/rating-trend  # Lichess rating over time

Subscriptions
├── POST   /subscriptions/checkout  # Stripe checkout session
├── POST   /webhooks/stripe         # Stripe events (raw body + signature)
└── GET    /subscriptions/status    # Current subscription status
```

**Phase 2 endpoints (not implemented in MVP):**
- `/glitch-report/history`, `/sessions/{id}/review` (full debrief), `/sessions/{id}/analyze`, `/sessions/{id}/hint`
- `/endgame/*` (all conversion failure + endgame drill endpoints)
- `/mission/*` (daily mission system)
- `/achievements/*` (achievement system)
- `/analytics/opening-performance`, `/analytics/theory-depth`, `/analytics/weekly-summary`
- `/drill/custom` (custom position creation)
- `/openings`, `/openings/{id}` (full browse)

#### Key Contracts

**POST /sessions (Create sparring session)**
```json
Request:
{
  "opening_id": "uuid",
  "player_color": "white",
  "opponent_elo": 1400
}

Response:
{
  "session_id": "uuid",
  "current_fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "player_color": "white",
  "opponent_elo": 1400,
  "opening_name": "Sicilian Defense: Dragon Variation",
  "theory_integrity": 100.0,
  "neon_intro": "Sicilian Dragon. Your win rate here is 22%. Let's change that."
}
```

**POST /sessions/{id}/moves**
```json
Request:
{ "from": "e2", "to": "e4", "promotion": null }

Response (valid move):
{
  "valid": true,
  "new_fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
  "theory_integrity": 100.0,
  "theory_exit_detected": false,
  "out_of_book": false,
  "coach_message": null
}

Response (user exits theory):
{
  "valid": true,
  "new_fen": "...",
  "theory_integrity": 82.0,
  "theory_exit_detected": true,
  "theory_exit_move": 9,
  "coach_message": "You're off-book at move 9. This is your critical zone. What's the plan?"
}

Response (illegal move):
{
  "valid": false,
  "error": "Illegal move: e2 to e5",
  "legal_moves": ["e2e3", "e2e4", "g1f3"]
}
```

**Note on move quality:** In MVP, move quality evaluation (`excellent`, `good`, `inaccuracy`, `mistake`, `blunder`) is computed client-side via stockfish.wasm and displayed locally. The server does NOT run Stockfish per move during sparring. The server only validates legality, tracks theory integrity, and returns the opponent's probabilistic response. This is the key cost optimization of ADR-002.

The client sends a lightweight `move_quality` field back to the server on the *next* move (or session end) for stats tracking:
```json
POST /sessions/{id}/moves
{
  "from": "e2", "to": "e4", "promotion": null,
  "prev_move_quality": "blunder",
  "prev_move_eval_cp": -185
}
```

**POST /lichess/import**
```json
Request:
{ "lichess_username": "your_username", "max_games": 50 }

Response:
{
  "job_id": "uuid",
  "status": "processing",
  "estimated_seconds": 15,
  "message": "Fetching your games from Lichess..."
}
```

**GET /glitch-report/current**
```json
Response:
{
  "id": "uuid",
  "games_analyzed": 47,
  "rating_at_generation": 1340,
  "generated_at": "2026-04-07T...",
  "source": "lichess",
  "critical_openings": [
    {
      "eco_code": "B70",
      "opening_name": "Sicilian Defense: Dragon Variation",
      "games": 18,
      "wins": 4,
      "losses": 14,
      "win_rate": 22.2,
      "avg_collapse_move": 9,
      "collapse_type": "tactical_blunder",
      "neon_diagnosis": "You reach a solid position then drop material at move 9. Undefended pieces — same pattern across 4 games.",
      "is_critical": true,
      "linked_opening_id": "uuid",
      "training_unlocked": true
    },
    {
      "eco_code": "D20",
      "opening_name": "Queen's Gambit Accepted",
      "games": 9,
      "wins": 3,
      "losses": 6,
      "win_rate": 33.3,
      "avg_collapse_move": 11,
      "collapse_type": "opening_error",
      "neon_diagnosis": "You go off-book at move 8 and the center collapses. The theory runs deeper than you think.",
      "is_critical": true,
      "linked_opening_id": "uuid",
      "training_unlocked": false
    }
  ],
  "strengths": [
    {
      "eco_code": "C50",
      "opening_name": "Italian Game",
      "games": 15,
      "win_rate": 66.7
    }
  ],
  "overall_pattern": "You play solid opening theory through move 8. The middlegame transition is costing you. Sparring sessions past move 10 will expose and fix the pattern."
}
```

**GET /analytics/dashboard**
```json
Response:
{
  "lichess_rating": {
    "current": 1387,
    "30_day_delta": 47,
    "trend": [1340, 1345, 1352, 1361, 1378, 1387]
  },
  "this_week": {
    "sessions": 6,
    "drill_cards_reviewed": 84,
    "win_rate": 64,
    "avg_accuracy": 79.4
  },
  "opening_improvements": [
    {
      "eco_code": "B70",
      "opening_name": "Sicilian Defense",
      "baseline_win_rate": 22.2,
      "current_win_rate": 41.0,
      "delta": 18.8,
      "status": "improving"
    }
  ],
  "drill_queue_count": 7,
  "streak": 5,
  "recommended_session": {
    "opening_id": "uuid",
    "opening_name": "Sicilian Defense: Dragon",
    "reason": "Your weakest opening this week"
  },
  "estimated_drill_minutes": 6
}
```

---

### 8. Backend Project Structure

```
backend/
├── app/
│   ├── main.py                         # FastAPI init, CORS, routers
│   ├── config.py                       # Pydantic Settings (env vars)
│   ├── dependencies.py                 # DB session, auth dependencies
│   │
│   ├── core/
│   │   ├── security.py                 # JWT signing/validation
│   │   ├── exceptions.py               # Custom HTTP exceptions
│   │   └── middleware.py               # CORS, rate limiter
│   │
│   ├── db/
│   │   ├── session.py                  # Async session factory
│   │   └── models/
│   │       ├── user.py
│   │       ├── sparring_session.py
│   │       ├── opening.py
│   │       ├── lichess_game.py
│   │       ├── glitch_report.py
│   │       ├── lichess_rating_snapshot.py
│   │       ├── user_move_mastery.py
│   │       ├── user_repertoire.py
│   │       └── subscription.py
│   │
│   ├── schemas/                        # Pydantic V2 request/response models
│   │   ├── auth.py
│   │   ├── session.py
│   │   ├── lichess.py
│   │   ├── glitch_report.py
│   │   ├── drill.py
│   │   └── analytics.py
│   │
│   ├── api/v1/
│   │   ├── auth.py
│   │   ├── sessions.py
│   │   ├── lichess.py
│   │   ├── glitch_report.py
│   │   ├── repertoire.py
│   │   ├── drill.py
│   │   ├── analytics.py
│   │   └── webhooks.py
│   │
│   ├── services/                       # ALL business logic
│   │   ├── auth_service.py             # Firebase + JWT
│   │   ├── session_service.py          # Move validation, state machine
│   │   ├── chess_service.py            # python-chess wrapper
│   │   ├── ai_service.py              # Template library + Gemini fallback
│   │   ├── coach_templates.py          # NEON template library (YAML/JSON)
│   │   ├── lichess_service.py          # Game import, Explorer, rating fetch
│   │   ├── lichess_analyzer.py         # Glitch Report generation
│   │   ├── stockfish_service.py        # Engine analysis — ONLY for Glitch Report
│   │   ├── srs_service.py              # SM-2 spaced repetition
│   │   ├── analytics_service.py        # Dashboard aggregation
│   │   └── subscription_service.py     # Stripe + pro status
│   │
│   └── workers/
│       └── lichess_import_worker.py    # Async background job for game import
│
├── data/
│   └── neon_templates.yaml             # NEON coaching template library
│
├── alembic/
├── tests/
├── scripts/
│   ├── seed_openings.py
│   └── admin_queries.py                # CLI admin utilities (see Section 10)
├── .env.example
├── requirements.txt
├── ecosystem.config.js                 # PM2 config for Hostinger
└── Dockerfile
```

#### Environment Variables

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@host/neongambit
REDIS_URL=redis://default:password@host:6379
FIREBASE_PROJECT_ID=neongambit-prod
FIREBASE_CREDENTIALS_PATH=./firebase-admin-key.json
GOOGLE_GEMINI_API_KEY=your_key
LICHESS_API_TOKEN=lip_xxx              # Higher rate limits on authenticated calls
STOCKFISH_PATH=/usr/local/bin/stockfish
STOCKFISH_MAX_DEPTH=15
JWT_SECRET_KEY=change-in-prod
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
STRIPE_PRICE_ID_MONTHLY=price_xxx
STRIPE_PRICE_ID_YEARLY=price_xxx
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:3000,https://neongambit.com
RATE_LIMIT_MOVES_PER_MINUTE=60
RATE_LIMIT_ANALYSES_PER_DAY_FREE=3
RATE_LIMIT_DRILLS_PER_DAY_FREE=5
```

---

### 9. Architecture Decision Records

#### ⚡ ADR-001 — Why Next.js Over Flutter

Antigravity's browser agent verifies UI changes in Chrome without a compilation step. Flutter breaks the autonomous Plan → Build → Verify loop. TypeScript + Tailwind + shadcn/ui is the highest-quality stack for AI-generated code. Decision is final.

#### ⚡ ADR-002 — Stockfish: Client WASM for Sparring, Server for Glitch Report

**Context:** Running Stockfish server-side for every move during sparring sessions is the single biggest cost and scalability risk. At depth 15, each evaluation takes 200-500ms of CPU. With 50 concurrent users, a single server instance cannot keep up.

**Decision:**
- **Sparring (real-time):** Stockfish runs client-side via `stockfish.wasm` in a Web Worker. The browser evaluates each move locally. Move quality (excellent/good/inaccuracy/mistake/blunder) is determined by comparing the user's move eval to the best move eval, using standard centipawn thresholds. Results are sent back to the server for stats tracking.
- **Glitch Report (async):** Stockfish runs server-side on the Hostinger VPS. This is a background job that analyzes a sample of 5 worst games per user. It runs once per Lichess import, not in real-time. CPU load is bounded and predictable.

**Consequences:**
- Server CPU is freed from the most expensive operation (per-move analysis during sparring).
- Client devices (phones, laptops) handle WASM evaluation easily — stockfish.wasm at depth 12-15 runs in <300ms on modern devices.
- The server's role during sparring is reduced to: validate legality, look up Explorer data, return opponent move, track game state. All lightweight operations.
- Trade-off: client-side eval means a user could theoretically tamper with move quality reports. This is acceptable — the user only cheats themselves, and the server still validates move legality.

**Implementation notes:**
- `stockfish.wasm` is loaded as a Web Worker on first sparring session start. Stays loaded for session duration.
- Depth is capped at 12 client-side (fast enough for real-time) and 15 server-side (Glitch Report, where latency doesn't matter).
- If the user's device cannot run WASM (very old browsers), fall back to server-side analysis with a rate limit of 1 eval per move and depth capped at 10.

#### ⚡ ADR-003 — Hostinger VPS Over Render/Railway

**Context:** Render free tier has 30+ second cold starts. Railway and Fly.io have minimum $5/mo costs. An existing Hostinger KVM 1 VPS is already running for Singular Mind.

**Decision:** Deploy FastAPI on the existing Hostinger VPS using PM2 + nginx reverse proxy. Stockfish binary is installed directly on the VPS (apt install stockfish).

**Consequences:**
- Zero cold starts. The API is always warm.
- Stockfish is a native binary, not a container — maximum performance for Glitch Report generation.
- PM2 handles process management, restarts, and logging.
- nginx handles TLS termination, rate limiting at the network level, and reverse proxy to the FastAPI process.
- Trade-off: manual server management (updates, monitoring). Acceptable for a solopreneur who already manages this VPS.

**PM2 ecosystem config:**
```javascript
// ecosystem.config.js
module.exports = {
  apps: [{
    name: 'neongambit-api',
    script: 'uvicorn',
    args: 'app.main:app --host 0.0.0.0 --port 8000',
    interpreter: 'python3',
    env: {
      ENVIRONMENT: 'production'
    },
    max_memory_restart: '500M',
    instances: 1,
    autorestart: true
  }]
};
```

#### ⚡ ADR-004 — NEON Coach: Templates First, LLM Second

**Context:** LLM-generated coaching text has three risks: inconsistent tone, tactically incorrect chess advice, and per-call cost/latency. During sparring, a user expects instant feedback (<100ms display latency).

**Decision:** In-game coaching uses a curated template library (80% of messages). Gemini is used only for narrative generation in Glitch Reports and post-session summaries (20% of messages).

**Consequences:**
- In-game coaching is instant (template lookup, no network call).
- NEON's voice is consistent and curated — every message has been reviewed for tone and chess accuracy.
- Gemini costs are bounded: ~1 call per Glitch Report generation + ~1 call per session end. At 100 daily active users, that's ~200 Gemini calls/day — well within free tier.
- Trade-off: less variety in in-game messages. Mitigated by having 200+ templates across patterns and ELO ranges.

#### ⚡ ADR-005 — Internationalization: English + Spanish from Day 1

**Context:** The chess improvement market is global. The Lichess user base has significant Spanish-speaking representation (Latin America and Spain). Launching in English-only leaves a large addressable market untapped. Adding i18n retroactively is painful — string extraction after the fact is one of the worst refactoring tasks in frontend development.

**Decision:** Ship MVP with English (default) and Spanish. Use `next-intl` (lightweight, App Router native) for frontend i18n. Backend API responses that contain user-facing text (NEON coaching messages, Glitch Report narratives) are also localized.

**What gets translated:**
- All UI strings (buttons, labels, headers, error messages, onboarding copy)
- NEON coaching template library — full Spanish version of all ~200 templates. The NEON persona translates naturally: direct, efficient, slightly cryptic works in both languages. Use "tú" form, not "usted."
- Glitch Report narrative: the Gemini prompt includes a `language` parameter. Narrative is generated in the user's preferred language.
- Post-session summary narrative: same approach.
- Opening names remain in English (they are standardized international terms: "Sicilian Defense", "Ruy Lopez"). No translation needed.

**What does NOT get translated (MVP):**
- Admin scripts and internal logging (English only)
- Error codes and API field names (technical, not user-facing)

**Implementation:**
- Frontend: `next-intl` with JSON message files per locale (`messages/en.json`, `messages/es.json`). Language detected from browser `Accept-Language` header on first visit, stored in user preferences, changeable in settings.
- NEON templates: `neon_templates.yaml` has a top-level locale key. Each template has `en` and `es` variants:
```yaml
blunder_hanging_piece:
  en:
    low: "Your {piece} on {square} is undefended. That's a hanging piece — scan for undefended pieces before every move."
  es:
    low: "Tu {piece} en {square} está sin defender. Es una pieza colgada — revisa las piezas sin protección antes de cada jugada."
```
- Gemini calls: include `"Respond in {locale}"` in system prompt. Works reliably for en/es.
- User model: add `preferred_language TEXT DEFAULT 'en' CHECK (preferred_language IN ('en', 'es'))` to `users` table.

**Consequences:**
- ~30% more work on template authoring (200 templates × 2 languages = 400 entries). But this is content work, not engineering — can be done in parallel with development.
- String extraction discipline from day 1 means adding Portuguese, French, German later is a content task, not a refactoring task.
- The Spanish-speaking chess community on Reddit (r/ajedrez), YouTube (partidas en español channels), and Lichess forums becomes a viable acquisition channel from launch.

**Future languages (Phase 2+):** Portuguese (Brazil has a massive chess community), French, German. Added when acquisition data shows demand.

---

### 10. Administration (No Backoffice)

**Decision:** No admin panel in MVP. All administration is done via direct database access and CLI scripts.

**Tools:**
- **Neon Console** (web UI): SQL queries for user lookup, stats, debugging
- **Stripe Dashboard**: Subscription management, revenue tracking, refunds
- **Upstash Console**: Redis cache inspection and flushing
- **`scripts/admin_queries.py`**: CLI utilities for common admin tasks

**Admin script examples:**

```python
# scripts/admin_queries.py

async def get_user_summary(lichess_username: str):
    """Full user overview: profile, stats, subscription, glitch report."""
    ...

async def regenerate_glitch_report(user_id: str):
    """Force regenerate a user's Glitch Report."""
    ...

async def toggle_pro(user_id: str, enable: bool):
    """Manually grant or revoke Pro status (for testing, comps)."""
    ...

async def daily_metrics():
    """Print DAU, new users, sessions played, drills completed, conversions."""
    ...

async def user_retention_cohort(days: int = 7):
    """Users who were active N days ago — how many returned today?"""
    ...

async def lichess_api_health():
    """Check Lichess API availability and current rate limit status."""
    ...
```

**When to build an admin panel:** When support requests exceed what can be handled via SQL + scripts (estimated: 500+ users), or when a non-technical team member needs access to user data.

---

### 11. Cost Optimization (Solo Founder)

| Resource | Strategy | Rationale |
|---------|---------|---------|
| **Stockfish (sparring)** | Client-side WASM. Zero server cost per move. | The single biggest cost saving in the architecture. |
| **Stockfish (Glitch Report)** | Server-side, depth 15, sample of 5 worst games only. Runs on Hostinger VPS native binary. | Bounded: one analysis per import, not per session. |
| **Lichess API** | Cache all Explorer responses (Redis, 30-day TTL). 90% of sessions hit cache. | Free and unlimited — be aggressive with caching |
| **Gemini AI** | Template library for in-game coaching. Gemini only for Glitch Report narrative + session summary. Under 200 calls/day at 100 DAU. | Free tier covers this. Templates are faster and more reliable. |
| **Neon DB** | Delete `lichess_games` records >90 days old for Free users (keep ECO stats). Delete completed sessions >30 days. | Stays within free tier storage |
| **Hostinger VPS** | Already paid for (Singular Mind). FastAPI + Stockfish share the VPS. | Incremental cost: $0 |
| **Vercel** | Frontend on free tier. Auto-deploy from GitHub. | Free for personal projects |
| **Total MVP hosting cost** | **~$0/month** (Neon free + Upstash free + Hostinger existing + Vercel free) | First dollar of revenue is pure margin |

---

### 12. User Acquisition Strategy

**The document that ships the code is useless without the plan that brings users.**

**Target:** 50 active users in first 30 days. 200 in 90 days. First paying user by day 45.

#### Pre-Launch (2 weeks before deploy)

1. **Create r/chess and r/lichess presence.** Post a "I analyzed my last 200 Lichess games and found out exactly why I'm stuck at 1350" thread. Show a real Glitch Report (your own account). Don't mention the product yet. Build curiosity.
2. **Record a 60-second screen capture** of the Glitch Report reveal animation. Post to r/chess, Twitter/X chess community, and Lichess forum. Caption: "I built a tool that finds your exact weakness pattern from your Lichess history."
3. **Landing page** with email capture: "Be first to try NeonGambit. Enter your Lichess username for early access." Collect emails. Build anticipation.

#### Launch Week

4. **r/chess launch post:** "I built NeonGambit — it reads your Lichess games and tells you exactly why you keep losing. Free to try." Direct link to PWA. Engage every comment.
5. **r/lichess cross-post** with Lichess-specific framing: "Built on top of the Lichess API — your game data finally put to work."
6. **Chess YouTube/Twitch outreach:** Contact 5-10 chess content creators in the 1K-10K subscriber range. Offer free Pro access in exchange for a try-it-on-stream segment. The Glitch Report reveal is inherently good content — it's dramatic and personal.

#### Ongoing

7. **Weekly "Glitch Report of the Week"** social media post. Anonymized report from a real user (with permission) showing before/after improvement. This is the core content loop.
8. **Lichess forum presence.** Answer "how do I improve" threads with genuine advice + subtle mention: "I built a tool that automates exactly this analysis."
9. **SEO play:** Blog posts targeting "why am I stuck at 1200 chess," "how to improve at chess without a coach," "lichess analysis tool." Spanish SEO: "cómo mejorar en ajedrez," "estoy estancado en ajedrez," "herramienta de análisis lichess." These queries have volume and low competition in both languages.
10. **Spanish-speaking chess community.** r/ajedrez, YouTube channels de ajedrez en español (Luisón, Rey Enigma, etc.), Lichess forum in Spanish. Post Glitch Report content in Spanish. This is a low-competition channel — almost no chess improvement tools market actively in Spanish. The product ships bilingual from day 1, which is a genuine differentiator.

**What NOT to spend time on:** Paid ads (budget doesn't support it), ProductHunt launch (wrong audience), Instagram/TikTok (chess content underperforms on visual-first platforms unless you're a streamer).

---

### 13. Antigravity Development — Mission Architecture

Each mission is designed for full autonomous execution in Antigravity's Manager View. The agent plans, codes, verifies in browser, and produces artifacts — no manual compilation steps.

**Total estimated build time: ~27 hours across 8 missions.**

#### Mission Definitions

**Mission 0 — Frontend Foundation (3h)**
> Set up Next.js 14 App Router + TypeScript strict + Tailwind + shadcn/ui + next-pwa.
> Configure manifest.json (portrait-locked, mobile-first).
> Add Orbitron, JetBrains Mono, Inter fonts.
> Create `lib/utils/designTokens.ts` with canonical color tokens.
> Create `app/globals.css` with .glass, .scanlines, .glitch-animation, and neon text utilities.
> Extend tailwind.config.js.
> Set up stockfish.wasm Web Worker infrastructure (`lib/stockfish/worker.ts`).
> Set up `next-intl` with `messages/en.json` and `messages/es.json`. Configure locale detection from `Accept-Language` header.
> Verify: `npm run build` succeeds. Lighthouse PWA score > 90. Locale switching works.

**Mission 1 — Backend Foundation (4h)**
> Set up FastAPI project structure per Section 8.
> Create all database models from Section 6 schema.
> Set up Alembic migrations and run initial migration.
> Implement health check endpoint.
> Create `ecosystem.config.js` for PM2.
> Create nginx config template for Hostinger deployment.
> Verify: `GET /health` returns `{"status": "ok"}`. All tables created in Neon.

**Mission 2 — Auth + Lichess Import (4h)**
> Implement all `/auth/*` endpoints. Guest creates JWT from UUID. Firebase validates.
> Implement `lichess_service.py`: fetch user games, parse ECO + result + PGN.
> Implement `POST /lichess/import` with async background worker.
> Implement `GET /lichess/import/status` for polling.
> Implement Lichess API degraded mode: cache-first, retry queue, graceful fallback.
> Verify: Guest token flow works. Lichess import fetches 20 games for a real username.

**Mission 3 — Glitch Report Engine (4h)**
> Implement `lichess_analyzer.py`:
>   - Aggregate win rate per ECO code
>   - Identify critical openings (win_rate < 40%)
>   - Sample 5 worst games, run Stockfish SERVER-SIDE to find collapse move
>   - Classify collapse type per opening: `opening_error`, `tactical_blunder`, `positional_drift`, `time_pressure`
>   - Call Gemini to generate neon_diagnosis (including collapse type context) and overall_pattern
> Implement `POST /glitch-report/generate` + `GET /glitch-report/current`
> Implement mini Glitch Report generation from NeonGambit session data (fallback for no-Lichess users).
> Auto-assign top 2 critical openings to user's repertoire (Free) or all critical openings (Pro).
> Verify: Generate report for a real Lichess username with 20+ games. Critical openings identified correctly.

**Mission 4 — Chess Engine + Sparring Sessions (5h)**
> Implement `chess_service.py`, `lichess_service.py` (Explorer endpoint for opponent move selection).
> Implement opening cache (Redis + Postgres).
> Implement all MVP `/sessions/*` endpoints per Section 7.
> Implement `session_service.py` with move validation and opponent response logic.
> Frontend: integrate stockfish.wasm Web Worker for client-side move evaluation.
> Implement client → server move quality reporting (prev_move_quality field).
> Implement tilt tracking in user_stats (consecutive loss counter).
> Verify: Full sparring session works end-to-end. Illegal move → 400. Client-side eval displays move quality. Opponent responds with human-like delay.

**Mission 5 — NEON Coach Templates (3h)**
> Create `data/neon_templates.yaml` with ~200 coaching templates across patterns and ELO ranges, in English and Spanish. Each blunder/mistake template follows the consequence → pattern name → forward seed structure.
> Implement `coach_templates.py`: template selection engine (move quality × tactical pattern × ELO range × locale).
> Implement `ai_service.py`: Gemini integration for Glitch Report narrative + session summary.
> Implement fallback chain: template → Gemini → generic.
> Theory exit detection: when move is not in opening's `starting_moves`, flag `theory_exit_detected`.
> Tilt detection NEON intervention message.
> Verify: Blunder on known position returns template message under 20 words. ELO-adaptive: different text for 1100 vs 1600. Gemini generates Glitch Report narrative.

**Mission 6 — Neural Drill + SRS (3h)**
> Implement `srs_service.py` (SM-2 algorithm).
> Implement all `/drill/*` endpoints.
> Populate `user_move_mastery` table from opening moves when openings are assigned to repertoire.
> Verify: SM-2 correctly advances interval after quality=4. Due cards return correctly after 24h.

**Mission 7 — Frontend: Core Screens (5h)**
> Build all MVP screens:
>   - Mission Control dashboard (Home screen) per Section 5, Feature 7.
>   - Glitch Report reveal screen with cinematic load sequence. Display collapse type per opening (tactical blunder / positional drift / opening error / time pressure).
>   - The Arena (sparring session) with full game loop + client-side Stockfish eval display.
>   - Neural Drill screen with Shadow Move hint.
>   - Tilt detection intervention overlay.
>   - Session summary card (post-game).
>   - Profile screen (basic: username, Lichess link, subscription status, streak, language selector).
>   - Upgrade/paywall screens with natural triggers.
>   - All screens use `next-intl` translation keys — no hardcoded user-facing strings.
> Verify: Full user journey from guest → Lichess import → Glitch Report → Sparring → Drill works end-to-end. Switch to Spanish and verify all screens render correctly.

**Mission 8 — Deploy + Polish (2h)**
> Deploy backend to Hostinger VPS: PM2 + nginx + SSL (Let's Encrypt).
> Deploy frontend to Vercel with production env vars.
> Configure Cloudflare DNS.
> Configure Stripe webhooks with production endpoint.
> Test full PWA install flow on iOS Safari and Android Chrome.
> Verify: PWA installs. Lighthouse PWA score > 90. Payment flow works end-to-end.

---

### 14. Phase 2 Roadmap (Post-Validation)

**Trigger to begin Phase 2:** 50+ weekly active users AND at least 5 paying subscribers AND qualitative signal that the core loop (Diagnose → Practice → Measure) is working (users reporting ELO gains).

| Priority | Feature | Estimated Effort | Trigger |
|----------|---------|-----------------|---------|
| P0 | Conversion Failures + Endgame Drill | 2 weeks | Users asking "what about my endgames?" |
| P0 | Full Game Review / Debrief | 1 week | Users wanting move-by-move analysis after sparring |
| P1 | Achievement System | 1 week | Retention data shows D7 drop-off needs gamification |
| P1 | Daily Mission System | 3 days | Drill queue alone isn't driving daily return |
| P1 | Repertoire Builder (full browse) | 1 week | Users asking to train openings beyond Glitch Report |
| P2 | Telegram Bot notifications | 3 days | Email open rates are low |
| P2 | Voice TTS for NEON (Pro) | 1 week | User research shows demand |
| P2 | Chess.com integration | 2 weeks | When Chess.com API access is available |
| P3 | Opponent Preparation Mode | 1 week | Tournament players requesting it |
| P3 | Capacitor native wrapper | 1 week | PWA install rates are a measurable retention bottleneck |

---

*End of NeonGambit Master Guide v5.0*
*Ship the loop. Let users tell you what to build next.*
