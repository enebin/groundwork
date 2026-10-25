---
name: slack-report
description: Configure or post repository work reports to the user's chosen Slack workspace, with one thread per work branch. Use when asked to report to Slack, configure Slack reporting, or when an opted-in turn-end hook requests a report. Do not post merely because onboarding lists this add-on.
---

Read `reference/config.md` under the plugin root (two directories above this skill), the repository's `GROUNDWORK.md`, and its rules. Talk in `language.conversation`. Reports use that language unless the user requests another. This skill and its Python helpers are shared by Claude Code and Codex.

Use only the adjacent `post.py` and the credentials in `~/.config/slack-report/`. Never print credentials or send through another Slack connection as a fallback. If posting fails, report the error and stop; do not automatically repeat a possibly successful request. Never include secrets or unrelated personal information in reports.

## Setup

Selecting this add-on authorizes setup, not a sample post. Inspect `SLACK_INFO.md` at the Git root and existing credential file presence without reading their contents into the conversation. Keep existing choices on reruns unless the user asks to change them.

Ask only for missing choices: the intended workspace, channel (recommend the repository folder name), and on-demand or automatic reporting (recommend on-demand). Explain that automatic reporting sends work changes and verification results after a turn that changes the repository. A configured workspace must be the one the user has authorized for these reports.

Credential prerequisites are in [references/setup.md](references/setup.md). Use it when credentials are missing or the workspace needs checking. `python3 <skill-directory>/post.py --check` reports the connected workspace identity without posting. Show that identity for the user to confirm during setup; save its `team_id` in the settings below. Do not post before the intended workspace and connected identity match.

Write `SLACK_INFO.md` only after the setup choices are agreed:

```markdown
# Slack reports

channel: <channel name>
workspace_id: <confirmed team_id>
auto_report: false
```

For automatic reporting, use `auto_report: true` and run `python3 <skill-directory>/install.py` from the repository. It installs runtime copies in ignored `.groundwork/slack-report/` beside the shared Git directory and merges a Stop hook into the current checkout's `.claude/settings.json` and `.codex/hooks.json`, preserving unrelated hooks. It also adds a managed instruction to `CLAUDE.md` and `AGENTS.md`. Hook commands resolve the shared Git directory, so linked worktrees can use the same runtime without storing a personal directory or plugin-cache version in shared settings. Each worktree still reads its own `SLACK_INFO.md` and keeps its own reported-state fingerprint; shared code does not enable reporting in an unconfigured worktree. Include the hook settings and `SLACK_INFO.md` in the branches used for new worktrees, or run setup in an existing worktree that lacks them. On a different machine, run the installer again to populate the ignored runtime; after upgrading the plugin, rerun it to refresh those copies.

Tell Codex users to review and trust the new hook through `/hooks`; do not bypass trust. Hook format references: [Claude Code Stop hooks](https://code.claude.com/docs/en/hooks#stop), [Codex Stop hooks](https://learn.chatgpt.com/docs/hooks#stop).

For on-demand reporting, leave automatic reporting disabled and do not install hooks. To disable existing automatic reporting, set `auto_report: false`; the installed hook then does nothing. Do not remove other user hooks. Record setup through `catalog/addons.md`. Show the written settings and any remaining prerequisite; never claim the setup works before checking it. Do not commit setup files without a request.

## Posting

Post only on the user's request or an opted-in hook request. If `SLACK_INFO.md` or confirmed workspace identity is missing, complete setup before posting. Follow repository GitHub account-routing rules before the helper's PR lookups; if `gh` is unavailable, the report can still use verified local evidence and must say PR metadata is unavailable.

1. Summarize work since the last report from the conversation, `git status`, relevant diff and commits. Distinguish committed work, uncommitted changes, actual verification, and things left unverified. Do not ask the user to write the report.
2. Write the body to a temporary file using Slack mrkdwn: `*bold*`, `_italic_`, backticks, `•` bullets, and `<url|label>` links. Separate sections with a line containing only `---`. Keep each section below 3000 characters. Use a short, plain-language title about the work; the first work-branch title describes the branch's overall goal. Custom sign-offs are optional and require a user preference; do not assume a particular mascot or custom workspace emoji exists.
3. Run `python3 <skill-directory>/post.py --title "<title>" --body <temporary-file> [--channel <name>]`. The helper verifies `workspace_id` before any channel or message mutation. The channel defaults to `SLACK_INFO.md`, then the repository name. One thread is reused per channel and work branch. On main/develop/master or detached HEAD, each report gets a fresh thread. The helper updates thread parents with available PR status, saves a fingerprint of the repository observed before posting, and prints the message link.
4. Return that link. If the helper reports `not_in_channel`, relay its invite hint. If a call failed after some messages were posted, explain possible partial delivery and ask before retrying.
