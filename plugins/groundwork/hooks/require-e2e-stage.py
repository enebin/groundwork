#!/usr/bin/env python3
import json
import re
import subprocess
import sys
from pathlib import Path

STAGES = ("review", "checkpoint", "release", "screenshot")
STAGE_PATTERN = re.compile(r"(?:^|[\s;&|(])E2E_STAGE=(%s)(?![\w-])" % "|".join(STAGES))

BLOCK_MESSAGE = """The e2e-stage add-on is on, and this command runs a UI test command from verification.ui_tests in GROUNDWORK.md. Put the current stage in front of it, such as `E2E_STAGE=screenshot <command>`.
- screenshot: the targeted tests for screens you changed, during implementation or fixes
- review: the full suite once before the first review (every round in sport), UI tests during rendered QA, or re-verification after a rebase
- checkpoint: a run on the integration branch after several merges
- release: pre-release checks
When no stage fits, do not run the suite. Reuse an earlier result from the same build instead."""


def repo_root(cwd):
    result = subprocess.run(
        ["git", "-C", cwd, "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
    )
    return Path(result.stdout.strip() if result.returncode == 0 else cwd)


def frontmatter(groundwork_md):
    lines = groundwork_md.splitlines()
    if not lines or lines[0].strip() != "---":
        return []
    body = []
    for line in lines[1:]:
        if line.strip() == "---":
            break
        body.append(line.split(" #")[0].rstrip())
    return body


def block(lines, key):
    for index, line in enumerate(lines):
        if line.strip().startswith(key + ":"):
            indent = len(line) - len(line.lstrip())
            nested = [line.split(":", 1)[1]]
            for child in lines[index + 1:]:
                if child.strip() and len(child) - len(child.lstrip()) <= indent:
                    break
                nested.append(child)
            return nested
    return []


def stage_addon_on(lines):
    addons = " ".join(block(block(lines, "verification"), "addons"))
    return "e2e-stage" in re.findall(r"[\w-]+", addons)


def ui_test_commands(lines):
    commands = []
    for line in block(block(lines, "verification"), "ui_tests"):
        match = re.match(r"\s*(targeted|full):\s*(.*)$", line)
        if not match:
            continue
        prefix = match.group(2).strip().strip("\"'").split("{test}")[0].strip()
        if prefix and prefix != "null" and not prefix.startswith("<"):
            commands.append(" ".join(prefix.split()))
    return commands


def main():
    payload = json.load(sys.stdin)
    command = payload.get("tool_input", {}).get("command", "")
    if isinstance(command, list):
        command = " ".join(command)
    if not command:
        return 0
    groundwork = repo_root(payload.get("cwd") or ".") / "GROUNDWORK.md"
    if not groundwork.is_file():
        return 0
    lines = frontmatter(groundwork.read_text())
    if not stage_addon_on(lines):
        return 0
    flat = " ".join(command.split())
    if not any(ui in flat for ui in ui_test_commands(lines)):
        return 0
    if STAGE_PATTERN.search(command):
        return 0
    print(BLOCK_MESSAGE, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
