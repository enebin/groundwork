---
name: update
description: Brings a repository already set up with groundwork up to the installed plugin version. Reads the release notes between the version the repository was set up with and the installed one, applies required migrations, lets the user pick which new features to attach, and refreshes rule blocks whose text changed. Does not repeat onboarding. Use after updating the plugin, or for "what's new in groundwork", "update groundwork", or "upgrade GROUNDWORK.md".
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, Skill, AskUserQuestion
---

Bring this repository's groundwork setup up to the installed plugin version. Ask only about what changed between versions; every other choice stays as it is.

Read `reference/config.md` under the plugin root (two directories above this skill's directory), then `GROUNDWORK.md` at the repository root. If `GROUNDWORK.md` is missing, there is nothing to update: tell the user to run `/groundwork:onboarding` and stop. Talk in `language.conversation`; write in `language.artifacts`. Ask questions as the Asking section of `skills/onboarding/SKILL.md` says.

This skill writes nothing until the user approves the final preview. Plan mode: gather everything read-only, write the plan, and continue after approval.

## 1. Pin the version range

- **Installed:** `version` in `.claude-plugin/plugin.json` under the plugin root.
- **Set up with:** `plugin_version` in `GROUNDWORK.md`. When it is absent, the file predates this key. Show the published versions and ask which one the repository was set up with: "Not sure — check every release (Recommended)", plus the versions. Checking every release is safe, because step 3 skips what is already in place.
- **Latest published:** from the releases of `enebin/groundwork`. Read `https://api.github.com/repos/enebin/groundwork/releases?per_page=100` with `curl`, following the `Link` header to later pages; if that fails, use `gh release list -R enebin/groundwork --limit 1000`. Release tags are `groundwork--v<version>`. Skip drafts and releases whose version is not in the range.

Compare versions numerically. Then:

- Latest published is newer than installed: say so, and tell the user to update the plugin first: in Claude Code, `claude plugin update groundwork@groundwork` and a restart; in Codex, update it the way it was installed and start a new session. Release notes describe features the installed plugin does not have yet, so offer to continue only up to the installed version.
- Installed is newer than latest published, such as a build from `develop`: say the installed version has no release notes yet. Continue only up to the latest published version, and treat that version as installed in every later step.
- Set up with equals installed: say the repository is up to date and stop.
- Set up with is newer than installed, or `groundwork` (the schema version) is newer than `reference/config.md` knows: stop and ask the user to update the plugin.
- The releases cannot be read: say why, and stop. Do not reconstruct the changes from memory or from the plugin's files. Name the ways forward: retry later, retry with `gh` installed and logged in, or run `/groundwork:onboarding`, which migrates the whole file without release notes.

## 2. Read the release notes

Read the notes of every release after "set up with", up to and including installed, oldest first. Take each bullet as one item and keep its version and section (New features, Bug fixes, Upgrading, or another heading).

## 3. Sort each item

Check each item against this repository's current `GROUNDWORK.md`, rules document, and the plugin's current skills and catalog. Put it in exactly one group:

| Group | Means | What happens |
|---|---|---|
| Needs migration | An Upgrading note, or a key the installed plugin needs that the file lacks | Applied, following the migration rules in `reference/config.md` and the onboarding step that owns the key |
| Can attach | A new choice: a config value, a bundle option, or an add-on from `catalog/addons.md` | The user picks |
| Comes automatically | A change inside a skill or agent with nothing to set, and every bug fix | Listed only |
| Already in place | The repository already has it, such as a key with a value or an add-on recorded in `## Add-ons` | Listed only |

When an item is unclear, read the skill or catalog entry it describes before sorting it. Do not invent an item the notes do not contain.

Then compare managed rule blocks. For each `<!-- groundwork:begin <id> -->` block in `docs.rules` and `docs.architecture` whose text comes from a plugin file (`implementation` from `reference/implementation.md`, `minimal-structure` and the architecture contract from `catalog/architecture/`, and catalog rule sets for the chosen bundles), compare it with that file's current text for this repository's choices. Each block that differs is a **Rule text changed** item. Skip blocks built from the user's own answers, such as onboarding step 8 rules, review focus sections, and `## Add-ons`.

## 4. Choose

Show one table, grouped as above, with the version and one line per item in plain words. Then ask in one interaction any question a **Needs migration** item requires, using the question its onboarding step asks (for example the UX method when old settings ran UX both from the code and on the app); which **Can attach** items to add (multi-select, none preselected) and which **Rule text changed** blocks to refresh ("Refresh (Recommended) — keeps the rules in line with what the skills now expect"). Show a block's diff only when the user asks.

For each item the user picks, collect only what it needs:

- A config value or bundle option: ask only that onboarding step's questions for it, with the current values as recommendations.
- An add-on: note it; it runs after the write in step 6.

## 5. Final preview

Mandatory. Show the migrations with their resulting values, the chosen items, the refreshed blocks, and each file to change with one line on what changes. Show `plugin_version` moving to the installed version. Show full file contents only when the user asks.

Write only after approval. In `GROUNDWORK.md`, change only the frontmatter keys an item concerns and the managed `addons` block. In `docs.rules` and `docs.architecture`, never edit text outside `<!-- groundwork:begin/end -->` markers. Set `plugin_version` to the installed version last, so a failed write leaves the old version and a re-run picks up the same items.

## 6. Finish

- Report what was written in a short list, and the items that came automatically.
- For each chosen add-on, invoke `/groundwork:<skill>` in Claude Code, or read and follow `skills/<skill>/SKILL.md` in Codex, one at a time.
- Offer to commit the changes. Commit only if the user says yes.
