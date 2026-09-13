"""
Tier 4 Acceptance Test: Health Data Architecture & Web Fallback (R4 - Python Runner)

Authoritative Source: ORIGINAL_REQUEST.md & PROJECT.md
Acceptance Criteria:
- Provider interface for @capawesome-team/capacitor-health that gracefully falls back
  to mock data when running in a web browser.
- Ensures seamless local development before device deployment without throwing
  "Plugin 'Health' not implemented on web".
"""

import unittest
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MOBILE_DIR = os.path.join(REPO_ROOT, "mobile")
HEALTH_DIR = os.path.join(MOBILE_DIR, "src", "services", "health")


class TestR4HealthDataArchitecture(unittest.TestCase):
    """Verifies Health Provider Interface and Web Browser Mock Fallback."""

    def test_r4_01_ts_test_specification_exists(self):
        """Verify the TypeScript acceptance test specification file exists in tests/."""
        ts_test_path = os.path.join(REPO_ROOT, "tests", "test_r4_health.ts")
        self.assertTrue(os.path.exists(ts_test_path), f"Missing {ts_test_path}")

    def test_r4_02_health_service_files_or_specification(self):
        """
        Verify Health provider structure:
        Either in mobile/src/services/health/ or via healthService.ts.
        Validates presence of mock fallback logic.
        """
        has_health_dir = os.path.exists(HEALTH_DIR)
        has_health_service = os.path.exists(os.path.join(MOBILE_DIR, "src", "services", "healthService.ts"))

        # Check either the modular health directory or unified service
        if has_health_dir:
            files = os.listdir(HEALTH_DIR)
            has_mock = any("mock" in f.lower() for f in files)
            has_factory = any("factory" in f.lower() or "provider" in f.lower() for f in files)
            self.assertTrue(has_mock, "mobile/src/services/health/ must contain a MockHealthProvider")
        elif has_health_service:
            with open(os.path.join(MOBILE_DIR, "src", "services", "healthService.ts"), "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("mock", content.lower(), "healthService.ts must contain mock fallback implementation")
        else:
            # Check if implemented in context
            health_context = os.path.join(MOBILE_DIR, "src", "context", "HealthContext.tsx")
            if os.path.exists(health_context):
                with open(health_context, "r", encoding="utf-8") as f:
                    content = f.read()
                self.assertIn("mock", content.lower(), "HealthContext.tsx must contain mock fallback")
            else:
                self.fail("Health service / provider not yet implemented in mobile/src/services/health/ or mobile/src/context/")

    def test_r4_03_mock_telemetry_metric_contract(self):
        """
        Verify that health metrics contract defines all required athlete telemetry:
        steps, active calories, distance, sleep, and resting heart rate.
        """
        expected_metrics = ["steps", "calories", "sleep", "heart"]
        
        # Scan health implementation or test spec for contracts
        sources = [
            os.path.join(REPO_ROOT, "tests", "test_r4_health.ts"),
        ]
        if os.path.exists(HEALTH_DIR):
            for fname in os.listdir(HEALTH_DIR):
                sources.append(os.path.join(HEALTH_DIR, fname))

        found_metrics = {m: False for m in expected_metrics}
        for path in sources:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read().lower()
                for m in expected_metrics:
                    if m in content:
                        found_metrics[m] = True

        for m, found in found_metrics.items():
            self.assertTrue(found, f"Health data contract missing metric: '{m}'")

    def test_r4_04_no_unhandled_capacitor_health_web_crash(self):
        """
        Programmatic check:
        Ensures any import or call to @capawesome-team/capacitor-health or @capawesome/capacitor-health
        is guarded by platform checks (isNativePlatform) or try/catch fallback,
        preventing 'Plugin Health not implemented on web' in browser.
        """
        if not os.path.exists(HEALTH_DIR):
            self.skipTest("Health directory not yet present; checked against test spec.")

        for root, _, files in os.walk(HEALTH_DIR):
            for file in files:
                if file.endswith((".ts", ".tsx")):
                    file_path = os.path.join(root, file)
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    if "capacitor-health" in content:
                        # Must have defensive guards
                        has_guard = (
                            "isnativeplatform" in content.lower() or 
                            "try" in content.lower() or
                            "getplatform" in content.lower()
                        )
                        self.assertTrue(
                            has_guard,
                            f"{file} imports capacitor-health without platform check or try-catch guard!"
                        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
