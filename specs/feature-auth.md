# Feature Spec: Authentication — "Play First, Understand Later"

## Contexto del usuario
The Frustrated Improver does not want to create an account before seeing value. Every friction point before the first game is a drop-off. Auth must be invisible until the user has a reason to care about saving progress.

**Emotion target:** "I didn't even have to log in. It just worked."

## Comportamiento esperado

1. **App open → auto guest session.** No login screen. A UUID-based guest token is created server-side and stored in `sessionStorage`. The user lands directly in the app.
2. **After first sparring session loss or close game:** A prompt appears: "Connect your Lichess account to discover why you keep losing the same openings." This is the highest-motivation moment.
3. **Lichess connect:** User enters username only (no password). No OAuth. Public read-only API.
4. **Account creation (email/Google/Apple):** Triggered only when user wants to save progress or subscribe. Guest session is linked to the new account — no data loss.
5. **Token storage:**
   - Guests: `sessionStorage` (cleared on tab close)
   - Authenticated: httpOnly cookie via Next.js API route

**Fallback for no-Lichess users:**
- After 5 completed sessions: "Generate My Report" from NeonGambit session data only.
- Lichess connection remains available for deeper analysis at any time.

## Criterios de aceptación (BDD)

```
GIVEN a new visitor with no session
WHEN the app loads
THEN a guest user is created automatically via POST /v1/auth/guest
AND a JWT is stored in sessionStorage
AND the user lands on the main screen without any login prompt

GIVEN a guest user after completing their first sparring session
WHEN the session ends (win or loss)
THEN a Lichess connect prompt appears with the message:
     "Connect your Lichess account to discover why you keep losing the same openings."

GIVEN a guest user with a valid Firebase ID token
WHEN they complete Firebase auth (email/Google/Apple)
AND POST /v1/auth/link-account is called with their Firebase token
THEN their guest session data is preserved
AND a new JWT is returned with their upgraded user record

GIVEN an authenticated user with a valid Firebase token
WHEN they call POST /v1/auth/validate
THEN a JWT is returned
AND the token expires in 30 days

GIVEN a request to any protected endpoint without a Bearer token
WHEN the request is processed
THEN 401 Unauthorized is returned
```

## Contratos de API

```
POST /v1/auth/guest
  Request:  {} (no body)
  Response: { "access_token": string, "token_type": "bearer" }
  Auth:     None
  Notes:    Creates a User row with guest_token, no email/firebase_uid.
            Rate limit: 10/hour per IP.

POST /v1/auth/validate
  Request:  { "firebase_token": string }
  Response: { "access_token": string, "token_type": "bearer" }
  Auth:     None
  Notes:    Validates Firebase ID token via Firebase Admin SDK.
            Creates user if new, finds existing if returning.

POST /v1/auth/link-account
  Request:  { "firebase_token": string }
  Response: { "access_token": string, "token_type": "bearer" }
  Auth:     Bearer (guest JWT)
  Notes:    Links Firebase identity to existing guest account.
            Preserves all session/drill/report data under the guest user.id.
            Returns a new JWT with same user.id but updated firebase_uid.

GET /health
  Response: { "status": "ok", "version": "5.1.0" }
  Auth:     None
```

## Estado del frontend

```
useAuthStore (Zustand):
  - user: { id, isGuest, isAuthenticated, isPro, lichessUsername, preferredLanguage }
  - token: string | null
  - setToken(token: string): void
  - setUser(user: User): void
  - logout(): void

On app boot:
  1. Check sessionStorage for existing token
  2. If none → call POST /auth/guest → store token in sessionStorage → hydrate store
  3. If exists → decode JWT, hydrate store from payload

On Firebase auth complete:
  1. Get Firebase ID token
  2. If user.isGuest → call POST /auth/link-account
  3. Else → call POST /auth/validate
  4. Update sessionStorage + store with new JWT
```

## Criterios de performance

- `POST /auth/guest` must respond in < 200ms (simple DB insert + JWT sign)
- `POST /auth/validate` must respond in < 500ms (Firebase SDK call + DB lookup)
- Guest session lasts 30 days in Redis TTL

## Edge cases

- **Duplicate guest creation:** If guest token already exists in DB, return existing JWT
- **Firebase token expired:** Return 401 with `"detail": "Firebase token expired"` — frontend prompts re-auth
- **Link account when Firebase account already exists:** Merge: use existing firebase_uid's data, discard empty guest record
- **Tab close (guest):** sessionStorage cleared → next open creates new guest. This is expected.
- **Offline on app boot:** Show cached last session if available; don't block UI on auth failure

## Tests requeridos (antes de implementar)

```
# /backend/tests/test_auth.py

test_create_guest_returns_token
  → POST /auth/guest → 200, has access_token field

test_create_guest_creates_user_row
  → After POST /auth/guest, user row exists in DB with guest_token set

test_validate_firebase_creates_user
  → POST /auth/validate with mock Firebase token → 200, new user created

test_validate_firebase_finds_existing_user
  → POST /auth/validate twice with same Firebase uid → returns same user.id

test_link_account_preserves_guest_data
  → Create guest → create sparring session → link account → session still exists

test_protected_endpoint_rejects_no_token
  → GET /sessions without Bearer → 401

test_protected_endpoint_rejects_invalid_token
  → GET /sessions with "Bearer invalid" → 401

test_link_account_requires_guest_token
  → POST /auth/link-account without Bearer → 401
```
