"""Behavior checks use temporary repositories and fake Slack/GitHub boundaries."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import call, patch

SKILL = Path(__file__).resolve().parents[1] / "plugins/groundwork/skills/slack-report"


def load_helper(name):
    spec = importlib.util.spec_from_file_location(name, SKILL / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


post = load_helper("post")
install = load_helper("install")
stop_hook = load_helper("stop_hook")


class IsolatedTest(unittest.TestCase):
    def setUp(self):
        self.context = contextlib.ExitStack()
        self.addCleanup(self.context.close)


class ReportTests(IsolatedTest):
    TOKEN = "test-token-not-a-credential"
    TEAM = "T_TEST"
    CHANNEL = "C_TEST"
    BRANCH = "step/example"
    TITLE = "Saved filters are ready"
    BODY = "Added saved filters.\n---\nTests passed."
    STAMP = "123.456"

    def setUp(self):
        super().setUp()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.token = self.root / "token"
        self.token.write_text(self.TOKEN)
        self.body = self.root / "body.txt"
        self.body.write_text(self.BODY)
        self.info = self.root / "SLACK_INFO.md"
        self.info.write_text(f"channel: team-work\nworkspace_id: {self.TEAM}\nauto_report: false\n")
        self.state = self.root / "reported-state"
        patches = (
            patch.object(post, "TOKEN_PATH", self.token),
            patch.object(post, "USER_ID_PATH", self.root / "user-id"),
            patch.object(post, "THREADS_DIR", self.root / "threads"),
            patch.object(post, "STATE_DIR", self.root / "state"),
            patch.object(post, "state_path", return_value=self.state),
            patch.object(post, "git", side_effect=self.fake_git),
            patch.object(post, "repo_name", return_value="example"),
            patch.object(post, "fingerprint", return_value="observed-before-post"),
            patch.object(post, "current_pr", return_value=None),
            patch.object(post, "call", side_effect=self.fake_slack),
            patch.object(post, "invite_owner"),
        )
        self.mocks = [self.context.enter_context(item) for item in patches]
        self.api = self.mocks[-2]

    def fake_git(self, *args):
        if args == ("rev-parse", "--show-toplevel"):
            return str(self.root)
        if args == ("symbolic-ref", "--short", "-q", "HEAD"):
            return self.BRANCH
        raise AssertionError(f"Unexpected Git request: {args}")

    def fake_slack(self, method, token, **params):
        self.assertEqual(token, self.TOKEN)
        if method == "auth.test":
            return {"ok": True, "team": "Test workspace", "team_id": self.TEAM, "user": "report-bot"}
        if method == "conversations.create":
            return {"ok": True, "channel": {"id": self.CHANNEL}}
        if method == "chat.postMessage":
            return {"ok": True, "channel": self.CHANNEL, "ts": self.STAMP}
        if method == "chat.getPermalink":
            return {"ok": True, "permalink": "https://example.invalid/report"}
        if method == "chat.update":
            return {"ok": True}
        raise AssertionError(f"Unexpected Slack request: {method}")

    def run_main(self, *extra):
        args = ["post.py", "--title", self.TITLE, "--body", str(self.body), *extra]
        output = io.StringIO()
        with patch.object(sys, "argv", args), contextlib.redirect_stdout(output):
            post.main()
        return output.getvalue()

    def test_report_uses_the_confirmed_channel_and_returns_a_link(self):
        # Given a confirmed workspace and a report.
        expected_link = "https://example.invalid/report"
        # When a report is posted.
        output = self.run_main()
        # Then it uses the configured channel and records delivery.
        self.assertIn(expected_link, output)
        self.assertIn(call("conversations.create", self.TOKEN, name="team-work"), self.api.call_args_list)
        self.assertEqual(self.state.read_text(), "observed-before-post")

    def test_check_shows_workspace_identity_without_posting(self):
        # Given configured local credentials.
        output = io.StringIO()
        # When the user checks the connection.
        with patch.object(sys, "argv", ["post.py", "--check"]), contextlib.redirect_stdout(output):
            post.main()
        # Then only identity is returned and no message or state is written.
        self.assertEqual(json.loads(output.getvalue())["team_id"], self.TEAM)
        self.api.assert_called_once_with("auth.test", self.TOKEN)
        self.assertNotIn(self.TOKEN, output.getvalue())
        self.assertFalse(self.state.exists())

    def test_missing_credentials_fail_before_the_network_boundary(self):
        # Given a missing token file.
        self.token.unlink()
        # When reporting is requested.
        with self.assertRaisesRegex(SystemExit, "Slack token missing"):
            self.run_main()
        # Then the failure explains setup and no network request occurs.
        self.api.assert_not_called()

    def test_wrong_workspace_is_rejected_before_mutations(self):
        # Given credentials for a different workspace.
        self.info.write_text("workspace_id: T_OTHER\n")
        # When reporting is requested.
        with self.assertRaisesRegex(SystemExit, "does not match"):
            self.run_main()
        # Then only the identity lookup occurred.
        self.api.assert_called_once_with("auth.test", self.TOKEN)
        self.assertFalse(self.state.exists())

    def test_rejected_credentials_do_not_attempt_delivery(self):
        # Given an expired bot token.
        self.api.return_value = {"ok": False, "error": "invalid_auth"}
        self.api.side_effect = None
        # When reporting is requested.
        with self.assertRaisesRegex(SystemExit, "invalid_auth"):
            self.run_main()
        # Then authentication is the only request and no state is acknowledged.
        self.api.assert_called_once_with("auth.test", self.TOKEN)
        self.assertFalse(self.state.exists())

    def test_unconfirmed_workspace_requires_setup_before_mutations(self):
        # Given legacy settings without a confirmed workspace.
        self.info.write_text("auto_report: false\n")
        # When reporting is requested.
        with self.assertRaisesRegex(SystemExit, "save workspace_id"):
            self.run_main()
        # Then no channel or message is created.
        self.api.assert_called_once_with("auth.test", self.TOKEN)

    def test_empty_report_does_not_create_a_channel(self):
        # Given an empty report.
        self.body.write_text(" \n---\n ")
        # When reporting is requested.
        with self.assertRaisesRegex(SystemExit, "body is empty"):
            self.run_main()
        # Then no write request occurred.
        self.api.assert_called_once_with("auth.test", self.TOKEN)

    def test_repeated_branch_reports_reuse_the_parent(self):
        # Given a branch with one delivered report.
        self.run_main()
        self.api.reset_mock()
        # When the next report is sent.
        self.run_main()
        # Then it adds a reply without another parent.
        writes = [item for item in self.api.call_args_list if item.args[0] == "chat.postMessage"]
        self.assertEqual(len(writes), 1)
        self.assertEqual(writes[0].kwargs["thread_ts"], self.STAMP)

    def test_channel_override_does_not_reuse_a_different_channel_thread(self):
        # Given a report on the default channel.
        self.run_main()
        self.api.reset_mock()
        # When a report is requested for another channel.
        self.run_main("--channel", "other-work")
        # Then a parent is created for that channel instead of reusing the old parent.
        writes = [item for item in self.api.call_args_list if item.args[0] == "chat.postMessage"]
        self.assertEqual(writes[0].kwargs["channel"], "#other-work")
        self.assertNotIn("thread_ts", writes[0].kwargs)

    def test_long_repository_names_keep_channel_threads_separate(self):
        # Given a long repository name and a report already sent to one channel.
        repository = "r" * 75
        next_channel = "second-channel"
        with patch.object(post, "repo_name", return_value=repository):
            self.run_main("--channel", "first-channel")
            self.api.reset_mock()
            # When a report targets a different channel on the same branch.
            self.run_main("--channel", next_channel)
        # Then it creates that channel's parent instead of using the old channel ID.
        writes = [item for item in self.api.call_args_list if item.args[0] == "chat.postMessage"]
        self.assertEqual(writes[0].kwargs["channel"], f"#{next_channel}")
        self.assertNotIn("thread_ts", writes[0].kwargs)

    def test_main_branch_reports_each_start_a_new_thread(self):
        # Given a trunk branch.
        self.BRANCH = "main"
        # When two reports are posted.
        self.run_main()
        self.run_main()
        # Then each has its own parent.
        parents = [item for item in self.api.call_args_list if item.args[0] == "chat.postMessage" and "thread_ts" not in item.kwargs]
        self.assertEqual(len(parents), 2)

    def test_failed_reply_leaves_delivery_unacknowledged(self):
        # Given Slack accepts a parent but rejects its reply.
        def fail_reply(method, token, **params):
            if method == "chat.postMessage" and "thread_ts" in params:
                return {"ok": False, "error": "ratelimited"}
            return self.fake_slack(method, token, **params)
        self.api.side_effect = fail_reply
        # When reporting is attempted.
        with self.assertRaisesRegex(SystemExit, "ratelimited"):
            self.run_main()
        # Then the hook fingerprint remains unacknowledged and there was no retry.
        self.assertFalse(self.state.exists())
        replies = [item for item in self.api.call_args_list if item.args[0] == "chat.postMessage" and "thread_ts" in item.kwargs]
        self.assertEqual(len(replies), 1)

    def test_changes_arriving_during_delivery_are_not_marked_reported(self):
        # Given the repository changes while Slack is processing the report.
        fingerprint = self.mocks[7]
        fingerprint.side_effect = ["before-delivery", "changed-during-delivery"]
        # When delivery finishes.
        self.run_main()
        # Then the saved observation cannot hide the later change.
        self.assertEqual(self.state.read_text(), "before-delivery")
        self.assertNotEqual(self.state.read_text(), post.fingerprint())

    def test_long_sections_are_split_without_losing_text(self):
        # Given one section longer than the Slack reply budget.
        section = "x" * (post.MAX_REPLY_CHARS * 2 + 7)
        # When the report is chunked.
        chunks = post.chunk_report(self.TITLE, section)
        # Then every chunk fits and its body can be reconstructed.
        self.assertTrue(all(len(chunk) <= post.MAX_REPLY_CHARS for chunk in chunks))
        self.assertEqual("".join(chunks[1:]), section)

    def test_pr_status_refresh_keeps_the_original_title(self):
        # Given an open PR and its original branch title.
        pr = {"number": 7, "url": "https://example.invalid/pr/7", "status": "open"}
        entry = {"title": self.TITLE, "channel": self.CHANNEL, "ts": self.STAMP}
        # When the PR merges and the parent is refreshed twice.
        pr["status"] = "merged"
        post.sync_parent(self.TOKEN, entry, pr)
        post.sync_parent(self.TOKEN, entry, pr)
        # Then one update records the merge and preserves the branch goal.
        expected = post.parent_text(self.TITLE, pr)
        self.api.assert_called_once_with("chat.update", self.TOKEN, channel=self.CHANNEL, ts=self.STAMP, text=expected)
        self.assertEqual(entry["parent_text"], expected)

    def test_failed_parent_refresh_keeps_the_previous_status(self):
        # Given a saved draft whose Slack update will fail.
        previous = post.parent_text(self.TITLE, None)
        entry = {"title": self.TITLE, "channel": self.CHANNEL, "ts": self.STAMP, "parent_text": previous}
        pr = {"number": 7, "url": "https://example.invalid/pr/7", "status": "merged"}
        self.api.side_effect = None
        self.api.return_value = {"ok": False, "error": "message_not_found"}
        # When the parent status is refreshed.
        with contextlib.redirect_stderr(io.StringIO()) as error:
            post.sync_parent(self.TOKEN, entry, pr)
        # Then failed synchronization is visible and is not recorded as success.
        self.assertIn("message_not_found", error.getvalue())
        self.assertEqual(entry["parent_text"], previous)


class HookTests(IsolatedTest):
    def setUp(self):
        super().setUp()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.info = self.root / "SLACK_INFO.md"
        self.info.write_text("auto_report: true\n")
        self.state = self.root / "state"
        self.context.enter_context(patch.object(stop_hook.os, "chdir"))
        self.context.enter_context(patch.object(post, "git", return_value=str(self.root)))
        self.context.enter_context(patch.object(post, "state_path", return_value=self.state))
        self.context.enter_context(patch.object(post, "fingerprint", return_value="changed"))

    def invoke(self, event):
        output = io.StringIO()
        with patch.object(sys, "stdin", io.StringIO(event)), contextlib.redirect_stdout(output):
            stop_hook.main()
        return output.getvalue()

    def test_both_client_stop_payloads_request_one_report(self):
        # Given supported Claude Code and Codex Stop payloads.
        events = ({"hook_event_name": "Stop", "session_id": "claude-test"}, {"hook_event_name": "Stop", "turn_id": "codex-test"})
        # When their turn ends with unreported changes.
        for event in events:
            with self.subTest(event=event):
                result = json.loads(self.invoke(json.dumps(event)))
                # Then the documented continuation requests the shared skill.
                self.assertEqual(result["decision"], "block")
                self.assertIn("groundwork:slack-report", result["reason"])

    def test_manual_mode_never_requests_an_automatic_post(self):
        # Given automatic reports are disabled.
        self.info.write_text("auto_report: false\n")
        # When a turn ends.
        output = self.invoke("{}")
        # Then the hook remains silent.
        self.assertEqual(output, "")

    def test_malformed_opt_in_does_not_enable_reporting(self):
        # Given an opt-in value placed on the wrong line.
        self.info.write_text("auto_report:\ntrue\n")
        # When a turn ends.
        output = self.invoke("{}")
        # Then malformed configuration cannot authorize an automatic report.
        self.assertEqual(output, "")

    def test_unchanged_repository_is_ignored(self):
        # Given the last report covered this fingerprint.
        self.state.write_text("changed")
        # When the turn ends.
        output = self.invoke("{}")
        # Then no duplicate report is requested.
        self.assertEqual(output, "")

    def test_failed_post_continuation_can_end_without_a_loop(self):
        # Given a hook already continued this turn and posting failed.
        event = json.dumps({"stop_hook_active": True})
        # When the continued turn ends.
        output = self.invoke(event)
        # Then another post is not requested indefinitely.
        self.assertEqual(output, "")

    def test_invalid_hook_input_is_ignored(self):
        # Given malformed or non-object input.
        for event in ("not-json", "[]", "null"):
            # When the hook reads it.
            with self.subTest(event=event):
                output = self.invoke(event)
                # Then it has no effect on the agent turn.
                self.assertEqual(output, "")


class InstallationTests(IsolatedTest):
    def setUp(self):
        super().setUp()
        self.temp = tempfile.TemporaryDirectory(prefix="groundwork tests ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.context.enter_context(patch.object(post, "git", side_effect=self.fake_git))
        self.context.enter_context(contextlib.redirect_stdout(io.StringIO()))

    def fake_git(self, *args):
        if args == ("rev-parse", "--show-toplevel"):
            return str(self.root)
        if args == ("rev-parse", "--path-format=absolute", "--git-common-dir"):
            return str(self.root / ".git")
        raise AssertionError(f"Unexpected Git request: {args}")

    def test_reinstallation_preserves_user_settings_and_avoids_duplicate_hooks(self):
        # Given existing unrelated settings and a custom Stop hook in each client.
        custom = {"type": "command", "command": "echo keep-custom"}
        for rel in install.TARGETS:
            path = self.root / rel
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps({"user_setting": True, "hooks": {"Stop": [{"hooks": [custom]}]}}))
        rules = self.root / "AGENTS.md"
        rules.write_text("# My repository rules\n")
        # When setup runs twice.
        install.main()
        first = {rel: (self.root / rel).read_bytes() for rel in (*install.TARGETS, "AGENTS.md", "CLAUDE.md")}
        install.main()
        # Then settings, custom hooks, and instruction text survive without duplicates.
        for rel, expected in first.items():
            self.assertEqual((self.root / rel).read_bytes(), expected)
        for rel in install.TARGETS:
            config = json.loads((self.root / rel).read_text())
            self.assertTrue(config["user_setting"])
            hooks = [hook for group in config["hooks"]["Stop"] for hook in group["hooks"]]
            self.assertIn(custom, hooks)
            self.assertEqual(sum(install.MARKER in hook["command"] for hook in hooks), 1)
        self.assertTrue(rules.read_text().startswith("# My repository rules"))

    def test_invalid_existing_json_is_not_overwritten(self):
        # Given a malformed existing Codex hook file.
        path = self.root / ".codex/hooks.json"
        path.parent.mkdir()
        invalid = "{invalid"
        path.write_text(invalid)
        # When setup is attempted.
        with self.assertRaises(json.JSONDecodeError):
            install.main()
        # Then existing content is preserved and no partial install begins.
        self.assertEqual(path.read_text(), invalid)
        self.assertFalse((self.root / ".claude").exists())
        self.assertFalse((self.root / ".groundwork").exists())

    def test_personal_hook_path_is_migrated_without_a_duplicate(self):
        # Given a legacy personal installation.
        rel = install.TARGETS[0]
        path = self.root / rel
        path.parent.mkdir()
        path.write_text(json.dumps({"hooks": {"Stop": [{"hooks": [{"type": "command", "command": 'python3 "$HOME/.claude/skills/slack-report/stop_hook.py"'}]}]}}))
        # When the portable setup is installed.
        install.main()
        # Then the legacy hook is replaced in place.
        groups = json.loads(path.read_text())["hooks"]["Stop"]
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["hooks"][0]["command"], install.COMMAND)

    def test_installed_hooks_work_from_a_subdirectory_without_the_original_skill(self):
        # Given a fresh temporary repository and copied runtime.
        subprocess.run(["git", "init", "--quiet", str(self.root)], check=True)
        install.main()
        (self.root / "SLACK_INFO.md").write_text("auto_report: true\n")
        nested = self.root / "nested"
        nested.mkdir()
        # When either client's installed command runs from a subdirectory.
        for rel in install.TARGETS:
            config = json.loads((self.root / rel).read_text())
            command = config["hooks"]["Stop"][0]["hooks"][0]["command"]
            result = subprocess.run(["sh", "-c", command], cwd=nested, input=json.dumps({"cwd": str(nested)}), capture_output=True, text=True, check=True)
            # Then its local runtime emits the shared continuation without personal paths.
            self.assertEqual(json.loads(result.stdout)["decision"], "block")
            self.assertNotIn(str(SKILL), command)
        ignored = subprocess.run(["git", "check-ignore", str(self.root / ".groundwork/slack-report/post.py")], cwd=self.root, capture_output=True, text=True)
        self.assertEqual(ignored.returncode, 0)

    def test_missing_local_runtime_is_a_safe_noop(self):
        # Given shared hook settings on a new clone without local runtime.
        subprocess.run(["git", "init", "--quiet", str(self.root)], check=True)
        # When the hook runs before local installation.
        result = subprocess.run(["sh", "-c", install.COMMAND], cwd=self.root, input="{}", capture_output=True, text=True)
        # Then it ends successfully without continuing or posting.
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_fresh_worktrees_use_shared_runtime_and_their_own_opt_in(self):
        # Given one installation and a new worktree that shares hook settings.
        subprocess.run(["git", "init", "--quiet", str(self.root)], check=True)
        install.main()
        worktree = self.root / "issue-worktree"
        subprocess.run(["git", "worktree", "add", "--orphan", "-b", "step/test", str(worktree)], cwd=self.root, capture_output=True, text=True, check=True)
        info = worktree / "SLACK_INFO.md"
        info.write_text("auto_report: true\n")
        environment = dict(os.environ, HOME=str(self.root / "test-home"))
        for rel in install.TARGETS:
            destination = worktree / rel
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(self.root / rel, destination)
        # When both clients run the inherited hook in that fresh worktree.
        for rel in install.TARGETS:
            config = json.loads((worktree / rel).read_text())
            command = config["hooks"]["Stop"][0]["hooks"][0]["command"]
            result = subprocess.run(["sh", "-c", command], cwd=worktree, env=environment, input=json.dumps({"cwd": str(worktree)}), capture_output=True, text=True, check=True)
            # Then shared code requests a report without copying a runtime into the worktree.
            self.assertEqual(json.loads(result.stdout)["decision"], "block")
            self.assertFalse((worktree / ".groundwork/slack-report").exists())
        info.write_text("auto_report: false\n")
        result = subprocess.run(["sh", "-c", install.COMMAND], cwd=worktree, env=environment, input=json.dumps({"cwd": str(worktree)}), capture_output=True, text=True, check=True)
        self.assertEqual(result.stdout, "")

    def test_installing_from_a_linked_worktree_populates_the_shared_runtime(self):
        # Given a linked worktree before Slack reporting has been installed.
        subprocess.run(["git", "init", "--quiet", str(self.root)], check=True)
        worktree = self.root / "issue-worktree"
        subprocess.run(["git", "worktree", "add", "--orphan", "-b", "step/test", str(worktree)], cwd=self.root, capture_output=True, text=True, check=True)
        # When setup runs from that linked worktree.
        subprocess.run([sys.executable, str(SKILL / "install.py")], cwd=worktree, capture_output=True, text=True, check=True)
        # Then runtime is shared while each client's settings belong to this checkout.
        self.assertTrue((self.root / ".groundwork/slack-report/stop_hook.py").exists())
        self.assertFalse((worktree / ".groundwork/slack-report").exists())
        for rel in install.TARGETS:
            self.assertTrue((worktree / rel).exists())
            self.assertFalse((self.root / rel).exists())


class FingerprintTests(IsolatedTest):
    def setUp(self):
        super().setUp()
        self.temp = tempfile.TemporaryDirectory(prefix="groundwork fingerprint ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        subprocess.run(["git", "init", "--quiet", str(self.root)], check=True)
        original_cwd = Path.cwd()
        self.addCleanup(os.chdir, original_cwd)

    def test_untracked_content_changes_are_detected_from_a_subdirectory(self):
        # Given an untracked file while the session is in a nested folder.
        nested = self.root / "nested"
        nested.mkdir()
        file = nested / "draft.md"
        file.write_text("before")
        os.chdir(nested)
        before = post.fingerprint()
        # When only the untracked file contents change.
        file.write_text("after")
        after = post.fingerprint()
        # Then the hook can see the change.
        self.assertNotEqual(before, after)

    def test_non_ascii_and_newline_filenames_keep_their_content_in_the_hash(self):
        # Given filenames that Git would quote in a line-based listing.
        os.chdir(self.root)
        for name in ("한글.md", "two\nlines.md"):
            with self.subTest(name=name):
                file = self.root / name
                file.write_text("before")
                before = post.fingerprint()
                # When only the file contents change.
                file.write_text("after")
                after = post.fingerprint()
                # Then lossless filename handling includes the new contents.
                self.assertNotEqual(before, after)

    def test_ignored_file_changes_do_not_change_the_reported_fingerprint(self):
        # Given a file excluded by repository rules.
        os.chdir(self.root)
        (self.root / ".gitignore").write_text("*.cache\n")
        ignored = self.root / "scratch.cache"
        ignored.write_text("before")
        before = post.fingerprint()
        # When only the ignored file contents change.
        ignored.write_text("after")
        after = post.fingerprint()
        # Then local runtime and cache updates do not create duplicate work reports.
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
