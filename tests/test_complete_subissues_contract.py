"""Contract checks for how complete-subissues hands work to takeoff, autoland, and step."""
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
CALLER = "`complete-subissues` invokes it"


class CompleteSubissuesContractTests(unittest.TestCase):
    def read(self, relative_path):
        return (ROOT / relative_path).read_text()

    def test_given_complete_subissues_run_when_takeoff_finishes_then_it_does_not_chain_into_autoland(self):
        takeoff = self.read("plugins/groundwork/skills/takeoff/SKILL.md")
        next_step = re.search(r"10\. \*\*Next\.\*\*(.*)", takeoff).group(1)

        self.assertIn(CALLER, takeoff)
        self.assertLess(
            next_step.index("started by `complete-subissues`, stop here"),
            next_step.index("continue with `/groundwork:autoland <ISSUE>`"),
        )

    def test_given_complete_subissues_run_when_autoland_is_invoked_then_it_is_an_allowed_caller(self):
        autoland = self.read("plugins/groundwork/skills/autoland/SKILL.md")
        driver = self.read("plugins/groundwork/skills/complete-subissues/SKILL.md")

        self.assertIn(CALLER, autoland)
        self.assertIn("tell it this run comes from `complete-subissues`, so it does not chain into autoland", driver)

    def test_given_checkpoint_mode_when_rules_are_read_then_the_full_ui_suite_is_moved_not_removed(self):
        implementation = self.read("plugins/groundwork/reference/implementation.md")
        config = self.read("plugins/groundwork/reference/config.md")

        self.assertIn("while `complete-subissues` runs a parent's sub-issues in checkpoint mode", implementation)
        self.assertIn("No mode removes required tests or screenshot inspection", implementation)
        self.assertIn("while `complete-subissues` runs a parent's sub-issues in checkpoint mode", config)

    def test_given_step_help_when_read_then_ui_checkpoint_is_not_a_public_option(self):
        step = self.read("plugins/groundwork/skills/step/SKILL.md")
        argument_hint = re.search(r"^argument-hint: (.*)$", step, re.MULTILINE).group(1)

        self.assertNotIn("--ui-checkpoint", argument_hint)
        self.assertIn("only `/groundwork:complete-subissues` passes it", step)


if __name__ == "__main__":
    unittest.main()
