"""Behavior checks use temporary files and a fake Discord API boundary."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
import urllib.error
from unittest.mock import patch

SKILL = Path(__file__).resolve().parents[1] / "plugins/groundwork/skills/discord-report"
spec = importlib.util.spec_from_file_location("discord_post", SKILL / "post.py")
post = importlib.util.module_from_spec(spec)
spec.loader.exec_module(post)

TOKEN = "test-token-not-a-credential"
GUILD = "100"
OTHER_GUILD = "999"
CHANNEL = "200"
STARTER = "300"
TITLE = "Saved filters are ready"
LINK = f"https://discord.com/channels/{GUILD}/{STARTER}"


class FakeDiscord:
    """Answers requests by (method, path); records every call in order."""

    def __init__(self, routes):
        self.routes = routes
        self.calls = []

    def __call__(self, method, path, token, payload=None):
        assert token == TOKEN
        self.calls.append((method, path, payload))
        answer = self.routes.get((method, path))
        if isinstance(answer, Exception):
            raise answer
        if callable(answer):
            return answer(payload)
        return answer

    def writes(self):
        return [(method, path) for method, path, _ in self.calls if method != "GET"]

    def messages_to(self, channel_id):
        return [payload["content"] for method, path, payload in self.calls if (method, path) == ("POST", f"/channels/{channel_id}/messages")]


def report_routes(overrides=None):
    routes = {
        ("GET", f"/channels/{CHANNEL}"): {"id": CHANNEL, "name": "example", "guild_id": GUILD},
        ("POST", f"/channels/{CHANNEL}/messages"): {"id": STARTER},
        ("POST", f"/channels/{CHANNEL}/messages/{STARTER}/threads"): {"id": STARTER},
        ("POST", f"/channels/{STARTER}/messages"): {"id": "301"},
        ("GET", f"/channels/{STARTER}"): {"id": STARTER, "guild_id": GUILD, "parent_id": CHANNEL},
        ("DELETE", f"/channels/{STARTER}"): None,
        ("DELETE", f"/channels/{CHANNEL}/messages/{STARTER}"): None,
    }
    routes.update(overrides or {})
    return routes


class DiscordReportTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.token = self.root / "token"
        self.token.write_text(TOKEN)
        self.env = self.root / ".env"
        self.info = self.root / "DISCORD_INFO.md"
        self.info.write_text(f"# Discord reports\n\nchannel_id: {CHANNEL}\nguild_id: {GUILD}\n")
        self.body = self.root / "body.md"
        self.body.write_text("Added saved filters.\nTests passed.")
        context = contextlib.ExitStack()
        self.addCleanup(context.close)
        context.enter_context(patch.object(post, "TOKEN_OVERRIDE_PATH", self.token))
        context.enter_context(patch.object(post, "CHANNEL_PLUGIN_ENV_PATH", self.env))
        context.enter_context(patch.object(post, "git", side_effect=self.fake_git))

    def fake_git(self, *args):
        if args == ("rev-parse", "--show-toplevel"):
            return str(self.root)
        if args == ("rev-parse", "--path-format=absolute", "--git-common-dir"):
            return str(self.root / "My Repo" / ".git")
        raise AssertionError(f"Unexpected Git request: {args}")

    def run_helper(self, api, *argv):
        out, err = io.StringIO(), io.StringIO()
        code = 0
        with patch.object(post, "request", api), patch.object(sys, "argv", ["post.py", *argv]):
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                try:
                    post.main()
                except SystemExit as exit:
                    code = exit.code if isinstance(exit.code, int) else 1
                    err.write(str(exit.code))
        return code, out.getvalue(), err.getvalue()

    def test_check_prints_bot_servers_and_channel_match_without_posting(self):
        # Given a configured channel in the saved server
        api = FakeDiscord(report_routes({
            ("GET", "/users/@me"): {"username": "reporter"},
            ("GET", "/users/@me/guilds"): [{"id": GUILD, "name": "Team"}],
        }))
        # When checking the connection
        code, out, _ = self.run_helper(api, "--check")
        # Then it prints identities and writes nothing
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out), {
            "bot": "reporter",
            "guilds": [{"id": GUILD, "name": "Team"}],
            "channel": {"id": CHANNEL, "name": "example", "guild_id": GUILD},
            "guild_matches": True,
        })
        self.assertEqual(api.writes(), [])

    def test_check_before_setup_lists_servers_only(self):
        # Given no settings file yet
        self.info.unlink()
        api = FakeDiscord({("GET", "/users/@me"): {"username": "reporter"}, ("GET", "/users/@me/guilds"): []})
        # When checking
        code, out, _ = self.run_helper(api, "--check")
        # Then no channel is looked up
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out), {"bot": "reporter", "guilds": []})

    def test_token_falls_back_to_channel_plugin_env_file(self):
        # Given only the Discord channel plugin's env file
        self.token.unlink()
        self.env.write_text(f"OTHER=1\nDISCORD_BOT_TOKEN={TOKEN}\n")
        # When loading the token
        # Then the plugin's token is used
        self.assertEqual(post.load_token(), TOKEN)

    def test_missing_token_names_both_files(self):
        # Given no token anywhere
        self.token.unlink()
        # When posting
        code, _, err = self.run_helper(FakeDiscord({}), "--check")
        # Then the error names where to put it
        self.assertEqual(code, 1)
        self.assertIn(str(self.env), err)
        self.assertIn(str(self.token), err)

    def test_create_channel_creates_text_channel_named_after_repository(self):
        # Given a server without the channel
        api = FakeDiscord({
            ("GET", f"/guilds/{GUILD}"): {"name": "Team"},
            ("GET", f"/guilds/{GUILD}/channels"): [{"id": "1", "name": "general", "type": 0}],
            ("POST", f"/guilds/{GUILD}/channels"): lambda payload: {"id": CHANNEL, "name": payload["name"]},
        })
        # When creating the report channel
        code, out, _ = self.run_helper(api, "--create-channel", "--guild", GUILD)
        # Then a text channel named after the repository folder is created
        self.assertEqual(code, 0)
        self.assertEqual(api.calls[-1], ("POST", f"/guilds/{GUILD}/channels", {"name": "my-repo", "type": 0}))
        self.assertEqual(json.loads(out)["channel_id"], CHANNEL)
        self.assertTrue(json.loads(out)["created"])

    def test_create_channel_reuses_existing_text_channel(self):
        # Given a text channel with the same name
        api = FakeDiscord({
            ("GET", f"/guilds/{GUILD}"): {"name": "Team"},
            ("GET", f"/guilds/{GUILD}/channels"): [{"id": CHANNEL, "name": "reports", "type": 0}],
        })
        # When creating it again
        code, out, _ = self.run_helper(api, "--create-channel", "--guild", GUILD, "--name", "reports")
        # Then nothing is created
        self.assertEqual(code, 0)
        self.assertEqual(api.writes(), [])
        self.assertFalse(json.loads(out)["created"])

    def test_waiting_report_opens_thread_and_ends_first_message_with_owner(self):
        # Given a configured channel
        api = FakeDiscord(report_routes())
        # When posting a waiting report with an owner
        code, out, _ = self.run_helper(api, "--kind", "waiting", "--title", TITLE, "--body", str(self.body), "--owner", "/work/tree claude abc")
        # Then a starter, a thread, and the body with the owner line are posted in order
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), LINK)
        self.assertEqual(api.writes(), [
            ("POST", f"/channels/{CHANNEL}/messages"),
            ("POST", f"/channels/{CHANNEL}/messages/{STARTER}/threads"),
            ("POST", f"/channels/{STARTER}/messages"),
        ])
        self.assertEqual(api.messages_to(CHANNEL), [f"⏳ Waiting: {TITLE}"])
        self.assertEqual(api.messages_to(STARTER), ["⏳ Waiting\nAdded saved filters.\nTests passed.\nowner: /work/tree claude abc"])

    def test_done_report_marks_starter_thread_name_and_first_message_with_check_emoji(self):
        # Given a configured channel
        api = FakeDiscord(report_routes())
        # When posting a done report
        code, _, _ = self.run_helper(api, "--kind", "done", "--title", TITLE, "--body", str(self.body))
        # Then the starter, the thread name, and the first thread message all start with ✅
        self.assertEqual(code, 0)
        self.assertEqual(api.messages_to(CHANNEL), [f"✅ Done: {TITLE}"])
        thread_payload = next(payload for method, path, payload in api.calls if path.endswith("/threads"))
        self.assertEqual(thread_payload, {"name": f"✅ {TITLE}"})
        self.assertTrue(api.messages_to(STARTER)[0].startswith("✅ Done\n"))

    def test_body_opening_with_heading_keeps_heading_at_line_start(self):
        # Given a body that opens with a Markdown heading
        self.body.write_text("# Summary\nAdded saved filters.")
        api = FakeDiscord(report_routes())
        # When posting a done report
        self.run_helper(api, "--kind", "done", "--title", TITLE, "--body", str(self.body))
        # Then the heading still starts its own line
        self.assertEqual(api.messages_to(STARTER)[0].split("\n")[1], "# Summary")

    def test_first_message_with_emoji_and_owner_stays_under_cap(self):
        # Given a body exactly at the message cap and an owner line
        self.body.write_text("z" * post.MAX_MESSAGE_CHARS)
        api = FakeDiscord(report_routes())
        # When posting a waiting report
        code, _, _ = self.run_helper(api, "--kind", "waiting", "--title", TITLE, "--body", str(self.body), "--owner", "/work/tree claude abc")
        # Then every message fits and the first one keeps both the emoji and the owner line
        sent = api.messages_to(STARTER)
        self.assertEqual(code, 0)
        self.assertTrue(all(len(message) <= post.MAX_MESSAGE_CHARS for message in sent))
        self.assertTrue(sent[0].startswith("⏳ Waiting\n"))
        self.assertTrue(sent[0].endswith("\nowner: /work/tree claude abc"))

    def test_report_messages_never_ping(self):
        # Given a body that mentions everyone
        self.body.write_text("@everyone done")
        api = FakeDiscord(report_routes())
        # When posting
        self.run_helper(api, "--kind", "done", "--title", TITLE, "--body", str(self.body))
        # Then every message disables mentions
        posted = [payload for method, _, payload in api.calls if method == "POST" and "content" in (payload or {})]
        self.assertTrue(posted)
        self.assertTrue(all(payload["allowed_mentions"] == {"parse": []} for payload in posted))

    def test_long_report_is_split_under_discord_cap_at_line_breaks(self):
        # Given a body longer than one message
        lines = [f"line {index:04d} " + "x" * 90 for index in range(40)]
        self.body.write_text("\n".join(lines))
        api = FakeDiscord(report_routes())
        # When posting
        code, _, _ = self.run_helper(api, "--kind", "done", "--title", TITLE, "--body", str(self.body))
        # Then every message fits and no line is broken
        sent = api.messages_to(STARTER)
        self.assertEqual(code, 0)
        self.assertGreater(len(sent), 1)
        self.assertTrue(all(len(message) <= post.MAX_MESSAGE_CHARS for message in sent))
        self.assertEqual("\n".join(sent).removeprefix("✅ Done\n").split("\n"), lines)

    def test_overlong_line_is_hard_split(self):
        # Given one line longer than the cap
        line = "y" * (post.MAX_MESSAGE_CHARS * 2 + 5)
        # When splitting
        chunks = post.split_message(line)
        # Then it becomes capped pieces that rejoin to the line
        self.assertEqual([len(chunk) for chunk in chunks], [post.MAX_MESSAGE_CHARS, post.MAX_MESSAGE_CHARS, 5])
        self.assertEqual("".join(chunks), line)

    def test_post_refuses_channel_in_another_server(self):
        # Given the channel now belongs to another server
        api = FakeDiscord(report_routes({("GET", f"/channels/{CHANNEL}"): {"id": CHANNEL, "guild_id": OTHER_GUILD}}))
        # When posting
        code, _, err = self.run_helper(api, "--kind", "done", "--title", TITLE, "--body", str(self.body))
        # Then nothing is written
        self.assertEqual(code, 1)
        self.assertIn("not in the configured server", err)
        self.assertEqual(api.writes(), [])

    def test_post_without_settings_asks_for_setup(self):
        # Given no settings file
        self.info.unlink()
        api = FakeDiscord({})
        # When posting
        code, _, err = self.run_helper(api, "--kind", "done", "--title", TITLE, "--body", str(self.body))
        # Then it stops before calling Discord
        self.assertEqual(code, 1)
        self.assertIn("DISCORD_INFO.md", err)
        self.assertEqual(api.calls, [])

    def test_worktree_without_settings_uses_main_checkout_settings(self):
        # Given settings only in the main checkout, not in the linked worktree
        main = self.root / "My Repo"
        main.mkdir()
        self.info.rename(main / "DISCORD_INFO.md")
        api = FakeDiscord(report_routes())
        # When posting from the worktree
        code, out, _ = self.run_helper(api, "--kind", "waiting", "--title", TITLE, "--body", str(self.body))
        # Then the report goes to the main checkout's channel
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), LINK)
        self.assertEqual(api.writes()[0][1], f"/channels/{CHANNEL}/messages")

    def test_worktree_settings_win_over_main_checkout_settings(self):
        # Given the main checkout points at another channel
        main = self.root / "My Repo"
        main.mkdir()
        (main / "DISCORD_INFO.md").write_text("channel_id: 999\nguild_id: 888\n")
        api = FakeDiscord(report_routes())
        # When posting from a worktree with its own settings
        code, _, _ = self.run_helper(api, "--kind", "waiting", "--title", TITLE, "--body", str(self.body))
        # Then the worktree's channel is used
        self.assertEqual(code, 0)
        self.assertEqual(api.writes()[0][1], f"/channels/{CHANNEL}/messages")

    def test_missing_settings_error_names_worktree_and_main_checkout(self):
        # Given settings in neither the worktree nor the main checkout
        self.info.unlink()
        api = FakeDiscord({})
        # When posting
        code, _, err = self.run_helper(api, "--kind", "waiting", "--title", TITLE, "--body", str(self.body))
        # Then the error names both places and the recovery
        self.assertEqual(code, 1)
        self.assertIn(str(self.info), err)
        self.assertIn(str(self.root / "My Repo" / "DISCORD_INFO.md"), err)
        self.assertIn("commit DISCORD_INFO.md", err)
        self.assertEqual(api.calls, [])

    def test_empty_body_is_refused(self):
        # Given an empty body
        self.body.write_text("  \n")
        api = FakeDiscord(report_routes())
        # When posting
        code, _, err = self.run_helper(api, "--kind", "done", "--title", TITLE, "--body", str(self.body))
        # Then nothing is sent
        self.assertEqual(code, 1)
        self.assertIn("empty", err)
        self.assertEqual(api.calls, [])

    def test_thread_failure_reports_orphan_starter(self):
        # Given thread creation fails after the starter is posted
        failure = post.DiscordError("POST threads failed: 403 Missing Permissions")
        api = FakeDiscord(report_routes({("POST", f"/channels/{CHANNEL}/messages/{STARTER}/threads"): failure}))
        # When posting
        code, _, err = self.run_helper(api, "--kind", "waiting", "--title", TITLE, "--body", str(self.body))
        # Then the partial delivery names the starter message
        self.assertEqual(code, 1)
        self.assertIn(f"starter message {STARTER} was posted without a thread", err)

    def test_body_failure_reports_how_many_messages_were_posted(self):
        # Given the second body message fails
        responses = iter([{"id": "301"}, post.DiscordError("POST failed: 429 rate limited")])

        def flaky(payload):
            answer = next(responses)
            if isinstance(answer, Exception):
                raise answer
            return answer

        self.body.write_text("a" * post.MAX_MESSAGE_CHARS + "\nb")
        api = FakeDiscord(report_routes({("POST", f"/channels/{STARTER}/messages"): flaky}))
        # When posting
        code, _, err = self.run_helper(api, "--kind", "done", "--title", TITLE, "--body", str(self.body))
        # Then it reports partial delivery and does not retry
        self.assertEqual(code, 1)
        self.assertIn(f"1 of 2 messages posted in {LINK}", err)
        self.assertEqual(len([c for c in api.calls if c[1] == f"/channels/{STARTER}/messages"]), 2)

    def test_answer_posts_into_thread(self):
        # Given a thread in the report channel
        api = FakeDiscord(report_routes())
        # When answering
        code, out, _ = self.run_helper(api, "--answer", "--thread", STARTER, "--body", str(self.body))
        # Then the answer goes into that thread only
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), LINK)
        self.assertEqual(api.writes(), [("POST", f"/channels/{STARTER}/messages")])

    def test_close_deletes_thread_then_starter(self):
        # Given a waiting thread in the report channel
        api = FakeDiscord(report_routes())
        # When closing it
        code, _, _ = self.run_helper(api, "--close", "--thread", STARTER)
        # Then the thread and its starter message are deleted
        self.assertEqual(code, 0)
        self.assertEqual(api.writes(), [("DELETE", f"/channels/{STARTER}"), ("DELETE", f"/channels/{CHANNEL}/messages/{STARTER}")])

    def test_close_refuses_thread_outside_report_channel(self):
        # Given a thread whose parent is another channel
        api = FakeDiscord(report_routes({("GET", f"/channels/{STARTER}"): {"id": STARTER, "guild_id": GUILD, "parent_id": "777"}}))
        # When closing it
        code, _, err = self.run_helper(api, "--close", "--thread", STARTER)
        # Then nothing is deleted
        self.assertEqual(code, 1)
        self.assertIn("nothing was changed", err)
        self.assertEqual(api.writes(), [])

    def test_close_reports_starter_left_behind(self):
        # Given the starter delete fails after the thread delete
        failure = post.DiscordError("DELETE failed: 403 Missing Permissions")
        api = FakeDiscord(report_routes({("DELETE", f"/channels/{CHANNEL}/messages/{STARTER}"): failure}))
        # When closing
        code, _, err = self.run_helper(api, "--close", "--thread", STARTER)
        # Then it says the thread is gone but the starter remains
        self.assertEqual(code, 1)
        self.assertIn("starter message is still in the channel", err)


class RequestBoundaryTests(unittest.TestCase):
    def test_http_error_becomes_discord_error_with_status_and_message(self):
        # Given Discord rejects the request
        seen = []

        def reject(req, timeout):
            seen.append(req)
            raise urllib.error.HTTPError(req.full_url, 403, "Forbidden", {}, io.BytesIO(b'{"message": "Missing Permissions", "code": 50013}'))

        # When calling the API
        with patch.object(post.urllib.request, "urlopen", reject):
            with self.assertRaises(post.DiscordError) as raised:
                post.request("DELETE", f"/channels/{STARTER}", TOKEN)
        # Then the error names the call and Discord's reason, and the request identified itself as a bot
        self.assertEqual(str(raised.exception), f"DELETE /channels/{STARTER} failed: 403 Missing Permissions")
        self.assertEqual(seen[0].get_header("Authorization"), f"Bot {TOKEN}")
        self.assertTrue(seen[0].get_header("User-agent").startswith("DiscordBot "))


if __name__ == "__main__":
    unittest.main()
