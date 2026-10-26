---
name: ux-review
description: Reviews whether end-user personas can finish their tasks, from the code or on the running app as ux.method says. Runs under the UX screen check or on request. Overall effort controls scope; reports only.
argument-hint: "[--full] [--mode eco|normal|sport]"
---

# UX Review

Check whether each selected `user` persona in `review.personas` can find and finish its tasks. `ux.method` picks how: `code` runs one `ux-flow-reviewer` that reads the code and never launches the app; `app` runs one independent persona review per persona on the running app and merges the results. It runs when the UX screen check in `reference/config.md` triggers, or on request. It reports only; fixes belong to the implementation agent. For the app method, explain the platform/tool cost guidance from `catalog/screen-checks.md` before launch. Developer personas are code-based DX review, not UX.

Paths below are relative to the plugin root, two directories above this skill's directory. Resolve the plugin root to an absolute path and put it in every agent prompt as a `Plugin root: <path>` line; an agent does not know where its own definition file lives, so it cannot find `reference/` or `catalog/` without it.

## 1. Read the configuration

Read `GROUNDWORK.md` at the repository root and follow `reference/config.md` for missing files, missing keys, and schema versions. Resolve `ux.method` as Screen checks in `reference/config.md` specifies; a file without a `ux` mapping uses the app method, as before. This skill needs `review.personas`; select only `kind: user` (legacy missing kind means user). With no user personas, report UX Review: NOT APPLICABLE and stop. Read the `## Persona: <name>` sections that exist, and for the app method the `## UI QA notes` section.

## 2. Establish the target and scope

Establish the assigned worktree and current source, the task requirements, the affected screens and flows, design references, and known build and test evidence with provenance.

For each persona, decide whether the change affects any of its tasks before launching anything. Backend changes can affect flows too. Resolve `--mode` or the configured overall mode. Without `--full`, select affected user personas/tasks in eco and normal, and every user persona/task in sport. An explicit usability request still runs in eco; automatic change checks in eco skip the app method. With `--full`, every task of every user persona is in scope in all modes.

- If no persona is affected, report `UX Review: NOT APPLICABLE` with a concrete reason and stop.
- Dispatch only selected personas. List the other user personas as NOT APPLICABLE with the scope reason; do not launch agents solely to report no work.

For the code method, continue with step 3. For the app method, skip to step 4.

## 3. Code method

Dispatch one reviewer. In Claude Code, use the agent `groundwork:ux-flow-reviewer`. In Codex, spawn a fresh subagent and tell it to read and follow `agents/ux-flow-reviewer.md` under the plugin root. Keep the current model settings. If delegation is unavailable, report that limitation instead of claiming independent review.

Give it the selected personas and tasks, and the code reviewers' reporting rules and output format from step 5 of `skills/review/SKILL.md`. For a change scope, also give the target, pinned refs, and diff command as that skill's local mode sets them. For `--full`, or every task in sport, assign a whole-app review instead: trace every selected task from its entry point, with no diff, and pre-existing problems count.

Send its 🔴/🟠 findings to Skeptic Review once, as step 7 of `skills/review/SKILL.md` does under `review.skeptic`. Overall status: **FAIL** if a confirmed 🔴/🟠 remains, or an unverified one when Skeptic Review is OFF; otherwise **BLOCKED** if the reviewer failed or reported missing coverage; otherwise **PASS**. Then report as step 7 says.

## 4. App method: prepare isolated environments

Every persona reviewer follows `agents/ux-persona-reviewer.md` and `reference/rendered-review.md`. Follow the isolation rules in `reference/rendered-review.md`. Give each persona reviewer its own device or browser context and artifact directory. For flows that create, change, or reset data, give each its own database or dataset and server configuration; different ports alone do not isolate a shared test database. Use synthetic data and test access only.

If safe parallel interaction cannot be established for a persona, mark that persona's coverage BLOCKED. Do not let two reviewers share mutable state or a UI driver.

## 5. App method: dispatch

Launch every persona reviewer **at the same time, in one message**. In Claude Code, use the agent `groundwork:ux-persona-reviewer` once per persona. In Codex, spawn one fresh subagent per persona and tell it to read and follow `agents/ux-persona-reviewer.md` under the plugin root. Keep the current model settings. If delegation is unavailable, report that limitation instead of claiming independent review.

Give each reviewer:

- The effective overall effort mode and exact task scope.
- Its persona: name, goal, and the full `## Persona: <name>` section if present.
- The shared target, requirements, affected screens and flows, design references, and evidence with provenance.
- Its own environment: device or browser context, URLs, test access, dataset, and artifact directory.

Do not give a reviewer another persona's scope or findings. Reviewers may not delegate or invoke this skill.

## 6. App method: merge

- Merge observations that share a cause, keeping every persona's attribution and evidence.
- Keep persona-specific problems separate.
- Overall status: **FAIL** if any reviewer establishes a defect or evidenced usability obstacle; otherwise **BLOCKED** if any required coverage is missing; otherwise **PASS** if all applicable checks passed. **NOT APPLICABLE** only when no persona is affected. A failed or missing reviewer never becomes PASS.

## 7. Report

Lead with `UX Review: <status>` and the method. Then:

1. Each persona's status, with completed and missing coverage.
2. Defects: persona, task, and where the user gets stuck — the screen, state, steps, and absolute screenshot paths for the app method, or the code path for the code method — with expected versus actual behavior, impact, and severity. For the code method, add the Skeptic Review status line from `skills/review/SKILL.md`.
3. Preference-only suggestions and unverified assumptions, kept apart from defects. For the code method, also the reviewer's pre-existing problems and rendered-check handoffs.
4. Evidence limits and blockers. Expert review is not real-user validation.

After a fix, recheck the affected persona behavior on the updated build or code.
