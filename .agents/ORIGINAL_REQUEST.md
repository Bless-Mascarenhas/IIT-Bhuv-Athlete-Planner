# Original User Request

## Initial Request — 2026-09-13T09:46:13Z

Build out the React + Capacitor frontend and FastAPI backend for "Pace", an autonomous athlete performance planner. The system will integrate an AI intent router for natural language data entry and a 5-tab mobile interface for daily planning and reporting.

Requested team: Full autonomous team
Working directory: d:/IIT-Bhuv
Integrity mode: development

## Requirements

### R1. Database and Backend Overhaul
Transition the backend to a 1-day rolling "Quests" generator. Implement new database tables (`users`, `google_fit_logs`) and update `training_plans` to track task completion for daily streaks.

### R2. AI Intent Router
Build a natural language processing agent that classifies user chats into three distinct intents (Update Calendar, Update Plan, General QA) and autonomously executes the corresponding database modifications without requiring manual form entry.

### R3. Mobile SPA Frontend
Implement a 5-tab mobile-first React application (Dashboard, Planner, Chat, Calendar, Settings) featuring a persistent header with a dynamic streak counter and a Strava-style bottom navigation bar.

### R4. Health Data Architecture
Implement a provider interface for `@capawesome-team/capacitor-health` that gracefully falls back to mock data when running in a web browser, ensuring seamless local development before device deployment.

## Acceptance Criteria

### Backend & Database (R1)
- [ ] An agent successfully executes a script that calls the API to generate a 1-day rolling plan, and programmatically verifies the `training_plans` SQLite table contains exactly one day of data formatted as Quests.

### AI Intent Router (R2)
- [ ] An agent sends a test string ("I have a match tomorrow") to the chat endpoint, and programmatically verifies the SQLite `events` table was autonomously updated with the new match.

### Frontend UI (R3 & R4)
- [ ] An agent starts the Vite dev server, navigates the 5 tabs in the browser, and visually confirms (via screenshot or DOM check) that the Strava-style layout and Health mock providers load without crashing.
