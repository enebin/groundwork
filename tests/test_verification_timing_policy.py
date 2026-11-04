"""Contract checks for verification timing in groundwork workflow instructions."""
import importlib.util
from pathlib import Path
import re
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIRST_REVIEW_POLICY = "once immediately before the first review"
FIX_ONLY_POLICY = "only tests added or changed"
SCAN_PATH = ROOT / "plugins/groundwork/skills/update/scan.py"
SCAN_SPEC = importlib.util.spec_from_file_location("verification_policy_scan", SCAN_PATH)
SCAN = importlib.util.module_from_spec(SCAN_SPEC)
sys.modules["verification_policy_scan"] = SCAN
SCAN_SPEC.loader.exec_module(SCAN)


class VerificationTimingPolicyTests(unittest.TestCase):
    def read(self, relative_path):
        return (ROOT / relative_path).read_text()

    def test_given_eco_or_normal_step_when_review_starts_then_full_verification_runs_once(self):
        step = self.read("plugins/groundwork/skills/step/SKILL.md")

        self.assertIn("run every `verification.commands` entry once", step)
        self.assertIn(FIRST_REVIEW_POLICY, step)
        self.assertNotIn("Run every `verification.commands` entry before completion", step)
        self.assertIn("For a non-design step, do both:", step)
        self.assertIn("- Run the after-implementation gate", step)

    def test_given_review_fixes_when_verified_then_only_new_or_changed_tests_run(self):
        fixer = self.read("plugins/groundwork/agents/fixer.md")
        quick = self.read("plugins/groundwork/skills/review-and-fix/SKILL.md")

        self.assertIn(FIX_ONLY_POLICY, fixer)
        self.assertIn(FIX_ONLY_POLICY, quick)
        self.assertIn("Do not repeat the complete suite at finish", quick)

    def test_given_documented_modes_when_read_then_sport_keeps_full_rounds(self):
        config = self.read("plugins/groundwork/reference/config.md")
        implementation = self.read("plugins/groundwork/reference/implementation.md")

        self.assertIn("every verification command in every round", config)
        self.assertIn(FIRST_REVIEW_POLICY, implementation)
        self.assertIn("Sport runs the full suite in every review round", implementation)

    def test_given_repository_rules_when_source_is_current_then_marker_matches(self):
        rules = self.read("AGENTS.md")
        marker = re.search(r"groundwork:begin implementation source=([0-9a-f]+)", rules)

        self.assertIsNotNone(marker)
        self.assertEqual(marker.group(1), SCAN.sources()["implementation"])

    def test_given_rebase_when_incoming_code_changes_then_affected_tests_run(self):
        takeoff = self.read("plugins/groundwork/skills/takeoff/SKILL.md")

        self.assertIn("run the tests affected by the incoming commits", takeoff)


if __name__ == "__main__":
    unittest.main()
