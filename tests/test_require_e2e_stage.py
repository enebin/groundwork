import json
from pathlib import Path
import subprocess
import tempfile
import unittest

HOOK = Path(__file__).resolve().parents[1] / "plugins/groundwork/hooks/require-e2e-stage.py"
FULL = "npx playwright test"
TARGETED = "npx playwright test --grep"
GROUNDWORK_MD = f"""---
verification:
  addons: [isolated-e2e, e2e-stage]
  ui_tests:
    targeted: "{TARGETED} {{test}}"
    full: "{FULL}"
  design_source: null
---
"""


class RequireE2EStageTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.repo = Path(self.dir.name)
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)

    def tearDown(self):
        self.dir.cleanup()

    def run_hook(self, command, groundwork_md=GROUNDWORK_MD):
        if groundwork_md is not None:
            (self.repo / "GROUNDWORK.md").write_text(groundwork_md)
        payload = {"tool_name": "Bash", "cwd": str(self.repo), "tool_input": {"command": command}}
        return subprocess.run(
            ["python3", str(HOOK)], input=json.dumps(payload), capture_output=True, text=True
        )

    def test_given_full_ui_suite_without_stage_when_run_then_it_is_blocked_with_the_stages(self):
        result = self.run_hook(FULL)

        self.assertEqual(result.returncode, 2)
        for stage in ("screenshot", "review", "checkpoint", "release"):
            self.assertIn(stage, result.stderr)

    def test_given_targeted_test_without_stage_when_run_then_it_is_blocked(self):
        result = self.run_hook(f"cd app && {TARGETED} login")

        self.assertEqual(result.returncode, 2)

    def test_given_a_valid_stage_after_cd_when_run_then_it_passes(self):
        result = self.run_hook(f"cd app && E2E_STAGE=checkpoint {FULL}")

        self.assertEqual(result.returncode, 0)

    def test_given_an_unknown_stage_when_run_then_it_is_blocked(self):
        result = self.run_hook(f"E2E_STAGE=anytime {FULL}")

        self.assertEqual(result.returncode, 2)

    def test_given_an_unrelated_command_when_run_then_it_passes(self):
        result = self.run_hook("npm run build")

        self.assertEqual(result.returncode, 0)

    def test_given_no_groundwork_file_when_run_then_it_passes(self):
        result = self.run_hook(FULL, groundwork_md=None)

        self.assertEqual(result.returncode, 0)

    def test_given_the_add_on_is_off_when_the_full_suite_runs_without_stage_then_it_passes(self):
        off = GROUNDWORK_MD.replace("[isolated-e2e, e2e-stage]", "[isolated-e2e]")

        result = self.run_hook(FULL, groundwork_md=off)

        self.assertEqual(result.returncode, 0)

    def test_given_the_add_on_in_a_block_list_when_run_without_stage_then_it_is_blocked(self):
        block_list = GROUNDWORK_MD.replace("  addons: [isolated-e2e, e2e-stage]\n", "  addons:\n    - e2e-stage\n")

        result = self.run_hook(FULL, groundwork_md=block_list)

        self.assertEqual(result.returncode, 2)

    def test_given_unset_ui_tests_when_run_then_it_passes(self):
        unset = "---\nverification:\n  addons: [e2e-stage]\n  ui_tests:\n    targeted: null\n    full: null\n---\n"

        result = self.run_hook(FULL, groundwork_md=unset)

        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
