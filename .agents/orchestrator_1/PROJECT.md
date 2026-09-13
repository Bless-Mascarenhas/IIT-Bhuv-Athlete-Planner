# Project: Pace - Autonomous Athlete Performance Planner

## Architecture
Pace is a dual-tier mobile and backend platform for high-performance athletes:
1. **Backend (FastAPI + SQLite)**:
   - Location: `backend/`
   - Database: `backend/athlete_planner.db`
   - Key modules:
     - `database.py`: Schema definitions (`users`, `google_fit_logs`, `athletes`, `events`, `daily_logs`, `training_plans`), dynamic migrations, connection management (`sqlite3.Row`).
     - `algorithm.py`: Acute:Chronic Workload Ratio (ACWR) calculation, pre-match tapering, post-match recovery load management.
     - `agent.py`: 1-day rolling Quests generator (`generate_daily_quests`) with sports-science constraints and Groq / deterministic fallback.
     - `intent_router.py`: Intent classifier (`Update Calendar`, `Update Plan`, `General QA`) and autonomous DB modifiers.
     - `main.py`: REST API endpoints (`/api/plan/generate`, `/api/quests/{id}/complete`, `/api/chat`, `/api/events`, `/api/user/profile`, `/api/health/sync`, etc.).
2. **Frontend (React 19 + TypeScript + Vite 8 + Capacitor 8)**:
   - Location: `mobile/`
   - 5-tab SPA navigation (`/dashboard`, `/planner`, `/chat`, `/calendar`, `/settings`).
   - Persistent `Header` with dynamic streak counter and greeting.
   - Strava-style bottom `Footer` navigation with active branding and elevated AI tab.
   - Health Data Architecture: Strategy pattern with `IHealthProvider`, `NativeHealthProvider`, and `MockHealthProvider` ensuring no crashes in web browser.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Users Table | SQLite schema for athlete profile and streak tracking (`current_streak`, `last_active_date`, `daily_streak`) | M1 | ORIGINAL_REQUEST R1 (DONE) |
| 2 | Google Fit Logs Table | SQLite schema for synchronized Google Fit telemetry logs | M1 | ORIGINAL_REQUEST R1 (DONE) |
| 3 | Training Plans Quests Schema | Extend `training_plans` with `quest_title`, `task_type`, `is_completed`, `completed_at`, `duration_minutes` | M1 | ORIGINAL_REQUEST R1 (DONE) |
| 4 | 1-Day Rolling Quests Generator | Transition `/api/plan/generate` to output 1-day actionable quest tasks instead of 7-day array | M1 | ORIGINAL_REQUEST R1 (DONE) |
| 5 | Quest Completion & Streak Logic | API endpoint `/api/quests/{id}/complete` to toggle quest completion and increment streak | M1 | ORIGINAL_REQUEST R1 (DONE) |
| 6 | AI Intent Classifier | Classify incoming user chat into `Update Calendar`, `Update Plan`, or `General QA` | M2 | ORIGINAL_REQUEST R2 (DONE) |
| 7 | Autonomous DB Event Executor | Parse calendar events (e.g. "I have a match tomorrow") and insert into `events` table autonomously | M2 | ORIGINAL_REQUEST R2 (DONE) |
| 8 | Autonomous Plan Update Executor | Parse training updates (e.g. "feeling sick", "tweak hamstring") and update plans/recovery | M2 | ORIGINAL_REQUEST R2 (DONE) |
| 9 | General QA Conversational Chat | Provide sports science and recovery coaching feedback | M2 | ORIGINAL_REQUEST R2 (DONE) |
| 10 | Health Provider Interface | Abstract interface (`IHealthProvider`) for biometric telemetry | M3 | ORIGINAL_REQUEST R4 (DONE) |
| 11 | Mock Health Data Provider | Fallback provider delivering realistic athlete biometrics in browser without Capacitor crash | M3 | ORIGINAL_REQUEST R4 (DONE) |
| 12 | Native Capacitor Health Provider | Provider interfacing `@capawesome-team/capacitor-health` for mobile devices | M3 | ORIGINAL_REQUEST R4 (DONE) |
| 13 | 5-Tab Mobile Layout Shell | Persistent Header with dynamic streak counter + Strava-style bottom navigation | M3 | ORIGINAL_REQUEST R3 (DONE) |
| 14 | Dashboard Page | Athlete readiness score, ACWR gauge, recent activity, health telemetry | M3 | ORIGINAL_REQUEST R3 (DONE) |
| 15 | Planner Page | Today's 1-Day Quests with interactive check-off and streak increment feedback | M3 | ORIGINAL_REQUEST R3 (DONE) |
| 16 | Chat Page | Interactive conversational interface connected to AI Intent Router (`POST /api/chat`) | M3 | ORIGINAL_REQUEST R3 (DONE) |
| 17 | Calendar Page | Upcoming matches and training events list with add/delete support | M3 | ORIGINAL_REQUEST R3 (DONE) |
| 18 | Settings Page | User profile, streak statistics, and mock health data status | M3 | ORIGINAL_REQUEST R3 (DONE) |
| 19 | E2E Acceptance Verification | Programmatic verification of 1-day plan generation, intent router DB update, and browser UI | M4 | ORIGINAL_REQUEST AC (DONE) |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Database & Backend Overhaul (R1) | `users`, `google_fit_logs`, updated `training_plans`, 1-day rolling Quests generator, streak tracking | none | DONE |
| M2 | AI Intent Router (R2) | `POST /api/chat`, 3-way intent classification, autonomous SQLite `events` insertion | M1 | DONE |
| M3 | Mobile SPA Frontend & Health Data (R3 & R4) | 5-tab React SPA, persistent header streak, Strava-style nav, Health provider & mock fallback | M1, M2 | DONE |
| M4 | Final E2E Acceptance Verification | Dual-track programmatic verification of R1, R2, R3, R4 Acceptance Criteria (21/21 passed) | M1, M2, M3 | DONE |

## Interface Contracts
### Backend ↔ Frontend / Intent Router
1. **Plan Generation (`POST /api/plan/generate`)**:
   - Request: `{ athlete_id: int, target_date?: string, current_fatigue?: int, current_sleep?: int }`
   - Response: `{ status: "success", plan_date: string, quests: [ { id: int, quest_title: string, task_type: string, target_rpe: int, duration_minutes: int, is_completed: bool } ] }`
2. **Quest Completion (`POST /api/quests/{id}/complete`)**:
   - Request: `{ is_completed: bool }`
   - Response: `{ status: "success", quest_id: int, is_completed: bool, daily_streak: int }`
3. **Chat Intent Router (`POST /api/chat`)**:
   - Request: `{ athlete_id: int, message: string, history?: list }`
   - Response: `{ status: "success", intent: "Update Calendar" | "Update Plan" | "General QA", response: string, action_taken?: string, data?: any }`
4. **Events API (`GET /api/events`, `POST /api/events/add`)**:
   - GET Response: `{ status: "success", events: [ { id: int, athlete_id: int, event_date: string, event_type: string, duration_minutes: int } ] }`
5. **Health Data Provider (`IHealthProvider`)**:
   - `getTodaySteps(): Promise<number>`
   - `getHeartRate(): Promise<{ current: number, resting: number }>`
   - `getSleepHours(): Promise<number>`
   - `getCaloriesBurned(): Promise<number>`

## Code Layout
- `backend/`:
  - `main.py`: FastAPI routes and application lifecycle
  - `database.py`: SQLite table creation and connection helper
  - `algorithm.py`: ACWR engine and workload safety constraints
  - `agent.py`: LLM / algorithmic plan generation
  - `intent_router.py`: Intent classifier and autonomous DB modifiers
  - `tests/`: Automated test suite
- `mobile/`:
  - `src/services/health/`: `IHealthProvider.ts`, `MockHealthProvider.ts`, `NativeHealthProvider.ts`, `HealthProviderFactory.ts`
  - `src/services/api.ts`: API client connecting to backend endpoints
  - `src/context/AthleteContext.tsx`: Shared state for streak, active quests, athlete profile
  - `src/components/Header.tsx`: Persistent header with dynamic streak
  - `src/components/Footer.tsx`: Strava-style bottom navigation
  - `src/pages/`: `Dashboard.tsx`, `Planner.tsx`, `Chat.tsx`, `Calendar.tsx`, `Settings.tsx`
