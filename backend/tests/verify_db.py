import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "athlete_planner.db")

def verify():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    print("Tables in DB:", tables)
    assert "users" in tables, "users table missing"
    assert "google_fit_logs" in tables, "google_fit_logs table missing"
    assert "training_plans" in tables, "training_plans table missing"
    assert "athletes" in tables, "athletes table missing"
    
    users = c.execute("SELECT * FROM users").fetchall()
    print("Users rows:", users)
    assert len(users) >= 1, "users table is empty"
    
    # Verify training_plans schema
    plan_cols = [col[1] for col in c.execute("PRAGMA table_info(training_plans)").fetchall()]
    print("training_plans cols:", plan_cols)
    for col in ['quest_title', 'session_description', 'task_type', 'target_rpe', 'duration_minutes', 'is_completed', 'completed_at']:
        assert col in plan_cols, f"Column {col} missing in training_plans"
        
    # Verify google_fit_logs schema
    fit_cols = [col[1] for col in c.execute("PRAGMA table_info(google_fit_logs)").fetchall()]
    print("google_fit_logs cols:", fit_cols)
    for col in ['user_id', 'log_date', 'steps', 'heart_rate_avg', 'heart_rate_resting', 'sleep_hours', 'calories_burned', 'synced_at']:
        assert col in fit_cols, f"Column {col} missing in google_fit_logs"
        
    # Verify users schema
    user_cols = [col[1] for col in c.execute("PRAGMA table_info(users)").fetchall()]
    print("users cols:", user_cols)
    for col in ['id', 'name', 'email', 'current_streak', 'last_active_date', 'created_at']:
        assert col in user_cols, f"Column {col} missing in users"
        
    print("ALL DB SCHEMAS AND SEEDS VERIFIED SUCCESSFULLY!")

if __name__ == "__main__":
    verify()
