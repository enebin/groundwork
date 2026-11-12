import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "bin" / "groundwork.js"
NODE = shutil.which("node")

# Real `plugin list --json` output shapes, trimmed to the fields the installer reads.
PLUGIN_LIST = {
    "claude": {
        True: '[{"id": "groundwork@groundwork", "version": "0.4.0", "scope": "user", "enabled": true}]',
        False: "[]",
    },
    "codex": {
        True: '{"installed": [{"pluginId": "groundwork@groundwork", "name": "groundwork", '
        '"marketplaceName": "groundwork", "installed": true, "enabled": true}], "available": []}',
        False: '{"installed": [], "available": []}',
    },
}
LIST_ARGS = {"claude": "plugin list --json", "codex": "plugin list -m groundwork --json"}


@unittest.skipUnless(NODE, "node is not installed")
class NpxInstallerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.bin = self.tmp / "bin"
        self.bin.mkdir()
        self.log = self.tmp / "calls.log"

    def fake_cli(self, name, fail_on=None, has_groundwork=True):
        fail = f'[ "$*" = "{fail_on}" ] && exit 3\n' if fail_on else ""
        listing = f"[ \"$*\" = \"{LIST_ARGS[name]}\" ] && echo '{PLUGIN_LIST[name][has_groundwork]}'\n"
        script = self.bin / name
        script.write_text(f'#!/bin/sh\necho "{name} $*" >> "{self.log}"\n{fail}{listing}exit 0\n')
        script.chmod(0o755)

    def run_installer(self, *args):
        env = {**os.environ, "PATH": f"{self.bin}:/usr/bin:/bin"}
        return subprocess.run(
            [NODE, str(INSTALLER), *args], env=env, capture_output=True, text=True
        )

    def calls(self):
        if not self.log.exists():
            return []
        return [
            line
            for line in self.log.read_text().splitlines()
            if not line.endswith(("--version", *LIST_ARGS.values()))
        ]

    def test_install_runs_native_commands_for_each_cli(self):
        self.fake_cli("claude")
        self.fake_cli("codex")
        result = self.run_installer("install")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            self.calls(),
            [
                "claude plugin marketplace add enebin/groundwork",
                "claude plugin install groundwork@groundwork",
                "codex plugin marketplace add enebin/groundwork",
                "codex plugin add groundwork@groundwork",
            ],
        )

    def test_update_refreshes_marketplace_then_plugin(self):
        self.fake_cli("claude")
        self.fake_cli("codex")
        result = self.run_installer("update")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            self.calls(),
            [
                "claude plugin marketplace update groundwork",
                "claude plugin update groundwork@groundwork",
                "codex plugin marketplace upgrade groundwork",
                "codex plugin add groundwork@groundwork",
            ],
        )

    def test_update_skips_cli_without_groundwork(self):
        self.fake_cli("claude", has_groundwork=False)
        self.fake_cli("codex")
        result = self.run_installer("update")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("groundwork is not installed for Claude Code; skipped.", result.stdout)
        self.assertIn("npx @enebin/groundwork@latest install", result.stdout)
        self.assertEqual(
            self.calls(),
            [
                "codex plugin marketplace upgrade groundwork",
                "codex plugin add groundwork@groundwork",
            ],
        )

    def test_update_without_groundwork_anywhere_points_to_install(self):
        self.fake_cli("claude", has_groundwork=False)
        self.fake_cli("codex", has_groundwork=False)
        result = self.run_installer("update")
        self.assertEqual(result.returncode, 1)
        self.assertIn("npx @enebin/groundwork@latest install", result.stderr)
        self.assertEqual(self.calls(), [])

    def test_update_runs_anyway_when_plugin_list_is_unreadable(self):
        self.fake_cli("claude", fail_on=LIST_ARGS["claude"])
        self.fake_cli("codex")
        result = self.run_installer("update")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Could not read the plugin list from `claude plugin list --json`", result.stderr)
        self.assertEqual(
            self.calls(),
            [
                "claude plugin marketplace update groundwork",
                "claude plugin update groundwork@groundwork",
                "codex plugin marketplace upgrade groundwork",
                "codex plugin add groundwork@groundwork",
            ],
        )

    def test_only_detected_cli_is_used(self):
        self.fake_cli("codex")
        result = self.run_installer("install")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(all(call.startswith("codex ") for call in self.calls()))

    def test_no_cli_found_fails_with_recovery(self):
        result = self.run_installer("install")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Install one of them", result.stderr)

    def test_failure_in_one_cli_still_runs_the_other_and_exits_nonzero(self):
        self.fake_cli("claude", fail_on="plugin marketplace add enebin/groundwork")
        self.fake_cli("codex")
        result = self.run_installer("install")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Failed for Claude Code", result.stderr)
        self.assertNotIn("claude plugin install groundwork@groundwork", self.calls())
        self.assertIn("codex plugin add groundwork@groundwork", self.calls())

    def test_unknown_command_shows_usage(self):
        result = self.run_installer("instal")
        self.assertEqual(result.returncode, 2)
        self.assertIn("Unknown argument: instal", result.stderr)
        self.assertIn("Usage:", result.stderr)

    def test_no_command_installs(self):
        self.fake_cli("claude")
        result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            self.calls(),
            [
                "claude plugin marketplace add enebin/groundwork",
                "claude plugin install groundwork@groundwork",
            ],
        )

    def test_target_limits_to_one_cli(self):
        self.fake_cli("claude")
        self.fake_cli("codex")
        result = self.run_installer("install", "--target", "codex")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            self.calls(),
            [
                "codex plugin marketplace add enebin/groundwork",
                "codex plugin add groundwork@groundwork",
            ],
        )

    def test_target_before_command(self):
        self.fake_cli("claude")
        self.fake_cli("codex")
        result = self.run_installer("--target", "codex", "update")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            self.calls(),
            [
                "codex plugin marketplace upgrade groundwork",
                "codex plugin add groundwork@groundwork",
            ],
        )

    def test_target_equals_form(self):
        self.fake_cli("claude")
        self.fake_cli("codex")
        result = self.run_installer("--target=claude")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(all(call.startswith("claude ") for call in self.calls()))

    def test_two_commands_rejected(self):
        result = self.run_installer("install", "update")
        self.assertEqual(result.returncode, 2)
        self.assertIn("Unknown argument: update", result.stderr)

    def test_target_not_on_path_names_it(self):
        self.fake_cli("claude")
        result = self.run_installer("--target", "codex")
        self.assertEqual(result.returncode, 1)
        self.assertIn("`codex` was not found on PATH", result.stderr)
        self.assertEqual(self.calls(), [])

    def test_invalid_target_shows_usage(self):
        result = self.run_installer("install", "--target", "cursor")
        self.assertEqual(result.returncode, 2)
        self.assertIn("--target must be claude or codex, got: cursor", result.stderr)


if __name__ == "__main__":
    unittest.main()
