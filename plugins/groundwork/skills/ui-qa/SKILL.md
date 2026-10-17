---
name: ui-qa
description: Delegates rendered UI and interaction verification to an independent ui-qa agent after UI changes or when the user asks for screen QA. Uses the task's design source and actual app evidence; does not replace code review.
---

# UI QA

Paths below are relative to the plugin root, two directories above this skill's directory. The QA agent follows `agents/ui-qa.md` and `reference/rendered-review.md`. If you are already acting as the QA agent, follow those files directly instead of spawning another agent.

Run this after a change that affects appearance, layout, scrolling, keyboard handling, or screen behavior, when a changed file matches `verification.ui_paths`, or when the user asks for screen QA. Documentation-only and non-UI changes do not need it.

## 1. Read the configuration

Read `GROUNDWORK.md` at the repository root and follow `reference/config.md` for missing files, missing keys, and schema versions. Read `verification` and the `## UI QA notes` section.

## 2. Delegate

Prepare a short assignment with:

- The absolute worktree path, the relevant diff and files, and the current build state.
- The user's requirements and the design source (`verification.design_source` or the one the task names), including available local references.
- Affected screens, the required states and actions, and any launch mode from the UI QA notes.
- The device, simulator, emulator, or browser context reserved for QA, and for web the isolated database, ports, and server configuration (required when `verification.addons` contains `isolated-e2e`).
- UI test results already produced for this build, with the commit and dirty state they came from, so QA reuses them instead of rerunning. Run each UI test once per build.
- An output directory outside tracked source, and any execution constraints.

Spawn one fresh QA agent. In Claude Code, use `groundwork:ui-qa`. In Codex, spawn a fresh subagent and tell it to read and follow `agents/ui-qa.md` under the plugin root. Keep the current model settings. Pass requirements and evidence, not the implementer's conclusion or proposed diagnosis.

Reserve QA's device or browser context until it returns. Do not drive it or change the target UI while QA runs; independent non-UI work may continue. If delegation is unavailable, disclose that limitation instead of claiming independent QA.

## 3. Act on the result

Keep the QA status, evidence paths, and coverage limits in the user-facing result. The implementation agent fixes defects and adds or repairs regression tests, then returns the affected checks to QA on a fresh build. A blocked check stays unverified; never relabel it PASS. Stop and report a repeated blocker when no independent work remains.

This workflow tests rendered behavior. Code-review findings go through the `review` skill and its Skeptic Review rules; do not present visual observations as completed code review.
