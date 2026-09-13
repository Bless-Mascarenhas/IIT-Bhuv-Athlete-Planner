# BRIEFING — 2026-09-13T10:06:00Z

## Mission
Implement Milestone 2: AI Intent Router (R2) with dual-engine (Groq LLM + Deterministic Regex fallback) autonomous intent classification, database modification for calendar updates and plan adjustments, QA sports science advice, and FastAPI `/api/chat` endpoint.

## 🔒 My Identity
- Archetype: worker
- Roles: implementer, qa, specialist
- Working directory: d:\IIT-Bhuv\.agents\worker_m2
- Original parent: a0855948-dc80-4ba2-9790-4b8041c8b54c
- Milestone: Milestone 2 (R2 - AI Intent Router)

## 🔒 Key Constraints
- Exclusively create/modify: backend/intent_router.py, backend/main.py
- DO NOT CHEAT: Genuine implementation, no hardcoded strings or test dummy returns.
- Three distinct intents: Update Calendar, Update Plan, General QA
- Update Calendar: extracts match/training, relative date (tomorrow, weekday, etc.), inserts into `events` table (athlete_id, event_date, event_type, duration_minutes), returns action_taken="calendar_updated".
- Update Plan: adjusts today's training_plans (e.g. intensity/rpe/workout) or registers recovery, does NOT touch events, returns action_taken="plan_adjusted".
- General QA: sports science coaching guidance, does NOT touch DB.
- Dual-engine: Groq LLM if GROQ_API_KEY present and valid, deterministic fallback when offline/no key.
- Verify 100% tests pass on test_r2_intent.py and regression test test_r1_quests.py.

## Current Parent
- Conversation ID: a0855948-dc80-4ba2-9790-4b8041c8b54c
- Updated: 2026-09-13T10:06:00Z

## Task Summary
- **What to build**: backend/intent_router.py and backend/main.py chat endpoint
- **Success criteria**: All tests in tests/test_r2_intent.py pass, regression tests pass.
- **Interface contracts**: backend/main.py `POST /api/chat`
- **Code layout**: Python backend with SQLite

## Change Tracker
- **Files modified**: [TBD]
- **Build status**: [TBD]
- **Pending issues**: None

## Quality Status
- **Build/test result**: [TBD]
- **Lint status**: Clean
- **Tests added/modified**: tests/test_r2_intent.py exists

## Loaded Skills
- None
