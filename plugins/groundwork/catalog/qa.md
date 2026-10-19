# QA bundles

QA means an agent exercises the running app and judges the uncovered screens and user tasks. Automated tests and the implementer's inspection of test screenshots are mandatory implementation work, independent of this choice. Code reviewers stay in the Review step.

Onboarding asks this as step 7 for projects with screens. Show not applicable for a project without screens and write `qa.bundle: manual`. Write the selected id to `qa.bundle`. Keep `review.release_qa` as a compatibility mirror: false for manual, true for release and continuous. `qa.bundle` is authoritative when present.

Token costs are relative estimates within this step, not measured prices.

| Bundle | Pros | Cons | Token cost |
|---|---|---|---|
| `manual` (Recommended) | No automatic app-driving overhead | A human must request checks beyond automated tests | Low |
| `release` | Independent QA before each release | Defects needing judgment may wait until release | High |
| `continuous` | Uncovered problems checked after each implementation | Repeated app setup and interactions increase time and usage | Very high |

- **manual:** run UI/UX QA only when the user asks. The coverage ledger is the human's release checklist. Recommended initially, preserving the previous release-QA-off default.
- **release:** before releasing, check every uncovered ledger row and every end-user persona task. A FAIL or BLOCKED stops the release.
- **continuous:** also run QA once after implementation and code-review fixes, before declaring the implementation done. Select changed screens and affected tasks using the effective overall mode; do not repeat QA in every code review round. A FAIL or BLOCKED stops completion. Before release, perform the same full check as release.

`mode` is the overall effort control, like a reasoning-effort setting. It adjusts review repetition, test breadth, and the scope of an applicable QA run together. It does not choose a model or turn an automatic QA trigger on when the user chose manual. See Modes and QA in `reference/config.md`. Users who need finer control can edit the config later; do not turn onboarding into separate controls for every check.

## Explain the execution cost

Show this guidance before the user picks a QA bundle:

> Web QA can use tools that locate page elements directly. iOS simulators and Android emulators may take longer because of builds, installation, startup, and the available UI tools. Screenshot-based web QA can also be slow. Time and token usage depend on the tools, coverage, user tasks, and retries. Each additional persona adds work. Missing screen access or input control can block QA entirely.

Do not promise a universal platform multiplier or minutes per screen. A local fixed-action pilot measured warm automation execution, not an AI's complete visual QA or dollar cost; Android was not measured. Do not present those results as a general platform ranking.

## Follow-ups

When release or continuous is selected, ask for a design source if not already set (a readable link, local specs, or none), and how to build and launch the app, sample data and launch flags. Write these to `verification.design_source` and `## UI QA notes`. A null design source permits requirement-based QA, but never a claim of exact design matching.

Ask for end-user personas if not already collected in Review. Keep developer personas for code-based DX review; rendered UX QA dispatches only personas whose kind is user (legacy entries with no kind are user).

For manual, collect launch notes and personas when a direct QA request needs them; a design source needed by an automatically detected design-fidelity rule is still collected during setup.
