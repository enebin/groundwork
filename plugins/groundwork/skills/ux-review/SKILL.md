---
name: ux-review
description: Reviews usability with one independent reviewer per selected end-user persona, merging observations and screenshot evidence. Runs under the separate QA policy or on request. Overall effort controls scope; reports only.
argument-hint: "[--full] [--mode eco|normal|sport]"
---

# UX Review

Run one independent persona review per selected `user` persona in `review.personas`, and merge the results. It runs when the QA policy in `reference/config.md` triggers, or on request. It reports only; fixes belong to the implementation agent. Explain the platform/tool cost guidance from `catalog/qa.md` before launch. Developer personas are code-based DX review, not rendered UX QA.

Paths below are relative to the plugin root, two directories above this skill's directory. Resolve the plugin root to an absolute path and put it in every agent prompt as a `Plugin root: <path>` line; an agent does not know where its own definition file lives, so it cannot find `reference/` or `catalog/` without it. Every persona reviewer follows `agents/ux-persona-reviewer.md` and `reference/rendered-review.md`.



## 1. Read the configuration

Read `GROUNDWORK.md` at the repository root and follow `reference/config.md` for missing files, missing keys, and schema versions. This skill needs `review.personas`; select only `kind: user` (legacy missing kind means user). With no user personas, report UX Review: NOT APPLICABLE and stop. Read the `## Persona: <name>` sections that exist, and the `## UI QA notes` section.

## 2. Establish the target and scope

Establish the assigned worktree and current source, the task requirements, the affected screens and flows, design references, and known build and test evidence with provenance.

For each persona, decide whether the change affects any of its tasks before launching anything. Backend changes can affect flows too. Resolve `--mode` or the configured overall mode. Without `--full`, select affected user personas/tasks in eco and normal, and every user persona/task in sport. An explicit usability request still runs in eco; automatic change QA in eco calls UI QA only. With `--full`, every task of every user persona is in scope in all modes.

- If no persona is affected, report `UX Review: NOT APPLICABLE` with a concrete reason and stop.
- Dispatch only selected personas. List the other user personas as NOT APPLICABLE with the scope reason; do not launch agents solely to report no work.

## 3. Prepare isolated environments

Follow the isolation rules in `reference/rendered-review.md`. Give each persona reviewer its own device or browser context and artifact directory. For flows that create, change, or reset data, give each its own database or dataset and server configuration; different ports alone do not isolate a shared test database. Use synthetic data and test access only.

If safe parallel interaction cannot be established for a persona, mark that persona's coverage BLOCKED. Do not let two reviewers share mutable state or a UI driver.

## 4. Dispatch

Launch every persona reviewer **at the same time, in one message**. In Claude Code, use the agent `groundwork:ux-persona-reviewer` once per persona. In Codex, spawn one fresh subagent per persona and tell it to read and follow `agents/ux-persona-reviewer.md` under the plugin root. Keep the current model settings. If delegation is unavailable, report that limitation instead of claiming independent review.

Give each reviewer:

- The effective overall effort mode and exact task scope.
- Its persona: name, goal, and the full `## Persona: <name>` section if present.
- The shared target, requirements, affected screens and flows, design references, and evidence with provenance.
- Its own environment: device or browser context, URLs, test access, dataset, and artifact directory.

Do not give a reviewer another persona's scope or findings. Reviewers may not delegate or invoke this skill.

## 5. Merge

- Merge observations that share a cause, keeping every persona's attribution and evidence.
- Keep persona-specific problems separate.
- Overall status: **FAIL** if any reviewer establishes a defect or evidenced usability obstacle; otherwise **BLOCKED** if any required coverage is missing; otherwise **PASS** if all applicable checks passed. **NOT APPLICABLE** only when no persona is affected. A failed or missing reviewer never becomes PASS.

## 6. Report

Lead with `UX Review: <status>`. Then:

1. Each persona's status, with completed and missing coverage.
2. Defects: persona, screen and state, steps, expected versus actual behavior, impact, severity, and absolute screenshot paths.
3. Preference-only suggestions and unverified assumptions, kept apart from defects.
4. Evidence limits and blockers. Expert review is not real-user validation.

After a fix, recheck the affected persona behavior on the updated build.
