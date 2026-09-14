import os
import psycopg2
from psycopg2.extras import RealDictCursor

# The URL from the user
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:[YOUR-PASSWORD]@db.jgfztxjzgjuvedhiqdjm.supabase.co:5432/postgres")

def get_db_connection():
    """Returns a PostgreSQL connection with RealDictCursor for dict-like access."""
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
    except Exception as e:
        print(f"Warning: Failed to connect to database on startup. {e}")
        return

    try:
        cursor.execute("ALTER TABLE events ADD COLUMN is_deleted BOOLEAN DEFAULT false")
    except Exception:
        conn.rollback()

    # Athletes Table (preserved for backward compatibility)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS athletes (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        sport_type TEXT DEFAULT 'team_sport',
        baseline_fatigue REAL DEFAULT 5.0,
        baseline_sleep REAL DEFAULT 7.0
    )
    ''')

    # Seed default athlete if empty
    cursor.execute("SELECT count(*) FROM athletes")
    if cursor.fetchone()['count'] == 0:
        cursor.execute('''
            INSERT INTO athletes (id, name, sport_type, baseline_fatigue, baseline_sleep)
            VALUES (1, 'Champ', 'team_sport', 5.0, 7.0)
            ON CONFLICT (id) DO NOTHING
        ''')

    # Users Table for athlete profile and streak tracking
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT,
        current_streak INTEGER DEFAULT 0,
        daily_streak INTEGER DEFAULT 0,
        sport_type TEXT DEFAULT 'Soccer',
        position TEXT DEFAULT '',
        password_hash TEXT,
        is_guest BOOLEAN DEFAULT false,
        active_goal TEXT DEFAULT 'Stay Fit',
        goal_end_date DATE,
        last_active_date DATE,
        last_streak_date DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Events / Match Calendar Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS events (
        id SERIAL PRIMARY KEY,
        athlete_id INTEGER,
        event_date DATE NOT NULL,
        event_type TEXT NOT NULL,
        duration_minutes INTEGER,
        is_deleted BOOLEAN DEFAULT false,
        FOREIGN KEY(athlete_id) REFERENCES athletes(id) ON DELETE CASCADE
    )
    ''')

    # Daily Logs
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS daily_logs (
        id SERIAL PRIMARY KEY,
        athlete_id INTEGER,
        log_date DATE NOT NULL,
        rpe INTEGER, 
        duration_minutes INTEGER,
        sleep_quality INTEGER, 
        fatigue INTEGER, 
        soreness INTEGER,
        acute_workload REAL,
        FOREIGN KEY(athlete_id) REFERENCES athletes(id) ON DELETE CASCADE
    )
    ''')

    # Google Fit Telemetry Logs Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS google_fit_logs (
        id SERIAL PRIMARY KEY,
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
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    ''')

    # Training Plans
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS training_plans (
        id SERIAL PRIMARY KEY,
        athlete_id INTEGER,
        plan_date DATE NOT NULL,
        intensity_category TEXT NOT NULL DEFAULT 'Moderate',
        target_load REAL DEFAULT 0.0,
        status TEXT DEFAULT 'planned',
        revision_reason TEXT DEFAULT '',
        quest_title TEXT DEFAULT '',
        session_description TEXT DEFAULT '',
        task_type TEXT DEFAULT 'workout',
        target_rpe INTEGER DEFAULT 5,
        duration_minutes INTEGER DEFAULT 30,
        target_steps INTEGER DEFAULT 10000,
        target_calories INTEGER DEFAULT 2500,
        is_completed BOOLEAN DEFAULT false,
        completed_at TIMESTAMP,
        FOREIGN KEY(athlete_id) REFERENCES athletes(id) ON DELETE CASCADE
    )
    ''')

    # Seed default user (id=1, name='Champ', daily_streak=0) if empty
    cursor.execute("SELECT count(*) FROM users")
    if cursor.fetchone()['count'] == 0:
        cursor.execute('''
            INSERT INTO users (id, name, email, current_streak, daily_streak, sport_type, last_active_date, last_streak_date)
            VALUES (1, 'Champ', 'athlete@pace.ai', 0, 0, 'Soccer', CURRENT_DATE - INTERVAL '1 day', CURRENT_DATE - INTERVAL '1 day')
            ON CONFLICT (id) DO NOTHING
        ''')
    else:
        # Ensure user id=1 exists
        cursor.execute("SELECT id, daily_streak, last_streak_date FROM users WHERE id=1")
        u = cursor.fetchone()
        if not u:
            cursor.execute('''
                INSERT INTO users (id, name, email, current_streak, daily_streak, sport_type, last_active_date, last_streak_date)
                VALUES (1, 'Champ', 'athlete@pace.ai', 0, 0, 'Soccer', CURRENT_DATE - INTERVAL '1 day', CURRENT_DATE - INTERVAL '1 day')
                ON CONFLICT (id) DO NOTHING
            ''')
        else:
            if u['last_streak_date'] is None:
                cursor.execute("UPDATE users SET last_streak_date = CURRENT_DATE - INTERVAL '1 day', last_active_date = CURRENT_DATE - INTERVAL '1 day' WHERE id=1")

    # Dynamic migrations for users table
    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='users'")
    existing_cols = [row['column_name'] for row in cursor.fetchall()]

    user_migrations = {
        'position': 'TEXT DEFAULT \'\'',
        'password_hash': 'TEXT',
        'is_guest': 'BOOLEAN DEFAULT false',
        'athlete_tier': 'TEXT DEFAULT \'Semi-Pro\''
    }

    for col_name, col_def in user_migrations.items():
        if col_name not in existing_cols:
            try:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}")
            except Exception:
                conn.rollback()

    # ── One-time schema migrations ──────────────────────────────────────
    # A migrations table tracks which fixes have already been applied.
    # Each migration runs exactly once, then is recorded and never re-runs.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    def run_once(name: str, sql: str):
        """Execute sql exactly once, guarded by the migrations table."""
        try:
            cursor.execute("SELECT 1 FROM schema_migrations WHERE name = %s", (name,))
            if cursor.fetchone():
                return  # already applied
            cursor.execute(sql)
            cursor.execute("INSERT INTO schema_migrations (name) VALUES (%s)", (name,))
        except Exception:
            conn.rollback()

    # Fix: reset streaks that were incorrectly set to 12 by the old
    # /admin/restore-streaks endpoint. Only touches guest accounts and
    # accounts with no email — registered users with real earned streaks
    # are left untouched.
    run_once(
        "fix_inflated_guest_streaks_v1",
        "UPDATE users SET daily_streak = 0, current_streak = 0 WHERE is_guest = true OR email IS NULL"
    )
    # ───────────────────────────────────────────────────────────────────

    conn.commit()
    conn.close()
    print("PostgreSQL Database initialized at Supabase")

if __name__ == "__main__":
    init_db()
