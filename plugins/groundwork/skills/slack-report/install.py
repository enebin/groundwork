#!/usr/bin/env python3
"""Install repository-local Slack report hooks for Claude Code and Codex."""
import json
import shutil
import sys
from pathlib import Path

import post

MARKER = "slack-report/stop_hook.py"
COMMAND = (
    'common=$(git rev-parse --path-format=absolute --git-common-dir 2>/dev/null) || exit 0; '
    'f="$(dirname "$common")/.groundwork/slack-report/stop_hook.py"; '
    '[ ! -f "$f" ] || exec python3 "$f"'
)
INSTRUCTION = (
    "- Slack reports (SLACK_INFO.md): when an opted-in turn-end hook requests "
    "a report, run the `groundwork:slack-report` skill before ending the turn."
)
BEGIN = "<!-- groundwork:begin slack-report -->"
END = "<!-- groundwork:end slack-report -->"
TARGETS = (".claude/settings.json", ".codex/hooks.json")


def install_hook(root, rel):
    path = root / rel
    config = json.loads(path.read_text()) if path.exists() else {}
    groups = config.setdefault("hooks", {}).setdefault("Stop", [])
    hook = {"type": "command", "command": COMMAND, "timeout": 30}
    found = False
    changed = False
    for group in groups:
        for index, existing in enumerate(group.get("hooks", [])):
            if MARKER in existing.get("command", ""):
                found = True
                if existing != hook:
                    group["hooks"][index] = hook.copy()
                    changed = True
    if not found:
        groups.append({"hooks": [hook]})
        changed = True
    if changed:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n")
    return changed


def install_instruction(root, name):
    path = root / name
    text = path.read_text() if path.exists() else ""
    block = f"{BEGIN}\n{INSTRUCTION}\n{END}"
    if BEGIN in text:
        start = text.index(BEGIN)
        end = text.index(END, start) + len(END)
        updated = text[:start] + block + text[end:]
    else:
        updated = text.rstrip("\n") + ("\n\n" if text else "") + block + "\n"
    if updated == text:
        return False
    path.write_text(updated)
    return True


def install_runtime(root):
    source = Path(__file__).resolve().parent
    runtime = root / ".groundwork/slack-report"
    runtime.mkdir(parents=True, exist_ok=True)
    ignore = runtime / ".gitignore"
    if not ignore.exists():
        ignore.write_text("*\n")
    names = ("post.py", "stop_hook.py", "references/setup.md")
    for name in names:
        origin, target = source / name, runtime / name
        if origin.resolve() != target.resolve():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(origin, target)


def main():
    root_str = post.git("rev-parse", "--show-toplevel")
    if root_str is None:
        sys.exit("Not inside a Git repository; run this from the target repository.")
    root = Path(root_str)
    for rel in TARGETS:
        path = root / rel
        if path.exists():
            json.loads(path.read_text())
    for name in ("CLAUDE.md", "AGENTS.md"):
        path = root / name
        if path.exists():
            text = path.read_text()
            if (BEGIN in text) != (END in text):
                sys.exit(f"Incomplete Slack report markers in {name}; repair them before installing.")
    common = post.git("rev-parse", "--path-format=absolute", "--git-common-dir")
    if common is None:
        sys.exit("Cannot find the shared Git directory; check the repository before installing.")
    install_runtime(Path(common).parent)
    changed = [rel for rel in TARGETS if install_hook(root, rel)]
    changed += [name for name in ("CLAUDE.md", "AGENTS.md") if install_instruction(root, name)]
    print("changed: " + ", ".join(changed) if changed else "hooks already installed; runtime refreshed")


if __name__ == "__main__":
    main()
