---
name: "boarding"
description: Flight stage 1. Reads a tracker issue, writes down its requirements and the code it touches, and caches both on disk. Use for "board <id>", or as the first step before door-closing.
allowed-tools: Bash, Read, Write, Grep, Glob, Agent, AskUserQuestion, TodoWrite
argument-hint: <issue id> [--force]
---

Stage 1 of the Flight sequence. Read the issue, summarize what it asks for, and note which code it touches. No code changes, no git changes, no remote side effects.

## 0. Read the config

Read `reference/config.md` under the plugin root (two directories above this skill's directory), then `GROUNDWORK.md` at the repository root as it says. Stop if the file is missing or a key this skill needs is missing.

Talk to the user in `language.conversation`. Write the cached files in `language.artifacts`.

Every tracker action below is an operation from `reference/config.md` "Tracker operations". Perform it as `catalog/trackers/<tracker.type>.md` says. If the tracker or its CLI is not authorized, stop and tell the user the command to run. Do not log in or switch accounts yourself.

In plan mode, do not refuse. Inspect with read-only tools, write the concrete plan, and ask for approval. After approval, carry it out as planned.

## 1. Arguments

1. Split `--force` out of the arguments. The first remaining token is `<ISSUE>`.
2. If `<ISSUE>` is empty, show the usage `/groundwork:boarding <issue id> [--force]` and stop.

## 2. State files

- `MAIN_REPO_ROOT = $(git rev-parse --path-format=absolute --git-common-dir | xargs dirname)`
- `KEY` = `<ISSUE>` without a leading `#` (`#12` → `12`).
- `STATE_DIR = $MAIN_REPO_ROOT/.groundwork/state`
- `STATE_FILE = $STATE_DIR/<KEY>.json`
- `ISSUE_FILE = $STATE_DIR/<KEY>.issue.md`

Create `STATE_DIR` if it does not exist. If `git check-ignore -q .groundwork/state/x` fails, append `.groundwork/state/` and `.groundwork/worktrees/` to `.git/info/exclude` so the state stays out of commits without touching tracked files.

## 3. Run

1. Load `STATE_FILE`. If it does not exist, start from an empty state with every `stages.*.done_at` set to `null`.
2. **Skip check.** If `stages.boarding.done_at` is set and `--force` is absent, print `boarding skipped (done at <time>)` and stop.
3. **Read the issue.** `read(<ISSUE>)`. If it is not found, tell the user and stop. If its state is `done` or `cancelled`, warn the user and ask whether to continue.
4. **Find the code it touches.** Search the code for the issue's keywords, symbols, and screens with Grep and Glob. If the search is broad, hand it to one Explore subagent.
5. **Write `ISSUE_FILE`:**

   ```markdown
   # <ISSUE> — <title>

   - State: <state>
   - Labels: <labels>
   - Branch: <branch_name(ISSUE)>

   ## Requirements
   1. ...

   ## Acceptance criteria
   - ...

   ## Code in scope
   - `<path>` — <one-line note>
   ```

   If the issue states no acceptance criteria, derive them from the requirements and mark them as derived.
6. **Write `STATE_FILE`:**

   ```json
   {
     "issue": "<ISSUE>",
     "branch": "<branch_name(ISSUE)>",
     "stages": {
       "boarding":     { "done_at": "<UTC ISO 8601>" },
       "door_closing": { "done_at": null },
       "taxiing":      { "done_at": null },
       "takeoff":      { "done_at": null }
     },
     "issue_cache": {
       "title": "...",
       "body_md": "...",
       "labels": [],
       "state": "...",
       "fetched_at": "<UTC ISO 8601>"
     },
     "issue_summary_path": "<ISSUE_FILE relative to MAIN_REPO_ROOT>"
   }
   ```

7. **Report** in one or two sentences: the issue title, the number of requirements, and the number of files in scope.

## Rules

- No code changes, no commits, no worktree.
- `--force` overwrites `ISSUE_FILE` and `issue_cache`.
- Do not change the issue's state here. `door-closing` does that.
