# Survey Report: AI Intent Router (R2) & Health Data Architecture (R4)

**Agent**: Survey Explorer 3  
**Working Directory**: `d:\IIT-Bhuv\.agents\explorer_survey_3`  
**Date**: 2026-09-13  
**Mission**: Map existing implementations and technical requirements for R2 (AI Intent Router) and R4 (Health Data Architecture) in the 'Pace' project.

---

## 1. Observation

### 1.1 Existing Chat, Events, and Calendar Implementations

1. **Database Schema (`backend/database.py`)**:
   - `events` table is created at lines 22–31:
     ```python
     # Events / Match Calendar Table
     cursor.execute('''
     CREATE TABLE IF NOT EXISTS events (
         id INTEGER PRIMARY KEY AUTOINCREMENT,
         athlete_id INTEGER,
         event_date DATE NOT NULL,
         event_type TEXT NOT NULL, -- e.g., 'match', 'training'
         duration_minutes INTEGER,
         FOREIGN KEY(athlete_id) REFERENCES athletes(id)
     )
     ''')
     ```
   - Current tables in `backend/database.py`: `athletes`, `events`, `daily_logs`, `training_plans`.
   - **Gaps**:
     - No `chat_log` table exists (specified in `plan.md`: line 29: `chat_log: message_id, timestamp, role, text, parsed_intent, resulting_action`).
     - In `events`, columns `title`, `location`, `source` (e.g. `'chat'` vs `'manual'`) from `plan.md` (line 28) are missing.

2. **Backend API Endpoints (`backend/main.py`)**:
   - Only onboarding chat exists (`backend/main.py:81-89`):
     ```python
     @app.post("/api/onboard/chat")
     def onboard_chat(request: ChatRequest):
         """Endpoint for the 'Grill' Agent."""
         history = [{"role": m.role, "content": m.content} for m in request.history]
         try:
             response = get_onboarding_response(history)
             return {"response": response}
         except Exception as e:
             raise HTTPException(status_code=500, detail=str(e))
     ```
   - No general chat endpoint (e.g., `POST /api/chat`) exists.
   - Only event insertion exists (`backend/main.py:139-152`):
     ```python
     @app.post("/api/events/add")
     def add_event(event: Event):
         """Adds an upcoming match or training to the calendar."""
         try:
             conn = get_db_connection()
             cursor = conn.cursor()
             cursor.execute('''
                 INSERT INTO events (athlete_id, event_date, event_type, duration_minutes)
                 VALUES (?, ?, ?, ?)
             ''', (event.athlete_id, event.event_date.strftime("%Y-%m-%d"), event.event_type, event.duration_minutes))
             conn.commit()
             conn.close()
             return {"status": "success", "message": "Event added."}
         except Exception as e:
             raise HTTPException(status_code=500, detail=str(e))
     ```
   - **Gaps**:
     - No `GET /api/events` endpoint exists (preventing frontend Calendar and Dashboard from reading events).
     - No `DELETE /api/events/{event_id}` endpoint exists.
     - No intent classification endpoint or intent-driven DB execution exists.

3. **LLM Agent Implementation (`backend/agent.py`)**:
   - Uses Groq SDK (`groq.Groq`) initialized with `GROQ_API_KEY = os.getenv("GROQ_API_KEY")` (`backend/agent.py:8-9`).
   - Line 12 specifies `MODEL = "openai/gpt-oss-120b"` (note: Groq standard models are typically `llama-3.3-70b-versatile`, `llama-3.1-70b-versatile`, etc.).
   - Contains two agent functions:
     - `get_onboarding_response(conversation_history: list) -> str` ("Grill Agent" for baseline profile discovery).
     - `generate_weekly_plan(athlete_id: int, start_date_str: str, fatigue: int = None, sleep: int = None) -> dict` (7-day rolling plan generation).
   - **Gaps**: ZERO intent routing logic, ZERO entity extraction (dates, event types), and ZERO database modification routines in `backend/agent.py`.

4. **Downstream Integration with Load Management Engine (`backend/algorithm.py`)**:
   - `algorithm.py` lines 120–145 directly consume `events` table data for safety rules:
     - Rule 1 (Pre-Match Tapering): queries `events` for tomorrow (`event_type='match'`) to cap load at 30%, and day-after-tomorrow to cap load at 50%.
     - Rule 2 (Post-Match Recovery): queries `events` for yesterday (`event_type='match'`) to enforce active recovery or passive rest if duration > 90 mins.
   - This confirms that autonomously writing events to SQLite `events` directly steers the athlete's training workload engine!

5. **Frontend State (`mobile/src/pages/Chat.tsx` and `Calendar.tsx`)**:
   - Both `mobile/src/pages/Chat.tsx` and `mobile/src/pages/Calendar.tsx` are 9-line empty stubs:
     ```tsx
     export default function Chat() {
       return (
         <div className="neu-box">
           <h2>Chat Tab</h2>
           <p>This view will be built out next!</p>
         </div>
       );
     }
     ```
   - In legacy prototype `frontend/index.html` (lines 303–329), chat sends to `/api/onboard/chat` and simply renders raw strings in a floating box.

---

### 1.2 Health Data Architecture (R4) Implementation Status

1. **Dependencies (`mobile/package.json`)**:
   - Lines 12–21 list dependencies:
     ```json
     "dependencies": {
       "@capacitor/android": "^8.5.2",
       "@capacitor/core": "^8.5.2",
       "@capacitor/geolocation": "^8.2.2",
       "@capacitor/ios": "^8.5.2",
       "lucide-react": "^1.45.0",
       "react": "^19.2.8",
       "react-dom": "^19.2.8",
       "react-router-dom": "^7.18.3"
     }
     ```
   - `@capawesome-team/capacitor-health` is **completely absent** from `package.json`.
2. **Codebase search for "health"**:
   - `grep_search` across `mobile/src` returned **0 results**.
   - No health provider interface, no mock health provider, and no platform detection exists in `mobile/src`.
   - `mobile/src/pages/Dashboard.tsx` is an empty stub with no metric cards or widgets.

---

### 1.3 Test Harness & Acceptance Test Status

1. **Repository Search for Tests**:
   - `find_by_name` across `backend` and `mobile` returned 0 user-written test files (no `test_*.py`, no `*.test.tsx`, no `*.spec.ts`).
   - `backend/requirements.txt` contains: `fastapi`, `uvicorn`, `groq`, `pydantic`, `python-dateutil`. Neither `pytest` nor `httpx` (for FastAPI TestClient) are listed.
   - `backend/simulator.py` (lines 1–75) only tests `/api/logs/submit` and `/api/plan/generate`. It does not test chat or calendar updates.
   - `mobile/package.json` contains no test script (no `vitest`, `jest`, or `playwright`).
2. **Authoritative Acceptance Criteria (`ORIGINAL_REQUEST.md`)**:
   - **R2 Acceptance Criterion**:
     `"An agent sends a test string ("I have a match tomorrow") to the chat endpoint, and programmatically verifies the SQLite events table was autonomously updated with the new match."`
   - **R4 Acceptance Criterion**:
     `"An agent starts the Vite dev server, navigates the 5 tabs in the browser, and visually confirms (via screenshot or DOM check) that the Strava-style layout and Health mock providers load without crashing."`

---

## 2. Logic Chain

### 2.1 Logic Chain for R2 (AI Intent Router)

1. **Premise 1**: The user sends natural language messages (e.g. `"I have a match tomorrow"`, `"Make today lighter, my knee hurts"`, or `"What should I eat before a match?"`) to a chat endpoint.
2. **Premise 2**: These messages represent three mutually exclusive intent categories:
   - `Update Calendar`: User enters, changes, or removes competitions/practices.
   - `Update Plan`: User reports subjective feedback (soreness, fatigue, injury) requesting workout adaptation.
   - `General QA`: User seeks advice, explanations, or conversational interaction.
3. **Premise 3**: For `Update Calendar`, the acceptance test specifically requires: sending `"I have a match tomorrow"` must cause the backend to update SQLite table `events` with a match for tomorrow.
4. **Premise 4**: Relying purely on an external cloud LLM (Groq) for acceptance testing creates fragile dependencies on:
   - External network connectivity
   - Valid `GROQ_API_KEY` present in runtime environment
   - Groq API rate limits and model availability
5. **Deduction 1 (Dual-Engine Router Architecture)**:
   The backend chat architecture must employ a **hybrid intent router**:
   - **Primary Engine**: LLM (Groq) with structured JSON prompt / function calling for complex, ambiguous, or multi-turn queries.
   - **Deterministic Fallback Engine**: Rule-based regex/NLP pattern matcher using `python-dateutil` and regex pattern matching:
     - Regex pattern `r"(match|game|trial|practice|training)\s+(tomorrow|today|on\s+\w+)"` or `"have a match tomorrow"` deterministically classifies `Update Calendar`, sets `event_type='match'`, and calculates `event_date = date.today() + timedelta(days=1)`.
     - Regex pattern `r"(knee|ankle|sore|hurt|tired|exhausted|lighter|rest day)"` classifies `Update Plan`.
     - Everything else falls back to `General QA`.
   - This ensures 100% deterministic success during automated acceptance tests and offline environments, while enabling LLM intelligence when `GROQ_API_KEY` is configured.
6. **Deduction 2 (Autonomous DB Modification)**:
   When `Update Calendar` is identified:
   - Extract: `event_date` (relative or absolute), `event_type` (`match`, `training`, `trial`), `duration_minutes` (default 90 min for matches, 60 min for training), `title`.
   - Write directly to `events` table via SQLite cursor inside a transaction.
   - Return confirmation: `"Got it! Scheduled your match for tomorrow (2026-09-14). I've updated your calendar and your training plan will taper accordingly."`
7. **Deduction 3 (Calendar Read API)**:
   To make the Calendar and Dashboard tabs functional in the mobile SPA, `backend/main.py` must expose `GET /api/events` returning JSON array of events for the given athlete.

---

### 2.2 Logic Chain for R4 (Health Data Architecture)

1. **Premise 1**: Native mobile devices (Android/iOS) expose health data through Health Connect and HealthKit, which `@capawesome-team/capacitor-health` accesses.
2. **Premise 2**: In standard web browsers (such as during `vite dev` or browser acceptance testing), native Capacitor plugins are unavailable and throw runtime exceptions (e.g. `Plugin 'Health' not implemented on web`).
3. **Premise 3**: Acceptance criterion R4 states:
   `"Implement a provider interface for @capawesome-team/capacitor-health that gracefully falls back to mock data when running in a web browser, ensuring seamless local development before device deployment."`
4. **Deduction 1 (Strategy Pattern & Provider Interface)**:
   A TypeScript interface `IHealthProvider` must be defined with methods:
   - `isAvailable(): Promise<boolean>`
   - `requestPermissions(): Promise<boolean>`
   - `getTodayMetrics(): Promise<HealthMetrics>`
   - `getHistoricalMetrics(days: number): Promise<HealthMetrics[]>`
   where `HealthMetrics` includes `{ steps, activeCalories, distanceMeters, sleepMinutes, restingHeartRate, hrvMs, date, source }`.
5. **Deduction 2 (Implementation Hierarchy)**:
   - `NativeHealthProvider`: Interacts with `@capawesome-team/capacitor-health`. Wraps all plugin calls in defensive checks (`Capacitor.isNativePlatform()`).
   - `MockHealthProvider`: Returns realistic athlete telemetry (e.g., 8,420 steps, 580 kcal, 6.2 km, 465 min sleep, 58 bpm resting HR, 65 ms HRV).
   - `HealthProviderFactory`:
     ```typescript
     export class HealthProviderFactory {
       static getProvider(): IHealthProvider {
         if (Capacitor.isNativePlatform()) {
           try {
             return new NativeHealthProvider();
           } catch {
             return new MockHealthProvider();
           }
         }
         return new MockHealthProvider();
       }
     }
     ```
   - React Hook `useHealthData()`: Exposes `{ metrics, loading, isMock, refresh }` to `Dashboard.tsx`.
6. **Deduction 3 (Zero Build/Runtime Failure Guarantee)**:
   Because `@capawesome-team/capacitor-health` is not yet installed in `mobile/package.json` and npm registry access might vary, `NativeHealthProvider` must dynamically check or safely import the plugin, ensuring Vite build (`npm run build`) and dev server (`vite dev`) succeed without build breakages.

---

## 3. Caveats

1. **Groq API Key Dependency**: If `GROQ_API_KEY` is not set in `.env` or system environment, pure LLM calls fail with an authentication error. The hybrid router fallback is mandatory to prevent broken test suites.
2. **Package Name Verification**: `@capawesome-team/capacitor-health` is the scoped package mentioned in `ORIGINAL_REQUEST.md` and `plan.md`. In public npm, Capawesome packages sometimes exist under `@capawesome/capacitor-health`. The provider wrapper must be decoupled such that the application compiles and works cleanly regardless of package registry variations.
3. **Database Schema Harmonization with R1**:
   - Explorer Survey 1 is investigating R1 (`users`, `google_fit_logs`, `training_plans` daily streaks, and 1-day rolling Quests).
   - `events` table modifications (adding optional columns `title TEXT`, `location TEXT`, `source TEXT DEFAULT 'manual'`) must remain backwards-compatible with `backend/algorithm.py`'s queries (`SELECT event_date, event_type, duration_minutes FROM events`).
4. **Timezone and Date Parsing**: When parsing `"tomorrow"`, the server must use the athlete's local date context (or server date `datetime.now().date() + timedelta(days=1)`).

---

## 4. Conclusion

### 4.1 Required Architecture for R2 (AI Intent Router)

```
                       User Chat Message
                              │
                              ▼
                      POST /api/chat
                              │
             ┌────────────────┴────────────────┐
             ▼                                 ▼
      [LLM Router]                     [Regex Rule Router]
    (Groq API with JSON)             (Fast deterministic fallback)
             │                                 │
             └────────────────┬────────────────┘
                              ▼
                     Intent Classification
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
   UPDATE_CALENDAR       UPDATE_PLAN          GENERAL_QA
          │                   │                   │
  Extract Entities      Extract Parameters   Coaching Advice
  - event_type: match   - target: today      - nutritional/
  - event_date: +1 day  - intensity: lower     physiological
  - duration: 90m       - reason: fatigue      guidance
          │                   │                   │
          ▼                   ▼                   ▼
   INSERT INTO events    UPDATE training_     NO DB writes
   (auto-commits DB)     plans (Quests)       (logs chat)
          │                   │                   │
          └───────────────────┼───────────────────┘
                              ▼
                      Formatted Response
```

#### Detailed API Specification for R2:
- **Endpoint**: `POST /api/chat`
- **Request Payload**:
  ```json
  {
    "athlete_id": 1,
    "message": "I have a match tomorrow",
    "history": []
  }
  ```
- **Response Payload**:
  ```json
  {
    "status": "success",
    "intent": "Update Calendar",
    "reply": "I've added your match scheduled for tomorrow to your calendar. Your workload forecast will adjust to taper before the match.",
    "action_taken": {
      "type": "database_insert",
      "table": "events",
      "record": {
        "athlete_id": 1,
        "event_date": "2026-09-14",
        "event_type": "match",
        "duration_minutes": 90,
        "title": "Match"
      }
    }
  }
  ```
- **Companion Endpoints**:
  - `GET /api/events?athlete_id={id}`: Returns list of upcoming events for the Calendar tab and Dashboard "Upcoming Trials" card.
  - `DELETE /api/events/{event_id}`: Allows deleting an event.

---

### 4.2 Required Architecture for R4 (Health Data Architecture)

```
                         Dashboard Component
                                 │
                                 ▼
                          useHealthData()
                                 │
                                 ▼
                       HealthProviderFactory
                                 │
                ┌────────────────┴────────────────┐
                ▼                                 ▼
        Capacitor Native?                   Web Browser?
                │                                 │
                ▼                                 ▼
       NativeHealthProvider               MockHealthProvider
  (@capawesome-team/capacitor-health)    (Realistic athlete metrics)
```

#### Directory & File Layout for R4:
```
mobile/src/services/health/
├── types.ts                # IHealthProvider, HealthMetrics, HealthPermissionStatus
├── NativeHealthProvider.ts # Native plugin implementation
├── MockHealthProvider.ts   # Browser fallback with realistic simulated metrics
├── HealthProviderFactory.ts# Platform detection and factory instantiation
├── useHealthData.ts        # React hook for easy UI consumption
└── index.ts                # Barrel export
```

#### HealthMetrics Contract:
```typescript
export interface HealthMetrics {
  steps: number;             // e.g. 8,420
  activeCalories: number;    // e.g. 580 kcal
  distanceMeters: number;    // e.g. 6,200 m
  sleepMinutes: number;      // e.g. 465 min (7h 45m)
  restingHeartRate: number;  // e.g. 58 bpm
  hrvMs?: number;            // e.g. 65 ms
  date: string;              // YYYY-MM-DD
  source: 'native' | 'mock';
}
```

---

## 5. Verification Method

### 5.1 Verification Script for R2 (AI Intent Router)

Create an automated verification test script `backend/tests/verify_r2_intent.py`:

```python
import sqlite3
import os
import requests
from datetime import date, timedelta

BASE_URL = "http://localhost:8000"
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "athlete_planner.db")

def test_intent_router_match_tomorrow():
    tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    # 1. Clean existing matches for tomorrow to ensure clean test
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM events WHERE event_date = ? AND event_type = 'match'", (tomorrow,))
    conn.commit()
    conn.close()

    # 2. Call chat endpoint with authoritative test string
    payload = {
        "athlete_id": 1,
        "message": "I have a match tomorrow",
        "history": []
    }
    res = requests.post(f"{BASE_URL}/api/chat", json=payload)
    assert res.status_code == 200, f"Chat endpoint failed: {res.status_code} {res.text}"
    data = res.json()
    assert "Calendar" in data.get("intent", ""), f"Unexpected intent: {data.get('intent')}"

    # 3. Verify SQLite events table was autonomously updated
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, athlete_id, event_date, event_type FROM events WHERE event_date = ? AND event_type = 'match'", (tomorrow,))
    row = cursor.fetchone()
    conn.close()

    assert row is not None, f"Assertion failed: SQLite events table does not contain match for {tomorrow}"
    print(f"PASS: SQLite events table autonomously updated with match: {row}")

if __name__ == "__main__":
    test_intent_router_match_tomorrow()
```

### 5.2 Verification Procedure for R4 (Health Data Architecture)

1. **Static Build Check**:
   ```powershell
   cd d:\IIT-Bhuv\mobile
   npm run build
   ```
   Must compile without TypeScript errors (`tsc -b`) and bundle Vite assets cleanly.
2. **Browser Runtime Check**:
   ```powershell
   cd d:\IIT-Bhuv\mobile
   npm run dev
   ```
   - Open browser at `http://localhost:5173`.
   - Verify Dashboard tab displays: Steps, Active Calories, Distance, Sleep, Resting HR.
   - Verify browser console: no `Uncaught Error: Plugin 'Health' not implemented on web`.
   - Verify health metrics source indicator shows mock fallback active in browser.

### 5.3 Invalidation Conditions
- If the chat endpoint requires manual confirmation before writing to SQLite, the R2 acceptance criterion is violated.
- If sending `"I have a match tomorrow"` fails when `GROQ_API_KEY` is not provided, the test harness is brittle and invalid.
- If the frontend Dashboard crashes or fails to render stats cards in the browser, the R4 acceptance criterion is violated.
