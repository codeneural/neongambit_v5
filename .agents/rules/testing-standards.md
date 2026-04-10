# Testing Standards

## Mandatory Coverage Thresholds
- Backend services: minimum 80% coverage
- Backend routers: minimum 70% coverage
- Frontend stores: minimum 75% coverage
- Frontend hooks: minimum 60% coverage

## Test Categories and When to Write Them

### Unit Tests (write FIRST — TDD)
For every service method:
- Happy path: normal input → expected output
- Edge case: boundary values, empty inputs
- Error case: invalid input → correct exception raised

### Integration Tests (write SECOND)
For every API endpoint:
- Auth: unauthenticated request → 401
- Valid request → correct response schema
- Invalid request → correct error code and message
- Rate limit: exceeding limit → 429

### E2E Tests (write THIRD — browser agent)
Critical user journeys only:
1. Guest → sparring session → debrief
2. Lichess connect → Glitch Report reveal
3. Neural drill → complete queue → streak update
4. Upgrade modal → Stripe checkout redirect

## Test File Locations
- Backend unit: /backend/tests/test_[service_name].py
- Backend integration: /backend/tests/test_[router_name].py
- Frontend unit: /frontend/lib/[module].test.ts
- Frontend E2E: /frontend/e2e/[journey].spec.ts

## Required Test Data
See /backend/tests/conftest.py for fixtures.
Never use production Lichess usernames in tests.
Use test username: "NeonGambitTestUser" (a real account with public games).
Never use real Stripe keys in tests. Use Stripe test mode keys.

## The TDD Cycle (enforced by /new-feature workflow)
1. Write failing test that describes expected behavior
2. Run: pytest — confirm test fails
3. Write minimum code to pass the test
4. Run: pytest — confirm test passes
5. Refactor: improve code quality without breaking tests
6. Run: pytest — confirm still passes
7. Repeat for next behavior
