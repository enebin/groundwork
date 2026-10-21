# local

Token cost levels are relative estimates within this step, not measurements.

Summary: Issues are Markdown files in the repository's main checkout, one file per issue. No account, no network. Every worktree reads and writes the same files.

Fits:
- Solo projects and new repositories with no tracker yet.
- Trying the plugin before connecting a team tracker.
- Offline work.

Pros:
- Works on day one with nothing to install or authorize.
- Plain files: readable with any editor, searchable with `grep`.
- Shared across all worktrees of the repository, so parallel steps see the same issues.

Cons:
- Only on this machine. Teammates, phones, and CI cannot see it (unless `shared: true`, which has its own costs below).
- No notifications, no web view, no automation; state never changes on its own.
- Nothing enforces the format; a hand edit that breaks the frontmatter breaks `read`.

Token cost: Low — local file reads and writes, no network round trips.

Recommended when: you work alone, or you want to start now and connect a real tracker later.

## Config

```yaml
tracker:
  type: local
  path: .groundwork/issues   # relative to the main checkout
  shared: false              # false = ignored by git
  keep: true                 # false = delete an issue file once its PR merges
```

`keep` was added later. When it is absent, treat it as `true`.

## Where the files live

Always resolve `tracker.path` against the **main checkout**, never against the current worktree. Worktrees have their own working trees, so a relative path would give each worktree a separate copy.

```bash
MAIN=$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")
DIR="$MAIN/<tracker.path>"
```

Each issue is `$DIR/L-<n>.md`.

## File format

```markdown
---
id: L-12
title: "Checkout: validate address"
state: todo                 # todo | in_progress | done | cancelled
parent: L-3                 # or null
labels: []                  # e.g. ["needs planning"]
created: 2026-10-17T09:30:00Z
---
## Goal
...

## Done when
- [ ] Verification commands in GROUNDWORK.md pass

## Log

### 2026-10-17T10:02:11Z
### Round 1
- Verify: pass
...
```

- The **body** is everything between the closing `---` and the last line that is exactly `## Log`.
- The **log** is everything after that line. Each comment starts at a line matching `### YYYY-MM-DDTHH:MM:SSZ` and runs to the next such line. Other headings inside a comment (such as `### Round 1`) belong to that comment.
- Issue bodies must not contain a line that is exactly `## Log`.
- Quote `title` when it contains `:` or `#`.

## Operations

### read(id)

1. Read `$DIR/<id>.md`. If it does not exist, stop and say so, with one exception: a missing id at or below the number in `$DIR/.last-id` was deleted after its PR merged, even if `keep` is `true` now. Treat it as `done`; this is how a later step learns that a step it depends on has merged.
2. Parse the frontmatter for `title`, `state`, `parent`, `labels`. Split body and log, and the log into comments, as above.
3. Children: every file in `$DIR` whose frontmatter has `parent: <id>`.

```bash
grep -l "^parent: <id>$" "$DIR"/L-*.md
```

### create(title, body, parent?, labels?)

1. If `$DIR` does not exist, create it (see Setup for git ignore).
2. Pick `n` = the highest existing number or the number in `$DIR/.last-id`, whichever is larger, + 1 (1 when there is neither). `.last-id` keeps ids from being reused after `keep: false` deletes files.
3. Create the file exclusively so two worktrees cannot take the same id. If the create fails because the file exists, add 1 and try again.

```bash
top=$(ls "$DIR" | sed -n 's/^L-\([0-9]*\)\.md$/\1/p' | sort -n | tail -1)
last=$(cat "$DIR/.last-id" 2>/dev/null)
n=$(( (${top:-0} > ${last:-0} ? ${top:-0} : ${last:-0}) + 1 ))
until (set -C; : > "$DIR/L-$n.md") 2>/dev/null; do n=$((n + 1)); done
```

4. Write `n` to `$DIR/.last-id` if it is larger than the number there.
5. Write the frontmatter (`state: todo`, `parent` or `null`, `labels` or `[]`, `created` as UTC now), the body, a blank line, and `## Log`.
6. Return `L-<n>`.

### link(child, parent)

Set `parent: <parent>` in the child's frontmatter. If the child already has a different parent, stop and ask.

### comment(id, body)

Append to the end of the file:

```markdown

### <UTC timestamp>
<body>
```

Never edit or remove earlier log entries.

### update_body(id, body)

Replace only the text between the frontmatter and `## Log`. Keep the frontmatter and the log as they are.

### set_state(id, state)

Set `state:` in the frontmatter to `todo`, `in_progress`, `done`, or `cancelled`.

The local tracker never changes state on its own. Skills always call `set_state` themselves.

### branch_name(id)

`<branches.work_prefix>/<id>-<slug>`, for example `step/L-12-validate-address`. The slug is the title in lowercase ASCII, words joined by `-`, at most 40 characters.

### closes(id)

There is no closing syntax. Add `Issue: <id>` to the PR body for reference. After the PR merges, the skill that sees the merge (`landing`, `autoland`, or `step` when it confirms the merge) calls `set_state(<id>, done)`.

## After the merge

With `keep: false`, the skill that closed the issue after its PR merged first raises `$DIR/.last-id` to at least the id's number (a repository that used the tracker before `.last-id` existed has no such file yet), then deletes `$DIR/<id>.md`. If the issue had a parent and no file in `$DIR` still names that parent, raise `.last-id` for the parent too and delete its file. Delete nothing earlier: `takeoff` reads the issue and its round log to write the PR, and a later step reads its parent's "Decisions". With `keep: true`, delete nothing.

## Setup

1. **Detect.** Choose local when no tracker is detected, or when the user asks for it.
2. **Ask.** "Should the issue files be committed to the repository so others can see them?" Default: No.
   Then ask: "Keep finished issues as files, or delete each one once its PR merges?" Options: keep (Recommended); delete (looking up past work gets slower or harder, because the decisions and review rounds go with the file). Kept files hold the decisions and review rounds, so a later session can see why the code is the way it is. Deleting keeps the folder small for people who do not want the files to pile up.
3. **Prepare the directory.** Create `$MAIN/<tracker.path>`. When `shared: false`, write a file named `.gitignore` containing the single line `*` inside that directory. Git then ignores the directory and that file itself, so no tracked file changes, and every worktree sees the same ignored files. Agent harnesses usually refuse writes inside `.git/`, so never use `.git/info/exclude`.
4. **Verify.** Create nothing. Check that `$DIR` is writable and that `git check-ignore "$DIR/probe.md"` reports it ignored when `shared: false`.
5. **Record.** `tracker: {type: local, path: <path>, shared: <bool>, keep: <bool>}`.

With `shared: true`, the files live in the main checkout's working tree like any other file. groundwork never commits them on a work branch. The user decides when and where to commit them. This mode is untested.

## Migrating to a real tracker later

When the user connects GitHub, Linear, or Jira:

1. Run the new tracker's Setup.
2. Create issues in id order so parents exist before children. For each local issue: `create` with the same title and body, its labels, and the new parent id. Then post the whole local log as one `comment` headed `Migrated from <local id>`. Then `set_state` to the local state.
3. Write `migrated_to: <new id>` into each local file's frontmatter as soon as it is created, so a failed run can resume without duplicates.
4. Update `tracker` in `GROUNDWORK.md`.
5. Keep the local files. Tell the user they can delete `$DIR` once they have checked the new tracker. Work branches named with `L-` ids keep working; new branches use the new ids.
