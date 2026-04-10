# NeonGambit Frontend Implementation Guide

> **Version:** 5.1 — MVP-Scoped · Stockfish WASM · Template Coach · i18n · Hostinger Deploy
> **Backend API:** `https://api.neongambit.com/v1` | Swagger: `https://api.neongambit.com/docs`
> **Platform:** Next.js 14 PWA · Mobile-First · Vercel deployment
> **Development IDE:** Google Antigravity (Gemini 3 Pro primary, Claude Sonnet 4.6 available)
> **Master Guide:** v5.1 (single source of truth for all product decisions)
> **Last Updated:** April 2026

---

## Table of Contents

1. [Stack & Rationale](#1-stack--rationale)
2. [Project Architecture](#2-project-architecture)
3. [Design System](#3-design-system)
4. [API Integration Layer](#4-api-integration-layer)
5. [State Management](#5-state-management)
6. [Screen Specifications](#6-screen-specifications)
   - [6.1 Splash / Boot](#61-splash--boot-screen)
   - [6.2 Mission Control (Home)](#62-mission-control-home)
   - [6.3 Lichess Connect & Import](#63-lichess-connect--import)
   - [6.4 Glitch Report Reveal](#64-glitch-report-reveal)
   - [6.5 The Arena (Sparring)](#65-the-arena-sparring)
   - [6.6 Session Debrief (Summary)](#66-session-debrief)
   - [6.7 Neural Drill](#67-neural-drill)
   - [6.8 Profile & Settings](#68-profile--settings)
7. [Stockfish WASM Integration](#7-stockfish-wasm-integration)
8. [Component Library](#8-component-library)
9. [Performance & UX Patterns](#9-performance--ux-patterns)
10. [Navigation Structure](#10-navigation-structure)
11. [Implementation Phases — Antigravity Mission Plan](#11-implementation-phases--antigravity-mission-plan)
12. [Quick Reference: API Endpoints (MVP)](#12-quick-reference-api-endpoints)

---

## 1. Stack & Rationale

### Definitive Stack

```
Framework:     Next.js 14 (App Router)
Language:      TypeScript (strict mode)
Styling:       Tailwind CSS v3 + shadcn/ui
Animations:    Framer Motion v11
Chess UI:      react-chessboard v4
Chess Logic:   chess.js v1 (optimistic UI only — server is source of truth)
Chess Engine:  stockfish.wasm via Web Worker (client-side move evaluation during sparring)
State:         Zustand v4 (flat stores)
Auth:          Firebase Auth v10 + NextAuth.js v5
HTTP:          Axios v1 with typed interceptors + polling helpers
i18n:          next-intl (App Router native) — English + Spanish
Audio:         Howler.js v2
Haptics:       Web Vibration API (navigator.vibrate)
Fonts:         Orbitron + JetBrains Mono + Inter (Google Fonts)
Charts:        Recharts (rating trend, win rate history)
PWA:           next-pwa v5
Deployment:    Vercel (auto-deploy from GitHub main)
```

### Why This Stack for Antigravity

Antigravity's core value is the **Plan → Build → Verify** loop: the agent writes code, launches `npm run dev`, then opens Chrome to test the result — autonomously. This stack maximizes that loop:

- **TypeScript + Tailwind + shadcn/ui** is the highest-density stack in AI training data. Agents produce more accurate, less hallucinated code here than in any alternative.
- **shadcn/ui** components live in the repo — agents can open, read, and modify them directly. No black boxes.
- **Zustand flat stores** are maximally readable for agents. A store is just a plain object with functions. Agents understand them in one read without tracing reducers or atoms.
- **Next.js App Router** directory structure is self-documenting — a route is a folder. Agents navigate and create files without confusion.
- **Vercel + GitHub** CI/CD means agents can trigger a deploy by pushing code — no manual steps.

### Why PWA Over Flutter

Flutter requires a separate compilation step that breaks Antigravity's browser-based verification. The agent cannot open a Flutter app in its embedded Chrome. Next.js can be verified in the browser instantly. Decision is final and documented in Master Guide ADR-001.

---

## 2. Project Architecture

### Directory Structure

```
/
├── app/                                  # Next.js App Router
│   ├── layout.tsx                        # Root — fonts, providers, PWA meta tags
│   ├── page.tsx                          # Splash → auto-redirect logic
│   │
│   ├── (auth)/
│   │   └── login/page.tsx               # Login (shown only when saving progress)
│   │
│   └── (main)/
│       ├── layout.tsx                    # Dashboard shell — BottomNav + TopBar
│       ├── page.tsx                      # Mission Control (Home)
│       ├── glitch-report/
│       │   └── page.tsx                  # Glitch Report reveal + full view
│       ├── arena/
│       │   └── page.tsx                  # Sparring session screen
│       ├── debrief/
│       │   └── [sessionId]/page.tsx      # Post-session review
│       ├── drill/
│       │   └── page.tsx                  # Neural Drill
│       └── profile/
│           └── page.tsx                  # Stats, settings, language selector
│
├── components/
│   ├── ui/                               # shadcn/ui base (lives in repo)
│   │
│   ├── chess/
│   │   ├── NeonChessboard.tsx            # react-chessboard with cyberpunk theme
│   │   ├── TheoryBar.tsx                 # Theory integrity progress bar
│   │   ├── EvalGauge.tsx                 # Vertical win probability VU meter (stockfish.wasm driven)
│   │   ├── MoveTimeline.tsx              # Colored dot timeline for debrief
│   │   └── SurvivalBanner.tsx            # Out-of-book amber banner
│   │
│   ├── coach/
│   │   ├── NeonTerminal.tsx              # Typewriter coaching widget
│   │   └── NeonAvatar.tsx                # Animated NEON persona icon
│   │
│   ├── glitch/
│   │   ├── GlitchReportReveal.tsx        # Cinematic reveal sequence
│   │   ├── CriticalOpeningCard.tsx       # Per-opening vulnerability card (with collapse_type)
│   │   ├── StrengthRow.tsx               # Strengths section row
│   │   └── PatternSummary.tsx            # NEON overall pattern block
│   │
│   ├── progress/
│   │   ├── RatingChart.tsx               # Lichess rating trend (Recharts)
│   │   ├── OpeningImprovementRow.tsx     # Baseline vs current win rate
│   │   ├── StreakBadge.tsx               # Streak flame counter
│   │   └── MasteryGauge.tsx              # Radial progress ring per opening
│   │
│   ├── drill/
│   │   ├── DrillCard.tsx                 # Single drill position card
│   │   ├── ShadowMove.tsx                # Ghost piece hint overlay
│   │   └── DrillResult.tsx               # Correct/incorrect feedback
│   │
│   └── shared/
│       ├── SystemBoot.tsx                # Cold start terminal animation (kept for brand feel)
│       ├── CyberpunkCard.tsx             # Glassmorphism wrapper
│       ├── NeonButton.tsx                # Primary/secondary/danger variants
│       ├── NeonBadge.tsx                 # Status/tier badges
│       ├── UpgradeModal.tsx              # Pro paywall with feature preview
│       ├── LichessConnectPrompt.tsx      # Post-game "connect Lichess" nudge
│       ├── TiltIntervention.tsx          # NEON tilt warning overlay
│       ├── LoadingTerminal.tsx           # Processing screens with log lines
│       └── BottomNav.tsx                 # Persistent 3-tab navigation (Arena / Drill / Profile)
│
├── lib/
│   ├── api/
│   │   ├── client.ts                     # Axios instance + interceptors + polling
│   │   ├── auth.ts
│   │   ├── sessions.ts                   # Sparring session endpoints + types
│   │   ├── lichess.ts                    # Import + status polling
│   │   ├── glitchReport.ts              # Glitch Report endpoints + types
│   │   ├── repertoire.ts                 # User repertoire (simplified MVP)
│   │   ├── drill.ts                      # Neural Drill + SRS
│   │   ├── analytics.ts                  # Dashboard + trend data
│   │   └── user.ts
│   │
│   ├── store/
│   │   ├── useAuthStore.ts
│   │   ├── useSessionStore.ts            # Active sparring session state
│   │   ├── useDrillStore.ts
│   │   └── useDashboardStore.ts
│   │
│   ├── stockfish/
│   │   ├── worker.ts                     # Stockfish WASM Web Worker wrapper
│   │   ├── useStockfish.ts               # React hook for client-side eval
│   │   └── stockfish.wasm                # WASM binary (loaded from /public or CDN)
│   │
│   ├── hooks/
│   │   ├── useTypewriter.ts              # Letter-by-letter text animation
│   │   ├── useHaptics.ts                 # navigator.vibrate wrapper
│   │   ├── useAudio.ts                   # Howler.js sound manager
│   │   ├── useBootSequence.ts            # Cold start detection + SystemBoot trigger
│   │   ├── usePollJobStatus.ts           # Polling hook for async backend jobs
│   │   └── useGlitchReveal.ts            # Orchestrates the reveal animation sequence
│   │
│   └── utils/
│       ├── designTokens.ts               # Canonical colors, spacing, typography
│       ├── chess.ts                      # chess.js helpers (optimistic FEN, move display)
│       └── format.ts                     # Numbers, percentages, dates
│
├── messages/
│   ├── en.json                           # English UI strings
│   └── es.json                           # Spanish UI strings
│
├── public/
│   ├── sounds/
│   │   ├── move.mp3
│   │   ├── capture.mp3
│   │   ├── blunder-glitch.mp3
│   │   ├── excellent.mp3
│   │   └── mission-complete.mp3
│   ├── stockfish/
│   │   └── stockfish.wasm                # Stockfish WASM binary
│   ├── icons/                            # PWA icons (192, 512, maskable)
│   └── manifest.json
│
├── i18n.ts                               # next-intl configuration
└── next.config.js                        # next-pwa, next-intl, env vars
```

---

## 3. Design System

### Canonical Color Tokens

```typescript
// lib/utils/designTokens.ts
// THE ONLY place colors are defined. Import from here everywhere. Never hardcode hex.

export const colors = {
  // BACKGROUNDS
  void:        '#080810',   // Page background
  surface:     '#0F0F1A',   // Cards, panels
  elevated:    '#161625',   // Modals, tooltips, dropdowns
  border:      '#1E1E35',   // Dividers, card outlines

  // PRIMARY BRAND
  cyan:        '#00E5FF',   // Main accent — CTAs, white pieces, links
  cyanDim:     '#00A3B5',   // Hover state, secondary labels
  cyanGlow:    'rgba(0, 229, 255, 0.15)',

  magenta:     '#E0008C',   // Opponent color, destructive actions, black pieces
  magentaDim:  '#9A006E',
  magentaGlow: 'rgba(224, 0, 140, 0.15)',

  // ACCENTS
  violet:      '#7C3AED',   // Pro tier, premium UI elements
  amber:       '#F59E0B',   // Warnings, out-of-book survival mode
  emerald:     '#10B981',   // Success, wins, excellent moves

  // MOVE QUALITY (chess-specific)
  excellent:   '#10B981',
  good:        '#34D399',
  inaccuracy:  '#F59E0B',
  mistake:     '#F97316',
  blunder:     '#EF4444',

  // TEXT
  textPrimary:   '#F0F0F5',  // Main text — slight blue-white tint
  textSecondary: '#8B8BA0',  // Muted labels
  textMuted:     '#4B4B65',  // Disabled, placeholder

  // ACHIEVEMENT TIERS
  bronze:    '#CD7F32',
  silver:    '#A8A8B0',
  gold:      '#F5C518',
  platinum:  '#D0D0E0',
  neon:      '#00E5FF',
} as const;

export const spacing = {
  xs: '4px', sm: '8px', md: '16px', lg: '24px', xl: '32px', xxl: '48px',
} as const;

export const typography = {
  h1: { fontFamily: 'Orbitron', fontSize: '28px', fontWeight: '700' },
  h2: { fontFamily: 'Orbitron', fontSize: '22px', fontWeight: '600' },
  h3: { fontFamily: 'Orbitron', fontSize: '18px', fontWeight: '600' },
  body: { fontFamily: 'Inter', fontSize: '16px', fontWeight: '400' },
  caption: { fontFamily: 'Inter', fontSize: '14px', fontWeight: '400' },
  mono: { fontFamily: 'JetBrains Mono', fontSize: '13px', fontWeight: '400' },
  label: { fontFamily: 'Orbitron', fontSize: '11px', fontWeight: '600', letterSpacing: '0.12em' },
} as const;
```

### Tailwind Config

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        void: '#080810', surface: '#0F0F1A', elevated: '#161625', border: '#1E1E35',
        cyan: '#00E5FF', magenta: '#E0008C', violet: '#7C3AED',
        amber: '#F59E0B', emerald: '#10B981',
      },
      fontFamily: {
        orbitron: ['Orbitron', 'sans-serif'],
        mono:     ['JetBrains Mono', 'monospace'],
        sans:     ['Inter', 'sans-serif'],
      },
      boxShadow: {
        'neon-cyan':    '0 0 20px rgba(0, 229, 255, 0.35)',
        'neon-magenta': '0 0 20px rgba(224, 0, 140, 0.35)',
        'neon-sm':      '0 0 8px rgba(0, 229, 255, 0.2)',
        'neon-amber':   '0 0 16px rgba(245, 158, 11, 0.35)',
      },
      animation: {
        'glitch':       'glitch 0.2s steps(2) forwards',
        'scanline':     'scanline 8s linear infinite',
        'pulse-neon':   'pulse-neon 2s ease-in-out infinite',
        'flicker':      'flicker 0.15s ease-in-out',
        'slide-up':     'slide-up 0.3s ease-out',
        'fade-in':      'fade-in 0.4s ease-out',
      },
    },
  },
};
```

### Global CSS Effects

```css
/* app/globals.css */

/* Glassmorphism — apply to all cards/panels */
.glass {
  background: rgba(15, 15, 26, 0.85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(30, 30, 53, 0.9);
}

/* Scanlines — apply to .terminal, NEON widget */
.scanlines::after {
  content: '';
  position: absolute;
  inset: 0;
  background: repeating-linear-gradient(
    0deg, transparent, transparent 2px,
    rgba(0, 0, 0, 0.12) 2px, rgba(0, 0, 0, 0.12) 4px
  );
  pointer-events: none;
  z-index: 10;
}

/* Neon glow text */
.text-glow-cyan    { text-shadow: 0 0 12px rgba(0, 229, 255, 0.8); }
.text-glow-magenta { text-shadow: 0 0 12px rgba(224, 0, 140, 0.8); }
.text-glow-amber   { text-shadow: 0 0 12px rgba(245, 158, 11, 0.8); }

/* Chromatic aberration — triggered on blunder */
@keyframes glitch {
  0%   { filter: none; }
  25%  { filter: drop-shadow(-3px 0 #E0008C) drop-shadow(3px 0 #00E5FF); }
  75%  { filter: drop-shadow(3px 0 #E0008C) drop-shadow(-3px 0 #00E5FF); }
  100% { filter: none; }
}
.glitch-animation { animation: glitch 0.2s steps(2) forwards; }

/* Amber screen flash — out-of-book survival mode */
@keyframes flicker {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.85; }
}
.survival-flash {
  animation: flicker 0.15s ease-in-out 3;
  background: rgba(245, 158, 11, 0.06);
}

/* Slide-up entrance for cards */
@keyframes slide-up {
  from { transform: translateY(16px); opacity: 0; }
  to   { transform: translateY(0); opacity: 1; }
}
.slide-up { animation: slide-up 0.3s ease-out; }

/* Fade in */
@keyframes fade-in {
  from { opacity: 0; }
  to   { opacity: 1; }
}
.fade-in { animation: fade-in 0.4s ease-out; }
```

---

## 4. API Integration Layer

### Base Client

```typescript
// lib/api/client.ts
import axios, { AxiosInstance } from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'https://api.neongambit.com/v1';

export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE,
  timeout: 15000, // Hostinger VPS is always-on — no cold start delays
  headers: { 'Content-Type': 'application/json' },
});

// Inject auth token on every request
apiClient.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = sessionStorage.getItem('ng_token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth expiry
apiClient.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) {
      sessionStorage.removeItem('ng_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Polling utility — for async backend jobs (Lichess import, Glitch Report generation)
export const pollUntilDone = async <T>(
  fetchFn: () => Promise<{ data: { status: string } & T }>,
  isDone: (data: { status: string } & T) => boolean,
  intervalMs = 2000,
  maxAttempts = 30
): Promise<{ status: string } & T> => {
  for (let i = 0; i < maxAttempts; i++) {
    const { data } = await fetchFn();
    if (isDone(data)) return data;
    await new Promise(r => setTimeout(r, intervalMs));
  }
  throw new Error('Job timed out');
};
```

### Auth API

```typescript
// lib/api/auth.ts
import { apiClient } from './client';

export interface TokenResponse { access_token: string; token_type: 'bearer'; }

export const loginGuest = () =>
  apiClient.post<TokenResponse>('/auth/guest', {});

export const loginFirebase = (firebaseToken: string) =>
  apiClient.post<TokenResponse>('/auth/validate', { firebase_token: firebaseToken });

export const linkAccount = (firebaseToken: string) =>
  apiClient.post<TokenResponse>('/auth/link-account', { firebase_token: firebaseToken });
```

### Lichess & Glitch Report API

```typescript
// lib/api/lichess.ts
import { apiClient, pollUntilDone } from './client';

export interface ImportJobStatus {
  job_id: string;
  status: 'processing' | 'done' | 'error';
  games_imported?: number;
  message: string;
}

export const startImport = (lichessUsername: string, maxGames: number = 50) =>
  apiClient.post<ImportJobStatus>('/lichess/import', { lichess_username: lichessUsername, max_games: maxGames });

export const getImportStatus = (jobId: string) =>
  apiClient.get<ImportJobStatus>(`/lichess/import/status?job_id=${jobId}`);

export const waitForImport = (jobId: string) =>
  pollUntilDone(
    () => getImportStatus(jobId),
    (data) => data.status === 'done' || data.status === 'error',
    2500, 30
  );

export const getLichessRating = () =>
  apiClient.get<{ rating: number; rating_type: string; fetched_at: string }>('/user/lichess-rating');
```

```typescript
// lib/api/glitchReport.ts
import { apiClient, pollUntilDone } from './client';

export interface CriticalOpening {
  eco_code: string;
  opening_name: string;
  games: number;
  wins: number;
  losses: number;
  win_rate: number;
  avg_collapse_move: number;
  collapse_type: 'opening_error' | 'tactical_blunder' | 'positional_drift' | 'time_pressure' | null;
  neon_diagnosis: string;
  is_critical: boolean;
  linked_opening_id: string | null;
  training_unlocked: boolean;  // Free: top 2, Pro: all
}

export interface GlitchReport {
  id: string;
  games_analyzed: number;
  rating_at_generation: number;
  generated_at: string;
  source: 'lichess' | 'sessions';
  critical_openings: CriticalOpening[];
  strengths: { eco_code: string; opening_name: string; games: number; win_rate: number }[];
  overall_pattern: string;
}

export interface GenerateJobStatus {
  job_id: string;
  status: 'processing' | 'done' | 'error';
  message: string;
}

export const generateGlitchReport = () =>
  apiClient.post<GenerateJobStatus>('/glitch-report/generate');

export const getGenerateStatus = (jobId: string) =>
  apiClient.get<GenerateJobStatus & { report?: GlitchReport }>(`/glitch-report/status?job_id=${jobId}`);

export const waitForGlitchReport = (jobId: string) =>
  pollUntilDone(
    () => getGenerateStatus(jobId),
    (data) => data.status === 'done' || data.status === 'error',
    3000, 20
  );

export const getCurrentReport = () =>
  apiClient.get<GlitchReport>('/glitch-report/current');
```

### Sparring Sessions API

```typescript
// lib/api/sessions.ts
import { apiClient } from './client';

export type MoveQuality = 'excellent' | 'good' | 'inaccuracy' | 'mistake' | 'blunder';

export interface SparringSession {
  id: string;
  current_fen: string;
  player_color: 'white' | 'black';
  opponent_elo: number;
  opening_name: string;
  session_status: 'active' | 'completed' | 'abandoned';
  accuracy_score: number;
  theory_integrity: number;
  theory_exit_move: number | null;
  move_history: MoveRecord[];
  neon_intro: string;
}

export interface MoveRecord {
  move: string; from: string; to: string; san: string;
  quality: MoveQuality; eval_cp: number; timestamp: string;
}

export interface MoveResponse {
  valid: boolean;
  new_fen?: string;
  theory_integrity?: number;
  theory_exit_detected?: boolean;
  theory_exit_move?: number;
  out_of_book?: boolean;
  coach_message?: string | null;  // Template-driven, instant from server
  error?: string;
  legal_moves?: string[];
  // NOTE: move_quality and evaluation are NOT in server response.
  // Move quality is evaluated CLIENT-SIDE via stockfish.wasm. See Section 7.
}

export interface OpponentMoveResponse {
  move: { from: string; to: string; san: string; uci: string };
  new_fen: string;
  thinking_time_ms: number;
  out_of_book: boolean;
  source: 'lichess_cache' | 'lichess_api' | 'fallback';
}

export interface SessionReview {
  session: SparringSession;
  move_analyses: Array<{
    move_number: number; fen_before: string; move_quality: MoveQuality;
    coach_text: string; eval_before: number; eval_after: number;
  }>;
  summary: {
    opening_accuracy: number; theory_exit_move: number | null;
    turning_point_move: number | null; neon_debrief: string;
  };
}

export const createSession = (data: {
  opening_id: string; player_color: 'white' | 'black'; opponent_elo: number;
}) => apiClient.post<SparringSession>('/sessions', data);

export const makeMove = (sessionId: string, move: {
  from: string; to: string; promotion?: string | null;
  prev_move_quality?: MoveQuality | null;
  prev_move_eval_cp?: number | null;
}) => apiClient.post<MoveResponse>(`/sessions/${sessionId}/moves`, move);

export const getOpponentMove = (sessionId: string) =>
  apiClient.post<OpponentMoveResponse>(`/sessions/${sessionId}/opponent-move`);

export const resignSession = (sessionId: string) =>
  apiClient.post(`/sessions/${sessionId}/resign`);

export const getSessionHistory = (limit = 10, offset = 0) =>
  apiClient.get<SparringSession[]>(`/sessions/history?limit=${limit}&offset=${offset}`);
```

### Neural Drill API

```typescript
// lib/api/drill.ts
import { apiClient } from './client';

export interface DrillCard {
  opening_id: string;
  opening_name: string;
  move_number: number;
  expected_move: string;
  fen_before_move: string;
  move_sequence_hash: string;
  repetitions: number;
  correct_count: number;
}

export interface MasteryProgress {
  opening_id: string; opening_name: string;
  total_moves: number; mastered_moves: number; mastery_percent: number;
  next_due_at: string | null;
}

export const getDrillQueue = (limit = 8) =>
  apiClient.get<DrillCard[]>(`/drill/queue?limit=${limit}`);

export const getDrillQueueCount = () =>
  apiClient.get<{ count: number }>('/drill/queue/count');

export const recordDrillReview = (data: {
  opening_id: string; move_sequence_hash: string;
  quality: 0 | 1 | 2 | 3 | 4 | 5; move_number: number;
}) => apiClient.post('/drill/review', data);

export const getOpeningMastery = (openingId: string) =>
  apiClient.get<MasteryProgress>(`/drill/mastery/${openingId}`);
```

### Analytics API

```typescript
// lib/api/analytics.ts
import { apiClient } from './client';

export interface DashboardData {
  lichess_rating: {
    current: number; delta_30_day: number;
    trend: number[];
  } | null;
  this_week: {
    sessions: number; drill_cards_reviewed: number;
    win_rate: number; avg_accuracy: number;
  };
  opening_improvements: Array<{
    eco_code: string; opening_name: string;
    baseline_win_rate: number; current_win_rate: number;
    delta: number; status: 'improving' | 'stable' | 'declining';
  }>;
  drill_queue_count: number;
  streak: number;
  tilt_detected: boolean;
  has_glitch_report: boolean;
  critical_opening_count: number;
  recommended_session: {
    opening_id: string; opening_name: string; reason: string;
  } | null;
  estimated_drill_minutes: number;
}

export const getDashboard = () =>
  apiClient.get<DashboardData>('/analytics/dashboard');

export const getRatingTrend = () =>
  apiClient.get<{ snapshots: Array<{ rating: number; snapshotted_at: string }> }>('/analytics/rating-trend');
```

---

## 5. State Management

### Auth Store

```typescript
// lib/store/useAuthStore.ts
import { create } from 'zustand';
import * as authApi from '@/lib/api/auth';

interface User {
  id: string; email?: string; lichess_username?: string | null;
  target_elo: number; is_pro: boolean; play_style: string | null;
}

interface AuthState {
  token: string | null; user: User | null;
  isGuest: boolean; isLoading: boolean;
  hasLichessAccount: boolean;
  loginAsGuest: () => Promise<void>;
  loginWithFirebase: (token: string) => Promise<void>;
  setUser: (user: User) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: typeof window !== 'undefined' ? sessionStorage.getItem('ng_token') : null,
  user: null, isGuest: true, isLoading: false, hasLichessAccount: false,

  loginAsGuest: async () => {
    set({ isLoading: true });
    const { data } = await authApi.loginGuest();
    sessionStorage.setItem('ng_token', data.access_token);
    set({ token: data.access_token, isGuest: true, isLoading: false });
  },

  loginWithFirebase: async (firebaseToken) => {
    set({ isLoading: true });
    const { data } = await authApi.loginFirebase(firebaseToken);
    sessionStorage.setItem('ng_token', data.access_token);
    set({ token: data.access_token, isGuest: false, isLoading: false });
  },

  setUser: (user) => set({ user, hasLichessAccount: !!user.lichess_username }),

  logout: () => {
    sessionStorage.removeItem('ng_token');
    set({ token: null, user: null, isGuest: true });
  },
}));
```

### Session Store (Active Sparring)

```typescript
// lib/store/useSessionStore.ts
import { create } from 'zustand';
import type { MoveQuality } from '@/lib/api/sessions';

interface SessionState {
  sessionId: string | null;
  fen: string;
  moveHistory: string[];
  coachMessage: string;
  lastMoveQuality: MoveQuality | null;
  theoryIntegrity: number;
  theoryExitMove: number | null;
  evalScore: number;
  isOutOfBook: boolean;
  isThinking: boolean;
  isBlunderGlitch: boolean;
  isSurvivalMode: boolean;

  // Actions
  startSession: (sessionId: string, fen: string, neonIntro: string) => void;
  applyMoveResult: (result: {
    fen: string; quality: MoveQuality; integrity: number;
    evalCp: number; theoryExit?: boolean; theoryExitMove?: number;
    outOfBook?: boolean; coachMsg?: string | null;
  }) => void;
  applyOpponentMove: (fen: string, outOfBook: boolean) => void;
  setCoachMessage: (msg: string) => void;
  setThinking: (v: boolean) => void;
  triggerBlunderGlitch: () => void;
  activateSurvivalMode: () => void;
  resetSession: () => void;
}

const NEON_STANDBY = '> NEON ONLINE. Neural link established.';

export const useSessionStore = create<SessionState>((set) => ({
  sessionId: null, fen: 'start', moveHistory: [], coachMessage: NEON_STANDBY,
  lastMoveQuality: null, theoryIntegrity: 100, theoryExitMove: null,
  evalScore: 0, isOutOfBook: false, isThinking: false,
  isBlunderGlitch: false, isSurvivalMode: false,

  startSession: (sessionId, fen, neonIntro) =>
    set({ sessionId, fen, coachMessage: `> NEON: "${neonIntro}"`, theoryIntegrity: 100 }),

  applyMoveResult: ({ fen, quality, integrity, evalCp, theoryExit, theoryExitMove, outOfBook, coachMsg }) =>
    set((s) => ({
      fen, lastMoveQuality: quality, theoryIntegrity: integrity, evalScore: evalCp,
      theoryExitMove: theoryExitMove ?? s.theoryExitMove,
      isOutOfBook: outOfBook ?? s.isOutOfBook,
      coachMessage: coachMsg ? `> NEON: "${coachMsg}"` : s.coachMessage,
    })),

  applyOpponentMove: (fen, outOfBook) =>
    set((s) => ({ fen, isOutOfBook: outOfBook, isSurvivalMode: outOfBook || s.isSurvivalMode })),

  setCoachMessage: (coachMessage) => set({ coachMessage }),
  setThinking: (isThinking) => set({ isThinking }),

  triggerBlunderGlitch: () => {
    set({ isBlunderGlitch: true });
    setTimeout(() => set({ isBlunderGlitch: false }), 350);
  },

  activateSurvivalMode: () => set({ isSurvivalMode: true }),

  resetSession: () => set({
    sessionId: null, fen: 'start', moveHistory: [], coachMessage: NEON_STANDBY,
    lastMoveQuality: null, theoryIntegrity: 100, theoryExitMove: null,
    evalScore: 0, isOutOfBook: false, isThinking: false,
    isBlunderGlitch: false, isSurvivalMode: false,
  }),
}));
```

### Drill Store

```typescript
// lib/store/useDrillStore.ts
import { create } from 'zustand';
import type { DrillCard } from '@/lib/api/drill';
import * as drillApi from '@/lib/api/drill';

interface DrillState {
  queue: DrillCard[]; currentIndex: number;
  currentCard: DrillCard | null;
  isLoading: boolean; isComplete: boolean;
  showShadow: boolean; lastResult: 'correct' | 'incorrect' | null;
  load: () => Promise<void>;
  markCorrect: () => Promise<void>;
  markIncorrect: () => Promise<void>;
  showHint: () => void;
  skip: () => void;
}

export const useDrillStore = create<DrillState>((set, get) => ({
  queue: [], currentIndex: 0, currentCard: null,
  isLoading: false, isComplete: false,
  showShadow: false, lastResult: null,

  load: async () => {
    set({ isLoading: true });
    const { data } = await drillApi.getDrillQueue(8);
    set({ queue: data, currentCard: data[0] ?? null, currentIndex: 0, isLoading: false, isComplete: !data.length });
  },

  markCorrect: async () => {
    const { currentCard } = get();
    if (!currentCard) return;
    set({ lastResult: 'correct' });
    await drillApi.recordDrillReview({
      opening_id: currentCard.opening_id,
      move_sequence_hash: currentCard.move_sequence_hash,
      quality: get().showShadow ? 3 : 5, // Shadow hint used = quality 3
      move_number: currentCard.move_number,
    });
    setTimeout(() => get()._advance(), 800);
  },

  markIncorrect: async () => {
    const { currentCard } = get();
    if (!currentCard) return;
    set({ lastResult: 'incorrect' });
    await drillApi.recordDrillReview({
      opening_id: currentCard.opening_id,
      move_sequence_hash: currentCard.move_sequence_hash,
      quality: 1,
      move_number: currentCard.move_number,
    });
    setTimeout(() => get()._advance(), 1500);
  },

  showHint: () => set({ showShadow: true }),

  skip: () => get()._advance(),

  _advance: () => {
    const { queue, currentIndex } = get();
    const next = currentIndex + 1;
    set({ currentIndex: next, currentCard: queue[next] ?? null, isComplete: next >= queue.length, showShadow: false, lastResult: null });
  },
} as DrillState & { _advance: () => void }));
```

---

## 6. Screen Specifications

### 6.1 Splash / Boot Screen

**File:** `app/page.tsx`

**Logic:**
1. Check `sessionStorage.getItem('ng_token')`
2. If token → call `GET /user/profile` to validate
3. If valid → `router.push('/')` (dashboard)
4. If invalid / missing → `POST /auth/guest` → store token → `router.push('/')`
5. If any request takes >2s → show `<SystemBoot>` overlay

```typescript
// app/page.tsx
'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { SystemBoot } from '@/components/shared/SystemBoot';
import { useAuthStore } from '@/lib/store/useAuthStore';
import * as authApi from '@/lib/api/auth';
import * as userApi from '@/lib/api/user';

export default function SplashPage() {
  const router = useRouter();
  const { loginAsGuest, setUser } = useAuthStore();
  const [showBoot, setShowBoot] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setShowBoot(true), 2000);

    const init = async () => {
      try {
        const token = sessionStorage.getItem('ng_token');
        if (token) {
          const { data: user } = await userApi.getProfile();
          setUser(user);
        } else {
          await loginAsGuest();
        }
        clearTimeout(timer);
        router.push('/dashboard');
      } catch {
        await loginAsGuest();
        clearTimeout(timer);
        router.push('/dashboard');
      }
    };

    init();
    return () => clearTimeout(timer);
  }, []);

  if (showBoot) return <SystemBoot onComplete={() => {}} />;
  return <div className="min-h-screen bg-void" />;
}
```

---

### 6.2 Mission Control (Home)

**File:** `app/(main)/page.tsx` — API: `GET /analytics/dashboard`

This is the emotional anchor of the app. It shows the user's progress at a glance and makes the training feel personal and alive. Single API call on mount loads everything.

**Layout:**
```
┌────────────────────────────────────────────┐
│  🔥 Streak: 5    ╔══════════╗   [Settings]  │
│                  ║  1,387   ║               │
│                  ║  +47 mo  ║  Lichess ELO  │
│                  ╚══════════╝               │
├────────────────────────────────────────────┤
│  ── OPENING PROGRESS ──────────────────    │
│  Sicilian  ▓▓▓▓▓▓▓▓░░  41% (+19%) 📈       │
│  Ruy Lopez ▓▓▓▓▓░░░░░  31% (–2%)  ─        │
│  [View Full Glitch Report]                  │
├────────────────────────────────────────────┤
│  ── TODAY'S DRILL ─────────────────────    │
│  7 moves due · Est. 6 min                  │
│  [▶ START DRILL]                           │
├────────────────────────────────────────────┤
│  ── RECOMMENDED SESSION ───────────────    │
│  Sparring · Sicilian at 1400 ELO           │
│  "Your weakest opening this week"          │
│  [▶ START SPARRING]                        │
├────────────────────────────────────────────┤
│  [⚔ ARENA]      [🧠 DRILL]      [👤 PROFILE] │
└────────────────────────────────────────────┘
```

**Tilt Intervention — shown INSTEAD of "Play Again" after 3rd consecutive sparring loss:**
```
┌──────────────────────────────────────────┐
│  ╔══════════════════════════════════╗    │
│  ║ > NEON: "Three losses in 22min. ║    │
│  ║   The position data looks fine. ║    │
│  ║   This is pattern, not tactics. ║    │
│  ║   Switch to Drill — reset."     ║    │
│  ╚══════════════════════════════════╝    │
│                                          │
│  [▶ GO TO DRILL]    [Play anyway]        │
└──────────────────────────────────────────┘
```

**Tilt implementation (`useSessionStore` addition):**
```typescript
// After session ends with result='loss', check tilt from dashboard data
const { data } = await getDashboard();
if (data.tilt_detected) {
  setShowTiltIntervention(true);  // Shows the NEON intervention instead of Play Again
} else {
  setShowPlayAgain(true);
}
```

**Emotional design rules:**
- The Lichess ELO box is the first thing the eye lands on. It should have a subtle cyan glow. The delta `+47` is emerald green when positive, magenta when negative.
- Opening progress rows must show both directions: improving (emerald + arrow up), declining (amber + dash), stable (gray).
- The drill queue IS the daily mission in MVP. No separate mission card needed.
- Tilt intervention: shown full-width, NEON terminal styling. "Play anyway" is a small secondary button — present but not emphasized.
- If no Lichess account connected: replace ELO box with a pulsing "Connect Lichess" CTA.
- If no Glitch Report yet: replace opening progress section with "Scan Your Games" button.

**State logic:**
```typescript
// Unified dashboard fetch on mount
const [data, setData] = useState<DashboardData | null>(null);
useEffect(() => {
  getDashboard().then(({ data }) => setData(data));
}, []);
```

**Updated `DashboardData` type (add to `lib/api/analytics.ts`):**
```typescript
export interface DashboardData {
  lichess_rating: { current: number; delta_30_day: number; trend: number[] } | null;
  this_week: { sessions: number; drill_cards_reviewed: number; win_rate: number; avg_accuracy: number };
  opening_improvements: OpeningImprovement[];
  drill_queue_count: number;
  streak: number;
  tilt_detected: boolean;
  has_glitch_report: boolean;
  critical_opening_count: number;
  recommended_session: { opening_id: string; opening_name: string; reason: string } | null;
  estimated_drill_minutes: number;
}
```

---

### 6.3 Lichess Connect & Import

**Trigger:** CTA from Mission Control, or post-game `<LichessConnectPrompt>`.

**File:** Modal / bottom sheet — not a full page. Lives as `components/shared/LichessConnectPrompt.tsx`

**Design principle:** This is a conversion moment. The user must feel what they're about to get, not just see a form.

**UI flow:**

```
Step 1 — The Promise:
┌──────────────────────────────────────────┐
│  ⚡ CONNECT YOUR LICHESS ACCOUNT          │
│                                          │
│  NeonGambit will analyze your last       │
│  50 games and tell you exactly why       │
│  you keep losing the same openings.      │
│                                          │
│  No password needed — read-only access.  │
│                                          │
│  Username: [___________________]         │
│                                          │
│  [SCAN MY GAMES]                         │
└──────────────────────────────────────────┘

Step 2 — The Processing (LoadingTerminal):
┌──────────────────────────────────────────┐
│  > CONNECTING TO LICHESS NODES...        │
│  > FETCHING 50 GAMES...                  │
│  > ANALYZING @username...                │
│  > CALCULATING WIN RATES...              │
│  > IDENTIFYING PATTERNS...              │
│  > GENERATING NEON DIAGNOSIS...         │
│  > COMPLETE. LOADING REPORT.            │
└──────────────────────────────────────────┘
```

**Implementation:**
```typescript
const handleConnect = async (username: string) => {
  setStep('processing');

  // Step 1: Import games
  const { data: importJob } = await startImport(username, 50);
  await waitForImport(importJob.job_id);

  // Step 2: Generate Glitch Report
  const { data: reportJob } = await generateGlitchReport();
  await waitForGlitchReport(reportJob.job_id);

  // Step 3: Reveal
  router.push('/glitch-report');
};
```

**Post-game trigger timing:** Show `<LichessConnectPrompt>` after the user's first session ends. Specifically: if the session result is a loss OR the user spent >5 minutes playing. This is the moment of maximum emotional receptivity.

---

### 6.4 Glitch Report Reveal

**File:** `app/(main)/glitch-report/page.tsx`

**This is the product's most important moment. Design it accordingly.**

The reveal must feel cinematic — like a security scan completing and exposing vulnerabilities. Data should appear line by line, not all at once.

**Reveal sequence (orchestrated by `useGlitchReveal` hook):**

```
0ms    — Screen fades in from black. Header: "⚡ GLITCH REPORT — @username" types out.
500ms  — "Analyzed 47 games · Rapid 1340 ELO" appears.
1000ms — Section header: "── CRITICAL VULNERABILITIES ──" flickers in (red).
1500ms — First critical opening card slides up with red left border. Win rate bar fills left to right.
2000ms — NEON diagnosis types out letter by letter.
2500ms — Second critical opening card slides up.
3200ms — Section header: "── CONVERSION FAILURES ──" flickers in (amber). Distinct from red.
3700ms — Conversion failure card slides up. Count breakdown appears line by line.
4200ms — Win rate projection and ELO range fade in.
4700ms — "── STRENGTHS ──" section appears in emerald.
5200ms — "── YOUR PATTERN ──" block appears. NEON's overall diagnosis types out.
5800ms — CTA buttons appear: [▶ DRILL YOUR WEAKEST NOW] [VIEW FULL REPORT]
```

**Full screen layout after reveal:**
```
┌──────────────────────────────────────────────────────────┐
│  ⚡ GLITCH REPORT                          @username      │
│  47 games analyzed · Rapid 1,340 ELO                     │
├──────────────────────────────────────────────────────────┤
│  ── CRITICAL VULNERABILITIES ──────────────────────────  │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ ██  SICILIAN DEFENSE (B70)                          │ │
│  │     Win Rate ▓▓░░░░░░░░  22% (18 games)            │ │
│  │     Avg collapse: move 9                            │ │
│  │     "You reach a solid position then collapse       │ │
│  │      at move 9. The Nd5 response is your           │ │
│  │      blind spot."                                  │ │
│  │     [▶ DRILL THIS OPENING]                         │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ █  RUY LOPEZ — Berlin (C67)                         │ │
│  │    Win Rate ▓▓▓░░░░░░░  31% (13 games)             │ │
│  │    "Fine in theory. Lost when they deviated."      │ │
│  │    [▶ PRACTICE DEVIATIONS]                         │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                          │
│  [3 more critical openings — Unlock with Pro ▒▒▒▒▒]     │  ← blurred for free tier
├──────────────────────────────────────────────────────────┤
│  ── CONVERSION FAILURES ───────────────────────────────  │  ← amber header
│  ┌─────────────────────────────────────────────────────┐ │
│  │  You had a winning position in 11 of 47 games.     │ │
│  │  You converted 3. You dropped 8.                   │ │
│  │                                                    │ │
│  │  King + pawn endings:  6  ← dominant pattern       │ │
│  │  Rook endings:          1                          │ │
│  │  Middlegame conversion: 1                          │ │
│  │                                                    │ │
│  │  "You're losing the technical game, not the        │ │
│  │   tactical one. King + pawn technique is your      │ │
│  │   highest-ROI fix."                                │ │
│  │                                                    │ │
│  │  Converting half → win rate 48%→57%               │ │
│  │  Roughly +60 to +80 ELO over time. (Approx.)      │ │
│  │                                                    │ │
│  │  [▶ DRILL YOUR DROPPED ENDGAMES]                   │ │
│  └─────────────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────────────┤
│  ── STRENGTHS TO BUILD ON ─────────────────────────────  │
│  ✅ Italian Game     67%  (15 games) — Keep playing this │
│  ✅ Queen's Gambit   58%  (8 games)                      │
├──────────────────────────────────────────────────────────┤
│  ── YOUR PATTERN ──────────────────────────────────────  │
│  "You play solid theory through move 8. The middlegame  │
│   transition is costing you. Sparring past move 10      │
│   will expose and fix the pattern."                     │
├──────────────────────────────────────────────────────────┤
│  [⚔ DRILL YOUR WEAKEST NOW]  [↩ BACK TO MISSION CONTROL] │
└──────────────────────────────────────────────────────────┘
```

**`ConversionFailureCard` component (new):**
- Amber left border (3px) — distinct from the red/magenta of critical openings
- Win count breakdown renders as small horizontal bars per type
- ELO projection always shown as a range ("~60 to +80") with "(Approx.)" suffix — never a single number
- Disclaimer text in `textMuted` color below the projection
- Free tier: shows full breakdown but hides individual game positions (shown as `▒▒▒▒▒`)
- Pro: "See the Positions" button reveals each specific game date and FEN

**`CriticalOpeningCard` component:**
- Red left border (3px) with magenta glow
- Win rate bar fills from 0% with a 600ms ease animation
- `neon_diagnosis` text types out with `useTypewriter`
- Background: `surface` with subtle magenta glow on hover

**Free tier display (v5.1):** ALL critical openings are visible with full stats, collapse type, and NEON diagnosis. The difference: only the top 2 openings have `training_unlocked: true`. The 3rd+ openings show a lock icon on the "DRILL THIS" CTA button, not on the card itself. The user sees the full problem; Pro unlocks the full solution.

**`CriticalOpeningCard` component:**
- Left border color: red (3px) with magenta glow
- **Collapse type badge**: small label below win rate showing the dominant collapse type:
  - `TACTICAL BLUNDER` → red badge
  - `POSITIONAL DRIFT` → amber badge
  - `OPENING ERROR` → magenta badge
  - `TIME PRESSURE` → gray badge
- Win rate bar fills from 0% with a 600ms ease animation
- `neon_diagnosis` text types out with `useTypewriter`
- If `training_unlocked: false` → CTA button shows lock icon: "[🔒 DRILL THIS — Pro]"
- If `training_unlocked: true` → CTA button: "[▶ DRILL THIS NOW]"

---

### 6.5 The Arena (Sparring Session)

**File:** `app/(main)/arena/page.tsx`

**The full game loop is described in Master Guide Feature 2. This section specifies the UI implementation.**

**Pre-session selector (MVP — simplified, no browse):**
```
┌──────────────────────────────────────────┐
│  ── SELECT MISSION ─────────────────     │
│                                          │
│  OPENING (from your Glitch Report)       │
│  [Sicilian Defense ⚠ weak]  ← recommended │
│  [Ruy Lopez — Berlin  ⚠ weak]           │
│  [🔒 Queen's Gambit — Unlock Pro]        │
│                                          │
│  Or: [Let NeonGambit pick]               │
│                                          │
│  OPPONENT ELO                            │
│  [800] [1000] [1200] ●[1400] [1600]     │
│                                          │
│  COLOR    ●[White] [Black] [Random]      │
│                                          │
│  [⚔ START SPARRING]                      │
└──────────────────────────────────────────┘
```

Note: In MVP, the opening list comes from the user's auto-assigned repertoire (top critical openings from Glitch Report). No "Browse All" — that's Phase 2 Repertoire Builder.

**In-session layout (mobile portrait):**
```
┌─────────────────────────────────────────────┐
│  ← Exit        ARENA         Acc: 87%        │
│  THEORY ████████░░░░  73%  ⚠ Exit: move 9   │  ← TheoryBar
├─────────────────────────────────────────────┤
│ │                                            │
│ │   ┌──────────────────────────────────┐    │
│Eval│  │                                │    │
│Gauge│  │        CHESSBOARD              │    │
│ │   │   cyberpunk square colors        │    │
│ │   │                                  │    │
│ │   └──────────────────────────────────┘    │
├─────────────────────────────────────────────┤
│  ╔══════════════════════════════════════╗   │
│  ║ > NEON: "You're off-book at move 9. ║   │  ← NeonTerminal
│  ║   This is your critical zone.       ║   │
│  ╚══════════════════════════════════════╝   │
├─────────────────────────────────────────────┤
│  [💡 Hint]      [📊 Analyze]    [🏳 Resign]  │
└─────────────────────────────────────────────┘
```

**Survival Mode (amber state):**
- Background of the eval gauge area shifts to amber tint
- `<SurvivalBanner>` slides down from top: "SURVIVAL MODE — Opponent off-book"
- Theory bar freezes (stops draining — theory no longer applies)
- NEON: "Non-standard move. Don't panic. What's the threat?"

**Key game loop logic:**

```typescript
const handlePlayerMove = async (from: string, to: string) => {
  const { fen, sessionId, applyMoveResult, setThinking, triggerBlunderGlitch, activateSurvivalMode } = useSessionStore.getState();
  const { evaluate } = useStockfish(); // Client-side stockfish.wasm hook

  // 1. Optimistic update
  const optimisticFen = calcOptimisticFen(fen, from, to);
  useSessionStore.setState({ fen: optimisticFen });
  playSound('move');
  haptic(40);

  // 2. Client-side eval (stockfish.wasm — runs in Web Worker, non-blocking)
  // Evaluate position BEFORE the move to determine move quality
  const evalBefore = await evaluate(fen, 12);        // depth 12 client-side
  const evalAfter = await evaluate(optimisticFen, 12);
  const quality = classifyMoveQuality(evalBefore.score_cp, evalAfter.score_cp);

  // 3. Server validation (sends prev move quality for stats tracking)
  setThinking(true);
  const { data: move } = await makeMove(sessionId!, {
    from, to,
    prev_move_quality: quality,
    prev_move_eval_cp: evalAfter.score_cp,
  });

  if (!move.valid) {
    useSessionStore.setState({ fen }); // revert
    useSessionStore.getState().setCoachMessage(`> SYSTEM: ${move.error}`);
    setThinking(false);
    return;
  }

  // 4. Apply result (theory + coaching from server, eval from client)
  applyMoveResult({
    fen: move.new_fen!, quality,
    integrity: move.theory_integrity!, evalCp: evalAfter.score_cp,
    theoryExit: move.theory_exit_detected, theoryExitMove: move.theory_exit_move,
    outOfBook: move.out_of_book, coachMsg: move.coach_message,
  });

  if (quality === 'blunder') { triggerBlunderGlitch(); playSound('blunder-glitch'); haptic([100, 50, 100]); }
  if (quality === 'excellent') { playSound('excellent'); }

  // 5. Opponent response (with human-like delay)
  const { data: opp } = await getOpponentMove(sessionId!);
  await delay(Math.min(opp.thinking_time_ms, 1800));
  useSessionStore.getState().applyOpponentMove(opp.new_fen, opp.out_of_book);
  if (opp.out_of_book) activateSurvivalMode();
  playSound(opp.move.san.includes('x') ? 'capture' : 'move');
  haptic(30);

  setThinking(false);
};

// Move quality classification (same thresholds as Master Guide)
function classifyMoveQuality(evalBeforeCp: number, evalAfterCp: number): MoveQuality {
  const cpLoss = Math.abs(evalBeforeCp - evalAfterCp);
  if (cpLoss <= 0) return 'excellent';
  if (cpLoss <= 25) return 'good';
  if (cpLoss <= 75) return 'inaccuracy';
  if (cpLoss <= 150) return 'mistake';
  return 'blunder';
}
```

**After a blunder — Retry prompt (Pro):**
```
┌──────────────────────────────────────────┐
│  ⚠ BLUNDER DETECTED                      │
│  That gives them a passed pawn.          │
│                                          │
│  [↩ RETRY FROM THIS POSITION]  (Pro)     │
│  [CONTINUE GAME]                         │
└──────────────────────────────────────────┘
```

---

### 6.6 Session Debrief (Summary — MVP)

**File:** `app/(main)/debrief/[sessionId]/page.tsx`
**API:** `GET /sessions/{id}` (session data already available from store; no separate review endpoint in MVP)

This screen appears after every session ends. MVP shows a summary card only — no move-by-move narration (Phase 2).

**Layout:**
```
┌──────────────────────────────────────────┐
│  SESSION DEBRIEF                          │
│  Sicilian Defense · vs 1400 ELO          │
├──────────────────────────────────────────┤
│  RESULT: LOSS      Accuracy: 74%         │
│  Theory exit: move 9  (your typical zone)│
├──────────────────────────────────────────┤
│  MOVE QUALITY BREAKDOWN                   │
│  [●●●●●●●●●●●●●●●●●] ← MoveTimeline     │
│  Excellent: 3  Good: 8  Inaccuracy: 2   │
│  Mistakes: 1   Blunders: 1              │
├──────────────────────────────────────────┤
│  > NEON ASSESSMENT:                      │
│  "Your opening was solid through move 9. │
│   Move 14 was the turning point — you   │
│   missed the knight outpost. Consistent │
│   with your Glitch Report pattern."     │
├──────────────────────────────────────────┤
│  [📋 FULL REVIEW]  [↩ DRILL THIS NOW]   │
│  [⚔ PLAY AGAIN]    [← BACK HOME]        │
└──────────────────────────────────────────┘
```

**`MoveTimeline`:** A horizontal row of colored dots (one per move). Tap any dot → jump to that position in Full Review. Dot colors map to `MoveQuality`. The turning point move has a pulsing white ring around it.

**NEON Assessment** must always:
1. Name the move number where things changed ("Move 14 was the turning point")
2. Connect it to their Glitch Report pattern ("Consistent with your Glitch Report")
3. End with a specific action ("Drill this position" or "Spar deeper than move 9")

---

### 6.7 Neural Drill

**File:** `app/(main)/drill/page.tsx`

**Design principle:** Feels like quick practice, not homework. The user completes the queue and feels accomplished in 5–7 minutes.

**Queue screen (before starting):**
```
┌──────────────────────────────────────────┐
│  ← Back        NEURAL DRILL              │
├──────────────────────────────────────────┤
│  DUE TODAY                               │
│  ┌────────────────────────────────────┐  │
│  │ 7 moves due · Est. 6 minutes      │  │
│  │                                    │  │
│  │ Sicilian Def. — moves 8, 9        │  │
│  │ Ruy Lopez Berlin — moves 11,12,14 │  │
│  │ Italian Game — move 7             │  │
│  └────────────────────────────────────┘  │
│                                          │
│  [▶ START DRILL]                         │
├──────────────────────────────────────────┤
│  OPENING MASTERY                         │
│  Sicilian    ◌◌◌◌◌◌◌◌○○  73%            │
│  Ruy Lopez   ◌◌◌◌◌○○○○○  48%            │
│  Italian     ◌◌◌◌◌◌◌◌◌◌  91%            │
└──────────────────────────────────────────┘
```

**Active drill card:**
```
┌──────────────────────────────────────────┐
│  Move 3/7           Sicilian Defense     │
│  Progress: ████░░░░░░  3 of 7           │
├──────────────────────────────────────────┤
│  ┌──────────────────────────────────┐    │
│  │                                  │    │
│  │   [CHESSBOARD]                   │    │
│  │   Position after 1.e4 c5 2.Nf3  │    │
│  │   What's Black's best move?      │    │
│  │                                  │    │
│  └──────────────────────────────────┘    │
├──────────────────────────────────────────┤
│  > NEON: "Find the theoretical move."   │
├──────────────────────────────────────────┤
│  [💡 SHADOW HINT]           [SKIP]       │
└──────────────────────────────────────────┘
```

**After 5s of inactivity → Shadow Move appears:** Ghost of the correct piece rendered at 25% opacity on its target square. The piece silhouette glows faintly cyan.

**Correct answer feedback (800ms display):**
```
┌──────────────────────────────────────────┐
│  ✓ CALCULATED                            │
│  ...d6 is correct.                       │
│  Board shows the move animating.        │
└──────────────────────────────────────────┘
```

**Wrong answer feedback (1500ms display):**
```
┌──────────────────────────────────────────┐
│  ✗ SYSTEM ERROR                          │
│  Correct move: ...d6                     │
│  "This move contests the center and      │
│   prepares Nf6."                         │
│  (Board plays the correct move)          │
└──────────────────────────────────────────┘
```

**Session complete screen:**
```
┌──────────────────────────────────────────┐
│  ⚡ NEURAL SYNC COMPLETE                  │
│  7 moves reviewed · Streak: 5 🔥        │
│  You got 5/7 correct (71%)              │
│                                          │
│  Next review: tomorrow                   │
│  Sicilian move 9 needs 1 more session   │
│                                          │
│  [⚔ SPAR NOW]     [← HOME]             │
└──────────────────────────────────────────┘
```

**SM-2 quality mapping (internal, not shown to user):**
- Correct, no hint used: `quality = 5`
- Correct, shadow hint used: `quality = 3`
- Incorrect, answered after seeing correct: `quality = 1`
- Explicit skip: `quality = 0` (resets interval)

---

### 6.8 Profile & Settings

**File:** `app/(main)/profile/page.tsx`

```
┌──────────────────────────────────────────┐
│  OPERATOR PROFILE                        │
├──────────────────────────────────────────┤
│  @username · ELO 1,387 🔥 Streak: 5     │
│  Play style: Tactical                    │
│  [👑 UPGRADE TO GRANDMASTER]  (if free)  │
├──────────────────────────────────────────┤
│  LICHESS PROGRESS                        │
│  ┌──────────────────────────────────┐    │
│  │   [RATING TREND CHART]           │    │  ← Recharts LineChart, cyan line
│  │   Last 8 weeks · Rapid           │    │
│  └──────────────────────────────────┘    │
├──────────────────────────────────────────┤
│  THIS MONTH                              │
│  Sessions: 24 · Accuracy: 78% avg        │
│  Drills: 142 cards · Win rate: 61%       │
├──────────────────────────────────────────┤
│  SETTINGS                                │
│  Target ELO: ●────────── 1400            │
│  Language: [English ▾] / [Español ▾]     │
│  Lichess: @username  [Re-sync Games]     │
└──────────────────────────────────────────┘
```

**Language selector:** Reads `user.preferred_language` from profile. On change, calls `PATCH /user/profile` with `{ preferred_language: 'es' }` and reloads the locale via `next-intl`'s `useRouter`. All UI strings switch immediately. NEON coaching templates and Glitch Report narratives will use the new locale on next generation.

---

## 7. Stockfish WASM Integration

**This is the key architectural decision that eliminates server CPU costs during sparring. See Master Guide ADR-002.**

### Worker Setup

```typescript
// lib/stockfish/worker.ts
/**
 * Stockfish WASM Web Worker wrapper.
 * Loaded once on first sparring session start. Stays loaded for session duration.
 * Depth capped at 12 client-side (fast enough for real-time, <300ms on modern devices).
 */

let engine: Worker | null = null;
let resolveEval: ((result: { score_cp: number; best_move: string }) => void) | null = null;

export function initStockfish(): Promise<void> {
  return new Promise((resolve) => {
    engine = new Worker('/stockfish/stockfish.js'); // stockfish.wasm loaded by the JS wrapper
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

let lastScoreCp = 0;

export function evaluate(fen: string, depth: number = 12): Promise<{ score_cp: number; best_move: string }> {
  return new Promise((resolve) => {
    if (!engine) throw new Error('Stockfish not initialized');
    resolveEval = resolve;
    engine.postMessage(`position fen ${fen}`);
    engine.postMessage(`go depth ${depth}`);
  });
}

export function terminate() {
  engine?.terminate();
  engine = null;
}
```

### React Hook

```typescript
// lib/stockfish/useStockfish.ts
import { useEffect, useRef, useCallback } from 'react';
import { initStockfish, evaluate as sfEvaluate, terminate } from './worker';

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

### WASM Fallback

If the user's device cannot run WASM (very old browsers), the `useStockfish` hook returns a no-op that skips client-side eval. In this case:
- Move quality is not displayed during the game (the board still works, coaching still fires from templates based on theory tracking)
- The server is NOT called for Stockfish — the feature simply degrades gracefully
- Detection: `if (typeof WebAssembly === 'undefined')` → set `wasmSupported = false`

---

## 8. Component Library

### SystemBoot

```tsx
// components/shared/SystemBoot.tsx
'use client';
import { useEffect, useState } from 'react';

const LOGS = [
  '> INITIALIZING NEON CORE v4.0...',
  '> CONNECTING TO LICHESS NODES...',
  '> LOADING OPENING BOOK [312,441 positions]...',
  '> ESTABLISHING NEURAL LINK...',
  '> SYSTEM ONLINE.',
];

export const SystemBoot = ({ onComplete }: { onComplete: () => void }) => {
  const [lines, setLines] = useState<string[]>([]);

  useEffect(() => {
    let i = 0;
    const id = setInterval(() => {
      setLines(p => [...p, LOGS[i]]);
      i++;
      if (i >= LOGS.length) { clearInterval(id); setTimeout(onComplete, 700); }
    }, 550);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="fixed inset-0 bg-void flex items-center justify-center z-50">
      <div className="font-mono text-sm text-cyan max-w-xs w-full px-6 space-y-2">
        {lines.map((l, i) => (
          <p key={i} className="text-glow-cyan fade-in">{l}</p>
        ))}
        {lines.length < LOGS.length && <span className="animate-pulse text-cyan">█</span>}
      </div>
    </div>
  );
};
```

### NeonTerminal

```tsx
// components/coach/NeonTerminal.tsx
import { useTypewriter } from '@/lib/hooks/useTypewriter';

export const NeonTerminal = ({ message }: { message: string }) => {
  const displayed = useTypewriter(message, 28);
  return (
    <div className="relative glass scanlines rounded p-4 font-mono text-sm text-cyan min-h-[72px] overflow-hidden">
      <span>{displayed}</span>
      <span className="animate-pulse">▋</span>
    </div>
  );
};
```

### LoadingTerminal (for async jobs)

```tsx
// components/shared/LoadingTerminal.tsx
import { useEffect, useState } from 'react';

interface Props { lines: string[]; intervalMs?: number; onComplete?: () => void; }

export const LoadingTerminal = ({ lines, intervalMs = 700, onComplete }: Props) => {
  const [shown, setShown] = useState<string[]>([]);

  useEffect(() => {
    let i = 0;
    const id = setInterval(() => {
      setShown(p => [...p, lines[i]]);
      i++;
      if (i >= lines.length) { clearInterval(id); onComplete?.(); }
    }, intervalMs);
    return () => clearInterval(id);
  }, [lines]);

  return (
    <div className="glass rounded p-6 font-mono text-sm space-y-2 min-h-[200px]">
      {shown.map((l, i) => (
        <p key={i} className={`fade-in ${i === shown.length - 1 ? 'text-cyan text-glow-cyan' : 'text-textSecondary'}`}>
          {l}
        </p>
      ))}
      {shown.length < lines.length && <span className="text-cyan animate-pulse">█</span>}
    </div>
  );
};
```

### NeonChessboard

```tsx
// components/chess/NeonChessboard.tsx
import { Chessboard } from 'react-chessboard';
import { colors } from '@/lib/utils/designTokens';
import { useSessionStore } from '@/lib/store/useSessionStore';

interface Props {
  fen: string;
  orientation: 'white' | 'black';
  onMove?: (from: string, to: string) => void;
  disabled?: boolean;
  shadowSquare?: string | null; // Target square for ghost hint
}

export const NeonChessboard = ({ fen, orientation, onMove, disabled, shadowSquare }: Props) => {
  const { isBlunderGlitch } = useSessionStore();

  const customSquareStyles = shadowSquare
    ? { [shadowSquare]: { backgroundColor: 'rgba(0, 229, 255, 0.25)', boxShadow: `inset 0 0 12px ${colors.cyan}` } }
    : {};

  return (
    <div className={`relative ${isBlunderGlitch ? 'glitch-animation' : ''}`}>
      <Chessboard
        position={fen}
        onPieceDrop={onMove ? (from, to) => { onMove(from, to); return true; } : undefined}
        boardOrientation={orientation}
        arePiecesDraggable={!disabled}
        customDarkSquareStyle={{ backgroundColor: colors.elevated }}
        customLightSquareStyle={{ backgroundColor: colors.surface }}
        customSquareStyles={customSquareStyles}
        customBoardStyle={{
          borderRadius: '4px',
          boxShadow: `0 0 40px ${colors.cyanGlow}`,
        }}
      />
    </div>
  );
};
```

### TheoryBar

```tsx
// components/chess/TheoryBar.tsx
interface Props { integrity: number; exitMove: number | null; }

export const TheoryBar = ({ integrity, exitMove }: Props) => {
  const color = integrity > 60 ? '#00E5FF' : integrity > 30 ? '#F59E0B' : '#E0008C';
  return (
    <div className="w-full">
      <div className="flex justify-between items-center mb-1">
        <span className="font-orbitron text-[10px] text-textMuted tracking-widest">THEORY INTEGRITY</span>
        <div className="flex items-center gap-2">
          {exitMove && <span className="font-mono text-[10px] text-amber">Exit: move {exitMove}</span>}
          <span className="font-mono text-xs" style={{ color }}>{integrity.toFixed(0)}%</span>
        </div>
      </div>
      <div className="h-1.5 rounded-full bg-elevated overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${integrity}%`, backgroundColor: color, boxShadow: `0 0 6px ${color}` }}
        />
      </div>
    </div>
  );
};
```

### MasteryGauge

```tsx
// components/progress/MasteryGauge.tsx
interface Props { percent: number; size?: number; label?: string; }

export const MasteryGauge = ({ percent, size = 52, label }: Props) => {
  const r = size / 2 - 5;
  const circ = 2 * Math.PI * r;
  const offset = circ - (percent / 100) * circ;
  return (
    <div className="flex flex-col items-center gap-1">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="#1E1E35" strokeWidth="3" />
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="#00E5FF" strokeWidth="3"
          strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round"
          transform={`rotate(-90 ${size/2} ${size/2})`}
          style={{ filter: 'drop-shadow(0 0 4px #00E5FF)', transition: 'stroke-dashoffset 0.8s ease' }}
        />
        <text x={size/2} y={size/2 + 4} textAnchor="middle" fill="#F0F0F5"
          fontSize="11" fontFamily="Orbitron" fontWeight="600">
          {percent}%
        </text>
      </svg>
      {label && <span className="font-mono text-[10px] text-textMuted text-center">{label}</span>}
    </div>
  );
};
```

### UpgradeModal

```tsx
// components/shared/UpgradeModal.tsx
interface Props { trigger: string; onClose: () => void; }

export const UpgradeModal = ({ trigger, onClose }: Props) => (
  <div className="fixed inset-0 bg-black/80 flex items-end justify-center z-50 p-4">
    <div className="glass rounded-xl p-6 w-full max-w-md slide-up">
      <div className="font-orbitron text-xs text-violet tracking-widest mb-1">GRANDMASTER TIER</div>
      <h2 className="font-orbitron text-xl text-textPrimary mb-2">Unlock Full Access</h2>
      <p className="font-sans text-sm text-textSecondary mb-4">{trigger}</p>
      <div className="space-y-2 mb-6">
        {['Full Lichess history (200 games)', 'Complete Glitch Report — all openings', 'Move-by-move NEON review', 'Unlimited Neural Drill', 'Retry from any position'].map(f => (
          <div key={f} className="flex items-center gap-2">
            <span className="text-violet text-xs">▸</span>
            <span className="font-sans text-sm text-textSecondary">{f}</span>
          </div>
        ))}
      </div>
      <button className="w-full bg-violet text-white font-orbitron text-sm py-3 rounded-lg shadow-neon-cyan mb-2">
        $4.99 / month  ·  Start Free Trial
      </button>
      <button onClick={onClose} className="w-full text-textMuted font-sans text-sm py-2">
        Not now
      </button>
    </div>
  </div>
);
```

---

## 9. Performance & UX Patterns

### Token Security

```typescript
// Guests: sessionStorage (cleared on tab close — acceptable UX tradeoff)
// Authenticated users: httpOnly cookie via Next.js API route

// app/api/auth/set-cookie/route.ts
import { NextResponse } from 'next/server';
export async function POST(req: Request) {
  const { token } = await req.json();
  const res = NextResponse.json({ ok: true });
  res.cookies.set('ng_token', token, {
    httpOnly: true, secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax', maxAge: 60 * 60 * 24 * 30, // 30 days
  });
  return res;
}
```

### Optimistic Move Updates

```typescript
// lib/utils/chess.ts
import { Chess } from 'chess.js';

export const calcOptimisticFen = (fen: string, from: string, to: string): string => {
  try {
    const chess = new Chess(fen);
    const move = chess.move({ from, to, promotion: 'q' });
    return move ? chess.fen() : fen;
  } catch {
    return fen; // Revert gracefully on invalid FEN
  }
};
```

### Sound & Haptics Hooks

```typescript
// lib/hooks/useAudio.ts
import { Howl } from 'howler';
const sounds = {
  move:            new Howl({ src: ['/sounds/move.mp3'],            volume: 0.6 }),
  capture:         new Howl({ src: ['/sounds/capture.mp3'],         volume: 0.7 }),
  'blunder-glitch':new Howl({ src: ['/sounds/blunder-glitch.mp3'], volume: 0.85 }),
  excellent:       new Howl({ src: ['/sounds/excellent.mp3'],       volume: 0.5 }),
  'mission-complete': new Howl({ src: ['/sounds/mission-complete.mp3'], volume: 0.7 }),
};
export const playSound = (id: keyof typeof sounds) => sounds[id]?.play();

// lib/hooks/useHaptics.ts
export const haptic = (pattern: number | number[]) => {
  if (typeof navigator !== 'undefined' && 'vibrate' in navigator) navigator.vibrate(pattern);
};
```

### useTypewriter Hook

```typescript
// lib/hooks/useTypewriter.ts
import { useState, useEffect } from 'react';

export const useTypewriter = (text: string, msPerChar = 28): string => {
  const [displayed, setDisplayed] = useState('');
  useEffect(() => {
    setDisplayed('');
    let i = 0;
    const id = setInterval(() => {
      setDisplayed(text.slice(0, i + 1));
      i++;
      if (i >= text.length) clearInterval(id);
    }, msPerChar);
    return () => clearInterval(id);
  }, [text, msPerChar]);
  return displayed;
};
```

### usePollJobStatus Hook

```typescript
// lib/hooks/usePollJobStatus.ts
import { useState, useEffect } from 'react';

interface PollState<T> { data: T | null; isDone: boolean; isError: boolean; }

export const usePollJobStatus = <T extends { status: string }>(
  fetchFn: () => Promise<{ data: T }>,
  isComplete: (d: T) => boolean,
  intervalMs = 2500
): PollState<T> => {
  const [state, setState] = useState<PollState<T>>({ data: null, isDone: false, isError: false });

  useEffect(() => {
    let active = true;
    const poll = async () => {
      try {
        const { data } = await fetchFn();
        if (!active) return;
        if (isComplete(data)) {
          setState({ data, isDone: true, isError: false });
        } else {
          setState({ data, isDone: false, isError: false });
          setTimeout(poll, intervalMs);
        }
      } catch {
        if (active) setState(s => ({ ...s, isError: true }));
      }
    };
    poll();
    return () => { active = false; };
  }, []);

  return state;
};
```

---

## 10. Navigation Structure

```
/                      → Splash (instant redirect, no visible UI beyond boot)
/login                 → Login (only when saving progress or subscribing)
/dashboard             → Mission Control (Home)
/glitch-report         → Glitch Report reveal + full view
/arena                 → Sparring session (opens with selector)
/debrief/[sessionId]   → Post-session summary
/drill                 → Neural Drill queue + active drill
/profile               → Stats + settings + language selector
```

### Bottom Navigation (3 tabs — persistent in dashboard layout)

```tsx
// components/shared/BottomNav.tsx
const TABS = [
  { href: '/arena',     label: 'ARENA', icon: '⚔' },
  { href: '/drill',     label: 'DRILL', icon: '🧠', badge: true },
  { href: '/profile',   label: 'OPS',   icon: '👤' },
];
```

**Badge on DRILL tab:** Pulls count from `GET /analytics/dashboard` (`drill_queue_count` field). Shows count if > 0 with a cyan circle badge.

**Mission Control (Home) access:** The dashboard is the default landing after splash. Tapping the NeonGambit logo in the top bar returns to `/dashboard` from any screen.

**Phase 2 routes (not implemented in MVP):**
- `/endgame-drill` — Endgame Drill from conversion failures
- `/repertoire` — Full opening browser + manual repertoire building
- `/review/[sessionId]` — Move-by-move game review with NEON narration

---

## 11. Implementation Phases — Antigravity Mission Plan

Each phase is an **Antigravity Mission** — written as a directive for the Agent Manager. The agent plans, builds, verifies in its embedded Chrome browser, and produces artifacts. No manual compilation steps.

### Mission 0 — Design System Foundation (2h)
```
Task: Initialize Next.js 14 + TypeScript strict + Tailwind + shadcn/ui + next-pwa.
Configure manifest.json: portrait-locked, mobile-first, NeonGambit icons.
Add Google Fonts: Orbitron, JetBrains Mono, Inter.
Create lib/utils/designTokens.ts with all canonical color and typography tokens.
Create tailwind.config.js with all color, font, shadow, and animation extensions.
Create app/globals.css with: .glass, .scanlines, .glitch-animation, .survival-flash,
.text-glow-cyan, .text-glow-magenta, .slide-up, .fade-in utilities.
Set up next-intl with messages/en.json and messages/es.json. Configure locale detection.
Create i18n.ts configuration file.
Verify: npm run build succeeds. Page renders void background with Orbitron font.
Verify: Lighthouse PWA score > 90. Locale switching works.
```

### Mission 1 — Navigation Shell (2h)
```
Task: Create full Next.js App Router directory structure per Section 2.
Create app/(main)/layout.tsx with BottomNav (3 tabs: Arena, Drill, Profile).
Apply bg-void to root layout.
Create stub pages for all MVP routes — each renders a centered placeholder with
the route name in Orbitron font.
Create BottomNav.tsx with active tab highlighting using cyan color.
Install Framer Motion.
Verify: All MVP routes render without 404. BottomNav visible on all (main) routes.
Active tab shows correct highlight.
```

### Mission 2 — API Layer + Auth + Splash + Stockfish WASM (3h)
```
Task: Create all files in lib/api/ (client.ts, auth.ts, sessions.ts, lichess.ts,
glitchReport.ts, repertoire.ts, drill.ts, analytics.ts, user.ts)
exactly as specified in Section 4.
Install Zustand. Create all stores in lib/store/ per Section 5.
Create all hooks in lib/hooks/.
Set up lib/stockfish/worker.ts and lib/stockfish/useStockfish.ts per Section 7.
Place stockfish.wasm in public/stockfish/.
Implement app/page.tsx splash logic per Section 6.1.
Implement SystemBoot component per Section 8.
Verify: Fresh browser session → guest token created → redirected to /dashboard in <3s.
Verify: Stockfish WASM loads in Web Worker and evaluates a test position.
```

### Mission 3 — Lichess Import + Glitch Report Reveal (4h)
```
Task: Implement LichessConnectPrompt component (Section 6.3): username input,
LoadingTerminal during processing, polling with usePollJobStatus hook.
Wire startImport → waitForImport → generateGlitchReport → waitForGlitchReport → router.push('/glitch-report').
Implement full Glitch Report reveal page (Section 6.4):
- useGlitchReveal hook orchestrates the timed reveal sequence
- CriticalOpeningCard with animated win rate bar, typewriter diagnosis, magenta left border
  - Collapse type badge (TACTICAL BLUNDER / POSITIONAL DRIFT / OPENING ERROR / TIME PRESSURE)
  - training_unlocked=false → lock icon on CTA: "[🔒 DRILL THIS — Pro]"
  - training_unlocked=true → "[▶ DRILL THIS NOW]"
- ALL critical openings visible in Free tier (no blurred cards)
- StrengthRow components
- PatternSummary with full-width NEON text
All UI strings use next-intl translation keys — no hardcoded text.
Verify: Enter a real Lichess username → full processing flow → cinematic reveal.
Verify: Cards appear in sequence with correct delays. Win rate bars animate.
Verify: Collapse type badge renders with correct color.
Verify: 3rd+ opening shows lock on CTA, not on card. Switch to Spanish and verify.
```

### Mission 4 — Chess Components + Sparring Arena (5h)
```
Task: Install react-chessboard and chess.js.
Create NeonChessboard, TheoryBar, EvalGauge, NeonTerminal, SurvivalBanner (Section 8).
Create useAudio.ts and useHaptics.ts hooks. Place all 5 sound files in public/sounds/.
Implement full /arena/page.tsx per Section 6.5:
- Pre-session selector (opening from auto-assigned repertoire, ELO, color)
  - No "Browse All" — openings come from Glitch Report auto-assignment
  - Locked openings show lock icon + "Pro" label
- Full game loop per Section 6.5:
  - Client-side eval via useStockfish() hook (stockfish.wasm Web Worker)
  - classifyMoveQuality() from client eval
  - makeMove sends prev_move_quality + prev_move_eval_cp to server
  - Server returns: validity + theory tracking + coach_message (template-driven)
  - Client displays: move quality color + eval gauge + coach message
- Blunder glitch, survival mode, theory exit detection
- Tilt intervention: after session loss, re-fetch dashboard → if tilt_detected, show TiltIntervention
- Resign button
- Post-session redirect to /debrief/[sessionId]
Verify: Full game loop works end-to-end. Illegal move reverts board.
Verify: Blunder triggers chromatic aberration animation. Move quality displays from client eval.
Verify: Opponent responds with human-like delay. Out-of-book triggers amber survival banner.
Verify: 3 consecutive losses → tilt intervention appears with "Go to Drill" + "Play anyway".
```

### Mission 5 — Session Debrief + Neural Drill (4h)
```
Task: Implement /debrief/[sessionId]/page.tsx per Section 6.6:
- Summary card: accuracy, theory integrity, move quality breakdown
- NEON summary text (from session data, not a separate API call)
- Action buttons: [Practice Again] [Go to Drill] [Back to Dashboard]

Implement /drill/page.tsx per Section 6.7:
- Queue screen with opening breakdown and MasteryGauge per opening
- Active drill card: NeonChessboard at position, NEON prompt, Shadow hint after 5s
- Correct/incorrect result overlays with 800ms/1500ms display
- Session complete screen with streak increment message
- Wire useDrillStore to all UI states
All UI strings use next-intl keys.
Verify: Drill queue shows correct count. Shadow hint appears after 5s.
Verify: Correct answer records quality=5, incorrect records quality=1.
Verify: Complete screen shows stats and streak. Spanish locale works.
```

### Mission 6 — Mission Control Dashboard (3h)
```
Task: Implement /dashboard/page.tsx per Section 6.2.
Single GET /analytics/dashboard call on mount — all data from one endpoint.
Components:
- Rating box (cyan glow, delta in emerald/magenta)
- Opening progress rows with directional deltas
- Drill queue section: "{N} moves due · Est. {M} min · [▶ START DRILL]"
- Recommended session: opening name + reason + [▶ START SPARRING]
- Streak badge (flame icon + count)
- [No Lichess account] → large "Connect Lichess" CTA
- [No Glitch Report] → "Scan Your Games" button
Install Recharts. Implement RatingChart for profile screen.
Verify: Dashboard renders in < 1s from single API call.
Verify: No Lichess account → Connect CTA prominent.
Verify: Recommended session navigates to /arena with opening pre-selected.
```

### Mission 7 — Profile + Upgrade + Deploy (3h)
```
Task: Implement /profile/page.tsx per Section 6.8:
- RatingChart (Recharts), stats summary, settings
- Language selector (EN/ES) that patches user profile and reloads locale
- Lichess re-sync button
- Upgrade CTA for free users
Implement UpgradeModal triggered from: locked openings, exceeded drill limit.
Implement LichessConnectPrompt trigger after first session ends (loss or >5 min session).
Push to GitHub main → auto-deploy Vercel.
Run Lighthouse on deployed URL: PWA score > 90, Performance > 75 mobile throttled.
Verify: "Add to Home Screen" works on iOS Safari and Android Chrome.
Verify: Language switch to Spanish works across all screens.
Verify: Full user journey: Splash → Guest → Arena → Lichess Connect → Glitch Report → Drill → Dashboard.
```

---

## 12. Quick Reference: API Endpoints (MVP)

| Action | Method | Endpoint | Auth |
|--------|--------|----------|------|
| Guest login | POST | `/auth/guest` | None |
| Firebase login | POST | `/auth/validate` | None |
| Link account | POST | `/auth/link-account` | Bearer |
| Get profile | GET | `/user/profile` | Bearer |
| Update profile | PATCH | `/user/profile` | Bearer |
| Get Lichess rating | GET | `/user/lichess-rating` | Bearer |
| Start Lichess import | POST | `/lichess/import` | Bearer |
| Import status | GET | `/lichess/import/status?job_id=` | Bearer |
| Generate Glitch Report | POST | `/glitch-report/generate` | Bearer |
| Current Glitch Report | GET | `/glitch-report/current` | Bearer |
| My repertoire | GET | `/repertoire` | Bearer |
| Add to repertoire | POST | `/repertoire` | Bearer |
| Create session | POST | `/sessions` | Bearer |
| Make move | POST | `/sessions/{id}/moves` | Bearer |
| Opponent move | POST | `/sessions/{id}/opponent-move` | Bearer |
| Resign | POST | `/sessions/{id}/resign` | Bearer |
| Session history | GET | `/sessions/history` | Bearer |
| Drill queue | GET | `/drill/queue?limit=` | Bearer |
| Drill queue count | GET | `/drill/queue/count` | Bearer |
| Record drill review | POST | `/drill/review` | Bearer |
| Opening mastery | GET | `/drill/mastery/{opening_id}` | Bearer |
| Tilt status | GET | `/user/tilt-status` | Bearer |
| Dashboard | GET | `/analytics/dashboard` | Bearer |
| Rating trend | GET | `/analytics/rating-trend` | Bearer |
| Stripe checkout | POST | `/subscriptions/checkout` | Bearer |
| Subscription status | GET | `/subscriptions/status` | Bearer |

**Phase 2 endpoints (not used in MVP):**
`/endgame/*`, `/mission/*`, `/achievements/*`, `/sessions/{id}/analyze`, `/sessions/{id}/hint`, `/sessions/{id}/review`, `/openings` (browse), `/glitch-report/history`

**Swagger docs (full schemas):** `https://api.neongambit.com/docs`

---

*End of NeonGambit Frontend Implementation Guide v5.1*
*Every screen serves the emotional arc. The client owns the engine. The templates own the coaching.*
