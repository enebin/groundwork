---
name: "autoland"
description: Waits for a PR's CI checks, merges it once every check passes, then cleans up like landing. Runs takeoff first when no PR exists yet. Use for "autoland", or after takeoff when `workflow.autoland` is true.
allowed-tools: Bash, Read, Skill, AskUserQuestion
argument-hint: [issue id | branch | PR URL] [--interval <seconds>] [--timeout <minutes>]
---

Merge a PR once CI passes, then clean up locally. It polls with the GitHub CLI; it does not use webhooks or GitHub's own auto-merge.

## 0. Read the config

Read `reference/config.md` under the plugin root (two directories above this skill's directory), then `GROUNDWORK.md` at the repository root as it says. Stop if the file is missing or a key this skill needs is missing.

Talk to the user in `language.conversation`.

Every tracker action below is an operation from `reference/config.md` "Tracker operations". Perform it as `catalog/trackers/<tracker.type>.md` says. If the tracker or its CLI is not authorized, stop and tell the user the command to run. Do not log in or switch accounts yourself.

This skill invokes other skills as `/groundwork:<name>`. In Codex, invoke one by reading and following `skills/<name>/SKILL.md` under the plugin root.

In plan mode, do not refuse. Inspect with read-only tools, write the concrete plan (PR, checks, merge command, cleanup), and ask for approval. After approval, carry it out as planned.

`workflow.bundle` `quick` and `review-only` do not use autoland. If the bundle is one of them, tell the user and stop.

## 1. Arguments

1. Before moving anywhere, save `CURRENT_BRANCH = $(git branch --show-current)`.
2. The first token that is not a flag is `<TARGET>`. Without one, use `CURRENT_BRANCH`. If both are empty, ask the user.
3. `--interval <seconds>`: default `30`. Stop if it is not a number of at least 1.
4. `--timeout <minutes>`: default `60`. Stop if it is not a number of at least 1.

## 2. Run

1. **Go to the main repository.** `MAIN_REPO_ROOT = $(git rev-parse --path-format=absolute --git-common-dir | xargs dirname)`, then `cd $MAIN_REPO_ROOT`.
2. **GitHub CLI.** Run `gh auth status`. In a sandbox, keyring access can fail and make a valid token look invalid; if so, check once more outside the sandbox before deciding. If it is not authenticated, expired, or lacks permission, stop and tell the user to run `gh auth login` themselves. Never run `gh auth login` or `gh auth switch`.
3. **Resolve the target.**
   - An issue id in the tracker's form (`#12`, `ABC-12`, `L-12`): keep it as `<ISSUE>`; the branch is `branch_name(<ISSUE>)`.
   - A URL of the form `https://github.com/<owner>/<repo>/pull/<n>`: use it as the PR.
   - Otherwise it is a branch. If it has the form `<branches.work_prefix>/<id>-<slug>`, take `<ISSUE>` from it.
4. **Find the PR.** `gh pr view <PR or branch> --json number,url,state,isDraft,baseRefName,headRefName,headRefOid,mergeable`.
   - No PR and `<ISSUE>` is known: run `/groundwork:takeoff <ISSUE>` and tell it this run comes from autoland, so it does not chain back. If takeoff stops for the user (force-push approval, conflict, uncommitted changes, missing worktree), stop too. Afterwards run `gh pr view` again. If there is still no PR, stop.
   - No PR and no `<ISSUE>`: stop.
   - `state` is `MERGED`: skip to step 10.
   - `state` is not `OPEN`, `isDraft` is true, or `baseRefName` is not `branches.integration`: stop.
   - From here on, pin the PR URL, number, `headRefName`, and `headRefOid`.
5. **Initial checks.** `gh pr checks <PR> --json bucket,state,name,workflow,link`. Stop if it returns no checks, or if any check's `bucket` is `fail` or `cancel`.
6. **Wait.** `gh pr checks <PR> --watch --fail-fast --interval <interval>`. If it runs longer than `<timeout>` minutes, end the wait and do not merge. If the watch ends in failure, cancellation, or timeout, list the failing checks with their links and stop.
7. **Final checks.** Run `gh pr checks <PR> --json bucket,state,name,workflow,link` again. Stop if it returns no checks, or if any `bucket` is not `pass`. `skipping` and `pending` do not count as passing.
8. **Recheck the PR.** `gh pr view <PR> --json state,isDraft,baseRefName,headRefOid,mergeable`. Stop if it is no longer `OPEN`, became a draft, changed base, or its `headRefOid` differs from the pinned one; new commits need a new CI run.
9. **Merge.** `gh pr merge <PR> --<branches.merge> --match-head-commit <headRefOid>`, where `--<branches.merge>` is `--squash`, `--merge`, or `--rebase`. Never use `--admin` or `--auto`. If branch protection, a required review, a merge conflict, or a permission error blocks it, stop and report. Do not work around it.
10. **Clean up.** Follow `/groundwork:landing` with `<ISSUE>` when known, otherwise with `headRefName`. If the worktree is missing, landing skips it.
11. **Manual checks.** Use the PR body's "Manual checks" section. Without one, read the diff, commits, and issue, and list one to five things the user can see for themselves. If nothing is visible, say so. Mark guesses as guesses.
12. **Report:** the PR URL, the check results, the merge method used, the landing result, and the manual checks.

## Rules

- Never merge with failed, cancelled, timed-out, pending, or missing checks.
- Never merge a draft, closed, or wrong-base PR.
- Never bypass branch protection, required reviews, or merge conflicts. No `--admin`, `--auto`, force-push, or direct push to `branches.integration`.
