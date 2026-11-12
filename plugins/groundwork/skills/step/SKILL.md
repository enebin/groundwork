---
name: "step"
description: Runs one step sub-issue, or a standalone issue, to completion. Implements it, then repeats verify → review → fix until the review leaves no confirmed 🔴/🟠, logging each round on the issue. Use for "run step <id>", "continue <id>", a change request that has no issue yet ("fix X", "add Y"), which it files as a standalone issue first, a request that only asks to file an issue, which it files without implementing, or when another skill hands over an implemented step. A parent issue goes to `complete-subissues` after the user agrees.
allowed-tools: Bash, Read, Edit, Write, Grep, Glob, Skill, Agent, AskUserQuestion
argument-hint: <issue id | request> [--implemented] [--mode eco|normal|sport]
---

Drive one step to its done criteria.

## 0. Read the config

Read `reference/config.md` under the plugin root (two directories above this skill's directory), then `GROUNDWORK.md` at the repository root as it says. Stop if the file is missing or a key this skill needs is missing.

`workflow.bundle` must be `step-loop`, `design-first`, or `tdd-loop`. Otherwise stop and point the user to the skill that serves their bundle:

- `flight`: removed. Tell the user to run `/groundwork:onboarding`, which migrates it to `step-loop` with `workflow.worktree: true`.
- `quick`: `/groundwork:review-and-fix`, then `/groundwork:commit-push`
- `review-only`: `/groundwork:review`

Talk to the user in `language.conversation`. Write issue comments, logs, and commits in `language.artifacts`.

Every tracker action below is an operation from `reference/config.md` "Tracker operations". Perform it as `catalog/trackers/<tracker.type>.md` says. If the tracker or its CLI is not authorized, stop and tell the user the command to run. Do not log in or switch accounts yourself.

This skill invokes other skills as `/groundwork:<name>`. In Codex, invoke one by reading and following `skills/<name>/SKILL.md` under the plugin root.

If `docs.rules` and this skill disagree, follow `docs.rules`.

## 1. Load context

- If the argument is not an issue id in the tracker's form, it is a request. File it as one standalone issue: `create` it with no parent, using the "Sub-issue body" from `skills/plan/SKILL.md` filled from the request, with labels as "Labels" in `reference/config.md` says. Create it without asking, unless `workflow.confirm_issue` is `true` and the tracker is not `local`; then show it and ask before creating. If the request only asks to file an issue, such as a reminder for something to do after the next release, report its id and labels and stop without implementing it; the `plan` hand-off below does not apply to it. Hand the request to `/groundwork:plan` instead when it clearly needs more than one PR, when `workflow.bundle` is `design-first` (its design step and approval come first), when any `verification.commands` entry has `verified: false`, or when the repository has no commits; `plan` adds the design or scaffold step those cases need. After a `plan` hand-off that created a parent issue, treat that parent as below; when it created one issue with no parent, continue with it. Otherwise continue with the new standalone id. When the argument is only a number, ask which issue is meant instead of filing it.
- `read` the issue with its comments, then `read` the parent issue it belongs to, if it has one.
- If the issue has sub-issues, it is a parent, not a step. Ask whether to run `/groundwork:complete-subissues <id>`, which implements, merges, and cleans up every open sub-issue in order. On yes, invoke it; that answer is its authorization, and this skill stops. On no, ask which sub-issue to run instead.
- Read `docs.rules`, `docs.architecture` (when set) and the documents it links that are in scope, and the code in scope.
- If a step listed in "Depends on" is still open and its branch is not available, stop and say so.
- Earlier round comments on the issue tell you where the last session stopped. Continue from there.
- A **design step** is the step whose "Done when" includes user approval of a document (the first step under `design-first`). It follows the design-step notes below.
- `set_state(id, in_progress)` if the issue is still `todo`.

## 2. Branch

Never work on `branches.integration` or `branches.production`. Use `branch_name(id)`. Branch from `branches.integration` when every dependency is merged, otherwise from the dependency step's branch. Fetch the base first (`git fetch origin <branches.integration>`). Reuse the branch if it already exists.

When `workflow.worktree` is true, work in a worktree instead of switching the main checkout. From the main checkout (`git rev-parse --path-format=absolute --git-common-dir | xargs dirname`):

- New branch: `git worktree add --no-track -b <branch> .groundwork/worktrees/<branch> <base>`.
- The branch exists without a worktree: `git worktree add .groundwork/worktrees/<branch> <branch>`.
- The branch is checked out in the main checkout, for example after `/groundwork:rejoin`: git will not check out one branch in two places. If the main checkout has no uncommitted changes to tracked files, switch it to `branches.integration` first, then add the worktree as above. Otherwise tell the user and stop.
- The worktree exists: reuse it.

If `.groundwork/worktrees/.gitignore` in the main checkout does not exist, write it with the single line `*`, so the worktrees do not show up as untracked files in the main checkout. Do not use `.git/info/exclude`; agent harnesses usually refuse writes inside `.git/`. Then work inside `.groundwork/worktrees/<branch>` for the rest of the step. `/groundwork:rejoin` moves the branch back to the main checkout, and `/groundwork:landing` removes the worktree after the merge.

## 3. Implement

Skip this section if `--implemented` is given; the caller has already done it.

- Follow the issue's "Implementation notes" first. If they say another procedure or skill does the implementation, use it.
- Write the tests `docs.rules` requires together with the code.
- In eco and normal, run only the tests added or changed by the implementation. Sport runs the full suite in the loop below.
- `tdd-loop` bundle, or `test-first` in `verification.base`: work red → green → refactor. Write the failing test first and run it. Before writing any implementation, `comment` a `### Red` log with the command and the failing test name. Then make it pass, then refactor with the tests green.
- Design step: write no code. Change only `docs.architecture`, its sub-documents, or the design note.

## 4. Loop

The mode is `--mode` if given, otherwise `mode` in `GROUNDWORK.md`. It sets the round limit and what reruns; see Modes in `reference/config.md`. Log the mode in round 1.

`--ui-checkpoint` is not a user option: only `/groundwork:complete-subissues` passes it, for the checkpoint-mode exception in `docs.rules`. If the run was not started by `complete-subissues`, ignore the flag and run the full UI suite as usual.

Repeat for round `r = 1` up to the mode's limit:

1. **Verify.** Verification failures do not count as a round. A design step skips this. From round 2, the fixer has already verified its fixes; use its report and do not run them again.
   - In eco and normal round 1, run every `verification.commands` entry once immediately before the first review. When the change touches `verification.ui_paths`, run `verification.ui_tests.full` once, unless `--ui-checkpoint` is given: then a later checkpoint run by `/groundwork:complete-subissues` covers it, so log `Full UI suite: deferred to checkpoint`. Record these complete results in the round log.
   - In sport, run every `verification.commands` entry and the full UI suite in every round, except the full UI suite under `--ui-checkpoint`.
   - During implementation and after review fixes in eco and normal, run only tests added or changed by that work. For changed screens, use `verification.ui_tests.targeted` and open their screenshots.
   - Each changed screen needs a UI test that attaches a screenshot. Write or extend those tests with the code, then open the attached screenshots yourself and check that the screen renders as the task requires: nothing missing, overlapping, or clipped. Keep rendered QA out of this verification round; run it after the review loop only when the screen checks require it (`reference/config.md`).
   - Update the UI coverage ledger (`verification.ui_coverage`) for every screen you changed: a row per check, the test that covers it, or for a check no test can make, the reason in "Why QA must look" and Last verified `stale`.
     A check may go there only as the "Why QA must look" rule in `reference/implementation.md` allows. Write the test instead whenever that rule says one can be written.
   - In round 2 or later, skip UI tests when the fixes since the last pass touch nothing under `verification.ui_paths`. Log them as `not rerun — no UI change since round <r>`.
   - Add-ons in `verification.addons` add checks here. `design-fidelity`: re-measure the changed screens against `verification.design_source`. `api-contract`, `visual-regression`, and any other add-on: run its check. `e2e-stage` adds no check; its rules say how to start UI test commands. For each, follow the rules for that add-on in `docs.rules`.
2. **Review.** Invoke `/groundwork:review` in local mode with `--only` set to the reviewers in `review.reviewers`, plus `ux` when a present `ux` mapping is `continuous` with `code` (Screen checks in `reference/config.md`). From round 2 in `normal`, narrow `--only` to the reviewers that raised a confirmed 🔴/🟠 in the previous round, and make it a follow-up review with `--since <snapshot> --fixes <file>`: `<snapshot>` is the working-tree snapshot you took just before handing the fixes to the fixer (the command is in `/groundwork:review` step 3), and `<file>` is a temporary file holding the fixer's "Fixed" lines. `sport` reviews the whole change every round. From round 2, add `--no-copy-edit`; round 1's copy edits were already applied. For a design step, the review covers the document.
3. **Decide.**
   - A required check is blocked and cannot be unblocked within the authorized scope (for example no simulator) → report the blocker and stop without marking the step complete. Do not spend rounds repeating unchanged blocked checks.
   - Verification passed (including UI tests and your look at their screenshots for changed screens), and no confirmed 🔴/🟠 → go to step 5. In round 1, first hand any copy edits to the fixer as below; its verification replaces another round.
   - Otherwise fix only the confirmed 🔴/🟠. Leave 🟡, nits, and UNVERIFIED items for the log.
   - In round 1, also apply every line under **Copy edits**. Leave out an edit marked replaced when its finding is in the fixer's list. Copy edits do not count as findings and never trigger another review round. Ask the user about **Missing copy** before adding any of it.
   - If the report has trade-offs or high-impact UNVERIFIED items, ask the user before acting on them.
   - In `normal`, take a working-tree snapshot first, for the next round's follow-up review.
   - Hand the fixes to the `fixer` agent instead of making them yourself. By this point your context holds the whole implementation, and every fix, test run, and screenshot would be re-read on each later turn. In Claude Code, launch `groundwork:fixer`. In Codex, spawn a fresh subagent and tell it to read and follow `agents/fixer.md` under the plugin root. Give it a `Plugin root: <path>` line, the issue id, the branch, the mode, the round, the screens the step changes, and each finding to fix copied verbatim from the review report (title, location, evidence, suggestion), plus the user's answer for any finding they decided on. Add the copy edits to apply, copied verbatim, in their own list. Do not edit files while it runs, and do not re-read its changes; its report is what you log. A finding it reports as not fixed stays open for the next round's decision, and a `BLOCKED` report is a blocked check. A 🔴/🟠 under "Noticed, not fixed" has had no independent check; treat it as a high-impact UNVERIFIED item and ask the user before the step can finish. If delegation is unavailable, make the fixes yourself.
4. **Log** the round with `comment`:

```markdown
### Round <r>
- Verify: <pass / what failed and how it was fixed / not applicable>
- Screens: <screenshots inspected and what they showed / not applicable / not rerun> — <screenshot paths>
- Review: 🔴 <n> / 🟠 <n> / 🟡 <n> confirmed
- Fixed: <one line per fixed finding>
- Copy edits: <n> applied / <n> unchanged; not applied: <ID — why>; other matches left: <ID — file:line> (or "not run")
- Left: <🟡, nits, UNVERIFIED — one line each>
```

If the last allowed round ends with confirmed 🔴/🟠 still open, stop and ask the user how to proceed. In `eco`, fix the round-1 findings, verify, and then report anything you could not confirm as fixed instead of reviewing again.

## 5. Finish

1. Do not repeat the complete verification at finish. For a non-design step, do both:
   - Confirm that round 1 recorded every `verification.commands` entry and the required full UI suite as passing (or deferred to checkpoint under `--ui-checkpoint`), and that tests added or changed for every later edit passed.
   - Run the after-implementation gate from Screen checks in `reference/config.md` when a check on the running app resolves to continuous, passing the effective mode and the complete change scope. Run it even if code review had no findings. A FAIL or BLOCKED prevents completion; follow the QA repair/recheck limit before continuing below.
2. Design step: show the user the document and the review result, and stop until they approve it. Their requested changes go back to step 4.
3. Tick the satisfied "Done when" boxes in the issue body with `update_body`.
4. If the step has a parent and produced a decision that later steps need, append it to the parent's "Decisions" with `update_body`. Structural decisions go into `docs.architecture` or its sub-documents instead.
5. `comment` a closing note: what was done, anything left, the branch name.
6. Commits and pushes happen only when the user asks. Offer a commit, and for the push and PR, `/groundwork:takeoff <id>`.
7. `set_state(id, done)`. With `ci-gate` in `verification.base`, the step is done only after the PR's CI passes. Once the user has asked for the push and PR, wait on the checks the way `/groundwork:autoland` does. Do not merge unless `workflow.autoland` is true. Until CI passes, leave the state `in_progress`.
