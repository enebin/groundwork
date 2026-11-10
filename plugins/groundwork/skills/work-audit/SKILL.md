---
name: work-audit
description: Audit how efficiently agent work (Claude Code and Codex, including subagents) ran in this repository over a time range, by default the last 24 hours — stalls, wasted time, token overuse, rule violations, repeated mistakes — and write a plain-language report with problem → fix pairs. Use for a scheduled morning audit, or when asked "how efficient was yesterday's work?". Audits the work process, not the code.
argument-hint: "[--since <time>] [--until <time>]"
---

Judge whether the agent work in this repository during a time range was efficient, and write a report a person reads in the morning. This audits **how the work was done**, not the code. Run start to finish without asking the user anything. Never edit code, rules, skills, memory, issues, or PRs: only propose changes in the report.

Read `reference/config.md` under the plugin root (two directories above this skill), then the repository's `GROUNDWORK.md` and its rules. Write the report in `language.conversation`; without `GROUNDWORK.md`, use the language the user writes in.

## Inputs

- `--since <time>` and `--until <time>`: the range to audit, given by whoever runs this skill (a schedule or a person). ISO 8601, such as `2026-11-09` or `2026-11-09T07:00`; without an offset it is the machine's local time, and a bare date means midnight. `--until` defaults to now, `--since` to 24 hours before `--until`. `END` below is the date of `--until`, `YYYY-MM-DD`.
- The repository is the current one. Use its main checkout, `git rev-parse --path-format=absolute --git-common-dir` without the trailing `/.git`, even when started inside a worktree.
- Saved files go to `.groundwork/work-audit/` in the main checkout. Create it with a `.gitignore` containing `*` if absent. Reports quote local session paths and messages, so they stay out of Git.

## Step 1: Collect

1. Run `python3 <this skill's folder>/digest.py --repo <main checkout> [--since <time>] [--until <time>] > <main checkout>/.groundwork/work-audit/<END>.json`, passing the range as given. If the script rejects the range or the repository, stop and show its error.
   The script reads every agent session whose working folder is the repository or one of its worktrees: Claude Code (`~/.claude/projects/` and `$CLAUDE_CONFIG_DIR/projects/`) and Codex (`$CODEX_HOME/sessions/`, default `~/.codex/sessions/`), with their subagents. Sessions live only on the machine that ran them, so the audit sees this machine's work only; say so in the report. If it lists no sessions, write a one-line report saying no agent work ran in the range, then go to Step 4.
2. Read the digest. Per session (`agent` is `claude` or `codex`) and its `subagents` it holds: title, start/end, token counts, `cost_usd_session_total` (Claude only), command kinds with run count and minutes (`e2e`, `pytest`, `build`, `lint`, `unit`, `ios`, `android`), calls slower than 3 minutes, repeated errors, idle gaps over 20 minutes with what came right before, the last event in the range, compactions, aborted turns, human messages, skills used, spawned agents, and PR numbers.
   - `cost_usd_session_total` covers the whole session, which may extend outside the range. Say so when you quote it for a session that crosses either end. Codex has no cost figure; compare Codex by tokens.
   - Do not open raw transcripts in bulk. Open one transcript (the `file` field) only to confirm a specific finding, and read only the lines around it.
3. Read the rules the work should have followed: the user's global instructions for each client that ran (Claude Code `~/.claude/CLAUDE.md` or `$CLAUDE_CONFIG_DIR/CLAUDE.md`, Codex `~/.codex/AGENTS.md`), `docs.rules`, `CLAUDE.md`, and `GROUNDWORK.md`. Read the repository's Claude Code memory index if it exists (`projects/<main checkout with every / and . replaced by ->/memory/MEMORY.md` under the same Claude folders). Open a single memory file only when a finding touches it.
4. Collect tracker and host facts for the range. Follow the repository's and user's account rules before any authenticated command. If a source is unavailable, skip it and say so in the report.
   - PRs merged in the range, by base branch.
   - Release PRs open or merged in the range (`release/<version>` when `branches.strategy` is `develop-release`), and their CI results. A saved `.groundwork/release-prep/` package that is blocked or awaiting approval counts as a stall.
   - Issues whose round-log or progress comments were posted in the range, read through `catalog/trackers/<tracker.type>.md`, and how many review/fix rounds each took.
5. Read the reports in `.groundwork/work-audit/` dated in the 7 days before `END` to spot problems that recur.

## Step 2: Judge

Look for these problems. Each finding needs evidence: agent, session title, local time, and a number. Skip anything you cannot back with evidence.

- **Stalls and unfinished work.** A session whose last event in the range is a question to the user. An idle gap where an unattended agent waited for the user, or waited on a tool, check, or subagent much longer than needed. A release or step agent that stopped (blocked, bug, failing check, environment problem) so a planned merge or release did not happen. Say how long it sat idle and what did not get done.
- **Wasted time.** Test or build runs the repository's rules say to skip at that stage. For example, the implementation rules run the full verification and UI suite once before the first review in eco and normal; more full runs in those modes are waste. Also: long polling or wait loops, the same slow command repeated, many review/fix rounds on one issue, and duplicate work such as two agents reviewing the same change.
- **Token overuse.** The most expensive sessions and why: many subagents, large subagent output, duplicated reviewers, the same files or logs read repeatedly, huge command output pulled into context, frequent compactions.
- **Rule violations and repeated mistakes.** Anything that breaks the rules read in Step 1. Errors with the same pattern three or more times (for example the same missing file or broken command). A problem that also appears in those earlier reports counts as **repeated**; say on which days.

Do not flag work that was justified. Example: running unit tests many times is correct when the task was reproducing a flaky test. When a finding might be justified, say what would make it so. `mode: sport` reruns every check each round by design.

Give the range one verdict: good, fair, or poor, with the main reason.

## Step 3: Write the report

Write so a high-school student understands it on the first read. A person reads this, not a machine.

- Plain words, short sentences, one idea per sentence.
- When a technical term is unavoidable, explain it in half a sentence the first time. Example: "E2E test (a test that opens a real browser and clicks through the screens)".
- Keep numbers, issue/PR numbers, and file names exact.
- Say what it cost the person (time lost, money or tokens spent, work not done), not how the agent works internally.
- No padding, no greetings, no closing remarks.

Use Slack mrkdwn, which also reads as plain text: `*bold*`, `` `code` ``, `• ` bullets, `<url|label>` links. No `#` headings, no `**`. Separate sections with a line containing only `---`. Keep each section under 3000 characters.

Sections, in this order, with headings translated into the report language:

1. `*At a glance*` — the verdict and its reason in one sentence, then: sessions run (Claude / Codex), total Claude cost (USD), total tokens, PRs merged, longest stall.
2. `*Stalled or unfinished work*`
3. `*Wasted time*`
4. `*Token overuse*`
5. `*Rule violations and repeated mistakes*` — mark repeated ones with the earlier days, such as `(repeated: 11/7, 11/8)`.
6. `*Summary*` — the problems that matter most, at most 5, most costly first, one line each in exactly this form:
   `• <problem>: <recommended fix>`
   - The problem says what happened and what it cost, with a number.
   - The fix is one concrete action and names where it goes: a line in a rules file, a skill or agent prompt, a memory, a tool setting, or a habit to change.
   - Example: `• Ran the E2E suite 4 times during implementation, 38 minutes: add "E2E once, before the first review" back to the fixer's instructions`.
   - A repeated problem gets a stronger fix than a one-off.

When a section has no findings, write one line saying none.

Title: one plain sentence with the range and the verdict, e.g. `11/9 work audit: fair, the release agent waited over 2 hours`.

## Step 4: Save and deliver

1. Save the body to `<main checkout>/.groundwork/work-audit/<END>.md`, with the title as its first line.
2. If the main checkout has a `SLACK_INFO.md`, post from the main checkout with the `slack-report` skill's `post.py` under the same plugin root:
   `python3 <plugin root>/skills/slack-report/post.py --title "<title>" --body <body file without the title line>`
   If posting fails, keep the saved file and end with the error. Do not retry through any other Slack connection.
3. Otherwise end with the saved file's path and the full report.

## Scheduling

On request, schedule a recurring run as "Scheduling in either client" in `skills/release-prep/SKILL.md` describes, with this skill and the repository's main checkout in the saved prompt. The prompt passes the range that matches the cadence, such as nothing for a daily run or `--since` 7 days back for a weekly one, and says to run without questions and to change nothing but `.groundwork/work-audit/`. Use a scheduler that runs on this machine: a cloud run cannot read the session transcripts. Record the setup through `catalog/addons.md`.
