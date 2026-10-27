---
name: ux-journey
description: Runs a usability test of an end-to-end user journey, such as landing page → sign-up → organization setup, on the running app. A participant agent that has not seen the code walks each journey from a clean state while this skill moderates and reports where users hesitate, get lost, or give up. On first run it explores the project, proposes journeys, and asks the user to confirm them. Use on request, after changing first-run screens, or as a release gate when ux.journey is release.
argument-hint: "[<journey name>...] [--discover] [--full] [--mode eco|normal|sport]"
---

# Journey test

Moderate a usability test of one or more journeys from `skills/ux-journey/references/journey-test.md`. This skill prepares clean environments, dispatches one `ux-journey-tester` per session, and turns the sessions into a report. It does not modify product code; fixes belong to the implementation agent.

Paths below are relative to the plugin root, two directories above this skill's directory. Resolve the plugin root to an absolute path and put it in every agent prompt as a `Plugin root: <path>` line.

Read `skills/ux-journey/references/journey-test.md` before starting. It defines the journey format, first-run discovery, milestone results, and the report.

## 1. Read the configuration

Read `GROUNDWORK.md` at the repository root and follow `reference/config.md` for missing files, missing keys, and schema versions. This skill needs `project.kind`, `review.personas`, and the `## Journey:` and `## UI QA notes` body sections. `ux.journey` is optional; absent means manual. Talk to the user in `language.conversation` and write `GROUNDWORK.md` text in `language.artifacts`.

If the project has no screens, report `UX Journey: NOT APPLICABLE` with the reason and stop.

Questions and setup happen only when the user invoked this skill directly. When another skill runs it, such as a release gate or a scheduled `release-prep`, never ask and never start discovery: report anything that needs the user as `UX Journey: BLOCKED`, naming what is missing and the command that fixes it.

Before launching anything, explain the cost: each session builds or starts the app, starts from a clean state, and walks every screen of a journey, so it takes longer and uses more tokens than `ux-review`. Each extra device adds a session.

## 2. Define journeys on first run

Run first-run discovery from `skills/ux-journey/references/journey-test.md` when no `## Journey:` section exists, when `--discover` is given, or when a journey's screens no longer exist. Discovery ends only with the user's approval; never run a journey the user has not confirmed. When run by another skill, report a missing or stale journey as BLOCKED with the journey, the missing screen, and the recovery `/groundwork:ux-journey --discover`, which offers to update drifted journeys.

When this skill was opened from the add-on menu, or discovery just wrote the first journeys, also ask whether the journey test should gate releases:

- **Only on request** (`manual`): nothing runs automatically.
- **Before every release** (`release`): the before-release gate runs every journey on every listed device, and a FAIL or BLOCKED stops the release. With `develop-release`, `/groundwork:release` runs it; with `main-only`, the workflow that tags a version runs it (Before release in `reference/config.md`).

Write the choice to `ux.journey` only when the frontmatter already has a `ux` mapping. A file without one still runs on legacy UX behavior, and a `ux` mapping that holds only `journey` would make it invalid (Screen checks in `reference/config.md`). In that case, write nothing for `manual`, because absent already means manual. For `release`, tell the user to run `/groundwork:onboarding` first to migrate the `ux` mapping, and keep the journey test manual for now. Then say how to turn on the gate afterwards: choose Journey usability test from `/groundwork:addons`, which asks this question again, or set `ux.journey: release` in the frontmatter.

Record the add-on in the `## Add-ons` section as `catalog/addons.md` describes, linking the `## Journey:` sections instead of copying them. Then ask whether to run the journeys now. Setup alone runs nothing.

## 3. Select sessions

Named journeys select those journeys; without names, select every journey. Resolve `--mode` or the configured overall mode. In eco and normal, run each selected journey on its first listed device. In sport, or with `--full`, run every listed device. A release gate always uses `--full`. A source journey also runs on every device its selected continuing journeys need, so each continuing session has a checkpoint from its own device kind.

Check each selected journey before launching, and report each problem with the journey, what is wrong, and how to fix it:

- It has Start, Scenario, Milestones, and Success lines. A journey without Continues from also has Persona, Devices, Test access, and Reset lines; only a journey with Continues from may inherit those four, as Shared beginnings in `skills/ux-journey/references/journey-test.md` allows. Fix: add the line.
- Its Persona, its own or inherited, is a `user` persona in `review.personas`. Fix: correct the journey's Persona line, or add the persona to `review.personas` with `kind: user`. Adding a `user` persona can start other UX checks; Screen checks in `reference/config.md` says which.
- A Continues from names an existing journey, the chain has no cycle, and its Devices are a subset of the source's. Fix: correct the line.
- `## UI QA notes` says how to launch the app. Fix: add the launch steps there, or rerun with `--discover`.

A journey with a problem is BLOCKED; continue with the others.

Order the sessions by Continues from: a journey runs after the journey it continues from, and a continuing journey whose source is not selected adds that source to the run. Before launching, show the session list: each journey, its devices, which sessions start from a checkpoint, and the total number of sessions. When the user invoked the skill directly with no journey names and more than one journey is selected, let them narrow the list first. A release gate runs the whole list without asking.

## 4. Prepare clean environments

Establish the target as `reference/rendered-review.md` describes: the worktree, the build or server it came from, and its commit and dirty state. Use the launch steps in `## UI QA notes`.

Every session starts from the journey's Start state: signed out, no stored data, a new browser context or a freshly installed app. Give each session its own synthetic identity from the Test access line, its own artifact directory outside tracked source, and its own device or browser context. Set its viewport or device to the journey's Devices entry when the tools allow, and record the size it actually ran at. Cookies are shared across ports on one host, so parallel web sessions in one browser also need their own host name (for example `s1.localhost`).

Follow the isolation rules in `reference/rendered-review.md`; the participant does not read them, so this step is where they are applied. Sign-up and setup create data, so sessions that run at the same time each need their own database or dataset. When that is not available, run sessions one after another and run the journey's Reset between them. Parallel sessions also need their own inbox, or an inbox view filtered to their own address (for example a mail catcher's search URL for that recipient); give the participant that view as its inbox. Sessions that restore the same checkpoint share one address, so a filtered view does not separate them. When inboxes cannot be separated, including for those sessions, run the sessions that receive email one after another. If a session cannot start from a clean Start state, mark it BLOCKED instead of reusing an earlier session's account or data.

Then create the journey's Precondition in that session's environment with its seed or setup command, using that session's synthetic identity. When no command exists, create it yourself through the product as setup, not as part of the test, and record how. Never let a session continue in another session's live environment; one session's actions must not change another's state.

For a journey that continues from another, follow Shared beginnings in `skills/ux-journey/references/journey-test.md`: after the source session ends and meets the checkpoint condition there, save a checkpoint, then restore a separate copy for each continuing session on the same device kind. Dispatch continuing sessions only after their checkpoint exists. If the environment cannot save and restore that state, tell the user and mark the continuing journey BLOCKED rather than starting it from a guessed state.

## 5. Dispatch participants

Launch the sessions that can run in parallel **at the same time, in one message**, but no more than the UI tools can hold: a browser may cap its tabs, and you need one for your own setup. Sessions that drive one shared browser window wait on each other, so more sessions at once may not finish sooner. In Claude Code, use the agent `groundwork:ux-journey-tester` once per session. In Codex, spawn a fresh subagent per session and tell it to read and follow `agents/ux-journey-tester.md` under the plugin root. Keep the current model settings. If delegation is unavailable, report that limitation; do not walk the journey yourself, because you have read the code and the milestones.

Give each participant only:

- `Plugin root: <path>`.
- The persona's name, as background. Leave out its goal and `## Persona:` tasks: they name other journeys' steps, and a participant given them goes on to do those too.
- The journey's Scenario, Start, and Test access lines, with this session's synthetic identity and its own inbox view filled in. A continuing session gets the identity from its checkpoint.
- Its device or viewport, the URLs or app to open, and its artifact directory.

Never give a participant the Precondition, Milestones, Success, Code map, the `## Persona:` section, other journeys, the diff, or another session's results. They tell it the path, which would turn the session into a walkthrough.

## 6. Moderate the results

For each session:

1. Confirm the Success state yourself: on screen, or with a read-only query against that session's test data. A participant that believes it finished is not proof.
2. Map the participant's step log to the Milestones and give each a result from `skills/ux-journey/references/journey-test.md`.
3. Open the screenshots behind every 🔴/🟠 obstacle and confirm they show it. Keep an obstacle the evidence does not show as unverified, apart from confirmed obstacles.

Then merge across sessions and journeys: combine obstacles that share a screen and cause, keeping every session's and journey's attribution, and count how many sessions hit each one. Use the Code map to add a suspected cause only as a labeled inference.

Report as `skills/ux-journey/references/journey-test.md` says. A participant that failed to run, or a missing session, never becomes PASS.

After a fix, rerun the affected journeys from a clean state on the new build, and discard checkpoints taken before it. Never carry a PASS across edits to the screens a journey passes through.
