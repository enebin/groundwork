---
name: "step"
description: Runs one step sub-issue to completion. Implements it, then repeats verify → review → fix until the review leaves no confirmed 🔴/🟠, logging each round on the issue. Use for "run step <id>", "continue <id>", or when another skill hands over an implemented step.
allowed-tools: Bash, Read, Edit, Write, Grep, Glob, Skill, Agent, AskUserQuestion
argument-hint: <sub-issue id> [--implemented] [--mode eco|normal|sport]
---

Drive one step to its done criteria.

## 0. Read the config

Read `reference/config.md` under the plugin root (two directories above this skill's directory), then `GROUNDWORK.md` at the repository root as it says. Stop if the file is missing or a key this skill needs is missing.

`workflow.bundle` must be `step-loop`, `design-first`, or `tdd-loop`. Otherwise stop and point the user to the skill that serves their bundle:

- `flight`: `/groundwork:boarding` and the stages after it
- `quick`: `/groundwork:review-and-fix`, then `/groundwork:commit-push`
- `review-only`: `/groundwork:review`

Talk to the user in `language.conversation`. Write issue comments, logs, and commits in `language.artifacts`.

Every tracker action below is an operation from `reference/config.md` "Tracker operations". Perform it as `catalog/trackers/<tracker.type>.md` says. If the tracker or its CLI is not authorized, stop and tell the user the command to run. Do not log in or switch accounts yourself.

This skill invokes other skills as `/groundwork:<name>`. In Codex, invoke one by reading and following `skills/<name>/SKILL.md` under the plugin root.

If `docs.rules` and this skill disagree, follow `docs.rules`.

## 1. Load context

- `read` the issue with its comments, then `read` the parent issue it belongs to.
- Read `docs.rules`, `docs.architecture` (when set) and the documents it links that are in scope, and the code in scope.
- If a step listed in "Depends on" is still open and its branch is not available, stop and say so.
- Earlier round comments on the issue tell you where the last session stopped. Continue from there.
- A **design step** is the step whose "Done when" includes user approval of a document (the first step under `design-first`). It follows the design-step notes below.
- `set_state(id, in_progress)` if the issue is still `todo`.

## 2. Branch

Never work on `branches.integration` or `branches.production`. Use `branch_name(id)`. Branch from `branches.integration` when every dependency is merged, otherwise from the dependency step's branch. Reuse the branch if it already exists.

## 3. Implement

Skip this section if `--implemented` is given; the caller has already done it.

- Follow the issue's "Implementation notes" first. If they say another procedure or skill does the implementation, use it.
- Write the tests `docs.rules` requires together with the code.
- `tdd-loop` bundle, or `test-first` in `verification.base`: work red → green → refactor. Write the failing test first and run it. Before writing any implementation, `comment` a `### Red` log with the command and the failing test name. Then make it pass, then refactor with the tests green.
- Design step: write no code. Change only `docs.architecture`, its sub-documents, or the design note.

## 4. Loop

The mode is `--mode` if given, otherwise `mode` in `GROUNDWORK.md`. It sets the round limit and what reruns; see Modes in `reference/config.md`. Log the mode in round 1.

Repeat for round `r = 1` up to the mode's limit:

1. **Verify.** Run the `verification.commands` the change affects. Verification failures do not count as a round. A design step skips this.
   - When the change touches `verification.ui_paths`, run only the UI tests that cover the changed screens with `verification.ui_tests.targeted`. The full suite runs once in step 5.
   - `sport` runs the full suite every round.
   - Each changed screen needs a UI test that attaches a screenshot. Write or extend those tests with the code, then open the attached screenshots yourself and check that the screen renders as the task requires: nothing missing, overlapping, or clipped. Do not launch a separate QA or UX agent; those run only in release QA (`reference/config.md`).
   - Update the UI coverage ledger (`verification.ui_coverage`) for every screen you changed: a row per check, the test that covers it, or for a check no test can make, the reason in "Why QA must look" and Last verified `stale`.
     A check may go to "Why QA must look" only when no UI test can make it, after considering all three ways: asserting a value (sizes, frames, visibility, text), launching with a different condition (dark appearance, largest text size, locale, an empty or error state), and attaching a screenshot that the implementer opens. The reason must say why each of the three fails. What remains is human judgment: whether wording reads naturally, whether a flow feels easy, how an animation feels. Write the test instead whenever one of the three works.
   - In round 2 or later, skip UI tests when the fixes since the last pass touch nothing under `verification.ui_paths`. Log them as `not rerun — no UI change since round <r>`.
   - Add-ons in `verification.addons` add checks here. `design-fidelity`: re-measure the changed screens against `verification.design_source`. `api-contract`, `visual-regression`, and any other add-on: run its check. For each, follow the rules for that add-on in `docs.rules`.
2. **Review.** Invoke `/groundwork:review` in local mode with `--only` set to the reviewers in `review.reviewers`. From round 2 in `normal`, narrow `--only` to the reviewers that raised a confirmed 🔴/🟠 in the previous round. For a design step, the review covers the document.
3. **Decide.**
   - A required check is blocked and cannot be unblocked within the authorized scope (for example no simulator) → report the blocker and stop without marking the step complete. Do not spend rounds repeating unchanged blocked checks.
   - Verification passed (including UI tests and your look at their screenshots for changed screens), and no confirmed 🔴/🟠 → go to step 5.
   - Otherwise fix only the confirmed 🔴/🟠. Leave 🟡, nits, and UNVERIFIED items for the log.
   - If the report has trade-offs or high-impact UNVERIFIED items, ask the user before acting on them.
4. **Log** the round with `comment`:

```markdown
### Round <r>
- Verify: <pass / what failed and how it was fixed / not applicable>
- Screens: <screenshots inspected and what they showed / not applicable / not rerun> — <screenshot paths>
- Review: 🔴 <n> / 🟠 <n> / 🟡 <n> confirmed
- Fixed: <one line per fixed finding>
- Left: <🟡, nits, UNVERIFIED — one line each>
```

If the last allowed round ends with confirmed 🔴/🟠 still open, stop and ask the user how to proceed. In `eco`, fix the round-1 findings, verify, and then report anything you could not confirm as fixed instead of reviewing again.

## 5. Finish

1. If the step changed anything under `verification.ui_paths`, run `verification.ui_tests.full` once. A failure sends you back to step 4 and counts as a verification failure, not a round.
2. Design step: show the user the document and the review result, and stop until they approve it. Their requested changes go back to step 4.
3. Tick the satisfied "Done when" boxes in the issue body with `update_body`.
4. If the step produced a decision that later steps need, append it to the parent's "Decisions" with `update_body`. Structural decisions go into `docs.architecture` or its sub-documents instead.
5. `comment` a closing note: what was done, anything left, the branch name.
6. Commits and pushes happen only when the user asks. Offer a commit and a PR whose body includes `closes(id)`.
7. `set_state(id, done)`. With `ci-gate` in `verification.base`, the step is done only after the PR's CI passes. Once the user has asked for the push and PR, wait on the checks the way `/groundwork:autoland` does. Do not merge unless `workflow.autoland` is true. Until CI passes, leave the state `in_progress`.
8. If `workflow.autoland` is true and the PR exists, offer to hand over to `/groundwork:autoland`.
