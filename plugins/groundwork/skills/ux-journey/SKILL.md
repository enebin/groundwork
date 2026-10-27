---
name: ux-journey
description: Runs a usability test of an end-to-end user journey, such as landing page → sign-up → organization setup, on the running app. A participant agent that has not seen the code walks each journey from a clean state while this skill moderates and reports where users hesitate, get lost, or give up. On first run it explores the project, proposes journeys, and asks the user to confirm them. Use on request, after changing first-run screens, or as a release gate when ux.journey is release.
argument-hint: "[<journey name>...] [--discover] [--full] [--mode eco|normal|sport]"
---

# Journey test

Moderate a usability test of one or more journeys from `ux/journey-test.md`. This skill prepares clean environments, dispatches one `ux-journey-tester` per session, and turns the sessions into a report. It does not modify product code; fixes belong to the implementation agent.

Paths below are relative to the plugin root, two directories above this skill's directory. Resolve the plugin root to an absolute path and put it in every agent prompt as a `Plugin root: <path>` line.

Read `ux/journey-test.md` before starting. It defines the journey format, first-run discovery, milestone results, and the report.

## 1. Read the configuration

Read `GROUNDWORK.md` at the repository root and follow `reference/config.md` for missing files, missing keys, and schema versions. This skill needs `project.kind`, `review.personas`, and the `## Journey:` and `## UI QA notes` body sections. `ux.journey` is optional; absent means manual. Talk to the user in `language.conversation` and write `GROUNDWORK.md` text in `language.artifacts`.

If the project has no screens, report `UX Journey: NOT APPLICABLE` with the reason and stop.

Before launching anything, explain the cost: each session builds or starts the app, starts from a clean state, and walks every screen of a journey, so it takes longer and uses more tokens than `ux-review`. Each extra device adds a session.

## 2. Define journeys on first run

Run first-run discovery from `ux/journey-test.md` when no `## Journey:` section exists, when `--discover` is given, or when a journey's screens no longer exist. Discovery ends only with the user's approval; never run a journey the user has not confirmed.

When this skill was opened from the add-on menu, or discovery just wrote the first journeys, also ask whether the journey test should gate releases:

- **Only on request** (`manual`): nothing runs automatically.
- **Before every release** (`release`): `/groundwork:release` runs every journey on every listed device before cutting a release, and a FAIL or BLOCKED stops it.

Write the choice to `ux.journey` in the frontmatter, and record the add-on in the `## Add-ons` section as `catalog/addons.md` describes, linking the `## Journey:` sections instead of copying them. Then ask whether to run the journeys now. Setup alone runs nothing.

## 3. Select sessions

Named journeys select those journeys; without names, select every journey. Resolve `--mode` or the configured overall mode. In eco and normal, run each selected journey on its first listed device. In sport, or with `--full`, run every listed device. A release gate always uses `--full`.

Check each selected journey before launching: its Persona is a `user` persona in `review.personas`, and it has Start, Scenario, Milestones, and Success lines. Report a malformed journey as BLOCKED with the missing line, and continue with the others.

## 4. Prepare clean environments

Establish the target as `reference/rendered-review.md` describes: the worktree, the build or server it came from, and its commit and dirty state. Use the launch steps in `## UI QA notes`.

Every session starts from the journey's Start state: signed out, no stored data, a new browser context or a freshly installed app. Give each session its own synthetic identity from the Test access line, its own artifact directory outside tracked source, and its own device or browser context.

Follow the isolation rules in `reference/rendered-review.md`. Sign-up and setup create data, so sessions that run at the same time each need their own database or dataset. When that is not available, run sessions one after another and run the journey's Reset between them. If a session cannot start from a clean Start state, mark it BLOCKED instead of reusing an earlier session's account or data.

## 5. Dispatch participants

Launch the sessions that can run in parallel **at the same time, in one message**. In Claude Code, use the agent `groundwork:ux-journey-tester` once per session. In Codex, spawn a fresh subagent per session and tell it to read and follow `agents/ux-journey-tester.md` under the plugin root. Keep the current model settings. If delegation is unavailable, report that limitation; do not walk the journey yourself, because you have read the code and the milestones.

Give each participant only:

- `Plugin root: <path>`.
- The persona's name and goal from `review.personas`, as background.
- The journey's Scenario, Start, and Test access lines, with this session's synthetic identity filled in.
- Its device or viewport, the URLs or app to open, and its artifact directory.

Never give a participant the Milestones, Success, Code map, the `## Persona:` section, other journeys, the diff, or another session's results. They tell it the path, which would turn the session into a walkthrough.

## 6. Moderate the results

For each session:

1. Confirm the Success state yourself: on screen, or with a read-only query against that session's test data. A participant that believes it finished is not proof.
2. Map the participant's step log to the Milestones and give each a result from `ux/journey-test.md`.
3. Open the screenshots behind every 🔴/🟠 obstacle and confirm they show it. Keep an obstacle the evidence does not show as unverified, apart from confirmed obstacles.

Then merge across sessions: combine obstacles that share a screen and cause, keeping every session's attribution, and count how many sessions hit each one. Use the Code map to add a suspected cause only as a labeled inference.

Report as `ux/journey-test.md` says. A participant that failed to run, or a missing session, never becomes PASS.

After a fix, rerun the affected journeys from a clean state on the new build. Never carry a PASS across edits to the screens a journey passes through.
