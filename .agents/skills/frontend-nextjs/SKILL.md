# Skill: frontend-nextjs

Next.js 14 (App Router) patterns for NeonGambit frontend.

## Stack

```
Framework:  Next.js 14 (App Router)
Language:   TypeScript strict mode — NO 'any'
Styling:    Tailwind CSS v3 + shadcn/ui
Animations: Framer Motion v11
Chess UI:   react-chessboard v4
Chess Logic: chess.js v1 (optimistic UI only — server is source of truth)
State:      Zustand v4 (flat stores only)
Auth:       Firebase Auth v10 + NextAuth.js v5
HTTP:       Axios v1 with typed interceptors
i18n:       next-intl (en + es)
PWA:        next-pwa v5
```

## Directory Structure (Section 2)

```
/
├── app/
│   ├── layout.tsx              # Root — fonts, providers, PWA meta
│   ├── page.tsx                # Splash → auto-redirect
│   ├── (auth)/login/page.tsx
│   └── (main)/
│       ├── layout.tsx          # Dashboard shell — BottomNav + TopBar
│       ├── page.tsx            # Mission Control (Home)
│       ├── glitch-report/page.tsx
│       ├── arena/page.tsx
│       ├── debrief/[sessionId]/page.tsx
│       ├── drill/page.tsx
│       └── profile/page.tsx
├── components/
│   ├── chess/    # NeonChessboard, TheoryBar, EvalGauge, MoveTimeline, SurvivalBanner
│   ├── coach/    # NeonTerminal, NeonAvatar
│   ├── glitch/   # GlitchReportReveal, CriticalOpeningCard, StrengthRow, PatternSummary
│   ├── progress/ # RatingChart, OpeningImprovementRow, StreakBadge, MasteryGauge
│   ├── drill/    # DrillCard, ShadowMove, DrillResult
│   └── shared/   # SystemBoot, CyberpunkCard, NeonButton, NeonBadge, UpgradeModal,
│                 # LichessConnectPrompt, TiltIntervention, LoadingTerminal, BottomNav
├── lib/
│   ├── api/      # client.ts, auth.ts, sessions.ts, lichess.ts, drill.ts, analytics.ts
│   ├── store/    # useAuthStore, useSessionStore, useDrillStore, useDashboardStore
│   ├── stockfish/ # worker.ts, useStockfish.ts
│   ├── hooks/    # useTypewriter, useHaptics, useAudio, usePollJobStatus, useGlitchReveal
│   └── utils/    # designTokens.ts, chess.ts, format.ts
└── messages/
    ├── en.json
    └── es.json
```

## API Client (Section 4)

```typescript
// lib/api/client.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'https://api.neongambit.com/v1';
export const apiClient = axios.create({ baseURL: API_BASE, timeout: 15000 });
// Interceptor: attach JWT from auth store on every request
// Interceptor: 401 → clear auth store + redirect to splash
```

## State Management (Section 5)

Zustand **flat stores only**. No Redux. No React Context for shared state.

```typescript
// lib/store/useAuthStore.ts
interface AuthState {
  user: User | null;
  token: string | null;
  setUser: (user: User, token: string) => void;
  clearAuth: () => void;
}
```

## i18n Rules

- ALL user-facing strings use `next-intl` translation keys
- NEVER hardcode UI text
- Supported locales: `en`, `es`
- Keys stored in `messages/en.json` and `messages/es.json`

## Color Rules

- ALL colors imported from `lib/utils/designTokens.ts`
- NEVER hardcode hex values in components

## Navigation (Section 10)

3-tab BottomNav (persistent in dashboard layout):
- **Arena** `/arena`
- **Drill** `/drill`
- **Profile** `/profile`

## Key Constraints

- Frontend is a **dumb client** — backend is source of truth for game state
- Move **validation** is server-side. Move **quality evaluation** is client-side (WASM)
- No Stockfish calls to server during sparring
- No LLM calls during gameplay — only NEON templates
