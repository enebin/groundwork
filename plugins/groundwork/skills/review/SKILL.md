---
name: review
description: Reviews a change with the reviewers listed in GROUNDWORK.md, in parallel. Merges code findings, verifies them with Skeptic Review, and reports rendered UX and UI QA results separately. Reports only; does not modify code.
argument-hint: "[<PR number> | <path>] [--only <keys>] [--since <tree> --fixes <file>]"
---

# Review

Review a change from every angle the repository chose. This skill **only reports.** Fixing belongs to the implementation agent.

Paths below are relative to the plugin root, two directories above this skill's directory. Resolve the plugin root to an absolute path and put it in every agent prompt as a `Plugin root: <path>` line; an agent does not know where its own definition file lives, so it cannot find `reference/` or `catalog/` without it.

## 1. Read the configuration

Read `GROUNDWORK.md` at the repository root and follow `reference/config.md` for missing files, missing keys, and schema versions. This skill needs `review.reviewers`, `review.skeptic`, `docs.rules`, and, in local mode, `branches.integration`. Read `ux.bundle` and `ux.method` when the `ux` mapping is present (Screen checks in `reference/config.md`); `ux` also needs `review.personas`. Read `review.external` when present (External runners in `reference/config.md`). If an entry names a key that is not a reviewer key, or its value is not a non-empty string, stop. Name the entry, list the reviewer keys, say the value is a plain-words description of the model to use, and tell the user to fix or remove the entry in `GROUNDWORK.md`.

Read the rules document before starting.

## 2. Parse arguments

Split the arguments on whitespace.

- `--only <key,...>` narrows the run to those reviewer keys from `reference/config.md`. Stop and say so if a key is unknown. Without it, run every key in `review.reviewers`, plus `ux` when a present `ux` mapping is `continuous` with `code`. A legacy file without a `ux` mapping runs `ux` only when it is listed in `review.reviewers`.
- `architecture` never runs when `architecture.bundle` is `none`; if `--only` names it, stop and say there is no standard to judge against. `ux` needs at least one entry in `review.personas`.
- `--since <tree> --fixes <file>` makes a **follow-up review** in local mode: only what changed since the working-tree snapshot `<tree>`, judged against the findings listed in `<file>` as fixed since then. Both flags go together. Stop and say so if either is given without the other, or with PR or path mode.
- If the first remaining token is a number, use **PR mode**. If it is a path, use **path mode**. With none, use **local mode**. Reject anything else, or an ambiguous target.

## 3. Decide what to review

Each mode pins its refs and sets `DIFF_CMD` (how to see the change) and `READ_HINT` (how to read file contents). Track the file list with status, including deletions and renames (`--name-status`).

- **Local mode.** Resolve `origin/<branches.integration>`, falling back to the local `<branches.integration>`; stop if neither exists. Record the base ref and SHA, `HEAD`, dirty state, and `BASE=$(git merge-base <base-ref> HEAD)`. `DIFF_CMD = git diff $BASE --`, which includes uncommitted changes. Add untracked files from `git ls-files --others --exclude-standard`, even when the tracked diff is empty. Do not open local databases, backups, credentials, or generated artifacts just because they are untracked. `READ_HINT` is "read files from the working tree".
  - Follow-up review: take a snapshot of the working tree with `T=$(mktemp -u); GIT_INDEX_FILE=$T git add -A && GIT_INDEX_FILE=$T git write-tree; rm -f $T`, which records untracked files too and leaves the real index alone. `DIFF_CMD = git diff <since> <snapshot> --`, and the file list comes from the same diff.
- **PR mode.** Before any authenticated host command, follow the repository's and user's rules on which account to use. Read the PR's base branch and head without checking it out (for example `gh pr view <N> --json baseRefName,baseRefOid,headRefOid`). Fetch only the refs you need (`git fetch origin <base> pull/<N>/head`), then pin `HEAD_SHA` and `BASE=$(git merge-base origin/<base> $HEAD_SHA)`. Use the PR's actual target branch even when it differs from `branches.integration`. `DIFF_CMD = git diff $BASE $HEAD_SHA`. `READ_HINT` is "read with `git show $HEAD_SHA:<path>`". Do not touch the working tree. If the head cannot be inspected, report the coverage as blocked instead of substituting local files.
- **Path mode.** Review every tracked and untracked file under the path, as whole files, with no diff. Pre-existing defects in that path are in scope; label the report as a whole-path review. Reject a missing or empty path; never expand to the whole repository. `READ_HINT` is "read files from the working tree".

Report the target, pinned refs, and file list. If there is nothing to review, report `SkepticReview: NOT RUN — no first-pass findings` and stop.

## 4. Decide which reviewers apply

For each selected key, decide whether the change gives it anything to judge. Record `NOT APPLICABLE` with a concrete reason for those that do not apply; they do not run.

- `architecture`, `code-quality`, `security`: apply to any code change.
- `writing`: applies when user-facing copy changed, or behavior changed in a way that makes existing wording wrong.
- `dx`: applies when a public surface changed: a library's public symbols or extension points, an HTTP or RPC endpoint or its schema, a command-line command, flag, or output, or developer documentation for any of them.
- `ux`: applies when the change touches a screen, navigation path, state, or action on the way to a persona task, including backend changes that alter what a screen shows or allows. Needs at least one `user` persona in `review.personas` (a persona without `kind` is a `user`). One `ux-flow-reviewer` covers every `user` persona; it reads code and never launches the app.
- `ui-qa` and `ux-persona-reviewer` exercise the running app and are never dispatched here. They run separately under the screen checks in `reference/config.md` or when the user calls them directly.

In path mode, every selected reviewer whose area the path contains applies.

## 5. Run the reviewers in parallel

Launch every applicable reviewer **at the same time, in one message**. In Claude Code, use the agent `groundwork:<agent>` from the table in `reference/config.md`. In Codex, spawn a fresh subagent per reviewer and tell it to read and follow `agents/<agent>.md` under the plugin root. Keep the current model settings. Do not give a reviewer another reviewer's conclusions. If delegation is unavailable, report that limitation instead of claiming independent reviews ran. A key listed in `review.external` runs on its external runner instead (below), launched in the same message.

### Code reviewers

Do not paste the diff into the prompt; reviewers read it with `DIFF_CMD`. Give every code reviewer the following, identically. For a follow-up review, add after the changed files: "Follow-up review: the change is only the fixes since the last review. Read the fixed findings in `<file>`. For each, confirm the defect is gone and that its new or changed test would fail without the fix. Report problems the fixes introduced. Anything outside these fixes is out of scope."

```
Target: <mode> (<PR number / path / local changes against base-ref>)
Pinned refs: <base SHA, head SHA or "working tree", dirty state>
View the change: <DIFF_CMD, or "none — review whole files">
Read files: <READ_HINT>
Changed files:
<file list with status>

Read GROUNDWORK.md, the documents it names, and your own "## Review focus: <key>" section.
Do not modify code. Use only read-only git commands.

Reporting rules:
- Attach one piece of evidence to every finding: a section of the rules or architecture document, or a concrete failure scenario (which input or state leads to what going wrong). Security findings name actor, entry point, control failure, and impact.
- Drop any finding you cannot back with evidence, and anything the compiler or framework already prevents.
- Report only problems the change created or made worse. In whole-path mode, pre-existing defects in the path count.
- Say whether a scenario was inspected or a test was actually run.
- Keep taste-only points as nits, without severity.
- If you have no findings, write only "No findings". Report evidence you could not access as a coverage limit.

Output format (per finding):
### <severity> <one-line summary>
- Location: <file:line>
- Evidence: <document section or failure scenario>
- Impact: <what goes wrong for whom>
- Suggestion: <direction of the fix; code only when needed>

Severity:
- 🔴 Critical: breaks the build, behavior, data, security, or a public contract, or locks in structure that is hard to undo
- 🟠 Major: a rule violation or reproducible defect that must be fixed before merge
- 🟡 Minor: worth fixing; does not block merge
```

### External runners

For a key in `review.external`, launch a driver subagent instead of the reviewer: a general-purpose agent in Claude Code, a fresh subagent in Codex. The driver picks a command-line tool and model, then relays; the external model does the review. Give the driver the `Plugin root` line, the key, its agent from `reference/config.md`, the description from `review.external`, the prompt you would give that reviewer, and these instructions:

```
You relay a review to an external model. Do not review the change yourself, and do not add, drop, or reword findings.

1. Choose the runner and model.
   - Each file in catalog/runners/ under the plugin root is a runner. Use only those; never build a command for a tool without a file there.
   - Run each runner's Detect check. For each installed runner, read its model list as its Models section says. If the Models command fails, that runner failed; keep its first error line.
   - Then take the first case that applies:
     a. No runner is installed: reply only `NOT RUN: no supported command-line tool is installed`, the tool each runner file describes (such as "GitHub Copilot CLI"), and the recovery "install one of these tools, or remove review.external.<key> from GROUNDWORK.md".
     b. The description names a runner that is not installed: reply only `NOT RUN: <runner> is not installed`, with the "not found" recovery from its Failures table. Do not switch to another runner.
     c. The description names a runner that failed: reply only `NOT RUN: <runner>: <reason>`, quoting its error line, with the matching recovery from its Failures table.
     d. A runner that did not fail has a fitting model: pick the runner and model that best fit the description. A named runner or model id wins; otherwise judge from each runner's Models guidance.
     e. Some runner failed: reply only `NOT RUN: <runner>: <reason>` for each failed runner, quoting its error line, with the matching recovery from its Failures table.
     f. Otherwise nothing fits: reply only `NOT RUN: no installed model fits "<description>"`, the installed runners with their models, and the recovery "change review.external.<key> in GROUNDWORK.md to one of these models, install a runner that offers a fitting model, or remove the key".
2. Create one prompt file with `mktemp` in the system temporary directory. Write into it, in order:
   - `Plugin root: <path>`;
   - agents/<agent>.md under the plugin root, without its frontmatter;
   - the reviewer prompt you were given, with its "View the change" line replaced by "The change is below." and, when the runner's Commands are none, "Use only read-only git commands." replaced by "You cannot run commands.";
   - the output of the "View the change" command and, in local mode, each untracked file in the list, or "none — review whole files";
   - in PR mode, each added, modified, or renamed text file's content at the head (`git show <head SHA>:<path>`), and a "Read files" note that other files opened from disk show the working tree, not the PR head.
3. Run the runner's Run command with that file and model, as its Run section says. Set the timeout on your command tool itself; a `timeout` command is not available everywhere.
4. Read the run's output where the runner's Run section says it goes (stdout or an output file). Then delete the prompt file and any output file, whatever the result.
5. If the run failed as the runner's Failures section defines, timed out, or produced none of findings, coverage limits, or "No findings", reply only `NOT RUN: <runner> <model>: <reason>`, quoting the first error line, then the matching recovery from the Failures table, or "run the command by hand to see the full error".
6. Otherwise reply with a first line `Runner: <runner> <model>`, then the findings and coverage limits from the output you read, changing only their layout to match the output format.
```

A `NOT RUN` reply is a coverage limit for that key, as in step 6. Report it with its recovery line. Do not run the key on the current agent instead.

## 6. Merge code findings

- Merge findings that share a `file:line` or a root cause. Keep the highest supported severity and list every source reviewer.
- When reviewers pull in opposite directions (for example `dx` wants a convenience API and `architecture` calls it premature), do not pick a side. Put both under **Trade-offs** with their evidence side by side.
- If a reviewer failed or returned something abnormal, record it as a coverage limit. Do not rerun it, and do not treat it as clean.

## 7. Skeptic Review

Skeptic Review is the separately installed `skeptic-review` skill. It applies to code reviewer findings only, never to rendered results.

Choose what to send by `review.skeptic`:

- `blocking`: only merged 🔴/🟠 findings. 🟡 stays unverified, since verifying it would not change whether the change can merge. If there are findings but none is 🔴/🟠, do not invoke it.
- `all`: every merged finding except nits.

If there is something to send, invoke `skeptic-review` **exactly once** with those findings, the target, pinned refs, and `DIFF_CMD`. Do not invoke it recursively. If it is not installed or not enabled, do not substitute another verifier.

## 8. Report

Start with one Skeptic Review status line:

- Ran: `SkepticReview: APPLIED — CONFIRMED <n> / UNVERIFIED <n> / REJECTED <n>`
- No code findings: `SkepticReview: NOT RUN — no first-pass findings`
- `blocking` mode with only 🟡: `SkepticReview: NOT RUN — no blocking findings`
- Unavailable: `SkepticReview: OFF`

Then, in this order:

1. **Conclusion** in one or two sentences: whether anything blocks merge. Incomplete or blocked coverage cannot establish that the change is safe to merge.
2. **Findings.** CONFIRMED findings by severity. Prefix each title with `[CONFIRMED]` and the reviewer key, such as `[CONFIRMED] [code-quality]`. A key run on an external runner also names the runner and model from the driver's `Runner:` line, such as `[CONFIRMED] [writing · copilot gemini-4-argon]`, everywhere the key appears in the report, and Coverage shows the description it was chosen from. When Skeptic Review is OFF, list first-pass 🔴/🟠 here prefixed `[UNVERIFIED]` instead, and do not treat them as confirmed.
3. **Needs confirmation.** High-impact UNVERIFIED findings, each with one line on what could not be confirmed.
4. **Unverified minor.** In `blocking` mode, every 🟡, prefixed `[UNVERIFIED]` and the reviewer key. These were not sent to Skeptic Review.
5. **Trade-offs,** if any.
6. **Nits,** if any, one line each.
7. **Coverage.** Reviewers that were NOT APPLICABLE, failed, or blocked, with reasons.

Leave REJECTED findings out.

