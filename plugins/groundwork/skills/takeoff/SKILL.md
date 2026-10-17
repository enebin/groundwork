---
name: "takeoff"
description: Flight stage 4. Rebases the issue branch on the integration branch, pushes it, and opens a PR. The only Flight stage with remote side effects. Use for "takeoff <id>", or after taxiing.
allowed-tools: Bash, Read, Skill, AskUserQuestion, TodoWrite
argument-hint: <issue id> [--force]
---

Stage 4 of the Flight sequence. Rebase on the integration branch, push, and open a PR. Only this stage, `autoland`, and `release` touch the remote. On success, delete the issue's state files.

## 0. Read the config

Read `reference/config.md` under the plugin root (two directories above this skill's directory), then `GROUNDWORK.md` at the repository root as it says. Stop if the file is missing or a key this skill needs is missing.

Talk to the user in `language.conversation`. Write the PR title and body in `language.artifacts`.

Every tracker action below is an operation from `reference/config.md` "Tracker operations". Perform it as `catalog/trackers/<tracker.type>.md` says. If the tracker or its CLI is not authorized, stop and tell the user the command to run. Do not log in or switch accounts yourself.

This skill invokes other skills as `/groundwork:<name>`. In Codex, invoke one by reading and following `skills/<name>/SKILL.md` under the plugin root.

In plan mode, do not refuse. Inspect with read-only tools, write the concrete plan (rebase target, push command, PR title and body), and ask for approval. After approval, carry it out as planned.

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

Load `STATE_FILE`, then run each earlier stage whose `done_at` is `null`, or every one with `--force`. Print a one-line skip message for the others.

1. `/groundwork:boarding <ISSUE> [--force]`
2. `/groundwork:door-closing <ISSUE> [--force]`
3. `/groundwork:taxiing <ISSUE> [--force]`

The chain never runs `landing`.

## 4. Run

1. **Skip check.** If `stages.takeoff.done_at` is set and `--force` is absent, stop. This is rare, because a successful takeoff deletes the state file.
2. **GitHub CLI.** Run `gh auth status`. If it is not authenticated or lacks permission for this repository, stop and tell the user to run `gh auth login` themselves. Never run `gh auth login` or `gh auth switch`.
3. **Enter the worktree.** `cd` to `worktree_path`. If it is missing, tell the user and stop.
4. **Clean tree.** If `git status` shows uncommitted changes, tell the user and stop.
5. **Rebase.** `git fetch origin <branches.integration> && git rebase origin/<branches.integration>`. On a conflict, do not resolve it. Leave the rebase in progress, tell the user which files conflict and that they can finish with `git rebase --continue` or back out with `git rebase --abort`, and stop.
6. **Re-verify.** If the rebase brought in new commits, run the `verification.commands` the change affects again. On failure, stop and report.
7. **Push.**
   - First push: `git push -u origin <branch>`.
   - The branch already exists on the remote and the rebase rewrote its history: ask the user, then `git push --force-with-lease origin <branch>`. Never plain `--force`.
   - Never push to `branches.integration` or `branches.production`.
8. **Manual checks.** From `PLAN_FILE`, `ISSUE_FILE`, and the commits, list one to five things the user can see for themselves: a screen, a button, a list, a status, a message, a user flow. If nothing is visible (refactoring, tests, infrastructure), write "No visible change to check". Mark guesses as guesses.
9. **Open the PR.** `gh pr create --base <branches.integration> --head <branch>` with the body in a HEREDOC.
   - Title: the format in `docs.rules` if it defines one. Otherwise a short imperative summary followed by `(<ISSUE>)`.
   - Body:

     ```markdown
     ## Summary
     - <goal from PLAN_FILE and commit summary, one to three lines>

     ## Changes
     - <from the commits and the plan's files to change>

     ## Test plan
     - [ ] <from the plan's verification section>

     ## Manual checks
     - <from step 8>

     <closing reference for ISSUE, in the syntax catalog/trackers/<tracker.type>.md gives>
     ```

10. **Report** the PR URL and the manual checks.
11. **Clean up state.** First set `stages.takeoff.done_at = <UTC ISO 8601>` and save, so a failure below does not rerun takeoff. Then `rm -f $STATE_FILE $ISSUE_FILE $PLAN_FILE`. If deletion fails, warn and keep going.
12. **Next.** If `workflow.autoland` is true and this run was not started by `autoland`, continue with `/groundwork:autoland <ISSUE>`. Otherwise stop here and tell the user that `/groundwork:landing <ISSUE>` cleans up after the merge.

## Rules

- No other Flight stage runs `git push` or `gh pr create`.
- Do not resolve rebase conflicts automatically.
- Force-push only with the user's approval, and only with `--force-with-lease`.
- Never bypass hooks or branch protection.
