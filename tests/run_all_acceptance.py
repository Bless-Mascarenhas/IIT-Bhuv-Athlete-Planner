"""
Master Acceptance Test Runner for Pace Athlete Performance Planner.

Executes all Tier 1 through Tier 4 acceptance test suites:
  - Tier 1 (R1): Backend & Database Overhaul (1-day Quests, users, google_fit_logs, streaks)
  - Tier 2 (R2): AI Intent Router (POST /api/chat, "I have a match tomorrow", autonomous events)
  - Tier 3 (R3): Mobile SPA Frontend (5-tab navigation, Header streak, Strava-style footer)
  - Tier 4 (R4): Health Data Architecture (Capacitor health mock fallback without web crashes)

Usage:
  python tests/run_all_acceptance.py
"""

import sys
import os
import unittest
import time

# Ensure repo root and backend are in sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(REPO_ROOT, "backend")

if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Set fallback GROQ_API_KEY for offline/test environments
os.environ.setdefault("GROQ_API_KEY", "gsk_test_fixture_pace_mock_key")

from tests.test_r1_quests import TestR1BackendAndDatabase
from tests.test_r2_intent import TestR2AIIntentRouter
from tests.test_r3_frontend import TestR3MobileFrontend
from tests.test_r4_health import TestR4HealthDataArchitecture


def run_acceptance_suite():
    print("=" * 78)
    print("PACE AUTONOMOUS ATHLETE PLANNER - ACCEPTANCE TEST SUITE RUNNER")
    print("=" * 78)
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
    print(f"Workspace: {REPO_ROOT}")
    print("=" * 78)

    suite = unittest.TestSuite()
    loader = unittest.TestLoader()

    tiers = [
        ("Tier 1: Backend & 1-Day Quests (R1)", TestR1BackendAndDatabase),
        ("Tier 2: AI Intent Router & Autonomous DB (R2)", TestR2AIIntentRouter),
        ("Tier 3: Mobile SPA Frontend Shell (R3)", TestR3MobileFrontend),
        ("Tier 4: Health Data Architecture & Mock Fallback (R4)", TestR4HealthDataArchitecture),
    ]

    for tier_name, test_class in tiers:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    runner = unittest.TextTestRunner(verbosity=2)
    start_time = time.time()
    result = runner.run(suite)
    duration = time.time() - start_time

    print("\n" + "=" * 78)
    print("ACCEPTANCE VERIFICATION SUMMARY REPORT")
    print("=" * 78)
    print(f"Tests Run:    {result.testsRun}")
    print(f"Passed:       {result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped)}")
    print(f"Failures:     {len(result.failures)}")
    print(f"Errors:       {len(result.errors)}")
    print(f"Skipped:      {len(result.skipped)}")
    print(f"Elapsed Time: {duration:.2f}s")
    print("=" * 78)

    if result.wasSuccessful():
        print("RESULT: ALL ACCEPTANCE CRITERIA SATISFIED! (READY FOR RELEASE)")
        return 0
    else:
        print("RESULT: ACCEPTANCE GAPS IDENTIFIED - SEE DIAGNOSTICS ABOVE")
        if result.failures:
            print("\nFAILURES:")
            for test, traceback in result.failures:
                print(f"  - {test.id()}:")
                # Print last line of failure traceback
                lines = traceback.strip().split("\n")
                print(f"    {lines[-1]}")
        if result.errors:
            print("\nERRORS (Implementation not yet wired or broken):")
            for test, traceback in result.errors:
                print(f"  - {test.id()}:")
                lines = traceback.strip().split("\n")
                print(f"    {lines[-1]}")
        return 1


if __name__ == "__main__":
    sys.exit(run_acceptance_suite())
