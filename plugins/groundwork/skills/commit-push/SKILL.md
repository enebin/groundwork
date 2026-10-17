---
name: "commit-push"
description: Commits the current branch's changes and pushes them to the remote without asking for confirmation, except in the warning cases. Use for "commit and push", or after review-and-fix in the quick workflow.
allowed-tools: Bash, Read, Grep, Glob, AskUserQuestion
argument-hint: [commit message hint]
---

Commit the current branch's changes and push them. The argument, if any, is a hint for the commit message.

## 0. Read the config

Read `reference/config.md` under the plugin root (two directories above this skill's directory), then `GROUNDWORK.md` at the repository root as it says. Stop if the file is missing or a key this skill needs is missing.

Talk to the user in `language.conversation`. Write the commit message in `language.artifacts`.

In plan mode, do not refuse. Inspect with read-only tools, write the concrete plan (files to stage, commit message, push command), and ask for approval. After approval, carry it out as planned.

If `docs.rules` and this skill disagree, follow `docs.rules`.

## Steps

1. **Status.** `git status`. If nothing changed, tell the user and stop.
2. **Diff.** Read `git diff` and `git diff --staged`.
3. **Style.** Read `git log --oneline -5` to match recent commits.
4. **Message.** Use the commit message format in `docs.rules`. If it defines none, write a short imperative subject. Use the argument as a hint.
5. **Stage** changed files one by one. Leave out `.env`, credential files, and other secrets, and tell the user you left them out.
6. **Commit.** Never bypass hooks (`--no-verify` and the like). If a hook fails, fix the cause or report it.
7. **Push.** If the branch tracks a remote branch, `git push`. Otherwise `git push -u origin <branch>`. If the push is rejected, report why and stop. Never force-push.

## Warnings

Proceed without asking unless one of these applies:

- The current branch is `branches.integration` or `branches.production`: warn and ask before committing.
- A secret file is among the changes: leave it out and tell the user.
- Changed files contain leftover debug output, such as stray print or console log calls: tell the user.
