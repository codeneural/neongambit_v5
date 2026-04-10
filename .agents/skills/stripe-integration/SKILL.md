# Skill: stripe-integration

Stripe checkout and webhook handling for NeonGambit Pro subscriptions.

## SubscriptionService (Section 6.10)

```python
# app/services/subscription_service.py
import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

class SubscriptionService:

    async def create_checkout_session(self, user: User, plan: str) -> str:
        """Returns Stripe checkout URL."""
        price_id = (settings.STRIPE_PRICE_ID_MONTHLY if plan == "monthly"
                    else settings.STRIPE_PRICE_ID_YEARLY)
        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url="https://neongambit.com/dashboard?upgraded=true",
            cancel_url="https://neongambit.com/dashboard",
            client_reference_id=str(user.id),
            customer_email=user.email,
        )
        return session.url

    async def handle_webhook(self, payload: bytes, sig_header: str, db: AsyncSession):
        """Verify signature and process Stripe events."""
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
        except Exception:
            raise ValueError("Invalid webhook signature")

        event_type = event["type"]
        data = event["data"]["object"]

        if event_type in ("customer.subscription.created", "customer.subscription.updated"):
            await self._upsert_subscription(data, db, active=data["status"] == "active")
        elif event_type in ("customer.subscription.deleted", "invoice.payment_failed"):
            await self._upsert_subscription(data, db, active=False)
```

## Webhook Router (Section 7.7)

```python
# app/api/v1/webhooks.py
@router.post("/stripe")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    await subscription_svc.handle_webhook(payload, sig_header, db)
    return {"received": True}
```

**Critical:** The webhook endpoint must receive the raw request body (not parsed JSON) for Stripe signature verification.

## Config Variables Required

```
STRIPE_SECRET_KEY        — sk_live_...
STRIPE_WEBHOOK_SECRET    — whsec_...
STRIPE_PRICE_ID_MONTHLY  — price_...
STRIPE_PRICE_ID_YEARLY   — price_...
```

## Subscription Model

```python
class Subscription(Base):
    __tablename__ = "subscriptions"
    # user_id, stripe_subscription_id, stripe_customer_id,
    # plan ('monthly'|'yearly'), status, current_period_end
```

## Pro Feature Gates

When `is_pro = True`, the user gets:
- Unlimited Lichess game imports (200 vs 20)
- All openings in Glitch Report have `training_unlocked = True`
- Unlimited drills per day (vs 5 free)

## Stripe Events to Handle

| Event | Action |
|-------|--------|
| `customer.subscription.created` | Set `users.is_pro = True` |
| `customer.subscription.updated` | Update status (active/paused) |
| `customer.subscription.deleted` | Set `users.is_pro = False` |
| `invoice.payment_failed` | Set `users.is_pro = False` |

## Test Webhook Locally

```bash
stripe listen --forward-to localhost:8000/v1/webhooks/stripe
```
