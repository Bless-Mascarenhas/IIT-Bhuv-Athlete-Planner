import os
import sys
import sqlite3
from datetime import date, timedelta

WORKSPACE_DIR = r"d:\IIT-Bhuv"
BACKEND_DIR = os.path.join(WORKSPACE_DIR, "backend")
FRONTEND_DIR = os.path.join(WORKSPACE_DIR, "mobile")
DB_PATH = os.path.join(BACKEND_DIR, "athlete_planner.db")
sys.path.insert(0, BACKEND_DIR)

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_ac1():
    print("=== [AC1] 1-Day Rolling Quests Generator & SQLite Training Plans ===")
    test_target_date = (date.today() + timedelta(days=5)).strftime("%Y-%m-%d")
    athlete_id = 1

    # Pre-clean
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("DELETE FROM training_plans WHERE athlete_id = ? AND plan_date = ?", (athlete_id, test_target_date))
    conn.commit()

    # Call API to generate 1-day rolling plan
    res = client.post(
        f"/api/plan/generate?athlete_id={athlete_id}&target_date={test_target_date}",
        json={
            "athlete_id": athlete_id,
            "target_date": test_target_date,
            "current_fatigue": 2,
            "current_sleep": 8
        }
    )
    print(f"API Response Code: {res.status_code}")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    res_data = res.json()
    quests_in_api = res_data.get("quests", [])
    print(f"API Status: {res_data.get('status')}, Quests Count: {len(quests_in_api)}")
    assert len(quests_in_api) >= 1, "Expected at least 1 quest returned"

    # Verify SQLite database
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
    print(f"DB Quests Found in training_plans: {len(quests)}")
    for q in quests:
        print(f"  Quest #{q['id']}: title='{q['quest_title']}', task_type='{q['task_type']}', RPE={q['target_rpe']}, duration={q['duration_minutes']}m, completed={q['is_completed']}")
        assert q['quest_title'], "Empty quest_title"
        assert q['task_type'], "Null task_type"
        assert 1 <= q['target_rpe'] <= 10, f"Invalid RPE {q['target_rpe']}"
        assert q['duration_minutes'] > 0, f"Invalid duration {q['duration_minutes']}"
        assert q['is_completed'] in (0, 1), f"Invalid is_completed {q['is_completed']}"

    # Also test completing a quest advances daily streak
    quest_to_complete = quests[0]
    complete_res = client.post(
        f"/api/quests/{quest_to_complete['id']}/complete",
        json={"is_completed": True}
    )
    assert complete_res.status_code == 200, f"Expected 200, got {complete_res.status_code}"
    complete_data = complete_res.json()
    print(f"Complete quest response: {complete_data}")
    assert complete_data.get("daily_streak") is not None, "Missing daily_streak"

    cursor.execute("SELECT is_completed FROM training_plans WHERE id = ?", (quest_to_complete['id'],))
    updated_quest = cursor.fetchone()
    assert updated_quest['is_completed'] == 1, "Quest was not marked as completed in SQLite"
    print("Quest completion verified in SQLite.")

    conn.close()
    print("[AC1] RESULT: PASS\n")


def test_ac2():
    print("=== [AC2] AI Intent Router ('I have a match tomorrow') & SQLite Events Update ===")
    athlete_id = 1
    tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")

    # Clean prior match for tomorrow to ensure fresh verification
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
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    res_data = res.json()
    print(f"Chat Response: {res_data}")
    assert "calendar" in res_data.get("intent", "").lower(), f"Expected calendar intent, got {res_data.get('intent')}"
    assert res_data.get("action_taken") == "calendar_updated", f"Expected action calendar_updated, got {res_data.get('action_taken')}"

    # Programmatically verify SQLite events table
    cursor.execute(
        "SELECT id, athlete_id, event_date, event_type, duration_minutes FROM events WHERE athlete_id = ? AND event_date = ? AND event_type = 'match'",
        (athlete_id, tomorrow)
    )
    row = cursor.fetchone()
    print(f"SQLite Event row: {row}")
    assert row is not None, f"Event not found in SQLite events table for {tomorrow}"
    print(f"Found event id={row[0]}, athlete_id={row[1]}, date={row[2]}, type={row[3]}, duration={row[4]}")
    assert row[2] == tomorrow, f"Expected date {tomorrow}, got {row[2]}"
    assert row[3] == "match", f"Expected type 'match', got {row[3]}"
    conn.close()
    print("[AC2] RESULT: PASS\n")


def test_ac3_frontend_facade_and_authenticity():
    print("=== [AC3] Frontend 5 Pages Authenticity & Non-Facade Verification ===")
    pages_dir = os.path.join(FRONTEND_DIR, "src", "pages")
    required_pages = ["Dashboard.tsx", "Planner.tsx", "Chat.tsx", "Calendar.tsx", "Settings.tsx"]

    for page in required_pages:
        page_path = os.path.join(pages_dir, page)
        assert os.path.exists(page_path), f"Page {page} missing!"
        with open(page_path, "r", encoding="utf-8") as f:
            content = f.read()
            lines = content.splitlines()

        print(f"Inspecting {page}: {len(lines)} lines, {len(content)} bytes")
        # Ensure it is NOT a stub
        assert len(lines) >= 50, f"{page} is too short ({len(lines)} lines), possible facade!"
        assert "This view will be built out next!" not in content, f"{page} contains stub text!"
        assert "export default function" in content, f"{page} missing default export function!"
        assert "return" in content, f"{page} missing return statement!"

        # Check page-specific genuine logic
        if page == "Dashboard.tsx":
            assert "getHealthProvider" in content or "useAthlete" in content, "Dashboard missing health provider/context"
            assert "Readiness" in content or "ACWR" in content or "Biometrics" in content, "Dashboard missing athlete telemetry"
        elif page == "Planner.tsx":
            assert "completeQuest" in content or "quests" in content, "Planner missing quest logic"
            assert "streak" in content.lower(), "Planner missing streak incentive"
        elif page == "Chat.tsx":
            assert "sendChatMessage" in content or "api.sendChatMessage" in content or "POST" in content, "Chat missing chat API connection"
            assert "QUICK_PROMPTS" in content or "prompts" in content.lower(), "Chat missing quick prompts"
        elif page == "Calendar.tsx":
            assert "api.getEvents" in content or "getEvents" in content, "Calendar missing events API connection"
            assert "handleAddEvent" in content or "addEvent" in content, "Calendar missing add event functionality"
        elif page == "Settings.tsx":
            assert "healthProviderName" in content or "Health Data Architecture" in content, "Settings missing health architecture inspector"

    print("All 5 pages verified as genuine, non-facade implementations.")
    print("[AC3] RESULT: PASS\n")


def test_ac4_health_architecture_and_build():
    print("=== [AC4] Health Data Architecture & Web Fallback Verification ===")
    health_dir = os.path.join(FRONTEND_DIR, "src", "services", "health")
    assert os.path.exists(os.path.join(health_dir, "HealthProviderFactory.ts")), "HealthProviderFactory.ts missing"
    assert os.path.exists(os.path.join(health_dir, "MockHealthProvider.ts")), "MockHealthProvider.ts missing"
    assert os.path.exists(os.path.join(health_dir, "NativeHealthProvider.ts")), "NativeHealthProvider.ts missing"

    with open(os.path.join(health_dir, "HealthProviderFactory.ts"), "r", encoding="utf-8") as f:
        factory_content = f.read()
    assert "MockHealthProvider" in factory_content, "Factory does not import MockHealthProvider"
    assert "Capacitor.isNativePlatform" in factory_content, "Factory does not check native platform"

    with open(os.path.join(health_dir, "MockHealthProvider.ts"), "r", encoding="utf-8") as f:
        mock_content = f.read()
    assert "getTodayMetrics" in mock_content, "Mock provider missing getTodayMetrics"
    assert "steps" in mock_content and "restingHeartRate" in mock_content and "caloriesBurned" in mock_content, "Mock provider missing biometrics"

    # Verify build artifacts in mobile/dist
    dist_index = os.path.join(FRONTEND_DIR, "dist", "index.html")
    assert os.path.exists(dist_index), "dist/index.html missing, build artifact not found!"
    print("Verified dist/index.html exists.")

    print("[AC4] RESULT: PASS\n")

if __name__ == "__main__":
    test_ac1()
    test_ac2()
    test_ac3_frontend_facade_and_authenticity()
    test_ac4_health_architecture_and_build()
    print("ALL INDEPENDENT VERIFICATION TESTS PASSED SUCCESSFULLY!")
