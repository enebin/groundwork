# Optional add-ons

These skills ship with Groundwork in Claude Code and Codex. They are optional follow-ups after the eight onboarding choices. Selecting one starts its setup or one-off use; installing Groundwork does not enable reporting, scheduling, or publication.

Use this table as the single menu source. Translate names and descriptions into `language.conversation`, keeping the skill names exact. Add a row only when its skill exists. Skeptic Review belongs to the base review setup and is not an add-on.

| Skill | Name | What it does | When it helps |
|---|---|---|---|
| `slack-report` | Slack reports | Collect work changes and verification results in a repository channel. | Follow progress across several repositories from one place. |
| `handoff` | Handoff notes | Save completed work, remaining work, and the next starting point. | Resume work in a new session without reconstructing the previous conversation. |
| `weekly-summary` | Weekly work summary | Summarize a week's commits, pull requests, and issues with evidence. | Prepare a weekly update or retrospective. |
| `release-notes` | Release notes | Turn the changes between two revisions into user-facing notes. | Explain new features, fixes, and compatibility changes when shipping a version. |
| `ux-journey` | Journey usability test | Have a first-time user walk a whole journey, such as landing page → sign-up → organization setup, on the running app, and report where they hesitate, get lost, or give up. First use explores the project and proposes journeys for you to confirm. | Before a launch or release, or after changing the landing page, sign-up, or onboarding. Can also gate every release. |
| `release-prep` | Scheduled release preparation | Prepare and verify a release on a chosen cadence, recommend a version from the diff, and request final publication approval. | Keep releases moving without repeating the preparation checklist yourself. |

## Menu behavior

Show a compact list under a heading equivalent to **You might also find these useful**. Each entry includes both its task and its use case, not just its name. Offer to finish without selecting anything; do not turn the list into a ninth onboarding step. Choosing all onboarding recommendations never opts into add-ons.

Read an existing `## Add-ons` section in `GROUNDWORK.md` and the relevant settings before describing an item as configured. Mark configured items in the list, retaining their current settings until the user asks to change them. A missing section means no recorded setup, not that the skill is unavailable.

Configure or run only the item the user chooses. After it finishes, offer another item or finish; do not start the next item automatically. Opening the menu alone authorizes no files, Slack posts, scheduled tasks, or releases.

## Recording setup

When the user asks to keep a setup choice, store a short Markdown table in an optional `## Add-ons` body section of `GROUNDWORK.md`, inside `<!-- groundwork:begin addons -->` and `<!-- groundwork:end addons -->`. Keep unrelated text intact. Columns: `Skill | Settings`. Link detailed settings such as `SLACK_INFO.md`, `RELEASE_PREP.md`, or the `## Journey:` sections instead of duplicating them. One-off use needs no configuration write.

Record only actual setup: on-demand use, a confirmed Slack reporting mode, or a scheduler's successful response and task identity. If scheduling is unavailable, record **not scheduled**, with the recovery action; a saved desired cadence is not an active schedule. Do not put secrets in this section. These add-ons are unrelated to `verification.addons`.
