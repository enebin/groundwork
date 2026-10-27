# Journey test

A journey test works like a moderated usability test. The `ux-journey` skill is the moderator: it prepares a clean environment, hands a participant a scenario, and turns the session into a report. Each participant is a fresh `ux-journey-tester` agent that has never seen the code. It walks one journey on the running app the way a first-time user would, thinking aloud as it goes.

A journey covers a path from first contact to first value, across several screens: for example landing page → sign-up → email verification → organization setup → first invitation. A persona task in `ux-review` is usually one screen or one feature; a journey is the whole road to it.

A product usually has several journeys: the first-run sign-up, a teammate joining from an invitation, a returning user signing in, account recovery, each alternative sign-up method, a plan upgrade. Each is its own `## Journey:` section. Two ways into the same place, such as email sign-up and Google sign-in, are two journeys, because a user only ever takes one of them. Journeys that share a beginning can reuse it; see Shared beginnings.

## Journey format

Journeys live in the `GROUNDWORK.md` body, one `## Journey: <name>` section each. The moderator reads them. The participant sees only the Scenario, Start, and Test access lines.

```markdown
## Journey: New workspace
- Persona: Team admin
- Devices: desktop 1440×900; phone 390×844
- Start: http://localhost:3000/ — signed out, new browser context
- Precondition: none
- Scenario: You run a five-person design studio. A friend said this tool helps small teams share tasks. Find out what it does, create an account, and set up a space for your team.
- Test access: Use a new address like journey-<run>@example.test. Your inbox is at http://localhost:8025.
- Reset: npm run db:reset:test
- Milestones:
  1. Understands what the product does and finds where to sign up
  2. Creates an account
  3. Verifies the email address
  4. Creates and names an organization
- Success: An organization exists with the new account as owner.
- Code map: app/(marketing)/page.tsx → app/signup/page.tsx → app/verify/page.tsx → app/onboarding/org/page.tsx
```

Write values that differ per session as placeholders the moderator fills in: `<host>`, `<port>`, `<run>`, and `<data>` for the data directory.

- **Persona** names a `user` persona from `review.personas`. The participant gets only its name as background; its goal and `## Persona:` tasks stay with the moderator, because a participant given them goes on to do those too.
- **Devices** lists the viewport sizes or simulators to run. Each device is a separate participant session.
- **Start** is where the session begins and in what state. A first-run journey starts signed out with no stored data.
- **Precondition** is what must already exist before the participant starts, when a clean state is not enough and no other journey produces it: for an invited teammate, an organization that has sent an invitation to this session's address. Write it with the seed or setup command that creates it. The participant never sees this line; it meets the precondition only as a user would, for example as an invitation email.
- **Scenario** is written in the second person, in the user's words, with a motivation and an end goal. It never names screens, buttons, or steps, because that would tell the participant the path.
- **Test access** gives only what a real user would have: an email address and inbox, a phone number for codes, a test card. The moderator replaces the inbox with one that shows only this session's messages when sessions run in parallel. Never production credentials or real personal data.
- **Reset** returns the environment to the Start state between sessions.
- **Milestones** are the moderator's checkpoints, in order. The participant never sees them.
- **Success** is an observable end state the moderator can confirm afterwards, on screen or in the test data.
- **Code map** lists the screens behind the journey, for the moderator's root-cause notes. The participant never sees it.
- **Continues from** is optional. It names another journey whose end state this journey starts from. See Shared beginnings below.
- **Profiles** is optional: the profile mix for this journey, such as `typical ×2, hurried`. See Participant profiles below.
- **Slips** is optional: realistic mistakes this journey's screens should survive, such as a weak password, a mistyped email, or signing in before confirming the email. See Participant profiles below.

## Shared beginnings

Journeys often start the same way. "Invite a teammate" and "Create a first project" both begin with sign-up and organization setup. Walking that beginning again in every journey costs a full session each time and finds the same obstacles again. Instead, split the flows where they branch: the shared beginning is one journey, and each branch is a journey with `Continues from: <journey>`, which starts from a checkpoint of that journey's end state. A branch can itself be continued, so the journeys form a tree.

```markdown
## Journey: First project
- Persona: Team admin
- Continues from: New workspace
- Start: the screen the checkpoint left open, signed in
- Scenario: Yesterday you created an account and set up a space for your studio. Now set up your first client project so the team can start using it.
- Milestones:
  1. Finds where to create a project
  2. Creates and names the project
- Success: The organization has one project, created by its owner.
```

- **Milestones and Success** cover only what comes after the checkpoint. The shared beginning is tested once, in the journey it continues from.
- **Scenario** says in the user's words what they already did, so the participant knows why it is signed in. It still never names screens or steps.
- **Devices** are a subset of the source journey's, because a checkpoint is reused only on the device kind it was taken on.
- **Persona, Start, Test access, and Precondition** may differ from the source's. An invited teammate, for example, continues from the owner's workspace as a different persona, starts signed out from the invitation email, and has a Precondition that the owner sent the invitation.
- **Devices, Test access, Reset, and Persona** may be left out; a continuing journey then inherits them from the journey it continues from. The example above sets its Persona and inherits the other three.

The checkpoint is the source session's end state, taken after the session ends. Participants never know the milestones, so a session cannot be stopped at one; that is why the shared beginning must be a journey of its own. The checkpoint condition: the moderator takes a checkpoint only from a session whose Success state was confirmed with every milestone Completed or Completed with difficulty. A source session that met it still reports its own 🟠 obstacles and can still FAIL; its continuing journeys run anyway, so one obstacle in a shared beginning does not hide the branches. The checkpoint holds what that user would carry forward: a copy of the session's data (a database dump or snapshot), the signed-in browser storage or the app's data container, the synthetic identity, and the screen it ended on. Each continuing session restores its own copy, so sessions stay independent even though they share a beginning. To restore into another session's environment, copy the checkpoint there first. When the signed-in state cannot be carried over, for example an HttpOnly cookie, sign the session in as setup before dispatch, through the sign-in page or a test-only route, and never show that route to the participant. A checkpoint belongs to one build; any edit to a screen the source journey passes through discards it.

Use a checkpoint only when the environment can save and restore that state. Otherwise write the state as a Precondition with a seed command, or keep the beginning inside the journey. When no source session on a device kind met the checkpoint condition, the journeys that continue from it on that device kind do not run. They are Not reached when the source stopped because of the product (a Failed or Assisted milestone, or no Success state), and the report points to the source journey's obstacle. They are Blocked when the source was Blocked or its checkpoint could not be saved or restored.

Discovery proposes this split where candidate journeys share their first screens, and the user confirms it with the rest of the journeys.

## Participant profiles

A capable AI reads every word, picks strong passwords, and never mistypes, so it walks past problems that stop many real users. Usability tests are run with typical users, a little below the middle of the range, not with experts. Each session therefore gets a profile that sets how the participant behaves, and the moderator assigns its habits and slips.

| Profile | Reads | Patience | Familiarity | Decides |
|---|---|---|---|---|
| `typical` (default) | Headlines, buttons, and field labels; skips helper text, small print, and footers unless stuck | Gives up after two failed tries at the same goal | Has used a few web apps; does not open unlabeled icons or settings to look for things | Clicks the first plausible option |
| `careful` | Everything on the screen | Three tries | Comfortable with web apps; explores menus | Compares options before choosing |
| `hurried` | Only buttons and headings | One retry | As `typical` | Takes the shortest-looking path and fills forms quickly |

**Mix per journey.** In eco and normal, each journey runs one `typical` session. In sport or with `--full`, each journey runs three sessions per device: two `typical` and one `careful`. A journey's `Profiles:` line, for example `typical ×2, hurried`, replaces the sport and `--full` mix; eco and normal run one session with the first profile it names. A profile name other than `typical`, `careful`, or `hurried` is a configuration problem. An obstacle that only `typical` or `hurried` sessions hit is still an obstacle; an obstacle that even `careful` hits is likely to stop most users.

**Habits and slips.** The moderator gives each `typical` and `hurried` session one or two items from the journey's Slips line, or from the error paths discovery found, spread so that different sessions get different ones and every slip runs at least once. Write each as a habit in the participant's words, not as an order to fail: "You use the same short password everywhere: biscuit7", "You type quickly and often swap two letters in your email", "You open the sign-in page before checking your email". `careful` sessions get none. Record each session's profile, habits, and slips in the report, so an obstacle can be traced to the slip that led into it.

**False alarms.** A profile that is too clumsy reports problems that a typical user would not have. When the product has screens known to be clear, or when a `careful` session moved through a screen without hesitation, treat a `typical` or `hurried` obstacle there with suspicion: keep it only when its screenshots show what misled the participant.

A slip can also make a participant blame the wrong thing. After a mistyped email, "Email or password is incorrect" is the truth, not an unclear message. For each obstacle that follows a slip, check what actually happened in the session's data before rating the screen: keep the obstacle when the product gave no way to notice or undo the slip, and drop it when the message was accurate.

## First-run discovery

When `GROUNDWORK.md` has no `## Journey:` section, or the user asks to redefine journeys, the moderator explores the project and proposes journeys before anything runs. Nothing is written until the user approves.

1. **Read what the product promises.** `project.summary`, the `user` personas and their `## Persona:` sections, `## UI QA notes`, the README, and product docs. With no `user` persona, or when an existing journey names a persona that is not a `user` persona in `review.personas`, draft the missing personas from the product, for the user to approve in step 5.
2. **Map the screens.** Find every entry point (the landing page, root route, first screen at launch, and links that arrive by email such as invitations and password resets) and the routes or screens a user passes through: marketing pages, sign-up and sign-in by each method, verification, password reset, onboarding, organization or workspace creation, plan or billing selection, invitations, and the first core action. Use the router configuration, page directories, navigation graphs, and end-to-end tests. Note each screen's file.
3. **Find what a session needs, and what can go wrong.** List the error paths a user could fall into, such as hidden input rules, emails that must be opened in order, or forms that clear on error, as candidate Slips. Then: how to launch the app and reach its start URL; test accounts and seed scripts; how verification email or SMS codes reach a test inbox (a local mail catcher, a test-mode flag, logged codes); third-party sign-in or payment sandboxes; how to reset the data; and how to save and restore it, for checkpoints.
4. **Draft.** Show the user a flow map, from each entry point to first value, with the screen files on each step and where the flows share screens. Where candidate journeys share a beginning, propose splitting it into its own journey with the branches as `Continues from` journeys, and say how many sessions it saves. List every candidate journey found, one line each: name, persona, entry point, end state, and what it needs to run. Do not cap the list. Mark the ones you recommend keeping, the first-run journey first and then the flows the product depends on most, and say why the others can wait. Then write the recommended ones in the format above. Mark every line that is inferred rather than found in the repository with `[inferred]`. Show the launch steps found in step 3 that `## UI QA notes` does not already hold, and any drafted personas. List what is missing as questions: a blocking gap, such as no way to receive a verification email in a test environment, becomes a question, never a guess.
5. **Confirm.** Ask the user which candidates to keep, then to approve or edit each kept journey, the drafted personas, and the launch steps, using the client's question tool. Before the user approves a drafted persona, check Screen checks in `reference/config.md`: when a new `user` persona would make a UX check run that does not run now, such as the on-app check in a file without a `ux` mapping, say which check starts and when, so the user approves that too. Apply edits and show the result again until the user approves. A candidate the user does not keep is not written; discovery can propose it again later.
6. **Record.** Write the approved journeys as `## Journey:` sections in the `GROUNDWORK.md` body. Add approved personas to `review.personas` with `kind: user`, and add approved launch, seed, inbox, reset, and checkpoint steps to `## UI QA notes`, so later runs, including release gates, do not depend on this conversation. Keep unrelated text intact.

When existing journeys reference screens that no longer exist, report the drift and offer to rerun discovery instead of running a stale journey. Rerunning discovery keeps the existing journeys, offers an updated version of each journey whose screens no longer exist, and proposes flows not yet covered, unless the user asks to redefine them all.

## Results per milestone

The moderator maps each session's log to the milestones:

- **Completed:** reached without a 🟠 or 🔴 obstacle.
- **Completed with difficulty:** reached, but with a 🟠 obstacle on the way.
- **Failed:** the participant gave up, or reached a wrong end state believing it was right.
- **Assisted:** reached only after the participant gave up and switched to assisted search (see the agent file). It does not count as completed.
- **Not reached:** an earlier milestone stopped the session, or the journey it continues from left no checkpoint because of the product.
- **Blocked:** the environment or the configuration, not the product, stopped the session: a crashed server, no test inbox, a missing seed, a persona or launch step that `GROUNDWORK.md` does not hold, or a source journey that was itself Blocked.

## Report

Lead with `UX Journey: <status>`:

- **PASS:** every milestone of every session is Completed or Completed with difficulty, each session's Success state was confirmed, and no confirmed 🔴/🟠 obstacle remains.
- **FAIL:** a milestone Failed, was Assisted, or was Not reached; a session that was not Blocked is missing its Success state; or a confirmed 🔴/🟠 obstacle remains.
- **BLOCKED:** no product failure is established, but a session could not run or finish because of the environment or missing configuration. Name each missing item and the command or edit that supplies it.
- **NOT APPLICABLE:** the selected journeys do not exist or the project has no screens, with the reason.

Then:

1. **Summary,** when more than one journey ran: one line per journey with its status, sessions run, and the milestone where most sessions struggled. Obstacles on a screen that several journeys share are listed once, with every journey that hit them.
2. **Sessions.** Journey, device, profile with its habits and slips, environment, build provenance, the synthetic identity used, and for a continuing session the checkpoint it started from.
3. **Journey map.** One row per milestone per session: result, actions taken, backtracks, and the participant's ease rating where it applies.
4. **Obstacles,** most severe first: the milestone, the screen and state, what the participant expected and what happened, the participant's own words from the log, severity from `reference/ux-heuristics.md`, absolute screenshot paths, and how many sessions hit it. Add a suspected cause from the Code map only as a labeled inference.
5. **What worked.** Moments the participant moved through without hesitation, so a fix does not remove them.
6. **Preferences and unverified assumptions,** kept apart from obstacles.
7. **Evidence limits.** An AI participant is not a real user: it reads every word, never gets bored, and may know common product patterns better or worse than the target persona. It also rarely mistypes or picks a weak password, so error and recovery paths often go untested; name the ones no session reached, and check them with `ux-review` instead.
