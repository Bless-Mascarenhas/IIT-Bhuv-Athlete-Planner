import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "athlete_planner.db")

def get_db_connection(db_path: str = None):
    """Returns a SQLite connection with Row row_factory for dict-like access."""
    target_path = db_path if db_path else DB_PATH
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: str = None):
    target_path = db_path if db_path else DB_PATH
    conn = sqlite3.connect(target_path)
    cursor = conn.cursor()

    # Athletes Table (preserved for backward compatibility)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS athletes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        sport_type TEXT DEFAULT 'team_sport',
        baseline_fatigue REAL DEFAULT 5.0,
        baseline_sleep REAL DEFAULT 7.0
    )
    ''')

    # Seed default athlete if empty
    cursor.execute("SELECT count(*) FROM athletes")
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO athletes (id, name, sport_type, baseline_fatigue, baseline_sleep)
            VALUES (1, 'Champ', 'team_sport', 5.0, 7.0)
        ''')

    # Users Table for athlete profile and streak tracking
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT,
        current_streak INTEGER DEFAULT 12,
        daily_streak INTEGER DEFAULT 12,
        sport_type TEXT DEFAULT 'Soccer',
        last_active_date DATE,
        last_streak_date DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

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

    # Daily Logs (Data pulled from device or entered manually)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS daily_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        athlete_id INTEGER,
        log_date DATE NOT NULL,
        rpe INTEGER, 
        duration_minutes INTEGER,
        sleep_quality INTEGER, 
        fatigue INTEGER, 
        soreness INTEGER,
        acute_workload REAL, -- RPE * duration_minutes (Session-RPE method)
        FOREIGN KEY(athlete_id) REFERENCES athletes(id)
    )
    ''')

    # Google Fit Telemetry Logs Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS google_fit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        log_date DATE NOT NULL,
        steps INTEGER DEFAULT 0,
        active_calories REAL DEFAULT 0.0,
        calories_burned REAL DEFAULT 0.0,
        distance_meters REAL DEFAULT 0.0,
        sleep_minutes INTEGER DEFAULT 0,
        sleep_hours REAL DEFAULT 0.0,
        heart_rate_avg REAL DEFAULT 0.0,
        resting_hr REAL DEFAULT 0.0,
        heart_rate_resting REAL DEFAULT 0.0,
        hrv REAL DEFAULT 0.0,
        source TEXT DEFAULT 'google_fit',
        synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, log_date),
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    ''')

    # Training Plans (1-Day Rolling Quests & Historical Plans)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS training_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        athlete_id INTEGER,
        plan_date DATE NOT NULL,
        intensity_category TEXT NOT NULL DEFAULT 'Moderate', -- 'Rest', 'Recovery', 'Moderate', 'High'
        target_load REAL DEFAULT 0.0,
        status TEXT DEFAULT 'planned', -- 'planned', 'completed', 'revised'
        revision_reason TEXT DEFAULT '',
        quest_title TEXT DEFAULT '',
        session_description TEXT DEFAULT '',
        task_type TEXT DEFAULT 'workout', -- 'workout', 'recovery', 'wellness'
        target_rpe INTEGER DEFAULT 5,
        duration_minutes INTEGER DEFAULT 30,
        is_completed BOOLEAN DEFAULT 0,
        completed_at TIMESTAMP,
        FOREIGN KEY(athlete_id) REFERENCES athletes(id)
    )
    ''')

    # Dynamic schema migration for training_plans table
    cursor.execute("PRAGMA table_info(training_plans)")
    existing_plan_cols = [col[1] for col in cursor.fetchall()]

    plan_migrations = {
        'quest_title': 'TEXT DEFAULT ""',
        'session_description': 'TEXT DEFAULT ""',
        'task_type': 'TEXT DEFAULT "workout"',
        'target_rpe': 'INTEGER DEFAULT 5',
        'duration_minutes': 'INTEGER DEFAULT 30',
        'is_completed': 'BOOLEAN DEFAULT 0',
        'completed_at': 'TIMESTAMP'
    }

    for col_name, col_def in plan_migrations.items():
        if col_name not in existing_plan_cols:
            cursor.execute(f"ALTER TABLE training_plans ADD COLUMN {col_name} {col_def}")

    # Dynamic schema migration for users table
    cursor.execute("PRAGMA table_info(users)")
    existing_user_cols = [col[1] for col in cursor.fetchall()]

    user_migrations = {
        'current_streak': 'INTEGER DEFAULT 12',
        'daily_streak': 'INTEGER DEFAULT 12',
        'sport_type': 'TEXT DEFAULT "Soccer"',
        'last_active_date': 'DATE',
        'last_streak_date': 'DATE',
        'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
    }

    for col_name, col_def in user_migrations.items():
        if col_name not in existing_user_cols:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}")

    # Dynamic schema migration for google_fit_logs table
    cursor.execute("PRAGMA table_info(google_fit_logs)")
    existing_fit_cols = [col[1] for col in cursor.fetchall()]

    fit_migrations = {
        'active_calories': 'REAL DEFAULT 0.0',
        'calories_burned': 'REAL DEFAULT 0.0',
        'distance_meters': 'REAL DEFAULT 0.0',
        'sleep_minutes': 'INTEGER DEFAULT 0',
        'sleep_hours': 'REAL DEFAULT 0.0',
        'heart_rate_avg': 'REAL DEFAULT 0.0',
        'resting_hr': 'REAL DEFAULT 0.0',
        'heart_rate_resting': 'REAL DEFAULT 0.0',
        'hrv': 'REAL DEFAULT 0.0',
        'source': 'TEXT DEFAULT "google_fit"'
    }

    for col_name, col_def in fit_migrations.items():
        if col_name not in existing_fit_cols:
            cursor.execute(f"ALTER TABLE google_fit_logs ADD COLUMN {col_name} {col_def}")

    # Seed default user (id=1, name='Champ', daily_streak=12) if empty
    cursor.execute("SELECT count(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO users (id, name, email, current_streak, daily_streak, sport_type, last_active_date, last_streak_date)
            VALUES (1, 'Champ', 'athlete@pace.ai', 12, 12, 'Soccer', DATE('now', '-1 day'), DATE('now', '-1 day'))
        ''')
    else:
        # Ensure user id=1 exists
        cursor.execute("SELECT id, daily_streak, last_streak_date FROM users WHERE id=1")
        u = cursor.fetchone()
        if not u:
            cursor.execute('''
                INSERT INTO users (id, name, email, current_streak, daily_streak, sport_type, last_active_date, last_streak_date)
                VALUES (1, 'Champ', 'athlete@pace.ai', 12, 12, 'Soccer', DATE('now', '-1 day'), DATE('now', '-1 day'))
            ''')
        else:
            # Sync last_streak_date if null
            if u[2] is None:
                cursor.execute("UPDATE users SET last_streak_date = DATE('now', '-1 day'), last_active_date = DATE('now', '-1 day') WHERE id=1")

    conn.commit()
    conn.close()
    print(f"Database initialized at {target_path}")

if __name__ == "__main__":
    init_db()
