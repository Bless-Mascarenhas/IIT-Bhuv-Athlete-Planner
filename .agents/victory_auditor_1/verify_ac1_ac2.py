import os
import sys
import sqlite3
from datetime import date, timedelta

BACKEND_DIR = r"d:\IIT-Bhuv\backend"
DB_PATH = os.path.join(BACKEND_DIR, "athlete_planner.db")
sys.path.insert(0, BACKEND_DIR)

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_ac1():
    print("--- TESTING AC1 (Backend & Database R1) ---")
    test_target_date = (date.today() + timedelta(days=3)).strftime("%Y-%m-%d")
    athlete_id = 1

    # Call API to generate 1-day rolling plan
    res = client.post(
        f"/api/plan/generate?athlete_id={athlete_id}&target_date={test_target_date}",
        json={
            "athlete_id": athlete_id,
            "target_date": test_target_date,
            "current_fatigue": 3,
            "current_sleep": 8
        }
    )
    print(f"API Response Code: {res.status_code}")
    res_data = res.json()
    print(f"API Status: {res_data.get('status')}, Quests Count: {len(res_data.get('quests', []))}")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"

    # Verify SQLite database
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        "SELECT DISTINCT plan_date FROM training_plans WHERE athlete_id = ? AND plan_date = ?",
        (athlete_id, test_target_date)
    )
    distinct_dates = [r['plan_date'] for r in cursor.fetchall()]
    print(f"Distinct plan dates in DB for target: {distinct_dates}")
    assert len(distinct_dates) == 1 and distinct_dates[0] == test_target_date, f"Expected exactly 1 date {test_target_date}, got {distinct_dates}"

    cursor.execute(
        "SELECT id, quest_title, task_type, target_rpe, duration_minutes, is_completed FROM training_plans WHERE athlete_id = ? AND plan_date = ?",
        (athlete_id, test_target_date)
    )
    quests = cursor.fetchall()
    print(f"DB Quests Found: {len(quests)}")
    for q in quests:
        print(f"  Quest #{q['id']}: title='{q['quest_title']}', task_type='{q['task_type']}', RPE={q['target_rpe']}, duration={q['duration_minutes']}m, completed={q['is_completed']}")
        assert q['quest_title'], "Empty quest_title"
        assert q['task_type'], "Null task_type"
        assert 1 <= q['target_rpe'] <= 10, f"Invalid RPE {q['target_rpe']}"
        assert q['duration_minutes'] > 0, f"Invalid duration {q['duration_minutes']}"
    conn.close()
    print("AC1 VERIFICATION: PASS\n")

def test_ac2():
    print("--- TESTING AC2 (AI Intent Router R2) ---")
    athlete_id = 1
    tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")

    # Pre-clean match for tomorrow
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM events WHERE athlete_id = ? AND event_date = ? AND event_type = 'match'", (athlete_id, tomorrow))
    conn.commit()

    # Send test string "I have a match tomorrow" to POST /api/chat
    payload = {
        "athlete_id": athlete_id,
        "message": "I have a match tomorrow",
        "history": []
    }
    res = client.post("/api/chat", json=payload)
    print(f"POST /api/chat response code: {res.status_code}")
    res_data = res.json()
    print(f"Chat Response: {res_data}")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    assert "calendar" in res_data.get("intent", "").lower(), f"Expected calendar intent, got {res_data.get('intent')}"

    # Programmatically verify SQLite events table
    cursor.execute(
        "SELECT id, athlete_id, event_date, event_type, duration_minutes FROM events WHERE athlete_id = ? AND event_date = ? AND event_type = 'match'",
        (athlete_id, tomorrow)
    )
    row = cursor.fetchone()
    print(f"SQLite Event row: {row}")
    assert row is not None, f"Event not found in SQLite events table for {tomorrow}"
    print(f"Found event id={row[0]}, date={row[2]}, type={row[3]}, duration={row[4]}")
    conn.close()
    print("AC2 VERIFICATION: PASS\n")

if __name__ == "__main__":
    test_ac1()
    test_ac2()
