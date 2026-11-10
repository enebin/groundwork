#!/usr/bin/env python3
import json
import re
import subprocess
import sys
from pathlib import Path

STAGES = ("review", "checkpoint", "release", "screenshot")
COMMAND_START = r"(?:^|[;&|(\n])\s*((?:[A-Za-z_]\w*=\S*\s+)*)"

BLOCK_MESSAGE = """The e2e-stage add-on in GROUNDWORK.md requires a stage in front of `{ui}`, such as `E2E_STAGE=screenshot {ui}`. Valid stages, case-sensitive:
- screenshot: the targeted tests for screens you changed, during implementation or fixes
- review: the full suite once before the first review (every round in sport), UI tests during rendered QA, or re-verification after a rebase
- checkpoint: a run on the integration branch after several merges
- release: pre-release checks
When no stage fits, do not run the suite. Reuse an earlier result from the same build instead. To turn this check off, remove e2e-stage from verification.addons."""


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
    ui_tests = block(block(lines, "verification"), "ui_tests")
    for index, line in enumerate(ui_tests):
        match = re.match(r"\s*(targeted|full):\s*(.*)$", line)
        if not match:
            continue
        value = match.group(2).strip()
        if value[:1] in ("|", ">"):
            value = " ".join(block(ui_tests[index:], match.group(1))[1:])
        prefix = value.strip("\"'").split("{test}")[0].strip()
        if prefix and prefix != "null" and not prefix.startswith("<"):
            commands.append(" ".join(prefix.split()))
    return commands


def unstaged_ui_command(command, ui_commands):
    for ui in ui_commands:
        pattern = COMMAND_START + r"\s+".join(map(re.escape, ui.split())) + r"(?![\w-])"
        for match in re.finditer(pattern, command):
            stages = re.findall(r"E2E_STAGE=(\S*)", match.group(1))
            if not any(stage in STAGES for stage in stages):
                return ui
    return None


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
    ui = unstaged_ui_command(command, ui_test_commands(lines))
    if ui is None:
        return 0
    print(BLOCK_MESSAGE.format(ui=ui), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
