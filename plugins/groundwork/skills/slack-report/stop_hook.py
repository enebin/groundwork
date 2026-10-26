#!/usr/bin/env python3
"""Turn-end hook for Claude Code and Codex (Stop).

When the repository's SLACK_INFO.md says `auto_report: true` and the working
tree changed since the last report, ask the agent to post one. Never fails the
agent's turn: any problem exits 0 silently.
"""
import json
import os
import re
import sys
from pathlib import Path

import post

def main():
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return
    # A turn the hook already continued must be allowed to end, or a failed post would loop.
    if not isinstance(event, dict) or event.get("stop_hook_active"):
        return
    os.chdir(event.get("cwd") or os.getcwd())
    root = post.git("rev-parse", "--show-toplevel")
    if root is None:
        return
    info = Path(root) / "SLACK_INFO.md"
    if not info.exists() or not re.search(r"^auto_report:[ \t]*true[ \t]*$", info.read_text(), re.M):
        return
    state = post.state_path()
    if state.exists() and state.read_text() == post.fingerprint():
        return
    print(json.dumps({
        "decision": "block",
        "reason": (
            "Slack report needed: the repository changed during this turn. "
            "Run the installed groundwork:slack-report skill and follow its "
            "Posting section now, then end your turn."
        ),
    }))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
