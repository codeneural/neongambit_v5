# Git Workflow Rules

## Branch Strategy
- main: production. Protected. Direct pushes blocked.
- develop: integration branch. All feature PRs merge here.
- feature/[name]: agent work on new features
- fix/[name]: bug fixes
- agent/[name]: large autonomous agent tasks (refactors, migrations)
- chore/[name]: dependency updates, config changes

## Commit Format (Conventional Commits)
feat: add Glitch Report generation endpoint
fix: prevent double-move race condition in session service
test: add SM-2 edge cases for quality=0
docs: update API spec for /drill/queue endpoint
refactor: extract move quality logic to separate method
chore: upgrade python-chess to 2.0

## PR Rules
- PR title matches commit format
- PR description includes: what changed, why, how to test
- All tests must pass before PR is created
- Never merge your own PR — review the agent's diff carefully
- Agent PRs go to: feature/[name] → develop

## Agent Branch Protocol
When assigning a large task to an agent:
1. Create branch: git checkout -b agent/[task-name]
2. Tell agent: "Work on branch agent/[task-name]"
3. Agent commits incrementally with descriptive messages
4. When done: review diff carefully, then merge to develop
5. Never let agent push directly to main

## Pre-commit Checklist (enforced in CI)
- [ ] Tests pass: pytest (backend) / vitest (frontend)
- [ ] No hardcoded secrets (checked by trufflehog)
- [ ] Type check passes: mypy (backend) / tsc --noEmit (frontend)
- [ ] Lint passes: ruff (backend) / eslint (frontend)
