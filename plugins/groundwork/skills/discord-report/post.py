#!/usr/bin/env python3
"""Post work reports to threads in a Discord channel.

Usage:
  post.py --check
  post.py --create-channel --guild ID [--name NAME]
  post.py --kind waiting|done --title TEXT --body FILE [--owner TEXT]
  post.py --answer --thread ID --body FILE
  post.py --close --thread ID

Every report opens its own thread: a short starter message in the channel,
a thread on it, then the body inside the thread.
Settings: channel_id and guild_id in DISCORD_INFO.md at the Git root; a linked
worktree without one uses the main checkout's.
"""
import argparse
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

API = "https://discord.com/api/v10"
# Discord's edge rejects requests without a bot-style User-Agent.
USER_AGENT = "DiscordBot (https://github.com/enebin/groundwork, 1)"
TOKEN_OVERRIDE_PATH = Path.home() / ".config" / "discord-report" / "token"
CHANNEL_PLUGIN_ENV_PATH = Path.home() / ".claude" / "channels" / "discord" / ".env"
MAX_MESSAGE_CHARS = 2000
MAX_THREAD_NAME_CHARS = 100
TEXT_CHANNEL = 0
STARTER_LABELS = {"waiting": "⏳ Waiting", "done": "✅ Done"}


class DiscordError(Exception):
    pass


def request(method, path, token, payload=None):
    req = urllib.request.Request(
        f"{API}{path}",
        method=method,
        data=None if payload is None else json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bot {token}",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as res:
            body = res.read()
    except urllib.error.HTTPError as error:
        detail = error.read().decode(errors="replace")
        try:
            detail = json.loads(detail).get("message", detail)
        except ValueError:
            pass
        raise DiscordError(f"{method} {path} failed: {error.code} {detail}") from None
    except urllib.error.URLError as error:
        raise DiscordError(f"{method} {path} failed: {error.reason}") from None
    return json.loads(body) if body else None


def load_token():
    if TOKEN_OVERRIDE_PATH.exists() and TOKEN_OVERRIDE_PATH.read_text().strip():
        return TOKEN_OVERRIDE_PATH.read_text().strip()
    if CHANNEL_PLUGIN_ENV_PATH.exists():
        found = re.search(r"^DISCORD_BOT_TOKEN=[ \t]*['\"]?([^'\"\s]+)", CHANNEL_PLUGIN_ENV_PATH.read_text(), re.M)
        if found:
            return found.group(1)
    sys.exit(
        f"Discord bot token missing. Put DISCORD_BOT_TOKEN in {CHANNEL_PLUGIN_ENV_PATH} "
        f"or the token alone in {TOKEN_OVERRIDE_PATH}; see references/setup.md."
    )


def git(*args):
    res = subprocess.run(["git", *args], capture_output=True, text=True)
    return res.stdout.strip() if res.returncode == 0 else None


def main_checkout():
    # The shared .git dir, not the toplevel: a linked worktree's toplevel is its own folder.
    common = git("rev-parse", "--path-format=absolute", "--git-common-dir")
    if common is None:
        sys.exit("not inside a git repository")
    return Path(common).parent


def repo_name():
    return main_checkout().name


def channel_name(repo):
    return re.sub(r"[^a-z0-9_-]+", "-", repo.lower()).strip("-")[:100]


def settings_files():
    """The current worktree's DISCORD_INFO.md first, then the main checkout's."""
    root = git("rev-parse", "--show-toplevel")
    if root is None:
        sys.exit("not inside a git repository")
    files = [Path(root) / "DISCORD_INFO.md"]
    main = main_checkout() / "DISCORD_INFO.md"
    if main != files[0]:
        files.append(main)
    return files


def load_settings():
    for info in settings_files():
        if info.exists():
            return dict(re.findall(r"^(channel_id|guild_id):[ \t]*(\d+)[ \t]*$", info.read_text(), re.M))
    return {}


def require_settings():
    settings = load_settings()
    if not settings.get("channel_id") or not settings.get("guild_id"):
        places = " or ".join(str(info) for info in settings_files())
        sys.exit(
            f"Save channel_id and guild_id in DISCORD_INFO.md before posting; looked in {places}. "
            "Run setup, or commit DISCORD_INFO.md to the branch new worktrees start from."
        )
    return settings


def verify_channel(token, settings):
    channel = request("GET", f"/channels/{settings['channel_id']}", token)
    if channel.get("guild_id") != settings["guild_id"]:
        sys.exit("The report channel is not in the configured server; check DISCORD_INFO.md and the bot token.")
    return channel


def verify_thread(token, settings, thread_id):
    """Refuse any thread outside the report channel, so --close never deletes elsewhere."""
    thread = request("GET", f"/channels/{thread_id}", token)
    if thread.get("guild_id") != settings["guild_id"] or thread.get("parent_id") != settings["channel_id"]:
        sys.exit(f"Thread {thread_id} is not in the configured report channel; nothing was changed.")
    return thread


def split_message(text, first_limit=MAX_MESSAGE_CHARS):
    """Split at line breaks into messages under Discord's cap; hard-split only overlong lines."""
    chunks, current, limit = [], "", first_limit
    for line in text.strip().split("\n"):
        while len(line) > limit:
            if current:
                chunks.append(current)
                current, limit = "", MAX_MESSAGE_CHARS
            chunks.append(line[:limit])
            line = line[limit:]
            limit = MAX_MESSAGE_CHARS
        candidate = f"{current}\n{line}" if current else line
        if len(candidate) > limit:
            chunks.append(current)
            current, limit = line, MAX_MESSAGE_CHARS
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def send(token, channel_id, content):
    # Report text must never ping @everyone, roles, or users.
    return request("POST", f"/channels/{channel_id}/messages", token, {"content": content, "allowed_mentions": {"parse": []}})


def post_chunks(token, thread_id, link, chunks):
    for index, chunk in enumerate(chunks):
        try:
            send(token, thread_id, chunk)
        except DiscordError as error:
            sys.exit(f"{error}\nPartial delivery: {index} of {len(chunks)} messages posted in {link}. Ask before retrying.")


def read_body(path):
    body = Path(path).read_text().strip()
    if not body:
        sys.exit("Report body is empty; write the report before posting.")
    return body


def thread_link(guild_id, thread_id):
    return f"https://discord.com/channels/{guild_id}/{thread_id}"


def check(token):
    bot = request("GET", "/users/@me", token)
    guilds = request("GET", "/users/@me/guilds", token)
    result = {"bot": bot.get("username"), "guilds": [{"id": g["id"], "name": g["name"]} for g in guilds]}
    settings = load_settings()
    if settings.get("channel_id"):
        channel = request("GET", f"/channels/{settings['channel_id']}", token)
        result["channel"] = {"id": channel["id"], "name": channel.get("name"), "guild_id": channel.get("guild_id")}
        result["guild_matches"] = channel.get("guild_id") == settings.get("guild_id")
    print(json.dumps(result, ensure_ascii=False))


def create_channel(token, guild_id, name):
    guild = request("GET", f"/guilds/{guild_id}", token)
    for channel in request("GET", f"/guilds/{guild_id}/channels", token):
        if channel.get("type") == TEXT_CHANNEL and channel.get("name") == name:
            created = False
            break
    else:
        channel = request("POST", f"/guilds/{guild_id}/channels", token, {"name": name, "type": TEXT_CHANNEL})
        created = True
    print(json.dumps({"guild": guild.get("name"), "guild_id": guild_id, "channel": channel["name"], "channel_id": channel["id"], "created": created}, ensure_ascii=False))


def open_report(token, settings, kind, title, body, owner):
    verify_channel(token, settings)
    channel_id, guild_id = settings["channel_id"], settings["guild_id"]
    suffix = f"\nowner: {owner}" if owner else ""
    chunks = split_message(body, MAX_MESSAGE_CHARS - len(suffix))
    chunks[0] += suffix
    starter = send(token, channel_id, f"{STARTER_LABELS[kind]}: {title}"[:MAX_MESSAGE_CHARS])
    try:
        thread = request(
            "POST",
            f"/channels/{channel_id}/messages/{starter['id']}/threads",
            token,
            {"name": title[:MAX_THREAD_NAME_CHARS]},
        )
    except DiscordError as error:
        sys.exit(f"{error}\nPartial delivery: starter message {starter['id']} was posted without a thread. Ask before retrying.")
    link = thread_link(guild_id, thread["id"])
    post_chunks(token, thread["id"], link, chunks)
    print(link)


def answer(token, settings, thread_id, body):
    verify_thread(token, settings, thread_id)
    link = thread_link(settings["guild_id"], thread_id)
    post_chunks(token, thread_id, link, split_message(body))
    print(link)


def close(token, settings, thread_id):
    verify_thread(token, settings, thread_id)
    request("DELETE", f"/channels/{thread_id}", token)
    # A thread opened from a message shares that starter message's id.
    try:
        request("DELETE", f"/channels/{settings['channel_id']}/messages/{thread_id}", token)
    except DiscordError as error:
        sys.exit(f"{error}\nThread {thread_id} was deleted, but its starter message is still in the channel.")
    print(f"deleted thread {thread_id} and its starter message")


def main():
    ap = argparse.ArgumentParser()
    action = ap.add_mutually_exclusive_group(required=True)
    action.add_argument("--check", action="store_true")
    action.add_argument("--create-channel", action="store_true")
    action.add_argument("--kind", choices=sorted(STARTER_LABELS))
    action.add_argument("--answer", action="store_true")
    action.add_argument("--close", action="store_true")
    ap.add_argument("--guild")
    ap.add_argument("--name")
    ap.add_argument("--title")
    ap.add_argument("--body")
    ap.add_argument("--owner")
    ap.add_argument("--thread")
    args = ap.parse_args()

    if args.create_channel and not args.guild:
        ap.error("--create-channel needs --guild")
    if args.kind and (not args.title or not args.body):
        ap.error("--kind needs --title and --body")
    if args.answer and (not args.thread or not args.body):
        ap.error("--answer needs --thread and --body")
    if args.close and not args.thread:
        ap.error("--close needs --thread")

    token = load_token()
    try:
        if args.check:
            check(token)
        elif args.create_channel:
            create_channel(token, args.guild, args.name or channel_name(repo_name()))
        elif args.kind:
            open_report(token, require_settings(), args.kind, args.title, read_body(args.body), args.owner)
        elif args.answer:
            answer(token, require_settings(), args.thread, read_body(args.body))
        else:
            close(token, require_settings(), args.thread)
    except DiscordError as error:
        sys.exit(str(error))


if __name__ == "__main__":
    main()
