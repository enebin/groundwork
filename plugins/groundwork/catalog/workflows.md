# Workflow bundles

Token cost levels are relative estimates within this step, not measurements.

Onboarding shows these bundles as one choice and writes the id to `workflow.bundle`. Each bundle decides which skills drive the work and when review runs. The verification and review bundles are chosen separately and apply to every workflow.

| Id | Shape | Unit of work |
|---|---|---|
| `step-loop` | `plan` → `step` per sub-issue | One sub-issue, one PR |
| `flight` | `boarding` → `door-closing` → `taxiing` → `takeoff` → `landing` | One issue, one worktree, one PR |
| `design-first` | `plan` with an approved design step first, then `step` | One sub-issue, one PR |
| `quick` | implement → `review-and-fix` → `commit-push` | The current branch |
| `tdd-loop` | `step-loop` where each step runs red → green → refactor | One sub-issue, one PR |
| `review-only` | The human writes code; `review` / `ui-qa` / `ux-review` on demand | Whatever the human asks about |

## step-loop

Summary: Split a job into sub-issues with `plan`, then run each one with `step`: implement, then verify → review → fix until no confirmed 🔴/🟠 remains, logging every round on the issue.

Skills: `plan` → `step` (per sub-issue). `step` calls `review`, then applies the separate QA policy after final verification.

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

## flight

Summary: One issue flies through fixed stages. Each stage caches its output on disk, so rerunning a later stage skips the stages already done. Only `takeoff` touches the remote.

Skills:
- `boarding`: read the issue, write a requirement summary and the code it touches. No code or git changes.
- `door-closing`: update the integration branch, create a worktree, write `plan.md`. No code changes.
- `taxiing`: implement the plan in the worktree with intermediate commits. No push, no PR.
- `takeoff`: rebase on the integration branch, push, open the PR. Runs review first when `review.trigger` is `per-implementation`.
- `landing`: after the PR merges, remove the worktree, update the integration branch, delete the local branch. Always run by hand.
- `rejoin`: leave the worktree and keep the branch as a local branch in the main checkout, rebased on the integration branch. For switching context without losing work.
- `release`: open a release PR from the integration branch to the production branch (only with `branches.strategy: develop-release`).
- `autoland`: after `takeoff`, wait for CI, merge when every check passes, then run `landing`. Only when `workflow.autoland` is `true`.

Each later stage chains the earlier ones it still needs. Stage state lives under the main checkout, so every worktree sees it.

Fits:
- A steady stream of issue-sized tasks (one issue, one PR).
- Repositories where several agents work in parallel worktrees.
- Teams that want a hard line between local work and remote side effects.

Does not fit:
- Jobs that need several PRs. Use `step-loop` or `design-first`; flight has no parent/child split.
- Repositories that cannot run in a second worktree (heavy per-checkout setup, local-only secrets).

Pros:
- Remote side effects happen in exactly one stage, so a mistake before `takeoff` stays local.
- Stages are resumable; a crash in `taxiing` does not redo `boarding`.
- Worktrees keep parallel tasks apart and leave the main checkout clean.
- `rejoin` gives a way out of a worktree without pushing half-done work.

Cons:
- Each worktree needs its own dependency install, build cache, and IDE index.
- Five stage names to learn; the metaphor helps some people and confuses others.
- Review happens once, at the end, unless the user runs it more often; there is no round log on the issue.
- Rebase conflicts at `takeoff` stop the flow and need a human.

Token cost: Medium — review runs once per implementation (at `takeoff`) instead of every round; resumed stages re-read cached files instead of redoing work.

Recommended when: most work items are single-PR issues and you run more than one task at a time.

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
- Large UI changes that need more planning than the quick workflow provides; QA still follows its separate policy.

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

Asked after the workflow choice, for `step-loop`, `flight`, `design-first`, and `tdd-loop`. Writes `workflow.autoland`.

Skipped for `quick` (it pushes to the current branch and opens no PR) and `review-only` (the plugin opens no PR). Both get `autoland: false`.

Question: "After a PR is opened, should the plugin wait for CI and merge it by itself when every check passes?"

Default: **No.**

Reason for the default: CI only proves what the tests cover. Agent review is not the same as a person reading the diff, and auto-merge removes the last moment a person looks before the change reaches the integration branch. Turn it on once you trust the verification and review setup in this repository.

When `true`, autoland follows these rules:
- Merge only when there is at least one check and every check passed. Pending, skipped, failed, cancelled, or timed-out checks stop it.
- Re-read the PR right before merging. If it is closed, a draft, aimed at another base, or its head commit changed, stop.
- Merge with `branches.merge` and pin the head commit. Never use admin overrides, never bypass branch protection or required reviews, never force-push.
- Then run `landing`, and list the visible changes the user should check by hand.
