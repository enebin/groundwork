---
name: weekly-summary
description: Draft an evidence-based weekly repository summary from commits, pull requests, and issues. Use for a weekly update or retrospective. Runs on demand; does not schedule recurring work or post to another service unless explicitly requested.
---

Read `reference/config.md` under the plugin root (two directories above this skill), the repository's `GROUNDWORK.md`, and its rules. Talk in `language.conversation`; write the summary in `language.artifacts` unless the user requested another language.

## Scope and evidence

Use a supplied date range and timezone. Otherwise use the previous completed Monday-to-Monday week in the user's known timezone; ask only when the timezone cannot be determined. Show the exact start, exclusive end, and timezone. A requested current week ends at the current time and must be labeled partial. Never silently mix local dates with UTC timestamps.

Inspect local history for `branches.integration` and relevant work branches, including commit subjects and diffs. Collect merged PRs and issue changes through `catalog/trackers/<tracker.type>.md` read operations where supported. Follow account routing before authenticated calls. Fetch additional result pages when needed; state coverage limits when access or pagination is unavailable. Apply the same date bounds to every source. Exclude issue events outside the interval rather than presenting an issue's current status as a historical event.

Group by delivered outcome, combining commits belonging to the same PR. Keep merged changes, work in progress, and blockers separate. Do not infer completion from a commit message or a closed issue alone when the merge or delivery evidence disagrees. List evidence links or exact commit ids so each substantive statement can be checked. A commit or PR is not proof of deployment.

## Output

Write a short overview, delivered changes, work in progress, blockers, and next steps supported by the evidence. Include the date range, timezone, branches and sources inspected, and unavailable sources. Omit empty sections. When no activity was found, say which sources and period were checked; do not invent progress or next steps.

Use the requested destination. Otherwise create a fresh `.groundwork/notes/weekly-<start-date>-<end-date>.md`, adding a timestamp if that file already exists. Create a self-ignoring `.gitignore` containing `*` inside `.groundwork/notes/` if absent. Return a link to the file. Writing a summary does not authorize Slack posting, issue comments, or a recurring schedule; use `slack-report` only when the user requested delivery there.
