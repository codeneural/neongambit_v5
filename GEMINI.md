# NeonGambit — Antigravity-Specific Configuration

## Agent Mode Preferences
- Use Planning Mode for any task that touches more than 2 files
- Use Fast Mode only for single-file changes and bug fixes
- Always generate Implementation Plan artifact before touching code on complex tasks
- Always produce a Walkthrough artifact after completing a mission

## Multi-Agent Orchestration
For missions involving both backend and frontend:
- Assign Backend Agent to services, routers, schemas
- Assign Frontend Agent to components, stores, hooks
- Assign Test Agent to write tests for both (runs in parallel)
- Never let one agent modify both backend and frontend in the same task

## Browser Agent Instructions
- After implementing any UI component, take a screenshot
- Compare screenshot against DESIGN.md color tokens and layout specs
- Flag any deviation from designTokens.ts canonical values
- Verify all Tailwind classes match the tailwind.config.js extensions

## Knowledge Base
Update the project Knowledge Base when:
- A non-obvious architectural pattern is established
- A bug is found and fixed that could recur
- A service integration behaves differently than documented
- A performance optimization is discovered

## Model Assignment
- Complex reasoning (architecture, debugging): Claude Opus 4.6
- Standard implementation (services, components): Gemini 3.1 Pro (High)
- Fast tasks (formatting, simple fixes): Gemini 3 Flash
- Frontend visual work: Gemini 3.1 Pro (High) — better Tailwind/React output

## File Organization Rules
- Backend agent works exclusively in /backend
- Frontend agent works exclusively in /frontend
- Neither agent touches the other's directory
- Shared types go in /shared/types/ (if created)
- Migration files created by Database Agent, reviewed by you before running
