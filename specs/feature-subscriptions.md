# Feature Spec: Subscriptions — "Grandmaster Tier"

## Contexto del usuario
The Frustrated Improver has seen their Glitch Report. They know they have 4 critical openings but can only train 2. They've hit the drill cap of 5 cards/day. They've seen "Retry from this position" grayed out after a blunder. They know exactly what they're paying for. This is the highest-converting paywall design: show the full problem, gate the full solution.

**Emotion target:** "I know exactly what I'm unlocking."

## Comportamiento esperado

1. User encounters a Pro-gated feature (3rd opening, drill limit, retry-from-position).
2. UpgradeModal appears — non-intrusive, not blocking. Shows exactly which feature is locked and why Pro unlocks it.
3. User taps "Upgrade to Grandmaster" → `POST /v1/subscriptions/checkout` → redirected to Stripe Checkout.
4. Stripe handles payment. On success → redirect to `neongambit.com/dashboard?upgraded=true`.
5. Stripe sends webhook to `POST /v1/webhooks/stripe` → server updates `user.is_pro=true`.
6. Dashboard shows "Grandmaster" badge on next load.
7. On subscription cancel/payment failure → webhook sets `user.is_pro=false`.

**Pricing:**
- Monthly: $4.99/month
- Annual: $39.99/year (save 33%)

**No trial period in MVP.** May add 7-day trial in Phase 2 based on conversion data.

**Upgrade triggers (natural, not intrusive):**
- "DRILL THIS NOW" on 3rd+ critical opening → UpgradeModal: "Recruit tier includes 2 openings. Unlock this one?"
- Daily drill cap reached → UpgradeModal: "Your next due review is Ruy Lopez move 8. See it tomorrow or unlock now."
- "Retry from position" tapped → UpgradeModal: "Retry from this position? [Pro feature]"
- Lichess sync shows > 20 games → banner: "You have 847 more games. Unlock your full pattern history."

## Criterios de aceptación (BDD)

```
GIVEN an authenticated user (any tier)
WHEN POST /v1/subscriptions/checkout is called with plan='monthly'
THEN a Stripe Checkout URL is returned
AND the user is redirected to Stripe's hosted checkout page

GIVEN a Stripe subscription.created event with status='active'
WHEN POST /v1/webhooks/stripe receives the event
THEN user.is_pro is set to true
AND subscription row is upserted in the subscriptions table

GIVEN a Stripe customer.subscription.deleted event
WHEN the webhook is processed
THEN user.is_pro is set to false

GIVEN an invoice.payment_failed event
WHEN the webhook is processed
THEN user.is_pro is set to false

GIVEN a Pro user
WHEN GET /v1/analytics/dashboard is called
THEN all drill cards are accessible (no 5-card cap)
AND all Glitch Report openings have training_unlocked=true
AND Lichess import allows up to 200 games

GIVEN a free-tier user
WHEN they request 200 games in the Lichess import
THEN max_games is silently capped to 20

GIVEN an invalid Stripe webhook signature
WHEN POST /v1/webhooks/stripe receives the request
THEN 400 is returned
AND no database changes are made

GIVEN a webhook for an unknown Stripe customer
WHEN the webhook is processed
THEN the webhook is logged and 200 returned (idempotent — Stripe retries)
AND no application error is raised
```

## Contratos de API

```
POST /v1/subscriptions/checkout
  Auth:    Bearer JWT (any user)
  Request: { "plan": "monthly" | "annual" }
  Response 200: { "checkout_url": string }
  Response 400: { "detail": "Invalid plan. Use 'monthly' or 'annual'." }
  Notes:   Stripe Checkout session uses client_reference_id=user.id
           so the webhook can identify the user after payment.
           customer_email is populated from user.email if available.

POST /v1/subscriptions/status
  Auth:    Bearer JWT (any user)
  Response 200: {
    "is_pro": bool,
    "plan": "monthly" | "annual" | null,
    "current_period_end": datetime | null,  // When subscription renews or expires
    "cancel_at_period_end": bool
  }
  Notes:   Used by Profile page to show subscription status and manage billing.

POST /v1/webhooks/stripe
  Auth:    None (verified via Stripe-Signature header)
  Headers: Stripe-Signature: string
  Request: Raw bytes (Stripe event payload)
  Response 200: { "received": true }
  Response 400: { "detail": "Invalid signature" }
  Notes:   MUST read raw request body (not request.json()).
           Processes: subscription.created, subscription.updated,
           subscription.deleted, invoice.payment_failed
```

## Webhook processing logic

```
stripe_webhook handler:
  1. Read raw body bytes
  2. Verify signature via stripe.Webhook.construct_event(body, sig, WEBHOOK_SECRET)
     → If invalid: return 400, stop processing
  3. event_type = event["type"]
  4. data = event["data"]["object"]

  CASE subscription.created OR subscription.updated:
    → If data["status"] == "active":
        find user by client_reference_id OR customer email
        set user.is_pro = True
        upsert subscriptions table:
          { stripe_subscription_id, stripe_customer_id, plan, status, current_period_end }
    → If data["status"] != "active":
        set user.is_pro = False

  CASE subscription.deleted:
    → set user.is_pro = False
    → update subscriptions.status = 'cancelled'

  CASE invoice.payment_failed:
    → set user.is_pro = False
    → update subscriptions.status = 'past_due'

  All cases:
    → return 200 { "received": true }
    → If user not found: log warning, still return 200 (Stripe will retry otherwise)

NOTE: The webhook must be idempotent. Stripe can send the same event multiple times.
      Always upsert, never insert-only.
```

## Pro tier features (enforcement points)

```
Enforcement is server-side. Never trust is_pro from the client.

1. Lichess import max_games:
   → max_games = min(request.max_games, 200 if user.is_pro else 20)

2. Glitch Report training_unlocked:
   → Free: training_unlocked=True only for top 2 critical openings
   → Pro: all openings get training_unlocked=True (set in /glitch-report/current router)

3. Drill daily cap:
   → Free: if today_reviews >= 5 → 429
   → Pro: no cap (limit param from request, default 8)

4. Session opening access:
   → Free: only openings where user_repertoire.training_unlocked=True
   → Pro: all openings in repertoire

5. Retry from position (Phase 2):
   → Pro only. Gated in the session resign/complete flow.
   → Not implemented in MVP — just show the button grayed out.

6. Session history:
   → Free: last 10 sessions visible
   → Pro: unlimited
```

## Database model

```python
# app/db/models/subscription.py
class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    stripe_subscription_id: Mapped[str] = mapped_column(String, unique=True)
    stripe_customer_id: Mapped[str] = mapped_column(String, index=True)
    plan: Mapped[str] = mapped_column(String)   # 'monthly' | 'annual'
    status: Mapped[str] = mapped_column(String)  # 'active' | 'cancelled' | 'past_due'
    current_period_end: Mapped[DateTime | None] = mapped_column(DateTime)
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
```

## Estado del frontend

```
useSubscriptionStore (Zustand):
  - isPro: boolean              // Derived from JWT payload or /subscriptions/status
  - plan: 'monthly' | 'annual' | null
  - currentPeriodEnd: Date | null
  - createCheckout(plan: 'monthly' | 'annual'): void  // Opens Stripe Checkout

UpgradeModal component:
  - Triggered by: locked feature tap
  - Props: featureName (string), description (string)
  - Shows: feature being unlocked, plan comparison, pricing
  - Two CTAs: [Monthly $4.99] [Annual $39.99]
  - On CTA tap: POST /subscriptions/checkout → redirect to checkout_url
  - Closes on background tap or [Not now] button

Dashboard (post-upgrade):
  - On load with ?upgraded=true query param:
    → Show "Welcome to Grandmaster" toast
    → Remove upgrade param from URL
    → Refresh dashboard data

Profile page subscription panel:
  - Shows: current plan, renewal date, [Manage Billing] link
  - [Manage Billing] → Stripe Customer Portal (if needed, Phase 2)
  - If free: shows upgrade CTA with pricing
```

## Criterios de performance

- `POST /subscriptions/checkout`: < 1s (Stripe API call, synchronous)
- `POST /webhooks/stripe`: < 300ms (signature verify + DB upsert)
- Stripe webhook retries: handled idempotently — same event processed twice has no side effects

## Edge cases

- **User has no email (guest):** Checkout session created without customer_email. user.is_pro is still updated via client_reference_id on webhook.
- **Webhook arrives before user is in DB:** Log warning, return 200. Don't fail. The user will sync on next login.
- **Double webhook (Stripe retry):** Upsert on stripe_subscription_id handles this. user.is_pro ends up correctly set.
- **Subscription downgrade/cancel mid-period:** is_pro remains true until period_end. Set by subscription.updated webhook with cancel_at_period_end=true. On next subscription.deleted event, is_pro=false.
- **Invalid plan in checkout request:** 400 error. Never pass to Stripe.
- **Stripe API down:** Checkout fails with 503. Frontend shows "Payment service unavailable. Try again in a moment."

## Tests requeridos (antes de implementar)

```
# /backend/tests/test_subscriptions.py

test_checkout_creates_stripe_session
  → POST /subscriptions/checkout plan='monthly' → 200, checkout_url is Stripe URL

test_checkout_invalid_plan
  → POST /subscriptions/checkout plan='enterprise' → 400

test_checkout_requires_auth
  → POST /subscriptions/checkout without Bearer → 401

test_webhook_subscription_created_sets_pro
  → mock Stripe subscription.created event → user.is_pro=True

test_webhook_subscription_deleted_clears_pro
  → mock Stripe subscription.deleted event → user.is_pro=False

test_webhook_payment_failed_clears_pro
  → mock invoice.payment_failed event → user.is_pro=False

test_webhook_invalid_signature_returns_400
  → wrong Stripe-Signature → 400, DB unchanged

test_webhook_unknown_user_returns_200
  → webhook with unknown client_reference_id → 200, no error raised

test_webhook_idempotent
  → same webhook processed twice → no duplicate subscription rows, user.is_pro stable

test_pro_user_gets_training_unlocked_all
  → is_pro=True → GET /glitch-report/current → all critical openings training_unlocked=True

test_free_user_capped_at_20_import_games
  → free user requests max_games=200 → capped to 20

test_pro_user_allowed_200_import_games
  → pro user requests max_games=200 → 200 accepted

test_subscription_status_endpoint
  → GET /subscriptions/status → correct is_pro, plan, period_end fields
```
