---
name: handoff
description: Save or read a repository handoff note with completed work, remaining work, verification evidence, and the next starting point. Use to end a work session, hand work to another person, or resume in a new session. Does not create a new chat or send messages.
---

Read `reference/config.md` under the plugin root (two directories above this skill), the repository's `GROUNDWORK.md`, and its rules. Talk in `language.conversation`; save notes in `language.artifacts`. Inspect only relevant files. Never copy credentials or unrelated personal information into a note.

## Save

Use the current conversation and read-only repository evidence: repository root, current branch, `HEAD`, `git status --short`, relevant diff and recent commits, and the current issue or PR when already known. Follow the repository's GitHub account routing before any authenticated call. Do not require a network service to write a local handoff; state which remote information was unavailable.

Write a compact note with:

- Goal and current issue or PR, with links when verified.
- Repository, branch or worktree, and commit. List dirty files separately from committed work.
- Completed work and decisions that affect the next step.
- Remaining work, blockers, and unanswered questions.
- Verification: exact commands, results, and the revision and dirty state tested. Distinguish commands actually run from suggested commands.
- Next starting point: the first file to read, the next concrete action, and any command needed to continue.

Use the path the user provides. Otherwise create `.groundwork/notes/` with a self-ignoring `.gitignore` containing `*` if absent, and create a fresh `handoff-YYYYMMDD-HHMMSS.md`. Do not overwrite an existing note. Return the absolute path and a pasteable resume instruction, such as: "Read this handoff, verify the repository state, and continue the remaining work: <absolute path>."

## Resume

Read the specified note. With no path, inspect the newest `handoff-*.md` under `.groundwork/notes/`; if several notes describe different active tasks, ask which task to resume. Compare the note's branch, commit, dirty state, and pending issue with the current repository before acting. A note is historical context, not permission to repeat commits, remote writes, or destructive commands. Never check out another branch over the user's changes.

Explain what still applies and the next action in a few lines. Continue work only when the user asked to resume it, preserving the original task's authorization limits. A stale test result is not proof for a changed revision. If no note exists, say so and offer to reconstruct context from the relevant repository history; do not invent prior decisions.
