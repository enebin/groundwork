---
name: update
description: Brings a repository already set up with groundwork up to the installed plugin version. Reads the plugin's change list between the version the repository was set up with and the installed one, applies required migrations, lets the user pick which new features to attach, and refreshes rule blocks whose text changed. Does not repeat onboarding, except that it points to onboarding when an update brings more than 8 choices. Use after updating the plugin, or for "what's new in groundwork", "update groundwork", or "upgrade GROUNDWORK.md".
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, Skill, AskUserQuestion
---

Bring this repository's groundwork setup up to the installed plugin version. Ask only about what changed between versions; every other choice stays as it is.

Read `reference/config.md` under the plugin root (two directories above this skill's directory), then `GROUNDWORK.md` at the repository root. Talk in `language.conversation`; write in `language.artifacts`. Ask questions as the Asking section of `skills/onboarding/SKILL.md` says.

This skill writes nothing until the user approves the final preview. Plan mode: gather everything read-only, write the plan, and continue after approval.

## 1. Scan

Run `python3 <plugin root>/skills/update/scan.py <repository root>`. It reads `CHANGES.json` at the plugin root, which lists every release's items with what each one concerns, and needs no network. It prints one JSON report:

- `installed`, `latest_known` (the newest release in `CHANGES.json`), `set_up_with` (`plugin_version` in `GROUNDWORK.md`; null when the file predates the key, and then every release is checked), `target` (the installed version, or the latest release in `CHANGES.json` when the installed build is newer, such as one from `develop`), and `schema`.
- `status`: `not-set-up` (no `GROUNDWORK.md`: tell the user to run `/groundwork:onboarding` and stop), `plugin-older-than-setup` (stop and ask the user to update the plugin with `npx @enebin/groundwork@latest update`; the commands without Node.js are below), `up-to-date` (say so and stop), or `ok`.
- `items`: each release item after `set_up_with`, up to `target`, oldest first, with its version, section, group, `text` (the release-note line), and the `key` or `addons` it concerns.
- `blocks`: each managed block in `docs.rules` and `docs.architecture`, with its status.

Also stop and ask the user to update the plugin with `npx @enebin/groundwork@latest update` (the commands without Node.js are below) when `schema` is newer than `reference/config.md` knows. If the script cannot run (no `python3`), say why and stop; name `/groundwork:onboarding` as the way forward, which migrates the whole file.

Then check for a newer release with one request: `curl -fsS --max-time 5 https://raw.githubusercontent.com/enebin/groundwork/main/plugins/groundwork/.claude-plugin/plugin.json`. When its `version` is newer than `installed`, say so and tell the user to update the plugin first: `npx @enebin/groundwork@latest update`, then a Claude Code restart or a new Codex session. Without Node.js, `claude plugin update groundwork@groundwork` in Claude Code, or `codex plugin marketplace upgrade groundwork` then `codex plugin add groundwork@groundwork` in Codex. Offer to continue up to the installed version. When the request fails, continue without it.

## 2. Read the groups

The script already sorted each item, from the item's tag in `CHANGES.json` and this repository's `GROUNDWORK.md`. Use its groups as they are; do not re-sort items by reading skills or the catalog.

| Group | Means | What happens |
|---|---|---|
| `needs_migration` | An Upgrading note, or a key the installed plugin needs that the file lacks | Applied, following the migration rules in `reference/config.md` and the onboarding step that owns the key |
| `can_attach` | A new choice: a config value, a bundle option, or an add-on from `catalog/addons.md` | The user picks |
| `comes_automatically` | A change inside a skill or agent with nothing to set, and every bug fix | Listed only |
| `already_in_place` | The key has a value, or the add-on is recorded in `## Add-ons` | Listed only |

Each managed block has one status:

- `same`: the plugin's rule text has not changed. Nothing to do.
- `changed`: a **Rule text changed** item.
- `unstamped-same`: the block matches the current source but its marker has no `source` hash yet. Add the hash when writing; no question.
- `unstamped`: an older marker without a hash, whose text differs from the English source. Compare it once with the source for this repository's choices, as translated into `language.artifacts`. Only a difference in meaning makes it a **Rule text changed** item; otherwise add the hash when writing.
- `unknown`: the id names no plugin source. Skip it: it holds the user's answers (such as `project-rules`, onboarding step 8 rules, review focus sections, and `addons`) or an add-on's own text (such as `slack-report`). Compare it as for `unstamped` only when its text is plainly one of the plugin's rule sets written under an older id.

Then count the choices: the report's `choices` (Needs migration and Can attach items). When there are more than 8, there are too many changes to recommend one by one. Say so with the count, list the items by group so the user knows what is new, and tell the user to run `/groundwork:onboarding` in full to apply them, not to come back to update. Onboarding keeps the current values as recommendations, offers new settings in its steps, and lists new add-ons after setup. Stop without writing anything. Items that need no choice (Comes automatically, Already in place) and Rule text changed blocks do not count.

## 3. Choose

Show one table, grouped as above, with the version and one line per item in plain words. Then ask in one interaction any question a **Needs migration** item requires, using the question its onboarding step asks (for example the UX method when old settings ran UX both from the code and on the app); which **Can attach** items to add (multi-select, none preselected) and which **Rule text changed** blocks to refresh ("Refresh (Recommended) — keeps the rules in line with what the skills now expect"). Show a block's diff only when the user asks.

For each item the user picks, collect only what it needs:

- A config value or bundle option: ask only that onboarding step's questions for it, with the current values as recommendations.
- An add-on: note it; it runs after the write in step 5.

## 4. Final preview

Mandatory. Show the migrations with their resulting values, the chosen items, the refreshed blocks, and each file to change with one line on what changes. Show `plugin_version` moving to the report's `target`. Show full file contents only when the user asks.

Write only after approval. In `GROUNDWORK.md`, change only the frontmatter keys an item concerns and the managed `addons` block. In `docs.rules` and `docs.architecture`, never edit text outside `<!-- groundwork:begin/end -->` markers. Write each refreshed or stamped block's marker as `<!-- groundwork:begin <id> source=<hash> -->`, with the `source` the report gives, as the Final review section of `skills/onboarding/SKILL.md` says. Set `plugin_version` to `target` last, so a failed write leaves the old version and a re-run picks up the same items.

## 5. Finish

- Report what was written in a short list, and the items that came automatically.
- For each chosen add-on, invoke `/groundwork:<skill>` in Claude Code, or read and follow `skills/<skill>/SKILL.md` in Codex, one at a time.
- Offer to commit the changes. Commit only if the user says yes.
