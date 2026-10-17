---
name: "door-closing"
description: Flight stage 2. Fetches the integration branch, creates a worktree for the issue, and writes an implementation plan. Use for "door-closing <id>", or after boarding.
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, Agent, Skill, AskUserQuestion, TodoWrite
argument-hint: <issue id> [--force]
---

Stage 2 of the Flight sequence. Create a worktree for the issue from the latest integration branch and write the implementation plan. No code changes, no commits, no pushes.

## 0. Read the config

Read `reference/config.md` under the plugin root (two directories above this skill's directory), then `GROUNDWORK.md` at the repository root as it says. Stop if the file is missing or a key this skill needs is missing.

Talk to the user in `language.conversation`. Write the plan in `language.artifacts`.

Every tracker action below is an operation from `reference/config.md` "Tracker operations". Perform it as `catalog/trackers/<tracker.type>.md` says. If the tracker or its CLI is not authorized, stop and tell the user the command to run. Do not log in or switch accounts yourself.

This skill invokes other skills as `/groundwork:<name>`. In Codex, invoke one by reading and following `skills/<name>/SKILL.md` under the plugin root.

In plan mode, do not refuse. Inspect with read-only tools, write the concrete plan (worktree path, files, commands), and ask for approval. After approval, carry it out as planned.

If `docs.rules` and this skill disagree, follow `docs.rules`.

## 1. Arguments

Split `--force` out of the arguments. The first remaining token is `<ISSUE>`. If it is empty, show the usage and stop.

## 2. State files

- `MAIN_REPO_ROOT = $(git rev-parse --path-format=absolute --git-common-dir | xargs dirname)`
- `KEY` = `<ISSUE>` without a leading `#`.
- `STATE_FILE = $MAIN_REPO_ROOT/.groundwork/state/<KEY>.json`
- `ISSUE_FILE = $MAIN_REPO_ROOT/.groundwork/state/<KEY>.issue.md`
- `PLAN_FILE = $MAIN_REPO_ROOT/.groundwork/state/<KEY>.plan.md`

## 3. Chain

Load `STATE_FILE`. If `stages.boarding.done_at` is `null` or `--force` is given, run `/groundwork:boarding <ISSUE> [--force]` first. Otherwise print `boarding skipped (done at <time>)`.

## 4. Run

1. **Skip check.** If `stages.door_closing.done_at` is set and `--force` is absent, print a one-line summary and stop.
2. **Go to the main repository.** `cd $MAIN_REPO_ROOT`.
3. **Fetch the integration branch.** `git fetch origin <branches.integration>`. If it fails, report the cause and stop.
4. **Branch name.** Use `branch` from `STATE_FILE`. If it is empty, use `branch_name(<ISSUE>)` and store it.
5. **Create the worktree** at `.groundwork/worktrees/<branch>`:
   - New branch: `git worktree add --no-track -b <branch> .groundwork/worktrees/<branch> origin/<branches.integration>`.
   - The branch exists but has no worktree: `git worktree add .groundwork/worktrees/<branch> <branch>`.
   - The worktree already exists: reuse it. With `--force`, ask the user whether to remove and recreate it. Only after a yes, run `git worktree remove .groundwork/worktrees/<branch>` and recreate it. If removal fails because of uncommitted changes, stop and tell the user. Do not add `--force` to the removal.
6. **Move the issue.** `set_state(<ISSUE>, in_progress)` if it is still `todo`, unless the tracker document says the tracker moves it on its own.
7. **Write the plan.** Read `ISSUE_FILE`, `docs.rules`, `docs.architecture` (when set), and the code in scope inside the worktree. If the search is broad, hand it to one Explore subagent. Write `PLAN_FILE`:

   ```markdown
   # <ISSUE> implementation plan

   ## Goal
   - <one line>

   ## Files to change
   - `<path>` — <reason>

   ## Steps
   1. ...

   ## Verification
   - <which `verification.commands` entries the change needs>
   - <UI tests to run with `verification.ui_tests.targeted`, when files under `verification.ui_paths` change>
   - <tests to add, as `docs.rules` requires>

   ## Acceptance criteria mapping
   - <criterion from ISSUE_FILE> → <change or test that meets it>

   ## Risks and open questions
   - ...
   ```

8. **Update `STATE_FILE`.** Set `worktree_path`, `plan_path`, and `stages.door_closing.done_at = <UTC ISO 8601>`.
9. **Report** in one or two sentences: the worktree path, the number of files to change, and the number of steps. Ask about any open question in the plan before the user moves on.

## Rules

- No code changes, commits, `git push`, or `gh pr create` here. `taxiing` writes code; `takeoff` is the only remote step.
- Never commit to `branches.integration` or `branches.production`.
- `--force` overwrites `PLAN_FILE`.
