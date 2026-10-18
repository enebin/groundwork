# GROUNDWORK.md contract

Every groundwork skill reads `GROUNDWORK.md` at the repository root before doing anything else. The `onboarding` skill writes it. This document is the single definition of its shape.

If `GROUNDWORK.md` is missing, stop and tell the user to run `/groundwork:onboarding`. Never guess a value that the file should hold.

If a key a skill needs is missing, stop and name the key. Do not fall back to a default silently.

## Compatibility

The file is a public contract: other people's repositories hold it. Keys are only ever added. A key is never renamed or removed, and a value never changes meaning. When a breaking change is unavoidable, bump `groundwork` (the schema version) and teach `onboarding` to migrate the old shape. A skill that reads a `groundwork` version newer than it knows stops and asks the user to update the plugin.

## Shape

YAML frontmatter holds values. The Markdown body holds prose that a value cannot express.

```yaml
---
groundwork: 1

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
  # local:  path: .groundwork/issues     shared: false   (false = gitignored)
  # github: owner: <owner>  repo: <repo>  project: <number>
  # linear: team: <key>  project: <name>
  # jira:   site: <host>  project: <key>  step_type: subtask | child

workflow:
  bundle: step-loop                      # step-loop | flight | design-first | quick | tdd-loop | review-only
  autoland: false                        # merge automatically once CI passes (not for quick / review-only)

branches:
  strategy: develop-release              # develop-release | main-only
  integration: develop                   # branch that work branches start from and merge into
  production: main
  work_prefix: step                      # work branches are <work_prefix>/<issue-id>-<slug>
  merge: squash                          # squash | merge | rebase — how PRs land on the integration branch

verification:
  base: evidence                         # evidence | ci-gate | test-first | basic
  addons: []                             # design-fidelity | api-contract | isolated-e2e | visual-regression
  commands:
    - name: Build
      run: "<command>"
      verified: false                    # true once the command has passed in this repository
  ui_paths: []                           # paths whose change requires UI tests and rendered review
  ui_tests:
    targeted: "<command with {test} placeholder>"
    full: "<command>"
  design_source: null                    # path or URL of the design source, when design-fidelity is on
  ui_coverage: docs/ui-coverage.md       # UI coverage ledger, committed; present when ui-qa is in review.reviewers

architecture:
  bundle: unidirectional                 # unidirectional | mvvm | layered-service | layered-web | none

review:
  bundle: app                            # app | sdk | product | light
  reviewers: [architecture, code-quality, ux, ui-qa]
  skeptic: blocking                      # blocking (🔴/🟠 only) | all (every non-nit finding)
  trigger: per-round                     # per-round | per-implementation | on-request
  personas:
    - name: "Habit tracker user"
      goal: "Record today's habits in a few taps"

mode: normal                             # eco | normal | sport — how much review and UI QA a change gets (see Modes)
---
```

## Body sections

Optional. Skills read only the section that applies to them.

- `## Review focus: <reviewer>` — repository-specific checks for one reviewer, such as `## Review focus: architecture`. The reviewer adds these to its own checklist. They narrow where to look; the documents in `docs` stay the standard.
- `## Persona: <name>` — the tasks a UX persona performs, when `review.personas[].goal` is not enough.
- `## Release checks` — checks the `release` skill runs before cutting a release, beyond its built-in ones.
- `## UI QA notes` — how to launch the app for QA, sample data, launch flags, screen-specific checks.
- `## Notes` — anything else the user added during onboarding that applies to every skill.

## Value meanings

### Reviewer keys

| Key | Agent | Looks at |
|---|---|---|
| `architecture` | `architecture-reviewer` | Layers, coupling, boundaries, the chosen architecture bundle |
| `code-quality` | `code-quality-reviewer` | Correctness, readability, cost, tests |
| `security` | `security-reviewer` | Authorization, data isolation, personal data, untrusted input |
| `writing` | `writing-reviewer` | User-facing copy, terminology, accuracy against behavior |
| `dx` | `dx-reviewer` | Public API usability for library users |
| `ux` | `ux-persona-reviewer` | Usability, one agent per persona |
| `ui-qa` | `ui-qa` | Rendered UI against requirements and the design source |

`ux` and `ui-qa` exercise the running product. The rest read code.

In Claude Code the agents are registered as `groundwork:<agent>`. In Codex, spawn a fresh subagent and tell it to read and follow `agents/<agent>.md` under the plugin root.

### Review bundles

| Bundle | Reviewers | Skeptic |
|---|---|---|
| `app` | architecture, code-quality, ux, ui-qa | blocking |
| `sdk` | architecture, code-quality, dx, ui-qa (when the library has UI) | blocking |
| `product` | architecture, code-quality, security, writing, ux | all |
| `light` | code-quality | blocking |

`review.reviewers` is the source of truth after onboarding. The bundle name records where the list came from. `architecture` is dropped from any bundle when `architecture.bundle` is `none`, because the reviewer has no standard to judge against.

### Modes

`mode` sets how much review and rendered QA a change gets. It never chooses a model. Reviewers, the Skeptic policy, and verification rules stay as configured. Skills that run a review loop accept `--mode <mode>` for a single run.

| | `eco` | `normal` | `sport` | Release QA (every mode) |
|---|---|---|---|---|
| Review rounds, at most | 1 | 3 | 3 | — |
| Who reviews again from round 2 | — | reviewers that raised a confirmed 🔴/🟠 | every reviewer | — |
| Automated UI tests | changed screens | changed screens; full suite at finish | full suite every round | full suite |
| UI QA: ledger rows checked | none; the changed screens' rows are marked `stale` | rows without an automated test, on changed screens | the same, on changed and related screens | every row without an automated test, `stale` first |
| Appearance conditions | — | default; dark and largest text too when the change touches color, typography, or layout | light, dark, largest text | every condition the ledger lists |
| UX personas | none | only personas whose tasks the change touches | every task the change touches | every task |
| Done | verification passes, no confirmed 🔴/🟠; UI recorded as unverified | verification and UI QA pass, no confirmed 🔴/🟠 | as `normal` | a FAIL or BLOCKED stops the release |

**Related screens** are screens that use a changed component, style, or theme value, and screens that navigate directly into or out of a changed screen.

**Release QA** is `/groundwork:ui-qa --full`, plus `/groundwork:ux-review --full` when `ux` is in `review.reviewers`. Under `develop-release`, the `release` skill runs it before cutting a release. Under `main-only`, run it before tagging a version.

In `eco`, a 🔴/🟠 left after round 1's fixes are verified is reported to the user rather than reviewed again.

### UI coverage ledger

`verification.ui_coverage` is a committed Markdown table of what each screen needs checked:

| Screen | Check | Automated test | Why QA must look | Last verified |
|---|---|---|---|---|

- UI QA checks only rows whose Automated test cell is empty. A row with a test is covered by that build's test result.
- UI QA maintains the ledger: it adds rows for new or changed screens, fills Last verified (`<branch or commit>, PASS` or `FAIL`), and proposes a test in its report for any row that could be automated. When the implementation agent adds that test, it writes the test name into the row.
- In `eco`, the implementing skill sets Last verified to `stale` on the changed screens' rows instead of running UI QA. Nothing else edits the ledger.

### Severity

Every reviewer uses the same scale.

- 🔴 Critical: breaks the build, behavior, data, security, or a public contract, or locks in structure that is hard to undo.
- 🟠 Major: a rule violation or reproducible defect that must be fixed before merge.
- 🟡 Minor: worth fixing; does not block merge.
- Nit: taste only. No severity.

Done means verification passed, required rendered review passed, and no confirmed 🔴/🟠 remains.

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
