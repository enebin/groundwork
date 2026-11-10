"""Behavior checks for the work-audit digest, against fake Claude Code and Codex transcripts."""
from datetime import datetime, timedelta
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "plugins/groundwork/skills/work-audit/digest.py"
spec = importlib.util.spec_from_file_location("digest", SCRIPT)
digest = importlib.util.module_from_spec(spec)
sys.modules["digest"] = digest
spec.loader.exec_module(digest)

DAY_START = datetime(2026, 1, 1).astimezone()
DAY_END = DAY_START + timedelta(days=1)
E2E_COMMAND = "npx playwright test"
OUTPUT_TOKENS = 100
CODEX_SESSION_ID = "codex-parent"


def at(hour, minute=0):
    return (DAY_START + timedelta(hours=hour, minutes=minute)).isoformat()


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))


def claude_turn(cwd, when_user, when_tool_done, when_next):
    return [
        {"type": "user", "cwd": cwd, "timestamp": when_user, "message": {"content": "Run the tests"}},
        {"type": "assistant", "timestamp": when_user, "message": {
            "usage": {"output_tokens": OUTPUT_TOKENS},
            "content": [{"type": "tool_use", "id": "t1", "name": "Bash", "input": {"command": E2E_COMMAND}}]}},
        {"type": "user", "timestamp": when_tool_done, "message": {
            "content": [{"type": "tool_result", "tool_use_id": "t1", "content": "ok"}]}},
        {"type": "assistant", "timestamp": when_next, "message": {
            "usage": {"output_tokens": OUTPUT_TOKENS}, "content": [{"type": "text", "text": "Done"}]}},
    ]


def codex_session(cwd, session_id, parent=None):
    source = {"subagent": {"thread_spawn": {"parent_thread_id": parent, "agent_path": "a/reviewer"}}} if parent else "cli"
    return [
        {"type": "session_meta", "timestamp": at(9), "payload": {"cwd": cwd, "id": session_id, "source": source}},
        {"type": "response_item", "timestamp": at(9), "payload": {
            "type": "function_call", "name": "exec_command", "call_id": "c1", "arguments": json.dumps({"cmd": E2E_COMMAND})}},
        {"type": "response_item", "timestamp": at(9, 2), "payload": {
            "type": "function_call_output", "call_id": "c1", "output": "Process exited with code 1"}},
        {"type": "token_usage_record", "timestamp": at(9, 2), "payload": {"usage": {"output_tokens": OUTPUT_TOKENS}}},
    ]


class DigestTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.home = self.tmp / "home"
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        self.repo_path = os.path.realpath(self.repo)
        env = {"HOME": str(self.home), "CODEX_HOME": str(self.home / ".codex")}
        patcher = mock.patch.dict(os.environ, env)
        patcher.start()
        os.environ.pop("CLAUDE_CONFIG_DIR", None)
        self.addCleanup(patcher.stop)

    def claude_file(self, root, name):
        return self.home / root / "projects" / "p" / f"{name}.jsonl"

    def codex_file(self, name):
        return self.home / ".codex" / "sessions" / "2026" / "01" / "01" / f"{name}.jsonl"

    def collect(self):
        return digest.collect(self.repo_path, DAY_START, DAY_END)

    def test_claude_session_in_the_repository_reports_tokens_commands_and_idle_gaps(self):
        # Given a Claude session in the repository with a 5-minute E2E run and a 40-minute pause
        write_jsonl(self.claude_file(".claude", "s1"), claude_turn(self.repo_path, at(9), at(9, 5), at(9, 45)))

        # When the range is collected
        sessions = self.collect()

        # Then its tokens, E2E run, and idle gap are reported
        self.assertEqual(len(sessions), 1)
        session = sessions[0]
        self.assertEqual(session["tokens"]["out_tok"], 2 * OUTPUT_TOKENS)
        self.assertEqual(session["cmd_kinds"]["e2e"], {"n": 1, "min": 5.0})
        self.assertEqual([gap["minutes"] for gap in session["idle_gaps"]], [40])

    def test_session_in_another_folder_is_ignored(self):
        # Given a Claude session that ran outside the repository
        write_jsonl(self.claude_file(".claude", "s1"), claude_turn(str(self.tmp), at(9), at(9, 5), at(9, 6)))

        # When the range is collected
        sessions = self.collect()

        # Then it is not reported
        self.assertEqual(sessions, [])

    def test_events_outside_the_range_are_not_counted(self):
        # Given a session whose last reply arrives after the range ends
        after_range = (DAY_END + timedelta(hours=1)).isoformat()
        write_jsonl(self.claude_file(".claude", "s1"), claude_turn(self.repo_path, at(23), at(23, 5), after_range))

        # When the range is collected
        session = self.collect()[0]

        # Then only the reply inside the range counts
        self.assertEqual(session["tokens"]["out_tok"], OUTPUT_TOKENS)

    def test_sessions_under_a_custom_claude_config_dir_are_read_too(self):
        # Given one session in ~/.claude and one in a custom CLAUDE_CONFIG_DIR
        write_jsonl(self.claude_file(".claude", "s1"), claude_turn(self.repo_path, at(9), at(9, 5), at(9, 6)))
        write_jsonl(self.claude_file("profile", "s2"), claude_turn(self.repo_path, at(10), at(10, 5), at(10, 6)))
        os.environ["CLAUDE_CONFIG_DIR"] = str(self.home / "profile")

        # When the range is collected
        sessions = self.collect()

        # Then both are reported
        self.assertEqual(len(sessions), 2)

    def test_one_reply_split_over_several_lines_counts_its_tokens_once(self):
        # Given one assistant reply written as a thinking line and a tool-use line with the same id and usage
        reply = {"id": "msg-1", "usage": {"output_tokens": OUTPUT_TOKENS}}
        write_jsonl(self.claude_file(".claude", "s1"), [
            {"type": "user", "cwd": self.repo_path, "timestamp": at(9), "message": {"content": "Run the tests"}},
            {"type": "assistant", "timestamp": at(9), "message": {**reply, "content": [{"type": "thinking"}]}},
            {"type": "assistant", "timestamp": at(9), "message": {**reply, "content": [
                {"type": "tool_use", "id": "t1", "name": "Bash", "input": {"command": E2E_COMMAND}}]}},
        ])

        # When the range is collected
        session = self.collect()[0]

        # Then the reply's tokens count once
        self.assertEqual(session["tokens"]["out_tok"], OUTPUT_TOKENS)

    def test_a_folder_that_is_not_a_git_repository_is_rejected(self):
        # Given a session in a folder outside any Git repository, and that folder passed as the repository
        outside = self.tmp / "outside"
        outside.mkdir()
        write_jsonl(self.claude_file(".claude", "s1"), claude_turn(str(outside), at(9), at(9, 5), at(9, 6)))

        # When the range is collected
        # Then it fails and names the path instead of collecting the unrelated session
        with self.assertRaisesRegex(ValueError, "is not a Git repository"):
            digest.collect(os.path.realpath(outside), DAY_START, DAY_END)

    def test_session_in_a_worktree_outside_the_repository_folder_is_included(self):
        # Given a worktree created outside the repository folder, and a session that ran in it
        subprocess.run(["git", "-C", self.repo_path, "commit", "-q", "--allow-empty", "-m", "init"], check=True,
                       env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"})
        worktree = self.tmp / "worktree"
        subprocess.run(["git", "-C", self.repo_path, "worktree", "add", "-q", str(worktree)], check=True)
        write_jsonl(self.claude_file(".claude", "s1"), claude_turn(os.path.realpath(worktree), at(9), at(9, 5), at(9, 6)))

        # When the range is collected
        sessions = self.collect()

        # Then the session is reported
        self.assertEqual(len(sessions), 1)

    def test_claude_subagent_that_ran_after_its_parent_went_quiet_is_kept(self):
        # Given a parent session with no events in the range, and its subagent that worked in the range
        parent = self.claude_file(".claude", "s1")
        before_range = (DAY_START - timedelta(hours=1)).isoformat()
        write_jsonl(parent, claude_turn(self.repo_path, before_range, before_range, before_range))
        child = parent.with_suffix("") / "subagents" / "agent-1.jsonl"
        write_jsonl(child, claude_turn(self.repo_path, at(1), at(1, 5), at(1, 6)))
        child.with_suffix(".meta.json").write_text(json.dumps({"agentType": "fixer"}))

        # When the range is collected
        sessions = self.collect()

        # Then the subagent's work is reported under a placeholder for its parent
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0]["subagents"]["count"], 1)
        self.assertEqual(sessions[0]["subagents"]["by_type"], {"fixer": 1})
        self.assertEqual(sessions[0]["subagents"]["cmd_kinds"]["e2e"]["n"], 1)

    def test_codex_subagent_is_folded_into_its_parent_session(self):
        # Given a Codex session and a subagent it spawned, both running a failing E2E command
        write_jsonl(self.codex_file("parent"), codex_session(self.repo_path, CODEX_SESSION_ID))
        write_jsonl(self.codex_file("child"), codex_session(self.repo_path, "child", parent=CODEX_SESSION_ID))

        # When the range is collected
        sessions = self.collect()

        # Then one session is reported, with the subagent's work under it
        self.assertEqual(len(sessions), 1)
        session = sessions[0]
        self.assertEqual(session["agent"], "codex")
        self.assertEqual(session["cmd_kinds"]["e2e"]["n"], 1)
        self.assertEqual(sum(n for _, n in session["repeated_errors"]), 1)
        self.assertEqual(session["subagents"]["count"], 1)
        self.assertEqual(session["subagents"]["by_type"], {"reviewer": 1})


class WindowTest(unittest.TestCase):
    NOW = datetime(2026, 1, 2, 7, 30).astimezone()

    def test_no_range_means_the_last_24_hours(self):
        # Given no --since or --until
        # When the range is resolved
        start, end = digest.window(None, None, self.NOW)

        # Then it ends now and starts 24 hours earlier
        self.assertEqual((start, end), (self.NOW - timedelta(hours=24), self.NOW))

    def test_dates_without_a_time_mean_local_midnight(self):
        # Given a range written as two dates
        # When the range is resolved
        start, end = digest.window("2026-01-01", "2026-01-02", self.NOW)

        # Then both ends are local midnight
        self.assertEqual((start, end), (DAY_START, DAY_END))

    def test_since_alone_runs_until_now(self):
        # Given only --since
        # When the range is resolved
        start, end = digest.window("2026-01-01", None, self.NOW)

        # Then the range ends now
        self.assertEqual((start, end), (DAY_START, self.NOW))

    def test_a_time_that_is_not_iso_8601_names_its_flag(self):
        # Given --since written in words
        # When the range is resolved
        # Then it fails and names the flag and an accepted format
        with self.assertRaisesRegex(ValueError, r"--since 'yesterday' is not ISO 8601; use a value such as 2026-11-09"):
            digest.window("yesterday", None, self.NOW)

    def test_a_range_that_ends_before_it_starts_is_rejected(self):
        # Given --since after --until
        # When the range is resolved
        # Then it fails and names both ends
        with self.assertRaisesRegex(ValueError, "is not before"):
            digest.window("2026-01-02", "2026-01-01", self.NOW)


if __name__ == "__main__":
    unittest.main()
