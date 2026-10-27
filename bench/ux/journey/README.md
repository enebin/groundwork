# Journey test benchmark

This benchmark runs the `ux-journey` skill on a small web app with seeded usability defects. It answers three questions:

1. Does the skill work end to end: first-run discovery, recording, isolated sessions, checkpoints, and moderation?
2. Does the participant stay naive, or does it read the code and walk a path it already knows?
3. Is a separate participant agent needed, or would the persona reviewer do the same job?

All runs used Sonnet. Results were judged by hand against `answer-key.json`.

## Results (run r1)

### Discovery

A fresh agent followed the skill's first-run discovery on the app, read-only. It found every screen and entry point, including links that arrive by email. It proposed the first-run journey first and split the shared beginning (sign-up through organization setup) from its branches with `Continues from`. It drafted a `user` persona for the empty `review.personas`, listed launch, inbox, reset, and checkpoint steps for `## UI QA notes`, and reported that the new persona would start no automatic check. It also listed ten places where the skill was unclear; the main ones are fixed (see below).

### Three ways to run a participant

Three journeys, desktop, one session each:

- **A**: the separate participant agent (`agents/participant.md`, the version used in r1).
- **B**: the persona reviewer with a first-time section merged in (`agents/persona-first-time.md`).
- **C**: the current persona reviewer, given a "First-timer" persona the way `ux-review` would dispatch it, with the code available.

| | A | B | C |
|---|---|---|---|
| Seeded defects reached | 5/6 | 5/6 | 5/6 |
| Severity matches the key (after the D1 correction) | 4/5 | 4/5 | 4/5 |
| Reads of the app's code or `GROUNDWORK.md` | 0 | 0 | 0 |
| Did tasks outside the scenario | 2 of 3 sessions | 2 of 3 sessions | 0 |
| Think-aloud log, give-up point, ease ratings | yes | yes | no |
| Mean cost per session | $1.98 | $1.98 | $1.57 |
| Mean tool calls per session | 40 | 35 | 29 |

- **No variant read the code.** C had the worktree path and was allowed to read it, and still worked only from the screen. On this app, the participant's naivety did not depend on which agent file ran.
- **D2 was reached by no one.** It needs a weak password, and every participant chose a strong one. AI participants rarely make input mistakes, so error and recovery paths need a different check.
- **The invite journey worked like a usability test in A and B.** Both participants sent the invite twice, because nothing showed it went out, then gave up at "knows whether the invitation went out". C reached the same defect as an expert finding, without the duplicate-submit behavior or a give-up point.
- **C judged more strictly in one place and less in another.** It rated the hidden "New project" action 🟠 where A and B said 🟡, and rated the disabled Continue 🟡 where A and B said 🟠. It reported the new-workspace journey as PASS.
- **A and B wandered.** Given the persona's goal ("then add the first project and teammates") as background, 4 of 6 A and B sessions went on to create projects or invite people the scenario never asked for. The skill now passes only the persona's name.
- **Every session took about 32 minutes.** Nine sessions shared one browser window and waited on each other; a tenth could not open a tab at all. A single session took far less tool time than that.

The answer key was wrong once: D1 (sign-up only in the footer) was keyed 🟠, but the path stays visible, which the heuristics rate 🟡. All three variants said 🟡, and the key now does too.

### What r1 changed in the skill

- The participant gets the persona's name only, not its goal or tasks, and is told to do only what the scenario asks.
- The skill limits parallel sessions to what the UI tools can hold, gives each web session its own host name (cookies ignore ports), sets the viewport, and records the size actually used.
- Continuing journeys may use another persona, start, test access, and precondition; checkpoints can be copied between environments; sign-in that cannot be restored is done as setup.
- Placeholders (`<host>`, `<port>`, `<run>`, `<data>`) and the `[inferred]` marker are defined.
- The report names error paths no session reached.

Caveats: one app, one run per session, desktop only, hand-judged. The branch sessions all started from one scripted checkpoint (`session.sh ... workspace`), not from each variant's own sign-up session, so every variant met the same starting state.

## Results (run r2): participant profiles

r1's participants read every word and chose strong passwords, so they walked past problems that stop many people. r2 adds participant profiles: `typical` (the default, a little below the middle: skims, gives up after two tries, does not open unlabeled icons), `careful`, and `hurried`, plus habits and slips the moderator assigns, such as "you use the short password biscuit7". Six sessions of variant A, three at a time; one session walked the clean invitation-acceptance screen to catch false alarms.

| | r1, variant A | r2, profiles |
|---|---|---|
| D2 (weak password rejected with no reason) reached | 0 of 1 sign-up sessions | 1 of 1 sessions given that habit |
| Sessions that gave up somewhere | 1 of 3 | 4 of 6 |
| Severity of D1 (sign-up only in the footer) | 🟡 | 🟠 in both `typical` sign-ups (they gave up), 🟡 for `careful` |
| Severity of D6 (New project only in "⋯") | 🟡 | 🟠 (`typical` gave up) |
| False alarms | 0 | 1 |
| Reads of the app's code | 0 | 0 |
| Mean time per session | about 32 min (9 at once) | 96 s (3 at once) |
| Mean cost per session | $1.98 | $1.35 |

- **Profiles made the participants behave like typical users.** The weak-password habit reached D2, which no r1 session did. `typical` participants gave up where a careful reader only hesitated, so the same defect now shows how many users it stops: the careful session rated the footer-only sign-up 🟡, both typical sessions gave up there.
- **Slips found a real gap the answer key missed.** A participant who mistyped their email had no way to correct it or resend the confirmation.
- **The same slip caused the only false alarm.** That participant blamed "Email or password is incorrect" for not mentioning confirmation, but the account did not exist because of the typo, so the message was accurate. The skill now tells the moderator to check what actually happened before rating an obstacle that follows a slip.
- **The clean screen stayed clean.** On invitation acceptance, the typical participant with the weak-password habit was rejected once, recovered from the stated rule, and reported only accurate 🟡 points.
- **Running three at a time was about 20 times faster** than nine at once, and cheaper, because sessions no longer waited on one browser window.

Caveats: six sessions, one run each, hand-judged; one session per slip.

## Running it

Requirements: Claude Code with its built-in browser, Node 18 or later, and `curl`.

1. Copy the app outside this repository, so its `CLAUDE.md` does not reach the agents: `cp -R app ~/.cache/groundwork-bench/ux-journey/taskfold`, then `git init` and commit there. For a run on recorded journeys, replace its `GROUNDWORK.md` with `GROUNDWORK.recorded.md`.
2. Start one server per session: `./session.sh <run> <id> <port> [workspace]`. `workspace` seeds an owner with an organization for branch journeys; sign the browser in with `/dev/login?email=lead-<run>@example.test` as setup.
3. Dispatch one subagent per session that reads and follows the variant's agent file, with the assignment fields shown in `runs/r1-results.json` and the recorded journeys. Give each its own `s<N>.localhost` host and tab.
4. Score each report against `answer-key.json`, check each session's `db.json` for the journey's Success line, and count code reads in the subagent transcripts.

## Files

| Path | Purpose |
|---|---|
| `app/` | Taskfold, the fixture app, with its own `GROUNDWORK.md` before discovery |
| `GROUNDWORK.recorded.md` | The app's `GROUNDWORK.md` after discovery was approved and recorded |
| `answer-key.json` | Seeded defects, expected severities, clean areas, and discovery expectations |
| `agents/` | Variant A and B agent snapshots used in r1 |
| `session.sh` | Starts one isolated server per session, optionally from the workspace checkpoint |
| `runs/r1-results.json`, `runs/r2-results.json` | Per-session results, cost, and time |
