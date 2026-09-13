"""
Common Test Fixtures, Harness Configuration, and Database Utilities
for the Pace Acceptance Test Suite.
"""

import os
import sys
import sqlite3
from typing import Optional, Dict, Any

# Ensure backend directory is in python path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(REPO_ROOT, "backend")
MOBILE_DIR = os.path.join(REPO_ROOT, "mobile")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Ensure a mock GROQ_API_KEY exists to allow top-level module import if unset
if "GROQ_API_KEY" not in os.environ:
    os.environ["GROQ_API_KEY"] = "gsk_test_fixture_pace_mock_key"

DB_PATH = os.path.join(BACKEND_DIR, "athlete_planner.db")


def get_db_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Returns an active SQLite connection with row factory enabled."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


class PaceTestClientWrapper:
    """
    Unified client supporting both FastAPI in-process TestClient and live HTTP requests.
    Enables testing without requiring external port listeners or background daemons.
    """

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.environ.get("PACE_API_URL")
        self._test_client = None
        
        if not self.base_url:
            # Use FastAPI TestClient directly
            try:
                from fastapi.testclient import TestClient
                import main
                self._test_client = TestClient(main.app)
            except Exception as e:
                # If FastAPI TestClient fails to load, fallback to default URL
                self._init_error = e
                self.base_url = "http://localhost:8000"

    def get(self, path: str, params: Optional[Dict[str, Any]] = None):
        if self._test_client:
            return self._test_client.get(path, params=params)
        import requests
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        return requests.get(url, params=params, timeout=5)

    def post(self, path: str, json: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None):
        if self._test_client:
            return self._test_client.post(path, json=json, params=params)
        import requests
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        return requests.post(url, json=json, params=params, timeout=5)

    def delete(self, path: str, params: Optional[Dict[str, Any]] = None):
        if self._test_client:
            return self._test_client.delete(path, params=params)
        import requests
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        return requests.delete(url, params=params, timeout=5)


def get_test_client() -> PaceTestClientWrapper:
    """Returns the configured Pace test client."""
    return PaceTestClientWrapper()


def ensure_test_athlete_exists(athlete_id: int = 1, athlete_name: str = "Test Athlete") -> None:
    """Ensures at least one athlete/user exists in SQLite for tests."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if users table exists and seed
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if cursor.fetchone():
        cursor.execute("SELECT id FROM users WHERE id = ?", (athlete_id,))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT OR IGNORE INTO users (id, name, sport_type, daily_streak, last_streak_date)
                VALUES (?, ?, 'Soccer', 12, DATE('now', '-1 day'))
            """, (athlete_id, athlete_name))
            conn.commit()

    # Check if athletes table exists and seed
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='athletes'")
    if cursor.fetchone():
        cursor.execute("SELECT id FROM athletes WHERE id = ?", (athlete_id,))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT OR IGNORE INTO athletes (id, name, sport_type)
                VALUES (?, ?, 'Soccer')
            """, (athlete_id, athlete_name))
            conn.commit()

    conn.close()
