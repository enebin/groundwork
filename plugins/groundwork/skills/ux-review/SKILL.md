---
name: ux-review
description: Reviews usability by running one ux-persona-reviewer per persona in GROUNDWORK.md, concurrently, and merging their browser or device observations and screenshot evidence. Part of ordinary review; reports only.
---

# UX Review

Run one independent persona review per entry in `review.personas`, all at once, and merge the results. This is part of ordinary review, not a release gate. It reports only; fixes belong to the implementation agent.

Paths below are relative to the plugin root, two directories above this skill's directory. Every persona reviewer follows `agents/ux-persona-reviewer.md` and `reference/rendered-review.md`.

The `review` skill uses steps 2–4 of this procedure when `ux` is selected. If it already dispatched the persona reviewers, do not dispatch them again. Standalone invocation is supported.

## 1. Read the configuration

Read `GROUNDWORK.md` at the repository root and follow `reference/config.md` for missing files, missing keys, and schema versions. This skill needs `review.personas` with at least one entry, the `## Persona: <name>` sections that exist, and the `## UI QA notes` section.

## 2. Establish the target and scope

Establish the assigned worktree and current source, the task requirements, the affected screens and flows, design references, and known build and test evidence with provenance.

For each persona, decide whether the change affects any of its tasks. Backend changes can affect flows too.

- If no persona is affected, report `UX Review: NOT APPLICABLE` with a concrete reason and stop.
- If only some personas are affected, still dispatch the others with the scope evidence so they can report NOT APPLICABLE rather than invent checks.

## 3. Prepare isolated environments

Follow the isolation rules in `reference/rendered-review.md`. Give each persona reviewer its own device or browser context and artifact directory. For flows that create, change, or reset data, give each its own database or dataset and server configuration; different ports alone do not isolate a shared test database. Use synthetic data and test access only.

If safe parallel interaction cannot be established for a persona, mark that persona's coverage BLOCKED. Do not let two reviewers share mutable state or a UI driver.

## 4. Dispatch

Launch every persona reviewer **at the same time, in one message**. In Claude Code, use the agent `groundwork:ux-persona-reviewer` once per persona. In Codex, spawn one fresh subagent per persona and tell it to read and follow `agents/ux-persona-reviewer.md` under the plugin root. Keep the current model settings. If delegation is unavailable, report that limitation instead of claiming independent review.

Give each reviewer:

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
