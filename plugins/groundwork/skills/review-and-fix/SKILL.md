---
name: "review-and-fix"
description: Reviews the current branch's local changes with the repository's reviewers, fixes the confirmed findings at or above a severity threshold, verifies, then commits and pushes. Use for "review and fix", or as the first half of the quick workflow.
allowed-tools: Bash, Read, Edit, Write, Grep, Glob, Skill, Agent, AskUserQuestion
argument-hint: [critical | major | minor] [--mode eco|normal|sport]
---

Review the local changes on the current branch, fix what the review confirms, and commit and push the fixes.

The argument sets the lowest severity to fix. Default: `major`.

- `critical` → 🔴 only
- `major` → 🔴 and 🟠
- `minor` → 🔴, 🟠, and 🟡

## 0. Read the config

Read `reference/config.md` under the plugin root (two directories above this skill's directory), then `GROUNDWORK.md` at the repository root as it says. Stop if the file is missing or a key this skill needs is missing.

Talk to the user in `language.conversation`. Write commits in `language.artifacts`.

This skill invokes other skills as `/groundwork:<name>`. In Codex, invoke one by reading and following `skills/<name>/SKILL.md` under the plugin root.

In plan mode, do not refuse. Inspect with read-only tools, write the concrete plan (change range, review, likely fixes, commands), and ask for approval. After approval, carry it out as planned.

If `docs.rules` and this skill disagree, follow `docs.rules`.

## 1. Check the scope

1. `git branch --show-current`. If it is `branches.integration` or `branches.production`, warn and stop.
2. Confirm there is something to review: commits since `git merge-base HEAD origin/<branches.integration>` (fall back to the local `<branches.integration>`), staged or unstaged changes, or untracked files. If there is nothing, tell the user and stop.

## 2. Review

Resolve the effective overall mode from `--mode` or `mode`. In eco and normal, run every `verification.commands` entry and the full required UI suite once immediately before this first review. In sport, run the complete suite before every review round. Inspect the required UI screenshots and record the results. Do not continue until these checks pass.

Invoke `/groundwork:review` in local mode. It reviews the branch's commits, the uncommitted changes, and untracked files against the integration branch. This skill is an explicit request for a review, so it runs whatever `review.trigger` says.

From the report, keep:

- `[CONFIRMED]` findings at or above the threshold.
- When the report says `SkepticReview: OFF`, the `[UNVERIFIED]` findings at or above the threshold, marked as unverified.
- Every line under **Copy edits**, whatever the threshold. Leave out an edit marked replaced only when you keep its finding.

Only problems in the change count. Pre-existing code outside the diff is out of scope. Skip 🟡 findings that are only about test code style.

## 3. Confirm

List what you kept:

```
[1] 🔴 Critical — <file:line>
    <one-line summary>

[2] 🟠 Major — <file:line>
    <one-line summary>

[3] Copy edit — <file:line>
    "<original>" → "<edit>"
```

If the list is empty, report that no review fixes are needed and continue to step 5 without a fix confirmation. Otherwise ask whether to fix them. Raise trade-offs, high-impact items from "Needs confirmation", and **Missing copy** separately; do not act on them without the user's answer.

## 4. Fix

For each item, read the file and the code around the finding, then fix it in the file's existing style. Apply a copy edit verbatim at its listed `file:line`. Change another copy only when it is the same string in the same context, such as the same key in another locale file, and tell the user about other matches instead of rewriting them. If the fix is unclear or needs a structural change that cannot be applied safely, skip it and tell the user why.

## 5. Verify

Follow Modes in `reference/config.md`. In eco and normal, run only tests added or changed by review fixes, including targeted UI tests and their screenshots. Do not repeat the complete suite at finish. In sport, run every `verification.commands` entry and the full UI suite before each review round. Reuse only results matching the current build. Update the coverage ledger. Do not move on until required checks pass; fix failures at the root cause.

If `review.trigger` is `per-round`, review again (step 2) with `--no-copy-edit`, since this run already applied the copy edits, and repeat until nothing at or above the threshold remains. Stop after the round limit of the mode (`--mode` or `mode`; see Modes in `reference/config.md`), or as soon as a round fixes nothing, and ask the user how to proceed.

After the review fixes and their added or changed tests, apply the after-implementation gate from Screen checks in `reference/config.md` when a check on the running app resolves to continuous. Pass the effective mode and the complete implementation diff, not just review fixes. Run this even with no review findings. FAIL or BLOCKED prevents completion and commit/push; follow the QA repair/recheck limit. If no review fixes or QA ledger edits were made, report the result and stop without committing or pushing. Otherwise include the verified ledger edits with the fixes.

## 6. Commit and push

1. Stage the fixed files one by one. Never stage or edit `.env`, credential files, or other secrets.
2. Commit with the message format in `docs.rules`. If it defines none, use a short imperative subject such as `Address review findings (<threshold> and above)`. Never bypass hooks.
3. If the branch tracks a remote branch, `git push`. Otherwise `git push -u origin <branch>`. If the push is rejected, report why and stop. Never force-push.

If every requested fix was skipped, tell the user and stop without committing. Do not claim a skipped blocking finding was resolved by passing QA.
