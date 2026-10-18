---
name: ui-qa
description: Release QA for screens. An independent agent launches the app and checks only the UI coverage ledger rows that no automated UI test covers. Runs before a release when review.release_qa is on, or when the user asks. Very high token and time cost; not part of a change's review loop.
argument-hint: "[--full | <screen>...]"
---

# UI QA

Paths below are relative to the plugin root, two directories above this skill's directory. Resolve the plugin root to an absolute path and put it in every agent prompt as a `Plugin root: <path>` line; an agent does not know where its own definition file lives, so it cannot find `reference/` or `catalog/` without it. The QA agent follows `agents/ui-qa.md` and `reference/rendered-review.md`. If you are already acting as the QA agent, follow those files directly instead of spawning another agent.

Run this only for release QA (`--full`, Release QA in `reference/config.md`) or when the user asks for screen QA, optionally naming screens. Never run it on every change: in testing one screen took 10 to 20 minutes. Tell the user that before starting when they call it directly.

## 1. Read the configuration

Read `GROUNDWORK.md` at the repository root and follow `reference/config.md` for missing files, missing keys, and schema versions. Read `verification` and the `## UI QA notes` section.

## 2. Delegate

Prepare a short assignment with:

- The absolute worktree path, the relevant diff and files, and the current build state.
- The user's requirements and the design source (`verification.design_source` or the one the task names), including available local references.
- The check list from the ledger (`verification.ui_coverage`): every row with no automated test, `stale` rows first, or only the named screens' rows. Rows with a passing automated test are not checked.
- Any launch mode from the UI QA notes.
- The device, simulator, emulator, or browser context reserved for QA, and for web the isolated database, ports, and server configuration (required when `verification.addons` contains `isolated-e2e`).
- UI test results already produced for this build, with the commit and dirty state they came from, so QA reuses them instead of rerunning. Run each UI test once per build.
- An output directory outside tracked source, and any execution constraints.

Spawn one fresh QA agent. In Claude Code, use `groundwork:ui-qa`. In Codex, spawn a fresh subagent and tell it to read and follow `agents/ui-qa.md` under the plugin root. Keep the current model settings. Pass requirements and evidence, not the implementer's conclusion or proposed diagnosis.

Reserve QA's device or browser context until it returns. Do not drive it or change the target UI while QA runs; independent non-UI work may continue. If delegation is unavailable, disclose that limitation instead of claiming independent QA.

## 3. Act on the result

Keep the QA status, evidence paths, and coverage limits in the user-facing result. The implementation agent fixes defects and adds or repairs regression tests, then returns the affected checks to QA on a fresh build. A blocked check stays unverified; never relabel it PASS. Stop and report a repeated blocker when no independent work remains.

This workflow tests rendered behavior. Code-review findings go through the `review` skill and its Skeptic Review rules; do not present visual observations as completed code review.
