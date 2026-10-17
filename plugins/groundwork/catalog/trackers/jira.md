# jira

Token cost levels are relative estimates within this step, not measurements.

Summary: Jira issues through the Atlassian MCP server. Steps are either sub-tasks of a parent issue or child issues of an epic. Bodies are stored in Atlassian Document Format, not Markdown.

Fits:
- Teams whose planning already lives in Jira.
- Organizations that require work to be tracked there.

Pros:
- Fits existing team boards, sprints, and reporting.
- Workflows and automation rules can be as strict as the organization needs.

Cons:
- Bodies are not Markdown; checkboxes need special handling (below).
- Workflows, issue types, and transition names differ per project, so every state change needs a lookup.
- Labels cannot contain spaces (`needs-planning`, not `needs planning`).
- Least tested of the trackers here; expect to adjust the details below for your site.

Token cost: High — site and transition lookups per call, and bodies are verbose ADF JSON that must be read and rewritten whole to tick a checkbox.

Recommended when: the team already tracks work in Jira and will not move.

## Config

```yaml
tracker:
  type: jira
  site: <host>               # e.g. example.atlassian.net
  project: <key>             # e.g. ABC
  step_type: subtask | child
```

- `subtask`: the parent is a Task or Story; each step is a Sub-task created under it.
- `child`: the parent is an Epic; each step is a Task whose parent is the epic.

Every tool call passes `cloudId`. The tools accept the site URL there, so use `https://<site>`. Ids are written `ABC-12`.

## Tools

`getJiraIssue`, `createJiraIssue`, `editJiraIssue`, `addCommentToJiraIssue`, `getTransitionsForJiraIssue`, `transitionJiraIssue`, `createIssueLink`, `searchJiraIssuesUsingJql`, `getJiraProjectIssueTypesMetadata`, `getVisibleJiraProjects`, `getAccessibleAtlassianResources`. If they are missing, stop and tell the user to add and authorize the Atlassian MCP server in their client.

## Bodies and checkboxes

Jira stores descriptions as Atlassian Document Format (ADF), a JSON tree. The tools accept Markdown (`contentFormat: "markdown"`) and convert it, but checkbox lists do not survive the round trip reliably.

- **Write** bodies that contain checkboxes as ADF: each `- [ ] text` becomes a `taskItem` with `attrs.state: "TODO"` inside a `taskList`; `- [x]` becomes `state: "DONE"`. Everything else may be sent as Markdown.
- **Read** with `responseContentFormat: "adf"` when you will update the body, and `"markdown"` when you only need to read it.
- Comments are sent as Markdown. Headings and lists convert well; checkboxes in comments appear as plain text, which is fine for logs.

## Operations

### read(id)

1. `getJiraIssue` with `fields: ["summary", "description", "status", "issuetype", "parent", "subtasks", "labels", "comment"]`.
2. Children: in `subtask` mode, the `subtasks` field. In `child` mode, `searchJiraIssuesUsingJql` with `parent = ABC-12`.

State mapping by status **category**: To Do is `todo`, In Progress is `in_progress`, Done is `done` unless the status name or resolution says cancelled / won't do, which is `cancelled`.

### create(title, body, parent?, labels?)

`createJiraIssue` with `projectKey`, `summary`, `description`, and:

| Case | `issueTypeName` | `parent` |
|---|---|---|
| Parent issue, `step_type: subtask` | Task (or Story) | none |
| Parent issue, `step_type: child` | Epic | none |
| Step under a parent | Sub-task in `subtask` mode, Task in `child` mode | the parent key |
| Other issues (needs planning) | Task | none |

Pass labels through `additional_fields: {"labels": [...]}`, with spaces replaced by `-`. Use the exact issue type names from `getJiraProjectIssueTypesMetadata`; sites rename them (for example "Subtask" vs "Sub-task"). Return the key it gives back.

### link(child, parent)

- `child` mode: `editJiraIssue` on the child with `fields: {"parent": {"key": "<parent>"}}`.
- `subtask` mode: an existing issue cannot become a sub-task through these tools. Create a "Relates" link with `createIssueLink`, list the child in the parent's Steps section, and tell the user it is not a true sub-task.

If the child already has another parent, stop and ask.

### comment(id, body)

`addCommentToJiraIssue` with `commentBody` and `contentFormat: "markdown"`.

### update_body(id, body)

1. `getJiraIssue` with `fields: ["description"]` and `responseContentFormat: "adf"`.
2. Change only what is needed, for example a `taskItem`'s `attrs.state` from `TODO` to `DONE`.
3. `editJiraIssue` with `fields: {"description": <whole ADF document>}` and `contentFormat: "adf"`.

Never send a partial document; the description is replaced whole.

### set_state(id, state)

Transitions are per project and per current status, so look them up every time.

1. `getTransitionsForJiraIssue`.
2. Pick the transition whose target status matches, by name first, then by category:
   - `todo`: "To Do", "Open", "Backlog"; category To Do.
   - `in_progress`: "In Progress"; category In Progress.
   - `done`: "Done", "Closed", "Resolved"; category Done.
   - `cancelled`: "Cancelled", "Canceled", "Won't Do"; if none exists, ask the user.
3. If no transition or more than one fits, ask once, then write the mapping under `## Notes` (for example `Jira transitions: in_progress = "Start work"`) and use it from then on.
4. `transitionJiraIssue` with that transition id.

**What Jira does on its own:** nothing by default. A site may have automation rules (for example "PR merged → Done", "branch created → In Progress") through a development tool integration. Setup records what the user says under `## Notes`:
- `Jira moves issues on PR open: yes` → skills skip `set_state(in_progress)` once a PR exists.
- `Jira moves issues on merge: yes` → skills skip `set_state(done)` after a merge.
When the note is missing or says no, skills call `set_state` themselves.

### branch_name(id)

`<branches.work_prefix>/<key>-<slug>`, for example `step/ABC-12-validate-address`. Keep the key in upper case so Jira's development integration recognizes it. The slug is the summary in lowercase ASCII, words joined by `-`, at most 40 characters.

### closes(id)

Put `Jira: ABC-12` on its own line in the PR body and the key in the PR title. The key is what Jira's development integration uses to link the PR; there is no closing keyword. Smart-commit commands such as `#done` work only in commit messages and only on sites that enabled them, so do not rely on them. After the merge, call `set_state(done)` unless `## Notes` says Jira moves issues on merge.

## Setup

1. **Detect.** Atlassian MCP tools are available, or the user names Jira.
2. **Ask.** Which site (show `getAccessibleAtlassianResources`), which project (show `getVisibleJiraProjects`), and `step_type`. Show the issue types from `getJiraProjectIssueTypesMetadata`: offer `subtask` only when a sub-task type exists and `child` only when Epic exists. Ask: "Does your Jira move issues on its own when a branch or PR is created, or when a PR merges?" Offer "not sure" and treat it as no.
3. **Verify with read-only calls.** `getVisibleJiraProjects` must list the project, and `getJiraProjectIssueTypesMetadata` must succeed. If the MCP server is unauthorized, stop and tell the user to authorize it in their client. Create nothing.
4. **Record.** `tracker: {type: jira, site, project, step_type}`, and the automation lines under `## Notes`.
