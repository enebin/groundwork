---
name: "taxiing"
description: Flight stage 3. Implements the plan inside the issue's worktree, verifies and reviews it, and commits locally without pushing. Use for "taxi <id>", or after door-closing.
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, Agent, Skill, AskUserQuestion, TodoWrite
argument-hint: <issue id> [--force] [--mode eco|normal|sport]
---

Stage 3 of the Flight sequence. Follow the plan in the worktree: write the code, verify it, review it, and commit. Never run `git push`, `gh pr create`, or any other remote side effect.

## 0. Read the config

Read `reference/config.md` under the plugin root (two directories above this skill's directory), then `GROUNDWORK.md` at the repository root as it says. Stop if the file is missing or a key this skill needs is missing.

Talk to the user in `language.conversation`. Write commits in `language.artifacts`.

This skill invokes other skills as `/groundwork:<name>`. In Codex, invoke one by reading and following `skills/<name>/SKILL.md` under the plugin root.

In plan mode, do not refuse. Inspect with read-only tools, write the concrete plan (files, commit units, commands), and ask for approval. After approval, carry it out as planned.

If `docs.rules` and this skill disagree, follow `docs.rules`.

## 1. Arguments

Split `--force` out of the arguments. The first remaining token is `<ISSUE>`. If it is empty, show the usage and stop.

## 2. State files

- `MAIN_REPO_ROOT = $(git rev-parse --path-format=absolute --git-common-dir | xargs dirname)`
- `KEY` = `<ISSUE>` without a leading `#`.
- `STATE_FILE = $MAIN_REPO_ROOT/.groundwork/state/<KEY>.json`
- `PLAN_FILE = $MAIN_REPO_ROOT/.groundwork/state/<KEY>.plan.md`

## 3. Chain

Load `STATE_FILE`, then:

1. `stages.boarding.done_at` is `null` or `--force` → `/groundwork:boarding <ISSUE> [--force]`. Otherwise print a one-line skip message.
2. `stages.door_closing.done_at` is `null` or `--force` → `/groundwork:door-closing <ISSUE> [--force]`. Otherwise print a one-line skip message.

## 4. Run

1. **Skip check.** If `stages.taxiing.done_at` is set and `--force` is absent, print a skip message and stop. With `--force`, the existing commits cannot be undone here. Ask the user once: continue with the rest of the plan on top of the existing commits, or let the user reset the branch themselves and call again.
2. **Enter the worktree.** `cd` to `worktree_path` from `STATE_FILE`. If it is missing, tell the user to run `/groundwork:door-closing <ISSUE> --force` and stop.
3. **Load the plan.** Read `PLAN_FILE` and track its steps with TodoWrite.
4. **Implement.**
   - Follow `docs.rules` and `docs.architecture` (when set).
   - Write the tests `docs.rules` requires together with the code.
   - Commit at each meaningful unit. Use the commit message format in `docs.rules`. If it defines none, write a short imperative subject that ends with `(<ISSUE>)`.
   - Stage files one by one. Never stage `.env`, credential files, or other secrets.
   - If something in the plan is unclear, ask the user instead of guessing.
5. **Verify.** Run the `verification.commands` the change affects. When the change touches `verification.ui_paths`, also run the UI tests that cover the changed screens with `verification.ui_tests.targeted`. Fix failures at the root cause before moving on.
6. **Review**, as `review.trigger` says. Screens are covered in verify, not here: each changed screen needs a UI test with a screenshot that you open and check, and a ledger update, as in the `step` skill. QA and UX agents run only in release QA.
   - `per-round`: invoke `/groundwork:review` in local mode. Fix only the confirmed 🔴/🟠, verify again, and review again. Stop after the round limit of the mode (`--mode` or `mode`; see Modes in `reference/config.md`) if any remain, and ask the user how to proceed.
   - `per-implementation`: invoke `/groundwork:review` in local mode once. Fix the confirmed 🔴/🟠, and verify again.
   - `on-request`: skip the review unless the user asked for one.
   - Ask the user before acting on trade-offs or high-impact UNVERIFIED findings. When the report says `SkepticReview: OFF`, show the user the `[UNVERIFIED]` 🔴/🟠 and ask which to fix. Leave 🟡 and nits for the summary.
7. **Final UI run.** If the change touched `verification.ui_paths`, run `verification.ui_tests.full` once. A failure sends you back to step 5.
8. **Leftovers.** Tell the user about debug output left in changed files, such as stray print or console log calls.
9. **Commit the rest.** Do not finish while `git status` shows uncommitted changes.
10. **Update `STATE_FILE`.** Set `stages.taxiing.done_at = <UTC ISO 8601>`.
11. **Report** in one or two sentences: the number of commits added, which checks passed, and the review result.

## Rules

- No `git push`, `git push --force*`, `gh pr create`, or `gh pr edit`. That is `takeoff`'s job.
- Never commit to `branches.integration` or `branches.production`.
- Never bypass hooks (`--no-verify` and the like). If a hook fails, fix the cause.
