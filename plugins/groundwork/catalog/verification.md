# Verification rule reference

Token cost levels are relative estimates within this step, not measurements.

Verification is no longer an onboarding choice. `reference/implementation.md` supplies mandatory implementation and test rules. This catalog preserves the existing `verification.base` and `verification.addons` values and their supplemental rule blocks for compatibility and manual customization. Onboarding derives applicable settings, presents them in the final preview, and writes supplemental rules to `docs.rules` in `language.artifacts`. Keep commands, paths, and code identifiers unchanged when translating.

## Commands come from the repository, not from this catalog

The rules below say *when* to verify. The commands that do it live in `verification.commands`, `verification.ui_tests`, and `verification.ui_paths` in `GROUNDWORK.md`.

- Onboarding detects them from the build manifest, CI config, and scripts (`package.json`, `Package.swift`, `pyproject.toml`, `Makefile`, `.github/workflows`, and the like), runs each one, and sets `verified: true` for those that pass.
- A command onboarding cannot run yet (empty repository, missing toolchain) is written with `verified: false`. `plan` then proposes a first scaffold step whose done criteria are that every command passes and is flipped to `verified: true`.
- No skill treats a `verified: false` command as proof of anything.

| Id | Kind | One line |
|---|---|---|
| `evidence` | base | Tests for state, targeted then full runs, screenshots, zero warnings, report what did not run |
| `ci-gate` | base | `evidence` plus: done only after the PR's CI passes |
| `test-first` | base | `evidence` plus: watch a test fail before implementing |
| `basic` | base | Build and tests pass; report what did not run |
| `design-fidelity` | add-on | Read values from the design source; never eyeball |
| `api-contract` | add-on | Documented public API, checked surface, compiling examples, deprecation path |
| `isolated-e2e` | add-on | Each concurrent agent gets its own test DB and ports |
| `visual-regression` | add-on | Baseline screenshots compared on every change |

## evidence

Summary: Every claim of "done" comes with evidence: tests for anything that holds state, targeted runs while fixing and one full run before finishing, screenshots for UI, zero compiler warnings, and an honest list of what could not run.

Pros:
- State bugs are caught by tests that name the input and the expected transition, not by manual poking.
- Targeted runs keep the fix loop fast; the single full run still catches regressions elsewhere.
- Sharing one UI test run between implementer and QA, tied to a commit and dirty state, removes duplicate multi-minute runs.
- "Could not run, because…" is reported instead of hidden, so a skipped check never reads as a pass.

Cons:
- Writing Given/When/Then tests for every state-holding type is real work on small changes.
- Provenance (commit + dirty state) must be recorded for every UI run, or the result cannot be reused.
- Zero warnings can force cleanup of warnings the change did not cause, the first time it is enforced.

Token cost: Medium — writing state tests, targeted runs while fixing, one full run, and inspecting screenshots.

Recommended when: almost always. This is the default base bundle.

### Rules to write

The mandatory block in `reference/implementation.md`. Onboarding writes that block for every project; there is no separate `evidence` block.

## ci-gate

Summary: `evidence`, plus the work is done only after the pull request's CI checks pass. Local green is necessary but not sufficient.

Pros:
- Catches "works on my machine" differences: clean checkout, other OS, other toolchain version, missing generated files.
- Gives `autoland` a real signal to merge on.
- The same gate applies to humans and agents.

Cons:
- Done waits on CI queue time; slow CI makes every step slow.
- Flaky CI blocks done for reasons unrelated to the change; someone must fix the flake, not retry until green.
- Needs CI that actually runs the tests. A CI that only lints gives false confidence.

Token cost: Medium — `evidence` plus polling CI and reading failure logs when a check fails.

Recommended when: the repository has CI that runs the full test suite, especially with `autoland` on.

### Rules to write

Write the block from `reference/implementation.md` first, then this one.

```markdown
### CI gate

- Work is done only after every CI check on its pull request has passed. Local verification is required first, but it does not replace CI.
- A PR with no CI checks is not done. Say so and ask; do not treat "no checks" as "checks passed".
- A failing or flaky check is fixed at its root cause. Do not rerun until green, skip the check, or mark it optional to get through.
- When CI fails and the same command passed locally, record the difference (environment, version, missing file) in the issue before fixing it.
```

## test-first

Summary: `evidence`, plus a failing test is observed before any implementation. The failure must be for the expected reason.

Pros:
- Every behavior has a test that has been seen to fail, so a test that can never fail is caught.
- Bug fixes ship with their reproduction.
- Pairs naturally with the `tdd-loop` workflow.

Cons:
- Hard to apply to visual and layout work, where the "test" is a screenshot and a design comparison.
- A failure from a missing symbol or a typo looks like red but proves nothing; the failure message must be checked.
- Adds a run before every implementation; slow suites make this expensive.

Token cost: High — `evidence` plus a red run and a read of the failure message before every behavior.

Recommended when: logic-heavy code, libraries, and bug-fix work; required with `tdd-loop`.

### Rules to write

Write the block from `reference/implementation.md` first, then this one.

```markdown
### Test first

- Before implementing a behavior or fixing a bug, write a test for it and run it. It must fail, and the failure message must show the missing behavior, not a compile error, a missing symbol, or a typo.
- Record the failing run (command and the failing assertion) in the work log before changing production code.
- Then make the test pass with the smallest change. Refactor only while all tests stay green.
- If a behavior cannot get a meaningful failing test first (pure layout, a third-party callback with no seam), say so in the work log and use rendered evidence instead.
```

## basic

Summary: The build passes and the tests pass. Report anything that could not run. Nothing more is required.

Pros:
- Lowest overhead; fits any repository on day one.
- No rules about test style or structure to argue about.

Cons:
- Nothing requires new tests, so "tests pass" can mean "no tests touched this".
- No rendered evidence for UI changes.
- Warnings and flaky checks pile up unnoticed.

Token cost: Low — run the commands once and report.

Recommended when: prototypes, scripts, and repositories with no test suite yet. Plan to move to `evidence` once the code has users.

### Rules to write

```markdown
### Verification

- Before declaring work done, run every command in `verification.commands`. All must pass.
- If any command could not run, say which one and why in the work result. Report it as unverified. Never report it as passed.
```

## design-fidelity (add-on)

Summary: Visual values (spacing, sizes, colors, type) are read from the design source, not estimated from a screenshot. After implementing, the same values are read again and compared. Asks for `verification.design_source`.

Pros:
- Removes the most common UI drift: paddings and sizes guessed by eye.
- Re-measuring after implementation catches off-by-a-few-points errors before review.
- Values the source lacks are recorded as "new", so the design reference stays the single place to look.

Cons:
- Requires a design source the agent can read values from (a design tool connection, exported specs, or a token table). Screenshots alone are not enough.
- Slower for small UI tweaks.
- Stops and asks when a value cannot be read, which interrupts autonomous runs.

Token cost: High — reading values for each element from the design source twice (before and after implementing).

Recommended when: the product has a real design source and pixel accuracy matters.

### Rules to write

```markdown
### Design fidelity

The design source is `verification.design_source`. When a task names another source, that one wins for the task.

- Read real values from the design source. Do not estimate them from a screenshot.
  - Read each element's x / y / width / height. Derive paddings and gaps from the coordinate difference between sibling elements.
  - Read colors and fonts from the source's token definitions, not from sampled pixels.
  - Match: horizontal and vertical padding, gaps between elements, fixed sizes (avatars, icons, badges), divider insets, font size and weight.
- After implementing, read the same elements again and compare. Where they differ, follow the source. If you keep a different value on purpose, give the reason in the PR body.
- A value the source does not have (a new state, a new screen, a loading or empty or error view) is built from the nearest existing component's tokens and values. Add it to the design reference marked "new", with the reason.
- If a value cannot be read, ask. Never fill in a color, font, or spacing by guessing.
- Do not write color or font literals in view code. Use the project's tokens or theme. When a token is missing, add it to the token source first.
```

## api-contract (add-on)

Summary: For libraries and SDKs. Every public symbol is documented with the version it appeared in, an automated check keeps the published API surface and its docs or catalog in agreement, example code compiles without warnings, and breaking changes go through deprecation.

Pros:
- Users (and their coding agents) can trust the docs, because a check fails when docs and API disagree.
- Examples that do not compile are caught before users copy them.
- Deprecation paths stop accidental breaking changes from shipping in a minor version.

Cons:
- Needs a surface-check tool for the stack (API extractor, symbol graph diff, generated catalog compare); building one is a step of its own.
- Every public change touches docs, the catalog, and examples in the same PR.
- Since-version tags must be kept right at release time.

Token cost: Medium — regenerating the docs or catalog and compiling examples on every public change.

Recommended when: `project.kind` is `library`, or anything other code depends on by version.

### Rules to write

```markdown
### Public API contract

- Every public symbol has a doc comment that says what it does, and a since-version tag (for example `- Since: 1.0.0`).
- An automated check compares the published API surface with the docs or component catalog. It runs in `verification.commands` and in CI. When a public symbol or its doc comment changes, regenerate the docs or catalog in the same PR.
- Example code that ships with the library (README, guides, catalog examples) compiles with zero warnings against the current source. A changed example is compiled before merge.
- Do not change the signature or access level of an existing public symbol. Add the new symbol, keep the old one working, and mark it deprecated with a pointer to the replacement. Remove it only in a major version.
- Things a user must do before a component works (registration, configuration keys, permissions) are written in that component's doc comment.
```

## isolated-e2e (add-on)

Summary: When more than one agent or reviewer runs end-to-end tests or drives the app at the same time, each gets its own test database and its own ports. Nobody resets a database they do not own, and no real personal data is used.

Pros:
- Parallel reviewers (for example two UX personas) stop corrupting each other's data.
- Removes the class of "test passed because another run created the record" results.
- Protects real data from a reset aimed at the wrong database.

Cons:
- Needs test config that takes the DB path and ports from the environment; older setups hard-code them.
- More processes and disk per run.
- When isolation cannot be set up, checks are reported as blocked instead of run, which slows sign-off.

Token cost: Low — mostly environment setup commands; little extra reading.

Recommended when: the app has a database and E2E or browser tests, and you run reviewers or worktrees in parallel.

### Rules to write

```markdown
### Isolated end-to-end runs

- Each concurrent agent, reviewer, or worktree that runs E2E tests or drives the app uses its own test database and its own free ports. Different ports alone do not isolate data: check which database the test config actually opens.
- Before reusing a running server, confirm it serves this worktree's current source and this run's database. Otherwise start your own.
- Never reset, migrate, or seed a database you did not create for this run. Never reset an unknown database or a production one. Reset endpoints are used only on the isolated test setup.
- Use synthetic data only. No real personal data, real accounts, live third-party services, or remote APIs.
- Do not stop another session's servers or share its mutable test data.
- If safe isolation cannot be set up, report the affected checks as blocked, with the reason. Do not share mutable state to get a result.
```

## visual-regression (add-on)

Summary: Baseline screenshots are stored in the repository and compared on every change with a tool fit for the stack. Baselines change only on purpose, and the change is reviewed in the PR.

Stack tools: iOS uses a snapshot-testing library; web uses Playwright `toHaveScreenshot`; other stacks use their equivalent.

Pros:
- Catches unintended visual changes no assertion covers: spacing, clipping, color, wrapping.
- The baseline diff in the PR shows reviewers exactly what moved.
- Cheap to run once set up.

Cons:
- Rendering differs across OS, simulator, browser, and font versions; baselines must be recorded on a pinned environment or they flake.
- Every intended UI change updates baselines, which adds image churn to PRs.
- Easy to approve a baseline update without looking; the rule only works if reviewers open the diff.
- Not yet run in the source projects; adopted from common practice.

Token cost: Medium — inspecting image diffs whenever baselines change; little when nothing visual moved.

Recommended when: UI is a large part of the product and visual mistakes have reached users before.

### Rules to write

```markdown
### Visual regression

- Screens and components in `verification.ui_paths` have baseline screenshots, compared on every change by the project's snapshot tool (iOS: a snapshot-testing library; web: Playwright `toHaveScreenshot`).
- Baselines are recorded on one pinned environment (device or browser, OS version, scale, locale, theme). Comparisons run on the same environment.
- Update a baseline only when the visual change is intended. Say which baselines changed and why in the PR body. Reviewers open the image diff before approving.
- A failing comparison is a failure. Do not raise the tolerance or re-record the baseline to make it pass without finding the cause.
```
