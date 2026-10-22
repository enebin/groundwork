# Screen checks

Screen checks look at an app's screens and user flows beyond what automated tests prove. There are two:

- **UX:** whether each end-user persona can find and finish its tasks. It runs from the code (`ux-flow-reviewer`) or on the running app (one `ux-persona-reviewer` per persona), as `ux.method` says.
- **QA:** whether the rendered UI matches the task's requirements and the design source. It always runs on the running app (`ui-qa`), because code cannot establish what a screen looks like.

Automated tests and the implementer's inspection of test screenshots are mandatory implementation work, independent of these choices. The other code reviewers stay in the Review step.

Onboarding asks this as step 7 for projects with screens. For a project without screens, show not applicable and write `ux.bundle: manual`, `ux.method: code`, and `qa.bundle: manual` without asking. Keep `review.release_qa` as a compatibility mirror of `qa.bundle`: false for manual, true for release and continuous. `qa.bundle` is authoritative when present.

Token costs are relative estimates within this step, not measured prices.

## Explain the execution cost

Show this before the user picks anything:

> Checks on the running app can take a long time and use many tokens. Web checks can use tools that locate page elements directly. iOS simulators and Android emulators may take longer because of builds, installation, startup, and the available UI tools. Screenshot-based web checks can also be slow. Time and token usage depend on the tools, coverage, user tasks, and retries. Each additional persona adds work. Missing screen access or input control can block a check entirely.

Do not promise a universal platform multiplier or minutes per screen. A local fixed-action pilot measured warm automation execution, not an AI's complete visual QA or dollar cost; Android was not measured. Do not present those results as a general platform ranking.

## Frequency

UX and QA each pick one. Show the label to the user and write the id to `ux.bundle` or `qa.bundle`.

| Bundle | Pros | Cons | Token cost |
|---|---|---|---|
| `continuous` — every PR | Problems are caught before each change is done | Runs on every change; on the running app this adds the most time | Medium from the code; very high on the running app |
| `release` — before release only | Independent check before each release | Defects needing judgment may wait until release | High |
| `manual` | No automatic overhead | A human must ask for checks beyond automated tests | Low |

- **continuous:** check each change before declaring it done. Code-based UX runs as a reviewer in every review round. A check on the running app runs once after implementation and code-review fixes; do not repeat it in every review round. A FAIL or BLOCKED stops completion. Before release, perform the same full check as release.
- **release:** before releasing, check every user-persona task (UX) or every uncovered ledger row (QA). A FAIL or BLOCKED stops the release.
- **manual:** run only when the user asks. The coverage ledger's uncovered rows are the human's release checklist.

Recommend `continuous` for UX when the project has screens, and `manual` for QA. On re-runs, the existing values are the recommendations.

## UX method

| Bundle | Pros | Cons | Token cost |
|---|---|---|---|
| `code` (Recommended) — from the code | Fast; needs no build or launch | Cannot judge how a screen looks or feels; may miss what only shows on screen | Medium |
| `app` — on the simulator or browser | Closest to real use | Slow; every build, launch, and persona adds time and tokens | High |

QA has no method choice.

## Scope follows the overall mode

There is no separate scope choice. When a check runs for one change, the effective overall `mode` decides how much it covers:

- `eco` and `normal`: only the screens and user tasks the change may affect. In `eco`, the after-implementation check on the running app runs QA only.
- `sport`: everything — every uncovered screen and every user-persona task.

A before-release check always covers everything, in every mode. See Modes and Screen checks in `reference/config.md`.

## Follow-ups

- When `ux.bundle` is not manual, ask for end-user personas if not already collected: who uses the app and the main thing they come to do. Write them to `review.personas` with `kind: user`, and several tasks under `## Persona: <name>`. Suggest one or two from `project.summary`.
- When any check runs on the running app automatically (`qa.bundle` not manual, or `ux.method: app` with `ux.bundle` not manual), ask how to build and launch the app, sample data, and launch flags. Write them to `## UI QA notes`.
- When `qa.bundle` is not manual, ask for a design source if not already set: a readable link, local specs, or none. Write it to `verification.design_source`. A null design source permits requirement-based QA, but never a claim of exact design matching.

For manual checks, collect launch notes and personas when a direct request needs them. A design source needed by an automatically detected design-fidelity rule is still collected during setup.
