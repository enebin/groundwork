---
name: "landing"
description: Cleans up after a PR merges. Confirms the merge, removes the issue's worktree if it has one, deletes the local branch, and updates the local integration branch. Use for "land <id>" after a PR merges.
allowed-tools: Bash, Read, AskUserQuestion
argument-hint: [issue id | branch]
---

Clean up after a PR merges: remove the worktree if there is one, update the local integration branch, and delete the local work branch. `takeoff` never chains into this stage, because only the user knows when the PR merges. `autoland` runs it after its own merge.

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
   - If `<branch>` has the form `<branches.work_prefix>/<id>-<slug>`, take `<ISSUE>` from it.
4. If `<branch>` is `branches.integration` or `branches.production`, refuse and stop.

## 2. Run

1. **GitHub CLI.** Run `gh auth status`. If it is not authenticated or lacks permission, stop and tell the user to run `gh auth login` themselves. Never run `gh auth login` or `gh auth switch`.
2. **Merged?** `gh pr view <branch> --json state,number,url`.
   - `state` is not `MERGED`: tell the user the state and ask whether to remove the worktree anyway. Suggest `/groundwork:rejoin` if they want to keep the branch.
   - No PR: tell the user and ask whether to clean up the worktree only.
3. **Remove the worktree.** Find the worktree for `<branch>` with `git worktree list --porcelain`.
   - None: print `worktree not present, skipping` and go on. This is normal when `workflow.worktree` is false or after `/groundwork:rejoin`.
   - It has uncommitted changes: tell the user and stop.
   - Otherwise `git worktree remove <path>`. If it fails for another reason, such as a locked file, ask the user before adding `--force`.
4. **Update the integration branch.** If the main checkout has uncommitted changes to tracked files (`git status --porcelain --untracked-files=no` is not empty; untracked files go along with a checkout and do not block it), tell the user and skip this step. Otherwise `git checkout <branches.integration> && git pull --ff-only origin <branches.integration>`. If the fast-forward fails, report it and stop.
5. **Delete the local branch.** Try `git branch -d <branch>`. With `branches.merge` set to `squash` or `rebase`, this usually fails because the merged commits have new hashes. If it fails, show the user the PR state and ask before `git branch -D <branch>`.
6. **Close the issue.** If `<ISSUE>` is known and the PR is merged, `set_state(<ISSUE>, done)`, unless the tracker document says the tracker does this on its own. Then do what the tracker document's "After the merge" section says, if it has one.
7. **Report** in one or two sentences: the merged PR URL, the removed worktree path, and the latest commit hash of `branches.integration`.

## Rules

- Remove the worktree of an unmerged PR only after the user approves.
- `git branch -D` and `git worktree remove --force` only after the user approves.
- No commits or pushes to `branches.integration` or `branches.production`.
