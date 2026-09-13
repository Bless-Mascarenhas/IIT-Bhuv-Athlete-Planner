# Survey Explorer 1 Report: Backend Architecture & Database Structure (R1)

**Working Directory**: `d:\IIT-Bhuv\.agents\explorer_survey_1`  
**Date**: 2026-09-13  
**Status**: Hard Handoff (Investigation Complete)  

---

## 1. Observation

### 1.1 Backend Framework and Entry Point
- **Framework**: FastAPI (`v0.141.1`) running on Uvicorn (`v0.52.4`) under Python `3.14.0`.
- **Primary Entry Point**: `d:\IIT-Bhuv\backend\main.py`.
- **CORS Configuration** (`backend/main.py:11-17`):
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["*"],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```
- **Existing Routes** in `backend/main.py`:
  1. `GET /`: Returns `{"status": "ok", "message": "Athlete Planner API is running. Ready for Capacitor UI."}` (`lines 42-44`).
  2. `GET /api/data/acwr_history`: Reads `backend/user_data.csv` and returns rolling 28-day ACWR history for Chart.js (`lines 49-79`).
  3. `POST /api/onboard/chat`: Accepts `ChatRequest(history: List[ChatMessage])` and queries `agent.get_onboarding_response` ("Grill" agent) (`lines 81-89`).
  4. `POST /api/plan/generate`: Accepts `athlete_id: int`, `target_date: date`, optional `current_fatigue: int`, `current_sleep: int`. Calls `agent.generate_weekly_plan(...)`, inserting a 7-day array of daily items into `training_plans` (`lines 91-118`).
  5. `POST /api/logs/submit`: Accepts `DailyLog(athlete_id, log_date, rpe, duration_minutes, sleep_quality, fatigue, soreness)`. Computes `acute_workload = rpe * duration_minutes` and inserts into `daily_logs` (`lines 120-137`).
  6. `POST /api/events/add`: Accepts `Event(athlete_id, event_date, event_type, duration_minutes)`. Inserts into `events` (`lines 139-154`).

### 1.2 SQLite Database Configuration & Session Management
- **Database Location**: `d:\IIT-Bhuv\backend\athlete_planner.db`.
- **Configured paths**:
  - `backend/database.py:4`: `DB_PATH = os.path.join(os.path.dirname(__file__), "athlete_planner.db")`
  - `backend/algorithm.py:5`: `DB_PATH = os.path.join(os.path.dirname(__file__), "athlete_planner.db")`
- **Connection Handling**:
  - Standard library `sqlite3` without ORM (no SQLAlchemy, no SQLModel).
  - Helper in `backend/algorithm.py:7-10`:
    ```python
    def get_db_connection():
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    ```
  - Connections are opened per request/call and manually closed.
- **Existing Table Schemas Verified in `athlete_planner.db` via `sqlite_master`**:
  - **`athletes`**:
    ```sql
    CREATE TABLE athletes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        sport_type TEXT DEFAULT 'team_sport',
        baseline_fatigue REAL DEFAULT 5.0,
        baseline_sleep REAL DEFAULT 7.0
    );
    ```
  - **`events`**:
    ```sql
    CREATE TABLE events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        athlete_id INTEGER,
        event_date DATE NOT NULL,
        event_type TEXT NOT NULL, -- e.g., 'match', 'training'
        duration_minutes INTEGER,
        FOREIGN KEY(athlete_id) REFERENCES athletes(id)
    );
    ```
  - **`daily_logs`**:
    ```sql
    CREATE TABLE daily_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        athlete_id INTEGER,
        log_date DATE NOT NULL,
        rpe INTEGER, 
        duration_minutes INTEGER,
        sleep_quality INTEGER, 
        fatigue INTEGER, 
        soreness INTEGER,
        acute_workload REAL,
        FOREIGN KEY(athlete_id) REFERENCES athletes(id)
    );
    ```
  - **`training_plans`**:
    ```sql
    CREATE TABLE training_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        athlete_id INTEGER,
        plan_date DATE NOT NULL,
        intensity_category TEXT NOT NULL, -- 'Rest', 'Recovery', 'Moderate', 'High'
        target_load REAL,
        status TEXT DEFAULT 'planned', -- 'planned', 'completed', 'revised'
        revision_reason TEXT,
        FOREIGN KEY(athlete_id) REFERENCES athletes(id)
    );
    ```
  - Current Row Counts: `athletes: 3`, `events: 0`, `daily_logs: 105`, `training_plans: 22`.

### 1.3 Training Plan Generator Implementation
- **Files**: `backend/agent.py` and `backend/algorithm.py`.
- **Workflow**:
  1. `main.py:generate_plan` calls `agent.generate_weekly_plan(athlete_id, target_date_str, current_fatigue, current_sleep)`.
  2. `agent.py:47` calls `algorithm.evaluate_daily_constraints(athlete_id, start_date_str, fatigue, sleep)`, which enforces 5 hard load-management rules:
     - Rule 1: Pre-Match Tapering (24h = <30% load, 48h = <50% load).
     - Rule 2: Post-Match Recovery (Day after = Active Recovery Max 25%, Rest if match > 90 mins).
     - Rule 3: Fatigue / Wellness Threshold (Fatigue > 7 OR Sleep < 5 -> Forced Recovery Max 40% load).
     - Rule 4: Acute:Chronic Workload Ratio (ACWR > 1.5 -> Remove 'High', Max 70% load).
     - Rule 5: Consecutive High-Intensity Days (>= 2 -> Remove 'High').
  3. `agent.py:54-57` fetches calendar events for next 7 days from `events`.
  4. `agent.py:8-12` configures Groq LLM:
     ```python
     GROQ_API_KEY = os.getenv("GROQ_API_KEY")
     client = Groq(api_key=GROQ_API_KEY)
     MODEL = "openai/gpt-oss-120b"
     ```
  5. `agent.py:101-106` calls Groq `chat.completions.create` requesting a 7-day schedule array with keys `date`, `intensity`, `session_description`, `target_rpe`, `duration_mins`, `agent_reasoning`.
  6. `main.py:101-112` iterates over `weekly_plan` and inserts 7 rows into `training_plans`.

### 1.4 Critical Defect Observed: Top-Level `Groq(api_key=None)` Crash
- In `backend/agent.py:9`, `client = Groq(api_key=GROQ_API_KEY)` is executed at top-level module import.
- Running `python -c "import main"` when `GROQ_API_KEY` is not set in environment immediately crashes with:
  ```
  groq.GroqError: The api_key client option must be set either by passing api_key to the client or by setting the GROQ_API_KEY environment variable
  ```
- Running with a dummy key (`GROQ_API_KEY=gsk_test`) allows import, but calling `/api/plan/generate` fails with `500 Internal Server Error (401 Invalid API Key)` unless an active paid Groq key is provided.

### 1.5 Python Environment & Backend Dependencies
- **Interpreter**: `d:\IIT-Bhuv\backend\venv\Scripts\python.exe` (Python 3.14.0).
- **Installed Packages**: `fastapi (0.141.1)`, `uvicorn (0.52.4)`, `groq (1.7.0)`, `pydantic (2.13.5)`, `python-dateutil (2.9.0.post0)`, `httpx (0.28.1)`, `requests (2.34.2)`, `starlette (1.6.0)`.
- `pytest` is **not** currently installed in `venv`. However, standard library `unittest` and `starlette.testclient.TestClient` / `fastapi.testclient.TestClient` are fully functional without any extra installation.

---

## 2. Logic Chain

1. **R1 Requirement Definition**:
   `ORIGINAL_REQUEST.md` requires:
   - "Transition the backend to a 1-day rolling 'Quests' generator."
   - "Implement new database tables (`users`, `google_fit_logs`)."
   - "Update `training_plans` to track task completion for daily streaks."
   - Acceptance Criteria: "An agent successfully executes a script that calls the API to generate a 1-day rolling plan, and programmatically verifies the `training_plans` SQLite table contains exactly one day of data formatted as Quests."

2. **From 7-Day Plan to 1-Day Rolling Quests**:
   - In commit `16d84a1`, the generator was expanded to 7 days, returning a `weekly_plan` array.
   - For R1, the generator must target the athlete's single day (`target_date` or today) and output a structured list of actionable daily "Quests" (e.g. Warm-up/Mobility, Main Workout, Recovery/Cool-down).
   - In `training_plans`, records inserted for that generation must belong strictly to that target date (`plan_date == target_date`), with columns that represent Quests: `quest_title`, `session_description`, `task_type`, `target_rpe`, `duration_minutes`, `target_load`, `status`, `is_completed`.
   - Before inserting new quests for that date, any prior uncompleted/planned quests for that `(athlete_id, target_date)` should be cleared so the table contains exactly one day of active quests.

3. **Database Architecture & Evolution**:
   - **`users` Table**:
     Currently athletes are in `athletes` table. `plan.md` and R1 demand user identity with streak tracking and settings.
     Schema must provide:
     `id`, `name`, `email`, `sport_type`, `dob`, `height`, `weight`, `daily_streak` (integer, default 0), `last_streak_date` (date), `baseline_fatigue`, `baseline_sleep`, `created_at`.
     A default user row (`id=1`, `name='Champ'`, `daily_streak=12`) should be seeded for instant compatibility with mobile's persistent header (`Header.tsx` hardcoded value: 12).
   - **`google_fit_logs` Table**:
     R1 and R4 require health data storage (Steps, Active Calories, Distance, Sleep, Resting HR, HRV).
     Schema must provide:
     `id`, `user_id`, `log_date`, `steps`, `active_calories`, `distance_meters`, `sleep_minutes`, `resting_hr`, `hrv`, `source` (default 'google_fit' or 'mock'), `raw_data`, `created_at`, with `UNIQUE(user_id, log_date)`.
   - **`training_plans` Table Migration**:
     Add columns: `quest_title TEXT`, `session_description TEXT`, `task_type TEXT`, `target_rpe INTEGER`, `duration_minutes INTEGER`, `is_completed INTEGER DEFAULT 0`, `completed_at TIMESTAMP`.
     Using `ALTER TABLE training_plans ADD COLUMN ...` if columns don't exist ensures seamless migration of existing databases.

4. **Task Completion & Streak Logic**:
   - An endpoint (`POST /api/plan/complete-quest` or `POST /api/quests/{quest_id}/complete`) must update `training_plans.is_completed = 1` and `status = 'completed'`.
   - When a quest is completed:
     If `users.last_streak_date != today`:
       - If `users.last_streak_date == yesterday`: increment `users.daily_streak += 1`.
       - Else: set `users.daily_streak = 1`.
       - Set `users.last_streak_date = today`.
     Returns updated streak counter for mobile header sync.

5. **LLM Fallback & Offline Resilience**:
   - Because `GROQ_API_KEY` may be unset in test environments or CI, `agent.py` must:
     a. Initialize `Groq` conditionally (`if GROQ_API_KEY: client = Groq(...)`).
     b. Provide an algorithmic heuristic generator when Groq is unavailable or throws errors.
     c. Use `algorithm.evaluate_daily_constraints` to produce sport-science-compliant Quests (Rest, Recovery, Moderate, High) deterministically.
     This ensures 100% test reliability and eliminates 500 crashes during acceptance verification.

---

## 3. Caveats

1. **Groq Model Dependency**:
   In `agent.py:12`, `MODEL = "openai/gpt-oss-120b"` is configured. On Groq, commonly supported models are `llama-3.3-70b-versatile` or `llama3-70b-8192`. If an external Groq key is supplied in production, ensure the model string is supported by the user's Groq tier, and ensure the heuristic fallback is always present.
2. **Backwards Compatibility with `athletes`**:
   Existing endpoints use `athlete_id`. The new `users` table should either replace `athletes` or synchronize with it (`athlete_id == user_id == 1`) so existing routes and foreign keys continue functioning without regression.
3. **Intent Router (R2 Scope)**:
   R2 will introduce conversational intent routing to update `events` and `training_plans`. The database schema designed here directly provides the necessary tables (`events`, `training_plans`, `users`) that R2's router will modify.

---

## 4. Conclusion & Concrete Implementation Recommendations

### 4.1 Required Schema Changes (`database.py`)
Update `database.py:init_db()` to create the following tables and migrations:

```python
# 1. New Users Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT,
    sport_type TEXT DEFAULT 'team_sport',
    dob DATE,
    height REAL DEFAULT 175.0,
    weight REAL DEFAULT 70.0,
    daily_streak INTEGER DEFAULT 0,
    last_streak_date DATE,
    baseline_fatigue REAL DEFAULT 5.0,
    baseline_sleep REAL DEFAULT 7.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# Seed default user if empty
cursor.execute("SELECT count(*) FROM users")
if cursor.fetchone()[0] == 0:
    cursor.execute('''
        INSERT INTO users (id, name, sport_type, daily_streak, last_streak_date)
        VALUES (1, 'Champ', 'Soccer', 12, DATE('now', '-1 day'))
    ''')

# 2. New Google Fit Logs Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS google_fit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    log_date DATE NOT NULL,
    steps INTEGER DEFAULT 0,
    active_calories REAL DEFAULT 0.0,
    distance_meters REAL DEFAULT 0.0,
    sleep_minutes INTEGER DEFAULT 0,
    resting_hr REAL DEFAULT 0.0,
    hrv REAL DEFAULT 0.0,
    source TEXT DEFAULT 'google_fit',
    raw_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, log_date),
    FOREIGN KEY(user_id) REFERENCES users(id)
)
''')

# 3. Dynamic Migration for training_plans
cursor.execute("PRAGMA table_info(training_plans)")
existing_cols = [col[1] for col in cursor.fetchall()]

new_cols = {
    'quest_title': 'TEXT DEFAULT ""',
    'session_description': 'TEXT DEFAULT ""',
    'task_type': 'TEXT DEFAULT "main"',
    'target_rpe': 'INTEGER DEFAULT 5',
    'duration_minutes': 'INTEGER DEFAULT 30',
    'is_completed': 'INTEGER DEFAULT 0',
    'completed_at': 'TIMESTAMP'
}

for col_name, col_type in new_cols.items():
    if col_name not in existing_cols:
        cursor.execute(f"ALTER TABLE training_plans ADD COLUMN {col_name} {col_type}")
```

### 4.2 1-Day Rolling Quests Generator Specification (`agent.py`)
Refactor `generate_weekly_plan` into `generate_daily_quests(athlete_id: int, target_date_str: str, fatigue: int = None, sleep: int = None) -> dict`:
- Evaluates `constraints = evaluate_daily_constraints(athlete_id, target_date_str, fatigue, sleep)`.
- If Groq client and key exist, calls LLM requesting JSON:
  ```json
  {
    "date": "2026-09-13",
    "intensity": "Recovery",
    "quests": [
      {
        "title": "Morning Activation & Mobility",
        "description": "Dynamic stretching, foam rolling for hips and thoracic spine.",
        "task_type": "warmup",
        "intensity": "Recovery",
        "target_rpe": 3,
        "duration_mins": 15,
        "agent_reasoning": "Promotes blood flow without accumulating acute fatigue."
      },
      {
        "title": "Low-Impact Active Recovery Flush",
        "description": "Zone 1 easy cycling or brisk walking.",
        "task_type": "main",
        "intensity": "Recovery",
        "target_rpe": 3,
        "duration_mins": 30,
        "agent_reasoning": "Honors forced recovery constraint due to ACWR spike."
      }
    ]
  }
  ```
- **Heuristic Fallback**:
  If Groq fails or `GROQ_API_KEY` is absent, generate 2-3 structured Quests matching `constraints['allowed_intensity'][-1]`, setting realistic RPE and durations adhering to `max_load_percentage`.

### 4.3 Endpoint Specifications (`main.py`)
1. **`POST /api/plan/generate`**:
   - Parameters: `athlete_id: int = 1`, `target_date: Optional[date] = None`, `current_fatigue: Optional[int] = None`, `current_sleep: Optional[int] = None`.
   - Clears prior uncompleted quests for `(athlete_id, target_date)`.
   - Generates 1-day rolling Quests.
   - Inserts each quest as a row in `training_plans`.
   - Returns:
     ```json
     {
       "status": "success",
       "plan_date": "2026-09-13",
       "was_revised": false,
       "constraint_reasons": [],
       "quests": [...]
     }
     ```
2. **`GET /api/plan/today`**:
   - Query: `athlete_id: int = 1`, `date: Optional[str] = None`.
   - Returns today's quests from `training_plans`.
3. **`POST /api/quests/{quest_id}/complete`**:
   - Updates `is_completed = 1`, `status = 'completed'`, `completed_at = CURRENT_TIMESTAMP`.
   - Updates `users.daily_streak` and `users.last_streak_date`.
   - Returns `{"status": "success", "quest_id": quest_id, "is_completed": 1, "daily_streak": user_streak}`.
4. **`POST /api/health/sync`**:
   - Ingests health metrics into `google_fit_logs`.
   - Returns `{"status": "success", "message": "Synced successfully"}`.
5. **`GET /api/health/today`**:
   - Returns today's health metrics from `google_fit_logs`.
6. **`GET /api/user/profile`**:
   - Returns user profile and current `daily_streak`.

---

## 5. Verification Method

### 5.1 Verification Commands
The implementer can independently verify all changes using the following Python verification script:

```bash
# 1. Run database initialization and migration
d:\IIT-Bhuv\backend\venv\Scripts\python.exe -c "import database; database.init_db()"

# 2. Verify tables exist in athlete_planner.db
d:\IIT-Bhuv\backend\venv\Scripts\python.exe -c "import sqlite3; conn = sqlite3.connect('athlete_planner.db'); cursor = conn.cursor(); tables = [r[0] for r in cursor.execute('SELECT name FROM sqlite_master WHERE type=\'table\'').fetchall()]; print('Tables:', tables); assert 'users' in tables and 'google_fit_logs' in tables and 'training_plans' in tables"

# 3. Verify training_plans schema contains Quest columns
d:\IIT-Bhuv\backend\venv\Scripts\python.exe -c "import sqlite3; conn = sqlite3.connect('athlete_planner.db'); cursor = conn.cursor(); cols = [c[1] for c in cursor.execute('PRAGMA table_info(training_plans)').fetchall()]; print('Cols:', cols); assert all(k in cols for k in ['quest_title', 'session_description', 'task_type', 'target_rpe', 'duration_minutes', 'is_completed'])"

# 4. Programmatic Acceptance Test for R1 (Using TestClient):
d:\IIT-Bhuv\backend\venv\Scripts\python.exe -c "from fastapi.testclient import TestClient; import main, sqlite3; client = TestClient(main.app); res = client.post('/api/plan/generate?athlete_id=1&target_date=2026-09-13'); print('Status:', res.status_code); assert res.status_code == 200; data = res.json(); assert data['status'] == 'success' and 'quests' in data; conn = sqlite3.connect('athlete_planner.db'); cursor = conn.cursor(); dates = cursor.execute('SELECT DISTINCT plan_date FROM training_plans WHERE athlete_id=1 AND plan_date=\"2026-09-13\"').fetchall(); print('Dates in DB:', dates); assert len(dates) == 1; quests = cursor.execute('SELECT quest_title, target_rpe, duration_minutes, is_completed FROM training_plans WHERE athlete_id=1 AND plan_date=\"2026-09-13\"').fetchall(); print('Quests found:', quests); assert len(quests) >= 1; print('R1 VERIFIED SUCCESSFULLY!')"
```

### 5.2 Invalidation Conditions
- If `training_plans` contains rows for more than one date when `/api/plan/generate` is called for a single target date.
- If `import main` fails when `GROQ_API_KEY` is not present in the environment.
- If `users` or `google_fit_logs` tables fail to create or are missing required columns.
- If completing a quest does not update `training_plans.is_completed` or does not increment `users.daily_streak`.
