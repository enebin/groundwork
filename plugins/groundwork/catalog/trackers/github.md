# github

Token cost levels are relative estimates within this step, not measurements.

Summary: GitHub Issues through the `gh` CLI, with sub-issues for steps and an optional Projects (v2) board for status.

Fits:
- Code already on GitHub.
- Open source and small teams who track work next to the code.

Pros:
- Issues, PRs, and CI in one place; `Closes #N` links and closes issues on merge.
- `gh` is scriptable and already installed for most GitHub users.
- Native sub-issues show step progress on the parent.

Cons:
- Status beyond open/closed needs a Projects board, and setting a board field takes several calls.
- Closing keywords only fire for PRs into the default branch; with a separate integration branch, issues stay open until closed by hand.
- Projects need an extra token scope that the user must grant.

Token cost: Medium — one `gh` call per operation, but `set_state` on a Projects board needs several lookups (item, field, option) per change.

Recommended when: the repository is on GitHub and the team does not already live in another tracker.

## Config

```yaml
tracker:
  type: github
  owner: <owner>       # user or organization login
  repo: <repo>
  project: <number>    # optional; Projects (v2) number
```

Below, `R` stands for `--repo <owner>/<repo>`. Always pass it, so a worktree with another remote cannot redirect the call. Ids are written `#12`; commands take the bare number `12`.

Never run `gh auth switch` or `gh auth login`. The active account is shared with other sessions. If a call fails for authentication or scope, stop and tell the user the command to run.

## Operations

### read(id)

```bash
gh issue view 12 R --json number,title,body,state,stateReason,labels,comments,url,projectItems
gh api graphql -F n=12 -f o=<owner> -f r=<repo> -f query='
  query($o: String!, $r: String!, $n: Int!) {
    repository(owner: $o, name: $r) {
      issue(number: $n) {
        parent { number title state }
        subIssues(first: 100) { nodes { number title state } }
      }
    }
  }'
```

State: closed with `stateReason: COMPLETED` is `done`, closed `NOT_PLANNED` is `cancelled`. An open issue is `in_progress` when its board Status (from `projectItems`) is In Progress, otherwise `todo`.

### create(title, body, parent?, labels?)

1. Write the body to a temporary file.
2. Create the issue. Add it to the board when `project` is set; `--project` takes the board **title**, so look it up from the number once.

```bash
TITLE=$(gh project view <project> --owner <owner> --format json --jq .title)
gh issue create R --title "<title>" --body-file <file> --project "$TITLE" [--label "<label>" ...]
```

3. The command prints the issue URL. The id is `#` + its last path segment.
4. If a label does not exist, the create fails. Create the label with `gh label create "<label>" R`, tell the user, and retry.
5. If `parent` is given, `link` the new issue to it.

### link(child, parent)

The sub-issues API takes the child's numeric **id**, not its issue number.

```bash
CHILD_ID=$(gh api repos/<owner>/<repo>/issues/<child number> --jq .id)
gh api -X POST repos/<owner>/<repo>/issues/<parent number>/sub_issues -F sub_issue_id=$CHILD_ID
```

An issue has at most one parent. If the child already has another parent, the call fails; stop and ask instead of replacing it.

### comment(id, body)

```bash
gh issue comment 12 R --body-file <file>
```

### update_body(id, body)

`read` first, change only what is needed (for example `- [ ]` to `- [x]`), then:

```bash
gh issue edit 12 R --body-file <file>
```

### set_state(id, state)

| State | Issue | Board Status (when `project` is set) |
|---|---|---|
| `todo` | `gh issue reopen 12 R` if closed | Todo |
| `in_progress` | `gh issue reopen 12 R` if closed | In Progress |
| `done` | `gh issue close 12 R --reason completed` | Done |
| `cancelled` | `gh issue close 12 R --reason "not planned"` | leave as is |

To set the board Status:

```bash
PROJECT_ID=$(gh project view <project> --owner <owner> --format json --jq .id)
ITEM_ID=$(gh project item-list <project> --owner <owner> --format json --limit 1000 \
  --jq '.items[] | select(.content.number == 12 and .content.repository == "<owner>/<repo>") | .id')
gh project field-list <project> --owner <owner> --format json   # find the "Status" field id and option ids
gh project item-edit --project-id "$PROJECT_ID" --id "$ITEM_ID" \
  --field-id <status field id> --single-select-option-id <option id>
```

Match option names case-insensitively. If the board has no Status field or no matching option, skip the board update and say so once.

**What GitHub does on its own:**
- A PR whose body has `Closes #12` closes the issue when it merges **into the repository's default branch**. A PR into any other branch does not close it.
- Projects boards have built-in workflows (for example "Item closed → Done", "Pull request merged → Done"). When they are on, the board Status follows the issue.

So: when `branches.integration` is the default branch, skills skip `set_state(done)` after a merge of a PR that carried `closes(id)`; they still set `in_progress` themselves. When the integration branch is not the default branch, skills call `set_state(done)` after the merge. Setup records which case applies.

### branch_name(id)

`<branches.work_prefix>/<number>-<slug>`, for example `step/12-validate-address`. The slug is the title in lowercase ASCII, words joined by `-`, at most 40 characters. GitHub does not supply branch names.

### closes(id)

Put `Closes #12` on its own line in the PR body. It closes the issue only when the PR merges into the default branch (see `set_state`). For a PR into another branch, use `Refs #12` instead and close after merge with `set_state`.

## Setup

1. **Detect.** `git remote get-url origin` points at `github.com`. Propose `owner` and `repo` from it.
2. **Ask.** Confirm owner and repo. Ask whether to use a Projects board; list candidates with `gh project list --owner <owner>`.
3. **Verify with read-only calls.** Do not switch accounts.

```bash
gh api user -q .login                                          # show which account the calls use
gh repo view <owner>/<repo> --json nameWithOwner,hasIssuesEnabled,defaultBranchRef
gh project view <project> --owner <owner> --format json --jq .title   # only when a board is used
```

   - If issues are disabled, stop and tell the user.
   - If the project call fails for a missing scope, tell the user to run `gh auth refresh -s project` themselves, then retry.
   - If the account is wrong for this repository, stop and tell the user. Do not change it.
4. **Check automation.** Compare `defaultBranchRef.name` with `branches.integration`. Write one line under `## Notes` in `GROUNDWORK.md`: `GitHub closes issues on merge: yes` when they match, `no — integration branch is not the default branch` otherwise. When a board is used, ask the user whether its "Item closed → Done" workflow is on and add that to the same line.
5. **Record.** `tracker: {type: github, owner, repo, project}`.
