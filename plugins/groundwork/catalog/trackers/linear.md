# linear

Token cost levels are relative estimates within this step, not measurements.

Summary: Linear issues through the Linear MCP server. Steps are child issues of the parent. Linear supplies the branch name for each issue.

Fits:
- Teams already planning in Linear.
- Repositories connected to Linear's GitHub or GitLab integration.

Pros:
- Parent/child issues and workflow states are first-class.
- Bodies and comments are Markdown, so checkboxes and round logs render as written.
- Linear supplies a branch name per issue, and its VCS integration can move states on branch, PR, and merge.

Cons:
- Needs the Linear MCP server connected and authorized in every client that runs the plugin.
- MCP tool names and parameters can change between server versions; check the tool schema before calling.
- Linear's branch names do not follow `branches.work_prefix`.

Token cost: Medium — one MCP call per operation; `set_state` needs a status lookup, and MCP responses are larger than CLI output.

Recommended when: the team already uses Linear.

## Config

```yaml
tracker:
  type: linear
  team: <key>         # team key, e.g. ABC
  project: <name>     # optional; project new issues go into
```

Ids are written `ABC-12`.

## Tools

Use the Linear MCP server's tools. Their names are like `get_issue`, `list_issues`, `create_issue`, `update_issue`, `list_comments`, `create_comment`, `list_issue_statuses`, `list_teams`, `list_projects`. Read each tool's schema before the first call; parameter names (for example `parentId` vs `parent`, `state` vs `stateId`) differ between server versions. If the tools are missing, stop and tell the user to add and authorize the Linear MCP server in their client.

## Operations

### read(id)

1. `get_issue` with the id. It returns title, description (the body), state, parent, labels, and `gitBranchName`.
2. `list_comments` for the issue.
3. Children: `list_issues` filtered by parent id, or the children field on `get_issue` when the server returns one.

State mapping by the status **type**: `backlog` or `unstarted` is `todo`, `started` is `in_progress`, `completed` is `done`, `canceled` is `cancelled`.

### create(title, body, parent?, labels?)

`create_issue` with `team`, `title`, `description` (Markdown), `project` when set, `labels` when given, and the parent's id when `parent` is given. Return the identifier it gives back (`ABC-13`).

If a label does not exist in the team, say so and create the issue without it, unless the user asks you to create the label.

### link(child, parent)

`update_issue` on the child with the parent's id. If the child already has another parent, stop and ask.

### comment(id, body)

`create_comment` with the issue id and the Markdown body.

### update_body(id, body)

`get_issue` first, change only what is needed (for example `- [ ]` to `- [x]`), then `update_issue` with the new `description`.

### set_state(id, state)

1. `list_issue_statuses` for the team. Pick the status whose type matches: `unstarted` for `todo`, `started` for `in_progress`, `completed` for `done`, `canceled` for `cancelled`. When a type has several statuses, prefer the team's default (usually "Todo", "In Progress", "Done", "Canceled"); if still unclear, ask once and note the answer under `## Notes`.
2. `update_issue` with that status.

**What Linear does on its own:** with the GitHub or GitLab integration on, Linear can move an issue to a started state when its branch is pushed or its PR opens, and to a completed state when the PR merges. Which moves happen is set per team. Setup records the answer under `## Notes`:
- `Linear moves issues on PR open: yes` → skills skip `set_state(in_progress)` once a PR exists.
- `Linear moves issues on merge: yes` → skills skip `set_state(done)` after a merge of a PR that carried `closes(id)`.
When the note is missing or says no, skills call `set_state` themselves.

### branch_name(id)

Use `gitBranchName` from `get_issue` as is. Linear's integration matches branches by this name. Only when it is empty, fall back to `<branches.work_prefix>/<id>-<slug>`.

### closes(id)

Put `Closes ABC-12` on its own line in the PR body. With the integration on, Linear links the PR and, if the team is set up for it, completes the issue on merge. Without the integration the line does nothing, and the skill calls `set_state(done)` after the merge.

## Setup

1. **Detect.** Linear MCP tools are available, or the user names Linear.
2. **Ask.** Which team (show `list_teams`), and optionally which project (show `list_projects` for that team). Ask: "Is Linear's GitHub/GitLab integration on for this team? Does it move issues when a PR opens, and when it merges?" Offer "not sure" and treat it as no.
3. **Verify with read-only calls.** `list_teams` and `list_issue_statuses` for the chosen team must succeed. If the MCP server is unauthorized, stop and tell the user to authorize it in their client. Create nothing.
4. **Record.** `tracker: {type: linear, team, project}`, and the two automation lines under `## Notes`.
