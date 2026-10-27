# UX checks

Groundwork checks end-user usability three ways. Each answers a different question and costs a different amount. Developer experience of APIs and CLIs is `dx-reviewer`'s job, not part of this folder.

| Check | Question | How | When | Agent |
|---|---|---|---|---|
| Flow review | Did this change make a persona's task harder? | Reads the code and the diff; never launches the app | Every change or on request, per `ux.bundle` with `ux.method: code` | `ux-flow-reviewer` |
| Persona review | Can each persona still finish its tasks on the running app? | Uses the running app, with the code and diff for context | Per `ux.bundle` with `ux.method: app`, or on request | `ux-persona-reviewer` |
| Journey test | Can a first-time user get from first contact to first value on their own? | A participant who has not seen the code walks a whole journey, such as landing → sign-up → organization setup, on the running app | On request, or before release when `ux.journey: release` | `ux-journey-tester` |

The first two run through `/groundwork:ux-review`. The journey test runs through `/groundwork:ux-journey`, which is an add-on: it does nothing until a user asks for it or sets it as a release gate.

All three report expert observations from an AI, not results from real-user research. A journey test is the closest of the three to a usability test, but it still does not replace sessions with real people.

## Files

| File | Holds |
|---|---|
| `heuristics.md` | What a rendered session judges, and the severity scale for usability obstacles. Used by `ux-persona-reviewer` and `ux-journey-tester`. |
| `journey-test.md` | The journey format in `GROUNDWORK.md`, how first-run discovery proposes journeys, and the journey report. |

Shared rules for any agent on the running app (environment isolation, evidence, independence) stay in `reference/rendered-review.md`, because `ui-qa` uses them too. Screen-check frequencies and their cost guidance stay in `catalog/screen-checks.md`.

## Choosing a check

- Run the flow review on every change. It is fast and cheap, and it finds failure paths the app cannot easily trigger.
- Run the persona review on the flow review's rendered-check handoffs and on refactors of display code.
- Run the journey test before a launch or release, and after changing the landing page, sign-up, onboarding, or first-run setup. It is the slowest of the three, because each participant walks a whole journey from a clean state.
