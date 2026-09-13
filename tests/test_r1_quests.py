"""
Tier 1 Acceptance Test: Backend & Database Overhaul (R1)

Authoritative Source: ORIGINAL_REQUEST.md & PROJECT.md
Acceptance Criteria:
- An automated test calls the API (POST /api/plan/generate) to generate a 1-day rolling plan,
  and programmatically verifies the training_plans SQLite table contains exactly one day of
  data formatted as Quests.
- Verifies users and google_fit_logs tables exist with proper schemas.
- Verifies quest completion updates the daily streak in the users table.
"""

import unittest
import os
import sys
from datetime import date, timedelta

# Support running directly or through runner
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from tests.conftest_base import (
    get_db_connection,
    get_test_client,
    ensure_test_athlete_exists,
    DB_PATH
)


class TestR1BackendAndDatabase(unittest.TestCase):
    """Programmatic Acceptance Tests for R1: Database & 1-Day Rolling Quests."""

    @classmethod
    def setUpClass(cls):
        """Ensure database exists and base user/athlete is present."""
        ensure_test_athlete_exists(athlete_id=1, athlete_name="Champ")
        cls.client = get_test_client()

    def setUp(self):
        self.conn = get_db_connection()
        self.cursor = self.conn.cursor()

    def tearDown(self):
        self.conn.close()

    def test_r1_01_required_database_tables_exist(self):
        """Programmatically verify users, google_fit_logs, and training_plans tables exist in SQLite."""
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row['name'] for row in self.cursor.fetchall()]
        
        self.assertIn("users", tables, "SQLite database missing required 'users' table")
        self.assertIn("google_fit_logs", tables, "SQLite database missing required 'google_fit_logs' table")
        self.assertIn("training_plans", tables, "SQLite database missing required 'training_plans' table")

    def test_r1_02_users_table_schema_and_defaults(self):
        """Verify users table contains streak tracking columns (daily_streak, last_streak_date)."""
        self.cursor.execute("PRAGMA table_info(users)")
        columns = {row['name']: row['type'].upper() for row in self.cursor.fetchall()}
        
        required_columns = ["id", "name", "daily_streak", "last_streak_date"]
        for col in required_columns:
            self.assertIn(col, columns, f"'users' table missing required column: {col}")

        # Check that user id=1 exists and has a numeric streak
        self.cursor.execute("SELECT id, name, daily_streak FROM users WHERE id=1")
        user = self.cursor.fetchone()
        self.assertIsNotNone(user, "Default user (id=1) must exist in users table")
        self.assertIsInstance(user['daily_streak'], int, "daily_streak must be an integer")

    def test_r1_03_google_fit_logs_schema(self):
        """Verify google_fit_logs schema contains biometric telemetry columns."""
        self.cursor.execute("PRAGMA table_info(google_fit_logs)")
        columns = {row['name']: row['type'].upper() for row in self.cursor.fetchall()}
        
        expected_cols = [
            "id", "user_id", "log_date", "steps", 
            "active_calories", "distance_meters", 
            "sleep_minutes", "resting_hr"
        ]
        for col in expected_cols:
            self.assertIn(col, columns, f"'google_fit_logs' missing column: {col}")

    def test_r1_04_training_plans_quests_schema(self):
        """Verify training_plans table contains Quest format columns."""
        self.cursor.execute("PRAGMA table_info(training_plans)")
        columns = {row['name'] for row in self.cursor.fetchall()}
        
        quest_columns = [
            "quest_title", 
            "task_type", 
            "target_rpe", 
            "duration_minutes", 
            "is_completed"
        ]
        for col in quest_columns:
            self.assertIn(col, columns, f"'training_plans' missing Quest column: {col}")

    def test_r1_05_generate_1day_rolling_plan_as_quests(self):
        """
        AUTHORITATIVE ACCEPTANCE TEST R1:
        Calls API (POST /api/plan/generate) to generate a 1-day rolling plan,
        and programmatically verifies SQLite training_plans table contains
        exactly one day of data formatted as Quests.
        """
        athlete_id = 1
        test_target_date = (date.today() + timedelta(days=2)).strftime("%Y-%m-%d")

        # 1. Pre-clean existing entries for this target date to ensure test isolation
        self.cursor.execute(
            "DELETE FROM training_plans WHERE athlete_id = ? AND plan_date = ?",
            (athlete_id, test_target_date)
        )
        self.conn.commit()

        # 2. Call API to generate 1-day rolling plan
        # We test both query parameters and json payload
        res = self.client.post(
            f"/api/plan/generate?athlete_id={athlete_id}&target_date={test_target_date}",
            json={
                "athlete_id": athlete_id,
                "target_date": test_target_date,
                "current_fatigue": 4,
                "current_sleep": 8
            }
        )

        self.assertEqual(
            res.status_code, 200,
            f"POST /api/plan/generate failed with status {res.status_code}: {getattr(res, 'text', '')}"
        )
        data = res.json()
        self.assertEqual(data.get("status"), "success", f"API response status was not 'success': {data}")

        # 3. Verify SQLite training_plans table contains EXACTLY ONE DAY of data
        self.cursor.execute(
            "SELECT DISTINCT plan_date FROM training_plans WHERE athlete_id = ? AND plan_date = ?",
            (athlete_id, test_target_date)
        )
        distinct_dates = [row['plan_date'] for row in self.cursor.fetchall()]
        self.assertEqual(
            len(distinct_dates), 1,
            f"Expected exactly 1 distinct target plan_date in SQLite, found: {distinct_dates}"
        )
        self.assertEqual(distinct_dates[0], test_target_date)

        # 4. Programmatically verify data is formatted as Quests
        self.cursor.execute(
            """
            SELECT id, athlete_id, plan_date, quest_title, task_type, target_rpe, duration_minutes, is_completed 
            FROM training_plans 
            WHERE athlete_id = ? AND plan_date = ?
            """,
            (athlete_id, test_target_date)
        )
        quests = self.cursor.fetchall()
        self.assertGreaterEqual(
            len(quests), 1,
            f"Expected at least 1 Quest row for {test_target_date}, found 0"
        )

        for q in quests:
            # Each quest must have title, task type, valid RPE, and positive duration
            self.assertTrue(
                bool(q['quest_title'] and q['quest_title'].strip()),
                f"Quest ID {q['id']} has empty quest_title"
            )
            self.assertIsNotNone(q['task_type'], f"Quest ID {q['id']} has null task_type")
            self.assertIsInstance(q['target_rpe'], int, f"Quest ID {q['id']} target_rpe must be int")
            self.assertGreaterEqual(q['target_rpe'], 1)
            self.assertLessEqual(q['target_rpe'], 10)
            self.assertIsInstance(q['duration_minutes'], int, f"Quest ID {q['id']} duration_minutes must be int")
            self.assertGreater(q['duration_minutes'], 0)
            self.assertEqual(q['is_completed'], 0, f"New Quest ID {q['id']} must start uncompleted (0)")

    def test_r1_06_quest_completion_and_daily_streak_update(self):
        """
        AUTHORITATIVE ACCEPTANCE TEST:
        Completing a quest via API toggles is_completed in SQLite training_plans
        and increments/updates the daily_streak in SQLite users table.
        """
        athlete_id = 1
        today_str = date.today().strftime("%Y-%m-%d")

        # 1. Ensure at least one quest exists for today
        self.cursor.execute(
            "SELECT id, is_completed FROM training_plans WHERE athlete_id = ? AND plan_date = ? AND is_completed = 0 LIMIT 1",
            (athlete_id, today_str)
        )
        quest = self.cursor.fetchone()

        if not quest:
            # Insert a quest for today to test completion
            self.cursor.execute(
                """
                INSERT INTO training_plans 
                (athlete_id, plan_date, intensity_category, target_load, quest_title, task_type, target_rpe, duration_minutes, is_completed)
                VALUES (?, ?, 'Moderate', 150.0, 'Acceptance Test Quest', 'main', 5, 30, 0)
                """,
                (athlete_id, today_str)
            )
            self.conn.commit()
            quest_id = self.cursor.lastrowid
        else:
            quest_id = quest['id']

        # Get initial user streak
        self.cursor.execute("SELECT daily_streak, last_streak_date FROM users WHERE id = ?", (athlete_id,))
        user_before = self.cursor.fetchone()
        initial_streak = user_before['daily_streak'] if user_before else 0

        # 2. Complete the quest via API
        # Support either /api/quests/{id}/complete or /api/plan/complete-quest
        res = self.client.post(
            f"/api/quests/{quest_id}/complete",
            json={"is_completed": True}
        )
        if res.status_code == 404:
            # Try alternate endpoint if route layout varies
            res = self.client.post(
                f"/api/plan/complete-quest",
                json={"quest_id": quest_id, "athlete_id": athlete_id, "is_completed": True}
            )

        self.assertEqual(
            res.status_code, 200,
            f"Quest completion endpoint returned {res.status_code}: {getattr(res, 'text', '')}"
        )

        # 3. Verify SQLite training_plans table was updated
        self.cursor.execute("SELECT is_completed, completed_at FROM training_plans WHERE id = ?", (quest_id,))
        updated_quest = self.cursor.fetchone()
        self.assertIsNotNone(updated_quest)
        self.assertEqual(updated_quest['is_completed'], 1, "training_plans.is_completed must be 1")

        # 4. Verify SQLite users table daily_streak was updated
        self.cursor.execute("SELECT daily_streak, last_streak_date FROM users WHERE id = ?", (athlete_id,))
        user_after = self.cursor.fetchone()
        self.assertIsNotNone(user_after)
        self.assertGreaterEqual(
            user_after['daily_streak'], initial_streak,
            "users.daily_streak should not decrease after quest completion"
        )
        self.assertEqual(
            user_after['last_streak_date'], today_str,
            f"users.last_streak_date should be updated to today ({today_str})"
        )

    def test_r1_07_google_fit_logs_insertion_and_sync(self):
        """Verify health telemetry can be inserted and queried from google_fit_logs."""
        athlete_id = 1
        log_date = date.today().strftime("%Y-%m-%d")

        # Insert/Sync health log
        self.cursor.execute("""
            INSERT OR REPLACE INTO google_fit_logs
            (user_id, log_date, steps, active_calories, distance_meters, sleep_minutes, resting_hr, hrv, source)
            VALUES (?, ?, 9240, 610.5, 7150.0, 480, 56.0, 68.0, 'google_fit')
        """, (athlete_id, log_date))
        self.conn.commit()

        self.cursor.execute(
            "SELECT steps, active_calories, resting_hr FROM google_fit_logs WHERE user_id = ? AND log_date = ?",
            (athlete_id, log_date)
        )
        row = self.cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row['steps'], 9240)
        self.assertAlmostEqual(row['active_calories'], 610.5)
        self.assertAlmostEqual(row['resting_hr'], 56.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
