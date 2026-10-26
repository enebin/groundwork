---
name: addons
description: Show Groundwork's optional productivity skills and continue with the user's chosen setup or one-off task. Use after onboarding or when the user asks about add-ons, Slack reporting, handoff notes, weekly summaries, or release preparation options.
---

Read `reference/config.md` under the plugin root (two directories above this skill), then the repository's `GROUNDWORK.md` and its rules. Use `language.conversation` for the menu and `language.artifacts` for saved documents.

Read `catalog/addons.md` and follow its menu and setup-recording rules. Show all available entries, each with what it does and when it is useful, plus any verified setup status. Make it clear the user can finish now and return later with `/groundwork:addons`.

Accept an item by name or number, or a request to finish. With no selection, ask which item the user wants, or whether to finish, using the client's available question tool; do not silently select a recommendation. In Claude Code, invoke the chosen `/groundwork:<skill>`. In Codex, read and follow `skills/<skill>/SKILL.md` under the same plugin root. All entries use the same skill files in both clients.

If the user names a specific task, carry its details into the chosen skill instead of asking again. If the selection is setup only, do not create an example report, post to Slack, or publish anything. On return, briefly report the result and offer another item or finish.
