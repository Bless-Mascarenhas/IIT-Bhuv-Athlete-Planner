import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "athlete_planner.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Athletes Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS athletes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        sport_type TEXT DEFAULT 'team_sport',
        baseline_fatigue REAL DEFAULT 5.0,
        baseline_sleep REAL DEFAULT 7.0
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
    # Scales: RPE (1-10), Sleep (1-10, 10=best), Fatigue & Soreness (1-10, 10=worst)
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

    # Training Plans (Generated & revised by the AI)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS training_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        athlete_id INTEGER,
        plan_date DATE NOT NULL,
        intensity_category TEXT NOT NULL, -- 'Rest', 'Recovery', 'Moderate', 'High'
        target_load REAL,
        status TEXT DEFAULT 'planned', -- 'planned', 'completed', 'revised'
        revision_reason TEXT, -- Stores agent's reasoning if changed based on constraints
        FOREIGN KEY(athlete_id) REFERENCES athletes(id)
    )
    ''')

    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")

if __name__ == "__main__":
    init_db()
