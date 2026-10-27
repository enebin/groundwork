# Journey test

A journey test works like a moderated usability test. The `ux-journey` skill is the moderator: it prepares a clean environment, hands a participant a scenario, and turns the session into a report. Each participant is a fresh `ux-journey-tester` agent that has never seen the code. It walks one journey on the running app the way a first-time user would, thinking aloud as it goes.

A journey covers a path from first contact to first value, across several screens: for example landing page → sign-up → email verification → organization setup → first invitation. A persona task in `ux-review` is usually one screen or one feature; a journey is the whole road to it.

## Journey format

Journeys live in the `GROUNDWORK.md` body, one `## Journey: <name>` section each. The moderator reads them. The participant sees only the Scenario, Start, and Test access lines.

```markdown
## Journey: New workspace
- Persona: Team admin
- Devices: desktop 1440×900; phone 390×844
- Start: http://localhost:3000/ — signed out, new browser context
- Scenario: You run a five-person design studio. A friend said this tool helps small teams share tasks. Find out what it does, create an account, and set up a space for your team.
- Test access: Use a new address like journey-<run>@example.test. Your inbox is at http://localhost:8025.
- Reset: npm run db:reset:test
- Milestones:
  1. Understands what the product does and finds where to sign up
  2. Creates an account
  3. Verifies the email address
  4. Creates and names an organization
  5. Invites a teammate
- Success: An organization exists with the new account as owner, and one invitation is pending.
- Code map: app/(marketing)/page.tsx → app/signup/page.tsx → app/verify/page.tsx → app/onboarding/org/page.tsx
```

- **Persona** names a `user` persona from `review.personas`, so its goal and `## Persona:` section give the participant's background.
- **Devices** lists the viewport sizes or simulators to run. Each device is a separate participant session.
- **Start** is where the session begins and in what state. A first-run journey starts signed out with no stored data.
- **Scenario** is written in the second person, in the user's words, with a motivation and an end goal. It never names screens, buttons, or steps, because that would tell the participant the path.
- **Test access** gives only what a real user would have: an email address and inbox, a phone number for codes, a test card. Never production credentials or real personal data.
- **Reset** returns the environment to the Start state between sessions.
- **Milestones** are the moderator's checkpoints, in order. The participant never sees them.
- **Success** is an observable end state the moderator can confirm afterwards, on screen or in the test data.
- **Code map** lists the screens behind the journey, for the moderator's root-cause notes. The participant never sees it.

## First-run discovery

When `GROUNDWORK.md` has no `## Journey:` section, or the user asks to redefine journeys, the moderator explores the project and proposes journeys before anything runs. Nothing is written until the user approves.

1. **Read what the product promises.** `project.summary`, the `user` personas and their `## Persona:` sections, `## UI QA notes`, the README, and product docs.
2. **Map the screens.** Find the entry point (the landing page, root route, or first screen at launch) and the routes or screens a new user passes through: marketing pages, sign-up and sign-in, verification, password reset, onboarding, organization or workspace creation, plan or billing selection, invitations, and the first core action. Use the router configuration, page directories, navigation graphs, and end-to-end tests. Note each screen's file.
3. **Find what a session needs.** How to launch the app and reach its start URL; test accounts and seed scripts; how verification email or SMS codes reach a test inbox (a local mail catcher, a test-mode flag, logged codes); third-party sign-in or payment sandboxes; how to reset the data.
4. **Draft.** Show the user a short flow map, from first contact to first value, with the screen files on each step. Then propose one to three journeys in the format above, the first-run journey first. Mark every line that is inferred rather than found in the repository. List what is missing as questions: a blocking gap, such as no way to receive a verification email in a test environment, becomes a question, never a guess.
5. **Confirm.** Ask the user to approve, edit, or drop each journey, using the client's question tool. Apply edits and show the result again until the user approves.
6. **Record.** Write the approved journeys as `## Journey:` sections in the `GROUNDWORK.md` body, keeping unrelated text intact.

When existing journeys reference screens that no longer exist, report the drift and offer to rerun discovery instead of running a stale journey.

## Results per milestone

The moderator maps each session's log to the milestones:

- **Completed:** reached without a 🟠 or 🔴 obstacle.
- **Completed with difficulty:** reached, but with a 🟠 obstacle on the way.
- **Failed:** the participant gave up, or reached a wrong end state believing it was right.
- **Assisted:** reached only after the participant gave up and switched to assisted search (see the agent file). It does not count as completed.
- **Not reached:** an earlier milestone stopped the session.
- **Blocked:** the environment, not the product, stopped the session: a crashed server, no test inbox, a missing seed.

## Report

Lead with `UX Journey: <status>`:

- **PASS:** every milestone of every session is Completed or Completed with difficulty, each session's Success state was confirmed, and no confirmed 🔴/🟠 obstacle remains.
- **FAIL:** a milestone Failed or was Assisted, a Success state is missing, or a confirmed 🔴/🟠 obstacle remains.
- **BLOCKED:** no product failure is established, but a session could not run or finish because of the environment.
- **NOT APPLICABLE:** the selected journeys do not exist or the project has no screens, with the reason.

Then:

1. **Sessions.** Journey, device, environment, build provenance, and the synthetic identity used.
2. **Journey map.** One row per milestone per session: result, actions taken, backtracks, and the participant's ease rating where it applies.
3. **Obstacles,** most severe first: the milestone, the screen and state, what the participant expected and what happened, the participant's own words from the log, severity from `ux/heuristics.md`, absolute screenshot paths, and how many sessions hit it. Add a suspected cause from the Code map only as a labeled inference.
4. **What worked.** Moments the participant moved through without hesitation, so a fix does not remove them.
5. **Preferences and unverified assumptions,** kept apart from obstacles.
6. **Evidence limits.** An AI participant is not a real user: it reads every word, never gets bored, and may know common product patterns better or worse than the target persona.
