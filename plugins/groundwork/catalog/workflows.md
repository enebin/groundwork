# Workflow bundles

Token cost levels are relative estimates within this step, not measurements.

Onboarding shows these bundles as one choice and writes the id to `workflow.bundle`. Each bundle decides which skills drive the work and when review runs. The verification and review bundles are chosen separately and apply to every workflow.

| Id | Shape | Unit of work |
|---|---|---|
| `step-loop` | `plan` → `step` per sub-issue → `takeoff` | One sub-issue, one PR |
| `design-first` | `plan` with an approved design step first, then `step` | One sub-issue, one PR |
| `quick` | implement → `review-and-fix` → `commit-push` | The current branch |
| `tdd-loop` | `step-loop` where each step runs red → green → refactor | One sub-issue, one PR |
| `review-only` | The human writes code; `review` / `ui-qa` / `ux-review` on demand | Whatever the human asks about |

## step-loop

Summary: Split a job into sub-issues with `plan`, then run each one with `step`: implement, then verify → review → fix until no confirmed 🔴/🟠 remains, logging every round on the issue.

Skills: `plan` → `step` (per sub-issue) → `takeoff` when the user asks for a push. `step` calls `review`, then applies the screen checks after final verification. `step` also runs a standalone issue that has no parent. After the merge, `landing` cleans up; `autoland` merges and cleans up by itself when it is on.

Fits:
- Jobs that take several PRs and several sessions.
- Work where a new session must pick up from the issue alone.
- Teams that want every round of review on the record.

Does not fit:
- One-line fixes and typo PRs. The planning and logging cost more than the change.
- Spikes where the goal is still unknown. There is nothing to split yet.

Pros:
- The issue holds decisions, rounds, and what was left, so a fresh session continues without the old chat.
- A step is one PR a reviewer reads in one sitting, so review findings stay concrete.
- The loop stops after 3 rounds with 🔴/🟠 still open and asks, instead of looping forever.
- 🟡 and nits are logged, not fixed, so a step does not grow during review.

Cons:
- Each step pays a full verify + review cycle; small steps feel slow.
- Splitting well takes judgment; a bad split shows up as steps that cannot build alone.
- Many small PRs mean many merges; stacked steps need care when the base step is squash-merged.

Token cost: High — every step pays issue reads, implementation, a full verify, and up to 3 review rounds with all configured reviewers, plus a round log on the issue.

Recommended when: the work is bigger than one PR and you want an agent to carry it across sessions. This is the default.

## design-first

Summary: `step-loop` with a gate in front. `plan` makes the first step a design step that changes `docs.architecture` or adds a design note. Every other step depends on it, and it is done only when the user approves the document.

Skills: `plan` (design step first) → `step` on the design step (document review, then user approval) → `step` per remaining sub-issue.

Fits:
- New features that change structure, public API, data shape, or a contract with another system.
- Greenfield repositories where the first decisions are expensive to undo.
- Work several people will build on, where agreeing on the shape first saves rework.

Does not fit:
- Bug fixes and changes inside an existing, documented structure.
- Exploratory work where the design only becomes clear by writing code.

Pros:
- Structure is argued once, in a document, before code locks it in.
- Later steps implement an approved design instead of inventing one each.
- The architecture doc stays current, because changing it is the first step.

Cons:
- Nothing ships until the user approves the design; an idle approver blocks the whole job.
- Design documents can drift into speculation; the reviewers must hold them to the current requirement.
- A design that turns out wrong mid-job needs a new design step, not a quiet code change.

Token cost: High — the `step-loop` cost plus a design step that adds at least one document review round and an approval wait before any code.

Recommended when: the job changes structure or a public contract, or the repository is new.

## quick

Summary: Write the change on the current branch, run `review-and-fix` to review the local diff and fix what it finds, then `commit-push`. No issue split, no worktree, no round log.

Skills: implement (directly, no skill) → `review-and-fix` → `commit-push`.

Fits:
- Solo projects and small fixes.
- Repositories without a tracker habit.
- Changes that fit in one sitting and one commit or two.

Does not fit:
- Work that spans sessions; nothing records where you stopped.
- Shared integration branches with strict review requirements.
- Large UI changes that need more planning than the quick workflow provides; screen checks still follow their own setting.

Pros:
- Lowest ceremony; the fix and its review land in minutes.
- Review is still independent of the author, so obvious bugs are caught.
- `review-and-fix` takes a minimum severity, so you choose how much it fixes.

Cons:
- No history beyond commit messages; a later session cannot see why a choice was made.
- Review and fix happen in one pass, so the fixer also judges its own fixes.
- `commit-push` pushes without a separate confirmation; a wrong branch check is the only guard.
- Easy to keep using after the project has outgrown it.

Token cost: Low — one `review-and-fix` pass over the local diff; no planning and no tracker reads or writes.

Recommended when: you work alone on small changes and want review without process.

## tdd-loop

Summary: `step-loop`, but each step is built red → green → refactor. Before implementing, write a test for the step's behavior and watch it fail for the expected reason. Then make it pass with the smallest change, then clean up with the tests green.

Skills: `plan` → `step`, with the red → green → refactor cycle inside the implement phase. Onboarding automatically installs the test-first implementation rules.

Fits:
- Logic with clear inputs and outputs: parsers, state machines, pricing, scheduling rules.
- Bug fixes, where the failing test is the reproduction.
- Libraries whose behavior is the product.

Does not fit:
- Visual work, where the "test" is a rendered screenshot and design review.
- Prototypes whose behavior is not decided yet.
- Code that is mostly glue to external systems with no test seam.

Pros:
- Every behavior has a test that was seen to fail, so tests that pass vacuously are caught early.
- Bug fixes come with their reproduction.
- Smaller, more focused implementations, because code is written to make one test pass.

Cons:
- Slower for UI and integration-heavy steps, where a meaningful failing test is hard to write first.
- The agent can write a test that fails for the wrong reason (missing symbol, typo); the red step must check the failure message.
- Untested in the source projects as a full workflow; adopted from common practice.

Token cost: High — the `step-loop` cost plus a red test run and failure check before each behavior, and a refactor pass after it.

Recommended when: the work is logic-heavy and you value tests as specification.

## review-only

Summary: The human writes the code. The plugin does not plan, implement, branch, commit, or push. It runs `review`, `ui-qa`, or `ux-review` when asked and reports.

Skills: `review` (code reviewers from `review.reviewers`), `ui-qa`, `ux-review`. All on demand.

Fits:
- People who want to keep writing code themselves.
- Teams trying the plugin before letting an agent change code.
- Repositories where agent commits are not allowed.

Does not fit:
- Anyone who wants the agent to carry work to done.

Pros:
- No change to how you work; the plugin only adds independent reviewers.
- Nothing is changed without you; reports only.
- The same reviewers, severity scale, and skeptic pass as the other bundles.

Cons:
- Findings are only as useful as your follow-through; nothing tracks whether they were fixed.
- No done criteria are enforced.

Token cost: Low — runs only when asked; each request costs what the configured reviewers cost.

Recommended when: you want reviewers, not an implementer.

## Follow-up: autoland

Asked after the workflow choice, for `step-loop`, `design-first`, and `tdd-loop`. Writes `workflow.autoland`.

Skipped for `quick` (it pushes to the current branch and opens no PR) and `review-only` (the plugin opens no PR). Both get `autoland: false`.

Question: "After a PR is opened, should the plugin wait for CI and merge it by itself when every check passes?"

Default: **No.**

Reason for the default: CI only proves what the tests cover. Agent review is not the same as a person reading the diff, and auto-merge removes the last moment a person looks before the change reaches the integration branch. Turn it on once you trust the verification and review setup in this repository.

When `true`, autoland follows these rules:
- Merge only when there is at least one check and every check passed. Pending, skipped, failed, cancelled, or timed-out checks stop it.
- Re-read the PR right before merging. If it is closed, a draft, aimed at another base, or its head commit changed, stop.
- Merge with `branches.merge` and pin the head commit. Never use admin overrides, never bypass branch protection or required reviews, never force-push.
- Then run `landing`, and list the visible changes the user should check by hand.

## Follow-up: worktree

Asked after the workflow choice, for `step-loop`, `design-first`, and `tdd-loop`. Writes `workflow.worktree`. `quick` and `review-only` get `false`.

Question: "Work on each issue in its own worktree?"

Default: **Yes.**

When `true`, `step` creates `.groundwork/worktrees/<branch>` for the issue and works there, so several steps can run in parallel without touching the main checkout. `rejoin` moves a branch back to the main checkout, and `landing` removes the worktree after the merge.

Reason for the default: the main checkout stays clean, and steps can run in parallel without touching each other. The cost is a dependency install, build cache, and editor index per worktree. Turn it off when your tools, such as editors and agent apps that start each session in its own worktree, already isolate parallel work.
