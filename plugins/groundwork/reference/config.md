# GROUNDWORK.md contract

Every groundwork skill reads `GROUNDWORK.md` at the repository root before doing anything else. The `onboarding` skill writes it. This document is the single definition of its shape.

If `GROUNDWORK.md` is missing, stop and tell the user to run `/groundwork:onboarding`. Never guess a value that the file should hold.

If a key a skill needs is missing, stop and name the key. Do not fall back to a default silently.

## Compatibility

The file is a public contract: other people's repositories hold it. Before 1.0, a beta release may still change a value's meaning; the release notes say so, and `onboarding` migrates the file. Keys are only ever added. A key is never renamed or removed, and a value never changes meaning. When a breaking change is unavoidable, bump `groundwork` (the schema version) and teach `onboarding` to migrate the old shape. `update` applies migrations and new features release by release, from `plugin_version` to the installed plugin version, without repeating onboarding. A skill that reads a `groundwork` version newer than it knows stops and asks the user to update the plugin.

## Shape

YAML frontmatter holds values. The Markdown body holds prose that a value cannot express.

```yaml
---
groundwork: 1
plugin_version: 0.2.0             # plugin version that last wrote this file; onboarding and update set it

language:
  conversation: ko          # language for talking to the user
  artifacts: en             # commits, issues, code comments, work logs

project:
  summary: "SwiftUI iOS habit tracker"   # the user's own words from onboarding
  stack: [swift, swiftui, ios]           # free-form tags used to filter catalog entries
  kind: app                              # app | library | service | tool

docs:
  rules: AGENTS.md                       # working rules; groundwork writes chosen rule sets here
  architecture: ARCHITECTURE.md          # always present; holds minimal-structure, plus the bundle contract unless the bundle is none

tracker:
  type: local                            # local | github | linear | jira
  # local:  path: .groundwork/issues     shared: false   (false = gitignored)   keep: true   (false = delete an issue file once its PR merges)
  # github: owner: <owner>  repo: <repo>  project: <number>
  # linear: team: <key>  project: <name>
  # jira:   site: <host>  project: <key>  step_type: subtask | child

workflow:
  bundle: step-loop                      # step-loop | design-first | quick | tdd-loop | review-only (flight: removed; onboarding migrates it)
  autoland: false                        # merge automatically once CI passes (not for quick / review-only)
  worktree: true                         # true = step works in .groundwork/worktrees/<branch> (step-loop, design-first, tdd-loop)

branches:
  strategy: develop-release              # develop-release | main-only
  integration: develop                   # branch that work branches start from and merge into
  production: main
  work_prefix: step                      # work branches are <work_prefix>/<issue-id>-<slug>
  merge: squash                          # squash | merge | rebase — how PRs land on the integration branch

verification:
  base: evidence                         # automatic implementation policy; legacy values: evidence | ci-gate | test-first | basic
  addons: []                             # design-fidelity | api-contract | isolated-e2e | visual-regression
  commands:
    - name: Build
      run: "<command>"
      verified: false                    # true once the command has passed in this repository
  ui_paths: []                           # paths whose change requires UI tests with screenshots
  ui_tests:
    targeted: "<command with {test} placeholder>"
    full: "<command>"
  design_source: null                    # path or URL of the design source, when design-fidelity is on
  ui_coverage: docs/ui-coverage.md       # UI coverage ledger, committed; present when the project has screens

architecture:
  bundle: unidirectional                 # unidirectional | mvvm | layered-service | layered-web | none

review:
  bundle: app                            # app | sdk | product | light
  reviewers: [architecture, code-quality]
  release_qa: false                      # compatibility mirror: qa.bundle != manual; used only when qa is absent
  skeptic: blocking                      # blocking (🔴/🟠 only) | all (every non-nit finding)
  trigger: per-round                     # per-round | per-implementation | on-request
  personas:
    - name: "Habit tracker user"
      goal: "Record today's habits in a few taps"
      kind: user                         # user (end user of the product) | developer (builds on its API, library, or CLI); default user

qa:
  bundle: manual                         # manual | release | continuous — when ui-qa runs on the running app

ux:
  bundle: continuous                     # manual | release | continuous — when the UX check runs
  method: code                           # code (ux-flow-reviewer reads the code) | app (ux-persona-reviewer uses the running app)
  journey: manual                        # manual | release — when the ux-journey add-on runs; optional, absent means manual

mode: normal                             # eco | normal | sport — overall effort for verification, review, and screen checks
---
```

## Body sections

Optional. Skills read only the section that applies to them.

- `## Review focus: <reviewer>` — repository-specific checks for one reviewer, such as `## Review focus: architecture`. The reviewer adds these to its own checklist. They narrow where to look; the documents in `docs` stay the standard.
- `## Persona: <name>` — the tasks a UX persona performs, when `review.personas[].goal` is not enough.
- `## Journey: <name>` — an end-to-end journey for the `ux-journey` add-on: persona, devices, start, precondition, scenario, test access, reset, milestones, success, code map, continues from, profiles, and slips. The format is in `skills/ux-journey/references/journey-test.md`.
- `## Release checks` — checks the `release` skill runs before cutting a release, beyond its built-in ones.
- `## UI QA notes` — how to launch the app for QA, sample data, launch flags, screen-specific checks.
- `## Notes` — anything else the user added during onboarding that applies to every skill.
- `## Add-ons` — optional setup choices from `catalog/addons.md`, inside the managed `addons` block. Links to feature settings and actual scheduler state, never credentials. Missing means no recorded setup; all bundled add-on skills remain available on demand. This is separate from `verification.addons`.

## Value meanings

### Reviewer keys

| Key | Agent | Looks at |
|---|---|---|
| `architecture` | `architecture-reviewer` | Layers, coupling, boundaries, the chosen architecture bundle |
| `code-quality` | `code-quality-reviewer` | Correctness, readability, cost, tests |
| `security` | `security-reviewer` | Authorization, data isolation, personal data, untrusted input |
| `writing` | `writing-reviewer` | User-facing copy, terminology, accuracy against behavior |
| `dx` | `dx-reviewer` | Developer experience of a library API, HTTP or RPC API, or command-line tool, traced through `developer` personas' tasks |
| `ux` | `ux-flow-reviewer` | Whether each `user` persona can finish its tasks in the app, traced through the code |

All of these read code. Every key except `ux` runs on every change when listed in `review.reviewers`. `ux` is never listed there, except in a legacy file without a `ux` mapping (see Screen checks compatibility): it runs in a review when a present `ux` mapping is `ux.bundle: continuous` with `ux.method: code`, and `/groundwork:review --only ux` runs it on request. The agents that exercise the running app, `ui-qa` and `ux-persona-reviewer`, are not reviewer keys: they run according to the screen checks below, or when the user calls `/groundwork:ui-qa` or `/groundwork:ux-review` directly.

The `fixer` agent is not a reviewer either: the `step` skill hands it each round's confirmed findings, so fixes and their test runs stay out of the step's own context.

In Claude Code the agents are registered as `groundwork:<agent>`. In Codex, spawn a fresh subagent and tell it to read and follow `agents/<agent>.md` under the plugin root.

### Review bundles

| Bundle | Reviewers | Skeptic |
|---|---|---|
| `app` | architecture, code-quality | blocking |
| `sdk` | architecture, code-quality, dx | blocking |
| `service` | architecture, code-quality, security, dx | blocking |
| `product` | architecture, code-quality, security, writing (+ dx when it exposes a public API) | all |
| `light` | code-quality | blocking |

`review.reviewers` is the source of truth after onboarding. The bundle name records where the list came from. `architecture` is dropped from any bundle when `architecture.bundle` is `none`, because the reviewer has no standard to judge against.

### Modes

`mode` is an overall effort preset for implementation verification, review, and screen checks, like a reasoning-effort setting. It never chooses a model. Reviewers, the Skeptic policy, mandatory implementation rules, and the chosen screen-check frequencies stay as configured. Implementation and QA skills accept `--mode <mode>` for one run and forward the resolved value to nested skills and agents. Validate eco, normal, or sport; absent an override, use the configured `mode`. The default is normal. Users can edit individual policies later instead of using the preset.

| | `eco` | `normal` | `sport` |
|---|---|---|---|
| Review rounds, at most | 1 | 3 | 3 |
| Who reviews again from round 2 | — (fixes are checked by verification only) | reviewers that raised a confirmed 🔴/🟠 | every reviewer |
| What round 2+ reviews | — | only the fixes since the last review | the whole change |
| UI tests | changed screens; full suite at finish | changed screens; full suite at finish | full suite every round |
| Screen checks for one change, when triggered | only screens the change may affect; QA only on the running app | only screens and user tasks the change may affect | everything: every uncovered screen and every user-persona task |

In every mode, each changed screen needs a UI test that attaches a screenshot, and the agent that changed the screen opens those screenshots before declaring done: the step itself while implementing, the `fixer` agent for review fixes. In `eco`, a 🔴/🟠 left after round 1's fixes are verified is reported to the user rather than reviewed again.

### Default implementation policy

Onboarding writes `reference/implementation.md` into `docs.rules` for every project. Tests, build/test execution, UI screenshot inspection, and honest reporting of blocked checks are implementation requirements, not a QA-strength choice. The `verification` keys continue to describe commands and supplemental rules. CI gates and test-first rules remain additional requirements when configured.

### Screen checks

`qa` and `ux` are set together in onboarding step 7; their bundles and cost guidance are in `catalog/screen-checks.md`. QA always runs `ui-qa` on the running app. UX runs by `ux.method`: `code` runs one `ux-flow-reviewer`, which reads the code and never launches the app; `app` runs one `ux-persona-reviewer` per `user` persona on the running app. `/groundwork:ux-review` runs whichever the method names. `reference/ux-checks.md` compares these with the journey test.

The journey test (`/groundwork:ux-journey`, one `ux-journey-tester` per session) is an add-on, not a screen-check bundle. `ux.journey` decides only whether it gates releases: `manual` or absent runs it on request; `release` adds it to the before-release gate. It never runs after implementation, because each session walks a whole journey from a clean state.

| Bundle | After implementation | Before release |
|---|---|---|
| manual | only on request | human checklist; agents only on request |
| release | only on request | full check |
| continuous | code-based UX: in every review round; on the running app: once, scope from effective mode | full check |

**Compatibility:** when the entire `qa` mapping is absent in a schema-1 file, explicitly report the legacy mapping: `review.release_qa: false` means manual, true means release. If that legacy key is also absent, stop. A present but missing/unknown `qa.bundle` is an error, not a legacy fallback.

When the entire `ux` mapping is absent, the file keeps its old UX triggers until onboarding migrates it; explicitly report that it is running on legacy UX behavior. A `ux` listed in `review.reviewers` runs as a reviewer in every review round. The check on the running app follows the resolved QA bundle: skills resolve it as `ux.bundle` equal to that QA bundle with `ux.method: app`, and it runs only when at least one `user` persona exists. A present `ux` mapping with a missing or unknown value is an error.

Onboarding writes both mappings and migrates the old UX triggers. `ux` in `review.reviewers` becomes `ux.bundle: continuous` with `ux.method: code`. Otherwise, a QA bundle of release or continuous with at least one `user` persona becomes the same bundle with `ux.method: app`. Otherwise it becomes manual with `code`. When both old triggers were on, one `ux.method` cannot keep both: say by name which on-app check stops (before release, and after implementation for continuous), and let the user pick the method in step 7. Onboarding then removes `ux` from `review.reviewers`, preserves `review.release_qa` as a mirror of `qa.bundle` (false for manual, true otherwise), and explains the migration in the final preview. No schema bump is needed for these additive keys.

**After implementation:** only continuous runs automatically. Code-based UX runs as the `ux` reviewer in every review round, so its findings follow the review's Skeptic and fix rules. Checks on the running app run once after the final verification and code-review fixes, before completion; quick runs them in review-and-fix even when code review has no findings. When `qa.bundle` is continuous, use `/groundwork:ui-qa <changed screens> --mode <effective-mode>`. When `ux.bundle` is continuous and `ux.method` is app, use `/groundwork:ux-review --mode <effective-mode>` for affected end-user tasks, except in eco. In sport use `--full` for both. Derive affected flows from the complete change, including non-UI code that changes user-visible behavior; do not decide solely from `ui_paths`. Record NOT APPLICABLE with a reason if no uncovered check or user task is affected. Do not turn an empty changed-screen list into an accidental full check. For review-only there is no implementation trigger; run only on request or before release. A mode never turns manual or release into continuous.

**Before release:** when `qa.bundle` is release or continuous, run `/groundwork:ui-qa --full --mode <effective-mode>`. When `ux.bundle` is release or continuous and at least one user persona exists, run `/groundwork:ux-review --full --mode <effective-mode>` with the configured method. When `ux.journey` is release, run `/groundwork:ux-journey --full --mode <effective-mode>`; with no `## Journey:` section it reports BLOCKED with the recovery, rather than the gate being skipped. Explicit `--full` keeps all uncovered checks and all user tasks in scope in every mode; eco does not remove this release gate. Use the exact release candidate (the integration head for develop-release, production head for main-only). The release skill runs the gate before creating a release branch or PR. For main-only, the workflow creating a version tag must run this gate before tagging, since the release-branch skill is not applicable. Manual shows the uncovered ledger rows as the human checklist.

**Results and fixes:** select rows with no automated test, stale rows first, and skip checks already proven by matching automated results. A FAIL or BLOCKED stops implementation completion or release, depending on the trigger. The implementation agent fixes defects, adds regression coverage where possible, re-verifies, and returns the affected checks to QA on the new build. UI QA can update the ledger; commit that update only as the calling workflow allows. Never carry PASS across new edits that affect a checked behavior. Keep QA repair/recheck attempts within the effective mode's round limit; if still failing, or if a blocker cannot be resolved within scope, report and stop without marking done, tagging, pushing, or creating a release PR. Respect existing workflow permissions for all such actions.

### UI coverage ledger

`verification.ui_coverage` is a committed Markdown table of what each screen needs checked:

| Screen | Check | Automated test | Why QA must look | Last verified |
|---|---|---|---|---|

- The implementing skill keeps it current. When it adds or changes a screen, it adds a row for each check, names the UI test that covers it, and for a check no test can make (whether wording reads naturally, how a flow or animation feels) fills "Why QA must look" instead. It sets Last verified to `stale` on the uncovered rows of every screen it changed.
- When a check may go to "Why QA must look" is set by the rule on it in `reference/implementation.md`. `code-quality-reviewer` checks each new or changed "Why QA must look" row against it and reports a row that a test could cover as 🟠.
- Release QA checks only rows with no automated test, fills Last verified (`<branch or commit>, PASS` or `FAIL`), and proposes a test for any row that turns out to be automatable.

### Severity

Every reviewer uses the same scale.

- 🔴 Critical: breaks the build, behavior, data, security, or a public contract, or locks in structure that is hard to undo.
- 🟠 Major: a rule violation or reproducible defect that must be fixed before merge.
- 🟡 Minor: worth fixing; does not block merge.
- Nit: taste only. No severity.

Done means verification passed (including UI tests with screenshots for changed screens), and no confirmed 🔴/🟠 remains.

## Tracker operations

Skills never call a tracker directly. They name an operation and follow `catalog/trackers/<tracker.type>.md`, which says how to perform it. Every tracker document implements exactly these operations.

| Operation | Meaning |
|---|---|
| `read(id)` | Title, body, state, parent, children, and comments of one issue |
| `create(title, body, parent?, labels?)` | Create an issue; returns its id |
| `link(child, parent)` | Make an existing issue a child of another |
| `comment(id, body)` | Append a comment |
| `update_body(id, body)` | Replace the body (used to tick checkboxes) |
| `set_state(id, state)` | `todo`, `in_progress`, `done`, or `cancelled` |
| `branch_name(id)` | The work branch name: `<work_prefix>/<id>-<slug>` unless the tracker supplies one |
| `closes(id)` | The line to put in a PR body so merging the PR closes the issue, or how to close it after merge when the tracker has no such syntax |

Issue ids are written as the tracker shows them: `#12` for GitHub, `ABC-12` for Linear and Jira, `L-12` for local.

## Paths

Paths in skills and agents are relative to the plugin root, which is the directory that holds `skills/`, `agents/`, `catalog/`, and `reference/`. From a skill, the plugin root is two directories above the skill's own directory. An agent cannot locate its own file, so the skill that dispatches it passes the absolute plugin root as a `Plugin root: <path>` line in the prompt.
