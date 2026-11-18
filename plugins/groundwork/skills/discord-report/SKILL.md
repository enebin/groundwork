---
name: discord-report
description: Configure or post repository work reports to threads in a Discord channel, one thread per report. Reports go out when work stops for the user (waiting) or when a unit of work finishes (done), never at every turn end. Use when asked to report to Discord, configure Discord reporting, answer or close a report thread, or when the repository's Discord report rules call for a report. Do not post merely because onboarding lists this add-on.
---

Read `reference/config.md` under the plugin root (two directories above this skill), the repository's `GROUNDWORK.md`, and its rules. Talk in `language.conversation`. Reports use that language unless the user requests another. This skill and its helper are shared by Claude Code and Codex.

Use only the adjacent `post.py` and the bot token it reads. Never print the token or send through another Discord connection as a fallback. If a call fails, report the error and stop; do not automatically repeat a possibly successful request. Never include secrets or unrelated personal information in reports.

## Setup

Selecting this add-on authorizes setup, not a sample post. Inspect `DISCORD_INFO.md` at the Git root, or in the main checkout when working in a linked worktree, and whether a token file exists, without reading its contents into the conversation. Keep existing choices on reruns unless the user asks to change them.

1. **Token.** The helper reads `DISCORD_BOT_TOKEN` from `~/.claude/channels/discord/.env`, the file the official Discord channel plugin uses. When `~/.config/discord-report/token` exists, it wins; use it for Codex or without that plugin. If neither exists, follow [references/setup.md](references/setup.md) and stop until the user has saved a token locally.
2. **Server.** Run `python3 <skill-directory>/post.py --check`. It prints the bot's name and the servers it is in, without posting. Ask which server the reports belong in.
3. **Channel.** Run `python3 <skill-directory>/post.py --create-channel --guild <server id> [--name <name>]`. The name defaults to the repository folder name. The bot creates the text channel, or reuses a text channel of that name. It needs the Manage Channels permission; if the call fails for permissions, relay the fix from `references/setup.md`.
4. **Settings.** Write `DISCORD_INFO.md` once the user agrees with the server and channel:

```markdown
# Discord reports

channel_id: <channel id>
guild_id: <server id>
```

5. **Rules.** Reports are triggered by rules, not hooks. Add this block to `docs.rules`, and also to `CLAUDE.md` when it exists and does not already point to `docs.rules`. Replace an existing block with the same markers; keep the rest of each file intact.

```markdown
<!-- groundwork:begin discord-report -->
## Discord reports

Report to Discord with the `groundwork:discord-report` skill in two cases only. Do not report at every turn end.

- **Waiting.** Work stops for the user: a decision to make, or proposals to approve. Report right away, with the question and what each answer would do.
- **Done.** A unit of work finishes: a PR merges, or a long job ends, whether it succeeded or failed. Report what changed and anything left undone. When the work had a waiting thread, close that thread first.
<!-- groundwork:end discord-report -->
```

6. **Check.** Run `--check` again. It must show the saved channel with `guild_matches: true`. Never claim setup works before this passes.

Record setup through `catalog/addons.md`. Show the written settings and any remaining prerequisite. Do not commit setup files without a request.

Linked worktrees start from committed files only. Tell the user to commit the rules block in `docs.rules` (and `CLAUDE.md`) to the branch new worktrees start from; otherwise agents in those worktrees never see the rules and never report. A worktree without `DISCORD_INFO.md` uses the main checkout's, so committing it is optional; commit it too so other clones get it.

Replies to report threads reach an agent only through the optional **Discord channels** feature: a relay session that forwards each thread reply to the agent that owns the work. It needs the Discord channel plugin for Claude Code. Mention it once at the end of setup; set it up only when the user asks, following [references/discord-channels.md](references/discord-channels.md).

## Posting

Post when the repository's Discord report rules call for it, or on the user's request. If `post.py` exits asking for settings, complete setup first; it already looks in both the worktree and the main checkout. Every write checks that the channel, or the thread's parent channel, matches `DISCORD_INFO.md` before changing anything.

1. Write the report from the conversation, `git status`, the diff, and commits. Distinguish committed work, uncommitted changes, actual verification, and things left unverified. Do not ask the user to write it.
   - **Waiting:** the question, the options, and what each option would do.
   - **Done:** what changed, how it was verified, and what is left.
2. Write the body to a temporary file in Discord Markdown: `**bold**`, `*italic*`, backticks, `-` bullets, `[label](url)` links, and `#`–`###` headings. The helper splits it at line breaks to fit Discord's 2000-character message cap.
3. Run `python3 <skill-directory>/post.py --kind waiting|done --title "<title>" --body <file>`. Use a short, plain title about the work. It posts a starter message, opens a thread on it, posts the body inside, and prints the thread link. When the Discord channels feature is set up, add `--owner "<owner>"` to a waiting report, in the form [references/discord-channels.md](references/discord-channels.md) gives.
4. Return the link. If it reports partial delivery, explain what was posted and ask before retrying.

**Answering.** To answer a reply in a thread, write the answer to a file and run `post.py --answer --thread <thread id> --body <file>`. The thread id is the last number in the thread link.

**Closing.** When the work a waiting thread was about finishes, or the user declines everything in it, run `post.py --close --thread <thread id>`. It deletes the thread and its starter message. Then post the done report as a new thread. Never close or delete a done thread; done threads stay as the record.
