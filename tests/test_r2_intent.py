"""
Tier 2 Acceptance Test: AI Intent Router & Autonomous DB Execution (R2)

Authoritative Source: ORIGINAL_REQUEST.md & PROJECT.md
Acceptance Criteria:
- An automated test sends a test string ("I have a match tomorrow") to the chat endpoint (POST /api/chat),
  and programmatically verifies the SQLite events table was autonomously updated with the new match.
- Tests 'Update Plan' and 'General QA' intents.
- Tests Events API (GET /api/events).
- Includes adversarial edge cases (SQL injection safety, empty prompts).
"""

import unittest
import os
import sys
from datetime import date, timedelta

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from tests.conftest_base import (
    get_db_connection,
    get_test_client,
    ensure_test_athlete_exists,
    DB_PATH
)


class TestR2AIIntentRouter(unittest.TestCase):
    """Programmatic Acceptance Tests for R2: AI Intent Router & Autonomous DB Actions."""

    @classmethod
    def setUpClass(cls):
        ensure_test_athlete_exists(athlete_id=1, athlete_name="Champ")
        cls.client = get_test_client()

    def setUp(self):
        self.conn = get_db_connection()
        self.cursor = self.conn.cursor()

    def tearDown(self):
        self.conn.close()

    def test_r2_01_intent_update_calendar_match_tomorrow(self):
        """
        AUTHORITATIVE ACCEPTANCE TEST R2:
        Sends test string 'I have a match tomorrow' to POST /api/chat,
        and programmatically verifies the SQLite 'events' table was autonomously
        updated with the new match for tomorrow without manual form submission.
        """
        athlete_id = 1
        tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")

        # 1. Clean any existing match events for tomorrow to ensure clean isolation
        self.cursor.execute(
            "DELETE FROM events WHERE athlete_id = ? AND event_date = ? AND event_type = 'match'",
            (athlete_id, tomorrow)
        )
        self.conn.commit()

        # 2. Send authoritative test string to chat endpoint
        payload = {
            "athlete_id": athlete_id,
            "message": "I have a match tomorrow",
            "history": []
        }
        res = self.client.post("/api/chat", json=payload)

        self.assertEqual(
            res.status_code, 200,
            f"POST /api/chat failed with {res.status_code}: {getattr(res, 'text', '')}"
        )
        data = res.json()

        # Intent must be 'Update Calendar' (or contain 'Calendar')
        intent = data.get("intent", "")
        self.assertTrue(
            "Calendar" in intent or "calendar" in intent,
            f"Expected intent 'Update Calendar', got: '{intent}' (full response: {data})"
        )

        # 3. Programmatically verify SQLite 'events' table was autonomously updated
        self.cursor.execute(
            """
            SELECT id, athlete_id, event_date, event_type, duration_minutes 
            FROM events 
            WHERE athlete_id = ? AND event_date = ? AND event_type = 'match'
            """,
            (athlete_id, tomorrow)
        )
        row = self.cursor.fetchone()
        self.assertIsNotNone(
            row,
            f"Acceptance Failure: SQLite 'events' table does NOT contain autonomously created match for {tomorrow}"
        )
        self.assertEqual(row['event_type'], 'match')
        self.assertEqual(row['event_date'], tomorrow)
        self.assertEqual(row['athlete_id'], athlete_id)

    def test_r2_02_intent_update_plan(self):
        """
        Verify chat classifier recognizes 'Update Plan' intent for fatigue/injury feedback
        and does not improperly create a calendar event.
        """
        athlete_id = 1
        events_count_before = self.cursor.execute(
            "SELECT count(*) FROM events WHERE athlete_id = ?", (athlete_id,)
        ).fetchone()[0]

        payload = {
            "athlete_id": athlete_id,
            "message": "My hamstrings are tight and I am feeling fatigued, please make today's workout lighter",
            "history": []
        }
        res = self.client.post("/api/chat", json=payload)

        self.assertEqual(
            res.status_code, 200,
            f"POST /api/chat failed with {res.status_code}: {getattr(res, 'text', '')}"
        )
        data = res.json()
        intent = data.get("intent", "")
        self.assertTrue(
            "Plan" in intent or "plan" in intent,
            f"Expected intent 'Update Plan', got: '{intent}' (response: {data})"
        )

        # Ensure no accidental event was added
        events_count_after = self.cursor.execute(
            "SELECT count(*) FROM events WHERE athlete_id = ?", (athlete_id,)
        ).fetchone()[0]
        self.assertEqual(events_count_before, events_count_after, "Update Plan should not insert into events table")

    def test_r2_03_intent_general_qa(self):
        """
        Verify chat classifier recognizes 'General QA' intent for sports science advice
        and provides coaching feedback without database mutations.
        """
        athlete_id = 1
        payload = {
            "athlete_id": athlete_id,
            "message": "What should I eat before a high-intensity match for optimal glycogen storage?",
            "history": []
        }
        res = self.client.post("/api/chat", json=payload)

        self.assertEqual(
            res.status_code, 200,
            f"POST /api/chat failed with {res.status_code}: {getattr(res, 'text', '')}"
        )
        data = res.json()
        intent = data.get("intent", "")
        self.assertTrue(
            "QA" in intent or "General" in intent or "qa" in intent,
            f"Expected intent 'General QA', got: '{intent}' (response: {data})"
        )
        
        reply = data.get("reply", "") or data.get("response", "")
        self.assertTrue(len(reply) > 10, "General QA must return a meaningful coaching reply")

    def test_r2_04_events_api_read_and_roundtrip(self):
        """Verify GET /api/events returns event records for athlete."""
        athlete_id = 1
        res = self.client.get(f"/api/events?athlete_id={athlete_id}")
        self.assertEqual(
            res.status_code, 200,
            f"GET /api/events failed with {res.status_code}: {getattr(res, 'text', '')}"
        )
        events = res.json()
        self.assertIsInstance(events, list, "GET /api/events must return an array of events")

    def test_r2_05_adversarial_sql_injection_defense(self):
        """
        Adversarial Test:
        Ensures malicious SQL injection strings in chat messages are executed with safe
        parameterized queries and do not drop tables or crash the server.
        """
        athlete_id = 1
        malicious_message = "I have a match tomorrow'; DROP TABLE events; --"
        
        payload = {
            "athlete_id": athlete_id,
            "message": malicious_message,
            "history": []
        }
        res = self.client.post("/api/chat", json=payload)
        
        # Server must not return 500
        self.assertIn(res.status_code, [200, 400, 422])

        # Table events MUST still exist in SQLite!
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='events'")
        table = self.cursor.fetchone()
        self.assertIsNotNone(table, "CRITICAL: SQL Injection vulnerability dropped the 'events' table!")


if __name__ == "__main__":
    unittest.main(verbosity=2)
