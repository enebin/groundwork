# Rendered review procedure

The shared procedure for reviewers that exercise the running product: `ui-qa` and `ux-persona-reviewer`. They run according to Screen checks in `reference/config.md` or on explicit request. `qa.bundle` and `ux.bundle` control timing; the effective overall mode controls change-scoped coverage. Each agent's own file says what it judges. `ux-journey-tester` does not read this file: it must not read the project, so the `ux-journey` skill applies these rules for it. This file says how to establish the target, keep the environment safe, collect evidence, stay independent, and report.

`ui-qa` judges the rendered UI against the task's requirements and the design source. `ux-persona-reviewer` judges how easily one persona understands and completes its tasks. Both inspect what a user actually sees; neither reviews code.

## Before you start

Read `GROUNDWORK.md` at the repository root. Take `docs.rules`, `docs.architecture` (if set), `project.kind`, `project.stack`, and `verification` (`ui_tests`, `ui_paths`, `design_source`, `addons`, `ui_coverage`) from its frontmatter, and the `## UI QA notes` section from its body. UI QA notes hold everything project-specific: how to build and launch the app, sample data and backends, launch flags or modes, test fixtures, and screen-specific checks. If launching needs a value that neither the notes nor the assignment supplies, report it as a blocker instead of guessing.

Read the parts of the rules and architecture documents that describe the affected screens. Use product overviews for context, not as proof that a historical limitation still exists.

## Establish the target

Use the worktree, requirements, and design source the caller assigned. Inspect the diff and sample call sites only to select affected screens and states.

Record provenance: branch and commit, whether the tree is dirty, the build or server it came from, and the result paths. Confirm the build or running server was produced from the assigned worktree after the latest relevant edits. Reuse a running server only if it serves this worktree at its current state. Never present a passing run or a screenshot from an older build as evidence for the current code.

Record the environment as well:

- **Native apps:** device or simulator/emulator model and OS, its identifier, appearance (light or dark), locale, and any launch mode the UI QA notes define.
- **Web:** app and API URLs, browser, viewport sizes, theme, and the test account or dataset used.

## Environment isolation

Rendered reviewers often run at the same time as each other and as the implementation agent. Never share a mutable environment.

- **Native apps.** Run one UI driver per device at a time. Use the assigned device by its identifier. If another session is using it, create or obtain a separate device; do not terminate the other session. With desktop UI tools, select the window of that exact device before interacting. Tell the caller which device you used, and restore appearance or other device settings you changed.
- **Web.** Use your own browser context and artifact directory. Any action that creates, edits, or deletes data, or resets fixtures, needs its own database or dataset and its own server configuration. Different ports or tabs alone do not isolate a shared default test database. When `verification.addons` contains `isolated-e2e`, a separate test database and separate ports per reviewer are required, not optional. Read the test configuration and fixtures named in the UI QA notes before running end-to-end tests, and verify who owns any server you reuse.
- **Data.** Use local, synthetic test data and test credentials only. Never reset an unknown or production database, call live integrations or remote production APIs, or use real personal records.

If safe isolated interaction cannot be established, mark the affected checks BLOCKED. Do not silently share mutable state, run two drivers on one device or context, or switch to another backend to get a pass.

## Exercise and inspect

Your checks are the assignment's list: the ledger rows, screens, and appearance conditions the caller selected. State them before running them. Add a check only when the changed code directly puts it at risk, and give that reason in the report. With `--full`, check every ledger row without an automated test, `stale` rows first.

Do not re-check what a passing automated UI test in the supplied results already covers.

When a new or changed screen has no ledger rows yet, write them from these typical checks, keeping only those the change affects:

- **Layout at rest.** The first and last items, headers, footers, banners, and input bars do not overlap or clip once scrolling stops. Content passing behind a translucent bar during a deliberate scroll differs from an item staying hidden at rest.
- **Insets and keyboards.** Safe areas and system bars, the keyboard shown and hidden, interactive dismissal, and reaching the newest or last item.
- **Scrolling and loading.** Loading more content, keeping the visible anchor, pull-to-refresh, and reveal of loading or retry controls.
- **Responsive layout.** For web and adaptive layouts, a phone width and a desktop or tablet width with actual sizes recorded, both sides of any changed breakpoint, horizontal overflow, modal and sheet reachability, focus order, and keyboard access.
- **Appearance.** Light and dark modes or theme variants, short and long or multiline content, host customization points next to defaults.
- **States.** Loading, empty, error and retry, offline or disconnected, permission denied, attachments or streamed content.
- **Demos and previews.** A simulated preview does not prove the real flow works.

Add the screen-specific checks listed in the UI QA notes.

### Reuse test results

Run each UI test once per build. When the caller supplies UI test results (for example an `.xcresult` bundle or a Playwright report) whose commit and dirty state match the target, use them and do not rerun those tests. Run only relevant tests they do not cover, using the targeted command in `verification.ui_tests.targeted`. Do not run the full suite unless the assignment asks for it.

### Evidence

Open every screenshot you rely on and inspect it yourself. Prefer the screenshots the UI tests already attached. Take a new one only for a row that needs it: one per row and condition, and settle animations and transitions first so you do not retake it. Passing element-existence assertions or a successful build do not establish visual correctness. Use the available UI tools for interactions no test covers.

When a design source supplies geometry, colors, or tokens, read the actual values and compare matching elements. Do not infer exact spacing or colors from pixels. A screenshot can still prove a visible overlap without exact measurements; state that limit. If exact matching is required and the values are unavailable, the check stays unverified.

If a relevant regression has no automated coverage, describe the missing test for the implementation agent.

## Coverage ledger

The implementing skill writes the ledger rows; `ui-qa` updates Last verified on the rows it checked and adds a row for any uncovered check it finds missing. Create the file with its header row if it does not exist. For each row you checked that a UI test could cover, propose the test in the report: name, steps, and assertion. `ux-persona-reviewer` does not edit the ledger.

## Independence

Do not modify application, test, project, configuration, design, or agent files. The one exception is the coverage ledger, which only `ui-qa` edits. Build products, temporary files, logs, screenshots, traces, and reports go outside tracked source. Generated project files may be produced only as the UI QA notes instruct. Do not commit or push. Do not delegate the review again or invoke the dispatcher that launched you.

Do not disable assertions, skip a failing required check, or substitute a different backend or dataset to obtain a pass. Distinguish a product defect from a broken test setup or an environment failure, and keep the evidence of the failure.

For an artifacts-only assignment (screenshots supplied, nothing to launch), inspect the images but label the coverage as artifacts-only. Do not claim you launched the app, exercised flows, or verified the current build.

## Report

Lead with the agent's status line: `UI QA: <status>` or `UX Review: <status>`, with one of:

- **PASS:** every required check ran against the target build, the screenshots were opened and inspected, and no unresolved defect or evidenced obstacle remains.
- **FAIL:** a defect or evidenced obstacle is visible or reproducible. Report completed checks and any blocked coverage too.
- **BLOCKED:** no defect is established, but required execution or evidence is missing. Missing tools, an unverified server, or an absence of findings is not a pass.

A reviewer whose assigned scope is not affected reports `NOT APPLICABLE` with the concrete reason instead of inventing checks.

Then include:

1. **Target and environment,** with any provenance limits.
2. **Coverage:** each required check marked PASS, FAIL, or NOT RUN, with a reason for NOT RUN.
3. **Defects:** severity (🔴/🟠/🟡 as defined in `reference/config.md`; usability obstacles use `ux/heuristics.md`), screen and state, reproduction steps, expected versus actual behavior, impact, and an absolute screenshot path. Add observed coordinates when useful. Keep design preferences separate from defects, and label a suspected code cause as an inference.
4. **Evidence:** absolute paths to screenshots, logs, traces, and test results, and which checks each supports. Keep raw screenshots intact. Private references the user supplied stay outside the repository.
5. **Blockers,** workarounds used, and unverified assumptions. If none, say so briefly.

After the implementation agent changes code, verify the changed behavior again on a fresh build and rerun the checks that fix touches. Never carry a previous PASS over new UI edits.
