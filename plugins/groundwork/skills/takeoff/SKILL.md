---
name: "takeoff"
description: Step-workflow push. Rebases an issue's branch on the integration branch, re-verifies, pushes it, and opens a PR, once the user asks for a push. Use for "takeoff <id>", "push and open a PR for <id>", or after a step is done.
allowed-tools: Bash, Read, Skill, AskUserQuestion
argument-hint: <issue id> [--mode eco|normal|sport]
---

Rebase on the integration branch, push, and open a PR. Only this skill, `autoland`, and `release` touch the remote.

## 0. Read the config

Read `reference/config.md` under the plugin root (two directories above this skill's directory), then `GROUNDWORK.md` at the repository root as it says. Stop if the file is missing or a key this skill needs is missing.

Talk to the user in `language.conversation`. Write the PR title and body in `language.artifacts`.

Every tracker action below is an operation from `reference/config.md` "Tracker operations". Perform it as `catalog/trackers/<tracker.type>.md` says. If the tracker or its CLI is not authorized, stop and tell the user the command to run. Do not log in or switch accounts yourself.

This skill invokes other skills as `/groundwork:<name>`. In Codex, invoke one by reading and following `skills/<name>/SKILL.md` under the plugin root.

Run only when the user asked in so many words to push or open a PR, or when `autoland` hands over after such a request. A vague request ("ship it", "upload this", "wrap it up") is not enough; ask first.

In plan mode, do not refuse. Inspect with read-only tools, write the concrete plan (rebase target, push command, PR title and body), and ask for approval. After approval, carry it out as planned.

If `docs.rules` and this skill disagree, follow `docs.rules`.

## 1. Arguments

Split `--mode <eco|normal|sport>` out of the arguments. Validate the mode and resolve it against the configured overall mode. The first remaining token is `<ISSUE>`. If it is empty, show the usage and stop.

## 2. Run

1. **GitHub CLI.** Run `gh auth status`. If it is not authenticated or lacks permission for this repository, stop and tell the user to run `gh auth login` themselves. Never run `gh auth login` or `gh auth switch`.
2. **Find the branch.** `<branch>` is `branch_name(<ISSUE>)`. If `git worktree list --porcelain` shows it checked out in a worktree, `cd` there. Otherwise it must be the current branch of the main checkout; if it is not, tell the user and stop.
3. **Clean tree.** If `git status` shows uncommitted changes, tell the user and stop.
4. **Rebase.** `git fetch origin <branches.integration> && git rebase origin/<branches.integration>`. On a conflict, do not resolve it. Leave the rebase in progress, tell the user which files conflict and that they can finish with `git rebase --continue` or back out with `git rebase --abort`, and stop.
5. **Re-verify.** If the rebase brought in new commits, run the `verification.commands` the change affects again. Recheck affected UI tests and screenshots, and invalidate any earlier rendered QA whose checked behavior changed. For continuous QA, rerun the affected after-implementation QA gate from `reference/config.md` on the rebased candidate with the effective mode before pushing. On FAIL or BLOCKED, stop and report. If QA updates the ledger, include it in a local commit under the existing workflow permissions before pushing; do not leave a dirty candidate.
6. **Push.**
   - First push: `git push -u origin <branch>`.
   - The branch already exists on the remote and the rebase rewrote its history: ask the user, then `git push --force-with-lease origin <branch>`. Never plain `--force`.
   - Never push to `branches.integration` or `branches.production`.
7. **Manual checks.** From the issue, its round log, and the commits, list one to five things the user can see for themselves: a screen, a button, a list, a status, a message, a user flow. If nothing is visible (refactoring, tests, infrastructure), write "No visible change to check". Mark guesses as guesses.
8. **Open the PR.** `gh pr create --base <branches.integration> --head <branch>` with the body in a HEREDOC. If a PR for the branch is already open, report its URL instead.
   - Title: the format in `docs.rules` if it defines one. Otherwise a short imperative summary followed by `(<ISSUE>)`.
   - Body:

     ```markdown
     ## Summary
     - <the issue's goal and what the commits did, one to three lines>

     ## Changes
     - <from the commits>

     ## Test plan
     - [ ] <the verification the step ran>

     ## Manual checks
     - <from step 7>

     <closing reference for ISSUE, in the syntax catalog/trackers/<tracker.type>.md gives>
     ```

9. **Report** the PR URL and the manual checks.
10. **Next.** If `workflow.autoland` is true and this run was not started by `autoland`, continue with `/groundwork:autoland <ISSUE>`. Otherwise stop here and tell the user that `/groundwork:landing <ISSUE>` cleans up after the merge.

## Rules

- Do not resolve rebase conflicts automatically.
- Force-push only with the user's approval, and only with `--force-with-lease`.
- Never bypass hooks or branch protection.
