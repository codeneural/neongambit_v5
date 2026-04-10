# Skill: stitch-design

NeonGambit cyberpunk design system — canonical tokens, Tailwind config, CSS effects.

## Canonical Color Tokens (Section 3)

```typescript
// lib/utils/designTokens.ts — THE ONLY place colors are defined.
// Import from here everywhere. NEVER hardcode hex in components.

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
} as const;

export const typography = {
  h1: { fontFamily: 'Orbitron', fontSize: '28px', fontWeight: '700' },
  h2: { fontFamily: 'Orbitron', fontSize: '22px', fontWeight: '600' },
  h3: { fontFamily: 'Orbitron', fontSize: '18px', fontWeight: '600' },
  body: { fontFamily: 'Inter', fontSize: '16px', fontWeight: '400' },
  mono: { fontFamily: 'JetBrains Mono', fontSize: '13px', fontWeight: '400' },
  label: { fontFamily: 'Orbitron', fontSize: '11px', fontWeight: '600', letterSpacing: '0.12em' },
} as const;
```

## Tailwind Config (Section 3)

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
        'glitch':     'glitch 0.2s steps(2) forwards',
        'pulse-neon': 'pulse-neon 2s ease-in-out infinite',
        'flicker':    'flicker 0.15s ease-in-out',
        'slide-up':   'slide-up 0.3s ease-out',
        'fade-in':    'fade-in 0.4s ease-out',
      },
    },
  },
};
```

## Global CSS Effects (Section 3)

```css
/* Glassmorphism — all cards/panels */
.glass {
  background: rgba(15, 15, 26, 0.85);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(30, 30, 53, 0.9);
}

/* Scanlines — NEON terminal, coaching widget */
.scanlines::after {
  content: '';
  position: absolute; inset: 0;
  background: repeating-linear-gradient(0deg, transparent, transparent 2px,
    rgba(0, 0, 0, 0.12) 2px, rgba(0, 0, 0, 0.12) 4px);
  pointer-events: none; z-index: 10;
}

/* Neon glow text */
.text-glow-cyan    { text-shadow: 0 0 12px rgba(0, 229, 255, 0.8); }
.text-glow-magenta { text-shadow: 0 0 12px rgba(224, 0, 140, 0.8); }
.text-glow-amber   { text-shadow: 0 0 12px rgba(245, 158, 11, 0.8); }

/* Chromatic aberration — triggered on blunder */
.glitch-animation { animation: glitch 0.2s steps(2) forwards; }
@keyframes glitch {
  25%  { filter: drop-shadow(-3px 0 #E0008C) drop-shadow(3px 0 #00E5FF); }
  75%  { filter: drop-shadow(3px 0 #E0008C) drop-shadow(-3px 0 #00E5FF); }
}

/* Amber flash — out-of-book survival mode */
.survival-flash { animation: flicker 0.15s ease-in-out 3; background: rgba(245, 158, 11, 0.06); }

/* Entrance animations */
.slide-up { animation: slide-up 0.3s ease-out; }
.fade-in  { animation: fade-in 0.4s ease-out; }
```

## Typography Fonts (load in root layout.tsx)

- **Orbitron** — headers, labels, UI titles (cyberpunk feel)
- **JetBrains Mono** — terminal output, FEN, move notation
- **Inter** — body text, descriptions

## Design Rules

1. Background is always `void` (`#080810`) — never white or light gray
2. Cards use `surface` with `.glass` class
3. CTAs (primary buttons) use `cyan` with `shadow-neon-cyan`
4. Opponent / destructive elements use `magenta`
5. Pro tier gating uses `violet`
6. Warnings / out-of-book use `amber`
7. If Stitch exports conflict with these tokens, **designTokens.ts wins**

## Google Stitch Screens (FASE 1)

5 screens to generate:
1. Mission Control (Home)
2. The Arena (Sparring)
3. Glitch Report Reveal
4. Neural Drill
5. Profile/Settings
