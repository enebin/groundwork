---
name: "rejoin"
description: Removes an issue's worktree but keeps its branch, rebased on the integration branch, as a local branch in the main checkout. Use to continue work or switch context in the main checkout, whether or not the PR has merged.
allowed-tools: Bash, Read, AskUserQuestion
argument-hint: [issue id | branch]
---

Leave the worktree and keep the branch in the main checkout, rebased on the integration branch. A worktree is a separate directory, so it needs its own dependency install, build cache, and editor index. Rejoining moves the work back to the main checkout, which already has all of that. Local only: nothing is pushed.

## 0. Read the config

Read `reference/config.md` under the plugin root (two directories above this skill's directory), then `GROUNDWORK.md` at the repository root as it says. Stop if the file is missing or a key this skill needs is missing.

Talk to the user in `language.conversation`.

Every tracker action below is an operation from `reference/config.md` "Tracker operations". Perform it as `catalog/trackers/<tracker.type>.md` says. If the tracker or its CLI is not authorized, stop and tell the user the command to run. Do not log in or switch accounts yourself.

In plan mode, do not refuse. Inspect with read-only tools, write the concrete plan (worktree path, branch, commands), and ask for approval. After approval, carry it out as planned.

## 1. Resolve the target

1. Before moving anywhere, save `CURRENT_BRANCH = $(git branch --show-current)`.
2. `MAIN_REPO_ROOT = $(git rev-parse --path-format=absolute --git-common-dir | xargs dirname)`, then `cd $MAIN_REPO_ROOT`.
3. Decide `<branch>` and, when possible, `<ISSUE>`:
   - No argument: use `CURRENT_BRANCH`. If that is empty too, ask the user.
   - The argument looks like an issue id in the tracker's form (`#12`, `ABC-12`, `L-12`): it is `<ISSUE>`, and `<branch>` is `branch_name(<ISSUE>)`.
   - Otherwise it is `<branch>`.
4. If `<branch>` is `branches.integration` or `branches.production`, refuse and stop.

## 2. Run

1. **Find the worktree.** `git worktree list --porcelain`.
   - No worktree but the local branch exists: ask the user whether to only rebase the branch.
   - Neither exists: stop.
2. **Uncommitted changes.** If `git status --porcelain` inside the worktree is not empty, tell the user to commit or stash first, and stop. Never stash on their behalf.
3. **Update the integration branch.** In the main checkout: `git fetch origin <branches.integration>`, `git checkout <branches.integration>`, `git pull --ff-only origin <branches.integration>`. If the main checkout has uncommitted changes or the fast-forward fails, tell the user and stop.
4. **Remove the worktree.** `git worktree remove <path>`. If it fails for another reason, such as a locked file, ask the user before adding `--force`.
5. **Rebase the branch.** `git checkout <branch>`, then `git rebase origin/<branches.integration>`. On a conflict, do not resolve it. Leave the rebase in progress, tell the user to resolve and run `git rebase --continue`, or `git rebase --abort`, and stop.
6. **Report** in one or two sentences: how many commits `<branch>` is ahead (`git rev-list --count origin/<branches.integration>..<branch>`), the HEAD hash, the removed worktree path, and that nothing was pushed.

## Rules

- No push, force-push, or `gh pr` calls.
- Never stash automatically.
- Do not resolve rebase conflicts automatically.
- Do not change the issue's state.
- After the PR merges, clean up with `/groundwork:landing`. It skips the missing worktree.
