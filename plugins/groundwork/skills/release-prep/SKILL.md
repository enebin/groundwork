---
name: release-prep
description: Configure or run scheduled release preparation, infer a version from the release diff, verify the candidate, and present release notes and a reasoned version recommendation for final yes-or-no publication approval. Use for recurring release preparation or preparing the next release for approval.
---

Read `reference/config.md` under the plugin root (two directories above this skill), the repository's `GROUNDWORK.md`, and its rules. Talk in `language.conversation`; write saved configuration and drafts in `language.artifacts`. In Claude Code, invoke other skills as `/groundwork:<name>`; in Codex, read their `skills/<name>/SKILL.md` under the same plugin root.

With no saved `RELEASE_PREP.md`, perform first setup. With an existing setup, run preparation directly unless the user asked to change setup. A scheduled run must never enter interactive setup: report a missing or invalid required setting as a blocker. A human reply to an existing approval package handles that pending candidate, not a new release cycle.

## First setup

Inspect existing release tags, version files, release commands, and the repository's release policy before asking questions. Ask once for the missing setup choices, grouped together: preparation cadence and time, timezone, publication destination, and the scope of autonomous cleanup. Derive the versioning convention from the repository; never ask the user to choose the next version number.

Recommend preparation that updates local release notes and version metadata, runs required verification and review, and fixes release-blocking defects within the approved scope. Keep changes in an isolated work branch or worktree using the configured work prefix. Do not include unrelated refactors, dependency removal, history rewrites, or CI/deployment configuration changes in a generic cleanup allowance. Existing repository approval requirements still apply; collect any specific necessary standing authorization during setup, never promise to bypass it later.

Preview `RELEASE_PREP.md` at the repository root with the cadence, timezone, source and production branches, release/version convention, version-file locations, allowed cleanup, verification commands, exact publication procedure, and scheduler choice. Resolve required setup gaps now; recurring runs should not repeatedly ask preparation questions. Save after the user approves setup. Record scheduler identity and its actual status after creation, not before.

## Scheduling in either client

Use only scheduling capabilities actually available in the current client. Inspect an existing matching schedule and update it instead of creating duplicates. Use the user-approved cadence and timezone, and store a cohesive prompt pointing to this repository, this skill, and `RELEASE_PREP.md`. Every run must stop at the approval package described below. Do not create a schedule merely because this skill was installed or listed.

The saved prompt must say to run preparation from the existing setup without setup questions, preserve any pending approval candidate, stay quiet when no new release changes exist, and stop after presenting a new approval package or a meaningful blocker. Include the absolute repository path and the instruction to use the installed `groundwork:release-prep` skill in either client. Keep notification preferences in the scheduler's settings where supported.

- Codex: discover the app's automation tool and follow its schema. Use a thread follow-up when it can support the approved release cadence; use a standalone project automation only when the user explicitly chooses that execution style. Do not edit automation storage files directly.
- Claude Code: use an available durable scheduling tool or Claude Code Desktop's Scheduled tasks setup. A terminal `/loop` is suitable for session polling, not a promise of durable weekly releases. If no scheduling tool is exposed, provide the exact prompt, repository, cadence and timezone for Desktop setup, and record **not scheduled** until creation is confirmed.
- If no compatible scheduler is available, finish the local configuration and explain the missing scheduling step. The user can still run `/groundwork:release-prep` on demand. Do not silently install a cron job or weaken permissions to make it automatic.

Scheduled prompts notify only when a new candidate is ready for approval, a meaningful failure occurs, or user action is required. With no changes since the last release, stay quiet. Never treat a timer or an automated continuation as publication approval. References: [Codex automations](https://developers.openai.com/codex/app/automations), [Claude Code Desktop scheduled tasks](https://code.claude.com/docs/en/desktop-scheduled-tasks).

## Prepare a candidate

1. Read the saved setup and repository state. Follow Git identity and account-routing rules before Git network operations or authenticated commands. Preserve unrelated dirty work. Inspect and reuse any existing pending candidate for this release cycle; do not duplicate branches or publish the same candidate twice. Pin the released baseline and source revision to SHAs.
2. Read the full diff, public API or behavior changes, and relevant PR evidence. Infer the next version using the repository's version policy and the highest-impact change: a compatibility break, new compatible capability, or compatible fix. Respect documented pre-1.0 and component-specific conventions. Commit labels are hints, not proof. If a baseline or policy cannot be established, report a preparation blocker instead of inventing a version or asking the user to supply one.
3. In the isolated work branch or worktree, prepare the approved version metadata and call `release-notes` for the pinned range with a local destination. Use a self-ignoring `.groundwork/release-prep/` directory for candidate notes, verification evidence, and approval state; create its `.gitignore` containing `*` if absent. Keep a record of baseline and source SHAs, the candidate commit when one exists, a content fingerprint covering all prepared tracked and untracked changes, proposed version and reason, output paths, and scheduler run or cycle identity. A source SHA alone does not identify an uncommitted candidate. Do not overwrite a pending candidate's evidence with a new revision.
4. Run every `verification.commands` entry and the repository's required release checks, including screen checks from `reference/config.md`. Run `review` using configured reviewers and Skeptic policy. Fix confirmed release blockers within the allowed scope, then rerun affected checks and review as required by the effective mode. Stop with a clear blocker if a required check is unavailable or fails beyond that limit. Do not ask routine preparation questions or skip failing checks. Do not commit, push, merge, tag, or deploy unless separately authorized for that exact preparation action.
5. Reread the final candidate diff, regenerate notes and the version recommendation if fixes changed their meaning, and verify the exact candidate. Preparation fixes that change public behavior invalidate the earlier version recommendation. Before requesting approval, stage a concrete publication plan with the precise version, candidate identity, reviewed diff, checks, and commands so no unresolved choice remains for the user.

## Final approval

Present a concise approval package in the user's language, with a link to the full release notes. Lead with the version and the most meaningful changes, explain the version recommendation in one or two sentences, and state verification results. For example, translated naturally:

> **Ready to release 1.5.0**
>
> This adds saved filters and fixes lost selections. [Full release notes]
>
> I recommend **1.5.0** because this adds a capability while preserving existing behavior.
> All required checks passed for this candidate.
>
> **Approve releasing 1.5.0? — Yes / No**

The only decision at this stage is yes or no. Do not ask for a version, repeat setup questions, or offer a version-editing form. A No leaves the prepared artifacts for inspection and performs no publication. Silence is not approval. In an unattended run, save the package as **awaiting approval**, notify the user once, and stop; the scheduler cannot approve it.

Bind a human Yes to that exact candidate, version, and publication plan. Immediately before executing, check that source, baseline, version availability, and prepared content still match the approved state. If any changed, reprepare and request fresh approval. Do not publish a different revision or carry approval to a later cycle. Execute only the saved, approved procedure; do not ask a nested `release` skill to repeat its version or approval dialog. If the procedure requires new approval outside the agreed scope, report the setup gap instead of bypassing it. Report the actual release result, record completion only after success, and preserve failure state without blind retries.
