#!/usr/bin/env python3
"""Post a work report to a personal Slack workspace.

Usage: post.py --title TEXT --body FILE [--channel NAME]

Channel: --channel, or the current git repository's folder name.
Thread: one per git branch. The first report on a branch creates a parent
message (a PR status icon, the linked PR number once a PR exists, and the
first report's title); every report is one reply in that thread.
On develop/main (or detached HEAD) each report is its own thread instead:
parent = title, one reply per `---`-separated section of the body.
Thread ids are kept in ~/.config/slack-report/threads/, scoped to the
confirmed workspace, repository name, and destination channel.
After a report, the working tree fingerprint is saved so stop_hook.py knows
the repository has not changed since.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "slack-report"
TOKEN_PATH = CONFIG_DIR / "token"
USER_ID_PATH = CONFIG_DIR / "user_id"
THREADS_DIR = CONFIG_DIR / "threads"
STATE_DIR = CONFIG_DIR / "state"
TRUNK_BRANCHES = {"develop", "main", "master"}
MAX_REPLY_CHARS = 3500


def call(method, token, **params):
    req = urllib.request.Request(
        f"https://slack.com/api/{method}",
        data=json.dumps(params).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as res:
        return json.load(res)


def git(*args):
    res = subprocess.run(["git", *args], capture_output=True, text=True)
    return res.stdout.strip() if res.returncode == 0 else None


def fingerprint():
    """Hash of HEAD, tracked changes, and untracked file contents."""
    h = hashlib.sha256()
    root = Path(git("rev-parse", "--show-toplevel"))
    for part in (git("-C", str(root), "rev-parse", "HEAD"), git("-C", str(root), "status", "--porcelain"), git("-C", str(root), "diff", "HEAD")):
        h.update((part or "").encode())
    names = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-o", "--exclude-standard", "-z"],
        capture_output=True,
        check=True,
    ).stdout
    for name in filter(None, names.split(b"\0")):
        try:
            h.update(name + (root / os.fsdecode(name)).read_bytes())
        except OSError:
            pass
    return h.hexdigest()


def state_path():
    root = git("rev-parse", "--show-toplevel")
    return STATE_DIR / hashlib.sha256(root.encode()).hexdigest()[:16]


def repo_name():
    # The shared .git dir, not the toplevel: a worktree's toplevel is named after its branch.
    common = git("rev-parse", "--path-format=absolute", "--git-common-dir")
    if common is None:
        sys.exit("not inside a git repository")
    return Path(common).parent.name


def channel_name(repo):
    return re.sub(r"[^a-z0-9_-]+", "-", repo.lower()).strip("-")[:80]


def invite_owner(token, channel_id):
    """Invite the workspace owner so a freshly created channel shows up in their sidebar."""
    if not USER_ID_PATH.exists():
        print(f"warning: {USER_ID_PATH} missing; join the channel manually", file=sys.stderr)
        return
    res = call("conversations.invite", token, channel=channel_id, users=USER_ID_PATH.read_text().strip())
    if not res["ok"] and res["error"] != "already_in_channel":
        print(f"warning: invite failed: {res['error']}", file=sys.stderr)


def ensure_channel(token, name):
    created = call("conversations.create", token, name=name)
    if created["ok"]:
        invite_owner(token, created["channel"]["id"])
    elif created["error"] != "name_taken":
        sys.exit(f"conversations.create failed: {created['error']}")


def post(token, channel, text, thread_ts=None):
    params = {"channel": channel, "text": text}
    if thread_ts:
        params["thread_ts"] = thread_ts
    res = call("chat.postMessage", token, **params)
    if not res["ok"]:
        hint = ""
        if res["error"] == "not_in_channel":
            bot = call("auth.test", token).get("user", "the bot")
            hint = f" (run `/invite @{bot}` in {channel})"
        sys.exit(f"chat.postMessage failed: {res['error']}{hint}")
    return res


def split_sections(body):
    return [s.strip() for s in body.split("\n---\n") if s.strip()]


def chunk_report(title, body):
    """One reply per report; split on section breaks only when too long."""
    stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    whole = f"*{title}* · {stamp}\n\n" + "\n\n".join(split_sections(body))
    if len(whole) <= MAX_REPLY_CHARS:
        return [whole]
    chunks = [f"*{title}* · {stamp}"]
    for section in split_sections(body):
        chunks.extend(section[start:start + MAX_REPLY_CHARS] for start in range(0, len(section), MAX_REPLY_CHARS))
    return chunks


def load_threads(repo):
    path = THREADS_DIR / f"{hashlib.sha256(repo.encode()).hexdigest()}.json"
    return path, (json.loads(path.read_text()) if path.exists() else {})


PR_ICONS = {"draft": "[draft]", "open": "[open]", "merged": "[merged]", "closed": "[closed]"}


def current_pr(branch=None):
    """The PR of `branch` (default: the current branch) as {number, url, status}, or None."""
    target = [branch] if branch else []
    try:
        res = subprocess.run(
            ["gh", "pr", "view", *target, "--json", "number,url,state,isDraft"],
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if res.returncode != 0:
        return None
    pr = json.loads(res.stdout)
    status = "draft" if pr["isDraft"] else pr["state"].lower()
    return {"number": pr["number"], "url": pr["url"], "status": status}


def parent_text(title, pr):
    # No PR yet counts as a draft.
    if pr is None:
        return f"{PR_ICONS['draft']} {title}"
    return f"{PR_ICONS[pr['status']]} <{pr['url']}|#{pr['number']}> {title}"


def sync_parent(token, entry, pr):
    """Rewrite the thread's parent when its PR number or status changed."""
    if "title" not in entry:
        return
    text = parent_text(entry["title"], pr)
    if entry.get("parent_text") == text:
        return
    res = call("chat.update", token, channel=entry["channel"], ts=entry["ts"], text=text)
    if res["ok"]:
        entry["parent_text"] = text
    else:
        print(f"warning: chat.update failed: {res['error']}", file=sys.stderr)


def sync_other_threads(token, repo, current_branch):
    """Refresh every unfinished thread's parent, not just the current branch's.

    A branch is usually deleted right after its PR merges, so no later report
    lands in its thread and its icon would stay "open" for good.
    """
    path, threads = load_threads(repo)
    done = (PR_ICONS["merged"], PR_ICONS["closed"])
    for branch, entry in threads.items():
        if branch == current_branch or (entry.get("parent_text") or "").startswith(done):
            continue
        pr = current_pr(branch)
        if pr:
            sync_parent(token, entry, pr)
    if threads:
        path.write_text(json.dumps(threads, indent=2, ensure_ascii=False))


def post_branch_report(token, channel, repo, branch, title, body):
    path, threads = load_threads(repo)
    entry = threads.get(branch)
    pr = current_pr()
    if entry is None:
        text = parent_text(title, pr)
        parent = post(token, f"#{channel}", text)
        invite_owner(token, parent["channel"])
        entry = {"channel": parent["channel"], "ts": parent["ts"], "title": title, "parent_text": text}
        threads[branch] = entry
    else:
        sync_parent(token, entry, pr)
    THREADS_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(threads, indent=2, ensure_ascii=False))
    for text in chunk_report(title, body):
        post(token, entry["channel"], text, thread_ts=entry["ts"])
    return entry["channel"], entry["ts"]


def post_standalone_report(token, channel, title, body):
    parent = post(token, f"#{channel}", title)
    invite_owner(token, parent["channel"])
    for section in split_sections(body):
        post(token, parent["channel"], section, thread_ts=parent["ts"])
    return parent["channel"], parent["ts"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--channel")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--title")
    ap.add_argument("--body")
    args = ap.parse_args()

    if not args.check and (not args.title or not args.body):
        ap.error("--title and --body are required when posting")
    if not TOKEN_PATH.exists() or not TOKEN_PATH.read_text().strip():
        sys.exit(f"Slack token missing. Configure {TOKEN_PATH} locally; see references/setup.md.")
    token = TOKEN_PATH.read_text().strip()
    identity = call("auth.test", token)
    if not identity.get("ok"):
        sys.exit(f"Slack authentication failed: {identity.get('error', 'unknown_error')}")
    if args.check:
        print(json.dumps({key: identity.get(key) for key in ("team", "team_id", "user")}))
        return
    repo = repo_name()
    root = Path(git("rev-parse", "--show-toplevel"))
    info = root / "SLACK_INFO.md"
    settings = dict(re.findall(r"^(channel|workspace_id):[ \t]*(\S+)[ \t]*$", info.read_text(), re.M)) if info.exists() else {}
    if not settings.get("workspace_id"):
        sys.exit("Confirm the Slack workspace with --check and save workspace_id in SLACK_INFO.md before posting.")
    if settings["workspace_id"] != identity.get("team_id"):
        sys.exit("Configured Slack workspace does not match the token; check SLACK_INFO.md and local credentials.")
    channel = (args.channel or settings.get("channel") or channel_name(repo)).lstrip("#")
    body = Path(args.body).read_text()
    if not split_sections(body):
        sys.exit("Report body is empty; write the report before posting.")
    branch = git("symbolic-ref", "--short", "-q", "HEAD")
    observed = fingerprint()
    thread_key = f"{identity['team_id']}-{repo}-{channel}"

    ensure_channel(token, channel)
    if branch and branch not in TRUNK_BRANCHES:
        channel_id, ts = post_branch_report(token, channel, thread_key, branch, args.title, body)
    else:
        channel_id, ts = post_standalone_report(token, channel, args.title, body)

    sync_other_threads(token, thread_key, branch)

    link = call("chat.getPermalink", token, channel=channel_id, message_ts=ts)
    print(link.get("permalink", f"posted to #{channel} (ts {ts})"))
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state_path().write_text(observed)


if __name__ == "__main__":
    main()
