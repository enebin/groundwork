---
name: "complete-subissues"
description: Completes every open sub-issue of a parent issue one at a time — implement, verify, review, commit, open a PR, merge, and clean up — then reports. Use for "complete the sub-issues of <id>", "finish every step of <id>", after `plan` creates a parent issue, or when `step` is given a parent issue. Not for planning, one standalone issue, or a report-only request.
allowed-tools: Bash, Read, Edit, Write, Grep, Glob, Skill, Agent, AskUserQuestion
argument-hint: <parent issue id> [--mode eco|normal|sport]
---

Drive a fixed set of sub-issues to resolution. One explicit invocation with a parent issue id authorizes commits, pushes, PR creation, and ordinary protected merges for that starting set, even when `workflow.autoland` is false. It does not authorize force-pushes, bypassing branch protection, resolving conflicts automatically, destructive cleanup, or adding sub-issues linked after the run starts.

## 0. Read the config

Read `reference/config.md` under the plugin root (two directories above this skill's directory), then `GROUNDWORK.md` at the repository root as it says. Stop if the file is missing or a key this skill needs is missing.

`workflow.bundle` must be `step-loop`, `design-first`, or `tdd-loop`. Otherwise stop and point the user to the skill that serves their bundle, as `/groundwork:step` lists.

Talk to the user in `language.conversation`. Write issue comments, logs, and commits in `language.artifacts`.

Every tracker action below is an operation from `reference/config.md` "Tracker operations". Perform it as `catalog/trackers/<tracker.type>.md` says. If the tracker or its CLI is not authorized, stop and tell the user the command to run. Do not log in or switch accounts yourself. Before commits, pushes, and merges, apply the commit-identity and account rules in `docs.rules`; if the identity or account is wrong, stop instead of changing it.

This skill invokes other skills as `/groundwork:<name>`. In Codex, invoke one by reading and following `skills/<name>/SKILL.md` under the plugin root.

If `docs.rules` and this skill disagree, follow `docs.rules`.

## 1. Prepare

1. Require one parent issue id. Pass `--mode` on to every skill below that takes it.
2. `read` the parent with its comments and sub-issues. If it has no sub-issues, stop: it is not a parent. Point the user to `/groundwork:step <id>`.
3. Snapshot the sub-issue ids in the parent's "Steps" order, or tracker order when it has none. A sub-issue is already resolved when it is cancelled, or done with its PR merged or a note that no merge is needed. Every other sub-issue is a target. `step` marks an issue done before its PR merges, so a done sub-issue with an open or missing PR is a target too: resume it at takeoff (3.4) or merge (§4) instead of running `step` again. Running this skill again with the same parent id is how a stopped run resumes.
4. Choose the UI mode. Read each target and judge whether it will likely change a screen: a path under `verification.ui_paths`, a UI test, or an API shape a screen reads. Use **checkpoint mode** when 2 or more targets likely change screens, or when the user asks. Otherwise each step runs its full UI suite as `/groundwork:step` requires. If a target turns out to change a screen and that brings the count to 2, switch to checkpoint mode from that target onward.
5. `comment` a first progress note on the parent: the targets in order, the already-resolved sub-issues, the UI mode, and in checkpoint mode the checkpoint plan with reasons.

## 2. Choose the next sub-issue

Work one at a time, because later steps may depend on earlier merges.

- Re-read the parent and its sub-issues before each one.
- If a sub-issue was linked after the snapshot, ask whether to add it. Do not expand the run silently.
- Choose the first unresolved target whose "Depends on" items are resolved. A dependency is resolved only when its PR is merged, or its issue says no merge is needed.
- If no unresolved target can run, stop and name the dependency cycle or outside dependency. Do not skip ahead.
- A target cancelled during the run counts as resolved; report it and do not implement it.

## 3. Complete one sub-issue

1. Invoke `/groundwork:step <id>`, adding `--ui-checkpoint` in checkpoint mode. Follow it fully: it owns implementation, tests, review, fixes, issue logs, and done criteria. Do not run another review because a PR follows.
2. Stop when the step stops: a failed or blocked required check, an open confirmed finding, a high-impact UNVERIFIED finding, design approval, or another question it asks. Keep the branch, and resume the same sub-issue after the user answers.
3. When the step is complete, look at that sub-issue's working tree only. If it has changes, stage only its files and commit with a message `docs.rules` allows. Never bypass hooks. If unrelated changes are present, stop instead of including them.
4. Invoke `/groundwork:takeoff <id>` and tell it this run comes from `complete-subissues`, so it does not chain into autoland even when `workflow.autoland` is true. This invocation already gives it the push-and-PR request. Stop on conflicts, a dirty tree, failed re-verification, or a needed force-push. Never resolve a rebase conflict or force-push on your own.
5. Read the PR and pin its URL, base branch, head branch, and head commit. It must be open, not a draft, based on `branches.integration`, mergeable, and without an active changes-requested review. Check that the step's log shows every required check passed and no confirmed blocking finding remains.

## 4. Merge

- Query the PR's checks. If at least one exists, invoke `/groundwork:autoland <id>` and tell it this run comes from `complete-subissues`; this invocation already gives it the merge request. It waits, rechecks the pinned head, merges with `branches.merge`, and cleans up. A failed, cancelled, skipped, timed-out, or changed-head result stops the run.
- If no checks exist, merge only when `verification.base` is `evidence` and the step log proves its verification and review passed. In checkpoint mode, `Full UI suite: deferred to checkpoint` satisfies the UI part. Re-read the PR right before merging, confirm the pinned head and mergeability again, then run `gh pr merge` with `branches.merge` and `--match-head-commit <head>`. Never use `--admin` or `--auto`, never push straight to `branches.integration` or `branches.production`, and never merge without checks when `verification.base` has `ci-gate`.
- After such a manual merge, do the tracker's post-merge state change (`set_state(id, done)` when the tracker does not close it on merge) and invoke `/groundwork:landing <id>`. If cleanup alone needs approval for a destructive action, leave the worktree or branch, note it, and continue; leftover cleanup does not undo a merge.
- If branch protection, a required human approval, a conflict, permissions, or tracker state blocks the merge, stop. Do not count that sub-issue as resolved, and do not start one that depends on it.

After a merge, re-read the sub-issue and its PR. It is resolved only when the PR is merged and the issue is done.

## 5. UI checkpoints

Checkpoint mode only. A checkpoint runs `verification.ui_tests.full` on merged code in the background, so implementation never waits for it.

- Plan checkpoints by judgment, not a fixed count, and keep them few: each is a full suite run. Run one after a group of sub-issues that touch the same screens. Sub-issues with no screen change need none of their own. Always run one after the last merge. Revise the plan as sub-issues land, and note changes on the parent.
- A later sub-issue that builds on screens an earlier checkpoint covers starts right away. Check that checkpoint's result before merging it: wait if it is still running, and if it shows a break on a screen the sub-issue builds on, stop before merging and ask.
- At a checkpoint, pin the head commit of `branches.integration` after the latest merge. If no sub-issue merged since the last checkpoint changed a screen, skip it and note why.
- Launch one background subagent per checkpoint, then continue with the next sub-issue. Give it the pinned commit and the sub-issues it covers. It adds its own worktree at that commit, installs dependencies, keeps its test data and ports apart from other runs, runs `verification.ui_tests.full` once (with `E2E_STAGE=checkpoint` in front when `verification.addons` has `e2e-stage`), opens the attached screenshots, removes its worktree, and reports each failure with the test, the error, the screenshot path, and the likely sub-issue. It does not edit code, commit, or touch the tracker. Do not start a checkpoint while the previous one is running; fold its sub-issues into the next one.
- When a checkpoint reports, `comment` the result on the parent. `create` each distinct failure as a new sub-issue of the parent with the commit, the failing test, the evidence, and the suspected sub-issue. Do not rerun a failure to get a pass, and do not add these new sub-issues to the current run. A checkpoint that could not run is blocked, not passed.
- A checkpoint failure does not stop the run or reopen a merged sub-issue, unless a not-yet-started target cannot proceed because of it; then stop and ask.

## 6. Finish

Re-read the parent and every snapshotted sub-issue. Finish only when every target is resolved as Prepare item 3 defines it, no merge is pending, and in checkpoint mode the last checkpoint has reported. Do not close the parent unless the user asked.

Report:

- each sub-issue and its final state;
- each PR URL and merge result;
- verification or review that was blocked or did not apply;
- in checkpoint mode, each checkpoint's commit, result, and the sub-issues created from its failures;
- local cleanup left behind;
- sub-issues linked during the run that were not added.

If the run stops early, lead with the sub-issue and the blocker, then the command or decision that resumes it.
