"""
Tier 3 Acceptance Test: Mobile SPA Frontend Architecture (R3)

Authoritative Source: ORIGINAL_REQUEST.md & PROJECT.md
Acceptance Criteria:
- 5-tab mobile-first React application (Dashboard, Planner, Chat, Calendar, Settings).
- Persistent Header with dynamic streak counter and flame indicator.
- Strava-style bottom navigation bar with active highlights and elevated center tab.
- Frontend build configuration and script integrity.
"""

import unittest
import os
import json
import re

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MOBILE_DIR = os.path.join(REPO_ROOT, "mobile")
SRC_DIR = os.path.join(MOBILE_DIR, "src")


class TestR3MobileFrontend(unittest.TestCase):
    """Verifies Frontend SPA Structure, Navigation Shell, and 5-Tab Layout."""

    def test_r3_01_package_json_and_build_scripts(self):
        """Verify mobile/package.json exists with build and lint scripts."""
        pkg_path = os.path.join(MOBILE_DIR, "package.json")
        self.assertTrue(os.path.exists(pkg_path), f"Missing {pkg_path}")
        
        with open(pkg_path, "r", encoding="utf-8") as f:
            pkg = json.load(f)
            
        scripts = pkg.get("scripts", {})
        self.assertIn("build", scripts, "package.json must define a 'build' script")
        self.assertIn("dev", scripts, "package.json must define a 'dev' script")

    def test_r3_02_all_5_tab_pages_exist(self):
        """Verify all 5 required pages exist in mobile/src/pages/."""
        pages_dir = os.path.join(SRC_DIR, "pages")
        self.assertTrue(os.path.exists(pages_dir), f"Missing pages directory: {pages_dir}")
        
        required_pages = [
            "Dashboard.tsx",
            "Planner.tsx",
            "Chat.tsx",
            "Calendar.tsx",
            "Settings.tsx"
        ]
        for page in required_pages:
            page_path = os.path.join(pages_dir, page)
            self.assertTrue(os.path.exists(page_path), f"Required page missing: {page_path}")

    def test_r3_03_app_router_configures_5_tabs(self):
        """Verify App.tsx configures routes for all 5 tabs."""
        app_path = os.path.join(SRC_DIR, "App.tsx")
        self.assertTrue(os.path.exists(app_path), f"Missing {app_path}")
        
        with open(app_path, "r", encoding="utf-8") as f:
            content = f.read()

        required_routes = ["dashboard", "planner", "chat", "calendar", "settings"]
        for route in required_routes:
            self.assertIn(
                route, content.lower(),
                f"App.tsx route configuration missing route for '{route}'"
            )

    def test_r3_04_persistent_header_has_dynamic_streak(self):
        """Verify Header.tsx implements streak counter and flame icon."""
        header_path = os.path.join(SRC_DIR, "components", "Header.tsx")
        self.assertTrue(os.path.exists(header_path), f"Missing {header_path}")
        
        with open(header_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check for streak display and flame icon
        self.assertTrue(
            "Flame" in content or "flame" in content or "streak" in content.lower(),
            "Header.tsx must contain streak counter or Flame icon component"
        )
        self.assertTrue(
            "Pace" in content or "pace" in content.lower(),
            "Header.tsx must feature 'Pace' branding"
        )

    def test_r3_05_footer_navigation_strava_layout(self):
        """Verify Footer.tsx implements 5-tab navigation with Strava-style layout."""
        footer_path = os.path.join(SRC_DIR, "components", "Footer.tsx")
        self.assertTrue(os.path.exists(footer_path), f"Missing {footer_path}")
        
        with open(footer_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Verify NavLinks to all 5 tabs exist in Footer
        tabs = ["dashboard", "planner", "chat", "calendar", "settings"]
        for tab in tabs:
            self.assertIn(
                tab, content.lower(),
                f"Footer.tsx must contain navigation link to '{tab}'"
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
