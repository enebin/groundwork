---
name: ui-qa
description: Checks uncovered rendered UI with an independent agent. Runs when the separate QA policy triggers or on request. Scope follows the overall effort mode or explicit screens/full selection; time and token usage depend on tools and coverage.
argument-hint: "[--full | <screen>...] [--mode eco|normal|sport]"
---

# UI QA

Paths below are relative to the plugin root, two directories above this skill's directory. Resolve the plugin root to an absolute path and put it in every agent prompt as a `Plugin root: <path>` line; an agent does not know where its own definition file lives, so it cannot find `reference/` or `catalog/` without it. The QA agent follows `agents/ui-qa.md` and `reference/rendered-review.md`. If you are already acting as the QA agent, follow those files directly instead of spawning another agent.

Run when the QA policy in `reference/config.md` triggers, or on explicit request. Resolve `--mode` or the configured overall mode. Named screens select those screens; `--full` selects every uncovered ledger row. Without an explicit selection, eco and normal use affected screens and sport uses the full ledger. With no affected rows, report UI QA: NOT APPLICABLE and explain why. Before starting, state the scope and the platform/tool cost guidance from `catalog/qa.md`; do not promise fixed minutes or a platform multiplier. A named screen or `--full` is an explicit scope override.

## 1. Read the configuration

Read `GROUNDWORK.md` at the repository root and follow `reference/config.md` for missing files, missing keys, and schema versions. Read `verification` and the `## UI QA notes` section.

## 2. Delegate

Prepare a short assignment with:

- The absolute worktree path, the relevant diff and files, and the current build state.
- The user's requirements and the design source (`verification.design_source` or the one the task names), including available local references.
- The check list from the ledger (`verification.ui_coverage`): the selected rows with no automated test, `stale` rows first, following the scope resolved above. Rows with a passing automated test are not checked.
- The effective overall effort mode and the exact selected rows; any launch mode from the UI QA notes.
- The device, simulator, emulator, or browser context reserved for QA, and for web the isolated database, ports, and server configuration (required when `verification.addons` contains `isolated-e2e`).
- UI test results already produced for this build, with the commit and dirty state they came from, so QA reuses them instead of rerunning. Run each UI test once per build.
- An output directory outside tracked source, and any execution constraints.

Spawn one fresh QA agent. In Claude Code, use `groundwork:ui-qa`. In Codex, spawn a fresh subagent and tell it to read and follow `agents/ui-qa.md` under the plugin root. Keep the current model settings. Pass requirements and evidence, not the implementer's conclusion or proposed diagnosis.

Reserve QA's device or browser context until it returns. Do not drive it or change the target UI while QA runs; independent non-UI work may continue. If delegation is unavailable, disclose that limitation instead of claiming independent QA.

## 3. Act on the result

Keep the QA status, evidence paths, and coverage limits in the user-facing result. The implementation agent fixes defects and adds or repairs regression tests, then returns the affected checks to QA on a fresh build. A blocked check stays unverified; never relabel it PASS. Stop and report a repeated blocker when no independent work remains.

This workflow tests rendered behavior. Code-review findings go through the `review` skill and its Skeptic Review rules; do not present visual observations as completed code review.
