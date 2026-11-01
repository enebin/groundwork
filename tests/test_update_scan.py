"""Behavior checks for the update scan, against a fake plugin and temporary repositories."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "plugins/groundwork/skills/update/scan.py"
spec = importlib.util.spec_from_file_location("scan", SCRIPT)
scan = importlib.util.module_from_spec(spec)
sys.modules["scan"] = scan
spec.loader.exec_module(scan)

IMPLEMENTATION_RULES = "### Implementation\n\n- Test state changes."
CHANGES = {
    "releases": [
        {"version": "0.1.0", "items": []},
        {"version": "0.2.0", "items": [
            {"section": "Upgrading", "kind": "migrate", "key": "workflow.bundle", "values": ["flight"], "text": "Migrate flight."},
            {"section": "New features", "kind": "attach", "addons": ["handoff"], "text": "Handoff notes."},
        ]},
        {"version": "0.3.0", "items": [
            {"section": "New features", "kind": "attach", "key": "review.external", "text": "External reviewers."},
            {"section": "Upgrading", "kind": "migrate", "key": "ux", "text": "Migrate UX."},
            {"section": "Bug fixes", "kind": "auto", "text": "Banner fixed."},
        ]},
    ]
}


def config(plugin_version="0.1.0", bundle="step-loop", external="{}", body=""):
    version_line = f"plugin_version: {plugin_version}\n" if plugin_version else ""
    return (
        "---\ngroundwork: 1\n" + version_line
        + "docs:\n  rules: AGENTS.md\n  architecture: ARCHITECTURE.md\n"
        + f"workflow:\n  bundle: {bundle}  # step-loop | flight\n"
        + "verification:\n  commands:\n    - name: Test\n      run: |\n        ux: not a key\n"
        + f"review:\n  reviewers: [code-quality]\n  external: {external}\n"
        + "---\n" + body
    )


class ScanTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.plugin = Path(temp.name) / "plugin"
        self.repo = Path(temp.name) / "repo"
        self.repo.mkdir()
        self.write(self.plugin / ".claude-plugin/plugin.json", json.dumps({"version": "0.3.0"}))
        self.write(self.plugin / "CHANGES.json", json.dumps(CHANGES))
        self.write(self.plugin / "reference/implementation.md",
                   f"# Rules\n\n## Rules to write\n\n```markdown\n{IMPLEMENTATION_RULES}\n```\n")
        self.write(self.plugin / "catalog/architecture/mvvm.md",
                   "# mvvm\n\n## Contract to write\n\n````markdown\n## State\n\n```\nView -> Model\n```\n````\n")
        self.write(self.plugin / "catalog/verification.md",
                   "# Verification\n\n## evidence\n\n### Rules to write\n\nNo block.\n\n"
                   "## api-contract (add-on)\n\n### Rules to write\n\n```markdown\n### API\n```\n")
        original = scan.PLUGIN
        scan.PLUGIN = self.plugin
        self.addCleanup(setattr, scan, "PLUGIN", original)

    def write(self, path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def groups(self, report):
        return {item["text"]: item["group"] for item in report["items"]}

    def test_given_no_groundwork_file_when_scanned_then_reports_not_set_up(self):
        self.assertEqual(scan.scan(self.repo), {"status": "not-set-up"})

    def test_given_setup_at_installed_version_when_scanned_then_up_to_date(self):
        self.write(self.repo / "GROUNDWORK.md", config(plugin_version="0.3.0"))

        report = scan.scan(self.repo)

        self.assertEqual(report["status"], "up-to-date")
        self.assertEqual(report["items"], [])

    def test_given_setup_newer_than_plugin_when_scanned_then_asks_for_plugin_update(self):
        self.write(self.repo / "GROUNDWORK.md", config(plugin_version="0.4.0"))

        self.assertEqual(scan.scan(self.repo)["status"], "plugin-older-than-setup")

    def test_given_older_setup_when_scanned_then_sorts_only_later_releases(self):
        self.write(self.repo / "GROUNDWORK.md", config(plugin_version="0.2.0"))

        report = scan.scan(self.repo)

        self.assertEqual(self.groups(report), {
            "External reviewers.": "can_attach",
            "Migrate UX.": "needs_migration",
            "Banner fixed.": "comes_automatically",
        })
        self.assertEqual(report["choices"], 2)

    def test_given_no_plugin_version_when_scanned_then_checks_every_release(self):
        self.write(self.repo / "GROUNDWORK.md", config(plugin_version=None))

        report = scan.scan(self.repo)

        self.assertEqual({item["version"] for item in report["items"]}, {"0.2.0", "0.3.0"})

    def test_given_flight_workflow_when_scanned_then_flight_migration_is_needed(self):
        self.write(self.repo / "GROUNDWORK.md", config(bundle="flight"))

        self.assertEqual(self.groups(scan.scan(self.repo))["Migrate flight."], "needs_migration")

    def test_given_other_workflow_when_scanned_then_flight_migration_is_in_place(self):
        self.write(self.repo / "GROUNDWORK.md", config())

        self.assertEqual(self.groups(scan.scan(self.repo))["Migrate flight."], "already_in_place")

    def test_given_configured_key_when_scanned_then_attach_item_is_in_place(self):
        self.write(self.repo / "GROUNDWORK.md", config(external='{writing: "Gemini"}'))

        self.assertEqual(self.groups(scan.scan(self.repo))["External reviewers."], "already_in_place")

    def test_given_text_inside_block_scalar_when_scanned_then_it_is_not_read_as_a_key(self):
        self.write(self.repo / "GROUNDWORK.md", config())

        self.assertEqual(self.groups(scan.scan(self.repo))["Migrate UX."], "needs_migration")

    def test_given_recorded_addon_when_scanned_then_addon_item_is_in_place(self):
        addons = "## Add-ons\n\n<!-- groundwork:begin addons -->\n| Skill | Settings |\n|---|---|\n| `handoff` | On demand |\n<!-- groundwork:end addons -->\n"
        self.write(self.repo / "GROUNDWORK.md", config(body=addons))

        self.assertEqual(self.groups(scan.scan(self.repo))["Handoff notes."], "already_in_place")

    def test_given_managed_blocks_when_scanned_then_reports_each_source_status(self):
        current = scan.sources()["implementation"]
        self.write(self.repo / "GROUNDWORK.md", config(plugin_version="0.3.0"))
        self.write(self.repo / "AGENTS.md", "\n".join([
            "<!-- groundwork:begin project-rules -->\nOwn rules\n<!-- groundwork:end project-rules -->",
            f"<!-- groundwork:begin implementation source={current} -->\nTranslated text\n<!-- groundwork:end implementation -->",
            "<!-- groundwork:begin api-contract source=000000000000 -->\n### API\n<!-- groundwork:end api-contract -->",
        ]))
        self.write(self.repo / "ARCHITECTURE.md",
                   "<!-- groundwork:begin mvvm -->\n## State\n\n```\nView -> Model\n```\n<!-- groundwork:end mvvm -->\n")

        report = scan.scan(self.repo)

        self.assertEqual({block["id"]: block["status"] for block in report["blocks"]}, {
            "project-rules": "unknown",
            "implementation": "same",
            "api-contract": "changed",
            "mvvm": "unstamped-same",
        })
        self.assertEqual(report["status"], "ok")

    def test_given_section_without_fence_when_sources_listed_then_it_has_no_hash(self):
        self.assertEqual(set(scan.sources()), {"implementation", "mvvm", "api-contract"})

    def test_given_release_when_notes_rendered_then_sections_follow_release_order(self):
        self.assertEqual(scan.notes("0.3.0"), (
            "## 0.3.0\n\n### New features\n\n- External reviewers.\n\n"
            "### Bug fixes\n\n- Banner fixed.\n\n### Upgrading\n\n- Migrate UX.\n"
        ))


class ShippedChangesTests(unittest.TestCase):
    def test_given_shipped_changes_when_read_then_every_item_is_well_formed(self):
        kinds = {"migrate", "attach", "auto"}
        for release in json.loads((SCRIPT.parents[2] / "CHANGES.json").read_text())["releases"]:
            scan.version_key(release["version"])
            for item in release["items"]:
                self.assertIn(item["kind"], kinds, item["text"])
                if item["kind"] == "attach":
                    self.assertTrue("key" in item or "addons" in item, item["text"])

    def test_given_shipped_changes_when_read_then_latest_release_matches_plugin_version(self):
        plugin = SCRIPT.parents[2]
        installed = json.loads((plugin / ".claude-plugin/plugin.json").read_text())["version"]
        versions = [release["version"] for release in json.loads((plugin / "CHANGES.json").read_text())["releases"]]
        self.assertEqual(max(versions, key=scan.version_key), installed)


if __name__ == "__main__":
    unittest.main()
